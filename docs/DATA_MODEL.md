# Data Model

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-29
- Status: logical model only; no database schema or migrations in Stage 2

## Modeling Principles

- Project data is isolated by `tenant_id`, `owner_id`, and `project_id`.
- Local Stage 4 data uses a synthetic tenant and user from day one.
- Source documents and chunks are canonical.
- Embeddings, vector indexes, generated media, and caches are derived.
- Generated outputs must preserve context references and evaluation metadata.
- Provider-native IDs are metadata, not canonical IDs.
- Every security-relevant action can produce an audit event.

## Entity Relationship Summary

```text
Tenant
-> User
-> Project
-> IdempotencyRecord
-> KnowledgeDocument
-> KnowledgeChunk
-> EmbeddingRecord
-> IngestionRun
-> WalkthroughRun
-> EvaluationResult
-> EvidenceSnapshot
-> ClaimSupport
-> JobLease
-> OutboxEvent
-> Tombstone
-> Artifact
-> AuditEvent
```

Stage 4 operates in local single-user mode through synthetic tenant/user records,
not by omitting authorization fields.

## Synthetic Local Tenant And User

Stage 4 must create or assume these logical records:

- `tenant_id = tenant_local`
- `user_id = user_local`
- `owner_id = user_local`

All project-scoped entities include `tenant_id` and `project_id`; user-owned
entities include `owner_id` or `actor_id`. Future auth changes how the actor is
resolved, not the storage shape.

## Entities

### Tenant

Fields:

- `tenant_id`
- `name`
- `status`
- `created_at`
- `updated_at`

### User

Fields:

- `user_id`
- `tenant_id`
- `email`
- `display_name`
- `role`
- `created_at`
- `updated_at`

### Project

Fields:

- `project_id`
- `tenant_id`
- `owner_id`
- `name`
- `description`
- `default_language`
- `default_audience`
- `project_status`
- `created_at`
- `updated_at`
- optional `deleted_at`

Project statuses:

- `ACTIVE`
- `DELETED`

Indexes:

- `project_id`
- `(tenant_id, project_id)`
- `(tenant_id, owner_id)`
- `(tenant_id, owner_id, created_at, project_id)`

### IdempotencyRecord

Durable write-safety record. Every mutating endpoint creates or reads this record
transactionally before provider calls, vector writes, artifact writes, cache writes,
or outbox dispatch.

Fields:

- `idempotency_record_id`
- `idempotency_key`
- `tenant_id`
- `actor_id`
- optional `project_id`
- `idempotency_scope`
- `endpoint`
- `request_checksum`
- `status`
- optional `response_status`
- optional `response_body_checksum`
- optional `response_body_ref`
- optional `resource_type`
- optional `resource_id`
- optional `job_ref`
- optional `error_code`
- optional `locked_by`
- optional `locked_at`
- optional `locked_until`
- `created_at`
- `updated_at`
- `expires_at`

Statuses:

- `RESERVED`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `EXPIRED`

Rules:

- `idempotency_scope` is non-null; use `project:create` for `POST /projects` and
  `project_id` for project-scoped writes
- unique key is `(tenant_id, actor_id, idempotency_scope, endpoint,
  idempotency_key)`
- same key and same checksum returns stored response or current job state
- same key and different checksum returns `IDEMPOTENCY_CONFLICT`
- failed records are replayable only when no external side effect was committed;
  otherwise retry resumes from the persisted job or outbox state

Indexes:

- `(tenant_id, actor_id, idempotency_scope, endpoint, idempotency_key)`
- `(tenant_id, actor_id, idempotency_scope, endpoint, request_checksum)`
- `(expires_at)`

### KnowledgeDocument

Fields:

- `document_id`
- `project_id`
- `tenant_id`
- `source_filename`
- `sanitized_filename`
- `content_type`
- `size_bytes`
- `checksum`
- `storage_uri`
- `document_status`
- `approval_status`
- `ingestion_status`
- optional `approved_by`
- optional `approved_at`
- optional `quarantine_reason`
- optional `ingested_at`
- `created_at`
- optional `deleted_at`

Document statuses:

- `UPLOADED`
- `STORED`
- `QUARANTINED`
- `DELETED`

Approval statuses:

- `PENDING`
- `APPROVED`
- `REJECTED`

