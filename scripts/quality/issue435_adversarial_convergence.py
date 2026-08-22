#!/usr/bin/env python3
"""Issue #435 adversarial convergence contract.

C2 RED skeleton. Public functions return exact typed NOT_IMPLEMENTED results so
the fixed tests fail on absent behavior rather than imports or exceptions.
"""

from __future__ import annotations

import enum
import errno  # noqa: F401 - frozen RED race classification surface.
import os  # noqa: F401 - frozen RED import surface for repository discovery.
import stat  # noqa: F401 - frozen RED import surface for no-follow type checks.
import subprocess  # noqa: F401 - frozen RED process boundary for exact Git evidence.
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs/governance/adversarial-convergence-invariant-matrix-v1.json"
FREEZE_PATH = ROOT / "docs/governance/adversarial-convergence-red-freeze-v1.json"
ACTIVATION = "NONE"
AUTHORITY_EFFECT = "NO_AUTHORITY_EFFECT"
EXPECTED_RED_FAILURES_COUNT = 36
EXPECTED_RED_FAILURES_SHA256 = "0b808d20a985f7cf38d7403a937669bd2da5493acc90dcd698fe20dc742fe2e3"
STATIC_ALLOWED_IMPORTS = (
    "__future__.annotations",
    "ast",
    "collections.abc.Callable",
    "collections.abc.Mapping",
    "cryptography.exceptions.InvalidSignature",
    "cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey",
    "dataclasses.dataclass",
    "enum",
    "errno",
    "hashlib",
    "json",
    "os",
    "pathlib.Path",
    "stat",
    "subprocess",
    "typing.Any",
)
STATIC_ALLOWED_CALL_SHAPES = (
    "Ed25519PublicKey.from_public_bytes(public_key).verify(signature,message)",
    "module:Path(__file__).resolve()",
    "_read_governed_bytes(root,'docs/governance/adversarial-convergence-invariant-matrix-v1.json')",
    "_read_governed_bytes(root,'docs/governance/adversarial-convergence-red-freeze-v1.json')",
    "_read_governed_bytes(root,'tests/unit/test_issue435_adversarial_convergence.py')",
    "_read_governed_bytes(root,'tests/unit/test_issue435_adversarial_convergence_repository.py')",
    "_read_governed_bytes:ancestor.is_symlink()",
    "_read_governed_bytes:governed_path.is_symlink()",
    "_read_governed_bytes:governed_path.exists()",
    "_read_governed_bytes:governed_path.is_file()",
    "_read_governed_bytes:governed_path.resolve()",
    "_read_governed_bytes:root.resolve()",
    "_read_governed_bytes:resolved.is_relative_to(root_resolved)",
    "_read_governed_bytes:ancestor.relative_to(root).as_posix()",
    "_read_governed_bytes:governed_path.read_bytes()",
    "_read_governed_bytes:Finding(file,CURRENT,exact-code,exact-location)",
    "_read_governed_bytes:GovernedReadResult(payload,findings)",
    "ast.parse(source)",
    "ast.dump(node,annotate_fields=True,include_attributes=False)",
    "bytes.decode(utf-8)",
    "bytes.fromhex(hex)",
    "bytes.hex()",
    "hashlib.sha256(bytes)",
    "json.loads(text,object_pairs_hook=closed)",
    "Path.as_posix()",
    "str.encode(utf-8)",
    "git-metadata:exact-reader-and-discovery-ast",
    "subprocess.run(exact_read_only_git,cwd=root,check=False,exact-streams,text=False,exact-timeout,direct-literal-env)",
)
STATIC_ALLOWED_GOVERNED_READ_PATHS = (
    "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
    "docs/governance/adversarial-convergence-red-freeze-v1.json",
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
)
STATIC_GOVERNED_READER_AST_SHA256 = (
    "c3736cb8403e1ffd63d808cabf0f7289055c3b1691f39164bfe48c475c21724d"
)
STATIC_GOVERNED_READER_BINDING = "one_top_level_functiondef_no_other_binding_or_delete"
STATIC_GOVERNED_READER_FORBIDDEN_BINDINGS = (
    "duplicate_functiondef",
    "async_functiondef",
    "classdef",
    "assign",
    "annotated_assign",
    "lambda_assign",
    "for_target",
    "with_alias",
    "named_expression",
    "import_alias",
    "except_handler",
    "destructuring_store",
    "augmented_assign",
    "match_capture",
    "type_alias",
    "async_for_global",
    "async_with_global",
    "nested_global_assign",
    "nested_global_delete",
    "delete",
)
STATIC_GOVERNED_READ_RESULT_FIELDS = ("payload", "findings")
STATIC_GOVERNED_READER_STEPS = (
    "signature(root:Path,relative:str)->GovernedReadResult",
    "guard-relative-in-exact-allowlist",
    "derive-governed-path-from-root-and-relative",
    "resolve-validated-root",
    "iterate-every-non-root-ancestor",
    "return-exact-ancestor-symlink-finding",
    "return-exact-target-symlink-finding",
    "resolve-governed-path",
    "return-exact-outside-root-finding",
    "return-exact-missing-finding",
    "return-exact-nonregular-finding",
    "read-derived-governed-path",
    "return-exact-binary-finding",
    "return-typed-payload",
)
STATIC_GIT_PREFIX = (
    "/usr/bin/git",
    "--no-pager",
    "--no-replace-objects",
    "--no-optional-locks",
    "--no-lazy-fetch",
    "-c",
    "protocol.allow=never",
    "-c",
    "core.commitGraph=false",
    "-c",
    "log.showSignature=false",
    "-c",
    "fsck.skipList=/dev/null",
)
STATIC_GIT_ENV_CONTRACT = (
    ("LC_ALL", "C"),
    ("GIT_CONFIG_NOSYSTEM", "1"),
    ("GIT_CONFIG_GLOBAL", "/dev/null"),
    ("GIT_NO_LAZY_FETCH", "1"),
    ("GIT_NO_REPLACE_OBJECTS", "1"),
    ("GIT_OPTIONAL_LOCKS", "0"),
    ("GIT_TERMINAL_PROMPT", "0"),
    ("GIT_DIR", "derived_git_dir"),
    ("GIT_COMMON_DIR", "derived_common_dir"),
    ("GIT_WORK_TREE", "derived_root"),
)
STATIC_GIT_FILESYSTEM_THREAT_MODEL = (
    ("scope", "stable_local_filesystem_metadata_and_object_snapshot_for_full_validator_invocation"),
    (
        "proofs",
        (
            "fail_closed_parsing",
            "descriptor_relative_no_follow_traversal",
            "reader_local_inode_continuity",
            "prohibited_metadata_absence_at_validated_read_points",
            "exact_path_based_git_object_evidence_under_snapshot_assumption",
        ),
    ),
    (
        "defenseInDepth",
        (
            "reader_local_lstat_open_fstat_postread_replacement_detection",
            "final_dot_git_linked_git_dir_common_dir_revalidation",
        ),
    ),
    ("gitProcessBinding", "path_based_absolute_git_with_explicit_git_dir_common_dir_work_tree"),
    (
        "excludedThreat",
        "concurrent_out_of_process_mutation_after_validated_descriptor_close_before_or_during_path_based_git_reopen",
    ),
    (
        "claimsNotMade",
        (
            "race_free_validation",
            "atomic_check_to_use",
            "descriptor_bound_git_subprocess",
            "detection_or_prevention_of_concurrent_repository_mutation",
        ),
    ),
    ("strongerClaimDisposition", "EVIDENCE_BLOCKER"),
)
STATIC_GIT_FILESYSTEM_THREAT_MODEL_FINDINGS = (
    (
        "scope",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.scope",
    ),
    (
        "proofs",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.proofs",
    ),
    (
        "defenseInDepth",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.defenseInDepth",
    ),
    (
        "gitProcessBinding",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.gitProcessBinding",
    ),
    (
        "excludedThreat",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.excludedThreat",
    ),
    (
        "claimsNotMade",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.claimsNotMade",
    ),
    (
        "strongerClaimDisposition",
        "ACP.MATRIX.FILESYSTEM_THREAT_MODEL_MISMATCH",
        "staticBoundaryContract.gitEvidenceContract.filesystemThreatModel.strongerClaimDisposition",
    ),
)
STATIC_GIT_DOCUMENTATION_CLAIM_CONTRACT = (
    ("validator", "filesystem_threat_document_findings"),
    ("blockStart", "<!-- issue-435-filesystem-snapshot-boundary:start -->"),
    ("blockEnd", "<!-- issue-435-filesystem-snapshot-boundary:end -->"),
    (
        "approvedBlockSha256",
        (
            (
                "docs/ADR/0064-adversarial-convergence-protocol.md",
                "1e9c8e1ef77f7583da58edd6263d1bec851517206daa25edefd3ba55d935579e",
            ),
            (
                "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
                "4d2661cac412e05b3e051d34a2e95f7f42d4c9de27792325dcceabbb397ae208",
            ),
            (
                "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
                "cd8d7b6c24e43689f8aff316f7f9fe4f04e9409b231ecd526cf0eea9b62ebc8f",
            ),
        ),
    ),
    (
        "prohibitedClaimFamilies",
        (
            "race_free_validation",
            "atomic_check_to_use",
            "descriptor_bound_git_subprocess",
            "detection_or_prevention_of_all_concurrent_repository_mutation",
        ),
    ),
    (
        "normalization",
        (
            "ascii-lowercase",
            "remove-markdown-emphasis-asterisk-underscore-backtick",
            "collapse-whitespace-and-hyphen-runs-to-space",
            "strip-leading-and-trailing-space",
        ),
    ),
    (
        "variantAxes",
        (
            "case",
            "whitespace",
            "hyphen",
            "markdown",
            "bounded-synonym",
            "case+markdown+hyphen",
            "bounded-synonym+markdown+hyphen",
            "backtick-only",
            "edge-whitespace-only",
            "case+markdown+hyphen+backtick+edge-whitespace",
            "bounded-synonym+markdown+hyphen+backtick+edge-whitespace",
        ),
    ),
    (
        "prohibitedFamilyGrammar",
        (
            (
                "race_free_validation",
                ("repository validation is race free", "validator is free of races"),
            ),
            (
                "atomic_check_to_use",
                (
                    "repository validation is an atomic check to use operation",
                    "validation is atomic between check and use",
                ),
            ),
            (
                "descriptor_bound_git_subprocess",
                (
                    "git subprocess evidence is descriptor bound",
                    "git process evidence is bound to descriptors",
                ),
            ),
            (
                "detection_or_prevention_of_all_concurrent_repository_mutation",
                (
                    "validator detects and prevents all concurrent repository mutation",
                    "all concurrent repository changes are detected and prevented",
                ),
            ),
        ),
    ),
    ("variantCount", 44),
    (
        "variantSha256",
        "9a6f83544ddc8e595861d2cd3d7b0a8d24fac7b75e5d61024868e222d561f3b8",
    ),
    (
        "normalizerMutantFields",
        ("mutantId", "hostileAxis"),
    ),
    (
        "normalizerMutants",
        (
            (
                "omit-backtick-removal",
                "backtick-only",
            ),
            (
                "omit-final-strip",
                "edge-whitespace-only",
            ),
        ),
    ),
    ("normalizerMutantCount", 2),
    (
        "normalizerMutantSha256",
        "b365ac98f1bcdf8501259e4a39c5441ab60cb24a8a0f66c21d921ee28fbbec96",
    ),
    (
        "findingContracts",
        (
            ("block", "ACP.DOC.THREAT_MODEL_BLOCK"),
            ("overclaim", "ACP.DOC.THREAT_MODEL_OVERCLAIM"),
        ),
    ),
    ("location", "governed-document-path"),
)
STATIC_GIT_METADATA_TARGETS = (
    "info/grafts",
    "shallow",
    "objects/info/alternates",
    "objects/info/http-alternates",
)
STATIC_GIT_METADATA_ROLE_SPECS = (
    ("dot_git", "directory_or_regular_record", 4096, ".git", "root/.git"),
    ("linked_git_dir", "directory", 0, ".git.gitdir", "dot_git_record.gitdir"),
    ("backlink", "regular_record", 4096, "git-dir/gitdir", "linked_git_dir/gitdir"),
    ("commondir", "regular_record", 4096, "git-dir/commondir", "linked_git_dir/commondir"),
    ("common_dir", "directory", 0, "common-dir", "linked_git_dir.parent.parent"),
    ("prohibited_grafts", "prohibited_absent", 0, "info/grafts", "common_dir/info/grafts"),
    ("prohibited_shallow", "prohibited_absent", 0, "shallow", "common_dir/shallow"),
    (
        "prohibited_alternates",
        "prohibited_absent",
        0,
        "objects/info/alternates",
        "common_dir/objects/info/alternates",
    ),
    (
        "prohibited_http_alternates",
        "prohibited_absent",
        0,
        "objects/info/http-alternates",
        "common_dir/objects/info/http-alternates",
    ),
)
STATIC_GIT_METADATA_RECORD_FIELDS = (
    "path",
    "payload",
    "mode",
    "device",
    "inode",
    "ancestor_records",
)
STATIC_GIT_METADATA_READER_AST_SHA256 = (
    "863b27de1ca08e6c3eed30cfea241234d30ddf61cdf51452b91529cca654d2ee"
)
STATIC_GIT_METADATA_DISCOVERY_AST_SHA256 = (
    "3971ba54da0ad93e2f48842bf07fbb0fa26cf265e60494a319b2ee66e79f2913"
)
STATIC_GIT_METADATA_BINDING = "one_top_level_sync_function_each_no_alias_rebind_or_delete"
STATIC_GIT_METADATA_FINDINGS = (
    ("missing", "ACP.GIT_METADATA.MISSING"),
    ("ancestor_symlink", "ACP.GIT_METADATA.ANCESTOR_SYMLINK"),
    ("target_symlink", "ACP.GIT_METADATA.TARGET_SYMLINK"),
    ("wrong_type", "ACP.GIT_METADATA.WRONG_TYPE"),
    ("byte_cap", "ACP.GIT_METADATA.BYTE_CAP"),
    ("io_error", "ACP.GIT_METADATA.IO_ERROR"),
    ("invalid_utf8", "ACP.GIT_METADATA.INVALID_UTF8"),
    ("line_count", "ACP.GIT_METADATA.LINE_COUNT"),
    ("record_shape", "ACP.GIT_METADATA.RECORD_SHAPE"),
    ("read_type", "ACP.GIT_METADATA.READ_TYPE"),
    ("nonabsolute", "ACP.GIT_METADATA.NONABSOLUTE"),
    ("containment", "ACP.GIT_METADATA.CONTAINMENT"),
    ("layout", "ACP.GIT_METADATA.LAYOUT"),
    ("backlink_mismatch", "ACP.GIT_METADATA.BACKLINK_MISMATCH"),
    ("commondir_mismatch", "ACP.GIT_METADATA.COMMONDIR_MISMATCH"),
    ("identity_changed", "ACP.GIT_METADATA.IDENTITY_CHANGED"),
    ("prohibited", "ACP.GIT_METADATA.PROHIBITED"),
)
STATIC_GIT_METADATA_CASES = (
    ("conventional-positive", "public", "conventional", "dot_git", "directory", None, ".git"),
    ("linked-positive", "public", "linked", "linked_git_dir", "registered", None, ".git.gitdir"),
    (
        "root-nonabsolute",
        "public",
        "root",
        "dot_git",
        "relative-root",
        "ACP.GIT_METADATA.NONABSOLUTE",
        "root",
    ),
    (
        "root-dotdot",
        "public",
        "root",
        "dot_git",
        "root-dotdot",
        "ACP.GIT_METADATA.NONABSOLUTE",
        "root",
    ),
    ("root-dot", "public", "root", "dot_git", "root-dot", "ACP.GIT_METADATA.NONABSOLUTE", "root"),
    (
        "root-repeated-separator",
        "public",
        "root",
        "dot_git",
        "root-repeated-separator",
        "ACP.GIT_METADATA.NONABSOLUTE",
        "root",
    ),
    (
        "root-trailing-separator",
        "public",
        "root",
        "dot_git",
        "root-trailing-separator",
        "ACP.GIT_METADATA.NONABSOLUTE",
        "root",
    ),
    (
        "dot-git-missing",
        "public",
        "conventional",
        "dot_git",
        "missing",
        "ACP.GIT_METADATA.MISSING",
        ".git",
    ),
    (
        "dot-git-target-symlink",
        "public",
        "conventional",
        "dot_git",
        "symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        ".git",
    ),
    (
        "dot-git-fifo",
        "public",
        "conventional",
        "dot_git",
        "fifo",
        "ACP.GIT_METADATA.WRONG_TYPE",
        ".git",
    ),
    (
        "dot-git-cap-n-malformed",
        "public",
        "linked",
        "dot_git",
        "4096-bytes",
        "ACP.GIT_METADATA.RECORD_SHAPE",
        ".git",
    ),
    (
        "dot-git-cap-n-plus-one",
        "public",
        "linked",
        "dot_git",
        "4097-bytes",
        "ACP.GIT_METADATA.BYTE_CAP",
        ".git",
    ),
    (
        "dot-git-invalid-utf8",
        "public",
        "linked",
        "dot_git",
        "invalid-utf8",
        "ACP.GIT_METADATA.INVALID_UTF8",
        ".git",
    ),
    (
        "dot-git-missing-lf",
        "public",
        "linked",
        "dot_git",
        "missing-lf",
        "ACP.GIT_METADATA.LINE_COUNT",
        ".git",
    ),
    (
        "dot-git-crlf",
        "public",
        "linked",
        "dot_git",
        "crlf",
        "ACP.GIT_METADATA.RECORD_SHAPE",
        ".git",
    ),
    (
        "dot-git-extra-lf",
        "public",
        "linked",
        "dot_git",
        "extra-lf",
        "ACP.GIT_METADATA.LINE_COUNT",
        ".git",
    ),
    (
        "dot-git-extra-record",
        "public",
        "linked",
        "dot_git",
        "extra-record",
        "ACP.GIT_METADATA.LINE_COUNT",
        ".git",
    ),
    (
        "dot-git-relative",
        "public",
        "linked",
        "dot_git",
        "relative-gitdir",
        "ACP.GIT_METADATA.NONABSOLUTE",
        ".git.gitdir",
    ),
    (
        "dot-git-dot-component",
        "public",
        "linked",
        "dot_git",
        "dot-component",
        "ACP.GIT_METADATA.CONTAINMENT",
        ".git.gitdir",
    ),
    (
        "dot-git-dotdot-component",
        "public",
        "linked",
        "dot_git",
        "dotdot-component",
        "ACP.GIT_METADATA.CONTAINMENT",
        ".git.gitdir",
    ),
    (
        "dot-git-empty-component",
        "public",
        "linked",
        "dot_git",
        "double-slash",
        "ACP.GIT_METADATA.CONTAINMENT",
        ".git.gitdir",
    ),
    (
        "dot-git-nul",
        "public",
        "linked",
        "dot_git",
        "nul",
        "ACP.GIT_METADATA.CONTAINMENT",
        ".git.gitdir",
    ),
    (
        "dot-git-degenerate-common-root",
        "public",
        "linked",
        "dot_git",
        "filesystem-root-common-dir",
        "ACP.GIT_METADATA.LAYOUT",
        ".git.gitdir",
    ),
    (
        "linked-layout-outside",
        "public",
        "linked",
        "dot_git",
        "outside-worktrees",
        "ACP.GIT_METADATA.LAYOUT",
        ".git.gitdir",
    ),
    (
        "linked-git-dir-target-symlink",
        "public",
        "linked",
        "linked_git_dir",
        "symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        ".git.gitdir",
    ),
    (
        "backlink-missing",
        "public",
        "linked",
        "backlink",
        "missing",
        "ACP.GIT_METADATA.MISSING",
        "git-dir/gitdir",
    ),
    (
        "backlink-directory",
        "public",
        "linked",
        "backlink",
        "directory",
        "ACP.GIT_METADATA.WRONG_TYPE",
        "git-dir/gitdir",
    ),
    (
        "backlink-fifo",
        "public",
        "linked",
        "backlink",
        "fifo",
        "ACP.GIT_METADATA.WRONG_TYPE",
        "git-dir/gitdir",
    ),
    (
        "backlink-symlink",
        "public",
        "linked",
        "backlink",
        "symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "git-dir/gitdir",
    ),
    (
        "backlink-cap-n-malformed",
        "public",
        "linked",
        "backlink",
        "4096-bytes",
        "ACP.GIT_METADATA.RECORD_SHAPE",
        "git-dir/gitdir",
    ),
    (
        "backlink-cap-n-plus-one",
        "public",
        "linked",
        "backlink",
        "4097-bytes",
        "ACP.GIT_METADATA.BYTE_CAP",
        "git-dir/gitdir",
    ),
    (
        "backlink-invalid-utf8",
        "public",
        "linked",
        "backlink",
        "invalid-utf8",
        "ACP.GIT_METADATA.INVALID_UTF8",
        "git-dir/gitdir",
    ),
    (
        "backlink-missing-lf",
        "public",
        "linked",
        "backlink",
        "missing-lf",
        "ACP.GIT_METADATA.LINE_COUNT",
        "git-dir/gitdir",
    ),
    (
        "backlink-extra-lf",
        "public",
        "linked",
        "backlink",
        "extra-lf",
        "ACP.GIT_METADATA.LINE_COUNT",
        "git-dir/gitdir",
    ),
    (
        "backlink-mismatch",
        "public",
        "linked",
        "backlink",
        "wrong-root",
        "ACP.GIT_METADATA.BACKLINK_MISMATCH",
        "git-dir/gitdir",
    ),
    (
        "commondir-missing",
        "public",
        "linked",
        "commondir",
        "missing",
        "ACP.GIT_METADATA.MISSING",
        "git-dir/commondir",
    ),
    (
        "commondir-directory",
        "public",
        "linked",
        "commondir",
        "directory",
        "ACP.GIT_METADATA.WRONG_TYPE",
        "git-dir/commondir",
    ),
    (
        "commondir-fifo",
        "public",
        "linked",
        "commondir",
        "fifo",
        "ACP.GIT_METADATA.WRONG_TYPE",
        "git-dir/commondir",
    ),
    (
        "commondir-symlink",
        "public",
        "linked",
        "commondir",
        "symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "git-dir/commondir",
    ),
    (
        "commondir-cap-n-malformed",
        "public",
        "linked",
        "commondir",
        "4096-bytes",
        "ACP.GIT_METADATA.RECORD_SHAPE",
        "git-dir/commondir",
    ),
    (
        "commondir-cap-n-plus-one",
        "public",
        "linked",
        "commondir",
        "4097-bytes",
        "ACP.GIT_METADATA.BYTE_CAP",
        "git-dir/commondir",
    ),
    (
        "commondir-invalid-utf8",
        "public",
        "linked",
        "commondir",
        "invalid-utf8",
        "ACP.GIT_METADATA.INVALID_UTF8",
        "git-dir/commondir",
    ),
    (
        "commondir-missing-lf",
        "public",
        "linked",
        "commondir",
        "missing-lf",
        "ACP.GIT_METADATA.LINE_COUNT",
        "git-dir/commondir",
    ),
    (
        "commondir-extra-lf",
        "public",
        "linked",
        "commondir",
        "extra-lf",
        "ACP.GIT_METADATA.LINE_COUNT",
        "git-dir/commondir",
    ),
    (
        "commondir-mismatch",
        "public",
        "linked",
        "commondir",
        "wrong-relative",
        "ACP.GIT_METADATA.COMMONDIR_MISMATCH",
        "git-dir/commondir",
    ),
    (
        "root-symlink",
        "public",
        "both",
        "dot_git",
        "root-symlink",
        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
        "root",
    ),
    (
        "pre-root-symlink",
        "public",
        "both",
        "dot_git",
        "pre-root-symlink",
        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
        "root",
    ),
    (
        "root-replacement",
        "public",
        "both",
        "dot_git",
        "root-lstat-open-race",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "root",
    ),
    (
        "pre-root-replacement",
        "public",
        "both",
        "dot_git",
        "pre-root-lstat-open-race",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "root",
    ),
    (
        "ancestor-replacement",
        "public",
        "both",
        "prohibited_grafts",
        "ancestor-lstat-open-race",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "info",
    ),
    (
        "between-read-conventional-dot-git",
        "public",
        "conventional",
        "common_dir",
        "replace-dot-git-before-common-read",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    (
        "between-read-linked-directory",
        "public",
        "linked",
        "backlink",
        "replace-linked-dir-before-backlink",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git.gitdir",
    ),
    (
        "between-read-common-directory",
        "public",
        "linked",
        "prohibited_grafts",
        "replace-common-dir-before-prohibited-read",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "common-dir",
    ),
    (
        "between-read-linked-common-directory",
        "public",
        "linked",
        "common_dir",
        "replace-common-dir-before-common-read",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "common-dir",
    ),
    (
        "final-binding-revalidation",
        "public",
        "conventional",
        "dot_git",
        "replace-dot-git-before-final-revalidation",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    (
        "leaf-replacement",
        "public",
        "both",
        "dot_git",
        "leaf-lstat-open-race",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    (
        "fstat-device",
        "public",
        "both",
        "dot_git",
        "device-drift",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    (
        "fstat-inode",
        "public",
        "both",
        "dot_git",
        "inode-drift",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    (
        "fstat-type",
        "public",
        "both",
        "dot_git",
        "type-drift",
        "ACP.GIT_METADATA.WRONG_TYPE",
        ".git",
    ),
    (
        "post-read-type",
        "public",
        "linked",
        "dot_git",
        "post-type-drift",
        "ACP.GIT_METADATA.WRONG_TYPE",
        ".git",
    ),
    (
        "post-read-device",
        "public",
        "linked",
        "dot_git",
        "post-device-drift",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    (
        "post-read-inode",
        "public",
        "linked",
        "dot_git",
        "post-inode-drift",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        ".git",
    ),
    ("short-read", "direct", "linked", "dot_git", "one-byte-to-eof", None, ".git"),
    ("read-type", "public", "linked", "dot_git", "non-bytes", "ACP.GIT_METADATA.READ_TYPE", ".git"),
    (
        "lstat-error",
        "public",
        "both",
        "dot_git",
        "lstat-oserror",
        "ACP.GIT_METADATA.IO_ERROR",
        ".git",
    ),
    (
        "open-error",
        "public",
        "both",
        "dot_git",
        "open-oserror",
        "ACP.GIT_METADATA.IO_ERROR",
        ".git",
    ),
    (
        "read-error",
        "public",
        "linked",
        "dot_git",
        "read-oserror",
        "ACP.GIT_METADATA.IO_ERROR",
        ".git",
    ),
    (
        "close-error",
        "public",
        "both",
        "dot_git",
        "close-oserror",
        "ACP.GIT_METADATA.IO_ERROR",
        ".git",
    ),
    ("reverse-close", "direct", "linked", "dot_git", "reverse-once", None, ".git"),
    (
        "grafts-file",
        "public",
        "both",
        "prohibited_grafts",
        "file",
        "ACP.GIT_METADATA.PROHIBITED",
        "info/grafts",
    ),
    (
        "grafts-directory",
        "public",
        "both",
        "prohibited_grafts",
        "directory",
        "ACP.GIT_METADATA.PROHIBITED",
        "info/grafts",
    ),
    (
        "grafts-fifo",
        "public",
        "both",
        "prohibited_grafts",
        "fifo",
        "ACP.GIT_METADATA.PROHIBITED",
        "info/grafts",
    ),
    (
        "grafts-live-symlink",
        "public",
        "both",
        "prohibited_grafts",
        "live-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "info/grafts",
    ),
    (
        "grafts-broken-symlink",
        "public",
        "both",
        "prohibited_grafts",
        "broken-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "info/grafts",
    ),
    (
        "grafts-ancestor-symlink",
        "public",
        "both",
        "prohibited_grafts",
        "info-symlink",
        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
        "info",
    ),
    (
        "shallow-file",
        "public",
        "both",
        "prohibited_shallow",
        "file",
        "ACP.GIT_METADATA.PROHIBITED",
        "shallow",
    ),
    (
        "shallow-directory",
        "public",
        "both",
        "prohibited_shallow",
        "directory",
        "ACP.GIT_METADATA.PROHIBITED",
        "shallow",
    ),
    (
        "shallow-fifo",
        "public",
        "both",
        "prohibited_shallow",
        "fifo",
        "ACP.GIT_METADATA.PROHIBITED",
        "shallow",
    ),
    (
        "shallow-live-symlink",
        "public",
        "both",
        "prohibited_shallow",
        "live-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "shallow",
    ),
    (
        "shallow-broken-symlink",
        "public",
        "both",
        "prohibited_shallow",
        "broken-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "shallow",
    ),
    (
        "alternates-file",
        "public",
        "both",
        "prohibited_alternates",
        "file",
        "ACP.GIT_METADATA.PROHIBITED",
        "objects/info/alternates",
    ),
    (
        "alternates-directory",
        "public",
        "both",
        "prohibited_alternates",
        "directory",
        "ACP.GIT_METADATA.PROHIBITED",
        "objects/info/alternates",
    ),
    (
        "alternates-fifo",
        "public",
        "both",
        "prohibited_alternates",
        "fifo",
        "ACP.GIT_METADATA.PROHIBITED",
        "objects/info/alternates",
    ),
    (
        "alternates-live-symlink",
        "public",
        "both",
        "prohibited_alternates",
        "live-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "objects/info/alternates",
    ),
    (
        "alternates-broken-symlink",
        "public",
        "both",
        "prohibited_alternates",
        "broken-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "objects/info/alternates",
    ),
    (
        "alternates-ancestor-symlink",
        "public",
        "both",
        "prohibited_alternates",
        "objects-info-symlink",
        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
        "objects/info",
    ),
    (
        "http-alternates-file",
        "public",
        "both",
        "prohibited_http_alternates",
        "file",
        "ACP.GIT_METADATA.PROHIBITED",
        "objects/info/http-alternates",
    ),
    (
        "http-alternates-directory",
        "public",
        "both",
        "prohibited_http_alternates",
        "directory",
        "ACP.GIT_METADATA.PROHIBITED",
        "objects/info/http-alternates",
    ),
    (
        "http-alternates-fifo",
        "public",
        "both",
        "prohibited_http_alternates",
        "fifo",
        "ACP.GIT_METADATA.PROHIBITED",
        "objects/info/http-alternates",
    ),
    (
        "http-alternates-live-symlink",
        "public",
        "both",
        "prohibited_http_alternates",
        "live-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "objects/info/http-alternates",
    ),
    (
        "http-alternates-broken-symlink",
        "public",
        "both",
        "prohibited_http_alternates",
        "broken-symlink",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        "objects/info/http-alternates",
    ),
    (
        "http-alternates-ancestor-symlink",
        "public",
        "both",
        "prohibited_http_alternates",
        "objects-info-symlink",
        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
        "objects/info",
    ),
    (
        "linked-external-ancestor-symlink",
        "public",
        "linked",
        "prohibited_alternates",
        "external-objects-info-symlink",
        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
        "objects/info",
    ),
    (
        "linked-external-ancestor-replacement",
        "public",
        "linked",
        "prohibited_alternates",
        "external-objects-info-lstat-open-race",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "objects/info",
    ),
)
STATIC_GIT_METADATA_CASE_COUNT = 94
STATIC_GIT_METADATA_CASE_SHA256 = "9da07ee4ae676313a8b267ae7374bad049781025d969e99201aba9e45a4ca3e9"
STATIC_GIT_METADATA_EXECUTION_CONTRACT_FIELDS = (
    "caseRow",
    "operationalMode",
    "configuredStimulusFacts",
    "configuredStimulusIdentity",
    "observedExecutionEvidenceIdentity",
    "rolePrefix",
    "normalizedIoCleanupPrefix",
)
STATIC_GIT_METADATA_TRIGGER_RECEIPT_FIELDS = (
    "role",
    "callbackVector",
    "lstatVector",
    "openVector",
    "fstatVector",
    "rawReadRequestVector",
    "rawReadChunkLengthVector",
    "rawReadCountVector",
    "readTypeVector",
    "normalizedReadPayloadIdentityVector",
    "postLstatVector",
    "rawCloseAttemptOrderVector",
    "closeResultVector",
)
STATIC_GIT_METADATA_FIXTURE_PARENT_ABSOLUTE_LENGTH = 700
STATIC_GIT_METADATA_FIXTURE_PARENT_LEXICAL_DEPTH = 16
STATIC_GIT_METADATA_FIXTURE_ROOT_REPLAY_SHAPES = ((27, 4), (108, 10))
STATIC_GIT_METADATA_TRIGGER_RECEIPT_SCHEDULE_CONTRACT = (
    "fixture-parent-fsencoded-length-exactly-700",
    "fixture-parent-lexical-depth-exactly-16",
    "fixed-width-neutral-child-slots-before-two-variable-final-components",
    "raw-read-requests-equal-cap-minus-consumed",
    "raw-read-chunks-concatenate-to-observed-payload",
    "raw-read-request-chunk-count-and-type-vectors-exact",
    "raw-close-attempt-result-and-order-vectors-exact",
    "path-content-normalized-only-for-portable-payload-identity",
    "measure-original-root-shapes-27-bytes-depth-4-and-108-bytes-depth-10",
    "run-complete-129-case-collector-independently-under-each-root",
    "separate-execution-stimulus-trigger-receipt-raw-read-close-order-normalized-payload-catalogs-row-and-digest-equal",
)
STATIC_GIT_METADATA_TRIGGER_RECEIPT_COUNT = 129
STATIC_GIT_METADATA_TRIGGER_RECEIPT_SHA256 = (
    "0c61c46db77fcd5a5f2ee21d2839fce9d02edf5fdacf4641410c53aad4ec95a6"
)
STATIC_GIT_METADATA_COLLECTION_FIELDS = (
    "fullExecutions",
    "stimuli",
    "triggerReceipts",
    "rawReadCatalog",
    "closeOrderCatalog",
    "normalizedPayloadCatalog",
    "configuredPlanReceipts",
)
STATIC_GIT_METADATA_RAW_READ_CATALOG_FIELDS = (
    "executionId",
    "roleOrdinal",
    "role",
    "rawReadRequestVector",
    "rawReadChunkLengthVector",
    "rawReadRequestCount",
    "rawReadChunkCount",
    "readTypeVector",
)
STATIC_GIT_METADATA_RAW_READ_CATALOG_COUNT = 466
STATIC_GIT_METADATA_RAW_READ_CATALOG_SHA256 = (
    "83e4d288ea34bda6765e3b3fe4ed0b39d4f6d794f7ddda521ded6038bfb23955"
)
STATIC_GIT_METADATA_CLOSE_ORDER_CATALOG_FIELDS = (
    "executionId",
    "roleOrdinal",
    "role",
    "rawCloseAttemptOrderVector",
    "closeResultVector",
)
STATIC_GIT_METADATA_CLOSE_ORDER_CATALOG_COUNT = 466
STATIC_GIT_METADATA_CLOSE_ORDER_CATALOG_SHA256 = (
    "3c97f0952634e4ff610bef7f61565e90ccaadda0fe36b25263b3e453499246a3"
)
STATIC_GIT_METADATA_NORMALIZED_PAYLOAD_CATALOG_FIELDS = (
    "executionId",
    "roleOrdinal",
    "role",
    "normalizedPayloadSha256",
)
STATIC_GIT_METADATA_NORMALIZED_PAYLOAD_CATALOG_COUNT = 466
STATIC_GIT_METADATA_NORMALIZED_PAYLOAD_CATALOG_SHA256 = (
    "9f328cbc155b9b57047f4ab53d78720842fbeb02cae54c5a7e03090ab001bda1"
)
STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPE_FIELDS = (
    "rootShape",
    "governedParentShape",
    "finalComponentLengths",
    "evidenceIdentity",
)
STATIC_GIT_METADATA_ROOT_REPLAY_EVIDENCE_FIELDS = (
    "fullExecutions",
    "stimuli",
    "triggerReceipts",
    "rawReadCatalog",
    "closeOrderCatalog",
    "normalizedPayloadCatalog",
)
STATIC_GIT_METADATA_ROOT_REPLAY_FINAL_COMPONENT_LENGTHS = ((90, 91), (197, 197))
STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPES = (
    (
        (27, 4),
        (700, 16),
        (90, 91),
        "4a436fa2d1433aa757c3823d81d1903cd6fcff124af30e083210d9d651968bec",
    ),
    (
        (108, 10),
        (700, 16),
        (197, 197),
        "4a436fa2d1433aa757c3823d81d1903cd6fcff124af30e083210d9d651968bec",
    ),
)
STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPE_COUNT = 2
STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPE_SHA256 = (
    "9d4ea90d35d429c1b1018fb3ad9af8f0b59bd0b4592d0bea1c933120ddc1024a"
)
STATIC_GIT_METADATA_ROOT_REPLAY_EVIDENCE_IDENTITY_SHA256 = (
    "4a436fa2d1433aa757c3823d81d1903cd6fcff124af30e083210d9d651968bec"
)
STATIC_GIT_METADATA_ROOT_REPLAY_CONFIGURED_PLAN_RECEIPT_EQUALITY = (
    "capture-under-each-root",
    "exact-row-equality",
    "exact-digest-equality-before-portability-credit",
)
STATIC_GIT_METADATA_CROSS_ROOT_REPLAY_FINDING = (
    "evidence",
    "CURRENT",
    "ACP.EVIDENCE.CROSS_ROOT_REPLAY_MISMATCH",
    "rootReplay.evidenceIdentity",
)
STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANT_FIELDS = (
    "mutantId",
    "catalog",
    "executionId",
    "roleOrdinal",
    "coordinate",
    "mutation",
    "findingLocation",
)
STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANTS = (
    (
        "raw-read-coordinate",
        "raw_reads",
        "linked-positive@linked",
        0,
        "rawReadRequestVector[0]",
        "increment-first-request",
        "metadataReplay.rawReads[linked-positive@linked][0].rawReadRequestVector[0]",
    ),
    (
        "normalized-payload-coordinate",
        "normalized_payloads",
        "conventional-positive@conventional",
        0,
        "normalizedPayloadSha256",
        "replace-first-payload-identity",
        "metadataReplay.normalizedPayloads[conventional-positive@conventional][0].normalizedPayloadSha256",
    ),
)
STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANT_COUNT = 2
STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANT_SHA256 = (
    "6d399932abf4cc9a2a4b7324b70f2f63cad5b53ca37636cb9d123fbd214e0c64"
)
STATIC_GIT_METADATA_FORMER_COLLISION_GROUPS = (
    (
        "root-pre-root-symlink-conventional",
        ("root-symlink@conventional", "pre-root-symlink@conventional"),
    ),
    ("root-pre-root-symlink-linked", ("root-symlink@linked", "pre-root-symlink@linked")),
    (
        "root-pre-root-replacement-conventional",
        ("root-replacement@conventional", "pre-root-replacement@conventional"),
    ),
    (
        "root-pre-root-replacement-linked",
        ("root-replacement@linked", "pre-root-replacement@linked"),
    ),
    (
        "grafts-live-broken-conventional",
        ("grafts-live-symlink@conventional", "grafts-broken-symlink@conventional"),
    ),
    ("grafts-live-broken-linked", ("grafts-live-symlink@linked", "grafts-broken-symlink@linked")),
    (
        "shallow-live-broken-conventional",
        ("shallow-live-symlink@conventional", "shallow-broken-symlink@conventional"),
    ),
    (
        "shallow-live-broken-linked",
        ("shallow-live-symlink@linked", "shallow-broken-symlink@linked"),
    ),
    (
        "alternates-live-broken-conventional",
        ("alternates-live-symlink@conventional", "alternates-broken-symlink@conventional"),
    ),
    (
        "alternates-live-broken-linked",
        ("alternates-live-symlink@linked", "alternates-broken-symlink@linked"),
    ),
    (
        "http-alternates-live-broken-conventional",
        (
            "http-alternates-live-symlink@conventional",
            "http-alternates-broken-symlink@conventional",
        ),
    ),
    (
        "http-alternates-live-broken-linked",
        ("http-alternates-live-symlink@linked", "http-alternates-broken-symlink@linked"),
    ),
    (
        "linked-layout-short-read-reverse-close",
        ("linked-layout-outside@linked", "short-read@linked", "reverse-close@linked"),
    ),
    (
        "linked-external-ordinary-ancestor-symlink",
        ("linked-external-ancestor-symlink@linked", "alternates-ancestor-symlink@linked"),
    ),
    (
        "configured-removed-linked-pre-root-class",
        ("pre-root-symlink@linked", "fstat-type@linked", "open-error@linked"),
    ),
    (
        "configured-removed-conventional-race-and-io-class",
        (
            "root-replacement@conventional",
            "ancestor-replacement@conventional",
            "between-read-conventional-dot-git@conventional",
            "final-binding-revalidation@conventional",
            "leaf-replacement@conventional",
            "fstat-device@conventional",
            "fstat-inode@conventional",
            "fstat-type@conventional",
            "lstat-error@conventional",
            "open-error@conventional",
            "close-error@conventional",
        ),
    ),
    (
        "configured-removed-linked-root-class",
        ("root-replacement@linked", "leaf-replacement@linked", "post-read-device@linked"),
    ),
    (
        "configured-removed-linked-between-read-class",
        ("between-read-linked-directory@linked", "between-read-common-directory@linked"),
    ),
    (
        "configured-removed-linked-fstat-io-class",
        ("fstat-inode@linked", "lstat-error@linked", "close-error@linked"),
    ),
)
STATIC_GIT_METADATA_FORMER_COLLISION_GROUP_COUNT = 19
STATIC_GIT_METADATA_FORMER_COLLISION_GROUP_SHA256 = (
    "3d6ec3f35db4037153555ae3e3fd4332f70b5812e8413923399b1fa805753185"
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_COLLISION_COUNT = 5
STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_FIELDS = (
    "historicalGroupName",
    "executionPair",
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUPS = (
    (
        "configured-removed-linked-pre-root-fstat",
        ("pre-root-symlink@linked", "fstat-type@linked"),
    ),
    (
        "configured-removed-linked-pre-root-open",
        ("pre-root-symlink@linked", "open-error@linked"),
    ),
    (
        "configured-removed-conventional-ancestor",
        ("root-replacement@conventional", "ancestor-replacement@conventional"),
    ),
    (
        "configured-removed-conventional-between",
        (
            "root-replacement@conventional",
            "between-read-conventional-dot-git@conventional",
        ),
    ),
    (
        "configured-removed-conventional-final",
        (
            "root-replacement@conventional",
            "final-binding-revalidation@conventional",
        ),
    ),
    (
        "configured-removed-conventional-leaf",
        ("root-replacement@conventional", "leaf-replacement@conventional"),
    ),
    (
        "configured-removed-conventional-fstat-device",
        ("root-replacement@conventional", "fstat-device@conventional"),
    ),
    (
        "configured-removed-conventional-fstat-inode",
        ("root-replacement@conventional", "fstat-inode@conventional"),
    ),
    (
        "configured-removed-conventional-fstat-type",
        ("root-replacement@conventional", "fstat-type@conventional"),
    ),
    (
        "configured-removed-conventional-lstat",
        ("root-replacement@conventional", "lstat-error@conventional"),
    ),
    (
        "configured-removed-conventional-open",
        ("root-replacement@conventional", "open-error@conventional"),
    ),
    (
        "configured-removed-conventional-close",
        ("root-replacement@conventional", "close-error@conventional"),
    ),
    (
        "configured-removed-linked-root-leaf",
        ("root-replacement@linked", "leaf-replacement@linked"),
    ),
    (
        "configured-removed-linked-root-postread",
        ("root-replacement@linked", "post-read-device@linked"),
    ),
    (
        "configured-removed-linked-between-read",
        ("between-read-linked-directory@linked", "between-read-common-directory@linked"),
    ),
    (
        "configured-removed-linked-fstat-lstat",
        ("fstat-inode@linked", "lstat-error@linked"),
    ),
    (
        "configured-removed-linked-fstat-close",
        ("fstat-inode@linked", "close-error@linked"),
    ),
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_COUNT = 17
STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_SHA256 = (
    "aa41b6ec402fa9bedc1fb441baf6532011bb7b2f2dc813f360c387edb35da13d"
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_SOURCE = (
    "Reset29:be4aba72a9b808569091ed5c69471f7c747eca6e:"
    "EXPECTED_METADATA_FORMER_COLLISION_GROUPS[-17:]"
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_SOURCE_BLOB = (
    "472efe3987d419213c705b72b88e7a2bad7f3c3e"
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_IDENTITY_CONTRACT = (
    "non-label",
    "non-terminal",
    "derived-from-configured-callback-target-phase-effect",
    "included-in-every-valid-execution-binding",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_FIELDS = (
    "executionId",
    "callback",
    "target",
    "phase",
    "effect",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_COUNT = 22
STATIC_GIT_METADATA_CONFIGURED_PLAN_SHA256 = (
    "be232294b50b2ab84f96df800d6b495ace266077218bd6fb2c716353622015e8"
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_FIELDS = (
    "executionId",
    "observedCallback",
    "observedTarget",
    "observedTargetRole",
    "observedTargetPath",
    "observedPhase",
    "observedRoleOrdinal",
    "observedCallbackOrdinal",
    "observedEffect",
    "callbackEvents",
    "metadataEvents",
    "statEvents",
    "exceptionEvents",
    "rawEvidenceIdentity",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS = (
    "callbackEvents",
    "metadataEvents",
    "statEvents",
    "exceptionEvents",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS = (
    "callback",
    "target",
    "phase",
    "effect",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_IDENTITY_CONTRACT = (
    "derive-raw-evidence-identity-from-actual-callback-metadata-stat-and-exception-events-before-semantic-projection",
    "derive-semantic-fields-only-from-raw-evidence",
    "must-not-read-configured-plan-case-row-expected-finding-or-terminal-result",
    "project-callback-target-phase-effect-and-require-exact-declared-plan-equality-before-binding",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_COUNT = 22
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_SHA256 = (
    "44e55951513a7f7ab555765007a17335198681f09a0fbb8b7cf907b243335ad5"
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_FIELDS = (
    "mutantId",
    "executionId",
    "coordinate",
    "mutation",
    "expectedDisposition",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANTS = (
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-CALLBACK",
        "fstat-type@linked",
        "callback",
        "replace-with-different-closed-callback",
        "exact-plan-receipt-binding-fails",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-TARGET",
        "fstat-type@linked",
        "target",
        "replace-with-different-role-path-target",
        "exact-plan-receipt-binding-fails",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-PHASE",
        "fstat-type@linked",
        "phase",
        "replace-with-different-closed-phase-order",
        "exact-plan-receipt-binding-fails",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-EFFECT",
        "fstat-type@linked",
        "effect",
        "replace-with-different-closed-effect",
        "exact-plan-receipt-binding-fails",
    ),
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_COUNT = 4
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_SHA256 = (
    "82edf76324128f8a05909768c9aae0c2e801f2e105f053549b00a8c5ce28ddf3"
)
STATIC_GIT_METADATA_VALID_EXECUTION_BINDING_FIELDS = (
    "configuredStimulusIdentity",
    "configuredPlanIdentity",
    "configuredPlanReceiptIdentity",
    "actualReceiptIdentity",
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_EQUIVALENCE_CLASS_FIELDS = (
    "groupName",
    "completeExecutionIds",
    "strippedFactsIdentity",
    "declaredCollision",
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_EQUIVALENCE_CLASS_COUNT = 5
STATIC_GIT_METADATA_CONFIGURED_REMOVED_EQUIVALENCE_CLASS_SHA256 = (
    "b71385899ad0186538de9ade027e0b1b768af8fe30cd19ac8d8e026e6b2dc60a"
)
STATIC_GIT_METADATA_RECEIPT_HYBRID_CONTRACT_FIELDS = (
    "groupName",
    "sourceExecutionId",
    "swappedReceiptExecutionId",
    "strippedFactsIdentity",
    "configuredPlanIdentity",
    "actualReceiptIdentity",
    "hybridBindingIdentity",
    "validSetMembership",
)
STATIC_GIT_METADATA_RECEIPT_HYBRID_COUNT = 130
STATIC_GIT_METADATA_RECEIPT_HYBRID_SHA256 = (
    "bd26f841084c593d62f16c8fba27731be0c101b20a20332f48ed348caa6d32e0"
)
STATIC_GIT_METADATA_CONSTANT_RECEIPT_SURVIVOR_CONTRACT = (
    "replace-all-actual-receipts-with-one-constant",
    "at-least-one-hybrid-binding-must-be-absent-from-exact-valid-set",
)
STATIC_GIT_METADATA_EXECUTION_IDS = (
    "conventional-positive@conventional",
    "linked-positive@linked",
    "linked-layout-outside@linked",
    "root-nonabsolute@root",
    "root-dotdot@root",
    "root-dot@root",
    "root-repeated-separator@root",
    "root-trailing-separator@root",
    "root-symlink@conventional",
    "root-symlink@linked",
    "pre-root-symlink@conventional",
    "pre-root-symlink@linked",
    "root-replacement@conventional",
    "root-replacement@linked",
    "pre-root-replacement@conventional",
    "pre-root-replacement@linked",
    "ancestor-replacement@conventional",
    "ancestor-replacement@linked",
    "between-read-conventional-dot-git@conventional",
    "between-read-linked-directory@linked",
    "between-read-linked-common-directory@linked",
    "between-read-common-directory@linked",
    "final-binding-revalidation@conventional",
    "dot-git-missing@conventional",
    "dot-git-target-symlink@conventional",
    "dot-git-fifo@conventional",
    "dot-git-cap-n-malformed@linked",
    "dot-git-cap-n-plus-one@linked",
    "dot-git-invalid-utf8@linked",
    "dot-git-missing-lf@linked",
    "dot-git-crlf@linked",
    "dot-git-extra-lf@linked",
    "dot-git-extra-record@linked",
    "dot-git-relative@linked",
    "dot-git-dot-component@linked",
    "dot-git-dotdot-component@linked",
    "dot-git-empty-component@linked",
    "dot-git-nul@linked",
    "dot-git-degenerate-common-root@linked",
    "leaf-replacement@conventional",
    "leaf-replacement@linked",
    "fstat-device@conventional",
    "fstat-inode@conventional",
    "fstat-type@conventional",
    "fstat-device@linked",
    "fstat-inode@linked",
    "fstat-type@linked",
    "post-read-device@linked",
    "post-read-inode@linked",
    "post-read-type@linked",
    "read-type@linked",
    "read-error@linked",
    "lstat-error@conventional",
    "lstat-error@linked",
    "open-error@conventional",
    "open-error@linked",
    "close-error@conventional",
    "close-error@linked",
    "backlink-missing@linked",
    "backlink-directory@linked",
    "backlink-fifo@linked",
    "backlink-symlink@linked",
    "backlink-cap-n-malformed@linked",
    "backlink-cap-n-plus-one@linked",
    "backlink-invalid-utf8@linked",
    "backlink-missing-lf@linked",
    "backlink-extra-lf@linked",
    "backlink-mismatch@linked",
    "commondir-missing@linked",
    "commondir-directory@linked",
    "commondir-fifo@linked",
    "commondir-symlink@linked",
    "commondir-cap-n-malformed@linked",
    "commondir-cap-n-plus-one@linked",
    "commondir-invalid-utf8@linked",
    "commondir-missing-lf@linked",
    "commondir-extra-lf@linked",
    "commondir-mismatch@linked",
    "grafts-file@conventional",
    "grafts-directory@conventional",
    "grafts-fifo@conventional",
    "grafts-live-symlink@conventional",
    "grafts-broken-symlink@conventional",
    "grafts-ancestor-symlink@conventional",
    "grafts-file@linked",
    "grafts-directory@linked",
    "grafts-fifo@linked",
    "grafts-live-symlink@linked",
    "grafts-broken-symlink@linked",
    "grafts-ancestor-symlink@linked",
    "shallow-file@conventional",
    "shallow-directory@conventional",
    "shallow-fifo@conventional",
    "shallow-live-symlink@conventional",
    "shallow-broken-symlink@conventional",
    "shallow-file@linked",
    "shallow-directory@linked",
    "shallow-fifo@linked",
    "shallow-live-symlink@linked",
    "shallow-broken-symlink@linked",
    "alternates-file@conventional",
    "alternates-directory@conventional",
    "alternates-fifo@conventional",
    "alternates-live-symlink@conventional",
    "alternates-broken-symlink@conventional",
    "alternates-ancestor-symlink@conventional",
    "alternates-file@linked",
    "alternates-directory@linked",
    "alternates-fifo@linked",
    "alternates-live-symlink@linked",
    "alternates-broken-symlink@linked",
    "alternates-ancestor-symlink@linked",
    "http-alternates-file@conventional",
    "http-alternates-directory@conventional",
    "http-alternates-fifo@conventional",
    "http-alternates-live-symlink@conventional",
    "http-alternates-broken-symlink@conventional",
    "http-alternates-ancestor-symlink@conventional",
    "http-alternates-file@linked",
    "http-alternates-directory@linked",
    "http-alternates-fifo@linked",
    "http-alternates-live-symlink@linked",
    "http-alternates-broken-symlink@linked",
    "http-alternates-ancestor-symlink@linked",
    "linked-external-ancestor-symlink@linked",
    "linked-external-ancestor-replacement@linked",
    "linked-git-dir-target-symlink@linked",
    "short-read@linked",
    "reverse-close@linked",
)
STATIC_GIT_METADATA_EXECUTION_COUNT = 129
STATIC_GIT_METADATA_EXECUTION_SHA256 = (
    "dc206260cb4f4c2d1217ba9a6cf274279c2fdbe6c98f5c4c0db21d133558e91b"
)
STATIC_GIT_METADATA_FULL_EXECUTION_SHA256 = (
    "74c0225e39f7fc6c170a1922246133daf07f458ee5040a1d581272602573190c"
)
STATIC_GIT_METADATA_STIMULUS_COUNT = 129
STATIC_GIT_METADATA_STIMULUS_SHA256 = (
    "d93d3a44c3a3b18a9bd46edec8fe7f981790f6e0dd55da96ce1be3a18eab498d"
)
STATIC_GIT_METADATA_PAYLOAD_FINGERPRINT_COUNT = 25
STATIC_GIT_METADATA_PAYLOAD_FINGERPRINT_SHA256 = (
    "77fa92e04dc499feca8c37b78fb9d119858d7f0ac8df7c148019c89bf49b77d4"
)
STATIC_GIT_METADATA_READER_STEPS = (
    "reject-noncanonical-raw-root-before-Path-construction",
    "derive-kind-cap-location-and-target-from-closed-role-and-dot-git-record",
    "reject-nonabsolute-dot-dotdot-or-unauthorized-provenance-before-io",
    "open-root-and-hold-parent-directory-descriptors",
    "lstat-each-component-relative-to-held-parent",
    "open-each-directory-with-O_DIRECTORY-and-O_NOFOLLOW-relative-to-parent",
    "fstat-type-before-device-inode-identity",
    "compare-every-reopened-parent-record-type-device-and-inode",
    "open-final-record-with-O_NOFOLLOW-relative-to-held-parent",
    "bounded-read-through-cap-plus-one",
    "post-read-type-before-device-inode-identity",
    "close-every-descriptor-once-in-reverse-order-in-finally",
    "return-typed-record-or-first-exact-finding",
)
STATIC_GIT_METADATA_DISCOVERY_STEPS = (
    "bind-lexically-normalized-absolute-root",
    "read-root-dot-git-before-any-process",
    "accept-only-conventional-directory-or-strict-absolute-linked-record",
    "derive-linked-git-dir-from-exact-dot-git-record-not-git-output",
    "require-linked-git-dir-under-common-dir-worktrees-single-name",
    "read-linked-directory",
    "read-backlink",
    "strictly-parse-backlink-utf8-line-shape-before-relationship-mismatch",
    "stop-on-backlink-finding-parse-or-mismatch-before-commondir",
    "read-commondir",
    "strictly-parse-commondir-utf8-line-shape-before-relationship-mismatch",
    "stop-on-commondir-finding-parse-or-mismatch-before-common-dir",
    "derive-common-dir-independently",
    "bind-directory-records-into-every-dependent-read",
    "reject-four-prohibited-common-dir-inodes-no-follow",
    "revalidate-dot-git-linked-and-common-bindings-before-process",
    "return-exact-binding-or-first-finding-by-identity",
    "start-no-git-process-until-discovery-complete",
)
STATIC_GIT_METADATA_FAILURE_PRECEDENCE = (
    "missing",
    "ancestor_symlink",
    "target_symlink",
    "wrong_type",
    "byte_cap",
    "io_error",
    "identity_changed",
    "read_type",
    "invalid_utf8",
    "line_count",
    "record_shape",
    "nonabsolute",
    "containment",
    "layout",
    "backlink_mismatch",
    "commondir_mismatch",
    "prohibited",
)
STATIC_ALLOWED_GIT_FORMS = (
    ("{git-prefix}", "rev-parse", "--show-object-format"),
    (
        "{git-prefix}",
        "fsck",
        "--full",
        "--strict",
        "--no-dangling",
        "--no-reflogs",
        "--no-progress",
    ),
    ("{git-prefix}", "rev-parse", "HEAD^{commit}"),
    ("{git-prefix}", "cat-file", "-t", "{red_head}"),
    ("{git-prefix}", "cat-file", "-s", "{red_head}"),
    ("{git-prefix}", "merge-base", "--is-ancestor", "{red_head}", "{head}"),
    ("{git-prefix}", "rev-list", "--min-parents=2", "--max-count=1", "{red_head}..{head}"),
    (
        "{git-prefix}",
        "rev-list",
        "--parents",
        "--ancestry-path",
        "--reverse",
        "--max-count=65",
        "{red_head}..{head}",
    ),
    (
        "{git-prefix}",
        "diff-tree",
        "-r",
        "--no-ext-diff",
        "--no-renames",
        "--ignore-submodules=none",
        "--quiet",
        "{red_head}",
        "{c3_head}",
        "--",
        ".",
        ":(exclude)docs/governance/adversarial-convergence-red-freeze-v1.json",
    ),
    (
        "{git-prefix}",
        "diff-tree",
        "-r",
        "--no-ext-diff",
        "--no-renames",
        "--ignore-submodules=none",
        "--quiet",
        "{red_head}",
        "{c3_head}",
        "--",
        "docs/governance/adversarial-convergence-red-freeze-v1.json",
    ),
    (
        "{git-prefix}",
        "rev-parse",
        "{red_head}^{tree}",
        "{red_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json",
        "{red_head}:tests/unit/test_issue435_adversarial_convergence.py",
        "{red_head}:tests/unit/test_issue435_adversarial_convergence_repository.py",
    ),
    (
        "{git-prefix}",
        "cat-file",
        "-s",
        "{c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json",
    ),
    (
        "{git-prefix}",
        "show",
        "{c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json",
    ),
    (
        "{git-prefix}",
        "show",
        "--no-notes",
        "--no-show-signature",
        "-s",
        "--format=%ae",
        "{red_head}",
    ),
)
STATIC_GIT_FORM_IDS = (
    "object_format",
    "object_integrity",
    "head",
    "red_type",
    "red_size",
    "red_ancestor",
    "merge_scan",
    "ancestry_chain",
    "c3_other_scope",
    "c3_freeze_change",
    "red_objects",
    "c3_freeze_size",
    "c3_freeze_payload",
    "red_author",
)
STATIC_GIT_TEXTUAL_TRANSFORMATIONS = (
    ("object_format", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "object_format"),
    ("object_format", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "object_format"),
    ("object_format", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "object_format"),
    ("object_format", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "object_format"),
    ("object_format", "valid_token", True, "freeze", "ACP.FREEZE.OBJECT_FORMAT", "objectFormat"),
    ("object_integrity", "missing_lf", False, None, None, None),
    ("object_integrity", "crlf", False, None, None, None),
    ("object_integrity", "extra_line", False, None, None, None),
    ("object_integrity", "corrupt_token", False, None, None, None),
    ("object_integrity", "valid_token", False, None, None, None),
    ("head", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "head"),
    ("head", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "head"),
    ("head", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "head"),
    ("head", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "head"),
    ("head", "valid_token", True, "freeze", "ACP.FREEZE.C3_MISSING", "redHead"),
    ("red_type", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "red_type"),
    ("red_type", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "red_type"),
    ("red_type", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "red_type"),
    ("red_type", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "red_type"),
    ("red_type", "valid_token", True, "freeze", "ACP.FREEZE.RED_HEAD_NOT_COMMIT", "redHead"),
    ("red_size", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "red_size"),
    ("red_size", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "red_size"),
    ("red_size", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "red_size"),
    ("red_size", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "red_size"),
    ("red_size", "valid_token", True, "git", "ACP.GIT.SIZE_MISMATCH", "red_size"),
    ("red_ancestor", "missing_lf", False, None, None, None),
    ("red_ancestor", "crlf", False, None, None, None),
    ("red_ancestor", "extra_line", False, None, None, None),
    ("red_ancestor", "corrupt_token", False, None, None, None),
    ("red_ancestor", "valid_token", False, None, None, None),
    ("merge_scan", "missing_lf", False, None, None, None),
    ("merge_scan", "crlf", True, "git", "ACP.GIT.OUTPUT_TOKEN", "merge_scan"),
    ("merge_scan", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "merge_scan"),
    ("merge_scan", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "merge_scan"),
    ("merge_scan", "valid_token", True, "freeze", "ACP.FREEZE.HISTORY_MERGE", "HEAD"),
    ("ancestry_chain", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "ancestry_chain"),
    ("ancestry_chain", "crlf", True, "git", "ACP.GIT.OUTPUT_TOKEN", "ancestry_chain"),
    ("ancestry_chain", "extra_line", True, "git", "ACP.GIT.OUTPUT_TOKEN", "ancestry_chain"),
    ("ancestry_chain", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "ancestry_chain"),
    (
        "ancestry_chain",
        "valid_token",
        True,
        "freeze",
        "ACP.FREEZE.HISTORY_CHAIN",
        "ancestry[0].parent",
    ),
    ("c3_other_scope", "missing_lf", False, None, None, None),
    ("c3_other_scope", "crlf", False, None, None, None),
    ("c3_other_scope", "extra_line", False, None, None, None),
    ("c3_other_scope", "corrupt_token", False, None, None, None),
    ("c3_other_scope", "valid_token", False, None, None, None),
    ("c3_freeze_change", "missing_lf", False, None, None, None),
    ("c3_freeze_change", "crlf", False, None, None, None),
    ("c3_freeze_change", "extra_line", False, None, None, None),
    ("c3_freeze_change", "corrupt_token", False, None, None, None),
    ("c3_freeze_change", "valid_token", False, None, None, None),
    ("red_objects", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "red_objects"),
    ("red_objects", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "red_objects"),
    ("red_objects", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "red_objects"),
    ("red_objects", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "red_objects"),
    ("red_objects", "valid_token", True, "freeze", "ACP.FREEZE.RED_TREE_MISMATCH", "redTree"),
    ("c3_freeze_size", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "c3_freeze_size"),
    ("c3_freeze_size", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "c3_freeze_size"),
    ("c3_freeze_size", "extra_line", True, "git", "ACP.GIT.STDOUT_BYTES", "c3_freeze_size"),
    ("c3_freeze_size", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "c3_freeze_size"),
    ("c3_freeze_size", "valid_token", True, "git", "ACP.GIT.SIZE_MISMATCH", "c3_freeze_size"),
    ("c3_freeze_payload", "missing_lf", False, None, None, None),
    ("c3_freeze_payload", "crlf", False, None, None, None),
    ("c3_freeze_payload", "extra_line", False, None, None, None),
    ("c3_freeze_payload", "corrupt_token", False, None, None, None),
    ("c3_freeze_payload", "valid_token", False, None, None, None),
    ("red_author", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "red_author"),
    ("red_author", "crlf", True, "git", "ACP.GIT.OUTPUT_TOKEN", "red_author"),
    ("red_author", "extra_line", True, "git", "ACP.GIT.OUTPUT_LINES", "red_author"),
    ("red_author", "corrupt_token", True, "git", "ACP.GIT.OUTPUT_TOKEN", "red_author"),
    (
        "red_author",
        "valid_token",
        True,
        "freeze",
        "ACP.FREEZE.AUTHOR_MISMATCH",
        "implementationAuthor",
    ),
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_COUNT = 70
STATIC_GIT_TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT = 44
STATIC_GIT_TEXTUAL_TRANSFORMATION_SHA256 = (
    "7e4e4eded6736f4894747e012cfb3b5727a073a0c9950b38712684a0c1e2b6d2"
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_FIELDS = (
    "role",
    "transformation",
    "applicable",
    "baseSource",
    "builder",
    "byteRelation",
    "expectedStage",
    "expectedCode",
    "expectedLocation",
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_BUILDERS = (
    ("missing_lf", "remove-one-terminal-lf", "base[:-1]"),
    ("crlf", "replace-lf-with-crlf", "base.replace(LF,CRLF)"),
    ("extra_line", "role-specific-extra-line", "extra(base,role)"),
    ("corrupt_token", "role-specific-corrupt-token", "corrupt(base,role)"),
    ("valid_token", "role-specific-valid-semantic", "valid(base,role,freeze)"),
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_SHA256 = (
    "d94fc0a49bf78e072ac44997785e40e073c19e9d14f0a19ab5a9415d88e60456"
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_FIELDS = (
    "role",
    "transformation",
    "identityMode",
    "tokenMapShape",
    "normalizedBaseLength",
    "normalizedBaseSha256",
    "normalizedTransformedLength",
    "normalizedTransformedSha256",
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITIES = (
    (
        "object_format",
        "missing_lf",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "335277ee77cfc8d51d6602e4137232cf6041aac2bc663777e384b90d5ae74d51",
        4,
        "b1565820a5cdac40e0520d23f9d0b1497f240ddc51d72eac6423d97d952d444f",
    ),
    (
        "object_format",
        "crlf",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "335277ee77cfc8d51d6602e4137232cf6041aac2bc663777e384b90d5ae74d51",
        6,
        "e221f895b353e3205971a3fa214f947de76223ac08f37409b19181ac05274ae7",
    ),
    (
        "object_format",
        "extra_line",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "335277ee77cfc8d51d6602e4137232cf6041aac2bc663777e384b90d5ae74d51",
        7,
        "860830f48fd532a6070337f8ae768a52bae254d4784eed3f3e34ef307b44359f",
    ),
    (
        "object_format",
        "corrupt_token",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "335277ee77cfc8d51d6602e4137232cf6041aac2bc663777e384b90d5ae74d51",
        5,
        "d7bb01a3fc06a6887fd52d385d0e7d0e33361af272b68d9696f8efcc71090ca8",
    ),
    (
        "object_format",
        "valid_token",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "335277ee77cfc8d51d6602e4137232cf6041aac2bc663777e384b90d5ae74d51",
        5,
        "0353d3653787940d227569c94e1065eebadbb750a8ca70f6bd673388a1837e46",
    ),
    (
        "head",
        "missing_lf",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID",), ("C3_HEAD_OID",)),
        14,
        "3c84561a66be097818466a1745b2d0c9ab2e1b8830e21f87aada75d6f51fa84d",
        13,
        "cc8ab54fac22c0bdc74773629fccc7f3c46ee854f11f86f892216ea7d8552f29",
    ),
    (
        "head",
        "crlf",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID",), ("C3_HEAD_OID",)),
        14,
        "3c84561a66be097818466a1745b2d0c9ab2e1b8830e21f87aada75d6f51fa84d",
        15,
        "b3bfaa2d1852e196ca2786988a21d24a9f0e9102317b2286563699e9a6c5a962",
    ),
    (
        "head",
        "extra_line",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID",), ("C3_HEAD_OID",)),
        14,
        "3c84561a66be097818466a1745b2d0c9ab2e1b8830e21f87aada75d6f51fa84d",
        16,
        "365489169dcc9a5c779e1f09a39eaa99584476559001a6222cddd7571834256c",
    ),
    (
        "head",
        "corrupt_token",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID",), ()),
        14,
        "3c84561a66be097818466a1745b2d0c9ab2e1b8830e21f87aada75d6f51fa84d",
        41,
        "e10ef6c0d91b1551fb41f2043ef6efdf5dd161775b4a6abc328ef5a6ae89332d",
    ),
    (
        "head",
        "valid_token",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID",), ()),
        14,
        "3c84561a66be097818466a1745b2d0c9ab2e1b8830e21f87aada75d6f51fa84d",
        41,
        "e3f3d59b587fc7a5beaef3ee3cc8fa1b7bfd482d5ce2a5604cb9a0743cf462a5",
    ),
    (
        "red_type",
        "missing_lf",
        "raw-non-oid-bytes",
        ((), ()),
        7,
        "50836eee574ecff79dea3b4fd40673d7d000f7a5f177d8a6a3000b59c78383b8",
        6,
        "9505cacb7c710ed17125fcc6cb3669e8ddca6c8cd8af6a31f6b3cd64604c3098",
    ),
    (
        "red_type",
        "crlf",
        "raw-non-oid-bytes",
        ((), ()),
        7,
        "50836eee574ecff79dea3b4fd40673d7d000f7a5f177d8a6a3000b59c78383b8",
        8,
        "03c247f0017db08a67be3cc39595c0c94c04e2808fad0767305c64525479aa85",
    ),
    (
        "red_type",
        "extra_line",
        "raw-non-oid-bytes",
        ((), ()),
        7,
        "50836eee574ecff79dea3b4fd40673d7d000f7a5f177d8a6a3000b59c78383b8",
        9,
        "808ed7f5e3b3532ca1da6db79faf4c7793a428e53c302d2ffbc3b3a782cb52ee",
    ),
    (
        "red_type",
        "corrupt_token",
        "raw-non-oid-bytes",
        ((), ()),
        7,
        "50836eee574ecff79dea3b4fd40673d7d000f7a5f177d8a6a3000b59c78383b8",
        7,
        "45cb38bf01adb9c1963546de581f121df11e73b1c4cbe1522c226de8869b53a4",
    ),
    (
        "red_type",
        "valid_token",
        "raw-non-oid-bytes",
        ((), ()),
        7,
        "50836eee574ecff79dea3b4fd40673d7d000f7a5f177d8a6a3000b59c78383b8",
        5,
        "bc103b4a84971ef6459b294a2b98568a2bfb72cded09d4acd1e16366a401f95b",
    ),
    (
        "red_size",
        "missing_lf",
        "raw-non-oid-bytes",
        ((), ()),
        4,
        "e595be81bf15aa95763adb4fc0ba525bbed1971cf5fccdf3a946cd37025fb2c9",
        3,
        "0f4121d0ef1df4c86854c7ebb47ae1c93de8aec8f944035eeaa6495dd71a0678",
    ),
    (
        "red_size",
        "crlf",
        "raw-non-oid-bytes",
        ((), ()),
        4,
        "e595be81bf15aa95763adb4fc0ba525bbed1971cf5fccdf3a946cd37025fb2c9",
        5,
        "fe15ccd797eb272fc2c2d29e28a3380456402a670081f8d83a1fba7183a4ccb0",
    ),
    (
        "red_size",
        "extra_line",
        "raw-non-oid-bytes",
        ((), ()),
        4,
        "e595be81bf15aa95763adb4fc0ba525bbed1971cf5fccdf3a946cd37025fb2c9",
        6,
        "85244fec5aa1bf11a30556a6182b39e324d1460a16f834e142e3a2cb0aa12886",
    ),
    (
        "red_size",
        "corrupt_token",
        "raw-non-oid-bytes",
        ((), ()),
        4,
        "e595be81bf15aa95763adb4fc0ba525bbed1971cf5fccdf3a946cd37025fb2c9",
        4,
        "faca203908d4e36a81479e252f005ce30b6e8f7ee4dee874b8dbf7b4ae7f0f05",
    ),
    (
        "red_size",
        "valid_token",
        "raw-non-oid-bytes",
        ((), ()),
        4,
        "e595be81bf15aa95763adb4fc0ba525bbed1971cf5fccdf3a946cd37025fb2c9",
        4,
        "2fa7660fa51eaa80d3212ae92ef3e870b6d246404eb81efabda68d5319c7d07b",
    ),
    (
        "merge_scan",
        "crlf",
        "raw-non-oid-bytes",
        ((), ()),
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        2,
        "7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6",
    ),
    (
        "merge_scan",
        "extra_line",
        "raw-non-oid-bytes",
        ((), ()),
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        82,
        "278589e204c8f682c4f8ee88e7452f4ac13fbee299fd5ff8c1e4bee7645900f5",
    ),
    (
        "merge_scan",
        "corrupt_token",
        "raw-non-oid-bytes",
        ((), ()),
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        41,
        "fd29d675a24e1b3bd4d0538d35610ceaa70214dba8148e0633d956592d5f8e71",
    ),
    (
        "merge_scan",
        "valid_token",
        "raw-non-oid-bytes",
        ((), ()),
        0,
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        41,
        "bba1b0a81a5ad83dd7905145aabfc1cde9e5ac32efcf5f8833ea2995baf8be11",
    ),
    (
        "ancestry_chain",
        "missing_lf",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID", "RED_HEAD_OID"), ("C3_HEAD_OID", "RED_HEAD_OID")),
        29,
        "48411b289a7ead58c64ec84b9f691e168c0bc489a6acd839d23b41e94722141c",
        28,
        "a216b9b5d810d11aff2979d83c7f0be194ae6bba85ea84e019a6f73a336547a3",
    ),
    (
        "ancestry_chain",
        "crlf",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID", "RED_HEAD_OID"), ("C3_HEAD_OID", "RED_HEAD_OID")),
        29,
        "48411b289a7ead58c64ec84b9f691e168c0bc489a6acd839d23b41e94722141c",
        30,
        "589d9c5a372f7168a45ab7b5c8be8b0fe4e018b7694fd6f06b9b0a362c4caef0",
    ),
    (
        "ancestry_chain",
        "extra_line",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID", "RED_HEAD_OID"), ("C3_HEAD_OID", "RED_HEAD_OID")),
        29,
        "48411b289a7ead58c64ec84b9f691e168c0bc489a6acd839d23b41e94722141c",
        31,
        "bc019c0ff28831dd05921ab843784fa7ab2c36e2b2a75257c19e29f81bbb309e",
    ),
    (
        "ancestry_chain",
        "corrupt_token",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID", "RED_HEAD_OID"), ("RED_HEAD_OID",)),
        29,
        "48411b289a7ead58c64ec84b9f691e168c0bc489a6acd839d23b41e94722141c",
        56,
        "6da4ee90c1c770273fb5b7f45140b51b3a7f2bf4cc2661b6158617a0a13aa286",
    ),
    (
        "ancestry_chain",
        "valid_token",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID", "RED_HEAD_OID"), ("RED_HEAD_OID",)),
        29,
        "48411b289a7ead58c64ec84b9f691e168c0bc489a6acd839d23b41e94722141c",
        56,
        "5871e0cebd48e4f83aeeeb25ed5d0b3a68b1b1b09fc0e7943335c70b29db5fa4",
    ),
    (
        "red_objects",
        "missing_lf",
        "named-dynamic-oid-token",
        (
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
        ),
        85,
        "5a592f86d5603a45567ce109c8dd7d10ddebd7b205fc5bebb4b0a130d57bdce1",
        84,
        "4d98becc0211e1b3e42aafa80a69bf909e3fc0a505039ecfe26f8be81b4bd35a",
    ),
    (
        "red_objects",
        "crlf",
        "named-dynamic-oid-token",
        (
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
        ),
        85,
        "5a592f86d5603a45567ce109c8dd7d10ddebd7b205fc5bebb4b0a130d57bdce1",
        89,
        "9e22e268ab6916ada22760d160a1928d0b492ba65c6b1cea1da348918fcaebbc",
    ),
    (
        "red_objects",
        "extra_line",
        "named-dynamic-oid-token",
        (
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
        ),
        85,
        "5a592f86d5603a45567ce109c8dd7d10ddebd7b205fc5bebb4b0a130d57bdce1",
        87,
        "a2124722752c9f7221f04523fb7a69e56116989b08355d3be23b8cd00755828a",
    ),
    (
        "red_objects",
        "corrupt_token",
        "named-dynamic-oid-token",
        (
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
            ("MATRIX_BLOB_OID", "CORE_ORACLE_BLOB_OID", "REPOSITORY_ORACLE_BLOB_OID"),
        ),
        85,
        "5a592f86d5603a45567ce109c8dd7d10ddebd7b205fc5bebb4b0a130d57bdce1",
        111,
        "0e3cc7be02467c2d6fc06bb2a1f803d78428917f9c18c2295d3453397f01b06c",
    ),
    (
        "red_objects",
        "valid_token",
        "named-dynamic-oid-token",
        (
            (
                "RED_TREE_OID",
                "MATRIX_BLOB_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            ),
            ("MATRIX_BLOB_OID", "CORE_ORACLE_BLOB_OID", "REPOSITORY_ORACLE_BLOB_OID"),
        ),
        85,
        "5a592f86d5603a45567ce109c8dd7d10ddebd7b205fc5bebb4b0a130d57bdce1",
        111,
        "6c5c6b52a7f076558deda90c7d5e54bba392b4ad79e991d7750bfaed98d08417",
    ),
    (
        "c3_freeze_size",
        "missing_lf",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "dc23d3655da416802f01fd3cffd7de986615051f4dd4fc4ff8933b954b9502f3",
        4,
        "8e0c19142ee61342e1f8b09a6fccbcf5867db1542444474ed37ad11bd08eb062",
    ),
    (
        "c3_freeze_size",
        "crlf",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "dc23d3655da416802f01fd3cffd7de986615051f4dd4fc4ff8933b954b9502f3",
        6,
        "9477f52ece818433b8980ceb2a3704dd67e7ad11975e00c3c3d30c01c3528201",
    ),
    (
        "c3_freeze_size",
        "extra_line",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "dc23d3655da416802f01fd3cffd7de986615051f4dd4fc4ff8933b954b9502f3",
        7,
        "732159d94c2281ad07501e8ac605244577332800a4e39990101c3827973702e5",
    ),
    (
        "c3_freeze_size",
        "corrupt_token",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "dc23d3655da416802f01fd3cffd7de986615051f4dd4fc4ff8933b954b9502f3",
        5,
        "05718f1e7f59f10c0338e536fe099e1bf3d9ba8395e69930dbce21bd4a88edb1",
    ),
    (
        "c3_freeze_size",
        "valid_token",
        "raw-non-oid-bytes",
        ((), ()),
        5,
        "dc23d3655da416802f01fd3cffd7de986615051f4dd4fc4ff8933b954b9502f3",
        5,
        "fe4e3bab9fb4bab90dd1607f94319043a1b6dbb6bdd7fe670420291b89263098",
    ),
    (
        "red_author",
        "missing_lf",
        "raw-non-oid-bytes",
        ((), ()),
        33,
        "89dcf64642139c5a8309e8c5ec9b251b66ec749d799aafdee30017b50019ad83",
        32,
        "51eaf37165c21c1dabf8e2a3fa45eed56a431b7f2f0ce1abb16b4b363e5250f9",
    ),
    (
        "red_author",
        "crlf",
        "raw-non-oid-bytes",
        ((), ()),
        33,
        "89dcf64642139c5a8309e8c5ec9b251b66ec749d799aafdee30017b50019ad83",
        34,
        "8270b75b46228a52971060f320b595477f5390488c5771d3ff6f0c6cce740b4f",
    ),
    (
        "red_author",
        "extra_line",
        "raw-non-oid-bytes",
        ((), ()),
        33,
        "89dcf64642139c5a8309e8c5ec9b251b66ec749d799aafdee30017b50019ad83",
        35,
        "7141c203a08f6d938311e7403f069d5852839f26bb327240cc7b0f3385bfda5b",
    ),
    (
        "red_author",
        "corrupt_token",
        "raw-non-oid-bytes",
        ((), ()),
        33,
        "89dcf64642139c5a8309e8c5ec9b251b66ec749d799aafdee30017b50019ad83",
        18,
        "da4eb6a5e26bdce6563408c932d7feb2a8af5490800be249ba6701364bd15533",
    ),
    (
        "red_author",
        "valid_token",
        "raw-non-oid-bytes",
        ((), ()),
        33,
        "89dcf64642139c5a8309e8c5ec9b251b66ec749d799aafdee30017b50019ad83",
        18,
        "f601bb0f05a9f3039ad86243cbd9318906b2663db30ac9e2615a7720c6d2cd43",
    ),
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_COUNT = 44
STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_SHA256 = (
    "59d4077c8ab7ae0ac9f72181b62dc0e628921c60b86797919d8d96af1dcbcab2"
)
STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_NORMALIZATION = (
    (
        "dynamicOidRoles",
        (
            ("head", ("C3_HEAD_OID",)),
            ("merge_scan", ()),
            ("ancestry_chain", ("C3_HEAD_OID", "RED_HEAD_OID")),
            (
                "red_objects",
                (
                    "RED_TREE_OID",
                    "MATRIX_BLOB_OID",
                    "CORE_ORACLE_BLOB_OID",
                    "REPOSITORY_ORACLE_BLOB_OID",
                ),
            ),
        ),
    ),
    ("tokenEncoding", "angle-bracketed-uppercase-name-preserving-lf-and-row-order"),
    (
        "selfReferenceRule",
        "strictly-parse-role-output-then-normalize-only-position-bound-oids-proven-equal-to-contemporaneous-fixture-or-freeze-objects-before-length-and-sha256",
    ),
    ("nonOidBytes", "must-remain-byte-exact"),
    (
        "oidRoleMappingFields",
        (
            "role",
            "rowOrdinal",
            "columnOrdinal",
            "semanticName",
            "identitySource",
        ),
    ),
    (
        "oidRoleMappings",
        (
            ("head", 0, 0, "C3_HEAD_OID", "repository-HEAD"),
            ("ancestry_chain", 0, 0, "C3_HEAD_OID", "repository-HEAD"),
            ("ancestry_chain", 0, 1, "RED_HEAD_OID", "redHead"),
            ("red_objects", 0, 0, "RED_TREE_OID", "redTree"),
            ("red_objects", 1, 0, "MATRIX_BLOB_OID", "matrixBlobOid"),
            (
                "red_objects",
                2,
                0,
                "CORE_ORACLE_BLOB_OID",
                "focusedOracleBlobs[0].blobOid",
            ),
            (
                "red_objects",
                3,
                0,
                "REPOSITORY_ORACLE_BLOB_OID",
                "focusedOracleBlobs[1].blobOid",
            ),
        ),
    ),
    ("oidRoleMappingCount", 7),
    (
        "oidRoleMappingSha256",
        "9f0817328f5e411f2b39ca4bfdc4300cc48884e065d251e929b7569328da028f",
    ),
    (
        "completenessContract",
        (
            "every-parsed-base-oid-position-has-exactly-one-mapping",
            "mapping-order-equals-role-output-order",
            "token-names-and-output-positions-unique-within-role",
            "no-unverified-oid-is-replaced",
        ),
    ),
    (
        "hostileOidSemanticClasses",
        ("uppercase", "corrupt", "injected-valid-but-wrong", "reordered", "missing", "extra"),
    ),
    (
        "hostileOidDisposition",
        "fixed-f-e-F-and-every-other-wrong-oid-remain-raw-or-receive-explicit-hostile-token-only-after-exact-hostile-proof-and-stay-distinct-from-every-verified-dynamic-token",
    ),
    (
        "hostileOidEvidenceFields",
        (
            "role",
            "transform",
            "hostileOidTokenVector",
            "verifiedSemanticVector",
            "normalizedTransformedSha256",
        ),
    ),
    (
        "hostileOidEvidence",
        (
            (
                "head",
                "corrupt_token",
                ("CORRUPT_UPPERCASE_PREFIX:C3_HEAD_OID",),
                (),
                "e10ef6c0d91b1551fb41f2043ef6efdf5dd161775b4a6abc328ef5a6ae89332d",
            ),
            (
                "head",
                "valid_token",
                ("ROLE_INELIGIBLE:RED_HEAD_OID",),
                (),
                "e3f3d59b587fc7a5beaef3ee3cc8fa1b7bfd482d5ce2a5604cb9a0743cf462a5",
            ),
            (
                "merge_scan",
                "extra_line",
                ("e" * 40, "f" * 40),
                (),
                "278589e204c8f682c4f8ee88e7452f4ac13fbee299fd5ff8c1e4bee7645900f5",
            ),
            (
                "merge_scan",
                "corrupt_token",
                ("F" * 40,),
                (),
                "fd29d675a24e1b3bd4d0538d35610ceaa70214dba8148e0633d956592d5f8e71",
            ),
            (
                "merge_scan",
                "valid_token",
                ("f" * 40,),
                (),
                "bba1b0a81a5ad83dd7905145aabfc1cde9e5ac32efcf5f8833ea2995baf8be11",
            ),
            (
                "ancestry_chain",
                "corrupt_token",
                ("CORRUPT_UPPERCASE_PREFIX:C3_HEAD_OID",),
                ("RED_HEAD_OID",),
                "6da4ee90c1c770273fb5b7f45140b51b3a7f2bf4cc2661b6158617a0a13aa286",
            ),
            (
                "ancestry_chain",
                "valid_token",
                ("f" * 40,),
                ("RED_HEAD_OID",),
                "5871e0cebd48e4f83aeeeb25ed5d0b3a68b1b1b09fc0e7943335c70b29db5fa4",
            ),
            (
                "red_objects",
                "corrupt_token",
                ("CORRUPT_UPPERCASE_PREFIX:RED_TREE_OID",),
                (
                    "MATRIX_BLOB_OID",
                    "CORE_ORACLE_BLOB_OID",
                    "REPOSITORY_ORACLE_BLOB_OID",
                ),
                "0e3cc7be02467c2d6fc06bb2a1f803d78428917f9c18c2295d3453397f01b06c",
            ),
            (
                "red_objects",
                "valid_token",
                ("f" * 40,),
                (
                    "MATRIX_BLOB_OID",
                    "CORE_ORACLE_BLOB_OID",
                    "REPOSITORY_ORACLE_BLOB_OID",
                ),
                "6c5c6b52a7f076558deda90c7d5e54bba392b4ad79e991d7750bfaed98d08417",
            ),
        ),
    ),
    ("hostileOidEvidenceCount", 9),
    (
        "hostileOidEvidenceSha256",
        "9857553f7bfefc345c64de7a5d0f8168d7d3a0a431f11a936e2ec0b3f8061502",
    ),
    (
        "hostileOidInequalityContract",
        (
            "corrupt-normalized-bytes-not-equal-valid-normalized-bytes",
            "injected-valid-but-wrong-not-equal-trusted-semantic-token",
            "reordered-missing-extra-token-shapes-remain-distinct",
        ),
    ),
)
STATIC_GIT_MERGE_SCAN_EMPTY_TRANSFORMATION_RELATIONS = (
    ("missing_lf", "inapplicable-empty-base"),
    ("crlf", "empty-base-to-single-crlf"),
    ("extra_line", "empty-base-to-two-ordered-oid-lines"),
    ("corrupt_token", "empty-base-to-one-uppercase-oid-line"),
    ("valid_token", "empty-base-to-one-lowercase-oid-line"),
)
STATIC_GIT_DETERMINISTIC_FIXTURE_COMMIT_METADATA = (
    ("GIT_AUTHOR_NAME", "Issue 435 Fixture"),
    ("GIT_AUTHOR_EMAIL", "issue435-fixture@example.invalid"),
    ("GIT_AUTHOR_DATE", "1704067200 +0000"),
    ("GIT_COMMITTER_NAME", "Issue 435 Fixture"),
    ("GIT_COMMITTER_EMAIL", "issue435-fixture@example.invalid"),
    ("GIT_COMMITTER_DATE", "1704067200 +0000"),
)
STATIC_GIT_OBJECT_BINDINGS = (
    ("red_tree", "redTree"),
    ("matrix_blob", "matrixBlobOid"),
    ("core_oracle_blob", "focusedOracleBlobs[0].blobOid"),
    ("repository_oracle_blob", "focusedOracleBlobs[1].blobOid"),
)
STATIC_GIT_FAILURE_PRECEDENCE = (
    "metadata",
    "governed_schema",
    "timeout",
    "os_error",
    "result_type",
    "args",
    "stdout_type",
    "stderr_type",
    "returncode_type",
    "return_code",
    "stdout_bytes",
    "strict_decode",
    "line_count",
    "token_shape",
    "topology_or_size",
    "field_binding",
    "author_binding",
    "c3_immutability",
)
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_CASES = (
    (
        "metadata-target-symlink-plus-matrix-schema",
        "validate_repository_freeze",
        "dot-git-target-symlink",
        "matrix-schema-version-wrong",
        "74459b011344be2e067eb5bba03760fecd87ff5895e694a116943a6b5a6f5e6d",
        "git-metadata",
        "CURRENT",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        ".git",
        "identity",
        0,
        0,
    ),
)
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_COUNT = 1
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_SHA256 = (
    "5f25c0757507c7061d70cd885aae48c3341163d8957f018a20db6649bbf207e2"
)
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANT_FIELDS = (
    "mutantId",
    "filesystemRereadHelper",
    "hostileDecoy",
    "substitution",
    "requiredDescriptor",
    "requiredSchemaIdentity",
    "expectedDisposition",
)
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANTS = (
    (
        "MUT-METADATA-GOVERNED-REREAD-SUBSTITUTE-DECOY",
        "reread-matrix-with-controlled-decoy",
        "correct-schema-decoy-bytes",
        "replace-filesystem-reread-with-hostile-decoy",
        "matrix-schema-version-wrong",
        "74459b011344be2e067eb5bba03760fecd87ff5895e694a116943a6b5a6f5e6d",
        "exact-observed-schema-assertion-fails-before-credit",
    ),
)
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANT_COUNT = 1
STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANT_SHA256 = (
    "ddaf256a0bdf6c063ab8fd0e5a8eeb74ec97b4c78a58d380f17ed8a93453093e"
)
STATIC_RESET31_BUDGET_CAPS = (
    (
        "perFile",
        (
            ("matrix", 4200),
            ("protocol", 4200),
            ("coreOracle", 4200),
            ("repositoryOracle", 14500),
            ("template", 600),
            ("adr0064", 550),
        ),
    ),
    ("partitions", (("route", 5800), ("architectureSecurity", 2200), ("validator", 28000))),
    ("aggregate", ("sevenSemanticPaths", 34000)),
    ("binary", 0),
)
STATIC_RESET31_READABILITY_DISPOSITION = (
    "actual-at-or-above-85-percent-requires-recorded-readability-and-convergence-risk-review",
    "actual-at-or-above-90-percent-stops-before-C3-and-GREEN-for-decomposition",
    "semantic-compression-to-fit-cap-prohibited",
)
STATIC_GIT_RETURN_CODES = (
    ("object_format", (0,), (), (-1, 2, 127)),
    ("object_integrity", (0,), (1,), (-1, 2, 127)),
    ("head", (0,), (), (-1, 2, 127)),
    ("red_type", (0,), (128,), (-1, 2, 127)),
    ("red_size", (0,), (), (-1, 2, 127)),
    ("red_ancestor", (0,), (1,), (-1, 2, 127)),
    ("merge_scan", (0,), (), (-1, 2, 127)),
    ("ancestry_chain", (0,), (), (-1, 2, 127)),
    ("c3_other_scope", (0,), (1,), (-1, 2, 127)),
    ("c3_freeze_change", (1,), (0,), (-1, 2, 127)),
    ("red_objects", (0,), (), (-1, 2, 127)),
    ("c3_freeze_size", (0,), (), (-1, 2, 127)),
    ("c3_freeze_payload", (0,), (), (-1, 2, 127)),
    ("red_author", (0,), (), (-1, 2, 127)),
)


class Stage(str, enum.Enum):
    BOUNDS = "bounds"
    PARSE = "parse"
    SCHEMA = "schema"
    CANONICAL_IDENTITY = "canonical_identity"
    INDEPENDENT_TRUST = "independent_trust"
    AUTHORIZATION = "authorization"
    GRAPH_CONFLICT = "graph_conflict"
    PHASE_VERDICT = "phase_verdict"


class Phase(str, enum.Enum):
    HISTORICAL = "HISTORICAL"
    CURRENT = "CURRENT"
    ACCEPTANCE = "ACCEPTANCE"


class Verdict(str, enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICTING = "CONFLICTING"


class BlockerClass(str, enum.Enum):
    IMPLEMENTATION = "IMPLEMENTATION_BLOCKER"
    EVIDENCE = "EVIDENCE_BLOCKER"


class BudgetDisposition(str, enum.Enum):
    NORMAL = "NORMAL"
    RISK_REVIEW_REQUIRED = "RISK_REVIEW_REQUIRED"
    STOP_BEFORE_GREEN = "STOP_BEFORE_GREEN"


@dataclass(frozen=True, order=True)
class Finding:
    stage: str
    phase: str
    code: str
    location: str


@dataclass(frozen=True)
class GovernedReadResult:
    payload: bytes | None
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class GitRepositoryBinding:
    root: Path
    git_dir: Path
    common_dir: Path


@dataclass(frozen=True)
class GitDiscoveryResult:
    binding: GitRepositoryBinding | None
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class GitMetadataRecord:
    path: Path
    payload: bytes | None
    mode: int
    device: int
    inode: int
    ancestor_records: tuple[GitMetadataRecord, ...] = ()


@dataclass(frozen=True)
class GitMetadataProvenance:
    role: str
    dot_git_record: GitMetadataRecord | None
    parent_records: tuple[tuple[str, GitMetadataRecord], ...] = ()


@dataclass(frozen=True)
class GitMetadataReadResult:
    record: GitMetadataRecord | None
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class MetadataIO:
    lstat: Callable[..., os.stat_result]
    open: Callable[..., int]
    fstat: Callable[[int], os.stat_result]
    read: Callable[[int, int], bytes]
    close: Callable[[int], None]


SYSTEM_METADATA_IO = MetadataIO(os.lstat, os.open, os.fstat, os.read, os.close)


@dataclass(frozen=True)
class StageCall:
    stage: str
    candidate_id: str
    ordinal: int


@dataclass(frozen=True)
class CryptoCall:
    candidate_id: str
    signature_hex: str
    ordinal: int
    candidate_count: int
    phase: str
    public_key_sha256: str
    message_sha256: str
    result: bool


@dataclass(frozen=True)
class CryptoProbe:
    candidate_id: str
    signature: bytes
    ordinal: int
    candidate_count: int
    phase: Phase
    public_key: bytes
    message: bytes


@dataclass(frozen=True, order=True)
class PhaseVerdict:
    phase: Phase
    verdict: Verdict


@dataclass(frozen=True)
class EvaluationContext:
    expected_phase: Phase
    trusted_public_keys: Mapping[str, bytes]
    authorized_candidate_ids: frozenset[str]
    evaluation_time: str
    max_candidates: int = 4
    max_candidate_bytes: int = 2048
    max_aggregate_bytes: int = 4096
    max_json_depth: int = 4
    max_json_members: int = 13
    max_findings: int = 32
    max_retained_materials: int = 4


@dataclass(frozen=True)
class Evaluation:
    findings: tuple[Finding, ...]
    historical_verdict: Verdict
    current_verdict: Verdict
    acceptance_verdict: Verdict
    phase_verdicts: tuple[PhaseVerdict, ...]
    eligible_candidate_ids: tuple[str, ...]
    selected_candidate_id: str | None
    stage_calls: tuple[StageCall, ...]
    crypto_calls: tuple[CryptoCall, ...]
    graph_call_count: int


@dataclass(frozen=True)
class MatrixValidation:
    findings: tuple[Finding, ...]
    semantic_sha256: str
    invariant_ids: tuple[str, ...]
    blocker_classes: tuple[BlockerClass, ...]
    normalized_case_ids: tuple[str, ...] = ()
    implementation_blockers: int = 0
    evidence_blockers: int = 0


@dataclass(frozen=True)
class MatrixCryptoExpectation:
    candidate_reference: str
    signature_hex: str
    ordinal: int
    candidate_count: int
    phase: Phase
    public_key_sha256: str
    message_sha256: str
    result: bool


@dataclass(frozen=True)
class MatrixCase:
    case_id: str
    dimension: str
    test_class: str
    target_phase: Phase
    input_class: str
    input_reference: str
    input_sha256: str
    execution_mode: str
    stage: str
    findings: tuple[Finding, ...]
    phase_verdicts: tuple[PhaseVerdict, ...]
    stage_calls: tuple[StageCall, ...]
    crypto_expectations: tuple[MatrixCryptoExpectation, ...]
    graph_eligible: bool
    graph_call_count: int
    selected_candidate_reference: str | None
    test_node: str
    mutant_id: str
    assertion_id: str
    blocker_class: BlockerClass
    evidence_state: str


@dataclass(frozen=True)
class MatrixObservation:
    stimulus_sha256: str
    evaluation: Evaluation


@dataclass(frozen=True)
class MatrixStimulus:
    candidate_documents: tuple[bytes, ...]
    context: EvaluationContext
    retained: RetainedEvaluation | None


@dataclass(frozen=True)
class MatrixStimulusParse:
    stimulus: MatrixStimulus | None
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class MatrixFixtureExecution:
    observation: MatrixObservation | None
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class RetainedEvaluation:
    candidate_sha256s: tuple[str, ...]
    evaluation_phase: Phase
    evaluation_time: str
    trusted_key_sha256s: tuple[tuple[str, str], ...]
    authorized_candidate_ids: tuple[str, ...]
    findings: tuple[Finding, ...]
    phase_verdicts: tuple[PhaseVerdict, ...]
    eligible_candidate_ids: tuple[str, ...]
    selected_candidate_id: str | None
    stage_calls: tuple[StageCall, ...]
    crypto_calls: tuple[CryptoCall, ...]
    graph_call_count: int
    max_candidates: int
    max_candidate_bytes: int
    max_aggregate_bytes: int
    max_json_depth: int
    max_json_members: int
    max_findings: int
    max_retained_materials: int


CryptoVerifier = Callable[[CryptoProbe], bool]


def _not_implemented(location: str, phase: Phase = Phase.CURRENT) -> Finding:
    return Finding("protocol", phase.value, "ACP.NOT_IMPLEMENTED", location)


def canonical_json_bytes(value: object) -> bytes:
    del value
    return b""


def candidate_identity(document_without_id: Mapping[str, object]) -> str:
    del document_without_id
    return "0" * 64


def semantic_projection(matrix_document: Mapping[str, object]) -> Mapping[str, object]:
    del matrix_document
    return {}


def semantic_sha256(matrix_document: Mapping[str, object]) -> str:
    del matrix_document
    return "0" * 64


def normalized_case_catalog(
    matrix_document: Mapping[str, object],
) -> tuple[MatrixCase, ...]:
    del matrix_document
    return ()


def parse_matrix_stimulus(fixture_bytes: bytes) -> MatrixStimulusParse:
    del fixture_bytes
    return MatrixStimulusParse(None, (_not_implemented("matrix-stimulus"),))


def execute_matrix_fixture(
    fixture_bytes: bytes,
    *,
    crypto_verifier: CryptoVerifier,
) -> MatrixFixtureExecution:
    del fixture_bytes, crypto_verifier
    return MatrixFixtureExecution(None, (_not_implemented("matrix-fixture"),))


def verify_ed25519(public_key: bytes, message: bytes, signature: bytes) -> bool:
    del public_key, message, signature
    return False


def budget_disposition(charged_lines: int, cap: int) -> BudgetDisposition:
    del charged_lines, cap
    return BudgetDisposition.STOP_BEFORE_GREEN


def artifact_bound_findings(
    *,
    matrix_bytes: bytes,
    freeze_bytes: bytes,
    finding_count: int,
    retained_material_count: int,
    matrix_row_count: int,
) -> tuple[Finding, ...]:
    del matrix_bytes, freeze_bytes, finding_count, retained_material_count, matrix_row_count
    return (_not_implemented("artifact-bounds"),)


def convergence_blockers(
    *,
    unresolved_implementation_nodes: tuple[str, ...],
    unresolved_review_findings: tuple[str, ...],
    surviving_mutants: tuple[str, ...],
    focused_failures: tuple[str, ...],
) -> tuple[int, int]:
    del (
        unresolved_implementation_nodes,
        unresolved_review_findings,
        surviving_mutants,
        focused_failures,
    )
    return (1, 1)


def filesystem_threat_document_findings(
    documents: tuple[tuple[str, str], ...],
) -> tuple[Finding, ...]:
    del documents
    return (_not_implemented("filesystem-threat-documents"),)


def validate_matrix_bytes(
    matrix_bytes: bytes,
    freeze_bytes: bytes | None,
    *,
    expected_red_identity: Mapping[str, object] | None = None,
) -> MatrixValidation:
    del matrix_bytes, freeze_bytes, expected_red_identity
    return MatrixValidation(
        findings=(_not_implemented("matrix"),),
        semantic_sha256="0" * 64,
        invariant_ids=(),
        blocker_classes=(BlockerClass.IMPLEMENTATION,),
    )


def validate_repository_freeze(root: str | Path = ROOT) -> tuple[Finding, ...]:
    del root
    return (_not_implemented("repository-freeze"),)


def discover_git_repository(root: str | Path) -> GitDiscoveryResult:
    del root
    return GitDiscoveryResult(None, (_not_implemented("git-metadata"),))


def _read_git_metadata_nofollow(
    root: str | Path,
    *,
    provenance: GitMetadataProvenance,
    io: MetadataIO,
) -> GitMetadataReadResult:
    del root, provenance, io
    return GitMetadataReadResult(None, (_not_implemented("git-metadata"),))


def _read_governed_bytes(root: Path, relative: str) -> GovernedReadResult:
    del root
    return GovernedReadResult(None, (_not_implemented(relative),))


def evaluate_candidates(
    candidate_documents: tuple[bytes, ...],
    *,
    context: EvaluationContext,
    crypto_verifier: CryptoVerifier,
) -> Evaluation:
    del candidate_documents, crypto_verifier
    return Evaluation(
        findings=(_not_implemented("candidate-set", context.expected_phase),),
        historical_verdict=Verdict.UNAVAILABLE,
        current_verdict=Verdict.UNAVAILABLE,
        acceptance_verdict=Verdict.UNAVAILABLE,
        phase_verdicts=(
            PhaseVerdict(Phase.HISTORICAL, Verdict.UNAVAILABLE),
            PhaseVerdict(Phase.CURRENT, Verdict.UNAVAILABLE),
            PhaseVerdict(Phase.ACCEPTANCE, Verdict.UNAVAILABLE),
        ),
        eligible_candidate_ids=(),
        selected_candidate_id=None,
        stage_calls=(),
        crypto_calls=(),
        graph_call_count=0,
    )


def reconstruct_candidates(
    candidate_documents: tuple[bytes, ...],
    *,
    retained: RetainedEvaluation,
    context: EvaluationContext,
    crypto_verifier: CryptoVerifier,
) -> Evaluation:
    del candidate_documents, retained, crypto_verifier
    return Evaluation(
        findings=(_not_implemented("retained-evaluation", context.expected_phase),),
        historical_verdict=Verdict.UNAVAILABLE,
        current_verdict=Verdict.UNAVAILABLE,
        acceptance_verdict=Verdict.UNAVAILABLE,
        phase_verdicts=(
            PhaseVerdict(Phase.HISTORICAL, Verdict.UNAVAILABLE),
            PhaseVerdict(Phase.CURRENT, Verdict.UNAVAILABLE),
            PhaseVerdict(Phase.ACCEPTANCE, Verdict.UNAVAILABLE),
        ),
        eligible_candidate_ids=(),
        selected_candidate_id=None,
        stage_calls=(),
        crypto_calls=(),
        graph_call_count=0,
    )


def retained_equality_findings(
    observed: RetainedEvaluation, expected: RetainedEvaluation
) -> tuple[Finding, ...]:
    del observed, expected
    return (_not_implemented("retained-equality"),)


def route_findings(
    root: Path = ROOT, *, changed_paths: tuple[str, ...] | None = None
) -> tuple[Finding, ...]:
    del root, changed_paths
    return (_not_implemented("route"),)


def static_boundary_findings(source: str) -> tuple[Finding, ...]:
    del source
    return (_not_implemented("static-boundary"),)


def main() -> int:
    result = validate_matrix_bytes(
        MATRIX_PATH.read_bytes() if MATRIX_PATH.is_file() else b"",
        FREEZE_PATH.read_bytes() if FREEZE_PATH.is_file() else None,
    )
    for finding in result.findings:
        print(f"{finding.stage}|{finding.phase}|{finding.code}|{finding.location}")
    return 0 if not result.findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
