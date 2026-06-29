#!/usr/bin/env python3
"""Executable Stage 2 quality gate for NarraTwin AI."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE2_BRANCH_PATTERN = re.compile(r"^stage2-")

REQUIRED_FILES = [
    ".env.example",
    ".gitignore",
    ".stage/current",
    "Makefile",
    "docs/ADR/0001-system-architecture.md",
    "docs/ADR/0002-rag-storage.md",
    "docs/ADR/0003-llm-provider-routing.md",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/ADR/0005-observability-and-evals.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_MODEL.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/QUALITY_GATES.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THREAT_MODEL.md",
    "docs/TRACEABILITY.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage2_docs.py",
]

STAGE2_ALLOWED_FILES = {
    ".env.example",
    ".gitignore",
    ".stage/current",
    "Makefile",
    "docs/ADR/0001-architecture-approach.md",
    "docs/ADR/0001-system-architecture.md",
    "docs/ADR/0002-provider-agnostic-adapters.md",
    "docs/ADR/0002-rag-storage.md",
    "docs/ADR/0003-free-mode-vs-premium-mode.md",
    "docs/ADR/0003-llm-provider-routing.md",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/ADR/0005-observability-and-evals.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_MODEL.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/QUALITY_GATES.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/THREAT_MODEL.md",
    "docs/TRACEABILITY.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage2_docs.py",
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
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage0_docs.py",
    "scripts/quality/check_stage1_docs.py",
    "scripts/quality/check_stage2_docs.py",
)

STDLIB_IMPORT_ROOTS = set(getattr(sys, "stdlib_module_names", set())) | {"__future__"}

REQUIRED_PHRASES_BY_FILE = {
    "docs/ARCHITECTURE.md": [
        "Synthetic Local Principal",
        "Document Approval State Machine",
        "Stage 4 Resource Budgets",
        "Queue And Backpressure Contract",
        "Provider Adapter Contract",
        "Observability Event Contract",
    ],
    "docs/SECURITY_AND_PRIVACY.md": [
        "Authorization Model",
        "Secret screening is mandatory before non-local provider egress",
        "Rate And Cost Limit Values",
        "Approved Knowledge Controls",
    ],
    "docs/AI_SAFETY_AND_EVALUATION.md": [
        "Stage 4 Evaluation Policy",
        "unsupported_claim_count = 0",
        "claim-level context references",
        "Evaluation Fixture Contract",
        "UI Evaluation State Matrix",
    ],
    "docs/API_CONTRACT.md": [
        "/api/v1",
        "Idempotency Requirements",
        "Typed Response Schemas",
        "`ing_`",
        "`ctx_`",
        "Stage 4 Language Scope",
    ],
    "docs/DATA_MODEL.md": [
        "Synthetic Local Tenant And User",
        "IngestionRun",
        "ClaimSupport",
        "Required Indexes",
        "Retention And Deletion Decision",
    ],
    "docs/OBSERVABILITY_AND_COST.md": [
        "Event Schema",
        "p95",
        "queue_depth",
        "cost_budget_exceeded",
    ],
    "docs/PORTABILITY_STRATEGY.md": [
        "Provider Adapter Contract",
        "Export Tombstones",
        "Synthetic local tenant",
    ],
    "docs/THREAT_MODEL.md": [
        "Approved Knowledge Poisoning",
        "Authorization Boundary",
        "secret screening is mandatory",
    ],
    "docs/QUALITY_GATES.md": [
        "Stage 2 quality is executable",
        "Stage 2 validates",
    ],
    "docs/STAGE_ISSUE_PLAN.md": [
        "Stage 2 Architecture And Safety Branch Scope",
        "docs/API_CONTRACT.md",
    ],
    "docs/STATUS.md": [
        "Stage 2 quality is executable locally",
        "Stage 2 remediation",
    ],
}


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
            fail(f"Missing required Stage 2 file: {rel}", failures)


def check_current_stage(failures: list[str]) -> None:
    current = ROOT / ".stage" / "current"
    if not current.exists():
        fail("Missing .stage/current.", failures)
        return
    value = current.read_text(encoding="utf-8").strip()
    if value != "2":
        fail(f".stage/current must contain 2 during Stage 2, found: {value!r}", failures)


def check_branch_name(failures: list[str]) -> None:
    result = run(["git", "branch", "--show-current"])
    if result.returncode != 0:
        fail(result.stderr.strip() or "Could not determine current branch.", failures)
        return
    branch = result.stdout.strip() or os.environ.get("GITHUB_HEAD_REF", "").strip()
    if branch == "main":
        return
    if not STAGE2_BRANCH_PATTERN.search(branch):
        fail(f"Stage 2 branch must match `stage2-*` before merge or be `main` after merge, found: {branch}", failures)


def check_stage2_scope(failures: list[str]) -> None:
    try:
        changed_files = changed_files_for_stage_scope()
    except RuntimeError as exc:
        fail(str(exc), failures)
        return
    for rel in changed_files:
        if rel not in STAGE2_ALLOWED_FILES:
            fail(f"Stage 2 branch changed file outside the allowed scope: {rel}", failures)


def check_no_product_code(files: list[str], failures: list[str]) -> None:
    allowed_scripts = {
        "scripts/guardrails_check.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/check_stage0_docs.py",
        "scripts/quality/check_stage1_docs.py",
        "scripts/quality/check_stage2_docs.py",
        "scripts/quality/stage_not_implemented.py",
    }
    for rel in files:
        if rel in allowed_scripts:
            continue
        if any(pattern.search(rel) for pattern in PRODUCT_CODE_PATTERNS):
            fail(f"Product/runtime code or manifest is not allowed in Stage 2: {rel}", failures)


def check_required_phrases(failures: list[str]) -> None:
    for rel, phrases in REQUIRED_PHRASES_BY_FILE.items():
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} must include Stage 2 remediation phrase: {phrase}", failures)


def check_adr_canon(failures: list[str]) -> None:
    legacy_adrs = {
        "docs/ADR/0001-architecture-approach.md": "Superseded by `docs/ADR/0001-system-architecture.md`",
        "docs/ADR/0002-provider-agnostic-adapters.md": "Superseded by `docs/ADR/0003-llm-provider-routing.md`",
        "docs/ADR/0003-free-mode-vs-premium-mode.md": "Superseded by `docs/ADR/0001-system-architecture.md`",
    }
    for rel, phrase in legacy_adrs.items():
        path = ROOT / rel
        if path.exists() and phrase not in path.read_text(encoding="utf-8"):
            fail(f"{rel} must mark the legacy ADR as superseded: {phrase}", failures)


def check_mock_local_defaults(failures: list[str]) -> None:
    text = read(".env.example") if (ROOT / ".env.example").exists() else ""
    for default in (
        "LLM_PROVIDER=mock",
        "EMBEDDING_PROVIDER=mock",
        "EVALUATION_PROVIDER=mock",
        "AVATAR_PROVIDER=mock",
        "TTS_PROVIDER=mock",
        "STT_PROVIDER=mock",
        "STORAGE_PROVIDER=local",
    ):
        if default not in text:
            fail(f".env.example must include free/local test default: {default}", failures)


def check_no_contradictory_stage2_language(failures: list[str]) -> None:
    combined = "\n".join(
        read(rel)
        for rel in (
            "docs/ARCHITECTURE.md",
            "docs/SECURITY_AND_PRIVACY.md",
            "docs/API_CONTRACT.md",
            "docs/AI_SAFETY_AND_EVALUATION.md",
        )
        if (ROOT / rel).exists()
    )
    banned = [
        "optional obvious-secret screening before non-local provider egress",
        "fail, warn, or regenerate according to stage policy",
        "Authentication is future Stage 3/4 design",
        "Before Stage 4 code:",
    ]
    for phrase in banned:
        if phrase in combined:
            fail(f"Stage 2 docs still contain unresolved or contradictory language: {phrase}", failures)


def check_makefile_and_dispatcher(failures: list[str]) -> None:
    makefile = read("Makefile") if (ROOT / "Makefile").exists() else ""
    dispatcher = read("scripts/quality/check_quality_stage.py") if (ROOT / "scripts/quality/check_quality_stage.py").exists() else ""
    guardrails = read("scripts/guardrails_check.py") if (ROOT / "scripts/guardrails_check.py").exists() else ""
    if "python3 scripts/quality/check_stage2_docs.py" not in makefile:
        fail("Makefile stage2-quality must run scripts/quality/check_stage2_docs.py.", failures)
    if "check_stage2_docs.py" not in dispatcher:
        fail("scripts/quality/check_quality_stage.py must dispatch Stage 2 to check_stage2_docs.py.", failures)
    for default in ("LLM_PROVIDER=mock", "EMBEDDING_PROVIDER=mock", "EVALUATION_PROVIDER=mock"):
        if default not in guardrails:
            fail(f"scripts/guardrails_check.py must enforce provider default: {default}", failures)


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
                if root not in STDLIB_IMPORT_ROOTS:
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
        print(f"Stage 2 quality failures:\n- {exc}")
        return 1

    check_required_files(failures)
    check_current_stage(failures)
    check_branch_name(failures)
    check_stage2_scope(failures)
    check_no_product_code(files, failures)
    check_required_phrases(failures)
    check_adr_canon(failures)
    check_mock_local_defaults(failures)
    check_no_contradictory_stage2_language(failures)
    check_makefile_and_dispatcher(failures)
    check_no_obvious_secrets(failures)
    check_python_governance_scripts(failures)
    check_git_diff_clean(failures)

    if failures:
        print("Stage 2 quality failures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Stage 2 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
