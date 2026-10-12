"""variance.py -- how much of the curve-to-curve variation do classes explain? (spec 4.8)

1. Variance split. For each curve parameter (edge position, log width, height,
   first FPCA scores) fit a linear mixed model with crossed random intercepts:

       value ~ 1 + (1 | mineral_class) + (1 | sorbate_class) + (1 | mineral:sorbate) + (1 | reference)

   Fitted by REML with phslope/reml.py, which computes the same likelihood as
   statsmodels MixedLM (checked in the tests) but works with the matrix of
   random-effect levels instead of an n x n covariance, so the bootstrap is
   affordable (statsmodels needs a single dummy group for crossed effects and
   took ~50 s per fit). `fit_components_statsmodels` is kept for the cross-check.
   Each component is reported as a
   share of the total (components + residual). Intervals: cluster bootstrap over
   references (resample whole papers with replacement, refit), percentile 95%.

   A second fit adds the experimental conditions as fixed effects (log10 solids
   loading, log10 total sorbate, log10 ionic strength, carbonate flag, and
   temperature if reported for enough curves) to see how much of the "study"
   share is really conditions. Rows missing a covariate are dropped and counted.

2. Go/no-go permutation test (spec Stage 2 pass rule). Statistic: the share of
   variance between class cells (mineral_class x sorbate_class, i.e. both main
   effects and their interaction), = between-cell sum of squares / total.
   Null distribution: shuffle the class-cell labels among curves WITHIN each
   reference, so a study's own offset can never look like a class effect.
   References that contain only one class cell cannot be shuffled; their count
   is reported, because they make the test conservative.
"""
import warnings

import numpy as np
import pandas as pd

from phslope.reml import fit_reml

TERMS = {"mineral_class": "0 + C(mineral_class)", "sorbate_class": "0 + C(sorbate_class)",
         "mineral_sorbate": "0 + C(pair)", "reference": "0 + C(reference)"}
FACTORS = {"mineral_class": "mineral_class", "sorbate_class": "sorbate_class", "mineral_sorbate": "pair",
           "reference": "reference"}


def _prep(df, value):
    d = df[["mineral_class", "sorbate_class", "mineral", "sorbate", "reference", value]].dropna().copy()
    d["pair"] = d["mineral"].astype(str) + " | " + d["sorbate"].astype(str)
    d["one"] = 1
    return d.rename(columns={value: "y"})


def fit_components(df, value, fixed=None):
    """REML variance components (fast path). Returns dict components (incl. residual), n, converged."""
    d = _prep(df, value) if fixed is None else _prep_fixed(df, value, fixed)
    r = fit_reml(d, "y", FACTORS, fixed)
    return {"components": r["components"], "n": r["n"], "converged": r["converged"]}


def fit_components_statsmodels(df, value, fixed=None):
    """Same model through statsmodels MixedLM (slow; used to cross-check reml.py)."""
    import statsmodels.formula.api as smf
    d = _prep(df, value) if fixed is None else _prep_fixed(df, value, fixed)
    formula = "y ~ 1" + ("" if not fixed else " + " + " + ".join(fixed))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.mixedlm(formula, d, groups="one", vc_formula=TERMS, re_formula="0")
        r = m.fit(reml=True, method=["lbfgs", "powell"])
    names = list(m.exog_vc.names)
    comp = {n: float(v) for n, v in zip(names, r.vcomp)}
    comp["residual"] = float(r.scale)
    return {"components": comp, "n": len(d), "converged": bool(r.converged)}


def _prep_fixed(df, value, fixed):
    cols = ["mineral_class", "sorbate_class", "mineral", "sorbate", "reference", value] + list(fixed)
    d = df[cols].dropna().copy()
    d["pair"] = d["mineral"].astype(str) + " | " + d["sorbate"].astype(str)
    d["one"] = 1
    return d.rename(columns={value: "y"})


def shares(components):
    total = sum(components.values())
    return {k: v / total for k, v in components.items()} if total > 0 else {k: np.nan for k in components}


