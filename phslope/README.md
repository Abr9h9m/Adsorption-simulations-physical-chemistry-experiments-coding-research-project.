# phslope — pH-only slope library and transfer model

Build spec: `PH_ONLY_DEV_SPEC.md` (project root). This README holds the decisions the spec asks to be written down, the conventions, and how to run each stage.

**Status (2026-10-13):** Stage 0 PASS. Stage 1: synthetic PASS, real data **FAIL** (46.8% < 80%); Samuel chose to continue with the 745-curve core library, so **everything from Stage 2 on is EXPLORATORY**. Stage 2 (`--exploratory`): go/no-go rule met with the unconfirmed classes (signal is mostly sorbate class and the specific pair; mineral class adds little). Stage 3 (`--exploratory`, no descriptors yet): every model fails (median edge error 1.1-1.8 pH vs 0.5); the same pair measured in another paper predicts to 0.6 pH. Pooled-pair comparison: pooling across papers widens edges ~1.4x. Export tables in `export/`. Blocked for confirmatory runs: classes confirmation, descriptor tables, freezing thresholds.yaml.

## Improvement program (PH_ONLY_TEST_PROTOCOL.md)

Code in `phslope/experiments/`, settings and pre-declared decision rules in `config/experiments.yaml`, outputs in
`reports/phslope/experiments/E0 ... E9, F/`, every run in `REGISTRY.md`, accepted/rejected adjustments in
`MODEL_ADJUSTMENTS.md`. A seeded 20% of papers (24 of 120) is LOCKED in `config/locked_test_papers.txt`;
development code drops them (`registry.drop_locked`). The locked set is opened once, by
`python -m phslope.experiments.integrate --open-locked-set "I understand this is the single final look"`.
Status and plain-English summary: `reports/phslope/experiments/CHECKPOINT.md`.

```
python -m phslope.experiments.e00_inventory      # E0.1 raw inventory + mass balance
python -m phslope.experiments.e03_audit          # E3 duplicates, lineage clusters, validity flags
python -m phslope.experiments.e01_logk_mixed     # E1 log10 K mixed model (~14 min; --reuse to redo the summary)
python -m phslope.experiments.e02_weights_censoring   # E2 (~40 min)
python -m phslope.experiments.e04_lab_effect     # E4
python -m phslope.experiments.e05_coverage       # E5
python -m phslope.experiments.e07_carbonate      # E7 step 1a (~25 min)
python -m phslope.experiments.e08_ionic_strength # E8
python -m phslope.experiments.e09_surface_area   # E9
python -m phslope.experiments.templates          # E6/E9/E10 data-entry templates + priority list
python -m phslope.experiments.integrate          # F on development papers only
```

## How to run

From the project root:

```
python -m pytest                      # all phslope tests (real-data tests skip if the file is absent)
python -m phslope.load                # load + clean the raw file, print unit report
python -m phslope.census              # Stage 0 -> reports/phslope/stage0/
python -m phslope.census --data PATH  # use a different raw file
python -m phslope.stage1 --synthetic  # Stage 1 synthetic check
python -m phslope.stage1              # Stage 1 on the real file (~25 min, 11 workers)
python -m phslope.stage2 --exploratory  # Stage 2, all parts, labelled exploratory
python -m phslope.pooled              # pooled-pair comparison (exploratory)
python -m phslope.stage3 --exploratory  # Stage 3 (~75 min); without --exploratory it needs frozen thresholds
python -m phslope.export              # tables for the web interface -> export/
```

The raw file is found in this order: `--data` flag, `SORPTION_DATA_FILE` environment variable, `data.file` in `phslope/config/config.yaml`, then `data_audit.CONFIG["DATA_FILE"]`.

Every stage writes `RUN_INFO.json` (git commit, config hash, data file, time) next to its outputs. A commit ending in `-dirty` means tracked files had uncommitted changes when it ran.

## Curve definition (Task 0.2) — confirmed by Samuel 2026-10-12

**One curve = one `Set`.**

What `Set` and `SetID` are, from the file itself (38,906 rows, 3,125 Sets, 334 References):

- `Set` is one plotted series inside one paper. Its name is the reference code plus a figure or table tag, e.g. `azbn00_f1` = paper `azbn00`, figure 1; `_t` = table. 99.5% of Set names start with their Reference.
- `SetID` is a row counter inside a Set (1, 2, 3, …). `(Set, SetID)` is unique for every row. It is not a batch or experiment ID.
- Every Set has exactly one Reference, mineral, sorbate and electrolyte signature.
- Every Set whose pH spans at least 1 unit has exactly one value of ionic strength, total sorbate, solids loading and temperature. So a pH-sweep Set is already "one pH sweep at constant conditions". No extra grouping rule is needed.
- Sets with constant pH are mostly isotherms (total sorbate varies); they are not pH curves.

