"""Regression tests for the unit/eigenvector/response fixes. Run: python test_fixes.py"""
import numpy as np, pandas as pd
from scaling import *
from compare import hessian_shape_similarity, eigenvector_orientation_angle, dominant_eigenvector
from fingerprint import fingerprint_vector
from response import compute_response

def test_scaled_roundtrip():
    s = {"pH_min": 3, "pH_max": 10, "I_min": 0.01, "I_max": 0.5}
    g = np.array([1.3, -4.0]); H = np.array([[0.2, 0.05], [0.05, -0.7]])
    assert np.allclose(gradient_to_real_units(gradient_to_scaled_units(g, s), s), g)
    assert np.allclose(hessian_to_real_units(hessian_to_scaled_units(H, s), s), H)

def test_dominant_eigenvector_uses_magnitude():
    # strongly NEGATIVE curvature along pH (axis 0), weak positive along I (axis 1)
    H = np.diag([-5.0, 0.5])
    v = dominant_eigenvector(H)
    assert abs(v[0]) > 0.99, "must pick the pH axis (largest |lambda|), not the most positive eigenvalue"
    assert eigenvector_orientation_angle(H, np.diag([-3.0, 0.2])) < 1e-6

def test_orientation_is_sign_invariant():
    a = np.array([[2.0, 1.0], [1.0, 2.0]]); assert eigenvector_orientation_angle(a, a) < 1e-6

def test_raw_units_saturate_but_scaled_discriminates():
    # Same physical curvature in two systems, but different (pH, I) ranges. In raw units
    # the I-I entry dwarfs the rest; in scaled coordinates the shapes are genuinely different.
    sA = {"pH_min": 3, "pH_max": 11, "I_min": 0.1, "I_max": 0.9}
    sB = {"pH_min": 2, "pH_max": 10, "I_min": 0.05, "I_max": 0.43}
    HA_scaled = np.array([[0.0014, 0.0043], [0.0043, 0.0029]])   # cross-term dominant
    HB_scaled = np.array([[0.0043, 0.0006], [0.0006, 0.0043]])   # diagonal dominant
    rawA, rawB = hessian_to_real_units(HA_scaled, sA), hessian_to_real_units(HB_scaled, sB)
    raw_cos = hessian_shape_similarity(rawA, rawB)               # (wrongly) fed raw units
    scaled_cos = hessian_shape_similarity(HA_scaled, HB_scaled)
    assert raw_cos > 0.95 and scaled_cos < 0.8, (raw_cos, scaled_cos)

def test_fingerprint_dominant_axis_is_unit_free():
    # identical response surface in two coordinate systems => identical dominant-axis fraction
    scalerA = {"pH_min": 0, "pH_max": 10, "I_min": 0, "I_max": 1}
    scalerB = {"pH_min": 0, "pH_max": 10, "I_min": 0, "I_max": 0.01}   # I in different units
    g_scaled = np.array([2.0, 1.0]); H_scaled = np.eye(2)
    def res(scaler):
        return {"gradient_scaled": g_scaled, "hessian_scaled": H_scaled,
                "gradient": gradient_to_real_units(g_scaled, scaler), "hessian": hessian_to_real_units(H_scaled, scaler)}
    _, a = fingerprint_vector([(1, 1)], [res(scalerA)]); _, b = fingerprint_vector([(1, 1)], [res(scalerB)])
    assert a["frac_pH_dominant"] == b["frac_pH_dominant"] == 1.0

def test_response_normalization():
    df = pd.DataFrame({"Sorbed_val": [1e-7, 9e-7], "Sorbate_val": [1e-6, 1e-6], "Aq_val": [9e-7, 1e-7]})
    assert np.allclose(compute_response(df).to_numpy(), [0.1, 0.9])

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"): fn(); print("PASS", name)