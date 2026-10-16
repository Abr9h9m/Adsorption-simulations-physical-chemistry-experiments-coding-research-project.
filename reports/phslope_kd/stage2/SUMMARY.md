# Stage 2 summary: do mineral and sorbate classes matter?

> **EXPLORATORY.** Stage 1 did not meet its pre-set survival rule (46.8% of census-set curves survived QC; 80% required). Samuel chose on 2026-10-12 to continue with the core library. The classes in Part B are the PROPOSED assignment in classes.yaml, **not yet confirmed** by Samuel and Dr. Black. Nothing here is a confirmatory result.

Run: commit `d468a46`, config `7683c4e695c4`, data `library: C:\Users\itzju\Mineral Fingerprinting\reports\phslope_kd\stage1\library`, 2026-10-16T11:56:51Z.

## Part A: registration and shape components (task 2.2)

- Single-edge (rising/falling) core curves registered: 286 of 683 core curves. Registered slope source: {'spline': 286}.
- Slope variance removed by registration alone (aligning edge position, width and height): 87.2% overall; rising 81.1%; falling 74.2%.
- FPCA: 5 component(s) kept (rule: >= 90% of variance, max 5). Explained: FPC1 42.1%, FPC2 23.9%, FPC3 14.8%, FPC4 6.9%, FPC5 6.0%. 27.3% of the cells were filled by iterative SVD imputation, so these shares are somewhat optimistic.
- Score uncertainty (median bootstrap SD of projected scores vs the spread of scores across curves): FPC1 0.0908 vs spread 0.215, FPC2 0.0928 vs spread 0.162, FPC3 0.0832 vs spread 0.127, FPC4 0.056 vs spread 0.0867, FPC5 0.061 vs spread 0.0808.

Files: `registration_and_scores.csv` (warp a, b, w per curve, ratios to the median curve, FPC scores and SDs), `fpca_components.csv`, `registration_and_fpca.png`.

## Part B: class tests (tasks 2.3-2.5)

### Go/no-go: **PASS**

classes explain more than chance and more than study-to-study variation. For edge position: class share (mineral class + sorbate class + pair) = 52.8%, reference (study) share = 24.5%; within-reference permutation p = 0.0010 (2000 permutations).

Permutation informativeness: 19 of 128 references (115 of 434 curves) contain more than one class cell and can be shuffled; the rest are fixed under the null, which makes the test conservative.

Unassigned names (excluded): {'minerals': [], 'sorbates': []}

### Variance shares (95% parametric-bootstrap intervals: simulate from the fitted model, refit)

