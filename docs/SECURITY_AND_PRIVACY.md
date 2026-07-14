# Security and Privacy v1.0

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-07-02
- Implementation status: policy and architecture only; product implementation blocked
- Stage 4 branch status: first local slice implementation started with mock/local
  providers only

## Security Posture

NarraTwin AI processes user-uploaded project knowledge and uses AI providers to
produce grounded walkthrough content. The system must assume that uploaded files,
filenames, prompts, transcripts, retrieved context, provider responses, and model
outputs are untrusted.

The security goal is to make the first product slice safe enough to review before
it handles public portfolio or customer-facing content.

## Assets

High-value assets:

- provider API keys and future user credentials
- uploaded project knowledge
- generated walkthrough scripts
- context references and retrieval metadata
- evaluation results
- project and tenant metadata
- audit logs
- cost and provider usage metadata
- future avatar, voice, subtitle, and video artifacts
- future consent records for identity media

## Security Principles

- Validate input at system boundaries.
- Authorize every project-scoped read and write.
- Keep provider keys isolated from frontend and prompts.
- Treat model output as data, not trusted instructions or code.
- Fail closed when context, authorization, evaluation, or provider state is unsafe.
- Redact secrets and sensitive content before logging.
- Prefer local/mock providers for development and CI.
- Keep third-party provider egress explicit, auditable, and optional.
- Secret screening is mandatory before non-local provider egress.

## Required Controls

### Secret Scanning

Controls:

- keep `.env` and `.env.*` ignored except `.env.example`
- document provider variables in `.env.example` without values
- run repository secret scanning in CI
- block private keys, provider keys, GitHub tokens, credentials, and certificates
- rotate any secret that reaches a remote
- run secret screening on every provider-bound text segment before any non-local
  provider egress, including upload, retrieved_context, user_prompt, transcript,
  provider_payload, and evaluator_payload

Reviewer checks:

- no provider key assignment outside `.env.example`
- no real keys in docs, tests, fixtures, logs, screenshots, or examples
- no raw secret values in pull request descriptions

### Secret Screening Result

Provider egress is blocked unless every provider-bound text segment has a passed
`SecretScreeningResult`. Provider-bound segments include upload, retrieved_context,
user_prompt, transcript, provider_payload, and evaluator_payload.

Required fields:

- `secret_screening_id`
- `tenant_id`
- `project_id`
- `screened_input_type`
- `screened_input_id`
- optional `document_id`
- `content_checksum`
- `scanner_version`
- `categories`
- `finding_count`
- `blocking`
- `redaction_applied`
- `override_required`
- `egress_decision`
- optional `reviewer_id`
- `audit_event_id`
- `created_at`

Blocking categories include provider keys, private keys, GitHub tokens, cloud
credentials, bearer tokens, JWT-like credentials, passwords, and high-confidence
credential assignments. False positives may be overridden only through an explicit
review action that records reviewer, reason, redaction decision, and audit event.
Local/mock provider calls may continue with quarantined content only when no
external egress occurs.

### Prompt Injection Controls

Controls:

- uploaded project knowledge is data, not instructions
- retrieved context is quoted or delimited as untrusted evidence
- system/developer safety rules are not sourced from user-editable documents
- tool permissions are enforced in code, not by prompt text
- prompt-injection fixtures are required before Stage 4 merge
- generated output must cite context references for project-specific claims
- empty or insufficient context produces refusal

Blocked behavior:

- uploaded text overriding system or developer rules
- retrieved text changing provider routing or tool permissions
- generated model output invoking shell, SQL, file paths, or HTML rendering

### File Upload Validation

Stage 4 allowed upload types:

- markdown
- plain text

Required validation:

- extension allowlist
- content-type allowlist
- maximum file size
- maximum project corpus size
- filename sanitization
- generated storage path
- checksum recording
- binary/executable/archive rejection
- server-side UTF-8 decoding and content sniffing
- NUL-byte rejection
- archive magic-byte rejection
- control-character threshold enforcement
- path traversal rejection
- mandatory secret screening before non-local provider egress

