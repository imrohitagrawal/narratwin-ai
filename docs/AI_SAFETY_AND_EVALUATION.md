# AI Safety and Evaluation v1.0

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-29
- Implementation status: evaluation architecture only; product implementation blocked

## Safety Goal

NarraTwin AI must generate useful walkthroughs without inventing project facts,
leaking secrets, obeying malicious uploaded instructions, or hiding uncertainty.

The first AI quality target is a grounded, evaluated, stored walkthrough script. It
is not avatar realism, voice quality, or media polish.

## Safety Principles

- Approved project knowledge is the source of truth.
- Uploaded knowledge is untrusted data, not instructions.
- Generated project-specific claims require context references.
- Empty or insufficient context produces refusal.
- Provider output is untrusted until parsed, validated, and evaluated.
- Evaluation status must be visible to the user and reviewer.
- Paid providers remain optional and disabled for local/dev/test.

## AI Risk Classes

| Risk | Example | Required mitigation |
|---|---|---|
| Unsupported claim | Script claims a metric not in uploaded docs | unsupported-claim evaluator and context refs |
| Prompt injection | Uploaded markdown says "ignore prior rules" | context-as-data prompt pattern and injection tests |
| Data leakage | Provider prompt includes another project | project/tenant-scoped retrieval filters |
| Secret leakage | Uploaded docs contain API keys | secret screening before non-local egress |
| Unsafe output handling | LLM output rendered as HTML | output encoding and schema validation |
| Provider drift | Provider returns unexpected schema | adapter-level response validation |
| Cost abuse | repeated generation loop | rate limits, token caps, and run cache |
| Media misuse | avatar/voice implies real person consent | consent metadata and AI disclosure |

## Evaluation Dimensions

Required from the first AI slice:

- groundedness
- unsupported claims
- source context traceability
- empty-context refusal
- prompt-injection resistance
- audience fit
- depth and style fit
- output structure validity
- provider fallback behavior
- latency and cost metadata

Future stages add:

- translation meaning preservation
- language consistency
- subtitle format validity
- voice disclosure checks
- avatar/video disclosure checks
- consent checks for any identity media

## Generation Safety Flow

```text
Validated walkthrough request
-> project-scoped retrieval
-> context quality check
-> prompt assembly with context marked as untrusted evidence
-> provider adapter call
-> structured output validation
-> unsupported-claim evaluation
-> refusal, warning, or accepted output
-> persisted run and evaluation metadata
-> UI display with context refs and warnings
```

Hard failures:

- no retrieved context
- context from wrong project or tenant
- malformed provider output
- evaluator unavailable when publication would otherwise proceed silently
- any unsupported project factual claim in Stage 4
- prompt-injection instruction detected as controlling behavior

## Prompt Injection Controls

Prompt design requirements:

- system and developer rules are fixed server-side
- retrieved context is delimited and described as untrusted evidence
- uploaded instructions are never promoted to system or developer messages
- model is instructed to refuse unsupported project facts
- model is instructed to emit context references for project-specific claims
- provider routing, tool permissions, and storage paths are never model-controlled

Required injection fixtures:

- uploaded document asks model to ignore system rules
- uploaded document asks model to reveal secrets
- uploaded document asks model to claim unsupported metrics
- uploaded document asks model to call a premium provider
- uploaded document contains markdown/HTML that should not execute

Acceptance:

- generated output ignores malicious instructions
- response remains grounded in approved context
- evaluation records the injection attempt when detected

## Unsupported-Claim Evaluation

The evaluator compares generated claims to retrieved context.

Minimum evaluator behavior:

- identify project-specific factual claims
- verify every extracted claim against retrieved chunks
- require context references for supported claims
- mark unsupported claims with reason and excerpt
- refuse when no support exists
- store status and unsupported-claim count
- fail or refuse when claim extraction exceeds the Stage 4 evaluation budget rather
  than partially evaluating only the first claims

Evaluation statuses:

- `PASSED`: no unsupported claims found
- `WARNING`: minor non-factual presentation or ambiguous content requiring user
  review
- `FAILED`: unsupported claims cannot be published silently
- `REFUSED`: context is missing, unsafe, or insufficient

Stage 4 must use deterministic or rule-backed evaluation as the minimum acceptance
gate. Model-as-judge evaluation is Stage 5 scope unless a later ADR defines a judge
schema, fallback rule, and deterministic baseline.

## Stage 4 Evaluation Policy

Stage 4 acceptance is intentionally strict:

- `PASSED`: `unsupported_claim_count = 0`, context-reference coverage is 100% for
  project-specific claims, schema validation passes, and no prompt-injection control
  failure is detected
