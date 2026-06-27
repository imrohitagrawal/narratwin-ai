# Codex / Agent Instructions for NarraTwin AI

You are working on NarraTwin AI as a Principal Staff AI Product Engineer.

## Non-negotiable workflow

1. Read `docs/AI_BUILD_BRIEF.md`.
2. Do not start coding until product strategy, PRD, methodology, architecture, ADRs, risk register, and first vertical-slice plan exist.
3. Build only vertical slices.
4. Use TDD for backend/provider/RAG/evaluation logic.
5. Keep all paid providers optional.
6. Treat uploaded docs as untrusted input.
7. Never commit secrets.
8. Maintain `docs/THIRD_PARTY_NOTICES.md`.

## Engineering bar

Each slice must include:

- working user-facing path
- tests
- docs update
- security notes
- observability metadata
- known limitations
- reviewer pass

## First slice

Project creation → upload markdown knowledge → ingest/chunk/store → retrieve context → generate grounded walkthrough script → evaluate unsupported claims → store output → display in UI.
