from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, cast

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


def _sarif(tool: str, cves: tuple[str, ...] = TARGET_CVES, severity: str = "8.0", purl: str = "pkg:generic/python@3.13.14") -> dict[str, Any]:
    rules = [{"id": f"{cve}-python" if tool == "grype" else cve, "helpUri": f"https://nvd.nist.gov/vuln/detail/{cve}", "properties": {"purls": [purl], "security-severity": severity}} for cve in cves]
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": tool, "rules": rules}}, "results": [{"ruleId": rule["id"]} for rule in rules]}]}


def _sbom(target: str, *, frontend: bool) -> dict[str, Any]:
    packages = (("nodejs-26", "26.7.0-r0", "MIT"), ("npm-12", "12.0.2-r2", "Artistic-2.0")) if frontend else (("python", "3.13.14", "PSF-2.0"),)
    components = [{"type": "library", "name": name, "version": version, "purl": f"pkg:apk/wolfi/{name}@{version}?arch=x86_64&distro=20230201", "licenses": [{"license": {"id": license_id}}]} for name, version, license_id in packages]
    return {"bomFormat": "CycloneDX", "specVersion": "1.7", "metadata": {"component": {"type": "container", "properties": [{"name": "aquasecurity:trivy:ImageID", "value": target}]}}, "components": components}


def _envelope(name: str, payload: dict[str, Any], target: str, tool: str) -> dict[str, Any]:
    digest, size = _digest(payload)
    return {
        "schema_version": "ContainerScanEvidenceV1", "name": name, "session": SESSION, "tool": tool,
        "argv": ["scanner", target], "artifact_path": f"reports/security/{name}.raw.json", "target": target,
        "config_digest": target, "architecture": "amd64",
        "started_at": NOW - 120, "completed_at": NOW - 60, "artifact_sha256": digest, "artifact_size": size, "exit_code": 0,
    }


def _case() -> dict[str, Any]:
    reports: dict[str, Any] = {
        "backend-trivy": _sarif("trivy"),
        "backend-grype": _sarif("grype"),
        "frontend-trivy": _sarif("trivy", ()),
        "frontend-grype": _sarif("grype", ()),
        "backend-sbom": _sbom(BACKEND_CONFIG, frontend=False),
        "frontend-sbom": _sbom(FRONTEND_CONFIG, frontend=True),
        "backend-cpython-regressions": {"status": "pass", "config_digest": BACKEND_CONFIG, "patch_sha256": PATCH_SHA256, "checks": {c: {"status": "pass", "seconds": 0.01} for c in TARGET_CVES}},
    }
    envelopes = {
        name: _envelope(name, reports[name], BACKEND_CONFIG if name.startswith("backend") else FRONTEND_CONFIG, name.split("-", 1)[1])
        for name in ARTIFACTS
    }
    return {
        "expected_session": SESSION, "now": NOW,
        "image_identity": {"backend": {"config_digest": BACKEND_CONFIG, "architecture": "amd64"}, "frontend": {"config_digest": FRONTEND_CONFIG, "architecture": "amd64"}},
        "component_purl": "pkg:generic/python@3.13.14",
        "patch_manifest": {"schema_version": "CPythonSecurityBackportsV1", "base_image": "docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0", "patch_sha256": PATCH_SHA256},
        "reports": reports, "envelopes": envelopes,
    }


def _rehash(case: dict[str, Any], name: str) -> None:
    digest, size = _digest(case["reports"][name])
    case["envelopes"][name]["artifact_sha256"] = digest
    case["envelopes"][name]["artifact_size"] = size


def _evaluate(case: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _load().evaluate_consensus(**case))


