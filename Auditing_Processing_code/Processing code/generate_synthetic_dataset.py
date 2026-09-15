"""
Synthetic Pilot Dataset — for building and testing the fitting pipeline
=========================================================================
Generates a clean, well-covered, schema-matched dataset for the four pilot
systems, using known closed-form "ground truth" response functions. This is
NOT meant to replicate the current real dataset's pooled/clustered ionic-
strength problem — it's deliberately well-behaved, standing in for what a
properly-designed dataset should look like, so surrogate.py / derivatives.py
/ fingerprint.py can be built and tested now, before better real data (from
further scraping) is in hand.

Because the response functions below are known in closed form, this file also
doubles as the Week 5 synthetic-validation fixture (Math spec §10): the exact
gradient and Hessian can be computed from the model directly (via very fine
finite differences on the noise-free function, which is numerically safe
since the function itself is smooth) and compared against whatever the real
fitting pipeline recovers from the noisy sampled data.

Usage:
    python generate_synthetic_dataset.py
Writes: synthetic_pilot_data.csv, matching the real Appendix A schema.
"""

import numpy as np
import pandas as pd

# =============================================================================
# Ground-truth response models, one per pilot system
# =============================================================================
# All models share the same functional form for consistency and easy
# comparison: a logistic (or inverted logistic) transition in pH, whose
# midpoint shifts with log10(ionic strength) -- a simple, chemically
# motivated stand-in for double-layer screening shifting the apparent
# sorption edge. This guarantees a real, nonzero pH x I interaction term
# (cross-Hessian), which is useful specifically because it gives the
# validation step something nontrivial to recover correctly, not just a
# flat or separable surface.
#
#   A(pH, I) = Amax * sigmoid( sign * (pH - pH50 - b*log10(I)) / w )
#
# where sign=+1 gives an increasing edge (more sorption at higher pH, the
# goethite/ferrihydrite pattern) and sign=-1 gives a decreasing edge (more
# sorption at low pH, the selenium(IV) pattern). Montmorillonite uses a
# shallow, wide, weakly I-dependent version of the same form (a "weak,
# diffuse" response, consistent with looser clay-surface binding).

SYSTEM_PARAMS = {
    "goethite|U(+6)":         dict(Amax=100, pH50=6.0, b=0.35, w=0.6, sign=+1, mineralsites=2.3, formula="FeOOH"),
    "goethite|Se(+4)":        dict(Amax=100, pH50=5.5, b=0.20, w=0.9, sign=-1, mineralsites=2.3, formula="FeOOH"),
    "montmorillonite|U(+6)":  dict(Amax=40,  pH50=6.5, b=0.05, w=2.5, sign=+1, mineralsites=0.9, formula="Al2Si4O10(OH)2"),
    "ferrihydrite|U(+6)":     dict(Amax=100, pH50=5.8, b=0.45, w=0.5, sign=+1, mineralsites=3.1, formula="Fe10O14(OH)2"),
}


def true_response(pH, I, Amax, pH50, b, w, sign, **_):
    """The exact, noise-free ground-truth response. I must be > 0."""
    shifted_pH50 = pH50 + b * np.log10(I)
    z = sign * (pH - shifted_pH50) / w
    return Amax / (1.0 + np.exp(-z))