Rule as implemented (`curves.py`, settings in `config.yaml → curves`):

| Kind | Rule | Count (2025 file) |
|---|---|---|
| `ph_sweep` | ≥ 3 distinct pH values (2 decimals) and pH span ≥ 1, counting usable rows only | 1,704 |
| `constant_ph` | pH span < 0.2 | 1,389 |
| `too_few_ph_levels` | everything else | 32 |

A usable row has pH in [0, 14] and a fraction-sorbed value. The constant-conditions facts are re-checked on every run (`conditions_vary` column; currently 0 curves), not assumed.

A **clean curve** is a `ph_sweep` curve with no `unit_mismatch` and no `conditions_vary` (1,680 curves). Stage 0 counts use clean curves only. Stage 1 QC (spec 4.5) is applied on top of that.

## Electrolyte signature and co-solutes (Task 0.4)

The signature splits 73 studies (reference, mineral, sorbate) into several groups. Because a curve is a Set, the split never cuts a curve in two. Pairs are `(mineral, sorbate)`, so the signature is not a grouping key anywhere. Example: d01 ferrihydrite–U(VI) with nitrate + Na only is 23 Sets, 390 points, 6 ionic-strength levels, as the spec expected.

What the extra signature members are: mostly **co-solutes** that change the chemistry (carbonate, sulfate, phosphate, humic/fulvic acid, a second sorbate), not tracer ions. Each curve gets:

- `cosolutes`: signature members that are not background salt (`config.yaml → curves.background_ions`), joined with `+`.
- `has_cosolute`: 237 of 1,680 clean curves.
- `co2_present`: CO2(g) reported with partial pressure > 0, or a C(+4) electrolyte (1,052 clean curves).

Co-solute curves are **kept and flagged** (Samuel, 2026-10-12). Ca(+2) and Mg(+2) count as background salt.

## Conventions

- **Never split a joined label string.** Labels contain `+`, `-` and parentheses (`Na(+1)`, `Se(-2)`, `Cl(-1)`). The old junk sorbate `2)` came from splitting `mineral-signature-Se(-2)` on `-`. Use `load.split_signature` for signatures and `load.pair_label` / `split_pair_label` (separator ` | `) for display strings. `load.standardise_labels` refuses any sorbate or mineral label shorter than 2 characters or with no letter.
- **Ionic strength** comes from `data_audit.compute_ionic_strength` (oxyanion charges corrected).
- **Response** is fraction sorbed = `Sorbed_val / Sorbate_val`, falling back to `1 - Aq_val / Sorbate_val` when `Sorbed_val` is missing, via `response.compute_response`. `Sorbate_val` is converted to mol/L first (39 rows are in nmol/L).
- **Solids loading:** g/L, mg/mL and mg/L are converted to `solids_g_L`; m2/L goes to `solids_m2_L`; cm3/g and L/kg (18 rows) cannot be converted and stay missing.
- **Bad pH:** rows with pH missing or outside [0, 14] are flagged `bad_ph` and kept in the observation table, but never used in a curve. 35 rows have pH > 14 (e.g. 60.2, 70.3), which are data-entry errors.
- **Unit mismatch:** a curve is flagged if more than 5% of its fraction-sorbed values are above 1.05 or below −0.05 (24 curves).

## Outputs (Stage 0)

`reports/phslope/stage0/`:

| File | Content |
|---|---|
| `SUMMARY.md` | numbers, pass/fail, next decision |
| `RUN_INFO.json` | commit, config hash, data file |
| `curves.csv` | one row per Set: identity, kind, conditions, flags |
| `pair_table.csv` | one row per (mineral, sorbate) from clean curves, with `passes` |
| `pair_table_conditions_reported.csv` | same, counting only curves that report solids loading and total sorbate |
| `matrix_curves.csv`, `matrix_references.csv` | mineral × sorbate counts |
| `gap_list.csv` | empty or thin cells in the dense block (top 12 minerals × top 12 sorbates) |
| `signature_fragmentation.csv` | Task 0.4 table |

`data/descriptors/`: `*_template.csv` is rewritten each run; `mineral_descriptors.csv` / `sorbate_descriptors.csv` are created once and never overwritten (Samuel fills them, with a source for every value).

## Not built yet

Work-order item 11: Stage 4 predictor (`predict_slope_curve`) and the Stage 5 report. (Items 9–10 are built: `export`, `descriptors`, `transfer` (baselines live here), `cv`, `stage3`.) (Items 4–8 are built: `synth`, `fit_edge`, `fit_smooth`, `slope`, `bootstrap`, `qc`, `library`, `registration`, `fpca`, `reml`, `variance`, `cluster`, `schemes`, `report`, `stage1`, `stage2`.)
