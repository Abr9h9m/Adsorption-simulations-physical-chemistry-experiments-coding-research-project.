# pH-only slope library: results summary and next steps

Written 2026-10-13 from the contents of the project folder (Stage 0–3 reports, pooled-pair comparison, export tables, README, OPEN_QUESTIONS, thresholds, git log). I read every stage summary in full, looked at two figures (`stage3/p50_error_by_model.png`, `stage2/variance_shares.png`) and recomputed a few headline numbers from `stage1/curve_table.csv` (marked **[checked]**). I did not re-run any stage or review the per-curve diagnostic PDFs.

**Everything from Stage 2 on is labelled EXPLORATORY** in the reports, because Stage 1 missed its pre-set survival rule, the classes are not yet confirmed, the descriptor tables are empty and `thresholds.yaml` is not frozen. Nothing below is a confirmatory result.

---

## 1. Bottom line

1. **The data are smaller than we thought.** The file in use has **38,906 rows**, not ~80,000. The earlier "census" numbers in my pH-only design doc (105 pairs, ~27,700 rows) came from an old audit table and should be replaced by the Stage 0 numbers below.
2. **There is real structure, and it is mostly in the sorbate.** Sorbate class explains most of what differs between curves: it sets whether the edge rises (cations) or falls (anions) and how tall it is, and it shifts where the edge sits. Mineral class adds little once the sorbate is known.
3. **Predicting an unseen system's edge position is not working yet.** Held-out median error is **1.1–1.8 pH units** for every model, against a target of 0.5. No model beats the simple baselines. This is a real negative result for the "classes and properties predict the curve" idea as currently built.
4. **The target of 0.5 pH may be unreachable even in principle.** If you predict a curve's edge from the *same mineral–sorbate pair measured in a different paper*, the median error is still **about 0.6 pH [checked: 0.63]**. That is the data's own reproducibility ceiling. A fair goal has to be set relative to it.
5. **What is predictable today:** edge direction (rising vs falling) from the sorbate class alone is right about **98%** of the time, against 66% for a global average. Edge position to roughly ±1.2 pH is the best any current model does.
6. **Only 46.8% of curves survived Stage 1 QC** (target 80%), mostly because the edge falls in a gap in the data or its position is too uncertain. We continued with the 745-curve core library by choice.

---

## 2. Status by stage

| Stage | Question | Result | Verdict |
|---|---|---|---|
| 0 Census | Enough pairs with a full pH range and 2+ papers? | 76 pairs pass (need 60) | **PASS** |
| 1 synthetic | Do the fitters recover known curves? | median slope error 0.076 of range (limit 0.20) | **PASS** |
| 1 real | Do ≥80% of curves survive QC with a usable shape? | 546 of 1,166 census-set curves = **46.8%** | **FAIL**, continued as exploratory (Samuel, 2026-10-12) |
| Pooled (extra) | What if curves are pooled instead of fitted one by one? | pooling widens edges ~1.4× and mixes in paper offsets | exploratory finding |
| 2 classes | Do classes explain more than chance and more than study? | class share 60.8% vs study 24.0% for edge position; permutation p = 0.0005 | **PASS** (exploratory, unconfirmed classes) |
| 3 prediction | Can we predict a held-out curve better than baselines? | every model fails at every level | **FAIL** (exploratory) |
| 4 transformation, 5 report | | not started | — |

---

## 3. What each stage found

### Stage 0: the data
- 38,906 rows, 3,125 `Set`s, 334 references. Decision recorded: **one curve = one `Set`** (a Set is one plotted series in one paper, at constant conditions).
- 1,704 pH-sweep curves; **1,680 clean**. Median 12 points and a 5.6-unit pH span per curve.
- **76 mineral–sorbate pairs** meet the rule (≥50 points, pH span ≥4, ≥2 references). Best covered: ferrihydrite–U(VI) (60 curves, 9 references), montmorillonite–U(VI), hematite–Np(V), goethite–Se(IV), hematite–U(VI).
- The four earlier pipeline subsets reproduce their row counts (104, 105, 66) with one correction: goethite–nitrate+Na–U(VI) is **275** rows, not 205. The 205 was only the one reference that varies ionic strength.
- Electrolyte-signature fragmentation turned out to be harmless for curves (a Set is never split). It mostly reflects **co-solutes** (phosphate, sulfate, humic acid, a second sorbate): 237 of 1,680 curves. Kept and flagged.
- 1,052 curves have CO2 or carbonate reported; 657 rows have impossible pH and are ignored; 9,092 rows have no response.
- 85 empty or thin cells in the dense 12 × 12 mineral–sorbate block: this is the gap list for data expansion.