Stage 4 Slice 1 implementation notes:

- accepted uploads are limited to `.md` and `.txt`
- files are decoded as UTF-8 and rejected when empty, oversized, path-like, or an
  unsupported media type
- multipart uploads are read with a hard Stage 4 byte cap instead of buffering an
  unlimited file before validation
- archive magic bytes, NUL bytes, and control-heavy text are rejected before
  storage
- prompt-injection-like uploaded content is rejected before ingestion and unsafe
  retrieved context is refused before generation
- public evidence excerpts and unsupported-output excerpts are capped and passed
  through the local redaction helper before response serialization
- raw upload content is not echoed in public validation errors
- uploaded markdown is treated as text evidence and is not rendered as trusted HTML
- non-local provider egress is disabled in tests and local slice execution

File handling rules:

- never trust the original filename as a path
- never execute uploaded content
- never render uploaded markdown as trusted HTML
- store source metadata with every document and chunk
- preserve deletion and retention hooks for future cloud storage

### Authorization Model

Stage 4+ local/dev/test mode uses a synthetic local principal instead of skipping
authorization:

- `tenant_id = tenant_local`
- default `owner_id = user_local`
- default `actor_id = user_local`

`APP_ENV` is read from the environment; unset or blank values default to the
effective environment `local` for local-first development. In effective
local/dev/test environments only, `X-Local-User-Id` may simulate a different
local principal. The header is not authentication, is not a production identity
source, and is accepted only after normalization and validation: whitespace-only
values fall back to `user_local`; non-empty values must contain only ASCII
letters, digits, underscore, or dash and be at most 64 characters. Invalid
non-empty values return `400 VALIDATION_ERROR`. Non-empty values outside
local/dev/test return `400 LOCAL_PRINCIPAL_HEADER_NOT_ALLOWED`.

Every endpoint must resolve the actor before data access. Every project-scoped
query must enforce `(tenant_id, owner_id, project_id)` before lookup, retrieval,
generation, evaluation, export, or delete. Future real authentication replaces
only the principal source, not this authorization predicate. Child tables may
either denormalize `owner_id` or be accessed only through a server-side project
authorization guard that joins through `Project`. Generated IDs are not
authorization proof. Missing access returns `403`; missing resources that are not
visible to the actor return `404`.

### Tenant And Project Isolation

Stage 4 starts with project isolation plus a synthetic local tenant/default user
and trusted local-only principal simulation for tests. Future multi-user mode
replaces the principal source without changing the isolation predicate.

Controls:

- every document, chunk, embedding, run, artifact, and audit event includes
  `tenant_id` and `project_id`
- owner-scoped access is enforced through `owner_id` on `Project` or a documented
  server-side authorization guard
- every retrieval query filters by tenant and project
- provider prompts include only authorized project context
- artifact storage paths use generated IDs
- access checks happen before retrieval, generation, evaluation, export, and delete

Required tests before multi-user release:

- cross-project retrieval is impossible
- cross-tenant retrieval is impossible using the current `tenant_id` predicate
- unauthorized project access returns `403`
- missing project returns `404` without leaking existence across tenants

Stage 4 Slice 1 includes a retrieval test that inserts chunks for two projects and
asserts that retrieval for one project excludes chunks from the other project under
the synthetic local tenant.

### Approved Knowledge Controls

Uploaded documents are not trusted source material until explicitly approved.

Controls:

- upload validation stores documents as `UPLOADED`, `STORED`, or `QUARANTINED`
- only documents with `document_status = STORED`, `approval_status = APPROVED`, and
  `ingestion_status = INGESTED` can be retrieved or sent to non-local providers
- ingestion can start only after `approval_status = APPROVED`
- prompt-injection text can be present in approved evidence, but it remains quoted
  data and never becomes an instruction
