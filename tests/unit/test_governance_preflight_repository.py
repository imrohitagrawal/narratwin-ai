from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from scripts.governance_preflight_repository import validate_governance_preflight_repository


ISSUE = 176
BRANCH = "phase-1-closure-process-176-gpf-v1-repository-integration"
PREFLIGHT = "docs/governance/preflights/issue-176.json"
PATHS = [
    PREFLIGHT,
    "scripts/governance_preflight_repository.py",
    "tests/unit/test_governance_preflight_repository.py",
    "scripts/guardrails_check.py",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
]
FORBIDDEN = [
    "backend/", "frontend/", ".github/workflows/", "docker/",
    "pyproject.toml", "uv.lock", "package.json", "package-lock.json",
]
SEEDS = (32001, 32002, 32003, 32004)


def _git(repo: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, check=check, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
    )
    return completed.stdout.strip()


def _write(repo: Path, relative: str, content: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str, *, empty: bool = False) -> str:
    _git(repo, "add", "-A")
    args = ["commit", "-m", message]
    if empty:
        args.append("--allow-empty")
    _git(repo, *args)
    return _git(repo, "rev-parse", "HEAD")


def _artifact(
    *, issue: int = ISSUE, branch: str = BRANCH,
    required: list[str] | None = None, allowed: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "GovernancePreflightV1",
        "issue_number": issue,
        "branch": branch,
        "objective": "Integrate GovernancePreflightV1 prospectively into offline repository guardrails.",
        "status_decision": "update-minimally",
        "scope": {
            "required": list(required or PATHS),
            "allowed_prefixes": list(allowed or PATHS),
            "forbidden": list(FORBIDDEN),
        },
    }


def _new_repo(tmp_path: Path, name: str = "repo") -> tuple[Path, str]:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@narratwin.local")
    _git(repo, "config", "user.name", "NarraTwin Tests")
    _write(repo, "README.md", "base\n")
    return repo, _commit(repo, "base")


def _valid_repo(
    tmp_path: Path,
    *,
    name: str = "repo",
    branch: str = BRANCH,
    artifact: dict[str, Any] | None = None,
    first_extra: str | None = None,
    preflight_path: str = PREFLIGHT,
    empty_commits: int = 0,
    split_later: bool = False,
) -> tuple[Path, str, str]:
    repo, base = _new_repo(tmp_path, name)
    _git(repo, "checkout", "-q", "-b", branch)
    _write(repo, preflight_path, json.dumps(artifact or _artifact(), indent=2) + "\n")
    if first_extra:
        _write(repo, first_extra, "first\n")
    _commit(repo, "preflight")
    for index in range(empty_commits):
        _commit(repo, f"empty-{index}", empty=True)
    later = [path for path in PATHS if path != PREFLIGHT]
    groups = (later[:4], later[4:]) if split_later else (later,)
    for group_index, group in enumerate(groups):
        for path in group:
            _write(repo, path, f"final {path}\n")
        _commit(repo, f"implementation-{group_index}")
    return repo, base, _git(repo, "rev-parse", "HEAD")


def _codes(repo: Path, base: str, head: str, *, issue: int = ISSUE, branch: str = BRANCH) -> list[str]:
    return [
        finding.code
        for finding in validate_governance_preflight_repository(
            repo, base_sha=base, head_sha=head, issue_number=issue, branch=branch
        )
    ]


def _rewrite_artifact(repo: Path, mutate: Callable[[dict[str, Any]], None]) -> str:
    artifact = json.loads((repo / PREFLIGHT).read_text(encoding="utf-8"))
    mutate(artifact)
    _write(repo, PREFLIGHT, json.dumps(artifact, indent=2) + "\n")
    return _commit(repo, "mutate artifact")


def test_exact_valid_repository_has_no_findings(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("missing", ["GPF.REPO.PREFLIGHT_MISSING"]),
        ("multiple", ["GPF.REPO.PREFLIGHT_MULTIPLE"]),
        ("not-first", ["GPF.REPO.PREFLIGHT_NOT_FIRST"]),
        ("first-extra", ["GPF.REPO.PREFLIGHT_NOT_FIRST"]),
        ("filename", ["GPF.REPO.ISSUE_REF_MISMATCH"]),
    ),
)
def test_each_repository_mutation_returns_complete_vector(
    tmp_path: Path, mutation: str, expected: list[str]
) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    if mutation == "missing":
        _git(repo, "rm", PREFLIGHT)
        head = _commit(repo, "remove preflight")
    elif mutation == "multiple":
        _write(repo, "docs/governance/preflights/issue-999.json", "{}\n")
        head = _commit(repo, "second preflight")
    elif mutation == "not-first":
        first = _git(repo, "rev-list", "--reverse", f"{base}..{head}").splitlines()[0]
        _git(repo, "filter-branch", "-f", "--tree-filter", f"rm -f {PREFLIGHT}", f"{first}^..{first}")
        head = _git(repo, "rev-parse", "HEAD")
    elif mutation == "first-extra":
        repo, base, head = _valid_repo(tmp_path, name="mutated", first_extra="extra.txt")
    else:
        wrong = "docs/governance/preflights/issue-177.json"
        _git(repo, "mv", PREFLIGHT, wrong)
        head = _commit(repo, "rename preflight")
    assert _codes(repo, base, head) == expected


