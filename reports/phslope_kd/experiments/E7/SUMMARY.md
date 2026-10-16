# E7 Carbonate (step 1a: CO2 partial pressure, no DIC)

**Plain English.** Dissolved carbonate (from CO2 in air) grabs uranium and some other metals in solution and can pull them off minerals at high pH. We replaced the old yes/no 'CO2 present' flag with the actual CO2 pressure each paper reported and tested whether it improves predictions above pH 7. Result: **DO NOT KEEP log10 pCO2 (rule not met)**. The full test, which converts CO2 pressure into dissolved carbonate at each pH, needs carbonate equilibrium constants from a source Samuel chooses (decision D5).

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## What the old CO2 flag meant

Of the 848 development curves flagged 'CO2 present', 88% are simply open to air (reported pCO2 2.5e-4 to 5e-4 bar):

| atmosphere | curves |
|---|---|
| air_equilibrated | 744 |
| co2_free | 76 |
| controlled_co2 | 18 |
| unknown | 10 |

## Held-out log10 K RMSE at pH > 7: E1 + log10 pCO2 minus E1 (negative = better)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | set | sorbates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 + log10 pCO2 | E1 | 126 | 0.0531 | -0.0531 | 0.293 | 0.0207 | -0.0104 | 0.0645 | 0.986 | 0.933 | 0.381 | 0 | carbonate-sensitive | U(+6), Np(+5), Eu(+3), Am(+3) |
| E1 + log10 pCO2 | E1 | 122 | -0.01 | -0.037 | 0.0421 | -0.00481 | -0.0289 | 0.00567 | 0.55 | 0.56 | 0.557 | 0 | control | Se(+4), Oxalic acid, Ni(+2) |

Level coefficient of log10 pCO2 (full development fit): -0.220 +/- 0.131 (95%), log10 K units per decade of pCO2. Correlation of log10 pCO2 with the native edge: 0.26 (carbonate and pH are coupled; read the coefficient with that in mind).

## Not done

- DIC(pH) covariate (needs carbonate constants and their source, D5).
- Step 2 (aqueous speciation, e.g. PHREEQC) needs Samuel's go-ahead (D6).
