# Stage 3 summary: can we predict a held-out system's slope curve?

> **EXPLORATORY.** Stage 1 failed its survival rule; classes are the unconfirmed proposal; thresholds.yaml is not frozen (frozen: false). Feature sets other than `descriptors` use the uncited mineral property table and Claude's proposed sorbate schemes. Nothing here is a confirmatory result.

Run: commit `20ada89`, config `83dd23d2ed5f`, data `library: C:\Users\itzju\Mineral Fingerprinting\reports\phslope\stage1\library`, 2026-10-13T13:00:01Z.

Data: 405 single-edge (rising/falling) core curves, 120 papers, 115 mineral-sorbate pairs.

Feature sets used: `properties` (65 features, 232 curves with every feature), `conditions` (4 features, 397 curves with every feature).
Not used: `descriptors`: descriptor tables are empty or too sparse ({'n_features': 4, 'n_curves': 405, 'n_complete': 397}).

Without the descriptor tables the edge-position rule baseline (edge from PZC and first hydrolysis constant), the one the spec says decides whether the project says anything new, cannot run.

## Verdict per model and level (thresholds.yaml stage3)

Pass = median edge error <= 0.5 pH, slope-interval coverage in [0.8, 0.95], and better than every baseline (95% interval of the paired difference below zero, for edge error and curve error).

| level | model | median_p50_error | p50_ok | interval_coverage | coverage_ok | beats_every_baseline | verdict |
|---|---|---|---|---|---|---|---|
| mineral | version_a@conditions | 1.19 | False | 0.87 | True | False | FAIL |
| mineral | version_a@properties | 1.19 | False | 0.864 | True | False | FAIL |
| mineral | version_b@conditions | 1.19 | False | 0.871 | True | False | FAIL |
| mineral | version_b@properties | 1.19 | False | 0.87 | True | False | FAIL |
| pair | version_a@conditions | 1.21 | False | 0.882 | True | False | FAIL |
| pair | version_a@properties | 1.37 | False | 0.865 | True | False | FAIL |
| pair | version_b@conditions | 1.21 | False | 0.883 | True | False | FAIL |
| pair | version_b@properties | 1.37 | False | 0.866 | True | False | FAIL |
| sorbate | version_a@conditions | 1.32 | False | 0.859 | True | False | FAIL |
| sorbate | version_a@properties | 1.8 | False | 0.839 | True | False | FAIL |
| sorbate | version_b@conditions | 1.32 | False | 0.858 | True | False | FAIL |
| sorbate | version_b@properties | 1.8 | False | 0.842 | True | False | FAIL |
| study | version_a@conditions | 1.25 | False | 0.878 | True | False | FAIL |
| study | version_a@properties | 1.13 | False | 0.884 | True | False | FAIL |
| study | version_b@conditions | 1.25 | False | 0.879 | True | False | FAIL |
| study | version_b@properties | 1.13 | False | 0.886 | True | False | FAIL |

## Metrics by model

