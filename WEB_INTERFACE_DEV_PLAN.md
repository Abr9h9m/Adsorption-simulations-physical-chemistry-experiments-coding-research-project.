# WEB_INTERFACE_DEV_PLAN.md: granular development plan for the curve-library web interface

Written 2026-10-14 from a read of the repository (`curvelib/`, `packs/sorption/`, `tests/curvelib/`, `phslope/`, `reports/phslope/experiments/CHECKPOINT.md`). Audience: Abraham (lead developer) and Claude Code. Owner of the chemistry and analysis: Samuel. PI: Dr. Suely Black (not a field specialist; anything she sees must be plain English).

`WEB_INTERFACE_PROTOCOL.md` is the requirements document (R1–R22, section 3b–3f layouts). This file is the work plan: what exists today, what is missing, and the tasks, tests and gates for each week. Everything shown to users is EXPLORATORY until the locked test set has been evaluated.

---

## 1. What we are trying to do

Build a web interface to the LLNL L-SCIE compiled sorption database (`sc.dataset.csv`, 38,906 rows, 82 columns) with four views:

1. **Periodic-table front page.** Elements coloured by how much sorbate data exists; click to select.
2. **Query.** Choose oxidation states, then minerals, then any combination of facets (year, ionic strength, pH, solids, loading regime, atmosphere, paper, curve direction, quality flags). Counts update live; the selection is a shareable URL.
3. **Plot and fit.** Choose x and y, colour and symbol, log or linear; optionally fit a curve (several model types) and see n, papers, R², RMSE, parameters and paper-level intervals.
4. **Hover and click.** Every point shows its source (paper code, material, conditions, flags) and links to the paper's other curves.

