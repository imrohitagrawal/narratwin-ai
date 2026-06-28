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
9. Never commit directly to `main`.
10. Start every stage from a GitHub issue.
11. Use a dedicated branch for every issue/stage.
12. Open a pull request linked with `Closes #<issue-number>`.
13. Do not merge until CI passes.
14. Update `docs/ADR/` for architecture-impacting changes.
15. Update `docs/TRACEABILITY.md` for PRD-impacting changes.

## Repository guardrails

Before changing files, read:

- `docs/REPOSITORY_GUARDRAILS.md`
- `.github/pull_request_template.md`
- `scripts/guardrails_check.py`

The repository quality workflow enforces least-privilege CI, issue-linked PRs, secret checks, mock/local provider defaults, eval blocking, security blocking, source-citation expectations, LLM tracing expectations, ADR updates, and PRD traceability updates.

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
