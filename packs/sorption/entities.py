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
