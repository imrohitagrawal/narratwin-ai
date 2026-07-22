from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def load_checkpoint3_module() -> ModuleType:
    module_path = (
        Path(__file__).parents[2]
        / "scripts"
        / "quality"
        / "check_checkpoint3_acceptance.py"
    )
    spec = importlib.util.spec_from_file_location("checkpoint3_acceptance_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checkpoint3: Any = load_checkpoint3_module()


def test_checkpoint3_acceptance_dispatches_api_probe_and_keeps_later_probes_planned(
    monkeypatch: Any, capsys: Any
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, "kwargs": kwargs})
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="api e2e passed\n")

    monkeypatch.setattr(checkpoint3.subprocess, "run", fake_run)

    assert checkpoint3.main() == 1

    output = capsys.readouterr().out
    assert len(calls) == 5
    assert calls[0]["args"][0] == (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_api_e2e.py",
        "-q",
    )
    assert calls[1]["args"][0] == (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_language_quality.py",
        "-q",
    )
    assert calls[2]["args"][0] == (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_media_artifacts.py",
        "-q",
    )
    assert calls[3]["args"][0] == (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_access_quota_retention.py",
        "-q",
    )
    assert calls[4]["args"][0] == (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_output_correctness.py",
        "-q",
    )
    assert all(call["kwargs"]["shell"] is False for call in calls)
    assert all(call["kwargs"]["env"]["NARRATWIN_CP3_PRODUCT_FAITHFUL"] == "1" for call in calls)
    assert "PASS API E2E" in output
    assert "PASS language quality" in output
    assert "PASS media artifacts" in output
    assert "PASS access/quota/retention" in output
    assert "PASS output-correctness that executes rather than reads" in output
    assert "PLANNED security/observability" in output
    assert "PLANNED performance" in output
    assert "PLANNED real-browser E2E with no success-path interception" in output
    assert "5 passed, 3 planned, 0 failed" in output


def test_checkpoint3_acceptance_probe_contract_is_complete() -> None:
    labels = [probe.label for probe in checkpoint3.PROBES]
    commands = [checkpoint3.display_command(probe) for probe in checkpoint3.PROBES]
    combined = "\n".join(labels + commands)

    assert labels == [
        "API E2E",
        "language quality",
        "media artifacts",
        "access/quota/retention",
        "security/observability",
        "performance",
        "real-browser E2E with no success-path interception",
        "output-correctness that executes rather than reads",
    ]
    assert all("NARRATWIN_CP3_PRODUCT_FAITHFUL=1" in command for command in commands)
    assert "NARRATWIN_REAL_STACK=1" in combined
    assert "test_checkpoint3_api_e2e.py" in combined
    assert "test_checkpoint3_language_quality.py" in combined
    assert "test_checkpoint3_media_artifacts.py" in combined
    assert "test_checkpoint3_access_quota_retention.py" in combined
    assert "test_checkpoint3_security_observability.py" in combined
    assert "test_checkpoint3_performance.py" in combined
    assert "playwright.checkpoint3.config.ts" in combined
    assert "test_checkpoint3_output_correctness.py" in combined
    assert checkpoint3.validate_probe_contract(checkpoint3.PROBES) == []
    assert [probe.label for probe in checkpoint3.PROBES if probe.implemented] == [
        "API E2E",
        "language quality",
        "media artifacts",
        "access/quota/retention",
        "output-correctness that executes rather than reads",
    ]
    planned_reasons = [probe.planned_reason for probe in checkpoint3.PROBES if not probe.implemented]
    assert planned_reasons
    assert all("CP1, CP2, CP3, CP4, and CP5" in reason for reason in planned_reasons)


def test_checkpoint3_acceptance_rejects_docs_only_probe_commands() -> None:
    bad_probes = (
        checkpoint3.Probe(
            label="API E2E",
            command=("rg", "Checkpoint 3A", "docs/QUALITY_GATES.md"),
            env=(("NARRATWIN_CP3_PRODUCT_FAITHFUL", "1"),),
            implemented=True,
            planned_reason="",
        ),
        *checkpoint3.PROBES[1:],
    )

    failures = checkpoint3.validate_probe_contract(bad_probes)

    assert any("must execute pytest through uv" in failure for failure in failures)
    assert any("must target executable acceptance tests" in failure for failure in failures)
    assert any("must not target docs/" in failure for failure in failures)
    assert any("must not rely on rg scanning" in failure for failure in failures)


def test_checkpoint3_acceptance_rejects_static_output_correctness_probe_command() -> None:
    probes = tuple(
        checkpoint3.Probe(
            label=probe.label,
            command=("uv", "run", "pytest", "tests/fixtures/static_output_correctness_snapshot.py", "-q"),
            env=probe.env,
            implemented=probe.implemented,
            planned_reason=probe.planned_reason,
        )
        if probe.label == "output-correctness that executes rather than reads"
        else probe
        for probe in checkpoint3.PROBES
    )

    failures = checkpoint3.validate_probe_contract(probes)

    assert any("output-correctness must dispatch tests/acceptance/test_checkpoint3_output_correctness.py" in failure for failure in failures)
    assert any("must not target static content" in failure for failure in failures)


