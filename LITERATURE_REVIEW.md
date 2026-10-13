# Literature review: chemical explanations for our discrepancies, and prior art for the paper ideas

2026-10-13. Prepared for Samuel Uwechue; written so Dr. Black (non-specialist) can follow the chemistry.

**How to read the evidence tags.** Every source is tagged by how much I actually read:

- **[read]**: I fetched the abstract or page and the statement below is from it.
- **[title only]**: a search returned the title/link; I did NOT read the content. The chemistry is general background I am confident of, but the paper is not confirmed to say it. Open it before citing.
- **[not reached]**: fetch was blocked (PubMed CAPTCHA, the OECD-NEA report returned "robots disallowed"). Nothing from those is asserted.

Novelty claims below are **my reading of a short search, not a systematic review**. Samuel and Dr. Black must confirm novelty before any paper claim.

---

## 0. Most important finding: this has been done in part, by the likely owner of your dataset

- **L-SCIE** (LLNL Surface Complexation/Ion Exchange database) is a FAIR community database of digitized sorption data with unit conversion, built to support parameter estimation and ML. Its first use was U(VI) on quartz; the authors found a multisite model **with carbonate surface species** fit the compiled data best. [read, abstract] [Community Data Mining Approach for Surface Complexation Database Development, Environ. Sci. Technol. 56(4) (DOE PAGES)](https://www.osti.gov/pages/biblio/1866540-community-data-mining-approach-surface-complexation-database-development)
- **L-SURF** (Chang, Zavarin, Beverly, Wainwright; LLNL/LBNL): a chemistry-informed random forest on PHREEQC speciation features, trained on L-SCIE (page states >27,000 raw points: Kd, percent sorbed, surface excess, conditions), shown for U(VI) on quartz and montmorillonite. [read, project page] [A Chemistry-Informed Hybrid ML Approach to Predict Metal Sorption to Mineral Surfaces](https://ess.science.energy.gov/?p=12179)
- **Confirmed by Samuel (2026-10-13): `sc.dataset.csv` is the LLNL L-SCIE dataset.** It has 38,906 rows; the L-SCIE page quotes ~27,000 raw points, so this is presumably a later release (record the version/date in the manifest).

**What this means for novelty.** "ML on compiled sorption data" is not new. What I did not find in my search is a **pH-only, curve-level slope library with leave-one-paper-out transfer and an explicit paper-effect noise ceiling**. L-SURF is a point-wise, speciation-feature model, with demonstration on U(VI) only. Your angle (curve shape/edge as the unit, cross-paper reproducibility quantified, a modular query interface) looks distinct, but verify against the L-SURF paper itself and the other L-SCIE papers (see Gaps).

---

## 1. Discrepancy-by-discrepancy: is there a known chemical reason?

| # | What we see | Known chemistry (plain English) | Evidence status |
|---|---|---|---|
| 1 | Papers disagree on edge position by ~0.9 pH even for the same mineral–sorbate pair; plain cross-paper average only reaches ~0.6 pH | Each lab uses a different solid (synthesis route, crystallinity, surface area, site density), solids concentration, electrolyte, CO₂ exposure, equilibration time. The "same" mineral is not the same material. | Mechanisms 2–6 below; general background. Interlab-variability papers: [not reached]/title-only |
| 2 | Falling (anion) edges: solids effect disappears after dividing by solids; rising (cation) edges: shift is only −0.49 pH/decade vs −1.5 predicted | Linear sorption predicts a fixed shift. Cations deviating from it is the classic **particle concentration effect**: apparent Kd falls as solids rise. Proposed causes include incomplete separation of fine particles/colloids that carry sorbate into the "dissolved" fraction (Brownian pumping), and measurement artifacts. | Effect and its names confirmed as a literature topic by search; I did **not** read the papers. [title only]: [Journal of Marine Research record](https://elischolar.library.yale.edu/journal_of_marine_research/1958), [McMaster thesis record](https://macsphere.mcmaster.ca/handle/11375/5872), [MRS proceedings: liquid/solid ratio effect on distribution ratio](https://www.cambridge.org/core/journals/mrs-online-proceedings-library-archive/article/abs/studies-of-the-liquidsolid-ratio-effect-on-the-distribution-ratio-rd-in-sorption/FC8E432389D53400CD592AF642825DAE) |
| 3 | At loading above ~1e-4 mol/g, Kd drops ~0.45 log units; anion edges move with loading | A surface has a finite number of binding sites. Once the stronger sites fill, extra sorbate goes to weaker sites (lower Kd) and eventually precipitates on the surface. Dzombak & Morel needed **two site types (strong and weak)** for Cd on hydrous ferric oxide, saw Langmuir behaviour at low and Freundlich at moderate concentration, a maximum at high concentration, and a shift to surface precipitation as the surface saturates. | [read, abstract] [Dzombak & Morel 1986, J. Colloid Interface Sci. 112:588](https://collaborate.princeton.edu/en/publications/sorption-of-cadmium-on-hydrous-ferric-oxide-at-high-sorbatesorben/) |
| 4 | Loading breakpoint poorly located | Saturation depends on **site density and surface area**, not grams. Mass loading is the wrong axis; it should be per site. Ferrihydrite and goethite site densities and reactive surface areas are modelled explicitly in MUSIC work. | [read, abstract] [Hiemstra et al. 2009, GCA 73:4437](https://hzdr.de/publications/Publ-11430). Supports adding surface area/site density to the descriptor table (protocol E9). |
| 5 | U(VI) (and carbonate-bearing systems) show unusual shapes; the edge can fall at high pH | Carbonate in solution forms strongly bound dissolved uranyl–carbonate complexes that compete with the surface; at high pH and carbonate the surface also holds ternary uranyl–carbonate complexes. This can turn a rising edge into a rise-then-fall. CO₂ exposure differs between labs, so it is a hidden variable. | [read, abstract] Hiemstra et al. 2009 above (uranyl–triscarbonato surface complex at high pH and carbonate; uranyl polymerizes at high uranyl concentration). L-SCIE abstract: carbonate surface species best fit U(VI) on quartz. Other U(VI) reviews found by search: [ANSTO review "Uranium (VI) interactions with mineral surfaces"](https://apo.ansto.gov.au/handle/10238/15601) [title only], [Jang et al. 2007 EST](https://www.engr.psu.edu/ce/enve/burgos/new/publications/Jang%20et%20al%202007%20EST%20-%20U%20sorption.pdf) [title only] |
| 6 | Ionic strength effect is null on average, but papers differ | A null on average is expected to be a **mixture**: **inner-sphere** complexes (direct bonds) are insensitive to salt, **outer-sphere** complexes (held by electrostatics) are pushed off by salt. Pooling both types averages to ~0. Selenate on iron oxides is the textbook case of mixed behaviour. | Search summaries point to this for selenate; I could not read it (PubMed blocked). [title only] [Mechanisms of selenate adsorption on iron oxides and hydroxides (PubMed)](https://pubmed.ncbi.nlm.nih.gov/11999051/) [not reached], [Peak & Sparks work hosted at U. Delaware](https://www1.udel.edu/soilchem/peak02est.html) [title only] |
| 7 | Sorbate (not mineral class) dominates edge position and height | Metal hydrolysis strength and the mineral's point of zero charge together set where binding starts. Across metals, binding strength tracks the metal's hydrolysis constant (linear free-energy relationship). A cation with a lower hydrolysis pH sorbs at a lower pH. This predicts your finding that the sorbate matters more than mineral class. | LFER for intrinsic sorption constants exists: [novel equation for prediction of intrinsic sorption constants of metal cations (MRS)](https://resolve.cambridge.org/core/journals/mrs-online-proceedings-library-archive/article/abs/novel-equation-for-prediction-of-intrinsic-sorption-constants-of-metal-cations-at-mineralwater-interfaces/94E6B8FF662F7F8FFAD5921955C241D3) [title only]; [Predicting divalent metal sorption to hydrous Al, Fe and Mn oxides](https://researchwith.njit.edu/en/publications/predicting-divalent-metal-sorption-to-hydrous-al-fe-and-mn-oxides/) [title only]. Dzombak & Morel's HFO compilation is the standard reference but I could not retrieve the LFER section. |
| 8 | Duplicate/near-duplicate curves, outliers | Equilibration time (slow kinetics at high sorbate:sorbent ratios—Dzombak & Morel report much slower sorption there), pH drift in unbuffered tubes, filter/centrifuge differences. | Kinetics claim [read, abstract] (Dzombak & Morel 1986). The rest is general lab practice, no specific source. |

---

## 2. Plain-English summary for Dr. Black

1. **Same mineral name ≠ same surface.** Labs make goethite/ferrihydrite differently, with different surface area and number of binding sites. This alone can move an edge by a pH unit.
2. **More solid in the tube usually means a bigger fraction sorbed**, but cations sorb less per gram than simple theory says at higher solids. That is a recognized, still-debated artifact/effect.
3. **When the surface gets crowded, binding weakens** (strong sites fill first). Your high-loading Kd drop is textbook behavior.
4. **Carbonate competes** for uranium, in solution and on the surface; CO₂ in the lab air is rarely reported.
5. **Salt only affects loosely held (outer-sphere) species.** Our "no ionic-strength effect" is probably two opposite behaviours averaging out. Test it by sorbate type (protocol E8).
6. **Which metal** (its tendency to hydrolyze) sets the edge more than which mineral. This matches the LFER literature.

## 3. New testable hypotheses these suggest

| Hypothesis | Prediction | Protocol |
|---|---|---|
| H1 Carbonate/CO₂ causes the U(VI) high-pH fall | Edge-fall depth correlates with reported carbonate/atmosphere | E7 |
| H2 Inner- vs outer-sphere mixture hides ionic-strength effect | IS slope nonzero for known outer-sphere anions (Se(VI)), zero for inner-sphere (U, Am) | E8 |
| H3 Per-site loading collapses the loading regime | Breakpoint tighter when loading is per m² or per site | E9 |
| H4 Particle concentration effect explains the cation solids slope | Effect larger where separation method is filtration vs ultracentrifugation | E10 |
| H5 Edge position follows hydrolysis constant | Edge pH vs log K(MOH) linear across sorbates | E6 |

## 4. Paper ideas vs prior art (my preliminary read)

| Idea | Closest prior art found | Verdict (needs confirmation) |
|---|---|---|
| Cross-paper reproducibility ceiling of compiled sorption curves | L-SCIE FAIR database papers; nothing found quantifying paper-effect noise ceilings | Possibly open |
| pH-only transfer model, leave-one-paper-out | L-SURF (point-wise RF, U(VI), speciation features) | Differentiated, but must be compared against L-SURF explicitly |
| Solids and loading regimes from compiled data | Classical single-system studies (Dzombak & Morel; particle-effect literature) | Compiled, multi-mineral quantification may be new; need the particle-effect papers read |
| Ionic strength null as inner/outer-sphere mixture | Selenate mixture work | Testing it across a compiled database is plausible but unverified |
| Modular query interface for sorption data | L-SCIE is a database, I did not find a modular multi-dataset explorer | Possible software/tools note |

## 5. Gaps and what I could not verify

- Not read: the OECD-NEA thermodynamic sorption models/Kd guidance report (fetch blocked), PubMed pages, James & Healy, Hayes, Hiemstra & van Riemsdijk 1999, the Dzombak & Morel book LFER chapter.
- All `[title only]` entries need opening before citation.
- No systematic search (Web of Science/Scopus) was run. Use Dr. Black's library access for one before claiming novelty.
- L-SURF paper itself (journal, year, metrics) not read; only the project summary.

## Sources

- [Community Data Mining Approach for Surface Complexation Database Development (OSTI)](https://www.osti.gov/pages/biblio/1866540-community-data-mining-approach-surface-complexation-database-development)
- [L-SURF project page](https://ess.science.energy.gov/?p=12179)
- [Dzombak & Morel 1986, Cd on HFO](https://collaborate.princeton.edu/en/publications/sorption-of-cadmium-on-hydrous-ferric-oxide-at-high-sorbatesorben/)
- [Hiemstra et al. 2009, ferrihydrite II](https://hzdr.de/publications/Publ-11430)
- [Particle concentration effect records](https://elischolar.library.yale.edu/journal_of_marine_research/1958), [McMaster](https://macsphere.mcmaster.ca/handle/11375/5872), [MRS liquid/solid ratio](https://www.cambridge.org/core/journals/mrs-online-proceedings-library-archive/article/abs/studies-of-the-liquidsolid-ratio-effect-on-the-distribution-ratio-rd-in-sorption/FC8E432389D53400CD592AF642825DAE)
- [ANSTO U(VI) review](https://apo.ansto.gov.au/handle/10238/15601), [Jang et al. 2007](https://www.engr.psu.edu/ce/enve/burgos/new/publications/Jang%20et%20al%202007%20EST%20-%20U%20sorption.pdf)
- [Selenate mechanisms (PubMed)](https://pubmed.ncbi.nlm.nih.gov/11999051/), [Peak & Sparks](https://www1.udel.edu/soilchem/peak02est.html)
- [LFER intrinsic constants (MRS)](https://resolve.cambridge.org/core/journals/mrs-online-proceedings-library-archive/article/abs/novel-equation-for-prediction-of-intrinsic-sorption-constants-of-metal-cations-at-mineralwater-interfaces/94E6B8FF662F7F8FFAD5921955C241D3), [divalent metals on Al/Fe/Mn oxides](https://researchwith.njit.edu/en/publications/predicting-divalent-metal-sorption-to-hydrous-al-fe-and-mn-oxides/)
