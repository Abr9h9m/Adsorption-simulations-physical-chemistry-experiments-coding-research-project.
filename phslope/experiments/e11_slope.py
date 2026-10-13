"""E11 -- proton stoichiometry: is the log10 K slope b chemically interpretable? (Addendum 1, E11)
EXPLORATORY; development papers only.

If sorbing one sorbate releases (cations) or takes up (anions) n protons, the slope of log10 K against
pH is near n in the simplest case. That expectation is a HYPOTHESIS: surface-complex stoichiometry
depends on the complex (see LITERATURE_REVIEW.md), so the data may spread widely.

Data: per-curve log10 K line fits (E1 main set: right sign, R2 >= 0.5, crossing near the data).
1. Distribution of b by sorbate and direction (median, IQR, paper-level bootstrap interval of the median).
2. Share of |b| within 0.3 of the nearest integer or half-integer, against what uniform spread would give.
3. Variance split of b: REML with crossed random effects for sorbate x direction, mineral, and paper
   (unit); decision (pre-declared): interpretable if between-sorbate variance exceeds between-paper
   variance (ratio > 1) with a parametric-bootstrap 95% interval excluding 1.
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)
from phslope.reml import fit_reml, simulate

OUT = os.path.join(EXP_DIR, "E11")
FACTORS = {"sorbate": "sorbate_dir", "mineral": "mineral", "paper": "unit"}


def near_half_integer_share(b, tol=0.3):
    x = np.abs(np.asarray(b, float)) * 2
    return float(np.mean(np.abs(x - np.round(x)) <= 2 * tol))


def variance_ratio(d, B, seed):
    fit = fit_reml(d, "b_abs", FACTORS)
    comp = fit["components"]
    ratio = comp["sorbate"] / comp["paper"] if comp["paper"] > 0 else np.inf
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(B):
        y = simulate(d, FACTORS, None, comp, fit["beta"], rng)
        try:
            c2 = fit_reml(d.assign(b_abs=y), "b_abs", FACTORS)["components"]
            boots.append(c2["sorbate"] / c2["paper"] if c2["paper"] > 0 else np.inf)
        except ValueError:
            continue
    lo, hi = np.percentile(np.clip(boots, 0, 1e6), [2.5, 97.5])
    return comp, ratio, lo, hi


def run(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    curves, _ = build(purpose="E11")
    stamp = exp_stamp(extra={"experiment": "E11"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    c["b_abs"] = c["b"].abs()
    c["sorbate_dir"] = c["sorbate"] + "|" + c["shape"]

    rng = np.random.default_rng(seed)
    rows = []
    for (s, shape), g in c.groupby(["sorbate", "shape"]):
        if len(g) < 8:
            continue
        units = g["unit"].unique()
        meds = [np.median(np.concatenate([g.loc[g["unit"] == u, "b_abs"].to_numpy() for u in rng.choice(units, len(units))]))
                for _ in range(300)] if len(units) >= 2 else [np.nan]
        rows.append({"sorbate": s, "direction": shape, "curves": len(g), "papers": len(units),
                     "median_abs_b": g["b_abs"].median(), "median_lo": np.nanpercentile(meds, 2.5),
                     "median_hi": np.nanpercentile(meds, 97.5), "q25": g["b_abs"].quantile(.25),
                     "q75": g["b_abs"].quantile(.75)})
    T = pd.DataFrame(rows).sort_values("curves", ascending=False)
    share_tight = near_half_integer_share(c["b_abs"], 0.1)
    comp, ratio, lo, hi = variance_ratio(c, ecfg["e11"]["bootstrap_B"], seed)
    tot = sum(comp.values())
    V = pd.DataFrame([{"component": k, "variance": v, "share": v / tot} for k, v in comp.items()])
    verdict = "INTERPRETABLE (sorbate > paper)" if lo > 1 else (
        "DOMINATED BY PAPER EFFECTS (paper > sorbate)" if hi < 1 else "UNDECIDED (ratio interval includes 1)")

    T.to_csv(os.path.join(OUT, "slope_by_sorbate.csv"), index=False)
    V.to_csv(os.path.join(OUT, "slope_variance.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E11 What does the steepness of a curve mean?", "",
        "**Plain English.** On a log scale, the steepness of a sorption curve against pH roughly counts how many "
        "hydrogen ions are released (or taken up) when one sorbate binds. If that were the main driver, curves "
        "of the same sorbate would have similar steepness whoever measured them. We checked whether steepness "
        f"differs more between sorbates than between papers. Result: **{verdict}**.", "",
        f"> EXPLORATORY. {len(c)} curves (E1 main set), development papers only. The 'proton count' reading is a "
        f"hypothesis (LITERATURE_REVIEW.md). Locked set hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## |b| (log10 K per pH unit) by sorbate (>= 8 curves), median with paper-bootstrap 95% interval", "",
        md_table(T), "",
        "## Variance of |b| (REML: sorbate x direction, mineral, paper/lineage unit, residual)", "", md_table(V), "",
        f"Between-sorbate / between-paper variance ratio: {ratio:.2f}, parametric-bootstrap 95% interval "
        f"[{lo:.2f}, {hi:.2f}] (rule: interval above 1 -> interpretable).", "",
        f"Share of |b| within 0.1 of a whole or half number: {share_tight:.0%} (40% expected by chance for a "
        "smooth spread). No clustering at simple stoichiometries is claimed unless this is clearly above 40%.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E11", verdict, f"ratio {ratio:.2f} [{lo:.2f}, {hi:.2f}]", stamp)
    record_adjustment("E11 slope as a chemical descriptor (library field)", verdict,
                      f"sorbate/paper variance ratio {ratio:.2f} [{lo:.2f}, {hi:.2f}]")
    print(verdict, ratio, lo, hi)


if __name__ == "__main__":
    run()
