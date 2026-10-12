# Pipeline Run Summary (synthetic data)

## Per-system fingerprints (scaled units)

| system | N | bandwidth | valid_pts | mean_grad_mag | std_grad_mag | mean_lambda1 | mean_lambda2 | std_lambda1 | std_lambda2 | frac_cross_positive | frac_pH_dominant |
|---|---|---|---|---|---|---|---|---|---|---|---|
| goethite-U(+6) | 600 | (0.1, 0.1) | 48 | 19.8 | 17.2 | 86.7 | -2.31 | 89.6 | 10.9 | 0.542 | 0.646 |
| goethite-Se(+4) | 600 | (0.15, 0.15) | 78 | 14.4 | 7.84 | 3.25 | -20.5 | 4.92 | 24.9 | 0.333 | 0.821 |
| montmorillonite-U(+6) | 600 | (0.15, 0.15) | 91 | 3.47 | 0.413 | 0.381 | -1.26 | 0.948 | 1.56 | 0.56 | 1 |
| ferrihydrite-U(+6) | 600 | (0.075, 0.075) | 24 | 24.7 | 24.6 | 200 | -3.44 | 183 | 13.4 | 0.5 | 0.375 |

## Bootstrap uncertainty at the representative point (gradient std; Hessian [Hpp,Hii,Hpi] std; real units)

| system | success_frac | grad_std | hess_std |
|---|---|---|---|
| goethite-U(+6) | 1.0 | [0.368 6.139] | [ 0.455 37.353  3.42 ] |
| goethite-Se(+4) | 1.0 | [0.18  3.802] | [ 0.227 14.975  1.109] |
| montmorillonite-U(+6) | 1.0 | [0.057 1.439] | [0.063 5.654 0.359] |
| ferrihydrite-U(+6) | 1.0 | [ 0.46  11.014] | [ 1.065 88.056  5.851] |

## Fitted vs true at the representative point (validation)

| system | fitted_grad | true_grad |
|---|---|---|
| goethite-U(+6) | [ 15.638 -78.246] | [ 14.701 -51.16 ] |
| goethite-Se(+4) | [-15.996  33.691] | [-18.436  37.366] |
| montmorillonite-U(+6) | [3.702 0.218] | [ 3.983 -1.57 ] |
| ferrihydrite-U(+6) | [ 10.876 -77.124] | [  9.929 -54.758] |

## Cross-system comparison (scaled Hessians; |lambda|-dominant eigenvector)

| system_1 | system_2 | same_mineral | same_sorbate | tier1_z_distance | tier2_shape_sim | tier2_shape_sim_signless | tier2_angle_deg | n_matched |
|---|---|---|---|---|---|---|---|---|
| goethite-U(+6) | goethite-Se(+4) | True | False | 4.239 | -0.886 | 0.912 | 13.913 | 48 |
| goethite-U(+6) | montmorillonite-U(+6) | False | True | 3.723 | 0.434 | 0.669 | 27.497 | 48 |
| goethite-U(+6) | ferrihydrite-U(+6) | False | True | 2.503 | 0.774 | 0.853 | 29.165 | 48 |
| goethite-Se(+4) | montmorillonite-U(+6) | False | False | 4.837 | -0.391 | 0.79 | 24.152 | 78 |
| goethite-Se(+4) | ferrihydrite-U(+6) | False | False | 5.512 | -0.793 | 0.873 | 27.835 | 48 |
| montmorillonite-U(+6) | ferrihydrite-U(+6) | False | True | 6.011 | 0.133 | 0.571 | 43.123 | 48 |

## Metric sanity flags
- Signed shape similarity treats an increasing edge (e.g. cation) and a decreasing edge (e.g. anion) as opposite shapes; use the signless column to ask about geometry independent of sorbate charge.
- Only 4 systems: Tier-1 z-scored distances are descriptive only.