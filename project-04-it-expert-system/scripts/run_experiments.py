"""Unified experiment runner reproducing every table and figure in the Final Report.

Usage (from inside `code/`):
    python scripts/run_experiments.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_step(script_rel: str, out_dir: Path) -> None:
    cmd = [sys.executable, str(ROOT / script_rel), str(out_dir)]
    print(f"==> Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=ROOT, check=False)
    if res.returncode != 0:
        raise SystemExit(res.returncode)


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "experiments" / "results"
    run_step("experiments/ablation.py", out_dir)
    run_step("experiments/reasoning_probes.py", out_dir)
    run_step("experiments/product_eval.py", out_dir)
    print(f"\nAll tables and figures successfully reproduced in: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
