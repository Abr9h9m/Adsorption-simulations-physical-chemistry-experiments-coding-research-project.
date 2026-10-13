"""E2 -- weighting and censoring of points (protocol section 5, E2). EXPLORATORY; development only.

Schemes for the step-1 line fits of E1 (everything else in E1 unchanged):
  W0  unweighted, window (0.03, 0.97)                    [current]
  W1  empirical weights: 1 / variance of log10 K line residuals in fraction-sorbed bins,
      estimated from the W0 fits of all development curves (an error model, not an outcome)
  W2  fraction-space additive error: var(log10 K) ~ 1 / (f (1 - f))^2  ->  weight (f (1 - f))^2
  window sensitivity for W0: (0.01, 0.99), (0.03, 0.97), (0.10, 0.90)
  W3  censored / Tobit treatment of points outside the window: NOT implemented (stated in SUMMARY)

Evaluation: E1 leave-one-unit-out with each scheme; held-out log10 K RMSE always on the SAME points
(the held-out curve's 0.03-0.97 points) and on curves present under every scheme. Decision
(pre-declared): adopt a scheme if it lowers the median held-out log10 K RMSE by >= 5% relative to W0
and keeps edge-interval coverage in [0.80, 0.95]; otherwise keep W0 and (0.03, 0.97).
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import harness as H
from phslope.experiments.data import build, refit_lines
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E2")
BINS = np.array([0.0, 0.03, 0.06, 0.1, 0.2, 0.35, 0.5, 0.65, 0.8, 0.9, 0.94, 0.97, 1.0])


def empirical_error_model(curves, obs):
    """Residual variance of log10 K about each curve's W0 line, by fraction-sorbed bin."""
    o = obs.merge(curves[["curve_id", "a", "b"]], on="curve_id").dropna(subset=["a", "log10K"])
    o = o[(o["response"] > 0) & (o["response"] < 1)]
    o["res"] = o["log10K"] - (o["a"] + o["b"] * o["pH"])
    o["bin"] = pd.cut(o["response"], BINS)
    v = o.groupby("bin", observed=False)["res"].agg(lambda s: np.median(s ** 2) / 0.455).rename("var")  # robust
    tab = pd.DataFrame({"f_mid": [(i.left + i.right) / 2 for i in v.index], "var": v.to_numpy(),
                        "n": o.groupby("bin", observed=False).size().to_numpy()})
    return tab


def weight_W1(tab):
    ok = tab.dropna(subset=["var"])
    ok = ok[ok["n"] >= 30]

    def w(g):
        var = np.interp(g["response"].to_numpy(), ok["f_mid"], ok["var"])
        return 1.0 / np.maximum(var, 1e-6)
    return w


def weight_W2(g):
    f = g["response"].to_numpy()
    return np.clip(f * (1 - f), 1e-4, None) ** 2


def evaluate_scheme(curves, obs, cfg, name, window=None, weight=None, seed=0):
    c = curves if (window is None and weight is None) else refit_lines(curves, obs, window, weight)
    c = E1.attach_units(c) if "unit" not in c else c
    base, main = E1.main_set(c, cfg)
    P = E1.cross_validate(main, obs, cfg, covariates=True, seed=seed)
    P["scheme"] = name
    P["covered"] = (P["pH_native_eval"] >= P["edge_lo"]) & (P["pH_native_eval"] <= P["edge_hi"]) \
        if "pH_native_eval" in P else np.nan
    return P, len(main), len(base)


