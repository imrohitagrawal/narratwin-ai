"""Repository/Git/nonactivation RED oracle for Issue #435."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import zlib
from copy import deepcopy
from dataclasses import dataclass, replace
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, cast

import pytest

from scripts.quality import issue435_adversarial_convergence as protocol
from tests.unit import test_issue435_adversarial_convergence as core_oracle


Reset47RawResult = tuple[tuple[int, ...], tuple[protocol.Finding, ...]]

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
PROTOCOL_GOVERNED_READER: Any = getattr(protocol, "_read_governed_bytes")
PROTOCOL_DISCOVERY: Any = getattr(protocol, "discover_git_repository")
PROTOCOL_DOCUMENTATION_VALIDATOR: Any = getattr(
    protocol, "filesystem_threat_document_findings", None
)
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
DETERMINISTIC_GIT_METADATA = {
    "GIT_AUTHOR_NAME": "Issue 435 Fixture",
    "GIT_AUTHOR_EMAIL": "issue435-fixture@example.invalid",
    "GIT_AUTHOR_DATE": "1704067200 +0000",
    "GIT_COMMITTER_NAME": "Issue 435 Fixture",
    "GIT_COMMITTER_EMAIL": "issue435-fixture@example.invalid",
    "GIT_COMMITTER_DATE": "1704067200 +0000",
}
GOVERNED_FIXTURE_PARENT_BYTES = 700
GOVERNED_FIXTURE_PARENT_DEPTH = 18
GOVERNED_FIXTURE_SLOT_BYTES = 48
PORTABLE_ROOT_SLOT_NAMES = ("slot-a00", "slot-b00")
PORTABLE_ROOT_CHILD_COMPONENT_BYTES = (12, 12, 12, 12, 12, 15)
PORTABLE_ROOT_RELATIVE_DELTA = (81, 6)
EXPECTED_RESET47_RED_SNAPSHOT_SCHEMA_VERSION = "C2R50_RED_SNAPSHOT_ONLY_V1"
EXPECTED_RESET47_RED_SNAPSHOT_FIXED_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
EXPECTED_RESET47_RED_SNAPSHOT_C1_HEAD = "142dc1502ebec9483c58770f1c03dca9862e9bc8"
EXPECTED_RESET47_RED_SNAPSHOT_FIELDS = (
    "scope",
    "name",
    "source",
    "use",
    "limit",
    "percent",
    "disposition",
)
EXPECTED_RESET47_RED_SNAPSHOT_ROWS = (
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
EXPECTED_RESET47_RED_SNAPSHOT_COUNT = 12
EXPECTED_RESET47_RED_SNAPSHOT_SHA256 = (
    "32b47bf3eebdb87e512fb8e3e4c99c4d168a20f24811b041061fead2f2997a10"
)
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_SCHEMA_VERSION = (
    "RESET50_DYNAMIC_CURRENT_HEAD_BUDGET_V1"
)
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_FIXED_BASE = "a6284f7d8f1a14ef4c9a99493d6b06046505f20c"
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_PREFIX = (
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
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_DIFF_ARGUMENTS = (
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
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ENVIRONMENT = (
    ("LC_ALL", "C"),
    ("GIT_CONFIG_NOSYSTEM", "1"),
    ("GIT_CONFIG_GLOBAL", "/dev/null"),
    ("GIT_NO_LAZY_FETCH", "1"),
    ("GIT_NO_REPLACE_OBJECTS", "1"),
    ("GIT_OPTIONAL_LOCKS", "0"),
    ("GIT_TERMINAL_PROMPT", "0"),
)
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_CHECKOUT_PATHS = (
    "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
    "scripts/quality/issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
    "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
    "docs/ADR/0064-adversarial-convergence-protocol.md",
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
)
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_OUTPUT_PATHS = (
    "docs/ADR/0064-adversarial-convergence-protocol.md",
    "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
    "docs/governance/adversarial-convergence-invariant-matrix-v1.json",
    "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
    "scripts/quality/issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence.py",
    "tests/unit/test_issue435_adversarial_convergence_repository.py",
)
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_ITEM_BYTE_LIMIT = 4194304
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_TOTAL_BYTE_LIMIT = 16777216
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_MEASUREMENT_CONTRACT = (
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
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RISK_THRESHOLD_PERCENT = 85
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_STOP_THRESHOLD_PERCENT = 90
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_FIELDS = ("scope", "name", "source", "limit")
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ROWS = (
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
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_COUNT = 12
EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_SHA256 = (
    "8639b677175273825f7249834cc69f94bee1201bfdf0465d273b44157103d5ce"
)
EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS = (
    "path",
    "marker",
    "repositoryUse",
    "validatorUse",
    "aggregateUse",
    "repositoryPercent",
    "validatorPercent",
    "aggregatePercent",
)
EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS = (
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
EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT = 3
EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256 = (
    "84b9ed78f4bd7eb548e9b8ebdee3616f38426dbcf4433a39a5639fec31f468aa"
)
RESET47_SUBPROCESS_RUN = subprocess.run
MetadataCaseRow = tuple[str, str, str, str, str, str | None, str]
NormalizedMetadataIo = tuple[str, ...]
MetadataRoleTrace = tuple[str, NormalizedMetadataIo]
MetadataStimulusFacts = tuple[tuple[str, str], ...]
MetadataTriggerReceipt = tuple[tuple[str, tuple[str, ...]], ...]
MetadataRawReadRow = tuple[
    str, int, str, tuple[int, ...], tuple[int, ...], int, int, tuple[str, ...]
]
MetadataCloseOrderRow = tuple[str, int, str, tuple[int, ...], tuple[str, ...]]
MetadataNormalizedPayloadRow = tuple[str, int, str, str]
ConfiguredPlanReceipt = tuple[object, ...]
MetadataExecution = tuple[
    MetadataCaseRow,
    str,
    MetadataStimulusFacts,
    str,
    str,
    tuple[str, ...],
    tuple[MetadataRoleTrace, ...],
]


@dataclass(frozen=True)
class PortableRootPlan:
    label: str
    owner_path: str
    owner_mode: int
    owner_device: int
    owner_inode: int
    candidate_components: tuple[str, ...]
    candidate_component_bytes: tuple[int, ...]
    candidate_bytes: int
    candidate_depth: int
    filler_components: tuple[str, ...]
    final_components: tuple[str, str]
    governed_path: str
    governed_bytes: int
    governed_depth: int


@dataclass(frozen=True)
class PortableConstructionResult:
    plans: tuple[PortableRootPlan, PortableRootPlan]
    planning_transcript: tuple[tuple[str, str], ...]
    filesystem_receipts: tuple[tuple[int, str, str, int, int, int, int], ...]
    governed_roots: tuple[Path, Path]


@dataclass(frozen=True)
class MetadataCollection:
    full_executions: tuple[MetadataExecution, ...]
    stimuli: tuple[tuple[MetadataStimulusFacts, str], ...]
    trigger_receipts: tuple[MetadataTriggerReceipt, ...]
    raw_reads: tuple[MetadataRawReadRow, ...]
    close_orders: tuple[MetadataCloseOrderRow, ...]
    normalized_payloads: tuple[MetadataNormalizedPayloadRow, ...]
    configured_plan_receipts: tuple[ConfiguredPlanReceipt, ...]


@dataclass(frozen=True)
class ConfiguredProjectionResult:
    projection: tuple[str, str, str, str] | None
    findings: tuple[protocol.Finding, ...]


@dataclass(frozen=True)
class ParsedConfiguredRawReceipt:
    raw_receipt: tuple[tuple[str, ...], ...]
    callback_prefixes: tuple[str, ...]
    successful_opens: tuple[tuple[int, int, int, str, str], ...]
    projection: tuple[str, str, str, str]
    observed: tuple[str, str, int, int]


@dataclass(frozen=True)
class ConfiguredRawIntegrityResult:
    parsed: ParsedConfiguredRawReceipt | None
    findings: tuple[protocol.Finding, ...]


@dataclass(frozen=True)
class _SplitFunctionReturn:
    value: Any


TextualTransformation = tuple[str, str, bool, str | None, str | None, str | None]
NormalizedGitByteIdentity = tuple[object, ...]
VerifiedGitOidMapping = tuple[str, int, int, str, str]
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
    "configuredStimulusFacts",
    "configuredStimulusIdentity",
    "observedExecutionEvidenceIdentity",
    "rolePrefix",
    "normalizedIoCleanupPrefix",
)
EXPECTED_METADATA_TRIGGER_RECEIPT_FIELDS = (
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
EXPECTED_METADATA_INTER_ROLE_TRIGGER_RECEIPT_FIELDS = (
    "role",
    "afterRole",
    "path",
    "beforeType",
    "afterType",
    "identityChanged",
    "triggered",
)
EXPECTED_METADATA_TRIGGER_RECEIPT_COUNT = 129
EXPECTED_METADATA_TRIGGER_RECEIPT_SHA256 = (
    "a7891e4113c89b48be4dedcc3f260d5211d622853ec16f52b5f4f9e355015d0e"
)
EXPECTED_METADATA_TRIGGER_RECEIPT_SCHEDULE_CONTRACT = (
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
EXPECTED_METADATA_FIXTURE_ROOT_RELATION_FIELDS = (
    "slot",
    "relativeFilesystemByteDelta",
    "relativeLexicalDepthDelta",
)
EXPECTED_METADATA_FIXTURE_ROOT_RELATIONS = (("A", 0, 0), ("B", 81, 6))
EXPECTED_METADATA_FIXTURE_PORTABLE_OWNER_MODELS = (("darwin", 27, 4), ("linux", 17, 3))
EXPECTED_METADATA_FIXTURE_OWNERSHIP_CONTRACT = (
    "one-cleanup-owned-platform-temporary-base",
    "equal-width-A-B-slot-components",
    "B-only-six-component-relative-suffix",
    "resolved-base-inode-owned-and-stable",
    "feasibility-plan-proved-before-creation",
    "infeasible-model-fails-before-filesystem-mutation",
    "no-hardcoded-private-tmp",
)
EXPECTED_METADATA_COLLECTION_FIELDS = (
    "fullExecutions",
    "stimuli",
    "triggerReceipts",
    "rawReadCatalog",
    "closeOrderCatalog",
    "normalizedPayloadCatalog",
    "configuredPlanReceipts",
)
EXPECTED_METADATA_ROOT_REPLAY_ENVELOPE_FIELDS = (
    "slot",
    "relativeRootShape",
    "governedParentShape",
    "finalComponentLengths",
    "evidenceIdentity",
)
EXPECTED_METADATA_ROOT_REPLAY_EVIDENCE_FIELDS = (
    "fullExecutions",
    "stimuli",
    "triggerReceipts",
    "rawReadCatalog",
    "closeOrderCatalog",
    "normalizedPayloadCatalog",
)
EXPECTED_METADATA_ROOT_REPLAY_EVIDENCE_IDENTITY_SHA256 = (
    "d47f7eb94ac3ad3e841ba4e99741e2a346683f059bb493fc120b03c5d40eeeee"
)
EXPECTED_METADATA_ROOT_REPLAY_ENVELOPE_COUNT = 2
EXPECTED_METADATA_ROOT_REPLAY_RELATION_SHA256 = (
    "555b222414c70aeea1e4bb2bbfd57f26d0117e957f63635fb8d5a3ce83d48903"
)
EXPECTED_METADATA_ROOT_REPLAY_RUNTIME_CONTRACT = (
    "derive-runtime-envelope-from-owned-base-and-relative-relation",
    "final-components-each-8-through-255-filesystem-bytes",
    "governed-parent-exactly-700-bytes-depth-18",
    "both-evidence-identities-exact-and-equal",
)
EXPECTED_METADATA_ROOT_REPLAY_CONFIGURED_PLAN_RECEIPT_EQUALITY = (
    "capture-under-each-root",
    "exact-row-equality",
    "exact-digest-equality-before-portability-credit",
)
EXPECTED_METADATA_RAW_READ_FIELDS = (
    "executionId",
    "roleOrdinal",
    "role",
    "rawReadRequestVector",
    "rawReadChunkLengthVector",
    "rawReadRequestCount",
    "rawReadChunkCount",
    "readTypeVector",
)
EXPECTED_METADATA_RAW_READ_COUNT = 466
EXPECTED_METADATA_RAW_READ_SHA256 = (
    "83e4d288ea34bda6765e3b3fe4ed0b39d4f6d794f7ddda521ded6038bfb23955"
)
EXPECTED_METADATA_CLOSE_ORDER_FIELDS = (
    "executionId",
    "roleOrdinal",
    "role",
    "rawCloseAttemptOrderVector",
    "closeResultVector",
)
EXPECTED_METADATA_CLOSE_ORDER_COUNT = 466
EXPECTED_METADATA_CLOSE_ORDER_SHA256 = (
    "1072b8834f65136320bf419d760eae50cf916fc8b411a90362f2c100a6fdcf73"
)
EXPECTED_METADATA_NORMALIZED_PAYLOAD_FIELDS = (
    "executionId",
    "roleOrdinal",
    "role",
    "normalizedPayloadSha256",
)
EXPECTED_METADATA_NORMALIZED_PAYLOAD_COUNT = 466
EXPECTED_METADATA_NORMALIZED_PAYLOAD_SHA256 = (
    "9f328cbc155b9b57047f4ab53d78720842fbeb02cae54c5a7e03090ab001bda1"
)
EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANTS = (
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
        "metadataReplay.normalizedPayloads[conventional-positive@conventional][0]"
        ".normalizedPayloadSha256",
    ),
)
EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANT_FIELDS = (
    "mutantId",
    "catalog",
    "executionId",
    "roleOrdinal",
    "coordinate",
    "mutation",
    "findingLocation",
)
EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANT_SHA256 = (
    "6d399932abf4cc9a2a4b7324b70f2f63cad5b53ca37636cb9d123fbd214e0c64"
)
EXPECTED_METADATA_REMOVED_CONFIG_COLLISION_COUNT = 5
EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_FIELDS = (
    "historicalGroupName",
    "executionPair",
)
EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIRS = (
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
EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_COUNT = 17
EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_SHA256 = (
    "aa41b6ec402fa9bedc1fb441baf6532011bb7b2f2dc813f360c387edb35da13d"
)
EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_SOURCE_IDENTITY = (
    "Reset29:be4aba72a9b808569091ed5c69471f7c747eca6e:"
    "EXPECTED_METADATA_FORMER_COLLISION_GROUPS[-17:]"
)
EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENT_FIELDS = (
    "historicalGroupName",
    "executionPair",
    "uniqueCompleteClass",
)
REPOSITORY_EVIDENCE_FIXTURE_PATH = (
    ROOT / "tests/fixtures/governance/issue435-repository-evidence-v1.json"
)
EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_SCHEMA = "Issue435RepositoryEvidenceFixtureV1"
EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_BYTE_CAP = 1_500_000
EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_SHA256 = (
    "8d040be04eda3236c6bce82ebefda11691a7b53d523d536520e7089e09ccaa77"
)
EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_PROVENANCE = {
    "determinism": "normalized synthetic Git fixtures; no provider or external data",
    "issue": 435,
    "preservationCommit": "3a5fba3a08ffdb7e6c6645a479f83fb4cd7ce328",
    "preservationTree": "d84292e567d9789d6d79b043d38499ad2e2c25fb",
}
EXPECTED_REPOSITORY_EVIDENCE_CATALOG_CONTRACT = (
    (
        "configuredEquivalenceClasses",
        5,
        "b71385899ad0186538de9ade027e0b1b768af8fe30cd19ac8d8e026e6b2dc60a",
    ),
    (
        "configuredPlanMutants",
        104,
        "7ebcf4b63a1d5bd109aaa3308ede26aa5db3bf0dbe26feea9f306976e1c1e837",
    ),
    (
        "configuredReceiptBindings",
        22,
        "9aed869589d56316ac76e8b6b7cd005da51a5edcc17cb926a6444468f84809d3",
    ),
    (
        "historicalPairContainments",
        17,
        "c89bc0e10ccc1cb720014aba723f9a4ecda4c75a5973311d97029e9bc4a33e8e",
    ),
    (
        "hostileGitOidEvidence",
        9,
        "0997c929375f6e5216ed9d0d8ace2ccb366a5bf1e2f43632abc6e330efffbbca",
    ),
    ("metadataExecutions", 129, "74c0225e39f7fc6c170a1922246133daf07f458ee5040a1d581272602573190c"),
    (
        "normalizedGitByteIdentities",
        44,
        "29938b5b3c6533e7e97c852f7dfb95b606763bdbe18e81d1a14e02535483e492",
    ),
    (
        "positionBoundGitCases",
        8,
        "4604114cb67d2eeacc65351c14bd65040526c8f14e54dcbcf016d5810c723f20",
    ),
    ("receiptHybrids", 130, "bd26f841084c593d62f16c8fba27731be0c101b20a20332f48ed348caa6d32e0"),
    (
        "textualTransformations",
        70,
        "7e4e4eded6736f4894747e012cfb3b5727a073a0c9950b38712684a0c1e2b6d2",
    ),
    (
        "verifiedGitOidMappings",
        7,
        "9f0817328f5e411f2b39ca4bfdc4300cc48884e065d251e929b7569328da028f",
    ),
)


def repository_evidence_fixture_finding(code: str, location: str) -> tuple[protocol.Finding, ...]:
    return (protocol.Finding("evidence-fixture", "CURRENT", code, location),)


def _tuple_tree(value: object) -> object:
    if isinstance(value, list):
        return tuple(_tuple_tree(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuple_tree(item) for key, item in value.items()}
    return value


def _fixture_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate fixture key: {key}")
        result[key] = value
    return result


def validate_repository_evidence_fixture_bytes(
    payload: bytes,
) -> tuple[dict[str, tuple[object, ...]] | None, tuple[protocol.Finding, ...]]:
    if len(payload) > EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_BYTE_CAP:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.BYTE_CAP", "bytes")
    if b"\0" in payload or b"\r" in payload:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.ENCODING", "bytes")
    try:
        document = json.loads(payload, object_pairs_hook=_fixture_object)
    except UnicodeDecodeError:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.JSON", "document")
    except json.JSONDecodeError:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.JSON", "document")
    except ValueError:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.DUPLICATE", "document")
    if type(document) is not dict or set(document) != {"catalogs", "provenance", "schemaVersion"}:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.FIELDS", "document")
    if document["schemaVersion"] != EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_SCHEMA:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.SCHEMA", "schemaVersion")
    if document["provenance"] != EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_PROVENANCE:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.PROVENANCE", "provenance")
    catalogs = document["catalogs"]
    expected_names = tuple(row[0] for row in EXPECTED_REPOSITORY_EVIDENCE_CATALOG_CONTRACT)
    if type(catalogs) is not dict or tuple(sorted(catalogs)) != tuple(sorted(expected_names)):
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.CATALOGS", "catalogs")
    loaded: dict[str, tuple[object, ...]] = {}
    for name, expected_count, expected_identity in EXPECTED_REPOSITORY_EVIDENCE_CATALOG_CONTRACT:
        catalog = catalogs[name]
        if type(catalog) is not dict or set(catalog) != {"count", "rows", "sha256"}:
            return None, repository_evidence_fixture_finding("ACP.FIXTURE.CATALOG_FIELDS", name)
        rows = catalog["rows"]
        if (
            type(rows) is not list
            or type(catalog["count"]) is not int
            or catalog["count"] != expected_count
            or len(rows) != expected_count
        ):
            return None, repository_evidence_fixture_finding("ACP.FIXTURE.COUNT", name)
        identity = hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if (
            type(catalog["sha256"]) is not str
            or catalog["sha256"] != expected_identity
            or identity != expected_identity
        ):
            return None, repository_evidence_fixture_finding("ACP.FIXTURE.IDENTITY", name)
        loaded[name] = cast(tuple[object, ...], _tuple_tree(rows))
    expected_payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    if payload != expected_payload:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.CANONICAL", "document")
    if hashlib.sha256(payload).hexdigest() != EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_SHA256:
        return None, repository_evidence_fixture_finding("ACP.FIXTURE.WHOLE_IDENTITY", "document")
    return loaded, ()


_REPOSITORY_EVIDENCE_CATALOGS, _REPOSITORY_EVIDENCE_FINDINGS = (
    validate_repository_evidence_fixture_bytes(REPOSITORY_EVIDENCE_FIXTURE_PATH.read_bytes())
)
assert _REPOSITORY_EVIDENCE_FINDINGS == ()
assert _REPOSITORY_EVIDENCE_CATALOGS is not None

EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENTS = cast(
    Any, _REPOSITORY_EVIDENCE_CATALOGS["historicalPairContainments"]
)
EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENT_COUNT = 17
EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENT_SHA256 = (
    "c89bc0e10ccc1cb720014aba723f9a4ecda4c75a5973311d97029e9bc4a33e8e"
)
EXPECTED_METADATA_HISTORICAL_CROSS_CLASS_MUTANT = (
    "MUT-HISTORICAL-PAIR-CROSS-CLASS",
    ("pre-root-symlink@linked", "root-replacement@conventional"),
    "configuredRemovedHistoricalPairs[17]",
)
EXPECTED_METADATA_FORMER_COLLISION_GROUPS = (
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
EXPECTED_METADATA_FORMER_COLLISION_GROUP_COUNT = 19
EXPECTED_METADATA_FORMER_COLLISION_GROUP_SHA256 = (
    "3d6ec3f35db4037153555ae3e3fd4332f70b5812e8413923399b1fa805753185"
)
EXPECTED_METADATA_CONFIGURED_PLAN_FIELDS = (
    "executionId",
    "callback",
    "target",
    "phase",
    "effect",
)
EXPECTED_METADATA_CONFIGURED_PLAN_IDENTITY_CONTRACT = (
    "non-label",
    "non-terminal",
    "derived-from-configured-callback-target-phase-effect",
    "included-in-every-valid-execution-binding",
)
EXPECTED_METADATA_CONFIGURED_PLANS = (
    ("pre-root-symlink@linked", "filesystem-state", "root-ancestor", "before-discovery", "symlink"),
    ("fstat-type@linked", "fstat", "dot-git", "after-open", "type-drift"),
    ("open-error@linked", "open", "dot-git", "initial-open", "os-error"),
    ("root-replacement@conventional", "lstat", "root", "after-lstat", "identity-replacement"),
    (
        "ancestor-replacement@conventional",
        "lstat",
        "info-ancestor",
        "after-lstat",
        "identity-replacement",
    ),
    (
        "between-read-conventional-dot-git@conventional",
        "inter-role",
        "dot-git",
        "after-dot-git-read",
        "dot-git-replacement",
    ),
    (
        "final-binding-revalidation@conventional",
        "inter-role",
        "dot-git",
        "after-prohibited-http-alternates-read",
        "identity-replacement",
    ),
    ("leaf-replacement@conventional", "lstat", "dot-git", "after-lstat", "identity-replacement"),
    ("fstat-device@conventional", "fstat", "dot-git", "after-open", "device-drift"),
    ("fstat-inode@conventional", "fstat", "dot-git", "after-open", "inode-drift"),
    ("fstat-type@conventional", "fstat", "dot-git", "after-open", "type-drift"),
    ("lstat-error@conventional", "lstat", "dot-git", "initial-lstat", "os-error"),
    ("open-error@conventional", "open", "dot-git", "initial-open", "os-error"),
    ("close-error@conventional", "close", "dot-git", "cleanup", "os-error"),
    ("root-replacement@linked", "lstat", "root", "after-lstat", "identity-replacement"),
    ("leaf-replacement@linked", "lstat", "dot-git", "after-lstat", "identity-replacement"),
    ("post-read-device@linked", "lstat", "dot-git", "after-read", "device-drift"),
    (
        "between-read-linked-directory@linked",
        "inter-role",
        "linked-git-dir",
        "after-linked-git-dir-read",
        "linked-dir-replacement",
    ),
    (
        "between-read-common-directory@linked",
        "inter-role",
        "common-dir",
        "after-common-dir-read",
        "common-dir-replacement",
    ),
    ("fstat-inode@linked", "fstat", "dot-git", "after-open", "inode-drift"),
    ("lstat-error@linked", "lstat", "dot-git", "initial-lstat", "os-error"),
    ("close-error@linked", "close", "dot-git", "cleanup", "os-error"),
)
EXPECTED_METADATA_CONFIGURED_PLAN_COUNT = 22
EXPECTED_METADATA_CONFIGURED_PLAN_SHA256 = (
    "be232294b50b2ab84f96df800d6b495ace266077218bd6fb2c716353622015e8"
)
EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_FIELDS = (
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
EXPECTED_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS = (
    "callbackArguments",
    "callbackEvents",
    "roleEvents",
    "metadataEvents",
    "statEvents",
    "exceptionEvents",
    "closeEffects",
    "interRoleEvidence",
)
EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS = (
    "callback",
    "target",
    "phase",
    "effect",
)
EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_IDENTITY_CONTRACT = (
    "capture-root-relative-or-descriptor-role-ordinal-actual-callback-arguments-with-argument-type-and-event-ordinal",
    "derive-raw-evidence-identity-from-callback-role-metadata-stat-exception-close-and-inter-role-events-before-semantic-projection",
    "pure-projector-accepts-only-raw-receipt-and-derives-semantic-fields",
    "must-not-read-configured-plan-case-row-expected-finding-or-terminal-result",
    "separate-binder-validates-raw-integrity-and-exact-callback-target-phase-effect-against-declared-plan",
)
EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS = (
    ("callbackArguments", 1024),
    ("callbackEvents", 1024),
    ("roleEvents", 16),
    ("metadataEvents", 1024),
    ("statEvents", 768),
    ("exceptionEvents", 32),
    ("closeEffects", 512),
    ("interRoleEvidence", 7),
)
EXPECTED_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP = 4096
EXPECTED_METADATA_CONFIGURED_EXCEPTION_TYPES = (
    "FileNotFoundError",
    "NotADirectoryError",
    "OSError",
)
EXPECTED_METADATA_CONFIGURED_CLOSED_ROLES = (
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
EXPECTED_METADATA_CONFIGURED_INTER_ROLE_RELATION_FIELDS = (
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
EXPECTED_METADATA_CONFIGURED_INTER_ROLE_RELATIONS = (
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
EXPECTED_METADATA_CONFIGURED_INTER_ROLE_SCHEDULE_FIELDS = (
    "afterRole",
    "roleSchedule",
    "targetRoleOrdinal",
    "triggerRoleOrdinal",
    "terminalRoleOrdinal",
    "benignExceptionLedger",
)
EXPECTED_METADATA_CONFIGURED_INTER_ROLE_SCHEDULES = (
    ("dot_git", ("discovery", "dot_git", "common_dir"), 1, 1, 2, ()),
    (
        "linked_git_dir",
        ("discovery", "dot_git", "linked_git_dir", "backlink"),
        2,
        2,
        3,
        (),
    ),
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
EXPECTED_METADATA_CONFIGURED_ALLOWED_ROLE_SCHEDULES = (
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
EXPECTED_METADATA_CONFIGURED_NON_INTER_ALLOWED_ROLE_SCHEDULES = (
    ("discovery",),
    ("discovery", "dot_git"),
    ("discovery", "dot_git", "common_dir", "prohibited_grafts"),
)
EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS = (
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
EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_FIELDS = (
    "mutantId",
    "targetRoleOrdinal",
    "changedFieldSet",
    "findingLocation",
)
EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_COUNT = 2
EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_SHA256 = (
    "b9e02deec92e8005bad764079147f07a5f871b146028356cacd6b1bdd64eefe4"
)
EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE = (
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
EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_FIELDS = (
    "mutantId",
    "operation",
    "changedFieldSet",
    "expectedCoordinate",
    "findingLocation",
)
EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_COUNT = 8
EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_SHA256 = (
    "bd5d97eeb27e0f55867812f4dff7c412ee494010f97ff05181224e6589566d75"
)
EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_COUNT = 22
EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_SHA256 = (
    "a35b10c41378c50b01ab03110481bc068667454fd3927b77f7162d34a5ce6d02"
)
EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_FIELDS = (
    "executionEvidenceIdentity",
    "rawEvidenceIdentity",
    "observed",
    "projection",
)
EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDINGS = cast(
    Any, _REPOSITORY_EVIDENCE_CATALOGS["configuredReceiptBindings"]
)
EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAPS = (
    (1, 2),
    (8, 9),
    (11, 13),
    (12, 14),
    (16, 17),
    (18, 19),
    (20, 21),
)
EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_FIELDS = (
    "donorReceiptIndex",
    "recipientReceiptIndex",
)
EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_COUNT = 22
EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_SHA256 = (
    "9aed869589d56316ac76e8b6b7cd005da51a5edcc17cb926a6444468f84809d3"
)
EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_COUNT = 7
EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_SHA256 = (
    "421384f1402ffdad681b6062288eb0bcfba55834ef2f9e28f630b50a74ed4c49"
)
EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS = cast(
    Any, _REPOSITORY_EVIDENCE_CATALOGS["configuredPlanMutants"]
)
EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_FIELDS = (
    "mutantId",
    "executionId",
    "expectedCoordinate",
    "mutationLayer",
    "changedFieldSet",
    "operation",
    "rawIdentityAction",
    "findingLocation",
)
EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_COUNT = 104
EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_SHA256 = (
    "7ebcf4b63a1d5bd109aaa3308ede26aa5db3bf0dbe26feea9f306976e1c1e837"
)
EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_FIELDS = (
    "mutantId",
    "operation",
    "expectedCode",
    "expectedLocation",
    "filesystemBoundary",
)
EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANTS = (
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
EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_COUNT = 9
EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_SHA256 = (
    "f8a2204b6cddcf2f324124945bba87629d862c76377bcfbc2cf4d6c01bbaa7c0"
)
EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_FIELDS = (
    "mutantId",
    "operation",
    "expectedLocation",
    "expectedSeamCalls",
)
EXPECTED_PORTABLE_ROOT_PLAN_FIELDS = (
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
EXPECTED_PORTABLE_ROOT_PLAN_FIELD_COUNT = 14
EXPECTED_PORTABLE_ROOT_PLAN_FIELD_SHA256 = (
    "7d979d7ec622de838582a8fa021d0adf1b95e13f2fcab32de23960f92fc76d7c"
)
EXPECTED_PORTABLE_CONSTRUCTION_MUTANTS = (
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
EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_COUNT = 29
EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_SHA256 = (
    "18f988577e4eb104238c25489f8f29e56a88161f25bf212ba3eba9590f347361"
)
EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_FIELDS = (
    "groupName",
    "completeExecutionIds",
    "strippedFactsIdentity",
    "declaredCollision",
)
EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_CLASSES = cast(
    Any, _REPOSITORY_EVIDENCE_CATALOGS["configuredEquivalenceClasses"]
)
EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_COUNT = 5
EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_SHA256 = (
    "b71385899ad0186538de9ade027e0b1b768af8fe30cd19ac8d8e026e6b2dc60a"
)
EXPECTED_METADATA_RECEIPT_HYBRID_FIELDS = (
    "groupName",
    "sourceExecutionId",
    "swappedReceiptExecutionId",
    "strippedFactsIdentity",
    "configuredPlanIdentity",
    "actualReceiptIdentity",
    "hybridBindingIdentity",
    "validSetMembership",
)
EXPECTED_METADATA_RECEIPT_HYBRIDS = cast(Any, _REPOSITORY_EVIDENCE_CATALOGS["receiptHybrids"])
EXPECTED_METADATA_RECEIPT_HYBRID_COUNT = 130
EXPECTED_METADATA_RECEIPT_HYBRID_SHA256 = (
    "bd26f841084c593d62f16c8fba27731be0c101b20a20332f48ed348caa6d32e0"
)
EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES = (
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
EXPECTED_METADATA_GOVERNED_PRECEDENCE_SHA256 = (
    "5f25c0757507c7061d70cd885aae48c3341163d8957f018a20db6649bbf207e2"
)
EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANT_FIELDS = (
    "mutantId",
    "filesystemRereadHelper",
    "hostileDecoy",
    "substitution",
    "requiredDescriptor",
    "requiredSchemaIdentity",
    "expectedDisposition",
)
EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANTS = (
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
EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANT_SHA256 = (
    "ddaf256a0bdf6c063ab8fd0e5a8eeb74ec97b4c78a58d380f17ed8a93453093e"
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
EXPECTED_GIT_FILESYSTEM_THREAT_MODEL_FINDINGS = (
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
EXPECTED_DOCUMENT_OVERCLAIM_NORMALIZATION = (
    "ascii-lowercase",
    "remove-markdown-emphasis-asterisk-underscore-backtick",
    "collapse-whitespace-and-hyphen-runs-to-space",
    "strip-leading-and-trailing-space",
)
EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_AXES = (
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
)
EXPECTED_DOCUMENT_PROHIBITED_FAMILY_GRAMMAR = (
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
)
EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_COUNT = 44
EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_SHA256 = (
    "9a6f83544ddc8e595861d2cd3d7b0a8d24fac7b75e5d61024868e222d561f3b8"
)
EXPECTED_DOCUMENT_NORMALIZATION_MUTANTS = (
    ("omit-backtick-removal", "backtick-only"),
    ("omit-final-strip", "edge-whitespace-only"),
)
EXPECTED_DOCUMENT_NORMALIZATION_MUTANT_SHA256 = (
    "b365ac98f1bcdf8501259e4a39c5441ab60cb24a8a0f66c21d921ee28fbbec96"
)
EXPECTED_GIT_DOCUMENTATION_CLAIM_CONTRACT = {
    "validator": "filesystem_threat_document_findings",
    "blockStart": "<!-- issue-435-filesystem-snapshot-boundary:start -->",
    "blockEnd": "<!-- issue-435-filesystem-snapshot-boundary:end -->",
    "approvedBlockSha256": [
        [
            "docs/ADR/0064-adversarial-convergence-protocol.md",
            "1e9c8e1ef77f7583da58edd6263d1bec851517206daa25edefd3ba55d935579e",
        ],
        [
            "docs/ADVERSARIAL_VERIFICATION_PLAYBOOK.md",
            "4d2661cac412e05b3e051d34a2e95f7f42d4c9de27792325dcceabbb397ae208",
        ],
        [
            "docs/templates/ADVERSARIAL_INVARIANT_MATRIX.md",
            "cd8d7b6c24e43689f8aff316f7f9fe4f04e9409b231ecd526cf0eea9b62ebc8f",
        ],
    ],
    "prohibitedClaimFamilies": [
        "race_free_validation",
        "atomic_check_to_use",
        "descriptor_bound_git_subprocess",
        "detection_or_prevention_of_all_concurrent_repository_mutation",
    ],
    "normalization": list(EXPECTED_DOCUMENT_OVERCLAIM_NORMALIZATION),
    "variantAxes": list(EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_AXES),
    "prohibitedFamilyGrammar": [
        [family, list(phrases)] for family, phrases in EXPECTED_DOCUMENT_PROHIBITED_FAMILY_GRAMMAR
    ],
    "variantCount": EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_COUNT,
    "variantSha256": EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_SHA256,
    "normalizerMutantFields": ["mutantId", "hostileAxis"],
    "normalizerMutants": [list(row) for row in EXPECTED_DOCUMENT_NORMALIZATION_MUTANTS],
    "normalizerMutantCount": len(EXPECTED_DOCUMENT_NORMALIZATION_MUTANTS),
    "normalizerMutantSha256": EXPECTED_DOCUMENT_NORMALIZATION_MUTANT_SHA256,
    "findingContracts": [
        ["block", "ACP.DOC.THREAT_MODEL_BLOCK"],
        ["overclaim", "ACP.DOC.THREAT_MODEL_OVERCLAIM"],
    ],
    "location": "governed-document-path",
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
EXPECTED_METADATA_EXECUTIONS = cast(
    tuple[MetadataExecution, ...], _REPOSITORY_EVIDENCE_CATALOGS["metadataExecutions"]
)
EXPECTED_METADATA_EXECUTION_COUNT = 129
EXPECTED_METADATA_EXECUTION_SHA256 = (
    "dc206260cb4f4c2d1217ba9a6cf274279c2fdbe6c98f5c4c0db21d133558e91b"
)
EXPECTED_METADATA_FULL_EXECUTION_SHA256 = (
    "74c0225e39f7fc6c170a1922246133daf07f458ee5040a1d581272602573190c"
)
EXPECTED_METADATA_STIMULUS_COUNT = 129
EXPECTED_METADATA_STIMULUS_SHA256 = (
    "d93d3a44c3a3b18a9bd46edec8fe7f981790f6e0dd55da96ce1be3a18eab498d"
)

TEXTUAL_TRANSFORMS = ("missing_lf", "crlf", "extra_line", "corrupt_token", "valid_token")
EXPECTED_TEXTUAL_TRANSFORMATIONS = cast(
    tuple[TextualTransformation, ...], _REPOSITORY_EVIDENCE_CATALOGS["textualTransformations"]
)
TEXTUAL_TRANSFORMATION_COUNT = 70
TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT = 44
TEXTUAL_TRANSFORMATION_SHA256 = "7e4e4eded6736f4894747e012cfb3b5727a073a0c9950b38712684a0c1e2b6d2"
TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_FIELDS = (
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
TEXTUAL_TRANSFORMATION_BUILDERS = (
    ("missing_lf", "remove-one-terminal-lf", "base[:-1]"),
    ("crlf", "replace-lf-with-crlf", "base.replace(LF,CRLF)"),
    ("extra_line", "role-specific-extra-line", "extra(base,role)"),
    ("corrupt_token", "role-specific-corrupt-token", "corrupt(base,role)"),
    ("valid_token", "role-specific-valid-semantic", "valid(base,role,freeze)"),
)
TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_SHA256 = (
    "d94fc0a49bf78e072ac44997785e40e073c19e9d14f0a19ab5a9415d88e60456"
)
TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_FIELDS = (
    "role",
    "transformation",
    "identityMode",
    "tokenMapShape",
    "normalizedBaseLength",
    "normalizedBaseSha256",
    "normalizedTransformedLength",
    "normalizedTransformedSha256",
)
EXPECTED_VERIFIED_GIT_OID_MAPPING_FIELDS = (
    "role",
    "rowOrdinal",
    "columnOrdinal",
    "semanticName",
    "identitySource",
)
EXPECTED_VERIFIED_GIT_OID_MAPPINGS = cast(
    tuple[VerifiedGitOidMapping, ...], _REPOSITORY_EVIDENCE_CATALOGS["verifiedGitOidMappings"]
)
EXPECTED_VERIFIED_GIT_OID_MAPPING_COUNT = 7
EXPECTED_VERIFIED_GIT_OID_MAPPING_SHA256 = (
    "9f0817328f5e411f2b39ca4bfdc4300cc48884e065d251e929b7569328da028f"
)
EXPECTED_POSITION_BOUND_GIT_CASE_FIELDS = (
    "caseId",
    "role",
    "mutation",
    "stage",
    "code",
    "location",
    "exactStoppedRolePrefix",
)
EXPECTED_POSITION_BOUND_GIT_CASES = cast(
    Any, _REPOSITORY_EVIDENCE_CATALOGS["positionBoundGitCases"]
)
EXPECTED_POSITION_BOUND_GIT_CASE_COUNT = 8
EXPECTED_POSITION_BOUND_GIT_CASE_SHA256 = (
    "4604114cb67d2eeacc65351c14bd65040526c8f14e54dcbcf016d5810c723f20"
)
EXPECTED_HOSTILE_GIT_OID_EVIDENCE_FIELDS = (
    "role",
    "transform",
    "hostileOidTokenVector",
    "verifiedSemanticVector",
    "normalizedTransformedSha256",
)
EXPECTED_HOSTILE_GIT_OID_EVIDENCE = cast(
    tuple[tuple[object, ...], ...], _REPOSITORY_EVIDENCE_CATALOGS["hostileGitOidEvidence"]
)
EXPECTED_HOSTILE_GIT_OID_EVIDENCE_COUNT = 9
EXPECTED_HOSTILE_GIT_OID_EVIDENCE_SHA256 = (
    "0997c929375f6e5216ed9d0d8ace2ccb366a5bf1e2f43632abc6e330efffbbca"
)
EXPECTED_NORMALIZED_GIT_BYTE_IDENTITIES = cast(
    tuple[NormalizedGitByteIdentity, ...],
    _REPOSITORY_EVIDENCE_CATALOGS["normalizedGitByteIdentities"],
)
EXPECTED_NORMALIZED_GIT_BYTE_IDENTITY_COUNT = 44
EXPECTED_NORMALIZED_GIT_BYTE_IDENTITY_SHA256 = (
    "29938b5b3c6533e7e97c852f7dfb95b606763bdbe18e81d1a14e02535483e492"
)


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
    role_specs["discovery"] = ("directory", 0, "root", "root")
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
    if provenance.role == "discovery":
        if provenance.dot_git_record is not None or provenance.parent_records:
            return result(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", location),),
            )
        path = root_path
    elif provenance.role == "dot_git":
        if (
            provenance.dot_git_record is not None
            or len(provenance.parent_records) not in {1, 2}
            or provenance.parent_records[0][0] != "discovery"
            or provenance.parent_records[0][1].path != root_path
            or provenance.parent_records[0][1].payload is not None
            or (
                len(provenance.parent_records) == 2
                and (
                    provenance.parent_records[1][0] != "dot_git"
                    or provenance.parent_records[1][1].path != root_path / ".git"
                )
            )
        ):
            return result(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", "root"),),
            )
        if not stat.S_ISDIR(provenance.parent_records[0][1].mode):
            return result(
                None,
                (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.WRONG_TYPE", "root"),),
            )
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

    discovery = _read_git_metadata_nofollow(
        root,
        provenance=GitMetadataProvenance("discovery", None),
        io=SYSTEM_METADATA_IO,
    )
    if discovery.findings:
        return GitDiscoveryResult(None, discovery.findings)
    if discovery.record is None:
        return GitDiscoveryResult(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.MISSING", "root"),),
        )

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

    dot_git_provenance = GitMetadataProvenance(
        "dot_git", None, (("discovery", discovery.record),)
    )
    if dot_git_provenance.parent_records[0][1] is not discovery.record:
        return GitDiscoveryResult(
            None,
            (Finding("git-metadata", "CURRENT", "ACP.GIT_METADATA.CONTAINMENT", "root"),),
        )
    dot_git = _read_git_metadata_nofollow(
        root,
        provenance=dot_git_provenance,
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
            "dot_git",
            None,
            (("discovery", discovery.record), ("dot_git", dot_git.record)),
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


def reset47_budget_finding(coordinate: str) -> tuple[protocol.Finding, ...]:
    location = (
        coordinate
        if coordinate.startswith(("dynamicBudget", "rawCheckout"))
        else f"budgetPolicy.{coordinate}"
    )
    return (
        protocol.Finding(
            "evidence",
            "CURRENT",
            "ACP.EVIDENCE.RESET47_BUDGET_MISMATCH",
            location,
        ),
    )


def expected_reset47_budget_policy() -> dict[str, object]:
    return {
        "chargeRule": "additions_plus_deletions_no_deletion_credit",
        "riskThresholdPercent": 85,
        "stopThresholdPercent": 90,
        "denseCompressionProhibited": True,
        "repositoryEvidenceFixtureByteBudget": [
            "tests/fixtures/governance/issue435-repository-evidence-v1.json",
            1_272_789,
            1_500_000,
            1_275_000,
            1_350_000,
            "84.85",
            "8d040be04eda3236c6bce82ebefda11691a7b53d523d536520e7089e09ccaa77",
        ],
        "reset47RedSnapshot": {
            "schemaVersion": EXPECTED_RESET47_RED_SNAPSHOT_SCHEMA_VERSION,
            "fixedBase": EXPECTED_RESET47_RED_SNAPSHOT_FIXED_BASE,
            "c1Head": EXPECTED_RESET47_RED_SNAPSHOT_C1_HEAD,
            "fields": list(EXPECTED_RESET47_RED_SNAPSHOT_FIELDS),
            "rows": [list(row) for row in EXPECTED_RESET47_RED_SNAPSHOT_ROWS],
            "count": EXPECTED_RESET47_RED_SNAPSHOT_COUNT,
            "sha256": EXPECTED_RESET47_RED_SNAPSHOT_SHA256,
        },
        "dynamicCurrentHeadBudgetContract": {
            "schemaVersion": EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_SCHEMA_VERSION,
            "fixedBase": EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_FIXED_BASE,
            "gitPrefix": list(EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_PREFIX),
            "gitDiffArguments": list(
                EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_DIFF_ARGUMENTS
            ),
            "environment": [
                list(row) for row in EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ENVIRONMENT
            ],
            "rawCheckoutPaths": list(
                EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_CHECKOUT_PATHS
            ),
            "gitOutputPaths": list(EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_OUTPUT_PATHS),
            "rawItemByteLimit": EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_ITEM_BYTE_LIMIT,
            "rawTotalByteLimit": EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_TOTAL_BYTE_LIMIT,
            "measurementContract": list(
                EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_MEASUREMENT_CONTRACT
            ),
            "riskThresholdPercent": (
                EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RISK_THRESHOLD_PERCENT
            ),
            "stopThresholdPercent": (
                EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_STOP_THRESHOLD_PERCENT
            ),
            "fields": list(EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_FIELDS),
            "rows": [list(row) for row in EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ROWS],
            "count": EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_COUNT,
            "sha256": EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_SHA256,
        },
        "reset47RedSnapshotProseUse": {
            "fields": list(EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS),
            "rows": [list(row) for row in EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS],
            "count": EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT,
            "sha256": EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256,
        },
        "levels": ["per_file", "partition", "aggregate"],
    }


def same_reset47_value(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        actual_dict = cast(dict[object, object], actual)
        return tuple(actual_dict) == tuple(expected) and all(
            same_reset47_value(actual_dict[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        actual_list = cast(list[object], actual)
        return len(actual_list) == len(expected) and all(
            same_reset47_value(item, wanted)
            for item, wanted in zip(actual_list, expected, strict=True)
        )
    return actual == expected


def validate_reset47_catalog(
    actual: object, expected: dict[str, object], location: str
) -> tuple[protocol.Finding, ...]:
    if type(actual) is not dict:
        return reset47_budget_finding(f"{location}.type")
    catalog = cast(dict[str, object], actual)
    if tuple(catalog) != tuple(expected):
        return reset47_budget_finding(f"{location}.keys")
    rows = catalog["rows"]
    expected_rows = cast(list[object], expected["rows"])
    if type(rows) is not list:
        return reset47_budget_finding(f"{location}.rows.type")
    if len(rows) != len(expected_rows):
        return reset47_budget_finding(f"{location}.rows.count")
    if type(expected["count"]) is not int or expected["count"] != len(expected_rows):
        return reset47_budget_finding(f"{location}.expectedCount")
    normalized: list[tuple[object, ...]] = []
    for ordinal, (row, wanted) in enumerate(zip(rows, expected_rows, strict=True)):
        if type(row) is not list or len(row) != len(cast(list[object], wanted)):
            return reset47_budget_finding(f"{location}.rows[{ordinal}].type")
        if any(
            type(value) is not type(expected_value)
            for value, expected_value in zip(row, cast(list[object], wanted), strict=True)
        ):
            return reset47_budget_finding(f"{location}.rows[{ordinal}].type")
        normalized.append(tuple(row))
    expected_normalized = tuple(tuple(cast(list[object], row)) for row in expected_rows)
    if len({canonical(row) for row in normalized}) != len(normalized):
        return reset47_budget_finding(f"{location}.rows.duplicate")
    if tuple(normalized) != expected_normalized:
        if sorted(normalized, key=canonical) == sorted(expected_normalized, key=canonical):
            return reset47_budget_finding(f"{location}.rows.order")
        return reset47_budget_finding(f"{location}.rows.value")
    if not same_reset47_value(catalog["count"], len(expected_rows)):
        return reset47_budget_finding(f"{location}.count")
    expected_sha = hashlib.sha256(canonical(expected_rows)).hexdigest()
    if catalog["sha256"] != expected_sha or expected["sha256"] != expected_sha:
        return reset47_budget_finding(f"{location}.sha256")
    for key in tuple(expected)[:-3]:
        if not same_reset47_value(catalog[key], expected[key]):
            return reset47_budget_finding(f"{location}.{key}")
    return ()


def validate_reset47_budget_policy(policy: object) -> tuple[protocol.Finding, ...]:
    expected = expected_reset47_budget_policy()
    if type(policy) is not dict:
        return reset47_budget_finding("type")
    actual = cast(dict[str, object], policy)
    if tuple(actual) != tuple(expected):
        return reset47_budget_finding("keys")
    for key in ("chargeRule", "riskThresholdPercent", "stopThresholdPercent"):
        if not same_reset47_value(actual[key], expected[key]):
            return reset47_budget_finding(key)
    if not same_reset47_value(actual["denseCompressionProhibited"], True):
        return reset47_budget_finding("denseCompressionProhibited")
    if not same_reset47_value(
        actual["repositoryEvidenceFixtureByteBudget"],
        expected["repositoryEvidenceFixtureByteBudget"],
    ):
        return reset47_budget_finding("repositoryEvidenceFixtureByteBudget")
    for key in (
        "reset47RedSnapshot",
        "dynamicCurrentHeadBudgetContract",
        "reset47RedSnapshotProseUse",
    ):
        findings = validate_reset47_catalog(
            actual[key], cast(dict[str, object], expected[key]), key
        )
        if findings:
            return findings
    if not same_reset47_value(actual["levels"], expected["levels"]):
        return reset47_budget_finding("levels")
    return ()


def reset47_budget_percentages(uses: tuple[int, ...]) -> tuple[str, ...]:
    percentages: list[str] = []
    for use, row in zip(uses, EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ROWS, strict=True):
        limit = row[3]
        if limit is None:
            percentages.append("N/A")
        elif limit == 0:
            percentages.append("0.00")
        else:
            ratio = Decimal(use) * Decimal(100) / Decimal(limit)
            percentages.append(format(ratio.quantize(Decimal("0.01"), ROUND_HALF_EVEN), ".2f"))
    return tuple(percentages)


def reset47_prose_finding(coordinate: str) -> tuple[protocol.Finding, ...]:
    return (
        protocol.Finding(
            "evidence",
            "CURRENT",
            "ACP.EVIDENCE.RESET47_RED_SNAPSHOT_PROSE_USE_MISMATCH",
            f"budgetPolicy.reset47RedSnapshotProseUse.{coordinate}",
        ),
    )


def validate_reset47_prose_catalog(catalog: object) -> tuple[protocol.Finding, ...]:
    if type(catalog) is not dict:
        return reset47_prose_finding("catalog.type")
    typed_catalog = cast(dict[str, object], catalog)
    if set(typed_catalog) != {"fields", "rows", "count", "sha256"}:
        return reset47_prose_finding("catalog.type")
    fields = typed_catalog["fields"]
    if type(fields) is not list or tuple(fields) != EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS:
        return reset47_prose_finding("catalog.fields")
    rows = typed_catalog["rows"]
    if type(rows) is not list:
        return reset47_prose_finding("catalog.rows")
    if len(rows) < EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT:
        return reset47_prose_finding("catalog.rows.missing")
    if len(rows) > EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT:
        return reset47_prose_finding("catalog.rows.cardinality")
    if any(type(row) is not list or len(row) != 8 for row in rows):
        return reset47_prose_finding("catalog.rows")
    expected_types = (str, str, int, int, int, str, str, str)
    if any(
        tuple(type(value) for value in cast(list[object], row)) != expected_types for row in rows
    ):
        return reset47_prose_finding("catalog.rows.type")
    normalized_rows = tuple(tuple(cast(list[object], row)) for row in rows)
    if len({canonical(row) for row in normalized_rows}) != len(normalized_rows):
        return reset47_prose_finding("catalog.rows.duplicate")
    if normalized_rows != EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS:
        if set(normalized_rows) == set(EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS):
            return reset47_prose_finding("catalog.rows.order")
        if any(
            row[2:8] != expected[2:8]
            for row, expected in zip(
                normalized_rows, EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS, strict=True
            )
        ):
            return reset47_prose_finding("catalog.values")
        return reset47_prose_finding("catalog.rows")
    if type(typed_catalog["count"]) is not int or (
        typed_catalog["count"] != EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT
    ):
        return reset47_prose_finding("catalog.count")
    expected_sha = hashlib.sha256(canonical(rows)).hexdigest()
    if type(typed_catalog["sha256"]) is not str or (
        typed_catalog["sha256"] != EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256
        or expected_sha != EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256
    ):
        return reset47_prose_finding("catalog.sha256")
    return ()


def reset47_expected_use_sentence(path: str, tokens: tuple[str, ...]) -> str:
    if path.endswith("0064-adversarial-convergence-protocol.md"):
        return (
            f"Exact file use is {', '.join(tokens[:6])}, and {tokens[6]} lines. "
            f"Exact partitions are {tokens[7]}, {tokens[8]}, and {tokens[9]}; "
            f"the {tokens[10]}."
        )
    if path.endswith("ADVERSARIAL_VERIFICATION_PLAYBOOK.md"):
        return f"Exact use: {'; '.join(tokens[:10])}; and {tokens[10]}."
    return f"Exact use is {'; '.join(tokens[:10])}; and {tokens[10]}."


def validate_reset47_prose_documents(
    rows: object,
    documents: object,
    uses: dict[str, int],
    caps: dict[str, int],
) -> tuple[protocol.Finding, ...]:
    if type(rows) is not tuple or type(documents) is not dict:
        return reset47_prose_finding("documents.type")
    expected_paths = tuple(row[0] for row in EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS)
    if len(rows) != EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT:
        return reset47_prose_finding("documents.rows")
    if set(cast(dict[object, object], documents)) != set(expected_paths):
        return reset47_prose_finding("documents.path")
    start_prefix = b"<!-- issue-435-reset47-red-snapshot:sha256="
    end_prefix = b"<!-- issue-435-reset47-red-snapshot:end"
    end_line = b"<!-- issue-435-reset47-red-snapshot:end -->\n"
    marker_pattern = re.compile(
        rb"(?m)^<!-- issue-435-reset47-red-snapshot:sha256=([0-9a-f]{64}) -->\n"
    )
    names = (
        "matrix",
        "protocol",
        "coreOracle",
        "repositoryOracle",
        "template",
        "adr0064",
        "playbook",
        "validator",
        "architectureSecurity",
        "route",
        "sevenSemanticPaths",
    )
    labels = (
        "matrix",
        "protocol",
        "core",
        "repository",
        "template",
        "ADR",
        "playbook",
        "validator",
        "architecture/security",
        "route",
        "seven-path aggregate",
    )
    for ordinal, untyped_row in enumerate(cast(tuple[object, ...], rows)):
        if type(untyped_row) is not tuple or len(untyped_row) != 8:
            return reset47_prose_finding("documents.rows")
        row = cast(tuple[object, ...], untyped_row)
        expected_types = (str, str, int, int, int, str, str, str)
        if tuple(type(value) for value in row) != expected_types:
            return reset47_prose_finding("documents.rows.type")
        path, marker = cast(str, row[0]), cast(str, row[1])
        if path != expected_paths[ordinal]:
            return reset47_prose_finding("documents.path")
        values = (uses["repositoryOracle"], uses["validator"], uses["sevenSemanticPaths"])
        percents = (
            f"{values[0] * 100 / caps['repositoryOracle']:.2f}",
            f"{values[1] * 100 / caps['validator']:.2f}",
            f"{values[2] * 100 / caps['sevenSemanticPaths']:.2f}",
        )
        if row[2:5] != values or row[5:8] != percents:
            return reset47_prose_finding("documents.values")
        payload = cast(dict[str, object], documents)[path]
        if type(payload) is not bytes:
            return reset47_prose_finding("documents.blocks.type")
        lines = payload.splitlines(keepends=True)
        start_candidates = tuple(line for line in lines if start_prefix in line)
        end_candidates = tuple(line for line in lines if end_prefix in line)
        if not start_candidates or not end_candidates:
            return reset47_prose_finding("documents.blocks.missing")
        exact_starts = tuple(marker_pattern.finditer(payload))
        exact_ends = sum(line == end_line for line in lines)
        if len(exact_starts) > 1 and exact_ends > 1:
            return reset47_prose_finding("documents.blocks.duplicate")
        if len(start_candidates) > 1 or len(end_candidates) > 1:
            return reset47_prose_finding("documents.blocks.nested")
        if len(exact_starts) != 1 or exact_ends != 1:
            return reset47_prose_finding("documents.marker.wholeLine")
        start_match = exact_starts[0]
        end = payload.find(end_line)
        if start_match.start() >= end:
            return reset47_prose_finding("documents.blocks.pairing")
        if b"\0" in payload:
            return reset47_prose_finding("documents.text.nul")
        if b"\r" in payload:
            return reset47_prose_finding("documents.text.crlf")
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError:
            return reset47_prose_finding("documents.text.encoding")
        actual_marker = payload[start_match.start() : start_match.end() - 1].decode("ascii")
        if marker != actual_marker:
            return reset47_prose_finding("documents.marker.substitution")
        interior = payload[start_match.end() : end]
        if not interior.endswith(b"\n"):
            return reset47_prose_finding("documents.text.trailing")
        text = " ".join(interior.decode("utf-8").split())
        tokens: list[str] = []
        positions: list[int] = []
        for name, label in zip(names, labels, strict=True):
            if ordinal == 0 and name == "sevenSemanticPaths":
                label = "seven-path aggregate is"
            percent_required = name != "playbook"
            pattern = re.compile(
                rf"(?<![\w/]){re.escape(label)} ([0-9][0-9,]*)(?:/([0-9][0-9,]*))?"
                + (r" \(([0-9]+\.[0-9]{2})%\)" if percent_required else "")
            )
            matches = tuple(pattern.finditer(text))
            if not matches:
                coordinate = {
                    "repositoryOracle": "documents.repositoryUse",
                    "validator": "documents.validatorUse",
                    "sevenSemanticPaths": "documents.aggregateUse",
                }.get(name, "documents.tokens")
                return reset47_prose_finding(coordinate)
            if len(matches) > 1:
                groups = {match.groups() for match in matches}
                coordinate = (
                    "documents.tokens.duplicate"
                    if len(groups) == 1
                    else "documents.tokens.contradictory"
                )
                return reset47_prose_finding(coordinate)
            match = matches[0]
            use_text, cap_text = match.group(1), match.group(2)
            use = int(use_text.replace(",", ""))
            observed_cap = int(cap_text.replace(",", "")) if cap_text else None
            expected_cap = (
                None if path == expected_paths[1] and name in names[:7] else caps.get(name)
            )
            if use != uses[name] or observed_cap != expected_cap:
                coordinate = {
                    "repositoryOracle": "documents.repositoryUse",
                    "validator": "documents.validatorUse",
                    "sevenSemanticPaths": "documents.aggregateUse",
                }.get(name, "documents.tokens")
                return reset47_prose_finding(coordinate)
            if use_text != f"{uses[name]:,}" or (
                cap_text is not None and cap_text != f"{cast(int, expected_cap):,}"
            ):
                return reset47_prose_finding("documents.tokens.number")
            if percent_required:
                expected_percent = f"{uses[name] * 100 / caps[name]:.2f}"
                if match.group(3) != expected_percent:
                    coordinate = {
                        "repositoryOracle": "documents.repositoryPercent",
                        "validator": "documents.validatorPercent",
                        "sevenSemanticPaths": "documents.aggregatePercent",
                    }.get(name, "documents.percentage")
                    return reset47_prose_finding(coordinate)
            tokens.append(match.group(0))
            positions.append(match.start())
        if positions != sorted(positions):
            return reset47_prose_finding("documents.tokens.order")
        if reset47_expected_use_sentence(path, tuple(tokens)) not in text:
            return reset47_prose_finding("documents.tokens.grammar")
        required = (
            "core, repository, validator, and aggregate",
            (
                "Readability/convergence PASS",
                "aggregate readability and convergence reviews PASS",
                "repository, validator, and aggregate reviews PASS",
            )[ordinal],
            "independent semantic literals and catalog assertions",
            "below",
            "90",
            "no semantic compression",
            "further",
            "growth",
        )
        if any(fragment.lower() not in text.lower() for fragment in required):
            return reset47_prose_finding("documents.tokens.clauses")
        marker_contract = (
            (
                "The whole-line start marker encodes SHA-256 of the raw UTF-8/LF bytes strictly "
                "between the newline after this marker and the byte before the end marker, "
                "including exactly one terminal LF and excluding both marker lines."
            ),
            (
                "The whole-line start marker encodes SHA-256 of raw UTF-8/LF bytes strictly "
                "between the marker lines, including exactly one terminal LF."
            ),
            (
                "The whole-line start marker encodes SHA-256 of raw UTF-8/LF bytes strictly "
                "between the marker lines, including exactly one terminal LF and excluding both markers."
            ),
        )[ordinal]
        if not text.endswith(marker_contract):
            return reset47_prose_finding("documents.text.trailing")
        if hashlib.sha256(interior).hexdigest() != start_match.group(1).decode("ascii"):
            return reset47_prose_finding("documents.blockHash")
    return ()


def validate_reset47_prose_contract(
    catalog: object,
    load_documents: Callable[[tuple[str, ...]], object],
    uses: dict[str, int],
    caps: dict[str, int],
) -> tuple[protocol.Finding, ...]:
    catalog_findings = validate_reset47_prose_catalog(catalog)
    if catalog_findings:
        return catalog_findings
    rows = tuple(
        tuple(row) for row in cast(list[list[object]], cast(dict[str, object], catalog)["rows"])
    )
    paths = tuple(cast(str, row[0]) for row in rows)
    documents = load_documents(paths)
    return validate_reset47_prose_documents(rows, documents, uses, caps)


def configured_receipt_finding(index: int, coordinate: str) -> tuple[protocol.Finding, ...]:
    return (
        protocol.Finding(
            "evidence",
            "CURRENT",
            "ACP.EVIDENCE.CONFIGURED_PLAN_MISMATCH",
            f"configuredPlanReceipts[{index}].{coordinate}",
        ),
    )


def _configured_finding(index: int, coordinate: str) -> ConfiguredRawIntegrityResult:
    return ConfiguredRawIntegrityResult(None, configured_receipt_finding(index, coordinate))


def _configured_path(value: str) -> bool:
    ancestor = re.fullmatch(r"root-ancestor-distance-([1-9]|[1-5][0-9]|6[0-4])", value)
    if ancestor is not None:
        return True
    match = re.fullmatch(
        r"(\$ROOT|\$COMMON|\$LINKED_GIT_DIR|fixture-relative:\$TMP/\$CASE)((?:/[A-Za-z0-9._-]+)*)",
        value,
    )
    if match is None:
        return False
    components = tuple(part for part in match.group(2).split("/") if part)
    return len(components) <= 64 and all(
        part not in {".", ".."} and len(part.encode("utf-8")) <= 255 for part in components
    )


def _configured_argument_path(detail: str) -> str | None:
    if "path-" not in detail:
        return None
    path_tail = detail.split("path-", 1)[1]
    return (
        path_tail.split(":dirfd", 1)[0]
        if path_tail.startswith("fixture-relative:")
        else path_tail.split(":", 1)[0]
    )


def _configured_child_path(parent: str, child: str) -> bool:
    parent_ancestor = re.fullmatch(r"root-ancestor-distance-([1-9]|[1-5][0-9]|6[0-4])", parent)
    child_ancestor = re.fullmatch(r"root-ancestor-distance-([1-9]|[1-5][0-9]|6[0-4])", child)
    if parent_ancestor is not None:
        distance = int(parent_ancestor.group(1))
        if distance == 1:
            return (
                child == "$ROOT"
                or re.fullmatch(r"fixture-relative:\$TMP/\$CASE/[A-Za-z0-9._-]+", child) is not None
            )
        return child_ancestor is not None and int(child_ancestor.group(1)) == distance - 1
    for base in ("$ROOT", "$COMMON", "$LINKED_GIT_DIR", "fixture-relative:$TMP/$CASE"):
        if parent == base:
            return child.startswith(base + "/") and "/" not in child[len(base) + 1 :]
        if parent.startswith(base + "/"):
            prefix = parent + "/"
            return child.startswith(prefix) and "/" not in child[len(prefix) :]
    return False


def _configured_role_path(role: str, path: str) -> bool:
    """Bind every lexical callback path to one closed reader-role domain."""
    if re.fullmatch(r"root-ancestor-distance-(?:[1-9]|[1-5][0-9]|6[0-4])", path):
        return True
    external_git = "fixture-relative:$TMP/$CASE/source/repository/.git"
    external_prefixes = {
        "fixture-relative:$TMP/$CASE/source",
        "fixture-relative:$TMP/$CASE/source/repository",
        external_git,
    }
    role_paths = {
        "discovery": {"$ROOT"},
        "dot_git": {"$ROOT", "$ROOT/.git"},
        "linked_git_dir": external_prefixes
        | {
            external_git + "/worktrees",
            external_git + "/worktrees/linked",
        },
        "backlink": external_prefixes
        | {
            external_git + "/worktrees",
            external_git + "/worktrees/linked",
            external_git + "/worktrees/linked/gitdir",
        },
        "commondir": external_prefixes
        | {
            external_git + "/worktrees",
            external_git + "/worktrees/linked",
            external_git + "/worktrees/linked/commondir",
        },
        "common_dir": {"$ROOT", "$ROOT/.git"} | external_prefixes,
        "prohibited_grafts": {
            "$ROOT",
            "$ROOT/.git",
            "$ROOT/.git/info",
            "$ROOT/.git/info/grafts",
            *external_prefixes,
            external_git + "/info",
            external_git + "/info/grafts",
        },
        "prohibited_shallow": {
            "$ROOT",
            "$ROOT/.git",
            "$ROOT/.git/shallow",
            *external_prefixes,
            external_git + "/shallow",
        },
        "prohibited_alternates": {
            "$ROOT",
            "$ROOT/.git",
            "$ROOT/.git/objects",
            "$ROOT/.git/objects/info",
            "$ROOT/.git/objects/info/alternates",
            *external_prefixes,
            external_git + "/objects",
            external_git + "/objects/info",
            external_git + "/objects/info/alternates",
        },
        "prohibited_http_alternates": {
            "$ROOT",
            "$ROOT/.git",
            "$ROOT/.git/objects",
            "$ROOT/.git/objects/info",
            "$ROOT/.git/objects/info/http-alternates",
            *external_prefixes,
            external_git + "/objects",
            external_git + "/objects/info",
            external_git + "/objects/info/http-alternates",
        },
    }
    return path in role_paths.get(role, set())


def configured_raw_bounds_findings(
    raw_receipt: tuple[object, ...], index: int
) -> tuple[protocol.Finding, ...]:
    """Apply field-count and encoded-item limits before receipt grammar."""
    caps = dict(EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS)
    for coordinate, value in zip(
        EXPECTED_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS, raw_receipt, strict=True
    ):
        if type(value) is not tuple:
            return configured_receipt_finding(index, coordinate)
        if len(value) > caps[coordinate]:
            return configured_receipt_finding(index, f"{coordinate}.countLimit")
        if any(type(item) is not str for item in value):
            return configured_receipt_finding(index, coordinate)
        try:
            if any(
                len(item.encode("utf-8")) > EXPECTED_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP
                for item in value
            ):
                return configured_receipt_finding(index, f"{coordinate}.itemByteLimit")
        except UnicodeEncodeError:
            return configured_receipt_finding(index, f"{coordinate}.itemEncoding")
    return ()


def _validate_configured_raw_receipt_part_1(
    raw_receipt: Any,
    stored_identity: Any,
    index: Any,
) -> Any:
    """Strictly validate the closed raw receipt before semantic projection."""
    if type(index) is not int or index < 0 or index >= EXPECTED_METADATA_CONFIGURED_PLAN_COUNT:
        return _SplitFunctionReturn(_configured_finding(0, "receiptIndex"))
    if type(raw_receipt) is not tuple or len(raw_receipt) != 8:
        return _SplitFunctionReturn(_configured_finding(index, "rawReceipt"))

    bounds_findings = configured_raw_bounds_findings(raw_receipt, index)
    if bounds_findings:
        return _SplitFunctionReturn(ConfiguredRawIntegrityResult(None, bounds_findings))
    fields = cast(tuple[tuple[str, ...], ...], raw_receipt)
    receipt = cast(tuple[tuple[str, ...], ...], tuple(fields))
    if (
        type(stored_identity) is not str
        or stored_identity != hashlib.sha256(canonical(receipt)).hexdigest()
    ):
        return _SplitFunctionReturn(_configured_finding(index, "rawEvidenceIdentity"))
    arguments, events, roles, metadata, stats, exceptions, closes, inter = receipt
    inter_markers = tuple(item for item in roles if item.startswith("interReceiptOrdinal-"))
    reader_roles = tuple(item for item in roles if not item.startswith("interReceiptOrdinal-"))
    if not inter and inter_markers:
        return _SplitFunctionReturn(_configured_finding(index, "roleEvents"))
    parsed_roles: list[tuple[int, str]] = []
    for expected_ordinal, item in enumerate(reader_roles):
        match = re.fullmatch(r"(0|[1-9][0-9]*):([a-z_]+)", item)
        if (
            match is None
            or int(match.group(1)) != expected_ordinal
            or match.group(2) not in EXPECTED_METADATA_CONFIGURED_CLOSED_ROLES
        ):
            return _SplitFunctionReturn(_configured_finding(index, "roleEvents"))
        parsed_roles.append((expected_ordinal, match.group(2)))
    if not parsed_roles or parsed_roles[0] != (0, "discovery"):
        return _SplitFunctionReturn(_configured_finding(index, "roleEvents"))
    prefixes: list[str] = []
    role_event_counts = [0] * len(parsed_roles)
    last_role = -1
    callback_rows: list[tuple[int, int, str, str, str, str | None]] = []
    for item in arguments:
        match = re.fullmatch(
            r"event-(0|[1-9][0-9]*):role-([a-z_]+):roleOrdinal-(0|[1-9][0-9]*):(lstat|open|fstat|read|close):(.+)",
            item,
        )
        if match is None:
            return _SplitFunctionReturn(_configured_finding(index, "callbackArguments"))
        event_ordinal, role, role_ordinal, operation, detail = match.groups()
        ordinal = int(role_ordinal)
        if ordinal >= len(parsed_roles) or parsed_roles[ordinal][1] != role or ordinal < last_role:
            return _SplitFunctionReturn(_configured_finding(index, "callbackArguments"))
        if int(event_ordinal) != role_event_counts[ordinal]:
            return _SplitFunctionReturn(
                _configured_finding(index, "callbackArguments.eventOrdinal")
            )
        path_value = _configured_argument_path(detail)
        if path_value is not None:
            if not _configured_path(path_value):
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.path"))
            if not _configured_role_path(role, path_value):
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.path"))
            if path_value.startswith("fixture-relative:") and role in {
                "discovery",
                "dot_git",
            }:
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.path"))
        if operation == "lstat":
            if (
                path_value is None
                or re.fullmatch(
                    rf"argType-str:path-{re.escape(path_value)}:(dirfd-none|dirfdOpenOrdinal-(0|[1-9][0-9]*))",
                    detail,
                )
                is None
            ):
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.lstat"))
        elif operation == "open":
            if (
                path_value is None
                or re.fullmatch(
                    rf"argTypes-str,int:path-{re.escape(path_value)}:"
                    r"(dirfd-none|dirfdOpenOrdinal-(0|[1-9][0-9]*)):"
                    r"flags-(RDONLY\|NOFOLLOW(?:\|DIRECTORY)?):"
                    r"(result-openOrdinal-(0|[1-9][0-9]*)|result-error-([A-Za-z]+))",
                    detail,
                )
                is None
            ):
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.open"))
        elif operation == "fstat":
            if re.fullmatch(r"argType-int:descriptorOpenOrdinal-(0|[1-9][0-9]*)", detail) is None:
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.fstat"))
        elif operation == "read":
            read_match = re.fullmatch(
                r"argTypes-int,int:descriptorOpenOrdinal-(0|[1-9][0-9]*):"
                r"count-(0|[1-9][0-9]*)",
                detail,
            )
            if read_match is None or int(read_match.group(2)) > 4097:
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.read"))
        elif (
            re.fullmatch(
                r"argType-int:descriptorOpenOrdinal-(0|[1-9][0-9]*):"
                r"(result-ok|result-error-([A-Za-z]+))",
                detail,
            )
            is None
        ):
            return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.close"))
        last_role = ordinal
        role_event_counts[ordinal] += 1
        prefix = ":".join(item.split(":")[:4])
        prefixes.append(prefix)
        callback_rows.append((int(event_ordinal), ordinal, role, operation, detail, path_value))
    if any(count == 0 for count in role_event_counts):
        return _SplitFunctionReturn(_configured_finding(index, "roleEvents"))
    anchor_distances = tuple(
        int(rows[0][5].rsplit("-", 1)[1])
        for role_ordinal in range(len(parsed_roles))
        if (rows := tuple(row for row in callback_rows if row[1] == role_ordinal))
        and rows[0][3] == "open"
        and rows[0][5] is not None
        and rows[0][5].startswith("root-ancestor-distance-")
    )
    if len(anchor_distances) != len(parsed_roles) or len(set(anchor_distances)) != 1:
        return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.rootAnchor"))
    shared_anchor_distance = anchor_distances[0]
    for role_ordinal in range(len(parsed_roles)):
        ancestor_distances = tuple(
            int(row[5].rsplit("-", 1)[1])
            for row in callback_rows
            if row[1] == role_ordinal
            and row[3] == "lstat"
            and row[5] is not None
            and row[5].startswith("root-ancestor-distance-")
        )
        if ancestor_distances and ancestor_distances != tuple(
            range(
                shared_anchor_distance - 1,
                shared_anchor_distance - len(ancestor_distances) - 1,
                -1,
            )
        ):
            return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.rootAnchor"))
    live_by_role: dict[int, list[int]] = {}
    open_paths_by_role: dict[tuple[int, int], str] = {}
    next_open_by_role: dict[int, int] = {}
    last_lstat_path_by_role: dict[int, str] = {}
    previous_callback_by_role: dict[int, tuple[str, str | None]] = {}
    root_anchor_by_role: dict[int, int] = {}
    for event_ordinal, ordinal, _, operation, detail, path_value in callback_rows:
        live = live_by_role.setdefault(ordinal, [])
        next_open = next_open_by_role.setdefault(ordinal, 0)
        if operation in {"lstat", "open"}:
            dirfd = re.search(r":(dirfd-none|dirfdOpenOrdinal-([0-9]+))(?:[:]|$)", detail)
            if dirfd is None:
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.dirfd"))
            if dirfd.group(2) is not None and int(dirfd.group(2)) not in live:
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.dirfd"))
            if dirfd.group(2) is not None:
                assert path_value is not None
                parent_path = open_paths_by_role[(ordinal, int(dirfd.group(2)))]
                if not _configured_child_path(parent_path, path_value):
                    return _SplitFunctionReturn(
                        _configured_finding(index, "callbackArguments.path")
                    )
            elif path_value is None or not path_value.startswith("root-ancestor-distance-"):
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.dirfd"))
            if operation == "lstat":
                assert path_value is not None
                last_lstat_path_by_role[ordinal] = path_value
        if operation == "open":
            opened = re.search(r":result-openOrdinal-([0-9]+)$", detail)
            error = re.search(r":result-error-([^:]+)$", detail)
            if opened is None and error is None:
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.result"))
            root_anchor = (
                event_ordinal == 0
                and opened is not None
                and opened.group(1) == "0"
                and path_value is not None
                and path_value.startswith("root-ancestor-distance-")
                and ":dirfd-none:flags-RDONLY|NOFOLLOW|DIRECTORY:" in detail
            )
            if event_ordinal == 0 and not root_anchor:
                return _SplitFunctionReturn(
                    _configured_finding(index, "callbackArguments.rootAnchor")
                )
            if root_anchor:
                if ordinal in root_anchor_by_role:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "callbackArguments.rootAnchor")
                    )
                root_anchor_by_role[ordinal] = 0
            elif path_value is None or previous_callback_by_role.get(ordinal) != (
                "lstat",
                path_value,
            ):
                return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.path"))
            if opened is not None:
                opened_ordinal = int(opened.group(1))
                if opened_ordinal != next_open:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "callbackArguments.openOrdinal")
                    )
                assert path_value is not None
                assert dirfd is not None
                live.append(opened_ordinal)
                open_paths_by_role[(ordinal, opened_ordinal)] = path_value
                next_open_by_role[ordinal] += 1
        elif operation in {"fstat", "read", "close"}:
            descriptor = re.search(r"descriptorOpenOrdinal-([0-9]+)", detail)
            if descriptor is None or int(descriptor.group(1)) not in live:
                return _SplitFunctionReturn(
                    _configured_finding(index, "callbackArguments.descriptor")
                )
            descriptor_ordinal = int(descriptor.group(1))
            if operation == "close":
                if descriptor_ordinal != live[-1]:
                    return _SplitFunctionReturn(_configured_finding(index, "closeEffects"))
                live.pop()
        previous_callback_by_role[ordinal] = (operation, path_value)
    if any(live for live in live_by_role.values()):
        return _SplitFunctionReturn(_configured_finding(index, "closeEffects"))
    if set(root_anchor_by_role) != set(range(len(parsed_roles))):
        return _SplitFunctionReturn(_configured_finding(index, "callbackArguments.rootAnchor"))
    event_prefixes: list[str] = []
    callback_sources: list[str] = []
    custom_rows: list[tuple[int, int, str, str, str, str | None]] = []
    for item in events:
        if not item.endswith((":system", ":custom")):
            return _SplitFunctionReturn(_configured_finding(index, "callbackEvents"))
        prefix, source = item.rsplit(":", 1)
        event_prefixes.append(prefix)
        callback_sources.append(source)
        matched = next(
            (
                row
                for row, arg in zip(callback_rows, arguments, strict=True)
                if arg.startswith(prefix + ":")
            ),
            None,
        )
        if matched is None:
            return _SplitFunctionReturn(_configured_finding(index, "callbackEvents"))
        if source == "custom":
            custom_rows.append(matched)
    if tuple(event_prefixes) != tuple(prefixes):
        return _SplitFunctionReturn(_configured_finding(index, "callbackEvents"))
    custom_operations = frozenset(
        row[3]
        for row, source in zip(callback_rows, callback_sources, strict=True)
        if source == "custom"
    )
    if custom_operations not in {
        frozenset(),
        frozenset({"lstat"}),
        frozenset({"open"}),
        frozenset({"open", "fstat"}),
        frozenset({"read"}),
        frozenset({"close"}),
    }:
        return _SplitFunctionReturn(_configured_finding(index, "callbackEvents.source"))
    if tuple(callback_sources) != tuple(
        "custom" if row[3] in custom_operations else "system" for row in callback_rows
    ):
        return _SplitFunctionReturn(_configured_finding(index, "callbackEvents.source"))
    # Every result is tied to an actual callback prefix and uses a closed result grammar.
    metadata_prefixes: list[str] = []
    metadata_results: list[str] = []
    for item in metadata:
        parts = item.split(":")
        if len(parts) < 6 or not re.fullmatch(r"event-(0|[1-9][0-9]*)", parts[0]):
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents"))
        prefix = ":".join(parts[:4])
        if prefix not in event_prefixes:
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents"))
        operation = parts[3]
        if parts[4] not in {operation, "post-lstat"}:
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents"))
        result_value = ":".join(parts[4:])
        closed_result = {
            "lstat": (
                r"lstat:(?:ok:(?:symlink|directory|regular|other)|"
                r"error:(?:FileNotFoundError|NotADirectoryError|OSError):(errno|no-errno))|"
                r"post-lstat:(?:identity|type-drift|device-drift|inode-drift):"
                r"(?:symlink|directory|regular|other)"
            ),
            "open": (
                r"open:(?:ok:(?:directory|regular):nofollow|"
                r"error:(?:FileNotFoundError|NotADirectoryError|OSError):(errno|no-errno))"
            ),
            "fstat": (
                r"fstat:(?:(?:identity|type-drift|device-drift|inode-drift|"
                r"stored-parent-(?:dot_git|linked_git_dir|common_dir)-type-drift|"
                r"stored-parent-(?:dot_git|linked_git_dir|common_dir)-device-drift|"
                r"stored-parent-(?:dot_git|linked_git_dir|common_dir)-inode-drift):"
                r"(?:symlink|directory|regular|other)|"
                r"error:(?:FileNotFoundError|NotADirectoryError|OSError):(errno|no-errno))"
            ),
            "read": (
                r"read:(?:bytes:(?:0|[1-9][0-9]*)|type:[A-Za-z]+|"
                r"error:(?:FileNotFoundError|NotADirectoryError|OSError):(errno|no-errno))"
            ),
            "close": (
                r"close:(?:ok|error:(?:FileNotFoundError|NotADirectoryError|OSError):"
                r"(errno|no-errno))"
            ),
        }[operation]
        if re.fullmatch(closed_result, result_value) is None:
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents"))
        if ":error:" in item:
            error_match = re.search(r":error:([^:]+):(errno|no-errno)$", item)
            if (
                error_match is None
                or error_match.group(1) not in EXPECTED_METADATA_CONFIGURED_EXCEPTION_TYPES
            ):
                return _SplitFunctionReturn(_configured_finding(index, "metadataEvents"))
        metadata_prefixes.append(prefix)
        metadata_results.append(result_value)
    if tuple(metadata_prefixes) != tuple(event_prefixes):
        return _SplitFunctionReturn(_configured_finding(index, "metadataEvents"))
    expected_stats = tuple(
        item
        for item, result_value in zip(metadata, metadata_results, strict=True)
        if result_value.startswith(("lstat:", "fstat:", "post-lstat:"))
    )
    if stats != expected_stats:
        return _SplitFunctionReturn(_configured_finding(index, "statEvents"))
    if exceptions != tuple(item for item in metadata if ":error:" in item):
        return _SplitFunctionReturn(_configured_finding(index, "exceptionEvents"))
    expected_closes = tuple(item for item in arguments if ":close:" in item)
    if closes != expected_closes:
        return _SplitFunctionReturn(_configured_finding(index, "closeEffects"))
    semantic_live: dict[int, list[int]] = {}
    eligible_reads: set[tuple[int, int]] = set()
    read_consumed: dict[tuple[int, int], int] = {}
    read_eof: set[tuple[int, int]] = set()
    last_read_path: dict[int, str] = {}
    terminal_roles: set[int] = set()
    global_terminal_role: int | None = None
    lstat_kind_by_role: dict[int, tuple[str, str]] = {}
    open_kind_by_descriptor: dict[tuple[int, int], str] = {}
    post_read_validated: set[tuple[int, int]] = set()
    read_failed: set[tuple[int, int]] = set()
    return (
        receipt,
        roles,
        exceptions,
        closes,
        inter,
        inter_markers,
        reader_roles,
        parsed_roles,
        item,
        prefixes,
        callback_rows,
        event_ordinal,
        role,
        role_ordinal,
        operation,
        detail,
        ordinal,
        path_value,
        open_paths_by_role,
        root_anchor_by_role,
        live,
        opened,
        error,
        root_anchor,
        opened_ordinal,
        descriptor,
        callback_sources,
        custom_rows,
        source,
        custom_operations,
        metadata_results,
        result_value,
        semantic_live,
        eligible_reads,
        read_consumed,
        read_eof,
        last_read_path,
        terminal_roles,
        global_terminal_role,
        lstat_kind_by_role,
        open_kind_by_descriptor,
        post_read_validated,
        read_failed,
    )


def _validate_configured_raw_receipt_part_2(
    index: Any,
    callback_rows: Any,
    event_ordinal: Any,
    role: Any,
    role_ordinal: Any,
    operation: Any,
    detail: Any,
    path_value: Any,
    open_paths_by_role: Any,
    root_anchor_by_role: Any,
    live: Any,
    opened: Any,
    error: Any,
    root_anchor: Any,
    opened_ordinal: Any,
    descriptor: Any,
    metadata_results: Any,
    result_value: Any,
    semantic_live: Any,
    eligible_reads: Any,
    read_consumed: Any,
    read_eof: Any,
    last_read_path: Any,
    terminal_roles: Any,
    global_terminal_role: Any,
    lstat_kind_by_role: Any,
    open_kind_by_descriptor: Any,
    post_read_validated: Any,
    read_failed: Any,
) -> Any:
    identity_validated: set[tuple[int, int]] = set()
    fstat_attempted: set[tuple[int, int]] = set()
    pending_post_lstat: dict[int, tuple[int, int]] = {}
    post_read_complete: set[int] = set()
    successful_opens: list[tuple[int, int, int, str, str]] = []
    for callback, result_value in zip(callback_rows, metadata_results, strict=True):
        event_ordinal, role_ordinal, role, operation, detail, path_value = callback
        live = semantic_live.setdefault(role_ordinal, [])
        if role_ordinal in pending_post_lstat and operation != "lstat":
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.postLstat"))
        if role_ordinal in post_read_complete and operation != "close":
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.postLstat"))
        if global_terminal_role is not None and (
            role_ordinal != global_terminal_role or operation != "close"
        ):
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.failFast"))
        if role_ordinal in terminal_roles and operation != "close":
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.failFast"))
        if operation in {"lstat", "open"}:
            dirfd_match = re.search(r":dirfdOpenOrdinal-([0-9]+)(?::|$)", detail)
            if (
                dirfd_match is not None
                and (
                    role_ordinal,
                    int(dirfd_match.group(1)),
                )
                not in identity_validated
                and root_anchor_by_role.get(role_ordinal) != int(dirfd_match.group(1))
            ):
                return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.fstat"))
        if operation == "lstat" and role_ordinal in lstat_kind_by_role:
            return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.lstat"))
        if operation == "open":
            opened = re.search(r":result-openOrdinal-([0-9]+)$", detail)
            error = re.search(r":result-error-([A-Za-z]+)$", detail)
            flags = re.search(r":flags-([^:]+):", detail)
            assert flags is not None
            expected_lstat = lstat_kind_by_role.pop(role_ordinal, None)
            expected_kind = "directory" if flags.group(1).endswith("|DIRECTORY") else "regular"
            root_anchor = (
                root_anchor_by_role.get(role_ordinal) == 0
                and opened is not None
                and opened.group(1) == "0"
            )
            if not root_anchor and expected_lstat != (path_value, expected_kind):
                return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.open"))
            if opened is not None:
                opened_ordinal = int(opened.group(1))
                if result_value != f"open:ok:{expected_kind}:nofollow":
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.open"))
                assert path_value is not None
                live.append(opened_ordinal)
                open_kind_by_descriptor[(role_ordinal, opened_ordinal)] = expected_kind
                successful_opens.append(
                    (role_ordinal, event_ordinal, opened_ordinal, role, path_value)
                )
            else:
                assert error is not None
                if error.group(1) not in EXPECTED_METADATA_CONFIGURED_EXCEPTION_TYPES:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "callbackArguments.open")
                    )
                if not result_value.startswith(f"open:error:{error.group(1)}:"):
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.open"))
                terminal_roles.add(role_ordinal)
                global_terminal_role = role_ordinal
        elif operation == "lstat":
            if result_value.startswith("lstat:error:"):
                terminal_roles.add(role_ordinal)
                if not (
                    role.startswith("prohibited_")
                    and result_value.startswith("lstat:error:FileNotFoundError:")
                ):
                    global_terminal_role = role_ordinal
            elif result_value == "lstat:ok:symlink":
                terminal_roles.add(role_ordinal)
                global_terminal_role = role_ordinal
            elif result_value.startswith("post-lstat:"):
                if path_value is None or last_read_path.get(role_ordinal) != path_value:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "metadataEvents.postLstat")
                    )
                descriptor_key = next(
                    (
                        (role_ordinal, descriptor)
                        for descriptor in reversed(live)
                        if open_paths_by_role[(role_ordinal, descriptor)] == path_value
                        and (role_ordinal, descriptor) in read_eof
                        and (role_ordinal, descriptor) not in post_read_validated
                    ),
                    None,
                )
                if descriptor_key is None or descriptor_key not in read_eof:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "metadataEvents.postLstat")
                    )
                if pending_post_lstat.pop(role_ordinal, None) != descriptor_key:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "metadataEvents.postLstat")
                    )
                post_read_validated.add(descriptor_key)
                post_read_complete.add(role_ordinal)
                if result_value != "post-lstat:identity:regular":
                    terminal_roles.add(role_ordinal)
                    global_terminal_role = role_ordinal
            else:
                assert path_value is not None
                if role_ordinal in lstat_kind_by_role:
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.lstat"))
                lstat_kind_by_role[role_ordinal] = (
                    path_value,
                    result_value.removeprefix("lstat:ok:"),
                )
        elif operation in {"fstat", "read", "close"}:
            descriptor_match = re.search(r"descriptorOpenOrdinal-([0-9]+)", detail)
            assert descriptor_match is not None
            semantic_descriptor = int(descriptor_match.group(1))
            descriptor_key = (role_ordinal, semantic_descriptor)
            if operation == "fstat":
                if descriptor_key in fstat_attempted:
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.fstat"))
                fstat_attempted.add(descriptor_key)
                opened_kind = open_kind_by_descriptor.get(descriptor_key)
                if result_value == f"fstat:identity:{opened_kind}":
                    identity_validated.add(descriptor_key)
                    if opened_kind == "regular":
                        eligible_reads.add(descriptor_key)
                elif result_value.startswith("fstat:error:") or "-drift:" in result_value:
                    terminal_roles.add(role_ordinal)
                    global_terminal_role = role_ordinal
                    read_failed.add(descriptor_key)
                else:
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.fstat"))
            elif operation == "read":
                if descriptor_key not in eligible_reads or descriptor_key in read_eof:
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.read"))
                count_match = re.search(r":count-([0-9]+)$", detail)
                assert count_match is not None
                consumed = read_consumed.get(descriptor_key, 0)
                count = int(count_match.group(1))
                if count <= 0 or count != 4097 - consumed:
                    return _SplitFunctionReturn(
                        _configured_finding(index, "callbackArguments.read")
                    )
                chunk_match = re.fullmatch(r"read:bytes:([0-9]+)", result_value)
                if chunk_match is None:
                    terminal_roles.add(role_ordinal)
                    global_terminal_role = role_ordinal
                    read_failed.add(descriptor_key)
                else:
                    chunk = int(chunk_match.group(1))
                    if chunk > count:
                        return _SplitFunctionReturn(
                            _configured_finding(index, "metadataEvents.read")
                        )
                    read_consumed[descriptor_key] = consumed + chunk
                    last_read_path[role_ordinal] = open_paths_by_role[descriptor_key]
                    if chunk == 0:
                        if consumed == 0:
                            return _SplitFunctionReturn(
                                _configured_finding(index, "metadataEvents.read")
                            )
                        read_eof.add(descriptor_key)
                        pending_post_lstat[role_ordinal] = descriptor_key
            else:
                argument_error = re.search(r":result-error-([A-Za-z]+)$", detail)
                if argument_error is None:
                    if result_value != "close:ok":
                        return _SplitFunctionReturn(
                            _configured_finding(index, "metadataEvents.close")
                        )
                else:
                    if argument_error.group(1) not in EXPECTED_METADATA_CONFIGURED_EXCEPTION_TYPES:
                        return _SplitFunctionReturn(
                            _configured_finding(index, "callbackArguments.close")
                        )
                    if not result_value.startswith(f"close:error:{argument_error.group(1)}:"):
                        return _SplitFunctionReturn(
                            _configured_finding(index, "metadataEvents.close")
                        )
                    terminal_roles.add(role_ordinal)
                    global_terminal_role = role_ordinal
                if not live or live[-1] != semantic_descriptor:
                    return _SplitFunctionReturn(_configured_finding(index, "closeEffects"))
                if (
                    descriptor_key not in fstat_attempted
                    and root_anchor_by_role.get(role_ordinal) != semantic_descriptor
                ):
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.fstat"))
                if (
                    open_kind_by_descriptor.get(descriptor_key) == "regular"
                    and descriptor_key not in read_failed
                    and descriptor_key not in post_read_validated
                ):
                    return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.read"))
                live.pop()
    if any(live for live in semantic_live.values()):
        return _SplitFunctionReturn(_configured_finding(index, "closeEffects"))
    if lstat_kind_by_role:
        return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.lstat"))
    if pending_post_lstat:
        return _SplitFunctionReturn(_configured_finding(index, "metadataEvents.postLstat"))
    return (
        event_ordinal,
        role,
        role_ordinal,
        operation,
        detail,
        result_value,
        identity_validated,
        successful_opens,
        callback,
        descriptor_match,
    )


def _validate_configured_raw_receipt_part_3(
    index: Any,
    receipt: Any,
    roles: Any,
    exceptions: Any,
    closes: Any,
    inter: Any,
    inter_markers: Any,
    reader_roles: Any,
    parsed_roles: Any,
    item: Any,
    prefixes: Any,
    callback_rows: Any,
    event_ordinal: Any,
    role: Any,
    role_ordinal: Any,
    operation: Any,
    detail: Any,
    ordinal: Any,
    open_paths_by_role: Any,
    callback_sources: Any,
    custom_rows: Any,
    source: Any,
    custom_operations: Any,
    metadata_results: Any,
    result_value: Any,
    identity_validated: Any,
    successful_opens: Any,
    callback: Any,
    descriptor_match: Any,
) -> Any:
    projection: tuple[str, str, str, str]
    observed: tuple[str, str, int, int]
    if inter:
        if len(inter) != 7 or inter[0] != "role=inter-role-mutation":
            return _configured_finding(index, "interRoleEvidence")
        keys = ("afterRole", "path", "beforeType", "afterType", "identityChanged", "triggered")
        values: list[str] = []
        for inter_key, item in zip(keys, inter[1:], strict=True):
            if not item.startswith(inter_key + "="):
                return _configured_finding(index, "interRoleEvidence")
            values.append(item.split("=", 1)[1])
        if len(inter_markers) != 1 or roles != (*reader_roles, inter_markers[0]):
            return _configured_finding(index, "interRoleEvidence.triggerOrdinal")
        relation = next(
            (
                row
                for row in EXPECTED_METADATA_CONFIGURED_INTER_ROLE_RELATIONS
                if row[1:7] == tuple(values)
            ),
            None,
        )
        if relation is None:
            return _configured_finding(index, "interRoleEvidence")
        schedule = next(
            row for row in EXPECTED_METADATA_CONFIGURED_INTER_ROLE_SCHEDULES if row[0] == values[0]
        )
        expected_marker = f"interReceiptOrdinal-{schedule[3] + 1}:afterRole-{values[0]}"
        if inter_markers != (expected_marker,):
            return _configured_finding(index, "interRoleEvidence.triggerOrdinal")
        if (
            tuple(role for _, role in parsed_roles) != schedule[1]
            or tuple(exceptions) != schedule[5]
        ):
            return _configured_finding(index, "roleEvents")
        if custom_operations:
            return _configured_finding(index, "callbackEvents.source")
        projection = ("inter-role", relation[7], relation[8], relation[9])
        target_ordinal = schedule[2]
        trigger_ordinal = schedule[3]
        terminal_ordinal = schedule[4]
        if not all(
            type(ordinal) is int and 0 <= ordinal < len(parsed_roles)
            for ordinal in (target_ordinal, trigger_ordinal, terminal_ordinal)
        ):
            return _configured_finding(index, "interRoleEvidence")
        target_role = parsed_roles[target_ordinal][1]
        if (
            target_role
            != {
                "dot-git": "dot_git",
                "linked-git-dir": "linked_git_dir",
                "common-dir": "common_dir",
            }[relation[7]]
            or parsed_roles[trigger_ordinal][1] != values[0]
            or terminal_ordinal != len(parsed_roles) - 1
        ):
            return _configured_finding(index, "interRoleEvidence")
        terminal_relations = tuple(
            (callback, result_value)
            for callback, result_value in zip(callback_rows, metadata_results, strict=True)
            if callback[1] == terminal_ordinal and result_value.startswith("fstat:stored-parent-")
        )
        if len(terminal_relations) != 1:
            return _configured_finding(index, "interRoleEvidence.terminalRelation")
        terminal_callback, terminal_result = terminal_relations[0]
        terminal_descriptor = re.search(r"descriptorOpenOrdinal-([0-9]+)", terminal_callback[4])
        expected_target_path = {
            "dot-git": "$ROOT/.git",
            "linked-git-dir": (
                "fixture-relative:$TMP/$CASE/source/repository/.git/worktrees/linked"
            ),
            "common-dir": "fixture-relative:$TMP/$CASE/source/repository/.git",
        }[relation[7]]
        expected_parent_role = {
            "dot-git": "dot_git",
            "linked-git-dir": "linked_git_dir",
            "common-dir": "common_dir",
        }[relation[7]]
        target_open_rows = tuple(
            row
            for row in successful_opens
            if row[0] == target_ordinal and row[4] == expected_target_path
        )
        if (
            len(target_open_rows) != 1
            or (
                target_ordinal,
                target_open_rows[0][2],
            )
            not in identity_validated
        ):
            return _configured_finding(index, "interRoleEvidence.targetProvenance")
        if (
            terminal_descriptor is None
            or open_paths_by_role.get((terminal_ordinal, int(terminal_descriptor.group(1))))
            != expected_target_path
            or values[2] != values[3]
            or terminal_result
            not in {
                f"fstat:stored-parent-{expected_parent_role}-device-drift:directory",
                f"fstat:stored-parent-{expected_parent_role}-inode-drift:directory",
            }
        ):
            return _configured_finding(index, "interRoleEvidence.terminalRelation")
        target_open = target_open_rows[0]
        observed = (
            target_open[3],
            target_open[4],
            target_open[0],
            target_open[1],
        )
    else:
        if inter_markers:
            return _configured_finding(index, "roleEvents")
        actual_role_schedule = tuple(role for _, role in parsed_roles)
        if (
            actual_role_schedule
            not in EXPECTED_METADATA_CONFIGURED_NON_INTER_ALLOWED_ROLE_SCHEDULES
        ):
            return _configured_finding(index, "roleEvents")
        if not custom_rows:
            symlink_rows = tuple(
                row
                for row, result_value in zip(callback_rows, metadata_results, strict=True)
                if result_value == "lstat:ok:symlink"
            )
            if len(symlink_rows) != 1:
                return _configured_finding(index, "rawReceipt")
            symlink_row = symlink_rows[0]
            if (
                symlink_row[2] != "discovery"
                or symlink_row[5] is None
                or re.fullmatch(
                    r"root-ancestor-distance-(?:[1-9]|[1-5][0-9]|6[0-4])",
                    symlink_row[5],
                )
                is None
                or symlink_row[1] != len(parsed_roles) - 1
            ):
                return _configured_finding(index, "callbackArguments.path")
            projection = ("filesystem-state", "root-ancestor", "before-discovery", "symlink")
            observed = (
                symlink_row[2],
                symlink_row[5],
                symlink_row[1],
                symlink_row[0],
            )
        else:
            operations = {row[3] for row in custom_rows}
            if operations not in ({"lstat"}, {"open"}, {"open", "fstat"}, {"read"}, {"close"}):
                return _configured_finding(index, "callbackEvents")
            custom_candidates = tuple(
                (row, result_value, ordinal)
                for ordinal, (row, result_value, source) in enumerate(
                    zip(callback_rows, metadata_results, callback_sources, strict=True)
                )
                if source == "custom"
            )
            decisive_candidates = tuple(
                row
                for row, result_value, ordinal in custom_candidates
                if (row[3] == "close" and result_value.startswith("close:error:"))
                or (row[3] == "open" and result_value.startswith("open:error:"))
                or (row[3] == "fstat" and "-drift:" in result_value)
                or (
                    row[3] == "lstat"
                    and (
                        result_value == "lstat:ok:symlink"
                        or result_value.startswith("lstat:error:")
                        or result_value.startswith("post-lstat:")
                        and "-drift:" in result_value
                        or (
                            ordinal + 1 < len(metadata_results)
                            and callback_rows[ordinal + 1][1] == row[1]
                            and callback_rows[ordinal + 1][3] == "open"
                            and metadata_results[ordinal + 1].startswith("open:error:")
                        )
                    )
                )
            )
            if len(decisive_candidates) != 1:
                return _configured_finding(index, "metadataEvents.decisive")
            decisive = decisive_candidates[0]
            event_ordinal, role_ordinal, role, operation, detail, decisive_path = decisive
            if operation in {"fstat", "read", "close"}:
                descriptor_match = re.search(r"descriptorOpenOrdinal-([0-9]+)", detail)
                if descriptor_match is None:
                    return _configured_finding(index, "callbackArguments.descriptor")
                decisive_path = open_paths_by_role.get(
                    (role_ordinal, int(descriptor_match.group(1)))
                )
            if decisive_path is None:
                return _configured_finding(index, "callbackArguments.path")
            if role == "discovery" and decisive_path == "$ROOT":
                target, path = "root", decisive_path
            elif role == "dot_git" and decisive_path == "$ROOT/.git":
                target, path = "dot-git", decisive_path
            elif role == "prohibited_grafts" and decisive_path.endswith("/info"):
                target, path = "info-ancestor", decisive_path
            else:
                return _configured_finding(index, "callbackArguments.path")
            if role_ordinal != len(parsed_roles) - 1:
                return _configured_finding(index, "roleEvents")
            if operation == "lstat":
                decisive_result = metadata_results[callback_rows.index(decisive)]
                if decisive_result.startswith("post-lstat:"):
                    phase = "after-read"
                    effect = decisive_result.split(":", 1)[1].split(":", 1)[0]
                elif decisive_result.startswith("lstat:error:"):
                    phase, effect = "initial-lstat", "os-error"
                else:
                    phase, effect = "after-lstat", "identity-replacement"
            elif operation == "open":
                phase, effect = "initial-open", "os-error"
            elif operation == "close":
                if not any("error-" in row for row in closes):
                    return _configured_finding(index, "closeEffects")
                phase, effect = "cleanup", "os-error"
            elif operation == "fstat":
                decisive_result = metadata_results[callback_rows.index(decisive)]
                if "-drift:" not in decisive_result:
                    return _configured_finding(index, "statEvents")
                phase = "after-open"
                effect = decisive_result.split(":", 1)[1].split(":", 1)[0]
            else:
                phase, effect = "after-read", "device-drift"
            projection = (operation, target, phase, effect)
            observed = (role, path, role_ordinal, event_ordinal)
    return ConfiguredRawIntegrityResult(
        ParsedConfiguredRawReceipt(
            receipt, tuple(prefixes), tuple(successful_opens), projection, observed
        ),
        (),
    )


def validate_configured_raw_receipt(
    raw_receipt: object, stored_identity: object, index: object
) -> ConfiguredRawIntegrityResult:
    _part_1_result = _validate_configured_raw_receipt_part_1(raw_receipt, stored_identity, index)
    if isinstance(_part_1_result, _SplitFunctionReturn):
        return cast(ConfiguredRawIntegrityResult, _part_1_result.value)
    (
        receipt,
        roles,
        exceptions,
        closes,
        inter,
        inter_markers,
        reader_roles,
        parsed_roles,
        item,
        prefixes,
        callback_rows,
        event_ordinal,
        role,
        role_ordinal,
        operation,
        detail,
        ordinal,
        path_value,
        open_paths_by_role,
        root_anchor_by_role,
        live,
        opened,
        error,
        root_anchor,
        opened_ordinal,
        descriptor,
        callback_sources,
        custom_rows,
        source,
        custom_operations,
        metadata_results,
        result_value,
        semantic_live,
        eligible_reads,
        read_consumed,
        read_eof,
        last_read_path,
        terminal_roles,
        global_terminal_role,
        lstat_kind_by_role,
        open_kind_by_descriptor,
        post_read_validated,
        read_failed,
    ) = cast(tuple[Any, ...], _part_1_result)
    _part_2_result = _validate_configured_raw_receipt_part_2(
        index,
        callback_rows,
        event_ordinal,
        role,
        role_ordinal,
        operation,
        detail,
        path_value,
        open_paths_by_role,
        root_anchor_by_role,
        live,
        opened,
        error,
        root_anchor,
        opened_ordinal,
        descriptor,
        metadata_results,
        result_value,
        semantic_live,
        eligible_reads,
        read_consumed,
        read_eof,
        last_read_path,
        terminal_roles,
        global_terminal_role,
        lstat_kind_by_role,
        open_kind_by_descriptor,
        post_read_validated,
        read_failed,
    )
    if isinstance(_part_2_result, _SplitFunctionReturn):
        return cast(ConfiguredRawIntegrityResult, _part_2_result.value)
    (
        event_ordinal,
        role,
        role_ordinal,
        operation,
        detail,
        result_value,
        identity_validated,
        successful_opens,
        callback,
        descriptor_match,
    ) = cast(tuple[Any, ...], _part_2_result)
    return cast(
        ConfiguredRawIntegrityResult,
        _validate_configured_raw_receipt_part_3(
            index,
            receipt,
            roles,
            exceptions,
            closes,
            inter,
            inter_markers,
            reader_roles,
            parsed_roles,
            item,
            prefixes,
            callback_rows,
            event_ordinal,
            role,
            role_ordinal,
            operation,
            detail,
            ordinal,
            open_paths_by_role,
            callback_sources,
            custom_rows,
            source,
            custom_operations,
            metadata_results,
            result_value,
            identity_validated,
            successful_opens,
            callback,
            descriptor_match,
        ),
    )


def project_configured_raw_receipt(
    parsed: ParsedConfiguredRawReceipt,
) -> ConfiguredProjectionResult:
    """Project only an already validated receipt."""
    if type(parsed) is not ParsedConfiguredRawReceipt:
        return ConfiguredProjectionResult(None, configured_receipt_finding(0, "rawReceipt"))
    return ConfiguredProjectionResult(parsed.projection, ())


def bind_configured_plan(
    raw_receipt: object,
    stored_identity: object,
    stored_observation: object,
    claimed_projection: object,
    declared_plan: object,
    index: object,
) -> tuple[protocol.Finding, ...]:
    validated = validate_configured_raw_receipt(raw_receipt, stored_identity, index)
    if validated.findings:
        return validated.findings
    assert validated.parsed is not None
    safe_index = cast(int, index)
    if type(stored_observation) is not tuple or len(stored_observation) != 4:
        return configured_receipt_finding(safe_index, "observedTargetRole")
    if any(
        type(value) is not expected
        for value, expected in zip(stored_observation, (str, str, int, int), strict=True)
    ):
        return configured_receipt_finding(safe_index, "observedTargetRole")
    if stored_observation != validated.parsed.observed:
        for coordinate, actual, expected in zip(
            (
                "observedTargetRole",
                "observedTargetPath",
                "observedRoleOrdinal",
                "observedCallbackOrdinal",
            ),
            cast(tuple[object, ...], stored_observation),
            validated.parsed.observed,
            strict=True,
        ):
            if actual != expected:
                return configured_receipt_finding(safe_index, coordinate)
    for value, coordinate in ((claimed_projection, "callback"), (declared_plan, "callback")):
        if (
            type(value) is not tuple
            or len(value) != 4
            or any(type(item) is not str for item in value)
        ):
            return configured_receipt_finding(safe_index, coordinate)
    for coordinate, claimed, observed in zip(
        EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS,
        cast(tuple[str, ...], claimed_projection),
        validated.parsed.projection,
        strict=True,
    ):
        if claimed != observed:
            return configured_receipt_finding(safe_index, coordinate)
    for coordinate, actual, declared in zip(
        EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS,
        cast(tuple[str, ...], claimed_projection),
        cast(tuple[str, ...], declared_plan),
        strict=True,
    ):
        if actual != declared:
            return configured_receipt_finding(safe_index, coordinate)
    return ()


def bind_configured_receipt_schedule(
    execution_evidence_identity: object,
    raw_identity: object,
    observed: object,
    projection: object,
    index: object,
) -> tuple[protocol.Finding, ...]:
    """Bind a parsed receipt to its independently frozen execution slot."""
    if type(index) is not int or not 0 <= index < len(
        EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDINGS
    ):
        return configured_receipt_finding(0, "receiptIndex")
    safe_index = index
    expected = EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDINGS[safe_index]
    if type(execution_evidence_identity) is not str or execution_evidence_identity != expected[0]:
        return configured_receipt_finding(safe_index, "executionEvidenceIdentity")
    if type(raw_identity) is not str or raw_identity != expected[1]:
        return configured_receipt_finding(safe_index, "rawEvidenceIdentity")
    for value, required, coordinate in (
        (observed, expected[2], "observedTargetRole"),
        (projection, expected[3], "callback"),
    ):
        if type(value) is not tuple or value != required:
            return configured_receipt_finding(safe_index, coordinate)
    return ()


def execute_discovery_handoff_mutant(
    reader: Callable[..., protocol.GitMetadataReadResult],
    root: Path,
    operation: str,
) -> tuple[tuple[protocol.Finding, ...], tuple[tuple[str, str], ...]]:
    """Execute one exact malformed discovery-to-dot-git provenance handoff."""
    root_status = root.lstat()
    parent_role = "discovery"
    if operation == "remove-parent-record":
        parents: tuple[tuple[str, protocol.GitMetadataRecord], ...] = ()
    else:
        if operation == "replace-discovery-role":
            parent_role = "common_dir"
        path = root.parent if "path" in operation else root
        mode = stat.S_IFREG | 0o600 if "type" in operation else root_status.st_mode
        device = root_status.st_dev + (1 if "device" in operation else 0)
        inode = root_status.st_ino + (1 if operation == "replace-root-inode" else 0)
        parents = (
            (
                parent_role,
                protocol.GitMetadataRecord(path, None, mode, device, inode),
            ),
        )
    callbacks: list[tuple[str, str]] = []
    descriptor_paths: dict[int, str] = {}
    system_io = protocol.SYSTEM_METADATA_IO

    def observed_lstat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        callbacks.append(("lstat", path))
        return system_io.lstat(path, dir_fd=dir_fd)

    def observed_open(path: str, flags: int, *, dir_fd: int | None = None) -> int:
        callbacks.append(("open", path))
        descriptor = system_io.open(path, flags, dir_fd=dir_fd)
        descriptor_paths[descriptor] = path
        return descriptor

    def observed_fstat(descriptor: int) -> os.stat_result:
        callbacks.append(("fstat", descriptor_paths[descriptor]))
        return system_io.fstat(descriptor)

    def observed_read(descriptor: int, count: int) -> bytes:
        callbacks.append(("read", f"{descriptor_paths[descriptor]}:{count}"))
        return system_io.read(descriptor, count)

    def observed_close(descriptor: int) -> None:
        callbacks.append(("close", descriptor_paths[descriptor]))
        system_io.close(descriptor)

    observed = reader(
        root,
        provenance=protocol.GitMetadataProvenance("dot_git", None, parents),
        io=protocol.MetadataIO(
            observed_lstat,
            observed_open,
            observed_fstat,
            observed_read,
            observed_close,
        ),
    )
    return observed.findings, tuple(callbacks)


def apply_configured_receipt_mutant(
    receipt: ConfiguredPlanReceipt,
    declared_plan: tuple[str, ...],
    receipt_index: int,
    operation: str,
    raw_identity_action: str,
) -> tuple[object, object, object, object, object, object]:
    """Apply one catalogued single-coordinate mutation to a frozen receipt."""
    raw: list[object] = list(receipt[1:9])
    identity: object = receipt[9]
    observed: object = tuple(receipt[14:18])
    projection: object = tuple(receipt[10:14])
    declared: object = declared_plan
    index: object = receipt_index

    def shift_role_events(role_ordinal: int, first_event: int, delta: int) -> None:
        marker = f":roleOrdinal-{role_ordinal}:"
        for field_ordinal in range(7):
            shifted: list[str] = []
            for value in cast(tuple[str, ...], raw[field_ordinal]):
                event = re.match(r"event-([0-9]+):", value)
                if event is not None and marker in value and int(event.group(1)) >= first_event:
                    value = re.sub(
                        r"^event-[0-9]+:",
                        f"event-{int(event.group(1)) + delta}:",
                        value,
                    )
                shifted.append(value)
            raw[field_ordinal] = tuple(shifted)

    if operation == "index-bool":
        index = True
    elif operation == "index-string":
        index = "14"
    elif operation == "index-negative":
        index = -1
    elif operation == "index-count":
        index = EXPECTED_METADATA_CONFIGURED_PLAN_COUNT
    elif operation == "index-count-plus-one":
        index = EXPECTED_METADATA_CONFIGURED_PLAN_COUNT + 1
    elif operation == "raw-list":
        raw = list(raw)
    elif operation == "raw-short":
        raw = raw[:-1]
    elif operation == "raw-long":
        raw.append(())
    elif match := re.fullmatch(r"field-list-([0-7])", operation):
        field_ordinal = int(match.group(1))
        raw[field_ordinal] = list(cast(tuple[object, ...], raw[field_ordinal]))
    elif match := re.fullmatch(r"field-over-cap-([0-7])", operation):
        field_ordinal = int(match.group(1))
        field_name = EXPECTED_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS[field_ordinal]
        raw[field_ordinal] = ("x",) * (
            dict(EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS)[field_name] + 1
        )
    elif match := re.fullmatch(r"field-item-type-([0-7])", operation):
        field_ordinal = int(match.group(1))
        raw[field_ordinal] = (1,)
    elif operation == "field-invalid-utf8":
        raw[0] = ("\ud800",)
    elif operation == "preserve-stale-identity":
        raw[4] = cast(tuple[object, ...], raw[4])[:-1]
    elif operation == "role-empty":
        raw[2] = ()
    elif operation == "role-first-not-discovery":
        roles = list(cast(tuple[str, ...], raw[2]))
        roles[0] = roles[0].replace(":discovery", ":dot_git")
        raw[2] = tuple(roles)
    elif operation == "role-ordinal-duplicate":
        roles = list(cast(tuple[str, ...], raw[2]))
        roles[1] = re.sub(r"^[0-9]+:", "0:", roles[1])
        raw[2] = tuple(roles)
    elif operation == "role-reentered":
        role_tuple = cast(tuple[str, ...], raw[2])
        raw[2] = (*role_tuple, f"{len(role_tuple)}:discovery")
    elif operation == "callback-reorder":
        events = list(cast(tuple[str, ...], raw[1]))
        events[0], events[1] = events[1], events[0]
        raw[1] = tuple(events)
    elif operation == "callback-event-gap":
        arguments = list(cast(tuple[str, ...], raw[0]))
        arguments[1] = re.sub(r"^event-[0-9]+", "event-99", arguments[1])
        raw[0] = tuple(arguments)
    elif operation == "custom-add-operation":
        events = list(cast(tuple[str, ...], raw[1]))
        system_ordinal = next(
            ordinal for ordinal, value in enumerate(events) if value.endswith(":system")
        )
        events[system_ordinal] = events[system_ordinal].removesuffix(":system") + ":custom"
        raw[1] = tuple(events)
    elif operation == "custom-remove-operation":
        events = list(cast(tuple[str, ...], raw[1]))
        custom_ordinal = next(
            ordinal for ordinal, value in enumerate(events) if value.endswith(":custom")
        )
        events[custom_ordinal] = events[custom_ordinal].removesuffix(":custom") + ":system"
        raw[1] = tuple(events)
    elif operation in {"path-root-prefix", "path-dotdot", "path-cross-role"}:
        arguments = list(cast(tuple[str, ...], raw[0]))
        if operation == "path-root-prefix":
            arguments[0] = re.sub(r"root-ancestor-distance-[0-9]+", "$ROOTevil", arguments[0])
        elif operation == "path-dotdot":
            target_ordinal = next(
                ordinal for ordinal, value in enumerate(arguments) if "$ROOT/.git" in value
            )
            arguments[target_ordinal] = arguments[target_ordinal].replace(
                "$ROOT/.git", "$ROOT/../evil"
            )
        else:
            target_ordinal = next(
                ordinal for ordinal, value in enumerate(arguments) if "$ROOT/.git" in value
            )
            arguments[target_ordinal] = arguments[target_ordinal].replace("$ROOT/.git", "$COMMON")
        raw[0] = tuple(arguments)
    elif operation == "root-anchor-rebase":
        arguments = list(cast(tuple[str, ...], raw[0]))
        match = re.search(r"root-ancestor-distance-([0-9]+)", arguments[0])
        assert match is not None and int(match.group(1)) > 1
        arguments[0] = arguments[0].replace(
            match.group(0), f"root-ancestor-distance-{int(match.group(1)) - 1}"
        )
        raw[0] = tuple(arguments)
    elif operation in {"anchor-dirfd", "anchor-flags", "anchor-result"}:
        arguments = list(cast(tuple[str, ...], raw[0]))
        anchor_ordinal = next(
            ordinal
            for ordinal, value in enumerate(arguments)
            if ":open:" in value and ":dirfd-none:" in value
        )
        replacements = {
            "anchor-dirfd": (":dirfd-none:", ":dirfdOpenOrdinal-0:"),
            "anchor-flags": (
                ":flags-RDONLY|NOFOLLOW|DIRECTORY:",
                ":flags-RDONLY|NOFOLLOW:",
            ),
            "anchor-result": (":result-openOrdinal-0", ":result-error-OSError"),
        }
        before, after = replacements[operation]
        arguments[anchor_ordinal] = arguments[anchor_ordinal].replace(before, after)
        raw[0] = tuple(arguments)
    elif operation == "anchor-final-close-omit":
        argument_tuple = cast(tuple[str, ...], raw[0])
        close_ordinal = next(
            ordinal
            for ordinal in range(len(argument_tuple) - 1, -1, -1)
            if ":close:" in argument_tuple[ordinal]
            and ":descriptorOpenOrdinal-0:" in argument_tuple[ordinal]
        )
        close_prefix = ":".join(argument_tuple[close_ordinal].split(":")[:4])
        for field_ordinal in (0, 1, 3, 6):
            raw[field_ordinal] = tuple(
                value
                for value in cast(tuple[str, ...], raw[field_ordinal])
                if not value.startswith(close_prefix + ":")
            )
    elif operation == "later-role-after-terminal":
        for field_ordinal in (0, 1, 3, 4, 6):
            source_rows = tuple(
                value
                for value in cast(tuple[str, ...], raw[field_ordinal])
                if ":roleOrdinal-0:" in value
            )
            raw[field_ordinal] = (
                *cast(tuple[str, ...], raw[field_ordinal]),
                *(
                    value.replace(":role-discovery:", ":role-common_dir:").replace(
                        ":roleOrdinal-0:", ":roleOrdinal-2:"
                    )
                    for value in source_rows
                ),
            )
        raw[2] = (*cast(tuple[str, ...], raw[2]), "2:common_dir")
    elif operation == "descriptor-unknown":
        arguments = list(cast(tuple[str, ...], raw[0]))
        descriptor_ordinal = next(
            ordinal for ordinal, value in enumerate(arguments) if ":fstat:" in value
        )
        arguments[descriptor_ordinal] = re.sub(
            r"descriptorOpenOrdinal-[0-9]+$",
            "descriptorOpenOrdinal-99",
            arguments[descriptor_ordinal],
        )
        raw[0] = tuple(arguments)
    elif operation == "descriptor-reuse":
        arguments = list(cast(tuple[str, ...], raw[0]))
        open_ordinals = [ordinal for ordinal, value in enumerate(arguments) if ":open:" in value]
        arguments[open_ordinals[1]] = re.sub(
            r"result-openOrdinal-[0-9]+$",
            "result-openOrdinal-0",
            arguments[open_ordinals[1]],
        )
        raw[0] = tuple(arguments)
    elif operation == "stat-omit":
        raw[4] = cast(tuple[str, ...], raw[4])[:-1]
    elif operation == "exception-add":
        raw[5] = (
            *cast(tuple[str, ...], raw[5]),
            "event-0:role-discovery:roleOrdinal-0:lstat:lstat:error:OSError:no-errno",
        )
    elif operation == "close-reorder":
        raw[6] = tuple(reversed(cast(tuple[str, ...], raw[6])))
    elif operation == "close-result-mismatch":
        raw[6] = tuple(
            re.sub(r"result-error-[A-Za-z]+$", "result-ok", value)
            for value in cast(tuple[str, ...], raw[6])
        )
    elif operation in {"read-count-zero", "read-count-wrong"}:
        arguments = list(cast(tuple[str, ...], raw[0]))
        read_ordinal = next(ordinal for ordinal, value in enumerate(arguments) if ":read:" in value)
        count_match = re.search(r":count-([0-9]+)$", arguments[read_ordinal])
        assert count_match is not None
        replacement = 0 if operation == "read-count-zero" else int(count_match.group(1)) - 1
        arguments[read_ordinal] = re.sub(
            r":count-[0-9]+$", f":count-{replacement}", arguments[read_ordinal]
        )
        raw[0] = tuple(arguments)
    elif operation in {"read-chunk-oversize", "read-zero-first"}:
        metadata = list(cast(tuple[str, ...], raw[3]))
        read_ordinal = next(
            ordinal for ordinal, value in enumerate(metadata) if ":read:read:bytes:" in value
        )
        chunk_replacement = "9999" if operation == "read-chunk-oversize" else "0"
        metadata[read_ordinal] = re.sub(
            r"read:bytes:[0-9]+$",
            f"read:bytes:{chunk_replacement}",
            metadata[read_ordinal],
        )
        raw[3] = tuple(metadata)
    elif operation == "read-eof-omit":
        metadata_tuple = cast(tuple[str, ...], raw[3])
        remove_ordinal = next(
            ordinal
            for ordinal, value in enumerate(metadata_tuple)
            if value.endswith("read:bytes:0")
        )
        removed = metadata_tuple[remove_ordinal]
        event_ordinal = int(removed.split(":", 1)[0].removeprefix("event-"))
        role_match = re.search(r":roleOrdinal-([0-9]+):", removed)
        assert role_match is not None
        role_ordinal = int(role_match.group(1))
        for field_ordinal in (0, 1, 3):
            values = list(cast(tuple[str, ...], raw[field_ordinal]))
            values.pop(remove_ordinal)
            raw[field_ordinal] = tuple(values)
        shift_role_events(role_ordinal, event_ordinal + 1, -1)
    elif operation == "read-work-after-post":
        metadata_tuple = cast(tuple[str, ...], raw[3])
        post_ordinal = next(
            ordinal for ordinal, value in enumerate(metadata_tuple) if ":post-lstat:" in value
        )
        post = metadata_tuple[post_ordinal]
        role_match = re.search(r":roleOrdinal-([0-9]+):", post)
        assert role_match is not None
        role_ordinal = int(role_match.group(1))
        event_ordinal = int(post.split(":", 1)[0].removeprefix("event-")) + 1
        prior_lstat_ordinal = next(
            ordinal
            for ordinal in range(post_ordinal - 1, -1, -1)
            if f":roleOrdinal-{role_ordinal}:lstat:" in cast(tuple[str, ...], raw[0])[ordinal]
        )
        first_lstat = cast(tuple[str, ...], raw[0])[prior_lstat_ordinal]
        first_result = metadata_tuple[prior_lstat_ordinal]
        shift_role_events(role_ordinal, event_ordinal, 1)
        prefix = f"event-{event_ordinal}:role-{post.split(':role-', 1)[1].split(':', 1)[0]}:roleOrdinal-{role_ordinal}:lstat"
        argument = prefix + ":" + first_lstat.split(":lstat:", 1)[1]
        result = prefix + ":" + first_result.split(":lstat:", 1)[1]
        for field_ordinal, value in (
            (0, argument),
            (1, prefix + ":custom"),
            (3, result),
            (4, result),
        ):
            values = list(cast(tuple[str, ...], raw[field_ordinal]))
            insert_at = post_ordinal + 1 if field_ordinal != 4 else len(values)
            values.insert(insert_at, value)
            raw[field_ordinal] = tuple(values)
    elif operation == "fstat-duplicate":
        metadata_tuple = cast(tuple[str, ...], raw[3])
        fstat_ordinal = next(
            ordinal for ordinal, value in enumerate(metadata_tuple) if ":fstat:fstat:" in value
        )
        original = metadata_tuple[fstat_ordinal]
        role_match = re.search(r":roleOrdinal-([0-9]+):", original)
        assert role_match is not None
        role_ordinal = int(role_match.group(1))
        event_ordinal = int(original.split(":", 1)[0].removeprefix("event-")) + 1
        shift_role_events(role_ordinal, event_ordinal, 1)
        for field_ordinal in (0, 1, 3):
            values = list(cast(tuple[str, ...], raw[field_ordinal]))
            copied = values[fstat_ordinal]
            copied = re.sub(r"^event-[0-9]+:", f"event-{event_ordinal}:", copied)
            values.insert(fstat_ordinal + 1, copied)
            raw[field_ordinal] = tuple(values)
        stats = list(cast(tuple[str, ...], raw[4]))
        stat_ordinal = next(ordinal for ordinal, value in enumerate(stats) if value == original)
        copied_stat = re.sub(r"^event-[0-9]+:", f"event-{event_ordinal}:", original)
        stats.insert(stat_ordinal + 1, copied_stat)
        raw[4] = tuple(stats)
    elif operation == "metadata-reorder":
        metadata = list(cast(tuple[str, ...], raw[3]))
        metadata[0], metadata[1] = metadata[1], metadata[0]
        raw[3] = tuple(metadata)
    elif operation.startswith("inter-"):
        inter_values = list(cast(tuple[str, ...], raw[7]))
        inter_operations = {
            "inter-leading-key": (0, "role=other"),
            "inter-after-role": (1, "afterRole=dot_git"),
            "inter-path": (2, "path=$TMP/$CASE/repository/.git"),
            "inter-before-type": (3, "beforeType=32768"),
            "inter-after-type": (4, "afterType=32768"),
            "inter-identity": (5, "identityChanged=false"),
            "inter-triggered": (6, "triggered=false"),
        }
        if operation in inter_operations:
            inter_ordinal, inter_replacement = inter_operations[operation]
            inter_values[inter_ordinal] = inter_replacement
            raw[7] = tuple(inter_values)
        elif operation in {"inter-marker-before", "inter-marker-after"}:
            roles = list(cast(tuple[str, ...], raw[2]))
            marker_ordinal = next(
                ordinal
                for ordinal, value in enumerate(roles)
                if value.startswith("interReceiptOrdinal-")
            )
            observed_marker = re.match(r"interReceiptOrdinal-([0-9]+)", roles[marker_ordinal])
            assert observed_marker is not None
            delta = -1 if operation.endswith("before") else 1
            roles[marker_ordinal] = re.sub(
                r"interReceiptOrdinal-[0-9]+",
                f"interReceiptOrdinal-{int(observed_marker.group(1)) + delta}",
                roles[marker_ordinal],
            )
            raw[2] = tuple(roles)
        elif operation == "inter-marker-physical-reorder":
            roles = list(cast(tuple[str, ...], raw[2]))
            marker = roles.pop()
            roles.insert(1, marker)
            raw[2] = tuple(roles)
        elif operation == "inter-arm-missing":
            raw[7] = tuple(inter_values[:-1])
        elif operation == "inter-arm-extra":
            raw[7] = (*inter_values, "extra=true")
        elif operation == "inter-arm-reorder":
            inter_values[1], inter_values[2] = inter_values[2], inter_values[1]
            raw[7] = tuple(inter_values)
        elif operation == "inter-terminal-success":
            raw[3] = tuple(
                re.sub(
                    r"fstat:stored-parent-[a-z_]+-(?:device|inode)-drift:directory$",
                    "fstat:identity:directory",
                    value,
                )
                for value in cast(tuple[str, ...], raw[3])
            )
            raw[4] = tuple(
                re.sub(
                    r"fstat:stored-parent-[a-z_]+-(?:device|inode)-drift:directory$",
                    "fstat:identity:directory",
                    value,
                )
                for value in cast(tuple[str, ...], raw[4])
            )
        elif operation == "inter-parent-role":
            raw[3] = tuple(
                value.replace("stored-parent-linked_git_dir", "stored-parent-common_dir")
                for value in cast(tuple[str, ...], raw[3])
            )
            raw[4] = tuple(
                value.replace("stored-parent-linked_git_dir", "stored-parent-common_dir")
                for value in cast(tuple[str, ...], raw[4])
            )
        elif operation == "inter-target-provenance":
            target_path = "fixture-relative:$TMP/$CASE/source/repository/.git/worktrees/linked"
            removed_prefixes = {
                ":".join(value.split(":")[:4])
                for value in cast(tuple[str, ...], raw[0])
                if ":role-linked_git_dir:" in value
                and (
                    f":path-{target_path}:" in value
                    or re.search(r":descriptorOpenOrdinal-23(?::|$)", value) is not None
                )
            }
            kept_arguments = tuple(
                value
                for value in cast(tuple[str, ...], raw[0])
                if ":".join(value.split(":")[:4]) not in removed_prefixes
            )
            prefix_map: dict[str, str] = {}
            next_event = 0
            for value in kept_arguments:
                old_prefix = ":".join(value.split(":")[:4])
                if ":role-linked_git_dir:" in value:
                    prefix_map[old_prefix] = re.sub(
                        r"^event-[0-9]+", f"event-{next_event}", old_prefix
                    )
                    next_event += 1
            for field_ordinal in range(7):
                rewritten: list[str] = []
                for value in cast(tuple[str, ...], raw[field_ordinal]):
                    old_prefix = ":".join(value.split(":")[:4])
                    if old_prefix in removed_prefixes:
                        continue
                    if old_prefix in prefix_map:
                        value = prefix_map[old_prefix] + value[len(old_prefix) :]
                    rewritten.append(value)
                raw[field_ordinal] = tuple(rewritten)
        else:
            raise AssertionError(operation)
    elif match := re.fullmatch(r"observed-coordinate-([0-3])", operation):
        mutated_values = list(cast(tuple[object, ...], observed))
        ordinal = int(match.group(1))
        mutated_values[ordinal] = -1 if ordinal >= 2 else "decoy"
        observed = tuple(mutated_values)
    elif match := re.fullmatch(r"projection-coordinate-([0-3])", operation):
        mutated_values = list(cast(tuple[object, ...], projection))
        mutated_values[int(match.group(1))] = "decoy"
        projection = tuple(mutated_values)
    elif match := re.fullmatch(r"declared-coordinate-([0-3])", operation):
        mutated_values = list(cast(tuple[object, ...], declared))
        mutated_values[int(match.group(1))] = "decoy"
        declared = tuple(mutated_values)
    elif operation == "replace-custom-callback-with-other-closed-callback":
        raw[1] = tuple(
            value.replace(":fstat:custom", ":open:custom")
            for value in cast(tuple[str, ...], raw[1])
        )
    elif operation == "replace-callback-target-argument":
        raw[0] = tuple(
            value.replace("$ROOT/.git", "$COMMON") for value in cast(tuple[str, ...], raw[0])
        )
    elif operation == "replace-callback-event-ordinal":
        raw[0] = tuple(
            re.sub(r"^event-[0-9]+", "event-99", value) if ":fstat:" in value else value
            for value in cast(tuple[str, ...], raw[0])
        )
    elif operation == "replace-stat-effect-evidence":
        raw[4] = tuple(
            value.replace("type-drift", "inode-drift") for value in cast(tuple[str, ...], raw[4])
        )
    elif operation == "remove-custom-callback-trigger":
        raw[1] = tuple(
            value.replace(":custom", ":system") for value in cast(tuple[str, ...], raw[1])
        )
    elif operation == "replace-observed-close-error-with-ok":
        raw[6] = tuple(
            re.sub(r"result-error-[^:]+$", "result-ok", value)
            for value in cast(tuple[str, ...], raw[6])
        )
    elif operation == "replace-triggered-before-after-observation-with-unchanged":
        raw[7] = tuple(
            "identityChanged=false" if value == "identityChanged=true" else value
            for value in cast(tuple[str, ...], raw[7])
        )
    elif operation == "replace-declared-plan-after-raw-projection":
        mutated_values = list(cast(tuple[object, ...], declared))
        mutated_values[3] = "decoy"
        declared = tuple(mutated_values)
    elif operation == "copy-declared-decoy-instead-of-projecting-raw-receipt":
        mutated_values = list(cast(tuple[object, ...], declared))
        mutated_values[3] = "decoy"
        declared = tuple(mutated_values)
        projection = declared
    else:
        raise AssertionError(operation)
    raw_object: object = tuple(raw)
    if operation == "raw-list":
        raw_object = raw
    if raw_identity_action == "recompute-after-mutation":
        identity = hashlib.sha256(canonical(raw_object)).hexdigest()
    else:
        assert raw_identity_action == "preserve-stale"
    return raw_object, identity, observed, projection, declared, index


def historical_pair_containment(
    pair: tuple[str, str],
    classes: tuple[tuple[str, tuple[str, ...]], ...],
    index: int,
) -> tuple[str | None, tuple[protocol.Finding, ...]]:
    containing = tuple(name for name, members in classes if set(pair) <= set(members))
    if len(containing) != 1:
        return (
            None,
            (
                protocol.Finding(
                    "evidence",
                    "CURRENT",
                    "ACP.EVIDENCE.HISTORICAL_PAIR_RELATION",
                    f"configuredRemovedHistoricalPairs[{index}]",
                ),
            ),
        )
    return containing[0], ()


def reread_matrix_with_controlled_decoy(
    path: Path,
    decoy: bytes,
    *,
    substitute_decoy: bool,
) -> tuple[bytes, bytes]:
    """Return the independently reread bytes and the controlled selected evidence."""
    reread = path.read_bytes()
    return reread, decoy if substitute_decoy else reread


def observed_matrix_schema_evidence(payload: bytes, expected_schema: str) -> tuple[str, str]:
    parsed = json.loads(payload.decode("utf-8", errors="strict"))
    assert type(parsed) is dict
    assert canonical(parsed) + b"\n" == payload
    schema = parsed["schemaVersion"]
    assert type(schema) is str
    descriptor = (
        "matrix-schema-version-wrong"
        if schema != expected_schema
        else "matrix-schema-version-current"
    )
    identity = hashlib.sha256(canonical({"schemaVersion": schema})).hexdigest()
    return descriptor, identity


def normalize_document_overclaim(value: str) -> str:
    """Apply the frozen bounded ASCII/Markdown/spacing normalization."""
    ascii_lowered = "".join(
        chr(ord(character) + 32) if "A" <= character <= "Z" else character for character in value
    )
    emphasis_removed = re.sub(r"[*_`]", "", ascii_lowered)
    return re.sub(r"[\s-]+", " ", emphasis_removed).strip()


def document_overclaim_variants() -> tuple[tuple[str, str, str, str], ...]:
    rows: list[tuple[str, str, str, str]] = []
    for family, phrases in EXPECTED_DOCUMENT_PROHIBITED_FAMILY_GRAMMAR:
        canonical_phrase, synonym = phrases
        variants = (
            ("case", canonical_phrase.upper()),
            ("whitespace", " \t\n ".join(canonical_phrase.split(" "))),
            ("hyphen", "-".join(canonical_phrase.split(" "))),
            ("markdown", " ".join(f"**{word}**" for word in canonical_phrase.split(" "))),
            ("bounded-synonym", synonym),
            (
                "case+markdown+hyphen",
                "-".join(f"**{word.upper()}**" for word in canonical_phrase.split(" ")),
            ),
            (
                "bounded-synonym+markdown+hyphen",
                "-".join(f"_{word}_" for word in synonym.split(" ")),
            ),
            ("backtick-only", f"`{canonical_phrase}`"),
            ("edge-whitespace-only", f" \t{canonical_phrase}\n "),
            (
                "case+markdown+hyphen+backtick+edge-whitespace",
                " \t"
                + "-".join(f"`**{word.upper()}**`" for word in canonical_phrase.split(" "))
                + "\n ",
            ),
            (
                "bounded-synonym+markdown+hyphen+backtick+edge-whitespace",
                " \t" + "-".join(f"`_{word}_`" for word in synonym.split(" ")) + "\n ",
            ),
        )
        for axis, variant in variants:
            normalized = normalize_document_overclaim(variant)
            expected_normalized = (
                synonym if axis.startswith("bounded-synonym") else canonical_phrase
            )
            assert normalized == expected_normalized
            rows.append((family, axis, variant, normalized))
    return tuple(rows)


def finding(stage: str, code: str, location: str) -> tuple[protocol.Finding, ...]:
    return (protocol.Finding(stage, "CURRENT", code, location),)


def apply_textual_transform(
    role: str,
    transform: str,
    freeze: dict[str, Any],
    base: bytes,
) -> bytes:
    if transform == "missing_lf":
        assert role != "merge_scan"
        assert base.endswith(b"\n")
        return base[:-1]
    if transform == "crlf":
        return b"\r\n" if role == "merge_scan" else base.replace(b"\n", b"\r\n")
    if transform == "extra_line":
        if role == "merge_scan":
            return (b"e" * 40) + b"\n" + (b"f" * 40) + b"\n"
        return base + b"x\n"
    if transform == "valid_token":
        if role == "head":
            red_head = freeze["redHead"]
            assert type(red_head) is str
            return red_head.encode() + b"\n"
        if role == "red_type":
            return b"blob\n"
        if role == "red_size":
            return str(int(base[:-1]) + 1).encode() + b"\n"
        if role == "merge_scan":
            return (b"f" * 40) + b"\n"
        if role == "ancestry_chain":
            first, second = base.split(b" ", 1)
            replacement = (b"f" * 40) if first != (b"f" * 40) else (b"e" * 40)
            return replacement + b" " + second
        if role == "red_objects":
            first, *remaining = base.splitlines(keepends=True)
            replacement = (b"f" * 40) + b"\n"
            if first == replacement:
                replacement = (b"e" * 40) + b"\n"
            return replacement + b"".join(remaining)
        if role == "c3_freeze_size":
            return str(int(base[:-1]) + 1).encode() + b"\n"
        if role == "red_author":
            return b"other@example.com\n"
        return b"sha2\n"
    corruptions = {
        "object_format": b"Sha2\n",
        "head": b"A" + base[1:],
        "red_type": b"Commit\n",
        "red_size": base[:-2] + b"x\n",
        "merge_scan": (b"F" * 40) + b"\n",
        "ancestry_chain": b"A" + base[1:],
        "red_objects": b"A" + base[1:],
        "c3_freeze_size": base[:-2] + b"x\n",
        "red_author": b"other.example.com\n",
    }
    assert transform == "corrupt_token"
    return corruptions[role]


def normalized_git_text_bytes(
    role: str,
    payload: bytes,
    expected_oid_values: dict[str, bytes],
) -> tuple[bytes, tuple[str, ...]]:
    """Replace only exact OIDs at the seven independently frozen coordinates."""
    normalized, observed_names, _ = position_bound_git_tokens(role, payload, expected_oid_values)
    return normalized, observed_names


def position_bound_git_tokens(
    role: str,
    payload: bytes,
    expected_oid_values: dict[str, bytes],
) -> tuple[bytes, tuple[str, ...], tuple[str, ...]]:
    mappings = tuple(row for row in EXPECTED_VERIFIED_GIT_OID_MAPPINGS if row[0] == role)
    if not mappings:
        raw_hostile = tuple(
            token.decode("ascii")
            for token in re.findall(rb"(?<![0-9A-Za-z])[0-9A-Fa-f]{40}(?![0-9A-Za-z])", payload)
        )
        return payload, (), raw_hostile
    coordinate_map = {(row, column): semantic for _, row, column, semantic, _ in mappings}
    assert len(coordinate_map) == len(mappings)
    rows = payload.splitlines(keepends=True)
    normalized_rows: list[bytes] = []
    observed: list[str] = []
    hostile_tokens: list[str] = []
    seen_coordinates: set[tuple[int, int]] = set()
    known_by_value = {value: name for name, value in expected_oid_values.items()}
    for row_ordinal, row in enumerate(rows):
        tokens = tuple(re.finditer(rb"\S+", row.rstrip(b"\r\n")))
        cursor = 0
        rebuilt = bytearray()
        for column_ordinal, match in enumerate(tokens):
            rebuilt.extend(row[cursor : match.start()])
            token = match.group()
            coordinate = (row_ordinal, column_ordinal)
            semantic = coordinate_map.get(coordinate)
            if semantic is not None and token == expected_oid_values[semantic]:
                rebuilt.extend(f"<{semantic}>".encode())
                observed.append(semantic)
                seen_coordinates.add(coordinate)
            else:
                if re.fullmatch(rb"[0-9A-Fa-f]{40}", token):
                    exact_semantic = known_by_value.get(token)
                    corrupt_semantic = next(
                        (
                            name
                            for value, name in known_by_value.items()
                            if token[:1] == b"A" and token[1:] == value[1:]
                        ),
                        None,
                    )
                    if exact_semantic is not None:
                        marker = f"MISPLACED:{exact_semantic}@{row_ordinal}:{column_ordinal}"
                        hostile_tokens.append(marker)
                        rebuilt.extend(f"<{marker}>".encode())
                    elif corrupt_semantic is not None:
                        marker = f"CORRUPT_UPPERCASE_PREFIX:{corrupt_semantic}"
                        hostile_tokens.append(marker)
                        rebuilt.extend(f"<{marker}>".encode())
                    else:
                        hostile_tokens.append(token.decode("ascii"))
                        rebuilt.extend(token)
                else:
                    rebuilt.extend(token)
            cursor = match.end()
        rebuilt.extend(row[cursor:])
        normalized_rows.append(bytes(rebuilt))
    for coordinate, semantic in coordinate_map.items():
        if coordinate not in seen_coordinates:
            hostile_tokens.append(f"MISSING:{semantic}@{coordinate[0]}:{coordinate[1]}")
    return b"".join(normalized_rows), tuple(observed), tuple(hostile_tokens)


def assert_independent_textual_relation(
    role: str,
    transform: str,
    freeze: dict[str, Any],
    base: bytes,
    transformed: bytes,
) -> None:
    """Check one frozen byte transformation without calling its builder."""
    if transform == "missing_lf":
        assert role != "merge_scan"
        assert base.endswith(b"\n")
        assert transformed == base[:-1]
        return
    if transform == "crlf":
        expected = b"\r\n" if role == "merge_scan" else base.replace(b"\n", b"\r\n")
        assert transformed == expected
        return
    if transform == "extra_line":
        expected = (
            (b"e" * 40) + b"\n" + (b"f" * 40) + b"\n" if role == "merge_scan" else base + b"x\n"
        )
        assert transformed == expected
        return
    if transform == "valid_token":
        if role == "head":
            red_head = freeze["redHead"]
            assert type(red_head) is str
            expected = red_head.encode() + b"\n"
        elif role == "red_type":
            expected = b"blob\n"
        elif role in {"red_size", "c3_freeze_size"}:
            expected = str(int(base[:-1]) + 1).encode() + b"\n"
        elif role == "merge_scan":
            expected = (b"f" * 40) + b"\n"
        elif role == "ancestry_chain":
            first, second = base.split(b" ", 1)
            replacement = (b"f" * 40) if first != (b"f" * 40) else (b"e" * 40)
            expected = replacement + b" " + second
        elif role == "red_objects":
            first, *remaining = base.splitlines(keepends=True)
            replacement = (b"f" * 40) + b"\n"
            if first == replacement:
                replacement = (b"e" * 40) + b"\n"
            expected = replacement + b"".join(remaining)
        elif role == "red_author":
            expected = b"other@example.com\n"
        else:
            expected = b"sha2\n"
        assert transformed == expected
        return
    independent_corruptions = {
        "object_format": b"Sha2\n",
        "head": b"A" + base[1:],
        "red_type": b"Commit\n",
        "red_size": base[:-2] + b"x\n",
        "merge_scan": (b"F" * 40) + b"\n",
        "ancestry_chain": b"A" + base[1:],
        "red_objects": b"A" + base[1:],
        "c3_freeze_size": base[:-2] + b"x\n",
        "red_author": b"other.example.com\n",
    }
    assert transform == "corrupt_token"
    assert transformed == independent_corruptions[role]


def git(root: Path, *arguments: str, env: dict[str, str] | None = None) -> str:
    deterministic_env = {
        **os.environ,
        **DETERMINISTIC_GIT_METADATA,
        **({} if env is None else env),
    }
    result = subprocess.run(
        ("git", *arguments),
        cwd=root,
        env=deterministic_env,
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
) -> tuple[subprocess.CompletedProcess[bytes], ...]:
    expected = expected_git_argv(root, freeze)
    expected_env = expected_git_environment(root)
    calls: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    environment_ids: list[int] = []
    results: list[subprocess.CompletedProcess[bytes]] = []

    def record(argv: tuple[str, ...], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        recorded = {**kwargs, "env": kwargs["env"].copy()}
        calls.append((argv, recorded))
        environment_ids.append(id(kwargs["env"]))
        result = REAL_SUBPROCESS_RUN(argv, **kwargs)
        results.append(result)
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
    return tuple(results)


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


def portable_governed_parent_plan(root_bytes: int, root_depth: int) -> tuple[int, int, int]:
    """Return filler count and two feasible final component byte lengths."""
    filler_count = GOVERNED_FIXTURE_PARENT_DEPTH - 2 - root_depth
    assert filler_count >= 0
    bytes_before_finals = root_bytes + filler_count * (GOVERNED_FIXTURE_SLOT_BYTES + 1)
    final_budget = GOVERNED_FIXTURE_PARENT_BYTES - bytes_before_finals - 2
    assert 8 * 2 <= final_budget <= 255 * 2
    first_final = final_budget // 2
    return filler_count, first_final, final_budget - first_final


def _portable_root_plan(
    owner: Path,
    owner_status: os.stat_result,
    label: str,
    candidate_components: tuple[str, ...],
) -> PortableRootPlan:
    candidate = owner.joinpath(*candidate_components)
    candidate_bytes = len(os.fsencode(candidate))
    candidate_depth = len(candidate.parts)
    filler_count, first_final_bytes, second_final_bytes = portable_governed_parent_plan(
        candidate_bytes, candidate_depth
    )
    filler_components = tuple(
        (prefix := f"slot-{ordinal:02d}-") + ("p" * (GOVERNED_FIXTURE_SLOT_BYTES - len(prefix)))
        for ordinal in range(filler_count)
    )
    final_components = ("f" * first_final_bytes, "g" * second_final_bytes)
    governed = candidate.joinpath(*filler_components, *final_components)
    return PortableRootPlan(
        label,
        owner.as_posix(),
        stat.S_IFMT(owner_status.st_mode),
        owner_status.st_dev,
        owner_status.st_ino,
        candidate_components,
        tuple(len(os.fsencode(item)) for item in candidate_components),
        candidate_bytes,
        candidate_depth,
        filler_components,
        final_components,
        governed.as_posix(),
        len(os.fsencode(governed)),
        len(governed.parts),
    )


def plan_portable_fixture_roots(owner: Path) -> tuple[PortableRootPlan, PortableRootPlan]:
    """Plan both governed roots completely before any descendant mutation."""
    owner_status = owner.lstat()
    owner_resolved = owner.resolve(strict=True)
    assert owner == owner_resolved
    assert stat.S_ISDIR(owner_status.st_mode) and not owner.is_symlink()
    child_components = tuple(
        (prefix := f"r{ordinal}-") + ("s" * (size - len(prefix)))
        for ordinal, size in enumerate(PORTABLE_ROOT_CHILD_COMPONENT_BYTES)
    )
    plans = (
        _portable_root_plan(owner, owner_status, "A", (PORTABLE_ROOT_SLOT_NAMES[0],)),
        _portable_root_plan(
            owner,
            owner_status,
            "B",
            (PORTABLE_ROOT_SLOT_NAMES[1], *child_components),
        ),
    )
    assert tuple(len(os.fsencode(item)) for item in PORTABLE_ROOT_SLOT_NAMES) == (8, 8)
    assert (
        plans[1].candidate_bytes - plans[0].candidate_bytes,
        plans[1].candidate_depth - plans[0].candidate_depth,
    ) == PORTABLE_ROOT_RELATIVE_DELTA
    for plan in plans:
        assert plan.governed_bytes == GOVERNED_FIXTURE_PARENT_BYTES
        assert plan.governed_depth == GOVERNED_FIXTURE_PARENT_DEPTH
        assert all(
            8 <= len(os.fsencode(item)) <= 255
            for item in (*plan.filler_components, *plan.final_components)
        )
    return plans


def portable_construction_finding(coordinate: str) -> tuple[protocol.Finding, ...]:
    return (
        protocol.Finding(
            "evidence",
            "CURRENT",
            "ACP.EVIDENCE.PORTABLE_CONSTRUCTION",
            f"portableConstruction.{coordinate}",
        ),
    )


def validate_portable_fixture_plans(owner: Path, plans: object) -> tuple[protocol.Finding, ...]:
    """Validate every frozen plan coordinate without creating descendants."""
    if type(plans) is not tuple or len(plans) != 2:
        return portable_construction_finding("plans")
    if any(type(plan) is not PortableRootPlan for plan in plans):
        return portable_construction_finding("plans.type")
    try:
        owner_status = owner.lstat()
        owner_resolved = owner.resolve(strict=True)
    except OSError:
        return portable_construction_finding("owner")
    if owner != owner_resolved or owner.is_symlink() or not stat.S_ISDIR(owner_status.st_mode):
        return portable_construction_finding("owner.identity")
    expected = plan_portable_fixture_roots(owner)
    for ordinal, (actual, required) in enumerate(
        zip(cast(tuple[PortableRootPlan, PortableRootPlan], plans), expected, strict=True)
    ):
        for field in PortableRootPlan.__dataclass_fields__:
            if getattr(actual, field) != getattr(required, field):
                return portable_construction_finding(f"plans[{ordinal}].{field}")
    return ()


def construct_portable_fixture_roots(
    owner: Path,
    plans: object,
    *,
    mkdir_seam: Callable[[Path], None] | None = None,
) -> tuple[PortableConstructionResult | None, tuple[protocol.Finding, ...]]:
    """Consume two prevalidated plans, then create descendants through one seam."""
    findings = validate_portable_fixture_plans(owner, plans)
    if findings:
        return None, findings
    typed_plans = cast(tuple[PortableRootPlan, PortableRootPlan], plans)
    owner_status = owner.lstat()
    planning_transcript = (
        ("plan-complete", "A"),
        ("plan-complete", "B"),
        ("relation-validated", "+81-bytes/+6-depth"),
    )
    seam = mkdir_seam or (lambda path: path.mkdir())
    receipts: list[tuple[int, str, str, int, int, int, int]] = []
    observed_nodes: dict[Path, tuple[int, int, int]] = {}
    for plan in typed_plans:
        current = owner
        components = (
            *plan.candidate_components,
            *plan.filler_components,
            *plan.final_components,
        )
        for component_ordinal, component in enumerate(components):
            target = current / component
            if target.exists() or target.is_symlink():
                return None, portable_construction_finding(
                    f"filesystemReceipts[{len(receipts)}].preAbsent"
                )
            try:
                current_owner = owner.lstat()
            except OSError:
                return None, portable_construction_finding("owner.identity")
            if (
                stat.S_IFMT(current_owner.st_mode),
                current_owner.st_dev,
                current_owner.st_ino,
            ) != (
                stat.S_IFMT(owner_status.st_mode),
                owner_status.st_dev,
                owner_status.st_ino,
            ):
                return None, portable_construction_finding("owner.identity")
            for prior_path, identity in observed_nodes.items():
                try:
                    prior = prior_path.lstat()
                except OSError:
                    return None, portable_construction_finding(
                        f"filesystemReceipts[{len(receipts)}].parentIdentity"
                    )
                if (
                    stat.S_IFMT(prior.st_mode),
                    prior.st_dev,
                    prior.st_ino,
                ) != identity or prior_path.is_symlink():
                    return None, portable_construction_finding(
                        f"filesystemReceipts[{len(receipts)}].parentIdentity"
                    )
            try:
                seam(target)
                observed = target.lstat()
            except OSError:
                return None, portable_construction_finding(
                    f"seam.{plan.label}[{component_ordinal}].mkdir"
                )
            if not stat.S_ISDIR(observed.st_mode) or target.is_symlink():
                return None, portable_construction_finding(
                    f"filesystemReceipts[{len(receipts)}].observedType"
                )
            observed_nodes[target] = (
                stat.S_IFMT(observed.st_mode),
                observed.st_dev,
                observed.st_ino,
            )
            receipts.append(
                (
                    len(receipts),
                    target.relative_to(owner).as_posix(),
                    "." if current == owner else current.relative_to(owner).as_posix(),
                    len(os.fsencode(component)),
                    stat.S_IFMT(observed.st_mode),
                    observed.st_dev,
                    observed.st_ino,
                )
            )
            current = target
        if current.as_posix() != plan.governed_path:
            return None, portable_construction_finding(f"plans[{plan.label}].governedPath")
    try:
        final_owner = owner.lstat()
    except OSError:
        return None, portable_construction_finding("owner.identity")
    if (
        stat.S_IFMT(final_owner.st_mode),
        final_owner.st_dev,
        final_owner.st_ino,
    ) != (
        stat.S_IFMT(owner_status.st_mode),
        owner_status.st_dev,
        owner_status.st_ino,
    ):
        return None, portable_construction_finding("owner.identity")
    for prior_path, identity in observed_nodes.items():
        try:
            prior = prior_path.lstat()
        except OSError:
            return None, portable_construction_finding("filesystemReceipts.finalIdentity")
        if (stat.S_IFMT(prior.st_mode), prior.st_dev, prior.st_ino) != identity:
            return None, portable_construction_finding("filesystemReceipts.finalIdentity")
    governed_roots = tuple(Path(plan.governed_path) for plan in typed_plans)
    if not all(
        len(os.fsencode(path)) == GOVERNED_FIXTURE_PARENT_BYTES
        and len(path.parts) == GOVERNED_FIXTURE_PARENT_DEPTH
        for path in governed_roots
    ):
        return None, portable_construction_finding("governedRoots")
    return (
        PortableConstructionResult(
            typed_plans,
            planning_transcript,
            tuple(receipts),
            cast(tuple[Path, Path], governed_roots),
        ),
        (),
    )


def validate_portable_construction_result(
    owner: Path, result: object
) -> tuple[protocol.Finding, ...]:
    """Revalidate the immutable plan, transcript, and every filesystem receipt."""
    if type(result) is not PortableConstructionResult:
        return portable_construction_finding("result.type")
    typed = result
    plan_findings = validate_portable_fixture_plans(owner, typed.plans)
    if plan_findings:
        return plan_findings
    if typed.planning_transcript != (
        ("plan-complete", "A"),
        ("plan-complete", "B"),
        ("relation-validated", "+81-bytes/+6-depth"),
    ):
        return portable_construction_finding("planningTranscript")
    if type(typed.filesystem_receipts) is not tuple:
        return portable_construction_finding("filesystemReceipts")
    expected_receipts: list[tuple[int, str, str, int, int, int, int]] = []
    try:
        for plan in typed.plans:
            current = owner
            for component in (
                *plan.candidate_components,
                *plan.filler_components,
                *plan.final_components,
            ):
                target = current / component
                observed = target.lstat()
                if not stat.S_ISDIR(observed.st_mode) or target.is_symlink():
                    return portable_construction_finding(
                        f"filesystemReceipts[{len(expected_receipts)}].observedType"
                    )
                expected_receipts.append(
                    (
                        len(expected_receipts),
                        target.relative_to(owner).as_posix(),
                        "." if current == owner else current.relative_to(owner).as_posix(),
                        len(os.fsencode(component)),
                        stat.S_IFMT(observed.st_mode),
                        observed.st_dev,
                        observed.st_ino,
                    )
                )
                current = target
    except (OSError, ValueError):
        return portable_construction_finding("filesystemReceipts")
    receipt_fields = (
        "ordinal",
        "relativePath",
        "parentRelativePath",
        "componentBytes",
        "observedMode",
        "device",
        "inode",
    )
    for ordinal, actual in enumerate(typed.filesystem_receipts):
        if type(actual) is not tuple or len(actual) != len(receipt_fields):
            return portable_construction_finding(f"filesystemReceipts[{ordinal}]")
        if ordinal >= len(expected_receipts):
            return portable_construction_finding(f"filesystemReceipts[{ordinal}].ordinal")
        expected = expected_receipts[ordinal]
        for coordinate, (actual_value, expected_value) in enumerate(
            zip(actual, expected, strict=True)
        ):
            if type(actual_value) is not type(expected_value) or actual_value != expected_value:
                return portable_construction_finding(
                    f"filesystemReceipts[{ordinal}].{receipt_fields[coordinate]}"
                )
    if len(typed.filesystem_receipts) < len(expected_receipts):
        return portable_construction_finding(
            f"filesystemReceipts[{len(typed.filesystem_receipts)}].ordinal"
        )
    expected_roots = tuple(Path(plan.governed_path) for plan in typed.plans)
    if typed.governed_roots != expected_roots:
        return portable_construction_finding("governedRoots")
    return ()


def portable_component_boundary_findings(
    root_bytes: int, root_depth: int
) -> tuple[protocol.Finding, ...]:
    try:
        _, first_final, second_final = portable_governed_parent_plan(root_bytes, root_depth)
    except AssertionError:
        return portable_construction_finding("componentBytes")
    if not all(8 <= value <= 255 for value in (first_final, second_final)):
        return portable_construction_finding("componentBytes")
    return ()


def execute_portable_construction_mutant(
    operation: str,
) -> tuple[tuple[protocol.Finding, ...], int]:
    """Execute one named plan, seam, boundary, or result mutation."""
    boundaries = {
        "component-7": (684, 16),
        "component-8": (682, 16),
        "component-255": (188, 16),
        "component-256": (186, 16),
    }
    if operation in boundaries:
        return portable_component_boundary_findings(*boundaries[operation]), 0
    if operation == "infeasible":
        return portable_component_boundary_findings(699, 17), 0
    with TemporaryDirectory(prefix="r-") as base_text:
        base = Path(base_text).resolve(strict=True)
        owner = base / ("o" * 30)
        owner.mkdir()
        plans: object = plan_portable_fixture_roots(owner)
        typed = cast(tuple[PortableRootPlan, PortableRootPlan], plans)
        if operation == "plans-zero":
            plans = ()
        elif operation == "plans-one":
            plans = typed[:1]
        elif operation == "plans-three":
            plans = (*typed, typed[0])
        elif operation == "owner-alias":
            alias = owner / ".." / owner.name
            return validate_portable_fixture_plans(alias, plans), 0
        elif operation == "owner-symlink":
            alias = base / "s"
            alias.symlink_to(owner, target_is_directory=True)
            return validate_portable_fixture_plans(alias, plans), 0
        elif operation == "owner-inode":
            owner.rename(base / "shadow")
            owner.mkdir()
        elif operation == "delta":
            plans = (typed[0], replace(typed[1], candidate_bytes=typed[1].candidate_bytes + 1))
        if operation not in {
            "seam-error",
            "early-a",
            "early-b",
            "seam-noop",
            "seam-wrong-path",
            "transcript",
            "receipt-duplicate",
            "receipt-missing",
            "receipt-reordered",
            "receipt-ordinal",
            "receipt-path",
            "receipt-parent",
            "receipt-bytes",
            "receipt-type",
            "receipt-device",
            "receipt-inode",
            "envelope",
        }:
            return validate_portable_fixture_plans(owner, plans), 0
        seam_calls: list[Path] = []

        def seam(path: Path) -> None:
            seam_calls.append(path)
            first_plan_count = len(
                (
                    *typed[0].candidate_components,
                    *typed[0].filler_components,
                    *typed[0].final_components,
                )
            )
            if (
                operation == "early-a"
                or (operation == "early-b" and len(seam_calls) == first_plan_count + 1)
                or (operation == "seam-error" and len(seam_calls) == 2)
            ):
                raise OSError("controlled")
            if operation == "seam-noop":
                return
            if operation == "seam-wrong-path":
                path.with_name(path.name + "-wrong").mkdir()
                return
            path.mkdir()

        result, findings = construct_portable_fixture_roots(owner, plans, mkdir_seam=seam)
        if findings:
            if operation == "seam-noop":
                assert not seam_calls[0].exists()
            elif operation == "seam-wrong-path":
                assert not seam_calls[0].exists()
                assert seam_calls[0].with_name(seam_calls[0].name + "-wrong").is_dir()
            return findings, len(seam_calls)
        assert result is not None
        if operation == "transcript":
            result = replace(result, planning_transcript=result.planning_transcript[::-1])
        elif operation.startswith("receipt-"):
            first = result.filesystem_receipts[0]
            receipts = result.filesystem_receipts
            if operation == "receipt-duplicate":
                receipts = (first, *receipts)
            elif operation == "receipt-missing":
                receipts = receipts[1:]
            elif operation == "receipt-reordered":
                receipts = (receipts[1], receipts[0], *receipts[2:])
            else:
                coordinate = {
                    "receipt-ordinal": 0,
                    "receipt-path": 1,
                    "receipt-parent": 2,
                    "receipt-bytes": 3,
                    "receipt-type": 4,
                    "receipt-device": 5,
                    "receipt-inode": 6,
                }[operation]
                values = list(first)
                values[coordinate] = (
                    cast(int, values[coordinate]) + 1
                    if type(values[coordinate]) is int
                    else str(values[coordinate]) + "-mutant"
                )
                receipts = (
                    cast(tuple[int, str, str, int, int, int, int], tuple(values)),
                    *receipts[1:],
                )
            result = replace(result, filesystem_receipts=receipts)
        elif operation == "envelope":
            result = replace(result, governed_roots=result.governed_roots[::-1])
        return validate_portable_construction_result(owner, result), len(seam_calls)


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
    git(root, "config", "user.name", DETERMINISTIC_GIT_METADATA["GIT_AUTHOR_NAME"])
    git(root, "config", "user.email", DETERMINISTIC_GIT_METADATA["GIT_AUTHOR_EMAIL"])
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
        "implementationAuthor": DETERMINISTIC_GIT_METADATA["GIT_AUTHOR_EMAIL"],
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


def _initialize_repository_metadata_collection(
    original_tmp_path: Any,
) -> Any:
    tmp_path = original_tmp_path
    assert len(os.fsencode(tmp_path)) == GOVERNED_FIXTURE_PARENT_BYTES
    assert len(tmp_path.parts) == GOVERNED_FIXTURE_PARENT_DEPTH
    final_components = tuple(len(os.fsencode(part)) for part in tmp_path.parts[-2:])
    assert len(final_components) == 2
    assert all(8 <= length <= 255 for length in final_components)
    root, freeze = create_real_git_freeze(tmp_path)
    metadata_execution_rows: list[MetadataExecution] = []
    metadata_stimulus_rows: list[tuple[MetadataStimulusFacts, str]] = []
    metadata_trigger_rows: list[MetadataTriggerReceipt] = []
    metadata_raw_read_rows: list[MetadataRawReadRow] = []
    metadata_close_order_rows: list[MetadataCloseOrderRow] = []
    metadata_normalized_payload_rows: list[MetadataNormalizedPayloadRow] = []
    metadata_configured_plan_receipts: list[ConfiguredPlanReceipt] = []
    baseline_metadata_io = protocol.SYSTEM_METADATA_IO

    def normalized_observed_path(raw_path: str) -> str:
        raw_temporary = os.fspath(tmp_path)
        resolved_temporary = os.path.realpath(raw_temporary)
        temporary_aliases = {
            raw_temporary,
            resolved_temporary,
            raw_temporary.removeprefix("/private")
            if raw_temporary.startswith("/private/")
            else f"/private{raw_temporary}",
            resolved_temporary.removeprefix("/private")
            if resolved_temporary.startswith("/private/")
            else f"/private{resolved_temporary}",
        }
        normalized = raw_path
        for temporary_alias in sorted(temporary_aliases, key=len, reverse=True):
            normalized = normalized.replace(temporary_alias, "$TMP", 1)
        normalized = normalized.replace(tmp_path.name, "$CASE")
        temporary_marker = normalized.find("$TMP")
        if temporary_marker == -1:
            return normalized
        suffix_start = temporary_marker + len("$TMP")
        suffix = normalized[suffix_start:]
        for component in re.finditer(r"[^/]+", suffix):
            if component.group() in {".", "..", "$CASE"}:
                continue
            suffix = f"{suffix[: component.start()]}$CASE{suffix[component.end() :]}"
            break
        return f"{normalized[:suffix_start]}{suffix}"

    def normalized_observed_payload(payload: bytes) -> bytes:
        raw_temporary = os.fspath(tmp_path).encode()
        resolved_temporary = os.path.realpath(tmp_path).encode()
        temporary_aliases = {
            raw_temporary,
            resolved_temporary,
            raw_temporary.removeprefix(b"/private")
            if raw_temporary.startswith(b"/private/")
            else b"/private" + raw_temporary,
            resolved_temporary.removeprefix(b"/private")
            if resolved_temporary.startswith(b"/private/")
            else b"/private" + resolved_temporary,
        }
        normalized = payload
        for temporary_alias in sorted(temporary_aliases, key=len, reverse=True):
            normalized = normalized.replace(temporary_alias, b"$TMP")
        normalized = normalized.replace(tmp_path.name.encode(), b"$CASE")
        return re.sub(rb"\$TMP/[^/\r\n\x00]+", b"$TMP/$CASE", normalized)

    def observed_path_facts(label: str, path: Path) -> tuple[tuple[str, str], ...]:
        normalized_path = normalized_observed_path(os.fspath(path))
        path_facts = (
            (f"{label}.path", normalized_path),
            (
                f"{label}.depth",
                str(len(tuple(part for part in normalized_path.split("/") if part))),
            ),
        )
        try:
            status = path.lstat()
        except (OSError, ValueError) as error:
            return (*path_facts, (f"{label}.kind", f"absent:{type(error).__name__}"))
        if stat.S_ISLNK(status.st_mode):
            raw_target = os.readlink(path)
            return (
                *path_facts,
                (f"{label}.kind", "symlink"),
                (f"{label}.rawTarget", normalized_observed_path(raw_target)),
                (f"{label}.liveness", "live" if path.exists() else "broken"),
            )
        if stat.S_ISDIR(status.st_mode):
            return (*path_facts, (f"{label}.kind", "directory"))
        if stat.S_ISREG(status.st_mode):
            payload = path.read_bytes()
            normalized_payload = normalized_observed_payload(payload)
            return (
                *path_facts,
                (f"{label}.kind", "regular"),
                (f"{label}.payloadBytes", str(len(payload))),
                (
                    f"{label}.payloadSha256",
                    hashlib.sha256(normalized_payload).hexdigest(),
                ),
            )
        return (*path_facts, (f"{label}.kind", "other"))

    def observe_pre_execution_stimulus(
        case_root: str | Path,
        operational_mode: str,
        configured_operation: str,
    ) -> MetadataStimulusFacts:
        raw_root = os.fspath(case_root)
        normalized_root = normalized_observed_path(raw_root)
        lexical_depth = len(tuple(part for part in normalized_root.split("/") if part))
        root_path = Path(raw_root)
        facts: list[tuple[str, str]] = [
            ("root.spelling", normalized_root),
            ("root.lexicalDepth", str(lexical_depth)),
            ("operational.mode", operational_mode),
            ("operation.configured", configured_operation),
            *observed_path_facts("root", root_path),
            *observed_path_facts("dotGit", root_path / ".git"),
        ]
        common_directory = root_path / ".git"
        try:
            dot_git_status = common_directory.lstat()
            if stat.S_ISREG(dot_git_status.st_mode):
                dot_git_payload = common_directory.read_bytes()
                if dot_git_payload.startswith(b"gitdir: ") and dot_git_payload.endswith(b"\n"):
                    linked_directory = Path(dot_git_payload[8:-1].decode("utf-8"))
                    facts.extend(observed_path_facts("linkedGitDir", linked_directory))
                    backlink = linked_directory / "gitdir"
                    commondir_record = linked_directory / "commondir"
                    facts.extend(observed_path_facts("backlink", backlink))
                    facts.extend(observed_path_facts("commondirRecord", commondir_record))
                    if commondir_record.is_file():
                        common_text = commondir_record.read_text(encoding="utf-8")
                        if common_text.endswith("\n"):
                            common_directory = linked_directory / common_text[:-1]
                    facts.extend(observed_path_facts("commonDir", common_directory))
        except (OSError, UnicodeError, ValueError):
            pass
        for label, relative in (
            ("grafts", "info/grafts"),
            ("shallow", "shallow"),
            ("alternates", "objects/info/alternates"),
            ("httpAlternates", "objects/info/http-alternates"),
        ):
            relative_path = Path(relative)
            for ancestor_ordinal, ancestor_relative in enumerate(
                reversed(relative_path.parents[:-1])
            ):
                facts.extend(
                    observed_path_facts(
                        f"{label}.ancestor[{ancestor_ordinal}]",
                        common_directory / ancestor_relative,
                    )
                )
            facts.extend(observed_path_facts(label, common_directory / relative_path))
        return tuple(facts)

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

    return (
        tmp_path,
        final_components,
        root,
        freeze,
        metadata_execution_rows,
        metadata_stimulus_rows,
        metadata_trigger_rows,
        metadata_raw_read_rows,
        metadata_close_order_rows,
        metadata_normalized_payload_rows,
        metadata_configured_plan_receipts,
        baseline_metadata_io,
        normalized_observed_path,
        normalized_observed_payload,
        observe_pre_execution_stimulus,
        metadata_case,
        observed_payload_stimulus,
    )


def _build_traced_metadata_reader(
    baseline_metadata_io: Any,
    normalized_observed_path: Any,
    normalized_observed_payload: Any,
) -> Any:
    def traced_metadata_reader(
        called_root: str | Path,
        *,
        provenance: protocol.GitMetadataProvenance,
        io: protocol.MetadataIO,
        role_calls: list[str],
        role_traces: list[MetadataRoleTrace],
        trigger_receipts: list[tuple[str, tuple[str, ...]]],
    ) -> protocol.GitMetadataReadResult:
        role_calls.append(provenance.role)
        operations: list[str] = []
        opened: list[int] = []
        close_attempts: list[int] = []
        observed_lstats: list[os.stat_result] = []
        observed_fstats: list[os.stat_result] = []
        callback_events: list[str] = []
        callback_argument_events: list[str] = []
        read_requests: list[int] = []
        read_chunk_lengths: list[int] = []
        read_chunks: list[bytes] = []
        read_types: list[str] = []
        close_results: list[str] = []
        descriptor_open_ordinals: dict[int, int] = {}
        descriptor_paths: dict[int, Path] = {}
        closed_descriptors: set[int] = set()

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

        def callback_path(path: str, dir_fd: int | None) -> str:
            assert type(path) is str
            if dir_fd is not None:
                assert dir_fd in descriptor_open_ordinals
                assert dir_fd in descriptor_paths
                assert dir_fd not in closed_descriptors
                assert not os.path.isabs(path)
                candidate = descriptor_paths[dir_fd] / path
            else:
                candidate = Path(path)
            root_path = Path(os.path.normpath(os.fspath(called_root)))
            candidate_path = Path(os.path.normpath(os.fspath(candidate)))
            if candidate_path == root_path:
                return "$ROOT"
            try:
                relative = candidate_path.relative_to(root_path).as_posix()
            except ValueError:
                try:
                    distance = len(root_path.relative_to(candidate_path).parts)
                except ValueError:
                    normalized = cast(str, normalized_observed_path(os.fspath(candidate_path)))
                    assert normalized.startswith("$TMP/$CASE")
                    return "fixture-relative:" + normalized
                return f"root-ancestor-distance-{distance}"
            return "$ROOT" if relative == "." else "$ROOT/" + relative

        def callback_prefix(callback: str) -> str:
            return (
                f"event-{len(callback_argument_events)}:role-{provenance.role}:"
                f"roleOrdinal-{len(role_calls) - 1}:{callback}"
            )

        def observed_lstat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
            event_prefix = callback_prefix("lstat")
            dirfd_token = (
                "dirfd-none"
                if dir_fd is None
                else f"dirfdOpenOrdinal-{descriptor_open_ordinals[dir_fd]}"
            )
            callback_argument_events.append(
                f"{event_prefix}:argType-str:path-{callback_path(path, dir_fd)}:{dirfd_token}"
            )
            callback_events.append(
                f"{event_prefix}:"
                + ("system" if io.lstat is baseline_metadata_io.lstat else "custom")
            )
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
            event_prefix = callback_prefix("open")
            argument_path = callback_path(path, dir_fd)
            descriptor_candidate = (
                descriptor_paths[dir_fd] / path if dir_fd is not None else Path(path)
            )
            descriptor_candidate = Path(os.path.normpath(os.fspath(descriptor_candidate)))
            symbolic_flags = "RDONLY|NOFOLLOW" + ("|DIRECTORY" if flags & os.O_DIRECTORY else "")
            dirfd_token = (
                "dirfd-none"
                if dir_fd is None
                else f"dirfdOpenOrdinal-{descriptor_open_ordinals[dir_fd]}"
            )
            assert flags & os.O_NOFOLLOW
            assert flags & os.O_ACCMODE == os.O_RDONLY
            callback_events.append(
                f"{event_prefix}:"
                + ("system" if io.open is baseline_metadata_io.open else "custom")
            )
            try:
                descriptor = io.open(path, flags, dir_fd=dir_fd)
            except OSError as error:
                callback_argument_events.append(
                    f"{event_prefix}:argTypes-str,int:path-{argument_path}:"
                    f"{dirfd_token}:flags-{symbolic_flags}:result-error-{type(error).__name__}"
                )
                operations.append(
                    f"open:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            opened.append(descriptor)
            assert descriptor not in descriptor_open_ordinals or descriptor in closed_descriptors
            descriptor_open_ordinals[descriptor] = len(opened) - 1
            descriptor_paths[descriptor] = descriptor_candidate
            closed_descriptors.discard(descriptor)
            callback_argument_events.append(
                f"{event_prefix}:argTypes-str,int:path-{argument_path}:"
                f"{dirfd_token}:flags-{symbolic_flags}:"
                f"result-openOrdinal-{descriptor_open_ordinals[descriptor]}"
            )
            operations.append(
                "open:ok:"
                + ("directory" if flags & os.O_DIRECTORY else "regular")
                + (":nofollow" if flags & os.O_NOFOLLOW else ":follow")
            )
            return descriptor

        def observed_fstat(descriptor: int) -> os.stat_result:
            event_prefix = callback_prefix("fstat")
            callback_argument_events.append(
                f"{event_prefix}:argType-int:descriptorOpenOrdinal-"
                f"{descriptor_open_ordinals[descriptor]}"
            )
            assert descriptor not in closed_descriptors
            callback_events.append(
                f"{event_prefix}:"
                + ("system" if io.fstat is baseline_metadata_io.fstat else "custom")
            )
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
            stored_parent_entry = next(
                (
                    (parent_role, record)
                    for parent_role, record in provenance.parent_records
                    if Path(os.path.normpath(os.fspath(record.path)))
                    == descriptor_paths[descriptor]
                ),
                None,
            )
            stored_parent_role = stored_parent_entry[0] if stored_parent_entry is not None else None
            stored_parent = stored_parent_entry[1] if stored_parent_entry is not None else None
            if stored_parent is not None and kind(observed.st_mode) != kind(stored_parent.mode):
                relation = f"stored-parent-{stored_parent_role}-type-drift"
            elif stored_parent is not None and observed.st_dev != stored_parent.device:
                relation = f"stored-parent-{stored_parent_role}-device-drift"
            elif stored_parent is not None and observed.st_ino != stored_parent.inode:
                relation = f"stored-parent-{stored_parent_role}-inode-drift"
            elif kind(observed.st_mode) != kind(prior.st_mode):
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
            event_prefix = callback_prefix("read")
            callback_argument_events.append(
                f"{event_prefix}:argTypes-int,int:descriptorOpenOrdinal-"
                f"{descriptor_open_ordinals[descriptor]}:count-{count}"
            )
            assert descriptor not in closed_descriptors
            callback_events.append(
                f"{event_prefix}:"
                + ("system" if io.read is baseline_metadata_io.read else "custom")
            )
            read_requests.append(count)
            try:
                observed = io.read(descriptor, count)
            except OSError as error:
                operations.append(
                    f"read:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            if type(observed) is bytes:
                read_chunk_lengths.append(len(observed))
                read_chunks.append(observed)
                read_types.append("bytes")
                operations.append(f"read:bytes:{len(observed)}")
            else:
                read_chunk_lengths.append(-1)
                read_types.append(type(observed).__name__)
                operations.append(f"read:type:{type(observed).__name__}")
            return observed

        def observed_close(descriptor: int) -> None:
            event_prefix = callback_prefix("close")
            callback_events.append(
                f"{event_prefix}:"
                + ("system" if io.close is baseline_metadata_io.close else "custom")
            )
            close_attempts.append(descriptor)
            try:
                io.close(descriptor)
            except OSError as error:
                callback_argument_events.append(
                    f"{event_prefix}:argType-int:descriptorOpenOrdinal-"
                    f"{descriptor_open_ordinals[descriptor]}:result-error-{type(error).__name__}"
                )
                closed_descriptors.add(descriptor)
                close_results.append(
                    f"error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                operations.append(
                    f"close:error:{type(error).__name__}:"
                    + ("errno" if error.errno is not None else "no-errno")
                )
                raise
            close_results.append("ok")
            callback_argument_events.append(
                f"{event_prefix}:argType-int:descriptorOpenOrdinal-"
                f"{descriptor_open_ordinals[descriptor]}:result-ok"
            )
            closed_descriptors.add(descriptor)
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
        normalized_read_payload_identity = ""
        if read_chunks:
            observed_read_bytes = b"".join(read_chunks)
            assert len(read_requests) == len(read_chunks) == len(read_chunk_lengths)
            assert sum(read_chunk_lengths) == len(observed_read_bytes)
            assert tuple(read_requests) == tuple(
                4097 - sum(read_chunk_lengths[:ordinal])
                for ordinal in range(len(read_chunk_lengths))
            )
            if observed.record is not None and observed.record.payload is not None:
                assert observed_read_bytes == observed.record.payload
            normalized_read_payload = normalized_observed_payload(observed_read_bytes)
            normalized_read_payload_identity = hashlib.sha256(normalized_read_payload).hexdigest()
        trigger_receipts.append(
            (
                provenance.role,
                (
                    "callback-args=" + ";".join(callback_argument_events),
                    "callbacks=" + ",".join(callback_events),
                    "results=" + ",".join(operations),
                    "lstats=" + ",".join(item for item in operations if item.startswith("lstat:")),
                    "opens=" + ",".join(item for item in operations if item.startswith("open:")),
                    "fstats=" + ",".join(item for item in operations if item.startswith("fstat:")),
                    "read-requests=" + ",".join(str(item) for item in read_requests),
                    "read-chunks=" + ",".join(str(item) for item in read_chunk_lengths),
                    f"read-counts=requests:{len(read_requests)},chunks:{len(read_chunk_lengths)}",
                    "readTypes=" + ",".join(read_types),
                    "normalized-read-payload-sha256=" + normalized_read_payload_identity,
                    "post-lstats="
                    + ",".join(item for item in operations if item.startswith("post-lstat:")),
                    "close-attempt-order="
                    + ",".join(str(opened.index(item)) for item in close_attempts),
                    "close-results=" + ",".join(close_results),
                ),
            )
        )
        return observed

    return traced_metadata_reader


def _build_metadata_execution_recorders(
    monkeypatch: Any,
    metadata_execution_rows: Any,
    metadata_stimulus_rows: Any,
    metadata_trigger_rows: Any,
    metadata_raw_read_rows: Any,
    metadata_close_order_rows: Any,
    metadata_normalized_payload_rows: Any,
    metadata_configured_plan_receipts: Any,
    observe_pre_execution_stimulus: Any,
    metadata_case: Any,
    observed_payload_stimulus: Any,
    traced_metadata_reader: Any,
) -> Any:
    def finish_metadata_execution(
        case_id: str,
        role_calls: list[str],
        role_traces: list[MetadataRoleTrace],
        pre_execution_facts: MetadataStimulusFacts,
        trigger_receipts: list[tuple[str, tuple[str, ...]]],
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
        execution_evidence_identity = hashlib.sha256(
            canonical((mode, payload_sha, role_traces))
        ).hexdigest()
        pre_execution_identity = hashlib.sha256(canonical(pre_execution_facts)).hexdigest()
        assert all("finding:" not in value for _, value in pre_execution_facts)
        assert all("result:" not in value for _, value in pre_execution_facts)
        assert pre_execution_identity not in {identity for _, identity in metadata_stimulus_rows}
        metadata_stimulus_rows.append((pre_execution_facts, pre_execution_identity))
        frozen_trigger_receipt = tuple(trigger_receipts)
        assert all(case_id not in value for _, values in frozen_trigger_receipt for value in values)
        assert all(
            "finding:" not in value for _, values in frozen_trigger_receipt for value in values
        )
        assert all(
            "result:" not in value for _, values in frozen_trigger_receipt for value in values
        )
        assert all("ACP." not in value for _, values in frozen_trigger_receipt for value in values)
        metadata_trigger_rows.append(frozen_trigger_receipt)
        execution_id = f"{case_id}@{mode}"
        for role_ordinal, (role, values) in enumerate(frozen_trigger_receipt):
            if role == "inter-role-mutation":
                continue
            receipt_values = {item.split("=", 1)[0]: item.split("=", 1)[1] for item in values}
            requests = tuple(
                int(item) for item in receipt_values["read-requests"].split(",") if item
            )
            chunks = tuple(int(item) for item in receipt_values["read-chunks"].split(",") if item)
            read_types = tuple(item for item in receipt_values["readTypes"].split(",") if item)
            metadata_raw_read_rows.append(
                (
                    execution_id,
                    role_ordinal,
                    role,
                    requests,
                    chunks,
                    len(requests),
                    len(chunks),
                    read_types,
                )
            )
            close_order = tuple(
                int(item) for item in receipt_values["close-attempt-order"].split(",") if item
            )
            close_results = tuple(
                item for item in receipt_values["close-results"].split(",") if item
            )
            metadata_close_order_rows.append(
                (execution_id, role_ordinal, role, close_order, close_results)
            )
            metadata_normalized_payload_rows.append(
                (
                    execution_id,
                    role_ordinal,
                    role,
                    receipt_values["normalized-read-payload-sha256"],
                )
            )
        raw_role_receipts = tuple(
            (
                role,
                {item.split("=", 1)[0]: item.split("=", 1)[1] for item in values},
            )
            for role, values in frozen_trigger_receipt
            if role != "inter-role-mutation"
        )
        callback_arguments = tuple(
            item
            for _, values in raw_role_receipts
            for item in values["callback-args"].split(";")
            if item
        )
        callback_events = tuple(
            item
            for _, values in raw_role_receipts
            for item in values["callbacks"].split(",")
            if item
        )
        role_events = tuple(
            f"{ordinal}:{role}" for ordinal, (role, _) in enumerate(raw_role_receipts)
        )
        inter_receipt_rows = tuple(
            (ordinal, values)
            for ordinal, (role, values) in enumerate(frozen_trigger_receipt)
            if role == "inter-role-mutation"
        )
        if inter_receipt_rows:
            assert len(inter_receipt_rows) == 1
            inter_ordinal, inter_values = inter_receipt_rows[0]
            after_role_value = next(
                value.split("=", 1)[1] for value in inter_values if value.startswith("afterRole=")
            )
            role_events = (
                *role_events,
                f"interReceiptOrdinal-{inter_ordinal}:afterRole-{after_role_value}",
            )
        metadata_events = tuple(
            callback.rsplit(":", 1)[0] + ":" + result
            for _, values in raw_role_receipts
            for callback, result in zip(
                tuple(item for item in values["callbacks"].split(",") if item),
                tuple(item for item in values["results"].split(",") if item),
                strict=True,
            )
        )
        stat_events = tuple(
            item
            for item in metadata_events
            if ":lstat:" in item or ":fstat:" in item or ":post-lstat:" in item
        )
        exception_events = tuple(item for item in metadata_events if ":error:" in item)
        close_effects = tuple(item for item in callback_arguments if ":close:" in item)
        inter_role_values = next(
            (values for role, values in frozen_trigger_receipt if role == "inter-role-mutation"),
            (),
        )
        inter_role_evidence = (
            ("role=inter-role-mutation", *inter_role_values) if inter_role_values else ()
        )
        raw_evidence = (
            callback_arguments,
            callback_events,
            role_events,
            metadata_events,
            stat_events,
            exception_events,
            close_effects,
            inter_role_evidence,
        )
        plan_rows = tuple(
            plan for plan in EXPECTED_METADATA_CONFIGURED_PLANS if plan[0] == execution_id
        )
        if plan_rows:
            assert len(plan_rows) == 1
            declared_plan = plan_rows[0][1:]
            receipt_index = len(metadata_configured_plan_receipts)
            raw_identity = hashlib.sha256(canonical(raw_evidence)).hexdigest()
            integrity = validate_configured_raw_receipt(raw_evidence, raw_identity, receipt_index)
            assert integrity.findings == ()
            assert integrity.parsed is not None
            projection_result = project_configured_raw_receipt(integrity.parsed)
            assert projection_result.findings == ()
            assert projection_result.projection is not None
            projection = projection_result.projection
            assert (
                bind_configured_plan(
                    raw_evidence,
                    raw_identity,
                    integrity.parsed.observed,
                    projection,
                    declared_plan,
                    receipt_index,
                )
                == ()
            ), (
                execution_id,
                projection,
                declared_plan,
                tuple(event for event in callback_arguments if "info" in event),
            )
            assert (
                bind_configured_receipt_schedule(
                    execution_evidence_identity,
                    raw_identity,
                    integrity.parsed.observed,
                    projection,
                    receipt_index,
                )
                == ()
            )
            callback, target, phase, effect = projection
            target_role, target_path, role_ordinal, callback_ordinal = integrity.parsed.observed
            metadata_configured_plan_receipts.append(
                (
                    execution_id,
                    *raw_evidence,
                    raw_identity,
                    callback,
                    target,
                    phase,
                    effect,
                    target_role,
                    target_path,
                    role_ordinal,
                    callback_ordinal,
                    execution_evidence_identity,
                )
            )
        execution: MetadataExecution = (
            row,
            mode,
            pre_execution_facts,
            pre_execution_identity,
            execution_evidence_identity,
            normalized_roles,
            tuple(role_traces),
        )
        assert execution not in metadata_execution_rows
        assert execution == EXPECTED_METADATA_EXECUTIONS[len(metadata_execution_rows)]
        metadata_execution_rows.append(execution)
        return cast(MetadataCaseRow, row)

    def execute_metadata_success_case(
        case_id: str,
        case_root: str | Path,
        expected: protocol.GitDiscoveryResult,
    ) -> None:
        row = metadata_case(case_id)
        mode = "conventional" if row[2] == "both" else row[2]
        pre_execution_facts = observe_pre_execution_stimulus(case_root, mode, "system-reader")
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []
        trigger_receipts: list[tuple[str, tuple[str, ...]]] = []
        discovery_records: list[protocol.GitMetadataRecord] = []

        def observed_reader(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            observed = traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
                trigger_receipts=trigger_receipts,
            )
            if provenance.role == "discovery" and observed.record is not None:
                discovery_records.append(observed.record)
            elif provenance.role == "dot_git":
                assert discovery_records
                assert provenance.parent_records[0][1] is discovery_records[-1]
            return cast(protocol.GitMetadataReadResult, observed)

        with monkeypatch.context() as success_patch:
            success_patch.setattr(protocol, "_read_git_metadata_nofollow", observed_reader)
            assert protocol.discover_git_repository(case_root) == expected
        finish_metadata_execution(
            case_id, role_calls, role_traces, pre_execution_facts, trigger_receipts
        )

    def execute_metadata_case(
        case_id: str,
        case_root: str | Path,
        expected_finding: tuple[protocol.Finding, ...],
        operational_mode: str | None = None,
    ) -> None:
        row = metadata_case(case_id)
        mode = operational_mode or ("conventional" if row[2] == "both" else row[2])
        pre_execution_facts = observe_pre_execution_stimulus(case_root, mode, "system-reader")
        payload_sha = observed_payload_stimulus(case_id, case_root)
        assert row[1] == "public"
        assert row[5] is not None
        assert expected_finding == finding("git-metadata", row[5], row[6])
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []
        trigger_receipts: list[tuple[str, tuple[str, ...]]] = []
        discovery_records: list[protocol.GitMetadataRecord] = []

        def observed_reader(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            observed = traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
                trigger_receipts=trigger_receipts,
            )
            if provenance.role == "discovery" and observed.record is not None:
                discovery_records.append(observed.record)
            elif provenance.role == "dot_git":
                assert discovery_records
                assert provenance.parent_records[0][1] is discovery_records[-1]
            return cast(protocol.GitMetadataReadResult, observed)

        with monkeypatch.context() as reader_patch:
            reader_patch.setattr(protocol, "_read_git_metadata_nofollow", observed_reader)
            assert_metadata_failure(case_root, reader_patch, expected_finding)
        assert role_calls
        assert role_calls[-1] == row[3]
        finish_metadata_execution(
            case_id,
            role_calls,
            role_traces,
            pre_execution_facts,
            trigger_receipts,
            operational_mode,
            payload_sha,
        )

    return (finish_metadata_execution, execute_metadata_success_case, execute_metadata_case)


def _exercise_metadata_io_and_baseline_transcript(
    monkeypatch: Any,
    root: Any,
    freeze: Any,
    normalized_observed_path: Any,
    observe_pre_execution_stimulus: Any,
    metadata_case: Any,
    traced_metadata_reader: Any,
    finish_metadata_execution: Any,
    execute_metadata_success_case: Any,
) -> Any:
    def execute_metadata_io_case(
        case_id: str,
        case_root: str | Path,
        metadata_io: protocol.MetadataIO,
        expected_finding: tuple[protocol.Finding, ...],
        operational_mode: str | None = None,
    ) -> None:
        row = metadata_case(case_id)
        mode = operational_mode or ("conventional" if row[2] == "both" else row[2])
        injected_operations = ",".join(
            (
                metadata_io.lstat.__name__,
                metadata_io.open.__name__,
                metadata_io.fstat.__name__,
                metadata_io.read.__name__,
                metadata_io.close.__name__,
            )
        )
        pre_execution_facts = observe_pre_execution_stimulus(
            case_root, mode, f"injected:{injected_operations}"
        )
        assert row[1] == "public"
        assert row[5] is not None
        assert expected_finding == finding("git-metadata", row[5], row[6])
        git_calls: list[tuple[str, ...]] = []
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []
        trigger_receipts: list[tuple[str, tuple[str, ...]]] = []
        discovery_records: list[protocol.GitMetadataRecord] = []

        def observed_reader(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            observed = traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
                trigger_receipts=trigger_receipts,
            )
            if provenance.role == "discovery" and observed.record is not None:
                discovery_records.append(observed.record)
            elif provenance.role == "dot_git":
                assert discovery_records
                assert provenance.parent_records[0][1] is discovery_records[-1]
            return cast(protocol.GitMetadataReadResult, observed)

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
        finish_metadata_execution(
            case_id,
            role_calls,
            role_traces,
            pre_execution_facts,
            trigger_receipts,
            operational_mode,
        )

    def execute_between_read_case(
        case_id: str,
        case_root: Path,
        after_role: str,
        mutate: Callable[[], None],
        operational_mode: str | None = None,
    ) -> None:
        row = metadata_case(case_id)
        mode = operational_mode or ("conventional" if row[2] == "both" else row[2])
        pre_execution_facts = observe_pre_execution_stimulus(
            case_root, mode, f"race-after:{after_role}"
        )
        assert row[1] == "public"
        assert row[5] is not None
        role_calls: list[str] = []
        role_traces: list[MetadataRoleTrace] = []
        trigger_receipts: list[tuple[str, tuple[str, ...]]] = []
        mutated = False
        inter_role_observation: tuple[str, ...] | None = None
        inter_role_receipt_ordinal: int | None = None
        git_calls: list[tuple[str, ...]] = []

        def mutate_between_roles(
            called_root: str | Path,
            *,
            provenance: protocol.GitMetadataProvenance,
            io: protocol.MetadataIO,
        ) -> protocol.GitMetadataReadResult:
            nonlocal inter_role_observation, inter_role_receipt_ordinal, mutated
            result = traced_metadata_reader(
                called_root,
                provenance=provenance,
                io=io,
                role_calls=role_calls,
                role_traces=role_traces,
                trigger_receipts=trigger_receipts,
            )
            if provenance.role == after_role and not result.findings and not mutated:
                before_record = result.record
                if before_record is None and after_role == "prohibited_http_alternates":
                    before_record = provenance.dot_git_record
                assert before_record is not None
                mutate()
                mutated = True
                try:
                    after_status = before_record.path.lstat()
                except OSError as error:
                    after_type = f"absent:{type(error).__name__}"
                    identity_changed = True
                else:
                    after_type = str(stat.S_IFMT(after_status.st_mode))
                    identity_changed = (before_record.device, before_record.inode) != (
                        after_status.st_dev,
                        after_status.st_ino,
                    )
                inter_role_observation = (
                    f"afterRole={after_role}",
                    f"path={normalized_observed_path(os.fspath(before_record.path))}",
                    f"beforeType={stat.S_IFMT(before_record.mode)}",
                    f"afterType={after_type}",
                    "identityChanged=" + str(identity_changed).lower(),
                    "triggered=true",
                )
                inter_role_receipt_ordinal = len(trigger_receipts)
            return cast(protocol.GitMetadataReadResult, result)

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
        assert mutated
        assert inter_role_observation is not None
        assert inter_role_receipt_ordinal is not None
        trigger_receipts.insert(
            inter_role_receipt_ordinal, ("inter-role-mutation", inter_role_observation)
        )
        finish_metadata_execution(
            case_id,
            role_calls,
            role_traces,
            pre_execution_facts,
            trigger_receipts,
            operational_mode,
        )

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
    successful_git_results = assert_exact_git_transcript(root, freeze, monkeypatch)
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
    verified_oid_values = {
        "C3_HEAD_OID": git(root, "rev-parse", "HEAD").encode(),
        "RED_HEAD_OID": cast(str, freeze["redHead"]).encode(),
        "RED_TREE_OID": cast(str, freeze["redTree"]).encode(),
        "MATRIX_BLOB_OID": cast(str, freeze["matrixBlobOid"]).encode(),
        "CORE_ORACLE_BLOB_OID": cast(str, freeze["focusedOracleBlobs"][0]["blobOid"]).encode(),
        "REPOSITORY_ORACLE_BLOB_OID": cast(
            str, freeze["focusedOracleBlobs"][1]["blobOid"]
        ).encode(),
    }
    assert hashlib.sha256(canonical(EXPECTED_VERIFIED_GIT_OID_MAPPINGS)).hexdigest() == (
        EXPECTED_VERIFIED_GIT_OID_MAPPING_SHA256
    )
    assert len(EXPECTED_VERIFIED_GIT_OID_MAPPINGS) == EXPECTED_VERIFIED_GIT_OID_MAPPING_COUNT
    successful_by_role = dict(zip(roles, successful_git_results, strict=True))
    for role, row_ordinal, column_ordinal, semantic_name, _ in EXPECTED_VERIFIED_GIT_OID_MAPPINGS:
        saved_result = successful_by_role[role]
        assert type(saved_result.stdout) is bytes
        saved_rows = saved_result.stdout.splitlines()
        assert saved_rows[row_ordinal].split()[column_ordinal] == verified_oid_values[semantic_name]
    assert successful_by_role["head"].stdout == verified_oid_values["C3_HEAD_OID"] + b"\n"
    assert successful_by_role["ancestry_chain"].stdout == (
        verified_oid_values["C3_HEAD_OID"] + b" " + verified_oid_values["RED_HEAD_OID"] + b"\n"
    )
    assert successful_by_role["red_objects"].stdout == b"".join(
        verified_oid_values[name] + b"\n"
        for name in (
            "RED_TREE_OID",
            "MATRIX_BLOB_OID",
            "CORE_ORACLE_BLOB_OID",
            "REPOSITORY_ORACLE_BLOB_OID",
        )
    )
    baseline_position_tokens = tuple(
        (
            role,
            *position_bound_git_tokens(role, successful_by_role[role].stdout, verified_oid_values),
        )
        for role in ("head", "ancestry_chain", "red_objects")
    )
    assert sum(len(row[2]) for row in baseline_position_tokens) == 7
    assert all(row[3] == () for row in baseline_position_tokens)
    assert tuple(name for row in baseline_position_tokens for name in row[2]) == tuple(
        mapping[3] for mapping in EXPECTED_VERIFIED_GIT_OID_MAPPINGS
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
    builder_contract = dict(
        (name, (builder, relation)) for name, builder, relation in TEXTUAL_TRANSFORMATION_BUILDERS
    )
    assert tuple(builder_contract) == TEXTUAL_TRANSFORMS
    observed_transform_contract: list[tuple[object, ...]] = []
    observed_byte_identities: list[tuple[object, ...]] = []
    observed_hostile_oid_evidence: list[tuple[object, ...]] = []
    return (
        execute_metadata_io_case,
        execute_between_read_case,
        successful_git_results,
        roles,
        verified_oid_values,
        successful_by_role,
        role,
        _,
        saved_result,
        output_caps,
        builder_contract,
        observed_transform_contract,
        observed_byte_identities,
        observed_hostile_oid_evidence,
    )


def _exercise_textual_position_and_git_failures(
    monkeypatch: Any,
    root: Any,
    freeze: Any,
    successful_git_results: Any,
    roles: Any,
    verified_oid_values: Any,
    successful_by_role: Any,
    role: Any,
    saved_result: Any,
    output_caps: Any,
    builder_contract: Any,
    observed_transform_contract: Any,
    observed_byte_identities: Any,
    observed_hostile_oid_evidence: Any,
) -> Any:
    for role, transform_name, applicable, stage, code, location in EXPECTED_TEXTUAL_TRANSFORMATIONS:
        builder, relation = builder_contract[transform_name]
        base_source = "saved-real-success-stdout"
        if not applicable:
            assert role in {
                "object_integrity",
                "red_ancestor",
                "c3_other_scope",
                "c3_freeze_change",
                "c3_freeze_payload",
                "merge_scan",
            }
            if role == "merge_scan":
                assert transform_name == "missing_lf"
            base_source = "no-canonical-text-output"
            observed_transform_contract.append(
                (
                    role,
                    transform_name,
                    applicable,
                    base_source,
                    builder,
                    relation,
                    stage,
                    code,
                    location,
                )
            )
            assert stage is code is location is None
            continue
        assert stage is not None and code is not None and location is not None
        ordinal = roles.index(role)
        saved_result = successful_git_results[ordinal]
        assert type(saved_result) is subprocess.CompletedProcess
        assert type(saved_result.stdout) is bytes
        saved_stdout = saved_result.stdout
        transformed_payload = apply_textual_transform(role, transform_name, freeze, saved_stdout)
        assert transformed_payload != saved_stdout
        assert_independent_textual_relation(
            role, transform_name, freeze, saved_stdout, transformed_payload
        )
        normalized_base, base_token_shape = normalized_git_text_bytes(
            role, saved_stdout, verified_oid_values
        )
        normalized_transformed, transformed_token_shape = normalized_git_text_bytes(
            role, transformed_payload, verified_oid_values
        )
        if role in {"head", "ancestry_chain", "red_objects", "merge_scan"}:
            _, independently_verified_names, hostile_tokens = position_bound_git_tokens(
                role, transformed_payload, verified_oid_values
            )
            assert independently_verified_names == transformed_token_shape
            if hostile_tokens:
                observed_hostile_oid_evidence.append(
                    (
                        role,
                        transform_name,
                        tuple(hostile_tokens),
                        transformed_token_shape,
                        hashlib.sha256(normalized_transformed).hexdigest(),
                    )
                )
        identity_mode = (
            "named-dynamic-oid-token"
            if role in {"head", "ancestry_chain", "red_objects"}
            else "raw-non-oid-bytes"
        )
        byte_identity: NormalizedGitByteIdentity = (
            role,
            transform_name,
            identity_mode,
            (base_token_shape, transformed_token_shape),
            len(normalized_base),
            hashlib.sha256(normalized_base).hexdigest(),
            len(normalized_transformed),
            hashlib.sha256(normalized_transformed).hexdigest(),
        )
        assert len(byte_identity) == len(TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_FIELDS)
        observed_byte_identities.append(byte_identity)
        observed_transform_contract.append(
            (
                role,
                transform_name,
                applicable,
                base_source,
                builder,
                relation,
                stage,
                code,
                location,
            )
        )
        transform_calls: list[tuple[str, ...]] = []

        def inject_textual_transform(
            argv: tuple[str, ...], **kwargs: Any
        ) -> subprocess.CompletedProcess[bytes]:
            call_ordinal = len(transform_calls)
            transform_calls.append(argv)
            result = REAL_SUBPROCESS_RUN(argv, **kwargs)
            if call_ordinal != ordinal:
                return result
            assert type(result) is subprocess.CompletedProcess
            assert result.args == saved_result.args
            assert result.returncode == saved_result.returncode
            assert result.stdout == saved_result.stdout
            assert result.stderr == saved_result.stderr
            return subprocess.CompletedProcess(
                result.args,
                result.returncode,
                transformed_payload,
                result.stderr,
            )

        with monkeypatch.context() as textual_patch:
            textual_patch.setattr(PROTOCOL_SUBPROCESS, "run", inject_textual_transform)
            assert protocol.validate_repository_freeze(root) == finding(stage, code, location)
        assert tuple(transform_calls) == expected_git_argv(root, freeze)[: ordinal + 1]
    assert len(observed_transform_contract) == TEXTUAL_TRANSFORMATION_COUNT
    assert tuple(item[:3] + item[6:] for item in observed_transform_contract) == (
        EXPECTED_TEXTUAL_TRANSFORMATIONS
    )
    assert hashlib.sha256(canonical(observed_transform_contract)).hexdigest() == (
        TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_SHA256
    )
    assert len(observed_byte_identities) == TEXTUAL_TRANSFORMATION_APPLICABLE_COUNT
    assert len(set(observed_byte_identities)) == len(observed_byte_identities)
    assert tuple(observed_byte_identities) == EXPECTED_NORMALIZED_GIT_BYTE_IDENTITIES
    assert hashlib.sha256(canonical(observed_byte_identities)).hexdigest() == (
        EXPECTED_NORMALIZED_GIT_BYTE_IDENTITY_SHA256
    )
    assert tuple(observed_hostile_oid_evidence) == EXPECTED_HOSTILE_GIT_OID_EVIDENCE
    assert len(observed_hostile_oid_evidence) == EXPECTED_HOSTILE_GIT_OID_EVIDENCE_COUNT
    assert hashlib.sha256(canonical(observed_hostile_oid_evidence)).hexdigest() == (
        EXPECTED_HOSTILE_GIT_OID_EVIDENCE_SHA256
    )
    assert (
        dict((row[0:2], row[2]) for row in observed_hostile_oid_evidence)[
            ("merge_scan", "corrupt_token")
        ]
        != dict((row[0:2], row[2]) for row in observed_hostile_oid_evidence)[
            ("merge_scan", "valid_token")
        ]
    )
    assert len(EXPECTED_POSITION_BOUND_GIT_CASES) == EXPECTED_POSITION_BOUND_GIT_CASE_COUNT
    assert hashlib.sha256(canonical(EXPECTED_POSITION_BOUND_GIT_CASES)).hexdigest() == (
        EXPECTED_POSITION_BOUND_GIT_CASE_SHA256
    )
    position_payloads = {
        "ancestry-reversed": verified_oid_values["RED_HEAD_OID"]
        + b" "
        + verified_oid_values["C3_HEAD_OID"]
        + b"\n",
        "ancestry-missing-token": verified_oid_values["C3_HEAD_OID"] + b"\n",
        "ancestry-duplicate-token": successful_by_role["ancestry_chain"].stdout.rstrip(b"\n")
        + b" "
        + verified_oid_values["RED_HEAD_OID"]
        + b"\n",
        "ancestry-known-oid-wrong-column": successful_by_role["ancestry_chain"].stdout.rstrip(b"\n")
        + b" "
        + verified_oid_values["C3_HEAD_OID"]
        + b"\n",
        "red-objects-missing-row": b"".join(
            verified_oid_values[name] + b"\n"
            for name in ("RED_TREE_OID", "MATRIX_BLOB_OID", "CORE_ORACLE_BLOB_OID")
        ),
        "red-objects-swapped-rows": b"".join(
            verified_oid_values[name] + b"\n"
            for name in (
                "MATRIX_BLOB_OID",
                "RED_TREE_OID",
                "CORE_ORACLE_BLOB_OID",
                "REPOSITORY_ORACLE_BLOB_OID",
            )
        ),
        "head-corrupt-uppercase": b"A" + verified_oid_values["C3_HEAD_OID"][1:] + b"\n",
        "head-valid-but-wrong": verified_oid_values["RED_HEAD_OID"] + b"\n",
    }
    for (
        case_id,
        role,
        _,
        stage,
        code,
        location,
        stopped_role_prefix,
    ) in EXPECTED_POSITION_BOUND_GIT_CASES:
        payload = position_payloads[case_id]
        _, semantic_vector, hostile_vector = position_bound_git_tokens(
            role, payload, verified_oid_values
        )
        assert hostile_vector, case_id
        assert len(semantic_vector) < len(
            tuple(mapping for mapping in EXPECTED_VERIFIED_GIT_OID_MAPPINGS if mapping[0] == role)
        ) or case_id in {"ancestry-duplicate-token", "ancestry-known-oid-wrong-column"}
        target_ordinal = roles.index(role)
        position_case_calls: list[tuple[str, ...]] = []

        def inject_position_case(
            argv: tuple[str, ...], **kwargs: Any
        ) -> subprocess.CompletedProcess[bytes]:
            call_ordinal = len(position_case_calls)
            position_case_calls.append(argv)
            result = REAL_SUBPROCESS_RUN(argv, **kwargs)
            if call_ordinal != target_ordinal:
                return result
            saved = successful_git_results[target_ordinal]
            assert result.args == saved.args
            assert result.returncode == saved.returncode
            assert result.stdout == saved.stdout
            assert result.stderr == saved.stderr
            return subprocess.CompletedProcess(
                result.args, result.returncode, payload, result.stderr
            )

        with monkeypatch.context() as position_patch:
            position_patch.setattr(PROTOCOL_SUBPROCESS, "run", inject_position_case)
            assert protocol.validate_repository_freeze(root) == finding(stage, code, location)
        assert tuple(roles[: len(position_case_calls)]) == stopped_role_prefix
        assert (
            tuple(position_case_calls)
            == expected_git_argv(root, freeze)[: len(position_case_calls)]
        )
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
    return (
        role,
        _,
        code,
        location,
        ordinal,
        case_id,
        payload,
        argv,
        transform,
        unsupported_returncode,
    )


def _exercise_git_output_and_ancestry_boundaries(
    monkeypatch: Any,
    root: Any,
    freeze: Any,
    roles: Any,
    role: Any,
    output_caps: Any,
    code: Any,
    location: Any,
    ordinal: Any,
    payload: Any,
    argv: Any,
    transform: Any,
    unsupported_returncode: Any,
) -> Any:
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
    return (
        role,
        code,
        location,
        ordinal,
        payload,
        cap,
        returncode,
        value,
        author_payload,
        expected,
    )


def _exercise_git_bundle_corruption_and_linked_baseline(
    monkeypatch: Any,
    tmp_path: Any,
    root: Any,
    freeze: Any,
    execute_metadata_success_case: Any,
    execute_metadata_case: Any,
    execute_metadata_io_case: Any,
    code: Any,
    location: Any,
    ordinal: Any,
    payload: Any,
    returncode: Any,
    author_payload: Any,
    expected: Any,
) -> Any:
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
    return (
        _,
        code,
        location,
        ordinal,
        expected,
        count,
        relative,
        metadata_root,
        linked_root,
        linked_git_dir,
        replacement_io,
    )


def _exercise_root_replacement_and_metadata_modes(
    tmp_path: Any,
    execute_metadata_case: Any,
    execute_metadata_io_case: Any,
    execute_between_read_case: Any,
    code: Any,
    location: Any,
    metadata_root: Any,
    replacement_io: Any,
) -> Any:
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
        return cast(os.stat_result, before)

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
        return cast(os.stat_result, before)

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
        return cast(os.stat_result, before)

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
        return cast(os.stat_result, before)

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
        return cast(os.stat_result, before)

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
    return (_, code, name, public_race_root, public_dot_git)


def _exercise_metadata_races_and_errors(
    tmp_path: Any,
    execute_metadata_io_case: Any,
    _: Any,
    case_id: Any,
    public_race_root: Any,
    public_dot_git: Any,
) -> Any:
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

            changed_fstat.__name__ = f"changed_fstat_coordinate_{stat_index}_value_{stat_value}"

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
    return (_, case_id, system_io, operational_mode, stat_value, case_base, linked_record_cases)


def _exercise_linked_records_precedence_and_raw_io(
    monkeypatch: Any,
    tmp_path: Any,
    execute_metadata_case: Any,
    execute_metadata_io_case: Any,
    role: Any,
    _: Any,
    code: Any,
    count: Any,
    relative: Any,
    linked_root: Any,
    linked_git_dir: Any,
    system_io: Any,
    operational_mode: Any,
    case_base: Any,
    linked_record_cases: Any,
) -> Any:
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
                preserved_ancestor = ancestor.with_name(
                    f"{ancestor.name}-preserved-for-{Path(relative).name}"
                )
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
        return cast(os.stat_result, before)

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
    composition_root, _ = create_real_git_freeze(tmp_path / "metadata-composition")
    composition_matrix = composition_root / MATRIX_PATH.relative_to(ROOT)
    source_matrix_bytes = composition_matrix.read_bytes()
    correct_matrix = json.loads(source_matrix_bytes.decode("utf-8", errors="strict"))
    assert type(correct_matrix) is dict
    correct_matrix_bytes = canonical(correct_matrix) + b"\n"
    composition_matrix.write_bytes(correct_matrix_bytes)
    assert canonical(correct_matrix) + b"\n" == correct_matrix_bytes
    correct_schema = correct_matrix["schemaVersion"]
    assert type(correct_schema) is str
    wrong_matrix = deepcopy(correct_matrix)
    wrong_matrix["schemaVersion"] = "WrongMatrixV1"
    expected_wrong_matrix_bytes = canonical(wrong_matrix) + b"\n"
    composition_matrix.write_bytes(expected_wrong_matrix_bytes)
    observed_wrong_matrix_bytes, selected_wrong_matrix_bytes = reread_matrix_with_controlled_decoy(
        composition_matrix,
        correct_matrix_bytes,
        substitute_decoy=False,
    )
    assert observed_wrong_matrix_bytes == expected_wrong_matrix_bytes
    assert selected_wrong_matrix_bytes == observed_wrong_matrix_bytes
    assert observed_wrong_matrix_bytes != correct_matrix_bytes
    observed_schema_descriptor, observed_schema_identity = observed_matrix_schema_evidence(
        selected_wrong_matrix_bytes, correct_schema
    )
    control_schema_descriptor, _ = observed_matrix_schema_evidence(
        correct_matrix_bytes, correct_schema
    )
    assert observed_schema_descriptor == "matrix-schema-version-wrong"
    assert control_schema_descriptor == "matrix-schema-version-current"
    assert observed_schema_descriptor != control_schema_descriptor
    assert observed_schema_identity == (
        "74459b011344be2e067eb5bba03760fecd87ff5895e694a116943a6b5a6f5e6d"
    )
    reread_for_mutant, selected_decoy_bytes = reread_matrix_with_controlled_decoy(
        composition_matrix,
        correct_matrix_bytes,
        substitute_decoy=True,
    )
    assert reread_for_mutant == expected_wrong_matrix_bytes
    decoy_descriptor, decoy_identity = observed_matrix_schema_evidence(
        selected_decoy_bytes, correct_schema
    )
    with pytest.raises(AssertionError, match="controlled decoy changed observed schema evidence"):
        assert (decoy_descriptor, decoy_identity) == (
            observed_schema_descriptor,
            observed_schema_identity,
        ), "controlled decoy changed observed schema evidence"
    composition_git = composition_root / ".git"
    preserved_composition_git = composition_root / ".git-preserved"
    composition_git.rename(preserved_composition_git)
    composition_git.symlink_to(preserved_composition_git, target_is_directory=True)
    real_discovery = cast(protocol.GitDiscoveryResult, PROTOCOL_DISCOVERY(composition_root))
    expected_composition_finding = finding(
        "git-metadata", "ACP.GIT_METADATA.TARGET_SYMLINK", ".git"
    )
    assert real_discovery.binding is None
    assert real_discovery.findings == expected_composition_finding
    discovery_calls: list[Path] = []
    governed_calls: list[tuple[Path, str]] = []

    def one_call_real_discovery(called_root: Path) -> protocol.GitDiscoveryResult:
        discovery_calls.append(called_root)
        assert called_root == composition_root
        return real_discovery

    def later_governed_failure(called_root: Path, relative: str) -> protocol.GovernedReadResult:
        governed_calls.append((called_root, relative))
        return cast(protocol.GovernedReadResult, PROTOCOL_GOVERNED_READER(called_root, relative))

    with monkeypatch.context() as composition_patch:
        composition_patch.setattr(protocol, "discover_git_repository", one_call_real_discovery)
        composition_patch.setattr(protocol, "_read_governed_bytes", later_governed_failure)
        composition_patch.setattr(
            PROTOCOL_SUBPROCESS,
            "run",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("Git must not run after metadata failure")
            ),
        )
        validation_findings = protocol.validate_repository_freeze(composition_root)
        assert validation_findings is real_discovery.findings
        assert validation_findings == expected_composition_finding
    assert discovery_calls == [composition_root]
    assert governed_calls == []
    executed_precedence_row = (
        "metadata-target-symlink-plus-matrix-schema",
        "validate_repository_freeze",
        "dot-git-target-symlink",
        observed_schema_descriptor,
        observed_schema_identity,
        validation_findings[0].stage,
        validation_findings[0].phase,
        validation_findings[0].code,
        validation_findings[0].location,
        "identity" if validation_findings is real_discovery.findings else "copy",
        len(governed_calls),
        0,
    )
    assert (executed_precedence_row,) == EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES
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
    return (
        role,
        _,
        code,
        io_root,
        io_record,
        io_payload,
        real_io,
        opened_fds,
        closed_fds,
        metadata_operations,
        chunked_io,
        identity,
        expected_ancestor_records,
    )


def _exercise_raw_io_and_receipt_baseline(
    tmp_path: Any,
    metadata_stimulus_rows: Any,
    observe_pre_execution_stimulus: Any,
    traced_metadata_reader: Any,
    finish_metadata_execution: Any,
    _: Any,
    code: Any,
    case_id: Any,
    stat_value: Any,
    io_root: Any,
    io_record: Any,
    io_payload: Any,
    real_io: Any,
    opened_fds: Any,
    closed_fds: Any,
    metadata_operations: Any,
    chunked_io: Any,
    identity: Any,
    expected_ancestor_records: Any,
) -> Any:
    short_roles: list[str] = []
    short_traces: list[MetadataRoleTrace] = []
    short_trigger_receipts: list[tuple[str, tuple[str, ...]]] = []
    short_stimulus = observe_pre_execution_stimulus(io_root, "linked", "one-byte-reads")
    short_stimulus = (
        *short_stimulus,
        ("read.chunkPlan", "one-byte-until-eof"),
        ("read.expectedCallCount", str(len(io_payload) + 1)),
        ("close.configuredBehavior", "reverse-complete"),
    )
    assert traced_metadata_reader(
        io_root,
        provenance=protocol.GitMetadataProvenance("dot_git", None),
        io=chunked_io,
        role_calls=short_roles,
        role_traces=short_traces,
        trigger_receipts=short_trigger_receipts,
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
    short_read_sizes = tuple(len(item[3]) for item in metadata_operations if item[0] == "read")
    assert short_read_sizes == (*((1,) * len(io_payload)), 0)
    finish_metadata_execution(
        "short-read", short_roles, short_traces, short_stimulus, short_trigger_receipts
    )
    reverse_opened: list[int] = []
    reverse_closed: list[int] = []

    def reverse_open(path: str, flags: int, *, dir_fd: int | None = None) -> int:
        descriptor = real_io.open(path, flags, dir_fd=dir_fd)
        reverse_opened.append(descriptor)
        return cast(int, descriptor)

    def reverse_close(file_descriptor: int) -> None:
        reverse_closed.append(file_descriptor)
        real_io.close(file_descriptor)

    reverse_roles: list[str] = []
    reverse_traces: list[MetadataRoleTrace] = []
    reverse_trigger_receipts: list[tuple[str, tuple[str, ...]]] = []
    reverse_stimulus = observe_pre_execution_stimulus(
        io_root, "linked", "system-read-callback+reverse-descriptor-cleanup"
    )
    reverse_stimulus = (
        *reverse_stimulus,
        ("read.chunkPlan", "system-until-eof"),
        ("read.expectedCallCount", "reader-controlled"),
        ("close.configuredBehavior", "reverse-complete"),
    )
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
        trigger_receipts=reverse_trigger_receipts,
    )
    assert reverse_result.findings == ()
    assert reverse_closed == reverse_opened[::-1]
    finish_metadata_execution(
        "reverse-close", reverse_roles, reverse_traces, reverse_stimulus, reverse_trigger_receipts
    )
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
        return cast(os.stat_result, result)

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
        return cast(os.stat_result, result)

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
        return cast(int, descriptor)

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
        return cast(os.stat_result, before)

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
    expected_stimulus_rows = tuple(
        (execution[2], execution[3]) for execution in EXPECTED_METADATA_EXECUTIONS
    )
    for execution in EXPECTED_METADATA_EXECUTIONS:
        case_id = execution[0][0]
        for _, observed_value in execution[2]:
            assert case_id not in observed_value
            assert "/private$TMP" not in observed_value
            assert "$TMP_NAME" not in observed_value
            if "$TMP" in observed_value:
                assert re.search(
                    r"\$TMP/(?:\$CASE|\./\$CASE|\.\./\$CASE|/\$CASE)(?:/|$)",
                    observed_value,
                )
    assert tuple(metadata_stimulus_rows) == expected_stimulus_rows
    return (code, expected_stimulus_rows, execution)


def _assert_receipt_integrity_and_composed_mutants(
    monkeypatch: Any,
    metadata_execution_rows: Any,
    metadata_stimulus_rows: Any,
    metadata_trigger_rows: Any,
    metadata_raw_read_rows: Any,
    metadata_close_order_rows: Any,
    metadata_normalized_payload_rows: Any,
    metadata_configured_plan_receipts: Any,
    role: Any,
    ordinal: Any,
    cap: Any,
    value: Any,
    expected: Any,
    name: Any,
    expected_stimulus_rows: Any,
) -> Any:
    assert hashlib.sha256(canonical(expected_stimulus_rows)).hexdigest() == (
        EXPECTED_METADATA_STIMULUS_SHA256
    )
    assert (
        len(metadata_stimulus_rows)
        == EXPECTED_METADATA_STIMULUS_COUNT
        == EXPECTED_METADATA_EXECUTION_COUNT
        == 129
    )
    observed_stimulus_identities = tuple(
        stimulus_hash for _, stimulus_hash in metadata_stimulus_rows
    )
    assert len(set(observed_stimulus_identities)) == len(observed_stimulus_identities)
    for ordinal, (facts, stimulus_hash) in enumerate(metadata_stimulus_rows):
        swapped_facts = metadata_stimulus_rows[(ordinal + 1) % len(metadata_stimulus_rows)][0]
        assert swapped_facts != facts
        assert hashlib.sha256(canonical(swapped_facts)).hexdigest() != stimulus_hash
    assert tuple(metadata_execution_rows) == EXPECTED_METADATA_EXECUTIONS
    assert hashlib.sha256(canonical(metadata_execution_rows)).hexdigest() == (
        EXPECTED_METADATA_FULL_EXECUTION_SHA256
    )
    assert len(metadata_trigger_rows) == EXPECTED_METADATA_TRIGGER_RECEIPT_COUNT
    for receipt in metadata_trigger_rows:
        for role, values in receipt:
            if role == "inter-role-mutation":
                assert (
                    "role",
                    *(value.split("=", 1)[0] for value in values),
                ) == EXPECTED_METADATA_INTER_ROLE_TRIGGER_RECEIPT_FIELDS
            else:
                assert len(values) + 1 == len(EXPECTED_METADATA_TRIGGER_RECEIPT_FIELDS)
    assert hashlib.sha256(canonical(metadata_trigger_rows)).hexdigest() == (
        EXPECTED_METADATA_TRIGGER_RECEIPT_SHA256
    )
    assert len(metadata_raw_read_rows) == EXPECTED_METADATA_RAW_READ_COUNT
    assert hashlib.sha256(canonical(metadata_raw_read_rows)).hexdigest() == (
        EXPECTED_METADATA_RAW_READ_SHA256
    )
    assert len(metadata_close_order_rows) == EXPECTED_METADATA_CLOSE_ORDER_COUNT
    assert hashlib.sha256(canonical(metadata_close_order_rows)).hexdigest() == (
        EXPECTED_METADATA_CLOSE_ORDER_SHA256
    )
    assert len(metadata_normalized_payload_rows) == EXPECTED_METADATA_NORMALIZED_PAYLOAD_COUNT
    assert hashlib.sha256(canonical(metadata_normalized_payload_rows)).hexdigest() == (
        EXPECTED_METADATA_NORMALIZED_PAYLOAD_SHA256
    )
    assert len(metadata_configured_plan_receipts) == (
        EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_COUNT
    )
    assert hashlib.sha256(canonical(metadata_configured_plan_receipts)).hexdigest() == (
        EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_SHA256
    )
    configured_bindings = tuple(
        (receipt[18], receipt[9], tuple(receipt[14:18]), tuple(receipt[10:14]))
        for receipt in metadata_configured_plan_receipts
    )
    assert configured_bindings == EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDINGS
    assert len(EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_FIELDS) == 4
    assert len(configured_bindings) == EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_COUNT
    assert hashlib.sha256(canonical(configured_bindings)).hexdigest() == (
        EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_SHA256
    )
    assert len(EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAPS) == (
        EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_COUNT
    )
    assert len(EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_FIELDS) == 2
    assert (
        hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAPS)).hexdigest()
        == EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_SHA256
    )
    inter_receipt = metadata_configured_plan_receipts[5]
    assert len(EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_FIELDS) == 4
    assert len(EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS) == (
        EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_COUNT
    )
    assert (
        hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS)).hexdigest()
        == EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_SHA256
    )
    for (
        mutant_id,
        hostile_target_ordinal,
        changed_field_set,
        finding_location,
    ) in EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS:
        assert changed_field_set == "interRoleSchedule.targetRoleOrdinal"
        assert finding_location == "configuredPlanReceipts[5].interRoleEvidence"
        hostile_schedules = tuple(
            (*row[:2], hostile_target_ordinal, *row[3:]) if row[0] == "linked_git_dir" else row
            for row in EXPECTED_METADATA_CONFIGURED_INTER_ROLE_SCHEDULES
        )
        with monkeypatch.context() as ordinal_patch:
            ordinal_patch.setattr(
                sys.modules[__name__],
                "EXPECTED_METADATA_CONFIGURED_INTER_ROLE_SCHEDULES",
                hostile_schedules,
            )
            assert validate_configured_raw_receipt(
                tuple(inter_receipt[1:9]), inter_receipt[9], 5
            ) == _configured_finding(5, "interRoleEvidence"), mutant_id
    empty_raw_fields: list[tuple[str, ...]] = [()] * 8
    for field_ordinal, (field_name, field_cap) in enumerate(
        EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS
    ):
        at_count_cap = list(empty_raw_fields)
        at_count_cap[field_ordinal] = ("x",) * field_cap
        assert configured_raw_bounds_findings(tuple(at_count_cap), 14) == ()
        over_count_cap = list(at_count_cap)
        over_count_cap[field_ordinal] = (*over_count_cap[field_ordinal], "x")
        assert configured_raw_bounds_findings(
            tuple(over_count_cap), 14
        ) == configured_receipt_finding(14, f"{field_name}.countLimit")
        at_item_cap = list(empty_raw_fields)
        at_item_cap[field_ordinal] = ("x" * EXPECTED_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP,)
        assert configured_raw_bounds_findings(tuple(at_item_cap), 14) == ()
        over_item_cap = list(empty_raw_fields)
        over_item_cap[field_ordinal] = ("x" * (EXPECTED_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP + 1),)
        assert configured_raw_bounds_findings(
            tuple(over_item_cap), 14
        ) == configured_receipt_finding(14, f"{field_name}.itemByteLimit")
        with monkeypatch.context() as count_cap_patch:
            count_cap_patch.setattr(
                sys.modules[__name__],
                "EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS",
                tuple(
                    (name, cap + (name == field_name))
                    for name, cap in EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS
                ),
            )
            assert configured_raw_bounds_findings(tuple(over_count_cap), 14) == ()
        with monkeypatch.context() as item_cap_patch:
            item_cap_patch.setattr(
                sys.modules[__name__],
                "EXPECTED_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP",
                EXPECTED_METADATA_CONFIGURED_RAW_ITEM_BYTE_CAP + 1,
            )
            assert configured_raw_bounds_findings(tuple(over_item_cap), 14) == ()
    precedence_receipt = metadata_configured_plan_receipts[14]
    precedence_raw = tuple(precedence_receipt[1:9])
    precedence_observed = tuple(precedence_receipt[14:18])
    precedence_projection = tuple(precedence_receipt[10:14])
    precedence_plan = EXPECTED_METADATA_CONFIGURED_PLANS[14][1:]
    over_count_and_encoding = list(precedence_raw)
    over_count_and_encoding[0] = ("x",) * (
        dict(EXPECTED_METADATA_CONFIGURED_RAW_FIELD_CAPS)["callbackArguments"] + 1
    )
    over_count_and_encoding[1] = ("\ud800",)
    stale_role_raw = list(precedence_raw)
    stale_role_raw[2] = ()
    argument_event_raw = list(precedence_raw)
    changed_arguments = list(cast(tuple[str, ...], argument_event_raw[0]))
    old_prefix = ":".join(changed_arguments[0].split(":")[:4])
    changed_arguments[0] = changed_arguments[0].replace("event-0:", "event-99:", 1)
    new_prefix = ":".join(changed_arguments[0].split(":")[:4])
    changed_events = list(cast(tuple[str, ...], argument_event_raw[1]))
    matching_event = next(
        ordinal
        for ordinal, value in enumerate(changed_events)
        if value.startswith(old_prefix + ":")
    )
    changed_events[matching_event] = changed_events[matching_event].replace(
        old_prefix, new_prefix, 1
    )
    argument_event_raw[0] = tuple(changed_arguments)
    argument_event_raw[1] = tuple(changed_events)
    metadata_derived_raw = list(precedence_raw)
    for field_ordinal in (3, 4, 5, 6):
        metadata_derived_raw[field_ordinal] = ()
    composed_findings = (
        bind_configured_plan([], "stale", None, None, None, True),
        bind_configured_plan(
            list(precedence_raw),
            "stale",
            precedence_observed,
            precedence_projection,
            precedence_plan,
            14,
        ),
        bind_configured_plan(
            tuple(over_count_and_encoding),
            hashlib.sha256(canonical(tuple(over_count_and_encoding))).hexdigest(),
            precedence_observed,
            precedence_projection,
            precedence_plan,
            14,
        ),
        bind_configured_plan(
            tuple(stale_role_raw),
            precedence_receipt[9],
            precedence_observed,
            precedence_projection,
            precedence_plan,
            14,
        ),
        bind_configured_plan(
            tuple(argument_event_raw),
            hashlib.sha256(canonical(tuple(argument_event_raw))).hexdigest(),
            precedence_observed,
            precedence_projection,
            precedence_plan,
            14,
        ),
        bind_configured_plan(
            tuple(metadata_derived_raw),
            hashlib.sha256(canonical(tuple(metadata_derived_raw))).hexdigest(),
            precedence_observed,
            precedence_projection,
            precedence_plan,
            14,
        ),
        bind_configured_plan(
            precedence_raw,
            precedence_receipt[9],
            None,
            ("bad", *precedence_projection[1:]),
            ("worse", *precedence_plan[1:]),
            14,
        ),
        bind_configured_plan(
            precedence_raw,
            precedence_receipt[9],
            precedence_observed,
            ("bad", *precedence_projection[1:]),
            ("worse", *precedence_plan[1:]),
            14,
        ),
    )
    for (
        mutant_id,
        _,
        changed_field_set,
        coordinate,
        finding_location,
    ), actual in zip(
        EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE,
        composed_findings,
        strict=True,
    ):
        assert changed_field_set
        expected = configured_receipt_finding(0 if coordinate == "receiptIndex" else 14, coordinate)
        assert expected[0].location == finding_location
        assert actual == expected, mutant_id
    assert len(EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_FIELDS) == 5
    assert len(EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE) == (
        EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_COUNT
    )
    assert (
        hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE)).hexdigest()
        == EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_SHA256
    )
    for donor_index, recipient_index in EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAPS:
        donor = configured_bindings[donor_index]
        assert (
            EXPECTED_METADATA_CONFIGURED_PLANS[donor_index][1:]
            == (EXPECTED_METADATA_CONFIGURED_PLANS[recipient_index][1:])
        )
        assert bind_configured_receipt_schedule(
            *donor,
            recipient_index,
        ) == configured_receipt_finding(recipient_index, "executionEvidenceIdentity")
        recipient = configured_bindings[recipient_index]
        if donor[1] != recipient[1]:
            assert bind_configured_receipt_schedule(
                recipient[0], donor[1], donor[2], donor[3], recipient_index
            ) == configured_receipt_finding(recipient_index, "rawEvidenceIdentity")
        else:
            assert donor[1:] == recipient[1:]
    assert len(EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS) == (
        EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_COUNT
    )
    configured_mutant_ids = tuple(row[0] for row in EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS)
    assert len(configured_mutant_ids) == len(set(configured_mutant_ids))
    assert hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS)).hexdigest() == (
        EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_SHA256
    )
    receipt_index = {
        cast(str, receipt[0]): ordinal
        for ordinal, receipt in enumerate(metadata_configured_plan_receipts)
    }
    assert receipt_index["fstat-type@linked"] == 14
    assert receipt_index["between-read-linked-directory@linked"] == 5
    assert receipt_index["close-error@linked"] == 21
    return (
        ordinal,
        receipt,
        mutant_id,
        changed_field_set,
        coordinate,
        recipient_index,
        receipt_index,
    )


def _assert_configured_receipt_mutants_and_history(
    monkeypatch: Any,
    metadata_execution_rows: Any,
    metadata_trigger_rows: Any,
    metadata_configured_plan_receipts: Any,
    ordinal: Any,
    name: Any,
    execution: Any,
    receipt: Any,
    mutant_id: Any,
    changed_field_set: Any,
    coordinate: Any,
    recipient_index: Any,
    receipt_index: Any,
) -> Any:
    for (
        mutant_id,
        execution_id,
        expected_coordinate,
        mutation_layer,
        changed_field_set,
        mutant_operation,
        raw_identity_action,
        expected_location,
    ) in EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS:
        index = receipt_index[execution_id]
        finding_index = 0 if mutation_layer == "index" else index
        assert expected_location == (
            f"configuredPlanReceipts[{finding_index}].{expected_coordinate}"
        )
        configured_receipt = metadata_configured_plan_receipts[index]
        declared_plan = cast(
            tuple[str, ...],
            next(row[1:] for row in EXPECTED_METADATA_CONFIGURED_PLANS if row[0] == execution_id),
        )
        (
            mutated_raw_object,
            mutated_identity_object,
            mutated_observation_object,
            mutated_projection_object,
            mutated_declared_object,
            mutated_index_object,
        ) = apply_configured_receipt_mutant(
            configured_receipt,
            declared_plan,
            index,
            mutant_operation,
            raw_identity_action,
        )
        assert mutation_layer in {
            "index",
            "raw",
            "observed",
            "projection",
            "declared",
        }
        changed_fields: list[str] = []
        original_raw = tuple(configured_receipt[1:9])
        if mutated_raw_object != original_raw:
            if type(mutated_raw_object) is not tuple or len(mutated_raw_object) != 8:
                changed_fields.append("rawReceipt")
            else:
                changed_fields.extend(
                    field
                    for field, before, after in zip(
                        EXPECTED_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS,
                        original_raw,
                        cast(tuple[object, ...], mutated_raw_object),
                        strict=True,
                    )
                    if before != after
                )
        for field, before, after in (
            ("observed", tuple(configured_receipt[14:18]), mutated_observation_object),
            ("projection", tuple(configured_receipt[10:14]), mutated_projection_object),
            ("declared", declared_plan, mutated_declared_object),
            ("index", index, mutated_index_object),
        ):
            if before != after:
                changed_fields.append(field)
        assert "+".join(changed_fields) == changed_field_set, mutant_id
        assert changed_fields
        if raw_identity_action == "recompute-after-mutation":
            assert (
                mutated_identity_object == hashlib.sha256(canonical(mutated_raw_object)).hexdigest()
            )
        else:
            assert raw_identity_action == "preserve-stale"
            assert mutated_identity_object == configured_receipt[9]
        assert bind_configured_plan(
            mutated_raw_object,
            mutated_identity_object,
            mutated_observation_object,
            mutated_projection_object,
            mutated_declared_object,
            mutated_index_object,
        ) == (
            protocol.Finding(
                "evidence",
                "CURRENT",
                "ACP.EVIDENCE.CONFIGURED_PLAN_MISMATCH",
                expected_location,
            ),
        ), mutant_id
    donor_receipt = metadata_configured_plan_receipts[0]
    donor_raw = tuple(donor_receipt[1:9])
    donor_identity = donor_receipt[9]
    donor_projection = cast(tuple[str, ...], tuple(donor_receipt[10:14]))
    donor_observation = tuple(donor_receipt[14:18])
    donor_plan = cast(tuple[str, ...], EXPECTED_METADATA_CONFIGURED_PLANS[0][1:])
    assert (
        bind_configured_plan(
            donor_raw,
            donor_identity,
            donor_observation,
            donor_projection,
            donor_plan,
            0,
        )
        == ()
    )
    donor_parsed = validate_configured_raw_receipt(donor_raw, donor_identity, 0)
    permuted_plans = (
        *EXPECTED_METADATA_CONFIGURED_PLANS[1:],
        EXPECTED_METADATA_CONFIGURED_PLANS[0],
    )
    with monkeypatch.context() as plan_table_patch:
        plan_table_patch.setattr(
            sys.modules[__name__],
            "EXPECTED_METADATA_CONFIGURED_PLANS",
            permuted_plans,
        )
        assert validate_configured_raw_receipt(donor_raw, donor_identity, 0) == donor_parsed
        assert (
            bind_configured_plan(
                donor_raw,
                donor_identity,
                donor_observation,
                donor_projection,
                cast(tuple[str, ...], permuted_plans[0][1:]),
                0,
            )
            != ()
        )
    for recipient_index, recipient_plan_row in enumerate(
        EXPECTED_METADATA_CONFIGURED_PLANS[1:], start=1
    ):
        recipient_plan = cast(tuple[str, ...], recipient_plan_row[1:])
        mismatch_coordinate = next(
            coordinate
            for coordinate, donor_value, recipient_value in zip(
                EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS,
                donor_projection,
                recipient_plan,
                strict=True,
            )
            if donor_value != recipient_value
        )
        assert bind_configured_plan(
            donor_raw,
            donor_identity,
            donor_observation,
            donor_projection,
            recipient_plan,
            recipient_index,
        ) == configured_receipt_finding(recipient_index, mismatch_coordinate)
    metadata_execution_ids = tuple(
        f"{execution[0][0]}@{execution[1]}" for execution in metadata_execution_rows
    )
    assert metadata_execution_ids == EXPECTED_METADATA_EXECUTION_IDS
    assert len(metadata_execution_ids) == EXPECTED_METADATA_EXECUTION_COUNT
    assert hashlib.sha256(canonical(metadata_execution_ids)).hexdigest() == (
        EXPECTED_METADATA_EXECUTION_SHA256
    )
    execution_index = {
        execution_id: ordinal for ordinal, execution_id in enumerate(metadata_execution_ids)
    }
    assert len(execution_index) == EXPECTED_METADATA_EXECUTION_COUNT
    group_names = tuple(name for name, _ in EXPECTED_METADATA_FORMER_COLLISION_GROUPS)
    assert len(group_names) == len(set(group_names))
    assert sum(name.startswith("configured-removed-") for name in group_names) == (
        EXPECTED_METADATA_REMOVED_CONFIG_COLLISION_COUNT
    )
    assert len(EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIRS) == (
        EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_COUNT
    )
    assert (
        hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIRS)).hexdigest()
        == EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_SHA256
    )
    configured_class_members = {
        member
        for name, members in EXPECTED_METADATA_FORMER_COLLISION_GROUPS
        if name.startswith("configured-removed-")
        for member in members
    }
    complete_configured_classes = tuple(
        (name, tuple(members))
        for name, members in EXPECTED_METADATA_FORMER_COLLISION_GROUPS
        if name.startswith("configured-removed-")
    )
    observed_historical_containments: list[tuple[object, ...]] = []
    for historical_index, (historical_name, pair) in enumerate(
        EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIRS
    ):
        assert historical_name.startswith("configured-removed-")
        assert len(pair) == len(set(pair)) == 2
        assert set(pair) <= configured_class_members
        class_name, relation_findings = historical_pair_containment(
            pair, complete_configured_classes, historical_index
        )
        assert relation_findings == ()
        assert class_name is not None
        observed_historical_containments.append((historical_name, pair, class_name))
    assert tuple(observed_historical_containments) == (
        EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENTS
    )
    assert len(observed_historical_containments) == (
        EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENT_COUNT
    )
    assert hashlib.sha256(canonical(observed_historical_containments)).hexdigest() == (
        EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENT_SHA256
    )
    cross_mutant_id, cross_pair, cross_location = EXPECTED_METADATA_HISTORICAL_CROSS_CLASS_MUTANT
    assert historical_pair_containment(
        cross_pair, complete_configured_classes, EXPECTED_METADATA_HISTORICAL_PAIR_CONTAINMENT_COUNT
    ) == (
        None,
        (
            protocol.Finding(
                "evidence",
                "CURRENT",
                "ACP.EVIDENCE.HISTORICAL_PAIR_RELATION",
                cross_location,
            ),
        ),
    ), cross_mutant_id
    for _, group_execution_ids in EXPECTED_METADATA_FORMER_COLLISION_GROUPS:
        assert len(group_execution_ids) >= 2
        assert len(group_execution_ids) == len(set(group_execution_ids))
        for source_id in group_execution_ids:
            source_ordinal = execution_index[source_id]
            source_execution = EXPECTED_METADATA_EXECUTIONS[source_ordinal]
            source_binding = (
                source_execution[2],
                source_execution[3],
                metadata_trigger_rows[source_ordinal],
            )
            source_identity = hashlib.sha256(canonical(source_binding)).hexdigest()
            for swapped_id in group_execution_ids:
                if swapped_id == source_id:
                    continue
                swapped_ordinal = execution_index[swapped_id]
                swapped_execution = EXPECTED_METADATA_EXECUTIONS[swapped_ordinal]
                swapped_binding = (
                    swapped_execution[2],
                    swapped_execution[3],
                    metadata_trigger_rows[swapped_ordinal],
                )
                assert swapped_binding != source_binding
                assert hashlib.sha256(canonical(swapped_binding)).hexdigest() != source_identity
    assert len(EXPECTED_METADATA_CONFIGURED_PLANS) == EXPECTED_METADATA_CONFIGURED_PLAN_COUNT
    assert hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_PLANS)).hexdigest() == (
        EXPECTED_METADATA_CONFIGURED_PLAN_SHA256
    )
    plan_by_execution = {row[0]: row[1:] for row in EXPECTED_METADATA_CONFIGURED_PLANS}
    assert len(plan_by_execution) == EXPECTED_METADATA_CONFIGURED_PLAN_COUNT
    stripped_facts_by_execution: dict[str, MetadataStimulusFacts] = {}
    stripped_classes: dict[str, list[str]] = {}
    for execution_id, execution in zip(
        metadata_execution_ids, metadata_execution_rows, strict=True
    ):
        stripped_facts = tuple(item for item in execution[2] if item[0] != "operation.configured")
        stripped_facts_by_execution[execution_id] = stripped_facts
        stripped_identity = hashlib.sha256(canonical(stripped_facts)).hexdigest()
        stripped_classes.setdefault(stripped_identity, []).append(execution_id)
    observed_non_singleton_classes = {
        tuple(members) for members in stripped_classes.values() if len(members) > 1
    }
    expected_configured_classes = complete_configured_classes
    assert observed_non_singleton_classes == {members for _, members in expected_configured_classes}
    observed_equivalence_classes: list[tuple[object, ...]] = []
    observed_receipt_hybrids: list[tuple[object, ...]] = []
    configured_receipt_by_execution = {
        cast(str, receipt[0]): receipt for receipt in metadata_configured_plan_receipts
    }
    return (
        execution_id,
        field,
        donor_receipt,
        execution_index,
        source_id,
        plan_by_execution,
        stripped_facts_by_execution,
        stripped_identity,
        expected_configured_classes,
        observed_equivalence_classes,
        observed_receipt_hybrids,
        configured_receipt_by_execution,
    )


def _assert_equivalence_freeze_mutations_and_history(
    monkeypatch: Any,
    tmp_path: Any,
    root: Any,
    freeze: Any,
    metadata_execution_rows: Any,
    metadata_trigger_rows: Any,
    code: Any,
    ordinal: Any,
    execution_id: Any,
    field: Any,
    donor_receipt: Any,
    execution_index: Any,
    source_id: Any,
    plan_by_execution: Any,
    stripped_facts_by_execution: Any,
    stripped_identity: Any,
    expected_configured_classes: Any,
    observed_equivalence_classes: Any,
    observed_receipt_hybrids: Any,
    configured_receipt_by_execution: Any,
) -> Any:
    for group_name, class_execution_ids in expected_configured_classes:
        class_stripped_identities = {
            hashlib.sha256(canonical(stripped_facts_by_execution[execution_id])).hexdigest()
            for execution_id in class_execution_ids
        }
        assert len(class_stripped_identities) == 1
        class_stripped_identity = next(iter(class_stripped_identities))
        observed_equivalence_classes.append(
            (group_name, class_execution_ids, class_stripped_identity, True)
        )
        valid_bindings: set[tuple[str, str, str]] = set()
        for execution_id in class_execution_ids:
            ordinal = execution_index[execution_id]
            configured_operation = dict(metadata_execution_rows[ordinal][2])["operation.configured"]
            stripped_identity = hashlib.sha256(
                canonical(stripped_facts_by_execution[execution_id])
            ).hexdigest()
            plan = plan_by_execution[execution_id]
            plan_callback = plan[0]
            if plan_callback == "filesystem-state":
                assert configured_operation == "system-reader"
            elif plan_callback == "inter-role":
                assert configured_operation.startswith("race-after:")
                assert (
                    plan[2].removeprefix("after-").removesuffix("-read").replace("-", "_")
                    in configured_operation
                )
            else:
                assert configured_operation.startswith("injected:")
                configured_callbacks = configured_operation.removeprefix("injected:").split(",")
                callback_ordinal = {"lstat": 0, "open": 1, "fstat": 2, "close": 4}[plan_callback]
                assert configured_callbacks[callback_ordinal] != plan_callback
            plan_identity = hashlib.sha256(canonical(plan)).hexdigest()
            valid_bindings.add(
                (
                    stripped_identity,
                    plan_identity,
                    hashlib.sha256(canonical(metadata_trigger_rows[ordinal])).hexdigest(),
                )
            )
        assert len(valid_bindings) == len(class_execution_ids)
        complete_receipt_bindings = {
            (
                hashlib.sha256(canonical(stripped_facts_by_execution[execution_id])).hexdigest(),
                hashlib.sha256(
                    canonical(configured_receipt_by_execution[execution_id])
                ).hexdigest(),
                hashlib.sha256(
                    canonical(metadata_trigger_rows[execution_index[execution_id]])
                ).hexdigest(),
            )
            for execution_id in class_execution_ids
        }
        assert len(complete_receipt_bindings) == len(class_execution_ids)
        for source_id in class_execution_ids:
            complete_source_binding = next(
                binding
                for binding in complete_receipt_bindings
                if binding[1]
                == hashlib.sha256(canonical(configured_receipt_by_execution[source_id])).hexdigest()
            )
            for donor_id in class_execution_ids:
                if donor_id == source_id:
                    continue
                complete_hybrid = (
                    complete_source_binding[0],
                    hashlib.sha256(
                        canonical(configured_receipt_by_execution[donor_id])
                    ).hexdigest(),
                    complete_source_binding[2],
                )
                assert complete_hybrid not in complete_receipt_bindings
        for source_id in class_execution_ids:
            source_ordinal = execution_index[source_id]
            del source_ordinal
            source_stripped_identity = hashlib.sha256(
                canonical(stripped_facts_by_execution[source_id])
            ).hexdigest()
            source_plan_identity = hashlib.sha256(
                canonical(plan_by_execution[source_id])
            ).hexdigest()
            for donor_id in class_execution_ids:
                if donor_id == source_id:
                    continue
                donor_receipt = metadata_trigger_rows[execution_index[donor_id]]
                donor_receipt_identity = hashlib.sha256(canonical(donor_receipt)).hexdigest()
                hybrid = (
                    source_stripped_identity,
                    source_plan_identity,
                    donor_receipt_identity,
                )
                assert hybrid not in valid_bindings
                observed_receipt_hybrids.append(
                    (
                        group_name,
                        source_id,
                        donor_id,
                        source_stripped_identity,
                        source_plan_identity,
                        donor_receipt_identity,
                        hashlib.sha256(canonical(hybrid)).hexdigest(),
                        hybrid in valid_bindings,
                    )
                )
        constant_receipt_identity = hashlib.sha256(
            canonical(metadata_trigger_rows[execution_index[class_execution_ids[0]]])
        ).hexdigest()
        constant_receipt_bindings = {
            (
                hashlib.sha256(canonical(stripped_facts_by_execution[execution_id])).hexdigest(),
                hashlib.sha256(canonical(plan_by_execution[execution_id])).hexdigest(),
                constant_receipt_identity,
            )
            for execution_id in class_execution_ids
        }
        assert len(constant_receipt_bindings & valid_bindings) == 1
        assert constant_receipt_bindings != valid_bindings
    assert tuple(observed_equivalence_classes) == (EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_CLASSES)
    assert len(observed_equivalence_classes) == EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_COUNT
    assert hashlib.sha256(canonical(observed_equivalence_classes)).hexdigest() == (
        EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_SHA256
    )
    assert tuple(observed_receipt_hybrids) == EXPECTED_METADATA_RECEIPT_HYBRIDS
    assert len(observed_receipt_hybrids) == EXPECTED_METADATA_RECEIPT_HYBRID_COUNT
    assert hashlib.sha256(canonical(observed_receipt_hybrids)).hexdigest() == (
        EXPECTED_METADATA_RECEIPT_HYBRID_SHA256
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
    return None


def _freeze_metadata_collection_result(
    original_tmp_path: Any,
    final_components: Any,
    metadata_execution_rows: Any,
    metadata_stimulus_rows: Any,
    metadata_trigger_rows: Any,
    metadata_raw_read_rows: Any,
    metadata_close_order_rows: Any,
    metadata_normalized_payload_rows: Any,
    metadata_configured_plan_receipts: Any,
) -> Any:
    return (
        MetadataCollection(
            tuple(metadata_execution_rows),
            tuple(metadata_stimulus_rows),
            tuple(metadata_trigger_rows),
            tuple(metadata_raw_read_rows),
            tuple(metadata_close_order_rows),
            tuple(metadata_normalized_payload_rows),
            tuple(metadata_configured_plan_receipts),
        ),
        (len(os.fsencode(original_tmp_path)), len(original_tmp_path.parts)),
        (final_components[0], final_components[1]),
    )


def _collect_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability(
    original_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[MetadataCollection, tuple[int, int], tuple[int, int]]:
    (
        tmp_path,
        final_components,
        root,
        freeze,
        metadata_execution_rows,
        metadata_stimulus_rows,
        metadata_trigger_rows,
        metadata_raw_read_rows,
        metadata_close_order_rows,
        metadata_normalized_payload_rows,
        metadata_configured_plan_receipts,
        baseline_metadata_io,
        normalized_observed_path,
        normalized_observed_payload,
        observe_pre_execution_stimulus,
        metadata_case,
        observed_payload_stimulus,
    ) = cast(tuple[Any, ...], _initialize_repository_metadata_collection(original_tmp_path))
    traced_metadata_reader = _build_traced_metadata_reader(
        baseline_metadata_io, normalized_observed_path, normalized_observed_payload
    )
    (finish_metadata_execution, execute_metadata_success_case, execute_metadata_case) = cast(
        tuple[Any, ...],
        _build_metadata_execution_recorders(
            monkeypatch,
            metadata_execution_rows,
            metadata_stimulus_rows,
            metadata_trigger_rows,
            metadata_raw_read_rows,
            metadata_close_order_rows,
            metadata_normalized_payload_rows,
            metadata_configured_plan_receipts,
            observe_pre_execution_stimulus,
            metadata_case,
            observed_payload_stimulus,
            traced_metadata_reader,
        ),
    )
    (
        execute_metadata_io_case,
        execute_between_read_case,
        successful_git_results,
        roles,
        verified_oid_values,
        successful_by_role,
        role,
        _,
        saved_result,
        output_caps,
        builder_contract,
        observed_transform_contract,
        observed_byte_identities,
        observed_hostile_oid_evidence,
    ) = cast(
        tuple[Any, ...],
        _exercise_metadata_io_and_baseline_transcript(
            monkeypatch,
            root,
            freeze,
            normalized_observed_path,
            observe_pre_execution_stimulus,
            metadata_case,
            traced_metadata_reader,
            finish_metadata_execution,
            execute_metadata_success_case,
        ),
    )
    (
        role,
        _,
        code,
        location,
        ordinal,
        case_id,
        payload,
        argv,
        transform,
        unsupported_returncode,
    ) = cast(
        tuple[Any, ...],
        _exercise_textual_position_and_git_failures(
            monkeypatch,
            root,
            freeze,
            successful_git_results,
            roles,
            verified_oid_values,
            successful_by_role,
            role,
            saved_result,
            output_caps,
            builder_contract,
            observed_transform_contract,
            observed_byte_identities,
            observed_hostile_oid_evidence,
        ),
    )
    (role, code, location, ordinal, payload, cap, returncode, value, author_payload, expected) = (
        cast(
            tuple[Any, ...],
            _exercise_git_output_and_ancestry_boundaries(
                monkeypatch,
                root,
                freeze,
                roles,
                role,
                output_caps,
                code,
                location,
                ordinal,
                payload,
                argv,
                transform,
                unsupported_returncode,
            ),
        )
    )
    (
        _,
        code,
        location,
        ordinal,
        expected,
        count,
        relative,
        metadata_root,
        linked_root,
        linked_git_dir,
        replacement_io,
    ) = cast(
        tuple[Any, ...],
        _exercise_git_bundle_corruption_and_linked_baseline(
            monkeypatch,
            tmp_path,
            root,
            freeze,
            execute_metadata_success_case,
            execute_metadata_case,
            execute_metadata_io_case,
            code,
            location,
            ordinal,
            payload,
            returncode,
            author_payload,
            expected,
        ),
    )
    (_, code, name, public_race_root, public_dot_git) = cast(
        tuple[Any, ...],
        _exercise_root_replacement_and_metadata_modes(
            tmp_path,
            execute_metadata_case,
            execute_metadata_io_case,
            execute_between_read_case,
            code,
            location,
            metadata_root,
            replacement_io,
        ),
    )
    (_, case_id, system_io, operational_mode, stat_value, case_base, linked_record_cases) = cast(
        tuple[Any, ...],
        _exercise_metadata_races_and_errors(
            tmp_path, execute_metadata_io_case, _, case_id, public_race_root, public_dot_git
        ),
    )
    (
        role,
        _,
        code,
        io_root,
        io_record,
        io_payload,
        real_io,
        opened_fds,
        closed_fds,
        metadata_operations,
        chunked_io,
        identity,
        expected_ancestor_records,
    ) = cast(
        tuple[Any, ...],
        _exercise_linked_records_precedence_and_raw_io(
            monkeypatch,
            tmp_path,
            execute_metadata_case,
            execute_metadata_io_case,
            role,
            _,
            code,
            count,
            relative,
            linked_root,
            linked_git_dir,
            system_io,
            operational_mode,
            case_base,
            linked_record_cases,
        ),
    )
    (code, expected_stimulus_rows, execution) = cast(
        tuple[Any, ...],
        _exercise_raw_io_and_receipt_baseline(
            tmp_path,
            metadata_stimulus_rows,
            observe_pre_execution_stimulus,
            traced_metadata_reader,
            finish_metadata_execution,
            _,
            code,
            case_id,
            stat_value,
            io_root,
            io_record,
            io_payload,
            real_io,
            opened_fds,
            closed_fds,
            metadata_operations,
            chunked_io,
            identity,
            expected_ancestor_records,
        ),
    )
    (ordinal, receipt, mutant_id, changed_field_set, coordinate, recipient_index, receipt_index) = (
        cast(
            tuple[Any, ...],
            _assert_receipt_integrity_and_composed_mutants(
                monkeypatch,
                metadata_execution_rows,
                metadata_stimulus_rows,
                metadata_trigger_rows,
                metadata_raw_read_rows,
                metadata_close_order_rows,
                metadata_normalized_payload_rows,
                metadata_configured_plan_receipts,
                role,
                ordinal,
                cap,
                value,
                expected,
                name,
                expected_stimulus_rows,
            ),
        )
    )
    (
        execution_id,
        field,
        donor_receipt,
        execution_index,
        source_id,
        plan_by_execution,
        stripped_facts_by_execution,
        stripped_identity,
        expected_configured_classes,
        observed_equivalence_classes,
        observed_receipt_hybrids,
        configured_receipt_by_execution,
    ) = cast(
        tuple[Any, ...],
        _assert_configured_receipt_mutants_and_history(
            monkeypatch,
            metadata_execution_rows,
            metadata_trigger_rows,
            metadata_configured_plan_receipts,
            ordinal,
            name,
            execution,
            receipt,
            mutant_id,
            changed_field_set,
            coordinate,
            recipient_index,
            receipt_index,
        ),
    )
    _assert_equivalence_freeze_mutations_and_history(
        monkeypatch,
        tmp_path,
        root,
        freeze,
        metadata_execution_rows,
        metadata_trigger_rows,
        code,
        ordinal,
        execution_id,
        field,
        donor_receipt,
        execution_index,
        source_id,
        plan_by_execution,
        stripped_facts_by_execution,
        stripped_identity,
        expected_configured_classes,
        observed_equivalence_classes,
        observed_receipt_hybrids,
        configured_receipt_by_execution,
    )
    return cast(
        tuple[MetadataCollection, tuple[int, int], tuple[int, int]],
        _freeze_metadata_collection_result(
            original_tmp_path,
            final_components,
            metadata_execution_rows,
            metadata_stimulus_rows,
            metadata_trigger_rows,
            metadata_raw_read_rows,
            metadata_close_order_rows,
            metadata_normalized_payload_rows,
            metadata_configured_plan_receipts,
        ),
    )


def _assert_repository_fixture_and_git_budget_contracts() -> Any:
    source = Path(__file__).read_text(encoding="utf-8")
    syntax = ast.parse(source)
    repository_tests = tuple(
        node.name
        for node in syntax.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )
    core_syntax = ast.parse(CORE_ORACLE_PATH.read_text(encoding="utf-8"))
    core_tests = tuple(
        node.name
        for node in core_syntax.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )
    assert (
        repository_tests.count(
            "test_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability"
        )
        == 1
    )
    assert repository_tests[0] == (
        "test_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability"
    )
    assert core_tests.count("test_budget_thresholds_are_exact_at_85_and_90_percent") == 1
    assert core_tests[0] == "test_budget_thresholds_are_exact_at_85_and_90_percent"

    fixture_payload = REPOSITORY_EVIDENCE_FIXTURE_PATH.read_bytes()
    loaded_fixture, fixture_findings = validate_repository_evidence_fixture_bytes(fixture_payload)
    assert fixture_findings == ()
    assert loaded_fixture == _REPOSITORY_EVIDENCE_CATALOGS
    matrix_document = json.loads(MATRIX_PATH.read_bytes())
    assert tuple(matrix_document["budgetPolicy"]["repositoryEvidenceFixtureByteBudget"]) == (
        REPOSITORY_EVIDENCE_FIXTURE_PATH.relative_to(ROOT).as_posix(),
        len(fixture_payload),
        EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_BYTE_CAP,
        1_275_000,
        1_350_000,
        "84.85",
        EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_SHA256,
    )

    def fixture_bytes(document: dict[str, object]) -> bytes:
        return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()

    fixture_document = cast(dict[str, object], json.loads(fixture_payload))
    missing = deepcopy(fixture_document)
    cast(dict[str, object], missing["catalogs"]).pop("metadataExecutions")
    extra = deepcopy(fixture_document)
    cast(dict[str, object], extra["catalogs"])["unexpected"] = {}
    count_drift = deepcopy(fixture_document)
    cast(dict[str, object], cast(dict[str, object], count_drift["catalogs"])["metadataExecutions"])[
        "count"
    ] = 128
    reordered = deepcopy(fixture_document)
    reordered_rows = cast(
        list[object],
        cast(
            dict[str, object], cast(dict[str, object], reordered["catalogs"])["metadataExecutions"]
        )["rows"],
    )
    reordered_rows[0], reordered_rows[1] = reordered_rows[1], reordered_rows[0]
    substituted = deepcopy(fixture_document)
    cast(
        list[object],
        cast(
            dict[str, object],
            cast(dict[str, object], substituted["catalogs"])["metadataExecutions"],
        )["rows"],
    )[0] = "substituted"
    fixture_mutants = (
        (fixture_bytes(missing), "ACP.FIXTURE.CATALOGS", "catalogs"),
        (fixture_bytes(extra), "ACP.FIXTURE.CATALOGS", "catalogs"),
        (fixture_bytes(count_drift), "ACP.FIXTURE.COUNT", "metadataExecutions"),
        (fixture_bytes(reordered), "ACP.FIXTURE.IDENTITY", "metadataExecutions"),
        (fixture_bytes(substituted), "ACP.FIXTURE.IDENTITY", "metadataExecutions"),
        (
            fixture_payload.replace(b'"catalogs": {', b'"catalogs": {}, "catalogs": {', 1),
            "ACP.FIXTURE.DUPLICATE",
            "document",
        ),
        (fixture_payload.replace(b"{\n", b"{ \n", 1), "ACP.FIXTURE.CANONICAL", "document"),
        (b"\xff" + fixture_payload, "ACP.FIXTURE.JSON", "document"),
        (
            b"x" * (EXPECTED_REPOSITORY_EVIDENCE_FIXTURE_BYTE_CAP + 1),
            "ACP.FIXTURE.BYTE_CAP",
            "bytes",
        ),
    )
    for mutant_payload, code, location in fixture_mutants:
        assert validate_repository_evidence_fixture_bytes(mutant_payload) == (
            None,
            repository_evidence_fixture_finding(code, location),
        )

    expected_policy = expected_reset47_budget_policy()
    assert validate_reset47_budget_policy(expected_policy) == ()
    catalog_mutants: list[tuple[str, object, str]] = [("non-dict", (), "type")]

    def add_catalog_mutant(mutant_id: str, changed: object, coordinate: str) -> None:
        catalog_mutants.append((mutant_id, changed, coordinate))

    changed = deepcopy(expected_policy)
    changed.pop("levels")
    add_catalog_mutant("policy-missing", changed, "keys")
    changed = {"unexpected": False, **deepcopy(expected_policy)}
    add_catalog_mutant("policy-extra", changed, "keys")
    changed = deepcopy(expected_policy)
    changed["riskThresholdPercent"] = True
    add_catalog_mutant("threshold-bool", changed, "riskThresholdPercent")
    changed = deepcopy(expected_policy)
    changed["stopThresholdPercent"] = 89
    add_catalog_mutant("stop-threshold", changed, "stopThresholdPercent")

    catalog_name = "dynamicCurrentHeadBudgetContract"

    def changed_catalog() -> tuple[dict[str, object], dict[str, object], list[object]]:
        changed_policy = deepcopy(expected_policy)
        catalog = cast(dict[str, object], changed_policy[catalog_name])
        return changed_policy, catalog, cast(list[object], catalog["rows"])

    changed = deepcopy(expected_policy)
    changed[catalog_name] = ()
    add_catalog_mutant("catalog-non-dict", changed, f"{catalog_name}.type")
    changed, catalog, rows = changed_catalog()
    catalog["unexpected"] = False
    add_catalog_mutant("catalog-extra-key", changed, f"{catalog_name}.keys")
    changed, catalog, rows = changed_catalog()
    catalog["fields"] = ["name", "scope", "source", "limit"]
    add_catalog_mutant("fields", changed, f"{catalog_name}.fields")
    changed, catalog, rows = changed_catalog()
    catalog["rows"] = ()
    add_catalog_mutant("rows-non-list", changed, f"{catalog_name}.rows.type")
    changed, catalog, rows = changed_catalog()
    rows.pop()
    add_catalog_mutant("rows-missing", changed, f"{catalog_name}.rows.count")
    changed, catalog, rows = changed_catalog()
    rows.append(deepcopy(rows[-1]))
    add_catalog_mutant("rows-extra", changed, f"{catalog_name}.rows.count")
    changed, catalog, rows = changed_catalog()
    rows[-1] = deepcopy(rows[-2])
    add_catalog_mutant("rows-duplicate", changed, f"{catalog_name}.rows.duplicate")
    changed, catalog, rows = changed_catalog()
    rows[0], rows[1] = rows[1], rows[0]
    add_catalog_mutant("rows-order", changed, f"{catalog_name}.rows.order")
    changed, catalog, rows = changed_catalog()
    cast(list[object], rows[0])[3] = True
    add_catalog_mutant("row-bool", changed, f"{catalog_name}.rows[0].type")
    changed, catalog, rows = changed_catalog()
    cast(list[object], rows[0])[1] = "changed"
    add_catalog_mutant("row-value", changed, f"{catalog_name}.rows.value")
    changed, catalog, rows = changed_catalog()
    catalog["count"] = 13
    add_catalog_mutant("count", changed, f"{catalog_name}.count")
    changed, catalog, rows = changed_catalog()
    catalog["sha256"] = "0" * 64
    add_catalog_mutant("sha", changed, f"{catalog_name}.sha256")
    for key, value in (
        ("schemaVersion", "WRONG"),
        ("gitPrefix", ["git"]),
        ("gitDiffArguments", ["diff", "HEAD"]),
        ("environment", [["LC_ALL", "hostile"]]),
        ("gitOutputPaths", ["docs/unlisted"]),
    ):
        changed, catalog, rows = changed_catalog()
        catalog[key] = value
        add_catalog_mutant(f"identity-{key}", changed, f"{catalog_name}.{key}")

    runner_calls: list[object] = []

    def forbidden_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        runner_calls.append((args, kwargs))
        raise AssertionError("catalog fault reached Git")

    def raising_raw(error: BaseException) -> Callable[[], Reset47RawResult]:
        def callback() -> Reset47RawResult:
            raise error

        return callback

    for mutant_id, mutant_policy, coordinate in catalog_mutants:
        assert validate_reset47_budget_policy(mutant_policy) == reset47_budget_finding(
            coordinate
        ), mutant_id
        assert core_oracle.measure_reset47_current_budget(
            mutant_policy, forbidden_runner, raising_raw(AssertionError())
        )
        assert runner_calls == []

    command = (
        *EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_PREFIX,
        *EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_DIFF_ARGUMENTS,
    )

    def git_stdout(path_uses: tuple[int, ...]) -> bytes:
        by_path = dict(
            zip(
                EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_RAW_CHECKOUT_PATHS,
                path_uses,
                strict=True,
            )
        )
        return b"".join(
            f"{by_path[path]}\t0\t{path}\n".encode()
            for path in EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_GIT_OUTPUT_PATHS
        )

    safe_path_uses = (1, 1, 1, 1, 1, 1, 1)
    valid_process = subprocess.CompletedProcess(command, 0, git_stdout(safe_path_uses), b"")
    observed_calls: list[tuple[object, dict[str, object]]] = []

    def result_runner(
        *args: object, result: object = valid_process, **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        observed_calls.append((args[0], kwargs))
        return cast(subprocess.CompletedProcess[bytes], result)

    clean = core_oracle.measure_reset47_current_budget(
        expected_policy,
        result_runner,
        lambda: (safe_path_uses, ()),
    )
    assert isinstance(clean, core_oracle.Reset47BudgetEvidence)
    assert clean.state is core_oracle.Reset47BudgetState.CLEAN_EQUAL
    assert observed_calls == [
        (
            command,
            {
                "cwd": ROOT,
                "env": dict(EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ENVIRONMENT),
                "check": False,
                "capture_output": True,
                "text": False,
                "timeout": 5,
            },
        )
    ]

    raw_calls: list[str] = []

    def observed_raw(value: object) -> Callable[[], Reset47RawResult]:
        def callback() -> Reset47RawResult:
            raw_calls.append("raw")
            return cast(Reset47RawResult, value)

        return callback

    git_mutants = (
        ("result-type", object(), "dynamicBudget.git.result"),
        (
            "bool-return",
            subprocess.CompletedProcess(command, True, b"", b""),
            "dynamicBudget.git.returncode",
        ),
        (
            "returncode",
            subprocess.CompletedProcess(command, 1, b"", b""),
            "dynamicBudget.git.returncode",
        ),
        (
            "stderr-type",
            subprocess.CompletedProcess(command, 0, b"", ""),
            "dynamicBudget.git.stderr",
        ),
        (
            "stderr",
            subprocess.CompletedProcess(command, 0, b"", b"hostile"),
            "dynamicBudget.git.stderr",
        ),
        (
            "stdout-type",
            subprocess.CompletedProcess(command, 0, "", b""),
            "dynamicBudget.git.stdout",
        ),
        (
            "stdout-lf",
            subprocess.CompletedProcess(command, 0, b"1\t0\tpath", b""),
            "dynamicBudget.git.stdout",
        ),
        (
            "row-count",
            subprocess.CompletedProcess(command, 0, b"1\t0\tpath\n", b""),
            "dynamicBudget.git.rows",
        ),
        (
            "tabs",
            subprocess.CompletedProcess(
                command, 0, valid_process.stdout.replace(b"\t", b" ", 1), b""
            ),
            "dynamicBudget.git.rows[0]",
        ),
        (
            "digits",
            subprocess.CompletedProcess(
                command, 0, valid_process.stdout.replace(b"1\t", b"01\t", 1), b""
            ),
            "dynamicBudget.git.rows[0].count",
        ),
        (
            "binary",
            subprocess.CompletedProcess(
                command, 0, valid_process.stdout.replace(b"1\t", b"-\t", 1), b""
            ),
            "dynamicBudget.git.rows[0].count",
        ),
        (
            "path",
            subprocess.CompletedProcess(
                command, 0, valid_process.stdout.replace(b"docs/ADR", b"docs/XXX", 1), b""
            ),
            "dynamicBudget.git.rows[0]",
        ),
        (
            "deletion",
            subprocess.CompletedProcess(
                command, 0, valid_process.stdout.replace(b"\t0\t", b"\t1\t", 1), b""
            ),
            "dynamicBudget.git.rows[0].deletions",
        ),
    )
    for mutant_id, process, location in git_mutants:
        raw_calls.clear()
        assert core_oracle.measure_reset47_current_budget(
            expected_policy,
            lambda *args, process=process, **kwargs: cast(
                subprocess.CompletedProcess[bytes], process
            ),
            observed_raw((safe_path_uses, ())),
        ) == core_oracle.reset47_budget_failure(location), mutant_id
        assert raw_calls == []
    return (
        matrix_document,
        location,
        expected_policy,
        changed,
        raising_raw,
        mutant_id,
        coordinate,
        command,
        git_stdout,
        safe_path_uses,
        result_runner,
        raw_calls,
        observed_raw,
    )


def _assert_git_budget_and_prose_mutants(
    matrix_document: Any,
    location: Any,
    expected_policy: Any,
    changed: Any,
    raising_raw: Any,
    mutant_id: Any,
    coordinate: Any,
    command: Any,
    git_stdout: Any,
    safe_path_uses: Any,
    result_runner: Any,
    raw_calls: Any,
    observed_raw: Any,
) -> Any:
    over_cap = (1, 1, 4500, 1, 1, 1, 1)
    raw_calls.clear()
    assert core_oracle.measure_reset47_current_budget(
        expected_policy,
        lambda *args, **kwargs: subprocess.CompletedProcess(command, 0, git_stdout(over_cap), b""),
        observed_raw((safe_path_uses, ())),
    ) == core_oracle.reset47_budget_failure("dynamicBudget.gitUses[2].stop")
    assert raw_calls == []

    raw_mutants: tuple[tuple[str, object, str], ...] = (
        ("result", [], "dynamicBudget.raw.result"),
        ("findings", (safe_path_uses, []), "dynamicBudget.raw.findings"),
        ("uses-count", ((1,), ()), "dynamicBudget.raw.uses"),
        ("uses-bool", ((True, 1, 1, 1, 1, 1, 1), ()), "dynamicBudget.raw.uses"),
        ("uses-negative", ((-1, 1, 1, 1, 1, 1, 1), ()), "dynamicBudget.raw.uses"),
    )
    for mutant_id, raw_result, location in raw_mutants:
        assert core_oracle.measure_reset47_current_budget(
            expected_policy,
            result_runner,
            observed_raw(raw_result),
        ) == core_oracle.reset47_budget_failure(location), mutant_id

    for error in (OSError("raw"), subprocess.TimeoutExpired(command, 5)):
        assert core_oracle.measure_reset47_current_budget(
            expected_policy,
            result_runner,
            raising_raw(error),
        ) == core_oracle.reset47_budget_failure("dynamicBudget.raw.invocation")
    with pytest.raises(ValueError, match="unhandled"):
        core_oracle.measure_reset47_current_budget(
            expected_policy,
            result_runner,
            raising_raw(ValueError("unhandled")),
        )

    below = (1, 1, 4249, 1, 1, 1, 1)
    boundary = (1, 1, 4250, 1, 1, 1, 1)
    below_result = core_oracle.measure_reset47_current_budget(
        expected_policy, result_runner, observed_raw((below, ()))
    )
    boundary_result = core_oracle.measure_reset47_current_budget(
        expected_policy, result_runner, observed_raw((boundary, ()))
    )
    assert isinstance(below_result, core_oracle.Reset47BudgetEvidence)
    assert isinstance(boundary_result, core_oracle.Reset47BudgetEvidence)
    assert "coreOracle" not in below_result.raw_risk_set
    assert "coreOracle" in boundary_result.raw_risk_set
    assert reset47_budget_percentages((1,) * 12)[6] == "N/A"
    assert reset47_budget_percentages((1,) * 11 + (0,))[11] == "0.00"

    live = core_oracle.measure_reset47_current_budget(
        expected_policy,
        core_oracle.RESET47_SUBPROCESS_RUN,
        core_oracle.read_reset47_raw_checkout,
    )
    assert isinstance(live, core_oracle.Reset47BudgetEvidence)
    assert live.state is core_oracle.Reset47BudgetState.CLEAN_EQUAL
    line_uses = dict(
        zip(
            (row[1] for row in EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ROWS),
            live.raw_uses,
            strict=True,
        )
    )
    caps = {
        row[1]: row[3]
        for row in EXPECTED_RESET47_DYNAMIC_CURRENT_HEAD_BUDGET_ROWS
        if type(row[3]) is int
    }
    matrix_document = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    budget_policy = cast(dict[str, object], matrix_document["budgetPolicy"])
    assert budget_policy == expected_policy
    assert validate_reset47_budget_policy(budget_policy) == ()
    suffixes = tuple(
        name.removeprefix("EXPECTED_RESET47_")
        for name in globals()
        if name.startswith("EXPECTED_RESET47_")
    )
    for suffix in suffixes:
        assert globals()[f"EXPECTED_RESET47_{suffix}"] == getattr(
            protocol, f"STATIC_RESET47_{suffix}"
        )

    prose_catalog = cast(dict[str, object], budget_policy["reset47RedSnapshotProseUse"])
    prose_rows = tuple(tuple(row) for row in cast(list[list[object]], prose_catalog["rows"]))
    assert (
        tuple(cast(list[str], prose_catalog["fields"]))
        == (EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS)
        == protocol.STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS
    )
    assert prose_rows == EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS
    assert cast(object, prose_rows) == cast(
        object, protocol.STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_ROWS
    )
    assert (
        prose_catalog["count"]
        == (EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT)
        == protocol.STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT
    )
    assert (
        prose_catalog["sha256"]
        == (EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256)
        == protocol.STATIC_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256
    )
    assert hashlib.sha256(canonical(prose_rows)).hexdigest() == (
        EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_SHA256
    )
    assert validate_reset47_prose_catalog(prose_catalog) == ()

    expected_prose_paths = tuple(row[0] for row in prose_rows)
    document_load_calls: list[tuple[str, ...]] = []

    def load_prose_documents(paths: tuple[str, ...]) -> object:
        document_load_calls.append(paths)
        return {path: (ROOT / path).read_bytes() for path in paths}

    assert (
        validate_reset47_prose_contract(prose_catalog, load_prose_documents, line_uses, caps) == ()
    )
    assert document_load_calls == [expected_prose_paths]
    prose_documents = cast(dict[str, object], load_prose_documents(expected_prose_paths))
    document_load_calls.clear()

    def hostile_prose_catalog() -> tuple[dict[str, object], list[object]]:
        changed = deepcopy(prose_catalog)
        return changed, cast(list[object], changed["rows"])

    prose_catalog_mutants: list[tuple[str, object, str]] = [
        ("non-dict", (), "catalog.type"),
    ]
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_mutant["unknown"] = "value"
    prose_catalog_mutants.append(("unknown-key", prose_mutant, "catalog.type"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_rows_mutant.pop()
    prose_catalog_mutants.append(("missing", prose_mutant, "catalog.rows.missing"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_rows_mutant.append(deepcopy(prose_rows_mutant[0]))
    prose_catalog_mutants.append(("extra", prose_mutant, "catalog.rows.cardinality"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_rows_mutant[-1] = deepcopy(prose_rows_mutant[-2])
    prose_catalog_mutants.append(("duplicate", prose_mutant, "catalog.rows.duplicate"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_rows_mutant[0], prose_rows_mutant[1] = prose_rows_mutant[1], prose_rows_mutant[0]
    prose_catalog_mutants.append(("reorder", prose_mutant, "catalog.rows.order"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    cast(list[object], prose_rows_mutant[0])[2] = line_uses["repositoryOracle"] + 1
    prose_catalog_mutants.append(("value", prose_mutant, "catalog.values"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_mutant["fields"] = ["marker", *EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_FIELDS[1:]]
    prose_catalog_mutants.append(("fields", prose_mutant, "catalog.fields"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_mutant["count"] = EXPECTED_RESET47_RED_SNAPSHOT_PROSE_USE_COUNT + 1
    prose_catalog_mutants.append(("count", prose_mutant, "catalog.count"))
    prose_mutant, prose_rows_mutant = hostile_prose_catalog()
    prose_mutant["sha256"] = "0" * 64
    prose_catalog_mutants.append(("sha", prose_mutant, "catalog.sha256"))
    for mutant_id, field_ordinal, mutant_value in (
        ("nested-list", 0, ["path"]),
        ("nested-dict", 1, {"marker": "value"}),
        ("bool", 2, True),
        ("wrong-percent-type", 5, 0),
    ):
        prose_mutant, prose_rows_mutant = hostile_prose_catalog()
        cast(list[object], prose_rows_mutant[0])[field_ordinal] = mutant_value
        prose_catalog_mutants.append((mutant_id, prose_mutant, "catalog.rows.type"))

    for mutant_id, mutant_catalog, coordinate in prose_catalog_mutants:
        forbidden_calls: list[tuple[str, ...]] = []

        def forbidden_document_loader(paths: tuple[str, ...]) -> object:
            forbidden_calls.append(paths)
            return {"docs/unlisted.md": "dual document fault"}

        assert validate_reset47_prose_contract(
            mutant_catalog, forbidden_document_loader, line_uses, caps
        ) == reset47_prose_finding(coordinate), mutant_id
        assert forbidden_calls == [], mutant_id

    def run_document_mutant(documents: object) -> tuple[protocol.Finding, ...]:
        calls: list[tuple[str, ...]] = []

        def hostile_document_loader(paths: tuple[str, ...]) -> object:
            calls.append(paths)
            return documents

        findings = validate_reset47_prose_contract(
            prose_catalog, hostile_document_loader, line_uses, caps
        )
        assert calls == [expected_prose_paths]
        return findings

    missing_documents = dict(prose_documents)
    missing_documents.pop(expected_prose_paths[0])
    extra_documents = {**prose_documents, "docs/unlisted.md": b"extra"}
    substituted_documents = {
        **missing_documents,
        "docs/unlisted.md": prose_documents[expected_prose_paths[0]],
    }
    for mutant_id, documents in (
        ("mapping-missing", missing_documents),
        ("mapping-extra", extra_documents),
        ("mapping-substitution", substituted_documents),
    ):
        assert run_document_mutant(documents) == reset47_prose_finding("documents.path"), mutant_id

    governed_path = expected_prose_paths[0]
    governed_payload = prose_documents[governed_path]
    assert type(governed_payload) is bytes
    governed_marker = prose_rows[0][1]
    start_line = governed_marker.encode("ascii") + b"\n"
    end_line = b"<!-- issue-435-reset47-red-snapshot:end -->\n"
    start = governed_payload.index(start_line)
    content_start = start + len(start_line)
    end = governed_payload.index(end_line, content_start)
    interior = governed_payload[content_start:end]

    def changed_document(old: bytes, new: bytes) -> dict[str, object]:
        assert old in governed_payload and old != new
        changed = dict(prose_documents)
        changed[governed_path] = governed_payload.replace(old, new, 1)
        return changed

    paired_payload = (
        governed_payload[:start]
        + end_line
        + start_line
        + interior
        + governed_payload[end + len(end_line) :]
    )
    duplicate_payload = (
        governed_payload[: end + len(end_line)]
        + start_line
        + interior
        + end_line
        + governed_payload[end + len(end_line) :]
    )
    payload_marker_drift = re.sub(rb"[0-9a-f]{64}", b"e" * 64, start_line)
    raw_document_mutants = (
        ("non-bytes", {**prose_documents, governed_path: "text"}, "documents.blocks.type"),
        ("missing", changed_document(start_line, b""), "documents.blocks.missing"),
        (
            "duplicate",
            {**prose_documents, governed_path: duplicate_payload},
            "documents.blocks.duplicate",
        ),
        ("nested", changed_document(end_line, start_line + end_line), "documents.blocks.nested"),
        ("pairing", {**prose_documents, governed_path: paired_payload}, "documents.blocks.pairing"),
        (
            "start-prefix-junk",
            changed_document(start_line, b"> " + start_line),
            "documents.marker.wholeLine",
        ),
        (
            "start-suffix-junk",
            changed_document(start_line, start_line[:-1] + b" junk\n"),
            "documents.marker.wholeLine",
        ),
        (
            "end-prefix-junk",
            changed_document(end_line, b"> " + end_line),
            "documents.marker.wholeLine",
        ),
        (
            "end-suffix-junk",
            changed_document(end_line, end_line[:-1] + b" junk\n"),
            "documents.marker.wholeLine",
        ),
        (
            "crlf",
            changed_document(interior, interior.replace(b"\n", b"\r\n", 1)),
            "documents.text.crlf",
        ),
        ("nul", changed_document(interior, b"\0" + interior), "documents.text.nul"),
        ("encoding", changed_document(interior, b"\xff" + interior), "documents.text.encoding"),
        (
            "payload-marker",
            changed_document(start_line, payload_marker_drift),
            "documents.marker.substitution",
        ),
    )
    for mutant_id, documents, coordinate in raw_document_mutants:
        assert run_document_mutant(documents) == reset47_prose_finding(coordinate), mutant_id
    return (
        mutant_id,
        coordinate,
        line_uses,
        caps,
        prose_rows,
        expected_prose_paths,
        prose_documents,
        field_ordinal,
        run_document_mutant,
        documents,
        end_line,
        content_start,
        end,
    )


def _assert_prose_portability_and_cross_root_collection(
    monkeypatch: Any,
    mutant_id: Any,
    coordinate: Any,
    line_uses: Any,
    caps: Any,
    prose_rows: Any,
    expected_prose_paths: Any,
    prose_documents: Any,
    run_document_mutant: Any,
    documents: Any,
    end_line: Any,
    content_start: Any,
    end: Any,
) -> Any:
    for path_ordinal, governed_row in enumerate(prose_rows):
        branch_path = governed_row[0]
        payload = prose_documents[branch_path]
        assert type(payload) is bytes
        marker = governed_row[1]
        repository_use = f"{line_uses['repositoryOracle']:,}".encode()
        repository_percent = (
            f"{line_uses['repositoryOracle'] * 100 / caps['repositoryOracle']:.2f}"
        ).encode()
        cap_text = b"" if path_ordinal == 1 else f"/{caps['repositoryOracle']:,}".encode()
        duplicate_token = (
            b"repository " + repository_use + cap_text + b" (" + repository_percent + b"%)"
        )
        contradictory_token = b"repository 1" + cap_text + b" (0.01%)"
        grammar_phrase = (b"Exact file use is", b"Exact use:", b"Exact use is")[path_ordinal]
        review_phrase = (
            b"Readability/convergence PASS",
            b"aggregate readability and convergence reviews PASS",
            b"repository, validator, and aggregate reviews PASS",
        )[path_ordinal]

        def branch_document(old: bytes, new: bytes) -> dict[str, object]:
            branch_start_line = marker.encode("ascii") + b"\n"
            branch_start = payload.index(branch_start_line) + len(branch_start_line)
            branch_end = payload.index(end_line, branch_start)
            branch_interior = payload[branch_start:branch_end]
            if old == end_line:
                assert branch_interior.endswith(b"\n") and new.endswith(end_line)
                changed_interior = branch_interior[:-1] + new.removesuffix(end_line)
            else:
                assert old in branch_interior and old != new
                changed_interior = branch_interior.replace(old, new, 1)
            changed_payload = payload[:branch_start] + changed_interior + payload[branch_end:]
            return {**prose_documents, branch_path: changed_payload}

        payload_marker = re.sub(rb"[0-9a-f]{64}", b"f" * 64, marker.encode())
        branch_mutants = (
            ("type", {**prose_documents, branch_path: "text"}, "documents.blocks.type"),
            (
                "marker",
                {
                    **prose_documents,
                    branch_path: payload.replace(marker.encode(), payload_marker, 1),
                },
                "documents.marker.substitution",
            ),
            ("hash", branch_document(b"helpers", b"helpers "), "documents.blockHash"),
            (
                "use",
                branch_document(repository_use, f"{line_uses['repositoryOracle'] + 1:,}".encode()),
                "documents.repositoryUse",
            ),
            (
                "percent",
                branch_document(
                    repository_percent, f"{float(repository_percent) + 0.01:.2f}".encode()
                ),
                "documents.repositoryPercent",
            ),
            (
                "duplicate",
                branch_document(end_line, duplicate_token + b"\n" + end_line),
                "documents.tokens.duplicate",
            ),
            (
                "contradictory",
                branch_document(end_line, contradictory_token + b"\n" + end_line),
                "documents.tokens.contradictory",
            ),
            (
                "grammar",
                branch_document(grammar_phrase, b"Inexact" + grammar_phrase[5:]),
                "documents.tokens.grammar",
            ),
            (
                "clause",
                branch_document(review_phrase, review_phrase.replace(b"PASS", b"FAIL")),
                "documents.tokens.clauses",
            ),
            (
                "trailing",
                branch_document(end_line, b"trailing junk\n" + end_line),
                "documents.text.trailing",
            ),
        )
        for mutant_id, documents, coordinate in branch_mutants:
            assert run_document_mutant(documents) == reset47_prose_finding(coordinate), (
                f"path-{path_ordinal}-{mutant_id}"
            )

    first_payload = prose_documents[expected_prose_paths[0]]
    assert type(first_payload) is bytes
    validator_token = (
        f"validator {line_uses['validator']:,}/{caps['validator']:,} "
        f"({line_uses['validator'] * 100 / caps['validator']:.2f}%)"
    ).encode()
    aggregate_token = (
        f"the seven-path aggregate is {line_uses['sevenSemanticPaths']:,}/"
        f"{caps['sevenSemanticPaths']:,} "
        f"({line_uses['sevenSemanticPaths'] * 100 / caps['sevenSemanticPaths']:.2f}%)"
    ).encode()
    matrix_token = (
        f"matrix {line_uses['matrix']:,}/{caps['matrix']:,}"
        f"\n({line_uses['matrix'] * 100 / caps['matrix']:.2f}%)"
    ).encode()
    protocol_token = (
        f"protocol {line_uses['protocol']:,}/{caps['protocol']:,} "
        f"({line_uses['protocol'] * 100 / caps['protocol']:.2f}%)"
    ).encode()

    def first_interior_mutant(old: bytes, new: bytes) -> dict[str, object]:
        first_interior = first_payload[content_start:end]
        assert old in first_interior and old != new
        changed_interior = first_interior.replace(old, new, 1)
        changed_payload = first_payload[:content_start] + changed_interior + first_payload[end:]
        return {**prose_documents, expected_prose_paths[0]: changed_payload}

    semantic_document_mutants = (
        (
            "validator-use",
            first_interior_mutant(
                validator_token,
                validator_token.replace(
                    f"{line_uses['validator']:,}".encode(),
                    f"{line_uses['validator'] + 1:,}".encode(),
                ),
            ),
            "documents.validatorUse",
        ),
        (
            "aggregate-use",
            first_interior_mutant(
                aggregate_token,
                aggregate_token.replace(
                    f"{line_uses['sevenSemanticPaths']:,}".encode(),
                    f"{line_uses['sevenSemanticPaths'] + 1:,}".encode(),
                ),
            ),
            "documents.aggregateUse",
        ),
        (
            "validator-percent",
            first_interior_mutant(
                validator_token,
                validator_token.replace(
                    f"{line_uses['validator'] * 100 / caps['validator']:.2f}".encode(),
                    f"{line_uses['validator'] * 100 / caps['validator'] + 0.01:.2f}".encode(),
                ),
            ),
            "documents.validatorPercent",
        ),
        (
            "aggregate-percent",
            first_interior_mutant(
                aggregate_token,
                aggregate_token.replace(
                    f"{line_uses['sevenSemanticPaths'] * 100 / caps['sevenSemanticPaths']:.2f}".encode(),
                    f"{line_uses['sevenSemanticPaths'] * 100 / caps['sevenSemanticPaths'] + 0.01:.2f}".encode(),
                ),
            ),
            "documents.aggregatePercent",
        ),
        (
            "order",
            first_interior_mutant(
                matrix_token + b", " + protocol_token, protocol_token + b", " + matrix_token
            ),
            "documents.tokens.order",
        ),
        (
            "number",
            first_interior_mutant(
                matrix_token,
                matrix_token.replace(
                    f"{line_uses['matrix']:,}".encode(), f"0{line_uses['matrix']:,}".encode()
                ),
            ),
            "documents.tokens.number",
        ),
    )
    for mutant_id, documents, coordinate in semantic_document_mutants:
        assert run_document_mutant(documents) == reset47_prose_finding(coordinate), mutant_id

    assert len(EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_FIELDS) == 4
    assert len(EXPECTED_PORTABLE_CONSTRUCTION_MUTANTS) == (
        EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_COUNT
    )
    assert len({row[0] for row in EXPECTED_PORTABLE_CONSTRUCTION_MUTANTS}) == (
        EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_COUNT
    )
    assert (
        hashlib.sha256(canonical(EXPECTED_PORTABLE_CONSTRUCTION_MUTANTS)).hexdigest()
        == EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_SHA256
    )
    with TemporaryDirectory(prefix="r-") as count_text:
        count_owner = Path(count_text).resolve(strict=True) / ("o" * 30)
        count_owner.mkdir()
        count_plans = plan_portable_fixture_roots(count_owner)
        first_plan_descendants = len(
            (
                *count_plans[0].candidate_components,
                *count_plans[0].filler_components,
                *count_plans[0].final_components,
            )
        )
        all_planned_descendants = sum(
            len((*plan.candidate_components, *plan.filler_components, *plan.final_components))
            for plan in count_plans
        )
        assert validate_portable_fixture_plans(
            count_owner, (object(), count_plans[1])
        ) == portable_construction_finding("plans.type")
        assert tuple(PortableRootPlan.__dataclass_fields__) == (EXPECTED_PORTABLE_ROOT_PLAN_FIELDS)
        assert len(EXPECTED_PORTABLE_ROOT_PLAN_FIELDS) == (EXPECTED_PORTABLE_ROOT_PLAN_FIELD_COUNT)
        assert (
            hashlib.sha256(canonical(EXPECTED_PORTABLE_ROOT_PLAN_FIELDS)).hexdigest()
            == EXPECTED_PORTABLE_ROOT_PLAN_FIELD_SHA256
        )
        for plan_ordinal in range(2):
            for plan_field in EXPECTED_PORTABLE_ROOT_PLAN_FIELDS:
                original_value = getattr(count_plans[plan_ordinal], plan_field)
                changed_value = (
                    original_value + 1
                    if type(original_value) is int
                    else original_value + "-mutant"
                    if type(original_value) is str
                    else (*original_value, "mutant")
                )
                changed_plan = cast(
                    PortableRootPlan,
                    cast(Any, replace)(count_plans[plan_ordinal], **{plan_field: changed_value}),
                )
                changed_plans = list(count_plans)
                changed_plans[plan_ordinal] = changed_plan
                assert validate_portable_fixture_plans(
                    count_owner, tuple(changed_plans)
                ) == portable_construction_finding(f"plans[{plan_ordinal}].{plan_field}")
    for _, operation, expected_location, expected_calls in EXPECTED_PORTABLE_CONSTRUCTION_MUTANTS:
        actual_findings, actual_calls = execute_portable_construction_mutant(operation)
        assert actual_findings == (
            () if expected_location == "valid" else portable_construction_finding(expected_location)
        )
        symbolic_calls = {
            "first-plan-descendants+1": first_plan_descendants + 1,
            "all-planned-descendants": all_planned_descendants,
        }
        required_calls = (
            expected_calls
            if type(expected_calls) is int
            else symbolic_calls[cast(str, expected_calls)]
        )
        assert actual_calls == required_calls
    portable_plans: list[tuple[object, ...]] = []
    for model, owner_bytes, owner_depth in EXPECTED_METADATA_FIXTURE_PORTABLE_OWNER_MODELS:
        first_shape = (owner_bytes + 1 + len(PORTABLE_ROOT_SLOT_NAMES[0]), owner_depth + 1)
        second_shape = (
            first_shape[0] + PORTABLE_ROOT_RELATIVE_DELTA[0],
            first_shape[1] + PORTABLE_ROOT_RELATIVE_DELTA[1],
        )
        portable_plans.append(
            (
                model,
                (owner_bytes, owner_depth),
                first_shape,
                portable_governed_parent_plan(*first_shape),
                second_shape,
                portable_governed_parent_plan(*second_shape),
            )
        )
    with pytest.raises(AssertionError):
        portable_governed_parent_plan(699, GOVERNED_FIXTURE_PARENT_DEPTH - 1)
    root_relation_evidence = (
        EXPECTED_METADATA_FIXTURE_ROOT_RELATIONS,
        EXPECTED_METADATA_FIXTURE_PORTABLE_OWNER_MODELS,
        tuple(portable_plans),
    )
    assert hashlib.sha256(canonical(root_relation_evidence)).hexdigest() == (
        EXPECTED_METADATA_ROOT_REPLAY_RELATION_SHA256
    )
    owner_path: Path
    with TemporaryDirectory(prefix="r32-owner-") as owner_text:
        owner_path = Path(owner_text)
        owner_resolved = owner_path.resolve(strict=True)
        owner_status = owner_resolved.lstat()
        portable_root_plans = plan_portable_fixture_roots(owner_resolved)
        construction, construction_findings = construct_portable_fixture_roots(
            owner_resolved, portable_root_plans
        )
        assert construction_findings == ()
        assert construction is not None
        assert validate_portable_construction_result(owner_resolved, construction) == ()
        first_root, second_root = construction.governed_roots
        assert construction.planning_transcript == (
            ("plan-complete", "A"),
            ("plan-complete", "B"),
            ("relation-validated", "+81-bytes/+6-depth"),
        )
        assert tuple(row[0] for row in construction.filesystem_receipts) == tuple(
            range(len(construction.filesystem_receipts))
        )
        first_shape = (
            construction.plans[0].candidate_bytes,
            construction.plans[0].candidate_depth,
        )
        second_shape = (
            construction.plans[1].candidate_bytes,
            construction.plans[1].candidate_depth,
        )
        assert (
            second_shape[0] - first_shape[0],
            second_shape[1] - first_shape[1],
        ) == PORTABLE_ROOT_RELATIVE_DELTA
        first, first_observed_shape, first_finals = (
            _collect_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability(
                first_root, monkeypatch
            )
        )
        second, second_observed_shape, second_finals = (
            _collect_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability(
                second_root, monkeypatch
            )
        )
        assert owner_path.resolve(strict=True) == owner_resolved
        assert (owner_path.lstat().st_dev, owner_path.lstat().st_ino) == (
            owner_status.st_dev,
            owner_status.st_ino,
        )
    assert not owner_path.exists()
    with pytest.raises(FileNotFoundError):
        owner_path.lstat()
    return (
        coordinate,
        operation,
        expected_location,
        first,
        first_observed_shape,
        first_finals,
        second,
        second_observed_shape,
        second_finals,
    )


def _assert_cross_root_replay_evidence(
    coordinate: Any,
    field_ordinal: Any,
    operation: Any,
    expected_location: Any,
    first: Any,
    first_observed_shape: Any,
    first_finals: Any,
    second: Any,
    second_observed_shape: Any,
    second_finals: Any,
) -> Any:
    assert first == second
    assert first.configured_plan_receipts == second.configured_plan_receipts
    evidence_identities = tuple(
        hashlib.sha256(
            canonical(
                tuple(
                    hashlib.sha256(canonical(getattr(collection, field))).hexdigest()
                    for field in (
                        "full_executions",
                        "stimuli",
                        "trigger_receipts",
                        "raw_reads",
                        "close_orders",
                        "normalized_payloads",
                    )
                )
            )
        ).hexdigest()
        for collection in (first, second)
    )
    assert evidence_identities == (EXPECTED_METADATA_ROOT_REPLAY_EVIDENCE_IDENTITY_SHA256,) * 2
    replay_envelopes = (
        (
            "A",
            (0, 0),
            (GOVERNED_FIXTURE_PARENT_BYTES, GOVERNED_FIXTURE_PARENT_DEPTH),
            first_finals,
            evidence_identities[0],
        ),
        (
            "B",
            PORTABLE_ROOT_RELATIVE_DELTA,
            (GOVERNED_FIXTURE_PARENT_BYTES, GOVERNED_FIXTURE_PARENT_DEPTH),
            second_finals,
            evidence_identities[1],
        ),
    )
    assert first_observed_shape == (
        GOVERNED_FIXTURE_PARENT_BYTES,
        GOVERNED_FIXTURE_PARENT_DEPTH,
    )
    assert second_observed_shape == first_observed_shape
    assert all(8 <= length <= 255 for row in replay_envelopes for length in row[3])
    assert len(replay_envelopes) == EXPECTED_METADATA_ROOT_REPLAY_ENVELOPE_COUNT

    def replay_findings(
        expected: MetadataCollection, observed: MetadataCollection
    ) -> tuple[protocol.Finding, ...]:
        catalogs = (
            ("raw_reads", "rawReads", EXPECTED_METADATA_RAW_READ_FIELDS),
            (
                "normalized_payloads",
                "normalizedPayloads",
                EXPECTED_METADATA_NORMALIZED_PAYLOAD_FIELDS,
            ),
        )
        for attribute, location_name, fields in catalogs:
            expected_rows = getattr(expected, attribute)
            observed_rows = getattr(observed, attribute)
            for expected_row, observed_row in zip(expected_rows, observed_rows, strict=True):
                if expected_row == observed_row:
                    continue
                execution_id, role_ordinal = expected_row[:2]
                for field_ordinal, (expected_value, observed_value) in enumerate(
                    zip(expected_row, observed_row, strict=True)
                ):
                    if expected_value == observed_value:
                        continue
                    field_location = fields[field_ordinal]
                    if isinstance(expected_value, tuple) and isinstance(observed_value, tuple):
                        changed_ordinals = tuple(
                            index
                            for index, values in enumerate(
                                zip(expected_value, observed_value, strict=True)
                            )
                            if values[0] != values[1]
                        )
                        assert len(changed_ordinals) == 1
                        field_location += f"[{changed_ordinals[0]}]"
                    return finding(
                        "evidence",
                        "ACP.EVIDENCE.CROSS_ROOT_REPLAY_MISMATCH",
                        (
                            f"metadataReplay.{location_name}[{execution_id}]"
                            f"[{role_ordinal}].{field_location}"
                        ),
                    )
        return ()

    assert replay_findings(first, second) == ()
    for (
        mutant_name,
        field_name,
        execution_id,
        role_ordinal,
        coordinate,
        operation,
        expected_location,
    ) in EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANTS:
        replay_rows = list(cast(tuple[tuple[object, ...], ...], getattr(second, field_name)))
        matching = tuple(
            ordinal
            for ordinal, replay_row in enumerate(replay_rows)
            if replay_row[0] == execution_id and replay_row[1] == role_ordinal
        )
        assert len(matching) == 1
        row_index = matching[0]
        replay_row = list(replay_rows[row_index])
        if operation == "increment-first-request":
            requests = list(cast(tuple[int, ...], replay_row[3]))
            requests[0] += 1
            replay_row[3] = tuple(requests)
        else:
            assert operation == "replace-first-payload-identity"
            replay_row[3] = "0" * 64
        replay_rows[row_index] = tuple(replay_row)
        changed_collection = replace(second, **cast(Any, {field_name: tuple(replay_rows)}))
        assert replay_findings(first, changed_collection) == finding(
            "evidence",
            "ACP.EVIDENCE.CROSS_ROOT_REPLAY_MISMATCH",
            expected_location,
        ), (mutant_name, coordinate)


def test_real_git_freeze_binds_ancestry_blobs_hashes_author_and_immutability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (
        matrix_document,
        location,
        expected_policy,
        changed,
        raising_raw,
        mutant_id,
        coordinate,
        command,
        git_stdout,
        safe_path_uses,
        result_runner,
        raw_calls,
        observed_raw,
    ) = cast(tuple[Any, ...], _assert_repository_fixture_and_git_budget_contracts())
    (
        mutant_id,
        coordinate,
        line_uses,
        caps,
        prose_rows,
        expected_prose_paths,
        prose_documents,
        field_ordinal,
        run_document_mutant,
        documents,
        end_line,
        content_start,
        end,
    ) = cast(
        tuple[Any, ...],
        _assert_git_budget_and_prose_mutants(
            matrix_document,
            location,
            expected_policy,
            changed,
            raising_raw,
            mutant_id,
            coordinate,
            command,
            git_stdout,
            safe_path_uses,
            result_runner,
            raw_calls,
            observed_raw,
        ),
    )
    (
        coordinate,
        operation,
        expected_location,
        first,
        first_observed_shape,
        first_finals,
        second,
        second_observed_shape,
        second_finals,
    ) = cast(
        tuple[Any, ...],
        _assert_prose_portability_and_cross_root_collection(
            monkeypatch,
            mutant_id,
            coordinate,
            line_uses,
            caps,
            prose_rows,
            expected_prose_paths,
            prose_documents,
            run_document_mutant,
            documents,
            end_line,
            content_start,
            end,
        ),
    )
    _assert_cross_root_replay_evidence(
        coordinate,
        field_ordinal,
        operation,
        expected_location,
        first,
        first_observed_shape,
        first_finals,
        second,
        second_observed_shape,
        second_finals,
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


def _assert_governed_reads_and_documentation_boundary(
    tmp_path: Any,
    monkeypatch: Any,
) -> Any:
    root, freeze = create_real_git_freeze(tmp_path)
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
    matrix_threat_findings = tuple(
        tuple(item) for item in git_contract["filesystemThreatModelFindingContracts"]
    )
    assert (
        matrix_threat_findings
        == EXPECTED_GIT_FILESYSTEM_THREAT_MODEL_FINDINGS
        == protocol.STATIC_GIT_FILESYSTEM_THREAT_MODEL_FINDINGS
    )
    protocol_documentation_contract = json.loads(
        json.dumps(dict(protocol.STATIC_GIT_DOCUMENTATION_CLAIM_CONTRACT))
    )
    assert (
        git_contract["documentationClaimContract"]
        == EXPECTED_GIT_DOCUMENTATION_CLAIM_CONTRACT
        == protocol_documentation_contract
    )
    documentation_contract = git_contract["documentationClaimContract"]
    assert tuple(documentation_contract["normalization"]) == (
        EXPECTED_DOCUMENT_OVERCLAIM_NORMALIZATION
    )
    assert tuple(documentation_contract["variantAxes"]) == (
        EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_AXES
    )
    assert (
        tuple(
            (family, tuple(phrases))
            for family, phrases in documentation_contract["prohibitedFamilyGrammar"]
        )
        == EXPECTED_DOCUMENT_PROHIBITED_FAMILY_GRAMMAR
    )
    assert documentation_contract["variantCount"] == EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_COUNT
    assert documentation_contract["variantSha256"] == EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_SHA256
    threat_mutations: tuple[tuple[str, object], ...] = (
        ("scope", "concurrent_mutation_safe"),
        ("proofs", ["atomic_check_to_use"]),
        ("defenseInDepth", ["race_free_guarantee"]),
        ("gitProcessBinding", "descriptor_bound_git_subprocess"),
        ("excludedThreat", None),
        ("claimsNotMade", []),
        ("strongerClaimDisposition", "PASS"),
    )
    matrix_document = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    threat_finding_contracts = EXPECTED_GIT_FILESYSTEM_THREAT_MODEL_FINDINGS
    for (field, hostile_value), finding_contract in zip(
        threat_mutations, threat_finding_contracts, strict=True
    ):
        assert field == finding_contract[0]
        hostile_threat_model = deepcopy(
            cast(dict[str, object], EXPECTED_GIT_FILESYSTEM_THREAT_MODEL)
        )
        hostile_threat_model[field] = hostile_value
        assert hostile_threat_model != git_contract["filesystemThreatModel"]
        assert canonical(hostile_threat_model) != canonical(git_contract["filesystemThreatModel"])
        hostile_matrix = deepcopy(matrix_document)
        hostile_matrix["staticBoundaryContract"]["gitEvidenceContract"]["filesystemThreatModel"] = (
            hostile_threat_model
        )
        result = protocol.validate_matrix_bytes(canonical(hostile_matrix), canonical(freeze))
        assert result.findings == finding("matrix", finding_contract[1], finding_contract[2])
    required_document_claims = (
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
    )
    documents = tuple(
        (path, (ROOT / path).read_text(encoding="utf-8")) for path, _ in required_document_claims
    )
    assert PROTOCOL_DOCUMENTATION_VALIDATOR is not None
    assert PROTOCOL_DOCUMENTATION_VALIDATOR(documents) == ()
    block_start = "<!-- issue-435-filesystem-snapshot-boundary:start -->"
    block_end = "<!-- issue-435-filesystem-snapshot-boundary:end -->"
    overclaim_variants = document_overclaim_variants()
    assert len(overclaim_variants) == EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_COUNT
    assert hashlib.sha256(canonical(overclaim_variants)).hexdigest() == (
        EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_SHA256
    )
    assert hashlib.sha256(canonical(EXPECTED_DOCUMENT_NORMALIZATION_MUTANTS)).hexdigest() == (
        EXPECTED_DOCUMENT_NORMALIZATION_MUTANT_SHA256
    )
    variants_by_axis = {axis: variant for _, axis, variant, _ in overclaim_variants}
    backtick_variant = variants_by_axis["backtick-only"]
    lowered_without_backtick_removal = "".join(
        chr(ord(character) + 32) if "A" <= character <= "Z" else character
        for character in backtick_variant
    )
    assert re.sub(r"[\s-]+", " ", lowered_without_backtick_removal).strip().startswith("`")
    edge_variant = variants_by_axis["edge-whitespace-only"]
    edge_without_final_strip = re.sub(
        r"[\s-]+",
        " ",
        re.sub(r"[*_`]", "", edge_variant.lower()),
    )
    assert edge_without_final_strip.startswith(" ") and edge_without_final_strip.endswith(" ")
    assert tuple(dict.fromkeys(row[0] for row in overclaim_variants)) == tuple(
        cast(
            list[str],
            EXPECTED_GIT_DOCUMENTATION_CLAIM_CONTRACT["prohibitedClaimFamilies"],
        )
    )
    assert tuple(dict.fromkeys(row[1] for row in overclaim_variants)) == (
        EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_AXES
    )
    return (
        relative,
        code,
        source,
        prefix,
        environment,
        allowed_expressions,
        allowed_git_source,
        read_only_git,
        static_contract,
        git_contract,
        result,
        required_document_claims,
        documents,
        block_start,
        block_end,
        overclaim_variants,
    )


def _assert_metadata_execution_and_replay_catalogs(
    read_only_git: Any,
    git_contract: Any,
    required_document_claims: Any,
    documents: Any,
    block_start: Any,
    block_end: Any,
    overclaim_variants: Any,
) -> Any:
    for path, required_claim in required_document_claims:
        document = dict(documents)[path]
        assert document.count(required_claim) == 1
        assert document.count(block_start) == document.count(block_end) == 1
        assert "`EVIDENCE_BLOCKER`" in document
        approved_block = document[
            document.index(block_start) : document.index(block_end) + len(block_end)
        ]
        expected_block_hashes = dict(
            (item[0], item[1])
            for item in cast(
                list[list[str]],
                EXPECTED_GIT_DOCUMENTATION_CLAIM_CONTRACT["approvedBlockSha256"],
            )
        )
        assert hashlib.sha256(approved_block.encode()).hexdigest() == expected_block_hashes[path]
        without_block = (
            document[: document.index(block_start)]
            + document[document.index(block_end) + len(block_end) :]
        )
        assert PROTOCOL_DOCUMENTATION_VALIDATOR(((path, without_block),)) == finding(
            "documentation", "ACP.DOC.THREAT_MODEL_BLOCK", path
        )
        for family, axis, overclaim, normalized in overclaim_variants:
            assert family in cast(
                list[str],
                EXPECTED_GIT_DOCUMENTATION_CLAIM_CONTRACT["prohibitedClaimFamilies"],
            )
            assert axis in EXPECTED_DOCUMENT_OVERCLAIM_VARIANT_AXES
            assert normalized in dict(EXPECTED_DOCUMENT_PROHIBITED_FAMILY_GRAMMAR)[family]
            injected = document + "\n" + overclaim + ".\n"
            assert PROTOCOL_DOCUMENTATION_VALIDATOR(((path, injected),)) == finding(
                "documentation", "ACP.DOC.THREAT_MODEL_OVERCLAIM", path
            )
    assert "pass_fds" not in read_only_git
    assert "/proc/self/fd" not in read_only_git
    assert tuple(git_contract["gitPrefix"]) == GIT_PREFIX == protocol.STATIC_GIT_PREFIX
    assert (
        tuple(tuple(item) for item in git_contract["deterministicFixtureCommitMetadata"])
        == (tuple(DETERMINISTIC_GIT_METADATA.items()))
        == protocol.STATIC_GIT_DETERMINISTIC_FIXTURE_COMMIT_METADATA
    )
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
        == cast(tuple[str, ...], protocol.STATIC_GIT_METADATA_EXECUTION_CONTRACT_FIELDS)
    )
    assert (
        git_contract["metadata"]["fullExecutionSha256"]
        == EXPECTED_METADATA_FULL_EXECUTION_SHA256
        == protocol.STATIC_GIT_METADATA_FULL_EXECUTION_SHA256
    )
    assert (
        git_contract["metadata"]["stimulusCount"]
        == EXPECTED_METADATA_STIMULUS_COUNT
        == protocol.STATIC_GIT_METADATA_STIMULUS_COUNT
    )
    assert (
        git_contract["metadata"]["stimulusSha256"]
        == EXPECTED_METADATA_STIMULUS_SHA256
        == protocol.STATIC_GIT_METADATA_STIMULUS_SHA256
    )
    assert (
        cast(object, tuple(git_contract["metadata"]["triggerReceiptFields"]))
        == cast(object, EXPECTED_METADATA_TRIGGER_RECEIPT_FIELDS)
        == cast(object, protocol.STATIC_GIT_METADATA_TRIGGER_RECEIPT_FIELDS)
    )
    assert (
        cast(object, tuple(git_contract["metadata"]["interRoleTriggerReceiptFields"]))
        == cast(object, EXPECTED_METADATA_INTER_ROLE_TRIGGER_RECEIPT_FIELDS)
        == cast(object, protocol.STATIC_GIT_METADATA_INTER_ROLE_TRIGGER_RECEIPT_FIELDS)
    )
    assert (
        git_contract["metadata"]["triggerReceiptCount"]
        == EXPECTED_METADATA_TRIGGER_RECEIPT_COUNT
        == protocol.STATIC_GIT_METADATA_TRIGGER_RECEIPT_COUNT
    )
    assert (
        git_contract["metadata"]["triggerReceiptSha256"]
        == EXPECTED_METADATA_TRIGGER_RECEIPT_SHA256
        == protocol.STATIC_GIT_METADATA_TRIGGER_RECEIPT_SHA256
    )
    assert (
        git_contract["metadata"]["fixtureParentAbsoluteLength"]
        == (GOVERNED_FIXTURE_PARENT_BYTES)
        == protocol.STATIC_GIT_METADATA_FIXTURE_PARENT_ABSOLUTE_LENGTH
    )
    assert (
        git_contract["metadata"]["fixtureParentLexicalDepth"]
        == (GOVERNED_FIXTURE_PARENT_DEPTH)
        == protocol.STATIC_GIT_METADATA_FIXTURE_PARENT_LEXICAL_DEPTH
    )
    assert (
        tuple(git_contract["metadata"]["fixtureRootRelationFields"])
        == (EXPECTED_METADATA_FIXTURE_ROOT_RELATION_FIELDS)
        == protocol.STATIC_GIT_METADATA_FIXTURE_ROOT_RELATION_FIELDS
    )
    assert (
        tuple(tuple(row) for row in git_contract["metadata"]["fixtureRootRelations"])
        == (EXPECTED_METADATA_FIXTURE_ROOT_RELATIONS)
        == protocol.STATIC_GIT_METADATA_FIXTURE_ROOT_RELATIONS
    )
    assert (
        tuple(git_contract["metadata"]["fixtureRootChildComponentBytes"])
        == (PORTABLE_ROOT_CHILD_COMPONENT_BYTES)
        == protocol.STATIC_GIT_METADATA_FIXTURE_ROOT_CHILD_COMPONENT_BYTES
    )
    assert (
        tuple(tuple(row) for row in git_contract["metadata"]["fixturePortableOwnerModels"])
        == (EXPECTED_METADATA_FIXTURE_PORTABLE_OWNER_MODELS)
        == protocol.STATIC_GIT_METADATA_FIXTURE_PORTABLE_OWNER_MODELS
    )
    assert (
        git_contract["metadata"]["fixtureRootRelationSha256"]
        == (EXPECTED_METADATA_ROOT_REPLAY_RELATION_SHA256)
        == protocol.STATIC_GIT_METADATA_FIXTURE_ROOT_RELATION_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["fixtureOwnershipContract"])
        == (EXPECTED_METADATA_FIXTURE_OWNERSHIP_CONTRACT)
        == protocol.STATIC_GIT_METADATA_FIXTURE_OWNERSHIP_CONTRACT
    )
    assert (
        tuple(git_contract["metadata"]["metadataCollectionFields"])
        == (EXPECTED_METADATA_COLLECTION_FIELDS)
        == protocol.STATIC_GIT_METADATA_COLLECTION_FIELDS
    )
    assert (
        tuple(git_contract["metadata"]["rawReadCatalogFields"])
        == (EXPECTED_METADATA_RAW_READ_FIELDS)
        == protocol.STATIC_GIT_METADATA_RAW_READ_CATALOG_FIELDS
    )
    assert (
        git_contract["metadata"]["rawReadCatalogCount"]
        == (EXPECTED_METADATA_RAW_READ_COUNT)
        == protocol.STATIC_GIT_METADATA_RAW_READ_CATALOG_COUNT
    )
    assert (
        git_contract["metadata"]["rawReadCatalogSha256"]
        == (EXPECTED_METADATA_RAW_READ_SHA256)
        == protocol.STATIC_GIT_METADATA_RAW_READ_CATALOG_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["closeOrderCatalogFields"])
        == (EXPECTED_METADATA_CLOSE_ORDER_FIELDS)
        == protocol.STATIC_GIT_METADATA_CLOSE_ORDER_CATALOG_FIELDS
    )
    assert (
        git_contract["metadata"]["closeOrderCatalogCount"]
        == (EXPECTED_METADATA_CLOSE_ORDER_COUNT)
        == protocol.STATIC_GIT_METADATA_CLOSE_ORDER_CATALOG_COUNT
    )
    assert (
        git_contract["metadata"]["closeOrderCatalogSha256"]
        == (EXPECTED_METADATA_CLOSE_ORDER_SHA256)
        == protocol.STATIC_GIT_METADATA_CLOSE_ORDER_CATALOG_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["normalizedPayloadCatalogFields"])
        == (EXPECTED_METADATA_NORMALIZED_PAYLOAD_FIELDS)
        == protocol.STATIC_GIT_METADATA_NORMALIZED_PAYLOAD_CATALOG_FIELDS
    )
    assert (
        git_contract["metadata"]["normalizedPayloadCatalogCount"]
        == (EXPECTED_METADATA_NORMALIZED_PAYLOAD_COUNT)
        == protocol.STATIC_GIT_METADATA_NORMALIZED_PAYLOAD_CATALOG_COUNT
    )
    assert (
        git_contract["metadata"]["normalizedPayloadCatalogSha256"]
        == (EXPECTED_METADATA_NORMALIZED_PAYLOAD_SHA256)
        == protocol.STATIC_GIT_METADATA_NORMALIZED_PAYLOAD_CATALOG_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["rootReplayEnvelopeFields"])
        == (EXPECTED_METADATA_ROOT_REPLAY_ENVELOPE_FIELDS)
        == protocol.STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPE_FIELDS
    )
    assert (
        tuple(git_contract["metadata"]["rootReplayEvidenceFields"])
        == (EXPECTED_METADATA_ROOT_REPLAY_EVIDENCE_FIELDS)
        == protocol.STATIC_GIT_METADATA_ROOT_REPLAY_EVIDENCE_FIELDS
    )
    assert (
        git_contract["metadata"]["rootReplayEnvelopeCount"]
        == (EXPECTED_METADATA_ROOT_REPLAY_ENVELOPE_COUNT)
        == protocol.STATIC_GIT_METADATA_ROOT_REPLAY_ENVELOPE_COUNT
    )
    assert (
        tuple(git_contract["metadata"]["rootReplayRuntimeContract"])
        == (EXPECTED_METADATA_ROOT_REPLAY_RUNTIME_CONTRACT)
        == protocol.STATIC_GIT_METADATA_ROOT_REPLAY_RUNTIME_CONTRACT
    )
    assert (
        git_contract["metadata"]["rootReplayEvidenceIdentitySha256"]
        == (EXPECTED_METADATA_ROOT_REPLAY_EVIDENCE_IDENTITY_SHA256)
        == protocol.STATIC_GIT_METADATA_ROOT_REPLAY_EVIDENCE_IDENTITY_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["rootReplayConfiguredPlanReceiptEquality"])
        == (EXPECTED_METADATA_ROOT_REPLAY_CONFIGURED_PLAN_RECEIPT_EQUALITY)
        == protocol.STATIC_GIT_METADATA_ROOT_REPLAY_CONFIGURED_PLAN_RECEIPT_EQUALITY
    )
    assert (
        tuple(git_contract["metadata"]["crossRootDivergenceMutantFields"])
        == (EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANT_FIELDS)
        == protocol.STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANT_FIELDS
    )
    replay_mutants = tuple(
        tuple(row) for row in git_contract["metadata"]["crossRootDivergenceMutants"]
    )
    assert replay_mutants == EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANTS
    assert cast(object, replay_mutants) == cast(
        object, protocol.STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANTS
    )
    assert (
        git_contract["metadata"]["crossRootDivergenceMutantCount"]
        == len(EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANTS)
        == protocol.STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANT_COUNT
    )
    assert (
        git_contract["metadata"]["crossRootDivergenceMutantSha256"]
        == (EXPECTED_METADATA_REPLAY_DIVERGENCE_MUTANT_SHA256)
        == protocol.STATIC_GIT_METADATA_CROSS_ROOT_DIVERGENCE_MUTANT_SHA256
    )
    assert (
        cast(object, tuple(git_contract["metadata"]["triggerReceiptScheduleContract"]))
        == cast(object, EXPECTED_METADATA_TRIGGER_RECEIPT_SCHEDULE_CONTRACT)
        == cast(object, protocol.STATIC_GIT_METADATA_TRIGGER_RECEIPT_SCHEDULE_CONTRACT)
    )
    former_collision_groups = tuple(
        (name, tuple(execution_ids))
        for name, execution_ids in git_contract["metadata"]["formerCollisionGroups"]
    )
    assert former_collision_groups == EXPECTED_METADATA_FORMER_COLLISION_GROUPS
    assert cast(object, former_collision_groups) == cast(
        object, protocol.STATIC_GIT_METADATA_FORMER_COLLISION_GROUPS
    )
    assert (
        git_contract["metadata"]["formerCollisionGroupCount"]
        == EXPECTED_METADATA_FORMER_COLLISION_GROUP_COUNT
        == protocol.STATIC_GIT_METADATA_FORMER_COLLISION_GROUP_COUNT
    )
    assert (
        hashlib.sha256(canonical(former_collision_groups)).hexdigest()
        == git_contract["metadata"]["formerCollisionGroupSha256"]
        == EXPECTED_METADATA_FORMER_COLLISION_GROUP_SHA256
        == protocol.STATIC_GIT_METADATA_FORMER_COLLISION_GROUP_SHA256
    )
    assert (
        git_contract["metadata"]["configuredRemovedCollisionCount"]
        == EXPECTED_METADATA_REMOVED_CONFIG_COLLISION_COUNT
        == protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_COLLISION_COUNT
    )
    historical_pairs = tuple(
        (name, tuple(pair))
        for name, pair in git_contract["metadata"]["configuredRemovedHistoricalPairGroups"]
    )
    assert historical_pairs == EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIRS
    assert cast(object, historical_pairs) == cast(
        object, protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUPS
    )
    assert (
        git_contract["metadata"]["configuredRemovedHistoricalPairGroupCount"]
        == (EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_COUNT)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_COUNT
    )
    return path


def _assert_configured_plan_and_precedence_catalogs(
    source: Any,
    git_contract: Any,
) -> Any:
    assert (
        git_contract["metadata"]["configuredRemovedHistoricalPairGroupSha256"]
        == (EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_SHA256)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_SHA256
    )
    assert (
        git_contract["metadata"]["configuredRemovedHistoricalPairGroupSource"]
        == (EXPECTED_METADATA_CONFIGURED_REMOVED_HISTORICAL_SOURCE_IDENTITY)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_HISTORICAL_PAIR_GROUP_SOURCE
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanIdentityContract"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_IDENTITY_CONTRACT)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_IDENTITY_CONTRACT
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanFields"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_FIELDS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_FIELDS
    )
    configured_plan_sha = hashlib.sha256(canonical(EXPECTED_METADATA_CONFIGURED_PLANS)).hexdigest()
    assert (
        len(EXPECTED_METADATA_CONFIGURED_PLANS)
        == (git_contract["metadata"]["configuredPlanCount"])
        == EXPECTED_METADATA_CONFIGURED_PLAN_COUNT
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_COUNT
    )
    assert (
        configured_plan_sha
        == git_contract["metadata"]["configuredPlanSha256"]
        == (EXPECTED_METADATA_CONFIGURED_PLAN_SHA256)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanReceiptFields"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_FIELDS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_FIELDS
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanRawEvidenceFields"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RAW_EVIDENCE_FIELDS
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanReceiptProjectionFields"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_PROJECTION_FIELDS
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanReceiptIdentityContract"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_IDENTITY_CONTRACT)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_IDENTITY_CONTRACT
    )
    assert (
        git_contract["metadata"]["configuredPlanReceiptCount"]
        == (EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_COUNT)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_COUNT
    )
    assert (
        git_contract["metadata"]["configuredPlanReceiptSha256"]
        == (EXPECTED_METADATA_CONFIGURED_PLAN_RECEIPT_SHA256)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_SHA256
    )
    configured_receipt_mutants = tuple(
        tuple(row) for row in git_contract["metadata"]["configuredPlanReceiptMutants"]
    )
    assert (
        tuple(git_contract["metadata"]["configuredPlanReceiptMutantFields"])
        == (EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_FIELDS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_FIELDS
    )
    assert configured_receipt_mutants == EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS
    assert cast(object, configured_receipt_mutants) == cast(
        object, protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANTS
    )
    assert (
        git_contract["metadata"]["configuredPlanReceiptMutantCount"]
        == len(EXPECTED_METADATA_CONFIGURED_PLAN_MUTANTS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_COUNT
    )
    assert (
        git_contract["metadata"]["configuredPlanReceiptMutantSha256"]
        == (EXPECTED_METADATA_CONFIGURED_PLAN_MUTANT_SHA256)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_PLAN_RECEIPT_MUTANT_SHA256
    )

    def assert_metadata_catalog_cross_copy(
        stem: str,
        rows_key: str,
        fields: tuple[str, ...],
        rows: tuple[object, ...],
        count: int,
        identity: str,
        protocol_fields: tuple[str, ...],
        protocol_rows: tuple[object, ...],
        protocol_count: int,
        protocol_identity: str,
    ) -> None:
        metadata_contract = git_contract["metadata"]
        assert tuple(metadata_contract[f"{stem}Fields"]) == fields == protocol_fields
        assert canonical(metadata_contract[rows_key]) == canonical(rows) == canonical(protocol_rows)
        assert metadata_contract[f"{stem}Count"] == count == protocol_count
        assert metadata_contract[f"{stem}Sha256"] == identity == protocol_identity

    assert_metadata_catalog_cross_copy(
        "configuredReceiptBinding",
        "configuredReceiptBindings",
        EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_FIELDS,
        EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDINGS,
        EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_COUNT,
        EXPECTED_METADATA_CONFIGURED_RECEIPT_BINDING_SHA256,
        protocol.STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDING_FIELDS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDINGS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDING_COUNT,
        protocol.STATIC_GIT_METADATA_CONFIGURED_RECEIPT_BINDING_SHA256,
    )
    assert_metadata_catalog_cross_copy(
        "configuredSamePlanSwap",
        "configuredSamePlanSwaps",
        EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_FIELDS,
        EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAPS,
        EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_COUNT,
        EXPECTED_METADATA_CONFIGURED_SAME_PLAN_SWAP_SHA256,
        protocol.STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAP_FIELDS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAPS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAP_COUNT,
        protocol.STATIC_GIT_METADATA_CONFIGURED_SAME_PLAN_SWAP_SHA256,
    )
    assert_metadata_catalog_cross_copy(
        "configuredInterOrdinalMutant",
        "configuredInterOrdinalMutants",
        EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_FIELDS,
        EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS,
        EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_COUNT,
        EXPECTED_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_SHA256,
        protocol.STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_FIELDS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANTS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_COUNT,
        protocol.STATIC_GIT_METADATA_CONFIGURED_INTER_ORDINAL_MUTANT_SHA256,
    )
    assert_metadata_catalog_cross_copy(
        "configuredComposedPrecedence",
        "configuredComposedPrecedence",
        EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_FIELDS,
        EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE,
        EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_COUNT,
        EXPECTED_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_SHA256,
        protocol.STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_FIELDS,
        protocol.STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE,
        protocol.STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_COUNT,
        protocol.STATIC_GIT_METADATA_CONFIGURED_COMPOSED_PRECEDENCE_SHA256,
    )
    assert_metadata_catalog_cross_copy(
        "discoveryHandoffMutant",
        "discoveryHandoffMutants",
        EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_FIELDS,
        EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANTS,
        EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_COUNT,
        EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_SHA256,
        protocol.STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANT_FIELDS,
        protocol.STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANTS,
        protocol.STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANT_COUNT,
        protocol.STATIC_GIT_METADATA_DISCOVERY_HANDOFF_MUTANT_SHA256,
    )
    assert_metadata_catalog_cross_copy(
        "portableConstructionMutant",
        "portableConstructionMutants",
        EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_FIELDS,
        EXPECTED_PORTABLE_CONSTRUCTION_MUTANTS,
        EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_COUNT,
        EXPECTED_PORTABLE_CONSTRUCTION_MUTANT_SHA256,
        protocol.STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANT_FIELDS,
        protocol.STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANTS,
        protocol.STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANT_COUNT,
        protocol.STATIC_GIT_METADATA_PORTABLE_CONSTRUCTION_MUTANT_SHA256,
    )
    assert (
        tuple(git_contract["metadata"]["portableRootPlanFields"])
        == (EXPECTED_PORTABLE_ROOT_PLAN_FIELDS)
        == protocol.STATIC_GIT_METADATA_PORTABLE_ROOT_PLAN_FIELDS
    )
    assert (
        git_contract["metadata"]["portableRootPlanFieldCount"]
        == (EXPECTED_PORTABLE_ROOT_PLAN_FIELD_COUNT)
        == protocol.STATIC_GIT_METADATA_PORTABLE_ROOT_PLAN_FIELD_COUNT
    )
    assert (
        git_contract["metadata"]["portableRootPlanFieldSha256"]
        == (EXPECTED_PORTABLE_ROOT_PLAN_FIELD_SHA256)
        == protocol.STATIC_GIT_METADATA_PORTABLE_ROOT_PLAN_FIELD_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["configuredRemovedEquivalenceClassFields"])
        == (EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_FIELDS)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_EQUIVALENCE_CLASS_FIELDS
    )
    configured_equivalence_sha = hashlib.sha256(
        canonical(EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_CLASSES)
    ).hexdigest()
    assert (
        cast(object, git_contract["metadata"]["configuredRemovedEquivalenceClassCount"])
        == cast(object, EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_COUNT)
        == cast(object, protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_EQUIVALENCE_CLASS_COUNT)
    )
    assert (
        configured_equivalence_sha
        == git_contract["metadata"]["configuredRemovedEquivalenceClassSha256"]
        == (EXPECTED_METADATA_CONFIGURED_EQUIVALENCE_SHA256)
        == protocol.STATIC_GIT_METADATA_CONFIGURED_REMOVED_EQUIVALENCE_CLASS_SHA256
    )
    assert (
        tuple(git_contract["metadata"]["receiptHybridContractFields"])
        == (EXPECTED_METADATA_RECEIPT_HYBRID_FIELDS)
        == protocol.STATIC_GIT_METADATA_RECEIPT_HYBRID_CONTRACT_FIELDS
    )
    receipt_hybrid_sha = hashlib.sha256(canonical(EXPECTED_METADATA_RECEIPT_HYBRIDS)).hexdigest()
    assert (
        cast(object, git_contract["metadata"]["receiptHybridCount"])
        == cast(object, EXPECTED_METADATA_RECEIPT_HYBRID_COUNT)
        == cast(object, protocol.STATIC_GIT_METADATA_RECEIPT_HYBRID_COUNT)
    )
    assert (
        receipt_hybrid_sha
        == git_contract["metadata"]["receiptHybridSha256"]
        == (EXPECTED_METADATA_RECEIPT_HYBRID_SHA256)
        == protocol.STATIC_GIT_METADATA_RECEIPT_HYBRID_SHA256
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
    assert governed_precedence_cases == EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES
    assert cast(object, EXPECTED_METADATA_GOVERNED_PRECEDENCE_CASES) == cast(
        object, protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_CASES
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
    assert (
        tuple(git_contract["metadataGovernedPrecedenceMutantFields"])
        == (EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANT_FIELDS)
        == protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANT_FIELDS
    )
    governed_precedence_mutants = tuple(
        tuple(item) for item in git_contract["metadataGovernedPrecedenceMutants"]
    )
    assert governed_precedence_mutants == EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANTS
    assert cast(object, governed_precedence_mutants) == cast(
        object, protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANTS
    )
    assert (
        git_contract["metadataGovernedPrecedenceMutantCount"]
        == (len(EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANTS))
        == protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANT_COUNT
    )
    assert (
        git_contract["metadataGovernedPrecedenceMutantSha256"]
        == (EXPECTED_METADATA_GOVERNED_PRECEDENCE_MUTANT_SHA256)
        == protocol.STATIC_GIT_METADATA_GOVERNED_PRECEDENCE_MUTANT_SHA256
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
    return protocol_module


def _assert_protocol_ast_handoff_and_oid_contracts(
    code: Any,
    source: Any,
    static_contract: Any,
    git_contract: Any,
    result: Any,
    path: Any,
    protocol_module: Any,
) -> Any:
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
    handoff_reader_namespace = dict(vars(protocol))
    exec(METADATA_READER_SOURCE, handoff_reader_namespace)
    handoff_reader = cast(
        Callable[..., protocol.GitMetadataReadResult],
        handoff_reader_namespace["_read_git_metadata_nofollow"],
    )
    assert len(EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANTS) == (
        EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_COUNT
    )
    assert len(EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_FIELDS) == 5
    assert len({row[0] for row in EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANTS}) == (
        EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_COUNT
    )
    assert (
        hashlib.sha256(canonical(EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANTS)).hexdigest()
        == EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANT_SHA256
    )
    with TemporaryDirectory(prefix="issue435-handoff-") as handoff_text:
        handoff_root = Path(handoff_text).resolve(strict=True) / "repository"
        (handoff_root / ".git").mkdir(parents=True)
        for _, operation, code, location, boundary in EXPECTED_METADATA_DISCOVERY_HANDOFF_MUTANTS[
            :-1
        ]:
            findings, callbacks = execute_discovery_handoff_mutant(
                handoff_reader, handoff_root, operation
            )
            assert findings == finding("git-metadata", code, location)
            if boundary == "zero-reader-callbacks":
                assert callbacks == ()
            else:
                assert callbacks
                assert all(operation != "read" for operation, _ in callbacks)
                assert all(path != ".git" for _, path in callbacks)
                opened_paths = tuple(path for operation, path in callbacks if operation == "open")
                expected_components = tuple(handoff_root.parts[1:])
                assert (
                    tuple(path for operation, path in callbacks if operation == "lstat")
                    == expected_components
                )
                assert opened_paths == ("/", *expected_components)
                assert (
                    tuple(path for operation, path in callbacks if operation == "fstat")
                    == expected_components
                )
                assert (
                    tuple(path for operation, path in callbacks if operation == "close")
                    == opened_paths[::-1]
                )
        handoff_status = handoff_root.lstat()
        handoff_record = protocol.GitMetadataRecord(
            handoff_root,
            None,
            handoff_status.st_mode,
            handoff_status.st_dev,
            handoff_status.st_ino,
        )

        def run_handoff_source(
            discovery_source: str,
        ) -> tuple[tuple[str, ...], tuple[protocol.Finding, ...]]:
            observed_roles: list[str] = []

            def handoff_spy(
                called_root: str | Path,
                *,
                provenance: protocol.GitMetadataProvenance,
                io: protocol.MetadataIO,
            ) -> protocol.GitMetadataReadResult:
                del called_root, io
                observed_roles.append(provenance.role)
                if provenance.role == "discovery":
                    return protocol.GitMetadataReadResult(handoff_record, ())
                assert provenance.parent_records[0][1] is handoff_record
                return protocol.GitMetadataReadResult(
                    None,
                    finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
                )

            handoff_namespace = dict(vars(protocol))
            handoff_namespace["_read_git_metadata_nofollow"] = handoff_spy
            exec(discovery_source, handoff_namespace)
            discover = cast(
                Callable[[Path], protocol.GitDiscoveryResult],
                handoff_namespace["discover_git_repository"],
            )
            result = discover(handoff_root)
            return tuple(observed_roles), result.findings

        assert run_handoff_source(METADATA_DISCOVERY_SOURCE) == (
            ("discovery", "dot_git"),
            finding("git-metadata", "ACP.GIT_METADATA.IO_ERROR", ".git"),
        )
        copied_record_expression = (
            '(("discovery", GitMetadataRecord(discovery.record.path, '
            "discovery.record.payload, discovery.record.mode, "
            "discovery.record.device, discovery.record.inode, "
            "discovery.record.ancestor_records)),)"
        )
        copied_source = METADATA_DISCOVERY_SOURCE.replace(
            '(("discovery", discovery.record),)',
            copied_record_expression,
        )
        assert copied_source != METADATA_DISCOVERY_SOURCE
        assert run_handoff_source(copied_source) == (
            ("discovery",),
            finding("git-metadata", "ACP.GIT_METADATA.CONTAINMENT", "root"),
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
    assert tuple(git_contract["textualTransformationInputContractFields"]) == (
        TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_FIELDS
    )
    assert cast(object, TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_FIELDS) == cast(
        object, protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_FIELDS
    )
    assert (
        tuple(tuple(item) for item in git_contract["textualTransformationBuilders"])
        == TEXTUAL_TRANSFORMATION_BUILDERS
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_BUILDERS
    )
    assert (
        git_contract["textualTransformationInputContractSha256"]
        == TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_SHA256
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_INPUT_CONTRACT_SHA256
    )
    assert (
        tuple(git_contract["textualTransformationByteIdentityFields"])
        == (TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_FIELDS)
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_FIELDS
    )
    normalized_byte_identities = tuple(
        (
            item[0],
            item[1],
            item[2],
            (tuple(item[3][0]), tuple(item[3][1])),
            *item[4:],
        )
        for item in git_contract["textualTransformationByteIdentities"]
    )
    assert normalized_byte_identities == EXPECTED_NORMALIZED_GIT_BYTE_IDENTITIES
    assert cast(object, normalized_byte_identities) == cast(
        object, getattr(protocol, "STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITIES", None)
    )
    assert (
        git_contract["textualTransformationByteIdentityCount"]
        == (EXPECTED_NORMALIZED_GIT_BYTE_IDENTITY_COUNT)
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_COUNT
    )
    assert (
        git_contract["textualTransformationByteIdentitySha256"]
        == (EXPECTED_NORMALIZED_GIT_BYTE_IDENTITY_SHA256)
        == protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_IDENTITY_SHA256
    )
    byte_normalization = git_contract["textualTransformationByteNormalization"]
    oid_mappings = tuple(tuple(row) for row in byte_normalization["oidRoleMappings"])
    assert tuple(byte_normalization["oidRoleMappingFields"]) == (
        EXPECTED_VERIFIED_GIT_OID_MAPPING_FIELDS
    )
    assert oid_mappings == EXPECTED_VERIFIED_GIT_OID_MAPPINGS
    assert byte_normalization["oidRoleMappingCount"] == EXPECTED_VERIFIED_GIT_OID_MAPPING_COUNT
    assert byte_normalization["oidRoleMappingSha256"] == (EXPECTED_VERIFIED_GIT_OID_MAPPING_SHA256)
    hostile_oid_evidence = tuple(
        (row[0], row[1], tuple(row[2]), tuple(row[3]), row[4])
        for row in byte_normalization["hostileOidEvidence"]
    )
    assert tuple(byte_normalization["hostileOidEvidenceFields"]) == (
        EXPECTED_HOSTILE_GIT_OID_EVIDENCE_FIELDS
    )
    assert hostile_oid_evidence == EXPECTED_HOSTILE_GIT_OID_EVIDENCE
    assert byte_normalization["hostileOidEvidenceCount"] == (
        EXPECTED_HOSTILE_GIT_OID_EVIDENCE_COUNT
    )
    assert byte_normalization["hostileOidEvidenceSha256"] == (
        EXPECTED_HOSTILE_GIT_OID_EVIDENCE_SHA256
    )
    static_byte_normalization = dict(protocol.STATIC_GIT_TEXTUAL_TRANSFORMATION_BYTE_NORMALIZATION)
    assert oid_mappings == static_byte_normalization["oidRoleMappings"]
    assert hostile_oid_evidence == static_byte_normalization["hostileOidEvidence"]
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
    return (code, operation)


def _assert_governed_reader_ast_and_allowed_members(
    monkeypatch: Any,
    relative: Any,
    allowed_expressions: Any,
    allowed_git_source: Any,
    read_only_git: Any,
) -> Any:
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
    return (policy_patch, allowed_source)


def _assert_hostile_and_allowed_git_static_forms(
    monkeypatch: Any,
    code: Any,
    source: Any,
    prefix: Any,
    environment: Any,
    allowed_expressions: Any,
    allowed_git_source: Any,
    operation: Any,
    policy_patch: Any,
    allowed_source: Any,
) -> Any:
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
    return (code, changed_expression)


def _assert_targeted_and_unknown_static_sources(
    code: Any,
    allowed_expressions: Any,
    allowed_git_source: Any,
    changed_expression: Any,
) -> Any:
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


def test_repository_validator_is_read_only_and_static_boundary_is_ast_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (
        relative,
        code,
        source,
        prefix,
        environment,
        allowed_expressions,
        allowed_git_source,
        read_only_git,
        static_contract,
        git_contract,
        result,
        required_document_claims,
        documents,
        block_start,
        block_end,
        overclaim_variants,
    ) = cast(
        tuple[Any, ...], _assert_governed_reads_and_documentation_boundary(tmp_path, monkeypatch)
    )
    path = _assert_metadata_execution_and_replay_catalogs(
        read_only_git,
        git_contract,
        required_document_claims,
        documents,
        block_start,
        block_end,
        overclaim_variants,
    )
    protocol_module = _assert_configured_plan_and_precedence_catalogs(source, git_contract)
    (code, operation) = cast(
        tuple[Any, ...],
        _assert_protocol_ast_handoff_and_oid_contracts(
            code, source, static_contract, git_contract, result, path, protocol_module
        ),
    )
    (policy_patch, allowed_source) = cast(
        tuple[Any, ...],
        _assert_governed_reader_ast_and_allowed_members(
            monkeypatch, relative, allowed_expressions, allowed_git_source, read_only_git
        ),
    )
    (code, changed_expression) = cast(
        tuple[Any, ...],
        _assert_hostile_and_allowed_git_static_forms(
            monkeypatch,
            code,
            source,
            prefix,
            environment,
            allowed_expressions,
            allowed_git_source,
            operation,
            policy_patch,
            allowed_source,
        ),
    )
    _assert_targeted_and_unknown_static_sources(
        code, allowed_expressions, allowed_git_source, changed_expression
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
