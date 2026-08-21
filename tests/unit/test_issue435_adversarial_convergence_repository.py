"""Repository/Git/nonactivation RED oracle for Issue #435."""

from __future__ import annotations

import ast
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
CORE_ORACLE_PATH = ROOT / ORACLE_PATHS[0]


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


def frozen_red_nodes() -> tuple[str, ...]:
    module = ast.parse(CORE_ORACLE_PATH.read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXPECTED_RED_FAILURES"
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            assert isinstance(value, tuple) and all(isinstance(item, str) for item in value)
            return value
    raise AssertionError("EXPECTED_RED_FAILURES literal is missing")


def create_real_git_freeze(
    tmp_path: Path, *, extra_c3_path: bool = False, merge_c3: bool = False
) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "repository"
    root.mkdir(parents=True)
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
    red_nodes = frozen_red_nodes()
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
        "expectedRedFailures": list(red_nodes),
        "redCatalogSha256": hashlib.sha256(canonical(red_nodes)).hexdigest(),
        "redBlockers": {
            "IMPLEMENTATION_BLOCKER": len(red_nodes),
            "EVIDENCE_BLOCKER": 0,
        },
        "reviewBlockers": {"IMPLEMENTATION_BLOCKER": 0, "EVIDENCE_BLOCKER": 0},
        "reviewFindings": [],
        "activation": "NONE",
        "authorityEffect": "NO_AUTHORITY_EFFECT",
        "completionState": "PRE_GREEN_REVIEWS_COMPLETE",
    }
    freeze_path = root / FREEZE_PATH
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    if extra_c3_path:
        (root / "unexpected-c3-path.txt").write_text("scope drift\n", encoding="utf-8")
    git(root, "add", FREEZE_PATH)
    if extra_c3_path:
        git(root, "add", "unexpected-c3-path.txt")
    if merge_c3:
        unrelated = git(root, "commit-tree", red_tree, "-m", "unrelated parent")
        c3_tree = git(root, "write-tree")
        c3_head = git(
            root,
            "commit-tree",
            c3_tree,
            "-p",
            red_head,
            "-p",
            unrelated,
            "-m",
            "C3 merge freeze",
        )
        git(root, "update-ref", "HEAD", c3_head)
    else:
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
    red_nodes = frozen_red_nodes()
    assert len(red_nodes) == protocol.EXPECTED_RED_FAILURES_COUNT
    assert hashlib.sha256(canonical(red_nodes)).hexdigest() == (
        protocol.EXPECTED_RED_FAILURES_SHA256
    )
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
    for ordinal in range(2):
        for field, value, code in (
            ("path", "tests/unit/wrong.py", "ACP.FREEZE.ORACLE_PATH_MISMATCH"),
            ("blobOid", "0" * 40, "ACP.FREEZE.ORACLE_BLOB_MISMATCH"),
            ("sha256", "0" * 64, "ACP.FREEZE.ORACLE_SHA_MISMATCH"),
        ):
            changed = deepcopy(freeze)
            changed["focusedOracleBlobs"][ordinal][field] = value
            freeze_path.write_bytes(canonical(changed) + b"\n")
            assert protocol.validate_repository_freeze(root) == finding(
                "freeze", code, f"focusedOracleBlobs[{ordinal}].{field}"
            )
        for field in ("path", "blobOid", "sha256"):
            changed = deepcopy(freeze)
            del changed["focusedOracleBlobs"][ordinal][field]
            freeze_path.write_bytes(canonical(changed) + b"\n")
            assert protocol.validate_repository_freeze(root) == finding(
                "freeze", "ACP.FREEZE.FIELD_MISSING", f"focusedOracleBlobs[{ordinal}].{field}"
            )
        changed = deepcopy(freeze)
        changed["focusedOracleBlobs"][ordinal]["unknown"] = True
        freeze_path.write_bytes(canonical(changed) + b"\n")
        assert protocol.validate_repository_freeze(root) == finding(
            "freeze", "ACP.FREEZE.UNKNOWN_FIELD", f"focusedOracleBlobs[{ordinal}].unknown"
        )
    for changed, code in (
        (
            {**freeze, "focusedOracleBlobs": freeze["focusedOracleBlobs"][::-1]},
            "ACP.FREEZE.ORACLE_ORDER",
        ),
        (
            {**freeze, "focusedOracleBlobs": freeze["focusedOracleBlobs"][:1]},
            "ACP.FREEZE.ORACLE_COUNT",
        ),
        (
            {
                **freeze,
                "focusedOracleBlobs": [
                    *freeze["focusedOracleBlobs"],
                    freeze["focusedOracleBlobs"][0],
                ],
            },
            "ACP.FREEZE.ORACLE_COUNT",
        ),
    ):
        freeze_path.write_bytes(canonical(changed) + b"\n")
        assert protocol.validate_repository_freeze(root) == finding(
            "freeze", code, "focusedOracleBlobs"
        )
    nonancestor = git(root, "commit-tree", freeze["redTree"], "-m", "nonancestor RED")
    changed = deepcopy(freeze)
    changed["redHead"] = nonancestor
    for reviewer in changed["reviewers"]:
        reviewer["reviewedRedHead"] = nonancestor
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.RED_NOT_C3_PARENT", "redHead"
    )
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    (root / ORACLE_PATHS[0]).write_text("post-RED mutation\n", encoding="utf-8")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.ORACLE_IMMUTABLE", ORACLE_PATHS[0]
    )
    scoped_root, _ = create_real_git_freeze(tmp_path / "scope", extra_c3_path=True)
    assert protocol.validate_repository_freeze(scoped_root) == finding(
        "freeze",
        "ACP.FREEZE.C3_SCOPE",
        "docs/governance/adversarial-convergence-red-freeze-v1.json",
    )
    merge_root, _ = create_real_git_freeze(tmp_path / "merge", merge_c3=True)
    assert protocol.validate_repository_freeze(merge_root) == finding(
        "freeze", "ACP.FREEZE.C3_PARENT_COUNT", "HEAD"
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
    wrong_schema = deepcopy(freeze)
    wrong_schema["schemaVersion"] = "OtherV1"
    wrong_matrix = deepcopy(freeze)
    wrong_matrix["matrixId"] = "issue-999-adversarial-convergence-v1"
    cases: tuple[tuple[dict[str, Any], str, str], ...] = (
        (missing, "ACP.FREEZE.FIELD_MISSING", "redBlockers"),
        (unknown, "ACP.FREEZE.UNKNOWN_FIELD", "selfApproved"),
        (no_red, "ACP.FREEZE.RED_FAILURES_EMPTY", "expectedRedFailures"),
        (conflated, "ACP.FREEZE.REVIEW_BLOCKERS_NONZERO", "reviewBlockers.EVIDENCE_BLOCKER"),
        (self_review, "ACP.FREEZE.SELF_REVIEW", "reviewers[0].identity"),
        (wrong_schema, "ACP.FREEZE.SCHEMA_VERSION", "schemaVersion"),
        (wrong_matrix, "ACP.FREEZE.MATRIX_ID", "matrixId"),
    )
    for document, code, location in cases:
        result = protocol.validate_matrix_bytes(matrix, canonical(document))
        assert result.findings == finding("freeze", code, location)

    red_nodes = frozen_red_nodes()
    for replacement in (
        red_nodes[:-1],
        (*red_nodes[:-1], red_nodes[0]),
        red_nodes[::-1],
        (*red_nodes[:-1], "tests/unit/substituted.py::test_substituted"),
    ):
        changed = deepcopy(freeze)
        changed["expectedRedFailures"] = list(replacement)
        result = protocol.validate_matrix_bytes(matrix, canonical(changed))
        assert result.findings == finding(
            "freeze", "ACP.FREEZE.RED_CATALOG_MISMATCH", "expectedRedFailures"
        )
    changed = deepcopy(freeze)
    changed["redCatalogSha256"] = "0" * 64
    assert protocol.validate_matrix_bytes(matrix, canonical(changed)).findings == finding(
        "freeze", "ACP.FREEZE.RED_CATALOG_SHA_MISMATCH", "redCatalogSha256"
    )
    changed = deepcopy(freeze)
    changed["redBlockers"]["IMPLEMENTATION_BLOCKER"] -= 1
    assert protocol.validate_matrix_bytes(matrix, canonical(changed)).findings == finding(
        "freeze", "ACP.FREEZE.RED_BLOCKER_COUNT", "redBlockers.IMPLEMENTATION_BLOCKER"
    )

    reviewer_mutations: list[tuple[dict[str, Any], str, str]] = []
    changed = deepcopy(freeze)
    changed["reviewers"] = changed["reviewers"][::-1]
    reviewer_mutations.append((changed, "ACP.FREEZE.REVIEW_ROLE_ORDER", "reviewers"))
    for field, value, code in (
        ("role", "wrong", "ACP.FREEZE.REVIEW_ROLE"),
        ("disposition", "REQUEST_CHANGES", "ACP.FREEZE.REVIEW_DISPOSITION"),
        ("reviewedRedHead", "0" * 40, "ACP.FREEZE.REVIEW_HEAD"),
        ("semanticSha256", "0" * 64, "ACP.FREEZE.REVIEW_SEMANTIC"),
        ("commentUrl", "https://example.invalid/review", "ACP.FREEZE.REVIEW_URL"),
    ):
        changed = deepcopy(freeze)
        changed["reviewers"][0][field] = value
        reviewer_mutations.append((changed, code, f"reviewers[0].{field}"))
    changed = deepcopy(freeze)
    changed["reviewers"][1]["identity"] = changed["reviewers"][0]["identity"]
    reviewer_mutations.append(
        (changed, "ACP.FREEZE.REVIEW_IDENTITY_DUPLICATE", "reviewers[1].identity")
    )
    changed = deepcopy(freeze)
    changed["reviewers"][1]["commentUrl"] = changed["reviewers"][0]["commentUrl"]
    reviewer_mutations.append(
        (changed, "ACP.FREEZE.REVIEW_URL_DUPLICATE", "reviewers[1].commentUrl")
    )
    changed = deepcopy(freeze)
    changed["reviewFindings"] = ["unresolved"]
    reviewer_mutations.append((changed, "ACP.FREEZE.REVIEW_FINDINGS_NONZERO", "reviewFindings"))
    changed = deepcopy(freeze)
    del changed["reviewers"][0]["role"]
    reviewer_mutations.append((changed, "ACP.FREEZE.FIELD_MISSING", "reviewers[0].role"))
    changed = deepcopy(freeze)
    changed["reviewers"][0]["unknown"] = True
    reviewer_mutations.append((changed, "ACP.FREEZE.UNKNOWN_FIELD", "reviewers[0].unknown"))
    for document, code, location in reviewer_mutations:
        assert protocol.validate_matrix_bytes(matrix, canonical(document)).findings == finding(
            "freeze", code, location
        )


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
    read_only_git = (
        "import subprocess\n"
        "subprocess.run(('git', 'rev-parse', 'HEAD'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'rev-parse', 'HEAD^'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'rev-parse', f'{red_head}:docs/freeze.json'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'merge-base', '--is-ancestor', red_head, 'HEAD'), cwd=root, check=False, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'show', '-s', '--format=%ae', red_head), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'cat-file', '-e', red_head), cwd=root, check=True, capture_output=True, text=True)\n"
    )
    assert protocol.static_boundary_findings(read_only_git) == ()
    for hostile, code in (
        ("import requests\n", "ACP.STATIC.NETWORK_IMPORT"),
        ("from socket import socket as connect\n", "ACP.STATIC.NETWORK_IMPORT"),
        ("import urllib.request as net\n", "ACP.STATIC.NETWORK_IMPORT"),
        ("from httpx import get\n", "ACP.STATIC.NETWORK_IMPORT"),
        ("import boto3\n", "ACP.STATIC.PROVIDER_IMPORT"),
        ("from google.cloud import storage\n", "ACP.STATIC.PROVIDER_IMPORT"),
        (
            "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey\n",
            "ACP.STATIC.PRIVATE_KEY",
        ),
        ("key = Ed25519PrivateKey.generate()\n", "ACP.STATIC.KEY_GENERATION"),
        ("signature = key.sign(message)\n", "ACP.STATIC.SIGNING"),
        ("x = __import__('socket')\n", "ACP.STATIC.DYNAMIC_IMPORT"),
        ("import importlib\nx = importlib.import_module(name)\n", "ACP.STATIC.DYNAMIC_IMPORT"),
        ("eval(source)\n", "ACP.STATIC.DYNAMIC_EXECUTION"),
        ("exec(source)\n", "ACP.STATIC.DYNAMIC_EXECUTION"),
        ("open('state', mode='w')\n", "ACP.STATIC.WRITE"),
        ("from builtins import open as persist\npersist('state', 'w')\n", "ACP.STATIC.WRITE"),
        ("Path('state').write_text('x')\n", "ACP.STATIC.WRITE"),
        ("Path('state').write_bytes(b'x')\n", "ACP.STATIC.WRITE"),
        ("Path('state').open(mode='w')\n", "ACP.STATIC.WRITE"),
        ("Path('state').touch()\n", "ACP.STATIC.WRITE"),
        ("Path('state').rename('other')\n", "ACP.STATIC.WRITE"),
        ("Path('state').replace('other')\n", "ACP.STATIC.WRITE"),
        ("Path('state').unlink()\n", "ACP.STATIC.WRITE"),
        ("os.open('state', os.O_WRONLY)\n", "ACP.STATIC.WRITE"),
        ("shutil.copyfile('a', 'b')\n", "ACP.STATIC.PERSISTENCE"),
        ("sqlite3.connect('state.db')\n", "ACP.STATIC.PERSISTENCE"),
        ("subprocess.run(['curl', 'https://example.invalid'])\n", "ACP.STATIC.PROCESS"),
        ("from subprocess import run as execute\nexecute(command)\n", "ACP.STATIC.PROCESS"),
        ("subprocess.call(command)\n", "ACP.STATIC.PROCESS"),
        ("subprocess.check_output(command)\n", "ACP.STATIC.PROCESS"),
        ("subprocess.Popen(command)\n", "ACP.STATIC.PROCESS"),
        ("getattr(subprocess, 'Popen')(command)\n", "ACP.STATIC.PROCESS"),
        ("os.system(command)\n", "ACP.STATIC.PROCESS"),
        ("from os import system as execute\nexecute(command)\n", "ACP.STATIC.PROCESS"),
        ("asyncio.create_subprocess_exec('git', 'status')\n", "ACP.STATIC.PROCESS"),
        ("Path('state').mkdir()\n", "ACP.STATIC.WRITE"),
        ("Path('state').rmdir()\n", "ACP.STATIC.WRITE"),
        ("Path('state').chmod(0o600)\n", "ACP.STATIC.WRITE"),
        ("Path('state').symlink_to('target')\n", "ACP.STATIC.WRITE"),
        ("os.unlink('state')\n", "ACP.STATIC.WRITE"),
        ("os.remove('state')\n", "ACP.STATIC.WRITE"),
        ("os.rename('state', 'other')\n", "ACP.STATIC.WRITE"),
        ("os.replace('state', 'other')\n", "ACP.STATIC.WRITE"),
        ("os.mkdir('state')\n", "ACP.STATIC.WRITE"),
        ("shutil.move('a', 'b')\n", "ACP.STATIC.PERSISTENCE"),
        ("shutil.rmtree('a')\n", "ACP.STATIC.PERSISTENCE"),
        ("shutil.copytree('a', 'b')\n", "ACP.STATIC.PERSISTENCE"),
        ("subprocess.run(('git', 'commit', '-m', 'x'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'reset', '--hard', 'HEAD'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'clean', '-fdx'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'checkout', 'other'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'update-ref', 'HEAD', value))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'apply', 'patch'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'add', '.'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'config', 'x', 'y'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'hash-object', '-w', 'x'))\n", "ACP.STATIC.GIT_MUTATION"),
        ("subprocess.run(('git', 'ls-remote', 'origin'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'fetch', 'origin'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'pull'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'push'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'clone', 'remote'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'show', '--output=state', 'HEAD'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'rev-parse', '--verify', 'HEAD'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        ("subprocess.run(('git', 'cat-file', '-p', 'HEAD'))\n", "ACP.STATIC.GIT_FORBIDDEN"),
        (
            "subprocess.run(('git', 'diff-tree', '-r', '--name-only', 'HEAD'))\n",
            "ACP.STATIC.GIT_FORBIDDEN",
        ),
        (
            "subprocess.run(('git', 'rev-parse', 'HEAD'), env=environment)\n",
            "ACP.STATIC.GIT_DYNAMIC",
        ),
        ("subprocess.run(('git', 'rev-parse', 'HEAD'), shell=True)\n", "ACP.STATIC.PROCESS"),
        (
            "subprocess.run(('git', 'rev-parse', 'HEAD'), cwd=dynamic_root)\n",
            "ACP.STATIC.GIT_DYNAMIC",
        ),
        ("subprocess.run(('git', command, 'HEAD'))\n", "ACP.STATIC.GIT_DYNAMIC"),
    ):
        assert protocol.static_boundary_findings(hostile) == finding("static", code, "source")


def write_preflight(root: Path, *, objective: str, required: list[str], issue: int = 435) -> Path:
    path = root / f"docs/governance/preflights/issue-{issue}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "GovernancePreflightV1",
                "issue_number": issue,
                "branch": f"process-{issue}-neutral",
                "objective": objective,
                "status_decision": "update-minimally",
                "scope": {"required": required, "allowed_prefixes": required, "forbidden": []},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_sensitive_route_uses_paths_and_exact_issue_artifacts(tmp_path: Path) -> None:
    root, freeze = create_real_git_freeze(tmp_path)
    preflight = write_preflight(
        root, objective="routine documentation", required=["docs/SECURITY_AND_PRIVACY.md"]
    )
    location = preflight.relative_to(root).as_posix()
    assert protocol.route_findings(root) == ()
    freeze_path = root / FREEZE_PATH
    freeze_path.write_text("{}\n", encoding="utf-8")
    assert protocol.route_findings(root) == finding("route", "ACP.ROUTE.FREEZE_INVALID", location)
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    changed = deepcopy(freeze)
    changed["matrixId"] = "issue-999-adversarial-convergence-v1"
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.route_findings(root) == finding("route", "ACP.ROUTE.ISSUE_MISMATCH", location)
    route_mutations = (
        ("semanticSha256", "0" * 64, "ACP.FREEZE.INDEPENDENT_SEMANTIC_MISMATCH", "semanticSha256"),
        ("reviewFindings", ["unresolved"], "ACP.FREEZE.REVIEW_FINDINGS_NONZERO", "reviewFindings"),
        ("completionState", "RED_RECORDED", "ACP.FREEZE.COMPLETION_STATE", "completionState"),
    )
    for field, value, code, finding_location in route_mutations:
        changed = deepcopy(freeze)
        changed[field] = value
        freeze_path.write_bytes(canonical(changed) + b"\n")
        assert protocol.route_findings(root) == finding("freeze", code, finding_location)
    changed = deepcopy(freeze)
    changed["focusedOracleBlobs"][0]["sha256"] = "0" * 64
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.route_findings(root) == finding(
        "freeze", "ACP.FREEZE.ORACLE_SHA_MISMATCH", "focusedOracleBlobs[0].sha256"
    )
    changed = deepcopy(freeze)
    changed["reviewers"][0]["disposition"] = "REQUEST_CHANGES"
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.route_findings(root) == finding(
        "freeze", "ACP.FREEZE.REVIEW_DISPOSITION", "reviewers[0].disposition"
    )
    freeze_path.write_bytes(canonical(freeze) + b" " * 32768)
    assert protocol.route_findings(root) == finding("bounds", "ACP.BOUNDS.FREEZE_BYTES", "freeze")
    matrix_path = root / protocol.MATRIX_PATH.relative_to(protocol.ROOT)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    for field, limit_value, code, finding_location in (
        ("findingCount", 33, "ACP.BOUNDS.FINDING_COUNT", "findings"),
        ("retainedMaterialCount", 5, "ACP.BOUNDS.RETAINED_COUNT", "retained-materials"),
    ):
        changed_matrix = deepcopy(matrix)
        changed_matrix["limits"][field] = limit_value
        matrix_path.write_bytes(canonical(changed_matrix) + b"\n")
        assert protocol.route_findings(root) == finding("bounds", code, finding_location)
    matrix_path.write_bytes(canonical(matrix) + b"\n")
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    assert protocol.route_findings(root, changed_paths=("../escape",)) == finding(
        "route", "ACP.ROUTE.PATH_TRAVERSAL", "../escape"
    )


@pytest.mark.parametrize(
    ("stage", "branch", "policy_only"),
    (
        ("8", "process-435", False),
        ("8", "process-435", True),
        ("8", "final-review-435", False),
        ("8", "phase-1-closure-435", False),
        ("8", "main", False),
        ("8", "main", True),
        ("8", "neutral-435", False),
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
