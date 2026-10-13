# CLAUDE.md — Response-Surface Fingerprinting of Mineral Sorption Sensitivity

Read this first. It is the handoff from a long claude.ai chat into Claude Code (written 2026-10-11). Sections 0, 2, 3 and 4 were re-checked against the files on 2026-10-12; where the original handoff and the disk disagreed, the disk wins and the difference is noted.

## 0. Verified state on 2026-10-12 (read before trusting anything below)

- **`python test_fixes.py`: 4 PASS, then `test_fingerprint_dominant_axis_is_unit_free` FAILS** (the runner stops at the first failure, so `test_response_normalization` does not run). Cause: `fingerprint.py` on disk is the old 2026-10-05 version (identical to the repo copy). `fingerprint_vector` still reads raw-unit `r["gradient"]` / `r["hessian"]`, not `gradient_scaled` / `hessian_scaled`. The scaled-units fix described in the chat never reached this file.
- Consequence: the per-system fingerprint tables in `results/pipeline_synthetic/SUMMARY.md` and `results/pipeline_real/SUMMARY.md` are headed "scaled units" but were computed in **raw units** (`mean_lambda*`, `std_lambda*`, `frac_pH_dominant`, `mean/std_grad_mag`, `frac_cross_positive` are unit-dependent). The cross-system comparison table uses `compare.py`, which is fixed.
- **Missing from disk** (described in the chat but never saved here or anywhere under `C:\Users\itzju`): `model_based_fit.py`, `compare_numerical_vs_model.py`, `identifiability_probe.py`, and docs `Mathematical_Formulation.md`, `Analysis_Plan.md`, `Data_Audit_Protocol.md`, `Defining_Similarity.md`, `Literature_Review.md`. The §6 numbers from those scripts cannot be reproduced until the scripts are recovered from the chat.
- **The real pipeline has been run** (`results/pipeline_real/`, 2026-10-10 18:16, after the compare/derivatives fixes) on four subsets. Treat it as a first pass, not findings: fingerprints are raw-unit (above), and whether `ONLY_I_VARYING_REFS` filtering was on was not checked.
- `results/data_audit/` holds output from an older audit run (system labels without electrolyte signatures, e.g. `goethite-_-Se__4_`). The newer audit plots with signatures are in `Adsorption-simulations-project/Data_Audit_outputs/`.

## 1. The project in 60 seconds

- **Question:** Treat sorption A(pH, ionic strength I) as a scalar field. Estimate its local gradient and Hessian from real compiled data using local weighted quadratic regression. Test whether that gradient/Hessian field is a mineral- or sorbate-specific "fingerprint" that can be compared across systems.
- **Origin:** extends the user's earlier pH-only derivative work (the "Information Overload" NOVELS poster).
- **Data:** LLNL L-SCIE compiled sorption dataset (**38,906 rows in the file in use, not ~80k; corrected 2026-10-13**;  "Appendix A" schema), at `C:\Users\itzju\sc.dataset.csv` (outside the project folder). Pilot systems: goethite–U(VI), goethite–Se(IV), montmorillonite–U(VI), ferrihydrite–U(VI). NOTE: the active direction is now the pH-only library (`phslope/`, `PH_ONLY_DEV_SPEC.md`, `PH_ONLY_TEST_PROTOCOL.md`); the ionic-strength fingerprint sections below are historical, and the goethite–Se(IV) ionic-strength candidate is superseded (the pooled ionic-strength effect is null).
- **People:** Samuel Uwechue (NSU chemistry undergrad, owner, itzjustsam01@gmail.com); Dr. Suely Black (PI, not a specialist in the field, so anything for her must be plain-English, gen-chem level); Abraham (CS collaborator).
- **Timeline:** 15-week project; the current plan covers the next 7 weeks starting 2026-10-12.
- **Goal now:** the user wants a paper. Realistic framing is a **methods/feasibility paper**, not a mechanistic one (see §7).

