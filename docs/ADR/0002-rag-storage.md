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

Approved knowledge is canonical only after an explicit document approval state.
`UPLOADED` and `QUARANTINED` documents are not eligible for chunking, embedding,
retrieval, or non-local provider egress.

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
history, evaluations, and future tenant isolation need structured metadata.

### Cloud storage first

Rejected for MVP because local-first storage reduces privacy and provider setup risk
while the product is pre-release.

## Consequences

Positive:

- local/dev/test can run without managed services
- source documents remain auditable
- vector stores can be replaced
- embeddings can be regenerated after provider or model changes
- project and future tenant isolation can be enforced at metadata and retrieval
  layers

Negative:

- ingestion needs metadata discipline from the first slice
- export/import contracts are required for portability
- storage adapter tests are required

## Security Requirements

- every document, chunk, embedding, run, and artifact includes `project_id`
- every document, chunk, embedding, run, and artifact includes `tenant_id`
- retrieval queries must filter by project and tenant from Stage 4 local mode onward
- artifact paths use generated IDs, not user filenames
- uploaded content remains untrusted after storage
- obvious-secret screening is required before non-local provider egress
- retrieval uses deterministic chunking with documented chunk size, overlap, top-k,
  threshold, and strategy version

## Related Documents

- `docs/DATA_MODEL.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/SECURITY_AND_PRIVACY.md`
