# Model adjustments (accepted and rejected, with evidence)

Locked test set: 20% of papers, seeded (decision D1 default). Each adjustment enters the model only if it meets its pre-declared rule on development papers.

| adjustment | decision | evidence |
|---|---|---|
| E5 slope-based QC rule (edge error predicted from SE(b) and extrapolation) | DOES NOT MEET RULE (adoption needs decision D3) | retains 0.0% of census curves vs Stage 1 36.3%; validated median error nan pH; rank correlation 0.65 |
| E5 slope-based QC rule (edge error predicted from SE(b) and extrapolation) | MEETS RULE (adoption needs decision D3) | retains 93.4% of census curves vs Stage 1 36.3%; validated median error 0.11 pH; rank correlation 0.52 |
| E4 lab random effect / different-lab matching | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | B3-B0 different lab (exact): 0.000 [0.000, 0.000]; B3 median 0.566 |
| E8 class-specific ionic-strength term | ACCEPT | outer-sphere vs inner-sphere slope difference 0.638 [0.165, 1.110] pH per log10 I |