def run(seed=None):
    ecfg = load_exp_config()
    cfg = ecfg["e1"]
    seed = ecfg["seed"] if seed is None else seed
    curves, obs = build(purpose="E2")
    stamp = exp_stamp(extra={"experiment": "E2"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    # observed native edge for coverage: always the W0 line edge (so schemes are judged on one target)
    target = curves.set_index("curve_id")["pH_native"]
    tab = empirical_error_model(curves, obs)
    tab.to_csv(os.path.join(OUT, "error_model_by_f.csv"), index=False)
    schemes = [("W0 (0.03, 0.97)", None, None), ("W0 (0.01, 0.99)", (0.01, 0.99), None),
               ("W0 (0.10, 0.90)", (0.10, 0.90), None), ("W1 empirical (0.03, 0.97)", (0.03, 0.97), weight_W1(tab)),
               ("W2 logit-delta (0.03, 0.97)", (0.03, 0.97), weight_W2)]
    res, counts = [], []
    for name, window, weight in schemes:
        P, n_main, n_base = evaluate_scheme(curves, obs, cfg, name, window, weight, seed)
        P["target_edge"] = P["curve_id"].map(target)
        P["covered"] = (P["target_edge"] >= P["edge_lo"]) & (P["target_edge"] <= P["edge_hi"])
        P["edge_error"] = (P["pred_edge"] - P["target_edge"]).abs()
        res.append(P)
        n_pts = int(((obs["response"] > (window or (0.03, 0.97))[0]) & (obs["response"] < (window or (0.03, 0.97))[1])
                     & obs["log10K"].notna()).sum())
        counts.append({"scheme": name, "curves_in_main_set": n_main, "of_rising_falling": n_base, "points_in_window": n_pts})
        print(f"E2 {name}: {n_main} curves")
    R = pd.concat(res, ignore_index=True)
    common = set.intersection(*[set(d["curve_id"]) for _, d in R.groupby("scheme")])
    Rc = R[R["curve_id"].isin(common)]
    Rc = Rc.merge(curves[["curve_id", "unit"]], on="curve_id")
    summ = Rc.groupby("scheme").agg(n=("curve_id", "size"), median_logK_rmse=("logK_rmse", "median"),
                                    median_edge_error=("edge_error", "median"), coverage=("covered", "mean")).reset_index()
    w0 = summ.set_index("scheme").loc["W0 (0.03, 0.97)", "median_logK_rmse"]
    summ["rel_change_vs_W0"] = summ["median_logK_rmse"] / w0 - 1
    L = Rc.rename(columns={"logK_rmse": "metric", "scheme": "model"})[["curve_id", "unit", "model", "metric"]]
    diffs = pd.concat([H.paired(L, s, ["W0 (0.03, 0.97)"], B=ecfg["harness"]["paper_bootstrap_B"], seed=seed,
                                metric="metric") for s in summ["scheme"] if s != "W0 (0.03, 0.97)"])
    dec = ecfg["e2"]["decision"]
    summ["meets_rule"] = (summ["rel_change_vs_W0"] <= -dec["rmse_gain_min"]) & summ["coverage"].between(*dec["coverage"])
    summ.loc[summ["scheme"] == "W0 (0.03, 0.97)", "meets_rule"] = False
    winners = summ[summ["meets_rule"]].sort_values("median_logK_rmse")
    chosen = winners["scheme"].iloc[0] if len(winners) else "W0 (0.03, 0.97)"
    verdict = f"ADOPT {chosen}" if len(winners) else "KEEP W0 (0.03, 0.97)"

    summ.to_csv(os.path.join(OUT, "scheme_summary.csv"), index=False)
    diffs.to_csv(os.path.join(OUT, "paired_vs_W0.csv"), index=False)
    pd.DataFrame(counts).to_csv(os.path.join(OUT, "window_counts.csv"), index=False)
    R.to_csv(os.path.join(OUT, "heldout_by_scheme.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E2 Weighting and point windows for the log10 K lines", "",
        "**Plain English.** Points where almost nothing or almost everything is stuck are the least reliable, "
        "because small measurement errors there become huge errors on the log scale. We tried down-weighting them "
        "in different ways and changing which points are used, and checked whether predictions of held-out papers "
        f"got better. Result: **{verdict}**.", "",
        f"> EXPLORATORY. Development papers only; E1 model unchanged except the step-1 line fits. Locked set hash "
        f"`{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## Error model (W1): robust variance of log10 K about the curve's own line, by fraction sorbed", "",
        md_table(tab), "",
        f"## Held-out results on the {len(common)} curves present under every scheme (same evaluation points)", "",
        md_table(summ), "",
        "## Paired differences in held-out log10 K RMSE vs W0 (95% intervals over units)", "", md_table(diffs), "",
        "## Curves and points per window", "", md_table(pd.DataFrame(counts)), "",
        "## Notes", "",
        "- W3 (censored/Tobit fit of points outside the window) was not implemented in this round.",
        "- The W1 error model is estimated from all development curves' own line residuals (a property of the "
        "measurements, not of held-out outcomes).",
        "- Reported detection limits were looked for in E0.1; the file has no detection-limit column.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E2", verdict, f"{len(schemes)} schemes, {len(diffs)} paired tests", stamp)
    record_adjustment("E2 point weighting / window", verdict,
                      "; ".join(f"{r.scheme}: {r.rel_change_vs_W0:+.1%}, coverage {r.coverage:.2f}" for r in summ.itertuples()))
    print(summ.to_string())
    return summ


if __name__ == "__main__":
    run()