@pytest.mark.parametrize("bad", ("0" * 40, "not-a-sha", "-" + "a" * 39))
@pytest.mark.parametrize("which", ("base", "head"))
def test_unavailable_or_injectable_history_fails_closed(
    tmp_path: Path, bad: str, which: str
) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    if which == "base":
        base = bad
    else:
        head = bad
    assert _codes(repo, base, head) == ["GPF.REPO.HISTORY_UNAVAILABLE"]


def test_non_ancestor_history_is_unavailable(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    _git(repo, "checkout", "-q", "--orphan", "unrelated")
    _git(repo, "rm", "-rf", ".")
    _write(repo, "other.txt", "other\n")
    unrelated = _commit(repo, "unrelated")
    assert _codes(repo, unrelated, head) == ["GPF.REPO.HISTORY_UNAVAILABLE"]


@pytest.mark.parametrize(
    ("name", "mutate", "expected"),
    (
        ("body-issue", lambda a: a.__setitem__("issue_number", 177), ["GPF.BINDING.ISSUE_MISMATCH"]),
        ("body-branch", lambda a: a.__setitem__("branch", BRANCH + "-wrong"), ["GPF.BINDING.BRANCH_MISMATCH"]),
        ("status", lambda a: a.__setitem__("status_decision", "skip"), ["GPF.STATUS.DECISION_INVALID"]),
        ("unknown", lambda a: a.__setitem__("unknown", True), ["GPF.SCHEMA.UNKNOWN"]),
        ("duplicate", lambda a: a["scope"]["required"].append(PATHS[0]), ["GPF.SCHEMA.DUPLICATE"]),
        ("traversal", lambda a: a["scope"]["required"].__setitem__(1, "../escape"), ["GPF.PATH.INVALID"]),
        ("control", lambda a: a["scope"]["required"].__setitem__(1, "bad\npath"), ["GPF.PATH.INVALID"]),
        ("required-missing", lambda a: a["scope"]["required"].append("missing.txt"), ["GPF.SCOPE.REQUIRED_NOT_CHANGED"]),
        ("required-forbidden", lambda a: a["scope"]["forbidden"].append(PATHS[1]), ["GPF.SCOPE.REQUIRED_FORBIDDEN"]),
        ("required-not-allowed", lambda a: a["scope"]["allowed_prefixes"].remove(PATHS[1]), ["GPF.SCOPE.REQUIRED_NOT_ALLOWED"]),
    ),
)
def test_pr_a_findings_pass_through_unchanged(
    tmp_path: Path, name: str, mutate: Callable[[dict[str, Any]], None], expected: list[str]
) -> None:
    del name
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    head = _rewrite_artifact(repo, mutate)
    assert _codes(repo, base, head) == expected


def test_malformed_and_oversized_artifacts_use_pr_a_codes(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    _write(repo, PREFLIGHT, "{not-json\n")
    head = _commit(repo, "malformed")
    assert _codes(repo, base, head) == ["GPF.SCHEMA.TYPE"]
    _write(repo, PREFLIGHT, "x" * 65_537)
    head = _commit(repo, "oversized")
    assert _codes(repo, base, head) == ["GPF.SCHEMA.LIMIT"]


def test_order_and_later_commit_grouping_do_not_change_validity(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path, name="grouped")
    assert _codes(repo, base, head) == []
    artifact = _artifact()
    artifact = json.loads(json.dumps(artifact, sort_keys=True))
    for value in artifact["scope"].values():
        value.reverse()
    other, other_base, other_head = _valid_repo(
        tmp_path, name="split", artifact=artifact, split_later=True
    )
    assert _codes(other, other_base, other_head) == []


def test_commit_limits_and_maximum_valid_performance(tmp_path: Path) -> None:
    constructed = time.perf_counter()
    repo, base, head = _valid_repo(tmp_path, empty_commits=998)
    construction_seconds = time.perf_counter() - constructed
    started = time.perf_counter()
    assert _codes(repo, base, head) == []
    validation_seconds = time.perf_counter() - started
    assert len(_git(repo, "rev-list", f"{base}..{head}").splitlines()) == 1_000
    assert validation_seconds < 5.0, (construction_seconds, validation_seconds)
    _commit(repo, "limit", empty=True)
    assert _codes(repo, base, _git(repo, "rev-parse", "HEAD")) == ["GPF.REPO.LIMIT_EXCEEDED"]


@pytest.mark.parametrize(("count", "expected"), ((2_000, []), (2_001, ["GPF.REPO.LIMIT_EXCEEDED"])))
def test_changed_path_limit_is_isolated(tmp_path: Path, count: int, expected: list[str]) -> None:
    required = [PREFLIGHT, "docs/STATUS.md"]
    artifact = _artifact(required=required, allowed=required + ["generated/"])
    repo, base = _new_repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", BRANCH)
    _write(repo, PREFLIGHT, json.dumps(artifact))
    _commit(repo, "preflight")
    _write(repo, "docs/STATUS.md", "status\n")
    for index in range(count - 2):
        _write(repo, f"generated/{index:04d}.txt", "x")
    head = _commit(repo, "paths")
    assert len(_git(repo, "diff", "--name-only", base, head).splitlines()) == count
    assert _codes(repo, base, head) == expected


def test_prospective_cutover_preserves_legacy_and_unrelated_branches(tmp_path: Path) -> None:
    repo, base = _new_repo(tmp_path)
    for branch in (
        "feature/unrelated", "stage4-product", "phase-1-closure-process-169-retained-evidence"
    ):
        assert _codes(repo, "invalid", "invalid", issue=999, branch=branch) == []
    assert _codes(
        repo, base, base, issue=999, branch="phase-1-closure-process-999-later"
    ) == []


def test_exactly_40_seeded_histories_report_reproducible_diagnostics(tmp_path: Path) -> None:
    results: list[bool] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for case_index in range(10):
            valid = case_index < 5
            name = f"seed-{seed}-{case_index}"
            repo, base, head = _valid_repo(tmp_path, name=name, split_later=bool(rng.getrandbits(1)))
            mutation = "none" if valid else ("missing" if case_index % 2 else "body-issue")
            expected: list[str] = []
            if mutation == "missing":
                _git(repo, "rm", PREFLIGHT)
                head = _commit(repo, "single fault")
                expected = ["GPF.REPO.PREFLIGHT_MISSING"]
            elif mutation == "body-issue":
                head = _rewrite_artifact(repo, lambda value: value.__setitem__("issue_number", 177))
                expected = ["GPF.BINDING.ISSUE_MISMATCH"]
            actual = _codes(repo, base, head)
            assert actual == expected, (
                f"seed={seed} case={case_index} mutation={mutation} base={base} head={head} "
                f"expected={expected} actual={actual} "
                f"paths={_git(repo, 'diff', '--name-only', base, head).splitlines()}"
            )
            results.append(valid)
    assert len(results) == 40
    assert results.count(True) == results.count(False) == 20


def test_real_guardrail_subprocess_is_offline_and_sanitized(tmp_path: Path) -> None:
    source = Path(__file__).parents[2]
    repo = tmp_path / "full-repository"
    shutil.copytree(source, repo, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache"))
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@narratwin.local")
    _git(repo, "config", "user.name", "NarraTwin Tests")
    saved = {path: (repo / path).read_bytes() for path in PATHS}
    for path in PATHS:
        target = repo / path
        if target.exists():
            target.unlink()
    for path in PATHS[3:]:
        original = subprocess.run(
            ["git", "show", f"origin/main:{path}"], cwd=source, check=True,
            stdout=subprocess.PIPE, timeout=10,
        ).stdout
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original)
    base = _commit(repo, "base")
    _git(repo, "checkout", "-q", "-b", BRANCH)
    (repo / PREFLIGHT).parent.mkdir(parents=True, exist_ok=True)
    (repo / PREFLIGHT).write_bytes(saved[PREFLIGHT])
    _commit(repo, "preflight")
    for path in PATHS[1:]:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(saved[path])
    head = _commit(repo, "implementation")
    blocker = tmp_path / "network-blocker"
    blocker.mkdir()
    _write(blocker, "sitecustomize.py", "import socket\ndef denied(*a, **k): raise AssertionError('NETWORK_ATTEMPT')\nsocket.socket = denied\n")
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(blocker),
        "PYTHONDONTWRITEBYTECODE": "1", "GITHUB_BASE_SHA": base,
        "GITHUB_HEAD_SHA": head, "GITHUB_HEAD_REF": BRANCH,
        "NARRATWIN_TEST_PARENT_TOKEN": "must-not-appear",
    }
    completed = subprocess.run(
        [sys.executable, "scripts/guardrails_check.py"], cwd=repo, env=env,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=20,
    )
    assert completed.returncode == 0
    assert completed.stdout == "All NarraTwin AI repository guardrails passed.\n"
    assert completed.stderr == ""
    assert "must-not-appear" not in completed.stdout + completed.stderr
    assert "NETWORK_ATTEMPT" not in completed.stdout + completed.stderr
