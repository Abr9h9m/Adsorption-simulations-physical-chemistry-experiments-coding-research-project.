import numpy as np

from phslope.experiments.e11_slope import near_half_integer_share


def test_near_half_integer_share():
    assert near_half_integer_share([1.0, 1.5, 2.05, 0.97], 0.1) == 1.0
    assert near_half_integer_share([1.25, 0.75], 0.1) == 0.0
    rng = np.random.default_rng(0)
    assert abs(near_half_integer_share(rng.uniform(0, 5, 20000), 0.1) - 0.4) < 0.02
