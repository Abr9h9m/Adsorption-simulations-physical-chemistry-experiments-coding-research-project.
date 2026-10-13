# PH_ONLY_TEST_PROTOCOL_ADDENDUM_1.md: more tests and modifications

2026-10-13. Extends `PH_ONLY_TEST_PROTOCOL.md` (E0–E10 and F). All ground rules there still apply: exploratory label, locked test set, pre-declared decision rules, one change at a time, synthetic test with a planted null, no descriptor values from memory, plain-English summary on every experiment.

Why this addendum: (1) the literature pass (`LITERATURE_REVIEW.md`) gave chemical reasons for several discrepancies that the protocol does not yet test directly; (2) the original program tests *what to add to the model*, but not *how fragile our conclusions are* or *whether a different model class would do better*. Items marked **[lit]** come from a literature lead; leads marked title-only in the review must be read before the result is worded as confirming them.

---

## A. Priority table

| Rank | ID | What | Why it could matter | Effort | Needs human data? |
|---|---|---|---|---|---|
| 1 | M-Power | Power and minimal detectable effect for every test | Makes nulls (e.g. ionic strength) interpretable; stops over-reading | 1 d | no |
| 2 | E11 | Proton stoichiometry: is the log K slope b chemically interpretable? | Gives the PI a chemistry reason for curve steepness | 2 d | no |
| 3 | E12 | Loading shifts the edge (high-/low-affinity sites, Freundlich exponent) **[lit]** | Explains the high-loading Kd drop with a mechanism | 3 d | no |
| 4 | E13 | Competition by co-solutes (carbonate, phosphate, silicate, sulfate) **[lit]** | Hidden variable behind several outliers | 3 d | no (from electrolyte columns) |
| 5 | E14 | Specification curve (multiverse) over all extraction choices | Shows which conclusions survive arbitrary choices | 3 d | no |
| 6 | E15 | Model-class bake-off incl. random forest, with grouped vs random splits | Direct comparison to the L-SURF style; shows how much random splits inflate performance | 4 d | no |
| 7 | E16 | Leave-one-mineral-out and leave-one-sorbate-out transfer | Tests the real "new system" use case | 2 d | no |
| 8 | E17 | Particle-concentration diagnostics for cation edges **[lit]** | Tests a specific mechanism for the rising-edge solids result | 3 d | partly (E10 table) |
| 9 | E18 | Edge at PZC-relative position | Chemistry reason for cation vs anion edge placement | 2 d | yes (PZC table, sourced) |
| 10 | E19 | pKa kinks: slope changes at sorbate acid constants | Chemistry reason for non-linear log K curves | 2 d | yes (E6 table) |
| 11 | E20 | Temperature and time covariates | Known confounders in a few systems | 1–2 d | no, if columns exist |
| 12 | E21 | Calibrated intervals with conformal prediction at paper level | Honest uncertainty with few papers | 2 d | no |
| 13 | E22 | Where-to-measure-next (data-value) map | Turns the model into advice for experimentalists; feeds the web interface | 2 d | no |
| 14 | E23 | Placebo and negative-control battery | Guards against false discoveries across ~20 experiments | 2 d | no |
| 15 | E24 | Source-data audit of L-SCIE digitization and conversions | Quantifies an error floor we currently ignore | 2 d + reading | yes (read the database documentation) |

Do M-Power, E23 and E24 first; they change how all later results are read.

---

## B. Modifications to existing experiments

| ID | Change | Where | Reason |
|---|---|---|---|
| M1 | Report every headline metric **two ways**: curve-weighted and paper-weighted (each paper counts once). | E0.3 harness | A few papers contribute many curves and dominate medians. |
| M2 | Add alternative edge definitions: pH20, pH50, pH80, plus width = pH80 − pH20, to the metrics. | E0.3, E1 | A single edge hides steepness errors; avoids dependence on one definition. |
| M3 | Add a **decision-oriented metric**: mean absolute error of fraction sorbed over the pH grid (what a user of the web interface sees). | E0.3 | pH error is not the same as the practical error; a 0.5 pH error is large on a steep edge. |
| M4 | Fit rising and falling edges as **separate models** (not one model with an interaction) as a sensitivity run. | E1 | Solids results already differ in sign by direction. |
| M5 | E1 gets an alternative random-effects structure: pair nested in sorbate class **crossed with** mineral class, compared by held-out error. | E1 | Tests partial pooling choice; sorbate dominates, mineral adds little. |
| M6 | Estimate the loading hinge **inside** cross-validation on training papers only, with a bootstrap interval; also test a smooth saturation form (Langmuir-type decline) against the hinge. | E1, E12 | Breakpoint was poorly located; a hinge may be the wrong shape. |
| M7 | Add a sensitivity run on the 79 conditions-matched curves with paper-level bootstrap intervals and an explicit count of distinct papers. | E0, E4 | The 0.25 pH result rests on few papers; show its uncertainty prominently. |
| M8 | E3: add a "same figure digitized twice" check (identical pH sets and near-identical values across references). | E3 | A form of duplication that inflates agreement. |
| M9 | E5: report truncation error separately for steep and shallow edges. | E5 | Extrapolation error depends on steepness. |
| M10 | Add a `data_version` field (L-SCIE release, file hash, download date) to every `RUN_INFO.json`. | all | Dataset is a living database; results must be tied to a version. |

