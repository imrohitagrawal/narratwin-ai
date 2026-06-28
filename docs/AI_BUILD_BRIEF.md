# AI Build Brief: NarraTwin AI

You are acting as a Principal Staff AI Product Engineer, AI Platform Architect, Product Strategist, and Enterprise Software Reviewer.

## Product name

NarraTwin AI

## Product definition

NarraTwin AI is a standalone multilingual AI avatar walkthrough platform. It turns approved project knowledge, README files, architecture docs, demo scripts, and demo videos into audience-aware avatar walkthroughs for recruiters, hiring managers, engineers, product leaders, customers, and global non-English audiences.

## Product modes to preserve

The repo is currently a seed operating model. PM/spec skills must preserve and harden these two product modes before coding starts.

### Mode 1: Pre-rendered multilingual demo video

Future product flow:

```text
English demo video or demo script
→ transcription / script cleanup
→ audience-specific script generation
→ translation / localization
→ voiceover generation
→ avatar or video rendering
→ subtitles
→ export/shareable demo
```

This mode is useful for LinkedIn, YouTube, portfolio pages, recruiter sharing, product onboarding, and customer education.

### Mode 2: Interactive AI avatar guide

Future product flow:

```text
User selects language, audience, depth, and style
→ user asks a project question
→ system retrieves approved project context
→ system generates a grounded answer
→ system evaluates unsupported claims
→ future TTS/avatar provider speaks the answer
```

This mode is useful for recruiters, hiring managers, engineers, product leaders, customers, and global users who want a personalized explanation.

## Reusable project-avatar-pack

NarraTwin AI should support the reusable project knowledge contract documented in:

```text
docs/PROJECT_AVATAR_PACK.md
```

The project-avatar-pack is the approved source-of-truth folder for future generated scripts, video walkthroughs, and interactive Q&A. PM/spec skills must validate that PRD, roadmap, architecture, and Slice 1 planning do not lose this reusable-pack concept.

## Product capabilities

The product must support:

- multilingual walkthroughs
- audience-aware explanations
- project-specific RAG
- script generation
- translation/localization
- subtitles
- text-to-speech
- avatar video generation
- interactive Q&A
- free engineering mode
- optional premium provider mode
- provider-agnostic architecture
- AI evaluation
- observability
- cost tracking
- security and privacy controls

## Mandatory methodology

Do not start coding immediately.

Use this methodology:

1. Product discovery
2. Product strategy
3. PRD creation
4. PRD red-team review
5. North Star metric and supporting metrics
6. Spec-driven development
7. Architecture and ADRs
8. Vertical-slice implementation planning
9. TDD-driven execution
10. AI evaluation-driven quality gates
11. Security-by-design
12. Observability and cost-control from day one
13. Release-readiness review

## Skills to use before coding

Use installed PM/spec/engineering skills where available:

- `phuryn/pm-skills` for discovery, strategy, PRD, red-team PRD, user stories, test scenarios, North Star metric, roadmap, AI shipping review.
- GitHub Spec Kit or equivalent for constitution, specs, plan, tasks, and implementation control.
- `addyosmani/agent-skills` for spec discipline, planning, incremental build, testing, code review, security review, and shipping checklist.
- TDD skill or workflow for red-green-refactor.
- Security hardening skill for uploads, prompt injection, secrets, provider risk, and license checks.

## Documents to create before coding

Create these before application implementation:

- `docs/PRODUCT_STRATEGY.md`
- `docs/PRD.md`
- `docs/PRD_RED_TEAM_REVIEW.md`
- `docs/NORTH_STAR_METRICS.md`
- `docs/METHODOLOGY.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT_AVATAR_PACK.md`
- `docs/ADR/0001-architecture-approach.md`
- `docs/ADR/0002-provider-agnostic-adapters.md`
- `docs/ADR/0003-free-mode-vs-premium-mode.md`
- `docs/SECURITY_AND_PRIVACY.md`
- `docs/AI_SAFETY_AND_EVALUATION.md`
- `docs/OBSERVABILITY_AND_COST.md`
- `docs/ROADMAP.md`
- `docs/RELEASE_QUALITY_BAR.md`
- `docs/THIRD_PARTY_NOTICES.md`

## Required architecture

Use provider-agnostic interfaces:

- `LLMProvider`
- `EmbeddingProvider`
- `TranslationProvider`
- `TTSProvider`
- `STTProvider`
- `AvatarProvider`
- `SubtitleProvider`
- `VideoRenderer`
- `StorageProvider`
- `EvaluationProvider`
- `ObservabilityProvider`

## Default free-first stack

- Gemini API for LLM, translation, evaluation, and optionally embeddings/TTS
- FastAPI backend
- Next.js + TypeScript frontend
- ChromaDB local vector store
- local filesystem storage first
- FFmpeg for subtitles/video assembly
- mock avatar provider first
- optional SadTalker local provider only after license review

## Optional premium adapters

- HeyGen
- Tavus
- D-ID
- ElevenLabs

## Critical license rule

Do not use non-commercial or research-only tools in public, recruiter-facing, portfolio, or commercial workflows.

Wav2Lip must not be enabled by default because its usage restrictions can create public/commercial-use risk.

Every third-party package, model, media asset, avatar tool, dataset, or generated sample must be documented in `docs/THIRD_PARTY_NOTICES.md`.

## Security rules

- no secrets committed
- use `.env` and `.env.example`
- validate uploads
- sanitize filenames
- restrict file types
- treat uploaded docs as untrusted input
- defend against prompt injection
- do not allow generated outputs to claim facts not present in approved project knowledge
- add AI-generated avatar/voice disclosure
- require consent for any cloned face or voice feature

## First vertical slice

Implement only after documents are created and reviewed:

Project creation → upload markdown project knowledge → ingest/chunk/store knowledge → retrieve relevant context → generate grounded walkthrough script → evaluate unsupported claims → store output → display output in UI → tests passing → docs updated.

Slice 1 must preserve the future two-mode product vision but must not implement avatar video, TTS, subtitles, premium provider adapters, or interactive avatar Q&A.

## Completion checkpoint before coding

After creating the documents, pause and provide:

1. Product strategy summary
2. PRD summary
3. Methodology summary
4. Proposed vertical slices
5. Risk register
6. Recommended first implementation slice
7. Files created
8. Open questions or assumptions