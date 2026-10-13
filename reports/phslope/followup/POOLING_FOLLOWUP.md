# Pooling follow-up: capped pools, similar-curve pools, and what else explains the differences

2026-10-13. **EXPLORATORY.** Run on the Stage 1 library and Stage 0 curve table (core library of 745 curves; single-edge curves = rising or falling). I wrote and ran this as a stand-alone script (`pool_experiments.py`, in the tables zip) rather than through the `phslope` package, so numbers are not drawn from the package's own code. Seeds are fixed. The figure is `pool_followup.png`.

## Short answers

1. **Capping the number of papers helps a little.** Pools of 2 papers smear the edge less (width ratio 1.24 vs 1.49 for all papers) and carry less "which paper" scatter (14% vs 31%). Pools of 3–4 papers are barely better than pooling everything.
2. **Pooling only papers whose curves already agree helps most, with a catch.** Tightest-3 pools: ratio 1.24, paper scatter 10%, and a 95% edge interval of 0.4 pH versus 1.5 pH for everything. But picking papers because their edges agree makes the result look good by construction. It only becomes useful if we can tell *in advance* which papers will agree.
3. **We can, to a useful degree, from the experimental conditions.** The covariate analysis shows the **solids loading** (grams of mineral per litre) is the strongest thing separating similar from different curves. Matching on conditions predicted a held-out paper's edge **to a median 0.25 pH** for the 79 curves that had a conditions-matched paper, against 0.68 pH for a plain average.
4. **This revises something I wrote earlier.** I called ~0.6 pH the data's reproducibility ceiling. It is the ceiling for a plain average of other papers. Matching on conditions beats it, so part of that 0.6 pH is explainable condition differences, not irreducible noise. A target near 0.5 pH is more reachable than I said.

## Part 1 and 2: capped and filtered pools

Setup: 27 mineral–sorbate groups (separated by rising/falling) with at least 4 papers, 522 curves. Each pool is fitted as one 4-parameter logistic to the raw points and compared with the same curves fitted one by one. "Width ratio" above 1 means pooling smears the edge. Random caps use 12 random draws per group. Edge-similarity filters use the paper's median single-curve edge.

| Pool | Median papers | Width ratio (median) | Share of pools with ratio > 1.5 | Leftover scatter that is "which paper" | Passes my QC proxy* | 95% edge interval (pH) |
|---|---|---|---|---|---|---|
| all papers | 5 | 1.49 | 48% | 31% | 0% | 1.48 |
| random 4 papers | 4 | 1.33 | 41% | 27% | 6% | 1.41 |
| random 3 papers | 3 | 1.37 | 44% | 26% | 8% | 1.16 |
| random 2 papers | 2 | 1.24 | 37% | 14% | 19% | n/a |
| edges within 1.0 pH of group median | 4 | 1.34 | 33% | 17% | 19% | 0.67 |
| edges within 0.5 pH of group median | 3 | 1.29 | 32% | 10% | 23% | 0.41 |
| tightest 4 by edge | 4 | 1.26 | 33% | 13% | 11% | 0.63 |
| tightest 3 by edge | 3 | 1.24 | 33% | 10% | 30% | 0.38 |
| tightest 2 by edge | 2 | 1.24 | 30% | 2% | 44% | n/a |
| *control: widest 3 by edge* | 3 | 1.37 | 44% | 32% | 4% | 1.98 |

*QC proxy: edge has data on both sides, width not at a fitting limit, RMSE under 0.10. It is my approximation, not the Stage 1 QC.

What this says:
- **The control behaves.** Deliberately picking papers with the widest spread of edges gives the worst numbers (32% paper scatter), and the tightest the best (2%), so the metrics respond to what we think they measure.
- **Agreement removes the offset but not all the smearing.** Even when edges agree within 0.06 pH, the width ratio stays about 1.24. So some of the widening is not edge offset: papers differ in height or width, or the single-curve fits are slightly too sharp. I cannot separate those here.
- **Fewer papers helps mainly because fewer offsets are being combined**, and costs data: 2-paper pools pass the QC proxy 19% of the time and the all-paper pools 0%. The failing criterion is the fit error: all-paper pools have a median RMSE of 0.21 (fraction sorbed) against a 0.10 limit, while edge coverage and width limits are met. Each retained small pool rests on little data.
- **The "edge interval" for the all-papers pool is 1.5 pH** when whole papers are resampled. Tight pools are far narrower, partly by construction.
- Group counts shrink: 22 of 27 groups keep at least 2 papers under the 0.5 pH filter; 21 under 1.0.