def test_checkpoint3_acceptance_rejects_static_language_quality_probe_command() -> None:
    probes = tuple(
        checkpoint3.Probe(
            label=probe.label,
            command=("uv", "run", "pytest", "tests/fixtures/static_language_quality_snapshot.py", "-q"),
            env=probe.env,
            implemented=probe.implemented,
            planned_reason=probe.planned_reason,
        )
        if probe.label == "language quality"
        else probe
        for probe in checkpoint3.PROBES
    )

    failures = checkpoint3.validate_probe_contract(probes)

    assert any("language quality must dispatch tests/acceptance/test_checkpoint3_language_quality.py" in failure for failure in failures)
    assert any("must not target static content" in failure for failure in failures)


def test_checkpoint3_acceptance_rejects_static_media_artifacts_probe_command() -> None:
    probes = tuple(
        checkpoint3.Probe(
            label=probe.label,
            command=("uv", "run", "pytest", "tests/fixtures/static_media_artifacts_snapshot.py", "-q"),
            env=probe.env,
            implemented=probe.implemented,
            planned_reason=probe.planned_reason,
        )
        if probe.label == "media artifacts"
        else probe
        for probe in checkpoint3.PROBES
    )

    failures = checkpoint3.validate_probe_contract(probes)

    assert any("media artifacts must dispatch tests/acceptance/test_checkpoint3_media_artifacts.py" in failure for failure in failures)
    assert any("must not target static content" in failure for failure in failures)


def test_checkpoint3_acceptance_rejects_static_access_quota_retention_probe_command() -> None:
    probes = tuple(
        checkpoint3.Probe(
            label=probe.label,
            command=("uv", "run", "pytest", "tests/fixtures/static_access_quota_retention_snapshot.py", "-q"),
            env=probe.env,
            implemented=probe.implemented,
            planned_reason=probe.planned_reason,
        )
        if probe.label == "access/quota/retention"
        else probe
        for probe in checkpoint3.PROBES
    )

    failures = checkpoint3.validate_probe_contract(probes)

    assert any(
        "access/quota/retention must dispatch tests/acceptance/test_checkpoint3_access_quota_retention.py" in failure
        for failure in failures
    )
    assert any("must not target static content" in failure for failure in failures)


@pytest.mark.parametrize(
    "command",
    (
        ("uv", "run", "pytest", "docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md", "-q"),
        ("uv", "run", "pytest", "tests/fixtures/static_checkpoint3_snapshot.py", "-q"),
        ("python3", "-c", "print('Checkpoint 3A passed')"),
        ("cat", "docs/QUALITY_GATES.md"),
    ),
)
def test_checkpoint3_acceptance_rejects_prose_static_or_noop_substitutions(
    command: tuple[str, ...]
) -> None:
    bad_probe = checkpoint3.Probe(
        label="API E2E",
        command=command,
        env=(("NARRATWIN_CP3_PRODUCT_FAITHFUL", "1"),),
        implemented=True,
        planned_reason="",
    )

    assert checkpoint3.validate_implemented_probe(bad_probe)


def test_checkpoint3_acceptance_redacts_failed_probe_output(
    monkeypatch: Any, capsys: Any
) -> None:
    sensitive_output = "\n".join(
        (
            "raw upload: Atlas Notes private source body",
            "generated script: should not be dumped",
            "provider payload with token SHOULD_NOT_PRINT",
            "private identifier reviewer-123",
        )
    )

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout=sensitive_output)

    monkeypatch.setattr(checkpoint3.subprocess, "run", fake_run)

    assert checkpoint3.main() == 1

    output = capsys.readouterr().out
    assert "FAIL API E2E" in output
    assert "returncode=1" in output
    assert "output_summary=" in output
    assert "raw upload" not in output.lower()
    assert "Atlas Notes private source body" not in output
    assert "generated script" not in output.lower()
    assert "provider payload" not in output.lower()
    assert "SHOULD_NOT_PRINT" not in output
    assert "reviewer-123" not in output
    assert len(output) < 2000


def test_checkpoint3_acceptance_redacts_runtime_evidence_fields() -> None:
    output = checkpoint3.summarize_failure_output(
        "\n".join(
            (
                "acceptedScriptText: Atlas Output full generated body",
                "claimText: Unsupported runtime claim",
                "contextRefs: [{'redactedExcerpt': 'approved source excerpt'}]",
                "evidenceSnapshot: {'chunkChecksum': 'sha256:example'}",
            )
        )
    )

    assert "acceptedScriptText" not in output
    assert "Atlas Output full generated body" not in output
    assert "claimText" not in output
    assert "Unsupported runtime claim" not in output
    assert "contextRefs" not in output
    assert "redactedExcerpt" not in output
    assert "approved source excerpt" not in output
    assert "evidenceSnapshot" not in output
    assert "chunkChecksum" not in output


