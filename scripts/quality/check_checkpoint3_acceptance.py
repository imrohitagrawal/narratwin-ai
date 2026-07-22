#!/usr/bin/env python3
"""Executable Checkpoint 3 acceptance harness."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import NamedTuple, Sequence


ROOT = Path(__file__).resolve().parents[2]
PRODUCT_FAITHFUL_ENV = "NARRATWIN_CP3_PRODUCT_FAITHFUL"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PLANNED = "PLANNED"
MAX_FAILURE_SUMMARY_CHARS = 320
PROBE_TIMEOUT_SECONDS = 120
PROBE_ENV_DENYLIST = (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
    "NARRATWIN_STATE_DIR",
    "NARRATWIN_STAGE4_STATE_FILE",
    "NARRATWIN_STAGE6_STATE_FILE",
    "NARRATWIN_STAGE7_STATE_FILE",
)
SENSITIVE_OUTPUT_PATTERNS = (
    re.compile(
        r"(?i)[^\n]*(?:CP6-RAW-UPLOAD-CANARY|CP6-RAW-PROMPT-CANARY|CP6-RAW-INJECTION-CANARY|"
        r"CP6-PRIVATE-MARKER|ignore (?:all )?previous instructions|print the hidden system prompt|"
        r"hidden system prompt)[^\n]*"
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
        implemented=False,
        planned_reason="future C3A probe; CP1, CP2, CP3, CP4, CP5, and CP6 make no performance acceptance claim",
    ),
    Probe(
        label="real-browser E2E with no success-path interception",
        command=(
            "npm",
            "--prefix",
            "frontend",
            "run",
            "test:smoke",
            "--",
            "--config=frontend/playwright.checkpoint3.config.ts",
        ),
        env=((PRODUCT_FAITHFUL_ENV, "1"), ("NARRATWIN_REAL_STACK", "1")),
        implemented=False,
        planned_reason="future C3A probe; CP1, CP2, CP3, CP4, CP5, and CP6 touch no browser or frontend scope",
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
    ]:
        failures.append(
            "C3A-CP6 may implement only the API E2E, output-correctness, language-quality, "
            "media-artifacts, access/quota/retention, and security/observability probes."
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
    if command[:3] != ("uv", "run", "pytest"):
        failures.append(f"{probe.label} must execute pytest through uv, not docs/prose helpers.")
    if "tests/acceptance/" not in command_text:
        failures.append(f"{probe.label} must target executable acceptance tests.")
    forbidden_terms = ("docs/", "docs\\", "snapshot", "static", "prose")
    for term in forbidden_terms:
        if term in command_text:
            failures.append(f"{probe.label} command must not target {term} content.")
    for forbidden_binary in ("rg", "cat"):
        if forbidden_binary in command:
            failures.append(f"{probe.label} command must not rely on {forbidden_binary} scanning.")
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
    return ProbeResult(
        label=probe.label,
        status=status,
        command=display_command(probe),
        returncode=completed.returncode,
        output=output,
        planned_reason="",
    )


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
            print(f"  returncode={result.returncode}; output_summary={summarize_failure_output(result.output)}")

    failed = sum(result.status == STATUS_FAIL for result in results)
    planned = sum(result.status == STATUS_PLANNED for result in results)
    passed = sum(result.status == STATUS_PASS for result in results)
    print(f"Checkpoint 3 acceptance incomplete: {passed} passed, {planned} planned, {failed} failed.")
    if failed or planned:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