## Part 3: what goes with similarity (covariates)

Data: 285 core single-edge curves in 44 mineral–sorbate–direction groups with at least 2 papers (90 papers). Covariates available at curve level: ionic strength, total sorbate, solids loading, sorbate-per-solid ratio, temperature, CO2 flag, co-solute flag, background anion, mineral site density, paper year (from the reference code), pH span of the curve. **I did not have access to the raw dataset file in this session** (it sits outside the project folder), so other raw columns were not examined.

### 3a. Within a pair, which covariates move the edge? (edge minus group mean, per 1 SD change; errors clustered by paper)

| Covariate | Effect on edge | 95% interval | p | Reading |
|---|---|---|---|---|
| **solids loading (log)**, falling edges (9 groups, 22 papers) | **+0.88 pH per SD** (about 1.5 pH per tenfold) | +0.73 to +1.04 | <0.001 | more solid, edge moves to higher pH |
| **solids loading (log)**, rising edges (35 groups, 67 papers) | −0.17 pH per SD | −0.32 to −0.02 | 0.023 | more solid, edge moves to lower pH |
| total sorbate (log) | +0.07 | −0.10 to +0.25 | 0.41 | nothing detectable |
| sorbate per gram of solid (log) | −0.05 | −0.20 to +0.10 | 0.50 | nothing detectable |
| ionic strength (log) | +0.003 | −0.06 to +0.07 | 0.92 | **clear null**, narrow interval |
| CO2 present | +0.02 | −0.13 to +0.17 | 0.80 | nothing detectable |
| co-solute present | +0.10 | 0.00 to +0.19 | 0.04 | small, borderline |
| background anion (4 types) | n/a | n/a | 0.92 | nothing detectable |
| paper year | −0.14 | −0.33 to +0.04 | 0.12 | weak hint |
| pH span of curve | +0.04 | −0.12 to +0.20 | 0.65 | nothing detectable |
| temperature | not reliable | | | only 51 curves in 6 groups, effectively 1–2 papers |

- Solids loading has the opposite sign for the two edge directions, as expected chemically: more mineral gives more binding sites, so cation edges shift to lower pH and anion edges to higher pH. The pooled coefficient (+0.31, within-group R² 0.16) hides this.
- The falling-edge effect rests on 9 groups and 22 papers, so it is large but not yet well replicated.
- A joint model with six covariates reaches within-group R² = 0.20; only solids loading is clearly non-zero.
- **Ionic strength does not move the edge** once the pair is fixed. That agrees with the earlier finding that ionic-strength curvature is not recoverable, but here it is a direct null on the edge itself.

### 3b. Cross-paper curve pairs: similar (edges within 0.5 pH, 423 pairs) vs different (more than 1.5 pH, 284 pairs)

| Difference between the two curves | Median, similar pairs | Median, different pairs | Chance a similar pair differs *less* |
|---|---|---|---|
| solids loading (decades) | 0.28 | 1.48 | 87% |
| total sorbate (decades) | 0.36 | 1.27 | 70% |
| sorbate per solid (decades) | 0.60 | 0.98 | 62% |
| paper year (years) | 8 | 13 | 62% |
| pH span of the curve (units) | 1.08 | 1.63 | 65% |
| ionic strength (decades) | 1.00 | 0.76 | 36% (similar pairs differ *more*) |
| CO2 flag differs | 1 (usually) | 0 | 40% (similar pairs differ *more*) |
| same background anion | 0 (usually different) | 1 | 33% chance a similar pair shares it more (similar pairs share it *less*) |
| co-solute flag differs | 0 | 0 | no difference |

- Spearman correlation of |difference in edge| with the covariate difference: solids loading **0.55**, total sorbate 0.32, pH span 0.26, loading 0.24, paper year 0.18; ionic strength −0.17, CO2 −0.16. Solids loading and total sorbate are only weakly related to each other within a group (r = 0.24), so they are not one effect counted twice.
- **Ionic strength, CO2 and background salt do not make curves more alike**; the sign even runs the other way. They are not what is driving agreement or disagreement.
- **Two signs of measurement effects, not chemistry:** curves with a similar **pH span** agree more (the edge estimate depends on how much of the curve was measured), and papers from the **same era** agree more (about 8 vs 13 years apart).

