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
- `Makefile`
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
- `tests/api/test_health_api.py`
- `tests/api/test_stage8_hardening_api.py`
- `tests/unit/test_health_contract.py`
- `tests/unit/test_stage6_multilingual.py`
- `demo/stage8_seed_project.md`
- `docs/ADR/0006-stage8-release-hardening.md`
- `docs/API_CONTRACT.md`
- `docs/QUALITY_GATES.md`
- `docs/RECOMMENDED_REVIEW_ITEMS.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/RELEASE_READINESS_REVIEW.md`
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
