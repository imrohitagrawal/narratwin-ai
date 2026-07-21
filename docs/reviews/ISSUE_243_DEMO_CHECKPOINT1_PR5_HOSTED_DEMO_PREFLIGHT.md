# Issue 243 Demo Checkpoint 1 PR5 Hosted-Demo Preflight

Accessed date for source facts: 2026-07-22.

## Objective

Demo Checkpoint 1 PR5 adds the narrow hosted-demo access, quota, retention, and
reviewer-facing polish layer needed to complete Checkpoint 1. The implementation
must stay local/fake by default: no hosted deployment, public URL, real provider
call, paid spend, provider account setup, provider dashboard configuration,
wallet funding, provider key, invite secret, access token, signing key, cloned
identity, Product Mode 2, or production-readiness claim is authorized.

The PR5 demo layer may consume PR3 TTS metadata and PR4 avatar/video provider
metadata, but it must preserve their disabled-provider boundaries. Hosted-demo
behavior is represented as a disabled/default-safe local API contract and tested
with fake access, quota, retention, artifact, and provider-deletion evidence.

## Non-Goals

- No hosted deployment, public URL exposure, production rollout, or production
  readiness.
- No provider account setup, dashboard configuration, paid plan activation,
  wallet funding, paid spend, provider SDK installation, real provider calls, or
  real provider test calls.
- No cloned voice, cloned face, Digital Twin, replica-profile creation,
  real-person likeness, Product Mode 2, or Checkpoint 2 cloned identity work.
- No broad refactor outside the PR5 hosted-demo access/quota/retention/demo
  polish boundary.
- No weakening PR1, PR2, PR3, or PR4 source facts, disabled-provider posture,
  disclosure, evidence, or stopped predecessor surfaces #162/#163/#166/#167/#168.

## Changed-File Allowlist

The issue #243 branch may change only these paths:

- `docs/governance/preflights/issue-243.json`
- `docs/reviews/ISSUE_243_DEMO_CHECKPOINT1_PR5_HOSTED_DEMO_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/LAUNCH_LEVELS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/API_CONTRACT.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `backend/app/hosted_demo.py`
- `backend/app/main.py`
- `tests/unit/test_hosted_demo.py`
- `tests/api/test_hosted_demo_api.py`
- `frontend/src/app/page.tsx`
- `frontend/src/app/page.test.tsx`
- `frontend/tests/smoke.spec.ts`

Checker support must reject near-match issue #243 branches and unrelated files
including GitHub workflows, Dockerfiles, dependency manifests, database
migrations, provider SDK manifests, provider secrets, hosted deployment files,
Checkpoint 2 clone paths, and Stage 6/Stage 7 provider internals. PR5 may
consume Stage 6/Stage 7 metadata but must not mutate `backend/app/stage6.py`,
`backend/app/stage7.py`, or provider ledgers in this issue branch.

## Official Source Facts

| Area | Official source | Fact used for PR5 | Design implication |
|---|---|---|---|
| FastAPI errors | `https://fastapi.tiangolo.com/tutorial/handling-errors/` and `https://fastapi.tiangolo.com/reference/exceptions/` | `HTTPException` is raised for client-visible API errors; custom handlers can keep one structured error shape. | PR5 should reuse the existing `Stage*Error` to API-error handler pattern and return stable demo denial/quota/retention error codes without stack traces. |
| FastAPI middleware | `https://fastapi.tiangolo.com/tutorial/middleware/` | Middleware runs before path operation processing and after response creation. | PR5 should not add broad middleware unless the same behavior cannot stay endpoint-scoped; demo abuse limits can be local endpoint/service logic. |
| Pydantic extra fields | `https://pydantic.dev/docs/validation/2.0/usage/model_config/` and `https://pydantic.dev/docs/validation/dev/api/pydantic/config/` | Pydantic can forbid unexpected input fields with `ConfigDict(extra=\"forbid\")`; default extra behavior is ignore. | PR5 boundary models must explicitly reject unexpected fields where demo access, artifact, retention, and deletion evidence are accepted from local/fake inputs. |
| OWASP LLM prompt injection | `https://owasp.org/www-project-top-10-for-large-language-model-applications/` and `https://genai.owasp.org/llmrisk/llm01-prompt-injection/` | Prompt injection can manipulate model/application behavior; LLM output handling remains a security boundary. | PR5 must treat scripts, transcripts, provider outputs, access display text, and reviewer-visible metadata as untrusted and reject prompt-injection markers before storage/display/download. |
| Next.js environment variables | `https://nextjs.org/docs/pages/guides/environment-variables` and `https://nextjs.org/docs/app/api-reference/config/next-config-js/env` | Browser-exposed variables require `NEXT_PUBLIC_`; values placed in `next.config.js env` are bundled into client JavaScript. | PR5 must not add secrets, invite codes, provider keys, access tokens, signing keys, or hosted credentials to frontend code or build-time public config. |
| Vercel plan limits | `https://vercel.com/docs/plans/hobby`, `https://vercel.com/pricing`, `https://vercel.com/docs/pricing`, and `https://vercel.com/docs/limits/fair-use-guidelines` | Hobby is restricted to personal/non-commercial use; commercial usage requires Pro or Enterprise. | PR5 may document hosted-demo posture but must not select Vercel Hobby for recruiter-facing use or create deployment/account actions. |
| Railway pricing/cost control | `https://docs.railway.com/pricing/plans`, `https://docs.railway.com/pricing/faqs`, and `https://docs.railway.com/pricing/cost-control` | Railway has subscription plus resource usage costs; usage beyond included credits can be charged. | PR5 must keep hosting as no-deploy/no-spend; any later Railway use needs owner approval, budget, alerts, and teardown. |
| Render free behavior | `https://render.com/docs/free` | Free web services spin down after 15 minutes idle and take about one minute to spin back up. | PR5 must not claim hosted first-view reliability from a free Render-like service; local fake demo must show provider/hosting disabled posture instead. |

