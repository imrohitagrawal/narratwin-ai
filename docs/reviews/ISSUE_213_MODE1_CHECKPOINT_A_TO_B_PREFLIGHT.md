# Issue #213 Mode 1 Checkpoint A Through Checkpoint B Preflight

## Objective

Complete one controlled local/mock Product Mode 1 PR under parent issue `#155`
that proves the local demo path from Checkpoint A through Checkpoint B:
project creation, knowledge upload, approval, ingestion, grounded run,
multilingual run, durable consent, avatar render, and visible/downloadable
artifacts through a real local browser and backend.

## Acceptance Criteria

- Checkpoint A evidence is captured before implementation changes are claimed.
- `CH-M1-03` defines the Stage 6 multilingual media-bundle contract consumed by
  Stage 7.
- `CH-M1-04` makes Stage 7 render from a validated multilingual bundle for the
  Mode 1 checkpoint path and rejects missing, mismatched, stale, replayed,
  consent-invalid, and tampered bundle evidence.
- `CH-M1-05` exposes translated script, subtitles, voice manifest, avatar demo,
  render manifest, and video placeholder artifacts in the UI with language,
  provenance, MIME, filename, checksum, size, schema, and active-HTML checks.
- `CH-M1-06` updates demo checklist/script/screenshot guidance and deterministic
  seed posture without real media, providers, hosted launch, public
  distribution, or production-readiness claims.
- Checkpoint B evidence proves the full real-stack local path without
  Playwright supplying application API success through route interception.

## Non-Goals

- Product Mode 2.
- Real audio binaries, MP4/WebM, STT/imported video, cloned identity, external
  providers, hosted/public launch, public distribution, multi-worker claims, or
  production readiness.
- Provider SDKs, provider keys, dependency changes, workflow changes, Compose
  topology changes, or mutation of stopped evidence surfaces `#162`, `#163`,
  `#166`, `#167`, and `#168`.

## Source Facts

| Fact | Source | Engineering consequence |
|---|---|---|
| Issue `#155` is the serialized Mode 1 controller and the next action is a new issue-linked Checkpoint A step. | `docs/STATUS.md`; issue `#155` comment after PR `#212` | Issue `#213` and this branch are the only mutable lane. |
| Existing CH-M1-02 real-stack evidence proves browser -> frontend -> backend -> Compose but stops before Checkpoint A/B completion. | `docs/ADR/0029-ch-m1-02-real-stack-evidence.md`; `frontend/tests/real-stack.spec.ts` | Reuse the non-intercepted Playwright pattern and extend evidence, not the normal mocked smoke claim. |
| Stage 6 already exposes translated script, subtitles, voice manifest, metadata, trace context refs, citation indexes, and evaluation checksum. | `docs/API_CONTRACT.md`; `backend/app/stage6.py` | Stage 7 can require a validated Stage 6 bundle without inventing new provider surfaces. |
| Stage 7 currently renders from a completed grounded source run and returns HTML/JSON placeholder artifacts with consent and source evidence. | `docs/API_CONTRACT.md`; `backend/app/stage7.py`; ADR `0021` | Binding must preserve existing local/mock consent and artifact checks while adding multilingual provenance. |
| Frontend artifact links are enabled only after local safety checks. | `frontend/src/app/page.tsx`; `docs/API_CONTRACT.md` | UI changes must extend artifact kinds and validation rather than bypassing download safety. |

## Failure Matrix

