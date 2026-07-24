#!/usr/bin/env python3
"""Executable Checkpoint 3 acceptance harness."""

from __future__ import annotations

import os
import json
import re
import shlex
import shutil
import socket
import subprocess
from pathlib import Path
from typing import NamedTuple, Sequence


ROOT = Path(__file__).resolve().parents[2]
PRODUCT_FAITHFUL_ENV = "NARRATWIN_CP3_PRODUCT_FAITHFUL"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PLANNED = "PLANNED"
MAX_FAILURE_SUMMARY_CHARS = 280
PROBE_TIMEOUT_SECONDS = 120
CP8_LABEL = "real-browser E2E with no success-path interception"
FULL_PROJECT_MULTILINGUAL_LABEL = "full-project multilingual corpus"
CP8_BROWSER_TEST_TITLE = (
    "Issue #269 C3A-CP8 real browser path exercises local controlled demo without fabricated success"
)
CP8_EVIDENCE_ROOT = ROOT / "reports" / "checkpoint3-real-browser" / "playwright-output"
CP8_EVIDENCE_FILE_NAME = "issue-269-c3a-cp8-browser-evidence.json"
CP8_BACKEND_PORT_ENV = "NARRATWIN_CP8_BACKEND_PORT"
CP8_FRONTEND_PORT_ENV = "NARRATWIN_CP8_FRONTEND_PORT"
CP8_NEXT_DEV_LOCK = ROOT / "frontend" / ".next" / "dev" / "lock"
CP8_REQUIRED_IDEMPOTENCY_PREFIXES = frozenset(
    {
        "ui-project",
        "ui-upload",
        "ui-approval",
        "ui-ingest",
        "ui-generate",
        "ui-multilingual",
        "ui-avatar-consent",
        "ui-avatar",
    }
)
CP8_REQUIRED_IDEMPOTENCY_STEPS = {
    "project": "ui-project",
    "upload": "ui-upload",
    "approval": "ui-approval",
    "ingest": "ui-ingest",
    "generate": "ui-generate",
    "multilingual": "ui-multilingual",
    "avatarConsent": "ui-avatar-consent",
    "avatar": "ui-avatar",
}
CP8_AUDIENCE = "RECRUITER"
CP8_DEPTH = "STANDARD"
CP8_TARGET_LANGUAGE = "fr"
CP8_REQUESTED_VOICE_PROVIDER = "mock"
CP8_REQUESTED_AVATAR_PROVIDER = "mock"
CP8_GLOSSARY_STATIC_TERMS = ("NarraTwin AI", "Checkpoint 3A")
CP8_REQUIRED_REPRESENTATIVE_BROWSER_GROUPS = frozenset(
    {
        "Hindi / Devanagari",
        "Arabic / RTL Arabic script",
        "Hebrew / RTL",
        "Japanese / CJK",
        "Korean / Hangul",
        "Russian / Cyrillic",
        "French / Latin",
        "Thai / Southeast Asia",
    }
)
CP8_KNOWLEDGE_TEMPLATE = """# NarraTwin AI

NarraTwin AI turns approved project knowledge into grounded walkthrough scripts with source chunk citations.

It supports recruiters, hiring managers, engineers, product leaders, customers, beginners, and global audiences with audience-aware explanations.

The Stage 4 slice uses a mock local LLM and mock local embeddings for deterministic tests.

Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.

## Checkpoint 3A browser evidence nonce: {runtime_nonce}"""
PROBE_ENV_DENYLIST = (
    "ANTHROPIC_API_KEY",
    "AVATAR_PROVIDER",
    "DID_API_KEY",
    "ELEVENLABS_API_KEY",
    "EMBEDDING_PROVIDER",
    "EVALUATION_PROVIDER",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "HEYGEN_API_KEY",
    "NARRATWIN_STATE_DIR",
    "NARRATWIN_STAGE4_STATE_FILE",
    "NARRATWIN_STAGE6_STATE_FILE",
    "NARRATWIN_STAGE7_STATE_FILE",
    "STORAGE_PROVIDER",
    "STT_PROVIDER",
    "SUBTITLE_PROVIDER",
    "TAVUS_API_KEY",
    "TRANSLATION_PROVIDER",
    "TTS_PROVIDER",
)
SENSITIVE_OUTPUT_PATTERNS = (
    re.compile(
        r"(?i)[^\n]*(?:CP6-RAW-UPLOAD-CANARY|CP6-RAW-PROMPT-CANARY|CP6-RAW-INJECTION-CANARY|"
        r"CP6-PRIVATE-MARKER|CP7-RAW-UPLOAD-CANARY|CP7-RAW-PROMPT-CANARY|CP7-RAW-INJECTION-CANARY|"
        r"CP7-PRIVATE-MARKER|CP8-RAW-UPLOAD-CANARY|CP8-RAW-PROMPT-CANARY|CP8-RAW-INJECTION-CANARY|"
        r"CP8-PRIVATE-MARKER|ignore (?:all )?previous instructions|print the hidden system prompt|"
        r"hidden system prompt|generated full script text|SHOULD_NOT_PRINT_CP8)[^\n]*"
    ),
    re.compile(r"(?i)(secret|token|provider payload|raw upload|raw prompt|generated script|private identifier)[^\n]*"),
    re.compile(
        r"(?i)(api[_-]?key(?:[_-]?value)?|authorization|bearer|password|secret|token|credential)"
        r"\s*[:=]\s*['\"]?[^'\"\s]+"
    ),
    re.compile(
        r"(?i)(rawPromptInjectionText|promptInjectionAttempt|instructionOverride|unsafeContent|"
        r"observabilityRecord|observabilityBinding|logEvent|spanAttributes|privateMarker|requestId|traceId|"
        r"runId|evaluationId|runtimeNonce)[^\n]*"
    ),
    re.compile(
        r"(?i)(raw_prompt_injection_text|prompt_injection_attempt|instruction_override|unsafe_content|"
        r"observability_record|observability_binding|log_event|span_attributes|private_marker|request_id|trace_id|"
        r"run_id|evaluation_id|runtime_nonce|api_key_value)[^\n]*"
    ),
    re.compile(
        r"(?i)(acceptedScriptText|sourceScriptText|translatedScriptText|subtitlesText|contentBase64|demoExport|"
        r"renderManifest|videoExportPlaceholder|voiceManifest|fileName|checksum|claimText|contextRefs|"
        r"claimSupports|sourceClaimSupportIds|evidenceSnapshot|redactedExcerpt)[^\n]*"
    ),
    re.compile(
        r"(?i)(inviteSecret|sessionSecret|quotaReservationId|quota_reservation_id|idempotencyScope|"
        r"idempotency_scope|requestChecksum|request_checksum|retentionRecordId|retention_record_id|"
        r"tombstoneChecksum|tombstone_checksum|deletionEvidenceId|deletion_evidence_id|accessRecordId|"
        r"access_record_id|artifactChecksum|artifact_checksum)[^\n]*"
    ),
    re.compile(
        r"(?i)(performanceFailureContext|operationTiming|operationName|elapsedMs|thresholdMs|thresholds|"
        r"requestIdBound|request_id_bound|traceLatencyMs|trace_latency_ms|runtimeSource|runtime_source|"
        r"runtimePosture|runtime_posture|performanceEvidence|performance_evidence)[^\n]*"
    ),
    re.compile(
        r"(?i)(browserEvidence|browser_evidence|successPathInterception|success_path_interception|"
        r"route\.fulfill|requestSequence|request_sequence|sourceBinding|source_binding|browserConsole|"
        r"browser_console|serverFailure|server_failure|browserFailure|browser_failure)[^\n]*"
    ),
)


