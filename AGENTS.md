# Codex / Agent Instructions for NarraTwin AI

You are working on NarraTwin AI as a Principal Staff AI Product Engineer.

## Required Reading

Before changing files, read:

- `docs/AI_BUILD_BRIEF.md`
- `docs/STATUS.md`
- `docs/REPOSITORY_GUARDRAILS.md`
- `.github/pull_request_template.md`
- `scripts/guardrails_check.py`
- `docs/CODEX_OPERATING_MODEL.md`
- `docs/QUALITY_GATES.md`
- `docs/SKILL_LOCK.md`
- `docs/STAGE_ISSUE_PLAN.md`

## Non-Negotiable Workflow

1. Never commit directly to `main`.
2. Every stage must start from a GitHub issue.
3. Every stage must use a dedicated branch.
4. Every stage must be reviewed through a pull request linked to the issue.
5. Do not merge until CI and the local stage quality target pass.
6. Do not start product implementation until Stage 0 and Stage 1 gates pass.
7. Do not implement backend, frontend, RAG, avatar, provider, Docker, database, or runtime product code in Stage 0.
8. Build only approved vertical slices after the gates allow implementation.
9. Use TDD for backend, provider, RAG, and evaluation logic when those stages begin.
10. Keep all paid providers optional and disabled for local/dev/test.
11. Treat uploaded docs, prompts, transcripts, and provider outputs as untrusted input.
12. Never commit secrets, credentials, tokens, private certificates, or real provider keys.
13. Maintain `docs/THIRD_PARTY_NOTICES.md` for third-party packages, tools, skills, models, APIs, datasets, providers, media assets, and generated samples.
14. Update `docs/ADR/` for architecture-impacting changes.
15. Update `docs/TRACEABILITY.md` for PRD-impacting changes.
16. Update `docs/STATUS.md` when stage state, issue ownership, PR status, or governance progress changes.

## Approved Build Stages

| Stage | Name | Product implementation allowed? |
|---|---|---:|
| Stage 0 | Codex operating model and skill lock | No |
| Stage 1 | Product strategy and PRD v1.0 | No |
| Stage 2 | Architecture, security, AI safety | No |
| Stage 3 | Repo foundation and CI/CD quality gates | No product feature code |
| Stage 4 | Project upload to grounded script generation | Yes, first vertical slice only |
| Stage 5 | Evaluations, guardrails, observability | Yes, slice-scoped |
| Stage 6 | Multilingual scripts, subtitles, voice adapter | Yes, slice-scoped |
| Stage 7 | Avatar rendering adapter and export | Yes, slice-scoped |
| Stage 8 | Performance, security hardening, release readiness | Yes, hardening only |
| Final Review | Independent release review | No new feature implementation |

## Quality Commands

Run the stage gate before committing:

```bash
make quality
```

During Stage 0, `make quality` must run only Stage 0 checks. Future stage targets exist but must fail loudly until implemented for that stage.

## Engineering Bar For Implementation Stages

Each implementation slice must include:

- working user-facing path
- tests
- docs update
- security notes
- observability metadata
- known limitations
- reviewer pass

## First Implementation Slice

Stage 4 is the first product implementation stage:

Project creation -> upload markdown knowledge -> ingest/chunk/store -> retrieve context -> generate grounded walkthrough script -> evaluate unsupported claims -> store output -> display in UI.
