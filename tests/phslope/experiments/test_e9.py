import numpy as np
import pandas as pd

from phslope.experiments.e09_surface_area import within_pair_r2


def test_area_beats_mass_when_area_drives_the_edge():
    rng = np.random.default_rng(0)
    rows = []
    for p in range(20):
        for k in range(6):
            ls = rng.uniform(-1, 1); sa = rng.uniform(0, 2)        # log10 g/L, log10 m2/g
            area = ls + sa
            rows.append({"pair_dir": f"p{p}", "shape": "rising", "log10_solids": ls, "log10_area": area,
                         "pH_native": 6 - 0.8 * area + rng.normal(0, 0.1)})
    c = pd.DataFrame(rows)
    assert within_pair_r2(c, "log10_area")["R2"] > 1.2 * within_pair_r2(c, "log10_solids")["R2"]
    assert abs(within_pair_r2(c, "log10_area")["slope_rising"] + 0.8) < 0.05
