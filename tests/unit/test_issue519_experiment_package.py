"""Exact-scope regression and fail-closed boundaries for the Issue 519 successor."""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace
from typing import Any, cast

import pytest

from scripts.quality.phase1_closure import runner

BRANCH = "phase-1-closure-process-519-experiment-first-package-v2"
PREFLIGHT = "docs/governance/preflights/issue-519.json"


@pytest.fixture
def packet(monkeypatch: Any) -> dict[str, Any]:
    raw = (runner.ROOT / PREFLIGHT).read_bytes()
    paths = json.loads(raw)["scope"]["required"]
    state: dict[str, Any] = {
        "manifest": raw, "first": raw, "ancestry": b"", "paths": paths,
        "calls": [], "findings": [], "parity": [],
        "numstat": "".join(f"1\t0\t{path}\0" for path in paths).encode(),
    }
    checker = runner.legacy._load_checker()
    monkeypatch.setattr(checker, "current_branch", lambda: BRANCH)
    monkeypatch.setattr(checker, "changed_files", lambda: state["paths"])

    def old_route() -> int:
        failures: list[str] = []
        checker.check_changed_files(failures)
        return int(bool(failures))

    monkeypatch.setattr(runner, "current_branch", lambda root: BRANCH)
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", old_route)
    # During RED the missing issue module does not mask the actual legacy rejection.
    try:
        module = importlib.import_module("scripts.quality.issue519_experiment_package")
    except ModuleNotFoundError as error:
        if error.name != "scripts.quality.issue519_experiment_package":
            raise
        return state

    def git(root: Any, *args: str) -> bytes | None:
        if args == ("rev-parse", "HEAD"):
            return b"a" * 40
        if args[0] == "merge-base":
            return cast(bytes | None, state["ancestry"])
        if args[0] == "show":
            if args[1].startswith(module.C1 + ":"):
                return cast(bytes | None, state["first"])
            return cast(bytes | None, state["manifest"])
        if args[:2] == ("diff", "--name-only"):
            return "".join(f"{path}\0" for path in state["paths"]).encode()
        if args[:2] == ("diff", "--numstat"):
            return cast(bytes | None, state["numstat"])
        raise AssertionError(f"Unexpected Git boundary: {args}")

    fake = SimpleNamespace(
        check_branch=lambda failures: state["calls"].append("branch"),
        check_required_files=lambda failures: state["calls"].append("required"),
        check_final_review_baseline=lambda failures: state["calls"].append("preserved"),
    )
    monkeypatch.setattr(module, "_git", git)
    monkeypatch.setattr(module, "validate_governance_preflight_repository", lambda *a, **k: state["findings"])
    monkeypatch.setattr(runner.legacy, "_load_checker", lambda: fake)
    monkeypatch.setattr(runner.legacy, "legacy_parity_failures", lambda value: state["parity"])
    monkeypatch.setattr(runner.legacy, "PRESERVED_CHECKS", ("check_final_review_baseline",))
    monkeypatch.setattr(runner.legacy, "_print_result", lambda failures: int(bool(failures)))
    return state


def test_exact_dispatch_replaces_frozen_path_list_only(packet: dict[str, Any]) -> None:
    assert runner.run_preserved_contracts() == 0
    assert packet["calls"] == ["branch", "required", "preserved"]


@pytest.mark.parametrize("mutation", ["extra", "missing", "substituted", "duplicate"])
def test_path_mismatch_stops_preserved(packet: dict[str, Any], mutation: str) -> None:
    paths = packet["paths"][:]
    if mutation == "extra":
        paths.append("extra.md")
    elif mutation == "missing":
        paths.pop()
    elif mutation == "substituted":
        paths[-1] = "substitute.md"
    else:
        paths.append(paths[0])
    packet["paths"] = paths
    assert runner.run_preserved_contracts() == 1
    assert packet["calls"] == []


@pytest.mark.parametrize("mutation", [
    "per-file", "aggregate", "binary", "malformed", "unavailable", "negative", "duplicate", "missing", "termination",
])
def test_uncountable_or_excess_lines_stop_preserved(packet: dict[str, Any], mutation: str) -> None:
    caps = json.loads(packet["manifest"])["change_budget"]["per_file_charged_lines"]
    records = [f"1\t0\t{path}" for path in packet["paths"]]
    first = packet["paths"][0]
    if mutation == "per-file":
        records[0] = f"{caps[first]}\t1\t{first}"
    elif mutation == "aggregate":
        records = [f"{cap}\t0\t{path}" for path, cap in caps.items()]
    elif mutation == "binary":
        records[0] = f"-\t-\t{first}"
    elif mutation == "malformed":
        records[0] = "1\t0"
    elif mutation == "negative":
        records[0] = f"-1\t0\t{first}"
    elif mutation == "duplicate":
        records.append(records[0])
    elif mutation == "missing":
        records.pop()
    raw = ("\0".join(records) + ("" if mutation == "termination" else "\0")).encode()
    packet["numstat"] = None if mutation == "unavailable" else raw
    assert runner.run_preserved_contracts() == 1
    assert packet["calls"] == []


