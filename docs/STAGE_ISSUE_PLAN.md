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
