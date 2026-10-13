import numpy as np
import pandas as pd
import pytest

from phslope.experiments.e21_conformal_metrics import conformal, edges_from_line, frac


def test_edges_from_line_consistent_forms():
    e1 = edges_from_line(np.array([0.5]), np.array([1.0]), np.array([6.0]))
    e2 = edges_from_line(None, np.array([1.0]), None, a=np.array([0.5 - 6.0]))
    for k in ("pH20", "pH50", "pH80", "width"):
        assert e1[k][0] == pytest.approx(e2[k][0])
    assert e1["pH50"][0] == pytest.approx(5.5) and e1["width"][0] == pytest.approx(2 * np.log10(4))
    assert frac(0.0) == pytest.approx(0.5)


def test_conformal_cv_plus_covers_exchangeable_errors():
    rng = np.random.default_rng(0)
    n_u = 60
    P = pd.DataFrame({"unit": np.repeat(np.arange(n_u), 3), "pred_edge": 6.0})
    P["pH_native"] = 6.0 + rng.normal(0, 1, len(P))
    out = conformal(P, 0.9)
    cov = ((out["pH_native"] >= out["conf_lo"]) & (out["pH_native"] <= out["conf_hi"])).mean()
    assert 0.82 <= cov <= 0.97
