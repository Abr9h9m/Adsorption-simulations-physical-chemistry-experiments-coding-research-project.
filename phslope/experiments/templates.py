"""templates.py -- human-entry tables for E6, E9, E10 and the priority list (protocol sections 5, 8 D4).

Writes (never overwriting a file that already has content beyond the header):
  data/descriptors/sorbate_chemistry.csv  E6  one row per sorbate
  data/descriptors/study_materials.csv    E9  one row per (reference, mineral)
  data/descriptors/study_methods.csv      E10 one row per reference
  reports/phslope/experiments/DATA_ENTRY_PRIORITY.csv   references ranked by curves in pairs with >= 3 papers
Values come from cited sources entered by Samuel or Abraham; Claude Code never fills them.
The dataset's own surface area and material source are pre-filled as REFERENCE columns
(dataset_surface_area_m2_g, dataset_mineral_source) so the person entering data can check them; the
columns to fill are left empty.
"""
import os

import numpy as np
import pandas as pd

from phslope.common import DESCRIPTOR_DIR
from phslope.experiments.registry import EXP_DIR

SORBATE_COLS = ["sorbate", "element", "oxidation_state", "speciation_class", "effective_charge", "ionic_radius_A",
                "log_K_hydrolysis_1", "pKa1", "pKa2", "pKa3", "source", "source_version", "notes"]
MATERIAL_COLS = ["reference", "mineral", "dataset_surface_area_m2_g", "dataset_mineral_source", "material_type",
                 "synthesis_or_source", "surface_area_m2_g", "surface_area_method", "source_page_or_table", "notes"]
METHOD_COLS = ["reference", "equilibration_time_h", "solid_pre_equilibration_h", "atmosphere", "separation",
               "container", "pH_adjustment", "pH_measured_when", "sorbate_stock_source", "source_page_or_table", "notes"]


def _write_if_empty(df, path):
    if os.path.exists(path):
        old = pd.read_csv(path, dtype=str)
        filled = old.drop(columns=[c for c in old.columns if c in ("sorbate", "reference", "mineral")
                                   or c.startswith("dataset_")], errors="ignore")
        if filled.notna().any().any():
            return f"{os.path.basename(path)} kept (already has entries)"
    df.to_csv(path, index=False)
    return f"{os.path.basename(path)} written ({len(df)} rows)"


def priority(curves):
    """References ranked by number of curves in mineral-sorbate pairs measured by >= 3 papers."""
    c = curves[curves["shape"].isin(["rising", "falling"])].copy()
    c["pair"] = c["mineral"] + " | " + c["sorbate"]
    n_ref = c.groupby("pair")["reference"].nunique()
    c = c[c["pair"].map(n_ref) >= 3]
    p = c.groupby("reference").agg(curves_in_pairs_with_3plus_papers=("curve_id", "size"),
                                   pairs=("pair", lambda s: "; ".join(sorted(s.unique())))).reset_index()
    p = p.sort_values("curves_in_pairs_with_3plus_papers", ascending=False).reset_index(drop=True)
    p["priority_rank"] = np.arange(1, len(p) + 1)
    p["fill_first"] = p["priority_rank"] <= 40
    return p


def run(curves):
    """`curves`: ALL curves (development and locked; data entry is not analysis)."""
    os.makedirs(DESCRIPTOR_DIR, exist_ok=True)
    out = []
    s = pd.DataFrame({c: "" for c in SORBATE_COLS}, index=range(curves["sorbate"].nunique()))
    s["sorbate"] = sorted(curves["sorbate"].unique())
    out.append(_write_if_empty(s, os.path.join(DESCRIPTOR_DIR, "sorbate_chemistry.csv")))
    m = curves.groupby(["reference", "mineral"]).agg(
        dataset_surface_area_m2_g=("surface_area_m2_g", "median"),
        dataset_mineral_source=("mineral_source", lambda x: x.dropna().iloc[0] if x.notna().any() else "")).reset_index()
    for col in MATERIAL_COLS:
        if col not in m:
            m[col] = ""
    out.append(_write_if_empty(m[MATERIAL_COLS], os.path.join(DESCRIPTOR_DIR, "study_materials.csv")))
    t = pd.DataFrame({c: "" for c in METHOD_COLS}, index=range(curves["reference"].nunique()))
    t["reference"] = sorted(curves["reference"].unique())
    out.append(_write_if_empty(t, os.path.join(DESCRIPTOR_DIR, "study_methods.csv")))
    p = priority(curves)
    os.makedirs(EXP_DIR, exist_ok=True)
    p.to_csv(os.path.join(EXP_DIR, "DATA_ENTRY_PRIORITY.csv"), index=False)
    out.append(f"DATA_ENTRY_PRIORITY.csv written ({len(p)} references; top 40 marked)")
    return out


if __name__ == "__main__":
    from phslope.experiments.data import build
    curves, _ = build(include_locked=True, purpose="data-entry templates and priority list (no outcomes used)")
    for line in run(curves):
        print(line)
