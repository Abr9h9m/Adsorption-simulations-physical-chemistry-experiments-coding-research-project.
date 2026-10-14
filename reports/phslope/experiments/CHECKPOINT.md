# Improvement program: checkpoint report (2026-10-13)

Covers `PH_ONLY_TEST_PROTOCOL.md` (E0-E10, F) and `PH_ONLY_TEST_PROTOCOL_ADDENDUM_1.md` (M1-M10, E11-E24). **Everything is EXPLORATORY**: development papers only, the 24 locked papers have not been opened, decision rules were written into `phslope/config/experiments.yaml` before each run, and every run is listed in `REGISTRY.md`.

## For Dr. Black (plain English)

We rebuilt the core model so that it uses 81% of the usable curves instead of 36%. A machine-learning model (gradient boosting) tested the honest way, on papers it had never seen, did better still: about 0.7 pH for systems measured before and 1.1 pH for systems measured only once (versus 1.7 for the statistical model); careless testing (hiding random points instead of whole papers) would have made every model look 2-3 times better than it is: instead of requiring a full S-shaped curve, it fits a straight line to how strongly the contaminant sticks (on a log scale) against pH, which works for partial curves too. For a paper the model has not seen, it places the sorption edge to within about 0.8 pH units (median), reliably better than averaging the other papers on the same system (1.0) and slightly better than copying the most similar experiments (0.96, a difference just inside the uncertainty). Its stated uncertainty ranges are honest (they contain the true value about 90% of the time), but they are wide, about 6 pH units, which shows how much papers differ even for the same mineral and contaminant.

Several earlier conclusions changed:
- **Copies inflate agreement.** 28 curves appear in two different papers. Once copies are treated as one source, the advantage of "find the most similar experiment" shrinks and is no longer clearly better than a plain average.
- **Salt matters after all, for some contaminants.** The overall "salt has no effect" result hid opposite effects: more salt moves the edge of weakly held metals (caesium, strontium, radium, barium) by +0.8 pH per tenfold salt, as textbooks predict, and moves anion edges the other way (-0.3 pH).
- **The amount of mineral matters, and an earlier estimate was confounded.** A deliberate "shuffle the data" check showed that part of the mineral-amount effect came from comparing different contaminant-mineral systems rather than changing the amount within one system. With that fixed, anion sorption scales almost exactly as simple chemistry predicts; metal-cation sorption does not (it rises much less than expected as mineral is added).
- **Predicting a brand-new mineral or contaminant does not work yet** (about 1.5-1.8 pH error, no better than class averages). That needs the chemical property tables (surface charge points, hydrolysis constants), which must be filled from published sources.

## Status by experiment

| ID | What | Verdict (pre-declared rule) | Key number |
|---|---|---|---|
| E0 | Inventory, mass balance, harness | PASS | Harness reproduces the follow-up benchmark exactly; mass balance 99.9%; raw file has surface area, material source, CO2 pressure; no time, container or author fields |
| E1 | log10 K mixed model (two-step) | ACCEPT on the rule; gain over B3 not significant | median edge error 0.88 vs 0.96 pH; coverage 0.85; uses 81% of curves |
| E2 | Point weighting / window | KEEP W0 (0.03-0.97) | best scheme -2.5% log K error (rule: 5%) |
| E3 | Duplicates, validity | done | 28 cross-paper copies; 17 papers in lineage clusters; 62 curves queued for human review |
| E4 | Lab effect (initials proxy) | gain does not survive | matching gain small and borderline even before excluding same-lab papers; lab = 8% of level variance |
| E5 | Coverage artefact, slope-based QC | MEETS RULE (needs D3) | keeps 93% of census curves (Stage 1: 36%), validated median error 0.11 pH |
| E6 | Sorbate chemistry | WAITING | template `data/descriptors/sorbate_chemistry.csv` (human, sourced) |
| E7 | Carbonate, step 1a (pCO2) | not kept | DIC(pH) test waits for constants (D5); 87% of "CO2" curves are just open to air |
| E8 | Ionic strength by sorbate type | EFFECT FOUND | outer-sphere +0.79 pH/decade [0.32, 1.25]; oxyanion -0.30 |
| E9 | Surface area (dataset values), material | not adopted | area explains 13% more than mass (rule 20%); breakpoint not located on either scale |
| E10 | Methods covariates | WAITING | template `study_methods.csv`; no method columns in the file |
| M1-M3, M10 | Paper-weighted metrics, pH20/80, fraction error, data version | done | fraction-sorbed error ~0.15 for every model |
| E11 | Slope interpretability | UNDECIDED | sorbate/paper variance ratio 1.29 [0.56, 2.42] |
| E13 | Competing co-solutes | not kept | anion test has 1 usable pair; cation "control" responds (plausible complexation) |
| E16 | New mineral / new sorbate | not useful yet | 1.50 / 1.80 pH, no better than class means |
| E20 | Temperature | anecdotal | 3 series only; no time column |
| E21 | Paper-level conformal intervals | PREFER conformal | coverage 0.90 vs 0.85, width ~5.9 pH |
| E23 | Placebos + power | 2 of 3 pass; a failure exposed confounding, now fixed | solids placebo 0.48 -> 0.06 after within-between split |
| E12 | Loading and heterogeneous sites | HETEROGENEITY SUPPORTED | Freundlich exponent 0.66 [0.49, 0.82]; two-site beats one-site; anion edges -1.3 pH per decade of total sorbate |
| E14 | Specification curve (648 specs) | 2 of 5 headlines robust | robust: falling solids (91%), overall I null (97%); fragile: matching gain (73%), rising solids (51%), loading drop (83%) |
| E15 | Model bake-off | ADOPT gradient boosting | grouped validation: GBM edge 0.72 vs E1 0.80 (n.s.), single-paper pairs 1.08 vs 1.73 (sig.), beats B3 -0.24 [-0.40, -0.11]; random point splits overstate skill 1.7-2.8x |
| E15c | GBM follow-ups | reported | identities and conditions both matter (0.81 -> 1.19 / 1.09 pH without); conformal coverage 0.90, width 5.4 pH |
| E17 | Particle concentration (partial) | (i) not supported | falling edges scale ~linearly (+0.95), rising +0.33; (ii) needs E10 |
| E22 | Where to measure next | reported | one more paper per pair barely narrows new-paper predictions (paper variance dominates) |
| M7-M9 | Matched subset, twice-digitized, steepness | reported | matched gain on dev: 38 curves / 18 papers, interval touches 0; 2 twice-digitized pairs; steep edges truncate better |
| F | Integration (development) | final model beats B0 significantly; vs B3 borderline | 0.80 vs B0 0.99 [-0.41, -0.005]; locked set NOT opened |

