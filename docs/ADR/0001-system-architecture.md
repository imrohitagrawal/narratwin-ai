# ADR 0001: System Architecture

## Status

Accepted for Stage 2 planning.

## Date

2026-06-29

## Context

NarraTwin AI must support grounded walkthrough generation, future multilingual
scripts, future subtitles, future voice, future avatar/video rendering, and future
interactive avatar Q&A without creating provider lock-in or requiring paid provider
keys for local development and tests.

The repository is still pre-implementation. Stage 2 may define architecture,
security, AI safety, and portability, but must not add backend, frontend, RAG,
provider, Docker, database, or runtime product code.

## Decision

Use a modular, provider-agnostic architecture with explicit boundaries:

- frontend
- backend API
- ingestion worker
- RAG service
- script generation service
- evaluator service
- avatar rendering adapter
- provider abstraction
- storage and vector-store adapters
- observability pipeline
- CI quality gates

The first implementation slice will build only the project upload to grounded script
generation path. Avatar, voice, subtitles, video, premium providers, and interactive
Q&A remain future stage scope.

Stage 4 local mode still uses the production-shaped identity and authorization
contract through `tenant_local` and `user_local`. Uploaded knowledge must pass an
approval state before ingestion. Unsupported factual claims fail acceptance rather
than becoming warnings.

## Alternatives Considered

### Provider-first implementation

Start directly with Gemini, HeyGen, Tavus, D-ID, ElevenLabs, or other SDKs.

Rejected because it would make tests depend on real keys, increase cost risk, and
couple core logic to providers before safety is proven.

### Media-first implementation

Build avatar/video output before grounded script generation.

Rejected because polished media without grounded evaluation would amplify
unsupported claims and weaken the product's trust promise.

### Full platform skeleton

Scaffold all backend, frontend, provider, storage, and media surfaces at once.

Rejected because it encourages broad shallow code before a reviewed vertical slice.

## Consequences

Positive:

- provider SDKs can be replaced without rewriting domain logic
- local/dev/test can run with mocks and local storage
- generated outputs can be traced to source chunks and evaluations
- future media providers inherit safety, consent, and disclosure boundaries
- reviewers can assess one vertical slice at a time

Negative:

- more interface design is required before implementation
- adapter contract tests become mandatory
- first visible output is text-only rather than media-rich

## Guardrails

- No product implementation in Stage 2.
- Stage 4 starts with grounded script generation only.
- Provider keys stay out of frontend, prompts, logs, tests, and committed files.
- Evaluation status must be stored and shown before output is treated as accepted.
- Stage 4 uses hard resource budgets, idempotent writes, and queue/job state even
  when local execution is synchronous.

## Remediation Locks

Stage 4 implementation must include:

- `IdempotencyRecord` before mutating side effects
- split knowledge state: `document_status`, `approval_status`, and
  `ingestion_status`
- job leases, attempts, and committed outbox events
- retrieval strategy v1 thresholds and deterministic refusal behavior
- same-egress-class provider fallback only
- cache keys that include retrieval, evaluation, provider, safety, and approved
  corpus versions
- separate `RunMetadata`, `EventEnvelope`, and `MetricPoint` schemas
- public run responses that omit raw generated text for `FAILED` and `REFUSED`
  outcomes

## Related Documents

- `docs/ARCHITECTURE.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`
- `docs/THREAT_MODEL.md`
