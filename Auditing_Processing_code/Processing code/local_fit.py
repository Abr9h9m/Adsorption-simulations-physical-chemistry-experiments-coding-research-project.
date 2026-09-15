"""
local_fit.py -- OWNER: split -- design_matrix (you), fit_weighted_quadratic (CS collaborator)

Fits a local quadratic surface to a small, weighted neighborhood of points,
in the (deliberately) scaled basis that avoids the factor-of-2 Hessian bug.
"""

import numpy as np


def design_matrix(delta_pH: np.ndarray, delta_I: np.ndarray) -> np.ndarray:
    """
    [YOU BUILD THIS]
    N x 6 design matrix, columns in this exact order:
      [1, dpH, dI, 0.5*dpH^2, 0.5*dI^2, dpH*dI]
    The 0.5 factor on the squared terms is deliberate -- it's what makes the
    fitted coefficients equal the Hessian entries directly, with no
    factor-of-2 correction needed later. Do not remove it.
    """
    ones = np.ones_like(delta_pH)
    return np.column_stack([
        ones,
        delta_pH,
        delta_I,
        0.5 * delta_pH**2,
        0.5 * delta_I**2,
        delta_pH * delta_I,
    ])


def fit_weighted_quadratic(Phi: np.ndarray, y: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    [CS COLLABORATOR BUILDS THIS]
    Weighted least squares via sqrt(weight) row-scaling + ordinary lstsq
    (more numerically stable than forming Phi.T @ W @ Phi directly).
    Returns theta = [a0, b_pH, b_I, C_pH_pH, C_I_I, C_pH_I]
    """
    sqrt_w = np.sqrt(weights)
    Phi_weighted = Phi * sqrt_w[:, None]
    y_weighted = y * sqrt_w
    theta, residuals, rank, sv = np.linalg.lstsq(Phi_weighted, y_weighted, rcond=None)
    return theta


if __name__ == "__main__":
    # Validation test: recover a KNOWN gradient/Hessian exactly (no noise).
    # Written in the SAME convention the fit uses (Math spec section 2):
    #   z = a0 + b.dx + 0.5 * dx^T H dx
    # so the recovered theta should equal these values directly, with NO
    # factor of 2 anywhere -- if you instead write a plain polynomial like
    # "0.5*x**2" and expect the fitted coefficient to match that same 0.5,
    # you'll be off by 2x on the diagonal terms. That mismatch is not a bug
    # in the fit -- it's exactly the factor-of-2 trap this basis convention
    # is designed to avoid, so this test writes ground truth the correct way.
    rng = np.random.default_rng(1)
    n = 50
    dpH = rng.uniform(-1, 1, n)
    dI = rng.uniform(-1, 1, n)

    a0_true = 2.0
    b_true = np.array([3.0, -1.0])          # gradient
    H_true = np.array([[1.0, 0.2],          # Hessian: [[Hpp, Hpi],[Hpi, Hii]]
                        [0.2, -0.6]])

    z_true = (a0_true
              + b_true[0]*dpH + b_true[1]*dI
              + 0.5*(H_true[0,0]*dpH**2 + 2*H_true[0,1]*dpH*dI + H_true[1,1]*dI**2))

    Phi = design_matrix(dpH, dI)
    weights = np.ones(n)  # uniform weights for this pure recovery test
    theta = fit_weighted_quadratic(Phi, z_true, weights)

    print("Recovered theta:", np.round(theta, 4))
    print("Expected:       ", [a0_true, *b_true, H_true[0,0], H_true[1,1], H_true[0,1]])
    print("(theta[3] and theta[4] ARE the Hessian diagonal directly -- no factor-of-2 correction needed)")
