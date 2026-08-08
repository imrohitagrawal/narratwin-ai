from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest


ROOT = Path(__file__).resolve().parents[2]
ISSUE403_BASE = "246042d82483e0d84c74a5d5c9736a72c710e369"
NANOID_PATH = "node_modules/nanoid"
NANOID_INTEGRITY = (
    "sha512-xQLf0A3HOMlgHq0n247/LRuAOYmB7dXJ/DvAxGvsSBij45XtBSmQycu+"
    "F8ODbHwns/XyFZagyL1+J0Offw1E0g=="
)


def _base_text(path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ISSUE403_BASE}:{path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


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
        "3.3.17",
        "https://registry.npmjs.org/nanoid/-/nanoid-3.3.17.tgz",
        NANOID_INTEGRITY,
    )
    base_nanoid = base_lock["packages"][NANOID_PATH]
    assert {key: value for key, value in nanoid.items() if key not in {"version", "resolved", "integrity"}} == {
        key: value for key, value in base_nanoid.items() if key not in {"version", "resolved", "integrity"}
    }
    normalized = copy.deepcopy(lock)
    normalized["packages"][NANOID_PATH] = base_nanoid
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
        version="3.3.17",
        resolved="https://registry.npmjs.org/nanoid/-/nanoid-3.3.17.tgz",
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
    direct.setdefault("dependencies", {})["nanoid"] = "3.3.17"
    mutations.extend(((package_text, drifted), (json.dumps(direct), patched)))
    for candidate_package, candidate_lock in mutations:
        with pytest.raises(AssertionError):
            _assert_nanoid_contract(candidate_package, candidate_lock)
