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
