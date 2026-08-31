# Observability and Cost

## Goal

NarraTwin AI must make every walkthrough run traceable, debuggable, and cost-aware from the first usable slice.

The MVP does not need a full dashboard, but it must store enough metadata to explain what happened in each run.

## Publication-safe telemetry

Logs, traces, metrics labels, search queries, and provider request metadata are
publication surfaces under `PublicationBoundaryV1`. Telemetry carries the most
restrictive source classification and must use bounded identifiers rather than
raw internal/restricted content. Observability cannot promote data to `PUBLIC`,
and a public dashboard requires a separate reviewed projection contract.

## RunMetadata

Run metadata is persisted business/run state. It is not a log event and not an
aggregate metric.

- `run_id`
- `project_id`
- `tenant_id`
- `actor_id`
- `language`
- `audience`
- `depth`
- `style`
- `provider`
- `provider_mode`
- `latency_ms`
- `cache_hit`
- `token_usage` when available
- `estimated_cost` when available
- `retrieved_context_count`
- `queue_depth`
- `evaluation_status`
- `unsupported_claim_count`
- `error_code`
- `created_at`

## EventEnvelope

Every structured event uses this envelope:

- `event_id`
- `event_name`
- `trace_id`
- `tenant_id`
- `actor_id`
- `project_id`
- `resource_type`
- `resource_id`
- `outcome`
- `reason_code`
- `created_at`
- redacted `metadata`

Metadata must never contain provider keys, raw auth tokens, private certificates,
full raw uploads, full prompts, or unredacted provider payloads.

## MetricPoint

Metric points are numeric time-series data for aggregation and alerting. They must
not contain raw prompts, uploads, provider payloads, generated script text, user
emails, request IDs, or other high-cardinality values.

Fields:

- `metric_name`
- `tenant_id`
- optional `project_id`
- `stage`
- `provider_mode`
- `value`
- `unit`
- `timestamp`
- bounded `labels`

Aggregate metrics compute p50, p95, and p99 from `latency_ms`; p95 is never stored
as a per-run field.

## Structured log events

### Upload events

- `knowledge_upload_received`
- `knowledge_upload_rejected`
- `knowledge_upload_stored`

### Ingestion events

- `knowledge_ingestion_started`
- `knowledge_chunk_created`
- `knowledge_ingestion_completed`
- `knowledge_ingestion_failed`

### Generation events

- `walkthrough_generation_requested`
- `context_retrieval_completed`
- `llm_generation_completed`
- `llm_generation_failed`

### Evaluation events

- `evaluation_completed`
- `unsupported_claim_detected`
- `empty_context_refused`
- `prompt_injection_detected`

### Budget and operations events

- `queue_depth_changed`
- `rate_limit_hit`
- `provider_timeout`
- `cost_budget_exceeded`
- `cache_hit`
- `cache_invalidated`

## Cost Controls And Cache Key Safety

- cache generated scripts using a key that includes `tenant_id`, `project_id`,
  `actor_id`, audience, requested language, depth, style, normalized prompt
  checksum, approved document IDs, approved document checksums, chunk IDs, chunk
  checksums, chunking strategy version, embedding provider, embedding model, vector
  index version, retrieval strategy version, retrieval topK, retrieval score
  threshold, prompt template version, LLM provider, LLM model, evaluator version,
  evaluation policy version, evaluation schema version, provider mode, and safety
  policy version
- canonical cache-key field names are `tenant_id`, `project_id`, `actor_id`,
  `audience`, `requested_language`, `depth`, `style`,
  `normalized_prompt_checksum`, `approved_corpus_version`, `approval_epoch`,
  `approved_document_ids`, `chunk_ids`, `document_checksums`,
  `chunk_checksums`, `chunking_strategy_version`, `retrieval_strategy_version`,
  `retrieval_top_k`, `retrieval_score_threshold`, `embedding_provider`,
  `embedding_model`, `vector_index_version`, `evaluation_policy_version`,
  `evaluation_schema_version`, `provider_mode`, `llm_provider`, `llm_model`,
  `provider`, `model`, `evaluator_version`, `prompt_template_version`,
  `safety_policy_version`, and `secret_screening_version`
- canonical cache invalidation triggers are `approval_change`, `quarantine`,
  `rejection`, `deletion`, `source_checksum_change`,
  `chunking_strategy_change`, `embedding_provider_change`,
  `embedding_model_change`, `vector_index_rebuild`,
  `retrieval_strategy_change`, `retrieval_threshold_change`,
  `prompt_template_change`, `evaluator_version_change`,
  `evaluation_schema_change`, `safety_policy_change`, `provider_change`,
  `model_change`, and `unsupported_claim_evaluation_change`