Ingestion statuses:

- `NOT_STARTED`
- `QUEUED`
- `RUNNING`
- `INGESTED`
- `FAILED`
- `REFUSED`
- `CANCELLED`
- `INVALIDATED`

Rules:

- upload cannot directly approve or ingest a document
- ingestion requires `document_status = STORED` and `approval_status = APPROVED`
- retrieval requires `document_status = STORED`, `approval_status = APPROVED`,
  `ingestion_status = INGESTED`, and no source or chunk tombstone
- approval, quarantine, rejection, deletion, checksum changes, rechunking, embedding
  model changes, and retrieval-policy changes invalidate derived chunks,
  embeddings, retrieval caches, and generated-script caches

Indexes:

- `(project_id, document_id)`
- `(project_id, checksum)`
- `(tenant_id, project_id, document_id)`
- `(tenant_id, project_id, approval_status)`
- `(tenant_id, project_id, document_status)`
- `(tenant_id, project_id, ingestion_status)`
- `(tenant_id, project_id, document_status, approval_status, ingestion_status)`
- `(tenant_id, project_id, created_at, document_id)`

### KnowledgeChunk

Fields:

- `chunk_id`
- `project_id`
- `tenant_id`
- `document_id`
- `chunk_index`
- `text`
- `token_count`
- `checksum`
- `metadata`
- optional `line_start`
- optional `line_end`
- `created_at`

Metadata:

- source filename
- heading path when available
- chunking strategy version
- document checksum

Indexes:

- `(project_id, document_id, chunk_index)`
- `(project_id, chunk_id)`
- `(tenant_id, project_id, chunk_id)`
- `(tenant_id, project_id, document_id, chunk_index)`

### EmbeddingRecord

Derived record.

Fields:

- `embedding_id`
- `project_id`
- `tenant_id`
- `chunk_id`
- `provider`
- `model`
- `vector_store`
- `vector_ref`
- `embedding_dim`
- `status`
- `created_at`

Rules:

- can be regenerated from `KnowledgeChunk`
- not treated as canonical source of truth
- retrieval filters must include tenant and project metadata

Indexes:

- `(tenant_id, project_id, chunk_id)`
- `(tenant_id, project_id, provider, model, status)`
- `(tenant_id, project_id, vector_store, vector_ref)`

### IngestionRun

Fields:

- `ingestion_run_id`
- `tenant_id`
- `project_id`
- `actor_id`
- `document_ids`
- `status`
- `idempotency_key`
- optional `idempotency_record_id`
- `attempt_count`
- `max_attempts`
- optional `next_attempt_at`
- optional `locked_by`
- optional `locked_at`
- optional `lease_expires_at`
- `chunk_count`
- `embedding_count`
- optional `error_code`
- optional `last_error_code`
- optional `refusal_reason`
- optional `outbox_event_id`
- `queued_at`
- optional `started_at`
- optional `completed_at`
- optional `failed_at`
- `created_at`
- `updated_at`

Statuses:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `REFUSED`
- `CANCELLED`

Indexes:

- `(tenant_id, project_id, ingestion_run_id)`
- `(tenant_id, project_id, status, queued_at)`
- `(tenant_id, project_id, status, created_at)`
- `(tenant_id, project_id, idempotency_key)`
- `(tenant_id, project_id, lease_expires_at)`

### WalkthroughRequest

May be stored separately or embedded in `WalkthroughRun`.

Fields:

- `request_id`
- `project_id`
- `tenant_id`
- `audience`
- `requested_language`
- `depth`
- `style`
- optional `prompt`
- `created_at`

### WalkthroughRun

Fields:

- `run_id`
- `project_id`
- `tenant_id`
- `request_id`
- `status`
- `audience`
- `requested_language`
- `depth`
- `style`
- optional `raw_generated_text`
- optional `accepted_script_text`
- optional `failure_public_message`
- `context_refs`
- `provider`
- `provider_mode`
- optional `model`
- `trace_id`
- `idempotency_key`
- optional `idempotency_record_id`
- `prompt_template_version`
- `retrieval_strategy_version`
- `retrieval_top_k`
- `retrieval_score_threshold`
- `retrieved_context_count`
- `attempt_count`
- `max_attempts`
- optional `next_attempt_at`
- optional `locked_at`
- optional `locked_by`
- optional `lease_expires_at`
- `latency_ms`
- optional `token_usage`
- optional `estimated_cost`
- `error_code`
- optional `refusal_reason`
- optional `outbox_event_id`
- `queued_at`
- optional `started_at`
- optional `completed_at`
- optional `failed_at`
- `created_at`
- `updated_at`