class Probe(NamedTuple):
    label: str
    command: tuple[str, ...]
    env: tuple[tuple[str, str], ...]
    implemented: bool
    planned_reason: str


class ProbeResult(NamedTuple):
    label: str
    status: str
    command: str
    returncode: int | None
    output: str
    planned_reason: str


PROBES: tuple[Probe, ...] = (
    Probe(
        label="API E2E",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_api_e2e.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label="output-correctness that executes rather than reads",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_output_correctness.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label="language quality",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_language_quality.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label="media artifacts",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_media_artifacts.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label="access/quota/retention",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_access_quota_retention.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label="security/observability",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_security_observability.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label="performance",
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_performance.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label=FULL_PROJECT_MULTILINGUAL_LABEL,
        command=("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_full_project_multilingual.py", "-q"),
        env=((PRODUCT_FAITHFUL_ENV, "1"),),
        implemented=True,
        planned_reason="",
    ),
    Probe(
        label=CP8_LABEL,
        command=(
            "npm",
            "--prefix",
            "frontend",
            "run",
            "test:smoke",
            "--",
            "--config=playwright.checkpoint3.config.ts",
        ),
        env=((PRODUCT_FAITHFUL_ENV, "1"), ("NARRATWIN_REAL_STACK", "1")),
        implemented=True,
        planned_reason="",
    ),
)

