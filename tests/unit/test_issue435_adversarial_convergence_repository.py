"""Repository/Git/nonactivation RED oracle for Issue #435."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import subprocess
import sys
import zlib
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, cast

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
REAL_SUBPROCESS_RUN = subprocess.run
PROTOCOL_SUBPROCESS: Any = getattr(protocol, "subprocess")
PROTOCOL_METADATA_READER: Any = getattr(protocol, "_read_git_metadata_nofollow")
GIT_PREFIX = (
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
GIT_ENV_FIXED = (
    ("LC_ALL", "C"),
    ("GIT_CONFIG_NOSYSTEM", "1"),
    ("GIT_CONFIG_GLOBAL", "/dev/null"),
    ("GIT_NO_LAZY_FETCH", "1"),
    ("GIT_NO_REPLACE_OBJECTS", "1"),
    ("GIT_OPTIONAL_LOCKS", "0"),
    ("GIT_TERMINAL_PROMPT", "0"),
)
MetadataCaseRow = tuple[str, str, str, str, str, str | None, str]
NormalizedMetadataIo = tuple[str, ...]
MetadataRoleTrace = tuple[str, NormalizedMetadataIo]
MetadataExecution = tuple[
    MetadataCaseRow,
    str,
    str,
    tuple[str, ...],
    tuple[MetadataRoleTrace, ...],
]
TextualTransformation = tuple[str, str, bool, str | None, str | None, str | None]
EXPECTED_METADATA_CASES: tuple[MetadataCaseRow, ...] = (
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
    (
        "root-dot",
        "public",
        "root",
        "dot_git",
        "root-dot",
        "ACP.GIT_METADATA.NONABSOLUTE",
        "root",
    ),
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
EXPECTED_METADATA_CASE_IDS = tuple(item[0] for item in EXPECTED_METADATA_CASES)
EXPECTED_METADATA_CASE_COUNT = 94
EXPECTED_METADATA_CASE_SHA256 = "9da07ee4ae676313a8b267ae7374bad049781025d969e99201aba9e45a4ca3e9"
EXPECTED_METADATA_PAYLOAD_SHA256 = {
    "dot-git-cap-n-malformed": "f7ddf5d443f1f023fd6b183e650633c70985d98fdf61db0a3652b3d807b0b6bb",
    "dot-git-cap-n-plus-one": "3e97197f4b8d46a893067c94ab15e195e3d97fb5f24eede5ef047b571240d92b",
    "dot-git-invalid-utf8": "43c795ec75535d6881bc0de5d3d0ef4f7f8a944b830a1b9cf7f3f2a2f42f2886",
    "dot-git-missing-lf": "4723510a592850f30781a95f63d6269212620e3ad2243f36a1a4a25ed8c8c37c",
    "dot-git-crlf": "28434deabacf60e689459de7c7e452c69b38939e297315859365cb03d8c6b524",
    "dot-git-extra-lf": "06b499b952fee1e58c423086bdf9ef74a7404bb732775d599e227394bc61e732",
    "dot-git-extra-record": "2d2c2176e0bb947f18b391d1daf34f64f2695aad078d09c2d71fd53996dc3a69",
    "dot-git-relative": "76c03fce0148428f30f51ab2b3bd75162d3f14c5911d49dfb93e5b7ce33f264a",
    "dot-git-dot-component": "a6d3695ce08b4dc1818bd8ad18a760c731e78a0a08fe2951a7195ec4ae2e8459",
    "dot-git-dotdot-component": "cd229178b0c982c91b80cb1e03d7bcc46bd3db838eb71df19bec1f0e2fe95838",
    "dot-git-empty-component": "f11efa1983e578fe1609b58b7ebcc9f5ffbeb7325ef0f429bdac82ccdda2e068",
    "dot-git-nul": "067333a9152cd303b9cfa259c9672180a84e6b1de7630d6dc1025f105e013238",
    "dot-git-degenerate-common-root": "a7235dcd14921ed62b5ce7d9106746cae4d5396146c1ac9ad11e99aec2b4927e",
    "backlink-cap-n-malformed": "f7ddf5d443f1f023fd6b183e650633c70985d98fdf61db0a3652b3d807b0b6bb",
    "backlink-cap-n-plus-one": "3e97197f4b8d46a893067c94ab15e195e3d97fb5f24eede5ef047b571240d92b",
    "backlink-invalid-utf8": "e4688624e5f1ad0629505e6768e3bb36244f2f3e33e751215afa820334a76ed3",
    "backlink-missing-lf": "8810ad581e59f2bc3928b261707a71308f7e139eb04820366dc4d5c18d980225",
    "backlink-extra-lf": "de2c14c6b1e0c1c94ee4ac3d92ffb5df2333f9db06d341c363e5fc51a6d0273f",
    "backlink-mismatch": "971e9e926b7d7f02e26d96e874453956a113c1b2493c0bef87cf99b6a010fb72",
    "commondir-cap-n-malformed": "f7ddf5d443f1f023fd6b183e650633c70985d98fdf61db0a3652b3d807b0b6bb",
    "commondir-cap-n-plus-one": "3e97197f4b8d46a893067c94ab15e195e3d97fb5f24eede5ef047b571240d92b",
    "commondir-invalid-utf8": "e4688624e5f1ad0629505e6768e3bb36244f2f3e33e751215afa820334a76ed3",
    "commondir-missing-lf": "8810ad581e59f2bc3928b261707a71308f7e139eb04820366dc4d5c18d980225",
    "commondir-extra-lf": "de2c14c6b1e0c1c94ee4ac3d92ffb5df2333f9db06d341c363e5fc51a6d0273f",
    "commondir-mismatch": "55680f2e2c0396a16cb23d09962dd10ac92835d80183cadeab928d13b0d3b472",
}
EXPECTED_METADATA_PAYLOAD_FINGERPRINT_COUNT = 25
EXPECTED_METADATA_PAYLOAD_FINGERPRINT_SHA256 = (
    "77fa92e04dc499feca8c37b78fb9d119858d7f0ac8df7c148019c89bf49b77d4"
)
EXPECTED_METADATA_EXECUTION_CONTRACT_FIELDS = (
    "caseRow",
    "operationalMode",
    "observedStimulusIdentity",
    "rolePrefix",
    "normalizedIoCleanupPrefix",
)
EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES = (
    (
        "metadata-target-symlink-plus-matrix-schema",
        "validate_repository_freeze",
        "dot-git-target-symlink",
        "matrix-schema-version-wrong",
        "git-metadata",
        "CURRENT",
        "ACP.GIT_METADATA.TARGET_SYMLINK",
        ".git",
        "identity",
        0,
        0,
    ),
)
EXPECTED_METADATA_GOVERNED_PRECEDENCE_SHA256 = (
    "881ebe4a28d10cfe7c8ccfd9a1f2bd4677ff6f2f1bcc642514031b282042f971"
)
EXPECTED_GIT_FILESYSTEM_THREAT_MODEL = {
    "scope": "stable_local_filesystem_metadata_and_object_snapshot_for_full_validator_invocation",
    "proofs": [
        "fail_closed_parsing",
        "descriptor_relative_no_follow_traversal",
        "reader_local_inode_continuity",
        "prohibited_metadata_absence_at_validated_read_points",
        "exact_path_based_git_object_evidence_under_snapshot_assumption",
    ],
    "defenseInDepth": [
        "reader_local_lstat_open_fstat_postread_replacement_detection",
        "final_dot_git_linked_git_dir_common_dir_revalidation",
    ],
    "gitProcessBinding": "path_based_absolute_git_with_explicit_git_dir_common_dir_work_tree",
    "excludedThreat": (
        "concurrent_out_of_process_mutation_after_validated_descriptor_close_before_or_during_"
        "path_based_git_reopen"
    ),
    "claimsNotMade": [
        "race_free_validation",
        "atomic_check_to_use",
        "descriptor_bound_git_subprocess",
        "detection_or_prevention_of_concurrent_repository_mutation",
    ],
    "strongerClaimDisposition": "EVIDENCE_BLOCKER",
}
EXPECTED_METADATA_EXECUTION_IDS = (
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
# fmt: off
EXPECTED_METADATA_EXECUTIONS: tuple[MetadataExecution, ...] = (
    (('conventional-positive', 'public', 'conventional', 'dot_git', 'directory', None, '.git'), 'conventional', 'dd62899343434f8f57712ad0fcbde3f0c1d3b872106da51585d273dbba7133ab', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates', 'dot_git', 'common_dir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('linked-positive', 'public', 'linked', 'linked_git_dir', 'registered', None, '.git.gitdir'), 'linked', '7607b433d729228571437910c6a464299db36b3fc56d054cb28f71d6d0e206e3', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates', 'dot_git', 'linked_git_dir', 'common_dir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('linked-layout-outside', 'public', 'linked', 'dot_git', 'outside-worktrees', 'ACP.GIT_METADATA.LAYOUT', '.git.gitdir'), 'linked', '35fbce1c0092aca820d29705ece0f5bc287b6d184c8ebed65037845eae44cafb', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-nonabsolute', 'public', 'root', 'dot_git', 'relative-root', 'ACP.GIT_METADATA.NONABSOLUTE', 'root'), 'root', 'fc5da2ee5e732ec124a622d0b52b76235899a2b0af3dd3c162f1f7f712674413', ('dot_git',), (('dot_git', ('reader-call', 'root:relative', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.NONABSOLUTE:root', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-dotdot', 'public', 'root', 'dot_git', 'root-dotdot', 'ACP.GIT_METADATA.NONABSOLUTE', 'root'), 'root', 'c80ebdfe066dfa3caf8a6ea1e3dd509f1929c2e3d2fc1bdaf87a53820156241e', ('dot_git',), (('dot_git', ('reader-call', 'root:dotdot-component', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.NONABSOLUTE:root', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-dot', 'public', 'root', 'dot_git', 'root-dot', 'ACP.GIT_METADATA.NONABSOLUTE', 'root'), 'root', '8e2b51e090446bb5882a57b74081d7a103b66f21b1c4791a502e4f2e1ef708f3', ('dot_git',), (('dot_git', ('reader-call', 'root:dot-component', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.NONABSOLUTE:root', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-repeated-separator', 'public', 'root', 'dot_git', 'root-repeated-separator', 'ACP.GIT_METADATA.NONABSOLUTE', 'root'), 'root', '0babb11673578bf7ac01dcd2ed0d68aba450af41b9604031417c9c64fd3688f8', ('dot_git',), (('dot_git', ('reader-call', 'root:repeated-separator', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.NONABSOLUTE:root', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-trailing-separator', 'public', 'root', 'dot_git', 'root-trailing-separator', 'ACP.GIT_METADATA.NONABSOLUTE', 'root'), 'root', '4bb0aa2066c5810c124ca6445d19fe6113229a9fecc633f2afe32fa261f4907f', ('dot_git',), (('dot_git', ('reader-call', 'root:trailing-separator', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.NONABSOLUTE:root', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-symlink', 'public', 'both', 'dot_git', 'root-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'root'), 'conventional', 'b1ddfc26dc18296a0acc7bd804089592b09555350c891a75e4c1aea7478bdf69', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-symlink', 'public', 'both', 'dot_git', 'root-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'root'), 'linked', '2c9c459f2ca1755703cf049b44ff37ed1a28b74f3813242983d37545d60b635a', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('pre-root-symlink', 'public', 'both', 'dot_git', 'pre-root-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'root'), 'conventional', 'b1ddfc26dc18296a0acc7bd804089592b09555350c891a75e4c1aea7478bdf69', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('pre-root-symlink', 'public', 'both', 'dot_git', 'pre-root-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'root'), 'linked', '2c9c459f2ca1755703cf049b44ff37ed1a28b74f3813242983d37545d60b635a', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-replacement', 'public', 'both', 'dot_git', 'root-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'root'), 'conventional', '0714f38f86972af267473df790c396de2f7a9478df930aab74ba39c10c1f0889', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('root-replacement', 'public', 'both', 'dot_git', 'root-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'root'), 'linked', 'bc9c42f7bebccfb1c6b91362d87fcf5dda138973c79043067a0ec493d27738ca', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('pre-root-replacement', 'public', 'both', 'dot_git', 'pre-root-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'root'), 'conventional', '0714f38f86972af267473df790c396de2f7a9478df930aab74ba39c10c1f0889', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('pre-root-replacement', 'public', 'both', 'dot_git', 'pre-root-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'root'), 'linked', 'bc9c42f7bebccfb1c6b91362d87fcf5dda138973c79043067a0ec493d27738ca', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:root', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('ancestor-replacement', 'public', 'both', 'prohibited_grafts', 'ancestor-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'info'), 'conventional', '970e91b6b34a299595e8e0cd3097b98edd68dec3617238efd20d0ee4a18be882', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('ancestor-replacement', 'public', 'both', 'prohibited_grafts', 'ancestor-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'info'), 'linked', 'e5ee21cd940d6c009c690317adce20aff60c8a74058c1537df477854b2e3a7ad', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('between-read-conventional-dot-git', 'public', 'conventional', 'common_dir', 'replace-dot-git-before-common-read', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'conventional', '180f3f96557311fd15476bb9b4d7a16b4c6c55cd972ec88d9c2baa13081708f9', ('dot_git', 'common_dir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('between-read-linked-directory', 'public', 'linked', 'backlink', 'replace-linked-dir-before-backlink', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git.gitdir'), 'linked', '36dbaccd5aa9904cd3e6e7b64cce106acbae58c3171cbf6f3cb9e0cfd2c1eb51', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git.gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('between-read-linked-common-directory', 'public', 'linked', 'common_dir', 'replace-common-dir-before-common-read', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'common-dir'), 'linked', '1142ad0bbe7a2526547586e042598a103250e9419ddc1dda301bfe4e4f9a94f9', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:common-dir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('between-read-common-directory', 'public', 'linked', 'prohibited_grafts', 'replace-common-dir-before-prohibited-read', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'common-dir'), 'linked', 'a444142dd35bffd7c420a95e6ca785ae354ebd38b65d005a2c4dc7cf55afad5b', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:common-dir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('final-binding-revalidation', 'public', 'conventional', 'dot_git', 'replace-dot-git-before-final-revalidation', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'conventional', '013b359336d4cbe3282dabb9f89d11c34c11511fb5f766b1a6fe0de868b2bb9c', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates', 'dot_git'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('dot-git-missing', 'public', 'conventional', 'dot_git', 'missing', 'ACP.GIT_METADATA.MISSING', '.git'), 'conventional', '36f65c119524a3621b5a9a5729959d9ad15f500ba2a44e4df82c5073c2799c83', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'finding:ACP.GIT_METADATA.MISSING:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-target-symlink', 'public', 'conventional', 'dot_git', 'symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', '.git'), 'conventional', 'f667f77a7fb424fae65aee3550f2d114d8dacb767fe8638bb138510882f5ddcd', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-fifo', 'public', 'conventional', 'dot_git', 'fifo', 'ACP.GIT_METADATA.WRONG_TYPE', '.git'), 'conventional', '9b7ade5f1795cafa51eb3606ec270af11f8fdb85a73bd7818db97e98e5f10154', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-cap-n-malformed', 'public', 'linked', 'dot_git', '4096-bytes', 'ACP.GIT_METADATA.RECORD_SHAPE', '.git'), 'linked', '34e0741aa1d747a3314578127ddadc538be062cacdbc6833a22167efc7ec4039', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-cap-n-plus-one', 'public', 'linked', 'dot_git', '4097-bytes', 'ACP.GIT_METADATA.BYTE_CAP', '.git'), 'linked', 'd6a66def63b87e235eda59e6f35aa468279aeefd38a2b21c6547222421fea390', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:one', 'read:bytes:nonempty', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.BYTE_CAP:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-invalid-utf8', 'public', 'linked', 'dot_git', 'invalid-utf8', 'ACP.GIT_METADATA.INVALID_UTF8', '.git'), 'linked', 'f7ab454fc587128fa28f2a0f0830d5941615f4c41d2225bf4f24939802cb1e19', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-missing-lf', 'public', 'linked', 'dot_git', 'missing-lf', 'ACP.GIT_METADATA.LINE_COUNT', '.git'), 'linked', 'd1090596d452a9398de40f3b05049e8697377c45c95668b8290b0cfd35569586', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-crlf', 'public', 'linked', 'dot_git', 'crlf', 'ACP.GIT_METADATA.RECORD_SHAPE', '.git'), 'linked', '98315870f732eac9764a50d38bd5e7968a325e1e5869dfc2eb81816a00e14210', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-extra-lf', 'public', 'linked', 'dot_git', 'extra-lf', 'ACP.GIT_METADATA.LINE_COUNT', '.git'), 'linked', 'f46e40917f0ba5f776ca58b8822686b38eaad1e26a9630f70e27193ae0b67b8b', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-extra-record', 'public', 'linked', 'dot_git', 'extra-record', 'ACP.GIT_METADATA.LINE_COUNT', '.git'), 'linked', 'c11c6cd54a83150d52a3b869ce965233c763e08753732f83621225e70a9af145', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-relative', 'public', 'linked', 'dot_git', 'relative-gitdir', 'ACP.GIT_METADATA.NONABSOLUTE', '.git.gitdir'), 'linked', '3419deeeafecc9ffd9870c0bba3ff5c3f2ea8dcc1e8e217a0b02ab98ffd0cdc8', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-dot-component', 'public', 'linked', 'dot_git', 'dot-component', 'ACP.GIT_METADATA.CONTAINMENT', '.git.gitdir'), 'linked', 'f0b1c60d89732b4cd7b7b1023daa2fdfcd8a259100763d24a008bed069ee5991', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-dotdot-component', 'public', 'linked', 'dot_git', 'dotdot-component', 'ACP.GIT_METADATA.CONTAINMENT', '.git.gitdir'), 'linked', '7aba93d23f40b1973ada1745e92518206318e7b1d07127cd01950bcc44d76aa3', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-empty-component', 'public', 'linked', 'dot_git', 'double-slash', 'ACP.GIT_METADATA.CONTAINMENT', '.git.gitdir'), 'linked', '34b0a12e34693d6149ffefe78eb0c190769b07f61a148593233436608a7d2a56', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-nul', 'public', 'linked', 'dot_git', 'nul', 'ACP.GIT_METADATA.CONTAINMENT', '.git.gitdir'), 'linked', 'c2e0d02aa7610cda6a00c881f425b601ab4581425c6578397ad5e1704eaa17c5', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('dot-git-degenerate-common-root', 'public', 'linked', 'dot_git', 'filesystem-root-common-dir', 'ACP.GIT_METADATA.LAYOUT', '.git.gitdir'), 'linked', 'e5105114b9d25ff6f3b55e221c1e72fbee64e7f3deb16e36ad0b0da60c890866', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('leaf-replacement', 'public', 'both', 'dot_git', 'leaf-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'conventional', '6de20376818c6d6d6d5039a5099795e2bf976083e3448ec15b54bbe11f11b97e', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('leaf-replacement', 'public', 'both', 'dot_git', 'leaf-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'linked', 'e1ac3deef3c159087fbd2ed1d3f08a7041c5a332db2401bf88c6a333291eca08', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('fstat-device', 'public', 'both', 'dot_git', 'device-drift', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'conventional', '34ed8b216d1ff46c8e729ce798b377aeee8fab975d9113f41249fc7836cae9e2', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:device-drift:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('fstat-inode', 'public', 'both', 'dot_git', 'inode-drift', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'conventional', '01acd674736e04c8c10f8308e76e06ac94109e89f256692917483de8968b3346', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:inode-drift:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('fstat-type', 'public', 'both', 'dot_git', 'type-drift', 'ACP.GIT_METADATA.WRONG_TYPE', '.git'), 'conventional', 'b972764380da4a78c6787e5434530454e24e65c78ec130452b6b5c3a804e3c0b', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:type-drift:other', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('fstat-device', 'public', 'both', 'dot_git', 'device-drift', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'linked', '06db47f185754ddd92cc3d599ee8163709f24c12b7aeca3f56e25d7e4d22b95b', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:device-drift:regular', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('fstat-inode', 'public', 'both', 'dot_git', 'inode-drift', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'linked', 'ef60a3cb21dff33f1faa76d75234c97befb54a4b810a574fd70877412b10f75d', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:inode-drift:regular', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('fstat-type', 'public', 'both', 'dot_git', 'type-drift', 'ACP.GIT_METADATA.WRONG_TYPE', '.git'), 'linked', '78d7a72732b1bcb9be57f9d87090ed64b4447e835465cc9d00d821d0678e200e', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:type-drift:other', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('post-read-device', 'public', 'linked', 'dot_git', 'post-device-drift', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'linked', 'd28f40d5b68c704afafe332577211d79986801973a038e97252c3eb8e4dfbb06', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:device-drift:regular', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('post-read-inode', 'public', 'linked', 'dot_git', 'post-inode-drift', 'ACP.GIT_METADATA.IDENTITY_CHANGED', '.git'), 'linked', '688694a3202eb25f3d223e22463269ae337ac89cbc5b8e81be8ad01234a0464e', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:inode-drift:regular', 'exception:none', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('post-read-type', 'public', 'linked', 'dot_git', 'post-type-drift', 'ACP.GIT_METADATA.WRONG_TYPE', '.git'), 'linked', 'e22ac1cda9b7a83151313fdb28d41329d5caee4cf967f90cbd5f16fa2ba034ad', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:type-drift:other', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('read-type', 'public', 'linked', 'dot_git', 'non-bytes', 'ACP.GIT_METADATA.READ_TYPE', '.git'), 'linked', '1df90aefe7e5f65cd3bd05e1aa25390f053436a9711ceaf114f52acd7216ef06', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:one', 'read:type:str', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.READ_TYPE:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('read-error', 'public', 'linked', 'dot_git', 'read-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'linked', 'f40dd0b7adc485f9a925d183cd5c9a0347b1817d107f7fa824d0b77c44f3f3a6', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:one', 'read:error:OSError:no-errno', 'post-lstat:none', 'exception:one', 'read:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('lstat-error', 'public', 'both', 'dot_git', 'lstat-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'conventional', '515d6897c09bc9b6ab4cbbeb38cdd7f55be2f9167b8a58a7ccdfd4f6066cd89f', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:OSError:no-errno', 'open:one', 'open:ok:directory:nofollow', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:one', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('lstat-error', 'public', 'both', 'dot_git', 'lstat-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'linked', 'cf1ca87c9861dbe120dcad3ca44cd97d5bea858896c7a7ae5fe5c73aded3ebe4', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:OSError:no-errno', 'open:one', 'open:ok:directory:nofollow', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:one', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('open-error', 'public', 'both', 'dot_git', 'open-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'conventional', '9815fdc1f48f767f6c22a53bba72631918af4975021778b1fd923f2df1cddc84', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('open-error', 'public', 'both', 'dot_git', 'open-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'linked', '2751840e355fab7bafd587922c4322a74759e6092b6c19d52f8df7907c90aaa4', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:none', 'lstat:none', 'open:none', 'fstat:none', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:none', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('close-error', 'public', 'both', 'dot_git', 'close-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'conventional', 'f09c5e39e03710a4a609ad8b54de92dfe6250bf71f00633169661fc6db075e82', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:multiple', 'close:error:OSError:no-errno', 'close:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:multiple', 'close:error:OSError:no-errno', 'close:error:OSError:no-errno', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('close-error', 'public', 'both', 'dot_git', 'close-oserror', 'ACP.GIT_METADATA.IO_ERROR', '.git'), 'linked', '00de52b4c8f3a430abc5bcc8f506fe0e061943660a1d16e7346b16b414485570', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:multiple', 'close:error:OSError:no-errno', 'close:error:OSError:no-errno', 'finding:ACP.GIT_METADATA.IO_ERROR:.git', 'close:multiple', 'close:error:OSError:no-errno', 'close:error:OSError:no-errno', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('backlink-missing', 'public', 'linked', 'backlink', 'missing', 'ACP.GIT_METADATA.MISSING', 'git-dir/gitdir'), 'linked', '11f20310ec56797c2252baae5e213de16382cd960c2f8c9f8bf241194807ef2f', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'finding:ACP.GIT_METADATA.MISSING:git-dir/gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-directory', 'public', 'linked', 'backlink', 'directory', 'ACP.GIT_METADATA.WRONG_TYPE', 'git-dir/gitdir'), 'linked', '10bb03f5788af52f1ccad849bc072601a26d6a58efba2eaf65ae46bd8943c016', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:git-dir/gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-fifo', 'public', 'linked', 'backlink', 'fifo', 'ACP.GIT_METADATA.WRONG_TYPE', 'git-dir/gitdir'), 'linked', '37c28831b55a623bc3f44f6935f820c8158f1e958281f883bb120bd80bcca70e', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:git-dir/gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-symlink', 'public', 'linked', 'backlink', 'symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'git-dir/gitdir'), 'linked', 'd0ff1450994885a7e67030d9cc40f7de9a97855a0e66d81e5d8b68aceae76b51', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:git-dir/gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-cap-n-malformed', 'public', 'linked', 'backlink', '4096-bytes', 'ACP.GIT_METADATA.RECORD_SHAPE', 'git-dir/gitdir'), 'linked', '4ae1a5dfa753f17c54b6e86345870201cd81e88d1ce9b71ebd4f5f975832cc83', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-cap-n-plus-one', 'public', 'linked', 'backlink', '4097-bytes', 'ACP.GIT_METADATA.BYTE_CAP', 'git-dir/gitdir'), 'linked', '03d56a6bc4cd7335939d430596ce412326581515f582c8495db9bf997cbd4038', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:one', 'read:bytes:nonempty', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.BYTE_CAP:git-dir/gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-invalid-utf8', 'public', 'linked', 'backlink', 'invalid-utf8', 'ACP.GIT_METADATA.INVALID_UTF8', 'git-dir/gitdir'), 'linked', 'f8545053f5f3ff7979e5f4c86b77e3113763d9bc4e2e424fc8e5415f16452f44', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-missing-lf', 'public', 'linked', 'backlink', 'missing-lf', 'ACP.GIT_METADATA.LINE_COUNT', 'git-dir/gitdir'), 'linked', 'bb9515e430de410eff4cbda8b8b73056c7d33a486e7042419503643fba14b33d', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-extra-lf', 'public', 'linked', 'backlink', 'extra-lf', 'ACP.GIT_METADATA.LINE_COUNT', 'git-dir/gitdir'), 'linked', '0bf9132e4c1512844e44fc8ef783e557466f32b016b143b3b120ee74a876de90', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('backlink-mismatch', 'public', 'linked', 'backlink', 'wrong-root', 'ACP.GIT_METADATA.BACKLINK_MISMATCH', 'git-dir/gitdir'), 'linked', '1891a7b6301e6ceead03a11361e936113146ce8bfc9823e360c0a03a1ce536dc', ('dot_git', 'linked_git_dir', 'backlink'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-missing', 'public', 'linked', 'commondir', 'missing', 'ACP.GIT_METADATA.MISSING', 'git-dir/commondir'), 'linked', '64eaac5ca5cc93ac2863e428bf36f9bd563740f91725fb325ac196a4124eaa4e', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'finding:ACP.GIT_METADATA.MISSING:git-dir/commondir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-directory', 'public', 'linked', 'commondir', 'directory', 'ACP.GIT_METADATA.WRONG_TYPE', 'git-dir/commondir'), 'linked', 'a3603e37c371e51d871d5008ecdead17fcf529db3d08e4b8d186d6f2bc60d466', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:git-dir/commondir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-fifo', 'public', 'linked', 'commondir', 'fifo', 'ACP.GIT_METADATA.WRONG_TYPE', 'git-dir/commondir'), 'linked', '773a328114af1593aa0999b8e7c7ce8d1786ebb3a358bb5c74f853f0905a8402', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.WRONG_TYPE:git-dir/commondir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-symlink', 'public', 'linked', 'commondir', 'symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'git-dir/commondir'), 'linked', '5ac053e47d6cf60c183a6a7f9e0ef0471a6e5d48c22d6e1446e25573d6badd2e', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:git-dir/commondir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-cap-n-malformed', 'public', 'linked', 'commondir', '4096-bytes', 'ACP.GIT_METADATA.RECORD_SHAPE', 'git-dir/commondir'), 'linked', '42044cea7e3867efabc171c034c87b5cf4d07389934d52480854e8b938612133', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-cap-n-plus-one', 'public', 'linked', 'commondir', '4097-bytes', 'ACP.GIT_METADATA.BYTE_CAP', 'git-dir/commondir'), 'linked', 'e3a384c51984783d5828fc196d50be17dcaad58670e92a91627e1408fb4f7298', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:one', 'read:bytes:nonempty', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.BYTE_CAP:git-dir/commondir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-invalid-utf8', 'public', 'linked', 'commondir', 'invalid-utf8', 'ACP.GIT_METADATA.INVALID_UTF8', 'git-dir/commondir'), 'linked', 'cc61bf3eee2be8a806abc800ee050b0318c3e450076ec7ab6fd4e8278422f796', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-missing-lf', 'public', 'linked', 'commondir', 'missing-lf', 'ACP.GIT_METADATA.LINE_COUNT', 'git-dir/commondir'), 'linked', '9b9f1b97ff6bd8dbf0383c07df55b069264f9ca76b4103dec107f916aa3be8b6', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-extra-lf', 'public', 'linked', 'commondir', 'extra-lf', 'ACP.GIT_METADATA.LINE_COUNT', 'git-dir/commondir'), 'linked', 'f66c2b77bcd5fdf6e8ab4fd59a59a82a356fcf466731307e184b31e3aaedd81e', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('commondir-mismatch', 'public', 'linked', 'commondir', 'wrong-relative', 'ACP.GIT_METADATA.COMMONDIR_MISMATCH', 'git-dir/commondir'), 'linked', '373b84cf79bf8e5fdea432a63aa3ce30d82ebccabb57840e010708aa98ed13ee', ('dot_git', 'linked_git_dir', 'backlink', 'commondir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-file', 'public', 'both', 'prohibited_grafts', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'info/grafts'), 'conventional', 'c4ebcc87f09be1898b9a6b6bda59b65e1f4084e8d583520dcdc30fd9dda6b48a', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-directory', 'public', 'both', 'prohibited_grafts', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'info/grafts'), 'conventional', '05cf91c259232ba9b09b3b532830691533b2f363cdb5e152b9acbfd9386df468', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-fifo', 'public', 'both', 'prohibited_grafts', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'info/grafts'), 'conventional', 'ca7222ba014106974cb36c77397f6266ffdd824f0d0209fc94e3bd50060d7336', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-live-symlink', 'public', 'both', 'prohibited_grafts', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'info/grafts'), 'conventional', '1f3806b4a2ed0abe27fb9a022b35194077b862265ee25c08eab5ca51576a355c', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-broken-symlink', 'public', 'both', 'prohibited_grafts', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'info/grafts'), 'conventional', '1f3806b4a2ed0abe27fb9a022b35194077b862265ee25c08eab5ca51576a355c', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-ancestor-symlink', 'public', 'both', 'prohibited_grafts', 'info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'info'), 'conventional', 'c0b6d8cda208670b7917d21dcd57da0509d36e901b39758c0198a34ea903715f', ('dot_git', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-file', 'public', 'both', 'prohibited_grafts', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'info/grafts'), 'linked', 'f2274ebfcfdb13cf6969c562609463fa7014d963c4c227e5fae14972bcb39f93', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-directory', 'public', 'both', 'prohibited_grafts', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'info/grafts'), 'linked', '6feaa0dab7c46866df597d9fba4167119e6ba14a485245239c14792a54dd547e', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-fifo', 'public', 'both', 'prohibited_grafts', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'info/grafts'), 'linked', '8caa89e92ec73dac4166fbb020d9f8f226a23316775a8472dde098193a6dfdb1', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-live-symlink', 'public', 'both', 'prohibited_grafts', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'info/grafts'), 'linked', '98fc354cc48612e419003173aceafad61e3573267655757012ed622fdad8a2a3', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-broken-symlink', 'public', 'both', 'prohibited_grafts', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'info/grafts'), 'linked', '98fc354cc48612e419003173aceafad61e3573267655757012ed622fdad8a2a3', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:info/grafts', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('grafts-ancestor-symlink', 'public', 'both', 'prohibited_grafts', 'info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'info'), 'linked', '73531cf5a8856dce136ed97ef88765a22e6226fd02b154e9fdeb4fbccc6d816d', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-file', 'public', 'both', 'prohibited_shallow', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'shallow'), 'conventional', '4297a01db0c23ddbc6f1dcdc3e61522422258f93bcaaee11c0cc85a6a8bb7642', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-directory', 'public', 'both', 'prohibited_shallow', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'shallow'), 'conventional', '385fa8de4292f2d29d20a762bb1af06d01c91c9e7a59ecb521036b4014d782bd', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-fifo', 'public', 'both', 'prohibited_shallow', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'shallow'), 'conventional', 'ee611b5682170426f3b1bdceb00c26270e7f5cdc74971752761b168a3d801be9', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-live-symlink', 'public', 'both', 'prohibited_shallow', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'shallow'), 'conventional', '8c50f67e21ef47e3c6cac327fc6f5e8e4601f6e00929a1c18736d6db1b00baa5', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-broken-symlink', 'public', 'both', 'prohibited_shallow', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'shallow'), 'conventional', '8c50f67e21ef47e3c6cac327fc6f5e8e4601f6e00929a1c18736d6db1b00baa5', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-file', 'public', 'both', 'prohibited_shallow', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'shallow'), 'linked', '7ded01e5880cff15112d5e3b097783e0365e41713d7614c5099d781a8bec829c', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-directory', 'public', 'both', 'prohibited_shallow', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'shallow'), 'linked', '36b39ceae97ec3330273238b8ec307036ca8a64f80e72c8936b99b8b629bdb4f', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-fifo', 'public', 'both', 'prohibited_shallow', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'shallow'), 'linked', '0f11420ed47ab0d44093728c5ffde6b6ceca78dc5ac0865a29eb7d248da310e5', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-live-symlink', 'public', 'both', 'prohibited_shallow', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'shallow'), 'linked', 'e9e50a4f7ac27cbee98c53feb34d9b81b7e9f1abe4944f598f6143c494ef7ea5', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('shallow-broken-symlink', 'public', 'both', 'prohibited_shallow', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'shallow'), 'linked', 'e9e50a4f7ac27cbee98c53feb34d9b81b7e9f1abe4944f598f6143c494ef7ea5', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:shallow', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-file', 'public', 'both', 'prohibited_alternates', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/alternates'), 'conventional', 'c16b0f2132ccfb26ef6ba72de8a18bc643309f98b570a44af2994dcb98d51647', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-directory', 'public', 'both', 'prohibited_alternates', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/alternates'), 'conventional', '37efbccb8685bc11484be116eacbb3a5ff18f01cf0a2dc00e53a09377a2063b4', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-fifo', 'public', 'both', 'prohibited_alternates', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/alternates'), 'conventional', 'd0e0e4462d44d80876056bf30859a2795a7020417febfba51741c786503b57b9', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-live-symlink', 'public', 'both', 'prohibited_alternates', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/alternates'), 'conventional', '8bbf1b8bb6e2d718293a429206b6bbe0e507a1f3d27cfcd2c11ff2f2496998e2', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-broken-symlink', 'public', 'both', 'prohibited_alternates', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/alternates'), 'conventional', '8bbf1b8bb6e2d718293a429206b6bbe0e507a1f3d27cfcd2c11ff2f2496998e2', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-ancestor-symlink', 'public', 'both', 'prohibited_alternates', 'objects-info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'objects/info'), 'conventional', 'db08023378b72226c60d9780cce6d5bbc87205164a2db8646380b065279d217a', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:objects/info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-file', 'public', 'both', 'prohibited_alternates', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/alternates'), 'linked', '6023270ca43ad7c4a5dafc78d3add88c96aa35a40abe5aa1cc5d8b151628241c', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-directory', 'public', 'both', 'prohibited_alternates', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/alternates'), 'linked', 'c760f74931ad947ac1ad6912222b8c3a24e5ec9aaad8137e5df94523a8c14693', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-fifo', 'public', 'both', 'prohibited_alternates', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/alternates'), 'linked', '435898f9d8bb7f331cd837d57e17f424aa461b760eb91f5386ed5efc93bd22af', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-live-symlink', 'public', 'both', 'prohibited_alternates', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/alternates'), 'linked', '9eb70b70bf8eb2379df7a94e91438e23ee76f44ac693e50a1546416a7b54744a', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-broken-symlink', 'public', 'both', 'prohibited_alternates', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/alternates'), 'linked', '9eb70b70bf8eb2379df7a94e91438e23ee76f44ac693e50a1546416a7b54744a', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('alternates-ancestor-symlink', 'public', 'both', 'prohibited_alternates', 'objects-info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'objects/info'), 'linked', '25f133f06a8221f4a9429e1f4be0377a32221c08481121be416f120ae7bcfe3e', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:objects/info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-file', 'public', 'both', 'prohibited_http_alternates', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/http-alternates'), 'conventional', '3f357ca1f4284997a17b41ca26cb13d9596247738109c989e0ef91725c603855', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-directory', 'public', 'both', 'prohibited_http_alternates', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/http-alternates'), 'conventional', 'ccd3893079f179608497efb56ea34820d0b6a26090e7ef9cf0b681781919e267', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-fifo', 'public', 'both', 'prohibited_http_alternates', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/http-alternates'), 'conventional', '65d5980fe7e14cc2428c8250cb73b5abf41ed85bee20b85cab98132e2a16a574', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-live-symlink', 'public', 'both', 'prohibited_http_alternates', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/http-alternates'), 'conventional', 'a8343807ccadc2ed8158fc3f54c1cbbd30c59eff47056e87ceb8c2e8d8db112b', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-broken-symlink', 'public', 'both', 'prohibited_http_alternates', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/http-alternates'), 'conventional', 'a8343807ccadc2ed8158fc3f54c1cbbd30c59eff47056e87ceb8c2e8d8db112b', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-ancestor-symlink', 'public', 'both', 'prohibited_http_alternates', 'objects-info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'objects/info'), 'conventional', 'f642edd718bdcd55455d3180433c3abd98c42d288f5e3c660cd2c862c9c780fd', ('dot_git', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:objects/info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-file', 'public', 'both', 'prohibited_http_alternates', 'file', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/http-alternates'), 'linked', 'fc4f159dd5e0a8c6e7ed40d34e03d491d8961b085eaedcd7d74e3e1c713f35d3', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-directory', 'public', 'both', 'prohibited_http_alternates', 'directory', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/http-alternates'), 'linked', '2d3dd817537e21a673f0fd71a4d332410fc1597817375761baa953dbadac8dde', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-fifo', 'public', 'both', 'prohibited_http_alternates', 'fifo', 'ACP.GIT_METADATA.PROHIBITED', 'objects/info/http-alternates'), 'linked', 'c971266dfa0b671e3160d6c58bfbe644cf81ca3de58b6335e36a25183a9c2b2d', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:other', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.PROHIBITED:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-live-symlink', 'public', 'both', 'prohibited_http_alternates', 'live-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/http-alternates'), 'linked', '9a2fc3c8ce2949267070166c7bb235931de13f839466b2120d82ef27ebecdfd9', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-broken-symlink', 'public', 'both', 'prohibited_http_alternates', 'broken-symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', 'objects/info/http-alternates'), 'linked', '9a2fc3c8ce2949267070166c7bb235931de13f839466b2120d82ef27ebecdfd9', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:objects/info/http-alternates', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('http-alternates-ancestor-symlink', 'public', 'both', 'prohibited_http_alternates', 'objects-info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'objects/info'), 'linked', 'f63b5ce399393a2c47e11d3703b413afc98d5a1d3458c27831f95338964fbae2', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates', 'prohibited_http_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_http_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:objects/info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('linked-external-ancestor-symlink', 'public', 'linked', 'prohibited_alternates', 'external-objects-info-symlink', 'ACP.GIT_METADATA.ANCESTOR_SYMLINK', 'objects/info'), 'linked', '25f133f06a8221f4a9429e1f4be0377a32221c08481121be416f120ae7bcfe3e', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.ANCESTOR_SYMLINK:objects/info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('linked-external-ancestor-replacement', 'public', 'linked', 'prohibited_alternates', 'external-objects-info-lstat-open-race', 'ACP.GIT_METADATA.IDENTITY_CHANGED', 'objects/info'), 'linked', '51f5dd09b4b9cc30272ea7bdb9d996b1c18aba99430139dffaf2e047ad9bc996', ('dot_git', 'linked_git_dir', 'backlink', 'commondir', 'common_dir', 'prohibited_grafts', 'prohibited_shallow', 'prohibited_alternates'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('backlink', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('commondir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('common_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:directory', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'result:directory', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_grafts', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_shallow', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:error:FileNotFoundError:errno', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'lstat:error:FileNotFoundError:errno', 'result:absent', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('prohibited_alternates', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:one', 'open:error:OSError:errno', 'finding:ACP.GIT_METADATA.IDENTITY_CHANGED:objects/info', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('linked-git-dir-target-symlink', 'public', 'linked', 'linked_git_dir', 'symlink', 'ACP.GIT_METADATA.TARGET_SYMLINK', '.git.gitdir'), 'linked', '747b6fe385535068755dc779121334e5050a1014d8d9cf378709847f6a7db27c', ('dot_git', 'linked_git_dir'), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')), ('linked_git_dir', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:symlink', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:directory:nofollow', 'fstat:identity:directory', 'read:none', 'post-lstat:none', 'exception:none', 'finding:ACP.GIT_METADATA.TARGET_SYMLINK:.git.gitdir', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')))),
    (('short-read', 'direct', 'linked', 'dot_git', 'one-byte-to-eof', None, '.git'), 'linked', '35fbce1c0092aca820d29705ece0f5bc287b6d184c8ebed65037845eae44cafb', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
    (('reverse-close', 'direct', 'linked', 'dot_git', 'reverse-once', None, '.git'), 'linked', '35fbce1c0092aca820d29705ece0f5bc287b6d184c8ebed65037845eae44cafb', ('dot_git',), (('dot_git', ('reader-call', 'root:absolute-canonical', 'lstat:observed', 'lstat:ok:regular', 'open:multiple', 'open:ok:directory:nofollow', 'open:ok:regular:nofollow', 'fstat:identity:regular', 'read:multiple', 'read:bytes:nonempty', 'read:bytes:empty', 'post-lstat:identity:regular', 'exception:none', 'result:record', 'close:multiple', 'close:ok', 'close:ok', 'close:reverse', 'cleanup:reverse-complete')),)),
)
# fmt: on

EXPECTED_METADATA_EXECUTION_COUNT = 129
EXPECTED_METADATA_EXECUTION_SHA256 = (
    "dc206260cb4f4c2d1217ba9a6cf274279c2fdbe6c98f5c4c0db21d133558e91b"
)
EXPECTED_METADATA_FULL_EXECUTION_SHA256 = (
    "88a2ce093e0e937cff3922ae790eb5fddfb0fcf7758e92c4cfe0abf597f2ab5b"
)

TEXTUAL_TRANSFORMS = ("missing_lf", "crlf", "extra_line", "corrupt_token", "valid_token")
EXPECTED_TEXTUAL_TRANSFORMATIONS: tuple[TextualTransformation, ...] = (
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
    ("merge_scan", "missing_lf", True, "git", "ACP.GIT.OUTPUT_LINES", "merge_scan"),
    ("merge_scan", "crlf", True, "git", "ACP.GIT.STDOUT_BYTES", "merge_scan"),
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
TEXTUAL_TRANSFORMATION_COUNT = 70
TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT = 45
TEXTUAL_TRANSFORMATION_SHA256 = "707138d773ab4c86dfd8422048a5807c3f5e32bf5a3284dac28bf6d49650e217"


class CompletedProcessSubclass(subprocess.CompletedProcess[bytes]):
    """Exact-type negative for the Git result boundary."""


class BytesSubclass(bytes):
    """Exact-type negative for the Git stdout boundary."""


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

METADATA_READER_SOURCE = """def _read_git_metadata_nofollow(
    root: str | Path,
    *,
    provenance: GitMetadataProvenance,
    io: MetadataIO,
) -> GitMetadataReadResult:
    descriptors: list[int] = []
    directory_records: list[GitMetadataRecord] = []
    role_specs = {item[0]: item[1:] for item in STATIC_GIT_METADATA_ROLE_SPECS}
    role_spec = role_specs.get(provenance.role)
    location = role_spec[2] if role_spec is not None else "provenance"

    def result(
        record: GitMetadataRecord | None,
        findings: tuple[Finding, ...],
    ) -> GitMetadataReadResult:
        close_failed = False
        for descriptor in reversed(descriptors):
            try:
                io.close(descriptor)
            except OSError:
                close_failed = True
        descriptors.clear()
        if close_failed and not findings:
            return GitMetadataReadResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.IO_ERROR", location),),
            )
        return GitMetadataReadResult(record, findings)

    raw_root = os.fspath(root)
    raw_root_parts = raw_root.split("/")[1:] if raw_root.startswith("/") else []
    if (
        not raw_root.startswith("/")
        or raw_root == "/"
        or raw_root.endswith("/")
        or not raw_root_parts
        or any(part in {"", ".", ".."} for part in raw_root_parts)
    ):
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.NONABSOLUTE", "root"),),
        )
    root_path = Path(raw_root)
    if role_spec is None:
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
        )
    expected_kind = str(role_spec[0])
    max_bytes = int(role_spec[1])
    record = provenance.dot_git_record
    if provenance.role == "dot_git":
        path = root_path / ".git"
    elif record is None or record.path != root_path / ".git":
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
        )
    else:
        if record.payload is None:
            common_dir = root_path / ".git"
            linked = None
        else:
            try:
                record_text = record.payload.decode("utf-8")
            except UnicodeDecodeError:
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
                )
            if not record_text.startswith("gitdir: /") or not record_text.endswith("\\n"):
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
                )
            raw_linked = record_text[8:-1]
            raw_parts = raw_linked.split("/")[1:]
            if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
                )
            linked = Path(raw_linked)
            if linked.parent.name != "worktrees" or not linked.name:
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
                )
            common_dir = linked.parent.parent
        if provenance.role == "linked_git_dir" and linked is not None:
            path = linked
        elif provenance.role == "backlink" and linked is not None:
            path = linked / "gitdir"
        elif provenance.role == "commondir" and linked is not None:
            path = linked / "commondir"
        elif provenance.role == "common_dir":
            path = common_dir
        elif provenance.role.startswith("prohibited_"):
            prohibited_relatives = {
                "prohibited_grafts": "info/grafts",
                "prohibited_shallow": "shallow",
                "prohibited_alternates": "objects/info/alternates",
                "prohibited_http_alternates": "objects/info/http-alternates",
            }
            if provenance.role not in prohibited_relatives:
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
                )
            path = common_dir / prohibited_relatives[provenance.role]
        else:
            return result(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
            )
    if not path.is_absolute() or ".." in path.parts:
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
        )
    root_components = root_path.parts[1:]
    components = path.parts[1:]
    within_root = components[: len(root_components)] == root_components
    if not within_root and provenance.role == "dot_git":
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
        )
    relative_parts = components[len(root_components) :] if within_root else ()
    external_base_components = common_dir.parts[1:] if not within_root else ()
    root_component_count = len(root_path.parts) - 1
    try:
        parent_fd = io.open(
            "/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=None
        )
        descriptors.append(parent_fd)
        for ordinal, component in enumerate(components):
            final = ordinal == len(components) - 1
            before = io.lstat(component, dir_fd=parent_fd)
            if final:
                component_location = location
            elif not within_root:
                if ordinal < len(external_base_components) - 1:
                    component_location = "external-root"
                elif ordinal == len(external_base_components) - 1:
                    component_location = "common-dir"
                else:
                    traversed = components[len(external_base_components) : ordinal + 1]
                    component_location = Path(*traversed).as_posix()
            elif ordinal < root_component_count:
                component_location = "root"
            else:
                traversed = relative_parts[: ordinal - root_component_count + 1]
                if traversed and traversed[0] == ".git" and location != ".git":
                    traversed = traversed[1:]
                component_location = Path(*traversed).as_posix() if traversed else "root"
            if stat.S_ISLNK(before.st_mode):
                code = (
                    "ACP.GIT_METADATA.TARGET_SYMLINK"
                    if final
                    else "ACP.GIT_METADATA.ANCESTOR_SYMLINK"
                )
                return result(
                    None, (Finding("git-metadata", "CURRENT", code, component_location),)
                )
            if final and expected_kind == "prohibited_absent":
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.PROHIBITED", location),),
                )
            directory = stat.S_ISDIR(before.st_mode)
            regular = stat.S_ISREG(before.st_mode)
            if (not final and not directory) or (
                final
                and not (
                    (directory and expected_kind in {"directory", "directory_or_regular_record"})
                    or (regular and expected_kind in {"regular_record", "directory_or_regular_record"})
                )
            ):
                return result(
                    None,
                    (
                        Finding(
                            "git-metadata",
                            "CURRENT",
                            "ACP.GIT_METADATA.WRONG_TYPE",
                            component_location,
                        ),
                    ),
                )
            flags = os.O_RDONLY | os.O_NOFOLLOW | (os.O_DIRECTORY if directory else 0)
            try:
                child_fd = io.open(component, flags, dir_fd=parent_fd)
            except OSError as error:
                code = (
                    "ACP.GIT_METADATA.IDENTITY_CHANGED"
                    if error.errno in {errno.ENOENT, errno.ELOOP}
                    else "ACP.GIT_METADATA.IO_ERROR"
                )
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", code, component_location),),
                )
            descriptors.append(child_fd)
            after = io.fstat(child_fd)
            if stat.S_IFMT(before.st_mode) != stat.S_IFMT(after.st_mode):
                return result(
                    None,
                    (
                        Finding(
                            "git-metadata",
                            "CURRENT",
                            "ACP.GIT_METADATA.WRONG_TYPE",
                            component_location,
                        ),
                    ),
                )
            current_path = Path("/", *components[: ordinal + 1])
            for parent_role, parent_record in provenance.parent_records:
                if parent_record.path != current_path:
                    continue
                parent_spec = role_specs.get(parent_role)
                parent_location = (
                    str(parent_spec[2]) if parent_spec is not None else component_location
                )
                if stat.S_IFMT(parent_record.mode) != stat.S_IFMT(after.st_mode):
                    return result(
                        None,
                        (
                            Finding(
                                "git-metadata",
                                "CURRENT",
                                "ACP.GIT_METADATA.WRONG_TYPE",
                                parent_location,
                            ),
                        ),
                    )
                if (parent_record.device, parent_record.inode) != (
                    after.st_dev,
                    after.st_ino,
                ):
                    return result(
                        None,
                        (
                            Finding(
                                "git-metadata",
                                "CURRENT",
                                "ACP.GIT_METADATA.IDENTITY_CHANGED",
                                parent_location,
                            ),
                        ),
                    )
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                return result(
                    None,
                    (
                        Finding(
                            "git-metadata",
                            "CURRENT",
                            "ACP.GIT_METADATA.IDENTITY_CHANGED",
                            component_location,
                        ),
                    ),
                )
            if not final:
                directory_records.append(
                    GitMetadataRecord(
                        current_path,
                        None,
                        after.st_mode,
                        after.st_dev,
                        after.st_ino,
                        tuple(directory_records),
                    )
                )
                parent_fd = child_fd
                continue
            if directory:
                return result(
                    GitMetadataRecord(
                        path,
                        None,
                        after.st_mode,
                        after.st_dev,
                        after.st_ino,
                        tuple(directory_records),
                    ),
                    (),
                )
            payload = bytearray()
            while True:
                chunk = io.read(child_fd, max_bytes + 1 - len(payload))
                if type(chunk) is not bytes:
                    return result(
                        None,
                        (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.READ_TYPE", location),),
                    )
                payload.extend(chunk)
                if len(payload) > max_bytes:
                    return result(
                        None,
                        (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.BYTE_CAP", location),),
                    )
                if chunk == b"":
                    break
            post = io.lstat(component, dir_fd=parent_fd)
            if stat.S_IFMT(after.st_mode) != stat.S_IFMT(post.st_mode):
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.WRONG_TYPE", location),),
                )
            if (after.st_dev, after.st_ino) != (post.st_dev, post.st_ino):
                return result(
                    None,
                    (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.IDENTITY_CHANGED", location),),
                )
            return result(
                GitMetadataRecord(
                    path,
                    bytes(payload),
                    after.st_mode,
                    after.st_dev,
                    after.st_ino,
                    tuple(directory_records),
                ),
                (),
            )
    except FileNotFoundError:
        if expected_kind == "prohibited_absent":
            return result(None, ())
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.MISSING", location),),
        )
    except OSError:
        return result(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.IO_ERROR", location),),
        )
    return result(
        None,
        (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.IO_ERROR", location),),
    )
"""

METADATA_DISCOVERY_SOURCE = """def discover_git_repository(root: str | Path) -> GitDiscoveryResult:
    raw_root = os.fspath(root)
    root_path = Path(raw_root)

    def parsed_record(
        read_result: GitMetadataReadResult,
        *,
        location: str,
        absolute: bool,
    ) -> tuple[str | None, tuple[Finding, ...]]:
        if read_result.record is None or read_result.record.payload is None:
            return None, (
                Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.MISSING", location),
            )
        try:
            text = read_result.record.payload.decode("utf-8")
        except UnicodeDecodeError:
            return None, (
                Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.INVALID_UTF8", location),
            )
        if text.count("\\n") != 1 or not text.endswith("\\n"):
            return None, (
                Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.LINE_COUNT", location),
            )
        value = text[:-1]
        if "\\r" in value or "\\x00" in value or value == "":
            return None, (
                Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.RECORD_SHAPE", location),
            )
        parts = value.split("/")
        if absolute:
            valid = parts[0] == "" and len(parts) > 1 and all(
                part not in {"", ".", ".."} for part in parts[1:]
            )
        else:
            valid = bool(parts) and all(part == ".." for part in parts)
        if not valid:
            return None, (
                Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.RECORD_SHAPE", location),
            )
        return value, ()

    dot_git = _read_git_metadata_nofollow(
        root,
        provenance=GitMetadataProvenance("dot_git", None),
        io=SYSTEM_METADATA_IO,
    )
    if dot_git.findings:
        return GitDiscoveryResult(None, dot_git.findings)
    if dot_git.record is None:
        return GitDiscoveryResult(
            None, (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.MISSING", ".git"),)
        )
    if dot_git.record.payload is None:
        git_dir = root_path / ".git"
        common_dir = git_dir
    else:
        try:
            text = dot_git.record.payload.decode("utf-8")
        except UnicodeDecodeError:
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.INVALID_UTF8", ".git"),),
            )
        if text.count("\\n") != 1 or not text.endswith("\\n"):
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.LINE_COUNT", ".git"),),
            )
        if "\\r" in text or not text.startswith("gitdir: "):
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.RECORD_SHAPE", ".git"),),
            )
        raw_git_dir = text[8:-1]
        if not raw_git_dir.startswith("/"):
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.NONABSOLUTE", ".git.gitdir"),),
            )
        raw_parts = raw_git_dir.split("/")[1:]
        if (
            "\\x00" in raw_git_dir
            or not raw_parts
            or any(part in {"", ".", ".."} for part in raw_parts)
        ):
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", ".git.gitdir"),),
            )
        git_dir = Path(raw_git_dir)
        common_dir = git_dir.parent.parent
        if (
            git_dir.parent.name != "worktrees"
            or not git_dir.name
            or common_dir == Path("/")
        ):
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.LAYOUT", ".git.gitdir"),),
            )
        linked_provenance = GitMetadataProvenance("linked_git_dir", dot_git.record)
        linked_directory = _read_git_metadata_nofollow(
            root, provenance=linked_provenance, io=SYSTEM_METADATA_IO,
        )
        if linked_directory.findings:
            return GitDiscoveryResult(None, linked_directory.findings)
        if linked_directory.record is None:
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.MISSING", ".git.gitdir"),),
            )
        linked_directory_record = linked_directory.record
        backlink = _read_git_metadata_nofollow(
            root,
            provenance=GitMetadataProvenance(
                "backlink",
                dot_git.record,
                (("linked_git_dir", linked_directory_record),),
            ),
            io=SYSTEM_METADATA_IO,
        )
        if backlink.findings:
            return GitDiscoveryResult(None, backlink.findings)
        backlink_value, backlink_parse_findings = parsed_record(
            backlink, location="git-dir/gitdir", absolute=True,
        )
        if backlink_parse_findings:
            return GitDiscoveryResult(None, backlink_parse_findings)
        if backlink_value != f"{root_path / '.git'}":
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.BACKLINK_MISMATCH", "git-dir/gitdir"),),
            )
        commondir = _read_git_metadata_nofollow(
            root,
            provenance=GitMetadataProvenance(
                "commondir",
                dot_git.record,
                (("linked_git_dir", linked_directory_record),),
            ),
            io=SYSTEM_METADATA_IO,
        )
        if commondir.findings:
            return GitDiscoveryResult(None, commondir.findings)
        commondir_value, commondir_parse_findings = parsed_record(
            commondir, location="git-dir/commondir", absolute=False,
        )
        if commondir_parse_findings:
            return GitDiscoveryResult(None, commondir_parse_findings)
        if commondir_value != "../..":
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.COMMONDIR_MISMATCH", "git-dir/commondir"),),
            )
    if dot_git.record.payload is None:
        common_parent_records = (("dot_git", dot_git.record),)
    else:
        linked_common_records = tuple(
            record
            for record in linked_directory_record.ancestor_records
            if record.path == common_dir
        )
        if len(linked_common_records) != 1:
            return GitDiscoveryResult(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", "common-dir"),),
            )
        common_parent_records = (("common_dir", linked_common_records[0]),)
    common_provenance = GitMetadataProvenance(
        "common_dir", dot_git.record, common_parent_records,
    )
    common = _read_git_metadata_nofollow(
        root, provenance=common_provenance, io=SYSTEM_METADATA_IO,
    )
    if common.findings:
        return GitDiscoveryResult(None, common.findings)
    if common.record is None:
        return GitDiscoveryResult(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.MISSING", "common-dir"),),
        )
    for relative in STATIC_GIT_METADATA_TARGETS:
        prohibited_role = {
            "info/grafts": "prohibited_grafts",
            "shallow": "prohibited_shallow",
            "objects/info/alternates": "prohibited_alternates",
            "objects/info/http-alternates": "prohibited_http_alternates",
        }[relative]
        prohibited_provenance = GitMetadataProvenance(
            prohibited_role,
            dot_git.record,
            (("common_dir", common.record),),
        )
        prohibited = _read_git_metadata_nofollow(
            root, provenance=prohibited_provenance, io=SYSTEM_METADATA_IO,
        )
        if prohibited.findings:
            return GitDiscoveryResult(None, prohibited.findings)
    dot_git_revalidation = _read_git_metadata_nofollow(
        root,
        provenance=GitMetadataProvenance(
            "dot_git", None, (("dot_git", dot_git.record),),
        ),
        io=SYSTEM_METADATA_IO,
    )
    if dot_git_revalidation.findings:
        return GitDiscoveryResult(None, dot_git_revalidation.findings)
    if dot_git.record.payload is not None:
        linked_revalidation = _read_git_metadata_nofollow(
            root,
            provenance=GitMetadataProvenance(
                "linked_git_dir",
                dot_git.record,
                (("linked_git_dir", linked_directory_record),),
            ),
            io=SYSTEM_METADATA_IO,
        )
        if linked_revalidation.findings:
            return GitDiscoveryResult(None, linked_revalidation.findings)
    common_revalidation = _read_git_metadata_nofollow(
        root,
        provenance=GitMetadataProvenance(
            "common_dir", dot_git.record, (("common_dir", common.record),),
        ),
        io=SYSTEM_METADATA_IO,
    )
    if common_revalidation.findings:
        return GitDiscoveryResult(None, common_revalidation.findings)
    return GitDiscoveryResult(GitRepositoryBinding(root_path, git_dir, common_dir), ())
