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
    assert len(calls) == 1
    call = calls[0]
    assert call["args"][0] == (
        "uv",
        "run",
        "pytest",
        "tests/acceptance/test_checkpoint3_api_e2e.py",
        "-q",
    )
    assert call["kwargs"]["shell"] is False
    assert call["kwargs"]["env"]["NARRATWIN_CP3_PRODUCT_FAITHFUL"] == "1"
    assert "PASS API E2E" in output
    assert "PLANNED language quality" in output
    assert "PLANNED media artifacts" in output
    assert "PLANNED access/quota/retention" in output
    assert "PLANNED security/observability" in output
    assert "PLANNED performance" in output
    assert "PLANNED real-browser E2E with no success-path interception" in output
    assert "PLANNED output-correctness that executes rather than reads" in output
    assert "1 passed, 7 planned, 0 failed" in output


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
    assert [probe.label for probe in checkpoint3.PROBES if probe.implemented] == ["API E2E"]


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
    assert "PLANNED language quality" in result.stdout
    assert "tests/acceptance/test_checkpoint3_output_correctness.py" in result.stdout
