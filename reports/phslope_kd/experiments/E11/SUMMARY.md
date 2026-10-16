# E11 What does the steepness of a curve mean?

**Plain English.** On a log scale, the steepness of a sorption curve against pH roughly counts how many hydrogen ions are released (or taken up) when one sorbate binds. If that were the main driver, curves of the same sorbate would have similar steepness whoever measured them. We checked whether steepness differs more between sorbates than between papers. Result: **UNDECIDED (ratio interval includes 1)**.

> EXPLORATORY. 641 curves (E1 main set), development papers only. The 'proton count' reading is a hypothesis (LITERATURE_REVIEW.md). Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## |b| (log10 K per pH unit) by sorbate (>= 8 curves), median with paper-bootstrap 95% interval

| sorbate | direction | curves | papers | median_abs_b | median_lo | median_hi | q25 | q75 |
|---|---|---|---|---|---|---|---|---|
| U(+6) | rising | 116 | 29 | 0.921 | 0.631 | 1.12 | 0.444 | 1.28 |
| Se(+4) | falling | 66 | 15 | 0.547 | 0.329 | 0.859 | 0.305 | 0.949 |
| Se(+6) | falling | 55 | 11 | 0.59 | 0.465 | 0.663 | 0.442 | 0.676 |
| Np(+5) | rising | 46 | 14 | 0.552 | 0.413 | 0.889 | 0.41 | 0.907 |
| Ni(+2) | rising | 43 | 12 | 0.45 | 0.363 | 0.579 | 0.348 | 0.627 |
| Ra(+2) | rising | 41 | 10 | 0.335 | 0.147 | 0.704 | 0.17 | 0.852 |
| Eu(+3) | rising | 38 | 15 | 0.642 | 0.477 | 0.782 | 0.449 | 0.869 |
| Am(+3) | rising | 36 | 7 | 0.549 | 0.435 | 0.621 | 0.464 | 0.638 |
| Oxalic acid | falling | 23 | 5 | 0.538 | 0.336 | 0.555 | 0.409 | 0.559 |
| Sr(+2) | rising | 23 | 9 | 0.496 | 0.22 | 0.928 | 0.244 | 0.941 |
| Zn(+2) | rising | 21 | 10 | 0.671 | 0.456 | 0.941 | 0.445 | 0.915 |
| U(+6) | falling | 16 | 5 | 1.21 | 0.527 | 1.92 | 0.834 | 1.92 |
| Co(+2) | rising | 16 | 5 | 0.35 | 0.226 | 0.975 | 0.231 | 0.531 |
| Pu(+5) | rising | 11 | 2 | 0.773 | 0.16 | 0.782 | 0.746 | 0.814 |
| Th(+4) | rising | 9 | 4 | 0.961 | 0.667 | 1.98 | 0.661 | 1.05 |
| Cd(+2) | rising | 8 | 3 | 0.694 | 0.481 | 1 | 0.492 | 0.785 |
| Pu | rising | 8 | 2 | 0.62 | 0.218 | 0.717 | 0.428 | 0.767 |

## Variance of |b| (REML: sorbate x direction, mineral, paper/lineage unit, residual)

| component | variance | share |
|---|---|---|
| sorbate | 0.0576 | 0.223 |
| mineral | 0.0455 | 0.176 |
| paper | 0.0654 | 0.253 |
| residual | 0.0904 | 0.349 |

Between-sorbate / between-paper variance ratio: 0.88, parametric-bootstrap 95% interval [0.30, 1.83] (rule: interval above 1 -> interpretable).

Share of |b| within 0.1 of a whole or half number: 38% (40% expected by chance for a smooth spread). No clustering at simple stoichiometries is claimed unless this is clearly above 40%.
