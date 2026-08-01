"""Fail-closed composition for modular and preserved Phase 1 contracts."""

from __future__ import annotations

from scripts.quality.publication_boundary.cli import main as check_publication_boundary

from .legacy import run_preserved_contracts


def main() -> int:
    try:
        publication_status = check_publication_boundary()
        if publication_status != 0:
            return publication_status
        return run_preserved_contracts()
    except Exception:
        print("Phase 1 quality runner could not complete safely.")
        return 1
