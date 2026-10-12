"""stage1.py -- Stage 1: slope curves (spec section 7, Stage 1).

    python -m phslope.stage1 --synthetic        # synthetic check first (must pass)
    python -m phslope.stage1 [--data PATH]      # all clean pH-sweep curves from the real file
    options: --limit N (first N curves, for quick runs), --workers K, --B B, --no-pdf

Per curve: logistic fit + smoothing spline, shape class, choice of primary
model, pairs bootstrap, QC flags, logistic-vs-smoother disagreement.
Primary model = logistic when the curve is a single edge or flat AND the
logistic fit is not poor; otherwise the smoother (bell, multi-step, poor
logistic fit). Point estimates come from the full-data fit; intervals from
the bootstrap of the same model.
"""
import argparse
import os
import zlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from phslope import fit_edge, fit_smooth, qc
from phslope.bootstrap import bootstrap_curve
from phslope.common import REPORTS_DIR, load_config, load_thresholds, run_stamp, write_stamp
from phslope.library import build_library, save_library
from phslope.slope import edge_summary, make_grid, observed_mask, on_grid


def curve_seed(global_seed, curve_id):
    """Stable per-curve seed: same curve, same seed, regardless of run order."""
    return (int(global_seed) * 1_000_003 + zlib.crc32(str(curve_id).encode())) % (2 ** 32)


def _nan_arrays(G, B):
    nan = np.full(G, np.nan)
    return {"G": nan, "lower": nan, "upper": nan, "mask": np.zeros(G, bool), "G_logistic": nan,
            "G_spline": nan, "fitted": nan, "F_logistic": nan, "F_spline": nan, "draws": np.full((B, G), np.nan, np.float32)}


