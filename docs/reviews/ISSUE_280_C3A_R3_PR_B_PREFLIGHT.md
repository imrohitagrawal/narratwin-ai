# Issue 280 C3A-R3 PR B Preflight

Date: 2026-07-24

Issue: `#280` C3A-R3

Branch: `phase-1-closure-280-c3a-r3-pr-b-input-api-error-contract`

## Scope

PR B implements only the first executable contract slice from PR A:

- bounded arbitrary synthetic `text/markdown` input contract
- `/api/v1/checkpoint3/issue280/input-contract` request/response contract
- public-safe Issue 280 error taxonomy
- prompt-injection rejection
- unsafe/private/secret-like input rejection
- local/mock provider-disabled posture
- positive, negative, corner, API, contract, and regression tests for this slice

PR B does not implement the full local end-to-end multilingual demo, exact UI
evidence, hosted/public demo behavior, provider setup, provider SDKs, provider
keys, paid spend, real provider calls, cloned identity runtime, real media,
public distribution, arbitrary real-world translation quality, provider
quality, or production-readiness claims. Issues `#249` and `#280` remain open
after PR B.

## Source Facts

- FastAPI response models are declared on route decorators and used to validate
  and document response shapes. Source: `https://fastapi.tiangolo.com/tutorial/response-model/`
- FastAPI supports `APIRouter` route registration under an application prefix,
  matching the existing `/api/v1` app shape. Source:
  `https://fastapi.tiangolo.com/reference/apirouter/`
- FastAPI supports explicit exception handlers for request validation and custom
  exceptions, allowing the Issue 280 endpoint to map malformed payloads into the
  locked public-safe taxonomy. Source:
  `https://fastapi.tiangolo.com/tutorial/handling-errors/`
- FastAPI tests use Starlette `TestClient`, which is the existing API-test
  pattern in this repository. Sources:
  `https://fastapi.tiangolo.com/tutorial/testing/` and
  `https://www.starlette.io/testclient/`
- Pydantic v2 validators and typed models provide structured request parsing
  without ad hoc string parsing. Source:
  `https://docs.pydantic.dev/latest/concepts/validators/`

## Skill Selection

Invoked:

- `planning-and-task-breakdown`: bounded PR B to R280 input/API/error rows and
  kept full e2e, UI, provider, hosted, and media rows out of scope.
- `spec-driven-development`: converted PR A matrix rows into an executable
  request/response/error contract.
- `test-driven-development`: added RED acceptance tests before the endpoint and
  then implemented the smallest passing validator/route.
- `source-driven-development`: checked official FastAPI, Starlette, and
  Pydantic docs before selecting route, test-client, and model/error patterns.
- `security-and-hardening`: reused existing prompt-injection and secret-like
  detectors and kept raw markdown/provider/path/secret-like values out of API
  errors.
- `api-and-interface-design`: kept a versioned, bounded, response-model-backed
  contract with stable request IDs and provider posture fields.
- `observability-and-instrumentation`: preserved `X-Request-Id` and returned
  bounded trace metadata without raw inputs or provider internals.
- `code-review-and-quality`: added unit and acceptance coverage plus branch
  allowlist regression tests for the changed scope.
- `doubt-driven-development`: rejected overbroad test assertions that banned
  taxonomy vocabulary instead of raw input leakage, and kept duplicate glossary
  terms out of the rejection surface because the bounded corner test exercises
  repeated maximum-length terms.
- `git-workflow-and-versioning`: used a dedicated issue branch from current
  `main` and kept PR B file scope exact.
- `taste-check`: kept the endpoint as a small contract module rather than
  mixing temporary Issue 280 validation into Stage 4/6/7 services.

Rejected or deferred:

- exact UI tests: not invoked because PR B does not touch UI.
- full local/mock e2e flow tests: deferred to later #280 slices because PR B
  intentionally does not implement the end-to-end multilingual demo.
- provider, hosted, media, or cloned-identity tests: rejected because those
  surfaces are explicit non-goals for PR B.

## Test Level Mapping

| Required family | PR B evidence |
|---|---|
| Positive cases | `tests/acceptance/test_issue280_input_contract.py` accepts bounded synthetic markdown and exact document/glossary bounds. |
| Negative cases | Input/API/error tests reject unsafe, prompt-injection, oversized, wrong-type, too-many-document, invalid-glossary, malformed request, and safe-internal failures. |
| Corner cases | Exact `maxDocuments=3` and `maxGlossaryTerms=20` with 64-character terms are accepted. |
| API tests | `tests/acceptance/test_issue280_api_contract.py` checks status codes, response keys, request ID, error envelope, and local/mock provider posture. |
| Contract tests | `tests/acceptance/test_issue280_error_taxonomy.py` locks safe messages/details/remediation for PR B-triggered taxonomy codes. |
| Exact UI tests | Not touched in PR B; remains planned in R280 UI rows. |
| Regression tests | `tests/unit/test_issue280_contract.py` covers validator bounds and safe rejection; `tests/unit/test_phase1_closure_docs.py` covers PR B allowlist and #280-open gate behavior. |

## Remaining Rows

PR B claims executable evidence only for the PR B-owned input/API/error contract
rows represented by `R280-INPUT-001`, `R280-INPUT-002`,
`R280-ERROR-001`, `R280-TEST-STRATEGY-002`, and the narrow
`R280-GOV-002` branch-gate update. The remaining R280 rows still require later
executable evidence or reviewed re-scope before issue `#280` can close.

## Human Review Surfaces

- Confirm the endpoint response never includes raw submitted markdown.
- Confirm every error response remains public-safe and uses the global
  `error.requestId` envelope.
- Confirm provider posture remains local/mock/disabled and no provider setup,
  paid spend, hosted/public demo, cloned identity runtime, real media, public
  distribution, or production-readiness claim is introduced.
- Confirm #249 and #280 are reference-only and remain open after PR B.
