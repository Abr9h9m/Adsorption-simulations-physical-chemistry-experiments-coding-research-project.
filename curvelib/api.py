"""api.py -- JSON API and in-memory CSV upload flow over a curve dataset.

    python -m curvelib.api                      # blank workspace, http://127.0.0.1:8000

Generic: everything is addressed through manifest roles. A pack may add optional hooks in
packs/<name>/pack.py: `entity_picker(curves, coverage)` (front-page picker; default = faceted list) and
`predict(params)` (model prediction). Fits use the shared `phslope` logistic fit, so web numbers equal the
analysis numbers. Every response carries the dataset status ("exploratory") and schema_version (R7).
Nothing is written back; no data leaves the server except the JSON it is asked for.
"""
import hashlib
import importlib
import io
import os
import secrets
import threading
import time
from collections import OrderedDict

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse

from curvelib import engine as E
from curvelib import manifest as M

HERE = os.path.dirname(os.path.abspath(__file__))
SEP = "||"
MAX_UPLOAD_MB = max(1, int(os.environ.get("CURVELIB_MAX_UPLOAD_MB", "50")))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
UPLOAD_EXTENSIONS = {".csv", ".txt", ".tsv", ".xlsx", ".xlsm", ".xls"}
POOL_WARNING = ("Fit pools curves from several papers. In our analysis pooling across papers widened edges about "
                "1.4 times and mixes paper effects; the interval below resamples whole papers.")
SESSION_TTL_SECONDS = max(60, int(os.environ.get("CURVELIB_SESSION_TTL_SECONDS", "7200")))
MAX_ACTIVE_SESSIONS = max(1, int(os.environ.get("CURVELIB_MAX_ACTIVE_SESSIONS", "4")))


class SessionStates:
    """Small in-process registry for temporary per-browser datasets."""
    def __init__(self):
        self._states = OrderedDict()
        self._lock = threading.RLock()

    def _expire(self, now):
        expired = [sid for sid, (updated, _) in self._states.items()
                   if now - updated > SESSION_TTL_SECONDS]
        for sid in expired:
            self._states.pop(sid, None)

    def get(self, session_id):
        now = time.monotonic()
        with self._lock:
            self._expire(now)
            item = self._states.get(session_id)
            if item is None:
                return None
            self._states[session_id] = (now, item[1])
            self._states.move_to_end(session_id)
            return item[1]

    def set(self, session_id, state):
        now = time.monotonic()
        with self._lock:
            self._expire(now)
            self._states[session_id] = (now, state)
            self._states.move_to_end(session_id)
            while len(self._states) > MAX_ACTIVE_SESSIONS:
                self._states.popitem(last=False)


class State:
    def __init__(self, manifest_path, data_path):
        self.manifest = M.load(manifest_path)
        df = pd.read_csv(data_path, low_memory=False)
        with open(data_path, "rb") as f:
            self.data_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        r = E.run(df, self.manifest)
        self.rows, self.accounting, self.curves, self.coverage = r["rows"], r["accounting"], r["curves"], r["coverage"]
        key = self.manifest["curve"]["key"]
        self.rows["_curve_id"] = self.rows[key].astype(str).apply(lambda row: SEP.join(row.to_list()), axis=1)
        self.curves["curve_id"] = self.curves[key].astype(str).apply(lambda row: SEP.join(row.to_list()), axis=1)
        self.pack = None
        if self.manifest.get("pack"):
            try:
                self.pack = importlib.import_module(f"packs.{self.manifest['pack']}.pack")
            except ImportError:
                self.pack = None

    @classmethod
    def from_frame(cls, df, manifest, raw_bytes):
        """Create an in-memory state for a user-uploaded table."""
        obj = cls.__new__(cls)
        obj.manifest = manifest
        obj.data_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
        r = E.run(df, manifest)
        obj.rows, obj.accounting, obj.curves, obj.coverage = r["rows"], r["accounting"], r["curves"], r["coverage"]
        key = manifest["curve"]["key"]
        obj.rows["_curve_id"] = obj.rows[key].astype(str).apply(lambda row: SEP.join(row.to_list()), axis=1)
        obj.curves["curve_id"] = obj.curves[key].astype(str).apply(lambda row: SEP.join(row.to_list()), axis=1)
        obj.pack = None
        return obj

    def envelope(self, payload):
        d = self.manifest["dataset"]
        return {"dataset": d["id"], "status": d["status"], "schema_version": self.manifest["schema_version"],
                "data_version": self.data_hash, "data": payload}


def _records(df):
    # Normalize nullable values across numeric, object and pandas extension columns
    # before JSON encoding. Keeping every source column in /api/points means some
    # datasets include pd.NA/NaT values that the old numeric-only response avoided.
    clean = df.astype(object).where(pd.notna(df), None)
    return clean.to_dict("records")


