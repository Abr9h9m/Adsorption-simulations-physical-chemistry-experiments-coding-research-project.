"""E0.1 -- raw-file inventory and mass-balance check (protocol section 4).

Inventory uses the whole raw file (it describes columns, not outcomes). The mass-balance
check is computed on development papers only (locked papers removed).
Outputs reports/phslope/experiments/E0/: column_inventory.csv, candidate_columns.csv,
mass_balance_by_reference.csv, SUMMARY.md, RUN_INFO.json.
"""
import os
import re

import numpy as np
import pandas as pd

from phslope.common import load_config, resolve_data_file
from phslope.experiments.kd import mass_balance
from phslope.experiments.registry import (EXP_DIR, drop_locked, exp_stamp, load_exp_config, log_run,
                                          write_run_info)

# keywords for columns that could hold method / material / bibliographic information (protocol E0.1)
CANDIDATES = {
    "equilibration / contact time": r"time|equil|contact|kinet",
    "aging": r"aging|age\b",
    "atmosphere / gas": r"gas|atm|co2|n2|o2",
    "filtration / separation": r"filt|centri|separ",
    "container": r"contain|vessel|tube",
    "pH method": r"ph_?(method|meas)",
    "detection limit / reported error": r"_sd$|detect|limit|err",
    "surface area": r"sa\b|surface|mineralsa",
    "material origin": r"source|origin|synth|natural",
    "bibliographic": r"author|journal|year|doi|title|reference",
    "site density": r"site",
}


def inventory(raw):
    rows = []
    for c in raw.columns:
        s = raw[c]
        ex = s.dropna().astype(str).unique()[:4]
        rows.append({"column": c, "dtype": str(s.dtype), "missing_share": round(float(s.isna().mean()), 3),
                     "n_distinct": int(s.nunique()), "examples": " | ".join(ex)})
    inv = pd.DataFrame(rows)
    cand = []
    for label, pat in CANDIDATES.items():
        for c in raw.columns:
            if re.search(pat, c, flags=re.I):
                r = inv[inv["column"] == c].iloc[0]
                cand.append({"purpose": label, "column": c, "missing_share": r["missing_share"],
                             "examples": r["examples"]})
    return inv, pd.DataFrame(cand)


def mass_balance_report(obs, tol):
    rel, ok = mass_balance(obs, tol)
    d = obs.assign(rel=rel, ok=ok)[["Reference", "rel", "ok"]].dropna(subset=["rel"])
    by = d.groupby("Reference").agg(n_rows=("rel", "size"), share_consistent=("ok", "mean"),
                                    median_rel_diff=("rel", "median"), max_rel_diff=("rel", "max")).reset_index()
    by["systematic_mismatch"] = by["share_consistent"] < 0.5
    return d, by.sort_values("share_consistent")


def run(data_file=None):
    from phslope.load import clean_observations
    cfg, ecfg = load_config(), load_exp_config()
    out = os.path.join(EXP_DIR, "E0")
    path = resolve_data_file(data_file, cfg)
    raw = pd.read_csv(path, low_memory=False)
    stamp = exp_stamp(path)
    write_run_info(out, stamp)
    inv, cand = inventory(raw)
    inv.to_csv(os.path.join(out, "column_inventory.csv"), index=False)
    cand.to_csv(os.path.join(out, "candidate_columns.csv"), index=False)

    obs = drop_locked(clean_observations(raw, cfg), col="Reference")
    d, by = mass_balance_report(obs, ecfg["kd"]["mass_balance_tolerance"])
    by.to_csv(os.path.join(out, "mass_balance_by_reference.csv"), index=False)
    share = float(d["ok"].mean()) if len(d) else np.nan
    passed = share >= ecfg["e0"]["mass_balance_pass_fraction"]
    bad = by[by["systematic_mismatch"]]
    lines = [
        "# E0.1 Raw-file inventory and mass-balance check", "",
        "**Plain English.** We listed every column in the data file to see what extra information exists (for "
        "example how long experiments ran, or what surface area the mineral had), and checked whether the amounts "
        "add up: dissolved should equal added minus stuck. "
        + (f"They add up for {share:.0%} of the rows that report all three amounts, so the reported dissolved "
           "amounts can be used." if passed else
           f"They add up for only {share:.0%} of the rows that report all three amounts, below the 90% needed, so "
           "the reported dissolved amounts are not trusted until Samuel looks at the papers listed below."), "",
        f"> EXPLORATORY. Development papers only for the mass balance (locked set hash `{stamp['locked_set_hash']}`).", "",
        f"Run: commit `{stamp['git_commit']}`, data `{path}`.", "",
        "## Columns", "",
        f"{len(raw.columns)} columns, {len(raw):,} rows. Full table: `column_inventory.csv`.", "",
        "Columns that could hold method, material or bibliographic information (`candidate_columns.csv`):", "",
        _md(cand[["purpose", "column", "missing_share", "examples"]]), "",
        "Not present in this file (nothing matched): " + ", ".join(
            k for k in CANDIDATES if k not in set(cand["purpose"])) + ".", "",
        "## Mass balance (development papers)", "",
        f"Rows with sorbed, dissolved and total all reported: {len(d):,}. Within "
        f"{ecfg['kd']['mass_balance_tolerance']:.0%}: {share:.1%} (pass line "
        f"{ecfg['e0']['mass_balance_pass_fraction']:.0%}): **{'PASS' if passed else 'FAIL'}**.", "",
        f"References where fewer than half the rows are consistent ({len(bad)}):", "",
        _md(bad.head(30)), "",
        "Per-reference table: `mass_balance_by_reference.csv`.",
    ]
    with open(os.path.join(out, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E0.1", "PASS" if passed else "FAIL", f"mass balance consistent {share:.1%} of {len(d)} rows", stamp)
    print(f"E0.1 mass balance {share:.3f} -> {'PASS' if passed else 'FAIL'}")
    return {"share": share, "passed": passed, "by_reference": by, "candidates": cand}


def _md(df):
    from phslope.report import md_table
    return md_table(df)


if __name__ == "__main__":
    run()
