"""Explicit compatibility boundary for the frozen Phase 1 checker."""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Protocol

from scripts.quality.branch_identity import current_branch
from scripts.quality.publication_boundary.reporting import MAX_FAILURES, print_result
from scripts.quality.publication_boundary.scope import ISSUE_324_BRANCH


LEGACY_MAIN_SOURCE_SHA256 = "eb5c6a4892fbbdb9c7929f12ace5c360d627d620bd19db205ecf544b02f33944"
LEGACY_DEMO_SOURCE_SHA256 = "75c8ef1cd27526b649ba5cdc883c81ad4bdd5f40e3a48033e30a002592abb620"
ROOT = Path(__file__).resolve().parents[3]
FROZEN_LEGACY_FILES = (
    (
        "scripts/quality/check_phase1_closure_docs.py",
        "95ac28c955fcef4710e63b6dcab4129164d07d07d4b50ea10352f98bc3614958",
        7387,
    ),
    (
        "tests/unit/test_phase1_closure_docs.py",
        "8c36edf1f7f68c082243007b1e1327c71e3a4e3d93490c0b2ab4b9b1da9ee90a",
        9970,
    ),
)
ACTIVE_DEMO_DOCUMENT = "docs/demo/CONTROLLED_LOCAL_DEMO.md"
LEGACY_DEMO_DOCUMENT = "portfolio/README.md"
DEMO_DOCUMENTS = (
    "docs/demo/PHASE_1_DEMO_SCRIPT.md",
    "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
    "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
    ACTIVE_DEMO_DOCUMENT,
)
DEMO_MARKERS = (
    "cp .env.example .env",
    "docker compose up --build",
    "http://localhost:3000",
    "/api/v1/healthz",
    "/api/v1/readyz",
    "create project",
    "upload project knowledge",
    "generate walkthrough script",
    "citations",
    "eval result",
    "saved output",
    "single-process",
    "local-only",
    "JSON restart snapshots",
    "production durability",
    "mock/local providers only",
)
LEGACY_MAIN_CHECKS = (
    "check_branch",
    "check_required_files",
    "check_changed_files",
    "check_final_review_baseline",
    "check_closure_report",
    "check_golden_questions",
    "check_demo_docs",
    "check_real_media_demo_plan",
    "check_release_docs",
    "check_issue39_closure_plan",
    "check_issue125_local_restore_contract",
    "check_issue141_platform_ownership_contract",
    "check_issue126_restore_readiness_contract",
    "check_issue39_execution_strategy",
    "check_issue39_ch11_slo_contract",
    "check_phf020a_policy_contract",
    "check_status_state_v1_contract",
    "check_process_docs",
    "check_issue158_security_history_contract",
    "check_issue300_semantic_governance",
    "check_issue313_repair_feasibility",
    "check_issue319_agent_context",
)
PRESERVED_CHECKS = tuple(
    "check_active_demo_docs" if name == "check_demo_docs" else name
    for name in LEGACY_MAIN_CHECKS[3:]
)


class LegacyReader(Protocol):
    def read(self, path: str) -> str: ...


__all__ = [
    "ACTIVE_DEMO_DOCUMENT",
    "DEMO_MARKERS",
    "ISSUE_324_BRANCH",
    "LEGACY_DEMO_DOCUMENT",
    "MAX_FAILURES",
    "PRESERVED_CHECKS",
    "_load_checker",
    "_print_result",
    "check_active_demo_docs",
    "frozen_file_failures",
    "legacy_parity_failures",
    "run_preserved_contracts",
]


def _load_checker() -> ModuleType:
    return importlib.import_module("scripts.quality.check_phase1_closure_docs")


def _called_checks(source: str) -> tuple[str, ...]:
    tree = ast.parse(textwrap.dedent(source))
    return tuple(
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id.startswith("check_")
    )


def _demo_markers(source: str) -> tuple[str, ...]:
    tree = ast.parse(textwrap.dedent(source))
    candidates: list[tuple[str, ...]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Tuple) or not node.elts:
            continue
        values: list[str] = []
        for item in node.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                break
            values.append(item.value)
        else:
            candidates.append(tuple(values))
    return max(candidates, key=len, default=())


def frozen_file_failures() -> list[str]:
    failures: list[str] = []
    for relative_path, expected_digest, expected_lines in FROZEN_LEGACY_FILES:
        try:
            raw = (ROOT / relative_path).read_bytes()
            line_count = len(raw.decode("utf-8").splitlines())
        except (OSError, UnicodeError):
            failures.append(f"Frozen legacy file evidence unavailable: {relative_path}.")
            continue
        if hashlib.sha256(raw).hexdigest() != expected_digest or line_count != expected_lines:
            failures.append(f"Frozen legacy file receipt drifted: {relative_path}.")
    return failures


def legacy_parity_failures(checker: ModuleType) -> list[str]:
    try:
        main_source = inspect.getsource(checker.main)
        demo_source = inspect.getsource(checker.check_demo_docs)
        calls = _called_checks(main_source)
        markers = _demo_markers(demo_source)
    except (OSError, TypeError, SyntaxError, IndentationError):
        return ["Frozen Phase 1 checker parity evidence is unavailable."]
    failures = frozen_file_failures()
    if hashlib.sha256(main_source.encode()).hexdigest() != LEGACY_MAIN_SOURCE_SHA256:
        failures.append("Frozen Phase 1 checker source digest drifted.")
    if hashlib.sha256(demo_source.encode()).hexdigest() != LEGACY_DEMO_SOURCE_SHA256:
        failures.append("Frozen Phase 1 demo source digest drifted.")
    if calls != LEGACY_MAIN_CHECKS:
        failures.append("Frozen Phase 1 checker call order drifted.")
    if markers != DEMO_MARKERS:
        failures.append("Frozen Phase 1 demo marker contract drifted.")
    return failures


def check_active_demo_docs(checker: LegacyReader, failures: list[str]) -> None:
    combined = "\n".join(checker.read(path) for path in DEMO_DOCUMENTS)
    for marker in DEMO_MARKERS:
        if marker not in combined:
            failures.append(f"Phase 1 demo docs missing marker: {marker}")


def _print_result(failures: list[str]) -> int:
    return print_result(
        header="Phase 1 Closure quality failures:",
        success="Phase 1 Closure governance quality checks passed.",
        failures=failures,
    )


def run_preserved_contracts() -> int:
    checker = _load_checker()
    failures = legacy_parity_failures(checker)
    if failures:
        return _print_result(failures)
    branch = current_branch()
    if not branch:
        return _print_result(["Phase 1 branch evidence is unavailable or inconsistent."])
    checker.check_branch(failures)
    checker.check_required_files(failures)
    if branch != ISSUE_324_BRANCH:
        checker.check_changed_files(failures)
    if not failures:
        for name in PRESERVED_CHECKS:
            if name == "check_active_demo_docs":
                check_active_demo_docs(checker, failures)
            else:
                getattr(checker, name)(failures)
    return _print_result(failures)
