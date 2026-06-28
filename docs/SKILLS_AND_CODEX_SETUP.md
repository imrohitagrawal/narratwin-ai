# Skills and Codex Setup

This file is the quick-start summary. The authoritative operating plan is `docs/SKILL_EXECUTION_PLAN.md`, the lock file is `docs/SKILL_LOCK.md`, and the active-stage contract is `docs/CODEX_OPERATING_MODEL.md`.

Do not install skills from this file alone. First confirm the skill source, license, install command, execution behavior, and activation stage.

## Operating rule

Install or activate only the skill needed for the current stage. Do not install every skill at once.

## Approved stage order

| Stage | Install/use | Purpose | Stop condition |
|---|---|---|---|
| Stage 0 | PM/spec planning skills only, after trust review | Codex operating model, skill execution plan, skill lock, GitHub issue plan, quality gates | `make stage0-quality` and `make quality` pass |
| Stage 1 | PM skills, Spec Kit, spec-driven planning | Product strategy, PRD v1.0, roadmap, metrics, PRD red-team review, traceability | PRD v1.0 and traceability are complete; no product code |
| Stage 2 | Architecture, security, AI safety, ADR skills | Architecture v1.0, ADRs, threat model, API/data contracts, portability strategy | Architecture/security/AI safety contracts are approved |
| Stage 3 | CI/CD, TDD, security-hardening skills | Repo foundation, backend/frontend skeleton, Docker, CI, local Make targets | CI and local gates pass; only health checks implemented |
| Stage 4 | TDD, RAG testing, code-review skills | Slice 1: project upload to grounded script with citations and UI display | Slice 1 works through mocks/local providers and tests pass |
| Stage 5 | Eval, guardrail, observability, security skills | RAG evals, unsupported-claim detection, prompt-injection tests, tracing, cost tracking | Eval/security thresholds block merge and pass |
| Stage 6 | TDD, provider-adapter, artifact-generation skills | Multilingual scripts, subtitles, voice adapter, mock TTS, downloadable artifacts | Translation/subtitle/provider fallback tests pass |
| Stage 7 | UI/UX, frontend, provider-adapter, performance skills | Avatar rendering adapter, mock renderer, render jobs, preview/export UI | Render lifecycle and provider fallback tests pass |
| Stage 8 | Performance, security hardening, shipping/release skills | Performance budgets, rate limits, audits, image scan, runbook, release review, portfolio README | Release readiness review passes with no critical/high blockers |
| Final Review | Independent reviewer, security auditor, test engineer | Non-coding review, risk register, defect backlog, go/no-go | Go/no-go decision is recorded |

## Recommended skill families

1. PM Skills: product discovery, product strategy, PRD, roadmap, metrics, red-team PRD.
2. GitHub Spec Kit or equivalent: constitution, spec, plan, tasks, and implementation control.
3. Addy Osmani Agent Skills: plan-build-test-review-ship lifecycle.
4. Agent Skills standard: portable skill-folder structure and skill metadata discipline.
5. Wednesday AI agent skills: repo-aware codebase mapping after meaningful code exists.
6. UI/UX Pro Max: frontend and demo-preview polish after functional UI exists.
7. TDD workflow: red-green-refactor for backend, provider, RAG, and evaluation logic.
8. Security hardening: uploads, secrets, LLM prompt injection, provider risk, and license checks.
9. Python testing patterns: FastAPI, provider mocks, RAG tests, pytest fixtures.
10. Webapp/E2E testing: UI smoke, accessibility, Playwright flows.
11. Project documentation skills: README, runbooks, architecture docs, handoff docs.
12. Performance and shipping skills: release readiness, perf budgets, deployment hygiene.

## Stage-specific activation guidance

### Stage 0

Use skills only for operating-model and planning artifacts. Do not create product implementation code.

Required outputs:

- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/SKILL_LOCK.md`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`
- `.stage/current`
- stage-wise Make targets

### Stage 1

Use PM and spec skills to upgrade the seed PRD to v1.0.

Required outputs:

- `docs/PRODUCT_STRATEGY.md`
- `docs/PRD.md`
- `docs/PRD_RED_TEAM_REVIEW.md`
- `docs/NORTH_STAR_METRICS.md`
- `docs/ROADMAP.md`
- `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `docs/PHASE_PLAN.md`

### Stage 2

Use architecture, security, AI safety, and ADR skills.

Required outputs:

- `docs/ARCHITECTURE.md`
- `docs/ADR/`
- `docs/THREAT_MODEL.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`

### Stage 3

Use repo foundation, CI/CD, and security-hardening skills.

Required outputs:

- backend and frontend skeletons
- Docker Compose
- CI/security/eval workflows
- Make targets
- health checks

### Stage 4

Use TDD, RAG, grounding, and UI smoke-test skills for the first vertical slice.

### Stage 5

Use evaluation, guardrail, observability, prompt-injection, and security skills.

### Stage 6

Use translation, subtitle, voice-adapter, artifact, and fallback-test skills.

### Stage 7

Use avatar-adapter, UI preview, export, fallback, and performance-aware frontend skills.

### Stage 8

Use performance, security hardening, dependency audit, Docker image scan, runbook, release, and portfolio-readiness skills.

### Final Review

Use independent reviewer skills only. Do not fix issues in the final review pass.

## Conflict rule

If two skills disagree, apply this order:

1. Security, privacy, consent, and license constraints.
2. PRD acceptance criteria.
3. ADR decisions.
4. Quality gates.
5. Vertical-slice scope.
6. Skill suggestions.

If a skill proposes work outside the active stage, reject that work and record the reason in the stage review artifact.