def _read_upload(raw, filename, sample=False):
    """Read supported delimited-text and Excel uploads; Excel uses its first worksheet."""
    ext = os.path.splitext(filename.lower())[1]
    if ext not in UPLOAD_EXTENSIONS:
        raise ValueError("Choose a CSV, TXT, TSV, XLSX, XLSM, or XLS file.")
    buffer = io.BytesIO(raw)
    if ext in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(buffer, sheet_name=0, nrows=8 if sample else None)
    if ext == ".csv":
        return pd.read_csv(buffer, nrows=8 if sample else None, **({} if sample else {"low_memory": False}))
    # Text and TSV files can be tab- or delimiter-separated. Let pandas sniff the separator.
    return pd.read_csv(buffer, sep=None, engine="python", nrows=8 if sample else None)


async def _read_limited_body(request):
    """Read a request body incrementally so an oversized upload is rejected early."""
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"File is larger than the {MAX_UPLOAD_MB} MB upload limit.")
        chunks.append(chunk)
    return b"".join(chunks)


def create_app(manifest_path=None, data_path=None):
    # Start empty by default. Explicit paths remain available for tests and local callers.
    app = FastAPI(title="curvelib", description="Read-only curve-library API (exploratory)")
    app.state.curvelib_sessions = SessionStates()

    @app.middleware("http")
    async def identify_browser_session(request: Request, call_next):
        session_id = request.cookies.get("curvelib_session")
        new_session = not session_id or len(session_id) > 100
        if new_session:
            session_id = secrets.token_urlsafe(32)
        request.state.curvelib_session_id = session_id
        response = await call_next(request)
        response.set_cookie("curvelib_session", session_id, httponly=True, samesite="lax",
                            secure=request.url.scheme == "https", max_age=SESSION_TTL_SECONDS)
        return response

    if data_path:
        manifest_path = manifest_path or os.path.join(HERE, "..", "packs", "sorption", "manifest.yaml")
        initial_state = State(manifest_path, data_path)
        # Explicitly preloaded state is stored only in the initiating test/client session.
        app.state.initial_state = initial_state
    else:
        app.state.initial_state = None

    def current_state(request):
        state = app.state.curvelib_sessions.get(request.state.curvelib_session_id)
        if state is None and app.state.initial_state is not None:
            state = app.state.initial_state
            app.state.curvelib_sessions.set(request.state.curvelib_session_id, state)
        return state

    def require_state(request):
        state = current_state(request)
        if state is None:
            raise HTTPException(409, "No dataset is loaded. Upload a CSV dataset first.")
        return state

    @app.get("/api/meta")
    def meta(request: Request):
        st = current_state(request)
        if st is None:
            return {"dataset": None, "status": "empty", "schema_version": 1, "data_version": None,
                    "data": {"loaded": False, "upload_enabled": True, "upload_limit_mb": MAX_UPLOAD_MB}}
        m = st.manifest
        return st.envelope({"title": m["dataset"]["title"], "source": m["dataset"]["source"],
                            "loaded": True,
                            "rows": int(st.accounting["rows"].sum()),
                            "roles": {c["name"]: c["role"] for c in m["columns"]},
                            "response_modes": [r["id"] for r in m["response_modes"]],
                            "pair_coverage": m["pair_coverage"], "has_picker": hasattr(st.pack, "entity_picker"),
                            "has_predict": hasattr(st.pack, "predict"), "upload_enabled": True,
                            "upload_limit_mb": MAX_UPLOAD_MB})

    @app.post("/api/upload/inspect")
    async def inspect_upload(request: Request, filename: str = ""):
        raw = await _read_limited_body(request)
        try:
            frame = _read_upload(raw, filename or "upload.csv", sample=True)
        except Exception as e:
            raise HTTPException(400, f"Could not read the file: {e}")
        if len(frame.columns) < 2:
            raise HTTPException(400, "The first table needs at least two columns (one x column and one measured value).")
        return {"columns": [str(c) for c in frame.columns], "bytes": len(raw), "format": os.path.splitext(filename.lower())[1]}

    @app.post("/api/upload")
    async def upload(request: Request, name: str, group_a: str, group_b: str, cluster: str,
                     x: str, y: str, series: str = "", ionic_strength: str = "", filename: str = ""):
        raw = await _read_limited_body(request)
        try:
            frame = _read_upload(raw, filename or "upload.csv")
        except Exception as e:
            raise HTTPException(400, f"Could not read the file: {e}")
        mapped = [c for c in (group_a, group_b, cluster, x, y, series, ionic_strength) if c and c != "__all__"]
        if len(set(mapped)) != len(mapped):
            raise HTTPException(400, "Choose a different column for each mapped field.")
        missing = [c for c in mapped if c not in frame.columns]
        if missing:
            raise HTTPException(400, f"Mapped columns not found: {', '.join(missing)}")
        if x == y:
            raise HTTPException(400, "Choose different columns for x measurement and measured value.")
        frame = frame.copy()
        def fill_group(value, role, fallback):
            if value != "__all__":
                return value
            col = f"__upload_{role}"
            while col in frame.columns:
                col += "_"
            frame[col] = name[:100] or fallback
            return col
        group_a = fill_group(group_a, "group_a", "All data")
        group_b = fill_group(group_b, "group_b", "All data")
        cluster = fill_group(cluster, "source", "Uploaded file")
        curve_key = [cluster, group_a, group_b] + ([series] if series else [])
        manifest = {"schema_version": 1, "dataset": {"id": "uploaded_dataset", "title": name[:100] or "Uploaded dataset",
                    "source": "CSV uploaded to this running app session", "status": "exploratory"},
                    "columns": [{"name": str(c), "role": role} for c, role in
                                [(group_a,"group_a"),(group_b,"group_b"),(cluster,"cluster"),(x,"sweep_x"),(y,"value")]] +
                               ([{"name": ionic_strength, "role": "ionic_strength"}] if ionic_strength else []) +
                               ([{"name": series, "role": "series"}] if series else []),
                    "response_modes": [{"id": "uploaded_value", "column": y}],
                    "curve": {"key": curve_key, "x": x, "x_valid_range": [-1e308, 1e308],
                              "min_x_levels": 2, "x_round": 6, "min_x_span": 0},
                    "pair_coverage": {"min_points": 1, "min_clusters": 1, "min_x_span": 0}}
        try:
            M.validate(manifest)
            new_state = State.from_frame(frame, manifest, raw)
        except Exception as e:
            raise HTTPException(400, f"Could not load dataset: {e}")
        if not len(new_state.curves):
            raise HTTPException(400, "No usable curves found. Check that x and y columns contain numeric values.")
        app.state.curvelib_sessions.set(request.state.curvelib_session_id, new_state)
        return new_state.envelope({"rows": len(frame), "curves": len(new_state.curves), "pairs": len(new_state.coverage)})

    @app.get("/api/accounting")
    def accounting(request: Request):
        st = require_state(request)
        return st.envelope(_records(st.accounting))

    @app.get("/api/coverage")
    def coverage(request: Request, min_points: int = None, min_clusters: int = None, min_x_span: float = None):
        st = require_state(request)
        t = E.coverage(st.curves, min_points, min_clusters, min_x_span, st.manifest)
        return st.envelope(_records(t))

    @app.get("/api/sweep")
    def sweep(request: Request, points: str = "0,10,25,50,100", clusters: str = "1,2,3,4"):
        st = require_state(request)
        p = [int(x) for x in points.split(",")]
        k = [int(x) for x in clusters.split(",")]
        return st.envelope(_records(E.sweep(st.curves, p, k, st.manifest["pair_coverage"].get("min_x_span", 0.0))))

    @app.get("/api/entities")
    def entities(request: Request):
        st = require_state(request)
        if hasattr(st.pack, "entity_picker"):
            return st.envelope(st.pack.entity_picker(st.curves, st.coverage))
        g = st.curves[st.curves["clean"]].groupby("group_b").agg(curves=("n_points", "size"), points=("n_points", "sum"),
                                                                 clusters=("cluster", "nunique")).reset_index()
        return st.envelope({"type": "list", "cells": _records(g.rename(columns={"group_b": "id"}))})

    @app.get("/api/curves")
    def curves(request: Request, group_a: list[str] = Query(None), group_b: list[str] = Query(None), clean_only: bool = True):
        st = require_state(request)
        c = st.curves[st.curves["clean"]] if clean_only else st.curves
        if group_a:
            c = c[c["group_a"].isin(group_a)]
        if group_b:
            c = c[c["group_b"].isin(group_b)]
        cols = ["curve_id", "group_a", "group_b", "cluster", "n_points", "x_min", "x_max", "x_span", "clean"]
        return st.envelope(_records(c[cols]))

    @app.get("/api/points")
    def points(request: Request, curve_id: list[str] = Query(...)):
        st = require_state(request)
        r = st.rows[st.rows["_curve_id"].isin(curve_id) & (st.rows["_status"] == "usable")]
        if r.empty:
            raise HTTPException(404, "no usable points for these curves")
        # Keep all source and derived data columns for rich hover details, while hiding
        # engine-internal fields such as _status and _curve_id.
        reserved = {"_curve_id", "_x", "_y", "curve_id", "x", "y"}
        show = [c for c in r.columns if not c.startswith("_") and c not in reserved]
        out = r[["_curve_id", "_x", "_y"] + show].rename(columns={"_curve_id": "curve_id", "_x": "x", "_y": "y"})
        return st.envelope(_records(out))

    @app.get("/api/fit")
    def fit(request: Request, curve_id: list[str] = Query(...), model: str = "logistic", seed: int = 0):
        """Server-side fit with the shared analysis code. One fit over all selected curves; when they come
        from more than one cluster (paper), parameter intervals resample whole clusters and a warning is set."""
        st = require_state(request)
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
    def predict(request: Request, group_a: str, group_b: str, solids_g_L: float, total_sorbate_mol_L: float, ionic_strength: float,
                direction: str = None):
        st = require_state(request)
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


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.environ.get("CURVELIB_HOST", "127.0.0.1"),
                port=int(os.environ.get("PORT", "8000")), reload=False)