## 2. Honest status (do not overstate)

| Item | State |
| --- | --- |
| Pipeline code (scaling → windowing → local fit → derivatives → bandwidth CV → bootstrap → fingerprint → compare → viz) | Built, runs end to end on synthetic data. **`fingerprint.py` lacks the scaled-units fix; 1 of 6 tests fails** (§0) |
| Synthetic validation | Done. Gradients recovered well; ionic-strength curvature is the weakest quantity |
| Numerical vs model-based derivatives | Done on **synthetic data only**. Model-based wins only because the generator uses the same sigmoid. Scripts missing from disk (§0) |
| Real-data run | A first pass on pooled/unnormalized data exposed three comparison artifacts (fixed, tested). A later real-mode run exists in `results/pipeline_real/` but its fingerprints are raw-unit (§0). Not findings |
| Identifiability probe | Done once (see §6). One truth family, 3 seeds, no study offsets, so it is optimistic. Script missing from disk |
| Supplementary data | Candidate papers identified. None obtained or digitized yet |

Never present first-pass real-data results as findings. The apparent dA/dI sign flips from pooled data are probably study effects.

## 3. Repository layout

All code is flat Python at the project root (no package). Run everything from the project root: the modules' `__main__` self-tests read `synthetic_pilot_data.csv` from the working directory.

| Path | Role |
| --- | --- |
| `scaling.py` | `fit_scaler`, `to_scaled`; unit converters `gradient_to_real_units`, `hessian_to_real_units`, `gradient_to_scaled_units`, `hessian_to_scaled_units` (exact inverses) |
| `windowing.py` | `build_kdtree`, `find_candidate_neighbors(query, tree, bandwidth, radius_multiplier=4.0)`, `kernel_weights` (Gaussian, anisotropic bandwidth) |
| `local_fit.py` | `design_matrix`, `fit_weighted_quadratic(Phi, y, weights, max_condition_number=1e8)`, `IllConditionedFitError` |
| `derivatives.py` | `gradient_and_hessian_at_point(query_point, pH_all, I_all, y_all, tree, scaler, bandwidth, min_n_eff=18.0)` returns dict with `gradient`, `hessian` (real units), `gradient_scaled`, `hessian_scaled`, `n_eff`, `valid`, `theta`, `reason`. Also `evaluate_fitted_surrogate`, `finite_difference_cross_check` |
| `bandwidth_selection.py` | `loocv_error(..., max_points=300, seed=0, min_pred_frac=0.6)`, `select_bandwidth(...)` returns `(best, results)`. Brute-force LOOCV (hat-matrix speedup not done) |
| `uncertainty.py` | `bootstrap_gradient_hessian(query_point, pH_all, I_all, y_all, scaler, bandwidth, n_bootstrap=200, ...)` |
| `fingerprint.py` | `compute_field(pH, I, y, scaler, bandwidth, grid_n=15, min_n_eff=18, margin=0.1)`, `fingerprint_vector`. **Currently raw units, unfixed** (§0) |
| `compare.py` | `cosine_similarity`, `hessian_shape_similarity`, `dominant_eigenvector` (by |λ|), `eigenvector_orientation_angle`, `vector_distance(..., min_systems=6)`, `compare_on_shared_grid` |
| `viz.py` | `plot_gradient_quiver`, `plot_slope_slices`, `plot_hessian_heatmaps` (all empty-safe, scaled units) |
| `response.py` | `compute_response(df, mode, ...)` (`fraction_sorbed` or `log_kd`), `check_response_range` |
| `generate_synthetic_dataset.py` | Four systems with closed-form truth: `true_response`, `true_gradient_and_hessian`, `generate_full_dataset(n_per_system=600, noise_frac=0.04, ...)`. Truth: `A = Amax * sigmoid(sign * (pH - pH50 - b*log10 I) / w)`. Writes `synthetic_pilot_data.csv` to the working directory |
| `data_audit.py` | Data-sufficiency audit: per-system point count, pH span, I levels, joint coverage, per-reference I-variation, replicate/temperature/site-density/formula checks, `rank_systems`, `export_pilot_subset`, coverage plots. `CONFIG` and `THRESHOLDS` dicts at top. `SCAN_ALL_SYSTEMS=True` ranks every system. Writes to `results/data_audit/` |
| `run_pipeline.py` | End-to-end driver. Env vars: `PIPELINE_MODE` (`synthetic`/`real`, **default `real`**), `PIPELINE_DATA` (path to real CSV). Writes `results/pipeline_{MODE}/` |
| `test_fixes.py` | 6 regression tests, plain asserts, run with `python test_fixes.py` |
| `synthetic_pilot_data.csv` | Synthetic dataset (copy of the one in `results/pipeline_synthetic/`) |
| `results/pipeline_synthetic/` | Synthetic run outputs (SUMMARY.md, comparison_table.csv, figures). Fingerprint table is raw-unit (§0) |
| `results/pipeline_real/` | Real-mode first pass. Not findings (§0) |
| `results/data_audit/` | Older audit export: pilot subsets and per-reference breakdowns |
| `Adsorption-simulations-project/` | Abraham's GitHub clone (`origin` = github.com/Abr9h9m/...). Older code copies (Sept/early Oct), `Codebase_Documentation.md`, `Surrogate_Module_Spec.md`, `README.md`, stale `TODO.md`, newer audit plots in `Data_Audit_outputs/`. Has 2 uncommitted deletions. Not imported by the root code. Do not commit or push to it without asking |

