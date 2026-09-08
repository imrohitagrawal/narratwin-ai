"""Fail-closed contract for the reviewed Gitleaks false positives."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Callable, cast

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/ci/check_gitleaks_regression.py"
FROZEN_BASE = "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
SOURCE_HEAD = "570239effbcae3990a24ffdc809622f02364ff0d"
SCAN_HEAD = "9644296da92bf3b3f373cd2afd2c7a64d6ca7c8c"
PORTABLE_PUBLIC_KEY_HEAD = "d0da128657ed3acdb0c33fc29f4028c702ac52ab"
MAPPING_COMMIT = "74dc7c9cb670513cd2340cbd686d66d1d24b819e"
MAPPING_FINGERPRINT = (
    f"{MAPPING_COMMIT}:docs/governance/superset-mapping-v2.json:generic-api-key:1474"
)
MAPPING_BLOB_SHA256 = "ba12b1be49884f3eba25e0d6459104ea2a21588c21785ab4bf90401b41df1b97"
MAPPING_LINE_SHA256 = "072c497736eac919ac45974581ff2efde3e6f19b85152bba2e526413037b77a7"
MAPPING_REQUIREMENT_ID = "MPV2-EF7B22C3CF4ED775DC94"
MAPPING_CLAUSE_SHA256 = "845855204badc3593c9f4e729d2395d4c443ab2f83771cb1731f7a560f3089c1"
CURRENT_MAPPING_REQUIREMENT_IDS = (
    "MPV2-6008E4EF304A86BC7BD3",
    "MPV2-BE434AE78F7511BC7812",
)
V1_BLOB_SHA256 = "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
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
    MAPPING_FINGERPRINT,
    "b18aeed00527dfa3e6a1f1df475cf67765a17ebb:scripts/ci/check_gitleaks_regression.py:generic-api-key:71",
    "b18aeed00527dfa3e6a1f1df475cf67765a17ebb:scripts/quality/issue521_master_program_v2.py:generic-api-key:133",
    "547333d283914004257ab0fde86a216a93ff3e17:tests/unit/test_issue521_master_program_v2.py:generic-api-key:232",
    "66dabedecdce4ed51b8354e44f2d1c749c209898:backend/Dockerfile:generic-api-key:18",
    "0cea00fd0a2cda457473c4fccf1d6ab2b2250bae:backend/Dockerfile:generic-api-key:18",
    "dd1e2118dede2b5cf9060d69cace0a3c9ab8ae4c:backend/Dockerfile:generic-api-key:18",
)
EXPECTED_PUBLIC_KEY_FINGERPRINTS = EXPECTED_FINGERPRINTS[-3:]
EXPECTED_G1_SYNTHETIC_LINE_SHA256 = ("55a3972a5dc31361c33adb0014aed8b52940e7f21823f51e89c13dce3090a5b2", "76dfcad75e98c853b91e1340db355d7545c15ced75b117a6e3e191568f765908", "e047a0a498befbda500f90e7be2766c967b996f42ccb9a15721d7998ab730246")


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
    assert checker.SCAN_HEAD == SCAN_HEAD
    assert checker.PORTABLE_PUBLIC_KEY_HEAD == PORTABLE_PUBLIC_KEY_HEAD
    assert checker.EXPECTED_DIGEST == EXPECTED_DIGEST
    assert checker.EXPECTED_PUBLIC_KEY_SHA256 == EXPECTED_PUBLIC_KEY_SHA256
    assert checker.EXPECTED_DOCKERFILE_SHA256 == EXPECTED_DOCKERFILE_SHA256
    assert (
        checker.EXPECTED_PORTABLE_DOCKERFILE_SHA256
        == EXPECTED_PORTABLE_DOCKERFILE_SHA256
    )
    assert checker.EXPECTED_FINGERPRINTS == EXPECTED_FINGERPRINTS
    assert checker.G1_SYNTHETIC_LINE_SHA256 == EXPECTED_G1_SYNTHETIC_LINE_SHA256
    assert checker.validate(ROOT) == []
def test_g1_synthetic_line_hash_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = _load_checker()
    monkeypatch.setattr(checker, "G1_SYNTHETIC_LINE_SHA256", ("0" * 64, *EXPECTED_G1_SYNTHETIC_LINE_SHA256[1:]))
    assert "GITLEAKS.PROVENANCE.G1_SYNTHETIC_LINE" in checker.validate(ROOT)


def test_public_signed_delivery_urls_fail_closed() -> None:
    checker = _load_checker()
    azure_sas = (b"https://account.blob.core.windows.net/private/object.mp4?sv=2026-01-01" b"&se=2026-09-09T00%3A00%3A00Z&sp=r&s" b"ig=synthetic-review-canary")
    encoded_separator = b"https://cdn.invalid/object?sp=r&s" b"ig%3Dsynthetic"
    serialized = (
        b"https://cdn.invalid/object?sp=r&amp;s" b"ig=synthetic",
        br"https:\/\/cdn.invalid\/object?X-Amz-Sig" br"nature=synthetic",
        b"https%3A%2F%2Fcdn.invalid%2Fobject%3FX-Goog-Signa"
        b"ture%3Dsynthetic",
        br"https:\/\/cdn.invalid\/object?sp=r\u0026s" br"ig=synthetic",
        b"https://cdn.invalid/object?to" b"ken=synthetic",
        b"https://cdn.invalid/object?cred" b"ential=synthetic",
        b"https://cdn.invalid/object?k" b"ey=synthetic",
        b"https://cdn.invalid/object?s&#" b"105;g=synthetic",
        b"http&#" b"115;://cdn.invalid/object?s" b"ig=synthetic",
        b"//cdn.invalid/object?s" b"ig=synthetic",
        b"https%25253A%25252F%25252Fcdn.invalid%25252Fobject%25253F" b"sig%25253Dsynthetic",
        br"\u0068ttps:\/\/cdn.invalid/?s" br"ig=synthetic", b"%252F%252Fcdn.invalid%253Fs" b"ig%253Dsynthetic",
    )
    for candidate in (azure_sas, encoded_separator, *serialized):
        assert checker.validate_public_blob(candidate) == ["GITLEAKS.PUBLIC.SIGNED_URL"]
    assert checker.validate_public_blob(b"https://docs.invalid/signature-policy") == []
    assert checker.validate_public_blob(b"https://docs.invalid/?signal=public") == []
    for candidate in (b"/Use" b"rs/synthetic/private-evidence", b"fi" b"le:///Use" b"rs/synthetic/private-evidence", b"/Use&#" b"114;s/synthetic/private-evidence", b"%25252FUse" b"rs%25252Fsynthetic"):
        assert checker.validate_public_blob(candidate) == ["GITLEAKS.PUBLIC.PRIVATE_PATH"]


def test_tracked_public_blob_scan_enforces_signed_url_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checker = _load_checker()
    (tmp_path / "public-artifact.txt").write_bytes(b"https://cdn.invalid/private.mp4?expires=1&s" b"ig=synthetic")
    monkeypatch.setattr(
        checker, "_git", lambda root, *args: subprocess.CompletedProcess(args, 0, b"public-artifact.txt\0", b""),
    )
    assert checker._validate_tracked_public_blobs(tmp_path) == ["GITLEAKS.PUBLIC.SIGNED_URL"]
    (tmp_path / "public-artifact.txt").unlink()
    (tmp_path / "public-artifact.txt").symlink_to("https://cdn.invalid/private.mp4?s" + "ig=synthetic")
    assert checker._validate_tracked_public_blobs(tmp_path) == ["GITLEAKS.PUBLIC.SIGNED_URL"]


def test_inherited_synthetic_private_path_is_not_a_new_public_leak(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    checker = _load_checker()
    inherited = b"/Use" b"rs/synthetic/base-fixture"
    target = tmp_path / "public-artifact.txt"
    target.write_bytes(inherited)

    def git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        del root
        return subprocess.CompletedProcess(args, 0, b"public-artifact.txt\0" if args[0] == "ls-files" else inherited, b"")

    monkeypatch.setattr(checker, "_git", git)
    assert checker._validate_tracked_public_blobs(tmp_path) == []
    target.write_bytes(b"/Use" b"rs/synthetic/new-private-evidence")
    assert checker._validate_tracked_public_blobs(tmp_path) == ["GITLEAKS.PUBLIC.PRIVATE_PATH"]


def test_mapping_governance_clause_provenance_is_exact() -> None:
    checker = _load_checker()
    mapping = subprocess.run(
        ["git", "show", f"{MAPPING_COMMIT}:docs/governance/superset-mapping-v2.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    source = subprocess.run(
        ["git", "show", f"{checker.MAPPING_SOURCE_COMMIT}:{checker.MAPPING_SOURCE_PATH}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert checker.MAPPING_COMMIT == MAPPING_COMMIT
    assert checker.MAPPING_BLOB_SHA256 == MAPPING_BLOB_SHA256
    assert checker.MAPPING_LINE_SHA256 == MAPPING_LINE_SHA256
    assert checker.MAPPING_REQUIREMENT_ID == MAPPING_REQUIREMENT_ID
    assert checker.MAPPING_CLAUSE_SHA256 == MAPPING_CLAUSE_SHA256
    assert checker.MAPPING_SOURCE_SHA256 == V1_BLOB_SHA256
    assert checker.validate_mapping_clause_blobs(mapping, source) == []


def test_mapping_clause_provenance_rejects_blob_line_row_and_source_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    mapping = subprocess.run(
        ["git", "show", f"{MAPPING_COMMIT}:docs/governance/superset-mapping-v2.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    source = subprocess.run(
        ["git", "show", f"{checker.MAPPING_SOURCE_COMMIT}:{checker.MAPPING_SOURCE_PATH}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert "GITLEAKS.PROVENANCE.MAPPING_BLOB" in checker.validate_mapping_clause_blobs(
        mapping + b"\n", source
    )
    changed_line = mapping.replace(MAPPING_REQUIREMENT_ID.encode(), b"MPV2-EF7B22C3CF4ED775DC95", 1)
    monkeypatch.setattr(checker, "MAPPING_BLOB_SHA256", hashlib.sha256(changed_line).hexdigest())
    assert "GITLEAKS.PROVENANCE.MAPPING_LINE" in checker.validate_mapping_clause_blobs(
        changed_line, source
    )
    lines = changed_line.splitlines(keepends=True)
    monkeypatch.setattr(checker, "MAPPING_LINE_SHA256", hashlib.sha256(lines[1473]).hexdigest())
    assert "GITLEAKS.PROVENANCE.MAPPING_ROW" in checker.validate_mapping_clause_blobs(
        changed_line, source
    )
    assert "GITLEAKS.PROVENANCE.MAPPING_SOURCE" in checker.validate_mapping_clause_blobs(
        mapping, source + b"\n"
    )


def test_squash_checkout_uses_portable_mapping_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    original_git = cast(Callable[..., subprocess.CompletedProcess[bytes]], checker._git)

    def hosted_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        if MAPPING_COMMIT in " ".join(args):
            return subprocess.CompletedProcess(args, 128, b"", b"missing")
        return original_git(root, *args)

    monkeypatch.setattr(checker, "_git", hosted_git)
    assert checker.validate(ROOT) == []


def test_portable_mapping_requires_one_exact_requirement_row() -> None:
    checker = _load_checker()
    mapping_blob = (ROOT / checker.MAPPING_PATH).read_bytes()
    mapping = json.loads(mapping_blob)
    rows = [
        item
        for item in checker._logical_mapping_rows(mapping)
        if item["requirementId"] in CURRENT_MAPPING_REQUIREMENT_IDS
    ]
    source = subprocess.run(
        ["git", "show", f"{checker.MAPPING_SOURCE_COMMIT}:{checker.MAPPING_SOURCE_PATH}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert tuple(
        item["requirementId"] for item in checker.CURRENT_MAPPING_ROWS
    ) == CURRENT_MAPPING_REQUIREMENT_IDS
    portable = json.dumps({"rows": rows}, separators=(",", ":")).encode()
    assert checker.validate_portable_mapping_blob(portable, source) == []
    duplicated = json.dumps(
        {"rows": [*rows, rows[0]]}, separators=(",", ":")
    ).encode()
    assert "GITLEAKS.PROVENANCE.MAPPING_PORTABLE_UNIQUE" in checker.validate_portable_mapping_blob(
        duplicated, source
    )
    changed = {**rows[0], "sourceAnchor": rows[0]["sourceAnchor"] + "-drift"}
    altered = json.dumps(
        {"rows": [changed, rows[1]]}, separators=(",", ":")
    ).encode()
    assert "GITLEAKS.PROVENANCE.MAPPING_PORTABLE_ROW" in checker.validate_portable_mapping_blob(
        altered, source
    )


def test_current_mapping_uses_semantics_preserving_atomic_serialization() -> None:
    checker = _load_checker()
    mapping_blob = (ROOT / checker.MAPPING_PATH).read_bytes()
    assert checker.validate_portable_mapping_encoding(mapping_blob) == []
    document = json.loads(mapping_blob)
    rows = {
        item["requirementId"]: item
        for item in checker._logical_mapping_rows(document)
        if item["requirementId"] in CURRENT_MAPPING_REQUIREMENT_IDS
    }
    assert set(rows) == set(CURRENT_MAPPING_REQUIREMENT_IDS)
    assert {
        rows[item["requirementId"]]["normalizedAtomicRequirement"]
        for item in checker.CURRENT_MAPPING_ROWS
    } == {
        item["normalizedAtomicRequirement"] for item in checker.CURRENT_MAPPING_ROWS
    }
    assert document["rowEncoding"]["derivedThresholdComparisonsSha256"] == checker.MAPPING_DERIVED_THRESHOLD_SHA256
    document["rowEncoding"]["derivedThresholdComparisonsSha256"] = "0" * 64
    with pytest.raises(ValueError):
        checker._logical_mapping_rows(document)


def test_available_history_does_not_skip_current_portable_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    called = {"historical": 0, "portable": 0}
    historical = checker.validate_mapping_clause_blobs
    portable = checker.validate_portable_mapping_blob

    def track_historical(mapping_blob: bytes, source_blob: bytes) -> list[str]:
        called["historical"] += 1
        return cast(list[str], historical(mapping_blob, source_blob))

    def track_portable(mapping_blob: bytes, source_blob: bytes) -> list[str]:
        called["portable"] += 1
        return cast(list[str], portable(mapping_blob, source_blob))

    monkeypatch.setattr(checker, "validate_mapping_clause_blobs", track_historical)
    monkeypatch.setattr(checker, "validate_portable_mapping_blob", track_portable)
    assert checker._validate_mapping_clause_provenance(ROOT) == []
    assert called == {"historical": 1, "portable": 1}


@pytest.mark.skipif(shutil.which("gitleaks") is None, reason="gitleaks CLI unavailable")
def test_current_mapping_passes_with_a_new_squash_commit_fingerprint(tmp_path: Path) -> None:
    repository = tmp_path / "synthetic-squash"
    repository.mkdir()
    target = repository / "docs/governance/superset-mapping-v2.json"
    target.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "docs/governance/superset-mapping-v2.json", target)
    shutil.copyfile(ROOT / ".gitleaksignore", repository / ".gitleaksignore")
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(["git", "add", "."], cwd=repository, check=True)
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "NarraTwin test",
        "GIT_AUTHOR_EMAIL": "test@narratwin.invalid",
        "GIT_COMMITTER_NAME": "NarraTwin test",
        "GIT_COMMITTER_EMAIL": "test@narratwin.invalid",
    }
    subprocess.run(
        ["git", "commit", "-q", "-m", "synthetic squash"],
        cwd=repository,
        env=environment,
        check=True,
    )
    completed = subprocess.run(
        [cast(str, shutil.which("gitleaks")), "detect", "--redact", "--no-banner", "--source", "."],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize(
    "candidate",
    (
        EXPECTED_FINGERPRINTS[1:],
        (*EXPECTED_FINGERPRINTS, "wildcard:*"),
        (EXPECTED_FINGERPRINTS[0].replace("77ebfc32", "87ebfc32"), *EXPECTED_FINGERPRINTS[1:]),
        (EXPECTED_FINGERPRINTS[0].replace("stage8_cut1_routes.py", "other.py"), *EXPECTED_FINGERPRINTS[1:]),
        (EXPECTED_FINGERPRINTS[0].replace("generic-api-key", "private-key"), *EXPECTED_FINGERPRINTS[1:]),
        (EXPECTED_FINGERPRINTS[0].replace(":514", ":515"), *EXPECTED_FINGERPRINTS[1:]),
        tuple(
            fingerprint
            for fingerprint in EXPECTED_FINGERPRINTS
            if fingerprint != EXPECTED_PUBLIC_KEY_FINGERPRINTS[0]
        ),
        (
            *EXPECTED_FINGERPRINTS[:-3],
            EXPECTED_PUBLIC_KEY_FINGERPRINTS[0].replace(
                "backend/Dockerfile", "Dockerfile"
            ),
            *EXPECTED_PUBLIC_KEY_FINGERPRINTS[1:],
        ),
    ),
)
def test_ignore_contract_rejects_omission_addition_and_fingerprint_drift(
    candidate: tuple[str, ...],
) -> None:
    checker = _load_checker()
    assert checker.validate_ignore_lines(candidate) == ["GITLEAKS.IGNORE.EXACT"]


@pytest.mark.parametrize(
    "candidate",
    (
        MAPPING_FINGERPRINT.replace(MAPPING_COMMIT, "0" * 40),
        MAPPING_FINGERPRINT.replace("superset-mapping-v2.json", "other.json"),
        MAPPING_FINGERPRINT.replace("generic-api-key", "private-key"),
        MAPPING_FINGERPRINT.replace(":1474", ":1475"),
    ),
)
def test_mapping_fingerprint_rejects_commit_path_rule_and_line_drift(
    candidate: str,
) -> None:
    checker = _load_checker()
    altered = tuple(
        candidate if item == MAPPING_FINGERPRINT else item for item in EXPECTED_FINGERPRINTS
    )
    assert checker.validate_ignore_lines(altered) == ["GITLEAKS.IGNORE.EXACT"]


def test_frozen_api_contract_bytes_match_the_reviewed_digest() -> None:
    result = subprocess.run(
        ["git", "show", f"{FROZEN_BASE}:docs/API_CONTRACT.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert hashlib.sha256(result.stdout).hexdigest() == EXPECTED_DIGEST


def test_scan_head_contains_each_finding_commit() -> None:
    for fingerprint in EXPECTED_FINGERPRINTS[:4]:
        commit = fingerprint.split(":", 1)[0]
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, SCAN_HEAD],
            cwd=ROOT,
            check=False,
        )
        assert completed.returncode == 0


def test_public_key_provenance_topology_is_complete() -> None:
    availability: list[bool] = []
    for fingerprint in EXPECTED_PUBLIC_KEY_FINGERPRINTS:
        commit = fingerprint.split(":", 1)[0]
        completed = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=ROOT,
            check=False,
        )
        availability.append(completed.returncode == 0)
    assert all(availability) or not any(availability)

    portable = subprocess.run(
        ["git", "cat-file", "-e", f"{PORTABLE_PUBLIC_KEY_HEAD}^{{commit}}"],
        cwd=ROOT,
        check=False,
    )
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PORTABLE_PUBLIC_KEY_HEAD, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    assert portable.returncode == 0
    assert ancestor.returncode == 0


def test_every_reviewed_fingerprint_uses_a_full_lowercase_commit_id() -> None:
    commits = [
        *(fingerprint.split(":", 1)[0] for fingerprint in EXPECTED_FINGERPRINTS),
        PORTABLE_PUBLIC_KEY_HEAD,
    ]
    for commit in commits:
        assert len(commit) == 40
        assert all(character in "0123456789abcdef" for character in commit)


def test_historical_dockerfile_public_key_provenance_is_exact() -> None:
    checker = _load_checker()
    for fingerprint in EXPECTED_PUBLIC_KEY_FINGERPRINTS:
        commit, path, _, _ = fingerprint.rsplit(":", 3)
        assert path == "backend/Dockerfile"
        completed = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if completed.returncode == 0:
            assert checker.validate_public_signing_key_blob(completed.stdout) == []
    portable = subprocess.run(
        ["git", "show", f"{PORTABLE_PUBLIC_KEY_HEAD}:backend/Dockerfile"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert checker.validate_portable_public_signing_key_blob(portable.stdout) == []


def test_hosted_checkout_uses_reachable_public_key_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    original_git = cast(Callable[..., subprocess.CompletedProcess[bytes]], checker._git)
    local_only_commits = {
        fingerprint.split(":", 1)[0] for fingerprint in EXPECTED_PUBLIC_KEY_FINGERPRINTS
    }

    def hosted_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        if len(args) >= 3 and args[:2] == ("cat-file", "-e"):
            commit = args[2].removesuffix("^{commit}")
            if commit in local_only_commits:
                return subprocess.CompletedProcess(args, 128, b"", b"missing")
        if len(args) >= 2 and args[0] == "show":
            commit = args[1].split(":", 1)[0]
            if commit in local_only_commits:
                return subprocess.CompletedProcess(args, 128, b"", b"missing")
        return original_git(root, *args)

    monkeypatch.setattr(checker, "_git", hosted_git)
    assert checker.validate(ROOT) == []


def test_hosted_checkout_rejects_missing_portable_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    original_git = cast(
        Callable[..., subprocess.CompletedProcess[bytes]], checker._git
    )
    unavailable = {
        *(fingerprint.split(":", 1)[0] for fingerprint in EXPECTED_PUBLIC_KEY_FINGERPRINTS),
        PORTABLE_PUBLIC_KEY_HEAD,
    }

    def missing_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        if len(args) >= 3 and args[:2] == ("cat-file", "-e"):
            commit = args[2].removesuffix("^{commit}")
            if commit in unavailable:
                return subprocess.CompletedProcess(args, 128, b"", b"missing")
        return original_git(root, *args)

    monkeypatch.setattr(checker, "_git", missing_git)
    assert "GITLEAKS.PROVENANCE.PUBLIC_KEY_PORTABLE_HISTORY" in checker.validate(
        ROOT
    )


def test_partial_public_key_history_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    original_git = cast(
        Callable[..., subprocess.CompletedProcess[bytes]], checker._git
    )
    missing_commit = EXPECTED_PUBLIC_KEY_FINGERPRINTS[0].split(":", 1)[0]

    def partial_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        if len(args) >= 3 and args[:2] == ("cat-file", "-e"):
            commit = args[2].removesuffix("^{commit}")
            if commit == missing_commit:
                return subprocess.CompletedProcess(args, 128, b"", b"missing")
            if commit in {
                fingerprint.split(":", 1)[0]
                for fingerprint in EXPECTED_PUBLIC_KEY_FINGERPRINTS
            }:
                return subprocess.CompletedProcess(args, 0, b"", b"")
        return original_git(root, *args)

    monkeypatch.setattr(checker, "_git", partial_git)
    assert "GITLEAKS.PROVENANCE.PUBLIC_KEY_TOPOLOGY" in checker.validate(ROOT)


def test_available_public_key_snapshot_failure_never_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    original_git = cast(
        Callable[..., subprocess.CompletedProcess[bytes]], checker._git
    )
    first_commit = EXPECTED_PUBLIC_KEY_FINGERPRINTS[0].split(":", 1)[0]

    def unreadable_git(
        root: Path, *args: str
    ) -> subprocess.CompletedProcess[bytes]:
        if len(args) >= 3 and args[:2] == ("cat-file", "-e"):
            commit = args[2].removesuffix("^{commit}")
            if commit in {
                fingerprint.split(":", 1)[0]
                for fingerprint in EXPECTED_PUBLIC_KEY_FINGERPRINTS
            }:
                return subprocess.CompletedProcess(args, 0, b"", b"")
        if len(args) >= 2 and args[0] == "show" and args[1].startswith(
            f"{first_commit}:"
        ):
            return subprocess.CompletedProcess(args, 128, b"", b"unreadable")
        return original_git(root, *args)

    monkeypatch.setattr(checker, "_git", unreadable_git)
    assert "GITLEAKS.PROVENANCE.PUBLIC_KEY_SNAPSHOT" in checker.validate(ROOT)


def test_public_signing_key_provenance_rejects_blob_and_context_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    portable = subprocess.run(
        ["git", "show", f"{PORTABLE_PUBLIC_KEY_HEAD}:backend/Dockerfile"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    blob = portable.replace(b"python_gpg_fingerprint", b"python_gpg_key")
    monkeypatch.setattr(
        checker, "EXPECTED_DOCKERFILE_SHA256", hashlib.sha256(blob).hexdigest()
    )
    assert checker.validate_public_signing_key_blob(blob) == []
    assert checker.validate_public_signing_key_blob(
        blob.replace(b"python_gpg_key=", b"python_gpg_key=X", 1)
    )
    assert checker.validate_public_signing_key_blob(
        blob.replace(b"--recv-keys", b"--list-keys", 1)
    )


def test_portable_public_signing_key_provenance_rejects_drift() -> None:
    checker = _load_checker()
    blob = subprocess.run(
        ["git", "show", f"{PORTABLE_PUBLIC_KEY_HEAD}:backend/Dockerfile"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert checker.validate_portable_public_signing_key_blob(blob) == []
    assert checker.validate_portable_public_signing_key_blob(
        blob.replace(b"python_gpg_fingerprint=", b"python_gpg_fingerprint=X", 1)
    )
    assert checker.validate_portable_public_signing_key_blob(
        blob.replace(b"--recv-keys", b"--list-keys", 1)
    )


def test_security_wrapper_runs_contract_canary_and_full_history_scan() -> None:
    text = (ROOT / "scripts/ci/dependency-security.sh").read_text(encoding="utf-8")
    contract = "python3 scripts/ci/check_gitleaks_regression.py"
    canary = "gitleaks stdin"
    history = "gitleaks detect --redact --source ."
    assert text.index(contract) < text.index(canary) < text.index(history)
    assert 'GITLEAKS_CANARY_STATUS}" -ne 86' in text
    assert "--no-git" not in text
    assert "|| true" not in text
