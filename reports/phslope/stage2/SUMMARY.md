# Stage 2 summary: do mineral and sorbate classes matter?

> **EXPLORATORY.** Stage 1 did not meet its pre-set survival rule (46.8% of census-set curves survived QC; 80% required). Samuel chose on 2026-10-12 to continue with the core library. The classes in Part B are the PROPOSED assignment in classes.yaml, **not yet confirmed** by Samuel and Dr. Black. Nothing here is a confirmatory result.

Run: commit `fa0386e`, config `cf2a6ba65bec`, data `library: C:\Users\itzju\Mineral Fingerprinting\reports\phslope\stage1\library`, 2026-10-12T23:48:44Z.

## Part A: registration and shape components (task 2.2)

- Single-edge (rising/falling) core curves registered: 405 of 745 core curves. Registered slope source: {'spline': 405}.
- Slope variance removed by registration alone (aligning edge position, width and height): 86.3% overall; rising 77.2%; falling 86.9%.
- FPCA: 5 component(s) kept (rule: >= 90% of variance, max 5). Explained: FPC1 60.7%, FPC2 13.1%, FPC3 8.6%, FPC4 6.9%, FPC5 4.7%. 26.8% of the cells were filled by iterative SVD imputation, so these shares are somewhat optimistic.
- Score uncertainty (median bootstrap SD of projected scores vs the spread of scores across curves): FPC1 0.0925 vs spread 0.285, FPC2 0.0937 vs spread 0.132, FPC3 0.0887 vs spread 0.107, FPC4 0.0621 vs spread 0.0965, FPC5 0.0504 vs spread 0.0792.

Files: `registration_and_scores.csv` (warp a, b, w per curve, ratios to the median curve, FPC scores and SDs), `fpca_components.csv`, `registration_and_fpca.png`.

## Part B: class tests (tasks 2.3-2.5)

### Go/no-go: **PASS**

classes explain more than chance and more than study-to-study variation. For edge position: class share (mineral class + sorbate class + pair) = 60.8%, reference (study) share = 24.0%; within-reference permutation p = 0.0005 (2000 permutations).

Permutation informativeness: 31 of 141 references (217 of 576 curves) contain more than one class cell and can be shuffled; the rest are fixed under the null, which makes the test conservative.

Unassigned names (excluded): {'minerals': [], 'sorbates': []}

### Variance shares (95% cluster-bootstrap intervals over references)

