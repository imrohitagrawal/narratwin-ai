#!/usr/bin/env python3
"""Executable Phase 1 Closure artifact gate for NarraTwin AI."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PHASE1_BRANCH = re.compile(r"^phase-1-closure-.+")

REQUIRED_INPUT_FILES = {
    "docs/reviews/FINAL_REVIEW.md",
    "docs/reviews/RISK_REGISTER.md",
    "docs/reviews/DEFECT_BACKLOG.md",
    "docs/reviews/GO_NO_GO.md",
}

REQUIRED_PHASE1_FILES = {
    "docs/reviews/PHASE_1_CLOSURE_REPORT.md",
    "docs/RELEASE_READINESS_REVIEW.md",
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/RISK_REGISTER.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/reviews/PROCESS_HARDENING_FINDINGS.md",
    "docs/evals/phase1_golden_questions.jsonl",
    "docs/demo/PHASE_1_DEMO_SCRIPT.md",
    "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
    "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
    "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
}

MODULE_A_ALLOWED_CHANGED_FILES = REQUIRED_PHASE1_FILES | {
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/workflows/quality-gates.yml",
    "AGENTS.md",
    "Makefile",
    "README.md",
    "docs/PRD.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/ENGINEERING_PROCESS_RCA.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/RUNBOOK.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    "portfolio/README.md",
    "scripts/ci/verify_branch_protection.py",
    "scripts/quality/check_phase1_closure_docs.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
}
PROCESS_ONLY_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    "scripts/guardrails_check.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_EXECUTION_STRATEGY_ALLOWED_CHANGED_FILES = {
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_72_ALLOWED_CHANGED_FILES = PROCESS_ONLY_ALLOWED_CHANGED_FILES | {
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md",
}
ISSUE_37_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    "backend/app/main.py",
    "docs/ADR/0007-local-principal-contract.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_MODEL.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/THREAT_MODEL.md",
    "tests/api/test_stage4_slice_api.py",
}
ISSUE_42_ALLOWED_CHANGED_FILES = {
    "backend/app/main.py",
    "backend/app/stage7.py",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/API_CONTRACT.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/PHASE_1_CLOSURE_REPORT.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/api/test_stage7_avatar_api.py",
    "tests/unit/test_stage7_avatar.py",
}
ISSUE_39_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    ".env.example",
    "backend/app/main.py",
    "backend/app/rag/store.py",
    "backend/app/stage4.py",
    "backend/app/stage6.py",
    "backend/app/stage7.py",
    "backend/app/storage/__init__.py",
    "backend/app/storage/file_state.py",
    "docs/ADR/0008-postgresql-durability-schema-boundary.md",
    "docs/API_CONTRACT.md",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/LOCAL_DEVELOPMENT.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/PROJECT_LEARNINGS_TRACKER.md",
    "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "docs/RISK_REGISTER.md",
    "docs/reviews/RISK_REGISTER.md",
    "docs/SKILLS_AND_CODEX_SETUP.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "scripts/guardrails_check.py",
    "tests/api/test_health_api.py",
    "tests/unit/test_branch_protection_verifier.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
    "tests/unit/test_local_durability.py",
}
ISSUE_39_CONTEXT0_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    ".github/workflows/quality.yml",
    ".github/workflows/security.yml",
    "docs/PROJECT_LEARNINGS_TRACKER.md",
    "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "docs/SKILLS_AND_CODEX_SETUP.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "scripts/guardrails_check.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT1_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0008-postgresql-durability-schema-boundary.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT2_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT3_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0010-context3-migrations-rollback-compatibility.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT4_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0011-context4-backup-restore-drill.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT5_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0012-context5-metrics-slos-watch.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT6_ALLOWED_CHANGED_FILES = {
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}

EXPECTED_ISSUE_PRIORITIES = {
    "#35": "P0",
    "#36": "P0",
    "#37": "P1",
    "#38": "P1",
    "#39": "P1",
    "#40": "P0",
    "#41": "P0",
    "#42": "P1",
    "#43": "P2",
    "#44": "P2",
}
EXPECTED_MODULES = {
    "Module A",
    "Module B",
    "Module C",
    "Module D",
    "Module E",
    "Module F",
    "Module G",
}
METRIC_FLOORS = {
    "faithfulnessMin": 0.85,
    "answerRelevancyMin": 0.80,
    "contextPrecisionMin": 0.75,
    "contextRecallMin": 0.70,
}
REQUIRED_GOLDEN_QUESTIONS = {
    "What is this project?",
    "Who is the audience?",
    "What problem does it solve?",
    "What are Mode 1 and Mode 2?",
    "What data sources does it use?",
    "What should the system not claim?",
    "What are the current limitations?",
    "What is the demo flow?",
}
GOLDEN_KEYS = {
    "id",
    "fixtureType",
    "question",
    "expectedAnswer",
    "expectedEvidence",
    "requiredClaims",
    "forbiddenClaims",
    "expectedCitationPolicy",
    "metrics",
    "unsupportedClaimsMax",
}

REQUIRED_PR_TEMPLATE_SECTIONS = (
    "Preflight evidence",
    "Human-only review surfaces",
    "Pre-implementation evidence",
    "Validation evidence",
)

REQUIRED_PR_PREFLIGHT_TABLE_HEADERS = (
    "Evidence",
    "Artifact reference",
    "Matrix IDs",
    "Command / CI / Source",
    "Reviewer",
    "Evidence type",
    "Completion status",
    "Residual risk decision",
)

REQUIRED_PR_HUMAN_ONLY_TABLE_HEADERS = (
    "Surface",
    "Automation gap",
    "Owner",
    "Evidence",
    "Residual risk decision",
    "Expiry / revisit trigger",
)

REQUIRED_PHASE1_VALIDATION_COMMANDS = (
    "uv run pytest tests/unit/test_guardrails_check.py",
    "uv run pytest tests/unit/test_phase1_closure_docs.py",
    "python3 scripts/guardrails_check.py",
    "make quality",
    "uv run ruff check scripts tests",
    "uv run mypy scripts tests",
    "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1",
)

OPTIONAL_PHASE1_VALIDATION_COMMANDS = (
    "uv run pytest tests/unit/test_branch_protection_verifier.py",
)
REQUIRED_MEDIUM_LOW_PHF_ITEMS = {
    "PHF-007",
    "PHF-008",
    "PHF-009",
    "PHF-010",
    "PHF-011",
    "PHF-012",
    "PHF-013",
}
AUTOMATED_EVIDENCE_TEST = re.compile(r"(?<!/)\btest_[A-Za-z0-9_]+\b(?!\.py)")
AUTOMATED_EVIDENCE_SCRIPT = re.compile(r"\bscripts/[A-Za-z0-9_./-]+\.py\b")
AUTOMATED_EVIDENCE_COMMAND = re.compile(
    r"\b(?:make quality|python3 scripts/guardrails_check\.py|uv run pytest [^`|\n]+)"
)
PHF_CLOSED_STATUSES = {"closed by local edits", "superseded by local edits"}
REQUIRED_ISSUE_39_MATRIX_IDS = {
    "DUR-ACID-001",
    "DUR-IDEMP-001",
    "DUR-STAGE4-001",
    "DUR-LEASE-001",
    "DUR-OUTBOX-001",
    "DUR-STAGE6-001",
    "DUR-STAGE7-001",
    "DUR-MIG-001",
    "DUR-ROLLBACK-001",
    "DUR-RESTORE-001",
    "OPS-METRICS-001",
    "OPS-SLO-001",
    "OPS-ALERT-001",
    "OPS-WATCH-001",
    "OPS-ROLLBACK-001",
    "MEDIA-CONSENT-001",
    "MEDIA-REVOKE-001",
    "MEDIA-PROVENANCE-001",
    "MEDIA-DISCLOSURE-001",
    "PROVIDER-POSTURE-001",
    "SEC-RETENTION-001",
    "SEC-UNTRUSTED-001",
    "GOV-SCOPE-001",
}
VALID_ISSUE_39_MATRIX_STATUSES = {"open", "closed"}
REPOSITORY_FULL_NAME = "imrohitagrawal/narratwin-ai"
EXPECTED_ISSUE_39_CHUNK_MATRIX_IDS = {
    "CH-00": {"GOV-SCOPE-001"},
    "CH-01": {"DUR-MIG-001"},
    "CH-02": {"DUR-ACID-001"},
    "CH-03": {"DUR-STAGE4-001"},
    "CH-04": {"DUR-IDEMP-001"},
    "CH-05": {"DUR-LEASE-001"},
    "CH-06": {"DUR-OUTBOX-001"},
    "CH-07": {"DUR-STAGE6-001"},
    "CH-08": {"DUR-STAGE7-001"},
    "CH-09": {"DUR-ROLLBACK-001"},
    "CH-10": {"OPS-METRICS-001"},
    "CH-11": {"OPS-SLO-001"},
    "CH-12": {"OPS-ALERT-001"},
    "CH-13": {"OPS-WATCH-001"},
    "CH-14": {"DUR-RESTORE-001"},
    "CH-15": {"OPS-ROLLBACK-001"},
    "CH-16": {"MEDIA-CONSENT-001"},
    "CH-17": {"MEDIA-REVOKE-001"},
    "CH-18": {"MEDIA-PROVENANCE-001"},
    "CH-19": {"MEDIA-DISCLOSURE-001"},
    "CH-20": {"PROVIDER-POSTURE-001"},
    "CH-21": {"SEC-RETENTION-001"},
    "CH-22": {"SEC-UNTRUSTED-001"},
    "CH-23": REQUIRED_ISSUE_39_MATRIX_IDS,
}
EXPECTED_ISSUE_39_CHUNK_DEPENDENCIES = {
    "CH-00": set(),
    "CH-01": {"CH-00"},
    "CH-02": {"CH-01"},
    "CH-03": {"CH-02", "CH-04", "CH-06"},
    "CH-04": {"CH-02"},
    "CH-05": {"CH-02"},
    "CH-06": {"CH-02"},
    "CH-07": {"CH-03", "CH-04"},
    "CH-08": {"CH-03", "CH-04", "CH-16"},
    "CH-09": {"CH-01", "CH-02", "CH-03"},
    "CH-10": {"CH-04", "CH-05", "CH-06"},
    "CH-11": {"CH-10"},
    "CH-12": {"CH-10", "CH-11"},
    "CH-13": {"CH-12"},
    "CH-14": {"CH-01", "CH-02", "CH-10"},
    "CH-15": {"CH-09", "CH-12", "CH-13"},
    "CH-16": {"CH-02"},
    "CH-17": {"CH-16"},
    "CH-18": {"CH-08", "CH-16"},
    "CH-19": {"CH-18"},
    "CH-20": {"CH-18"},
    "CH-21": {"CH-02", "CH-14", "CH-16", "CH-18"},
    "CH-22": {"CH-03", "CH-07", "CH-08", "CH-21"},
    "CH-23": {f"CH-{index:02d}" for index in range(23)},
}
ISSUE_39_SENSITIVE_ROW_REQUIRED_TERMS = {
    "MEDIA-CONSENT-001": (
        "actor",
        "timestamp",
        "consent text/version",
        "artifact refs",
        "source-run",
        "scope",
        "audit retention",
    ),
    "MEDIA-REVOKE-001": ("retain", "block replay", "takedown", "communication paths"),
    "MEDIA-PROVENANCE-001": (
        "source run",
        "consent record",
        "artifact checksum",
        "identity/likeness denial",
    ),
    "MEDIA-DISCLOSURE-001": ("disclosure versioning", "validation", "artifacts"),
    "PROVIDER-POSTURE-001": (
        "legal/license",
        "mock/local",
        "no real keys in local/dev/test/ci",
        "deny-by-default egress",
        "key isolation",
        "no secret logging",
        "prompt inclusion",
        "rollback disablement",
        "explicit production enablement",
    ),
    "SEC-RETENTION-001": (
        "encryption",
        "redaction",
        "retention",
        "deletion/erasure",
        "backup expiry",
        "restore re-delete",
        "access control",
        "replay/export blocking",
    ),
    "SEC-UNTRUSTED-001": (
        "uploaded docs",
        "prompts",
        "transcripts",
        "provider outputs",
        "model outputs",
        "restored artifacts",
        "exported media metadata",
        "replayed provenance",
        "validation",
        "output encoding",
        "log redaction",
        "prompt-injection/poisoned-retrieval",
        "restore-time revalidation",
        "replay/export safety",
    ),
}
ISSUE_39_OPERATIONAL_CLOSURE_EVIDENCE_TERMS = {
    "DUR-MIG-001": (("migration",), ("dry run", "execution log", "migration log")),
    "DUR-ROLLBACK-001": (("rollback",), ("compatibility", "forward repair")),
    "DUR-RESTORE-001": (("restore drill",), ("rto",), ("rpo",)),
    "OPS-METRICS-001": (("metric",), ("dashboard", "query")),
    "OPS-SLO-001": (("slo",), ("threshold", "error budget")),
    "OPS-ALERT-001": (("alert",), ("route", "routing")),
    "OPS-WATCH-001": (("watch log",), ("120",), ("180",)),
    "OPS-ROLLBACK-001": (("rollback comms", "rollback communication"),),
    "MEDIA-CONSENT-001": (("consent",), ("actor",), ("scope",), ("audit",)),
    "MEDIA-REVOKE-001": (("revocation",), ("block replay",), ("takedown",)),
    "MEDIA-PROVENANCE-001": (("provenance",), ("source run",), ("checksum",)),
    "MEDIA-DISCLOSURE-001": (("disclosure",), ("version",), ("export", "artifact")),
    "PROVIDER-POSTURE-001": (
        ("provider",),
        ("legal/license",),
        ("egress",),
        ("key",),
        ("explicit production enablement",),
    ),
    "SEC-RETENTION-001": (("retention",), ("deletion", "erasure"), ("redaction",), ("restore re-delete",)),
    "SEC-UNTRUSTED-001": (("untrusted",), ("validation",), ("output encoding",), ("log redaction",)),
}


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=False, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def current_branch() -> str:
    return os.environ.get("GITHUB_HEAD_REF", "").strip() or run_git(["branch", "--show-current"])


def resolve_base() -> str:
    preferred = os.environ.get("GITHUB_BASE_SHA", "").strip()
    if preferred and not re.fullmatch(r"0+", preferred):
        verified = run_git(["rev-parse", "--verify", f"{preferred}^{{commit}}"])
        if verified:
            return preferred
    for candidate in ("origin/main", "main"):
        merge_base = run_git(["merge-base", candidate, "HEAD"])
        if merge_base:
            return merge_base
    return "HEAD~1"


def changed_files() -> list[str]:
    base = resolve_base()
    outputs: list[str] = []
    for args in (
        ["diff", "--name-only", base, "HEAD"],
        ["diff", "--name-only", "HEAD"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        output = run_git(args)
        outputs.append(output)
    return sorted(
        {line.strip() for output in outputs for line in output.splitlines() if line.strip()}
    )


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def known_test_names() -> set[str]:
    return {test_name for test_names in known_tests_by_path().values() for test_name in test_names}


def known_tests_by_path() -> dict[str, set[str]]:
    tests_by_path: dict[str, set[str]] = {}
    test_root = ROOT / "tests"
    for path in test_root.rglob("*.py"):
        relative_path = path.relative_to(ROOT).as_posix()
        tests_by_path[relative_path] = set(
            re.findall(
                r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(",
                path.read_text(encoding="utf-8"),
                flags=re.M,
            )
        )
    return tests_by_path


def pytest_target_paths(text: str) -> set[str]:
    paths, _, _ = pytest_targets_invalid_targets_and_node_ids(text)
    return paths


def pytest_targets_invalid_targets_and_node_ids(text: str) -> tuple[set[str], set[str], set[tuple[str, str, str]]]:
    paths: set[str] = set()
    invalid_targets: set[str] = set()
    node_ids: set[tuple[str, str, str]] = set()
    for command_match in re.finditer(r"\buv run pytest (?P<targets>[^`|\n]+)", text):
        target_text = command_match.group("targets").split("->", maxsplit=1)[0]
        target_text = target_text.split("#", maxsplit=1)[0]
        for token in target_text.split():
            cleaned = token.strip("` ,;:")
            if not cleaned or cleaned.startswith("-"):
                continue
            target_path, separator, node_part = cleaned.partition("::")
            if target_path.startswith("./"):
                target_path = target_path[2:]
            if target_path.endswith(".py") or target_path.startswith("tests/"):
                paths.add(target_path)
                if separator:
                    node_match = re.search(r"\b(test_[A-Za-z0-9_]+)\b", node_part)
                    if node_match:
                        node_ids.add((target_path, node_match.group(1), f"{target_path}::{node_match.group(1)}"))
                    else:
                        invalid_targets.add(cleaned)
            else:
                invalid_targets.add(cleaned)
    return paths, invalid_targets, node_ids


def phf_automated_evidence_failures(item: str, automated: str) -> list[str]:
    failures: list[str] = []
    cited_tests = set(AUTOMATED_EVIDENCE_TEST.findall(automated))
    for test_name in sorted(cited_tests - known_test_names()):
        failures.append(f"{item} Medium/Low matrix cites unknown test evidence: {test_name}")

    cited_scripts = {match.strip("`") for match in AUTOMATED_EVIDENCE_SCRIPT.findall(automated)}
    for script_path in sorted(path for path in cited_scripts if not (ROOT / path).is_file()):
        failures.append(f"{item} Medium/Low matrix cites missing script evidence: {script_path}")

    target_paths, invalid_targets, node_ids = pytest_targets_invalid_targets_and_node_ids(automated)
    for target_path in sorted(path for path in target_paths if not (ROOT / path).is_file()):
        failures.append(f"{item} Medium/Low matrix cites missing pytest target: {target_path}")
    for target in sorted(invalid_targets):
        failures.append(f"{item} Medium/Low matrix cites unsupported pytest target: {target}")
    tests_by_path = known_tests_by_path()
    for target_path, test_name, node_id in sorted(node_ids):
        if (ROOT / target_path).is_file() and test_name not in tests_by_path.get(target_path, set()):
            failures.append(f"{item} Medium/Low matrix cites pytest node id with test outside target: {node_id}")

    has_automated_evidence = bool(
        cited_tests or cited_scripts or AUTOMATED_EVIDENCE_COMMAND.search(automated)
    )
    if not has_automated_evidence:
        failures.append(f"{item} Medium/Low matrix must map to an automated test/guardrail or human-only surface.")
    return failures


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def table_rows(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def section(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group("body") if match else ""


def has_heading(text: str, heading: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(heading)}\s*$", text, flags=re.M))


def parse_table_lines(section_text: str) -> tuple[list[str], list[list[str]]]:
    lines = section_text.splitlines()
    headers: list[str] = []
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if headers and rows:
                break
            continue
        if "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if not headers:
            headers = cells
            continue
        rows.append(cells)
    return headers, rows


def yaml_inline_list_contains_token(value: str, token: str) -> bool:
    if "[" not in value or "]" not in value:
        return False
    start = value.find("[")
    end = value.rfind("]")
    if end <= start:
        return False
    list_body = value[start + 1 : end]
    for item in list_body.split(","):
        if item.strip().strip("\"'").lower() == token:
            return True
    return False


def workflow_has_pull_request_edited(yaml_text: str) -> bool:
    lines = yaml_text.splitlines()
    for index, line in enumerate(lines):
        on_match = re.match(r"^(?P<indent>\s*)on:\s*$", line)
        if not on_match or on_match.group("indent"):
            continue
        on_indent = 0
        i = index + 1
        direct_child_indent: int | None = None
        while i < len(lines):
            current = lines[i]
            if not current.strip() or current.lstrip().startswith("#"):
                i += 1
                continue
            current_indent = len(current) - len(current.lstrip(" "))
            if current_indent <= on_indent:
                break
            if direct_child_indent is None:
                direct_child_indent = current_indent
            if current_indent != direct_child_indent:
                i += 1
                continue
            pull_match = re.match(r"^(?P<indent>\s*)pull_request:\s*$", current)
            if not pull_match:
                i += 1
                continue
            pull_indent = len(pull_match.group("indent"))
            i += 1
            pull_child_indent: int | None = None
            while i < len(lines):
                current = lines[i]
                if not current.strip() or current.lstrip().startswith("#"):
                    i += 1
                    continue
                indent = len(current) - len(current.lstrip(" "))
                if indent <= pull_indent:
                    break
                if pull_child_indent is None:
                    pull_child_indent = indent
                if indent != pull_child_indent:
                    i += 1
                    continue
                types_match = re.match(r"^(?P<indent>\s*)types:\s*(?P<value>.*)$", current)
                if not types_match:
                    i += 1
                    continue
                types_indent = len(types_match.group("indent"))
                value = types_match.group("value").strip()
                if value:
                    if yaml_inline_list_contains_token(value, "edited"):
                        return True
                    i += 1
                    continue
                i += 1
                while i < len(lines):
                    item = lines[i]
                    if not item.strip() or item.lstrip().startswith("#"):
                        i += 1
                        continue
                    item_indent = len(item) - len(item.lstrip(" "))
                    if item_indent <= types_indent:
                        break
                    item_value_match = re.match(r"^\s*-\s*(?P<value>[A-Za-z0-9_-]+)\s*$", item)
                    if item_value_match and item_value_match.group("value").lower() == "edited":
                        return True
                    i += 1
                continue
            continue

    return False


def guardrail_workflow_paths() -> list[str]:
    workflow_dir = ROOT / ".github" / "workflows"
    paths = sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])
    return [
        path.relative_to(ROOT).as_posix()
        for path in paths
        if "scripts/guardrails_check.py" in read(path.relative_to(ROOT).as_posix())
    ]


def workflow_has_guardrail_github_token_wiring(yaml_text: str) -> bool:
    guardrail_steps = workflow_guardrail_step_blocks(yaml_text)
    if not guardrail_steps:
        return False
    return (
        "issues: read" in yaml_text
        and "pull-requests: read" in yaml_text
        and all(
            "GITHUB_TOKEN:" in step and ("github.token" in step or "secrets.GITHUB_TOKEN" in step)
            for step in guardrail_steps
        )
    )


def workflow_guardrail_step_blocks(yaml_text: str) -> list[str]:
    lines = yaml_text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        step_match = re.match(r"^(?P<indent>\s*)-\s+name:\s+.*$", line)
        if not step_match:
            index += 1
            continue
        step_indent = len(step_match.group("indent"))
        block_lines = [line]
        index += 1
        while index < len(lines):
            current = lines[index]
            if current.strip() and not current.lstrip().startswith("#"):
                current_indent = len(current) - len(current.lstrip(" "))
                if current_indent <= step_indent:
                    break
            block_lines.append(current)
            index += 1
        block = "\n".join(block_lines)
        if "scripts/guardrails_check.py" in block:
            blocks.append(block)
    return blocks


def check_required_headings(failures: list[str], text: str, owner: str, headings: tuple[str, ...]) -> None:
    for heading in headings:
        if not has_heading(text, heading):
            failures.append(f"{owner} missing required heading: {heading}")


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def section_contains_required_commands(section_text: str, required: tuple[str, ...]) -> list[str]:
    normalized = section_text.lower()
    return [command for command in required if command.lower() not in normalized]


def check_preflight_table_columns(
    failures: list[str], *, section_name: str, section_text: str, required_headers: tuple[str, ...]
) -> None:
    headers, _ = parse_table_lines(section_text)
    if not headers:
        failures.append(f"{section_name} section in .github/pull_request_template.md is missing a table header row.")
        return
    normalized_headers = {normalize_header(header) for header in headers}
    missing = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing:
        failures.append(
            f"{section_name} table in .github/pull_request_template.md is missing headers: {', '.join(missing)}"
        )


def check_matrix_template_rows(
    failures: list[str],
    *,
    section_name: str,
    section_text: str,
    required_keyword_groups: tuple[tuple[str, ...], ...],
) -> None:
    headers, rows = parse_table_lines(section_text)
    normalized_headers = [normalize_header(header) for header in headers]
    required_headers = (
        "id",
        "area",
        "invariant",
        "old failure / false-pass risk",
        "positive test",
        "negative / mutation test",
        "status",
    )
    missing_headers = [header for header in required_headers if header not in normalized_headers]
    if missing_headers:
        failures.append(f"{section_name} matrix template missing headers: {', '.join(missing_headers)}")
        return

    index_by_header = {header: normalized_headers.index(header) for header in required_headers}
    seen_ids: set[str] = set()
    for row in rows:
        if len(row) < len(headers):
            failures.append(f"{section_name} matrix row has too few columns: {row}")
            continue
        row_id = row[index_by_header["id"]].strip("` ")
        positive_test = row[index_by_header["positive test"]].strip()
        negative_test = row[index_by_header["negative / mutation test"]].strip()
        status = row[index_by_header["status"]].strip("` ").lower()
        row_text = " ".join(row).lower()
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}", row_id):
            failures.append(f"{section_name} matrix row has non-concrete ID: {row_id}")
        if row_id in seen_ids:
            failures.append(f"{section_name} matrix row duplicates ID: {row_id}")
        seen_ids.add(row_id)
        if status != "pass":
            failures.append(f"{section_name} matrix row {row_id} must use status pass, not {status or '<empty>'}.")
        if re.search(r"\b(?:through|thru|to)\b|\.{2,}|[–—]", row_id, flags=re.I):
            failures.append(f"{section_name} matrix row {row_id} uses range or placeholder ID syntax.")
        if row_id.startswith("HUMAN-"):
            continue
        if "test_" not in positive_test.lower() and "make test" not in positive_test.lower():
            failures.append(f"{section_name} matrix row {row_id} must name positive test evidence.")
        if "test_" not in negative_test.lower() and "make test" not in negative_test.lower():
            failures.append(f"{section_name} matrix row {row_id} must name negative test evidence.")
        if "test_" not in row_text and "make test" not in row_text:
            failures.append(f"{section_name} matrix row {row_id} must name test evidence.")
        if not any(
            term in row_text
            for term in ("break-test", "mutation", "old behavior failed", "old-behavior proof", "fails-before")
        ):
            failures.append(f"{section_name} matrix row {row_id} must name old-behavior or mutation proof.")

    for keywords in required_keyword_groups:
        if not any(all(keyword in " ".join(row).lower() for keyword in keywords) for row in rows):
            failures.append(
                f"{section_name} matrix template missing one row with required binding terms: {', '.join(keywords)}"
            )


def check_process_hardening_findings(failures: list[str], text: str) -> None:
    remaining_headers, remaining_rows = parse_table_lines(section(text, "Medium/Low PHF Follow-up Matrix (Remaining)"))
    required_remaining_headers = (
        "item",
        "risk",
        "failure mode",
        "prior review evidence",
        "owning doc / script / template",
        "automated test / guardrail",
        "human-only surface (if not automatable)",
        "residual risk",
    )
    normalized_remaining_headers = [normalize_header(header) for header in remaining_headers]
    missing_remaining_headers = [
        header for header in required_remaining_headers if header not in normalized_remaining_headers
    ]
    if missing_remaining_headers:
        failures.append(
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md Medium/Low matrix missing headers: "
            + ", ".join(missing_remaining_headers)
        )
        return

    remaining_index = {header: normalized_remaining_headers.index(header) for header in required_remaining_headers}
    seen_remaining: set[str] = set()
    for row in remaining_rows:
        if len(row) < len(remaining_headers):
            failures.append(f"PHF Medium/Low matrix row has too few columns: {row}")
            continue
        item = row[remaining_index["item"]].strip("` ")
        seen_remaining.add(item)
        automated = row[remaining_index["automated test / guardrail"]]
        human_only = row[remaining_index["human-only surface (if not automatable)"]]
        residual = row[remaining_index["residual risk"]]
        for field_name, value in (
            ("failure mode", row[remaining_index["failure mode"]]),
            ("prior review evidence", row[remaining_index["prior review evidence"]]),
            ("owning doc / script / template", row[remaining_index["owning doc / script / template"]]),
            ("automated test / guardrail", automated),
            ("residual risk", residual),
        ):
            if value.strip().lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"{item} Medium/Low matrix has placeholder {field_name}.")
        if human_only.strip().lower() in {"", "todo", "tbd", "pending"}:
            failures.append(f"{item} Medium/Low matrix has placeholder human-only surface.")
        human_only_is_na = human_only.strip().lower() in {"n/a", "na"}
        evidence_failures = phf_automated_evidence_failures(item, automated)
        if human_only_is_na:
            failures.extend(evidence_failures)
        else:
            failures.extend(
                failure
                for failure in evidence_failures
                if "must map to an automated test/guardrail or human-only surface" not in failure
            )

    missing_remaining = sorted(REQUIRED_MEDIUM_LOW_PHF_ITEMS - seen_remaining)
    if missing_remaining:
        failures.append("Medium/Low PHF matrix missing items: " + ", ".join(missing_remaining))

    register_headers, register_rows = parse_table_lines(section(text, "Findings Register"))
    normalized_register_headers = [normalize_header(header) for header in register_headers]
    required_register_headers = ("id", "severity", "status", "acceptance criteria")
    missing_register_headers = [
        header for header in required_register_headers if header not in normalized_register_headers
    ]
    if missing_register_headers:
        failures.append(
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md Findings Register missing headers: "
            + ", ".join(missing_register_headers)
        )
        return
    register_index = {header: normalized_register_headers.index(header) for header in required_register_headers}
    seen_register: set[str] = set()
    for row in register_rows:
        if len(row) < len(register_headers):
            failures.append(f"PHF findings register row has too few columns: {row}")
            continue
        item = row[register_index["id"]].strip("` ")
        if item in seen_register:
            failures.append(f"PHF findings register duplicates item: {item}")
        seen_register.add(item)
        if item in REQUIRED_MEDIUM_LOW_PHF_ITEMS:
            status = row[register_index["status"]].strip().lower()
            acceptance = row[register_index["acceptance criteria"]].strip()
            if status not in PHF_CLOSED_STATUSES:
                failures.append(f"{item} must be closed or superseded in the findings register; got {status}.")
            if acceptance.lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"{item} findings register has placeholder acceptance criteria.")


def check_issue39_closure_plan(failures: list[str]) -> None:
    rel = "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
    path = ROOT / rel
    if not path.is_file():
        failures.append(f"Missing required issue #39 production closure plan: {rel}")
        return

    headers, rows = parse_table_lines(section(read(rel), "Master Evidence Matrix"))
    required_headers = ("ID", "Requirement", "Evidence target", "Owner", "Minimum evidence contract", "Status")
    normalized_headers = [normalize_header(header) for header in headers]
    missing_headers = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing_headers:
        failures.append(
            "Issue #39 production closure plan Master Evidence Matrix missing headers: "
            + ", ".join(missing_headers)
        )
        return

    seen_ids: set[str] = set()
    closed_ids: set[str] = set()
    for row in rows:
        if len(row) != len(headers):
            failures.append(f"Issue #39 matrix row must have 6 columns: {row}")
            continue
        row_id = row[normalized_headers.index("id")].strip("` ")
        status = row[normalized_headers.index("status")].strip("` ")
        if row_id in seen_ids:
            failures.append(f"Issue #39 production closure plan duplicates matrix ID: {row_id}")
        seen_ids.add(row_id)
        if not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}", row_id):
            failures.append(f"Issue #39 matrix row has invalid ID: {row_id}")
        if status.lower() not in VALID_ISSUE_39_MATRIX_STATUSES:
            failures.append(f"Issue #39 matrix row {row_id} status must be Open or Closed; got {status}.")
        if status.lower() == "closed":
            closed_ids.add(row_id)
        for value in row[1:5]:
            if value.strip().lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"Issue #39 matrix row {row_id} has placeholder evidence contract content.")
                break
        required_terms = ISSUE_39_SENSITIVE_ROW_REQUIRED_TERMS.get(row_id, ())
        row_contract = " ".join(row[1:5]).lower()
        missing_terms = [term for term in required_terms if term.lower() not in row_contract]
        if missing_terms:
            failures.append(
                f"Issue #39 matrix row {row_id} missing required contract terms: "
                + ", ".join(missing_terms)
            )

    missing_ids = sorted(REQUIRED_ISSUE_39_MATRIX_IDS - seen_ids)
    if missing_ids:
        failures.append("Issue #39 production closure plan missing matrix IDs: " + ", ".join(missing_ids))

    unexpected_ids = sorted(seen_ids - REQUIRED_ISSUE_39_MATRIX_IDS)
    if unexpected_ids:
        failures.append("Issue #39 production closure plan has unexpected matrix IDs: " + ", ".join(unexpected_ids))

    if closed_ids:
        check_issue39_closed_row_records(failures, read(rel), closed_ids)


def check_issue39_closed_row_records(failures: list[str], text: str, closed_ids: set[str]) -> None:
    headers, rows = parse_table_lines(section(text, "Row Closure Records"))
    normalized_headers = [normalize_header(header) for header in headers]
    required_headers = (
        "Matrix ID",
        "Child issue / PR",
        "Artifact reference",
        "Validation or human evidence",
        "Owner",
        "Reviewer",
        "Residual-risk decision",
        "Timestamp / merge commit",
        "Satisfies row because",
    )
    missing_headers = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing_headers:
        failures.append("Issue #39 Row Closure Records missing headers: " + ", ".join(missing_headers))
        return

    index = {header: normalized_headers.index(normalize_header(header)) for header in required_headers}
    records_by_id: dict[str, list[str]] = {}
    for row in rows:
        if len(row) != len(headers):
            failures.append(f"Issue #39 row closure record has wrong column count: {row}")
            continue
        row_id = row[index["Matrix ID"]].strip("` ")
        records_by_id[row_id] = row

    for row_id in sorted(closed_ids):
        record = records_by_id.get(row_id)
        if not record:
            failures.append(f"Issue #39 matrix row {row_id} is Closed without a row closure record.")
            continue
        for header in required_headers[1:]:
            value = record[index[header]].strip()
            if value.lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"Issue #39 closed row {row_id} has placeholder {header}.")
        child_reference = record[index["Child issue / PR"]]
        issue_numbers = same_repo_issue_numbers(child_reference)
        pr_numbers = same_repo_pr_numbers(child_reference)
        if not issue_numbers or not pr_numbers:
            failures.append(
                f"Issue #39 closed row {row_id} must cite concrete same-repository child issue and PR URLs."
            )
        if "39" in issue_numbers:
            failures.append(f"Issue #39 closed row {row_id} must cite a child issue distinct from #39.")
        if "64" in pr_numbers:
            failures.append(f"Issue #39 closed row {row_id} must not use Context 0 PR #64 as final proof.")
        artifact = record[index["Artifact reference"]].lower()
        evidence = record[index["Validation or human evidence"]].lower()
        reason = record[index["Satisfies row because"]].lower()
        combined_evidence = " ".join((artifact, evidence, reason))
        if "docs/reviews/issue_39_production_closure_plan.md" in artifact and not any(
            token in combined_evidence for token in ("test_", "actions/runs/", "drill log", "human-only")
        ):
            failures.append(
                f"Issue #39 closed row {row_id} must not use the production closure plan alone as final proof."
            )
        if not has_concrete_issue39_closure_evidence(
            evidence=evidence,
            owner=record[index["Owner"]],
            residual_risk=record[index["Residual-risk decision"]],
        ):
            failures.append(f"Issue #39 closed row {row_id} lacks concrete validation or human-only evidence.")
        missing_groups = missing_issue39_operational_evidence_terms(row_id, combined_evidence)
        if missing_groups:
            failures.append(
                f"Issue #39 closed row {row_id} missing operational closure evidence terms: "
                + "; ".join(" or ".join(group) for group in missing_groups)
            )


def same_repo_issue_numbers(text: str) -> set[str]:
    return set(
        re.findall(
            rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/issues/(\d+)\b",
            text,
            flags=re.I,
        )
    )


def same_repo_pr_numbers(text: str) -> set[str]:
    return set(
        re.findall(
            rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/pull/(\d+)\b",
            text,
            flags=re.I,
        )
    )


def has_concrete_issue39_closure_evidence(*, evidence: str, owner: str, residual_risk: str) -> bool:
    cited_tests = set(re.findall(r"\btest_[A-Za-z0-9_]+\b", evidence))
    if cited_tests:
        return cited_tests <= known_test_names()
    if re.search(rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/actions/runs/\d+", evidence):
        return True
    if re.search(
        rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/(?:blob|tree)/[A-Za-z0-9_./-]+",
        evidence,
    ):
        return True
    if re.search(rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/actions/runs/\d+/artifacts/\d+", evidence):
        return True
    if re.search(r"\b(?:docs|reports|artifacts|logs)/[A-Za-z0-9_./-]+", evidence) and "drill log" in evidence:
        return True
    if "human-only" in evidence and owner.strip() and residual_risk.strip().lower() not in {
        "",
        "n/a",
        "na",
        "todo",
        "tbd",
        "pending",
    }:
        return True
    return False


def missing_issue39_operational_evidence_terms(row_id: str, evidence: str) -> list[tuple[str, ...]]:
    required_groups = ISSUE_39_OPERATIONAL_CLOSURE_EVIDENCE_TERMS.get(row_id, ())
    return [group for group in required_groups if not any(term in evidence for term in group)]


def check_issue39_execution_strategy(failures: list[str]) -> None:
    rel = "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md"
    path = ROOT / rel
    if not path.is_file():
        failures.append(f"Missing required issue #39 execution strategy: {rel}")
        return

    text = read(rel)
    check_required_headings(
        failures,
        text,
        rel,
        (
            "Objective",
            "Tracking Contract",
            "Chunk Definition Of Done",
            "Execution State Machine",
            "Parallelization Model",
            "Agent Review Protocol",
            "Re-Review After Fixes",
            "Chunk Work Plan",
            "Deployment Transition Plan",
            "Stop Rules And Handoffs",
        ),
    )

    required_markers = (
        "Refs #39",
        "reference-only",
        "pre-code",
        "positive invariants",
        "negative invariants",
        "false-pass",
        "RED tests",
        "adversarial-review",
        "re-review",
        "GOV-SCOPE-001",
        "DUR-ACID-001",
        "OPS-WATCH-001",
        "SEC-UNTRUSTED-001",
        "No-Go",
        "Go",
        "phase-1-closure-39-",
    )
    missing_markers = [marker for marker in required_markers if marker not in text]
    if missing_markers:
        failures.append(
            "Issue #39 execution strategy missing required markers: "
            + ", ".join(missing_markers)
        )

    if re.search(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#39\b", text, flags=re.I):
        failures.append("Issue #39 execution strategy must not use auto-closing #39 wording.")

    check_issue39_strategy_required_terms(failures, text)

    headers, rows = parse_table_lines(section(text, "Chunk Work Plan"))
    required_headers = (
        "Chunk",
        "Matrix IDs",
        "Dependencies",
        "Parallel group",
        "Required planning artifact",
        "Required review agents",
        "Done when",
    )
    normalized_headers = [normalize_header(header) for header in headers]
    missing_headers = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing_headers:
        failures.append("Issue #39 execution strategy Chunk Work Plan missing headers: " + ", ".join(missing_headers))
        return

    matrix_index = normalized_headers.index("matrix ids")
    chunk_index = normalized_headers.index("chunk")
    dependencies_index = normalized_headers.index("dependencies")
    parallel_index = normalized_headers.index("parallel group")
    planning_index = normalized_headers.index("required planning artifact")
    review_index = normalized_headers.index("required review agents")
    done_index = normalized_headers.index("done when")

    seen_ids: set[str] = set()
    chunks_by_id: dict[str, set[str]] = {}
    dependencies_by_chunk: dict[str, set[str]] = {}
    for row in rows:
        if len(row) != len(headers):
            failures.append(f"Issue #39 execution strategy chunk row has wrong column count: {row}")
            continue
        chunk = row[chunk_index].strip("` ")
        chunk_match = re.match(r"^(CH-\d{2})\b", chunk)
        if not chunk_match:
            failures.append(f"Issue #39 execution strategy chunk has invalid chunk label: {chunk}")
            continue
        chunk_id = chunk_match.group(1)
        if chunk_id in chunks_by_id:
            failures.append(f"Issue #39 execution strategy duplicates chunk: {chunk_id}")
        matrix_ids = set(re.findall(r"[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}", row[matrix_index]))
        if not matrix_ids:
            failures.append(f"Issue #39 execution strategy chunk {chunk} has no matrix IDs.")
        chunks_by_id[chunk_id] = matrix_ids
        dependencies_by_chunk[chunk_id] = set(re.findall(r"CH-\d{2}", row[dependencies_index]))
        seen_ids.update(matrix_ids)
        for index, label in (
            (dependencies_index, "Dependencies"),
            (parallel_index, "Parallel group"),
            (planning_index, "Required planning artifact"),
            (review_index, "Required review agents"),
            (done_index, "Done when"),
        ):
            if row[index].strip().lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"Issue #39 execution strategy chunk {chunk} has placeholder {label}.")

    missing_ids = sorted(REQUIRED_ISSUE_39_MATRIX_IDS - seen_ids)
    if missing_ids:
        failures.append("Issue #39 execution strategy missing matrix IDs: " + ", ".join(missing_ids))

    unexpected_ids = sorted(seen_ids - REQUIRED_ISSUE_39_MATRIX_IDS)
    if unexpected_ids:
        failures.append("Issue #39 execution strategy has unexpected matrix IDs: " + ", ".join(unexpected_ids))

    expected_chunks = set(EXPECTED_ISSUE_39_CHUNK_MATRIX_IDS)
    actual_chunks = set(chunks_by_id)
    missing_chunks = sorted(expected_chunks - actual_chunks)
    if missing_chunks:
        failures.append("Issue #39 execution strategy missing chunks: " + ", ".join(missing_chunks))
    unexpected_chunks = sorted(actual_chunks - expected_chunks)
    if unexpected_chunks:
        failures.append("Issue #39 execution strategy has unexpected chunks: " + ", ".join(unexpected_chunks))

    for chunk_id, expected_ids in EXPECTED_ISSUE_39_CHUNK_MATRIX_IDS.items():
        if chunk_id not in chunks_by_id:
            continue
        actual_ids = chunks_by_id[chunk_id]
        if actual_ids != expected_ids:
            failures.append(
                f"Issue #39 execution strategy chunk {chunk_id} matrix IDs must be "
                f"{', '.join(sorted(expected_ids))}; got {', '.join(sorted(actual_ids))}."
            )

    for chunk_id, dependencies in dependencies_by_chunk.items():
        unknown = sorted(dependencies - actual_chunks)
        if unknown:
            failures.append(
                f"Issue #39 execution strategy chunk {chunk_id} depends on unknown chunks: "
                + ", ".join(unknown)
            )
    for chunk_id, expected_dependencies in EXPECTED_ISSUE_39_CHUNK_DEPENDENCIES.items():
        if chunk_id not in dependencies_by_chunk:
            continue
        actual_dependencies = dependencies_by_chunk[chunk_id]
        if actual_dependencies != expected_dependencies:
            failures.append(
                f"Issue #39 execution strategy chunk {chunk_id} dependencies must be "
                f"{', '.join(sorted(expected_dependencies)) or 'None'}; got "
                f"{', '.join(sorted(actual_dependencies)) or 'None'}."
            )
    cycle = issue39_chunk_dependency_cycle(dependencies_by_chunk)
    if cycle:
        failures.append("Issue #39 execution strategy has dependency cycle: " + " -> ".join(cycle))


def check_issue39_strategy_required_terms(failures: list[str], text: str) -> None:
    required_by_section = {
        "Chunk Definition Of Done": (
            "pre-code plan exists before implementation",
            "source facts",
            "non-goals",
            "positive invariants",
            "negative invariants",
            "failure or false-pass",
            "test mapping",
            "RED tests",
            "executable negative tests",
            "documented human-only evidence surface",
            "implementation and tests",
            "recorded disposition",
            "fixed",
            "rejected with evidence",
            "non-goal with rationale",
            "human-only follow-up",
            "re-reviewed by a fresh reviewer",
        ),
        "Deployment Transition Plan": (
            "Production deployment remains blocked",
            "Staging/pre-production transition",
            "make quality",
            "make ci",
            "make security",
            "make dependency-audit",
            "make container-scan",
            "make secrets-scan",
            "make eval",
            "migration dry run",
            "backup/restore drill evidence",
            "dashboard, alert, and watch evidence",
            "docs/reviews/GO_NO_GO.md",
            "docs/RELEASE_CHECKLIST.md",
            "health",
            "readiness",
            "metrics",
            "alerts",
            "rollback probes",
            "Failed production transition probes halt before enablement",
            "watch or SLO threshold",
            "rollback communications",
        ),
    }
    for heading, terms in required_by_section.items():
        section_text = section(text, heading).lower()
        missing_terms = [term for term in terms if term.lower() not in section_text]
        if missing_terms:
            failures.append(
                f"docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md {heading} missing required terms: "
                + ", ".join(missing_terms)
            )
    headers, rows = parse_table_lines(section(text, "Chunk Work Plan"))
    normalized_headers = [normalize_header(header) for header in headers]
    if "chunk" not in normalized_headers or "done when" not in normalized_headers:
        return
    chunk_index = normalized_headers.index("chunk")
    done_index = normalized_headers.index("done when")
    for row in rows:
        if len(row) != len(headers):
            continue
        chunk = row[chunk_index]
        if "`CH-10`" not in chunk:
            continue
        done_when = row[done_index].lower()
        required_ch10_terms = (
            "metric catalog",
            "shared instrumentation contracts",
            "restore and rollback metric emissions close with `ch-14` and `ch-15`",
        )
        missing_ch10_terms = [term for term in required_ch10_terms if term not in done_when]
        if missing_ch10_terms:
            failures.append(
                "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md CH-10 row missing required terms: "
                + ", ".join(missing_ch10_terms)
            )


def issue39_chunk_dependency_cycle(dependencies_by_chunk: dict[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(chunk_id: str) -> list[str]:
        if chunk_id in visiting:
            start = stack.index(chunk_id)
            return [*stack[start:], chunk_id]
        if chunk_id in visited:
            return []
        visiting.add(chunk_id)
        stack.append(chunk_id)
        for dependency in sorted(dependencies_by_chunk.get(chunk_id, set())):
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(chunk_id)
        visited.add(chunk_id)
        return []

    for chunk_id in sorted(dependencies_by_chunk):
        cycle = visit(chunk_id)
        if cycle:
            return cycle
    return []


def issues_from_cell(value: str) -> set[str]:
    return set(re.findall(r"#\d+", value))


def check_branch(failures: list[str]) -> None:
    branch = current_branch()
    if not branch:
        fail(failures, "Phase 1 Closure gate could not resolve the current branch; failing closed.")
    elif branch != "main" and not PHASE1_BRANCH.match(branch):
        fail(failures, f"Phase 1 Closure work must run on phase-1-closure-* or main; got {branch}.")


def check_required_files(failures: list[str]) -> None:
    for rel in sorted(REQUIRED_INPUT_FILES | REQUIRED_PHASE1_FILES):
        if not (ROOT / rel).is_file():
            fail(failures, f"Missing required Phase 1 Closure file: {rel}")


def check_changed_files(failures: list[str]) -> None:
    branch = current_branch()
    if branch.startswith("phase-1-closure-process-72-"):
        allowed_files = ISSUE_72_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-process-"):
        allowed_files = PROCESS_ONLY_ALLOWED_CHANGED_FILES
    elif branch == "phase-1-closure-39-execution-strategy":
        allowed_files = ISSUE_39_EXECUTION_STRATEGY_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-37-"):
        allowed_files = ISSUE_37_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context0-"):
        allowed_files = ISSUE_39_CONTEXT0_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context1-"):
        allowed_files = ISSUE_39_CONTEXT1_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context2-"):
        allowed_files = ISSUE_39_CONTEXT2_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context3-"):
        allowed_files = ISSUE_39_CONTEXT3_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context4-"):
        allowed_files = ISSUE_39_CONTEXT4_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context5-"):
        allowed_files = ISSUE_39_CONTEXT5_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context6-"):
        allowed_files = ISSUE_39_CONTEXT6_ALLOWED_CHANGED_FILES
    elif branch == "phase-1-closure-39-durability-monitoring":
        allowed_files = ISSUE_39_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-"):
        allowed_files = ISSUE_39_EXECUTION_STRATEGY_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-42-"):
        allowed_files = ISSUE_42_ALLOWED_CHANGED_FILES
    else:
        allowed_files = MODULE_A_ALLOWED_CHANGED_FILES
    for rel in changed_files():
        if rel not in allowed_files:
            fail(failures, f"Phase 1 Closure branch {branch} may not change {rel}.")


def check_final_review_baseline(failures: list[str]) -> None:
    text = read("docs/reviews/GO_NO_GO.md")
    required_lines = (
        "No-Go for production release.",
        "No-Go for multi-worker deployment.",
        "No-Go for external paid/provider-backed generation.",
        "No-Go for real video export.",
        "No-Go for public synthetic-media distribution.",
    )
    for line in required_lines:
        if line not in text:
            fail(failures, f"GO_NO_GO.md must preserve Final Review baseline line: {line}")
    if "issues `#35` through `#44`" not in text:
        fail(failures, "GO_NO_GO.md must continue to reference issues #35 through #44.")


def check_closure_report(failures: list[str]) -> None:
    text = read("docs/reviews/PHASE_1_CLOSURE_REPORT.md")
    if "No release tag has been created" not in text:
        fail(failures, "Phase 1 closure report must state that no release tag has been created.")
    if "No Final Review follow-up is currently classified as P3" not in text:
        fail(failures, "Phase 1 closure report must explicitly state the current P3 posture.")

    reconciliation = table_rows(section(text, "Finding-To-Issue Reconciliation"))
    issue_rows = [row for row in reconciliation if row and re.fullmatch(r"`#\d+`", row[0])]
    seen: dict[str, list[str]] = {}
    for row in issue_rows:
        if len(row) != 4:
            fail(failures, f"Finding row must have 4 columns: {row}")
            continue
        issue = row[0].strip("`")
        priority = row[1]
        module = row[2].split(":", maxsplit=1)[0]
        disposition = row[3]
        seen[issue] = row
        expected_priority = EXPECTED_ISSUE_PRIORITIES.get(issue)
        if expected_priority is None:
            fail(failures, f"Unexpected Phase 1 issue in reconciliation table: {issue}")
        elif priority != expected_priority:
            fail(failures, f"{issue} priority must be {expected_priority}; got {priority}.")
        if priority not in {"P0", "P1", "P2", "P3"}:
            fail(failures, f"{issue} priority must be one of P0/P1/P2/P3.")
        if priority in {"P0", "P1"} and module not in EXPECTED_MODULES:
            fail(failures, f"{issue} must map to a valid closure module; got {module}.")
        if not disposition:
            fail(failures, f"{issue} must include a Phase 1 disposition.")

    missing_issues = sorted(set(EXPECTED_ISSUE_PRIORITIES) - set(seen))
    if missing_issues:
        fail(failures, f"Finding reconciliation missing issues: {', '.join(missing_issues)}")
    duplicate_count = len([row[0].strip("`") for row in issue_rows])
    if duplicate_count != len(seen):
        fail(failures, "Finding reconciliation contains duplicate issue rows.")

    module_rows = table_rows(section(text, "Closure Modules"))
    modules: dict[str, list[str]] = {}
    covered_issues: set[str] = set()
    for row in module_rows:
        if len(row) != 4 or not row[0].startswith("Module "):
            continue
        module, _scope, issue_cell, evidence = row
        modules[module] = row
        covered_issues.update(issues_from_cell(issue_cell))
        if module not in EXPECTED_MODULES:
            fail(failures, f"Unexpected closure module row: {module}")
        if not evidence or evidence.lower() == "none":
            fail(failures, f"{module} must include required evidence.")

    missing_modules = sorted(EXPECTED_MODULES - set(modules))
    if missing_modules:
        fail(failures, f"Closure module table missing modules: {', '.join(missing_modules)}")

    required_coverage = {
        issue for issue, priority in EXPECTED_ISSUE_PRIORITIES.items() if priority in {"P0", "P1"}
    }
    missing_coverage = sorted(required_coverage - covered_issues)
    if missing_coverage:
        fail(
            failures,
            f"Closure module table does not cover P0/P1 issues: {', '.join(missing_coverage)}",
        )


def check_golden_questions(failures: list[str]) -> None:
    path = ROOT / "docs/evals/phase1_golden_questions.jsonl"
    questions: set[str] = set()
    ids: set[str] = set()
    fixture_types: set[str] = set()

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(failures, f"Golden question line {index} is invalid JSON: {exc}")
            continue

        unknown = set(row) - GOLDEN_KEYS
        missing = GOLDEN_KEYS - set(row)
        if unknown:
            fail(
                failures,
                f"Golden question line {index} has unknown keys: {', '.join(sorted(unknown))}",
            )
        if missing:
            fail(
                failures,
                f"Golden question line {index} missing keys: {', '.join(sorted(missing))}",
            )

        row_id = row.get("id")
        if not isinstance(row_id, str) or not re.fullmatch(r"phase1-q\d{3}", row_id):
            fail(failures, f"Golden question line {index} id must match phase1-qNNN.")
        elif row_id in ids:
            fail(failures, f"Golden question id is duplicated: {row_id}")
        else:
            ids.add(row_id)

        question = row.get("question")
        if not isinstance(question, str) or not question:
            fail(failures, f"Golden question line {index} must include a non-empty question.")
        else:
            questions.add(question)

        fixture_type = row.get("fixtureType")
        if not isinstance(fixture_type, str) or not fixture_type:
            fail(failures, f"Golden question line {index} must include fixtureType.")
        else:
            fixture_types.add(fixture_type)

        for key in ("expectedAnswer", "expectedCitationPolicy"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                fail(failures, f"Golden question line {index} must include non-empty {key}.")
        for key in ("expectedEvidence", "requiredClaims", "forbiddenClaims"):
            value = row.get(key)
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(item, str) and item for item in value)
            ):
                fail(
                    failures,
                    f"Golden question line {index} must include a non-empty string list for {key}.",
                )
        for evidence in row.get("expectedEvidence", []):
            if isinstance(evidence, str) and not (ROOT / evidence).exists():
                fail(
                    failures,
                    f"Golden question line {index} references missing evidence path: {evidence}",
                )

        metrics = row.get("metrics")
        if not isinstance(metrics, dict):
            fail(failures, f"Golden question line {index} must include metrics object.")
        else:
            for metric, floor in METRIC_FLOORS.items():
                value = metrics.get(metric)
                if not isinstance(value, (int, float)) or value < floor:
                    fail(failures, f"Golden question line {index} {metric} must be >= {floor}.")
        if row.get("unsupportedClaimsMax") != 0:
            fail(failures, f"Golden question line {index} must require unsupportedClaimsMax = 0.")

    missing_questions = sorted(REQUIRED_GOLDEN_QUESTIONS - questions)
    if missing_questions:
        fail(failures, f"Golden question set missing questions: {', '.join(missing_questions)}")
    if "prompt_injection_refusal" not in fixture_types:
        fail(failures, "Golden question set must include a prompt_injection_refusal fixture.")
    if "safety_boundary" not in fixture_types:
        fail(failures, "Golden question set must include a safety_boundary fixture.")


def check_demo_docs(failures: list[str]) -> None:
    script = read("docs/demo/PHASE_1_DEMO_SCRIPT.md")
    checklist = read("docs/demo/PHASE_1_DEMO_CHECKLIST.md")
    screenshot = read("docs/demo/PHASE_1_SCREENSHOT_GUIDE.md")
    portfolio = read("portfolio/README.md")
    combined = "\n".join((script, checklist, screenshot, portfolio))
    for marker in (
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
    ):
        if marker not in combined:
            fail(failures, f"Phase 1 demo docs missing marker: {marker}")


def check_release_docs(failures: list[str]) -> None:
    files = {
        "docs/RELEASE_READINESS_REVIEW.md": read("docs/RELEASE_READINESS_REVIEW.md"),
        "docs/RELEASE_CHECKLIST.md": read("docs/RELEASE_CHECKLIST.md"),
        "docs/RUNBOOK.md": read("docs/RUNBOOK.md"),
        "docs/STATUS.md": read("docs/STATUS.md"),
        "docs/RISK_REGISTER.md": read("docs/RISK_REGISTER.md"),
        "docs/THIRD_PARTY_NOTICES.md": read("docs/THIRD_PARTY_NOTICES.md"),
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": read(
            "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md"
        ),
    }
    expected_by_file = {
        "docs/RELEASE_READINESS_REVIEW.md": (
            "No-Go",
            "PR `#45`",
            "issues `#35` through `#44`",
            "No tag is permitted",
            "downgraded with evidence",
        ),
        "docs/RELEASE_CHECKLIST.md": ("Phase 1", "make ci", "make security", "make eval"),
        "docs/RUNBOOK.md": ("make phase1-closure-quality", "make ci", "docker compose up --build"),
        "docs/STATUS.md": ("Phase 1 Closure", "PR `#45`", "`#35`"),
        "docs/RISK_REGISTER.md": ("Final Review Risk Register", "Phase 1 Closure"),
        "docs/THIRD_PARTY_NOTICES.md": (
            "Phase 1 golden-question dataset",
            "docs/evals/phase1_golden_questions.jsonl",
        ),
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": (
            "Canonical issue: `#1`",
            "Reconciliation issue: `#40`",
        ),
    }
    for rel, markers in expected_by_file.items():
        for marker in markers:
            if marker not in files[rel]:
                fail(failures, f"{rel} missing marker: {marker}")
    check_issue39_status_ledger(failures, files["docs/STATUS.md"], read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"))


def check_issue39_status_ledger(failures: list[str], status_text: str, closure_plan_text: str) -> None:
    issue39_row = next(
        (line for line in status_text.splitlines() if line.startswith("| `#39` |")),
        "",
    )
    if not issue39_row:
        failures.append("docs/STATUS.md missing issue #39 ledger row.")
        return
    cells = [cell.strip() for cell in issue39_row.strip("|").split("|")]
    if len(cells) < 2:
        failures.append("docs/STATUS.md issue #39 ledger row is malformed.")
        return
    status = cells[1].lower()
    if not issue39_all_matrix_rows_closed(closure_plan_text) and "open" not in status:
        failures.append("docs/STATUS.md issue #39 must remain Open while production closure matrix rows are Open.")


def issue39_all_matrix_rows_closed(closure_plan_text: str) -> bool:
    headers, rows = parse_table_lines(section(closure_plan_text, "Master Evidence Matrix"))
    normalized_headers = [normalize_header(header) for header in headers]
    if "id" not in normalized_headers or "status" not in normalized_headers:
        return False
    id_index = normalized_headers.index("id")
    status_index = normalized_headers.index("status")
    statuses = {
        row[id_index].strip("` "): row[status_index].strip("` ").lower()
        for row in rows
        if len(row) == len(headers)
    }
    return (
        set(statuses) == REQUIRED_ISSUE_39_MATRIX_IDS
        and all(status == "closed" for status in statuses.values())
    )


def check_process_docs(failures: list[str]) -> None:
    required_files = (
        ".github/CODEOWNERS",
        ".github/pull_request_template.md",
        "AGENTS.md",
        "docs/ENGINEERING_PROCESS_RCA.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    )
    for rel in required_files:
        if not (ROOT / rel).is_file():
            fail(failures, f"Missing required process artifact: {rel}")

    pr_template = read(".github/pull_request_template.md")
    changed = set(changed_files())
    check_required_headings(
        failures,
        pr_template,
        ".github/pull_request_template.md",
        REQUIRED_PR_TEMPLATE_SECTIONS,
    )
    check_preflight_table_columns(
        failures,
        section_name=".github/pull_request_template.md preflight evidence table",
        section_text=section(pr_template, "Preflight evidence"),
        required_headers=REQUIRED_PR_PREFLIGHT_TABLE_HEADERS,
    )
    check_preflight_table_columns(
        failures,
        section_name=".github/pull_request_template.md human-only review table",
        section_text=section(pr_template, "Human-only review surfaces"),
        required_headers=REQUIRED_PR_HUMAN_ONLY_TABLE_HEADERS,
    )
    if "tests/unit/test_branch_protection_verifier.py" in changed:
        missing_optional_validation = section_contains_required_commands(
            section(pr_template, "Validation evidence"), OPTIONAL_PHASE1_VALIDATION_COMMANDS
        )
        if missing_optional_validation:
            fail(
                failures,
                "Validation evidence section in .github/pull_request_template.md should include optional command "
                f"{OPTIONAL_PHASE1_VALIDATION_COMMANDS[0]} when branch-protection verifier evidence is relevant.",
            )
    missing_required_validation = section_contains_required_commands(
        section(pr_template, "Validation evidence"), REQUIRED_PHASE1_VALIDATION_COMMANDS
    )
    if missing_required_validation:
        fail(
            failures,
            ".github/pull_request_template.md Validation evidence section missing required commands: "
            + ", ".join(missing_required_validation),
        )

    agents = read("AGENTS.md")
    for marker in (
        "docs/ENGINEERING_PROCESS_RCA.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "preflight evidence",
    ):
        if marker not in agents:
            fail(failures, f"AGENTS.md missing process marker: {marker}")

    codeowners = read(".github/CODEOWNERS")
    for marker in (
        ".github/workflows/",
        "scripts/guardrails_check.py",
        "scripts/ci/verify_branch_protection.py",
        "scripts/quality/",
        "tests/unit/test_guardrails_check.py",
        "docs/ENGINEERING_PROCESS_RCA.md",
    ):
        if marker not in codeowners:
            fail(failures, f".github/CODEOWNERS missing process marker: {marker}")

    for workflow_path in guardrail_workflow_paths():
        workflow_text = read(workflow_path)
        if not workflow_has_pull_request_edited(workflow_text):
            fail(failures, f"{workflow_path} must rerun guardrails on pull_request.edited")
        if not workflow_has_guardrail_github_token_wiring(workflow_text):
            fail(
                failures,
                f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails",
            )

    rca = read("docs/ENGINEERING_PROCESS_RCA.md")
    check_required_headings(
        failures,
        rca,
        "docs/ENGINEERING_PROCESS_RCA.md",
        (
            "Durability Restore Invariant Checklist",
            "Governance / CI / False-Pass",
            "Invariant-To-Test Matrix Template",
            "Bad Partial Fixes Versus Complete Coverage",
            "Mandatory Rule For Future Durability And Process PRs",
            "Required Future Workflow For NarraTwin",
        ),
    )
    check_preflight_table_columns(
        failures,
        section_name="docs/ENGINEERING_PROCESS_RCA.md matrix template",
        section_text=section(rca, "Invariant-To-Test Matrix Template"),
        required_headers=("ID", "Area", "Invariant"),
    )
    check_matrix_template_rows(
        failures,
        section_name="docs/ENGINEERING_PROCESS_RCA.md",
        section_text=section(rca, "Invariant-To-Test Matrix Template"),
        required_keyword_groups=(
            ("source run", "retrieved context", "evaluation", "citation", "claim-support"),
            ("canonical-stage", "issue-closing", "final squash"),
        ),
    )

    playbook = read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    check_required_headings(
        failures,
        playbook,
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        (
            "Durability / Restore / Replay Checklist",
            "Derived Artifact Consistency Checklist",
            "Governance / CI / False-Pass Checklist",
            "Human-Only Review Surfaces",
            "Invariant-to-Test Matrix Template",
            "Definition of Done for Process-Sensitive Work",
            "RCA Pause Artifact",
            "Stop Rules",
            "Definition Of Done",
        ),
    )
    check_preflight_table_columns(
        failures,
        section_name="docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md matrix template",
        section_text=section(playbook, "Invariant-to-Test Matrix Template"),
        required_headers=("ID", "Area", "Invariant"),
    )
    check_matrix_template_rows(
        failures,
        section_name="docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        section_text=section(playbook, "Invariant-to-Test Matrix Template"),
        required_keyword_groups=(
            ("source run", "retrieved context", "evaluation", "citation", "claim-support"),
            ("concrete artifacts", "matrix-id coverage", "old-behavior proof"),
        ),
    )

    check_process_hardening_findings(
        failures,
        read("docs/reviews/PROCESS_HARDENING_FINDINGS.md"),
    )


def main() -> int:
    failures: list[str] = []
    check_branch(failures)
    check_required_files(failures)
    check_changed_files(failures)
    if not failures:
        check_final_review_baseline(failures)
        check_closure_report(failures)
        check_golden_questions(failures)
        check_demo_docs(failures)
        check_release_docs(failures)
        check_issue39_closure_plan(failures)
        check_issue39_execution_strategy(failures)
        check_process_docs(failures)

    if failures:
        print("Phase 1 Closure quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Phase 1 Closure governance quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
