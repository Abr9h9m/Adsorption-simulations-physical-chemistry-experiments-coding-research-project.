"""Sorption pack entity picker data (WEB_INTERFACE_PROTOCOL.md section 3b, phase P2a).

`propose_sorbate_map` PARSES the dataset's sorbate labels into (element, oxidation state); it does not look
anything up. Labels that do not parse as `<Element>(<+/-n>)` (organic acids, `Pu` without an oxidation
state, `COM`) are written with status `needs_review`, never dropped. The resulting
packs/sorption/sorbate_map.csv is a PROPOSAL for Samuel to review (protocol section 7, item 5); a human
edits `species_form` and sets `status: reviewed`.

`entity_counts` gives the per-element numbers the periodic table colours by (points, curves, papers,
pairs with >= 2 papers, minerals), computed by the generic engine so they equal engine counts exactly.
"""
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(HERE, "sorbate_map.csv")
_LABEL = re.compile(r"^([A-Z][a-z]?)\(([+-]\d+)\)$")
ELEMENTS = {"H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K",
            "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb",
            "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs",
            "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf",
            "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac",
            "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"}


def parse_label(label):
    s = str(label).strip()
    m = _LABEL.match(s)
    if m and m.group(1) in ELEMENTS:
        return {"element": m.group(1), "oxidation_state": int(m.group(2)), "status": "parsed"}
    if s in ELEMENTS:
        return {"element": s, "oxidation_state": None, "status": "needs_review",
                "note": "element without oxidation state"}
    return {"element": None, "oxidation_state": None, "status": "needs_review",
            "note": "not an element label (organic or unknown); shown under 'Other sorbates'"}


def propose_sorbate_map(labels):
    rows = []
    for lab in sorted(set(labels)):
        r = parse_label(lab)
        rows.append({"sorbate_label": lab, "element": r["element"], "oxidation_state": r["oxidation_state"],
                     "species_form": "", "status": r["status"], "note": r.get("note", "")})
    return pd.DataFrame(rows)


def write_map(labels, path=MAP_PATH):
    """Writes the proposal unless a reviewed map already exists."""
    if os.path.exists(path):
        old = pd.read_csv(path)
        if (old["status"] == "reviewed").any():
            return f"kept {path} (contains reviewed rows)"
    propose_sorbate_map(labels).to_csv(path, index=False)
    return f"wrote {path}"


def entity_counts(curves, coverage, sorbate_map):
    """Per element: points, curves, papers, minerals, pairs with >= 2 papers (from clean curves).
    `curves` and `coverage` come from curvelib.engine.run. Unresolved labels are returned separately."""
    m = sorbate_map.set_index("sorbate_label")
    c = curves[curves["clean"]].copy()
    c["element"] = c["group_b"].map(m["element"])
    cov = coverage.copy()
    cov["element"] = cov["group_b"].map(m["element"])
    g = c.dropna(subset=["element"]).groupby("element")
    out = pd.DataFrame({"points": g["n_points"].sum(), "curves": g.size(), "papers": g["cluster"].nunique(),
                        "minerals": g["group_a"].nunique(),
                        "oxidation_states": c.dropna(subset=["element"]).assign(
                            ox=c["group_b"].map(m["oxidation_state"])).groupby("element")["ox"].nunique()})
    out["pairs_2plus_papers"] = cov[cov["clusters"] >= 2].groupby("element").size()
    out = out.fillna(0).astype(int).reset_index()
    other = c[c["element"].isna()].groupby("group_b").agg(points=("n_points", "sum"), curves=("n_points", "size"),
                                                          papers=("cluster", "nunique")).reset_index()
    return out, other


# Standard periodic-table layout: (symbol, row, column). Rows 1-7 main table; lanthanides row 9, actinides
# row 10 (columns 3-17), as in the usual 18-column display.
_MAIN = """H 1 1|He 1 18|Li 2 1|Be 2 2|B 2 13|C 2 14|N 2 15|O 2 16|F 2 17|Ne 2 18|Na 3 1|Mg 3 2|Al 3 13|Si 3 14|P 3 15|S 3 16|Cl 3 17|Ar 3 18|K 4 1|Ca 4 2|Sc 4 3|Ti 4 4|V 4 5|Cr 4 6|Mn 4 7|Fe 4 8|Co 4 9|Ni 4 10|Cu 4 11|Zn 4 12|Ga 4 13|Ge 4 14|As 4 15|Se 4 16|Br 4 17|Kr 4 18|Rb 5 1|Sr 5 2|Y 5 3|Zr 5 4|Nb 5 5|Mo 5 6|Tc 5 7|Ru 5 8|Rh 5 9|Pd 5 10|Ag 5 11|Cd 5 12|In 5 13|Sn 5 14|Sb 5 15|Te 5 16|I 5 17|Xe 5 18|Cs 6 1|Ba 6 2|Hf 6 4|Ta 6 5|W 6 6|Re 6 7|Os 6 8|Ir 6 9|Pt 6 10|Au 6 11|Hg 6 12|Tl 6 13|Pb 6 14|Bi 6 15|Po 6 16|At 6 17|Rn 6 18|Fr 7 1|Ra 7 2"""
_LAN = "La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu".split()
_ACT = "Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr".split()
POSITIONS = {s: (int(r), int(c)) for s, r, c in (x.split() for x in _MAIN.split("|"))}
POSITIONS.update({s: (9, 3 + i) for i, s in enumerate(_LAN)})
POSITIONS.update({s: (10, 3 + i) for i, s in enumerate(_ACT)})


def entity_picker(curves, coverage, sorbate_map=None):
    """The sorption pack's front page: a periodic table of sorbate elements (WEB_INTERFACE_PROTOCOL.md 3b)."""
    smap = sorbate_map if sorbate_map is not None else (
        pd.read_csv(MAP_PATH) if os.path.exists(MAP_PATH) else propose_sorbate_map(curves["group_b"].unique()))
    counts, other = entity_counts(curves, coverage, smap)
    labels = smap.dropna(subset=["element"]).groupby("element")["sorbate_label"].apply(list).to_dict()
    cells = []
    for sym, (row, col) in POSITIONS.items():
        r = counts[counts["element"] == sym]
        cell = {"id": sym, "label": sym, "row": row, "col": col, "has_data": bool(len(r)),
                "members": labels.get(sym, [])}
        if len(r):
            cell.update({k: int(v) for k, v in r.iloc[0].drop("element").items()})
        cells.append(cell)
    return {"type": "periodic_table", "metrics": ["points", "curves", "papers", "pairs_2plus_papers", "minerals"],
            "cells": cells, "other": other.rename(columns={"group_b": "label"}).to_dict("records"),
            "needs_review": smap[smap["status"] == "needs_review"]["sorbate_label"].tolist()}
