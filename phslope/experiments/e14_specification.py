"""E14 -- specification curve (multiverse) over extraction choices (Addendum 1). EXPLORATORY; development only.

Grid (frozen in experiments.yaml e14 before running): fraction window x minimum points per curve x line R2
threshold x minimum units per pair x edge definition (pH20/50/80) x duplicate collapse (lineage units or
papers) x weighting (each curve, or each unit counts once). 324 specifications.
Headline conclusions re-estimated in every specification:
  H1 matching gain        median B3 error < median B0 error
  H2 rising solids slope  within-pair edge vs log10 solids: slope < 0, 95% interval below 0
  H3 falling solids slope slope > 0, interval above 0
  H4 loading Kd drop      within-pair log10 Kd at the pair reference pH vs max(log10 L + 4.5, 0): slope < 0,
                          interval below 0
  H5 ionic strength null  within-pair edge vs log10 I: interval includes 0
A conclusion is "robust" if it holds in >= 90% of specifications (D8 default).
"""
import itertools
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from phslope.common import solids_term
from phslope.experiments import harness as H
from phslope.experiments.data import build, refit_lines
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info

OUT = os.path.join(EXP_DIR, "E14")
LOGK = {"pH20": np.log10(0.25), "pH50": 0.0, "pH80": np.log10(4.0)}


def within_slope(d, ycol, xcol, unit_col, weighting):
    d = d.dropna(subset=[ycol, xcol]).copy()
    d = d[d.groupby("grp")[xcol].transform("nunique") >= 2]
    if len(d) < 10 or d[unit_col].nunique() < 3:
        return np.nan, np.nan, np.nan
    y = d[ycol] - d.groupby("grp")[ycol].transform("mean")
    x = d[xcol] - d.groupby("grp")[xcol].transform("mean")
    w = 1.0 / d.groupby(unit_col)[unit_col].transform("size") if weighting == "paper" else np.ones(len(d))
    r = sm.WLS(y, sm.add_constant(x), weights=w).fit(cov_type="cluster",
                                                   cov_kwds={"groups": pd.factorize(d[unit_col])[0]})
    lo, hi = r.conf_int().iloc[1]
    return r.params.iloc[1], lo, hi


def one_spec(base_by_window, spec):
    win, minp, r2, minu, edef, collapse, weighting = spec
    c = base_by_window[tuple(win)]
    unit_col = "lineage_cluster" if collapse else "reference"
    c = c[c["shape"].isin(["rising", "falling"]) & (c["solids_g_L"] > 0) & (c["total_sorbate_mol_L"] > 0)
          & c["line_dir_ok"] & (c["r2"] >= r2) & c["line_in_range"] & (c["n_points"] >= minp)].copy()
    c["edge_x"] = (LOGK[edef] - c["a"]) / c["b"]
    c["grp"] = c["pair"] + "|" + c["shape"]
    c = c[c.groupby("grp")[unit_col].transform("nunique") >= minu]
    out = {"window": f"{win[0]}-{win[1]}", "min_points": minp, "r2": r2, "min_units": minu, "edge": edef,
           "collapse_duplicates": collapse, "weighting": weighting, "curves": len(c), "units": c[unit_col].nunique()}
    if len(c) < 30:
        return out
    hc = H.prepare(c.drop(columns=["edge"], errors="ignore"), "edge_x")
    p = H.baseline_predictions(hc, unit_col=unit_col)
    L = H.long_errors(hc, p, ["B0_all_other", "B3_matched_fb"], unit_col=unit_col)
    s = H.summarize(L, B=0).set_index("model")
    col = "median_paper_weighted" if weighting == "paper" else "median"
    out["B0_median"], out["B3_median"] = s.loc["B0_all_other", col], s.loc["B3_matched_fb", col]
    for k, shape in (("rising_solids", "rising"), ("falling_solids", "falling")):
        out[k], out[k + "_lo"], out[k + "_hi"] = within_slope(c[c["shape"] == shape], "edge_x", "log10_solids",
                                                               unit_col, weighting)
    c["pH_ref"] = c["grp"].map(c.groupby("grp")["pH_native"].median())
    c["logKd"] = c["a"] + c["b"] * c["pH_ref"] - solids_term(c["log10_solids"])
    c["hinge"] = np.maximum(c["log10L"] + 4.5, 0)
    out["loading"], out["loading_lo"], out["loading_hi"] = within_slope(c, "logKd", "hinge", unit_col, weighting)
    out["ionic"], out["ionic_lo"], out["ionic_hi"] = within_slope(c, "edge_x", "log10_I", unit_col, weighting)
    return out


