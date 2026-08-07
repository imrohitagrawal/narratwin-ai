from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any, cast

import pytest
from packaging.version import Version

import scripts.ci.check_semgrep_security as semgrep_security
from scripts.ci.check_semgrep_security import (
    ContractError,
    EXPECTED_TARGETS,
    REVIEWED_INPUTS,
    validate_audit_wrappers,
    validate_canary_result,
    validate_installed_tool,
    validate_project_contract,
    validate_reviewed_inputs,
    validate_rule_ids,
    validate_scan_result,
)


ROOT = Path(__file__).resolve().parents[2]
ISSUE360_BASE = "b9a2a8cd4aa05328116565990fc30ae44592c875"
ISSUE396_BASE = "9ee3f4a4d3b8cf1e78b5a878904748b60d557a76"
BRACE_PATH = "node_modules/brace-expansion"
JS_YAML_PATH = "node_modules/js-yaml"
JS_YAML_431_INTEGRITY = (
    "sha512-CY6crGq313MX8GkwvB7tzgp99vjQxY1++5y10/BKN/GUfHqWaOGQMNZkBvqSzsZKWk/ijwHlWzzkLulsGHhjWQ=="
)
BRACE_509_INTEGRITY = (
    "sha512-ScQ4IuvIEF1TMlP7Zt+vjJ//9zlPb2SDcxWxM3bk8s6t6GGdJ7KO1dCcTidOPJKePW30LE/2cT7wCyPho9/Wxg=="
)
SEMGREP_LOCK_SHA256 = "1975bebb0fca718a45742ad13a759e2092162c44c944c310572b4d553de4d51c"


def _text_at(ref: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True, capture_output=True, check=True
    )
    return result.stdout


def _base_text(path: str) -> str:
    return _text_at(ISSUE360_BASE, path)


def _base_json(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_base_text(path)))


def _assert_js_yaml_431_contract(package_text: str, lock: dict[str, Any]) -> None:
    base_package = _text_at(ISSUE396_BASE, "frontend/package.json")
    base_lock = cast(dict[str, Any], json.loads(_text_at(ISSUE396_BASE, "frontend/package-lock.json")))
    assert package_text == base_package
    paths = [path for path in lock["packages"] if path.endswith(JS_YAML_PATH)]
    assert paths == [JS_YAML_PATH]
    js_yaml, base_js_yaml = lock["packages"][JS_YAML_PATH], base_lock["packages"][JS_YAML_PATH]
    assert (js_yaml["version"], js_yaml["resolved"], js_yaml["integrity"]) == (
        "4.3.1",
        "https://registry.npmjs.org/js-yaml/-/js-yaml-4.3.1.tgz",
        JS_YAML_431_INTEGRITY,
    )
    assert {key: value for key, value in js_yaml.items() if key not in {"version", "resolved", "integrity"}} == {
        key: value for key, value in base_js_yaml.items() if key not in {"version", "resolved", "integrity"}
    }
    normalized = copy.deepcopy(lock)
    for field in ("version", "resolved", "integrity"):
        normalized["packages"][JS_YAML_PATH][field] = base_js_yaml[field]
    assert normalized == base_lock


def test_frontend_js_yaml_lock_is_exact_isolated_and_patched() -> None:
    _assert_js_yaml_431_contract(
        (ROOT / "frontend/package.json").read_text(encoding="utf-8"),
        json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8")),
    )


