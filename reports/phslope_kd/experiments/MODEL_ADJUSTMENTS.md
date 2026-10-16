# Model adjustments (accepted and rejected, with evidence)

Locked test set: 20% of papers, seeded (decision D1 default). Each adjustment enters the model only if it meets its pre-declared rule on development papers.

| adjustment | decision | evidence |
|---|---|---|
| E1 log10 K mixed model (two-step) as the core model | ACCEPT | multi-unit pairs: median edge error E1 0.751 vs B3 0.828 pH; logK paired diff vs B3 0.008 [-0.102, 0.094]; coverage 0.83; usage 0.78 |
| E21 interval method | PREFER conformal | parametric coverage 0.83 width 4.80; conformal 0.90 width 5.57 |
| E4 lab random effect / different-lab matching | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | B3-B0 different lab (exact): -0.032 [-0.132, 0.037]; B3 median 0.496 |
| E5 slope-based QC rule (edge error predicted from SE(b) and extrapolation) | MEETS RULE (adoption needs decision D3) | retains 89.9% of census curves vs Stage 1 30.4%; validated median error 0.17 pH; rank correlation 0.52 |
| E8 class-specific ionic-strength term | ACCEPT | outer-sphere vs inner-sphere slope difference 1.130 [0.331, 1.929] pH per log10 I |
| E9 surface-area normalisation of solids | DO NOT ADOPT area normalisation (rule not met) | within-pair R2 mass 0.048 vs area 0.008; breakpoint CI width 3.40 (per g) vs 4.67 (per m2) |
| E11 slope as a chemical descriptor (library field) | UNDECIDED (ratio interval includes 1) | sorbate/paper variance ratio 0.88 [0.30, 1.83] |
| E13 competitor molarity term | DO NOT KEEP competitor term (rule not met) | oxyanion (test), log10 K at pair reference pH: 0.097 [-0.252, 0.447]; oxyanion (test), native edge (pH): 0.482 [-0.004, 0.968]; cations (control), log10 K at pair reference pH: 0.045 [-0.019, 0.110]; cations (control), native edge (pH): -0.037 [-0.124, 0.050] |
| E15 flexible model class (RF / gradient boosting) | ADOPT random_forest, gradient_boosting | B0_all_other: grouped 0.616, random 0.368; B5_global_mean: grouped 1.208, random 1.148; E1_final: grouped 0.764, random 0.316; gradient_boosting: grouped 0.472, random 0.192; random_forest: grouped 0.604, random 0.254 |
| E15c GBM conformal intervals | reported | coverage 0.90, width 5.95 pH |
| E12 two-site loading term | ACCEPT | Freundlich 0.60 [0.43, 0.77]; LOPO SSE one-site 76.1 vs two-site 74.4 |
| E17 particle-concentration interaction | REJECT | rising solids x strength -0.043 [-0.224, 0.137] |
| E7 log10 pCO2 level covariate (step 1a) | DO NOT KEEP log10 pCO2 (rule not met) | carbonate-sensitive: 0.053 [-0.053, 0.293]; control: -0.010 [-0.037, 0.042] |
| E2 point weighting / window | KEEP W0 (0.03, 0.97) | W0 (0.01, 0.99): +5.2%, coverage 0.87; W0 (0.03, 0.97): +0.0%, coverage 0.84; W0 (0.10, 0.90): +5.4%, coverage 0.86; W1 empirical (0.03, 0.97): +0.5%, coverage 0.84; W2 logit-delta (0.03, 0.97): +0.4%, coverage 0.82 |