| level | model | n_curves | n_groups | median_p50_error | p50_error_q25 | p50_error_q75 | median_curve_error | median_curve_error_unweighted | shape_correct | sign_correct | interval_coverage | p50_coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mineral | global_mean | 405 | 31 | 1.2 | 0.6 | 2.21 | 0.0797 | 0.432 | 0.659 | 0.565 | 0.872 | 0.896 |
| mineral | mineral_class_mean | 405 | 31 | 1.16 | 0.456 | 2.27 | 0.0765 | 0.45 | 0.536 | 0.449 | 0.876 | 0.889 |
| mineral | sorbate_class_mean | 405 | 31 | 1.16 | 0.674 | 1.99 | 0.109 | 0.43 | 0.985 | 0.842 | 0.874 | 0.911 |
| mineral | version_a@conditions | 397 | 29 | 1.19 | 0.618 | 2.21 | 0.0696 | 0.454 | 0.688 | 0.564 | 0.87 | 0.897 |
| mineral | version_a@properties | 232 | 17 | 1.19 | 0.582 | 2.06 | 0.131 | 0.446 | 0.991 | 0.828 | 0.864 | 0.901 |
| mineral | version_b@conditions | 397 | 29 | 1.19 | 0.618 | 2.21 | 0.0773 | 0.454 | 0.688 | 0.574 | 0.871 | 0.897 |
| mineral | version_b@properties | 232 | 17 | 1.19 | 0.582 | 2.06 | 0.135 | 0.448 | 0.991 | 0.81 | 0.87 | 0.901 |
| pair | global_mean | 405 | 115 | 1.22 | 0.571 | 2.24 | 0.0748 | 0.437 | 0.659 | 0.57 | 0.879 | 0.894 |
| pair | mineral_class_mean | 405 | 115 | 1.18 | 0.418 | 2.28 | 0.0639 | 0.451 | 0.659 | 0.558 | 0.88 | 0.896 |
| pair | sorbate_class_mean | 405 | 115 | 1.2 | 0.684 | 2.09 | 0.112 | 0.425 | 0.985 | 0.837 | 0.88 | 0.886 |
| pair | version_a@conditions | 397 | 113 | 1.21 | 0.58 | 2.25 | 0.0664 | 0.443 | 0.748 | 0.632 | 0.882 | 0.894 |
| pair | version_a@properties | 232 | 62 | 1.37 | 0.703 | 2.46 | 0.162 | 0.45 | 0.991 | 0.763 | 0.865 | 0.793 |
| pair | version_b@conditions | 397 | 113 | 1.21 | 0.58 | 2.25 | 0.0703 | 0.445 | 0.748 | 0.642 | 0.883 | 0.894 |
| pair | version_b@properties | 232 | 62 | 1.37 | 0.703 | 2.46 | 0.165 | 0.451 | 0.991 | 0.789 | 0.866 | 0.793 |
| sorbate | global_mean | 405 | 35 | 1.33 | 0.598 | 2.35 | 0.0749 | 0.444 | 0.659 | 0.541 | 0.86 | 0.881 |
| sorbate | mineral_class_mean | 405 | 35 | 1.29 | 0.438 | 2.39 | 0.0751 | 0.455 | 0.659 | 0.543 | 0.863 | 0.874 |
| sorbate | sorbate_class_mean | 405 | 35 | 1.41 | 0.819 | 2.56 | 0.15 | 0.455 | 0.975 | 0.738 | 0.844 | 0.785 |
| sorbate | version_a@conditions | 397 | 35 | 1.32 | 0.632 | 2.46 | 0.0787 | 0.457 | 0.635 | 0.489 | 0.859 | 0.846 |
| sorbate | version_a@properties | 232 | 25 | 1.8 | 0.715 | 3.16 | 0.192 | 0.442 | 0.991 | 0.694 | 0.839 | 0.659 |
| sorbate | version_b@conditions | 397 | 35 | 1.32 | 0.632 | 2.46 | 0.0752 | 0.46 | 0.635 | 0.526 | 0.858 | 0.846 |
| sorbate | version_b@properties | 232 | 25 | 1.8 | 0.715 | 3.16 | 0.194 | 0.444 | 0.991 | 0.707 | 0.842 | 0.659 |
| study | global_mean | 405 | 120 | 1.21 | 0.545 | 2.16 | 0.0748 | 0.432 | 0.659 | 0.57 | 0.881 | 0.901 |
| study | mineral_class_mean | 405 | 120 | 1.15 | 0.394 | 2.21 | 0.0657 | 0.444 | 0.659 | 0.565 | 0.884 | 0.899 |
| study | sorbate_class_mean | 405 | 120 | 1.15 | 0.647 | 2.08 | 0.109 | 0.415 | 0.975 | 0.837 | 0.881 | 0.894 |
| study | version_a@conditions | 397 | 117 | 1.25 | 0.616 | 2.22 | 0.0704 | 0.454 | 0.748 | 0.627 | 0.878 | 0.889 |
| study | version_a@properties | 232 | 71 | 1.13 | 0.478 | 2.08 | 0.124 | 0.43 | 0.974 | 0.866 | 0.884 | 0.879 |
| study | version_b@conditions | 397 | 117 | 1.25 | 0.616 | 2.22 | 0.0723 | 0.456 | 0.748 | 0.627 | 0.879 | 0.889 |
| study | version_b@properties | 232 | 71 | 1.13 | 0.478 | 2.08 | 0.111 | 0.429 | 0.974 | 0.871 | 0.886 | 0.879 |

Note on curve error: the spec weights each grid point by the inverse of its bootstrap variance. Plateau points have narrow intervals and slopes near zero, so they dominate, and a nearly flat prediction (e.g. a global mean that averages rising and falling edges) can score well while getting the edge direction wrong. Read `median_curve_error` together with `median_curve_error_unweighted`, `shape_correct` and `sign_correct`.

## Paired differences vs baselines (model minus baseline; negative = model better; 95% intervals over held-out papers)

