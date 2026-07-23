# Issue 269 C3A-CP8 Preflight

## Objective

C3A-CP8 implements the eighth Checkpoint 3A child implementation checkpoint for
public tracker issue `#249` and child issue `#269`: an executable real-browser
E2E probe for the local/mock controlled-demo path with no success-path API or
route interception.

The claim is deliberately narrow: `make checkpoint3-acceptance` dispatches a
real Playwright browser test that launches the local backend and frontend,
drives the user-visible controlled-demo workflow, and verifies runtime-bound
public-safe evidence. This completes the currently listed Checkpoint 3A probe
set only; it does not authorize Checkpoint 3B, Checkpoint 3C, hosted/public
demo work, provider setup, cloned identity, real media, or production readiness.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3A-CP8-HARNESS-001 | The Checkpoint 3 acceptance harness implements the `real-browser E2E with no success-path interception` probe through `npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts`, with `shell=False`, `timeout=120`, and bounded/redacted failure output. |
| C3A-CP8-BROWSER-001 | The Playwright probe launches local backend and frontend processes, opens the browser UI, fills approved synthetic project knowledge, approves and ingests it through user-visible controls, generates grounded output, and captures public-safe run/request/source/eval/artifact/observability evidence from browser-observed API-backed state. |
| C3A-CP8-NO-INTERCEPTION-001 | The success path uses no `page.route`, no `context.route`, no `route.fulfill`, no HAR replay, no MSW success mock, and no API-only substitute; Playwright observes network requests and responses without fabricating success. |
| C3A-CP8-BINDING-001 | Browser evidence is bound to a runtime nonce, project/document/ingestion/run/evaluation IDs, API request sequence, source citations, artifact metadata, local/mock provider posture, and bounded ops/status evidence from the same runtime session. |
| C3A-CP8-REDACTION-001 | The browser test and harness keep raw uploaded content, prompt-injection text, private-looking markers, sensitive tokens, provider payloads, generated full script text, timeout output, and server/browser failures bounded and redacted. |
| C3A-CP8-FALSEPASS-001 | Docs/prose/static-snapshot checks, API-only tests, route/network interception that fabricates success, canned success files, success-shaped browser state without runtime nonce/source/run binding, missing run/request/source/eval binding, stale evidence, and cross-project replay cannot pass. |
| C3A-CP8-NONGOAL-001 | CP8 remains local/mock Checkpoint 3A evidence only. |

## Scope

In scope:

- `scripts/quality/check_checkpoint3_acceptance.py`
- `frontend/playwright.checkpoint3.config.ts`
- `frontend/tests/checkpoint3-real-browser.spec.ts`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `docs/ADR/0033-checkpoint3-real-browser-acceptance-evidence.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md`
- `docs/governance/preflights/issue-269.json`

Out of scope: no provider setup, provider SDKs, real provider calls, paid spend,
no hosted deployment, public URL, cloned voice, cloned face, digital twin,
real-person likeness, public distribution, no production-readiness claim,
Checkpoint 3B, Checkpoint 3C, Product Mode 2, Docker/runtime deployment, new
dependencies, secrets, private media, private planning files, no cloned
identity, and real personal data.

The PR may bundle repository-ledger cleanup for PR `#268` and issue `#267`
because this is a substantive child checkpoint, not a standalone status-only
follow-up. Issue #249 remains open.

Replacement PR note: PR `#272` supersedes closed PR `#271` after GitHub branch
protection could not determine the last pusher on that prior PR. The CP8 scope,
evidence boundary, local/mock posture, and issue `#249`/`#269` status remain
unchanged.

## Source Facts

Accessed date: 2026-07-23.

