import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def load_dispatcher() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_quality_stage.py"
    spec = importlib.util.spec_from_file_location("quality_dispatcher_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_dispatcher(
    monkeypatch: Any,
    tmp_path: Path,
    *,
    branch: str,
    stage_marker: str = "8",
    status_text: str,
    policy_only: bool = False,
) -> list[list[str]]:
    dispatcher = load_dispatcher()
    stage_file = tmp_path / "current"
    stage_file.write_text(stage_marker, encoding="utf-8")
    status_file = tmp_path / "STATUS.md"
    status_file.write_text(status_text, encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(dispatcher, "STATUS_DOC", status_file, raising=False)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: branch)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda stage: 0)

    def record_subprocess_call(
        args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
    ) -> int:
        del cwd, env
        calls.append(list(args))
        return 0

    monkeypatch.setattr(dispatcher.subprocess, "call", record_subprocess_call)
    if policy_only:
        monkeypatch.setenv("NARRATWIN_POLICY_ONLY", "1")
    else:
        monkeypatch.delenv("NARRATWIN_POLICY_ONLY", raising=False)

    assert dispatcher.main() == 0
    return calls


PHASE1_STATUS_ROW = (
    "| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure | "
    "Phase 1 Closure remains active; release posture remains No-Go. |"
)

PHASE1_STATUS = f"""
# Program Status

## StatusStateV1

| ID | State kind | Owner | Expected status | Current status | Contract |
|---|---|---|---|---|---|
{PHASE1_STATUS_ROW}
""".strip()


STAGE8_STATUS = """
# Program Status

## StatusStateV1

| ID | State kind | Owner | Expected status | Current status | Contract |
|---|---|---|---|---|---|
| SSV1-MODE | repo-mode | Stage 8 | stage8 | stage8 | Stage 8 hardening mode. |
""".strip()

ISSUE435_BRANCH = "governance-435-adversarial-convergence-framework-v1"
ISSUE435_ROUTE_COMMAND = [sys.executable, "-I", "-P", "scripts/quality/adversarial_convergence.py", "--route-only"]
ISSUE435_ACCEPTANCE_COMMAND = [
    sys.executable,
    *"-I -P -m pytest -p no:cacheprovider -o addopts= -q tests/unit/test_adversarial_convergence.py".split(),
]


def test_issue435_exact_branch_dispatches_only_dedicated_gate(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch=ISSUE435_BRANCH,
        status_text=PHASE1_STATUS,
    )

    assert calls == [ISSUE435_ROUTE_COMMAND, ISSUE435_ACCEPTANCE_COMMAND]


def test_issue435_policy_only_cannot_bypass_dedicated_gate(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch=ISSUE435_BRANCH,
        status_text=STAGE8_STATUS,
        policy_only=True,
    )

    assert calls == [ISSUE435_ROUTE_COMMAND, ISSUE435_ACCEPTANCE_COMMAND]


def test_issue435_runner_uses_exact_argv_cwd_and_scrubbed_environment(monkeypatch: Any) -> None:
    dispatcher = load_dispatcher()
    inherited = {
        "PATH": "/bad", "TMPDIR": "/trusted/tmp", "PYTHONPATH": "/bad", "PYTEST_ADDOPTS": "-k nothing",
        "GITHUB_HEAD_REF": ISSUE435_BRANCH, "GITHUB_BASE_SHA": "b" * 40, "GITHUB_HEAD_SHA": "a" * 40,
    }
    observed: list[tuple[list[str], Path, dict[str, str]]] = []

    def record_call(args: list[str], *, cwd: Path, env: dict[str, str]) -> int:
        observed.append((list(args), cwd, env))
        return 0

    monkeypatch.setattr(dispatcher.os, "environ", inherited)
    monkeypatch.setattr(dispatcher.subprocess, "call", record_call)

    assert dispatcher.run_adversarial_convergence_gate() == 0
    assert [row[0] for row in observed] == [ISSUE435_ROUTE_COMMAND, ISSUE435_ACCEPTANCE_COMMAND]
    expected_env = {
        "LC_ALL": "C", "PATH": dispatcher.os.defpath, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "TMPDIR": "/trusted/tmp", "GITHUB_HEAD_REF": ISSUE435_BRANCH,
        "GITHUB_BASE_SHA": "b" * 40, "GITHUB_HEAD_SHA": "a" * 40,
    }
    assert all(cwd == dispatcher.ROOT and env == expected_env for _, cwd, env in observed)


def test_issue435_route_failure_stops_before_acceptance(monkeypatch: Any) -> None:
    dispatcher = load_dispatcher()
    calls: list[list[str]] = []
    def fail(args: list[str], **kwargs: object) -> int:
        calls.append(args)
        return 17
    monkeypatch.setattr(dispatcher.subprocess, "call", fail)
    assert dispatcher.run_adversarial_convergence_gate() == 17
    assert calls == [ISSUE435_ROUTE_COMMAND]


def test_issue435_acceptance_runner_exit_is_propagated(monkeypatch: Any) -> None:
    dispatcher = load_dispatcher()
    monkeypatch.setattr(dispatcher, "current_branch", lambda: ISSUE435_BRANCH)
    monkeypatch.setattr(dispatcher, "run_adversarial_convergence_gate", lambda: 17)

    assert dispatcher.main() == 17


def test_issue435_near_match_receives_no_route_authority(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch=f"{ISSUE435_BRANCH}-evil",
        status_text=STAGE8_STATUS,
    )

    assert calls == [["make", "stage8-quality"]]


def test_main_dispatches_phase1_closure_when_status_state_says_phase1(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(monkeypatch, tmp_path, branch="main", status_text=PHASE1_STATUS)

    assert len(calls) == 1
    assert calls[0][-1] == "scripts/quality/check_phase1_quality.py"


def test_phase1_closure_branch_dispatch_still_uses_phase1_gate(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch="phase-1-closure-208-ch-m1-02-demo-evidence",
        status_text=STAGE8_STATUS,
    )

    assert calls[0][-1] == "scripts/quality/check_phase1_quality.py"


def test_main_stage8_dispatch_is_preserved_when_status_state_is_not_phase1(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(monkeypatch, tmp_path, branch="main", status_text=STAGE8_STATUS)

    assert calls == [["make", "stage8-quality"]]


def test_stage8_policy_only_dispatch_is_preserved_when_status_state_is_not_phase1(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls = run_dispatcher(monkeypatch, tmp_path, branch="main", status_text=STAGE8_STATUS, policy_only=True)

    assert calls[0][-1] == "scripts/quality/check_stage8_docs.py"


def test_stage8_branch_dispatch_is_not_weakened_by_phase1_status(monkeypatch: Any, tmp_path: Path) -> None:
    calls = run_dispatcher(
        monkeypatch,
        tmp_path,
        branch="stage8-performance-security-release-readiness",
        status_text=PHASE1_STATUS,
    )

    assert calls == [["make", "stage8-quality"]]


def test_dispatcher_rejects_unavailable_branch_evidence(monkeypatch: Any, tmp_path: Path) -> None:
    dispatcher = load_dispatcher()
    stage_file = tmp_path / "current"
    stage_file.write_text("8\n", encoding="utf-8")
    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: "")

    assert dispatcher.main() == 1


def test_touched_quality_scripts_bootstrap_imports_outside_repository(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    command = "import runpy,sys; runpy.run_path(sys.argv[1], run_name='import_smoke')"
    for relative_path in (
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/check_stage8_docs.py",
    ):
        result = subprocess.run(
            [sys.executable, "-c", command, str(root / relative_path)],
            cwd=tmp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
