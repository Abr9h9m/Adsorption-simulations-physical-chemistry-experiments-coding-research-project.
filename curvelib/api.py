"""api.py -- read-only JSON API over a curve dataset (WEB_INTERFACE_PROTOCOL.md phase P2).

    python -m curvelib.api                      # sorption pack, http://127.0.0.1:8000
    CURVELIB_MANIFEST=... CURVELIB_DATA=... python -m curvelib.api

Generic: everything is addressed through manifest roles. A pack may add optional hooks in
packs/<name>/pack.py: `entity_picker(curves, coverage)` (front-page picker; default = faceted list) and
`predict(params)` (model prediction). Fits use the shared `phslope` logistic fit, so web numbers equal the
analysis numbers. Every response carries the dataset status ("exploratory") and schema_version (R7).
Nothing is written back; no data leaves the server except the JSON it is asked for.
"""
import hashlib
import importlib
import os

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from curvelib import engine as E
from curvelib import manifest as M

HERE = os.path.dirname(os.path.abspath(__file__))
SEP = "||"
POOL_WARNING = ("Fit pools curves from several papers. In our analysis pooling across papers widened edges about "
                "1.4 times and mixes paper effects; the interval below resamples whole papers.")


class State:
    def __init__(self, manifest_path, data_path):
        self.manifest = M.load(manifest_path)
        df = pd.read_csv(data_path, low_memory=False)
        with open(data_path, "rb") as f:
            self.data_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        r = E.run(df, self.manifest)
        self.rows, self.accounting, self.curves, self.coverage = r["rows"], r["accounting"], r["curves"], r["coverage"]
        key = self.manifest["curve"]["key"]
        self.rows["_curve_id"] = self.rows[key].astype(str).agg(SEP.join, axis=1)
        self.curves["curve_id"] = self.curves[key].astype(str).agg(SEP.join, axis=1)
        self.pack = None
        if self.manifest.get("pack"):
            try:
                self.pack = importlib.import_module(f"packs.{self.manifest['pack']}.pack")
            except ImportError:
                self.pack = None

    def envelope(self, payload):
        d = self.manifest["dataset"]
        return {"dataset": d["id"], "status": d["status"], "schema_version": self.manifest["schema_version"],
                "data_version": self.data_hash, "data": payload}


def _records(df):
    return df.replace({np.nan: None}).to_dict("records")


