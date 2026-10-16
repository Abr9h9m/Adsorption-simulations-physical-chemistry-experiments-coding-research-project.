"""rerun_all.py -- run every stage and experiment again under the current PHSLOPE_RESPONSE.

    PHSLOPE_RESPONSE=kd python -m phslope.rerun_all

Stage 0 and Stage 1 run first (everything reads the Stage 1 library); then two chains run in parallel:
stages 2/3, pooled and export; and the experiment program (E0-E23, F on development papers only).
A failing step is logged and the chain continues. The locked set is never opened. Log per step in
<REPORTS_DIR>/rerun_logs/, overview in <REPORTS_DIR>/rerun_logs/RERUN.md.
"""
import os
import subprocess
import sys
import threading
import time

from phslope.common import PROJECT_ROOT, REPORTS_DIR, RESPONSE

FIRST = [["phslope.census"], ["phslope.stage1"]]
STAGES = [["phslope.stage2", "--exploratory"], ["phslope.pooled"], ["phslope.export"],
          ["phslope.stage3", "--exploratory"]]
EXPERIMENTS = [[f"phslope.experiments.{m}"] for m in (
    "e00_inventory", "e03_audit", "e01_logk_mixed", "e21_conformal_metrics", "e04_lab_effect", "e05_coverage",
    "e08_ionic_strength", "e09_surface_area", "e11_slope", "e13_competition", "e16_transfer", "e20_temperature",
    "e23_placebo_power", "integrate", "m_checks", "e15_bakeoff", "e15b_edge", "e15c_gbm_followup", "e12_loading",
    "e17_e22", "e14_specification", "e07_carbonate", "e02_weights_censoring")]

LOG_DIR = os.path.join(REPORTS_DIR, "rerun_logs")
LOCK = threading.Lock()
ROWS = []


def step(args):
    name = args[0].split(".")[-1]
    t0 = time.time()
    with open(os.path.join(LOG_DIR, f"{name}.log"), "w", encoding="utf-8") as log:
        rc = subprocess.run([sys.executable, "-m", *args], cwd=PROJECT_ROOT, stdout=log, stderr=subprocess.STDOUT,
                            env=dict(os.environ, PHSLOPE_RESPONSE=RESPONSE, PYTHONIOENCODING="utf-8")).returncode
    row = (" ".join(args), "ok" if rc == 0 else f"FAILED (exit {rc})", round((time.time() - t0) / 60, 1))
    with LOCK:
        ROWS.append(row)
        print(f"[{time.strftime('%H:%M')}] {row[0]}: {row[1]} ({row[2]} min)", flush=True)
        write_overview()
    return rc


def write_overview():
    with open(os.path.join(LOG_DIR, "RERUN.md"), "w", encoding="utf-8") as f:
        f.write(f"# Rerun under PHSLOPE_RESPONSE={RESPONSE}\n\n| step | result | minutes |\n|---|---|---|\n")
        f.writelines(f"| {a} | {b} | {c} |\n" for a, b, c in ROWS)


def chain(steps):
    for s in steps:
        step(s)


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"response = {RESPONSE}; outputs in {REPORTS_DIR}", flush=True)
    for s in FIRST:
        if step(s) != 0:
            print("stopping: everything downstream needs this step", flush=True)
            return 1
    threads = [threading.Thread(target=chain, args=(c,)) for c in (STAGES, EXPERIMENTS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return 0


if __name__ == "__main__":
    sys.exit(main())
