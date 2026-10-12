import data_audit
from phslope.common import config_hash, git_commit, resolve_data_file, run_stamp


def test_data_path_precedence(monkeypatch):
    monkeypatch.setenv("SORPTION_DATA_FILE", "env.csv")
    assert resolve_data_file("cli.csv") == "cli.csv"
    assert resolve_data_file(None, {"data": {"file": "cfg.csv"}}) == "env.csv"
    monkeypatch.delenv("SORPTION_DATA_FILE")
    assert resolve_data_file(None, {"data": {"file": "cfg.csv"}}) == "cfg.csv"
    assert resolve_data_file(None, {"data": {"file": None}}) == data_audit.CONFIG["DATA_FILE"]


def test_stamp_fields():
    s = run_stamp("x.csv")
    assert len(config_hash()) == 12 and s["config_hash"] == config_hash()
    assert s["git_commit"] == git_commit() and s["data_file"] == "x.csv"