def test_js_yaml_contract_rejects_identity_integrity_and_unrelated_drift() -> None:
    package_text = _text_at(ISSUE396_BASE, "frontend/package.json")
    base_lock = cast(dict[str, Any], json.loads(_text_at(ISSUE396_BASE, "frontend/package-lock.json")))
    patched = copy.deepcopy(base_lock)
    patched["packages"][JS_YAML_PATH].update(version="4.3.1", resolved="https://registry.npmjs.org/js-yaml/-/js-yaml-4.3.1.tgz", integrity=JS_YAML_431_INTEGRITY)
    mutations = []
    for field, value in (("version", "4.3.0"), ("resolved", "https://example.invalid/js-yaml.tgz"), ("integrity", "sha512-wrong")):
        candidate = copy.deepcopy(patched)
        candidate["packages"][JS_YAML_PATH][field] = value
        mutations.append((package_text, candidate))
    missing = copy.deepcopy(patched)
    del missing["packages"][JS_YAML_PATH]
    drifted = copy.deepcopy(patched)
    drifted["packages"]["node_modules/argparse"]["version"] = "0.0.0"
    mutations.extend(((package_text, missing), (package_text, drifted), (package_text + "\n", patched)))
    for candidate_package, candidate_lock in mutations:
        with pytest.raises((AssertionError, KeyError)):
            _assert_js_yaml_431_contract(candidate_package, candidate_lock)


def test_frontend_brace_expansion_override_and_lock_are_isolated_and_patched() -> None:
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8"))
    base_package, base_lock = _base_json("frontend/package.json"), _base_json("frontend/package-lock.json")

    assert package["overrides"]["brace-expansion"] == "5.0.9"
    normalized_package = copy.deepcopy(package)
    normalized_package["overrides"]["brace-expansion"] = base_package["overrides"]["brace-expansion"]
    assert normalized_package == base_package

    brace_paths = [path for path in lock["packages"] if path.endswith(BRACE_PATH)]
    assert brace_paths == [BRACE_PATH]
    brace = lock["packages"][BRACE_PATH]
    assert (brace["version"], brace["resolved"], brace["integrity"]) == (
        "5.0.9",
        "https://registry.npmjs.org/brace-expansion/-/brace-expansion-5.0.9.tgz",
        BRACE_509_INTEGRITY,
    )
    normalized_lock = copy.deepcopy(lock)
    for field in ("version", "resolved", "integrity"):
        normalized_lock["packages"][BRACE_PATH][field] = base_lock["packages"][BRACE_PATH][field]
    assert normalized_lock == base_lock


def _packages(lock_path: Path) -> dict[str, set[str]]:
    data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages: dict[str, set[str]] = {}
    for package in data["package"]:
        version = package.get("version")
        if version is not None:
            packages.setdefault(package["name"], set()).add(version)
    return packages


def test_root_and_semgrep_tool_locks_are_separate_and_patched() -> None:
    validate_project_contract(ROOT, today=dt.date(2026, 7, 14))

    root_project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    tool_project = tomllib.loads(
        (ROOT / "tools/semgrep/pyproject.toml").read_text(encoding="utf-8")
    )
    root_packages = _packages(ROOT / "uv.lock")
    tool_packages = _packages(ROOT / "tools/semgrep/uv.lock")

    assert "override-dependencies" not in root_project.get("tool", {}).get("uv", {})
    assert "semgrep" not in root_packages
    assert len(root_packages["click"]) == 1
    assert Version(next(iter(root_packages["click"]))) >= Version("8.3.3")
    assert tool_project["project"]["dependencies"] == ["semgrep==1.168.0"]
    assert tool_project["tool"]["uv"]["override-dependencies"] == ["click==8.3.3", "mcp==1.28.1"]
    assert tool_packages["semgrep"] == {"1.168.0"}
    assert tool_packages["click"] == {"8.3.3"}
    assert tool_packages["mcp"] == {"1.28.1"}
    assert tool_packages["cryptography"] == {"50.0.0"}
    assert tool_packages["pyjwt"] == {"2.13.0"}


def test_semgrep_cryptography_generated_lock_delta_is_exact_and_isolated() -> None:
    lock_bytes = (ROOT / "tools/semgrep/uv.lock").read_bytes()
    lock = tomllib.loads(lock_bytes.decode())
    base_lock = tomllib.loads(_base_text("tools/semgrep/uv.lock"))
    assert hashlib.sha256(lock_bytes).hexdigest() == SEMGREP_LOCK_SHA256

    current_indexes = [i for i, package in enumerate(lock["package"]) if package["name"] == "cryptography"]
    base_crypto = [package for package in base_lock["package"] if package["name"] == "cryptography"]
    assert len(current_indexes) == len(base_crypto) == 1
    assert lock["package"][current_indexes[0]]["version"] == "50.0.0"
    assert base_crypto[0]["version"] == "49.0.0"
    normalized = copy.deepcopy(lock)
    normalized["package"][current_indexes[0]] = base_crypto[0]
    assert normalized == base_lock


