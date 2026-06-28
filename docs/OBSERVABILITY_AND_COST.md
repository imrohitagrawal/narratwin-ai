# Observability and Cost

## Goal

NarraTwin AI must make every walkthrough run traceable, debuggable, and cost-aware from the first usable slice.

The MVP does not need a full dashboard, but it must store enough metadata to explain what happened in each run.

## Track per run

- `run_id`
- `project_id`
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
- `evaluation_status`
- `unsupported_claim_count`
- `error_code`
- `created_at`

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

## Cost controls

- cache scripts
- cache translations
- cache audio metadata
- cache video metadata
- avoid repeated generation unless requested
- default to free engineering mode
- use mock providers for tests
- keep premium providers optional
- store provider and estimated cost per run

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