---

## C. New experiments

Each uses the E0 harness (leave-one-paper-out, lineage clusters after E3) and the guards in the main protocol. Decision rules below are **proposed**; they go into `experiments.yaml` before running.

### M-Power: power and minimal detectable effect
**Question.** For each planned test, what is the smallest effect we could detect with the number of papers we have?
**Method.** For each experiment, simulate from the fitted model with a planted effect of varying size, at the observed paper counts and noise, and compute detection probability. Output a table: test, number of papers, minimal detectable effect at 80% power.
**Use.** Every null result is reported with its detectable effect ("no effect larger than X pH could have been detected"). The ionic-strength null (95% interval −0.06 to +0.07 pH per SD) is the first case.
**Effort** 1 day. **Depends on** E1 variance components (a placeholder from Stage 2 is fine to start).

### E11: proton stoichiometry (why are edges steep or shallow?)
**Question.** If sorption releases n protons per sorbed sorbate, the slope of log10 K against pH should be near n in the simple case. Is the fitted slope b clustered around interpretable values by sorbate charge and class?
**Method.** From the per-curve line fits (840 clean curves) collect b by sorbate, mineral and direction. Compare to the simple expectations: cation hydrolysis and proton release give positive b of order 1 to 3; anion binding with proton uptake gives negative b. Report the distribution by sorbate with paper-level intervals, the share within ±0.3 of the nearest integer or half-integer, and between-paper variance of b relative to between-sorbate variance. Expected values are **hypotheses to test, not facts**: the literature on ion binding (for example uranyl on ferrihydrite) describes surface structures through models whose proton stoichiometry depends on the complex, so the data may spread widely.
**Decision rule.** Interpretable if between-sorbate variance of b exceeds between-paper variance (ratio > 1, interval excluding 1). Otherwise report that slope is dominated by lab-to-lab effects.
**Output.** Per-sorbate slope table (feeds the web library), plain-English paragraph for Dr. Black. **Effort** 2 days.

### E12: loading shifts the edge; heterogeneous sites **[lit]**
**Background.** Selenite on goethite: higher total selenite shifted the edge to lower pH and goethite sites were heterogeneous (Balistrieri & Chao 1987, abstract read). Cd on hydrous ferric oxide needed strong and weak sites and showed Langmuir behaviour at low and Freundlich at moderate concentration (Dzombak & Morel 1986, abstract read).
**Question.** Within a paper and pair, does the edge move with total sorbate, in which direction, and does the pattern fit a two-site picture?
**Method.**
1. **Within-paper concentration series:** curves differing mainly in total sorbate (solids equal within 10%). Effect of log10 total sorbate on native edge, solids-normalised edge, plateau height, slope b.
2. **Freundlich exponent:** at fixed pH, regress log10 sorbed on log10 aqueous concentration across the series; exponent below 1 indicates heterogeneity. Report per pair, with paper-level intervals.
3. **Two-site test:** compare a one-site and a two-site (strong+weak) model for log Kd vs loading using held-out likelihood.
**Decision rule.** Heterogeneity supported if the Freundlich exponent is below 1 with 95% interval excluding 1 in at least the pairs with ≥ 3 loading levels, and the two-site model beats one-site in held-out likelihood. Count how many pairs qualify; expect few.
**Pitfalls.** Precipitation at high loading mimics saturation; flag curves where aqueous concentration may exceed solubility if the analysis can say so from the data (do not guess solubility limits; ask Samuel for a cited source). **Effort** 3 days.

