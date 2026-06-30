#!/usr/bin/env python3
"""Executable Stage 4 quality gate for the first grounded-script slice."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE4_BRANCH_PATTERN = re.compile(r"^stage4-")

REQUIRED_FILES = [
    ".stage/current",
    ".github/workflows/eval-smoke.yml",
    "Makefile",
    "backend/app/main.py",
    "backend/app/rag/__init__.py",
    "backend/app/stage4.py",
    "backend/app/rag/chunking.py",
    "backend/app/rag/grounding.py",
    "backend/app/rag/models.py",
    "backend/app/rag/providers.py",
    "backend/app/rag/retrieval.py",
    "backend/app/rag/store.py",
    "tests/fixtures/stage4_project.md",
    "tests/unit/test_chunking.py",
    "tests/unit/test_retrieval_and_grounding.py",
    "tests/api/test_stage4_slice_api.py",
    "evals/smoke/stage4_grounded_script_dataset.json",
    "scripts/ci/eval-smoke.sh",
    "frontend/src/app/page.tsx",
    "frontend/src/app/page.module.css",
    "frontend/src/app/page.test.tsx",
    "frontend/tests/smoke.spec.ts",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/ADR/0002-rag-storage.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_MODEL.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/QUALITY_GATES.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
]

STAGE4_ALLOWED_FILES = set(REQUIRED_FILES) | {
    "pyproject.toml",
    "uv.lock",
    "frontend/playwright.config.ts",
    "tests/api/test_health_api.py",
    "tests/unit/test_health_contract.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage4_docs.py",
}

BLOCKED_STAGE4_PATTERNS = [
    re.compile(r"(^|/)(avatar|tts|voice|video|rendering|heygen|elevenlabs|tavus|wav2lip)(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)(terraform|infra)(/|$)", re.IGNORECASE),
]

REQUIRED_DIRECT_DEPENDENCIES = {
    "beautifulsoup4",
    "markdown",
    "pgvector",
    "pypdf",
    "python-docx",
    "tiktoken",
}

REQUIRED_OPTIONAL_DEPENDENCIES = {
    "datasets",
    "litellm",
    "openai",
    "sentence-transformers",
}

BLOCKED_DEPENDENCIES = {
    "elevenlabs",
    "heygen",
    "sadtalker",
    "tavus",
    "wav2lip",
}


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except subprocess.CalledProcessError:
        return ""


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def changed_files_for_stage_scope() -> list[str]:
    base_candidates = [os.environ.get("GITHUB_BASE_SHA", "").strip(), "origin/main", "main"]
    merge_base = ""
    for candidate in [item for item in base_candidates if item]:
        result = run(["git", "merge-base", candidate, "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
    if not merge_base:
        raise RuntimeError("git merge-base failed for Stage 4 scope.")

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


def check_required_files(failures: list[str]) -> None:
    for rel_path in REQUIRED_FILES:
        if not (ROOT / rel_path).is_file():
            fail(f"Missing required Stage 4 file: {rel_path}", failures)


def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "4":
        fail(".stage/current must contain 4 for Stage 4 quality.", failures)
    branch = run_git(["branch", "--show-current"])
    if branch and branch != "main" and not STAGE4_BRANCH_PATTERN.match(branch):
        fail(f"Stage 4 work must run on a stage4-* branch or main after merge; got {branch}.", failures)


def check_stage_scope(failures: list[str]) -> None:
    for rel_path in changed_files_for_stage_scope():
        if rel_path not in STAGE4_ALLOWED_FILES:
            fail(f"Stage 4 changed file outside the allowlist: {rel_path}", failures)
        for pattern in BLOCKED_STAGE4_PATTERNS:
            if pattern.search(rel_path):
                fail(f"Stage 4 Slice 1 must not include blocked avatar/TTS/video/infra scope: {rel_path}", failures)


def check_dependencies(failures: list[str]) -> None:
    data = tomllib.loads(read("pyproject.toml"))
    dependencies = {
        str(raw).split(">=", maxsplit=1)[0].split("==", maxsplit=1)[0].lower()
        for raw in data.get("project", {}).get("dependencies", [])
    }
    optional_dependencies = {
        str(raw).split(">=", maxsplit=1)[0].split("==", maxsplit=1)[0].lower()
        for values in data.get("project", {}).get("optional-dependencies", {}).values()
        for raw in values
    }
    missing = REQUIRED_DIRECT_DEPENDENCIES - dependencies
    if missing:
        fail(f"Missing required Stage 4 direct dependencies: {sorted(missing)}", failures)
    missing_optional = REQUIRED_OPTIONAL_DEPENDENCIES - optional_dependencies
    if missing_optional:
        fail(f"Missing required Stage 4 optional dependencies: {sorted(missing_optional)}", failures)
    blocked = BLOCKED_DEPENDENCIES & dependencies
    if blocked:
        fail(f"Stage 4 Slice 1 must not include avatar/TTS/video dependencies: {sorted(blocked)}", failures)


def check_backend_contracts(failures: list[str]) -> None:
    main_text = read("backend/app/main.py")
    stage4_text = read("backend/app/stage4.py")
    grounding_text = read("backend/app/rag/grounding.py")
    provider_text = read("backend/app/rag/providers.py")
    for route in (
        "/api/v1/projects",
        "knowledge-documents",
        "ingestion-runs",
        "walkthrough-runs",
    ):
        if route not in main_text:
            fail(f"Missing Stage 4 API route marker: {route}", failures)
    for required in (
        "MockEmbeddingProvider",
        "MockLLMProvider",
        "retrieve_context",
        "evaluate_grounding",
        "unsupported_claim_count",
        "policyVersion",
        "schemaVersion",
        "safetyPolicyVersion",
    ):
        if required not in stage4_text + grounding_text + provider_text:
            fail(f"Stage 4 backend must include {required}.", failures)
    if "source_filename=file.filename" not in main_text:
        fail("Upload endpoint must preserve sanitized source filename metadata.", failures)
    if "UNSUPPORTED_MEDIA_TYPE" not in stage4_text:
        fail("Upload validation must reject unsupported media types.", failures)


def check_tests_and_eval(failures: list[str]) -> None:
    expected_test_terms = {
        "tests/unit/test_chunking.py": "chunk_document",
        "tests/unit/test_retrieval_and_grounding.py": "evaluate_grounding",
        "tests/api/test_stage4_slice_api.py": "walkthrough-runs",
        "frontend/tests/smoke.spec.ts": "Grounded script generation",
    }
    for rel_path, term in expected_test_terms.items():
        if term not in read(rel_path):
            fail(f"{rel_path} must cover {term}.", failures)
    fixture = json.loads(read("evals/smoke/stage4_grounded_script_dataset.json"))
    if fixture.get("expected", {}).get("unsupportedClaimCount") != 0:
        fail("Stage 4 eval smoke fixture must require zero unsupported claims.", failures)
    eval_script = read("scripts/ci/eval-smoke.sh")
    for term in ("stage4_grounded_script_dataset.json", "unsupportedClaimCount", "contextRefs"):
        if term not in eval_script:
            fail(f"Stage 4 eval smoke must validate {term}.", failures)


def check_docs(failures: list[str]) -> None:
    status = read("docs/STATUS.md")
    notices = read("docs/THIRD_PARTY_NOTICES.md")
    traceability = read("docs/TRACEABILITY.md")
    review_items = read("docs/RECOMMENDED_REVIEW_ITEMS.md")
    for term in ("stage4-grounded-script-generation", "Stage 4", "make stage4-quality"):
        if term not in status:
            fail(f"docs/STATUS.md must record {term}.", failures)
    for dependency in sorted(REQUIRED_DIRECT_DEPENDENCIES):
        if dependency not in notices.lower():
            fail(f"docs/THIRD_PARTY_NOTICES.md must record {dependency}.", failures)
    for deferred in ("chromadb", "ragas"):
        if deferred not in notices.lower() or "deferred" not in notices.lower():
            fail(f"docs/THIRD_PARTY_NOTICES.md must record deferred decision for {deferred}.", failures)
    if "Stage 4 First Slice Traceability" not in traceability:
        fail("docs/TRACEABILITY.md must include Stage 4 first slice traceability.", failures)
    for item_id in ("RR-005", "RR-009", "RR-010", "RR-011", "RR-012", "RR-013"):
        row = next((line for line in review_items.splitlines() if line.startswith(f"| {item_id} ")), "")
        if "| Open |" in row or "| In Progress |" in row:
            fail(f"{item_id} must be resolved, accepted, or superseded for Stage 4.", failures)


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    if failures:
        print("Stage 4 quality failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    check_stage_marker_and_branch(failures)
    check_stage_scope(failures)
    check_dependencies(failures)
    check_backend_contracts(failures)
    check_tests_and_eval(failures)
    check_docs(failures)

    if failures:
        print("Stage 4 quality failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Stage 4 static quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
