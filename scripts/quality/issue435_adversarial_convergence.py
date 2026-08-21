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
    result: bool


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
    max_json_members: int = 7


@dataclass(frozen=True)
class Evaluation:
    findings: tuple[Finding, ...]
    historical_verdict: Verdict
    current_verdict: Verdict
    eligible_candidate_ids: tuple[str, ...]
    stage_calls: tuple[StageCall, ...]
    crypto_calls: tuple[CryptoCall, ...]
    graph_call_count: int


@dataclass(frozen=True)
class MatrixValidation:
    findings: tuple[Finding, ...]
    semantic_sha256: str
    invariant_ids: tuple[str, ...]
    blocker_classes: tuple[BlockerClass, ...]


CryptoVerifier = Callable[[bytes, bytes, bytes], bool]


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


def verify_ed25519(public_key: bytes, message: bytes, signature: bytes) -> bool:
    del public_key, message, signature
    return False


def budget_disposition(charged_lines: int, cap: int) -> BudgetDisposition:
    del charged_lines, cap
    return BudgetDisposition.STOP_BEFORE_GREEN


def validate_matrix_bytes(matrix_bytes: bytes, freeze_bytes: bytes | None) -> MatrixValidation:
    del matrix_bytes, freeze_bytes
    return MatrixValidation(
        findings=(_not_implemented("matrix"),),
        semantic_sha256="0" * 64,
        invariant_ids=(),
        blocker_classes=(BlockerClass.IMPLEMENTATION,),
    )


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
        eligible_candidate_ids=(),
        stage_calls=(),
        crypto_calls=(),
        graph_call_count=0,
    )


def route_findings(
    root: Path = ROOT, *, changed_paths: tuple[str, ...] | None = None
) -> tuple[Finding, ...]:
    del root, changed_paths
    return (_not_implemented("route"),)


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