- secret-like content places the document in `QUARANTINED` and blocks external
  provider egress until reviewed
- every approval, rejection, quarantine, and deletion creates an audit event
- deleted or rejected documents invalidate derived chunks, embeddings, retrieval
  caches, and generation caches

### Provider Key Isolation

Controls:

- provider keys are read only from environment-backed configuration or a future
  secret manager
- keys are never sent to frontend clients
- keys are never included in prompts, uploaded files, logs, traces, eval reports, or
  error messages
- provider access is routed through backend adapters only
- real provider usage is opt-in and disabled for local/dev/test by default
- provider mode and selected provider are recorded per run

### No Secret Logging

Controls:

- structured logs use identifiers, counts, statuses, and error codes
- raw prompts, raw uploads, and provider payloads are excluded from default logs
- any debug logging that includes content is local-only and disabled by default
- logs redact `api_key`, `secret`, `token`, `password`, `credential`, and provider
  authorization headers
- audit logs record security decisions without storing provider secrets

### Rate Limits And Cost Limits

Required rate limits:

- upload requests per user/project
- ingestion jobs per project
- generation runs per project and user
- provider calls per provider mode
- failed auth attempts when auth exists
- export/render requests for future media providers

Cost controls:

- cache generated scripts where request and context are unchanged
- cap maximum tokens, retrieved chunks, and output length
- cap concurrent provider calls
- record estimated cost where provider data allows
- block repeated failed runs from looping indefinitely

### Rate And Cost Limit Values

Stage 4 local/dev/test implemented limits are process-local lifetime caps unless
otherwise noted. Sliding-window per-hour limits require a durable rate limiter and
remain future Stage 5/8 hardening work.

| Control | Limit |
|---|---:|
| Accepted file size | 1 MiB per file |
| Upload request body | 1 MiB file plus multipart overhead |
| Project corpus size | 5 MiB |
| Documents per project | 10 active documents |
| Documents per ingestion request | 10 documents |
| Chunks per document | 100 chunks |
| Chunks per project | 200 chunks |
| Projects per tenant | 25 projects |
| Concurrent ingestion jobs | 1 per project |
| Generation runs | 50 per project |
| Concurrent generation jobs | 1 per project |
| Prompt input | 2,000 characters per generation run |
| Idempotency records | 500 per tenant/user |
| Automatic regeneration | Disabled |
| Estimated local cost budget | USD 0.00 for mock/local mode |

Real provider modes must fail closed when cost metadata is unavailable and a budget
would otherwise be unenforceable.

Evaluation and drift controls are security-relevant. Every accepted or failed
generation record must include `evaluator_version`, `prompt_template_version`,
`retrieval_strategy_version`, `embedding_model_version`, `retrieval_top_k`, and
`retrieval_score_threshold`. Stage 4 uses deterministic, rule-backed evaluation;
model-as-judge evaluation is future scope and requires a separate ADR.

### Audit Logs

Audit events:

- project created, updated, deleted
- knowledge uploaded, rejected, ingested, deleted
- walkthrough requested, generated, refused, evaluated
- provider mode selected
- external provider call attempted
- evaluation failed or unsupported claim detected
- prompt injection detected or neutralized
- future consent recorded or revoked
- future export created or deleted

Audit log rules:

- include `event_id`, `trace_id`, `tenant_id`, `project_id`, `actor_id`, action,
  outcome, timestamp, and reason code for project-scoped or security-relevant
  events; system events use `actor_id = system`
- do not store raw secrets
- avoid storing full uploaded content in audit logs
- preserve enough metadata for reviewer and incident analysis

### Dependency Scanning

Required before product code merges:

- lockfile committed for each package ecosystem
- CI installs with reproducible commands where applicable
- dependency scanner runs on pull requests
- critical/high reachable vulnerabilities block merge
- moderate findings require triage and owner
- new dependencies require third-party notice review
- provider SDK additions require adapter and contract-test review