def test_fixed_cve_case_is_green_with_exact_vex_and_all_raw_artifacts() -> None:
    case = _case()
    result = _evaluate(case)
    assert result["findings"] == [] and result["fixed"] == list(TARGET_CVES)
    assert result["artifacts"] == list(ARTIFACTS) and sorted(result["raw_artifacts"]) == sorted(ARTIFACTS)
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
        (lambda c: c["envelopes"]["backend-trivy"].update(architecture="s390x"), ["IMAGE_IDENTITY_INVALID"], True),
        (lambda c: c["envelopes"]["backend-grype"].update(exit_code=3), ["SCANNER_EXECUTION_INVALID"], True),
        (lambda c: c["envelopes"]["backend-trivy"].update(started_at=NOW - 721), ["SCAN_SESSION_INVALID"], True),
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


def test_frontend_runtime_medium_findings_fail_closed() -> None:
    case = _case()
    case["reports"]["frontend-grype"] = _sarif("grype", ("CVE-MEDIUM",), "6.5")
    _rehash(case, "frontend-grype")
    assert _evaluate(case)["findings"] == ["FRONTEND_RUNTIME_MEDIUM_OR_HIGHER"]
    case["reports"]["frontend-grype"] = _sarif("grype", ("CVE-HIGH",), "7.0")
    _rehash(case, "frontend-grype")
    assert _evaluate(case)["findings"] == ["FRONTEND_RUNTIME_MEDIUM_OR_HIGHER"]


def test_issue389_npm12_findings_fail_consensus() -> None:
    case = _case()
    for cve, severity in (("CVE-2026-69152","8.2"), ("CVE-2026-69192","8.1"), ("CVE-2026-69198","6.5")):
        case["reports"]["frontend-grype"] = _sarif("grype", (cve,), severity)
        _rehash(case, "frontend-grype")
        assert _evaluate(case)["findings"] == ["FRONTEND_RUNTIME_MEDIUM_OR_HIGHER"]


@pytest.mark.parametrize("mutation", [lambda s:s.clear(), lambda s:s.update(components=[]),
    lambda s:s["metadata"]["component"]["properties"][0].update(value="sha256:"+"0"*64),
    lambda s:s["components"][0].update(version="26.6.0-r0"), lambda s:s["components"][1].update(version="12.0.2-r1"),
    lambda s:s["components"][1].update(licenses=[{"license":{"id":"MIT"}}]),
    lambda s:s["components"][0].update(purl="pkg:apk/wolfi/nodejs-26@26.7.0-r0"),
    lambda s:s["components"][0].update(purl="pkg:apk/wolfi/nodejs-26@26.7.0-r0?arch=evil&distro=ubuntu"),
    lambda s:s["components"][0].update(purl="pkg:apk/wolfi/nodejs-26@26.7.0-r0?arch=x86_64&arch=aarch64&distro=20230201"),
    lambda s:s["components"][0].update(purl="pkg:apk/wolfi/nodejs-26@26.7.0-r0?arch=x86_64&distro=20230201&foreign=yes")])
def test_frontend_sbom_identity_packages_and_licenses_fail_closed(mutation: Callable[[dict[str, Any]], None]) -> None:
    sbom = _sbom(FRONTEND_CONFIG, frontend=True)
    mutation(sbom)
    module = _load()
    assert not module._valid_cyclonedx_sbom(sbom, FRONTEND_CONFIG, module.FRONTEND_SBOM_COMPONENTS, "amd64")


def test_backend_medium_findings_retain_the_existing_high_policy() -> None:
    case = _case()
    case["reports"]["backend-grype"] = _sarif("grype", ("CVE-MEDIUM",), "6.5")
    _rehash(case, "backend-grype")
    assert _evaluate(case)["findings"] == []


