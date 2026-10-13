"""stage3.py -- Stage 3: predict held-out curves (spec section 7, Stage 3).

    python -m phslope.stage3                 # confirmatory: needs frozen thresholds, confirmed classes,
                                             # and filled descriptor tables
    python -m phslope.stage3 --exploratory   # runs now with what exists, labelled EXPLORATORY

Data: core-library single-edge (rising / falling) curves, registered as in Stage 2.
Models (spec 4.10-4.11): global_mean, sorbate_class_mean, mineral_class_mean,
edge_position_rule (only with descriptors), version_a and version_b per feature set.
Feature sets: `descriptors` (spec, needs data/descriptors filled), and in exploratory
mode `properties` (Samuel's property table + sorbate schemes + conditions) and
`conditions` (conditions only). Levels: leave one study / pair / mineral / sorbate out.
"""
import argparse
import os
import subprocess

import numpy as np
import pandas as pd

from phslope import cv, descriptors as desc, registration
from phslope.common import (PROJECT_ROOT, REPORTS_DIR, load_config, load_thresholds, run_stamp, write_stamp)
from phslope.library import load_library
from phslope.stage2 import analysis_table, attach_classes, classes_confirmed

THRESHOLDS_PATH = "phslope/config/thresholds.yaml"
BASELINES = ["global_mean", "sorbate_class_mean", "mineral_class_mean"]


def _git(*args):
    return subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()


def freeze_status():
    """(ok, message, freeze_commit). ok only if thresholds.yaml says frozen: true, has no
    uncommitted changes, and no commit after the freezing commit touched it."""
    if _git("status", "--porcelain", "--", THRESHOLDS_PATH):
        return False, "thresholds.yaml has uncommitted changes", None
    if not load_thresholds().get("frozen"):
        return False, "thresholds.yaml is not frozen (frozen: false)", None
    commits = _git("log", "--format=%h", "--reverse", "-S", "frozen: true", "--", THRESHOLDS_PATH).split()
    if not commits:
        return False, "no commit sets frozen: true", None
    later = _git("log", "--format=%h", f"{commits[0]}..HEAD", "--", THRESHOLDS_PATH)
    if later:
        return False, f"thresholds.yaml changed after the freezing commit {commits[0]}: {later.split()}", commits[0]
    return True, f"thresholds frozen at commit {commits[0]}", commits[0]


def build_dataset(lib, config, classes):
    reg = registration.register(lib, config)
    meta, _ = attach_classes(lib["meta"], classes)
    t = analysis_table(meta)
    t = t.set_index("curve_id").loc[reg["warp"]["curve_id"]].reset_index()
    t["pair"] = t["mineral"] + " | " + t["sorbate"]
    keep = t[["mineral_class", "sorbate_class"]].notna().all(axis=1).to_numpy()
    idx = reg["idx"][keep]
    return {"t": t[keep].reset_index(drop=True), "R": reg["R"][keep], "G": lib["G"][idx],
            "lower": lib["lower"][idx], "upper": lib["upper"][idx], "mask": lib["mask"][idx],
            "grid": lib["grid"], "u": reg["u"]}


def feature_sets(D, exploratory):
    """name -> (X array, report). Missing descriptor tables or empty columns -> set skipped, with a reason."""
    t, out, skipped = D["t"], {}, {}
    try:
        m, s = desc.load_descriptors()
        X, rep = desc.build_features(t, "descriptors", descriptors=(m, s))
        if rep["n_features"] > len(desc.CONDITION_FEATURES) and rep["n_complete"] >= 30:
            out["descriptors"] = (X, rep)
            for c in ("pzc_mid", "first_hydrolysis_logK"):
                if c in X:
                    t[c] = X[c].to_numpy()
        else:
            skipped["descriptors"] = f"descriptor tables are empty or too sparse ({rep})"
    except (FileNotFoundError, desc.DescriptorError) as e:
        skipped["descriptors"] = str(e)
    if exploratory:
        from phslope.schemes import load_mineral_properties, load_schemes
        cfg = load_schemes()
        props, _ = load_mineral_properties(cfg, t["mineral"].unique())
        out["properties"] = desc.build_features(t, "properties", props=props, schemes_cfg=cfg)
        out["conditions"] = desc.build_features(t, "conditions")
    return out, skipped


def main():
    ap = argparse.ArgumentParser(description="Stage 3: held-out prediction.")
    ap.add_argument("--library", default=os.path.join(REPORTS_DIR, "stage1", "library"))
    ap.add_argument("--exploratory", action="store_true")
    ap.add_argument("--levels", default="study,pair,mineral,sorbate")
    ap.add_argument("--out", default=os.path.join(REPORTS_DIR, "stage3"))
    args = ap.parse_args()

    frozen, freeze_msg, freeze_commit = freeze_status()
    confirmed, classes = classes_confirmed()
    print(f"[stage3] {freeze_msg}; classes {'confirmed' if confirmed else 'NOT confirmed'}")
    if not args.exploratory and not (frozen and confirmed):
        raise SystemExit("Stage 3 (confirmatory) refuses to run: " + freeze_msg
                         + ("" if confirmed else "; classes.yaml not confirmed")
                         + ". Use --exploratory for a labelled exploratory run.")

    config, thr_all = load_config(), load_thresholds()
    os.makedirs(args.out, exist_ok=True)
    stamp = dict(run_stamp(f"library: {args.library}"), thresholds=freeze_msg, freeze_commit=freeze_commit,
                 exploratory=args.exploratory, classes_confirmed=confirmed)
    write_stamp(args.out, stamp)

    lib = load_library(args.library)
    D = build_dataset(lib, config, classes)
    fsets, skipped = feature_sets(D, args.exploratory)
    if not fsets:
        raise SystemExit(f"No usable feature set: {skipped}")
    models, X_by = list(BASELINES), {}
    if "pzc_mid" in D["t"] and "first_hydrolysis_logK" in D["t"]:
        models.append("edge_position_rule")
    for name, (X, _) in fsets.items():
        for v in ("version_a", "version_b"):
            models.append(f"{v}@{name}")
            X_by[f"{v}@{name}"] = X.to_numpy(float)
    per = []
    for level in args.levels.split(","):
        print(f"[stage3] leave one {level} out: {len(models)} models")
        per.append(cv.run_cv(D, level, models, X_by, config["fpca"]))
    per = pd.concat(per, ignore_index=True)
    per.sort_values(["level", "model", "p50_error"], ascending=[True, True, False]).to_csv(
        os.path.join(args.out, "per_curve_worst_first.csv"), index=False)
    summ = cv.summarize(per)
    summ.to_csv(os.path.join(args.out, "metrics_by_model.csv"), index=False)
    diffs = pd.concat([cv.paired_differences(per, m, [b for b in models if b in BASELINES + ["edge_position_rule"]])
                       for m in models if m.startswith("version")], ignore_index=True)
    diffs.to_csv(os.path.join(args.out, "paired_differences.csv"), index=False)
    from phslope import report
    report.stage3_summary(args.out, D, fsets, skipped, summ, diffs, thr_all, stamp)


if __name__ == "__main__":
    main()
