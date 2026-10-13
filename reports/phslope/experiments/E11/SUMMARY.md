# E11 What does the steepness of a curve mean?

**Plain English.** On a log scale, the steepness of a sorption curve against pH roughly counts how many hydrogen ions are released (or taken up) when one sorbate binds. If that were the main driver, curves of the same sorbate would have similar steepness whoever measured them. We checked whether steepness differs more between sorbates than between papers. Result: **UNDECIDED (ratio interval includes 1)**.

> EXPLORATORY. 757 curves (E1 main set), development papers only. The 'proton count' reading is a hypothesis (LITERATURE_REVIEW.md). Locked set hash `88b1c3a1b769`. Commit `2cdce27`.

## |b| (log10 K per pH unit) by sorbate (>= 8 curves), median with paper-bootstrap 95% interval

| sorbate | direction | curves | papers | median_abs_b | median_lo | median_hi | q25 | q75 |
|---|---|---|---|---|---|---|---|---|
| U(+6) | rising | 129 | 26 | 1.04 | 0.63 | 1.27 | 0.577 | 1.42 |
| Se(+4) | falling | 79 | 18 | 0.6 | 0.307 | 0.974 | 0.291 | 1.13 |
| Se(+6) | falling | 57 | 11 | 0.646 | 0.511 | 0.762 | 0.438 | 0.742 |
| Am(+3) | rising | 54 | 10 | 0.586 | 0.42 | 0.635 | 0.463 | 0.796 |
| Ni(+2) | rising | 52 | 14 | 0.401 | 0.342 | 0.52 | 0.326 | 0.578 |
| Np(+5) | rising | 50 | 14 | 0.489 | 0.418 | 0.798 | 0.415 | 0.834 |
| Ra(+2) | rising | 44 | 9 | 0.581 | 0.18 | 1.11 | 0.201 | 1.19 |
| Eu(+3) | rising | 42 | 13 | 0.57 | 0.507 | 0.739 | 0.452 | 0.852 |
| Oxalic acid | falling | 28 | 7 | 0.535 | 0.336 | 0.634 | 0.392 | 0.627 |
| Sr(+2) | rising | 26 | 9 | 0.452 | 0.216 | 0.828 | 0.232 | 0.917 |
| Zn(+2) | rising | 22 | 9 | 0.63 | 0.485 | 1.04 | 0.438 | 0.959 |
| U(+6) | falling | 18 | 5 | 1.67 | 0.725 | 2.34 | 0.862 | 2.52 |
| Ca(+2) | rising | 13 | 3 | 0.347 | 0.241 | 1.22 | 0.252 | 1.02 |
| Cu(+2) | rising | 12 | 3 | 0.724 | 0.681 | 0.842 | 0.623 | 0.899 |
| Co(+2) | rising | 12 | 5 | 0.82 | 0.309 | 0.984 | 0.312 | 1 |
| Pu(+5) | rising | 12 | 2 | 0.777 | 0.264 | 0.803 | 0.674 | 0.817 |
| Th(+4) | rising | 9 | 4 | 0.287 | 0.285 | 1.05 | 0.272 | 0.806 |
| Cd(+2) | rising | 8 | 3 | 0.694 | 0.481 | 1.6 | 0.492 | 1.24 |

## Variance of |b| (REML: sorbate x direction, mineral, paper/lineage unit, residual)

| component | variance | share |
|---|---|---|
| sorbate | 0.0726 | 0.288 |
| mineral | 0.0415 | 0.165 |
| paper | 0.0564 | 0.223 |
| residual | 0.0819 | 0.324 |

Between-sorbate / between-paper variance ratio: 1.29, parametric-bootstrap 95% interval [0.56, 2.42] (rule: interval above 1 -> interpretable).

Share of |b| within 0.1 of a whole or half number: 39% (40% expected by chance for a smooth spread). No clustering at simple stoichiometries is claimed unless this is clearly above 40%.
