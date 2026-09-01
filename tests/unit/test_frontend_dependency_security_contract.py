from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest


ROOT = Path(__file__).resolve().parents[2]
ISSUE403_BASE = "a02286240212ad8958915aec01aa5ebaf60fa705"
NANOID_PATH = "node_modules/nanoid"
NANOID_INTEGRITY = "sha512-DTg4MJbGMWkfi6VZFdNt2/caMbQy4Ou+Op/hJQvGEWcnVfoA1QA+xzRKAzw9jD6+GVOOeYr/mIcuDSdug6F6+w=="
ISSUE495_FRONTEND_PACKAGES = {
    "baseline-browser-mapping": ("2.11.20", "sha512-H0ulySigv6icDJ1F7SjtdCD6PrhTpdYCmP0CactWy1+ekh0AFd0o1Wn5T8b+hnTmdBx19u9yhL6wvCylXMY7zw=="),
    "browserslist": ("4.28.8", "sha512-V2NpofLblG64mfOtSgDhOJESZEGogzDMBv/q+W6oc4LXWP/q75eOXoOaaOu1EOadB9U4Bwx/e0yzbvwKH8zalA=="),
    "caniuse-lite": ("1.0.30001810", "sha512-TITQPUkaz+aVk5GL6NhOdwk1aEaNTSDPsGFWrTuhKGtjTF70jL/Oht2W4c6rXUe5fu7Ie19VIahAXHIIiWWNeg=="),
    "electron-to-chromium": ("1.5.419", "sha512-nHMPn8x4yCxCI0iSnL+LlHL5sUoUfjLXkcRIagZ4GBdrfFLFaiLNvzJWbJqZhFT9IAhw5tUSNlhggWN+otvp/A=="),
    "node-releases": ("2.0.54", "sha512-YHs7BmmcsdAI5Ozuf8JZo6PT0mv2GIWC9vMfvUC3dp65M8hn7Ux8CPL+2oBI7juNuj9d0ndhTcznq2ODBps9cQ=="),
    "update-browserslist-db": ("1.3.2", "sha512-UQ+MSxlhRm1bzjhU+DcuXfjFO1FzNtqhK5+9Yvlp90ItDLk5vT932A0rFu619nf7RVS+Y/VeaUW1jaRDqZ8VJw=="),
}


def _base_text(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ISSUE403_BASE}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def _normalize_issue495_delta(lock: dict[str, Any], base_lock: dict[str, Any]) -> None:
    for name, (version, integrity) in ISSUE495_FRONTEND_PACKAGES.items():
        path = f"node_modules/{name}"
        record = lock["packages"][path]
        assert (record["version"], record["resolved"], record["integrity"]) == (
            version,
            f"https://registry.npmjs.org/{name}/-/{name}-{version}.tgz",
            integrity,
        )
        lock["packages"][path] = base_lock["packages"][path]


def _assert_nanoid_contract(package_text: str, lock: dict[str, Any]) -> None:
    base_package = _base_text("frontend/package.json")
    base_lock = cast(dict[str, Any], json.loads(_base_text("frontend/package-lock.json")))
    assert package_text == base_package
    package = json.loads(package_text)
    for section in ("dependencies", "devDependencies", "optionalDependencies", "overrides"):
        assert "nanoid" not in package.get(section, {})

    assert [path for path in lock["packages"] if path.endswith(NANOID_PATH)] == [NANOID_PATH]
    nanoid = lock["packages"][NANOID_PATH]
    assert (nanoid["version"], nanoid["resolved"], nanoid["integrity"]) == (
        "3.3.18",
        "https://registry.npmjs.org/nanoid/-/nanoid-3.3.18.tgz",
        NANOID_INTEGRITY,
    )
    base_nanoid = base_lock["packages"][NANOID_PATH]
    assert {key: value for key, value in nanoid.items() if key not in {"version", "resolved", "integrity"}} == {
        key: value for key, value in base_nanoid.items() if key not in {"version", "resolved", "integrity"}
    }
    normalized = copy.deepcopy(lock)
    normalized["packages"][NANOID_PATH] = base_nanoid
    _normalize_issue495_delta(normalized, base_lock)
    assert normalized == base_lock


def test_frontend_nanoid_lock_is_exact_isolated_transitive_and_patched() -> None:
    _assert_nanoid_contract(
        (ROOT / "frontend/package.json").read_text(encoding="utf-8"),
        json.loads((ROOT / "frontend/package-lock.json").read_text(encoding="utf-8")),
    )


def test_nanoid_contract_rejects_identity_integrity_direct_dependency_and_drift() -> None:
    package_text = _base_text("frontend/package.json")
    base_lock = cast(dict[str, Any], json.loads(_base_text("frontend/package-lock.json")))
    patched = copy.deepcopy(base_lock)
    patched["packages"][NANOID_PATH].update(
        version="3.3.18",
        resolved="https://registry.npmjs.org/nanoid/-/nanoid-3.3.18.tgz",
        integrity=NANOID_INTEGRITY,
    )
    mutations: list[tuple[str, dict[str, Any]]] = []
    for field, value in (("version", "3.3.16"), ("resolved", "https://example.invalid/nanoid.tgz"),
                         ("integrity", "sha512-wrong")):
        candidate = copy.deepcopy(patched)
        candidate["packages"][NANOID_PATH][field] = value
        mutations.append((package_text, candidate))
    drifted = copy.deepcopy(patched)
    drifted["packages"]["node_modules/ms"]["version"] = "0.0.0"
    direct = json.loads(package_text)
    direct.setdefault("dependencies", {})["nanoid"] = "3.3.18"
    mutations.extend(((package_text, drifted), (json.dumps(direct), patched)))
    for candidate_package, candidate_lock in mutations:
        with pytest.raises(AssertionError):
            _assert_nanoid_contract(candidate_package, candidate_lock)
