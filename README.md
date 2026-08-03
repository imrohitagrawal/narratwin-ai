# NarraTwin AI

**NarraTwin AI** explores how approved product knowledge can become grounded,
cited, multilingual walkthroughs without hiding unsupported claims or
synthetic-media risk.

> **Release posture: No-Go.** This repository demonstrates an implemented
> local/mock vertical slice. It is not hosted, publicly released,
> production-ready, or connected to a real avatar, video, TTS, or paid
> generation provider.

[Run the local demo](#local-demo) ·
[Contribute](https://github.com/imrohitagrawal/.github/blob/main/CONTRIBUTING.md) ·
[Join a Discussion](https://github.com/imrohitagrawal/narratwin-ai/discussions) ·
[Report a bug](https://github.com/imrohitagrawal/narratwin-ai/issues/new)

## What works now—and what does not

The implemented local/mock path accepts approved markdown or text, builds a
project-scoped retrieval index, generates a grounded walkthrough script,
displays citations, evaluates unsupported claims, and stores the result for the
local UI.

Not implemented: interactive avatar Q&A, real avatar or video generation,
provider-backed media generation, hosted deployment, production durability,
public release, or production readiness.

All current media behavior is synthetic and local/mock. Cloned face or voice
use requires explicit documented consent and remains disabled; AI-generated
media must retain provenance and disclosure boundaries.

## Current repository state

Stage 8 and the Final Independent Reviewer Pass are merged to `main`. Phase 1
Closure is active, and the release posture remains **No-Go** until required P0/P1
closure issues are resolved or explicitly downgraded with reviewer evidence.

Current governance and delivery status is tracked in:

- `docs/STATUS.md`
- `docs/PROJECT_LEARNINGS_TRACKER.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/CODEX_OPERATING_MODEL.md`

Reusable project learnings are tracked in
`docs/PROJECT_LEARNINGS_TRACKER.md` and link to dedicated reference pages such
as `docs/REVIEW_RIGOR_RETROSPECTIVE.md` and
`docs/PROJECT_GOVERNANCE_LEARNINGS.md`. Check these before starting a new
implementation stage, opening a release-readiness PR, or using this project as a
template for a new application.

The current demo is local-only, single-process, process-local, and non-durable.

## Local demo

```bash
cp .env.example .env && docker compose up --build
```

Then, in another terminal, verify the local services:

```bash
curl http://localhost:8000/api/v1/healthz
curl http://localhost:8000/api/v1/readyz
```

Open `http://localhost:3000` and follow
`docs/demo/PHASE_1_DEMO_SCRIPT.md`.

## Planned provider modes

The entries below are architecture candidates, not current executable product
modes. The present slice uses local/mock adapters: it makes no real provider
calls and produces no real audio, avatar, or video output.

### Free/open-stack candidates

- Gemini API as an optional LLM candidate, disabled by default
- pgvector as a future RAG candidate; ChromaDB is currently removed and blocked
- FastAPI and Next.js as the current application foundations
- FFmpeg as a future media-assembly candidate, not enabled in the current slice
- Optional local avatar providers only after license review and implementation

### Premium provider candidates

Future, disabled-by-default adapter candidates include:

- HeyGen
- Tavus
- D-ID
- ElevenLabs

None of these providers is used by the current local/mock path. Any future
adapter must remain outside core business logic and pass terms, consent,
privacy, provenance, safety, and release review before use.

## First vertical slice

Project creation → upload markdown knowledge → ingest/chunk/store → retrieve context → generate grounded walkthrough script → evaluate unsupported claims → store output → display in UI → tests passing → docs updated.

## Critical quality rules

- No mandatory paid APIs.
- No secrets committed.
- No unsupported project claims.
- No non-commercial tools in external, public, or commercial paths.
- Wav2Lip must not be enabled by default.
- AI avatar/voice disclosure is mandatory.
- Cloned face/voice requires explicit documented consent.

## Quality gates

On Phase 1 Closure branches, `make quality` runs the governance closure gate.
Run `make ci` for the broader local lint, typecheck, test, eval, security,
Docker, and Lighthouse wrapper suite where local tooling is available.