EXPECTED_IMPLEMENTED_COMMANDS: dict[str, tuple[str, ...]] = {
    "API E2E": ("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_api_e2e.py", "-q"),
    "output-correctness that executes rather than reads": (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_output_correctness.py",
        "-q",
    ),
    "language quality": ("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_language_quality.py", "-q"),
    "media artifacts": ("uv", "run", "pytest", "tests/acceptance/test_checkpoint3_media_artifacts.py", "-q"),
    "access/quota/retention": (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_access_quota_retention.py",
        "-q",
    ),
    "security/observability": (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_security_observability.py",
        "-q",
    ),
    "performance": (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_performance.py",
        "-q",
    ),
    FULL_PROJECT_MULTILINGUAL_LABEL: (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_full_project_multilingual.py",
        "-q",
    ),
    CP8_LABEL: (
        "npm",
        "--prefix",
        "frontend",
        "run",
        "test:smoke",
        "--",
        "--config=playwright.checkpoint3.config.ts",
    ),
}


def display_command(probe: Probe) -> str:
    env_prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in probe.env)
    command = " ".join(shlex.quote(part) for part in probe.command)
    return f"{env_prefix} {command}".strip()


PLANNED_PROBES = tuple((probe.label, display_command(probe)) for probe in PROBES)


def validate_probe_contract(probes: Sequence[Probe]) -> list[str]:
    failures: list[str] = []
    implemented = [probe for probe in probes if probe.implemented]
    if [probe.label for probe in implemented] != [
        "API E2E",
        "output-correctness that executes rather than reads",
        "language quality",
        "media artifacts",
        "access/quota/retention",
        "security/observability",
        "performance",
        "full-project multilingual corpus",
        "real-browser E2E with no success-path interception",
    ]:
        failures.append(
            "Checkpoint 3A must implement only the API E2E, output-correctness, language-quality, "
            "media-artifacts, access/quota/retention, security/observability, performance, "
            "full-project multilingual corpus, and real-browser E2E probes."
        )
    for probe in probes:
        env = dict(probe.env)
        if env.get(PRODUCT_FAITHFUL_ENV) != "1":
            failures.append(f"{probe.label} missing {PRODUCT_FAITHFUL_ENV}=1.")
        if probe.implemented:
            failures.extend(validate_implemented_probe(probe))
        elif not probe.planned_reason:
            failures.append(f"{probe.label} planned probe must carry a planned reason.")
    return failures


def validate_implemented_probe(probe: Probe) -> list[str]:
    failures: list[str] = []
    command = probe.command
    command_text = " ".join(command).lower()
    expected_command = EXPECTED_IMPLEMENTED_COMMANDS.get(probe.label)
    if expected_command is not None and command != expected_command:
        failures.append(f"{probe.label} must dispatch {' '.join(expected_command)}.")
    forbidden_terms = ("docs/", "docs\\", "snapshot", "static", "prose")
    for term in forbidden_terms:
        if term in command_text:
            failures.append(f"{probe.label} command must not target {term} content.")
    for forbidden_binary in ("rg", "cat"):
        if forbidden_binary in command:
            failures.append(f"{probe.label} command must not rely on {forbidden_binary} scanning.")
    if probe.label == CP8_LABEL:
        if command != EXPECTED_IMPLEMENTED_COMMANDS[probe.label]:
            failures.append(f"{probe.label} must use the dedicated Playwright browser config.")
        if "playwright.checkpoint3.config.ts" not in command_text:
            failures.append(f"{probe.label} must target the dedicated real-browser Playwright config.")
        return failures
    if command[:3] != ("uv", "run", "pytest"):
        failures.append(f"{probe.label} must execute pytest through uv, not docs/prose helpers.")
    if "tests/acceptance/" not in command_text:
        failures.append(f"{probe.label} must target executable acceptance tests.")
    return failures


