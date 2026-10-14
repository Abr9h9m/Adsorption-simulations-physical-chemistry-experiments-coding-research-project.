"""E15 -- model-class bake-off and the inflation from random splits (Addendum 1). EXPLORATORY; development only.

Target: log10 K at each mid-range point of the E1 main-set curves. Models:
  B0   mean line of the same pair (and direction) from other units
  B5   global mean line (same direction) from other units
  E1   final development model (E1 + within-between solids + E8 terms), predicting class + pair effects
  RF   random forest (scikit-learn), HGB histogram gradient boosting (scikit-learn), on point features:
       pH, direction, mineral, sorbate, mineral class, sorbate class (integer codes; HGB treats them as
       categorical), log10 solids, log10 total sorbate, log10 loading, log10 I, co-solute, CO2
Splits: (a) GROUPED: 20 folds of whole lineage units (every model on the same folds; tuning-free models,
so nothing is tuned on held-out units); (b) RANDOM 80/20 split by POINT, 5 seeds (the common but leaky
protocol: points of a held-out curve sit in training). For E1 under the random split, the unit effect is
known (the paper is in training) and is used; that is the leakage the random split allows.
Metric: per held-out curve, RMSE of log10 K over its held-out points; medians compared with the
difference-of-medians interval over units. Decision (pre-declared, experiments.yaml e15).
"""
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import GroupKFold

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.integrate import accepted_adjustments, prepare
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E15")
CAT = ["mineral", "sorbate", "mineral_class", "sorbate_class"]
NUM = ["pH", "falling", "log10_solids", "log10_total", "log10L", "log10_I", "cosolute", "co2"]


def point_table(c, obs):
    o = obs[obs["mid"] & obs["log10K"].notna() & obs["curve_id"].isin(c["curve_id"])][["curve_id", "pH", "log10K"]]
    keep = ["curve_id", "unit", "pair_dir", "shape"] + CAT + [x for x in NUM if x != "pH"]
    P = o.merge(c[keep], on="curve_id")
    for col in CAT:
        P[col + "_code"] = pd.factorize(P[col].fillna("NA"))[0]
    return P.reset_index(drop=True)


def features(P):
    return P[[x for x in NUM] + [c + "_code" for c in CAT]].to_numpy(float)


def fit_predict_trees(P, tr, te, seed, n_est):
    X, y = features(P), P["log10K"].to_numpy()
    rf = RandomForestRegressor(n_estimators=n_est, min_samples_leaf=3, n_jobs=-1, random_state=seed)
    rf.fit(X[tr], y[tr])
    cat_mask = np.array([False] * len(NUM) + [True] * len(CAT))
    hgb = HistGradientBoostingRegressor(max_iter=n_est, categorical_features=cat_mask, random_state=seed)
    hgb.fit(X[tr], y[tr])
    return {"random_forest": rf.predict(X[te]), "gradient_boosting": hgb.predict(X[te])}


def line_baselines(P, curves_tr, te):
    """B0 (pair-direction mean line over other units) and B5 (direction mean line), from training curves."""
    pair = curves_tr.groupby(["pair_dir", "unit"])[["a", "b"]].mean().groupby("pair_dir").mean()
    dirm = curves_tr.groupby("shape")[["a", "b"]].mean()
    t = P.loc[te]
    a0 = t["pair_dir"].map(pair["a"]); b0 = t["pair_dir"].map(pair["b"])
    a5 = t["shape"].map(dirm["a"]); b5 = t["shape"].map(dirm["b"])
    return {"B0_all_other": (a0 + b0 * t["pH"]).to_numpy(), "B5_global_mean": (a5 + b5 * t["pH"]).to_numpy()}


def e1_predict(c_tr, P, te, ecfg, covs, wb, use_unit):
    m = E1.E1Model(ecfg["e1"], True, covs, wb).fit(c_tr)
    t = P.loc[te]
    cc = t.drop_duplicates("curve_id")[["curve_id"]].merge(P_curves_cache["c"], on="curve_id")
    d = cc.copy()
    d["pH_c"] = E1.reference_pH(m.train, d)
    d = E1.add_covariates(d, m.bp)
    for v in m.within_between:
        d[v + "_pm"] = d["pair_dir"].map(m.pair_means[v]).fillna(d[v])
    ok = d[m.level_fixed].notna().all(axis=1)
    d = d[ok]
    ma, _ = m._mean(d, "a")
    mb, _ = m._mean(d, "b")
    if use_unit:
        ua = m.ea["unit"].set_index("level")["blup"]; ub = m.eb["unit"].set_index("level")["blup"]
        ma = ma + d["unit"].map(ua).fillna(0).to_numpy()
        mb = mb + d["unit"].map(ub).fillna(0).to_numpy()
    lines = pd.DataFrame({"curve_id": d["curve_id"].to_numpy(), "ma": ma, "mb": mb, "pH_c": d["pH_c"].to_numpy()})
    t2 = t[["curve_id", "pH"]].reset_index().merge(lines, on="curve_id", how="left").set_index("index").loc[t.index]
    return (t2["ma"] + t2["mb"] * (t2["pH"] - t2["pH_c"])).to_numpy()


P_curves_cache = {}


def per_curve_rmse(P, idx, preds, split, fold):
    rows = []
    t = P.loc[idx, ["curve_id", "unit", "log10K"]].copy()
    for name, yhat in preds.items():
        t["err2"] = (np.asarray(yhat, float) - t["log10K"].to_numpy()) ** 2
        g = t.dropna(subset=["err2"]).groupby(["curve_id", "unit"])["err2"].mean().reset_index()
        g["logK_rmse"] = np.sqrt(g["err2"])
        rows.append(g.assign(model=name, split=split, fold=fold).drop(columns="err2"))
    return pd.concat(rows)


