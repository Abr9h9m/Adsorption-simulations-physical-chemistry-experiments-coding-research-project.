"""Sorption pack: the only place with sorption-specific logic (WEB_INTERFACE_PROTOCOL.md section 2).

Reuses the analysis code so web numbers equal analysis numbers:
  ionic_strength         data_audit.compute_ionic_strength (oxyanion charges corrected)
  electrolyte_signature  data_audit.electrolyte_signature
  fraction               fraction sorbed = Sorbed / total, total converted to mol/L first; falls back to
                         1 - Aq / total when Sorbed is missing (phslope.load / response.compute_response)
"""
import pandas as pd

import data_audit
from phslope.load import CONC_TO_MOL_L
from response import compute_response


def ionic_strength(d):
    return data_audit.compute_ionic_strength(d, 7)


def electrolyte_signature(d):
    return data_audit.electrolyte_signature(d, 7)


def total_mol_L(d):
    return pd.to_numeric(d["Sorbate_val"], errors="coerce") * d["Sorbate_units"].map(CONC_TO_MOL_L)


def fraction(d):
    tmp = pd.DataFrame({"Sorbed_val": d["Sorbed_val"], "Sorbate_val": total_mol_L(d), "Aq_val": d["Aq_val"]})
    return compute_response(tmp, mode="fraction_sorbed")


def log_kd(d):
    tmp = pd.DataFrame({"Sorbed_val": d["Sorbed_val"], "Sorbate_val": total_mol_L(d), "Aq_val": d["Aq_val"]})
    return compute_response(tmp, mode="log_kd")


# ---------------------------------------------------------------- optional hooks used by curvelib.api

def entity_picker(curves, coverage):
    from packs.sorption.entities import entity_picker as _ep
    return _ep(curves, coverage)


def predict(params):
    """Model prediction for the web interface (EXPLORATORY; development-paper model, never the locked papers)."""
    from phslope.predictor import predict_slope_curve
    out = predict_slope_curve(params["group_a"], params["group_b"],
                              {"solids_g_L": float(params["solids_g_L"]),
                               "total_sorbate_mol_L": float(params["total_sorbate_mol_L"]),
                               "ionic_strength": float(params["ionic_strength"])},
                              direction=params.get("direction"))
    return {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in out.items()}
