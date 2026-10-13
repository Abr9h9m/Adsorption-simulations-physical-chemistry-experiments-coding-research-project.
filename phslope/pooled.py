"""pooled.py -- what happens if curves are pooled instead of fitted one by one? (EXPLORATORY)

Not in the spec; added at Samuel's request (2026-10-12). Two pooling modes:

  pair_band   all points of a mineral-sorbate pair within one ionic-strength band
              (bands from schemes.yaml), across Sets and references
  pair_all    all points of a mineral-sorbate pair, whatever the ionic strength

Each pool goes through the same Stage 1 processing as a single curve (logistic
+ smoother, shape class, QC flags, point bootstrap). Because points from the same
paper are not independent, the edge interval is ALSO computed by a cluster
bootstrap that resamples whole references; that interval is the honest one.

Comparison with the single-curve library, per pool:
  edge_shift     pooled edge - median edge of the pool's own core curves (pH)
  width_ratio    pooled width / median width of those curves (> 1 = pooling smears the edge)
  resid_ref_R2   share of the pooled fit's residual variance that lies between references
                 (how much of the scatter around the pooled curve is "which paper")
Inputs: clean curves (Stage 0 rule), not only core curves, so pooling gets the
data that Stage 1 QC rejected.
"""
import os

import numpy as np
import pandas as pd

from phslope import fit_edge
from phslope.load import pair_label
from phslope.stage1 import curve_seed, process_curve

EDGE_SHAPES = ("rising", "falling", "bell", "multi_step")


def band_labels(ionic_strength, bands):
    return pd.cut(ionic_strength, bins=bands["bins"], labels=bands["labels"], right=False).astype(object)


def define_pools(curves, curve_obs, mode, bands, cfg):
    """Returns (pools, pooled_obs). pools: one row per pool with its curves and the spread of
    conditions inside it. pooled_obs: pool_id, pH, response, reference, curve_id."""
    c = curves.copy()
    c["band"] = band_labels(c["ionic_strength"], bands)
    keys = ["mineral", "sorbate"] + (["band"] if mode == "pair_band" else [])
    c = c.dropna(subset=keys)
    obs = curve_obs.merge(c[["curve_id"] + keys], on="curve_id")
    rows, parts = [], []
    for k, g in c.groupby(keys):
        k = k if isinstance(k, tuple) else (k,)
        pid = pair_label(k[0], k[1]) + (f" | {k[2]}" if mode == "pair_band" else "")
        o = obs[obs["curve_id"].isin(g["curve_id"])]
        if len(g) < cfg["min_curves"] or len(o) < cfg["min_points"]:
            continue
        tot = np.log10(g["total_sorbate_mol_L"].where(g["total_sorbate_mol_L"] > 0))
        rows.append({
            "pool_id": pid, "mode": mode, "mineral": k[0], "sorbate": k[1],
            "band": k[2] if mode == "pair_band" else "all",
            "n_curves": len(g), "n_references": g["reference"].nunique(), "n_points": len(o),
            "I_min": g["ionic_strength"].min(), "I_max": g["ionic_strength"].max(),
            "I_span_decades": np.log10(g["ionic_strength"].max() / g["ionic_strength"].min())
            if (g["ionic_strength"] > 0).all() else np.nan,
            "n_I_bands": g["band"].nunique(),
            "total_sorbate_span_decades": tot.max() - tot.min(),
            "solids_span_ratio": g["solids_g_L"].max() / g["solids_g_L"].min() if (g["solids_g_L"] > 0).all() else np.nan,
            "co2_fraction": g["co2_present"].mean(), "cosolute_fraction": g["has_cosolute"].mean(),
            "curve_ids": ";".join(g["curve_id"]),
        })
        parts.append(o.assign(pool_id=pid)[["pool_id", "pH", "response", "Reference", "curve_id"]])
    pools = pd.DataFrame(rows)
    pooled_obs = pd.concat(parts, ignore_index=True).rename(columns={"Reference": "reference"}) if parts else \
        pd.DataFrame(columns=["pool_id", "pH", "response", "reference", "curve_id"])
    return pools, pooled_obs


