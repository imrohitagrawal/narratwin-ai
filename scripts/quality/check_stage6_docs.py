#!/usr/bin/env python3
"""Executable Stage 6 quality gate for multilingual scripts, subtitles, and voice adapters."""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE6_BRANCH_PATTERN = re.compile(r"^stage6-")

REQUIRED_FILES = [
    ".stage/current",
    "Makefile",
    "backend/app/main.py",
    "backend/app/stage4.py",
    "backend/app/stage6.py",
    "frontend/src/app/page.tsx",
    "frontend/src/app/page.module.css",
    "frontend/src/app/page.test.tsx",
    "frontend/tests/smoke.spec.ts",
    "tests/unit/test_stage6_multilingual.py",
    "tests/api/test_stage6_multilingual_api.py",
    "tests/unit/test_health_contract.py",
    "tests/api/test_health_api.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage6_docs.py",
    "docs/API_CONTRACT.md",
    "docs/ADR/0002-provider-agnostic-adapters.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
    "pyproject.toml",
    "uv.lock",
]

STAGE6_ALLOWED_FILES = set(REQUIRED_FILES) | {
    "scripts/quality/check_recommended_review_items.py",
}

REQUIRED_DIRECT_DEPENDENCIES = {
    "audioop-lts",
    "babel",
    "langcodes",
    "pydub",
    "srt",
}

