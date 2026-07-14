#!/usr/bin/env python3
"""Executable Stage 8 quality gate for hardening and release readiness."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGE8_BRANCH_PATTERN = re.compile(r"^stage8-")
ISSUE84_GUARDRAIL_BRANCH = "guardrail-main-merge-push-detection-84"
ISSUE157_GOVERNANCE_BRANCH = "governance-mode1-status-157"
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
CONTRACT_FENCE = "narratwin-contract"
STAGE1_PRODUCT_MODE_PROSE = (
    "Slice 1 is pure grounding; this gate does not authorize avatar, video, audio, or interactive Q&A implementation."
)
STAGE1_PRODUCT_MODE_CONTRACT = {
    "contract": "stage1-product-mode-validation",
    "status": "active",
    "owners": "stage1-pm-spec",
    "timing": "before-application-coding",
    "targets": "prd,roadmap,architecture,first-vertical-slice-plan",
    "mode-1": "pre-rendered-multilingual-demo-video",
    "mode-2": "interactive-ai-avatar-guide",
    "avatar-pack": "reusable-project-avatar-pack",
    "first-slice": "pure-grounding",
    "avatar": "blocked",
    "video": "blocked",
    "audio": "blocked",
    "interactive-q-and-a": "blocked",
    "premature-implementation": "blocked",
    "on-failure": "repair-planning-documents-before-application-code",
}
MODE1_STATUS_CONTRACT = {
    "contract": "mode1-local-demo-audited-status",
    "issue-3": "closed-superseded",
    "issue-8": "open-pending-stage1-gate-correction",
    "issue-17": "open-stage6-fallback-integrity",
    "issue-18": "open-playable-audio-later",
    "artifact-18": "json-voice-manifest-not-playable-audio-no-audio-bytes",
    "issue-19": "open-timed-video-later",
    "artifact-19": "html-json-placeholders-not-real-video-mp4-webm-unimplemented",
    "issue-43": "open-real-stack-browser-e2e",
    "evidence-43": "intercepted-api-insufficient-performance-split-to-160",
    "issue-138": "closed-by-pr-152",
    "issue-151": "open-unresolved",
    "security-151": "blocks-clean-container-hosted-release-production-readiness",
    "issue-155": "open-mode1-parent",
    "issue-156": "closed-governance-audit",
    "issue-157": "open-stage1-gate-status",
    "issue-158": "open-security-history",
    "issue-159": "open-release-security-evidence",
    "issue-160": "open-performance-split-from-43",
    "issue-161": "open-final-review-go-no-go-split-from-159",
    "pr-152": "merged-648c81c-closes-138-not-151",
}
MODE1_STATUS_MATRIX_IDS = {
    "artifact-18": "STATUS-ARTIFACT-001",
    "artifact-19": "STATUS-ARTIFACT-001",
    "evidence-43": "STATUS-ARTIFACT-001",
    "issue-151": "STATUS-SEC-001",
    "security-151": "STATUS-SEC-001",
    "pr-152": "STATUS-SEC-001",
}

REQUIRED_FILES = [
    ".stage/current",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    "Makefile",
    "README.md",
    "backend/app/main.py",
    "backend/app/stage4.py",
    "backend/app/stage6.py",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/app/page.test.tsx",
    "frontend/scripts/run-lighthouse.mjs",
    "perf/stage8_locustfile.py",
    "pyproject.toml",
    "uv.lock",
    "scripts/ci/dependency-security.sh",
    "scripts/ci/docker-image-scan.sh",
    "scripts/ci/frontend-lighthouse.sh",
    "scripts/ci/performance-smoke.sh",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_stage8_docs.py",
    "tests/api/test_stage4_slice_api.py",
    "tests/api/test_stage6_multilingual_api.py",
    "tests/api/test_stage8_hardening_api.py",
    "tests/unit/test_stage6_multilingual.py",
    "tests/unit/test_stage8_quality_gate.py",
    "demo/stage8_seed_project.md",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/QUALITY_GATES.md",
    "docs/PROJECT_LEARNINGS_TRACKER.md",
    "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/RELEASE_READINESS_REVIEW.md",
    "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
    "docs/RUNBOOK.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
    "portfolio/README.md",
]

STAGE8_ALLOWED_FILES = set(REQUIRED_FILES) | {
    "tests/api/test_health_api.py",
    "tests/unit/test_health_contract.py",
}

PROCESS_BRANCH_ALLOWED_FILES = {
    ISSUE84_GUARDRAIL_BRANCH: {
        "docs/STATUS.md",
        "scripts/guardrails_check.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_guardrails_check.py",
        "tests/unit/test_stage8_quality_gate.py",
    },
    ISSUE157_GOVERNANCE_BRANCH: {
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
    },
}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def active_markdown(text: str) -> str:
    """Return Markdown after removing content hidden in HTML comments."""
    def erase_comment(match: re.Match[str]) -> str:
        return "".join("\n" if character == "\n" else " " for character in match.group())

    return HTML_COMMENT_PATTERN.sub(erase_comment, text)


def markdown_lines_with_visibility(text: str) -> tuple[list[str], list[bool]]:
    """Mark lines visible to Markdown heading parsing outside fenced code."""
    lines = active_markdown(text).splitlines()
    visibility: list[bool] = []
    fence_character = ""
    fence_length = 0
    for line in lines:
        is_visible = not fence_character
        visibility.append(is_visible)
        if fence_character:
            closing = re.match(r"^ {0,3}(`{3,}|~{3,})\s*$", line)
            if closing and closing.group(1)[0] == fence_character and len(closing.group(1)) >= fence_length:
                fence_character = ""
                fence_length = 0
            continue
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(?:[^`~].*)?$", line)
        if opening:
            fence_character = opening.group(1)[0]
            fence_length = len(opening.group(1))
    return lines, visibility


def markdown_section(text: str, heading: str, level: int) -> str | None:
    """Return one exact active Markdown section, excluding peer/parent sections."""
    lines, visibility = markdown_lines_with_visibility(text)
    expected = f"{'#' * level} {heading}"
    starts = [index for index, line in enumerate(lines) if visibility[index] and line == expected]
    if len(starts) != 1:
        return None

    start = starts[0] + 1
    end = len(lines)
    heading_pattern = re.compile(r"^(#{1," + str(level) + r"})\s+")
    for index in range(start, len(lines)):
        if visibility[index] and heading_pattern.match(lines[index]):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def check_exact_contract(
    text: str,
    heading: str,
    expected: dict[str, str],
    matrix_id: str,
    failures: list[str],
    key_matrix_ids: dict[str, str] | None = None,
    required_prose: str | None = None,
) -> None:
    """Validate one comment-aware, bounded key/value contract section."""
    section = markdown_section(text, heading, 2)
    if section is None:
        fail(f"[{matrix_id}] Must contain exactly one active `{heading}` section.", failures)
        return

    lines = section.splitlines()
    if required_prose:
        if lines[:2] != [required_prose, ""]:
            fail(f"[{matrix_id}] Section must start with the canonical human-readable boundary.", failures)
            return
        lines = lines[2:]
    if len(lines) < 3 or lines[0] != f"```{CONTRACT_FENCE}" or lines[-1] != "```":
        fail(f"[{matrix_id}] Section must contain only one bounded `{CONTRACT_FENCE}` record.", failures)
        return

    record: dict[str, str] = {}
    invalid = False
    for line in lines[1:-1]:
        if not re.fullmatch(r"[a-z0-9-]+=[a-z0-9,.-]+", line):
            invalid = True
            continue
        key, value = line.split("=", 1)
        if key in record:
            invalid = True
        record[key] = value
    if invalid:
        fail(f"[{matrix_id}] Contract has a duplicate, blank, or malformed extra line.", failures)
    key_matrix_ids = key_matrix_ids or {}
    for key in expected.keys() - record.keys():
        key_matrix_id = key_matrix_ids.get(key, matrix_id)
        fail(f"[{key_matrix_id}] Contract is missing canonical key `{key}`.", failures)
    if record.keys() - expected.keys():
        fail(f"[{matrix_id}] Contract contains an unknown key.", failures)
    for key in record.keys() & expected.keys():
        if record[key] != expected[key]:
            key_matrix_id = key_matrix_ids.get(key, matrix_id)
            fail(f"[{key_matrix_id}] Contract value for `{key}` must be `{expected[key]}`.", failures)


def current_branch() -> str:
    env_branch = os.environ.get("GITHUB_HEAD_REF", "").strip()
    if env_branch:
        return env_branch
    return run(["git", "branch", "--show-current"]).stdout.strip()


def changed_files_for_stage_scope() -> list[str]:
    base_candidates = [os.environ.get("GITHUB_BASE_SHA", "").strip(), "origin/main", "main"]
    merge_base = ""
    for candidate in [item for item in base_candidates if item]:
        result = run(["git", "merge-base", candidate, "HEAD"])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
    if not merge_base:
        raise RuntimeError("git merge-base failed for Stage 8 scope.")

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
            fail(f"Missing required Stage 8 file: {path}", failures)


def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "8":
        fail(".stage/current must contain 8 for Stage 8 quality.", failures)

    branch = current_branch()
    if (
        branch
        and branch != "main"
        and not STAGE8_BRANCH_PATTERN.match(branch)
        and branch not in PROCESS_BRANCH_ALLOWED_FILES
    ):
        fail(f"Stage 8 work must run on a stage8-* branch or main after merge; got {branch}.", failures)


def check_stage_scope(failures: list[str]) -> None:
    allowed_files = PROCESS_BRANCH_ALLOWED_FILES.get(current_branch(), STAGE8_ALLOWED_FILES)
    for path in changed_files_for_stage_scope():
        if path not in allowed_files:
            fail(f"Stage 8 changed file outside the allowlist: {path}", failures)


def check_backend_and_tests(failures: list[str]) -> None:
    main_text = read("backend/app/main.py")
    stage4_text = read("backend/app/stage4.py")
    tests = read("tests/api/test_stage8_hardening_api.py")
    stage4_api_tests = read("tests/api/test_stage4_slice_api.py")
    stage6_api_tests = read("tests/api/test_stage6_multilingual_api.py")
    stage6_unit_tests = read("tests/unit/test_stage6_multilingual.py")
    for marker in (
        'stage="8"',
        "MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE",
        "Stage8WriteRateLimiter",
        "RATE_LIMIT_EXCEEDED",
        "REQUEST_TOO_LARGE",
        "CONTENT_LENGTH_REQUIRED",
        "MAX_STAGE8_RATE_LIMIT_KEYS",
        "rate_limit_key_from_scope",
        "actual_bytes",
        "Stage8RequestSizeLimitMiddleware",
        "stage8_write_rate_limiter.reset",
    ):
        if marker not in main_text:
            fail(f"Stage 8 API hardening must include {marker}.", failures)
    if "MAX_API_REQUEST_BYTES" not in stage4_text:
        fail("Stage 8 must define a general API request size limit.", failures)
    for marker in (
        "health_reports_stage8_with_local_latency_budget",
        "write_rate_limit_rejects_excess_requests",
        "write_rate_limit_uses_client_ip_and_bounds_retained_keys",
        "json_request_size_limit_is_enforced",
        "json_request_size_limit_rejects_missing_content_length",
        "json_request_size_limit_rejects_underreported_content_length",
        "upload_mime_validation_rejects_octet_stream",
        "mocked_script_generation_path_stays_under_two_seconds",
        "latency_ms < 200",
        "latency_ms < 2_000",
    ):
        if marker not in tests:
            fail(f"Stage 8 tests must cover {marker}.", failures)
    for marker in ("SECRET_LIKE_CONTENT", "IDEMPOTENCY_CONFLICT", "stage6-secret-glossary"):
        if marker not in stage6_api_tests:
            fail(f"Stage 8 Stage 6 API tests must cover {marker}.", failures)
    for marker in ("replay_response", "conflict_response", "secret-upload"):
        if marker not in stage4_api_tests:
            fail(f"Stage 8 Stage 4 API tests must cover {marker}.", failures)
    for marker in ("test_tts_provider_manifest_rejects_unknown_schema_fields", "unexpectedTopLevel", "unexpectedNested"):
        if marker not in stage6_unit_tests:
            fail(f"Stage 8 Stage 6 unit tests must cover {marker}.", failures)
    frontend_dockerfile = read("frontend/Dockerfile")
    for marker in ("/usr/local/lib/node_modules/npm", "/usr/local/bin/npm", "/usr/local/bin/npx"):
        if marker not in frontend_dockerfile:
            fail(f"Stage 8 frontend runtime image must remove {marker}.", failures)


def check_stage1_product_mode_validation_gate(failures: list[str]) -> None:
    check_exact_contract(
        read("docs/SKILL_EXECUTION_PLAN.md"),
        "Stage 1 Product-Mode Validation Gate",
        STAGE1_PRODUCT_MODE_CONTRACT,
        "M1-GATE-001",
        failures,
        required_prose=STAGE1_PRODUCT_MODE_PROSE,
    )


def check_mode1_status_contract(failures: list[str]) -> None:
    check_exact_contract(
        read("docs/STATUS.md"),
        "Mode 1 Audited Status Contract",
        MODE1_STATUS_CONTRACT,
        "STATUS-LIVE-001",
        failures,
        MODE1_STATUS_MATRIX_IDS,
    )


def check_dependencies_and_scripts(failures: list[str]) -> None:
    pyproject = read("pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    package_lock = read("frontend/package-lock.json")
    makefile = read("Makefile")
    security_workflow = read(".github/workflows/security.yml")
    ci_workflow = read(".github/workflows/ci.yml")
    if "locust" not in pyproject:
        fail("Stage 8 must lock locust as a dev-only performance tool.", failures)
    if "lighthouse" not in package.get("devDependencies", {}):
        fail("Stage 8 must lock Lighthouse as a frontend dev dependency.", failures)
    if '"lighthouse"' not in package_lock:
        fail("frontend/package-lock.json must include Lighthouse.", failures)
    for marker in (
        "check_stage8_docs.py",
        "performance-smoke.sh",
        "frontend-lighthouse.sh",
        "dependency-security.sh",
        "docker-image-scan.sh",
    ):
        if marker not in makefile:
            fail(f"make stage8-quality must run {marker}.", failures)
    scripts = "\n".join(
        read(path)
        for path in (
            "scripts/ci/performance-smoke.sh",
            "scripts/ci/frontend-lighthouse.sh",
            "scripts/ci/docker-image-scan.sh",
            "frontend/scripts/run-lighthouse.mjs",
            "perf/stage8_locustfile.py",
        )
    )
    for marker in (
        "locust",
        "stage8_hardening_api",
        "--headless",
        "NARRATWIN_LOCUST_HEALTH_P95_MS",
        "lighthouse",
        "docker scout cves",
        "trivy image",
        "aquasec/trivy@sha256",
        "largest-contentful-paint",
        "cumulative-layout-shift",
        "--only-severity critical,high",
        "performance",
        "accessibility",
    ):
        if marker not in scripts:
            fail(f"Stage 8 scripts must include {marker}.", failures)
    for marker in ("security / docker build", "Docker image vulnerability scan", "docker-image-scan.sh", "upload-artifact"):
        if marker not in security_workflow:
            fail(f"Stage 8 security workflow must include {marker}.", failures)
    for marker in ("stage8 / performance lighthouse", "performance-smoke.sh", "frontend-lighthouse.sh", "stage8-performance-lighthouse-reports"):
        if marker not in ci_workflow:
            fail(f"Stage 8 CI workflow must include {marker}.", failures)


def check_docs(failures: list[str]) -> None:
    docs = {
        path: read(path)
        for path in (
            "docs/API_CONTRACT.md",
            ".github/pull_request_template.md",
            "docs/ADR/0006-stage8-release-hardening.md",
            "docs/ARCHITECTURE.md",
            "docs/QUALITY_GATES.md",
            "docs/PROJECT_LEARNINGS_TRACKER.md",
            "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
            "docs/RECOMMENDED_REVIEW_ITEMS.md",
            "docs/REPOSITORY_GUARDRAILS.md",
            "docs/RELEASE_CHECKLIST.md",
            "docs/RELEASE_READINESS_REVIEW.md",
            "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
            "docs/RUNBOOK.md",
            "docs/SKILL_LOCK.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/THIRD_PARTY_NOTICES.md",
            "docs/TRACEABILITY.md",
            "portfolio/README.md",
            "demo/stage8_seed_project.md",
        )
    }
    combined = "\n".join(docs.values())
    for marker in (
        "Stage 8",
        "Performance, security hardening, release readiness",
        "health endpoint < 200 ms local",
        "script generation mocked path < 2 sec",
        "upload limit enforced",
        "no critical/high dependency vulnerabilities",
        "no critical/high container vulnerabilities",
        "rate limiting",
        "request size limits",
        "Content-Length is required",
        "actual ASGI body",
        "SECRET_LIKE_CONTENT",
        "Voice provider artifacts must be JSON manifests",
        "top-level or nested fields fail",
        "upload MIME validation",
        "Lighthouse",
        "p95",
        "Trivy",
        "Docker Scout",
        "release checklist",
        "rollback",
        "runbook",
        "demo seed data",
        "portfolio",
        "LRN-001",
        "LRN-002",
        "Review Rigor Retrospective",
        "Project Governance Learnings",
        "PROJECT_LEARNINGS_TRACKER.md",
        "REVIEW_RIGOR_RETROSPECTIVE.md",
        "invariant, exploit-matrix, and contract/gate review",
        "branch protection",
        "Required status checks",
        "stage8 / performance lighthouse",
        "RR-029",
        "RR-030",
        "RR-031",
        "RR-032",
        "RR-033",
        "RR-034",
        "RR-035",
        "multi-worker deployment blocked",
        "source-run based avatar export",
    ):
        if marker not in combined:
            fail(f"Stage 8 docs must include {marker}.", failures)
    if "| RR-029 |" not in docs["docs/RECOMMENDED_REVIEW_ITEMS.md"]:
        fail("Stage 8 must carry forward RR-029 through RR-035.", failures)


def main() -> int:
    failures: list[str] = []
    check_required_files(failures)
    if not failures:
        check_stage_marker_and_branch(failures)
        check_stage_scope(failures)
        check_backend_and_tests(failures)
        check_stage1_product_mode_validation_gate(failures)
        check_mode1_status_contract(failures)
        check_dependencies_and_scripts(failures)
        check_docs(failures)

    if failures:
        print("Stage 8 quality gate failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Stage 8 quality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
