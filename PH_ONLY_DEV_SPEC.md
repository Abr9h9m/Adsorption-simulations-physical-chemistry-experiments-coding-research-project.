# PH_ONLY_DEV_SPEC.md — Build spec for the pH-only slope library and transfer model

Audience: Claude Code, working directly in this repository.
Owner: Samuel Uwechue. PI: Dr. Suely Black (not a field specialist, so anything written for her is plain English at general-chemistry level). Collaborator: Abraham (CS).
Read `CLAUDE.md` first. This file adds the pH-only direction on top of it and does not replace it.
Design rationale (the "why") lives in the Claude Doc "pH-Only Slope Library and Transfer Model". This file is the "how".

---

## 0. One-paragraph summary

For each experimental sorption curve A(pH), estimate the slope curve g(pH) = dA/dpH on a shared pH grid, with uncertainty. Stack these into a library matrix G (rows = curves/systems, columns = grid points). Then answer, in order: (1) can we extract trustworthy slope curves, (2) do mineral class and sorbate class explain differences between curves more than study-to-study variation does, (3) can we predict the slope curve of a held-out system from its mineral, sorbate and conditions better than simple baselines, (4) is there a compact transformation (shift, stretch, scale of a reference curve) driven by a few descriptors. Each stage has a pass condition fixed in advance. A failed stage is a valid result: stop and report it.

Why pH only: pH is the best-covered axis in the data. The two-axis (pH × ionic strength) method failed on ionic strength (identifiability probe: ionic-strength curvature is unrecoverable; real studies have 1–3 levels). This direction needs no ionic-strength variation.

---

## 1. Ground rules

1. **Do not break existing code.** Existing modules (`local_fit.py`, `derivatives.py`, `compare.py`, `run_pipeline.py`, `data_audit.py`, …) and `test_fixes.py` must keep working. New code goes in a new package `phslope/`. Reuse, do not copy: `data_audit.prepare_data` / `compute_ionic_strength` / `electrolyte_signature` (ionic strength is already corrected for oxyanion labels), `response.compute_response`, `scaling`.
2. **No invented science.** Never fill a descriptor value (PZC, surface area, hydrolysis constant, …) from memory. Descriptor files are templates that Samuel fills with cited sources. Missing stays missing and is reported (section 8).
3. **Thresholds are written down before results are seen.** All pass/fail numbers live in `phslope/config/thresholds.yaml`, committed before Stage 3 runs (section 7, Stage 3).
4. **Validation unit is the study, never the point.** All cross-validation leaves out whole references (papers), whole pairs, whole minerals or whole sorbates. Random point splits are forbidden anywhere in this package.
5. **Uncertainty everywhere.** Every extracted slope curve carries a bootstrap interval. Every comparison states how uncertain the inputs were.
6. **Reproducible.** Seeds in config. Pinned versions in `requirements.txt`. Every script prints the git commit and config hash it ran with and writes them next to its outputs.
7. **Small, tested steps.** One module per concern, a test file per module, `pytest` passes before moving to the next stage. Commit after each task with a message that says what changed and why.
8. **Plain-English outputs for the PI.** Anything under `reports/` that is meant for Dr. Black avoids jargon. If a technical term is needed, define it in one sentence the first time.
9. **Math in docs.** Plain-text symbols inline; formulas in fenced blocks. (Applies to Claude Doc exports, not to code comments.)
10. **Ask rather than guess** when a choice would change the scientific meaning of a result (what counts as one "curve", which classes, which threshold). Put the question in `OPEN_QUESTIONS.md` and continue with the documented default.

---

## 2. Data contract

**Raw file:** `C:\Users\itzju\sc.dataset.csv` (path comes from `data_audit.CONFIG["DATA_FILE"]`; make it overridable with an environment variable `SORPTION_DATA_FILE` and a CLI flag). ~80k rows, "Appendix A" schema.

