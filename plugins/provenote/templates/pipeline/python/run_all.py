#!/usr/bin/env python3
"""Run every numbered step src/NN_*.py in order; stop at the first failure.

Usage: python3 run_all.py   (or: uv run python run_all.py)
Each step runs as its own process with the project root as working directory.
Exit codes: 0 all steps passed, 1 a step failed, 2 no steps found.
"""
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("run_all.py needs Python 3.9 or newer")

ROOT = Path(__file__).resolve().parent


def log(msg: str) -> None:
    print(f"{datetime.now().isoformat(timespec='seconds')} {msg}", flush=True)


def main() -> int:
    steps = sorted(p for p in (ROOT / "src").glob("[0-9][0-9]_*.py"))
    if not steps:
        log("no steps found in src/")
        return 2
    for step in steps:
        log(f"START {step.name}")
        t0 = time.time()
        r = subprocess.run([sys.executable, str(step)], cwd=ROOT)
        dt = time.time() - t0
        if r.returncode != 0:
            log(f"FAIL  {step.name} (exit {r.returncode}, {dt:.1f}s)")
            return 1
        log(f"OK    {step.name} ({dt:.1f}s)")
    log(f"PASS  {len(steps)} step(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
