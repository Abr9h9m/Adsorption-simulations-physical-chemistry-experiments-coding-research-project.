"""E15c -- follow-ups for the adopted gradient-boosting model (E15). EXPLORATORY; development only.

Same 20 grouped folds of lineage units. Feature sets:
  full          pH, direction, mineral, sorbate, mineral class, sorbate class, conditions (E15)
  no_identity   pH, direction, classes, conditions (no mineral / sorbate names)
  no_conditions pH, direction, mineral, sorbate, classes (no solids, total, loading, I, co-solute, CO2)
For each: held-out edge (grid crossing, as E15b), fraction-sorbed MAE over the curve's measured points (M3),
and paper-level conformal (CV+) 90% edge intervals: prediction +/- the 90% quantile of |edge errors| of
the OTHER units' held-out curves. Coverage and width, overall and by pair size.
"""
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

from phslope.experiments import e15_bakeoff as X
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.e21_conformal_metrics import conformal
from phslope.experiments.integrate import accepted_adjustments, prepare
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment

OUT = os.path.join(EXP_DIR, "E15")
GRID = np.arange(1.0, 13.0001, 0.02)
COND = ["log10_solids", "log10_total", "log10L", "log10_I", "cosolute", "co2"]
SETS = {"full": (X.NUM, X.CAT),
        "no_identity": (X.NUM, ["mineral_class", "sorbate_class"]),
        "no_conditions": ([x for x in X.NUM if x not in COND], X.CAT)}


def feats(P, num, cat):
    return P[num + [c + "_code" for c in cat]].to_numpy(float), np.array([False] * len(num) + [True] * len(cat))


def edge_from_grid(lk, rising):
    cross = np.where(np.sign(lk[:-1]) != np.sign(lk[1:]))[0]
    if len(cross):
        i = cross[0] if rising else cross[-1]
        return GRID[i] + (GRID[i + 1] - GRID[i]) * (-lk[i]) / (lk[i + 1] - lk[i])
    return GRID[0] if (lk[0] > 0) == rising else GRID[-1]


def run_set(P, obs_all, name, seed, n_est):
    num, cat = SETS[name]
    Xall, mask = feats(P, num, cat)
    y = P["log10K"].to_numpy()
    cf = P.drop_duplicates("curve_id").set_index("curve_id")
    rows = []
    for tr, te in GroupKFold(n_splits=20).split(P, groups=P["unit"]):
        m = HistGradientBoostingRegressor(max_iter=n_est, categorical_features=mask, random_state=seed)
        m.fit(Xall[tr], y[tr])
        for cid in P.loc[te, "curve_id"].unique():
            f = cf.loc[[cid]]
            G = pd.concat([f] * len(GRID), ignore_index=True)
            G["pH"] = GRID
            lk = m.predict(feats(G, num, cat)[0])
            o = obs_all.get(cid)
            if o is not None:
                lk_pts = np.interp(o["pH"].to_numpy(), GRID, lk)
                mae = float(np.mean(np.abs(1 / (1 + 10 ** -lk_pts) - o["response"].to_numpy())))
            else:
                mae = np.nan
            rows.append({"curve_id": cid, "unit": f["unit"].iloc[0], "pred_edge": edge_from_grid(lk, f["shape"].iloc[0] == "rising"),
                         "fraction_mae": mae})
    return pd.DataFrame(rows).assign(feature_set=name)


def run():
    ecfg = load_exp_config()
    seed, n_est = ecfg["seed"], ecfg["e15"]["n_estimators"]
    curves, obs = build(purpose="E15c")
    stamp = exp_stamp(extra={"experiment": "E15c"})
    acc = accepted_adjustments()
    c = prepare(curves, obs, ecfg, acc)
    P = X.point_table(c, obs)
    obs_all = {k: g for k, g in obs[obs["curve_id"].isin(c["curve_id"])].groupby("curve_id")}
    R = pd.concat([run_set(P, obs_all, n, seed, n_est) for n in SETS], ignore_index=True)
    R = R.merge(c[["curve_id", "pH_native", "pair_dir", "shape"]], on="curve_id")
    R.to_csv(os.path.join(OUT, "gbm_followup_per_curve.csv"), index=False)
    pair_units = c.groupby("pair_dir")["unit"].nunique()
    R["pair_size"] = R["pair_dir"].map(pair_units).map(lambda n: "1 unit" if n == 1 else ("2-3 units" if n <= 3 else "4+ units"))
    rows, cov = [], []
    for name, d in R.groupby("feature_set"):
        d = conformal(d)
        d["edge_error"] = (d["pred_edge"] - d["pH_native"]).abs()
        d["covered"] = (d["pH_native"] >= d["conf_lo"]) & (d["pH_native"] <= d["conf_hi"])
        rows.append({"feature_set": name, "n": len(d), "median_edge_error": d["edge_error"].median(),
                     "median_edge_error_multi_unit_pairs": d.loc[d["pair_size"] != "1 unit", "edge_error"].median(),
                     "median_edge_error_single_unit_pairs": d.loc[d["pair_size"] == "1 unit", "edge_error"].median(),
                     "median_fraction_mae": d["fraction_mae"].median(),
                     "conformal_coverage": d["covered"].mean(),
                     "conformal_median_width": (d["conf_hi"] - d["conf_lo"]).median()})
        for ps, g in d.groupby("pair_size"):
            cov.append({"feature_set": name, "pair_size": ps, "n": len(g), "coverage": g["covered"].mean()})
    S, C = pd.DataFrame(rows), pd.DataFrame(cov)
    S.to_csv(os.path.join(OUT, "gbm_followup_summary.csv"), index=False)
    C.to_csv(os.path.join(OUT, "gbm_followup_coverage_by_pair_size.csv"), index=False)
    from phslope.report import md_table
    with open(os.path.join(OUT, "SUMMARY.md"), "a", encoding="utf-8") as f:
        f.write("\n## E15c: gradient boosting follow-ups (feature ablation, fraction error, conformal intervals)\n\n"
                "Same 20 grouped folds. Edge errors are on all E1 main-set curves (single- and multi-unit pairs). "
                "Fraction MAE = mean |predicted - observed fraction sorbed| over the curve's measured points (E21/M3: "
                "E1 0.153, B0 0.161, B3 0.163 on multi-unit pairs). Conformal = paper-level CV+.\n\n"
                + md_table(S) + "\n\nCoverage by pair size:\n\n" + md_table(C) + "\n")
    log_run("E15c", "reported", "; ".join(f"{r.feature_set}: {r.median_edge_error:.2f}" for r in S.itertuples()), stamp)
    full = S.set_index("feature_set").loc["full"]
    record_adjustment("E15c GBM conformal intervals", "reported",
                      f"coverage {full['conformal_coverage']:.2f}, width {full['conformal_median_width']:.2f} pH")
    print(S.to_string()); print(C.to_string())


if __name__ == "__main__":
    run()