def true_gradient_and_hessian(pH, I, params, h=1e-4):
    """
    Exact gradient/Hessian at a point, computed via very fine central
    differences directly on the closed-form (noise-free) function above.
    This is safe here specifically because the function is smooth and has
    no measurement noise -- the same justification used elsewhere in this
    project for differentiating a fitted surrogate rather than raw data.
    Used as the known 'right answer' when validating the real pipeline.
    """
    def f(p, i):
        return true_response(p, i, **params)

    dA_dpH = (f(pH + h, I) - f(pH - h, I)) / (2 * h)
    dA_dI = (f(pH, I + h) - f(pH, I - h)) / (2 * h)

    d2A_dpH2 = (f(pH + h, I) - 2 * f(pH, I) + f(pH - h, I)) / h**2
    d2A_dI2 = (f(pH, I + h) - 2 * f(pH, I) + f(pH, I - h)) / h**2
    d2A_dpHdI = (f(pH + h, I + h) - f(pH + h, I - h) - f(pH - h, I + h) + f(pH - h, I - h)) / (4 * h**2)

    gradient = np.array([dA_dpH, dA_dI])
    hessian = np.array([[d2A_dpH2, d2A_dpHdI], [d2A_dpHdI, d2A_dI2]])
    return gradient, hessian


# =============================================================================
# Dataset generation
# =============================================================================

def generate_system_data(mineral, sorbate, params, n_points, noise_frac, n_references, rng):
    """
    Generates n_points for one system, deliberately with GOOD joint (pH, I)
    coverage -- pH sampled broadly, ionic strength sampled log-uniformly
    across a wide, continuous range, split across a few synthetic
    'references' each of which DOES vary I internally (unlike the pooled
    real-data problem this is meant to stand in for).
    """
    pH = rng.uniform(2.5, 10.5, n_points)
    I = 10 ** rng.uniform(-3, 0.3, n_points)  # ~0.001 to ~2 M, continuous, log-uniform

    true_A = true_response(pH, I, **params)
    noise = rng.normal(0, noise_frac * params["Amax"], n_points)
    observed_A = np.clip(true_A + noise, 0, None)  # sorption can't be negative

    reference_ids = rng.integers(0, n_references, n_points)
    references = [f"synthetic_study_{i}" for i in reference_ids]

    # Group nearby points into small "Sets" (replicate blocks), matching the
    # real schema's replicate-detection design.
    n_sets = max(1, n_points // 4)
    set_ids = rng.integers(0, n_sets, n_points)

    return pd.DataFrame({
        "Reference": references,
        "Set": set_ids,
        "SetID": np.arange(n_points),
        "Mineral": mineral,
        "Mineral_formula": params["formula"],
        "Sorbate": sorbate,
        "Temp": rng.normal(25.0, 0.3, n_points),
        "pH": pH,
        "Electrolyte1": "Na(+1)",
        "Electrolyte1_val": I,      # z=+1, so this column alone gives ionic strength directly
        "Electrolyte2": "NO3(-1)",
        "Electrolyte2_val": I,      # paired counter-ion at matching concentration
        "Mineralsites": params["mineralsites"],
        "Sorbed_val": observed_A,
    })


def generate_full_dataset(n_per_system=600, noise_frac=0.04, n_references=4, seed=0):
    rng = np.random.default_rng(seed)
    blocks = []
    for key, params in SYSTEM_PARAMS.items():
        mineral, sorbate = key.split("|")
        blocks.append(generate_system_data(mineral, sorbate, params, n_per_system, noise_frac, n_references, rng))
    return pd.concat(blocks, ignore_index=True)


if __name__ == "__main__":
    df = generate_full_dataset()
    df.to_csv("synthetic_pilot_data.csv", index=False)
    print(f"Wrote synthetic_pilot_data.csv: {len(df):,} rows across {len(SYSTEM_PARAMS)} systems.")
    print(df.groupby(["Mineral", "Sorbate"]).size())

    # Quick sanity check: print exact ground-truth gradient/Hessian at one
    # representative point per system, for later comparison against the
    # real fitting pipeline's output.
    print("\nExample ground-truth gradient/Hessian at pH=6, I=0.1 (for validation later):")
    for key, params in SYSTEM_PARAMS.items():
        grad, hess = true_gradient_and_hessian(6.0, 0.1, params)
        print(f"  {key}: gradient={grad.round(3)}, Hessian diag={np.diag(hess).round(3)}, "
              f"cross-term={hess[0,1]:.4f}")
