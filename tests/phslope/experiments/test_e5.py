import numpy as np
import pandas as pd

from phslope.experiments.e05_coverage import fit_error_model, predict_error


def test_error_model_learns_planted_dependence():
    rng = np.random.default_rng(0)
    n = 400
    d = pd.DataFrame({"se_b": 10 ** rng.uniform(-2.5, -0.5, n), "abs_b": 1.0, "extrap_dist": rng.uniform(0, 2, n),
                      "n_mid": rng.integers(3, 15, n)})
    true = 10 ** (0.5 + 0.8 * np.log10(d["se_b"]) + 0.3 * d["extrap_dist"])
    d["edge_error"] = true * 10 ** rng.normal(0, 0.1, n)
    beta, sd = fit_error_model(d)
    assert abs(beta[1] - 0.8) < 0.1 and abs(beta[2] - 0.3) < 0.1 and sd < 0.15
    assert np.corrcoef(np.log10(predict_error(beta, d)), np.log10(true))[0, 1] > 0.95
