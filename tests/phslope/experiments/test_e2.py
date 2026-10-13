import numpy as np
import pandas as pd

from phslope.experiments.e02_weights_censoring import weight_W2
from phslope.experiments.kd import line_fit


def _sim(noise, seed):
    rng = np.random.default_rng(seed)
    errs0, errs2 = [], []
    for _ in range(200):
        pH = np.linspace(3, 9, 13)
        logK = -6 + 1.0 * pH
        f_true = 1 / (1 + 10 ** -logK)
        if noise == "fraction":                       # additive error in fraction sorbed + detection floor
            f = np.clip(f_true + rng.normal(0, 0.02, len(pH)), 0.005, 0.995)
            y = np.log10(f / (1 - f))
        else:                                         # homoscedastic error in log10 K
            y = logK + rng.normal(0, 0.1, len(pH))
            f = 1 / (1 + 10 ** -y)
        m = (f > 0.03) & (f < 0.97)
        if m.sum() < 3:
            continue
        g = pd.DataFrame({"response": f[m]})
        errs0.append(abs(line_fit(pH[m], y[m])["b"] - 1.0))
        errs2.append(abs(line_fit(pH[m], y[m], weight_W2(g))["b"] - 1.0))
    return np.median(errs0), np.median(errs2)


def test_w2_beats_w0_under_fraction_space_noise():
    e0, e2 = _sim("fraction", 1)
    assert e2 < e0


def test_w0_not_worse_under_homoscedastic_logk_noise():
    e0, e2 = _sim("logk", 2)
    assert e0 <= e2 * 1.05


def test_weighted_line_fit_reduces_to_ols_with_equal_weights():
    pH = np.array([4., 5, 6, 7]); y = np.array([-2.1, -0.9, 0.1, 1.05])
    a = line_fit(pH, y); b = line_fit(pH, y, np.full(4, 3.0))
    assert np.isclose(a["b"], b["b"]) and np.isclose(a["a"], b["a"])
