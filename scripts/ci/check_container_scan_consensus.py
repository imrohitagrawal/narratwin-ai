#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlsplit


TARGET_CVES = ("CVE-2026-11940", "CVE-2026-11972", "CVE-2026-15308")
ARTIFACTS = (
    "backend-trivy",
    "backend-grype",
    "frontend-trivy",
    "frontend-grype",
    "backend-sbom",
    "frontend-sbom",
    "backend-cpython-regressions",
)
PATCH_SHA256 = {
    "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
}
BASE_IMAGE = (
    "docker.io/library/python:3.13-alpine@"
    "sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
)
FRONTEND_SECRET_FIELDS = (
    "previewModeId",
    "previewModeSigningKey",
    "previewModeEncryptionKey",
    "serverActionKey",
)
FRONTEND_ENGINE_CONFIG_DEFAULTS = {
    "AttachStderr": False,
    "AttachStdin": False,
    "AttachStdout": False,
    "Domainname": "",
    "Hostname": "",
    "Image": "",
    "OnBuild": None,
    "OpenStdin": False,
    "StdinOnce": False,
    "Tty": False,
    "Volumes": None,
}
FRONTEND_INVENTORY_RECORD_BOUNDS = {"amd64": (1580, 1620), "arm64": (1580, 1620)}
FRONTEND_INVENTORY_PATTERN = re.compile(r"^(?P<records>[1-9]\d{0,4}):(?P<digest>[0-9a-f]{64})$")
FRONTEND_RUNTIME_INDEX = "sha256:aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019"
FRONTEND_RUNTIME_PLATFORM_DIGESTS = {
    "amd64": "sha256:b4fea132199070b0c8ea9ac66f363fe2cd6d1e4f994e61d8c87976c2157a1b8a",
    "arm64": "sha256:d778881fd638833a2a0ed0fbb30577718729ab08112776dea4555eb5551826da",
}
FRONTEND_NODE_SOURCE_INDEX = FRONTEND_RUNTIME_INDEX
FRONTEND_NODE_SOURCE_PLATFORM_DIGESTS = {
    "amd64": "sha256:b4fea132199070b0c8ea9ac66f363fe2cd6d1e4f994e61d8c87976c2157a1b8a",
    "arm64": "sha256:d778881fd638833a2a0ed0fbb30577718729ab08112776dea4555eb5551826da",
}
FRONTEND_RUNTIME_OPENSSL_VERSION = "3.5.7"
FRONTEND_RUNTIME_PACKAGES = {
    "alpine-keys": "2.6-r0", "alpine-release": "3.24.1-r0",
    "ca-certificates-bundle": "20260611-r0", "libgcc": "15.2.0-r5",
    "libstdc++": "15.2.0-r5", "musl": "1.2.6-r2",
}
FRONTEND_SBOM_COMPONENTS = {
    "alpine-keys": ("2.6-r0", ("MIT",), "alpine", "3.24.1"),
    "alpine-release": ("3.24.1-r0", ("MIT",), "alpine", "3.24.1"),
    "ca-certificates-bundle": ("20260611-r0", ("MIT", "MPL-2.0"), "alpine", "3.24.1"),
    "libgcc": ("15.2.0-r5", ("GPL-2.0-or-later", "LGPL-2.1-or-later"), "alpine", "3.24.1"),
    "libstdc++": ("15.2.0-r5", ("GPL-2.0-or-later", "LGPL-2.1-or-later"), "alpine", "3.24.1"),
    "musl": ("1.2.6-r2", ("MIT",), "alpine", "3.24.1"),
}
FRONTEND_SHARP_COMPONENTS = {
    "amd64": {
        ("sharp", "0.35.3", "pkg:npm/sharp@0.35.3"),
        ("sharp-linuxmusl-x64", "0.35.3", "pkg:npm/%40img/sharp-linuxmusl-x64@0.35.3"),
        ("sharp-libvips-linuxmusl-x64", "1.3.2", "pkg:npm/%40img/sharp-libvips-linuxmusl-x64@1.3.2"),
    },
    "arm64": {
        ("sharp", "0.35.3", "pkg:npm/sharp@0.35.3"),
        ("sharp-linuxmusl-arm64", "0.35.3", "pkg:npm/%40img/sharp-linuxmusl-arm64@0.35.3"),
        ("sharp-libvips-linuxmusl-arm64", "1.3.2", "pkg:npm/%40img/sharp-libvips-linuxmusl-arm64@1.3.2"),
    },
}
ARTIFACT_TOOLS = {
    "backend-trivy": "trivy", "backend-grype": "grype",
    "frontend-trivy": "trivy", "frontend-grype": "grype",
    "backend-sbom": "trivy-cyclonedx", "frontend-sbom": "trivy-cyclonedx",
    "backend-cpython-regressions": "cpython-regressions",
}
SARIF_DRIVERS = {"trivy": "Trivy", "grype": "grype"}