def process_curve(curve_id, pH, y, config, thr, grid, seed, unit_mismatch=False, extra=None):
    """Everything Stage 1 does to one curve. Returns {"meta": dict, "arrays": dict}."""
    order = np.argsort(pH)
    pH, y = np.asarray(pH, float)[order], np.asarray(y, float)[order]
    B, G = config["bootstrap"]["B"], len(grid)
    p_lo, p_hi = float(pH.min()), float(pH.max())
    meta = {"curve_id": curve_id, **(extra or {}), "n_points": len(pH), "pH_min": p_lo, "pH_max": p_hi,
            "pH_span": p_hi - p_lo, "unit_mismatch": bool(unit_mismatch)}
    mask = observed_mask(grid, p_lo, p_hi)

    logit = spline = None
    errors = []
    try:
        logit = fit_edge.fit_logistic(pH, y, config["fit"], seed=seed)
    except fit_edge.EdgeFitError as e:
        errors.append(f"logistic: {e}")
    try:
        spline = fit_smooth.fit_spline(pH, y, config["smooth"])
    except fit_smooth.SmoothFitError as e:
        errors.append(f"spline: {e}")
    meta["fit_errors"] = "; ".join(errors)

    if logit is None and spline is None:
        info = dict(meta, shape="unclassified", fit_failed=True)
        flags = qc.flags_for(info, thr)
        meta.update(shape="unclassified", primary_model="none", qc_flags=";".join(flags), in_core_library=False)
        arr = _nan_arrays(G, B)
        arr["mask"] = mask
        return {"meta": meta, "arrays": arr}

    dense = np.linspace(p_lo, p_hi, config["shape"]["dense_n"])
    if spline is not None:
        shape = qc.shape_class(dense, fit_smooth.predict(spline, dense), fit_smooth.slope(spline, dense),
                               config["shape"])
    else:
        shape = qc.shape_class(dense, fit_edge.predict(logit, dense), fit_edge.slope(logit, dense),
                               config["shape"])

    rep = qc.replicate_scatter(pH, y, config["smooth"]["ph_decimals"], thr["replicate_min_groups"])
    limit = qc.poor_fit_limit(rep, thr)
    use_logit = logit is not None and (spline is None or (shape in ("rising", "falling", "flat")
                                                           and logit["rmse"] <= limit))
    primary = "logistic" if use_logit else "spline"
    pfit = logit if use_logit else spline
    mod = fit_edge if use_logit else fit_smooth

    if use_logit:
        edge = {"edge_pH": logit["p50"], "height": logit["hi"] - logit["lo"], "width": logit["w"],
                "max_slope": float(fit_edge.slope(logit, logit["p50"]))}
    spline_edge = None
    if spline is not None:
        spline_edge = edge_summary(lambda p: fit_smooth.predict(spline, p), lambda p: fit_smooth.slope(spline, p),
                                   p_lo, p_hi, config["shape"]["dense_n"], config["shape"]["min_step"])
    if not use_logit:
        edge = dict(spline_edge)
    if shape == "flat":
        edge["edge_pH"] = np.nan          # a flat curve has no edge position

    boot = bootstrap_curve(pH, y, logit, spline, grid, mask, config, B, seed, spline_edge=spline_edge)
    pb = boot[primary]
    edge_ci = pb["edge_pct"][2] - pb["edge_pct"][0]

    info = dict(meta, shape=shape, edge_pH=edge["edge_pH"], pH=pH, rmse=pfit["rmse"], rep_scatter=rep,
                edge_ci_width=edge_ci, boot_fail_frac=pb["fail_frac"], fit_failed=False)
    flags = qc.flags_for(info, thr)

    G_l = on_grid(lambda p: fit_edge.slope(logit, p), grid, mask) if logit else np.full(G, np.nan)
    G_s = on_grid(lambda p: fit_smooth.slope(spline, p), grid, mask) if spline else np.full(G, np.nan)
    n_disagree = 0
    if logit and spline:
        hw = lambda o: (o["slope_pct"][2] - o["slope_pct"][0]) / 2
        tol = np.fmax(hw(boot["logistic"]), hw(boot["spline"]))
        n_disagree = int(np.nansum(np.abs(G_l - G_s) > tol))

    meta.update({
        "shape": shape, "primary_model": primary, "qc_flags": ";".join(flags),
        "in_core_library": qc.in_core_library(flags, shape),
        "edge_pH": edge["edge_pH"], "edge_lo": pb["edge_pct"][0] if shape != "flat" else np.nan,
        "edge_hi": pb["edge_pct"][2] if shape != "flat" else np.nan,
        "width": edge["width"], "height": edge["height"], "max_slope": edge["max_slope"],
        "rmse": pfit["rmse"], "rep_scatter": rep, "poor_fit_limit": limit,
        "boot_fail_frac": pb["fail_frac"],
        "logistic_lo": logit["lo"] if logit else np.nan, "logistic_hi": logit["hi"] if logit else np.nan,
        "logistic_p50": logit["p50"] if logit else np.nan, "logistic_w": logit["w"] if logit else np.nan,
        "logistic_rmse": logit["rmse"] if logit else np.nan,
        "spline_lam": spline["lam"] if spline else np.nan, "spline_rmse": spline["rmse"] if spline else np.nan,
        "n_disagree_points": n_disagree,
    })
    arrays = {"G": G_l if use_logit else G_s, "lower": pb["slope_pct"][0], "upper": pb["slope_pct"][2],
              "mask": mask, "G_logistic": G_l, "G_spline": G_s,
              "fitted": on_grid(lambda p: mod.predict(pfit, p), grid, mask),
              "F_logistic": on_grid(lambda p: fit_edge.predict(logit, p), grid, mask) if logit else np.full(G, np.nan),
              "F_spline": on_grid(lambda p: fit_smooth.predict(spline, p), grid, mask) if spline else np.full(G, np.nan),
              "draws": pb["slopes"].astype(np.float32)}
    return {"meta": meta, "arrays": arrays}


def _work(job):
    return process_curve(**job)


def run_curves(jobs, workers):
    if workers <= 1:
        return [_work(j) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_work, jobs, chunksize=8))


def make_jobs(curve_table, obs, config, thr, grid, extra_cols=()):
    seed0 = config["seeds"]["global"]
    groups = {cid: g for cid, g in obs.groupby("curve_id", sort=False)}
    jobs = []
    for row in curve_table.itertuples(index=False):
        g = groups[row.curve_id]
        jobs.append(dict(curve_id=row.curve_id, pH=g["pH"].to_numpy(), y=g["response"].to_numpy(),
                         config=config, thr=thr, grid=grid, seed=curve_seed(seed0, row.curve_id),
                         unit_mismatch=bool(getattr(row, "unit_mismatch", False)),
                         extra={c: getattr(row, c) for c in extra_cols}))
    return jobs


# ---------------------------------------------------------------- synthetic --

