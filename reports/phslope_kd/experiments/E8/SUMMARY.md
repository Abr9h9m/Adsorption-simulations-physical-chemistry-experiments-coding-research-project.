# E8 Ionic strength by sorbate type

**Plain English.** Overall, the amount of background salt did not move the sorption edge. Here we checked whether it matters for weakly held cations (like caesium or strontium), where textbook chemistry says more salt should reduce sorption, using experiments where the same lab changed only the salt. Result: **EFFECT FOUND (meets rule)**.

> EXPLORATORY. Development papers only. Classes pre-declared in experiments.yaml. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Within-paper ionic-strength series (solids, total sorbate, temperature within 10%)

| i_class | series | curves | papers |
|---|---|---|---|
| inner_sphere_prone | 40 | 147 | 27 |
| organic_acid | 2 | 8 | 2 |
| outer_sphere_prone | 13 | 35 | 8 |
| oxyanion | 17 | 43 | 10 |

## Effects per unit log10 I (pH units for edges, fraction sorbed for plateau)

16 class-level tests; q = Benjamini-Hochberg over them.

| analysis | class | outcome | n_series | n | n_clusters | slope | ci_lo | ci_hi | p | q_value |
|---|---|---|---|---|---|---|---|---|---|---|
| within paper | outer_sphere_prone | native_edge | 13 | 35 | 8 | 1.22 | 0.44 | 2.01 | 0.00219 | 0.00971 |
| within paper | outer_sphere_prone | solids_normalised_edge | 13 | 35 | 8 | 1.22 | 0.44 | 2.01 | 0.00219 | 0.00971 |
| within paper | outer_sphere_prone | plateau | 13 | 35 | 8 | -0.0759 | -0.127 | -0.0248 | 0.00364 | 0.00971 |
| within paper | inner_sphere_prone | native_edge | 40 | 147 | 27 | 0.0932 | -0.175 | 0.362 | 0.496 | 0.611 |
| within paper | inner_sphere_prone | solids_normalised_edge | 40 | 147 | 27 | 0.0932 | -0.175 | 0.362 | 0.496 | 0.611 |
| within paper | inner_sphere_prone | plateau | 40 | 147 | 27 | 0.00123 | -0.00818 | 0.0106 | 0.798 | 0.798 |
| within paper | oxyanion | native_edge | 17 | 43 | 10 | -0.44 | -0.734 | -0.146 | 0.00336 | 0.00971 |
| within paper | oxyanion | solids_normalised_edge | 17 | 43 | 10 | -0.44 | -0.734 | -0.146 | 0.00336 | 0.00971 |
| within paper | oxyanion | plateau | 17 | 43 | 10 | -0.0351 | -0.105 | 0.0348 | 0.325 | 0.52 |
| within paper | organic_acid | native_edge | 2 | 8 | 2 | -0.295 | -0.827 | 0.237 | 0.277 | 0.492 |
| within paper | organic_acid | solids_normalised_edge | 2 | 8 | 2 | -0.295 | -0.827 | 0.237 | 0.277 | 0.492 |
| within paper | organic_acid | plateau | 2 | 8 | 2 | -0.01 | -0.0763 | 0.0562 | 0.766 | 0.798 |
| within paper | all | native_edge | 72 | 233 | 45 | 0.138 | -0.148 | 0.424 | 0.345 |  |
| within paper | all | solids_normalised_edge | 72 | 233 | 45 | 0.138 | -0.148 | 0.424 | 0.345 |  |
| within paper | all | plateau | 72 | 233 | 45 | -0.0185 | -0.0395 | 0.00256 | 0.0852 |  |
| cross paper | outer_sphere_prone | native_edge |  | 76 | 21 | 1.32 | 0.492 | 2.15 | 0.00177 | 0.00971 |
| cross paper | inner_sphere_prone | native_edge |  | 397 | 86 | 0.038 | -0.112 | 0.188 | 0.618 | 0.707 |
| cross paper | oxyanion | native_edge |  | 133 | 26 | -0.224 | -0.701 | 0.253 | 0.358 | 0.52 |
| cross paper | organic_acid | native_edge |  | 32 | 11 | -1.32 | -2.43 | -0.216 | 0.0191 | 0.0437 |
| cross paper | all | native_edge |  | 639 | 133 | 0.0568 | -0.125 | 0.238 | 0.539 |  |

## Outer-sphere minus inner-sphere slope (native edge, within paper)

1.130 pH per log10 I, 95% interval [0.331, 1.929], p = 0.00555, n = 182.

Expected sign for outer-sphere complexes: sorption decreases as ionic strength increases, i.e. a rising edge moves to higher pH (positive slope).

## Bands vs linear (within paper, native edge)

AIC linear in log10 I: 537.6; AIC with bands (<0.01, 0.01-0.1, >0.1 M): 540.4 (lower is better).

Files: `within_paper_series.csv`, `effects.csv`.