### Stage 1: slope curves
- Synthetic: fits recover rising and falling edges well (edge interval coverage 0.93–0.98). Bell and two-step curves are harder (coverage 0.55–0.68, so **edge intervals for smoother-fitted curves are too narrow**).
- Real: 745 of 1,680 curves are in the core library. Shapes across all processed curves: rising 799, falling 371, flat 236, bell 214, multi-step 27, unclassified 33.
- Where the census-set curves are lost: edge not bracketed (304), edge interval wider than 1 pH (277), too narrow a span (151), too few points (140). Diagnosis in the report: most losses have the edge inside a **sampling gap** (median gap 0.9 pH) or an edge-position interval of ~1.8 pH, not an edge outside the measured range (only 33 curves). Even a looser bracketing rule would give 55.8%, still a fail.
- 948 curves have logistic and smoother slopes that disagree beyond their uncertainty, so many curves are not simple S-shapes.

### Pooled-pair comparison (extra, exploratory)
- Pooling all points of a pair across papers, then fitting, gives edges **1.4× wider** than single-curve fits (median ratio 1.37–1.42; about 30% of pools above 1.5×). Pooled edge position shifts a median 0.2–0.3 pH.
- A resampling that keeps each paper together gives intervals **~2× wider** than resampling points. The ordinary point bootstrap is too optimistic whenever points from one paper are combined.
- About 22% of a pooled fit's leftover scatter lines up with papers.
- Takeaway: do not pool across papers and fit one curve. Fit per curve, or fit a model that has a paper effect.

### Stage 2: do classes matter?
Registration alone (aligning edge position, width and height) removes 86% of slope-shape variance. Edge-position variance splits as:

| Component | Share of edge-position variance |
|---|---|
| mineral class | 2.7% |
| sorbate class | 25.7% |
| specific mineral–sorbate pair | 32.4% |
| paper (study) | 24.0% |
| leftover | 15.2% |

- **Height** (how much the curve rises or falls) is **75.5% sorbate class**: rising cation edges versus falling anion edges.
- **Width** is mostly noise (48.5% leftover); weak class signal.
- **Shape beyond position, width and height (principal-curve scores)**: no class structure found; only the first component is resolved above its own uncertainty.
- Clustering on edge parameters matches sorbate class (permutation p = 0.0005) but not mineral class.
- Exploratory screen of 50 groupings: 10 pass the false-discovery correction. The strongest are sorbate charge form (48% of edge variance), sorbate redox sensitivity and "manganese-containing" mineral. Many mineral-property splits are duplicates of each other. The mineral property table has no sources and three rows that contradict the mineral's formula.
- **Caution on the p-values:** the within-paper permutation test can only use the 31 of 141 papers (217 of 576 curves) that contain more than one class, so it rests on few papers. The class-level intervals are wide because there are only 5–7 classes per side.

### Stage 3: held-out prediction (405 single-edge curves, 120 papers, 115 pairs)
- **Every model fails at every level** (leave one paper, pair, mineral or sorbate out): median edge error 1.1–1.8 pH; target ≤0.5.
- Nothing beats the best baseline by a margin that is clear. Differences against the sorbate-class average are small, and for unseen sorbates the property-based models are worse (1.8 pH) and overconfident (edge coverage 0.66).
- The **conditions-only** models (solids loading, total sorbate, ionic strength, carbonate) are no better than the global average.
- **Shape is where classes help:** with the sorbate-class average, rising-vs-falling is correct for about 98% of held-out curves (global average 66%) and slope sign for roughly 84% (vs 57%).
- **Why Stage 2 passed and Stage 3 failed (the central point):** Stage 2's "class" share includes the specific-pair component (32%). That is real, but it is the part that **does not transfer to an unmeasured pair**. The part that transfers (sorbate class) cuts squared edge error by only about 14% (per the report's analyst note).
- **Noise ceiling:** predicting a curve's edge from the same pair in other papers gives ~0.6 pH median error (the report says 0.60; I get 0.63, RMSE 1.22 **[checked]**) for the 287 curves whose pair appears in more than one paper. The 118 curves whose pair appears in only one paper have nothing better than the class mean (1.73 pH).
- Spec baseline that decides novelty (edge from PZC and first hydrolysis constant) **did not run**: the descriptor tables are empty.

### Other things I checked from the curve table **[checked]**
- 405 single-edge core curves: 267 rising (median edge pH 5.8), 138 falling (median 7.4). Overall edge SD 1.93 pH.
- Edge SD within a sorbate is about 1.0–1.2 pH for the big ones (U(VI) 1.17, Se(IV) 1.21, Ni(II) 1.20, Np(V) 1.05); smaller for Am(III) 0.47 and Ra(II) 0.38.
- Only **43 of 115 pairs** have curves from 2 or more papers. Median spread of a pair's paper-means is 0.55 pH.
- Within a sorbate, the edge residual correlates +0.18 with log solids loading and about 0 with total sorbate and ionic strength. Curves with a co-solute sit ~0.3 pH higher than those without. These are weak, uncontrolled correlations, a hint for where to look, not a finding.