| parameter | component | share | share_lo | share_hi |
|---|---|---|---|---|
| edge_pH | mineral_class | 0.0269 | 1.41e-06 | 0.0826 |
| edge_pH | sorbate_class | 0.257 | 0.087 | 0.406 |
| edge_pH | mineral_sorbate | 0.324 | 0.294 | 0.57 |
| edge_pH | reference | 0.24 | 0.0855 | 0.25 |
| edge_pH | residual | 0.152 | 0.0902 | 0.19 |
| log_width | mineral_class | 0.0283 | 4.25e-07 | 0.132 |
| log_width | sorbate_class | 0.14 | 0.0541 | 0.188 |
| log_width | mineral_sorbate | 0.193 | 0.239 | 0.46 |
| log_width | reference | 0.153 | 5.55e-08 | 0.159 |
| log_width | residual | 0.485 | 0.332 | 0.532 |
| height | mineral_class | 3.21e-07 | 2.22e-09 | 0.00351 |
| height | sorbate_class | 0.755 | 0.711 | 0.827 |
| height | mineral_sorbate | 0.064 | 0.0564 | 0.133 |
| height | reference | 0.105 | 0.0269 | 0.121 |
| height | residual | 0.0759 | 0.0412 | 0.0943 |
| fpc1 | mineral_class | 5.7e-09 | 0 | 0.0157 |
| fpc1 | sorbate_class | 9.6e-08 | 1.81e-10 | 0.0257 |
| fpc1 | mineral_sorbate | 9.65e-07 | 0.00458 | 0.79 |
| fpc1 | reference | 0.175 | 0 | 0.352 |
| fpc1 | residual | 0.825 | 0.178 | 0.946 |
| fpc2 | mineral_class | 0.0491 | 7.68e-09 | 0.136 |
| fpc2 | sorbate_class | 0.012 | 1.08e-09 | 0.138 |
| fpc2 | mineral_sorbate | 0.131 | 0.182 | 0.639 |
| fpc2 | reference | 0.0791 | 0 | 0.0875 |
| fpc2 | residual | 0.729 | 0.31 | 0.742 |
| fpc3 | mineral_class | 0.0286 | 4.35e-08 | 0.0838 |
| fpc3 | sorbate_class | 0.056 | 3.96e-08 | 0.135 |
| fpc3 | mineral_sorbate | 0.0368 | 0.103 | 0.472 |
| fpc3 | reference | 0.0546 | 0 | 0.13 |
| fpc3 | residual | 0.824 | 0.427 | 0.856 |
| fpc4 | mineral_class | 6.31e-08 | 0 | 0.0269 |
| fpc4 | sorbate_class | 0.0559 | 7.44e-10 | 0.22 |
| fpc4 | mineral_sorbate | 0.232 | 0.243 | 0.656 |
| fpc4 | reference | 0.0692 | 0 | 0.0402 |
| fpc4 | residual | 0.643 | 0.259 | 0.733 |
| fpc5 | mineral_class | 0.0211 | 1.78e-09 | 0.0719 |
| fpc5 | sorbate_class | 2.52e-07 | 0 | 0.184 |
| fpc5 | mineral_sorbate | 0.209 | 0.212 | 0.642 |
| fpc5 | reference | 0.078 | 0 | 0.105 |
| fpc5 | residual | 0.692 | 0.332 | 0.741 |

### Edge position with conditions as fixed effects (n = 567, 9 curves dropped for a missing covariate; temperature not included (reported for < 80% of curves); constant covariates dropped: none)

| component | share |
|---|---|
| mineral_class | 0.0495 |
| sorbate_class | 0.205 |
| mineral_sorbate | 0.343 |
| reference | 0.247 |
| residual | 0.156 |

### Clustering vs class labels (within-reference permutations)

| features | labels | n | ARI | ARI_p | ARI_null_mean | PERMANOVA_F | PERMANOVA_R2 | PERMANOVA_p |
|---|---|---|---|---|---|---|---|---|
| edge parameters | mineral_class | 576 | -0.0124 | 0.353 | -0.0131 | 9.39 | 0.0617 | 0.04 |
| edge parameters | sorbate_class | 576 | 0.139 | 0.0005 | 0.113 | 64.2 | 0.36 | 0.0005 |
| FPCA scores | mineral_class | 404 | 0.00808 | 0.507 | 0.00824 | 1.8 | 0.0178 | 0.0955 |
| FPCA scores | sorbate_class | 404 | 0.00437 | 0.541 | 0.00468 | 2.51 | 0.0306 | 0.201 |

Figures: `variance_shares.png`, `edge_grid.png`.

### Next decision

Stage 2 passes: continue to Stage 3 (descriptor tables, then freeze thresholds.yaml). (Exploratory: the verdict uses unconfirmed classes and a library that failed Stage 1.)

## Part C: exploratory groupings (config/schemes.yaml)

48 groupings tested on 576 core edge curves: one T-vs-F split per usable column of the mineral property table, two mineral schemes built from it, four sorbate schemes and four ionic-condition schemes. Each was tested for edge position (all) and log width and height (schemes only): variance share in a model with study as a second random effect, and a within-reference permutation test of the between-group share. 68 tests in total; q = Benjamini-Hochberg adjusted p. Significant after FDR: 10.

Mineral property table: `mineral properties.csv`; cell codes {'F': 1407, 'T': 532, 'TO': 46, 'O': 24, 'FO': 7} (only T and F used; TO/O/FO treated as missing). Rows left out pending correction: Calcite, Maghemite, Corundum. Minerals in the library with no row: hematite. The table has no source column, so these are uncited properties.

### Edge position, all groupings (sorted by q)

