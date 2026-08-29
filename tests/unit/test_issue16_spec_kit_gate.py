from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from scripts.quality import check_issue16_spec_kit as gate


ROOT = Path(__file__).resolve().parents[2]
ISSUE16_BRANCH = "stage1-16-spec-kit-gate"
ISSUE16_ACCEPTED_SHA = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
ISSUE16_GATE_COMMAND = [sys.executable, "scripts/quality/check_issue16_spec_kit.py"]


def _load_dispatcher() -> ModuleType:
    module_path = ROOT / "scripts/quality/check_quality_stage.py"
    spec = importlib.util.spec_from_file_location("issue16_dispatcher_under_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_dispatcher(
    monkeypatch: Any, tmp_path: Path, *, branch: str, policy_only: bool = False
) -> list[list[str]]:
    dispatcher = _load_dispatcher()
    stage_file = tmp_path / "current"
    stage_file.write_text("8", encoding="utf-8")
    status_file = tmp_path / "STATUS.md"
    status_file.write_text("# status", encoding="utf-8")
    calls: list[list[str]] = []
    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(dispatcher, "STATUS_DOC", status_file)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: branch)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda stage: 0)

    def record_call(args: list[str], **kwargs: object) -> int:
        del kwargs
        calls.append(list(args))
        return 0

    monkeypatch.setattr(dispatcher.subprocess, "call", record_call)
    if policy_only:
        monkeypatch.setenv("NARRATWIN_POLICY_ONLY", "1")
    else:
        monkeypatch.delenv("NARRATWIN_POLICY_ONLY", raising=False)
    assert dispatcher.main() == 0
    return calls


def test_issue16_exact_branch_dispatches_only_dedicated_gate(
    monkeypatch: Any, tmp_path: Path
) -> None:
    assert _run_dispatcher(monkeypatch, tmp_path, branch=ISSUE16_BRANCH) == [
        ISSUE16_GATE_COMMAND
    ]


def test_issue16_policy_only_cannot_bypass_dedicated_gate(
    monkeypatch: Any, tmp_path: Path
) -> None:
    assert _run_dispatcher(
        monkeypatch, tmp_path, branch=ISSUE16_BRANCH, policy_only=True
    ) == [ISSUE16_GATE_COMMAND]


def test_issue16_gate_failure_is_propagated(monkeypatch: Any) -> None:
    dispatcher = _load_dispatcher()
    monkeypatch.setattr(dispatcher, "current_branch", lambda: ISSUE16_BRANCH)
    monkeypatch.setattr(dispatcher, "run_issue16_spec_kit_gate", lambda: 17)
    assert dispatcher.main() == 17


def test_issue16_near_match_receives_no_route_authority(
    monkeypatch: Any, tmp_path: Path
) -> None:
    assert _run_dispatcher(
        monkeypatch, tmp_path, branch=f"{ISSUE16_BRANCH}-extra"
    ) == [["make", "stage8-quality"]]


def _copy_contract(tmp_path: Path) -> Path:
    content, _, _, _, _ = gate.historical_snapshot(ROOT)
    for relative, text in content.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return tmp_path