| parameter | component | share | share_lo | share_hi |
|---|---|---|---|---|
| edge_pH | mineral_class | 0.0294 | 3.36e-07 | 0.17 |
| edge_pH | sorbate_class | 0.134 | 1.67e-06 | 0.315 |
| edge_pH | mineral_sorbate | 0.364 | 0.239 | 0.505 |
| edge_pH | reference | 0.245 | 0.146 | 0.388 |
| edge_pH | residual | 0.227 | 0.162 | 0.321 |
| log_width | mineral_class | 2.45e-06 | 1.26e-08 | 0.0848 |
| log_width | sorbate_class | 0.111 | 6.6e-08 | 0.277 |
| log_width | mineral_sorbate | 0.206 | 0.0925 | 0.325 |
| log_width | reference | 0.312 | 0.196 | 0.455 |
| log_width | residual | 0.371 | 0.283 | 0.499 |
| height | mineral_class | 4.12e-07 | 8.3e-10 | 0.0324 |
| height | sorbate_class | 0.786 | 0.31 | 0.9 |
| height | mineral_sorbate | 0.0491 | 0.0187 | 0.16 |
| height | reference | 0.0792 | 0.0355 | 0.261 |
| height | residual | 0.0863 | 0.0404 | 0.243 |
| fpc1 | mineral_class | 2.23e-08 | 4.68e-10 | 0.0979 |
| fpc1 | sorbate_class | 0.00607 | 1.27e-10 | 0.137 |
| fpc1 | mineral_sorbate | 0.74 | 0.577 | 0.809 |
| fpc1 | reference | 0.0291 | 1.49e-09 | 0.0932 |
| fpc1 | residual | 0.225 | 0.161 | 0.299 |
| fpc2 | mineral_class | 7.43e-09 | 9.65e-11 | 0.056 |
| fpc2 | sorbate_class | 0.0113 | 1.47e-09 | 0.0949 |
| fpc2 | mineral_sorbate | 3.94e-07 | 0 | 0.0837 |
| fpc2 | reference | 0.0628 | 0 | 0.166 |
| fpc2 | residual | 0.926 | 0.777 | 0.995 |
| fpc3 | mineral_class | 0.00854 | 9.74e-09 | 0.122 |
| fpc3 | sorbate_class | 8.17e-08 | 1.88e-09 | 0.0678 |
| fpc3 | mineral_sorbate | 0.177 | 0.0131 | 0.296 |
| fpc3 | reference | 0.0555 | 1.36e-08 | 0.175 |
| fpc3 | residual | 0.759 | 0.605 | 0.914 |
| fpc4 | mineral_class | 1.84e-07 | 0 | 0.0697 |
| fpc4 | sorbate_class | 0.0137 | 8.71e-09 | 0.113 |
| fpc4 | mineral_sorbate | 0.228 | 0.0536 | 0.341 |
| fpc4 | reference | 0.0115 | 0 | 0.119 |
| fpc4 | residual | 0.747 | 0.576 | 0.881 |
| fpc5 | mineral_class | 2.28e-07 | 0 | 0.069 |
| fpc5 | sorbate_class | 8.13e-07 | 0 | 0.0791 |
| fpc5 | mineral_sorbate | 0.221 | 0.0458 | 0.325 |
| fpc5 | reference | 3.08e-07 | 0 | 0.0947 |
| fpc5 | residual | 0.779 | 0.607 | 0.9 |

### Edge position with conditions as fixed effects (n = 434, 0 curves dropped for a missing covariate; temperature not included (reported for < 80% of curves); constant covariates dropped: none)

| component | share |
|---|---|
| mineral_class | 0.0964 |
| sorbate_class | 0.137 |
| mineral_sorbate | 0.328 |
| reference | 0.237 |
| residual | 0.202 |

### Clustering vs class labels (within-reference permutations)

| features | labels | n | ARI | ARI_p | ARI_null_mean | PERMANOVA_F | PERMANOVA_R2 | PERMANOVA_p |
|---|---|---|---|---|---|---|---|---|
| edge parameters | mineral_class | 434 | -0.0191 | 0.105 | -0.0201 | 5.48 | 0.0486 | 0.357 |
| edge parameters | sorbate_class | 434 | 0.184 | 0.013 | 0.178 | 38.9 | 0.312 | 0.001 |
| FPCA scores | mineral_class | 286 | 0.0215 | 0.004 | 0.0073 | 0.849 | 0.0119 | 0.023 |
| FPCA scores | sorbate_class | 286 | -0.0264 | 0.598 | -0.0259 | 2.07 | 0.0357 | 0.297 |

Figures: `variance_shares.png`, `edge_grid.png`.

### Next decision

Stage 2 passes: continue to Stage 3 (descriptor tables, then freeze thresholds.yaml). (Exploratory: the verdict uses unconfirmed classes and a library that failed Stage 1.)

## Part C: exploratory groupings (config/schemes.yaml)

48 groupings tested on 434 core edge curves: one T-vs-F split per usable column of the mineral property table, two mineral schemes built from it, four sorbate schemes and four ionic-condition schemes. Each was tested for edge position (all) and log width and height (schemes only): variance share in a model with study as a second random effect, and a within-reference permutation test of the between-group share. 72 tests in total; q = Benjamini-Hochberg adjusted p over the exploratory groupings. Significant after FDR: 3. The two pre-specified classes from classes.yaml are included as reference rows (kind `prespecified_class`), tested the same way, with their raw p and no q: they are not part of the exploratory screen.

