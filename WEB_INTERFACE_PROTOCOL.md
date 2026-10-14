# Modular web interface: development protocol (for Claude Code)

2026-10-13, updated 2026-10-14 to match `WEB_INTERFACE_DEV_PLAN.md`. Supersedes the single-dataset Claude Doc "Web Interface Development Protocol".

**Status (2026-10-14):** P0 and P1 done; P2 v0 built (read-only FastAPI API and a single-page front end with Elements, Coverage, Curves and Predict tabs); P2a data layer built (periodic-table picker, sorbate map proposal). Everything else is not started; see the requirement status in section 4.

**How the two documents divide the work:** this protocol says *what* the interface must do (design, requirements, tests, honesty rules). `WEB_INTERFACE_DEV_PLAN.md` says *who does it and when* (code inventory, milestones M0–M9, tasks, acceptance tests, dates). Where they disagree, fix whichever is wrong and keep them in step. Abraham is the lead developer; sign-off target is **Dec 20, 2026**.

## 1. Goal and constraint

A visualization and query interface over curve libraries that works for **any tabular dataset of curves** (response vs a swept variable), not only radiochemical sorption. Dr. Black's requirement: modular. Sorption is the first **domain pack**; a second, non-sorption dataset loaded with only a manifest is the acceptance test (plan milestone M7).

Four views make up v1: periodic-table front page (3b), query with shareable URL (3c), plot builder with fits (3d), hover/click provenance (3e).

Non-goals (v1): user accounts, writing back to data, live model training in the browser.

## 2. Architecture

```
dataset.csv + manifest.yaml
        │
   [loader/validator]  ── curvelib/manifest.py: schema, units, validity rules
        │
   [generic engine]    ── curvelib/engine.py: curve definition, coverage/sweep, (facets: M1.2)
        │
   [domain pack]       ── packs/sorption/: derived columns, response modes, entity_picker, predict
        │
   [API layer]         ── curvelib/api.py: read-only JSON (FastAPI)
        │
   [frontend]          ── curvelib/web/index.html: static page, Plotly
```