- cache-hit revalidation fields are `document_status`, `approval_status`,
  `ingestion_status`, `deleted_at`, `tombstone_id`, `secret_screening_id`,
  `secret_screening_version`, `source_document_checksum`, and `chunk_checksum`
- never key generated outputs only by prompt text
- cache translations only after Stage 6 approval
- cache audio metadata only after Stage 6 approval
- cache video metadata only after Stage 7 approval
- avoid repeated generation unless requested through a distinct idempotency key
- default to free engineering mode
- use mock providers for tests
- keep premium providers optional
- store provider and estimated cost per run
- generated script output is capped at `generatedScriptWords = 1200` and
  `generatedScriptOutputTokens = 2500`

Cache rules:

- cache TTL is 24 hours in local Stage 4 mode
- cache size is capped at 100 generated-script entries per project
- cache hits must reuse or revalidate an evaluation result
- document approval change, quarantine, rejection, deletion, source checksum change,
  chunking strategy change, embedding provider/model change, vector index rebuild,
  retrieval strategy or threshold change, prompt template change, evaluator version
  change, evaluation schema change, safety policy change, provider/model change, or
  unsupported-claim evaluation change invalidates affected cache entries
- cache hits must re-check current approval, deletion, secret-screening, and
  tombstone state before returning accepted output

## Stage 4 Operational Metrics

Stage 4 records:

- p50, p95, and p99 latency by stage: upload, ingestion, retrieval, generation,
  evaluation, persistence, and API response
- queue_depth and oldest queued job age
- worker retry count
- timeout count
- upload bytes
- document count
- chunk count
- retrieved chunk count
- input token count
- output token count
- rate-limit hit count
- provider error count by error code
- estimated cost by provider mode
- `cost_budget_exceeded` events

Alert thresholds for local/free-provider modes:

- per-project queue depth greater than 20
- generation p95 greater than 60 seconds
- evaluation p95 greater than 30 seconds
- any cost above USD 0.00 in mock/local mode
- unsupported-claim rate above 0 for accepted outputs

Stage 4 Slice 1 implementation records lightweight response metadata in the
walkthrough response:

- `trace.traceId`
- `trace.latencyMs`
- `trace.inputTokens`
- `trace.outputTokens`
- `trace.estimatedCost`
- `provider.provider`
- `provider.providerMode`
- evaluation policy, schema, and safety policy versions

The mock/local provider path must always report estimated cost `0`.

## MVP observability rule

Every generated output must be linked to:

- source project
- source documents/chunks
- generation request parameters
- provider used
- evaluation result
- error or refusal reason when applicable

## Local operational status

`GET /api/v1/ops/status` reports bounded operational posture for the local
backend:

- whether optional file-backed durable state is enabled for Stage 4, Stage 6,
  and Stage 7
- non-sensitive state backend type, without filesystem paths
- record counts for project/document/run/idempotency/render/artifact metadata
- health, readiness, structured logging, walkthrough metrics instrumentation,
  metrics-endpoint exposure, production-alert posture, and Langfuse
  configuration flags

The endpoint must not expose raw uploads, prompts, generated outputs, provider
payloads, filesystem paths, environment values, or secrets.

## Future dashboard metrics

- time to first walkthrough
- generation success rate
- unsupported claim rate
- prompt-injection test pass rate
- average latency
- p95 latency
- cache hit rate
- estimated cost per run
- provider error rate
- language success rate

## Cut 1 narration observability

The Issue #382 domain emits bounded local events for draft creation, evaluation
required, evaluation result, speech approval, text-authority consumption, and
restore refusal. Allowed fields are event/reason code, bounded project ID,
narration version/state, counts, and checksums. Raw narration, retrieved/source
text, claims/support reasons, filenames, persisted bytes, paths, secrets, and
provider-shaped payloads are excluded.
Missing-receipt and detached-receipt snapshots use the same bounded
`restore_refused` event and expose no narration or raw persistence content.

No provider is called and no cost or real audio-duration observation is
created. The 90–120-second value is requirement metadata only; Issue #368 must
measure generated audio before it can record duration evidence.

## Release blocker list

Do not merge a slice if:

- run output cannot be traced to project and context
- evaluation result is not stored
- provider errors disappear without logs
- repeated generation has no cache or cost metadata plan
- premium provider usage is not visible in metadata

## Issue #368 optional Google TTS evidence

Implemented Google adapter telemetry is allowlisted metadata only: event/error code,
trace and request fingerprints, semantic presenter, provider mode, Europe region
label, attempt count, elapsed/byte/duration buckets, input/output token estimates,
reserved/committed/released/billable-unknown spend state, decoded validation
outcomes, retention/deletion state and non-content checksums. Narration, style
prompt, request/response payload, audio bytes, auth headers, credentials, tokens
and raw provider errors are excluded.

