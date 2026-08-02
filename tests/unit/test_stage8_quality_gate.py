from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from scripts.guardrails_check import canonical_stage_issue


TRANSITION_BRANCH = "cut1-process-346-governance-transition"
ISSUE335_BRANCH = "cut1-335-r0c-a2-1-stage4-rag-v1-lineage"
TRANSITION_FILES = {
    "docs/governance/preflights/issue-346.json", "scripts/quality/check_stage8_docs.py",
    "tests/unit/test_stage8_quality_gate.py", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
}
ISSUE335_FILES = {
    "docs/governance/preflights/issue-335.json", "tests/unit/test_retrieval_strategy_v1_contract.py",
    "backend/app/rag/models.py", "backend/app/stage4.py", "docs/API_CONTRACT.md", "docs/STATUS.md",
}


def load_stage8_quality_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_stage8_docs.py"
    spec = importlib.util.spec_from_file_location("stage8_quality_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage8: Any = load_stage8_quality_module()


def load_quality_dispatcher_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_quality_stage.py"
    spec = importlib.util.spec_from_file_location("quality_dispatcher_under_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def write(repo: Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def init_repo(repo: Path) -> str:
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Scope Test")
    git(repo, "config", "user.email", "scope@example.invalid")
    write(repo, "base.txt", "base\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    return git(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize(
    ("branch", "expected"),
    ((TRANSITION_BRANCH, TRANSITION_FILES), (ISSUE335_BRANCH, ISSUE335_FILES)),
)
def test_exact_cut1_branch_uses_literal_allowlist(
    monkeypatch: Any, branch: str, expected: set[str]
) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: sorted(expected))

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)

    assert failures == []


@pytest.mark.parametrize("branch", (TRANSITION_BRANCH, ISSUE335_BRANCH))
def test_exact_cut1_branch_dispatches_stage8_without_issue13_binding(
    monkeypatch: Any, tmp_path: Path, branch: str
) -> None:
    dispatcher: Any = load_quality_dispatcher_module()
    stage = tmp_path / "current"
    status = tmp_path / "STATUS.md"
    stage.write_text("8\n", encoding="utf-8")
    status.write_text(
        "| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure |\n",
        encoding="utf-8",
    )
    calls: list[list[str]] = []
    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage)
    monkeypatch.setattr(dispatcher, "STATUS_DOC", status)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: branch)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda _stage: 0)
    def record_call(args: list[str], cwd: Path) -> int:
        calls.append(args)
        return 0
    monkeypatch.setattr(dispatcher.subprocess, "call", record_call)

    assert dispatcher.main() == 0
    assert calls == [["make", "stage8-quality"]]
    assert canonical_stage_issue(branch) is None


@pytest.mark.parametrize(
    "branch",
    (
        f"{TRANSITION_BRANCH}-copy", f"{TRANSITION_BRANCH}-retry",
        f"{TRANSITION_BRANCH}/child", "cut1-process-347-governance-transition",
        f"{ISSUE335_BRANCH}-copy", f"{ISSUE335_BRANCH}-retry",
        f"{ISSUE335_BRANCH}/child", "cut1-336-r0c-a2-1-stage4-rag-v1-lineage",
        "cut1-proces\u0455-346-governance-transition",
    ),
)
def test_near_cut1_branch_fails_closed(monkeypatch: Any, branch: str) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["backend/app/stage4.py"])

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)

    assert any("Stage 8 work must run" in failure for failure in failures)
    assert f"Stage 8 scope requires an exact reviewed branch; got {branch}." in failures


@pytest.mark.parametrize(
    ("branch", "unexpected"),
    ((TRANSITION_BRANCH, "backend/app/stage4.py"), (ISSUE335_BRANCH, "backend/app/main.py")),
)
def test_exact_cut1_route_rejects_broad_stage8_path(
    monkeypatch: Any, branch: str, unexpected: str
) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: [unexpected])
    failures: list[str] = []

    stage8.check_stage_scope(failures)

    assert failures == [f"Stage 8 changed file outside the allowlist: {unexpected}"]


@pytest.mark.parametrize(
    ("branch", "expected", "extra"),
    (
        (TRANSITION_BRANCH, TRANSITION_FILES, "docs/API_CONTRACT.md"),
        (ISSUE335_BRANCH, ISSUE335_FILES, "scripts/quality/check_stage8_docs.py"),
    ),
)
def test_exact_cut1_route_rejects_seventh_path(
    monkeypatch: Any, branch: str, expected: set[str], extra: str
) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: sorted(expected | {extra}))
    failures: list[str] = []

    stage8.check_stage_scope(failures)

    assert failures == [f"Stage 8 changed file outside the allowlist: {extra}"]


