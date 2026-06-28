# Stage Issue Plan

This file is the repository-side issue plan for NarraTwin AI. If GitHub issues are created, their links should be added here.

## Required issues

| Issue | Title | Stage | Purpose | Status |
|---:|---|---|---|---|
| 1 | Stage 0 — Codex operating model and skill lock | Stage 0 | Operating model, skill lock, stage issue plan, executable quality gates | Planned |
| 2 | Stage 1 — Product strategy and PRD v1.0 | Stage 1 | Product strategy, PRD hardening, roadmap, metrics, traceability | Planned |
| 3 | Stage 2 — Architecture, security, AI safety | Stage 2 | Architecture, ADRs, threat model, API/data contracts, portability | Planned |
| 4 | Stage 3 — Repo foundation and CI/CD gates | Stage 3 | Backend/frontend skeleton, Docker, CI, security workflows, Make targets | Planned |
| 5 | Stage 4 — Slice 1: project upload to grounded script | Stage 4 | Project creation, upload, RAG ingestion, grounded cited script, UI display | Planned |
| 6 | Stage 5 — Evaluation, guardrails, observability | Stage 5 | RAG evals, unsupported-claim detection, prompt-injection tests, tracing | Planned |
| 7 | Stage 6 — Multilingual scripts, subtitles, voice adapter | Stage 6 | Translation, glossary preservation, subtitle files, mock TTS, artifacts | Planned |
| 8 | Stage 7 — Avatar rendering adapter and demo export | Stage 7 | Avatar provider interface, mock renderer, render jobs, preview/export UI | Planned |
| 9 | Stage 8 — Performance, security hardening, release readiness | Stage 8 | Performance budgets, rate limits, audits, image scan, runbook, portfolio README | Planned |
| 10 | Final Review — Independent reviewer pass | Final Review | Final review, risk register, defect backlog, go/no-go decision | Planned |

## Usage rule

Every stage must be executed through its issue, branch, pull request, quality gate, and review artifact.

## Branch naming convention

| Stage | Branch pattern |
|---|---|
| Stage 0 | `stage0-operating-model-quality-gate` |
| Stage 1 | `stage1-product-strategy-prd-v1` |
| Stage 2 | `stage2-architecture-security-ai-safety` |
| Stage 3 | `stage3-repo-foundation-ci-gates` |
| Stage 4 | `stage4-upload-to-grounded-script` |
| Stage 5 | `stage5-evals-guardrails-observability` |
| Stage 6 | `stage6-multilingual-subtitles-voice` |
| Stage 7 | `stage7-avatar-rendering-export` |
| Stage 8 | `stage8-performance-security-release` |
| Final Review | `final-independent-review` |

## PR rule

A PR is ready for review only after:

- the direct stage gate passes
- `make quality` passes
- review artifacts are updated
- no blocker remains open
- scope stays inside the active stage
