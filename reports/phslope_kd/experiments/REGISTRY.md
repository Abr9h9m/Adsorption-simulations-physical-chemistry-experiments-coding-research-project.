# Experiment registry (every run, including failures)

| when (UTC) | experiment | commit | locked-set hash | verdict | note |
|---|---|---|---|---|---|
| 2026-10-16 11:56 | E0.1 | d468a46 | 88b1c3a1b769 | PASS | mass balance consistent 99.9% of 24617 rows |
| 2026-10-16 11:57 | E3 | d468a46 | 88b1c3a1b769 | done (no decision rule) | 67 duplicate pairs, 22 cross-paper; 16 papers in multi-paper lineage clusters |
| 2026-10-16 12:09 | E1 | d468a46 | 88b1c3a1b769 | ACCEPT | edge median E1 0.751 vs B3 0.828; coverage 0.83; usage 0.78 |
| 2026-10-16 12:09 | E21/M2/M3 | d468a46 | 88b1c3a1b769 | PREFER conformal | from cached E1 predictions |
| 2026-10-16 12:10 | E4 | d468a46 | 88b1c3a1b769 | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | lab proxy from reference code; 2 proxies |
| 2026-10-16 12:11 | E5 | d468a46 | 88b1c3a1b769 | MEETS RULE | retained 89.9%; validated median error 0.17 |
| 2026-10-16 12:11 | E8 | d468a46 | 88b1c3a1b769 | EFFECT FOUND (meets rule) | 16 tests; 72 within-paper series |
| 2026-10-16 12:12 | E9 | d468a46 | 88b1c3a1b769 | DO NOT ADOPT area normalisation (rule not met) | R2 gain -83%; breakpoint narrowing -37% |
| 2026-10-16 12:13 | E11 | d468a46 | 88b1c3a1b769 | UNDECIDED (ratio interval includes 1) | ratio 0.88 [0.30, 1.83] |
| 2026-10-16 12:14 | E13 | d468a46 | 88b1c3a1b769 | DO NOT KEEP competitor term (rule not met) | oxyanion (test)/log10 K : 0.097; oxyanion (test)/native e: 0.482; cations (control)/log10 K : 0.045; cations (control)/native e: -0.037 |
| 2026-10-16 12:15 | E16 | d468a46 | 88b1c3a1b769 | reported | useful: {'mineral': False, 'sorbate': False} |
| 2026-10-16 12:16 | E20 | d468a46 | 88b1c3a1b769 | reported | 1 temperature series |
| 2026-10-16 12:22 | E23/M-Power | d468a46 | 88b1c3a1b769 | PLACEBOS PASS | a 0.04; b 0.10; c 0.06; e 1.00 |
| 2026-10-16 12:41 | F-dev | d468a46 | 88b1c3a1b769 | done | accepted: ['E8 ionic strength x sorbate type', 'E1 within-between solids (E23)'] |
| 2026-10-16 12:41 | M7-M9 | d468a46 | 88b1c3a1b769 | reported | M7 n=44; M8 2 pairs |
| 2026-10-16 12:44 | E15 | d468a46 | 88b1c3a1b769 | ADOPT random_forest, gradient_boosting | grouped vs random split; RF, HGB, E1, B0, B5 |
| 2026-10-16 12:45 | E15b | d468a46 | 88b1c3a1b769 | reported | gbm edge vs E1 final |
| 2026-10-16 12:49 | E15c | d468a46 | 88b1c3a1b769 | reported | full: 0.93; no_conditions: 1.02; no_identity: 1.30 |
| 2026-10-16 12:49 | E12 | d468a46 | 88b1c3a1b769 | HETEROGENEITY SUPPORTED | Freundlich 0.60 [0.43,0.77]; SSE one 76.1 two 74.4 |
| 2026-10-16 12:50 | E17 | d468a46 | 88b1c3a1b769 | PREDICTION (i) NOT SUPPORTED | (ii) waits for E10 |
| 2026-10-16 12:50 | E22 | d468a46 | 88b1c3a1b769 | reported | 211 pairs ranked |
| 2026-10-16 13:07 | E14 | d468a46 | 88b1c3a1b769 | reported | H1 0.73; H2 0.00; H3 0.00; H4 0.89; H5 0.98 |
| 2026-10-16 13:16 | E7 | d468a46 | 88b1c3a1b769 | DO NOT KEEP log10 pCO2 (rule not met) | step 1a only (pCO2); DIC waits for D5 |
| 2026-10-16 13:39 | E2 | d468a46 | 88b1c3a1b769 | KEEP W0 (0.03, 0.97) | 5 schemes, 4 paired tests |
