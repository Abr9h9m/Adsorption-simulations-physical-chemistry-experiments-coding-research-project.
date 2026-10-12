# Pipeline Run Summary (real data)

## Per-system fingerprints (scaled units)

| system | N | bandwidth | valid_pts | mean_grad_mag | std_grad_mag | mean_lambda1 | mean_lambda2 | std_lambda1 | std_lambda2 | frac_cross_positive | frac_pH_dominant |
|---|---|---|---|---|---|---|---|---|---|---|---|
| goethite-Cl(-1)+Na(+1)+P(+5)-Se(+4) | 104 | (0.15, 0.15) | 32 | 136 | 72.6 | 1.55e+05 | -0.0143 | 2.13e+04 | 0.0186 | 0.688 | 0 |
| ferrihydrite-N(+5)+Na(+1)+P(+5)-U(+6) | 105 | (0.3, 0.3) | 120 | 0.515 | 0.196 | 3.4 | -0.195 | 0.777 | 0.0115 | 0.1 | 0.467 |
| montmorillonite-Cl(-1)+Na(+1)-U(+6) | 66 | (0.3, 0.3) | 65 | 3.12 | 2.12 | 14.4 | -136 | 30.5 | 118 | 1 | 0.0154 |
| goethite-N(+5)+Na(+1)-U(+6) | 205 | (0.2, 0.2) | 21 | 1.14 | 0.935 | -0.0989 | -2.96 | 0.257 | 1.23 | 1 | 0.381 |

## Bootstrap uncertainty at the representative point (gradient std; Hessian [Hpp,Hii,Hpi] std; real units)

| system | success_frac | grad_std | hess_std |
|---|---|---|---|
| goethite-Cl(-1)+Na(+1)+P(+5)-Se(+4) | 1.0 | [2.385e-03 5.075e+00] | [3.055e-03 1.470e+04 2.449e+00] |
| ferrihydrite-N(+5)+Na(+1)+P(+5)-U(+6) | 1.0 | [0.017 0.468] | [0.01  2.683 0.127] |
| montmorillonite-Cl(-1)+Na(+1)-U(+6) | 0.97 | [0.01  1.484] | [1.375e-02 3.090e+02 1.038e+00] |
| goethite-N(+5)+Na(+1)-U(+6) | 0.0 | None | None |

## Cross-system comparison (scaled Hessians; |lambda|-dominant eigenvector)

| system_1 | system_2 | same_mineral | same_sorbate | tier1_z_distance | tier2_shape_sim | tier2_shape_sim_signless | tier2_angle_deg | n_matched |
|---|---|---|---|---|---|---|---|---|
| goethite-Cl(-1)+Na(+1)+P(+5)-Se(+4) | ferrihydrite-N(+5)+Na(+1)+P(+5)-U(+6) | False | False | 5.388 | 0.203 | 0.211 | 85.577 | 31 |
| goethite-Cl(-1)+Na(+1)+P(+5)-Se(+4) | montmorillonite-Cl(-1)+Na(+1)-U(+6) | False | False | 5.706 | nan | nan | nan | 0 |
| goethite-Cl(-1)+Na(+1)+P(+5)-Se(+4) | goethite-N(+5)+Na(+1)-U(+6) | True | False | 5.04 | nan | nan | nan | 0 |
| ferrihydrite-N(+5)+Na(+1)+P(+5)-U(+6) | montmorillonite-Cl(-1)+Na(+1)-U(+6) | False | True | 4.624 | nan | nan | nan | 0 |
| ferrihydrite-N(+5)+Na(+1)+P(+5)-U(+6) | goethite-N(+5)+Na(+1)-U(+6) | False | True | 2.484 | 0.816 | 0.816 | 22.157 | 47 |
| montmorillonite-Cl(-1)+Na(+1)-U(+6) | goethite-N(+5)+Na(+1)-U(+6) | False | True | 3.669 | nan | nan | nan | 0 |

## Metric sanity flags
- Signed shape similarity treats an increasing edge (e.g. cation) and a decreasing edge (e.g. anion) as opposite shapes; use the signless column to ask about geometry independent of sorbate charge.
- Only 4 systems: Tier-1 z-scored distances are descriptive only.