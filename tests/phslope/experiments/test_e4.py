import numpy as np
import pandas as pd

from phslope.experiments import harness as H
from phslope.experiments.e04_lab_effect import lab_ids


def test_lab_ids_from_reference_codes():
    t = lab_ids(["azbn00", "azbn03", "az01", "d01", "emibsgg17"]).set_index("reference")
    assert t.loc["azbn00", "lab_exact"] == t.loc["azbn03", "lab_exact"] == "azbn"
    assert t.loc["az01", "lab_exact"] != t.loc["azbn00", "lab_exact"]
    assert t.loc["az01", "lab_coarse"] == t.loc["azbn00", "lab_coarse"] == "az"


def test_baselines_can_require_a_different_lab():
    rows = []
    for k, (unit, lab, edge) in enumerate([("p1", "L1", 5.0), ("p2", "L1", 5.1), ("p3", "L2", 7.0)]):
        rows.append({"curve_id": f"c{k}", "unit": unit, "lab": lab, "edge": edge, "grp": "g", "sorbate_class": "x",
                     "shape": "rising", "log10_solids": 0.0, "log10_total": -6.0, "log10_I": -1.0, "co2": 0.0,
                     "cosolute": 0.0, "background": "nitrate"})
    c = pd.DataFrame(rows)
    p_any = H.baseline_predictions(c, unit_col="unit").set_index("curve_id")
    p_diff = H.baseline_predictions(c, unit_col="unit", also_differ=("lab",)).set_index("curve_id")
    assert p_any.loc["c0", "B1_nearest1"] == 5.1          # same-lab paper is the closest match
    assert p_diff.loc["c0", "B1_nearest1"] == 7.0         # forced to another lab
