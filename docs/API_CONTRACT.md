# API Contract

## Version

- Version: 1.0
- Stage: Stage 8 performance, security hardening, release readiness
- Canonical issue: `#13`
- Last updated: 2026-07-02
- Status: Stage 8 branch adds local performance budgets, request hardening,
  dependency/container scan gates, and release-readiness evidence on top of the
  Stage 7 mock/local avatar path

## API Principles

- Stage 4 endpoints live under `/api/v1`.
- REST endpoints use plural nouns.
- JSON fields use camelCase.
- Inputs and outputs use separate schemas.
- Every list endpoint is paginated.
- Every error response uses one structured error shape.
- Validation happens at API boundaries.
- Project-scoped endpoints enforce authorization before data access.
- Generated outputs expose evaluation state and context references.
- Provider secrets are never accepted from frontend request bodies.
- Write requests are locally rate limited and return `RATE_LIMIT_EXCEEDED` with
  HTTP `429` when the Stage 8 local window is exceeded. This local flood-control
  check runs before endpoint idempotency handling, so over-budget duplicate
  idempotency replays can receive `429 RATE_LIMIT_EXCEEDED`.
- API write requests have a general request size limit and must send a valid
  non-negative `Content-Length`. Missing length returns
  `411 CONTENT_LENGTH_REQUIRED`; malformed length returns
  `400 INVALID_CONTENT_LENGTH`. Stage 8 also counts actual ASGI body bytes, so
  under-reported `Content-Length` cannot bypass the local request budget. Uploads
  keep the stricter multipart upload limit and streaming read limit.
- Markdown uploads must use `text/markdown`; plain-text uploads must use
  `text/plain`. `application/octet-stream` compatibility is intentionally
  rejected until a validated compatibility exception is approved.
- `GET /api/v1/ops/status` is a read-only operational posture endpoint. It
  returns durable-state configuration and bounded record counts for Stage 4,
  Stage 6, and Stage 7, plus local monitoring feature flags. It must not expose
  uploaded document text, prompts, generated script text, provider payloads,
  filesystem contents, environment values, or secrets.

## API Versioning

The initial public contract uses `/api/v1`. Backward-compatible additions are
preferred over breaking field changes. Removing fields, changing enum meaning, or
changing status semantics requires a new ADR and migration/deprecation plan.

## Common Headers

Request headers:

- `X-Request-Id`: optional caller-provided request ID
- `Idempotency-Key`: required for upload, ingestion, generation, approval, deletion,
  and future media-render write operations
- `X-Local-User-Id`: optional trusted local/dev/test-only principal simulation
  header. It is not authentication and must never be accepted as production
  identity.

Response headers:

- `X-Request-Id`: server request ID
- `Content-Type: application/json`

Stage 4+ local mode resolves a synthetic tenant with `tenantId = tenant_local`.
By default, `ownerId = user_local` and `actorId = user_local`. The backend reads
`APP_ENV` from the environment and defaults an unset or blank value to the
effective environment `local`. In effective local/dev/test environments only,
`X-Local-User-Id` may simulate a different local principal for isolation tests
and local demos. The header value is trimmed, must contain only ASCII letters,
digits, underscore, or dash, and is capped at 64 characters. Missing or
whitespace-only values fall back to `user_local`. Invalid non-empty values return
`400 VALIDATION_ERROR`. Any non-empty `X-Local-User-Id` outside local/dev/test
returns `400 LOCAL_PRINCIPAL_HEADER_NOT_ALLOWED`.

`X-Local-User-Id` is not authentication. Production identity must come from a
future real authentication source, and that change must replace only principal
resolution, not the authorization predicate. API handlers must enforce
`(tenantId, ownerId, projectId)` before every project-scoped lookup, retrieval,
generation, evaluation, export, or delete. Generated IDs are not authorization
proof.

## Error Shape

All errors use:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request.",
    "details": {},
    "requestId": "req_123"
  }
}
```

`error.details` is allowlisted metadata only. It may contain stable identifiers,
counts, enum values, retry hints, validation field names, and redacted excerpts.
It must not contain raw prompts, raw uploads, raw retrieved context, raw provider
payloads, provider payloads, stack traces, environment variables, configuration dumps, filesystem
paths, provider keys, bearer tokens, credentials, or other secrets.

Status mapping:

| Status | Use |
|---:|---|
| 400 | malformed request |
| 401 | unauthenticated after auth exists |
| 403 | authenticated but unauthorized |
| 404 | resource not found |
| 409 | conflict or duplicate |
| 413 | upload too large |
| 415 | unsupported media type |
| 422 | semantic validation failure |
| 429 | rate limit exceeded |
| 500 | internal error with generic message |
| 502 | provider failure |
| 503 | dependency unavailable |

## Pagination Shape

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 0,
    "totalPages": 0
  }
}
```

## Resource IDs

Canonical IDs use stable prefixes:

- `proj_` for projects
- `doc_` for documents
- `chunk_` for chunks
- `ctx_` for context references
- `ing_` for ingestion runs
- `run_` for walkthrough runs
- `mlrun_` for multilingual walkthrough artifact runs
- `avrun_` for avatar render runs
- `eval_` for evaluation results
- `claim_` for unsupported or supported claim records
- `claimsup_` for claim-support records
- `evsnap_` for evidence snapshots
- `art_` for artifacts
- `tomb_` for tombstones
- `audit_` for audit events
- `req_` for request records
- `trace_` for trace records
- `emb_` for embedding records
- `idem_` for idempotency records
- `secscan_` for secret-screening records

Provider-native IDs are stored as provider metadata, not canonical IDs.

## Idempotency Requirements

Idempotency keys are scoped by tenant, actor, endpoint, non-null
`idempotencyScope`, and `idempotencyKey`. The request body checksum is stored on
the idempotency record for conflict detection, not uniqueness. Request checksum
preimages must be structured so user/provider strings containing delimiters
cannot collide across fields. For project creation, `idempotencyScope =
"project:create"` because no `projectId` exists yet. For project-scoped writes,
`idempotencyScope = projectId`. Implementations must persist an
`IdempotencyRecord` before provider calls, vector writes, generated artifacts,
approval state changes, or tombstone writes.
Nested media writes that act on a specific source run, such as Stage 6
multilingual generation and Stage 7 avatar rendering, narrow the scope to the
authenticated tenant, actor, project, and source run so replay/conflict checks
cannot cross source-run boundaries.

`IdempotencyRecord` fields:

- `idempotencyRecordId`
- `tenantId`
- `actorId`
- optional `projectId`
- `idempotencyScope`
- `endpoint`
- `idempotencyKey`
- `requestChecksum`
- optional `responseStatus`
- optional `responseBodyRef`
- optional `jobRef`
- `status`
- optional `lockedBy`
- optional `lockedAt`
- `expiresAt`
- `createdAt`
- `updatedAt`