def run(seed=None):
    ecfg = load_exp_config()
    cfg = ecfg["e15"]
    seed = ecfg["seed"] if seed is None else seed
    curves, obs = build(purpose="E15")
    stamp = exp_stamp(extra={"experiment": "E15"})
    write_run_info(OUT, stamp)
    acc = accepted_adjustments()
    c = prepare(curves, obs, ecfg, acc)
    covs = [x for s in acc.values() for x in s.get("covs", [])]
    wb = [x for s in acc.values() for x in s.get("within_between", [])]
    P = point_table(c, obs)
    P_curves_cache["c"] = c
    os.makedirs(OUT, exist_ok=True)
    res = []
    # (a) grouped folds
    gkf = GroupKFold(n_splits=20)
    for k, (tr, te) in enumerate(gkf.split(P, groups=P["unit"])):
        tr_units = set(P.loc[tr, "unit"])
        c_tr = c[c["unit"].isin(tr_units)]
        preds = fit_predict_trees(P, tr, te, seed, cfg["n_estimators"])
        preds.update(line_baselines(P, c_tr, te))
        preds["E1_final"] = e1_predict(c_tr, P, P.index[te], ecfg, covs, wb, use_unit=False)
        res.append(per_curve_rmse(P, P.index[te], preds, "grouped (whole units)", k))
        print(f"E15 grouped fold {k + 1}/20", flush=True)
    # (b) random point splits
    for s in range(cfg["random_split_seeds"]):
        rng = np.random.default_rng(seed + 100 + s)
        te = np.sort(rng.choice(len(P), int(0.2 * len(P)), replace=False))
        tr = np.setdiff1d(np.arange(len(P)), te)
        tr_curves = set(P.loc[tr, "curve_id"])
        c_tr = c[c["curve_id"].isin(tr_curves)]
        preds = fit_predict_trees(P, tr, te, seed, cfg["n_estimators"])
        preds.update(line_baselines(P, c_tr, te))
        preds["E1_final"] = e1_predict(c_tr, P, P.index[te], ecfg, covs, wb, use_unit=True)
        res.append(per_curve_rmse(P, P.index[te], preds, "random 80/20 by point", s))
        print(f"E15 random split {s + 1}", flush=True)
    R = pd.concat(res, ignore_index=True)
    R.to_csv(os.path.join(OUT, "per_curve_rmse.csv"), index=False)
    B = ecfg["harness"]["paper_bootstrap_B"]
    summ, diffs = [], []
    for split, d in R.groupby("split"):
        if split.startswith("random"):          # average a curve's rmse over seeds where it was held out
            d = d.groupby(["curve_id", "unit", "model"])["logK_rmse"].mean().reset_index()
        L = d.rename(columns={"logK_rmse": "metric"})
        s = H.summarize(L, B=B, seed=seed, metric="metric")
        summ.append(s.assign(split=split))
        diffs.append(H.paired(L, "E1_final", ["random_forest", "gradient_boosting", "B0_all_other", "B5_global_mean"],
                              B=B, seed=seed, metric="metric").assign(split=split))
    S, D = pd.concat(summ), pd.concat(diffs)
    piv = S.pivot(index="model", columns="split", values="median")
    piv["inflation (grouped / random)"] = piv["grouped (whole units)"] / piv["random 80/20 by point"]
    flex_beats = D[(D["split"].str.startswith("grouped")) & D["baseline"].isin(["random_forest", "gradient_boosting"])]
    adopt = flex_beats[flex_beats["diff_lo"] > 0]           # E1 minus flexible > 0 -> flexible better
    verdict = ("ADOPT " + ", ".join(adopt["baseline"])) if len(adopt) else "KEEP E1 (no flexible model beats it under grouped validation)"
    S.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    D.to_csv(os.path.join(OUT, "paired.csv"), index=False)
    piv.reset_index().to_csv(os.path.join(OUT, "inflation.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E15 Model bake-off and how much random splits overstate skill", "",
        "**Plain English.** Machine-learning studies on compiled sorption data often test models by hiding a "
        "random 20% of the data points. Points from the same experiment then sit on both sides of the split, so "
        "the model mostly 'remembers' the experiment. We compared that with hiding whole papers, which is what "
        "predicting new work requires. "
        f"Model choice under the honest test: **{verdict}**.", "",
        f"> EXPLORATORY. Development papers only; grouped split = 20 folds of whole lineage units (all models on "
        f"the same folds). Target: log10 K at mid-range points ({len(P):,} points, {P['curve_id'].nunique()} curves). "
        f"Locked set hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## Median per-curve log10 K RMSE, by split", "", md_table(piv.reset_index()), "",
        "An inflation factor above 1 means the random split makes the model look that many times better than it "
        "is for new papers.", "",
        "## Full summaries", "", md_table(S), "",
        "## E1 minus each alternative (negative = E1 better; difference of medians, interval over units)", "",
        md_table(D),
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E15", verdict, "grouped vs random split; RF, HGB, E1, B0, B5", stamp)
    record_adjustment("E15 flexible model class (RF / gradient boosting)", verdict,
                      "; ".join(f"{m}: grouped {r['grouped (whole units)']:.3f}, random {r['random 80/20 by point']:.3f}"
                                for m, r in piv.iterrows()))
    print(verdict)
    print(piv.to_string())


if __name__ == "__main__":
    run()
