import numpy as np
import pandas as pd

from phslope.experiments.data import _atmosphere, _gas_co2
from phslope.experiments.e07_carbonate import carbonate_columns


def _g(gases):
    d = {}
    for i, (lab, val) in enumerate(gases, start=1):
        d[f"Gas{i}"], d[f"Gas{i}_val"] = [lab], [val]
    return pd.DataFrame(d)


def test_atmosphere_classes():
    air = _g([("N2(g)", 0.8), ("O2(g)", 0.2), ("CO2(g)", 3.6e-4)])
    assert _atmosphere(air, _gas_co2(air)) == "air_equilibrated"
    ctrl = _g([("CO2(g)", 0.01)])
    assert _atmosphere(ctrl, _gas_co2(ctrl)) == "controlled_co2"
    n2 = _g([("N2(g)", 1.0)])
    assert np.isnan(_gas_co2(n2)) and _atmosphere(n2, np.nan) == "co2_free"
    none = pd.DataFrame({"Gas1": [np.nan], "Gas1_val": [np.nan]})
    assert _atmosphere(none, np.nan) == "unknown"


def test_pco2_floor_and_unknown_indicator():
    c = pd.DataFrame({"log10_pco2": [-3.4, np.nan, np.nan], "atmosphere": ["air_equilibrated", "co2_free", "unknown"]})
    out = carbonate_columns(c, -6.0)
    assert list(out["log10_pco2_f"]) == [-3.4, -6.0, -6.0] and list(out["atmosphere_unknown"]) == [0, 0, 1]
