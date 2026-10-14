# Modular web interface: development protocol (for Claude Code)

2026-10-13. Supersedes the single-dataset Claude Doc "Web Interface Development Protocol". Status: plan, nothing built.

## 1. Goal and constraint

A visualization and query interface over curve libraries that works for **any tabular dataset of curves** (response vs a swept variable), not only radiochemical sorption. Dr. Black's requirement: modular. Sorption is the first **domain pack**; a second, non-sorption dataset is the acceptance test.

Non-goals (v1): user accounts, writing back to data, live model training in the browser.

## 2. Architecture

```
dataset.csv + manifest.yaml
        │
   [loader/validator]  ── manifest schema, units, validity rules
        │
   [generic engine]    ── curve definition, coverage/sweep, fit hooks, export
        │
   [domain pack]       ── derived columns, response modes, flags, descriptors
        │
   [API layer]         ── read-only JSON (FastAPI)
        │
   [frontend]          ── coverage heatmap, curve viewer, library, query builder
```

Rules: the engine and frontend contain **no sorption words**. Anything sorption-specific (ionic strength computation, fraction sorbed, Kd, loading regimes, carbonate flags) lives in `packs/sorption/`.

## 3. Dataset manifest (YAML)

```yaml
schema_version: 1
dataset: {id: lscie_like, title: "...", source: "...", status: exploratory}
columns:
  - {name: Mineral, role: group_a}          # entity A in a pair
  - {name: Sorbate, role: group_b}
  - {name: Paper_ID, role: cluster}         # independence unit; drives uncertainty
  - {name: pH, role: sweep_x, units: pH}
  - {name: Sorbed_val, role: value, units_from: Sorbed_unit}
  - {name: Mineral_val, role: covariate, units_from: Mineral_unit, convert_to: g/L}
  - {name: Ionic_strength, role: covariate, derived_by: pack.sorption.ionic_strength}
response_modes:
  - {id: fraction, expr: "Sorbed_val/Sorbate_val", range: [0,1]}
  - {id: log_kd, expr: pack.sorption.log_kd}
curve: {key: [Paper_ID, group_a, group_b, series_id], x: sweep_x, min_points: 5}
pair_coverage: {min_points: 15, min_clusters: 2}
validity: [{rule: "response in range", action: flag}, {rule: "x monotone unique", action: drop_dup}]
flags: [high_loading, single_paper, extrapolated_edge]
```

Requirements: manifest validated by JSON Schema; unknown roles are an error; unit conversions declared, never inferred; every dropped/flagged row is counted and shown in a data-quality panel.

## 3b. Front page: periodic table of sorbates

- 18-column periodic table layout with lanthanide/actinide rows; each cell is an element that appears as a sorbate. Elements with no data are greyed and not clickable.
- **Colour = amount of data**, switchable (R16): data points, curves, papers, mineral-sorbate pairs with at least 2 papers. Use a sequential colour scale (log-scaled counts), a legend, and a text count on hover; do not rely on colour alone (show the number in the cell or on focus). Include a colour-blind-safe palette and a table view of the same counts.
- Hover on an element: name, total points/curves/papers, number of oxidation states, number of minerals. Click to select (multi-select with shift/ctrl).
- Data source: the pack's *sorbate parser* maps the dataset's sorbate field to (element, oxidation state, species form). The mapping table lives in `packs/sorption/sorbate_map.csv` (human-reviewed; unresolved entries listed in a "needs review" panel, never silently dropped). Organic or non-element sorbates (for example oxalic acid) appear in a separate "Other sorbates" panel under the table.
- Genericity: the front page asks the active pack for an `EntityPicker`. The sorption pack returns the periodic table. A dataset with no picker gets the default faceted list (R22). The engine only knows "entity with a count".

## 3c. Query flow (after clicking an element)

1. **Oxidation state / species:** checkboxes with counts (for example U(VI), U(IV)); default all.
2. **Mineral:** checkboxes grouped by mineral class, with counts, searchable.
3. **Other facets** (side panel, all live-counted, all optional): year range (slider), ionic strength range and electrolyte, pH range, solids loading range, loading regime (low / transition / high), atmosphere or CO2 flag, response availability, data flags, paper/reference search, curve direction (rising / falling / bell / unclassified), minimum points per curve, minimum papers per pair.
4. Counts update as filters change; an empty selection shows why (which facet removed the last rows).
5. A results summary: points, curves, papers, pairs, plus the coverage heatmap (mineral by oxidation state) for the current selection.
6. **Year:** confirm in E0.1 whether a year or bibliographic field exists; if not, the reference code encodes year (two digits) and the facet must say "year derived from reference code". Do not guess the century; if ambiguous, show it as unresolved.