| grouping | kind | n_curves | n_groups | group_share | reference_share | between_group_R2 | p_value | q_value | curves_shufflable |
|---|---|---|---|---|---|---|---|---|---|
| sorbate_charge_form | sorbate_scheme | 569 | 8 | 0.48 | 0.288 | 0.192 | 0.0005 | 0.00566 | 162 |
| sorbate_redox | sorbate_scheme | 533 | 2 | 0.182 | 0.461 | 0.0579 | 0.0005 | 0.00566 | 121 |
| property: Manganese-containing | mineral_property | 477 | 2 | 0.346 | 0.354 | 0.0793 | 0.005 | 0.0378 | 25 |
| carbonate | condition_scheme | 576 | 2 | 0.0259 | 0.541 | 0.00568 | 0.0065 | 0.0442 | 46 |
| sorbate_element_group | sorbate_scheme | 575 | 10 | 0.134 | 0.442 | 0.108 | 0.0085 | 0.0525 | 156 |
| mineral_metal | mineral_scheme | 477 | 6 | 0.127 | 0.464 | 0.12 | 0.023 | 0.12 | 132 |
| property: Framework silicates (tectosilicates) | mineral_property | 477 | 2 | 0.0423 | 0.536 | 0.00278 | 0.0275 | 0.134 | 94 |
| property: Framework structure | mineral_property | 477 | 2 | 0.0255 | 0.544 | 0.00166 | 0.038 | 0.164 | 97 |
| property: Mixed metal oxides | mineral_property | 471 | 2 | 0.0182 | 0.555 | 0.0185 | 0.0435 | 0.164 | 119 |
| property: Hydrous minerals | mineral_property | 468 | 2 | 0.0125 | 0.524 | 0.013 | 0.05 | 0.164 | 106 |
| property: Anhydrous minerals | mineral_property | 456 | 2 | 0.0135 | 0.53 | 0.0155 | 0.05 | 0.164 | 106 |
| property: Hydroxides | mineral_property | 378 | 2 | 0.0401 | 0.493 | 0.0244 | 0.0515 | 0.164 | 95 |
| property: Amorphous (non-crystalline) | mineral_property | 460 | 2 | 0.0172 | 0.587 | 0.0271 | 0.053 | 0.164 | 101 |
| property: Polymorphs | mineral_property | 477 | 2 | 0.00437 | 0.555 | 0.0162 | 0.053 | 0.164 | 169 |
| mineral_structure | mineral_scheme | 477 | 6 | 0.0337 | 0.529 | 0.0702 | 0.0595 | 0.176 | 146 |
| property: Dioxides (MO2) | mineral_property | 452 | 2 | 0.0667 | 0.509 | 0.0389 | 0.062 | 0.176 | 104 |
| property: Iron-containing | mineral_property | 399 | 2 | 0.0423 | 0.5 | 0.0543 | 0.079 | 0.215 | 113 |
| property: Ion exchangers | mineral_property | 477 | 2 | 0.0227 | 0.537 | 0.0128 | 0.13 | 0.316 | 112 |
| property: Monoclinic crystals | mineral_property | 477 | 2 | 0.0358 | 0.531 | 0.0215 | 0.149 | 0.34 | 60 |
| sorbate_hsab | sorbate_scheme | 420 | 3 | 0.0136 | 0.54 | 0.028 | 0.15 | 0.34 | 76 |
| property: Thermally stable | mineral_property | 477 | 2 | 6.65e-08 | 0.557 | 0.00768 | 0.158 | 0.346 | 122 |
| property: Oxyhydroxides | mineral_property | 452 | 2 | 0.0234 | 0.53 | 0.0172 | 0.212 | 0.45 | 99 |
| property: Orthorhombic crystals | mineral_property | 477 | 2 | 1.72e-07 | 0.557 | 0.00166 | 0.225 | 0.463 | 72 |
| property: Magnesium-containing | mineral_property | 463 | 2 | 0.00947 | 0.546 | 0.00221 | 0.232 | 0.465 | 46 |
| property: Redox active | mineral_property | 477 | 2 | 0.0128 | 0.543 | 0.00969 | 0.384 | 0.67 | 100 |
| property: Redox inactive | mineral_property | 477 | 2 | 0.0128 | 0.543 | 0.00969 | 0.384 | 0.67 | 100 |
| property: Aluminosilicates | mineral_property | 477 | 2 | 0.000331 | 0.557 | 0.000218 | 0.427 | 0.714 | 87 |
| property: Hexagonal crystals | mineral_property | 477 | 2 | 0.00739 | 0.554 | 0.000535 | 0.431 | 0.714 | 99 |
| property: Clay minerals | mineral_property | 477 | 2 | 0.00103 | 0.556 | 0.000202 | 0.486 | 0.735 | 90 |
| property: Sheet silicates (phyllosilicates) | mineral_property | 477 | 2 | 0.00103 | 0.556 | 0.000202 | 0.486 | 0.735 | 90 |
| property: Alpha particle resistant | mineral_property | 477 | 2 | 1.33e-08 | 0.557 | 8.91e-05 | 0.497 | 0.735 | 101 |
| property: Gamma radiation resistant | mineral_property | 477 | 2 | 1.33e-08 | 0.557 | 8.91e-05 | 0.497 | 0.735 | 101 |
| ionic_strength_band | condition_scheme | 576 | 3 | 6.27e-07 | 0.553 | 0.0297 | 0.527 | 0.763 | 281 |
| property: Radiation resistant | mineral_property | 477 | 2 | 4.22e-07 | 0.557 | 0.00402 | 0.571 | 0.809 | 114 |
| property: Layered structure | mineral_property | 467 | 2 | 0.00897 | 0.546 | 0.0145 | 0.593 | 0.809 | 113 |
| property: Titanium-containing | mineral_property | 477 | 2 | 0.000763 | 0.556 | 0.0245 | 0.605 | 0.809 | 6 |
| property: Isometric crystals | mineral_property | 477 | 2 | 7.29e-07 | 0.557 | 0.00101 | 0.612 | 0.809 | 15 |
| property: Silicates | mineral_property | 477 | 2 | 0.02 | 0.544 | 5.15e-05 | 0.681 | 0.858 | 94 |
| property: Silica-rich minerals | mineral_property | 477 | 2 | 0.02 | 0.544 | 5.15e-05 | 0.681 | 0.858 | 94 |
| property: Oxides | mineral_property | 477 | 2 | 0.0106 | 0.55 | 1.22e-05 | 0.844 | 1 | 97 |
| property: Aluminum-containing | mineral_property | 477 | 2 | 1.27e-10 | 0.557 | 2.19e-05 | 0.882 | 1 | 121 |
| background_anion | condition_scheme | 576 | 4 | 0.0252 | 0.537 | 0.0183 | 0.934 | 1 | 33 |
| property: Potassium-containing | mineral_property | 411 | 2 | 0.0158 | 0.537 | 1.65e-06 | 0.943 | 1 | 12 |
| property: Radionuclide sorbents | mineral_property | 477 | 2 | 0.00309 | 0.556 | 0.00146 | 0.944 | 1 | 116 |
| cosolute | condition_scheme | 576 | 2 | 5.61e-07 | 0.553 | 2.58e-07 | 0.988 | 1 | 126 |
| property: Calcium-containing | mineral_property | 399 | 2 | 0.0929 | 0.492 | 0.00227 | 1 | 1 | 0 |
| property: Sodium-containing | mineral_property | 399 | 2 | 5.4e-08 | 0.544 | 5.99e-06 | 1 | 1 | 0 |
| property: Zeolite group | mineral_property | 477 | 2 | 5.06e-05 | 0.557 | 1.92e-05 | 1 | 1 | 3 |

