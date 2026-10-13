import numpy as np
import pandas as pd

from phslope.experiments.e23_placebo_power import shuffle_within


def test_shuffle_within_keeps_group_values():
    df = pd.DataFrame({"g": ["a"] * 5 + ["b"] * 5, "x": np.arange(10.0)})
    out = shuffle_within(df, "x", "g", np.random.default_rng(0))
    for g in "ab":
        assert sorted(out.loc[out.g == g, "x"]) == sorted(df.loc[df.g == g, "x"])
