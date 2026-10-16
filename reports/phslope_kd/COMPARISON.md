# Kd instead of fraction sorbed: what changed (2026-10-16, EXPLORATORY)

Every stage (0-3, pooled, export) and every experiment (E0-E23, M-checks, F on development papers) was rerun with
**Kd = 1000 x Sorbed_val / (Mineral_val x Aq_val)** (L/kg, solids in g/L) as the sorption parameter. Command:
`PHSLOPE_RESPONSE=kd python -m phslope.rerun_all` (commit `d468a46`; 29 of 29 steps ran without error,
`rerun_logs/RERUN.md`). The fraction-sorbed results in `reports/phslope/` are untouched. All tables side by side:
`comparison/COMPARISON_TABLES.md`; figures `comparison/fig*.png`. The 24 locked papers were not opened.

## How Kd was used

- Log-scale analyses (E1, E8, E11-E17, E21-E23, F) use log10 Kd where they used log10 K.
- Analyses built on S-shaped fits (Stages 1-3, E5, pooled) use Kd / (Kd + 1000): the fraction that **would** be
  sorbed at a standard 1 g/L of mineral. An "edge" is then the pH where Kd = 1000 L/kg.
- Analyses that already converted to Kd themselves (the "solids-normalised edge", E9, E12, E14, E17 strength) do
  not divide by solids a second time.
- Rows need solids in g/L to have a Kd, so the data shrink a little: 1,627 clean curves instead of 1,680, 72
  passing pairs instead of 76, 459 instead of 535 curves in the main validation set. Comparisons below are
  therefore on slightly different curve sets.
- Within one curve the solids amount is fixed, so log Kd and log K differ only by a constant: **slopes cannot
  change much** (E11 confirms); edges, levels and anything comparing curves at different solids can.

## Headlines

| Question | Fraction sorbed | Kd | What it means |
|---|---|---|---|
| Does mineral amount still change anion (falling-edge) sorption? E17 | +0.95 [0.53, 1.37] | **-0.03 [-0.34, 0.28]** | Kd removes the solids effect for anions completely: anion Kd is the same at any mineral amount |
| ... and cation (rising-edge) sorption? E17 | +0.33 [0.12, 0.53] | **-0.24 [-0.40, -0.08]** | Kd over-corrects for cations: cation Kd falls as more mineral is added (a "particle-concentration effect") |
| Shuffle-the-solids placebo, E23 (should be ~0.05) | 0.48 (failed; needed the within-between fix) | **0.04 (passes as is)** | The confounding E23 found came from solids sitting inside the response; Kd removes it |
| How much of the edge scatter solids explain inside a pair, E9 | R2 0.24 | 0.05 | Most of the solids-related scatter was the phase ratio, which Kd takes out |
| Edge prediction for a new paper, E1 (median error, pH) | 0.88 | **0.75** | Kd edges are more predictable |
| Plain average of other papers, B0 | 0.99 | **0.82** | Simple baselines gain most |
| Final model (E1 + solids split + E8), F | 0.80 | 0.77 | The extra terms no longer help (E1 alone 0.75): their job was mostly fixing solids |
| Gradient boosting, held-out per-curve error, E15 (grouped) | 0.52 | 0.47 | Still the best model; random splits still overstate skill ~2.5x |
| Conditions vs no conditions in gradient boosting, E15c (edge, pH) | 0.81 vs 1.09 | 0.93 vs 1.02 | Experimental conditions carry far less information once Kd is used (most of it was solids) |
| Salt effect, outer-sphere metals, E8 (pH per tenfold salt) | +0.79 [0.32, 1.25] | **+1.22 [0.44, 2.01]** | Stronger, still found |
| Salt effect, oxyanions, E8 | -0.30 [-0.46, -0.13] | -0.44 [-0.73, -0.15] | Stronger, still found |
| Overall salt effect is null, E14 | 97% of specifications | 98% | Unchanged |
| Heterogeneous sites (Freundlich exponent), E12 | 0.66 [0.49, 0.82] | 0.60 [0.43, 0.77] | Unchanged: sites are not all alike |
| Higher loading lowers Kd, E14 H4 | 83% of specifications | 89% | Slightly more robust |
| New mineral / new sorbate prediction, E16 | 1.50 / 1.80 pH | 1.38 / 1.57 pH | Still no better than class means |
| Core library (Stage 1) | 745 curves (46.8% survival; fails 80%) | 683 (43.7%; fails) | Unchanged verdict; more curves look "flat" at high solids |
| Stage 2: share of edge variance from sorbate class | 0.26 | 0.13 | Sorbate class matters less once solids are removed; pair and residual shares grow |
| E1 level variance between pairs | 0.084 | 0.011 | Most level differences between mineral-sorbate pairs were solids differences |

E14 H2 and H3 ("rising solids slope < 0", "falling solids slope > 0") drop to 0%. This is expected: those are
fraction-space hypotheses, and in Kd space the falling slope is ~0 and the rising slope has the opposite sign.

## For Dr. Black (plain English)

We switched from "what fraction of the contaminant stuck" to "how strongly it sticks per gram of mineral" (Kd).
The fraction depends on how much mineral was in the bottle; Kd is meant not to. The rerun shows that for
negatively charged contaminants (selenite, arsenate and similar) Kd really is independent of the amount of
mineral, so it is the fairer number to compare between papers. For positively charged metals it over-corrects:
their Kd goes down when more mineral is added, a known effect in the literature. With Kd, predicting where the
sorption edge falls in a new paper improves from about 0.9 to 0.75 pH units, and simple averaging of other papers
improves the most, because much of the paper-to-paper disagreement was just different amounts of mineral. The
salt and site-heterogeneity findings stay the same or get stronger.

## Caveats

- The Kd edge (pH where Kd = 1000 L/kg) is a different quantity from the fraction-sorbed edge, and the curve sets
  differ (curves without solids in g/L drop out), so error numbers are not a like-for-like contest.
- E1 coefficients `solids_r` / `solids_f` are on E1's own scale; the cleanest solids test is E17.
- Kd uses the reported Sorbed and Aq without the 10% mass-balance screen the fraction run applied to K
  (E0: 99.9% of rows pass it anyway).
- The 1 g/L reference squashes curves measured far from 1 g/L (more "flat" shapes); log-scale results do not
  depend on that choice.
