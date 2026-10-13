#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = ROOT / "tools/semgrep"
TOOL_ENV = (ROOT / ".uv-cache/semgrep-venv").resolve()
EXPECTED_TARGETS = (
    "backend",
    "frontend/src",
    "frontend/tests",
    "scripts",
    "tests",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/workflows/eval-smoke.yml",
    ".github/workflows/quality.yml",
    ".github/workflows/quality-gates.yml",
    "docker-compose.yml",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    ".env.example",
    "pyproject.toml",
    "frontend/package.json",
)
EXPECTED_RULE_IDS = (
    "python-subprocess-shell-true",
    "python-exec-eval",
    "react-dangerously-set-inner-html",
    "github-action-mutable-ref",
)
CANARY_PATHS = {
    "scripts/ci/fixtures/semgrep/clean.py",
    "scripts/ci/fixtures/semgrep/positive.py",
}
REVIEWED_INPUTS = (
    "semgrep.yml",
    "scripts/ci/dependency-audit.sh",
    "scripts/ci/dependency-security.sh",
    "scripts/ci/fixtures/semgrep/clean.py",
    "scripts/ci/fixtures/semgrep/positive.py",
    "scripts/ci/run-semgrep.sh",
    "scripts/ci/semgrep-canary.yml",
    "scripts/ci/semgrep-targets.txt",
    "tools/semgrep/pyproject.toml",
    "tools/semgrep/uv.lock",
    "docs/security/DEPENDENCY_REFRESH.json",
)
FORBIDDEN_AUDIT_BYPASSES = (
    "--ignore-vuln",
    "pysec-2026-2132",
    "cve-2026-7246",
    "ghsa-47fr-3ffg-hgmw",
    "|| true",
    "pip_audit_ignore",
)


class ContractError(RuntimeError):
    pass


def _toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _locked_versions(path: Path) -> dict[str, set[str]]:
    versions: dict[str, set[str]] = {}
    for package in _toml(path)["package"]:
        version = package.get("version")
        if version is not None:
            versions.setdefault(_canonical_name(package["name"]), set()).add(version)
    return versions


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _manifest_targets(root: Path) -> tuple[str, ...]:
    lines = (root / "scripts/ci/semgrep-targets.txt").read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip() and not line.startswith("#"))


def _configured_rule_ids(path: Path) -> tuple[str, ...]:
    ids = re.findall(r"^\s+- id:\s*([a-z0-9-]+)\s*$", path.read_text(encoding="utf-8"), re.M)
    return tuple(ids)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def _version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise ContractError(f"non-numeric version is not allowed here: {value}") from exc


def load_security_profile(root: Path = ROOT) -> dict[str, Any]:
    """Validate public artifact policy; agreement never substitutes for a current audit."""

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            _require(key not in result, "duplicate security profile field")
            result[key] = value
        return result

    try:
        profile = json.loads(
            (root / "docs/security/DEPENDENCY_REFRESH.json").read_text(encoding="utf-8"),
            object_pairs_hook=unique,
        )
    except (OSError, ValueError) as error:
        raise ContractError("security profile unavailable") from error
    fields = {
        "schemaVersion",
        "baseSha",
        "rootVersions",
        "toolVersions",
        "toolIdentity",
        "rootRecordHashes",
        "toolRecordHashes",
        "rootProjectHash",
        "toolProjectHash",
        "apk",
        "sourceReceipts",
        "toolVerificationTimeoutSeconds",
    }
    _require(type(profile) is dict and set(profile) == fields, "security profile schema drifted")
    _require(
        type(profile["schemaVersion"]) is int and profile["schemaVersion"] == 1,
        "security profile version drifted",
    )
    _require(
        type(profile["toolVerificationTimeoutSeconds"]) is int
        and profile["toolVerificationTimeoutSeconds"] > 0,
        "tool verification timeout invalid",
    )

    def matches(value: Any, pattern: str) -> bool:
        return isinstance(value, str) and re.fullmatch(pattern, value, re.ASCII) is not None

    _require(matches(profile["baseSha"], r"[0-9a-f]{40}"), "security profile base invalid")
    for key in ("rootProjectHash", "toolProjectHash"):
        _require(matches(profile[key], r"[0-9a-f]{64}"), "security profile project hash invalid")
    for key in (
        "rootVersions",
        "toolVersions",
        "toolIdentity",
        "rootRecordHashes",
        "toolRecordHashes",
    ):
        values = profile[key]
        pattern = r"[0-9a-f]{64}" if key.endswith("Hashes") else r"\d+(?:\.\d+){1,2}"
        _require(
            type(values) is dict
            and bool(values)
            and all(
                matches(name, r"[a-z0-9]+(?:-[a-z0-9]+)*") and matches(value, pattern)
                for name, value in values.items()
            ),
            "security profile mapping invalid",
        )
    _require(
        set(profile["rootRecordHashes"]) == set(profile["rootVersions"]) | {"narratwin-ai"}
        and set(profile["toolRecordHashes"])
        == set(profile["toolVersions"]) | {"narratwin-semgrep-tool"},
        "security profile record cardinality drifted",
    )
    _require(
        set(profile["toolIdentity"])
        == {"semgrep", "click", "mcp", "cryptography", "pyjwt", "urllib3"}
        and all(
            profile["toolIdentity"].get(name) == version
            for name, version in profile["toolVersions"].items()
        ),
        "security profile tool identity drifted",
    )
    apk = profile["apk"]
    _require(
        type(apk) is dict
        and set(apk) == {"opensslApkVersion", "opensslVersion", "alpineRelease"}
        and matches(apk["opensslVersion"], r"\d+\.\d+\.\d+")
        and all(
            matches(apk[key], r"\d+\.\d+\.\d+-r\d+")
            for key in ("opensslApkVersion", "alpineRelease")
        ),
        "security profile APK policy invalid",
    )
    versions = profile["rootVersions"] | profile["toolVersions"]
    receipts = profile["sourceReceipts"]
    _require(
        type(receipts) is dict and set(receipts) == set(versions),
        "security source cardinality drifted",
    )
    for name, row in receipts.items():
        _require(
            type(row) is dict
            and set(row) == {"url", "sha256", "bytes", "version"}
            and row["version"] == versions[name]
            and row["url"] == f"https://pypi.org/pypi/{name}/{versions[name]}/json"
            and matches(row["sha256"], r"[0-9a-f]{64}")
            and type(row["bytes"]) is int
            and row["bytes"] > 0,
            "security source receipt invalid",
        )
    return cast(dict[str, Any], profile)


