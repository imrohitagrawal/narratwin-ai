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
    "docs/evals/phase1_golden_questions.jsonl",
    "docs/demo/PHASE_1_DEMO_SCRIPT.md",
    "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
    "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
}

MODULE_A_ALLOWED_CHANGED_FILES = REQUIRED_PHASE1_FILES | {
    "Makefile",
    "README.md",
    "docs/PRD.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/RUNBOOK.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "portfolio/README.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
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
    allowed_files = ISSUE_37_ALLOWED_CHANGED_FILES if branch.startswith("phase-1-closure-37-") else MODULE_A_ALLOWED_CHANGED_FILES
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
        "process-local",
        "non-durable",
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

    if failures:
        print("Phase 1 Closure quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Phase 1 Closure governance quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
