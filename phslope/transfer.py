"""transfer.py -- predicting a held-out curve: baselines, Version A, Version B (spec 4.10, 4.11).

Every model predicts the edge warp of a curve (edge position b, log width, signed
height h) and a registered shape r(u); the slope curve is rebuilt as

    g(pH) = h / w * r((pH - b) / w)

so all models are scored on the same footing.

Shapes:
  class-cell reference  mean registered slope of training curves in the same
                        (mineral_class, sorbate_class) cell; fallback: same sorbate
                        class; fallback: all training curves (spec 4.10)
  Version B             FPCA mean + predicted scores (FPCA refitted on training
                        curves only, so the held-out shape never enters the basis)

Warp models:
  global_mean           training means
  sorbate_class_mean    means within the sorbate class (fallback global)
  mineral_class_mean    means within the mineral class (fallback global)
  edge_position_rule    edge = OLS on pzc_mid and first_hydrolysis_logK (training);
                        width/height = sorbate-class means. Needs the descriptor tables.
  version_a             ridge regression of each warp parameter on the features;
                        penalty chosen by leave-study-out CV inside the training set
  version_b             version_a warp + ridge-predicted FPCA scores

Prediction intervals: split-conformal style from leave-study-out residuals inside the
training set (the 90% quantile of |residual|), for the edge position and, pointwise
on the pH grid, for the slope.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

from phslope import fpca as fpca_mod

ALPHAS = np.logspace(-3, 3, 13)
TARGETS = ("edge_pH", "log_width", "height")


# ------------------------------------------------------------------ shapes

def nanmean_rows(R):
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return np.nanmean(R, axis=0)


def class_cell_shapes(train, R_train):
    shapes = {"__global__": nanmean_rows(R_train)}
    for key, idx in train.groupby(["mineral_class", "sorbate_class"]).indices.items():
        shapes[("cell",) + key] = nanmean_rows(R_train[idx])
    for key, idx in train.groupby("sorbate_class").indices.items():
        shapes[("sorbate", key)] = nanmean_rows(R_train[idx])
    return shapes


def lookup_shape(shapes, mineral_class, sorbate_class):
    for k in (("cell", mineral_class, sorbate_class), ("sorbate", sorbate_class), "__global__"):
        if k in shapes and np.isfinite(shapes[k]).any():
            return shapes[k]
    return shapes["__global__"]


def rebuild(b, log_w, h, shape, u, grid):
    w = np.exp(log_w)
    ref = np.nan_to_num(shape)
    return h / w * np.interp((grid - b) / w, u, ref, left=0.0, right=0.0)


# ------------------------------------------------------------------ warp models

def _group_mean(train, col, test, target):
    g = train.groupby(col)[target].mean()
    return test[col].map(g).fillna(train[target].mean()).to_numpy()


def _ridge_cv(X, y, groups, n_splits=5):
    """Ridge with alpha chosen by grouped CV; returns (fitted model, mu, sd, alpha, oof predictions)."""
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd = np.where(sd > 0, sd, 1)
    Z = (X - mu) / sd
    k = min(n_splits, len(np.unique(groups)))
    best = (np.inf, None, None)
    for a in ALPHAS:
        oof = np.full(len(y), np.nan)
        if k >= 2:
            for tr, te in GroupKFold(k).split(Z, y, groups):
                oof[te] = Ridge(alpha=a).fit(Z[tr], y[tr]).predict(Z[te])
        err = np.nanmean((oof - y) ** 2) if k >= 2 else 0.0
        if err < best[0]:
            best = (err, a, oof)
    model = Ridge(alpha=best[1]).fit(Z, y)
    return model, mu, sd, best[1], best[2]


class WarpModel:
    """Base: fit(train, X_train) then predict(test, X_test) -> DataFrame of TARGETS."""
    needs_features = False
    name = "base"

    def fit(self, train, X=None):
        self.train = train
        return self

    def oof(self, train, X=None):
        """Out-of-fold (leave-study-out) predictions on the training set, for conformal intervals."""
        refs = train["reference"].to_numpy()
        k = min(5, len(np.unique(refs)))
        out = pd.DataFrame(np.nan, index=train.index, columns=list(TARGETS))
        if k < 2:
            return out
        for tr, te in GroupKFold(k).split(train, groups=refs):
            m = type(self)(**getattr(self, "_kw", {})).fit(train.iloc[tr], None if X is None else X[tr])
            out.iloc[te] = m.predict(train.iloc[te], None if X is None else X[te]).to_numpy()
        return out


class GlobalMean(WarpModel):
    name = "global_mean"

    def predict(self, test, X=None):
        return pd.DataFrame({t: np.full(len(test), self.train[t].mean()) for t in TARGETS}, index=test.index)


class ClassMean(WarpModel):
    def __init__(self, col):
        self.col, self._kw = col, {"col": col}
        self.name = f"{col.replace('_class', '')}_class_mean"

    def predict(self, test, X=None):
        return pd.DataFrame({t: _group_mean(self.train, self.col, test, t) for t in TARGETS}, index=test.index)


class EdgePositionRule(WarpModel):
    name = "edge_position_rule"
    needs = ("pzc_mid", "first_hydrolysis_logK")

    def fit(self, train, X=None):
        self.train = train
        d = train.dropna(subset=list(self.needs))
        self.ok = len(d) >= 5
        if self.ok:
            A = np.column_stack([np.ones(len(d))] + [d[c] for c in self.needs])
            self.coef = np.linalg.lstsq(A, d["edge_pH"].to_numpy(), rcond=None)[0]
        return self

    def predict(self, test, X=None):
        out = pd.DataFrame({t: _group_mean(self.train, "sorbate_class", test, t) for t in TARGETS}, index=test.index)
        if self.ok and all(c in test for c in self.needs):
            A = np.column_stack([np.ones(len(test))] + [test[c] for c in self.needs])
            out["edge_pH"] = A @ self.coef
        else:
            out["edge_pH"] = np.nan
        return out


class VersionA(WarpModel):
    name = "version_a"
    needs_features = True

    def fit(self, train, X):
        self.train = train
        g = train["reference"].to_numpy()
        self.models = {t: _ridge_cv(X, train[t].to_numpy(), g) for t in TARGETS}
        return self

    def predict(self, test, X):
        return pd.DataFrame({t: m.predict((X - mu) / sd) for t, (m, mu, sd, _, _) in self.models.items()},
                            index=test.index)

    def alphas(self):
        return {t: v[3] for t, v in self.models.items()}


# ------------------------------------------------------------------ Version B shape

class ShapeScores:
    """FPCA on training registered curves; ridge from features to scores."""

    def __init__(self, fpca_cfg):
        self.cfg = fpca_cfg

    def fit(self, train, R_train, X):
        self.f = fpca_mod.fpca(R_train, self.cfg)
        S = self.f["scores"]
        ok = np.isfinite(S).all(axis=1)
        g = train["reference"].to_numpy()[ok]
        self.models = [_ridge_cv(X[ok], S[ok, j], g) for j in range(self.f["n_components"])]
        return self

    def predict_shapes(self, X, n_u):
        S = np.column_stack([m.predict((X - mu) / sd) for m, mu, sd, _, _ in self.models])
        out = np.full((len(X), n_u), np.nan)
        out[:, self.f["columns"]] = self.f["mean"] + S @ self.f["components"]
        return out
