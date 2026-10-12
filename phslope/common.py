"""common.py -- config loading, data-path resolution, and run stamps.

Every stage script calls `run_stamp` and writes it next to its outputs, so any
number in a report can be traced to the exact code (git commit) and settings
(config hash) that produced it.
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

import yaml

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PKG_DIR)
CONFIG_DIR = os.path.join(PKG_DIR, "config")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "phslope")
DESCRIPTOR_DIR = os.path.join(PROJECT_ROOT, "data", "descriptors")


def load_yaml(name):
    with open(os.path.join(CONFIG_DIR, name), encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config():
    return load_yaml("config.yaml")


def load_thresholds():
    return load_yaml("thresholds.yaml")


def resolve_data_file(cli_path=None, config=None):
    """--data flag > SORPTION_DATA_FILE env var > config.yaml > data_audit.CONFIG."""
    if cli_path:
        return cli_path
    if os.environ.get("SORPTION_DATA_FILE"):
        return os.environ["SORPTION_DATA_FILE"]
    if config and config.get("data", {}).get("file"):
        return config["data"]["file"]
    import data_audit
    return data_audit.CONFIG["DATA_FILE"]


def config_hash():
    """Short hash over the config files, in a fixed order."""
    h = hashlib.sha256()
    for name in ("config.yaml", "thresholds.yaml", "classes.yaml", "schemes.yaml"):
        with open(os.path.join(CONFIG_DIR, name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:12]


def git_commit():
    """Current commit, with '-dirty' appended if tracked files have uncommitted changes."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=PROJECT_ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_stamp(data_file=None):
    return {
        "git_commit": git_commit(),
        "config_hash": config_hash(),
        "data_file": data_file,
        "run_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_stamp(out_dir, stamp):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "RUN_INFO.json"), "w", encoding="utf-8") as f:
        json.dump(stamp, f, indent=2)
    print(f"[run] commit {stamp['git_commit']}  config {stamp['config_hash']}")
