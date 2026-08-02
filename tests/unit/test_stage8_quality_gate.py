from __future__ import annotations
# ruff: noqa: E302, E305, E701, E702

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from scripts.guardrails_check import canonical_stage_issue
TRANSITION = "cut1-process-346-governance-transition"
A2_1 = "cut1-335-r0c-a2-1-stage4-rag-v1-lineage"
SCOPES = {
    TRANSITION: {"docs/governance/preflights/issue-346.json", "scripts/quality/check_stage8_docs.py",
                 "tests/unit/test_stage8_quality_gate.py", "docs/QUALITY_GATES.md",
                 "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md"},
    A2_1: {"docs/governance/preflights/issue-335.json", "tests/unit/test_retrieval_strategy_v1_contract.py",
           "backend/app/rag/models.py", "backend/app/stage4.py", "docs/API_CONTRACT.md", "docs/STATUS.md"},
}
def load_module(relative: str, name: str) -> ModuleType:
    module_path = Path(__file__).parents[2] / relative
    spec = importlib.util.spec_from_file_location(name, module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

stage8: Any = load_module("scripts/quality/check_stage8_docs.py", "stage8_quality_under_test")

def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()

def put(repo: Path, path: str, value: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")

def test_cut1_routes_are_exact_stage8_and_not_preflight_owned(monkeypatch: Any, tmp_path: Path) -> None:
    for branch, scope in SCOPES.items():
        monkeypatch.setattr(stage8, "current_branch", lambda branch=branch: branch)
        monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda scope=scope: sorted(scope))
        failures: list[str] = []
        stage8.check_stage_marker_and_branch(failures); stage8.check_stage_scope(failures)
        assert failures == []
        extra = "backend/app/main.py" if branch == A2_1 else "backend/app/stage4.py"
        monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda extra=extra: [extra])
        failures = []; stage8.check_stage_scope(failures)
        assert failures == [f"Stage 8 changed file outside the allowlist: {extra}"]
    for branch in (f"{TRANSITION}-retry", f"{TRANSITION}/child", "cut1-process-347-governance-transition",
                   f"{A2_1}-copy", "cut1-336-r0c-a2-1-stage4-rag-v1-lineage", "cut1-proces\u0455-346-transition"):
        monkeypatch.setattr(stage8, "current_branch", lambda branch=branch: branch)
        failures = []; stage8.check_stage_marker_and_branch(failures); stage8.check_stage_scope(failures)
        assert len(failures) == 2
    artifact = json.loads((Path(__file__).parents[2] / "docs/governance/preflights/issue-346.json").read_text())
    assert artifact["branch"] == TRANSITION and set(artifact["scope"]["required"]) == SCOPES[TRANSITION]
    original_read = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda path, *a, **kw: (_ for _ in ()).throw(AssertionError())
                        if path.name in {"issue-346.json", "issue-335.json"} else original_read(path, *a, **kw))
    policy = load_module("scripts/quality/check_stage8_docs.py", "reloaded").PROCESS_BRANCH_ALLOWED_FILES
    assert {branch: policy[branch] for branch in SCOPES} == SCOPES
    assert {branch for branch in policy if branch.startswith("cut1-")} == set(SCOPES)
    dispatcher: Any = load_module("scripts/quality/check_quality_stage.py", "dispatcher")
    stage_file, status_file = tmp_path / "stage", tmp_path / "status"
    mode = "| SSV1-MODE | repo-mode | Phase 1 Closure | phase1-closure | phase1-closure |\n"
    stage_file.write_text("8\n"); status_file.write_text(mode)
    calls: list[list[str]] = []
    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", stage_file)
    monkeypatch.setattr(dispatcher, "STATUS_DOC", status_file)
    monkeypatch.setattr(dispatcher, "run_recommended_review_item_check", lambda _stage: 0)
    def record(args: list[str], cwd: Path) -> int:
        calls.append(args); return 0
    monkeypatch.setattr(dispatcher.subprocess, "call", record)
    for branch in SCOPES:
        calls.clear(); monkeypatch.setattr(dispatcher, "current_branch", lambda branch=branch: branch)
        assert (dispatcher.main(), calls, canonical_stage_issue(branch)) == (0, [["make", "stage8-quality"]], None)