| Source | Fact used |
| --- | --- |
| https://playwright.dev/docs/test-webserver | Playwright `webServer` can launch local servers before tests, supports multiple web servers, uses a configured readiness URL, and supports startup timeout and `reuseExistingServer`. |
| https://playwright.dev/docs/test-configuration | Playwright configuration supports `testDir`, `testMatch`, per-test `timeout`, `use.baseURL`, and Chromium project configuration. |
| https://playwright.dev/docs/network | Playwright can monitor browser network requests and responses with events, while `page.route`/`browserContext.route` are the documented APIs for network mocking/interception. |
| https://playwright.dev/docs/api/class-page#page-route | `page.route` installs route handlers; CP8 must not use it on the success path because it can intercept and modify/fulfill requests. |
| https://docs.python.org/3/library/subprocess.html#subprocess.run | `subprocess.run` supports argument sequences, `shell=False`, timeout, stdout/stderr capture, text mode, cwd, and environment isolation. |

Repository facts:

- `frontend/package.json` locks the browser test path to Playwright `^1.61.1`
  and may receive an existing-dependency Next.js patch only if required to keep
  `make dependency-audit` green.
- `frontend/next.config.ts` proxies same-origin `/api/v1/*` browser requests to
  `NARRATWIN_API_PROXY_TARGET`, defaulting to the local backend.
- `frontend/src/app/page.tsx` already exposes the user-visible project,
  knowledge-document, approval, ingestion, grounded generation, multilingual,
  synthetic-avatar consent, avatar render, citation, trace metadata, and artifact
  surfaces needed for the controlled-demo path.
- `frontend/tests/real-stack.spec.ts` is prior real-stack evidence and remains
  separate; CP8 adds a Checkpoint 3A-specific browser probe and config instead
  of reusing an API-only test.
