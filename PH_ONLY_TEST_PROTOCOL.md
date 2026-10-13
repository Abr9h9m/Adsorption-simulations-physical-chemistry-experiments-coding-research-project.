# PH_ONLY_TEST_PROTOCOL.md — Testing and analysis protocol for improving the pH-only model

Audience: Claude Code, working directly in this repository.
Owner: Samuel Uwechue. PI: Dr. Suely Black (not a field specialist; PI-facing text is plain English at general-chemistry level). Collaborator: Abraham (CS).

**Read first, in this order:** `CLAUDE.md`, `PH_ONLY_DEV_SPEC.md` (build rules, still binding), `OPEN_QUESTIONS.md`, `reports/phslope/RESULTS_SUMMARY_AND_NEXT_STEPS.md`, `reports/phslope/followup/POOLING_FOLLOWUP.md`, `reports/phslope/followup/SOLIDS_AND_LOADING.md`. Reference implementations of the two follow-up analyses are in `reports/phslope/followup/*_tables.zip` (`pool_experiments.py`, `solids_loading.py`); port them into the package with tests, do not run them as loose scripts.

This protocol lists everything we want to test or correct to make the model work better, how to test each item, and the rule for deciding whether to keep it. It does not replace the Stage 0–5 plan; it is the improvement program that runs on top of the existing exploratory Stage 1–3 results.

---

## 0. Where we are (facts this protocol builds on)

| Fact | Source |
|---|---|
| File has 38,906 rows; 1,680 clean pH-sweep curves; 745 in the core library; 405 single-edge (rising/falling) core curves from 120 papers, 115 pairs; 43 pairs with ≥2 papers | Stage 0, 1 |
| Stage 1 survival 46.8% (limit 80%): most losses are edges in sampling gaps or wide edge intervals | Stage 1 |
| The response is **fraction sorbed = Sorbed_val / Sorbate_val**. It is not corrected for the mineral amount; `log_kd` is also uncorrected | `response.py`, `load.py` |
| Held-out edge error: every class/property model 1.1–1.8 pH vs 0.5 target; plain average of the same pair in other papers 0.60 pH; conditions-matched 0.38–0.44 pH (0.25 pH on the 79 curves with a matched paper) | Stage 3, follow-up |
| Pooling across papers widens edges ~1.4–1.5×; paper-resampling intervals are ~2× the point-bootstrap intervals; ~22–31% of pooled scatter is "which paper" | Pooled, follow-up |
| Solids loading: falling edges +1.23 pH per tenfold more solids, rising −0.49; linear-Kd expectation is about ∓1.5; falling edges collapse after solids correction, rising edges overcorrect | Solids follow-up |
| Loading (mol sorbate per g solid): Kd flat to about 1e-4 mol/g, falls ~0.45 log units above (45 curves, 13 groups); anions most affected | Solids follow-up |
| Ionic strength: no detectable effect on the edge within a pair (95% interval −0.06 to +0.07 pH per SD) | Pooling follow-up |
| Descriptor tables are empty; thresholds not frozen; classes unconfirmed | OPEN_QUESTIONS |

**Numbers to reproduce (regression tests for the harness, tolerance ±0.02 pH):** held-out edge error, leave-one-paper-out, 285 core single-edge curves in groups with ≥2 papers: plain average of other papers median 0.595, nearest-conditions paper 0.375, three nearest 0.420, conditions-matched-else-average 0.437; on the 79 curves with a matched paper, plain 0.679 vs matched 0.250. Definitions are in `pool_experiments.py` Part 4.

---

## 1. Ground rules

