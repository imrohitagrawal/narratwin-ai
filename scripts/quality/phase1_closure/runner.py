"""Fail-closed composition for modular and preserved Phase 1 contracts."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.governance_preflight_repository import validate_governance_preflight_repository
from scripts.quality.branch_identity import current_branch
from scripts.quality.cut1_presenter_contract import validate_contract_bundle
from scripts.quality.publication_boundary.cli import main as check_publication_boundary

from . import legacy as legacy


ROOT = Path(__file__).resolve().parents[3]
ISSUE456_BRANCH = "phase-1-closure-process-456-cut1-live-binding-v2"
ISSUE456_BASE = "c3ac83bf05336a539dbdd6af1de9905e6b954289"
ISSUE456_PATHS = frozenset({
    "docs/governance/preflights/issue-456.json",
    "docs/governance/cut1-presenter-live-binding-v2.json",
    "scripts/quality/cut1_presenter_contract.py",
    "tests/unit/test_cut1_presenter_live_binding_v2.py",
    "scripts/quality/phase1_closure/runner.py",
    "tests/unit/phase1_closure/test_runner.py",
    "tests/unit/test_stage8_quality_gate.py",
    "docs/ADR/0066-cut1-presenter-live-binding-v2.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
})
ISSUE391_BRANCH = "phase-1-closure-process-391-resource-lifecycle-enforcement"
ISSUE391_BASE = "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"
ISSUE391_PATHS = frozenset({
    ".github/pull_request_template.md",
    "docs/ADR/0076-session-scoped-resource-lifecycle-enforcement.md",
    "docs/QUALITY_GATES.md",
    "docs/RESOURCE_LIFECYCLE.md",
    "docs/STATUS.md",
    "docs/governance/preflights/issue-391.json",
    "docs/templates/AI_SESSION_FINALIZER_PROMPT.md",
    "scripts/guardrails_check.py",
    "scripts/quality/phase1_closure/runner.py",
    "tests/unit/phase1_closure/test_runner.py",
    "tests/unit/test_guardrails_check.py",
})


def _git(*args: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["/usr/bin/git", *args], cwd=ROOT,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"},
            capture_output=True, check=False, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def _head() -> str:
    raw = _git("rev-parse", "HEAD")
    try:
        return raw.decode("ascii").strip() if raw is not None else ""
    except UnicodeError:
        return ""


def _changed_paths(head: str, base: str = ISSUE456_BASE) -> frozenset[str]:
    raw = _git("diff", "--name-only", "-z", base, head, "--")
    try:
        return frozenset(raw.decode("utf-8").rstrip("\0").split("\0")) if raw else frozenset()
    except UnicodeError:
        return frozenset()


def check_cut1_presenter_contract() -> int:
    return 1 if validate_contract_bundle(ROOT) else 0


def run_preserved_contracts() -> int:
    branch = current_branch(ROOT)
    if branch == ISSUE456_BRANCH:
        base = ISSUE456_BASE
        issue = 456
        paths = ISSUE456_PATHS
    elif branch == ISSUE391_BRANCH:
        base = ISSUE391_BASE
        issue = 391
        paths = ISSUE391_PATHS
    else:
        return legacy.run_preserved_contracts()
    head = _head()
    findings = validate_governance_preflight_repository(
        ROOT, base_sha=base, head_sha=head, issue_number=issue, branch=branch,
    )
    changed_paths = _changed_paths(head) if issue == 456 else _changed_paths(head, base)
    if findings or changed_paths != paths:
        return legacy._print_result(
            [f"Issue #{issue} exact governance preflight scope failed."]
        )
    checker = legacy._load_checker()
    failures = legacy.legacy_parity_failures(checker)
    checker.check_branch(failures)
    checker.check_required_files(failures)
    if not failures:
        for name in legacy.PRESERVED_CHECKS:
            if name == "check_active_demo_docs":
                legacy.check_active_demo_docs(checker, failures)
            else:
                getattr(checker, name)(failures)
    return legacy._print_result(failures)


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
