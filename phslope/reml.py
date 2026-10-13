"""reml.py -- REML for crossed random intercepts, fast enough to bootstrap.

Model:  y = X beta + sum_k Z_k u_k + e,   u_k ~ N(0, s_k^2 I),  e ~ N(0, s^2 I)

statsmodels MixedLM fits the same model, but with crossed effects it needs a
single dummy group, which makes it work with an n x n covariance matrix
(~50 s per fit at n ~ 1,100). Here the computation uses the q x q matrix of
random-effect levels instead (q = total number of class, pair and reference
levels), via the identity

    V0 = I + Z L L Z'                     (V = s^2 V0, L = diag(sqrt(s_k^2 / s^2)))
    M  = I_q + L Z'Z L
    log|V0| = log|M|,     V0^-1 a = a - Z L M^-1 L Z' a

and maximizes the profiled REML likelihood over log variance ratios with
L-BFGS-B. tests/phslope/test_variance_cluster.py checks it against statsmodels.
"""
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

LOG_RATIO_BOUNDS = (-25.0, 12.0)


def design(df, factors):
    """Sparse indicator matrix Z (n x q) and the level slice of each factor."""
    blocks, slices, start = [], {}, 0
    n = len(df)
    for name, col in factors.items():
        codes, levels = pd.factorize(df[col].astype(str))
        blocks.append(sparse.csr_matrix((np.ones(n), (np.arange(n), codes)), shape=(n, len(levels))))
        slices[name] = slice(start, start + len(levels))
        start += len(levels)
    return sparse.hstack(blocks).tocsr(), slices


def _neg2_reml(eta, y, X, Z, ZtZ, Zty, ZtX, slices, n, p):
    ratios = np.exp(eta)
    lam = np.empty(ZtZ.shape[0])
    for k, sl in enumerate(slices.values()):
        lam[sl] = np.sqrt(ratios[k])
    M = np.eye(len(lam)) + lam[:, None] * ZtZ * lam[None, :]
    try:
        cf = cho_factor(M, lower=True, check_finite=False)
    except np.linalg.LinAlgError:
        return np.inf, None
    logdetM = 2 * np.sum(np.log(np.diag(cf[0])))

    def vinv_quad(a_t_b, Zta, Ztb):
        """a' V0^-1 b given a'b, Z'a, Z'b."""
        return a_t_b - (lam[:, None] * Zta).T @ cho_solve(cf, lam[:, None] * Ztb, check_finite=False)

    XtVX = vinv_quad(X.T @ X, ZtX, ZtX)
    XtVy = vinv_quad((X.T @ y)[:, None], ZtX, Zty[:, None]).ravel()
    try:
        cx = cho_factor(XtVX, lower=True, check_finite=False)
    except np.linalg.LinAlgError:
        return np.inf, None
    beta = cho_solve(cx, XtVy, check_finite=False)
    yVy = vinv_quad(np.array([[y @ y]]), Zty[:, None], Zty[:, None])[0, 0]
    rss = yVy - XtVy @ beta
    s2 = rss / (n - p)
    if s2 <= 0:
        return np.inf, None
    logdetXVX = 2 * np.sum(np.log(np.diag(cx[0])))
    val = (n - p) * np.log(s2) + logdetM + logdetXVX
    return val, (beta, s2)


def simulate(df, factors, fixed, components, beta, rng):
    """One parametric-bootstrap response vector from a fitted model:
    y* = X beta + sum_k Z_k u_k + e, with u_k ~ N(0, s_k^2) per level and e ~ N(0, s^2).
    `df` must already be restricted to complete rows (same rows as the fit)."""
    n = len(df)
    X = np.column_stack([np.ones(n)] + [df[c].to_numpy(float) for c in (fixed or [])])
    y = X @ beta + rng.normal(0, np.sqrt(components["residual"]), n)
    for name, col in factors.items():
        codes, levels = pd.factorize(df[col].astype(str))
        y += rng.normal(0, np.sqrt(components[name]), len(levels))[codes]
    return y


def fit_reml(df, response, factors, fixed=None):
    """factors: {component name: column}. fixed: list of numeric covariate columns.
    Returns dict components (variances, incl. 'residual'), beta, n, converged."""
    cols = [response] + list(factors.values()) + list(fixed or [])
    d = df[cols].dropna()
    n = len(d)
    y = d[response].to_numpy(float)
    X = np.column_stack([np.ones(n)] + [d[c].to_numpy(float) for c in (fixed or [])])
    p = X.shape[1]
    Z, slices = design(d, factors)
    ZtZ = (Z.T @ Z).toarray()
    Zty = Z.T @ y
    ZtX = (Z.T @ X)
    ZtX = np.asarray(ZtX)
    args = (y, X, Z, ZtZ, Zty, ZtX, slices, n, p)
    f = lambda e: _neg2_reml(e, *args)[0]
    best = None
    for start in (0.0, -3.0):                      # two starts; keep the better optimum
        r = minimize(f, np.full(len(slices), start), method="L-BFGS-B",
                     bounds=[LOG_RATIO_BOUNDS] * len(slices))
        if best is None or r.fun < best.fun:
            best = r
    val, sol = _neg2_reml(best.x, *args)
    if sol is None:
        raise ValueError("REML fit is singular (e.g. a constant or collinear fixed covariate)")
    beta, s2 = sol
    comps = {name: float(np.exp(e) * s2) for name, e in zip(slices, best.x)}
    comps = {k: (0.0 if v < 1e-10 * s2 else v) for k, v in comps.items()}
    comps["residual"] = float(s2)
    return {"components": comps, "beta": beta, "n": n, "converged": bool(best.success)}