1. **Label everything EXPLORATORY** until the locked test set is evaluated (section 3). Inherit all rules in `PH_ONLY_DEV_SPEC.md` §1 (no invented descriptor values, thresholds written before results, validation by paper never by point, uncertainty everywhere, reproducible, small tested steps).
2. **Many looks are a problem.** There are only ~120 usable papers. Every experiment here is another look at them. To limit overfitting: (a) use the locked test set (section 3); (b) pre-declare a **primary metric and decision rule** for each experiment (below) before running it; (c) correct secondary comparisons with Benjamini–Hochberg inside each experiment and report the number of tests run; (d) record **every** experiment, including failures, in `reports/phslope/experiments/REGISTRY.md`.
3. **One change at a time into the model.** An adjustment becomes part of the baseline model only if it meets its decision rule on the development papers and does not worsen any pre-declared guard metric. Accepted and rejected adjustments, with evidence, go in `MODEL_ADJUSTMENTS.md`.
4. **Synthetic first.** Each experiment that introduces a new estimator needs a synthetic test with planted truth (and a planted null) before it touches real data.
5. **Never delete data automatically.** Flagging and sensitivity analyses only. A human decides exclusions.
6. **No descriptor value from memory.** Where a table must be filled (pKa, hydrolysis constants, surface area, methods), Claude Code builds the template, the loader, and the checks; Samuel or Abraham fills values with a cited source per row.
7. **Plain-English summary** at the top of every experiment `SUMMARY.md` (3–5 sentences, no jargon beyond defined terms).
8. **Stop and ask** (write to `OPEN_QUESTIONS.md`, continue with the documented default) whenever a choice would change the scientific meaning of a result.

---

## 2. Package layout additions

```
phslope/
  experiments/
    __init__.py
    harness.py            E0: leave-one-paper-out evaluation shared by all experiments
    kd.py                 E0: per-point K, logit, per-gram Kd, mass-balance checks
    registry.py           experiment registry, multiplicity helpers, RUN_INFO
    e01_logk_mixed.py     E1
    e02_weights_censoring.py   E2
    e03_audit.py          E3 duplicates and outliers
    e04_lab_effect.py     E4
    e05_coverage.py       E5
    e06_sorbate_chem.py   E6
    e07_carbonate.py      E7
    e08_ionic_strength.py E8
    e09_surface_area.py   E9
    e10_methods.py        E10
    integrate.py          final model comparison
  config/experiments.yaml thresholds, windows, seeds, decision rules (frozen per experiment before it runs)
data/descriptors/
  sorbate_chemistry.csv   E6 (template; human-filled)
  study_methods.csv       E10 (template; human-filled)
tests/phslope/experiments/  one test file per module
reports/phslope/experiments/E0 … E10, REGISTRY.md, MODEL_ADJUSTMENTS.md
```

Run pattern: `python -m phslope.experiments.run E1` (a small dispatcher in `registry.py`). Each run writes `reports/phslope/experiments/E<N>/` with `SUMMARY.md`, `RUN_INFO.json` (git commit, config hash, data file, locked-set hash), CSVs and PNGs. Add `statsmodels`, `scikit-learn`, `pyyaml`, `pytest` to `requirements.txt` with pins that you actually installed.

---

## 3. The locked test set (do this before any experiment)

Because all 10 experiments reuse the same papers, hold some out for a single final look.

- **Rule (proposed; Samuel confirms, decision D1):** lock 20% of papers (about 24), chosen by a fixed seed, stratified by sorbate class and by whether the paper's pair also appears in another paper. Whole papers only; never split a paper.
- Write `phslope/config/locked_test_papers.txt` and commit it **now**; record its hash in every `RUN_INFO.json`. Development code must refuse to load locked papers (a `dev_papers()` function is the only way to get data; the locked set is returned only by `final_papers()` inside `integrate.py`).
- The locked set is evaluated **once**, at the end (section F), for the final model and the baselines. If it is ever opened early, record it in the registry and treat all later results as exploratory on the full data.
- Cost: fewer development papers. Alternative if Samuel declines (D1): nested leave-paper-out CV with the outer loop reported only at the end. State the choice in `MODEL_ADJUSTMENTS.md`.

---

## 4. Shared infrastructure (E0)

### E0.1 Raw-file inventory and mass-balance check
- Locate the raw file (`--data`, env `SORPTION_DATA_FILE`, `config.yaml → data.file`; ask Samuel to copy it into the project folder if not reachable).
- Print every column with type, missing share and example values. Highlight columns that could hold: equilibration or contact time, aging, atmosphere, filtration or separation, container, pH method, detection limits, reported error, surface area, material origin (synthetic/natural), bibliographic fields (authors, journal, year).
- **Mass balance:** for rows with `Sorbed_val`, `Aq_val` and total sorbate all present, compare `Aq_val` with `total − Sorbed_val`. Report the distribution of relative differences by reference. Rows within 10% are "consistent"; list references with systematic mismatch (possible unit or definition differences). Output `E0/mass_balance_by_reference.csv`.
- **Pass:** at least 90% of rows with all three fields are consistent. If not, list the references and ask Samuel before using mass balance anywhere.

