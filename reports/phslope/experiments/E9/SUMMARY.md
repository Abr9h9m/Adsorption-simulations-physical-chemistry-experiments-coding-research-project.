# E9 Surface area and material variety

**Plain English.** Two papers can use the same grams of mineral but very different amounts of surface, if one mineral is finely divided. We checked whether expressing the mineral amount as surface area explains the edge shifts better than grams, and whether different material sources (suppliers or natural samples) behave differently. Result: **DO NOT ADOPT area normalisation (rule not met)**.

> EXPLORATORY. Uses the surface area and material source reported in the compiled dataset (method not recorded). 716 E1 curves report surface area. Development papers only. Locked set hash `88b1c3a1b769`. Commit `4f79b50`.

## 1. Within-pair edge variance explained (direction-specific slopes, pH per decade)

| x | n | pairs | R2 | slope_rising | slope_falling |
|---|---|---|---|---|---|
| log10_solids | 658 | 97 | 0.24 | -0.56 | 1.28 |
| log10_area | 658 | 97 | 0.271 | -0.566 | 1.32 |

Area vs mass: +13% relative change in R2 (rule: >= +20%).

## 2. Saturation breakpoint (log10 Kd at the pair reference pH vs loading; 90% bootstrap over papers)

| loading | n | breakpoint | ci90_lo | ci90_hi | ci_width |
|---|---|---|---|---|---|
| log10L | 478 | -6.24 | -9.01 | -3.99 | 5.02 |
| log10L_area | 493 | -10.8 | -10.6 | -5.93 | 4.67 |

Interval narrowing per m2 vs per gram: +7% (rule: >= 50%). Note: the per-m2 breakpoint is in log10 mol/m2, so the two breakpoints are on different scales; only the interval widths are compared.

## 3. Material source (within mineral) as a random effect on the pair-centred edge

| component | share |
|---|---|
| material_source | 0.0118 |
| unit | 0.283 |
| residual | 0.706 |

## Not done

- Loading per surface site (Mineralsites units unconfirmed).
- Surface-area method (BET vs other) and synthetic/natural labels: need data/descriptors/study_materials.csv.

## Analyst note

- The per-m2 breakpoint estimate (-10.8 log10 mol/m2) sits at the lower edge of the search grid and outside its own 90% bootstrap interval: the saturation break is not located on the area scale (nor well on the gram scale, interval width 5 decades). Neither normalisation pins down a breakpoint with these data.
