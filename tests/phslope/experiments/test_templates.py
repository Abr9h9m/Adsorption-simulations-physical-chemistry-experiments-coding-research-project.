import pandas as pd

from phslope.experiments.templates import _write_if_empty, priority


def test_priority_ranks_pairs_with_three_papers(tmp_path):
    rows = [{"curve_id": f"c{i}", "reference": r, "mineral": "g", "sorbate": "U", "shape": "rising"}
            for i, r in enumerate(["a", "a", "b", "c"])]
    rows.append({"curve_id": "x", "reference": "d", "mineral": "h", "sorbate": "U", "shape": "rising"})
    p = priority(pd.DataFrame(rows))
    assert list(p["reference"]) == ["a", "b", "c"] and p["priority_rank"].tolist() == [1, 2, 3]


def test_templates_never_overwrite_entries(tmp_path):
    path = tmp_path / "t.csv"
    pd.DataFrame({"sorbate": ["U"], "pKa1": [""]}).to_csv(path, index=False)
    _write_if_empty(pd.DataFrame({"sorbate": ["U", "Se"], "pKa1": ["", ""]}), str(path))
    assert len(pd.read_csv(path)) == 2                                   # empty template replaced
    pd.DataFrame({"sorbate": ["U"], "pKa1": ["4.2"]}).to_csv(path, index=False)
    msg = _write_if_empty(pd.DataFrame({"sorbate": ["U", "Se"], "pKa1": ["", ""]}), str(path))
    assert "kept" in msg and len(pd.read_csv(path)) == 1