**Columns used:** `Reference`, `Set`, `SetID`, `Mineral`, `Mineral_formula`, `Sorbate`, `Temp`, `pH`, `Electrolyte1..7` and `Electrolyte1..7_val`, `Gas1..3` and `Gas1..3_val`, `Mineralsites`, `Sorbed_val`, `Sorbate_val`, `Aq_val`.

**Response:** default `fraction_sorbed = Sorbed_val / Sorbate_val` (falls back to `1 - Aq_val/Sorbate_val` when `Sorbed_val` is missing), via `response.compute_response`. Secondary: `log_kd`. Slope units are then "fraction per pH unit". Always run `check_response_range`; if more than 5% of values exceed 1.05 or fall below -0.05, the group is flagged `unit_mismatch` and excluded from the library (not silently kept).

**Three units, kept distinct (this matters for the study-effect test):**

| Unit | Definition (default) | Used for |
|---|---|---|
| **Curve** | One pH sweep: rows sharing `Reference` + `Set`/`SetID` (verify, see Task 0.2) and the same mineral, sorbate and electrolyte signature, with near-constant conditions | Slope extraction, the library rows |
| **System** | A (mineral, sorbate) pair, aggregating its curves | Class tests, leave-pair-out |
| **Study** | A `Reference` | Random effect, leave-study-out |

**Task 0.2 is a blocking investigation:** determine what `Set` and `SetID` actually mean in this file (one titration series? one experiment batch?). Print examples. If `Set` does not cleanly identify a single pH sweep, define curves by `(Reference, Mineral, Sorbate, electrolyte signature, Temp, rounded Sorbate_val, rounded solids loading if present)` and document the rule. Do not proceed to Stage 1 until the curve definition is written down in `phslope/README.md` and confirmed by Samuel.

**Known data traps (from earlier work):**
- Ionic strength must come from the corrected `compute_ionic_strength`. `results/data_audit/audit_table.csv` and the PNGs in `Adsorption-simulations-project/` were produced before that fix. Treat them as stale; regenerate. Only pH-based numbers in them were ever valid.
- The sorbate parser once produced a junk label `2)`. Find the cause (probably labels containing parentheses or commas) and fix it at load. Add a test that no sorbate label is shorter than 2 characters or lacks a letter.
- `electrolyte_signature` splits one study into several groups when it adds a tracer ion. For curve building, report the signature but do not use it as a hard grouping key until you have checked what is being split (Task 0.4).
- `Sorbate` and electrolyte labels use **oxidation state in parentheses** (e.g. `U(+6)`, `N(+5)` for nitrate), not ionic charge. Anything that needs a true charge must go through a mapping table, not a regex.
- `Sorbed_val` is an absolute amount; never compare it across studies without normalising (hence the response above).
- Some systems have non-monotone or negative-going curves (U(VI) at high pH with carbonate; anion edges such as Se(IV)). Do not assume a rising sigmoid.
- `n_references` in older audit tables was summed across groups and may double count a paper. Recount from the raw rows.

---

## 3. Package layout

```
phslope/
  README.md                  curve definition, conventions, how to run each stage
  config/
    config.yaml              paths, grid, seeds, QC limits, bootstrap B
    thresholds.yaml          stage pass/fail numbers (frozen before Stage 3)
    classes.yaml             mineral-class and sorbate-class assignments (human-edited)
  load.py                    raw file -> clean observation table (wraps data_audit.prepare_data)
  census.py                  Stage 0: counts, coverage, gap list
  curves.py                  define curves from observations
  fit_edge.py                parametric edge fit (logistic family) + multistart
  fit_smooth.py              penalised-spline fit (flexible check)
  slope.py                   analytic / spline slope on grid, NaN outside observed range
  qc.py                      per-curve quality flags and shape classification
  bootstrap.py               pairs bootstrap for fits and slopes
  library.py                 build / save / load G, meta, uncertainty
  registration.py            align curves (shift/scale) and record the warp
  fpca.py                    functional principal components of aligned curves
  variance.py                mixed-effects variance split + within-study permutation tests
  cluster.py                 clustering + permutation-tested agreement with class labels
  descriptors.py             load/merge descriptor tables, report missingness
  baselines.py               global mean, sorbate-class mean, mineral-class mean, edge-position rule
  transfer.py                Version A (shift/stretch/scale) and Version B (score regression)
  cv.py                      leave-study / pair / mineral / sorbate out, metrics
  synth.py                   synthetic curve generator with planted structure and null controls
  report.py                  figures and tables for each stage
  export.py                  tables for the web interface
data/
  descriptors/
    mineral_descriptors.csv  TEMPLATE, auto-generated, human-filled
    sorbate_descriptors.csv  TEMPLATE, auto-generated, human-filled
tests/phslope/               one test file per module
reports/phslope/             stage outputs (figures, tables, SUMMARY.md)
OPEN_QUESTIONS.md
```

