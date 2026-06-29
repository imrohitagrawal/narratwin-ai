# API Contract

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-29
- Status: contract-first design only; no product endpoints implemented in Stage 2

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

Stage 4 local mode resolves a synthetic principal with `tenantId = tenant_local` and
`actorId = user_local`. API handlers must authorize this principal before data
access. Generated IDs are not authorization proof.

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
- `art_` for artifacts
- `audit_` for audit events

Provider-native IDs are stored as provider metadata, not canonical IDs.

## Idempotency Requirements

Idempotency keys are scoped by actor, project, endpoint, and request body checksum.
For duplicate keys:

- identical request body returns the original response or current job status
- different request body returns `409 IDEMPOTENCY_CONFLICT`
- provider calls, vector writes, and generated artifacts must not be duplicated
- idempotency records are retained for at least 24 hours in local mode

Write endpoints requiring idempotency:

- `POST /api/v1/projects`
- `POST /api/v1/projects/{projectId}/knowledge-documents`
- `PATCH /api/v1/projects/{projectId}/knowledge-documents/{documentId}/approval`
- `POST /api/v1/projects/{projectId}/ingestion-runs`
- `POST /api/v1/projects/{projectId}/walkthrough-runs`
- all future media-render endpoints

## Typed Response Schemas

The markdown examples below are illustrative, but implementation must define typed
request and response schemas before product code is accepted. Required schemas:

- `Project`
- `KnowledgeDocument`
- `IngestionRun`
- `WalkthroughRun`
- `EvaluationResult`
- `ContextRef`
- `UnsupportedClaim`
- `AuditEvent`
- `APIError`

All schemas include `tenantId`, `projectId` where project-scoped, `createdAt`, and
stable enum values. Provider-native fields live under `providerMetadata`.

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
  "name": "NarraTwin AI",
  "description": "Grounded project walkthrough generator",
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

### Delete Project

`DELETE /api/v1/projects/{projectId}`

Stage 4 delete is a soft delete for metadata plus local physical source-artifact
deletion where available. Audit events and tombstones remain.

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
  "projectId": "proj_123",
  "sourceFilename": "architecture.md",
  "contentType": "text/markdown",
  "sizeBytes": 12345,
  "checksum": "sha256:abc",
  "status": "UPLOADED",
  "createdAt": "2026-06-29T00:00:00Z"
}
```

Validation errors:

- `413` for oversized file
- `415` for unsupported type
- `422` for invalid filename or failed content validation

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
  "status": "APPROVED",
  "reviewNote": "Approved for local Stage 4 grounding."
}
```

Response `200`: knowledge document with approval status. Only `APPROVED` documents
can be ingested or retrieved.

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
  "projectId": "proj_123",
  "tenantId": "tenant_local",
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

Response `202` or `201`:

```json
{
  "runId": "run_123",
  "projectId": "proj_123",
  "status": "COMPLETED",
  "audience": "RECRUITER",
  "requestedLanguage": "en",
  "depth": "CONCISE",
  "style": "CONFIDENT",
  "scriptText": "Generated script text.",
  "contextRefs": [
    {
      "contextRefId": "ctx_123",
      "claimId": "claim_123",
      "chunkId": "chunk_123",
      "documentId": "doc_123",
      "sourceFilename": "project-summary.md",
      "scriptSpanStart": 0,
      "scriptSpanEnd": 42
    }
  ],
  "evaluation": {
    "evaluationId": "eval_123",
    "status": "PASSED",
    "groundednessScore": 1.0,
    "unsupportedClaimCount": 0,
    "unsupportedClaims": []
  },
  "provider": {
    "provider": "mock",
    "providerMode": "LOCAL"
  },
  "trace": {
    "traceId": "trace_123",
    "latencyMs": 100,
    "estimatedCost": 0
  },
  "createdAt": "2026-06-29T00:00:00Z"
}
```

Failure behavior:

- no approved context returns a persisted `REFUSED` run with `EMPTY_CONTEXT`
- unsupported project factual claims return persisted `FAILED` evaluation state
- provider failure returns structured `502` or stored failed run
- rate limits return `429`

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
  "projectId": "proj_123",
  "status": "PASSED",
  "groundednessScore": 1.0,
  "unsupportedClaimCount": 0,
  "unsupportedClaims": [],
  "contextRefs": [],
  "promptTemplateVersion": "stage4-v1",
  "retrievalStrategyVersion": "stage4-rag-v1",
  "evaluatorVersion": "stage4-deterministic-v1",
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
- `QUARANTINED`
- `APPROVED`
- `REJECTED`
- `INGESTED`
- `DELETED`

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