### E13: competing co-solutes **[lit]**
**Background.** Balistrieri & Chao report competition with selenite in the order phosphate > silicate ≥ citrate > molybdate > bicarbonate/carbonate > oxalate > fluoride > sulfate (abstract read). This supports a continuous competition variable.
**Method.** From electrolyte and `C(+4)`, `P(+5)`, `Si`, `S(+6)` columns, build a per-curve vector of competing-anion molarity (carbonate through the E7 variables). Test, within sorbate class (anions first), whether log10 K at fixed pH falls with competitor concentration, and whether edges shift to lower pH (anion edges) with competitor concentration. Negative control: cation sorbates.
**Decision rule.** Keep if the coefficient for anion sorbates has 95% interval excluding zero in the expected direction and the cation control includes zero. **Pitfalls.** Reported electrolyte columns encode oxidation state rather than charge (see `CLAUDE.md`); reuse the corrected mapping. **Effort** 3 days.

### E14: specification curve (multiverse)
**Question.** Which headline results survive reasonable alternative analysis choices?
**Method.** Pre-declare a grid of defensible choices: mid-range window (0.01–0.99, 0.03–0.97, 0.10–0.90), minimum points per curve (5, 8, 10), line-fit R² threshold (0.3, 0.5, 0.7), minimum papers per pair (2, 3), solids-missing handling, edge definition (pH20/50/80), duplicate collapse (yes/no), weighting (curve/paper). For each combination re-estimate the headline quantities: B0 and B3 errors, the conditions-matching gain, the falling and rising solids slopes, the loading Kd drop, the ionic-strength null. Plot each estimate across all combinations.
**Decision rule.** A conclusion is "robust" if its sign and interval conclusion hold in ≥ 90% of specifications. Report the rest as fragile in the paper.
**Effort** 3 days. **Depends on** E0, E1.

### E15: model-class bake-off and the inflation from random splits
**Question.** Does a flexible machine-learning model beat the mixed model under honest validation, and how much does careless validation inflate apparent skill?
**Method.** Models: B0–B5, E1 mixed model, gradient-boosted trees and random forest on tabular features (sorbate and mineral identifiers or properties, solids, loading, ionic strength, pH, co-solutes), and a Gaussian process on log K over pH with paper effects. For each, run (a) leave-one-paper-out, (b) a **random 80/20 split by point** (the common but leaky protocol). Report the performance gap between (b) and (a) for every model.
**Why.** The prior ML work on this database used chemistry-informed random forests (L-SURF; full paper not yet read). A demonstration that point-wise random splits overstate performance for compiled sorption data would be a result in itself, and it positions our paper-level validation.
**Decision rule.** Report all; adopt a flexible model only if it beats E1 on held-out `logK_rmse` with the paired paper-level interval below zero. **Pitfalls.** Tuning must happen inside the training papers. **Effort** 4 days.

### E16: transfer tests that match real use
**Question.** How well do we predict (a) a new mineral for a known sorbate and (b) a new sorbate on a known mineral, compared with held-out papers?
**Method.** Leave-one-mineral-out and leave-one-sorbate-out versions of the harness (build on the existing leave-sorbate-out numbers). Compare E1 (with whatever descriptors exist) against class means. Report by class.
**Decision rule.** Report only; define "useful" as a median error below the class-mean baseline with the interval excluding zero. **Effort** 2 days.

### E17: particle-concentration diagnostics for cation edges **[lit]**
**Background.** The decline of apparent Kd with increasing solids is a long-recognized effect with proposed causes such as incomplete separation of fine particles. I have only seen titles and links for the papers; read them before wording this.
**Question.** Does the weaker-than-expected shift of rising edges with solids (−0.49 vs about −1.5 pH per tenfold) behave like a separation artifact?
**Predictions to test (if the artifact explanation holds).** (i) the deficit is larger for strongly sorbing systems (higher Kd); (ii) larger when separation is by filtration with large pores than by ultracentrifugation or small pores (needs E10 table); (iii) larger in papers with high solids; (iv) absent for falling edges (as found).
**Method.** Add Kd level, solids, and separation method to the rising-edge solids model as interactions. **Decision rule.** Report the interactions with intervals; no adoption into the model unless prediction (i) or (ii) holds with an interval excluding zero. **Effort** 3 days; (ii) waits for E10 data.

### E18: PZC-relative edge position
**Question.** Is the edge position explained by where the mineral's surface charge changes sign?
**Data.** A `mineral_pzc.csv` with value, method, source (human-filled; never from memory).
**Method.** Within sorbate class (cations or anions), regress edge pH on mineral PZC across minerals, paper random effect; test the sign (cations: higher PZC → higher edge; anions: higher PZC → higher edge too for anion release at high pH). Report as hypotheses, not facts. **Decision rule.** Keep if PZC reduces the mineral-level variance of the edge by ≥ 20% with interval excluding zero. **Effort** 2 days after the table exists.

