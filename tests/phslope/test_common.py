import data_audit
from phslope import common
from phslope.common import config_hash, git_commit, resolve_data_file, run_stamp


def test_data_path_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv("SORPTION_DATA_FILE", "env.csv")
    assert resolve_data_file("cli.csv") == "cli.csv"
    assert resolve_data_file(None, {"data": {"file": "cfg.csv"}}) == "env.csv"
    monkeypatch.delenv("SORPTION_DATA_FILE")
    assert resolve_data_file(None, {"data": {"file": "cfg.csv"}}) == "cfg.csv"
    monkeypatch.setattr(common, "REPO_DATA_FILE", str(tmp_path / "data" / "raw" / "sc.dataset.csv"))
    assert resolve_data_file(None, {"data": {"file": None}}) == data_audit.CONFIG["DATA_FILE"]
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "sc.dataset.csv").write_text("x")
    assert resolve_data_file(None, {"data": {"file": None}}) == common.REPO_DATA_FILE   # repo copy wins when present


def test_stamp_fields():
    s = run_stamp("x.csv")
    assert len(config_hash()) == 12 and s["config_hash"] == config_hash()
    assert s["git_commit"] == git_commit() and s["data_file"] == "x.csv"