BLOCKED_DEPENDENCIES = {
    "elevenlabs",
    "heygen",
    "sadtalker",
    "tavus",
    "wav2lip",
}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def changed_files_for_stage_scope() -> list[str]:
    base_candidates = [os.environ.get("GITHUB_BASE_SHA", "").strip(), "origin/main", "main"]
    merge_base = ""
    for candidate in [item for item in base_candidates if item]:
        result = run(["git", "merge-base", candidate, "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
    if not merge_base:
        raise RuntimeError("git merge-base failed for Stage 6 scope.")

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
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            fail(f"Missing required Stage 6 file: {path}", failures)


def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "6":
        fail(".stage/current must contain 6 for Stage 6 quality.", failures)

    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch and branch != "main" and not STAGE6_BRANCH_PATTERN.match(branch):
        fail(f"Stage 6 work must run on a stage6-* branch or main after merge; got {branch}.", failures)


def check_stage_scope(failures: list[str]) -> None:
    for path in changed_files_for_stage_scope():
        if path not in STAGE6_ALLOWED_FILES:
            fail(f"Stage 6 changed file outside the allowlist: {path}", failures)


def check_dependencies(failures: list[str]) -> None:
    data = tomllib.loads(read("pyproject.toml"))
    dependencies = {
        re.split(r"[<>=!~\[]", value, maxsplit=1)[0].strip().lower()
        for value in data.get("project", {}).get("dependencies", [])
    }
    missing = REQUIRED_DIRECT_DEPENDENCIES - dependencies
    if missing:
        fail(f"Missing required Stage 6 direct dependencies: {sorted(missing)}", failures)
    blocked = BLOCKED_DEPENDENCIES & dependencies
    if blocked:
        fail(f"Stage 6 must not add paid/avatar provider dependencies: {sorted(blocked)}", failures)


def check_backend_contracts(failures: list[str]) -> None:
    main_text = read("backend/app/main.py")
    stage6_text = read("backend/app/stage6.py")
    for marker in (
        "multilingual-runs",
        "GenerateMultilingualWalkthroughRequest",
        "MultilingualWalkthroughResponse",
        "Stage6Error",
    ):
        if marker not in main_text:
            fail(f"Stage 6 API must include {marker}.", failures)
    for marker in (
        "TranslationProvider",
        "TTSProvider",
        "MockTranslationProvider",
        "MockTTSProvider",
        "Stage6IdempotencyRecord",
        "IDEMPOTENCY_IN_PROGRESS",
        "MAX_IDEMPOTENCY_RECORDS_PER_SCOPE",
        "validate_translation_output",
        "validate_voice_manifest_artifact",
        "is_safe_artifact_filename",
        "PROVIDER_OUTPUT_INVALID",
        "PROVIDER_OUTPUT_TOO_LARGE",
        "generate_subtitles",
        "MAX_CAPTION_COUNT",
        "multilingual_to_api",
        "UNSUPPORTED_LANGUAGE",
        "REQUESTED_PROVIDER_UNAVAILABLE",
        "application/x-subrip",
        "content_base64",
        "source_citation_count",
    ):
        if marker not in stage6_text:
            fail(f"Stage 6 backend must include {marker}.", failures)
    if any(provider in stage6_text.lower() for provider in BLOCKED_DEPENDENCIES):
        fail("Stage 6 backend must not hardcode paid provider names.", failures)


def check_tests_and_frontend(failures: list[str]) -> None:
    unit_tests = read("tests/unit/test_stage6_multilingual.py")
    api_tests = read("tests/api/test_stage6_multilingual_api.py")
    frontend_page = read("frontend/src/app/page.tsx")
    frontend_test = read("frontend/src/app/page.test.tsx")
    smoke_test = read("frontend/tests/smoke.spec.ts")
    for marker in (
        "preserves_project_terms",
        "subtitle_timing_format_is_valid_subrip",
        "falls_back_to_mock_provider",
        "unsupported_language",
        "concurrent_duplicate_idempotency_key_is_rejected_in_flight",
        "provider_output_must_preserve_glossary_terms",
        "provider_output_must_preserve_source_citation_markers",
        "tts_provider_output_must_be_a_valid_json_manifest_artifact",
        "caption_splitting_bounds_single_long_tokens",
        "accepts_non_mock_local_translation_adapter",
        "rejects_oversized_boundary_fields",
        "rejects_whitespace_only_glossary_terms",
    ):
        if marker not in unit_tests + api_tests:
            fail(f"Stage 6 tests must cover {marker}.", failures)
    for marker in (
        "Target language",
        "glossaryTerms",
        "Download script",
        "Download subtitles",
        "multilingual-runs",
        "multilingualSeed",
        "allowedArtifactMimeTypes",
        "safeArtifactFileName",
        "rejects unsafe artifact filenames",
        "button type=\"button\" disabled",
    ):
        if marker not in frontend_page + frontend_test + smoke_test:
            fail(f"Stage 6 frontend must expose {marker}.", failures)


def check_docs(failures: list[str]) -> None:
    docs = {
        path: read(path)
        for path in (
            "docs/API_CONTRACT.md",
            "docs/ADR/0002-provider-agnostic-adapters.md",
            "docs/QUALITY_GATES.md",
            "docs/RECOMMENDED_REVIEW_ITEMS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/THIRD_PARTY_NOTICES.md",
            "docs/TRACEABILITY.md",
        )
    }
    combined = "\n".join(docs.values())
    if "Stage: Stage 6 multilingual scripts, subtitles, voice adapter" not in docs["docs/API_CONTRACT.md"]:
        fail("API contract metadata must identify Stage 6.", failures)
    if "Last updated: 2026-07-01" not in docs["docs/TRACEABILITY.md"]:
        fail("Traceability metadata must be current for Stage 6.", failures)
    for marker in (
        "Stage 6",
        "multilingual-runs",
        "TranslationProvider",
        "TTSProvider",
        "subtitle",
        "accessibility",
        "mock/local",
        "downloadable",
        "IDEMPOTENCY_IN_PROGRESS",
        "PROVIDER_OUTPUT_INVALID",
        "PROVIDER_OUTPUT_TOO_LARGE",
        "provider-output validation",
        "request boundary",
        "does not synthesize real audio",
        "does not clone voices",
        "Voice provider artifacts must be JSON manifests",
        "safe filename",
        "Provider response schema",
        "audioop-lts",
        "RR-029",
        "RR-030",
        "RR-031",
    ):
        if marker not in combined:
            fail(f"Stage 6 docs must mention {marker}.", failures)


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    check_stage_marker_and_branch(failures)
    check_stage_scope(failures)
    check_dependencies(failures)
    check_backend_contracts(failures)
    check_tests_and_frontend(failures)
    check_docs(failures)

    if failures:
        print("Stage 6 quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Stage 6 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
