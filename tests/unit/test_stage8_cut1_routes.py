from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


REPO = Path(__file__).parents[2]
MODULE_PATH = REPO / "scripts/quality/stage8_cut1_routes.py"


def load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routes: Any = load(MODULE_PATH, "stage8_cut1_routes_under_test")
stage8: Any = load(REPO / "scripts/quality/check_stage8_docs.py", "stage8_with_cut1_routes")


EXPECTED = {
    "cut1-process-403-nanoid-3-3-17-security": {
        "docs/governance/preflights/issue-403.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0053-nanoid-3-3-17-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "cut1-process-401-pypdf-6-15-0-security": {
        "docs/governance/preflights/issue-401.json",
        "pyproject.toml",
        "uv.lock",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0052-pypdf-6-15-0-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "cut1-process-396-js-yaml-4-3-1-security": {
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "docs/governance/preflights/issue-396.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "cut1-process-386-modular-route-enforcement": {
        "docs/governance/preflights/issue-386.json",
        "scripts/quality/stage8_cut1_routes.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    "stage8-385-issue280-language-oracle": {
        "docs/governance/preflights/issue-385.json",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    "stage8-384-presenter-asset-route": {
        "docs/governance/preflights/issue-384.json",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-383-presenter-assets": {
        "docs/governance/preflights/issue-383.json",
        "frontend/public/demo/myra-synthetic-presenter.webp",
        "frontend/public/demo/raj-synthetic-presenter.webp",
        "tests/unit/test_cut1_presenter_assets.py",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-397-presenter-asset-adr-classifier": {
        "docs/governance/preflights/issue-397.json",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-393-historical-digest-test-isolation": {
        "docs/governance/preflights/issue-393.json",
        "docs/governance/preflights/issue-396.json",
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
}


def completed(args: list[str], code: int = 0, out: str = "", err: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args, code, out, err)


def test_routes_are_exact_pre_registered_and_issue386_preflight_matches() -> None:
    assert routes.ROUTES == EXPECTED
    assert {branch: stage8.EFFECTIVE_STAGE8_ROUTES[branch] for branch in EXPECTED} == EXPECTED
    artifact = json.loads((REPO / "docs/governance/preflights/issue-386.json").read_text(encoding="utf-8"))
    assert artifact["branch"] == routes.ISSUE386_BRANCH
    assert set(artifact["scope"]["required"]) == EXPECTED[routes.ISSUE386_BRANCH]
    assert set(artifact["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE386_BRANCH]
    assert routes.TEXT_LIMITS[routes.ISSUE386_BRANCH]["tests/unit/test_stage8_quality_gate.py"] == 20
    assert routes.TEXT_LIMITS[routes.ISSUE384_BRANCH]["scripts/quality/check_stage8_docs.py"] == 10
    assert routes.TEXT_LIMITS[routes.ISSUE384_BRANCH]["scripts/quality/stage8_cut1_routes.py"] == 20
    assert routes.TEXT_LIMITS[routes.ISSUE384_BRANCH]["tests/unit/test_stage8_cut1_routes.py"] == 20
    issue393 = json.loads((REPO / "docs/governance/preflights/issue-393.json").read_text(encoding="utf-8"))
    assert issue393["branch"] == routes.ISSUE393_BRANCH and set(issue393["scope"]["required"]) == EXPECTED[routes.ISSUE393_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE393_BRANCH] == 700
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["tests/unit/test_stage8_quality_gate.py"] == 160
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["tests/unit/test_dependency_security_contract.py"] == 80
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["scripts/ci/check_container_scan_consensus.py"] == 80
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["tests/unit/test_container_scan_consensus.py"] == 80
    issue396 = json.loads((REPO / "docs/governance/preflights/issue-396.json").read_text(encoding="utf-8"))
    assert issue396["branch"] == routes.ISSUE396_BRANCH
    assert set(issue396["scope"]["required"]) == EXPECTED[routes.ISSUE396_BRANCH]
    assert set(issue396["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE396_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE396_BRANCH] == 500
    assert routes.TEXT_LIMITS[routes.ISSUE396_BRANCH] == {
        path: 180 if path.endswith("issue-396.json") else 80 if path.startswith("tests/unit/") else 40
        for path in EXPECTED[routes.ISSUE396_BRANCH]
    }
    issue397 = json.loads((REPO / "docs/governance/preflights/issue-397.json").read_text(encoding="utf-8"))
    assert issue397["branch"] == routes.ISSUE397_BRANCH
    assert set(issue397["scope"]["required"]) == EXPECTED[routes.ISSUE397_BRANCH]
    assert set(issue397["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE397_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE397_BRANCH] == 500
    assert routes.TEXT_LIMITS[routes.ISSUE397_BRANCH]["scripts/guardrails_check.py"] == 100
    assert routes.TEXT_LIMITS[routes.ISSUE397_BRANCH]["tests/unit/test_guardrails_check.py"] == 160
    assert routes.TEXT_LIMITS[routes.ISSUE397_BRANCH]["docs/agent-context/context-policy-manifest-v1.json"] == 10
    issue401 = json.loads((REPO / "docs/governance/preflights/issue-401.json").read_text(encoding="utf-8"))
    assert issue401["branch"] == routes.ISSUE401_BRANCH
    assert set(issue401["scope"]["required"]) == EXPECTED[routes.ISSUE401_BRANCH]
    assert set(issue401["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE401_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE401_BRANCH] == 600
    issue403 = json.loads((REPO / "docs/governance/preflights/issue-403.json").read_text(encoding="utf-8"))
    assert issue403["branch"] == routes.ISSUE403_BRANCH
    assert set(issue403["scope"]["required"]) == EXPECTED[routes.ISSUE403_BRANCH]
    assert set(issue403["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE403_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE403_BRANCH] == 500
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    assert "from scripts.quality.check_stage8_docs" not in module_source
    assert "import scripts.quality.check_stage8_docs" not in module_source


def test_legacy_checker_caps_are_unchanged_and_executable() -> None:
    checker = REPO / "scripts/quality/check_stage8_docs.py"
    checker_text = checker.read_text(encoding="utf-8")
    assert len(checker_text.splitlines()) <= 500
    assert checker.stat().st_size <= 32_000
    assert len((REPO / "tests/unit/test_stage8_quality_gate.py").read_text(encoding="utf-8").splitlines()) <= 250
    for relative in (
        "scripts/quality/stage8_brace_expansion_unblock.py",
        "scripts/quality/stage8_cache_pruning.py",
    ):
        assert '"scripts/quality/check_stage8_docs.py": 500' in (REPO / relative).read_text(encoding="utf-8")


def test_exact_route_completeness_lookalikes_and_budgets(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES})
    for branch, paths in EXPECTED.items():
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, set(paths), failures)
        assert failures == []
        missing = sorted(paths)[0]
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, paths - {missing}, failures)
        issue = routes.ROUTE_ISSUES[branch]
        assert failures == [f"Issue #{issue} route is missing required path: {missing}"]
        confusable = (
            branch.replace("stage8", "stageв")
            if "stage8" in branch
            else branch.replace("process", "procesѕ")
        )
        for lookalike in (branch + "-retry", branch.upper(), confusable):
            failures = []
            routes.check_exact_route(REPO, lambda _: completed([]), lookalike, set(paths), failures)
            assert failures == []
            assert lookalike not in stage8.PROCESS_BRANCH_ALLOWED_FILES


def test_per_route_aggregate_per_file_and_binary_caps(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES})
    for branch, limit in routes.TOTAL_LIMITS.items():
        monkeypatch.setattr(routes, "route_text_charges", lambda *_, value=limit: (value + 1, {}))
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
        assert failures == [f"Issue #{routes.ROUTE_ISSUES[branch]} charge {limit + 1} exceeds {limit}."]
    branch = routes.ISSUE383_BRANCH
    path = "tests/unit/test_cut1_presenter_assets.py"
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (1, {path: 261}))
    failures = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == [f"Issue #383 charge for {path} exceeds 260."]
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {
        path: 500001 if "myra" in path else 1 for path in routes.ISSUE383_BINARY_FILES
    })
    failures = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == [
        "Issue #383 binary frontend/public/demo/myra-synthetic-presenter.webp exceeds 500000 bytes."
    ]


def test_dynamic_base_requires_current_origin_main_ancestor() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out="a" * 40 + "\n")

    assert routes.route_base(good, routes.ISSUE385_BRANCH) == "a" * 40
    assert calls == [
        ["git", "rev-parse", "origin/main^{commit}"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]
    outputs = iter((completed([], out="a" * 40 + "\n"), completed([], out="b" * 40 + "\n")))
    assert "current main" in str(pytest.raises(RuntimeError, routes.route_base, lambda _: next(outputs),
                                               routes.ISSUE385_BRANCH).value)
    assert "fixed base" in str(pytest.raises(RuntimeError, routes.route_base,
        lambda args: completed(args, 1, err="failed"), routes.ISSUE386_BRANCH).value)


def test_text_charges_use_additions_deletions_and_larger_complete_snapshot() -> None:
    calls: list[list[str]] = []

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if "ls-files" in args:
            return completed(args)
        return completed(args, out="4\t3\tdocs/file.md\n" if "--cached" in args else "5\t4\tdocs/file.md\n")

    assert routes.route_text_charges(run, "base", {"docs/file.md"}) == (9, {"docs/file.md": 9})
    assert ["git", "diff", "--cached", "--numstat", "--no-renames", "base", "--", "docs/file.md"] in calls
    assert ["git", "diff", "--numstat", "--no-renames", "base", "--", "docs/file.md"] in calls


@pytest.mark.parametrize(
    ("untracked", "diff", "message"),
    [
        (completed([], out="docs/file.md\0"), completed([]), "untracked"),
        (completed([], code=1, err="failed"), completed([]), "failed"),
        (completed([]), completed([], out="-\t1\tdocs/file.md\n"), "malformed or binary"),
        (completed([]), completed([], out="1\t1\tdocs/other.md\n"), "unexpected path"),
    ],
)
def test_text_charges_fail_closed(
    untracked: subprocess.CompletedProcess[str], diff: subprocess.CompletedProcess[str], message: str
) -> None:
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return untracked if "ls-files" in args else diff

    assert message in str(pytest.raises(RuntimeError, routes.route_text_charges,
                                        run, "base", {"docs/file.md"}).value)


def test_issue366_charge_uses_the_complete_fixed_base_snapshot() -> None:
    calls: list[list[str]] = []

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if "merge-base" in args:
            return completed(args, out="base\n")
        return completed(args, out="1\t1\tforeign/path.txt\n")

    assert routes.cut1_transition_charges(run, "base", {"docs/bound.md"}) == (
        2, {"foreign/path.txt": 2}
    )
    assert ["git", "diff", "--cached", "--numstat", "base", "--"] in calls
    assert ["git", "diff", "--numstat", "base", "--"] in calls


def test_binary_sizes_reject_missing_non_regular_empty_and_expose_oversize(tmp_path: Path) -> None:
    path = "frontend/public/demo/myra-synthetic-presenter.webp"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    assert "missing" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
    target.mkdir()
    assert "regular" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
    target.rmdir()
    target.write_bytes(b"")
    assert "empty" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
    target.write_bytes(b"x" * 500001)
    assert routes.route_binary_sizes(tmp_path, {path}) == {path: 500001}
    target.unlink()
    source = tmp_path / "source"
    source.write_bytes(b"x")
    target.symlink_to(source)
    assert "regular" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