Record statuses:

- `RESERVED`
- `RUNNING`
- `SUCCEEDED`
- `FAILED`
- `EXPIRED`

For duplicate keys:

- identical request body returns the original response or current job status
- different request body returns `409 IDEMPOTENCY_CONFLICT`
- an in-flight matching request returns `409 IDEMPOTENCY_IN_PROGRESS` or current
  accepted job status without starting duplicate work
- a terminal failed matching request returns the original failure code/message
  without starting duplicate provider work
- provider calls, vector writes, and generated artifacts must not be duplicated
- idempotency records are retained for at least 24 hours in local mode
- Stage 8 local rate limiting is a pre-idempotency flood-control guard. It can
  return `429 RATE_LIMIT_EXCEEDED` before idempotency replay logic when a caller
  exceeds the local write window.

Write endpoints requiring idempotency:

- `POST /api/v1/projects`
- `PATCH /api/v1/projects/{projectId}`
- `POST /api/v1/projects/{projectId}/knowledge-documents`
- `PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval`
- `DELETE /api/v1/projects/{projectId}/knowledge-documents/{documentId}`
- `POST /api/v1/projects/{projectId}/ingestion-runs`
- `POST /api/v1/projects/{projectId}/walkthrough-runs`
- `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/multilingual-runs`
- `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-consents`
- `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-renders`
- `DELETE /api/v1/projects/{projectId}`
- all future media-render endpoints

## Typed Response Schemas

The markdown examples below are canonical Stage 2 contract examples. Stage 4
implementation must define OpenAPI or JSON Schema equivalents before product code
is accepted. Required schemas:

- `Project`
- `KnowledgeDocument`
- `IngestionRun`
- `WalkthroughRun`
- `AcceptedWalkthroughRun`
- `UnsafeWalkthroughRun`
- `EvaluationSummary`
- `EvaluationResult`
- `ContextRef`
- `UnsupportedClaim`
- `ClaimSupport`
- `EvidenceSnapshot`
- `IdempotencyRecord`
- `SecretScreeningResult`
- `AuditEvent`
- `APIError`

Persisted project-scoped domain schemas include `tenantId`, `projectId` where
project-scoped, `createdAt`, and stable enum values. Endpoint-specific response
schemas below are authoritative for child action outputs such as multilingual
runs and avatar renders. Provider-native fields live under `providerMetadata`
or endpoint-specific provider/config objects when the response contract exposes
adapter state directly.
Public schemas must state whether `tenantId` and `ownerId` are returned or
server-internal. Stage 4 local API responses return `tenantId = tenant_local` and
default examples use `ownerId = user_local` to keep isolation visible. Trusted
local/dev/test simulation may return a different `ownerId` when
`X-Local-User-Id` is valid and accepted.

`SecretScreeningResult` is an internal schema. If exposed to reviewers later, it
must use camelCase fields equivalent to the security/data contract and omit raw
secret values.

## Project Endpoints

### Create Project

`POST /api/v1/projects`

Request:

```json
{
  "name": "NarraTwin AI",
  "description": "Grounded project walkthrough generator",
  "defaultAudience": "RECRUITER",
  "defaultLanguage": "en"
}
```

Response `201`:

```json
{
  "projectId": "proj_123",
  "tenantId": "tenant_local",
  "ownerId": "user_local",
  "name": "NarraTwin AI",
  "description": "Grounded project walkthrough generator",
  "projectStatus": "ACTIVE",
  "defaultAudience": "RECRUITER",
  "defaultLanguage": "en",
  "createdAt": "2026-06-29T00:00:00Z",
  "updatedAt": "2026-06-29T00:00:00Z"
}
```

### List Projects

`GET /api/v1/projects?page=1&pageSize=20`

Response `200`: paginated project list ordered by `createdAt desc, projectId desc`.
`pageSize` defaults to `20` and is capped at `100`.

### Get Project

`GET /api/v1/projects/{projectId}`

Response `200`: project.

### Update Project

`PATCH /api/v1/projects/{projectId}`

Partial request fields:

- `name`
- `description`
- `defaultAudience`
- `defaultLanguage`

`ProjectPatchRequest`:

```json
{
  "name": "NarraTwin AI",
  "description": "Updated project description",
  "defaultAudience": "ENGINEER",
  "defaultLanguage": "en"
}
```

Response `200`: canonical `Project` response. Duplicate idempotency key with the
same request checksum replays the same response or current project state. Duplicate
idempotency key with a different checksum returns `409 IDEMPOTENCY_CONFLICT`.

### Delete Project

`DELETE /api/v1/projects/{projectId}`

Stage 4 delete is a soft delete for metadata plus local physical source-artifact
deletion where available. Audit events and tombstones remain.

Response `200`:

```json
{
  "projectId": "proj_123",
  "tenantId": "tenant_local",
  "ownerId": "user_local",
  "projectStatus": "DELETED",
  "deletedAt": "2026-06-29T00:00:00Z",
  "tombstoneId": "tomb_123",
  "cacheInvalidationStatus": "COMPLETED"
}
```

Repeat delete with the same idempotency key replays the tombstone response. Delete
of an already deleted visible project returns the existing tombstone response.
Deletion invalidates document chunks, embeddings, retrieval caches, generation
caches, and future export paths.

## Knowledge Document Endpoints

### Upload Knowledge

`POST /api/v1/projects/{projectId}/knowledge-documents`

Content type:

- `multipart/form-data`

Accepted file types in Stage 4:

- `.md`
- `.txt`

Response `201`:

```json
{
  "documentId": "doc_123",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "sourceFilename": "architecture.md",
  "contentType": "text/markdown",
  "sizeBytes": 12345,
  "checksum": "sha256:abc",
  "documentStatus": "STORED",
  "approvalStatus": "PENDING",
  "ingestionStatus": "NOT_STARTED",
  "createdAt": "2026-06-29T00:00:00Z"
}
```

Validation errors:

- `413` for oversized file
- `415` for unsupported type
- `422 SECRET_LIKE_CONTENT` when uploaded content contains token-like or credential-like material
- `422` for invalid filename or other failed content validation

Stage 4 limits:

- file size: 1 MiB
- project corpus: 5 MiB
- active documents: 10
- accepted languages for generated scripts: English only

### Approve Knowledge Document

`PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval`

Request:

```json
{
  "approvalStatus": "APPROVED",
  "reviewNote": "Approved for local Stage 4 grounding."
}
```

Response `200`: knowledge document with approval status. Approval changes
`approvalStatus` only; ingestion changes `ingestionStatus` only; deletion changes
`documentStatus` and invalidates derived records. Retrieval eligibility requires
`documentStatus = STORED`, `approvalStatus = APPROVED`, `ingestionStatus =
INGESTED`, and valid non-deleted source and chunk checksums.