New dependencies (add to `requirements.txt` with pinned versions; check for Python 3.11 compatibility and pin what you actually install): `statsmodels`, `scikit-learn`, `pyyaml`, `pytest`, and `pyarrow` (optional, for parquet; fall back to CSV). Keep `numpy`, `pandas`, `scipy`, `matplotlib` pins as they are unless a conflict forces a change; if so, say so in the commit message.

---

## 4. Method details

### 4.1 Grid
Default pH grid: 2.0 to 11.0 in steps of 0.25 (37 points), set in `config.yaml`. A curve has values only where it has data: grid points outside `[min pH, max pH]` of that curve are `NaN`, never extrapolated. Store a mask alongside G.

### 4.2 Edge fit (default)
Four-parameter logistic, sign-agnostic:

```
A(p) = lo + (hi - lo) / (1 + exp(-(p - p50) / w)),    w > 0
```

- `hi < lo` is allowed (falling edge). Bounds: `p50` within the observed pH range ± 1, `w` between 0.05 and 3, `lo`, `hi` within [-0.1, 1.1] for fraction sorbed.
- Multi-start (at least 20 starts, seeded) with `scipy.optimize.least_squares`; keep the best by residual sum of squares. Fail loudly if every start fails.
- Slope is analytic: `g(p) = (hi - lo) / (4 w)` at the midpoint, general form `(hi-lo) * s * (1 - s) / w` with `s` the logistic.
- Report parameters `(lo, hi, p50, w)`, residual RMSE, and number of points.

### 4.3 Smoother (check, and fallback for non-sigmoid shapes)
Penalised cubic spline with a roughness penalty chosen by leave-one-out cross validation **within the curve**, optional monotone constraint. The slope is the spline derivative. Used when the logistic fit fails QC (bell shapes, two-step edges, carbonate drop-off), and always run alongside the logistic fit for the comparison in Stage 1.

### 4.4 Uncertainty
Pairs bootstrap, B = 200 (config), refit each resample, recompute the slope on the grid. Store the 2.5/50/97.5 percentiles per grid point and the bootstrap spread of `p50`, `w`, `hi - lo`. Count and report bootstrap failures; a curve with more than 20% failures is flagged.

### 4.5 QC flags and shape classes (`qc.py`)
Per-curve flags, all stored in the meta table, none silently dropping data:

| Flag | Rule (defaults, in config) |
|---|---|
| `too_few_points` | fewer than 8 points |
| `narrow_span` | pH span under 3 |
| `edge_not_bracketed` | fitted `p50` is not covered by data on both sides within 0.5 pH |
| `poor_fit` | residual RMSE above 2× the median within-curve replicate scatter (or above a fixed ceiling if no replicates) |
| `wide_interval` | bootstrap 95% width of `p50` above 1.0 pH |
| `unit_mismatch` | response-range check from section 2 |
| `bootstrap_unstable` | more than 20% of resamples failed |

