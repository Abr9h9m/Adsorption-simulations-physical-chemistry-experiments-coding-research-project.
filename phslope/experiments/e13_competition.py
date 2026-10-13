"""E13 -- competing co-solutes (Addendum 1, E13 [lit]). EXPLORATORY; development papers only.

[lit] Balistrieri & Chao (1987; abstract read): competition with selenite on goethite in the order
phosphate > silicate >= citrate > molybdate > bicarbonate/carbonate > oxalate > fluoride > sulfate.

Competitor molarity per curve = sum of the electrolyte concentrations of competing anions (experiments.yaml
e13.competitors, plus organic anions: electrolyte labels that are not an element symbol followed by an
oxidation state, e.g. Citrate(-3), Humic acid),
EXCLUDING the curve's own sorbate. Variable: log10(competitor + floor).
Within mineral-sorbate pair (pair-centred), errors clustered by lineage unit:
  log10 K at the pair reference pH and the native edge vs log10 competitor, separately for oxyanion
  sorbates and for cation sorbates (negative control).
Decision (pre-declared): keep if the oxyanion coefficient has a 95% interval excluding zero in the expected
(negative) direction and the cation interval includes zero.
"""
import os
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.e08_ionic_strength import assign_class
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E13")
_ELEMENT = re.compile(r"^[A-Z][a-z]?\(")         # element labels: symbol directly followed by "(" e.g. P(+5)


def competitor_molarity(obs, competitors, sorbate_of):
    """Per curve: summed median concentration of competing electrolytes (mol/L), excluding the sorbate."""
    rows = []
    for cid, g in obs.groupby("curve_id"):
        own = sorbate_of.get(cid)
        tot, names = 0.0, set()
        for i in range(1, 8):
            lab, val = f"Electrolyte{i}", f"Electrolyte{i}_val"
            if lab not in g:
                continue
            for label in g[lab].dropna().unique():
                if label == own:
                    continue
                organic = not _ELEMENT.match(str(label))     # e.g. Citrate(-3), Humic acid
                if label in competitors or organic:
                    v = pd.to_numeric(g.loc[g[lab] == label, val], errors="coerce").median()
                    if np.isfinite(v) and v > 0:
                        tot += v
                        names.add(str(label))
        rows.append({"curve_id": cid, "competitor_mol_L": tot, "competitors": ";".join(sorted(names))})
    return pd.DataFrame(rows)


def within_pair_effect(d, ycol, xcol):
    d = d.dropna(subset=[ycol, xcol]).copy()
    d = d[d.groupby("pair_dir")[xcol].transform("nunique") >= 2]
    if len(d) < 8 or d["unit"].nunique() < 3:
        return {"n": len(d), "pairs": d["pair_dir"].nunique(), "coef": np.nan, "ci_lo": np.nan, "ci_hi": np.nan,
                "p": np.nan}
    y = d[ycol] - d.groupby("pair_dir")[ycol].transform("mean")
    x = d[xcol] - d.groupby("pair_dir")[xcol].transform("mean")
    r = sm.OLS(y, sm.add_constant(x)).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["unit"])[0]})
    ci = r.conf_int().iloc[1]
    return {"n": len(d), "pairs": d["pair_dir"].nunique(), "units": d["unit"].nunique(), "coef": r.params.iloc[1],
            "ci_lo": ci[0], "ci_hi": ci[1], "p": r.pvalues.iloc[1]}


def run():
    ecfg = load_exp_config()
    cfg = ecfg["e13"]
    curves, obs = build(purpose="E13")
    stamp = exp_stamp(extra={"experiment": "E13"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    comp = competitor_molarity(obs[obs["curve_id"].isin(c["curve_id"])], set(cfg["competitors"]),
                               c.set_index("curve_id")["sorbate"].to_dict())
    c = c.merge(comp, on="curve_id", how="left")
    c["log10_comp"] = np.log10(c["competitor_mol_L"].fillna(0) + cfg["floor_mol_L"])
    c["pH_c"] = E1.reference_pH(c, c)
    c["logK_at_ref"] = c["a"] + c["b"] * c["pH_c"]
    c["i_class"] = c["sorbate"].map(lambda s: assign_class(s, ecfg["e8"]["classes"]))
    groups = {"oxyanion (test)": c["i_class"] == "oxyanion",
              "cations (control)": c["i_class"].isin(["inner_sphere_prone", "outer_sphere_prone"])}
    rows = []
    for gname, sel in groups.items():
        for ycol, label in (("logK_at_ref", "log10 K at pair reference pH"), ("pH_native", "native edge (pH)")):
            rows.append({"set": gname, "outcome": label, **within_pair_effect(c[sel], ycol, "log10_comp")})
    R = pd.DataFrame(rows)
    ox = R[R["set"].str.startswith("oxyanion")]
    ca = R[R["set"].str.startswith("cations")]
    ox_ok = (ox["ci_hi"] < 0).all()
    ca_ok = ((ca["ci_lo"] <= 0) & (ca["ci_hi"] >= 0)).all()
    verdict = "KEEP competitor term" if (ox_ok and ca_ok) else "DO NOT KEEP competitor term (rule not met)"
    counts = c.assign(has=c["competitor_mol_L"] > 0).groupby("i_class")["has"].agg(["size", "sum"]).reset_index()
    counts.columns = ["class", "curves", "with_competitor"]
    top = c.loc[c["competitor_mol_L"] > 0, "competitors"].str.split(";").explode().value_counts().head(10)
    os.makedirs(OUT, exist_ok=True)
    R.to_csv(os.path.join(OUT, "competition_effects.csv"), index=False)
    c[["curve_id", "sorbate", "competitor_mol_L", "competitors"]].to_csv(os.path.join(OUT, "competitors_per_curve.csv"),
                                                                          index=False)
    from phslope.report import md_table
    lines = [
        "# E13 Competing co-solutes", "",
        "**Plain English.** Other dissolved anions such as phosphate or carbonate can take the binding sites "
        "an anion like selenite needs. We measured how much of such competitors each experiment contained and "
        "checked whether more competitor means less sorption for anions, but not for metal cations (the "
        f"control). Result: **{verdict}**.", "",
        f"> EXPLORATORY. **[lit]** Balistrieri & Chao 1987 (abstract read). Development papers only. Locked set "
        f"hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## Curves with a competitor in the electrolyte", "", md_table(counts), "",
        "Most common competitors: " + ", ".join(f"{k} ({v})" for k, v in top.items()) + ".", "",
        "## Within-pair effect per decade of competitor concentration (clustered by unit)", "", md_table(R), "",
        "Expected for anions: negative on log10 K and negative on the (falling) edge.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E13", verdict, "; ".join(f"{r.set}/{r.outcome[:8]}: {r.coef:.3f}" for r in R.itertuples()), stamp)
    record_adjustment("E13 competitor molarity term", verdict,
                      "; ".join(f"{r.set}, {r.outcome}: {r.coef:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]" for r in R.itertuples()))
    print(verdict)
    print(R.to_string())


if __name__ == "__main__":
    run()
