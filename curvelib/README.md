# curvelib: generic curve-library engine (WEB_INTERFACE_PROTOCOL.md)

Status 2026-10-13: **P0, P1 done; P2 v0 built** (read-only API + single-page front end). Backend: FastAPI +
static page (the protocol's recommended default for open decision 1; not formally confirmed).

Run: `python -m curvelib.api` then open http://127.0.0.1:8000 (Elements = periodic table coloured by data,
Coverage = heatmap with thresholds, Curves = points per paper + server-side logistic fit with paper-level
intervals and the pooling warning, Predict = Stage 4 predictor with its warnings). Plotly loads from cdnjs.
Endpoints: /api/meta, /api/accounting, /api/coverage, /api/sweep, /api/entities, /api/curves, /api/points,
/api/fit, /api/predict. Every response carries status, schema_version and a data-version hash.
Not yet: query state in the URL (R21), full facet panel with live counts (R15), plot builder axes (R17),
exports (R10), phone-width screenshot test, second-dataset acceptance (P5).

- `curvelib/manifest.py`: JSON Schema for dataset manifests; extra checks (exactly one group_a, group_b,
  cluster, sweep_x; conversions declared, never inferred; curve key and response columns declared).
  Response modes: `column:` (any column name) or `expr:` (arithmetic; non-identifier names in backticks)
  or `expr: pack.<name>.<fn>`.
- `curvelib/engine.py`: no domain words. `run(df, manifest)` -> rows with `_status` (every row in exactly
  one bucket), curves (points, sweep span, sweep classification, response-range flag), coverage
  (group_a x group_b: points, curves, clusters, span, pass), `sweep()` for the threshold slider.
- `packs/sorption/`: `manifest.yaml` + `pack.py` (ionic strength, electrolyte signature, fraction sorbed
  with total converted to mol/L, log Kd). Reuses the analysis code, so numbers are identical.

P1 gate (census parity) **passes exactly**: 38,906 rows -> 1,704 sweep curves, 1,680 clean, 277 pairs,
76 passing; points and paper counts equal `reports/phslope/stage0/pair_table.csv` for every pair.

Tests: `python -m pytest tests/curvelib` (invalid manifests rejected with clear messages; row accounting
reconciles; a non-sorption dataset with arbitrary column names, including spaces and accents, round-trips;
census parity on the real file).
