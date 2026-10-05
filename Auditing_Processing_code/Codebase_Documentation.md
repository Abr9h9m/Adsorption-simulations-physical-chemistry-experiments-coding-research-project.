# Codebase Documentation — Current State

Two groups of code exist: **data preparation** (auditing the real dataset, generating a synthetic stand-in) and the **fitting/comparison pipeline** (turning data into gradients, Hessians, fingerprints, and cross-system comparisons). Everything below has been run and tested against real or synthetic data — nothing here is an untested stub.

---

## Part 1: Data Preparation

### `data_audit.py`

Checks whether a candidate (mineral, electrolyte, radionuclide) system has enough data, and the right spread, to support the fitting pipeline. Also exports clean data subsets once systems are chosen.

**Ionic strength & grouping**
- `compute_ionic_strength(df, n_slots)` — computes `I = 0.5·Σcᵢzᵢ²` by parsing ion charges directly out of the `Electrolyte1..N` label values (not column names) and pairing with `ElectrolyteN_val` concentrations. Fully vectorized.
- `electrolyte_signature(df, n_slots)` — builds a canonical, order-independent label for a row's background electrolyte composition (e.g. `"Cl(-1)+Na(+1)"`), used as the categorical grouping key.
- `load_raw_data(filepath)` / `prepare_data(df, config)` — loads CSV/Excel and adds all derived columns (`_pH`, `_ionic_strength`, `_electrolyte_sig`, `_temp`, `_mineralsites`).
- `group_by_system(df, config)` — groups by (mineral, electrolyte signature, sorbate).
- `select_candidate_systems(all_groups, pilot_systems)` — filters to a named pilot list, with `None` as a wildcard per field.