- CP1 through CP7 already execute local/mock API probes and must remain
  unchanged except for the harness reporting CP8 as implemented.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3A-CP8-HARNESS-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_all_checkpoint3a_probes` | planned RED before harness implementation, green before PR |
| C3A-CP8-BROWSER-001 | `frontend/tests/checkpoint3-real-browser.spec.ts` and `npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts` | planned RED/green before PR; first-class UI rendering covers the user-visible workflow/output while request/source/eval/artifact/observability IDs are captured from API-backed browser network state and bounded browser fetches |
| C3A-CP8-NO-INTERCEPTION-001 | Static CP8 Playwright canary plus runtime network-observation evidence with no `page.route`, no `context.route`, no `route.fulfill`, no HAR replay, and no MSW success mock | planned RED/green before PR |
| C3A-CP8-BINDING-001 | Runtime nonce, API request sequence, browser-visible run/trace/citation/artifact metadata, request/response binding, source/evaluation binding, and bounded ops/status fetch | planned RED/green before PR |
| C3A-CP8-REDACTION-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_real_browser_e2e_fields` and browser failure-output constraints | planned RED/green before PR |
| C3A-CP8-FALSEPASS-001 | Harness command canaries, static Playwright interception canary, and browser evidence contract mutation assertions | planned RED/green before PR |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3A-CP8-FALSEPASS-001 | The browser probe must not pass by grepping docs, reading planned prose, checking static snapshots, using canned success files, or accepting API-only results. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_browser_probe_api_only_or_static_commands` |
| C3A-CP8-NO-INTERCEPTION-001 | Route/network interception that fabricates success must not satisfy CP8. | Static assertions against `frontend/tests/checkpoint3-real-browser.spec.ts` and runtime evidence recording `noSuccessPathInterception: true` |
| C3A-CP8-BINDING-001 | Success-shaped browser state without runtime nonce/source/run binding, missing run/request/source/eval binding, stale evidence, and cross-project replay cannot pass. | Browser helper mutation assertions and API request sequence/source/eval binding checks |
| C3A-CP8-REDACTION-001 | Raw uploaded content, prompt-injection text, private-looking markers, sensitive tokens, provider payloads, generated full script text, timeout output, and browser/server failures must not appear in bounded failure output. | Harness redaction canary plus browser evidence avoiding raw generated script dumps |
| C3A-CP8-NONGOAL-001 | The probe must remain local/mock and must not claim hosted/public demo, provider setup, cloned identity, real media, public distribution, Checkpoint 3B, Checkpoint 3C, or production readiness. | Scope docs, status docs, and Playwright evidence limitations |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3A-CP8-FM-001 | Harness leaves CP8 planned. | Implemented probe labels require CP1 through CP8 and final harness output reports `8 passed, 0 planned, 0 failed` when all pass. |
| C3A-CP8-FM-002 | Harness points CP8 to docs/prose/static snapshot or API-only pytest. | Command validator requires the exact `npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts` command and forbids docs/static/snapshot/prose/pytest/`rg`/`cat` substitutions for CP8. |
| C3A-CP8-FM-003 | Browser test fabricates success through `page.route`, `context.route`, `route.fulfill`, HAR replay, or MSW. | CP8 static test canary rejects those terms in the CP8 spec/config and runtime evidence records `noSuccessPathInterception: true`. |
| C3A-CP8-FM-004 | Browser evidence is a canned success file or success-shaped DOM state. | Evidence contract requires runtime nonce text in the upload, live API calls, browser-visible trace/run/citation/artifact metadata, and same-session ops/status response. |
| C3A-CP8-FM-005 | Missing request/source/evaluation/artifact binding passes. | Browser and harness assertions bind project/document/ingestion/run/evaluation/consent IDs, browser-observed request/response sequence, upload request payload nonce, source/eval binding, citation indexes, artifact metadata, independently recomputed idempotency evidence, ops/status, and local/mock provider posture. |
| C3A-CP8-FM-006 | Stale or cross-project replay of valid-looking browser evidence passes. | A second runtime project/run mutation must fail the evidence helper; runtime nonce, request sequence, source/eval binding, and independently recomputed idempotency evidence reject stale reuse without storing raw request bodies. |
| C3A-CP8-FM-007 | Raw uploaded content, prompt-injection text, private-looking markers, sensitive tokens, provider payloads, or generated full script text leak in bounded failure output. | Harness redaction patterns cover CP8 browser evidence fields and canaries; browser evidence records metadata, hashes, counts, booleans, and bounded snippets rather than raw generated script output. |
| C3A-CP8-FM-008 | Browser/server timeout or startup failure hangs CI or leaks internals. | Harness uses a 120-second subprocess timeout and redacted summaries; Playwright config uses bounded server/test timeouts. |
| C3A-CP8-FM-009 | CP8 overclaims hosted/public/demo/production readiness, real media, provider enablement, or cloned identity. | Docs/status/probe evidence list local/mock-only limitations and no provider/public/production claims. |

## Fan-Out Review Findings

Pre-implementation sub-agent fan-out ran before implementation. Final
sub-agent fan-out completed before PR after implementation.

Required fan-out prompts before implementation covered:

- Browser/no-success-interception design.
- Synthetic-data and public/private boundary.
- API/frontend interface behavior.
- Performance/flakiness risk.
- Security/redaction preservation.
- Observability metadata preservation.
- Output correctness and grounding preservation.
- Access/replay/idempotency preservation.
- Quota/retention regression risk.
- Test/quality/CI.
- Governance/taste/scope.

Disposition before implementation:

- Browser/API/frontend/observability finding accepted: the frontend already
  renders the user-visible controlled-demo workflow and output, but not every
  project/document/ingestion/evaluation identifier as first-class UI text. CP8
  therefore captures request/source/eval/artifact/observability evidence through
  browser-observed API responses and bounded browser fetches while keeping the
  UI unchanged.
- Harness finding accepted: the CP8 probe must be implemented, included in the
  exact command allowlist, and counted in the final eight-probe acceptance
  result.
- Security/redaction finding accepted: ambient provider keys and provider
  selector variables are cleared before probe subprocess dispatch; CP8 failure
  output fields are added to bounded redaction canaries.
- Governance/status finding accepted: exact public-safety markers are included,
  CP7 repository-ledger wording is reconciled inside this material CP8 PR, and
  issue `#249` remains open.

Final fan-out disposition before PR:

- Browser/no-success-interception finding accepted and fixed: the harness no
  longer accepts CP8 zero-exit output alone. It requires the CP8 Playwright test
  title, `1 passed`, no skipped tests, and a fresh bounded evidence artifact
  with runtime IDs, request sequence, source/eval binding, artifact metadata,
  ops/status, and provider posture.
  Canary coverage:
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_skipped_cp8_browser_probe`
  and
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_zero_exit_without_browser_evidence`,
  plus
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_minimal_success_shaped_evidence`.
- Browser binding finding accepted and fixed: CP8 evidence now records bounded
  upload request payload nonce booleans and per-step observed/expected
  idempotency evidence. The Python harness independently recomputes the
  expected idempotency keys from the runtime nonce and consent record, then
  rejects boolean-only or self-attested fabricated idempotency evidence. Missing
  runtime nonce request binding is rejected through
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_evidence_without_nonce_request_binding`
  and missing runtime idempotency binding through
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_evidence_without_idempotency_binding`,
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_boolean_only_idempotency_evidence`,
  and
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_self_attested_idempotency_evidence`.
- Security/public-boundary finding accepted and fixed: direct Playwright runs
  now force local/mock provider posture and blank Langfuse/provider key/state
  variables in `frontend/playwright.checkpoint3.config.ts`, with canary coverage
  in
  `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_browser_config_forces_local_mock_environment`.
- API/frontend interface, observability, replay/idempotency, and
  quota/retention review returned clean.
- Manual governance/taste/scope review accepted one documentation cleanup:
  removed a duplicated historical allowlist line without expanding CP8 scope.
- Final sub-agent fan-out findings were accepted and fixed. The final
  governance review returned clean on first-commit, allowlist, scope, status,
  traceability, and public-safety wording. The final browser/harness review
  returned clean after confirming that self-attested idempotency artifacts are
  rejected by independent recomputation and that no success-path interception,
  provider setup, hosted/public demo, cloned identity, real media, or
  production-readiness claim is introduced.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue, branch, first-commit preflight, allowlist tests, browser test, harness, docs, validation, PR, CI watch, and approval-bound merge closeout. |
| spec-driven-development | Invoked | CP8 contract and failure matrix are defined before implementation. |
| test-driven-development | Invoked | Unit and browser regressions are added before harness implementation is completed. |
| source-driven-development | Invoked | Official Playwright and Python subprocess sources are cited. |
| security-and-hardening | Invoked | Synthetic fixtures, provider env clearing, public-safe failure output, prompt-injection text canaries, and sensitive token redaction are part of CP8. |
| api-and-interface-design | Invoked | Existing same-origin frontend proxy, API request sequence, idempotency, response metadata, and error shapes are asserted without adding API endpoints. |
| observability-and-instrumentation | Invoked | Browser-visible trace/run/evaluation metadata, local/mock provider posture, request sequence, and ops/status evidence are tested. |
| performance-optimization | Invoked | CP8 uses broad deterministic waits and startup/test timeouts, avoiding flaky micro-timing assertions. |
| code-review-and-quality | Invoked | Fan-out findings and dispositions are recorded before implementation and refreshed before human review. |
| doubt-driven-development | Invoked | False-pass, API-only, route-intercepted, canned success, missing binding, stale evidence, cross-project replay, timeout, and redaction risks are encoded as canaries. |
| taste-check | Invoked | CP8 adds a focused browser probe/config instead of new runtime abstractions or dependencies. |
| git-workflow-and-versioning | Invoked | Issue `#269`, dedicated branch, and preflight-only first commit preserve workflow. |
| frontend-ui-engineering | Invoked | CP8 validates the existing user-visible browser workflow; no frontend behavior change is planned unless the test exposes a real defect. |
| browser-testing-with-devtools | Rejected | CI needs deterministic Playwright regression evidence; DevTools exploration remains optional for diagnosis only. |

## Stop Rule

Stop and open a new issue if CP8 requires provider setup, provider SDKs, real
provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned
face, digital twin, real-person likeness, Checkpoint 3B, Checkpoint 3C, Product
Mode 2, Docker/runtime changes, new dependencies, private data, private media,
private planning files, secrets, or real personal data.
