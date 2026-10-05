"""compare.py -- Tier 1 (compressed-vector) and Tier 2 (shared-grid) comparisons."""

import numpy as np


def cosine_similarity(v1, v2):
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(np.dot(v1, v2) / denom) if denom > 0 else np.nan


def hessian_shape_similarity(hess1, hess2):
    """Cosine similarity between flattened [Hpp, Hii, Hpi] -- magnitude-independent shape comparison."""
    f1 = np.array([hess1[0, 0], hess1[1, 1], hess1[0, 1]])
    f2 = np.array([hess2[0, 0], hess2[1, 1], hess2[0, 1]])
    return cosine_similarity(f1, f2)


def eigenvector_orientation_angle(hess1, hess2):
    """
    Angle (degrees) between dominant eigenvectors. Uses |v1.v2| since an
    eigenvector and its negative represent the same direction (sign ambiguity).
    """
    _, v1 = np.linalg.eigh(hess1)
    _, v2 = np.linalg.eigh(hess2)
    dom1, dom2 = v1[:, -1], v2[:, -1]  # eigh sorts ascending; last = dominant
    cos_angle = np.clip(abs(np.dot(dom1, dom2)), -1, 1)
    return float(np.degrees(np.arccos(cos_angle)))


def vector_distance(phi1, phi2, feature_means=None, feature_stds=None):
    """Z-scored Euclidean distance between two compressed fingerprint vectors (Tier 1)."""
    if feature_means is not None:
        phi1 = (phi1 - feature_means) / feature_stds
        phi2 = (phi2 - feature_means) / feature_stds
    return float(np.linalg.norm(phi1 - phi2))


def compare_on_shared_grid(points1, results1, points2, results2, match_tolerance=0.5):
    """
    Tier 2: for points in system 1 with a close enough match in system 2
    (within match_tolerance in both pH and I), compute shape similarity and
    orientation angle. Returns a list of per-point comparison dicts.
    """
    comparisons = []
    for (pH1, I1), r1 in zip(points1, results1):
        best_match, best_dist = None, np.inf
        for j, (pH2, I2) in enumerate(points2):
            dist = abs(pH1 - pH2) + abs(I1 - I2) / max(I1, 1e-9)
            if dist < best_dist:
                best_dist, best_match = dist, j
        if best_match is not None and best_dist < match_tolerance:
            r2 = results2[best_match]
            comparisons.append({
                "pH": pH1, "I": I1,
                "shape_similarity": hessian_shape_similarity(r1["hessian"], r2["hessian"]),
                "orientation_angle_deg": eigenvector_orientation_angle(r1["hessian"], r2["hessian"]),
            })
    return comparisons


if __name__ == "__main__":
    import pandas as pd
    from scaling import fit_scaler
    from fingerprint import compute_field, fingerprint_vector

    df = pd.read_csv("synthetic_pilot_data.csv")
    systems = [("goethite", "U(+6)"), ("goethite", "Se(+4)"), ("montmorillonite", "U(+6)")]
    fields, vecs = {}, {}
    for mineral, sorbate in systems:
        sub = df[(df["Mineral"] == mineral) & (df["Sorbate"] == sorbate)]
        pH_all, I_all, y_all = sub["pH"].to_numpy(), sub["Electrolyte1_val"].to_numpy(), sub["Sorbed_val"].to_numpy()
        scaler = fit_scaler(pH_all, I_all)
        points, results = compute_field(pH_all, I_all, y_all, scaler, bandwidth=(0.1, 0.1), grid_n=10)
        fields[(mineral, sorbate)] = (points, results)
        vecs[(mineral, sorbate)], _ = fingerprint_vector(points, results)

    pairs = [(systems[0], systems[1], "same mineral, diff sorbate"),
             (systems[0], systems[2], "same sorbate, diff mineral")]
    print("Tier 1 (compressed vector) comparison:")
    for s1, s2, label in pairs:
        d = vector_distance(vecs[s1], vecs[s2])
        print(f"  {s1} vs {s2} ({label}): vector distance = {d:.3f}")

    print("\nTier 2 (shared-grid) comparison, mean over matched points:")
    for s1, s2, label in pairs:
        comps = compare_on_shared_grid(*fields[s1], *fields[s2])
        if comps:
            mean_sim = np.mean([c["shape_similarity"] for c in comps])
            mean_angle = np.mean([c["orientation_angle_deg"] for c in comps])
            print(f"  {s1} vs {s2} ({label}): n_matched={len(comps)}, "
                  f"mean shape similarity={mean_sim:.3f}, mean orientation angle={mean_angle:.1f} deg")
        else:
            print(f"  {s1} vs {s2}: no matched grid points within tolerance")
