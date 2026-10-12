"""fit_edge.py -- 4-parameter logistic edge fit with seeded multistart (spec 4.2).

    A(p) = lo + (hi - lo) / (1 + exp(-(p - p50) / w)),    w > 0

hi < lo is allowed (falling edge). Bounds: p50 within the observed pH range
+/- p50_pad, w in [w_min, w_max], lo and hi in [level_min, level_max].
Slope is analytic: g(p) = (hi - lo) * s * (1 - s) / w, with s the logistic.
"""
import numpy as np
from scipy.optimize import least_squares

from phslope.synth import logistic, logistic_slope

PARAMS = ("lo", "hi", "p50", "w")


class EdgeFitError(RuntimeError):
    """Raised when no start converges, or there are too few distinct pH values."""


def _bounds(pH, cfg):
    lb = [cfg["level_min"], cfg["level_min"], pH.min() - cfg["p50_pad"], cfg["w_min"]]
    ub = [cfg["level_max"], cfg["level_max"], pH.max() + cfg["p50_pad"], cfg["w_max"]]
    return np.array(lb), np.array(ub)


def _data_start(pH, y, lb, ub):
    """Start from the data: low/high plateaus from the ends, p50 where y crosses the middle."""
    order = np.argsort(pH)
    k = max(1, len(pH) // 4)
    lo, hi = np.mean(y[order[:k]]), np.mean(y[order[-k:]])
    mid = (lo + hi) / 2
    cross = np.where(np.diff(np.sign(y[order] - mid)) != 0)[0]
    p50 = pH[order][cross[0]] if len(cross) else np.median(pH)
    return np.clip([lo, hi, p50, 0.5], lb + 1e-9, ub - 1e-9)


def _random_start(rng, lb, ub):
    x = rng.uniform(lb, ub)
    x[3] = np.exp(rng.uniform(np.log(lb[3]), np.log(ub[3])))    # width log-uniform
    return x


def _jacobian(x, pH):
    """Analytic derivatives of the logistic with respect to (lo, hi, p50, w)."""
    lo, hi, p50, w = x
    s = 1.0 / (1.0 + np.exp(-(pH - p50) / w))
    ds = (hi - lo) * s * (1 - s)
    return np.column_stack([1 - s, s, -ds / w, -ds * (pH - p50) / w ** 2])


def fit_logistic(pH, y, cfg, n_starts=None, seed=0, x0=None):
    """Returns dict lo, hi, p50, w, rmse, n, n_success. The best start by residual
    sum of squares wins. `x0` (e.g. the full-data fit) is tried first when given.
    Raises EdgeFitError if fewer than 4 distinct pH values or every start fails."""
    pH, y = np.asarray(pH, float), np.asarray(y, float)
    if len(np.unique(pH)) < 4:
        raise EdgeFitError(f"only {len(np.unique(pH))} distinct pH values; need 4 for 4 parameters")
    n_starts = n_starts or cfg["n_starts"]
    lb, ub = _bounds(pH, cfg)
    rng = np.random.default_rng(seed)
    starts = [np.clip(x0, lb + 1e-9, ub - 1e-9)] if x0 is not None else [_data_start(pH, y, lb, ub)]
    starts += [_random_start(rng, lb, ub) for _ in range(n_starts - 1)]

    resid = lambda x: logistic(pH, *x) - y
    best, n_ok = None, 0
    for x in starts:
        try:
            r = least_squares(resid, x, jac=lambda x: _jacobian(x, pH), bounds=(lb, ub), method="trf")
        except (ValueError, np.linalg.LinAlgError):
            continue
        if r.status <= 0 or not np.all(np.isfinite(r.x)):
            continue
        n_ok += 1
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        raise EdgeFitError(f"all {len(starts)} starts failed")
    out = dict(zip(PARAMS, best.x))
    out["rmse"] = float(np.sqrt(np.mean(best.fun ** 2)))
    out["n"] = len(y)
    out["n_success"] = n_ok
    return out


def params_vector(fit):
    return np.array([fit[k] for k in PARAMS])


def predict(fit, p):
    return logistic(p, fit["lo"], fit["hi"], fit["p50"], fit["w"])


def slope(fit, p):
    return logistic_slope(p, fit["lo"], fit["hi"], fit["p50"], fit["w"])
