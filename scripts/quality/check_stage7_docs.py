#!/usr/bin/env python3
"""Executable Stage 7 quality gate for avatar rendering and demo export."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE7_BRANCH_PATTERN = re.compile(r"^stage7-")

REQUIRED_FILES = [
    ".stage/current",
    "Makefile",
    "backend/app/main.py",
    "backend/app/stage7.py",
    "frontend/src/app/page.tsx",
    "frontend/src/app/page.module.css",
    "frontend/src/app/page.test.tsx",
    "frontend/tests/smoke.spec.ts",
    "tests/unit/test_stage7_avatar.py",
    "tests/api/test_stage7_avatar_api.py",
    "tests/unit/test_health_contract.py",
    "tests/api/test_health_api.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage7_docs.py",
    "docs/API_CONTRACT.md",
    "docs/ADR/0002-provider-agnostic-adapters.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/SKILL_LOCK.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
]

STAGE7_ALLOWED_FILES = set(REQUIRED_FILES) | {
    "scripts/quality/check_recommended_review_items.py",
}

BLOCKED_DEPENDENCIES = {
    "d-id",
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
        raise RuntimeError("git merge-base failed for Stage 7 scope.")

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
            fail(f"Missing required Stage 7 file: {path}", failures)


def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "7":
        fail(".stage/current must contain 7 for Stage 7 quality.", failures)

    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch and branch != "main" and not STAGE7_BRANCH_PATTERN.match(branch):
        fail(f"Stage 7 work must run on a stage7-* branch or main after merge; got {branch}.", failures)


def check_stage_scope(failures: list[str]) -> None:
    for path in changed_files_for_stage_scope():
        if path not in STAGE7_ALLOWED_FILES:
            fail(f"Stage 7 changed file outside the allowlist: {path}", failures)


def check_backend_contracts(failures: list[str]) -> None:
    main_text = read("backend/app/main.py")
    stage7_text = read("backend/app/stage7.py")
    for marker in (
        "avatar-renders",
        "GenerateAvatarRenderRequest",
        "AvatarRenderResponse",
        "Stage7Error",
        "stage7_service.reset",
        'stage="7"',
    ):
        if marker not in main_text:
            fail(f"Stage 7 API must include {marker}.", failures)
    for marker in (
        "AvatarProvider",
        "MockAvatarProvider",
        "ExternalAvatarProviderStub",
        "ProviderConfig",
        "RenderJobStatusEvent",
        "render_job_status_history",
        "video_export_placeholder",
        "avatar_renders",
        "artifact_metadata",
        "Stage7IdempotencyRecord",
        "IDEMPOTENCY_IN_PROGRESS",
        "MAX_IDEMPOTENCY_RECORDS_PER_SCOPE",
        "CLONED_IDENTITY_DISABLED",
        "AVATAR_CONSENT_REQUIRED",
        "REQUESTED_PROVIDER_UNAVAILABLE",
        "PROVIDER_RENDER_FAILED",
        "PROVIDER_OUTPUT_INVALID",
        "PROVIDER_OUTPUT_TOO_LARGE",
        "ACTIVE_HTML_PATTERN",
        "validate_provider_result",
        "validate_provider_config",
        "validate_provider_metadata_matches_config",
        "validate_fallback_reason",
        "validate_export_artifact",
        "validate_demo_html_export",
        "validate_render_manifest",
        "validate_video_export_placeholder",
        "expected_render_manifest_payload",
        "expected_video_export_placeholder_payload",
        "source_context_ref_ids",
        "source_citation_indexes",
        "source_evaluation_checksum",
        "PUBLIC_USE_LICENSE_CHECK",
        "is_safe_artifact_filename",
        "text/html",
        "application/json",
        "local-html",
        "aiGenerated",
        "source_citation_count",
        "evaluation_status",
        "avatar_render_to_api",
    ):
        if marker not in stage7_text:
            fail(f"Stage 7 backend must include {marker}.", failures)
    if any(provider in stage7_text.lower() for provider in BLOCKED_DEPENDENCIES):
        fail("Stage 7 backend must not hardcode paid or restricted avatar provider names.", failures)


def check_tests_and_frontend(failures: list[str]) -> None:
    unit_tests = read("tests/unit/test_stage7_avatar.py")
    api_tests = read("tests/api/test_stage7_avatar_api.py")
    frontend_page = read("frontend/src/app/page.tsx")
    frontend_test = read("frontend/src/app/page.test.tsx")
    smoke_test = read("frontend/tests/smoke.spec.ts")
    for marker in (
        "valid_demo_export_with_disclosure",
        "falls_back_to_mock_local_provider",
        "cloned_identity_request_is_disabled",
        "synthetic_avatar_consent_is_required",
        "provider_artifacts_must_use_safe_expected_export_shapes",
        "provider_config_is_validated_before_artifacts_are_stored",
        "external_stub_config_cannot_produce_successful_stage7_output",
        "malformed_provider_output_is_rejected_without_server_error",
        "provider_html_export_rejects_active_content",
        "provider_html_export_must_exactly_match_trusted_renderer",
        "provider_mode_must_match_validated_provider_config",
        "provider_fallback_reason_is_enum_validated",
        "render_manifest_must_match_trusted_source_and_disclosure",
        "render_manifest_rejects_unexpected_provider_metadata_fields",
        "video_placeholder_rejects_unexpected_provider_metadata_fields",
        "unexpected_provider_exception_uses_mock_fallback",
        "failed_provider_uses_mock_fallback",
        "concurrent_duplicate_avatar_idempotency_key_is_rejected_in_flight",
        "failed_avatar_idempotency_key_replays_terminal_failure_without_retry",
        "avatar_consent_failure_idempotency_key_replays_terminal_failure",
        "avatar_validation_failure_idempotency_key_conflicts_on_changed_request",
        "returns_validated_demo_export_artifacts",
        "requires_synthetic_avatar_consent",
        "requires_evaluation_evidence",
        "replays_matching_idempotency_key",
    ):
        if marker not in unit_tests + api_tests:
            fail(f"Stage 7 tests must cover {marker}.", failures)
    for marker in (
        "Avatar demo export",
        "Generate avatar demo export",
        "Synthetic avatar consent",
        "Download avatar demo",
        "Download render manifest",
        "Download video placeholder",
        "Demo preview",
        "Export artifacts",
        "artifactSafetyState",
        "artifactBlockReason",
        "sha256Hex",
        "avatarRender?.sourceScriptText",
        "avatar-renders",
        "avatarSeed",
        "allowedArtifactMimeTypes",
        "safeArtifactFileName",
        "text/html",
        "application/json",
        "local-html",
    ):
        if marker not in frontend_page + frontend_test + smoke_test:
            fail(f"Stage 7 frontend must expose {marker}.", failures)


def check_docs(failures: list[str]) -> None:
    docs = {
        path: read(path)
        for path in (
            "docs/API_CONTRACT.md",
            "docs/ADR/0002-provider-agnostic-adapters.md",
            "docs/QUALITY_GATES.md",
            "docs/RECOMMENDED_REVIEW_ITEMS.md",
            "docs/SKILL_LOCK.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/THIRD_PARTY_NOTICES.md",
            "docs/TRACEABILITY.md",
        )
    }
    combined = "\n".join(docs.values())
    if "Stage: Stage 7 avatar rendering adapter and export" not in docs["docs/API_CONTRACT.md"]:
        fail("API contract metadata must identify Stage 7.", failures)
    if "Last updated: 2026-07-01" not in docs["docs/TRACEABILITY.md"]:
        fail("Traceability metadata must be current for Stage 7.", failures)
    for marker in (
        "Stage 7",
        "avatar-renders",
        "AvatarProvider",
        "MockAvatarProvider",
        "ProviderConfig",
        "render job status",
        "VideoRenderer",
        "video export placeholder",
        "mock/local",
        "provider-output validation",
        "active HTML content",
        "AI-generated avatar/video disclosure",
        "synthetic avatar consent",
        "cloned identity",
        "CLONED_IDENTITY_DISABLED",
        "AVATAR_CONSENT_REQUIRED",
        "REQUESTED_PROVIDER_UNAVAILABLE",
        "PROVIDER_OUTPUT_INVALID",
        "PROVIDER_OUTPUT_TOO_LARGE",
        "safe filename",
        "text/html",
        "application/json",
        "local-html",
        "source citations",
        "evaluation status",
        "source context-ref IDs",
        "terminal failed",
        "public-use license checks",
        "unexpected top-level or nested JSON fields",
        "RR-035",
        "RR-032",
        "RR-033",
        "RR-034",
        "UI/UX Pro Max",
    ):
        if marker not in combined:
            fail(f"Stage 7 docs must mention {marker}.", failures)


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    check_stage_marker_and_branch(failures)
    check_stage_scope(failures)
    check_backend_contracts(failures)
    check_tests_and_frontend(failures)
    check_docs(failures)

    if failures:
        print("Stage 7 quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Stage 7 quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