| level | model | baseline | n_common | p50_error_diff | p50_diff_lo | p50_diff_hi | curve_error_diff | curve_diff_lo | curve_diff_hi |
|---|---|---|---|---|---|---|---|---|---|
| mineral | version_a@properties | global_mean | 232 | -0.111 | -0.422 | 0.0739 | 0.00391 | -0.000306 | 0.0252 |
| mineral | version_a@properties | sorbate_class_mean | 232 | -0.00639 | -0.255 | 0.078 | 0.00024 | -0.00205 | 0.00425 |
| mineral | version_a@properties | mineral_class_mean | 232 | -0.158 | -0.345 | 0.111 | 0.00104 | -0.001 | 0.0263 |
| pair | version_a@properties | global_mean | 232 | -0.026 | -0.21 | 0.172 | 0.0148 | 0.00195 | 0.036 |
| pair | version_a@properties | sorbate_class_mean | 232 | 0.287 | 0.0324 | 0.387 | 0.00206 | -0.000625 | 0.0139 |
| pair | version_a@properties | mineral_class_mean | 232 | 0.0517 | -0.157 | 0.254 | 0.0187 | 0.00357 | 0.0445 |
| sorbate | version_a@properties | global_mean | 232 | 0.235 | 0.00841 | 0.392 | 0.0182 | 0.00564 | 0.0422 |
| sorbate | version_a@properties | sorbate_class_mean | 232 | 0.168 | -0.0492 | 0.307 | 0.00532 | -0.00154 | 0.0196 |
| sorbate | version_a@properties | mineral_class_mean | 232 | 0.383 | 0.161 | 0.5 | 0.0227 | 0.00701 | 0.0518 |
| study | version_a@properties | global_mean | 232 | -0.207 | -0.48 | 0.0178 | 0.00237 | -0.000854 | 0.0147 |
| study | version_a@properties | sorbate_class_mean | 232 | -0.038 | -0.159 | 0.0684 | -4.34e-05 | -0.00271 | 0.000861 |
| study | version_a@properties | mineral_class_mean | 232 | -0.205 | -0.457 | 0.105 | 0.00734 | 0.000387 | 0.0311 |
| mineral | version_b@properties | global_mean | 232 | -0.111 | -0.422 | 0.0739 | 0.00182 | -0.000487 | 0.0218 |
| mineral | version_b@properties | sorbate_class_mean | 232 | -0.00639 | -0.255 | 0.078 | -0.000168 | -0.00689 | 0.00114 |
| mineral | version_b@properties | mineral_class_mean | 232 | -0.158 | -0.345 | 0.111 | 0.000816 | -0.00104 | 0.0233 |
| pair | version_b@properties | global_mean | 232 | -0.026 | -0.21 | 0.172 | 0.0103 | 0.000802 | 0.0288 |
| pair | version_b@properties | sorbate_class_mean | 232 | 0.287 | 0.0324 | 0.387 | 0.000742 | -0.00269 | 0.0116 |
| pair | version_b@properties | mineral_class_mean | 232 | 0.0517 | -0.157 | 0.254 | 0.0127 | 4.88e-05 | 0.039 |
| sorbate | version_b@properties | global_mean | 232 | 0.235 | 0.00841 | 0.392 | 0.0204 | 0.00446 | 0.0427 |
| sorbate | version_b@properties | sorbate_class_mean | 232 | 0.168 | -0.0492 | 0.307 | 0.00173 | -0.00403 | 0.014 |
| sorbate | version_b@properties | mineral_class_mean | 232 | 0.383 | 0.161 | 0.5 | 0.0226 | 0.00445 | 0.0525 |
| study | version_b@properties | global_mean | 232 | -0.207 | -0.48 | 0.0178 | 0.00094 | -0.00123 | 0.0121 |
| study | version_b@properties | sorbate_class_mean | 232 | -0.038 | -0.159 | 0.0684 | -0.000432 | -0.00483 | 0.000272 |
| study | version_b@properties | mineral_class_mean | 232 | -0.205 | -0.457 | 0.105 | 0.00577 | -0.000203 | 0.0212 |
| mineral | version_a@conditions | global_mean | 397 | 0.000915 | -0.0192 | 0.023 | 3.4e-05 | -0.000386 | 0.000272 |
| mineral | version_a@conditions | sorbate_class_mean | 397 | 0.119 | -0.197 | 0.411 | -0.00333 | -0.0137 | -0.000338 |
| mineral | version_a@conditions | mineral_class_mean | 397 | 0.184 | -0.0138 | 0.374 | -7.11e-05 | -0.00125 | 0.000452 |
| pair | version_a@conditions | global_mean | 397 | 0.0259 | -0.0125 | 0.0426 | -0.000127 | -0.001 | 0.000133 |
| pair | version_a@conditions | sorbate_class_mean | 397 | 0.0887 | -0.164 | 0.365 | -0.00407 | -0.0145 | -0.000962 |
| pair | version_a@conditions | mineral_class_mean | 397 | 0.128 | -0.0341 | 0.246 | 0 | -0.000782 | 0.00155 |
| sorbate | version_a@conditions | global_mean | 397 | 0.0376 | 0.00104 | 0.0688 | 7.42e-05 | -0.000362 | 0.00106 |
| sorbate | version_a@conditions | sorbate_class_mean | 397 | 0.0566 | -0.101 | 0.216 | -0.00608 | -0.0214 | -0.00197 |
| sorbate | version_a@conditions | mineral_class_mean | 397 | 0.129 | 0.0278 | 0.239 | 0.000317 | -0.000266 | 0.00153 |
| study | version_a@conditions | global_mean | 397 | 0.0198 | -0.00321 | 0.054 | 1.6e-05 | -0.000848 | 0.000649 |
| study | version_a@conditions | sorbate_class_mean | 397 | 0.15 | -0.0535 | 0.493 | -0.00166 | -0.00653 | 3.1e-05 |
| study | version_a@conditions | mineral_class_mean | 397 | 0.169 | 0.0668 | 0.296 | 0.000209 | -0.000398 | 0.00262 |
| mineral | version_b@conditions | global_mean | 397 | 0.000915 | -0.0192 | 0.023 | -7.76e-05 | -0.00102 | 0.000131 |
| mineral | version_b@conditions | sorbate_class_mean | 397 | 0.119 | -0.197 | 0.411 | -0.00306 | -0.013 | -0.000411 |
| mineral | version_b@conditions | mineral_class_mean | 397 | 0.184 | -0.0138 | 0.374 | -0.000183 | -0.00133 | 0.000587 |
| pair | version_b@conditions | global_mean | 397 | 0.0259 | -0.0125 | 0.0426 | -0.000385 | -0.00161 | 7.82e-06 |
| pair | version_b@conditions | sorbate_class_mean | 397 | 0.0887 | -0.164 | 0.365 | -0.00394 | -0.0139 | -0.00118 |
| pair | version_b@conditions | mineral_class_mean | 397 | 0.128 | -0.0341 | 0.246 | -5.54e-05 | -0.000912 | 0.00114 |
| sorbate | version_b@conditions | global_mean | 397 | 0.0376 | 0.00104 | 0.0688 | -1.92e-05 | -0.000602 | 0.00102 |
| sorbate | version_b@conditions | sorbate_class_mean | 397 | 0.0566 | -0.101 | 0.216 | -0.00706 | -0.0256 | -0.00201 |
| sorbate | version_b@conditions | mineral_class_mean | 397 | 0.129 | 0.0278 | 0.239 | 0.000246 | -0.000308 | 0.00184 |
| study | version_b@conditions | global_mean | 397 | 0.0198 | -0.00321 | 0.054 | -0.000143 | -0.00128 | 0.000232 |
| study | version_b@conditions | sorbate_class_mean | 397 | 0.15 | -0.0535 | 0.493 | -0.0016 | -0.00569 | 6.9e-07 |
| study | version_b@conditions | mineral_class_mean | 397 | 0.169 | 0.0668 | 0.296 | 3.17e-06 | -0.000658 | 0.00187 |

