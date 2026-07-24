# Issue 280 C3A-R3 PR D Preflight

Date: 2026-07-24

Branch: `phase-1-closure-280-c3a-r3-pr-d-ui-browser-demo-slice`

Refs: `#249`, `#280`

## Objective

PR D adds exact user-visible UI and browser evidence for the merged PR C local/mock
API path:

`POST /api/v1/checkpoint3/issue280/local-e2e-demo`

The slice proves only the PR D-owned rows:

- `R280-UI-001`
- `R280-UI-002`
- `R280-CONVERSATION-UX-001`
- `R280-TEST-STRATEGY-004`
- narrow `R280-GOV-004`

## Non-Goals

PR D does not satisfy all of issue `#280`. It does not implement the final
`make issue280-output-correctness` closure gate, hosted/public demo behavior,
provider setup, paid spend, real provider calls, cloned identity runtime, cloned
voice, cloned face, digital twin behavior, real-person likeness, real media,
public distribution, arbitrary real-world translation quality, provider quality,
or production-readiness claims.

Issues `#249` and `#280` remain open after PR D unless every remaining R280 row
is later satisfied with executable evidence or explicitly reviewed/re-scoped.

## Source Facts

| Source | Fact Used |
|---|---|
| `backend/app/main.py` | PR D must call the locked `201` API path `POST /api/v1/checkpoint3/issue280/local-e2e-demo`. |
| `backend/app/issue280.py` | PR D must preserve the PR C request model, `ISSUE280_*` safe error taxonomy, local/mock provider-disabled posture, in-memory output storage, and supported local languages `en`, `hi`, and `es`. |
| `frontend/next.config.ts` | UI calls can use `/api/v1/...`; Next rewrites proxy same-origin requests to `NARRATWIN_API_PROXY_TARGET`. |
| React docs, `https://react.dev/reference/react/useState` | Client state is appropriate for loading, empty, success, replay, and safe-refusal UI state. |
| Next.js docs, `https://nextjs.org/docs/app/api-reference/directives/use-client` | The existing page is a client component and may use browser event handlers and state. |
| Playwright docs, `https://playwright.dev/docs/test-configuration` | A dedicated config can launch backend and frontend web servers, use desktop/mobile projects, and place output under issue-scoped evidence paths. |
| Playwright docs, `https://playwright.dev/docs/network` | Browser tests can observe request and response events without intercepting the success path. |

## Skill And Evidence Selection

| Skill | Used For | Evidence Required |
|---|---|---|
| planning-and-task-breakdown | PR D row mapping and work sequencing | This preflight and matrix row ownership. |
| spec-driven-development | Explicit slice contract before coding | Failure matrix below and PR body reviewer overview. |
| test-driven-development | Browser tests added before implementation | RED run of the new Issue 280 Playwright config before UI implementation. |
| source-driven-development | Official docs for React, Next.js, and Playwright usage | Source facts above plus local repo contract files. |
| security-and-hardening | Safe rendering, no raw leak, screenshot discipline | Browser anti-leak assertions and no committed raw traces. |
| api-and-interface-design | Frontend-only adapter over locked PR C response | No backend contract changes. |
| observability-and-instrumentation | User-visible request/session/output/eval trace metadata | UI renders bounded request ID, session ID, output ID, checksums, and replay flag. |
| frontend-ui-engineering | Accessible form, tooltips, mobile layout, keyboard flow | Playwright desktop/mobile checks and Vitest static checks. |
| browser-testing-with-devtools | Real browser path evidence | Dedicated Playwright verifier with request/response observation. |
| code-review-and-quality | Pre-PR review pass | Local code review findings recorded in PR body. |
| doubt-driven-development | Overclaim and false-pass review | Doubt review before PR creation. |
| git-workflow-and-versioning | Issue branch and PR workflow | Branch allowlist, no direct main commit, PR guardrail after PR creation. |
| taste-check | Scope and simplicity review | Local review confirms no parallel backend contract or broad refactor. |

Skill invocation alone is not evidence. Only result-bearing tests, verifier
output, browser observations, and reviewed source facts prove the claims.

## Sub-Agent Review Input

| Review Pass | Result |
|---|---|
| Matrix planner | PR D owns only UI, conversation UX, exact UI test strategy, and narrow governance rows; PR E rows must remain planned. |
| UI/UX reviewer | Current frontend is Stage 4/6/7 oriented and needs a separate Issue 280 UI adapter, accessible tooltips, DEEP, retry, mobile, and no-overclaim copy. |
| API contract reviewer | Backend contract is locked; PR D must adapt nested PR C fields in the frontend only and allowlist safe `ISSUE280_*` errors. |
| Security reviewer | Do not retain raw Playwright traces by default; screenshots/evidence must avoid raw markdown, idempotency keys, filesystem paths, stack traces, secrets, and provider payloads. |
| Test strategy reviewer | Add dedicated Playwright config/spec with non-intercepted success path, desktop/mobile, safe errors, retry, accessibility, and output-correctness evidence. |
| Governance reviewer | Add PR D branch allowlist, matrix PR D state, status, traceability, quality gate, and stage plan updates. |
| Doubt reviewer | Completed locally after implementation: no backend contract expansion, no final `#280` closure claim, no provider/hosted/real-media claim, no committed raw trace, no label collision with existing Checkpoint 3 browser flow after accessible-name repair, and remaining PR E rows stay planned. |