## Hosted-Demo Interface Contract

PR5 introduces a local/fake hosted-demo boundary with typed schemas:

- `HostedDemoAccessConfig`: `enabled`, `require_invite`, session TTL, allowed
  reviewer count, per-session quota, global quota, retention days, disclosure
  version, and disabled-provider posture.
- `HostedDemoAccessRequest`: invite identifier, session ID, source run ID, trace
  ID, language, audience, script checksum, citation refs, evaluation
  ID/status/checksum, optional TTS/audio checksum, optional avatar/video
  provider metadata checksum, artifact checksum, disclosure text/version, and
  requested operation.
- `HostedDemoDecision`: access state, denial reason, bounded session state,
  quota reservation state, retention state, deletion state, tombstone ID,
  deletion evidence ID, artifact visibility, retry-after/backoff metadata, and
  redaction-safe observability fields.

Provider-native payloads, hosted URLs, raw scripts, raw prompts, uploads,
cookies, invite secrets, access tokens, session secrets, provider payloads, and
media bytes must never be logged, stored in frontend config, or returned as
reviewer-facing evidence.

## Invariant and Test Matrix

| ID | Area | Invariant | Old failure / false-pass risk | Required proof |
|---|---|---|---|---|
| PR5-SCOPE-001 | Branch scope | Exact issue #243 branch allowlist permits only PR5 files and near-match branches fail closed. | Generic process branch could allow process docs while product/demo files bypass exact PR5 review. | RED checker tests in `tests/unit/test_phase1_closure_docs.py`; gate in `scripts/quality/check_phase1_closure_docs.py`. |
| PR5-ACCESS-001 | Disabled default | Hosted-demo access is disabled/denied by default and no invite/session grants access without explicit local config. | Existing API has no hosted-demo layer, so reviewers could infer access exists without denial proof. | Unit/API tests for disabled default, missing config, invalid config, access denied, invalid invite/session, stale/forged/replayed state. |
| PR5-ACCESS-002 | Access binding | Any visible demo artifact is bound to source run ID, trace ID, language, audience, script checksum, citation refs, evaluation ID/status/checksum, TTS/audio checksum when present, avatar/video metadata when present, artifact checksum, disclosure, access/session state, quota state, retention/deletion state, and tombstone evidence. | Valid artifact IDs can survive while source/eval/media/access/quota/retention evidence belongs to another run. | Unit/API mutation tests for stale source run, failed/stale eval, citation mismatch, access mismatch, quota mismatch, retention mismatch, and artifact checksum mismatch. |
| PR5-QUOTA-001 | Reservation before side effect | Quota reservation happens before fake artifact visibility or fake deletion side effects; failed local/fake jobs refund; ambiguous accepted work holds quota unknown; duplicate use/spend is blocked. | Existing provider quota ledgers are PR3/PR4-specific and do not protect hosted-demo access or view/regeneration spend. | Unit tests for quota exhaustion, reservation before side effect, refund/rollback, unknown hold, duplicate-use/duplicate-spend prevention, idempotency conflict, retry cap, timeout, Retry-After/backoff. |
| PR5-RETENTION-001 | Retention/deletion evidence | Demo access records and artifacts move through active, pending deletion, deleted, and tombstone states; pending deletion is never recorded as deleted proof; fake provider-side deletion evidence is local-only. | PR4 disabled metadata records `NOT_CREATED`; PR5 could falsely claim provider-side deletion or hard-delete without terminal evidence. | Unit/API tests for retention expiry, delete request, tombstone evidence, fake terminal provider deletion proof, pending deletion rejection, replay/export blocked after deletion. |
| PR5-VALIDATE-001 | Untrusted input/output | Duplicate JSON keys, unexpected fields, unsafe URLs, redirects, MIME/extension mismatch, oversized artifacts, checksum mismatch, prompt/provider-output injection, unsafe display text, and stale eval/source/media are rejected before storage/display/download. | Existing frontend/backend artifact validation is Stage 6/7-specific and may not cover hosted-demo access-display surfaces. | Unit/API/frontend tests for malformed response, duplicate JSON keys, unexpected MIME/extension, oversized artifact, unsafe URL rejection, prompt injection across script/transcript/provider-output/access display. |
| PR5-DISCLOSURE-001 | Reviewer polish | Reviewer-visible surfaces show disabled-provider posture, synthetic-media disclosure text/version, artifact metadata, clear denial states, quota/retention status, and evidence links without marketing or launch claims. | Demo polish could become a landing page or imply public production readiness. | Frontend unit/smoke or API response tests for disclosure visibility, disabled-provider posture, denial/error states, and no public URL/production claim. |
| PR5-OBS-001 | Redacted observability | Logs/metadata include stable event names, trace ID, bounded status/code, access outcome, quota outcome, retention/deletion state, and artifact validation result, but no raw prompts, scripts, uploads, provider payloads, URLs, invite secrets, cookies, tokens, session secrets, provider keys, or media bytes. | Redaction-by-absence could leave reviewers without useful operational evidence or leak untrusted content in errors/logs. | Unit tests inspect emitted redacted events and negative leak strings. |
| SRC-PR5-001 | Hosted platform facts | Hosted platform facts are documentation-only in PR5 and do not authorize account setup, deployment, public URL, or paid spend. | Source facts could be mistaken for owner approval to deploy. | Official source facts table plus human-only checklist row; no runtime deploy files in allowlist. |
| NONGOAL-PR5-001 | Clone/production boundary | Cloned identity, real-person likeness, Product Mode 2, public distribution, and production readiness remain out of scope. | Checkpoint 1 completion could be mistaken for Checkpoint 2 or launch readiness. | Docs/checker/human-only rows; no clone/provider/deployment files or real calls. |

