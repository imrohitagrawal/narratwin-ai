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

| Stage | Issue title | Branch pattern | Local quality target | PR requirement | Exit artifact |
|---|---|---|---|---|---|
| Stage 0 | Stage 0 - Codex operating model and skill lock | `stage0-*` | `make stage0-quality` | Linked PR to `main` | Operating model, skill lock, stage issue plan, Stage 0 quality gate |
| Stage 1 | Stage 1 - Product strategy and PRD v1.0 | `stage1-*` | `make stage1-quality` | Linked PR to `main` | Product strategy, PRD v1.0, red-team review, metrics, roadmap |
| Stage 2 | Stage 2 - Architecture, security, AI safety | `stage2-*` | `make stage2-quality` | Linked PR to `main` | Architecture, ADRs, security/privacy, AI safety/evaluation |
| Stage 3 | Stage 3 - Repo foundation and CI/CD quality gates | `stage3-*` | `make stage3-quality` | Linked PR to `main` | Local development docs, CI wrappers, executable quality gates |
| Stage 4 | Stage 4 - Project upload to grounded script generation | `stage4-*` | `make stage4-quality` | Linked PR to `main` | First vertical slice with tests, docs, security notes, observability metadata |
| Stage 5 | Stage 5 - Evaluations, guardrails, observability | `stage5-*` | `make stage5-quality` | Linked PR to `main` | Blocking evals, guardrails, trace/run metadata, observability |
| Stage 6 | Stage 6 - Multilingual scripts, subtitles, voice adapter | `stage6-*` | `make stage6-quality` | Linked PR to `main` | Multilingual script path, subtitles, mock/local voice adapter |
| Stage 7 | Stage 7 - Avatar rendering adapter and export | `stage7-*` | `make stage7-quality` | Linked PR to `main` | Mock/local avatar renderer, export artifacts, provider contract tests |
| Stage 8 | Stage 8 - Performance, security hardening, release readiness | `stage8-*` | `make stage8-quality` | Linked PR to `main` | Performance evidence, security hardening, release-readiness report |
| Final Review | Final Review - Independent review | `final-review-*` | `make final-review-quality` | Linked PR to `main` | Independent review report and release decision |

## Stage 0 Scope For This Branch

Current branch:

```text
stage0-redo-operating-model-quality-gate
```

Allowed changes:

- `AGENTS.md`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`
- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/SKILL_LOCK.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `.stage/current`
- `Makefile`
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
