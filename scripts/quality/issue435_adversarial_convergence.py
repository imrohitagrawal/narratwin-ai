#!/usr/bin/env python3
"""Issue #435 adversarial convergence contract.

C2 RED skeleton. Public functions return exact typed NOT_IMPLEMENTED results so
the fixed tests fail on absent behavior rather than imports or exceptions.
"""

from __future__ import annotations

import enum
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
    "git-metadata:no-follow-lstat-open-fstat-bounded-read",
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
STATIC_GIT_METADATA_TARGETS = (
    "info/grafts",
    "shallow",
    "objects/info/alternates",
    "objects/info/http-alternates",
)
STATIC_GIT_METADATA_ROLES = (
    ("root", "root"),
    ("dot_git", ".git"),
    ("linked_git_dir", ".git.gitdir"),
    ("backlink", "git-dir/gitdir"),
    ("commondir", "git-dir/commondir"),
    ("common_dir", "common-dir"),
    ("grafts", "info/grafts"),
    ("shallow", "shallow"),
    ("alternates", "objects/info/alternates"),
    ("http_alternates", "objects/info/http-alternates"),
)
STATIC_GIT_METADATA_RECORD_CAPS = (
    ("dot_git", 4096),
    ("backlink", 4096),
    ("commondir", 4096),
)
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
    ("nonabsolute_path", "ACP.GIT_METADATA.NONABSOLUTE"),
    ("containment", "ACP.GIT_METADATA.CONTAINMENT"),
    ("layout", "ACP.GIT_METADATA.LAYOUT"),
    ("backlink_mismatch", "ACP.GIT_METADATA.BACKLINK_MISMATCH"),
    ("commondir_mismatch", "ACP.GIT_METADATA.COMMONDIR_MISMATCH"),
    ("inode_or_identity_changed", "ACP.GIT_METADATA.IDENTITY_CHANGED"),
    ("prohibited_target_present", "ACP.GIT_METADATA.PROHIBITED"),
)
STATIC_GIT_METADATA_READER_STEPS = (
    "validate-absolute-root-and-exact-path-provenance",
    "open-root-and-hold-parent-directory-descriptors",
    "lstat-each-component-relative-to-held-parent",
    "open-each-directory-with-O_DIRECTORY-and-O_NOFOLLOW-relative-to-parent",
    "fstat-and-bind-every-directory-device-inode-type",
    "open-final-record-with-O_NOFOLLOW-relative-to-held-parent",
    "fstat-and-bind-final-device-inode-type",
    "bounded-read-through-cap-plus-one",
    "post-read-relative-lstat-device-inode-type-identity",
    "close-every-descriptor-once-in-reverse-order-in-finally",
    "return-typed-record-or-first-exact-finding",
)
STATIC_GIT_METADATA_DISCOVERY_STEPS = (
    "bind-lexically-normalized-absolute-root",
    "read-root-dot-git-before-any-process",
    "accept-only-conventional-directory-or-strict-absolute-linked-record",
    "derive-linked-git-dir-from-dot-git-record-not-git-output",
    "require-linked-git-dir-under-common-dir-worktrees-single-name",
    "read-and-bind-exact-backlink-and-commondir",
    "derive-common-dir-independently",
    "reject-four-prohibited-common-dir-inodes-no-follow",
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
STATIC_GIT_OBJECT_BINDINGS = (
    ("red_tree", "redTree"),
    ("matrix_blob", "matrixBlobOid"),
    ("core_oracle_blob", "focusedOracleBlobs[0].blobOid"),
    ("repository_oracle_blob", "focusedOracleBlobs[1].blobOid"),
)
STATIC_GIT_FAILURE_PRECEDENCE = (
    "governed_schema",
    "metadata",
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
STATIC_GIT_RETURN_CODES = (
    ("object_format", (0,), ()),
    ("object_integrity", (0,), ()),
    ("head", (0,), ()),
    ("red_type", (0,), (1,)),
    ("red_size", (0,), ()),
    ("red_ancestor", (0,), (1,)),
    ("merge_scan", (0,), ()),
    ("ancestry_chain", (0,), ()),
    ("c3_other_scope", (0,), (1,)),
    ("c3_freeze_change", (1,), (0,)),
    ("red_objects", (0,), ()),
    ("c3_freeze_size", (0,), ()),
    ("c3_freeze_payload", (0,), ()),
    ("red_author", (0,), ()),
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


def validate_repository_freeze(root: Path = ROOT) -> tuple[Finding, ...]:
    del root
    return (_not_implemented("repository-freeze"),)


def discover_git_repository(root: Path) -> GitDiscoveryResult:
    del root
    return GitDiscoveryResult(None, (_not_implemented("git-metadata"),))


def _read_git_metadata_nofollow(
    root: Path,
    path: Path,
    *,
    max_bytes: int,
    expected_kind: str,
    location: str,
    io: MetadataIO,
) -> GitMetadataReadResult:
    del root, path, max_bytes, expected_kind, io
    return GitMetadataReadResult(None, (_not_implemented(location),))


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
