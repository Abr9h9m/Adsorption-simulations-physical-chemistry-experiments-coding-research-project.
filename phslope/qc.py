"""qc.py -- per-curve quality flags and shape classes (spec 4.5).

Shape class, from the fitted curve on a dense grid inside the observed range:
  1. If the fitted response changes by less than flat_height overall -> flat.
  2. Otherwise find the significant rises and falls with a hysteresis rule: a
     move only counts once the response has changed by at least min_step since
     the last turning point (so noise wiggles are ignored).
       one rise  -> rising       one fall -> falling       rise then fall -> bell
       anything else -> unclassified
  3. A single rise or fall whose slope has two separate peaks, each carrying a
     step of at least min_step, with the slope between them dropping below
     multi_step_valley x the smaller peak -> multi_step.

Flags (none of them deletes data; they decide core-library membership):
  too_few_points, narrow_span, edge_not_bracketed, poor_fit, wide_interval,
  unit_mismatch, bootstrap_unstable, fit_failed.
"""
import numpy as np
from scipy.signal import find_peaks

SHAPES = ("rising", "falling", "flat", "bell", "multi_step", "unclassified")
EDGE_SHAPES = ("rising", "falling", "bell", "multi_step")


def moves(f, h):
    """Hysteresis zigzag: list of (+1 / -1, start_index, end_index) for moves of size >= h."""
    out, trend = [], 0
    run_min_i = run_max_i = 0
    start_i = ext_i = 0
    for i in range(1, len(f)):
        v = f[i]
        if trend == 0:
            if f[i] < f[run_min_i]:
                run_min_i = i
            if f[i] > f[run_max_i]:
                run_max_i = i
            if v - f[run_min_i] >= h:
                trend, start_i, ext_i = 1, run_min_i, i
            elif f[run_max_i] - v >= h:
                trend, start_i, ext_i = -1, run_max_i, i
        elif trend == 1:
            if v > f[ext_i]:
                ext_i = i
            elif f[ext_i] - v >= h:
                out.append((1, start_i, ext_i))
                trend, start_i, ext_i = -1, ext_i, i
        else:
            if v < f[ext_i]:
                ext_i = i
            elif v - f[ext_i] >= h:
                out.append((-1, start_i, ext_i))
                trend, start_i, ext_i = 1, ext_i, i
    if trend != 0:
        out.append((trend, start_i, ext_i))
    return out


def _n_steps(p, g_dir, h, valley_frac):
    """Number of separate steps inside one monotone move. g_dir = slope in the
    move's direction (positive where the curve moves that way)."""
    g = np.clip(g_dir, 0, None)
    if g.max() <= 0:
        return 0
    peaks, _ = find_peaks(np.concatenate([[0], g, [0]]))
    peaks = peaks - 1
    dp = np.gradient(p)
    # step carried by each peak: integral of slope between the neighbouring minima
    steps = []
    for k, pk in enumerate(peaks):
        left = peaks[k - 1] if k > 0 else 0
        right = peaks[k + 1] if k + 1 < len(peaks) else len(g) - 1
        lo = left + int(np.argmin(g[left:pk + 1])) if pk > left else left
        hi = pk + int(np.argmin(g[pk:right + 1])) if right > pk else right
        steps.append((pk, float(np.sum(g[lo:hi + 1] * dp[lo:hi + 1]))))
    big = [pk for pk, s in steps if s >= h]
    if len(big) < 2:
        return len(big)
    n = 1
    for a, b in zip(big[:-1], big[1:]):
        if g[a:b + 1].min() < valley_frac * min(g[a], g[b]):
            n += 1
    return n


def shape_class(p, f, g, cfg):
    """p: dense pH grid; f: fitted response; g: fitted slope."""
    if np.nanmax(f) - np.nanmin(f) < cfg["flat_height"]:
        return "flat"
    found = moves(f, cfg["min_step"])
    dirs = [d for d, _, _ in found]
    if dirs == [1, -1]:
        return "bell"
    if dirs in ([1], [-1]):
        d, i, j = found[0]
        if _n_steps(p[i:j + 1], d * g[i:j + 1], cfg["min_step"], cfg["multi_step_valley"]) >= 2:
            return "multi_step"
        return "rising" if d == 1 else "falling"
    if not dirs:
        return "flat"
    return "unclassified"


def replicate_scatter(pH, y, decimals, min_groups):
    """Median within-group SD over pH levels with >= 2 points; NaN if fewer than min_groups such levels."""
    key = np.round(np.asarray(pH, float), decimals)
    y = np.asarray(y, float)
    sds = [np.std(y[key == k], ddof=1) for k in np.unique(key) if np.sum(key == k) >= 2]
    return float(np.median(sds)) if len(sds) >= min_groups else np.nan


def poor_fit_limit(rep_scatter, thr):
    if np.isfinite(rep_scatter) and rep_scatter > 0:
        return thr["poor_fit_replicate_multiple"] * rep_scatter
    return thr["poor_fit_ceiling"]


def edge_bracketed(pH, edge, window):
    pH = np.asarray(pH, float)
    return bool(np.any((pH <= edge) & (pH >= edge - window)) and np.any((pH >= edge) & (pH <= edge + window)))


def flags_for(info, thr):
    """info keys: n_points, pH_span, shape, edge_pH, pH (array), rmse, rep_scatter,
    edge_ci_width, boot_fail_frac, unit_mismatch, fit_failed."""
    f = []
    if info.get("fit_failed"):
        f.append("fit_failed")
    if info["n_points"] < thr["too_few_points"]:
        f.append("too_few_points")
    if info["pH_span"] < thr["narrow_span"]:
        f.append("narrow_span")
    if info["unit_mismatch"]:
        f.append("unit_mismatch")
    if info.get("fit_failed"):
        return f
    if info["shape"] in EDGE_SHAPES and not edge_bracketed(info["pH"], info["edge_pH"], thr["edge_bracket_ph"]):
        f.append("edge_not_bracketed")
    if info["rmse"] > poor_fit_limit(info["rep_scatter"], thr):
        f.append("poor_fit")
    if info["shape"] in EDGE_SHAPES and not (info["edge_ci_width"] <= thr["wide_interval_p50"]):
        f.append("wide_interval")
    if info["boot_fail_frac"] > thr["bootstrap_fail_frac"]:
        f.append("bootstrap_unstable")
    return f


def in_core_library(flags, shape):
    return not flags and shape != "unclassified"