Run: `python -m curvelib.api` (sorption pack, http://127.0.0.1:8000), or set `CURVELIB_MANIFEST` and `CURVELIB_DATA` for another dataset.

Rules that apply to every task (plan section 3.3):

1. The engine and front end contain **no sorption words** (pH, sorbate, mineral, goethite, ...). Anything sorption-specific (ionic strength, fraction sorbed, Kd, loading regimes, carbonate flags, year from reference code) lives in `packs/sorption/`. A grep test enforces this (`tests/curvelib/test_no_domain_words.py`, to be written).
2. The pack imports analysis code (`phslope`, `data_audit`, `response`); the analysis code never imports the pack. A function both need lives in `phslope`.
3. A fit never runs on fewer than 4 distinct points.
4. Missing is shown as missing, never zero; fields absent from the dataset are omitted.
5. Numbers equal the analysis numbers: golden tests against `phslope` on frozen curves.
6. Every API response and every page carries status, schema version and data version (SHA-256 prefix of the data file).

## 3. Dataset manifest (YAML)

The live manifest is `packs/sorption/manifest.yaml`. Shape (abridged from it):

```yaml
schema_version: 1
pack: sorption
dataset: {id: lscie_sorption, title: "...", source: "LLNL L-SCIE ... sc.dataset.csv", status: exploratory}
columns:
  - {name: Mineral, role: group_a}            # entity A in a pair
  - {name: Sorbate, role: group_b}
  - {name: Reference, role: cluster}          # paper code; independence unit; drives uncertainty
  - {name: Set, role: series}                 # one plotted series = one curve
  - {name: pH, role: sweep_x, units: pH}
  - {name: Sorbed_val, role: value, units_from: Sorbed_units}
  - {name: Mineral_val, role: covariate, units_from: Mineral_units, convert_to: g/L}
  - {name: Ionic_strength, role: covariate, units: mol/L, derived_by: pack.sorption.ionic_strength}
  - {name: Electrolyte_signature, role: label, derived_by: pack.sorption.electrolyte_signature}
response_modes:
  - {id: fraction, expr: pack.sorption.fraction, range: [0, 1]}
  - {id: log_kd, expr: pack.sorption.log_kd}
curve: {key: [Reference, Set], x: pH, x_valid_range: [0, 14], min_x_levels: 3, min_x_span: 1.0}
pair_coverage: {min_points: 50, min_clusters: 2, min_x_span: 4.0}
validity: [{rule: "sweep value inside x_valid_range", action: exclude_row}, ...]
flags: [response_out_of_range]
```

A response mode is `column: <name>`, `expr: <pandas expression>` (backticks around names with spaces), or `pack.<name>.<fn>`.

Requirements: manifest validated on load; unknown roles are an error; unit conversions declared, never inferred; every dropped or flagged row is counted and shown (`/api/accounting`).

## 3a. Data contract for the new features (plan section 3)

What the source file contains (E0 inventory): `Reference` (paper code such as `azzbn01`), `Set`, `Mineral`, `Mineral_formula`, `Mineral_source`, surface area, site density, solids, `Temp`, `pH`, sorbed/aqueous/total sorbate with SDs, electrolytes 1–7, gases with partial pressures, `SurfCharge`, `CEC`. **Absent:** authors, title, journal, DOI, year, equilibration time, aging, separation method, container, pH method. So provenance is the paper code, not a citation.

Derived columns, all in `packs/sorption/pack.py` (task M1.1), none in the engine:

| Column | Source | Notes |
|---|---|---|
| `year` | Reference code suffix | Proposed rule: 00–25 → 2000s, 26–99 → 1900s, labelled "year (derived from reference code)"; **awaits Samuel's confirmation (M0.5)** |
| `element`, `oxidation_state` | `packs/sorption/sorbate_map.csv` | `needs_review` rows (organics, `Pu` without a state, `COM`) stay visible under "Other sorbates" |
| `direction` | `export/curves_meta.csv` `shape_class` | Join on curve ID |
| `loading_mol_per_g`, `loading_regime` | total sorbate ÷ solids; thresholds from `SOLIDS_AND_LOADING.md` | Exploratory; breakpoint poorly located, label says so |
| `atmosphere_class` | `phslope/experiments/data.py::_atmosphere` | Reuse, do not re-implement |
| `has_cosolute`, `co2_present` | `phslope/curves.py` | Reuse |
| `log_k`, `log_kd_per_g`, `aq_source` | `phslope/experiments/kd.py` | `aq_source` ∈ {reported, mass_balance} |
| `lineage_id`, `possible_copy` | E3 outputs (`lineage_clusters.csv`, `duplicate_pairs.csv`) | Join on reference |
| `quality_flags` | `curves_meta.qc_flags`, E3 `data_flags.csv` | Show, never drop |

API endpoints. Built: `/api/meta`, `/api/accounting`, `/api/coverage`, `/api/sweep`, `/api/entities`, `/api/curves`, `/api/points`, `/api/fit` (logistic only), `/api/predict`. Proposed (Abraham may rename):

| Endpoint | Purpose | Milestone |
|---|---|---|
| `GET /api/facets` | Facet definitions and live counts for a selection | M1.3 |
| `GET /api/query` | Points, curves, papers, pairs for a selection; why-empty explanation | M1.3 |
| `GET /api/points` (extend) | Any requested columns, including derived ones, with provenance | M3.1 |
| `GET /api/fit` (extend) | `model` ∈ logistic, logk_line, linear, loess, poly2, poly3; window; included papers | M3.3 |
| `GET /api/library` | Pair-summary rows plus counts and single-paper flag | M5.1 |
| `GET /api/export` | CSV/JSON of the selection with a header block (query, fit settings, data and schema version, status) | M5.2 |

URL grammar (one stable, readable string): `?el=U&ox=6&min=goethite,ferrihydrite&year=1990-2010&I=0.01-0.1&pH=3-9&regime=low,transition&dir=rising&x=pH&y=log_k&color=paper&fit=logk_line`. Unknown keys are ignored with a visible notice.

## 3b. Front page: periodic table of sorbates

- 18-column periodic table layout with lanthanide/actinide rows; each cell is an element that appears as a sorbate. Elements with no data are greyed and not clickable.
- **Colour = amount of data**, switchable (R16): data points, curves, papers, mineral-sorbate pairs with at least 2 papers, mineral count. Use a sequential colour scale (log-scaled counts), a legend, and a text count on hover; do not rely on colour alone (show the number in the cell or on focus). Include a colour-blind-safe palette and a table view of the same counts.
- Hover on an element: name, total points/curves/papers, number of oxidation states, number of minerals. Click to select (multi-select with shift/ctrl).
- Data source: the pack's sorbate parser (`packs/sorption/entities.py`) maps the dataset's sorbate field to (element, oxidation state, species form) by parsing labels such as `U(+6)`; it does not look anything up. The table lives in `packs/sorption/sorbate_map.csv` (56 entries: 42 parsed, 14 `needs_review`). It is a **proposal** until Samuel reviews it (Dr. Black checks unusual entries); unresolved entries are listed, never dropped. Organic or non-element sorbates (for example oxalic acid) appear in an "Other sorbates" panel under the table.
- Genericity: the front page asks the active pack's `entity_picker(curves, coverage)` hook. The sorption pack returns the periodic table. A dataset with no picker gets the default faceted list (R22). The engine only knows "entity with a count".

## 3c. Query flow (after clicking an element)

1. **Oxidation state / species:** checkboxes with counts (for example U(+6), U(+4)); default all; counts sum to the element total (M2.1).
2. **Mineral:** checkboxes grouped by mineral class, with counts equal to `/api/coverage`, searchable (M2.2). Class grouping uses `classes.yaml`, which is still `confirmed: false`; no class facet ships until Dr. Black confirms it.
3. **Other facets** (side panel, all live-counted, all optional; M2.3): year range, ionic strength range and electrolyte, pH range, solids range, loading regime (low / transition / high), atmosphere or CO2 flag, response availability, data flags, paper/reference search, curve direction (rising / falling / bell / unclassified), minimum points per curve, minimum papers per pair. Moving a slider updates counts in under 300 ms on the full file.
4. Counts update as filters change; an empty selection says which facet removed the last rows.
5. A results summary: points, curves, papers, pairs, single-paper pairs flagged, plus a coverage heatmap (mineral by oxidation state) for the selection (M2.4).
6. **Year:** the file has no year field. Use the derived year from section 3a and label it "year (derived from reference code)" everywhere. Until M0.5 confirms the century rule, show codes whose century is ambiguous as unresolved.
7. Selection and plot settings live in the URL (R21, M2.5); a copy-link button; saved queries in browser storage, wrapped in try/catch.

## 3d. Plot builder and fits

- **Axes:** any numeric manifest column or derived column (pH, fraction sorbed, log10 K, log10 Kd per gram, solids, loading, ionic strength, year, temperature) on x or y; log/linear toggle (log axis refuses non-positive values with a message); colour-by (paper by default, mineral, oxidation state, year, ionic strength, flag) and symbol-by.
- **Presets:** fraction sorbed vs pH; log10 K vs pH; log10 Kd vs pH (solids-normalised, with the source flag "reported Aq" or "assumed mass balance"); edge vs covariate (from the library tables).
- **Fit options (R18):** none; logistic edge (built); line of log10 K vs pH (reuse the E1 per-curve line); linear; local smooth (LOESS-type); polynomial degree 2 or 3. The user selects which curves/papers enter the fit. A mixed-effects fit (paper random effect) is a later option, not part of M3; label it clearly if added.
- **Fit statistics:** n points, n papers, R² (state which space), RMSE, parameters with 95% intervals (whole-paper resampling, 100 draws, when more than one paper), fitted band, residual plot toggle, fitting window and the reason excluded points were excluded.
- **Per-paper vs pooled:** default is one fit per paper (coloured by paper); "pool all selected" is allowed but displays the R20 warning (`POOL_WARNING` in `api.py`): pooling across papers widened edges about 1.4 times in our analysis and mixes paper effects. Lineage-linked papers (E3) count as one source in the paper counts shown next to fits.
- **Fits run on the server** using the shared `phslope` functions, so web numbers equal analysis numbers; no JavaScript re-implementation. Cache each fit by (selection hash, model, settings, data version).
- **Honesty rules:** "EXPLORATORY" status banner; never show a fit without n, papers and window; flag extrapolation beyond measured pH; no fit on fewer than 4 points.
- Export plot as PNG/SVG and the plotted data as CSV, with the query and fit settings embedded (M5.2, M5.3).

## 3e. Hover, click and provenance (R19)

Hovering a point shows a compact tooltip; clicking pins a detail panel (M4.1, M4.2). Fields (shown when present, never invented):

- reference code and set; year (derived, labelled as such). Authors, title, journal and DOI are **not in the file**; show them only if Samuel finds a metadata table keyed by `Reference` (M0.7). Never construct a URL.
- mineral (name, formula as stored, source, surface area), sorbate (element, oxidation state)
- pH, response (selected mode), reported sorbed and aqueous values with units and SDs, solids (g/L), total sorbate, loading (mol/g) and regime, ionic strength with electrolytes, gas/atmosphere, temperature
- curve ID, data flags, lineage cluster, "possible copy" badge (28 cross-paper pairs in E3), "needs review" badge (62 curves in E3 `outlier_review.csv`), whether `Aq` was reported or assumed (`aq_source`)
- jump links: other curves from the same paper in the same pair; other papers for this pair. Links change the selection and URL.

Also: a sortable, paged, virtualised data table of the selection; row click highlights the point (M4.3).

Performance: nearest-point lookup for up to ~40k points; WebGL scatter above ~5,000 points; hover latency under 100 ms at 38,906 points, measured and recorded (M4.4).

## 3f. Analysis findings that constrain the interface (plan section 2.6, all exploratory)

| Finding | Required behaviour |
|---|---|
| The paper a curve comes from dominates the scatter; pooling widens edges ~1.4× | Colour by paper by default; pooled-fit warning; paper-level intervals only |
| 28 curves appear in two papers | "Possible copy" flag; lineage-linked papers count as one source |
| Fraction sorbed is not corrected for solids | Show solids on every curve; log K and per-gram Kd presets with the `aq_source` flag |
| High loading lowers binding; breakpoint uncertain | Loading-regime facet and badge, labelled exploratory |
| Salt effect depends on sorbate type (E8) | Ionic strength is a facet; do not imply a universal effect |
| Predictions for a new mineral or sorbate are no better than class means | Predict tab shows distance warnings and "no better than the class mean" text for unseen systems (M5.4) |
| Locked set (24 papers) not opened | No page shows model skill on locked papers; any held-out error column comes from development papers only (check `pair_summary.csv` `heldout_p50_error`, M1.4) |
| Gradient boosting beat the mixed model on grouped validation | Predict tab keeps the Stage 4 development model until the locked-set evaluation is done (M8.3) |

## 3g. Layout sketch

```
[ Status banner: EXPLORATORY · schema v · data version · rows ]
[ Periodic table (colour = data) ]   [ Selection summary: points / curves / papers / pairs ]
        click element
[ Oxidation state ][ Minerals ][ Facets: year, I, pH, solids, regime, atmosphere, direction, flags, paper ]
[ Plot builder: x, y, colour, symbol, scale, preset, fit model, include/exclude papers ]
[ Plot with hover/click provenance ][ Fit table: n, papers, R2, RMSE, params +/- CI, window ]
[ Data table of the current selection (sortable, exportable) ]   [ Library ]   [ Predict ]
```

## 4. Requirements and status (2026-10-14)

| ID | Requirement | Status | Milestone |
|---|---|---|---|
| R1 | Load any manifest-conformant CSV without code changes | Done | proven in M7 |
| R2 | Coverage view: group_a × group_b heatmap of points, curves, clusters; threshold filters | Done | – |
| R3 | Sweep/threshold slider (min points, min clusters) with live counts | Partial (`/api/sweep` exists; check UI use, add live count text) | M2 |
| R4 | Curve viewer: raw points, fitted curve, per-cluster colour, uncertainty band | Partial (no fitted band, no residual toggle) | M3.4 |
| R5 | Query builder: filter on any role/covariate; shareable URL state | Not started | M1–M2 |
| R6 | Curve library view (pair summaries from `export/`): edge, width, height, n_clusters, paper-level CI | Not started | M5.1 |
| R7 | Show status ("exploratory"), schema version and data version on every page | Done | – |
| R8 | Always show **paper-level** uncertainty, never point-level; flag single-paper pairs | Partial (single-paper flag not shown everywhere) | M2.4, M5.1 |
| R9 | Flags visible and filterable: QC flags, loading regime, possible copy, assumed mass balance | Not started | M1.1, M2.3, M4.5 |
| R10 | Export filtered view as CSV/JSON with the query, fit settings and data version recorded | Not started | M5.2 |
| R11 | Pack mechanism: add a domain with a folder + manifest, no engine edits | Done (hooks `entity_picker`, `predict`; `pack.<name>.<fn>`) | M7 |
| R12 | Accessible, works at phone width, no CDN calls, no data leaves the server except requested JSON | Partial (no screenshot or keyboard test; Plotly from CDN) | M2.6, M6 |
| R13 | **Front page = entity map** (3b): periodic table of sorbates coloured by amount of data | Done (v0) | – |
| R14 | After choosing an element: select **oxidation state(s)**, then minerals, then other facets (3c) | Partial (states listed as text, no selector) | M2.1 |
| R15 | **Faceted query** with live counts on every facet | Not started | M1.2, M2.3 |
| R16 | Colour-by metric on the periodic table switchable | Done (v0) | – |
| R17 | **Plot builder** (3d): choose x, y, colour, symbol, response mode, log/linear, presets | Not started (axes fixed: pH vs fraction sorbed) | M3.2 |
| R18 | **Fit tool** with several models, server-side, with R² / RMSE / n / parameters and uncertainty | Partial (logistic only) | M3.3 |
| R19 | **Hover and click on any point** shows full provenance (3e) | Partial (a few hover fields; no pinned panel or jump links) | M4.1, M4.2 |
| R20 | Fits across several papers carry a visible warning and the paper-level interval | Done | – |
| R21 | Selection is a shareable URL; saved queries; export with query + data version | Not started | M2.5, M5.2 |
| R22 | Generic entity picker; another dataset supplies its own picker or gets the default list | Done | M7 |

## 5. Phases, gates and milestones

The original phases map onto the dated milestones in `WEB_INTERFACE_DEV_PLAN.md` section 4 (weeks start Monday; Thanksgiving week light).

| Phase | Work | Gate | Status / milestone |
|---|---|---|---|
| P0 | Manifest schema, loader, validator, unit tests | Invalid manifests rejected with clear errors; row accounting reconciles | Done |
| P1 | Engine: curve builder, coverage, sweep; parity with `phslope` counts | 38,906 rows → 1,704 sweep curves → 1,680 clean → 277 pairs → 76 pass; per-pair counts equal `reports/phslope/stage0/pair_table.csv` | Done |
| P2 | API + coverage heatmap + curve viewer | R2–R4 usable | v0 built; review in **M0 (Oct 14–18)**: Abraham runs it, records defects and the pytest pass count in `docs/web/V0_REVIEW.md`; stack and plot-library decisions |
| P2a | Entity picker framework + periodic table + sorbate map (R13, R16, R22) | Counts per element equal engine counts; unresolved sorbates listed | Built; sorbate map awaits review (Oct 30) |
| P3 | Sorption pack derived columns (3a) | Non-missing counts checked against sources (e.g. `direction` = 1,680); loading regimes 320/141/78 as in `SOLIDS_AND_LOADING.md` | **M1 (Oct 19–25)**, with the generic `facets()` and `/api/facets`, `/api/query`. Gate: facet counts equal a direct dataframe filter; grep test passes |
| P2b | Facet panel and URL state (R14, R15, R21) | Same counts reproduced from a copied URL | **M2 (Oct 26–Nov 1)**. Demo 1 to Dr. Black: U → U(+6) → goethite → I 0.01–0.1, pH 3–9 → copy link → same counts |
| P2c-i | Plot builder and server-side fits (R17, R18, R20) | Fit parity tests (5 curves × 6 models) pass; no fit under 4 points; pooled warning visible | **M3 (Nov 2–8)** |
| P2c-ii | Hover/click provenance, data table, speed (R19) | Hover latency recorded (< 100 ms); tooltips show only fields present | **M4 (Nov 9–15)** |
| P4 | Library view, export, Predict warnings (R6, R10) | 277 library rows match `export/pair_summary.csv`; export re-import gives equal counts | **M5 (Nov 16–22)**. Demo 2 to Dr. Black |
| – | Hardening: local Plotly, accessibility, phone width, error/empty states | Works offline; screenshots at 390 px and 1280 px in `docs/web/screens/` | **M6 (Nov 23–29)** |
| P5 | **Acceptance: second non-sorption dataset** onboarded with a manifest and at most a small pack | **Zero edits under `curvelib/`**; if not met, the release is delayed, not the criterion | **M7 (Nov 30–Dec 6)** |
| P6 | Docs (user, developer, manifest guide), deployment, buffer | Someone else can add a dataset from the guide; URL reachable by Dr. Black | **M8 (Dec 7–13)** |
| – | Sign-off | Dr. Black, unaided: pick an element, filter by mineral and ionic strength, plot log K vs pH, fit a curve per paper, hover a point to find its paper, export the selection, on both datasets | **M9 (Dec 14–20)** |

Cut order if time runs short (M8.4): saved queries, SVG export, per-gram Kd preset. Never cut the golden tests, the paper-level warnings or the second-dataset test.

## 6. Tests

Existing: `tests/curvelib/test_engine.py` (manifest validation, unit conversion, accounting, census parity, arbitrary column names) and `tests/curvelib/test_api.py` (envelope, coverage census, sweep, periodic-table counts, points provenance, single and pooled fit, < 4 points refused, predict leakage guard, index page). Run with `python -m pytest tests/curvelib`.

To write (plan section 5):

| File | Tests |
|---|---|
| `tests/curvelib/test_facets.py` | 200 random facet combinations equal a pandas filter; why-empty names the removing facet |
| `tests/curvelib/test_no_domain_words.py` | grep for forbidden words in `curvelib/*.py` |
| `tests/curvelib/test_fit_parity.py` | 5 frozen curves × 6 models equal `phslope` (tolerance 1e-6) |
| `tests/curvelib/test_provenance.py` | tooltip fields ⊆ available columns; nothing invented; year labelled derived |
| `tests/curvelib/test_url_state.py` | URL round-trip reproduces counts |
| `tests/curvelib/test_second_dataset.py` | the M7 dataset loads and returns coverage, curves, fits |
| `tests/curvelib/test_locked_guard.py` | nothing exposed reports model skill on the 24 locked papers (hash `88b1c3a1b769`, E0 run info) |
| UI smoke (Playwright) | each view loads; screenshots at 390 px and 1280 px; hover latency measured |

Also required: periodic-table counts per element and per oxidation state equal an independent groupby of the raw file; greyed elements not clickable; keyboard navigation and a non-colour readout work; derived columns (`log_k`, `log_kd_per_g`) equal `phslope/experiments/kd.py` on 100 random points (1e-9).

## 7. Decisions and handoffs

| Item | Owner | Needed by | State |
|---|---|---|---|
| Backend: keep FastAPI + static page (recommended, working) or move to a framework | Abraham | Oct 18 | FastAPI v0 in use; confirm in `OPEN_QUESTIONS.md` (M0.3) |
| Plot library: keep Plotly (scattergl) and bundle it locally | Abraham | Oct 18 | Open (M0.4) |
| Hosting, and whether the raw data may be served (L-SCIE licence, citation text) | Abraham (host), Samuel (licence) | Oct 18 | Open (M0.6) |
| Year rule (suffix 00–25 → 2000s) and the "derived" label | Samuel | Oct 18 | Open (M0.5) |
| Copy of the raw data to Abraham; L-SCIE release/date | Samuel | Oct 18 | Open (M0.6) |
| Review `sorbate_map.csv` (organics and `Pu` need decisions) | Samuel; Dr. Black on unusual entries | Oct 30 | Proposal written |
| Publication metadata (authors, DOI) held anywhere | Samuel | Oct 30 | Open (M0.7) |
| `heldout_p50_error` uses development papers only | Samuel | Oct 25 | Open (M1.4) |
| Class assignments (`classes.yaml`) if class grouping is used | Dr. Black | before any class facet ships | `confirmed: false` |
| Second dataset for M7 (any y-vs-x curves, grouped, with a cluster id; licence checked) | Samuel and Abraham | Nov 27 | Open |
| Predictor switch to gradient boosting | Samuel | Dec 13 (M8.3) | Only after the locked-set evaluation |
| Ownership | – | – | Abraham lead developer; Samuel owns data, decisions and the sorption pack review; Claude Code assists either |

Risks: no citation metadata (provenance is the paper code only); sorbate strings are messy and the map is a proposal; analysis outputs are exploratory and will change (hence the data-version hash and status banner); sorption words leaking into the engine (grep test and M7); people over-reading pooled fits (required warnings); the Predict tab depends on a model that may be replaced after the locked look.

## 8. Handoff

P0–P2a are built on branch `ph-slope` (code in `curvelib/`, `packs/sorption/`, `tests/curvelib/`). Next is M0: Abraham runs v0, reviews it and records decisions; then follow `WEB_INTERFACE_DEV_PLAN.md` milestone by milestone. Do not touch `phslope/` outputs. Report counts against the census after each milestone, and update the status column in section 4 when a requirement changes state.
