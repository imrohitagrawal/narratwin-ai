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

REQUIRED_FILES = [
    ".stage/current",
    ".github/workflows/security.yml",
    "Makefile",
    "backend/app/main.py",
    "backend/app/stage4.py",
    "backend/app/stage6.py",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "frontend/package.json",
    "frontend/package-lock.json",
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
    "tests/api/test_stage8_hardening_api.py",
    "tests/unit/test_stage6_multilingual.py",
    "demo/stage8_seed_project.md",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/API_CONTRACT.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/RELEASE_READINESS_REVIEW.md",
    "docs/RUNBOOK.md",
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

    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch and branch != "main" and not STAGE8_BRANCH_PATTERN.match(branch):
        fail(f"Stage 8 work must run on a stage8-* branch or main after merge; got {branch}.", failures)


def check_stage_scope(failures: list[str]) -> None:
    for path in changed_files_for_stage_scope():
        if path not in STAGE8_ALLOWED_FILES:
            fail(f"Stage 8 changed file outside the allowlist: {path}", failures)


def check_backend_and_tests(failures: list[str]) -> None:
    main_text = read("backend/app/main.py")
    stage4_text = read("backend/app/stage4.py")
    tests = read("tests/api/test_stage8_hardening_api.py")
    for marker in (
        'stage="8"',
        "MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE",
        "Stage8WriteRateLimiter",
        "RATE_LIMIT_EXCEEDED",
        "REQUEST_TOO_LARGE",
        "CONTENT_LENGTH_REQUIRED",
        "MAX_STAGE8_RATE_LIMIT_KEYS",
        "rate_limit_key_for",
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
        "upload_mime_validation_rejects_octet_stream",
        "mocked_script_generation_path_stays_under_two_seconds",
        "latency_ms < 200",
        "latency_ms < 2_000",
    ):
        if marker not in tests:
            fail(f"Stage 8 tests must cover {marker}.", failures)
    frontend_dockerfile = read("frontend/Dockerfile")
    for marker in ("/usr/local/lib/node_modules/npm", "/usr/local/bin/npm", "/usr/local/bin/npx"):
        if marker not in frontend_dockerfile:
            fail(f"Stage 8 frontend runtime image must remove {marker}.", failures)


def check_dependencies_and_scripts(failures: list[str]) -> None:
    pyproject = read("pyproject.toml")
    package = json.loads(read("frontend/package.json"))
    package_lock = read("frontend/package-lock.json")
    makefile = read("Makefile")
    security_workflow = read(".github/workflows/security.yml")
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
    for marker in ("Docker image vulnerability scan", "docker-image-scan.sh", "upload-artifact"):
        if marker not in security_workflow:
            fail(f"Stage 8 security workflow must include {marker}.", failures)


def check_docs(failures: list[str]) -> None:
    docs = {
        path: read(path)
        for path in (
            "docs/API_CONTRACT.md",
            "docs/ADR/0006-stage8-release-hardening.md",
            "docs/QUALITY_GATES.md",
            "docs/RECOMMENDED_REVIEW_ITEMS.md",
            "docs/RELEASE_CHECKLIST.md",
            "docs/RELEASE_READINESS_REVIEW.md",
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
