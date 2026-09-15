"""
windowing.py -- OWNER: CS collaborator

Finds which nearby data points count for a given query point, and how much.
Split into a cheap geometric prefilter (find_candidate_neighbors) and the
real statistical weighting (kernel_weights), so each half can be tested
independently.
"""

import numpy as np
from scipy.spatial import cKDTree


def build_kdtree(pH_scaled: np.ndarray, I_scaled: np.ndarray) -> cKDTree:
    """Build once per system; reuse for every subsequent query point."""
    coords = np.column_stack([pH_scaled, I_scaled])
    return cKDTree(coords)


def find_candidate_neighbors(query_point_scaled, tree: cKDTree, bandwidth, radius_multiplier=4.0):
    """
    Cheap hard-radius cutoff at radius_multiplier * max(bandwidth) -- points
    farther than this contribute ~0 weight under the Gaussian kernel anyway.
    Returns an array of indices into the original (scaled) coordinate arrays.
    """
    radius = radius_multiplier * max(bandwidth)
    idx = tree.query_ball_point(query_point_scaled, r=radius)
    return np.array(idx)


def kernel_weights(query_point_scaled, neighbor_points_scaled: np.ndarray, bandwidth) -> np.ndarray:
    """
    Gaussian kernel weight for each candidate neighbor:
      w = exp( -dpH^2/(2*h_pH^2) - dI^2/(2*h_I^2) )
    """
    d_pH = neighbor_points_scaled[:, 0] - query_point_scaled[0]
    d_I = neighbor_points_scaled[:, 1] - query_point_scaled[1]
    h_pH, h_I = bandwidth
    return np.exp(-(d_pH**2) / (2 * h_pH**2) - (d_I**2) / (2 * h_I**2))


if __name__ == "__main__":
    # Quick manual check
    rng = np.random.default_rng(0)
    pH_scaled = rng.uniform(0, 1, 200)
    I_scaled = rng.uniform(0, 1, 200)
    tree = build_kdtree(pH_scaled, I_scaled)

    query = (0.5, 0.5)
    bandwidth = (0.05, 0.05)

    idx = find_candidate_neighbors(query, tree, bandwidth, radius_multiplier=4.0)
    print(f"Found {len(idx)} candidate neighbors within 4x bandwidth of {query}")

    neighbor_coords = np.column_stack([pH_scaled[idx], I_scaled[idx]])
    weights = kernel_weights(query, neighbor_coords, bandwidth)
    print(f"Weight range: {weights.min():.4f} to {weights.max():.4f}")
    print("Expect the closest point's weight to be near 1.0:", weights.max())