def test_scope_collection_covers_exact_layers_and_forbidden_sources(monkeypatch: Any, tmp_path: Path) -> None:
    git(tmp_path, "init", "-b", "main"); git(tmp_path, "config", "user.name", "Scope Test")
    git(tmp_path, "config", "user.email", "scope@example.invalid")
    for path, value in {"rename-source": "rename", "copy-source": "copy", "cached-source": "cached",
                        "unstaged-source": "unstaged", "cancelled": "original"}.items():
        put(tmp_path, f"forbidden/{path}.txt", value)
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "base"); git(tmp_path, "checkout", "-b", "feature")
    git(tmp_path, "mv", "forbidden/rename-source.txt", "rename-destination.txt")
    put(tmp_path, "copy-destination.txt", "copy"); put(tmp_path, "committed.txt", "committed")
    put(tmp_path, "backend/app/main.py", "forbidden first push")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "first push"); first_head = git(tmp_path, "rev-parse", "HEAD")
    put(tmp_path, "docs/STATUS.md", "allowed second push")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "second push"); head = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "checkout", "main"); put(tmp_path, "main-only.txt", "main")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-m", "main"); base = git(tmp_path, "rev-parse", "HEAD")
    git(tmp_path, "update-ref", "refs/remotes/origin/main", base)
    git(tmp_path, "checkout", "feature"); git(tmp_path, "mv", "forbidden/cached-source.txt", "cached-destination.txt")
    (tmp_path / "forbidden/unstaged-source.txt").rename(tmp_path / "unstaged-destination.txt")
    put(tmp_path, "forbidden/cancelled.txt", "staged"); git(tmp_path, "add", "forbidden/cancelled.txt")
    put(tmp_path, "forbidden/cancelled.txt", "original"); put(tmp_path, "untracked\nnewline.txt", "new")
    real_run, calls = stage8.run, []
    def record(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args); return real_run(args)
    monkeypatch.setattr(stage8, "ROOT", tmp_path); monkeypatch.setattr(stage8, "run", record)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push"); monkeypatch.setenv("GITHUB_BASE_SHA", first_head)
    monkeypatch.setenv("GITHUB_HEAD_SHA", head); paths = set(stage8.changed_files_for_stage_scope())
    required = {"forbidden/rename-source.txt", "rename-destination.txt", "forbidden/copy-source.txt",
                "copy-destination.txt", "forbidden/cached-source.txt", "cached-destination.txt",
                "forbidden/unstaged-source.txt", "unstaged-destination.txt", "forbidden/cancelled.txt",
                "backend/app/main.py", "committed.txt", "docs/STATUS.md", "untracked\nnewline.txt"}
    assert required <= paths and "main-only.txt" not in paths
    assert ["git", "merge-base", "origin/main", head] in calls
    assert ["git", "merge-base", first_head, head] not in calls
    monkeypatch.setattr(stage8, "current_branch", lambda: TRANSITION); failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert all(f"Stage 8 changed file outside the allowlist: {path}" in failures for path in required)
    event = tmp_path / "event.json"; event.write_text(json.dumps({"pull_request": {"head": {"sha": first_head}}}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request"); monkeypatch.setenv("GITHUB_BASE_SHA", base)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event)); monkeypatch.delenv("GITHUB_HEAD_SHA")
    with pytest.raises(RuntimeError, match="exact head"): stage8.changed_files_for_stage_scope()

def test_scope_parser_flags_and_command_failures(monkeypatch: Any) -> None:
    assert stage8.parse_name_status_z("R087\0old\0new\0C064\0source\0copy\0") == ["old", "new", "source", "copy"]
    for malformed in ("R100\0old\0", "M\0path", "M\0\0", "Q\0path\0", "R101\0old\0new\0"):
        with pytest.raises(RuntimeError): stage8.parse_name_status_z(malformed)
    bad_bases = ("0" * 39, "0" * 41, "0" * 39 + "1", "invalid-explicit-base")
    layers = ("rev-parse", "merge-base", "committed", "cached", "unstaged", "untracked")
    cases = [(None, "0" * 40), *((layer, "base") for layer in layers)]
    cases += [("explicit-base", base) for base in bad_bases]
    for failed, base in cases:
        calls: list[list[str]] = []
        def fake(args: list[str]) -> subprocess.CompletedProcess[str]:
            calls.append(args)
            layer = ("rev-parse" if "rev-parse" in args else "merge-base" if "merge-base" in args else
                     "untracked" if "ls-files" in args else "cached" if "--cached" in args else
                     "committed" if any(".." in arg for arg in args) else "unstaged")
            output = "head\n" if layer == "rev-parse" else "base\n" if layer == "merge-base" else ""
            explicit_failure = failed == "explicit-base" and args == ["git", "merge-base", base, "head"]
            should_fail = layer == failed or explicit_failure or "0" * 40 in args
            return subprocess.CompletedProcess(args, int(should_fail), output, "failed")
        monkeypatch.setattr(stage8, "run", fake); monkeypatch.setenv("GITHUB_BASE_SHA", base)
        monkeypatch.setenv("GITHUB_HEAD_SHA", "head")
        if failed:
            with pytest.raises(RuntimeError, match="failed"): stage8.changed_files_for_stage_scope()
            if failed == "explicit-base":
                assert [args[2] for args in calls if args[:2] == ["git", "merge-base"]] == [base]
        else:
            assert stage8.changed_files_for_stage_scope() == []
            diffs = [args for args in calls if args[:2] == ["git", "diff"]]; assert len(diffs) == 3
            assert ["git", "merge-base", "origin/main", "head"] in calls
            for args in diffs:
                assert {"--name-status", "-z", "--find-renames", "--find-copies", "--find-copies-harder"} <= set(args)
def test_issue84_guardrail_branch_allows_process_guardrail_files(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: [
            "docs/STATUS.md",
            "scripts/guardrails_check.py",
            "scripts/quality/check_stage8_docs.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_stage8_quality_gate.py",
        ])
    failures: list[str] = []
    stage8.check_stage_marker_and_branch(failures)
    stage8.check_stage_scope(failures)
    assert failures == []
def test_issue84_guardrail_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: stage8.ISSUE84_GUARDRAIL_BRANCH)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: ["backend/app/stage4.py"])

    failures: list[str] = []; stage8.check_stage_scope(failures)
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

    failures: list[str] = []; stage8.check_stage_scope(failures)
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

    failures: list[str] = []; stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/main.py"]
def test_stage8_script_markers_match_mandatory_container_scanners() -> None:
    failures: list[str] = []; stage8.check_dependencies_and_scripts(failures)
    assert not [failure for failure in failures if "docker scout cves" in failure]
    assert not [failure for failure in failures if "--only-severity critical,high" in failure]
def test_non_stage8_non_process_branch_still_rejected(monkeypatch: Any) -> None:
    monkeypatch.setattr(stage8, "current_branch", lambda: "feature/untracked-stage8-work")

    failures: list[str] = []; stage8.check_stage_marker_and_branch(failures)
    assert failures == [
        "Stage 8 work must run on a stage8-* branch or main after merge; got feature/untracked-stage8-work."
    ]