| ID | Area | Failure mode or invariant | Evidence |
|---|---|---|---|
| M1A-BASE-001 | Checkpoint A | Baseline commands, health, ready, Compose state, and real-stack flow run at exact base commit before implementation claims. | command logs, screenshot/trace, PR evidence |
| M103-CONTRACT-001 | Bundle contract | Stage 7 cannot claim multilingual avatar output without `sourceRunId`, `multilingualRunId`, `targetLanguage`, translated-script/subtitles/voice checksums, context refs, citation indexes, evaluation ID/checksum, provider posture, and consent/disclosure version. | API contract/ADR, unit/API tests |
| M104-BIND-001 | Backend | Missing multilingual bundle is rejected. | RED/GREEN API or unit test |
| M104-BIND-002 | Backend | Mismatched `sourceRunId` is rejected. | RED/GREEN API or unit test |
| M104-BIND-003 | Backend | Wrong `targetLanguage` is rejected. | RED/GREEN API or unit test |
| M104-BIND-004 | Backend | Translated script, subtitle, or voice-manifest checksum mismatch is rejected. | RED/GREEN unit test |
| M104-BIND-005 | Backend | Missing subtitles or voice manifest is rejected. | RED/GREEN unit/API test |
| M104-BIND-006 | Backend | Unsupported or missing evaluation evidence is rejected. | RED/GREEN unit/API test |
| M104-BIND-007 | Backend | Stale/replayed bundle evidence cannot render a new multilingual avatar output. | RED/GREEN unit/API test |
| M104-BIND-008 | Backend | Reused or invalid `consentRecordId` is rejected. | existing plus focused test |
| M104-BIND-009 | Backend | Tampered render manifest/video placeholder cannot overclaim multilingual provenance. | RED/GREEN unit test |
| M105-UI-001 | Frontend | Translated script, subtitles, voice manifest, avatar demo, render manifest, and video placeholder are visible/downloadable. | component and real-stack Playwright |
| M105-UI-002 | Frontend/security | MIME, filename, size, checksum, JSON schema marker, and active HTML/script rejection block unsafe artifacts. | component tests |
| M105-UI-003 | Frontend/provenance | Target language and provenance are consistent across displayed artifacts and render metadata. | component and real-stack Playwright |
| M106-DOCS-001 | Demo docs | Demo docs state mock/local only, no provider keys, no real audio/video, no external providers, no cloned identity, no public distribution, no production readiness. | phase1 docs gate/tests |
| M1B-E2E-001 | Checkpoint B | Clean-state real browser path completes project -> upload -> approval -> ingestion -> grounded -> multilingual -> consent -> avatar render -> all artifacts visible/downloadable. | non-intercepted Playwright evidence |
| M1B-E2E-002 | Checkpoint B | Evidence records commands, commit SHA, case count, duration, API sequence, Compose ps/logs, screenshot, trace, artifact metadata/checksums, provider posture, and limitations. | reports and PR evidence |
| SCOPE-001 | Scope | No Product Mode 2, real media, provider, hosted/public launch, production-readiness, dependency/workflow/Compose topology, or stopped-evidence mutation enters the PR. | branch allowlist, diff review |
| HUMAN-001 | Human-only | Latest-head PR approval and final merge text are human-only. | PR review and PR body |

## Phase Mini-Plans

### Phase 0: Baseline And Checkpoint A

Objective: prove current `origin/main` local quality and real-stack behavior
before implementation.

Acceptance criteria: guardrails, `make quality`, `make phase1-closure-quality`,
Compose health/ready, and existing non-intercepted real-stack Playwright
complete or record an exact blocker.

Non-goals: no code behavior change and no Checkpoint B claim.

Tests/evidence: command transcript, duration, API sequence, screenshot, trace,
logs, provider posture, and limitations.

Failure matrix: `M1A-BASE-001`, `SCOPE-001`.

### Phase 1: CH-M1-03 Multilingual Media-Bundle Contract

Objective: freeze the Stage 6 -> Stage 7 bundle contract.

Acceptance criteria: API/ADR/traceability define required bundle fields and
tests fail if Stage 7 can overclaim multilingual avatar output without the
validated bundle.

Non-goals: no provider enablement and no real media.

Tests/evidence: focused unit/API RED/GREEN tests and docs gate.

Failure matrix: `M103-CONTRACT-001`.

### Phase 2: CH-M1-04 Backend Binding

Objective: render Mode 1 avatar output from the validated multilingual bundle.

