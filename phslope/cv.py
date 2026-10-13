"""cv.py -- held-out evaluation for Stage 3 (spec section 5).

Validation unit is always a whole group, never a point (spec ground rule 4):
  study    leave one reference out
  pair     leave one mineral-sorbate pair out
  mineral  leave one mineral out
  sorbate  leave one sorbate out

Per held-out curve (spec section 5):
  p50_error         |predicted - observed edge position| (pH)
  curve_error       RMS difference between predicted and observed slope over the curve's
                    observed grid points, weighted by inverse bootstrap variance, divided by
                    the observed slope range
  shape_correct     predicted single-edge direction (sign of height) equals the observed shape
  sign_correct      predicted slope sign equals observed over the edge region (observed grid
                    points with |slope| >= 25% of the curve's peak |slope|), majority rule
  interval_coverage fraction of observed slope values inside the 90% prediction band
  p50_covered       observed edge inside the 90% edge interval
Model-vs-baseline differences: paired over curves both models predicted; 95% intervals by
resampling held-out STUDIES (not curves).
"""
import numpy as np
import pandas as pd

from phslope import transfer

LEVELS = {"study": "reference", "pair": "pair", "mineral": "mineral", "sorbate": "sorbate"}


def curve_metrics(g_pred, lo, hi, g_obs, mask, low, up, edge_pred, edge_obs, edge_q, h_pred, shape_obs):
    m = mask & np.isfinite(g_obs) & np.isfinite(g_pred)
    if m.sum() == 0:
        return {}
    obs, pred = g_obs[m], g_pred[m]
    rng_ = obs.max() - obs.min()
    sd = (up[m] - low[m]) / 3.92
    w = 1 / np.where(np.isfinite(sd) & (sd > 0), sd, np.nanmedian(sd[sd > 0]) if (sd > 0).any() else 1) ** 2
    curve_err = np.sqrt(np.sum(w * (pred - obs) ** 2) / np.sum(w)) / rng_ if rng_ > 0 else np.nan
    region = np.abs(obs) >= 0.25 * np.abs(obs).max()
    sign_ok = np.mean(np.sign(pred[region]) == np.sign(obs[region])) > 0.5 if region.any() else np.nan
    pred_shape = "rising" if h_pred > 0 else "falling"
    return {"p50_error": abs(edge_pred - edge_obs), "curve_error": curve_err,
            "shape_correct": pred_shape == shape_obs, "sign_correct": sign_ok,
            "interval_coverage": float(np.mean((obs >= lo[m]) & (obs <= hi[m]))),
            "p50_covered": bool(abs(edge_pred - edge_obs) <= edge_q)}


def _conformal(model_name, warp_oof, train, R_train, shapes_fn, D, tr_idx, q=0.9):
    """90% quantiles of |edge residual| and, per grid point, |slope residual| from leave-study-out
    predictions inside the training set."""
    ok = warp_oof.notna().all(axis=1).to_numpy()
    if ok.sum() < 5:
        return np.nan, np.full(len(D["grid"]), np.nan)
    edge_q = np.quantile(np.abs(warp_oof["edge_pH"].to_numpy()[ok] - train["edge_pH"].to_numpy()[ok]), q)
    res = []
    for k in np.where(ok)[0]:
        i = tr_idx[k]
        row = warp_oof.iloc[k]
        g = transfer.rebuild(row["edge_pH"], row["log_width"], row["height"], shapes_fn(k), D["u"], D["grid"])
        r = np.abs(g - D["G"][i])
        r[~D["mask"][i]] = np.nan
        res.append(r)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            slope_q = np.nanquantile(np.array(res), q, axis=0)
    return edge_q, np.nan_to_num(slope_q, nan=np.nanmax(slope_q) if np.isfinite(slope_q).any() else 0.0)


