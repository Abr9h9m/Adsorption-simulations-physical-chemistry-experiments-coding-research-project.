import numpy as np
import pytest

from phslope.predictor import PredictorError, load_model, predict_slope_curve

COND = {"solids_g_L": 1.0, "total_sorbate_mol_L": 1e-6, "ionic_strength": 0.1}


@pytest.fixture(scope="module")
def model(real_file):
    return load_model()


def test_known_pair_prediction_shapes_and_bands(model):
    out = predict_slope_curve("goethite", "U(+6)", COND, model=model)
    g, lo, hi = out["slope"], out["lower"], out["upper"]
    assert len(g) == len(out["grid"]) == 37 and out["direction"] == "rising"
    assert (lo <= hi + 1e-12).all() and (g >= 0).all()
    assert out["fraction"][0] < out["fraction"][-1]
    assert out["edge_lo"] <= out["edge_pH"] <= out["edge_hi"]
    assert any("EXPLORATORY" in n for n in out["notes"])


def test_unseen_pair_and_extrapolation_warn(model):
    out = predict_slope_curve("zirconia", "Se(+4)", dict(COND, solids_g_L=900.0), model=model)
    text = " ".join(out["notes"])
    assert "NOT in the training data" in text and "extrapolation" in text and out["direction"] == "falling"


def test_missing_condition_raises(model):
    with pytest.raises(PredictorError, match="missing"):
        predict_slope_curve("goethite", "U(+6)", {"solids_g_L": 1.0}, model=model)
    with pytest.raises(PredictorError, match="not in the training data"):
        predict_slope_curve("goethite", "Xx(+9)", COND, model=model)