### List Knowledge Documents

`GET /api/v1/projects/{projectId}/knowledge-documents?page=1&pageSize=20`

### Get Knowledge Document

`GET /api/v1/projects/{projectId}/knowledge-documents/{documentId}`

Returns metadata, not necessarily raw content. Raw content exposure must be
authorization-gated.

### Delete Knowledge Document

`DELETE /api/v1/projects/{projectId}/knowledge-documents/{documentId}`

Deletion must invalidate derived chunks, embeddings, cached retrieval, and affected
run regeneration paths.

Response `200`:

```json
{
  "documentId": "doc_123",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "documentStatus": "DELETED",
  "approvalStatus": "REJECTED",
  "ingestionStatus": "INVALIDATED",
  "deletedAt": "2026-06-29T00:00:00Z",
  "tombstoneId": "tomb_456",
  "cacheInvalidationStatus": "COMPLETED"
}
```

Repeat delete with the same idempotency key replays the tombstone response. Delete
of an already deleted visible document returns the existing tombstone response.

## Ingestion Endpoints

### Start Ingestion

`POST /api/v1/projects/{projectId}/ingestion-runs`

Request:

```json
{
  "documentIds": ["doc_123"]
}
```

Response `201` in the Stage 4 through Stage 8 synchronous local path. Future
queued ingestion may return `202`:

```json
{
  "ingestionRunId": "ing_123",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "status": "QUEUED"
}
```

Stage 4 may implement ingestion synchronously and still return an equivalent run
record.

Ingestion may execute synchronously only when the request is within Stage 4 Resource
Budgets. The response still uses the `IngestionRun` schema.

### Get Ingestion Run

`GET /api/v1/projects/{projectId}/ingestion-runs/{ingestionRunId}`

## Walkthrough Run Endpoints

### Generate Walkthrough

`POST /api/v1/projects/{projectId}/walkthrough-runs`

Request:

```json
{
  "audience": "RECRUITER",
  "requestedLanguage": "en",
  "depth": "CONCISE",
  "style": "CONFIDENT",
  "prompt": "Create a 60-second walkthrough."
}
```

`prompt` is provider-bound user text. It must pass the same secret screening and
prompt-injection controls as uploads, transcripts, retrieved context, provider
payloads, and evaluator payloads before non-local provider egress.

Provider-bound text segment types:

- `upload`: sanitized uploaded document text before non-local egress
- `retrieved_context`: approved retrieved chunks selected for generation
- `user_prompt`: the `prompt` value in the walkthrough request
- `transcript`: future transcript text when an approved STT stage exists
- `provider_payload`: model or provider output before it is sent to another
  non-local provider
- `evaluator_payload`: internally constructed evaluation input containing the
  generated candidate, retrieved evidence, and claim list before evaluator egress

`evaluator_payload` is not a frontend request field. It is a backend-internal
provider-bound segment that must produce a `SecretScreeningResult` before any
non-local evaluator provider call.

API JSON uses camelCase. Internal cache, data-model, and observability fields use
snake_case; implementations must normalize API fields before cache-key generation.
For example, chunkingStrategyVersion maps to `chunking_strategy_version`.

Response `202` for queued or running work:

```json
{
  "runId": "run_123",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "status": "QUEUED",
  "evaluationStatus": null,
  "audience": "RECRUITER",
  "requestedLanguage": "en",
  "depth": "CONCISE",
  "style": "CONFIDENT",
  "createdAt": "2026-06-29T00:00:00Z"
}
```

Response `201` for newly accepted terminal output. In the Stage 4 through Stage 8
synchronous local path, an exact idempotency replay returns the stored original
`201` response body. Future asynchronous/persistent implementations may switch
replay to `200` only after the idempotency response contract and tests are
updated together. `GET` of an existing terminal run returns `200`.

```json
{
  "runId": "run_123",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "status": "COMPLETED",
  "evaluationStatus": "PASSED",
  "audience": "RECRUITER",
  "requestedLanguage": "en",
  "depth": "CONCISE",
  "style": "CONFIDENT",
  "acceptedScriptText": "Generated script text.",
  "contextRefs": [
    {
      "contextRefId": "ctx_123",
      "tenantId": "tenant_local",
      "projectId": "proj_123",
      "claimId": "claim_123",
      "chunkId": "chunk_123",
      "documentId": "doc_123",
      "sourceFilename": "project-summary.md",
      "chunkIndex": 0,
      "checksum": "sha256:chunk",
      "scriptSpanStart": 0,
      "scriptSpanEnd": 42,
      "evidenceSnapshot": {
        "evidenceSnapshotId": "evsnap_123",
        "tenantId": "tenant_local",
        "projectId": "proj_123",
        "documentId": "doc_123",
        "chunkId": "chunk_123",
        "sourceFilename": "project-summary.md",
        "chunkIndex": 0,
        "sourceDocumentChecksum": "sha256:doc",
        "chunkChecksum": "sha256:chunk",
        "chunkingStrategyVersion": "stage4-chunk-v1",
        "retrievalScore": 0.91,
        "redactedExcerpt": "Project fact used as evidence.",
        "excerptStart": 0,
        "excerptEnd": 30,
        "redactionFlags": [],
        "capturedAt": "2026-06-29T00:00:00Z",
        "snapshotChecksum": "sha256:snapshot"
      }
    }
  ],
  "evaluation": {
    "schema": "EvaluationSummary",
    "evaluationId": "eval_123",
    "evaluationStatus": "PASSED",
    "groundednessScore": 1.0,
    "faithfulness": 1.0,
    "answerRelevancy": 1.0,
    "contextPrecision": 1.0,
    "contextRecall": 1.0,
    "unsupportedClaimCount": 0,
    "unsupportedClaims": [],
    "claimSupports": [
      {
        "claimSupportId": "claimsup_123",
        "tenantId": "tenant_local",
        "projectId": "proj_123",
        "runId": "run_123",
        "evaluationId": "eval_123",
        "claimId": "claim_123",
        "contextRefId": "ctx_123",
        "chunkId": "chunk_123",
        "documentId": "doc_123",
        "supportStatus": "SUPPORTED",
        "supportScore": 1.0,
        "supportReason": "The claim is directly supported by the cited chunk.",
        "evidenceSnapshot": {
          "evidenceSnapshotId": "evsnap_123",
          "tenantId": "tenant_local",
          "projectId": "proj_123",
          "documentId": "doc_123",
          "chunkId": "chunk_123",
          "sourceFilename": "project-summary.md",
          "chunkIndex": 0,
          "sourceDocumentChecksum": "sha256:doc",
          "chunkChecksum": "sha256:chunk",
          "chunkingStrategyVersion": "stage4-chunk-v1",
          "retrievalScore": 0.91,
          "redactedExcerpt": "Project fact used as evidence.",
          "excerptStart": 0,
          "excerptEnd": 30,
          "redactionFlags": [],
          "capturedAt": "2026-06-29T00:00:00Z",
          "snapshotChecksum": "sha256:snapshot"
        }
      }
    ],
    "contextRefCoverage": 1.0,
    "embeddingProvider": "mock",
    "embeddingModel": "mock-embedding",
    "embeddingModelVersion": "stage4-local-v1",
    "embeddingDimension": 16,
    "vectorStore": "memory",
    "retrievalStrategyVersion": "stage4-rag-v1",
    "retrievalTopK": 6,
    "retrievalScoreThreshold": 0.72,
    "policyVersion": "stage4-grounding-policy-v1",
    "schemaVersion": "stage4-evaluation-schema-v1",
    "safetyPolicyVersion": "stage4-safety-policy-v1"
  },
  "provider": {
    "provider": "mock",
    "providerMode": "LOCAL"
  },
  "trace": {
    "traceId": "trace_123",
    "latencyMs": 100,
    "inputTokens": 58,
    "outputTokens": 15,
    "estimatedCost": 0
  },
  "createdAt": "2026-06-29T00:00:00Z"
}
```

