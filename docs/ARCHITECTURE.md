# Architecture v1.0

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-29
- Implementation status: blocked until Stage 4 gate approval

## Architecture Goal

NarraTwin AI uses a provider-agnostic, free-first architecture that turns approved
project knowledge into grounded walkthrough scripts before any avatar, voice,
subtitle, or video provider is enabled.

The first implementation slice must prove the trust loop:

```text
project creation
-> markdown/text upload
-> validation
-> ingestion and chunking
-> project-scoped retrieval
-> grounded script generation
-> unsupported-claim evaluation
-> stored output with context references
-> UI display
```

Product implementation remains blocked in Stage 2. This document defines the target
system boundaries, not runnable product code.

## Guiding Decisions

- Build vertical slices through issue-linked PRs.
- Keep core domain logic independent from provider SDKs.
- Make every paid or external provider optional and disabled for local/dev/test.
- Treat uploaded files, prompts, filenames, transcripts, provider outputs, and model
  outputs as untrusted input.
- Store context references, evaluation results, provider mode, and trace metadata
  for every generated output.
- Preserve both product modes: pre-rendered multilingual demo video and interactive
  AI avatar walkthrough.

## System Context

```text
User browser
-> Frontend application
-> Backend API
-> Ingestion worker
-> RAG service
-> Script generation service
-> Evaluator service
-> Storage and vector-store adapters
-> Optional provider adapters
-> Observability pipeline
-> CI quality gates
```

External systems are accessed only through adapters:

- LLM and evaluation providers
- embedding providers
- translation, TTS, STT, subtitle, avatar, and video providers
- vector store
- artifact storage
- observability sinks

## Component Architecture

### Frontend

Responsibilities:

- project creation and selection
- markdown/text knowledge upload
- walkthrough request form for audience, requested language, depth, and style
- generated script display
- context reference display
- evaluation warning display
- refusal and error state display

Security constraints:

- must not hold provider secrets
- must not call provider APIs directly
- must not bypass backend upload validation
- must not hide unsupported-claim warnings
- must render generated text as text, not trusted HTML

Stage 4 scope:

- minimal UI for project creation, upload, request, output, and warnings

Out of Stage 4:

- avatar video player
- audio playback
- subtitle editor
- interactive avatar Q&A

### Backend API

Responsibilities:

- synthetic local principal and authorization boundary from the first slice
- project CRUD
- upload intake and validation
- ingestion orchestration
- walkthrough run orchestration
- retrieval, generation, and evaluation coordination
- provider routing through internal interfaces
- persistence of metadata, outputs, and audit events
- structured API errors

Security constraints:

- validate all request input at the API boundary
- enforce project and future tenant isolation before reading or writing data
- never log secrets, provider keys, raw auth tokens, or private certificates
- enforce rate limits by user, project, route, and provider mode
- keep external provider egress explicit and auditable

### Ingestion Worker

Responsibilities:

- read validated uploaded knowledge from storage
- normalize markdown/plain text
- compute checksums
- chunk content deterministically
- attach source metadata to each chunk
- enqueue embedding/vector-store writes through adapters
- emit ingestion observability events

Security constraints:

- treat file content and filenames as untrusted
- store files under generated safe paths
- reject unsupported content types before ingestion
- cap file size, document count, chunk count, and total project corpus size
- keep prompt-injection text as data, not instructions

Stage 4 implementation may run ingestion synchronously inside the backend only for
inputs within the Stage 4 Resource Budgets. The architectural boundary must still
be explicit so it can move to a separate worker later.

### RAG Service

Responsibilities:

- query only chunks approved for the selected project
- rank retrieved chunks for the selected audience/depth request
- return context references with stable identifiers
- refuse retrieval results when context is empty or below quality thresholds
- isolate embeddings and metadata by future tenant and project

Security constraints:

- never retrieve across projects or tenants
- never expose raw vector-store internals to the frontend
- treat vector-store records as untrusted until validated against metadata
- protect against poisoned source content by separating retrieved facts from
  instructions

### Script Generation Service

Responsibilities:

- assemble prompts from trusted system rules, request parameters, and retrieved
  context
