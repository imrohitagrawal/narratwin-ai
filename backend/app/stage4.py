"""Stage 4 local product slice orchestration with source_chunk citations."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path, PurePath
from threading import RLock
from typing import Any, Literal, TypeVar, cast

from backend.app.rag.chunking import checksum_text, chunk_document
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import (
    CHUNKING_STRATEGY_VERSION,
    MOCK_EMBEDDING_MODEL,
    MOCK_EMBEDDING_MODEL_VERSION,
    OWNER_LOCAL,
    RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT,
    RETRIEVAL_MIN_SCORE,
    RETRIEVAL_STRATEGY_VERSION,
    RETRIEVAL_TOP_K,
    TENANT_LOCAL,
    ClaimSupport,
    EvaluationResult,
    GeneratedScript,
    KnowledgeChunk,
    RetrievedContext,
    ScriptClaim,
    UnsupportedClaim,
)
from backend.app.rag.providers import MockEmbeddingProvider, MockLLMProvider, audience_label_for_script
from backend.app.rag.retrieval import retrieve_context
from backend.app.rag.store import InMemoryRagStore
from backend.app.storage import load_state, resolve_state_file, write_state
from backend.app.eval.metrics import evaluate_token_usage, estimate_cost_usd
from backend.app.observability import (
    langfuse_observation,
    log_event,
    record_walkthrough_metrics,
    with_trace,
)
from backend.app.curation import (CURATION_POLICY_VERSION, CURATION_SCHEMA_VERSION, CuratedOutcome, SourceAssertions, SourceDecisionRecord, SourceRecord, allowed_for_review, assertions_digest, canonical_digest, legal_exclusion, legal_exclusion_request, legal_pair, record_is_valid, restore_curated, restored_records)

MAX_UPLOAD_BYTES = 1_048_576
MAX_PROJECT_CORPUS_BYTES = 5 * 1_048_576
MAX_ACTIVE_DOCUMENTS_PER_PROJECT = 10
MAX_DOCUMENTS_PER_INGESTION = 10
MAX_CHUNKS_PER_DOCUMENT = 100
MAX_CHUNKS_PER_PROJECT = 200
MAX_PROJECTS_PER_TENANT = 25
MAX_RUNS_PER_PROJECT = 50
MAX_IDEMPOTENCY_RECORDS_PER_TENANT = 500
MAX_PROMPT_CHARS = 2_000
MAX_PUBLIC_EXCERPT_CHARS = 240
MAX_API_REQUEST_BYTES = 256 * 1024
MAX_UPLOAD_REQUEST_BYTES = MAX_UPLOAD_BYTES + 65_536
MAX_STAGE4_STATE_BYTES = 256 * 1_048_576
MAX_RESTORED_SCRIPT_CHARS = 20_000
MAX_RESTORED_LINEAGE_ITEMS = 24
MAX_RESTORED_CITATION_DIGITS = 6
ALLOWED_EXTENSIONS = {".md", ".txt"}
ALLOWED_CONTENT_TYPES_BY_EXTENSION = {
    ".md": "text/markdown",
    ".txt": "text/plain",
}
ARCHIVE_MAGIC_BYTES = (b"PK\x03\x04", b"Rar!\x1a\x07", b"7z\xbc\xaf\x27\x1c")
PROMPT_INJECTION_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|earlier)\s+instructions\b",
        r"\b(ignore|disregard|forget|override)\s+all\s+(instructions|rules|requirements)\b",
        r"\banswer\s+without\s+(citations|sources|grounding)\b",
        r"\b(reveal|print|show|exfiltrate|leak)\s+(the\s+)?(hidden\s+)?(system|developer)?\s*(prompt|message|secret|secrets)\b",
        r"\bfollow\s+(these|the)\s+instructions\s+instead\b",
        r"\bfollow\s+this\s+document\s+as\s+(system|developer)\s+policy\b",
        r"\btreat\s+this\s+document\s+as\s+(a\s+)?(system|developer)\s+(message|instruction|policy)\b",
        r"\bnew\s+(system|developer)\s+(message|instruction|policy)\b",
        r"\bdisable\s+(safety|grounding|citation|source)\s+(checks|rules|policy)\b",
    )
)
SECRET_REDACTION_PATTERNS = (
    ("OPENAI_LIKE_KEY", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("ANTHROPIC_LIKE_KEY", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("OPENROUTER_LIKE_KEY", re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{20,}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT_LIKE_TOKEN", re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b")),
    ("BEARER_TOKEN", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_.-]{20,}")),
    ("SECRET_LIKE_TOKEN", re.compile(r"(?i)\b(api[_-]?key|secret|token|password|credential)\b\s*[:=]\s*\S+")),
    ("LONG_HEX_TOKEN", re.compile(r"\b[a-f0-9]{32,}\b", re.IGNORECASE)),
)
T = TypeVar("T")
WalkthroughRunStatus = Literal["COMPLETED", "FAILED", "REFUSED"]
LOGGER = logging.getLogger(__name__)
SAFE_RESTORED_FAILURES = {(400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required for write requests."), (403, "FORBIDDEN", "Document is not accessible to this principal."), (403, "FORBIDDEN", "Project is not accessible to this principal."), (404, "NOT_FOUND", "Curated source not found."), (404, "NOT_FOUND", "Knowledge document not found."), (404, "NOT_FOUND", "Project not found."), (409, "IDEMPOTENCY_CONFLICT", "Idempotency key was reused with a different request."), (409, "IDEMPOTENCY_IN_PROGRESS", "Idempotency key is already in progress."), (409, "SOURCE_NOT_APPROVABLE", "Curated source bindings or policy are stale."), (413, "DOCUMENT_TOO_LARGE", "Document exceeds the Stage 4 chunk limit."), (413, "INGESTION_TOO_LARGE", "Too many documents requested for one ingestion run."), (413, "PROJECT_CORPUS_TOO_LARGE", "Project exceeds the Stage 4 chunk limit."), (413, "PROJECT_CORPUS_TOO_LARGE", "Project exceeds the Stage 4 corpus size limit."), (413, "PROJECT_DOCUMENT_LIMIT_EXCEEDED", "Project exceeds the Stage 4 document limit."), (413, "PROMPT_TOO_LARGE", "Prompt exceeds the Stage 4 limit."), (413, "UPLOAD_FILE_TOO_LARGE", "Curated source file exceeds the size limit."), (413, "UPLOAD_TOO_LARGE", "Upload exceeds the Stage 4 size limit."), (415, "UNSUPPORTED_MEDIA_TYPE", "Archive uploads are not accepted in Stage 4."), (415, "UNSUPPORTED_MEDIA_TYPE", "Only markdown and plain text files are accepted."), (422, "DOCUMENT_NOT_APPROVED", "Document must be approved before ingestion."), (422, "SECRET_LIKE_CONTENT", "Prompt contains secret-like content."), (422, "SECRET_LIKE_CONTENT", "Uploaded document contains secret-like content."), (422, "SOURCE_KIND_MISMATCH", "Legacy documents cannot use curated ingestion."), (422, "SOURCE_NOT_INGESTIBLE", "At least one bounded curated source is required."), (422, "SOURCE_NOT_INGESTIBLE", "Every curated source must be approved and current."), (422, "UNSAFE_DOCUMENT_CONTENT", "Curated source contains unsafe content."), (422, "UNSAFE_DOCUMENT_CONTENT", "Document contains unsafe instruction-like content."), (422, "VALIDATION_ERROR", "At least one document is required."), (422, "VALIDATION_ERROR", "Curated source assertions are incomplete or ineligible."), (422, "VALIDATION_ERROR", "Invalid filename."), (422, "VALIDATION_ERROR", "Project name is required."), (422, "VALIDATION_ERROR", "Uploaded document contains NUL bytes."), (422, "VALIDATION_ERROR", "Uploaded document contains too many control characters."), (422, "VALIDATION_ERROR", "Uploaded document is empty."), (422, "VALIDATION_ERROR", "Uploaded document must be UTF-8 text."), (429, "BACKPRESSURE_QUEUE_FULL", "Another Stage 4 operation is already active for this project."), (429, "RESOURCE_LIMIT_EXCEEDED", "Project exceeds the Stage 4 generation run limit."), (429, "RESOURCE_LIMIT_EXCEEDED", "Tenant exceeds the Stage 4 idempotency record limit."), (429, "RESOURCE_LIMIT_EXCEEDED", "Tenant exceeds the Stage 4 project limit."), (422, "VALIDATION_ERROR", "Curated source content is not safe to retain."), (422, "SECRET_LIKE_CONTENT", "Curated source content is not safe to retain."), (422, "UNSAFE_DOCUMENT_CONTENT", "Curated source content is not safe to retain.")}
SAFE_RESTORED_FAILURES.add((422, "GENERATED_SCRIPT_TOO_LARGE", "Generated script exceeds the Stage 4 limit."))
RESTORED_FAILURE_CODES_BY_ENDPOINT = {
    "POST /api/v1/projects": {"VALIDATION_ERROR", "RESOURCE_LIMIT_EXCEEDED"},
    "POST /api/v1/projects/{projectId}/knowledge-documents": {"FORBIDDEN", "NOT_FOUND", "PROJECT_DOCUMENT_LIMIT_EXCEEDED", "PROJECT_CORPUS_TOO_LARGE", "UPLOAD_TOO_LARGE", "UPLOAD_FILE_TOO_LARGE", "UNSUPPORTED_MEDIA_TYPE", "VALIDATION_ERROR", "SECRET_LIKE_CONTENT", "UNSAFE_DOCUMENT_CONTENT"},
    "PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval": {"FORBIDDEN", "NOT_FOUND", "SOURCE_NOT_APPROVABLE"},
    "POST /api/v1/projects/{projectId}/ingestion-runs": {"FORBIDDEN", "NOT_FOUND", "SOURCE_NOT_INGESTIBLE", "SOURCE_KIND_MISMATCH", "VALIDATION_ERROR", "INGESTION_TOO_LARGE", "DOCUMENT_NOT_APPROVED", "UNSAFE_DOCUMENT_CONTENT", "DOCUMENT_TOO_LARGE", "PROJECT_CORPUS_TOO_LARGE", "BACKPRESSURE_QUEUE_FULL"},
    "POST /api/v1/projects/{projectId}/walkthrough-runs": {"FORBIDDEN", "NOT_FOUND", "PROMPT_TOO_LARGE", "SECRET_LIKE_CONTENT", "GENERATED_SCRIPT_TOO_LARGE", "RESOURCE_LIMIT_EXCEEDED", "BACKPRESSURE_QUEUE_FULL"},
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _context_ref_id(*, tenant_id: str, project_id: str, chunk_id: str, query: str) -> str:
    return "ctx_" + hashlib.sha256(f"{tenant_id}:{project_id}:{chunk_id}:{query}".encode("utf-8")).hexdigest()[:16]


def _valid_retrieval_tuple(values: tuple[Any, ...]) -> bool: return type(values[1]) is int and type(values[2]) is not bool and isinstance(values[2], (int, float)) and math.isfinite(values[2])


class Stage4Error(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
    def __deepcopy__(self, _memo: object) -> Stage4Error: return Stage4Error(self.status_code, self.code, self.message)


@dataclass
class LocalPrincipal:
    tenant_id: str = TENANT_LOCAL
    actor_id: str = OWNER_LOCAL


@dataclass
class ProjectRecord:
    project_id: str
    tenant_id: str
    owner_id: str
    name: str
    description: str
    default_audience: str
    default_language: str
    created_at: str
    updated_at: str


@dataclass
class DocumentRecord:
    document_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    source_filename: str
    content_type: str
    size_bytes: int
    checksum: str
    text: str
    document_status: Literal["STORED"] = "STORED"
    approval_status: Literal["PENDING", "APPROVED"] = "PENDING"
    ingestion_status: Literal["NOT_STARTED", "INGESTED"] = "NOT_STARTED"
    created_at: str = field(default_factory=_now)
    approved_at: str | None = None
    ingested_at: str | None = None


@dataclass
class IngestionRunRecord:
    ingestion_run_id: str
    tenant_id: str
    actor_id: str
    project_id: str
    document_ids: list[str]
    status: Literal["COMPLETED"]
    chunk_count: int
    embedding_count: int
    created_at: str
    source_ids: list[str] = field(default_factory=list)


@dataclass
class WalkthroughRunRecord:
    run_id: str
    tenant_id: str
    actor_id: str
    project_id: str
    status: WalkthroughRunStatus
    failure_reason: str | None
    evaluation_status: Literal["PASSED", "FAILED"] | None
    trace_id: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    audience: str
    requested_language: str
    depth: str
    style: str
    accepted_script_text: str | None
    generated_script: GeneratedScript | None
    retrieved_context: list[RetrievedContext]
    evaluation: EvaluationResult | None
    created_at: str
    request_checksum: str = ""
    retrieval_strategy_version: str | None = None
    retrieval_top_k: int | None = None
    retrieval_score_threshold: float | None = None


@dataclass
class IdempotencyRecord:
    idempotency_record_id: str
    tenant_id: str
    actor_id: str
    idempotency_scope: str
    endpoint: str
    idempotency_key: str
    request_checksum: str
    status: Literal["PENDING", "COMPLETED", "FAILED"]
    value: Any
    created_at: str
    updated_at: str


def restored_rag_store(payload: object) -> InMemoryRagStore:
    rows = payload.get("chunks", []) if isinstance(payload, dict) else []
    valid_rows: list[dict[str, Any]] = []
    for row in rows if isinstance(rows, list) else []:
        try:
            candidate = InMemoryRagStore.from_dict({"chunks": [row]})
            valid_rows.extend(cast(list[dict[str, Any]], candidate.to_dict()["chunks"]))
        except (KeyError, TypeError, ValueError):
            continue
    return InMemoryRagStore.from_dict({"chunks": valid_rows})


class Stage4Service:
    WALKTHROUGH_REFUSAL_REASON_PROMPT_INJECTION = "PROMPT_INJECTION_DETECTED"
    WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL = "LOW_RETRIEVAL_CONFIDENCE"
    WALKTHROUGH_REFUSAL_REASON_UNSAFE_CONTEXT = "UNSAFE_RETRIEVED_CONTEXT"
    WALKTHROUGH_REFUSAL_REASON_UNSUPPORTED_FACT = "UNSUPPORTED_PROJECT_FACT"

    def __init__(self, *, state_path: Path | None = None) -> None:
        self.embedder = MockEmbeddingProvider()
        self.llm = MockLLMProvider()
        self.rag_store = InMemoryRagStore()
        self.state_path = state_path
        self.projects: dict[str, ProjectRecord] = {}
        self.documents: dict[str, DocumentRecord] = {}
        self.sources: dict[str, SourceRecord] = {}
        self.source_decisions: dict[str, SourceDecisionRecord] = {}
        self.ingestion_runs: dict[str, IngestionRunRecord] = {}
        self.walkthrough_runs: dict[str, WalkthroughRunRecord] = {}
        self.idempotency_records: dict[tuple[str, str, str, str, str], IdempotencyRecord] = {}
        self._quarantined_walkthrough_rows, self._quarantined_idempotency_rows, self._stale_idempotency = cast(tuple[list[dict[str, Any]], list[dict[str, Any]], dict[tuple[str, str, str, str, str], str]], ([], [], {}))
        self._active_ingestions: set[tuple[str, str]] = set()
        self._active_generations: set[tuple[str, str]] = set()
        self._operation_lock = RLock()
        self._project_counter = 0
        self._document_counter = 0
        self._source_counter = 0
        self._ingestion_counter = 0
        self._run_counter = 0
        self._restore()

    def reset(self) -> None:
        with self._operation_lock:
            self._clear_runtime_state()
            self._persist_locked()

    def _clear_runtime_state(self) -> None:
        self.rag_store.clear()
        self.projects.clear()
        self.documents.clear()
        self.sources.clear()
        self.source_decisions.clear()
        self.ingestion_runs.clear()
        self.walkthrough_runs.clear()
        self.idempotency_records.clear()
        self._quarantined_walkthrough_rows, self._quarantined_idempotency_rows, self._stale_idempotency = [], [], {}
        self._active_ingestions.clear()
        self._active_generations.clear()
        self._project_counter = 0
        self._document_counter = 0
        self._source_counter = 0
        self._ingestion_counter = 0
        self._run_counter = 0

    def _restore(self) -> None:
        if self.state_path is not None:
            try:
                if self.state_path.exists() and self.state_path.stat().st_size > MAX_STAGE4_STATE_BYTES:
                    LOGGER.warning("Ignoring oversized Stage 4 local state snapshot at %s.", self.state_path)
                    return
            except OSError as exc:
                LOGGER.warning("Ignoring unreadable Stage 4 local state snapshot at %s: %s", self.state_path, exc)
                return
        payload = load_state(self.state_path)
        if payload is None:
            return
        try:
            if payload.get("schema") != "stage4-local-state-v1":
                raise ValueError("Stage 4 state schema mismatch.")
            self.projects = restored_records(payload.get("projects"), "project_id", lambda row: ProjectRecord(**row), self._restored_project_is_valid)
            self.documents = restored_records(payload.get("documents"), "document_id", lambda row: DocumentRecord(**row), self._restored_document_is_valid)
            self.sources, self.source_decisions = restore_curated(payload.get("sources"), payload.get("sourceDecisions"), self.projects, self._restored_curated_source_is_safe, self.documents)
            self.ingestion_runs = restored_records(payload.get("ingestionRuns"), "ingestion_run_id", lambda row: IngestionRunRecord(**row), self._restored_ingestion_run_is_valid)
            self.rag_store = restored_rag_store(payload.get("ragStore"))
            self.rag_store.prune(lambda chunk: record_is_valid(chunk, self._restored_chunk_is_valid))
            self.ingestion_runs = {
                run_id: run
                for run_id, run in self.ingestion_runs.items()
                if self._restored_ingestion_run_has_chunks(run)
            }
            self._reconcile_restored_document_ingestion_status()
            self.rag_store.prune(lambda chunk: record_is_valid(chunk, self._restored_chunk_is_valid))
            stale_runs = self._restore_walkthrough_rows(payload)
            self._restore_idempotency_rows(payload, stale_runs)
            counters = payload.get("counters", {})
            project_counter = max_numeric_suffix(self.projects, "proj_")
            document_counter = max_numeric_suffix(self.documents, "doc_")
            source_counter = max(max_numeric_suffix(self.sources, "source_"), max_numeric_suffix(self.source_decisions, "decision_"))
            ingestion_counter = max_numeric_suffix(self.ingestion_runs, "ing_")
            run_counter = max(max_numeric_suffix(self.walkthrough_runs, "run_"), max_numeric_suffix({str(row.get("run_id")): None for row in self._quarantined_walkthrough_rows}, "run_"))
            counter_values = counters if isinstance(counters, dict) else {}
            self._project_counter = max(counter_values.get("project", 0), project_counter) if type(counter_values.get("project", 0)) is int else project_counter
            self._document_counter = max(counter_values.get("document", 0), document_counter) if type(counter_values.get("document", 0)) is int else document_counter
            self._source_counter = min(999999, max(counter_values.get("source", 0), source_counter)) if type(counter_values.get("source", 0)) is int else min(999999, source_counter)
            self._ingestion_counter = max(counter_values.get("ingestion", 0), ingestion_counter) if type(counter_values.get("ingestion", 0)) is int else ingestion_counter
            self._run_counter = max(counter_values.get("run", 0), run_counter) if type(counter_values.get("run", 0)) is int else run_counter
            self._persist_locked()
        except (KeyError, TypeError, ValueError) as exc:
            LOGGER.warning("Ignoring incompatible Stage 4 local state snapshot: %s", exc)
            self._clear_runtime_state()

    def _restore_walkthrough_rows(self, payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        rows = [*(cast(list[object], payload.get("walkthroughRuns")) if isinstance(payload.get("walkthroughRuns"), list) else []), *(cast(list[object], payload.get("quarantinedWalkthroughRuns")) if isinstance(payload.get("quarantinedWalkthroughRuns"), list) else [])]
        rows = rows[: MAX_PROJECTS_PER_TENANT * MAX_RUNS_PER_PROJECT]
        identities = [row.get("run_id") for row in rows if isinstance(row, dict)]
        self.walkthrough_runs, self._quarantined_walkthrough_rows = {}, []
        stale: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("run_id"), str) or identities.count(row.get("run_id")) != 1:
                continue
            try:
                if not raw_walkthrough_lineage_is_bounded_and_typed(row):
                    continue
                run = walkthrough_run_from_dict(row)
                if not record_is_valid(run, self._restored_walkthrough_run_is_valid):
                    continue
                lineage_is_current = self._restored_retrieval_lineage_is_current(row, run)
                if lineage_is_current and self._restored_citation_lineage_is_valid(run):
                    self.walkthrough_runs[run.run_id] = run
                elif not lineage_is_current:
                    stale[run.run_id] = deepcopy(row)
                    self._quarantined_walkthrough_rows.append(deepcopy(row))
            except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
                LOGGER.warning("Skipping incompatible Stage 4 walkthrough row: %s", exc)
        return stale

    def _restore_idempotency_rows(self, payload: dict[str, Any], stale_runs: dict[str, dict[str, Any]]) -> None:
        rows = [*(cast(list[object], payload.get("idempotencyRecords")) if isinstance(payload.get("idempotencyRecords"), list) else []), *(cast(list[object], payload.get("quarantinedIdempotencyRecords")) if isinstance(payload.get("quarantinedIdempotencyRecords"), list) else [])]
        rows = rows[:MAX_IDEMPOTENCY_RECORDS_PER_TENANT]
        identities = [row.get("idempotency_record_id") for row in rows if isinstance(row, dict)]
        keys = [tuple(row.get(name) for name in ("tenant_id", "actor_id", "idempotency_scope", "endpoint", "idempotency_key")) for row in rows if isinstance(row, dict)]
        self.idempotency_records, self._quarantined_idempotency_rows, self._stale_idempotency = {}, [], {}
        for row in rows:
            if not isinstance(row, dict) or row.get("status") == "PENDING" or identities.count(row.get("idempotency_record_id")) != 1:
                continue
            raw_key = tuple(row.get(name) for name in ("tenant_id", "actor_id", "idempotency_scope", "endpoint", "idempotency_key"))
            if keys.count(raw_key) != 1:
                if all(isinstance(part, str) for part in raw_key):
                    self._stale_idempotency[cast(tuple[str, str, str, str, str], raw_key)] = ""
                continue
            stale = self._stale_idempotency_binding(row, stale_runs)
            if stale is not None:
                key, checksum = stale
                self._quarantined_idempotency_rows.append(deepcopy(row))
                self._stale_idempotency[key] = checksum
                continue
            try:
                record = idempotency_record_from_dict(row, self)
            except (KeyError, TypeError, ValueError) as exc:
                LOGGER.warning("Skipping incompatible Stage 4 idempotency record: %s", exc)
                continue
            key = (record.tenant_id, record.actor_id, record.idempotency_scope, record.endpoint, record.idempotency_key)
            self.idempotency_records[key] = record

    def _stale_idempotency_binding(self, row: dict[str, Any], stale_runs: dict[str, dict[str, Any]]) -> tuple[tuple[str, str, str, str, str], str] | None:
        names = ("tenant_id", "actor_id", "idempotency_scope", "endpoint", "idempotency_key", "request_checksum")
        if row.get("status") != "COMPLETED" or not all(isinstance(row.get(name), str) for name in names):
            return None
        tenant, actor, scope, endpoint, key, checksum = cast(tuple[str, str, str, str, str, str], tuple(row[name] for name in names))
        value, project = row.get("value"), self.projects.get(scope)
        run = stale_runs.get(str(value.get("id", ""))) if isinstance(value, dict) else None
        record_id, binding = "idem_" + hashlib.sha256(f"{tenant}:{actor}:{scope}:{endpoint}:{key}".encode()).hexdigest()[:16], [tenant, actor, scope, endpoint, checksum]
        if not isinstance(value, dict) or not isinstance(run, dict) or project is None:
            return None
        if row.get("idempotency_record_id") != record_id or re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", checksum) is None:
            return None
        if value.get("kind") != "walkthrough" or value.get("binding") != binding or endpoint != "POST /api/v1/projects/{projectId}/walkthrough-runs":
            return None
        if (tenant, actor, scope, checksum) != (run.get("tenant_id"), run.get("actor_id"), run.get("project_id"), run.get("request_checksum")) or (tenant, actor) != (project.tenant_id, project.owner_id):
            return None
        return (tenant, actor, scope, endpoint, key), checksum

    def _restore_failed_operation_locked(
        self,
        snapshot: dict[str, Any],
        *,
        record_key: tuple[str, str, str, str, str] | None,
        value: object | None,
    ) -> None:
        if record_key is not None:
            prior_record = snapshot["idempotencyRecords"].get(record_key)
            if prior_record is None:
                self.idempotency_records.pop(record_key, None)
            else:
                self.idempotency_records[record_key] = prior_record
        if isinstance(value, ProjectRecord):
            if value.project_id in snapshot["projects"]:
                self.projects[value.project_id] = snapshot["projects"][value.project_id]
            else:
                self.projects.pop(value.project_id, None)
        elif isinstance(value, DocumentRecord):
            if value.document_id in snapshot["documents"]:
                self.documents[value.document_id] = snapshot["documents"][value.document_id]
            else:
                self.documents.pop(value.document_id, None)
        elif isinstance(value, IngestionRunRecord):
            prior_rag_store = InMemoryRagStore.from_dict(snapshot["ragStore"])
            failed_document_ids = set(value.document_ids or value.source_ids)
            self.rag_store.prune(
                lambda chunk: not (
                    chunk.tenant_id == value.tenant_id
                    and chunk.project_id == value.project_id
                    and chunk.document_id in failed_document_ids
                    and not prior_rag_store.has_chunk(
                        tenant_id=chunk.tenant_id,
                        project_id=chunk.project_id,
                        chunk_id=chunk.chunk_id,
                    )
                )
            )
            self.ingestion_runs.pop(value.ingestion_run_id, None)
            for document_id in value.document_ids or value.source_ids:
                if document_id in snapshot["documents"]:
                    self.documents[document_id] = snapshot["documents"][document_id]
                elif document_id in snapshot["sources"]:
                    self.sources[document_id] = snapshot["sources"][document_id]
        elif isinstance(value, WalkthroughRunRecord):
            self.walkthrough_runs.pop(value.run_id, None)
        elif isinstance(value, CuratedOutcome):
            self.sources = deepcopy(snapshot["sources"])
            self.source_decisions = deepcopy(snapshot["sourceDecisions"])
        counters = snapshot["counters"]
        self._project_counter = max(int(counters["project"]), max_numeric_suffix(self.projects, "proj_"))
        self._document_counter = max(int(counters["document"]), max_numeric_suffix(self.documents, "doc_"))
        self._source_counter = max(int(counters["source"]), max_numeric_suffix(self.sources, "source_"))
        self._ingestion_counter = max(int(counters["ingestion"]), max_numeric_suffix(self.ingestion_runs, "ing_"))
        self._run_counter = max(int(counters["run"]), max_numeric_suffix(self.walkthrough_runs, "run_"))
        self._quarantined_walkthrough_rows = deepcopy(snapshot["quarantinedWalkthroughRuns"])
        self._quarantined_idempotency_rows = deepcopy(snapshot["quarantinedIdempotencyRecords"])
        self._stale_idempotency = deepcopy(snapshot["staleIdempotency"])

    def _restored_project_is_valid(self, project: ProjectRecord) -> bool:
        fields = (project.project_id, project.tenant_id, project.owner_id, project.name, project.description, project.default_audience, project.default_language, project.created_at, project.updated_at)
        return all(isinstance(value, str) for value in fields) and bool(project.project_id and project.tenant_id and project.owner_id and project.name.strip())

    def _restored_document_is_valid(self, document: DocumentRecord) -> bool:
        project = self.projects.get(document.project_id) if isinstance(document.project_id, str) else None
        strings = (document.document_id, document.tenant_id, document.owner_id, document.project_id, document.source_filename, document.content_type, document.checksum, document.text, document.document_status, document.approval_status, document.ingestion_status, document.created_at)
        timestamps_valid = (document.approved_at is None or isinstance(document.approved_at, str)) and (document.ingested_at is None or isinstance(document.ingested_at, str))
        state_valid = (document.approval_status, document.ingestion_status, document.approved_at is not None, document.ingested_at is not None) in {("PENDING", "NOT_STARTED", False, False), ("APPROVED", "NOT_STARTED", True, False), ("APPROVED", "INGESTED", True, True)}
        suffix = PurePath(document.source_filename).suffix.lower() if isinstance(document.source_filename, str) else ""
        content_valid = bool(document.text.strip()) and document.size_bytes == len(document.text.encode()) and document.checksum == checksum_text(document.text) and document.size_bytes <= MAX_UPLOAD_BYTES
        try:
            validate_upload_bytes(document.text.encode())
            boundary_valid = sanitize_filename(document.source_filename) == document.source_filename and normalize_content_type(document.content_type) == ALLOWED_CONTENT_TYPES_BY_EXTENSION.get(suffix)
        except Stage4Error:
            return False
        return all(isinstance(value, str) for value in strings) and isinstance(document.size_bytes, int) and not isinstance(document.size_bytes, bool) and timestamps_valid and state_valid and document.document_status == "STORED" and project is not None and (project.tenant_id, project.owner_id) == (document.tenant_id, document.owner_id) and content_valid and boundary_valid and not contains_secret_like_content(document.text) and not contains_prompt_injection(document.text)

    def _restored_failure_is_valid(self, tenant_id: str, actor_id: str, scope: str, endpoint: str, failure: tuple[object, object, object]) -> bool:
        codes = RESTORED_FAILURE_CODES_BY_ENDPOINT.get(endpoint)
        if failure not in SAFE_RESTORED_FAILURES or codes is None or failure[1] not in codes:
            return False
        if endpoint == "POST /api/v1/projects":
            return scope == "project:create"
        project = self.projects.get(scope)
        if project is None:
            return failure == (404, "NOT_FOUND", "Project not found.")
        if (project.tenant_id, project.owner_id) != (tenant_id, actor_id):
            return failure == (403, "FORBIDDEN", "Project is not accessible to this principal.")
        return failure not in {(404, "NOT_FOUND", "Project not found."), (403, "FORBIDDEN", "Project is not accessible to this principal."), (403, "FORBIDDEN", "Document is not accessible to this principal.")}

    def _restored_ingestion_run_is_valid(self, run: IngestionRunRecord) -> bool:
        if not all(isinstance(value, str) for value in (run.ingestion_run_id, run.tenant_id, run.actor_id, run.project_id, run.status, run.created_at)) or not isinstance(run.document_ids, list) or not isinstance(run.source_ids, list) or not all(isinstance(value, str) for value in run.document_ids + run.source_ids) or not all(isinstance(value, int) and not isinstance(value, bool) for value in (run.chunk_count, run.embedding_count)) or run.status != "COMPLETED":
            return False
        project = self.projects.get(run.project_id)
        if project is None:
            return False
        if project.tenant_id != run.tenant_id or project.owner_id != run.actor_id:
            return False
        ids = run.document_ids or run.source_ids
        members = [self.documents.get(identifier) or self.sources.get(identifier) for identifier in ids]
        return bool(bool(run.document_ids) != bool(run.source_ids) and len(ids) == len(set(ids)) and all(member and (member.tenant_id, member.owner_id, member.project_id) == (run.tenant_id, run.actor_id, run.project_id) for member in members) and all(any(decision.source_id == identifier and legal_pair(self.sources[identifier], decision) and decision.decision_state == "APPROVED" for decision in self.source_decisions.values()) for identifier in run.source_ids))

    def _restored_ingestion_run_has_chunks(self, run: IngestionRunRecord) -> bool:
        if not self._restored_ingestion_run_is_valid(run):
            return False
        chunks = [
            chunk
            for chunk in self.rag_store.chunks_for_project(tenant_id=run.tenant_id, project_id=run.project_id)
            if chunk.document_id in set(run.document_ids or run.source_ids)
        ]
        chunk_document_ids = {chunk.document_id for chunk in chunks}
        return (
            run.chunk_count == len(chunks)
            and run.embedding_count == len(chunks)
            and all(document_id in chunk_document_ids for document_id in (run.document_ids or run.source_ids))
        )

    def _reconcile_restored_document_ingestion_status(self) -> None:
        ingested_document_ids = {
            document_id for run in self.ingestion_runs.values() for document_id in run.document_ids
        }
        for document in self.documents.values():
            if document.ingestion_status == "INGESTED" and document.document_id not in ingested_document_ids:
                document.ingestion_status = "NOT_STARTED"
                document.ingested_at = None
        ingested_source_ids = {source_id for run in self.ingestion_runs.values() for source_id in run.source_ids}
        for source in self.sources.values():
            if source.ingestion_status == "INGESTED" and source.source_id not in ingested_source_ids:
                source.ingestion_status, source.ingested_at = "NOT_STARTED", None

    def _restored_chunk_is_valid(self, chunk: KnowledgeChunk) -> bool:
        source = self.sources.get(chunk.document_id)
        if source is not None:
            decision = next((value for value in self.source_decisions.values() if value.source_id == source.source_id), None)
            if decision is None or decision.decision_state != "APPROVED" or source.ingestion_status != "INGESTED":
                return False
            expected = chunk_document(document_id=source.source_id, project_id=source.project_id, tenant_id=source.tenant_id, source_filename=source.source_filename, text=source.text, source_document_checksum=source.checksum, approved_at=decision.approved_at or decision.created_at, max_chunks=MAX_CHUNKS_PER_DOCUMENT)
            return any(replace(value, embedding=self.embedder.embed(value.text)) == chunk for value in expected)
        document = self.documents.get(chunk.document_id)
        if document is None:
            return False
        if (
            document.ingestion_status != "INGESTED"
            or chunk.tenant_id != document.tenant_id
            or chunk.project_id != document.project_id
            or chunk.source_filename != document.source_filename
            or chunk.source_document_checksum != document.checksum
            or chunk.approved_at != (document.approved_at or document.created_at)
            or chunk.checksum != checksum_text(chunk.text)
        ):
            return False
        try:
            parsed_text = parse_document_text(document.text)
        except Stage4Error:
            return False
        try:
            expected_chunks = chunk_document(
                document_id=document.document_id,
                project_id=document.project_id,
                tenant_id=document.tenant_id,
                source_filename=document.source_filename,
                text=parsed_text,
                source_document_checksum=document.checksum,
                approved_at=document.approved_at or document.created_at,
                max_chunks=MAX_CHUNKS_PER_DOCUMENT,
            )
        except ValueError:
            return False
        return any(
            candidate.chunk_id == chunk.chunk_id
            and candidate.chunk_index == chunk.chunk_index
            and candidate.text == chunk.text
            and candidate.token_count == chunk.token_count
            and candidate.checksum == chunk.checksum
            and candidate.heading_path == chunk.heading_path
            and candidate.line_start == chunk.line_start
            and candidate.line_end == chunk.line_end
            for candidate in expected_chunks
        )

    def _restored_curated_source_is_safe(self, source: SourceRecord) -> bool:
        try:
            return source.size_bytes <= MAX_UPLOAD_BYTES and bool(source.text.strip()) and allowed_for_review(source.assertions) and sanitize_filename(source.source_filename) == source.source_filename and normalize_content_type(source.content_type) == ALLOWED_CONTENT_TYPES_BY_EXTENSION.get(PurePath(source.source_filename).suffix.lower()) and not contains_secret_like_content(source.text) and not contains_prompt_injection(source.text) and validate_upload_bytes(source.text.encode()) is None  # type: ignore[func-returns-value]
        except (AttributeError, Stage4Error, TypeError):
            return False
    def _restored_walkthrough_run_is_valid(self, run: WalkthroughRunRecord) -> bool:
        if not isinstance(run.audience, str) or not isinstance(run.requested_language, str) or not isinstance(run.depth, str) or not isinstance(run.style, str):
            return False
        if not isinstance(run.request_checksum, str) or run.request_checksum and re.fullmatch(r"sha256:[0-9a-f]{64}", run.request_checksum) is None:
            return False
        project = self.projects.get(run.project_id)
        if project is None:
            return False
        if project.tenant_id != run.tenant_id or project.owner_id != run.actor_id:
            return False
        if run.status == "COMPLETED":
            if (
                run.accepted_script_text is None
                or run.generated_script is None
                or run.evaluation is None
                or not run.retrieved_context
                or run.evaluation_status != "PASSED"
            ):
                return False
        elif run.status == "FAILED":
            if run.generated_script is None or run.evaluation is None or run.evaluation_status != "FAILED":
                return False
        elif run.status == "REFUSED":
            if (
                run.accepted_script_text is not None
                or run.generated_script is not None
                or run.evaluation is not None
                or run.retrieved_context
                or run.evaluation_status is not None
            ):
                return False
        else:
            return False
        if any((context.chunk.tenant_id, context.chunk.project_id) != (run.tenant_id, run.project_id)
               or not self._restored_chunk_is_valid(context.chunk) for context in run.retrieved_context):
            return False
        if any(
            not self.rag_store.has_chunk(
                tenant_id=context.chunk.tenant_id,
                project_id=context.chunk.project_id,
                chunk_id=context.chunk.chunk_id,
            )
            for context in run.retrieved_context
        ):
            return False
        if run.evaluation is None:
            return True
        if any(type(getattr(run.evaluation, name)) is bool or not math.isfinite(float(getattr(run.evaluation, name)))
               or not 0.0 <= float(getattr(run.evaluation, name)) <= 1.0 for name in ("groundedness_score", "faithfulness_score", "answer_relevancy", "context_precision", "context_recall", "context_ref_coverage")):
            return False
        if (
            run.evaluation.run_id != run.run_id
            or run.evaluation.tenant_id != run.tenant_id
            or run.evaluation.project_id != run.project_id
        ):
            return False
        context_by_ref = {context.context_ref_id: context for context in run.retrieved_context}
        context_chunk_ids = {context.chunk.chunk_id for context in run.retrieved_context}
        claim_ids = {claim.claim_id for claim in run.generated_script.claims} if run.generated_script is not None else set()
        unsupported_claim_ids = {claim.claim_id for claim in run.evaluation.unsupported_claims}
        if run.generated_script is not None and any(
            claim.chunk_id is not None
            and claim.chunk_id not in context_chunk_ids
            and claim.claim_id not in unsupported_claim_ids
            for claim in run.generated_script.claims
        ):
            return False
        return all(
            (support.document_id in self.documents or support.document_id in self.sources)
            and support.claim_id in claim_ids
            and support.context_ref_id in context_by_ref
            and context_by_ref[support.context_ref_id].chunk.chunk_id == support.chunk_id
            and context_by_ref[support.context_ref_id].chunk.document_id == support.document_id
            and self.rag_store.has_chunk(
                tenant_id=run.tenant_id,
                project_id=run.project_id,
                chunk_id=support.chunk_id,
            )
            for support in run.evaluation.claim_supports
        )

    def _restored_citation_lineage_is_valid(
        self,
        run: WalkthroughRunRecord,
    ) -> bool:
        script, evaluation = run.generated_script, run.evaluation
        if script is None or evaluation is None:
            return run.status == "REFUSED"
        expected_status = "PASSED" if run.status == "COMPLETED" else "FAILED"
        expected_failure = None if run.status == "COMPLETED" else self.WALKTHROUGH_REFUSAL_REASON_UNSUPPORTED_FACT
        if evaluation.evaluation_status != expected_status or run.failure_reason != expected_failure:
            return False
        if run.status == "COMPLETED" and run.accepted_script_text != script.text:
            return False
        if run.status == "FAILED" and run.accepted_script_text is not None:
            return False
        cursor = 0
        for claim in script.claims:
            if not (cursor <= claim.script_span_start < claim.script_span_end <= len(script.text)):
                return False
            if script.text[cursor : claim.script_span_start].strip():
                return False
            visible = script.text[claim.script_span_start : claim.script_span_end]
            visible_claim = re.sub(r"\s*\[\d+\]\s*", " ", visible).strip()
            visible_claim = re.sub(r"(?i)^for\s+[a-z_ -]+s,\s*", "", visible_claim).strip()
            if " ".join(visible_claim.split()) != " ".join(claim.text.split()):
                return False
            cursor = claim.script_span_end
        if not script.claims or script.text[cursor:].strip():
            return False
        reproduced = evaluate_grounding(
            tenant_id=run.tenant_id,
            project_id=run.project_id,
            run_id=run.run_id,
            candidate=script,
            retrieved_context=run.retrieved_context,
            prompt="",
            all_chunks=self.rag_store.chunks_for_project(
                tenant_id=run.tenant_id,
                project_id=run.project_id,
            ),
        )
        reproduced = replace(
            reproduced,
            answer_relevancy=evaluation.answer_relevancy, context_recall=evaluation.context_recall,
            retrieval_strategy_version=RETRIEVAL_STRATEGY_VERSION,
            retrieval_top_k=RETRIEVAL_TOP_K,
            retrieval_score_threshold=RETRIEVAL_MIN_SCORE,
        )
        return reproduced == evaluation

    def _fresh_lineage_ownership_is_valid(self, run: WalkthroughRunRecord) -> bool:
        contexts = {item.context_ref_id: item for item in run.retrieved_context}
        canonical = {item.chunk_id: item for item in self.rag_store.chunks_for_project(
            tenant_id=run.tenant_id, project_id=run.project_id
        )}
        if len(contexts) != len(run.retrieved_context) or any(
            (item.chunk.tenant_id, item.chunk.project_id) != (run.tenant_id, run.project_id)
            or canonical.get(item.chunk.chunk_id) != item.chunk
            for item in run.retrieved_context
        ):
            return False
        if run.evaluation is None or run.generated_script is None:
            return run.status == "REFUSED"
        evaluation = run.evaluation
        if (evaluation.tenant_id, evaluation.project_id, evaluation.run_id) != (run.tenant_id, run.project_id, run.run_id):
            return False
        if evaluation.evaluation_id != f"eval_{run.run_id.removeprefix('run_')}":
            return False
        if [item.claim_support_id for item in evaluation.claim_supports] != [
            f"claimsup_{index:03d}" for index in range(1, len(evaluation.claim_supports) + 1)
        ]:
            return False
        claims = {claim.claim_id: claim for claim in run.generated_script.claims}
        unsupported = {claim.claim_id for claim in evaluation.unsupported_claims}
        if len(claims) != len(run.generated_script.claims) or len(unsupported) != len(evaluation.unsupported_claims):
            return False
        supported = [support.claim_id for support in evaluation.claim_supports]
        if (
            len(supported) != len(set(supported)) or unsupported.intersection(supported)
            or set(supported).union(unsupported) != set(claims)
        ):
            return False
        context_chunks = {item.chunk.chunk_id for item in contexts.values()}
        if any(claim.chunk_id not in context_chunks and claim.claim_id not in unsupported for claim in run.generated_script.claims):
            return False
        return all(
            support.claim_id in claims and support.context_ref_id in contexts
            and claims[support.claim_id].chunk_id == support.chunk_id
            and claims[support.claim_id].citation_index == support.citation_index
            and 0 < support.citation_index <= len(run.retrieved_context)
            and run.retrieved_context[support.citation_index - 1].context_ref_id == support.context_ref_id
            and contexts[support.context_ref_id].chunk.chunk_id == support.chunk_id
            and contexts[support.context_ref_id].chunk.document_id == support.document_id
            for support in evaluation.claim_supports
        )

    def _restored_retrieval_lineage_is_current(self, row: dict[str, Any], run: WalkthroughRunRecord) -> bool:
        names, expected = ("retrieval_strategy_version", "retrieval_top_k", "retrieval_score_threshold"), (RETRIEVAL_STRATEGY_VERSION, RETRIEVAL_TOP_K, RETRIEVAL_MIN_SCORE)
        raw = tuple(row.get(name) for name in names)
        if not _valid_retrieval_tuple(raw) or raw != expected or tuple(getattr(run, name) for name in names) != expected:
            return False
        if run.status == "REFUSED":
            return row.get("evaluation") is None
        evaluation_row = row.get("evaluation")
        if not isinstance(evaluation_row, dict) or run.evaluation is None:
            return False
        evaluation_raw = tuple(evaluation_row.get(name) for name in names)
        if not _valid_retrieval_tuple(evaluation_raw) or evaluation_raw != expected or tuple(getattr(run.evaluation, name) for name in names) != expected:
            return False
        context_rows = row.get("retrieved_context")
        if not isinstance(context_rows, list) or len(context_rows) != len(run.retrieved_context) or len(context_rows) > RETRIEVAL_TOP_K:
            return False
        scores = [item.get("score") for item in context_rows if isinstance(item, dict)]
        if len(scores) != len(context_rows) or any(type(score) is bool or not isinstance(score, (int, float)) or not math.isfinite(score) or score < RETRIEVAL_MIN_SCORE for score in scores):
            return False
        contexts = run.retrieved_context
        if any(sum(other.chunk.document_id == context.chunk.document_id for other in contexts) > RETRIEVAL_MAX_CHUNKS_PER_DOCUMENT for context in contexts) or len({item.context_ref_id for item in contexts}) != len(contexts) or len({item.chunk.chunk_id for item in contexts}) != len(contexts):
            return False
        ordered = sorted(contexts, key=lambda item: (-item.score, tuple(-ord(char) for char in item.chunk.approved_at), item.chunk.chunk_index, item.chunk.chunk_id))
        return contexts == ordered

    def _runtime_snapshot_locked(self) -> dict[str, Any]:
        return {
            "ragStore": self.rag_store.to_dict(),
            "projects": deepcopy(self.projects),
            "documents": deepcopy(self.documents),
            "sources": deepcopy(self.sources),
            "sourceDecisions": deepcopy(self.source_decisions),
            "ingestionRuns": deepcopy(self.ingestion_runs),
            "walkthroughRuns": deepcopy(self.walkthrough_runs),
            "idempotencyRecords": deepcopy(self.idempotency_records),
            "quarantinedWalkthroughRuns": deepcopy(self._quarantined_walkthrough_rows), "quarantinedIdempotencyRecords": deepcopy(self._quarantined_idempotency_rows), "staleIdempotency": deepcopy(self._stale_idempotency),
            "activeIngestions": deepcopy(self._active_ingestions),
            "activeGenerations": deepcopy(self._active_generations),
            "counters": {
                "project": self._project_counter,
                "document": self._document_counter,
                "source": self._source_counter,
                "ingestion": self._ingestion_counter,
                "run": self._run_counter,
            },
        }

    def _persist_locked(self) -> None:
        if self.state_path is None:
            return
        payload = {
                "schema": "stage4-local-state-v1",
                "projects": [asdict(project) for project in self.projects.values()],
                "documents": [asdict(document) for document in self.documents.values()],
                "sources": [asdict(source) for source in self.sources.values()],
                "sourceDecisions": [asdict(decision) for decision in self.source_decisions.values()],
                "ingestionRuns": [asdict(run) for run in self.ingestion_runs.values()],
                "walkthroughRuns": [
                    walkthrough_run_to_dict(run) for run in self.walkthrough_runs.values()
                ],
                "quarantinedWalkthroughRuns": deepcopy(self._quarantined_walkthrough_rows),
                "idempotencyRecords": [
                    idempotency_record_to_dict(record) for record in self.idempotency_records.values()
                    if record.status != "PENDING"
                ],
                "quarantinedIdempotencyRecords": deepcopy(self._quarantined_idempotency_rows),
                "ragStore": self.rag_store.to_dict(),
                "counters": {
                    "project": self._project_counter,
                    "document": self._document_counter,
                    "source": self._source_counter,
                    "ingestion": self._ingestion_counter,
                    "run": self._run_counter,
                },
            }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(encoded) > MAX_STAGE4_STATE_BYTES:
            raise OSError("Stage 4 local state exceeds the restore size limit.")
        write_state(self.state_path, payload)

    def create_project(
        self,
        *,
        principal: LocalPrincipal,
        name: str,
        description: str = "",
        default_audience: str = "RECRUITER",
        default_language: str = "en",
        idempotency_key: str | None = None,
    ) -> ProjectRecord:
        return self._idempotent(
            principal=principal,
            endpoint="POST /api/v1/projects",
            scope="project:create",
            idempotency_key=idempotency_key,
            request_checksum=checksum_text(f"{name}\n{description}\n{default_audience}\n{default_language}"),
            create=lambda: self._create_project_once(
                principal=principal,
                name=name,
                description=description,
                default_audience=default_audience,
                default_language=default_language,
            ),
        )

    def _create_project_once(
        self,
        *,
        principal: LocalPrincipal,
        name: str,
        description: str,
        default_audience: str,
        default_language: str,
    ) -> ProjectRecord:
        if not name.strip():
            raise Stage4Error(422, "VALIDATION_ERROR", "Project name is required.")
        if self._project_count_for_tenant(principal=principal) >= MAX_PROJECTS_PER_TENANT:
            raise Stage4Error(429, "RESOURCE_LIMIT_EXCEEDED", "Tenant exceeds the Stage 4 project limit.")
        self._project_counter += 1
        now = _now()
        project = ProjectRecord(
            project_id=f"proj_{self._project_counter:06d}",
            tenant_id=principal.tenant_id,
            owner_id=principal.actor_id,
            name=name.strip(),
            description=description.strip(),
            default_audience=default_audience,
            default_language=default_language,
            created_at=now,
            updated_at=now,
        )
        self.projects[project.project_id] = project
        return project

    def upload_document(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        source_filename: str,
        content_type: str,
        data: bytes,
        idempotency_key: str | None = None,
    ) -> DocumentRecord:
        return self._idempotent(
            principal=principal,
            endpoint="POST /api/v1/projects/{projectId}/knowledge-documents",
            scope=project_id,
            idempotency_key=idempotency_key,
            request_checksum=checksum_text(
                f"{project_id}\n{source_filename}\n{content_type}\n{hashlib.sha256(data).hexdigest()}"
            ),
            create=lambda: self._upload_document_once(
                principal=principal,
                project_id=project_id,
                source_filename=source_filename,
                content_type=content_type,
                data=data,
            ),
        )

    def _upload_document_once(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        source_filename: str,
        content_type: str,
        data: bytes,
    ) -> DocumentRecord:
        self._require_project(principal=principal, project_id=project_id)
        if self._active_document_count(principal=principal, project_id=project_id) >= MAX_ACTIVE_DOCUMENTS_PER_PROJECT:
            raise Stage4Error(413, "PROJECT_DOCUMENT_LIMIT_EXCEEDED", "Project exceeds the Stage 4 document limit.")
        if self._project_corpus_bytes(principal=principal, project_id=project_id) + len(data) > MAX_PROJECT_CORPUS_BYTES:
            raise Stage4Error(413, "PROJECT_CORPUS_TOO_LARGE", "Project exceeds the Stage 4 corpus size limit.")
        safe_filename = sanitize_filename(source_filename)
        suffix = PurePath(safe_filename).suffix.lower()
        normalized_content_type = normalize_content_type(content_type)
        if suffix not in ALLOWED_EXTENSIONS or normalized_content_type != ALLOWED_CONTENT_TYPES_BY_EXTENSION.get(suffix):
            raise Stage4Error(415, "UNSUPPORTED_MEDIA_TYPE", "Only markdown and plain text files are accepted.")
        if len(data) > MAX_UPLOAD_BYTES:
            raise Stage4Error(413, "UPLOAD_TOO_LARGE", "Upload exceeds the Stage 4 size limit.")
        validate_upload_bytes(data)
        text = decode_upload(data)
        if not text.strip():
            raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document is empty.")
        if contains_secret_like_content(text):
            raise Stage4Error(422, "SECRET_LIKE_CONTENT", "Uploaded document contains secret-like content.")
        self._document_counter += 1
        document = DocumentRecord(
            document_id=f"doc_{self._document_counter:06d}",
            tenant_id=principal.tenant_id,
            owner_id=principal.actor_id,
            project_id=project_id,
            source_filename=safe_filename,
            content_type="text/markdown" if suffix == ".md" else "text/plain",
            size_bytes=len(data),
            checksum=checksum_text(text),
            text=text,
        )
        self.documents[document.document_id] = document
        return document

    def submit_curated_source(self, *, principal: LocalPrincipal, project_id: str, source_filename: str, content_type: str, data: bytes, assertions: SourceAssertions, schema_version: str, action: str, idempotency_key: str | None = None, file_sha256: str | None = None, size_bytes: int | None = None) -> CuratedOutcome:
        file_sha256, size_bytes = file_sha256 or hashlib.sha256(data).hexdigest(), size_bytes if size_bytes is not None else len(data)
        projection = {"endpoint": "curated-submit", "schema": schema_version, "tenant": principal.tenant_id, "actor": principal.actor_id, "project": project_id, "filename": source_filename.strip(), "mime": normalize_content_type(content_type), "fileSha256": file_sha256, "fileBytes": size_bytes, "assertions": asdict(assertions), "action": action}
        return self._idempotent(principal=principal, endpoint="POST /api/v1/projects/{projectId}/knowledge-documents", scope=project_id, idempotency_key=idempotency_key, request_checksum=canonical_digest(projection), create=lambda: self._submit_curated_source_once(principal, project_id, source_filename, content_type, data, assertions, schema_version, action, file_sha256, size_bytes, projection))
    def _submit_curated_source_once(self, principal: LocalPrincipal, project_id: str, source_filename: str, content_type: str, data: bytes, assertions: SourceAssertions, schema_version: str, action: str, file_sha256: str, size_bytes: int, projection: Mapping[str, Any]) -> CuratedOutcome:
        self._require_project(principal=principal, project_id=project_id)
        if size_bytes > MAX_UPLOAD_BYTES:
            raise Stage4Error(413, "UPLOAD_FILE_TOO_LARGE", "Curated source file exceeds the size limit.")
        if schema_version != CURATION_SCHEMA_VERSION or action not in {"ACCEPT_FOR_REVIEW", "EXCLUDE"}:
            raise Stage4Error(422, "VALIDATION_ERROR", "Curated source assertions are incomplete or ineligible.")
        filename = sanitize_filename(source_filename)
        suffix, mime = PurePath(filename).suffix.lower(), normalize_content_type(content_type)
        if suffix not in ALLOWED_EXTENSIONS or mime != ALLOWED_CONTENT_TYPES_BY_EXTENSION.get(suffix):
            raise Stage4Error(415, "UNSUPPORTED_MEDIA_TYPE", "Only markdown and plain text files are accepted.")
        validate_upload_bytes(data)
        text = decode_upload(data)
        if not text.strip() or contains_secret_like_content(text) or contains_prompt_injection(text):
            code = "VALIDATION_ERROR" if not text.strip() else "SECRET_LIKE_CONTENT" if contains_secret_like_content(text) else "UNSAFE_DOCUMENT_CONTENT"
            raise Stage4Error(422, code, "Curated source content is not safe to retain.")
        self._source_counter += 1
        source_id, decision_id, now = f"source_{self._source_counter:06d}", f"decision_{self._source_counter:06d}", _now()
        checksum, assertion_hash = file_sha256, assertions_digest(assertions)
        if action == "EXCLUDE" or not allowed_for_review(assertions):
            reason = "CURATOR_EXCLUDED" if action == "EXCLUDE" else "SERVER_POLICY_DENIED"
            decision = SourceDecisionRecord(decision_id, source_id, principal.tenant_id, principal.actor_id, project_id, checksum, assertions.source_version, assertion_hash, server_decision="DENY", action=cast(Any, action), reason=reason, decision_state="EXCLUDED", raw_content_retained=False, created_at=now)
            self.source_decisions[decision_id] = decision
            log_event(event_name="source.decision.excluded", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, source_id=source_id, decision_id=decision_id, decision_state=decision.decision_state, reason=reason)
            return CuratedOutcome("SOURCE_EXCLUDED", None, deepcopy(decision), request_projection=deepcopy(projection))
        source = SourceRecord(source_id, principal.tenant_id, principal.actor_id, project_id, filename, mime, size_bytes, checksum, text, assertions, assertion_hash, created_at=now)
        decision = SourceDecisionRecord(decision_id, source_id, principal.tenant_id, principal.actor_id, project_id, checksum, assertions.source_version, assertion_hash, created_at=now)
        self.sources[source_id], self.source_decisions[decision_id] = source, decision
        log_event(event_name="source.decision.allowed", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, source_id=source_id, decision_id=decision_id, decision_state=decision.decision_state)
        return CuratedOutcome("SOURCE_PENDING_REVIEW", deepcopy(source), deepcopy(decision))
    def approve_document(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        document_id: str,
        idempotency_key: str | None = None,
    ) -> DocumentRecord:
        return self._idempotent(
            principal=principal,
            endpoint="PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval",
            scope=project_id,
            idempotency_key=idempotency_key,
            request_checksum=checksum_text(f"{project_id}\n{document_id}\nAPPROVED"),
            create=lambda: self._approve_document_once(
                principal=principal,
                project_id=project_id,
                document_id=document_id,
            ),
        )

    def _approve_document_once(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        document_id: str,
    ) -> DocumentRecord:
        document = self._require_document(principal=principal, project_id=project_id, document_id=document_id)
        document.approval_status = "APPROVED"
        document.approved_at = _now()
        return document

    def approve_curated_source(self, *, principal: LocalPrincipal, project_id: str, source_id: str, bindings: Mapping[str, str], idempotency_key: str | None) -> CuratedOutcome:
        fingerprint = canonical_digest({"endpoint": "curated-approval", "tenant": principal.tenant_id, "actor": principal.actor_id, "project": project_id, **{key: bindings.get(key) for key in ("curationSchemaVersion", "action", "sourceId", "decisionId", "policyVersion", "sourceVersion", "checksum", "assertionsFingerprint")}})
        try:
            return self._idempotent(principal=principal, endpoint="PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval", scope=project_id, idempotency_key=idempotency_key, request_checksum=fingerprint, create=lambda: self._approve_curated_once(principal, project_id, source_id, bindings))
        except Stage4Error as exc:
            log_event(event_name="source.approval.denied", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, source_id=source_id, status=exc.status_code, code=exc.code)
            raise
    def _approve_curated_once(self, principal: LocalPrincipal, project_id: str, source_id: str, bindings: Mapping[str, str]) -> CuratedOutcome:
        self._require_project(principal=principal, project_id=project_id)
        source, decision = self.sources.get(source_id), self.source_decisions.get(bindings.get("decisionId", ""))
        if source is None or source.project_id != project_id:
            raise Stage4Error(404, "NOT_FOUND", "Curated source not found.")
        if decision is None or (bindings.get("curationSchemaVersion"), bindings.get("action"), bindings.get("sourceId"), bindings.get("policyVersion")) != ("source-curation-v1", "APPROVE", source_id, CURATION_POLICY_VERSION) or not legal_pair(source, decision) or decision.decision_state != "PENDING_REVIEW" or (bindings.get("sourceVersion"), bindings.get("checksum"), bindings.get("assertionsFingerprint")) != (source.assertions.source_version, source.checksum, source.assertions_fingerprint):
            raise Stage4Error(409, "SOURCE_NOT_APPROVABLE", "Curated source bindings or policy are stale.")
        decision.action, decision.reason, decision.decision_state = "APPROVE", "CURATOR_APPROVED_POLICY_VERIFIED", "APPROVED"
        decision.approved_at = _now()
        log_event(event_name="source.approval.completed", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, source_id=source_id, decision_id=decision.decision_id, decision_state=decision.decision_state)
        return CuratedOutcome("SOURCE_APPROVED", deepcopy(source), deepcopy(decision))
    def ingest_documents(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        document_ids: list[str],
        idempotency_key: str | None = None,
    ) -> IngestionRunRecord:
        return self._idempotent(
            principal=principal,
            endpoint="POST /api/v1/projects/{projectId}/ingestion-runs",
            scope=project_id,
            idempotency_key=idempotency_key,
            request_checksum=checksum_text(f"{project_id}\n{','.join(document_ids)}"),
            create=lambda: self._run_with_project_lock(
                active=self._active_ingestions,
                principal=principal,
                project_id=project_id,
                create=lambda: self._ingest_documents_once(
                    principal=principal,
                    project_id=project_id,
                    document_ids=document_ids,
                ),
            ),
        )
    def ingest_curated_sources(self, *, principal: LocalPrincipal, project_id: str, source_ids: list[str], idempotency_key: str | None) -> IngestionRunRecord:
        return self._idempotent(principal=principal, endpoint="POST /api/v1/projects/{projectId}/ingestion-runs", scope=project_id, idempotency_key=idempotency_key, request_checksum=canonical_digest({"project": project_id, "sourceIds": source_ids}), create=lambda: self._ingest_curated_once(principal, project_id, source_ids))
    def _ingest_curated_once(self, principal: LocalPrincipal, project_id: str, source_ids: list[str]) -> IngestionRunRecord:
        self._require_project(principal=principal, project_id=project_id)
        if not source_ids or len(source_ids) > MAX_DOCUMENTS_PER_INGESTION or len(source_ids) != len(set(source_ids)):
            raise Stage4Error(422, "SOURCE_NOT_INGESTIBLE", "At least one bounded curated source is required.")
        prepared: list[tuple[SourceRecord, list[KnowledgeChunk]]] = []
        for source_id in source_ids:
            if source_id in self.documents:
                raise Stage4Error(422, "SOURCE_KIND_MISMATCH", "Legacy documents cannot use curated ingestion.")
            source = self.sources.get(source_id)
            decision = next((value for value in self.source_decisions.values() if value.source_id == source_id), None)
            if source is None or (source.tenant_id, source.owner_id, source.project_id) != (principal.tenant_id, principal.actor_id, project_id) or decision is None or not legal_pair(source, decision) or decision.decision_state != "APPROVED" or source.ingestion_status != "NOT_STARTED":
                raise Stage4Error(422, "SOURCE_NOT_INGESTIBLE", "Every curated source must be approved and current.")
            text = parse_document_text(source.text)
            if contains_prompt_injection(text):
                raise Stage4Error(422, "UNSAFE_DOCUMENT_CONTENT", "Curated source contains unsafe content.")
            chunks = chunk_document(document_id=source_id, project_id=project_id, tenant_id=principal.tenant_id, source_filename=source.source_filename, text=text, source_document_checksum=source.checksum, approved_at=decision.approved_at or decision.created_at, max_chunks=MAX_CHUNKS_PER_DOCUMENT)
            prepared.append((source, chunks))
        chunks = [chunk for _source, values in prepared for chunk in values]
        if self.rag_store.chunk_count_for_project(tenant_id=principal.tenant_id, project_id=project_id) + len(chunks) > MAX_CHUNKS_PER_PROJECT:
            raise Stage4Error(413, "PROJECT_CORPUS_TOO_LARGE", "Project exceeds the Stage 4 chunk limit.")
        stored, now = self.rag_store.add_chunks(chunks, self.embedder), _now()
        for source, _chunks in prepared:
            source.ingestion_status, source.ingested_at = "INGESTED", now
        self._ingestion_counter += 1
        run = IngestionRunRecord(f"ing_{self._ingestion_counter:06d}", principal.tenant_id, principal.actor_id, project_id, [], "COMPLETED", len(stored), len(stored), now, source_ids)
        self.ingestion_runs[run.ingestion_run_id] = run
        log_event(event_name="source.ingestion.completed", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, ingestion_run_id=run.ingestion_run_id, source_count=len(source_ids), chunk_count=len(stored))
        return run
    def curation_summary(self, *, principal: LocalPrincipal, project_id: str) -> dict[str, Any]:
        try:
            project = self._require_project(principal=principal, project_id=project_id)
        except Stage4Error as exc:
            log_event(event_name="source.summary.denied", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, status=exc.status_code, code=exc.code)
            raise
        by_source = {decision.source_id: decision for decision in self.source_decisions.values()}
        curated = []
        for source in sorted(self.sources.values(), key=lambda value: value.source_id):
            decision = by_source.get(source.source_id)
            if (source.tenant_id, source.owner_id, source.project_id) != (principal.tenant_id, principal.actor_id, project_id) or decision is None or not legal_pair(source, decision):
                continue
            chunks = sorted((chunk for chunk in self.rag_store.chunks_for_project(tenant_id=principal.tenant_id, project_id=project_id) if chunk.document_id == source.source_id), key=lambda value: value.chunk_id)
            curated.append({"sourceId": source.source_id, "decisionId": decision.decision_id, "checksum": source.checksum, "sourceVersion": decision.source_version, "assertionsFingerprint": decision.assertions_fingerprint, "policyVersion": decision.policy_version, "serverDecision": decision.server_decision, "decisionState": decision.decision_state, "ingestionStatus": source.ingestion_status, "acceptedChunks": [{"chunkId": chunk.chunk_id, "checksum": chunk.checksum} for chunk in chunks]})
        excluded = [
            {"sourceId": decision.source_id, "decisionId": decision.decision_id, "checksum": decision.checksum, "sourceVersion": decision.source_version, "assertionsFingerprint": decision.assertions_fingerprint, "policyVersion": decision.policy_version, "serverDecision": decision.server_decision, "decisionState": decision.decision_state, "reason": decision.reason, "rawContentRetained": decision.raw_content_retained, "createdAt": decision.created_at}
            for decision in sorted(self.source_decisions.values(), key=lambda value: value.source_id)
            if (decision.tenant_id, decision.actor_id, decision.project_id) == (principal.tenant_id, principal.actor_id, project_id) and legal_exclusion(decision) and decision.source_id not in self.sources
        ]
        legacy = [
            {"documentId": document.document_id, "checksum": document.checksum, "approvalStatus": document.approval_status, "ingestionStatus": document.ingestion_status, "sourceKind": "UNSEALED_LEGACY"}
            for document in sorted(self.documents.values(), key=lambda value: value.document_id)
            if document.project_id == project_id and (document.tenant_id, document.owner_id) == (principal.tenant_id, principal.actor_id)
        ]
        log_event(event_name="source.summary.read", tenant_id=principal.tenant_id, actor_id=principal.actor_id, project_id=project_id, curated_count=len(curated), excluded_count=len(excluded), legacy_count=len(legacy))
        return {"schema": "source-curation-summary-v1", "tenantId": project.tenant_id, "ownerId": project.owner_id, "projectId": project.project_id, "curatedSources": curated, "excludedDecisions": excluded, "legacySources": legacy}
    def _ingest_documents_once(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        document_ids: list[str],
    ) -> IngestionRunRecord:
        self._require_project(principal=principal, project_id=project_id)
        if not document_ids:
            raise Stage4Error(422, "VALIDATION_ERROR", "At least one document is required.")
        if len(document_ids) > MAX_DOCUMENTS_PER_INGESTION:
            raise Stage4Error(413, "INGESTION_TOO_LARGE", "Too many documents requested for one ingestion run.")
        prepared_documents: list[tuple[DocumentRecord, list[KnowledgeChunk]]] = []
        pending_chunk_count = 0
        existing_chunk_count = self.rag_store.chunk_count_for_project(
            tenant_id=principal.tenant_id,
            project_id=project_id,
        )
        for document_id in document_ids:
            document = self._require_document(principal=principal, project_id=project_id, document_id=document_id)
            if document.approval_status != "APPROVED":
                raise Stage4Error(422, "DOCUMENT_NOT_APPROVED", "Document must be approved before ingestion.")
            parsed_text = parse_document_text(document.text)
            if contains_prompt_injection(parsed_text):
                raise Stage4Error(422, "UNSAFE_DOCUMENT_CONTENT", "Document contains unsafe instruction-like content.")
            try:
                chunks = chunk_document(
                    document_id=document.document_id,
                    project_id=project_id,
                    tenant_id=principal.tenant_id,
                    source_filename=document.source_filename,
                    text=parsed_text,
                    source_document_checksum=document.checksum,
                    approved_at=document.approved_at or document.created_at,
                    max_chunks=MAX_CHUNKS_PER_DOCUMENT,
                )
            except ValueError as exc:
                raise Stage4Error(413, "DOCUMENT_TOO_LARGE", "Document exceeds the Stage 4 chunk limit.") from exc
            if existing_chunk_count + pending_chunk_count + len(chunks) > MAX_CHUNKS_PER_PROJECT:
                raise Stage4Error(413, "PROJECT_CORPUS_TOO_LARGE", "Project exceeds the Stage 4 chunk limit.")
            pending_chunk_count += len(chunks)
            prepared_documents.append((document, chunks))

        all_chunks = [chunk for _document, chunks in prepared_documents for chunk in chunks]
        stored_chunks = self.rag_store.add_chunks(all_chunks, self.embedder)
        for document, _chunks in prepared_documents:
            document.ingestion_status = "INGESTED"
            document.ingested_at = _now()
        self._ingestion_counter += 1
        run = IngestionRunRecord(
            ingestion_run_id=f"ing_{self._ingestion_counter:06d}",
            tenant_id=principal.tenant_id,
            actor_id=principal.actor_id,
            project_id=project_id,
            document_ids=document_ids,
            status="COMPLETED",
            chunk_count=len(stored_chunks),
            embedding_count=len(stored_chunks),
            created_at=_now(),
        )
        self.ingestion_runs[run.ingestion_run_id] = run
        return run

    def generate_walkthrough(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        audience: str,
        requested_language: str,
        depth: str,
        style: str,
        prompt: str,
        idempotency_key: str | None = None,
    ) -> WalkthroughRunRecord:
        return self._idempotent(
            principal=principal,
            endpoint="POST /api/v1/projects/{projectId}/walkthrough-runs",
            scope=project_id,
            idempotency_key=idempotency_key,
            request_checksum=checksum_text(f"{project_id}\n{audience}\n{requested_language}\n{depth}\n{style}\n{prompt}"),
            create=lambda: self._run_with_project_lock(
                active=self._active_generations,
                principal=principal,
                project_id=project_id,
                create=lambda: self._generate_walkthrough_once(
                    principal=principal,
                    project_id=project_id,
                    audience=audience,
                    requested_language=requested_language,
                    depth=depth,
                    style=style,
                    prompt=prompt,
                ),
            ),
        )

    def _generate_walkthrough_once(
        self,
        *,
        principal: LocalPrincipal,
        project_id: str,
        audience: str,
        requested_language: str,
        depth: str,
        style: str,
        prompt: str,
    ) -> WalkthroughRunRecord:
        project = self._require_project(principal=principal, project_id=project_id)
        if len(prompt) > MAX_PROMPT_CHARS:
            raise Stage4Error(413, "PROMPT_TOO_LARGE", "Prompt exceeds the Stage 4 limit.")
        if contains_secret_like_content(prompt):
            raise Stage4Error(422, "SECRET_LIKE_CONTENT", "Prompt contains secret-like content.")
        if self._run_count_for_project(principal=principal, project_id=project_id) >= MAX_RUNS_PER_PROJECT:
            raise Stage4Error(429, "RESOURCE_LIMIT_EXCEEDED", "Project exceeds the Stage 4 generation run limit.")

        self._run_counter += 1
        run_id = f"run_{self._run_counter:06d}"
        started_at_ms = time.perf_counter()
        run_started_at = _now()

        with with_trace(
            scope="narratwin.walkthrough",
            name="walkthrough-generation",
            attributes={
                "run_id": run_id,
                "project_id": project_id,
                "tenant_id": principal.tenant_id,
                "audience": audience,
                "requested_language": requested_language,
                "depth": depth,
                "style": style,
            },
        ) as trace_id:
            log_event(
                event_name="walkthrough.run.started",
                run_id=run_id,
                tenant_id=principal.tenant_id,
                actor_id=principal.actor_id,
                project_id=project_id,
                trace_id=trace_id,
                prompt_signature=checksum_text(prompt),
                audience=audience,
                requested_language=requested_language,
                depth=depth,
                style=style,
            )
            with langfuse_observation(
                name="walkthrough.run",
                trace_id=trace_id,
                run_id=run_id,
                metadata={
                    "tenant_id": principal.tenant_id,
                    "project_id": project_id,
                    "audience": audience,
                    "requested_language": requested_language,
                    "depth": depth,
                    "style": style,
                },
            ) as lf_metadata:
                if contains_prompt_injection(prompt):
                    run = self._build_walkthrough_run(
                        run_id=run_id,
                        principal=principal,
                        project_id=project_id,
                        status="REFUSED",
                        failure_reason=self.WALKTHROUGH_REFUSAL_REASON_PROMPT_INJECTION,
                        evaluation_status=None,
                        trace_id=trace_id,
                        started_at=run_started_at,
                        latency_ms=self._elapsed_ms(started_at_ms, time.perf_counter()),
                        audience=audience,
                        requested_language=requested_language,
                        depth=depth,
                        style=style,
                        accepted_script_text=None,
                        generated_script=None,
                        retrieved_context=[],
                        evaluation=None,
                        log_metadata={
                            "run_status": "refused",
                            "failure_reason": self.WALKTHROUGH_REFUSAL_REASON_PROMPT_INJECTION,
                        },
                        lf_metadata=lf_metadata,
                    )
                else:
                    retrieval_query = (
                        f"{project.name} {project.description} {audience} "
                        f"{audience_label_for_script(audience)} {prompt}"
                    )
                    retrieved = retrieve_context(
                        store=self.rag_store,
                        embedder=self.embedder,
                        tenant_id=principal.tenant_id,
                        project_id=project_id,
                        query=retrieval_query,
                        top_k=RETRIEVAL_TOP_K,
                        min_score=RETRIEVAL_MIN_SCORE,
                    )
                    all_chunks = self.rag_store.chunks_for_project(
                        tenant_id=principal.tenant_id,
                        project_id=project_id,
                    )
                    if not retrieved:
                        run = self._build_walkthrough_run(
                            run_id=run_id,
                            principal=principal,
                            project_id=project_id,
                            status="REFUSED",
                            failure_reason=self.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL,
                            evaluation_status=None,
                            trace_id=trace_id,
                            started_at=run_started_at,
                            latency_ms=self._elapsed_ms(started_at_ms, time.perf_counter()),
                            audience=audience,
                            requested_language=requested_language,
                            depth=depth,
                            style=style,
                            accepted_script_text=None,
                            generated_script=None,
                            retrieved_context=[],
                            evaluation=None,
                            log_metadata={
                                "run_status": "refused",
                                "failure_reason": self.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL,
                            },
                        )
                    elif any(contains_prompt_injection(context.chunk.text) for context in retrieved):
                        run = self._build_walkthrough_run(
                            run_id=run_id,
                            principal=principal,
                            project_id=project_id,
                            status="REFUSED",
                            failure_reason=self.WALKTHROUGH_REFUSAL_REASON_UNSAFE_CONTEXT,
                            evaluation_status=None,
                            trace_id=trace_id,
                            started_at=run_started_at,
                            latency_ms=self._elapsed_ms(started_at_ms, time.perf_counter()),
                            audience=audience,
                            requested_language=requested_language,
                            depth=depth,
                            style=style,
                            accepted_script_text=None,
                            generated_script=None,
                            retrieved_context=[],
                            evaluation=None,
                            log_metadata={
                                "run_status": "refused",
                                "failure_reason": self.WALKTHROUGH_REFUSAL_REASON_UNSAFE_CONTEXT,
                            },
                        )
                    else:
                        generated = self.llm.generate_script(
                            audience=audience,
                            prompt=prompt,
                            retrieved_context=retrieved,
                        )
                        if not generated_script_is_bounded(generated):
                            raise Stage4Error(422, "GENERATED_SCRIPT_TOO_LARGE", "Generated script exceeds the Stage 4 limit.")
                        evaluation = evaluate_grounding(
                            tenant_id=principal.tenant_id,
                            project_id=project_id,
                            run_id=run_id,
                            candidate=generated,
                            retrieved_context=retrieved,
                            prompt=prompt,
                            all_chunks=all_chunks,
                        )
                        evaluation = replace(evaluation, retrieval_strategy_version=RETRIEVAL_STRATEGY_VERSION, retrieval_top_k=RETRIEVAL_TOP_K, retrieval_score_threshold=RETRIEVAL_MIN_SCORE)
                        input_tokens, output_tokens = evaluate_token_usage(
                            prompt=prompt,
                            retrieved_context=retrieved,
                            candidate_text=generated.text,
                        )
                        estimated_cost = estimate_cost_usd(
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )
                        run_status: WalkthroughRunStatus = (
                            "COMPLETED" if evaluation.evaluation_status == "PASSED" else "FAILED"
                        )
                        run = self._build_walkthrough_run(
                            run_id=run_id,
                            principal=principal,
                            project_id=project_id,
                            status=run_status,
                            failure_reason=self.WALKTHROUGH_REFUSAL_REASON_UNSUPPORTED_FACT
                            if run_status == "FAILED"
                            else None,
                            evaluation_status=evaluation.evaluation_status,
                            trace_id=trace_id,
                            started_at=run_started_at,
                            latency_ms=self._elapsed_ms(started_at_ms, time.perf_counter()),
                            audience=audience,
                            requested_language=requested_language,
                            depth=depth,
                            style=style,
                            accepted_script_text=generated.text if evaluation.evaluation_status == "PASSED" else None,
                            generated_script=generated,
                            retrieved_context=retrieved,
                            evaluation=evaluation,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            estimated_cost=estimated_cost,
                            log_metadata={
                                "run_status": run_status,
                                "evaluation_status": evaluation.evaluation_status,
                                "groundedness_score": evaluation.groundedness_score,
                                "unsupported_claims": evaluation.unsupported_claim_count,
                            },
                        )

        self.walkthrough_runs[run_id] = run
        return run

    def _build_walkthrough_run(
        self,
        *,
        run_id: str,
        principal: LocalPrincipal,
        project_id: str,
        status: WalkthroughRunStatus,
        failure_reason: str | None,
        evaluation_status: Literal["PASSED", "FAILED"] | None,
        trace_id: str,
        started_at: str,
        latency_ms: int,
        audience: str,
        requested_language: str,
        depth: str,
        style: str,
        accepted_script_text: str | None,
        generated_script: GeneratedScript | None,
        retrieved_context: list[RetrievedContext],
        evaluation: EvaluationResult | None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost: float = 0.0,
        log_metadata: dict[str, object] | None = None,
        lf_metadata: dict[str, object] | None = None,
    ) -> WalkthroughRunRecord:
        if evaluation is None and status == "FAILED":
            # Keep failure status semantics stable while still returning structured output.
            failure_reason = failure_reason or self.WALKTHROUGH_REFUSAL_REASON_UNSUPPORTED_FACT

        if input_tokens == 0 and output_tokens == 0 and accepted_script_text:
            input_tokens, output_tokens = evaluate_token_usage(
                prompt="",
                retrieved_context=retrieved_context,
                candidate_text=accepted_script_text,
            )
        if estimated_cost == 0.0 and (input_tokens or output_tokens):
            estimated_cost = estimate_cost_usd(input_tokens=input_tokens, output_tokens=output_tokens)

        if latency_ms < 0:
            latency_ms = 0

        run = WalkthroughRunRecord(
            run_id=run_id,
            tenant_id=principal.tenant_id,
            actor_id=principal.actor_id,
            project_id=project_id,
            status=status,
            failure_reason=failure_reason,
            evaluation_status=evaluation_status,
            trace_id=trace_id,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            audience=audience,
            requested_language=requested_language,
            depth=depth,
            style=style,
            accepted_script_text=accepted_script_text,
            generated_script=generated_script,
            retrieved_context=retrieved_context,
            evaluation=evaluation,
            created_at=started_at,
            retrieval_strategy_version=RETRIEVAL_STRATEGY_VERSION,
            retrieval_top_k=RETRIEVAL_TOP_K,
            retrieval_score_threshold=RETRIEVAL_MIN_SCORE,
        )
        if (
            not raw_walkthrough_lineage_is_bounded_and_typed(walkthrough_run_to_dict(run))
            or not self._restored_retrieval_lineage_is_current(walkthrough_run_to_dict(run), run)
            or not self._fresh_lineage_ownership_is_valid(run)
            or not self._restored_citation_lineage_is_valid(run)
        ):
            raise Stage4Error(422, "GENERATED_SCRIPT_TOO_LARGE", "Generated script exceeds the Stage 4 limit.")
        record_walkthrough_metrics(
            tenant_id=principal.tenant_id,
            run_id=run_id,
            status=status,
            evaluation_status=evaluation_status,
            reason_code=failure_reason,
            latency_ms=latency_ms,
            token_usage={
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "totalTokens": input_tokens + output_tokens,
            },
            estimated_cost=estimated_cost,
        )
        self.walkthrough_runs[run_id] = run

        safe_metadata = dict(log_metadata or {})
        for reserved in {
            "run_id",
            "status",
            "tenant_id",
            "project_id",
            "trace_id",
            "failure_reason",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "estimated_cost",
            "evaluation_status",
        }:
            safe_metadata.pop(reserved, None)
        safe_metadata.pop("event", None)
        log_event(
            event_name="walkthrough.run.completed",
            run_id=run_id,
            status=status,
            tenant_id=principal.tenant_id,
            project_id=project_id,
            trace_id=trace_id,
            failure_reason=failure_reason or "",
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            evaluation_status=evaluation_status or "",
            lf_metadata_keys=list((lf_metadata or {}).keys()),
            **safe_metadata,
        )
        return run

    def _elapsed_ms(self, started_at: float, ended_at: float) -> int:
        return int((ended_at - started_at) * 1000)

    def _require_project(self, *, principal: LocalPrincipal, project_id: str) -> ProjectRecord:
        project = self.projects.get(project_id)
        if project is None:
            raise Stage4Error(404, "NOT_FOUND", "Project not found.")
        if project.tenant_id != principal.tenant_id or project.owner_id != principal.actor_id:
            raise Stage4Error(403, "FORBIDDEN", "Project is not accessible to this principal.")
        return project

    def _require_document(self, *, principal: LocalPrincipal, project_id: str, document_id: str) -> DocumentRecord:
        self._require_project(principal=principal, project_id=project_id)
        document = self.documents.get(document_id)
        if document is None or document.project_id != project_id:
            raise Stage4Error(404, "NOT_FOUND", "Knowledge document not found.")
        if document.tenant_id != principal.tenant_id or document.owner_id != principal.actor_id:
            raise Stage4Error(403, "FORBIDDEN", "Document is not accessible to this principal.")
        return document

    def _idempotent(
        self,
        *,
        principal: LocalPrincipal,
        endpoint: str,
        scope: str,
        idempotency_key: str | None,
        request_checksum: str,
        create: Callable[[], T],
    ) -> T:
        if not idempotency_key:
            raise Stage4Error(400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required for write requests.")
        record_key = (principal.tenant_id, principal.actor_id, scope, endpoint, idempotency_key)
        with self._operation_lock:
            existing = self.idempotency_records.get(record_key)
            if existing is not None:
                if existing.request_checksum != request_checksum:
                    raise Stage4Error(409, "IDEMPOTENCY_CONFLICT", "Idempotency key was reused with a different request.")
                if existing.status == "PENDING":
                    raise Stage4Error(409, "IDEMPOTENCY_IN_PROGRESS", "Idempotency key is already in progress.")
                if existing.status == "FAILED":
                    raise cast(Stage4Error, existing.value)
                if isinstance(existing.value, CuratedOutcome):
                    return cast(T, replace(existing.value, idempotency_replayed=True))
                return cast(T, existing.value)
            stale_checksum = self._stale_idempotency.get(record_key)
            if stale_checksum is not None:
                if stale_checksum != request_checksum:
                    raise Stage4Error(409, "IDEMPOTENCY_CONFLICT", "Idempotency key was reused with a different request.")
                raise Stage4Error(409, "STALE_RETRIEVAL_LINEAGE", "Stored walkthrough cannot be replayed because its retrieval lineage is stale or unavailable.")
            if self._idempotency_count_for_tenant(principal=principal) >= MAX_IDEMPOTENCY_RECORDS_PER_TENANT:
                raise Stage4Error(429, "RESOURCE_LIMIT_EXCEEDED", "Tenant exceeds the Stage 4 idempotency record limit.")
            now = _now()
            record_id = "idem_" + hashlib.sha256(
                f"{principal.tenant_id}:{principal.actor_id}:{scope}:{endpoint}:{idempotency_key}".encode()
            ).hexdigest()[:16]
            pending = IdempotencyRecord(
                idempotency_record_id=record_id,
                tenant_id=principal.tenant_id,
                actor_id=principal.actor_id,
                idempotency_scope=scope,
                endpoint=endpoint,
                idempotency_key=idempotency_key,
                request_checksum=request_checksum,
                status="PENDING",
                value=None,
                created_at=now,
                updated_at=now,
            )
            snapshot = self._runtime_snapshot_locked()
            self.idempotency_records[record_key] = pending
        try:
            with self._operation_lock:
                value = create()
                if isinstance(value, WalkthroughRunRecord):
                    value.request_checksum = request_checksum
        except Stage4Error as exc:
            with self._operation_lock:
                pending.status = "FAILED"
                pending.value = exc
                pending.updated_at = _now()
                try:
                    self._persist_locked()
                except OSError:
                    self._restore_failed_operation_locked(snapshot, record_key=record_key, value=None)
                    raise exc
            raise
        except Exception:
            with self._operation_lock:
                self._restore_failed_operation_locked(snapshot, record_key=record_key, value=None)
                self._persist_locked()
            raise
        with self._operation_lock:
            pending.status = "COMPLETED"
            pending.value = value
            pending.updated_at = _now()
            try:
                self._persist_locked()
            except OSError:
                self._restore_failed_operation_locked(snapshot, record_key=record_key, value=value)
                raise
        return value

    def _project_count_for_tenant(self, *, principal: LocalPrincipal) -> int:
        return sum(1 for project in self.projects.values() if project.tenant_id == principal.tenant_id)

    def _run_count_for_project(self, *, principal: LocalPrincipal, project_id: str) -> int:
        return sum(
            1
            for run in self.walkthrough_runs.values()
            if run.tenant_id == principal.tenant_id
            and run.actor_id == principal.actor_id
            and run.project_id == project_id
        )

    def _idempotency_count_for_tenant(self, *, principal: LocalPrincipal) -> int:
        return sum(
            1
            for record in self.idempotency_records.values()
            if record.tenant_id == principal.tenant_id and record.actor_id == principal.actor_id
        )

    def _active_document_count(self, *, principal: LocalPrincipal, project_id: str) -> int:
        return sum(
            1
            for document in self.documents.values()
            if document.tenant_id == principal.tenant_id
            and document.owner_id == principal.actor_id
            and document.project_id == project_id
        )

    def _project_corpus_bytes(self, *, principal: LocalPrincipal, project_id: str) -> int:
        return sum(
            document.size_bytes
            for document in self.documents.values()
            if document.tenant_id == principal.tenant_id
            and document.owner_id == principal.actor_id
            and document.project_id == project_id
        )

    def _run_with_project_lock(
        self,
        *,
        active: set[tuple[str, str]],
        principal: LocalPrincipal,
        project_id: str,
        create: Callable[[], T],
    ) -> T:
        lock_key = (principal.tenant_id, project_id)
        with self._operation_lock:
            if lock_key in active:
                raise Stage4Error(429, "BACKPRESSURE_QUEUE_FULL", "Another Stage 4 operation is already active for this project.")
            active.add(lock_key)
        try:
            return create()
        finally:
            with self._operation_lock:
                active.remove(lock_key)


def walkthrough_run_to_dict(run: WalkthroughRunRecord) -> dict[str, Any]:
    return {
        **asdict(run),
        "generated_script": asdict(run.generated_script) if run.generated_script is not None else None,
        "retrieved_context": [retrieved_context_to_dict(context) for context in run.retrieved_context],
        "evaluation": asdict(run.evaluation) if run.evaluation is not None else None,
    }


def walkthrough_run_from_dict(row: dict[str, Any]) -> WalkthroughRunRecord:
    payload = dict(row)
    generated_script = payload.pop("generated_script", None)
    retrieved_context = payload.pop("retrieved_context", [])
    evaluation = payload.pop("evaluation", None)
    return WalkthroughRunRecord(
        **payload,
        generated_script=generated_script_from_dict(generated_script) if isinstance(generated_script, dict) else None,
        retrieved_context=[
            retrieved_context_from_dict(context)
            for context in retrieved_context
            if isinstance(context, dict)
        ],
        evaluation=evaluation_from_dict(evaluation) if isinstance(evaluation, dict) else None,
    )


def retrieved_context_to_dict(context: RetrievedContext) -> dict[str, Any]:
    return {"context_ref_id": context.context_ref_id, "chunk": knowledge_chunk_to_dict(context.chunk), "score": context.score}


def retrieved_context_from_dict(row: dict[str, Any]) -> RetrievedContext:
    return RetrievedContext(
        context_ref_id=str(row["context_ref_id"]),
        chunk=knowledge_chunk_from_dict(cast(dict[str, Any], row["chunk"])),
        score=float(row["score"]),
    )


def knowledge_chunk_to_dict(chunk: KnowledgeChunk) -> dict[str, Any]:
    return asdict(chunk)


def knowledge_chunk_from_dict(row: dict[str, Any]) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=str(row["chunk_id"]),
        tenant_id=str(row["tenant_id"]),
        project_id=str(row["project_id"]),
        document_id=str(row["document_id"]),
        source_filename=str(row["source_filename"]),
        source_document_checksum=str(row["source_document_checksum"]),
        approved_at=str(row["approved_at"]),
        chunk_index=int(row["chunk_index"]),
        text=str(row["text"]),
        token_count=int(row["token_count"]),
        checksum=str(row["checksum"]),
        heading_path=[str(part) for part in row.get("heading_path", [])],
        line_start=int(row["line_start"]),
        line_end=int(row["line_end"]),
        embedding=tuple(float(value) for value in row.get("embedding", ())),
    )


def _raw_strings(row: dict[str, Any], names: tuple[str, ...]) -> bool:
    return all(type(row.get(name)) is str for name in names)


def _raw_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(float(cast(int | float, value)))


def generated_script_is_bounded(candidate: object) -> bool:
    if not isinstance(candidate, GeneratedScript) or type(candidate.text) is not str:
        return False
    if len(candidate.text) > MAX_RESTORED_SCRIPT_CHARS or len(candidate.claims) > MAX_RESTORED_LINEAGE_ITEMS:
        return False
    return all(len(marker) <= MAX_RESTORED_CITATION_DIGITS for marker in re.findall(r"\[(\d+)\]", candidate.text))


def raw_walkthrough_lineage_is_bounded_and_typed(row: dict[str, Any]) -> bool:
    """Reject active coercible lineage; legacy retrieval scores may only reach inactive quarantine."""
    status = row.get("status")
    if status == "REFUSED":
        return row.get("generated_script") is None and row.get("evaluation") is None
    if status not in {"COMPLETED", "FAILED"}:
        return False
    script, evaluation, contexts = row.get("generated_script"), row.get("evaluation"), row.get("retrieved_context")
    if not isinstance(script, dict) or not isinstance(evaluation, dict) or not isinstance(contexts, list):
        return False
    text, claims = script.get("text"), script.get("claims")
    if type(text) is not str or not 0 < len(text) <= MAX_RESTORED_SCRIPT_CHARS or not isinstance(claims, list):
        return False
    if len(claims) > MAX_RESTORED_LINEAGE_ITEMS or len(contexts) > RETRIEVAL_TOP_K:
        return False
    markers = re.findall(r"\[(\d+)\]", text)
    if any(len(marker) > MAX_RESTORED_CITATION_DIGITS for marker in markers):
        return False
    for claim in claims:
        if not isinstance(claim, dict) or not _raw_strings(claim, ("claim_id", "text")):
            return False
        if type(claim.get("citation_index")) is not int or type(claim.get("script_span_start")) is not int or type(claim.get("script_span_end")) is not int:
            return False
        if claim.get("chunk_id") is not None and type(claim.get("chunk_id")) is not str:
            return False
    for context in contexts:
        if not isinstance(context, dict) or type(context.get("context_ref_id")) is not str:
            return False
        score = context.get("score")
        if not isinstance(score, (int, float)) and not (type(score) is str and len(score) <= 32):
            return False
        chunk = context.get("chunk")
        if not isinstance(chunk, dict) or not _raw_strings(chunk, ("chunk_id", "tenant_id", "project_id", "document_id")):
            return False
    supports, unsupported = evaluation.get("claim_supports"), evaluation.get("unsupported_claims")
    if not isinstance(supports, list) or not isinstance(unsupported, list):
        return False
    if len(supports) > MAX_RESTORED_LINEAGE_ITEMS or len(unsupported) > MAX_RESTORED_LINEAGE_ITEMS:
        return False
    if type(evaluation.get("unsupported_claim_count")) is not int or evaluation.get("unsupported_claim_count") != len(unsupported):
        return False
    if evaluation.get("evaluation_status") not in {"PASSED", "FAILED"}:
        return False
    metric_names = ("groundedness_score", "faithfulness_score", "answer_relevancy", "context_precision", "context_recall", "context_ref_coverage")
    if not all(_raw_number(evaluation.get(name)) for name in metric_names):
        return False
    for support in supports:
        if not isinstance(support, dict) or not _raw_strings(support, ("claim_support_id", "claim_id", "context_ref_id", "chunk_id", "document_id", "support_reason")):
            return False
        if support.get("support_status") != "SUPPORTED" or type(support.get("citation_index")) is not int or not _raw_number(support.get("support_score")):
            return False
    return all(isinstance(claim, dict) and _raw_strings(claim, ("claim_id", "claim_text", "reason")) for claim in unsupported)


def generated_script_from_dict(row: dict[str, Any]) -> GeneratedScript:
    return GeneratedScript(
        text=str(row["text"]),
        claims=[
            ScriptClaim(
                claim_id=str(claim["claim_id"]),
                text=str(claim["text"]),
                citation_index=int(claim["citation_index"]),
                chunk_id=str(claim["chunk_id"]) if claim.get("chunk_id") is not None else None,
                script_span_start=int(claim["script_span_start"]),
                script_span_end=int(claim["script_span_end"]),
            )
            for claim in row.get("claims", [])
            if isinstance(claim, dict)
        ],
    )


def evaluation_from_dict(row: dict[str, Any]) -> EvaluationResult:
    for field_name in ("groundedness_score", "faithfulness_score", "answer_relevancy", "context_precision", "context_recall", "context_ref_coverage"):
        if type(row.get(field_name)) is bool:
            raise TypeError("Evaluation metrics must not be boolean.")
    return EvaluationResult(
        evaluation_id=str(row["evaluation_id"]),
        run_id=str(row["run_id"]),
        tenant_id=str(row["tenant_id"]),
        project_id=str(row["project_id"]),
        evaluation_status=cast(Literal["PASSED", "FAILED"], row["evaluation_status"]),
        groundedness_score=float(row["groundedness_score"]),
        faithfulness_score=float(row["faithfulness_score"]),
        answer_relevancy=float(row["answer_relevancy"]),
        context_precision=float(row["context_precision"]),
        context_recall=float(row["context_recall"]),
        unsupported_claim_count=int(row["unsupported_claim_count"]),
        unsupported_claims=[
            UnsupportedClaim(
                claim_id=str(claim["claim_id"]),
                claim_text=str(claim["claim_text"]),
                reason=str(claim["reason"]),
            )
            for claim in row.get("unsupported_claims", [])
            if isinstance(claim, dict)
        ],
        claim_supports=[
            ClaimSupport(
                claim_support_id=str(support["claim_support_id"]),
                claim_id=str(support["claim_id"]),
                context_ref_id=str(support["context_ref_id"]),
                chunk_id=str(support["chunk_id"]),
                document_id=str(support["document_id"]),
                support_status=cast(Literal["SUPPORTED"], support["support_status"]),
                support_score=float(support["support_score"]),
                support_reason=str(support["support_reason"]),
                citation_index=int(support["citation_index"]),
            )
            for support in row.get("claim_supports", [])
            if isinstance(support, dict)
        ],
        context_ref_coverage=float(row["context_ref_coverage"]),
        policy_version=str(row["policy_version"]),
        schema_version=str(row["schema_version"]),
        safety_policy_version=str(row["safety_policy_version"]),
        retrieval_strategy_version=row.get("retrieval_strategy_version"), retrieval_top_k=row.get("retrieval_top_k"), retrieval_score_threshold=row.get("retrieval_score_threshold"),
    )


def idempotency_record_to_dict(record: IdempotencyRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "idempotency_record_id": record.idempotency_record_id,
        "tenant_id": record.tenant_id,
        "actor_id": record.actor_id,
        "idempotency_scope": record.idempotency_scope,
        "endpoint": record.endpoint,
        "idempotency_key": record.idempotency_key,
        "request_checksum": record.request_checksum,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    value = record.value
    if isinstance(value, Stage4Error):
        row["value"] = {"kind": "error", "status_code": value.status_code, "code": value.code, "message": value.message, "binding": [record.tenant_id, record.actor_id, record.idempotency_scope, record.endpoint, record.request_checksum]}
    elif isinstance(value, ProjectRecord):
        row["value"] = {"kind": "project", "id": value.project_id}
    elif isinstance(value, DocumentRecord):
        row["value"] = {"kind": "document", "id": value.document_id}
    elif isinstance(value, IngestionRunRecord):
        row["value"] = {"kind": "ingestion", "id": value.ingestion_run_id}
    elif isinstance(value, WalkthroughRunRecord):
        row["value"] = {"kind": "walkthrough", "id": value.run_id, "binding": [record.tenant_id, record.actor_id, record.idempotency_scope, record.endpoint, record.request_checksum]}
    elif isinstance(value, CuratedOutcome):
        row["value"] = {"kind": "curated", "code": value.code, "source": asdict(value.source) if value.source else None, "decision": asdict(value.decision), "request": dict(value.request_projection) if value.request_projection else None, "binding": [record.tenant_id, record.actor_id, record.idempotency_scope, record.endpoint, record.request_checksum]}
    else:
        row["value"] = {"kind": "none"}
    return row


def idempotency_record_from_dict(row: dict[str, Any], service: Stage4Service) -> IdempotencyRecord:
    names = ("idempotency_record_id", "tenant_id", "actor_id", "idempotency_scope", "endpoint", "idempotency_key", "request_checksum", "status", "created_at", "updated_at")
    if not all(isinstance(row.get(name), str) for name in names):
        raise ValueError("Stage 4 idempotency fields must be strings.")
    record_id, tenant_id, actor_id, scope, endpoint, key, request_checksum, status, created_at, updated_at = (row[name] for name in names)
    if record_id != "idem_" + hashlib.sha256(f"{tenant_id}:{actor_id}:{scope}:{endpoint}:{key}".encode()).hexdigest()[:16] or re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", request_checksum) is None:
        raise ValueError("Stage 4 idempotency binding is invalid.")
    value_ref = row.get("value", {})
    value: Any = None
    if isinstance(value_ref, dict):
        kind = value_ref.get("kind")
        identifier = cast(str, value_ref.get("id")) if isinstance(value_ref.get("id"), str) else ""
        if kind == "error":
            failure = (value_ref.get("status_code"), value_ref.get("code"), value_ref.get("message"))
            projection = [tenant_id, actor_id, scope, endpoint, request_checksum]
            legacy = failure in {(413, "UPLOAD_TOO_LARGE", "Upload exceeds the Stage 4 size limit."), (422, "VALIDATION_ERROR", "Project name is required.")}
            current = value_ref.get("binding") == projection and endpoint != "POST /api/v1/projects"
            value = Stage4Error(cast(int, failure[0]), cast(str, failure[1]), cast(str, failure[2])) if service._restored_failure_is_valid(tenant_id, actor_id, scope, endpoint, failure) and (current or value_ref.get("binding") is None and legacy) else None
        elif kind == "project":
            value = project_value if (project_value := service.projects.get(identifier)) is not None and (tenant_id, actor_id, scope, endpoint, request_checksum) == (project_value.tenant_id, project_value.owner_id, "project:create", "POST /api/v1/projects", checksum_text(f"{project_value.name}\n{project_value.description}\n{project_value.default_audience}\n{project_value.default_language}")) else None
        elif kind == "document":
            value = document_value if (document_value := service.documents.get(identifier)) is not None and (tenant_id, actor_id, scope, request_checksum) == (document_value.tenant_id, document_value.owner_id, document_value.project_id, checksum_text(f"{document_value.project_id}\n{document_value.source_filename}\n{document_value.content_type}\n{document_value.checksum.removeprefix('sha256:')}") if endpoint == "POST /api/v1/projects/{projectId}/knowledge-documents" else checksum_text(f"{document_value.project_id}\n{document_value.document_id}\nAPPROVED") if endpoint == "PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval" else "") else None
        elif kind == "ingestion":
            value = ingestion_value if (ingestion_value := service.ingestion_runs.get(identifier)) is not None and (tenant_id, actor_id, scope, endpoint, request_checksum) == (ingestion_value.tenant_id, ingestion_value.actor_id, ingestion_value.project_id, "POST /api/v1/projects/{projectId}/ingestion-runs", canonical_digest({"project": ingestion_value.project_id, "sourceIds": ingestion_value.source_ids}) if ingestion_value.source_ids else checksum_text(f"{ingestion_value.project_id}\n{','.join(ingestion_value.document_ids)}")) else None
        elif kind == "walkthrough":
            walkthrough_value = service.walkthrough_runs.get(identifier)
            if walkthrough_value is not None and (tenant_id, actor_id, scope, endpoint) == (walkthrough_value.tenant_id, walkthrough_value.actor_id, walkthrough_value.project_id, "POST /api/v1/projects/{projectId}/walkthrough-runs"):
                projection = [tenant_id, actor_id, scope, endpoint, request_checksum]
                if walkthrough_value.request_checksum == request_checksum and value_ref.get("binding") == projection:
                    value = walkthrough_value
                elif not walkthrough_value.request_checksum and value_ref.get("binding") is None:
                    value = walkthrough_value
        elif kind == "curated":
            source_data, decision_data = value_ref.get("source"), value_ref.get("decision")
            if not isinstance(decision_data, dict):
                raise ValueError("Curated idempotency projection is malformed.")
            decision = SourceDecisionRecord(**decision_data)
            live_decision = service.source_decisions.get(decision.decision_id) if isinstance(decision.decision_id, str) else None
            code = str(value_ref.get("code", ""))
            projection = [tenant_id, actor_id, scope, endpoint, request_checksum]
            if source_data is None:
                request_projection = value_ref.get("request")
                value = CuratedOutcome(code, None, decision, request_projection=cast(dict[str, Any], request_projection)) if live_decision == decision and code == "SOURCE_EXCLUDED" and legal_exclusion(decision) and legal_exclusion_request(decision, request_projection, request_checksum) and cast(dict[str, Any], request_projection)["fileBytes"] <= MAX_UPLOAD_BYTES and decision.source_id not in service.sources and value_ref.get("binding") == projection and (tenant_id, actor_id, scope, endpoint) == (decision.tenant_id, decision.actor_id, decision.project_id, "POST /api/v1/projects/{projectId}/knowledge-documents") else None
            else:
                if not isinstance(source_data, dict) or not isinstance(source_data.get("assertions"), dict):
                    raise ValueError("Curated idempotency projection is malformed.")
                source = SourceRecord(**(source_data | {"assertions": SourceAssertions(**cast(dict[str, Any], source_data.get("assertions", {}))) }))
                live_source = service.sources.get(source.source_id) if isinstance(source.source_id, str) else None
                expected_checksum = canonical_digest({"endpoint": "curated-submit", "schema": CURATION_SCHEMA_VERSION, "tenant": source.tenant_id, "actor": source.owner_id, "project": source.project_id, "filename": source.source_filename, "mime": source.content_type, "fileSha256": source.checksum, "fileBytes": source.size_bytes, "assertions": asdict(source.assertions), "action": decision.action} if code == "SOURCE_PENDING_REVIEW" else {"endpoint": "curated-approval", "tenant": source.tenant_id, "actor": source.owner_id, "project": source.project_id, "curationSchemaVersion": CURATION_SCHEMA_VERSION, "action": "APPROVE", "sourceId": source.source_id, "decisionId": decision.decision_id, "policyVersion": decision.policy_version, "sourceVersion": decision.source_version, "checksum": decision.checksum, "assertionsFingerprint": decision.assertions_fingerprint} if code == "SOURCE_APPROVED" else {})
                value = CuratedOutcome(code, source, decision) if live_source is not None and live_decision is not None and service._restored_curated_source_is_safe(source) and legal_pair(source, decision) and (code, decision.decision_state, source.ingestion_status) in (("SOURCE_PENDING_REVIEW", "PENDING_REVIEW", "NOT_STARTED"), ("SOURCE_APPROVED", "APPROVED", "NOT_STARTED")) and replace(source, ingestion_status=live_source.ingestion_status, ingested_at=live_source.ingested_at) == live_source and replace(decision, action=live_decision.action, reason=live_decision.reason, decision_state=live_decision.decision_state, approved_at=live_decision.approved_at) == live_decision and (tenant_id, actor_id, scope, endpoint, request_checksum) == (source.tenant_id, source.owner_id, source.project_id, "POST /api/v1/projects/{projectId}/knowledge-documents" if code == "SOURCE_PENDING_REVIEW" else "PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval", expected_checksum) else None
    status = str(row["status"])
    if status not in {"PENDING", "COMPLETED", "FAILED"}:
        raise ValueError(f"Unsupported Stage 4 idempotency status: {status}")
    if status == "COMPLETED" and (value is None or isinstance(value, Stage4Error)):
        raise ValueError("Completed Stage 4 idempotency record references missing value.")
    if status == "FAILED" and not isinstance(value, Stage4Error):
        raise ValueError("Failed Stage 4 idempotency record references missing error.")
    return IdempotencyRecord(
        idempotency_record_id=str(row["idempotency_record_id"]),
        tenant_id=str(row["tenant_id"]),
        actor_id=str(row["actor_id"]),
        idempotency_scope=str(row["idempotency_scope"]),
        endpoint=str(row["endpoint"]),
        idempotency_key=str(row["idempotency_key"]),
        request_checksum=request_checksum,
        status=cast(Literal["PENDING", "COMPLETED", "FAILED"], status),
        value=value,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def max_numeric_suffix(records: Mapping[str, object], prefix: str) -> int:
    maximum = 0
    for identifier in records:
        if identifier.startswith(prefix):
            try:
                maximum = max(maximum, int(identifier.removeprefix(prefix)))
            except ValueError:
                continue
    return maximum


def sanitize_filename(filename: str) -> str:
    raw = filename.strip()
    if (
        not raw
        or raw in {".", ".."}
        or "/" in raw
        or "\\" in raw
        or ".." in PurePath(raw).parts
        or len(raw) > 160
        or any(ord(char) < 32 for char in raw)
    ):
        raise Stage4Error(422, "VALIDATION_ERROR", "Invalid filename.")
    name = PurePath(raw).name
    return name


def validate_upload_bytes(data: bytes) -> None:
    if data.startswith(ARCHIVE_MAGIC_BYTES):
        raise Stage4Error(415, "UNSUPPORTED_MEDIA_TYPE", "Archive uploads are not accepted in Stage 4.")
    if b"\x00" in data:
        raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document contains NUL bytes.")
    control_count = sum(1 for byte in data if byte < 32 and byte not in {9, 10, 13})
    if data and control_count / len(data) > 0.01:
        raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document contains too many control characters.")


def decode_upload(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document must be UTF-8 text.") from exc


def parse_document_text(text: str) -> str:
    if "\x00" in text:
        raise Stage4Error(422, "VALIDATION_ERROR", "Uploaded document contains NUL bytes.")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if contains_secret_like_content(normalized):
        raise Stage4Error(422, "SECRET_LIKE_CONTENT", "Uploaded document contains secret-like content.")
    return normalized


def normalize_content_type(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def contains_prompt_injection(text: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower())
    normalized = " ".join(normalized.split())
    return any(pattern.search(normalized) for pattern in PROMPT_INJECTION_PATTERNS)


def contains_secret_like_content(text: str) -> bool:
    return any(pattern.search(text) for _, pattern in SECRET_REDACTION_PATTERNS)


def redact_public_text(text: str) -> tuple[str, list[str]]:
    redacted = text
    flags: list[str] = []
    for flag, pattern in SECRET_REDACTION_PATTERNS:
        if pattern.search(redacted):
            redacted = pattern.sub("[REDACTED]", redacted)
            flags.append(flag)
    if len(text) > MAX_PUBLIC_EXCERPT_CHARS or len(redacted) > MAX_PUBLIC_EXCERPT_CHARS:
        redacted = redacted[:MAX_PUBLIC_EXCERPT_CHARS]
        flags.append("TRUNCATED")
    return redacted, flags


def project_to_api(project: ProjectRecord) -> dict[str, Any]:
    return {
        "projectId": project.project_id,
        "tenantId": project.tenant_id,
        "ownerId": project.owner_id,
        "name": project.name,
        "description": project.description,
        "projectStatus": "ACTIVE",
        "defaultAudience": project.default_audience,
        "defaultLanguage": project.default_language,
        "createdAt": project.created_at,
        "updatedAt": project.updated_at,
    }


def document_to_api(document: DocumentRecord) -> dict[str, Any]:
    return {
        "documentId": document.document_id,
        "tenantId": document.tenant_id,
        "projectId": document.project_id,
        "sourceFilename": document.source_filename,
        "contentType": document.content_type,
        "sizeBytes": document.size_bytes,
        "checksum": document.checksum,
        "documentStatus": document.document_status,
        "approvalStatus": document.approval_status,
        "ingestionStatus": document.ingestion_status,
        "createdAt": document.created_at,
        "approvedAt": document.approved_at,
    }


def ingestion_to_api(run: IngestionRunRecord) -> dict[str, Any]:
    return {
        "ingestionRunId": run.ingestion_run_id,
        "tenantId": run.tenant_id,
        "actorId": run.actor_id,
        "projectId": run.project_id,
        "status": run.status,
        "documentIds": run.document_ids,
        "sourceIds": run.source_ids,
        "ingestionKind": "CURATED" if run.source_ids else "LEGACY",
        "chunkCount": run.chunk_count,
        "embeddingCount": run.embedding_count,
        "createdAt": run.created_at,
    }


def walkthrough_to_api(run: WalkthroughRunRecord) -> dict[str, Any]:
    base: dict[str, Any] = {
        "runId": run.run_id,
        "tenantId": run.tenant_id,
        "actorId": run.actor_id,
        "projectId": run.project_id,
        "status": run.status,
        "evaluationStatus": run.evaluation_status,
        "audience": run.audience,
        "requestedLanguage": run.requested_language,
        "depth": run.depth,
        "style": run.style,
        "contextRefs": [_context_ref_to_api(context, run) for context in run.retrieved_context],
        "provider": {"provider": "mock", "providerMode": "LOCAL"},
        "trace": {
            "traceId": run.trace_id,
            "latencyMs": run.latency_ms,
            "inputTokens": run.input_tokens,
            "outputTokens": run.output_tokens,
            "estimatedCost": run.estimated_cost,
        },
        "createdAt": run.created_at,
    }
    if run.accepted_script_text is not None and run.evaluation is not None:
        base["acceptedScriptText"] = run.accepted_script_text
        base["evaluation"] = evaluation_to_api(run.evaluation, run)
    elif run.status == "REFUSED":
        base["failure"] = {
            "reasonCode": run.failure_reason or "LOW_RETRIEVAL_CONFIDENCE",
            "message": _failure_message_for_reason(run.failure_reason),
            "unsupportedClaimCount": 0,
        }
    elif run.evaluation is not None:
        base["failure"] = {
            "reasonCode": run.failure_reason or "UNSUPPORTED_PROJECT_FACT",
            "message": "Generated output contained unsupported project facts.",
            "unsupportedClaimCount": run.evaluation.unsupported_claim_count,
        }
        base["redactedUnsupportedExcerpts"] = [
            redact_public_text(claim.claim_text)[0] for claim in run.evaluation.unsupported_claims
        ]
    return base


def _failure_message_for_reason(reason_code: str | None) -> str:
    if reason_code == Stage4Service.WALKTHROUGH_REFUSAL_REASON_PROMPT_INJECTION:
        return "The request was refused because it contained unsafe instruction-like content."
    if reason_code == Stage4Service.WALKTHROUGH_REFUSAL_REASON_UNSAFE_CONTEXT:
        return "The request was refused because retrieved approved context contained unsafe instruction-like content."
    if reason_code == Stage4Service.WALKTHROUGH_REFUSAL_REASON_LOW_RETRIEVAL:
        return "No safe approved ingested context was available for generation."
    return "The walkthrough request was refused by the safety policy."


def evaluation_to_api(evaluation: EvaluationResult, run: WalkthroughRunRecord) -> dict[str, Any]:
    context_by_id = {context.context_ref_id: context for context in run.retrieved_context}
    return {
        "schema": "EvaluationSummary",
        "evaluationId": evaluation.evaluation_id,
        "evaluationStatus": evaluation.evaluation_status,
        "groundednessScore": evaluation.groundedness_score,
        "faithfulness": evaluation.faithfulness_score,
        "answerRelevancy": evaluation.answer_relevancy,
        "contextPrecision": evaluation.context_precision,
        "contextRecall": evaluation.context_recall,
        "unsupportedClaimCount": evaluation.unsupported_claim_count,
        "unsupportedClaims": [
            {
                "claimId": claim.claim_id,
                "claimText": redact_public_text(claim.claim_text)[0],
                "reason": claim.reason,
            }
            for claim in evaluation.unsupported_claims
        ],
        "claimSupports": [
            {
                "claimSupportId": support.claim_support_id,
                "tenantId": evaluation.tenant_id,
                "projectId": evaluation.project_id,
                "runId": evaluation.run_id,
                "evaluationId": evaluation.evaluation_id,
                "claimId": support.claim_id,
                "contextRefId": support.context_ref_id,
                "chunkId": support.chunk_id,
                "documentId": support.document_id,
                "supportStatus": support.support_status,
                "supportScore": support.support_score,
                "supportReason": support.support_reason,
                "evidenceSnapshot": _context_ref_to_api(context_by_id[support.context_ref_id], run)["evidenceSnapshot"],
                "citationIndex": support.citation_index,
            }
            for support in evaluation.claim_supports
            if support.context_ref_id in context_by_id
        ],
        "contextRefCoverage": evaluation.context_ref_coverage,
        "embeddingProvider": "mock",
        "embeddingModel": MOCK_EMBEDDING_MODEL,
        "embeddingModelVersion": MOCK_EMBEDDING_MODEL_VERSION,
        "embeddingDimension": 16,
        "vectorStore": "memory",
        "retrievalStrategyVersion": evaluation.retrieval_strategy_version,
        "retrievalTopK": evaluation.retrieval_top_k,
        "retrievalScoreThreshold": evaluation.retrieval_score_threshold,
        "policyVersion": evaluation.policy_version,
        "schemaVersion": evaluation.schema_version,
        "safetyPolicyVersion": evaluation.safety_policy_version,
        "contextRefs": [_context_ref_to_api(context, run) for context in run.retrieved_context],
    }


def _context_ref_to_api(context: RetrievedContext, run: WalkthroughRunRecord) -> dict[str, Any]:
    claim = None
    if run.generated_script is not None:
        claim = next(
            (candidate for candidate in run.generated_script.claims if candidate.chunk_id == context.chunk.chunk_id),
            None,
        )
    excerpt, redaction_flags = redact_public_text(context.chunk.text)
    evidence_snapshot = {
        "evidenceSnapshotId": "evsnap_" + context.context_ref_id.removeprefix("ctx_"),
        "tenantId": context.chunk.tenant_id,
        "projectId": context.chunk.project_id,
        "documentId": context.chunk.document_id,
        "chunkId": context.chunk.chunk_id,
        "sourceFilename": context.chunk.source_filename,
        "chunkIndex": context.chunk.chunk_index,
        "sourceDocumentChecksum": context.chunk.source_document_checksum,
        "chunkChecksum": context.chunk.checksum,
        "chunkingStrategyVersion": CHUNKING_STRATEGY_VERSION,
        "retrievalScore": round(context.score, 4),
        "redactedExcerpt": excerpt,
        "excerptStart": 0,
        "excerptEnd": len(excerpt),
        "redactionFlags": redaction_flags,
        "capturedAt": run.created_at,
    }
    evidence_snapshot["snapshotChecksum"] = checksum_text(
        json.dumps(evidence_snapshot, sort_keys=True, separators=(",", ":"))
    )
    return {
        "contextRefId": context.context_ref_id,
        "tenantId": context.chunk.tenant_id,
        "projectId": context.chunk.project_id,
        "claimId": claim.claim_id if claim is not None else "",
        "chunkId": context.chunk.chunk_id,
        "documentId": context.chunk.document_id,
        "sourceFilename": context.chunk.source_filename,
        "chunkIndex": context.chunk.chunk_index,
        "checksum": context.chunk.checksum,
        "scriptSpanStart": claim.script_span_start if claim is not None else 0,
        "scriptSpanEnd": claim.script_span_end if claim is not None else 0,
        "evidenceSnapshot": evidence_snapshot,
    }


stage4_service = Stage4Service(state_path=resolve_state_file("stage4"))
