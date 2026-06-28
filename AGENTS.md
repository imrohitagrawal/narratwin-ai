# AGENTS.md

## Project

NarraTwin AI — AI Avatar Walkthrough Engine for Global Project Demos.

The product helps a user upload approved project knowledge and generate grounded, multilingual walkthrough scripts and avatar-demo export artifacts for recruiters, hiring managers, developers, product leaders, customers, and non-English audiences.

## Codex operating contract

Codex must work as an autonomous engineering agent, not as a random coding agent.

Codex must follow this order:

1. Read repository instructions.
2. Read the active stage from `.stage/current`.
3. Confirm the allowed scope for the stage.
4. Use only the required skills for the stage.
5. Make the smallest complete change.
6. Run the required quality gate.
7. Produce reviewable commits.
8. Open or update the stage PR.
9. Do not move to the next stage until the current stage gate passes.

## Non-negotiable rules

- No direct commits to remote `main`.
- Every stage must work through issue, branch, commit, PR, review, and merge.
- Do not start product implementation before Stage 0 and Stage 1 gates pass.
- Do not skip quality gates.
- Do not weaken tests to make a gate pass.
- Do not remove security checks to make CI pass.
- Do not commit secrets, tokens, API keys, provider keys, credentials, or private data.
- Do not require paid providers for local development, CI, or tests.
- All external services must have mock or local adapters.
- All provider keys must come from environment variables or secret managers.
- All generated scripts must cite source chunks.
- Unsupported generated claims must fail evaluation.
- Eval failures block merge.
- Critical or high security findings block merge.
- Architecture changes require ADR updates.
- PRD-impacting changes require traceability matrix updates.
- If a stage changes scope, update `docs/PHASE_PLAN.md` and `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`.
- If a tool, provider, framework, or architecture decision changes, update `docs/ADR/`.
- If a new external skill is installed or activated, update `docs/SKILL_LOCK.md`.

## Approved stage model

| Stage | Name | Main outcome |
|---|---|---|
| Stage 0 | Codex operating model and skill lock | Operating rules, skill lock, issue plan, executable quality gate |
| Stage 1 | Product strategy and PRD v1.0 | Hardened PRD, product strategy, roadmap, traceability |
| Stage 2 | Architecture, security, AI safety | Architecture, ADRs, threat model, API/data contracts |
| Stage 3 | Repo foundation and CI/CD quality gates | Backend/frontend skeleton, Docker, CI, security workflows |
| Stage 4 | Slice 1: project upload to grounded script | First vertical slice from upload to cited walkthrough script |
| Stage 5 | Evaluation, guardrails, observability | RAG evals, guardrails, tracing, cost and latency tracking |
| Stage 6 | Multilingual scripts, subtitles, voice adapter | Translation, subtitles, mock TTS, artifact output |
| Stage 7 | Avatar rendering adapter and demo export | Mock avatar renderer, render jobs, export-preview UI |
| Stage 8 | Performance, security hardening, release readiness | Perf gates, hardening, release checklist, runbook, portfolio README |
| Final Review | Independent reviewer pass | Risk register, defect backlog, go/no-go decision |

## Current stage source of truth

The file `.stage/current` controls the active stage.

Allowed values:

| Value | Meaning |
|---|---|
| 0 | Stage 0 is active |
| 1 | Stage 1 is active |
| 2 | Stage 2 is active |
| 3 | Stage 3 is active |
| 4 | Stage 4 is active |
| 5 | Stage 5 is active |
| 6 | Stage 6 is active |
| 7 | Stage 7 is active |
| 8 | Stage 8 is active |
| final | Final independent review is active |

`make quality` must run only the quality gates available up to the current stage.

## Stage scope rules

### Stage 0

Allowed: operating model, skill setup docs, skill lock, issue plan, quality gate setup, and review docs.

Not allowed: product feature implementation, backend feature work, frontend feature work, RAG implementation, avatar implementation, provider integration, or database schema work.

### Stage 1

Allowed: product strategy, PRD hardening, red-team review, roadmap, phase plan, and requirements traceability.

Not allowed: product feature implementation.

### Stage 2

Allowed: architecture, ADRs, threat model, API contract, data model, AI safety strategy, security model, privacy model, and portability strategy.

Not allowed: product feature implementation beyond contracts and architecture scaffolding.

### Stage 3

Allowed: repo foundation, backend skeleton, frontend skeleton, Docker Compose, CI workflows, security workflows, Makefile targets, and health checks.

Not allowed: full product features beyond health checks.

### Stage 4

Allowed: project creation, document upload, parsing, chunking, embeddings, retrieval, grounded script generation, citations, and UI display of generated script.

Required: mock LLM path for tests, deterministic fixtures, cited source chunks, and grounding tests.

### Stage 5

Allowed: eval runner, guardrails, unsupported-claim detection, prompt-injection test set, Langfuse adapter, OpenTelemetry traces, structured logs, and cost/latency/token tracking.

Required: eval thresholds must block merge.

### Stage 6

Allowed: translation adapter, glossary preservation, subtitle generation, voice provider interface, mock TTS, and downloadable artifacts.

Required: no hardcoded paid provider.

### Stage 7

Allowed: avatar provider interface, mock avatar renderer, render job lifecycle, export artifacts page, and demo preview UI.

Required: provider failure fallback.

### Stage 8

Allowed: performance smoke tests, latency budget checks, frontend Lighthouse checks, rate limiting, request size limits, MIME validation, dependency audit, Docker image scan, release checklist, runbook, demo seed data, portfolio README, and release-readiness review.

Required: no critical or high dependency vulnerabilities, no critical or high container vulnerabilities, and all security/eval gates pass.

### Final Review

Allowed: independent review, risk register, defect backlog, and go/no-go decision.

Not allowed: fixing issues during the review pass.

## Quality gate rule

Before any PR is considered ready, Codex must run:

```bash
make quality
```

For the active stage, Codex must also run the direct target, for example:

```bash
make stage0-quality
```

## Review rule

Each stage must produce or update review artifacts under `docs/reviews/`.

Minimum Stage 0 review files:

```text
docs/reviews/STAGE0_REVIEW.md
docs/reviews/STAGE0_DEFECT_BACKLOG.md
docs/reviews/STAGE0_GO_NO_GO.md
```

Future stages must follow the same naming pattern.

## Completion rule

A stage is complete only when:

1. Required artifacts exist.
2. Required quality gate passes.
3. Review artifact exists.
4. Defects are either fixed or explicitly accepted.
5. PR is approved.
6. Branch is merged to main.
7. Next stage branch is created from updated main.
