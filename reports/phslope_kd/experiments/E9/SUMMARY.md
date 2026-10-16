# E9 Surface area and material variety

**Plain English.** Two papers can use the same grams of mineral but very different amounts of surface, if one mineral is finely divided. We checked whether expressing the mineral amount as surface area explains the edge shifts better than grams, and whether different material sources (suppliers or natural samples) behave differently. Result: **DO NOT ADOPT area normalisation (rule not met)**.

> EXPLORATORY. Uses the surface area and material source reported in the compiled dataset (method not recorded). 600 E1 curves report surface area. Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## 1. Within-pair edge variance explained (direction-specific slopes, pH per decade)

| x | n | pairs | R2 | slope_rising | slope_falling |
|---|---|---|---|---|---|
| log10_solids | 549 | 82 | 0.0485 | 0.538 | -0.255 |
| log10_area | 549 | 82 | 0.00823 | 0.195 | -0.11 |

Area vs mass: -83% relative change in R2 (rule: >= +20%).

## 2. Saturation breakpoint (log10 Kd at the pair reference pH vs loading; 90% bootstrap over papers)

| loading | n | breakpoint | ci90_lo | ci90_hi | ci_width |
|---|---|---|---|---|---|
| log10L | 394 | -6.44 | -8.23 | -4.83 | 3.4 |
| log10L_area | 396 | -6.38 | -10.7 | -5.99 | 4.67 |

Interval narrowing per m2 vs per gram: -37% (rule: >= 50%). Note: the per-m2 breakpoint is in log10 mol/m2, so the two breakpoints are on different scales; only the interval widths are compared.

## 3. Material source (within mineral) as a random effect on the pair-centred edge

| component | share |
|---|---|
| material_source | 1.31e-08 |
| unit | 0.228 |
| residual | 0.772 |

## Not done

- Loading per surface site (Mineralsites units unconfirmed).
- Surface-area method (BET vs other) and synthetic/natural labels: need data/descriptors/study_materials.csv.
