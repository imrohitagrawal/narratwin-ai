#!/usr/bin/env python3
"""Executable Stage 0 quality gate for NarraTwin AI."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE0_BRANCH_PATTERN = re.compile(r"^stage0-")

REQUIRED_FILES = [
    "AGENTS.md",
    ".github/pull_request_template.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
    "docs/AI_BUILD_BRIEF.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
    ".stage/current",
    "Makefile",
    "README.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/stage_not_implemented.py",
]

OPERATING_DOCS = [
    "AGENTS.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
]

REQUIRED_TARGETS = [
    "quality",
    "stage0-quality",
    "stage1-quality",
    "stage2-quality",
    "stage3-quality",
    "stage4-quality",
    "stage5-quality",
    "stage6-quality",
    "stage7-quality",
    "stage8-quality",
    "final-review-quality",
]

STAGE0_ALLOWED_FILES = {
    ".github/pull_request_template.md",
    ".gitignore",
    ".stage/current",
    "AGENTS.md",
    "Makefile",
    "README.md",
    "docs/AI_BUILD_BRIEF.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/stage_not_implemented.py",
}

PRODUCT_CODE_PATTERNS = [
    re.compile(r"^(app|apps|api|backend|frontend|server|src|web|packages|services|rag|providers|avatar)/"),
    re.compile(r"(^|/)(package\.json|pyproject\.toml|requirements.*\.txt|uv\.lock|pnpm-lock\.yaml|package-lock\.json|yarn\.lock)$"),
    re.compile(r"(^|/)(Dockerfile|docker-compose\.ya?ml|compose\.ya?ml)$"),
]

TEXT_SUFFIXES = {
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

SECRET_SCAN_EXCLUDES = {
    "scripts/guardrails_check.py",
    "scripts/quality/check_stage0_docs.py",
}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def repo_files() -> list[str]:
    result = run(["git", "ls-files", "--others", "--exclude-standard"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files --others failed")
    untracked = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    result = run(["git", "ls-files"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    tracked = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    return sorted(set(tracked + untracked))


def changed_files_for_stage_scope() -> list[str]:
    merge_base = run(["git", "merge-base", "main", "HEAD"])
    if merge_base.returncode != 0:
        raise RuntimeError(merge_base.stderr.strip() or "git merge-base main HEAD failed")

    base = merge_base.stdout.strip()
    committed = run(["git", "diff", "--name-only", f"{base}..HEAD"])
    if committed.returncode != 0:
        raise RuntimeError(committed.stderr.strip() or "git diff base..HEAD failed")

    working = run(["git", "diff", "--name-only", "HEAD"])
    if working.returncode != 0:
        raise RuntimeError(working.stderr.strip() or "git diff HEAD failed")

    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files --others failed")

    files = {
        line.strip()
        for output in (committed.stdout, working.stdout, untracked.stdout)
        for line in output.splitlines()
        if line.strip()
    }
    return sorted(files)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def check_required_files(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            fail(f"Missing required Stage 0 file: {rel}", failures)


def check_current_stage(failures: list[str]) -> None:
    current = ROOT / ".stage" / "current"
    if not current.exists():
        return
    value = current.read_text(encoding="utf-8").strip()
    if value != "0":
        fail(f".stage/current must contain 0 during Stage 0, found: {value!r}", failures)


def check_branch_name(failures: list[str]) -> None:
    result = run(["git", "branch", "--show-current"])
    if result.returncode != 0:
        fail(result.stderr.strip() or "Could not determine current branch.", failures)
        return
    branch = result.stdout.strip()
    if not STAGE0_BRANCH_PATTERN.search(branch):
        fail(f"Stage 0 branch must match `stage0-*`, found: {branch}", failures)


def check_stage_documentation(failures: list[str]) -> None:
    combined = "\n".join(read(rel) for rel in OPERATING_DOCS if (ROOT / rel).exists())
    for stage in range(0, 9):
        if f"Stage {stage}" not in combined:
            fail(f"Stage {stage} is not documented in operating docs.", failures)
    if "Final Review" not in combined:
        fail("Final Review is not documented in operating docs.", failures)


def check_no_product_code(files: list[str], failures: list[str]) -> None:
    allowed_scripts = {
        "scripts/guardrails_check.py",
        "scripts/ci/backend-lint.sh",
        "scripts/ci/backend-test.sh",
        "scripts/quality/check_stage0_docs.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/stage_not_implemented.py",
    }
    for rel in files:
        if rel in allowed_scripts:
            continue
        if any(pattern.search(rel) for pattern in PRODUCT_CODE_PATTERNS):
            fail(f"Product/runtime code or manifest is not allowed in Stage 0: {rel}", failures)


def check_stage0_scope(failures: list[str]) -> None:
    try:
        changed_files = changed_files_for_stage_scope()
    except RuntimeError as exc:
        fail(str(exc), failures)
        return

    for rel in changed_files:
        if rel not in STAGE0_ALLOWED_FILES:
            fail(f"Stage 0 branch changed file outside the allowed scope: {rel}", failures)


def check_placeholders(failures: list[str]) -> None:
    placeholder = re.compile(r"\b(TODO|FIXME|TBD|REPLACE_ME|INSERT_HERE|CHANGEME)\b", re.IGNORECASE)
    for rel in OPERATING_DOCS:
        path = ROOT / rel
        if not path.exists():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if placeholder.search(line):
                fail(f"Unresolved placeholder in {rel}:{line_no}: {line.strip()}", failures)


def check_skill_lock(failures: list[str]) -> None:
    rel = "docs/SKILL_LOCK.md"
    path = ROOT / rel
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    required_headers = [
        "Source URL",
        "Pin/version status",
        "License status",
        "Purpose",
        "Active stage",
        "Activation status",
    ]
    for header in required_headers:
        if header not in text:
            fail(f"{rel} missing required lock field: {header}", failures)
    source_rows = [line for line in text.splitlines() if line.startswith("| ") and "`https://github.com/" in line]
    if len(source_rows) < 3:
        fail(f"{rel} must record locked skill/tool source URLs.", failures)
    for row in source_rows:
        columns = [column.strip() for column in row.strip("|").split("|")]
        if len(columns) < 7:
            fail(f"{rel} row does not contain all required fields: {row}", failures)
            continue
        if not all(columns[:7]):
            fail(f"{rel} row has an empty required field: {row}", failures)


def check_workflow_sources_locked(failures: list[str]) -> None:
    skill_lock = ROOT / "docs" / "SKILL_LOCK.md"
    if not skill_lock.exists():
        return
    text = skill_lock.read_text(encoding="utf-8")
    workflow_dir = ROOT / ".github" / "workflows"
    uses_pattern = re.compile(r"^\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@", re.MULTILINE)
    required_sources = set()
    for workflow in list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")):
        workflow_text = workflow.read_text(encoding="utf-8")
        for action in uses_pattern.findall(workflow_text):
            required_sources.add(f"https://github.com/{action}")

    for source in sorted(required_sources):
        if f"`{source}`" not in text:
            fail(f"docs/SKILL_LOCK.md is missing workflow source entry: {source}", failures)


def check_make_targets(failures: list[str]) -> None:
    makefile = ROOT / "Makefile"
    if not makefile.exists():
        return
    text = makefile.read_text(encoding="utf-8")
    for target in REQUIRED_TARGETS:
        if not re.search(rf"^{re.escape(target)}:", text, re.MULTILINE):
            fail(f"Makefile missing required target: {target}", failures)
    required_recipes = {
        "quality": "python3 scripts/quality/check_quality_stage.py",
        "stage0-quality": "python3 scripts/quality/check_stage0_docs.py",
    }
    for target, recipe in required_recipes.items():
        if not re.search(rf"^{re.escape(target)}:\n\t{re.escape(recipe)}", text, re.MULTILINE):
            fail(f"Makefile target must call the required recipe: {target} -> {recipe}", failures)
    for target in [*REQUIRED_TARGETS[2:], "final-review-quality"]:
        if not re.search(
            rf"^{re.escape(target)}:\n\tpython3 scripts/quality/stage_not_implemented\.py",
            text,
            re.MULTILINE,
        ):
            fail(f"Makefile target must fail loudly through stage_not_implemented.py: {target}", failures)


def check_diff_whitespace(failures: list[str]) -> None:
    result = run(["git", "diff", "--check"])
    if result.returncode != 0:
        fail("git diff --check failed:\n" + (result.stdout + result.stderr).strip(), failures)


def check_secret_patterns(files: list[str], failures: list[str]) -> None:
    for rel in files:
        if rel in SECRET_SCAN_EXCLUDES:
            continue
        path = ROOT / rel
        if path.suffix not in TEXT_SUFFIXES and path.name not in {"Makefile", ".env.example"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"Potential secret pattern found in tracked file: {rel}", failures)


def check_python_scripts_compile(failures: list[str]) -> None:
    for rel in [
        "scripts/guardrails_check.py",
        "scripts/quality/check_stage0_docs.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/stage_not_implemented.py",
    ]:
        result = run([sys.executable, "-m", "py_compile", rel])
        if result.returncode != 0:
            fail(f"Python compile failed for {rel}:\n{result.stderr.strip()}", failures)


def main() -> int:
    failures: list[str] = []

    check_required_files(failures)
    check_current_stage(failures)
    check_branch_name(failures)
    check_stage_documentation(failures)
    check_placeholders(failures)
    check_stage0_scope(failures)
    check_skill_lock(failures)
    check_workflow_sources_locked(failures)
    check_make_targets(failures)
    check_diff_whitespace(failures)
    check_python_scripts_compile(failures)

    try:
        files = repo_files()
    except RuntimeError as exc:
        fail(str(exc), failures)
        files = []

    check_no_product_code(files, failures)
    check_secret_patterns(files, failures)

    if failures:
        print("Stage 0 quality failures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Stage 0 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
