#!/usr/bin/env python3
"""Executable Stage 8 quality gate for hardening and release readiness."""
from __future__ import annotations
# ruff: noqa: E302, E305, E401
import json, os, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.quality.branch_identity import current_branch  # noqa: E402
from scripts.quality.check_stage2_docs import check_retrieval_strategy_v1_parity  # noqa: E402
from scripts.quality import stage8_brace_expansion_unblock as brace_security  # noqa: E402
from scripts.quality.stage8_a23b import A23A_BRANCH, A23B_BRANCH, A23_ROUTES, check_a23b  # noqa: E402
STAGE8_BRANCH_PATTERN = re.compile(r"^stage8-")
ISSUE84_GUARDRAIL_BRANCH = "guardrail-main-merge-push-detection-84"
ISSUE287_STAGE8_DRIFT_BRANCH = "phase-1-closure-process-287-stage8-quality-gate-drift"
ISSUE289_SECURITY_UNBLOCK_BRANCH = "phase-1-closure-process-289-security-postcss-stage8-gate-unblock"
ISSUE324_PUBLICATION_BRANCH = "phase-1-closure-process-324-publication-boundary-v2"
ISSUE346_TRANSITION_BRANCH = "cut1-process-346-governance-transition"
ISSUE335_A2_1_BRANCH = "cut1-335-r0c-a2-1-stage4-rag-v1-lineage"
ISSUE349_A2_2_BRANCH = "cut1-349-r0c-a2-2-machine-contract-parity"
QUIET_PRESENCE_BRANCH = "cut1-358-quiet-presence-ui"
ISSUE374_SECURITY_BRANCH = "stage8-374-node-image-cve-2026-58043"
ISSUE374_SECURITY_FILES = {
    "frontend/Dockerfile", "frontend/next.config.ts", "scripts/ci/docker-image-scan.sh", "scripts/ci/check_container_scan_consensus.py", "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py", "tests/unit/test_container_scan_consensus.py",
    "docs/ADR/0006-stage8-release-hardening.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md",
}
FRONTEND_NODE_BUILD_IMAGE = (
    "node:26.6.0-alpine@sha256:a4fb14143ee24c038c851864fe85fd90f9121abc8fdca3092798bcc02e06b1d8")
FRONTEND_NODE_RUNTIME_IMAGE = (
    "cgr.dev/chainguard/node:latest@sha256:cf7ae5ead5aed79a61404d7b1bbb9b89ea461991b21cb8fcb07d4b6ad4d8b734")
FRONTEND_BUILD_ARCHIVE_SHA512 = {"npm@12.0.2": "b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943", "brace-expansion@5.0.9": "49c43822ebc8105d533253fb66dfaf8c9ffff7394f6f64837315b13376e4f2ceade8619d27b28ed5d09c4e274e3c929e3d6df42c4ff6713ef00b23e1a3dfd6c6",
    "ip-address@10.3.1": "d5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea", "tar@7.5.21": "5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c", "undici@6.28.0": "2c863dd7483d4c8d77612f7996b305aecf119bfbbf8ab8077935a8282a2d79e274e02509f767847e3d2b567fbb54a30f06950f894a0129f84dc8b236dc413f28"}
FRONTEND_NODE_IMAGE_FAILURE = "Stage 8 frontend build and runtime images must retain the reviewed Node image pin."
QUIET_PRESENCE_FILES = {"docs/governance/preflights/issue-358.json", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
    "docs/THIRD_PARTY_NOTICES.md", "docs/ADR/0048-quiet-presence-embedded-guide.md",
    "scripts/quality/check_stage8_docs.py", "tests/unit/test_stage8_quality_gate.py", "frontend/src/app/demo/page.tsx",
    "frontend/src/app/demo/page.module.css", "frontend/src/app/demo/page.test.tsx",
    "frontend/src/app/demo/guide-client.ts", "frontend/src/app/demo/guide-client.test.ts",
    "frontend/tests/quiet-presence.spec.ts", "frontend/public/demo/narratwin-synthetic-presenter.webp"}
