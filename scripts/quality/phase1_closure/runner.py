"""Fail-closed composition for modular and preserved Phase 1 contracts."""

from __future__ import annotations

from pathlib import Path

from scripts.quality.cut1_presenter_contract import validate_contract_bundle
from scripts.quality.publication_boundary.cli import main as check_publication_boundary

from .legacy import run_preserved_contracts


def check_cut1_presenter_contract() -> int:
    root = Path(__file__).resolve().parents[3]
    return 1 if validate_contract_bundle(root) else 0


def main() -> int:
    try:
        publication_status = check_publication_boundary()
        if publication_status != 0:
            return publication_status
        cut1_status = check_cut1_presenter_contract()
        if cut1_status != 0:
            return cut1_status
        return run_preserved_contracts()
    except Exception:
        print("Phase 1 quality runner could not complete safely.")
        return 1