## Part 4: held-out test, does matching on conditions predict a new paper's edge?

Leave one paper out; predict each curve's edge from the other papers' curves of the same pair and direction. 285 curves. "Conditions matched" means within 0.5 decade of solids loading, within 1 decade of total sorbate, same CO2 flag, same co-solute flag (fallback: plain average).

| Predictor | n | Median error (pH) | RMSE (pH) | Within 0.5 pH | Within 1 pH |
|---|---|---|---|---|---|
| average of all other papers | 285 | 0.60 | 1.15 | 44% | 70% |
| single closest-conditions paper | 285 | 0.38 | 1.09 | 60% | 71% |
| 3 closest-conditions papers | 285 | 0.42 | 0.97 | 56% | 75% |
| conditions matched, else average | 285 | 0.44 | 1.04 | 55% | 74% |
| *only the 79 curves that had a matched paper:* plain average | 79 | 0.68 | 1.16 | 30% | 68% |
| *same 79 curves:* conditions matched | 79 | **0.25** | **0.70** | **70%** | 85% |

- Conditions matching cuts the median error by 27–37% on all 285 curves (0.60 to 0.38–0.44 pH), and by 63% on the 79 curves that had a matched paper (0.68 to 0.25 pH). The like-for-like comparison on those 79 is the cleanest evidence.
- Gains are in the middle of the distribution. RMSE improves less, so a minority of curves are still badly off (this ties to the outlier audit in the earlier next steps).
- **Caution:** a matched paper may come from the same research group using the same protocol, which I cannot separate from matched conditions. And 79 curves is not many.

## Caveats

- Exploratory; many comparisons and no multiplicity correction. Treat the solids-loading result as a strong lead, and the rest as descriptive.
- Part 1–2 use all rising/falling curves with a usable single-curve logistic fit, including those that failed Stage 1 QC (the point of pooling); Parts 3–4 use core curves only, where edges are trusted.
- The width ratio compares the pooled fit with single-curve logistic widths, which may be biased slightly low for sparse curves. That could account for part of the ~1.24 floor.
- Bootstrap interval uses 30 resamples of whole papers; it is rough.
- 27 groups for the pooling tests, dominated by a few large pairs (goethite–Se(IV), goethite–U(VI), ferrihydrite).
- Temperature and sorbate-per-solid have too few curves to say anything firm.
- Other raw columns (for example mineral formula details, gas partial pressures, units fields) were not tested; the raw file was not reachable here.

## What I would do next

1. **Add solids loading (with direction-specific sign) and a paper-level offset to the hierarchical model** proposed earlier. It should absorb the largest single, understood piece of the "paper" variance.
2. **Redefine the target using condition-matched prediction.** Report held-out error for (a) plain average and (b) conditions-matched, and set the "close" criterion against (b). Revisit the 0.5 pH target with Dr. Black.
3. **Build a "closest conditions" lookup in the web interface:** given a pair and conditions, show the nearest measured curves and a pooled curve from those only, with the paper-level interval.
4. **Test pooled fits using conditions-matched papers** (not edge-matched) so the improvement is not circular: pool the 2–3 closest-conditions papers and check the smearing and held-out error.
5. **Extend the covariate search to the other raw columns** once the raw file is copied into the project folder (or pointed to), including mineral formula and gas fields. Add paper-group (same-lab) identifiers if they can be derived from the reference codes or authors.
6. **Check the pH-span result:** refit curves on a common pH window and see whether similarity still depends on span. If it does, edge estimates are partly a coverage artefact and Stage 1 QC should account for it.
7. **Fix the earlier summary:** update `RESULTS_SUMMARY_AND_NEXT_STEPS.md` item A1 and section 1 point 4 (the 0.6 pH "ceiling" is the plain-average ceiling, not an irreducible one).

## Files

`pool_followup.png`; `pool_followup_tables.zip` (every CSV listed below, `pool_experiments.py`, `RUN_INFO.json`): `part12_pooled_fits.csv`, `part12_summary.csv`, `part12_paired_vs_all.csv`, `part3a_within_group_covariates.csv`, `part3a_joint_model.csv`, `part3b_similar_vs_different_pairs.csv`, `part3c_spearman_edge_diff.csv`, `part4_heldout_predictions.csv`, `part4_summary.csv`.
