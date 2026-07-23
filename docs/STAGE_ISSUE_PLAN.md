# Stage Issue Plan

Every NarraTwin AI stage must move through issue, branch, pull request, review, quality gate, and merge. This file defines the required issue plan and branch pattern for Stage 0 through Stage 8 plus Final Review.

## Workflow

```text
Create or identify stage issue
-> create dedicated branch from main
-> make stage-scoped changes only
-> run the local stage quality target
-> open PR linked to the issue
-> pass CI
-> complete review
-> merge
```

## Stage Plan

| Stage | Issue | Issue title | Branch pattern | Local quality target | PR requirement | Exit artifact |
|---|---|---|---|---|---|---|
| Stage 0 | `#14` | Stage 0 - Codex operating model and skill lock | `stage0-*` | `make stage0-quality` | Linked PR to `main` | Operating model, skill lock, stage issue plan, Stage 0 quality gate |
| Stage 1 | `#1`, `#16` | Stage 1 - Product strategy and PRD v1.0 | `stage1-*` | `make stage1-quality` | Linked PR to `main` | Product strategy, PRD v1.0, red-team review, metrics, roadmap |
| Stage 2 | `#2` | Stage 2 - Architecture, security, AI safety | `stage2-*` | `make stage2-quality` | Linked PR to `main` | Architecture, ADRs, security/privacy, AI safety/evaluation |
| Stage 3 | `#5` | Stage 3 - Repo foundation and CI/CD quality gates | `stage3-*` | `make stage3-quality` | Linked PR to `main` | Local development docs, CI wrappers, executable quality gates |
| Stage 4 | `#4` | Stage 4 - Project upload to grounded script generation | `stage4-*` | `make stage4-quality` | Linked PR to `main` | First vertical slice with tests, docs, security notes, observability metadata |
| Stage 5 | `#10` | Stage 5 - Evaluations, guardrails, observability | `stage5-*` | `make stage5-quality` | Linked PR to `main` | Blocking evals, guardrails, trace/run metadata, observability |
| Stage 6 | `#11` | Stage 6 - Multilingual scripts, subtitles, voice adapter | `stage6-*` | `make stage6-quality` | Linked PR to `main` | Multilingual script path, subtitles, mock/local voice adapter |
| Stage 7 | `#12` | Stage 7 - Avatar rendering adapter and export | `stage7-*` | `make stage7-quality` | Linked PR to `main` | Mock/local avatar renderer, export artifacts, provider contract tests |
| Stage 8 | `#13` | Stage 8 - Performance, security hardening, release readiness | `stage8-*` | `make stage8-quality` | Linked PR to `main` | Performance evidence, security hardening, release-readiness report |
| Final Review | `#6` | Final Review - Independent review | `final-review-*` | `make final-review-quality` | Linked PR to `main` | Independent review report and release decision |
| Phase 1 Closure | `#35`-`#44`, follow-ups including `#139`-`#149` | Phase 1 Closure - Final Review blockers | `phase-1-closure-*` | `make phase1-closure-quality`; stacked chunk PRs use `GITHUB_BASE_SHA=<reviewed-prereq-head> make phase1-closure-quality` | Linked PR to `main` or reviewed `phase-1-closure-*` stacked base | Closed or downgraded P0/P1 blockers, closure report, release readiness update |

## Stage 0 Governance Branch Scope

Allowed changes:

- `AGENTS.md`
- `.gitignore`
- `README.md`
- `.github/pull_request_template.md`
- `.github/workflows/quality.yml`
- `.github/workflows/quality-gates.yml`
- `docs/AI_BUILD_BRIEF.md`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`
- `docs/REPOSITORY_GUARDRAILS.md`
- `docs/STATUS.md`
- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/SKILL_LOCK.md`
- `docs/SKILL_TRUST_REVIEW.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `.stage/current`
- `.github/workflows/eval-smoke.yml`
- `Makefile`
- `scripts/guardrails_check.py`
- `scripts/quality/check_stage0_docs.py`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/stage_not_implemented.py`

Blocked changes:

- backend product code
- frontend product code
- RAG, vector store, or embedding code
- avatar, TTS, STT, subtitle, or provider adapter code
- Docker, database, or runtime deployment code
- Stage 1 product strategy or PRD expansion

## Stage 1 Product And PRD Branch Scope

Allowed changes:

- `.stage/current`
- `.github/workflows/eval-smoke.yml`
- `Makefile`
- `docs/NORTH_STAR_METRICS.md`
- `docs/PHASE_PLAN.md`
- `docs/PRD.md`
- `docs/PRD_RED_TEAM_REVIEW.md`
- `docs/PRODUCT_STRATEGY.md`
- `docs/QUALITY_GATES.md`
- `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `docs/ROADMAP.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `scripts/ci/backend-lint.sh`
- `scripts/ci/backend-test.sh`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_stage0_docs.py`
- `scripts/quality/check_stage1_docs.py`

Blocked changes:

- backend product code
- frontend product code
- RAG, vector store, or embedding code
- avatar, TTS, STT, subtitle, or provider adapter code
- Docker, database, or runtime deployment code
- dependency manifests or lockfiles for product/runtime code

## Stage 2 Architecture And Safety Branch Scope

Allowed changes:

- `.env.example`
- `.github/workflows/quality-gates.yml`
- `.gitignore`
- `.stage/current`
- `.github/workflows/security.yml`
- `Makefile`
- `docs/ADR/0001-architecture-approach.md`
- `docs/ADR/0001-system-architecture.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/ADR/0002-rag-storage.md`
- `docs/ADR/0003-free-mode-vs-premium-mode.md`
- `docs/ADR/0003-llm-provider-routing.md`
- `docs/ADR/0004-avatar-provider-adapter.md`
- `docs/ADR/0005-observability-and-evals.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/API_CONTRACT.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/STAGE2_ARCHITECTURE_CONTRACT.json`
- `docs/STAGE2_HUMAN_REVIEW_CHECKLIST.md`
- `docs/STAGE2_REVIEW_PROMPT_PACK.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/THREAT_MODEL.md`
- `docs/TRACEABILITY.md`
- `scripts/guardrails_check.py`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_recommended_review_items.py`
- `scripts/quality/check_stage2_docs.py`

Blocked changes:

- backend product code
- frontend product code
- RAG, vector store, or embedding implementation code
- avatar, TTS, STT, subtitle, or provider adapter implementation code
- Docker, database, infrastructure, or runtime deployment code
- dependency manifests or lockfiles for product/runtime code
- unapproved workflow automation, agent runtime configs, or external-provider
  automation not recorded in `docs/THIRD_PARTY_NOTICES.md` and `docs/SKILL_LOCK.md`

## Stage 3 Repo Foundation And CI/CD Branch Scope

Allowed changes:

- `.dockerignore`
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
- `.github/workflows/eval-smoke.yml`
- `.github/workflows/quality.yml`
- `.github/workflows/quality-gates.yml`
- `.pre-commit-config.yaml`
- `.gitignore`
- `.stage/current`
- `.env.example`
- `Makefile`
- `backend/Dockerfile`
- `backend/__init__.py`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `docker-compose.yml`
- `evals/smoke/stage3_health_fixture.json`
- `pyproject.toml`
- `semgrep.yml`
- `tests/api/test_health_api.py`
- `tests/unit/test_health_contract.py`
- `uv.lock`
- `frontend/Dockerfile`
- `frontend/.gitignore`
- `frontend/README.md`
- `frontend/eslint.config.mjs`
- `frontend/playwright.config.ts`
- `frontend/next.config.ts`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/app/favicon.ico`
- `frontend/src/app/globals.css`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/page.module.css`
- `frontend/src/app/page.test.tsx`
- `frontend/src/app/page.tsx`
- `frontend/tests/smoke.spec.ts`
- `frontend/tsconfig.json`
- `frontend/vitest.config.ts`
- `docs/ADR/0001-system-architecture.md`
- `docs/API_CONTRACT.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/REPOSITORY_GUARDRAILS.md`
- `docs/SKILL_LOCK.md`
- `docs/STAGE2_ARCHITECTURE_CONTRACT.json`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `scripts/guardrails_check.py`
- `scripts/ci/backend-lint.sh`
- `scripts/ci/backend-test.sh`
- `scripts/ci/docker-build.sh`
- `scripts/ci/eval-smoke.sh`
- `scripts/ci/frontend-build.sh`
- `scripts/ci/frontend-smoke.sh`
- `scripts/ci/dependency-security.sh`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_recommended_review_items.py`
- `scripts/quality/check_stage2_docs.py`
- `scripts/quality/check_stage3_docs.py`

Blocked changes:

- backend product implementation beyond health checks
- frontend product feature implementation beyond the minimal framework scaffold
- RAG, vector store, or embedding implementation code
- avatar, TTS, STT, subtitle, or provider adapter implementation code
- database migrations, infrastructure deployment, or non-local runtime deployment code
- broad backend, frontend, or test paths outside the exact Stage 3 scaffold
  allowlist
- premium-provider automation or real provider keys
- Vite frontend scaffolding unless a future ADR supersedes the documented
  Next.js frontend decision

## Stage 4 Grounded Script Branch Scope

Allowed changes:

- `.github/workflows/eval-smoke.yml`
- `.stage/current`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `Makefile`
- `backend/app/main.py`
- `backend/app/stage4.py`
- `backend/app/rag/`
- `evals/smoke/stage4_grounded_script_dataset.json`
- `frontend/src/app/page.tsx`
- `frontend/src/app/page.module.css`
- `frontend/src/app/page.test.tsx`
- `frontend/tests/smoke.spec.ts`
- `frontend/next.config.ts`
- `frontend/playwright.config.ts`
- `pyproject.toml`
- `uv.lock`
- `tests/fixtures/stage4_project.md`
- `tests/unit/test_chunking.py`
- `tests/unit/test_retrieval_and_grounding.py`
- `tests/api/test_health_api.py`
- `tests/api/test_stage4_slice_api.py`
- `tests/unit/test_health_contract.py`
- `docker-compose.yml`
- `frontend/Dockerfile`
- `scripts/ci/eval-smoke.sh`
- `scripts/ci/frontend-smoke.sh`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_stage4_docs.py`
- `docs/API_CONTRACT.md`
- `docs/ADR/0002-rag-storage.md`
- `docs/DATA_MODEL.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`

Blocked changes:

- avatar rendering, TTS, STT, subtitle, or video-rendering implementation
- premium-provider calls or required real provider keys
- cross-tenant or shared vector-store retrieval without tenant/project filters
- database migrations or asynchronous job infrastructure before the persistence
  decision and job uniqueness constraints are locked

## Stage 5 Evaluations, Guardrails, Observability Branch Scope

Allowed changes:

- `.github/workflows/eval-smoke.yml`
- `.stage/current`
- `Makefile`
- `backend/app/main.py`
- `backend/app/stage4.py`
- `backend/app/rag/grounding.py`
- `backend/app/rag/models.py`
- `backend/app/eval/`
- `backend/app/observability/`
- `evals/smoke/stage5_grounded_script_dataset.json`
- `evals/smoke/stage5_prompt_injection_set.json`
- `evals/smoke/stage5_file_upload_abuse_set.json`
- `tests/unit/test_retrieval_and_grounding.py`
- `tests/unit/test_health_contract.py`
- `tests/api/test_health_api.py`
- `tests/api/test_stage4_slice_api.py`
- `scripts/ci/eval-smoke.sh`
- `scripts/quality/check_stage5_docs.py`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_recommended_review_items.py`
- `docs/EVAL_REPORT.md`
- `docs/ADR/0005-observability-and-evals.md`
- `docs/API_CONTRACT.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `pyproject.toml`
- `uv.lock`

Blocked changes:

- avatar rendering, TTS, STT, subtitle, or video-rendering implementation
- premium-provider calls or required real provider keys
- database migrations, asynchronous job infrastructure, or production deployment
  infrastructure
- broad frontend feature changes outside the approved Stage 4 first-slice UI
- new provider integrations beyond local/mock evaluation and observability
  adapters

## Stage 6 Multilingual Scripts, Subtitles, Voice Adapter Branch Scope

Allowed changes:

- `.stage/current`
- `.github/workflows/security.yml`
- `Makefile`
- `README.md`
- `backend/app/main.py`
- `backend/app/stage6.py`
- `frontend/src/app/page.tsx`
- `frontend/src/app/page.module.css`
- `frontend/src/app/page.test.tsx`
- `frontend/tests/smoke.spec.ts`
- `tests/unit/test_stage6_multilingual.py`
- `tests/api/test_stage6_multilingual_api.py`
- `tests/unit/test_health_contract.py`
- `tests/api/test_health_api.py`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_stage6_docs.py`
- `docs/API_CONTRACT.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `pyproject.toml`
- `uv.lock`

Blocked changes:

- real paid provider calls or required real provider keys
- hardcoded premium-provider SDK usage
- avatar rendering, face cloning, voice cloning, or video rendering
- STT/video import workflows outside the approved Stage 6 source-script path
- database migrations, asynchronous job infrastructure, or production deployment
  infrastructure
- non-local TTS, translation, subtitle, or media-provider dependencies without
  provider-adapter review and third-party notice updates

Required Stage 6 hardening within this scope:

- write idempotency must reserve a pending record before provider work and reject
  duplicate in-flight requests
- provider output must be validated for non-empty translated text, size limits,
  glossary preservation, and citation-marker preservation before display or
  downloadable artifact creation
- API request fields must enforce target-language, glossary, and provider-ID
  boundary limits
- frontend artifact links must only be enabled for expected script/subtitle MIME
  types and file extensions
- mock/local voice behavior must remain a JSON manifest only, with no real audio,
  playback, voice cloning, or non-local provider egress

## Stage 7 Avatar Rendering Adapter And Export Branch Scope

Allowed changes:

- `.stage/current`
- `Makefile`
- `backend/app/main.py`
- `backend/app/stage7.py`
- `frontend/src/app/page.tsx`
- `frontend/src/app/page.module.css`
- `frontend/src/app/page.test.tsx`
- `frontend/tests/smoke.spec.ts`
- `tests/unit/test_stage7_avatar.py`
- `tests/api/test_stage7_avatar_api.py`
- `tests/unit/test_health_contract.py`
- `tests/api/test_health_api.py`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_stage7_docs.py`
- `docs/API_CONTRACT.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/SKILL_LOCK.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`

Blocked changes:

- real paid avatar-provider calls or required real provider keys
- hardcoded premium-provider SDK usage
- face cloning, voice cloning, or identity replication without explicit consent
- non-local video or avatar-provider dependencies without provider-adapter
  review and third-party notice updates
- database migrations, asynchronous job infrastructure, or production deployment
  infrastructure
- STT/video import workflows outside the approved generated-script-to-demo-export
  path

Required Stage 7 hardening within this scope:

- avatar rendering must use a mock/local provider by default and must not call
  premium providers in local/dev/test
- provider config, render job status history, failed provider fallback, and video
  export placeholder metadata must be explicit and tested
- export artifacts must be validated for expected MIME type, extension, size,
  checksum, and safe filename before API response or frontend download
- provider-produced config, render manifests, and video placeholders must be
  validated from the start before storage, response, or display
- generated demo exports must carry AI-generated avatar/video disclosure metadata
- any cloned identity feature must remain disabled unless consent controls,
  provenance metadata, and review evidence are implemented
- provider contracts must preserve trace/run metadata, source citations, and
  evaluation status from the grounded script path
- UI work must follow the activated UI/UX Pro Max guidance without committing
  `.codex` generated skill files
- any optional Stage 8 hardening recommendation discovered during Stage 7 must
  be recorded in `docs/RECOMMENDED_REVIEW_ITEMS.md` with a required stage/phase

## Stage 8 Performance, Security Hardening, Release Readiness Branch Scope

Issue `#151` is the bounded security-remediation branch for patched Python
runtime evidence and scanner-consensus hardening; it does not authorize product
runtime behavior changes.

Allowed changes:

- `.stage/current`
- `Makefile`
- `backend/app/main.py`
- `backend/app/stage4.py`
- `backend/app/stage6.py`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/app/page.test.tsx`
- `frontend/scripts/run-lighthouse.mjs`
- `perf/stage8_locustfile.py`
- `pyproject.toml`
- `uv.lock`
- `scripts/ci/dependency-security.sh`
- `scripts/ci/docker-image-scan.sh`
- `scripts/ci/frontend-lighthouse.sh`
- `scripts/ci/performance-smoke.sh`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_stage8_docs.py`
- `tests/api/test_stage4_slice_api.py`
- `tests/api/test_health_api.py`
- `tests/api/test_stage6_multilingual_api.py`
- `tests/api/test_stage8_hardening_api.py`
- `tests/unit/test_health_contract.py`
- `tests/unit/test_stage6_multilingual.py`
- `demo/stage8_seed_project.md`
- `docs/ADR/0006-stage8-release-hardening.md`
- `docs/API_CONTRACT.md`
- `docs/ARCHITECTURE.md`
- `docs/QUALITY_GATES.md`
- `docs/PROJECT_LEARNINGS_TRACKER.md`
- `docs/PROJECT_GOVERNANCE_LEARNINGS.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/REVIEW_RIGOR_RETROSPECTIVE.md`
- `docs/RUNBOOK.md`
- `docs/SKILL_LOCK.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `portfolio/README.md`

Blocked changes:

- real paid provider calls or required real provider keys
- new production credential dependency
- broad product feature implementation beyond release hardening
- multi-worker production enablement while Stage 6 and Stage 7 process-local
  idempotency/job/artifact state remains non-durable
- real video export implementation before renderer/provider license posture,
  performance limits, and artifact validation are approved
- external avatar provider or public synthetic-media export before persistent
  consent/provenance is implemented

Required Stage 8 hardening within this scope:

- performance smoke tests and API latency budget checks
- frontend Lighthouse checks
- rate limiting
- request size limits
- upload MIME validation
- dependency audit
- Docker image scan
- release checklist and rollback notes
- runbook
- demo seed data
- portfolio README
- `docs/RELEASE_READINESS_REVIEW.md`
- project learnings tracker and dedicated review-rigor/governance learning pages
- PR template checklist for learnings-tracker review and invariant,
  exploit-matrix, and contract/gate review
- Stage 8 CI budget status for Locust performance smoke and Lighthouse checks

## Phase 1 Closure Branch Scope

Allowed governance/reporting changes for Module A:

- `AGENTS.md`
- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `Makefile`
- `README.md`
- `docs/PRD.md`
- `docs/ENGINEERING_PROCESS_RCA.md`
- `docs/QUALITY_GATES.md`
- `docs/REPOSITORY_GUARDRAILS.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/RELEASE_READINESS_REVIEW.md`
- `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `docs/RISK_REGISTER.md`
- `docs/RUNBOOK.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/PROJECT_GOVERNANCE_LEARNINGS.md`
- `docs/TRACEABILITY.md`
- `docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md`
- `docs/reviews/PHASE_1_CLOSURE_REPORT.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/PROCESS_HARDENING_FINDINGS.md`
- `docs/evals/phase1_golden_questions.jsonl`
- `docs/demo/PHASE_1_DEMO_SCRIPT.md`
- `docs/demo/PHASE_1_DEMO_CHECKLIST.md`
- `docs/demo/PHASE_1_SCREENSHOT_GUIDE.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `portfolio/README.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `scripts/quality/check_quality_stage.py`
- `scripts/quality/check_recommended_review_items.py`

Process-only follow-up branches must use
`phase-1-closure-process-<issue>-<phf-id>-<slug>`. They inherit the Module A
governance/reporting list above and may additionally change only the executable
process guardrail and its tests:

- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/SKILL_SELECTION_AND_EVIDENCE.md`
- `scripts/guardrails_check.py`
- `tests/unit/test_guardrails_check.py`
- `tests/unit/test_phase1_closure_docs.py`

When a process-only branch is governed by GovernancePreflightV1, it may also
change exactly one matching preflight artifact:
`docs/governance/preflights/issue-<issue>.json`, where `<issue>` is the issue
number embedded in the branch name. It must not change a preflight artifact for
any other issue.

Process-only branches must not touch backend, frontend, provider, RAG, avatar,
database, Docker, or product runtime files. Issue-specific branches such as
`phase-1-closure-39-*` retain their separate implementation/evidence allowlist
only for the linked issue scope below.

Issue `#225` is the bounded Demo Phase 0 planning branch for the hosted
controlled real-media demo path. Branch
`phase-1-closure-process-225-demo-real-media-phase0-plan` may document source
facts, costs, hosted-demo controls, Checkpoint 1 and Checkpoint 2 sequencing,
failure-matrix categories, and fan-out review expectations in
`docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`, with the matching
`docs/governance/preflights/issue-225.json`, `docs/STAGE_ISSUE_PLAN.md`,
`docs/STATUS.md`, static gate updates, and focused gate tests.

It must not implement backend, frontend, provider, RAG, avatar, database,
Docker, hosted deployment, provider SDKs, provider keys, real audio generation,
real video generation, cloned identity, public synthetic-media distribution,
Product Mode 2, or production-readiness claims. Research for Checkpoint 1 and
Checkpoint 2 may be planned in parallel, but implementation remains sequential
and requires future issue-linked PRs.

Issue `#229` is the bounded Demo Checkpoint 1 PR 1 branch for
spec/source-facts/governance only. Branch
`phase-1-closure-process-229-demo-checkpoint1-spec-governance` may refresh
official provider/platform source facts, define future Checkpoint 1
implementation contracts, record cost-minimized controlled-demo constraints,
expand security/privacy/consent/eval failure matrices, and record fan-out review
findings in `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`, with the matching
`docs/governance/preflights/issue-229.json`, `docs/STAGE_ISSUE_PLAN.md`,
`docs/STATUS.md`, `docs/THIRD_PARTY_NOTICES.md`, and the narrow Phase 1
Closure status-contract test/checker files needed to keep `SSV1-NEXT` aligned:
`scripts/quality/check_phase1_closure_docs.py` and
`tests/unit/test_phase1_closure_docs.py`.

It must not implement backend, frontend, provider, RAG, avatar, database,
Docker, hosted deployment, provider SDKs, provider keys, real audio generation,
real video generation, cloned identity, public synthetic-media distribution,
Product Mode 2, or production-readiness claims. Future Checkpoint 1
implementation must proceed through separate issue-linked PRs, beginning with a
latency/capacity/cost/access/quota/cache/pre-generation/retention/launch-level
contract PR before provider abstraction plus real TTS, avatar/video provider
integration, and hosted-demo access/quota/retention/demo polish.

Issue `#235` is the bounded Demo Checkpoint 1 PR 2 branch for the latency,
capacity, cost, access, quota, cache/pre-generation, retention, and launch-level
contract that follows merged PR `#230` / issue `#229`. Branch
`phase-1-closure-process-235-demo-checkpoint1-contract` may define minimum
implementation requirements and future evidence mappings in
`docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md` and align canonical launch/access
wording in `docs/LAUNCH_LEVELS.md`, with the matching
`docs/governance/preflights/issue-235.json`, `docs/STAGE_ISSUE_PLAN.md`,
`docs/STATUS.md`, `docs/THIRD_PARTY_NOTICES.md`, and the narrow Phase 1 Closure
status-contract test/checker files needed to keep PR2 scope exact:
`scripts/quality/check_phase1_closure_docs.py` and
`tests/unit/test_phase1_closure_docs.py`.

It must not implement backend, frontend, provider abstraction, TTS, avatar/video,
hosted deployment, access-system implementation, database, Docker, CI workflow,
provider SDKs, provider keys, real audio generation, real video generation,
cloned identity, public synthetic-media distribution, Product Mode 2, or
production-readiness claims. It must also not set up provider accounts,
configure provider dashboards, activate paid plans, fund provider wallets,
select production models or voices, make real provider test calls, incur paid
spend, or pre-authorize the later hosted-demo PR. PR2 creates minimum future
requirements only; PR3 provider abstraction plus real TTS still requires fresh
selected-provider source facts and executable disabled-default, quota,
retention/deletion, redaction, timeout, retry, and duplicate-spend safeguards
before any provider egress is enabled.

Issue `#237` is the bounded Demo Checkpoint 1 PR 3 branch for server-side TTS
provider abstraction plus optional real TTS provider adapter work only. Branch
`phase-1-closure-process-237-demo-checkpoint1-pr3-real-tts` may add the PR3
planning/evidence artifact, refresh official TTS provider source facts, update
the server-side Stage 6 TTS boundary, add mock/fake-provider tests, and align
the API/status/traceability/third-party/provider-ADR documents impacted by that
TTS-only boundary:

- `docs/governance/preflights/issue-237.json`
- `docs/reviews/ISSUE_237_DEMO_CHECKPOINT1_PR3_TTS_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/API_CONTRACT.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `backend/app/tts_provider.py`
- `backend/app/stage6.py`
- `backend/app/main.py`
- `tests/unit/test_stage6_tts_provider.py`
- `tests/unit/test_stage6_multilingual.py`
- `tests/api/test_stage6_multilingual_api.py`

It must not implement avatar/video provider work, hosted deployment, hosted
access systems, public URLs, public synthetic-media distribution, cloned voice,
cloned face/avatar, Product Mode 2, production-readiness claims, Docker changes,
CI workflow changes, frontend changes, provider SDK installation, provider
account setup, provider dashboard configuration, paid plan activation, wallet
funding, paid spend, real provider calls in CI, or real provider test calls
without a fresh PR3 plan and explicit written human-owner approval. Mock/local
TTS remains the default for local/dev/test/CI, and every optional provider-egress
path must fail closed unless disabled-default, missing/invalid key,
language/script-length, quota reservation/refund, timeout/retry,
duplicate-spend prevention, output validation, retention/deletion, and redacted
logging safeguards are executable before egress.

Issue `#241` is the bounded Demo Checkpoint 1 PR 4 branch for server-side
avatar/video provider integration only. Branch
`phase-1-closure-process-241-demo-checkpoint1-pr4-avatar-video` may add the PR4
planning/evidence artifact, refresh official avatar/video provider source
facts, update the server-side Stage 7 avatar/video boundary, add mock/fake
provider tests, and align API/status/traceability/third-party/provider-ADR
documents impacted by that avatar/video-only boundary:

- `docs/governance/preflights/issue-241.json`
- `docs/reviews/ISSUE_241_DEMO_CHECKPOINT1_PR4_AVATAR_VIDEO_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/API_CONTRACT.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `backend/app/avatar_video_provider.py`
- `backend/app/stage7.py`
- `backend/app/main.py`
- `tests/unit/test_stage7_avatar_video_provider.py`
- `tests/unit/test_stage7_avatar.py`
- `tests/api/test_stage7_avatar_api.py`

It must not implement hosted deployment, hosted access systems, invite flows,
public URLs, demo polish, public synthetic-media distribution, cloned voice,
cloned face/avatar, digital twins, replica-profile creation, Product Mode 2,
production-readiness claims, Docker changes, CI workflow changes, frontend
changes, provider SDK installation, provider account setup, provider dashboard
configuration, paid plan activation, wallet funding, paid spend, real provider
calls in CI, or real provider test calls without a fresh PR4 plan and explicit
written human-owner approval. Mock/local avatar/video remains the default for
local/dev/test/CI, and every optional provider-egress path must fail closed
unless disabled-default, missing/invalid key, failed-eval block,
source/eval/media/citation binding, prompt-injection rejection,
quota reservation/refund, timeout/retry, retry-cap, duplicate-spend prevention,
provider response and artifact validation, retention/deletion evidence, synthetic
disclosure, and redacted logging safeguards are executable before egress.

Issue `#243` is the bounded Demo Checkpoint 1 PR 5 branch for hosted-demo
access, quota, retention, and reviewer-facing polish only. Branch
`phase-1-closure-process-243-demo-checkpoint1-pr5-hosted-demo` may add the PR5
planning/evidence artifact, refresh official hosted/access/quota/retention
source facts, add a local/fake hosted-demo decision boundary, add narrow API and
frontend evidence polish, and align API/status/traceability/third-party docs:

- `docs/governance/preflights/issue-243.json`
- `docs/reviews/ISSUE_243_DEMO_CHECKPOINT1_PR5_HOSTED_DEMO_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/LAUNCH_LEVELS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THIRD_PARTY_NOTICES.md`
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

It must not implement hosted deployment, public URLs, provider account setup,
provider dashboard configuration, paid plan activation, wallet funding, paid
spend, real provider calls, provider SDK installation, Docker changes, CI
workflow changes, database changes, Stage 6 provider-internal mutation, Stage 7
provider-internal mutation, public synthetic-media distribution, cloned voice,
cloned face/avatar, digital twins, replica-profile creation, Product Mode 2, or
production-readiness claims. PR5 hosted-demo behavior remains local/fake and
disabled by default unless a later issue records owner-written approval and
fresh safeguards for a real hosted environment.

Issue `#249` is the bounded C3-PR1 branch for Checkpoint 3A planning and
guardrails only. Branch
`phase-1-closure-process-249-checkpoint3a-planning-guardrails` may define the
public-safe roadmap update, Checkpoint 3A acceptance matrix, failing-by-design
`make checkpoint3-acceptance` skeleton, old-behavior failure proof, child issue
breakdown, fan-out findings, exact changed-file allowlist, and focused
regression tests:

- `docs/governance/preflights/issue-249.json`
- `docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `Makefile`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`

Checkpoint 3A sequence is public-safe and serialized: Checkpoint 3A
Non-Cloned Product-Faithful Controlled Demo first, Checkpoint 3B Cloned
Identity Consent And Provenance later, Checkpoint 3C Clone-Integrated
Controlled Demo after those gates, and production later. The Checkpoint 3A
planned probes are API E2E, language quality, media artifacts,
access/quota/retention, security/observability, performance, real-browser E2E
with no success-path interception, and output-correctness that executes rather
than reads.

It must not implement backend, frontend, provider, RAG, avatar, database,
Docker, workflow, dependency, product runtime, cloned voice, cloned face,
digital twin, real-person likeness, public URL, provider setup, provider SDK,
provider key, real provider call, paid spend, public distribution, or
production-readiness claims. It must not expose private plans, internal
strategy, provider strategy, private media, real personal data, secrets,
credentials, tokens, invite codes, private certificates, or real provider
payloads.

Issue `#253` is the bounded C3A-CP1 child implementation branch for the
Checkpoint 3 acceptance harness and API E2E foundation only. Branch
`phase-1-closure-process-253-c3a-cp1-acceptance-api-e2e` may convert
`make checkpoint3-acceptance` into an executable dispatcher, implement the API
E2E acceptance probe, keep later Checkpoint 3A probes planned/non-passing, add
old-behavior false-pass regressions, record sub-agent fan-out findings, and
update only these public-safe files:

- `docs/governance/preflights/issue-253.json`
- `docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_api_e2e.py`

C3A-CP1 must execute the local FastAPI product path for project creation,
approved synthetic knowledge upload, ingestion/chunk/store, retrieval, grounded
walkthrough generation, unsupported-claim evaluation, stored API replay
evidence, and bounded ops record-count evidence. It must not pass through
docs/prose/static-snapshot scanning. Later language quality, media artifacts,
access/quota/retention, security/observability, performance, real-browser E2E,
and output-correctness probes remain future Checkpoint 3A child work. The issue
does not authorize Checkpoint 3A completion, Checkpoint 3B, Checkpoint 3C,
providers, paid spend, hosted deployment, public URL, cloned identity, frontend
browser implementation, public distribution, or production-readiness claims.

Issue `#257` is the bounded C3A-CP2 child implementation branch for the
Checkpoint 3A executable output-correctness probe only. Branch
`phase-1-closure-process-257-c3a-cp2-output-correctness` may implement the
output-correctness probe in `make checkpoint3-acceptance`, keep the API E2E
foundation probe passing, keep later Checkpoint 3A probes planned/non-passing,
add old-behavior false-pass regressions, record sub-agent fan-out findings, and
update only these public-safe files:

- `docs/governance/preflights/issue-257.json`
- `docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_output_correctness.py`

C3A-CP2 must execute the local FastAPI product/API path for approved synthetic
project knowledge, ingestion/chunk/store, grounded walkthrough generation,
idempotent API replay, and runtime output/evidence checks. Required output
facts must be accepted only when bound to visible citations, `contextRefs`,
`claimSupports`, project/document/chunk identity, source checksums, and
`evidenceSnapshot` data returned through API-visible behavior. It must reject
docs/prose/static-snapshot or canned-success false passes, correct-looking text
without evidence binding, unsupported generated claims, and cross-project fact
replay. Later language quality, media artifacts, access/quota/retention,
security/observability, performance, and real-browser E2E probes remain future
Checkpoint 3A child work. The issue does not authorize Checkpoint 3A completion,
Checkpoint 3B, Checkpoint 3C, providers, paid spend, hosted deployment, public
URL, cloned identity, frontend browser implementation, public distribution, or
production-readiness claims.

Issue `#259` is the bounded C3A-CP3 child implementation branch for the
Checkpoint 3A executable language-quality probe only. Branch
`phase-1-closure-process-259-c3a-cp3-language-quality` may implement the
language-quality probe in `make checkpoint3-acceptance`, keep the API E2E
foundation and output-correctness probes passing, keep later Checkpoint 3A
probes planned/non-passing, add old-behavior false-pass regressions, record
sub-agent fan-out findings, and update only these public-safe files:

- `docs/governance/preflights/issue-259.json`
- `docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_language_quality.py`

C3A-CP3 must execute the local FastAPI product/API path for approved synthetic
project knowledge, ingestion/chunk/store, grounded walkthrough generation,
idempotent API replay, and runtime language/evidence checks. Generated language
quality must be accepted only when runtime `acceptedScriptText` has coherent
walkthrough structure, audience-appropriate English Stage 4 tone, readable
citation placement, non-trivial length, no placeholder text, no internal debug
leakage, no cross-project or unsupported language, and API-visible evidence in
`contextRefs`, `claimSupports`, citation indexes, and `evidenceSnapshot` data.
It must reject docs/prose/static-snapshot or canned-success false passes,
grounded-looking placeholder output, trivially short citation-bearing output,
debug/internal leakage, malformed citation placement, cross-project language
insertion, and style text without runtime API evidence. Later media artifacts,
access/quota/retention, security/observability, performance, and real-browser
E2E probes remain future Checkpoint 3A child work. The issue does not authorize
Checkpoint 3A completion, Checkpoint 3B, Checkpoint 3C, providers, paid spend,
hosted deployment, public URL, cloned identity, frontend browser
implementation, public distribution, or production-readiness claims.

Issue `#261` is the bounded C3A-CP4 child implementation branch for the
Checkpoint 3A executable media-artifacts probe only. Branch
`phase-1-closure-process-261-c3a-cp4-media-artifacts` may implement the
media-artifacts probe in `make checkpoint3-acceptance`, keep the API E2E
foundation, output-correctness, and language-quality probes passing, keep later
Checkpoint 3A probes planned/non-passing, add old-behavior false-pass
regressions, record sub-agent fan-out findings, bundle the PR `#260` / issue
`#259` ledger cleanup because this is a substantive child checkpoint, and update
only these public-safe files:

- `docs/governance/preflights/issue-261.json`
- `docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_media_artifacts.py`

C3A-CP4 must execute the local FastAPI product/API path for approved synthetic
project knowledge, ingestion/chunk/store, grounded walkthrough generation,
Stage 6 local/mock translated script, subtitles, and voice manifest, Stage 7
synthetic-avatar consent, demo HTML, render manifest, and video-export
placeholder artifacts, plus idempotent API replay and runtime artifact/evidence
checks. Media artifacts must be accepted only when runtime API-visible artifact
fields have valid MIME type, safe filename, Base64 content, checksum,
source-run/evaluation/citation/context/claim-support binding, local/mock
provider posture, no real media binary overclaim, and no cloned identity. It
must reject docs/prose/static-snapshot or canned-success false passes,
artifact-shape-only evidence without source binding, checksum or MIME mismatch,
real-media overclaim, and cloned-identity overclaim. Later
access/quota/retention, security/observability, performance, and real-browser
E2E probes remain future Checkpoint 3A child work. The issue does not authorize
Checkpoint 3A completion, Checkpoint 3B, Checkpoint 3C, providers, paid spend,
hosted deployment, public URL, cloned identity, frontend browser
implementation, backend/frontend/provider/dependency changes, real media
binaries, public distribution, or production-readiness claims.

Issue `#263` is the bounded C3A-CP5 child implementation branch for the
Checkpoint 3A executable access/quota/retention probe only. Branch
`phase-1-closure-263-c3a-cp5-access-quota-retention` may implement the
access/quota/retention probe in `make checkpoint3-acceptance`, keep the API E2E
foundation, output-correctness, language-quality, and media-artifacts probes
passing, keep later Checkpoint 3A probes planned/non-passing, add old-behavior
false-pass regressions, record fan-out findings, bundle the PR `#262` / issue
`#261` ledger cleanup because this is a substantive child checkpoint, and
update only these public-safe files:

- `docs/governance/preflights/issue-263.json`
- `docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_access_quota_retention.py`

C3A-CP5 must execute the local FastAPI product/API path for at least two
approved synthetic local projects, knowledge upload/approval, ingestion/chunk/
store, grounded walkthrough generation, API-visible access boundaries, scoped
idempotency replay, deterministic upload/request/body/document or local quota
limits, API-visible retention/deletion replay behavior, tombstone evidence,
bounded ops/status evidence, and public-safe redaction. It must reject
docs/prose/static-snapshot or canned-success false passes, cross-project replay
with valid-looking IDs, idempotency replay that attempts to bypass actor,
project, or source-run boundaries, over-limit requests that leak raw payload
text, deleted or retained evidence replayed as active when policy forbids it,
and style-only or status-only text without runtime API evidence. Later
security/observability, performance, and real-browser E2E probes remain future
Checkpoint 3A child work. The issue does not authorize Checkpoint 3A
completion, Checkpoint 3B, Checkpoint 3C, providers, paid spend, hosted
deployment, public URL, cloned identity, frontend browser implementation,
backend/frontend/provider/dependency changes, real media binaries, public
distribution, or production-readiness claims.

Issue `#265` is the bounded C3A-CP6 child implementation branch for the
Checkpoint 3A executable security/observability probe only. Branch
`phase-1-closure-265-c3a-cp6-security-observability` may implement the
security/observability probe in `make checkpoint3-acceptance`, keep the API E2E
foundation, output-correctness, language-quality, media-artifacts, and
access/quota/retention probes passing, keep later Checkpoint 3A probes
planned/non-passing, add old-behavior false-pass regressions, record fan-out
findings, bundle the PR `#264` / issue `#263` ledger cleanup because this is a
substantive child checkpoint, and update only these public-safe files:

- `docs/governance/preflights/issue-265.json`
- `docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_security_observability.py`

C3A-CP6 must execute the local FastAPI product/API path for approved synthetic
project knowledge, upload/approval/ingestion, grounded walkthrough generation,
runtime API-visible security controls, privacy/redaction behavior,
observability metadata, bounded failure evidence, local/mock provider posture,
and anti-false-pass guarantees. It must reject docs/prose/static-snapshot or
canned-success false passes, style-only/status-only text, success-shaped
dictionaries without acceptance-runtime nonce/source/run binding, missing trace/run/
evaluation/observability binding, unapproved or prompt-injection-bearing
knowledge where policy forbids it, unsupported claim acceptance, cross-project
replay with valid-looking IDs, same-payload cross-actor access attempts with a
reused idempotency key, same-actor idempotency conflicts that attempt to bypass
security, project, source-run, or evidence boundaries, unsafe replay, and public
failure output that leaks raw uploaded content, prompt-injection
text, private-looking markers, token/password/secret/api-key values, or
snake_case variants. Later performance and real-browser E2E probes remain
future Checkpoint 3A child work. The issue does not authorize Checkpoint 3A
completion, Checkpoint 3B, Checkpoint 3C, providers, paid spend, hosted
deployment, public URL, cloned identity, frontend browser implementation,
backend implementation, provider/dependency changes, real media binaries,
public distribution, or production-readiness claims.

Issue `#267` is the bounded C3A-CP7 child implementation branch for the
Checkpoint 3A executable performance probe only. Branch
`phase-1-closure-267-c3a-cp7-performance-probe` may implement the performance
probe in `make checkpoint3-acceptance`, keep the API E2E foundation,
output-correctness, language-quality, media-artifacts, access/quota/retention,
and security/observability probes passing, keep the later real-browser E2E
probe planned/non-passing, add old-behavior false-pass regressions, record
fan-out findings, bundle the PR `#266` / issue `#265` ledger cleanup because
this is a substantive child checkpoint, and update only these public-safe
files:

- `docs/governance/preflights/issue-267.json`
- `docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/acceptance/test_checkpoint3_performance.py`

C3A-CP7 must execute the local FastAPI product/API path for approved synthetic
project knowledge, upload/approval/ingestion, grounded walkthrough generation,
idempotent replay, bounded ops/status evidence, named operation timings,
explicit thresholds, request ID binding, elapsed durations, pass/fail status,
source-run/evaluation binding, generation trace latency, local/mock provider
posture, and public-safe failure context. It must reject docs/prose/static-
snapshot or canned-success false passes, style-only/status-only text,
success-shaped timing dictionaries without runtime nonce/source/run binding,
missing run/request/performance binding, stale performance evidence from a
different run, cross-project replay with valid-looking IDs, implicit
thresholds, zero-duration fake timings, unsafe provider/public/production
claims, timeout/subprocess failure leaks, and public failure output that leaks
raw uploaded content, prompt-injection text, private-looking markers, sensitive
tokens, or accepted script text. The later real-browser E2E probe remains
future Checkpoint 3A child work. The issue does not authorize Checkpoint 3A
completion, Checkpoint 3B, Checkpoint 3C, providers, paid spend, hosted
deployment, public URL, cloned identity, frontend browser implementation,
backend implementation, provider/dependency changes, real media binaries,
public distribution, or production-readiness claims.