def frontend_openssl_is_acceptable(version: str) -> bool:
    return version == FRONTEND_RUNTIME_OPENSSL_VERSION and version not in {"3.6.0", "3.6.1", "3.6.2", "3.6.3"}


def frontend_inventory_matches(architecture: str, inventory: str) -> bool:
    bounds = FRONTEND_INVENTORY_RECORD_BOUNDS.get(architecture)
    match = FRONTEND_INVENTORY_PATTERN.match(inventory)
    return bool(bounds and match and bounds[0] <= int(match["records"]) <= bounds[1])


def require_frontend_inventory(architecture: str, inventory: str) -> None:
    if not frontend_inventory_matches(architecture, inventory):
        raise SystemExit(
            f"Frontend runtime inventory is not reviewed: architecture={architecture} inventory={inventory}"
        )


def canonical_frontend_config(config: dict[str, Any]) -> dict[str, Any] | None:
    normalized = dict(config)
    for field, expected in FRONTEND_ENGINE_CONFIG_DEFAULTS.items():
        if field in normalized:
            actual = normalized.pop(field)
            if type(actual) is not type(expected) or actual != expected:
                return None
    return normalized


def _digest(value: Any) -> tuple[str, int]:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _add(findings: list[str], code: str) -> None:
    if code not in findings:
        findings.append(code)


def _valid_sarif_report(report: Any, expected_tool: str) -> bool:
    if not isinstance(report, dict) or report.get("version") != "2.1.0":
        return False
    runs = report.get("runs")
    if not isinstance(runs, list) or len(runs) != 1 or not isinstance(runs[0], dict):
        return False
    run = runs[0]
    driver = run.get("tool", {}).get("driver", {}) if isinstance(run.get("tool"), dict) else {}
    results = run.get("results")
    if not isinstance(driver, dict) or driver.get("name") != SARIF_DRIVERS.get(expected_tool):
        return False
    if not isinstance(results, list) or any(not isinstance(result, dict) for result in results):
        return False
    rules = driver.get("rules")
    if rules is None and expected_tool == "grype" and not results:
        rules = []
    if not isinstance(rules, list) or any(not isinstance(rule, dict) for rule in rules):
        return False
    rule_ids = [rule.get("id") for rule in rules]
    if any(not isinstance(rule_id, str) or not rule_id for rule_id in rule_ids):
        return False
    if len(rule_ids) != len(set(rule_ids)):
        return False
    rules_by_id = dict(zip(rule_ids, rules, strict=True))
    for result in results:
        rule_id = result.get("ruleId")
        if not isinstance(rule_id, str) or rule_id not in rules_by_id:
            return False
        properties = rules_by_id[rule_id].get("properties")
        if not isinstance(properties, dict):
            return False
        severity_value = properties.get("security-severity")
        if isinstance(severity_value, bool) or not isinstance(severity_value, (str, int, float)):
            return False
        try:
            severity = float(severity_value)
        except (TypeError, ValueError):
            return False
        if not math.isfinite(severity) or not 0.0 <= severity <= 10.0:
            return False
    return True


def _sarif_results(report: dict[str, Any]) -> list[tuple[str, float, str]]:
    result_ids: list[tuple[str, float, str]] = []
    for run in report["runs"]:
        rules = {rule.get("id"): rule for rule in run.get("tool", {}).get("driver", {}).get("rules") or []}
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "")
            rule = rules.get(rule_id, {})
            properties = rule.get("properties", {})
            purls = properties.get("purls") or [properties.get("purl", "")]
            cve = rule_id if rule_id in TARGET_CVES else str(rule.get("helpUri", "")).rsplit("/", 1)[-1]
            result_ids.append((cve if cve in TARGET_CVES else rule_id, float(properties.get("security-severity", 10.0)), purls[0] if isinstance(purls, list) and purls else ""))
    return result_ids


