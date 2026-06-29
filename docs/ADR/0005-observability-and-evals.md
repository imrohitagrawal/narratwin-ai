# ADR 0005: Observability and Evals

## Status

Accepted for Stage 2 planning.

## Date

2026-06-29

## Context

NarraTwin AI's value depends on generated outputs being reviewable. A walkthrough
script is not acceptable unless reviewers can see which project context supported it,
which provider produced it, whether evaluation passed, and what failure or refusal
path occurred.

## Decision

Make observability and evaluation metadata part of the core run contract from the
first implementation slice.

Each generated output must be linked to:

- project
- source documents and chunks
- request parameters
- provider and provider mode
- retrieval result
- evaluation result
- trace/run metadata
- latency and cost metadata where available
- error or refusal reason when applicable

Evaluation failures must not be hidden from the frontend.

Stage 4 acceptance requires deterministic evaluation with zero unsupported project
factual claims. Warning status is not allowed to mask unsupported facts.

Evaluation evidence includes `EvidenceSnapshot`, `ClaimSupport`, embedding
provider/model/version/dimension, vector store, retrieval threshold, and retrieval
strategy version. `FAILED` and `REFUSED` outputs are persisted for audit but exposed
publicly only as redacted failure/refusal metadata, never as accepted generated
scripts.

## Telemetry Schema Decision

`RunMetadata`, `EventEnvelope`, and `MetricPoint` are separate schemas:

- `RunMetadata` explains a run and stores durable run state
- `EventEnvelope` records discrete operational or audit events
- `MetricPoint` records aggregateable numeric measurements

No schema may carry provider keys, raw auth tokens, private certificates, full
uploads, full prompts, raw generated text for failed/refused runs, or unredacted
provider payloads.

## Alternatives Considered

### Add observability after features work

Rejected because AI behavior is difficult to debug after the fact without trace and
evaluation metadata.

### Store only the final generated script

Rejected because it loses grounding, provider, cost, and safety evidence.

### Rely only on model self-certification

Rejected because provider output is untrusted and must be checked against retrieved
context.

## Consequences

Positive:

- reviewers can audit generated output
- unsupported claims can be measured
- provider cost and latency can be controlled
- prompt-injection and refusal behavior can become regression tests

Negative:

- run storage model is more detailed
- eval fixtures and reports require maintenance
- UI must expose warnings instead of showing only polished output

## Required Events

- `knowledge_upload_received`
- `knowledge_upload_rejected`
- `knowledge_upload_stored`
- `knowledge_ingestion_started`
- `knowledge_ingestion_completed`
- `context_retrieval_completed`
- `walkthrough_generation_requested`
- `llm_generation_completed`
- `evaluation_completed`
- `unsupported_claim_detected`
- `empty_context_refused`
- `prompt_injection_detected`
- `provider_call_failed`
- `queue_depth_changed`
- `rate_limit_hit`
- `cost_budget_exceeded`
- `cache_invalidated`

Every event uses a shared envelope with `event_id`, `event_name`, `trace_id`,
`tenant_id`, `actor_id`, `project_id`, `resource_type`, `resource_id`, `outcome`,
`reason_code`, `created_at`, and redacted metadata.

`evaluation_completed` metadata includes `evaluation_status`,
`unsupported_claim_count`, `context_ref_coverage`, `embedding_model`, and
`evaluator_version`. `unsupported_claim_detected` metadata includes `tenant_id`,
`project_id`, `run_id`, `evaluation_id`, `claim_id`, `reason_code`, and severity.

## Required Evaluation Outcomes

- `PASSED`
- `WARNING`
- `FAILED`
- `REFUSED`

## Related Documents

- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/DATA_MODEL.md`
- `docs/API_CONTRACT.md`