### Width and height, schemes

| grouping | parameter | n_curves | group_share | reference_share | p_value | q_value |
|---|---|---|---|---|---|---|
| sorbate_charge_form | log_width | 569 | 0.206 | 0.288 | 0.0005 | 0.00566 |
| sorbate_charge_form | height | 569 | 0.734 | 0.175 | 0.0005 | 0.00566 |
| sorbate_element_group | height | 575 | 0.687 | 0.2 | 0.0005 | 0.00566 |
| carbonate | height | 576 | 0.215 | 0.668 | 0.0005 | 0.00566 |
| sorbate_element_group | log_width | 575 | 0.182 | 0.294 | 0.001 | 0.00971 |
| ionic_strength_band | log_width | 576 | 0.0195 | 0.469 | 0.0045 | 0.0378 |
| sorbate_hsab | height | 420 | 0.0771 | 0.585 | 0.018 | 0.102 |
| carbonate | log_width | 576 | 1.98e-07 | 0.476 | 0.047 | 0.164 |
| sorbate_redox | log_width | 533 | 0.0377 | 0.449 | 0.0835 | 0.218 |
| mineral_metal | height | 477 | 0.0191 | 0.813 | 0.098 | 0.247 |
| cosolute | log_width | 576 | 1.1e-06 | 0.476 | 0.276 | 0.536 |
| sorbate_redox | height | 533 | 0.0117 | 0.831 | 0.337 | 0.636 |
| mineral_structure | height | 477 | 0.0129 | 0.818 | 0.381 | 0.67 |
| background_anion | log_width | 576 | 0 | 0.476 | 0.477 | 0.735 |
| background_anion | height | 576 | 0.0544 | 0.785 | 0.619 | 0.809 |
| ionic_strength_band | height | 576 | 2.5e-09 | 0.839 | 0.782 | 0.967 |
| mineral_structure | log_width | 477 | 0.0166 | 0.469 | 0.798 | 0.969 |
| sorbate_hsab | log_width | 420 | 0.051 | 0.364 | 0.95 | 1 |
| mineral_metal | log_width | 477 | 0.00286 | 0.48 | 0.963 | 1 |
| cosolute | height | 576 | 0.0123 | 0.833 | 0.988 | 1 |

