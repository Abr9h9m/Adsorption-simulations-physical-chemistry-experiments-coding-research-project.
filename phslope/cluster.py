"""cluster.py -- do curves group by class without being told the classes? (spec 4.9)

Curves are clustered (Ward hierarchical clustering on standardized features:
FPCA scores, or separately the edge parameters edge_pH, log width, height),
cut into as many clusters as there are class labels, and compared with the
labels by the adjusted Rand index (ARI: 0 = chance agreement, 1 = identical).

Null distribution: class labels permuted WITHIN references (2,000 times by
default), so that curves from one paper sharing a cluster cannot pass for a
class effect. PERMANOVA (pseudo-F on the Euclidean distance matrix) is
reported for the same features, with the same within-reference permutations.
"""
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import adjusted_rand_score


def standardize(X):
    X = np.asarray(X, float)
    sd = X.std(axis=0)
    return (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1)


def ward_clusters(X, k):
    return fcluster(linkage(standardize(X), method="ward"), t=k, criterion="maxclust")


def _within_ref_perms(labels, refs, n_perm, rng):
    idx_by_ref = [np.where(refs == r)[0] for r in np.unique(refs)]
    shufflable = [ix for ix in idx_by_ref if len(np.unique(labels[ix])) > 1]
    for _ in range(n_perm):
        lab = labels.copy()
        for ix in shufflable:
            lab[ix] = lab[rng.permutation(ix)]
        yield lab


def ari_test(X, labels, refs, n_perm=2000, seed=0):
    labels = pd.factorize(pd.Series(labels).astype(str))[0]
    refs = pd.factorize(pd.Series(refs).astype(str))[0]
    k = len(np.unique(labels))
    cl = ward_clusters(X, k)
    obs = adjusted_rand_score(labels, cl)
    rng = np.random.default_rng(seed)
    null = np.array([adjusted_rand_score(lab, cl) for lab in _within_ref_perms(labels, refs, n_perm, rng)])
    return {"ari": float(obs), "p_value": float((1 + np.sum(null >= obs - 1e-12)) / (1 + n_perm)),
            "n_clusters": k, "null_mean": float(null.mean()), "n": len(labels)}


def pseudo_f(D2, labels):
    """PERMANOVA pseudo-F from a squared-distance matrix."""
    n = len(labels)
    groups = np.unique(labels)
    g = len(groups)
    ss_tot = D2[np.triu_indices(n, 1)].sum() / n
    ss_w = 0.0
    for lab in groups:
        ix = np.where(labels == lab)[0]
        if len(ix) > 1:
            sub = D2[np.ix_(ix, ix)]
            ss_w += sub[np.triu_indices(len(ix), 1)].sum() / len(ix)
    ss_b = ss_tot - ss_w
    return (ss_b / (g - 1)) / (ss_w / (n - g)) if g > 1 and n > g and ss_w > 0 else np.nan, ss_b / ss_tot


def permanova(X, labels, refs, n_perm=2000, seed=0):
    labels = pd.factorize(pd.Series(labels).astype(str))[0]
    refs = pd.factorize(pd.Series(refs).astype(str))[0]
    D2 = squareform(pdist(standardize(X))) ** 2
    F, r2 = pseudo_f(D2, labels)
    rng = np.random.default_rng(seed)
    null = np.array([pseudo_f(D2, lab)[0] for lab in _within_ref_perms(labels, refs, n_perm, rng)])
    return {"pseudo_F": float(F), "R2": float(r2), "p_value": float((1 + np.sum(null >= F - 1e-12)) / (1 + n_perm)),
            "n": len(labels)}