def cluster_bootstrap_edge(pH, y, refs, logit_fit, fit_cfg, B, seed):
    """Resample whole references with replacement, refit the logistic. Returns 2.5/50/97.5
    percentiles of p50 and w, and the failure fraction. A single-reference pool returns NaN."""
    u = np.unique(refs)
    nan3 = np.full(3, np.nan)
    if len(u) < 2 or logit_fit is None:
        return {"edge_pct": nan3, "width_pct": nan3, "fail_frac": np.nan, "n_refs": len(u)}
    idx = {r: np.where(refs == r)[0] for r in u}
    rng = np.random.default_rng(seed)
    x0 = fit_edge.params_vector(logit_fit)
    p50, w, fails = [], [], 0
    for b in range(B):
        pick = np.concatenate([idx[r] for r in rng.choice(u, len(u), replace=True)])
        try:
            f = fit_edge.fit_logistic(pH[pick], y[pick], fit_cfg, n_starts=fit_cfg["bootstrap_starts"],
                                      seed=int(seed) + b, x0=x0)
            p50.append(f["p50"])
            w.append(f["w"])
        except fit_edge.EdgeFitError:
            fails += 1
    pct = lambda v: np.percentile(v, [2.5, 50, 97.5]) if v else nan3
    return {"edge_pct": pct(p50), "width_pct": pct(w), "fail_frac": fails / B, "n_refs": len(u)}


def residual_reference_r2(y, pred, refs):
    """Between-reference share of residual variance (one-way, residuals about their mean)."""
    r = np.asarray(y, float) - np.asarray(pred, float)
    tot = np.sum((r - r.mean()) ** 2)
    if tot == 0 or len(np.unique(refs)) < 2:
        return np.nan
    df = pd.DataFrame({"r": r, "g": refs})
    m = df.groupby("g")["r"].agg(["mean", "size"])
    return float(np.sum(m["size"] * (m["mean"] - r.mean()) ** 2) / tot)


def process_pool(job):
    """Stage 1 processing of a pool, plus the reference-cluster bootstrap and residual study share."""
    refs = job.pop("refs")
    B_cluster = job.pop("B_cluster")
    res = process_curve(**job)
    m = res["meta"]
    pH, y = np.asarray(job["pH"], float), np.asarray(job["y"], float)
    logit = None
    if np.isfinite(m.get("logistic_p50", np.nan)):
        logit = {k: m[f"logistic_{k}"] for k in ("lo", "hi", "p50", "w")}
    cb = cluster_bootstrap_edge(pH, y, refs, logit, job["config"]["fit"], B_cluster, job["seed"])
    m["cluster_edge_lo"], m["cluster_edge_hi"] = cb["edge_pct"][0], cb["edge_pct"][2]
    m["cluster_width_lo"], m["cluster_width_hi"] = cb["width_pct"][0], cb["width_pct"][2]
    m["cluster_fail_frac"] = cb["fail_frac"]
    if logit is not None:
        m["resid_ref_R2"] = residual_reference_r2(y, fit_edge.predict(logit, pH), refs)
    else:
        m["resid_ref_R2"] = np.nan
    return res


def compare_with_curves(pool_meta, pools, lib_meta):
    """Per pool: pooled edge/width vs the pool's own core single-curve fits."""
    core = lib_meta[lib_meta["in_core_library"].astype(bool) & lib_meta["shape"].isin(EDGE_SHAPES)]
    core = core.set_index("curve_id")
    rows = []
    pm = pool_meta.set_index("curve_id")
    for p in pools.itertuples():
        ids = [i for i in p.curve_ids.split(";") if i in core.index]
        sub = core.loc[ids] if ids else core.iloc[:0]
        r = pm.loc[p.pool_id]
        med_edge = sub["edge_pH"].median() if len(sub) else np.nan
        med_w = sub["width"].median() if len(sub) else np.nan
        rows.append({
            "pool_id": p.pool_id, "n_core_curves": len(sub),
            "curves_edge_median": med_edge,
            "curves_edge_iqr": (sub["edge_pH"].quantile(.75) - sub["edge_pH"].quantile(.25)) if len(sub) > 1 else np.nan,
            "curves_width_median": med_w,
            "curves_majority_shape": sub["shape"].mode().iloc[0] if len(sub) else "",
            "edge_shift": r["edge_pH"] - med_edge,
            "width_ratio": r["width"] / med_w if med_w and np.isfinite(med_w) else np.nan,
        })
    return pd.DataFrame(rows)


