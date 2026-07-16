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

import scripts.governance_preflight_repository as repository_adapter
from scripts.governance_preflight_repository import validate_governance_preflight_repository


ISSUE = 176
BRANCH = "phase-1-closure-process-176-gpf-v1-repository-integration"
PREFLIGHT = "docs/governance/preflights/issue-176.json"
FROZEN = json.loads(Path(PREFLIGHT).read_text(encoding="utf-8"))
PATHS, FORBIDDEN = FROZEN["scope"]["required"], FROZEN["scope"]["forbidden"]
SEEDS = (32001, 32002, 32003, 32004)


def _git(repo: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(["git", *args], cwd=repo, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
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


def _artifact(*, issue: int = ISSUE, branch: str = BRANCH, required: list[str] | None = None, allowed: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "GovernancePreflightV1",
        "issue_number": issue,
        "branch": branch,
        "objective": "Integrate GovernancePreflightV1 prospectively into offline repository guardrails.",
        "status_decision": "update-minimally",
        "scope": {"required": list(required or PATHS), "allowed_prefixes": list(allowed or PATHS), "forbidden": list(FORBIDDEN)}}


def _new_repo(tmp_path: Path, name: str = "repo") -> tuple[Path, str]:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@narratwin.local")
    _git(repo, "config", "user.name", "NarraTwin Tests")
    _write(repo, "README.md", "base\n")
    return repo, _commit(repo, "base")


def _valid_repo(tmp_path: Path, *, name: str = "repo", branch: str = BRANCH, artifact: dict[str, Any] | None = None, first_extra: str | None = None, preflight_path: str = PREFLIGHT, empty_commits: int = 0, split_later: bool = False) -> tuple[Path, str, str]:
    repo, base = _new_repo(tmp_path, name)
    _git(repo, "checkout", "-q", "-b", branch)
    value = artifact or _artifact()
    _write(repo, preflight_path, json.dumps(value, indent=2) + "\n")
    if first_extra:
        _write(repo, first_extra, "first\n")
    _commit(repo, "preflight")
    for index in range(empty_commits):
        _commit(repo, f"empty-{index}", empty=True)
    later = [path for path in value["scope"]["required"] if path != preflight_path]
    groups = (later[:4], later[4:]) if split_later else (later,)
    for group_index, group in enumerate(groups):
        for path in group:
            _write(repo, path, f"final {path}\n")
        _commit(repo, f"implementation-{group_index}")
    return repo, base, _git(repo, "rev-parse", "HEAD")


def _codes(repo: Path, base: str, head: str, *, issue: int = ISSUE, branch: str = BRANCH) -> list[str]:
    return [finding.code for finding in validate_governance_preflight_repository(
        repo, base_sha=base, head_sha=head, issue_number=issue, branch=branch)]


def _rewrite_artifact(repo: Path, mutate: Callable[[dict[str, Any]], None]) -> str:
    artifact = json.loads((repo / PREFLIGHT).read_text(encoding="utf-8"))
    mutate(artifact)
    _write(repo, PREFLIGHT, json.dumps(artifact, indent=2) + "\n")
    return _commit(repo, "mutate artifact")


def test_exact_valid_repository_has_no_findings(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path)
    before = (_git(repo, "rev-parse", "HEAD"), _git(repo, "status", "--porcelain"))
    assert _codes(repo, base, head) == []
    assert (_git(repo, "rev-parse", "HEAD"), _git(repo, "status", "--porcelain")) == before


@pytest.mark.parametrize(("mutation", "expected"), (
        ("missing", ["GPF.REPO.PREFLIGHT_MISSING"]),
        ("multiple", ["GPF.REPO.PREFLIGHT_MULTIPLE"]),
        ("not-first", ["GPF.REPO.PREFLIGHT_NOT_FIRST"]),
        ("first-extra", ["GPF.REPO.PREFLIGHT_NOT_FIRST"]),
        ("filename", ["GPF.REPO.ISSUE_REF_MISMATCH"]),
        ("filename-body", ["GPF.REPO.ISSUE_REF_MISMATCH", "GPF.BINDING.ISSUE_MISMATCH"]),
        ("required-missing", ["GPF.SCOPE.REQUIRED_NOT_CHANGED"]),
        ("deleted-base", ["GPF.REPO.PREFLIGHT_MISSING"]),
    ))
def test_each_repository_mutation_returns_complete_vector(tmp_path: Path, mutation: str, expected: list[str]) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    if mutation == "missing":
        _git(repo, "rm", PREFLIGHT)
        head = _commit(repo, "remove preflight")
    elif mutation == "multiple":
        _write(repo, "docs/governance/preflights/issue-999.json", "{}\n")
        head = _commit(repo, "second preflight")
    elif mutation == "not-first":
        repo, base = _new_repo(tmp_path, "mutated")
        _git(repo, "checkout", "-q", "-b", BRANCH)
        _write(repo, PATHS[1], "first\n")
        _commit(repo, "implementation first")
        _write(repo, PREFLIGHT, json.dumps(_artifact()))
        for path in PATHS[2:]:
            _write(repo, path, "later\n")
        head = _commit(repo, "preflight later")
    elif mutation == "first-extra":
        repo, base, head = _valid_repo(tmp_path, name="mutated", first_extra=PATHS[1])
    elif mutation == "required-missing":
        _git(repo, "rm", PATHS[1])
        head = _commit(repo, "remove required path")
    elif mutation == "deleted-base":
        required = [PREFLIGHT, "docs/STATUS.md"]
        repo, _ = _new_repo(tmp_path, "mutated")
        _write(repo, PREFLIGHT, "old\n")
        base = _commit(repo, "base preflight")
        _git(repo, "checkout", "-q", "-b", BRANCH)
        _write(repo, PREFLIGHT, json.dumps(_artifact(required=required, allowed=required)))
        _commit(repo, "preflight")
        _write(repo, "docs/STATUS.md", "status\n")
        head = _commit(repo, "implementation")
        assert _codes(repo, base, head) == []
        _git(repo, "rm", PREFLIGHT)
        head = _commit(repo, "single deletion fault")
    else:
        wrong = "docs/governance/preflights/issue-177.json"
        wrong_paths = [wrong, *PATHS[1:]]
        artifact = _artifact(issue=177 if mutation == "filename-body" else ISSUE,
                             required=wrong_paths, allowed=wrong_paths)
        repo, base, head = _valid_repo(tmp_path, name="mutated", artifact=artifact,
                                      preflight_path=wrong)
    assert _codes(repo, base, head) == expected


@pytest.mark.parametrize("bad", ("0" * 40, "not-a-sha", "-" + "a" * 39))
@pytest.mark.parametrize("which", ("base", "head"))
def test_unavailable_or_injectable_history_fails_closed(tmp_path: Path, bad: str, which: str) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    if which == "base":
        base = bad
    else:
        head = bad
    assert _codes(repo, base, head) == ["GPF.REPO.HISTORY_UNAVAILABLE"]


def test_non_ancestor_history_is_unavailable(tmp_path: Path, monkeypatch: Any) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    _git(repo, "rm", PREFLIGHT)
    head = _commit(repo, "lower-priority missing preflight")
    assert _codes(repo, base, head) == ["GPF.REPO.PREFLIGHT_MISSING"]
    _git(repo, "checkout", "-q", "--orphan", "unrelated")
    _git(repo, "rm", "-rf", ".")
    _write(repo, "other.txt", "other\n")
    unrelated = _commit(repo, "unrelated")
    assert _codes(repo, unrelated, head) == ["GPF.REPO.HISTORY_UNAVAILABLE"]
    monkeypatch.setattr(repository_adapter, "_GIT", "/missing/git")
    assert _codes(repo, unrelated, head) == ["GPF.REPO.HISTORY_UNAVAILABLE"]


@pytest.mark.parametrize(("name", "mutate", "expected"), (
        ("body-issue", lambda a: a.__setitem__("issue_number", 177), ["GPF.BINDING.ISSUE_MISMATCH"]),
        ("body-branch", lambda a: a.__setitem__("branch", BRANCH + "-wrong"), ["GPF.BINDING.BRANCH_MISMATCH"]),
        ("status", lambda a: a.__setitem__("status_decision", "skip"), ["GPF.STATUS.DECISION_INVALID"]),
        ("unknown", lambda a: a.__setitem__("unknown", True), ["GPF.SCHEMA.UNKNOWN"]),
        ("duplicate", lambda a: a["scope"]["required"].append(PATHS[0]), ["GPF.SCHEMA.DUPLICATE"]),
        ("traversal", lambda a: a["scope"]["required"].__setitem__(1, "../escape"), ["GPF.PATH.INVALID"]),
        ("control", lambda a: a["scope"]["required"].__setitem__(1, "bad\npath"), ["GPF.PATH.INVALID"]),
        ("required-forbidden", lambda a: a["scope"]["forbidden"].append(PATHS[1]), ["GPF.SCOPE.REQUIRED_FORBIDDEN"]),
        ("required-not-allowed", lambda a: a["scope"]["allowed_prefixes"].remove(PATHS[1]), ["GPF.SCOPE.REQUIRED_NOT_ALLOWED"]),
        ("required-objective", lambda a: a.pop("objective"), ["GPF.SCHEMA.REQUIRED"]),
        ("blank-objective", lambda a: a.__setitem__("objective", " "), ["GPF.SCHEMA.BLANK"]),
        ("version", lambda a: a.__setitem__("schema_version", "GovernancePreflightV2"), ["GPF.SCHEMA.VERSION"]),
        ("issue-type", lambda a: a.__setitem__("issue_number", "176"), ["GPF.SCHEMA.TYPE"]),
        ("objective-limit", lambda a: a.__setitem__("objective", "x" * 2_001), ["GPF.SCHEMA.LIMIT"]),
        ("scope-required", lambda a: a["scope"].pop("forbidden"), ["GPF.SCHEMA.REQUIRED"]),
        ("scope-unknown", lambda a: a["scope"].__setitem__("extra", []), ["GPF.SCHEMA.UNKNOWN"]),
        ("absolute", lambda a: a["scope"]["required"].__setitem__(1, "/escape"), ["GPF.PATH.INVALID"]),
        ("dot", lambda a: a["scope"]["required"].__setitem__(1, "scripts/./x.py"), ["GPF.PATH.INVALID"]),
        ("status-required", lambda a: a["scope"]["required"].remove("docs/STATUS.md"), ["GPF.STATUS.REQUIRED_MISSING"]),
        ("status-allowed", lambda a: a["scope"]["allowed_prefixes"].remove("docs/STATUS.md"), ["GPF.STATUS.ALLOWED_MISSING"]),
        ("list-limit", lambda a: a["scope"]["allowed_prefixes"].extend(f"u/{i}/" for i in range(119)), ["GPF.SCHEMA.LIMIT"]),
        ("path-limit", lambda a: a["scope"]["required"].__setitem__(1, "x" * 513), ["GPF.SCHEMA.LIMIT"]),
        ("serialized-limit", lambda a: (a["scope"]["allowed_prefixes"].extend(f"u/{i:03d}/{'x' * 500}" for i in range(118)), a["scope"]["forbidden"].extend(f"f/{i:03d}/{'x' * 500}" for i in range(120))), ["GPF.SCHEMA.LIMIT"]),
        ("surrogate", lambda a: a.__setitem__("objective", "\ud800"), ["GPF.SCHEMA.TYPE"]),
        ("surrogate-path", lambda a: a["scope"]["required"].__setitem__(1, "scripts/\ud800.py"), ["GPF.PATH.INVALID"]),
    ))
def test_pr_a_findings_pass_through_unchanged(tmp_path: Path, name: str, mutate: Callable[[dict[str, Any]], None], expected: list[str]) -> None:
    del name
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    head = _rewrite_artifact(repo, mutate)
    assert _codes(repo, base, head) == expected


@pytest.mark.parametrize(("raw", "expected"), (
    ("{not-json\n", ["GPF.SCHEMA.TYPE"]), ("[]\n", ["GPF.SCHEMA.TYPE"]),
    ("x" * 65_537, ["GPF.SCHEMA.LIMIT"])))
def test_raw_artifacts_use_pr_a_codes(tmp_path: Path, raw: str, expected: list[str]) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    _write(repo, PREFLIGHT, raw)
    head = _commit(repo, "raw artifact")
    assert _codes(repo, base, head) == expected


@pytest.mark.parametrize(("path", "expected"), (
    (["backend/forbidden.py"], ["GPF.SCOPE.CHANGE_FORBIDDEN"]),
    (["tools/unapproved.py"], ["GPF.SCOPE.CHANGE_NOT_ALLOWED"]),
    (["backend/forbidden.py", "tools/unapproved.py"],
     ["GPF.SCOPE.CHANGE_FORBIDDEN", "GPF.SCOPE.CHANGE_NOT_ALLOWED"])))
def test_changed_path_findings_pass_through(tmp_path: Path, path: list[str], expected: list[str]) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    for changed in path:
        _write(repo, changed, "declared fault\n")
    head = _commit(repo, "changed path fault")
    assert _codes(repo, base, head) == expected


def test_order_and_later_commit_grouping_do_not_change_validity(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path, name="grouped")
    assert _codes(repo, base, head) == []
    required = PATHS + [f"nested/{index:03d}/file.txt" for index in range(117)]
    required.append(f"scripts/{'x' * 250}/{'y' * 250}.py")
    artifact = _artifact(required=required, allowed=required)
    artifact["objective"] = "界" * 2_000
    artifact["scope"]["forbidden"].extend(f"forbidden/{index:03d}/" for index in range(120))
    assert all(len(artifact["scope"][key]) == 128 for key in ("required", "allowed_prefixes", "forbidden"))
    assert len(required[-1]) == 512
    artifact = json.loads(json.dumps(artifact, sort_keys=True))
    for value in artifact["scope"].values():
        value.reverse()
    other, other_base, other_head = _valid_repo(
        tmp_path, name="split", artifact=artifact, split_later=True)
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
    print(f"maximum_fixture_construction_seconds={construction_seconds:.3f} maximum_validation_seconds={validation_seconds:.3f}")
    _commit(repo, "isolated limit", empty=True)
    assert _codes(repo, base, _git(repo, "rev-parse", "HEAD")) == ["GPF.REPO.LIMIT_EXCEEDED"]
    _write(repo, "docs/governance/preflights/issue-999.json", "{}\n")
    head = _commit(repo, "lower-priority multiple")
    assert _codes(repo, base, head) == ["GPF.REPO.LIMIT_EXCEEDED"]


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
    if count == 2_000:
        source = "generated/0000.txt"
        for target, fault in (("backend/fault.txt", "GPF.SCOPE.CHANGE_FORBIDDEN"),
                              ("tools/fault.txt", "GPF.SCOPE.CHANGE_NOT_ALLOWED"),
                              ("bad\npath.txt", "GPF.PATH.INVALID")):
            (repo / target).parent.mkdir(parents=True, exist_ok=True)
            _git(repo, "mv", source, target)
            head = _commit(repo, "large-diff fault")
            assert _codes(repo, base, head) == [fault]
            _git(repo, "mv", target, source)
            head = _commit(repo, "restore valid large diff")
            assert _codes(repo, base, head) == []
        head = _rewrite_artifact(repo, lambda value: value.__setitem__("objective", "x" * 2_001))
        assert _codes(repo, base, head) == ["GPF.SCHEMA.LIMIT"]


@pytest.mark.parametrize(("path", "expected"), (
    ("unicode/界.txt", []), ("bad\ncontrol.txt", ["GPF.PATH.INVALID"])))
def test_git_path_decoding_is_exact(tmp_path: Path, path: str, expected: list[str]) -> None:
    artifact = _artifact(allowed=PATHS + ["unicode/"])
    repo, base, head = _valid_repo(tmp_path, artifact=artifact)
    assert _codes(repo, base, head) == []
    _write(repo, path, "single Git path mutation\n")
    head = _commit(repo, "path mutation")
    assert _codes(repo, base, head) == expected


def test_prospective_cutover_preserves_legacy_and_unrelated_branches(tmp_path: Path) -> None:
    repo, base = _new_repo(tmp_path)
    for branch in ("feature/unrelated", "stage4-product", "phase-1-closure-process-169-retained-evidence"):
        assert _codes(repo, "invalid", "invalid", issue=999, branch=branch) == []
    assert _codes(repo, base, base, issue=999, branch="phase-1-closure-process-999-later") == []


def test_later_branch_activates_only_when_adapter_is_in_base_tree(tmp_path: Path) -> None:
    branch = "phase-1-closure-process-999-later"
    preflight = "docs/governance/preflights/issue-999.json"
    repo, _ = _new_repo(tmp_path)
    _write(repo, "scripts/governance_preflight_repository.py", "merged adapter\n")
    base = _commit(repo, "adapter merged")
    _git(repo, "checkout", "-q", "-b", branch)
    artifact = _artifact(issue=999, branch=branch, required=[preflight, "docs/STATUS.md"], allowed=[preflight, "docs/STATUS.md"])
    _write(repo, preflight, json.dumps(artifact))
    _commit(repo, "preflight")
    _write(repo, "docs/STATUS.md", "later\n")
    head = _commit(repo, "implementation")
    assert _codes(repo, base, head, issue=999, branch=branch) == []
    _git(repo, "rm", preflight)
    head = _commit(repo, "single missing fault")
    assert _codes(repo, base, head, issue=999, branch=branch) == ["GPF.REPO.PREFLIGHT_MISSING"]
    one, one_base = _new_repo(tmp_path, "one-commit")
    _git(one, "checkout", "-q", "-b", BRANCH)
    _write(one, PREFLIGHT, json.dumps(_artifact()))
    one_head = _commit(one, "preflight only")
    assert _codes(one, one_base, one_head) == ["GPF.SCOPE.REQUIRED_NOT_CHANGED"]


def test_exactly_40_seeded_histories_report_reproducible_diagnostics(tmp_path: Path) -> None:
    results: list[bool] = []
    validation_times: list[float] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for case_index in range(10):
            valid = case_index < 5
            name = f"seed-{seed}-{case_index}"
            repo, base, head = _valid_repo(tmp_path, name=name, split_later=bool(rng.getrandbits(1)))
            mutation = "none" if valid else ("missing" if case_index % 2 else "body-issue")
            expected = [] if valid else (["GPF.REPO.PREFLIGHT_MISSING"] if mutation == "missing" else ["GPF.BINDING.ISSUE_MISMATCH"])
            paths = _git(repo, "diff", "--name-only", base, head).splitlines()
            baseline = _codes(repo, base, head)
            detail = f"seed={seed} case={case_index} mutation={mutation} base={base} head={head} expected={expected} actual={baseline} paths={paths}"
            assert baseline == [], detail
            if mutation == "missing":
                _git(repo, "rm", PREFLIGHT)
                head = _commit(repo, "single fault")
            elif mutation == "body-issue":
                head = _rewrite_artifact(repo, lambda value: value.__setitem__("issue_number", 177))
            started = time.perf_counter()
            actual = _codes(repo, base, head)
            validation_times.append(time.perf_counter() - started)
            paths = _git(repo, "diff", "--name-only", base, head).splitlines()
            assert actual == expected, f"seed={seed} case={case_index} mutation={mutation} base={base} head={head} expected={expected} actual={actual} paths={paths}"
            results.append(valid)
    assert len(results) == 40 and results.count(True) == results.count(False) == 20
    print(f"generated_history_validation_p95_seconds={sorted(validation_times)[37]:.4f}")


@pytest.mark.parametrize(("mode", "returncode", "stdout"), (
    ("valid", 0, "All NarraTwin AI repository guardrails passed.\n"),
    ("missing", 1, "Guardrail failures:\n- Governance preflight finding: GPF.REPO.PREFLIGHT_MISSING\n"),
    ("invalid", 1, "Guardrail failures:\n- Governance preflight finding: GPF.SCHEMA.TYPE\n"),
    ("unrelated", 1, "Guardrail failures:\n- Evaluation failures found in reports/eval-results.json. Eval failures block merge.\n")))
def test_real_guardrail_subprocess_is_offline_and_sanitized(tmp_path: Path, mode: str, returncode: int, stdout: str) -> None:
    source = Path(__file__).parents[2]
    repo = tmp_path / f"full-repository-{mode}"
    shutil.copytree(source, repo, ignore=shutil.ignore_patterns(
        ".git", ".venv", ".uv-cache", ".mypy_cache", ".codex", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules", "outputs", "reports"))
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@narratwin.local")
    _git(repo, "config", "user.name", "NarraTwin Tests")
    saved = {path: (repo / path).read_bytes() for path in PATHS}
    for path in PATHS:
        target = repo / path
        if target.exists():
            target.unlink()
    for path in PATHS[1:]:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"synthetic historical baseline for issue 176 fixture: {path}\n", encoding="utf-8")
    if mode == "unrelated":
        _write(repo, "reports/eval-results.json", '{"status":"failed"}\n')
    base = _commit(repo, "base")
    _git(repo, "update-ref", "refs/remotes/origin/main", base)
    _git(repo, "checkout", "-q", "-b", BRANCH)
    (repo / PREFLIGHT).parent.mkdir(parents=True, exist_ok=True)
    if mode != "missing":
        (repo / PREFLIGHT).write_bytes(b"{not-json\n" if mode == "invalid" else saved[PREFLIGHT])
    _commit(repo, "preflight", empty=mode == "missing")
    for path in PATHS[1:]:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(saved[path])
    head = _commit(repo, "implementation")
    blocker = tmp_path / "network-blocker"
    blocker.mkdir(exist_ok=True)
    loaded, attempted = tmp_path / f"loaded-{mode}", tmp_path / f"attempted-{mode}"
    _write(blocker, "sitecustomize.py", f"import pathlib,socket\npathlib.Path({str(loaded)!r}).write_text('loaded')\nclass denied(socket.socket):\n def __new__(cls,*a,**k):\n  pathlib.Path({str(attempted)!r}).write_text('attempted'); raise AssertionError('NETWORK_ATTEMPT')\nsocket.socket=denied\n")
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(blocker),
        "PYTHONDONTWRITEBYTECODE": "1", "GITHUB_BASE_SHA": base,
        "GITHUB_HEAD_SHA": head, "GITHUB_HEAD_REF": BRANCH,
        "NARRATWIN_TEST_PARENT_TOKEN": "must-not-appear",
    }
    completed = subprocess.run([sys.executable, "scripts/guardrails_check.py"], cwd=repo, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20)
    assert (completed.returncode, completed.stdout, completed.stderr) == (returncode, stdout, "")
    if mode == "valid":
        prior_head, head = head, _commit(repo, "second push", empty=True)
        contexts = ((prior_head, "push", BRANCH, 0, stdout), ("invalid", "", "", 1, "Guardrail failures:\n- Governance preflight finding: GPF.REPO.HISTORY_UNAVAILABLE\n"))
        for context_base, event, ref, expected_code, expected_out in contexts:
            env.update(GITHUB_BASE_SHA=context_base, GITHUB_HEAD_SHA=head, GITHUB_EVENT_NAME=event, GITHUB_REF_NAME=ref)
            completed = subprocess.run([sys.executable, "scripts/guardrails_check.py"], cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=20)
            assert (completed.returncode, completed.stdout, completed.stderr) == (expected_code, expected_out, "")
    assert loaded.exists() and not attempted.exists()
    assert "GITHUB_TOKEN" not in env and "GH_TOKEN" not in env
    assert "must-not-appear" not in completed.stdout + completed.stderr
    assert "NETWORK_ATTEMPT" not in completed.stdout + completed.stderr


def test_historical_fixture_still_detects_unrestored_required_path(tmp_path: Path) -> None:
    repo, _ = _new_repo(tmp_path, "issue-176-historical")
    for path in PATHS[1:]:
        _write(repo, path, f"synthetic historical baseline {path}\n")
    base = _commit(repo, "historical baseline")
    _git(repo, "checkout", "-q", "-b", BRANCH)
    _write(repo, PREFLIGHT, json.dumps(FROZEN))
    _commit(repo, "preflight")
    for path in PATHS[1:]:
        if path != PATHS[3]:
            _write(repo, path, f"restored final {path}\n")
    head = _commit(repo, "implementation")
    assert _codes(repo, base, head) == ["GPF.SCOPE.REQUIRED_NOT_CHANGED"]


def test_missing_promisor_object_cannot_start_git_transport(tmp_path: Path) -> None:
    repo, base, head = _valid_repo(tmp_path)
    assert _codes(repo, base, head) == []
    marker, helper = tmp_path / "transport-attempted", tmp_path / "remote-helper"
    helper.write_text(f"#!/bin/sh\ntouch {marker}\nexit 1\n", encoding="utf-8")
    helper.chmod(0o700)
    for key, value in (("extensions.partialClone", "origin"), ("remote.origin.promisor", "true"), ("remote.origin.url", f"ext::{helper}"), ("protocol.ext.allow", "always")):
        _git(repo, "config", key, value)
    (repo / ".git" / "objects" / head[:2] / head[2:]).unlink()
    assert _codes(repo, base, head) == ["GPF.REPO.HISTORY_UNAVAILABLE"]
    assert not marker.exists()
