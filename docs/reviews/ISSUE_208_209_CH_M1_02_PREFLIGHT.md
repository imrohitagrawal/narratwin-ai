# Issue #208 / #209 CH-M1-02 Preflight And Evidence

## Objective

Prepare one consolidated Phase 1 Closure PR for issue `#208` as the primary
CH-M1-02 real-stack local browser-to-Compose evidence item, with issue `#209`
included only to clarify the directly coupled local `make quality` behavior on
`main`.

Parent controller: issue `#155`.

Related parent product-definition issue: issue `#8`, which remains open unless
its full original acceptance contract is reviewed as satisfied.

## Scope

In scope:

- A non-intercepted Playwright real-stack smoke against the local Compose
  frontend and backend.
- Runtime evidence for browser -> frontend -> backend -> Compose services using
  controlled local/mock Product Mode 1.
- The narrow top-level quality dispatcher correction for Phase 1 Closure
  `main`, with Stage 8 behavior and policy-only behavior preserved.
- Directly coupled `docs/STATUS.md`, `docs/QUALITY_GATES.md`,
  `docs/STAGE_ISSUE_PLAN.md`, and `docs/TRACEABILITY.md` updates.

Out of scope:

- Product Mode 2, real audio binaries, MP4/WebM generation, STT/imported video,
  external or paid providers, hosted/internal/public launch, public media
  distribution, multi-worker or production-readiness claims, and production
  release approval.
- Backend product behavior changes, frontend product UI changes, Compose
  topology changes, provider enablement, dependency changes, workflow changes,
  stopped PRs/issues `#166`, `#167`, `#168`, `#162`, and `#163`.

## Source Facts

| Fact | Source | Engineering consequence |
|---|---|---|
| Phase 1 Closure is active and release posture is No-Go. | `docs/STATUS.md`; issue `#155` closeout comment after PR `#207` | CH-M1-02 may prove a controlled local/mock demo path only. |
| Issue `#208` owns CH-M1-02 after issue `#206`/PR `#207` closeout. | issue `#208`; issue `#155` comment `#issuecomment-5017496581` | This branch may add real-stack local evidence for CH-M1-02. |
| Issue `#209` records the plain `make quality` ambiguity on `main`. | issue `#209`; issue `#155` comment `#issuecomment-5017500418` | The dispatcher/doc fix belongs in the same PR only if it stays narrow. |
| Existing mocked Playwright smoke uses `page.route("**/api/v1/**")`. | `frontend/tests/smoke.spec.ts` | It remains mocked browser evidence and cannot satisfy CH-M1-02. |
| Next.js rewrites `/api/v1/:path*` to `NARRATWIN_API_PROXY_TARGET`. | `frontend/next.config.ts` | A Compose frontend request can prove frontend proxy to backend when no browser route interception is used. |
| Compose binds frontend, backend, Postgres, and Redis only to localhost. | `docker-compose.yml` | Evidence remains local and controlled; no hosted/public surface is created. |
| `scripts/quality/check_quality_stage.py` dispatches by branch prefix first and otherwise by `.stage/current`. | `scripts/quality/check_quality_stage.py` | `main` needs an explicit current repo-mode interpretation for Phase 1 Closure. |

## Invariant And Failure Matrix

| ID | Claim or failure mode | Required proof |
|---|---|---|
| M1C02-E2E-001 | Real browser opens the local Compose frontend and completes the Mode 1 flow through backend APIs without application-route interception. | `frontend/tests/real-stack.spec.ts` with no `page.route`; command uses `NARRATWIN_REAL_STACK=1`. |
| M1C02-E2E-002 | The browser path reaches the expected API sequence: project, upload, approval, ingestion, grounded run, multilingual run, avatar consent, avatar render. | Real-stack Playwright request-finished assertions. |
| M1C02-SCOPE-003 | The evidence remains controlled local/mock Product Mode 1 only. | UI/API assertions for mock/local metadata and docs stating No-Go posture. |
| M1C02-SCOPE-004 | The branch does not change backend product behavior, frontend product UI, Compose topology, providers, dependencies, or workflows. | Phase 1 branch allowlist tests and final diff review. |
| M1C02-QUALITY-005 | Plain local `make quality` on `main` dispatches Phase 1 Closure while StatusStateV1 records `phase1-closure`. | RED/GREEN dispatcher unit test. |
| M1C02-QUALITY-006 | Stage 8 dispatch and `NARRATWIN_POLICY_ONLY=1` behavior are not weakened when repo mode is not Phase 1 Closure. | Dispatcher unit tests for Stage 8 main and policy-only paths. |
| M1C02-DOCS-007 | Docs and status guidance match executable quality behavior. | Phase 1 docs unit test for exact guidance text. |
| HUMAN-APPROVAL-001 | Human PR approval and final squash/merge wording remain outside automation. | PR review gate and PR body human-only surface. |
| NONGOAL-RELEASE-001 | Production/public release remains No-Go. | Status/review docs and PR body; no production closeout rows changed. |

## Red Evidence Plan

- `tests/unit/test_quality_dispatcher.py::test_main_dispatches_phase1_closure_when_status_state_says_phase1`
  fails before the dispatcher fix because `main` with `.stage/current = 8`
  dispatches `make stage8-quality`.