## Old-Behavior and Failure Proof

Before PR5 implementation, expected failing proofs are:

- No branch-specific allowlist exists for issue #243, and a near-match issue
  #243 branch is not explicitly failed closed.
- No `backend/app/hosted_demo.py` module or hosted-demo API contract exists.
- No tests prove hosted-demo disabled default, missing/invalid config,
  invite/session denial, stale/replayed access state, quota reservation before
  fake side effects, quota refund/unknown hold, duplicate-use/spend prevention,
  retention/deletion/tombstone evidence, pending deletion not counted as
  deleted, or redacted hosted-demo observability.
- No reviewer-facing PR5 response surface binds access/quota/retention state to
  source run, trace, citations, evaluation, TTS/audio metadata, avatar/video
  metadata, artifact checksum, disclosure, and tombstone evidence.
- Existing Stage 6/Stage 7 API responses include raw artifact bytes and text
  fields that are valid for local product APIs but are not acceptable as hosted
  reviewer evidence. PR5 must add a separate redacted metadata-only boundary.
- Existing local principal simulation defaults are not hosted authorization.
  PR5 must reject absent, forged, expired, wrong, or replayed invite/session
  state before any product data or artifact metadata becomes visible.

## Claim Mapping

| Claim | Proof type |
|---|---|
| Local/dev/test/CI require no hosted credentials, provider keys, paid services, public URLs, or real provider calls. | Executable unit/API tests, branch allowlist, docs, and human-only checklist. |
| Hosted-demo access is disabled/denied by default. | Executable unit/API tests. |
| Access, quota, retention, deletion, and artifacts are source/eval/media-bound. | Executable unit/API mutation tests. |
| Quota reservation/refund/unknown-hold/idempotency prevents duplicate use/spend. | Executable unit tests. |
| Retention/deletion/tombstone evidence is local/fake and terminal before `DELETED`. | Executable unit/API tests plus docs. |
| Prompt/provider-output/access display surfaces are untrusted. | Executable validation tests and OWASP source facts. |
| Redacted observability is useful without sensitive data. | Executable unit tests. |
| Hosted deployment, public URL, paid spend, clone, Product Mode 2, and production readiness remain false. | Branch allowlist, docs, PR human-only checklist, and non-goal rows. |

## Fan-Out Review Findings and Dispositions