Shape class (assigned from the fitted/smoothed curve): `rising`, `falling`, `flat`, `bell` (rise then fall), `multi_step`, `unclassified`. A curve enters the **core library** only if it has no QC flag and a shape class other than `unclassified`. Report how many curves are lost at each flag.

### 4.6 Registration (`registration.py`)
For rising and falling curves, compute a warp `p -> (p - b) / w_scale` that aligns each curve to a chosen reference, with `b` the edge position and `w_scale` the width ratio. Keep `(a, b, w)` where `a` is the height ratio. Do not discard the warp: it is the main result for Version A. Report what fraction of curve variance is removed by registration alone.

### 4.7 FPCA (`fpca.py`)
Functional principal components on the registered, gap-handled curves (use probabilistic PCA or iterative imputation for missing grid values; state which). Keep the number of components that explains at least 90% of variance, capped at 5. Report scores with uncertainty propagated from the bootstrap where feasible.

### 4.8 Variance split (`variance.py`)
For each of `p50`, `log(w)`, and `hi - lo` (and the first FPCA scores), fit:

```
response ~ 1 + (1 | mineral_class) + (1 | sorbate_class) + (1 | mineral:sorbate) + (1 | reference)
```

via `statsmodels` MixedLM or REML variance components (document the choice; crossed random effects may need the `vc_formula` interface with a single dummy group). Report each component as a share of total variance with a bootstrap or profile interval. Also fit with conditions as fixed effects (`log10` solids loading, `log10` total sorbate, `log10` ionic strength, temperature, carbonate flag) to see how much of the "study" share is explained by conditions.

### 4.9 Class tests (`cluster.py`)
Cluster curves (hierarchical, on FPCA scores and, separately, on edge parameters). Measure agreement with class labels using the adjusted Rand index. Null distribution by **permuting class labels within references**, 2,000 permutations, so that study effects are not mistaken for class effects. Also report PERMANOVA on the same distance matrix, stratified by reference.

### 4.10 Transfer model (`transfer.py`)
- **Version A:** pick a reference curve per class cell (fallback: nearest class with data). Predict `(a, b, w)` from descriptors by a regularised linear model (ridge or elastic net, regularisation chosen by nested leave-study-out). Predicted curve = `a * g_ref((p - b) / w)`.
- **Version B:** predict FPCA scores from descriptors by ridge regression or a random forest; reconstruct the curve.
- Both return prediction intervals (bootstrap over training studies, or conformal on leave-study-out residuals; pick one, document it).
- If a descriptor is missing for a system, that system is dropped from the model that needs it and counted in the report; never mean-imputed without a flag column.

### 4.11 Baselines (`baselines.py`) — all must be implemented and run in the same CV loop
1. **Global mean curve:** the average of all training curves (after the same registration treatment for the registered version).
2. **Sorbate-class mean.**
3. **Mineral-class mean.**
4. **Edge-position rule:** predict only `p50` from PZC and first hydrolysis constant using a fixed regression (fit on training studies), with the reference shape for the class. This is the closest relative of published relationships and is the baseline that decides whether the project says anything new.

---

## 5. Metrics (`cv.py`)

Computed per held-out curve, then summarised (median, IQR, and the full per-curve table sorted worst first):

| Metric | Definition |
|---|---|
| `p50_error` | absolute error of predicted edge position, pH units |
| `curve_error` | root-mean-square difference between predicted and observed slope curves over grid points both have, divided by the observed curve's range, weighted by inverse bootstrap variance |
| `shape_correct` | predicted shape class equals observed |
| `sign_correct` | predicted slope sign equals observed over the edge region |
| `interval_coverage` | fraction of observed values inside the 90% prediction interval (target 0.9) |

Report each model's metrics against each baseline's in the same table, with paired differences and bootstrap intervals over held-out studies (resample studies, not curves).

---

## 6. Synthetic validation (`synth.py`) — build this before touching real data

Generate curves with known truth so each stage can be tested:

