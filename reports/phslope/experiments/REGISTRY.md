# Experiment registry (every run, including failures)

| when (UTC) | experiment | commit | locked-set hash | verdict | note |
|---|---|---|---|---|---|
| 2026-10-13 16:28 | E0.1 | 9d88a0c | 88b1c3a1b769 | PASS | mass balance consistent 99.9% of 24617 rows |
| 2026-10-13 16:31 | data |  |  | INCLUDES LOCKED PAPERS | E0.3 regression check of the harness against the follow-up benchmark (computed on all papers before the lock) |
| 2026-10-13 16:32 | data |  |  | INCLUDES LOCKED PAPERS | test: harness regression check |
| 2026-10-13 16:32 | data |  |  | INCLUDES LOCKED PAPERS | test: harness regression check |
| 2026-10-13 16:35 | E3 | 2419b6b | 88b1c3a1b769 | done (no decision rule) | 74 duplicate pairs, 28 cross-paper; 17 papers in multi-paper lineage clusters |
| 2026-10-13 16:54 | E5 | 353c5ee-dirty | 88b1c3a1b769 | DOES NOT MEET RULE | retained 0.0%; validated median error nan |
| 2026-10-13 16:57 | E5 | b5c03f2 | 88b1c3a1b769 | MEETS RULE | retained 93.4%; validated median error 0.11 |
| 2026-10-13 16:58 | E4 | b5c03f2-dirty | 88b1c3a1b769 | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | lab proxy from reference code; 2 proxies |
| 2026-10-13 16:58 | E8 | b5c03f2-dirty | 88b1c3a1b769 | EFFECT FOUND (meets rule) | 13 tests; 81 within-paper series |
| 2026-10-13 16:58 | data |  |  | INCLUDES LOCKED PAPERS | data-entry templates and priority list (no outcomes used) |
| 2026-10-13 17:00 | E4 |  |  | RERUN SCHEDULED | first run used median of per-curve differences (degenerate with ties); paired statistic clarified to difference of medians in experiments.yaml |
| 2026-10-13 17:01 | E4 | 4f79b50 | 88b1c3a1b769 | GAIN DOES NOT SURVIVE (partly a lab effect, or not significant) | lab proxy from reference code; 2 proxies |
| 2026-10-13 17:02 | E9 | 4f79b50 | 88b1c3a1b769 | DO NOT ADOPT area normalisation (rule not met) | R2 gain +13%; breakpoint narrowing +7% |
| 2026-10-13 17:07 | E1 | 353c5ee-dirty | 88b1c3a1b769 | ACCEPT | edge median E1 0.882 vs B3 0.962; coverage 0.85; usage 0.81 |
| 2026-10-13 17:07 | E1 | e0652b2 | 88b1c3a1b769 | ACCEPT | edge median E1 0.882 vs B3 0.962; coverage 0.85; usage 0.81 |
| 2026-10-13 17:23 | E7 | 3e5912d | 88b1c3a1b769 | DO NOT KEEP log10 pCO2 (rule not met) | step 1a only (pCO2); DIC waits for D5 |
| 2026-10-13 21:14 | E21/M2/M3 | c835343-dirty | 88b1c3a1b769 | PREFER conformal | from cached E1 predictions |
| 2026-10-13 21:16 | E11 | 2cdce27 | 88b1c3a1b769 | UNDECIDED (ratio interval includes 1) | ratio 1.29 [0.56, 2.42] |
| 2026-10-13 21:22 | E20 | c80a5b8 | 88b1c3a1b769 | reported | 3 temperature series |
| 2026-10-13 21:23 | E13 | c80a5b8-dirty | 88b1c3a1b769 | DO NOT KEEP competitor term (rule not met) | oxyanion (test)/log10 K : -0.110; oxyanion (test)/native e: 0.299; cations (control)/log10 K : -0.168; cations (control)/native e: 0.342 |
| 2026-10-13 21:24 | E13 | c80a5b8-dirty | 88b1c3a1b769 | DO NOT KEEP competitor term (rule not met) | oxyanion (test)/log10 K : -0.110; oxyanion (test)/native e: 0.299; cations (control)/log10 K : -0.150; cations (control)/native e: 0.300 |
