# ADR 0003: LLM Provider Routing

## Status

Accepted for Stage 2 planning.

## Date

2026-06-29

## Context

NarraTwin AI needs LLM, embedding, translation, and evaluation capabilities, but
local development and CI must not require real paid provider keys. Provider choice
must be auditable because generated outputs need cost, trace, and evaluation
metadata.

## Decision

Route all LLM-like work through internal provider interfaces:

- `LLMProvider`
- `EmbeddingProvider`
- `TranslationProvider`
- `EvaluationProvider`

Provider selection is configuration-driven and server-side. Mock/local providers are
the default for local/dev/test. Real providers require explicit environment-backed
configuration and are recorded per run.

Uploaded content, user prompts, and model output must never control provider routing.

The provider adapter contract includes typed request/response schemas, capability
metadata, timeout/retry policy, structured error taxonomy, redaction behavior,
provider data-retention metadata, and deterministic mock fixtures.

## Routing Rules

- backend services call internal interfaces only
- provider SDK imports live only in adapter modules
- provider keys come only from environment-backed configuration or a future secret
  manager
- provider mode is stored on every run
- fallbacks are explicit and visible in metadata
- real provider tests are opt-in and skipped without explicit credentials
- premium providers are disabled by default

## Alternatives Considered

### Direct SDK calls in services

Rejected because it creates provider lock-in, makes tests expensive, and increases
the chance of accidental paid API usage.

### Frontend provider calls

Rejected because it exposes provider keys and bypasses backend security controls.

### User-selectable arbitrary provider config

Rejected for MVP because it expands the attack surface and complicates consent,
retention, cost, and data egress review.

## Consequences

Positive:

- provider replacement is possible
- local tests remain keyless
- cost and provider metadata are consistent
- prompt injection cannot route calls to premium providers

Negative:

- adapter contracts must be maintained
- provider capability differences need normalization
- provider-specific features may be delayed until adapter review

## Security Requirements

- provider keys are never exposed to frontend clients
- prompts never contain provider secrets
- prompt content is scoped to one project and future tenant
- provider responses are schema-validated
- provider errors are redacted before logging or display
- secret screening is mandatory before non-local provider egress
- model-as-judge evaluation is not part of Stage 4 acceptance unless a future ADR
  defines a judge schema and deterministic fallback

## Related Documents

- `docs/API_CONTRACT.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/OBSERVABILITY_AND_COST.md`