| `phslope/`, `tests/phslope/`, `reports/phslope/`, `data/descriptors/`, `OPEN_QUESTIONS.md` | pH-only direction, built from `PH_ONLY_DEV_SPEC.md`. Status and decisions in `phslope/README.md`. Branch `ph-slope` |
| `phslope/experiments/`, `reports/phslope/experiments/` | Improvement program from `PH_ONLY_TEST_PROTOCOL.md` (E0-E10, F). **24 papers are LOCKED** (`phslope/config/locked_test_papers.txt`): never load them in development; the locked set is opened once via `integrate.py --open-locked-set`. Status: `reports/phslope/experiments/CHECKPOINT.md` |

Not on disk (§0): `model_based_fit.py`, `compare_numerical_vs_model.py`, `identifiability_probe.py`, `Mathematical_Formulation.md`, `Analysis_Plan.md`, `Data_Audit_Protocol.md`, `Defining_Similarity.md`, `Literature_Review.md`.

Dependencies: numpy, pandas, scipy, matplotlib (`requirements.txt`). `ndarray.ptp()` is gone in new numpy; use `np.ptp`.

## 4. Commands

```
python test_fixes.py                              # 6 tests; currently 1 fails (§0)
python generate_synthetic_dataset.py              # writes synthetic_pilot_data.csv
PIPELINE_MODE=synthetic python run_pipeline.py    # default mode is real
PIPELINE_MODE=real PIPELINE_DATA=C:\Users\itzju\sc.dataset.csv python run_pipeline.py
python data_audit.py                              # CONFIG["DATA_FILE"] already points at the real file
```

## 5. Conventions and traps (learned the hard way)

