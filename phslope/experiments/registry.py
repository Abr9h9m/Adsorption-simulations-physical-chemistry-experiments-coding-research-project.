"""registry.py -- locked test set, development-data access, experiment registry, run stamps.

Locked test set (protocol section 3): a fixed, seeded 20% of papers, stratified, written to
config/locked_test_papers.txt and committed BEFORE any experiment. Development code gets
data only through `dev_mask` / `drop_locked`; the locked papers are returned only by
`final_papers()`, which integrate.py calls once, with an explicit flag.

Registry: every run (including failures) is appended to reports/phslope/experiments/REGISTRY.md.

    python -m phslope.experiments.registry lock      # create the locked set (refuses if it exists)
    python -m phslope.experiments.run E1             # dispatcher (see run.py)
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yaml

from phslope.common import CONFIG_DIR, PROJECT_ROOT, REPORTS_DIR, run_stamp

EXP_DIR = os.path.join(REPORTS_DIR, "experiments")
REGISTRY = os.path.join(EXP_DIR, "REGISTRY.md")
ADJUSTMENTS = os.path.join(EXP_DIR, "MODEL_ADJUSTMENTS.md")


def load_exp_config():
    with open(os.path.join(CONFIG_DIR, "experiments.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def locked_path(cfg=None):
    cfg = cfg or load_exp_config()
    return os.path.join(PROJECT_ROOT, cfg["locked_set"]["file"])


# ------------------------------------------------------------------ locked set

def choose_locked(papers, fraction, seed):
    """papers: DataFrame with columns reference, stratum. Stratified seeded draw; at least one
    paper per stratum of size >= 3, rounding so the total is round(fraction * n)."""
    rng = np.random.default_rng(seed)
    target = int(round(fraction * len(papers)))
    picks = []
    strata = papers.groupby("stratum")["reference"].apply(lambda s: sorted(s)).to_dict()
    quota = {k: fraction * len(v) for k, v in strata.items()}
    base = {k: int(np.floor(q)) for k, q in quota.items()}
    rest = target - sum(base.values())
    for k in sorted(quota, key=lambda k: quota[k] - base[k], reverse=True)[:max(rest, 0)]:
        base[k] += 1
    for k in sorted(strata):
        v = strata[k]
        n = min(base[k], len(v))
        picks += list(rng.choice(v, n, replace=False)) if n else []
    return sorted(picks)


def build_locked_set(lib_meta, classes, cfg):
    core = lib_meta[lib_meta["in_core_library"].astype(bool) & lib_meta["shape"].isin(["rising", "falling"])].copy()
    core["sorbate_class"] = core["sorbate"].map(classes.get("sorbates") or {}).fillna("unassigned")
    core["pair"] = core["mineral"] + " | " + core["sorbate"]
    multi = core.groupby("pair")["reference"].nunique()
    rows = []
    for ref, g in core.groupby("reference"):
        dom = g["sorbate_class"].value_counts().idxmax()
        in_other = bool((multi.loc[g["pair"].unique()] >= 2).any())
        rows.append({"reference": ref, "stratum": f"{dom}|{'pair_elsewhere' if in_other else 'pair_only_here'}"})
    papers = pd.DataFrame(rows)
    return choose_locked(papers, cfg["locked_set"]["fraction"], cfg["seed"]), papers


def write_locked(refs, path, papers):
    if os.path.exists(path):
        raise FileExistsError(f"{path} already exists; the locked set is created once")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Locked test papers (PH_ONLY_TEST_PROTOCOL.md section 3). Do not edit; do not load in development.\n")
        f.write(f"# created {datetime.now(timezone.utc):%Y-%m-%d}; {len(refs)} of {len(papers)} papers; "
                "stratified by dominant sorbate class x pair-in-other-paper; seeded\n")
        for r in refs:
            f.write(r + "\n")


def read_locked(cfg=None):
    path = locked_path(cfg)
    if not os.path.exists(path):
        raise FileNotFoundError(f"locked set not created: {path} (python -m phslope.experiments.registry lock)")
    with open(path, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}


def locked_hash(cfg=None):
    with open(locked_path(cfg), "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()[:12]


def drop_locked(df, col="reference"):
    """Development data only: rows whose paper is in the locked set are removed."""
    locked = read_locked()
    return df[~df[col].isin(locked)].copy()


def final_papers(confirm=False):
    """The locked papers. Only integrate.py may call this, once, with confirm=True."""
    if not confirm:
        raise PermissionError("the locked test set is opened only in integrate.py with confirm=True")
    log_run("F", "OPENED LOCKED TEST SET", "locked set opened")
    return read_locked()


# ------------------------------------------------------------------ registry and stamps

def exp_stamp(data_file=None, extra=None):
    s = run_stamp(data_file)
    try:
        s["locked_set_hash"] = locked_hash()
    except FileNotFoundError:
        s["locked_set_hash"] = None
    s.update(extra or {})
    return s


def write_run_info(out_dir, stamp):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "RUN_INFO.json"), "w", encoding="utf-8") as f:
        json.dump(stamp, f, indent=2, default=str)


def log_run(exp, verdict, note, stamp=None):
    os.makedirs(EXP_DIR, exist_ok=True)
    new = not os.path.exists(REGISTRY)
    with open(REGISTRY, "a", encoding="utf-8") as f:
        if new:
            f.write("# Experiment registry (every run, including failures)\n\n"
                    "| when (UTC) | experiment | commit | locked-set hash | verdict | note |\n|---|---|---|---|---|---|\n")
        s = stamp or {}
        f.write(f"| {datetime.now(timezone.utc):%Y-%m-%d %H:%M} | {exp} | {s.get('git_commit', '')} | "
                f"{s.get('locked_set_hash', '')} | {verdict} | {note} |\n")


def record_adjustment(name, decision, evidence):
    os.makedirs(EXP_DIR, exist_ok=True)
    new = not os.path.exists(ADJUSTMENTS)
    with open(ADJUSTMENTS, "a", encoding="utf-8") as f:
        if new:
            f.write("# Model adjustments (accepted and rejected, with evidence)\n\n"
                    "Locked test set: 20% of papers, seeded (decision D1 default). Each adjustment enters the "
                    "model only if it meets its pre-declared rule on development papers.\n\n"
                    "| adjustment | decision | evidence |\n|---|---|---|\n")
        f.write(f"| {name} | {decision} | {evidence} |\n")


def bh(p):
    from phslope.schemes import bh_adjust
    return bh_adjust(p)


def main():
    import sys
    from phslope.library import load_library
    from phslope.stage2 import classes_confirmed
    if len(sys.argv) < 2 or sys.argv[1] != "lock":
        raise SystemExit("usage: python -m phslope.experiments.registry lock")
    cfg = load_exp_config()
    lib = load_library(os.path.join(REPORTS_DIR, "stage1", "library"))
    _, classes = classes_confirmed()
    refs, papers = build_locked_set(lib["meta"], classes, cfg)
    write_locked(refs, locked_path(cfg), papers)
    print(f"locked {len(refs)} of {len(papers)} papers -> {locked_path(cfg)} (hash {locked_hash(cfg)})")
    print(papers.assign(locked=papers["reference"].isin(refs)).groupby("stratum")["locked"].agg(["size", "sum"]))


if __name__ == "__main__":
    main()