Mineral property table: `mineral properties.csv`; cell codes {'F': 1407, 'T': 532, 'TO': 46, 'O': 24, 'FO': 7} (only T and F used; TO/O/FO treated as missing). Rows left out pending correction: Calcite, Maghemite, Corundum. Minerals in the library with no row: hematite. The table has no source column, so these are uncited properties.

### Edge position, all groupings (sorted by q)

| grouping | kind | n_curves | n_groups | group_share | reference_share | between_group_R2 | p_value | q_value | curves_shufflable |
|---|---|---|---|---|---|---|---|---|---|
| sorbate_charge_form | sorbate_scheme | 426 | 7 | 0.107 | 0.511 | 0.0565 | 0.0005 | 0.0165 | 58 |
| sorbate_redox | sorbate_scheme | 401 | 2 | 0.0674 | 0.537 | 0.0285 | 0.0015 | 0.033 | 34 |
| carbonate | condition_scheme | 434 | 2 | 0.0516 | 0.521 | 0.00216 | 0.0105 | 0.173 | 30 |
| sorbate_element_group | sorbate_scheme | 433 | 8 | 0.112 | 0.487 | 0.0611 | 0.019 | 0.187 | 46 |
| property: Framework structure | mineral_property | 374 | 2 | 0.0988 | 0.484 | 0.00577 | 0.024 | 0.187 | 54 |
| property: Framework silicates (tectosilicates) | mineral_property | 374 | 2 | 0.0988 | 0.484 | 0.00577 | 0.024 | 0.187 | 54 |
| property: Hydrous minerals | mineral_property | 372 | 2 | 0.0494 | 0.487 | 0.0162 | 0.034 | 0.187 | 62 |
| property: Anhydrous minerals | mineral_property | 372 | 2 | 0.0494 | 0.487 | 0.0162 | 0.034 | 0.187 | 62 |
| property: Thermally stable | mineral_property | 374 | 2 | 0.0415 | 0.507 | 0.0183 | 0.0775 | 0.32 | 64 |
| property: Orthorhombic crystals | mineral_property | 374 | 2 | 2.32e-09 | 0.536 | 0.0058 | 0.096 | 0.333 | 45 |
| ionic_strength_band | condition_scheme | 434 | 3 | 0.00942 | 0.531 | 0.0494 | 0.156 | 0.49 | 209 |
| mineral_metal | mineral_scheme | 374 | 5 | 0.107 | 0.459 | 0.0574 | 0.205 | 0.589 | 70 |
| property: Dioxides (MO2) | mineral_property | 370 | 2 | 0.0359 | 0.495 | 0.0154 | 0.226 | 0.602 | 59 |
| property: Mixed metal oxides | mineral_property | 372 | 2 | 0.0132 | 0.526 | 0.0352 | 0.24 | 0.602 | 88 |
| property: Polymorphs | mineral_property | 374 | 2 | 0.000944 | 0.535 | 0.0111 | 0.242 | 0.602 | 116 |
| property: Isometric crystals | mineral_property | 374 | 2 | 2.59e-06 | 0.536 | 0.00538 | 0.246 | 0.602 | 14 |
| property: Amorphous (non-crystalline) | mineral_property | 369 | 2 | 0.0322 | 0.512 | 0.0549 | 0.262 | 0.606 | 71 |
| property: Hydroxides | mineral_property | 296 | 2 | 0.043 | 0.476 | 0.0327 | 0.275 | 0.606 | 66 |
| mineral_structure | mineral_scheme | 374 | 6 | 0.0279 | 0.509 | 0.0335 | 0.297 | 0.633 | 76 |
| property: Monoclinic crystals | mineral_property | 374 | 2 | 0.00945 | 0.529 | 0.0112 | 0.331 | 0.683 | 34 |
| property: Manganese-containing | mineral_property | 374 | 2 | 0.529 | 0.246 | 0.03 | 0.345 | 0.688 | 3 |
| property: Magnesium-containing | mineral_property | 357 | 2 | 8.6e-06 | 0.53 | 0.00358 | 0.355 | 0.688 | 27 |
| property: Iron-containing | mineral_property | 298 | 2 | 0.0285 | 0.504 | 0.016 | 0.454 | 0.773 | 60 |
| sorbate_hsab | sorbate_scheme | 325 | 3 | 1.55e-06 | 0.551 | 0.0156 | 0.457 | 0.773 | 38 |
| property: Redox active | mineral_property | 374 | 2 | 0.0116 | 0.523 | 0.0102 | 0.556 | 0.895 | 68 |
| property: Redox inactive | mineral_property | 374 | 2 | 0.0116 | 0.523 | 0.0102 | 0.556 | 0.895 | 68 |
| property: Radiation resistant | mineral_property | 374 | 2 | 0.0109 | 0.522 | 0.0144 | 0.575 | 0.904 | 81 |
| background_anion | condition_scheme | 434 | 4 | 0.0215 | 0.525 | 0.0101 | 0.628 | 0.942 | 14 |
| property: Oxyhydroxides | mineral_property | 370 | 2 | 0.0146 | 0.499 | 0.0156 | 0.647 | 0.948 | 64 |
| property: Silicates | mineral_property | 374 | 2 | 6.54e-07 | 0.536 | 0.000408 | 0.744 | 0.957 | 64 |
| property: Silica-rich minerals | mineral_property | 374 | 2 | 6.54e-07 | 0.536 | 0.000408 | 0.744 | 0.957 | 64 |
| cosolute | condition_scheme | 434 | 2 | 8.3e-07 | 0.543 | 0.00652 | 0.747 | 0.957 | 81 |
| property: Aluminum-containing | mineral_property | 374 | 2 | 0 | 0.536 | 0.00151 | 0.768 | 0.957 | 60 |
| property: Oxides | mineral_property | 374 | 2 | 5.13e-08 | 0.536 | 0.000624 | 0.773 | 0.957 | 61 |
| property: Ion exchangers | mineral_property | 374 | 2 | 0 | 0.536 | 0.00307 | 0.779 | 0.957 | 46 |
| property: Hexagonal crystals | mineral_property | 374 | 2 | 1.32e-08 | 0.536 | 5.06e-05 | 0.802 | 0.957 | 59 |
| property: Aluminosilicates | mineral_property | 374 | 2 | 2.1e-06 | 0.536 | 0.000326 | 0.864 | 0.957 | 43 |
| property: Radionuclide sorbents | mineral_property | 374 | 2 | 2.08e-06 | 0.536 | 8.01e-05 | 0.865 | 0.957 | 79 |
| property: Clay minerals | mineral_property | 374 | 2 | 2.73e-07 | 0.536 | 0.000144 | 0.87 | 0.957 | 43 |
| property: Sheet silicates (phyllosilicates) | mineral_property | 374 | 2 | 2.73e-07 | 0.536 | 0.000144 | 0.87 | 0.957 | 43 |
| property: Alpha particle resistant | mineral_property | 374 | 2 | 1.87e-08 | 0.536 | 0.000349 | 0.87 | 0.957 | 49 |
| property: Gamma radiation resistant | mineral_property | 374 | 2 | 1.87e-08 | 0.536 | 0.000349 | 0.87 | 0.957 | 49 |
| property: Layered structure | mineral_property | 369 | 2 | 6.24e-07 | 0.539 | 0.00331 | 0.897 | 0.97 | 46 |
| property: Calcium-containing | mineral_property | 298 | 2 | 9.09e-06 | 0.536 | 0.00166 | 1 | 1 | 0 |
| property: Potassium-containing | mineral_property | 313 | 2 | 1.71e-06 | 0.54 | 0.00489 | 1 | 1 | 2 |
| property: Titanium-containing | mineral_property | 374 | 2 | 0.222 | 0.412 | 0.0226 | 1 | 1 | 0 |
| sorbate_class (classes.yaml) | prespecified_class | 434 | 6 | 0.192 | 0.439 | 0.0626 | 0.0005 |  | 45 |
| mineral_class (classes.yaml) | prespecified_class | 434 | 5 | 0.0783 | 0.485 | 0.0598 | 0.264 |  | 70 |