---

## 4. How I read it

- **The slope-library idea is not dead; the prediction target was set too tight.** The data's own reproducibility is ~0.6 pH, so 0.5 pH is below what even a repeat experiment would give. A sensible framing has three tiers: (a) edge direction and height from sorbate; (b) edge position to about 1 pH; (c) full curve. Tier (a) already works.
- **The sorbate is the lever; the mineral is not (yet).** To get tier (b) we probably need numeric sorbate properties (hydrolysis constants, charge) and mineral surface properties (PZC), not class labels. That is the experiment that has not run.
- **Specific pairs matter more than classes.** The 32% pair component is large. This favours a **library lookup** (use the measured pair if it exists, with a paper-aware uncertainty) over a class-based guess, and a model that borrows strength within a pair across papers.
- **The two-step approach (fit each curve, then regress the fitted edge) throws away 55% of curves and treats noisy edges as exact.** A single model fitted to the raw points, with random effects for pair and paper, would use every curve and carry uncertainty through. This is probably the biggest methodological improvement available.
- **Honest paper status:** a methods/data-quality paper (what is and is not recoverable from compiled sorption data, the reproducibility ceiling, the pooling bias, the library as a table) is realistic. A "we can predict sorption from mineral and sorbate class" claim is not supported.

---

## 5. Caveats and things to double-check

1. **Choices made by Claude Code, not you:** QC thresholds, shape rules (flat if change <0.15; two steps ≥1.5 pH apart), sorbate schemes (hard/soft, charge form), the mineral-class assignments (`confirmed: false`), the ionic-strength bands. All were fixed before results, but none is confirmed. Open questions 13, 15 and 17 in `OPEN_QUESTIONS.md`.
2. **The ~0.5 pH threshold was proposed, not agreed.** Changing it now is allowed (thresholds are not frozen) but must be recorded as a decision made *after seeing that the data's own floor is ~0.6 pH*, with Dr. Black's agreement. Do not hide that.
3. **Stage 2 and Stage 3 use different curve sets** (576 core edge curves vs 405 single-edge curves). Both are stated in the reports, but the numbers are not directly comparable.
4. **The inverse-variance curve error rewards flat predictions.** The report added an unweighted version and shape/sign accuracy. Read all three together.
5. **Mineral property table is uncited** and has errors (open question 16: hematite missing, calcite, maghemite and corundum rows contradict their formulas). Mineral-property results are screening hints only.
6. **Carbonate flag counts air-equilibrated systems** (1,052 curves), which blurs the effect it is meant to isolate (open question 10).
7. **Smoother-based edge intervals are too narrow** (~55–70% coverage), which understates uncertainty for bell and two-step curves.
8. **Stale text elsewhere:** the Project Update doc, the Lab Meeting doc, `CLAUDE.md` and my own pH-only design doc still carry old claims (pipeline re-run pending, goethite–Se(IV) as an ionic-strength candidate, ~80k rows, 105 pairs). See next steps.
9. I did not review the per-curve diagnostic PDFs. The worst held-out errors (up to ~5.8 pH, e.g. silica `rbab91_f5c`, goethite `lyt14_t5a/b`) deserve a look for data-entry or unit problems before being treated as model failures.

---

## 6. Next steps

### A. Decisions (this week; Samuel and Dr. Black)
| # | Decision | Recommendation |
|---|---|---|
| A1 | What "close" means | Replace the single 0.5 pH rule with the three tiers above, and report every model as a fraction of the **noise ceiling** (same pair in another paper, ~0.6 pH) alongside the global-average baseline. Record the rationale. |
| A2 | Confirm class assignments (open question 13) | Review `classes.yaml`; decide on manganese oxides, micas, humic acids, actinides, Cs(I). Set `confirmed: true` only before any confirmatory run. |
| A3 | Is the slope library a deliverable on its own? | Yes: it is a table with uncertainty and it works regardless of Stage 3. |
| A4 | Carbonate definition and ionic-strength bands (Q10, Q17) | Choose before the next variance run. |
| A5 | Freeze `thresholds.yaml` | Only after A1; then Stage 3 can be re-run as confirmatory. |

