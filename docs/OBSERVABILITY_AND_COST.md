# Observability and Cost

## Goal

NarraTwin AI must make every walkthrough run traceable, debuggable, and cost-aware from the first usable slice.

The MVP does not need a full dashboard, but it must store enough metadata to explain what happened in each run.

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

## Release blocker list

Do not merge a slice if:

- run output cannot be traced to project and context
- evaluation result is not stored
- provider errors disappear without logs
- repeated generation has no cache or cost metadata plan
- premium provider usage is not visible in metadata
