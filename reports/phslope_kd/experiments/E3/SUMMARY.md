# E3 Duplicate and validity audit

**Plain English.** We looked for the same experiment appearing twice in the dataset (for example a figure re-used in a later paper), because copies make different papers look like they agree. We found 22 curve pairs that are near-copies across different papers and 45 within the same paper. Papers linked by copies are now treated as one source when testing predictions (8 such groups covering 16 papers). We also flagged curves that break simple validity rules; nothing was deleted.

> EXPLORATORY. Development papers only (locked set hash `88b1c3a1b769`). Commit `d468a46`.

## Duplicates

Rule: points match within 0.02 pH and 0.01 fraction sorbed; a pair is flagged when at least 80% of the shorter curve's points match. Flagged pairs: 67 (22 across papers). Table: `duplicate_pairs.csv`.

| curve_a | curve_b | mineral | sorbate | reference_a | reference_b | match_share | cross_paper |
|---|---|---|---|---|---|---|---|
| zb04_fa22 | zrhsk05_f10 | calcite | Np(+5) | zb04 | zrhsk05 | 1 | True |
| zb04_fb4 | zrhsk05_f11b | calcite | Pu(+5) | zb04 | zrhsk05 | 1 | True |
| awj06a_f2b | afi02_f1c | goethite | Mellitic acid | awj06a | afi02 | 0.914 | True |
| mf92_f1a | mf92a_f1c | goethite | Oxalic acid | mf92 | mf92a | 0.882 | True |
| mf92_f1a | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.875 | True |
| mf92_f2ab | mf92a_f1c | goethite | Oxalic acid | mf92 | mf92a | 0.944 | True |
| mf92_f2ab | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.875 | True |
| mf92_f2ac | mf92a_f2a | goethite | Oxalic acid | mf92 | mf92a | 0.889 | True |
| mf92_f2ad | mf92a_f2b | goethite | Oxalic acid | mf92 | mf92a | 0.923 | True |
| mf92_f2ad | mf92a_f3a | goethite | Oxalic acid | mf92 | mf92a | 0.923 | True |
| mf92_f2ad | mf92a_f3b | goethite | Oxalic acid | mf92 | mf92a | 0.923 | True |
| mf92_f2bb | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.875 | True |
| mf92_f2ca | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.938 | True |
| hpl88_f2aa | hrbhl87_f2a | goethite | Se(+4) | hpl88 | hrbhl87 | 0.857 | True |
| pbb99_f7a | pbb99a_f23apsi | illite | Cs(+1) | pbb99 | pbb99a | 0.828 | True |
| pbb99_f7a | pbb99a_f23aapsi | illite | Cs(+1) | pbb99 | pbb99a | 1 | True |
| pbb99_f7c | pbb99a_f23bpsi | illite | Cs(+1) | pbb99 | pbb99a | 1 | True |
| bb06_f1aapsi | BB06_f1a | montmorillonite | Am(+3) | bb06 | BB06 | 0.862 | True |
| azbn00_f1 | azbn98_f2c | quartz | U(+6) | azbn00 | azbn98 | 0.917 | True |
| d01_f5-6e | kckd96_f2a | quartz | U(+6) | d01 | kckd96 | 0.867 | True |
| d01_f5-6f | kckd96_f2b | quartz | U(+6) | d01 | kckd96 | 1 | True |
| d01_f5-8g | kckd96_f2a | quartz | U(+6) | d01 | kckd96 | 0.933 | True |

## Lineage clusters

196 clusters from 204 papers; 16 papers sit in 8 multi-paper clusters. Table: `lineage_clusters.csv`.

## Agreement benchmark: leaving out papers vs leaving out lineage clusters

Core single-edge development curves in groups with >= 2 units (edge = logistic p50). If duplicates inflated cross-paper agreement, errors rise when copies can no longer be used to predict each other.

| leave_out_unit | model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reference | B0_all_other | 155 | 61 | 0.481 |  |  | 0.153 | 0.941 | 0.869 | 0.523 | 0.768 |  | 0.499 | 0.501 |
| reference | B1_nearest1 | 155 | 61 | 0.339 |  |  | 0.119 | 0.897 | 0.835 | 0.6 | 0.774 |  | 0.464 | 0.531 |
| reference | B2_nearest3 | 155 | 61 | 0.471 |  |  | 0.18 | 0.72 | 0.78 | 0.581 | 0.845 |  | 0.48 | 0.542 |
| reference | B3_matched_fb | 155 | 61 | 0.463 |  |  | 0.19 | 0.854 | 0.851 | 0.548 | 0.787 |  | 0.481 | 0.513 |
| lineage_cluster | B0_all_other | 153 | 58 | 0.52 |  |  | 0.226 | 0.893 | 0.895 | 0.497 | 0.778 |  | 0.526 | 0.489 |
| lineage_cluster | B1_nearest1 | 153 | 58 | 0.555 |  |  | 0.217 | 1.04 | 0.904 | 0.477 | 0.725 |  | 0.555 | 0.488 |
| lineage_cluster | B2_nearest3 | 153 | 58 | 0.499 |  |  | 0.226 | 0.826 | 0.865 | 0.51 | 0.804 |  | 0.493 | 0.518 |
| lineage_cluster | B3_matched_fb | 153 | 58 | 0.481 |  |  | 0.217 | 0.849 | 0.876 | 0.516 | 0.791 |  | 0.499 | 0.502 |

## Validity flags (counts of curves; nothing dropped)

| index | curves_flagged |
|---|---|
| f_out_of_range | 1 |
| response_maybe_percent | 0 |
| pH_out_of_range | 3 |
| solids_nonpositive_or_implausible | 1 |
| total_sorbate_nonpositive | 0 |
| ionic_strength_not_finite | 0 |
| slope_sign_contradicts_shape | 2 |
| fewer_than_3_pH_values | 0 |

Per-curve flags: `data_flags.csv` (column `data_flag`).

## Outlier review

Pages and the review table are added after E1 (they need the E1 residuals): `outlier_pages.pdf`, `outlier_review.csv` with empty `reviewer`, `verdict`, `notes` columns for Samuel or Abraham. Sensitivity runs excluding verdict = data error wait for those verdicts.
