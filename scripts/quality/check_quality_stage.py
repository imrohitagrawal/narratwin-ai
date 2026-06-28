#!/usr/bin/env python3
"""Dispatch quality gates according to .stage/current."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ORDER = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "final"]
TARGETS = {
    "0": "stage0-quality",
    "1": "stage1-quality",
    "2": "stage2-quality",
    "3": "stage3-quality",
    "4": "stage4-quality",
    "5": "stage5-quality",
    "6": "stage6-quality",
    "7": "stage7-quality",
    "8": "stage8-quality",
    "final": "final-review-quality",
}


def read_current_stage() -> str:
    stage_file = ROOT / ".stage" / "current"
    if not stage_file.exists():
        print("[quality] FAIL: .stage/current is missing", file=sys.stderr)
        raise SystemExit(1)
    value = stage_file.read_text(encoding="utf-8").strip()
    if value not in ORDER:
        print(f"[quality] FAIL: unsupported .stage/current value: {value!r}", file=sys.stderr)
        raise SystemExit(1)
    return value


def run_target(target: str) -> None:
    print(f"[quality] running {target}")
    result = subprocess.run(["make", target], cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    current = read_current_stage()
    max_index = ORDER.index(current)
    for stage in ORDER[: max_index + 1]:
        run_target(TARGETS[stage])
    print(f"[quality] PASS through stage {current}")


if __name__ == "__main__":
    main()
