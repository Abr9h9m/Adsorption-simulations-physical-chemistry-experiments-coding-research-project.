"""E20 -- temperature and time (Addendum 1). EXPLORATORY; development papers only.

E0.1: the raw file has NO contact-time column; temperature (`Temp`) is reported for few curves.
Test: within-paper temperature series (same paper and pair, temperature differs, solids and total sorbate
within 10%): effect of temperature on the native edge, solids-normalised edge and log10 K slope b, with
paper-clustered intervals. No direction is assumed (literature leads are title-only).
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.e08_ionic_strength import clustered_slope
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info

OUT = os.path.join(EXP_DIR, "E20")


def temperature_series(c, tol=0.10):
    keep = []
    for (ref, pdir), g in c.dropna(subset=["temp"]).groupby(["reference", "pair_dir"]):
        if g["temp"].round(0).nunique() < 2:
            continue
        ok = np.ones(len(g), bool)
        for col in ("solids_g_L", "total_sorbate_mol_L"):
            med = g[col].median()
            ok &= ((g[col] - med).abs() <= tol * abs(med)).fillna(False).to_numpy()
        s = g[ok]
        if s["temp"].round(0).nunique() >= 2:
            keep.append(s.assign(series=f"{ref}|{pdir}"))
    return pd.concat(keep) if keep else c.iloc[:0].assign(series=[])


def run():
    ecfg = load_exp_config()
    curves, _ = build(purpose="E20")
    stamp = exp_stamp(extra={"experiment": "E20"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    n_temp = int(c["temp"].notna().sum())
    S = temperature_series(c)
    rows = []
    for out, col in (("native edge (pH per 10 degC)", "pH_native"), ("solids-normalised edge (pH per 10 degC)", "pH_S1"),
                     ("slope b (log10 K per pH, per 10 degC)", "b")):
        if len(S):
            y = S[col] - S.groupby("series")[col].transform("mean")
            x = (S["temp"] - S.groupby("series")["temp"].transform("mean")) / 10.0
            r = clustered_slope(y, x, S["reference"])
        else:
            r = {"n": 0}
        rows.append({"outcome": out, "series": S["series"].nunique() if len(S) else 0,
                     "papers": S["reference"].nunique() if len(S) else 0, **r})
    R = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    R.to_csv(os.path.join(OUT, "temperature_effects.csv"), index=False)
    if len(S):
        S[["curve_id", "reference", "pair_dir", "temp", "pH_native", "b"]].to_csv(
            os.path.join(OUT, "temperature_series.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E20 Temperature and contact time", "",
        "**Plain English.** Warmer or longer experiments can shift sorption curves. The dataset has no "
        "contact-time column at all, and temperature is reported for few curves, so only a small temperature "
        "check is possible: curves from the same paper that differ only in temperature.", "",
        f"> EXPLORATORY. Development papers only. {n_temp} of {len(c)} E1 curves report temperature. Locked set "
        f"hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        md_table(R), "",
        "Contact time: not in the file; it is a column of `data/descriptors/study_methods.csv` (E10, human entry).",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E20", "reported", f"{S['series'].nunique() if len(S) else 0} temperature series", stamp)
    print(R.to_string())


if __name__ == "__main__":
    run()