def test_checkpoint3_acceptance_redacts_media_artifact_fields() -> None:
    output = checkpoint3.summarize_failure_output(
        "\n".join(
            (
                "contentBase64: TWVkaWEgYnl0ZXM=",
                "sourceScriptText: MEDIA-SENTINEL-CP4 generated body",
                "translatedScriptText: translated generated body",
                "subtitlesText: subtitle generated body",
                "demoExport: <html>local demo body</html>",
                "renderManifest: {'fileName': 'demo.html', 'checksum': 'sha256:artifact'}",
                "videoExportPlaceholder: {'contentBase64': 'ZXhwb3J0'}",
                "sourceClaimSupportIds: ['claim-static-fixture']",
            )
        )
    )

    assert "contentBase64" not in output
    assert "TWVkaWEgYnl0ZXM=" not in output
    assert "sourceScriptText" not in output
    assert "MEDIA-SENTINEL-CP4 generated body" not in output
    assert "translatedScriptText" not in output
    assert "subtitlesText" not in output
    assert "demoExport" not in output
    assert "local demo body" not in output
    assert "renderManifest" not in output
    assert "fileName" not in output
    assert "checksum" not in output
    assert "videoExportPlaceholder" not in output
    assert "sourceClaimSupportIds" not in output
    assert "claim-static-fixture" not in output


def test_checkpoint3_acceptance_redacts_access_quota_retention_evidence_fields() -> None:
    output = checkpoint3.summarize_failure_output(
        "\n".join(
            (
                "inviteSecret: fake-invite-input",
                "sessionSecret: fake-session-input",
                "quotaReservationId: quota_private",
                "idempotencyScope: idem_scope_private",
                "requestChecksum: sha256:private",
                "retentionRecordId: retention_private",
                "tombstoneChecksum: sha256:private-tombstone",
                "deletionEvidenceId: deletion_private",
                "accessRecordId: access_private",
                "artifactChecksum: sha256:artifact-private",
                "quota_reservation_id: quota_snake_private",
                "idempotency_scope: idem_scope_snake_private",
                "request_checksum: sha256:snake-private",
                "retention_record_id: retention_snake_private",
                "tombstone_checksum: sha256:snake-tombstone",
                "deletion_evidence_id: deletion_snake_private",
                "access_record_id: access_snake_private",
                "artifact_checksum: sha256:artifact-snake-private",
            )
        )
    )

    assert "inviteSecret" not in output
    assert "fake-invite-input" not in output
    assert "sessionSecret" not in output
    assert "fake-session-input" not in output
    assert "quotaReservationId" not in output
    assert "quota_private" not in output
    assert "idempotencyScope" not in output
    assert "idem_scope_private" not in output
    assert "requestChecksum" not in output
    assert "retentionRecordId" not in output
    assert "retention_private" not in output
    assert "tombstoneChecksum" not in output
    assert "private-tombstone" not in output
    assert "deletionEvidenceId" not in output
    assert "deletion_private" not in output
    assert "accessRecordId" not in output
    assert "access_private" not in output
    assert "artifactChecksum" not in output
    assert "artifact-private" not in output
    assert "quota_reservation_id" not in output
    assert "quota_snake_private" not in output
    assert "idempotency_scope" not in output
    assert "idem_scope_snake_private" not in output
    assert "request_checksum" not in output
    assert "snake-private" not in output
    assert "retention_record_id" not in output
    assert "retention_snake_private" not in output
    assert "tombstone_checksum" not in output
    assert "snake-tombstone" not in output
    assert "deletion_evidence_id" not in output
    assert "deletion_snake_private" not in output
    assert "access_record_id" not in output
    assert "access_snake_private" not in output
    assert "artifact_checksum" not in output
    assert "artifact-snake-private" not in output


def test_checkpoint3_acceptance_timeout_is_bounded_and_redacted(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=kwargs["timeout"],
            output="acceptedScriptText: timed out generated body",
        )

    monkeypatch.setattr(checkpoint3.subprocess, "run", fake_run)

    result = checkpoint3.run_probe(checkpoint3.PROBES[0])
    output = checkpoint3.summarize_failure_output(result.output)

    assert result.status == "FAIL"
    assert "timed out after 120s" in output
    assert "acceptedScriptText" not in output
    assert "timed out generated body" not in output


def test_make_checkpoint3_acceptance_invokes_executable_harness() -> None:
    result = subprocess.run(
        ["make", "checkpoint3-acceptance"],
        check=False,
        cwd=Path(__file__).parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 2
    assert "python3 scripts/quality/check_checkpoint3_acceptance.py" in result.stdout
    assert "Checkpoint 3 acceptance probe results:" in result.stdout
    assert "PASS API E2E" in result.stdout
    assert "PASS language quality" in result.stdout
    assert "PASS media artifacts" in result.stdout
    assert "PASS access/quota/retention" in result.stdout
    assert "PASS output-correctness that executes rather than reads" in result.stdout
