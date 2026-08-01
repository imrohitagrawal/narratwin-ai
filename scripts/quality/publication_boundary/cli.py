"""Fail-closed command-line composition for the modular publication gate."""

from __future__ import annotations

from scripts.quality.branch_identity import current_branch

from .context import check_context_budgets
from .git_evidence import changed_files, charged_lines, resolve_base
from .reporting import print_result
from .repository import check_publication_boundary
from .scope import validate_issue_scope


def _evaluate() -> list[str]:
    failures: list[str] = []
    check_publication_boundary(failures)
    check_context_budgets(failures)
    branch = current_branch()
    if not branch:
        failures.append("Publication boundary branch evidence is unavailable or inconsistent.")
    elif branch.startswith("phase-1-closure-process-324-"):
        base = resolve_base()
        if base is None:
            failures.append("Issue #324 diff base is unavailable.")
        else:
            files = changed_files(base)
            if files is None:
                failures.append("Issue #324 changed-file evidence is unavailable.")
            else:
                failures.extend(
                    validate_issue_scope(
                        branch=branch,
                        changed_files=files,
                        charged_line_count=charged_lines(base),
                    )
                )
    return failures


def main() -> int:
    try:
        failures = _evaluate()
    except Exception:
        failures = ["Publication boundary gate could not complete safely."]
    return print_result(
        header="Publication boundary quality gate failed:",
        success="Publication boundary quality gate passed.",
        failures=failures,
    )
