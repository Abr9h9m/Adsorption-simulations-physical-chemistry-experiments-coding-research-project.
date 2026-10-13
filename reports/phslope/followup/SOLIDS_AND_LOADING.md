# Solids correction and sorbate-to-mineral loading

2026-10-13. **EXPLORATORY.** Script: `solids_loading.py`; tables and figure `solids_loading_figure.png` alongside.

## 1. Were we correcting for the amount of mineral? No.

What the code does (`response.py`, applied in `phslope/load.py`):

- **Response used everywhere:** `fraction sorbed = Sorbed_val / Sorbate_val`, both converted to mol/L. That divides by the **sorbate added**, not by the mineral. Solids loading (`Mineral_val`, converted to g/L) is read and stored, but never used in the response.
- **The alternative mode** (`log_kd = log10(Sorbed_val / Aq_val)`) is also not corrected: it is a dimensionless ratio of sorbed to dissolved, which still contains the solids concentration. A per-gram distribution coefficient needs one more division by solids (g/L). `log_kd` was computed but not used in Stages 1–3.
- **Evidence the units are at least consistent:** 1,680 of 1,704 pH-sweep curves have fraction-sorbed values inside 0 to 1, so `Sorbed_val` is per litre of suspension (as the code assumes), not per gram.

Why it matters: for simple (linear) sorption, fraction sorbed = Kd·S / (1 + Kd·S), where S is grams of mineral per litre. Doubling the mineral moves the whole curve, so the edge position depends on the solids used, even if the chemistry is identical. That is the solids-loading effect found in the pooling follow-up.

## 2. What correcting for solids does (edge in "Kd space")

I rebuilt the response from what we have, assuming mass balance (dissolved = added − sorbed): `K = f/(1−f)`, `Kd = K / S`. For each rising or falling curve I fitted a straight line of `log10 K` against pH over points with 3–97% sorbed. Its slope is how steeply the edge rises, and the pH where `K = 1` is the usual 50% edge. The solids-corrected edge is the pH where `Kd = 1 L/g`.

1,143 curves have solids and total sorbate; 840 give a clean line (right direction, R² ≥ 0.5, crossing near data); 622 of those sit in 60 groups with at least 2 papers (126 papers).

**Edge shift per tenfold more solids** (within a mineral–sorbate group, errors clustered by paper):

| Edge | As measured | After assuming Kd does not depend on solids |
|---|---|---|
| falling (anions; 9 groups, 36 papers) | **+1.23 pH** (0.92 to 1.54) | **−0.25 pH** (−0.82 to +0.32), effect gone |
| rising (cations; 51 groups, 93 papers) | −0.49 pH (−0.87 to −0.12) | **+0.92 pH** (0.69 to 1.14), overcorrected |

Reading:
- **Falling edges collapse.** Correcting for solids removes the effect, which says anion sorption behaves like simple, linear sorption with respect to the mineral amount.
- **Rising edges do not.** The linear model predicts a shift of about −1.5 pH per tenfold (the median 1/|slope| is 1.49). The data show only −0.49. So with more solids, cations bind *less per gram* than a constant Kd predicts. A "particle concentration effect" (apparent Kd falling as solids rise) is a known phenomenon in the sorption literature and is a candidate; I have not tested it here and other explanations (co-varying design choices, solid–liquid separation) are possible.
- **Net result:** applying the simple correction does not reduce disagreement between papers (median paper-to-paper edge difference 0.89 pH as measured, 1.06 pH corrected; median within-group SD 0.93 vs 0.87). The right fix is therefore **not** a blanket division by solids but solids as a covariate with its own, direction-specific sign.
- The edge steepness in Kd space is a useful new curve parameter: median |d log K / dpH| is 1.11 for U(VI) (rising), 0.6–0.7 for Se(IV), Se(VI), Am(III), Eu(III), 0.4–0.5 for Ni(II), Np(V).

## 3. Does the ratio of sorbate to mineral change the curve (nonlinearity)?

