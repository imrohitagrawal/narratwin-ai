#!/usr/bin/env python3
"""Fail clearly for future stage quality gates that are declared but not active yet."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORDER = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "final"]


def main() -> None:
    expected = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    stage_file = ROOT / ".stage" / "current"
    current = stage_file.read_text(encoding="utf-8").strip() if stage_file.exists() else "missing"

    if expected not in ORDER:
        print(f"[quality] FAIL: unknown expected stage {expected!r}", file=sys.stderr)
        raise SystemExit(1)

    if current not in ORDER:
        print(f"[quality] FAIL: unsupported current stage {current!r}", file=sys.stderr)
        raise SystemExit(1)

    if ORDER.index(current) < ORDER.index(expected):
        print(
            f"[quality] FAIL: stage {expected} gate is declared but not active yet; current stage is {current}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(
        f"[quality] FAIL: stage {expected} is active but its executable checks have not been implemented yet.",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
