"""kd.py -- per-point distribution quantities (protocol E0.2).

For every observation (with a `K_source` flag):
  K          Sorbed / Aq from the reported values when Aq is present AND the row passes the
             mass-balance check (K_source = "reported"); otherwise f / (1 - f) from fraction
             sorbed (K_source = "mass_balance"). NaN when f is outside (0, 1).
  log10K, logit_f (natural log of f/(1-f)), Kd_L_per_g = K / S (S = solids, g/L), log10Kd,
  loading L = total sorbate / S (mol per g solid), log10L,
  mid = mid_range[0] < f < mid_range[1].
Missing solids give NaN (never zero).
"""
import numpy as np
import pandas as pd

from phslope.common import RESPONSE


def mass_balance(df, tol):
    """Relative mismatch |Aq - (total - sorbed)| / total for rows with all three values,
    and whether it is within `tol`. NaN where a value is missing."""
    sorbed = pd.to_numeric(df["Sorbed_val"], errors="coerce")
    aq = pd.to_numeric(df["Aq_val"], errors="coerce")
    tot = df["total_sorbate_mol_L"]
    rel = (aq - (tot - sorbed)).abs() / tot.where(tot > 0)
    return rel, rel <= tol


def add_kd(df, cfg):
    """df: observation rows with response (f), Sorbed_val, Aq_val, total_sorbate_mol_L, solids_g_L."""
    out = df.copy()
    lo, hi = cfg["kd"]["mid_range"]
    f = out["response"].astype(float)
    rel, ok = mass_balance(out, cfg["kd"]["mass_balance_tolerance"])
    out["mass_balance_rel"] = rel
    out["mass_balance_ok"] = ok
    sorbed = pd.to_numeric(out["Sorbed_val"], errors="coerce")
    aq = pd.to_numeric(out["Aq_val"], errors="coerce")
    inside = (f > 0) & (f < 1)
    S = out["solids_g_L"].where(out["solids_g_L"] > 0)
    if RESPONSE == "kd":
        # response is already Kd / (Kd + 1000); K is Kd in L/g (= K at 1 g/L), straight from load.add_kd_response
        kd_g = out["Kd_L_kg"] / 1000
        out["K"] = kd_g.where(kd_g > 0)
        out["K_source"] = np.where(out["K"].notna(), out["kd_source"], "none")
        out["Kd_L_per_g"] = out["K"]
    else:
        k_rep = (sorbed / aq).where(ok.fillna(False) & (sorbed > 0) & (aq > 0))
        k_mb = (f / (1 - f)).where(inside)
        out["K"] = k_rep.fillna(k_mb)
        out["K_source"] = np.where(k_rep.notna(), "reported", np.where(k_mb.notna(), "mass_balance", "none"))
        out["Kd_L_per_g"] = out["K"] / S
    out["log10K"] = np.log10(out["K"].where(out["K"] > 0))
    out["logit_f"] = np.log((f / (1 - f)).where(inside))
    out["log10Kd"] = np.log10(out["Kd_L_per_g"].where(out["Kd_L_per_g"] > 0))
    out["loading_mol_per_g"] = out["total_sorbate_mol_L"] / S
    out["log10L"] = np.log10(out["loading_mol_per_g"].where(out["loading_mol_per_g"] > 0))
    out["mid"] = (f > lo) & (f < hi)
    return out


def line_fit(pH, log10K, w=None):
    """(Weighted) least squares of log10K on pH. Returns a (intercept), b (slope), r2, n,
    covariance of (a, b), residual SD. w = point weights (inverse variances, up to a constant)."""
    pH, y = np.asarray(pH, float), np.asarray(log10K, float)
    n = len(pH)
    w = np.ones(n) if w is None else np.asarray(w, float)
    X = np.column_stack([np.ones(n), pH])
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    res = y - X @ beta
    dof = max(n - 2, 1)
    s2 = float(w @ res ** 2 / dof)
    cov = s2 * np.linalg.pinv((X * w[:, None]).T @ X)
    ybar = np.sum(w * y) / np.sum(w)
    tss = float(np.sum(w * (y - ybar) ** 2))
    r2 = 1 - float(w @ res ** 2) / tss if tss > 0 else np.nan
    return {"a": beta[0], "b": beta[1], "r2": r2, "n": n, "cov": cov, "sd": np.sqrt(s2)}