### B. Science (weeks 2–4)
1. **Fill the descriptor tables with cited values** (Samuel; Claude Code must not guess): PZC (low/high with source), first hydrolysis constant, charge/oxidation state, surface area. Start with the pairs that have the most curves. This unlocks the decisive baseline and the "properties" feature set.
2. **Add a "noise-ceiling" report** to Stage 3: for each held-out curve, the same-pair-other-paper error where available, and a normalised score (how much of the gap between global average and ceiling a model closes).
3. **Build a hierarchical model on the raw points** (edge position, width, height each with sorbate, mineral, pair and paper effects) instead of two-step regression. This uses all curves, including the 55% that failed QC, and gives honest intervals. Compare against the two-step results on the same held-out splits.
4. **Condition-adjusted edge:** model edge position within a pair against log solids loading, total sorbate, co-solute and carbonate before comparing across systems. The pooled run and the +0.18 solids-loading correlation suggest this will absorb part of the "paper" share.
5. **Outlier audit:** open the 20 worst held-out curves, check units, pH, response definition and curve type; flag or fix data problems; re-run.
6. **Sorbate-first model:** predict direction, height and edge position from sorbate properties alone (charge, redox state, hydrolysis constant), then add mineral PZC. Test leave-one-sorbate-out with the noise ceiling as reference.
7. **Better intervals for smoother-fitted curves** (open question 14): undersmoothing bootstrap or a paper-level bootstrap; re-check coverage on synthetic data.
8. **Stage 4** (transformation model) only after items 1–3 show tier (b) is reachable; otherwise write the negative result.

### C. Data (parallel track)
- Use the gap list (85 empty or thin cells) and the 118 single-paper curves to choose which pairs to expand first. A pair with a second independent paper is worth much more than a tenth curve from the same paper.
- Confirm which dataset file is current and where Abraham gets it (open question 8; three copies exist and were not compared).

### D. Web interface
- The `export/` tables (curves, slope grid, observations, pair summary) exist with `schema_version = 1` and `library_status = exploratory`. Wire them into the Curve library view (R9). The interface must show the status and the paper-level uncertainty, and should flag pairs that have only one paper.

### E. Housekeeping (small, do now)
- Update **CLAUDE.md**, the **Project Update** doc, the **Lab Meeting** doc and my **pH-Only Slope Library** doc: real run is done; goethite–Se(IV) is not an ionic-strength candidate; dataset is 38,906 rows; census is 76 pairs; Stage 1 failed and Stage 2–3 are exploratory. I can do these edits if you say so.
- Add the noise ceiling and the three-tier criteria to `phslope/README.md` and `thresholds.yaml` comments once agreed.
- Commit the new `OPEN_QUESTIONS.md` answers; keep the large `draws.npz` and `diagnostics.pdf` out of git (already ignored).

### F. Suggested schedule (weeks 2–7 from 2026-10-12)
| Week | Focus |
|---|---|
| 2 | A1–A4 decisions; descriptor tables begun; outlier audit; update stale docs |
| 3 | Noise-ceiling report; condition-adjusted edge; Stage 3 re-run with descriptors (exploratory) |
| 4 | Hierarchical model on raw points; compare with two-step |
| 5 | Sorbate-first model; freeze thresholds; confirmatory Stage 3 run if criteria are agreed |
| 6 | Stage 4 or negative-result write-up; web interface library view |
| 7 | Final report and a plain-English summary for Dr. Black |

---

## 7. For Dr. Black: plain-English summary

We turned each lab experiment into a curve of "how much sticks as pH changes" and measured how fast it changes. About 1,700 curves from the compiled dataset are usable; 745 are clean enough to trust.

The biggest difference between curves is the **sorbate** (the thing being absorbed). Whether sorption goes up or down with pH, and by how much, is mostly set by the sorbate, and we can guess that direction correctly about 98% of the time without knowing anything about the mineral. The mineral type adds little on its own.

Guessing **where** the curve turns for a system nobody has measured works only to about 1 to 1.5 pH units. That is no better than simple averages. A fair comparison matters here: when two different labs measured the same mineral and sorbate, their curves still differ by about 0.6 pH, so a prediction accurate to 0.5 pH would be better than a repeat experiment. We suggest setting the goal relative to that, and adding real chemical properties (surface charge of the mineral, how readily the sorbate reacts with water) rather than category labels. Those values still need to be filled in from published sources.

Questions for you: what accuracy would count as useful; whether you agree with the mineral and sorbate groupings we proposed; and which published tables you prefer for the mineral surface charge and sorbate reaction constants.

---

## 8. File index (project folder)

| What | Where |
|---|---|
| Stage 0 summary and tables | `reports/phslope/stage0/` |
| Stage 1 summary, curve table, QC plots, per-curve PDF | `reports/phslope/stage1/` (library in `library/`) |
| Synthetic check | `reports/phslope/stage1_synthetic/` |
| Pooled-pair comparison | `reports/phslope/pooled/` |
| Stage 2 (variance split, class tests, exploratory groupings) | `reports/phslope/stage2/` |
| Stage 3 (metrics, paired differences, worst curves) | `reports/phslope/stage3/` |
| Web-interface tables | `export/` |
| Decisions and open questions | `phslope/README.md`, `OPEN_QUESTIONS.md` |
| Frozen-or-not thresholds | `phslope/config/thresholds.yaml` (`frozen: false`) |
