"""E21 + M2 + M3 -- from the saved E1 held-out predictions (no refitting). EXPLORATORY; development only.

M2  alternative edges: pH at 20%, 50% and 80% sorbed and width = |pH80 - pH20|, predicted from the E1
    line (a_c, b at pH_c) vs the held-out curve's own line.
M3  decision-oriented metric: mean absolute error of FRACTION SORBED over the curve's measured pH points
    (what a user of the web interface sees), for E1 and the line baselines B0 / B3.
E21 paper-level conformal intervals (CV+ style): for a held-out unit, the edge interval is the prediction
    +/- the 90% quantile of |held-out edge errors| of all OTHER units (each unit's errors come from its
    own leave-out fold). Compared with E1's parametric intervals on coverage and width, overall, by
    direction and by pair size. Decision (pre-declared, experiments.yaml e21).
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E21_M2_M3")
LOGK = {"pH20": np.log10(0.2 / 0.8), "pH50": 0.0, "pH80": np.log10(0.8 / 0.2)}


def edges_from_line(a_c, b, pH_c, a=None):
    """pH at 20/50/80% sorbed. With a_c, b, pH_c: log10K = a_c + b (pH - pH_c). With a: log10K = a + b pH."""
    out = {}
    for k, lk in LOGK.items():
        out[k] = (lk - a) / b if a is not None else pH_c + (lk - a_c) / b
    out["width"] = np.abs(out["pH80"] - out["pH20"])
    return out


def frac(logk):
    return 1.0 / (1.0 + 10.0 ** (-np.asarray(logk, float)))


def baseline_lines(c):
    """Per curve: B0 (mean over other units of unit-mean a, b) and B3 (matched curves' mean a, b, else B0)."""
    rows = []
    for _, r in c.iterrows():
        o = c[(c["pair_dir"] == r["pair_dir"]) & (c["unit"] != r["unit"])]
        if o.empty:
            continue
        um = o.groupby("unit")[["a", "b"]].mean()
        a0, b0 = um["a"].mean(), um["b"].mean()
        m = ((o["log10_solids"] - r["log10_solids"]).abs() < 0.5).fillna(False) \
            & ((o["log10_total"] - r["log10_total"]).abs() < 1.0).fillna(False) \
            & (o["co2"] == r["co2"]) & (o["cosolute"] == r["cosolute"])
        a3, b3 = (o.loc[m, "a"].mean(), o.loc[m, "b"].mean()) if m.sum() else (a0, b0)
        rows.append({"curve_id": r["curve_id"], "B0_a": a0, "B0_b": b0, "B3_a": a3, "B3_b": b3})
    return pd.DataFrame(rows)


def conformal(P, q=0.9):
    """CV+ style: interval for unit u = pred +/- quantile_q(|errors of other units|)."""
    P = P.copy()
    P["abs_err"] = (P["pred_edge"] - P["pH_native"]).abs()
    lo, hi = [], []
    for u, g in P.groupby("unit"):
        others = P.loc[P["unit"] != u, "abs_err"].dropna()
        half = np.quantile(others, q) if len(others) else np.nan
        lo.append(pd.Series(g["pred_edge"] - half, index=g.index))
        hi.append(pd.Series(g["pred_edge"] + half, index=g.index))
    P["conf_lo"], P["conf_hi"] = pd.concat(lo), pd.concat(hi)
    return P


def coverage_table(P, by=None):
    def stats(d):
        par = (d["pH_native"] >= d["edge_lo"]) & (d["pH_native"] <= d["edge_hi"])
        con = (d["pH_native"] >= d["conf_lo"]) & (d["pH_native"] <= d["conf_hi"])
        return pd.Series({"n": len(d), "parametric_coverage": par.mean(),
                          "parametric_median_width": (d["edge_hi"] - d["edge_lo"]).median(),
                          "conformal_coverage": con.mean(),
                          "conformal_median_width": (d["conf_hi"] - d["conf_lo"]).median()})
    if by is None:
        return stats(P).to_frame().T.assign(group="all")
    return P.groupby(by).apply(stats, include_groups=False).reset_index().rename(columns={by: "group"})


def run():
    ecfg = load_exp_config()
    curves, obs = build(purpose="E21/M2/M3")
    stamp = exp_stamp(extra={"experiment": "E21 + M2 + M3", "source": "E1 cv_with_covariates.csv"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    P = pd.read_csv(os.path.join(EXP_DIR, "E1", "cv_with_covariates.csv"))
    P = P.dropna(subset=["pred_edge", "pH_native"])

    # ---- M2: alternative edges and width
    pe = edges_from_line(P["pred_a_c"], P["pred_b"], P["pH_c"])
    oe = edges_from_line(None, P["b"], None, a=P["a"])
    m2 = pd.DataFrame({k: (pe[k] - oe[k]).abs() for k in ["pH20", "pH50", "pH80", "width"]})
    m2_sum = m2.describe(percentiles=[.25, .5, .75]).T[["count", "25%", "50%", "75%"]].reset_index().rename(
        columns={"index": "quantity", "50%": "median_abs_error"})

    # ---- M3: fraction-sorbed MAE over the curve's measured points, E1 vs B0 / B3
    bl = baseline_lines(c)
    o = obs[obs["curve_id"].isin(P["curve_id"])][["curve_id", "pH", "response"]]
    o = o.merge(P[["curve_id", "pred_a_c", "pred_b", "pH_c", "unit"]], on="curve_id").merge(bl, on="curve_id", how="left")
    o["E1"] = (frac(o["pred_a_c"] + o["pred_b"] * (o["pH"] - o["pH_c"])) - o["response"]).abs()
    o["B0"] = (frac(o["B0_a"] + o["B0_b"] * o["pH"]) - o["response"]).abs()
    o["B3"] = (frac(o["B3_a"] + o["B3_b"] * o["pH"]) - o["response"]).abs()
    per = o.groupby("curve_id")[["E1", "B0", "B3"]].mean().dropna().join(P.set_index("curve_id")["unit"])
    from phslope.experiments import harness as H
    L = per.reset_index().melt(id_vars=["curve_id", "unit"], value_vars=["E1", "B0", "B3"], var_name="model",
                               value_name="fraction_mae")
    m3_sum = H.summarize(L, B=ecfg["harness"]["paper_bootstrap_B"], metric="fraction_mae")
    m3_diff = H.paired(L, "E1", ["B0", "B3"], B=ecfg["harness"]["paper_bootstrap_B"], metric="fraction_mae")

    # ---- E21: conformal vs parametric
    P = conformal(P)
    pair_units = c.groupby("pair_dir")["unit"].nunique()
    P["pair_size"] = P["pair_dir"].map(pair_units).map(lambda n: "1 unit" if n == 1 else ("2-3 units" if n <= 3 else "4+ units"))
    cov = pd.concat([coverage_table(P), coverage_table(P, "shape"), coverage_table(P, "pair_size")], ignore_index=True)
    lo, hi = ecfg["e21"]["coverage"]
    allrow = cov[cov["group"] == "all"].iloc[0]
    ok = {m: lo <= allrow[f"{m}_coverage"] <= hi for m in ("parametric", "conformal")}
    if ok["parametric"] and ok["conformal"]:
        choice = min(("parametric", "conformal"), key=lambda m: allrow[f"{m}_median_width"])
    else:
        choice = next((m for m in ("parametric", "conformal") if ok[m]), "neither")
    verdict = f"PREFER {choice}"

    os.makedirs(OUT, exist_ok=True)
    m2_sum.to_csv(os.path.join(OUT, "M2_edge_definitions.csv"), index=False)
    m3_sum.to_csv(os.path.join(OUT, "M3_fraction_mae.csv"), index=False)
    m3_diff.to_csv(os.path.join(OUT, "M3_paired.csv"), index=False)
    cov.to_csv(os.path.join(OUT, "E21_coverage.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E21 calibrated intervals, M2 edge definitions, M3 fraction-sorbed error", "",
        "**Plain English.** (1) Our 90% ranges for where a new paper's curve turns are checked two ways; "
        f"result: **{verdict}** intervals. (2) Errors at the 20% and 80% points of the curve and in its width "
        "show whether the steepness is predicted as well as the midpoint. (3) The error a web-interface user "
        "would see, in fraction sorbed across the measured pH range, is reported for the model and the simple "
        "rules.", "",
        f"> EXPLORATORY. From E1's saved held-out predictions (development papers, lineage-cluster leave-out). "
        f"Locked set hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## M2: absolute errors of alternative edge definitions (pH units)", "", md_table(m2_sum), "",
        "## M3: mean absolute error in fraction sorbed over the measured points", "", md_table(m3_sum), "",
        md_table(m3_diff), "",
        "## E21: edge interval coverage and width (90% nominal)", "", md_table(cov), "",
        f"Decision rule: coverage in [{lo}, {hi}] with the narrower width -> **{verdict}**.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E21/M2/M3", verdict, "from cached E1 predictions", stamp)
    record_adjustment("E21 interval method", verdict,
                      f"parametric coverage {allrow['parametric_coverage']:.2f} width {allrow['parametric_median_width']:.2f}; "
                      f"conformal {allrow['conformal_coverage']:.2f} width {allrow['conformal_median_width']:.2f}")
    print(verdict)
    print(cov.to_string())


if __name__ == "__main__":
    run()
