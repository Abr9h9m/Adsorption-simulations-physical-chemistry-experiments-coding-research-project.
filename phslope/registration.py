"""registration.py -- align single-edge curves by position, width and height (spec 4.6).

For each core-library curve with shape rising or falling:
    b = edge position (half-way point; logistic p50)
    w = width (logistic w, or the logistic-equivalent width of the smoother)
    h = signed height of the edge (a = |h| is the height)
The warp p -> u = (p - b) / w puts every edge on a common coordinate, and the
registered slope is
    r(u) = g(b + w u) * w / h
For an exact logistic r(u) = s(u)(1 - s(u)) for every curve, so whatever is
left after registration is shape that position, width and height do not
explain. The registered slope uses the smoother's slope (the flexible
estimate) where it exists, because the logistic slope is identical for every
curve after registration by construction.

The warp (a, b, w) is kept for every curve; it is the main input to Version A
of the transfer model. Ratios to the median curve (the "reference") are also
reported: a_ratio = a / median a, w_scale = w / median w, b_shift = b - median b.
"""
import numpy as np
import pandas as pd

SINGLE_EDGE = ("rising", "falling")


def u_grid(config):
    r = config["registration"]
    return np.round(np.arange(r["u_min"], r["u_max"] + r["u_step"] / 2, r["u_step"]), 10)


def _row_slope(lib, i, source):
    """Slope row and its source; falls back to the primary slope if the smoother is missing."""
    if source == "spline" and np.isfinite(lib["G_spline"][i]).any():
        return lib["G_spline"][i], "spline"
    return lib["G"][i], "primary"


def interp_masked(grid, values, mask, at):
    """Linear interpolation of values on grid, using observed points only; NaN outside them."""
    x, y = grid[mask], values[mask]
    out = np.full(np.shape(at), np.nan)
    if len(x) < 2:
        return out
    inside = (at >= x[0]) & (at <= x[-1])
    out[inside] = np.interp(at[inside], x, y)
    return out


def select_curves(lib):
    m = lib["meta"]
    ok = (m["in_core_library"].astype(bool) & m["shape"].isin(SINGLE_EDGE) & np.isfinite(m["edge_pH"])
          & np.isfinite(m["width"]) & (m["width"] > 0) & np.isfinite(m["height"]) & (m["height"] != 0))
    return np.where(ok.to_numpy())[0]


def register(lib, config, idx=None, source="spline"):
    """Returns dict u, R (n x U registered slopes), idx (library rows), warp (DataFrame),
    reference (mean registered curve), source_used (per curve)."""
    idx = select_curves(lib) if idx is None else np.asarray(idx)
    u = u_grid(config)
    meta = lib["meta"]
    R = np.full((len(idx), len(u)), np.nan)
    used = []
    for k, i in enumerate(idx):
        b, w, h = meta.loc[i, "edge_pH"], meta.loc[i, "width"], meta.loc[i, "height"]
        g, src = _row_slope(lib, i, source)
        R[k] = interp_masked(lib["grid"], g, lib["mask"][i], b + w * u) * w / h
        used.append(src)
    warp = pd.DataFrame({
        "curve_id": lib["curve_ids"][idx], "shape": meta.loc[idx, "shape"].to_numpy(),
        "b": meta.loc[idx, "edge_pH"].to_numpy(), "w": meta.loc[idx, "width"].to_numpy(),
        "h": meta.loc[idx, "height"].to_numpy(), "slope_source": used,
    })
    warp["a"] = warp["h"].abs()
    warp["b_shift"] = warp["b"] - warp["b"].median()
    warp["w_scale"] = warp["w"] / warp["w"].median()
    warp["a_ratio"] = warp["a"] / warp["a"].median()
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Mean of empty slice")
            ref = np.nanmean(R, axis=0)
    return {"u": u, "R": R, "idx": idx, "warp": warp, "reference": ref}


def reconstruct(reg, grid, k):
    """Curve k rebuilt from the reference shape and its own warp, on the pH grid:
    g_hat(p) = h / w * reference((p - b) / w); zero slope beyond the registered range."""
    row = reg["warp"].iloc[k]
    uu = (grid - row["b"]) / row["w"]
    ref = np.nan_to_num(reg["reference"])
    out = np.interp(uu, reg["u"], ref, left=0.0, right=0.0)
    return out * row["h"] / row["w"]


def variance_removed(lib, reg, source="spline"):
    """Fraction of between-curve slope variance (pH grid, observed cells) removed by
    registration alone: 1 - SS(g - g_hat) / SS(g - mean over curves at each pH).
    Returned overall and per shape."""
    def frac(sel):
        if not len(sel):
            return np.nan
        rows = [_row_slope(lib, reg["idx"][k], source)[0] for k in sel]
        G = np.vstack(rows)
        M = np.vstack([lib["mask"][reg["idx"][k]] for k in sel]) & np.isfinite(G)
        Gm = np.where(M, G, np.nan)
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Mean of empty slice")
                col_mean = np.nanmean(Gm, axis=0)
        ss_tot = np.nansum((Gm - col_mean) ** 2)
        hat = np.vstack([reconstruct(reg, lib["grid"], k) for k in sel])
        ss_res = np.nansum(np.where(M, (G - hat) ** 2, np.nan))
        return float(1 - ss_res / ss_tot) if ss_tot > 0 else np.nan

    shapes = reg["warp"]["shape"].to_numpy()
    out = {"all": frac(np.arange(len(shapes)))}
    for s in SINGLE_EDGE:
        out[s] = frac(np.where(shapes == s)[0])
    return out
