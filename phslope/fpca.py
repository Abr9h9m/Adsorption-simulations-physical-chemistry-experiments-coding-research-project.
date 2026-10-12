"""fpca.py -- functional principal components of registered slope curves (spec 4.7).

Missing values: registered curves cover different stretches of the u grid.
Columns observed in fewer than min_column_frac of the curves are dropped; the
remaining gaps are filled by ITERATIVE SVD IMPUTATION (start from column means,
fit a rank-`max_components` SVD, replace only the missing cells with the
reconstruction, repeat until the filled values stop changing). Observed values
are never altered.

Components kept: the smallest number whose cumulative explained variance
reaches var_target, capped at max_components. Explained variance is computed on
the completed matrix, so it is somewhat optimistic where many cells were filled;
the fraction of filled cells is reported alongside.

Score uncertainty: each bootstrap draw of a curve's smoother slope is
registered with the curve's own full-fit warp (so only shape uncertainty is
propagated) and projected onto the components by least squares over the
columns that draw observes. The SD of the projected draws is the score SD.
"""
import numpy as np

from phslope.registration import interp_masked


def impute_svd(X, rank, max_iter=500, tol=1e-7):
    miss = ~np.isfinite(X)
    col = np.nanmean(X, axis=0)
    Z = np.where(miss, col, X)
    n_iter = 0
    for n_iter in range(1, max_iter + 1):
        mu = Z.mean(axis=0)
        U, S, Vt = np.linalg.svd(Z - mu, full_matrices=False)
        k = min(rank, len(S))
        rec = mu + (U[:, :k] * S[:k]) @ Vt[:k]
        change = np.sqrt(np.sum((rec[miss] - Z[miss]) ** 2) / max(1, miss.sum()))
        Z[miss] = rec[miss]
        if change < tol:
            break
    return Z, n_iter


def fpca(R, cfg):
    """R: curves x u-grid (NaN = not observed). Returns dict mean, components (k x cols),
    scores (n x k), explained (all), n_components, columns (kept column indices),
    filled_fraction, n_iter."""
    obs_frac = np.isfinite(R).mean(axis=0)
    cols = np.where(obs_frac >= cfg["min_column_frac"])[0]
    X = R[:, cols]
    keep_rows = np.isfinite(X).any(axis=1)
    if keep_rows.sum() < 3 or len(cols) < 3:
        raise ValueError(f"too little data for FPCA: {keep_rows.sum()} curves, {len(cols)} columns")
    filled = float((~np.isfinite(X[keep_rows])).mean())
    Z, n_iter = impute_svd(X[keep_rows], cfg["max_components"], cfg["max_iter"], cfg["tol"])
    mu = Z.mean(axis=0)
    U, S, Vt = np.linalg.svd(Z - mu, full_matrices=False)
    explained = S ** 2 / np.sum(S ** 2)
    k = int(np.searchsorted(np.cumsum(explained), cfg["var_target"]) + 1)
    k = min(k, cfg["max_components"], len(S))
    scores = np.full((len(R), k), np.nan)
    scores[keep_rows] = U[:, :k] * S[:k]
    return {"mean": mu, "components": Vt[:k], "scores": scores, "explained": explained,
            "n_components": k, "columns": cols, "filled_fraction": filled, "n_iter": n_iter,
            "rows_used": keep_rows}


def project(r, f):
    """Least-squares scores of one registered curve (full u grid) on the components,
    using only the kept columns it observes. NaN if it observes fewer columns than components."""
    x = r[f["columns"]]
    ok = np.isfinite(x)
    if ok.sum() < f["n_components"] + 1:
        return np.full(f["n_components"], np.nan)
    A = f["components"][:, ok].T
    s, *_ = np.linalg.lstsq(A, x[ok] - f["mean"][ok], rcond=None)
    return s


def score_uncertainty(lib, reg, f, draws_key="draws_spline"):
    """SD of projected bootstrap scores per curve (n x k). Needs lib[draws_key]."""
    D = lib[draws_key]
    out = np.full((len(reg["idx"]), f["n_components"]), np.nan)
    u = reg["u"]
    for k, i in enumerate(reg["idx"]):
        row = reg["warp"].iloc[k]
        if row["slope_source"] != "spline":
            D_i = lib["draws"][i]
        else:
            D_i = D[i]
        S = []
        for d in D_i:
            if not np.isfinite(d).any():
                continue
            r = interp_masked(lib["grid"], d, lib["mask"][i], row["b"] + row["w"] * u) * row["w"] / row["h"]
            S.append(project(r, f))
        S = np.array(S)
        if len(S) > 1:
            out[k] = np.nanstd(S, axis=0, ddof=1)
    return out
