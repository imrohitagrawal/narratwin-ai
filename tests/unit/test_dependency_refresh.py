"""Current security proof, followed by separately labelled historical compatibility.

RED: vulnerable, forged, duplicate or unrelated supplied inputs must not normalize.
"""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from scripts.ci.check_semgrep_security import (
    ALLOWED_TOOL_OVERRIDES,
    ContractError,
    load_security_profile,
)

ROOT = Path(__file__).resolve().parents[2]
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"
# Closed name sets: admitting any other record must fail, whatever its hash.
ROOT_VERSIONS = {
    "aiohttp": "3.14.5",
    "anyio": "4.14.2",
    "boto3": "1.43.124",
    "botocore": "1.43.124",
    "brotli": "1.2.1",
    "certifi": "2026.10.23",
    "filelock": "4.2.9",
    "fsspec": "2026.6.0",
    "jmespath": "1.1.0",
    "litellm": "1.100.4",
    "mako": "1.4.3",
    "msgpack": "1.2.4",
    "multidict": "6.9.1",
    "opentelemetry-api": "1.45.2",
    "opentelemetry-exporter-http-transport": "0.66b2",
    "opentelemetry-exporter-otlp-common": "0.66b2",
    "opentelemetry-exporter-otlp-proto-common": "1.45.2",
    "opentelemetry-exporter-otlp-proto-http": "1.45.2",
    "opentelemetry-instrumentation": "0.66b2",
    "opentelemetry-instrumentation-asgi": "0.66b2",
    "opentelemetry-instrumentation-fastapi": "0.66b2",
    "opentelemetry-proto": "1.45.2",
    "opentelemetry-sdk": "1.45.2",
    "opentelemetry-semantic-conventions": "0.66b2",
    "opentelemetry-util-http": "0.66b2",
    "pillow": "13.0.0",
    "pyasn1": "0.6.5",
    "pydantic-settings": "2.16.2",
    "pypdf": "6.21.4",
    "s3transfer": "0.19.3",
    "setuptools": "84.2.1",
    "soupsieve": "4.0.1",
    "urllib3": "2.8.0",
    "virtualenv": "21.15.5",
    "werkzeug": "3.1.9",
    "yarl": "1.25.1",
}
TOOL_VERSIONS = {
    "certifi": "2026.10.23",
    "mcp": "1.30.0",
    "opentelemetry-api": "1.45.2",
    "opentelemetry-exporter-http-transport": "0.66b2",
    "opentelemetry-exporter-otlp-common": "0.66b2",
    "opentelemetry-exporter-otlp-proto-common": "1.45.2",
    "opentelemetry-exporter-otlp-proto-http": "1.45.2",
    "opentelemetry-instrumentation": "0.66b2",
    "opentelemetry-instrumentation-requests": "0.66b2",
    "opentelemetry-instrumentation-threading": "0.66b2",
    "opentelemetry-proto": "1.45.2",
    "opentelemetry-sdk": "1.45.2",
    "opentelemetry-semantic-conventions": "0.66b2",
    "opentelemetry-util-http": "0.66b2",
    "pyjwt": "2.15.0",
    "semgrep": "1.183.0",
    "urllib3": "2.8.0",
}
ROOT_FLOORS = {
    "opentelemetry-api>=1.37.0": "opentelemetry-api>=1.45.1",
    "opentelemetry-sdk>=1.37.0": "opentelemetry-sdk>=1.45.1",
    "pypdf>=6.16.2": "pypdf>=6.21.4",
}
ROOT_DEV_FLOORS = {"pillow>=12.3.0": "pillow>=13.0.0"}
ROOT_EXTRA_FLOORS = {"litellm>=1.90.1": "litellm>=1.100.4"}
TOOL_REMOVED = {"importlib-metadata", "zipp"}


