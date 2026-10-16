# E0.1 Raw-file inventory and mass-balance check

**Plain English.** We listed every column in the data file to see what extra information exists (for example how long experiments ran, or what surface area the mineral had), and checked whether the amounts add up: dissolved should equal added minus stuck. They add up for 100% of the rows that report all three amounts, so the reported dissolved amounts can be used.

> EXPLORATORY. Development papers only for the mass balance (locked set hash `88b1c3a1b769`).

Run: commit `d468a46`, data `C:\Users\itzju\sc.dataset.csv`.

## Columns

82 columns, 38,906 rows. Full table: `column_inventory.csv`.

Columns that could hold method, material or bibliographic information (`candidate_columns.csv`):

| purpose | column | missing_share | examples |
|---|---|---|---|
| atmosphere / gas | Gas1 | 0.043 | N2(g) | O2(g) | Ar(g) | CO2(g) |
| atmosphere / gas | Gas1_val | 0.046 | 0.8 | 1.0 | 0.0101325 | 0.000316 |
| atmosphere / gas | Gas1_SD | 0.046 | 0.08 | 0.1 | 0.00101325 | 3.16e-05 |
| atmosphere / gas | Gas1_units | 0.063 | bar |
| atmosphere / gas | Gas2 | 0.538 | O2(g) | CO2(g) |
| atmosphere / gas | Gas2_val | 0.538 | 0.2 | 2e-06 | 0.0003678 | 0.0195 |
| atmosphere / gas | Gas2_SD | 0.538 | 0.02 | 2e-07 | 3.678e-05 | 0.00195 |
| atmosphere / gas | Gas2_units | 0.538 | bar |
| atmosphere / gas | Gas3 | 0.612 | CO2(g) |
| atmosphere / gas | Gas3_val | 0.613 | 0.0003659 | 0.0003678 | 0.0003707 | 0.000362 |
| atmosphere / gas | Gas3_SD | 0.612 | 3.659e-05 | 3.678e-05 | 3.707e-05 | 3.62e-05 |
| atmosphere / gas | Gas3_units | 0.612 | bar |
| detection limit / reported error | Electrolyte1_SD | 0.017 | 0.005 | 0.0005 | 0.00025 | 0.0001 |
| detection limit / reported error | Electrolyte2_SD | 0.022 | 0.005 | 0.0005 | 0.00025 | 0.0001 |
| detection limit / reported error | Electrolyte3_SD | 0.915 | 5e-06 | 2.5e-05 | 1e-07 | 2.5e-06 |
| detection limit / reported error | Electrolyte4_SD | 0.983 | 0.0005 | 0.0027 | 7.15e-07 | 7.15e-06 |
| detection limit / reported error | Electrolyte5_SD | 0.983 | 0.026 | 1.905e-06 | 1.905e-05 | 8.9e-05 |
| detection limit / reported error | Electrolyte6_SD | 0.985 | 0.001335 | 0.00041 | 5.5e-06 | 0.0014 |
| detection limit / reported error | Electrolyte7_SD | 0.992 | 8e-06 | 9e-05 | 3.05e-05 | 2.715e-05 |
| detection limit / reported error | pH_SD | 0.016 | 0.1 |
| detection limit / reported error | Sorbate_SD | 0.223 | 5e-08 | 5e-07 | 5e-06 | 1.015e-08 |
| detection limit / reported error | Aq_SD | 0.25 | 7.07107e-08 | 7.07107e-07 | 7.07107e-06 | 1.02202e-08 |
| detection limit / reported error | Sorbed_SD | 0.253 | 5e-08 | 5e-07 | 5e-06 | 1.4404e-08 |
| detection limit / reported error | SurfCharge_SD | 0.796 | 0.000135441 | 0.000127839 | 0.000121822 | 0.000115432 |
| detection limit / reported error | Mineral_SD | 0.05 | 1.2 | 1.25 | 2.86 | 5.0 |
| detection limit / reported error | MineralSA_SD | 0.147 | 0.02 | 1.0 | 0.031 | 0.01 |
| detection limit / reported error | Mineralsites_SD | 0 | 0.231 | 1.08 | 0.033 |
| detection limit / reported error | CEC_SD | 0.806 | 2.42 | 1.82 | 2.01 | 2.0 |
| detection limit / reported error | Gas1_SD | 0.046 | 0.08 | 0.1 | 0.00101325 | 3.16e-05 |
| detection limit / reported error | Gas2_SD | 0.538 | 0.02 | 2e-07 | 3.678e-05 | 0.00195 |
| detection limit / reported error | Gas3_SD | 0.612 | 3.659e-05 | 3.678e-05 | 3.707e-05 | 3.62e-05 |
| detection limit / reported error | X_SD | 1 |  |
| detection limit / reported error | Y_SD | 0.769 | 0.2307 | 0.233 | 0.5198 | 1.0988 |
| surface area | MineralSA | 0.147 | 0.2 | 10.0 | 0.31 | 0.03 |
| surface area | MineralSA_SD | 0.147 | 0.02 | 1.0 | 0.031 | 0.01 |
| surface area | MineralSA_units | 0.144 | m2/g |
| material origin | Mineral_source | 0.153 | Merck | Sigma | Wedron #510 | Min-U-Sil 30 |
| bibliographic | Reference | 0 | azbn00 | azzbn01 | jhlch99 | pjtp01 |
| site density | Mineralsites | 0 | 2.31 | 10.8 |
| site density | Mineralsites_SD | 0 | 0.231 | 1.08 | 0.033 |
| site density | Mineralsites_units | 0 | sites/nm2 |

Not present in this file (nothing matched): equilibration / contact time, aging, filtration / separation, container, pH method.

## Mass balance (development papers)

Rows with sorbed, dissolved and total all reported: 24,617. Within 10%: 99.9% (pass line 90%): **PASS**.

References where fewer than half the rows are consistent (1):

| Reference | n_rows | share_consistent | median_rel_diff | max_rel_diff | systematic_mismatch |
|---|---|---|---|---|---|
| b68 | 13 | 0.0769 | 0.606 | 0.914 | True |

Per-reference table: `mass_balance_by_reference.csv`.
