# NarraTwin AI

**NarraTwin AI** is a provider-agnostic multilingual AI avatar walkthrough platform.

It turns approved project knowledge, README files, architecture docs, demo scripts, and demo videos into audience-aware avatar walkthroughs for recruiters, hiring managers, engineers, product leaders, customers, and global non-English audiences.

## Current repository state

This repository is intentionally bootstrapped as a **strategy-first, spec-first, TDD-first** build.

Do not start by generating a large disconnected code skeleton.

The repo is currently operating under the Stage 0 to Stage 8 model documented in:

- `AGENTS.md`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`

## Active stage

The active stage is controlled by:

```text
.stage/current
```

Current value:

```text
0
```

This means Stage 0 is active.

## Quality gates

Run the current stage quality gate:

```bash
make stage0-quality
```

Run all gates available up to the active stage:

```bash
make quality
```

During Stage 0, `make quality` runs only Stage 0 checks. It must not require backend, frontend, Docker, database, RAG, avatar, or provider implementation code.

Future stages are declared in the Makefile so Codex cannot claim the quality targets are missing. Their executable checks must be implemented when each stage becomes active.

## Approved build stages

| Stage | Name |
|---|---|
| Stage 0 | Codex operating model and skill lock |
| Stage 1 | Product strategy and PRD v1.0 |
| Stage 2 | Architecture, security, AI safety |
| Stage 3 | Repo foundation and CI/CD quality gates |
| Stage 4 | Slice 1: project upload to grounded script |
| Stage 5 | Evaluation, guardrails, observability |
| Stage 6 | Multilingual scripts, subtitles, voice adapter |
| Stage 7 | Avatar rendering adapter and demo export |
| Stage 8 | Performance, security hardening, release readiness |
| Final Review | Independent reviewer pass |

## Product modes

### Free Engineering Mode

- Gemini API as primary LLM option
- ChromaDB or pgvector for RAG
- FastAPI backend
- React/Vite or Next.js frontend, depending on the Stage 3 architecture decision
- FFmpeg for subtitles/video assembly
- Mock avatar provider first
- Optional local avatar provider only after license review

### Premium Showcase Mode

Optional provider adapters for:

- HeyGen
- Tavus
- D-ID
- ElevenLabs

Premium providers must not be hardcoded into core business logic.

## First vertical slice

Project creation → upload markdown knowledge → ingest/chunk/store → retrieve context → generate grounded walkthrough script → evaluate unsupported claims → store output → display in UI → tests passing → docs updated.

## Critical quality rules

- No mandatory paid APIs.
- No secrets committed.
- No unsupported project claims.
- No non-commercial tools in public/portfolio/commercial paths.
- Wav2Lip must not be enabled by default.
- AI avatar/voice disclosure is mandatory.
- Cloned face/voice requires explicit documented consent.
- `make quality` must pass before any PR is considered ready.
- Stage 8 and Final Review must remain part of the operating model.

## Next step

Complete Stage 0 remediation and review before starting Stage 1. Do not implement product features until Stage 0 and Stage 1 gates pass.
