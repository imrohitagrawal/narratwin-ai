#!/usr/bin/env python3
"""Executable Final Review artifact gate for NarraTwin AI."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FINAL_REVIEW_BRANCH = re.compile(r"^final-review-.+")
REQUIRED_REVIEW_DOCS = {
    "docs/reviews/FINAL_REVIEW.md",
    "docs/reviews/RISK_REGISTER.md",
    "docs/reviews/DEFECT_BACKLOG.md",
    "docs/reviews/GO_NO_GO.md",
}
REQUIRED_INPUT_DOCS = {
    "docs/PRD.md",
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/QUALITY_GATES.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/RELEASE_READINESS_REVIEW.md",
}
ALLOWED_CHANGED_FILES = REQUIRED_REVIEW_DOCS | {
    "Makefile",
    "docs/QUALITY_GATES.md",
    "docs/STATUS.md",
    "scripts/quality/check_final_review_docs.py",
    "scripts/quality/check_quality_stage.py",
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
    output = run_git(["diff", "--name-only", base, "HEAD"])
    return [line.strip() for line in output.splitlines() if line.strip()]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def require_files(failures: list[str]) -> None:
    for rel in sorted(REQUIRED_REVIEW_DOCS | REQUIRED_INPUT_DOCS):
        if not (ROOT / rel).is_file():
            fail(f"Missing required Final Review input/artifact: {rel}", failures)


def check_branch(failures: list[str]) -> None:
    branch = current_branch()
    if branch and branch != "main" and not FINAL_REVIEW_BRANCH.match(branch):
        fail(f"Final Review work must run on a final-review-* branch or main after merge; got {branch}.", failures)


def check_changed_files(failures: list[str]) -> None:
    unexpected = sorted(set(changed_files()) - ALLOWED_CHANGED_FILES)
    for rel in unexpected:
        fail(f"Final Review artifact PR may not change {rel}.", failures)


def check_artifact_content(failures: list[str]) -> None:
    final_review = read("docs/reviews/FINAL_REVIEW.md")
    risk_register = read("docs/reviews/RISK_REGISTER.md")
    defect_backlog = read("docs/reviews/DEFECT_BACKLOG.md")
    go_no_go = read("docs/reviews/GO_NO_GO.md")

    for required in (
        "Linked stage issue: `#6`",
        "fb40113",
        "No-Go for production",
        "Four parallel sub-agent review slices",
    ):
        if required not in final_review:
            fail(f"docs/reviews/FINAL_REVIEW.md missing required marker: {required}", failures)

    for issue in range(35, 45):
        marker = f"`#{issue}`"
        if marker not in final_review + risk_register + defect_backlog + go_no_go:
            fail(f"Final Review artifacts must reference GitHub issue {marker}.", failures)

    for required in ("FR-RISK-001", "FR-RISK-012", "telemetry remains local/no-op"):
        if required not in risk_register:
            fail(f"docs/reviews/RISK_REGISTER.md missing required marker: {required}", failures)

    defect_ids = re.findall(r"\| (FR-DEF-\d+) \|", defect_backlog)
    duplicates = sorted({item for item in defect_ids if defect_ids.count(item) > 1})
    if duplicates:
        fail(f"docs/reviews/DEFECT_BACKLOG.md has duplicate defect IDs: {', '.join(duplicates)}", failures)

    for required in (
        "No-Go for production release.",
        "Conditional Go for local mock-provider portfolio/demo review only",
        "issues `#35` through `#44`",
    ):
        if required not in go_no_go:
            fail(f"docs/reviews/GO_NO_GO.md missing required marker: {required}", failures)


def main() -> int:
    failures: list[str] = []
    require_files(failures)
    if not failures:
        check_branch(failures)
        check_changed_files(failures)
        check_artifact_content(failures)

    if failures:
        print("Final Review quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Final Review artifact quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
