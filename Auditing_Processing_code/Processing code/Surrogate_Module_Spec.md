# surrogate.py, Broken Into Modules: Function Specs and Ownership

This week's actual coding target, broken into five small files instead of one big one — each with exact function signatures, what they return, and who's building what. Building it this way means you can each work on a real piece independently, then join them at `derivatives.py`.

**The pipeline, in order:** `scaling.py` → `windowing.py` (find the neighborhood) → `local_fit.py` (fit the quadratic within it) → `derivatives.py` (read off gradient/Hessian, orchestrate everything, check validity).

---

## 1. `scaling.py` — **you build this**

Simple, and it's the thing that makes everything downstream numerically sane (pH ranges 0–14, ionic strength ranges 0.001–2, and fitting on raw units breaks the math — see Mathematical Formulation §13).

```python
def fit_scaler(pH_all: np.ndarray, I_all: np.ndarray) -> dict:
    """
    Computes min/max for each dimension from the full dataset (once per
    system). Returns {"pH_min", "pH_max", "I_min", "I_max"}.
    """

def to_scaled(pH: np.ndarray, I: np.ndarray, scaler: dict) -> tuple[np.ndarray, np.ndarray]:
    """
    Min-max scales both arrays to [0, 1] using the fitted scaler.
    pH_scaled = (pH - scaler["pH_min"]) / (scaler["pH_max"] - scaler["pH_min"])
    """

def gradient_to_real_units(grad_scaled: np.ndarray, scaler: dict) -> np.ndarray:
    """
    Converts a gradient computed in scaled coordinates back to real
    pH/ionic-strength units via the chain rule:
      dA/dpH = (dA/dpH_scaled) / (pH_max - pH_min)
    """

def hessian_to_real_units(hess_scaled: np.ndarray, scaler: dict) -> np.ndarray:
    """
    Same idea, applied twice for the diagonal terms and once each for the
    cross term:
      d2A/dpH2 = (d2A/dpH_scaled2) / (pH_max - pH_min)**2
      d2A/dpH_dI = (d2A/dpH_scaled_dI_scaled) / ((pH_max-pH_min)*(I_max-I_min))
    """
```

**Test it against:** pick any two points from `synthetic_pilot_data.csv`, scale them, unscale a made-up gradient/Hessian, confirm you get back what you'd expect by hand-checking the arithmetic on one example.

---

## 2. `windowing.py` — **CS collaborator, this is the "find the window" piece**

This is the performance-critical part — for every query point, we need "which nearby data points count, and how much" without scanning the whole dataset each time.

```python
def build_kdtree(pH_scaled: np.ndarray, I_scaled: np.ndarray) -> scipy.spatial.cKDTree:
    """
    Build once per system (not once per query point) -- reused for every
    subsequent lookup. Takes the SCALED coordinates (post scaling.py).
    """

def find_candidate_neighbors(query_point_scaled: tuple[float, float],
                              tree: scipy.spatial.cKDTree,
                              bandwidth: tuple[float, float],
                              radius_multiplier: float = 4.0) -> np.ndarray:
    """
    This is literally your 'window threshold' idea: a cheap hard cutoff at
    radius_multiplier * max(bandwidth) around the query point, using the
    KD-tree, to get a short candidate list FAST -- before doing any real
    weighting. Points farther than ~4 bandwidths away get essentially zero
    weight under the Gaussian kernel anyway (see kernel_weights below), so
    excluding them up front is a legitimate approximation, not a hack.
    Returns an array of INDICES into the original data.
    """

def kernel_weights(query_point_scaled: tuple[float, float],
                    neighbor_points_scaled: np.ndarray,
                    bandwidth: tuple[float, float]) -> np.ndarray:
    """
    The actual statistical weight, computed ONLY for the candidates returned
    above (not the whole dataset):
      w = exp( -dpH^2/(2*h_pH^2) - dI^2/(2*h_I^2) )
    Returns one weight per candidate neighbor, same length as the input.
    """
```

**Why two separate functions instead of one:** `find_candidate_neighbors` is a cheap geometric filter (fast, approximate); `kernel_weights` is the real math (exact, but only run on the small filtered set). Splitting them means you can unit-test the geometry and the weighting independently.

**Test it against:** on the synthetic dataset, pick a query point, confirm `find_candidate_neighbors` returns more points as `radius_multiplier` increases, and confirm `kernel_weights` gives weight ≈1 for the query point's exact location and weight → 0 for points near the edge of the candidate radius.

---

## 3. `local_fit.py` — **split: design matrix (you), solver (CS collaborator)**

```python
def design_matrix(delta_pH: np.ndarray, delta_I: np.ndarray) -> np.ndarray:
    """
    [YOU BUILD THIS]
    Returns an N x 6 matrix with columns, in this exact order:
      [1, delta_pH, delta_I, 0.5*delta_pH**2, 0.5*delta_I**2, delta_pH*delta_I]

    IMPORTANT: the 0.5 factor on the squared terms is deliberate (Math spec
    section 2) -- it's what makes the fitted coefficients equal the Hessian
    entries directly later, with no factor-of-2 correction needed. Do not
    "simplify" this by dropping the 0.5.
    """

def fit_weighted_quadratic(Phi: np.ndarray, y: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """
    [CS COLLABORATOR BUILDS THIS]
    Weighted least squares. Recommended approach for numerical stability:
    scale each row of Phi and each entry of y by sqrt(weight), then solve
    with ordinary least squares (np.linalg.lstsq) rather than forming the
    normal equations (Phi.T @ W @ Phi) directly -- lstsq is better
    conditioned and handles near-singular cases more gracefully.

    Returns theta = [a0, b_pH, b_I, C_pH_pH, C_I_I, C_pH_I]
    """
```

