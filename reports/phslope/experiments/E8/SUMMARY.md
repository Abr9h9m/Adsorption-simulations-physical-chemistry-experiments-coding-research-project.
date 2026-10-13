# E8 Ionic strength by sorbate type

**Plain English.** Overall, the amount of background salt did not move the sorption edge. Here we checked whether it matters for weakly held cations (like caesium or strontium), where textbook chemistry says more salt should reduce sorption, using experiments where the same lab changed only the salt. Result: **EFFECT FOUND (meets rule)**.

> EXPLORATORY. Development papers only. Classes pre-declared in experiments.yaml. Locked set hash `88b1c3a1b769`. Commit `b5c03f2-dirty`.

## Within-paper ionic-strength series (solids, total sorbate, temperature within 10%)

| i_class | series | curves | papers |
|---|---|---|---|
| inner_sphere_prone | 51 | 183 | 36 |
| organic_acid | 1 | 6 | 1 |
| outer_sphere_prone | 11 | 29 | 7 |
| oxyanion | 18 | 49 | 11 |

## Effects per unit log10 I (pH units for edges, fraction sorbed for plateau)

13 class-level tests; q = Benjamini-Hochberg over them.

| analysis | class | outcome | n_series | n | n_clusters | slope | ci_lo | ci_hi | p | q_value |
|---|---|---|---|---|---|---|---|---|---|---|
| within paper | outer_sphere_prone | native_edge | 11 | 29 | 7 | 0.787 | 0.323 | 1.25 | 0.000891 | 0.0029 |
| within paper | outer_sphere_prone | solids_normalised_edge | 11 | 29 | 7 | 0.839 | 0.233 | 1.44 | 0.00667 | 0.0145 |
| within paper | outer_sphere_prone | plateau | 11 | 29 | 7 | -0.062 | -0.109 | -0.0148 | 0.01 | 0.0163 |
| within paper | inner_sphere_prone | native_edge | 51 | 183 | 36 | 0.15 | -0.0114 | 0.311 | 0.0685 | 0.0891 |
| within paper | inner_sphere_prone | solids_normalised_edge | 51 | 183 | 36 | 0.193 | 0.0373 | 0.349 | 0.0151 | 0.0218 |
| within paper | inner_sphere_prone | plateau | 51 | 183 | 36 | 0.00592 | -0.00181 | 0.0136 | 0.134 | 0.145 |
| within paper | oxyanion | native_edge | 18 | 49 | 11 | -0.295 | -0.462 | -0.128 | 0.000529 | 0.00236 |
| within paper | oxyanion | solids_normalised_edge | 18 | 49 | 11 | -0.356 | -0.623 | -0.09 | 0.00875 | 0.0162 |
| within paper | oxyanion | plateau | 18 | 49 | 11 | -0.0249 | -0.0384 | -0.0115 | 0.000267 | 0.00236 |
| within paper | organic_acid | native_edge | 1 | 6 |  |  |  |  |  |  |
| within paper | organic_acid | solids_normalised_edge | 1 | 6 |  |  |  |  |  |  |
| within paper | organic_acid | plateau | 1 | 6 |  |  |  |  |  |  |
| within paper | all | native_edge | 81 | 267 | 52 | 0.113 | -0.0522 | 0.278 | 0.18 |  |
| within paper | all | solids_normalised_edge | 81 | 267 | 52 | 0.13 | -0.0552 | 0.315 | 0.169 |  |
| within paper | all | plateau | 81 | 267 | 52 | -0.0105 | -0.0211 | 0.00022 | 0.0549 |  |
| cross paper | outer_sphere_prone | native_edge |  | 94 | 22 | 0.652 | 0.282 | 1.02 | 0.000545 | 0.00236 |
| cross paper | inner_sphere_prone | native_edge |  | 457 | 86 | 0.111 | -0.014 | 0.236 | 0.0819 | 0.0968 |
| cross paper | oxyanion | native_edge |  | 160 | 32 | -0.0759 | -0.461 | 0.31 | 0.699 | 0.699 |
| cross paper | organic_acid | native_edge |  | 42 | 13 | -1.2 | -1.93 | -0.458 | 0.00148 | 0.00385 |
| cross paper | all | native_edge |  | 757 | 143 | 0.104 | -0.0232 | 0.23 | 0.109 |  |

## Outer-sphere minus inner-sphere slope (native edge, within paper)

0.638 pH per log10 I, 95% interval [0.165, 1.110], p = 0.00823, n = 212.

Expected sign for outer-sphere complexes: sorption decreases as ionic strength increases, i.e. a rising edge moves to higher pH (positive slope).

## Bands vs linear (within paper, native edge)

AIC linear in log10 I: 456.1; AIC with bands (<0.01, 0.01-0.1, >0.1 M): 458.2 (lower is better).

Files: `within_paper_series.csv`, `effects.csv`.
