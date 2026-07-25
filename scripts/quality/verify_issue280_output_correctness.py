"""Evaluate Issue 280 semantic closure without trusting aggregate pass claims."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.quality.semantic_closure import evaluate_closure  # noqa: E402


MATRIX_PATH = ROOT / "reports" / "checkpoint3-issue280" / "requirement-matrix.json"
SEMANTIC_CLOSURE_ROW_IDS = (
    "R280-AUDIENCE-001",
    "R280-DEPTH-002",
    "R280-AUDIENCE-DEPTH-001",
    "R280-S6-001",
    "R280-CONVERSION-001",
    "R280-QUALITY-001",
    "R280-OUTPUT-CORRECTNESS-001",
)


def _head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", default=None)
    args = parser.parse_args(argv)

    try:
        artifact = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        matrix = artifact["semanticClosure"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Issue 280 semantic closure FAILED: matrix-unreadable:{exc}")
        return 2
    if not isinstance(matrix, dict):
        print("Issue 280 semantic closure FAILED: semanticClosure is not an object")
        return 2

    expected_head = args.expected_head or _head()
    result = evaluate_closure(
        matrix,
        expected_head=expected_head,
        expected_row_ids=SEMANTIC_CLOSURE_ROW_IDS,
    )
    if result.closed:
        print(f"Issue 280 semantic closure passed at exact head {expected_head}.")
        return 0

    print(f"Issue 280 semantic closure FAILED at exact head {expected_head}:")
    for reason in result.reasons:
        print(f"- {reason}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