def run_cv(D, level, models, X_by_model, fpca_cfg=None, min_test=1):
    """D: dict with t (DataFrame), R (registered shapes), G, lower, upper, mask, grid, u.
    models: list of model names. X_by_model: name -> feature matrix (n x p, NaN rows dropped) or None.
    Returns per-curve DataFrame: one row per (held-out curve, model)."""
    t = D["t"]
    groups = t[LEVELS[level]].to_numpy()
    rows = []
    for gval in pd.unique(groups):
        te_all = np.where(groups == gval)[0]
        tr_all = np.where(groups != gval)[0]
        if len(te_all) < min_test or len(np.unique(t["reference"].to_numpy()[tr_all])) < 3:
            continue
        shapes = transfer.class_cell_shapes(t.iloc[tr_all], D["R"][tr_all])
        for name in models:
            X = X_by_model.get(name)
            complete = np.ones(len(t), bool) if X is None else np.isfinite(X).all(axis=1)
            tr, te = tr_all[complete[tr_all]], te_all[complete[te_all]]
            if len(te) == 0 or len(tr) < 10:
                continue
            train, test = t.iloc[tr], t.iloc[te]
            Xtr = None if X is None else X[tr]
            Xte = None if X is None else X[te]
            model = make_model(name).fit(train, Xtr)
            warp = model.predict(test, Xte)
            oof = model.oof(train, Xtr)
            shape_model = None
            if name.split("@")[0] == "version_b":
                shape_model = transfer.ShapeScores(fpca_cfg).fit(train, D["R"][tr], Xtr)
                test_shapes = shape_model.predict_shapes(Xte, len(D["u"]))
                train_shapes = shape_model.predict_shapes(Xtr, len(D["u"]))
                shape_te = lambda k: test_shapes[k]
                shape_tr = lambda k: train_shapes[k]
            else:
                mc, sc = test["mineral_class"].to_numpy(), test["sorbate_class"].to_numpy()
                shape_te = lambda k: transfer.lookup_shape(shapes, mc[k], sc[k])
                mtr, stt = train["mineral_class"].to_numpy(), train["sorbate_class"].to_numpy()
                shape_tr = lambda k: transfer.lookup_shape(shapes, mtr[k], stt[k])
            edge_q, slope_q = _conformal(name, oof, train, D["R"][tr], shape_tr, D, tr)
            for k, i in enumerate(te):
                w = warp.iloc[k]
                if not np.isfinite(w.to_numpy(float)).all():
                    continue
                g = transfer.rebuild(w["edge_pH"], w["log_width"], w["height"], shape_te(k), D["u"], D["grid"])
                met = curve_metrics(g, g - slope_q, g + slope_q, D["G"][i], D["mask"][i], D["lower"][i],
                                    D["upper"][i], w["edge_pH"], t["edge_pH"].iloc[i], edge_q, w["height"],
                                    t["shape"].iloc[i])
                if met:
                    rows.append({"level": level, "held_out": gval, "curve_id": t["curve_id"].iloc[i],
                                 "reference": t["reference"].iloc[i], "model": name,
                                 "pred_edge": w["edge_pH"], "obs_edge": t["edge_pH"].iloc[i], **met})
    return pd.DataFrame(rows)


def make_model(name):
    """`name` may carry a feature-set suffix, e.g. 'version_a@properties'."""
    name = name.split("@")[0]
    return {"global_mean": transfer.GlobalMean, "version_a": transfer.VersionA,
            "version_b": transfer.VersionA, "edge_position_rule": transfer.EdgePositionRule,
            "sorbate_class_mean": lambda: transfer.ClassMean("sorbate_class"),
            "mineral_class_mean": lambda: transfer.ClassMean("mineral_class")}[name]()


def summarize(per_curve):
    g = per_curve.groupby(["level", "model"])
    return pd.DataFrame({
        "n_curves": g.size(), "n_groups": g["held_out"].nunique(),
        "median_p50_error": g["p50_error"].median(),
        "p50_error_q25": g["p50_error"].quantile(.25), "p50_error_q75": g["p50_error"].quantile(.75),
        "median_curve_error": g["curve_error"].median(),
        "shape_correct": g["shape_correct"].mean(), "sign_correct": g["sign_correct"].mean(),
        "interval_coverage": g["interval_coverage"].mean(), "p50_coverage": g["p50_covered"].mean(),
    }).reset_index()


def paired_differences(per_curve, model, baselines, B=1000, seed=0):
    """Median difference (model - baseline) in p50_error and curve_error over curves both predicted,
    with 95% intervals from resampling held-out studies."""
    rng = np.random.default_rng(seed)
    rows = []
    for level, d in per_curve.groupby("level"):
        a = d[d["model"] == model].set_index("curve_id")
        for base in baselines:
            b = d[d["model"] == base].set_index("curve_id")
            common = a.index.intersection(b.index)
            if not len(common):
                continue
            diff = pd.DataFrame({"reference": a.loc[common, "reference"],
                                 "p50": a.loc[common, "p50_error"] - b.loc[common, "p50_error"],
                                 "curve": a.loc[common, "curve_error"] - b.loc[common, "curve_error"]})
            refs = diff["reference"].unique()
            by_ref = {r: diff[diff["reference"] == r] for r in refs}
            boot = []
            for _ in range(B):
                s = pd.concat([by_ref[r] for r in rng.choice(refs, len(refs))])
                boot.append((s["p50"].median(), s["curve"].median()))
            boot = np.array(boot)
            rows.append({"level": level, "model": model, "baseline": base, "n_common": len(common),
                         "p50_error_diff": diff["p50"].median(),
                         "p50_diff_lo": np.nanpercentile(boot[:, 0], 2.5), "p50_diff_hi": np.nanpercentile(boot[:, 0], 97.5),
                         "curve_error_diff": diff["curve"].median(),
                         "curve_diff_lo": np.nanpercentile(boot[:, 1], 2.5), "curve_diff_hi": np.nanpercentile(boot[:, 1], 97.5)})
    return pd.DataFrame(rows)
