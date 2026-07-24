# Issue 280 C3A-R3 PR C Preflight

Date: 2026-07-24

Issue: `#280` C3A-R3

Branch: `phase-1-closure-280-c3a-r3-pr-c-local-e2e-demo-slice`

## Scope

PR C implements the next executable local/mock slice from the PR B contract:

- accept bounded arbitrary synthetic markdown through the existing PR B request
  contract;
- create a resettable local synthetic demo session;
- ingest, chunk, store, and retrieve approved synthetic markdown locally;
- generate deterministic citation-bound walkthrough script text;
- produce narrow local/mock multilingual transcript segments for `en`, `hi`,
  and `es`;
- evaluate generated claims against retrieved/source context;
- store generated output and evaluation metadata in issue-scoped in-memory
  persistence;
- expose the result through `/api/v1/checkpoint3/issue280/local-e2e-demo`.

PR C does not touch UI and therefore exact UI/browser tests are not applicable
for this slice. PR C does not implement the final
`make issue280-output-correctness` closure gate and does not satisfy all of
issue `#280`.

PR C does not implement hosted/public demo behavior, provider setup, provider
SDKs, provider keys, paid spend, real provider calls, cloned identity runtime,
cloned voice, cloned face, digital twin, real-person likeness, real media,
public distribution, arbitrary real-world translation quality, provider
quality, or production-readiness claims. Issues `#249` and `#280` remain open
after PR C.

## Source Facts

- FastAPI response models are declared on route decorators and used to validate
  and document response shapes. Source:
  `https://fastapi.tiangolo.com/tutorial/response-model/`, verified
  2026-07-24.
- FastAPI supports explicit exception handlers for request validation and
  custom exceptions, which supports mapping malformed local-demo requests into
  the locked public-safe Issue 280 taxonomy. Source:
  `https://fastapi.tiangolo.com/tutorial/handling-errors/`, verified
  2026-07-24.
- Pydantic models provide typed validation and model serialization hooks for
  stable request/response models without ad hoc response dictionaries. Sources:
  `https://docs.pydantic.dev/latest/concepts/models/` and
  `https://docs.pydantic.dev/latest/concepts/serialization/`, verified
  2026-07-24.
- The PR B contract artifact locks the accepted synthetic markdown, glossary,
  audience, language, safety, and error posture reused by PR C:
  `docs/reviews/ISSUE_280_C3A_R3_PR_B_PREFLIGHT.md`.
- The PR A matrix says issue `#280` remains open until all R280 rows have
  executable evidence or reviewed re-scope:
  `reports/checkpoint3-issue280/requirement-matrix.json`.

## Skill Selection

Invoked:

- `planning-and-task-breakdown`: bounded PR C to local/mock API e2e rows and
  kept UI, hosted, provider, media, cloned identity, and final gate rows out of
  scope.
- `spec-driven-development`: mapped PR C-owned R280 rows into endpoint,
  response, storage, multilingual, evaluation, and metadata contracts.
- `test-driven-development`: added RED acceptance tests before implementation;
  initial run failed with endpoint `404` and a missing generated-script hook,
  then passed after the local/mock service and route were implemented.
- `source-driven-development`: checked official FastAPI and Pydantic docs
  before extending route, error, and response-model patterns.
- `security-and-hardening`: reused the PR B validator and error taxonomy,
  rejected unsafe/private/secret-like input and prompt injection, and kept raw
  markdown, secrets, paths, provider internals, and stack traces out of errors.
- `api-and-interface-design`: reused the PR B request shape, added a
  response-model-backed endpoint, stable request IDs, idempotency replay, and
  provider-disabled posture fields.
- `observability-and-instrumentation`: added local trace metadata, provider
  posture, checksums, context refs, evaluation IDs, and stored-output metadata
  without raw submitted document leakage.
- `code-review-and-quality`: added acceptance/unit/guardrail regression tests
  and updated ADR, status, quality, stage, traceability, and matrix evidence.