1. **Hessian convention.** Basis is `[1, dpH, dI, 0.5*dpH², 0.5*dI², dpH*dI]`, so fitted coefficients ARE the Hessian entries. No factor-of-2 correction. An earlier test failed because its ground truth used the other convention.
2. **Always compare in scaled coordinates.** pH spans ~6 units, I spans a very different numeric range, so raw-unit Hessians differ by orders of magnitude and cosine similarity saturates near 1. `compare.py`, dominant-axis fraction and orientation all take scaled inputs.
3. **Dominant eigenvector = largest |λ|**, not most positive eigenvalue. Orientation uses `arctan2(|cross|, |dot|)` (arccos lost precision near 0°).
4. **Signed vs signless shape similarity.** An increasing edge (cation) and a decreasing edge (anion) look like opposite shapes under signed similarity. Report the signless column for geometry independent of sorbate charge.
5. **Normalize the response.** `Sorbed_val` is an absolute amount (~1e-6 mol/L). Use `fraction_sorbed = Sorbed/Sorbate_val` or `log10(Sorbed/Aq)` via `response.py`.
6. **Invalid points stay blank.** Validity requires `n_eff >= 18` (3× the 6 parameters) and a condition-number check. Never fill or guess.
7. **Bandwidth.** LOOCV can pick windows with no 2D coverage and can be biased toward easy points (rejected if <60% predicted). `choose_bandwidth` in `run_pipeline.py` uses least-smoothing-first and returns None when unsupported.
8. **Ionic-strength bug.** Electrolyte labels encode oxidation state, not charge: N(+5)=nitrate (−1), Cl(+7)=perchlorate (−1), S(+6)=sulfate (−2). Handled by `OXIDATION_STATE_TO_TRUE_CHARGE` in `data_audit.py`; C(+4) and P(+5) are approximate.
9. **Pooled ionic-strength coverage is mostly illusory.** It comes from stacking studies that each held I fixed. Real subsets must be single-study, and `ONLY_I_VARYING_REFS=True` with `MIN_I_LEVELS_PER_REF=3`.
10. **Real subset names** in `run_pipeline.py` `REAL_SUBSETS` must match the audit's `(mineral, electrolyte signature, sorbate)` spelling exactly; a missing group prints "NOT FOUND".
11. **Don't use pre-fix outputs.** The old pre-fix `pipeline_outputs/` folder is no longer on disk.

## 6. Results so far

**Identifiability probe** (relative RMSE of scaled derivatives; 1.0 = error as large as signal; N=600, 4% noise, 3 seeds, logistic edge):

| I design | axis | dA/dpH | dA/dI | H_pp | H_II | H_pI |
| --- | --- | --- | --- | --- | --- | --- |
| continuous | lin | 0.13 | 0.33 | 0.40 | 0.85 | 0.56 |
| continuous | log | 0.17 | 0.18 | 0.40 | 1.09 | 0.39 |
| 6 levels | lin | 0.11 | 0.51 | 0.26 | 0.71 | 0.47 |
| 6 levels | log | 0.12 | 0.14 | 0.30 | 2.52 | 0.38 |
| 3 levels | lin | 0.35 | 0.56 | 0.88 | 0.97 | 0.91 |
| 3 levels | log | 0.33 | 0.37 | 0.85 | 0.99 | 0.81 |

Takeaways: gradients recoverable with ≥6 I-levels; cross term only partly; **H_II is not recoverable in any design (mask it)**; log10(I) helps dA/dI; 3 levels is the cliff and is what most single studies have. Caveat: H_II "2.52" for 6-level/log is inflated by a tiny truth magnitude.

**Numerical vs model-based (synthetic, relative RMSE, goethite–U(VI) | montmorillonite–U(VI))**: gradient numerical 0.33 | 0.06, model 0.03 | 0.00; curvature numerical 0.73 | 0.47, model 0.06 | 0.01. Numerical underestimates the peak slope on goethite (~26 vs true ~39) and gets curvature sign wrong near the steepest part.

**Real data:** best candidate is goethite–Se(IV), `Cl(-1)+Na(+1)+P(+5)`, 104 points, 1 study, joint coverage 0.61, audit PASS, but its mineral formula is ambiguous (two formulas). Montmorillonite–U(VI): 66 points, narrow I range (0.001–0.025). Ferrihydrite and goethite–U(VI) subsets have little within-study I variation.

## 7. Paper viability (the user asked for an honest view)