def test_backend_cpython_release_and_checksum_are_qualified() -> None:
    """RED: the known vulnerable image release must not satisfy current qualification."""
    profile = load_security_profile(ROOT)
    assert profile["cpython"] == {
        "version": "3.13.18",
        "sha256": "abb0102e6d4ae027509bcb82327d9dd85515b44a3ba8ad538cfc5e9847029f68",
    }


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"version": True, "sha256": "0" * 64},
        {"version": "3.14.1", "sha256": "0" * 64},
        {"version": "3.13.18", "sha256": "bad"},
    ],
)
def test_cpython_configuration_fails_closed(tmp_path: Path, bad: Any) -> None:
    """RED: missing, foreign or wrongly typed CPython configuration must not activate."""
    value = load_security_profile(ROOT)
    value["cpython"] = bad
    path = tmp_path / "docs/security/DEPENDENCY_REFRESH.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value))
    with pytest.raises(ContractError, match="CPython policy invalid"):
        load_security_profile(tmp_path)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@functools.lru_cache(maxsize=None)
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
            expected_project["tool"]["mypy"].update(
                explicit_package_bases=True, mypy_path="tests/unit"
            )
            expected_project["project"]["dependencies"] = [
                ROOT_FLOORS.get(row, row) for row in expected_project["project"]["dependencies"]
            ]
            extras = expected_project["project"]["optional-dependencies"]
            extras["providers"] = [ROOT_EXTRA_FLOORS.get(row, row) for row in extras["providers"]]
            groups = expected_project["dependency-groups"]
            groups["dev"] = [ROOT_DEV_FLOORS.get(row, row) for row in groups["dev"]]
        else:
            expected_project["project"]["dependencies"] = [
                f"semgrep=={policy['toolIdentity']['semgrep']}"
            ]
            expected_project["tool"]["uv"]["override-dependencies"] = list(ALLOWED_TOOL_OVERRIDES)
        assert parsed_project == expected_project
        current = tomllib.loads(inputs[lock])
        baseline = tomllib.loads(historical_text(lock))
        records = current["package"]
        assert len({row["name"] for row in records}) == len(records)
        expected_hashes = policy[name + "RecordHashes"]
        for package, expected_hash in expected_hashes.items():
            rows = [row for row in records if row["name"] == package]
            assert len(rows) == 1 and "sha256:" + digest(rows[0]) == expected_hash
        for package, version in policy[name + "Versions"].items():
            row = next(row for row in records if row["name"] == package)
            assert row["version"] == version
            assert row["source"] == {"registry": "https://pypi.org/simple"}
        original_records = {row["name"]: row for row in baseline["package"]}
        normalized = copy.deepcopy(current)
        removed = TOOL_REMOVED if name == "tool" else set()
        assert not removed & {row["name"] for row in records}
        kept = [
            original_records[row["name"]] if row["name"] in expected_hashes else row
            for row in records
            if row["name"] in original_records or row["name"] not in expected_hashes
        ]
        normalized["package"] = sorted(
            kept + [original_records[item] for item in removed], key=lambda row: row["name"]
        )
        if name == "tool":
            assert normalized.pop("manifest") == {
                "overrides": [
                    {"name": row.split("==")[0], "specifier": "==" + row.split("==")[1]}
                    for row in sorted(ALLOWED_TOOL_OVERRIDES)
                ]
            }
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
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: subprocess.CompletedProcess(args, 1))
    with pytest.raises(ContractError):
        security.verify_installed_pyjwt()


def _lock_block(text: str, name: str) -> tuple[int, int]:
    start = text.index('[[package]]\nname = "' + name + '"\n')
    end = text.find("\n[[package]]", start + 1)
    return start, len(text) if end == -1 else end


@pytest.mark.parametrize(
    ("field", "path"), [("root", "uv.lock"), ("tool", "tools/semgrep/uv.lock")]
)
def test_current_graph_refuses_a_coherent_downgrade_outside_the_closed_set(
    monkeypatch: pytest.MonkeyPatch, field: str, path: str
) -> None:
    """RED: relaxing the closed name sets to a subset test admits this rehashed downgrade."""
    inputs = current_inputs()
    start, end = _lock_block(inputs[path], "idna")
    block = inputs[path][start:end]
    version = next(
        row["version"] for row in tomllib.loads(inputs[path])["package"] if row["name"] == "idna"
    )
    candidate = dict(inputs)
    candidate[path] = (
        inputs[path][:start]
        + block.replace(f'version = "{version}"', 'version = "3.1"', 1)
        + inputs[path][end:]
    )
    record = next(
        row for row in tomllib.loads(candidate[path])["package"] if row["name"] == "idna"
    )
    profile = copy.deepcopy(load_security_profile(ROOT))
    profile[field + "Versions"]["idna"] = "3.1"
    profile[field + "RecordHashes"]["idna"] = "sha256:" + digest(record)
    monkeypatch.setitem(validate_current_inputs.__globals__, "load_security_profile", lambda _: profile)
    with pytest.raises(AssertionError):
        validate_current_inputs(candidate)


@pytest.mark.parametrize(
    "extra",
    [
        'constraints = [{ name = "click", specifier = "==8.1.0" }]\n',
        'dependency-metadata = [{ name = "semgrep", version = "1.183.0", requires-dist = [] }]\n',
    ],
)
def test_tool_lock_manifest_refuses_any_row_beyond_the_recorded_overrides(extra: str) -> None:
    """RED: dropping the manifest without comparing it hides these rows from the delta check."""
    inputs = current_inputs()
    path = "tools/semgrep/uv.lock"
    candidate = dict(inputs)
    candidate[path] = inputs[path].replace("[manifest]\n", "[manifest]\n" + extra, 1)
    assert candidate[path] != inputs[path]
    with pytest.raises(AssertionError):
        validate_current_inputs(candidate)


@pytest.mark.parametrize(
    ("field", "name", "bad"),
    [
        ("rootVersions", "pypdf", "0.66rc1"),
        ("rootVersions", "pypdf", "1.2b"),
        ("rootVersions", "pypdf", "1.2.3.dev1"),
        ("rootRecordHashes", "pypdf", "0" * 64),
        ("rootRecordHashes", "pypdf", "sha256:short"),
        ("toolRecordHashes", "semgrep", "0" * 64),
    ],
)
def test_profile_refuses_other_version_and_hash_forms(
    tmp_path: Path, field: str, name: str, bad: str
) -> None:
    """RED: widening the beta suffix, or restoring bare hex, which a secret scan reads as a key."""
    value = load_security_profile(ROOT)
    value[field][name] = bad
    path = tmp_path / "docs/security/DEPENDENCY_REFRESH.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value))
    with pytest.raises(ContractError, match="mapping invalid"):
        load_security_profile(tmp_path)
