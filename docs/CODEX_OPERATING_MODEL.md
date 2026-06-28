# Codex Operating Model

## Purpose

This document defines how Codex must build NarraTwin AI.

It exists to prevent random coding, uncontrolled scope expansion, skipped quality gates, and undocumented architectural drift.

## Product

NarraTwin AI is an AI Avatar Walkthrough Engine for Global Project Demos.

It supports two product modes:

1. Pre-rendered multilingual demo video.
2. Interactive AI avatar walkthrough.

The MVP path is:

```text
project creation
→ knowledge upload
→ RAG ingestion
→ grounded script generation
→ multilingual output
→ avatar/demo export path
```

## Current repository state

The initial repository documents are seed documents. The existing PRD before Stage 1 is not final; it is a v0.1 seed that must be hardened in Stage 1 using PM and spec-driven skills.

## Operating principles

- Build stage-by-stage.
- Work issue-by-issue.
- Work PR-by-PR.
- Do not commit directly to remote main.
- Do not start a later stage before the current stage quality gate passes.
- Do not implement product code before Stage 0 and Stage 1 gates pass.
- Do not introduce paid-provider dependency into local development or CI.
- Use provider adapters for LLM, voice, avatar, storage, and observability integrations.
- Keep mock/local adapters for all external providers.
- Treat evaluation, security, observability, and release readiness as product requirements, not optional cleanup.

## Stage source of truth

The active stage is controlled by `.stage/current`.

Allowed values: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, and `final`.

`make quality` must inspect `.stage/current` and run only the gates available up to that stage.

## Stage map

| Stage | Name | Purpose | Output |
|---|---|---|---|
| Stage 0 | Codex operating model and skill lock | Establish repo operating contract, skills, issues, and quality gate | Skill lock, operating docs, issue plan, Stage 0 quality gate |
| Stage 1 | Product strategy and PRD v1.0 | Harden product definition before coding | PRD v1.0, product strategy, roadmap, traceability |
| Stage 2 | Architecture, security, AI safety | Define system design and risk controls | Architecture v1.0, ADRs, threat model, API/data contracts |
| Stage 3 | Repo foundation and CI/CD gates | Create executable app shell and CI gates | FastAPI/React skeleton, Docker, GitHub Actions, Make targets |
| Stage 4 | Slice 1: project upload to grounded script | Build first usable vertical slice | Upload, parse, chunk, retrieve, generate cited script, show in UI |
| Stage 5 | Evaluation, guardrails, observability | Add AI quality and production visibility | RAG evals, guardrails, tracing, eval report |
| Stage 6 | Multilingual scripts, subtitles, voice adapter | Add multilingual output and voice abstraction | Translation, subtitles, mock TTS, downloadable artifacts |
| Stage 7 | Avatar rendering adapter and demo export | Add avatar rendering workflow | Mock avatar renderer, render jobs, preview/export UI |
| Stage 8 | Performance, security hardening, release readiness | Prepare MVP for portfolio-quality release | Perf gates, hardening, runbook, release review, portfolio README |
| Final Review | Independent reviewer pass | Perform non-coding review | Final review, risk register, defect backlog, go/no-go |

## Stage 0 contract

### Goal

Create the operating model and prevent uncontrolled work.

### Required artifacts

- `AGENTS.md`
- `docs/SKILLS_AND_CODEX_SETUP.md`
- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/SKILL_LOCK.md`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`
- `.stage/current`
- `Makefile`
- `scripts/quality/`
- GitHub issue plan for Stage 0 through Stage 8 plus Final Review

### Gate

```bash
make stage0-quality
make quality
```

### Exit criteria

- Skill lock exists.
- Operating model exists.
- Stage 0 through Stage 8 and Final Review are documented.
- Quality gates exist from Stage 0.
- No product code has started.

## Stage 1 contract

### Goal

Harden product strategy and PRD.

### Required artifacts