- **Not supported:** "the Hessian fingerprints mineral mechanism". Not enough data, and part of the fingerprint is unidentifiable.
- **Realistic:** methods/feasibility paper: (1) the method; (2) synthetic ground-truth validation and identifiability/data-requirement analysis; (3) a real-data case study with uncertainty; (4) a demonstration that naive pooling creates fake curvature; (5) design guidance for experimentalists.
- **Likely reviewer objection:** "an SCM already predicts this." Reply: fitted mechanisms depend on assumed site density (Hayes 1991, Sposito 1991), so a model-free derivative field is a check that does not inherit those assumptions.
- **Field context:** RSM canonical analysis (within one system), conceptual-DFT Fukui functions (local derivative as cross-species descriptor), Sobol sensitivity, SCM identifiability literature. The Hessian in SCM-fitting papers is of the fitting objective, not of the sorption surface.

## 8. Prioritized work for Claude Code

0. **First:** apply the scaled-units fix to `fingerprint_vector` so `test_fixes.py` passes, then re-run both pipeline modes. Recover the missing scripts/docs (§0) from the claude.ai chat.
1. **Reference-stratified fitting** (per-study offset or random effect). Interface: pH, I, response, study ID. Biggest threat to real-data results.
2. **Null test for the fingerprint.** Permute system labels or shuffle I within a study; show the similarity metrics separate real structure from chance.
3. **Uncertainty-propagated comparison.** Bootstrap the similarity itself; mask components the probe marks unidentifiable (at least H_II).
4. **Full identifiability sweep:** N × noise × I-levels × edge steepness, one heatmap. Extends `identifiability_probe.py`. Central paper figure.
5. **Wrong-model-form test:** generate from a non-sigmoid truth and repeat numerical vs model-based.
6. Speedups: hat-matrix LOOCV; optional GPR with ARD.
7. Carry-overs: resolve goethite–Se(IV) formula ambiguity; run `data_audit.py` with `SCAN_ALL_SYSTEMS=True` on the real file; run the fixed pipeline in real mode on filtered subsets; digitize Missana et al. 2003 (goethite–U(VI), I 0.001–0.1 M), Su & Suarez 2000 (goethite–Se, I 0.01–1 M; selenite shows no I effect), a SWy-2 montmorillonite study, Waite et al. 1994 (ferrihydrite–U) with WebPlotDigitizer into the Appendix A schema; check RES³T database access; one-command reproduction script; sync the root code into Abraham's repo and replace its stale `TODO.md`.

Proposed 7-week schedule (not agreed dates): Samuel re-runs real subsets (Oct 12–18), digitizes papers (Oct 12–Nov 1), real-data numerical vs model (Oct 26–Nov 8), stability and null tests (Nov 2–15), merged comparison (Nov 9–22), paper draft (Nov 16–29). Abraham: per-study fitting (Oct 12–25), identifiability sweep (Oct 19–Nov 8), wrong-model-form test (Oct 26–Nov 8), fast LOOCV (Nov 2–15), bootstrap similarity (Nov 9–22), README/tests (Nov 16–29). PI check-in around Oct 19; data-sufficiency gate Nov 9.

## 9. How to work with this user

- Samuel is learning; explain the why briefly. Abraham is a CS undergrad who will own some modules, so ask before rewriting files whose task plan assigns them to him, and keep existing function signatures stable.
- The user has previously said they wanted to write core functions themselves with the collaborator. When in doubt, propose the design and stub, then implement what they ask for.
- Prefer tests alongside any fix (add to `test_fixes.py` or a new test file). Run `python test_fixes.py` before declaring anything done.
- Be explicit about what was validated on synthetic data versus real data. Say "not run" when something has not been run.
- Anything written for Dr. Black: plain English, no jargon without a gloss.
- Two Claude Docs exist from the prior chat: a paper-viability doc and a project-update-with-7-week-plan doc (links are in the claude.ai chat history; not reproduced here).