def run_probe(probe: Probe) -> ProbeResult:
    if not probe.implemented:
        return ProbeResult(
            label=probe.label,
            status=STATUS_PLANNED,
            command=display_command(probe),
            returncode=None,
            output="",
            planned_reason=probe.planned_reason,
        )
    env = os.environ.copy()
    for key in PROBE_ENV_DENYLIST:
        env.pop(key, None)
    env.update(dict(probe.env))
    if probe.label == CP8_LABEL:
        shutil.rmtree(CP8_EVIDENCE_ROOT, ignore_errors=True)
        cleanup_stale_cp8_next_dev_lock()
        configure_cp8_isolated_ports(env)
    try:
        completed = subprocess.run(
            probe.command,
            check=False,
            cwd=ROOT,
            env=env,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        timeout_output = exc.output if isinstance(exc.output, str) else ""
        return ProbeResult(
            label=probe.label,
            status=STATUS_FAIL,
            command=display_command(probe),
            returncode=None,
            output=f"probe timed out after {PROBE_TIMEOUT_SECONDS}s\n{timeout_output}",
            planned_reason="",
        )
    output = completed.stdout or ""
    status = STATUS_PASS if completed.returncode == 0 else STATUS_FAIL
    if status == STATUS_PASS:
        probe_failure = validate_completed_probe_output(probe, output)
        if probe_failure:
            status = STATUS_FAIL
            output = f"probe contract failed: {probe_failure}\n{output}"
    return ProbeResult(
        label=probe.label,
        status=status,
        command=display_command(probe),
        returncode=completed.returncode,
        output=output,
        planned_reason="",
    )


def configure_cp8_isolated_ports(env: dict[str, str]) -> None:
    """Avoid stale default Playwright ports while keeping the browser flow local."""

    used_ports: set[str] = set()
    backend_port = env.get(CP8_BACKEND_PORT_ENV, "")
    if backend_port:
        used_ports.add(backend_port)
    else:
        backend_port = allocate_loopback_port(used_ports)
        env[CP8_BACKEND_PORT_ENV] = backend_port
        used_ports.add(backend_port)

    frontend_port = env.get(CP8_FRONTEND_PORT_ENV, "")
    if frontend_port:
        return
    env[CP8_FRONTEND_PORT_ENV] = allocate_loopback_port(used_ports)


def cleanup_stale_cp8_next_dev_lock() -> None:
    """Remove a dead Next dev lock that would prevent Playwright from starting."""

    try:
        lock = json.loads(CP8_NEXT_DEV_LOCK.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return
    pid = lock.get("pid") if isinstance(lock, dict) else None
    if not isinstance(pid, int) or pid <= 0 or process_exists(pid):
        return
    try:
        CP8_NEXT_DEV_LOCK.unlink()
    except FileNotFoundError:
        return


def process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def allocate_loopback_port(excluded: set[str]) -> str:
    for _ in range(20):
        port = free_loopback_port()
        if port not in excluded:
            return port
    raise RuntimeError("Unable to allocate isolated CP8 loopback ports.")


def free_loopback_port() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return str(sock.getsockname()[1])


def validate_completed_probe_output(probe: Probe, output: str) -> str:
    if probe.label != CP8_LABEL:
        return ""
    if CP8_BROWSER_TEST_TITLE not in output:
        return "CP8 browser test title was not observed in Playwright output."
    if not re.search(r"\b1 passed\b", output):
        return "CP8 browser test did not report one executed passing test."
    if re.search(r"\b\d+\s+skipped\b", output):
        return "CP8 browser test reported skipped tests."

    evidence_files = sorted(CP8_EVIDENCE_ROOT.glob(f"**/{CP8_EVIDENCE_FILE_NAME}"))
    if len(evidence_files) != 1:
        return "CP8 browser evidence artifact was not created exactly once."
    try:
        evidence = json.loads(evidence_files[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "CP8 browser evidence artifact is unreadable."

    if not isinstance(evidence, dict):
        return "CP8 browser evidence artifact has the wrong shape."
    nonce = evidence.get("runtimeNonce")
    if not isinstance(nonce, str) or not nonce.startswith("cp8-"):
        return "CP8 browser evidence missing runtime nonce."
    if evidence.get("noSuccessPathInterception") is not True:
        return "CP8 browser evidence missing no-success-interception proof."
    consent_record_id = evidence.get("consentRecordId")
    if not isinstance(consent_record_id, str) or not consent_record_id.startswith("consent_"):
        return "CP8 browser evidence missing runtime identifiers."
    expected_idempotency_keys = expected_cp8_idempotency_keys(nonce, consent_record_id)

    binding = evidence.get("requestPayloadBinding")
    if not isinstance(binding, dict):
        return "CP8 browser evidence missing request payload binding."
    required_boolean_bindings = ("projectNameNonce", "sourceEvidenceNonce", "glossaryNonce")
    if any(binding.get(key) is not True for key in required_boolean_bindings):
        return "CP8 browser evidence missing runtime nonce request binding."
    idempotency_evidence = binding.get("idempotencyEvidence")
    if not isinstance(idempotency_evidence, dict) or set(idempotency_evidence) != set(
        CP8_REQUIRED_IDEMPOTENCY_STEPS
    ):
        return "CP8 browser evidence missing idempotency binding."
    for step, prefix in CP8_REQUIRED_IDEMPOTENCY_STEPS.items():
        entry = idempotency_evidence.get(step)
        if not isinstance(entry, dict):
            return "CP8 browser evidence missing idempotency binding."
        observed = entry.get("observed")
        expected = entry.get("expected")
        expected_key = expected_idempotency_keys[step]
        if (
            not isinstance(observed, str)
            or not isinstance(expected, str)
            or not observed.startswith(f"{prefix}-")
            or observed != expected_key
            or expected != expected_key
            or entry.get("prefix") != prefix
            or entry.get("matched") is not True
        ):
            return "CP8 browser evidence missing idempotency binding."
    prefixes = binding.get("idempotencyPrefixes")
    if not isinstance(prefixes, list) or not all(isinstance(item, str) for item in prefixes):
        return "CP8 browser evidence missing idempotency binding."
    if not CP8_REQUIRED_IDEMPOTENCY_PREFIXES.issubset(set(prefixes)):
        return "CP8 browser evidence missing idempotency binding."

    project_id = evidence.get("projectId")
    document_id = evidence.get("documentId")
    ingestion_run_id = evidence.get("ingestionRunId")
    run_id = evidence.get("runId")
    trace_id = evidence.get("traceId")
    evaluation_id = evidence.get("evaluationId")
    multilingual_run_id = evidence.get("multilingualRunId")
    avatar_render_id = evidence.get("avatarRenderId")
    expected_prefixes = (
        (project_id, "proj_"),
        (document_id, "doc_"),
        (ingestion_run_id, "ing_"),
        (run_id, "run_"),
        (trace_id, "trace_"),
        (evaluation_id, "eval_"),
        (consent_record_id, "consent_"),
        (multilingual_run_id, "mlrun_"),
        (avatar_render_id, "avrun_"),
    )
    if any(not isinstance(value, str) or not value.startswith(prefix) for value, prefix in expected_prefixes):
        return "CP8 browser evidence missing runtime identifiers."

    request_sequence = evidence.get("requestSequence")
    if not isinstance(request_sequence, list) or not all(isinstance(item, str) for item in request_sequence):
        return "CP8 browser evidence missing request sequence."
    required_requests = {
        "POST /api/v1/projects",
        f"POST /api/v1/projects/{project_id}/knowledge-documents",
        f"PATCH /api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        f"POST /api/v1/projects/{project_id}/ingestion-runs",
        f"POST /api/v1/projects/{project_id}/walkthrough-runs",
        f"POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
        f"POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
        f"POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
        "GET /api/v1/ops/status",
    }
    if not required_requests.issubset(set(request_sequence)):
        return "CP8 browser evidence missing request sequence."
    if evidence.get("failedRequestCount") != 0:
        return "CP8 browser evidence includes failed browser requests."
    request_origins = evidence.get("requestOrigins")
    if not isinstance(request_origins, list) or any(
        not isinstance(origin, str) or not origin.startswith("http://127.0.0.1:")
        for origin in request_origins
    ):
        return "CP8 browser evidence left the local browser origin."

    source_binding = evidence.get("sourceBinding")
    if not isinstance(source_binding, dict):
        return "CP8 browser evidence missing source/eval binding."
    if (
        source_binding.get("contextRefCount", 0) < 1
        or source_binding.get("claimSupportCount", 0) < 1
        or source_binding.get("citationCount", 0) < 1
        or source_binding.get("unsupportedClaimCount") != 0
        or source_binding.get("multilingualSourceRunId") != run_id
        or source_binding.get("avatarSourceRunId") != run_id
        or source_binding.get("avatarSourceEvaluationId") != evaluation_id
    ):
        return "CP8 browser evidence missing source/eval binding."

    artifacts = evidence.get("artifactMetadata")
    visible_transcript = evidence.get("visibleTranscript")
    if not isinstance(visible_transcript, dict) or not all(
        visible_transcript.get(key) is True
        for key in (
            "sourceEnglishVisible",
            "targetTranscriptVisible",
            "englishReferenceVisible",
            "citationsVisible",
            "metadataArtifactMatchesTranscript",
            "translatedScriptArtifactMatchesTranscript",
        )
    ):
        return "CP8 browser evidence missing visible transcript proof."
    representative_browser_coverage = evidence.get("representativeBrowserCoverage")
    if not isinstance(representative_browser_coverage, list):
        return "CP8 browser evidence missing representative script coverage."
    observed_representative_groups: set[str] = set()
    for entry in representative_browser_coverage:
        if not isinstance(entry, dict):
            return "CP8 browser evidence missing representative script coverage."
        group = entry.get("group")
        language_tag = entry.get("languageTag")
        if not isinstance(group, str) or not isinstance(language_tag, str):
            return "CP8 browser evidence missing representative script coverage."
        if all(
            entry.get(key) is True
            for key in (
                "targetSnippetVisible",
                "sourceEnglishVisible",
                "targetTranscriptVisible",
                "englishReferenceVisible",
                "citationsVisible",
                "metadataArtifactMatchesTranscript",
                "translatedScriptArtifactMatchesTranscript",
            )
        ):
            observed_representative_groups.add(group)
    if not CP8_REQUIRED_REPRESENTATIVE_BROWSER_GROUPS.issubset(observed_representative_groups):
        return "CP8 browser evidence missing representative script coverage."
    if not isinstance(artifacts, list) or len(artifacts) != 7:
        return "CP8 browser evidence missing artifact metadata."
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            return "CP8 browser evidence missing artifact metadata."
        if (
            not isinstance(artifact.get("label"), str)
            or not isinstance(artifact.get("fileNameSuffix"), str)
            or not isinstance(artifact.get("mimeType"), str)
            or not isinstance(artifact.get("checksum"), str)
            or not artifact["checksum"].startswith("sha256:")
            or artifact.get("byteLength", 0) <= 0
        ):
            return "CP8 browser evidence missing artifact metadata."

    ops_status = evidence.get("opsStatus")
    if not isinstance(ops_status, dict) or ops_status.get("operationalPosture") != "LOCAL_ONLY":
        return "CP8 browser evidence missing ops/status binding."
    for key in ("stage4Projects", "stage4Documents", "stage4IngestionRuns", "stage4WalkthroughRuns", "stage7AvatarRenders"):
        if ops_status.get(key, 0) < 1:
            return "CP8 browser evidence missing ops/status binding."

    providers = evidence.get("providers")
    if not isinstance(providers, dict):
        return "CP8 browser evidence missing local/mock provider posture."
    if (
        providers.get("llm") != "mock"
        or providers.get("translation") != "mock"
        or providers.get("voice") != "mock"
        or providers.get("avatar") != "mock"
        or providers.get("videoRenderer") != "local-html"
        or providers.get("networkEgress") is not False
        or providers.get("realVideo") is not False
        or providers.get("clonedIdentity") is not False
    ):
        return "CP8 browser evidence missing local/mock provider posture."
    return ""


def expected_cp8_idempotency_keys(runtime_nonce: str, consent_record_id: str) -> dict[str, str]:
    project_name = f"NarraTwin AI {runtime_nonce}"
    knowledge_document = CP8_KNOWLEDGE_TEMPLATE.format(runtime_nonce=runtime_nonce)
    request_seed = cp8_checksum_seed(
        project_name,
        knowledge_document,
        CP8_AUDIENCE,
        CP8_DEPTH,
        CP8_TARGET_LANGUAGE,
    )
    glossary_terms = ("Checkpoint 3A", runtime_nonce, "NarraTwin AI")
    multilingual_seed = cp8_checksum_seed(
        request_seed,
        CP8_REQUESTED_VOICE_PROVIDER,
        *glossary_terms,
    )
    avatar_consent_seed = cp8_checksum_seed(
        request_seed,
        CP8_REQUESTED_AVATAR_PROVIDER,
        "true",
        "avatar-consent-v1",
    )
    avatar_seed = cp8_checksum_seed(
        request_seed,
        CP8_REQUESTED_AVATAR_PROVIDER,
        "true",
        consent_record_id,
        "cloned-identity-false",
    )
    return {
        "project": f"ui-project-{request_seed}",
        "upload": f"ui-upload-{request_seed}",
        "approval": f"ui-approval-{request_seed}",
        "ingest": f"ui-ingest-{request_seed}",
        "generate": f"ui-generate-{request_seed}",
        "multilingual": f"ui-multilingual-{multilingual_seed}",
        "avatarConsent": f"ui-avatar-consent-{avatar_consent_seed}",
        "avatar": f"ui-avatar-{avatar_seed}",
    }


def cp8_checksum_seed(*values: str) -> str:
    checksum = 0
    for char in "|".join(values):
        checksum = (checksum * 31 + ord(char)) & 0xFFFFFFFF
    return f"{checksum:x}"


def summarize_failure_output(output: str) -> str:
    if not output:
        return "No subprocess output captured."
    sanitized = output
    for pattern in SENSITIVE_OUTPUT_PATTERNS:
        sanitized = pattern.sub("[redacted]", sanitized)
    lines = [line.strip() for line in sanitized.splitlines() if line.strip()]
    summary = " | ".join(lines[:3])
    if not summary:
        return "Subprocess output contained only blank lines."
    if len(summary) > MAX_FAILURE_SUMMARY_CHARS:
        return summary[: MAX_FAILURE_SUMMARY_CHARS - 3].rstrip() + "..."
    return summary


def main(probes: Sequence[Probe] = PROBES) -> int:
    contract_failures = validate_probe_contract(probes)
    if contract_failures:
        print("Checkpoint 3 acceptance probe contract failed:")
        for failure in contract_failures:
            print(f"- {failure}")
        return 1

    results = [run_probe(probe) for probe in probes]
    print("Checkpoint 3 acceptance probe results:")
    for result in results:
        suffix = f" ({result.planned_reason})" if result.status == STATUS_PLANNED else ""
        print(f"- {result.status} {result.label}: {result.command}{suffix}")
        if result.status == STATUS_FAIL and result.output:
            print(f" returncode={result.returncode}; output_summary={summarize_failure_output(result.output)}")

    failed = sum(result.status == STATUS_FAIL for result in results)
    planned = sum(result.status == STATUS_PLANNED for result in results)
    passed = sum(result.status == STATUS_PASS for result in results)
    if failed or planned:
        print(f"Checkpoint 3 acceptance incomplete: {passed} passed, {planned} planned, {failed} failed.")
        return 1
    print(f"Checkpoint 3 acceptance complete: {passed} passed, {planned} planned, {failed} failed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