Statuses:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `REFUSED`
- `CANCELLED`

Indexes:

- `(tenant_id, project_id, run_id)`
- `(tenant_id, project_id, status, queued_at)`
- `(tenant_id, project_id, status, created_at)`
- `(tenant_id, project_id, idempotency_key)`
- `(tenant_id, project_id, provider, provider_mode, created_at)`
- `(tenant_id, project_id, lease_expires_at)`

Rules:

- `raw_generated_text` is internal-only and may be retained for audit after
  redaction policy is applied
- public API responses expose `accepted_script_text` only when evaluation status is
  `PASSED` or an allowed non-factual `WARNING`
- `FAILED` and `REFUSED` public responses omit raw generated output and expose only
  refusal/failure metadata plus redacted unsupported excerpts

### ContextRef

Stored as structured records or embedded JSON attached to a run.

Fields:

- `context_ref_id`
- `run_id`
- `project_id`
- `tenant_id`
- `chunk_id`
- `document_id`
- `claim_id`
- `script_span_start`
- `script_span_end`
- `evidence_snapshot`
- `source_filename`
- `chunk_index`
- optional `line_start`
- optional `line_end`
- `checksum`

Rules:

- context refs used for grounding must be claim-level context references
- evidence snapshots use the typed `EvidenceSnapshot` shape
- deletion keeps tombstones so prior runs remain auditable

Indexes:

- `(tenant_id, project_id, run_id)`
- `(tenant_id, project_id, claim_id)`
- `(tenant_id, project_id, chunk_id)`

### EvidenceSnapshot

Immutable redacted evidence copied at evaluation time so historical runs remain
auditable after source deletion, rechunking, embedding changes, or provider drift.

Fields:

- `evidence_snapshot_id`
- `tenant_id`
- `project_id`
- `document_id`
- `chunk_id`
- `source_filename`
- `chunk_index`
- optional `line_start`
- optional `line_end`
- `source_document_checksum`
- `chunk_checksum`
- `chunking_strategy_version`
- `retrieval_score`
- `redacted_excerpt`
- `excerpt_start`
- `excerpt_end`
- `redaction_flags`
- `captured_at`
- `snapshot_checksum`

Rules:

- excerpts are redacted and truncated before storage
- `snapshot_checksum` covers the redacted snapshot payload
- raw source text is not required to reconstruct support decisions

### EvaluationResult

Fields:

- `evaluation_id`
- `run_id`
- `project_id`
- `tenant_id`
- `evaluation_status`
- `groundedness_score`
- `unsupported_claim_count`
- `unsupported_claims`
- `context_refs`
- `claim_supports`
- `context_ref_coverage`
- `evaluator_version`
- `prompt_template_version`
- `retrieval_strategy_version`
- `retrieval_top_k`
- `retrieval_score_threshold`
- `embedding_provider`
- `embedding_model`
- `embedding_model_version`
- `embedding_dimension`
- `vector_store`
- optional `error_code`
- `prompt_injection_detected`
- `language_check`
- `audience_fit_check`
- `output_schema_valid`
- optional `refusal_reason`
- `provider`
- `provider_mode`
- optional `model`
- `latency_ms`
- optional `estimated_cost`
- `created_at`

Statuses:

- `PASSED`
- `WARNING`
- `FAILED`
- `REFUSED`

Indexes:

- `(tenant_id, project_id, run_id)`
- `(tenant_id, project_id, evaluation_status, created_at)`
- `(tenant_id, project_id, evaluation_id)`

### UnsupportedClaim

Fields:

- `claim_id`
- `tenant_id`
- `project_id`
- `run_id`
- `evaluation_id`
- `claim_text`
- `claim_status`
- `severity`
- `reason_code`
- `supporting_context_refs`
- `reason`
- `script_span_start`
- `script_span_end`
- `redacted_excerpt`

Claim statuses:

- `SUPPORTED`
- `UNSUPPORTED`
- `AMBIGUOUS`
- `MISSING_CONTEXT_REF`

### ClaimSupport

Fields:

- `claim_support_id`
- `tenant_id`
- `project_id`
- `run_id`
- `evaluation_id`
- `claim_id`
- `context_ref_id`
- `chunk_id`
- `document_id`
- `support_status`
- `support_score`
- `support_reason`
- `evidence_snapshot`
- `created_at`

`evidence_snapshot` is the immutable redacted snapshot used by this support
decision. API responses may duplicate it on `claimSupports` for auditability and
also expose the same snapshot through the linked `ContextRef.evidenceSnapshot`.

Support statuses:

- `SUPPORTED`
- `UNSUPPORTED`
- `AMBIGUOUS`

Indexes:

- `(tenant_id, project_id, run_id, claim_id)`
- `(tenant_id, project_id, evaluation_id)`
- `(tenant_id, project_id, context_ref_id)`

### JobLease

Lease record for ingestion and walkthrough work. Stage 4 may execute synchronously,
but it must persist the same lifecycle so later worker execution does not require a
data-model rewrite.

Fields:

- `job_lease_id`
- `tenant_id`
- `project_id`
- `job_type`
- `job_id`
- `locked_by`
- `locked_at`
- `lease_expires_at`
- `attempt_count`
- `max_attempts`
- optional `last_error_code`
- `created_at`
- `updated_at`

Rules:

- a worker may execute only while holding an unexpired lease
- lease acquisition and `attempt_count` increment are transactional
- expired `RUNNING` jobs can be recovered by lease steal after `lease_expires_at`

Indexes:

- `(tenant_id, project_id, job_type, job_id)`
- `(tenant_id, project_id, lease_expires_at)`

### OutboxEvent

Committed side-effect record for audit, observability, provider/vector/cache
operations, and future worker dispatch.

Fields:

- `outbox_event_id`
- `tenant_id`
- optional `project_id`
- `event_type`
- `resource_type`
- `resource_id`
- `operation_key`
- `payload_ref`
- `status`
- `attempt_count`
- optional `last_error_code`
- `created_at`
- `updated_at`

Statuses:

- `PENDING`
- `DISPATCHED`
- `FAILED`
- `DEAD_LETTERED`

Rules:

- outbox rows are written in the same transaction as resource/job state changes
- external dispatch happens only from committed outbox rows
- dispatch is idempotent by `outbox_event_id` and `operation_key`
- Stage 4 sync mode may dispatch immediately after commit, but poison events move
  to `DEAD_LETTERED` after retry policy is exhausted

Indexes:

- `(tenant_id, project_id, status, created_at)`
- `(operation_key)`

### Tombstone

Deletion marker for canonical records and derived artifacts. Tombstones preserve
auditability, prevent accidental resurrection during import, and record cache
invalidation state.

Fields:

- `tombstone_id`
- `tenant_id`
- `project_id`
- `resource_type`
- `resource_id`
- `resource_status`
- `deleted_at`
- `deleted_by`
- `reason_code`
- optional `source_checksum`
- `cache_invalidation_status`
- optional `audit_event_id`
- `created_at`

Cache invalidation statuses:

- `PENDING`
- `COMPLETED`
- `FAILED`

Indexes:

- `(tenant_id, project_id, tombstone_id)`
- `(tenant_id, project_id, resource_type, resource_id)`
- `(tenant_id, project_id, cache_invalidation_status, created_at)`

### Artifact

Fields:

- `artifact_id`
- `project_id`
- `tenant_id`
- optional `run_id`
- `artifact_type`
- `storage_uri`
- `content_type`
- `size_bytes`
- `checksum`
- `provider`
- `provider_mode`
- `disclosure_text`
- optional `consent_ref`
- `created_at`
- optional `deleted_at`

Indexes:

- `(tenant_id, project_id, artifact_id)`
- `(tenant_id, project_id, run_id)`
- `(tenant_id, project_id, artifact_type, created_at)`

Artifact types:

- `SOURCE_DOCUMENT`
- `GENERATED_SCRIPT`
- `SUBTITLE`
- `AUDIO`
- `AVATAR_VIDEO`
- `EXPORT_BUNDLE`