def test_frontend_reproduction_requires_stable_build_id_and_fresh_secrets() -> None:
    validator = _load().frontend_reproduction_findings
    primary = {
        "buildId": "source-bound",
        "architecture": "amd64",
        "inventory": "1805:80a0ba0401cf0710ca3179727644965433e4b3a199dd0c81cc60f7938df71de0",
        "previewModeId": "1" * 32,
        "previewModeSigningKey": "2" * 64,
        "previewModeEncryptionKey": "3" * 64,
        "serverActionKey": "A" * 43 + "=",
    }
    reproduction = {
        "buildId": "source-bound",
        "architecture": "amd64",
        "inventory": primary["inventory"],
        "previewModeId": "4" * 32,
        "previewModeSigningKey": "5" * 64,
        "previewModeEncryptionKey": "6" * 64,
        "serverActionKey": "B" * 43 + "=",
    }
    assert validator(primary, reproduction) == []
    reproduction["inventory"] = "1805:" + "0" * 64
    assert validator(primary, reproduction) == ["FRONTEND_RUNTIME_INVENTORY_INVALID"]
    reproduction["inventory"] = primary["inventory"]
    for bad_inventory in (None, "", "unreviewed"):
        malformed_primary = {**primary, "inventory": bad_inventory}
        malformed_reproduction = {**reproduction, "inventory": bad_inventory}
        assert validator(malformed_primary, malformed_reproduction) == ["FRONTEND_RUNTIME_INVENTORY_INVALID"]
    wrong_arch_primary = {**primary, "inventory": "1803:1b00f69f5326e4466b69a49078231110e1ca5027ec25f8a215cf8e7aebb39587"}
    wrong_arch_reproduction = {**reproduction, "inventory": wrong_arch_primary["inventory"]}
    assert validator(wrong_arch_primary, wrong_arch_reproduction) == ["FRONTEND_RUNTIME_INVENTORY_INVALID"]
    reproduction["previewModeSigningKey"] = primary["previewModeEncryptionKey"]
    reproduction["previewModeEncryptionKey"] = primary["previewModeSigningKey"]
    assert validator(primary, reproduction) == ["FRONTEND_BUILD_SECRET_REUSED"]
    reproduction["previewModeSigningKey"] = "5" * 64
    reproduction["previewModeEncryptionKey"] = "6" * 64
    assert validator(primary, primary) == ["FRONTEND_BUILD_SECRET_REUSED"]
    reproduction["buildId"] = "changed"
    reproduction["serverActionKey"] = primary["serverActionKey"]
    assert validator(primary, reproduction) == [
        "FRONTEND_BUILD_ID_CHANGED",
        "FRONTEND_BUILD_SECRET_REUSED",
    ]