| Area | Finding | Disposition |
|---|---|---|
| Output-correctness that executes rather than reads | Required before implementation: run old-behavior probes that prove #243 checker support and hosted-demo behavior are absent. | Add RED tests and record commands before product implementation. |
| Security/privacy/consent/access control | Access state, invite identifiers, sessions, headers, cookies, and display text are untrusted even in a fake hosted-demo surface. Existing `X-Local-User-Id` local principal simulation is not hosted auth and must not grant hosted-demo access. | Validate boundary models, reject unsafe identifiers and prompt-injection markers, require hosted invite/session binding for hosted-demo decisions, and log only allowlisted metadata. |
| Raw data leak prevention | Existing Stage 6/Stage 7 local response shapes can include `contentBase64`, source script text, translated text, and full artifacts. | PR5 hosted-demo responses must use a separate redacted metadata-only shape; tests must assert absence of raw scripts, prompts, uploads, provider payloads, raw URLs, invite/session secrets, cookies, tokens, provider keys, and media bytes. |
| Cost/provider/hosted-service terms | Hosting and provider source facts must not become deployment/spend authorization. TTS timeout refund behavior from PR3 is not valid hosted spend proof because timeout-after-egress is billable-unknown unless provider idempotency or job lookup proves non-acceptance. | Keep deploy files, provider setup, keys, and paid calls outside the allowlist; document source facts as constraints only. PR5 quota tests must model timeout-after-egress as unknown hold, not refund, unless fake/local non-acceptance is explicit. |
| Quota/reliability/performance | Current TTS and avatar/video ledgers are in-memory provider-specific controls, not durable hosted-demo quota proof; any externally reachable URL changes launch level to external/invite-only soft launch. | PR5 quota is explicitly fake/local unless a later hosted environment issue exists; add tests for concurrent reservation, restart/replay or documented local-only reset, refund before egress, unknown billable holds, duplicate idempotency key, and changed-checksum conflict. |
| Retention/deletion evidence | Fake/local provider deletion evidence and pending provider deletion must not be described as real hosted/provider deletion proof. | Distinguish local tombstone, fake terminal deletion evidence, pending provider deletion, and source-backed real provider deletion; pending deletion must never satisfy `DELETED`. |
| Eval/grounding/citations/source-run binding | Demo artifact visibility must fail closed when source run, citation refs, or evaluation evidence is stale or mismatched. | Add source/eval/citation binding tests before accepting artifacts. |
| UX/demo/recruiter flow | Demo polish must show denial, disabled-provider posture, disclosure, metadata, quota, and retention state without a marketing page or launch claim. The current pre-generation unsupported-claims badge can read as completed evaluation evidence before any run. | Keep UI changes narrow and evidence-oriented; make pre-run evaluation state neutral/pending and reserve `0 unsupported claims` for completed evidence. |
| Performance/reliability/quota/rate-limit/idempotency | Quota and abuse limits must precede fake side effects and handle retries/timeouts deterministically. | Use in-memory fake ledgers with no sleeps and bounded retry metadata. |
| API/interface design | API fields must be additive, camelCase at boundary, and use structured error codes. The hosted-demo API boundary is currently absent and must not infer artifact/access records from downloadable inline bytes. | Add `backend/app/hosted_demo.py`, API contract docs, and Pydantic response/request models with `extra="forbid"`, explicit error codes, and first-class artifact/access/quota/retention records. |
| Observability/logging/redaction | Redaction must be tested with raw script/prompt/provider/invite/session leak canaries. | Unit tests inspect event payloads. |
| Retention/deletion/tombstone evidence | Pending deletion is not proof; terminal local/fake evidence must carry tombstone checksum. | Add deletion evidence state machine tests. |
| Governance/taste/scope | PR5 must not absorb Checkpoint 2, deployment, provider enablement, Stage 6/Stage 7 provider-internal edits, or broad refactors. | Exact branch allowlist, near-match rejection, Stage 6/Stage 7 negative allowlist tests, and PR body human-only rows. |

## Skill and Evidence Ledger

Invoked skills: `planning-and-task-breakdown`, `spec-driven-development`,
`test-driven-development`, `source-driven-development`,
`security-and-hardening`, `code-review-and-quality`,
`git-workflow-and-versioning`, `taste-check`,
`doubt-driven-development`, `api-and-interface-design`, and
`observability-and-instrumentation`.

Rejected options:

- Hosted deployment or public URL: rejected because PR5 has no owner-written
  approval for hosted environment controls, spend, secrets, monitoring,
  rollback, retention, incident response, or teardown.
- Provider SDK installation or real provider calls: rejected because PR5 can
  prove access/quota/retention with fake/local surfaces and PR3/PR4 keep real
  providers disabled by default.
- Real invite codes, auth secrets, access tokens, cookies, or signing keys:
  rejected because tests must use fake identifiers and no secrets may be
  committed.
- Checkpoint 2 clone work: rejected because consent/provenance and cloned
  identity require a separate issue.

## Stop Rule

Implementation may start only after this document, issue #243 preflight, branch
allowlist checker support, regression tests, source facts, and pre-implementation
fan-out review findings/dispositions are complete. If any fan-out reviewer finds
a blocker, keep the PR draft, update this contract first, add failing tests, and
only then implement the fix.