- `doubt-driven-development`: rechecked overclaim boundaries and rejected any
  claim that API evidence proves UI, hosted, provider, media, real-world
  quality, or production readiness.
- `git-workflow-and-versioning`: used the dedicated PR C branch from the
  verified `main`/`origin/main` baseline.
- `taste-check`: kept the local demo behavior isolated in the issue-specific
  module instead of broad refactors across Stage 4/6/7 services.

Rejected or deferred:

- `frontend-ui-engineering` and browser-testing skills: rejected because PR C
  does not touch UI. Exact UI/browser evidence remains a future row.
- Provider, hosted, media, or cloned-identity skills/tests: rejected because
  those surfaces are explicit non-goals for PR C.
- Final `make issue280-output-correctness`: deferred because PR C implements a
  narrow local/mock API slice, not complete issue `#280` closure.

## RED Evidence

Before implementation, the new PR C acceptance file failed:

```text
uv run pytest tests/acceptance/test_issue280_local_e2e_demo.py -q
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_accepts_synthetic_markdown_and_stores_grounded_multilingual_result - assert 404 == 201
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_replays_deterministically_with_idempotency_key - assert 404 == 201
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_rejects_unsupported_language_with_safe_error - assert 404 == 422
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_rejects_prompt_injection_and_secret_like_input_safely - assert 404 == 422
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_rejects_unsupported_file_type_without_raw_content - assert 404 == 415
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_maps_malformed_request_to_safe_error - assert 404 == 400
FAILED tests/acceptance/test_issue280_local_e2e_demo.py::test_issue280_local_e2e_demo_rejects_unsupported_generated_claim_attempt - AttributeError: module 'backend.app.issue280' has no attribute '_render_grounded_script'
```

## Test Level Mapping

| Required family | PR C evidence |
|---|---|
| Positive cases | `tests/acceptance/test_issue280_local_e2e_demo.py` proves valid bounded synthetic markdown creates a stored grounded walkthrough result with multilingual segments. |
| Negative cases | The same acceptance file rejects unsafe/private/secret-like input, prompt injection, unsupported file type, malformed request, unsupported language, and unsupported generated claim attempts with public-safe errors. |
| Corner cases | Boundary document count, repeated headings, empty-but-valid sections, max glossary terms, audience/depth/language edges, and deterministic replay are covered. |
| API tests | The acceptance file checks status codes, response schema, request ID, provider-disabled posture, idempotency replay metadata, and no raw markdown leakage. |
| Contract tests | PR B tests continue to pass unchanged, and PR C uses `Issue280InputContractRequest` plus the existing Issue 280 error taxonomy. |
| Unit tests | `tests/unit/test_issue280_contract.py` covers fact extraction and unsupported-claim evaluation helpers. |
| Exact UI tests | Not applicable because PR C does not touch UI. UI rows remain open. |
| Regression tests | Existing PR A/PR B tests continue passing with the new endpoint and service reset behavior. |

## Human Review Surfaces

- Confirm `/api/v1/checkpoint3/issue280/local-e2e-demo` never returns the full
  raw submitted markdown and never includes raw inputs in errors.
- Confirm generated script claims are citation-bound and claim supports map to
  retrieved local facts.
- Confirm provider posture remains local/mock/disabled and no provider setup,
  paid spend, real provider calls, hosted/public demo behavior, cloned identity
  runtime, real media, public distribution, or production-readiness claim is
  introduced.
- Confirm UI was not touched and exact UI/browser evidence is not claimed.
- Confirm #249 and #280 are reference-only and remain open after PR C.

## Remaining Rows

PR C claims executable evidence for the PR C-owned local end-to-end API slice
rows represented by `R280-S4-001`, `R280-S6-001`, and the narrow
`R280-GOV-003` branch/status update. The remaining R280 rows still require
later executable evidence or reviewed re-scope before issue `#280` can close.

## Stop Rule

Do not merge PR C unless local required validation passes, GitHub CI is green,
and a human approves the exact latest PR head. After merge, keep issue `#249`
open and keep issue `#280` open unless every R280 row is actually satisfied or
reviewed/re-scoped.
