# Model adjustments (accepted and rejected, with evidence)

Locked test set: 20% of papers, seeded (decision D1 default). Each adjustment enters the model only if it meets its pre-declared rule on development papers.

| adjustment | decision | evidence |
|---|---|---|
| E5 slope-based QC rule (edge error predicted from SE(b) and extrapolation) | DOES NOT MEET RULE (adoption needs decision D3) | retains 0.0% of census curves vs Stage 1 36.3%; validated median error nan pH; rank correlation 0.65 |
| E5 slope-based QC rule (edge error predicted from SE(b) and extrapolation) | MEETS RULE (adoption needs decision D3) | retains 93.4% of census curves vs Stage 1 36.3%; validated median error 0.11 pH; rank correlation 0.52 |
| E4 lab random effect / different-lab matching | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | B3-B0 different lab (exact): 0.000 [0.000, 0.000]; B3 median 0.566 |
| E8 class-specific ionic-strength term | ACCEPT | outer-sphere vs inner-sphere slope difference 0.638 [0.165, 1.110] pH per log10 I |
| E4 lab random effect / different-lab matching | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | B3-B0 different lab (exact): -0.092 [-0.267, 0.001]; B3 median 0.566 |
| E9 surface-area normalisation of solids | DO NOT ADOPT area normalisation (rule not met) | within-pair R2 mass 0.240 vs area 0.271; breakpoint CI width 5.02 (per g) vs 4.67 (per m2) |
| E1 log10 K mixed model (two-step) as the core model | ACCEPT | multi-unit pairs: median edge error E1 0.882 vs B3 0.962 pH; logK paired diff vs B3 -0.020 [-0.071, 0.038]; coverage 0.85; usage 0.81 |
| E1 log10 K mixed model (two-step) as the core model | ACCEPT | multi-unit pairs: median edge error E1 0.882 vs B3 0.962 pH; logK paired diff vs B3 -0.018 [-0.158, 0.096]; coverage 0.85; usage 0.81 |
| E7 log10 pCO2 level covariate (step 1a) | DO NOT KEEP log10 pCO2 (rule not met) | carbonate-sensitive: 0.059 [-0.073, 0.149]; control: 0.014 [-0.025, 0.043] |
| E21 interval method | PREFER conformal | parametric coverage 0.85 width 5.91; conformal 0.90 width 5.87 |
| E11 slope as a chemical descriptor (library field) | UNDECIDED (ratio interval includes 1) | sorbate/paper variance ratio 1.29 [0.56, 2.42] |
| E13 competitor molarity term | DO NOT KEEP competitor term (rule not met) | oxyanion (test), log10 K at pair reference pH: -0.110 [-0.525, 0.306]; oxyanion (test), native edge (pH): 0.299 [-0.577, 1.176]; cations (control), log10 K at pair reference pH: -0.168 [-0.285, -0.051]; cations (control), native edge (pH): 0.342 [0.104, 0.581] |
| E13 competitor molarity term | DO NOT KEEP competitor term (rule not met) | oxyanion (test), log10 K at pair reference pH: -0.110 [-0.525, 0.306]; oxyanion (test), native edge (pH): 0.299 [-0.577, 1.176]; cations (control), log10 K at pair reference pH: -0.150 [-0.255, -0.046]; cations (control), native edge (pH): 0.300 [0.087, 0.512] |
