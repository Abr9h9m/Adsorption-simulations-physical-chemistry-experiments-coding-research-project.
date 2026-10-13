"""stage2.py -- Stage 2: do mineral and sorbate classes matter? (spec section 7, Stage 2)

    python -m phslope.stage2                 # Part A always; Part B only if classes.yaml is confirmed
    python -m phslope.stage2 --exploratory   # Parts A, B (proposed classes) and C, all labelled EXPLORATORY
    options: --B (variance bootstrap), --perms (permutations), --out

EXPLORATORY mode exists because Stage 1 failed its survival rule and Samuel chose
(2026-10-12) to continue with the core library. It also lets Part B run with the
PROPOSED, unconfirmed classes; the report says so on every page.

Part A (task 2.2, no class labels needed): registration of single-edge core
curves, variance removed by registration, FPCA of the registered smoother
slopes with score uncertainty.

Part B (tasks 2.3-2.5, needs `confirmed: true` in classes.yaml): variance
split for edge position, log width, height and the FPCA scores; the same
with conditions as fixed effects; within-reference permutation test; Ward
clustering with ARI and PERMANOVA; the go/no-go verdict.

Part C (exploratory only, config/schemes.yaml): mineral-property splits from
Samuel's property table, mineral / sorbate / ionic-condition schemes, each
tested with a variance share and a within-reference permutation test, with
Benjamini-Hochberg false-discovery-rate correction across all tests.
"""
import argparse
import os

import numpy as np
import pandas as pd

from phslope import cluster, fpca as fpca_mod, registration, report, schemes, variance
from phslope.common import REPORTS_DIR, load_config, load_thresholds, load_yaml, run_stamp, write_stamp
from phslope.library import load_library

EDGE_SHAPES = ("rising", "falling", "bell", "multi_step")
CONDITION_COLS = ["log10_solids", "log10_total_sorbate", "log10_ionic_strength", "co2"]
MIN_CURVES = 20      # fewer curves than this for a parameter -> no variance split for it


# ------------------------------------------------------------------ Part A

def part_a(lib, config, out_dir):
    reg = registration.register(lib, config)
    vr = registration.variance_removed(lib, reg)
    f = fpca_mod.fpca(reg["R"], config["fpca"])
    sd = fpca_mod.score_uncertainty(lib, reg, f) if "draws_spline" in lib else None
    k = f["n_components"]
    scores = reg["warp"].copy()
    for j in range(k):
        scores[f"fpc{j + 1}"] = f["scores"][:, j]
        scores[f"fpc{j + 1}_sd"] = sd[:, j] if sd is not None else np.nan
    scores.to_csv(os.path.join(out_dir, "registration_and_scores.csv"), index=False)
    u_kept = reg["u"][f["columns"]]
    comp = pd.DataFrame({"u": u_kept, "mean": f["mean"], **{f"fpc{j + 1}": f["components"][j] for j in range(k)}})
    comp.to_csv(os.path.join(out_dir, "fpca_components.csv"), index=False)
    report.stage2_part_a_figures(out_dir, reg, f)
    return {"reg": reg, "variance_removed": vr, "fpca": f, "scores": scores}


# ------------------------------------------------------------------ Part B

def classes_confirmed():
    c = load_yaml("classes.yaml")
    return bool(c.get("confirmed")), c


def attach_classes(meta, classes):
    m = meta.copy()
    m["mineral_class"] = m["mineral"].map(classes.get("minerals") or {})
    m["sorbate_class"] = m["sorbate"].map(classes.get("sorbates") or {})
    unassigned = {"minerals": sorted(m.loc[m["mineral_class"].isna(), "mineral"].unique()),
                  "sorbates": sorted(m.loc[m["sorbate_class"].isna(), "sorbate"].unique())}
    return m, unassigned


def analysis_table(meta, scores=None):
    """Core curves with an edge, the parameters to explain, and condition covariates."""
    m = meta[meta["in_core_library"].astype(bool) & meta["shape"].isin(EDGE_SHAPES)].copy()
    m["log_width"] = np.log(m["width"].where(m["width"] > 0))
    m["log10_solids"] = np.log10(m["solids_g_L"].where(m["solids_g_L"] > 0))
    m["log10_total_sorbate"] = np.log10(m["total_sorbate_mol_L"].where(m["total_sorbate_mol_L"] > 0))
    m["log10_ionic_strength"] = np.log10(m["ionic_strength"].where(m["ionic_strength"] > 0))
    m["co2"] = m["co2_present"].astype(float)
    if scores is not None:
        fpc = [c for c in scores.columns if c.startswith("fpc") and not c.endswith("_sd")]
        m = m.merge(scores[["curve_id"] + fpc], on="curve_id", how="left")
    return m


