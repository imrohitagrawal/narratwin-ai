"""Fail-closed contract for the three reviewed Gitleaks false positives."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/ci/check_gitleaks_regression.py"
FROZEN_BASE = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
SOURCE_HEAD = "570239effbcae3990a24ffdc809622f02364ff0d"
EXPECTED_DIGEST = "910259f61acbbec4e3432c482d821fd56f2fe8b2073211c7ce112c3cd87405bf"
EXPECTED_FINGERPRINTS = (
    "77ebfc3218a003a06f7b43098624c30f2b43bf4e:scripts/quality/stage8_cut1_routes.py:generic-api-key:514",
    "8dd002589d45b41205a80dc004e7e6480bec901f:scripts/quality/stage8_cut1_routes.py:generic-api-key:515",
    "8dd002589d45b41205a80dc004e7e6480bec901f:tests/unit/test_stage8_cut1_routes.py:generic-api-key:1370",
)


def _load_checker() -> ModuleType:
    assert CHECKER.is_file(), "Gitleaks regression checker is required"
    spec = importlib.util.spec_from_file_location("gitleaks_regression_under_test", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_reviewed_fingerprints_and_provenance_pass() -> None:
    checker = _load_checker()
    assert checker.FROZEN_BASE == FROZEN_BASE
    assert checker.SOURCE_HEAD == SOURCE_HEAD
    assert checker.EXPECTED_DIGEST == EXPECTED_DIGEST
    assert checker.EXPECTED_FINGERPRINTS == EXPECTED_FINGERPRINTS
    assert checker.validate(ROOT) == []


@pytest.mark.parametrize(
    "candidate",
    (
        EXPECTED_FINGERPRINTS[1:],
        (*EXPECTED_FINGERPRINTS, "wildcard:*"),
        (EXPECTED_FINGERPRINTS[0].replace("77ebfc32", "87ebfc32"), *EXPECTED_FINGERPRINTS[1:]),
        (EXPECTED_FINGERPRINTS[0].replace("stage8_cut1_routes.py", "other.py"), *EXPECTED_FINGERPRINTS[1:]),
        (EXPECTED_FINGERPRINTS[0].replace("generic-api-key", "private-key"), *EXPECTED_FINGERPRINTS[1:]),
        (EXPECTED_FINGERPRINTS[0].replace(":514", ":515"), *EXPECTED_FINGERPRINTS[1:]),
    ),
)
def test_ignore_contract_rejects_omission_addition_and_fingerprint_drift(
    candidate: tuple[str, ...],
) -> None:
    checker = _load_checker()
    assert checker.validate_ignore_lines(candidate) == ["GITLEAKS.IGNORE.EXACT"]


def test_frozen_api_contract_bytes_match_the_reviewed_digest() -> None:
    result = subprocess.run(
        ["git", "show", f"{FROZEN_BASE}:docs/API_CONTRACT.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert hashlib.sha256(result.stdout).hexdigest() == EXPECTED_DIGEST


def test_source_head_contains_each_finding_commit() -> None:
    for fingerprint in EXPECTED_FINGERPRINTS:
        commit = fingerprint.split(":", 1)[0]
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, SOURCE_HEAD],
            cwd=ROOT,
            check=False,
        )
        assert completed.returncode == 0


def test_security_wrapper_runs_contract_canary_and_full_history_scan() -> None:
    text = (ROOT / "scripts/ci/dependency-security.sh").read_text(encoding="utf-8")
    assert "python3 scripts/ci/check_gitleaks_regression.py" in text
    assert "gitleaks stdin" in text
    assert "gitleaks detect --redact --source ." in text
