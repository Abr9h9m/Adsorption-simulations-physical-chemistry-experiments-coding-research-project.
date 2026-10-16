# Stage 0 summary: census and clean systems table

Run: commit `d468a46`, config `7683c4e695c4`, data `C:\Users\itzju\sc.dataset.csv`, 2026-10-16T11:34:07Z.

## Result

**PASS.** 72 mineral-sorbate pairs meet the rule (>= 50 usable points, pooled pH span >= 4.0, >= 2 references). The stage needs >= 60.

Pairs passing when only curves reporting both solids loading and total sorbate are counted: 72.

## Data loaded

- Rows: 38,906. (The handoff said ~80k; this file has fewer.)
- Rows with pH missing or outside [0, 14] (flagged `bad_ph`, kept but not used): 657.
- Rows with no fraction-sorbed response: 9,532.
- Total-sorbate units: {'mol/L': 30448, nan: 8419, 'nmol/L': 39} (converted to mol/L).
- Solids-loading units: {'g/L': 36971, nan: 1003, 'mg/mL': 416, 'm2/L': 311, 'mg/L': 187, 'cm3/g': 12, 'L/kg': 6}. g/L, mg/mL and mg/L are converted to g/L; m2/L is kept separately; 18 rows have a unit that cannot be converted (cm3/g, L/kg) and are left missing.

## Curves (one curve = one `Set`; provisional, see phslope/README.md)

- Sets by kind: {'ph_sweep': 1661, 'constant_ph': 1431, 'too_few_ph_levels': 33}.
- pH-sweep curves: 1,661; with conditions that vary inside the curve: 0; flagged unit_mismatch: 34; clean: 1,627.
- Clean curves: median 12 points, median pH span 5.60.
- Clean curves with a co-solute in the electrolyte (not plain background salt): 229; with CO2/carbonate: 1037.
- Clean curves reporting solids loading: 1627; total sorbate: 1627; temperature: 175.

## Task 0.4: electrolyte-signature fragmentation

73 (reference, mineral, sorbate) studies are split across more than one electrolyte signature. Because a curve is a Set, the split never cuts a curve in two; it only matters if signature were used to group curves. It is not: pairs are (mineral, sorbate) and the signature is kept as a reported column plus `has_cosolute`. Largest splits:

| reference | mineral | sorbate | n_signatures | n_curves | n_points | cosolutes |
|---|---|---|---|---|---|---|
| d01 | kaolinite | U(+6) | 5 | 29 | 480 | Citrate(-3); Humic acid; P(+5); S(+6) |
| d01 | quartz | U(+6) | 5 | 20 | 210 | F(-1); P(+5) |
| bm82 | goethite | Pb(+2) | 5 | 11 | 88 | S(+6) |
| d01 | ferrihydrite | U(+6) | 4 | 33 | 551 | Humic acid; P(+5); S(+6) |
| bm82 | goethite | Zn(+2) | 4 | 12 | 101 | S(+6) |
| bbs85 | kaolinite | Ra(+2) | 4 | 6 | 93 | S(+4) |
| bm82 | goethite | Cd(+2) | 4 | 9 | 80 | S(+6) |
| bm82 | goethite | Cu(+2) | 4 | 8 | 76 | S(+6) |

Most extra signature members are co-solutes (phosphate, sulfate, humic acid, a second sorbate), which change the chemistry, not tracer ions. Whether to exclude co-solute curves from the core library is an open question (OPEN_QUESTIONS.md).

## Known subset row counts (Task 0.1 check)

| mineral | electrolyte_sig | sorbate | expected | found | ok |
|---|---|---|---|---|---|
| goethite | Cl(-1)+Na(+1)+P(+5) | Se(+4) | 104 | 104 | True |
| ferrihydrite | N(+5)+Na(+1)+P(+5) | U(+6) | 105 | 105 | True |
| montmorillonite | Cl(-1)+Na(+1) | U(+6) | 66 | 66 | True |
| goethite | N(+5)+Na(+1) | U(+6) | 275 | 275 | True |

The spec quoted 205 rows for goethite-N(+5)+Na(+1)-U(+6). The raw group has 275 rows from 4 references; 205 was the count after `run_pipeline.py`'s I-varying-reference filter, so 275 is the correct raw check.

## Top pairs

| mineral | sorbate | n_curves | n_points | pH_span | n_references | n_curves_both_reported | passes |
|---|---|---|---|---|---|---|---|
| ferrihydrite | U(+6) | 60 | 982 | 7.85 | 9 | 60 | True |
| montmorillonite | U(+6) | 45 | 763 | 9.06 | 8 | 45 | True |
| hematite | Np(+5) | 49 | 739 | 8.30 | 6 | 49 | True |
| goethite | Se(+4) | 52 | 686 | 10.53 | 13 | 52 | True |
| hematite | U(+6) | 48 | 620 | 9.70 | 10 | 48 | True |
| goethite | Se(+6) | 47 | 604 | 8.13 | 8 | 47 | True |
| illite | Eu(+3) | 28 | 560 | 9.14 | 7 | 28 | True |
| kaolinite | U(+6) | 37 | 555 | 7.62 | 5 | 37 | True |
| quartz | U(+6) | 43 | 529 | 10.98 | 13 | 43 | True |
| goethite | U(+6) | 36 | 510 | 7.76 | 9 | 36 | True |
| montmorillonite | Ni(+2) | 14 | 507 | 10.06 | 3 | 14 | True |
| illite | Ni(+2) | 25 | 448 | 8.46 | 4 | 25 | True |
| hematite | Am(+3) | 33 | 432 | 8.38 | 2 | 33 | True |
| goethite | Oxalic acid | 34 | 406 | 10.86 | 9 | 34 | True |
| montmorillonite | Np(+5) | 22 | 395 | 9.19 | 5 | 22 | True |
| ferrihydrite | Se(+4) | 24 | 331 | 8.34 | 6 | 24 | True |
| montmorillonite | Eu(+3) | 13 | 319 | 10.87 | 6 | 13 | True |
| gibbsite | U(+6) | 16 | 274 | 8.40 | 5 | 16 | True |
| bentonite | U(+6) | 17 | 272 | 8.80 | 4 | 17 | True |
| ferrihydrite | Se(+6) | 26 | 259 | 7.60 | 7 | 26 | True |
| illite | Co(+2) | 12 | 235 | 8.70 | 2 | 12 | True |
| montmorillonite | Zn(+2) | 5 | 220 | 8.45 | 3 | 5 | True |
| alumina | Eu(+3) | 16 | 216 | 6.68 | 2 | 16 | True |
| illite | Cs(+1) | 13 | 214 | 8.66 | 2 | 13 | True |
| goethite | Ni(+2) | 17 | 203 | 7.95 | 5 | 17 | True |

Full table: `pair_table.csv`. Matrices: `matrix_curves.csv`, `matrix_references.csv`. Gap list (dense block 12 minerals x 12 sorbates): `gap_list.csv` (90 empty or thin cells).

## Descriptor templates

Written to data/descriptors/: mineral_descriptors_template.csv, sorbate_descriptors_template.csv. All descriptor columns are empty; Samuel fills them with cited sources.

## Next decision

Samuel confirms the curve definition (one curve = one Set) and the co-solute question before Stage 1. Stage 0 passes, so Stage 1 can start after that confirmation.
