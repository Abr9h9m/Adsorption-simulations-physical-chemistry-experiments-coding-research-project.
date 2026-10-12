"""slope.py -- slope curves on the shared pH grid (spec 4.1).

A curve has values only inside its own observed pH range. Grid points outside
[min pH, max pH] are NaN, never extrapolated; the mask says which are observed.
"""
import numpy as np

from phslope import fit_edge, fit_smooth


def make_grid(config):
    g = config["grid"]
    return np.round(np.arange(g["ph_min"], g["ph_max"] + g["step"] / 2, g["step"]), 10)


def observed_mask(grid, pH_min, pH_max):
    return (grid >= pH_min - 1e-9) & (grid <= pH_max + 1e-9)


def on_grid(values_fn, grid, mask):
    out = np.full(grid.shape, np.nan)
    if mask.any():
        out[mask] = values_fn(grid[mask])
    return out


def logistic_slope_on_grid(fit, grid, mask):
    return on_grid(lambda p: fit_edge.slope(fit, p), grid, mask)


def spline_slope_on_grid(fit, grid, mask):
    return on_grid(lambda p: fit_smooth.slope(fit, p), grid, mask)


def _crossing(p, f, level):
    """pH values where f crosses `level` (linear interpolation)."""
    d = f - level
    idx = np.where(np.sign(d[:-1]) * np.sign(d[1:]) <= 0)[0]
    return np.array([p[i] if d[i] == d[i + 1] else p[i] + (p[i + 1] - p[i]) * d[i] / (d[i] - d[i + 1])
                     for i in idx])


def edge_summary(fn_response, fn_slope, pH_min, pH_max, dense_n=200, min_step=0.15, track=None):
    """Model-agnostic edge description of a fitted curve, on a dense grid inside
    the observed range, with the same meaning as the logistic p50:

      edge_pH   pH where the curve is half-way through its main move (the
                significant rise or fall that contains the steepest point)
      mid_level response value at that half-way point
      sign      +1 for a rise, -1 for a fall
      max_slope steepest slope in the main move (signed)
      height    fitted response at the end minus at the start of the observed range
      width     logistic-equivalent width, |move height| / (4 |max slope|)

    track=(mid_level, sign, edge_pH, window): for a bootstrap draw, follow the same
    edge as the full fit: the crossing of the full-fit mid_level nearest to
    edge_pH and within +/- window. NaN edge if there is none."""
    from phslope.qc import moves
    p = np.linspace(pH_min, pH_max, dense_n)
    f, g = fn_response(p), fn_slope(p)
    height = float(f[-1] - f[0])
    if track is not None:
        level, sign, e0, window = track
        xs = _crossing(p, f, level)
        xs = xs[np.abs(xs - e0) <= window] if len(xs) else xs
        if not len(xs):
            return {"edge_pH": np.nan, "mid_level": level, "sign": sign, "max_slope": np.nan,
                    "height": height, "width": np.nan}
        e = float(xs[np.argmin(np.abs(xs - e0))])
        i = int(np.argmax(np.where(np.abs(p - e) <= window, sign * g, -np.inf)))
        return {"edge_pH": e, "mid_level": level, "sign": sign, "max_slope": float(g[i]),
                "height": height, "width": np.nan}
    i_steep = int(np.argmax(np.abs(g)))
    mv = [m for m in moves(f, min_step) if m[1] <= i_steep <= m[2]]
    d, a, b = mv[0] if mv else ((1 if g[i_steep] >= 0 else -1), 0, len(p) - 1)
    seg_p, seg_f = p[a:b + 1], f[a:b + 1]
    level = (seg_f[0] + seg_f[-1]) / 2
    xs = _crossing(seg_p, seg_f, level)
    e = float(xs[np.argmin(np.abs(xs - p[i_steep]))]) if len(xs) else float(p[i_steep])
    move_h = abs(seg_f[-1] - seg_f[0])
    return {"edge_pH": e, "mid_level": float(level), "sign": float(d), "max_slope": float(g[i_steep]),
            "height": height, "width": move_h / (4 * abs(g[i_steep])) if g[i_steep] != 0 else np.nan}
