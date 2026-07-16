from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from collections.abc import Callable
from typing import Any, cast

import pytest


ROOT = Path(__file__).resolve().parents[2]
SECURITY = ROOT / "security/cpython-3.13.14"
BASE_IMAGE = "docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
COMMITS = (
    ("CVE-2026-11972", "3f031d431f80668e14f3bc066bbf4369cd9281b9", "Lib/tarfile.py"),
    ("CVE-2026-11940", "771d12dda5140313db0ac550292987975651bbde", "Lib/tarfile.py"),
    ("CVE-2026-15308", "7933f4bf7131aa4140750f9404f5de0aa2969ced", "Lib/html/parser.py"),
)
AFTER = (
    "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
)


def _load(path: Path, name: str) -> ModuleType:
    assert path.is_file(), f"missing issue-151 implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((SECURITY / "backports.json").read_text(encoding="utf-8")))


def _set(data: dict[str, Any], path: tuple[Any, ...], value: Any) -> dict[str, Any]:
    changed = copy.deepcopy(data)
    node: Any = changed
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return changed


def test_manifest_binds_exact_base_platforms_commits_paths_and_hash_chain() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == "CPythonSecurityBackportsV1"
    assert manifest["base"]["image"] == BASE_IMAGE
    assert manifest["base"]["python"] == "3.13.14"
    assert manifest["base"]["platform_digests"] == {"linux/amd64": "sha256:c25cdd83c6d9613de985ca971f41913c039f8f4d448c3058fd17c7f5f00a36be", "linux/arm64": "sha256:051506d858e750104f80a63465684f260ce2eeb220a24446a56f5ecc1609ecc8"}
    assert [(p["cve"], p["commit"], p["path"], p["after_sha256"]) for p in manifest["patches"]] == [
        (*item, after) for item, after in zip(COMMITS, AFTER)
    ]
    assert [p["before_sha256"] for p in manifest["patches"]] == [
        manifest["base"]["file_sha256"]["Lib/tarfile.py"],
        AFTER[0],
        manifest["base"]["file_sha256"]["Lib/html/parser.py"],
    ]
    assert all(p["old"] and p["new"] for p in manifest["patches"])


@pytest.mark.parametrize(
    "path,value",
    [
        (("schema_version",), "bad"), (("base", "image"), "python:3.13-alpine"),
        (("base", "platform_digests", "linux/amd64"), "sha256:" + "0" * 64), (("patches", 0, "cve"), "CVE-TEST"),
        (("patches", 1, "commit"), "a" * 40), (("patches", 2, "path"), "Lib/ssl.py"),
        (("patches", 2, "after_sha256"), "c" * 64), (("patches", 0, "old"), ""), (("patches", 1, "new"), ""),
    ],
)
def test_manifest_validation_rejects_single_tamper(path: tuple[Any, ...], value: Any) -> None:
    module = _load(SECURITY / "apply_backports.py", "issue151_backports")
    baseline = _manifest()
    assert module.validate_manifest(copy.deepcopy(baseline)) == baseline
    with pytest.raises(module.BackportError):
        module.validate_manifest(_set(baseline, path, value))


def test_manifest_validation_rejects_missing_extra_or_reordered_patches() -> None:
    module = _load(SECURITY / "apply_backports.py", "issue151_backports_order")
    baseline = _manifest()
    for patches in (baseline["patches"][:2], baseline["patches"] + [baseline["patches"][0]], list(reversed(baseline["patches"]))):
        with pytest.raises(module.BackportError):
            module.validate_manifest({**baseline, "patches": patches})


def test_applier_rejects_arbitrary_manifest_and_base_mismatch_without_partial_write(tmp_path: Path) -> None:
    module = _load(SECURITY / "apply_backports.py", "issue151_backports_apply")
    target = tmp_path / "Lib/example.py"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    with pytest.raises(module.BackportError):
        module.apply_backports(tmp_path, {"patches": [{"cve": "CVE-TEST", "path": "Lib/example.py"}]})
    for path in ("Lib/tarfile.py", "Lib/html/parser.py"):
        file_path = tmp_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("not-the-pinned-base\n", encoding="utf-8")
    with pytest.raises(module.BackportError):
        module.apply_backports(tmp_path, _manifest())
    assert target.read_text(encoding="utf-8") == "before\n"


def test_runtime_regression_cli_is_bounded_and_probe_entrypoint_fails_closed() -> None:
    script = ROOT / "scripts/ci/verify-cpython-backports.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--expect", "fixed", "--max-seconds", "2"],
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )
    evidence = json.loads(completed.stdout)
    assert completed.returncode in (0, 1)
    assert sorted(evidence["checks"]) == sorted(cve for cve, _, _ in COMMITS)
    assert evidence["maximum_seconds"] < 2
    module = _load(script, "issue151_regression_module")
    calls: list[str] = []

    def passing_probe(name: str) -> Callable[[], bool]:
        def probe() -> bool:
            calls.append(name)
            return True

        return probe

    probes = {name: passing_probe(name) for name in module.CHECK_TO_CVE}
    assert module.run_regressions(expect="fixed", max_seconds=2.0, probes=probes)["status"] == "pass"
    assert calls == list(module.CHECK_TO_CVE)
    probes["streaming_tar_terminates"] = lambda: False
    assert module.run_regressions(expect="fixed", max_seconds=2.0, probes=probes)["status"] == "fail"


def test_dockerfile_copies_verified_backport_files_into_final_runtime() -> None:
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    assert "FROM " + BASE_IMAGE + " AS cpython-backports" in dockerfile
    assert "apply_backports.py" in dockerfile and "verify-cpython-backports.py" in dockerfile
    assert "COPY --from=cpython-backports /usr/local/lib/python3.13/tarfile.py /usr/local/lib/python3.13/tarfile.py" in dockerfile
    assert "COPY --from=cpython-backports /usr/local/lib/python3.13/html/parser.py /usr/local/lib/python3.13/html/parser.py" in dockerfile
    assert "curl " not in dockerfile and "wget " not in dockerfile and "ADD https://" not in dockerfile
