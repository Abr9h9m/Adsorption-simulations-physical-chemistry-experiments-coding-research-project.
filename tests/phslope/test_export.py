import numpy as np
import pandas as pd
import pytest

from phslope.common import load_config, load_thresholds
from phslope.export import CURVES_COLS, SCHEMA_VERSION, run
from phslope.library import save_library
from phslope.stage1 import run_synthetic


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    cfg = load_config()
    lib, _, obs = run_synthetic(cfg, load_thresholds()["qc"], None, workers=1, B=10, n_per_shape=4)
    m = lib["meta"]
    m["reference"], m["mineral"], m["sorbate"] = "ref", "goethite", m["true_shape"]
    m["electrolyte_sig"], m["temp"] = "N(+5)+Na(+1)", np.nan
    d = tmp_path_factory.mktemp("lib")
    save_library(lib, d)
    out = tmp_path_factory.mktemp("export")
    run(str(d), str(out), obs)
    return lib, obs, out


def test_files_and_schema(exported):
    _, _, out = exported
    cm = pd.read_csv(out / "curves_meta.csv")
    assert list(cm.columns) == CURVES_COLS + ["schema_version", "library_status"]
    for f in ("curves_meta.csv", "slope_grid.csv", "observations.csv", "pair_summary.csv"):
        assert (pd.read_csv(out / f)["schema_version"] == SCHEMA_VERSION).all()


def test_slope_grid_is_long_and_unobserved_is_blank(exported):
    lib, _, out = exported
    sg = pd.read_csv(out / "slope_grid.csv")
    assert len(sg) == lib["G"].size
    assert sg.loc[~sg["observed"], "slope"].isna().all()


def test_observations_fitted_close_to_data(exported):
    _, obs, out = exported
    o = pd.read_csv(out / "observations.csv")
    assert len(o) == len(obs)
    ok = o["fitted"].notna()
    assert np.sqrt(np.mean((o.loc[ok, "fitted"] - o.loc[ok, "response"]) ** 2)) < 0.1
    assert set(o["fitted_method"]) <= {"exact", "grid_interpolation", "none"}


def test_pair_summary_counts(exported):
    lib, _, out = exported
    ps = pd.read_csv(out / "pair_summary.csv")
    assert ps["curve_count"].sum() == len(lib["curve_ids"])
    assert not ps["predicted"].any()
