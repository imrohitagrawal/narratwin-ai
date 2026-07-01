# NarraTwin AI

**NarraTwin AI** is a provider-agnostic multilingual AI avatar walkthrough platform.

It turns approved project knowledge, README files, architecture docs, demo scripts, and demo videos into audience-aware avatar walkthroughs for recruiters, hiring managers, engineers, product leaders, customers, and global non-English audiences.

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

The implemented local/mock Phase 1 path covers:

- project creation
- markdown/text knowledge upload
- ingest, chunk, and project-scoped retrieval
- grounded walkthrough script generation
- citation/source-reference display
- unsupported-claim evaluation
- stored output display in the UI

The current demo is local-only, single-process, process-local, and non-durable.
It does not approve production release, multi-worker deployment, real video
export, external paid/provider-backed generation, cloned identity use, or public
synthetic-media distribution.

## Local demo

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/api/v1/healthz
curl http://localhost:8000/api/v1/readyz
```

Open `http://localhost:3000` and follow
`docs/demo/PHASE_1_DEMO_SCRIPT.md`.

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

## Quality gates

On Phase 1 Closure branches, `make quality` runs the governance closure gate.
Run `make ci` for the broader local lint, typecheck, test, eval, security,
Docker, and Lighthouse wrapper suite where local tooling is available.
