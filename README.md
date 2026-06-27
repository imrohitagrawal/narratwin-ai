# NarraTwin AI

**NarraTwin AI** is a provider-agnostic multilingual AI avatar walkthrough platform.

It turns approved project knowledge, README files, architecture docs, demo scripts, and demo videos into audience-aware avatar walkthroughs for recruiters, hiring managers, engineers, product leaders, customers, and global non-English audiences.

## Current repository state

This repository is intentionally bootstrapped as a **strategy-first, spec-first, TDD-first** build.

Do not start by generating a large disconnected code skeleton.

Start with:

1. Product strategy
2. PRD
3. PRD red-team review
4. Methodology
5. Architecture and ADRs
6. Vertical-slice implementation plan
7. TDD implementation for Slice 1

## Product modes

### Free Engineering Mode

- Gemini API as primary LLM
- ChromaDB or pgvector for RAG
- FastAPI backend
- Next.js frontend
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

## Next step

Open `docs/AI_BUILD_BRIEF.md` and give it to Codex from a fresh repo session.
