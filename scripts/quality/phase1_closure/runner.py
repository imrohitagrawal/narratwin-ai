"""Fail-closed composition for modular and preserved Phase 1 contracts."""

from __future__ import annotations

import hashlib
import json
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
ISSUE521_BRANCH = "phase-1-closure-process-521-master-program-v2"
ISSUE521_INTEGRATION_BASE = "0e4efa56b36773ad8c687fb9daa73adc0152b89c"
ISSUE521_PREFLIGHT = "docs/governance/preflights/issue-521.json"
ISSUE521_PREFLIGHT_SHA256 = "6f441468c5ae5d6d91010792c364c5fcbba9a3c3a909e39cf4db0fe20e41d92f"
ISSUE521_LINE_CAP = 8_500


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


def _changed_paths(head: str) -> frozenset[str]:
    raw = _git("diff", "--name-only", "-z", ISSUE456_BASE, head, "--")
    try:
        return frozenset(raw.decode("utf-8").rstrip("\0").split("\0")) if raw else frozenset()
    except UnicodeError:
        return frozenset()


def _changed_paths_since(base: str, head: str) -> frozenset[str]:
    raw = _git("diff", "--name-only", "-z", base, head, "--")
    try:
        return frozenset(raw.decode("utf-8").rstrip("\0").split("\0")) if raw else frozenset()
    except UnicodeError:
        return frozenset()


def _charged_lines(base: str, head: str) -> int | None:
    raw = _git("diff", "--numstat", base, head, "--")
    if raw is None:
        return None
    total = 0
    try:
        for line in raw.decode("utf-8").splitlines():
            fields = line.split("\t")
            if len(fields) != 3 or fields[0] == "-" or fields[1] == "-":
                return None
            total += int(fields[0]) + int(fields[1])
    except (UnicodeError, ValueError):
        return None
    return total


def _issue521_scope() -> tuple[frozenset[str], list[str]]:
    path = ROOT / ISSUE521_PREFLIGHT
    try:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ISSUE521_PREFLIGHT_SHA256:
            return frozenset(), ["Issue #521 preflight hash drifted."]
        artifact = json.loads(raw.decode("utf-8"))
        required = artifact["scope"]["required"]
        allowed = artifact["scope"]["allowed_prefixes"]
        if len(required) != 27 or set(required) != set(allowed):
            return frozenset(), ["Issue #521 preflight must contain exactly twenty-seven matching paths."]
        return frozenset(required), []
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError):
        return frozenset(), ["Issue #521 preflight could not be read safely."]


def run_issue521_master_program_v2() -> int:
    head = _head()
    expected_paths, scope_failures = _issue521_scope()
    findings = validate_governance_preflight_repository(
        ROOT, base_sha=ISSUE521_INTEGRATION_BASE, head_sha=head, issue_number=521, branch=ISSUE521_BRANCH,
    )
    changed = _changed_paths_since(ISSUE521_INTEGRATION_BASE, head)
    failures = scope_failures + [f"Issue #521 preflight finding: {finding.code}" for finding in findings]
    if changed != expected_paths:
        failures.append("Issue #521 exact governance preflight scope failed.")
    charged = _charged_lines(ISSUE521_INTEGRATION_BASE, head)
    if charged is None or charged > ISSUE521_LINE_CAP:
        failures.append(f"Issue #521 aggregate charged-line budget exceeded or uncountable (cap {ISSUE521_LINE_CAP}).")
    if not failures:
        from scripts.quality.issue521_master_program_v2 import validate_repository

        failures.extend(validate_repository(ROOT, certification=False))
    if failures:
        return legacy._print_result(failures)
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


def check_cut1_presenter_contract() -> int:
    return 1 if validate_contract_bundle(ROOT) else 0


def run_preserved_contracts() -> int:
    branch = current_branch(ROOT)
    if branch == ISSUE521_BRANCH:
        return run_issue521_master_program_v2()
    if branch != ISSUE456_BRANCH:
        return legacy.run_preserved_contracts()
    head = _head()
    findings = validate_governance_preflight_repository(
        ROOT, base_sha=ISSUE456_BASE, head_sha=head, issue_number=456, branch=branch,
    )
    if findings or _changed_paths(head) != ISSUE456_PATHS:
        return legacy._print_result(["Issue #456 exact governance preflight scope failed."])
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
