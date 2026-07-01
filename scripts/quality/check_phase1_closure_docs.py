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

REQUIRED_FILES = {
    "docs/reviews/PHASE_1_CLOSURE_REPORT.md",
    "docs/reviews/FINAL_REVIEW.md",
    "docs/reviews/RISK_REGISTER.md",
    "docs/reviews/DEFECT_BACKLOG.md",
    "docs/reviews/GO_NO_GO.md",
    "docs/RELEASE_READINESS_REVIEW.md",
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/RISK_REGISTER.md",
    "docs/evals/phase1_golden_questions.jsonl",
    "docs/demo/PHASE_1_DEMO_SCRIPT.md",
    "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
    "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
}

ALLOWED_CHANGED_FILES = REQUIRED_FILES | {
    "Makefile",
    "docs/PRD.md",
    "docs/QUALITY_GATES.md",
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
    return sorted({line.strip() for output in outputs for line in output.splitlines() if line.strip()})


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def check_branch(failures: list[str]) -> None:
    branch = current_branch()
    if branch and branch != "main" and not PHASE1_BRANCH.match(branch):
        fail(failures, f"Phase 1 Closure work must run on phase-1-closure-* or main; got {branch}.")


def check_required_files(failures: list[str]) -> None:
    for rel in sorted(REQUIRED_FILES):
        if not (ROOT / rel).is_file():
            fail(failures, f"Missing required Phase 1 Closure file: {rel}")


def check_changed_files(failures: list[str]) -> None:
    for rel in changed_files():
        if rel not in ALLOWED_CHANGED_FILES:
            fail(failures, f"Phase 1 Closure governance PR may not change {rel}.")


def check_closure_report(failures: list[str]) -> None:
    text = read("docs/reviews/PHASE_1_CLOSURE_REPORT.md")
    for marker in (
        "Phase 1 Closure Gate",
        "PR #45",
        "5a294c72d2b4b8cbbc0339f7bcb3f17089bddece",
        "P0",
        "P1",
        "Module A",
        "Module B",
        "Module C",
        "Module D",
        "Module E",
        "Module F",
        "Module G",
        "No release tag has been created",
    ):
        if marker not in text:
            fail(failures, f"Phase 1 closure report missing marker: {marker}")
    for issue in range(35, 45):
        if f"`#{issue}`" not in text:
            fail(failures, f"Phase 1 closure report must classify issue #{issue}.")


def check_golden_questions(failures: list[str]) -> None:
    path = ROOT / "docs/evals/phase1_golden_questions.jsonl"
    questions: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(failures, f"Golden question line {index} is invalid JSON: {exc}")
            continue
        question = row.get("question")
        if not isinstance(question, str) or not question:
            fail(failures, f"Golden question line {index} must include a non-empty question.")
            continue
        questions.append(question)
        if row.get("unsupportedClaimsMax") != 0:
            fail(failures, f"Golden question line {index} must require unsupportedClaimsMax = 0.")
    required = {
        "What is this project?",
        "Who is the audience?",
        "What problem does it solve?",
        "What are Mode 1 and Mode 2?",
        "What data sources does it use?",
        "What should the system not claim?",
        "What are the current limitations?",
        "What is the demo flow?",
    }
    missing = sorted(required - set(questions))
    if missing:
        fail(failures, f"Golden question set missing questions: {', '.join(missing)}")


def check_demo_docs(failures: list[str]) -> None:
    combined = "\n".join(
        read(path)
        for path in (
            "docs/demo/PHASE_1_DEMO_SCRIPT.md",
            "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
            "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
            "portfolio/README.md",
        )
    )
    for marker in (
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
    combined = "\n".join(
        read(path)
        for path in (
            "docs/RELEASE_READINESS_REVIEW.md",
            "docs/RELEASE_CHECKLIST.md",
            "docs/RUNBOOK.md",
            "docs/STATUS.md",
            "docs/RISK_REGISTER.md",
            "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
        )
    )
    for marker in (
        "Phase 1 Closure",
        "No-Go",
        "PR `#45`",
        "issues `#35` through `#44`",
        "Stage 8 merged",
        "Final Review merged",
        "FR-001",
        "Implemented",
        "Final Review Risk Register",
    ):
        if marker not in combined:
            fail(failures, f"Phase 1 release docs missing marker: {marker}")


def main() -> int:
    failures: list[str] = []
    check_branch(failures)
    check_required_files(failures)
    check_changed_files(failures)
    if not failures:
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