### OWASP Baseline Scan

When a web surface exists, CI must add an OWASP ZAP baseline scan against the local
or preview deployment.

Required scan posture:

- passive baseline scan first
- authenticated scan only after auth exists and test credentials are isolated
- critical/high findings block merge or release
- findings are recorded as CI artifacts
- false positives require documented owner, reason, and review date

### Security Headers And Browser Baseline

Frontend/backend deployment must include:

- Content Security Policy
- HSTS in non-local environments
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy`
- clickjacking protection through CSP `frame-ancestors` or equivalent
- restricted CORS origins
- secure, httpOnly, sameSite cookies when session cookies exist

### Isolated Security Tool Compatibility Exception

Issue `#138` removes Semgrep from the application/development dependency graph
so the backend, local test environment, and runtime image resolve a fixed Click
release. Semgrep `1.168.0` remains in the separate `tools/semgrep` project with
an exact `click==8.3.3` uv override because upstream declares
`click~=8.1.8`.

This is a narrow compatibility exception, not a vulnerability ignore and not a
claim that every Semgrep CLI path supports Click `8.3.3`. The repository:

- audits the root environment and exact isolated tool site-packages separately,
  with no ignored advisory IDs;
- verifies the installed tool inventory against the frozen tool lock;
- runs only the hash-bound local-rule invocation with metrics disabled;
- requires engine config validation, nonempty scan coverage, zero findings, and
  exact target/rule manifests;
- requires positive and clean Semgrep execution canaries;
- verifies the backend image contains Click `>=8.3.3` and no Semgrep; and
- fails the contract after `2026-08-13` unless a security/repo owner renews or
  removes the exception through review.

Any Semgrep version, lock, rule, target, canary, or invocation change breaks the
reviewed-input hash manifest and requires renewed compatibility review. Remove
the override when upstream publishes a reviewed
Semgrep version compatible with a fixed Click release; issue `#150` tracks the
deadline and removal work.

## Privacy Rules

- Use local-first storage for MVP.
- Do not send private project knowledge to external providers unless explicitly
  configured.
- Make provider egress visible in run metadata.
- Store only necessary project metadata.
- Do not log raw provider keys, raw auth tokens, or private certificates.
- Stage 4 local deletion uses soft-delete metadata for projects, documents, chunks,
  runs, evaluations, artifacts, and audit-linked resources. Physical source-file
  deletion may happen locally, but audit metadata and tombstones remain.
- Define cloud retention and provider-side deletion behavior before cloud storage or
  multi-user access.
- Do not enable voice cloning or face cloning without explicit consent.
- Preserve AI-generated avatar/voice disclosure for future media outputs.

## Security Test Requirements

Before Stage 4 Slice 1 can merge:

- upload type rejection
- filename sanitization
- path traversal rejection
- file size rejection
- project-scoped retrieval
- empty-context refusal
- prompt-injection-in-uploaded-document test
- prompt-injection retrieved-context refusal path
- unsupported-claim detection or refusal
- no real paid provider key required
- no secret committed in repository scan
- generated output displayed without trusted HTML execution

Before future provider/media stages merge:

- provider key never appears in logs or prompts
- provider failure fallback path
- provider response schema validation
- consent required for identity media
- AI disclosure present for voice/avatar outputs
- third-party license review complete

## Security Release Blockers

A PR or release is blocked if:

- a critical/high reachable security finding is unresolved
- tests require real paid provider keys
- uploaded documents can override system instructions
- unsupported claims can pass silently
- provider keys are committed or logged
- project isolation can be bypassed
- external provider egress is implicit or unaudited
- third-party license status is unresolved for used components
- AI avatar or voice output lacks disclosure where relevant
- cloned face or voice is enabled without explicit consent
- the Semgrep compatibility exception expires or changes without security-owner
  review

## Related Documents

- `docs/THREAT_MODEL.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/THIRD_PARTY_NOTICES.md`