**Audit checks** (each takes a system's subset, returns a dict of metrics)
- `audit_point_count`, `audit_pH_span`, `audit_ionic_strength_levels` (also returns the actual sorted distinct values, not just a count), `audit_joint_coverage` (2D histogram coverage fraction), `audit_missing_invalid`, `audit_replicates_via_set` (uses the dataset's own `Set`/`SetID` design), `audit_study_consistency` (distinct `Reference` count), `audit_temperature_consistency`, `audit_site_density` (flags if `Mineralsites` varies within a system when it should be fixed), `audit_mineral_formula_consistency` (flags ambiguous phase labeling).
- **`reference_breakdown(sub, config, decimals, min_I_levels_for_local_fit=3)`** — the most important check: for each individual `Reference`, counts distinct ionic-strength levels *within that single study*. Returns both a per-reference table and a summary (`n_refs_with_sufficient_I_variation`, `pct_points_in_I_varying_refs`). This is what caught the real problem: pooled coverage across many studies looked fine, but almost no single study varied ionic strength internally.
- `estimate_initial_bandwidth(sub)` — median nearest-neighbor distance in scaled (pH, I) space, via `scipy.spatial.cKDTree`; a rough starting bandwidth guess, later superseded by real cross-validation.
- `verdict_for_system(m, thresholds)` — combines all checks above into PASS/MARGINAL/FAIL with stated reasons.

**Orchestration & output**
- `export_pilot_subset(systems, config)` — writes clean per-system CSVs + one combined CSV (not just summary stats — the actual rows).
- `rank_systems(report)` — sorts by verdict, then by `pct_points_in_I_varying_refs`, then joint coverage, then point count — surfaces the best candidates first.
- `plot_coverage` / `plot_ionic_strength_detail` — log-scale coverage plots and a 3-panel diagnostic (log histogram, strip plot, ECDF) specifically for diagnosing ionic-strength coverage gaps.
- `run_audit(config, thresholds)` — the main entry point; supports both a named pilot list and `SCAN_ALL_SYSTEMS=True` (full-dataset scan with a minimum-size prefilter and capped plotting).
- `_make_synthetic_dataset`, `run_self_test`, `_performance_check` — internal self-tests (confirmed correct on fabricated data; confirmed fast on 80,000 synthetic rows).

### `generate_synthetic_dataset.py`

Builds a clean, schema-matched dataset with a **known, exact ground truth**, for building/testing the fitting pipeline without waiting on better real data.

- `true_response(pH, I, Amax, pH50, b, w, sign, **_)` — closed-form response: a logistic pH-transition whose midpoint shifts with `log10(I)` (a simple stand-in for double-layer screening), guaranteeing a real, nonzero pH×I interaction term.
- `true_gradient_and_hessian(pH, I, params, h=1e-4)` — the exact gradient/Hessian at a point, via fine central differences on the noise-free function (safe here since there's no measurement noise to amplify). This is the ground truth the whole pipeline is validated against.
- `generate_system_data(...)` / `generate_full_dataset(...)` — samples pH broadly and ionic strength log-uniformly and continuously (deliberately *not* replicating the real dataset's clustering problem), adds realistic noise, splits across several synthetic "references" that each internally vary I (unlike the real pooled-study issue), and fills every Appendix-A schema column.
- `SYSTEM_PARAMS` — the four pilot systems' model parameters, chosen so goethite/ferrihydrite show a sharp pH-increasing edge, Se(IV) shows a decreasing edge, and montmorillonite shows a weak, diffuse response — matching known literature contrasts.

---

## Part 2: Fitting & Comparison Pipeline

**Pipeline order:** `scaling.py` → `windowing.py` → `local_fit.py` → `derivatives.py` → (`bandwidth_selection.py`, `uncertainty.py`) → `fingerprint.py` → `compare.py` → `viz.py`

### `scaling.py`
- `fit_scaler(pH_all, I_all) -> dict` — min/max per dimension, from the full dataset.
- `to_scaled(pH, I, scaler) -> (pH_scaled, I_scaled)` — rescales both to [0,1].
- `gradient_to_real_units(grad_scaled, scaler)` / `hessian_to_real_units(hess_scaled, scaler)` — converts derivatives back to real units via the chain rule (necessary because pH and ionic strength are on wildly different numeric scales — fitting on raw units is numerically unstable).

### `windowing.py`
- `build_kdtree(pH_scaled, I_scaled) -> cKDTree` — built once per system, reused per query.
- `find_candidate_neighbors(query_point_scaled, tree, bandwidth, radius_multiplier=4.0)` — cheap geometric prefilter: a hard cutoff at `radius_multiplier × bandwidth`, since points farther away contribute ~0 weight anyway.
- `kernel_weights(query_point_scaled, neighbor_points_scaled, bandwidth)` — the actual Gaussian kernel weight, computed only on the prefiltered candidates.

### `local_fit.py`
- `design_matrix(delta_pH, delta_I)` — builds the 6-column basis `[1, dpH, dI, 0.5·dpH², 0.5·dI², dpH·dI]`. The `0.5` factor is deliberate: it makes the fitted coefficients equal the Hessian entries directly, with no factor-of-2 correction needed afterward (a confirmed, tested convention — see the validation test in this file).
- **`class IllConditionedFitError(Exception)`** — raised instead of silently returning a bad fit.
- `fit_weighted_quadratic(Phi, y, weights, max_condition_number=1e8)` — weighted least squares via `sqrt(weight)` row-scaling + `np.linalg.lstsq` (more stable than forming normal equations directly). Checks the design matrix's condition number first and raises `IllConditionedFitError` if the local neighborhood is too degenerate (e.g., near-collinear points) to trust.

### `derivatives.py` — the orchestration layer
- `gradient_and_hessian_at_point(query_point, pH_all, I_all, y_all, tree, scaler, bandwidth, min_n_eff=18.0) -> dict` — ties scaling → windowing → local_fit together. Returns `{"gradient", "hessian", "n_eff", "valid", "theta", "reason"}`. Returns `valid=False` with a stated reason (not a guess) if the effective sample size is too low or the fit is ill-conditioned — this is the direct, tested fix for the "sparse-data spike" artifact seen in last semester's single-variable work.
- `evaluate_fitted_surrogate(theta, delta_pH, delta_I)` — evaluates the already-fitted local quadratic directly from its coefficients (no refitting).
- `finite_difference_cross_check(theta, step=1e-4) -> dict` — an independent correctness check: central-differences `evaluate_fitted_surrogate` and confirms it agrees with the direct `theta` readout to ~6 decimal places. **Confirmed passing.** (An earlier version of this incorrectly refit the model at shifted points instead of evaluating the existing fit — fixed.)

### `bandwidth_selection.py`
- `loocv_error(pH_all, I_all, y_all, scaler, bandwidth, max_points=300, seed=0)` — brute-force leave-one-out cross-validation error for a candidate bandwidth (subsampled for speed on large datasets).
- `select_bandwidth(pH_all, I_all, y_all, scaler, candidate_bandwidths, max_points=300)` — tries each candidate, returns the best. **Confirmed on the synthetic goethite–U(VI) system:** `(0.1, 0.1)` — the placeholder value used throughout earlier development — was already near-optimal among the candidates tested.

### `uncertainty.py`
- `bootstrap_gradient_hessian(query_point, pH_all, I_all, y_all, scaler, bandwidth, n_bootstrap=200, min_n_eff=18.0, seed=0)` — resamples the data with replacement `n_bootstrap` times, refits at the same point each time, reports the point estimate alongside the bootstrap mean/std for the gradient and the three unique Hessian entries, plus the fraction of resamples that produced a valid fit. **Confirmed working:** on the synthetic data, gradient estimates were tight (std ≈ 2% of the value) while the `H_I,I` Hessian term showed proportionally much wider uncertainty — a concrete, quantified example of why second derivatives need more data to pin down than first derivatives.

### `fingerprint.py`
- `compute_field(pH_all, I_all, y_all, scaler, bandwidth, grid_n=15, min_n_eff=18.0, margin=0.1)` — evaluates gradient/Hessian across a grid spanning the data's extent (shrunk inward by `margin` to avoid edge bias), keeping only points that pass the validity check. Returns the valid grid coordinates and their results.
- `fingerprint_vector(points, results)` — compresses a computed field into the 8-element vector from the math spec: mean/std gradient magnitude, mean/std of both principal curvatures (`λ₁, λ₂`), fraction of the domain with a positive pH×I cross-term, and fraction of the domain where pH dominates over ionic strength. **Confirmed working** on all three synthetic test systems, producing visibly different vectors (e.g., montmorillonite's gradient magnitude ~6× smaller than goethite's, matching its "weak, diffuse" design).

### `compare.py`
- `cosine_similarity(v1, v2)` — standard cosine similarity.
- `hessian_shape_similarity(hess1, hess2)` — cosine similarity between flattened `[Hpp, Hii, Hpi]` vectors — compares curvature *shape*, independent of magnitude.
- `eigenvector_orientation_angle(hess1, hess2)` — angle (degrees) between two Hessians' dominant eigenvectors, using `|v1·v2|` to correctly handle the sign ambiguity (an eigenvector and its negative are the same direction).
- `vector_distance(phi1, phi2, feature_means=None, feature_stds=None)` — Euclidean distance between two compressed fingerprint vectors, optionally z-scored first. **Known caveat, confirmed in testing:** the demo script calls this *without* z-scoring, which lets montmorillonite's much smaller raw magnitudes distort the comparison — this is exactly why the math spec requires z-scoring before any real comparison; not yet wired into the demo.
- `compare_on_shared_grid(points1, results1, points2, results2, match_tolerance=0.5)` — Tier 2 comparison: for each point in system 1 with a close match in system 2, computes both similarity measures above. **Confirmed working** across all three synthetic systems.

### `viz.py`
- `plot_gradient_quiver(points, results, title, save_path)` — arrow map of gradient direction/magnitude.
- `plot_slope_slices(pH_all, I_all, y_all, scaler, bandwidth, fit_fn, tree, I_levels=None, pH_range=None, n_points=30, title, save_path)` — overlaid `dA/dpH` vs. pH curves at a few fixed ionic-strength levels, the direct visual for a pH×I interaction.
- `plot_hessian_heatmaps(points, results, title, save_path)` — three side-by-side heatmaps for `H_pH,pH`, `H_I,I`, `H_pH,I`. **All three confirmed rendering correctly** on synthetic data.

---

## What's genuinely not built yet

- A formal sweep confirming error shrinks as sample size grows and noise shrinks (the full Week-5 validation gate — individual-point validation has been done, the systematic sweep has not)
- The hat-matrix/linear-smoother speedup for `loocv_error` (brute-force version works and is what's tested; this is a deferred optimization, not a correctness gap)
- Z-scoring wired into the `compare.py` demo (the function supports it; the test script doesn't use it yet)
- Anything requiring real supplementary data (the goethite–Se(IV) mineral-formula issue, and the literature-sourced data extraction) — blocked on manual steps outside this codebase
