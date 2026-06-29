#!/usr/bin/env python3
"""Executable Stage 0 quality gate for NarraTwin AI."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE0_BRANCH_PATTERN = re.compile(r"^stage0-")

REQUIRED_FILES = [
    "AGENTS.md",
    ".github/pull_request_template.md",
    ".github/workflows/quality.yml",
    ".github/workflows/quality-gates.yml",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
    "docs/AI_BUILD_BRIEF.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/STATUS.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/THIRD_PARTY_NOTICES.md",
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
    "docs/STATUS.md",
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
    ".github/workflows/quality.yml",
    ".github/workflows/quality-gates.yml",
    ".gitignore",
    ".stage/current",
    "AGENTS.md",
    "Makefile",
    "README.md",
    "docs/AI_BUILD_BRIEF.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/STATUS.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/THIRD_PARTY_NOTICES.md",
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

STAGE0_PYTHON_GOVERNANCE_FILES = (
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/stage_not_implemented.py",
)

STAGE0_BANNED_IMPORT_ROOTS = {
    "aiohttp",
    "anthropic",
    "boto3",
    "chromadb",
    "django",
    "fastapi",
    "flask",
    "google",
    "gradio",
    "httpx",
    "langchain",
    "llama_index",
    "numpy",
    "openai",
    "pandas",
    "pytest",
    "requests",
    "sqlalchemy",
    "streamlit",
    "uvicorn",
}

STAGE0_MUTATING_CALL_NAMES = {
    "mkdir",
    "rename",
    "replace",
    "rmdir",
    "symlink_to",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
}

STAGE0_KNOWN_STDLIB_IMPORT_ROOTS = {
    "ast",
    "json",
    "os",
    "pathlib",
    "re",
    "subprocess",
    "sys",
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
        merge_base = run(["git", "merge-base", "origin/main", "HEAD"])
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


def section_text(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    remainder = text[start + len(heading):]
    match = re.search(r"\n## ", remainder)
    if not match:
        return remainder
    return remainder[:match.start()]


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
    branch = result.stdout.strip() or os.environ.get("GITHUB_HEAD_REF", "").strip()
    if branch == "main":
        return
    if not STAGE0_BRANCH_PATTERN.search(branch):
        fail(f"Stage 0 branch must match `stage0-*` before merge or be `main` after merge, found: {branch}", failures)


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


def check_third_party_notices(failures: list[str]) -> None:
    rel = "docs/THIRD_PARTY_NOTICES.md"
    path = ROOT / rel
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    required_entries = [
        "PM Skills",
        "GitHub Spec Kit",
        "Addy Osmani Agent Skills",
        "Agent Skills Standard",
        "GitHub Action: Checkout",
        "GitHub Action: Setup Python",
        "GitHub Action: Upload Artifact",
        "Gitleaks GitHub Action",
        "GitHub Action: Markdownlint CLI2",
    ]
    for entry in required_entries:
        if entry not in text:
            fail(f"{rel} must record the Stage 0 governed third-party source: {entry}", failures)


def check_status_doc(failures: list[str]) -> None:
    rel = "docs/STATUS.md"
    path = ROOT / rel
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    issue_section = section_text(text, "## Issue Ledger")
    pr_section = section_text(text, "## Pull Request Ledger")
    known_gaps_section = section_text(text, "## Known Gaps And Reconciliation Items")
    next_actions_section = section_text(text, "## Next Approved Actions")
    required_sections = [
        "# Program Status",
        "## Current Baseline",
        "## Executive Status",
        "## Stage Ledger",
        "## Issue Ledger",
        "## Pull Request Ledger",
        "## Completed Work",
        "## Pre-Implementation Document Inventory",
        "## Known Gaps And Reconciliation Items",
        "## Next Approved Actions",
        "## Maintenance Protocol",
    ]
    for section in required_sections:
        if section not in text:
            fail(f"{rel} is missing required status-tracker section: {section}", failures)
    current_stage = (ROOT / ".stage" / "current").read_text(encoding="utf-8").strip() if (ROOT / ".stage" / "current").exists() else ""
    current_branch = run(["git", "branch", "--show-current"]).stdout.strip()
    required_phrases = [
        "Last reviewed date:",
        "Current stage marker:",
        "Product implementation merged to `main`:",
        "Tracker enforcement scope:",
        "Out-of-band GitHub reconciliation:",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            fail(f"{rel} must include current-baseline field: {phrase}", failures)
    if current_stage and f".stage/current = {current_stage}" not in text:
        fail(f"{rel} must record the current stage marker value `.stage/current = {current_stage}`.", failures)
    for label in [*(f"Stage {stage}" for stage in range(0, 9)), "Final Review"]:
        if not re.search(rf"\|\s*{re.escape(label)}\s*\|", text):
            fail(f"{rel} must include a {label} row in the stage ledger.", failures)
    if not re.search(r"#\d+", text):
        fail(f"{rel} must record issue or pull request references using #<number> notation.", failures)
    if len(re.findall(r"(?m)^\|\s*`#\d+`\s*\|", issue_section)) < 10:
        fail(f"{rel} must include a populated issue ledger with repository-tracked issue rows.", failures)
    if len(re.findall(r"(?m)^\|\s*`#\d+`\s*\|", pr_section)) < 3:
        fail(f"{rel} must include a populated pull request ledger with repository-tracked PR rows.", failures)
    if not re.search(r"(?m)^1\.\s+", next_actions_section):
        fail(f"{rel} must include numbered next approved actions.", failures)
    if not re.search(r"(?m)^- ", known_gaps_section):
        fail(f"{rel} must record at least one known gap or reconciliation item.", failures)
    unstable_markers = [
        "Authoring branch at snapshot:",
        "Open governance issue at snapshot:",
        "Open governance PR at snapshot:",
        "Open at snapshot",
        "Until PR `#",
        "does not yet contain `docs/STATUS.md`",
        "This branch adds",
    ]
    for marker in unstable_markers:
        if marker in text:
            fail(f"{rel} contains merge-unstable tracker content that should not appear in the current baseline: {marker}", failures)
    if current_branch and current_branch != "main" and current_branch in text:
        fail(f"{rel} must not embed the current working branch name `{current_branch}` in the current baseline.", failures)


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


def check_quality_workflow(failures: list[str]) -> None:
    workflow_requirements = {
        ".github/workflows/quality-gates.yml": [
            "name: Run stage quality gate",
            "run: make quality",
            "name: Run repository guardrails",
        ],
        ".github/workflows/quality.yml": [
            'if [ -f ".stage/current" ] && [ "$(tr -d',
            'echo "Backend lint not applicable during Stage 0."',
            'echo "Backend tests not applicable during Stage 0."',
        ],
    }
    for rel, required_snippets in workflow_requirements.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in required_snippets:
            if snippet not in text:
                fail(f"{rel} must include the Stage 0 CI enforcement snippet: {snippet}", failures)


def is_stdlib_import(module_name: str) -> bool:
    if module_name == "__future__":
        return True
    stdlib_modules = getattr(sys, "stdlib_module_names", set()) or STAGE0_KNOWN_STDLIB_IMPORT_ROOTS
    return module_name in stdlib_modules


def check_stage0_script_purity(failures: list[str]) -> None:
    for rel in STAGE0_PYTHON_GOVERNANCE_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            fail(f"{rel} is not valid Python for Stage 0 purity checks: {exc}", failures)
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in STAGE0_BANNED_IMPORT_ROOTS:
                        fail(f"{rel} imports banned product/runtime module during Stage 0: {root}", failures)
                    elif not is_stdlib_import(root):
                        fail(f"{rel} imports non-stdlib module during Stage 0: {root}", failures)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                root = node.module.split(".", 1)[0]
                if root in STAGE0_BANNED_IMPORT_ROOTS:
                    fail(f"{rel} imports banned product/runtime module during Stage 0: {root}", failures)
                elif not is_stdlib_import(root):
                    fail(f"{rel} imports non-stdlib module during Stage 0: {root}", failures)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open" and len(node.args) >= 2:
                    mode = node.args[1]
                    if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and any(
                        flag in mode.value for flag in ("w", "a", "x", "+")
                    ):
                        fail(f"{rel} must stay read-only in Stage 0; found open(..., {mode.value!r}).", failures)
                elif isinstance(node.func, ast.Attribute) and node.func.attr in STAGE0_MUTATING_CALL_NAMES:
                    fail(f"{rel} must stay read-only in Stage 0; found mutating filesystem call: {node.func.attr}().", failures)


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
    check_status_doc(failures)
    check_third_party_notices(failures)
    check_workflow_sources_locked(failures)
    check_make_targets(failures)
    check_quality_workflow(failures)
    check_stage0_script_purity(failures)
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