def test_semgrep_tool_contract_rejects_vulnerable_cryptography_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root_project: dict[str, Any] = {"tool": {"uv": {}}}
    tool_project: dict[str, Any] = {
        "project": {"dependencies": ["semgrep==1.168.0"]},
        "tool": {"uv": {"override-dependencies": ["click==8.3.3", "mcp==1.28.1"]}},
    }
    root_lock = {"click": {"8.3.3"}}

    monkeypatch.setattr(
        semgrep_security,
        "_toml",
        lambda path: tool_project if "tools/semgrep" in str(path) else root_project,
    )
    monkeypatch.setattr(semgrep_security, "_manifest_targets", lambda root: EXPECTED_TARGETS)
    monkeypatch.setattr(
        semgrep_security,
        "_configured_rule_ids",
        lambda path: semgrep_security.EXPECTED_RULE_IDS,
    )
    monkeypatch.setattr(semgrep_security, "validate_reviewed_inputs", lambda root: None)
    monkeypatch.setattr(semgrep_security, "validate_audit_wrappers", lambda root: None)

    for version, accepted in (("49.0.0", False), ("50.0.0", True)):
        tool_lock = {
            "semgrep": {"1.168.0"},
            "click": {"8.3.3"},
            "mcp": {"1.28.1"},
            "cryptography": {version},
        }
        monkeypatch.setattr(
            semgrep_security,
            "_locked_versions",
            lambda path, lock=tool_lock: lock if "tools/semgrep" in str(path) else root_lock,
        )
        if accepted:
            validate_project_contract(ROOT, today=dt.date(2026, 8, 4))
        else:
            with pytest.raises(ContractError, match="cryptography"):
                validate_project_contract(ROOT, today=dt.date(2026, 8, 4))


def test_semgrep_tool_contract_rejects_missing_wrong_or_extra_mcp_override(monkeypatch: pytest.MonkeyPatch) -> None:
    root_project: dict[str, Any] = {"tool": {"uv": {}}}
    root_lock: dict[str, set[str]] = {"click": {"8.3.3"}}
    base_tool: dict[str, Any] = {"project": {"dependencies": ["semgrep==1.168.0"]}, "tool": {"uv": {"override-dependencies": ["click==8.3.3", "mcp==1.28.1"]}}}
    base_lock: dict[str, set[str]] = {"semgrep": {"1.168.0"}, "click": {"8.3.3"}, "mcp": {"1.28.1"}}

    def install(tool_project: dict[str, Any], tool_lock: dict[str, set[str]]) -> None:
        monkeypatch.setattr(semgrep_security, "_toml", lambda path: tool_project if "tools/semgrep" in str(path) else root_project)
        monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: tool_lock if "tools/semgrep" in str(path) else root_lock)
        monkeypatch.setattr(semgrep_security, "_manifest_targets", lambda root: semgrep_security.EXPECTED_TARGETS)
        monkeypatch.setattr(semgrep_security, "_configured_rule_ids", lambda path: semgrep_security.EXPECTED_RULE_IDS)
        monkeypatch.setattr(semgrep_security, "validate_reviewed_inputs", lambda root: None)
        monkeypatch.setattr(semgrep_security, "validate_audit_wrappers", lambda root: None)

    for overrides in (["click==8.3.3"], ["click==8.3.3", "mcp==1.23.3"], ["click==8.3.3", "mcp==1.28.1", "other==1"]):
        candidate = copy.deepcopy(base_tool)
        candidate["tool"]["uv"]["override-dependencies"] = overrides
        install(candidate, copy.deepcopy(base_lock))
        with pytest.raises(ContractError, match="Click and MCP"):
            validate_project_contract(ROOT, today=dt.date(2026, 7, 17))
    install(copy.deepcopy(base_tool), {**base_lock, "mcp": {"1.23.3"}})
    with pytest.raises(ContractError, match="MCP lock"):
        validate_project_contract(ROOT, today=dt.date(2026, 7, 17))


