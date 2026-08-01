"""Fail-closed composition for modular and preserved Phase 1 contracts."""

from __future__ import annotations

from scripts.quality.publication_boundary.cli import main as check_publication_boundary
from scripts.quality.publication_boundary.reporting import print_result
from scripts.quality.r0c_a1_scope import evaluate_repository_scope

from .legacy import run_preserved_contracts


def main() -> int:
    try:
        publication_status = check_publication_boundary()
        if publication_status != 0:
            return publication_status
        recovery_scope = evaluate_repository_scope()
        if recovery_scope.failures:
            return print_result(
                header="R0C-A1 scope quality failures:",
                success="R0C-A1 scope quality gate passed.",
                failures=recovery_scope.failures,
            )
        return run_preserved_contracts()
    except Exception:
        print("Phase 1 quality runner could not complete safely.")
        return 1
