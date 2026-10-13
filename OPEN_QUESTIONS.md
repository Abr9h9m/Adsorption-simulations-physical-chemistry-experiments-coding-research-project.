# Open questions (pH-only direction)

Questions whose answer would change the scientific meaning of a result. Work continues with the documented default until each is answered. Copied from `PH_ONLY_DEV_SPEC.md` §12, with what Stage 0 found added.

1. **What do `Set` and `SetID` identify?** *Found:* `Set` = one plotted series in one paper; `SetID` = row counter. Every pH-sweep Set has constant conditions. **Decided (Samuel, 2026-10-12): one curve = one Set.**
2. **Is there a solids-loading column?** *Found:* yes, `Mineral_val` + `Mineral_units`. 1,666 of 1,680 clean curves report it. Units are mixed: g/L, mg/mL and mg/L are converted; m2/L (311 rows) is kept separately; cm3/g and L/kg (18 rows) cannot be converted. *Open:* should m2/L loadings be converted to g/L using the mineral's surface area once descriptors exist?
3. What does "close" mean for Dr. Black: edge position within 0.5 pH, or a whole-curve error? Confirm `thresholds.yaml` before Stage 3.
4. Final class definitions for minerals and sorbates (Dr. Black). `classes.yaml` has the starting class names and no assignments yet.
5. Preferred sources for PZC, surface area and first hydrolysis constants.
6. Is the slope library itself, published as a table with uncertainty, a deliverable regardless of the Stage 3 outcome?
7. How should conditions be handled: restrict comparisons to similar loadings, or model the dependence?
8. Where is the complete dataset kept for collaborators (Abraham)? The file in use is `C:\Users\itzju\sc.dataset.csv` (38,906 rows, dated 2025-05-02). Copies also exist in `Downloads\`, `NoVEL Project\` and `python things\`; whether they are identical was not checked.
9. **New: co-solute curves.** 237 of 1,680 clean curves have something besides background salt in the electrolyte (carbonate, sulfate, phosphate, humic/fulvic acid, a second sorbate). **Decided (Samuel, 2026-10-12): keep and flag (`has_cosolute`); Ca(+2) and Mg(+2) count as plain background salt.**
10. **New: carbonate.** 1,052 clean curves have CO2 or C(+4) present. This flag counts any reported CO2(g) above zero, which includes air-equilibrated systems. Should air-equilibrated systems count as carbonate-bearing for the variance-split covariate?
11. **New: dataset size.** The handoff and spec say ~80k rows; this file has 38,906. **Answered (Samuel, 2026-10-12): no; this is the current file.**
12. **New: the 205-row count.** The spec quotes 205 rows for goethite–N(+5)+Na(+1)–U(+6). The raw group has 275 rows from 4 references; 205 is exactly reference t83, the only one of the four that varies ionic strength (3 levels), i.e. the count after `run_pipeline.py`'s I-varying-reference filter. The test uses 275. Confirm that's the intended check.
13. **New (Stage 2 blocker): review the proposed classes.** `phslope/config/classes.yaml` assigns every mineral and sorbate in the data to the spec's starting classes, with `confirmed: false`. Points to check: (a) manganese oxides (birnessite, vernadite, …), titanium oxides, apatites, zeolites and feldspars are all `other`. Should Mn oxides get their own class? (b) Micas and chlorite are put with `clay`. (c) Humic and fulvic acids are put with `organic_acid`. (d) Actinides are `actinide` whatever their charge (so U(VI) and Am(III) share a class). (e) Cs(+1) is `other` because the list has no monovalent class. (f) What is the sorbate `COM`? Set `confirmed: true` only after Dr. Black agrees; classes must not change after Part B results are seen.
14. **New: smoother-based edge intervals are too narrow.** On synthetic curves the 95% bootstrap interval for the edge of bell and two-step curves (fitted by the smoother) contains the truth only ~55–70% of the time; logistic intervals are close to 95%. Options: accept and report (current), widen with an undersmoothing bootstrap, or use a different interval method. Matters for Stage 3 interval coverage.
15. **New: shape-rule settings were Claude's choices.** `config.yaml → shape`: a curve is flat if the fitted response changes by < 0.15; a rise or fall must change it by ≥ 0.15; two steps must be ≥ 1.5 pH apart with the slope dropping below 30% between them. Fixed before any real-data Stage 1 result. Confirm or change before results are interpreted.
16. **New: the mineral property table (`phslope/mineral properties.csv`).** (a) What do the codes `TO` (46 cells), `O` (24) and `FO` (7) mean? Current default: only `T`/`F` are used; the others count as missing. (b) Three rows contradict the mineral's formula and are left out of every property-based grouping until corrected: Calcite (Carbonate minerals = F), Maghemite (Manganese-containing = T, Iron-containing = F; maghemite is γ-Fe2O3), Corundum (Framework silicates = T; corundum is Al2O3). Other rows were not checked cell by cell. (c) **Hematite has no row** (232 curves in the data), so it is missing from every property grouping. (d) The row `?-MnO2` lost its first character (probably δ); it matches nothing in the data. (e) The table has no source column; spec section 8 asks for a source for every descriptor value. (f) Several columns (radiation resistance, thermal stability) have no obvious link to sorption; they are screened anyway, with FDR correction, as you asked.
17. **New: proposed exploratory schemes (`phslope/config/schemes.yaml`).** Sorbate schemes (charge form, element group, hard/soft acid class, redox sensitivity) and ionic-condition schemes (ionic-strength bands < 0.01, 0.01–0.1, > 0.1 M; background anion; carbonate; co-solute) were written by Claude before any Stage 2 result. They are exploratory and never used for the Stage 2 go/no-go. Check: the hard/soft assignments (only Cd(+2) is "soft"), whether actinyl ions belong apart from other actinides, and the ionic-strength band edges.

## Improvement program (PH_ONLY_TEST_PROTOCOL.md), status 2026-10-13

Decisions from protocol section 8 (defaults in force until answered):

| ID | Decision | Status |
|---|---|---|
| D1 | Lock 20% of papers as a final test set | **Default applied**: 24 of 120 papers locked (seeded, stratified), `phslope/config/locked_test_papers.txt`, committed before any experiment. Not opened. |
| D2 | Program success criteria | Default (protocol section 7) in force; not yet evaluated (needs the locked look). |
| D3 | Relax the Stage 1 survival rule in favour of the E5 rule | **Needs Samuel and Dr. Black.** E5's slope-based rule keeps 93% of development census curves (Stage 1 rule: 36%) with a validated median edge error of 0.11 pH. Default: do not relax; both are reported. |
| D4 | Who fills E3 verdicts, E6, E9, E10 tables | Default: Samuel for E6; Abraham for E9, E10. Templates and `DATA_ENTRY_PRIORITY.csv` (top 40 references) are ready. |
| D5 | Sources for pKa, hydrolysis and carbonate constants | **Open.** E6 and the DIC part of E7 wait. |
| D6 | E7 step 2 (speciation software) | Default: no. |
| D7 | Raw dataset in the project folder | The file at `C:\Users\itzju\sc.dataset.csv` is reachable; E0.1 ran on it. Copying it in is still useful for Abraham. |

New questions raised by the experiments:

18. **E3 outlier verdicts.** `reports/phslope/experiments/E3/outlier_review.csv` lists 62 curves (worst held-out errors, largest E1 errors, data flags) with pages in `outlier_pages.pdf`. Fill `reviewer`, `verdict` (data error / real chemistry / different material / unclear), `notes`. Sensitivity runs wait for this.
19. **Duplicates.** E3 found 28 cross-paper near-copies; papers linked by copies are now one leave-out unit. Check a few in `duplicate_pairs.csv`: are they re-published data, or a compilation artefact?
20. **Paired statistic (clarified after the first E4 run).** "Paired 95% interval" now means the interval of the difference of medians. The first E4 run used the median of per-curve differences, which is 0 when most curves tie. Both runs are in the registry. Confirm this reading.
21. **E1 acceptance is on the point comparison.** E1 beats B3 on median edge error (0.88 vs 0.96 pH) as the rule requires, but the paired interval includes zero. Should the rule have required the interval to exclude zero? (If so, E1 would be REJECTED on that criterion; record any change as a new exploratory decision.)
22. **E8 sign for oxyanions.** Within papers, more salt moves oxyanion edges to LOWER pH (-0.30 pH per decade): sorption decreases with salt for anions too. Plausible chemically (outer-sphere anion complexes), but worth a literature check before it is written up.
23. **Surface area in the dataset.** E9 used the `MineralSA` column of the compiled dataset (method not recorded). Should E9 wait for the human-checked `study_materials.csv` instead, or is the dataset value acceptable with that caveat?