def _valid_envelope(name: str, envelope: Any, target: Any, architecture: Any) -> bool:
    if not isinstance(envelope, dict) or not isinstance(target, str) or not isinstance(architecture, str):
        return False
    tool = ARTIFACT_TOOLS[name]
    exit_code = envelope.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        return False
    artifact_path = envelope.get("artifact_path")
    suffix = ".raw.sarif.json" if name.endswith(("trivy", "grype")) else ".raw.json"
    if not isinstance(artifact_path, str) or artifact_path.startswith("/"):
        return False
    path = PurePosixPath(artifact_path)
    if ".." in path.parts or path.name != f"{name}{suffix}":
        return False
    allowed_exit_codes = (0,) if name.startswith("frontend-") or name not in ARTIFACTS[:4] else ((0, 2) if tool == "grype" else (0, 1))
    return (
        envelope.get("schema_version") == "ContainerScanEvidenceV1"
        and envelope.get("name") == name
        and envelope.get("tool") == tool
        and envelope.get("argv") == [tool, target]
        and exit_code in allowed_exit_codes
    )


def _valid_envelope_time(envelope: Any, now: float) -> bool:
    if not isinstance(envelope, dict):
        return False
    started_at, completed_at = envelope.get("started_at"), envelope.get("completed_at")
    if isinstance(started_at, bool) or not isinstance(started_at, (int, float)):
        return False
    if isinstance(completed_at, bool) or not isinstance(completed_at, (int, float)):
        return False
    return bool(now - 720 <= started_at <= completed_at <= now)


def _valid_vex(vex: dict[str, Any], backend_config: str, component_purl: str) -> bool:
    return vex == {
        "status": "fixed",
        "product": f"urn:narratwin-ai:docker-config:{backend_config}",
        "component": component_purl,
        "vulnerabilities": list(TARGET_CVES),
    }


def _package_identities(component: dict[str, Any]) -> set[str]:
    identities = {str(component.get("name", "")).casefold()}
    for field in ("purl", "bom-ref"):
        value = str(component.get(field, ""))
        if value.startswith("pkg:"):
            identities.add(
                unquote(urlsplit(value).path).rsplit("/", 1)[-1].split("@", 1)[0].casefold()
            )
    cpe = str(component.get("cpe", ""))
    if cpe.startswith("cpe:2.3:") and len(cpe.split(":")) > 4:
        identities.add(unquote(cpe.split(":")[4]).casefold())
    for prop in component.get("properties", []):
        if not isinstance(prop, dict):
            continue
        name, value = prop.get("name"), str(prop.get("value", ""))
        if name == "aquasecurity:trivy:PkgID":
            identities.add(value.split("@", 1)[0].casefold())
        elif name == "aquasecurity:trivy:SrcName":
            identities.add(value.casefold())
    return identities


