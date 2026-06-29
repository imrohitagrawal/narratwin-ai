# Observability and Cost

## Goal

NarraTwin AI must make every walkthrough run traceable, debuggable, and cost-aware from the first usable slice.

The MVP does not need a full dashboard, but it must store enough metadata to explain what happened in each run.

## Track per run

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
- `p95`
- `cache_hit`
- `token_usage` when available
- `estimated_cost` when available
- `retrieved_context_count`
- `queue_depth`
- `evaluation_status`
- `unsupported_claim_count`
- `error_code`
- `created_at`

## Event Schema

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

## Cost controls

- cache scripts using request checksum, approved chunk checksums, prompt template
  version, provider, model, and evaluator version
- cache translations only after Stage 6 approval
- cache audio metadata only after Stage 6 approval
- cache video metadata only after Stage 7 approval
- avoid repeated generation unless requested through a distinct idempotency key
- default to free engineering mode
- use mock providers for tests
- keep premium providers optional
- store provider and estimated cost per run

Cache rules:

- cache TTL is 24 hours in local Stage 4 mode
- cache size is capped at 100 generated-script entries per project
- cache hits must reuse or revalidate an evaluation result
- document approval, deletion, chunking-strategy change, embedding-model change, or
  prompt-template change invalidates affected cache entries

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

- queue depth greater than 20
- generation p95 greater than 60 seconds
- evaluation p95 greater than 30 seconds
- any cost above USD 0.00 in mock/local mode
- unsupported-claim rate above 0 for accepted outputs

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