### ConsentRecord

Future identity-media entity.

Fields:

- `consent_id`
- `tenant_id`
- `project_id`
- `subject_name`
- `subject_contact_ref`
- `consent_scope`
- `provider`
- `expires_at`
- `revoked_at`
- `created_at`

Additional consent fields required before any cloned identity feature:

- `consent_evidence_artifact_id`
- `verified_by`
- `captured_at`
- `scope_project_ids`
- `allowed_media_types`
- `revocation_cascade_status`

Required before any cloned voice or face feature.

### AuditEvent

Fields:

- `audit_event_id`
- `trace_id`
- `tenant_id`
- `actor_id`
- `project_id`
- `action`
- `resource_type`
- `resource_id`
- `outcome`
- `reason_code`
- `metadata`
- `created_at`

Rules:

- no raw provider keys
- no raw auth tokens
- no private certificates
- avoid full uploaded content
- include enough data to reconstruct security decisions

Indexes:

- `(tenant_id, project_id, created_at)`
- `(tenant_id, actor_id, created_at)`
- `(trace_id)`

## Required Indexes

Stage 4 must provide indexed access for:

- project lookup by `(tenant_id, project_id)`
- project listing by `(tenant_id, owner_id, created_at, project_id)`
- idempotency lookup by `(tenant_id, actor_id, idempotency_scope, endpoint,
  idempotency_key)`
- document listing by `(tenant_id, project_id, created_at, document_id)`
- document status filtering by `(tenant_id, project_id, document_status,
  approval_status, ingestion_status)`
- approved-document retrieval by `(tenant_id, project_id, approval_status)`
- chunk retrieval by `(tenant_id, project_id, chunk_id)`
- embedding lookup by `(tenant_id, project_id, provider, model, status)`
- ingestion status polling by `(tenant_id, project_id, ingestion_run_id)`
- ingestion queue lookup by `(tenant_id, project_id, status, queued_at)`
- walkthrough listing by `(tenant_id, project_id, created_at, run_id)`
- walkthrough queue lookup by `(tenant_id, project_id, status, queued_at)`
- evaluation lookup by `(tenant_id, project_id, run_id)`
- claim support lookup by `(tenant_id, project_id, run_id, claim_id)`
- job lease recovery by `(tenant_id, project_id, lease_expires_at)`
- outbox dispatch by `(tenant_id, project_id, status, created_at)`
- tombstone lookup by `(tenant_id, project_id, resource_type, resource_id)`
- artifact lookup by `(tenant_id, project_id, artifact_id)`
- audit review by `(tenant_id, project_id, created_at)`

## Retention And Deletion

Stage 4 local deletion behavior:

- projects are soft-deleted with `deleted_at`
- source document files may be physically removed locally
- document metadata, audit events, and tombstones remain
- chunks and embeddings are invalidated, not used for future retrieval
- prior runs and evaluation results remain immutable for audit
- generated artifacts are soft-deleted and retain checksum/tombstone metadata
- export bundles include tombstones for deleted canonical records

## Retention And Deletion Decision

Before cloud or multi-user release:

- retention periods must be documented
- export-before-delete must be considered
- derived vector records must be deleted or invalidated
- provider-side deletion behavior must be documented where external providers store
  data

## Derived Data Rebuild Rules

Embeddings:

- rebuild from `KnowledgeChunk`
- invalidate when chunk text, embedding model, or provider changes

Vector indexes:

- rebuild from `EmbeddingRecord` and chunk metadata
- never treated as canonical export source

Generated outputs:

- preserve original output for audit
- allow regeneration as a new run rather than mutating prior run history

## Data Model Validation Before Implementation

Stage 2 locks these Stage 4 defaults:

- metadata storage technology: local metadata store selected in Stage 3, but it must
  support the entities and indexes in this document
- ID generation strategy: NarraTwin-generated prefixed IDs
- local artifact storage layout: logical storage URIs under generated IDs, never
  original filenames
- max upload/corpus limits: 1 MiB per file, 5 MiB per project
- deletion behavior: local soft delete plus tombstones
- context reference storage shape: claim-level `ContextRef` and `ClaimSupport`
- evaluation result JSON schema: fields and enums defined in
  `docs/AI_SAFETY_AND_EVALUATION.md`