Files: `per_curve_worst_first.csv` (every held-out curve, worst first), `metrics_by_model.csv`, `paired_differences.csv`, `verdicts.csv`, `p50_error_by_model.png`.

## Analyst notes (added after the run, 2026-10-13)

- **Every model fails at every level** (median edge error 1.1-1.8 pH vs the 0.5 pH line; none beats every baseline). Interval coverage is close to the 0.9 target (0.84-0.89) except for property-based models leaving out a whole sorbate (edge coverage 0.66): they are overconfident when extrapolating to a new sorbate.
- **Why the classes predict so little although Stage 2 found a large class share.** Edge spread is 1.9 pH overall and 1.4-2.1 pH *within* each sorbate class (U(VI) alone: 1.7 pH). In squared error the sorbate-class mean does help (RMSE 1.95 -> 1.80 pH, about 14% less squared error, leaving one paper out); most of Stage 2's "class + pair" share is the specific pair (32%), which does not transfer to an unseen pair.
- **Diagnostic, not a spec baseline: the same pair measured in another paper.** Leaving one paper out, predicting a curve's edge by the mean edge of the same mineral-sorbate pair in OTHER papers gives median error **0.60 pH** (RMSE 1.20; 287 curves whose pair appears in another paper), against 0.97 pH for the sorbate-class mean on the same curves. For the 118 curves whose pair appears in only one paper, nothing better than the class mean (1.73 pH) is available. So the plain-average cross-paper ceiling for a system is ~0.6 pH (not an irreducible floor; conditions-matched baselines do better), and transfer to an unmeasured system from classes / the property table / conditions is ~1.1-1.8 pH.
- The spec's decisive baseline (edge from PZC and first hydrolysis constant) and the descriptor feature set did not run: the descriptor tables are empty.
- Run time 73 min (paired-difference bootstrap over papers is the slow step).
