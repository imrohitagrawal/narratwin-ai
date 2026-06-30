#!/usr/bin/env python3
"""Executable Stage 3 quality gate for NarraTwin AI."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE3_BRANCH_PATTERN = re.compile(r"^stage3-")

REQUIRED_FILES = [
    ".dockerignore",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/workflows/eval-smoke.yml",
    ".github/workflows/quality.yml",
    ".github/workflows/quality-gates.yml",
    ".pre-commit-config.yaml",
    ".gitignore",
    ".stage/current",
    ".env.example",
    "Makefile",
    "docker-compose.yml",
    "evals/smoke/stage3_health_fixture.json",
    "pyproject.toml",
    "semgrep.yml",
    "uv.lock",
    "backend/Dockerfile",
    "backend/__init__.py",
    "backend/app/__init__.py",
    "backend/app/main.py",
    "tests/api/test_health_api.py",
    "tests/unit/test_health_contract.py",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/Dockerfile",
    "frontend/.gitignore",
    "frontend/README.md",
    "frontend/eslint.config.mjs",
    "frontend/next.config.ts",
    "frontend/playwright.config.ts",
    "frontend/src/app/favicon.ico",
    "frontend/src/app/globals.css",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/page.module.css",
    "frontend/src/app/page.tsx",
    "frontend/src/app/page.test.tsx",
    "frontend/tsconfig.json",
    "frontend/tests/smoke.spec.ts",
    "frontend/vitest.config.ts",
    "scripts/ci/backend-lint.sh",
    "scripts/ci/backend-test.sh",
    "scripts/ci/docker-build.sh",
    "scripts/ci/eval-smoke.sh",
    "scripts/ci/frontend-build.sh",
    "scripts/ci/frontend-smoke.sh",
    "scripts/ci/dependency-security.sh",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
    "scripts/quality/check_stage2_docs.py",
    "scripts/quality/check_stage3_docs.py",
    "docs/LOCAL_DEVELOPMENT.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/SKILL_LOCK.md",
    "docs/API_CONTRACT.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
]

STAGE3_ALLOWED_FILES = {
    ".dockerignore",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/workflows/eval-smoke.yml",
    ".github/workflows/quality.yml",
    ".github/workflows/quality-gates.yml",
    ".pre-commit-config.yaml",
    ".gitignore",
    ".stage/current",
    ".env.example",
    "Makefile",
    "docker-compose.yml",
    "evals/smoke/stage3_health_fixture.json",
    "pyproject.toml",
    "semgrep.yml",
    "uv.lock",
    "backend/Dockerfile",
    "backend/__init__.py",
    "backend/app/__init__.py",
    "backend/app/main.py",
    "tests/api/test_health_api.py",
    "tests/unit/test_health_contract.py",
    "frontend/.gitignore",
    "frontend/README.md",
    "frontend/eslint.config.mjs",
    "frontend/next.config.ts",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/Dockerfile",
    "frontend/playwright.config.ts",
    "frontend/src/app/favicon.ico",
    "frontend/src/app/globals.css",
    "frontend/src/app/layout.tsx",
    "frontend/src/app/page.module.css",
    "frontend/src/app/page.tsx",
    "frontend/src/app/page.test.tsx",
    "frontend/tests/smoke.spec.ts",
    "frontend/tsconfig.json",
    "frontend/vitest.config.ts",
    "docs/LOCAL_DEVELOPMENT.md",
    "docs/ADR/0001-system-architecture.md",
    "docs/API_CONTRACT.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/SKILL_LOCK.md",
    "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
    "scripts/ci/backend-lint.sh",
    "scripts/ci/backend-test.sh",
    "scripts/ci/docker-build.sh",
    "scripts/ci/eval-smoke.sh",
    "scripts/ci/frontend-build.sh",
    "scripts/ci/frontend-smoke.sh",
    "scripts/ci/dependency-security.sh",
    "scripts/guardrails_check.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
    "scripts/quality/check_stage2_docs.py",
    "scripts/quality/check_stage3_docs.py",
}

BLOCKED_STAGE3_PATTERNS = [
    re.compile(r"^(api|server|src|rag|providers|avatar|infra|terraform|docker)/"),
    re.compile(r"(^|/)alembic/"),
]

PYTHON_DEPENDENCIES = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "psycopg",
    "psycopg-binary",
    "alembic",
    "redis",
    "python-multipart",
}

PYTHON_DEV_DEPENDENCIES = {
    "pytest",
    "pytest-cov",
    "ruff",
    "mypy",
    "bandit",
    "pip-audit",
    "pre-commit",
    "httpx",
    "httpx2",
    "semgrep",
}

FRONTEND_DEPENDENCIES = {"next", "react", "react-dom"}
FRONTEND_DEV_DEPENDENCIES = {
    "@playwright/test",
    "typescript",
    "eslint",
    "eslint-config-next",
    "vitest",
    "playwright",
}
FRONTEND_SCRIPTS = {"build", "lint", "typecheck", "test", "test:smoke"}

FRONTEND_ALLOWED_INSTALL_SCRIPTS = {
    "sharp@0.34.5",
    "unrs-resolver@1.12.2",
    "fsevents@2.3.2",
    "fsevents@2.3.3",
}

PRODUCT_TERMS_BLOCKED_IN_FRONTEND_SCAFFOLD = [
    "upload markdown",
    "generate script",
    "grounded walkthrough",
    "avatar rendering",
    "provider key",
    "rag ingestion",
]

PRODUCT_TERMS_BLOCKED_IN_BACKEND_SCAFFOLD = [
    "upload",
    "ingest",
    "chunk",
    "embedding",
    "generate_script",
    "avatar",
    "provider key",
]

ENV_DEFAULTS = {
    "DATABASE_URL=postgresql://narratwin:narratwin_local@127.0.0.1:5432/narratwin",
    "REDIS_URL=redis://:narratwin_redis_local@127.0.0.1:6379/0",
    "STORAGE_PROVIDER=local",
    "LOCAL_STORAGE_ROOT=./outputs",
    "VECTOR_STORE=disabled",
    "LLM_PROVIDER=mock",
    "EMBEDDING_PROVIDER=mock",
    "EVALUATION_PROVIDER=mock",
}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def changed_files_for_stage_scope() -> list[str]:
    base_candidates = [os.environ.get("GITHUB_BASE_SHA", "").strip(), "origin/main", "main"]
    merge_base = None
    attempted: list[str] = []
    for candidate in [item for item in base_candidates if item]:
        attempted.append(candidate)
        result = run(["git", "merge-base", candidate, "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
    if merge_base is None:
        raise RuntimeError(f"git merge-base failed for Stage 3 scope. Tried: {', '.join(attempted)}")

    outputs: list[str] = []
    for args in (
        ["git", "diff", "--name-only", f"{merge_base}..HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        result = run(args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")
        outputs.append(result.stdout)

    return sorted({line.strip() for output in outputs for line in output.splitlines() if line.strip()})


def current_branch() -> str:
    result = run(["git", "branch", "--show-current"])
    return result.stdout.strip() if result.returncode == 0 else ""


def package_names(values: list[str]) -> set[str]:
    names = set()
    for value in values:
        name = re.split(r"[<>=!~\[]", value, maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)
    return names


def check_required_files(failures: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            fail(f"Missing required Stage 3 file: {rel}", failures)


def check_stage_marker_and_branch(failures: list[str]) -> None:
    marker = read(".stage/current").strip() if (ROOT / ".stage/current").exists() else ""
    if marker != "3":
        fail(".stage/current must contain 3 for Stage 3.", failures)

    branch = current_branch()
    if branch and branch != "main" and not STAGE3_BRANCH_PATTERN.match(branch):
        fail(f"Stage 3 branch must start with stage3-. Current branch: {branch}", failures)


def check_stage_scope(failures: list[str]) -> None:
    for rel in changed_files_for_stage_scope():
        if rel not in STAGE3_ALLOWED_FILES:
            fail(f"Stage 3 changed file outside the allowlist: {rel}", failures)
        for pattern in BLOCKED_STAGE3_PATTERNS:
            if pattern.search(rel):
                fail(f"Stage 3 must not add blocked implementation/runtime path: {rel}", failures)


def check_python_manifest(failures: list[str]) -> None:
    data = tomllib.loads(read("pyproject.toml"))
    project = data.get("project", {})
    dependencies = package_names(project.get("dependencies", []))
    missing_dependencies = sorted(PYTHON_DEPENDENCIES - dependencies)
    if missing_dependencies:
        fail(f"pyproject.toml missing Stage 3 dependencies: {', '.join(missing_dependencies)}", failures)

    dependency_groups = data.get("dependency-groups", {})
    dev_dependencies = package_names(dependency_groups.get("dev", []))
    missing_dev = sorted(PYTHON_DEV_DEPENDENCIES - dev_dependencies)
    if missing_dev:
        fail(f"pyproject.toml missing Stage 3 dev dependencies: {', '.join(missing_dev)}", failures)

    if "gitleaks" in dependencies or "gitleaks" in dev_dependencies:
        fail("gitleaks must not be recorded as a Python dependency; use the CLI/action path.", failures)


def check_env_defaults(failures: list[str]) -> None:
    text = read(".env.example")
    for expected in sorted(ENV_DEFAULTS):
        if expected not in text:
            fail(f".env.example missing Stage 3 local/mock default: {expected}", failures)
    if "VECTOR_STORE=chroma" in text or "CHROMA_PATH=" in text:
        fail("Stage 3 must not default to Chroma before the Stage 4 vector-store decision is locked.", failures)


def check_frontend_manifest(failures: list[str]) -> None:
    data = json.loads(read("frontend/package.json"))
    dependencies = set(data.get("dependencies", {}))
    dev_dependencies = set(data.get("devDependencies", {}))
    scripts = set(data.get("scripts", {}))

    missing_dependencies = sorted(FRONTEND_DEPENDENCIES - dependencies)
    if missing_dependencies:
        fail(f"frontend/package.json missing dependencies: {', '.join(missing_dependencies)}", failures)

    missing_dev = sorted(FRONTEND_DEV_DEPENDENCIES - dev_dependencies)
    if missing_dev:
        fail(f"frontend/package.json missing dev dependencies: {', '.join(missing_dev)}", failures)

    missing_scripts = sorted(FRONTEND_SCRIPTS - scripts)
    if missing_scripts:
        fail(f"frontend/package.json missing scripts: {', '.join(missing_scripts)}", failures)

    if "vite" in dependencies or "vite" in dev_dependencies:
        fail("Stage 3 frontend foundation must follow the documented Next.js decision, not Vite.", failures)

    overrides = data.get("overrides", {})
    if overrides.get("postcss") != "^8.5.16":
        fail("frontend/package.json must keep the PostCSS security override pinned to ^8.5.16.", failures)

    allow_scripts = data.get("allowScripts", {})
    if set(allow_scripts) != FRONTEND_ALLOWED_INSTALL_SCRIPTS or not all(allow_scripts.values()):
        fail("frontend/package.json must explicitly allow only the reviewed install-script packages.", failures)


def check_ci_wrappers(failures: list[str]) -> None:
    required_commands = {
        "scripts/ci/backend-lint.sh": ["uv run ruff check", "uv run mypy"],
        "scripts/ci/backend-test.sh": ["uv run pytest", "py_compile"],
        "scripts/ci/docker-build.sh": ["docker build -f backend/Dockerfile", "docker build -f frontend/Dockerfile"],
        "scripts/ci/eval-smoke.sh": ["uv run python"],
        "scripts/ci/frontend-build.sh": [
            "npm ci --strict-allow-scripts=true",
            "npm run lint",
            "npm run typecheck",
            "npm test",
            "npm run build",
        ],
        "scripts/ci/frontend-smoke.sh": [
            "npm ci --strict-allow-scripts=true",
            "playwright install",
            "npm run test:smoke",
        ],
        "scripts/ci/dependency-security.sh": [
            "uv run pip-audit",
            "uv run bandit",
            "uv run semgrep",
            "npm --prefix frontend audit --audit-level=high",
            "gitleaks",
            "NARRATWIN_ALLOW_LOCAL_SECRET_SCAN_FALLBACK",
        ],
    }
    required_phrases = {
        "scripts/ci/eval-smoke.sh": ["stage3_health_fixture.json", "eval smoke report", "eval smoke passed"],
        "scripts/ci/dependency-security.sh": ["scripts/guardrails_check.py"],
    }
    for rel, commands in required_commands.items():
        text = read(rel)
        if not text.startswith("#!/usr/bin/env bash\nset -euo pipefail\n"):
            fail(f"{rel} must use the standard bash safety header.", failures)
        effective_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("echo ")
        ]
        for command in commands:
            if not any(command in line for line in effective_lines):
                fail(f"{rel} missing required executable command: {command}", failures)
    for rel, phrases in required_phrases.items():
        text = read(rel)
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} missing required phrase: {phrase}", failures)


def check_guardrails_scan_untracked_files(failures: list[str]) -> None:
    text = read("scripts/guardrails_check.py")
    required = ['run_git(["ls-files", "--others", "--exclude-standard"])', "tracked, untracked"]
    for phrase in required:
        if phrase not in text:
            fail(f"scripts/guardrails_check.py must scan untracked files; missing {phrase}", failures)


def text_files_under(*roots: str) -> list[Path]:
    suffixes = {".css", ".js", ".json", ".mjs", ".py", ".sh", ".ts", ".tsx", ".yml", ".yaml"}
    files: list[Path] = []
    for root in roots:
        base = ROOT / root
        if base.is_file() and base.suffix in suffixes:
            files.append(base)
            continue
        if not base.exists():
            continue
        files.extend(
            item
            for item in base.rglob("*")
            if item.is_file()
            and item.suffix in suffixes
            and "node_modules" not in item.parts
            and ".next" not in item.parts
        )
    return files


def check_frontend_scaffold_is_not_product_feature(failures: list[str]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in text_files_under("frontend/src", "frontend/tests"))
    for term in PRODUCT_TERMS_BLOCKED_IN_FRONTEND_SCAFFOLD:
        if term in text:
            fail(f"Stage 3 frontend scaffold contains product feature term: {term}", failures)


def check_backend_scaffold_is_health_only(failures: list[str]) -> None:
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in text_files_under("backend", "tests/api", "tests/unit"))
    for term in PRODUCT_TERMS_BLOCKED_IN_BACKEND_SCAFFOLD:
        if term in text:
            fail(f"Stage 3 backend scaffold contains product feature term: {term}", failures)
    main_text = read("backend/app/main.py")
    for required in (
        "FastAPI",
        "/healthz",
        "/readyz",
        "/api/v1/healthz",
        "/api/v1/readyz",
        "HealthResponse",
        "ErrorResponse",
        "requestId",
    ):
        if required not in main_text:
            fail(f"backend/app/main.py missing health-only foundation phrase: {required}", failures)
    for header in ("X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy", "Referrer-Policy"):
        if header not in main_text:
            fail(f"backend/app/main.py missing baseline security header: {header}", failures)


def check_workflows(failures: list[str]) -> None:
    required_phrases = {
        ".github/workflows/ci.yml": [
            "Backend lint and typecheck",
            "Backend unit and API tests",
            "Playwright smoke",
            "ci / docker build",
        ],
        ".github/workflows/security.yml": [
            "Gitleaks secret scan",
            "Bandit, dependency audit, Semgrep",
            "NARRATWIN_GITLEAKS_ACTION_COMPLETED",
        ],
        ".github/workflows/eval-smoke.yml": ["Run eval smoke"],
        ".github/workflows/quality.yml": ["quality / markdown"],
        ".github/workflows/quality-gates.yml": ["Run repository guardrails", "Run stage quality gate"],
    }
    for rel, phrases in required_phrases.items():
        text = read(rel)
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} missing required gate phrase: {phrase}", failures)

    for path in sorted((ROOT / ".github/workflows").glob("*.yml")) + sorted(
        (ROOT / ".github/workflows").glob("*.yaml")
    ):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        if "permissions:\n  contents: read" not in text:
            fail(f"{rel} must declare least-privilege contents: read permissions.", failures)
        for match in re.finditer(r"uses:\s*[^@\s]+@([^\s#]+)", text):
            ref = match.group(1)
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                fail(f"{rel} must pin GitHub Actions by immutable SHA, found: {match.group(0)}", failures)
        if re.search(r"\bnpm\s+(?:ci|install)\b(?![^\n]*--strict-allow-scripts=true)", text):
            fail(f"{rel} must not run npm install commands without --strict-allow-scripts=true.", failures)
        if "python -m pip install --upgrade uv" in text:
            fail(f"{rel} must pin uv instead of installing the latest version.", failures)
        if rel != ".github/workflows/quality-gates.yml" and "python -m pip install uv==0.11.18" in text and "uv sync --frozen" not in text:
            fail(f"{rel} installs uv but does not use frozen dependency sync.", failures)


def check_docker_and_precommit(failures: list[str]) -> None:
    required_phrases = {
        "docker-compose.yml": [
            "backend:",
            "frontend:",
            "postgres:",
            "redis:",
            "backend-data:",
            "postgres-data:",
            "redis-data:",
            "127.0.0.1:8000:8000",
            "127.0.0.1:3000:3000",
            "@sha256:",
            "no-new-privileges:true",
            "condition: service_healthy",
            "VECTOR_STORE: disabled",
        ],
        "backend/Dockerfile": [
            "@sha256:",
            "uv==0.11.18",
            "uv sync --frozen --no-dev",
            "uvicorn",
            "backend.app.main:app",
            "USER appuser",
        ],
        "frontend/Dockerfile": [
            "@sha256:",
            "NPM_CONFIG_STRICT_ALLOW_SCRIPTS=true",
            "npm ci --strict-allow-scripts=true",
            "npm run build",
            "server.js",
            "USER node",
        ],
        ".pre-commit-config.yaml": ["ruff check", "mypy", "pytest", "frontend lint"],
        "frontend/tests/smoke.spec.ts": [
            "content-security-policy",
            "referrer-policy",
            "x-content-type-options",
            "x-frame-options",
        ],
        "semgrep.yml": ["python-subprocess-shell-true", "react-dangerously-set-inner-html"],
    }
    for rel, phrases in required_phrases.items():
        text = read(rel)
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} missing required Stage 3 phrase: {phrase}", failures)


def check_docs(failures: list[str]) -> None:
    required_phrases = {
        "docs/QUALITY_GATES.md": ["Stage 3 quality is executable", "dependency/security scan path"],
        "docs/RECOMMENDED_REVIEW_ITEMS.md": ["RR-001", "RR-004", "Accepted Non-blocking"],
        "docs/STAGE_ISSUE_PLAN.md": [
            "Stage 3 Repo Foundation And CI/CD Branch Scope",
            "pyproject.toml",
            "frontend/.gitignore",
            "docs/REPOSITORY_GUARDRAILS.md",
            "docs/SKILL_LOCK.md",
        ],
        "docs/STATUS.md": ["Current stage marker: `.stage/current = 3`", "Stage 3"],
        "docs/TRACEABILITY.md": ["Stage 3 frontend foundation", "health checks"],
        "docs/ADR/0001-system-architecture.md": ["Stage 3 foundation"],
        "docs/LOCAL_DEVELOPMENT.md": [
            "uv sync --frozen",
            "npm --prefix frontend ci --strict-allow-scripts=true",
            "NARRATWIN_ALLOW_LOCAL_SECRET_SCAN_FALLBACK",
            "make stage3-quality",
        ],
        "docs/THIRD_PARTY_NOTICES.md": [
            "FastAPI",
            "Next.js",
            "Vitest",
            "Playwright",
            "pip-audit",
            "Semgrep",
            "PostCSS",
            "allowScripts",
        ],
    }
    for rel, phrases in required_phrases.items():
        text = read(rel)
        for phrase in phrases:
            if phrase not in text:
                fail(f"{rel} missing required Stage 3 phrase: {phrase}", failures)


def check_python_scripts_compile(failures: list[str]) -> None:
    for rel in [
        "scripts/guardrails_check.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/check_recommended_review_items.py",
        "scripts/quality/check_stage3_docs.py",
        "backend/app/main.py",
    ]:
        result = run([sys.executable, "-m", "py_compile", rel])
        if result.returncode != 0:
            fail(f"{rel} does not compile: {result.stderr.strip()}", failures)


def check_diff_whitespace(failures: list[str]) -> None:
    result = run(["git", "diff", "--check"])
    if result.returncode != 0:
        fail(result.stdout.strip() or "git diff --check failed.", failures)


def main() -> int:
    failures: list[str] = []

    check_required_files(failures)
    if not failures:
        check_stage_marker_and_branch(failures)
        check_stage_scope(failures)
        check_env_defaults(failures)
        check_python_manifest(failures)
        check_frontend_manifest(failures)
        check_ci_wrappers(failures)
        check_guardrails_scan_untracked_files(failures)
        check_backend_scaffold_is_health_only(failures)
        check_frontend_scaffold_is_not_product_feature(failures)
        check_workflows(failures)
        check_docker_and_precommit(failures)
        check_docs(failures)
        check_python_scripts_compile(failures)
        check_diff_whitespace(failures)

    if failures:
        print("Stage 3 quality failures:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Stage 3 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
