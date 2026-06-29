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
-> KnowledgeDocument
-> KnowledgeChunk
-> EmbeddingRecord
-> IngestionRun
-> WalkthroughRun
-> EvaluationResult
-> ClaimSupport
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
- `status`
- `created_at`
- `updated_at`
- optional `deleted_at`

Indexes:

- `project_id`
- `(tenant_id, project_id)`
- `(tenant_id, owner_id)`

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
- `status`
- `approval_status`
- `approved_by`
- optional `approved_at`
- optional `quarantine_reason`
- `ingested_at`
- `created_at`
- optional `deleted_at`

Statuses:

- `STORED`
- `UPLOADED`
- `QUARANTINED`
- `APPROVED`
- `REJECTED`
- `INGESTED`
- `FAILED`
- `DELETED`

Indexes:

- `(project_id, document_id)`
- `(project_id, checksum)`
- `(tenant_id, project_id, document_id)`
- `(tenant_id, project_id, approval_status)`
- `(tenant_id, project_id, status)`

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
- retrieval filters must include project and future tenant metadata

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
- `attempt_count`
- `chunk_count`
- `embedding_count`
- optional `error_code`
- optional `refusal_reason`
- `queued_at`
- optional `started_at`
- optional `completed_at`
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
- `(tenant_id, project_id, status, created_at)`
- `(tenant_id, project_id, idempotency_key)`

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
- `script_text`
- `context_refs`
- `provider`
- `provider_mode`
- optional `model`
- `trace_id`
- `idempotency_key`
- `prompt_template_version`
- `retrieval_strategy_version`
- `retrieval_top_k`
- `retrieval_score_threshold`
- `retrieved_context_count`
- `latency_ms`
- optional `token_usage`
- optional `estimated_cost`
- `error_code`
- optional `refusal_reason`
- `created_at`
- `updated_at`

Statuses:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `REFUSED`

Indexes:

- `(tenant_id, project_id, run_id)`
- `(tenant_id, project_id, status, created_at)`
- `(tenant_id, project_id, idempotency_key)`
- `(tenant_id, project_id, provider, provider_mode, created_at)`

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
- evidence snapshots are redacted and truncated
- deletion keeps tombstones so prior runs remain auditable

Indexes:

- `(tenant_id, project_id, run_id)`
- `(tenant_id, project_id, claim_id)`
- `(tenant_id, project_id, chunk_id)`

### EvaluationResult

Fields:

- `evaluation_id`
- `run_id`
- `project_id`
- `tenant_id`
- `status`
- `groundedness_score`
- `unsupported_claim_count`
- `unsupported_claims`
- `context_refs`
- `evaluator_version`
- `prompt_template_version`
- `retrieval_strategy_version`
- `retrieval_top_k`
- `retrieval_score_threshold`
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
- `(tenant_id, project_id, status, created_at)`
- `(tenant_id, project_id, evaluation_id)`

### UnsupportedClaim

Fields:

- `claim_id`
- `evaluation_id`
- `claim_text`
- `status`
- `severity`
- `supporting_context_refs`
- `reason`
- `script_span_start`
- `script_span_end`
- `redacted_excerpt`

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
- `support_status`
- `evidence_snapshot`
- `created_at`

Support statuses:

- `SUPPORTED`
- `UNSUPPORTED`
- `AMBIGUOUS`

Indexes:

- `(tenant_id, project_id, run_id, claim_id)`
- `(tenant_id, project_id, evaluation_id)`
- `(tenant_id, project_id, context_ref_id)`

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
- document listing by `(tenant_id, project_id, status, created_at)`
- approved-document retrieval by `(tenant_id, project_id, approval_status)`
- chunk retrieval by `(tenant_id, project_id, chunk_id)`
- embedding lookup by `(tenant_id, project_id, provider, model, status)`
- ingestion status polling by `(tenant_id, project_id, ingestion_run_id)`
- walkthrough listing by `(tenant_id, project_id, status, created_at)`
- evaluation lookup by `(tenant_id, project_id, run_id)`
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
