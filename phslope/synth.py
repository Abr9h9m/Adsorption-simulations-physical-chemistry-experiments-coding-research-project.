"""synth.py -- synthetic curves with known truth (spec section 6).

Every stage is tested here before it touches real data.

Truth is stored as a dict {"shape": ..., "params": {...}} so the exact response
and slope can be evaluated anywhere with `truth_response` / `truth_slope`.

Shapes (all in fraction-sorbed units):
  rising / falling : 4-parameter logistic, lo + (hi - lo) * s((p - p50) / w)
  bell             : lo + h * s((p - p50) / w) * (1 - s((p - p50b) / w2))
  two_step         : lo + h1 * s((p - p50) / w) + h2 * s((p - p50b) / w)
  flat             : constant c

Generators:
  known_edge_set            item 1: recovery of p50 / slope, uneven sampling
  planted_class_structure   items 2, 3 and 6: edge position = class effects +
                            study offset + noise; set the effect SDs to zero
                            for the null control, or make study_sd large for
                            the study-effect swamp.
"""
import numpy as np
import pandas as pd


def _sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def logistic(p, lo, hi, p50, w):
    return lo + (hi - lo) * _sig((np.asarray(p, float) - p50) / w)


def logistic_slope(p, lo, hi, p50, w):
    s = _sig((np.asarray(p, float) - p50) / w)
    return (hi - lo) * s * (1 - s) / w


def truth_response(truth, p):
    k, q = truth["shape"], truth["params"]
    p = np.asarray(p, float)
    if k in ("rising", "falling"):
        return logistic(p, q["lo"], q["hi"], q["p50"], q["w"])
    if k == "bell":
        return q["lo"] + q["h"] * _sig((p - q["p50"]) / q["w"]) * (1 - _sig((p - q["p50b"]) / q["w2"]))
    if k == "two_step":
        return q["lo"] + q["h1"] * _sig((p - q["p50"]) / q["w"]) + q["h2"] * _sig((p - q["p50b"]) / q["w"])
    if k == "flat":
        return np.full_like(p, q["c"])
    raise ValueError(k)


def truth_slope(truth, p):
    k, q = truth["shape"], truth["params"]
    p = np.asarray(p, float)
    if k in ("rising", "falling"):
        return logistic_slope(p, q["lo"], q["hi"], q["p50"], q["w"])
    if k == "bell":
        a, b = _sig((p - q["p50"]) / q["w"]), _sig((p - q["p50b"]) / q["w2"])
        da, db = a * (1 - a) / q["w"], b * (1 - b) / q["w2"]
        return q["h"] * (da * (1 - b) - a * db)
    if k == "two_step":
        return (logistic_slope(p, 0, q["h1"], q["p50"], q["w"])
                + logistic_slope(p, 0, q["h2"], q["p50b"], q["w"]))
    if k == "flat":
        return np.zeros_like(p)
    raise ValueError(k)


def truth_edge(truth):
    """Main edge position: p50 for logistic shapes, the first edge for bell / two_step."""
    return truth["params"].get("p50", np.nan)


def random_truth(shape, rng):
    if shape == "rising":
        return {"shape": shape, "params": dict(lo=rng.uniform(0, .1), hi=rng.uniform(.85, 1),
                                               p50=rng.uniform(4, 8), w=rng.uniform(.2, .8))}
    if shape == "falling":
        return {"shape": shape, "params": dict(lo=rng.uniform(.85, 1), hi=rng.uniform(0, .1),
                                               p50=rng.uniform(4, 8), w=rng.uniform(.2, .8))}
    if shape == "bell":
        p50 = rng.uniform(3.5, 5.5)
        return {"shape": shape, "params": dict(lo=rng.uniform(0, .05), h=rng.uniform(.8, .95), p50=p50,
                                               w=rng.uniform(.2, .5), p50b=p50 + rng.uniform(3, 4),
                                               w2=rng.uniform(.2, .5))}
    if shape == "two_step":
        p50 = rng.uniform(3.5, 5)
        h1 = rng.uniform(.35, .5)
        return {"shape": shape, "params": dict(lo=rng.uniform(0, .05), h1=h1, h2=rng.uniform(.35, .9 - h1),
                                               p50=p50, p50b=p50 + rng.uniform(2.5, 3.5),
                                               w=rng.uniform(.15, .35))}
    if shape == "flat":
        return {"shape": shape, "params": dict(c=rng.uniform(.1, .9))}
    raise ValueError(shape)


def sample_curve(truth, rng, n_points, noise_sd, ph_range=None, uneven=True):
    """Draws pH positions (uneven = random uniform, else evenly spaced) and noisy responses."""
    if ph_range is None:
        q = truth["params"]
        centre = q.get("p50", 6.5)
        far = q.get("p50b", centre)
        ph_range = (max(2.0, centre - rng.uniform(2, 3)), min(11.0, far + rng.uniform(2, 3)))
    lo, hi = ph_range
    pH = np.sort(rng.uniform(lo, hi, n_points)) if uneven else np.linspace(lo, hi, n_points)
    y = truth_response(truth, pH) + rng.normal(0, noise_sd, n_points)
    return pH, y