**Test it against:** generate points from a KNOWN simple quadratic (e.g., `z = 2 + 3*x - 1*y + 0.5*x**2 - 0.3*y**2 + 0.2*x*y`, no noise), fit it, confirm the recovered `theta` matches the coefficients you put in, to several decimal places. This is a smaller, faster version of the real synthetic-validation gate — good for catching bugs in `design_matrix` or `fit_weighted_quadratic` individually before blaming the whole pipeline.

---

## 4. `derivatives.py` — **you own the orchestration; joint build for the cross-check**

This is where the pieces above get called together, and where the validity/trust judgment calls live — which is why it's yours to own even though you're not writing the heaviest math here.

```python
def gradient_and_hessian_at_point(query_point: tuple[float, float],
                                   pH_all: np.ndarray, I_all: np.ndarray, y_all: np.ndarray,
                                   tree: scipy.spatial.cKDTree, scaler: dict,
                                   bandwidth: tuple[float, float],
                                   min_n_eff: float = 18.0) -> dict:
    """
    [YOU BUILD THIS -- the orchestration]
    1. Scale query_point using scaler (scaling.py)
    2. Find candidate neighbors (windowing.py)
    3. Compute kernel weights for those neighbors (windowing.py)
    4. Compute n_eff = sum(weights). If n_eff < min_n_eff, return
       {"valid": False, ...} rather than a shaky estimate -- this is the
       validity/support check from Math spec section 11, and it's the
       direct fix for the "sparse-data spike" problem from last semester.
    5. Build the design matrix on (delta_pH_scaled, delta_I_scaled) for the
       candidates (local_fit.py)
    6. Fit the weighted quadratic (local_fit.py)
    7. Extract gradient = theta[1:3], hessian = [[theta[3], theta[5]],
       [theta[5], theta[4]]] (still in scaled units)
    8. Convert both back to real units (scaling.py)
    9. Return {"gradient": ..., "hessian": ..., "n_eff": ..., "valid": True}
    """

def finite_difference_cross_check(fit_function, query_point: tuple[float, float],
                                   step: float = 1e-4) -> tuple[np.ndarray, np.ndarray]:
    """
    [BUILD TOGETHER -- good pairing task]
    An INDEPENDENT second way to get the gradient/Hessian at the same point,
    by taking central differences of the fitted surrogate itself (safe here
    because the surrogate is smooth, unlike raw noisy data). Must agree with
    step 7 above within a small tolerance before either is trusted -- if it
    doesn't, something in local_fit.py or windowing.py has a bug.
    """
```

**Test it against:** run `gradient_and_hessian_at_point` on several query points in `synthetic_pilot_data.csv`, compare against `true_gradient_and_hessian()` (already in `generate_synthetic_dataset.py`) — this is the actual Week 5 validation gate, not just a unit test.

---

## 5. `bandwidth_selection.py` — **CS collaborator, once 1–4 above are working**

Don't start this until the modules above are individually tested — bandwidth selection needs a working fit function to call repeatedly.

```python
def loocv_error(pH_all: np.ndarray, I_all: np.ndarray, y_all: np.ndarray,
                 bandwidth: tuple[float, float]) -> float:
    """
    Start with the brute-force version: for each point, refit excluding it
    (reusing gradient_and_hessian_at_point machinery), predict it, accumulate
    squared error. This is O(n) refits -- slow but simple and definitely
    correct. Get this working FIRST.

    Optimize later (not this week): local regression is a linear smoother,
    so there's a hat-matrix shortcut that avoids literally refitting n times
    -- worth implementing once the brute-force version is verified correct,
    not before.
    """

def select_bandwidth(pH_all, I_all, y_all, candidate_bandwidths: list) -> tuple:
    """Try each candidate, return the one with lowest loocv_error."""
```

---

## Suggested order for this week

1. **You:** `scaling.py` (quick, standalone)
2. **CS collaborator:** `windowing.py` (the main event for him this week)
3. **Both, in parallel:** `local_fit.py` — you take `design_matrix`, he takes `fit_weighted_quadratic`; these don't depend on each other so you can build simultaneously
4. **You, once 1–3 exist:** `gradient_and_hessian_at_point` in `derivatives.py` — this is where you'll actually see whether the pieces fit together correctly
5. **Together:** `finite_difference_cross_check` — good one to pair-program, since it's the moment you confirm the whole thing agrees with itself
6. **CS collaborator, if time remains:** start `bandwidth_selection.py`'s brute-force version; otherwise it rolls into next week

Test everything against `synthetic_pilot_data.csv` and `true_gradient_and_hessian()` — that's the whole reason that dataset exists right now.
