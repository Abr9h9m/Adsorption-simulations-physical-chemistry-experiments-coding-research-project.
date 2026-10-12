"""load.py -- raw sorption file -> clean observation table (Stage 0.1).

Wraps data_audit.prepare_data (corrected ionic strength, electrolyte signature)
and response.compute_response, then adds the fixes this direction needs:

- Labels are kept as separate columns (Mineral, Sorbate, electrolyte signature)
  and never round-tripped through a joined string. The old junk sorbate label
  "2)" came from splitting "mineral-signature-sorbate" on "-": any label with a
  negative oxidation state, e.g. "Se(-2)" or "Cl(-1)", breaks that split.
  Use `pair_label` (separator " | ") when a single display string is needed.
- pH outside [0, 14] is a data-entry error (35 rows in the 2025 file); those
  rows are flagged bad_ph and kept, never silently dropped.
- Sorbate_val is converted to mol/L before computing fraction sorbed (39 rows
  are in nmol/L while Sorbed_val is in mol/L).
- Solids loading (Mineral_val) is converted to g/L where the unit allows;
  m2/L loadings go to solids_m2_L; other units are left missing and counted.
"""
import argparse
import re

import numpy as np
import pandas as pd

import data_audit as da
from response import compute_response
from phslope.common import load_config, resolve_data_file

PAIR_SEP = " | "

CONC_TO_MOL_L = {"mol/L": 1.0, "mmol/L": 1e-3, "umol/L": 1e-6, "µmol/L": 1e-6, "nmol/L": 1e-9}
SOLIDS_TO_G_L = {"g/L": 1.0, "mg/mL": 1.0, "mg/L": 1e-3}

_HAS_LETTER = re.compile(r"[A-Za-z]")
# "+" joins signature members, but labels contain "+" too ("Na(+1)"), so only
# split on a "+" that is not inside parentheses.
_SIG_SPLIT = re.compile(r"\+(?![^(]*\))")


def pair_label(mineral, sorbate):
    return f"{mineral}{PAIR_SEP}{sorbate}"


def split_pair_label(label):
    mineral, sorbate = label.split(PAIR_SEP)
    return mineral, sorbate


def split_signature(sig):
    """'C(+4)+Cl(+7)+Na(+1)' -> ['C(+4)', 'Cl(+7)', 'Na(+1)']. Never use str.split('+')."""
    return [p for p in _SIG_SPLIT.split(str(sig)) if p] if isinstance(sig, str) else []


def is_valid_label(label):
    """A real species/mineral label has at least 2 characters and at least one letter."""
    s = str(label).strip()
    return len(s) >= 2 and bool(_HAS_LETTER.search(s))


def _to_unit(values, units, table):
    """Converts values to the table's base unit; unknown or missing units give NaN."""
    return pd.to_numeric(values, errors="coerce") * units.map(table)


def standardise_labels(df):
    for col in ("Reference", "Set", "Mineral", "Mineral_formula", "Sorbate"):
        if col in df.columns:
            df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
    bad = df["Sorbate"].dropna()
    bad = bad[~bad.map(is_valid_label)]
    if len(bad):
        raise ValueError(f"Junk sorbate labels in input: {sorted(bad.unique())}")
    bad = df["Mineral"].dropna()
    bad = bad[~bad.map(is_valid_label)]
    if len(bad):
        raise ValueError(f"Junk mineral labels in input: {sorted(bad.unique())}")
    return df


def carbonate_flag(df, n_gas=3):
    """True if CO2(g) is reported with a positive partial pressure, or a C(+4)
    (carbonate/bicarbonate) electrolyte is present."""
    flag = pd.Series(False, index=df.index)
    for i in range(1, n_gas + 1):
        lab, val = f"Gas{i}", f"Gas{i}_val"
        if lab in df.columns:
            flag |= (df[lab] == "CO2(g)") & (pd.to_numeric(df.get(val), errors="coerce") > 0)
    flag |= df["_electrolyte_sig"].apply(lambda sig: "C(+4)" in split_signature(sig))
    return flag


def clean_observations(raw, config=None):
    """Raw Appendix A table -> observation table with standard columns:
    pH, bad_ph, ionic_strength, electrolyte_sig, temp, total_sorbate_mol_L,
    solids_g_L, solids_m2_L, co2_present, mineralsites, response, log_kd."""
    config = config or load_config()
    df = da.prepare_data(raw, da.CONFIG)
    df = standardise_labels(df)

    out = df.copy()
    out["pH"] = df["_pH"]
    lo, hi = config["ph"]["valid_min"], config["ph"]["valid_max"]
    out["bad_ph"] = df["_pH"].isna() | (df["_pH"] < lo) | (df["_pH"] > hi)
    out["ionic_strength"] = df["_ionic_strength"]
    out["electrolyte_sig"] = df["_electrolyte_sig"]
    out["temp"] = df.get("_temp", pd.Series(np.nan, index=df.index))
    out["mineralsites"] = df.get("_mineralsites", pd.Series(np.nan, index=df.index))

    out["total_sorbate_mol_L"] = _to_unit(df["Sorbate_val"], df["Sorbate_units"], CONC_TO_MOL_L)
    out["solids_g_L"] = _to_unit(df["Mineral_val"], df["Mineral_units"], SOLIDS_TO_G_L)
    out["solids_m2_L"] = pd.to_numeric(df["Mineral_val"], errors="coerce").where(df["Mineral_units"] == "m2/L")
    out["co2_present"] = carbonate_flag(df)

    # Response on unit-corrected totals. Sorbed_val and Aq_val are mol/L in this file.
    tmp = pd.DataFrame({"Sorbed_val": df["Sorbed_val"], "Sorbate_val": out["total_sorbate_mol_L"],
                        "Aq_val": df["Aq_val"]})
    out["response"] = compute_response(tmp, mode="fraction_sorbed")
    out["log_kd"] = compute_response(tmp, mode="log_kd")
    return out


def load_observations(data_file=None, config=None):
    config = config or load_config()
    path = resolve_data_file(data_file, config)
    raw = pd.read_csv(path, low_memory=False)
    return clean_observations(raw, config), path


def unit_report(obs):
    """Counts of rows whose units could not be converted (reported, not hidden)."""
    return {
        "rows": len(obs),
        "bad_ph": int(obs["bad_ph"].sum()),
        "sorbate_units": obs["Sorbate_units"].value_counts(dropna=False).to_dict(),
        "solids_units": obs["Mineral_units"].value_counts(dropna=False).to_dict(),
        "solids_unconvertible": int((pd.to_numeric(obs["Mineral_val"], errors="coerce").notna()
                                     & obs["solids_g_L"].isna() & obs["solids_m2_L"].isna()).sum()),
        "response_missing": int(obs["response"].isna().sum()),
    }


def main():
    ap = argparse.ArgumentParser(description="Load and clean the raw sorption file.")
    ap.add_argument("--data", help="path to the raw CSV (overrides SORPTION_DATA_FILE)")
    args = ap.parse_args()
    obs, path = load_observations(args.data)
    print(f"Loaded {path}")
    for k, v in unit_report(obs).items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
