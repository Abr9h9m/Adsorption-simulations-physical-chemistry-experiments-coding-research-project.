"""
response.py -- turns raw sorption columns into a comparable response variable.

Why this exists: Sorbed_val is an ABSOLUTE amount (mol/L scale, ~1e-6), which
depends on how much sorbate each study added. Gradients/curvatures of an
absolute amount are not comparable across systems or across pooled studies.
Use a normalized response instead:
  fraction_sorbed : Sorbed_val / Sorbate_val        (dimensionless, ~0-1)
  log_kd          : log10(Sorbed_val / Aq_val)      (distribution-ratio shape)
  raw             : untouched (only for the synthetic data, already in %)
ASSUMPTION to verify on the real file: Sorbed_val and Sorbate_val are in the
same concentration-equivalent units (check_response_range will warn if not).
"""
import numpy as np
import pandas as pd


def compute_response(df, mode="fraction_sorbed", sorbed_col="Sorbed_val",
                     sorbate_col="Sorbate_val", aq_col="Aq_val"):
    sorbed = pd.to_numeric(df[sorbed_col], errors="coerce")
    if mode == "raw":
        return sorbed
    sorbate = pd.to_numeric(df[sorbate_col], errors="coerce") if sorbate_col in df.columns else pd.Series(np.nan, index=df.index)
    aq = pd.to_numeric(df[aq_col], errors="coerce") if aq_col in df.columns else pd.Series(np.nan, index=df.index)

    if mode == "fraction_sorbed":
        frac = sorbed / sorbate.where(sorbate > 0)
        fallback = 1.0 - aq / sorbate.where(sorbate > 0)      # when Sorbed_val is missing
        return frac.fillna(fallback)
    if mode == "log_kd":
        valid = (sorbed > 0) & (aq > 0)
        out = pd.Series(np.nan, index=df.index)
        out[valid] = np.log10(sorbed[valid] / aq[valid])
        return out
    raise ValueError(f"unknown response mode '{mode}'")


def check_response_range(resp, mode, label=""):
    """Prints a sanity summary and warns about unit mismatches."""
    r = resp.dropna()
    if r.empty:
        print(f"  [{label}] WARNING: response is empty after normalization"); return
    q = r.quantile([0.05, 0.5, 0.95]).round(3).tolist()
    print(f"  [{label}] response ({mode}): n={len(r)}, 5/50/95% = {q}")
    if mode == "fraction_sorbed":
        over = (r > 1.05).mean(); neg = (r < -0.05).mean()
        if over > 0.05 or neg > 0.05:
            print(f"  [{label}] WARNING: {over:.0%} of values >1.05 and {neg:.0%} <-0.05 -- "
                  f"Sorbed_val and Sorbate_val are probably NOT in the same units; check before trusting results.")