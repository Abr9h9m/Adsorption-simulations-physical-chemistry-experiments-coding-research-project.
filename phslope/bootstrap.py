"""bootstrap.py -- pairs bootstrap for the edge fit and the smoother (spec 4.4).

Each resample draws n (pH, response) pairs with replacement, refits, and
re-evaluates the slope on the curve's own observed grid points. Logistic
refits start from the full-data fit plus (bootstrap_starts - 1) random starts;
the smoother keeps the full-data penalty lam (no CV inside the bootstrap).
Failures are counted, never hidden.
"""
import warnings

import numpy as np

from phslope import fit_edge, fit_smooth
from phslope.slope import edge_summary, on_grid

PCTS = (2.5, 50, 97.5)


def _pct(draws):
    ok = np.isfinite(draws).any(axis=1) if draws.ndim == 2 else np.isfinite(draws)
    if not ok.any():
        return np.full((3,) + draws.shape[1:], np.nan)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice")   # unobserved grid columns
        return np.nanpercentile(draws[ok], PCTS, axis=0)


def bootstrap_curve(pH, y, logit_fit, spline_fit, grid, mask, config, B, seed, spline_edge=None):
    """Returns dict with, for each model ('logistic', 'spline') that had a full fit:
       slopes (B x grid, NaN where failed or unobserved), edge (B), height (B),
       width (B), n_fail, and percentile summaries slope_pct (3 x grid), edge_pct,
       height_pct, width_pct.
    spline_edge: the full-fit smoother edge_summary. Each draw's edge is where the
    draw crosses the full-fit half-way level, nearest the full-fit edge and within
    +/- edge_track_window pH, so bell and two-step curves do not jump between
    edges. A draw with no such crossing has a NaN edge (not a failed fit)."""
    pH, y = np.asarray(pH, float), np.asarray(y, float)
    rng = np.random.default_rng(seed)
    n, G = len(pH), len(grid)
    p_lo, p_hi = pH.min(), pH.max()
    dense_n = config["shape"]["dense_n"]
    out = {}
    models = {}
    if logit_fit is not None:
        models["logistic"] = logit_fit
    if spline_fit is not None:
        models["spline"] = spline_fit
    for name in models:
        out[name] = {"slopes": np.full((B, G), np.nan), "edge": np.full(B, np.nan),
                     "height": np.full(B, np.nan), "width": np.full(B, np.nan), "n_fail": 0}

    x0 = fit_edge.params_vector(logit_fit) if logit_fit is not None else None
    for b in range(B):
        idx = rng.integers(0, n, n)
        pb, yb = pH[idx], y[idx]
        if "logistic" in models:
            o = out["logistic"]
            try:
                f = fit_edge.fit_logistic(pb, yb, config["fit"], n_starts=config["fit"]["bootstrap_starts"],
                                          seed=int(seed) + b, x0=x0)
                o["slopes"][b] = on_grid(lambda p: fit_edge.slope(f, p), grid, mask)
                o["edge"][b], o["height"][b], o["width"][b] = f["p50"], f["hi"] - f["lo"], f["w"]
            except fit_edge.EdgeFitError:
                o["n_fail"] += 1
        if "spline" in models:
            o = out["spline"]
            try:
                f = fit_smooth.fit_spline(pb, yb, config["smooth"], lam=spline_fit["lam"])
                o["slopes"][b] = on_grid(lambda p: fit_smooth.slope(f, p), grid, mask)
                track = None if spline_edge is None else (
                    spline_edge["mid_level"], spline_edge["sign"], spline_edge["edge_pH"],
                    config["shape"]["edge_track_window"])
                e = edge_summary(lambda p: fit_smooth.predict(f, p), lambda p: fit_smooth.slope(f, p),
                                 p_lo, p_hi, dense_n, config["shape"]["min_step"], track=track)
                o["edge"][b], o["height"][b], o["width"][b] = e["edge_pH"], e["height"], e["width"]
            except fit_smooth.SmoothFitError:
                o["n_fail"] += 1

    for o in out.values():
        o["slope_pct"] = _pct(o["slopes"])
        for k in ("edge", "height", "width"):
            o[f"{k}_pct"] = _pct(o[k])
        o["fail_frac"] = o["n_fail"] / B
    return out
