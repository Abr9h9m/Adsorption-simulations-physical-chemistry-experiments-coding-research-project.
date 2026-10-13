# E13 Competing co-solutes

**Plain English.** Other dissolved anions such as phosphate or carbonate can take the binding sites an anion like selenite needs. We measured how much of such competitors each experiment contained and checked whether more competitor means less sorption for anions, but not for metal cations (the control). Result: **DO NOT KEEP competitor term (rule not met)**.

> EXPLORATORY. **[lit]** Balistrieri & Chao 1987 (abstract read). Development papers only. Locked set hash `88b1c3a1b769`. Commit `c80a5b8-dirty`.

## Curves with a competitor in the electrolyte

| class | curves | with_competitor |
|---|---|---|
| inner_sphere_prone | 457 | 93 |
| organic_acid | 42 | 0 |
| outer_sphere_prone | 94 | 8 |
| oxyanion | 160 | 2 |
| unclassified | 4 | 0 |

Most common competitors: C(+4) (53), P(+5) (15), S(+6) (14), Pyromellitate(-4) (5), F(-1) (4), Fulvic acid (4), Oxalate(-2) (3), Salicylate(-2) (3), Humic acid (2), Si(+4) (2).

## Within-pair effect per decade of competitor concentration (clustered by unit)

| set | outcome | n | pairs | units | coef | ci_lo | ci_hi | p |
|---|---|---|---|---|---|---|---|---|
| oxyanion (test) | log10 K at pair reference pH | 12 | 1 | 5 | -0.11 | -0.525 | 0.306 | 0.605 |
| oxyanion (test) | native edge (pH) | 12 | 1 | 5 | 0.299 | -0.577 | 1.18 | 0.503 |
| cations (control) | log10 K at pair reference pH | 249 | 25 | 40 | -0.15 | -0.255 | -0.0456 | 0.00492 |
| cations (control) | native edge (pH) | 249 | 25 | 40 | 0.3 | 0.087 | 0.512 | 0.00574 |

Expected for anions: negative on log10 K and negative on the (falling) edge.

## Analyst notes

- **The anion test has almost no data**: only 1 oxyanion pair (12 curves, 5 units) has curves that differ in competitor concentration, so the anion result is uninformative, not negative.
- **The cation "control" shows an effect** (log10 K -0.15 per decade of competitor, edge +0.30 pH). This is chemically plausible rather than a failed control: many listed competitors (citrate, humic acid, carbonate, phosphate) also form dissolved complexes with metal cations and so lower their sorption. A cation control is not a true null for complexing ligands; a better negative control would be a non-complexing anion (e.g. perchlorate concentration), which the file encodes as background salt.
- The pre-declared rule is not met; nothing is added to the model. The competitor variable is kept in `competitors_per_curve.csv` for the web filters.