How to read this: `group_share` is the share of variance the grouping takes when study is also in the model; `between_group_R2` is the plain share between groups (what the permutation test uses); `curves_shufflable` counts curves in papers that contain more than one group (only those carry information in the within-paper test). Groupings tested here are correlated (e.g. iron-containing and oxyhydroxide pick out almost the same minerals), so several significant rows can be one effect.

Files: `exploratory_groupings.csv`, `exploratory_group_labels.csv` (label of every curve under every grouping), `exploratory_groupings.png`.

## Analyst notes (added after the run, 2026-10-13)

- **Bootstrap intervals for the pair component are biased upward.** Several 95% intervals do not contain their own point estimate (e.g. edge_pH mineral_sorbate 0.324 with interval 0.294-0.570; log_width mineral_sorbate 0.193 with 0.239-0.460). Cause: the cluster bootstrap relabels a reference drawn twice as two references, but its curves keep the same mineral-sorbate pair, so the pair looks better replicated than it is. Point shares come from the full data and are not affected; treat the intervals, especially for `mineral_sorbate`, as unreliable until a crossed-design bootstrap replaces this one.
- **The permutation test rests on few papers.** Only 31 of 141 references (217 of 576 curves) contain more than one class cell; the other papers cannot be shuffled. p = 0.0005 is the smallest value 2,000 permutations can give.
- **Mineral class adds little once sorbate and pair are known** (edge position share 2.7%); the "class" signal for edge position is mostly sorbate class (25.7%) and the specific pair (32.4%). Height is almost entirely sorbate class (75.5%: rising cation edges vs falling anion edges).
- **Shape beyond position/width/height (FPCA) shows no class structure**; for FPC2-FPC5 the bootstrap SD of a curve's score is close to the spread of scores across curves, so only FPC1 is resolved.
- Part C: some property splits are exact complements or duplicates (Redox active / inactive; Clay minerals / Sheet silicates; Silicates / Silica-rich), so they repeat one test. "Manganese-containing" (q = 0.038) rests on 25 shufflable curves.
- Run time was 11.7 h wall clock because the computer slept overnight; CPU time was about 40 min.