"""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def finding(stage: str, code: str, location: str) -> tuple[protocol.Finding, ...]:
    return (protocol.Finding(stage, "CURRENT", code, location),)


def textual_canonical_payload(role: str) -> bytes:
    payloads = {
        "object_format": b"sha2\n",
        "head": (b"0" * 40) + b"\n",
        "red_type": b"commit\n",
        "red_size": b"65537\n",
        "merge_scan": (b"f" * 40) + b"\n",
        "ancestry_chain": (b"1" * 40) + b" " + (b"2" * 40) + b"\n",
        "red_objects": b"".join((bytes([48 + ordinal]) * 40) + b"\n" for ordinal in range(4)),
        "c3_freeze_size": b"32769\n",
        "red_author": b"other@example.com\n",
    }
    return payloads[role]


def apply_textual_transform(
    role: str,
    transform: str,
    freeze: dict[str, Any],
) -> bytes:
    canonical_payload = textual_canonical_payload(role)
    if transform == "missing_lf":
        return canonical_payload[:-1]
    if transform == "crlf":
        return canonical_payload.replace(b"\n", b"\r\n")
    if transform == "extra_line":
        return canonical_payload + b"x\n"
    if transform == "valid_token":
        if role == "head":
            red_head = freeze["redHead"]
            assert type(red_head) is str
            return red_head.encode() + b"\n"
        return b"blob\n" if role == "red_type" else canonical_payload
    corruptions = {
        "object_format": b"Sha2\n",
        "head": b"A" + canonical_payload[1:],
        "red_type": b"Commit\n",
        "red_size": b"6553x\n",
        "merge_scan": b"F" + canonical_payload[1:],
        "ancestry_chain": b"A" + canonical_payload[1:],
        "red_objects": b"A" + canonical_payload[1:],
        "c3_freeze_size": b"3276x\n",
        "red_author": b"other.example.com\n",
    }
    assert transform == "corrupt_token"
    return corruptions[role]


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


def subprocess_call_ast(source: str) -> tuple[ast.Module, ast.Call]:
    module = ast.parse(source)
    calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    assert len(calls) == 1
    return module, calls[0]


def mutate_argv_source(source: str, index: int, operation: str) -> str:
    module, call = subprocess_call_ast(source)
    assert call.args and isinstance(call.args[0], ast.Tuple)
    elements = call.args[0].elts
    if operation == "omit":
        elements.pop(index)
    elif operation == "wrong":
        elements[index] = ast.Constant(f"wrong-argv-{index}")
    elif operation == "dynamic":
        elements[index] = ast.Name(f"dynamic_argv_{index}", ast.Load())
    elif operation == "reorder":
        elements[index], elements[index + 1] = elements[index + 1], elements[index]
    else:
        raise AssertionError(operation)
    ast.fix_missing_locations(module)
    return ast.unparse(module) + "\n"


def mutate_keyword_source(source: str, index: int, operation: str) -> str:
    module, call = subprocess_call_ast(source)
    if operation == "omit":
        call.keywords.pop(index)
    elif operation == "wrong":
        call.keywords[index].value = ast.Constant(f"wrong-keyword-{index}")
    elif operation == "reorder":
        call.keywords[index], call.keywords[index + 1] = (
            call.keywords[index + 1],
            call.keywords[index],
        )
    else:
        raise AssertionError(operation)
    ast.fix_missing_locations(module)
    return ast.unparse(module) + "\n"


def mutate_environment_source(source: str, index: int, operation: str) -> str:
    module, call = subprocess_call_ast(source)
    environment_keyword = next(item for item in call.keywords if item.arg == "env")
    assert isinstance(environment_keyword.value, ast.Dict)
    keys = environment_keyword.value.keys
    values = environment_keyword.value.values
    if operation == "omit":
        keys.pop(index)
        values.pop(index)
    elif operation == "wrong-value":
        values[index] = ast.Constant(f"wrong-environment-{index}")
    elif operation == "reorder":
        keys[index], keys[index + 1] = keys[index + 1], keys[index]
        values[index], values[index + 1] = values[index + 1], values[index]
    else:
        raise AssertionError(operation)
    ast.fix_missing_locations(module)
    return ast.unparse(module) + "\n"


def expected_git_environment(root: Path) -> dict[str, str]:
    dot_git = root / ".git"
    if dot_git.is_file():
        record = dot_git.read_text(encoding="utf-8")
        assert record.startswith("gitdir: ") and record.endswith("\n")
        git_dir = Path(record.removeprefix("gitdir: ").removesuffix("\n"))
        common_dir = (git_dir / "../..").resolve()
    else:
        git_dir = dot_git.resolve()
        common_dir = git_dir
    return {
        **dict(GIT_ENV_FIXED),
        "GIT_DIR": git_dir.as_posix(),
        "GIT_COMMON_DIR": common_dir.as_posix(),
        "GIT_WORK_TREE": root.resolve().as_posix(),
    }


def expected_git_argv(root: Path, freeze: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    red_head = freeze["redHead"]
    head = git(root, "rev-parse", "HEAD")
    descendants = git(root, "rev-list", "--reverse", f"{red_head}..{head}").splitlines()
    c3_head = descendants[0]
    return (
        (*GIT_PREFIX, "rev-parse", "--show-object-format"),
        (
            *GIT_PREFIX,
            "fsck",
            "--full",
            "--strict",
            "--no-dangling",
            "--no-reflogs",
            "--no-progress",
        ),
        (*GIT_PREFIX, "rev-parse", "HEAD^{commit}"),
        (*GIT_PREFIX, "cat-file", "-t", red_head),
        (*GIT_PREFIX, "cat-file", "-s", red_head),
        (*GIT_PREFIX, "merge-base", "--is-ancestor", red_head, head),
        (*GIT_PREFIX, "rev-list", "--min-parents=2", "--max-count=1", f"{red_head}..{head}"),
        (
            *GIT_PREFIX,
            "rev-list",
            "--parents",
            "--ancestry-path",
            "--reverse",
            "--max-count=65",
            f"{red_head}..{head}",
        ),
        (
            *GIT_PREFIX,
            "diff-tree",
            "-r",
            "--no-ext-diff",
            "--no-renames",
            "--ignore-submodules=none",
            "--quiet",
            red_head,
            c3_head,
            "--",
            ".",
            f":(exclude){FREEZE_PATH}",
        ),
        (
            *GIT_PREFIX,
            "diff-tree",
            "-r",
            "--no-ext-diff",
            "--no-renames",
            "--ignore-submodules=none",
            "--quiet",
            red_head,
            c3_head,
            "--",
            FREEZE_PATH,
        ),
        (
            *GIT_PREFIX,
            "rev-parse",
            f"{red_head}^{{tree}}",
            f"{red_head}:{protocol.MATRIX_PATH.relative_to(protocol.ROOT)}",
            f"{red_head}:{ORACLE_PATHS[0]}",
            f"{red_head}:{ORACLE_PATHS[1]}",
        ),
        (*GIT_PREFIX, "cat-file", "-s", f"{c3_head}:{FREEZE_PATH}"),
        (*GIT_PREFIX, "show", f"{c3_head}:{FREEZE_PATH}"),
        (*GIT_PREFIX, "show", "--no-notes", "--no-show-signature", "-s", "--format=%ae", red_head),
    )


def assert_exact_git_transcript(
    root: Path,
    freeze: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = expected_git_argv(root, freeze)
    expected_env = expected_git_environment(root)
    calls: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    environment_ids: list[int] = []

    def record(argv: tuple[str, ...], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        recorded = {**kwargs, "env": kwargs["env"].copy()}
        calls.append((argv, recorded))
        environment_ids.append(id(kwargs["env"]))
        result = REAL_SUBPROCESS_RUN(argv, **kwargs)
        if len(calls) == 1:
            kwargs["env"]["GIT_DIR"] = "/mutated-after-first-call"
        return result

    with monkeypatch.context() as process_patch:
        for key in (
            "PATH",
            "HOME",
            "GIT_DIR",
            "GIT_COMMON_DIR",
            "GIT_WORK_TREE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_REPLACE_REF_BASE",
            "GIT_CONFIG_SYSTEM",
            "GIT_CONFIG_GLOBAL",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG",
            "GIT_CONFIG_PARAMETERS",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_KEY_0",
            "GIT_CONFIG_VALUE_0",
            "GIT_ASKPASS",
            "SSH_ASKPASS",
            "GIT_SSH",
            "GIT_SSH_COMMAND",
            "GIT_TERMINAL_PROMPT",
            "GIT_PAGER",
            "PAGER",
            "GIT_EXTERNAL_DIFF",
            "GIT_DIFF_OPTS",
            "GIT_NO_LAZY_FETCH",
            "GIT_NO_REPLACE_OBJECTS",
            "GIT_OPTIONAL_LOCKS",
            "GIT_NAMESPACE",
            "GIT_INDEX_FILE",
            "GIT_SHALLOW_FILE",
            "GIT_PROTOCOL",
            "GIT_ALLOW_PROTOCOL",
            "GIT_PROTOCOL_FROM_USER",
            "GIT_EXEC_PATH",
            "GIT_TEST_ASSUME_DIFFERENT_OWNER",
            "GIT_TEST_MISSING_PROMISOR_OBJECT",
        ):
            process_patch.setenv(key, "/hostile/ambient/value")
        process_patch.setattr(PROTOCOL_SUBPROCESS, "run", record)
        assert protocol.validate_repository_freeze(root) == ()
    assert tuple(argv for argv, _ in calls) == expected
    assert len(set(environment_ids)) == len(expected)
    for ordinal, (_, kwargs) in enumerate(calls):
        assert kwargs["cwd"] == root
        assert kwargs["check"] is False
        assert kwargs["stderr"] is subprocess.DEVNULL
        assert kwargs["text"] is False
        assert kwargs["env"] == expected_env
        if ordinal == 1:
            assert kwargs["stdout"] is subprocess.DEVNULL
            assert kwargs["timeout"] == 30
        else:
            assert kwargs["stdout"] is subprocess.PIPE
            assert kwargs["timeout"] == 5


def assert_injected_git_failure(
    root: Path,
    freeze: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    ordinal: int,
    effect: BaseException | object,
    expected_finding: tuple[protocol.Finding, ...],
) -> None:
    expected = expected_git_argv(root, freeze)
    calls: list[tuple[str, ...]] = []

    def inject(argv: tuple[str, ...], **kwargs: Any) -> Any:
        calls.append(argv)
        if len(calls) - 1 != ordinal:
            return REAL_SUBPROCESS_RUN(argv, **kwargs)
        if isinstance(effect, BaseException):
            raise effect
        if callable(effect):
            return effect(REAL_SUBPROCESS_RUN(argv, **kwargs))
        return effect

    with monkeypatch.context() as process_patch:
        process_patch.setattr(PROTOCOL_SUBPROCESS, "run", inject)
        assert protocol.validate_repository_freeze(root) == expected_finding
    assert tuple(calls) == expected[: ordinal + 1]


def assert_scripted_git_failure(
    root: Path,
    freeze: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    transforms: dict[int, Any],
    stopped_after: int,
    expected_finding: tuple[protocol.Finding, ...],
) -> None:
    expected = expected_git_argv(root, freeze)
    calls: list[tuple[str, ...]] = []

    def inject(argv: tuple[str, ...], **kwargs: Any) -> Any:
        ordinal = len(calls)
        calls.append(argv)
        result = REAL_SUBPROCESS_RUN(argv, **kwargs)
        transform = transforms.get(ordinal)
        return result if transform is None else transform(result)

    with monkeypatch.context() as process_patch:
        process_patch.setattr(PROTOCOL_SUBPROCESS, "run", inject)
        assert protocol.validate_repository_freeze(root) == expected_finding
    assert tuple(calls) == expected[:stopped_after]


def assert_metadata_failure(
    root: str | Path,
    monkeypatch: pytest.MonkeyPatch,
    expected_finding: tuple[protocol.Finding, ...],
) -> None:
    calls: list[tuple[str, ...]] = []

    def reject_git(argv: tuple[str, ...], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        del kwargs
        calls.append(argv)
        raise AssertionError("metadata failure must stop before Git")

    with monkeypatch.context() as metadata_patch:
        metadata_patch.setattr(PROTOCOL_SUBPROCESS, "run", reject_git)
        assert protocol.validate_repository_freeze(root) == expected_finding
    assert calls == []


def create_linked_git_freeze(
    tmp_path: Path, *, descendant_commits: int = 0
) -> tuple[Path, dict[str, Any], Path, Path]:
    source, freeze = create_real_git_freeze(
        tmp_path / "source", descendant_commits=descendant_commits
    )
    linked = tmp_path / "linked"
    git(source, "worktree", "add", "--detach", linked.as_posix(), "HEAD")
    git_dir = Path(git(linked, "rev-parse", "--path-format=absolute", "--git-dir"))
    common_dir = Path(git(linked, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return linked, freeze, git_dir, common_dir


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
    merge_after_c3: bool = False,
    dual_red_children: bool = False,
    unchanged_c3: bool = False,
    gitlink_c3: bool = False,
    rename_c3: bool = False,
    signed_red: bool = False,
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
    if rename_c3:
        (root / "rename-source.txt").write_text("renamed scope\n", encoding="utf-8")
    git(root, "add", ".")
    if gitlink_c3:
        initial_link = git(root, "commit-tree", git(root, "write-tree"), "-m", "initial gitlink")
        git(root, "update-index", "--add", "--cacheinfo", f"160000,{initial_link},nonfreeze-link")
    git(root, "commit", "-q", "-m", "genuine RED")
    if signed_red:
        signed_tree = git(root, "rev-parse", "HEAD^{tree}")
        signed_commit = (
            f"tree {signed_tree}\n"
            "author Implementation Author <implementation@example.com> 1787328000 +0000\n"
            "committer Implementation Author <implementation@example.com> 1787328000 +0000\n"
            "gpgsig -----BEGIN PGP SIGNATURE-----\n"
            " fake-signature-material\n"
            " -----END PGP SIGNATURE-----\n\n"
            "genuine signed-looking RED\n"
        ).encode()
        signed_result = REAL_SUBPROCESS_RUN(
            ("git", "hash-object", "-t", "commit", "-w", "--stdin"),
            cwd=root,
            input=signed_commit,
            check=True,
            capture_output=True,
        )
        git(root, "update-ref", "HEAD", signed_result.stdout.decode().strip())
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
    if gitlink_c3:
        replacement_link = git(root, "commit-tree", red_tree, "-m", "replacement gitlink")
        git(
            root,
            "update-index",
            "--cacheinfo",
            f"160000,{replacement_link},nonfreeze-link",
        )
    if rename_c3:
        git(root, "mv", "rename-source.txt", "rename-target.txt")
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
    elif unchanged_c3:
        c3_head = git(root, "commit-tree", red_tree, "-p", red_head, "-m", "unchanged C3")
        git(root, "update-ref", "HEAD", c3_head)
    elif dual_red_children:
        c3_tree = git(root, "write-tree")
        first = git(root, "commit-tree", c3_tree, "-p", red_head, "-m", "C3 first")
        second = git(root, "commit-tree", c3_tree, "-p", red_head, "-m", "C3 second")
        merged = git(
            root,
            "commit-tree",
            c3_tree,
            "-p",
            first,
            "-p",
            second,
            "-m",
            "merge sibling C3 commits",
        )
        git(root, "update-ref", "HEAD", merged)
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
    if merge_after_c3:
        c3_head = git(root, "rev-parse", "HEAD")
        other = git(root, "commit-tree", red_tree, "-p", red_head, "-m", "parallel child")
        merged = git(
            root,
            "commit-tree",
            git(root, "rev-parse", "HEAD^{tree}"),
            "-p",
            c3_head,
            "-p",
            other,
            "-m",
            "merge after C3",
        )
        git(root, "update-ref", "HEAD", merged)
    for ordinal in range(descendant_commits):
        descendant = root / f"post-c3-{ordinal}.txt"
        descendant.write_text(f"post C3 {ordinal}\n", encoding="utf-8")
        git(root, "add", descendant.name)
        git(root, "commit", "-q", "-m", f"post C3 {ordinal}")
    return root, freeze


def test_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, freeze = create_real_git_freeze(tmp_path)
    metadata_execution_rows: list[MetadataExecution] = []

    def metadata_case(case_id: str) -> MetadataCaseRow:
        matches = tuple(row for row in EXPECTED_METADATA_CASES if row[0] == case_id)
        assert len(matches) == 1
        return matches[0]

    def observed_payload_stimulus(case_id: str, case_root: str | Path) -> str | None:
        expected_sha = EXPECTED_METADATA_PAYLOAD_SHA256.get(case_id)
        if expected_sha is None:
            return None
        root_path = Path(case_root)
        if case_id.startswith("dot-git-"):
            payload_path = root_path / ".git"
        else:
            dot_git_payload = (root_path / ".git").read_bytes()
            assert dot_git_payload.startswith(b"gitdir: ") and dot_git_payload.endswith(b"\n")
            linked_git_dir = Path(dot_git_payload[8:-1].decode("utf-8"))
            payload_path = linked_git_dir / (
                "gitdir" if case_id.startswith("backlink-") else "commondir"
            )
        observed_sha = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        assert observed_sha == expected_sha
        return observed_sha

    def traced_metadata_reader(
        called_root: str | Path,
        *,
        provenance: protocol.GitMetadataProvenance,
        io: protocol.MetadataIO,
        role_calls: list[str],
        role_traces: list[MetadataRoleTrace],
    ) -> protocol.GitMetadataReadResult:
        role_calls.append(provenance.role)
        operations: list[str] = []
        opened: list[int] = []
        close_attempts: list[int] = []
        observed_lstats: list[os.stat_result] = []
        observed_fstats: list[os.stat_result] = []

        raw_root = os.fspath(called_root)
        if not os.path.isabs(raw_root):
            root_grammar = "root:relative"
        elif "/../" in raw_root:
            root_grammar = "root:dotdot-component"
        elif "/./" in raw_root:
            root_grammar = "root:dot-component"
        elif "//" in raw_root:
            root_grammar = "root:repeated-separator"
        elif raw_root.endswith("/"):
            root_grammar = "root:trailing-separator"
        else:
            root_grammar = "root:absolute-canonical"

        def kind(mode: int) -> str:
            if stat.S_ISLNK(mode):
                return "symlink"
            if stat.S_ISDIR(mode):
                return "directory"
            if stat.S_ISREG(mode):
                return "regular"
            return "other"

        def observed_lstat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
            try:
                observed = io.lstat(path, dir_fd=dir_fd)
            except OSError as error:
                operations.append(
                    f"lstat:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            if observed_fstats and any(item.startswith("read:") for item in operations):
                prior = observed_fstats[-1]
                if kind(observed.st_mode) != kind(prior.st_mode):
                    relation = "type-drift"
                elif observed.st_dev != prior.st_dev:
                    relation = "device-drift"
                elif observed.st_ino != prior.st_ino:
                    relation = "inode-drift"
                else:
                    relation = "identity"
                operations.append(f"post-lstat:{relation}:{kind(observed.st_mode)}")
            else:
                operations.append(f"lstat:ok:{kind(observed.st_mode)}")
            observed_lstats.append(observed)
            return observed

        def observed_open(
            path: str,
            flags: int,
            *,
            dir_fd: int | None = None,
        ) -> int:
            try:
                descriptor = io.open(path, flags, dir_fd=dir_fd)
            except OSError as error:
                operations.append(
                    f"open:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            opened.append(descriptor)
            operations.append(
                "open:ok:"
                + ("directory" if flags & os.O_DIRECTORY else "regular")
                + (":nofollow" if flags & os.O_NOFOLLOW else ":follow")
            )
            return descriptor

        def observed_fstat(descriptor: int) -> os.stat_result:
            try:
                observed = io.fstat(descriptor)
            except OSError as error:
                operations.append(
                    f"fstat:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            observed_fstats.append(observed)
            prior = observed_lstats[-1]
            if kind(observed.st_mode) != kind(prior.st_mode):
                relation = "type-drift"
            elif observed.st_dev != prior.st_dev:
                relation = "device-drift"
            elif observed.st_ino != prior.st_ino:
                relation = "inode-drift"
            else:
                relation = "identity"
            operations.append(f"fstat:{relation}:{kind(observed.st_mode)}")
            return observed

        def observed_read(descriptor: int, count: int) -> bytes:
            try:
                observed = io.read(descriptor, count)
            except OSError as error:
                operations.append(
                    f"read:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            if type(observed) is bytes:
                operations.append("read:bytes:empty" if observed == b"" else "read:bytes:nonempty")
            else:
                operations.append(f"read:type:{type(observed).__name__}")
            return observed

        def observed_close(descriptor: int) -> None:
            close_attempts.append(descriptor)
            try:
                io.close(descriptor)
            except OSError as error:
                operations.append(
                    f"close:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            operations.append("close:ok")

        observed = cast(
            protocol.GitMetadataReadResult,
            PROTOCOL_METADATA_READER(
                called_root,
                provenance=provenance,
                io=protocol.MetadataIO(
                    observed_lstat,
                    observed_open,
                    observed_fstat,
                    observed_read,
                    observed_close,
                ),
            ),
        )
        assert close_attempts == opened[::-1]
        read_events = tuple(item for item in operations if item.startswith("read:"))
        successful_open_events = tuple(item for item in operations if item.startswith("open:ok:"))
        close_events = tuple(item for item in operations if item.startswith("close:"))
        error_events = tuple(item for item in operations if ":error:" in item)
        last_lstat = next(
            (item for item in reversed(operations) if item.startswith("lstat:")),
            "lstat:none",
        )
        last_fstat = next(
            (item for item in reversed(operations) if item.startswith("fstat:")),
            "fstat:none",
        )
        last_read_index = next(
            (
                index
                for index in range(len(operations) - 1, -1, -1)
                if operations[index].startswith("read:")
            ),
            None,
        )
        post_lstat = next(
            (
                item
                for index, item in enumerate(operations)
                if last_read_index is not None
                and index > last_read_index
                and item.startswith("post-lstat:")
            ),
            "post-lstat:none",
        )
        if observed.findings:
            first_finding = observed.findings[0]
            terminal = f"finding:{first_finding.code}:{first_finding.location}"
        elif observed.record is None:
            terminal = "result:absent"
        elif observed.record.payload is None:
            terminal = "result:directory"
        else:
            terminal = "result:record"
        role_traces.append(
            (
                provenance.role,
                (
                    "reader-call",
                    root_grammar,
                    "lstat:observed" if last_lstat != "lstat:none" else "lstat:none",
                    last_lstat,
                    (
                        "open:none"
                        if not opened
                        else "open:one"
                        if len(opened) == 1
                        else "open:multiple"
                    ),
                    *(
                        successful_open_events
                        if len(successful_open_events) <= 1
                        else (successful_open_events[0], successful_open_events[-1])
                    ),
                    last_fstat,
                    (
                        "read:none"
                        if not read_events
                        else "read:one"
                        if len(read_events) == 1
                        else "read:multiple"
                    ),
                    *(read_events if len(read_events) <= 1 else (read_events[0], read_events[-1])),
                    post_lstat,
                    (
                        "exception:none"
                        if not error_events
                        else "exception:one"
                        if len(error_events) == 1
                        else "exception:multiple"
                    ),
                    *(
                        error_events
                        if len(error_events) <= 1
                        else (error_events[0], error_events[-1])
                    ),
                    terminal,
                    (
                        "close:none"
                        if not close_attempts
                        else "close:one"
                        if len(close_attempts) == 1
                        else "close:multiple"
                    ),
                    *(
                        close_events
                        if len(close_events) <= 1
                        else (close_events[0], close_events[-1])
                    ),
                    "close:reverse",
                    "cleanup:reverse-complete",
                ),
            )
        )
        return observed

    def finish_metadata_execution(
        case_id: str,
        role_calls: list[str],
        role_traces: list[MetadataRoleTrace],
        operational_mode: str | None = None,
        observed_payload_sha: str | None = None,
    ) -> MetadataCaseRow:
        row = metadata_case(case_id)
        mode = operational_mode or ("conventional" if row[2] == "both" else row[2])
        assert mode in ({"conventional", "linked"} if row[2] == "both" else {row[2]})
        normalized_roles = tuple(role_calls)
        expected_payload_sha = EXPECTED_METADATA_PAYLOAD_SHA256.get(case_id)
        assert observed_payload_sha == expected_payload_sha
        payload_sha = observed_payload_sha or "no-payload"
        stimulus_identity = hashlib.sha256(canonical((mode, payload_sha, role_traces))).hexdigest()
        execution: MetadataExecution = (
            row,
            mode,
            stimulus_identity,
            normalized_roles,
            tuple(role_traces),
        )
        assert execution not in metadata_execution_rows
        assert execution == EXPECTED_METADATA_EXECUTIONS[len(metadata_execution_rows)]
        metadata_execution_rows.append(execution)
        return row

    def execute_metadata_success_case(
        case_id: str,
        case_root: str | Path,
        expected: protocol.GitDiscoveryResult,
    ) -> None:
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []

        def observed_reader(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            return traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
            )

        with monkeypatch.context() as success_patch:
            success_patch.setattr(protocol, "_read_git_metadata_nofollow", observed_reader)
            assert protocol.discover_git_repository(case_root) == expected
        finish_metadata_execution(case_id, role_calls, role_traces)

    def execute_metadata_case(
        case_id: str,
        case_root: str | Path,
        expected_finding: tuple[protocol.Finding, ...],
        operational_mode: str | None = None,
    ) -> None:
        row = metadata_case(case_id)
        payload_sha = observed_payload_stimulus(case_id, case_root)
        assert row[1] == "public"
        assert row[5] is not None
        assert expected_finding == finding("git-metadata", row[5], row[6])
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []

        def observed_reader(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            return traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
            )

        with monkeypatch.context() as reader_patch:
            reader_patch.setattr(protocol, "_read_git_metadata_nofollow", observed_reader)
            assert_metadata_failure(case_root, reader_patch, expected_finding)
        assert role_calls
        assert role_calls[-1] == row[3]
        finish_metadata_execution(
            case_id,
            role_calls,
            role_traces,
            operational_mode,
            payload_sha,
        )

    def execute_metadata_io_case(
        case_id: str,
        case_root: str | Path,
        metadata_io: protocol.MetadataIO,
        expected_finding: tuple[protocol.Finding, ...],
        operational_mode: str | None = None,
    ) -> None:
        row = metadata_case(case_id)
        assert row[1] == "public"
        assert row[5] is not None
        assert expected_finding == finding("git-metadata", row[5], row[6])
        git_calls: list[tuple[str, ...]] = []
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []

        def observed_reader(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            return traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
            )

        with monkeypatch.context() as io_patch:
            io_patch.setattr(protocol, "SYSTEM_METADATA_IO", metadata_io)
            io_patch.setattr(protocol, "_read_git_metadata_nofollow", observed_reader)
            io_patch.setattr(
                PROTOCOL_SUBPROCESS,
                "run",
                lambda argv, **kwargs: git_calls.append(argv),
            )
            assert protocol.validate_repository_freeze(case_root) == expected_finding
        assert git_calls == []
        assert role_calls
        assert role_calls[-1] == row[3]
        finish_metadata_execution(case_id, role_calls, role_traces, operational_mode)

    def execute_between_read_case(
        case_id: str,
        case_root: Path,
        after_role: str,
        mutate: Callable[[], None],
        operational_mode: str | None = None,
    ) -> None:
        row = metadata_case(case_id)
        assert row[1] == "public"
        assert row[5] is not None
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []
        mutated = False
        git_calls: list[tuple[str, ...]] = []

        def mutate_between_roles(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            nonlocal mutated
            result = traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
            )
            if provenance.role == after_role and not result.findings and not mutated:
                mutate()
                mutated = True
            return result

        with monkeypatch.context() as between_patch:
            between_patch.setattr(protocol, "_read_git_metadata_nofollow", mutate_between_roles)
            between_patch.setattr(
                PROTOCOL_SUBPROCESS,
                "run",
                lambda argv, **kwargs: git_calls.append(argv),
            )
            assert protocol.validate_repository_freeze(case_root) == finding(
                "git-metadata", row[5], row[6]
            )
        assert mutated
        assert git_calls == []
        assert role_calls[-1] == row[3]
        finish_metadata_execution(case_id, role_calls, role_traces, operational_mode)

    red_nodes = frozen_red_nodes()
    assert len(red_nodes) == protocol.EXPECTED_RED_FAILURES_COUNT
    assert hashlib.sha256(canonical(red_nodes)).hexdigest() == (
        protocol.EXPECTED_RED_FAILURES_SHA256
    )
    execute_metadata_success_case(
        "conventional-positive",
        root,
        protocol.GitDiscoveryResult(
            protocol.GitRepositoryBinding(root, root / ".git", root / ".git"),
            (),
        ),
    )
    assert_exact_git_transcript(root, freeze, monkeypatch)
    roles = (
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
    output_caps = (5, None, 41, 7, 6, 0, 41, 5330, 0, 0, 164, 6, 32768, 320)
    assert len(EXPECTED_TEXTUAL_TRANSFORMATIONS) == TEXTUAL_TRANSFORMATION_COUNT
    assert sum(row[2] for row in EXPECTED_TEXTUAL_TRANSFORMATIONS) == (
        TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT
    )
    assert tuple(dict.fromkeys(row[0] for row in EXPECTED_TEXTUAL_TRANSFORMATIONS)) == roles
    assert all(
        tuple(row[1] for row in EXPECTED_TEXTUAL_TRANSFORMATIONS if row[0] == role)
        == TEXTUAL_TRANSFORMS
        for role in roles
    )
    assert hashlib.sha256(canonical(EXPECTED_TEXTUAL_TRANSFORMATIONS)).hexdigest() == (
        TEXTUAL_TRANSFORMATION_SHA256
    )
    for role, transform_name, applicable, stage, code, location in EXPECTED_TEXTUAL_TRANSFORMATIONS:
        if not applicable:
            assert role in {
                "object_integrity",
                "red_ancestor",
                "c3_other_scope",
                "c3_freeze_change",
                "c3_freeze_payload",
            }
            assert stage is code is location is None
            continue
        assert stage is not None and code is not None and location is not None
        ordinal = roles.index(role)
        transformed_payload = apply_textual_transform(role, transform_name, freeze)
        calls: list[tuple[str, ...]] = []

        def inject_textual_transform(
            argv: tuple[str, ...], **kwargs: Any
        ) -> subprocess.CompletedProcess[bytes]:
            call_ordinal = len(calls)
            calls.append(argv)
            result = REAL_SUBPROCESS_RUN(argv, **kwargs)
            if call_ordinal != ordinal:
                return result
            return subprocess.CompletedProcess(
                result.args,
                result.returncode,
                transformed_payload,
                result.stderr,
            )

        with monkeypatch.context() as textual_patch:
            textual_patch.setattr(PROTOCOL_SUBPROCESS, "run", inject_textual_transform)
            assert protocol.validate_repository_freeze(root) == finding(stage, code, location)
        assert tuple(calls) == expected_git_argv(root, freeze)[: ordinal + 1]
    for ordinal, role in enumerate(roles):
        argv = expected_git_argv(root, freeze)[ordinal]
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            subprocess.TimeoutExpired(argv, 5),
            finding("git", "ACP.GIT.TIMEOUT", role),
        )
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            OSError("contained"),
            finding("git", "ACP.GIT.OS_ERROR", role),
        )
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            object(),
            finding("git", "ACP.GIT.RESULT_TYPE", role),
        )
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            lambda result: CompletedProcessSubclass(
                result.args, result.returncode, result.stdout, result.stderr
            ),
            finding("git", "ACP.GIT.RESULT_TYPE", role),
        )
        for transform, code in (
            (
                lambda result: subprocess.CompletedProcess(
                    ("wrong",), result.returncode, result.stdout, result.stderr
                ),
                "ACP.GIT.ARGS_MISMATCH",
            ),
            (
                lambda result: subprocess.CompletedProcess(
                    result.args, True, result.stdout, result.stderr
                ),
                "ACP.GIT.RETURNCODE_TYPE",
            ),
            (
                lambda result: subprocess.CompletedProcess(
                    result.args, result.returncode, result.stdout, b"unexpected"
                ),
                "ACP.GIT.STDERR_TYPE",
            ),
            (
                lambda result: subprocess.CompletedProcess(
                    result.args,
                    result.returncode,
                    b"unexpected" if ordinal == 1 else "unexpected",
                    result.stderr,
                ),
                "ACP.GIT.STDOUT_TYPE",
            ),
            (
                lambda result: subprocess.CompletedProcess(
                    result.args,
                    result.returncode,
                    BytesSubclass(b"") if ordinal == 1 else BytesSubclass(result.stdout),
                    result.stderr,
                ),
                "ACP.GIT.STDOUT_TYPE",
            ),
            (
                lambda result: subprocess.CompletedProcess(
                    result.args, cast(Any, 0.0), result.stdout, result.stderr
                ),
                "ACP.GIT.RETURNCODE_TYPE",
            ),
        ):
            assert_injected_git_failure(
                root, freeze, monkeypatch, ordinal, transform, finding("git", code, role)
            )
        for unsupported_returncode in (-1, 2, 127):
            assert_injected_git_failure(
                root,
                freeze,
                monkeypatch,
                ordinal,
                lambda result, unsupported_returncode=unsupported_returncode: (
                    subprocess.CompletedProcess(
                        result.args,
                        unsupported_returncode,
                        (None if ordinal == 1 else b"x" * (cast(int, output_caps[ordinal]) + 1)),
                        result.stderr,
                    )
                ),
                finding("git", "ACP.GIT.RETURN_CODE", role),
            )
    assert_injected_git_failure(
        root,
        freeze,
        monkeypatch,
        1,
        lambda result: subprocess.CompletedProcess(result.args, 1, None, None),
        finding("freeze", "ACP.FREEZE.OBJECT_DB_INTEGRITY", "object-db"),
    )
    assert_injected_git_failure(
        root,
        freeze,
        monkeypatch,
        3,
        lambda result: subprocess.CompletedProcess(result.args, 128, b"", None),
        finding("freeze", "ACP.FREEZE.RED_HEAD_MISSING", "redHead"),
    )
    for ordinal, role in enumerate(roles):
        precedence_argv = expected_git_argv(root, freeze)[ordinal]
        for transform, code in (
            (
                lambda result: CompletedProcessSubclass(("wrong",), True, b"wrong", b"wrong"),
                "ACP.GIT.RESULT_TYPE",
            ),
            (
                lambda result: subprocess.CompletedProcess(("wrong",), True, "wrong", b"wrong"),
                "ACP.GIT.ARGS_MISMATCH",
            ),
            (
                lambda result, argv=precedence_argv: subprocess.CompletedProcess(
                    argv, True, "wrong", b"wrong"
                ),
                "ACP.GIT.STDOUT_TYPE",
            ),
            (
                lambda result, argv=precedence_argv: subprocess.CompletedProcess(
                    argv, True, result.stdout, b"wrong"
                ),
                "ACP.GIT.STDERR_TYPE",
            ),
            (
                lambda result, argv=precedence_argv: subprocess.CompletedProcess(
                    argv, True, result.stdout, result.stderr
                ),
                "ACP.GIT.RETURNCODE_TYPE",
            ),
        ):
            assert_injected_git_failure(
                root,
                freeze,
                monkeypatch,
                ordinal,
                transform,
                finding("git", code, role),
            )
    for ordinal, cap in enumerate(output_caps):
        if cap is None:
            continue

        def transform(
            result: subprocess.CompletedProcess[bytes], cap: int = cap
        ) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(
                result.args, result.returncode, b"x" * (cap + 1), result.stderr
            )

        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            transform,
            finding("git", "ACP.GIT.STDOUT_BYTES", roles[ordinal]),
        )
    for ordinal, cap in enumerate(output_caps):
        hostile_stdout = None if ordinal == 1 else b"x" * ((cap or 0) + 1)
        for unsupported_returncode in (-1, 2, 127):
            assert_injected_git_failure(
                root,
                freeze,
                monkeypatch,
                ordinal,
                lambda result, hostile_stdout=hostile_stdout, unsupported_returncode=unsupported_returncode: (
                    subprocess.CompletedProcess(
                        result.args, unsupported_returncode, hostile_stdout, result.stderr
                    )
                ),
                finding("git", "ACP.GIT.RETURN_CODE", roles[ordinal]),
            )
    for ordinal, returncode, code, location in (
        (1, 1, "ACP.FREEZE.OBJECT_DB_INTEGRITY", "object-db"),
        (3, 128, "ACP.FREEZE.RED_HEAD_MISSING", "redHead"),
        (5, 1, "ACP.FREEZE.RED_NOT_C3_PARENT", "redHead"),
        (8, 1, "ACP.FREEZE.C3_SCOPE", FREEZE_PATH),
        (9, 0, "ACP.FREEZE.C3_FREEZE_UNCHANGED", FREEZE_PATH),
    ):
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            lambda result, returncode=returncode, ordinal=ordinal: subprocess.CompletedProcess(
                result.args,
                returncode,
                None if ordinal == 1 else b"x" * 400,
                result.stderr,
            ),
            finding("freeze", code, location),
        )
    head = git(root, "rev-parse", "HEAD")
    red_head = freeze["redHead"]
    c3_head = git(root, "rev-list", "--reverse", f"{red_head}..{head}").splitlines()[0]
    boundary_rows = [f"{c3_head} {red_head}\n".encode()]
    prior = c3_head
    for value in range(2, 65):
        child = head if value == 64 else f"{value:040x}"
        boundary_rows.append(f"{child} {prior}\n".encode())
        prior = child
    exact_cap_payloads = (
        (0, b"sha1\n", None),
        (2, head.encode() + b"\n", None),
        (3, b"commit\n", None),
        (4, b"65536\n", None),
        (6, b"f" * 40 + b"\n", ("freeze", "ACP.FREEZE.HISTORY_MERGE", "HEAD")),
        (7, b"".join(boundary_rows), None),
        (
            10,
            b"f" * 40 + b"\n" + b"e" * 40 + b"\n" + b"d" * 40 + b"\n" + b"c" * 40 + b"\n",
            ("freeze", "ACP.FREEZE.RED_TREE_MISMATCH", "redTree"),
        ),
    )
    for ordinal, payload, terminal in exact_cap_payloads:
        expected_terminal = () if terminal is None else finding(*terminal)

        def transform(
            result: subprocess.CompletedProcess[bytes], payload: bytes = payload
        ) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(
                result.args, result.returncode, payload, result.stderr
            )

        if terminal is None:
            assert_scripted_git_failure(
                root,
                freeze,
                monkeypatch,
                {
                    ordinal: transform,
                    13: lambda result: subprocess.CompletedProcess(
                        result.args,
                        result.returncode,
                        b"implementation@example.com\n",
                        result.stderr,
                    ),
                },
                14,
                (),
            )
        else:
            assert_injected_git_failure(
                root, freeze, monkeypatch, ordinal, transform, expected_terminal
            )
    for author_payload, expected in (
        (
            (b"a" * 317) + b"@b\n",
            finding("freeze", "ACP.FREEZE.AUTHOR_MISMATCH", "implementationAuthor"),
        ),
        (b"a" * 318 + b"@b\n", finding("git", "ACP.GIT.STDOUT_BYTES", "red_author")),
    ):
        assert_scripted_git_failure(
            root,
            freeze,
            monkeypatch,
            {
                4: lambda result: subprocess.CompletedProcess(
                    result.args, result.returncode, b"320\n", result.stderr
                ),
                13: lambda result, author_payload=author_payload: subprocess.CompletedProcess(
                    result.args, result.returncode, author_payload, result.stderr
                ),
            },
            14,
            expected,
        )
    assert_scripted_git_failure(
        root,
        freeze,
        monkeypatch,
        {
            11: lambda result: subprocess.CompletedProcess(
                result.args, result.returncode, b"32768\n", result.stderr
            ),
            12: lambda result: subprocess.CompletedProcess(
                result.args, result.returncode, b"x" * 32768, result.stderr
            ),
        },
        14,
        finding("freeze", "ACP.FREEZE.C3_IMMUTABLE", FREEZE_PATH),
    )
    for ordinal in (0, 2, 3, 4, 6, 7, 10, 11, 13):

        def transform(
            result: subprocess.CompletedProcess[bytes],
        ) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(
                result.args, result.returncode, b"\xff", result.stderr
            )

        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            transform,
            finding("git", "ACP.GIT.UTF8", roles[ordinal]),
        )
    malformed_outputs = (
        (0, b"sha2\n", "ACP.FREEZE.OBJECT_FORMAT", "objectFormat"),
        (0, b"sha1", "ACP.GIT.OUTPUT_LINES", "object_format"),
        (0, b"sh\r\n", "ACP.GIT.OUTPUT_TOKEN", "object_format"),
        (2, b"A" * 40 + b"\n", "ACP.GIT.OUTPUT_TOKEN", "head"),
        (2, b"0" * 40, "ACP.GIT.OUTPUT_LINES", "head"),
        (2, b"0" * 39 + b"\r\n", "ACP.GIT.OUTPUT_TOKEN", "head"),
        (3, b"blob\n", "ACP.FREEZE.RED_HEAD_NOT_COMMIT", "redHead"),
        (3, b"commit", "ACP.GIT.OUTPUT_LINES", "red_type"),
        (3, b"comm\r\n", "ACP.GIT.OUTPUT_TOKEN", "red_type"),
        (4, b"01\n", "ACP.GIT.OUTPUT_TOKEN", "red_size"),
        (4, b"1", "ACP.GIT.OUTPUT_LINES", "red_size"),
        (4, b"1\r\n", "ACP.GIT.OUTPUT_TOKEN", "red_size"),
        (4, b"1\n2\n", "ACP.GIT.OUTPUT_LINES", "red_size"),
        (6, b"0" * 40 + b"\n", "ACP.FREEZE.HISTORY_MERGE", "HEAD"),
        (6, b"0" * 40, "ACP.GIT.OUTPUT_LINES", "merge_scan"),
        (6, b"0" * 39 + b"\r\n", "ACP.GIT.OUTPUT_TOKEN", "merge_scan"),
        (7, b"1" * 40 + b" " + b"2" * 40, "ACP.GIT.OUTPUT_LINES", "ancestry_chain"),
        (
            7,
            b"1" * 40 + b"  " + b"2" * 40 + b"\n",
            "ACP.GIT.OUTPUT_TOKEN",
            "ancestry_chain",
        ),
        (
            7,
            b"1" * 40 + b" " + b"2" * 40 + b"\r\n",
            "ACP.GIT.OUTPUT_TOKEN",
            "ancestry_chain",
        ),
        (7, b"", "ACP.FREEZE.C3_MISSING", "redHead"),
        (10, b"0" * 40 + b"\n", "ACP.GIT.OUTPUT_LINES", "red_objects"),
        (10, (b"0" * 40 + b"\n") * 3 + b"0" * 40, "ACP.GIT.OUTPUT_LINES", "red_objects"),
        (
            10,
            (b"0" * 40 + b"\n") * 3 + b"A" * 40 + b"\n",
            "ACP.GIT.OUTPUT_TOKEN",
            "red_objects",
        ),
        (11, b"0\n", "ACP.GIT.OUTPUT_TOKEN", "c3_freeze_size"),
        (11, b"1", "ACP.GIT.OUTPUT_LINES", "c3_freeze_size"),
        (11, b"1\r\n", "ACP.GIT.OUTPUT_TOKEN", "c3_freeze_size"),
        (11, b"1\n2\n", "ACP.GIT.OUTPUT_LINES", "c3_freeze_size"),
        (13, b"@invalid\n", "ACP.GIT.OUTPUT_TOKEN", "red_author"),
    )
    for ordinal, payload, code, location in malformed_outputs:

        def transform(
            result: subprocess.CompletedProcess[bytes], payload: bytes = payload
        ) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(
                result.args, result.returncode, payload, result.stderr
            )

        assert_injected_git_failure(
            root, freeze, monkeypatch, ordinal, transform, finding("git", code, location)
        )
    for payload, code in (
        (b"implementation@example.com", "ACP.GIT.OUTPUT_LINES"),
        (b"implementation@example.com\r\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b" implementation@example.com\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation@example.com \n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation\x00@example.com\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation\t@example.com\n", "ACP.GIT.OUTPUT_TOKEN"),
        ("implementation\u00a0@example.com\n".encode(), "ACP.GIT.OUTPUT_TOKEN"),
        ("implémentation@example.com\n".encode(), "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation.example.com\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation@@example.com\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"@example.com\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation@\n", "ACP.GIT.OUTPUT_TOKEN"),
        (b"implementation@example.com\nextra\n", "ACP.GIT.OUTPUT_LINES"),
    ):
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            13,
            lambda result, payload=payload: subprocess.CompletedProcess(
                result.args, result.returncode, payload, result.stderr
            ),
            finding("git", code, "red_author"),
        )
    ancestry_rows: list[bytes] = []
    parent = freeze["redHead"]
    for value in range(1, 66):
        child = f"{value:040x}"
        ancestry_rows.append(f"{child} {parent}\n".encode())
        parent = child
    assert_injected_git_failure(
        root,
        freeze,
        monkeypatch,
        7,
        lambda result: subprocess.CompletedProcess(
            result.args, result.returncode, b"".join(ancestry_rows), result.stderr
        ),
        finding("freeze", "ACP.FREEZE.HISTORY_LIMIT", "redHead..HEAD"),
    )
    valid_chain = [
        f"{c3_head} {red_head}\n".encode(),
        f"{head} {c3_head}\n".encode(),
    ]
    ancestry_mutations = (
        ([f"{c3_head} {'f' * 40}\n".encode(), valid_chain[1]], "ancestry[0].parent"),
        ([valid_chain[0], f"{head} {'e' * 40}\n".encode()], "ancestry[1].parent"),
        ([valid_chain[0], f"{'b' * 40} {red_head}\n".encode()], "ancestry[1].parent"),
        ([valid_chain[0], valid_chain[0]], "ancestry[1].child"),
        ([valid_chain[1], valid_chain[0]], "ancestry[0].parent"),
        ([valid_chain[0], f"{c3_head} {c3_head}\n".encode()], "ancestry[1].child"),
        ([f"{c3_head} {red_head} {'d' * 40}\n".encode()], "ancestry[0]"),
        ([valid_chain[0], f"{'c' * 40} {c3_head}\n".encode()], "HEAD"),
    )
    for rows, location in ancestry_mutations:
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            7,
            lambda result, rows=rows: subprocess.CompletedProcess(
                result.args, result.returncode, b"".join(rows), result.stderr
            ),
            finding("freeze", "ACP.FREEZE.HISTORY_CHAIN", location),
        )
    for ordinal, returncode, code, location in (
        (8, 1, "ACP.FREEZE.C3_SCOPE", FREEZE_PATH),
        (9, 0, "ACP.FREEZE.C3_FREEZE_UNCHANGED", FREEZE_PATH),
    ):
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            lambda result, returncode=returncode: subprocess.CompletedProcess(
                result.args, returncode, b"", result.stderr
            ),
            finding("freeze", code, location),
        )
    assert_injected_git_failure(
        root,
        freeze,
        monkeypatch,
        10,
        lambda result: subprocess.CompletedProcess(
            result.args,
            result.returncode,
            b"".join(result.stdout.splitlines(keepends=True)[1::-1])
            + b"".join(result.stdout.splitlines(keepends=True)[2:]),
            result.stderr,
        ),
        finding("freeze", "ACP.FREEZE.RED_TREE_MISMATCH", "redTree"),
    )
    bundle = tuple(
        line + b"\n"
        for line in REAL_SUBPROCESS_RUN(
            expected_git_argv(root, freeze)[10],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=False,
            timeout=5,
            env=expected_git_environment(root),
        ).stdout.split(b"\n")[:-1]
    )
    for count in (0, 1, 3, 5):
        payload = b"".join(bundle[:count]) + (b"0" * 40 + b"\n") * max(0, count - 4)
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            10,
            lambda result, payload=payload: subprocess.CompletedProcess(
                result.args, result.returncode, payload, result.stderr
            ),
            finding(
                "git",
                "ACP.GIT.STDOUT_BYTES" if count == 5 else "ACP.GIT.OUTPUT_LINES",
                "red_objects",
            ),
        )
    bundle_locations = (
        "redTree",
        "matrixBlobOid",
        "focusedOracleBlobs[0].blobOid",
        "focusedOracleBlobs[1].blobOid",
    )
    for first in range(4):
        substituted = list(bundle)
        substituted[first] = (f"{first + 10:040x}\n").encode()
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            10,
            lambda result, substituted=substituted: subprocess.CompletedProcess(
                result.args, result.returncode, b"".join(substituted), result.stderr
            ),
            finding(
                "freeze",
                (
                    "ACP.FREEZE.RED_TREE_MISMATCH"
                    if first == 0
                    else "ACP.FREEZE.MATRIX_BLOB_MISMATCH"
                    if first == 1
                    else "ACP.FREEZE.ORACLE_BLOB_MISMATCH"
                ),
                bundle_locations[first],
            ),
        )
    for first in range(4):
        for second in range(first + 1, 4):
            swapped = list(bundle)
            swapped[first], swapped[second] = swapped[second], swapped[first]
            assert_injected_git_failure(
                root,
                freeze,
                monkeypatch,
                10,
                lambda result, swapped=swapped: subprocess.CompletedProcess(
                    result.args, result.returncode, b"".join(swapped), result.stderr
                ),
                finding(
                    "freeze",
                    (
                        "ACP.FREEZE.RED_TREE_MISMATCH"
                        if first == 0
                        else "ACP.FREEZE.MATRIX_BLOB_MISMATCH"
                        if first == 1
                        else "ACP.FREEZE.ORACLE_BLOB_MISMATCH"
                    ),
                    bundle_locations[first],
                ),
            )
    assert_scripted_git_failure(
        root,
        freeze,
        monkeypatch,
        {
            11: lambda result: subprocess.CompletedProcess(
                result.args, result.returncode, b"1\n", result.stderr
            )
        },
        13,
        finding("git", "ACP.GIT.SIZE_MISMATCH", "c3_freeze_payload"),
    )
    assert_scripted_git_failure(
        root,
        freeze,
        monkeypatch,
        {
            4: lambda result: subprocess.CompletedProcess(
                result.args, result.returncode, b"5\n", result.stderr
            )
        },
        14,
        finding("git", "ACP.GIT.STDOUT_BYTES", "red_author"),
    )
    for ordinal, payload, location in (
        (4, b"65537\n", "red_size"),
        (11, b"32769\n", "c3_freeze_size"),
    ):
        assert_injected_git_failure(
            root,
            freeze,
            monkeypatch,
            ordinal,
            lambda result, payload=payload: subprocess.CompletedProcess(
                result.args, result.returncode, payload, result.stderr
            ),
            finding("git", "ACP.GIT.SIZE_MISMATCH", location),
        )
    for author_payload, expected in (
        (
            (b"a" * 21) + b"@x\n",
            finding("freeze", "ACP.FREEZE.AUTHOR_MISMATCH", "implementationAuthor"),
        ),
        (b"a" * 22 + b"@x\n", finding("git", "ACP.GIT.STDOUT_BYTES", "red_author")),
    ):
        assert_scripted_git_failure(
            root,
            freeze,
            monkeypatch,
            {
                4: lambda result: subprocess.CompletedProcess(
                    result.args, result.returncode, b"24\n", result.stderr
                ),
                13: lambda result, author_payload=author_payload: subprocess.CompletedProcess(
                    result.args, result.returncode, author_payload, result.stderr
                ),
            },
            14,
            expected,
        )
    corrupt_root, corrupt_freeze = create_real_git_freeze(tmp_path / "corrupt-object")
    matrix_oid = corrupt_freeze["matrixBlobOid"]
    corrupt_object = corrupt_root / ".git/objects" / matrix_oid[:2] / matrix_oid[2:]
    corrupt_payload = b"substituted object bytes"
    corrupt_object.write_bytes(
        zlib.compress(f"blob {len(corrupt_payload)}\0".encode() + corrupt_payload)
    )
    assert protocol.validate_repository_freeze(corrupt_root) == finding(
        "freeze", "ACP.FREEZE.OBJECT_DB_INTEGRITY", "object-db"
    )
    for relative in (
        "info/grafts",
        "shallow",
        "objects/info/alternates",
        "objects/info/http-alternates",
    ):
        metadata_root, _ = create_real_git_freeze(
            tmp_path / f"metadata-{relative.replace('/', '-')}"
        )
        metadata_path = metadata_root / ".git" / relative
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text("forbidden\n", encoding="utf-8")
        assert protocol.discover_git_repository(metadata_root).findings == finding(
            "git-metadata", "ACP.GIT_METADATA.PROHIBITED", relative
        )
    linked_source, linked_freeze = create_real_git_freeze(tmp_path / "linked-source")
    linked_root = tmp_path / "linked-worktree"
    git(linked_source, "worktree", "add", "--detach", linked_root.as_posix(), "HEAD")
    linked_git_dir = Path(git(linked_root, "rev-parse", "--path-format=absolute", "--git-dir"))
    linked_common_dir = Path(
        git(linked_root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    )
    execute_metadata_success_case(
        "linked-positive",
        linked_root,
        protocol.GitDiscoveryResult(
            protocol.GitRepositoryBinding(linked_root, linked_git_dir, linked_common_dir),
            (),
        ),
    )
    assert protocol.validate_repository_freeze(linked_root) == ()
    assert_exact_git_transcript(linked_root, linked_freeze, monkeypatch)
    linked_descendant_root, linked_descendant_freeze, _, _ = create_linked_git_freeze(
        tmp_path / "linked-descendants", descendant_commits=2
    )
    assert_exact_git_transcript(linked_descendant_root, linked_descendant_freeze, monkeypatch)
    redirected = tmp_path / "redirected-root"
    redirected.mkdir()
    alternate, _ = create_real_git_freeze(tmp_path / "alternate-repository")
    (redirected / ".git").write_text(
        f"gitdir: {(alternate / '.git').as_posix()}\n", encoding="utf-8"
    )
    assert protocol.discover_git_repository(redirected).findings == finding(
        "git-metadata", "ACP.GIT_METADATA.LAYOUT", ".git.gitdir"
    )
    execute_metadata_case(
        "linked-layout-outside",
        redirected,
        finding("git-metadata", "ACP.GIT_METADATA.LAYOUT", ".git.gitdir"),
    )
    execute_metadata_case(
        "root-nonabsolute",
        Path("relative-repository-root"),
        finding("git-metadata", "ACP.GIT_METADATA.NONABSOLUTE", "root"),
    )
    execute_metadata_case(
        "root-dotdot",
        tmp_path / ".." / tmp_path.name,
        finding("git-metadata", "ACP.GIT_METADATA.NONABSOLUTE", "root"),
    )
    root_text = root.as_posix()
    execute_metadata_case(
        "root-dot",
        f"{root.parent.as_posix()}/./{root.name}",
        finding("git-metadata", "ACP.GIT_METADATA.NONABSOLUTE", "root"),
    )
    execute_metadata_case(
        "root-repeated-separator",
        f"{root.parent.as_posix()}//{root.name}",
        finding("git-metadata", "ACP.GIT_METADATA.NONABSOLUTE", "root"),
    )
    execute_metadata_case(
        "root-trailing-separator",
        f"{root_text}/",
        finding("git-metadata", "ACP.GIT_METADATA.NONABSOLUTE", "root"),
    )
    physical_root, _ = create_real_git_freeze(tmp_path / "root-symlink-physical")
    lexical_root = tmp_path / "root-symlink"
    lexical_root.symlink_to(physical_root, target_is_directory=True)
    execute_metadata_case(
        "root-symlink",
        lexical_root,
        finding("git-metadata", "ACP.GIT_METADATA.ANCESTOR_SYMLINK", "root"),
        "conventional",
    )
    linked_physical_root, _, _, _ = create_linked_git_freeze(
        tmp_path / "root-symlink-linked-physical"
    )
    linked_lexical_root = tmp_path / "root-symlink-linked"
    linked_lexical_root.symlink_to(linked_physical_root, target_is_directory=True)
    execute_metadata_case(
        "root-symlink",
        linked_lexical_root,
        finding("git-metadata", "ACP.GIT_METADATA.ANCESTOR_SYMLINK", "root"),
        "linked",
    )
    physical_container = tmp_path / "pre-root-physical"
    nested_root, _ = create_real_git_freeze(physical_container / "nested")
    lexical_container = tmp_path / "pre-root-symlink"
    lexical_container.symlink_to(physical_container, target_is_directory=True)
    lexical_nested_root = lexical_container / nested_root.relative_to(physical_container)
    execute_metadata_case(
        "pre-root-symlink",
        lexical_nested_root,
        finding("git-metadata", "ACP.GIT_METADATA.ANCESTOR_SYMLINK", "root"),
        "conventional",
    )
    linked_pre_physical = tmp_path / "pre-root-linked-physical"
    linked_pre_root, _, _, _ = create_linked_git_freeze(linked_pre_physical)
    linked_pre_lexical = tmp_path / "pre-root-linked-symlink"
    linked_pre_lexical.symlink_to(linked_pre_physical, target_is_directory=True)
    linked_pre_nested_root = linked_pre_lexical / linked_pre_root.relative_to(linked_pre_physical)
    execute_metadata_case(
        "pre-root-symlink",
        linked_pre_nested_root,
        finding("git-metadata", "ACP.GIT_METADATA.ANCESTOR_SYMLINK", "root"),
        "linked",
    )
    replacement_io = protocol.SYSTEM_METADATA_IO
    replacement_root, _ = create_real_git_freeze(tmp_path / "root-replacement-repository")
    replacement_shadow = replacement_root.with_name(f"{replacement_root.name}-original")
    replacement_done = False

    def replace_root_after_lstat(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal replacement_done
        before = replacement_io.lstat(path, dir_fd=dir_fd)
        if path == replacement_root.name and not replacement_done:
            replacement_root.rename(replacement_shadow)
            replacement_root.symlink_to(replacement_shadow, target_is_directory=True)
            replacement_done = True
        return before

    execute_metadata_io_case(
        "root-replacement",
        replacement_root,
        protocol.MetadataIO(
            replace_root_after_lstat,
            replacement_io.open,
            replacement_io.fstat,
            replacement_io.read,
            replacement_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "root"),
        "conventional",
    )
    linked_replacement_root, _, _, _ = create_linked_git_freeze(
        tmp_path / "root-replacement-linked"
    )
    linked_replacement_shadow = linked_replacement_root.with_name(
        f"{linked_replacement_root.name}-original"
    )
    linked_replacement_done = False

    def replace_linked_root_after_lstat(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal linked_replacement_done
        before = replacement_io.lstat(path, dir_fd=dir_fd)
        if path == linked_replacement_root.name and not linked_replacement_done:
            linked_replacement_root.rename(linked_replacement_shadow)
            linked_replacement_root.symlink_to(linked_replacement_shadow, target_is_directory=True)
            linked_replacement_done = True
        return before

    execute_metadata_io_case(
        "root-replacement",
        linked_replacement_root,
        protocol.MetadataIO(
            replace_linked_root_after_lstat,
            replacement_io.open,
            replacement_io.fstat,
            replacement_io.read,
            replacement_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "root"),
        "linked",
    )
    pre_replacement_container = tmp_path / "pre-root-replacement-container"
    pre_replacement_root, _ = create_real_git_freeze(pre_replacement_container / "repository")
    pre_replacement_shadow = pre_replacement_container.with_name(
        f"{pre_replacement_container.name}-original"
    )
    pre_replacement_done = False

    def replace_pre_root_after_lstat(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal pre_replacement_done
        before = replacement_io.lstat(path, dir_fd=dir_fd)
        if path == pre_replacement_container.name and not pre_replacement_done:
            pre_replacement_container.rename(pre_replacement_shadow)
            pre_replacement_container.symlink_to(pre_replacement_shadow, target_is_directory=True)
            pre_replacement_done = True
        return before

    execute_metadata_io_case(
        "pre-root-replacement",
        pre_replacement_root,
        protocol.MetadataIO(
            replace_pre_root_after_lstat,
            replacement_io.open,
            replacement_io.fstat,
            replacement_io.read,
            replacement_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "root"),
        "conventional",
    )
    linked_pre_replacement_container = tmp_path / "pre-root-linked-replacement-container"
    linked_pre_replacement_root, _, _, _ = create_linked_git_freeze(
        linked_pre_replacement_container
    )
    linked_pre_replacement_shadow = linked_pre_replacement_container.with_name(
        f"{linked_pre_replacement_container.name}-original"
    )
    linked_pre_replacement_done = False

    def replace_linked_pre_root_after_lstat(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal linked_pre_replacement_done
        before = replacement_io.lstat(path, dir_fd=dir_fd)
        if path == linked_pre_replacement_container.name and not linked_pre_replacement_done:
            linked_pre_replacement_container.rename(linked_pre_replacement_shadow)
            linked_pre_replacement_container.symlink_to(
                linked_pre_replacement_shadow, target_is_directory=True
            )
            linked_pre_replacement_done = True
        return before

    execute_metadata_io_case(
        "pre-root-replacement",
        linked_pre_replacement_root,
        protocol.MetadataIO(
            replace_linked_pre_root_after_lstat,
            replacement_io.open,
            replacement_io.fstat,
            replacement_io.read,
            replacement_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "root"),
        "linked",
    )
    ancestor_replacement_root, _ = create_real_git_freeze(
        tmp_path / "ancestor-replacement-repository"
    )
    ancestor_info = ancestor_replacement_root / ".git/info"
    ancestor_info.mkdir(exist_ok=True)
    ancestor_shadow = ancestor_info.with_name("info-original")
    ancestor_replacement_done = False

    def replace_ancestor_after_public_lstat(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal ancestor_replacement_done
        before = replacement_io.lstat(path, dir_fd=dir_fd)
        if path == "info" and not ancestor_replacement_done:
            ancestor_info.rename(ancestor_shadow)
            ancestor_info.symlink_to(ancestor_shadow, target_is_directory=True)
            ancestor_replacement_done = True
        return before

    execute_metadata_io_case(
        "ancestor-replacement",
        ancestor_replacement_root,
        protocol.MetadataIO(
            replace_ancestor_after_public_lstat,
            replacement_io.open,
            replacement_io.fstat,
            replacement_io.read,
            replacement_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "info"),
        "conventional",
    )
    linked_ancestor_root, _, _, linked_ancestor_common = create_linked_git_freeze(
        tmp_path / "ancestor-replacement-linked"
    )
    linked_ancestor_info = linked_ancestor_common / "info"
    linked_ancestor_info.mkdir(exist_ok=True)
    linked_ancestor_shadow = linked_ancestor_info.with_name("info-original")
    linked_ancestor_done = False

    def replace_linked_ancestor_after_lstat(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal linked_ancestor_done
        before = replacement_io.lstat(path, dir_fd=dir_fd)
        if path == "info" and not linked_ancestor_done:
            linked_ancestor_info.rename(linked_ancestor_shadow)
            linked_ancestor_info.symlink_to(linked_ancestor_shadow, target_is_directory=True)
            linked_ancestor_done = True
        return before

    execute_metadata_io_case(
        "ancestor-replacement",
        linked_ancestor_root,
        protocol.MetadataIO(
            replace_linked_ancestor_after_lstat,
            replacement_io.open,
            replacement_io.fstat,
            replacement_io.read,
            replacement_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "info"),
        "linked",
    )
    between_conventional_root, _ = create_real_git_freeze(tmp_path / "between-read-conventional")
    between_conventional_original = between_conventional_root / ".git-original"

    def replace_conventional_dot_git() -> None:
        (between_conventional_root / ".git").rename(between_conventional_original)
        (between_conventional_root / ".git").mkdir()

    execute_between_read_case(
        "between-read-conventional-dot-git",
        between_conventional_root,
        "dot_git",
        replace_conventional_dot_git,
    )
    between_linked_root, _, between_linked_git_dir, _ = create_linked_git_freeze(
        tmp_path / "between-read-linked"
    )
    between_linked_original = between_linked_git_dir.with_name(
        f"{between_linked_git_dir.name}-original"
    )

    def replace_linked_directory() -> None:
        between_linked_git_dir.rename(between_linked_original)
        between_linked_git_dir.mkdir()

    execute_between_read_case(
        "between-read-linked-directory",
        between_linked_root,
        "linked_git_dir",
        replace_linked_directory,
    )
    before_common_root, _, _, before_common_dir = create_linked_git_freeze(
        tmp_path / "between-commondir-and-common"
    )
    before_common_original = before_common_dir.with_name(f"{before_common_dir.name}-original")

    def replace_before_common_read() -> None:
        before_common_dir.rename(before_common_original)
        before_common_dir.mkdir()

    execute_between_read_case(
        "between-read-linked-common-directory",
        before_common_root,
        "commondir",
        replace_before_common_read,
    )
    between_common_root, _, _, between_common_dir = create_linked_git_freeze(
        tmp_path / "between-read-common"
    )
    between_common_original = between_common_dir.with_name(f"{between_common_dir.name}-original")

    def replace_common_directory() -> None:
        between_common_dir.rename(between_common_original)
        between_common_dir.mkdir()

    execute_between_read_case(
        "between-read-common-directory",
        between_common_root,
        "common_dir",
        replace_common_directory,
    )
    final_revalidation_root, _ = create_real_git_freeze(tmp_path / "final-binding-revalidation")
    final_revalidation_original = final_revalidation_root / ".git-original"

    def replace_before_final_revalidation() -> None:
        (final_revalidation_root / ".git").rename(final_revalidation_original)
        (final_revalidation_root / ".git").mkdir()

    execute_between_read_case(
        "final-binding-revalidation",
        final_revalidation_root,
        "prohibited_http_alternates",
        replace_before_final_revalidation,
    )
    dot_git_cases: tuple[tuple[str, str, bytes | None, str, str], ...] = (
        ("missing", "missing", None, "ACP.GIT_METADATA.MISSING", ".git"),
        ("target-symlink", "symlink", None, "ACP.GIT_METADATA.TARGET_SYMLINK", ".git"),
        ("fifo", "fifo", None, "ACP.GIT_METADATA.WRONG_TYPE", ".git"),
        (
            "cap-n-malformed",
            "bytes",
            (b"x" * 4095) + b"\n",
            "ACP.GIT_METADATA.RECORD_SHAPE",
            ".git",
        ),
        ("cap-n-plus-one", "bytes", b"x" * 4097, "ACP.GIT_METADATA.BYTE_CAP", ".git"),
        (
            "invalid-utf8",
            "bytes",
            b"gitdir: \xff\n",
            "ACP.GIT_METADATA.INVALID_UTF8",
            ".git",
        ),
        ("missing-lf", "bytes", b"gitdir: /absolute", "ACP.GIT_METADATA.LINE_COUNT", ".git"),
        ("crlf", "bytes", b"gitdir: /absolute\r\n", "ACP.GIT_METADATA.RECORD_SHAPE", ".git"),
        ("extra-lf", "bytes", b"gitdir: /absolute\n\n", "ACP.GIT_METADATA.LINE_COUNT", ".git"),
        (
            "extra-record",
            "bytes",
            b"gitdir: /one\ngitdir: /two\n",
            "ACP.GIT_METADATA.LINE_COUNT",
            ".git",
        ),
        ("relative", "bytes", b"gitdir: relative\n", "ACP.GIT_METADATA.NONABSOLUTE", ".git.gitdir"),
        (
            "dot-component",
            "bytes",
            b"gitdir: /repo/./worktrees/name\n",
            "ACP.GIT_METADATA.CONTAINMENT",
            ".git.gitdir",
        ),
        (
            "dotdot-component",
            "bytes",
            b"gitdir: /repo/../worktrees/name\n",
            "ACP.GIT_METADATA.CONTAINMENT",
            ".git.gitdir",
        ),
        (
            "empty-component",
            "bytes",
            b"gitdir: /repo//worktrees/name\n",
            "ACP.GIT_METADATA.CONTAINMENT",
            ".git.gitdir",
        ),
        (
            "nul",
            "bytes",
            b"gitdir: /repo/worktrees/na\x00me\n",
            "ACP.GIT_METADATA.CONTAINMENT",
            ".git.gitdir",
        ),
        (
            "degenerate-common-root",
            "bytes",
            b"gitdir: /worktrees/name\n",
            "ACP.GIT_METADATA.LAYOUT",
            ".git.gitdir",
        ),
    )
    for name, mode, metadata_payload, code, location in dot_git_cases:
        metadata_root, _ = create_real_git_freeze(tmp_path / f"dot-git-{name}")
        dot_git = metadata_root / ".git"
        preserved_git = metadata_root / ".git-preserved"
        dot_git.rename(preserved_git)
        if mode == "symlink":
            dot_git.symlink_to(preserved_git, target_is_directory=True)
        elif mode == "fifo":
            os.mkfifo(dot_git)
        elif mode == "bytes":
            assert metadata_payload is not None
            dot_git.write_bytes(metadata_payload)
        execute_metadata_case(
            f"dot-git-{name}",
            metadata_root,
            finding("git-metadata", code, location),
        )
    public_race_root, _ = create_real_git_freeze(tmp_path / "public-leaf-race")
    public_dot_git = public_race_root / ".git"
    public_shadow = public_race_root / ".git-original"
    public_replaced = False
    system_io = protocol.SYSTEM_METADATA_IO

    def public_leaf_replacement(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        nonlocal public_replaced
        before = system_io.lstat(path, dir_fd=dir_fd)
        if path == ".git" and not public_replaced:
            public_dot_git.rename(public_shadow)
            public_dot_git.symlink_to(public_shadow, target_is_directory=True)
            public_replaced = True
        return before

    execute_metadata_io_case(
        "leaf-replacement",
        public_race_root,
        protocol.MetadataIO(
            public_leaf_replacement,
            system_io.open,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", ".git"),
        "conventional",
    )
    linked_leaf_root, _, _, _ = create_linked_git_freeze(tmp_path / "public-leaf-race-linked")
    linked_leaf_record = linked_leaf_root / ".git"
    linked_leaf_original = linked_leaf_root / ".git-original"
    linked_leaf_replaced = False

    def public_linked_leaf_replacement(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal linked_leaf_replaced
        before = system_io.lstat(path, dir_fd=dir_fd)
        if path == ".git" and not linked_leaf_replaced:
            linked_leaf_record.rename(linked_leaf_original)
            linked_leaf_record.symlink_to(linked_leaf_original)
            linked_leaf_replaced = True
        return before

    execute_metadata_io_case(
        "leaf-replacement",
        linked_leaf_root,
        protocol.MetadataIO(
            public_linked_leaf_replacement,
            system_io.open,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", ".git"),
        "linked",
    )
    for operational_mode in ("conventional", "linked"):
        for case_id, stat_index, stat_value, expected_code in (
            ("fstat-device", 2, -1, "ACP.GIT_METADATA.IDENTITY_CHANGED"),
            ("fstat-inode", 1, -1, "ACP.GIT_METADATA.IDENTITY_CHANGED"),
            ("fstat-type", 0, 0, "ACP.GIT_METADATA.WRONG_TYPE"),
        ):
            case_base = tmp_path / f"public-{operational_mode}-{case_id}"
            if operational_mode == "conventional":
                fstat_root, _ = create_real_git_freeze(case_base)
            else:
                fstat_root, _, _, _ = create_linked_git_freeze(case_base)
            final_descriptors: set[int] = set()

            def fstat_open(
                path: str,
                flags: int,
                *,
                dir_fd: int | None = None,
            ) -> int:
                descriptor = system_io.open(path, flags, dir_fd=dir_fd)
                if path == ".git":
                    final_descriptors.add(descriptor)
                return descriptor

            def changed_fstat(descriptor: int) -> os.stat_result:
                result = system_io.fstat(descriptor)
                if descriptor not in final_descriptors:
                    return result
                values = list(result)
                values[stat_index] = stat_value
                return os.stat_result(values)

            execute_metadata_io_case(
                case_id,
                fstat_root,
                protocol.MetadataIO(
                    system_io.lstat,
                    fstat_open,
                    changed_fstat,
                    system_io.read,
                    system_io.close,
                ),
                finding("git-metadata", expected_code, ".git"),
                operational_mode,
            )
    for case_id, stat_index, stat_value, expected_code in (
        ("post-read-device", 2, -1, "ACP.GIT_METADATA.IDENTITY_CHANGED"),
        ("post-read-inode", 1, -1, "ACP.GIT_METADATA.IDENTITY_CHANGED"),
        ("post-read-type", 0, 0, "ACP.GIT_METADATA.WRONG_TYPE"),
    ):
        post_root, _, _, _ = create_linked_git_freeze(tmp_path / f"public-{case_id}")
        dot_git_lstats = 0

        def changed_post_lstat(
            path: str,
            *,
            dir_fd: int | None = None,
        ) -> os.stat_result:
            nonlocal dot_git_lstats
            result = system_io.lstat(path, dir_fd=dir_fd)
            if path != ".git":
                return result
            dot_git_lstats += 1
            if dot_git_lstats == 1:
                return result
            values = list(result)
            values[stat_index] = stat_value
            return os.stat_result(values)

        execute_metadata_io_case(
            case_id,
            post_root,
            protocol.MetadataIO(
                changed_post_lstat,
                system_io.open,
                system_io.fstat,
                system_io.read,
                system_io.close,
            ),
            finding("git-metadata", expected_code, ".git"),
        )
    read_type_root, _, _, _ = create_linked_git_freeze(tmp_path / "public-read-type")
    execute_metadata_io_case(
        "read-type",
        read_type_root,
        protocol.MetadataIO(
            system_io.lstat,
            system_io.open,
            system_io.fstat,
            lambda descriptor, count: "not-bytes",  # type: ignore[arg-type,return-value]
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.READ_TYPE", ".git"),
    )
    read_error_root, _, _, _ = create_linked_git_freeze(tmp_path / "public-read-error")
    execute_metadata_io_case(
        "read-error",
        read_error_root,
        protocol.MetadataIO(
            system_io.lstat,
            system_io.open,
            system_io.fstat,
            lambda descriptor, count: (_ for _ in ()).throw(OSError("read error")),
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
    )
    lstat_error_root, _ = create_real_git_freeze(tmp_path / "public-lstat-error")

    def public_lstat_error(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        if path == ".git":
            raise OSError("lstat error")
        return system_io.lstat(path, dir_fd=dir_fd)

    execute_metadata_io_case(
        "lstat-error",
        lstat_error_root,
        protocol.MetadataIO(
            public_lstat_error,
            system_io.open,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        "conventional",
    )
    linked_lstat_error_root, _, _, _ = create_linked_git_freeze(
        tmp_path / "public-lstat-error-linked"
    )
    execute_metadata_io_case(
        "lstat-error",
        linked_lstat_error_root,
        protocol.MetadataIO(
            public_lstat_error,
            system_io.open,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        "linked",
    )
    open_error_root, _ = create_real_git_freeze(tmp_path / "public-open-error")

    def public_open_error(
        path: str,
        flags: int,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if path == ".git":
            raise OSError("open error")
        return system_io.open(path, flags, dir_fd=dir_fd)

    execute_metadata_io_case(
        "open-error",
        open_error_root,
        protocol.MetadataIO(
            system_io.lstat,
            public_open_error,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        "conventional",
    )
    linked_open_error_root, _, _, _ = create_linked_git_freeze(
        tmp_path / "public-open-error-linked"
    )
    execute_metadata_io_case(
        "open-error",
        linked_open_error_root,
        protocol.MetadataIO(
            system_io.lstat,
            public_open_error,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        "linked",
    )
    close_error_root, _ = create_real_git_freeze(tmp_path / "public-close-error")
    close_error_seen = False
    failed_close_descriptor: int | None = None

    def public_close_error(descriptor: int) -> None:
        nonlocal close_error_seen, failed_close_descriptor
        if not close_error_seen:
            close_error_seen = True
            failed_close_descriptor = descriptor
            raise OSError("close error")
        system_io.close(descriptor)

    execute_metadata_io_case(
        "close-error",
        close_error_root,
        protocol.MetadataIO(
            system_io.lstat,
            system_io.open,
            system_io.fstat,
            system_io.read,
            public_close_error,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        "conventional",
    )
    assert failed_close_descriptor is not None
    system_io.close(failed_close_descriptor)
    linked_close_error_root, _, _, _ = create_linked_git_freeze(
        tmp_path / "public-close-error-linked"
    )
    linked_close_error_seen = False
    linked_failed_close_descriptor: int | None = None

    def public_linked_close_error(descriptor: int) -> None:
        nonlocal linked_close_error_seen, linked_failed_close_descriptor
        if not linked_close_error_seen:
            linked_close_error_seen = True
            linked_failed_close_descriptor = descriptor
            raise OSError("close error")
        system_io.close(descriptor)

    execute_metadata_io_case(
        "close-error",
        linked_close_error_root,
        protocol.MetadataIO(
            system_io.lstat,
            system_io.open,
            system_io.fstat,
            system_io.read,
            public_linked_close_error,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        "linked",
    )
    assert linked_failed_close_descriptor is not None
    system_io.close(linked_failed_close_descriptor)
    linked_record_cases = (
        ("backlink", "gitdir", "ACP.GIT_METADATA.BACKLINK_MISMATCH"),
        ("commondir", "commondir", "ACP.GIT_METADATA.COMMONDIR_MISMATCH"),
    )
    for role, filename, mismatch_code in linked_record_cases:
        linked_mutations: tuple[tuple[str, bytes | None, str], ...] = (
            ("missing", None, "ACP.GIT_METADATA.MISSING"),
            ("directory", None, "ACP.GIT_METADATA.WRONG_TYPE"),
            ("fifo", None, "ACP.GIT_METADATA.WRONG_TYPE"),
            ("symlink", None, "ACP.GIT_METADATA.TARGET_SYMLINK"),
            ("cap-n-malformed", (b"x" * 4095) + b"\n", "ACP.GIT_METADATA.RECORD_SHAPE"),
            ("cap-n-plus-one", b"x" * 4097, "ACP.GIT_METADATA.BYTE_CAP"),
            ("invalid-utf8", b"\xff\n", "ACP.GIT_METADATA.INVALID_UTF8"),
            ("missing-lf", b"wrong", "ACP.GIT_METADATA.LINE_COUNT"),
            ("extra-lf", b"wrong\n\n", "ACP.GIT_METADATA.LINE_COUNT"),
            (
                "mismatch",
                b"/wrong/root/.git\n" if role == "backlink" else b"../../..\n",
                mismatch_code,
            ),
        )
        for mutation, linked_payload, code in linked_mutations:
            linked_root, _, linked_git_dir, _ = create_linked_git_freeze(
                tmp_path / f"linked-{role}-{mutation}"
            )
            record_path = linked_git_dir / filename
            if mutation == "missing":
                record_path.unlink()
            elif mutation == "directory":
                record_path.unlink()
                record_path.mkdir()
            elif mutation == "fifo":
                record_path.unlink()
                os.mkfifo(record_path)
            elif mutation == "symlink":
                original = record_path.with_name(f"{filename}-original")
                record_path.rename(original)
                record_path.symlink_to(original)
            else:
                assert linked_payload is not None
                record_path.write_bytes(linked_payload)
            execute_metadata_case(
                f"{role}-{mutation}",
                linked_root,
                finding("git-metadata", code, f"git-dir/{filename}"),
            )
    for relative in protocol.STATIC_GIT_METADATA_TARGETS:
        case_prefix = {
            "info/grafts": "grafts",
            "shallow": "shallow",
            "objects/info/alternates": "alternates",
            "objects/info/http-alternates": "http-alternates",
        }[relative]
        for operational_mode in ("conventional", "linked"):
            for inode_kind, code in (
                ("file", "ACP.GIT_METADATA.PROHIBITED"),
                ("directory", "ACP.GIT_METADATA.PROHIBITED"),
                ("fifo", "ACP.GIT_METADATA.PROHIBITED"),
                ("live-symlink", "ACP.GIT_METADATA.TARGET_SYMLINK"),
                ("broken-symlink", "ACP.GIT_METADATA.TARGET_SYMLINK"),
            ):
                case_base = (
                    tmp_path
                    / f"prohibited-{operational_mode}-{relative.replace('/', '-')}-{inode_kind}"
                )
                if operational_mode == "conventional":
                    prohibited_root, _ = create_real_git_freeze(case_base)
                    prohibited_common = prohibited_root / ".git"
                else:
                    prohibited_root, _, _, prohibited_common = create_linked_git_freeze(case_base)
                target = prohibited_common / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if inode_kind == "file":
                    target.write_bytes(b"forbidden")
                elif inode_kind == "directory":
                    target.mkdir()
                elif inode_kind == "fifo":
                    os.mkfifo(target)
                else:
                    link_target = target.with_name(
                        "live-target" if inode_kind == "live-symlink" else "missing-target"
                    )
                    if inode_kind == "live-symlink":
                        link_target.write_bytes(b"target")
                    target.symlink_to(link_target)
                execute_metadata_case(
                    f"{case_prefix}-{inode_kind}",
                    prohibited_root,
                    finding("git-metadata", code, relative),
                    operational_mode,
                )
            if Path(relative).parent != Path("."):
                case_base = (
                    tmp_path
                    / f"prohibited-ancestor-{operational_mode}-{relative.replace('/', '-')}"
                )
                if operational_mode == "conventional":
                    ancestor_root, _ = create_real_git_freeze(case_base)
                    ancestor_common = ancestor_root / ".git"
                else:
                    ancestor_root, _, _, ancestor_common = create_linked_git_freeze(case_base)
                ancestor = ancestor_common / Path(relative).parent
                preserved_ancestor = ancestor.with_name(f"{ancestor.name}-preserved")
                ancestor.rename(preserved_ancestor)
                ancestor.symlink_to(preserved_ancestor, target_is_directory=True)
                execute_metadata_case(
                    f"{case_prefix}-ancestor-symlink",
                    ancestor_root,
                    finding(
                        "git-metadata",
                        "ACP.GIT_METADATA.ANCESTOR_SYMLINK",
                        Path(relative).parent.as_posix(),
                    ),
                    operational_mode,
                )
    linked_external_symlink_root, _, _, linked_external_symlink_common = create_linked_git_freeze(
        tmp_path / "linked-external-ancestor-symlink"
    )
    linked_external_info = linked_external_symlink_common / "objects/info"
    linked_external_info.mkdir(parents=True, exist_ok=True)
    linked_external_info_original = linked_external_info.with_name("info-original")
    linked_external_info.rename(linked_external_info_original)
    linked_external_info.symlink_to(linked_external_info_original, target_is_directory=True)
    execute_metadata_case(
        "linked-external-ancestor-symlink",
        linked_external_symlink_root,
        finding("git-metadata", "ACP.GIT_METADATA.ANCESTOR_SYMLINK", "objects/info"),
    )
    linked_external_race_root, _, _, linked_external_race_common = create_linked_git_freeze(
        tmp_path / "linked-external-ancestor-replacement"
    )
    linked_external_race_info = linked_external_race_common / "objects/info"
    linked_external_race_info.mkdir(parents=True, exist_ok=True)
    linked_external_race_original = linked_external_race_info.with_name("info-original")
    linked_external_replaced = False

    def replace_linked_external_ancestor(
        path: str,
        *,
        dir_fd: int | None = None,
    ) -> os.stat_result:
        nonlocal linked_external_replaced
        before = system_io.lstat(path, dir_fd=dir_fd)
        if path == "info" and not linked_external_replaced:
            linked_external_race_info.rename(linked_external_race_original)
            linked_external_race_info.symlink_to(
                linked_external_race_original, target_is_directory=True
            )
            linked_external_replaced = True
        return before

    execute_metadata_io_case(
        "linked-external-ancestor-replacement",
        linked_external_race_root,
        protocol.MetadataIO(
            replace_linked_external_ancestor,
            system_io.open,
            system_io.fstat,
            system_io.read,
            system_io.close,
        ),
        finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "objects/info"),
    )
    linked_symlink_root, _, linked_symlink_git_dir, _ = create_linked_git_freeze(
        tmp_path / "linked-git-dir-symlink"
    )
    preserved_linked_git_dir = linked_symlink_git_dir.with_name(
        f"{linked_symlink_git_dir.name}-preserved"
    )
    linked_symlink_git_dir.rename(preserved_linked_git_dir)
    linked_symlink_git_dir.symlink_to(preserved_linked_git_dir, target_is_directory=True)
    execute_metadata_case(
        "linked-git-dir-target-symlink",
        linked_symlink_root,
        finding("git-metadata", "ACP.GIT_METADATA.TARGET_SYMLINK", ".git.gitdir"),
    )
    sentinel_findings = finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", ".git")
    governed_sentinel = finding("file", "ACP.FILE.NONCANONICAL", "matrix")
    metadata_calls: list[tuple[Path, protocol.GitMetadataProvenance, protocol.MetadataIO]] = []
    governed_calls: list[tuple[Path, str]] = []

    def first_metadata_failure(
        called_root: Path,
        *,
        provenance: protocol.GitMetadataProvenance,
        io: protocol.MetadataIO,
    ) -> protocol.GitMetadataReadResult:
        metadata_calls.append((called_root, provenance, io))
        return protocol.GitMetadataReadResult(None, sentinel_findings)

    composition_root, _ = create_real_git_freeze(tmp_path / "metadata-composition")

    def later_governed_failure(called_root: Path, relative: str) -> protocol.GovernedReadResult:
        governed_calls.append((called_root, relative))
        return protocol.GovernedReadResult(None, governed_sentinel)

    with monkeypatch.context() as composition_patch:
        composition_patch.setattr(protocol, "_read_git_metadata_nofollow", first_metadata_failure)
        composition_patch.setattr(protocol, "_read_governed_bytes", later_governed_failure)
        composition_patch.setattr(
            PROTOCOL_SUBPROCESS,
            "run",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("Git must not run after metadata failure")
            ),
        )
        discovery = protocol.discover_git_repository(composition_root)
        assert discovery.findings is sentinel_findings
        validation_findings = protocol.validate_repository_freeze(composition_root)
        assert validation_findings is sentinel_findings
    assert governed_calls == []
    assert metadata_calls == [
        (
            composition_root,
            protocol.GitMetadataProvenance("dot_git", None),
            protocol.SYSTEM_METADATA_IO,
        ),
        (
            composition_root,
            protocol.GitMetadataProvenance("dot_git", None),
            protocol.SYSTEM_METADATA_IO,
        ),
    ]
    io_root = tmp_path / "metadata-io"
    io_root.mkdir()
    io_record = io_root / ".git"
    io_payload = b"gitdir: /absolute/path\n"
    io_record.write_bytes(io_payload)
    real_io = protocol.SYSTEM_METADATA_IO
    opened_fds: list[int] = []
    closed_fds: list[int] = []
    metadata_operations: list[tuple[Any, ...]] = []

    def tracked_lstat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        metadata_operations.append(("lstat", path, dir_fd))
        return real_io.lstat(path, dir_fd=dir_fd)

    def tracked_open(path: str, flags: int, *, dir_fd: int | None = None) -> int:
        metadata_operations.append(("open", path, flags, dir_fd))
        descriptor = real_io.open(path, flags, dir_fd=dir_fd)
        opened_fds.append(descriptor)
        return descriptor

    def tracked_fstat(file_descriptor: int) -> os.stat_result:
        metadata_operations.append(("fstat", file_descriptor))
        return real_io.fstat(file_descriptor)

    def read_one_byte(file_descriptor: int, count: int) -> bytes:
        chunk = real_io.read(file_descriptor, min(count, 1))
        metadata_operations.append(("read", file_descriptor, count, chunk))
        return chunk

    def record_close(file_descriptor: int) -> None:
        metadata_operations.append(("close", file_descriptor))
        closed_fds.append(file_descriptor)
        real_io.close(file_descriptor)

    chunked_io = protocol.MetadataIO(
        tracked_lstat,
        tracked_open,
        tracked_fstat,
        read_one_byte,
        record_close,
    )
    identity = io_record.lstat()
    expected_ancestor_records: list[protocol.GitMetadataRecord] = []
    for component_count in range(1, len(io_root.parts)):
        ancestor_path = Path(*io_root.parts[: component_count + 1])
        ancestor_identity = ancestor_path.lstat()
        expected_ancestor_records.append(
            protocol.GitMetadataRecord(
                ancestor_path,
                None,
                ancestor_identity.st_mode,
                ancestor_identity.st_dev,
                ancestor_identity.st_ino,
                tuple(expected_ancestor_records),
            )
        )
    short_roles: list[str] = []
    short_traces: list[MetadataRoleTrace] = []
    assert traced_metadata_reader(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=chunked_io,
        role_calls=short_roles,
        role_traces=short_traces,
    ) == protocol.GitMetadataReadResult(
        protocol.GitMetadataRecord(
            io_record,
            io_payload,
            identity.st_mode,
            identity.st_dev,
            identity.st_ino,
            tuple(expected_ancestor_records),
        ),
        (),
    )
    assert closed_fds == opened_fds[::-1]
    open_operations = [item for item in metadata_operations if item[0] == "open"]
    assert open_operations[0] == (
        "open",
        "/",
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        None,
    )
    for operation_index, operation in enumerate(open_operations[1:], start=1):
        assert operation[1] != io_record.as_posix()
        assert Path(operation[1]).name == operation[1]
        assert operation[3] == opened_fds[operation_index - 1]
        assert operation[2] & os.O_NOFOLLOW
        if operation_index < len(open_operations) - 1:
            assert operation[2] & os.O_DIRECTORY
        else:
            assert not operation[2] & os.O_DIRECTORY
    assert [item[1] for item in metadata_operations if item[0] == "close"] == (opened_fds[::-1])
    final_component_lstats = [item for item in metadata_operations if item[:2] == ("lstat", ".git")]
    assert len(final_component_lstats) == 2
    assert final_component_lstats[0][2] == final_component_lstats[1][2]
    assert len([item for item in metadata_operations if item[0] == "read"]) == (len(io_payload) + 1)
    finish_metadata_execution("short-read", short_roles, short_traces)
    reverse_opened: list[int] = []
    reverse_closed: list[int] = []

    def reverse_open(path: str, flags: int, *, dir_fd: int | None = None) -> int:
        descriptor = real_io.open(path, flags, dir_fd=dir_fd)
        reverse_opened.append(descriptor)
        return descriptor

    def reverse_close(file_descriptor: int) -> None:
        reverse_closed.append(file_descriptor)
        real_io.close(file_descriptor)

    reverse_roles: list[str] = []
    reverse_traces: list[MetadataRoleTrace] = []
    reverse_result = traced_metadata_reader(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=protocol.MetadataIO(
            real_io.lstat,
            reverse_open,
            real_io.fstat,
            real_io.read,
            reverse_close,
        ),
        role_calls=reverse_roles,
        role_traces=reverse_traces,
    )
    assert reverse_result.findings == ()
    assert reverse_closed == reverse_opened[::-1]
    finish_metadata_execution("reverse-close", reverse_roles, reverse_traces)
    io_record.write_bytes(b"x" * 4097)
    assert PROTOCOL_METADATA_READER(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=chunked_io,
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.BYTE_CAP", ".git")
    io_record.write_bytes(io_payload)
    close_after_error: list[int] = []

    def failing_read(file_descriptor: int, count: int) -> bytes:
        del file_descriptor, count
        raise OSError("contained metadata read failure")

    def close_after_read_error(file_descriptor: int) -> None:
        close_after_error.append(file_descriptor)
        real_io.close(file_descriptor)

    failing_io = protocol.MetadataIO(
        real_io.lstat,
        real_io.open,
        real_io.fstat,
        failing_read,
        close_after_read_error,
    )
    assert PROTOCOL_METADATA_READER(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=failing_io,
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git")
    assert close_after_error
    original_stat = io_record.lstat()

    def mismatched_fstat(file_descriptor: int) -> os.stat_result:
        values = list(real_io.fstat(file_descriptor))
        values[1] = original_stat.st_ino + 1
        return os.stat_result(values)

    mismatched_io = protocol.MetadataIO(
        real_io.lstat,
        real_io.open,
        mismatched_fstat,
        real_io.read,
        real_io.close,
    )
    assert PROTOCOL_METADATA_READER(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=mismatched_io,
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", ".git")
    for io_variant, code in (
        (
            protocol.MetadataIO(
                real_io.lstat,
                real_io.open,
                lambda descriptor: os.stat_result(
                    [
                        stat_value if index else 0
                        for index, stat_value in enumerate(real_io.fstat(descriptor))
                    ]
                ),
                real_io.read,
                real_io.close,
            ),
            "ACP.GIT_METADATA.WRONG_TYPE",
        ),
        (
            protocol.MetadataIO(
                real_io.lstat,
                real_io.open,
                real_io.fstat,
                lambda descriptor, count: "not-bytes",  # type: ignore[arg-type,return-value]
                real_io.close,
            ),
            "ACP.GIT_METADATA.READ_TYPE",
        ),
        (
            protocol.MetadataIO(
                real_io.lstat,
                lambda path, flags, **kwargs: (_ for _ in ()).throw(OSError("open race")),
                real_io.fstat,
                real_io.read,
                real_io.close,
            ),
            "ACP.GIT_METADATA.IO_ERROR",
        ),
        (
            protocol.MetadataIO(
                real_io.lstat,
                real_io.open,
                real_io.fstat,
                real_io.read,
                lambda descriptor: (_ for _ in ()).throw(OSError("close failure")),
            ),
            "ACP.GIT_METADATA.IO_ERROR",
        ),
    ):
        assert PROTOCOL_METADATA_READER(
            io_root,
            provenance=protocol.GitMetadataProvenance("dot_git", None),
            io=io_variant,
        ).findings == finding("git-metadata", code, ".git")
    post_lstat_calls = 0

    def changed_after_read(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        nonlocal post_lstat_calls
        result = real_io.lstat(path, dir_fd=dir_fd)
        if path == ".git":
            post_lstat_calls += 1
            if post_lstat_calls > 1:
                values = list(result)
                values[1] += 1
                return os.stat_result(values)
        return result

    assert PROTOCOL_METADATA_READER(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=protocol.MetadataIO(
            changed_after_read,
            real_io.open,
            real_io.fstat,
            real_io.read,
            real_io.close,
        ),
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", ".git")
    race_root = tmp_path / "metadata-ancestor-race"
    race_git_dir = race_root / ".git"
    race_parent = race_git_dir / "info"
    race_parent.mkdir(parents=True)
    race_record = race_parent / "grafts"
    race_record.write_bytes(io_payload)
    race_git_identity = race_git_dir.lstat()
    race_dot_git_record = protocol.GitMetadataRecord(
        race_git_dir,
        None,
        race_git_identity.st_mode,
        race_git_identity.st_dev,
        race_git_identity.st_ino,
    )
    replaced_parent = race_git_dir / "info-original"
    replaced = False

    def replace_ancestor_after_lstat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        nonlocal replaced
        result = real_io.lstat(path, dir_fd=dir_fd)
        if path == "info" and not replaced:
            race_parent.rename(replaced_parent)
            race_parent.symlink_to(replaced_parent, target_is_directory=True)
            replaced = True
        return result

    assert PROTOCOL_METADATA_READER(
        race_root,
        provenance=protocol.GitMetadataProvenance("prohibited_grafts", race_dot_git_record),
        io=protocol.MetadataIO(
            replace_ancestor_after_lstat,
            real_io.open,
            real_io.fstat,
            real_io.read,
            real_io.close,
        ),
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", "info")
    close_failure_opened: list[int] = []
    close_failure_attempts: list[int] = []

    def close_failure_open(path: str, flags: int, *, dir_fd: int | None = None) -> int:
        descriptor = real_io.open(path, flags, dir_fd=dir_fd)
        close_failure_opened.append(descriptor)
        return descriptor

    def fail_first_close(file_descriptor: int) -> None:
        close_failure_attempts.append(file_descriptor)
        if len(close_failure_attempts) == 1:
            raise OSError("contained close failure")
        real_io.close(file_descriptor)

    assert PROTOCOL_METADATA_READER(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=protocol.MetadataIO(
            real_io.lstat,
            close_failure_open,
            real_io.fstat,
            real_io.read,
            fail_first_close,
        ),
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git")
    assert close_failure_attempts == close_failure_opened[::-1]
    real_io.close(close_failure_attempts[0])
    leaf_race_root = tmp_path / "metadata-leaf-race"
    leaf_race_root.mkdir()
    leaf_race_record = leaf_race_root / ".git"
    leaf_race_record.write_bytes(io_payload)
    leaf_original = leaf_race_root / ".git-original"
    leaf_replaced = False

    def replace_leaf_after_lstat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        nonlocal leaf_replaced
        before = real_io.lstat(path, dir_fd=dir_fd)
        if path == ".git" and not leaf_replaced:
            leaf_race_record.rename(leaf_original)
            leaf_race_record.symlink_to(leaf_original)
            leaf_replaced = True
        return before

    assert PROTOCOL_METADATA_READER(
        leaf_race_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=protocol.MetadataIO(
            replace_leaf_after_lstat,
            real_io.open,
            real_io.fstat,
            real_io.read,
            real_io.close,
        ),
    ).findings == finding("git-metadata", "ACP.GIT_METADATA.IDENTITY_CHANGED", ".git")
    assert tuple(metadata_execution_rows) == EXPECTED_METADATA_EXECUTIONS
    assert hashlib.sha256(canonical(metadata_execution_rows)).hexdigest() == (
        EXPECTED_METADATA_FULL_EXECUTION_SHA256
    )
    metadata_execution_ids = tuple(
        f"{execution[0][0]}@{execution[1]}" for execution in metadata_execution_rows
    )
    assert metadata_execution_ids == EXPECTED_METADATA_EXECUTION_IDS
    assert len(metadata_execution_ids) == EXPECTED_METADATA_EXECUTION_COUNT
    assert hashlib.sha256(canonical(metadata_execution_ids)).hexdigest() == (
        EXPECTED_METADATA_EXECUTION_SHA256
    )
    freeze_path = root / FREEZE_PATH
    mutations = (
        ("redHead", "0" * 40, "ACP.FREEZE.RED_HEAD_MISSING"),
        ("redTree", "0" * 40, "ACP.FREEZE.RED_TREE_MISMATCH"),
        ("matrixBlobOid", "0" * 40, "ACP.FREEZE.MATRIX_BLOB_MISMATCH"),
        ("matrixSha256", "0" * 64, "ACP.FREEZE.MATRIX_SHA_MISMATCH"),
        ("implementationAuthor", "other@example.com", "ACP.FREEZE.AUTHOR_MISMATCH"),
    )
    for field, mutation_value, finding_code in mutations:
        changed = deepcopy(freeze)
        changed[field] = mutation_value
        freeze_path.write_bytes(canonical(changed) + b"\n")
        assert protocol.validate_repository_freeze(root) == finding("freeze", finding_code, field)
    changed = deepcopy(freeze)
    changed["redTree"], changed["matrixBlobOid"] = (
        changed["matrixBlobOid"],
        changed["redTree"],
    )
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.RED_TREE_MISMATCH", "redTree"
    )
    changed = deepcopy(freeze)
    changed["focusedOracleBlobs"][0]["blobOid"], changed["focusedOracleBlobs"][1]["blobOid"] = (
        changed["focusedOracleBlobs"][1]["blobOid"],
        changed["focusedOracleBlobs"][0]["blobOid"],
    )
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.ORACLE_BLOB_MISMATCH", "focusedOracleBlobs[0].blobOid"
    )
    for ordinal in range(2):
        for field, oracle_value, finding_code in (
            ("path", "tests/unit/wrong.py", "ACP.FREEZE.ORACLE_PATH_MISMATCH"),
            ("blobOid", "0" * 40, "ACP.FREEZE.ORACLE_BLOB_MISMATCH"),
            ("sha256", "0" * 64, "ACP.FREEZE.ORACLE_SHA_MISMATCH"),
        ):
            changed = deepcopy(freeze)
            changed["focusedOracleBlobs"][ordinal][field] = oracle_value
            freeze_path.write_bytes(canonical(changed) + b"\n")
            assert protocol.validate_repository_freeze(root) == finding(
                "freeze", finding_code, f"focusedOracleBlobs[{ordinal}].{field}"
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
    changed = deepcopy(freeze)
    changed["redHead"] = freeze["matrixBlobOid"]
    for reviewer in changed["reviewers"]:
        reviewer["reviewedRedHead"] = freeze["matrixBlobOid"]
    freeze_path.write_bytes(canonical(changed) + b"\n")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.RED_HEAD_NOT_COMMIT", "redHead"
    )
    freeze_path.write_bytes(canonical(freeze) + b"\n")
    (root / ORACLE_PATHS[0]).write_text("post-RED mutation\n", encoding="utf-8")
    assert protocol.validate_repository_freeze(root) == finding(
        "freeze", "ACP.FREEZE.ORACLE_IMMUTABLE", ORACLE_PATHS[0]
    )
    scoped_root, _ = create_real_git_freeze(tmp_path / "scope", extra_c3_path=True)
    git(scoped_root, "config", "diff.renames", "copies")
    assert protocol.validate_repository_freeze(scoped_root) == finding(
        "freeze",
        "ACP.FREEZE.C3_SCOPE",
        "docs/governance/adversarial-convergence-red-freeze-v1.json",
    )
    gitlink_root, _ = create_real_git_freeze(tmp_path / "gitlink-scope", gitlink_c3=True)
    git(gitlink_root, "config", "diff.ignoreSubmodules", "all")
    assert protocol.validate_repository_freeze(gitlink_root) == finding(
        "freeze", "ACP.FREEZE.C3_SCOPE", FREEZE_PATH
    )
    rename_root, _ = create_real_git_freeze(tmp_path / "rename-scope", rename_c3=True)
    git(rename_root, "config", "diff.renames", "true")
    git(rename_root, "config", "diff.renameLimit", "1")
    assert protocol.validate_repository_freeze(rename_root) == finding(
        "freeze", "ACP.FREEZE.C3_SCOPE", FREEZE_PATH
    )
    configured_root, configured_freeze = create_real_git_freeze(
        tmp_path / "hostile-config", signed_red=True
    )
    marker = configured_root / "forbidden-marker"
    marker_program = configured_root / "marker-program"
    marker_program.write_text(f"#!/bin/sh\ntouch {marker.as_posix()}\nexit 97\n", encoding="utf-8")
    marker_program.chmod(0o700)
    git(
        configured_root,
        "notes",
        "add",
        "-m",
        "forbidden author contamination",
        configured_freeze["redHead"],
    )
    for key, config_value in (
        ("notes.displayRef", "refs/notes/*"),
        ("log.showSignature", "true"),
        ("gpg.program", marker_program.as_posix()),
        ("core.pager", marker_program.as_posix()),
        ("pager.show", "true"),
        ("diff.external", marker_program.as_posix()),
    ):
        git(configured_root, "config", key, config_value)
    signature_probe = REAL_SUBPROCESS_RUN(
        (
            "git",
            "show",
            "--show-signature",
            "--no-notes",
            "-s",
            "--format=%ae",
            configured_freeze["redHead"],
        ),
        cwd=configured_root,
        check=False,
        capture_output=True,
    )
    assert signature_probe.returncode != 0
    assert marker.exists()
    marker.unlink()
    assert protocol.validate_repository_freeze(configured_root) == ()
    assert not marker.exists()
    merge_root, _ = create_real_git_freeze(tmp_path / "merge", merge_c3=True)
    assert protocol.validate_repository_freeze(merge_root) == finding(
        "freeze", "ACP.FREEZE.HISTORY_MERGE", "HEAD"
    )
    later_merge_root, _ = create_real_git_freeze(tmp_path / "later-merge", merge_after_c3=True)
    assert protocol.validate_repository_freeze(later_merge_root) == finding(
        "freeze", "ACP.FREEZE.HISTORY_MERGE", "HEAD"
    )
    sibling_root, _ = create_real_git_freeze(tmp_path / "sibling-c3", dual_red_children=True)
    assert protocol.validate_repository_freeze(sibling_root) == finding(
        "freeze", "ACP.FREEZE.HISTORY_MERGE", "HEAD"
    )
    unchanged_root, _ = create_real_git_freeze(tmp_path / "unchanged-c3", unchanged_c3=True)
    assert protocol.validate_repository_freeze(unchanged_root) == finding(
        "freeze", "ACP.FREEZE.C3_FREEZE_UNCHANGED", FREEZE_PATH
    )
    missing_c3_root, _ = create_real_git_freeze(tmp_path / "missing-c3", omit_c3=True)
    assert protocol.validate_repository_freeze(missing_c3_root) == finding(
        "freeze", "ACP.FREEZE.C3_MISSING", "redHead"
    )
    descendant_root, descendant_document = create_real_git_freeze(
        tmp_path / "descendants", descendant_commits=2
    )
    assert_exact_git_transcript(descendant_root, descendant_document, monkeypatch)
    sixty_four_root, _ = create_real_git_freeze(tmp_path / "sixty-four", descendant_commits=63)
    assert protocol.validate_repository_freeze(sixty_four_root) == ()
    sixty_five_root, _ = create_real_git_freeze(tmp_path / "sixty-five", descendant_commits=64)
    assert protocol.validate_repository_freeze(sixty_five_root) == finding(
        "freeze", "ACP.FREEZE.HISTORY_LIMIT", "redHead..HEAD"
    )
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
    expected_prohibitions = (
        "accepted_authority",
        "active_route",
        "live_trust_root",
        "live_trust_producer",
        "private_or_signing_key",
        "credential",
        "network_or_egress",
        "spend",
        "persistence",
        "product_runtime",
        "provider",
        "workflow_capability",
        "dependency_mutation_or_activation",
        "media_generation",
        "deployment",
        "publication",
        "release",
        "public_availability",
        "sla_claim",
        "commercial_readiness_claim",
        "production_readiness",
        "issue_432",
        "child_c_through_f",
    )
    assert tuple(matrix["prohibitedCapabilities"]) == expected_prohibitions
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
    prefix = ", ".join(repr(item) for item in GIT_PREFIX)
    environment = (
        "{'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1', "
        "'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_NO_LAZY_FETCH': '1', "
        "'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_OPTIONAL_LOCKS': '0', "
        "'GIT_TERMINAL_PROMPT': '0', 'GIT_DIR': git_dir.as_posix(), "
        "'GIT_COMMON_DIR': common_dir.as_posix(), "
        "'GIT_WORK_TREE': root.as_posix()}"
    )
    allowed_expressions = (
        (f"({prefix}, 'rev-parse', '--show-object-format')", False),
        (
            f"({prefix}, 'fsck', '--full', '--strict', '--no-dangling', "
            "'--no-reflogs', '--no-progress')",
            True,
        ),
        (f"({prefix}, 'rev-parse', 'HEAD^{{commit}}')", False),
        (f"({prefix}, 'cat-file', '-t', red_head)", False),
        (f"({prefix}, 'cat-file', '-s', red_head)", False),
        (f"({prefix}, 'merge-base', '--is-ancestor', red_head, head)", False),
        (
            f"({prefix}, 'rev-list', '--min-parents=2', '--max-count=1', "
            "f'{red_head}..{head}')",
            False,
        ),
        (
            f"({prefix}, 'rev-list', '--parents', '--ancestry-path', '--reverse', "
            "'--max-count=65', f'{red_head}..{head}')",
            False,
        ),
        (
            f"({prefix}, 'diff-tree', '-r', '--no-ext-diff', '--no-renames', "
            "'--ignore-submodules=none', '--quiet', red_head, c3_head, '--', '.', "
            f"':(exclude){FREEZE_PATH}')",
            False,
        ),
        (
            f"({prefix}, 'diff-tree', '-r', '--no-ext-diff', '--no-renames', "
            "'--ignore-submodules=none', '--quiet', red_head, c3_head, '--', "
            f"'{FREEZE_PATH}')",
            False,
        ),
        (
            f"({prefix}, 'rev-parse', f'{{red_head}}^{{{{tree}}}}', "
            "f'{red_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', "
            "f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', "
            "f'{red_head}:tests/unit/test_issue435_adversarial_convergence_repository.py')",
            False,
        ),
        (f"({prefix}, 'cat-file', '-s', f'{{c3_head}}:{FREEZE_PATH}')", False),
        (f"({prefix}, 'show', f'{{c3_head}}:{FREEZE_PATH}')", False),
        (
            f"({prefix}, 'show', '--no-notes', '--no-show-signature', '-s', "
            "'--format=%ae', red_head)",
            False,
        ),
    )

    def allowed_git_source(expression: str, fsck: bool) -> str:
        stdout = "subprocess.DEVNULL" if fsck else "subprocess.PIPE"
        timeout = 30 if fsck else 5
        return (
            "import subprocess\n"
            f"subprocess.run({expression}, cwd=root, check=False, stdout={stdout}, "
            "stderr=subprocess.DEVNULL, text=False, "
            f"timeout={timeout}, env={environment})\n"
        )

    read_only_git = "".join(
        allowed_git_source(expression, fsck) for expression, fsck in allowed_expressions
    )
    assert protocol.static_boundary_findings(read_only_git) == ()
    static_contract = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))["staticBoundaryContract"]
    git_contract = static_contract["gitEvidenceContract"]
    protocol_threat_model = {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in protocol.STATIC_GIT_FILESYSTEM_THREAT_MODEL
    }
    assert (
        git_contract["filesystemThreatModel"]
        == EXPECTED_GIT_FILESYSTEM_THREAT_MODEL
        == protocol_threat_model
    )
    threat_mutations: tuple[tuple[str, object], ...] = (
        ("scope", "concurrent_mutation_safe"),
        ("proofs", ["atomic_check_to_use"]),
        ("defenseInDepth", ["race_free_guarantee"]),
        ("gitProcessBinding", "descriptor_bound_git_subprocess"),
        ("excludedThreat", None),
        ("claimsNotMade", []),
        ("strongerClaimDisposition", "PASS"),
    )
    for field, hostile_value in threat_mutations:
        hostile_threat_model = deepcopy(
            cast(dict[str, object], EXPECTED_GIT_FILESYSTEM_THREAT_MODEL)
        )
        hostile_threat_model[field] = hostile_value
        assert hostile_threat_model != git_contract["filesystemThreatModel"]
        assert canonical(hostile_threat_model) != canonical(git_contract["filesystemThreatModel"])
    for required_document_claim in (
        (
            "docs/ADR/0064-adversarial-convergence-protocol.md",
            "### Filesystem snapshot boundary",
        ),
        (
            "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
            "### Stable filesystem snapshot boundary",
        ),
        (
            "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
            "Issue #435 exemplar assumes one stable local filesystem metadata and object",
        ),
    ):
        document = (ROOT / required_document_claim[0]).read_text(encoding="utf-8")
        assert document.count(required_document_claim[1]) == 1
        assert "`EVIDENCE_BLOCKER`" in document
    assert "pass_fds" not in read_only_git
    assert "/proc/self/fd" not in read_only_git
    assert tuple(git_contract["gitPrefix"]) == GIT_PREFIX == protocol.STATIC_GIT_PREFIX
    assert (
        tuple(tuple(item) for item in git_contract["directEnvironment"])
        == (
            *GIT_ENV_FIXED,
            ("GIT_DIR", "derived_git_dir"),
            ("GIT_COMMON_DIR", "derived_common_dir"),
            ("GIT_WORK_TREE", "derived_root"),
        )
        == protocol.STATIC_GIT_ENV_CONTRACT
    )
    assert (
        tuple(git_contract["metadata"]["prohibitedCommonDirTargets"])
        == (
            "info/grafts",
            "shallow",
            "objects/info/alternates",
            "objects/info/http-alternates",
        )
        == protocol.STATIC_GIT_METADATA_TARGETS
    )
    assert tuple(tuple(item) for item in git_contract["metadata"]["roleSpecs"]) == (
        protocol.STATIC_GIT_METADATA_ROLE_SPECS
    )
    assert tuple(git_contract["metadata"]["findingContracts"]) == tuple(
        list(item) for item in protocol.STATIC_GIT_METADATA_FINDINGS
    )
    assert tuple(git_contract["metadata"]["readerSteps"]) == (
        protocol.STATIC_GIT_METADATA_READER_STEPS
    )
    assert tuple(git_contract["metadata"]["discoverySteps"]) == (
        protocol.STATIC_GIT_METADATA_DISCOVERY_STEPS
    )
    metadata_cases = tuple(tuple(item) for item in git_contract["metadata"]["caseUniverse"])
    assert metadata_cases == EXPECTED_METADATA_CASES == protocol.STATIC_GIT_METADATA_CASES
    assert tuple(item[0] for item in metadata_cases) == EXPECTED_METADATA_CASE_IDS
    assert len(set(EXPECTED_METADATA_CASE_IDS)) == len(EXPECTED_METADATA_CASE_IDS)
    metadata_case_sha = hashlib.sha256(canonical(EXPECTED_METADATA_CASES)).hexdigest()
    assert (
        len(EXPECTED_METADATA_CASES)
        == EXPECTED_METADATA_CASE_COUNT
        == git_contract["metadata"]["caseCount"]
        == protocol.STATIC_GIT_METADATA_CASE_COUNT
    )
    assert (
        metadata_case_sha
        == EXPECTED_METADATA_CASE_SHA256
        == git_contract["metadata"]["caseSha256"]
        == protocol.STATIC_GIT_METADATA_CASE_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["executionIds"])
        == EXPECTED_METADATA_EXECUTION_IDS
        == protocol.STATIC_GIT_METADATA_EXECUTION_IDS
    )
    assert (
        git_contract["metadata"]["executionCount"]
        == EXPECTED_METADATA_EXECUTION_COUNT
        == protocol.STATIC_GIT_METADATA_EXECUTION_COUNT
    )
    assert (
        git_contract["metadata"]["executionSha256"]
        == EXPECTED_METADATA_EXECUTION_SHA256
        == protocol.STATIC_GIT_METADATA_EXECUTION_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["executionContractFields"])
        == EXPECTED_METADATA_EXECUTION_CONTRACT_FIELDS
        == protocol.STATIC_GIT_METADATA_EXECUTION_CONTRACT_FIELDS
    )
    assert (
        git_contract["metadata"]["fullExecutionSha256"]
        == EXPECTED_METADATA_FULL_EXECUTION_SHA256
        == protocol.STATIC_GIT_METADATA_FULL_EXECUTION_SHA256
    )
    payload_fingerprint_sha = hashlib.sha256(
        canonical(EXPECTED_METADATA_PAYLOAD_SHA256)
    ).hexdigest()
    assert (
        len(EXPECTED_METADATA_PAYLOAD_SHA256)
        == EXPECTED_METADATA_PAYLOAD_FINGERPRINT_COUNT
        == git_contract["metadata"]["payloadFingerprintCount"]
        == protocol.STATIC_GIT_METADATA_PAYLOAD_FINGERPRINT_COUNT
    )
    assert (
        payload_fingerprint_sha
        == EXPECTED_METADATA_PAYLOAD_FINGERPRINT_SHA256
        == git_contract["metadata"]["payloadFingerprintSha256"]
        == protocol.STATIC_GIT_METADATA_PAYLOAD_FINGERPRINT_SHA256
    )
    governed_precedence_cases = tuple(
        tuple(item) for item in git_contract["metadataGovernedPrecedenceCases"]
    )
    governed_precedence_sha = hashlib.sha256(
        canonical(EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES)
    ).hexdigest()
    assert (
        governed_precedence_cases
        == EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES
        == protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_CASES
    )
    assert (
        len(governed_precedence_cases)
        == git_contract["metadataGovernedPrecedenceCount"]
        == protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_COUNT
        == 1
    )
    assert (
        governed_precedence_sha
        == EXPECTED_METADATA_GOVERNED_PRECEDENCE_SHA256
        == git_contract["metadataGovernedPrecedenceSha256"]
        == protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_SHA256
    )
    assert tuple(protocol.GitMetadataRecord.__dataclass_fields__) == (
        "path",
        "payload",
        "mode",
        "device",
        "inode",
        "ancestor_records",
    )
    assert tuple(git_contract["metadata"]["metadataRecordFields"]) == (
        protocol.STATIC_GIT_METADATA_RECORD_FIELDS
    )
    assert tuple(protocol.GitMetadataProvenance.__dataclass_fields__) == (
        "role",
        "dot_git_record",
        "parent_records",
    )
    assert git_contract["metadata"]["binding"] == protocol.STATIC_GIT_METADATA_BINDING
    protocol_module = ast.parse(source)
    for function_name, expected_source, matrix_field, expected_hash in (
        (
            "_read_git_metadata_nofollow",
            METADATA_READER_SOURCE,
            "readerAstSha256",
            protocol.STATIC_GIT_METADATA_READER_AST_SHA256,
        ),
        (
            "discover_git_repository",
            METADATA_DISCOVERY_SOURCE,
            "discoveryAstSha256",
            protocol.STATIC_GIT_METADATA_DISCOVERY_AST_SHA256,
        ),
    ):
        expected_node = ast.parse(expected_source).body[0]
        expected_ast_hash = hashlib.sha256(
            ast.dump(expected_node, annotate_fields=True, include_attributes=False).encode()
        ).hexdigest()
        actual_nodes = [
            node
            for node in protocol_module.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        ]
        assert len(actual_nodes) == 1
        actual_ast_hash = hashlib.sha256(
            ast.dump(actual_nodes[0], annotate_fields=True, include_attributes=False).encode()
        ).hexdigest()
        assert expected_ast_hash == expected_hash == git_contract["metadata"][matrix_field]
        assert actual_ast_hash == expected_hash
        for hostile_binding in (
            f"\n{function_name} = None\n",
            f"\nclass {function_name}:\n    pass\n",
            f"\ndef {function_name}():\n    pass\n",
            f"\ndel {function_name}\n",
        ):
            assert protocol.static_boundary_findings(source + hostile_binding) == finding(
                "static", "ACP.STATIC.NOT_ALLOWLISTED", "source"
            )
    assert tuple(git_contract["metadataFindingPrecedence"]) == (
        protocol.STATIC_GIT_METADATA_FAILURE_PRECEDENCE
    )
    assert (
        tuple(
            (item[0], tuple(item[1]), tuple(item[2]), tuple(item[3]))
            for item in git_contract["returnCodeContracts"]
        )
        == protocol.STATIC_GIT_RETURN_CODES
    )
    assert (
        tuple(item[0] for item in git_contract["outputContracts"])
        == (
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
        == protocol.STATIC_GIT_FORM_IDS
    )
    textual_transformations = tuple(
        tuple(item) for item in git_contract["textualTransformationCases"]
    )
    textual_transformation_sha = hashlib.sha256(
        canonical(EXPECTED_TEXTUAL_TRANSFORMATIONS)
    ).hexdigest()
    assert (
        textual_transformations
        == EXPECTED_TEXTUAL_TRANSFORMATIONS
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATIONS
    )
    assert (
        len(textual_transformations)
        == TEXTUAL_TRANSFORMATION_COUNT
        == git_contract["textualTransformationCount"]
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_COUNT
    )
    assert (
        sum(item[2] for item in textual_transformations)
        == TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT
        == git_contract["textualTransformationApplicableCount"]
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT
    )
    assert (
        textual_transformation_sha
        == TEXTUAL_TRANSFORMATION_SHA256
        == git_contract["textualTransformationSha256"]
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_SHA256
    )
    assert tuple(tuple(item) for item in git_contract["redObjectBindings"]) == (
        protocol.STATIC_GIT_OBJECT_BINDINGS
    )
    assert tuple(git_contract["findingPrecedence"]) == protocol.STATIC_GIT_FAILURE_PRECEDENCE
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
        "errno": "import errno\n",
        "hashlib": "import hashlib\n",
        "json": "import json\n",
        "os": "import os\n",
        "pathlib.Path": "from pathlib import Path\n",
        "stat": "import stat\n",
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
        "Path.as_posix()": "path.as_posix()\n",
        "str.encode(utf-8)": "value.encode('utf-8')\n",
        "git-metadata:exact-reader-and-discovery-ast": (
            METADATA_READER_SOURCE + "\n" + METADATA_DISCOVERY_SOURCE
        ),
        "subprocess.run(exact_read_only_git,cwd=root,check=False,exact-streams,text=False,exact-timeout,direct-literal-env)": (
            allowed_git_source(*allowed_expressions[0])
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

    for form_index, (expression, fsck) in enumerate(allowed_expressions):
        allowed_source = allowed_git_source(expression, fsck)
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
        stdout = "subprocess.DEVNULL" if fsck else "subprocess.PIPE"
        timeout = 30 if fsck else 5
        exact = (
            f"cwd=root, check=False, stdout={stdout}, stderr=subprocess.DEVNULL, "
            f"text=False, timeout={timeout}, env={environment}"
        )
        for changed_source, code in (
            (allowed_source.replace("'/usr/bin/git'", "'git'", 1), "ACP.STATIC.GIT_FORBIDDEN"),
            (allowed_source.replace("'--no-pager', ", "", 1), "ACP.STATIC.GIT_FORBIDDEN"),
            (allowed_source.replace("check=False", "check=True", 1), "ACP.STATIC.GIT_DYNAMIC"),
            (allowed_source.replace("text=False", "text=True", 1), "ACP.STATIC.GIT_DYNAMIC"),
            (allowed_source.replace("cwd=root", "cwd=dynamic_root", 1), "ACP.STATIC.GIT_DYNAMIC"),
            (
                allowed_source.replace(f"timeout={timeout}", "timeout=0", 1),
                "ACP.STATIC.GIT_DYNAMIC",
            ),
            (
                allowed_source.replace(f"env={environment}", "env=environment", 1),
                "ACP.STATIC.GIT_DYNAMIC",
            ),
            (
                allowed_source.replace(
                    f"env={environment}", f"env={{**os.environ, **{environment}}}", 1
                ),
                "ACP.STATIC.GIT_DYNAMIC",
            ),
            (allowed_source.replace(")\n", ", shell=True)\n", 1), "ACP.STATIC.PROCESS"),
        ):
            assert protocol.static_boundary_findings(changed_source) == finding(
                "static", code, "source"
            )
        prefix_items = list(GIT_PREFIX)
        for prefix_index in range(len(prefix_items)):
            changed_items = prefix_items.copy()
            changed_items[prefix_index] = f"wrong-prefix-{prefix_index}"
            changed_prefix = ", ".join(repr(item) for item in changed_items)
            changed_expression = expression.replace(prefix, changed_prefix, 1)
            assert protocol.static_boundary_findings(
                allowed_git_source(changed_expression, fsck)
            ) == finding("static", "ACP.STATIC.GIT_FORBIDDEN", "source")
            omitted_items = prefix_items[:prefix_index] + prefix_items[prefix_index + 1 :]
            omitted_prefix = ", ".join(repr(item) for item in omitted_items)
            omitted_expression = expression.replace(prefix, omitted_prefix, 1)
            assert protocol.static_boundary_findings(
                allowed_git_source(omitted_expression, fsck)
            ) == finding("static", "ACP.STATIC.GIT_FORBIDDEN", "source")
        for left in range(len(prefix_items) - 1):
            reordered_items = prefix_items.copy()
            reordered_items[left], reordered_items[left + 1] = (
                reordered_items[left + 1],
                reordered_items[left],
            )
            reordered_prefix = ", ".join(repr(item) for item in reordered_items)
            reordered_expression = expression.replace(prefix, reordered_prefix, 1)
            assert protocol.static_boundary_findings(
                allowed_git_source(reordered_expression, fsck)
            ) == finding("static", "ACP.STATIC.GIT_FORBIDDEN", "source")
        for env_key, _ in (
            *GIT_ENV_FIXED,
            ("GIT_DIR", ""),
            ("GIT_COMMON_DIR", ""),
            ("GIT_WORK_TREE", ""),
        ):
            changed_environment = environment.replace(f"'{env_key}':", f"'{env_key}_WRONG':", 1)
            changed_source = allowed_source.replace(environment, changed_environment, 1)
            assert protocol.static_boundary_findings(changed_source) == finding(
                "static", "ACP.STATIC.GIT_DYNAMIC", "source"
            )
            value_anchor = (
                f"'{env_key}': '{dict(GIT_ENV_FIXED)[env_key]}'"
                if env_key in dict(GIT_ENV_FIXED)
                else f"'{env_key}': "
            )
            if env_key in dict(GIT_ENV_FIXED):
                wrong_value = environment.replace(value_anchor, f"'{env_key}': 'WRONG'", 1)
            else:
                start = environment.index(value_anchor)
                value_start = start + len(value_anchor)
                value_end = environment.find(",", value_start)
                if value_end < 0:
                    value_end = environment.find("}", value_start)
                wrong_value = environment[:value_start] + "wrong_value" + environment[value_end:]
            assert protocol.static_boundary_findings(
                allowed_source.replace(environment, wrong_value, 1)
            ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
        assert protocol.static_boundary_findings(
            allowed_source.replace(environment, environment[:-1] + ", 'PATH': '/bin'}", 1)
        ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
        first_env = "'LC_ALL': 'C'"
        second_env = "'GIT_CONFIG_NOSYSTEM': '1'"
        reordered_environment = (
            environment.replace(first_env, "ENV-FIRST", 1)
            .replace(second_env, first_env, 1)
            .replace("ENV-FIRST", second_env, 1)
        )
        assert protocol.static_boundary_findings(
            allowed_source.replace(environment, reordered_environment, 1)
        ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
        stdout = "subprocess.DEVNULL" if fsck else "subprocess.PIPE"
        for changed_source in (
            allowed_source.replace(f"stdout={stdout}, ", "", 1),
            allowed_source.replace(f"stdout={stdout}", "stdout=None", 1),
            allowed_source.replace("stderr=subprocess.DEVNULL, ", "", 1),
            allowed_source.replace("stderr=subprocess.DEVNULL", "stderr=subprocess.PIPE", 1),
        ):
            assert protocol.static_boundary_findings(changed_source) == finding(
                "static", "ACP.STATIC.GIT_DYNAMIC", "source"
            )
        argv_with_extra = expression[:-1] + ", '--extra')"
        assert protocol.static_boundary_findings(
            allowed_git_source(argv_with_extra, fsck)
        ) == finding("static", "ACP.STATIC.GIT_FORBIDDEN", "source")
        for source in (
            f"import subprocess\nargv = {expression}\nsubprocess.run(argv, {exact})\n",
            f"import subprocess\nrunner = subprocess.run\nrunner({expression}, {exact})\n",
            f"import subprocess\nsubprocess.run(args={expression}, {exact})\n",
            f"import subprocess\nsubprocess.run((*{expression},), {exact})\n",
        ):
            assert protocol.static_boundary_findings(source) == finding(
                "static", "ACP.STATIC.GIT_DYNAMIC", "source"
            )
        _, allowed_call = subprocess_call_ast(allowed_source)
        assert allowed_call.args and isinstance(allowed_call.args[0], ast.Tuple)
        argv_count = len(allowed_call.args[0].elts)
        for argv_index in range(len(GIT_PREFIX), argv_count):
            for operation, code in (
                ("omit", "ACP.STATIC.GIT_FORBIDDEN"),
                ("wrong", "ACP.STATIC.GIT_FORBIDDEN"),
                ("dynamic", "ACP.STATIC.GIT_DYNAMIC"),
            ):
                assert protocol.static_boundary_findings(
                    mutate_argv_source(allowed_source, argv_index, operation)
                ) == finding("static", code, "source")
            if argv_index + 1 < argv_count:
                assert protocol.static_boundary_findings(
                    mutate_argv_source(allowed_source, argv_index, "reorder")
                ) == finding("static", "ACP.STATIC.GIT_FORBIDDEN", "source")
        for keyword_index in range(len(allowed_call.keywords)):
            for operation in ("omit", "wrong"):
                assert protocol.static_boundary_findings(
                    mutate_keyword_source(allowed_source, keyword_index, operation)
                ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
            if keyword_index + 1 < len(allowed_call.keywords):
                assert protocol.static_boundary_findings(
                    mutate_keyword_source(allowed_source, keyword_index, "reorder")
                ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
        for environment_index in range(10):
            for operation in ("omit", "wrong-value"):
                assert protocol.static_boundary_findings(
                    mutate_environment_source(allowed_source, environment_index, operation)
                ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
            if environment_index < 9:
                assert protocol.static_boundary_findings(
                    mutate_environment_source(allowed_source, environment_index, "reorder")
                ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
    legacy_expressions = (
        "('git', 'rev-parse', 'HEAD')",
        "('git', 'rev-parse', 'HEAD^')",
        "('git', 'merge-base', '--is-ancestor', red_head, 'HEAD')",
        "('git', 'show', '-s', '--format=%ae', red_head)",
        "('git', 'cat-file', '-e', red_head)",
        "('git', 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD')",
        "('git', 'rev-parse', f'{red_head}:docs/governance/adversarial-convergence-red-freeze-v1.json')",
        "('git', 'rev-list', '--ancestry-path', '--reverse', f'{red_head}..HEAD')",
        "('git', 'rev-parse', f'{red_head}^{commit}', f'{red_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial-convergence_repository.py')",
        "('git', 'rev-parse', f'{red_head}^{tree}', f'{other_head}:docs/governance/adversarial-convergence-invariant-matrix-v1.json', f'{red_head}:tests/unit/test_issue435_adversarial-convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial-convergence_repository.py')",
        "('git', 'rev-parse', f'{red_head}^{tree}', f'{red_head}:docs/{matrix_name}', f'{red_head}:tests/unit/test_issue435_adversarial_convergence.py', f'{red_head}:tests/unit/test_issue435_adversarial_convergence_repository.py')",
        "('git', 'rev-list', '--parents', '-n', '1', c3_head)",
        "('git', 'rev-parse', f'{c3_head}^@')",
        "('git', 'diff-tree', '--no-commit-id', '--name-only', '-r', c3_head)",
        "('git', 'cat-file', '-s', f'{c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json')",
        "('git', 'cat-file', '-s', red_head)",
        "('git', 'show', f'{c3_head}:docs/governance/adversarial-convergence-red-freeze-v1.json')",
        "('/usr/bin/git', '--no-replace-objects', '--no-optional-locks', 'rev-parse', 'HEAD^{commit}')",
        "('/usr/bin/git', '--no-replace-objects', '--no-optional-locks', 'rev-list', '--parents', '--ancestry-path', '--reverse', '--max-count=65', f'{red_head}..{head}')",
        "('/usr/bin/git', '--no-replace-objects', '--no-optional-locks', 'diff-tree', '--no-ext-diff', '--quiet', red_head, c3_head, '--', '.', f':(exclude){FREEZE_PATH}')",
        "('/usr/bin/git', '--no-pager', '--no-replace-objects', '--no-optional-locks', '--no-lazy-fetch', 'diff-tree', '--no-ext-diff', '-r', '--quiet', red_head, c3_head, '--', '.', f':(exclude){FREEZE_PATH}')",
        "('/usr/bin/git', '--no-pager', '--no-replace-objects', '--no-optional-locks', '--no-lazy-fetch', 'show', '-s', '--format=%ae', red_head)",
    )
    for expression in legacy_expressions:
        source = "import subprocess\nsubprocess.run(" + expression + ", cwd=root, check=False)\n"
        assert protocol.static_boundary_findings(source) == finding(
            "static", "ACP.STATIC.GIT_FORBIDDEN", "source"
        )
    targeted_expression_mutations = (
        allowed_expressions[5][0].replace("red_head, head", "other_head, head"),
        allowed_expressions[6][0].replace("{red_head}", "{other_head}"),
        allowed_expressions[7][0].replace("{red_head}", "{red_head!s}"),
        allowed_expressions[8][0].replace("c3_head", "other_c3_head"),
        allowed_expressions[9][0].replace(FREEZE_PATH, "docs/governance/wrong-freeze.json"),
        allowed_expressions[10][0].replace(
            "tests/unit/test_issue435_adversarial_convergence.py", "tests/unit/wrong-core.py"
        ),
        allowed_expressions[10][0].replace(
            "tests/unit/test_issue435_adversarial_convergence_repository.py",
            "tests/unit/wrong-repository.py",
        ),
        allowed_expressions[11][0].replace("c3_head", "other_c3_head"),
        allowed_expressions[12][0].replace(FREEZE_PATH, "docs/governance/{freeze_name}"),
        allowed_expressions[13][0].replace("red_head", "other_head"),
        allowed_expressions[8][0].replace("'-r', ", "", 1),
        allowed_expressions[8][0].replace("'--no-ext-diff', ", "", 1),
        allowed_expressions[8][0].replace("'--no-renames', ", "", 1),
        allowed_expressions[8][0].replace("'--ignore-submodules=none', ", "", 1),
        allowed_expressions[8][0].replace("'-r', '--no-ext-diff'", "'--no-ext-diff', '-r'", 1),
        allowed_expressions[9][0].replace("'--ignore-submodules=none', ", "", 1),
        allowed_expressions[13][0].replace("'--no-notes', ", "", 1),
        allowed_expressions[13][0].replace("'--no-show-signature', ", "", 1),
        allowed_expressions[13][0].replace(
            "'--no-notes', '--no-show-signature'",
            "'--no-show-signature', '--no-notes'",
            1,
        ),
    )
    for changed_expression in targeted_expression_mutations:
        assert protocol.static_boundary_findings(
            allowed_git_source(changed_expression, False)
        ) == finding("static", "ACP.STATIC.GIT_DYNAMIC", "source")
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
