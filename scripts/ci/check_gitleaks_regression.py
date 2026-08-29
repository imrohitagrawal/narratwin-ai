#!/usr/bin/env python3
"""Validate the exact reviewed Gitleaks fingerprints and their provenance."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FROZEN_BASE = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
SOURCE_HEAD = "570239effbcae3990a24ffdc809622f02364ff0d"
SCAN_HEAD = "9644296da92bf3b3f373cd2afd2c7a64d6ca7c8c"
EXPECTED_DIGEST = "910259f61acbbec4e3432c482d821fd56f2fe8b2073211c7ce112c3cd87405bf"
EXPECTED_FINGERPRINTS = (
    "77ebfc3218a003a06f7b43098624c30f2b43bf4e:scripts/quality/stage8_cut1_routes.py:generic-api-key:514",
    "8dd002589d45b41205a80dc004e7e6480bec901f:scripts/quality/stage8_cut1_routes.py:generic-api-key:515",
    "8dd002589d45b41205a80dc004e7e6480bec901f:tests/unit/test_stage8_cut1_routes.py:generic-api-key:1370",
    "9644296da92bf3b3f373cd2afd2c7a64d6ca7c8c:scripts/quality/stage8_cut1_routes.py:generic-api-key:509",
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["/usr/bin/git", *args],
        cwd=root,
        env={
            "PATH": "/usr/bin:/bin",
            "LC_ALL": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_LAZY_FETCH": "1",
        },
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )


def validate_ignore_lines(lines: tuple[str, ...]) -> list[str]:
    return [] if lines == EXPECTED_FINGERPRINTS else ["GITLEAKS.IGNORE.EXACT"]


def _append_once(failures: list[str], code: str) -> None:
    if code not in failures:
        failures.append(code)


def _read_ignore(root: Path, failures: list[str]) -> tuple[str, ...]:
    path = root / ".gitleaksignore"
    if not path.is_file() or path.is_symlink():
        _append_once(failures, "GITLEAKS.IGNORE.EXACT")
        return ()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _append_once(failures, "GITLEAKS.IGNORE.EXACT")
        return ()
    if not text.endswith("\n"):
        _append_once(failures, "GITLEAKS.IGNORE.EXACT")
    return tuple(text.splitlines())


def _blob(root: Path, ref: str, path: str) -> bytes:
    result = _git(root, "show", f"{ref}:{path}")
    if result.returncode != 0:
        raise RuntimeError("historical blob unavailable")
    return result.stdout


def validate(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    failures.extend(validate_ignore_lines(_read_ignore(root, failures)))

    try:
        api_contract = _blob(root, FROZEN_BASE, "docs/API_CONTRACT.md")
    except (OSError, subprocess.SubprocessError, RuntimeError):
        _append_once(failures, "GITLEAKS.PROVENANCE.SNAPSHOT")
    else:
        if hashlib.sha256(api_contract).hexdigest() != EXPECTED_DIGEST:
            _append_once(failures, "GITLEAKS.PROVENANCE.DIGEST")

    history = (_git(root, "cat-file", "-e", f"{head}^{{commit}}") for head in (SOURCE_HEAD, SCAN_HEAD))
    if any(result.returncode != 0 for result in history):
        _append_once(failures, "GITLEAKS.PROVENANCE.HISTORY")

    for fingerprint in EXPECTED_FINGERPRINTS:
        commit, path, rule, line_text = fingerprint.rsplit(":", 3)
        ancestor = _git(root, "merge-base", "--is-ancestor", commit, SCAN_HEAD)
        if ancestor.returncode != 0:
            _append_once(failures, "GITLEAKS.PROVENANCE.HISTORY")
            continue
        try:
            blob = _blob(root, commit, path).decode("utf-8")
            line = blob.splitlines()[int(line_text) - 1]
        except (IndexError, OSError, UnicodeError, ValueError, subprocess.SubprocessError, RuntimeError):
            _append_once(failures, "GITLEAKS.PROVENANCE.SNAPSHOT")
            continue
        if rule != "generic-api-key" or "API_CONTRACT.md" not in line or EXPECTED_DIGEST not in line:
            _append_once(failures, "GITLEAKS.PROVENANCE.LINE")

    return failures


def main() -> int:
    failures = validate()
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("Exact Gitleaks fingerprint regression contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
