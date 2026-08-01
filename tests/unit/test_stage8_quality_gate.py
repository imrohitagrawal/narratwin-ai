from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


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


def test_issue287_stage8_drift_branch_allows_only_governance_gate_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE287_STAGE8_DRIFT_BRANCH)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: sorted(
            {
                "docs/governance/preflights/issue-287.json",
                "docs/QUALITY_GATES.md",
                "docs/STAGE_ISSUE_PLAN.md",
                "docs/STATUS.md",
                "scripts/quality/check_phase1_closure_docs.py",
                "scripts/quality/check_stage8_docs.py",
                "tests/unit/test_phase1_closure_docs.py",
                "tests/unit/test_stage8_quality_gate.py",
            }
        ),
    )

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)

    assert failures == []


def test_issue287_stage8_drift_branch_rejects_dependency_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE287_STAGE8_DRIFT_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["frontend/package-lock.json"])

    failures: list[str] = []
    stage8.check_stage_scope(failures)

    assert failures == ["Stage 8 changed file outside the allowlist: frontend/package-lock.json"]


def test_issue289_security_unblock_branch_allows_combined_dependency_and_gate_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE289_SECURITY_UNBLOCK_BRANCH)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: sorted(
            {
                "docs/governance/preflights/issue-289.json",
                "docs/QUALITY_GATES.md",
                "docs/STAGE_ISSUE_PLAN.md",
                "docs/STATUS.md",
                "docs/ADR/0037-postcss-audit-remediation.md",
                "docs/TRACEABILITY.md",
                "docs/THIRD_PARTY_NOTICES.md",
                "frontend/package.json",
                "frontend/package-lock.json",
                "scripts/quality/check_phase1_closure_docs.py",
                "scripts/quality/check_stage8_docs.py",
                "tests/unit/test_phase1_closure_docs.py",
                "tests/unit/test_stage8_quality_gate.py",
            }
        ),
    )

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)

    assert failures == []


def test_issue289_security_unblock_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE289_SECURITY_UNBLOCK_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["backend/app/main.py"])

    failures: list[str] = []
    stage8.check_stage_scope(failures)

    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/main.py"]


def test_stage8_script_markers_match_mandatory_container_scanners() -> None:
    failures: list[str] = []
    stage8.check_dependencies_and_scripts(failures)

    assert not [failure for failure in failures if "docker scout cves" in failure]
    assert not [failure for failure in failures if "--only-severity critical,high" in failure]


def test_non_stage8_non_process_branch_still_rejected(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature/untracked-stage8-work")

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)

    assert failures == [
        "Stage 8 work must run on a stage8-* branch or main after merge; got feature/untracked-stage8-work."
    ]


def test_issue324_v2_branch_allows_only_modular_preflight_scope(monkeypatch: Any) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE324_PUBLICATION_BRANCH)
    expected = {
        "Makefile",
        "README.md",
        "docs/ADR/0047-publication-boundary.md",
        "docs/AI_BUILD_BRIEF.md",
        "docs/ARCHITECTURE.md",
        "docs/NORTH_STAR_METRICS.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/PRD.md",
        "docs/PRODUCT_STRATEGY.md",
        "docs/PUBLICATION_BOUNDARY.md",
        "docs/QUALITY_GATES.md",
        "docs/RELEASE_READINESS_REVIEW.md",
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/THREAT_MODEL.md",
        "docs/TRACEABILITY.md",
        "docs/demo/CONTROLLED_LOCAL_DEMO.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/evals/phase1_golden_questions.jsonl",
        "docs/governance/preflights/issue-324.json",
        "docs/governance/publication-boundary-v1.json",
        "portfolio/README.md",
        "scripts/quality/check_publication_boundary.py",
        "scripts/quality/check_quality_stage.py",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/publication_boundary/__init__.py",
        "scripts/quality/publication_boundary/cli.py",
        "scripts/quality/publication_boundary/contract.py",
        "scripts/quality/publication_boundary/decision.py",
        "scripts/quality/publication_boundary/repository.py",
        "scripts/quality/publication_boundary/scope.py",
        "tests/unit/publication_boundary/conftest.py",
        "tests/unit/publication_boundary/test_cli.py",
        "tests/unit/publication_boundary/test_contract.py",
        "tests/unit/publication_boundary/test_decision.py",
        "tests/unit/publication_boundary/test_repository.py",
        "tests/unit/publication_boundary/test_scope.py",
        "tests/unit/test_quality_stage_dispatch.py",
        "tests/unit/test_stage8_quality_gate.py",
    }
    assert stage8.PROCESS_BRANCH_ALLOWED_FILES[stage8.ISSUE324_PUBLICATION_BRANCH] == expected
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: sorted(expected))
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)
    assert failures == []


def test_issue324_stage8_scope_rejects_runtime_monolith_and_near_branch(
    monkeypatch: Any,
) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", stage8.ISSUE324_PUBLICATION_BRANCH)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: ["backend/app/main.py", "tests/unit/test_phase1_closure_docs.py"],
    )
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert len(failures) == 2

    monkeypatch.setenv("GITHUB_HEAD_REF", f"{stage8.ISSUE324_PUBLICATION_BRANCH}-copy")
    failures = []
    stage8.check_stage_marker_and_branch(failures)
    assert any("must run on a stage8-* branch" in failure for failure in failures)


def test_stage8_uses_neutral_controlled_demo_path() -> None:
    assert "docs/demo/CONTROLLED_LOCAL_DEMO.md" in stage8.REQUIRED_FILES
    assert "portfolio/README.md" not in stage8.REQUIRED_FILES
    assert not (stage8.ROOT / "portfolio" / "README.md").exists()
