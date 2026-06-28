# ADR 0000: Architecture Decision Record Process

## Status

Accepted

## Context

NarraTwin AI is a provider-agnostic AI product with RAG, LLM generation, evaluation, tracing, video/avatar provider boundaries, and free-first execution requirements. Architecture changes can silently weaken safety, cost control, provider abstraction, or testability if they are not recorded.

## Decision

All architecture-impacting changes must include an ADR update under `docs/ADR/`.

An ADR is required when a change affects:

- provider interfaces or adapters
- storage, vector store, retrieval, or ingestion design
- evaluation gates
- LLM tracing or observability design
- security/privacy architecture
- CI/CD quality gates
- external service integration
- paid provider enablement
- video/avatar/TTS/STT provider boundaries

## Consequences

- Pull requests touching architecture-sensitive paths are blocked by CI unless an ADR is included.
- Codex must not change architecture implicitly.
- Reviewers have a durable decision trail.
- Future portfolio readers can understand trade-offs, not just code.

## Related guardrails

- `docs/REPOSITORY_GUARDRAILS.md`
- `docs/TRACEABILITY.md`
- `.github/workflows/quality-gates.yml`
- `scripts/guardrails_check.py`
