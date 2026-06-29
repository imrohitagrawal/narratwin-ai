#!/usr/bin/env python3
"""Dispatch the top-level quality command to the current stage gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT_STAGE = ROOT / ".stage" / "current"


def main() -> int:
    if not CURRENT_STAGE.exists():
        print("Missing .stage/current. Cannot determine quality stage.")
        return 1

    stage = CURRENT_STAGE.read_text(encoding="utf-8").strip()
    if stage == "0":
        return subprocess.call([sys.executable, "scripts/quality/check_stage0_docs.py"], cwd=ROOT)
    if stage == "1":
        return subprocess.call([sys.executable, "scripts/quality/check_stage1_docs.py"], cwd=ROOT)

    return subprocess.call(
        [sys.executable, "scripts/quality/stage_not_implemented.py", f"Stage {stage}"],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