def _valid_cyclonedx_sbom(report: dict[str, Any], target: str, required: dict[str, tuple[str, tuple[str, ...], str, str]], architecture: str) -> bool:
    metadata = report.get("metadata", {}).get("component", {})
    components = report.get("components")
    if (report.get("bomFormat"), report.get("specVersion"), metadata.get("type")) != ("CycloneDX", "1.7", "container") or not isinstance(components, list) or not 0 < len(components) <= 5000 or any(not isinstance(component, dict) for component in components):
        return False
    image_ids = {p.get("value") for p in metadata.get("properties", []) if isinstance(p, dict) and p.get("name") == "aquasecurity:trivy:ImageID"}
    if image_ids != {target}:
        return False
    if required:
        for component in components:
            if _package_identities(component) & {"glibc", "gcompat"}:
                return False
        apk_components = [
            component for component in components
            if isinstance(component, dict) and str(component.get("purl", "")).startswith("pkg:apk/")
        ]
        if len(apk_components) != len(required) or {item.get("name") for item in apk_components} != set(required):
            return False
        expected_sharp = FRONTEND_SHARP_COMPONENTS.get(architecture)
        sharp_components = [
            component for component in components
            if any(identity == "sharp" or identity.startswith("sharp-")
                   for identity in _package_identities(component))
        ]
        actual_sharp = {
            (str(component.get("name", "")), str(component.get("version", "")), str(component.get("purl", "")))
            for component in sharp_components
        }
        if expected_sharp is None or len(sharp_components) != len(expected_sharp) or actual_sharp != expected_sharp:
            return False
    expected_arch = {"amd64": "x86_64", "arm64": "aarch64"}.get(architecture)
    for name, (version, expected_licenses, namespace, distro) in required.items():
        matches = [c for c in components if isinstance(c, dict) and c.get("name") == name]
        if len(matches) != 1:
            return False
        component = matches[0]
        licenses = {x.get("expression") or x.get("license", {}).get("id") for x in component.get("licenses", []) if isinstance(x, dict)}
        try:
            purl = urlsplit(str(component.get("purl", "")))
            qualifiers = parse_qs(purl.query, strict_parsing=True)
        except ValueError:
            return False
        if (component.get("type"), component.get("version"), purl.scheme, purl.path, qualifiers, licenses) != ("library", version, "pkg", f"apk/{namespace}/{quote(name, safe='')}@{version}", {"arch": [expected_arch], "distro": [distro]}, set(expected_licenses)):
            return False
    return True


