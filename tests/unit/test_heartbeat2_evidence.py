from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ci.heartbeat2_evidence import EvidenceError, _trusted_ci_context, prepare_failure_diagnostic


HEAD = "03b82c6471b66f9ca8a2781e93a90397a9cf8921"
RUN_ID = "h2-31250370346-20260808T092122Z"
CONTROLLED = b"controlled-private-marker"
CANARY = b"controlled-canary-marker"


def candidate(tmp_path: Path, text: str = "first line\nuseful browser failure\n") -> Path:
    root = tmp_path / "candidate"
    root.mkdir(parents=True)
    (root / "browser.log").write_text(text, encoding="utf-8")
    return root


def test_failure_diagnostic_is_minimized_bounded_and_bound(tmp_path: Path) -> None:
    source = candidate(tmp_path, "ignored\n" + "x" * 20_000 + "\nfinal browser failure\n")
    output = tmp_path / "withheld" / "diagnostic.json"

    result = prepare_failure_diagnostic(
        source,
        output,
        stage="browser",
        run_id=RUN_ID,
        head=HEAD,
        controlled=CONTROLLED,
        canary=CANARY,
    )

    assert result == json.loads(output.read_text(encoding="utf-8"))
    assert result["schema"] == "heartbeat2-withheld-diagnostic-v1"
    assert result["outcome"] == "WITHHELD"
    assert result["failureStage"] == "browser"
    assert result["runId"] == RUN_ID
    assert result["headSha"] == HEAD
    assert result["sourceLog"] == "browser.log"
    assert result["diagnosticTail"].endswith("final browser failure")
    assert len(output.read_bytes()) <= 20_000
    assert set(result) == {
        "schema", "outcome", "failureStage", "runId", "headSha",
        "sourceLog", "diagnosticTail", "candidateFileCount", "candidateMemberCount",
    }


@pytest.mark.parametrize("stage", ["", "unknown", "../browser", "BROWSER"])
def test_failure_diagnostic_rejects_invalid_stage(tmp_path: Path, stage: str) -> None:
    with pytest.raises(EvidenceError, match="FAILURE_DIAGNOSTIC"):
        prepare_failure_diagnostic(candidate(tmp_path), tmp_path / "out.json", stage=stage, run_id=RUN_ID, head=HEAD, controlled=CONTROLLED, canary=CANARY)


@pytest.mark.parametrize("run_id,head", [("bad id", HEAD), (RUN_ID, "0" * 39), (RUN_ID, "G" * 40)])
def test_failure_diagnostic_rejects_malformed_bindings(tmp_path: Path, run_id: str, head: str) -> None:
    with pytest.raises(EvidenceError, match="FAILURE_DIAGNOSTIC"):
        prepare_failure_diagnostic(candidate(tmp_path), tmp_path / "out.json", stage="browser", run_id=run_id, head=head, controlled=CONTROLLED, canary=CANARY)


def test_failure_diagnostic_rejects_controlled_input_and_output_collision(tmp_path: Path) -> None:
    source = candidate(tmp_path, CONTROLLED.decode())
    with pytest.raises(EvidenceError, match="FAILURE_DIAGNOSTIC"):
        prepare_failure_diagnostic(source, tmp_path / "out.json", stage="browser", run_id=RUN_ID, head=HEAD, controlled=CONTROLLED, canary=CANARY)

    clean = candidate(tmp_path / "clean")
    output = tmp_path / "existing.json"
    output.write_text("foreign", encoding="utf-8")
    with pytest.raises(EvidenceError, match="FAILURE_DIAGNOSTIC"):
        prepare_failure_diagnostic(clean, output, stage="browser", run_id=RUN_ID, head=HEAD, controlled=CONTROLLED, canary=CANARY)


def test_failure_diagnostic_rejects_symlink_and_oversized_log(tmp_path: Path) -> None:
    target = tmp_path / "target.log"
    target.write_text("outside", encoding="utf-8")
    source = candidate(tmp_path / "linked")
    (source / "browser.log").unlink()
    (source / "browser.log").symlink_to(target)
    with pytest.raises(EvidenceError, match="FAILURE_DIAGNOSTIC"):
        prepare_failure_diagnostic(source, tmp_path / "linked.json", stage="browser", run_id=RUN_ID, head=HEAD, controlled=CONTROLLED, canary=CANARY)

    large = candidate(tmp_path / "large", "x" * 65_537)
    with pytest.raises(EvidenceError, match="FAILURE_DIAGNOSTIC"):
        prepare_failure_diagnostic(large, tmp_path / "large.json", stage="browser", run_id=RUN_ID, head=HEAD, controlled=CONTROLLED, canary=CANARY)


def test_runner_and_workflow_publish_only_minimized_failure_diagnostic() -> None:
    root = Path(__file__).parents[2]
    runner = (root / "scripts/ci/heartbeat2-browser.sh").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "prepare_failure_diagnostic" in runner
    assert 'WITHHELD="$ROOT/reports/heartbeat2/withheld"' in runner
    assert "narratwin-heartbeat2-failure" not in runner
    assert "minimized zero-match diagnostic published" in runner
    assert "if: failure() && hashFiles('reports/heartbeat2/withheld/diagnostic.json') != ''" in workflow
    assert "path: reports/heartbeat2/withheld/diagnostic.json" in workflow
    assert "heartbeat2-withheld-diagnostic-${{ github.run_id }}-${{ github.run_attempt }}" in workflow


def ci_context(event: str = "workflow_dispatch", ref: str = "refs/heads/main") -> dict[str, str]:
    return {
        "repository": "imrohitagrawal/narratwin-ai",
        "eventName": event,
        "workflow": "ci",
        "workflowRef": f"imrohitagrawal/narratwin-ai/.github/workflows/ci.yml@{ref}",
        "workflowSha": HEAD,
        "job": "frontend",
        "runId": "31250896555",
        "runAttempt": "1",
        "headSha": HEAD,
    }


def test_ci_context_accepts_exact_main_dispatch_and_existing_events() -> None:
    assert _trusted_ci_context(ci_context(), HEAD)
    assert _trusted_ci_context(ci_context("push", "refs/heads/feature"), HEAD)
    assert _trusted_ci_context(ci_context("pull_request", "refs/pull/406/merge"), HEAD)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workflowRef", "imrohitagrawal/narratwin-ai/.github/workflows/ci.yml@refs/heads/feature"),
        ("workflowRef", "imrohitagrawal/narratwin-ai/.github/workflows/ci.yml@refs/heads/main-lookalike"),
        ("workflowSha", "f" * 40),
        ("headSha", "f" * 40),
        ("repository", "foreign/repository"),
        ("eventName", "schedule"),
        ("runAttempt", "0"),
    ],
)
def test_ci_context_rejects_foreign_or_inexact_dispatch(field: str, value: str) -> None:
    context = ci_context()
    context[field] = value
    assert not _trusted_ci_context(context, HEAD)
