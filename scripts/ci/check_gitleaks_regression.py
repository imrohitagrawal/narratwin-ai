#!/usr/bin/env python3
"""Validate the exact reviewed Gitleaks fingerprints and their provenance."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FROZEN_BASE = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
SOURCE_HEAD = "570239effbcae3990a24ffdc809622f02364ff0d"
SCAN_HEAD = "9644296da92bf3b3f373cd2afd2c7a64d6ca7c8c"
PORTABLE_PUBLIC_KEY_HEAD = "d0da128657ed3acdb0c33fc29f4028c702ac52ab"
EXPECTED_DIGEST = "910259f61acbbec4e3432c482d821fd56f2fe8b2073211c7ce112c3cd87405bf"
EXPECTED_PUBLIC_KEY_SHA256 = "6c3b7674b58d9f7266cd8b823ecf469b0a03d1bf2c8c24df1d0121d8e818f1fa"
EXPECTED_DOCKERFILE_SHA256 = "27a75b496a53f07037bceadd7eb57ebdf3e07112df33bb554e674925b9e9dc16"
EXPECTED_PORTABLE_DOCKERFILE_SHA256 = (
    "0e0f46b06a73eee744bcf94e730a0170b43783388bfe496c2f0f1ee5a171e2d8"
)
EXPECTED_FINGERPRINTS = (
    "77ebfc3218a003a06f7b43098624c30f2b43bf4e:scripts/quality/stage8_cut1_routes.py:generic-api-key:514",
    "8dd002589d45b41205a80dc004e7e6480bec901f:scripts/quality/stage8_cut1_routes.py:generic-api-key:515",
    "8dd002589d45b41205a80dc004e7e6480bec901f:tests/unit/test_stage8_cut1_routes.py:generic-api-key:1370",
    "9644296da92bf3b3f373cd2afd2c7a64d6ca7c8c:scripts/quality/stage8_cut1_routes.py:generic-api-key:509",
    "66dabedecdce4ed51b8354e44f2d1c749c209898:backend/Dockerfile:generic-api-key:18",
    "0cea00fd0a2cda457473c4fccf1d6ab2b2250bae:backend/Dockerfile:generic-api-key:18",
    "dd1e2118dede2b5cf9060d69cace0a3c9ab8ae4c:backend/Dockerfile:generic-api-key:18",
)
PUBLIC_KEY_FINGERPRINTS = frozenset(EXPECTED_FINGERPRINTS[-3:])


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


def validate_public_signing_key_blob(blob: bytes) -> list[str]:
    """Prove the reviewed value is a public source-verification key, not a secret."""
    failures: list[str] = []
    if hashlib.sha256(blob).hexdigest() != EXPECTED_DOCKERFILE_SHA256:
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_BLOB")
    try:
        lines = blob.decode("utf-8").splitlines()
        assignment = lines[17].strip()
        match = re.match(r"python_gpg_key=([A-F0-9]{40}); \\\Z", assignment)
        key = match.group(1) if match else ""
        receive = lines[18].strip()
        verify = lines[19].strip()
    except (IndexError, UnicodeError):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_LINE")
        return failures
    if (
        not match
        or hashlib.sha256(key.encode("ascii")).hexdigest()
        != EXPECTED_PUBLIC_KEY_SHA256
    ):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_LINE")
    if (
        receive
        != 'gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$python_gpg_key"; \\'
        or verify != "gpg --batch --verify python.tar.xz.asc python.tar.xz; \\"
    ):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_CONTEXT")
    return failures


def validate_portable_public_signing_key_blob(blob: bytes) -> list[str]:
    """Prove a reachable immutable snapshot uses the value as a public key."""
    failures: list[str] = []
    if hashlib.sha256(blob).hexdigest() != EXPECTED_PORTABLE_DOCKERFILE_SHA256:
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_BLOB")
    try:
        lines = blob.decode("utf-8").splitlines()
        assignment = lines[17].strip()
        match = re.match(r"python_gpg_fingerprint=([A-F0-9]{40}); \\\Z", assignment)
        key = match.group(1) if match else ""
        receive = lines[18].strip()
        verify = lines[19].strip()
    except (IndexError, UnicodeError):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_LINE")
        return failures
    if (
        not match
        or hashlib.sha256(key.encode("ascii")).hexdigest()
        != EXPECTED_PUBLIC_KEY_SHA256
    ):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_LINE")
    if (
        receive
        != 'gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$python_gpg_fingerprint"; \\'
        or verify != "gpg --batch --verify python.tar.xz.asc python.tar.xz; \\"
    ):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_CONTEXT")
    return failures


def _validate_portable_public_key_provenance(root: Path) -> list[str]:
    head = _git(root, "cat-file", "-e", f"{PORTABLE_PUBLIC_KEY_HEAD}^{{commit}}")
    ancestor = _git(
        root, "merge-base", "--is-ancestor", PORTABLE_PUBLIC_KEY_HEAD, "HEAD"
    )
    if head.returncode != 0 or ancestor.returncode != 0:
        return ["GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_HISTORY"]
    try:
        blob = _blob(root, PORTABLE_PUBLIC_KEY_HEAD, "backend/Dockerfile")
    except (OSError, subprocess.SubprocessError, RuntimeError):
        return ["GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_SNAPSHOT"]
    return validate_portable_public_signing_key_blob(blob)


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

    public_key_availability = {
        fingerprint: _git(
            root,
            "cat-file",
            "-e",
            f"{fingerprint.split(':', 1)[0]}^{{commit}}",
        ).returncode
        == 0
        for fingerprint in PUBLIC_KEY_FINGERPRINTS
    }
    if any(public_key_availability.values()) and not all(
        public_key_availability.values()
    ):
        _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_TOPOLOGY")

    portable_public_key_checked = False
    for fingerprint in EXPECTED_FINGERPRINTS:
        commit, path, rule, line_text = fingerprint.rsplit(":", 3)
        if fingerprint in PUBLIC_KEY_FINGERPRINTS:
            if not public_key_availability[fingerprint]:
                if not portable_public_key_checked:
                    failures.extend(_validate_portable_public_key_provenance(root))
                    portable_public_key_checked = True
                continue
            try:
                blob_bytes = _blob(root, commit, path)
                line = blob_bytes.decode("utf-8").splitlines()[int(line_text) - 1]
            except (
                IndexError,
                OSError,
                UnicodeError,
                ValueError,
                subprocess.SubprocessError,
                RuntimeError,
            ):
                _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_SNAPSHOT")
                continue
            failures.extend(validate_public_signing_key_blob(blob_bytes))
            if rule != "generic-api-key" or not line.strip().startswith(
                "python_gpg_key="
            ):
                _append_once(failures, "GITLEAKS.PROVENANCE.PUBLIC_KEY_LINE")
            continue
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