- generate audience-aware walkthrough scripts using only retrieved context
- require context references for project-specific claims
- keep requested language in run metadata
- record provider, provider mode, latency, token usage, and estimated cost when
  available

Security constraints:

- never include provider keys or secrets in prompts
- never include cross-project or cross-tenant context in prompts
- never pass model output to shell commands, SQL, file paths, or HTML rendering
- fail closed when context is unavailable

Stage 4 script acceptance is English-only. Stage 6 adds reviewed multilingual
generation and translation.

### Evaluator Service

Responsibilities:

- check generated output against retrieved context
- identify unsupported claims
- detect empty-context or insufficient-context generation attempts
- record prompt-injection resistance test outcomes when applicable
- return pass, warn, fail, or refused status
- persist evaluation metadata with the walkthrough run

Security constraints:

- evaluation failure blocks silent publication
- unsupported claims must be flagged, refused, or regenerated
- evaluator provider output is untrusted and must be schema-validated
- deterministic checks are preferred before model-as-judge evaluation

### Avatar Rendering Adapter

Responsibilities:

- define the future boundary for avatar/video generation
- accept grounded script, optional audio, optional subtitles, avatar profile, consent
  metadata, disclosure text, and provider mode
- return render status, output artifact reference, provider metadata, fallback reason,
  latency, and estimated cost

Security constraints:

- mock provider is default
- no avatar rendering in Stage 4
- no face cloning or voice cloning in MVP
- explicit documented consent is required for any cloned identity feature
- AI-generated avatar/voice disclosure is mandatory
- provider responses and callbacks are untrusted until validated
- Wav2Lip remains disabled by default

### Provider Abstraction

Core logic depends on internal interfaces:

- `LLMProvider`
- `EmbeddingProvider`
- `TranslationProvider`
- `TTSProvider`
- `STTProvider`
- `AvatarProvider`
- `SubtitleProvider`
- `VideoRenderer`
- `StorageProvider`
- `VectorStoreProvider`
- `EvaluationProvider`
- `ObservabilityProvider`

Adapter rules:

- provider SDK imports live only in adapter modules
- provider keys come only from environment-backed configuration or a future secret
  manager
- local/dev/test defaults use mock or local providers
- real provider tests are opt-in and skipped without explicit credentials
- adapter responses are schema-validated before use
- adapter errors use structured, non-secret error codes
- every adapter requires contract tests before enabling

### Observability Pipeline

Responsibilities:

- emit structured events for uploads, ingestion, retrieval, generation, evaluation,
  provider calls, refusals, and errors
- correlate events with `trace_id`, `run_id`, `project_id`, and future `tenant_id`
- track provider mode, latency, token usage, estimated cost, cache hit, and status
- record audit events for security-relevant actions
- redact secrets and sensitive content before logging

Minimum Stage 4 run metadata:

- `run_id`
- `project_id`
- `request_id` or `trace_id`
- `audience`
- `requested_language`
- `depth`
- `style`
- `provider`
- `provider_mode`
- `retrieved_context_count`
- `context_refs`
- `evaluation_status`
- `unsupported_claim_count`
- `latency_ms`
- `estimated_cost`
- `error_code`
- `created_at`

### CI Quality Gates

CI remains the remote enforcement layer. The architecture requires these checks as
the staged product grows:

- issue-linked PR validation
- branch and direct-main-push guardrails
- least-privilege workflow permissions
- secret scanning
- dependency scanning
- license and third-party notice review
- markdown/documentation validation
- stage-aware local quality target through `make quality`
- no mandatory paid provider keys in local/dev/test/CI
- architecture-impacting changes require ADR updates
- PRD-impacting changes require traceability updates
- future backend/frontend test wrappers
- future OWASP ZAP baseline scan after a web surface exists
- future eval report gate where failing evals block merge
- future security report gate where critical/high findings block merge

## Target Data Flow

### Upload And Ingestion

```text
Frontend upload form
-> Backend upload endpoint
-> upload validation
-> safe artifact storage
-> ingestion worker
-> deterministic chunking
-> embedding provider
-> vector-store adapter
-> chunk metadata store
-> observability events
```

Validation gates:

- allowed extension and content type
- size and corpus limits
- sanitized filename
- generated storage path
- checksum recorded
- mandatory obvious-secret screening before non-local provider egress

### Grounded Script Run

```text
Walkthrough request
-> Backend API validation
-> project authorization
-> RAG service retrieval
-> prompt assembly with context as data
-> LLM provider adapter
-> structured output validation
-> evaluator service
-> run/output persistence
-> observability events
-> frontend display with warnings
```

Failure behavior:

- no context: refusal
- any unsupported project factual claim: failed evaluation and no accepted output
- provider error: structured error and fallback path
- evaluation unavailable: fail closed for publication

### Future Avatar/Media Run

```text
Grounded script
-> translation/localization service
-> optional subtitle provider
-> optional TTS provider
-> avatar rendering adapter
-> video renderer
-> output storage
-> disclosure and audit metadata
```

This path is future Stage 6 and Stage 7 scope. Stage 2 only defines the boundary.

## Trust Boundaries

Untrusted inputs:

- browser input
- uploaded documents
- filenames and metadata
- user prompts
- transcripts
- retrieved text that originated from uploads
- LLM output
- evaluator output
- provider responses and callbacks
- vector-store records until metadata is checked

Trusted after validation:

- server-side configuration
- environment-backed provider selection
- generated internal identifiers
- sanitized metadata
- persisted run records
- approved context references
- structured audit events after redaction

## Synthetic Local Principal

Stage 4 is allowed to run in local single-user mode, but it must not treat possession
of a project ID as authorization. The local mode uses a synthetic principal:

- `tenant_id = tenant_local`
- `owner_id = user_local`
- `actor_id = user_local`

Every project-scoped read and write checks this synthetic principal before data
access. Future authentication replaces the principal source, not the authorization
predicate. This keeps project and tenant filters present from the first data model
and avoids later risky backfills.

## Document Approval State Machine

Approved project knowledge is a first-class trust primitive. Uploading a document
does not make it retrievable.

Allowed document states:

- `UPLOADED`: file passed transport-level validation and is stored safely
- `QUARANTINED`: file requires review because screening found suspicious content
- `APPROVED`: file is eligible for ingestion, embedding, retrieval, and provider
  egress
- `REJECTED`: file is retained only for audit metadata or deleted by policy
- `INGESTED`: approved file was chunked and indexed
- `DELETED`: source file is unavailable and derived records are invalidated

Only `APPROVED` and `INGESTED` documents can contribute chunks to RAG. Stage 4 may
offer a local explicit approval action, but it may not silently treat every upload as
approved project knowledge.

## Stage 4 Resource Budgets

These are safety budgets for the first implementation slice, not product-scale
targets:

| Resource | Stage 4 limit |
|---|---:|
| File size | 1 MiB per `.md` or `.txt` file |
| Documents per project | 10 active source documents |
| Project corpus size | 5 MiB total uploaded text |
| Chunk size | 800 tokens target, 1,000 tokens maximum |
| Chunk overlap | 100 tokens maximum |
| Chunks per document | 100 maximum |
| Chunks per project | 200 active chunks |
| Embedding batch size | 32 chunks maximum |
| Retrieval `topK` | 6 chunks maximum |
| Prompt context budget | 6,000 input tokens maximum |
| Generated script length | 1,200 words or 2,500 output tokens maximum |
| Unsupported claims evaluated | 100 claims maximum per run |
| Regeneration attempts | 1 automatic retry maximum |
| Generation timeout | 60 seconds per provider call |
| Evaluation timeout | 30 seconds per evaluation pass |
| Initial page size | 20 items, 100 maximum |

Stage 4 quality must fail if implementation exceeds these budgets without updating
this architecture and the corresponding ADR.

## Queue And Backpressure Contract

Ingestion and walkthrough generation are modeled as jobs even when Stage 4 executes
them synchronously for local simplicity.

Required state transitions:

```text
QUEUED -> RUNNING -> COMPLETED
QUEUED -> RUNNING -> FAILED
QUEUED -> RUNNING -> REFUSED
QUEUED -> CANCELLED
```

Operational limits:

- one active ingestion job per project
- one active generation job per project
- queue capacity of 20 pending jobs in local mode
- retry budget of one retry for retryable provider or storage failures
- non-retryable validation, authorization, unsupported-claim, and policy failures do
  not retry
- duplicate idempotency keys return the original job/result without re-running
- full queues return `429` or `503` with structured error code `BACKPRESSURE`
- timed-out jobs persist `FAILED` with timeout reason and audit event

## Provider Adapter Contract

Provider abstraction is a contract, not only a list of names. Every provider adapter
must define:

- typed request schema
- typed response schema
- capability metadata, including streaming, max tokens, supported languages, and
  whether external egress occurs
- timeout value and retry policy
- structured error taxonomy: `VALIDATION_ERROR`, `AUTH_ERROR`, `RATE_LIMITED`,
  `TIMEOUT`, `PROVIDER_UNAVAILABLE`, `POLICY_BLOCKED`, `SCHEMA_MISMATCH`
- redaction behavior for request, response, prompt, trace, and error fields
- data-retention and provider-egress metadata
- deterministic mock fixture for local/dev/test

Core services consume only this contract. Provider-native objects, response blobs,
and IDs stay behind adapters or in provider metadata.

## Observability Event Contract

Every event uses the same envelope:

- `event_id`
- `event_name`
- `trace_id`
- `project_id`
- `tenant_id`
- `actor_id`
- `resource_type`
- `resource_id`
- `outcome`
- `reason_code`
- `created_at`
- redacted `metadata`

Required Stage 4 operational metrics:

- p50, p95, and p99 latency for upload, ingestion, retrieval, generation, and
  evaluation
- `queue_depth`
- worker backlog age
- retry count
- timeout count
- upload bytes
- chunk count
- retrieved chunk count
- prompt input tokens
- output tokens
- rate-limit hits
- `cost_budget_exceeded`

Observability sink failure must not mark a generated output as accepted without a
persisted audit event.

## Data Isolation

Isolation rules:

- every data record includes `project_id`
- future multi-user records include `tenant_id` and `owner_id`
- retrieval filters must include `project_id` and future `tenant_id`
- provider calls include only context for the authorized project
- artifact paths use generated IDs, not user filenames
- logs include identifiers and counts, not raw secrets
- export bundles must preserve project boundaries

## Storage Architecture

Local-first defaults:

- metadata store: local database or file-backed store selected in Stage 3/4
- artifact store: local filesystem behind `StorageProvider`
- vector store: ChromaDB or equivalent behind `VectorStoreProvider`

Portability requirements:

- storage adapters expose export and import paths for project data
- embeddings can be regenerated from canonical chunks
- vector-store contents are derived artifacts, not the source of truth
- output artifacts include provenance metadata

## Provider Routing

Provider routing is configuration-driven:

- local/dev/test use mock/local providers by default
- real LLM providers require explicit environment configuration
- premium providers are disabled unless explicitly selected and configured
- provider selection is recorded per run
- fallback behavior is visible in metadata

Routing must never be controlled by uploaded content or generated model output.

## Deployment Posture

Stage 2 does not introduce deployment code. The target posture is:

- local-first engineering mode
- single-user/local project mode before multi-tenant cloud mode
- explicit provider egress configuration
- future cloud deployment only after Stage 3 foundation and Stage 4 slice readiness

## Architecture Guardrails

- No product implementation before the approved Stage 4 vertical slice.
- No backend, frontend, RAG, provider, avatar, Docker, database, or runtime product code in Stage 2.
- No direct SDK imports in domain logic.
- No mandatory paid providers in tests.
- No generated claims without context references.
- No silent evaluation failures.
- No secret logging.
- No cross-project retrieval.
- No avatar/voice cloning without explicit consent workflow.

## Related Documents

- `docs/ADR/0001-system-architecture.md`
- `docs/ADR/0002-rag-storage.md`
- `docs/ADR/0003-llm-provider-routing.md`
- `docs/ADR/0004-avatar-provider-adapter.md`
- `docs/ADR/0005-observability-and-evals.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`
- `docs/THREAT_MODEL.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/PORTABILITY_STRATEGY.md`