### E0.2 `kd.py`
For every observation compute, with a `source` flag:
- `K = Sorbed / Aq` using reported `Aq_val` when present and consistent (`source = reported`), else `K = f / (1 − f)` from fraction sorbed (`source = mass_balance`).
- `log10K`, `logit_f`, `Kd_L_per_g = K / S` (S = solids g/L), `log10Kd`.
- Loading `L = total_sorbate_mol_L / S` (mol per g solid) and `log10L`.
- Mid-range flag: `0.03 < f < 0.97` (config; E2 revisits the window).
- Unit tests: algebraic identities (`f/(1−f) = Sorbed/Aq` under mass balance); points with `f` outside (0,1) handled without NaN leakage; solids missing gives NaN not zero.

### E0.3 `harness.py` — the single evaluation loop
Inputs: a "model" object with `fit(train_curves)` and `predict(test_curve) -> edge, log10K(pH grid), intervals`. Always leave out whole **papers** (and, where defined, whole lineage clusters from E3 and lab clusters from E4). Metrics, per held-out curve then summarised (median, IQR, RMSE, share within 0.5 and 1 pH, full per-curve table worst first):
- `edge_error` (pH) on the native edge (f = 0.5 at the solids used) and on the solids-normalised edge (Kd = 1 L/g).
- `logK_rmse` over the curve's pH points inside the mid-range (the curve-level metric; it does not depend on one extracted edge).
- `interval_coverage` of the 90% prediction interval (target 0.9, acceptable 0.8–0.95).
- `shape_correct` and `sign_correct` (rising/falling).
Report with 95% intervals from resampling **papers** (not curves). Paired differences against the baselines below.

**Baselines in every run:** (B0) plain average of other papers of the same pair and direction; (B1) nearest-conditions paper; (B2) three nearest; (B3) conditions-matched else average; (B4) sorbate-class mean for pairs with no other paper; (B5) global mean. Subsets reported separately: pairs with ≥2 papers; pairs with 1 paper; curves with a conditions-matched paper.

**Noise-ceiling report (carry-over from the earlier plan):** for each held-out curve with ≥1 other paper of the same pair, record the B0 error; report each model's error as a fraction of the gap between B5 and B0, with a bootstrap interval.

**Pass for E0:** the harness reproduces the benchmark numbers in section 0 within ±0.02 pH (regression test).

---

## 5. Experiments

Each card gives: question, data, method, metrics and decision rule, outputs, pitfalls, dependencies, effort (Claude Code working days, rough). Pre-declared decision rules are written into `experiments.yaml` before the run.

### E1 — Log K linear mixed model (the proposed new core model)
**Question.** If log10 K is linear in pH inside a curve, fraction sorbed is exactly a logistic, so we can fit a straight line per curve with paper effects. That should (a) use curves with no full edge, (b) give directly comparable parameters (steepness b, level a), (c) let covariates enter cleanly.

**Data.** Rising/falling curves with solids and total sorbate (1,143 curves; 1,108 with a line fit; 840 clean). Mid-range points only (window from E2). Pair groups with ≥2 papers for the held-out evaluation; single-paper pairs handled by shrinkage to the sorbate class (partial pooling), reported separately.

**Model (one step).**
```
log10K_ijk = a_pair + u_a[paper] + v_a[curve]
           + (b_pair + u_b[paper]) * (pH_ijk - pH_c)
           + gamma . covariates + e_ijk
```
Covariates (direction-specific coefficients): log10 solids; loading regime term (hinge at the breakpoint from the solids follow-up, estimated inside CV, not fixed from the full data); log10 total sorbate; co-solute flag; CO2 flag; ionic strength (kept to confirm the null). Random effects for pair (partial pooling by sorbate class), paper, curve. `pH_c` = pair-level reference pH (median 50% edge). Fit with `statsmodels` MixedLM (variance components); document the formulation; if convergence is poor, fit a two-step version (per-curve lines, then a meta-regression weighted by their covariance) and report both.

**Prediction.** For a held-out paper: predict `a` and `b` from pair (or class) plus covariates, with parametric-bootstrap intervals that include paper variance; derive the native edge (log10K = 0) and the solids-normalised edge (log10K = log10 S, i.e., Kd = 1 L/g), and the full log10K curve on the pH grid.