def bootstrap_shares(df, value, B, seed, fixed=None):
    """Cluster bootstrap over references. Returns DataFrame (B rows x components) of shares."""
    rng = np.random.default_rng(seed)
    refs = df["reference"].unique()
    groups = {r: g for r, g in df.groupby("reference")}
    rows = []
    for b in range(B):
        pick = rng.choice(refs, len(refs), replace=True)
        parts = []
        for j, r in enumerate(pick):
            g = groups[r].copy()
            g["reference"] = f"{r}#{j}"           # a paper drawn twice counts as two papers
            parts.append(g)
        try:
            rows.append(shares(fit_components(pd.concat(parts), value, fixed)["components"]))
        except (np.linalg.LinAlgError, ValueError):
            continue
    return pd.DataFrame(rows)


def variance_split(df, value, B=100, seed=0, fixed=None):
    """Point shares + 95% cluster-bootstrap intervals for one parameter."""
    fit = fit_components(df, value, fixed)
    sh = shares(fit["components"])
    boot = bootstrap_shares(df, value, B, seed, fixed) if B else pd.DataFrame()
    rows = []
    for k, v in sh.items():
        lo, hi = (np.nanpercentile(boot[k], [2.5, 97.5]) if k in boot and len(boot) else (np.nan, np.nan))
        rows.append({"parameter": value, "component": k, "share": v, "share_lo": lo, "share_hi": hi,
                     "variance": fit["components"][k]})
    out = pd.DataFrame(rows)
    out.attrs.update(n=fit["n"], converged=fit["converged"], n_boot=len(boot))
    return out


# ------------------------------------------------------------- permutation test

def cell_share(y, cell_codes):
    """Between-cell sum of squares / total sum of squares."""
    y = np.asarray(y, float)
    tot = np.sum((y - y.mean()) ** 2)
    if tot == 0:
        return np.nan
    sums = np.bincount(cell_codes, weights=y)
    counts = np.bincount(cell_codes)
    nz = counts > 0
    between = np.sum(sums[nz] ** 2 / counts[nz]) - y.sum() ** 2 / len(y)
    return float(between / tot)


def within_reference_permutation_test(df, value, n_perm=2000, seed=0):
    """Is the class-cell share larger than when labels are shuffled inside each paper?
    Returns dict observed, p_value, null (array), n_refs, n_refs_shufflable."""
    d = df[["mineral_class", "sorbate_class", "reference", value]].dropna()
    cells = pd.factorize(d["mineral_class"].astype(str) + "|" + d["sorbate_class"].astype(str))[0]
    y = d[value].to_numpy(float)
    refs = pd.factorize(d["reference"])[0]
    obs = cell_share(y, cells)
    idx_by_ref = [np.where(refs == r)[0] for r in range(refs.max() + 1)]
    shufflable = [ix for ix in idx_by_ref if len(np.unique(cells[ix])) > 1]
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for b in range(n_perm):
        c = cells.copy()
        for ix in shufflable:
            c[ix] = c[rng.permutation(ix)]
        null[b] = cell_share(y, c)
    p = (1 + np.sum(null >= obs - 1e-12)) / (1 + n_perm)
    return {"observed": obs, "p_value": float(p), "null": null, "n": len(y),
            "n_refs": len(idx_by_ref), "n_refs_shufflable": len(shufflable),
            "n_curves_shufflable": int(sum(len(ix) for ix in shufflable))}


def stage2_verdict(split_p50, perm_p50, alpha):
    """Spec Stage 2 pass rule for edge position:
    (a) within-reference permutation p < alpha, and
    (b) reference share <= mineral_class + sorbate_class + mineral_sorbate shares."""
    s = split_p50.set_index("component")["share"]
    class_share = s.get("mineral_class", 0) + s.get("sorbate_class", 0) + s.get("mineral_sorbate", 0)
    ref_share = s.get("reference", np.nan)
    a = perm_p50["p_value"] < alpha
    b = ref_share <= class_share
    if a and b:
        verdict, why = "PASS", "classes explain more than chance and more than study-to-study variation"
    elif not b:
        verdict, why = "FAIL (study dominates)", "the reference (study) share is larger than the class share"
    else:
        verdict, why = "FAIL (not above chance)", "the class share is not larger than with labels shuffled within papers"
    return {"verdict": verdict, "reason": why, "class_share": float(class_share), "reference_share": float(ref_share),
            "perm_p": perm_p50["p_value"]}