def test_frontend_reproduction_inventory_rejection_survives_optimized_python() -> None:
    primary = {"buildId": "stable", "architecture": "amd64", "previewModeId": "1", "previewModeSigningKey": "2", "previewModeEncryptionKey": "3", "serverActionKey": "4"}
    reproduction = {**primary, "previewModeId": "5", "previewModeSigningKey": "6", "previewModeEncryptionKey": "7", "serverActionKey": "8"}
    completed = subprocess.run(
        [sys.executable, "-O", str(ROOT / "scripts/ci/check_container_scan_consensus.py"), "--verify-frontend-reproduction"],
        cwd=ROOT,
        input=f"{json.dumps(primary)}\n{json.dumps(reproduction)}\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert json.loads(completed.stdout)["findings"] == ["FRONTEND_RUNTIME_INVENTORY_INVALID"]


def test_runtime_inventory_orchestration_preserves_failures_and_distinct_values(tmp_path: Path) -> None:
    source = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    start = source.index('if [ "${SKIP_POLICY_EVALUATION:-0}" != "1" ]; then')
    block = source[start : source.index("\nfi", start) + 3]
    log = tmp_path / "reproduction.log"
    harness = f'''set -euo pipefail
prepare_frontend_images() {{ :; }}
verify_frontend_runtime() {{ false; printf -v "${{2:-ignored}}" %s "$1-inventory"; }}
verify_frontend_reproducibility() {{ printf '%s\n' "$@" >"$LOG"; }}
{block}
'''
    env = {**os.environ, "LOG": str(log), "FRONTEND_IMAGE": "primary:tag", "FRONTEND_REPRO_IMAGE": "repro:tag"}
    failed = subprocess.run(["bash"], input=harness, env=env, text=True, check=False)
    assert failed.returncode != 0
    harness = harness.replace("verify_frontend_runtime() { false;", "verify_frontend_runtime() { :;")
    passed = subprocess.run(["bash"], input=harness, env=env, text=True, check=False)
    assert passed.returncode == 0
    assert log.read_text().splitlines() == ["primary:tag", "repro:tag", "primary:tag-inventory", "repro:tag-inventory"]


def test_frontend_config_accepts_only_exact_host_engine_defaults() -> None:
    canonicalize = _load().canonical_frontend_config
    application_config = {"User": "65532:65532", "Cmd": ["server.js"]}
    engine_defaults = {
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
    assert canonicalize(application_config) == application_config
    assert canonicalize({**application_config, **engine_defaults}) == application_config
    for key, expected in engine_defaults.items():
        mutation = {**application_config, **engine_defaults}
        mutation[key] = not expected if isinstance(expected, bool) else "unexpected"
        assert canonicalize(mutation) is None
        if isinstance(expected, bool):
            mutation[key] = 0
            assert canonicalize(mutation) is None
    assert canonicalize({**application_config, "Unexpected": False}) == {
        **application_config,
        "Unexpected": False,
    }


@pytest.mark.parametrize("optimize", [None, "1"])
def test_frontend_config_rejection_does_not_disclose_untrusted_values(
    optimize: str | None,
) -> None:
    source = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    start = source.index("verify_frontend_runtime() {")
    function = source[start : source.index("\n}\n\nfrontend_build_identity()", start) + 3]
    marker = "UNTRUSTED-MARKER-MUST-NOT-APPEAR"
    config = json.dumps({"Labels": {"untrusted": marker}, "Unexpected": marker})
    env = {**os.environ, "MALICIOUS_CONFIG": config}
    if optimize:
        env["PYTHONOPTIMIZE"] = optimize
    completed = subprocess.run(
        ["bash"],
        cwd=ROOT,
        env=env,
        input=(
            "set -e\n"
            "docker() {\n"
            "  if [ \"$1\" = image ] && [ \"$2\" = inspect ]; then "
            "printf '%s\\n' \"$MALICIOUS_CONFIG\"; return; fi\n"
            "  return 97\n"
            "}\n"
            f"{function}\nverify_frontend_runtime image:tag\n"
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert marker not in output
    assert "Frontend runtime config does not match the reviewed contract." in output


def test_frontend_config_is_not_passed_in_python_argv(tmp_path: Path) -> None:
    source = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    start = source.index("verify_frontend_runtime() {")
    function = source[start : source.index("\n}\n\nfrontend_build_identity()", start) + 3]
    marker = "UNTRUSTED-ARGV-MARKER"
    argv_log = tmp_path / "argv.log"
    completed = subprocess.run(
        ["bash"],
        cwd=ROOT,
        env={**os.environ, "MALICIOUS_CONFIG": json.dumps({"Unexpected": marker}), "ARGV_LOG": str(argv_log)},
        input=(
            "set -e\n"
            "docker() { [ \"$1\" = image ] && printf '%s\\n' \"$MALICIOUS_CONFIG\"; }\n"
            "python3() { printf '%s\\n' \"$@\" >\"$ARGV_LOG\"; return 1; }\n"
            f"{function}\nverify_frontend_runtime image:tag\n"
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert marker not in argv_log.read_text(encoding="utf-8")


def test_frontend_inventory_contract_is_exact_and_architecture_bound() -> None:
    module = _load()
    matches = module.frontend_inventory_matches
    amd64 = "1805:80a0ba0401cf0710ca3179727644965433e4b3a199dd0c81cc60f7938df71de0"
    arm64 = "1803:1b00f69f5326e4466b69a49078231110e1ca5027ec25f8a215cf8e7aebb39587"
    assert module.FRONTEND_INVENTORIES == {
        "amd64": frozenset((amd64,)),
        "arm64": frozenset((arm64,)),
    }
    assert matches("amd64", amd64)
    assert matches("arm64", arm64)
    assert not matches("amd64", arm64)
    assert not matches("arm64", amd64)
    assert not matches("amd64", amd64[:-1] + "0")
    assert not matches("unknown", amd64)
    for stale in (
        "1805:1c078e196a032c50ff9ba7f1954c4da2501a4ad47364ac44665ac29aed8c86b2",
        "1803:e9a3cd116280dff5bd1e39833d511f9fa0eb952bbde5f0ffaf4aab0ab2306c9f",
        "1803:06e4628f15e836b24128401deedceedeaebe0561bef29f96f3c9de7e2306e3e0",
    ):
        assert not matches("amd64", stale)
        assert not matches("arm64", stale)


def test_frontend_inventory_rejection_survives_optimized_python() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-O",
            "-c",
            "from scripts.ci.check_container_scan_consensus import require_frontend_inventory; require_frontend_inventory('unknown', 'unreviewed')",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert completed.stderr.strip() == (
        "Frontend runtime inventory is not reviewed: architecture=unknown inventory=unreviewed"
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("FRONTEND_IMAGE", "FRONTEND_BUILD_IMAGE"),
        ("FRONTEND_IMAGE", "FRONTEND_REPRO_IMAGE"),
        ("FRONTEND_BUILD_IMAGE", "FRONTEND_REPRO_IMAGE"),
    ],
)
def test_container_scan_rejects_colliding_frontend_image_roles(tmp_path: Path, left: str, right: str) -> None:
    reports = tmp_path / "reports"
    env = {
        **os.environ,
        "REPORT_DIR": str(reports),
        "FRONTEND_IMAGE": "primary:tag",
        "FRONTEND_BUILD_IMAGE": "build:tag",
        "FRONTEND_REPRO_IMAGE": "repro:tag",
    }
    env[left] = env[right]
    completed = subprocess.run(
        [str(ROOT / "scripts/ci/docker-image-scan.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stderr == "Frontend image role references must be distinct.\n"


@pytest.mark.parametrize(("trivy_rc", "grype_rc"), [(0, 0), (1, 0), (0, 1)])
def test_dependency_scanners_bind_pre_reproduction_digest_and_fail_closed(
    tmp_path: Path, trivy_rc: int, grype_rc: int
) -> None:
    source = (ROOT / "scripts/ci/docker-image-scan.sh").read_text(encoding="utf-8")
    cleanup = 'rm -f "${REPORT_DIR}"/*.raw.json "${REPORT_DIR}"/*.raw.sarif.json'
    assert source.index(cleanup) < source.index("\n  prepare_frontend_images")
    start = source.index("prepare_frontend_images() {")
    function = source[start : source.index("\n}\n", start) + 3]
    log = tmp_path / "boundary.log"
    harness = f"""
docker() {{ printf 'docker:%s\\n' \"$*\" >>\"$LOG\"; }}
image_config() {{ printf 'sha256:dependency'; }}
scan_trivy() {{ printf 'trivy:%s\\n' \"$1\" >>\"$LOG\"; return \"$TRIVY_RC\"; }}
scan_grype() {{ printf 'grype:%s\\n' \"$1\" >>\"$LOG\"; return \"$GRYPE_RC\"; }}
{function}
prepare_frontend_images
"""
    env = {
        **os.environ,
        "LOG": str(log),
        "TRIVY_RC": str(trivy_rc),
        "GRYPE_RC": str(grype_rc),
        "FRONTEND_ARCH": "amd64",
        "FRONTEND_BUILD_IMAGE": "build:tag",
        "FRONTEND_REPRO_IMAGE": "repro:tag",
        "REPORT_DIR": str(tmp_path),
    }
    completed = subprocess.run(
        ["bash"], input=harness, env=env, text=True, capture_output=True, check=False
    )
    lines = log.read_text(encoding="utf-8").splitlines()
    if trivy_rc or grype_rc:
        assert completed.returncode != 0 and len(lines) == 3
    else:
        assert completed.returncode == 0
        assert "--target deps" in lines[0]
        assert lines[1:3] == ["trivy:sha256:dependency", "grype:sha256:dependency"]
        assert "--no-cache-filter build" in lines[3] and "repro:tag" in lines[3]


@pytest.mark.parametrize(
    "name,report",
    [
        ("backend-trivy", _sarif("trivy", ("CVE-2026-11940x",))),
        ("backend-grype", _sarif("grype", TARGET_CVES, purl="pkg:generic/other@1")),
        ("frontend-grype", _sarif("grype", TARGET_CVES)),
    ],
)
def test_fixed_cve_exception_requires_exact_backend_python_component(name: str, report: dict[str, Any]) -> None:
    case = _case()
    case["reports"][name] = report
    _rehash(case, name)
    expected = "FRONTEND_RUNTIME_MEDIUM_OR_HIGHER" if name.startswith("frontend") else "UNRELATED_HIGH_CRITICAL"
    assert _evaluate(case)["findings"] == [expected]


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
        env={"PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}", "SCAN_FAKE_LOG": str(log), "REPORT_DIR": str(reports), "BACKEND_IMAGE": BACKEND_CONFIG, "FRONTEND_IMAGE": FRONTEND_CONFIG, "BACKEND_ARCH": "amd64", "FRONTEND_ARCH": "amd64", "SKIP_POLICY_EVALUATION": "1"},
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    calls = log.read_text(encoding="utf-8")
    assert calls.count("trivy image") == 4 and calls.count("grype ") == 2
    assert calls.count("--format cyclonedx") == 2
    assert all((reports / f"{name}.envelope.json").is_file() for name in ARTIFACTS)
    assert all((reports / f"{name}.raw.sarif.json").is_file() for name in ARTIFACTS[:4])
    assert all((reports / f"{name}.raw.json").is_file() for name in ARTIFACTS[4:])


def test_dockerized_scanner_fallback_writes_to_mounted_report_path(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    reports = tmp_path / "reports"
    log = tmp_path / "docker.log"
    fake_bin.mkdir()
    reports.mkdir()
    (fake_bin / "docker").write_text(
        "#!/bin/sh\n"
        "echo \"$@\" >> \"$SCAN_FAKE_LOG\"\n"
        "host_reports=''\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = '-v' ]; then shift; case \"$1\" in *:/reports) host_reports=\"${1%:/reports}\" ;; esac; fi\n"
        "  shift || true\n"
        "done\n"
        "for arg in $(cat \"$SCAN_FAKE_LOG\"); do\n"
        "  case \"$arg\" in /reports/*) out=\"$host_reports/${arg#/reports/}\" ;; sarif=/reports/*) out=\"$host_reports/${arg#sarif=/reports/}\" ;; *) continue ;; esac\n"
        "  mkdir -p \"$(dirname \"$out\")\"\n"
        "  echo '{\"version\":\"2.1.0\",\"runs\":[]}' > \"$out\"\n"
        "done\n",
        encoding="utf-8",
    )
    (fake_bin / "docker").chmod(0o755)
    completed = subprocess.run(
        [str(ROOT / "scripts/ci/docker-image-scan.sh")],
        cwd=ROOT,
        env={"PATH": f"{fake_bin}{os.pathsep}/usr/bin:/bin:/usr/sbin:/sbin", "SCAN_FAKE_LOG": str(log), "REPORT_DIR": str(reports), "BACKEND_IMAGE": BACKEND_CONFIG, "FRONTEND_IMAGE": FRONTEND_CONFIG, "BACKEND_ARCH": "amd64", "FRONTEND_ARCH": "amd64", "SKIP_POLICY_EVALUATION": "1"},
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    calls = log.read_text(encoding="utf-8")
    assert "/reports/backend-trivy.raw.sarif.json" in calls
    assert "sarif=/reports/backend-grype.raw.sarif.json" in calls
    assert all((reports / f"{name}.raw.sarif.json").is_file() for name in ARTIFACTS[:4])