### E19: slope kinks at acid constants
**Question.** For oxyanions and weak acids, does the log K vs pH line change slope near the sorbate's pKa values (speciation change), which would explain curves that a straight line fits poorly?
**Method.** For curves with enough mid-range points, fit a piecewise-linear log K with a breakpoint free vs fixed at the nearest tabulated pKa (E6 table); compare held-out likelihood; test whether estimated breakpoints cluster near pKa values (permutation test of distances). Control: cation sorbates. **Decision rule.** Supported if free breakpoints are significantly closer to pKa than permuted ones, paper-level interval. **Effort** 2 days after the E6 table.

### E20: temperature and time
Check the raw file for temperature and contact-time columns (E0.1). If present: add as covariates; compare curves from the same paper differing in temperature only. Literature leads exist for temperature on selenate/goethite (title only), so report the effect without assuming a direction. **Effort** 1–2 days.

### E21: calibrated intervals (conformal, paper level)
**Question.** Are our 90% intervals calibrated for a new paper?
**Method.** Split-conformal or CV+ prediction intervals where the exchangeable unit is the **paper**; compare coverage and width to parametric intervals from E1. Report coverage by pair size (number of papers) and by direction. **Decision rule.** Prefer the method whose coverage lies in [0.85, 0.95] with the narrower width. **Effort** 2 days.

### E22: where to measure next
**Method.** Using the E1 model, compute for each mineral–sorbate pair the expected reduction in predictive variance from one additional paper at a given pH range and condition set; rank unmeasured or thinly measured pairs and conditions. Output a ranked table and a coverage-gap map for the web interface and for Dr. Black's lab planning. **Decision rule.** Report only. **Effort** 2 days.

### E23: placebo and negative-control battery
Run the full pipeline on data with the signal broken, and require null results: (a) shuffle paper labels among curves of a pair; (b) shuffle solids within a pair; (c) replace the covariate of interest with random noise matched in distribution; (d) permute pH values within curves (should destroy edges); (e) a planted covariate of known size (recovered). Report false-positive rate across all experiments' decision rules; if above the nominal rate, tighten rules. **Effort** 2 days. **Do early.**

### E24: source-data audit (L-SCIE)
**Question.** What error floor and conversions are baked into the compiled values?
**Method.** Read the L-SCIE data descriptor / database documentation (not yet read) and list: how values were digitized from figures, which unit conversions were applied, what quality checks exist, known issues, versioning. Then test the data against what is documented: rounding patterns (pH values clustering), repeated digits, values clipped at 0 or 1, percent-vs-fraction mixups by reference, impossible sums. Estimate a digitization noise floor from curves that appear in two sources if any. **Output.** `E24/SOURCE_AUDIT.md` and an `error_floor` figure used as a lower bound on any achievable edge error. **Effort** 2 days plus reading; Samuel should also ask the LLNL data owners about known issues.

---

## D. Updated order of work

1. Week 2: M-Power skeleton, E23, E24, M10; (main protocol) E0, E3.
2. Week 3: E1, E2 plus M1–M6; E14 grid defined and frozen **before** results.
3. Week 4: E12, E13, E11, E16, E4, E5, E8, E7 Step 1.
4. Week 5: E15, E21, E17 (partial), E20; start human-entry tables (E6, E9, E10, E18).
5. Week 6: E19, E18, E17(ii), E22; integration F.
6. Week 7: locked-set evaluation, ablation, write-up.

## E. Added decisions

| ID | Decision | Default |
|---|---|---|
| D8 | Accept the specification-curve rule (≥ 90% of specifications) for calling a result robust | Yes |
| D9 | Ask LLNL data owners about digitization, conversions and known issues (E24) | Yes, Samuel to email |
| D10 | Add PZC table (E18) to the human data-entry list | Yes, Samuel, sourced per row |
| D11 | Priority for an external reproduction check (second person re-runs one experiment end to end) | Abraham re-runs E1 |

## F. Added definition of done
- Power table row for the experiment filled.
- Placebo test run for the experiment's decision rule (E23).
- Entry in the specification-curve grid if the experiment feeds a headline number.
- Any literature-based hypothesis is labelled **[lit]** with the source's read status; no result is worded as confirming a paper whose content was not read.