def known_edge_set(n_per_shape=20, shapes=("rising", "falling", "bell", "two_step", "flat"),
                   n_points=(10, 25), noise_sd=0.03, seed=0):
    """Item 1. Returns (curves, obs, truths): curves has curve_id, shape and
    true edge position; obs has curve_id, pH, response; truths maps curve_id -> truth."""
    rng = np.random.default_rng(seed)
    rows, obs, truths = [], [], {}
    for shape in shapes:
        for i in range(n_per_shape):
            cid = f"syn_{shape}_{i:03d}"
            truth = random_truth(shape, rng)
            n = int(rng.integers(n_points[0], n_points[1] + 1))
            pH, y = sample_curve(truth, rng, n, noise_sd)
            truths[cid] = truth
            rows.append({"curve_id": cid, "shape": shape, "true_edge": truth_edge(truth), "n_points": n,
                         "pH_min": pH.min(), "pH_max": pH.max(), "reference": f"ref_{cid}",
                         "mineral": "synthite", "sorbate": f"S_{shape}"})
            obs.append(pd.DataFrame({"curve_id": cid, "pH": pH, "response": y}))
    return pd.DataFrame(rows), pd.concat(obs, ignore_index=True), truths


def planted_class_structure(n_mineral_classes=4, n_sorbate_classes=4, minerals_per_class=3,
                            sorbates_per_class=3, n_references=40, pairs_per_reference=(1, 3),
                            curves_per_pair=(2, 4), base_p50=6.0, mineral_sd=0.8, sorbate_sd=0.8,
                            interaction_sd=0.3, study_sd=0.3, residual_sd=0.2, seed=0):
    """Items 2, 3 and 6. Edge position for each curve:
        p50 = base + mineral_class_effect + sorbate_class_effect + interaction + study_offset + residual
    Width and height vary at random (not structured). Returns (curves, planted):
    curves has one row per curve with class labels, reference, true p50; planted
    holds the population SDs, the realized effects, and the population variance shares.
    Null control: mineral_sd = sorbate_sd = interaction_sd = 0.
    Study-effect swamp: study_sd much larger than the class SDs."""
    rng = np.random.default_rng(seed)
    m_eff = rng.normal(0, mineral_sd, n_mineral_classes)
    s_eff = rng.normal(0, sorbate_sd, n_sorbate_classes)
    ms_eff = rng.normal(0, interaction_sd, (n_mineral_classes, n_sorbate_classes))
    r_eff = rng.normal(0, study_sd, n_references)
    minerals = [(f"min{c}_{j}", c) for c in range(n_mineral_classes) for j in range(minerals_per_class)]
    sorbates = [(f"sorb{c}_{j}", c) for c in range(n_sorbate_classes) for j in range(sorbates_per_class)]

    rows = []
    for r in range(n_references):
        n_pairs = int(rng.integers(pairs_per_reference[0], pairs_per_reference[1] + 1))
        for _ in range(n_pairs):
            mineral, mc = minerals[rng.integers(len(minerals))]
            sorbate, sc = sorbates[rng.integers(len(sorbates))]
            for k in range(int(rng.integers(curves_per_pair[0], curves_per_pair[1] + 1))):
                p50 = base_p50 + m_eff[mc] + s_eff[sc] + ms_eff[mc, sc] + r_eff[r] + rng.normal(0, residual_sd)
                rows.append({"curve_id": f"ref{r:03d}_{mineral}_{sorbate}_{k}", "reference": f"ref{r:03d}",
                             "mineral": mineral, "sorbate": sorbate,
                             "mineral_class": f"M{mc}", "sorbate_class": f"S{sc}",
                             "p50": p50, "log_w": np.log(rng.uniform(.25, .8)), "height": rng.uniform(.7, 1)})
    curves = pd.DataFrame(rows)
    var = {"mineral_class": mineral_sd ** 2, "sorbate_class": sorbate_sd ** 2,
           "interaction": interaction_sd ** 2, "reference": study_sd ** 2, "residual": residual_sd ** 2}
    total = sum(var.values())
    planted = {"sd": {k: v ** 0.5 for k, v in var.items()},
               "share": {k: v / total for k, v in var.items()},
               "effects": {"mineral_class": m_eff, "sorbate_class": s_eff, "interaction": ms_eff,
                           "reference": r_eff}}
    return curves, planted


def observations_for(curves, rng, n_points=(10, 20), noise_sd=0.03):
    """Noisy rising-edge observations for a planted curve table (columns p50, log_w, height)."""
    obs = []
    for row in curves.itertuples():
        truth = {"shape": "rising", "params": dict(lo=0.02, hi=0.02 + row.height, p50=row.p50, w=np.exp(row.log_w))}
        pH, y = sample_curve(truth, rng, int(rng.integers(n_points[0], n_points[1] + 1)), noise_sd)
        obs.append(pd.DataFrame({"curve_id": row.curve_id, "pH": pH, "response": y}))
    return pd.concat(obs, ignore_index=True)