1. **Known-edge recovery:** logistic and non-logistic (bell, two-step) curves with noise and uneven pH sampling. Assert the fitters recover `p50` within a tolerance and that bootstrap intervals cover the truth about 90% of the time.
2. **Planted class structure:** edge position depends on mineral class and sorbate class by known amounts, plus a study offset. Assert the variance split recovers the planted shares within tolerance.
3. **Null control:** same curves with class labels randomly reassigned. Assert the class tests do **not** reject (false-positive rate near the nominal level over many replicates).
4. **Planted transfer relationship:** `p50` is a known linear function of two descriptors. Assert Version A beats the baselines on leave-study-out.
5. **Planted null transfer:** `p50` independent of descriptors. Assert Version A does **not** beat the global-mean baseline by more than chance.
6. **Study-effect swamp:** study offsets much larger than class effects. Assert Stage 2 reports "study dominates" and stops the pipeline.

A stage is not allowed to run on real data until its synthetic tests pass.

---

## 7. Stages, tasks, outputs, pass conditions

Each stage writes to `reports/phslope/stageN/` and ends with `SUMMARY.md` that states what was done, the numbers, the pass/fail against `thresholds.yaml`, and the next decision.

### Stage 0 — Census and clean systems table
- 0.1 `load.py`: load the raw file, apply corrected ionic strength, fix the junk-sorbate parse, standardise labels. Test: the four earlier pipeline subsets reproduce their known row counts (goethite–Cl+Na+P–Se(IV) = 104, ferrihydrite–N+Na+P–U = 105, montmorillonite–Cl+Na–U = 66, goethite–N+Na–U = 205).
- 0.2 Investigate `Set` / `SetID` and write the curve definition (section 2). Blocking.
- 0.3 `curves.py`: build curves; report how many, how many points each, pH span, conditions columns present or missing.
- 0.4 Check what the electrolyte-signature split is fragmenting (example: ferrihydrite d01 should come out as one 390-point, six-ionic-strength-level study when nitrate+Na groups are combined). Decide and document whether curve definition ignores tracer ions.
- 0.5 `census.py`: recount from raw rows using the rules in `thresholds.yaml` (default: ≥ 50 points, pH span ≥ 4). Produce: mineral × sorbate matrix of curve counts and independent-reference counts, per-pair table, a **gap list** (empty or thin cells in the dense block), and the same table split by whether solids loading and total sorbate are reported.
- 0.6 Generate `data/descriptors/*_template.csv` listing every mineral and sorbate that appears, with empty descriptor columns.

**Pass:** a clean curves table, and at least 60 mineral–sorbate pairs with ≥ 50 points, pH span ≥ 4 and ≥ 2 independent references. If this fails, report it and stop before Stage 1.

### Stage 1 — Slope curves
- 1.1 Implement `fit_edge.py`, `fit_smooth.py`, `slope.py`, `bootstrap.py`, `qc.py` with the synthetic tests from section 6 (items 1) passing first.
- 1.2 Run on all curves. Produce the library: `G` (curves × grid), mask, lower/upper bounds, meta table (IDs, mineral, sorbate, reference, conditions, fit parameters, QC flags, shape class).
- 1.3 Figures: one diagnostic page per curve (data, logistic fit, smoother, slope with interval), plus summary plots of flag counts and `p50` distribution by sorbate.
- 1.4 Compare logistic vs smoother slopes: report where they disagree by more than the bootstrap spread. These are the curves that are not simple edges.

**Pass:** on synthetic data, slope error under 20% of curve range in the median case; on real data, at least 80% of curves in the census set survive QC with a usable shape class. If shape classes other than `rising`/`falling` exceed 30%, say so and keep the multi-shape handling in scope.