def create_app(manifest_path=None, data_path=None):
    from phslope.common import resolve_data_file
    manifest_path = manifest_path or os.environ.get("CURVELIB_MANIFEST",
                                                    os.path.join(HERE, "..", "packs", "sorption", "manifest.yaml"))
    data_path = data_path or os.environ.get("CURVELIB_DATA") or resolve_data_file()
    st = State(manifest_path, data_path)
    app = FastAPI(title="curvelib", description="Read-only curve-library API (exploratory)")
    app.state.curvelib = st

    @app.get("/api/meta")
    def meta():
        m = st.manifest
        return st.envelope({"title": m["dataset"]["title"], "source": m["dataset"]["source"],
                            "rows": int(st.accounting["rows"].sum()),
                            "roles": {c["name"]: c["role"] for c in m["columns"]},
                            "response_modes": [r["id"] for r in m["response_modes"]],
                            "pair_coverage": m["pair_coverage"], "has_picker": hasattr(st.pack, "entity_picker"),
                            "has_predict": hasattr(st.pack, "predict")})

    @app.get("/api/accounting")
    def accounting():
        return st.envelope(_records(st.accounting))

    @app.get("/api/coverage")
    def coverage(min_points: int = None, min_clusters: int = None, min_x_span: float = None):
        t = E.coverage(st.curves, min_points, min_clusters, min_x_span, st.manifest)
        return st.envelope(_records(t))

    @app.get("/api/sweep")
    def sweep(points: str = "0,10,25,50,100", clusters: str = "1,2,3,4"):
        p = [int(x) for x in points.split(",")]
        k = [int(x) for x in clusters.split(",")]
        return st.envelope(_records(E.sweep(st.curves, p, k, st.manifest["pair_coverage"].get("min_x_span", 0.0))))

    @app.get("/api/entities")
    def entities():
        if hasattr(st.pack, "entity_picker"):
            return st.envelope(st.pack.entity_picker(st.curves, st.coverage))
        g = st.curves[st.curves["clean"]].groupby("group_b").agg(curves=("n_points", "size"), points=("n_points", "sum"),
                                                                 clusters=("cluster", "nunique")).reset_index()
        return st.envelope({"type": "list", "cells": _records(g.rename(columns={"group_b": "id"}))})

    @app.get("/api/curves")
    def curves(group_a: list[str] = Query(None), group_b: list[str] = Query(None), clean_only: bool = True):
        c = st.curves[st.curves["clean"]] if clean_only else st.curves
        if group_a:
            c = c[c["group_a"].isin(group_a)]
        if group_b:
            c = c[c["group_b"].isin(group_b)]
        cols = ["curve_id", "group_a", "group_b", "cluster", "n_points", "x_min", "x_max", "x_span", "clean"]
        return st.envelope(_records(c[cols]))

    @app.get("/api/points")
    def points(curve_id: list[str] = Query(...)):
        r = st.rows[st.rows["_curve_id"].isin(curve_id) & (st.rows["_status"] == "usable")]
        if r.empty:
            raise HTTPException(404, "no usable points for these curves")
        show = [c["name"] for c in st.manifest["columns"] if c["name"] in r.columns]
        out = r[["_curve_id", "_x", "_y"] + show].rename(columns={"_curve_id": "curve_id", "_x": "x", "_y": "y"})
        return st.envelope(_records(out))

    @app.get("/api/fit")
    def fit(curve_id: list[str] = Query(...), model: str = "logistic", seed: int = 0):
        """Server-side fit with the shared analysis code. One fit over all selected curves; when they come
        from more than one cluster (paper), parameter intervals resample whole clusters and a warning is set."""
        from phslope import fit_edge
        from phslope.common import load_config
        if model != "logistic":
            raise HTTPException(400, "available models: logistic")
        r = st.rows[st.rows["_curve_id"].isin(curve_id) & (st.rows["_status"] == "usable")]
        cl = M.column(st.manifest, "cluster")
        if r["_x"].nunique() < 4:
            raise HTTPException(400, "no fit is offered on fewer than 4 distinct points")
        cfg = load_config()["fit"]
        x, y, g = r["_x"].to_numpy(float), r["_y"].to_numpy(float), r[cl].astype(str).to_numpy()
        f = fit_edge.fit_logistic(x, y, cfg, seed=seed)
        res = y - fit_edge.predict(f, x)
        ss = float(((y - y.mean()) ** 2).sum())
        out = {"model": model, "n_points": int(len(x)), "n_clusters": int(len(set(g))), "n_curves": len(curve_id),
               "params": {k: float(f[k]) for k in ("lo", "hi", "p50", "w")}, "rmse": float(f["rmse"]),
               "r2_response_space": 1 - float(res @ res) / ss if ss > 0 else None,
               "fit_window": [float(x.min()), float(x.max())], "warning": None, "intervals": None}
        grid = np.linspace(x.min(), x.max(), 200)
        out["curve"] = {"x": grid.tolist(), "y": fit_edge.predict(f, grid).tolist()}
        units = sorted(set(g))
        if len(units) > 1:
            out["warning"] = POOL_WARNING
            rng = np.random.default_rng(seed)
            idx = {u: np.where(g == u)[0] for u in units}
            draws = []
            for _ in range(100):
                pick = np.concatenate([idx[u] for u in rng.choice(units, len(units))])
                try:
                    fb = fit_edge.fit_logistic(x[pick], y[pick], cfg, n_starts=3, seed=seed, x0=fit_edge.params_vector(f))
                    draws.append([fb[k] for k in ("lo", "hi", "p50", "w")])
                except fit_edge.EdgeFitError:
                    continue
            if draws:
                lo, hi = np.percentile(np.array(draws), [2.5, 97.5], axis=0)
                out["intervals"] = {k: [float(a), float(b)] for k, a, b in zip(("lo", "hi", "p50", "w"), lo, hi)}
                out["interval_method"] = "resampling whole clusters (papers), 100 draws"
        return st.envelope(out)

    @app.get("/api/predict")
    def predict(group_a: str, group_b: str, solids_g_L: float, total_sorbate_mol_L: float, ionic_strength: float,
                direction: str = None):
        if not hasattr(st.pack, "predict"):
            raise HTTPException(404, "this dataset's pack has no model")
        try:
            return st.envelope(st.pack.predict({"group_a": group_a, "group_b": group_b, "solids_g_L": solids_g_L,
                                                "total_sorbate_mol_L": total_sorbate_mol_L,
                                                "ionic_strength": ionic_strength, "direction": direction}))
        except ValueError as e:
            raise HTTPException(400, str(e))

    @app.get("/")
    def index():
        return FileResponse(os.path.join(HERE, "web", "index.html"))

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)