def frontend_reproduction_findings(primary: dict[str, Any], reproduction: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if primary.get("buildId") != reproduction.get("buildId"):
        findings.append("FRONTEND_BUILD_ID_CHANGED")
    primary_inventory = primary.get("inventory")
    reproduction_inventory = reproduction.get("inventory")
    primary_architecture = primary.get("architecture")
    reproduction_architecture = reproduction.get("architecture")
    inventories_are_reviewed = primary_architecture == reproduction_architecture and all(
        isinstance(value, str) and frontend_inventory_matches(str(record.get("architecture", "")), value)
        for record, value in ((primary, primary_inventory), (reproduction, reproduction_inventory))
    )
    if not inventories_are_reviewed:
        findings.append("FRONTEND_RUNTIME_INVENTORY_INVALID")
    elif primary_inventory != reproduction_inventory:
        findings.append("FRONTEND_RUNTIME_INVENTORY_CHANGED")
    primary_secrets = {primary.get(field) for field in FRONTEND_SECRET_FIELDS}
    reproduction_secrets = {reproduction.get(field) for field in FRONTEND_SECRET_FIELDS}
    if primary_secrets & reproduction_secrets:
        findings.append("FRONTEND_BUILD_SECRET_REUSED")
    return findings


def evaluate_consensus(
    *,
    expected_session: str,
    now: float,
    image_identity: dict[str, Any],
    component_purl: str,
    patch_manifest: dict[str, Any],
    reports: dict[str, Any],
    envelopes: dict[str, Any],
    vex_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    findings: list[str] = []
    raw_artifacts: dict[str, dict[str, Any]] = {}
    backend_config = image_identity.get("backend", {}).get("config_digest")
    frontend_config = image_identity.get("frontend", {}).get("config_digest")

    for name in ARTIFACTS:
        if name not in reports or name not in envelopes:
            _add(findings, "SCANNER_REPORT_MISSING")
    if findings:
        return {"status": "fail", "fixed": [], "findings": findings}

    for name in ARTIFACTS:
        envelope = envelopes[name]
        identity = image_identity.get("backend" if name.startswith("backend") else "frontend", {})
        target = backend_config if name.startswith("backend") else frontend_config
        digest, size = _digest(reports[name])
        raw_artifacts[name] = {"sha256": digest, "size": size}
        if envelope.get("session") != expected_session:
            _add(findings, "SCAN_SESSION_INVALID")
        if envelope.get("target") != target or envelope.get("config_digest") != target:
            _add(findings, "IMAGE_IDENTITY_INVALID")
        if envelope.get("architecture") != identity.get("architecture"):
            _add(findings, "IMAGE_IDENTITY_INVALID")
        if not _valid_envelope(name, envelope, target, identity.get("architecture")):
            _add(findings, "SCANNER_EXECUTION_INVALID")
        if not _valid_envelope_time(envelope, now):
            _add(findings, "SCAN_SESSION_INVALID")
        if envelope.get("artifact_sha256") != digest or envelope.get("artifact_size") != size:
            _add(findings, "ARTIFACT_INTEGRITY_INVALID")

    if "IMAGE_IDENTITY_INVALID" in findings:
        return {"status": "fail", "fixed": [], "findings": findings, "artifacts": list(ARTIFACTS), "raw_artifacts": raw_artifacts}

    if not _valid_cyclonedx_sbom(reports["backend-sbom"], backend_config, {}, str(image_identity.get("backend", {}).get("architecture", ""))):
        _add(findings, "SBOM_EVIDENCE_INVALID")
    if not _valid_cyclonedx_sbom(
        reports["frontend-sbom"], frontend_config, FRONTEND_SBOM_COMPONENTS,
        str(image_identity.get("frontend", {}).get("architecture", "")),
    ):
        _add(findings, "SBOM_EVIDENCE_INVALID")

    expected_manifest = {
        "schema_version": "CPythonSecurityBackportsV1",
        "base_image": BASE_IMAGE,
        "patch_sha256": PATCH_SHA256,
    }
    if patch_manifest != expected_manifest:
        _add(findings, "PATCH_EVIDENCE_INVALID")

    regression = reports["backend-cpython-regressions"]
    if regression.get("status") != "pass" or regression.get("config_digest") != backend_config:
        _add(findings, "REGRESSION_INVALID")
    if regression.get("patch_sha256") != PATCH_SHA256:
        _add(findings, "PATCH_EVIDENCE_INVALID")
    for cve in TARGET_CVES:
        if regression.get("checks", {}).get(cve, {}).get("status") != "pass":
            _add(findings, "REGRESSION_INVALID")

    valid_sarif: set[str] = set()
    for name in ARTIFACTS[:4]:
        if _valid_sarif_report(reports[name], ARTIFACT_TOOLS[name]):
            valid_sarif.add(name)
        else:
            _add(findings, "SCANNER_REPORT_MALFORMED")
    if "backend-grype" in valid_sarif and len(reports["backend-grype"]["runs"][0]["results"]) > 1000:
        _add(findings, "REPORT_RESOURCE_LIMIT")
    for name in ARTIFACTS[:4]:
        if "TOKEN-SECRET" in json.dumps(reports[name]):
            _add(findings, "SECRET_DISCLOSURE")
    for name in ("backend-trivy", "backend-grype", "frontend-trivy", "frontend-grype"):
        if name not in valid_sarif:
            continue
        for rule_id, severity, purl in _sarif_results(reports[name]):
            if name.startswith("backend") and rule_id in TARGET_CVES and purl == component_purl:
                continue
            elif name.startswith("frontend") and rule_id and severity >= 4.0:
                _add(findings, "FRONTEND_RUNTIME_MEDIUM_OR_HIGHER")
            elif rule_id and severity >= 7.0:
                _add(findings, "UNRELATED_HIGH_CRITICAL")

    vex = vex_override or {
        "status": "fixed",
        "product": f"urn:narratwin-ai:docker-config:{backend_config}",
        "component": component_purl,
        "vulnerabilities": list(TARGET_CVES),
    }
    if not _valid_vex(vex, backend_config, component_purl):
        _add(findings, "VEX_BOUNDARY_INVALID")

    return {"status": "pass" if not findings else "fail", "fixed": list(TARGET_CVES) if not findings else [], "findings": findings, "artifacts": list(ARTIFACTS), "raw_artifacts": raw_artifacts, "vex": vex}


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=Path)
    parser.add_argument("--verify-frontend-reproduction", action="store_true")
    args = parser.parse_args()
    if args.verify_frontend_reproduction:
        primary, reproduction = (json.loads(sys.stdin.readline()) for _ in range(2))
        findings = frontend_reproduction_findings(primary, reproduction)
        print(json.dumps({"status": "fail" if findings else "pass", "findings": findings}))
        return 1 if findings else 0
    if args.case is None:
        parser.error("--case is required unless verifying frontend reproduction")
    case = _load_json(args.case)
    case["now"] = time.time()
    result = evaluate_consensus(**case)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
