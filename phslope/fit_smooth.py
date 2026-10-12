"""fit_smooth.py -- penalised cubic smoothing spline, the flexible check (spec 4.3).

Replicates (same pH after rounding) are averaged first and weighted by their
count, because the spline needs strictly increasing pH. The roughness penalty
lam is chosen from a log-spaced grid by leave-one-pH-level-out cross validation
inside the curve (exact refits, not an approximation). The slope is the
spline's derivative.

Not implemented: the optional monotone constraint. Non-monotone curves (bell,
two-step) are exactly what the smoother is here to catch, so it is left
unconstrained.
"""
import numpy as np
from scipy.interpolate import make_smoothing_spline


class SmoothFitError(RuntimeError):
    pass


def aggregate_replicates(pH, y, decimals):
    key = np.round(np.asarray(pH, float), decimals)
    xs, inv, counts = np.unique(key, return_inverse=True, return_counts=True)
    ys = np.bincount(inv, weights=np.asarray(y, float)) / counts
    return xs, ys, counts.astype(float)


def lam_grid(cfg):
    return np.logspace(np.log10(cfg["lam_min"]), np.log10(cfg["lam_max"]), cfg["lam_n"])


def _loo_rmse(x, y, w, lam):
    """Leave one pH level out; needs >= 6 levels so each refit keeps >= 5."""
    errs = []
    for i in range(len(x)):
        keep = np.arange(len(x)) != i
        spl = make_smoothing_spline(x[keep], y[keep], w=w[keep], lam=lam)
        errs.append(w[i] * (spl(x[i]) - y[i]) ** 2)
    return float(np.sqrt(np.sum(errs) / np.sum(w)))


def fit_spline(pH, y, cfg, lam=None):
    """Returns dict spline, lam, loo_rmse, rmse (on raw points), n_unique, x_min, x_max.
    If `lam` is given (e.g. inside the bootstrap), no CV is done."""
    x, ya, w = aggregate_replicates(pH, y, cfg["ph_decimals"])
    if len(x) < cfg["min_unique_ph"]:
        raise SmoothFitError(f"only {len(x)} distinct pH values; need {cfg['min_unique_ph']}")
    loo = np.nan
    if lam is None:
        if len(x) < cfg["min_unique_ph"] + 1:
            raise SmoothFitError(f"only {len(x)} distinct pH values; leave-one-out needs {cfg['min_unique_ph'] + 1}")
        scores = [(_loo_rmse(x, ya, w, lam_i), lam_i) for lam_i in lam_grid(cfg)]
        loo, lam = min(scores)
    spl = make_smoothing_spline(x, ya, w=w, lam=lam)
    resid = spl(np.asarray(pH, float)) - np.asarray(y, float)
    return {"spline": spl, "lam": float(lam), "loo_rmse": loo, "rmse": float(np.sqrt(np.mean(resid ** 2))),
            "n_unique": len(x), "x_min": float(x.min()), "x_max": float(x.max())}


def predict(fit, p):
    return fit["spline"](np.asarray(p, float))


def slope(fit, p):
    return fit["spline"].derivative()(np.asarray(p, float))