Acceptance criteria: positive multilingual render includes bundle provenance;
negative tests reject missing/mismatched/checksum/stale/consent/tamper cases.

Non-goals: no Product Mode 2, production durability, or external provider path.

Tests/evidence: focused Stage 7 unit/API tests.

Failure matrix: `M104-BIND-001` through `M104-BIND-009`.

### Phase 3: CH-M1-05 Frontend/UI Artifact Proof

Objective: expose all required artifacts and block unsafe downloads.

Acceptance criteria: component tests and real-stack browser evidence show the
translated script, subtitles, voice manifest, avatar demo, render manifest, and
video placeholder are visible/downloadable and language/provenance consistent.

Non-goals: no visual redesign beyond existing local demo UI patterns.

Tests/evidence: frontend unit tests and non-intercepted Playwright.

Failure matrix: `M105-UI-001` through `M105-UI-003`.

### Phase 4: CH-M1-06 Demo Docs And Seed

Objective: update demo docs and seed posture for the complete local/mock flow.

Acceptance criteria: docs include all required non-goal talking points and
quality checks catch stale local-demo claims.

Non-goals: no README/portfolio production upgrade.

Tests/evidence: phase1 docs tests/gate.

Failure matrix: `M106-DOCS-001`.

### Phase 5: Checkpoint B Final Evidence

Objective: run the full clean-state local demo through a real browser and
record exact evidence.

Acceptance criteria: all requested local gates run, or exact tooling blockers
are recorded without success claims; full real-stack Playwright uses no
application API success interception.

Non-goals: no merge/close of `#155` without latest-head human approval and
Checkpoint B evidence.

Tests/evidence: full validation command set, reports, screenshots, trace,
artifact metadata/checksums, provider posture, limitations, and review findings.

Failure matrix: `M1B-E2E-001`, `M1B-E2E-002`, `HUMAN-001`.

## Skill And Tool Selection

| Skill/source | Decision | Evidence or prevented action |
|---|---|---|
| `git-workflow-and-versioning` | Used as workflow guidance | Issue `#213`, dedicated branch, one PR, reference-only parent issue wording. |
| `planning-and-task-breakdown` | Used | This preflight records phase mini-plans before implementation. |
| `incremental-implementation` | Used | Work is split into baseline, contract, backend, frontend, docs, evidence, and review increments. |
| `test-driven-development` | Used | Behavior changes require RED/GREEN tests for bundle and artifact boundaries. |
| `frontend-ui-engineering` | Used | Frontend artifact exposure and validation are user-facing. |
| `security-and-hardening` | Used | Uploads, provider outputs, generated artifacts, HTML/JSON downloads, and consent are untrusted. |
| `performance-optimization` | Used for smoke evidence only | Performance command results prove local demo budget posture; no premature optimization planned. |
| `code-review-and-quality` | Used | Independent review must find no Critical/High/Required findings before final PR readiness. |
| Custom skills/plugins | Rejected | Existing repo docs and available skills cover the work; no approved gap exists. |

## Stop Rule

Stop and update this matrix before coding again if review finds a new defect
class, if backend binding requires Product Mode 2 or real media, if tests need
provider keys or external services, if Compose cannot run after safe local
environment repair, if the branch needs dependency/workflow/Compose topology
changes, or if the same blocker repeats three times.

## Human-Only Surfaces

| Surface | Automation gap | Owner | Residual risk decision |
|---|---|---|---|
| Latest-head PR approval | Repository review approval is outside local execution. | repo owner/reviewer | Required before merge or `#155` closure preparation. |
| Final squash/merge wording | CI cannot inspect the final merge dialog. | repo owner/merger | Use reference-only wording unless explicit closure is approved. |
| `#155` closure decision | Requires Checkpoint B evidence plus human approval. | repo owner/reviewer | Do not close before those conditions are visible. |
| Production/public release | Requires separate platform/security/provider/durability/release approval. | repo owner/release authority | Remains No-Go. |