### Stage 2 — Do the classes matter?
- 2.1 Fill `classes.yaml` with the starting classes (mineral: iron oxide/hydroxide, aluminum oxide, silica, clay, carbonate, other; sorbate: divalent/trivalent/tetravalent cation, actinide, oxyanion, organic acid, other). Samuel and Dr. Black confirm. Do not tune the classes on the results.
- 2.2 Registration and FPCA.
- 2.3 Variance split (section 4.8). 2.4 Permutation-tested clustering (section 4.9).
- 2.5 Figures: variance-share bar chart per parameter with intervals; cluster heatmap annotated by class; the mineral × sorbate grid coloured by mean `p50`.

**Pass (go/no-go):** mineral class + sorbate class + their interaction explain clearly more variance than chance (within-reference permutation p < 0.05 for `p50`), and the reference share of variance for `p50` is not larger than the class-plus-interaction share. If not, stop, write the negative result, and recommend whether conditions-as-covariates (not classes) is the next thing to test.

### Stage 3 — Held-out prediction
- 3.1 Fill and verify descriptor tables (human step; report missingness per column).
- 3.2 **Freeze `thresholds.yaml`** and commit it. The Stage 3 entry script checks the working tree and refuses to run if that file is uncommitted or modified after the commit that froze it, and prints the commit hash.
- 3.3 Implement baselines, then Version A and B, then `cv.py`.
- 3.4 Run leave-one-study-out, leave-one-pair-out, leave-one-mineral-out, leave-one-sorbate-out.
- 3.5 Tables and figures: metrics vs baselines, per-curve error sorted worst first, predicted-vs-observed `p50`, the mineral × sorbate grid showing measured cells, predicted cells and held-out error.

**Pass:** Version A or B beats every baseline, including the edge-position rule, on `p50_error` and `curve_error` by the margin in `thresholds.yaml` (proposed starting value: median `p50_error` ≤ 0.5 pH; Dr. Black to confirm), with interval coverage between 0.8 and 0.95. If only `p50` is predictable and curve shape is not, state that as the finding.

### Stage 4 — Transformation model
- 4.1 Compare Version A (few parameters) with Version B.
- 4.2 Which descriptors carry the signal (permutation importance with leave-study-out), sensitivity to the choice of PZC and surface-area source.
- 4.3 Produce a function `predict_slope_curve(mineral, sorbate, conditions) -> (grid, g, lower, upper, notes)` with clear errors when a descriptor is missing or the system is far from the training set (distance warning).

**Pass:** Version A within the margin in `thresholds.yaml` of Version B with far fewer parameters, and the predictor runs end to end on three hand-picked held-out examples.

### Stage 5 — Report
- 5.1 `reports/phslope/FINAL.md`: what worked, what did not, limits, every figure referenced, plain-English section for Dr. Black.
- 5.2 Literature check list (for Samuel, not for you): prior work predicting sorption edges or distribution coefficients from ion and surface properties. Leave placeholders; do not cite from memory.

---

## 8. Descriptor tables

`data/descriptors/mineral_descriptors.csv` (one row per `Mineral`):
`mineral, mineral_class, formula, pzc_low, pzc_high, pzc_source, surface_area_m2_g, surface_area_source, notes`.

`data/descriptors/sorbate_descriptors.csv` (one row per `Sorbate`):
`sorbate, element, oxidation_state, speciation_class (cation / oxyanion / anion / neutral / organic), first_hydrolysis_logK, hydrolysis_source, notes`.

Rules: the loader refuses rows with a value but no source. Missing is allowed and is reported as a table (`reports/phslope/descriptor_missingness.csv`). Run sensitivity analyses over `pzc_low` vs `pzc_high` and over alternative sources once Samuel adds a second source column.

Condition covariates come from the data, not from these files: `Mineralsites`, solids loading (find the column; if it does not exist in this schema, say so in `OPEN_QUESTIONS.md`), `Sorbate_val`, ionic strength, `Temp`, carbonate/CO2 from the `Gas*` columns.

---

## 9. Export for the web interface (`export.py`)

Write plain files so the Streamlit app (see "Web Interface Development Protocol", requirement R9) can read them with no pipeline code:

