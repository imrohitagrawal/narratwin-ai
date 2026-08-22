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
                "0ee62de4bb552ec6445a5b5849882d4e430064036cdeb9a1e05be686b6d6ca46",
            ),
            (
                "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
                "ae61f545f27e67f250165a3b0b6a3bb97d21475714773b8685a93d44b03ed10e",
            ),
            (
                "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
                "14503534278577e7e29cd745f8a356d6e0e8b427cbd3e01291cf874e5c2684cd",
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
    ("variantAxes", ("case", "whitespace", "hyphen", "markdown", "bounded-synonym")),
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
    ("variantCount", 20),
    ("variantSha256", "a4666fdafd5443efaf7b5ea46073718d02d841f6dc4e088b4c7513620c14491b"),
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
    "normalizedIoCleanupIdentity",
    "rolePrefix",
    "normalizedIoCleanupPrefix",
)
STATIC_GIT_METADATA_TRIGGER_RECEIPT_FIELDS = (
    "role",
    "callbackVector",
    "lstatVector",
    "openVector",
    "fstatVector",
    "readRequestVector",
    "readChunkLengthVector",
    "readTypeVector",
    "postLstatVector",
    "closeAttemptOrderVector",
    "closeResultVector",
)
STATIC_GIT_METADATA_TRIGGER_RECEIPT_COUNT = 129
STATIC_GIT_METADATA_TRIGGER_RECEIPT_SHA256 = (
    "b7859e833216ef647dffbf6f246c69747895943a308f5f24cb327c1b3933c1f6"
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
    ("configured-removed-linked-pre-root-fstat", ("pre-root-symlink@linked", "fstat-type@linked")),
    ("configured-removed-linked-pre-root-open", ("pre-root-symlink@linked", "open-error@linked")),
    (
        "configured-removed-conventional-ancestor",
        ("root-replacement@conventional", "ancestor-replacement@conventional"),
    ),
    (
        "configured-removed-conventional-between",
        ("root-replacement@conventional", "between-read-conventional-dot-git@conventional"),
    ),
    (
        "configured-removed-conventional-final",
        ("root-replacement@conventional", "final-binding-revalidation@conventional"),
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
    ("configured-removed-linked-root-leaf", ("root-replacement@linked", "leaf-replacement@linked")),
    (
        "configured-removed-linked-root-postread",
        ("root-replacement@linked", "post-read-device@linked"),
    ),
    (
        "configured-removed-linked-between-read",
        ("between-read-linked-directory@linked", "between-read-common-directory@linked"),
    ),
    ("configured-removed-linked-fstat-lstat", ("fstat-inode@linked", "lstat-error@linked")),
    ("configured-removed-linked-fstat-close", ("fstat-inode@linked", "close-error@linked")),
)
STATIC_GIT_METADATA_FORMER_COLLISION_GROUP_COUNT = 31
STATIC_GIT_METADATA_FORMER_COLLISION_GROUP_SHA256 = (
    "977619f813077f29dd87070f760e2fffc2eee6281cdfc168cb7942f5cd45fc0b"
)
STATIC_GIT_METADATA_CONFIGURED_REMOVED_COLLISION_COUNT = 17
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
    "d57645ae195a559e1d88f3053385a900e723c9eb638f69cec66056765b24cdc0"
)
STATIC_GIT_METADATA_STIMULUS_COUNT = 129
STATIC_GIT_METADATA_STIMULUS_SHA256 = (
    "ebaffa1950528196ef5f408707f945ec71a5fbb7c8f6643bcef5b1b0cb21fbb9"
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
