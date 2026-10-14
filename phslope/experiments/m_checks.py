"""M7, M8, M9 (Addendum 1 modifications). EXPLORATORY; development papers only; no refitting.

M7  The conditions-matched result (follow-up: 0.25 pH on 79 curves) on DEVELOPMENT papers with lineage
    units: B3-matched vs B0 on the curves that have a matched paper, with unit-level bootstrap intervals and
    an explicit count of distinct papers and lineage units.
M8  "Same figure digitized twice": cross-paper curve pairs with the SAME number of points, every point
    matched (pH within 0.02, fraction within 0.01), from E3/duplicate_pairs.csv.
M9  E5 truncation error separately for steep and shallow edges (split at the median |b| of the
    well-measured curves).
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info

OUT = os.path.join(EXP_DIR, "M_checks")


def m7(curves, B, seed):
    lin = pd.read_csv(os.path.join(EXP_DIR, "E3", "lineage_clusters.csv"))
    c = curves.merge(lin[["reference", "lineage_cluster"]], on="reference")
    c["unit"] = c["lineage_cluster"]
    c = H.prepare(c[c["in_core_library"].astype(bool) & c["shape"].isin(["rising", "falling"])], "logistic_p50")
    c = c[c.groupby("grp")["unit"].transform("nunique") >= 2].reset_index(drop=True)
    p = H.baseline_predictions(c, unit_col="unit")
    m = p.dropna(subset=["B3_matched"])
    sub = c.set_index("curve_id").loc[m["curve_id"]]
    L = pd.concat([pd.DataFrame({"curve_id": m["curve_id"].to_numpy(), "unit": sub["unit"].to_numpy(), "model": name,
                                 "edge_error": np.abs(m[col].to_numpy() - sub["edge"].to_numpy())})
                   for name, col in (("B3 matched", "B3_matched"), ("B0 plain average", "B0_all_other"))])
    s = H.summarize(L, B=B, seed=seed)
    d = H.paired(L, "B3 matched", ["B0 plain average"], B=B, seed=seed)
    counts = {"curves_with_match": len(m), "papers": int(sub["reference"].nunique()),
              "lineage_units": int(sub["unit"].nunique())}
    return s, d, counts


def m8():
    dup = pd.read_csv(os.path.join(EXP_DIR, "E3", "duplicate_pairs.csv"))
    return dup[(dup["match_share"] >= 0.999) & dup["cross_paper"]]


def m8_same_length(curves, obs, d):
    n = obs.groupby("curve_id").size()
    return d[d["curve_a"].map(n) == d["curve_b"].map(n)]


def m9():
    t = pd.read_csv(os.path.join(EXP_DIR, "E5", "truncations.csv")).dropna(subset=["edge_error"])
    med = t.groupby("curve_id")["abs_b"].median()
    cut = med.median()
    t["steepness"] = np.where(t["curve_id"].map(med) >= cut, f"steep (|b| >= {cut:.2f})", f"shallow (|b| < {cut:.2f})")
    return t.groupby(["steepness", "window"]).agg(n=("edge_error", "size"), median_error=("edge_error", "median"),
                                                 within_0_5=("edge_error", lambda s: (s <= 0.5).mean())).reset_index()


def run(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    curves, obs = build(purpose="M7-M9")
    stamp = exp_stamp(extra={"experiment": "M7, M8, M9"})
    write_run_info(OUT, stamp)
    s7, d7, n7 = m7(curves, ecfg["harness"]["paper_bootstrap_B"], seed)
    d8 = m8_same_length(curves, obs, m8())
    t9 = m9()
    os.makedirs(OUT, exist_ok=True)
    s7.to_csv(os.path.join(OUT, "M7_matched_subset.csv"), index=False)
    d8.to_csv(os.path.join(OUT, "M8_same_figure_twice.csv"), index=False)
    t9.to_csv(os.path.join(OUT, "M9_truncation_by_steepness.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# M7, M8, M9 checks", "",
        f"> EXPLORATORY. Development papers only. Locked set hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## M7: the conditions-matched subset, with its uncertainty", "",
        f"Curves with a conditions-matched paper: {n7['curves_with_match']}, from {n7['papers']} papers in "
        f"{n7['lineage_units']} lineage units (development papers; the follow-up's 79 curves included locked papers "
        "and counted copies as separate papers).", "", md_table(s7), "", md_table(d7), "",
        "## M8: the same figure digitized twice (every point matches, same number of points, different papers)", "",
        f"{len(d8)} curve pairs.", "", md_table(d8), "",
        "## M9: truncation error by edge steepness (E5 truncations)", "", md_table(t9), "",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("M7-M9", "reported", f"M7 n={n7['curves_with_match']}; M8 {len(d8)} pairs", stamp)
    print(n7, len(d8))
    print(s7[["model", "n", "n_units", "median", "median_lo", "median_hi"]].to_string())
    print(d7[["median_diff", "diff_lo", "diff_hi"]].to_string())
    print(t9.to_string())


if __name__ == "__main__":
    run()
