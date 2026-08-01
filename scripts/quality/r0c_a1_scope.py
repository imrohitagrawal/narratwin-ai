"""Exact modular scope boundary for the R0C-A1.1 recovery children."""

from __future__ import annotations

import re
from dataclasses import dataclass

from scripts.quality import check_phase1_closure_docs as legacy_checker
from scripts.quality import publication_boundary as _publication_boundary
from scripts.quality.branch_identity import current_branch


git_evidence = _publication_boundary.git_evidence
CURRENT_BRANCH = "phase-1-closure-process-330-r0c-a1-1a-freshness-scope-freeze"
B_PATTERN = re.compile(r"^phase-1-closure-process-([1-9]\d*)-r0c-a1-1b-offline-freshness$")
C_PATTERN = re.compile(r"^phase-1-closure-process-([1-9]\d*)-r0c-a1-1c-live-freshness$")
B_FAMILY = re.compile(r"^phase-1-closure-process-([1-9]\d*)-r0c-a1-1b(?:-|$)")
C_FAMILY = re.compile(r"^phase-1-closure-process-([1-9]\d*)-r0c-a1-1c(?:-|$)")
CURRENT_FILES = frozenset(
    {
        "docs/governance/preflights/issue-330.json",
        "scripts/quality/r0c_a1_scope.py",
        "tests/unit/test_r0c_a1_scope.py",
        "scripts/quality/phase1_closure/runner.py",
        "scripts/quality/phase1_closure/legacy.py",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    }
)
B_FILES = frozenset(
    {
        "docs/agent-context/contracts-v1.schema.json",
        "docs/agent-context/current-state-v1.json",
        "docs/agent-context/context-policy-manifest-v1.json",
        "scripts/agent_context/core.py",
        "scripts/agent_context/cli.py",
        "tests/unit/test_agent_context_freshness.py",
        "docs/STATUS.md",
    }
)
C_FILES = frozenset(
    {
        "scripts/agent_context/github.py",
        "tests/unit/test_agent_context_github.py",
        ".github/workflows/quality-gates.yml",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
    }
)


@dataclass(frozen=True)
class ScopePolicy:
    files: frozenset[str]
    line_cap: int


@dataclass(frozen=True)
class ScopeEvaluation:
    managed: bool
    failures: tuple[str, ...]


def _policy(branch: str, *, allow_near_match: bool) -> ScopePolicy | None:
    if branch == CURRENT_BRANCH or (allow_near_match and branch.startswith(CURRENT_BRANCH)):
        return ScopePolicy(CURRENT_FILES, 500)
    patterns = ((B_PATTERN, B_FAMILY, B_FILES, 800), (C_PATTERN, C_FAMILY, C_FILES, 650))
    for exact, family, static_files, cap in patterns:
        match = (family if allow_near_match else exact).match(branch)
        if match:
            preflight = f"docs/governance/preflights/issue-{match.group(1)}.json"
            return ScopePolicy(static_files | {preflight}, cap)
    return None


def is_managed_branch(branch: str) -> bool:
    return _policy(branch, allow_near_match=False) is not None


def validate_scope(
    *, branch: str, changed_files: list[str] | None, charged_line_count: int | None
) -> ScopeEvaluation:
    policy = _policy(branch, allow_near_match=True)
    if policy is None:
        return ScopeEvaluation(False, ())
    failures: list[str] = []
    if not is_managed_branch(branch):
        failures.append("R0C-A1 work requires an exact frozen recovery branch.")
    if changed_files is None or not all(isinstance(path, str) for path in changed_files):
        failures.append("R0C-A1 changed-file evidence is unavailable.")
        changed: set[str] = set()
    else:
        if len(changed_files) != len(set(changed_files)):
            failures.append("R0C-A1 changed-file evidence contains a duplicate.")
        changed = set(changed_files)
    for path in sorted(policy.files - changed):
        failures.append(f"R0C-A1 required path {path} must change.")
    for path in sorted(changed - policy.files):
        failures.append(f"R0C-A1 path {path} may not change.")
    if (
        isinstance(charged_line_count, bool)
        or not isinstance(charged_line_count, int)
        or charged_line_count < 0
    ):
        failures.append("R0C-A1 charged-line evidence is unavailable.")
    elif charged_line_count > policy.line_cap:
        failures.append(f"R0C-A1 scope exceeds its {policy.line_cap}-line cap.")
    return ScopeEvaluation(True, tuple(failures))


def evaluate_repository_scope() -> ScopeEvaluation:
    branch = current_branch()
    if _policy(branch, allow_near_match=True) is None:
        return ScopeEvaluation(False, ())
    base = legacy_checker.resolve_base()
    if not base:
        return ScopeEvaluation(True, ("R0C-A1 diff-base evidence is unavailable.",))
    return validate_scope(
        branch=branch,
        changed_files=git_evidence.changed_files(base),
        charged_line_count=git_evidence.charged_lines(base),
    )