- `tests/unit/test_phase1_closure_docs.py::test_issue208_209_branch_allows_only_real_stack_demo_and_quality_scope`
  fails before the Phase 1 branch allowlist is updated because no #208/#209
  branch scope exists.
- `tests/unit/test_phase1_closure_docs.py::test_phase1_quality_docs_make_main_dispatch_behavior_unambiguous`
  fails before docs/status updates because the expected `main` behavior is not
  documented.

## Validation Plan

- `uv run pytest tests/unit/test_quality_dispatcher.py`
- `uv run pytest tests/unit/test_phase1_closure_docs.py`
- `python3 scripts/guardrails_check.py`
- `make phase1-closure-quality`
- `make quality`
- `uv run ruff check scripts tests`
- `uv run mypy scripts tests`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend test`
- `npm --prefix frontend run build`
- `NARRATWIN_REAL_STACK=1 NARRATWIN_REAL_STACK_BASE_URL=http://127.0.0.1:3000 npx --prefix frontend playwright test --config frontend/playwright.real-stack.config.ts frontend/tests/real-stack.spec.ts --project=chromium`
- Compose smoke with `docker compose up --build -d`, `docker compose ps`, and
  `docker compose logs` evidence.
- Forced PR guardrail event after PR body exists.

## Human-Only Surfaces

| Surface | Why automation cannot complete it | Owner |
|---|---|---|
| GitHub PR approval | Repository policy requires human review before merge. | repo owner/reviewer |
| Final squash/merge wording | The final merge dialog is outside local test control. | repo owner/merger |
| Issue `#8` closeout judgment | Requires review of the full product-definition acceptance contract, not just this CH-M1-02 evidence. | repo owner/reviewer |
| Production/public release approval | Requires separate platform, security, provider, durability, monitoring, and release authorization. | repo owner/release authority |

## Skill Selection Evidence

| Skill or source | Decision | Evidence or reason |
|---|---|---|
| `git-workflow-and-versioning` | Used as workflow guidance | Needed branch/worktree classification, issue-linked branch, PR, and closeout discipline. |
| `incremental-implementation` | Used | Scope is split into preflight/RED tests, dispatcher/doc fix, real-stack test, evidence, and review. |
| `test-driven-development` | Used | #209 is behavior-changing quality dispatch; tests define the RED/GREEN boundary. |
| `frontend-ui-engineering` | Used as guidance | Browser evidence touches user-facing workflow, but no UI redesign is intended. |
| `security-and-hardening` | Used as guidance | The flow handles untrusted uploaded docs and synthetic media/provider boundaries. |
| `ci-cd-and-automation` | Used as guidance | The local quality ambiguity is a gate-dispatch problem. |
| `code-review-and-quality` | Used | Required final review checks overclaim, evidence integrity, and scope drift. |
| Browser DevTools skill | Considered but not invoked | Repeatable Playwright evidence is sufficient unless exploratory diagnosis is needed. |
| Shipping/launch skills | Rejected | This PR is not hosted/public launch or production release work. |
| Custom skills/plugins | Rejected | Preinstalled repo docs and skills cover the work; no custom capability gap exists. |

## Stop Rule

Stop and split before implementation if the #209 fix requires broad Stage 8
scanner policy changes, if CH-M1-02 requires backend/frontend product behavior
changes, if Compose cannot run due to a missing local dependency that cannot be
safely installed, if evidence requires real media/provider/hosted surfaces, or
if review finds a new material defect class after two correction loops.

## Runtime Evidence

The exact-head runtime validation command, commit SHA, duration, CI links, and
issue/PR URLs are recorded in the PR body and durable issue comments after the
final local run, because a committed file cannot name its own final commit SHA
without becoming stale.

Required local evidence packet for `CH-M1-02`:

- Commands: `reports/ch-m1-02/commands.txt`.
- Compose state: `reports/ch-m1-02/compose-ps.jsonl`.
- Backend/frontend logs: `reports/ch-m1-02/compose-backend-frontend.log`.
- Browser screenshot:
  `reports/ch-m1-02/playwright-output/real-stack-CH-M1-02-real-b-fef05-es-without-API-interception-chromium/ch-m1-02-avatar-export.png`.
- Browser run summary:
  `reports/ch-m1-02/playwright-output/.last-run.json`.
- Browser trace after final validation:
  `reports/ch-m1-02/playwright-output/real-stack-CH-M1-02-real-b-fef05-es-without-API-interception-chromium/trace.zip`.

Evidence acceptance facts:

- Case count: one Chromium Playwright case,
  `CH-M1-02 real browser path reaches frontend, backend, and Compose services
  without API interception`.
- Browser path: real page load and form submission through the frontend, with
  passive request observation only and no application API interception.
- Service path: browser -> Compose frontend -> internal Compose backend ->
  internal Compose Postgres/Redis dependencies.
- Provider posture: `docker-compose.yml` keeps LLM, embedding, evaluation,
  translation, avatar, TTS, STT, and subtitle providers set to `mock`; video
  renderer remains local placeholder-only.
- Local port assumptions: host frontend port may be remapped when local ports
  are occupied; the accepted evidence command must point
  `NARRATWIN_REAL_STACK_BASE_URL` at localhost.
- Limitations: no hosted/public launch, no production readiness, no Product Mode
  2, no real audio, no real video export, no external/paid provider enablement,
  and no public media distribution.
- Release posture: production/public release remains No-Go.
