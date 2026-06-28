# Quality Gates

## Purpose

This document defines the executable quality gates for NarraTwin AI.

Quality gates are mandatory. They are not advisory. A stage is not complete until its direct quality target and `make quality` both pass.

## Commands

The repository must expose these commands:

```bash
make quality
make stage0-quality
make stage1-quality
make stage2-quality
make stage3-quality
make stage4-quality
make stage5-quality
make stage6-quality
make stage7-quality
make stage8-quality
make final-review-quality
```

## Current stage behavior

The active stage is stored in `.stage/current`.

Allowed values: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, and `final`.

`make quality` must run all gates up to the active stage.

Examples:

```text
.stage/current = 0      -> make quality runs Stage 0 gate only
.stage/current = 1      -> make quality runs Stage 0 and Stage 1 gates
.stage/current = 4      -> make quality runs Stage 0 through Stage 4 gates
.stage/current = 8      -> make quality runs Stage 0 through Stage 8 gates
.stage/current = final  -> make quality runs Stage 0 through Stage 8 plus Final Review gate
```

## Stage 0 quality gate

### Command

```bash
make stage0-quality
```

### Required files

- `AGENTS.md`
- `README.md`
- `docs/SKILLS_AND_CODEX_SETUP.md`
- `docs/SKILL_EXECUTION_PLAN.md`
- `docs/SKILL_LOCK.md`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`
- `docs/PRD.md`
- `docs/METHODOLOGY.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `.stage/current`
- `Makefile`

### Required validations

- `.stage/current` exists and is set to `0`.
- Stage 0 through Stage 8 plus Final Review are documented.
- Skill lock contains repo URL, pin or commit SHA, license status, purpose, and active stage.
- Codex operating model contains:
  - no direct commit to main
  - issue-by-issue execution
  - PR-by-PR execution
  - no product code before Stage 0 and Stage 1 gates pass
  - quality gates required for every stage
  - mock/local adapters for external services
  - no paid provider required for local/dev/test
  - eval/security failures block merge
- No product implementation code has started.
- Core operating docs contain no unresolved markers:
  - `TODO`
  - `TBD`
  - `FIXME`
  - `coming soon`
  - `lorem ipsum`

### Blocks merge if

- `make quality` is missing.
- Stage 8 is missing from operating docs.
- Final Review is missing from operating docs.
- Skill lock is incomplete.
- Product implementation starts early.
- Stage 0 review artifacts are missing when finalizing Stage 0.

## Stage 1 quality gate

### Command

```bash
make stage1-quality
```

### Required files

- `docs/PRODUCT_STRATEGY.md`
- `docs/PRD.md`
- `docs/PRD_RED_TEAM_REVIEW.md`
- `docs/NORTH_STAR_METRICS.md`
- `docs/ROADMAP.md`
- `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`
- `docs/PHASE_PLAN.md`

### Required validations

PRD must capture:

- pre-rendered multilingual demo video mode
- interactive AI avatar walkthrough mode
- project knowledge upload
- RAG ingestion
- grounded script generation
- multilingual script, voice, and subtitle flow
- avatar/lip-sync provider adapter
- evaluation gates
- security and privacy guardrails
- portfolio and recruiter use case
- free-first and premium-provider modes

### Blocks merge if

- PRD is not upgraded to v1.0.
- Acceptance criteria are missing.
- Out-of-scope is missing.
- Success metrics are missing.
- Traceability matrix is missing.
- Red-team review is missing.
- Product code starts during Stage 1.

## Stage 2 quality gate

### Command

```bash
make stage2-quality
```

### Required files

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

### Required validations

Architecture must include:

- frontend
- backend API
- ingestion worker
- RAG service
- script generation service
- evaluator service
- avatar rendering adapter
- provider abstraction
- observability pipeline
- CI quality gates

Security must include:

- secret scanning
- prompt injection controls
- file upload validation
- tenant/project isolation
- provider key isolation
- no secret logging
- rate limits
- audit logs
- dependency scanning
- OWASP baseline scan

### Blocks merge if

- Threat model is missing.
- ADRs are missing.
- API contract is missing.
- Data model is missing.
- Provider abstraction is unclear.
- AI safety strategy is missing.

## Stage 3 quality gate

### Command

```bash
make stage3-quality
```

### Required files and directories

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

### Required checks

- lint
- typecheck
- unit tests
- API tests
- frontend tests
- Playwright smoke
- secret scan
- Bandit
- dependency audit
- Semgrep
- Docker build
- eval smoke

### Blocks merge if

- CI does not run on PR.
- Health check is missing.
- Docker build fails.
- Secrets scan is missing.
- Security workflow is missing.
- Product features beyond health checks are implemented.

## Stage 4 quality gate

### Command

```bash
make stage4-quality
```

### Required flow

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

### Required checks

- unit tests for chunking
- parser tests
- upload API tests
- script generation API tests
- retrieval tests
- grounding tests
- UI smoke test
- eval smoke test
- mock LLM test path
- deterministic fixtures

### Blocks merge if

- Generated scripts do not include citations.
- Unsupported claims are allowed.
- Provider lock-in is introduced.
- Tests require paid provider keys.
- UI does not show generated script.

## Stage 5 quality gate

### Command

```bash
make stage5-quality
```

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
- `docs/EVAL_REPORT.md`

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

### Blocks merge if

- Evals do not block CI.
- Unsupported-claim detector is missing.
- Prompt-injection tests are missing.
- Tracing is missing.
- Logs expose secrets or provider keys.
- Eval report is missing.

## Stage 6 quality gate

### Command

```bash
make stage6-quality
```

### Required capabilities

- source English script
- target language selection
- translation adapter
- glossary and project-term preservation
- subtitle generation
- voice provider interface
- mock TTS provider
- downloadable script/subtitle artifacts

### Required checks

- translation preserves product terms
- subtitle file format is valid
- unsupported language returns clean error
- provider fallback works
- artifact metadata is stored

### Blocks merge if

- Translation breaks product terminology.
- Subtitle format is invalid.
- TTS is hardcoded to one paid vendor.
- Fallback path is missing.
- Generated artifacts are not downloadable.

## Stage 7 quality gate

### Command

```bash
make stage7-quality
```

### Required capabilities

- avatar provider interface
- mock avatar renderer
- provider config model
- render job status
- video export path
- UI demo preview
- export artifacts page
- provider failure fallback

### Required checks

- render job lifecycle tests
- failed provider fallback tests
- artifact metadata tests
- UI preview smoke test
- provider interface documentation

### Blocks merge if

- Avatar provider is hardcoded.
- Mock renderer is missing.
- Render job lifecycle is not testable.
- Provider failure crashes the app.
- UI cannot preview/export artifacts.

## Stage 8 quality gate

### Command

```bash
make stage8-quality
```

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

### Blocks merge if

- Performance budgets are missing.
- Rate limiting is missing.
- Upload limits are missing.
- High or critical vulnerabilities exist.
- Release checklist is incomplete.
- Runbook is missing.
- Portfolio README is weak.
- Demo seed data is missing.

## Final review quality gate

### Command

```bash
make final-review-quality
```

### Required files

- `docs/reviews/FINAL_REVIEW.md`
- `docs/reviews/RISK_REGISTER.md`
- `docs/reviews/DEFECT_BACKLOG.md`
- `docs/reviews/GO_NO_GO.md`

### Blocks release if

- Final review is missing.
- Risk register is missing.
- Defect backlog is missing.
- Go/no-go decision is missing.
- Critical unresolved defects exist without explicit acceptance.

## Stage completion checklist

A stage is complete only when:

- direct stage quality target passes
- `make quality` passes
- review document exists
- defect backlog is updated
- no blocker remains open
- PR is approved
- branch is merged into main