def verify_installed_pyjwt() -> None:
    """Exercise the options-reuse regression in the qualified, isolated tool interpreter."""
    timeout = load_security_profile()["toolVerificationTimeoutSeconds"]
    code = (
        "import jwt; options={}; original=options.copy(); "
        "key='local regression fixture key with sufficient length'; "
        "value=jwt.encode({'sub':'local'},key,algorithm='HS256'); "
        "jwt.decode(value,key,algorithms=['HS256'],options=options); assert options==original"
    )
    try:
        result = subprocess.run(
            [str(TOOL_ENV / "bin/python"), "-I", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ContractError("installed PyJWT regression unavailable") from error
    _require(result.returncode == 0, "installed PyJWT options regression failed")


def validate_reviewed_inputs(root: Path = ROOT) -> None:
    manifest_path = root / "tools/semgrep/reviewed-inputs.sha256"
    recorded: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, separator, relative_path = line.partition("  ")
        _require(bool(separator and digest and relative_path), "invalid reviewed-input hash line")
        _require(relative_path not in recorded, f"duplicate reviewed input: {relative_path}")
        recorded[relative_path] = digest

    _require(tuple(recorded) == REVIEWED_INPUTS, "reviewed Semgrep input manifest drifted")
    for relative_path, expected_digest in recorded.items():
        actual_digest = hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
        _require(
            actual_digest == expected_digest,
            f"reviewed Semgrep input changed without compatibility review: {relative_path}",
        )


def validate_audit_wrappers(root: Path = ROOT) -> None:
    wrapper_text = "\n".join(
        (root / path).read_text(encoding="utf-8")
        for path in (
            "scripts/ci/dependency-audit.sh",
            "scripts/ci/dependency-security.sh",
            "scripts/ci/run-semgrep.sh",
        )
    ).lower()
    for forbidden in FORBIDDEN_AUDIT_BYPASSES:
        _require(forbidden not in wrapper_text, f"forbidden audit bypass found: {forbidden}")


def validate_project_contract(root: Path = ROOT, *, today: object | None = None) -> None:
    del today
    root_project = _toml(root / "pyproject.toml")
    tool_project = _toml(root / "tools/semgrep/pyproject.toml")
    root_lock = _locked_versions(root / "uv.lock")
    tool_lock = _locked_versions(root / "tools/semgrep/uv.lock")
    identity = load_security_profile(root)["toolIdentity"]

    root_uv = root_project.get("tool", {}).get("uv", {})
    _require("override-dependencies" not in root_uv, "root dependency overrides are forbidden")
    _require("semgrep" not in root_lock, "Semgrep must not be present in the root lock")
    _require("mcp" not in root_lock, "MCP must not be present in the root lock")
    root_click = root_lock.get("click", set())
    _require(
        len(root_click) == 1 and _version_tuple(next(iter(root_click))) >= (8, 3, 3),
        "root Click must be locked to a fixed version >=8.3.3",
    )
    _require(
        tool_project["project"]["dependencies"] == [f"semgrep=={identity['semgrep']}"],
        "Semgrep tool pin must remain exact",
    )
    _require(
        "override-dependencies" not in tool_project["tool"]["uv"],
        "Semgrep tool dependency overrides are forbidden",
    )
    for name, version in identity.items():
        label = {"mcp": "MCP", "pyjwt": "PyJWT"}.get(name, name)
        _require(tool_lock.get(name) == {version}, f"tool {label} lock drifted")
    _require(_manifest_targets(root) == EXPECTED_TARGETS, "Semgrep target manifest drifted")
    validate_rule_ids(_configured_rule_ids(root / "semgrep.yml"))
    validate_reviewed_inputs(root)
    validate_audit_wrappers(root)


def validate_installed_tool(site_packages: Path) -> None:
    resolved = site_packages.resolve()
    _require(resolved.is_relative_to(TOOL_ENV), "tool audit path is outside isolated environment")
    _require(".venv" not in resolved.parts, "tool audit must not use the root environment")
    installed = {
        _canonical_name(distribution.metadata["Name"]): distribution.version
        for distribution in importlib.metadata.distributions(path=[str(resolved)])
        if distribution.metadata.get("Name")
    }
    for name, version in load_security_profile()["toolIdentity"].items():
        label = {"mcp": "MCP", "pyjwt": "PyJWT"}.get(name, name)
        _require(installed.get(name) == version, f"installed {label} identity mismatch")
    locked = _locked_versions(TOOL_ROOT / "uv.lock")
    unexpected = {
        f"{name}=={version}"
        for name, version in installed.items()
        if version not in locked.get(name, set())
    }
    _require(not unexpected, f"installed tool packages absent from lock: {sorted(unexpected)}")
    verify_installed_pyjwt()


def validate_scan_result(payload: dict[str, Any]) -> None:
    _require(not payload.get("errors"), "Semgrep reported parse or engine errors")
    results = payload.get("results")
    _require(isinstance(results, list), "Semgrep findings list is missing")
    _require(not results, "Semgrep repository scan reported security findings")
    scanned = payload.get("paths", {}).get("scanned", [])
    _require(isinstance(scanned, list) and bool(scanned), "Semgrep scanned zero files")
    _require(isinstance(payload.get("time"), dict), "Semgrep timing metadata is missing")


def validate_rule_ids(rule_ids: tuple[str, ...]) -> None:
    _require(rule_ids == EXPECTED_RULE_IDS, "Semgrep rule set is empty or drifted")


def validate_canary_result(payload: dict[str, Any]) -> None:
    _require(not payload.get("errors"), "Semgrep canary reported parse or engine errors")
    scanned = {str(path) for path in payload.get("paths", {}).get("scanned", [])}
    _require(scanned == CANARY_PATHS, "Semgrep canary did not scan exactly both fixtures")
    results = payload.get("results", [])
    _require(len(results) == 1, "Semgrep canary must produce exactly one finding")
    finding = results[0]
    _require(
        finding.get("check_id") == "scripts.ci.narratwin-semgrep-canary",
        "wrong canary rule",
    )
    _require(
        finding.get("path") == "scripts/ci/fixtures/semgrep/positive.py",
        "canary finding must come from the positive fixture",
    )


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict), "Semgrep JSON result must be an object")
    return cast(dict[str, Any], data)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("contract")
    installed = subparsers.add_parser("installed-tool")
    installed.add_argument("--site-packages", type=Path, required=True)
    scan = subparsers.add_parser("scan-result")
    scan.add_argument("path", type=Path)
    canary = subparsers.add_parser("canary-result")
    canary.add_argument("path", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "contract":
            validate_project_contract()
        elif args.command == "installed-tool":
            validate_installed_tool(args.site_packages)
        elif args.command == "scan-result":
            payload = _load_json(args.path)
            validate_scan_result(payload)
            print(
                "Semgrep repository scan contract passed: "
                f"{len(payload['paths']['scanned'])} files, 0 findings; "
                f"{len(EXPECTED_RULE_IDS)} configured rules"
            )
        elif args.command == "canary-result":
            payload = _load_json(args.path)
            validate_canary_result(payload)
            print("Semgrep canary contract passed: 2 files, 1 expected finding")
    except (ContractError, KeyError, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"Semgrep security contract failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
