from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.quality import stage8_a23b as a23b
from scripts.quality import stage8_cache_pruning as pruning
from scripts.quality import check_stage8_docs as stage8


def put(root: Path, relative: str, value: str = "pass\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return path


def test_repository_python_files_prunes_ignored_roots_before_descent(tmp_path: Path) -> None:
    owned = put(tmp_path, "src/owned.py")
    ignored = {
        ".git", ".venv", ".uv-cache", ".mypy_cache", ".pytest_cache",
        ".ruff_cache", "__pycache__", "node_modules", "outputs", "reports", ".codex",
    }
    for directory in ignored:
        put(tmp_path, f"{directory}/poison.py", "not valid python !!!")
        put(tmp_path, f"nested/{directory}/poison.py", "not valid python !!!")
    assert list(pruning.repository_python_files(tmp_path)) == [owned]


def test_repository_python_files_scans_similar_repository_owned_names(tmp_path: Path) -> None:
    expected = {
        put(tmp_path, "src/node_modules_adapter.py"),
        put(tmp_path, "src/.uv-cache-policy/owned.py"),
        put(tmp_path, "reports_owned/check.py"),
    }
    assert set(pruning.repository_python_files(tmp_path)) == expected


def test_repository_python_files_does_not_follow_symlink_escape_or_cycle(tmp_path: Path) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-external"
    put(external, "poison.py", "not valid python !!!")
    (tmp_path / "escape").symlink_to(external, target_is_directory=True)
    (tmp_path / "cycle").mkdir()
    (tmp_path / "cycle/back").symlink_to(tmp_path, target_is_directory=True)
    linked_file = tmp_path / "linked.py"
    linked_file.symlink_to(external / "poison.py")
    owned = put(tmp_path, "owned.py")
    assert list(pruning.repository_python_files(tmp_path)) == [owned]


def test_a23b_semantic_scan_uses_pruned_repository_file_iterator(
    monkeypatch: Any, tmp_path: Path
) -> None:
    owned = put(tmp_path, "backend/owned.py")
    put(tmp_path, ".uv-cache/archive/poison.py", "not valid python !!!")
    visited: list[Path] = []
    monkeypatch.setattr(a23b, "semantic_legacy_failures", lambda path: visited.append(path) or [])
    a23b.check_a23b(tmp_path, lambda _args: None, [], exact_route=False)
    assert visited == [owned]


def preflight() -> dict[str, Any]:
    return json.loads(
        (Path(__file__).parents[2] / "docs/governance/preflights/issue-375.json").read_text(encoding="utf-8")
    )


def test_preflight_and_route_are_exact_and_fail_closed() -> None:
    data = preflight()
    failures: list[str] = []
    pruning.validate_preflight(data, failures)
    assert failures == []
    assert pruning.CACHE_PRUNING_ROUTES == {pruning.BRANCH: pruning.ALLOWED_FILES}
    assert stage8.PROCESS_BRANCH_ALLOWED_FILES[pruning.BRANCH] == pruning.ALLOWED_FILES
    mutations = (
        ("branch", pruning.BRANCH + "-copy"),
        ("issue_number", 374),
        ("schema_version", "GovernancePreflightV0"),
    )
    for field, value in mutations:
        changed = json.loads(json.dumps(data)); changed[field] = value; failures = []
        pruning.validate_preflight(changed, failures)
        assert failures
    for key in ("required", "allowed_prefixes"):
        changed = json.loads(json.dumps(data)); changed["scope"][key].pop(); failures = []
        pruning.validate_preflight(changed, failures)
        assert failures


def test_exact_route_rejects_malformed_git_evidence(monkeypatch: Any, tmp_path: Path) -> None:
    put(tmp_path, "docs/governance/preflights/issue-375.json", json.dumps(preflight()))
    responses = {
        "rev-parse": subprocess.CompletedProcess([], 0, "not-a-sha\n", ""),
        "merge-base": subprocess.CompletedProcess([], 1, "", "failed"),
    }
    monkeypatch.setattr(pruning, "_check_budget", lambda *_args: None)
    pruning.check_exact_route(
        tmp_path,
        lambda args: responses["merge-base" if "merge-base" in args else "rev-parse"],
        failures := [],
        active=True,
    )
    assert any("Git evidence failed closed" in failure for failure in failures)
    assert any("exact authorized base" in failure for failure in failures)


def test_context_budgets_are_executable() -> None:
    root = Path(__file__).parents[2]
    budgets = {
        "scripts/quality/check_stage8_docs.py": 500,
        "scripts/quality/stage8_cache_pruning.py": 140,
        "tests/unit/test_stage8_cache_pruning.py": 180,
    }
    for relative, limit in budgets.items():
        lines = (root / relative).read_text(encoding="utf-8").splitlines()
        assert len(lines) <= limit
        if relative != "scripts/quality/check_stage8_docs.py":
            assert max(map(len, lines)) <= 120


@pytest.mark.parametrize("active", [False, True])
def test_exact_route_is_inert_off_branch_and_requires_preflight_on_branch(
    tmp_path: Path, active: bool
) -> None:
    failures: list[str] = []
    pruning.check_exact_route(tmp_path, lambda _args: None, failures, active=active)
    assert bool(failures) is active
