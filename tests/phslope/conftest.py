import os

import numpy as np
import pandas as pd
import pytest

from phslope.common import resolve_data_file


def make_raw(sets):
    """Minimal Appendix A rows. `sets` is a list of dicts with keys
    set, ref, pH (list), and optional overrides (see below)."""
    rows = []
    for s in sets:
        n = len(s["pH"])
        tot = s.get("tot", 1e-6)
        for i, ph in enumerate(s["pH"]):
            frac = s.get("frac", [0.5] * n)[i]
            rows.append({
                "Reference": s["ref"], "Set": s["set"], "SetID": i + 1,
                "Mineral": s.get("mineral", "goethite"), "Mineral_formula": "FeOOH",
                "Sorbate": s.get("sorbate", "U(+6)"),
                "Electrolyte1": s.get("e1", "Na(+1)"), "Electrolyte1_val": s.get("I", 0.1),
                "Electrolyte2": s.get("e2", "N(+5)"), "Electrolyte2_val": s.get("I", 0.1),
                "pH": ph, "Temp": np.nan,
                "Sorbate_val": s.get("tot_list", [tot] * n)[i],
                "Sorbate_units": s.get("tot_units", "mol/L"),
                "Sorbed_val": frac * tot * s.get("sorbed_scale", 1.0), "Sorbed_units": "mol/L",
                "Aq_val": (1 - frac) * tot, "Aq_units": "mol/L",
                "Mineral_val": s.get("solids", 1.0), "Mineral_units": s.get("solids_units", "g/L"),
                "Mineralsites": 2.0,
                "Gas1": s.get("gas", "N2(g)"), "Gas1_val": s.get("gas_val", 1.0),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def raw_small():
    return make_raw([
        {"set": "r1_f1", "ref": "r1", "pH": [3, 4, 5, 6, 7, 8], "frac": [0, .1, .4, .8, .95, 1]},
        {"set": "r1_f2", "ref": "r1", "pH": [5, 5, 5, 5], "tot_list": [1e-7, 1e-6, 1e-5, 1e-4]},
        {"set": "r2_f1", "ref": "r2", "sorbate": "Se(-2)", "pH": [4, 6, 8, 10], "gas": "CO2(g)"},
    ])


@pytest.fixture(scope="session")
def real_file():
    path = resolve_data_file()
    if not os.path.exists(path):
        pytest.skip(f"real data file not found: {path}")
    return path


@pytest.fixture(scope="session")
def real_obs(real_file):
    from phslope.load import load_observations
    obs, _ = load_observations(real_file)
    return obs