**Loading** = mol of sorbate added per gram of mineral (total sorbate / S). If sorption is linear, Kd at a fixed pH does not depend on loading. If the surface starts to fill, Kd drops. I evaluated each curve's `log Kd` at the pair's reference pH (the pair's median 50% edge, only inside the fitted pH range) and compared curves of the same pair across loadings: 539 curves, 50 groups, 117 papers, loading from about 10⁻¹³ to 10⁻³ mol/g.

| Test | Effect on log10 Kd per tenfold loading | 95% interval |
|---|---|---|
| all curves | −0.03 | −0.14 to +0.08 |
| rising (cations) | +0.02 | −0.11 to +0.15 |
| **falling (anions)** | **−0.22** | −0.31 to −0.12 |
| **within the same paper only** (313 curves) | **−0.18** | −0.26 to −0.10 |

- **Regime split.** Kd is flat across most of the range (binned means within ±0.1 log units up to about 10⁻⁴ mol/g) and falls by about **0.45 log units** in the top bin (above 10⁻⁴ mol/g; 45 curves, 13 groups). A piecewise-linear fit with one breakpoint improves on a straight line (AIC −601 vs −578): slope +0.03 below, −0.42 above. **The breakpoint itself is poorly located** (90% interval −9 to −4 in log10 mol/g); the evidence sits in the top bin.
- **Plateau height** falls slightly with loading: −0.018 in fraction sorbed per tenfold (−0.028 to −0.007); −0.046 for falling edges.
- **Edge position after solids correction:** unaffected by loading for rising edges; falling edges move **−0.57 pH** per tenfold loading (−0.86 to −0.27).
- **Regime labels** (per curve, in `B_curve_regimes.csv`): low loading (linear) 320 curves, transition 141, high loading (saturating) 78, using the breakpoint ±0.5 decade.

So yes, the ratio matters, but only at high loading, and mostly for anion edges. For most curves the system is in the linear regime.

## 4. Caveats

- `K = f/(1−f)` assumes dissolved = added − sorbed. The raw `Aq_val` column was not available here (the dataset sits outside the project folder). It should be used where reported and checked against this assumption.
- Only points with 3–97% sorbed enter the line fit, so a crossing may be an extrapolation. I require it to sit near the measured pH range, but this drops about a quarter of curves (1,108 → 840).
- Loading per gram is not loading per surface site. The saturation threshold should depend on surface area and site density (still empty in the descriptor tables). Differences between minerals in capacity are partly controlled by comparing within a pair, but not removed.
- High-loading evidence rests on 45 curves in 13 groups. Treat as a lead, not a result.
- No multiplicity correction; exploratory throughout. The explanation for the rising-edge result is a hypothesis.

## 5. What to do with this

1. **Add `log_kd_per_g = log10(Sorbed/Aq) − log10(S)`** to the loader (use reported `Aq_val`; fall back to mass balance and flag it). Keep fraction sorbed too.
2. **Use the line in Kd space as per-curve parameters:** steepness (log K per pH) and log Kd at a reference pH. They are more comparable across papers than the edge position, because solids drops out for falling edges and is a smaller issue elsewhere.
3. **Put solids and loading into the hierarchical model** with separate coefficients for rising and falling edges, and a loading-regime term (low vs high) rather than assuming one linear effect.
4. **Add the loading regime as a flag** to the library and to the web interface filters; hide or mark the high-loading curves when comparing pairs.
5. **Re-run the held-out test** (conditions-matched vs plain average) with these parameters to see if they improve on the 0.25–0.44 pH errors.
6. **Get the raw file into the project folder** to verify mass balance against `Aq_val`, and fill the surface-area and site-density columns so loading can be expressed per site.

## Files

`solids_loading_figure.png`; tables: `kd_line_fits_all.csv` (per-curve line fit), `A_edge_spread.csv`, `A_edge_spread_solids_vary.csv`, `A_solids_coefficient.csv`, `A_slope_by_sorbate.csv`, `B_loading_slope.csv`, `B_piecewise.csv`, `B_binned_logKd.csv`, `B_curve_regimes.csv`, `B_plateau_vs_loading.csv`, `B_edge_vs_loading.csv`, `RUN_INFO.json`.
