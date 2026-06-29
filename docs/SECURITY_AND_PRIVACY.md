# Security and Privacy v1.0

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-29
- Implementation status: policy and architecture only; product implementation blocked

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

File handling rules:

- never trust the original filename as a path
- never execute uploaded content
- never render uploaded markdown as trusted HTML
- store source metadata with every document and chunk
- preserve deletion and retention hooks for future cloud storage

### Authorization Model

Stage 4 local mode uses a synthetic local principal instead of skipping
authorization:

- `tenant_id = tenant_local`
- `owner_id = user_local`
- `actor_id = user_local`

Every endpoint must resolve the actor before data access. Every project-scoped query
must enforce `(tenant_id, owner_id, project_id)` before lookup, retrieval,
generation, evaluation, export, or delete. Child tables may either denormalize
`owner_id` or be accessed only through a server-side project authorization guard
that joins through `Project`. Generated IDs are not authorization proof. Missing
access returns `403`; missing resources that are not visible to the actor return
`404`.

### Tenant And Project Isolation

Stage 4 starts with project isolation plus a synthetic local tenant/user. Future
multi-user mode replaces the principal source without changing the isolation
predicate.

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

Stage 4 local/dev/test limits:

| Control | Limit |
|---|---:|
| Upload requests | 30 per project per hour |
| Accepted file size | 1 MiB per file |
| Project corpus size | 5 MiB |
| Documents per project | 10 active documents |
| Ingestion jobs | 10 per project per hour |
| Concurrent ingestion jobs | 1 per project |
| Generation runs | 20 per project per hour |
| Concurrent generation jobs | 1 per project |
| Provider calls | 30 per provider mode per project per hour |
| Prompt input tokens | 6,000 per generation run |
| Output tokens | 2,500 per generation run |
| Generated script length | 1,200 words per generation run |
| Unsupported claims evaluated | 100 extracted project-specific factual claims |
| Automatic regeneration | 1 retry maximum |
| Estimated local cost budget | USD 0.00 for mock/local mode |
| Estimated free-provider budget | USD 1.00 per project per day after explicit opt-in |

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

## Related Documents

- `docs/THREAT_MODEL.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/THIRD_PARTY_NOTICES.md`