- `docs/PRODUCT_STRATEGY.md`
- `docs/PRD.md`
- `docs/PRD_RED_TEAM_REVIEW.md`
- `docs/NORTH_STAR_METRICS.md`
- `docs/ROADMAP.md`
- `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `docs/PHASE_PLAN.md`

### Gate

```bash
make stage1-quality
make quality
```

### Exit criteria

- PRD upgraded to v1.0.
- Product modes are clearly defined.
- Acceptance criteria exist.
- Out-of-scope exists.
- Roadmap exists.
- Traceability matrix exists.
- Red-team review exists.
- No product code has started.

## Stage 2 contract

### Goal

Harden architecture, security, privacy, AI safety, and portability.

### Required artifacts

- `docs/ARCHITECTURE.md`
- `docs/ADR/0001-system-architecture.md`
- `docs/ADR/0002-rag-storage.md`
- `docs/ADR/0003-llm-provider-routing.md`
- `docs/ADR/0004-avatar-provider-adapter.md`
- `docs/ADR/0005-observability-and-evals.md`
- `docs/THREAT_MODEL.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/PORTABILITY_STRATEGY.md`
- `docs/API_CONTRACT.md`
- `docs/DATA_MODEL.md`

### Gate

```bash
make stage2-quality
make quality
```

### Exit criteria

- Architecture is complete enough for implementation.
- Security controls are explicit.
- AI safety controls are explicit.
- API and data contracts are defined.
- ADRs exist for major decisions.

## Stage 3 contract

### Goal

Create executable repo foundation and CI/CD hard gates.

### Required artifacts

- backend FastAPI skeleton
- frontend React/Vite skeleton
- `docker-compose.yml`
- `pyproject.toml`
- frontend `package.json`
- `.env.example`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
- `.github/workflows/eval-smoke.yml`
- updated `Makefile`

### Gate

```bash
make stage3-quality
make quality
```

### Exit criteria

- App shell runs.
- Health checks pass.
- CI blocks PRs.
- Security workflow exists.
- Docker build passes.
- No real product features beyond health checks.

## Stage 4 contract

### Goal

Build first vertical slice.

### Scope

```text
create project
→ upload docs
→ parse docs
→ chunk content
→ generate embeddings
→ store chunks
→ retrieve relevant context
→ generate grounded walkthrough script
→ return script with citations
→ show result in UI
```

### Gate

```bash
make stage4-quality
make quality
```

### Exit criteria

- Script generation is grounded.
- Citations are present.
- Unsupported claims fail.
- Mock LLM works in tests.
- UI shows generated script.

## Stage 5 contract

### Goal

Add AI evaluation, guardrails, and observability.

### Required capabilities

- RAG eval runner
- script faithfulness evaluator
- unsupported-claim detector
- prompt-injection test set
- file-upload abuse tests
- Langfuse tracing adapter
- OpenTelemetry traces
- structured logs
- cost, latency, token tracking
- generated eval report

### Gate

```bash
make stage5-quality
make quality
```

### Required thresholds

```text
faithfulness >= 0.85
answer relevancy >= 0.80
context precision >= 0.75
context recall >= 0.70
unsupported claims = 0 for golden tests
critical security findings = 0
secret scan findings = 0
```

## Stage 6 contract

### Goal

Add multilingual script, subtitle, and voice-provider abstraction.

### Required capabilities

- English source script
- target language selection
- translation adapter
- glossary preservation
- subtitle generation
- voice provider interface
- mock TTS provider
- downloadable script/subtitle artifacts

### Gate

```bash
make stage6-quality
make quality
```

### Exit criteria

- Product terms are preserved.
- Subtitle format is valid.
- Unsupported languages fail cleanly.
- No paid TTS provider is required.

## Stage 7 contract

### Goal

Add avatar rendering adapter and demo export path.

### Required capabilities

- avatar provider interface
- mock avatar renderer
- provider config model
- render job status
- video export path
- demo preview UI
- export artifacts page
- provider failure fallback

### Gate

```bash
make stage7-quality
make quality
```

### Exit criteria

- Render job lifecycle is tested.
- Provider fallback is tested.
- UI preview works.
- No paid avatar provider is required.

## Stage 8 contract

### Goal

Perform performance, security hardening, and release readiness.

### Required capabilities

- performance smoke tests
- API latency budget checks
- frontend Lighthouse checks
- rate limiting
- request size limits
- upload MIME validation
- dependency audit
- Docker image scan
- release checklist
- runbook
- demo seed data
- portfolio README
- `docs/RELEASE_READINESS_REVIEW.md`

### Gate

```bash
make stage8-quality
make quality
```

### Required budgets

```text
health endpoint < 200 ms local
mocked script generation path < 2 sec
upload limit enforced
no critical/high dependency vulnerabilities
no critical/high container vulnerabilities
all eval gates pass
all security gates pass
```

### Exit criteria

- Release checklist exists.
- Runbook exists.
- Portfolio README is ready.
- Demo data exists.
- Security and eval gates pass.
- Performance budgets pass.

## Final independent review contract

### Goal

Review the full repo without fixing issues.

### Required artifacts

- `docs/reviews/FINAL_REVIEW.md`
- `docs/reviews/RISK_REGISTER.md`
- `docs/reviews/DEFECT_BACKLOG.md`
- `docs/reviews/GO_NO_GO.md`

### Gate

```bash
make final-review-quality
```

### Exit criteria

- Final review exists.
- Risks are classified.
- Defects are listed.
- Go/no-go decision is recorded.

## Parallelism policy

| Stage | Max Codex sessions |
|---|---:|
| Stage 0 | 1 |
| Stage 1 | 1 |
| Stage 2 | 2 |
| Stage 3 | 2 |
| Stage 4 | 3 |
| Stage 5 | 2 |
| Stage 6 | 2 |
| Stage 7 | 2 |
| Stage 8 | 2 |
| Final Review | 1 |

Rules:

- Never run more than 3 sessions at once.
- Never parallelize PRD decisions.
- Never parallelize architecture contract finalization.
- Never parallelize final review.
- Parallelize only after contracts are stable.

## Human setup that cannot be fully automated

The user must perform or approve:

- connecting Codex to GitHub
- granting repo access
- adding real API keys as secrets
- approving paid provider accounts if used later
- configuring custom domain if required

Everything else should be Codex-driven.
