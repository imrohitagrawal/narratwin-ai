#!/usr/bin/env python3
"""Fail loudly for stage quality gates that are not implemented yet."""

from __future__ import annotations

import sys


def main() -> int:
    stage = sys.argv[1] if len(sys.argv) > 1 else "Requested stage"
    print(
        f"{stage} quality gate is not implemented yet. "
        "Open the stage issue, implement the gate in that stage branch, "
        "and wire it to the Makefile before using this target."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