def synthetic_scores(lib, curves, truths):
    """Per synthetic curve: slope error (RMSE over observed grid points / range of
    the true slope there), whether the 95% edge interval covers the true edge,
    and the shape the classifier assigned."""
    from phslope.synth import truth_response, truth_slope
    rows = []
    meta = lib["meta"].set_index("curve_id")
    for i, cid in enumerate(lib["curve_ids"]):
        t = truths[cid]
        m = lib["mask"][i]
        true_g = truth_slope(t, lib["grid"][m])
        est = lib["G"][i][m]
        rng_ = true_g.max() - true_g.min() if m.sum() else np.nan
        err = np.sqrt(np.nanmean((est - true_g) ** 2)) / rng_ if rng_ and rng_ > 1e-9 else np.nan
        # The true edge uses the same definition as the estimate (half-way point of
        # the main move inside the observed range); for a logistic that is p50.
        true_edge = np.nan
        if t["shape"] != "flat":
            true_edge = edge_summary(lambda p: truth_response(t, p), lambda p: truth_slope(t, p),
                                     meta.loc[cid, "pH_min"], meta.loc[cid, "pH_max"])["edge_pH"]
        lo, hi = meta.loc[cid, "edge_lo"], meta.loc[cid, "edge_hi"]
        rows.append({"curve_id": cid, "true_shape": t["shape"], "shape": meta.loc[cid, "shape"],
                     "primary_model": meta.loc[cid, "primary_model"], "slope_error": err,
                     "true_edge": true_edge, "edge_pH": meta.loc[cid, "edge_pH"],
                     "edge_covered": bool(lo <= true_edge <= hi) if np.isfinite(true_edge) and np.isfinite(lo)
                     else np.nan, "qc_flags": meta.loc[cid, "qc_flags"]})
    return pd.DataFrame(rows)


def run_synthetic(config, thr, out_dir, workers, B=None, n_per_shape=40):
    from phslope.synth import known_edge_set
    if B:
        config = {**config, "bootstrap": {**config["bootstrap"], "B": B}}
    curves, obs, truths = known_edge_set(n_per_shape=n_per_shape, seed=config["seeds"]["global"])
    grid = make_grid(config)
    jobs = make_jobs(curves, obs, config, thr, grid, extra_cols=("shape",))
    for j in jobs:
        j["extra"] = {"true_shape": j["extra"]["shape"]}
    lib = build_library(run_curves(jobs, workers), grid)
    scores = synthetic_scores(lib, curves, truths)
    return lib, scores, obs


# ---------------------------------------------------------------- real data --

def load_real(data_file, config):
    from phslope.census import clean_curves, pair_table
    from phslope.curves import build_curves
    from phslope.load import load_observations
    obs, path = load_observations(data_file, config)
    curves, curve_obs = build_curves(obs, config)
    clean = clean_curves(curves).copy()
    pairs = pair_table(curves, load_thresholds()["stage0"])
    passing = set(map(tuple, pairs.loc[pairs["passes"], ["mineral", "sorbate"]].to_numpy()))
    clean["in_census_set"] = [(m, s) in passing for m, s in zip(clean["mineral"], clean["sorbate"])]
    return clean, curve_obs, path


META_COLS = ("reference", "mineral", "sorbate", "electrolyte_sig", "cosolutes", "has_cosolute", "co2_present",
             "ionic_strength", "total_sorbate_mol_L", "solids_g_L", "solids_m2_L", "temp", "mineralsites",
             "in_census_set")


def main():
    ap = argparse.ArgumentParser(description="Stage 1: slope curves.")
    ap.add_argument("--data")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--B", type=int, help="bootstrap resamples (default from config)")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    from phslope import report
    config, thr_all = load_config(), load_thresholds()
    thr = thr_all["qc"]
    workers = args.workers or config["stage1"]["workers"]
    if args.B:
        config["bootstrap"]["B"] = args.B

    if args.synthetic:
        out_dir = args.out or os.path.join(REPORTS_DIR, "stage1_synthetic")
        stamp = run_stamp("synthetic: synth.known_edge_set")
        write_stamp(out_dir, stamp)
        lib, scores, obs = run_synthetic(config, thr, out_dir, workers)
        save_library(lib, os.path.join(out_dir, "library"), include_draws=False)
        scores.to_csv(os.path.join(out_dir, "synthetic_scores.csv"), index=False)
        report.stage1_synthetic_summary(out_dir, lib, scores, thr_all, stamp)
        return

    out_dir = args.out or os.path.join(REPORTS_DIR, "stage1")
    clean, curve_obs, path = load_real(args.data, config)
    if args.limit:
        clean = clean.head(args.limit)
    stamp = run_stamp(path)
    write_stamp(out_dir, stamp)
    grid = make_grid(config)
    jobs = make_jobs(clean, curve_obs, config, thr, grid, extra_cols=META_COLS)
    print(f"Stage 1: {len(jobs)} curves, B={config['bootstrap']['B']}, {workers} workers")
    lib = build_library(run_curves(jobs, workers), grid)
    save_library(lib, os.path.join(out_dir, "library"))
    report.stage1_real_summary(out_dir, lib, thr_all, stamp)
    if config["stage1"]["diagnostics_pdf"] and not args.no_pdf:
        report.diagnostics_pdf(os.path.join(out_dir, "diagnostics.pdf"), lib, curve_obs)


if __name__ == "__main__":
    main()
