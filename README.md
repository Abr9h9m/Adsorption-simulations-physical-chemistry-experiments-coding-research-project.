# Response-Surface Fingerprinting of Mineral Sorption Sensitivity

Estimates the local gradient and Hessian of sorption A(pH, ionic strength) from compiled
data (local weighted quadratic regression) and tests whether that derivative field works as
a mineral/sorbate "fingerprint". See `CLAUDE.md` for full status, conventions and plan.

## Layout

```
*.py                         pipeline code (flat; run everything from this folder)
synthetic_pilot_data.csv     synthetic dataset read by the modules' self-tests
phslope/                     pH-only slope library (PH_ONLY_DEV_SPEC.md); see phslope/README.md
tests/phslope/               pytest tests for phslope
reports/phslope/             phslope stage outputs
data/descriptors/            mineral/sorbate descriptor tables (human-filled, cited)
OPEN_QUESTIONS.md            decisions waiting on Samuel / Dr. Black
results/
  pipeline_synthetic/        run_pipeline.py output, synthetic mode
  pipeline_real/             run_pipeline.py output, real mode (first pass, NOT findings)
  data_audit/                data_audit.py output (pilot subsets, per-reference breakdown)
Adsorption-simulations-project/
                             shared GitHub repo (Abraham). Older copies of the code,
                             plus docs, audit plots and TODO.md. Not used by the code here.
```

Real data (LLNL compiled set) lives outside this folder: `C:\Users\itzju\sc.dataset.csv`.

## Commands

```
python test_fixes.py                       # regression tests (two-axis pipeline)
python -m pytest                           # phslope tests
python -m phslope.census                   # phslope Stage 0
python -m phslope.experiments.integrate    # improvement program, development papers (see phslope/README.md)
python generate_synthetic_dataset.py       # rewrites synthetic_pilot_data.csv
PIPELINE_MODE=synthetic python run_pipeline.py
PIPELINE_MODE=real PIPELINE_DATA=C:\Users\itzju\sc.dataset.csv python run_pipeline.py
python data_audit.py                       # uses CONFIG["DATA_FILE"]
```

`run_pipeline.py` defaults to **real** mode when `PIPELINE_MODE` is unset.