- `export/curves_meta.csv` — one row per curve: `curve_id, reference, set_id, mineral, sorbate, electrolyte_sig, temp_mean, n_points, pH_min, pH_max, shape_class, qc_flags, p50, p50_lo, p50_hi, width, height, in_core_library`.
- `export/slope_grid.csv` — long format: `curve_id, pH, slope, slope_lo, slope_hi, observed` (observed = inside data range).
- `export/observations.csv` — the points used per curve with the fitted value.
- `export/pair_summary.csv` — one row per (mineral, sorbate): curve count, reference count, mean `p50`, spread, whether predicted and the held-out error if known.

Document the schema in `phslope/README.md`. Changing a column name is a breaking change; add a `schema_version` field.

---

## 10. Work order (PR-sized chunks)

Create branch `ph-slope`. After each item: tests pass, commit.

1. Package skeleton, config, `load.py`, junk-sorbate fix, row-count tests (Stage 0.1).
2. Investigation of `Set`/`SetID` and the curve definition; write it up; **stop and ask Samuel to confirm** if anything is ambiguous (0.2–0.4).
3. `census.py` and the Stage 0 report; descriptor templates (0.5–0.6).
4. `synth.py` items 1–3 and their tests.
5. `fit_edge.py`, `slope.py`, `bootstrap.py`, `qc.py` with synthetic tests.
6. `fit_smooth.py`; run Stage 1 on real data; diagnostics report.
7. `library.py`, `registration.py`, `fpca.py`.
8. `variance.py`, `cluster.py`; Stage 2 report; **go/no-go checkpoint**.
9. `export.py`; hand tables to the web interface track.
10. `descriptors.py`, `baselines.py`, `cv.py`, `transfer.py`; synthetic items 4–5; freeze thresholds; Stage 3.
11. Stage 4 predictor and Stage 5 report.

Estimated schedule (aligned with the 7-week plan): Stages 0–1 about 2 weeks, Stage 2 about 1 week (first checkpoint), Stage 3 about 2 weeks, Stages 4–5 the last 2 weeks.

---

## 11. Definition of done (every stage)

- [ ] Synthetic tests for the stage pass; `pytest` is green; `test_fixes.py` still passes.
- [ ] Real-data run done with a recorded commit hash and config hash.
- [ ] `SUMMARY.md` states numbers, pass/fail against `thresholds.yaml`, and what is uncertain.
- [ ] Per-curve or per-system failures listed, not hidden.
- [ ] Figures saved with axis labels, units and sample sizes.
- [ ] `OPEN_QUESTIONS.md` updated.
- [ ] No descriptor values entered without a source.

---

## 12. Open questions (copy into `OPEN_QUESTIONS.md` at the start)

1. What do `Set` and `SetID` identify? (Task 0.2.)
2. Is there a solids-loading column? If not, can it be recovered from the source papers for the largest pairs?
3. What does "close" mean for Dr. Black: edge position within 0.5 pH, or a whole-curve error? Confirm `thresholds.yaml` before Stage 3.
4. Final class definitions for minerals and sorbates (Dr. Black).
5. Preferred sources for PZC, surface area and first hydrolysis constants.
6. Is the slope library itself, published as a table with uncertainty, a deliverable regardless of Stage 3 outcome?
7. How should conditions be handled: restrict comparisons to similar loadings, or model the dependence?
8. Where is the complete dataset kept for collaborators (Abraham)?

---

## 13. What not to do

- Do not use `audit_table.csv` or the pre-fix PNGs for any number in a report.
- Do not claim novelty. The result is empirical curve-level transfer across a compiled dataset with out-of-study validation. Prior work on edge prediction and linear free-energy relationships exists and must be checked by Samuel before any claim is worded.
- Do not tune class definitions, thresholds or descriptors after seeing Stage 3 results. If they change, record the change and rerun with the new values labelled as exploratory.
- Do not extrapolate slopes outside observed pH ranges.
- Do not report a single average error without the per-curve table.