Gemini 2.5 Pro TTS pricing observed on 2026-08-10 was $1 per million input text
tokens and $20 per million output audio tokens, with 25 audio tokens per second
and no free allowance. Pricing and effective quota must be refreshed before
activation. Reserve before egress; commit accepted work; release only proven
pre-egress failure. A timeout after possible egress is billable-unknown, holds
the reservation, and is neither automatically retried nor refunded.

The adapter durably reserves one fingerprint before identity or transport,
commits valid responses, retains failed-billable and billable-unknown states,
and releases only failures proven before egress. Restore converts an interrupted
pending reservation to billable-unknown, preventing automatic duplicate spend.
Each reservation counts raw prompt-plus-text UTF-8 bytes conservatively as input
tokens, reserves the 120-second/3,000-token maximum output and its micro-USD
ceiling, then reconciles a valid response to measured duration at 25 output
tokens per second. A receipt already present under any prior config fingerprint
cannot reserve or egress again.
Enabled operation cannot run without durable state. An atomic adjacent lock is
held from disk refresh through egress and finalization, so separate adapter
instances cannot reserve or dispatch the same receipt concurrently. A crash may
retain that lock and intentionally requires reconciliation instead of replay.
The implementation and its tests create no provider cost observation and make
no real provider call.

The runtime adds only bounded metadata for activation/transport diagnostics:
error code, phase, egress-possible classification, checked-address count,
selected peer, TLS/SNI/port booleans, response-size bucket and elapsed bucket.
Tokens, authorization headers, credential type/path, quota-project value,
request/response bodies, prompts and audio remain excluded. A write or response
failure after a write is `egress_possible=true` and is never retried; a DNS,
connect or TLS failure before the write is pre-egress.

Quota-project observability is limited to presence/equality booleans and the
approved SHA-256. Request fingerprints bind `quotaProjectRequired=true`, that
hash, and the exact three outbound header names. They never bind or emit the raw
project value. A mismatch during initial ADC resolution or the immediate
pre-egress reload releases the unspent reservation and records no paid attempt.
## Issue #421 atomic grounding observability

Cut 1 grounding reuses existing bounded Stage 4 run/evaluation metrics. The
policy version and resulting supported/unsupported counts are sufficient for
local diagnosis; raw narration, proposition statements, source spans, facts
JSON, repository paths, and Git output are not log fields. Validation failures
remain generic and fail closed.

Source classification is checksum lineage, not a log dimension. Metrics must
not collapse `OWNER_ASSERTED` into an externally verified category or emit the
owner span text. The canonical Meera revision is 261 words, 1,904 UTF-8 bytes,
and SHA-256 `3edffc6169460546ae0bdee867fdeaf3c0ae383535e2976e0333f39c03ff614e`.

The repair performs local hashing, JSON validation, and a bounded local Git
object read when current source bytes differ from the pinned revision. It makes
no provider or telemetry call and has no paid-call cost. Issue #368 call and
US$2 ceilings remain untouched at zero during this branch.

For `CUT1_ATOMIC_FACTS_V1`, the local trace ID is created without entering the
OpenTelemetry or Langfuse adapters, even when ambient exporter or Langfuse
configuration exists. Local bounded logs and metrics remain available; no
external-capable observation context is consulted.

## Issue #459 T05B audio/caption authority observability

T05B exposes deterministic local outcomes only: authority count, quarantine
state, typed failure code, presenter ID, receipt checksum, audio/caption
checksums, decoded duration/format/signal measurements, derived configuration
checksum, commitment-manifest sequence/checksum, and authority checksum. Raw narration, audio, captions, provider payloads,
identity values, credentials, and private paths are excluded from logs.

This increment performs zero credential/environment lookups, network requests,
egress, synthesis attempts, retries, or spend. Test-only materialized results
and WAV/SRT fixtures are validation stimuli, not provider or cost evidence. Issue #368
retains all paid-attempt, billable-unknown, listening, retention, and deletion
accounting before any genuine artifact can advance.

## Issue #479 listening-authority observability

T05C exposes bounded local outcomes through typed error codes and counts only:
accepted decision count, presenter position, resolver/commitment failure class,
replay/revocation, stale authority, and state quarantine. Reviewer IDs,
artifact-author IDs, timestamps, raw media/text, provider payloads, credentials,
and private configuration are not log or metric dimensions.

Validation is local hashing, comparison, and bounded JSON persistence. It makes
no network or provider call, reads no ambient credential/environment state, and
creates no spend. A test pass or structural media result is never emitted as a
human-listening acceptance observation.
