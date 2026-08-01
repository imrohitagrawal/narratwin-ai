"""Exact modular scope boundary for the R0C-A1.1 recovery children."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScopeEvaluation:
    managed: bool
    failures: tuple[str, ...]


def is_managed_branch(_branch: str) -> bool:
    return False


def validate_scope(
    *, branch: str, changed_files: list[str] | None, charged_line_count: int | None
) -> ScopeEvaluation:
    del branch, changed_files, charged_line_count
    return ScopeEvaluation(False, ("R0C-A1 scope validation is not implemented.",))


def evaluate_repository_scope() -> ScopeEvaluation:
    return ScopeEvaluation(False, ("R0C-A1 repository scope is not implemented.",))