def _replace(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_repository_contract_is_complete() -> None:
    assert gate.validate(ROOT) == []


def test_historical_contract_is_pinned_to_the_accepted_issue16_snapshot() -> None:
    assert gate.ACCEPTED_SHA == ISSUE16_ACCEPTED_SHA


def test_successor_branch_does_not_inherit_issue16_live_route_authority(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(gate, "current_branch", lambda root: "security-460-semgrep-override-removal")
    monkeypatch.setattr(
        gate,
        "repository_snapshot",
        lambda root: (_ for _ in ()).throw(AssertionError("live Issue #16 route evaluated")),
    )
    assert gate.validate(ROOT) == []


def test_successor_branch_fails_closed_when_accepted_snapshot_is_unavailable(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(gate, "current_branch", lambda root: "security-460-semgrep-override-removal")
    monkeypatch.setattr(
        gate,
        "historical_snapshot",
        lambda root: (_ for _ in ()).throw(RuntimeError("accepted object unavailable")),
    )
    assert gate.validate(ROOT) == ["I16.HISTORICAL.SNAPSHOT"]


@pytest.mark.parametrize(
    ("relative", "old", "new", "expected"),
    (
        (
            ".specify/memory/constitution.md",
            "No implementation before the gate",
            "Implementation may precede the gate",
            "I16.CONSTITUTION.PRINCIPLE",
        ),
        (
            "specs/001-grounded-walkthrough-script/spec.md",
            "FR-009",
            "FR-XXX",
            "I16.SPEC.REQUIREMENT",
        ),
        (
            "specs/001-grounded-walkthrough-script/spec.md",
            "NFR-012",
            "NFR-XXX",
            "I16.SPEC.REQUIREMENT",
        ),
        (
            "specs/001-grounded-walkthrough-script/plan.md",
            "Gate order: constitution -> spec -> plan -> tasks -> review checkpoint -> future issue",
            "Gate order: future issue -> implementation",
            "I16.PLAN.ORDER",
        ),
        (
            "specs/001-grounded-walkthrough-script/tasks.md",
            "LA-C1-T08",
            "LA-C1-TXX",
            "I16.TASK.IDS",
        ),
        (
            "specs/001-grounded-walkthrough-script/tasks.md",
            "Future Lane A Cut 1 issue: TBD after Issue #16 closes",
            "Future Lane A Cut 1 issue: #999",
            "I16.ISSUE.SEQUENCING",
        ),
        (
            "docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md",
            "REVIEWED_PENDING_IMPLEMENTATION_ISSUE",
            "IMPLEMENTATION_AUTHORIZED",
            "I16.REVIEW.CHECKPOINT",
        ),
        (
            "docs/STATUS.md",
            "Issue #16 specification-gate target state",
            "Issue #16 specification-gate draft",
            "I16.STATUS.TARGET",
        ),
        (
            "docs/STATUS.md",
            "Issue #456 Cut 1 live-binding prerequisite — merged and closed",
            "Issue #456 Cut 1 live-binding prerequisite — implementation complete, review pending",
            "I16.STATUS.STALE_456",
        ),
        (
            "docs/TRACEABILITY.md",
            "I16-GATE-01",
            "I16-GATE-XX",
            "I16.TRACEABILITY",
        ),
        (
            "docs/QUALITY_GATES.md",
            "make issue16-spec-quality",
            "make missing-issue16-gate",
            "I16.QUALITY.DOC",
        ),
        (
            "docs/STAGE_ISSUE_PLAN.md",
            "Post-gate Lane A sequencing",
            "Immediate Lane A implementation",
            "I16.STAGE.PLAN",
        ),
        (
            "Makefile",
            "issue16-spec-quality:",
            "issue16-spec-quality-disabled:",
            "I16.MAKE.TARGET",
        ),
        (
            ".stage/current",
            "8",
            "1",
            "I16.STAGE.CURRENT",
        ),
    ),
)
def test_each_load_bearing_mutation_fails_closed(
    tmp_path: Path, relative: str, old: str, new: str, expected: str
) -> None:
    root = _copy_contract(tmp_path)
    _replace(root, relative, old, new)
    assert expected in gate.validate(root)


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    root = _copy_contract(tmp_path)
    (root / "specs/001-grounded-walkthrough-script/tasks.md").unlink()
    assert "I16.ARTIFACT.MISSING" in gate.validate(root)


def test_task_graph_rejects_unknown_or_forward_dependencies(tmp_path: Path) -> None:
    root = _copy_contract(tmp_path)
    _replace(
        root,
        "specs/001-grounded-walkthrough-script/tasks.md",
        "| LA-C1-T03 |",
        "| LA-C1-T03 | LA-C1-T08,",
    )
    assert "I16.TASK.DEPENDENCY" in gate.validate(root)


def test_external_spec_kit_activation_claim_fails_closed(tmp_path: Path) -> None:
    root = _copy_contract(tmp_path)
    constitution = root / ".specify/memory/constitution.md"
    constitution.write_text(
        constitution.read_text(encoding="utf-8")
        + "\nGitHub Spec Kit is installed and activated for this repository.\n",
        encoding="utf-8",
    )
    assert "I16.SPECKIT.ACTIVATION" in gate.validate(root)


def test_scope_snapshot_rejects_path_binding_and_budget_mutations() -> None:
    artifact = gate.load_preflight(ROOT)
    required = artifact["scope"]["required"]
    charges = {path: 1 for path in required}

    def check(
        candidate: dict[str, Any] = artifact,
        *, branch: str = gate.ISSUE16_BRANCH,
        ancestor: bool = True,
        changed: list[str] = required,
        charged: dict[str, int] = charges,
    ) -> list[str]:
        return gate.validate_scope_snapshot(
            candidate, branch=branch, base_is_ancestor=ancestor,
            changed_files=changed, charged_lines=charged,
        )

    assert check() == []
    unauthorized = "frontend/unauthorized.ts"
    assert "I16.SCOPE.PATHS" in check(
        changed=[*required, unauthorized], charged={**charges, unauthorized: 1}
    )
    assert "I16.SCOPE.BINDING" in check(branch=f"{gate.ISSUE16_BRANCH}-extra")
    assert "I16.SCOPE.HISTORY" in check(ancestor=False)
    assert "I16.SCOPE.FILE_BUDGET" in check(charged={**charges, "docs/STATUS.md": 301})
    assert "I16.SCOPE.TOTAL_BUDGET" in check(charged={path: 200 for path in required})

    substituted = "frontend/unauthorized.ts"
    mutated_required = [substituted if path == "docs/TRACEABILITY.md" else path for path in required]
    mutated = {
        **artifact,
        "scope": {
            **artifact["scope"],
            "required": mutated_required,
            "allowed_prefixes": list(mutated_required),
        },
    }
    assert "I16.SCOPE.PATHS" in check(
        mutated, changed=mutated_required,
        charged={path: 1 for path in mutated_required},
    )
    forbidden_mutation = {**artifact, "scope": {**artifact["scope"], "forbidden": []}}
    assert "I16.SCOPE.PATHS" in check(forbidden_mutation)


def test_numstat_parser_rejects_duplicate_path_records() -> None:
    raw = b"1\t2\tdocs/STATUS.md\0" + b"3\t4\tdocs/STATUS.md\0"
    with pytest.raises(RuntimeError, match="duplicate numstat record"):
        gate._charged_lines(raw)


def test_live_repository_snapshot_is_part_of_validation(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_HEAD_REF", gate.ISSUE16_BRANCH)
    assert gate._branch_identity("") == gate.ISSUE16_BRANCH
    artifact = gate.load_preflight(ROOT)
    required = artifact["scope"]["required"]
    monkeypatch.setattr(gate, "current_branch", lambda root: gate.ISSUE16_BRANCH)
    monkeypatch.setattr(
        gate,
        "repository_snapshot",
        lambda root: (
            f"{gate.ISSUE16_BRANCH}-extra",
            True,
            required,
            {path: 1 for path in required},
        ),
    )

    assert "I16.SCOPE.BINDING" in gate.validate(ROOT)
