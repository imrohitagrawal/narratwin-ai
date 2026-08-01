#!/usr/bin/env python3
"""Stable entry point for the modular Phase 1 quality runner."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.quality.phase1_closure.runner import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
