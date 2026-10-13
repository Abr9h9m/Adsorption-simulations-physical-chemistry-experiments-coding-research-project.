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

## 5. Phases and gates

| Phase | Work | Gate |
|---|---|---|
| P0 | Manifest schema, loader, validator, unit tests on synthetic data (`phslope/synth.py`) | Invalid manifests rejected with clear errors; row accounting reconciles |
| P1 | Engine: curve builder, coverage, sweep; parity with `phslope` counts (38,906 rows → 76 pairs at current thresholds, must reproduce) | Counts match census exactly |
| P2 | API + coverage heatmap + curve viewer | Usable on exported tables; R2–R4 |
| P3 | Sorption pack: ionic strength, response modes, solids/loading flags, carbonate flag | Matches `SOLIDS_AND_LOADING.md` numbers (1,143 curves with solids; regimes 320/141/78) |
| P4 | Library view, query builder, URL state, exports | R5, R6, R10 |
| P5 | **Acceptance: second non-sorption dataset** (e.g. dose–response, soil moisture curves, or any x–y per group with a cluster id) onboarded by writing only a manifest plus at most a small pack | Zero engine/frontend changes; if any are needed, fix the abstraction before release |
| P6 | Docs, deployment, sign-off by Dr. Black | Demo on both datasets |

## 6. Tests

- Unit: manifest validation, unit conversion, validity rules, curve keys.
- Golden: engine outputs on the sorption data equal frozen `export/` tables.
- Property: random synthetic datasets of arbitrary column names round-trip through the engine.
- UI: smoke tests for each view; screenshot at desktop and phone width.
- Leakage guard: locked test set papers are never exposed to model-fitting views (see `PH_ONLY_TEST_PROTOCOL.md`).

## 7. Open decisions (need Samuel / Dr. Black)

1. Backend: FastAPI + a static frontend (recommended) or a notebook-based tool (e.g. Panel/Streamlit) as a quick v0.
2. Hosting and whether the raw data may be served (licence of the source dataset; dataset is LLNL L-SCIE; check its licence/terms and cite it).
3. Which second dataset for P5.
4. Whether Abraham owns frontend and Samuel owns the sorption pack.

## 8. Handoff

Start with P0–P1 in a branch; do not touch `phslope/` outputs. Report counts against the census after each phase.
