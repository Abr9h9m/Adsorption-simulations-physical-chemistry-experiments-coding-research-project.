# E7 Carbonate (step 1a: CO2 partial pressure, no DIC)

**Plain English.** Dissolved carbonate (from CO2 in air) grabs uranium and some other metals in solution and can pull them off minerals at high pH. We replaced the old yes/no 'CO2 present' flag with the actual CO2 pressure each paper reported and tested whether it improves predictions above pH 7. Result: **DO NOT KEEP log10 pCO2 (rule not met)**. The full test, which converts CO2 pressure into dissolved carbonate at each pH, needs carbonate equilibrium constants from a source Samuel chooses (decision D5).

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `3e5912d`.

## What the old CO2 flag meant

Of the 861 development curves flagged 'CO2 present', 87% are simply open to air (reported pCO2 2.5e-4 to 5e-4 bar):

| atmosphere | curves |
|---|---|
| air_equilibrated | 750 |
| co2_free | 83 |
| controlled_co2 | 18 |
| unknown | 10 |

## Held-out log10 K RMSE at pH > 7: E1 + log10 pCO2 minus E1 (negative = better)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | set | sorbates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 + log10 pCO2 | E1 | 147 | 0.0587 | -0.0725 | 0.149 | 0.0122 | -0.0291 | 0.0426 | 1.07 | 1.01 | 0.456 | 0 | carbonate-sensitive | U(+6), Np(+5), Eu(+3), Am(+3) |
| E1 + log10 pCO2 | E1 | 152 | 0.0138 | -0.0247 | 0.0426 | -1.12e-05 | -0.0162 | 0.0249 | 0.532 | 0.518 | 0.5 | 0 | control | Se(+4), Oxalic acid, Ni(+2) |

Level coefficient of log10 pCO2 (full development fit): -0.204 +/- 0.139 (95%), log10 K units per decade of pCO2. Correlation of log10 pCO2 with the native edge: 0.13 (carbonate and pH are coupled; read the coefficient with that in mind).

## Not done

- DIC(pH) covariate (needs carbonate constants and their source, D5).
- Step 2 (aqueous speciation, e.g. PHREEQC) needs Samuel's go-ahead (D6).

## Analyst notes

- CO2 lowers the overall level of log10 K (-0.20 per decade of pCO2, 95% interval excluding zero), but a constant shift does not improve held-out log10 K above pH 7 for the carbonate-sensitive sorbates. Carbonate complexation grows with pH, so the expected effect is a pH-dependent term (DIC(pH)); that test waits for the carbonate constants (D5).
- "co2_free" curves among the CO2-flagged ones (83) carry carbonate as an added electrolyte (C(+4)) rather than as gas.
