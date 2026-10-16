# E4 Lab (research-group) effect

**Plain English.** Papers from the same research group often reuse the same recipe, so their curves may agree for reasons that do not carry over to other labs. We asked whether the benefit of matching experimental conditions survives when the matched paper must come from a different group. Result (exact-initials grouping): **GAIN DOES NOT SURVIVE (partly a lab effect, or not significant)**.

> EXPLORATORY. The file has no author fields, so labs are a proxy built from the reference code (letters = author initials). 177 exact-initial groups, 139 first-two-letter groups. The exact proxy under-counts same-lab pairs (a lab with changing co-authors is split); the coarse proxy over-counts (unrelated authors with the same initials are merged). Development papers only; leave-out unit = lineage cluster. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## 2. Matched-gain survival (core single-edge curves, logistic edge)

| lab_id | matching | model | n | median | median_lo | median_hi | within_0_5 |
|---|---|---|---|---|---|---|---|
| lab_exact | any lab | B0_all_other | 153 | 0.52 | 0.42 | 0.631 | 0.497 |
| lab_exact | any lab | B1_nearest1 | 153 | 0.555 | 0.324 | 0.693 | 0.477 |
| lab_exact | any lab | B2_nearest3 | 153 | 0.499 | 0.372 | 0.574 | 0.51 |
| lab_exact | any lab | B3_matched_fb | 153 | 0.481 | 0.355 | 0.626 | 0.516 |
| lab_exact | different lab (lab_exact) | B0_all_other | 148 | 0.528 | 0.421 | 0.711 | 0.486 |
| lab_exact | different lab (lab_exact) | B1_nearest1 | 148 | 0.583 | 0.363 | 0.694 | 0.459 |
| lab_exact | different lab (lab_exact) | B2_nearest3 | 148 | 0.502 | 0.364 | 0.602 | 0.5 |
| lab_exact | different lab (lab_exact) | B3_matched_fb | 148 | 0.496 | 0.339 | 0.679 | 0.507 |
| lab_coarse | any lab | B0_all_other | 153 | 0.52 | 0.42 | 0.631 | 0.497 |
| lab_coarse | any lab | B1_nearest1 | 153 | 0.555 | 0.324 | 0.693 | 0.477 |
| lab_coarse | any lab | B2_nearest3 | 153 | 0.499 | 0.372 | 0.574 | 0.51 |
| lab_coarse | any lab | B3_matched_fb | 153 | 0.481 | 0.355 | 0.626 | 0.516 |
| lab_coarse | different lab (lab_coarse) | B0_all_other | 146 | 0.561 | 0.427 | 0.748 | 0.466 |
| lab_coarse | different lab (lab_coarse) | B1_nearest1 | 146 | 0.61 | 0.415 | 0.762 | 0.425 |
| lab_coarse | different lab (lab_coarse) | B2_nearest3 | 146 | 0.515 | 0.41 | 0.61 | 0.479 |
| lab_coarse | different lab (lab_coarse) | B3_matched_fb | 146 | 0.566 | 0.425 | 0.742 | 0.459 |

Paired B3 minus B0 (negative = matching helps):

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | matching | lab_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3_matched_fb | B0_all_other | 153 | -0.0393 | -0.125 | 0.0408 | 0 | 0 | 0 | 0.481 | 0.52 | 0.15 | 0.745 | any lab | lab_exact |
| B3_matched_fb | B0_all_other | 148 | -0.0322 | -0.132 | 0.0369 | 0 | 0 | 0 | 0.496 | 0.528 | 0.155 | 0.736 | different lab (lab_exact) | lab_exact |
| B3_matched_fb | B0_all_other | 153 | -0.0393 | -0.125 | 0.0408 | 0 | 0 | 0 | 0.481 | 0.52 | 0.15 | 0.745 | any lab | lab_coarse |
| B3_matched_fb | B0_all_other | 146 | 0.00572 | -0.051 | 0.0772 | 0 | 0 | 0 | 0.566 | 0.561 | 0.13 | 0.76 | different lab (lab_coarse) | lab_coarse |

Decision (exact proxy): paired 95% interval below zero: NO; B3 median 0.496 <= 0.5: yes -> **GAIN DOES NOT SURVIVE (partly a lab effect, or not significant)**.

## 1. Lab random effect in the E1 level model (variance shares)

| model | share_class_dir | share_pair_dir | share_unit | share_residual | share_lab | lab_id |
|---|---|---|---|---|---|---|
| without lab | 0.00837 | 0.0327 | 0.364 | 0.595 |  | lab_exact |
| with lab | 0.00581 | 0.0332 | 4.27e-09 | 0.56 | 0.401 | lab_exact |
| without lab | 0.00837 | 0.0327 | 0.364 | 0.595 |  | lab_coarse |
| with lab | 0.00835 | 0.0327 | 0.364 | 0.595 | 1.69e-06 | lab_coarse |

## 3. Same-lab vs different-lab cross-paper pairs (edge difference after solids adjustment)

| lab_id | same_lab_pairs | different_lab_pairs | median_same | median_different | mannwhitney_p |
|---|---|---|---|---|---|
| lab_exact | 4 | 356 | 0.296 | 0.71 |  |
| lab_coarse | 13 | 347 | 0.277 | 0.713 | 0.281 |