## 3d. Plot builder and fits

- **Axes:** any numeric manifest column or derived column (pH, fraction sorbed, log10 K, log10 Kd, solids, loading, ionic strength, year, temperature if present) on x or y; log/linear toggle; optional colour-by (paper, mineral, oxidation state, year, ionic strength, flag) and symbol-by.
- **Presets:** fraction sorbed vs pH; log10 K vs pH; log10 Kd vs pH (solids-normalised, with the source flag "reported Aq" or "assumed mass balance"); edge vs covariate (from the library tables).
- **Fit options (R18):** none; linear; line of log10 K vs pH (mid-range points); logistic edge; local smooth (LOESS-type); polynomial (degree 2 or 3); user can select which curves/papers are included in the fit.
- **Fit statistics:** n points, n papers, R2 (state which space), RMSE, parameters with 95% intervals (paper-level bootstrap when more than one paper), residual plot toggle. Show the fitting window (which points were used) and the reason excluded points were excluded.
- **Per-paper vs pooled:** default is one fit per paper (coloured by paper); "pool all selected" is allowed but displays the R20 warning: pooling across papers widened edges about 1.4 times in our analysis and mixes paper effects. A mixed-effects fit (paper random effect) is offered once E1 is built; label it clearly.
- **Fits run on the server** using the shared `phslope` functions, so the web numbers equal the analysis numbers; no separate JavaScript re-implementation. Each fit result is cached by (selection hash, model, settings, data version).
- **Honesty rules:** show the "EXPLORATORY" status banner; never show a fit without n, papers, and window; flag extrapolation beyond measured pH; no fit is offered on fewer than 4 points.
- Export plot as PNG/SVG and the plotted data as CSV, with the query and fit settings embedded.

## 3e. Hover, click and provenance (R19)

Hovering a point shows a compact tooltip; clicking pins a detail panel. Fields (shown when present, never invented):

- reference code/ID and, when the dataset has it, authors, title, journal, year, DOI (link only if a DOI field exists; never construct a URL)
- mineral (name and formula as stored), sorbate (element, oxidation state, form)
- pH, response (selected mode), reported sorbed and aqueous values with units, solids (g/L), total sorbate, loading (mol/g) and regime, ionic strength with electrolyte, atmosphere/gas, temperature and time if present
- curve ID, point index, data flags, lineage cluster (once E3 exists), whether `Aq` was reported or assumed
- the other curves from the same paper in the same pair (jump links), and "show other papers for this pair"

Performance: tooltips need nearest-point lookup (spatial index) for up to ~40k points; use canvas or WebGL rendering above ~5,000 points; test hover latency (< 100 ms).

## 3f. Layout sketch

```
[ Periodic table (colour = data) ]   [ Selection summary: points / curves / papers ]
        click element
[ Oxidation state ][ Minerals ][ Facets: year, I, pH, solids, regime, atmosphere, paper ]
[ Plot builder: x, y, colour, symbol, scale, fit model, include/exclude papers ]
[ Plot with hover/click provenance ][ Fit table: n, papers, R2, RMSE, params +/- CI ]
[ Data table of the current selection (sortable, exportable) ]
```

## 4. Requirements

| ID | Requirement |
|---|---|
| R1 | Load any manifest-conformant CSV without code changes |
| R2 | Coverage view: group_a × group_b heatmap of points, curves, clusters; filters by thresholds |
| R3 | Sweep/threshold slider (min points, min clusters) with live counts |
| R4 | Curve viewer: raw points, fitted curve, per-cluster colour, uncertainty band |
| R5 | Query builder: filter on any role/covariate; shareable URL state |
| R6 | Curve library view (pair summaries from `export/`): edge, width, height, n_clusters, paper-level CI |
| R7 | Show export status ("exploratory") and schema_version on every page |
| R8 | Always show **paper-level** uncertainty, never point-level; flag single-paper pairs |
| R9 | Flags visible and filterable: high loading, extrapolated edge, assumed mass balance |
| R10 | Export filtered view as CSV/JSON with the manifest and filters recorded |
| R11 | Pack mechanism: add a domain with a folder + manifest, no engine edits |
| R12 | Accessible, works at phone width, no data leaves the server |
| R13 | **Front page = entity map** (section 3b): a periodic table of sorbates, each element coloured by amount of data; click to select |
| R14 | After choosing an element: select **oxidation state(s)**, then minerals, then other facets (section 3c) |
| R15 | **Faceted query** over any manifest column: mineral, sorbate form, year range, ionic strength range, pH range, solids, loading regime, electrolyte, atmosphere, paper; live counts on every facet |
| R16 | Colour-by metric on the periodic table switchable: points, curves, papers, pairs with >=2 papers, mineral count |
| R17 | **Plot builder** (section 3d): choose x, y, colour, symbol; response mode; log/linear axes; one click presets (fraction vs pH, log K vs pH, log Kd vs pH) |
| R18 | **Fit tool**: optional fitted curve with a chosen model type, shown with R2 / RMSE / n / parameters and uncertainty; fit done server-side by the shared package code |
| R19 | **Hover and click on any point** shows full provenance (section 3e) |
| R20 | Fits across several papers carry a visible warning and the paper-level interval (pooling widens edges and mixes paper effects) |
| R21 | Selection is a shareable URL; "save query" and export (CSV + the query + manifest + data version) |
| R22 | Everything above is generic: the periodic table is one *entity picker* supplied by the sorption pack; another dataset can supply a different picker (tree, grid, list) or the default faceted list |

