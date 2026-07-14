from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def load_stage8_quality_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_stage8_docs.py"
    spec = importlib.util.spec_from_file_location("stage8_quality_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage8: Any = load_stage8_quality_module()


def test_issue84_guardrail_branch_allows_process_guardrail_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: [
            "docs/STATUS.md",
            "scripts/guardrails_check.py",
            "scripts/quality/check_stage8_docs.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_stage8_quality_gate.py",
        ],
    )
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)
    assert failures == []


def test_issue84_guardrail_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["backend/app/stage4.py"])
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/stage4.py"]


def test_issue157_governance_branch_allows_exact_owned_files(monkeypatch: Any) -> None:
    expected = {
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
    }
    assert stage8.PROCESS_BRANCH_ALLOWED_FILES[stage8.ISSUE157_GOVERNANCE_BRANCH] == expected
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE157_GOVERNANCE_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: sorted(expected))
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)
    assert failures == []


def test_issue157_rejects_unowned_governance_test_and_runtime_files(monkeypatch: Any) -> None:
    rejected = ["docs/TRACEABILITY.md", "tests/unit/test_guardrails_check.py", "backend/app/main.py"]
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE157_GOVERNANCE_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: rejected)
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == [f"Stage 8 changed file outside the allowlist: {path}" for path in rejected]


