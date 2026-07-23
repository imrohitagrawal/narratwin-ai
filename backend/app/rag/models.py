"""Typed Stage 4 RAG models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TENANT_LOCAL = "tenant_local"
OWNER_LOCAL = "user_local"
ACTOR_LOCAL = "user_local"
CHUNKING_STRATEGY_VERSION = "stage4-chunk-v1"
RETRIEVAL_STRATEGY_VERSION = "stage4-rag-v1"
RETRIEVAL_TOP_K = 6
RETRIEVAL_MIN_SCORE = 0.60
RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT = 6
MOCK_EMBEDDING_MODEL = "mock-embedding"
MOCK_EMBEDDING_MODEL_VERSION = "stage4-local-v1"


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    tenant_id: str
    project_id: str
    document_id: str
    source_filename: str
    source_document_checksum: str
    approved_at: str
    chunk_index: int
    text: str
    token_count: int
    checksum: str
    heading_path: list[str]
    line_start: int
    line_end: int
    embedding: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RetrievedContext:
    context_ref_id: str
    chunk: KnowledgeChunk
    score: float


@dataclass(frozen=True)
class ScriptClaim:
    claim_id: str
    text: str
    citation_index: int
    chunk_id: str | None
    script_span_start: int
    script_span_end: int


@dataclass(frozen=True)
class GeneratedScript:
    text: str
    claims: list[ScriptClaim]


@dataclass(frozen=True)
class UnsupportedClaim:
    claim_id: str
    claim_text: str
    reason: str


@dataclass(frozen=True)
class ClaimSupport:
    claim_support_id: str
    claim_id: str
    context_ref_id: str
    chunk_id: str
    document_id: str
    support_status: Literal["SUPPORTED"]
    support_score: float
    support_reason: str
    citation_index: int


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_id: str
    run_id: str
    tenant_id: str
    project_id: str
    evaluation_status: Literal["PASSED", "FAILED"]
    groundedness_score: float
    faithfulness_score: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    unsupported_claim_count: int
    unsupported_claims: list[UnsupportedClaim]
    claim_supports: list[ClaimSupport]
    context_ref_coverage: float
    policy_version: str
    schema_version: str
    safety_policy_version: str
