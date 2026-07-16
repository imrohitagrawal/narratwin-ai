from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest


ROOT = Path(__file__).resolve().parents[2]
TARGET_CVES = ("CVE-2026-11940", "CVE-2026-11972", "CVE-2026-15308")
BACKEND_CONFIG = "sha256:" + "a" * 64
FRONTEND_CONFIG = "sha256:" + "b" * 64
SESSION = "issue151-" + "c" * 32
NOW = 2_000_000_000.0
PATCH_SHA256 = {
    "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
}
ARTIFACTS = ("backend-trivy", "backend-grype", "frontend-trivy", "frontend-grype", "backend-sbom", "frontend-sbom", "backend-cpython-regressions")


def _load() -> ModuleType:
    path = ROOT / "scripts/ci/check_container_scan_consensus.py"
    assert path.is_file(), "missing issue-151 scanner-consensus implementation"
    spec = importlib.util.spec_from_file_location("issue151_consensus", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(value: Any) -> tuple[str, int]:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def _sarif(tool: str, cves: tuple[str, ...] = TARGET_CVES, severity: str = "8.0") -> dict[str, Any]:
    rules = [{"id": cve, "properties": {"purl": "pkg:generic/python@3.13.14", "security-severity": severity}} for cve in cves]
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": tool, "rules": rules}}, "results": [{"ruleId": cve} for cve in cves]}]}


def _envelope(name: str, payload: dict[str, Any], target: str, tool: str) -> dict[str, Any]:
    digest, size = _digest(payload)
    db = [{"path": "db/vulnerability.db", "size": 4, "sha256": "d" * 64}]
    db_hash = _digest(db)[0]
    return {
        "schema_version": "ContainerScanEvidenceV1", "name": name, "session": SESSION, "tool": tool,
        "argv": ["scanner", target], "artifact_path": f"reports/security/{name}.raw.json", "target": target,
        "config_digest": target, "architecture": "amd64", "rootfs": ["sha256:" + "f" * 64],
        "started_at": NOW - 120, "completed_at": NOW - 60, "database_updated_at": NOW - 3600,
        "database_next_update": NOW + 3600, "database_manifest_before": db, "database_manifest_after": copy.deepcopy(db),
        "database_manifest_before_sha256": db_hash, "database_manifest_after_sha256": db_hash,
        "artifact_sha256": digest, "artifact_size": size, "exit_code": 0,
    }


def _case() -> dict[str, Any]:
    reports: dict[str, Any] = {
        "backend-trivy": _sarif("trivy", ()),
        "backend-grype": _sarif("grype"),
        "frontend-trivy": _sarif("trivy", ()),
        "frontend-grype": _sarif("grype", ()),
        "backend-sbom": {"sbom": "cyclonedx", "target": BACKEND_CONFIG},
        "frontend-sbom": {"sbom": "cyclonedx", "target": FRONTEND_CONFIG},
        "backend-cpython-regressions": {"status": "pass", "config_digest": BACKEND_CONFIG, "patch_sha256": PATCH_SHA256, "checks": {c: {"status": "pass", "seconds": 0.01} for c in TARGET_CVES}},
    }
    envelopes = {
        name: _envelope(name, reports[name], BACKEND_CONFIG if name.startswith("backend") else FRONTEND_CONFIG, name.split("-", 1)[1])
        for name in ARTIFACTS
    }
    return {
        "expected_session": SESSION, "now": NOW,
        "image_identity": {"backend": {"config_digest": BACKEND_CONFIG, "architecture": "amd64", "rootfs": ["sha256:" + "f" * 64]}, "frontend": {"config_digest": FRONTEND_CONFIG, "architecture": "amd64", "rootfs": ["sha256:" + "f" * 64]}},
        "component_purl": "pkg:generic/python@3.13.14",
        "patch_manifest": {"schema_version": "CPythonSecurityBackportsV1", "base_image": "docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0", "patch_sha256": PATCH_SHA256},
        "reports": reports,
        "envelopes": envelopes,
    }


def _rehash(case: dict[str, Any], name: str) -> None:
    digest, size = _digest(case["reports"][name])
    case["envelopes"][name]["artifact_sha256"] = digest
    case["envelopes"][name]["artifact_size"] = size


def _evaluate(case: dict[str, Any]) -> dict[str, Any]:
    return _load().evaluate_consensus(**case)


def test_fixed_cve_case_is_green_with_exact_vex_and_all_raw_artifacts() -> None:
    case = _case()
    result = _evaluate(case)
    assert result["findings"] == []
    assert result["fixed"] == list(TARGET_CVES)
    assert result["artifacts"] == list(ARTIFACTS)
    assert sorted(result["raw_artifacts"]) == sorted(ARTIFACTS)
    assert result["vex"] == {
        "status": "fixed",
        "product": f"urn:narratwin-ai:docker-config:{BACKEND_CONFIG}",
        "component": "pkg:generic/python@3.13.14",
        "vulnerabilities": list(TARGET_CVES),
    }


@pytest.mark.parametrize(
    "mutation,expected,rehash",
    [
        (lambda c: c.update(expected_session="wrong"), ["SCAN_SESSION_INVALID"], True),
        (lambda c: c["reports"].pop("backend-grype"), ["SCANNER_REPORT_MISSING"], False),
        (lambda c: c["envelopes"]["backend-grype"].update(target="python:3.13-alpine"), ["IMAGE_IDENTITY_INVALID"], True),
        (lambda c: c["envelopes"]["backend-trivy"].update(started_at=NOW - 721), ["SCAN_SESSION_INVALID"], True),
        (lambda c: c["envelopes"]["backend-trivy"].update(database_updated_at=NOW - 172801), ["DATABASE_STALE"], True),
        (lambda c: c["envelopes"]["backend-grype"].update(database_manifest_after=[]), ["DATABASE_INTEGRITY_INVALID"], True),
        (lambda c: c["envelopes"]["backend-grype"].update(artifact_sha256="0" * 64), ["ARTIFACT_INTEGRITY_INVALID"], False),
        (lambda c: c["patch_manifest"].update(schema_version="bad"), ["PATCH_EVIDENCE_INVALID"], True),
        (lambda c: c["reports"]["backend-cpython-regressions"].update(status="fail"), ["REGRESSION_INVALID"], True),
        (lambda c: c["reports"]["backend-grype"]["runs"][0]["results"].append({"ruleId": "CVE-OTHER"}), ["UNRELATED_HIGH_CRITICAL"], True),
    ],
)
def test_single_faults_fail_closed(mutation: Callable[[dict[str, Any]], None], expected: list[str], rehash: bool) -> None:
    baseline = _case()
    assert _evaluate(copy.deepcopy(baseline))["findings"] == []
    candidate = copy.deepcopy(baseline)
    mutation(candidate)
    if rehash:
        for name in ARTIFACTS:
            if name in candidate["reports"] and name in candidate["envelopes"]:
                _rehash(candidate, name)
    assert _evaluate(candidate)["findings"] == expected


def test_medium_unrelated_findings_do_not_hide_high_policy() -> None:
    case = _case()
    case["reports"]["frontend-grype"] = _sarif("grype", ("CVE-MEDIUM",), "6.5")
    _rehash(case, "frontend-grype")
    assert _evaluate(case)["findings"] == []
    case["reports"]["frontend-grype"] = _sarif("grype", ("CVE-HIGH",), "7.0")
    _rehash(case, "frontend-grype")
    assert _evaluate(case)["findings"] == ["UNRELATED_HIGH_CRITICAL"]


@pytest.mark.parametrize(
    "vex",
    [
        {"status": "not_affected", "product": f"urn:narratwin-ai:docker-config:{BACKEND_CONFIG}", "component": "pkg:generic/python@3.13.14", "vulnerabilities": list(TARGET_CVES)},
        {"status": "fixed", "product": f"urn:narratwin-ai:docker-config:{BACKEND_CONFIG}", "component": "pkg:generic/python@3.13.13", "vulnerabilities": list(TARGET_CVES)},
        {"status": "fixed", "product": f"urn:narratwin-ai:docker-config:{FRONTEND_CONFIG}", "component": "pkg:generic/python@3.13.14", "vulnerabilities": list(TARGET_CVES)},
        {"status": "fixed", "product": f"urn:narratwin-ai:docker-config:{BACKEND_CONFIG}", "component": "pkg:generic/python@3.13.14", "vulnerabilities": ["CVE-OTHER"]},
    ],
)
def test_vex_is_exact_fixed_status_backend_component_and_three_cves(vex: dict[str, Any]) -> None:
    case = _case()
    case["vex_override"] = vex
    assert _evaluate(case)["findings"] == ["VEX_BOUNDARY_INVALID"]


def test_wrapper_runs_both_scanners_and_persists_all_raw_and_envelope_artifacts(tmp_path: Path) -> None:
    log = tmp_path / "scan.log"
    for name in ("trivy", "grype"):
        (tmp_path / name).write_text(
            "#!/bin/sh\n"
            f"echo {name} \"$@\" >> \"$SCAN_FAKE_LOG\"\n"
            "out=''\nfor arg in \"$@\"; do case \"$arg\" in --output) shift ;; sarif=*) out=\"${arg#sarif=}\" ;; esac; done\n"
            "[ -n \"$out\" ] || while [ \"$#\" -gt 0 ]; do [ \"$1\" = '--output' ] && { shift; out=\"$1\"; }; shift || true; done\n"
            "echo '{\"version\":\"2.1.0\",\"runs\":[]}' > \"$out\"\n",
            encoding="utf-8",
        )
        (tmp_path / name).chmod(0o755)
    reports = tmp_path / "reports"
    reports.mkdir()
    completed = subprocess.run(
        [str(ROOT / "scripts/ci/docker-image-scan.sh")],
        cwd=ROOT,
        env={"PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}", "SCAN_FAKE_LOG": str(log), "REPORT_DIR": str(reports), "BACKEND_IMAGE": BACKEND_CONFIG, "FRONTEND_IMAGE": FRONTEND_CONFIG, "SKIP_POLICY_EVALUATION": "1"},
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    calls = log.read_text(encoding="utf-8")
    assert calls.count("trivy image") == 2 and calls.count("grype ") == 2
    assert all((reports / f"{name}.envelope.json").is_file() for name in ARTIFACTS)
    assert all((reports / f"{name}.raw.sarif.json").is_file() for name in ARTIFACTS[:4])
    assert all((reports / f"{name}.raw.json").is_file() for name in ARTIFACTS[4:])
