# API Contract

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-30
- Status: Stage 4 branch implements the first local grounded-script endpoint path
  with mock/local providers and in-memory storage

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

## API Versioning

The initial public contract uses `/api/v1`. Backward-compatible additions are
preferred over breaking field changes. Removing fields, changing enum meaning, or
changing status semantics requires a new ADR and migration/deprecation plan.

## Common Headers

Request headers:

- `X-Request-Id`: optional caller-provided request ID
- `Idempotency-Key`: required for upload, ingestion, generation, approval, deletion,
  and future media-render write operations

Response headers:

- `X-Request-Id`: server request ID
- `Content-Type: application/json`

Stage 4 local mode resolves a synthetic principal with `tenantId = tenant_local`,
`ownerId = user_local`, and `actorId = user_local`. API handlers must enforce the
authorization predicate `(tenantId, ownerId, projectId)` before every
project-scoped lookup, retrieval, generation, evaluation, export, or delete.
Generated IDs are not authorization proof.

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
the idempotency record for conflict detection, not uniqueness. For project creation,
`idempotencyScope = "project:create"` because no `projectId` exists yet. For
project-scoped writes, `idempotencyScope = projectId`. Implementations must persist
an `IdempotencyRecord` before provider calls, vector writes, generated artifacts,
approval state changes, or tombstone writes.

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
- provider calls, vector writes, and generated artifacts must not be duplicated
- idempotency records are retained for at least 24 hours in local mode

Write endpoints requiring idempotency:

- `POST /api/v1/projects`
- `PATCH /api/v1/projects/{projectId}`
- `POST /api/v1/projects/{projectId}/knowledge-documents`
- `PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval`
- `DELETE /api/v1/projects/{projectId}/knowledge-documents/{documentId}`
- `POST /api/v1/projects/{projectId}/ingestion-runs`
- `POST /api/v1/projects/{projectId}/walkthrough-runs`
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

All schemas include `tenantId`, `projectId` where project-scoped, `createdAt`, and
stable enum values. Provider-native fields live under `providerMetadata`.
Public schemas must state whether `tenantId` and `ownerId` are returned or
server-internal. Stage 4 local API responses return `tenantId = tenant_local` and
`ownerId = user_local` in project-scoped examples to keep isolation visible.

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

Response `202`:

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

Response `201` for newly accepted terminal output. Response `200` is reserved for
idempotency replay or `GET` of an existing terminal run.

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
failure uses `201` with this shape; `200` is used only for `GET` or idempotency
replay of an existing terminal run.

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
- rate limits return `429 RATE_LIMITED`
- queue admission backpressure returns `429 BACKPRESSURE_QUEUE_FULL` with
  `Retry-After` when retry is safe
- worker or dependency unavailability returns `503 DEPENDENCY_UNAVAILABLE`

Backpressure error example:

```json
{
  "error": {
    "code": "BACKPRESSURE_QUEUE_FULL",
    "message": "The per-project queue is full. Retry after the provided interval.",
    "details": {
      "retryAfterSeconds": 60
    },
    "requestId": "req_123"
  }
}
```

Responses with `BACKPRESSURE_QUEUE_FULL` include `Retry-After`.

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
approved stages.

- `POST /api/v1/projects/{projectId}/subtitle-runs`
- `POST /api/v1/projects/{projectId}/tts-runs`
- `POST /api/v1/projects/{projectId}/avatar-renders`
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
- `MOCK`
- `FREE`
- `PREMIUM`

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
