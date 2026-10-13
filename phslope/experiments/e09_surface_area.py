"""E9 -- surface area and material variety (protocol section 5, E9). EXPLORATORY; development only.

Uses the specific surface area (MineralSA, m2/g) and material source (Mineral_source) REPORTED IN THE
COMPILED DATASET (E0.1 found them; measurement method, e.g. BET, is not recorded there). The
human-filled per-study materials table (data/descriptors/study_materials.csv) is still the protocol's
route for method and missing values; this run is what the dataset itself supports.

1. Within-pair edge variance explained by log10 solids (g/L) vs log10 area loading (m2/L = g/L x m2/g),
   with direction-specific slopes, on curves that report surface area.
2. Saturation breakpoint: log10 Kd at the pair's reference pH vs loading per gram and per m2; piecewise
   break with a bootstrap over papers; compare interval widths.
3. Material source as a random effect on the pair-centred edge (variance share).
Decision (pre-declared): adopt area normalisation if the area term explains >= 20% more within-pair edge
variance than solids by mass, OR the breakpoint interval narrows by >= 50%.
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)
from phslope.reml import fit_reml

OUT = os.path.join(EXP_DIR, "E9")


def within_pair_r2(c, xcol):
    """R2 of pair-centred native edge on pair-centred x with separate slopes for rising and falling."""
    d = c.dropna(subset=["pH_native", xcol]).copy()
    d = d[d.groupby("pair_dir")[xcol].transform("count") >= 2]
    y = d["pH_native"] - d.groupby("pair_dir")["pH_native"].transform("mean")
    x = d[xcol] - d.groupby("pair_dir")[xcol].transform("mean")
    X = np.column_stack([x * (d["shape"] == "rising"), x * (d["shape"] == "falling")])
    beta, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
    res = y.to_numpy() - X @ beta
    return {"x": xcol, "n": len(d), "pairs": d["pair_dir"].nunique(), "R2": 1 - res @ res / (y @ y),
            "slope_rising": beta[0], "slope_falling": beta[1]}


def breakpoint_interval(c, loading_col, B, seed):
    d = c.dropna(subset=[loading_col, "a", "b"]).copy()
    ref = d.groupby("pair_dir")["pH_native"].median()
    d["pH_ref"] = d["pair_dir"].map(ref)
    d = d[(d["pH_ref"] >= d["mid_pH_lo"] - 0.25) & (d["pH_ref"] <= d["mid_pH_hi"] + 0.25)]
    d["logKd"] = d["a"] + d["b"] * d["pH_ref"] - d["log10_solids"]
    d = d[d.groupby("pair_dir")[loading_col].transform(lambda s: s.max() - s.min()) >= 0.5]
    grid = np.linspace(d[loading_col].quantile(.1), d[loading_col].quantile(.9), 31)

    def best(dd):
        y = dd["logKd"] - dd.groupby("grp_b")["logKd"].transform("mean")
        x = dd[loading_col] - dd.groupby("grp_b")[loading_col].transform("mean")
        out = []
        for bp in grid:
            h = np.maximum(dd[loading_col] - bp, 0)
            h = h - h.groupby(dd["grp_b"]).transform("mean")
            X = np.column_stack([x, h])
            beta, *_ = np.linalg.lstsq(X, y.to_numpy(), rcond=None)
            out.append((float(((y.to_numpy() - X @ beta) ** 2).sum()), bp))
        return min(out)[1]
    d["grp_b"] = d["pair_dir"]
    bp0 = best(d)
    rng = np.random.default_rng(seed)
    refs = d["reference"].unique()
    bps = []
    for _ in range(B):
        parts = [d[d["reference"] == r].assign(grp_b=lambda z, i=i: z["pair_dir"] + f"#{i}")
                 for i, r in enumerate(rng.choice(refs, len(refs)))]
        bps.append(best(pd.concat(parts)))
    lo, hi = np.percentile(bps, [5, 95])
    return {"loading": loading_col, "n": len(d), "breakpoint": bp0, "ci90_lo": lo, "ci90_hi": hi,
            "ci_width": hi - lo}


def run(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    curves, _ = build(purpose="E9")
    stamp = exp_stamp(extra={"experiment": "E9", "surface_area_source": "MineralSA column of the compiled dataset"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    c = c[c["surface_area_m2_g"] > 0].copy()
    c["log10_area"] = c["log10_solids"] + np.log10(c["surface_area_m2_g"])
    c["log10L_area"] = c["log10_total"] - c["log10_area"]

    r_mass, r_area = within_pair_r2(c, "log10_solids"), within_pair_r2(c, "log10_area")
    T1 = pd.DataFrame([r_mass, r_area])
    gain = r_area["R2"] / r_mass["R2"] - 1 if r_mass["R2"] > 0 else np.nan
    bpg = breakpoint_interval(c, "log10L", 100, seed)
    bpa = breakpoint_interval(c, "log10L_area", 100, seed)
    T2 = pd.DataFrame([bpg, bpa])
    narrowing = 1 - bpa["ci_width"] / bpg["ci_width"] if bpg["ci_width"] > 0 else np.nan

    d = c.dropna(subset=["mineral_source"]).copy()
    d["edge_c"] = d["pH_native"] - d.groupby("pair_dir")["pH_native"].transform("mean")
    d["src"] = d["mineral"] + "|" + d["mineral_source"].astype(str)
    comp = fit_reml(d, "edge_c", {"material_source": "src", "unit": "unit"})["components"]
    tot = sum(comp.values())
    T3 = pd.DataFrame([{"component": k, "share": v / tot} for k, v in comp.items()])

    adopt = (np.isfinite(gain) and gain >= 0.20) or (np.isfinite(narrowing) and narrowing >= 0.5)
    verdict = "ADOPT area normalisation" if adopt else "DO NOT ADOPT area normalisation (rule not met)"
    T1.to_csv(os.path.join(OUT, "within_pair_r2.csv"), index=False)
    T2.to_csv(os.path.join(OUT, "breakpoints.csv"), index=False)
    T3.to_csv(os.path.join(OUT, "material_source_variance.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E9 Surface area and material variety", "",
        "**Plain English.** Two papers can use the same grams of mineral but very different amounts of surface, "
        "if one mineral is finely divided. We checked whether expressing the mineral amount as surface area "
        "explains the edge shifts better than grams, and whether different material sources (suppliers or "
        f"natural samples) behave differently. Result: **{verdict}**.", "",
        f"> EXPLORATORY. Uses the surface area and material source reported in the compiled dataset (method not "
        f"recorded). {len(c)} E1 curves report surface area. Development papers only. Locked set hash "
        f"`{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## 1. Within-pair edge variance explained (direction-specific slopes, pH per decade)", "", md_table(T1), "",
        f"Area vs mass: {gain:+.0%} relative change in R2 (rule: >= +20%).", "",
        "## 2. Saturation breakpoint (log10 Kd at the pair reference pH vs loading; 90% bootstrap over papers)", "",
        md_table(T2), "",
        f"Interval narrowing per m2 vs per gram: {narrowing:+.0%} (rule: >= 50%). Note: the per-m2 breakpoint is in "
        "log10 mol/m2, so the two breakpoints are on different scales; only the interval widths are compared.", "",
        "## 3. Material source (within mineral) as a random effect on the pair-centred edge", "", md_table(T3), "",
        "## Not done", "",
        "- Loading per surface site (Mineralsites units unconfirmed).",
        "- Surface-area method (BET vs other) and synthetic/natural labels: need data/descriptors/study_materials.csv.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E9", verdict, f"R2 gain {gain:+.0%}; breakpoint narrowing {narrowing:+.0%}", stamp)
    record_adjustment("E9 surface-area normalisation of solids", verdict,
                      f"within-pair R2 mass {r_mass['R2']:.3f} vs area {r_area['R2']:.3f}; breakpoint CI width "
                      f"{bpg['ci_width']:.2f} (per g) vs {bpa['ci_width']:.2f} (per m2)")
    print(f"E9 {verdict}")
    return T1, T2, T3


if __name__ == "__main__":
    run()