def test_transition_preflight_is_supporting_evidence_not_policy_input(
    monkeypatch: Any,
) -> None:
    artifact = json.loads(
        (Path(__file__).parents[2] / "docs/governance/preflights/issue-346.json").read_text(
            encoding="utf-8"
        )
    )
    assert artifact["branch"] == TRANSITION_BRANCH
    assert set(artifact["scope"]["required"]) == TRANSITION_FILES
    real_read_text = Path.read_text

    def reject_policy_read(path: Path, *args: Any, **kwargs: Any) -> str:
        if path.name in {"issue-346.json", "issue-335.json"}:
            raise AssertionError("Cut 1 policy must not load mutable preflight scope")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", reject_policy_read)
    reloaded: Any = load_stage8_quality_module()
    assert reloaded.PROCESS_BRANCH_ALLOWED_FILES[TRANSITION_BRANCH] == TRANSITION_FILES


@pytest.mark.parametrize(
    ("payload", "expected"),
    (
        ("M\0path with\nnewline\0", ["path with\nnewline"]),
        ("D\0deleted.txt\0", ["deleted.txt"]),
        ("R087\0old.txt\0new.txt\0", ["old.txt", "new.txt"]),
        ("C064\0source.txt\0copy.txt\0", ["source.txt", "copy.txt"]),
    ),
)
def test_name_status_parser_preserves_all_paths(payload: str, expected: list[str]) -> None:
    assert stage8.parse_name_status_z(payload) == expected


@pytest.mark.parametrize(
    "payload",
    (
        "R100\0old.txt\0",
        "M\0path.txt",
        "M\0\0",
        "Q\0path.txt\0",
        "R101\0old.txt\0new.txt\0",
    ),
)
def test_name_status_parser_rejects_malformed_records(payload: str) -> None:
    with pytest.raises(RuntimeError):
        stage8.parse_name_status_z(payload)


