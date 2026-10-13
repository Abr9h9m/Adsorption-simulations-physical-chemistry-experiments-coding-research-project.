"""descriptors.py -- descriptor tables and the feature matrix for Stage 3 (spec section 8).

Descriptor tables (data/descriptors/): one row per mineral / sorbate, filled by
Samuel with a source for every value. The loader REFUSES a row that has a value
but no source (spec section 8). Missing stays missing; missingness is reported.

Feature sets for the transfer model (`feature_set` argument):
  descriptors   spec descriptors: pzc (mid of low/high), surface area, first
                hydrolysis logK, oxidation state, speciation class (one-hot)
  properties    Samuel's mineral property table (T/F columns) + sorbate schemes
                from schemes.yaml (one-hot). EXPLORATORY: uncited, used because
                the descriptor tables are still empty.
  conditions    always added: log10 solids, log10 total sorbate, log10 ionic
                strength, carbonate flag.
Rows with any missing feature are dropped from that model and counted (no mean
imputation, spec 4.10).
"""
import os

import numpy as np
import pandas as pd

from phslope.common import DESCRIPTOR_DIR, REPORTS_DIR

MINERAL_SOURCES = {"pzc_low": "pzc_source", "pzc_high": "pzc_source", "surface_area_m2_g": "surface_area_source"}
SORBATE_SOURCES = {"first_hydrolysis_logK": "hydrolysis_source"}
CONDITION_FEATURES = ["log10_solids", "log10_total_sorbate", "log10_ionic_strength", "co2"]


class DescriptorError(ValueError):
    pass


def _check_sources(df, rules, key, label):
    bad = []
    for val_col, src_col in rules.items():
        if val_col not in df:
            continue
        has_val = pd.to_numeric(df[val_col], errors="coerce").notna()
        no_src = df.get(src_col, pd.Series("", index=df.index)).fillna("").astype(str).str.strip() == ""
        bad += [f"{r}: {val_col}" for r in df.loc[has_val & no_src, key]]
    if bad:
        raise DescriptorError(f"{label}: values without a source (spec section 8): {bad}")


def load_descriptors(directory=DESCRIPTOR_DIR):
    m = pd.read_csv(os.path.join(directory, "mineral_descriptors.csv"), dtype=str)
    s = pd.read_csv(os.path.join(directory, "sorbate_descriptors.csv"), dtype=str)
    _check_sources(m, MINERAL_SOURCES, "mineral", "mineral_descriptors.csv")
    _check_sources(s, SORBATE_SOURCES, "sorbate", "sorbate_descriptors.csv")
    for c in ("pzc_low", "pzc_high", "surface_area_m2_g"):
        m[c] = pd.to_numeric(m.get(c), errors="coerce")
    for c in ("first_hydrolysis_logK", "oxidation_state"):
        s[c] = pd.to_numeric(s.get(c), errors="coerce")
    m["pzc_mid"] = m[["pzc_low", "pzc_high"]].mean(axis=1)
    return m.set_index("mineral"), s.set_index("sorbate")


def missingness(m, s, out_dir=None):
    rows = [{"table": "mineral", "column": c, "filled": int(m[c].notna().sum()), "rows": len(m)}
            for c in ("pzc_low", "pzc_high", "surface_area_m2_g")]
    rows += [{"table": "sorbate", "column": c, "filled": int(s[c].notna().sum()), "rows": len(s)}
             for c in ("first_hydrolysis_logK", "oxidation_state", "speciation_class") if c in s]
    out = pd.DataFrame(rows)
    out["missing_fraction"] = 1 - out["filled"] / out["rows"].clip(lower=1)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        out.to_csv(os.path.join(out_dir, "descriptor_missingness.csv"), index=False)
    return out


def _one_hot(series, prefix):
    return pd.get_dummies(series, prefix=prefix, dtype=float).where(series.notna(), np.nan) if len(series) else \
        pd.DataFrame(index=series.index)


def condition_features(t):
    return pd.DataFrame({
        "log10_solids": np.log10(t["solids_g_L"].where(t["solids_g_L"] > 0)),
        "log10_total_sorbate": np.log10(t["total_sorbate_mol_L"].where(t["total_sorbate_mol_L"] > 0)),
        "log10_ionic_strength": np.log10(t["ionic_strength"].where(t["ionic_strength"] > 0)),
        "co2": t["co2_present"].astype(float),
    }, index=t.index)


def build_features(t, feature_set, descriptors=None, props=None, schemes_cfg=None):
    """Returns (X, report): X has one row per curve in t (NaN where a feature is missing)."""
    parts = [condition_features(t)]
    if feature_set == "descriptors":
        m, s = descriptors
        parts.append(pd.DataFrame({
            "pzc_mid": t["mineral"].map(m["pzc_mid"]),
            "surface_area": t["mineral"].map(m["surface_area_m2_g"]),
            "first_hydrolysis_logK": t["sorbate"].map(s["first_hydrolysis_logK"]),
            "oxidation_state": t["sorbate"].map(s["oxidation_state"]),
        }, index=t.index))
        if "speciation_class" in s:
            parts.append(_one_hot(t["sorbate"].map(s["speciation_class"]), "spec"))
    elif feature_set == "properties":
        prop = props.reindex(t["mineral"].to_numpy())
        prop.index = t.index
        keep = [c for c in prop.columns if prop[c].nunique(dropna=True) == 2]
        parts.append(prop[keep].add_prefix("prop_"))
        for name in ("sorbate_charge_form", "sorbate_element_group", "sorbate_redox"):
            parts.append(_one_hot(t["sorbate"].map(schemes_cfg["sorbate_schemes"][name]), name))
    elif feature_set != "conditions":
        raise ValueError(feature_set)
    X = pd.concat(parts, axis=1)
    X = X.loc[:, X.nunique(dropna=True) > 1]           # constant columns carry no information
    complete = X.notna().all(axis=1)
    return X, {"n_features": X.shape[1], "n_curves": len(X), "n_complete": int(complete.sum())}
