# ADR 0002: RAG Storage

## Status

Accepted for Stage 2 planning.

## Date

2026-06-29

## Context

The first product slice depends on trustworthy retrieval from approved project
knowledge. Uploaded project docs must be validated, chunked, stored, retrieved by
project, and cited in generated output. Future tenant isolation must not require a
storage rewrite.

The architecture must support local-first development while keeping cloud storage
and alternative vector stores possible later.

## Decision

Use a local-first storage design with explicit provider interfaces:

- canonical source documents stored through `StorageProvider`
- document and run metadata stored in a primary metadata store selected in Stage 3/4
- deterministic chunks stored with source metadata
- embeddings and vector records stored through `VectorStoreProvider`
- vector-store records treated as derived artifacts that can be regenerated from
  canonical documents and chunks

ChromaDB remains the planned first local vector-store candidate behind an internal
adapter, subject to dependency and license review before implementation.

Stage 4 Slice 1 implements the first local RAG path with an in-memory vector
store and deterministic mock embedding provider. pgvector is locked as dependency
preparation only. ChromaDB was removed from active dependencies because
`pip-audit` reports a vulnerable version with no fixed version available. The
in-memory store still enforces the same `tenant_id` and `project_id` retrieval
filter that future adapters must preserve.

Approved knowledge is canonical only when storage, approval, and ingestion state
all pass: `document_status = STORED`, `approval_status = APPROVED`, and
`ingestion_status = INGESTED`. `UPLOADED`, `QUARANTINED`, `REJECTED`,
`INVALIDATED`, and `DELETED` records are not eligible for retrieval or non-local
provider egress.

## Retrieval Strategy v1 Decision

Stage 4 retrieval uses `stage4-rag-v1`:

- `topK = 6`
- minimum score threshold `0.72`
- maximum three chunks per document
- tie-break order: `score desc`, `approved_at desc`, `chunk_index asc`,
  `chunk_id asc`
- deterministic keyword-overlap fallback only within the authorized project
- refusal before generation with `EMPTY_CONTEXT`, `LOW_RETRIEVAL_CONFIDENCE`,
  `AMBIGUOUS_CONTEXT`, `CROSS_PROJECT_CONTEXT`, or `UNSAFE_CONTEXT`

## Knowledge State Decision

Vector records, retrieval caches, and generated-script caches are derived from
approved source documents and chunks. Any source checksum change, approval change,
quarantine, rejection, deletion, chunking strategy change, embedding provider/model
change, retrieval threshold change, or safety-policy change invalidates affected
derived records.

## Data Ownership

Canonical records:

- project metadata
- source document metadata and checksums
- chunk text and source metadata
- walkthrough requests
- generated outputs
- evaluation results
- audit events

Derived records:

- embeddings
- vector-store indexes
- cached retrieval results
- cached provider outputs

Derived records must be rebuildable from canonical records.

## Alternatives Considered

### Vector store as source of truth

Rejected because vector records are provider- and embedding-model-dependent and are
harder to audit, export, or regenerate.

### Single flat filesystem only

Rejected as the long-term architecture because project-scoped retrieval, run
history, evaluations, and current `tenant_id` isolation need structured metadata.

### Cloud storage first

Rejected for MVP because local-first storage reduces privacy and provider setup risk
while the product is pre-release.

## Consequences

Positive:

- local/dev/test can run without managed services
- source documents remain auditable
- vector stores can be replaced
- embeddings can be regenerated after provider or model changes
- project and current `tenant_id` isolation can be enforced at metadata and retrieval
  layers

Negative:

- ingestion needs metadata discipline from the first slice
- export/import contracts are required for portability
- storage adapter tests are required

Stage 4 Slice 1 limitations:

- data is process-local and resets between app restarts
- ingestion and generation run synchronously, so durable active-job uniqueness
  constraints are deferred until asynchronous workers or database migrations start
- markdown and plain text are the only enabled upload formats
- mock embeddings and mock LLM output are deterministic and provider-agnostic, but
  are not quality-equivalent to real providers

Stage 4 verification hardening adds local-mode resource bounds and audit behavior
that future durable adapters must preserve: write APIs require an idempotency
record before side effects, in-memory indexes are keyed by tenant and project,
document chunk construction stops at the per-document budget, evidence snapshot
checksums cover the serialized snapshot payload, and the UI reaches FastAPI
through a same-origin Next.js rewrite rather than broad backend CORS.

## Security Requirements

- every document, chunk, embedding, run, and artifact includes `project_id`
- every document, chunk, embedding, run, and artifact includes `tenant_id`
- retrieval queries must filter by project and tenant from Stage 4 local mode onward
- artifact paths use generated IDs, not user filenames
- uploaded content remains untrusted after storage
- secret screening is required for every provider-bound text segment before
  non-local provider egress
- retrieval uses deterministic chunking with documented chunk size, overlap, top-k,
  threshold, and strategy version
- retrieved evidence must produce claim-level `ContextRef`, `ClaimSupport`, and
  `EvidenceSnapshot` records containing `tenant_id` and `project_id`

## Related Documents

- `docs/DATA_MODEL.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/SECURITY_AND_PRIVACY.md`