def run():
    ecfg = load_exp_config()
    g = ecfg["e14"]
    curves, obs = build(purpose="E14")
    stamp = exp_stamp(extra={"experiment": "E14"})
    write_run_info(OUT, stamp)
    lin = pd.read_csv(os.path.join(EXP_DIR, "E3", "lineage_clusters.csv"))
    curves = curves.merge(lin[["reference", "lineage_cluster"]], on="reference", how="left")
    curves["lineage_cluster"] = curves["lineage_cluster"].fillna(curves["reference"])
    base = {}
    for w in g["windows"]:
        base[tuple(w)] = curves if tuple(w) == (0.03, 0.97) else refit_lines(curves, obs, tuple(w))
    specs = list(itertools.product(g["windows"], g["min_points"], g["line_r2_min"], g["min_units_per_pair"],
                                   g["edge_definition"], g["collapse_duplicates"], g["weighting"]))
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for i, s in enumerate(specs):
        rows.append(one_spec(base, s))
        if (i + 1) % 25 == 0:
            print(f"E14 {i + 1}/{len(specs)}", flush=True)
            pd.DataFrame(rows).to_csv(os.path.join(OUT, "specifications.csv"), index=False)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(OUT, "specifications.csv"), index=False)
    v = R.dropna(subset=["B0_median"])
    holds = {
        "H1 matching gain (B3 < B0)": (v["B3_median"] < v["B0_median"]),
        "H2 rising solids slope < 0 (interval below 0)": (v["rising_solids_hi"] < 0),
        "H3 falling solids slope > 0 (interval above 0)": (v["falling_solids_lo"] > 0),
        "H4 loading Kd drop (interval below 0)": (v["loading_hi"] < 0),
        "H5 ionic strength null (interval includes 0)": (v["ionic_lo"] <= 0) & (v["ionic_hi"] >= 0),
    }
    T = pd.DataFrame([{"conclusion": k, "specifications": int(s.notna().sum()), "share_holding": float(s.mean()),
                       "robust (>= 90%)": bool(s.mean() >= 0.9)} for k, s in holds.items()])
    T.to_csv(os.path.join(OUT, "robustness.csv"), index=False)
    _figure(v, os.path.join(OUT, "specification_curve.png"))
    from phslope.report import md_table
    lines = [
        "# E14 Specification curve: which conclusions survive arbitrary analysis choices?", "",
        "**Plain English.** Every analysis involves choices that have no single right answer (which points to "
        "use, how strict the quality filter is, how the edge is defined, whether copies are merged). We redid the "
        f"headline analyses for all {len(R)} combinations of reasonable choices and counted how often each "
        "conclusion still holds. A conclusion that holds in at least 90% of them is called robust.", "",
        f"> EXPLORATORY. Development papers only. {len(v)} of {len(R)} specifications had enough curves. Locked set "
        f"hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        md_table(T), "",
        "Per-specification estimates: `specifications.csv`; figure: `specification_curve.png`.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E14", "reported", "; ".join(f"{r.conclusion[:2]} {r.share_holding:.2f}" for r in T.itertuples()), stamp)
    print(T.to_string())


def _figure(v, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from phslope.report import BLUE, GRAY, ORANGE, _style
    panels = [("rising_solids", "rising solids slope (pH/decade)"), ("falling_solids", "falling solids slope"),
              ("loading", "loading Kd drop (log10 Kd per decade)"), ("ionic", "ionic-strength slope (pH/decade)")]
    fig, axes = plt.subplots(len(panels), 1, figsize=(8, 2.2 * len(panels)))
    for ax, (k, lab) in zip(axes, panels):
        d = v.dropna(subset=[k]).sort_values(k).reset_index(drop=True)
        excl = (d[k + "_lo"] > 0) | (d[k + "_hi"] < 0)
        ax.vlines(d.index, d[k + "_lo"], d[k + "_hi"], color=GRAY, lw=0.6, alpha=.5)
        ax.scatter(d.index[excl], d[k][excl], s=6, color=BLUE, label="interval excludes 0")
        ax.scatter(d.index[~excl], d[k][~excl], s=6, color=ORANGE, label="interval includes 0")
        ax.axhline(0, color="#999", lw=0.8)
        ax.set_ylabel(lab, fontsize=7)
        _style(ax)
    axes[0].legend(frameon=False, fontsize=7)
    axes[-1].set_xlabel("specifications, sorted by estimate", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run()
