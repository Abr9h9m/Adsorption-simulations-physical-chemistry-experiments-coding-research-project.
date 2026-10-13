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


def test_paired_uses_difference_of_medians_robust_to_ties():
    rng = np.random.default_rng(1)
    n = 200
    base = np.abs(rng.normal(0, 1, n))
    model = base.copy()
    model[:60] = base[:60] * 0.3                               # better on 30% of curves, tied elsewhere
    L = pd.concat([pd.DataFrame({"curve_id": np.arange(n), "unit": np.arange(n) % 40, "model": m, "edge_error": e})
                   for m, e in (("m", model), ("b", base))])
    d = H.paired(L, "m", ["b"], B=300).iloc[0]
    assert d["median_of_diffs"] == 0 and d["share_tied"] >= 0.6     # the degenerate statistic
    assert d["median_diff"] < 0 and d["diff_hi"] < 0               # the decision statistic sees the gain


def test_paper_weighted_median_counts_each_unit_once():
    # unit u1 has 9 curves with error 0.1, units u2..u4 one curve each with error 2.0
    L = pd.DataFrame({"curve_id": range(12), "unit": ["u1"] * 9 + ["u2", "u3", "u4"], "model": "m",
                      "edge_error": [0.1] * 9 + [2.0] * 3})
    s = H.summarize(L, B=0).iloc[0]
    assert s["median"] == 0.1 and s["median_paper_weighted"] == 2.0