The embedded `evaluation` object in accepted walkthrough-run responses is an
`EvaluationSummary`, not the full canonical `EvaluationResult`. It exists for UI
state rendering and must include the decision fields needed to explain accepted
output. The full `EvaluationResult` is returned by
`GET /api/v1/projects/{projectId}/walkthrough-runs/{runId}/evaluation`.

Failed or refused terminal output shape. A newly created synchronous terminal
failure uses `201` with this shape. In the Stage 4 through Stage 8 synchronous
local path, exact idempotency replay returns the stored original `201` response
body. `GET` of an existing terminal run returns `200`.

```json
{
  "runId": "run_124",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "status": "FAILED",
  "evaluationStatus": "FAILED",
  "failure": {
    "reasonCode": "UNSUPPORTED_PROJECT_FACT",
    "message": "Generated output contained unsupported project facts.",
    "unsupportedClaimCount": 1
  },
  "redactedUnsupportedExcerpts": [
    "Unsupported metric claim."
  ],
  "contextRefs": [],
  "createdAt": "2026-06-29T00:00:00Z"
}
```

`rawGeneratedText` is internal-only. Public list and get responses for `FAILED` or
`REFUSED` runs must omit raw generated text and return only refusal or failure
metadata plus redacted excerpts. Only `PASSED` and allowed `WARNING` responses may
include `acceptedScriptText`.

Failure behavior:

- no approved context returns a persisted `REFUSED` run with `LOW_RETRIEVAL_CONFIDENCE`
- prompt-injection-like request text returns a persisted `REFUSED` run with
  `PROMPT_INJECTION_DETECTED`
- unsafe retrieved approved context returns a persisted `REFUSED` run with
  `UNSAFE_RETRIEVED_CONTEXT`
- unsupported project factual claims return persisted `FAILED` evaluation state
- provider failure returns structured `502` or stored failed run
- rate limits return `429 RATE_LIMIT_EXCEEDED`
- local per-project operation backpressure returns `429 BACKPRESSURE_QUEUE_FULL`
  without `Retry-After`; future queued workers may add `Retry-After` only when a
  safe retry interval is known and implemented
- worker or dependency unavailability returns `503 DEPENDENCY_UNAVAILABLE`

Backpressure error example:

```json
{
  "error": {
    "code": "BACKPRESSURE_QUEUE_FULL",
    "message": "Another Stage 4 operation is already active for this project.",
    "details": {},
    "requestId": "req_123"
  }
}
```

### Generate Multilingual Walkthrough

`POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/multilingual-runs`

Stage 6 translates an accepted English source walkthrough into a selected target
language, preserves glossary/project terms, generates SubRip subtitles, and
returns downloadable script/subtitle artifacts. The endpoint uses
`TranslationProvider` and `TTSProvider` adapter interfaces with mock/local
defaults; no paid provider is hardcoded or required for local/dev/test.
Stage 6 does not synthesize real audio, does not play audio, does not clone a
voice, and does not call non-local providers. The voice output is a downloadable
JSON manifest from the mock/local `TTSProvider`.

Request:

```json
{
  "targetLanguage": "es",
  "glossaryTerms": ["NarraTwin AI", "project knowledge", "source chunks"],
  "requestedVoiceProvider": "mock"
}
```

Supported Stage 6 target languages are `en`, `es`, `fr`, and `hi`. Unsupported
language tags return `422 UNSUPPORTED_LANGUAGE` without exposing raw source text.
When `requestedVoiceProvider` is unavailable, the response falls back to the mock
local voice provider and records `fallbackReason =
REQUESTED_PROVIDER_UNAVAILABLE`.

Request boundary limits:

- `targetLanguage`: 2-16 characters, BCP-47-like language tag, normalized to a
  supported base language
- `glossaryTerms`: at most 25 entries; each entry must be non-empty and at most
  80 characters
- `requestedVoiceProvider`: 1-64 characters, lowercase/uppercase letters,
  numbers, `_`, or `-`; normalized to lowercase before adapter use
- accepted source script and translated provider output: at most 20,000
  characters
- subtitle captions: deterministic local timing, at most 96 characters per
  caption and at most 250 captions

Post-provider validation:

- translated output must be non-empty
- translated output must stay within the Stage 6 size limit
- every configured glossary term present in the source script must remain present
  in translated output
- every source citation marker such as `[1]` must remain present in translated
  output before subtitles or downloadable artifacts are returned
- provider identifiers must satisfy the adapter identifier pattern
- Voice provider artifacts must be JSON manifests with safe `.json` filenames,
  `application/json` MIME type, decodable UTF-8 JSON object content, a checksum
  matching the decoded manifest text, and an exact schema. The Stage 8 local
  schema requires only `provider`, `providerMode`, `language`,
  `languageDisplayName`, `textChecksum`, `durationSecondsEstimate`,
  `mockAudioProfile`, and `disclosure`; `mockAudioProfile` allows only
  `durationMillisecondsEstimate`, `sampleRateHz`, and `channels`. Unknown
  top-level or nested fields fail with `PROVIDER_OUTPUT_INVALID`.

Response `201`:

```json
{
  "multilingualRunId": "mlrun_123",
  "sourceRunId": "run_123",
  "sourceLanguage": "en",
  "targetLanguage": "es",
  "status": "COMPLETED",
  "sourceScriptText": "Generated script text with citations.",
  "translatedScriptText": "Translated script text with preserved project terms.",
  "subtitlesText": "1\n00:00:00,000 --> 00:00:04,000\nTranslated script text.\n\n",
  "glossaryTerms": ["NarraTwin AI", "project knowledge"],
  "preservedTerms": ["NarraTwin AI", "project knowledge"],
  "translationProvider": {
    "provider": "mock",
    "providerMode": "LOCAL"
  },
  "voice": {
    "provider": "mock",
    "providerMode": "LOCAL",
    "requestedProvider": "mock",
    "fallbackReason": null,
    "language": "es",
    "artifact": {
      "fileName": "voice-manifest-es.json",
      "mimeType": "application/json",
      "contentBase64": "base64-json",
      "checksum": "sha256:voice"
    }
  },
  "artifacts": {
    "translatedScript": {
      "fileName": "run_123-es-script.md",
      "mimeType": "text/markdown",
      "contentBase64": "base64-script",
      "checksum": "sha256:script"
    },
    "subtitles": {
      "fileName": "run_123-es.srt",
      "mimeType": "application/x-subrip",
      "contentBase64": "base64-srt",
      "checksum": "sha256:srt"
    },
    "voiceManifest": {
      "fileName": "voice-manifest-es.json",
      "mimeType": "application/json",
      "contentBase64": "base64-json",
      "checksum": "sha256:voice"
    }
  },
  "trace": {
    "traceId": "trace_123",
    "sourceContextRefCount": 1,
    "sourceCitationCount": 1
  }
}
```

Provider response schema:

- `translationProvider.provider`, `voice.provider`, and
  `voice.requestedProvider` are provider IDs, not a hardcoded provider enum.
- `providerMode` is constrained to `LOCAL`, `DISABLED`, or
  `OPTIONAL_EXTERNAL`.
- Current Stage 6 local/dev/test behavior uses `mock` and `LOCAL`.
- Adding another adapter requires code changes in `backend/app/stage6.py`,
  API/contract updates in this file, tests in `tests/unit` and `tests/api`,
  third-party notices, and review of provider keys, egress, licensing, and
  output validation. A provider adapter must not require frontend-supplied
  secrets.

Failure modes:

| Status | Code | Meaning |
|---:|---|---|
| 400 | `IDEMPOTENCY_KEY_REQUIRED` | Missing `Idempotency-Key` on the write request |
| 403 | `FORBIDDEN` | Project or source run is not accessible to the principal |
| 404 | `NOT_FOUND` | Project or source walkthrough run does not exist |
| 409 | `IDEMPOTENCY_CONFLICT` | Idempotency key was reused with a different request body |
| 409 | `IDEMPOTENCY_IN_PROGRESS` | Duplicate request arrived while the first request is still pending |
| 413 | `SOURCE_SCRIPT_TOO_LARGE` | Accepted source script exceeds the Stage 6 source limit |
| 413 | `PROVIDER_OUTPUT_TOO_LARGE` | Translation provider output exceeds the Stage 6 output limit |
| 422 | `SECRET_LIKE_CONTENT` | Glossary terms contain secret-like content and are rejected before provider calls |
| 422 | `SOURCE_RUN_NOT_TRANSLATABLE` | Source run is not completed or has no accepted script |
| 422 | `UNSUPPORTED_LANGUAGE` | Target language is not supported by Stage 6 |
| 422 | `PROVIDER_OUTPUT_INVALID` | Provider output is empty, invalid, or failed glossary/citation preservation |
| 422 | `VALIDATION_ERROR` | Request boundary validation failed, including glossary/provider field limits |
| 429 | `RESOURCE_LIMIT_EXCEEDED` | Stage 6 idempotency record limit is exceeded for the request scope |

Subtitle artifacts must be valid SubRip (`.srt`) with deterministic timing.
Accessibility notes for Stage 6: generated subtitles are downloadable text
artifacts, keep readable caption lengths, and preserve source citation markers so
reviewers can compare multilingual output against accepted grounded evidence.
Frontend download links remain disabled until the response artifact matches the
expected MIME type, file extension, base64 shape, and safe filename rules.

### Generate Avatar Demo Export

### Capture Avatar Consent

`POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-consents`

Phase 1 Closure issue `#111` / `CH-16` adds a dedicated consent-capture step
for Stage 7 durable synthetic-media paths. The endpoint stores or replays an
affirmative consent record bound to the current principal, project, source run,
trace, grounded-evaluation hooks, canonical consent statement version/text, and
request checksum.

This endpoint does not close revocation, provenance, disclosure, retention, or
provider-release work. It creates the durable consent primitive those later
chunks will depend on.

Request:

```json
{
  "consentToUseSyntheticAvatar": true
}
```

Request boundary rules:

- `consentToUseSyntheticAvatar`: required boolean; must be `true`
- source run must be `COMPLETED`, `PASSED`, and include grounded evaluation
  evidence
- request must use the same project/run authorization checks as Stage 7 render
  generation
- each consent record is single-use for durable render binding; before render it
  returns `avatarRenderId = null` and `artifactChecksums = []`, and after a
  successful durable render it is considered consumed for future render
  requests

Response `201`:

```json
{
  "consentRecordId": "consent_000001",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "actorId": "user_local",
  "sourceRunId": "run_123",
  "traceId": "trace_123",
  "sourceContextRefIds": ["ctx_123_001"],
  "sourceCitationIndexes": [1],
  "sourceEvaluationId": "eval_123",
  "sourceEvaluationChecksum": "sha256:evaluation",
  "evaluationStatus": "PASSED",
  "consentStatementVersion": "stage7-synthetic-avatar-consent-v1",
  "consentStatementText": "I affirm that I am authorized to approve this Stage 7 synthetic local avatar demo for the selected walkthrough run.",
  "grantedAt": "2026-07-12T00:00:00Z",
  "requestChecksum": "sha256:consent-request",
  "avatarRenderId": null,
  "artifactChecksums": []
}
```

Consent idempotency rules:

- matching idempotency payloads replay the same consent record
- changed-payload reuse returns `409 IDEMPOTENCY_CONFLICT`
- stale `RUNNING` consent idempotency rows do not replay as success after
  restore
- malformed, incomplete, stale-version, malformed-timestamp, request-checksum-
  mismatched, cross-project, cross-run, or cross-actor restored consent rows
  are dropped

Failure modes:

| Status | Code | Meaning |
|---:|---|---|
| 400 | `IDEMPOTENCY_KEY_REQUIRED` | Missing `Idempotency-Key` on the write request |
| 403 | `FORBIDDEN` | Project or source run is not accessible to the principal |
| 404 | `NOT_FOUND` | Project or source walkthrough run does not exist |
| 409 | `IDEMPOTENCY_CONFLICT` | Idempotency key was reused with a different request body |
| 409 | `IDEMPOTENCY_IN_PROGRESS` | Duplicate request arrived while the first request is still pending |
| 422 | `SOURCE_RUN_NOT_RENDERABLE` | Source run is not completed, passed, or accepted |
| 422 | `AVATAR_CONSENT_REQUIRED` | The request did not affirm synthetic-avatar consent |
| 429 | `RESOURCE_LIMIT_EXCEEDED` | Stage 7 idempotency record limit is exceeded for the request scope |

### Generate Avatar Demo Export

`POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-renders`

Stage 7 renders a completed, passed grounded walkthrough run into a mock/local
avatar demo export. The endpoint uses an `AvatarProvider` adapter and a local
HTML `VideoRenderer` export path with mock/local defaults. Local/dev/test must
not call paid avatar providers or require real provider keys.

Stage 7 does not create a real video binary, does not clone a face, does not
clone a voice, and does not call non-local providers. The demo export is a
downloadable HTML artifact plus JSON render manifest and video-export
placeholder artifacts. The manifest carries AI-generated avatar/video disclosure
metadata, provider config metadata, source trace metadata, source citations, and
evaluation status from the grounded script path.

Phase 1 Closure issue `#42` hardens `sourceEvaluationChecksum` as a canonical
Stage 7 checksum shared by the API route and Stage 7 service. The checksum input
set is, in order: normalized `sourceEvaluationId`, `sourceRunId`, `traceId`,
normalized `evaluationStatus`, comma-joined normalized `sourceContextRefIds`,
and comma-joined normalized `sourceCitationIndexes`. The response schema is
unchanged. Stage 7 rejects supplied source-evaluation checksums that do not
match this canonical preimage at both the service and mock-provider boundary,
and rejects checksum string components containing delimiter/control characters
that would make the comma/newline preimage ambiguous. Positive source context
or citation counts require explicit source context ref IDs and citation indexes;
Stage 7 must not synthesize placeholder evidence identifiers for direct service
or mock-provider calls.

Request:

```json
{
  "requestedAvatarProvider": "mock",
  "consentToUseSyntheticAvatar": true,
  "consentRecordId": "consent_000001",
  "clonedIdentityRequested": false
}
```

Request boundary limits:

- `requestedAvatarProvider`: 1-64 characters, lowercase/uppercase letters,
  numbers, `_`, or `-`; normalized to lowercase before adapter use
- `consentToUseSyntheticAvatar`: required boolean; must be `true` for the
  synthetic local presenter export
- `consentRecordId`: required string on the API path because Stage 7 durable
  render generation must bind to a previously captured consent record.
- `clonedIdentityRequested`: optional boolean; `true` is disabled in Stage 7
- accepted source script: at most 20,000 characters
- export artifacts: at most 512 KiB each after base64 decoding

Post-provider validation:

- source run must be `COMPLETED` with `evaluationStatus = PASSED` and accepted
  script text
- durable API render paths require a previously captured consent record whose
  tenant, project, actor, source run, trace, source evaluation ID/checksum, and
  canonical consent statement version/text match the render request scope
- a consent record can be consumed by at most one successful durable render;
  after `avatarRenderId` and `artifactChecksums` are bound, later render
  attempts with the same `consentRecordId` are rejected with
  `AVATAR_CONSENT_INVALID`
- avatar provider identifiers must satisfy the adapter identifier pattern
- provider mode must be `LOCAL`, `DISABLED`, or `OPTIONAL_EXTERNAL`
- provider config must be validated before storage or response; every successful
  Stage 7 render must be `MOCK_LOCAL`, `LOCAL`, no network egress, no API-key
  requirement, no real video support, and no cloned-identity support
- `avatarProvider.providerMode` and `providerConfig.providerMode` must both be
  `LOCAL` on success, and provider metadata must match the validated provider
  config
- `fallbackReason` is either `null`, `REQUESTED_PROVIDER_UNAVAILABLE`, or
  `PROVIDER_RENDER_FAILED`; arbitrary provider-supplied reason strings are
  rejected
- demo export artifact must use `text/html`, `.html`, a safe filename, valid
  base64 UTF-8 content, a checksum matching decoded content, exact trusted
  renderer output for the source run/trace/disclosure, and no active HTML
  content such as scripts, style tags/attributes, base tags, `src`/`href`/
  `srcset` attributes, event-handler attributes, forms, iframes, external links,
  `javascript:` URLs in tags, or refresh metadata. Benign escaped source prose
  may mention terms such as CSS, `src=`, `href=`, or `url()` because those terms
  are inert text in the trusted renderer output.
- render manifest artifact must use `application/json`, `.json`, a safe filename,
  valid base64 UTF-8 JSON object content, and a checksum matching decoded content
- render manifest and video export placeholder JSON must not contain duplicate
  object keys at any nesting level
- render manifest must match trusted provider config, AI-generated avatar/video
  disclosure metadata, source run ID, source trace ID, source context count,
  source context ref IDs, source citation count/indexes, source evaluation ID,
  source evaluation checksum, script checksum, source evaluation status, and
  public-use license check; unexpected top-level or nested JSON fields are
  rejected before storage or response
- source evaluation checksum validation uses the shared Stage 7 checksum helper
  so the API route, render response, render manifest, and video placeholder bind
  the same source run identity, trace identity, evaluation ID/status, context
  refs, and citation indexes; service-level and direct mock-provider calls
  cannot override the canonical checksum with a stale or caller-supplied
  mismatch
- Stage 7 avatar render idempotency request checksums use structured JSON
  preimages so newline/comma characters in strings cannot collide across request
  fields
- video export placeholder artifact must use `application/json`, `.json`, a
  safe filename, valid base64 UTF-8 JSON object content, matching checksum,
  expected schema/version, source run ID, trace ID, local renderer, validated
  provider config, disclosure, citation/evaluation metadata, public-use license
  check, a non-empty reason, and `realVideoProduced = false`; unexpected
  top-level or nested JSON fields are rejected before storage or response

Response `201`:

```json
{
  "avatarRenderId": "avrun_123",
  "consentRecordId": "consent_000001",
  "sourceRunId": "run_123",
  "status": "COMPLETED",
  "renderJobStatus": "COMPLETED",
  "renderJobStatusHistory": [
    { "status": "QUEUED", "message": "Avatar render job queued." },
    { "status": "RUNNING", "message": "Avatar provider render started." },
    { "status": "COMPLETED", "message": "Avatar render job completed." }
  ],
  "sourceScriptText": "Generated script text with citations. [1]",
  "avatarProvider": {
    "provider": "mock",
    "providerMode": "LOCAL",
    "requestedProvider": "mock",
    "fallbackReason": null
  },
  "providerConfig": {
    "provider": "mock",
    "providerMode": "LOCAL",
    "adapterKind": "MOCK_LOCAL",
    "allowNetworkEgress": false,
    "requiresApiKey": false,
    "supportsRealVideo": false,
    "supportsClonedIdentity": false
  },
  "videoRenderer": {
    "renderer": "local-html",
    "rendererMode": "LOCAL",
    "exportFormat": "html"
  },
  "disclosure": {
    "aiGenerated": true,
    "clonedIdentity": false,
    "consentRequired": true,
    "consentStatus": "CONFIRMED",
    "message": "AI-generated avatar demo export using a synthetic local presenter. No cloned face, cloned voice, or paid avatar provider was used."
  },
  "artifacts": {
    "demoExport": {
      "fileName": "run_123-avatar-demo.html",
      "mimeType": "text/html",
      "contentBase64": "base64-html",
      "checksum": "sha256:html"
    },
    "renderManifest": {
      "fileName": "run_123-avatar-render-manifest.json",
      "mimeType": "application/json",
      "contentBase64": "base64-json",
      "checksum": "sha256:manifest"
    },
    "videoExportPlaceholder": {
      "fileName": "run_123-video-export-placeholder.json",
      "mimeType": "application/json",
      "contentBase64": "base64-json",
      "checksum": "sha256:placeholder"
    }
  },
  "trace": {
    "traceId": "trace_123",
    "sourceContextRefCount": 1,
    "sourceCitationCount": 1,
    "sourceContextRefIds": ["ctx_123_001"],
    "sourceCitationIndexes": [1],
    "sourceEvaluationId": "eval_123",
    "sourceEvaluationChecksum": "sha256:evaluation",
    "evaluationStatus": "PASSED"
  }
}
```

Provider response schema:

- `avatarProvider.provider` and `avatarProvider.requestedProvider` are provider
  IDs, not hardcoded provider enums.
- `providerMode` is constrained to `LOCAL`, `DISABLED`, or
  `OPTIONAL_EXTERNAL`.
- `providerConfig` is a separate validated response model that records adapter
  kind, network/key requirements, real-video capability, and cloned-identity
  capability. Stage 7 validates it the same way it validates provider artifacts,
  because Stage 6 showed that all provider-produced surfaces must be checked
  from the first implementation, not added after review. Any successful Stage 7
  render that advertises network egress, API keys, real video, cloned identity,
  or an external stub as the producing adapter is rejected with
  `PROVIDER_OUTPUT_INVALID`.
- `renderJobStatusHistory` records lifecycle events such as `QUEUED`, `RUNNING`,
  `FALLBACK`, `FAILED`, and `COMPLETED`; failed optional provider stubs fall
  back to the mock/local provider and keep the final job status `COMPLETED` only
  after fallback artifacts pass validation.
- Failed idempotent render attempts are retained as terminal failed records; an
  identical retry returns the same failure without re-entering the provider.
  Stage 7 semantic validation failures such as missing consent and cloned
  identity requests are retained when an idempotency key is supplied; replaying
  the key with a changed request returns `IDEMPOTENCY_CONFLICT`.
- Missing or invalid durable consent state returns `AVATAR_CONSENT_RECORD_REQUIRED`
  or `AVATAR_CONSENT_INVALID` even when the request boolean is `true`.
- Current Stage 7 local/dev/test behavior uses `mock` and `LOCAL`.
- Adding another adapter requires code changes in `backend/app/stage7.py`,
  API/contract updates in this file, tests in `tests/unit` and `tests/api`,
  third-party notices, public-use license review, environment-only key handling,
  consent/provenance review for identity features, and provider-output
  validation before activation.

Failure modes:

| Status | Code | Meaning |
|---:|---|---|
| 400 | `IDEMPOTENCY_KEY_REQUIRED` | Missing `Idempotency-Key` on the write request |
| 403 | `FORBIDDEN` | Project or source run is not accessible to the principal |
| 404 | `NOT_FOUND` | Project or source walkthrough run does not exist |
| 409 | `IDEMPOTENCY_CONFLICT` | Idempotency key was reused with a different request body |
| 409 | `IDEMPOTENCY_IN_PROGRESS` | Duplicate request arrived while the first request is still pending |
| 413 | `SOURCE_SCRIPT_TOO_LARGE` | Accepted source script exceeds the Stage 7 source limit |
| 413 | `PROVIDER_OUTPUT_TOO_LARGE` | Avatar provider output exceeds the Stage 7 output limit |
| 422 | `SOURCE_RUN_NOT_RENDERABLE` | Source run is not completed, passed, or accepted |
| 422 | `CLONED_IDENTITY_DISABLED` | Cloned identity rendering is disabled in Stage 7 |
| 422 | `AVATAR_CONSENT_REQUIRED` | Synthetic avatar export consent was not provided |
| 422 | `PROVIDER_OUTPUT_INVALID` | Provider output is invalid or failed artifact/disclosure validation, including duplicate JSON keys in provider JSON artifacts |
| 422 | `VALIDATION_ERROR` | Request boundary validation failed, including provider field limits |
| 429 | `RESOURCE_LIMIT_EXCEEDED` | Stage 7 idempotency record limit is exceeded for the request scope |
| 502 | `PROVIDER_RENDER_FAILED` | Avatar provider and fallback render both failed before a valid export could be produced |

Frontend download links remain disabled until the response artifact matches the
expected MIME type, file extension, base64/UTF-8 decoding, decoded size limit,
checksum, JSON schema marker for JSON artifacts, active-HTML blocklist for HTML
artifacts, and safe filename rules.

### List Walkthrough Runs

`GET /api/v1/projects/{projectId}/walkthrough-runs?page=1&pageSize=20`

### Get Walkthrough Run

`GET /api/v1/projects/{projectId}/walkthrough-runs/{runId}`

### Get Evaluation Result

`GET /api/v1/projects/{projectId}/walkthrough-runs/{runId}/evaluation`

Response `200`:

```json
{
  "evaluationId": "eval_123",
  "runId": "run_123",
  "tenantId": "tenant_local",
  "projectId": "proj_123",
  "evaluationStatus": "PASSED",
  "groundednessScore": 1.0,
  "faithfulness": 1.0,
  "answerRelevancy": 1.0,
  "contextPrecision": 1.0,
  "contextRecall": 1.0,
  "unsupportedClaimCount": 0,
  "unsupportedClaims": [],
  "claimSupports": [
    {
      "claimSupportId": "claimsup_123",
      "tenantId": "tenant_local",
      "projectId": "proj_123",
      "runId": "run_123",
      "evaluationId": "eval_123",
      "claimId": "claim_123",
      "contextRefId": "ctx_123",
      "chunkId": "chunk_123",
      "documentId": "doc_123",
      "supportStatus": "SUPPORTED",
      "supportScore": 1.0,
      "supportReason": "The claim is directly supported by the cited chunk.",
      "evidenceSnapshot": {
        "evidenceSnapshotId": "evsnap_123",
        "tenantId": "tenant_local",
        "projectId": "proj_123",
        "documentId": "doc_123",
        "chunkId": "chunk_123",
        "sourceFilename": "project-summary.md",
        "chunkIndex": 0,
        "sourceDocumentChecksum": "sha256:doc",
        "chunkChecksum": "sha256:chunk",
        "chunkingStrategyVersion": "stage4-chunk-v1",
        "retrievalScore": 0.91,
        "redactedExcerpt": "Project fact used as evidence.",
        "excerptStart": 0,
        "excerptEnd": 30,
        "redactionFlags": [],
        "capturedAt": "2026-06-29T00:00:00Z",
        "snapshotChecksum": "sha256:snapshot"
      }
    }
  ],
  "contextRefCoverage": 1.0,
  "contextRefs": [
    {
      "contextRefId": "ctx_123",
      "tenantId": "tenant_local",
      "projectId": "proj_123",
      "claimId": "claim_123",
      "chunkId": "chunk_123",
      "documentId": "doc_123",
      "sourceFilename": "project-summary.md",
      "chunkIndex": 0,
      "checksum": "sha256:chunk",
      "scriptSpanStart": 0,
      "scriptSpanEnd": 42,
      "evidenceSnapshot": {
        "evidenceSnapshotId": "evsnap_123",
        "tenantId": "tenant_local",
        "projectId": "proj_123",
        "documentId": "doc_123",
        "chunkId": "chunk_123",
        "sourceFilename": "project-summary.md",
        "chunkIndex": 0,
        "sourceDocumentChecksum": "sha256:doc",
        "chunkChecksum": "sha256:chunk",
        "chunkingStrategyVersion": "stage4-chunk-v1",
        "retrievalScore": 0.91,
        "redactedExcerpt": "Project fact used as evidence.",
        "excerptStart": 0,
        "excerptEnd": 30,
        "redactionFlags": [],
        "capturedAt": "2026-06-29T00:00:00Z",
        "snapshotChecksum": "sha256:snapshot"
      }
    }
  ],
  "embeddingProvider": "mock",
  "embeddingModel": "mock-embedding",
  "embeddingModelVersion": "stage4-local-v1",
  "embeddingDimension": 16,
  "vectorStore": "memory",
  "promptTemplateVersion": "stage4-v1",
  "retrievalStrategyVersion": "stage4-rag-v1",
  "retrievalTopK": 6,
  "retrievalScoreThreshold": 0.72,
  "policyVersion": "stage4-grounding-policy-v1",
  "schemaVersion": "stage4-evaluation-schema-v1",
  "safetyPolicyVersion": "stage4-safety-policy-v1",
  "evaluatorVersion": "stage4-deterministic-v1",
  "promptInjectionDetected": false,
  "languageCheck": "PASSED",
  "audienceFitCheck": "PASSED",
  "outputSchemaValid": true,
  "refusalReason": null,
  "provider": "mock",
  "providerMode": "LOCAL",
  "model": "mock-script-generator",
  "latencyMs": 100,
  "estimatedCost": 0,
  "createdAt": "2026-06-29T00:00:00Z"
}
```

## Future Media Endpoints

These endpoints are contract placeholders only. They must not be implemented before
approved stages. Stage 7 implements only the nested source-run endpoint
`POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-renders`
documented above; project-level artifact listing remains future scope.

- `POST /api/v1/projects/{projectId}/subtitle-runs`
- `POST /api/v1/projects/{projectId}/tts-runs`
- Future project-level avatar/artifact collection endpoint, exact path TBD
- `GET /api/v1/projects/{projectId}/artifacts/{artifactId}`

Future media endpoints must require:

- grounded source run reference
- disclosure metadata
- consent metadata where identity media is involved
- provider mode
- audit event

## Enums

Audience:

- `RECRUITER`
- `HIRING_MANAGER`
- `ENGINEER`
- `PRODUCT_LEADER`
- `BEGINNER`
- `GLOBAL_VIEWER`

Depth:

- `CONCISE`
- `STANDARD`
- `DEEP`

Style:

- `PLAIN`
- `CONFIDENT`
- `TECHNICAL`
- `EXECUTIVE`

Run status:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `REFUSED`
- `CANCELLED`

Evaluation status:

- `PASSED`
- `WARNING`
- `FAILED`
- `REFUSED`

Provider mode:

- `LOCAL`
- `DISABLED`
- `OPTIONAL_EXTERNAL`

Knowledge document status:

- `UPLOADED`
- `STORED`
- `QUARANTINED`
- `DELETED`

Approval status:

- `PENDING`
- `APPROVED`
- `REJECTED`

Ingestion status:

- `NOT_STARTED`
- `QUEUED`
- `RUNNING`
- `INGESTED`
- `FAILED`
- `REFUSED`
- `CANCELLED`
- `INVALIDATED`

Project status:

- `ACTIVE`
- `DELETED`

Claim support status:

- `SUPPORTED`
- `UNSUPPORTED`
- `AMBIGUOUS`

Claim status:

- `SUPPORTED`
- `UNSUPPORTED`
- `AMBIGUOUS`
- `MISSING_CONTEXT_REF`

Retrieval refusal reason:

- `EMPTY_CONTEXT`
- `LOW_RETRIEVAL_CONFIDENCE`
- `AMBIGUOUS_CONTEXT`
- `CROSS_PROJECT_CONTEXT`
- `UNSAFE_CONTEXT`

## List Ordering

Stage 4 list endpoints use page/pageSize pagination with page size capped at `100`
and offset depth capped at `500` records. All list endpoints must declare stable
ordering:

- projects: `createdAt desc, projectId desc`
- knowledge documents: `createdAt desc, documentId desc`
- ingestion runs: `createdAt desc, ingestionRunId desc`
- walkthrough runs: `createdAt desc, runId desc`

The data model must include indexes that match these orderings. Later stages may
replace page pagination with cursor pagination through an ADR.

## Stage 4 Language Scope

Stage 4 accepts only `requestedLanguage = "en"`. Any other requested language returns
`422 UNSUPPORTED_LANGUAGE_FOR_STAGE` and does not call a translation or LLM provider.
Stage 6 expands this contract.

## Contract Review Checklist

- every endpoint has typed request and response schemas before implementation
- every list endpoint is paginated
- all writes validate project access
- all errors use the common error shape
- generated output includes context refs and evaluation state
- provider keys are never accepted from frontend request bodies
- future media endpoints require disclosure and consent metadata
