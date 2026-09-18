"""Issue551 route RED: real policy decisions, injected read-only Git boundary."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.governance_preflight_v1 import validate_governance_preflight
from scripts.quality.phase1_closure import runner

ROOT = Path(__file__).resolve().parents[2]
MODULE = "scripts.quality.issue551_provider_input_qualification_route"
BRANCH = "phase-1-closure-process-551-provider-input-environment-qualification"
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"
C1 = "c459ca12568985334b7f33287808d9960f37bca4"
HEAD = "a" * 40
PREFLIGHT = "docs/governance/preflights/issue-551.json"
DIGEST = "f370303c61329342ff08753432d77b5af43ed368b43ee3656cb126f171d86427"
RAW = (ROOT / PREFLIGHT).read_bytes()
ARTIFACT = json.loads(RAW)
CAPS = ARTIFACT["change_budget"]["per_file_charged_lines"]
PATHS = tuple(CAPS)


def load_route() -> Any:
    assert importlib.util.find_spec(MODULE) is not None, "Issue551 exact route is not implemented"
    return importlib.import_module(MODULE)


def numstat(charges: dict[str, int]) -> bytes:
    return b"".join(f"{count}\t0\t{path}\0".encode() for path, count in charges.items())


def git_evidence() -> dict[tuple[str, ...], bytes]:
    return {
        ("rev-parse", "HEAD"): HEAD.encode(),
        ("merge-base", BASE, HEAD): BASE.encode(),
        ("rev-list", "--reverse", f"{BASE}..{HEAD}"): f"{C1}\n{HEAD}\n".encode(),
        ("rev-parse", f"{C1}^"): BASE.encode(),
        ("show", f"{C1}:{PREFLIGHT}"): RAW,
        ("diff-tree", "--no-commit-id", "--name-only", "-r", C1): PREFLIGHT.encode(),
        ("diff", "--no-renames", "--numstat", "-z", BASE, HEAD, "--"): numstat(dict.fromkeys(PATHS, 1)),
        ("status", "--porcelain", "--untracked-files=all"): b"",
    }


def scope(monkeypatch: Any, rows: dict[tuple[str, ...], bytes], branch: str = BRANCH,
          raw: bytes = RAW, findings: tuple[Any, ...] = ()) -> list[str]:
    route = load_route()
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: raw if p == ROOT / PREFLIGHT else original(p))
    monkeypatch.setattr(route, "_git", lambda root, *args: rows.get(args))
    monkeypatch.setattr(route, "validate_governance_preflight_repository", lambda *args, **kwargs: list(findings))
    return route.validate_scope(ROOT, branch)


def test_frozen_fixture_is_a_valid_thirteen_path_plan() -> None:
    assert hashlib.sha256(RAW).hexdigest() == DIGEST
    assert len(PATHS) == 13 and sum(CAPS.values()) == 1340
    assert ARTIFACT["change_budget"]["maximum_additions_plus_deletions"] == 1200
    assert ARTIFACT["change_budget"]["deletions_grant_credit"] is False
    assert not validate_governance_preflight(ARTIFACT, context={
        "issue_number": 551, "branch": BRANCH, "changed_files": list(PATHS),
    })


def test_exact_branch_base_c1_and_raw_preflight_accept(monkeypatch: Any) -> None:
    assert scope(monkeypatch, git_evidence()) == []


@pytest.mark.parametrize("branch", [BRANCH + "-extra", BRANCH.replace("551", "5510"), "main"])
def test_scope_rejects_near_name_and_other_branches(monkeypatch: Any, branch: str) -> None:
    assert scope(monkeypatch, git_evidence(), branch=branch)


@pytest.mark.parametrize("key,value", [
    (("merge-base", BASE, HEAD), b"b" * 40),
    (("rev-list", "--reverse", f"{BASE}..{HEAD}"), ("b" * 40 + "\n" + HEAD).encode()),
    (("rev-parse", f"{C1}^"), b"b" * 40),
    (("diff-tree", "--no-commit-id", "--name-only", "-r", C1), (PREFLIGHT + "\nextra").encode()),
    (("show", f"{C1}:{PREFLIGHT}"), RAW + b"\n"),
])
def test_identity_or_first_commit_drift_rejects(monkeypatch: Any, key: tuple[str, ...], value: bytes) -> None:
    rows = git_evidence()
    rows[key] = value
    assert scope(monkeypatch, rows)


@pytest.mark.parametrize("both", [False, True])
def test_current_or_coherently_rehashed_raw_preflight_rejects(monkeypatch: Any, both: bool) -> None:
    rows = git_evidence()
    if both:
        rows[("show", f"{C1}:{PREFLIGHT}")] = RAW + b"\n"
    assert scope(monkeypatch, rows, raw=RAW + b"\n")


@pytest.mark.parametrize("mutation", ["extra", "missing", "rename", "binary", "negative", "duplicate", "credit"])
def test_path_or_uncountable_charge_rejects(monkeypatch: Any, mutation: str) -> None:
    charges = dict.fromkeys(PATHS, 1)
    if mutation == "extra":
        charges["backend/unauthorized.py"] = 1
    if mutation == "missing":
        charges.pop(PATHS[-1])
    raw = numstat(charges)
    if mutation == "rename":
        raw += b"1\t1\t\0old\0new\0"
    if mutation in {"binary", "negative", "credit", "duplicate"}:
        values = {"binary": "-\t-", "negative": "-1\t2", "credit": f"0\t{CAPS[PATHS[0]] + 1}", "duplicate": "1\t0"}
        raw = numstat({p: c for p, c in charges.items() if p != PATHS[0]})
        raw += f"{values[mutation]}\t{PATHS[0]}\0".encode()
        if mutation == "duplicate":
            raw += f"1\t0\t{PATHS[0]}\0".encode()
    rows = git_evidence()
    rows[("diff", "--no-renames", "--numstat", "-z", BASE, HEAD, "--")] = raw
    assert scope(monkeypatch, rows)


@pytest.mark.parametrize("total", [1200, 1201])
def test_aggregate_boundary_has_no_per_file_breach(monkeypatch: Any, total: int) -> None:
    charges = dict(CAPS)
    charges[PREFLIGHT] -= sum(charges.values()) - total
    assert all(0 <= count <= CAPS[path] for path, count in charges.items())
    rows = git_evidence()
    rows[("diff", "--no-renames", "--numstat", "-z", BASE, HEAD, "--")] = numstat(charges)
    assert bool(scope(monkeypatch, rows)) is (total > 1200)


def test_per_file_breach_below_aggregate_rejects(monkeypatch: Any) -> None:
    charges = dict.fromkeys(PATHS, 1)
    charges[PATHS[-1]] = CAPS[PATHS[-1]] + 1
    assert sum(charges.values()) < 1200
    rows = git_evidence()
    rows[("diff", "--no-renames", "--numstat", "-z", BASE, HEAD, "--")] = numstat(charges)
    assert scope(monkeypatch, rows)


def test_generic_preflight_failure_cannot_be_discarded(monkeypatch: Any) -> None:
    assert scope(monkeypatch, git_evidence(), findings=(SimpleNamespace(code="GPF.TEST.FAIL"),))


def test_actual_runner_rejects_scope_failure_instead_of_generic_fallback(monkeypatch: Any) -> None:
    route = load_route()
    monkeypatch.setattr(route, "validate_scope", lambda root, branch: ["ISSUE551_TEST_SCOPE_FAILURE"])
    monkeypatch.setattr(runner, "current_branch", lambda root: BRANCH)
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: pytest.fail("scope failure reached legacy checks"))
    assert runner.run_preserved_contracts() == 1


@pytest.mark.parametrize("branch", ["main", BRANCH + "-extra", "phase-1-closure-process-455-other"])
def test_unrelated_and_near_name_routes_keep_legacy_dispatch(monkeypatch: Any, branch: str) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: branch)
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)
    assert runner.run_preserved_contracts() == 31


def test_valid_551_scope_runs_all_preserved_contracts(monkeypatch: Any) -> None:
    route = load_route()
    calls: list[str] = []
    names = ("check_branch", "check_required_files", *runner.legacy.PRESERVED_CHECKS)
    checker = SimpleNamespace(**{name: (lambda failures, n=name: calls.append(n)) for name in names})
    monkeypatch.setattr(route, "validate_scope", lambda root, branch: [])
    monkeypatch.setattr(runner, "current_branch", lambda root: BRANCH)
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: checker)
    monkeypatch.setattr(runner.legacy, "legacy_parity_failures", lambda value: [])
    monkeypatch.setattr(runner.legacy, "check_active_demo_docs", lambda value, failures: calls.append("check_active_demo_docs"))
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)
    assert runner.run_preserved_contracts() == 0
    assert calls == list(names)
