from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.metadata
import shutil
import tomllib
from pathlib import Path
from typing import Any

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
    monkeypatch.setattr(semgrep_security, "_locked_versions", lambda path: {"semgrep": {"1.168.0"}, "click": {"8.3.3"}, "mcp": {"1.28.1"}})
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: [dist("semgrep", "1.168.0"), dist("click", "8.3.3"), dist("mcp", "1.28.1")])
    validate_installed_tool(site_packages)
    monkeypatch.setattr(importlib.metadata, "distributions", lambda path: [dist("semgrep", "1.168.0"), dist("click", "8.3.3"), dist("mcp", "1.23.3")])
    with pytest.raises(ContractError, match="MCP identity"):
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