**Also built:** Stage 4 predictor `phslope.predictor.predict_slope_curve` (development-paper model, distance warnings); web interface P2 v0 (`python -m curvelib.api`, http://127.0.0.1:8000: periodic table, coverage heatmap, curve viewer with server-side fits and paper-level intervals, predictor).

**Still waiting on input or data:** E6, E18, E19 (chemistry tables), E10 and E17(ii) (methods table), E24 (L-SCIE documentation; D9 email), full E7 (carbonate constants, D5), web P5 (choice of a second dataset). **Not yet done (buildable):** M4/M5 E1 structure variants (lower value now that GBM is adopted), switching the predictor and web model to gradient boosting (best after the locked-set look), web R10/R15/R17/R21 (exports, facet panel, plot-builder axes, URL state).

## Integration on development papers (F)

Final model = E1 + within-between solids split (E23) + ionic strength x sorbate type (E8). Leave-one-lineage-unit-out, pairs measured by >= 2 units (535 curves, 107 units):

| model | median edge error (pH) | 95% interval | within 0.5 pH | coverage |
|---|---|---|---|---|
| final model | 0.80 | 0.61-0.98 | 36% | 0.88 |
| E1 core only | 0.88 | 0.67-1.12 | 34% | 0.90 |
| B3 conditions-matched | 0.96 | 0.79-1.21 | 30% | - |
| B0 plain average of other papers | 0.99 | 0.82-1.26 | 27% | - |
| B5 global mean | 1.34 | 0.95-1.58 | 21% | - |

- Final minus B0: **-0.19 pH [-0.41, -0.005]**: the final model is reliably better than averaging other papers.
- Final minus B3: -0.16 pH [-0.37, +0.007]: better, but the interval just touches zero.
- Ablation (protocol F2): removing E8 changes nothing (0.00 [-0.04, +0.05]), so **E8 is a candidate for removal from the predictive model** before the locked look; its chemistry finding (E8) stands on its own. Removing the within-between split worsens the median by 0.08 pH (interval includes zero); it stays because it fixes the confounding found by E23.
- Paper-weighted median (each unit counts once): final 0.95 vs B3 1.14 vs B0 1.10.

Details: `F/SUMMARY_DEV.md`, `F/dev_ablation_and_baselines.csv`. The locked set has not been opened.

## Decisions waiting (details in OPEN_QUESTIONS.md)

D3 (adopt the E5 QC rule?), D5 (sources for pKa, hydrolysis and carbonate constants), E3 outlier verdicts (62 curves), the tables for E6 / E9 / E10 / E18 (`DATA_ENTRY_PRIORITY.csv` ranks the papers to do first), question 21 (should E1's acceptance have required a significant gain?), and the class review (question 13). The locked test set is opened only after these, once.
