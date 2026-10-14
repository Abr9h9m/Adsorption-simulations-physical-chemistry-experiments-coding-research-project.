"""E15b -- edge-position check for the E15 winner (gradient boosting). EXPLORATORY; development only.

Same 20 grouped folds as E15. For every held-out curve, gradient boosting predicts log10 K on a fine pH
grid (0.02 pH) at the curve's own conditions; the native edge is where the prediction crosses 0 (first
crossing in the curve's direction inside 1-13). Compared with the final E1 model's held-out edges from
integration (F/cv_final_model.csv, leave-one-unit-out) and with B0 / B3 on the same curves.
"""
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

from phslope.experiments import e15_bakeoff as X
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.integrate import accepted_adjustments, prepare
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info

OUT = os.path.join(EXP_DIR, "E15")
GRID = np.arange(1.0, 13.0001, 0.02)


def hgb_edges(P, c, seed, n_est):
    gkf = GroupKFold(n_splits=20)
    cat_mask = np.array([False] * len(X.NUM) + [True] * len(X.CAT))
    rows = []
    curve_feats = P.drop_duplicates("curve_id").set_index("curve_id")
    for tr, te in gkf.split(P, groups=P["unit"]):
        m = HistGradientBoostingRegressor(max_iter=n_est, categorical_features=cat_mask, random_state=seed)
        m.fit(X.features(P)[tr], P["log10K"].to_numpy()[tr])
        for cid in P.loc[te, "curve_id"].unique():
            f = curve_feats.loc[[cid]]
            G = pd.concat([f] * len(GRID), ignore_index=True)
            G["pH"] = GRID
            lk = m.predict(X.features(G))
            sign = 1 if f["shape"].iloc[0] == "rising" else -1
            cross = np.where(np.sign(lk[:-1]) != np.sign(lk[1:]))[0]
            if len(cross):
                i = cross[0] if sign > 0 else cross[-1]
                edge = GRID[i] + (GRID[i + 1] - GRID[i]) * (-lk[i]) / (lk[i + 1] - lk[i])
            else:
                edge = GRID[0] if (lk[0] > 0) == (sign > 0) else GRID[-1]
            rows.append({"curve_id": cid, "gbm_edge": edge})
    return pd.DataFrame(rows)


def run():
    ecfg = load_exp_config()
    curves, obs = build(purpose="E15b")
    stamp = exp_stamp(extra={"experiment": "E15b"})
    acc = accepted_adjustments()
    c = prepare(curves, obs, ecfg, acc)
    P = X.point_table(c, obs)
    E = hgb_edges(P, c, ecfg["seed"], ecfg["e15"]["n_estimators"])
    F = pd.read_csv(os.path.join(EXP_DIR, "F", "cv_final_model.csv"))[["curve_id", "pred_edge"]]
    cb = H.prepare(c, "pH_native")
    base = H.baseline_predictions(cb, unit_col="unit").merge(E, on="curve_id").merge(
        F.rename(columns={"pred_edge": "E1_final"}), on="curve_id")
    L = H.long_errors(cb, base, ["gbm_edge", "E1_final", "B0_all_other", "B3_matched_fb"], unit_col="unit")
    multi = set(cb.loc[cb.groupby("grp")["unit"].transform("nunique") >= 2, "curve_id"])
    out = []
    for subset, sel in (("pairs with >= 2 units", L["curve_id"].isin(multi)), ("pairs with 1 unit", ~L["curve_id"].isin(multi))):
        d = L[sel]
        s = H.summarize(d, B=ecfg["harness"]["paper_bootstrap_B"]).assign(subset=subset)
        p = H.paired(d, "gbm_edge", ["E1_final", "B0_all_other", "B3_matched_fb"],
                     B=ecfg["harness"]["paper_bootstrap_B"]).assign(subset=subset)
        out.append((s, p))
    S = pd.concat([o[0] for o in out]); D = pd.concat([o[1] for o in out])
    S.to_csv(os.path.join(OUT, "edge_check_summary.csv"), index=False)
    D.to_csv(os.path.join(OUT, "edge_check_paired.csv"), index=False)
    from phslope.report import md_table
    with open(os.path.join(OUT, "SUMMARY.md"), "a", encoding="utf-8") as f:
        f.write("\n## E15b: edge position from gradient boosting (same grouped folds)\n\n"
                "Gradient boosting predicts log10 K on a fine pH grid at each held-out curve's conditions; its edge is "
                "where that crosses 0. E1_final edges are the integration run's leave-one-unit-out predictions.\n\n"
                + md_table(S[["subset", "model", "n", "median", "median_lo", "median_hi", "within_0_5", "median_paper_weighted"]])
                + "\n\ngbm minus each model (negative = gbm better):\n\n" + md_table(D) + "\n")
    log_run("E15b", "reported", "gbm edge vs E1 final", stamp)
    print(S[["subset", "model", "n", "median", "median_lo", "median_hi"]].to_string())
    print(D[["subset", "baseline", "median_diff", "diff_lo", "diff_hi"]].to_string())


if __name__ == "__main__":
    run()
