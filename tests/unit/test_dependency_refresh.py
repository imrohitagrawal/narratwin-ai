"""Current security proof, followed by separately labelled historical compatibility.

RED: vulnerable, forged, duplicate or unrelated supplied inputs must not normalize.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from scripts.ci.check_semgrep_security import ContractError, load_security_profile

ROOT = Path(__file__).resolve().parents[2]
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"
ROOT_VERSIONS = {
    "anyio": "4.14.2",
    "pypdf": "6.20.1",
    "soupsieve": "2.9",
    "urllib3": "2.8.0",
    "virtualenv": "21.14.7",
    "werkzeug": "3.1.9",
}
TOOL_VERSIONS = {"semgrep": "1.180.0", "pyjwt": "2.15.0", "urllib3": "2.8.0"}


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def historical_text(path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{BASE}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def current_inputs() -> dict[str, str]:
    return {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "pyproject.toml",
            "uv.lock",
            "tools/semgrep/pyproject.toml",
            "tools/semgrep/uv.lock",
        )
    }


def validate_current_inputs(inputs: dict[str, str]) -> None:
    """Validate the supplied pair itself before any historical replacement."""
    policy = load_security_profile(ROOT)
    assert policy["baseSha"] == BASE
    assert set(policy["rootVersions"]) == set(ROOT_VERSIONS) | {"packaging", "python-discovery"}
    assert set(policy["toolVersions"]) == set(TOOL_VERSIONS)
    assert set(inputs) == set(current_inputs())
    for name, project, lock in (
        ("root", "pyproject.toml", "uv.lock"),
        ("tool", "tools/semgrep/pyproject.toml", "tools/semgrep/uv.lock"),
    ):
        parsed_project = tomllib.loads(inputs[project])
        assert digest(parsed_project) == policy[name + "ProjectHash"]
        baseline_project = tomllib.loads(historical_text(project))
        expected_project = copy.deepcopy(baseline_project)
        if name == "root":
            expected_project["project"]["dependencies"] = [
                f"pypdf>={policy['rootVersions']['pypdf']}" if row == "pypdf>=6.16.2" else row
                for row in expected_project["project"]["dependencies"]
            ]
        else:
            expected_project["project"]["dependencies"] = [
                f"semgrep=={policy['toolIdentity']['semgrep']}"
            ]
        assert parsed_project == expected_project
        current = tomllib.loads(inputs[lock])
        baseline = tomllib.loads(historical_text(lock))
        records = current["package"]
        assert len({row["name"] for row in records}) == len(records)
        expected_hashes = policy[name + "RecordHashes"]
        for package, expected_hash in expected_hashes.items():
            rows = [row for row in records if row["name"] == package]
            assert len(rows) == 1 and digest(rows[0]) == expected_hash
        for package, version in policy[name + "Versions"].items():
            row = next(row for row in records if row["name"] == package)
            assert row["version"] == version
            assert row["source"] == {"registry": "https://pypi.org/simple"}
        original_records = {row["name"]: row for row in baseline["package"]}
        normalized = copy.deepcopy(current)
        normalized["package"] = [
            original_records[row["name"]] if row["name"] in expected_hashes else row
            for row in records
        ]
        assert normalized == baseline


def validated_historical_text(path: str) -> str:
    """Current source remains proved; old mutation suites exercise the preserved base."""
    validate_current_inputs(current_inputs())
    return historical_text(path)


def test_current_root_security_versions() -> None:
    lock = tomllib.loads(current_inputs()["uv.lock"])
    for name, version in ROOT_VERSIONS.items():
        records = [row for row in lock["package"] if row["name"] == name]
        assert len(records) == 1 and records[0]["version"] == version


def test_current_tool_security_versions() -> None:
    lock = tomllib.loads(current_inputs()["tools/semgrep/uv.lock"])
    for name, version in TOOL_VERSIONS.items():
        records = [row for row in lock["package"] if row["name"] == name]
        assert len(records) == 1 and records[0]["version"] == version


def test_current_graph_has_exact_provenance_and_only_qualified_delta() -> None:
    validate_current_inputs(current_inputs())


@pytest.mark.parametrize("path", ["uv.lock", "tools/semgrep/uv.lock"])
def test_current_graph_rejects_every_record_provenance_and_structure_mutation(path: str) -> None:
    """RED: replacing, duplicating, hiding or forging a current record cannot be erased."""
    inputs = current_inputs()
    lock = tomllib.loads(inputs[path])
    hashes = load_security_profile(ROOT)[
        "rootRecordHashes" if path == "uv.lock" else "toolRecordHashes"
    ]
    for name in hashes:
        record = next(row for row in lock["package"] if row["name"] == name)
        block_start = inputs[path].index('[[package]]\nname = "' + name + '"\n')
        block_end = inputs[path].find("\n[[package]]", block_start + 1)
        if block_end == -1:
            block_end = len(inputs[path])
        block = inputs[path][block_start:block_end]
        replacements = [
            "",
            block + "\n" + block,
            block.replace('version = "' + record["version"] + '"', 'version = "0.0.0"', 1),
        ]
        if "sdist" in record:
            replacements += [
                block.replace(record["sdist"]["hash"], "sha256:" + "0" * 64),
                block.replace(record["sdist"]["url"], "https://example.invalid/forged"),
                block.replace(
                    'registry = "https://pypi.org/simple"', 'registry = "https://example.invalid"'
                ),
                block.replace("size = " + str(record["sdist"]["size"]), "size = 1", 1),
                block + '\nforged = "extra"\n',
            ]
        for replacement in replacements:
            candidate = dict(inputs)
            candidate[path] = inputs[path][:block_start] + replacement + inputs[path][block_end:]
            with pytest.raises((AssertionError, KeyError, ValueError, StopIteration)):
                validate_current_inputs(candidate)
    # A change outside the admitted record set must not disappear during normalization.
    candidate = dict(inputs)
    candidate[path] = inputs[path].replace('version = "2.6.2"', 'version = "0.0.0"', 1)
    if candidate[path] == inputs[path]:
        candidate[path] = inputs[path].replace("revision = 3", "revision = 99", 1)
    assert candidate[path] != inputs[path]
    with pytest.raises(AssertionError):
        validate_current_inputs(candidate)


@pytest.mark.parametrize("path", ["pyproject.toml", "tools/semgrep/pyproject.toml"])
def test_current_project_rejects_old_floor_and_foreign_configuration(path: str) -> None:
    inputs = current_inputs()
    for text in (historical_text(path), inputs[path] + "\n[unexpected]\nactivation = true\n"):
        candidate = dict(inputs)
        candidate[path] = text
        with pytest.raises(AssertionError):
            validate_current_inputs(candidate)


def test_profile_schema_rejects_missing_foreign_duplicate_and_illtyped_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "docs/security/DEPENDENCY_REFRESH.json"
    path.parent.mkdir(parents=True)
    profile = load_security_profile(ROOT)
    mutations: list[dict[str, Any]] = []
    for key in profile:
        candidate = copy.deepcopy(profile)
        candidate.pop(key)
        mutations.append(candidate)
    for key, value in (
        ("schemaVersion", True),
        ("baseSha", "bad"),
        ("toolIdentity", {}),
        ("sourceReceipts", []),
        ("apk", {"opensslVersion": "bad"}),
    ):
        candidate = copy.deepcopy(profile)
        candidate[key] = value
        mutations.append(candidate)
    mutations.append({**profile, "foreign": "field"})
    for candidate in mutations:
        path.write_text(json.dumps(candidate))
        with pytest.raises(ContractError):
            load_security_profile(tmp_path)
    path.write_text(json.dumps(profile)[:-1] + ', "schemaVersion": 1}')
    with pytest.raises(ContractError):
        load_security_profile(tmp_path)
    path.unlink()
    with pytest.raises(ContractError):
        load_security_profile(tmp_path)


def test_tool_regression_uses_isolated_interpreter_and_effective_timeout(monkeypatch: Any) -> None:
    import scripts.ci.check_semgrep_security as security

    calls: list[tuple[list[str], dict[str, Any]]] = []

    def fake(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake)
    security.verify_installed_pyjwt()
    assert calls[0][0][:3] == [str(security.TOOL_ENV / "bin/python"), "-I", "-c"]
    assert "assert options==original" in calls[0][0][3]
    assert calls[0][1]["timeout"] == load_security_profile(ROOT)["toolVerificationTimeoutSeconds"]
    monkeypatch.setattr(
        subprocess, "run", lambda args, **kw: subprocess.CompletedProcess(args, 1)
    )
    with pytest.raises(ContractError):
        security.verify_installed_pyjwt()