**Metrics and decision rule (primary, pre-declared).** On development papers, leave-one-paper-out:
- median native `edge_error` ≤ B3 (conditions-matched) **and** not worse than B3 on `logK_rmse`, with the paired 95% interval over papers not above zero;
- `interval_coverage` in [0.80, 0.95];
- **curve usage:** at least 70% of rising/falling curves contribute (Stage 1 core kept 405 of 1,143).
Guard metrics: not worse than B0 on pairs with ≥2 papers; no degradation on falling edges.
Secondary: variance components of `a` and `b` by sorbate class (paper, pair, curve shares); covariate coefficients with intervals; Version with and without curve random effect.

**Synthetic tests.** Plant `a`, `b`, paper offsets, a solids effect of known size per direction, a loading saturation hinge, and partial-edge sampling (no point on one side of the edge). Assert: coefficients recovered within tolerance; coverage near nominal; curves with no full edge give unbiased `edge` with wider intervals; null planted effects not detected more than the nominal rate.

**Outputs.** `E1/` variance components, coefficients, held-out tables, per-curve predictions, calibration plot, curve-usage table (how many curves each stage uses).
**Pitfalls.** The line fails for bell and multi-step curves: restrict to line-fit R² ≥ 0.5 as the main set; add a quadratic term as a sensitivity run and report how many curves need it. Points at the extremes of f amplify noise (E2). A pair with one paper cannot estimate a paper effect (shrinkage handles it; report separately). Solids and total sorbate are weakly correlated within groups (r = 0.24); report variance inflation.
**Depends on** E0. **Effort** 4–5 days.

### E2 — Weighting and censoring of points
**Question.** Points near 0% or 100% sorbed carry detection-limit and wall-loss problems; our fits weight all points equally in fraction space. Does an error model improve the fit and the prediction?

**Method.** Estimate the empirical error of log10K as a function of f, total sorbate (detection limit proxy) and pH from residuals of the E1 per-curve lines (binned, with a smooth). Compare, inside E1's CV: (W0) unweighted log10K; (W1) empirical-variance weights; (W2) fraction-space additive error (var of logit ∝ 1/(f(1−f))²); (W3) censored/Tobit treatment of points with f < 0.03 or f > 0.97 (bounds, not values); window sensitivity: (0.01, 0.99), (0.03, 0.97), (0.10, 0.90).

**Decision rule.** Adopt the scheme that lowers held-out `logK_rmse` by ≥ 5% relative to W0 **and** keeps coverage in [0.80, 0.95]; otherwise keep W0 and the (0.03, 0.97) window. Report how many points and curves each window removes.

**Synthetic.** Add heteroscedastic noise and a detection floor; assert the chosen scheme beats W0 and W0 is not worse when noise is homoscedastic.
**Pitfalls.** Reported detection limits (if any) beat inferred ones; use them if E0.1 finds them. **Depends on** E1. **Effort** 2 days.

### E3 — Duplicate and outlier audit
**Question.** Are some curves the same experiment appearing twice (inflating cross-paper agreement), and are the worst errors data problems?

**Duplicates.** For curve pairs within the same (mineral, sorbate), across references and within a reference: match points by pH within 0.02 and compare f within 0.01; flag pairs where ≥ 80% of points match. Cluster flagged curves into **lineage clusters** (connected components). Outputs `E3/duplicate_pairs.csv`, `E3/lineage_clusters.csv`. From then on, the harness treats a lineage cluster as one "paper" for leave-out. Re-run the cross-paper agreement and the B0–B3 benchmark with duplicates collapsed and report the change.

**Automated validity rules** (flags in a new `data_flag` column; nothing is dropped): f outside [−0.05, 1.05]; pH outside [0, 14] or non-monotone duplicates; response apparently in percent (values up to ~100); solids ≤ 0 or implausible (> 500 g/L); total sorbate ≤ 0; non-finite ionic strength; sign of slope contradicting shape; curves with fewer than 3 distinct pH values after cleaning.

