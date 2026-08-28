from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.quality import check_issue16_spec_kit as gate


ROOT = Path(__file__).resolve().parents[2]


def _copy_contract(tmp_path: Path) -> Path:
    for relative in (*gate.REQUIRED_MARKDOWN, "Makefile", ".stage/current"):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return tmp_path


def _replace(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_repository_contract_is_complete() -> None:
    assert gate.validate(ROOT) == []


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
