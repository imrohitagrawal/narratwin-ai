#!/usr/bin/env python3
"""Repository guardrails for NarraTwin AI.

This script intentionally uses only the Python standard library so CI can run
without paid providers, real API keys, or project-specific dependencies.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import NamedTuple
from urllib.parse import urlparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".chroma",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "outputs",
    ".next",
    ".venv",
    "venv",
}

TEXT_SUFFIXES = {
    ".adoc",
    ".cer",
    ".crt",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".key",
    ".md",
    ".mjs",
    ".p12",
    ".pem",
    ".pfx",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

PRIVATE_KEY_CERT_SUFFIXES = {".pem", ".key", ".crt", ".cer", ".p12", ".pfx"}

SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("openai key", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
    ("anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openrouter key", re.compile(r"sk-or-v1-[A-Za-z0-9_\-]{20,}")),
    ("github token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("google api key", re.compile(r"AIza[0-9A-Za-z_\-]{20,}")),
    ("aws access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("jwt-like token", re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}")),
    ("bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}")),
    (
        "secret assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|credential)\b\s*[:=]\s*['\"]?([^'\"\s#]{8,})['\"]?"
        ),
    ),
]

PROVIDER_KEY_NAMES = {
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "HEYGEN_API_KEY",
    "TAVUS_API_KEY",
    "DID_API_KEY",
    "ELEVENLABS_API_KEY",
}

ARCHITECTURE_IMPACT_PREFIXES = (
    "src/",
    "app/",
    "backend/",
    "frontend/",
    "infra/",
    "terraform/",
    "docker/",
    "docs/ARCHITECTURE.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_MODEL.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/THREAT_MODEL.md",
)

PRD_IMPACT_PREFIXES = (
    "src/",
    "app/",
    "backend/",
    "frontend/",
    "docs/PRD.md",
    "docs/PRODUCT_STRATEGY.md",
    "docs/ROADMAP.md",
)

STATUS_IMPACT_PREFIXES = (
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/workflows/",
    ".stage/current",
    "AGENTS.md",
    "Makefile",
    "docs/ADR/",
    "docs/AI_BUILD_BRIEF.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/DATA_MODEL.md",
    "docs/ENGINEERING_PROCESS_RCA.md",
    "docs/METHODOLOGY.md",
    "docs/NORTH_STAR_METRICS.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/PRD.md",
    "docs/PRD_RED_TEAM_REVIEW.md",
    "docs/PRODUCT_STRATEGY.md",
    "docs/PROJECT_AVATAR_PACK.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/RELEASE_QUALITY_BAR.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/ROADMAP.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md",
    "docs/templates/",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/THREAT_MODEL.md",
    "docs/TRACEABILITY.md",
    "scripts/guardrails_check.py",
    "scripts/ci/verify_branch_protection.py",
    "scripts/quality/",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
)

CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"}

failures: list[str] = []
warnings: list[str] = []

REQUIRED_PREFLIGHT_EVIDENCE = {
    "intent/spec",
    "source facts",
    "failure matrix",
    "tests",
    "docs/gates",
    "adversarial review",
}

OLD_BEHAVIOR_PROOF_TERMS = {
    "break-test",
    "fails before",
    "failing test",
    "mutation",
    "old behavior fails",
    "red confirmed",
    "regression reproduced",
}

COMPLETED_PREFLIGHT_STATUSES = {"pass", "passed"}
PREFLIGHT_EMPTY_MARKERS = {"", "n/a", "na", "todo", "tbd", "pending"}
MATRIX_COVERAGE_EVIDENCE_TYPES = {"test", "gate", "source", "human-only", "non-goal"}
PLACEHOLDER_URL_HOSTS = {"example.com", "localhost", "127.0.0.1", "0.0.0.0"}  # nosec B104
PLACEHOLDER_URL_TERMS = {"todo", "tbd", "placeholder", "example", "invalid"}
LOCAL_REFERENCE_TYPES = {"repo-file"}
URL_REFERENCE_TYPES = {"url", "source-url", "source", "pr-comment", "ci-run"}
ALLOWED_REFERENCE_TYPES = LOCAL_REFERENCE_TYPES | URL_REFERENCE_TYPES
CANONICAL_STAGE_ISSUE_CLOSURE = (
    ("stage2-", "Stage 2", "2"),
    ("stage3-", "Stage 3", "5"),
    ("stage4-", "Stage 4", "4"),
    ("stage5-", "Stage 5", "10"),
    ("stage6-", "Stage 6", "11"),
    ("stage7-", "Stage 7", "12"),
    ("stage8-", "Stage 8", "13"),
)
FORCE_PULL_REQUEST_GUARDRAILS_ENV = "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS"
REQUIRED_PREIMPLEMENTATION_ROWS = {
    "invariant/failure matrix",
    "source facts",
    "human-only surfaces, if any",
}
REQUIRED_PR_VALIDATION_COMMANDS = (
    "uv run pytest tests/unit/test_guardrails_check.py",
    "uv run pytest tests/unit/test_phase1_closure_docs.py",
    "python3 scripts/guardrails_check.py",
    "make quality",
    "uv run ruff check scripts tests",
    "uv run mypy scripts tests",
    "GITHUB_EVENT_NAME=pull_request GITHUB_EVENT_PATH=",
)
VALIDATION_PASS_RESULT = re.compile(r"(?:->|:)\s*(?:(?:[1-9]\d*)\s+)?(?:passed|success|succeeded|green)\b")
VALIDATION_ZERO_PASS_RESULT = re.compile(r"(?<!\d)0+\s+passed\b")
VALIDATION_FAILURE_TERMS = (
    "example only",
    "failed",
    "failure",
    "not-run",
    "not run",
    "red",
    "todo",
    "tbd",
    "pending",
    "required local",
    "unsuccessful",
    "/path/to/",
)
FORCED_PR_VALIDATION_COMMAND = re.compile(
    r"^github_event_name=pull_request "
    r"github_event_path=(?P<event_path>\S+) "
    r"narratwin_force_pull_request_guardrails=1 "
    r"python3 scripts/guardrails_check\.py(?P<tail>(?:\s|:|$).*)$"
)


class PreflightEvidenceRow(NamedTuple):
    evidence_name: str
    artifact: str
    reference_type: str
    matrix_ids: str
    command: str
    reviewer: str
    evidence_type: str
    status: str
    residual: str
    raw_cells: tuple[str, ...]


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return ""


def git_command_succeeds(args: list[str]) -> bool:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def is_zero_sha(value: str) -> bool:
    return bool(value) and set(value) == {"0"}


def resolve_diff_base(head: str, preferred_base: str) -> str:
    if preferred_base and not is_zero_sha(preferred_base):
        verified = run_git(["rev-parse", "--verify", f"{preferred_base}^{{commit}}"])
        if verified:
            merge_base = run_git(["merge-base", preferred_base, head])
            if merge_base:
                return merge_base
    for candidate in ("origin/main", "main"):
        merge_base = run_git(["merge-base", candidate, head])
        if merge_base:
            return merge_base
    return "HEAD~1"


def changed_files() -> list[str]:
    base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    head = os.environ.get("GITHUB_HEAD_SHA", "").strip() or "HEAD"
    resolved_base = resolve_diff_base(head, base)
    output = run_git(["diff", "--name-only", resolved_base, head])
    return [line.strip() for line in output.splitlines() if line.strip()]


def closing_issue_pattern(issue_number: str = r"\d+") -> str:
    issue_ref = (
        rf"#(?:{issue_number})\b|"
        rf"[\w.-]+/[\w.-]+#(?:{issue_number})\b|"
        rf"https://github\.com/[\w.-]+/[\w.-]+/issues/(?:{issue_number})\b"
    )
    return rf"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s*(?:{issue_ref})"


def closing_issue_numbers(text: str) -> set[str]:
    issue_ref = (
        r"#(?P<short>\d+)\b|"
        r"[\w.-]+/[\w.-]+#(?P<repo>\d+)\b|"
        r"https://github\.com/[\w.-]+/[\w.-]+/issues/(?P<url>\d+)\b"
    )
    pattern = re.compile(rf"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s*(?:{issue_ref})")
    issue_numbers: set[str] = set()
    for match in pattern.finditer(text):
        issue_number = match.group("short") or match.group("repo") or match.group("url")
        if issue_number:
            issue_numbers.add(issue_number)
    return issue_numbers


def issue_link_pattern(issue_number: str = r"\d+") -> str:
    issue_ref = (
        rf"#(?:{issue_number})\b|"
        rf"[\w.-]+/[\w.-]+#(?:{issue_number})\b|"
        rf"https://github\.com/[\w.-]+/[\w.-]+/issues/(?:{issue_number})\b"
    )
    return rf"(?i)\b(refs?|references?)\b:?\s*(?:{issue_ref})"


PROCESS_CRITICAL_DOC_FILES = {
    "AGENTS.md",
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/workflows/quality-gates.yml",
    "docs/AI_BUILD_BRIEF.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/ENGINEERING_PROCESS_RCA.md",
    "docs/QUALITY_GATES.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    "docs/reviews/PROCESS_HARDENING_FINDINGS.md",
}


def is_nontrivial_pull_request(changes: list[str]) -> bool:
    if not changes:
        return False
    review_relevant_prefixes = (
        ".github/",
        "backend/",
        "frontend/",
        "scripts/",
        "tests/",
    )
    review_relevant_doc_prefixes = (
        "docs/ADR/",
        "docs/templates/",
        "docs/reviews/",
    )
    return any(
        Path(path).suffix in CODE_SUFFIXES
        or path in PROCESS_CRITICAL_DOC_FILES
        or path.startswith(review_relevant_prefixes)
        or path.startswith(review_relevant_doc_prefixes)
        or any(path.startswith(prefix) for prefix in ARCHITECTURE_IMPACT_PREFIXES + PRD_IMPACT_PREFIXES + STATUS_IMPACT_PREFIXES)
        for path in changes
    )


def should_enforce_pull_request_issue_checks() -> bool:
    if os.environ.get("GITHUB_EVENT_NAME", "") == "pull_request":
        return True
    return os.environ.get(FORCE_PULL_REQUEST_GUARDRAILS_ENV, "").strip().lower() in {"1", "true", "yes"}


def canonical_stage_issue(head_ref: str | None) -> tuple[str, str] | None:
    if not head_ref:
        return None
    for prefix, stage_name, issue_number in CANONICAL_STAGE_ISSUE_CLOSURE:
        if head_ref.startswith(prefix):
            return stage_name, issue_number
    return None


def has_completed_preflight_evidence(body: str) -> bool:
    completed_rows: dict[str, list[PreflightEvidenceRow]] = {}
    for cells in markdown_table_rows(body, "Preflight evidence"):
        row = parse_preflight_row(cells)
        if row is None:
            continue
        required = (
            row.evidence_name,
            row.artifact,
            row.reference_type,
            row.matrix_ids,
            row.command,
            row.reviewer,
            row.evidence_type,
            row.status,
            row.residual,
        )
        if any(is_placeholder_value(value) for value in required):
            continue
        if row.status.strip().lower() not in COMPLETED_PREFLIGHT_STATUSES:
            continue
        if row.evidence_name not in REQUIRED_PREFLIGHT_EVIDENCE:
            continue
        if not reference_type_matches_artifact(row.reference_type, row.artifact):
            continue
        if matrix_id_cell_uses_range_shorthand(row.matrix_ids):
            continue
        if not preflight_artifact_exists(row.artifact):
            continue
        completed_rows.setdefault(row.evidence_name, []).append(row)

    return (
        REQUIRED_PREFLIGHT_EVIDENCE.issubset(completed_rows)
        and has_invariant_test_mapping(completed_rows)
        and has_human_only_review_surfaces(body)
        and has_pre_implementation_evidence(body)
    )


def has_validation_evidence(body: str) -> bool:
    section_text = markdown_section(body, "Validation evidence")
    lines = [line.strip().lower() for line in section_text.splitlines()]
    return all(validation_command_has_result(lines, command) for command in REQUIRED_PR_VALIDATION_COMMANDS)


def validation_command_has_result(lines: list[str], command: str) -> bool:
    command_text = command.lower()
    has_valid_result = False
    for line in lines:
        if not validation_line_matches_command(line, command_text):
            continue
        if VALIDATION_ZERO_PASS_RESULT.search(line):
            return False
        if any(term in line for term in VALIDATION_FAILURE_TERMS):
            continue
        if VALIDATION_PASS_RESULT.search(line):
            has_valid_result = True
        if "github.com/" in line and "/actions/runs/" in line:
            has_valid_result = True
    return has_valid_result


def validation_line_matches_command(line: str, command_text: str) -> bool:
    if command_text.endswith("github_event_path="):
        return FORCED_PR_VALIDATION_COMMAND.match(line) is not None
    if not line.startswith(command_text):
        return False
    suffix = line[len(command_text) :]
    return not suffix or suffix[0].isspace() or suffix.startswith(":")


def markdown_table_rows(body: str, heading: str) -> list[list[str]]:
    lines = body.splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().lower() == f"## {heading.lower()}"
        ),
        None,
    )
    if start is None:
        return []
    rows: list[list[str]] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        header_names = {"evidence", "surface", "requirement"}
        if cells[0].strip().lower() in header_names:
            continue
        rows.append(cells)
    return rows


def markdown_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().lower() == f"## {heading.lower()}"
        ),
        None,
    )
    if start is None:
        return ""
    section_lines: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip().startswith("## "):
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def parse_preflight_row(cells: list[str]) -> PreflightEvidenceRow | None:
    if len(cells) >= 9:
        evidence, artifact, reference_type, matrix_ids, command, reviewer, evidence_type, status, residual = cells[:9]
    elif len(cells) >= 7:
        evidence, artifact, matrix_ids, command, reviewer, status, residual = cells[:7]
        reference_type = infer_reference_type(artifact)
        evidence_type = infer_evidence_type(evidence, command, residual)
    else:
        return None
    return PreflightEvidenceRow(
        evidence_name=normalize_preflight_evidence_name(evidence),
        artifact=artifact,
        reference_type=reference_type,
        matrix_ids=matrix_ids,
        command=command,
        reviewer=reviewer,
        evidence_type=normalize_evidence_type(evidence_type),
        status=status.strip().lower(),
        residual=residual,
        raw_cells=tuple(cells),
    )


def has_invariant_test_mapping(rows_by_evidence: dict[str, list[PreflightEvidenceRow]]) -> bool:
    matrix_rows = rows_by_evidence.get("failure matrix", [])
    test_rows = rows_by_evidence.get("tests", [])
    docs_rows = rows_by_evidence.get("docs/gates", [])
    coverage_rows = [
        row
        for evidence_name, rows in rows_by_evidence.items()
        if evidence_name != "failure matrix"
        for row in rows
        if row.evidence_type in MATRIX_COVERAGE_EVIDENCE_TYPES
    ]
    matrix_ids = {matrix_id for row in matrix_rows for matrix_id in split_matrix_ids(row.matrix_ids)}
    covered_ids = {matrix_id for row in coverage_rows for matrix_id in split_matrix_ids(row.matrix_ids)}
    executable_rows = [
        row
        for row in test_rows + docs_rows
        if row.evidence_type in {"test", "gate"}
    ]
    executable_ids = {matrix_id for row in executable_rows for matrix_id in split_matrix_ids(row.matrix_ids)}
    tested_ids = {matrix_id for row in test_rows for matrix_id in split_matrix_ids(row.matrix_ids)}
    if not matrix_ids or not tested_ids or not matrix_ids.issubset(covered_ids):
        return False
    non_executable_allowed_prefixes = ("SRC-", "HUMAN-", "NONGOAL-")
    if any(
        not matrix_id.startswith(non_executable_allowed_prefixes) and matrix_id not in executable_ids
        for matrix_id in matrix_ids
    ):
        return False
    test_evidence_text = " ".join(" | ".join(row.raw_cells).lower() for row in test_rows)
    if not any(term in test_evidence_text for term in OLD_BEHAVIOR_PROOF_TERMS):
        return False
    mapping_text = " ".join(
        " | ".join(row.raw_cells).lower() for row in matrix_rows + test_rows + docs_rows
    )
    return "invariant" in mapping_text and "test" in mapping_text


def has_human_only_review_surfaces(body: str) -> bool:
    rows = markdown_table_rows(body, "Human-only review surfaces")
    has_valid_surface = False
    has_final_merge_surface = False
    for cells in rows:
        if len(cells) < 6:
            continue
        surface, automation_gap, owner, evidence, residual, expiry = cells[:6]
        if any(is_placeholder_value(value) for value in (automation_gap, owner, evidence, residual, expiry)):
            continue
        if not preflight_artifact_exists(evidence):
            continue
        if is_na_value(surface):
            continue
        if is_placeholder_value(surface):
            continue
        has_valid_surface = True
        surface_text = f"{surface} {automation_gap}".lower()
        residual_text = residual.lower()
        if "final squash" in surface_text or "merge message" in surface_text:
            if not (
                "reference-only" in residual_text
                and (
                    "no issue-closing" in residual_text
                    or "no issue closing" in residual_text
                )
            ):
                continue
            has_final_merge_surface = True
    return has_valid_surface and has_final_merge_surface


def has_pre_implementation_evidence(body: str) -> bool:
    rows = markdown_table_rows(body, "Pre-implementation evidence")
    seen: set[str] = set()
    for cells in rows:
        if len(cells) < 5:
            continue
        requirement, artifact, timestamp_or_commit, reviewer, decision = cells[:5]
        if any(
            is_placeholder_value(value)
            for value in (requirement, artifact, timestamp_or_commit, reviewer, decision)
        ):
            continue
        requirement_name = normalize_requirement_name(requirement)
        if requirement_name not in REQUIRED_PREIMPLEMENTATION_ROWS:
            continue
        if decision.strip().lower() not in COMPLETED_PREFLIGHT_STATUSES:
            continue
        if not preflight_artifact_exists(artifact):
            continue
        if not has_concrete_preimplementation_marker(timestamp_or_commit):
            continue
        seen.add(requirement_name)
    return REQUIRED_PREIMPLEMENTATION_ROWS.issubset(seen)


def normalize_preflight_evidence_name(value: str) -> str:
    evidence_name = re.sub(r"\s+", " ", value.strip().lower())
    if evidence_name == "docs":
        return "docs/gates"
    if evidence_name.startswith("failure matrix"):
        return "failure matrix"
    if evidence_name.startswith("tests"):
        return "tests"
    return evidence_name


def normalize_evidence_type(value: str) -> str:
    evidence_type = re.sub(r"\s+", " ", value.strip().lower())
    aliases = {
        "docs": "gate",
        "docs/gates": "gate",
        "human": "human-only",
        "manual": "human-only",
        "manual review": "human-only",
        "source fact": "source",
        "source facts": "source",
        "not applicable": "non-goal",
    }
    return aliases.get(evidence_type, evidence_type)


def infer_evidence_type(evidence: str, command: str, residual: str) -> str:
    combined = f"{evidence} {command} {residual}".lower()
    if "human-only" in combined or "manual" in combined:
        return "human-only"
    evidence_name = normalize_preflight_evidence_name(evidence)
    if evidence_name == "tests":
        return "test"
    if evidence_name == "docs/gates":
        return "gate"
    if evidence_name in {"intent/spec", "source facts", "adversarial review"}:
        return "source"
    return "source"


def infer_reference_type(artifact: str) -> str:
    cleaned = clean_markdown_reference(artifact)
    if cleaned.startswith(("https://", "http://")):
        return "url"
    return "repo-file"


def normalize_reference_type(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().lower())


def reference_type_matches_artifact(reference_type: str, artifact: str) -> bool:
    normalized_type = normalize_reference_type(reference_type)
    if normalized_type not in ALLOWED_REFERENCE_TYPES:
        return False
    cleaned = clean_markdown_reference(artifact)
    is_url = cleaned.startswith(("https://", "http://"))
    if is_url:
        return normalized_type in URL_REFERENCE_TYPES
    return normalized_type in LOCAL_REFERENCE_TYPES


def split_matrix_ids(value: str) -> set[str]:
    normalized = value.strip().strip("`")
    if normalized.lower() in {"", "n/a", "na", "none", "todo", "tbd", "pending"}:
        return set()
    if matrix_id_cell_uses_range_shorthand(normalized):
        return set()
    return {
        token.strip("` ")
        for token in re.split(r"[\s,;]+", normalized)
        if re.search(r"[A-Za-z]", token) and re.search(r"\d", token)
    }


def matrix_id_cell_uses_range_shorthand(value: str) -> bool:
    normalized = value.strip().strip("`")
    if re.search(r"\b(?:through|thru|to)\b", normalized, flags=re.I):
        return True
    matrix_id = r"[A-Za-z]+(?:-[A-Za-z]+)*-\d+"
    return bool(re.search(rf"\b{matrix_id}\s*(?:\.{2,}|[-–—])\s*{matrix_id}\b", normalized))


def preflight_artifact_exists(value: str) -> bool:
    artifact = clean_markdown_reference(value)
    if artifact.startswith(("https://", "http://")):
        parsed = urlparse(artifact)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path.strip("/")
        if parsed.scheme not in {"http", "https"} or not hostname or not path:
            return False
        if hostname in PLACEHOLDER_URL_HOSTS or hostname.endswith(".example.com"):
            return False
        url_text = f"{hostname}/{path}".lower()
        if any(term in url_text for term in PLACEHOLDER_URL_TERMS):
            return False
        return True
    if not artifact or artifact.startswith(("/", "~")):
        return False
    artifact_path = strip_artifact_fragment_or_line(artifact)
    return (ROOT / artifact_path).is_file()


def clean_markdown_reference(value: str) -> str:
    artifact = value.strip().strip("`").strip()
    link_match = re.fullmatch(r"\[[^\]]+\]\(([^)]+)\)", artifact)
    if link_match:
        return link_match.group(1).strip()
    return artifact


def strip_artifact_fragment_or_line(value: str) -> str:
    without_fragment = value.split("#", maxsplit=1)[0]
    return re.sub(r":\d+$", "", without_fragment)


def is_na_value(value: str) -> bool:
    return value.strip().lower().strip("`") in {"n/a", "na"}


def is_placeholder_value(value: str) -> bool:
    normalized = value.strip().lower().strip("`")
    return normalized in PREFLIGHT_EMPTY_MARKERS


def normalize_requirement_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    if "invariant" in normalized or "failure matrix" in normalized:
        return "invariant/failure matrix"
    if "source fact" in normalized:
        return "source facts"
    if "human-only" in normalized or "human only" in normalized:
        return "human-only surfaces, if any"
    return normalized


def has_concrete_preimplementation_marker(value: str) -> bool:
    normalized = value.strip()
    comment_or_draft_match = re.search(
        r"(?:issue comment|draft pr):\s*(?P<url>https?://[^\s]+)",
        normalized,
        flags=re.I,
    )
    if comment_or_draft_match and preimplementation_url_has_concrete_shape(comment_or_draft_match.group("url")):
        return True
    commit_order_match = re.search(
        r"commit order:\s*(?P<earlier>[0-9a-f]{7,40})\s+before\s+(?P<later>[0-9a-f]{7,40})",
        normalized,
        flags=re.I,
    )
    if not commit_order_match:
        return False
    earlier = commit_order_match.group("earlier")
    later = commit_order_match.group("later")
    return (
        git_command_succeeds(["cat-file", "-e", f"{earlier}^{{commit}}"])
        and git_command_succeeds(["cat-file", "-e", f"{later}^{{commit}}"])
        and git_command_succeeds(["merge-base", "--is-ancestor", earlier, later])
    )


def preimplementation_url_has_concrete_shape(value: str) -> bool:
    if not preflight_artifact_exists(value):
        return False
    parsed = urlparse(clean_markdown_reference(value))
    path = parsed.path.strip("/")
    fragment = parsed.fragment.strip()
    if re.fullmatch(r"[^/]+/[^/]+/issues/\d+", path):
        return bool(re.fullmatch(r"issuecomment-\d+", fragment))
    if re.fullmatch(r"[^/]+/[^/]+/pull/\d+", path):
        return True
    return False


def pull_request_commit_messages() -> str:
    base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    head = os.environ.get("GITHUB_HEAD_SHA", "").strip() or "HEAD"
    resolved_base = resolve_diff_base(head, base)
    return run_git(["log", "--format=%B", f"{resolved_base}..{head}"])


def iter_text_files() -> list[Path]:
    tracked = run_git(["ls-files"])
    untracked = run_git(["ls-files", "--others", "--exclude-standard"])
    files: list[Path] = []
    for rel in sorted({line.strip() for output in (tracked, untracked) for line in output.splitlines()}):
        if not rel:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & EXCLUDED_DIRS:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", "Makefile", ".env.example"}:
            files.append(path)
    return files


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def line_for_match(text: str, match: re.Match[str]) -> str:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end]


def is_allowlisted_secret_match(path: str, text: str, match: re.Match[str]) -> bool:
    matched_text = match.group(0)
    if path.endswith(".env.example") and matched_text.endswith("="):
        return True
    if path.endswith(".env.example") and re.search(r"=\s*['\"]?\s*['\"]?$", matched_text):
        return True
    if "PLACEHOLDER" in matched_text or "example" in matched_text.lower():
        return True
    line = line_for_match(text, match)
    if path in {"scripts/guardrails_check.py", "scripts/quality/check_stage2_docs.py"}:
        if "re.compile" in line or "SECRET_PATTERNS" in line or "PROVIDER_KEY_NAMES" in line:
            return True
        if "expected_defaults" in line or "providerDefaults" in line:
            return True
    return False


def check_no_direct_main_push() -> None:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    ref = os.environ.get("GITHUB_REF_NAME", "")
    if event == "push" and ref == "main":
        failures.append("Direct push to main detected. All work must go through issue + branch + PR.")


def check_issue_linked_pull_request() -> None:
    if not should_enforce_pull_request_issue_checks():
        return
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        failures.append("Pull request event payload is unavailable; cannot verify issue linkage.")
        return
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"Could not read pull request event payload: {exc}")
        return
    pr = event.get("pull_request", {})
    title = pr.get("title") or ""
    body = pr.get("body") or ""
    head_ref = (pr.get("head") or {}).get("ref")
    base_ref = (pr.get("base") or {}).get("ref")
    if head_ref == "main":
        failures.append("Pull request head branch must not be main.")
    if base_ref != "main":
        failures.append("Pull requests for guarded work must target main.")
    stage_name, canonical_issue_number = canonical_stage_issue(head_ref) or ("", None)
    is_canonical_stage_branch = canonical_issue_number is not None
    visible_issue_text = f"{title}\n{body}\n{pull_request_commit_messages()}"
    issue_39_closing_pattern = closing_issue_pattern("39")
    if re.search(
        issue_39_closing_pattern,
        visible_issue_text,
    ):
        failures.append("Issue #39 pull requests must use reference-only wording and must not auto-close #39.")
    closed_issue_numbers = closing_issue_numbers(visible_issue_text)
    if not is_canonical_stage_branch and closed_issue_numbers:
        failures.append("Pull request title/body/commit messages must use reference-only issue wording.")
    if canonical_issue_number is not None and any(
        issue_number != canonical_issue_number for issue_number in closed_issue_numbers
    ):
        failures.append("Pull request title/body/commit messages must not close non-canonical issues.")
    changes = changed_files()
    reference_only_issue_39 = bool(
        head_ref
        and head_ref.startswith("phase-1-closure-39-")
        and re.search(r"(?i)\brefs\s+#39\b", body)
    )
    if not reference_only_issue_39 and not is_canonical_stage_branch and not re.search(issue_link_pattern(), body):
        failures.append("Pull request body must link an issue using reference-only wording such as Refs #<issue>.")
    if is_nontrivial_pull_request(changes):
        if not has_completed_preflight_evidence(body):
            failures.append("Non-trivial pull requests must include completed preflight evidence rows.")
        if not has_validation_evidence(body):
            failures.append("Non-trivial pull requests must include validation evidence commands.")
    if canonical_issue_number is not None:
        pattern = closing_issue_pattern(canonical_issue_number)
        if not re.search(pattern, body):
            failures.append(
                f"{stage_name} pull requests must close the canonical {stage_name} issue using "
                f"Closes #{canonical_issue_number}, Fixes #{canonical_issue_number}, or Resolves #{canonical_issue_number}."
            )


def check_workflows_least_privilege() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    if not workflow_dir.exists():
        failures.append("Missing .github/workflows directory. CI must be YAML-defined.")
        return
    for workflow in list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")):
        text = read_text(workflow)
        rel = relative(workflow)
        if "permissions:" not in text:
            failures.append(f"{rel} is missing explicit least-privilege permissions.")
        if re.search(r"permissions:\s*write-all", text):
            failures.append(f"{rel} uses write-all permissions. Use least privilege instead.")
        if re.search(r"contents:\s*write", text) and "pull_request" in text:
            failures.append(f"{rel} grants contents: write for PR validation. Use contents: read unless a write is required.")


def check_secrets() -> None:
    for path in iter_text_files():
        rel = relative(path)
        if path.suffix.lower() in PRIVATE_KEY_CERT_SUFFIXES:
            failures.append(f"{rel} is a key/certificate file. Private keys and certificates must not be committed.")
            continue
        text = read_text(path)
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if is_allowlisted_secret_match(rel, text, match):
                    continue
                failures.append(f"Potential {name} found in {rel}. No secrets may be committed.")


def check_provider_keys_are_env_only() -> None:
    env_example = ROOT / ".env.example"
    if not env_example.exists():
        failures.append("Missing .env.example. Provider keys must be documented as environment variables.")
        return
    env_text = read_text(env_example)
    for key in sorted(PROVIDER_KEY_NAMES):
        if key not in env_text:
            failures.append(f"Missing {key} placeholder in .env.example.")
    for path in iter_text_files():
        rel = relative(path)
        text = read_text(path)
        if rel.endswith(".env.example"):
            continue
        for key_name in PROVIDER_KEY_NAMES:
            assignment = re.compile(rf"{re.escape(key_name)}\s*=\s*['\"]?[^'\"\n#]+")
            for match in assignment.finditer(text):
                if is_allowlisted_secret_match(rel, text, match):
                    continue
                failures.append(f"{rel} appears to assign {key_name}. Provider keys must come from environment variables.")


def check_mock_local_defaults() -> None:
    env_example = ROOT / ".env.example"
    text = read_text(env_example) if env_example.exists() else ""
    expected_defaults = {
        "LLM_PROVIDER=mock",
        "EMBEDDING_PROVIDER=mock",
        "EVALUATION_PROVIDER=mock",
        "TRANSLATION_PROVIDER=mock",
        "AVATAR_PROVIDER=mock",
        "TTS_PROVIDER=mock",
        "STT_PROVIDER=mock",
        "SUBTITLE_PROVIDER=mock",
        "VIDEO_RENDERER=local",
        "STORAGE_PROVIDER=local",
        "VECTOR_STORE=disabled",
    }
    for default in sorted(expected_defaults):
        if default not in text:
            failures.append(f".env.example must include free/local test default: {default}")


def check_traceability_rules(changes: list[str]) -> None:
    if not changes:
        return
    changed_set = set(changes)
    architecture_changed = any(change.startswith(ARCHITECTURE_IMPACT_PREFIXES) for change in changes)
    adr_updated = any(change.startswith("docs/ADR/") for change in changes)
    if architecture_changed and not adr_updated:
        failures.append("Architecture-impacting changes require an ADR update under docs/ADR/.")

    prd_changed = any(change.startswith(PRD_IMPACT_PREFIXES) for change in changes)
    traceability_updated = "docs/TRACEABILITY.md" in changed_set
    if prd_changed and not traceability_updated:
        failures.append("PRD-impacting changes require docs/TRACEABILITY.md to be updated.")


def check_status_tracking_rules(changes: list[str]) -> None:
    if not changes:
        return
    changed_set = set(changes)
    status_updated = "docs/STATUS.md" in changed_set
    status_impacted = any(change.startswith(STATUS_IMPACT_PREFIXES) for change in changes)
    if status_impacted and not status_updated:
        failures.append("Repository-tracked stage/governance changes require docs/STATUS.md to be updated.")


def check_llm_tracing_and_citations() -> None:
    for path in iter_text_files():
        rel = relative(path)
        if path.suffix.lower() not in CODE_SUFFIXES:
            continue
        if rel == "scripts/guardrails_check.py" or rel.startswith("scripts/quality/"):
            continue
        text = read_text(path).lower()
        if any(term in text for term in ["llm", "generate_script", "walkthrough script", "generated_script"]):
            if "trace" not in text and "run_id" not in text:
                failures.append(f"{rel} appears to generate/use LLM output without trace/run_id metadata.")
            if any(term in text for term in ["script", "walkthrough", "answer"]):
                if "source_chunk" not in text and "citation" not in text and "context_id" not in text:
                    failures.append(f"{rel} appears to generate scripts/answers without source chunk citations.")


def check_eval_results_blocking() -> None:
    candidate_paths = [ROOT / "reports" / "eval-results.json", ROOT / "eval-results.json"]
    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            data = json.loads(read_text(path))
        except json.JSONDecodeError:
            failures.append(f"{relative(path)} is not valid JSON.")
            continue
        status = str(data.get("status", data.get("result", ""))).lower()
        failures_found = data.get("failures", [])
        if status in {"fail", "failed", "error"} or failures_found:
            failures.append(f"Evaluation failures found in {relative(path)}. Eval failures block merge.")


def check_security_results_blocking() -> None:
    candidate_paths = [ROOT / "reports" / "security-results.json", ROOT / "security-results.json"]
    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            data = json.loads(read_text(path))
        except json.JSONDecodeError:
            failures.append(f"{relative(path)} is not valid JSON.")
            continue
        findings = data.get("findings", data if isinstance(data, list) else [])
        for finding in findings:
            severity = str(finding.get("severity", "")).lower() if isinstance(finding, dict) else ""
            if severity in {"critical", "high"}:
                failures.append(f"Security {severity} finding found in {relative(path)}. Critical/high findings block merge.")


def main() -> int:
    changes = changed_files()
    check_no_direct_main_push()
    check_issue_linked_pull_request()
    check_workflows_least_privilege()
    check_secrets()
    check_provider_keys_are_env_only()
    check_mock_local_defaults()
    check_traceability_rules(changes)
    check_status_tracking_rules(changes)
    check_llm_tracing_and_citations()
    check_eval_results_blocking()
    check_security_results_blocking()

    if warnings:
        print("Guardrail warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if failures:
        print("Guardrail failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("All NarraTwin AI repository guardrails passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