**Outlier review.** For the 30 worst held-out curves in Stage 3, the 30 largest E1 residual curves, and the curves flagged above: write one diagnostic page per curve (data, fit, metadata, nearest other-paper curves) to `E3/outlier_pages.pdf` and a table `E3/outlier_review.csv` with empty columns `reviewer`, `verdict` (data error / real chemistry / different material / unclear) and `notes`. **Samuel (or Abraham) fills the verdict.** Then run sensitivity analyses with verdict = data error excluded.

**Decision rule.** No threshold; the output is (a) the lineage clusters used in all later CV, (b) the sensitivity of the headline results to the exclusions (report if any headline conclusion changes). **Depends on** E0. **Effort** 2–3 days plus human review time.

### E4 — Lab or research-group effect
**Question.** Does a part of the "paper" variance, and part of the conditions-matching gain, come from the same lab reusing a protocol?

**Group IDs.** (1) If the raw file has bibliographic fields, build `lab_id` as connected components of references sharing an author (surname and initial) or corresponding author. (2) Otherwise, a weak proxy from the reference code (letter prefix = author initials; two digits = year) with an explicit warning that initials are not unique; mark the result `proxy`.

**Tests.**
1. Add a lab random effect (crossed with paper) to E1; report its variance share and whether the paper share falls.
2. **Matched-gain survival test:** rerun B1–B3 requiring the matched paper to be from a **different lab** (and a different lineage cluster). Report errors with and without the same-lab matches.
3. Same-lab versus different-lab pairs: do edges of same-lab pairs differ less after adjusting for conditions?

**Decision rule.** The conditions-matching gain "survives" if, excluding same-lab matches, B3 still beats B0 with the paired 95% interval below zero and median error ≤ 0.5 pH. If not, report the gain as partly a lab effect, add the lab random effect to the model, and revisit the target in `OPEN_QUESTIONS.md`.
**Pitfalls.** Proxy groups merge unrelated labs and split related ones; state the direction of the bias. **Depends on** E1, E3. **Effort** 2 days.

### E5 — Edge-coverage artifact
**Question.** Does the estimated edge depend on how much of the pH range was measured? (Curves with similar pH span agreed more.) Can QC be based on how well the slope is determined instead of "edge bracketed"?

**Truncation experiment.** Select well-measured curves (pH span ≥ 6, line-fit R² ≥ 0.9, ≥ 12 points). Create truncated versions with windows of 2, 3, 4 and 5 pH units at random positions (seeded), keeping those with ≥ 3 mid-range points. Fit the E1 line and the logistic; record the error of the edge versus the full-curve edge as a function of (i) number of mid-range points, (ii) pH span of mid-range points, (iii) distance from the edge to the nearest measured point, (iv) the standard error of `b`.
**Outputs.** An empirical edge-error model, e.g., predicted error as a function of SE(b) and extrapolation distance; a revised QC rule; a re-run of the Stage 1 survival count under the new rule (report % of census-set curves retained at edge error ≤ 0.5 pH, as predicted by the model, **and** by validation on held-out truncations).
**Also.** Recompute the earlier similar-versus-different curve-pair analysis using edges estimated on a common window where both curves allow it; check whether the pH-span association disappears.
**Decision rule.** Adopt a QC rule that retains ≥ 70% of census-set curves **and** keeps median truncation error ≤ 0.5 pH on the retained curves. Any change to the Stage 1 survival rule is a **decision for Samuel and Dr. Black** (it relaxes a pre-set rule; record it explicitly, do not relabel the Stage 1 failure as a pass).
**Synthetic.** Logistic curves with known edge and uneven sampling. **Depends on** E1. **Effort** 2–3 days.

### E6 — Sorbate chemistry as predictors
**Question.** Does a numeric property of the sorbate predict the edge and the steepness better than class labels? (The sorbate explains most of the variance; class means did not transfer.)

**Descriptor sheet (template, human-filled with sources).** `data/descriptors/sorbate_chemistry.csv`: `sorbate, element, oxidation_state, speciation_class, effective_charge, ionic_radius_A, log_K_hydrolysis_1 (cations), pKa1, pKa2, pKa3 (acids and oxyanions), source, source_version, notes`. Suggested sources to consider (Samuel chooses and cites; record the edition): the OECD-NEA thermodynamic database series, Baes and Mesmer, IUPAC stability-constant compilations. Never fill from memory.