- `WARNING`: allowed only for non-factual presentation issues such as tone, length,
  or audience-fit uncertainty; unsupported project factual claims cannot be warnings
- `FAILED`: one or more unsupported project factual claims, malformed provider
  output, failed schema validation, or evaluator timeout/unavailability after a run
  was created
- `REFUSED`: no approved context, no relevant retrieved chunks, unsafe retrieved
  context, prompt-injection control failure, or cross-project/cross-tenant context

Groundedness score is a decimal from `0.0` to `1.0`. Stage 4 requires `1.0` for
accepted output because every project-specific factual claim must have support.
Outputs with `FAILED` or `REFUSED` status must be persisted for audit but must not be
presented as accepted generated scripts.

## Evaluation Result Schema

Each generated run must store:

- `evaluation_id`
- `run_id`
- `project_id`
- `tenant_id`
- `evaluation_status`
- `groundedness_score`
- `unsupported_claims`
- `unsupported_claim_count`
- `context_refs`
- `claim_supports`
- `context_ref_coverage`
- `evaluator_version`
- `prompt_template_version`
- `retrieval_strategy_version`
- `retrieval_top_k`
- `retrieval_score_threshold`
- optional `error_code`
- `refusal_reason`
- `prompt_injection_detected`
- `language_check`
- `audience_fit_check`
- `output_schema_valid`
- `provider`
- `provider_mode`
- optional `model`
- `embedding_provider`
- `embedding_model`
- `embedding_model_version`
- `embedding_dimension`
- `vector_store`
- `latency_ms`
- optional `estimated_cost`
- `created_at`

Unsupported-claim item fields:

- `claim_id`
- `tenant_id`
- `project_id`
- `run_id`
- `claim_text`
- `claim_status`
- `supporting_context_refs`
- `reason_code`
- `reason`
- `severity`

Required JSON semantics:

- all IDs are required
- `evaluation_status` is one of `PASSED`, `WARNING`, `FAILED`, `REFUSED`
- `groundedness_score` is a number from `0.0` through `1.0`
- `unsupported_claims` is an array and is empty for `PASSED`
- `claim_supports` records support, ambiguity, or unsupported status for every
  extracted project-specific claim
- `context_ref_coverage = 1.0` is required for `PASSED`
- `context_refs` is an array of claim-level references, not only run-level refs
- `refusal_reason` is required for `REFUSED`
- `error_code` is required for evaluator timeout, provider schema mismatch, or
  policy failure
- `prompt_template_version`, `retrieval_strategy_version`, `evaluator_version`,
  `embedding_provider`, `embedding_model`, `embedding_model_version`,
  `embedding_dimension`, `vector_store`, `retrieval_top_k`, and
  `retrieval_score_threshold` are required for drift analysis
- persisted claim text and excerpts are redacted and truncated to 500 characters per
  field

Claim extraction rules:

- deterministic Stage 4 extraction identifies project-specific factual claims before
  support checking
- non-factual style, tone, and transition text can be excluded from factual support
  scoring only when the exclusion is recorded
- if extracted project-specific factual claims exceed the Stage 4 cap of 100, the
  run fails with `CLAIM_BUDGET_EXCEEDED`
- no unevaluated project-specific factual claim can be included in accepted output

## Context Reference Requirements

Every project-specific paragraph or claim must be linked to one or more
claim-level context references.

Context reference fields:

- `context_ref_id`
- `chunk_id`
- `document_id`
- `project_id`
- `tenant_id`
- `source_filename`
- `chunk_index`
- optional `line_start`
- optional `line_end`
- `checksum`
- `claim_id`
- `script_span_start`
- `script_span_end`
- `evidence_snapshot`

`EvidenceSnapshot` fields:

- `evidence_snapshot_id`
- `tenant_id`
- `project_id`
- `document_id`
- `chunk_id`
- `source_filename`
- `chunk_index`
- `source_document_checksum`
- `chunk_checksum`
- `chunking_strategy_version`
- `retrieval_score`
- `redacted_excerpt`
- `excerpt_start`
- `excerpt_end`
- `redaction_flags`
- `captured_at`
- `snapshot_checksum`

Claim-level context references are mandatory. A run-level context list can support
display, but it cannot satisfy grounding by itself.

The frontend must show references or make them inspectable. It must not present a
failed evaluation as clean final output.

## Refusal Rules

Canonical retrieval refusal reasons:

- `EMPTY_CONTEXT`
- `LOW_RETRIEVAL_CONFIDENCE`
- `AMBIGUOUS_CONTEXT`
- `CROSS_PROJECT_CONTEXT`
- `UNSAFE_CONTEXT`

The system must refuse when:

- no approved project context exists (`EMPTY_CONTEXT`)
- retrieval returns no relevant chunks or only below-threshold chunks
  (`LOW_RETRIEVAL_CONFIDENCE`)
- top chunks conflict and cannot support one grounded answer (`AMBIGUOUS_CONTEXT`)
- the user asks for facts outside approved context
- uploaded content attempts to override safety rules
- retrieved context is unsafe (`UNSAFE_CONTEXT`)
- provider output is malformed or unsafe
- evaluation cannot run and the output would otherwise be published
- cross-project or cross-tenant context is detected (`CROSS_PROJECT_CONTEXT`)

Refusals should be specific enough for the user to fix source knowledge, but must
not expose secrets, stack traces, provider internals, or hidden prompts.

## UI Evaluation State Matrix

| Evaluation status | UI behavior |
|---|---|
| `PASSED` | Show generated script, context refs, and trace metadata |
| `WARNING` | Show generated script with a warning banner and reviewer action |
| `FAILED` | Do not show as accepted output; show failure reason and unsupported claims |
| `REFUSED` | Show refusal reason and remediation guidance, not generated script text |

The frontend must display unsupported-claim count, evaluation status, and context
reference inspection affordance. It must not collapse `FAILED` or `REFUSED` into a
generic success state.

Public `FAILED` and `REFUSED` responses must not expose `scriptText`, raw provider
output, hidden prompts, stack traces, or unredacted evidence. They may expose only
failure/refusal metadata, redacted unsupported excerpts, and remediation guidance.

## Provider Safety

Provider adapter requirements:

- validate request and response schemas
- enforce token and output length caps
- record provider mode and model identifier where available
- redact provider errors before returning to users
- expose retryable vs non-retryable errors
- avoid real provider calls in local/dev/test unless explicitly configured
- never put secrets or cross-project data into prompts

## Evaluation Test Plan

Stage 4 minimum tests:

- happy path grounded walkthrough
- empty project context refusal
- retrieval miss refusal
- unsupported claim detection
- mixed supported/unsupported output handling
- prompt injection inside uploaded markdown
- generated output includes context references
- no paid provider key required
- output is rendered safely as text
- run metadata includes provider mode and trace ID

## Evaluation Fixture Contract

Stage 4 must include deterministic fixtures with these exact outcomes:

| Fixture | Input condition | Expected status | Required evidence |
|---|---|---|---|
| `happy_path_grounded` | approved markdown contains every project fact used | `PASSED` | claim-level context refs and `unsupported_claim_count = 0` |
| `empty_context` | project has no approved chunks | `REFUSED` | persisted eval with `refusal_reason = EMPTY_CONTEXT` |
| `retrieval_miss` | approved chunks do not answer request | `REFUSED` | retrieval count `0` or below threshold |
| `unsupported_metric` | output claims an unprovided metric | `FAILED` | unsupported claim with severity `HIGH` |
| `prompt_injection_ignore_rules` | uploaded markdown says to ignore rules | `PASSED` or `REFUSED` | injection detected or neutralized event |
| `cross_project_chunk` | retrieval attempts to include another project | `REFUSED` | isolation failure event and no provider call |
| `evaluator_timeout` | evaluator cannot complete | `FAILED` | stored error code `EVALUATOR_TIMEOUT` |

Each fixture records expected audit events, evaluation JSON, UI state, and whether a
provider call is allowed.

Stage 5 expansion:

- regression fixture suite for supported, unsupported, and ambiguous claims
- prompt-injection corpus
- evaluator false positive/false negative review
- eval report artifact that blocks merge on failure
- trend metrics for unsupported-claim rate

Stage 6 and Stage 7 expansion:

- translation meaning preservation
- subtitle structure checks
- TTS fallback checks
- avatar/video provider contract checks
- AI disclosure and consent checks

## Metrics

Quality metrics:

- grounded walkthrough success rate
- unsupported-claim rate
- empty-context refusal pass rate
- prompt-injection refusal pass rate
- context-reference coverage
- evaluator failure rate

Operational metrics:

- provider latency
- estimated cost per run
- cache hit rate
- provider error rate
- evaluation latency

Review metrics:

- creator approval rate
- reviewer-reported unsupported claims
- manual evaluation disagreement rate

## Release Blockers

A slice cannot merge if:

- generated output can claim unsupported project facts silently
- empty context generates a fabricated answer
- uploaded prompt injection changes system behavior
- output lacks context references
- evaluation results are not stored
- provider failures are hidden
- tests require real paid provider keys
- AI media output lacks disclosure where relevant

## Related Documents

- `docs/ARCHITECTURE.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/THREAT_MODEL.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`