@pytest.mark.parametrize("mutation", ["bytes", "coherent-swap", "unavailable"])
def test_head_preflight_cannot_rewrite_c1_authority(packet: dict[str, Any], mutation: str) -> None:
    if mutation == "bytes":
        packet["manifest"] += b"\n"
    elif mutation == "unavailable":
        packet["manifest"] = None
    else:
        manifest = json.loads(packet["manifest"])
        old = manifest["scope"]["required"][-1]
        for key in ("required", "allowed_prefixes"):
            manifest["scope"][key][-1] = "substitute.md"
        caps = manifest["change_budget"]["per_file_charged_lines"]
        caps["substitute.md"] = caps.pop(old)
        packet["manifest"] = json.dumps(manifest).encode()
        packet["paths"][-1] = "substitute.md"
    assert runner.run_preserved_contracts() == 1
    assert packet["calls"] == []


def test_repository_preflight_finding_stops_preserved(packet: dict[str, Any]) -> None:
    packet["findings"] = [SimpleNamespace(code="GPF.REPO.PREFLIGHT_NOT_FIRST")]
    assert runner.run_preserved_contracts() == 1
    assert packet["calls"] == []


@pytest.mark.parametrize("field", ["first", "ancestry"])
def test_pinned_c1_custody_and_ancestry_required(packet: dict[str, Any], field: str) -> None:
    packet[field] = None
    assert runner.run_preserved_contracts() == 1
    assert packet["calls"] == []


def test_readable_but_byte_altered_c1_stops_preserved(packet: dict[str, Any]) -> None:
    packet["first"] += b"\n"
    assert json.loads(packet["first"]) == json.loads(packet["manifest"])
    assert runner.run_preserved_contracts() == 1
    assert packet["calls"] == []


def test_parity_failure_prevents_preserved_checks(packet: dict[str, Any]) -> None:
    packet["parity"] = ["frozen checker drifted"]
    assert runner.run_preserved_contracts() == 1
    assert "preserved" not in packet["calls"]


@pytest.mark.parametrize("branch", [BRANCH + "-other", BRANCH.removesuffix("-v2"), "cut1-519-other"])
def test_lookalikes_retain_legacy_fallback(monkeypatch: Any, branch: str) -> None:
    monkeypatch.setattr(runner, "current_branch", lambda root: branch)
    monkeypatch.setattr(runner.legacy, "run_preserved_contracts", lambda: 31)
    assert runner.run_preserved_contracts() == 31


def test_import_has_no_git_or_legacy_side_effects(monkeypatch: Any) -> None:
    module = importlib.import_module("scripts.quality.issue519_experiment_package")

    def prohibited(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Import must not execute Git or preserved checks")

    monkeypatch.setattr(module.subprocess, "run", prohibited)
    monkeypatch.setattr(runner.legacy, "_load_checker", prohibited)
    importlib.reload(module)


def test_wrong_branch_rejected_by_scope() -> None:
    module = importlib.import_module("scripts.quality.issue519_experiment_package")
    assert module.validate_scope(runner.ROOT, BRANCH + "-other") == ["Issue #519 exact branch required."]


def test_current_pvr_audio_and_driver_contract_is_bound() -> None:
    module = importlib.import_module("scripts.quality.issue519_experiment_package")
    assert module.validate_pvr_contract(runner.ROOT) == []


@pytest.mark.parametrize(
    ("path", "old", "new", "expected"),
    (
        (
            "docs/work/demo-comparison/EXECUTION_PLAN.md",
            "has no separate WAV input",
            "accepts a separate WAV input",
            "PVR input schema",
        ),
        (
            "docs/work/demo-comparison/EXECUTION_PLAN.md",
            "newly recorded, consented real-office performance",
            "stock performance",
            "primary driver rights route",
        ),
        (
            "docs/work/demo-comparison/EXECUTION_PLAN.md",
            "No conversion or remux is authorized now.",
            "Conversion is authorized now.",
            "derived-audio authority",
        ),
        (
            "docs/work/demo-comparison/DECISIONS.md",
            "Stock Envato/iStock footage is reference/fallback diagnostic material only",
            "Stock footage is the primary driver",
            "stock driver exclusion",
        ),
    ),
)
def test_pvr_contract_mutations_fail_closed(
    tmp_path: Any, path: str, old: str, new: str, expected: str
) -> None:
    module = importlib.import_module("scripts.quality.issue519_experiment_package")
    for required_path in module.PVR_CONTRACT_PATHS:
        source = runner.ROOT / required_path
        target = tmp_path / required_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    target = tmp_path / path
    original = target.read_text(encoding="utf-8")
    assert old in original
    target.write_text(original.replace(old, new), encoding="utf-8")
    assert any(expected in failure for failure in module.validate_pvr_contract(tmp_path))
