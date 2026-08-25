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
    "callbackArgumentVector",
    "callbackVector",
    "callbackResultVector",
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
STATIC_GIT_METADATA_INTER_ROLE_TRIGGER_RECEIPT_FIELDS = (
    "role",
    "afterRole",
    "path",
    "beforeType",
    "afterType",
    "identityChanged",
    "triggered",
)
STATIC_GIT_METADATA_FIXTURE_PARENT_ABSOLUTE_LENGTH = 700
STATIC_GIT_METADATA_FIXTURE_PARENT_LEXICAL_DEPTH = 18
STATIC_GIT_METADATA_FIXTURE_ROOT_RELATION_FIELDS = (
    "slot",
    "relativeFilesystemByteDelta",
    "relativeLexicalDepthDelta",
)
STATIC_GIT_METADATA_FIXTURE_ROOT_RELATIONS = (("A", 0, 0), ("B", 81, 6))
STATIC_GIT_METADATA_FIXTURE_ROOT_CHILD_COMPONENT_BYTES = (12, 12, 12, 12, 12, 15)
STATIC_GIT_METADATA_FIXTURE_PORTABLE_OWNER_MODELS = (("darwin", 27, 4), ("linux", 17, 3))
STATIC_GIT_METADATA_FIXTURE_ROOT_RELATION_SHA256 = (
    "9fd9494f55f68a5a611dd9be45bdc325f09045f264d42e44cb6ecd834829f019"
)
STATIC_GIT_METADATA_FIXTURE_OWNERSHIP_CONTRACT = (
    "one-cleanup-owned-platform-temporary-base",
    "equal-width-A-B-slot-components",
    "B-only-six-component-relative-suffix",
    "resolved-base-inode-owned-and-stable",
    "feasibility-plan-proved-before-creation",
    "infeasible-model-fails-before-filesystem-mutation",
    "no-hardcoded-private-tmp",
)
STATIC_GIT_METADATA_TRIGGER_RECEIPT_SCHEDULE_CONTRACT = (
    "fixture-parent-fsencoded-length-exactly-700",
    "fixture-parent-lexical-depth-exactly-18",
    "one-cleanup-owned-platform-temporary-base",
    "equal-width-A-B-slots",
    "B-relative-delta-exactly-81-filesystem-bytes-and-6-lexical-components",
    "resolved-base-inode-stable-through-both-collectors",
    "feasible-final-components-each-8-through-255-bytes-before-creation",
    "fixed-width-neutral-child-slots-before-two-variable-final-components",
    "raw-read-requests-equal-cap-minus-consumed",
    "raw-read-chunks-concatenate-to-observed-payload",
    "raw-read-request-chunk-count-and-type-vectors-exact",
    "raw-close-attempt-result-and-order-vectors-exact",
    "path-content-normalized-only-for-portable-payload-identity",
    "run-complete-129-case-collector-independently-under-each-root",
    "separate-execution-stimulus-trigger-receipt-raw-read-close-order-normalized-payload-catalogs-row-and-digest-equal",
)
STATIC_GIT_METADATA_TRIGGER_RECEIPT_COUNT = 129
STATIC_GIT_METADATA_TRIGGER_RECEIPT_SHA256 = (
    "a7891e4113c89b48be4dedcc3f260d5211d622853ec16f52b5f4f9e355015d0e"
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
    "1072b8834f65136320bf419d760eae50cf916fc8b411a90362f2c100a6fdcf73"
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
    "slot",
    "relativeRootShape",
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
STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPE_COUNT = 2
STATIC_GIT_METADATA_ROOT_REPLAY_RUNTIME_CONTRACT = (
    "derive-runtime-envelope-from-owned-base-and-relative-relation",
    "final-components-each-8-through-255-filesystem-bytes",
    "governed-parent-exactly-700-bytes-depth-18",
    "both-evidence-identities-exact-and-equal",
)
STATIC_GIT_METADATA_ROOT_REPLAY_EVIDENCE_IDENTITY_SHA256 = (
    "d47f7eb94ac3ad3e841ba4e99741e2a346683f059bb493fc120b03c5d40eeeee"
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
STATIC_GIT_METADATA_HISTORICAL_PAIR_CONTAINMENT_FIELDS = (
    "historicalGroupName",
    "executionPair",
    "uniqueCompleteClass",
)
STATIC_GIT_METADATA_HISTORICAL_PAIR_CONTAINMENTS = (
    (
        "configured-removed-linked-pre-root-fstat",
        ("pre-root-symlink@linked", "fstat-type@linked"),
        "configured-removed-linked-pre-root-class",
    ),
    (
        "configured-removed-linked-pre-root-open",
        ("pre-root-symlink@linked", "open-error@linked"),
        "configured-removed-linked-pre-root-class",
    ),
    (
        "configured-removed-conventional-ancestor",
        ("root-replacement@conventional", "ancestor-replacement@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-between",
        (
            "root-replacement@conventional",
            "between-read-conventional-dot-git@conventional",
        ),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-final",
        ("root-replacement@conventional", "final-binding-revalidation@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-leaf",
        ("root-replacement@conventional", "leaf-replacement@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-fstat-device",
        ("root-replacement@conventional", "fstat-device@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-fstat-inode",
        ("root-replacement@conventional", "fstat-inode@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-fstat-type",
        ("root-replacement@conventional", "fstat-type@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-lstat",
        ("root-replacement@conventional", "lstat-error@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-open",
        ("root-replacement@conventional", "open-error@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-conventional-close",
        ("root-replacement@conventional", "close-error@conventional"),
        "configured-removed-conventional-race-and-io-class",
    ),
    (
        "configured-removed-linked-root-leaf",
        ("root-replacement@linked", "leaf-replacement@linked"),
        "configured-removed-linked-root-class",
    ),
    (
        "configured-removed-linked-root-postread",
        ("root-replacement@linked", "post-read-device@linked"),
        "configured-removed-linked-root-class",
    ),
    (
        "configured-removed-linked-between-read",
        (
            "between-read-linked-directory@linked",
            "between-read-common-directory@linked",
        ),
        "configured-removed-linked-between-read-class",
    ),
    (
        "configured-removed-linked-fstat-lstat",
        ("fstat-inode@linked", "lstat-error@linked"),
        "configured-removed-linked-fstat-io-class",
    ),
    (
        "configured-removed-linked-fstat-close",
        ("fstat-inode@linked", "close-error@linked"),
        "configured-removed-linked-fstat-io-class",
    ),
)
STATIC_GIT_METADATA_HISTORICAL_PAIR_CONTAINMENT_COUNT = 17
STATIC_GIT_METADATA_HISTORICAL_PAIR_CONTAINMENT_SHA256 = (
    "c89bc0e10ccc1cb720014aba723f9a4ecda4c75a5973311d97029e9bc4a33e8e"
)
STATIC_GIT_METADATA_HISTORICAL_CROSS_CLASS_MUTANT = (
    "MUT-HISTORICAL-PAIR-CROSS-CLASS",
    ("pre-root-symlink@linked", "root-replacement@conventional"),
    "configuredRemovedHistoricalPairs[17]",
)
STATIC_GIT_METADATA_HISTORICAL_CROSS_CLASS_FINDING = (
    "evidence",
    "CURRENT",
    "ACP.EVIDENCE.HISTORICAL_PAIR_RELATION",
    "configuredRemovedHistoricalPairs[17]",
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
    "callbackArguments",
    "callbackEvents",
    "roleEvents",
    "metadataEvents",
    "statEvents",
    "exceptionEvents",
    "closeEffects",
    "interRoleEvidence",
    "rawEvidenceIdentity",
    "projectedCallback",
    "projectedTarget",
    "projectedPhase",
    "projectedEffect",
    "observedTargetRole",
    "observedTargetPath",
    "observedRoleOrdinal",
    "observedCallbackOrdinal",
    "executionEvidenceIdentity",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS = (
    "callbackArguments",
    "callbackEvents",
    "roleEvents",
    "metadataEvents",
    "statEvents",
    "exceptionEvents",
    "closeEffects",
    "interRoleEvidence",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS = (
    "callback",
    "target",
    "phase",
    "effect",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_IDENTITY_CONTRACT = (
    "capture-root-relative-or-descriptor-role-ordinal-actual-callback-arguments-with-argument-type-and-event-ordinal",
    "derive-raw-evidence-identity-from-callback-role-metadata-stat-exception-close-and-inter-role-events-before-semantic-projection",
    "pure-projector-accepts-only-raw-receipt-and-derives-semantic-fields",
    "must-not-read-configured-plan-case-row-expected-finding-or-terminal-result",
    "separate-binder-validates-raw-integrity-and-exact-callback-target-phase-effect-against-declared-plan",
)
STATIC_GIT_METADATA_CONFIGURED_RAW_FIELD_CAPS = (
    ("callbackArguments", 1024),
    ("callbackEvents", 1024),
    ("roleEvents", 16),
    ("metadataEvents", 1024),
    ("statEvents", 768),
    ("exceptionEvents", 32),
    ("closeEffects", 512),
    ("interRoleEvidence", 7),
)
STATIC_GIT_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP = 4096
STATIC_GIT_METADATA_CONFIGURED_EXCEPTION_TYPES = (
    "FileNotFoundError",
    "NotADirectoryError",
    "OSError",
)
STATIC_GIT_METADATA_CONFIGURED_CLOSED_ROLES = (
    "discovery",
    "dot_git",
    "linked_git_dir",
    "backlink",
    "commondir",
    "common_dir",
    "prohibited_grafts",
    "prohibited_shallow",
    "prohibited_alternates",
    "prohibited_http_alternates",
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ROLE_RELATION_FIELDS = (
    "role",
    "afterRole",
    "path",
    "beforeType",
    "afterType",
    "identityChanged",
    "triggered",
    "target",
    "phase",
    "effect",
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ROLE_RELATIONS = (
    (
        "role=inter-role-mutation",
        "dot_git",
        "$TMP/$CASE/repository/.git",
        "16384",
        "16384",
        "true",
        "true",
        "dot-git",
        "after-dot-git-read",
        "dot-git-replacement",
    ),
    (
        "role=inter-role-mutation",
        "prohibited_http_alternates",
        "$TMP/$CASE/repository/.git",
        "16384",
        "16384",
        "true",
        "true",
        "dot-git",
        "after-prohibited-http-alternates-read",
        "identity-replacement",
    ),
    (
        "role=inter-role-mutation",
        "linked_git_dir",
        "$TMP/$CASE/source/repository/.git/worktrees/linked",
        "16384",
        "16384",
        "true",
        "true",
        "linked-git-dir",
        "after-linked-git-dir-read",
        "linked-dir-replacement",
    ),
    (
        "role=inter-role-mutation",
        "common_dir",
        "$TMP/$CASE/source/repository/.git",
        "16384",
        "16384",
        "true",
        "true",
        "common-dir",
        "after-common-dir-read",
        "common-dir-replacement",
    ),
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ROLE_SCHEDULE_FIELDS = (
    "afterRole",
    "roleSchedule",
    "targetRoleOrdinal",
    "triggerRoleOrdinal",
    "terminalRoleOrdinal",
    "benignExceptionLedger",
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ROLE_SCHEDULES = (
    ("dot_git", ("discovery", "dot_git", "common_dir"), 1, 1, 2, ()),
    ("linked_git_dir", ("discovery", "dot_git", "linked_git_dir", "backlink"), 2, 2, 3, ()),
    (
        "common_dir",
        (
            "discovery",
            "dot_git",
            "linked_git_dir",
            "backlink",
            "commondir",
            "common_dir",
            "prohibited_grafts",
        ),
        5,
        5,
        6,
        (),
    ),
    (
        "prohibited_http_alternates",
        (
            "discovery",
            "dot_git",
            "common_dir",
            "prohibited_grafts",
            "prohibited_shallow",
            "prohibited_alternates",
            "prohibited_http_alternates",
            "dot_git",
        ),
        1,
        6,
        7,
        (
            "event-64:role-prohibited_grafts:roleOrdinal-3:lstat:lstat:error:FileNotFoundError:errno",
            "event-61:role-prohibited_shallow:roleOrdinal-4:lstat:lstat:error:FileNotFoundError:errno",
            "event-67:role-prohibited_alternates:roleOrdinal-5:lstat:lstat:error:FileNotFoundError:errno",
            "event-67:role-prohibited_http_alternates:roleOrdinal-6:lstat:lstat:error:FileNotFoundError:errno",
        ),
    ),
)
STATIC_GIT_METADATA_CONFIGURED_ALLOWED_ROLE_SCHEDULES = (
    ("discovery",),
    ("discovery", "dot_git"),
    ("discovery", "dot_git", "common_dir"),
    ("discovery", "dot_git", "common_dir", "prohibited_grafts"),
    ("discovery", "dot_git", "linked_git_dir", "backlink"),
    (
        "discovery",
        "dot_git",
        "linked_git_dir",
        "backlink",
        "commondir",
        "common_dir",
        "prohibited_grafts",
    ),
    (
        "discovery",
        "dot_git",
        "common_dir",
        "prohibited_grafts",
        "prohibited_shallow",
        "prohibited_alternates",
        "prohibited_http_alternates",
        "dot_git",
    ),
)
STATIC_GIT_METADATA_CONFIGURED_NON_INTER_ALLOWED_ROLE_SCHEDULES = (
    ("discovery",),
    ("discovery", "dot_git"),
    ("discovery", "dot_git", "common_dir", "prohibited_grafts"),
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_COUNT = 22
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_SHA256 = (
    "a35b10c41378c50b01ab03110481bc068667454fd3927b77f7162d34a5ce6d02"
)
STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDING_FIELDS = (
    "executionEvidenceIdentity",
    "rawEvidenceIdentity",
    "observed",
    "projection",
)
STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDINGS = (
    (
        "a3a1b0be111f71753bcf20517e1943aaa7d27614bba652b8177d4a7c57937565",
        "73742ccabcee1a95e44f26adeab4a86bb0a15c75e58cf2260a03b94f1fbbd78c",
        ("discovery", "root-ancestor-distance-1", 0, 52),
        ("filesystem-state", "root-ancestor", "before-discovery", "symlink"),
    ),
    (
        "593c6bd0b8f186ca3b1ae13dcff3d296b14b18fa3a7bd9398aec2f4aa1dd0aeb",
        "71bb2fc736c30997de7b43f2fcae5f9a6f2ea912ff537ed1fd57b7224863b24a",
        ("discovery", "$ROOT", 0, 55),
        ("lstat", "root", "after-lstat", "identity-replacement"),
    ),
    (
        "b0074bd70c20d90f671e24140810c1755cc7fb22e1b7f92547ea12831997b5c9",
        "71bb2fc736c30997de7b43f2fcae5f9a6f2ea912ff537ed1fd57b7224863b24a",
        ("discovery", "$ROOT", 0, 55),
        ("lstat", "root", "after-lstat", "identity-replacement"),
    ),
    (
        "8ceeaac02f96030748d13501bed95810e1a8fb8b01f1ceb365b6ec5d8ca59364",
        "4b99de7464f2e4bc4aec212291c5013ca9f13612feca0978bb1b9374483db3bc",
        ("prohibited_grafts", "$ROOT/.git/info", 3, 61),
        ("lstat", "info-ancestor", "after-lstat", "identity-replacement"),
    ),
    (
        "2f5ce9685bd567414dc7fc54eae3fbeccb9f1e84fc1a8d8782792286c77484b5",
        "3848496cb0c10fb9f06f1161f4673536b4a8d61320f97e7ac32d4b8f61602ae6",
        ("dot_git", "$ROOT/.git", 1, 59),
        ("inter-role", "dot-git", "after-dot-git-read", "dot-git-replacement"),
    ),
    (
        "2458c5284cd964554257c0dc3553d4a4482b396e644fe56254b2b382473b9ab3",
        "9f7c95014930ad1f4b76bc02aa5d0f1560fa224749fb7a23975df93665d7357d",
        (
            "linked_git_dir",
            "fixture-relative:$TMP/$CASE/source/repository/.git/worktrees/linked",
            2,
            68,
        ),
        ("inter-role", "linked-git-dir", "after-linked-git-dir-read", "linked-dir-replacement"),
    ),
    (
        "f5376ec16aabb783e133a85c0952fe646371dc48d98991a1964b7beb45fbe6a7",
        "129ca143dc58e348666403d645702420923e0656a10ec7176465c2b7474c495a",
        ("common_dir", "fixture-relative:$TMP/$CASE/source/repository/.git", 5, 62),
        ("inter-role", "common-dir", "after-common-dir-read", "common-dir-replacement"),
    ),
    (
        "77f4eacc2f969545adaa64d380a609af884544f0dabddd090d5cf9c703640093",
        "40d9a589d51bb33742f095ea22f70e40758d8bc50b3bb66ce142a3706b3770e3",
        ("dot_git", "$ROOT/.git", 1, 59),
        ("inter-role", "dot-git", "after-prohibited-http-alternates-read", "identity-replacement"),
    ),
    (
        "80ee55baf4e860ae355d4bf0097a6208258fe62d9f161d616c8bd5e6e91ad634",
        "10e2457ce2ff455d76a4bd032b69b39649b96ce8230ef879806c3540437c9550",
        ("dot_git", "$ROOT/.git", 1, 58),
        ("lstat", "dot-git", "after-lstat", "identity-replacement"),
    ),
    (
        "d18e1b0aa5115adb0c0ab5a3ea38876e5da5487b59f8aa24936f71ca4f3c23f9",
        "6069fba60169d85fb013993f04b83c0970302df4154839a5e619116394a71c94",
        ("dot_git", "$ROOT/.git", 1, 58),
        ("lstat", "dot-git", "after-lstat", "identity-replacement"),
    ),
    (
        "4bcaa272c38e7cbead4c3728795d53292adfd430e9b7821ff1f67f787a6d5548",
        "6a4d3106293bc80fff7a5c1939ca389a7898c199a12be6b455126ccafacd314c",
        ("dot_git", "$ROOT/.git", 1, 60),
        ("fstat", "dot-git", "after-open", "device-drift"),
    ),
    (
        "2177f34d530a49af140b3ed532b270bbd5dc4f18c113d81ebdcfc111a068adda",
        "149b9079e402b6dac79419127cc790b93044ab6fd454389cea278c31dd38cd13",
        ("dot_git", "$ROOT/.git", 1, 60),
        ("fstat", "dot-git", "after-open", "inode-drift"),
    ),
    (
        "73393605285472cad58f94e0afbecf96435e9200f7ae3267dfc0262693757af9",
        "c4beb067c5b37d7725527c3282ed2e72b9920fbeb64d93228d28aba3d39ab363",
        ("dot_git", "$ROOT/.git", 1, 60),
        ("fstat", "dot-git", "after-open", "type-drift"),
    ),
    (
        "5c3904d883801b4353e2040407940a803aa1e03f540973c6f4e1ddba7e0e6361",
        "e24e12f6d49dcf941eaa4fa36c898b801c30e6255eb67d97f88bde0374cc83cb",
        ("dot_git", "$ROOT/.git", 1, 60),
        ("fstat", "dot-git", "after-open", "inode-drift"),
    ),
    (
        "8b62454071d06776f92132cca76ec8d50a3202a7e27a6bae5d1c1a2942f61adb",
        "653a6676aff1ec2ad79793df8ad9a5163f1dcd3ab84284ab7d65c325b5e36bf4",
        ("dot_git", "$ROOT/.git", 1, 60),
        ("fstat", "dot-git", "after-open", "type-drift"),
    ),
    (
        "2fc1e6382961df21711097f86494a0b0436bf228091c4dbb689717b0a5cb2cb0",
        "eb0d762b7f2587bd18d1fdf53bf74078d72dcf5aee7940caa1d9c48432a13c87",
        ("dot_git", "$ROOT/.git", 1, 63),
        ("lstat", "dot-git", "after-read", "device-drift"),
    ),
    (
        "eadb03d7cdd0b703abf12f4dd4a6124eef28f4cda210881791c385f652c7aedc",
        "1641d9fdbd42f9ff91753f6245c7d105eefc451f6968d78d35eb4ad39364ca00",
        ("dot_git", "$ROOT/.git", 1, 58),
        ("lstat", "dot-git", "initial-lstat", "os-error"),
    ),
    (
        "a34fff95d184999579124d3dab38a4d8195136f03f160c44a8f0b7b494094b88",
        "1641d9fdbd42f9ff91753f6245c7d105eefc451f6968d78d35eb4ad39364ca00",
        ("dot_git", "$ROOT/.git", 1, 58),
        ("lstat", "dot-git", "initial-lstat", "os-error"),
    ),
    (
        "fc45bc1ea087390aab635144d4bd531478f0814d5c19242a5719d5817d5ef6be",
        "6be94f7538b5eecb254ae969ba137363373ae337d8a7715c99460a2382315822",
        ("dot_git", "$ROOT/.git", 1, 59),
        ("open", "dot-git", "initial-open", "os-error"),
    ),
    (
        "f2055033dbade8565eb27b08c333497d00a0b354f7125366bf1f44a27dd300bb",
        "20a68bb53ebe4a5f9d04cb8af5baf01d58fc83a25d9fed2a639ac0015d962de1",
        ("dot_git", "$ROOT/.git", 1, 59),
        ("open", "dot-git", "initial-open", "os-error"),
    ),
    (
        "9b3d4cc0138560fb60bd26a5a9931d72537e1a63c3482a085dbc8a275d2d9349",
        "65a32b7ec483ffd4eed61eb01176403a49a2665fdf72237aa559b27d55c90963",
        ("discovery", "$ROOT", 0, 58),
        ("close", "root", "cleanup", "os-error"),
    ),
    (
        "b0f885b816bb37b59f48e7647e0f2b391f113d5213c96395d06e3d6bce357f2a",
        "65a32b7ec483ffd4eed61eb01176403a49a2665fdf72237aa559b27d55c90963",
        ("discovery", "$ROOT", 0, 58),
        ("close", "root", "cleanup", "os-error"),
    ),
)
STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDING_COUNT = 22
STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDING_SHA256 = (
    "9aed869589d56316ac76e8b6b7cd005da51a5edcc17cb926a6444468f84809d3"
)
STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAP_FIELDS = (
    "donorReceiptIndex",
    "recipientReceiptIndex",
)
STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAPS = (
    (1, 2),
    (8, 9),
    (11, 13),
    (12, 14),
    (16, 17),
    (18, 19),
    (20, 21),
)
STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAP_COUNT = 7
STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAP_SHA256 = (
    "421384f1402ffdad681b6062288eb0bcfba55834ef2f9e28f630b50a74ed4c49"
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_FIELDS = (
    "mutantId",
    "executionId",
    "expectedCoordinate",
    "mutationLayer",
    "changedFieldSet",
    "operation",
    "rawIdentityAction",
    "findingLocation",
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANTS = (
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-CALLBACK",
        "fstat-type@linked",
        "callbackEvents",
        "raw",
        "callbackEvents",
        "replace-custom-callback-with-other-closed-callback",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-TARGET",
        "fstat-type@linked",
        "callbackArguments.path",
        "raw",
        "callbackArguments",
        "replace-callback-target-argument",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.path",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-PHASE",
        "fstat-type@linked",
        "callbackArguments.eventOrdinal",
        "raw",
        "callbackArguments",
        "replace-callback-event-ordinal",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.eventOrdinal",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-EFFECT",
        "fstat-type@linked",
        "statEvents",
        "raw",
        "statEvents",
        "replace-stat-effect-evidence",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].statEvents",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-NOOP",
        "fstat-type@linked",
        "rawReceipt",
        "raw",
        "callbackEvents",
        "remove-custom-callback-trigger",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].rawReceipt",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-CLOSE-RESULT",
        "close-error@linked",
        "closeEffects",
        "raw",
        "closeEffects",
        "replace-observed-close-error-with-ok",
        "recompute-after-mutation",
        "configuredPlanReceipts[21].closeEffects",
    ),
    (
        "MUT-CONFIGURED-PLAN-RECEIPT-INTER-ROLE",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "replace-triggered-before-after-observation-with-unchanged",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-CONFIGURED-PLAN-DECLARED-DECOY",
        "fstat-type@linked",
        "effect",
        "declared",
        "declared",
        "replace-declared-plan-after-raw-projection",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].effect",
    ),
    (
        "MUT-CONFIGURED-PLAN-COPY",
        "fstat-type@linked",
        "effect",
        "projection",
        "projection+declared",
        "copy-declared-decoy-instead-of-projecting-raw-receipt",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].effect",
    ),
    (
        "MUT-INDEX-BOOL",
        "fstat-type@linked",
        "receiptIndex",
        "index",
        "index",
        "index-bool",
        "recompute-after-mutation",
        "configuredPlanReceipts[0].receiptIndex",
    ),
    (
        "MUT-INDEX-STRING",
        "fstat-type@linked",
        "receiptIndex",
        "index",
        "index",
        "index-string",
        "recompute-after-mutation",
        "configuredPlanReceipts[0].receiptIndex",
    ),
    (
        "MUT-INDEX-NEGATIVE",
        "fstat-type@linked",
        "receiptIndex",
        "index",
        "index",
        "index-negative",
        "recompute-after-mutation",
        "configuredPlanReceipts[0].receiptIndex",
    ),
    (
        "MUT-INDEX-N",
        "fstat-type@linked",
        "receiptIndex",
        "index",
        "index",
        "index-count",
        "recompute-after-mutation",
        "configuredPlanReceipts[0].receiptIndex",
    ),
    (
        "MUT-INDEX-NPLUS1",
        "fstat-type@linked",
        "receiptIndex",
        "index",
        "index",
        "index-count-plus-one",
        "recompute-after-mutation",
        "configuredPlanReceipts[0].receiptIndex",
    ),
    (
        "MUT-RAW-LIST",
        "fstat-type@linked",
        "rawReceipt",
        "raw",
        "rawReceipt",
        "raw-list",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].rawReceipt",
    ),
    (
        "MUT-RAW-SHORT",
        "fstat-type@linked",
        "rawReceipt",
        "raw",
        "rawReceipt",
        "raw-short",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].rawReceipt",
    ),
    (
        "MUT-RAW-LONG",
        "fstat-type@linked",
        "rawReceipt",
        "raw",
        "rawReceipt",
        "raw-long",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].rawReceipt",
    ),
    (
        "MUT-FIELD-TYPE-CALLBACKARGUMENTS",
        "fstat-type@linked",
        "callbackArguments",
        "raw",
        "callbackArguments",
        "field-list-0",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments",
    ),
    (
        "MUT-FIELD-TYPE-CALLBACKEVENTS",
        "fstat-type@linked",
        "callbackEvents",
        "raw",
        "callbackEvents",
        "field-list-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents",
    ),
    (
        "MUT-FIELD-TYPE-ROLEEVENTS",
        "fstat-type@linked",
        "roleEvents",
        "raw",
        "roleEvents",
        "field-list-2",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents",
    ),
    (
        "MUT-FIELD-TYPE-METADATAEVENTS",
        "fstat-type@linked",
        "metadataEvents",
        "raw",
        "metadataEvents",
        "field-list-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].metadataEvents",
    ),
    (
        "MUT-FIELD-TYPE-STATEVENTS",
        "fstat-type@linked",
        "statEvents",
        "raw",
        "statEvents",
        "field-list-4",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].statEvents",
    ),
    (
        "MUT-FIELD-TYPE-EXCEPTIONEVENTS",
        "fstat-type@linked",
        "exceptionEvents",
        "raw",
        "exceptionEvents",
        "field-list-5",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].exceptionEvents",
    ),
    (
        "MUT-FIELD-TYPE-CLOSEEFFECTS",
        "fstat-type@linked",
        "closeEffects",
        "raw",
        "closeEffects",
        "field-list-6",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].closeEffects",
    ),
    (
        "MUT-FIELD-TYPE-INTERROLEEVIDENCE",
        "fstat-type@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "field-list-7",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].interRoleEvidence",
    ),
    (
        "MUT-FIELD-CAP-CALLBACKARGUMENTS",
        "fstat-type@linked",
        "callbackArguments.countLimit",
        "raw",
        "callbackArguments",
        "field-over-cap-0",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.countLimit",
    ),
    (
        "MUT-FIELD-CAP-CALLBACKEVENTS",
        "fstat-type@linked",
        "callbackEvents.countLimit",
        "raw",
        "callbackEvents",
        "field-over-cap-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents.countLimit",
    ),
    (
        "MUT-FIELD-CAP-ROLEEVENTS",
        "fstat-type@linked",
        "roleEvents.countLimit",
        "raw",
        "roleEvents",
        "field-over-cap-2",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents.countLimit",
    ),
    (
        "MUT-FIELD-CAP-METADATAEVENTS",
        "fstat-type@linked",
        "metadataEvents.countLimit",
        "raw",
        "metadataEvents",
        "field-over-cap-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].metadataEvents.countLimit",
    ),
    (
        "MUT-FIELD-CAP-STATEVENTS",
        "fstat-type@linked",
        "statEvents.countLimit",
        "raw",
        "statEvents",
        "field-over-cap-4",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].statEvents.countLimit",
    ),
    (
        "MUT-FIELD-CAP-EXCEPTIONEVENTS",
        "fstat-type@linked",
        "exceptionEvents.countLimit",
        "raw",
        "exceptionEvents",
        "field-over-cap-5",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].exceptionEvents.countLimit",
    ),
    (
        "MUT-FIELD-CAP-CLOSEEFFECTS",
        "fstat-type@linked",
        "closeEffects.countLimit",
        "raw",
        "closeEffects",
        "field-over-cap-6",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].closeEffects.countLimit",
    ),
    (
        "MUT-FIELD-CAP-INTERROLEEVIDENCE",
        "fstat-type@linked",
        "interRoleEvidence.countLimit",
        "raw",
        "interRoleEvidence",
        "field-over-cap-7",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].interRoleEvidence.countLimit",
    ),
    (
        "MUT-FIELD-ITEM-CALLBACKARGUMENTS",
        "fstat-type@linked",
        "callbackArguments",
        "raw",
        "callbackArguments",
        "field-item-type-0",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments",
    ),
    (
        "MUT-FIELD-ITEM-CALLBACKEVENTS",
        "fstat-type@linked",
        "callbackEvents",
        "raw",
        "callbackEvents",
        "field-item-type-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents",
    ),
    (
        "MUT-FIELD-ITEM-ROLEEVENTS",
        "fstat-type@linked",
        "roleEvents",
        "raw",
        "roleEvents",
        "field-item-type-2",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents",
    ),
    (
        "MUT-FIELD-ITEM-METADATAEVENTS",
        "fstat-type@linked",
        "metadataEvents",
        "raw",
        "metadataEvents",
        "field-item-type-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].metadataEvents",
    ),
    (
        "MUT-FIELD-ITEM-STATEVENTS",
        "fstat-type@linked",
        "statEvents",
        "raw",
        "statEvents",
        "field-item-type-4",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].statEvents",
    ),
    (
        "MUT-FIELD-ITEM-EXCEPTIONEVENTS",
        "fstat-type@linked",
        "exceptionEvents",
        "raw",
        "exceptionEvents",
        "field-item-type-5",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].exceptionEvents",
    ),
    (
        "MUT-FIELD-ITEM-CLOSEEFFECTS",
        "fstat-type@linked",
        "closeEffects",
        "raw",
        "closeEffects",
        "field-item-type-6",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].closeEffects",
    ),
    (
        "MUT-FIELD-ITEM-INTERROLEEVIDENCE",
        "fstat-type@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "field-item-type-7",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].interRoleEvidence",
    ),
    (
        "MUT-FIELD-INVALID-UTF8",
        "fstat-type@linked",
        "callbackArguments.itemEncoding",
        "raw",
        "callbackArguments",
        "field-invalid-utf8",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.itemEncoding",
    ),
    (
        "MUT-RAW-IDENTITY-STALE",
        "fstat-type@linked",
        "rawEvidenceIdentity",
        "raw",
        "statEvents",
        "preserve-stale-identity",
        "preserve-stale",
        "configuredPlanReceipts[14].rawEvidenceIdentity",
    ),
    (
        "MUT-ROLE-EMPTY",
        "fstat-type@linked",
        "roleEvents",
        "raw",
        "roleEvents",
        "role-empty",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents",
    ),
    (
        "MUT-ROLE-FIRST",
        "fstat-type@linked",
        "roleEvents",
        "raw",
        "roleEvents",
        "role-first-not-discovery",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents",
    ),
    (
        "MUT-ROLE-ORDINAL",
        "fstat-type@linked",
        "roleEvents",
        "raw",
        "roleEvents",
        "role-ordinal-duplicate",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents",
    ),
    (
        "MUT-ROLE-REENTER",
        "fstat-type@linked",
        "roleEvents",
        "raw",
        "roleEvents",
        "role-reentered",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].roleEvents",
    ),
    (
        "MUT-CALLBACK-REORDER",
        "fstat-type@linked",
        "callbackEvents",
        "raw",
        "callbackEvents",
        "callback-reorder",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents",
    ),
    (
        "MUT-CALLBACK-EVENT-GAP",
        "fstat-type@linked",
        "callbackArguments.eventOrdinal",
        "raw",
        "callbackArguments",
        "callback-event-gap",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.eventOrdinal",
    ),
    (
        "MUT-CUSTOM-ADD",
        "fstat-type@linked",
        "callbackEvents.source",
        "raw",
        "callbackEvents",
        "custom-add-operation",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents.source",
    ),
    (
        "MUT-CUSTOM-REMOVE",
        "fstat-type@linked",
        "callbackEvents.source",
        "raw",
        "callbackEvents",
        "custom-remove-operation",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackEvents.source",
    ),
    (
        "MUT-PATH-PREFIX",
        "fstat-type@linked",
        "callbackArguments.path",
        "raw",
        "callbackArguments",
        "path-root-prefix",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.path",
    ),
    (
        "MUT-PATH-DOTDOT",
        "fstat-type@linked",
        "callbackArguments.path",
        "raw",
        "callbackArguments",
        "path-dotdot",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.path",
    ),
    (
        "MUT-PATH-CROSS-ROLE",
        "fstat-type@linked",
        "callbackArguments.path",
        "raw",
        "callbackArguments",
        "path-cross-role",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.path",
    ),
    (
        "MUT-ROOT-ANCHOR-REBASE",
        "fstat-type@linked",
        "callbackArguments.rootAnchor",
        "raw",
        "callbackArguments",
        "root-anchor-rebase",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.rootAnchor",
    ),
    (
        "MUT-STAT-OMIT",
        "fstat-type@linked",
        "statEvents",
        "raw",
        "statEvents",
        "stat-omit",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].statEvents",
    ),
    (
        "MUT-EXCEPTION-ADD",
        "fstat-type@linked",
        "exceptionEvents",
        "raw",
        "exceptionEvents",
        "exception-add",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].exceptionEvents",
    ),
    (
        "MUT-CLOSE-REORDER",
        "close-error@linked",
        "closeEffects",
        "raw",
        "closeEffects",
        "close-reorder",
        "recompute-after-mutation",
        "configuredPlanReceipts[21].closeEffects",
    ),
    (
        "MUT-CLOSE-RESULT",
        "close-error@linked",
        "closeEffects",
        "raw",
        "closeEffects",
        "close-result-mismatch",
        "recompute-after-mutation",
        "configuredPlanReceipts[21].closeEffects",
    ),
    (
        "MUT-READ-COUNT-ZERO",
        "post-read-device@linked",
        "callbackArguments.read",
        "raw",
        "callbackArguments",
        "read-count-zero",
        "recompute-after-mutation",
        "configuredPlanReceipts[15].callbackArguments.read",
    ),
    (
        "MUT-READ-COUNT-WRONG",
        "post-read-device@linked",
        "callbackArguments.read",
        "raw",
        "callbackArguments",
        "read-count-wrong",
        "recompute-after-mutation",
        "configuredPlanReceipts[15].callbackArguments.read",
    ),
    (
        "MUT-READ-CHUNK-OVERSIZE",
        "post-read-device@linked",
        "metadataEvents.read",
        "raw",
        "metadataEvents",
        "read-chunk-oversize",
        "recompute-after-mutation",
        "configuredPlanReceipts[15].metadataEvents.read",
    ),
    (
        "MUT-READ-EOF-OMIT",
        "post-read-device@linked",
        "metadataEvents.postLstat",
        "raw",
        "callbackArguments+callbackEvents+metadataEvents+statEvents+closeEffects",
        "read-eof-omit",
        "recompute-after-mutation",
        "configuredPlanReceipts[15].metadataEvents.postLstat",
    ),
    (
        "MUT-READ-ZERO-FIRST",
        "post-read-device@linked",
        "metadataEvents.read",
        "raw",
        "metadataEvents",
        "read-zero-first",
        "recompute-after-mutation",
        "configuredPlanReceipts[15].metadataEvents.read",
    ),
    (
        "MUT-READ-WORK-AFTER-POST",
        "post-read-device@linked",
        "metadataEvents.postLstat",
        "raw",
        "callbackArguments+callbackEvents+metadataEvents+statEvents+closeEffects",
        "read-work-after-post",
        "recompute-after-mutation",
        "configuredPlanReceipts[15].metadataEvents.postLstat",
    ),
    (
        "MUT-FSTAT-DUPLICATE",
        "fstat-type@linked",
        "metadataEvents.fstat",
        "raw",
        "callbackArguments+callbackEvents+metadataEvents+statEvents+closeEffects",
        "fstat-duplicate",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].metadataEvents.fstat",
    ),
    (
        "MUT-METADATA-REORDER",
        "fstat-type@linked",
        "metadataEvents",
        "raw",
        "metadataEvents",
        "metadata-reorder",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].metadataEvents",
    ),
    (
        "MUT-INTER-LEADING",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-leading-key",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-AFTERROLE",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-after-role",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-PATH",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-path",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-BEFORETYPE",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-before-type",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-AFTERTYPE",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-after-type",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-IDENTITY",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-identity",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-TRIGGERED",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-triggered",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-TERMINAL-SUCCESS",
        "between-read-linked-directory@linked",
        "interRoleEvidence.terminalRelation",
        "raw",
        "metadataEvents+statEvents",
        "inter-terminal-success",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.terminalRelation",
    ),
    (
        "MUT-INTER-PARENT-ROLE",
        "between-read-linked-directory@linked",
        "interRoleEvidence.terminalRelation",
        "raw",
        "metadataEvents+statEvents",
        "inter-parent-role",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.terminalRelation",
    ),
    (
        "MUT-INTER-TARGET-PROVENANCE",
        "between-read-linked-directory@linked",
        "interRoleEvidence.targetProvenance",
        "raw",
        "callbackArguments+callbackEvents+metadataEvents+statEvents+closeEffects",
        "inter-target-provenance",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.targetProvenance",
    ),
    (
        "MUT-INTER-MARKER-BEFORE",
        "between-read-linked-directory@linked",
        "interRoleEvidence.triggerOrdinal",
        "raw",
        "roleEvents",
        "inter-marker-before",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.triggerOrdinal",
    ),
    (
        "MUT-INTER-MARKER-AFTER",
        "between-read-linked-directory@linked",
        "interRoleEvidence.triggerOrdinal",
        "raw",
        "roleEvents",
        "inter-marker-after",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.triggerOrdinal",
    ),
    (
        "MUT-INTER-MARKER-PHYSICAL-REORDER",
        "between-read-linked-directory@linked",
        "interRoleEvidence.triggerOrdinal",
        "raw",
        "roleEvents",
        "inter-marker-physical-reorder",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.triggerOrdinal",
    ),
    (
        "MUT-INTER-ARM-MISSING",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-arm-missing",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-ARM-EXTRA",
        "between-read-linked-directory@linked",
        "interRoleEvidence.countLimit",
        "raw",
        "interRoleEvidence",
        "inter-arm-extra",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence.countLimit",
    ),
    (
        "MUT-INTER-ARM-REORDER",
        "between-read-linked-directory@linked",
        "interRoleEvidence",
        "raw",
        "interRoleEvidence",
        "inter-arm-reorder",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-OBSERVED-PATH",
        "between-read-linked-directory@linked",
        "observedTargetPath",
        "observed",
        "observed",
        "observed-coordinate-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].observedTargetPath",
    ),
    (
        "MUT-INTER-OBSERVED-CALLBACK",
        "between-read-linked-directory@linked",
        "observedCallbackOrdinal",
        "observed",
        "observed",
        "observed-coordinate-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[5].observedCallbackOrdinal",
    ),
    (
        "MUT-ANCHOR-DIRFD",
        "fstat-type@linked",
        "callbackArguments.dirfd",
        "raw",
        "callbackArguments",
        "anchor-dirfd",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.dirfd",
    ),
    (
        "MUT-ANCHOR-FLAGS",
        "fstat-type@linked",
        "callbackArguments.rootAnchor",
        "raw",
        "callbackArguments",
        "anchor-flags",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.rootAnchor",
    ),
    (
        "MUT-ANCHOR-RESULT",
        "fstat-type@linked",
        "callbackArguments.rootAnchor",
        "raw",
        "callbackArguments",
        "anchor-result",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.rootAnchor",
    ),
    (
        "MUT-ANCHOR-FINAL-CLOSE",
        "fstat-type@linked",
        "closeEffects",
        "raw",
        "callbackArguments+callbackEvents+metadataEvents+closeEffects",
        "anchor-final-close-omit",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].closeEffects",
    ),
    (
        "MUT-NONINTER-LATER-ROLE",
        "fstat-type@linked",
        "metadataEvents.failFast",
        "raw",
        "callbackArguments+callbackEvents+roleEvents+metadataEvents+statEvents+closeEffects",
        "later-role-after-terminal",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].metadataEvents.failFast",
    ),
    (
        "MUT-DESCRIPTOR-UNKNOWN",
        "fstat-type@linked",
        "callbackArguments.descriptor",
        "raw",
        "callbackArguments",
        "descriptor-unknown",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.descriptor",
    ),
    (
        "MUT-DESCRIPTOR-REUSE",
        "fstat-type@linked",
        "callbackArguments.openOrdinal",
        "raw",
        "callbackArguments",
        "descriptor-reuse",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callbackArguments.openOrdinal",
    ),
    (
        "MUT-OBSERVED-OBSERVEDTARGETROLE",
        "fstat-type@linked",
        "observedTargetRole",
        "observed",
        "observed",
        "observed-coordinate-0",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].observedTargetRole",
    ),
    (
        "MUT-OBSERVED-OBSERVEDTARGETPATH",
        "fstat-type@linked",
        "observedTargetPath",
        "observed",
        "observed",
        "observed-coordinate-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].observedTargetPath",
    ),
    (
        "MUT-OBSERVED-OBSERVEDROLEORDINAL",
        "fstat-type@linked",
        "observedRoleOrdinal",
        "observed",
        "observed",
        "observed-coordinate-2",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].observedRoleOrdinal",
    ),
    (
        "MUT-OBSERVED-OBSERVEDCALLBACKORDINAL",
        "fstat-type@linked",
        "observedCallbackOrdinal",
        "observed",
        "observed",
        "observed-coordinate-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].observedCallbackOrdinal",
    ),
    (
        "MUT-PROJECTION-CALLBACK",
        "fstat-type@linked",
        "callback",
        "projection",
        "projection",
        "projection-coordinate-0",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callback",
    ),
    (
        "MUT-PROJECTION-TARGET",
        "fstat-type@linked",
        "target",
        "projection",
        "projection",
        "projection-coordinate-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].target",
    ),
    (
        "MUT-PROJECTION-PHASE",
        "fstat-type@linked",
        "phase",
        "projection",
        "projection",
        "projection-coordinate-2",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].phase",
    ),
    (
        "MUT-PROJECTION-EFFECT",
        "fstat-type@linked",
        "effect",
        "projection",
        "projection",
        "projection-coordinate-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].effect",
    ),
    (
        "MUT-DECLARED-CALLBACK",
        "fstat-type@linked",
        "callback",
        "declared",
        "declared",
        "declared-coordinate-0",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].callback",
    ),
    (
        "MUT-DECLARED-TARGET",
        "fstat-type@linked",
        "target",
        "declared",
        "declared",
        "declared-coordinate-1",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].target",
    ),
    (
        "MUT-DECLARED-PHASE",
        "fstat-type@linked",
        "phase",
        "declared",
        "declared",
        "declared-coordinate-2",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].phase",
    ),
    (
        "MUT-DECLARED-EFFECT",
        "fstat-type@linked",
        "effect",
        "declared",
        "declared",
        "declared-coordinate-3",
        "recompute-after-mutation",
        "configuredPlanReceipts[14].effect",
    ),
)
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_COUNT = 104
STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_SHA256 = (
    "7ebcf4b63a1d5bd109aaa3308ede26aa5db3bf0dbe26feea9f306976e1c1e837"
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_FIELDS = (
    "mutantId",
    "targetRoleOrdinal",
    "changedFieldSet",
    "findingLocation",
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS = (
    (
        "MUT-INTER-TARGET-ORDINAL-NEGATIVE",
        -1,
        "interRoleSchedule.targetRoleOrdinal",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
    (
        "MUT-INTER-TARGET-ORDINAL-COUNT",
        4,
        "interRoleSchedule.targetRoleOrdinal",
        "configuredPlanReceipts[5].interRoleEvidence",
    ),
)
STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_COUNT = 2
STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_SHA256 = (
    "b9e02deec92e8005bad764079147f07a5f871b146028356cacd6b1bdd64eefe4"
)
STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_FIELDS = (
    "mutantId",
    "operation",
    "changedFieldSet",
    "expectedCoordinate",
    "findingLocation",
)
STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE = (
    (
        "MUT-COMPOSED-INDEX-RAW",
        "invalid-index+raw-list",
        "index+rawReceipt",
        "receiptIndex",
        "configuredPlanReceipts[0].receiptIndex",
    ),
    (
        "MUT-COMPOSED-RAW-SHA",
        "raw-list+stale-sha",
        "rawReceipt+rawEvidenceIdentity",
        "rawReceipt",
        "configuredPlanReceipts[14].rawReceipt",
    ),
    (
        "MUT-COMPOSED-COUNT-ENCODING",
        "count-over+invalid-encoding",
        "callbackArguments+callbackEvents",
        "callbackArguments.countLimit",
        "configuredPlanReceipts[14].callbackArguments.countLimit",
    ),
    (
        "MUT-COMPOSED-SHA-ROLE",
        "stale-sha+empty-roles",
        "rawEvidenceIdentity+roleEvents",
        "rawEvidenceIdentity",
        "configuredPlanReceipts[14].rawEvidenceIdentity",
    ),
    (
        "MUT-COMPOSED-ARG-EVENT",
        "argument-and-event-gap",
        "callbackArguments+callbackEvents",
        "callbackArguments.eventOrdinal",
        "configuredPlanReceipts[14].callbackArguments.eventOrdinal",
    ),
    (
        "MUT-COMPOSED-METADATA-DERIVED",
        "metadata-and-derived-empty",
        "metadataEvents+statEvents+exceptionEvents+closeEffects",
        "metadataEvents",
        "configuredPlanReceipts[14].metadataEvents",
    ),
    (
        "MUT-COMPOSED-OBSERVATION-PROJECTION-PLAN",
        "observation+projection+plan",
        "observed+projection+declared",
        "observedTargetRole",
        "configuredPlanReceipts[14].observedTargetRole",
    ),
    (
        "MUT-COMPOSED-PROJECTION-PLAN",
        "projection+plan",
        "projection+declared",
        "callback",
        "configuredPlanReceipts[14].callback",
    ),
)
STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_COUNT = 8
STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_SHA256 = (
    "bd5d97eeb27e0f55867812f4dff7c412ee494010f97ff05181224e6589566d75"
)
STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANT_FIELDS = (
    "mutantId",
    "operation",
    "expectedCode",
    "expectedLocation",
    "filesystemBoundary",
)
STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANTS = (
    (
        "MUT-HANDOFF-MISSING-PARENT",
        "remove-parent-record",
        "ACP.GIT_METADATA.CONTAINMENT",
        "root",
        "zero-reader-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-ROLE",
        "replace-discovery-role",
        "ACP.GIT_METADATA.CONTAINMENT",
        "root",
        "zero-reader-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-PATH",
        "replace-root-path",
        "ACP.GIT_METADATA.CONTAINMENT",
        "root",
        "zero-reader-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-PATH-AND-TYPE",
        "replace-root-path-and-type",
        "ACP.GIT_METADATA.CONTAINMENT",
        "root",
        "zero-reader-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-TYPE",
        "replace-root-type",
        "ACP.GIT_METADATA.WRONG_TYPE",
        "root",
        "zero-reader-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-TYPE-AND-DEVICE",
        "replace-root-type-and-device",
        "ACP.GIT_METADATA.WRONG_TYPE",
        "root",
        "zero-reader-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-DEVICE",
        "replace-root-device",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "root",
        "zero-dot-git-component-callbacks",
    ),
    (
        "MUT-HANDOFF-WRONG-INODE",
        "replace-root-inode",
        "ACP.GIT_METADATA.IDENTITY_CHANGED",
        "root",
        "zero-dot-git-component-callbacks",
    ),
    (
        "MUT-HANDOFF-COPIED-RECORD",
        "copy-discovery-record-at-call-site",
        "ACP.GIT_METADATA.CONTAINMENT",
        "root",
        "zero-dot-git-reader-calls",
    ),
)
STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANT_COUNT = 9
STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANT_SHA256 = (
    "f8a2204b6cddcf2f324124945bba87629d862c76377bcfbc2cf4d6c01bbaa7c0"
)
STATIC_GIT_METADATA_PORTABLE_ROOT_PLAN_FIELDS = (
    "label",
    "owner_path",
    "owner_mode",
    "owner_device",
    "owner_inode",
    "candidate_components",
    "candidate_component_bytes",
    "candidate_bytes",
    "candidate_depth",
    "filler_components",
    "final_components",
    "governed_path",
    "governed_bytes",
    "governed_depth",
)
STATIC_GIT_METADATA_PORTABLE_ROOT_PLAN_FIELD_COUNT = 14
STATIC_GIT_METADATA_PORTABLE_ROOT_PLAN_FIELD_SHA256 = (
    "7d979d7ec622de838582a8fa021d0adf1b95e13f2fcab32de23960f92fc76d7c"
)
STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANT_FIELDS = (
    "mutantId",
    "operation",
    "expectedLocation",
    "expectedSeamCalls",
)
STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANTS = (
    ("MUT-CONSTRUCT-COMPONENT-7", "component-7", "componentBytes", 0),
    ("MUT-CONSTRUCT-COMPONENT-8", "component-8", "valid", 0),
    ("MUT-CONSTRUCT-COMPONENT-255", "component-255", "valid", 0),
    ("MUT-CONSTRUCT-COMPONENT-256", "component-256", "componentBytes", 0),
    ("MUT-CONSTRUCT-INFEASIBLE", "infeasible", "componentBytes", 0),
    ("MUT-CONSTRUCT-EARLY-A", "early-a", "seam.A[0].mkdir", 1),
    ("MUT-CONSTRUCT-EARLY-B", "early-b", "seam.B[0].mkdir", "first-plan-descendants+1"),
    ("MUT-CONSTRUCT-ROOTS-ZERO", "plans-zero", "plans", 0),
    ("MUT-CONSTRUCT-ROOTS-ONE", "plans-one", "plans", 0),
    ("MUT-CONSTRUCT-ROOTS-THREE", "plans-three", "plans", 0),
    ("MUT-CONSTRUCT-WRONG-DELTA", "delta", "plans[1].candidate_bytes", 0),
    (
        "MUT-CONSTRUCT-DUPLICATE",
        "receipt-duplicate",
        "filesystemReceipts[1].ordinal",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-MISSING",
        "receipt-missing",
        "filesystemReceipts[0].ordinal",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-REORDERED",
        "receipt-reordered",
        "filesystemReceipts[0].ordinal",
        "all-planned-descendants",
    ),
    ("MUT-CONSTRUCT-NOOP", "seam-noop", "seam.A[0].mkdir", 1),
    ("MUT-CONSTRUCT-WRONG-PATH", "seam-wrong-path", "seam.A[0].mkdir", 1),
    ("MUT-CONSTRUCT-SEAM-ERROR", "seam-error", "seam.A[1].mkdir", 2),
    ("MUT-CONSTRUCT-TRANSCRIPT", "transcript", "planningTranscript", "all-planned-descendants"),
    ("MUT-CONSTRUCT-ENVELOPE", "envelope", "governedRoots", "all-planned-descendants"),
    ("MUT-CONSTRUCT-OWNER-ALIAS", "owner-alias", "owner.identity", 0),
    ("MUT-CONSTRUCT-OWNER-SYMLINK", "owner-symlink", "owner.identity", 0),
    ("MUT-CONSTRUCT-OWNER-INODE", "owner-inode", "plans[0].owner_inode", 0),
    (
        "MUT-CONSTRUCT-RECEIPT-ORDINAL",
        "receipt-ordinal",
        "filesystemReceipts[0].ordinal",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-RECEIPT-PATH",
        "receipt-path",
        "filesystemReceipts[0].relativePath",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-RECEIPT-PARENT",
        "receipt-parent",
        "filesystemReceipts[0].parentRelativePath",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-RECEIPT-BYTES",
        "receipt-bytes",
        "filesystemReceipts[0].componentBytes",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-RECEIPT-TYPE",
        "receipt-type",
        "filesystemReceipts[0].observedMode",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-RECEIPT-DEVICE",
        "receipt-device",
        "filesystemReceipts[0].device",
        "all-planned-descendants",
    ),
    (
        "MUT-CONSTRUCT-RECEIPT-INODE",
        "receipt-inode",
        "filesystemReceipts[0].inode",
        "all-planned-descendants",
    ),
)
STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANT_COUNT = 29
STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANT_SHA256 = (
    "18f988577e4eb104238c25489f8f29e56a88161f25bf212ba3eba9590f347361"
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
        39,
        "56be674446a5f3e666c502bb1bc223d9b3070a5b69822b7eb6b23723896d3b6b",
    ),
    (
        "head",
        "valid_token",
        "named-dynamic-oid-token",
        (("C3_HEAD_OID",), ()),
        14,
        "3c84561a66be097818466a1745b2d0c9ab2e1b8830e21f87aada75d6f51fa84d",
        29,
        "52178e3a08325482127aad6b4347767bd08f83adc21d5c734bf39943469abf20",
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
        54,
        "461d6a211f2b7bb4a2c72f1c771878119f90c7d77ce397323bd44f3c0241d6db",
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
        110,
        "26257b226bbf240aa4b163fcc4114b410bf3d5043654f845ab366a6886b4ae25",
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
    "29938b5b3c6533e7e97c852f7dfb95b606763bdbe18e81d1a14e02535483e492"
)
STATIC_GIT_POSITION_BOUND_CASE_FIELDS = (
    "caseId",
    "role",
    "mutation",
    "stage",
    "code",
    "location",
    "exactStoppedRolePrefix",
)
_STATIC_GIT_POSITION_PREFIX_HEAD = ("object_format", "object_integrity", "head")
_STATIC_GIT_POSITION_PREFIX_ANCESTRY = (
    *_STATIC_GIT_POSITION_PREFIX_HEAD,
    "red_type",
    "red_size",
    "red_ancestor",
    "merge_scan",
    "ancestry_chain",
)
_STATIC_GIT_POSITION_PREFIX_RED_OBJECTS = (
    *_STATIC_GIT_POSITION_PREFIX_ANCESTRY,
    "c3_other_scope",
    "c3_freeze_change",
    "red_objects",
)
STATIC_GIT_POSITION_BOUND_CASES = (
    (
        "ancestry-reversed",
        "ancestry_chain",
        "reverse-two-required-oids",
        "freeze",
        "ACP.FREEZE.HISTORY_CHAIN",
        "redHead..HEAD",
        _STATIC_GIT_POSITION_PREFIX_ANCESTRY,
    ),
    (
        "ancestry-missing-token",
        "ancestry_chain",
        "remove-red-head-token",
        "git",
        "ACP.GIT.OUTPUT_TOKEN",
        "ancestry_chain",
        _STATIC_GIT_POSITION_PREFIX_ANCESTRY,
    ),
    (
        "ancestry-duplicate-token",
        "ancestry_chain",
        "duplicate-red-head-token",
        "git",
        "ACP.GIT.OUTPUT_TOKEN",
        "ancestry_chain",
        _STATIC_GIT_POSITION_PREFIX_ANCESTRY,
    ),
    (
        "ancestry-known-oid-wrong-column",
        "ancestry_chain",
        "append-c3-head-at-column-two",
        "git",
        "ACP.GIT.OUTPUT_TOKEN",
        "ancestry_chain",
        _STATIC_GIT_POSITION_PREFIX_ANCESTRY,
    ),
    (
        "red-objects-missing-row",
        "red_objects",
        "remove-repository-oracle-row",
        "git",
        "ACP.GIT.OUTPUT_LINES",
        "red_objects",
        _STATIC_GIT_POSITION_PREFIX_RED_OBJECTS,
    ),
    (
        "red-objects-swapped-rows",
        "red_objects",
        "swap-red-tree-and-matrix-blob-rows",
        "freeze",
        "ACP.FREEZE.RED_TREE_MISMATCH",
        "redTree",
        _STATIC_GIT_POSITION_PREFIX_RED_OBJECTS,
    ),
    (
        "head-corrupt-uppercase",
        "head",
        "uppercase-first-hex-character",
        "git",
        "ACP.GIT.OUTPUT_TOKEN",
        "head",
        _STATIC_GIT_POSITION_PREFIX_HEAD,
    ),
    (
        "head-valid-but-wrong",
        "head",
        "replace-c3-head-with-red-head",
        "freeze",
        "ACP.FREEZE.C3_MISSING",
        "redHead",
        _STATIC_GIT_POSITION_PREFIX_ANCESTRY,
    ),
)
STATIC_GIT_POSITION_BOUND_CASE_COUNT = 8
STATIC_GIT_POSITION_BOUND_CASE_SHA256 = (
    "4604114cb67d2eeacc65351c14bd65040526c8f14e54dcbcf016d5810c723f20"
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
                ("CORRUPT_UPPERCASE_PREFIX:C3_HEAD_OID", "MISSING:C3_HEAD_OID@0:0"),
                (),
                "56be674446a5f3e666c502bb1bc223d9b3070a5b69822b7eb6b23723896d3b6b",
            ),
            (
                "head",
                "valid_token",
                ("MISPLACED:RED_HEAD_OID@0:0", "MISSING:C3_HEAD_OID@0:0"),
                (),
                "52178e3a08325482127aad6b4347767bd08f83adc21d5c734bf39943469abf20",
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
                ("CORRUPT_UPPERCASE_PREFIX:C3_HEAD_OID", "MISSING:C3_HEAD_OID@0:0"),
                ("RED_HEAD_OID",),
                "461d6a211f2b7bb4a2c72f1c771878119f90c7d77ce397323bd44f3c0241d6db",
            ),
            (
                "ancestry_chain",
                "valid_token",
                ("f" * 40, "MISSING:C3_HEAD_OID@0:0"),
                ("RED_HEAD_OID",),
                "5871e0cebd48e4f83aeeeb25ed5d0b3a68b1b1b09fc0e7943335c70b29db5fa4",
            ),
            (
                "red_objects",
                "corrupt_token",
                ("CORRUPT_UPPERCASE_PREFIX:RED_TREE_OID", "MISSING:RED_TREE_OID@0:0"),
                (
                    "MATRIX_BLOB_OID",
                    "CORE_ORACLE_BLOB_OID",
                    "REPOSITORY_ORACLE_BLOB_OID",
                ),
                "26257b226bbf240aa4b163fcc4114b410bf3d5043654f845ab366a6886b4ae25",
            ),
            (
                "red_objects",
                "valid_token",
                ("f" * 40, "MISSING:RED_TREE_OID@0:0"),
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
        "0997c929375f6e5216ed9d0d8ace2ccb366a5bf1e2f43632abc6e330efffbbca",
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
STATIC_RESET47_RED_SNAPSHOT_SCHEMA_VERSION = "C2R50_RED_SNAPSHOT_ONLY_V1"
STATIC_RESET47_RED_SNAPSHOT_FIXED_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
STATIC_RESET47_RED_SNAPSHOT_C1_HEAD = "142dc1502ebec9483c58770f1c03dca9862e9bc8"
STATIC_RESET47_RED_SNAPSHOT_FIELDS = (
    "scope",
    "name",
    "source",
    "use",
    "limit",
    "percent",
    "disposition",
)
STATIC_RESET47_RED_SNAPSHOT_ROWS: tuple[tuple[object, ...], ...] = (
    (
        "path",
        "matrix",
        "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
        4510,
        5500,
        "82.00",
        "normal",
    ),
    (
        "path",
        "protocol",
        "scripts/quality/issue435_adversarial_convergence.py",
        5525,
        12000,
        "46.04",
        "normal",
    ),
    (
        "path",
        "coreOracle",
        "tests/unit/test_issue435_adversarial_convergence.py",
        4496,
        5000,
        "89.92",
        "readability-convergence-pass",
    ),
    (
        "path",
        "repositoryOracle",
        "tests/unit/test_issue435_adversarial_convergence_repository.py",
        15791,
        19000,
        "83.11",
        "normal",
    ),
    (
        "path",
        "template",
        "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
        408,
        600,
        "68.00",
        "normal",
    ),
    (
        "path",
        "adr0064",
        "docs/ADR/0064-adversarial-convergence-protocol.md",
        417,
        550,
        "75.82",
        "normal",
    ),
    (
        "path",
        "playbook",
        "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
        584,
        None,
        "N/A",
        "uncapped-contributor",
    ),
    ("partition", "route", "matrix", 4510, 5800, "77.76", "normal"),
    (
        "partition",
        "architectureSecurity",
        "template+adr0064+playbook",
        1409,
        2200,
        "64.05",
        "normal",
    ),
    (
        "partition",
        "validator",
        "protocol+coreOracle+repositoryOracle",
        25812,
        40000,
        "64.53",
        "normal",
    ),
    (
        "aggregate",
        "sevenSemanticPaths",
        "matrix+protocol+coreOracle+repositoryOracle+template+adr0064+playbook",
        31731,
        45000,
        "70.51",
        "normal",
    ),
    (
        "binary",
        "binary",
        "matrix+protocol+coreOracle+repositoryOracle+template+adr0064+playbook",
        0,
        0,
        "0.00",
        "binary-zero",
    ),
)
STATIC_RESET47_RED_SNAPSHOT_COUNT = 12
STATIC_RESET47_RED_SNAPSHOT_SHA256 = (
    "32b47bf3eebdb87e512fb8e3e4c99c4d168a20f24811b041061fead2f2997a10"
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_SCHEMA_VERSION = "RESET50_DYNAMIC_CURRENT_HEAD_BUDGET_V1"
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_FIXED_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_PREFIX = (
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
    "core.fsmonitor=false",
    "-c",
    "log.showSignature=false",
    "-c",
    "fsck.skipList=/dev/null",
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_DIFF_ARGUMENTS = (
    "diff",
    "--no-renames",
    "--ignore-submodules=none",
    "--no-ext-diff",
    "--no-textconv",
    "--diff-filter=A",
    "--numstat",
    "a6284f7d8f1a14ef4c9a99493d6b06046505f20c",
    "HEAD",
    "--",
    "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
    "scripts/quality/issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
    "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
    "docs/ADR/0064-adversarial-convergence-protocol.md",
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ENVIRONMENT = (
    ("LC_ALL", "C"),
    ("GIT_CONFIG_NOSYSTEM", "1"),
    ("GIT_CONFIG_GLOBAL", "/dev/null"),
    ("GIT_NO_LAZY_FETCH", "1"),
    ("GIT_NO_REPLACE_OBJECTS", "1"),
    ("GIT_OPTIONAL_LOCKS", "0"),
    ("GIT_TERMINAL_PROMPT", "0"),
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_CHECKOUT_PATHS = (
    "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
    "scripts/quality/issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
    "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
    "docs/ADR/0064-adversarial-convergence-protocol.md",
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_OUTPUT_PATHS = (
    "docs/ADR/0064-adversarial-convergence-protocol.md",
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
    "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
    "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
    "scripts/quality/issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_ITEM_BYTE_LIMIT = 4194304
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_TOTAL_BYTE_LIMIT = 16777216
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_MEASUREMENT_CONTRACT = (
    "tree-to-tree-fixed-base-head",
    "fixed-base-paths-absent",
    "git-deletions-zero",
    "raw-checkout-exact-allowlist-contained",
    "raw-checkout-ancestors-and-leaf-no-symlink",
    "raw-checkout-regular-fstat-bounded-descriptor-read",
    "raw-checkout-utf8-lf-no-cr-no-nul",
    "git-and-raw-derived-independently",
    "pre-commit-both-below-stop",
    "clean-immutable-head-git-equals-raw",
    "risk-set-derived-for-each-measurement",
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RISK_THRESHOLD_PERCENT = 85
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_STOP_THRESHOLD_PERCENT = 90
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_FIELDS = ("scope", "name", "source", "limit")
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ROWS: tuple[tuple[object, ...], ...] = (
    ("path", "matrix", "docs/governance/adversarial-convergence-invariant-matrix-v1.json", 5500),
    ("path", "protocol", "scripts/quality/issue435_adversarial_convergence.py", 12000),
    ("path", "coreOracle", "tests/unit/test_issue435_adversarial_convergence.py", 5000),
    (
        "path",
        "repositoryOracle",
        "tests/unit/test_issue435_adversarial_convergence_repository.py",
        19000,
    ),
    ("path", "template", "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md", 600),
    ("path", "adr0064", "docs/ADR/0064-adversarial-convergence-protocol.md", 550),
    ("path", "playbook", "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md", None),
    ("partition", "route", "matrix", 5800),
    ("partition", "architectureSecurity", "template+adr0064+playbook", 2200),
    ("partition", "validator", "protocol+coreOracle+repositoryOracle", 40000),
    (
        "aggregate",
        "sevenSemanticPaths",
        "matrix+protocol+coreOracle+repositoryOracle+template+adr0064+playbook",
        45000,
    ),
    (
        "binary",
        "binary",
        "matrix+protocol+coreOracle+repositoryOracle+template+adr0064+playbook",
        0,
    ),
)
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_COUNT = 12
STATIC_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_SHA256 = (
    "8639b677175273825f7249834cc69f94bee1201bfdf0465d273b44157103d5ce"
)
STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS = (
    "path",
    "marker",
    "repositoryUse",
    "validatorUse",
    "aggregateUse",
    "repositoryPercent",
    "validatorPercent",
    "aggregatePercent",
)
STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS: tuple[tuple[object, ...], ...] = (
    (
        "docs/ADR/0064-adversarial-convergence-protocol.md",
        "<!-- issue-435-reset47-red-snapshot:sha256=8e97148cbd13a76c5b091c8d3abfb6550b86fbaa13528af5e151315fdede83c4 -->",
        15791,
        25812,
        31731,
        "83.11",
        "64.53",
        "70.51",
    ),
    (
        "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
        "<!-- issue-435-reset47-red-snapshot:sha256=f3519f11231079688a811e0adab52a968aa2893ccf11d42dcf4d57118eee2270 -->",
        15791,
        25812,
        31731,
        "83.11",
        "64.53",
        "70.51",
    ),
    (
        "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
        "<!-- issue-435-reset47-red-snapshot:sha256=55aa43ac306e78ad73137963ef9437f114868c53753a0781f5988736242d1519 -->",
        15791,
        25812,
        31731,
        "83.11",
        "64.53",
        "70.51",
    ),
)
STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT = 3
STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256 = (
    "84b9ed78f4bd7eb548e9b8ebdee3616f38426dbcf4433a39a5639fec31f468aa"
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
