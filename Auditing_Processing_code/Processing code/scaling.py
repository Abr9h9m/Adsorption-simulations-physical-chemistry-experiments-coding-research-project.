"""
scaling.py -- OWNER: you (chemistry/analysis lead)

Rescales pH and ionic strength onto comparable [0,1] footing before fitting,
and converts derivatives back to real units afterward via the chain rule.
See Mathematical_Formulation.md section 13 for the reasoning.
"""

import numpy as np


def fit_scaler(pH_all: np.ndarray, I_all: np.ndarray) -> dict:
    """
    Computes min/max for each dimension from the full dataset (once per
    system, not once per query point).
    """
    return {
        "pH_min": float(np.min(pH_all)),
        "pH_max": float(np.max(pH_all)),
        "I_min": float(np.min(I_all)),
        "I_max": float(np.max(I_all)),
    }


def to_scaled(pH: np.ndarray, I: np.ndarray, scaler: dict) -> tuple:
    """Min-max scales pH and I to [0, 1] using the fitted scaler."""
    pH_scaled = (pH - scaler["pH_min"]) / (scaler["pH_max"] - scaler["pH_min"])
    I_scaled = (I - scaler["I_min"]) / (scaler["I_max"] - scaler["I_min"])
    return pH_scaled, I_scaled


def gradient_to_real_units(grad_scaled: np.ndarray, scaler: dict) -> np.ndarray:
    """Converts a gradient from scaled coordinates back to real units."""
    pH_range = scaler["pH_max"] - scaler["pH_min"]
    I_range = scaler["I_max"] - scaler["I_min"]
    return np.array([grad_scaled[0] / pH_range, grad_scaled[1] / I_range])


def hessian_to_real_units(hess_scaled: np.ndarray, scaler: dict) -> np.ndarray:
    """Converts a 2x2 Hessian from scaled coordinates back to real units."""
    pH_range = scaler["pH_max"] - scaler["pH_min"]
    I_range = scaler["I_max"] - scaler["I_min"]
    H_pp = hess_scaled[0, 0] / pH_range**2
    H_ii = hess_scaled[1, 1] / I_range**2
    H_pi = hess_scaled[0, 1] / (pH_range * I_range)
    return np.array([[H_pp, H_pi], [H_pi, H_ii]])


if __name__ == "__main__":
    # Quick manual check -- run `python scaling.py` to sanity-check by eye.
    pH_all = np.array([3.0, 5.0, 7.0, 9.0])
    I_all = np.array([0.01, 0.05, 0.1, 0.5])
    scaler = fit_scaler(pH_all, I_all)
    print("Scaler:", scaler)

    pH_s, I_s = to_scaled(pH_all, I_all, scaler)
    print("Scaled pH:", pH_s)
    print("Scaled I:", I_s)

    fake_grad_scaled = np.array([1.0, 1.0])
    print("Unscaled gradient:", gradient_to_real_units(fake_grad_scaled, scaler))

    fake_hess_scaled = np.array([[1.0, 0.5], [0.5, 1.0]])
    print("Unscaled Hessian:\n", hessian_to_real_units(fake_hess_scaled, scaler))