**Tests (mixed model with mineral effects, E1 framework).**
1. Cations: edge versus first hydrolysis constant, within mineral. Anions: edge versus the relevant pKa (the one nearest the observed edge is an outcome, so use a pre-declared rule, e.g., highest pKa below pH 11, to avoid choosing it after the fact).
2. Leave-one-sorbate-out: edge = mineral effect + c·descriptor + paper effect; compare with B4 (sorbate-class mean, 1.41 pH) and B5 (1.33 pH) from Stage 3.
3. Steepness b versus charge and class.

**Decision rule.** The descriptor model beats B4 on leave-one-sorbate-out with the paired 95% interval below zero **and** median error ≤ 1.0 pH. Otherwise report that sorbate numeric descriptors do not rescue transfer to unmeasured sorbates.
**Pitfalls.** Few sorbates (35 in the leave-sorbate-out set), so the fit rests on few points; use few descriptors; report leave-one-sorbate-out per sorbate (not only pooled). Descriptors differ between sources; run the sensitivity across sources if two are filled. **Depends on** E1, human data entry. **Effort** 3 days after the table is filled.

### E7 — Carbonate and speciation
**Question.** Does a continuous carbonate variable explain the falling and bell-shaped curves of carbonate-complexing sorbates (U(VI), Np(V), actinides), better than a yes/no CO2 flag?

**Step 1 (cheap, required).** Build continuous variables from the `Gas*` and `C(+4)` electrolyte columns: `log10_pCO2` (floor at a documented value for "none"), `DIC_added` (mol/L), `atmosphere_class` (air-equilibrated, controlled CO2, CO2-free, unknown). Add the equilibrium DIC as a pH-dependent covariate computed from pCO2 and the carbonate acid constants (state the constants and their source; Samuel confirms). Include in E1 per point: `log10 DIC(pH)`.
- **Test set:** carbonate-sensitive sorbates (U(VI), Np(V), Eu(III), Am(III) as the sorbates available) versus a negative-control set (e.g., Se(IV), oxalic acid, Ni(II)); the hypothesis is improvement for the first and no change for the second.
- **Outcome metrics:** held-out `logK_rmse` at pH > 7; classification of bell/falling shapes by DIC; coefficient of `log10 DIC` with interval.
**Decision rule.** Keep the variable if it improves held-out `logK_rmse` for the carbonate-sensitive set (paired 95% interval below zero) and does not change the control set (interval includes zero). Report the share of the 1,052 CO2-flagged curves that are only air-equilibrated.

