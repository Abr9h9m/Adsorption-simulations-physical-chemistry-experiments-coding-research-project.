import numpy as np
import pandas as pd

from phslope.experiments.e13_competition import competitor_molarity, within_pair_effect


def test_competitor_molarity_excludes_own_sorbate_and_background():
    obs = pd.DataFrame({"curve_id": ["c1"] * 2, "Electrolyte1": ["Na(+1)"] * 2, "Electrolyte1_val": [0.1] * 2,
                        "Electrolyte2": ["P(+5)"] * 2, "Electrolyte2_val": [1e-4] * 2,
                        "Electrolyte3": ["Citrate(-3)"] * 2, "Electrolyte3_val": [1e-3] * 2,
                        "Electrolyte4": ["Se(+4)"] * 2, "Electrolyte4_val": [1e-5] * 2})
    m = competitor_molarity(obs, {"P(+5)", "Se(+4)"}, {"c1": "Se(+4)"}).iloc[0]
    assert np.isclose(m["competitor_mol_L"], 1.1e-3) and m["competitors"] == "Citrate(-3);P(+5)"


def test_within_pair_effect_detects_planted_negative_effect():
    rng = np.random.default_rng(0)
    rows = []
    for p in range(15):
        for k in range(6):
            x = rng.choice([-7.0, -4.0])
            rows.append({"pair_dir": f"p{p}", "unit": f"u{p}_{k % 3}", "x": x, "y": -0.3 * x + rng.normal(0, .1)})
    r = within_pair_effect(pd.DataFrame(rows), "y", "x")
    assert r["ci_hi"] < 0 and abs(r["coef"] + 0.3) < 0.05
