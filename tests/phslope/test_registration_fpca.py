import numpy as np
import pandas as pd
import pytest

from phslope.common import load_config
from phslope.fpca import fpca, impute_svd, project
from phslope.registration import interp_masked, reconstruct, register, u_grid, variance_removed
from phslope.slope import make_grid, observed_mask
from phslope.synth import logistic_slope

CFG = load_config()


def _lib(params, shape_fn=None, ranges=None):
    """Toy library of logistic-like curves; params = list of (lo, hi, p50, w)."""
    grid = make_grid(CFG)
    rows, G, M = [], [], []
    for k, (lo, hi, p50, w) in enumerate(params):
        a, b = ranges[k] if ranges else (2.0, 11.0)
        m = observed_mask(grid, a, b)
        g = np.where(m, logistic_slope(grid, lo, hi, p50, w), np.nan)
        if shape_fn is not None:
            g = np.where(m, g + shape_fn(k, grid), np.nan)
        G.append(g)
        M.append(m)
        rows.append({"curve_id": f"c{k}", "shape": "rising" if hi > lo else "falling", "in_core_library": True,
                     "edge_pH": p50, "width": w, "height": hi - lo})
    G = np.array(G)
    return {"grid": grid, "curve_ids": np.array([r["curve_id"] for r in rows]), "meta": pd.DataFrame(rows),
            "G": G, "G_spline": G.copy(), "mask": np.array(M)}


def test_interp_masked_never_extrapolates():
    grid = np.arange(5.0)
    out = interp_masked(grid, grid * 2, np.array([0, 1, 1, 1, 0], bool), np.array([0.5, 2.5, 3.5]))
    assert np.isnan(out[0]) and out[1] == 5 and np.isnan(out[2])


def test_logistic_curves_collapse_after_registration():
    rng = np.random.default_rng(0)
    params = [(0.05, 0.95, rng.uniform(4, 8), rng.uniform(.6, 1.2)) for _ in range(8)]
    params += [(0.9, 0.1, rng.uniform(4, 8), rng.uniform(.6, 1.2)) for _ in range(4)]
    lib = _lib(params)
    reg = register(lib, CFG)
    u = reg["u"]
    s = 1 / (1 + np.exp(-u))
    # interpolation on the 0.25 pH grid limits accuracy
    assert np.nanmax(np.abs(reg["R"] - s * (1 - s))) < 0.02
    vr = variance_removed(lib, reg)
    assert vr["all"] > 0.95 and vr["rising"] > 0.95 and vr["falling"] > 0.95
    assert set(reg["warp"].columns) >= {"a", "b", "w", "a_ratio", "b_shift", "w_scale"}


def test_reconstruct_returns_original_logistic():
    lib = _lib([(0, 1, 6.0, 0.8), (0, 1, 5.0, 0.8)])
    reg = register(lib, CFG)
    g_hat = reconstruct(reg, lib["grid"], 0)
    m = lib["mask"][0]
    assert np.allclose(g_hat[m], lib["G"][0][m], atol=0.02)


def test_fpca_recovers_planted_shape_component():
    rng = np.random.default_rng(1)
    amps = rng.normal(0, 0.05, 30)
    params = [(0, 1, rng.uniform(5, 7), 1.0) for _ in range(30)]
    lib = _lib(params, shape_fn=lambda k, p: amps[k] * np.exp(-((p - params[k][2] - 1.0) ** 2) / 0.5))
    reg = register(lib, CFG)
    f = fpca(reg["R"], CFG["fpca"])
    assert f["n_components"] >= 1
    # first component scores track the planted amplitude
    r = np.corrcoef(f["scores"][:, 0], amps)[0, 1]
    assert abs(r) > 0.95


def test_impute_svd_keeps_observed_values():
    rng = np.random.default_rng(2)
    X = np.outer(rng.normal(size=20), rng.normal(size=10)) + 0.01 * rng.normal(size=(20, 10))
    Xm = X.copy()
    Xm[rng.random(X.shape) < 0.2] = np.nan
    Z, _ = impute_svd(Xm, rank=1)
    obs = np.isfinite(Xm)
    assert np.allclose(Z[obs], Xm[obs])
    assert np.sqrt(np.mean((Z[~obs] - X[~obs]) ** 2)) < 0.1 * X.std()


def test_project_needs_enough_columns():
    f = {"columns": np.arange(5), "components": np.eye(5)[:2], "mean": np.zeros(5), "n_components": 2}
    assert np.allclose(project(np.array([1., 2, 0, 0, 0]), f), [1, 2])
    assert np.isnan(project(np.array([1., np.nan, np.nan, np.nan, np.nan]), f)).all()


def test_u_grid():
    u = u_grid(CFG)
    assert u[0] == -6 and u[-1] == 6 and len(u) == 49
