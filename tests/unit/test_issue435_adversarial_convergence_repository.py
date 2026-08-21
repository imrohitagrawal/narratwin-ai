"""Repository/Git/nonactivation RED oracle for Issue #435."""

from __future__ import annotations

import ast
import hashlib
import json
import os
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
GOVERNED_READER_SOURCE = """def _read_governed_bytes(root: Path, relative: str) -> GovernedReadResult:
    if relative not in STATIC_ALLOWED_GOVERNED_READ_PATHS:
        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.PATH_NOT_ALLOWED", relative),))
    governed_path = root / relative
    root_resolved = root.resolve()
    for ancestor in governed_path.parents:
        if ancestor == root:
            break
        if ancestor.is_symlink():
            location = ancestor.relative_to(root).as_posix()
            return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.ANCESTOR_SYMLINK", location),))
    if governed_path.is_symlink():
        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.SYMLINK", relative),))
    resolved = governed_path.resolve()
    if not resolved.is_relative_to(root_resolved):
        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.OUTSIDE_ROOT", relative),))
    if not governed_path.exists():
        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.MISSING", relative),))
    if not governed_path.is_file():
        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.NONREGULAR", relative),))
    payload = governed_path.read_bytes()
    if b"\\x00" in payload:
        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.BINARY", relative),))
    return GovernedReadResult(payload, ())
"""


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
    tmp_path: Path,
    *,
    extra_c3_path: bool = False,
    merge_c3: bool = False,
    omit_c3: bool = False,
    descendant_commits: int = 0,
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
    if omit_c3:
        pass
    elif merge_c3:
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
    for ordinal in range(descendant_commits):
        descendant = root / f"post-c3-{ordinal}.txt"
        descendant.write_text(f"post C3 {ordinal}\n", encoding="utf-8")
        git(root, "add", descendant.name)
        git(root, "commit", "-q", "-m", f"post C3 {ordinal}")
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
    missing_c3_root, _ = create_real_git_freeze(tmp_path / "missing-c3", omit_c3=True)
    assert protocol.validate_repository_freeze(missing_c3_root) == finding(
        "freeze", "ACP.FREEZE.C3_MISSING", "redHead"
    )
    descendant_root, _ = create_real_git_freeze(tmp_path / "descendants", descendant_commits=2)
    assert protocol.validate_repository_freeze(descendant_root) == ()
    descendant_freeze = descendant_root / FREEZE_PATH
    changed = json.loads(descendant_freeze.read_text(encoding="utf-8"))
    changed["reviewers"][0]["commentUrl"] = (
        "https://github.com/imrohitagrawal/narratwin-ai/issues/435#issuecomment-99"
    )
    descendant_freeze.write_bytes(canonical(changed) + b"\n")
    git(descendant_root, "add", FREEZE_PATH)
    git(descendant_root, "commit", "-q", "-m", "mutate frozen C3 payload")
    assert protocol.validate_repository_freeze(descendant_root) == finding(
        "freeze", "ACP.FREEZE.C3_IMMUTABLE", FREEZE_PATH
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

    matrix_schema = b'"schemaVersion": "AdversarialInvariantMatrixV1",'
    freeze_bytes = canonical(freeze)
    freeze_schema = b'"schemaVersion":"AdversarialRedFreezeV1",'
    alternate_matrix = canonical(json.loads(matrix))
    alternate_freeze = json.dumps(freeze, sort_keys=True, indent=2).encode()
    assert alternate_matrix != matrix and json.loads(alternate_matrix) == json.loads(matrix)
    assert alternate_freeze != freeze_bytes and json.loads(alternate_freeze) == freeze
    for matrix_bytes, raw_freeze, stage, code, location in (
        (b"\xff", freeze_bytes, "matrix", "ACP.MATRIX.INVALID_UTF8", "matrix"),
        (b"{", freeze_bytes, "matrix", "ACP.MATRIX.INVALID_JSON", "matrix"),
        (b"", freeze_bytes, "matrix", "ACP.MATRIX.INVALID_JSON", "matrix"),
        (matrix + b"{}", freeze_bytes, "matrix", "ACP.MATRIX.INVALID_JSON", "matrix"),
        (b"[]", freeze_bytes, "matrix", "ACP.MATRIX.NON_OBJECT", "matrix"),
        (
            matrix.replace(matrix_schema, matrix_schema + matrix_schema, 1),
            freeze_bytes,
            "matrix",
            "ACP.MATRIX.DUPLICATE_MEMBER",
            "schemaVersion",
        ),
        (matrix + b" ", freeze_bytes, "matrix", "ACP.MATRIX.NONCANONICAL", "matrix"),
        (alternate_matrix, freeze_bytes, "matrix", "ACP.MATRIX.NONCANONICAL", "matrix"),
        (matrix, b"\xff", "freeze", "ACP.FREEZE.INVALID_UTF8", "freeze"),
        (matrix, b"{", "freeze", "ACP.FREEZE.INVALID_JSON", "freeze"),
        (matrix, b"", "freeze", "ACP.FREEZE.INVALID_JSON", "freeze"),
        (matrix, freeze_bytes + b"{}", "freeze", "ACP.FREEZE.INVALID_JSON", "freeze"),
        (matrix, b"[]", "freeze", "ACP.FREEZE.NON_OBJECT", "freeze"),
        (
            matrix,
            freeze_bytes.replace(freeze_schema, freeze_schema + freeze_schema, 1),
            "freeze",
            "ACP.FREEZE.DUPLICATE_MEMBER",
            "schemaVersion",
        ),
        (matrix, freeze_bytes + b" ", "freeze", "ACP.FREEZE.NONCANONICAL", "freeze"),
        (matrix, alternate_freeze, "freeze", "ACP.FREEZE.NONCANONICAL", "freeze"),
    ):
        assert protocol.validate_matrix_bytes(matrix_bytes, raw_freeze).findings == finding(
            stage, code, location
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = create_real_git_freeze(tmp_path)
    governed_paths = (
        protocol.MATRIX_PATH.relative_to(protocol.ROOT).as_posix(),
        FREEZE_PATH,
        *ORACLE_PATHS,
    )
    successful_calls: list[tuple[Path, str]] = []

    def successful_reader(called_root: Path, relative: str) -> protocol.GovernedReadResult:
        successful_calls.append((called_root, relative))
        return protocol.GovernedReadResult((called_root / relative).read_bytes(), ())

    with monkeypatch.context() as successful_patch:
        successful_patch.setattr(protocol, "_read_governed_bytes", successful_reader)
        assert protocol.validate_repository_freeze(root) == ()
        assert successful_calls == [(root, relative) for relative in governed_paths]
    for failure_ordinal, failure_path in enumerate(governed_paths):
        typed_failure = protocol.GovernedReadResult(
            None,
            finding("file", "ACP.FILE.ANCESTOR_SYMLINK", failure_path),
        )
        typed_calls: list[tuple[Path, str]] = []

        def typed_reader(called_root: Path, relative: str) -> protocol.GovernedReadResult:
            typed_calls.append((called_root, relative))
            if relative == failure_path:
                return typed_failure
            return protocol.GovernedReadResult((called_root / relative).read_bytes(), ())

        with monkeypatch.context() as typed_patch:
            typed_patch.setattr(protocol, "_read_governed_bytes", typed_reader)
            assert protocol.validate_repository_freeze(root) is typed_failure.findings
            assert typed_calls == [
                (root, relative) for relative in governed_paths[: failure_ordinal + 1]
            ]
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
    for ordinal, relative in enumerate(governed_paths):
        for kind, code in (
            ("symlink", "ACP.FILE.SYMLINK"),
            ("directory", "ACP.FILE.NONREGULAR"),
            ("binary", "ACP.FILE.BINARY"),
        ):
            governed_root, _ = create_real_git_freeze(tmp_path / f"governed-{ordinal}-{kind}")
            governed = governed_root / relative
            if kind == "symlink":
                payload = governed_root / f"payload-{ordinal}"
                payload.write_bytes(governed.read_bytes())
                governed.unlink()
                governed.symlink_to(payload)
            elif kind == "directory":
                governed.unlink()
                governed.mkdir()
            else:
                governed.write_bytes(b"\x00binary")
            assert protocol.validate_repository_freeze(governed_root) == finding(
                "file", code, relative
            )
    for path_ordinal, relative in enumerate(governed_paths):
        parent_parts = Path(relative).parent.parts
        for depth in range(1, len(parent_parts) + 1):
            ancestor_relative = Path(*parent_parts[:depth])
            ancestor_root, _ = create_real_git_freeze(
                tmp_path / f"ancestor-symlink-{path_ordinal}-{depth}"
            )
            governed_target = ancestor_root / relative
            governed_ancestor = ancestor_root / ancestor_relative
            within_root_shadow = ancestor_root / f".governed-shadow-{path_ordinal}-{depth}"
            governed_ancestor.rename(within_root_shadow)
            governed_ancestor.symlink_to(within_root_shadow, target_is_directory=True)
            original_ancestor_read = Path.read_bytes

            def reject_ancestor_read(path: Path) -> bytes:
                if path == governed_target:
                    raise AssertionError("ancestor symlink must be rejected before read")
                return original_ancestor_read(path)

            with monkeypatch.context() as ancestor_patch:
                ancestor_patch.setattr(Path, "read_bytes", reject_ancestor_read)
                assert protocol.validate_repository_freeze(ancestor_root) == finding(
                    "file",
                    "ACP.FILE.ANCESTOR_SYMLINK",
                    ancestor_relative.as_posix(),
                )
    fifo_root, _ = create_real_git_freeze(tmp_path / "fifo-nonregular")
    fifo_path = fifo_root / FREEZE_PATH
    fifo_path.unlink()
    os.mkfifo(fifo_path)
    original_read_bytes = Path.read_bytes

    def reject_fifo_read(path: Path) -> bytes:
        if path == fifo_path:
            raise AssertionError("FIFO must be rejected before read")
        return original_read_bytes(path)

    with monkeypatch.context() as fifo_patch:
        fifo_patch.setattr(Path, "read_bytes", reject_fifo_read)
        assert protocol.validate_repository_freeze(fifo_root) == finding(
            "file", "ACP.FILE.NONREGULAR", FREEZE_PATH
        )
    source = (ROOT / "scripts/quality/issue435_adversarial_convergence.py").read_text()
    assert protocol.static_boundary_findings(source) == ()
    read_only_git = (
        "import subprocess\n"
        "subprocess.run(('git', 'rev-parse', 'HEAD'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'rev-list', '--ancestry-path', '--reverse', f'{red_head}..HEAD'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'rev-list', '--parents', '-n', '1', c3_head), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'diff-tree', '--no-commit-id', '--name-only', '-r', c3_head), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'rev-parse', f'{red_head}^{{tree}}', f'{red_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial_convergence_repository.py'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'show', f'{c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json'), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'merge-base', '--is-ancestor', red_head, 'HEAD'), cwd=root, check=False, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'show', '-s', '--format=%ae', red_head), cwd=root, check=True, capture_output=True, text=True)\n"
        "subprocess.run(('git', 'cat-file', '-e', red_head), cwd=root, check=True, capture_output=True, text=True)\n"
    )
    assert protocol.static_boundary_findings(read_only_git) == ()
    static_contract = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))["staticBoundaryContract"]
    assert static_contract["gitEvidenceContract"] == {
        "c3Selection": "first_ordered_descendant_of_red_head",
        "c3Parent": "exactly_one_parent_equal_red_head",
        "c3ChangedPaths": [FREEZE_PATH],
        "redObjectOutputOrder": [
            "red_tree",
            "matrix_blob",
            "core_oracle_blob",
            "repository_oracle_blob",
        ],
        "redObjectOutputCount": 4,
        "c3FreezePayload": "current_governed_freeze_bytes_equal_exact_c3_committed_payload",
        "laterDescendants": "validation_is_head_independent_after_c3",
    }
    assert protocol.STATIC_ALLOWED_IMPORTS == tuple(static_contract["allowedImports"])
    assert protocol.STATIC_ALLOWED_CALL_SHAPES == tuple(static_contract["allowedCallShapes"])
    assert protocol.STATIC_ALLOWED_GOVERNED_READ_PATHS == tuple(
        static_contract["allowedGovernedReadPaths"]
    )
    reader_module = ast.parse(GOVERNED_READER_SOURCE)
    reader_nodes = [
        node
        for node in reader_module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_read_governed_bytes"
    ]
    assert len(reader_nodes) == 1
    governed_reader_ast_sha256 = hashlib.sha256(
        ast.dump(
            reader_nodes[0],
            annotate_fields=True,
            include_attributes=False,
        ).encode()
    ).hexdigest()
    assert (
        protocol.STATIC_GOVERNED_READER_AST_SHA256 == (static_contract["governedReaderAstSha256"])
    )
    assert governed_reader_ast_sha256 == protocol.STATIC_GOVERNED_READER_AST_SHA256
    assert protocol.STATIC_GOVERNED_READER_BINDING == static_contract["governedReaderBinding"]
    assert protocol.STATIC_GOVERNED_READER_FORBIDDEN_BINDINGS == tuple(
        static_contract["governedReaderForbiddenBindings"]
    )
    assert protocol.STATIC_GOVERNED_READ_RESULT_FIELDS == tuple(
        static_contract["governedReadResultFields"]
    )
    assert tuple(protocol.GovernedReadResult.__dataclass_fields__) == (
        protocol.STATIC_GOVERNED_READ_RESULT_FIELDS
    )
    assert protocol.STATIC_GOVERNED_READER_STEPS == tuple(static_contract["governedReaderSteps"])
    assert protocol.STATIC_ALLOWED_GIT_FORMS == tuple(
        tuple(item) for item in static_contract["allowedGitForms"]
    )
    assert protocol.static_boundary_findings(GOVERNED_READER_SOURCE) == ()
    for attribute in (
        "STATIC_GOVERNED_READER_AST_SHA256",
        "STATIC_GOVERNED_READER_BINDING",
        "STATIC_GOVERNED_READER_FORBIDDEN_BINDINGS",
        "STATIC_GOVERNED_READ_RESULT_FIELDS",
        "STATIC_GOVERNED_READER_STEPS",
    ):
        with monkeypatch.context() as policy_patch:
            policy_patch.setattr(
                protocol,
                attribute,
                "0" * 64
                if attribute.endswith("SHA256")
                else (() if attribute.endswith(("BINDINGS", "FIELDS", "STEPS")) else ""),
            )
            assert protocol.static_boundary_findings(GOVERNED_READER_SOURCE) == finding(
                "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
            )
    binding_reader_sources = {
        "duplicate_functiondef": GOVERNED_READER_SOURCE + "\n" + GOVERNED_READER_SOURCE,
        "async_functiondef": GOVERNED_READER_SOURCE
        + "\nasync def _read_governed_bytes(root, relative):\n    return None\n",
        "classdef": GOVERNED_READER_SOURCE + "\nclass _read_governed_bytes:\n    pass\n",
        "assign": GOVERNED_READER_SOURCE + "\n_read_governed_bytes = governed_reader_alias\n",
        "annotated_assign": GOVERNED_READER_SOURCE
        + "\n_read_governed_bytes: object = governed_reader_alias\n",
        "lambda_assign": GOVERNED_READER_SOURCE
        + "\n_read_governed_bytes = lambda root, relative: governed_reader_result\n",
        "for_target": GOVERNED_READER_SOURCE + "\nfor _read_governed_bytes in ():\n    pass\n",
        "with_alias": GOVERNED_READER_SOURCE
        + "\nwith governed_reader_context as _read_governed_bytes:\n    pass\n",
        "named_expression": GOVERNED_READER_SOURCE
        + "\n(_read_governed_bytes := governed_reader_alias)\n",
        "import_alias": GOVERNED_READER_SOURCE + "\nimport ast as _read_governed_bytes\n",
        "except_handler": GOVERNED_READER_SOURCE
        + "\ntry:\n    pass\nexcept Exception as _read_governed_bytes:\n    pass\n",
        "destructuring_store": GOVERNED_READER_SOURCE
        + "\n_read_governed_bytes, other = governed_reader_alias, other\n",
        "augmented_assign": GOVERNED_READER_SOURCE
        + "\n_read_governed_bytes += governed_reader_alias\n",
        "match_capture": GOVERNED_READER_SOURCE
        + "\nmatch governed_reader_alias:\n    case _read_governed_bytes:\n        pass\n",
        "type_alias": GOVERNED_READER_SOURCE + "\ntype _read_governed_bytes = bytes\n",
        "async_for_global": GOVERNED_READER_SOURCE + "\nasync def binding_attack(stream):\n"
        "    global _read_governed_bytes\n"
        "    async for _read_governed_bytes in stream:\n"
        "        pass\n",
        "async_with_global": GOVERNED_READER_SOURCE + "\nasync def binding_attack(context):\n"
        "    global _read_governed_bytes\n"
        "    async with context as _read_governed_bytes:\n"
        "        pass\n",
        "nested_global_assign": GOVERNED_READER_SOURCE + "\ndef binding_attack():\n"
        "    global _read_governed_bytes\n"
        "    _read_governed_bytes = governed_reader_alias\n",
        "nested_global_delete": GOVERNED_READER_SOURCE + "\ndef binding_attack():\n"
        "    global _read_governed_bytes\n"
        "    del _read_governed_bytes\n",
        "delete": GOVERNED_READER_SOURCE + "\ndel _read_governed_bytes\n",
    }
    assert tuple(binding_reader_sources) == protocol.STATIC_GOVERNED_READER_FORBIDDEN_BINDINGS
    hostile_reader_sources = (
        GOVERNED_READER_SOURCE.replace(
            "def _read_governed_bytes(root: Path, relative: str) -> GovernedReadResult:",
            "def _read_governed_bytes(other_root: Path, relative: str) -> GovernedReadResult:",
        ),
        GOVERNED_READER_SOURCE.replace(
            "    if relative not in STATIC_ALLOWED_GOVERNED_READ_PATHS:\n"
            '        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.PATH_NOT_ALLOWED", relative),))\n',
            "",
        ),
        GOVERNED_READER_SOURCE.replace(
            "    governed_path = root / relative",
            "    governed_path = root / '../secret'",
        ),
        GOVERNED_READER_SOURCE.replace(
            "    root_resolved = root.resolve()",
            "    root = root / 'shadow'\n    root_resolved = root.resolve()",
        ),
        GOVERNED_READER_SOURCE.replace(
            "    if not resolved.is_relative_to(root_resolved):\n"
            '        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.OUTSIDE_ROOT", relative),))',
            "    resolved.is_relative_to(root_resolved)",
        ),
        GOVERNED_READER_SOURCE.replace(
            "        if ancestor.is_symlink():\n"
            "            location = ancestor.relative_to(root).as_posix()\n"
            '            return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.ANCESTOR_SYMLINK", location),))',
            "        ancestor.is_symlink()",
        ),
        GOVERNED_READER_SOURCE.replace(
            "    if governed_path.is_symlink():\n"
            '        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.SYMLINK", relative),))',
            "    governed_path.is_symlink()",
        ),
        GOVERNED_READER_SOURCE.replace(
            "    if not governed_path.is_file():\n"
            '        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.NONREGULAR", relative),))\n'
            "    payload = governed_path.read_bytes()",
            "    payload = governed_path.read_bytes()\n"
            "    if not governed_path.is_file():\n"
            '        return GovernedReadResult(None, (Finding("file", "CURRENT", "ACP.FILE.NONREGULAR", relative),))',
        ),
        GOVERNED_READER_SOURCE.replace(
            "    payload = governed_path.read_bytes()",
            "    payload = root.read_bytes()",
        ),
        *binding_reader_sources.values(),
    )
    assert len(set(hostile_reader_sources)) == len(hostile_reader_sources)
    for hostile_reader in hostile_reader_sources:
        assert protocol.static_boundary_findings(hostile_reader) == finding(
            "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
        )
    allowed_import_sources = {
        "__future__.annotations": "from __future__ import annotations\n",
        "ast": "import ast\n",
        "collections.abc.Callable": "from collections.abc import Callable\n",
        "collections.abc.Mapping": "from collections.abc import Mapping\n",
        "cryptography.exceptions.InvalidSignature": (
            "from cryptography.exceptions import InvalidSignature\n"
        ),
        "cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey": (
            "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey\n"
        ),
        "dataclasses.dataclass": "from dataclasses import dataclass\n",
        "enum": "import enum\n",
        "hashlib": "import hashlib\n",
        "json": "import json\n",
        "pathlib.Path": "from pathlib import Path\n",
        "subprocess": "import subprocess\n",
        "typing.Any": "from typing import Any\n",
    }
    assert tuple(allowed_import_sources) == protocol.STATIC_ALLOWED_IMPORTS
    for member, allowed_source in allowed_import_sources.items():
        assert protocol.static_boundary_findings(allowed_source) == ()
        with monkeypatch.context() as policy_patch:
            policy_patch.setattr(
                protocol,
                "STATIC_ALLOWED_IMPORTS",
                tuple(item for item in protocol.STATIC_ALLOWED_IMPORTS if item != member),
            )
            assert protocol.static_boundary_findings(allowed_source) == finding(
                "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
            )
    allowed_call_sources = {
        "Ed25519PublicKey.from_public_bytes(public_key).verify(signature,message)": (
            "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey\n"
            "Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)\n"
        ),
        "module:Path(__file__).resolve()": (
            "from pathlib import Path\nROOT = Path(__file__).resolve()\n"
        ),
        **{
            f"_read_governed_bytes(root,{relative!r})": (
                f"_read_governed_bytes(root, {relative!r})\n"
            )
            for relative in protocol.STATIC_ALLOWED_GOVERNED_READ_PATHS
        },
        "_read_governed_bytes:ancestor.is_symlink()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:governed_path.is_symlink()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:governed_path.exists()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:governed_path.is_file()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:governed_path.resolve()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:root.resolve()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:resolved.is_relative_to(root_resolved)": (GOVERNED_READER_SOURCE),
        "_read_governed_bytes:ancestor.relative_to(root).as_posix()": (GOVERNED_READER_SOURCE),
        "_read_governed_bytes:governed_path.read_bytes()": GOVERNED_READER_SOURCE,
        "_read_governed_bytes:Finding(file,CURRENT,exact-code,exact-location)": (
            GOVERNED_READER_SOURCE
        ),
        "_read_governed_bytes:GovernedReadResult(payload,findings)": (GOVERNED_READER_SOURCE),
        "ast.parse(source)": "import ast\nast.parse(source)\n",
        "ast.dump(node,annotate_fields=True,include_attributes=False)": (
            "import ast\nast.dump(node, annotate_fields=True, include_attributes=False)\n"
        ),
        "bytes.decode(utf-8)": "payload.decode('utf-8')\n",
        "bytes.fromhex(hex)": "bytes.fromhex(value)\n",
        "bytes.hex()": "payload.hex()\n",
        "hashlib.sha256(bytes)": "import hashlib\nhashlib.sha256(payload)\n",
        "json.loads(text,object_pairs_hook=closed)": (
            "import json\njson.loads(text, object_pairs_hook=closed)\n"
        ),
        "str.encode(utf-8)": "value.encode('utf-8')\n",
        "subprocess.run(exact_read_only_git,cwd=root,check=exact,capture_output=True,text=True)": (
            "import subprocess\nsubprocess.run(('git', 'rev-parse', 'HEAD'), "
            "cwd=root, check=True, capture_output=True, text=True)\n"
        ),
    }
    assert tuple(allowed_call_sources) == protocol.STATIC_ALLOWED_CALL_SHAPES
    for member, allowed_source in allowed_call_sources.items():
        assert protocol.static_boundary_findings(allowed_source) == ()
        with monkeypatch.context() as policy_patch:
            policy_patch.setattr(
                protocol,
                "STATIC_ALLOWED_CALL_SHAPES",
                tuple(item for item in protocol.STATIC_ALLOWED_CALL_SHAPES if item != member),
            )
            assert protocol.static_boundary_findings(allowed_source) == finding(
                "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
            )
    for relative in protocol.STATIC_ALLOWED_GOVERNED_READ_PATHS:
        allowed_source = f"_read_governed_bytes(root, {relative!r})\n"
        with monkeypatch.context() as policy_patch:
            policy_patch.setattr(
                protocol,
                "STATIC_ALLOWED_GOVERNED_READ_PATHS",
                tuple(
                    item for item in protocol.STATIC_ALLOWED_GOVERNED_READ_PATHS if item != relative
                ),
            )
            assert protocol.static_boundary_findings(allowed_source) == finding(
                "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
            )
    with monkeypatch.context() as policy_patch:
        policy_patch.setattr(protocol, "STATIC_ALLOWED_GIT_FORMS", ())
        assert protocol.static_boundary_findings(read_only_git.splitlines()[1] + "\n") == finding(
            "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
        )
    for hostile, code in (
        ("import requests\n", "ACP.STATIC.NETWORK_IMPORT"),
        ("import aiohttp\n", "ACP.STATIC.NETWORK_IMPORT"),
        ("import urllib3\n", "ACP.STATIC.NETWORK_IMPORT"),
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
        ("Path('/etc/passwd').read_bytes()\n", "ACP.STATIC.CREDENTIAL_ACCESS"),
        (
            "_read_governed_bytes(root, '../../.ssh/id_ed25519')\n",
            "ACP.STATIC.CREDENTIAL_ACCESS",
        ),
        ("_read_governed_bytes(root, relative)\n", "ACP.STATIC.NOT_ALLOWLISTED"),
        (
            "_read_governed_bytes(other_root, "
            "'docs/governance/adversarial-convergence-invariant-matrix-v1.json')\n",
            "ACP.STATIC.NOT_ALLOWLISTED",
        ),
        ("(root / '../secret').read_bytes()\n", "ACP.STATIC.NOT_ALLOWLISTED"),
        ("(root / relative).read_bytes()\n", "ACP.STATIC.NOT_ALLOWLISTED"),
        ("governed_path.read_bytes()\n", "ACP.STATIC.NOT_ALLOWLISTED"),
        ("import io\nio.open('state', mode='w')\n", "ACP.STATIC.WRITE"),
        ("from builtins import open as persist\npersist('state', 'w')\n", "ACP.STATIC.WRITE"),
        ("Path('state').write_text('x')\n", "ACP.STATIC.WRITE"),
        ("Path('state').write_bytes(b'x')\n", "ACP.STATIC.WRITE"),
        ("Path('state').open(mode='w')\n", "ACP.STATIC.WRITE"),
        ("Path('state').touch()\n", "ACP.STATIC.WRITE"),
        ("Path('state').rename('other')\n", "ACP.STATIC.WRITE"),
        ("Path('state').replace('other')\n", "ACP.STATIC.WRITE"),
        ("Path('state').unlink()\n", "ACP.STATIC.WRITE"),
        ("os.open('state', os.O_WRONLY)\n", "ACP.STATIC.WRITE"),
        ("os.write(fd, b'x')\n", "ACP.STATIC.WRITE"),
        ("tempfile.NamedTemporaryFile()\n", "ACP.STATIC.PERSISTENCE"),
        ("os.getenv('TOKEN')\n", "ACP.STATIC.CREDENTIAL_ACCESS"),
        ("shutil.copyfile('a', 'b')\n", "ACP.STATIC.PERSISTENCE"),
        ("sqlite3.connect('state.db')\n", "ACP.STATIC.PERSISTENCE"),
        ("subprocess.run(['curl', 'https://example.invalid'])\n", "ACP.STATIC.PROCESS"),
        ("from subprocess import run as execute\nexecute(command)\n", "ACP.STATIC.PROCESS"),
        (
            "import subprocess as sp\nsp.run(('git', 'rev-parse', 'HEAD'))\n",
            "ACP.STATIC.PROCESS",
        ),
        (
            "import subprocess\ngetattr(subprocess, 'run')(('git', 'rev-parse', 'HEAD'))\n",
            "ACP.STATIC.PROCESS",
        ),
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
            "import ast\nast.dump(node, annotate_fields=False, include_attributes=False)\n",
            "ACP.STATIC.NOT_ALLOWLISTED",
        ),
        (
            "import ast\nast.dump(node, annotate_fields=True, include_attributes=True)\n",
            "ACP.STATIC.NOT_ALLOWLISTED",
        ),
        ("import ast\nast.dump(node)\n", "ACP.STATIC.NOT_ALLOWLISTED"),
        (
            "subprocess.run(('git', 'rev-parse', 'HEAD'), cwd=dynamic_root)\n",
            "ACP.STATIC.GIT_DYNAMIC",
        ),
        ("subprocess.run(('git', command, 'HEAD'))\n", "ACP.STATIC.GIT_DYNAMIC"),
    ):
        assert protocol.static_boundary_findings(hostile) == finding("static", code, "source")

    allowed_argv = (
        ("git", "rev-parse", "HEAD"),
        ("git", "rev-list", "--ancestry-path", "--reverse", "red-head..HEAD"),
        ("git", "rev-list", "--parents", "-n", "1", "c3-head"),
        ("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "c3-head"),
        (
            "git",
            "rev-parse",
            "red-head^{tree}",
            "red-head:docs/governance/adversarial-convergence-invariant-matrix-v1.json",
            "red-head:tests/unit/test_issue435_adversarial_convergence.py",
            "red-head:tests/unit/test_issue435_adversarial_convergence_repository.py",
        ),
        (
            "git",
            "show",
            "c3-head:docs/governance/adversarial-convergence-red-freeze-v1.json",
        ),
        ("git", "merge-base", "--is-ancestor", "red-head", "HEAD"),
        ("git", "show", "-s", "--format=%ae", "red-head"),
        ("git", "cat-file", "-e", "red-head"),
    )
    for argv in allowed_argv:
        variants = [argv[:-1], (*argv, "--extra"), (*argv[:-1], "wrong-token")]
        if len(argv) > 3:
            reordered = list(argv)
            reordered[-1], reordered[-2] = reordered[-2], reordered[-1]
            variants.append(tuple(reordered))
        for variant in variants:
            check = argv[1] != "merge-base"
            source = (
                "import subprocess\n"
                f"subprocess.run({variant!r}, cwd=root, check={check!r}, "
                "capture_output=True, text=True)\n"
            )
            assert protocol.static_boundary_findings(source) == finding(
                "static", "ACP.STATIC.GIT_FORBIDDEN", "source"
            )
    allowed_expressions = (
        ("('git', 'rev-parse', 'HEAD')", True),
        ("('git', 'rev-list', '--ancestry-path', '--reverse', f'{red_head}..HEAD')", True),
        ("('git', 'rev-list', '--parents', '-n', '1', c3_head)", True),
        ("('git', 'diff-tree', '--no-commit-id', '--name-only', '-r', c3_head)", True),
        (
            "('git', 'rev-parse', f'{red_head}^{{tree}}', "
            "f'{red_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', "
            "f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', "
            "f'{red_head}:tests/unit/test_issue435_adversarial_convergence_repository.py')",
            True,
        ),
        (
            "('git', 'show', "
            "f'{c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json')",
            True,
        ),
        ("('git', 'merge-base', '--is-ancestor', red_head, 'HEAD')", False),
        ("('git', 'show', '-s', '--format=%ae', red_head)", True),
        ("('git', 'cat-file', '-e', red_head)", True),
    )
    for form_index, (expression, check) in enumerate(allowed_expressions):
        exact = f"cwd=root, check={check!r}, capture_output=True, text=True"
        allowed_source = f"import subprocess\nsubprocess.run({expression}, {exact})\n"
        assert protocol.static_boundary_findings(allowed_source) == ()
        with monkeypatch.context() as policy_patch:
            policy_patch.setattr(
                protocol,
                "STATIC_ALLOWED_GIT_FORMS",
                tuple(
                    item
                    for index, item in enumerate(protocol.STATIC_ALLOWED_GIT_FORMS)
                    if index != form_index
                ),
            )
            assert protocol.static_boundary_findings(allowed_source) == finding(
                "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
            )
        for kwargs, code in (
            ("cwd=root, capture_output=True, text=True", "ACP.STATIC.GIT_DYNAMIC"),
            (
                f"cwd=root, check={(not check)!r}, capture_output=True, text=True",
                "ACP.STATIC.GIT_FORBIDDEN",
            ),
            (f"cwd=root, check={check!r}, text=True", "ACP.STATIC.GIT_DYNAMIC"),
            (
                f"cwd=root, check={check!r}, capture_output=False, text=True",
                "ACP.STATIC.GIT_DYNAMIC",
            ),
            (f"cwd=root, check={check!r}, capture_output=True", "ACP.STATIC.GIT_DYNAMIC"),
            (
                f"cwd=root, check={check!r}, capture_output=True, text=False",
                "ACP.STATIC.GIT_DYNAMIC",
            ),
            (f"{exact}, timeout=1", "ACP.STATIC.GIT_DYNAMIC"),
            (f"{exact}, env=environment", "ACP.STATIC.GIT_DYNAMIC"),
            (f"{exact}, shell=True", "ACP.STATIC.PROCESS"),
            (
                f"check={check!r}, capture_output=True, text=True, cwd=dynamic_root",
                "ACP.STATIC.GIT_DYNAMIC",
            ),
        ):
            source = f"import subprocess\nsubprocess.run({expression}, {kwargs})\n"
            assert protocol.static_boundary_findings(source) == finding("static", code, "source")
        for source in (
            f"import subprocess\nargv = {expression}\nsubprocess.run(argv, {exact})\n",
            f"import subprocess\nrunner = subprocess.run\nrunner({expression}, {exact})\n",
            f"import subprocess\nsubprocess.run(args={expression}, {exact})\n",
            f"import subprocess\nsubprocess.run((*{expression},), {exact})\n",
        ):
            assert protocol.static_boundary_findings(source) == finding(
                "static", "ACP.STATIC.GIT_DYNAMIC", "source"
            )
    for changed_expression in (
        "('git', 'rev-list', '--ancestry-path', '--reverse', f'{other_head}..HEAD')",
        "('git', 'rev-list', '--ancestry-path', '--reverse', f'{red_head!s}..HEAD')",
        "('git', 'rev-list', '--parents', '-n', '1', other_c3_head)",
        "('git', 'diff-tree', '--no-commit-id', '--name-only', '-r', other_c3_head)",
        "('git', 'rev-parse', f'{red_head}^{commit}', f'{red_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial-convergence_repository.py')",
        "('git', 'rev-parse', f'{red_head}^{tree}', f'{other_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', f'{red_head}:tests/unit/test_issue435_adversarial-convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial-convergence_repository.py')",
        "('git', 'rev-parse', f'{red_head}^{tree}', f'{red_head}:docs/{matrix_name}', f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial_convergence_repository.py')",
        "('git', 'show', f'{other_c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json')",
        "('git', 'show', f'{c3_head}:docs/governance/{freeze_name}')",
    ):
        source = (
            "import subprocess\n"
            f"subprocess.run({changed_expression}, cwd=root, check=True, "
            "capture_output=True, text=True)\n"
        )
        assert protocol.static_boundary_findings(source) == finding(
            "static", "ACP.STATIC.GIT_DYNAMIC", "source"
        )
    for aliased_source, code in (
        (
            "from pathlib import Path as P\nP('state').write_text('x')\n",
            "ACP.STATIC.WRITE",
        ),
        (
            "from shutil import rmtree as erase\nerase('state')\n",
            "ACP.STATIC.PERSISTENCE",
        ),
        (
            "from os import remove as erase\nerase('state')\n",
            "ACP.STATIC.WRITE",
        ),
        (
            "from asyncio import create_subprocess_exec as launch\nlaunch('git', 'status')\n",
            "ACP.STATIC.PROCESS",
        ),
    ):
        assert protocol.static_boundary_findings(aliased_source) == finding(
            "static", code, "source"
        )
    for unknown_source in (
        "import math\n",
        "mystery_call()\n",
        "client.send(payload)\n",
        "getattr(client, method)(payload)\n",
    ):
        assert protocol.static_boundary_findings(unknown_source) == finding(
            "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
        )


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
    freeze_raw = canonical(freeze) + b"\n"
    freeze_at_cap = freeze_raw + b" " * (32768 - len(freeze_raw))
    freeze_path.write_bytes(freeze_at_cap)
    assert protocol.route_findings(root) != finding("bounds", "ACP.BOUNDS.FREEZE_BYTES", "freeze")
    freeze_path.write_bytes(freeze_at_cap + b" ")
    assert protocol.route_findings(root) == finding("bounds", "ACP.BOUNDS.FREEZE_BYTES", "freeze")
    matrix_path = root / protocol.MATRIX_PATH.relative_to(protocol.ROOT)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix_raw = matrix_path.read_bytes()
    matrix_at_cap = matrix_raw + b" " * (65536 - len(matrix_raw))
    matrix_path.write_bytes(matrix_at_cap)
    freeze_path.write_bytes(freeze_raw)
    assert protocol.route_findings(root) != finding("bounds", "ACP.BOUNDS.MATRIX_BYTES", "matrix")
    matrix_path.write_bytes(matrix_at_cap + b" ")
    assert protocol.route_findings(root) == finding("bounds", "ACP.BOUNDS.MATRIX_BYTES", "matrix")
    for field, limit_value, code, finding_location in (
        ("findingCount", 33, "ACP.BOUNDS.FINDING_COUNT", "findings"),
        ("retainedMaterialCount", 5, "ACP.BOUNDS.RETAINED_COUNT", "retained-materials"),
    ):
        changed_matrix = deepcopy(matrix)
        changed_matrix["limits"][field] = limit_value
        matrix_path.write_bytes(canonical(changed_matrix) + b"\n")
        assert protocol.route_findings(root) == finding("bounds", code, finding_location)
    changed_matrix = deepcopy(matrix)
    assert len(changed_matrix["caseIndex"]) == 130
    changed_matrix["caseIndex"].append("unknown:overflow")
    matrix_path.write_bytes(canonical(changed_matrix) + b"\n")
    assert protocol.route_findings(root) == finding("bounds", "ACP.BOUNDS.MATRIX_ROWS", "caseIndex")
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