### Width and height, schemes

| grouping | parameter | n_curves | group_share | reference_share | p_value | q_value |
|---|---|---|---|---|---|---|
| carbonate | height | 434 | 0.282 | 0.624 | 0.0005 | 0.0165 |
| ionic_strength_band | log_width | 434 | 0.0335 | 0.536 | 0.02 | 0.187 |
| mineral_metal | height | 374 | 0.0466 | 0.797 | 0.028 | 0.187 |
| mineral_structure | height | 374 | 0.023 | 0.821 | 0.033 | 0.187 |
| carbonate | log_width | 434 | 1.32e-07 | 0.554 | 0.0505 | 0.256 |
| sorbate_element_group | log_width | 433 | 0.203 | 0.387 | 0.072 | 0.32 |
| sorbate_hsab | height | 325 | 0.0669 | 0.559 | 0.0735 | 0.32 |
| sorbate_charge_form | height | 426 | 0.709 | 0.167 | 0.0835 | 0.324 |
| sorbate_redox | height | 401 | 0.132 | 0.714 | 0.093 | 0.333 |
| background_anion | height | 434 | 0.0952 | 0.756 | 0.124 | 0.409 |
| sorbate_charge_form | log_width | 426 | 0.152 | 0.421 | 0.178 | 0.535 |
| sorbate_hsab | log_width | 325 | 0.147 | 0.376 | 0.269 | 0.606 |
| cosolute | log_width | 434 | 7.64e-08 | 0.554 | 0.365 | 0.688 |
| sorbate_element_group | height | 433 | 0.783 | 0.127 | 0.428 | 0.773 |
| mineral_metal | log_width | 374 | 0.0606 | 0.521 | 0.446 | 0.773 |
| mineral_structure | log_width | 374 | 0.065 | 0.515 | 0.617 | 0.942 |
| background_anion | log_width | 434 | 4.37e-08 | 0.554 | 0.709 | 0.957 |
| sorbate_redox | log_width | 401 | 6.49e-07 | 0.545 | 0.834 | 0.957 |
| ionic_strength_band | height | 434 | 0.00168 | 0.847 | 0.978 | 1 |
| cosolute | height | 434 | 0.0211 | 0.835 | 0.998 | 1 |
| sorbate_class (classes.yaml) | height | 434 | 0.776 | 0.13 | 0.0505 |  |
| sorbate_class (classes.yaml) | log_width | 434 | 0.163 | 0.416 | 0.134 |  |
| mineral_class (classes.yaml) | height | 434 | 0.0198 | 0.826 | 0.18 |  |
| mineral_class (classes.yaml) | log_width | 434 | 0.0308 | 0.542 | 0.917 |  |

How to read this: `group_share` is the share of variance the grouping takes when study is also in the model; `between_group_R2` is the plain share between groups (what the permutation test uses); `curves_shufflable` counts curves in papers that contain more than one group (only those carry information in the within-paper test). Groupings tested here are correlated (e.g. iron-containing and oxyhydroxide pick out almost the same minerals), so several significant rows can be one effect.

Files: `exploratory_groupings.csv`, `exploratory_group_labels.csv` (label of every curve under every grouping), `exploratory_groupings.png`.
