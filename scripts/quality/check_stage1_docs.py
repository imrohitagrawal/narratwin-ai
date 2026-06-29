#!/usr/bin/env python3
"""Executable Stage 1 quality gate for NarraTwin AI."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE1_BRANCH_PATTERN = re.compile(r"^stage1-")

REQUIRED_FILES = [
    "docs/PRODUCT_STRATEGY.md",
    "docs/PRD.md",
    "docs/PRD_RED_TEAM_REVIEW.md",
    "docs/NORTH_STAR_METRICS.md",
    "docs/ROADMAP.md",
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/PHASE_PLAN.md",
    "docs/TRACEABILITY.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/QUALITY_GATES.md",
    ".stage/current",
    "Makefile",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage1_docs.py",
]

STAGE1_ALLOWED_FILES = {
    ".stage/current",
    "Makefile",
    "docs/NORTH_STAR_METRICS.md",
    "docs/PHASE_PLAN.md",
    "docs/PRD.md",
    "docs/PRD_RED_TEAM_REVIEW.md",
    "docs/PRODUCT_STRATEGY.md",
    "docs/QUALITY_GATES.md",
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/ROADMAP.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "scripts/ci/backend-lint.sh",
    "scripts/ci/backend-test.sh",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/check_stage1_docs.py",
}

PRODUCT_CODE_PATTERNS = [
    re.compile(r"^(app|apps|api|backend|frontend|server|src|web|packages|services|rag|providers|avatar)/"),
    re.compile(r"(^|/)(package\.json|pyproject\.toml|requirements.*\.txt|uv\.lock|pnpm-lock\.yaml|package-lock\.json|yarn\.lock)$"),
    re.compile(r"(^|/)(Dockerfile|docker-compose\.ya?ml|compose\.ya?ml)$"),
]

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

PYTHON_GOVERNANCE_FILES = (
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/check_stage1_docs.py",
)

STAGE1_STDLIB_IMPORT_ROOTS = set(getattr(sys, "stdlib_module_names", set())) | {
    "__future__",
}
STAGE1_LOCAL_IMPORT_ROOTS: set[str] = set()


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def repo_files() -> list[str]:
    tracked = run(["git", "ls-files"])
    if tracked.returncode != 0:
        raise RuntimeError(tracked.stderr.strip() or "git ls-files failed")
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files --others failed")
    return sorted(
        {
            line.strip()
            for output in (tracked.stdout, untracked.stdout)
            for line in output.splitlines()
            if line.strip()
        }
    )


def changed_files_for_stage_scope() -> list[str]:
    merge_base = run(["git", "merge-base", "main", "HEAD"])
    if merge_base.returncode != 0:
        merge_base = run(["git", "merge-base", "origin/main", "HEAD"])
    if merge_base.returncode != 0:
        raise RuntimeError(merge_base.stderr.strip() or "git merge-base main HEAD failed")

    base = merge_base.stdout.strip()
    committed = run(["git", "diff", "--name-only", f"{base}..HEAD"])
    working = run(["git", "diff", "--name-only", "HEAD"])
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    for result, label in ((committed, "committed diff"), (working, "working diff"), (untracked, "untracked files")):
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"git {label} failed")
    return sorted(
        {
            line.strip()
            for output in (committed.stdout, working.stdout, untracked.stdout)
            for line in output.splitlines()
            if line.strip()
        }
    )


def check_required_files(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"Missing required Stage 1 file: {rel}", failures)


def check_current_stage(failures: list[str]) -> None:
    current = ROOT / ".stage" / "current"
    if not current.exists():
        fail("Missing .stage/current.", failures)
        return
    value = current.read_text(encoding="utf-8").strip()
    if value != "1":
        fail(f".stage/current must contain 1 during Stage 1, found: {value!r}", failures)


def check_branch_name(failures: list[str]) -> None:
    result = run(["git", "branch", "--show-current"])
    if result.returncode != 0:
        fail(result.stderr.strip() or "Could not determine current branch.", failures)
        return
    branch = result.stdout.strip() or os.environ.get("GITHUB_HEAD_REF", "").strip()
    if branch == "main":
        return
    if not STAGE1_BRANCH_PATTERN.search(branch):
        fail(f"Stage 1 branch must match `stage1-*` before merge or be `main` after merge, found: {branch}", failures)


def check_stage1_scope(failures: list[str]) -> None:
    try:
        changed_files = changed_files_for_stage_scope()
    except RuntimeError as exc:
        fail(str(exc), failures)
        return
    for rel in changed_files:
        if rel not in STAGE1_ALLOWED_FILES:
            fail(f"Stage 1 branch changed file outside the allowed scope: {rel}", failures)


def check_no_product_code(files: list[str], failures: list[str]) -> None:
    allowed_scripts = {
        "scripts/guardrails_check.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/check_stage0_docs.py",
        "scripts/quality/check_stage1_docs.py",
        "scripts/quality/stage_not_implemented.py",
    }
    for rel in files:
        if rel in allowed_scripts:
            continue
        if any(pattern.search(rel) for pattern in PRODUCT_CODE_PATTERNS):
            fail(f"Product/runtime code or manifest is not allowed in Stage 1: {rel}", failures)


def check_prd_artifacts(failures: list[str]) -> None:
    required_phrases_by_file = {
        "docs/PRODUCT_STRATEGY.md": [
            "pre-rendered multilingual demo video",
            "interactive AI avatar walkthrough",
            "free-first",
            "premium",
        ],
        "docs/PRD.md": [
            "PRD v1.0",
            "Project Knowledge Upload",
            "RAG Ingestion",
            "Grounded Script Generation",
            "Evaluation Gates",
            "Security And Privacy Guardrails",
            "Free-first And Premium-provider Modes",
        ],
        "docs/PRD_RED_TEAM_REVIEW.md": [
            "Top Kill-assumptions",
            "Kill criterion",
            "Cheapest test",
        ],
        "docs/NORTH_STAR_METRICS.md": [
            "North Star Metric",
            "One Metric That Matters",
            "Release Thresholds For Slice 1",
        ],
        "docs/ROADMAP.md": [
            "Outcome Roadmap",
            "Product Mode Alignment",
            "Roadmap Guardrails",
        ],
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": [
            "Canonical Requirement Matrix",
            "FR-001",
            "NFR-001",
        ],
        "docs/PHASE_PLAN.md": [
            "Phase-to-stage mapping",
            "First Vertical Slice",
            "Boundaries",
        ],
    }
    for rel, phrases in required_phrases_by_file.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} must include Stage 1 product phrase: {phrase}", failures)


def check_traceability_canonical(failures: list[str]) -> None:
    trace = read("docs/TRACEABILITY.md") if (ROOT / "docs/TRACEABILITY.md").exists() else ""
    rtm = read("docs/REQUIREMENTS_TRACEABILITY_MATRIX.md") if (ROOT / "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md").exists() else ""
    if "Canonical source: `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`" not in trace:
        fail("docs/TRACEABILITY.md must declare docs/REQUIREMENTS_TRACEABILITY_MATRIX.md as canonical.", failures)
    for req_id in ("FR-001", "FR-017", "FR-018", "FR-019", "NFR-001", "NFR-012"):
        if req_id not in rtm:
            fail(f"docs/REQUIREMENTS_TRACEABILITY_MATRIX.md missing requirement ID: {req_id}", failures)
    if "Stage 4 / `#4`" not in rtm:
        fail("docs/REQUIREMENTS_TRACEABILITY_MATRIX.md must map Slice 1 requirements to Stage 4 / #4.", failures)


def check_status_doc(failures: list[str]) -> None:
    text = read("docs/STATUS.md") if (ROOT / "docs/STATUS.md").exists() else ""
    required = [
        ".stage/current = 1",
        "PR `#26` represents the Stage 1 product/PRD hardening artifact set",
        "`#1` is product strategy and PRD v1.0 hardening",
        "`#16` remains the follow-on Spec Kit",
    ]
    for phrase in required:
        if phrase not in text:
            fail(f"docs/STATUS.md must record Stage 1 PR state: {phrase}", failures)


def check_makefile_and_dispatcher(failures: list[str]) -> None:
    makefile = read("Makefile") if (ROOT / "Makefile").exists() else ""
    dispatcher = read("scripts/quality/check_quality_stage.py") if (ROOT / "scripts/quality/check_quality_stage.py").exists() else ""
    if "python3 scripts/quality/check_stage1_docs.py" not in makefile:
        fail("Makefile stage1-quality must run scripts/quality/check_stage1_docs.py.", failures)
    if "check_stage1_docs.py" not in dispatcher:
        fail("scripts/quality/check_quality_stage.py must dispatch Stage 1 to check_stage1_docs.py.", failures)


def check_no_obvious_secrets(failures: list[str]) -> None:
    for rel in repo_files():
        path = ROOT / rel
        if not path.is_file() or path.suffix not in {".md", ".py", ".txt", ".yaml", ".yml", ".example"}:
            continue
        if rel == "scripts/guardrails_check.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"Potential committed secret pattern found in {rel}.", failures)


def check_python_governance_scripts(failures: list[str]) -> None:
    for rel in PYTHON_GOVERNANCE_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            fail(f"{rel} must compile: {exc}", failures)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = [node.module.split(".", 1)[0]]
            else:
                continue
            for root in roots:
                if root not in STAGE1_STDLIB_IMPORT_ROOTS and root not in STAGE1_LOCAL_IMPORT_ROOTS:
                    fail(f"{rel} imports non-stdlib dependency {root!r}.", failures)


def check_git_diff_clean(failures: list[str]) -> None:
    result = run(["git", "diff", "--check"])
    if result.returncode != 0:
        fail(result.stdout.strip() or result.stderr.strip() or "git diff --check failed.", failures)


def main() -> int:
    failures: list[str] = []
    try:
        files = repo_files()
    except RuntimeError as exc:
        print(f"Stage 1 quality failures:\n- {exc}")
        return 1

    check_required_files(failures)
    check_current_stage(failures)
    check_branch_name(failures)
    check_stage1_scope(failures)
    check_no_product_code(files, failures)
    check_prd_artifacts(failures)
    check_traceability_canonical(failures)
    check_status_doc(failures)
    check_makefile_and_dispatcher(failures)
    check_no_obvious_secrets(failures)
    check_python_governance_scripts(failures)
    check_git_diff_clean(failures)

    if failures:
        print("Stage 1 quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Stage 1 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