Issue `#269` is the bounded C3A-CP8 child implementation branch for the
Checkpoint 3A executable real-browser E2E probe only. Branch
`phase-1-closure-269-c3a-cp8-real-browser-e2e` may implement the
real-browser E2E probe in `make checkpoint3-acceptance`, keep the API E2E
foundation, output-correctness, language-quality, media-artifacts,
access/quota/retention, security/observability, and performance probes
passing, add old-behavior false-pass regressions, record fan-out findings,
bundle the PR `#268` / issue `#267` ledger cleanup because this is a
substantive child checkpoint, apply the existing Next.js dependency audit patch
required by `make dependency-audit`, and update only these public-safe files:

- `docs/governance/preflights/issue-269.json`
- `docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/playwright.checkpoint3.config.ts`
- `frontend/tests/checkpoint3-real-browser.spec.ts`

C3A-CP8 must execute the local browser-controlled demo path for approved
synthetic project knowledge through user-visible project creation,
upload/approval/ingestion, grounded walkthrough generation, multilingual
artifact generation, synthetic-avatar consent, local avatar-demo artifact
rendering, citations, browser-observed API request/response binding, bounded
ops/status evidence, runtime nonce binding, local/mock provider posture, and
public-safe failure context. It must reject docs/prose/static-snapshot or
canned-success false passes, API-only substitutes, route/network interception
that fabricates success, success-shaped browser state without runtime nonce,
missing run/request/source/eval binding, stale browser evidence from a
different run, cross-project replay with valid-looking IDs, unsafe
provider/public/production claims, timeout/subprocess failure leaks, and public
failure output that leaks raw uploaded content, prompt-injection text,
private-looking markers, sensitive tokens, provider payloads, or generated full
script text. The issue does not authorize Checkpoint 3B, Checkpoint 3C,
providers, paid spend, hosted deployment, public URL, provider setup,
cloned identity, frontend product behavior changes, backend implementation,
new provider/dependency families, real media binaries, public distribution, or
production-readiness claims. The only dependency-scope exception is the
existing Next.js patch recorded in `docs/THIRD_PARTY_NOTICES.md`; there is no
hosted deployment, no provider setup, no cloned identity, and no
production-readiness claim.

PR A branch `phase-1-closure-process-172-gpf-v1-offline-core` may additionally
change only the offline core paths below. This exception does not authorize a
repository adapter or CI/GitHub evidence verifier:

- `docs/governance/GOVERNANCE_PREFLIGHT_V1.schema.json`
- `scripts/governance_preflight_v1.py`
- `tests/unit/test_governance_preflight_v1.py`

PR B branch `phase-1-closure-process-176-gpf-v1-repository-integration` is
limited to the ten paths frozen in its issue-specific preflight and executable
phase allowlist. It adds offline, prospective repository validation: the first
branch commit contains only that preflight, later commits have no prescribed
grouping, and validation is bounded at 1,000 commits and 2,000 final paths.
Pre-PR-B bases, retained evidence, and unrelated branches stay exempt; GitHub
PR C issue `#178` adds those live API, identity, exact-head approval, lifecycle, and required-check proofs only in supported pull-request CI with bounded polling and no correction automation.

Issue `#181` is a bounded prerequisite maintenance branch for the pre-existing
local Lighthouse `NO_FCP` gate failure that blocked issue `#155` validation. It
may change only:

- `docs/governance/preflights/issue-181.json`
- `scripts/ci/frontend-lighthouse.sh`
- `frontend/scripts/run-lighthouse.mjs`
- `frontend/src/app/lighthouse-runner.test.ts`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `docs/ADR/0028-local-lighthouse-browser-selection.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/STATUS.md`

It must not change frontend product UI files, backend/runtime behavior,
provider behavior, hosted-launch policy, or production posture.

Issue `#184` is the PHF-020A replacement for stopped issue `#167` and retained
draft PR `#168`. Branch
`phase-1-closure-process-184-phf-020a-structured-policy-replacement` may change
only:

- `docs/governance/preflights/issue-184.json`
- `AGENTS.md`
- `docs/PHASE_PLAN.md`
- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

It replaces Product Mode free-form prose scanning with closed structured policy
authority. It must preserve exact-path scope, keep `docs/STATUS.md` as mutable
current-state authority until PHF-020B, and must not mutate stopped PRs or issues
`#166`, `#167`, `#168`, `#169`, or `#170`.

It must not authorize PHF-020B, Product Mode 2, runtime/CH-M1 work, real media,
providers, hosted/public launch, production, backend, frontend, workflow, Docker,
dependency, RAG, avatar, database, or product implementation work.

Issue `#188` is the PHF-020B StatusStateV1 successor after PR `#187`. Branch
`phase-1-closure-process-188-phf-020b-status-state-v1` may change only:

- `docs/governance/preflights/issue-188.json`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/SKILL_EXECUTION_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

It normalizes mutable current-state authority in `docs/STATUS.md` without
replacing the PHF-020A Product Mode authority tables in `docs/PHASE_PLAN.md`.
It must not close or satisfy issue `#8` or issue `#155`, must preserve stopped
issue `#167` and PR `#168`, and must not authorize Product Mode 2, runtime,
CH-M1 implementation, real media, providers, hosted/public launch, production,
backend, frontend, workflow, Docker, dependency, RAG, avatar, database, or
product implementation work.

Issue `#204` is the `CH-M1-01` Product Mode 1 child under controller issue
`#155`. Branches using `phase-1-closure-155-ch-m1-01-*` may change only:

- `docs/reviews/ISSUE_204_CH_M1_01_PREFLIGHT.md`
- `docs/ADR/0019-ch16-consent-capture.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `frontend/src/app/page.tsx`
- `frontend/tests/smoke.spec.ts`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

They are limited to repairing the local/mock frontend durable avatar-consent
request chain: call `/avatar-consents`, pass the returned `consentRecordId` to
`/avatar-renders`, and prove the sequence with mocked browser evidence. They
must not change backend consent semantics, provider behavior, Stage 4/6/7
runtime orchestration, external accounts, hosted/public launch, Product Mode 2,
real audio/video, imported media, cloned identity, public media distribution,
production durability, backup/restore, monitoring, release posture, or stopped
predecessor surfaces.

Issue `#208` is the `CH-M1-02` Product Mode 1 child under controller issue
`#155`; issue `#209` may be included only as the directly coupled local
Phase 1 Closure quality-dispatch clarification. Branches using
`phase-1-closure-208-*` may change only:

- `docs/governance/preflights/issue-208.json`
- `docs/reviews/ISSUE_208_209_CH_M1_02_PREFLIGHT.md`
- `docs/ADR/0029-ch-m1-02-real-stack-evidence.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `frontend/playwright.real-stack.config.ts`
- `frontend/tests/real-stack.spec.ts`
- `scripts/quality/check_phase1_closure_docs.py`
- `scripts/quality/check_quality_stage.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_quality_dispatcher.py`

They are limited to proving a controlled local/mock real browser -> frontend ->
backend -> Compose path without application API interception and clarifying
local Phase 1 Closure quality behavior on `main`. They must not change backend
product behavior, frontend product UI, Compose topology, workflows,
dependencies, providers, hosted/public launch, Product Mode 2, real audio/video,
imported media, cloned identity, public media distribution, production
durability, backup/restore, monitoring, release posture, or stopped predecessor
surfaces.

Issue `#213` is the combined Checkpoint A through Checkpoint B Product Mode 1
child under controller issue `#155`. Branch
`phase-1-closure-155-mode1-checkpoint-a-to-b` may change only:

