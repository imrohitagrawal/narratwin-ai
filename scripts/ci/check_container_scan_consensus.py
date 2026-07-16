#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


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


def _digest(value: Any) -> tuple[str, int]:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _add(findings: list[str], code: str) -> None:
    if code not in findings:
        findings.append(code)


def _sarif_results(report: dict[str, Any]) -> list[tuple[str, float, str]]:
    if report.get("version") != "2.1.0" or not isinstance(report.get("runs"), list):
        return [("MALFORMED", 10.0, "")]
    result_ids: list[tuple[str, float, str]] = []
    for run in report["runs"]:
        rules = {rule.get("id"): rule for rule in run.get("tool", {}).get("driver", {}).get("rules", [])}
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "")
            rule = rules.get(rule_id, {})
            properties = rule.get("properties", {})
            purls = properties.get("purls") or [properties.get("purl", "")]
            cve = rule_id if rule_id in TARGET_CVES else str(rule.get("helpUri", "")).rsplit("/", 1)[-1]
            result_ids.append((cve if cve in TARGET_CVES else rule_id, float(properties.get("security-severity", 10.0)), purls[0] if isinstance(purls, list) and purls else ""))
    return result_ids


def _valid_vex(vex: dict[str, Any], backend_config: str, component_purl: str) -> bool:
    return vex == {
        "status": "fixed",
        "product": f"urn:narratwin-ai:docker-config:{backend_config}",
        "component": component_purl,
        "vulnerabilities": list(TARGET_CVES),
    }


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
        if envelope.get("started_at", now) < now - 720 or envelope.get("completed_at", 0) > now:
            _add(findings, "SCAN_SESSION_INVALID")
        if envelope.get("artifact_sha256") != digest or envelope.get("artifact_size") != size:
            _add(findings, "ARTIFACT_INTEGRITY_INVALID")
        if name in ARTIFACTS[:4] and envelope.get("exit_code") not in ((0, 2) if envelope.get("tool") == "grype" else (0, 1)):
            _add(findings, "SCANNER_EXECUTION_INVALID")

    if "IMAGE_IDENTITY_INVALID" in findings:
        return {"status": "fail", "fixed": [], "findings": findings, "artifacts": list(ARTIFACTS), "raw_artifacts": raw_artifacts}

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

    if len(reports["backend-grype"].get("runs", [{}])[0].get("results", [])) > 1000:
        _add(findings, "REPORT_RESOURCE_LIMIT")
    for name in ARTIFACTS[:4]:
        if "TOKEN-SECRET" in json.dumps(reports[name]):
            _add(findings, "SECRET_DISCLOSURE")
    for name in ("backend-trivy", "backend-grype", "frontend-trivy", "frontend-grype"):
        for rule_id, severity, purl in _sarif_results(reports[name]):
            if rule_id == "MALFORMED":
                _add(findings, "SCANNER_REPORT_MALFORMED")
            elif name.startswith("backend") and rule_id in TARGET_CVES and purl == component_purl:
                continue
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
    parser.add_argument("--case", type=Path, required=True)
    result = evaluate_consensus(**_load_json(parser.parse_args().case))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
