#!/usr/bin/env python3
"""Issue #435 adversarial convergence contract.

C2 RED skeleton. Public functions return exact typed NOT_IMPLEMENTED results so
the fixed tests fail on absent behavior rather than imports or exceptions.
"""

from __future__ import annotations

import enum
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
) -> MatrixObservation | None:
    del fixture_bytes, crypto_verifier
    return None


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