## Local Review Passes

| Pass | Finding |
|---|---|
| Code review and quality | The implementation adds a frontend-only Issue 280 adapter and dedicated browser config/spec; no backend endpoint shape, success status, or PR C response model changes were made. |
| Security and hardening | Fake OpenAI-like fixture text was removed after guardrail detection; verifier evidence is ignored by git, Playwright traces are disabled in the PR D config, and generated screenshot strings plus JSON evidence were scanned for leak canaries. |
| Taste check | The change keeps the large existing page stable by adding a narrow, explicit Issue 280 view model instead of flattening PR C responses into Stage 6/7 artifact flows or introducing a parallel backend contract. |

## Failure Matrix

| Claim | Failure Mode | Required Test Or Verifier |
|---|---|---|
| UI calls the PR C endpoint | Browser test passes while using old Stage 4/6/7 path or mocked status | Observe a real network request to `/api/v1/checkpoint3/issue280/local-e2e-demo` with no success-path interception. |
| User sees stored grounded result | UI shows only success metadata or stale prior output | Assert accepted script, transcript, citations, claim support IDs, eval metadata, storage IDs, and provider posture are visible after submit. |
| Loading state is honest | Submit appears idle or leaves stale success as current state | Assert disabled action, `aria-busy`, and visible loading copy while request is in flight. |
| Empty state is honest | Empty result claims `0 unsupported claims` before evaluation exists | Assert pending copy for script, transcript, citations, evaluation, storage, provider posture, and export artifacts before submit. |
| Retry is idempotent | Retry creates unrelated output or hides replay flag | Submit same payload with same idempotency key and assert `session.replayed=true` plus stable output/checksum. |
| Safe refusals are useful | Errors degrade to generic status or echo unsafe input | Submit prompt injection, fake secret, unsupported file type, unsupported language, invalid glossary, and validation cases; assert only safe taxonomy copy renders. |
| Unsupported language is refused | UI fabricates unsupported-language output | Select unsupported local language and assert `ISSUE280_TRANSLATION_REFUSED` with no target transcript. |
| Tooltips are accessible | Help copy is mouse-only or missing required fields | Keyboard focus info controls for Project name, Knowledge document, Audience, Depth, Target language, Glossary terms, Synthetic avatar consent, Walkthrough script, Demo preview, Citations, Export artifacts, and local/mock provider posture. |
| Transcript expansion is clear | Long output hides without user-visible truncation state | Assert collapsed preview with count and an expand/collapse control that reveals all segments. |
| Mobile/touch is usable | Controls, IDs, or error text overlap/clipped | Run the same verifier in a mobile viewport and assert critical text remains visible. |
| Public-safe evidence | Screenshots/traces contain raw markdown, secrets, provider payloads, or local paths | Disable committed traces by default, screenshot output regions only, and scan evidence artifacts for leak canaries. |
| Scope remains bounded | PR D claims hosted/public/provider/production/real media/final closure | Matrix and PR body explicitly leave remaining rows planned and issues open. |

## RED Test Plan

Add `frontend/playwright.issue280.config.ts` and
`frontend/tests/issue280-ui-browser.spec.ts`, then run:

```bash
npm --prefix frontend run test:smoke -- --config=playwright.issue280.config.ts
```

Expected old behavior before UI implementation: fail because the page does not
call the PR C endpoint, lacks the Issue 280 local demo result surface, lacks
DEEP and required tooltips, and does not expose retry/refusal states through the
Issue 280 contract.

## Mandatory Output-Correctness Execution Verifier

After implementation and before PR creation, run the dedicated Playwright Issue
280 verifier against real local backend/frontend services. It must:

- open the UI in desktop and mobile browser projects;
- submit bounded arbitrary synthetic markdown through the UI;
- observe the `/api/v1/checkpoint3/issue280/local-e2e-demo` request/response;
- prove the stored grounded result, citations, context refs, claim supports,
  evaluation metadata, trace metadata, and local/mock provider posture are
  visible;
- prove loading, success, empty, replay, safe refusal, validation error,
  unsupported file type, prompt-injection rejection, unsafe/private input
  rejection, unsupported language, keyboard tooltip, and mobile behavior;
- write public-safe result-bearing evidence only;
- fail if evidence contains raw markdown canaries, fake secrets,
  `Idempotency-Key`, provider payloads, stack traces, filesystem paths,
  credentials, tokens, or provider internals.

## Stop Rule

Stop before PR creation if the dedicated browser verifier passes only through
metadata, static files, screenshots alone, mocked status, route interception of
the success path, or docs-only evidence. Stop before merge if CI is red or human
approval is absent on the exact latest PR head.