def part_b(meta, classes, scores, config, thr_all, out_dir, B, n_perm, seed):
    m, unassigned = attach_classes(meta, classes)
    t = analysis_table(m, scores).dropna(subset=["mineral_class", "sorbate_class"])
    params = ["edge_pH", "log_width", "height"] + [c for c in t.columns if c.startswith("fpc") and not c.endswith("_sd")]
    splits = []
    for p in params:
        if t[p].notna().sum() >= MIN_CURVES:
            splits.append(variance.variance_split(t, p, B=B, seed=seed))
    if not splits:
        raise ValueError(f"Part B needs >= {MIN_CURVES} classed core edge curves per parameter; found {len(t)}")
    split = pd.concat(splits, ignore_index=True)
    split.to_csv(os.path.join(out_dir, "variance_split.csv"), index=False)

    temp_ok = t["temp"].notna().mean() >= 0.8
    fixed = CONDITION_COLS + (["temp"] if temp_ok else [])
    constant = [c for c in fixed if t[c].nunique(dropna=True) < 2]
    fixed = [c for c in fixed if c not in constant]
    cond = variance.variance_split(t, "edge_pH", B=0, fixed=fixed)
    cond.attrs["dropped_rows"] = int(t["edge_pH"].notna().sum() - cond.attrs["n"])
    cond.attrs["temp_used"] = temp_ok
    cond.attrs["constant_covariates_dropped"] = constant
    cond.to_csv(os.path.join(out_dir, "variance_split_edge_with_conditions.csv"), index=False)

    perm = variance.within_reference_permutation_test(t, "edge_pH", n_perm=n_perm, seed=seed)
    verdict = variance.stage2_verdict(split[split["parameter"] == "edge_pH"], perm, thr_all["stage2"]["permutation_p"])

    tests = []
    feats = {"edge parameters": t[["edge_pH", "log_width", "height"]].dropna().index}
    fpc_cols = [c for c in t.columns if c.startswith("fpc") and not c.endswith("_sd")]
    if fpc_cols:
        feats["FPCA scores"] = t[fpc_cols].dropna().index
    for fname, ix in feats.items():
        cols = ["edge_pH", "log_width", "height"] if fname == "edge parameters" else fpc_cols
        X = t.loc[ix, cols].to_numpy()
        for lab in ("mineral_class", "sorbate_class"):
            a = cluster.ari_test(X, t.loc[ix, lab], t.loc[ix, "reference"], n_perm=n_perm, seed=seed)
            pm = cluster.permanova(X, t.loc[ix, lab], t.loc[ix, "reference"], n_perm=n_perm, seed=seed)
            tests.append({"features": fname, "labels": lab, "n": a["n"], "ARI": a["ari"], "ARI_p": a["p_value"],
                          "ARI_null_mean": a["null_mean"], "PERMANOVA_F": pm["pseudo_F"], "PERMANOVA_R2": pm["R2"],
                          "PERMANOVA_p": pm["p_value"]})
    tests = pd.DataFrame(tests)
    tests.to_csv(os.path.join(out_dir, "class_tests.csv"), index=False)
    report.stage2_part_b_figures(out_dir, split, t)
    return {"split": split, "cond": cond, "perm": perm, "verdict": verdict, "tests": tests,
            "unassigned": unassigned, "table": t}


def part_c(meta, scores, out_dir, n_perm, seed):
    cfg = schemes.load_schemes()
    t = analysis_table(meta, scores)
    props, prop_report = schemes.load_mineral_properties(cfg, meta["mineral"].unique())
    _, classes = classes_confirmed()
    res, groupings = schemes.run_exploratory(t, cfg, props, n_perm, seed, classes=classes)
    res.to_csv(os.path.join(out_dir, "exploratory_groupings.csv"), index=False)
    labels = t[["curve_id", "mineral", "sorbate", "reference"]].copy()
    for g in groupings:
        labels[g["name"]] = g["labels"]
    labels.to_csv(os.path.join(out_dir, "exploratory_group_labels.csv"), index=False)
    report.stage2_part_c_figure(out_dir, res)
    return {"results": res, "property_report": prop_report, "n_curves": len(t), "n_groupings": len(groupings)}


def main():
    ap = argparse.ArgumentParser(description="Stage 2: do the classes matter?")
    ap.add_argument("--library", default=os.path.join(REPORTS_DIR, "stage1", "library"))
    ap.add_argument("--B", type=int, default=200, help="cluster-bootstrap resamples for variance shares")
    ap.add_argument("--perms", type=int)
    ap.add_argument("--out", default=os.path.join(REPORTS_DIR, "stage2"))
    ap.add_argument("--exploratory", action="store_true",
                    help="run Part B with unconfirmed classes and Part C; label everything exploratory")
    args = ap.parse_args()

    config, thr_all = load_config(), load_thresholds()
    n_perm = args.perms or thr_all["stage2"]["n_permutations"]
    os.makedirs(args.out, exist_ok=True)
    lib = load_library(args.library, with_draws=os.path.exists(os.path.join(args.library, "draws.npz")))
    stamp = run_stamp(f"library: {args.library}")
    write_stamp(args.out, stamp)

    seed = config["seeds"]["global"]
    a = part_a(lib, config, args.out)
    confirmed, classes = classes_confirmed()
    b = c = None
    if confirmed or args.exploratory:
        b = part_b(lib["meta"], classes, a["scores"], config, thr_all, args.out, args.B, n_perm, seed)
    if args.exploratory:
        c = part_c(lib["meta"], a["scores"], args.out, n_perm, seed)
    report.stage2_summary(args.out, lib, a, b, thr_all, stamp,
                          exploratory=args.exploratory, classes_confirmed=confirmed, c=c)


if __name__ == "__main__":
    main()