def run(curves, curve_obs, lib_meta, config, thr, bands, workers, modes=("pair_band", "pair_all")):
    from phslope.slope import make_grid
    pcfg = config["pooled"]
    cfg = {**config, "smooth": {**config["smooth"], "ph_decimals": pcfg["ph_decimals"]},
           "bootstrap": {**config["bootstrap"], "B": pcfg["point_bootstrap_B"]}}
    grid = make_grid(cfg)
    out = {}
    for mode in modes:
        pools, pobs = define_pools(curves, curve_obs, mode, bands, pcfg)
        jobs = []
        for p in pools.itertuples():
            o = pobs[pobs["pool_id"] == p.pool_id]
            jobs.append(dict(curve_id=p.pool_id, pH=o["pH"].to_numpy(), y=o["response"].to_numpy(), config=cfg,
                             thr=thr, grid=grid, seed=curve_seed(config["seeds"]["global"], p.pool_id),
                             extra={"mode": mode}, refs=o["reference"].to_numpy(),
                             B_cluster=pcfg["cluster_bootstrap_B"]))
        results = run_curves_pool(jobs, workers)
        meta = pd.DataFrame([r["meta"] for r in results])
        comp = compare_with_curves(meta, pools, lib_meta) if len(pools) else pd.DataFrame()
        # the fit's own n_points / pH range duplicate the pool columns; keep the pool's
        dup = [c for c in meta.columns if c in pools.columns and c != "pool_id"] + ["mode"]
        table = pools.drop(columns="curve_ids").merge(meta.drop(columns=dup), left_on="pool_id",
                                                      right_on="curve_id", how="left").merge(comp, on="pool_id")
        out[mode] = {"pools": pools, "obs": pobs, "table": table, "results": results}
    return out


def _work_pool(job):
    return process_pool(job)


def run_curves_pool(jobs, workers):
    if workers <= 1:
        return [_work_pool(j) for j in jobs]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_work_pool, jobs, chunksize=2))


def main():
    import argparse
    from phslope import report
    from phslope.common import REPORTS_DIR, load_config, load_thresholds, run_stamp, write_stamp
    from phslope.library import load_library
    from phslope.schemes import load_schemes
    from phslope.stage1 import load_real

    ap = argparse.ArgumentParser(description="EXPLORATORY: pooled-pair curves vs single curves.")
    ap.add_argument("--data")
    ap.add_argument("--library", default=os.path.join(REPORTS_DIR, "stage1", "library"))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(REPORTS_DIR, "pooled"))
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()

    config, thr_all = load_config(), load_thresholds()
    os.makedirs(args.out, exist_ok=True)
    clean, curve_obs, path = load_real(args.data, config)
    stamp = run_stamp(path)
    write_stamp(args.out, stamp)
    lib = load_library(args.library)
    bands = load_schemes()["condition_schemes"]["ionic_strength_band"]
    res = run(clean, curve_obs, lib["meta"], config, thr_all["qc"], bands, args.workers)
    for mode, r in res.items():
        r["table"].to_csv(os.path.join(args.out, f"pools_{mode}.csv"), index=False)
    report.pooled_summary(args.out, res, stamp, bands)
    if not args.no_pdf:
        report.pooled_pdf(os.path.join(args.out, "pooled_diagnostics.pdf"), res)


if __name__ == "__main__":
    main()
