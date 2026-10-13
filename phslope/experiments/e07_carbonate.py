"""E7 -- carbonate (protocol section 5, E7). EXPLORATORY; development papers only.

Step 1 as specified needs the equilibrium dissolved inorganic carbon DIC(pH), computed from pCO2 and the
carbonate acid constants with a cited source (decision D5). D5 is open, so this module runs STEP 1a:
the continuous variables that need no constants, and a test of log10 pCO2 as an E1 level covariate.

Variables (data.py, from the Gas* and C(+4) electrolyte columns):
  log10_pco2        reported CO2 partial pressure (bar); curves with no CO2 reported get the floor
                    pco2_floor_log10 (experiments.yaml) plus an indicator `atmosphere_unknown` when the
                    atmosphere itself is not reported (none vs not reported are kept apart)
  atmosphere        air_equilibrated (2.5e-4 to 5e-4 bar), controlled_co2, co2_free, unknown
  dic_added_mol_L   carbonate added as electrolyte
Test: E1 with and without log10 pCO2 (+ indicator), leave-one-unit-out; held-out log10 K RMSE at pH > 7
for the pre-declared carbonate-sensitive sorbates and the control set. Decision (pre-declared): keep if
the sensitive set improves (paired 95% interval below zero) and the control set's interval includes zero.
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E7")


def carbonate_columns(c, floor):
    c = c.copy()
    c["log10_pco2_f"] = c["log10_pco2"].fillna(floor)
    c["atmosphere_unknown"] = (c["atmosphere"] == "unknown").astype(float)
    return c


def run(seed=None):
    ecfg = load_exp_config()
    cfg = ecfg["e7"]
    seed = ecfg["seed"] if seed is None else seed
    curves, obs = build(purpose="E7")
    stamp = exp_stamp(extra={"experiment": "E7", "step": "1a (no DIC; D5 open)"})
    write_run_info(OUT, stamp)
    curves = carbonate_columns(E1.attach_units(curves), cfg["pco2_floor_log10"])
    _, c = E1.main_set(curves, ecfg["e1"])

    flagged = curves[curves["co2_present"].astype(bool)]
    atm = flagged["atmosphere"].value_counts().rename_axis("atmosphere").reset_index(name="curves")
    air_share = float((flagged["atmosphere"] == "air_equilibrated").mean())

    P0 = E1.cross_validate(c, obs, ecfg["e1"], covariates=True, seed=seed)
    P1 = E1.cross_validate(c, obs, ecfg["e1"], covariates=True, seed=seed,
                           extra_covs=["log10_pco2_f", "atmosphere_unknown"])
    rows = []
    for name, P in (("E1", P0), ("E1 + log10 pCO2", P1)):
        m = E1.logk_metrics(P, obs, min_pH=7.0).assign(model=name)
        rows.append(m)
    M = pd.concat(rows).merge(c[["curve_id", "unit", "sorbate"]], on="curve_id")
    out = []
    for label, sorbs in (("carbonate-sensitive", cfg["sensitive_sorbates"]), ("control", cfg["control_sorbates"])):
        d = M[M["sorbate"].isin(sorbs)].rename(columns={"logK_rmse": "metric"})
        out.append(H.paired(d, "E1 + log10 pCO2", ["E1"], B=ecfg["harness"]["paper_bootstrap_B"], seed=seed,
                            metric="metric").assign(set=label, sorbates=", ".join(sorbs)))
    D = pd.concat(out)
    sens = D[D["set"] == "carbonate-sensitive"].iloc[0] if (D["set"] == "carbonate-sensitive").any() else None
    ctrl = D[D["set"] == "control"].iloc[0] if (D["set"] == "control").any() else None
    keep = sens is not None and sens["diff_hi"] < 0 and (ctrl is None or ctrl["diff_lo"] <= 0 <= ctrl["diff_hi"])
    verdict = "KEEP log10 pCO2" if keep else "DO NOT KEEP log10 pCO2 (rule not met)"
    full = E1.E1Model(ecfg["e1"], True, ["log10_pco2_f", "atmosphere_unknown"]).fit(c)
    names = ["intercept"] + full.level_fixed
    i = names.index("log10_pco2_f") if "log10_pco2_f" in names else None
    coef = (full.fa["beta"][i], np.sqrt(full.cov_a[i, i])) if i is not None else (np.nan, np.nan)
    corr = c[["log10_pco2_f", "pH_native"]].corr().iloc[0, 1]

    D.to_csv(os.path.join(OUT, "paired_logK_pH_above_7.csv"), index=False)
    atm.to_csv(os.path.join(OUT, "atmosphere_of_co2_flagged_curves.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E7 Carbonate (step 1a: CO2 partial pressure, no DIC)", "",
        "**Plain English.** Dissolved carbonate (from CO2 in air) grabs uranium and some other metals in "
        "solution and can pull them off minerals at high pH. We replaced the old yes/no 'CO2 present' flag with "
        f"the actual CO2 pressure each paper reported and tested whether it improves predictions above pH 7. "
        f"Result: **{verdict}**. The full test, which converts CO2 pressure into dissolved carbonate at each pH, "
        "needs carbonate equilibrium constants from a source Samuel chooses (decision D5).", "",
        f"> EXPLORATORY. Development papers only. Locked set hash `{stamp['locked_set_hash']}`. Commit "
        f"`{stamp['git_commit']}`.", "",
        "## What the old CO2 flag meant", "",
        f"Of the {len(flagged)} development curves flagged 'CO2 present', {air_share:.0%} are simply open to air "
        "(reported pCO2 2.5e-4 to 5e-4 bar):", "", md_table(atm), "",
        "## Held-out log10 K RMSE at pH > 7: E1 + log10 pCO2 minus E1 (negative = better)", "", md_table(D), "",
        f"Level coefficient of log10 pCO2 (full development fit): {coef[0]:.3f} +/- {1.96 * coef[1]:.3f} "
        f"(95%), log10 K units per decade of pCO2. Correlation of log10 pCO2 with the native edge: {corr:.2f} "
        "(carbonate and pH are coupled; read the coefficient with that in mind).", "",
        "## Not done", "",
        "- DIC(pH) covariate (needs carbonate constants and their source, D5).",
        "- Step 2 (aqueous speciation, e.g. PHREEQC) needs Samuel's go-ahead (D6).",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E7", verdict, "step 1a only (pCO2); DIC waits for D5", stamp)
    record_adjustment("E7 log10 pCO2 level covariate (step 1a)", verdict,
                      "; ".join(f"{r.set}: {r.median_diff:.3f} [{r.diff_lo:.3f}, {r.diff_hi:.3f}]" for r in D.itertuples()))
    print(f"E7 {verdict}")
    return D


if __name__ == "__main__":
    run()
