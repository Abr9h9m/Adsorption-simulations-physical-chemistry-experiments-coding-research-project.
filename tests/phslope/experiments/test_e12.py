import numpy as np
import pandas as pd

from phslope.experiments.e12_loading import _shape, fit_saturation


def test_one_site_saturation_recovered():
    rng = np.random.default_rng(0)
    rows = []
    for p in range(12):
        c = rng.normal(0, 1)
        for L in np.linspace(-8, -2, 8):
            rows.append({"pair_dir": f"p{p}", "log10L": L,
                         "logKd": c + _shape([-4.0], np.array([L]), False)[0] + rng.normal(0, 0.03)})
    d = pd.DataFrame(rows)
    assert abs(fit_saturation(d, False)[0] + 4.0) < 0.2