## 5. Phases and gates

| Phase | Work | Gate |
|---|---|---|
| P0 | Manifest schema, loader, validator, unit tests on synthetic data (`phslope/synth.py`) | Invalid manifests rejected with clear errors; row accounting reconciles |
| P1 | Engine: curve builder, coverage, sweep; parity with `phslope` counts (38,906 rows → 76 pairs at current thresholds, must reproduce) | Counts match census exactly |
| P2 | API + coverage heatmap + curve viewer | Usable on exported tables; R2–R4 |
| P2a | Entity picker framework + **periodic table front page** + sorbate map (R13, R16, R22) | Counts per element equal the engine counts exactly; unresolved sorbates listed, none dropped |
| P2b | **Facet panel** and query state in URL (R14, R15, R21) | Same selection reproduced from a URL; facet counts equal a direct dataframe filter in tests |
| P2c | **Plot builder, server-side fits, hover/provenance** (R17–R20) | Fit numbers equal `phslope` outputs (golden tests); hover shows all provenance fields; pooled-fit warning present |
| P3 | Sorption pack: ionic strength, response modes, solids/loading flags, carbonate flag | Matches `SOLIDS_AND_LOADING.md` numbers (1,143 curves with solids; regimes 320/141/78) |
| P4 | Library view, query builder, URL state, exports | R5, R6, R10 |
| P5 | **Acceptance: second non-sorption dataset** (e.g. dose–response, soil moisture curves, or any x–y per group with a cluster id) onboarded by writing only a manifest plus at most a small pack | Zero engine/frontend changes; if any are needed, fix the abstraction before release |
| P6 | Docs, deployment, sign-off by Dr. Black | Demo on both datasets |

## 6. Tests

- Unit: manifest validation, unit conversion, validity rules, curve keys.
- Golden: engine outputs on the sorption data equal frozen `export/` tables.
- Property: random synthetic datasets of arbitrary column names round-trip through the engine.
- UI: smoke tests for each view; screenshot at desktop and phone width.
- Periodic table: counts per element and per oxidation state equal an independent groupby of the raw file; every unresolved sorbate is listed; greyed elements are not clickable; keyboard navigation and a non-colour readout work.
- Facets: random combinations of facets give the same row counts as a plain dataframe filter (property test); URL round-trip reproduces the selection.
- Fits: golden tests against `phslope` fits on frozen curves; refuse fits on < 4 points; paper-level intervals present when > 1 paper.
- Hover: every tooltip field maps to a manifest column or derived column; missing fields are omitted, never blank-filled; latency test at 40,000 points.
- Leakage guard: locked test set papers are never exposed to model-fitting views (see `PH_ONLY_TEST_PROTOCOL.md`).

## 7. Open decisions (need Samuel / Dr. Black)

1. Backend: FastAPI + a static frontend (recommended) or a notebook-based tool (e.g. Panel/Streamlit) as a quick v0.
2. Hosting and whether the raw data may be served (licence of the source dataset; dataset is LLNL L-SCIE; check its licence/terms and cite it).
3. Which second dataset for P5.
4. Whether Abraham owns frontend and Samuel owns the sorption pack.
5. Who reviews `sorbate_map.csv` (element, oxidation state, form for every sorbate string); proposed: Samuel, with Dr. Black checking unusual entries.
6. Whether year/authors/DOI exist in the L-SCIE file (E0.1 of the test protocol answers this); the tooltip and year facet degrade gracefully if not.

## 8. Handoff

Start with P0–P1 in a branch (P2a–P2c follow; the periodic-table front page, facet query and plot/fit/hover tools in sections 3b–3e are required for sign-off); do not touch `phslope/` outputs. Report counts against the census after each phase.
