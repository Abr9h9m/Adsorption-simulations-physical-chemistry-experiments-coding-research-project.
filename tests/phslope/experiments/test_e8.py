import numpy as np
import pandas as pd

from phslope.experiments.e08_ionic_strength import assign_class, clustered_slope, within_paper_series


def test_assign_class():
    cl = {"outer": ["Cs(+1)"], "inner": ["U(+6)"]}
    assert assign_class("Cs(+1)", cl) == "outer" and assign_class("Zz", cl) == "unclassified"


def test_within_paper_series_requires_matched_conditions():
    rows = []
    for k, (I, sol) in enumerate([(0.01, 1.0), (0.1, 1.05), (1.0, 3.0)]):       # third differs in solids
        rows.append({"curve_id": f"c{k}", "reference": "p1", "pair_dir": "g|U|rising", "log10_I": np.log10(I),
                     "solids_g_L": sol, "total_sorbate_mol_L": 1e-6, "temp": np.nan})
    s = within_paper_series(pd.DataFrame(rows), 0.10)
    assert list(s["curve_id"]) == ["c0", "c1"]


def test_clustered_slope_recovers_planted_effect():
    rng = np.random.default_rng(0)
    g = np.repeat(np.arange(30), 4)
    x = rng.normal(size=120)
    y = 0.4 * x + rng.normal(0, 0.1, 120) + np.repeat(rng.normal(0, 0.05, 30), 4)
    r = clustered_slope(y, x, g)
    assert r["ci_lo"] < 0.4 < r["ci_hi"] and r["ci_lo"] > 0
    r0 = clustered_slope(rng.normal(0, 0.1, 120), x, g)
    assert r0["ci_lo"] < 0 < r0["ci_hi"]