def test_installed_semgrep_tool_identity_requires_locked_mcp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def dist(name: str, version: str) -> object:
        return type("Dist", (), {"metadata": {"Name": name}, "version": version})()

    site_packages = tmp_path / "semgrep-tool" / "lib"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(semgrep_security, "TOOL_ENV", tmp_path)
    lock = {"semgrep": {"1.168.0"}, "click": {"8.3.3"}, "mcp": {"1.28.1"}, "cryptography": {"50.0.0"}}
    installed = [dist("semgrep", "1.168.0"), dist("click", "8.3.3"), dist("mcp", "1.28.1"), dist("cryptography", "50.0.0")]
    monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: lock)
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: installed)
    validate_installed_tool(site_packages)
    installed[2] = dist("mcp", "1.23.3")
    with pytest.raises(ContractError, match="MCP identity"):
        validate_installed_tool(site_packages)


def test_installed_semgrep_tool_identity_rejects_vulnerable_cryptography(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def dist(name: str, version: str) -> object:
        return type("Dist", (), {"metadata": {"Name": name}, "version": version})()

    site_packages = tmp_path / "semgrep-tool" / "lib"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(semgrep_security, "TOOL_ENV", tmp_path)
    locked = {
        "semgrep": {"1.168.0"},
        "click": {"8.3.3"},
        "mcp": {"1.28.1"},
        "cryptography": {"50.0.0"},
    }
    monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: locked)
    installed = [
        dist("semgrep", "1.168.0"),
        dist("click", "8.3.3"),
        dist("mcp", "1.28.1"),
        dist("cryptography", "49.0.0"),
    ]
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: installed)
    with pytest.raises(ContractError, match="cryptography"):
        validate_installed_tool(site_packages)


def test_security_wrapper_is_fail_closed_without_advisory_suppression() -> None:
    wrapper = (ROOT / "scripts/ci/dependency-security.sh").read_text(encoding="utf-8")
    audit_wrapper = (ROOT / "scripts/ci/dependency-audit.sh").read_text(encoding="utf-8")
    semgrep_wrapper = (ROOT / "scripts/ci/run-semgrep.sh").read_text(encoding="utf-8")
    combined = f"{wrapper}\n{audit_wrapper}\n{semgrep_wrapper}".lower()

    assert "bash scripts/ci/dependency-audit.sh" in wrapper
    assert "uv run pip-audit --strict" in audit_wrapper
    assert "--path" in audit_wrapper
    assert "python3 scripts/ci/check_semgrep_security.py installed-tool" in audit_wrapper
    assert "bash scripts/ci/run-semgrep.sh" in wrapper
    for forbidden in (
        "--ignore-vuln",
        "pysec-2026-2132",
        "cve-2026-7246",
        "ghsa-47fr-3ffg-hgmw",
        "|| true",
        "pip_audit_ignore",
    ):
        assert forbidden not in combined

    assert "semgrep scan \\\n  --validate" in semgrep_wrapper
    assert "--config semgrep.yml" in semgrep_wrapper
    assert "--error" in semgrep_wrapper
    assert "--metrics=off" in semgrep_wrapper
    assert "--json-output \"${SCAN_RESULT}\"" in semgrep_wrapper


