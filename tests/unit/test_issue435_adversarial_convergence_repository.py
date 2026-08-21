"""Repository/Git/nonactivation RED oracle for Issue #435."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from scripts.quality import issue435_adversarial_convergence as protocol


ROOT = Path(__file__).parents[2]
MATRIX_PATH = ROOT / "docs/governance/adversarial-convergence-invariant-matrix-v1.json"
FREEZE_PATH = "docs/governance/adversarial-convergence-red-freeze-v1.json"
ORACLE_PATHS = (
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def finding(stage: str, code: str, location: str) -> tuple[protocol.Finding, ...]:
    return (protocol.Finding(stage, "CURRENT", code, location),)


def git(root: Path, *arguments: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ("git", *arguments),
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_real_git_freeze(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "repository"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Implementation Author")
    git(root, "config", "user.email", "implementation@example.com")
    matrix = root / protocol.MATRIX_PATH.relative_to(protocol.ROOT)
    matrix.parent.mkdir(parents=True)
    matrix.write_bytes(MATRIX_PATH.read_bytes())
    for ordinal, relative in enumerate(ORACLE_PATHS):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"frozen oracle {ordinal}\n", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "genuine RED")
    red_head = git(root, "rev-parse", "HEAD")
    red_tree = git(root, "rev-parse", "HEAD^{tree}")
    semantic_sha = hashlib.sha256(
        canonical(json.loads(matrix.read_text(encoding="utf-8")))
    ).hexdigest()
    freeze: dict[str, Any] = {
        "schemaVersion": "AdversarialRedFreezeV1",
        "matrixId": "issue-435-adversarial-convergence-v1",
        "redHead": red_head,
        "redTree": red_tree,
        "matrixBlobOid": git(root, "rev-parse", f"{red_head}:{matrix.relative_to(root)}"),
        "matrixSha256": file_sha(matrix),
        "focusedOracleBlobs": [
            {
                "path": relative,
                "blobOid": git(root, "rev-parse", f"{red_head}:{relative}"),
                "sha256": file_sha(root / relative),
            }
            for relative in ORACLE_PATHS
        ],
        "semanticSha256": semantic_sha,
        "implementationAuthor": "implementation@example.com",
        "reviewers": [
            {
                "role": role,
                "identity": f"{role}@review.invalid",
                "commentUrl": f"https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-{index}",
                "disposition": "PASS",
                "reviewedRedHead": red_head,
                "semanticSha256": semantic_sha,
            }
            for index, role in enumerate(
                ("architecture", "security_trust", "mutation_false_pass"), start=1
            )
        ],
        "expectedRedFailures": ["test_red_one", "test_red_two"],
        "redBlockers": {"IMPLEMENTATION_BLOCKER": 2, "EVIDENCE_BLOCKER": 0},
        "reviewBlockers": {"IMPLEMENTATION_BLOCKER": 0, "EVIDENCE_BLOCKER": 0},
        "reviewFindings": [],
        "activation": "NONE",
        "authorityEffect": "NO_AUTHORITY_EFFECT",
        "completionState": "PRE_GREEN_REVIEWS_COMPLETE",
    }
    freeze_path = root / FREEZE_PATH
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    git(root, "add", FREEZE_PATH)
    git(
        root,
        "-c",
        "user.name=Freeze Owner",
        "-c",
        "user.email=owner@example.com",
        "commit",
        "-q",
        "-m",
        "C3 freeze",
    )
    return root, freeze


def test_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability(
    tmp_path: Path,
) -> None:
    root, freeze = create_real_git_freeze(tmp_path)
    assert protocol.validate_repository_freeze(root) == ()
    freeze_path = root / FREEZE_PATH
    mutations = (
        ("redHead", "0" * 40, "ACP.FREEZE.RED_HEAD_MISSING"),
        ("redTree", "0" * 40, "ACP.FREEZE.RED_TREE_MISMATCH"),
        ("matrixBlobOid", "0" * 40, "ACP.FREEZE.MATRIX_BLOB_MISMATCH"),
        ("matrixSha256", "0" * 64, "ACP.FREEZE.MATRIX_SHA_MISMATCH"),
        ("implementationAuthor", "other@example.com", "ACP.FREEZE.AUTHOR_MISMATCH"),
    )
    for field, value, code in mutations:
        changed = deepcopy(freeze)
        changed[field] = value
        freeze_path.write_bytes(canonical(changed) + b"\n")
        assert protocol.validate_repository_freeze(root) == finding("freeze", code, field)
    changed = deepcopy(freeze)
    changed["focusedOracleBlobs"][1]["sha256"] = "0" * 64
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.ORACLE_SHA_MISMATCH", "focusedOracleBlobs[1].sha256"
    )
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    (root / ORACLE_PATHS[0]).write_text("post-RED mutation\n", encoding="utf-8")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.ORACLE_IMMUTABLE", ORACLE_PATHS[0]
    )


def test_freeze_schema_closes_roles_red_nodes_and_separate_blockers(tmp_path: Path) -> None:
    root, freeze = create_real_git_freeze(tmp_path)
    matrix = (root / protocol.MATRIX_PATH.relative_to(protocol.ROOT)).read_bytes()
    assert protocol.validate_matrix_bytes(matrix, canonical(freeze)).findings == ()
    missing = deepcopy(freeze)
    del missing["redBlockers"]
    unknown = deepcopy(freeze)
    unknown["selfApproved"] = True
    no_red = deepcopy(freeze)
    no_red["expectedRedFailures"] = []
    conflated = deepcopy(freeze)
    conflated["reviewBlockers"]["EVIDENCE_BLOCKER"] = 1
    self_review = deepcopy(freeze)
    self_review["reviewers"][0]["identity"] = freeze["implementationAuthor"]
    cases: tuple[tuple[dict[str, Any], str, str], ...] = (
        (missing, "ACP.FREEZE.FIELD_MISSING", "redBlockers"),
        (unknown, "ACP.FREEZE.UNKNOWN_FIELD", "selfApproved"),
        (no_red, "ACP.FREEZE.RED_FAILURES_EMPTY", "expectedRedFailures"),
        (conflated, "ACP.FREEZE.REVIEW_BLOCKERS_NONZERO", "reviewBlockers.EVIDENCE_BLOCKER"),
        (self_review, "ACP.FREEZE.SELF_REVIEW", "reviewers[0].identity"),
    )
    for document, code, location in cases:
        result = protocol.validate_matrix_bytes(matrix, canonical(document))
        assert result.findings == finding("freeze", code, location)


def test_activation_authority_and_every_prohibition_fail_exactly(tmp_path: Path) -> None:
    root, freeze = create_real_git_freeze(tmp_path)
    matrix_path = root / protocol.MATRIX_PATH.relative_to(protocol.ROOT)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    for field, value, code in (
        ("activation", "ACTIVE", "ACP.BOUNDARY.ACTIVATION"),
        ("authorityEffect", "AUTHORITY_CREATED", "ACP.BOUNDARY.AUTHORITY_EFFECT"),
    ):
        changed = deepcopy(matrix)
        changed[field] = value
        result = protocol.validate_matrix_bytes(canonical(changed), canonical(freeze))
        assert result.findings == finding("matrix", code, field)
    for capability in matrix["prohibitedCapabilities"]:
        changed = deepcopy(matrix)
        changed["prohibitedCapabilities"].remove(capability)
        result = protocol.validate_matrix_bytes(canonical(changed), canonical(freeze))
        assert result.findings == finding(
            "matrix", "ACP.BOUNDARY.PROHIBITION_MISSING", f"prohibitedCapabilities.{capability}"
        )


def test_repository_validator_is_read_only_and_static_boundary_is_ast_exact(
    tmp_path: Path,
) -> None:
    root, _ = create_real_git_freeze(tmp_path)
    before = {
        path.relative_to(root).as_posix(): file_sha(path)
        for path in root.rglob("*")
        if path.is_file()
    }
    assert protocol.validate_repository_freeze(root) == ()
    after = {
        path.relative_to(root).as_posix(): file_sha(path)
        for path in root.rglob("*")
        if path.is_file()
    }
    assert after == before
    source = (ROOT / "scripts/quality/issue435_adversarial_convergence.py").read_text()
    assert protocol.static_boundary_findings(source) == ()
    for hostile, code in (
        ("import requests\n", "ACP.STATIC.NETWORK_IMPORT"),
        (
            "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey\n",
            "ACP.STATIC.PRIVATE_KEY",
        ),
        ("x = __import__('socket')\n", "ACP.STATIC.DYNAMIC_IMPORT"),
        ("open('state', mode='w')\n", "ACP.STATIC.WRITE"),
        ("subprocess.run(['curl', 'https://example.invalid'])\n", "ACP.STATIC.PROCESS"),
    ):
        assert protocol.static_boundary_findings(hostile) == finding("static", code, "source")


def write_preflight(root: Path, *, objective: str, required: list[str]) -> Path:
    path = root / "docs/governance/preflights/issue-900.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "GovernancePreflightV1",
                "issue_number": 900,
                "branch": "process-900-neutral",
                "objective": objective,
                "status_decision": "update-minimally",
                "scope": {"required": required, "allowed_prefixes": required, "forbidden": []},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_sensitive_route_uses_paths_and_exact_issue_artifacts(tmp_path: Path) -> None:
    preflight = write_preflight(
        tmp_path, objective="routine documentation", required=["docs/SECURITY_AND_PRIVACY.md"]
    )
    location = preflight.relative_to(tmp_path).as_posix()
    assert protocol.route_findings(tmp_path) == (
        *finding("route", "ACP.ROUTE.MATRIX_REQUIRED", location),
        *finding("route", "ACP.ROUTE.FREEZE_REQUIRED", location),
    )
    matrix = tmp_path / "docs/governance/adversarial-invariant-matrix-issue-900.json"
    freeze = tmp_path / "docs/governance/adversarial-red-freeze-issue-900.json"
    matrix.write_bytes(MATRIX_PATH.read_bytes())
    freeze.write_text("{}\n", encoding="utf-8")
    assert protocol.route_findings(tmp_path) == ()
    matrix.rename(matrix.with_name("adversarial-invariant-matrix-issue-901.json"))
    assert protocol.route_findings(tmp_path) == finding(
        "route", "ACP.ROUTE.MATRIX_REQUIRED", location
    )
    assert protocol.route_findings(tmp_path, changed_paths=("../escape",)) == finding(
        "route", "ACP.ROUTE.PATH_TRAVERSAL", "../escape"
    )


@pytest.mark.parametrize(
    ("stage", "branch", "policy_only"),
    (
        ("8", "process-435", False),
        ("8", "process-435", True),
        ("8", "final-review-435", False),
        ("8", "phase-1-closure-435", False),
    ),
)
def test_dispatcher_runs_protocol_first_and_fails_fast(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    branch: str,
    policy_only: bool,
) -> None:
    from scripts.quality import check_quality_stage as dispatcher

    current = tmp_path / ".stage/current"
    current.parent.mkdir()
    current.write_text(stage, encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fake_call(command: list[str], *, cwd: Path) -> int:
        del cwd
        calls.append(tuple(command))
        return 73 if command[-1] == "scripts/quality/issue435_adversarial_convergence.py" else 0

    monkeypatch.setattr(dispatcher, "CURRENT_STAGE", current)
    monkeypatch.setattr(dispatcher, "current_branch", lambda: branch)
    monkeypatch.setattr("scripts.quality.check_quality_stage.subprocess.call", fake_call)
    monkeypatch.setenv("NARRATWIN_POLICY_ONLY", "1" if policy_only else "0")
    assert dispatcher.main() == 73
    assert calls == [(sys.executable, "scripts/quality/issue435_adversarial_convergence.py")]
