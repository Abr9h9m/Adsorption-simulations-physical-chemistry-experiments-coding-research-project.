# curvelib: generic curve-library engine (WEB_INTERFACE_PROTOCOL.md)

Status 2026-10-13: **P0, P1 done; P2 v0 built** (read-only API + single-page front end). Backend: FastAPI +
static page (the protocol's recommended default for open decision 1; not formally confirmed).

**Setup on a new machine.** The raw L-SCIE file is **not in the repo** (the repo is public and the data licence
is still unchecked, WEB_INTERFACE_DEV_PLAN M0.6); Samuel shares `sc.dataset.csv` (16.8 MB, 38,906 rows) privately.

1. Branch `ph-slope`, Python 3.11: `pip install -r requirements.txt`
2. Put the file at `data/raw/sc.dataset.csv` (git-ignored, so it cannot be committed by accident), or point
   `SORPTION_DATA_FILE` (or `CURVELIB_DATA`) at it wherever it lives.
3. Check: `python -c "from phslope.common import resolve_data_file; print(resolve_data_file())"` prints that path,
   and `python -m pytest tests/curvelib` passes (22 tests; the real-data tests skip if the file is missing).
4. `python -m curvelib.api`. The first Predict call refits the predictor (a few minutes) because the cached
   model file is git-ignored; after that it is cached.

Everything else the app reads (`export/`, `reports/phslope/stage1/library/`, `packs/sorption/sorbate_map.csv`,
config) is tracked.

Run: `python -m curvelib.api` then open http://127.0.0.1:8000. The app starts empty; upload a dataset to
begin. For compatible sorption datasets, the UI also provides Elements, Coverage, Curves, and Predict views.
Coverage is a heatmap with thresholds; Curves shows points per source and server-side logistic fits with paper-level
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

## Run with Python 3.15 on macOS

The original `requirements.txt` records the Python 3.11.9 environment used for the existing analysis
outputs. A separate `requirements-py315.txt` upgrades the numerical stack for Python 3.15. Since this
changes NumPy and other scientific packages, numerical parity should be checked before comparing new
results with the existing outputs.

From the repository root, create and activate an environment, then install the Python 3.15 dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
PYYAML_FORCE_LIBYAML=0 python -m pip install -r requirements-py315.txt
python -m curvelib.api
```

The app opens with an empty workspace. Open http://127.0.0.1:8000 and upload a CSV to begin. The upload
flow is domain-neutral for curve-shaped data: choose numeric x and response columns and map optional group
and source columns. The PyYAML setting selects its pure-Python parser while Python 3.15 wheels for its
optional C extension are unavailable. Uploaded data stays in memory and clears when the server stops.

## Render deployment preparation

The repository includes `render.yaml` and `.python-version`. The Blueprint uses the Python 3.11.9 dependency
set from `requirements.txt`, binds Uvicorn to Render's `$PORT`, and runs one worker because uploaded datasets
are held in process memory. Render's initial configuration caps uploads at 10 MB and keeps up to four active
browser datasets in memory. Each browser has an isolated dataset session; session data expires after two hours
of inactivity and is lost when the service restarts or redeploys. Keep one service instance unless state
storage is moved to a shared backend. Creating or deploying the Render service still requires linking the
repository in the user's Render account.
