from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any


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


def test_checkpoint3_acceptance_fails_by_design(capsys: Any) -> None:
    assert checkpoint3.main() == 1

    output = capsys.readouterr().out
    assert "Checkpoint 3 acceptance is not implemented yet." in output
    assert "failing-by-design gate" in output
    for label, command in checkpoint3.PLANNED_PROBES:
        assert label in output
        assert command in output


def test_checkpoint3_acceptance_probe_contract_is_complete() -> None:
    labels = [label for label, _command in checkpoint3.PLANNED_PROBES]
    commands = [command for _label, command in checkpoint3.PLANNED_PROBES]
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


def test_make_checkpoint3_acceptance_invokes_red_gate() -> None:
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
    assert "Checkpoint 3 acceptance is not implemented yet." in result.stdout
    assert "tests/acceptance/test_checkpoint3_output_correctness.py" in result.stdout
