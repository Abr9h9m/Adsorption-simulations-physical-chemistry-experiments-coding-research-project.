# E13 Competing co-solutes

**Plain English.** Other dissolved anions such as phosphate or carbonate can take the binding sites an anion like selenite needs. We measured how much of such competitors each experiment contained and checked whether more competitor means less sorption for anions, but not for metal cations (the control). Result: **DO NOT KEEP competitor term (rule not met)**.

> EXPLORATORY. **[lit]** Balistrieri & Chao 1987 (abstract read). Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Curves with a competitor in the electrolyte

| class | curves | with_competitor |
|---|---|---|
| inner_sphere_prone | 399 | 86 |
| organic_acid | 32 | 0 |
| outer_sphere_prone | 76 | 5 |
| oxyanion | 133 | 2 |
| unclassified | 1 | 0 |

Most common competitors: C(+4) (58), P(+5) (12), S(+6) (6), Pyromellitate(-4) (5), Oxalate(-2) (3), Salicylate(-2) (3), Humic acid (3), Fulvic acid (2), Si(+4) (2), F(-1) (1).

## Within-pair effect per decade of competitor concentration (clustered by unit)

| set | outcome | n | pairs | units | coef | ci_lo | ci_hi | p |
|---|---|---|---|---|---|---|---|---|
| oxyanion (test) | log10 K at pair reference pH | 13 | 1 | 4 | 0.0973 | -0.252 | 0.447 | 0.585 |
| oxyanion (test) | native edge (pH) | 13 | 1 | 4 | 0.482 | -0.00362 | 0.968 | 0.0517 |
| cations (control) | log10 K at pair reference pH | 205 | 22 | 42 | 0.0454 | -0.0193 | 0.11 | 0.169 |
| cations (control) | native edge (pH) | 205 | 22 | 42 | -0.0371 | -0.124 | 0.0503 | 0.406 |

Expected for anions: negative on log10 K and negative on the (falling) edge.