The interface must also be **modular** (Dr. Black's requirement): sorption-specific logic lives in a plug-in "pack"; the engine and front end know only roles such as group, sweep axis, value, cluster. The proof is a second, non-sorption dataset loaded by writing only a manifest (milestone M7).

**Done means (sign-off, target Dec 20):** all four views work on the real data; every number shown equals the analysis code's number (golden tests); every page shows status, schema version and data version; a second dataset loads with zero engine or front-end edits; Dr. Black can run a query, a plot and a fit without help.

---

## 2. What exists today (verified in the repo, 2026-10-14)

### 2.1 Code inventory

| Piece | File | Lines | What it does |
|---|---|---|---|
| Manifest schema and validator | `curvelib/manifest.py` | 119 | JSON Schema for dataset manifests; roles `group_a, group_b, cluster, series, sweep_x, value, covariate, label`; conversions must be declared, never inferred; all problems listed together |
| Generic engine | `curvelib/engine.py` | 134 | `load_rows` (unit conversions, pack-derived columns), `account_rows` (every row in exactly one status bucket), `build_curves`, `coverage`, `sweep`, `run` |
| API | `curvelib/api.py` | 182 | FastAPI, read-only. Endpoints: `/api/meta`, `/api/accounting`, `/api/coverage`, `/api/sweep`, `/api/entities`, `/api/curves`, `/api/points`, `/api/fit` (logistic, paper-resampled intervals, pooling warning), `/api/predict`. Every response has `status`, `schema_version`, `data_version` (hash) |
| Front end | `curvelib/web/index.html` | ~230 | One static page, tabs Elements / Coverage / Curves / Predict; Plotly 2.27 loaded from cdnjs; status banner; phone-width CSS |
| Sorption pack | `packs/sorption/pack.py`, `manifest.yaml`, `entities.py`, `sorbate_map.csv` | – | Ionic strength, electrolyte signature, fraction sorbed, log Kd (reuse analysis code); periodic-table counts; sorbate map (57 rows, parsed or `needs_review`); `predict` hook calls `phslope.predictor` |
| Tests | `tests/curvelib/test_engine.py` (7), `test_api.py` (9) | – | Invalid manifests rejected; row accounting reconciles; a non-sorption dataset with spaces and accents in column names round-trips; census parity on the real file. I did **not** re-run them (no pytest in the device shell); Abraham records the pass count in M0 |

Run it: `python -m curvelib.api`, open http://127.0.0.1:8000. Dependencies are already pinned in `requirements.txt` (`fastapi==0.143.0`, `uvicorn==0.54.0`, `httpx==0.28.1`, `jsonschema==4.25.0`, `PyYAML`, `pandas==2.2.3`).

### 2.2 Verified numbers (P1 census gate, passes exactly per `curvelib/README.md`)

38,906 rows → 1,704 sweep curves → 1,680 clean → 277 mineral–sorbate pairs → 76 pass (`pair_coverage`: at least 50 points, 2 papers, 4 pH units of span). Counts equal `reports/phslope/stage0/pair_table.csv` for every pair.

### 2.3 Requirement status (R-numbers from the protocol)

| R | Requirement | Status | Evidence / gap |
|---|---|---|---|
| R1 | Load any manifest-conformant CSV | Done | `engine.run`; arbitrary-column test |
| R2 | Coverage heatmap, thresholds | Done | Coverage tab, `/api/coverage` |
| R3 | Threshold sweep slider with live counts | Partial | `/api/sweep` exists; confirm the UI uses it, add live count text |
| R4 | Curve viewer with uncertainty | Partial | Points per paper and a logistic fit with parameter intervals; no fitted band, no residual toggle |
| R5 | Query builder on any column | Not started | Only element → mineral picking |
| R6 | Library view of pair summaries | Not started | `export/pair_summary.csv` (277 rows) not shown |
| R7 | Status and schema on every page | Done | Banner shows status, schema v, data hash, row count |
| R8 | Paper-level uncertainty; flag single-paper pairs | Partial | Fit intervals resample whole papers; single-paper flag not shown everywhere |
| R9 | Flags visible and filterable | Not started | Flags exist in `curves_meta.csv` (`qc_flags`, `shape_class`, `in_core_library`), not in the API |
| R10 | Export of filtered view | Not started | |
| R11 | Pack mechanism | Done | Hooks `entity_picker`, `predict`; `derived_by: pack.<name>.<fn>` |
| R12 | Accessible, phone width | Partial | Media query and focus outlines exist; no screenshot or keyboard test |
| R13 | Periodic-table front page | Done (v0) | Elements tab; other sorbates panel; counts table |
| R14 | Oxidation-state selection | Partial | States are listed as text after clicking an element; no selector |
| R15 | Faceted query with live counts | Not started | |
| R16 | Colour-by metric switch | Done (v0) | `PICK.metrics` |
| R17 | Plot builder (choose axes) | Not started | Axes fixed: pH vs fraction sorbed |
| R18 | Fit tool, several models | Partial | Logistic only (`model != "logistic"` is refused) |
| R19 | Hover and click provenance | Partial | Hover text shows a few fields (`index.html` line ~178); no click-to-pin panel, no "other curves from this paper" |
| R20 | Pooled-fit warning and paper-level intervals | Done | `POOL_WARNING`, whole-paper resampling, 100 draws |
| R21 | Shareable URL state, saved queries | Not started | |
| R22 | Pluggable entity picker | Done | `entity_picker` hook; list fallback |

### 2.4 What the data does and does not contain (E0 inventory, `reports/phslope/experiments/E0/`)

Present: `Reference` (paper code, e.g. `azzbn01`), `Set` (one plotted series), `Mineral`, `Mineral_formula`, `Mineral_source` (85% present), `MineralSA` + units (m²/g, 85%), `Mineralsites` (sites/nm²), `Mineral_val` + units (solids), `Temp`, `pH` and `pH_SD`, `Sorbed_*`, `Aq_*`, `Sorbate_*` with SDs, electrolytes 1–7 with SDs, `Gas1–3` with partial pressures in bar, `SurfCharge`, `CEC`.
**Absent:** authors, title, journal, DOI, year, equilibration time, aging, separation method, container, pH method. So the hover tooltip can show the paper code but not a citation. **Year** can only be derived from the two-digit suffix of the reference code (examples seen: `azzbn01`, `jhlch99`, `BB06`, `t83`, `b68`). Proposed rule, needing Samuel's confirmation: suffix 00–25 → 2000s, 26–99 → 1900s; label every such value "year (derived from reference code)".

### 2.5 Analysis assets the interface can use (all exploratory)

- `export/` (schema v1, status "exploratory: Stage 1 core-survival rule not met (46.8% < 80%)"): `curves_meta.csv` (1,680 rows; columns include `shape_class`, `qc_flags`, `p50`, `p50_lo`, `p50_hi`, `width`, `height`, `in_core_library`), `observations.csv` (23,405 rows with fitted values), `pair_summary.csv` (277), `slope_grid.csv` (62,160).
- Per-curve data flags and lineage clusters: `reports/phslope/experiments/E3/data_flags.csv`, `lineage_clusters.csv`, `duplicate_pairs.csv` (28 cross-paper near-copies; 17 papers in lineage clusters; 62 curves queued for human review in `outlier_review.csv`).
- Atmosphere classes from the gas columns (E0/E7: air-equilibrated 750, CO2-free 515, unknown 114, controlled CO2 18 on development curves); `has_cosolute` and `co2_present` flags in `phslope/curves.py`.
- Loading regimes from `reports/phslope/followup/solids_loading_tables.zip` (`B_curve_regimes.csv`: 320 low, 141 transition, 78 high). The breakpoint is poorly located, so the UI label must say so.
- Predictor: `phslope/predictor.py::predict_slope_curve` (development-paper model with distance warnings). The CHECKPOINT notes gradient boosting beat the mixed model on grouped validation; **switching the predictor to it waits until after the locked-set evaluation**, so do not rebuild the Predict tab around it yet.

### 2.6 Results that constrain the interface

| Finding (CHECKPOINT.md, exploratory) | Required interface behaviour |
|---|---|
| Which paper a curve comes from dominates the scatter; pooling widens edges ~1.4× | Colour by paper by default; pooled-fit warning (exists); paper-level intervals only |
| 28 curves appear in two papers; copies inflate agreement | Show a "possible copy" flag from `duplicate_pairs.csv`; treat lineage-linked papers as one source in paper counts shown next to fits |
| Fraction sorbed is not corrected for solids; effect differs by anions and cations | Show solids on every curve; offer log K and per-gram Kd presets with "reported Aq" vs "assumed mass balance" flag (E0: 99.9% of rows consistent, but this likely means the compilers derived one value from the other) |
| High loading lowers binding; breakpoint uncertain | Loading-regime facet and badge, labelled exploratory |
| Salt effect depends on sorbate type (E8: outer-sphere +0.79 pH per decade; oxyanions −0.30; overall null robust in 97% of specifications) | Ionic strength is a facet; do not imply a universal effect |
| New mineral or new sorbate predictions are no better than class means (1.5 / 1.8 pH) | Predict tab must show distance warnings and "no better than class mean" text for unseen systems |
| Locked set (24 papers) not opened | No page may show model skill on locked papers; any held-out error column must come from development papers only (`pair_summary.csv` `heldout_p50_error` must be checked before display) |

---

## 3. Data contract for the new features

### 3.1 Derived columns to add (all in `packs/sorption/pack.py`, none in the engine)

| Column | Source | Notes |
|---|---|---|
| `year` | Reference code suffix | Rule above; `year_source = "derived from reference code"` |
| `oxidation_state`, `element` | `sorbate_map.csv` | 57 rows; `needs_review` rows (organics, `Pu` without state, `COM`) stay visible in "Other sorbates" |
| `direction` | `curves_meta.shape_class` (rising, falling, bell, …) | Join on curve ID |
| `loading_mol_per_g`, `loading_regime` | total sorbate (mol/L) ÷ solids (g/L); thresholds in pack config from `SOLIDS_AND_LOADING.md` | Mark "exploratory" |
| `atmosphere_class` | gas columns, code in `phslope/experiments/data.py::_atmosphere` | Reuse, do not re-implement |
| `has_cosolute`, `co2_present` | `phslope/curves.py` | Reuse |
| `log_k`, `log_kd_per_g` | `phslope/experiments/kd.py` | Reuse; carry `aq_source` ∈ {reported, mass_balance} |
| `lineage_id`, `possible_copy` | E3 outputs | Join on reference |
| `quality_flags` | `curves_meta.qc_flags`, E3 `data_flags.csv` | Show, never drop |

Rule: the pack imports analysis code; the analysis code never imports the pack. If a function is needed by both, it lives in `phslope`.

### 3.2 API additions (proposed; Abraham may rename)

| Endpoint | Purpose | Key parameters | Returns |
|---|---|---|---|
| `GET /api/facets` | Facet definitions and live counts for the current selection | `select` (see grammar below) | per facet: type (range/list), values or min/max, counts |
| `GET /api/query` | Counts for a selection | `select` | points, curves, papers, pairs; why-empty explanation |
| `GET /api/points` (extend) | Points with chosen columns | `curve_id[]`, `x`, `y`, `color`, `columns[]` | one record per point with every requested column and provenance fields |
| `GET /api/fit` (extend) | Fit with model choice | `model` ∈ logistic, logk_line, linear, loess, poly2, poly3; `window`; `include_paper[]` | params, intervals, n, papers, R² (state space), RMSE, window, excluded points and reasons, warnings |
| `GET /api/library` | Pair summary view | `select` | rows from `pair_summary` plus counts, single-paper flag |
| `GET /api/export` | Download | `select`, `format` | CSV or JSON with the query, fit settings and data version in a header block |

**URL grammar** (one string, stable, human-readable): `?el=U&ox=6&min=goethite,ferrihydrite&year=1990-2010&I=0.01-0.1&pH=3-9&regime=low,transition&dir=rising&x=pH&y=log_k&color=paper&fit=logk_line`. Unknown keys are ignored with a visible notice.

### 3.3 Rules that apply to every task

1. No sorption words in `curvelib/` (a test greps for them: element symbols aside, words such as pH, sorbate, mineral, goethite must not appear in `engine.py`, `manifest.py`, or `api.py`; the current files use `group_a/group_b`).
2. A fit never runs on fewer than 4 distinct points (already enforced).
3. Missing is shown as missing, never zero; fields absent from the dataset are omitted.
4. Numbers equal the analysis numbers: golden tests against `phslope` on frozen curves.
5. Every response and every page carries status, schema version and data version.

---

## 4. Milestones, tasks, gates

Weeks start on Mondays; today is Wed Oct 14. Thanksgiving week (Nov 23–29) is planned light. Owners: A = Abraham, S = Samuel, C = Claude Code (working for either). Estimates are working days.

### M0 · Oct 14–18 · Review and decisions

| ID | Task | Owner | Acceptance |
|---|---|---|---|
| M0.1 | Run v0 locally; click through all four tabs; record screenshots and the pass count of `python -m pytest tests/curvelib` | A | A short `docs/web/V0_REVIEW.md` with screenshots and a list of defects |
| M0.2 | Read `curvelib/*.py`, `packs/sorption/*`, `WEB_INTERFACE_PROTOCOL.md`; write down unclear points | A | Questions sent to Samuel |
| M0.3 | Decide stack: keep FastAPI + static page (recommended; already working) or move to a framework | A | Written in `OPEN_QUESTIONS.md` |
| M0.4 | Decide plot library: keep Plotly (scattergl handles ~40,000 points) or replace; bundle it locally rather than load from cdnjs | A | Decision plus a task in M6 |
| M0.5 | Confirm the year-from-reference-code rule and the "derived" label | S | Answer in `OPEN_QUESTIONS.md` |
| M0.6 | Copy `sc.dataset.csv` to Abraham; confirm L-SCIE release/date if known; check licence and citation wording | S | File delivered; citation text agreed |
| M0.7 | Check L-SCIE for publication metadata (authors, DOI) held elsewhere | S | Yes/no; if yes, a table keyed by `Reference` |

**Gate M0:** decisions M0.3–M0.5 written; v0 review exists; Abraham can run the app and the tests.

### M1 · Oct 19–25 · Facet data layer

| ID | Task | Files | Acceptance test | Owner | Days |
|---|---|---|---|---|---|
| M1.1 | Pack derived columns from section 3.1 (year, element, oxidation state, direction, loading, regime, atmosphere, flags, lineage) | `packs/sorption/pack.py`, manifest `derived_by` entries | Each column's non-missing count printed and checked against its source (for example `direction` non-missing = 1,680) | A+C | 3 |
| M1.2 | Engine: generic `facets(rows, curves, manifest)` returning types and counts for any `covariate`/`label` column | `curvelib/engine.py` | Property test: random facet combinations give counts identical to a plain pandas filter (200 random cases) | A | 2 |
| M1.3 | `/api/facets`, `/api/query` with why-empty explanation | `curvelib/api.py` | Selecting a facet value with zero rows names the facet that removed the last rows | A | 1 |
| M1.4 | Verify `heldout_p50_error` in `pair_summary.csv` uses development papers only; if not, drop the column from anything exposed | `phslope/export.py` check | Written note in `OPEN_QUESTIONS.md` | S | 0.5 |

**Gate M1:** `/api/facets` counts equal a direct dataframe filter on the real file; engine still contains no sorption words (grep test).

### M2 · Oct 26–Nov 1 · Query UI and URL state

| ID | Task | Acceptance | Owner | Days |
|---|---|---|---|---|
| M2.1 | Oxidation-state selector after element click (R14), with counts and "needs review" sorbates under Other | Selecting U shows U(+6), U(+4) (whatever the map holds) with counts that sum to the element total | A | 1 |
| M2.2 | Mineral list with counts and class grouping, searchable | Counts equal `/api/coverage` | A | 1 |
| M2.3 | Facet panel (R15): range sliders (year, ionic strength, pH, solids), checkbox lists (regime, atmosphere, direction, flags), paper search | Moving a slider updates counts in under 300 ms on the full file | A | 2 |
| M2.4 | Selection summary: points, curves, papers, pairs, single-paper pairs flagged; mini coverage heatmap for the selection | Matches `/api/query` | A | 1 |
| M2.5 | URL state (R21): selection and plot settings round-trip; copy-link button; saved queries in browser storage (try/catch) | Opening a copied URL in a fresh tab reproduces the same counts | A | 1 |
| M2.6 | Periodic table keyboard and non-colour access (counts in cells, table view toggle) | Tab order covers every element with data; screen-reader labels include the count | A | 1 |

**Gate M2 / Demo 1 (Nov 1):** "click uranium, choose U(VI), choose goethite, restrict to ionic strength 0.01–0.1 and pH 3–9, copy the link, open it in a new tab: same counts." Show Dr. Black.

### M3 · Nov 2–8 · Plot builder and fits

| ID | Task | Acceptance | Owner | Days |
|---|---|---|---|---|
| M3.1 | Extend `/api/points` to return any requested columns and derived columns (`log_k`, `log_kd_per_g`, loading) with `aq_source` | Values equal `phslope/experiments/kd.py` on 100 random points (tolerance 1e-9) | A+C | 2 |
| M3.2 | Axis, scale, colour and symbol controls (R17); presets: fraction vs pH, log K vs pH, log Kd vs pH, edge vs covariate | Every numeric column selectable; log axis refuses non-positive values with a message | A | 2 |
| M3.3 | Fit models (R18): logistic (exists), **log K line** (reuse the E1 per-curve line), linear, LOESS-type smooth, polynomial degree 2 and 3 | Each model's parameters equal the `phslope` function on 5 frozen curves (tolerance 1e-6); no fit under 4 points | A+C | 3 |
| M3.4 | Fit statistics panel: n, papers, R² (say which space), RMSE, parameters with paper-level intervals, fitted window, excluded points and reasons; residual plot toggle; fitted band | Matches API values; extrapolation beyond measured pH flagged | A | 1 |
| M3.5 | Per-paper fit by default, pooled on request with the existing warning; include or exclude papers by checkbox | Pooled fit shows `POOL_WARNING` text | A | 1 |
| M3.6 | Golden-test file `tests/curvelib/test_fit_parity.py` | 5 curves × 6 models pass in CI | A | 1 |

**Gate M3:** fit parity tests pass; no fit offered under 4 points; pooled warning visible.

### M4 · Nov 9–15 · Hover, click, data table, speed

| ID | Task | Acceptance | Owner | Days |
|---|---|---|---|---|
| M4.1 | Provenance tooltip: Reference, Set, year (derived), Mineral and formula, source, surface area, Sorbate (element, state), pH, response, reported Sorbed/Aq with SDs where present, solids, loading and regime, ionic strength and electrolytes, Temp, gas, flags, `aq_source`, lineage, `possible_copy` | Every tooltip field maps to a column in section 2.4 or 3.1; missing fields omitted | A | 2 |
| M4.2 | Click to pin a detail panel; "other curves from this paper in this pair"; "other papers for this pair" | Links change the selection and URL | A | 1 |
| M4.3 | Sortable data table of the selection, paged; row click highlights the point | 40,000 rows render without freezing (virtualised) | A | 1 |
| M4.4 | Performance: WebGL scatter above 5,000 points; nearest-point lookup | Hover latency under 100 ms at 38,906 points (measured, recorded) | A | 1 |
| M4.5 | "Possible copy" and "needs review" badges from E3 | Badge count equals 28 pairs / 62 curves in `E3` outputs | A+C | 1 |

**Gate M4:** latency number recorded; tooltips show only fields present.

### M5 · Nov 16–22 · Library view and export

| ID | Task | Acceptance | Owner | Days |
|---|---|---|---|---|
| M5.1 | `/api/library` and a library table: pair, curves, papers, edge (p50) with paper-level interval, width, height, single-paper flag, QC flags | 277 rows; matches `export/pair_summary.csv` (and curves_meta) | A | 2 |
| M5.2 | Export (R10): CSV and JSON of the current selection with a header block listing query URL, fit settings, data version, schema version and status | Re-import test: counts equal | A | 1 |
| M5.3 | Plot export PNG and SVG | File opens; contains title and status line | A | 1 |
| M5.4 | Predict tab: keep the Stage 4 model; add plain-English warnings (distance, "no better than class mean for unseen systems"); do not rebuild on gradient boosting until the locked look is done | Warnings appear for an unseen mineral or sorbate | A+S | 1 |
| M5.5 | Schema v2 placeholder: how new analysis columns (slope in log K space, regime label, lineage cluster) will be added without breaking v1 readers | One-page note | S | 0.5 |

**Gate M5 / Demo 2 (Nov 22):** library, export and Predict warnings shown to Dr. Black.

### M6 · Nov 23–29 · Hardening (light week)

| ID | Task | Acceptance | Owner |
|---|---|---|---|
| M6.1 | Bundle Plotly (and any fonts) locally; no CDN calls | App works with the network off | A |
| M6.2 | Accessibility: keyboard path through all views, labels, colour-independent cues | Manual checklist in `docs/web/A11Y.md` | A |
| M6.3 | Phone-width layout; screenshots at 390 px and 1280 px | Committed to `docs/web/screens/` | A |
| M6.4 | Error and empty states (API down, zero rows, unfittable selection) | Each has a message that says what to do | A |

### M7 · Nov 30–Dec 6 · Modularity proof

| ID | Task | Acceptance | Owner |
|---|---|---|---|
| M7.1 | Pick a non-sorption dataset: any curves of y against x, grouped, with a cluster id (a study or source). Check its licence | Chosen and recorded | S+A |
| M7.2 | Write `packs/<new>/manifest.yaml` and, only if needed, a small pack | Loads with `python -m curvelib.api` using `CURVELIB_MANIFEST`/`CURVELIB_DATA` | A |
| M7.3 | Run all four views on it | **Zero edits** under `curvelib/` | A |
| M7.4 | If edits were needed: fix the abstraction, list what leaked, add a regression test | Written note | A |

**Gate M7:** zero engine or front-end changes for the second dataset. If not met, the release is delayed, not the criterion.

### M8 · Dec 7–13 · Documentation, deployment, buffer

| ID | Task | Acceptance |
|---|---|---|
| M8.1 | README for users and for developers; manifest guide with two worked examples | Someone else can add a dataset from the guide |
| M8.2 | Deployment (host decided in M0; data-serving permission checked) | URL reachable by Dr. Black |
| M8.3 | Predictor switch to gradient boosting **only if** the locked-set evaluation is finished by then; otherwise leave the development model and say so on the Predict tab | Decision recorded |
| M8.4 | Buffer for slipped items (cut order: saved queries, SVG export, per-gram Kd preset) | – |

### M9 · Dec 14–20 · Sign-off

Sign-off session with Dr. Black on both datasets. Pass if she can, unaided: pick an element, filter by mineral and ionic strength, plot log K vs pH, fit a curve per paper, hover a point to find its paper, and export the selection. Never cut the golden tests, the paper-level warnings or the second-dataset test.

---

## 5. Test plan (new test files)

| File | Tests |
|---|---|
| `tests/curvelib/test_facets.py` | 200 random facet combinations equal a pandas filter; why-empty names the removing facet |
| `tests/curvelib/test_no_domain_words.py` | grep forbidden words in `curvelib/*.py` |
| `tests/curvelib/test_fit_parity.py` | 5 frozen curves × 6 models equal `phslope` |
| `tests/curvelib/test_provenance.py` | tooltip fields ⊆ available columns; no field invented; year labelled derived |
| `tests/curvelib/test_url_state.py` | URL round-trip reproduces counts |
| `tests/curvelib/test_second_dataset.py` | the M7 dataset loads and returns coverage, curves, fits |
| `tests/curvelib/test_locked_guard.py` | nothing exposed reports model skill on the 24 locked papers (hash `88b1c3a1b769` recorded in E0 run info) |
| UI smoke (Playwright, Chromium is preinstalled in the cloud container) | each view loads; screenshots at 390 px and 1280 px; hover latency measured |

---

## 6. Handoffs, decisions, risks

| Item | Owner | Needed by |
|---|---|---|
| Year rule confirmed (suffix 00–25 → 2000s) | Samuel | Oct 18 |
| Copy of the raw data, release/date, licence and citation text | Samuel | Oct 18 |
| Review of `sorbate_map.csv` (57 rows; organics and `Pu` need decisions) | Samuel, Dr. Black on unusual entries | Oct 30 |
| Whether publication metadata (authors, DOI) exists anywhere | Samuel | Oct 30 |
| Second dataset chosen | Samuel and Abraham | Nov 27 |
| Stack, plot library, hosting | Abraham | Oct 18 |
| Confirm class assignments (`classes.yaml`, still `confirmed: false`) if class colouring is used | Dr. Black | before any class facet ships |

Risks: (1) no citation metadata, so provenance is the paper code only; (2) sorbate strings are messy and the map is a proposal; (3) analysis outputs are exploratory and will change, hence the data-version hash and status banner; (4) engine leakage of sorption words, hence the grep test and M7; (5) people over-reading pooled fits, hence the required warnings; (6) the Predict tab depends on a model that may be replaced after the locked look.

## 7. One-page checklist

- [ ] M0 Oct 18: review, decisions, data and year rule
- [ ] M1 Oct 25: facet data layer, counts equal pandas
- [ ] M2 Nov 1: query UI + URL state; Demo 1
- [ ] M3 Nov 8: plot builder + six fit models; parity tests
- [ ] M4 Nov 15: hover/click provenance; <100 ms at 38,906 points
- [ ] M5 Nov 22: library, export, Predict warnings; Demo 2
- [ ] M6 Nov 29: offline assets, accessibility, phone width
- [ ] M7 Dec 6: second dataset, zero engine edits
- [ ] M8 Dec 13: docs, deployment, buffer
- [ ] M9 Dec 20: sign-off demo