- `docs/governance/preflights/issue-213.json`
- `docs/reviews/ISSUE_213_MODE1_CHECKPOINT_A_TO_B_PREFLIGHT.md`
- `docs/ADR/0030-mode1-stage6-stage7-bundle-binding.md`
- `docs/API_CONTRACT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/demo/PHASE_1_DEMO_CHECKLIST.md`
- `docs/demo/PHASE_1_DEMO_SCRIPT.md`
- `docs/demo/PHASE_1_SCREENSHOT_GUIDE.md`
- `demo/stage8_seed_project.md`
- `README.md`
- `portfolio/README.md`
- `backend/app/main.py`
- `backend/app/stage6.py`
- `backend/app/stage7.py`
- `tests/unit/test_stage6_multilingual.py`
- `tests/unit/test_stage7_avatar.py`
- `tests/unit/test_local_durability.py`
- `tests/api/test_stage6_multilingual_api.py`
- `tests/api/test_stage7_avatar_api.py`
- `frontend/src/app/page.tsx`
- `frontend/src/app/page.test.tsx`
- `frontend/tests/smoke.spec.ts`
- `frontend/tests/real-stack.spec.ts`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

This combined branch is limited to Checkpoint A evidence, `CH-M1-03`
multilingual bundle contract, `CH-M1-04` backend bundle-bound render behavior,
`CH-M1-05` frontend artifact proof, `CH-M1-06` demo docs/seed updates, and
Checkpoint B evidence for the controlled local/mock Mode 1 demo. It must not
implement Product Mode 2, real audio binaries, MP4/WebM generation,
STT/imported video, external or paid providers, hosted launch, public
distribution, multi-worker or production-readiness claims, dependency/workflow
or Compose topology changes, provider keys, provider SDKs, or mutation of
stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and `#168`.

Context 0 issue `#39` closure-contract branches using
`phase-1-closure-39-context0-*` are stricter than general issue `#39` branches:
they may touch only docs, guardrails, tests, PR templates, and CI workflow
guardrail wiring. They must not touch backend, frontend, schema, migration,
worker, provider, monitoring, database, Docker, or runtime product files.

`phase-1-closure-39-ch01-*` is reserved for the `CH-01` migration baseline
chunk for issue `#39` child issue `#86`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/migrations.py`
- `docs/ADR/0013-ch01-migration-baseline-runner.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_storage_migrations.py`

`phase-1-closure-39-ch01-*` must not touch Stage 4/6/7 runtime orchestration,
provider/media logic, ACID/CAS durable metadata kernel work, backup/restore,
monitoring, release posture, or unrelated governance/process files.

`phase-1-closure-39-ch-02-*` is reserved for the `CH-02` ACID/CAS storage
kernel chunk for issue `#39` child issue `#93`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/postgres_state.py`
- `docs/ADR/0014-ch02-acid-cas-storage-kernel.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_postgres_state.py`

`phase-1-closure-39-ch-02-*` must not touch Stage 4/6/7 durable graph or
artifact orchestration, idempotency/lease/outbox runtime semantics, backup or
restore flows, monitoring/alerts/watch, release posture, provider/media/privacy
controls, or unrelated governance/process files.

`phase-1-closure-39-ch-03-*` is reserved for the `CH-03` Stage 4 durable graph
chunk for issue `#39` child issue `#107`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/stage4_graph.py`
- `docs/ADR/0018-ch03-stage4-durable-graph.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_stage4_durable_graph.py`

`phase-1-closure-39-ch-03-*` must not touch Stage 6/7 durable artifact
orchestration, operations monitoring, backup or restore flows, release posture,
provider/media/privacy controls, retention/untrusted-input closure, or unrelated
governance/process files.

`phase-1-closure-39-ch-04-*` is reserved for the `CH-04` idempotency semantics
chunk for issue `#39` child issue `#97`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/postgres_state.py`
- `docs/ADR/0015-ch04-idempotency-semantics.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_postgres_state.py`

`phase-1-closure-39-ch-04-*` must not touch Stage 4/6/7 durable graph or
artifact orchestration, lease or outbox runtime semantics, backup or restore
flows, monitoring/alerts/watch, release posture, provider/media/privacy
controls, or unrelated governance/process files.

`phase-1-closure-39-ch-05-*` is reserved for the `CH-05` lease fencing chunk
for issue `#39` child issue `#95`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/postgres_state.py`
- `docs/ADR/0016-ch05-lease-fencing.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_postgres_state.py`

`phase-1-closure-39-ch-05-*` must not touch Stage 4/6/7 durable graph or
artifact orchestration, idempotency or outbox runtime semantics, backup or
restore flows, monitoring/alerts/watch, release posture, provider/media/privacy
controls, or unrelated governance/process files.

`phase-1-closure-39-ch-06-*` is reserved for the `CH-06` committed outbox chunk
for issue `#39` child issue `#96`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/postgres_state.py`
- `docs/ADR/0017-ch06-committed-outbox.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_postgres_state.py`

`phase-1-closure-39-ch-06-*` must not touch Stage 4/6/7 durable graph or
artifact orchestration, idempotency or lease runtime semantics, backup or
restore flows, monitoring/alerts/watch, release posture, provider/media/privacy
controls, or unrelated governance/process files.

`phase-1-closure-39-ch-07-*` is reserved for the `CH-07` Stage 6 durable replay
chunk for issue `#39` child issue `#109`. It may touch only:

- `backend/app/main.py`
- `backend/app/stage6.py`
- `backend/app/storage/__init__.py`
- `backend/app/storage/file_state.py`
- `docs/ADR/0009-context2-idempotency-lease-outbox-contract.md`
- `docs/ADR/0020-ch07-stage6-durable-replay.md`
- `docs/API_CONTRACT.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/api/test_stage6_multilingual_api.py`
- `tests/unit/test_local_durability.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_stage6_multilingual.py`

`phase-1-closure-39-ch-07-*` must not touch Stage 4 durable graph storage
contracts, Stage 7 render/export state, lease or outbox runtime semantics,
backup or restore flows, monitoring/alerts/watch, release posture,
provider/media/privacy controls, retention/untrusted-input closure, or unrelated
governance/process files.

`phase-1-closure-39-ch-08-*` is reserved for the `CH-08` Stage 7 render artifact
state chunk for issue `#39`. Issue `#115` remains the closed preflight-only
child issue, issue `#119` is the closed implementation child issue, and narrow
CH-08 closeout reconciliation work may use the same branch family only for the
files below. It may touch only:

- `backend/app/main.py`
- `backend/app/stage7.py`
- `backend/app/storage/file_state.py`
- `docs/ADR/0021-ch08-stage7-render-artifact-state.md`
- `docs/API_CONTRACT.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/api/test_stage7_avatar_api.py`
- `tests/unit/test_local_durability.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_stage7_avatar.py`

`phase-1-closure-39-ch-08-*` must not touch Stage 4 durable graph storage
contracts, Stage 6 durable replay, lease or outbox runtime semantics, backup or
restore flows, monitoring/alerts/watch, release posture, provenance/disclosure
closure, provider/media/privacy controls beyond the render-state checkpoint,
retention/untrusted-input closure, or unrelated governance/process files.

`phase-1-closure-39-ch-09-*` is reserved for the `CH-09` technical rollback
compatibility chunk for issue `#39` child issue `#123`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/migrations.py`
- `docs/ADR/0022-ch09-technical-rollback-compatibility.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_storage_migrations.py`

`phase-1-closure-39-ch-09-*` must not touch Stage 4/6/7 runtime orchestration,
lease or outbox runtime semantics, backup or restore flows, monitoring/alerts/watch,
rollback communications, provider/media/privacy controls, retention/untrusted-input
closure, or unrelated governance/process files.

`phase-1-closure-39-restore-local-drill` is reserved for issue `#125`, the
local restore-integrity and restore-replay-safety drill for `DUR-RESTORE-001`.
This is a local file-backed evidence slice only and is explicitly not the
production `CH-14` backup/restore drill. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/local_restore_drill.py`
- `docs/ADR/0023-local-restore-integrity-drill.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_local_restore_drill.py`
- `tests/unit/test_phase1_closure_docs.py`

`phase-1-closure-39-restore-local-drill` must not touch production backup
platform assumptions, cloud snapshot or database-managed restore services,
metrics/SLO/alert/watch work, rollback communications, provider posture,
retention/erasure, provenance/disclosure, untrusted-input closure, Stage 4/6/7
runtime semantics, or unrelated governance/process files.

`phase-1-closure-138-*` is reserved for issue `#138`, the Click
`PYSEC-2026-2132` security remediation. It isolates Semgrep from the
application/runtime graph, locks patched Click releases, and hardens the
security gates without changing product runtime behavior. It may touch only:

- `docs/QUALITY_GATES.md`
- `docs/ADR/0006-stage8-release-hardening.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/RISK_REGISTER.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_138_CLICK_SECURITY_PREFLIGHT.md`
- `pyproject.toml`
- `scripts/__init__.py`
- `scripts/ci/__init__.py`
- `scripts/ci/backend-image-package-check.sh`
- `scripts/ci/check_semgrep_security.py`
- `scripts/ci/dependency-audit.sh`
- `scripts/ci/dependency-security.sh`
- `scripts/ci/docker-build.sh`
- `scripts/ci/fixtures/semgrep/clean.py`
- `scripts/ci/fixtures/semgrep/positive.py`
- `scripts/ci/run-semgrep.sh`
- `scripts/ci/semgrep-canary.yml`
- `scripts/ci/semgrep-targets.txt`
- `scripts/quality/check_phase1_closure_docs.py`
- `scripts/quality/check_stage3_docs.py`
- `tests/unit/test_dependency_security_contract.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tools/semgrep/pyproject.toml`
- `tools/semgrep/reviewed-inputs.sha256`
- `tools/semgrep/uv.lock`
- `uv.lock`

`phase-1-closure-138-*` must not touch backend/frontend product behavior,
production durability/restore implementation, provider/media paths, or issue
`#39` closure evidence. The Semgrep tool-only compatibility override remains a
human-reviewed, expiring exception and must not become a general dependency
override or advisory suppression.

`phase-1-closure-141-*` is reserved for issue `#141`, the architecture and
ownership prerequisite for the production-like durability readiness sequence.
It chooses a platform and handoff contract for issues `#142` through `#149`, but
does not provision infrastructure, connect runtime code, configure backups,
execute a restore, or close issue `#126`, `DUR-RESTORE-001`, or issue `#39`.
The contract must structurally validate all Stage 4/6/7 ownership rows and every
`#142`-`#149` dependency/acceptance row. Issue `#144` owns the source and restore
landing zone rather than a pre-created target DB; `#146` depends on the live
environment/catalog foundation; `#148` and the `#149` Go decision require tested
CH-12 alert routes from issue `#130` in addition to `#145`-`#147` handoffs; and
the later `#126` drill alone creates the PITR target and records actual results.
The target contract uses supported PITR inputs including IAM DB authentication,
verifies engine/configuration after creation, bounds S3 recovery to single-copy
objects `<=5,000,000,000 bytes`, registers cleanup before creation, uses
separately scoped target RDS/S3 inventory/deletion authority, deletes without a
final snapshot or retained automated backup, and blocks another exercise until
live inventory is clean. Detailed security/operations controls and S3/journal
STRIDE rows are mutation guarded.
It may touch only:

- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/ADR/0011-context4-backup-restore-drill.md`
- `docs/ADR/0027-production-like-durability-platform-ownership.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THREAT_MODEL.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

`phase-1-closure-141-*` must reject backend/frontend/runtime, database migration,
IaC, cloud provisioning, credentials, backup tooling, catalogs containing live
secrets/data, restore execution, and evidence claims that require an actual
environment. Human cost/account/region/owner/security approvals remain blockers.

`phase-1-closure-39-ch-14-*` is reserved for issue `#126`, the narrow
restore-readiness contract slice for `DUR-RESTORE-001`. This branch does not
execute a successful production restore drill. It packages the merged `#125`
local restore evidence with the current repo-baselined `CH-10` and `CH-11`
restore-adjacent contract artifacts, records the remaining human-only proof
surfaces, and adds anti-overclaim guardrails. It may touch only:

- `docs/ADR/0026-ch14-restore-readiness-contract.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md`
- `docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

`phase-1-closure-39-ch-14-*` must not touch backup tooling, cloud snapshot or
database-managed restore services, local restore drill runtime code, metrics
emitters, dashboards/alerts/watch, rollback communications, retention/erasure,
provider posture, provenance/disclosure, consent revocation, untrusted-input
closure, Stage 4/6/7 runtime semantics, or unrelated governance/process files.

`phase-1-closure-39-ch-10-*` is reserved for the `CH-10` production metrics
contract chunk for issue `#39` child issue `#128`. It may touch only:

- `backend/app/storage/__init__.py`
- `backend/app/storage/file_state.py`
- `backend/app/storage/migrations.py`
- `backend/app/storage/ops_metrics.py`
- `backend/app/storage/postgres_state.py`
- `docs/ADR/0024-ch10-production-metrics-contract.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_ops_metrics.py`
- `tests/unit/test_phase1_closure_docs.py`

`phase-1-closure-39-ch-10-*` must not touch dashboards, alert routing, paging,
first-hour watch execution, backup tooling, restore-drill execution evidence,
rollback communications evidence, Stage 4/6/7 application flows, provider/media/
privacy controls, retention/untrusted-input closure, or unrelated governance/
process files.

`phase-1-closure-39-ch-11-*` is reserved for the `CH-11` SLO and error-budget
contract chunk for issue `#39` child issue `#127`. It may touch only:

- `docs/ADR/0025-ch11-slo-error-budget.md`
- `docs/STATUS.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`

`phase-1-closure-39-ch-11-*` must not touch runtime metrics emitters,
dashboards, alert routing, paging, first-hour watch execution, backup tooling,
restore-drill execution evidence, rollback communications evidence, Stage 4/6/7
application flows, provider/media/privacy controls, retention/untrusted-input
closure, or unrelated governance/process files.

`phase-1-closure-39-ch-16-*` is reserved for the `CH-16` consent capture chunk
for issue `#39` child issue `#111`. It may touch only:

- `backend/app/main.py`
- `backend/app/stage7.py`
- `docs/ADR/0019-ch16-consent-capture.md`
- `docs/API_CONTRACT.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/api/test_stage7_avatar_api.py`
- `tests/unit/test_local_durability.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_stage7_avatar.py`

`phase-1-closure-39-ch-16-*` must not touch Stage 4 or Stage 6 durable replay,
ACID/CAS kernel internals, lease or outbox semantics, provenance/disclosure or
revocation closure, provider-release posture, retention/erasure,
untrusted-input closure, frontend paths, or unrelated governance/process files.

Additional allowed implementation/evidence changes for Phase 1 Closure issue
`#39`:

- `.env.example`
- `backend/app/main.py`
- `backend/app/rag/store.py`
- `backend/app/stage4.py`
- `backend/app/stage6.py`
- `backend/app/stage7.py`
- `backend/app/storage/__init__.py`
- `backend/app/storage/file_state.py`
- `docs/API_CONTRACT.md`
- `docs/ADR/0006-stage8-release-hardening.md`
- `docs/LOCAL_DEVELOPMENT.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `docs/RISK_REGISTER.md`
- `docs/reviews/RISK_REGISTER.md`
- `scripts/guardrails_check.py`
- `tests/api/test_health_api.py`
- `tests/unit/test_branch_protection_verifier.py`
- `tests/unit/test_guardrails_check.py`
- `tests/unit/test_phase1_closure_docs.py`
- `tests/unit/test_local_durability.py`

Allowed implementation/contract changes for Module F issue `#37`:

- `backend/app/main.py`
- `tests/api/test_stage4_slice_api.py`
- `docs/ADR/0007-local-principal-contract.md`
- `docs/API_CONTRACT.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/QUALITY_GATES.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/THREAT_MODEL.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/PHASE_1_CLOSURE_REPORT.md`
- `scripts/quality/check_phase1_closure_docs.py`

Allowed implementation/contract changes for Module B issue `#42`:

- `backend/app/main.py`
- `backend/app/stage7.py`
- `tests/unit/test_stage7_avatar.py`
- `tests/api/test_stage7_avatar_api.py`
- `docs/ADR/0004-avatar-provider-adapter.md`
- `docs/API_CONTRACT.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/PHASE_1_CLOSURE_REPORT.md`
- `scripts/quality/check_phase1_closure_docs.py`

Final Review baseline artifacts under `docs/reviews/FINAL_REVIEW.md`,
`docs/reviews/RISK_REGISTER.md`, `docs/reviews/DEFECT_BACKLOG.md`, and
`docs/reviews/GO_NO_GO.md` are required inputs for Phase 1 Closure but are not
allowed Module A edits. Any release-posture change must happen in a separately
reviewed closure PR with explicit downgrade evidence.

Changes to the three Phase 1 quality scripts above require explicit reviewer
scrutiny because the PR branch executes its own in-repo gate code.

Blocked changes:

- Phase 2 feature work
- real paid provider calls or required real provider keys
- production/multi-worker enablement
- real video export
- external avatar provider or public synthetic-media distribution
- release tag creation before all Phase 1 gates pass
