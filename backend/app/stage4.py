"""Stage 4 local product slice orchestration with source_chunk citations."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field
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
from backend.app.rag.providers import MockEmbeddingProvider, MockLLMProvider
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


def _now() -> str:
    return datetime.now(UTC).isoformat()


class Stage4Error(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


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
        self.ingestion_runs: dict[str, IngestionRunRecord] = {}
        self.walkthrough_runs: dict[str, WalkthroughRunRecord] = {}
        self.idempotency_records: dict[tuple[str, str, str, str, str], IdempotencyRecord] = {}
        self._active_ingestions: set[tuple[str, str]] = set()
        self._active_generations: set[tuple[str, str]] = set()
        self._operation_lock = RLock()
        self._project_counter = 0
        self._document_counter = 0
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
        self.ingestion_runs.clear()
        self.walkthrough_runs.clear()
        self.idempotency_records.clear()
        self._active_ingestions.clear()
        self._active_generations.clear()
        self._project_counter = 0
        self._document_counter = 0
        self._ingestion_counter = 0
        self._run_counter = 0

    def _restore(self) -> None:
        payload = load_state(self.state_path)
        if payload is None:
            return
        try:
            if payload.get("schema") != "stage4-local-state-v1":
                raise ValueError("Stage 4 state schema mismatch.")
            self.projects = {
                str(row["project_id"]): ProjectRecord(**row)
                for row in payload.get("projects", [])
                if isinstance(row, dict) and "project_id" in row
            }
            self.documents = {
                str(row["document_id"]): DocumentRecord(**row)
                for row in payload.get("documents", [])
                if isinstance(row, dict) and "document_id" in row
            }
            self.documents = {
                document_id: document
                for document_id, document in self.documents.items()
                if document.project_id in self.projects
                and self.projects[document.project_id].tenant_id == document.tenant_id
                and self.projects[document.project_id].owner_id == document.owner_id
            }
            self.ingestion_runs = {
                str(row["ingestion_run_id"]): IngestionRunRecord(**row)
                for row in payload.get("ingestionRuns", [])
                if isinstance(row, dict) and "ingestion_run_id" in row
            }
            self.ingestion_runs = {
                run_id: run
                for run_id, run in self.ingestion_runs.items()
                if self._restored_ingestion_run_is_valid(run)
            }
            self.rag_store = InMemoryRagStore.from_dict(cast(dict[str, Any], payload.get("ragStore", {})))
            self.walkthrough_runs = {
                str(row["run_id"]): walkthrough_run_from_dict(row)
                for row in payload.get("walkthroughRuns", [])
                if isinstance(row, dict) and "run_id" in row
            }
            self.rag_store.prune(self._restored_chunk_is_valid)
            self.ingestion_runs = {
                run_id: run
                for run_id, run in self.ingestion_runs.items()
                if self._restored_ingestion_run_has_chunks(run)
            }
            self._reconcile_restored_document_ingestion_status()
            self.walkthrough_runs = {
                run_id: run
                for run_id, run in self.walkthrough_runs.items()
                if self._restored_walkthrough_run_is_valid(run)
            }
            self.idempotency_records = {}
            for row in payload.get("idempotencyRecords", []):
                if not isinstance(row, dict):
                    continue
                if row.get("status") == "PENDING":
                    continue
                try:
                    record = idempotency_record_from_dict(row, self)
                except (KeyError, TypeError, ValueError) as exc:
                    LOGGER.warning("Skipping incompatible Stage 4 idempotency record at %s: %s", self.state_path, exc)
                    continue
                key = (
                    record.tenant_id,
                    record.actor_id,
                    record.idempotency_scope,
                    record.endpoint,
                    record.idempotency_key,
                )
                self.idempotency_records[key] = record
            counters = payload.get("counters", {})
            project_counter = max_numeric_suffix(self.projects, "proj_")
            document_counter = max_numeric_suffix(self.documents, "doc_")
            ingestion_counter = max_numeric_suffix(self.ingestion_runs, "ing_")
            run_counter = max_numeric_suffix(self.walkthrough_runs, "run_")
            if isinstance(counters, dict):
                self._project_counter = max(int(counters.get("project", project_counter)), project_counter)
                self._document_counter = max(int(counters.get("document", document_counter)), document_counter)
                self._ingestion_counter = max(int(counters.get("ingestion", ingestion_counter)), ingestion_counter)
                self._run_counter = max(int(counters.get("run", run_counter)), run_counter)
            else:
                self._project_counter = project_counter
                self._document_counter = document_counter
                self._ingestion_counter = ingestion_counter
                self._run_counter = run_counter
        except (KeyError, TypeError, ValueError) as exc:
            LOGGER.warning("Ignoring incompatible Stage 4 local state snapshot at %s: %s", self.state_path, exc)
            self._clear_runtime_state()

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
            self.ingestion_runs.pop(value.ingestion_run_id, None)
            for document_id in value.document_ids:
                if document_id in snapshot["documents"]:
                    self.documents[document_id] = snapshot["documents"][document_id]
        elif isinstance(value, WalkthroughRunRecord):
            self.walkthrough_runs.pop(value.run_id, None)
        counters = snapshot["counters"]
        self._project_counter = max(int(counters["project"]), max_numeric_suffix(self.projects, "proj_"))
        self._document_counter = max(int(counters["document"]), max_numeric_suffix(self.documents, "doc_"))
        self._ingestion_counter = max(int(counters["ingestion"]), max_numeric_suffix(self.ingestion_runs, "ing_"))
        self._run_counter = max(int(counters["run"]), max_numeric_suffix(self.walkthrough_runs, "run_"))

    def _restored_ingestion_run_is_valid(self, run: IngestionRunRecord) -> bool:
        project = self.projects.get(run.project_id)
        if project is None:
            return False
        if project.tenant_id != run.tenant_id or project.owner_id != run.actor_id:
            return False
        if not all(document_id in self.documents for document_id in run.document_ids):
            return False
        return all(
            self.documents[document_id].tenant_id == run.tenant_id
            and self.documents[document_id].owner_id == run.actor_id
            and self.documents[document_id].project_id == run.project_id
            for document_id in run.document_ids
        )

    def _restored_ingestion_run_has_chunks(self, run: IngestionRunRecord) -> bool:
        if not self._restored_ingestion_run_is_valid(run):
            return False
        chunks = [
            chunk
            for chunk in self.rag_store.chunks_for_project(tenant_id=run.tenant_id, project_id=run.project_id)
            if chunk.document_id in set(run.document_ids)
        ]
        chunk_document_ids = {chunk.document_id for chunk in chunks}
        return (
            run.chunk_count == len(chunks)
            and run.embedding_count == len(chunks)
            and all(document_id in chunk_document_ids for document_id in run.document_ids)
        )

    def _reconcile_restored_document_ingestion_status(self) -> None:
        ingested_document_ids = {
            document_id for run in self.ingestion_runs.values() for document_id in run.document_ids
        }
        for document in self.documents.values():
            if document.ingestion_status == "INGESTED" and document.document_id not in ingested_document_ids:
                document.ingestion_status = "NOT_STARTED"
                document.ingested_at = None

    def _restored_chunk_is_valid(self, chunk: KnowledgeChunk) -> bool:
        document = self.documents.get(chunk.document_id)
        if document is None:
            return False
        if (
            chunk.tenant_id != document.tenant_id
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

    def _restored_walkthrough_run_is_valid(self, run: WalkthroughRunRecord) -> bool:
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
        if any(not self._restored_chunk_is_valid(context.chunk) for context in run.retrieved_context):
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
        if (
            run.evaluation.run_id != run.run_id
            or run.evaluation.tenant_id != run.tenant_id
            or run.evaluation.project_id != run.project_id
        ):
            return False
        context_by_ref = {context.context_ref_id: context for context in run.retrieved_context}
        context_chunk_ids = {context.chunk.chunk_id for context in run.retrieved_context}
        claim_ids = {claim.claim_id for claim in run.generated_script.claims} if run.generated_script is not None else set()
        if run.generated_script is not None and any(
            claim.chunk_id is not None and claim.chunk_id not in context_chunk_ids
            for claim in run.generated_script.claims
        ):
            return False
        return all(
            support.document_id in self.documents
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

    def _runtime_snapshot_locked(self) -> dict[str, Any]:
        return {
            "ragStore": self.rag_store.to_dict(),
            "projects": deepcopy(self.projects),
            "documents": deepcopy(self.documents),
            "ingestionRuns": deepcopy(self.ingestion_runs),
            "walkthroughRuns": deepcopy(self.walkthrough_runs),
            "idempotencyRecords": self.idempotency_records.copy(),
            "activeIngestions": deepcopy(self._active_ingestions),
            "activeGenerations": deepcopy(self._active_generations),
            "counters": {
                "project": self._project_counter,
                "document": self._document_counter,
                "ingestion": self._ingestion_counter,
                "run": self._run_counter,
            },
        }

    def _restore_runtime_snapshot_locked(self, snapshot: dict[str, Any]) -> None:
        self.rag_store = InMemoryRagStore.from_dict(snapshot["ragStore"])
        self.projects = deepcopy(snapshot["projects"])
        self.documents = deepcopy(snapshot["documents"])
        self.ingestion_runs = deepcopy(snapshot["ingestionRuns"])
        self.walkthrough_runs = deepcopy(snapshot["walkthroughRuns"])
        self.idempotency_records = snapshot["idempotencyRecords"].copy()
        self._active_ingestions = deepcopy(snapshot["activeIngestions"])
        self._active_generations = deepcopy(snapshot["activeGenerations"])
        counters = snapshot["counters"]
        self._project_counter = int(counters["project"])
        self._document_counter = int(counters["document"])
        self._ingestion_counter = int(counters["ingestion"])
        self._run_counter = int(counters["run"])

    def _persist_locked(self) -> None:
        write_state(
            self.state_path,
            {
                "schema": "stage4-local-state-v1",
                "projects": [asdict(project) for project in self.projects.values()],
                "documents": [asdict(document) for document in self.documents.values()],
                "ingestionRuns": [asdict(run) for run in self.ingestion_runs.values()],
                "walkthroughRuns": [
                    walkthrough_run_to_dict(run) for run in self.walkthrough_runs.values()
                ],
                "idempotencyRecords": [
                    idempotency_record_to_dict(record) for record in self.idempotency_records.values()
                    if record.status != "PENDING"
                ],
                "ragStore": self.rag_store.to_dict(),
                "counters": {
                    "project": self._project_counter,
                    "document": self._document_counter,
                    "ingestion": self._ingestion_counter,
                    "run": self._run_counter,
                },
            },
        )

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
        self._require_project(principal=principal, project_id=project_id)
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
                    retrieved = retrieve_context(
                        store=self.rag_store,
                        embedder=self.embedder,
                        tenant_id=principal.tenant_id,
                        project_id=project_id,
                        query=f"{audience} {prompt}",
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
                        evaluation = evaluate_grounding(
                            tenant_id=principal.tenant_id,
                            project_id=project_id,
                            run_id=run_id,
                            candidate=generated,
                            retrieved_context=retrieved,
                            prompt=prompt,
                            all_chunks=all_chunks,
                        )
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
        )
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
                return cast(T, existing.value)
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
                support_status="SUPPORTED",
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
        row["value"] = {"kind": "error", "status_code": value.status_code, "code": value.code, "message": value.message}
    elif isinstance(value, ProjectRecord):
        row["value"] = {"kind": "project", "id": value.project_id}
    elif isinstance(value, DocumentRecord):
        row["value"] = {"kind": "document", "id": value.document_id}
    elif isinstance(value, IngestionRunRecord):
        row["value"] = {"kind": "ingestion", "id": value.ingestion_run_id}
    elif isinstance(value, WalkthroughRunRecord):
        row["value"] = {"kind": "walkthrough", "id": value.run_id}
    else:
        row["value"] = {"kind": "none"}
    return row


def idempotency_record_from_dict(row: dict[str, Any], service: Stage4Service) -> IdempotencyRecord:
    value_ref = row.get("value", {})
    value: Any = None
    if isinstance(value_ref, dict):
        kind = value_ref.get("kind")
        identifier = str(value_ref.get("id", ""))
        if kind == "error":
            value = Stage4Error(
                int(value_ref.get("status_code", 500)),
                str(value_ref.get("code", "INTERNAL_SERVER_ERROR")),
                str(value_ref.get("message", "Request failed.")),
            )
        elif kind == "project":
            value = service.projects.get(identifier)
        elif kind == "document":
            value = service.documents.get(identifier)
        elif kind == "ingestion":
            value = service.ingestion_runs.get(identifier)
        elif kind == "walkthrough":
            value = service.walkthrough_runs.get(identifier)
    status = str(row["status"])
    if status not in {"PENDING", "COMPLETED", "FAILED"}:
        raise ValueError(f"Unsupported Stage 4 idempotency status: {status}")
    if status == "COMPLETED" and value is None:
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
        request_checksum=str(row["request_checksum"]),
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
        "retrievalStrategyVersion": RETRIEVAL_STRATEGY_VERSION,
        "retrievalTopK": RETRIEVAL_TOP_K,
        "retrievalScoreThreshold": RETRIEVAL_MIN_SCORE,
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