NULL_GIT_SHA = "0" * 40
def issue324_allowed_files() -> set[str]:
    path = ROOT / "docs/governance/preflights/issue-324.json"
    return set(json.loads(path.read_text(encoding="utf-8"))["scope"]["required"])
REQUIRED_FILES = [
    ".stage/current", ".github/pull_request_template.md", ".github/workflows/ci.yml", ".github/workflows/security.yml",
    "Makefile", "README.md", "backend/app/main.py", "backend/app/stage4.py", "backend/app/stage6.py",
    "backend/Dockerfile",
    "frontend/Dockerfile", "frontend/package.json", "frontend/package-lock.json", "frontend/src/app/page.test.tsx",
    "frontend/scripts/run-lighthouse.mjs", "perf/stage8_locustfile.py", "pyproject.toml", "uv.lock",
    "scripts/ci/dependency-security.sh", "scripts/ci/docker-image-scan.sh", "scripts/ci/frontend-lighthouse.sh",
    "scripts/ci/performance-smoke.sh", "scripts/quality/check_quality_stage.py", "scripts/quality/check_stage8_docs.py",
    "tests/api/test_stage4_slice_api.py", "tests/api/test_stage6_multilingual_api.py",
    "tests/api/test_stage8_hardening_api.py", "tests/unit/test_stage6_multilingual.py", "demo/stage8_seed_project.md",
    "docs/ADR/0006-stage8-release-hardening.md", "docs/API_CONTRACT.md", "docs/ARCHITECTURE.md",
    "docs/QUALITY_GATES.md", "docs/PROJECT_LEARNINGS_TRACKER.md", "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md", "docs/REPOSITORY_GUARDRAILS.md", "docs/RELEASE_CHECKLIST.md",
    "docs/RELEASE_READINESS_REVIEW.md", "docs/REVIEW_RIGOR_RETROSPECTIVE.md", "docs/RUNBOOK.md",
    "docs/SKILL_LOCK.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md", "docs/demo/CONTROLLED_LOCAL_DEMO.md",
]
STAGE8_ALLOWED_FILES = set(REQUIRED_FILES) | {"tests/api/test_health_api.py", "tests/unit/test_health_contract.py"}
PROCESS_BRANCH_ALLOWED_FILES = {
    ISSUE374_SECURITY_BRANCH: ISSUE374_SECURITY_FILES,
    ISSUE346_TRANSITION_BRANCH: {
        "docs/governance/preflights/issue-346.json", "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_quality_gate.py", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
    },
    ISSUE335_A2_1_BRANCH: {
        "docs/governance/preflights/issue-335.json", "tests/unit/test_retrieval_strategy_v1_contract.py",
        "backend/app/rag/models.py", "backend/app/stage4.py", "docs/STATUS.md", "frontend/src/app/page.tsx",
        "docs/API_CONTRACT.md", "tests/unit/test_local_durability.py", "docs/ADR/0002-rag-storage.md",
        "backend/app/storage/local_restore_drill.py", "tests/api/test_stage4_slice_api.py",
        "tests/api/test_stage6_multilingual_api.py", "docs/TRACEABILITY.md",
        "scripts/quality/check_stage8_docs.py", "docs/ADR/0047-publication-boundary.md",
        "tests/unit/test_stage8_quality_gate.py", "docs/EVAL_REPORT.md", "docs/STAGE_ISSUE_PLAN.md",
        "evals/smoke/stage5_grounded_script_dataset.json", "scripts/ci/heartbeat2_evidence.py",
        "tests/unit/test_phase1_closure_docs.py", "scripts/quality/phase1_closure/legacy.py"},
    ISSUE349_A2_2_BRANCH: {
        "docs/governance/preflights/issue-349.json", "docs/STAGE2_ARCHITECTURE_CONTRACT.json",
        "scripts/quality/check_stage2_docs.py", "tests/unit/test_stage8_quality_gate.py", "docs/STATUS.md",
        "scripts/quality/check_stage8_docs.py", "docs/ADR/0002-rag-storage.md", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md"},
    ISSUE84_GUARDRAIL_BRANCH: {
        "docs/STATUS.md",
        "scripts/guardrails_check.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_guardrails_check.py",
        "tests/unit/test_stage8_quality_gate.py",
    },
    ISSUE287_STAGE8_DRIFT_BRANCH: {
        "docs/governance/preflights/issue-287.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
    },
    ISSUE289_SECURITY_UNBLOCK_BRANCH: {
        "docs/governance/preflights/issue-289.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/ADR/0037-postcss-audit-remediation.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "frontend/package.json",
        "frontend/package-lock.json",
        "scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
    },
    ISSUE324_PUBLICATION_BRANCH: issue324_allowed_files(),
    QUIET_PRESENCE_BRANCH: QUIET_PRESENCE_FILES,
}
PROCESS_BRANCH_ALLOWED_FILES.update(A23_ROUTES)
EFFECTIVE_STAGE8_ROUTES = PROCESS_BRANCH_ALLOWED_FILES | brace_security.BRACE_EXPANSION_ROUTES
def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")
def fail(message: str, failures: list[str]) -> None:
    failures.append(message)
def changed_files_for_stage_scope() -> list[str]:
    head_result = run(["git", "rev-parse", "HEAD"])
    if head_result.returncode != 0 or not head_result.stdout.strip():
        raise RuntimeError(head_result.stderr.strip() or "git rev-parse HEAD failed")
    head = head_result.stdout.strip()
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    expected_head = os.environ.get("GITHUB_HEAD_SHA", "").strip()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "").strip()
    if event_path and event_name in {"pull_request", "pull_request_review", "push"}:
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
            event_head = (payload["after"] if event_name == "push" else payload["pull_request"]["head"]["sha"])
        except (KeyError, OSError, TypeError, ValueError) as error:
            raise RuntimeError("GitHub exact head evidence is malformed or unavailable.") from error
        if not isinstance(event_head, str) or not event_head.strip():
            raise RuntimeError("GitHub exact head evidence is malformed or unavailable.")
        if expected_head and expected_head != event_head.strip():
            raise RuntimeError("GitHub exact head evidence contradicts GITHUB_HEAD_SHA.")
        expected_head = event_head.strip()
    if not expected_head and event_name in {"pull_request", "pull_request_review", "push"}:
        raise RuntimeError("GitHub exact head evidence is malformed or unavailable.")
    if expected_head:
        expected_result = run(["git", "rev-parse", f"{expected_head}^{{commit}}"])
        if expected_result.returncode != 0 or not expected_result.stdout.strip():
            raise RuntimeError(expected_result.stderr.strip() or "git rev-parse exact head failed")
        if expected_result.stdout.strip() != head:
            raise RuntimeError("Stage 8 scope checkout does not match the exact head.")
    preferred_base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    push_ref = os.environ.get("NARRATWIN_HEAD_REF", os.environ.get("GITHUB_REF_NAME", "")).strip()
    branch_base = (event_name == "push" and push_ref != "main") or not preferred_base or preferred_base == NULL_GIT_SHA
    base_candidates = ["origin/main", "main"] if branch_base else [preferred_base]
    merge_base = ""
    last_error = ""
    for candidate in base_candidates:
        result = run(["git", "merge-base", candidate, head])
        if result.returncode == 0 and result.stdout.strip():
            merge_base = result.stdout.strip()
            break
        last_error = result.stderr.strip()
    if not merge_base:
        raise RuntimeError(last_error or "git merge-base failed for Stage 8 scope.")
    diff_flags = ["--name-status", "-z", "--find-renames", "--find-copies", "--find-copies-harder"]
    paths: list[str] = []
    for args in (
        ["git", "diff", *diff_flags, f"{merge_base}..{head}", "--"],
        ["git", "diff", "--cached", *diff_flags, head, "--"],
        ["git", "diff", *diff_flags, "--"],
    ):
        result = run(args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"{' '.join(args)} failed")
        paths.extend(parse_name_status_z(result.stdout))
    untracked = run(["git", "ls-files", "-z", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(untracked.stderr.strip() or "git ls-files failed")
    paths.extend(parse_paths_z(untracked.stdout))
    return sorted(set(paths))
def parse_paths_z(output: str) -> list[str]:
    if not output:
        return []
    if not output.endswith("\0"):
        raise RuntimeError("Malformed NUL-delimited Git path output.")
    paths = output[:-1].split("\0")
    if any(not path for path in paths):
        raise RuntimeError("Malformed empty Git path.")
    return paths
def parse_name_status_z(output: str) -> list[str]:
    fields = parse_paths_z(output)
    paths: list[str] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status in {"A", "B", "D", "M", "T", "U"}:
            arity = 1
        elif re.fullmatch(r"[RC]\d{1,3}", status) and int(status[1:]) <= 100:
            arity = 2
        else:
            raise RuntimeError(f"Malformed Git name-status record: {status!r}")
        record_paths = fields[index : index + arity]
        if len(record_paths) != arity:
            raise RuntimeError(f"Incomplete Git name-status record: {status!r}")
        paths.extend(record_paths)
        index += arity
    return paths
def check_required_files(failures: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not (ROOT / path).is_file():
            fail(f"Missing required Stage 8 file: {path}", failures)
A23A_CONTRACT_MARKERS = {
    "docs/API_CONTRACT.md": (
        "stage7-source-evaluation-checksum-v2", "compact sorted-key UTF-8 JSON",
        "`scope`: normalized `tenantId` and `projectId`", "even when `selectedContext` is empty",
        "`topK=6`", '`minimumScoreThreshold="0.72"`', '`minimumScoreComparison="inclusive-gte"`',
        "`minimumRetrievedChunks=1`", "`minimumDistinctDocuments=1`",
        "`maximumChunksPerDocument=3`", "`tieBreakOrder` is exact", "`fallback`",
        "`computedEvidenceScoresOnly=true`", "`syntheticEligibilityScoresAllowed=false`",
        "`belowThresholdBackfill=false`", "`terminalRefusalBeforeGeneration=true`",
        "`EMPTY_CONTEXT`", "`LOW_RETRIEVAL_CONFIDENCE`", "`AMBIGUOUS_CONTEXT`",
        "`CROSS_PROJECT_CONTEXT`", "`UNSAFE_CONTEXT`", "`approvedAt`",
        "unique `contextRefId` and `chunkId`", "array position is its zero-based context ordinal",
        "every row's tenant/project IDs must equal `scope`", "finite IEEE-754 binary64",
        "shortest correctly rounded base-10", "expand any exponent to fixed notation", "canonical zero is `0`",
        "independently verified `snapshotChecksum`", "`sourceCitationIndexes`: positive integers",
        "sha256:a956a969f4f147fb020fa06b71722d8fcf76ad850f0c5f6be8d78bbbadb81377"),
    "docs/ADR/0004-avatar-provider-adapter.md": (
        "local/mock stale-or-mismatch integrity", "not cryptographic authenticity",
        "Legacy v1 rows cannot replay as v2"),
    "docs/QUALITY_GATES.md": ("A2.3a evaluation-lineage contract gate", "wrong-schema"),
    "docs/STAGE_ISSUE_PLAN.md": (A23A_BRANCH, "300 charged lines"),
    "docs/STATUS.md": ("Issue `#351`", "A2.3b remains blocked"),
}
def evaluation_lineage_checksum_v2_contract_valid(documents: dict[str, str]) -> bool:
    return all(marker in documents[path] for path, markers in A23A_CONTRACT_MARKERS.items() for marker in markers)
def check_evaluation_lineage_checksum_v2_contract(root: Path, failures: list[str]) -> None:
    documents = {path: (root / path).read_text(encoding="utf-8") for path in A23A_CONTRACT_MARKERS}
    if not evaluation_lineage_checksum_v2_contract_valid(documents):
        fail("A2.3a contract is incomplete or drifted.", failures)
def check_stage_marker_and_branch(failures: list[str]) -> None:
    current = read(".stage/current").strip()
    if current != "8":
        fail(".stage/current must contain 8 for Stage 8 quality.", failures)
    branch = current_branch()
    if not branch:
        fail("Stage 8 branch evidence is unavailable or inconsistent.", failures)
        return
    if (
        branch
        and branch != "main"
        and not STAGE8_BRANCH_PATTERN.match(branch)
        and branch not in EFFECTIVE_STAGE8_ROUTES
    ):
        fail(f"Stage 8 work must run on a stage8-* branch or main after merge; got {branch}.", failures)
def check_stage_scope(failures: list[str]) -> None:
    branch = current_branch()
    if not branch:
        fail("Stage 8 scope branch evidence is unavailable or inconsistent.", failures)
        return
    if branch not in EFFECTIVE_STAGE8_ROUTES and branch != "main" and not STAGE8_BRANCH_PATTERN.match(branch):
        fail(f"Stage 8 scope requires an exact reviewed branch; got {branch}.", failures)
        return
    allowed_files = EFFECTIVE_STAGE8_ROUTES.get(branch, STAGE8_ALLOWED_FILES)
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
    for marker in ("test_tts_provider_manifest_rejects_unknown_schema_fields", "unexpectedTopLevel",
                   "unexpectedNested"):
        if marker not in stage6_unit_tests:
            fail(f"Stage 8 Stage 6 unit tests must cover {marker}.", failures)
    frontend_dockerfile = read("frontend/Dockerfile")
    for marker in ("/usr/lib/node_modules", "/usr/local/lib/node_modules", "/usr/local/bin", "/bin", "/usr/bin",
                   "p!=='/usr/bin/node'"):
        if marker not in frontend_dockerfile:
            fail(f"Stage 8 frontend runtime image must remove {marker}.", failures)
def frontend_node_image_valid(dockerfile: str) -> bool:
    expected = [f"FROM {FRONTEND_NODE_BUILD_IMAGE} AS deps", "FROM deps AS build", f"FROM {FRONTEND_NODE_RUNTIME_IMAGE} AS runner"]
    actual = [line.strip() for line in dockerfile.splitlines() if re.match(r"(?i)^from(?:\s|$)", line.lstrip())]
    return (actual == expected and dockerfile.count("sha512sum -c -") == len(FRONTEND_BUILD_ARCHIVE_SHA512)
            and all(package in dockerfile and f"echo '{digest}  /tmp/" in dockerfile
                    for package, digest in FRONTEND_BUILD_ARCHIVE_SHA512.items()))
def check_frontend_node_image(failures: list[str]) -> None:
    if not frontend_node_image_valid(read("frontend/Dockerfile")):
        fail(FRONTEND_NODE_IMAGE_FAILURE, failures)
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
        "trivy image",
        "aquasec/trivy@sha256", "verify_frontend_runtime", 'process.version!=="v26.6.0"',
        '"65532:65532"', "extras.length", "expected_inventory", "actual_inventory", "immutable filesystem",
        'encoding:"buffer"', "readlinkSync", "s.uid", "s.gid", "CapEff", "--connect-timeout", "--max-time", "cleanup_frontend_runtime", "FRONTEND_BUILD_IMAGE", "--target deps", "NODE_OPTIONS", "config == expected",
        "largest-contentful-paint",
        "cumulative-layout-shift",
        "performance",
        "accessibility",
    ):
        if marker not in scripts:
            fail(f"Stage 8 scripts must include {marker}.", failures)
    for marker in (
        "security / docker build",
        "Docker image vulnerability scan",
        "docker-image-scan.sh",
        "upload-artifact",
    ):
        if marker not in security_workflow:
            fail(f"Stage 8 security workflow must include {marker}.", failures)
    for marker in (
        "stage8 / performance lighthouse",
        "performance-smoke.sh",
        "frontend-lighthouse.sh",
        "stage8-performance-lighthouse-reports",
    ):
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
            "docs/demo/CONTROLLED_LOCAL_DEMO.md",
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
        "Controlled Local Demo",
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
    check_retrieval_strategy_v1_parity(ROOT, failures)
    check_evaluation_lineage_checksum_v2_contract(ROOT, failures)
    if not failures:
        check_stage_marker_and_branch(failures)
        check_stage_scope(failures)
        check_a23b(ROOT, run, failures, current_branch() == A23B_BRANCH)
        brace_security.check_exact_route(ROOT, run, failures, current_branch() == brace_security.BRANCH)
        check_frontend_node_image(failures)
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