def test_runtime_bypass_validator_covers_the_actual_audit_wrapper(tmp_path: Path) -> None:
    for relative_path in (
        "scripts/ci/dependency-audit.sh",
        "scripts/ci/dependency-security.sh",
        "scripts/ci/run-semgrep.sh",
    ):
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("set -euo pipefail\n", encoding="utf-8")

    validate_audit_wrappers(tmp_path)
    (tmp_path / "scripts/ci/dependency-audit.sh").write_text(
        "uv run pip-audit --ignore-vuln example\n", encoding="utf-8"
    )
    with pytest.raises(ContractError, match="forbidden audit bypass"):
        validate_audit_wrappers(tmp_path)


def test_reviewed_semgrep_inputs_are_hash_bound(tmp_path: Path) -> None:
    for relative_path in REVIEWED_INPUTS:
        source = ROOT / relative_path
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    manifest = tmp_path / "tools/semgrep/reviewed-inputs.sha256"
    manifest.write_text(
        "".join(
            f"{hashlib.sha256((tmp_path / path).read_bytes()).hexdigest()}  {path}\n"
            for path in REVIEWED_INPUTS
        ),
        encoding="utf-8",
    )
    validate_reviewed_inputs(tmp_path)

    with (tmp_path / "semgrep.yml").open("a", encoding="utf-8") as config:
        config.write("\n")
    with pytest.raises(ContractError, match="changed without compatibility review"):
        validate_reviewed_inputs(tmp_path)


def test_semgrep_target_manifest_is_exact_and_independently_guarded() -> None:
    manifest = ROOT / "scripts/ci/semgrep-targets.txt"
    actual = tuple(
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    )
    assert actual == EXPECTED_TARGETS

    shrunk = actual[:-1]
    assert len(shrunk) != len(EXPECTED_TARGETS)


def test_repository_scan_requires_files_no_errors_and_zero_findings() -> None:
    payload: dict[str, Any] = {
        "errors": [],
        "results": [],
        "paths": {"scanned": ["backend/app/main.py"]},
        "time": {},
    }
    validate_scan_result(payload)

    mutation: dict[str, Any]
    for mutation in (
        {"paths": {"scanned": []}},
        {"errors": [{"message": "parse failure"}]},
        {"results": [{"check_id": "python-exec-eval"}]},
    ):
        candidate = copy.deepcopy(payload)
        candidate.update(mutation)
        with pytest.raises(ContractError):
            validate_scan_result(candidate)

    with pytest.raises(ContractError):
        validate_rule_ids(())


def test_semgrep_canary_requires_one_finding_and_both_files() -> None:
    payload: dict[str, Any] = {
        "errors": [],
        "paths": {
            "scanned": [
                "scripts/ci/fixtures/semgrep/clean.py",
                "scripts/ci/fixtures/semgrep/positive.py",
            ]
        },
        "results": [
            {
                "check_id": "scripts.ci.narratwin-semgrep-canary",
                "path": "scripts/ci/fixtures/semgrep/positive.py",
            }
        ],
    }
    validate_canary_result(payload)

    mutation: dict[str, Any]
    for mutation in (
        {"results": []},
        {"paths": {"scanned": ["scripts/ci/fixtures/semgrep/positive.py"]}},
        {"errors": [{"message": "engine failure"}]},
    ):
        candidate = copy.deepcopy(payload)
        candidate.update(mutation)
        with pytest.raises(ContractError):
            validate_canary_result(candidate)


def test_override_expiry_fails_closed() -> None:
    with pytest.raises(ContractError, match="expired"):
        validate_project_contract(ROOT, today=dt.date(2026, 8, 14))


def test_backend_build_requires_explicit_click_and_semgrep_inventory() -> None:
    docker_build = (ROOT / "scripts/ci/docker-build.sh").read_text(encoding="utf-8")
    inventory = (ROOT / "scripts/ci/backend-image-package-check.sh").read_text(
        encoding="utf-8"
    )

    assert (
        "BACKEND_IMAGE=narratwin-ai-backend:ci "
        "bash scripts/ci/backend-image-package-check.sh"
    ) in docker_build
    assert 'importlib.metadata.version("click")' in inventory
    assert "click_version < (8, 3, 3)" in inventory
    assert 'importlib.metadata.version("semgrep")' in inventory