def test_scope_collection_uses_merge_base_to_exact_head(
    monkeypatch: Any, tmp_path: Path
) -> None:
    base = init_repo(tmp_path)
    git(tmp_path, "checkout", "-b", "feature")
    write(tmp_path, "feature.txt", "feature\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "feature")
    head = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "checkout", "main")
    write(tmp_path, "main-only.txt", "main\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "main advance")
    git(tmp_path, "checkout", "feature")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.setenv("GITHUB_BASE_SHA", git(tmp_path, "rev-parse", "main"))
    monkeypatch.setenv("GITHUB_HEAD_SHA", head)

    assert stage8.changed_files_for_stage_scope() == ["feature.txt"]
    assert git(tmp_path, "merge-base", "main", head) == base


def test_scope_collection_includes_committed_cached_unstaged_and_untracked(
    monkeypatch: Any, tmp_path: Path
) -> None:
    init_repo(tmp_path)
    for path in ("cached-source.txt", "unstaged-source.txt", "cancelled.txt"):
        write(tmp_path, path, "original\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "tracked fixtures")
    git(tmp_path, "checkout", "-b", "feature")
    write(tmp_path, "committed.txt", "committed\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "feature")
    git(tmp_path, "mv", "cached-source.txt", "cached-destination.txt")
    (tmp_path / "unstaged-source.txt").rename(tmp_path / "unstaged-destination.txt")
    write(tmp_path, "cancelled.txt", "staged\n")
    git(tmp_path, "add", "cancelled.txt")
    write(tmp_path, "cancelled.txt", "original\n")
    write(tmp_path, "untracked\nnewline.txt", "untracked\n")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_SHA", raising=False)

    assert stage8.changed_files_for_stage_scope() == [
        "cached-destination.txt", "cached-source.txt", "cancelled.txt", "committed.txt",
        "unstaged-destination.txt", "unstaged-source.txt",
        "untracked\nnewline.txt",
    ]


def test_scope_collection_includes_rename_and_copy_sources_and_destinations(
    monkeypatch: Any, tmp_path: Path
) -> None:
    init_repo(tmp_path)
    write(tmp_path, "forbidden/rename-source.txt", "unique rename\n")
    write(tmp_path, "forbidden/copy-source.txt", "unique copy\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "sources")
    git(tmp_path, "checkout", "-b", "feature")
    git(tmp_path, "mv", "forbidden/rename-source.txt", "rename-destination.txt")
    write(tmp_path, "copy-destination.txt", "unique copy\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "rename and copy")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)
    monkeypatch.delenv("GITHUB_HEAD_SHA", raising=False)

    paths = stage8.changed_files_for_stage_scope()
    assert set(paths) == {
        "forbidden/rename-source.txt",
        "rename-destination.txt",
        "forbidden/copy-source.txt",
        "copy-destination.txt",
    }
    monkeypatch.setattr(stage8, "current_branch", lambda: TRANSITION_BRANCH)
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert "Stage 8 changed file outside the allowlist: forbidden/rename-source.txt" in failures
    assert "Stage 8 changed file outside the allowlist: forbidden/copy-source.txt" in failures


def test_scope_collection_rejects_wrong_exact_head(monkeypatch: Any, tmp_path: Path) -> None:
    base = init_repo(tmp_path)
    git(tmp_path, "checkout", "-b", "feature")
    write(tmp_path, "feature.txt", "feature\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "feature")
    monkeypatch.setattr(stage8, "ROOT", tmp_path)
    monkeypatch.setenv("GITHUB_HEAD_SHA", base)

    with pytest.raises(RuntimeError, match="exact head"):
        stage8.changed_files_for_stage_scope()


@pytest.mark.parametrize(
    "failed_layer", ("rev-parse", "merge-base", "committed", "cached", "unstaged", "untracked")
)
def test_scope_collection_rejects_partial_git_evidence(
    monkeypatch: Any, failed_layer: str
) -> None:
    def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            layer = "rev-parse"
            output = "head\n"
        elif args[:2] == ["git", "merge-base"]:
            layer = "merge-base"
            output = "base\n"
        elif "ls-files" in args:
            layer, output = "untracked", ""
        elif "--cached" in args:
            layer, output = "cached", ""
        elif any(".." in arg for arg in args):
            layer, output = "committed", ""
        else:
            layer, output = "unstaged", ""
        return subprocess.CompletedProcess(
            args, 1 if layer == failed_layer else 0, output, "failed"
        )

    monkeypatch.setattr(stage8, "run", fake_run)
    monkeypatch.setenv("GITHUB_BASE_SHA", "base")
    monkeypatch.setenv("GITHUB_HEAD_SHA", "head")

    with pytest.raises(RuntimeError, match="failed"):
        stage8.changed_files_for_stage_scope()


def test_all_tracked_scope_layers_use_nul_rename_copy_flags(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fake_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        output = "head\n" if "rev-parse" in args else "base\n" if "merge-base" in args else ""
        return subprocess.CompletedProcess(args, 0, output, "")

    monkeypatch.setattr(stage8, "run", fake_run)
    monkeypatch.setenv("GITHUB_BASE_SHA", "base")
    monkeypatch.setenv("GITHUB_HEAD_SHA", "head")
    stage8.changed_files_for_stage_scope()

    diffs = [args for args in calls if args[:2] == ["git", "diff"]]
    assert len(diffs) == 3
    for args in diffs:
        assert {"--name-status", "-z", "--find-renames", "--find-copies", "--find-copies-harder"} <= set(args)


def test_issue84_guardrail_branch_allows_process_guardrail_files(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE84_GUARDRAIL_BRANCH)
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
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["backend/app/stage4.py"])

    failures: list[str] = []
    stage8.check_stage_scope(failures)

    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/stage4.py"]


def test_issue287_stage8_drift_branch_allows_only_governance_gate_files(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE287_STAGE8_DRIFT_BRANCH)
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
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE287_STAGE8_DRIFT_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["frontend/package-lock.json"])

    failures: list[str] = []
    stage8.check_stage_scope(failures)

    assert failures == ["Stage 8 changed file outside the allowlist: frontend/package-lock.json"]


def test_issue289_security_unblock_branch_allows_combined_dependency_and_gate_files(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE289_SECURITY_UNBLOCK_BRANCH)
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
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE289_SECURITY_UNBLOCK_BRANCH)
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
    monkeypatch.setattr(stage8, "current_branch", lambda: "feature/untracked-stage8-work")

    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)

    assert failures == [
        "Stage 8 work must run on a stage8-* branch or main after merge; got feature/untracked-stage8-work."
    ]