**Step 2 (optional, after Step 1 and Samuel's go-ahead).** Aqueous speciation of the sorbate using a thermodynamic database (for example via PHREEQC, if installable in this environment; otherwise a small reaction table supplied and cited by Samuel). Compute the fraction of sorbate present as the reactive species versus pH, ionic strength, carbonate; add as an offset or covariate. Evaluate on U(VI) only first (74 single-edge curves). Do not extend to other sorbates until the U(VI) result is clear.
**Pitfalls.** Mixed units for gas columns; "none" versus "not reported". Carbonate and pH are strongly coupled; report collinearity. **Depends on** E1. **Effort** 3 days (Step 1), 5+ days (Step 2).

### E8 — Ionic strength by sorbate type
**Question.** The overall ionic-strength effect on the edge is null, but it may exist for weakly bound (outer-sphere-prone) cations, and hide in the average.

**Classes (pre-declared in `experiments.yaml`, before the run).** Outer-sphere-prone (alkali and alkaline-earth metals, e.g., Cs, Sr, Ba, Ca, Ra), inner-sphere-prone (actinides, transition and heavy metals, lanthanides), oxyanions, organic acids. Any reclassification after seeing results is reported as a separate exploratory run.

**Tests.** (1) **Within paper**: curves from the same paper and pair that differ in ionic strength and nothing else of interest (solids, total sorbate, temperature equal within 10%): effect of log10 I on the native edge, the solids-normalised edge and the plateau, by class. (2) Cross-paper version with the E1 covariates. (3) Nonlinearity: ionic-strength bands (below 0.01, 0.01–0.1, above 0.1 M) versus linear in log10 I.
**Decision rule.** For the outer-sphere class, a within-paper effect with a 95% interval excluding zero **and** a difference from the inner-sphere class (interval excluding zero). Expected sign for outer-sphere complexes: sorption decreases as ionic strength increases; report if the data contradict this.
**Pitfalls.** Few within-paper ionic-strength series; report counts. Multiple classes: BH correction. **Depends on** E0, E1. **Effort** 1–2 days.

### E9 — Surface area, site density and mineral variety
**Question.** Is "grams of mineral" the wrong unit? Would solids expressed as surface area (m² per litre), and loading per surface site, tighten the solids effect, collapse the saturation breakpoint across minerals, and separate material types (synthetic versus natural, different crystallinity)?

**Data collection (human, with a protocol).** `data/descriptors/mineral_descriptors.csv` (per mineral) and a per-reference table `data/descriptors/study_materials.csv`: `reference, mineral, material_type (synthetic / natural / commercial / unknown), synthesis_or_source, surface_area_m2_g, surface_area_method (BET etc.), source_page_or_table, notes`. Priority list generated by Claude Code: references ranked by number of curves in pairs with ≥ 3 papers; fill the top 40 first. Where a curve has `m2/L` solids already (311 rows), use it directly.

**Tests.**
1. Within-pair edge variance explained by log10 solids (g/L) versus log10 (solids × specific surface area); compare solids coefficient sizes by direction.
2. Loading per m² (and per site using `Mineralsites` once its units are confirmed): re-estimate the breakpoint; compare its bootstrap interval width with the per-gram version across minerals.
3. Within-mineral clustering of curves by material type: random effect for material, variance share.
**Decision rule.** Adopt surface-area normalisation if the solids-by-area term explains ≥ 20% more within-pair edge variance than solids by mass on the papers that have surface area, **or** the breakpoint interval narrows by ≥ 50%. State how many papers support the conclusion (it will be few).
**Pitfalls.** Surface area is measured differently in different papers (BET versus geometric); the table must record the method. Units of `Mineralsites`: confirm before use (open question). **Depends on** E1, human data entry. **Effort** 2 days after data entry.

### E10 — Methods covariates (time, aging, atmosphere, separation, pH method)
**Question.** How much of the paper-to-paper scatter is protocol: equilibration time, pre-equilibration, atmosphere, filtration or centrifugation, container material, pH adjustment, sorbate source?

**Data.** First use any columns found in E0.1. For missing ones, build `data/descriptors/study_methods.csv` keyed by `reference` with: `equilibration_time_h, solid_pre_equilibration_h, atmosphere (air / N2 / controlled), separation (filter pore size / centrifuge), container (PP / PE / glass / PTFE), pH_adjustment, pH_measured_when (initial / final), sorbate_stock_source, notes` plus `source_page_or_table`. Priority: the same ranking as E9.

**Tests.** Add each covariate to the E1 model as a fixed effect, one at a time and then jointly (few levels to avoid overfitting). Outcome: change in the **paper variance component** (the point of this experiment) and in held-out error. Special check for kinetics: curves with short equilibration times (relative to the median) should show lower plateau and a shifted edge.
**Decision rule.** Keep a covariate if it reduces the paper variance component by ≥ 10% (bootstrap interval over papers excluding zero) and does not worsen held-out error.
**Pitfalls.** Many levels and missing values; report coverage of the table per covariate and never impute silently. **Depends on** E1, human data entry. **Effort** 2 days after data entry.

---

## 6. Dependencies and order

```
E0 (inventory, kd, harness, locked set)
 ├─ E3 audit (lineage clusters feed all later CV)
 ├─ E1 mixed model ── E2 weights/censoring
 │        ├─ E4 lab effect (needs E3)
 │        ├─ E5 coverage artifact
 │        ├─ E7 carbonate (Step 1)
 │        └─ E8 ionic strength
 └─ human data entry (parallel): E6 sorbate chemistry, E9 surface area/materials, E10 methods
        → E6, E9, E10 run when the tables exist
F integration and locked-test evaluation
```

**Checkpoints (stop and report to Samuel):** after E0 + E3 (are the data clean enough?); after E1 + E2 (does the new core model beat the benchmarks?); after E4–E8 (which adjustments earned a place); before F.

Suggested schedule (weeks 2–7 of the plan; adjust to Dr. Black's decisions):

| Week | Work |
|---|---|
| 2 | E0 (inventory, kd, harness, locked set), E3 audit; start data-entry templates (E6, E9, E10) |
| 3 | E1 mixed model, E2; checkpoint 2 |
| 4 | E4, E5, E8; E7 Step 1 |
| 5 | E6, E9, E10 if tables are ready; update `MODEL_ADJUSTMENTS.md` |
| 6 | Integration, sensitivity analyses, web-interface export update |
| 7 | Locked-test evaluation, write-up, plain-English summary for Dr. Black |

---

## 7. Integration (F)

1. **Assemble the final model:** E1 core plus every adjustment that met its decision rule, in the order of effect size. Re-fit on all development papers.
2. **Ablation table:** drop each accepted adjustment one at a time; held-out error change with 95% interval. An adjustment that does not help in ablation is removed.
3. **Compare** against B0–B5 and the Stage 3 class/property models on the development papers (reproducing earlier numbers as a regression check).
4. **Open the locked test set once.** Report the final model and baselines on the locked papers, with intervals, in `reports/phslope/experiments/FINAL.md`, whatever the outcome. Report the gap between development and locked performance (an overfitting check).
5. **Export:** update `export/` tables with: per-curve line parameters (a, b, SE), solids-normalised edge, loading regime label, data flags, lineage cluster, `status` field. Add the `schema_version` increment and a changelog.
6. **Write-up:** `FINAL.md` with a plain-English section for Dr. Black: which corrections mattered, which did not, how close predictions get, and what limits remain.
7. **Update stale docs:** `README.md`, `CLAUDE.md`, and `OPEN_QUESTIONS.md` with the new status and findings (Samuel will update the Claude Docs separately).

**Success criteria for the whole program (proposed; Dr. Black confirms, decision D2):**
- Locked-set median native edge error ≤ 0.5 pH for curves with a conditions-matched paper, and ≤ 1.0 pH for pairs measured in other papers without a match;
- coverage of 90% intervals between 0.8 and 0.95;
- more than 70% of rising/falling curves used;
- improvement over B0 with the 95% interval below zero.
If these are not met, the result is a documented negative or partial result, not a reason to change the criteria after the fact.

---

## 8. Decisions needed from Samuel and Dr. Black

| ID | Decision | Default if no answer |
|---|---|---|
| D1 | Lock 20% of papers as a final test set (section 3) | Yes, 20%, seeded |
| D2 | Program success criteria (section 7) | As proposed |
| D3 | Relaxing the Stage 1 survival rule in favour of the E5 rule | Do not relax; report both |
| D4 | Who fills the human-entry tables (E3 outlier verdicts, E6, E9, E10) and in what order | Samuel for E6; Abraham for E9, E10; priority lists generated by Claude Code |
| D5 | Sources for pKa, hydrolysis constants and carbonate constants | None until chosen; E6 and E7 Step 1 wait |
| D6 | Go-ahead for E7 Step 2 (speciation software or reaction table) | No |
| D7 | Copy the raw dataset into the project folder | Needed for E0.1, E3, E4, E10 |

---

## 9. Definition of done (per experiment)

- [ ] Decision rule, primary metric and config written to `experiments.yaml` before the run.
- [ ] Synthetic test (with a planted null) passes.
- [ ] Unit tests pass; `pytest` green; earlier tests still pass.
- [ ] Real-data run on development papers only; `RUN_INFO.json` includes the locked-set hash.
- [ ] `SUMMARY.md` with plain-English paragraph, numbers, the decision-rule verdict, counts of tests run, and limitations.
- [ ] Entry in `REGISTRY.md`; accepted or rejected adjustments recorded in `MODEL_ADJUSTMENTS.md` with evidence.
- [ ] Per-curve or per-paper failures listed, not hidden.
- [ ] `OPEN_QUESTIONS.md` updated.

## 10. What not to do

- Do not look at the locked test papers before section F.
- Do not change decision rules or classes after seeing results; if they change, label the rerun exploratory and say why.
- Do not drop or edit data without a human verdict; flag it and run sensitivities.
- Do not fill descriptor values from memory or from an unnamed source.
- Do not describe an exploratory improvement as a confirmed result.
- Do not apply a blanket division of fraction sorbed by solids; the rising-edge result showed it overcorrects. Solids enters as a covariate with direction-specific effects (E1).
- Do not report only an average error; always include the per-curve table sorted worst first.
- Do not claim novelty. Prior work on sorption-edge prediction, solids-concentration effects and linear free-energy relationships exists; Samuel checks the literature before any claim is worded.