def test_non_stage8_non_process_branch_still_rejected(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/untracked-stage8-work")
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    assert failures == [
        "Stage 8 work must run on a stage8-* branch or main after merge; got feature/untracked-stage8-work."
    ]


def run_doc_check(monkeypatch: Any, path: str, content: str, checker: Any) -> list[str]:
    original_read = stage8.read
    monkeypatch.setattr(stage8, "read", lambda candidate: content if candidate == path else original_read(candidate))
    failures: list[str] = []
    checker(failures)
    return failures


@pytest.mark.parametrize(
    ("path", "checker"),
    [
        ("docs/SKILL_EXECUTION_PLAN.md", stage8.check_stage1_product_mode_validation_gate),
        ("docs/STATUS.md", stage8.check_mode1_status_contract),
    ],
)
def test_exact_contracts_accept_canonical_documents(path: str, checker: Any) -> None:
    failures: list[str] = []
    checker(failures)
    assert failures == []


@pytest.mark.parametrize("key", tuple(stage8.STAGE1_PRODUCT_MODE_CONTRACT))
def test_stage1_contract_rejects_every_value_mutation(monkeypatch: Any, key: str) -> None:
    path = "docs/SKILL_EXECUTION_PLAN.md"
    content = stage8.read(path)
    expected = stage8.STAGE1_PRODUCT_MODE_CONTRACT[key]
    failures = run_doc_check(
        monkeypatch,
        path,
        content.replace(f"{key}={expected}", f"{key}=wrong", 1),
        stage8.check_stage1_product_mode_validation_gate,
    )
    assert any("M1-GATE-001" in item for item in failures)


@pytest.mark.parametrize("key", ("first-slice", "avatar", "video", "audio", "interactive-q-and-a"))
def test_stage1_contract_rejects_missing_slice_boundary_keys(monkeypatch: Any, key: str) -> None:
    path = "docs/SKILL_EXECUTION_PLAN.md"
    content = stage8.read(path)
    expected = stage8.STAGE1_PRODUCT_MODE_CONTRACT[key]
    failures = run_doc_check(
        monkeypatch,
        path,
        content.replace(f"{key}={expected}\n", "", 1),
        stage8.check_stage1_product_mode_validation_gate,
    )
    assert any("M1-GATE-001" in item for item in failures)


def test_stage1_contract_rejects_missing_human_slice_boundary_prose(monkeypatch: Any) -> None:
    path = "docs/SKILL_EXECUTION_PLAN.md"
    content = stage8.read(path).replace(stage8.STAGE1_PRODUCT_MODE_PROSE, "", 1)
    failures = run_doc_check(monkeypatch, path, content, stage8.check_stage1_product_mode_validation_gate)
    assert any("M1-GATE-001" in item for item in failures)


@pytest.mark.parametrize("key", tuple(stage8.MODE1_STATUS_CONTRACT))
def test_status_contract_rejects_every_value_mutation(monkeypatch: Any, key: str) -> None:
    path = "docs/STATUS.md"
    content = stage8.read(path)
    expected = stage8.MODE1_STATUS_CONTRACT[key]
    failures = run_doc_check(
        monkeypatch,
        path,
        content.replace(f"{key}={expected}", f"{key}=wrong", 1),
        stage8.check_mode1_status_contract,
    )
    matrix_id = stage8.MODE1_STATUS_MATRIX_IDS.get(key, "STATUS-LIVE-001")
    assert any(matrix_id in item for item in failures)


@pytest.mark.parametrize(
    "replacement",
    [
        "",
        "status=active\nstatus=active",
        "status=active\nunknown=x",
        "status=active\nnot-a-record-line",
    ],
    ids=("missing", "duplicate", "unknown", "malformed-extra-line"),
)
def test_exact_contract_parser_rejects_noncanonical_key_shapes(monkeypatch: Any, replacement: str) -> None:
    path = "docs/SKILL_EXECUTION_PLAN.md"
    content = stage8.read(path).replace("status=active", replacement, 1)
    failures = run_doc_check(monkeypatch, path, content, stage8.check_stage1_product_mode_validation_gate)
    assert any("M1-GATE-001" in item for item in failures)


@pytest.mark.parametrize(
    "content",
    [
        stage8.read("docs/SKILL_EXECUTION_PLAN.md").replace(
            "## Stage 1 Product-Mode Validation Gate",
            "## Product-Mode Notes",
            1,
        ),
        stage8.read("docs/SKILL_EXECUTION_PLAN.md")
        .replace("## Stage 1 Product-Mode Validation Gate", "<!--\n## Stage 1 Product-Mode Validation Gate", 1)
        .replace("\n## Activation Rules", "\n-->\n\n## Activation Rules", 1),
    ],
    ids=("displaced", "comment-hidden"),
)
def test_stage1_contract_requires_one_active_canonical_section(monkeypatch: Any, content: str) -> None:
    failures = run_doc_check(
        monkeypatch,
        "docs/SKILL_EXECUTION_PLAN.md",
        content,
        stage8.check_stage1_product_mode_validation_gate,
    )
    assert any("M1-GATE-001" in item for item in failures)


@pytest.mark.parametrize(
    ("path", "checker", "heading", "matrix_id"),
    [
        (
            "docs/SKILL_EXECUTION_PLAN.md",
            stage8.check_stage1_product_mode_validation_gate,
            "## Stage 1 Product-Mode Validation Gate",
            "M1-GATE-001",
        ),
        (
            "docs/STATUS.md",
            stage8.check_mode1_status_contract,
            "## Mode 1 Audited Status Contract",
            "STATUS-LIVE-001",
        ),
    ],
)
@pytest.mark.parametrize("hidden_by", ("tilde-fence", "indent"))
def test_contract_headings_must_be_visible_column_zero_markdown(
    monkeypatch: Any,
    path: str,
    checker: Any,
    heading: str,
    matrix_id: str,
    hidden_by: str,
) -> None:
    content = stage8.read(path)
    if hidden_by == "tilde-fence":
        content = f"~~~markdown\n{content}\n~~~"
    else:
        content = content.replace(heading, f"    {heading}", 1)

    failures = run_doc_check(monkeypatch, path, content, checker)

    assert any(matrix_id in item for item in failures)


@pytest.mark.parametrize(
    ("path", "checker"),
    [
        (
            "docs/SKILL_EXECUTION_PLAN.md",
            stage8.check_stage1_product_mode_validation_gate,
        ),
        (
            "docs/STATUS.md",
            stage8.check_mode1_status_contract,
        ),
    ],
)
def test_mixed_fence_runs_cannot_expose_a_hidden_contract(
    monkeypatch: Any,
    path: str,
    checker: Any,
) -> None:
    content = f"````markdown\n```~\n{stage8.read(path)}\n````"

    failures = run_doc_check(monkeypatch, path, content, checker)

    assert failures


@pytest.mark.parametrize(
    ("path", "checker"),
    [
        (
            "docs/SKILL_EXECUTION_PLAN.md",
            stage8.check_stage1_product_mode_validation_gate,
        ),
        (
            "docs/STATUS.md",
            stage8.check_mode1_status_contract,
        ),
    ],
)
def test_fence_info_strings_may_start_with_the_other_fence_character(
    monkeypatch: Any,
    path: str,
    checker: Any,
) -> None:
    content = f"```~markdown\n{stage8.read(path)}"

    failures = run_doc_check(monkeypatch, path, content, checker)

    assert failures
