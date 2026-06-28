# Roadmap

## Roadmap principle

Build NarraTwin AI as reviewed vertical slices. Do not build a large disconnected skeleton.

Each phase must produce a working, tested, documented outcome before the next phase starts.

The roadmap must preserve two product modes while still implementing the grounding loop first:

- Mode 1: Pre-rendered multilingual demo video.
- Mode 2: Interactive AI avatar guide.

## Phase -1: Skill and repo trust setup

Outcome:

- `docs/SKILL_TRUST_REVIEW.md`
- clarified skill setup and conflict rules
- no blind vendoring
- no app code

Exit gate:

- each skill source is approved, rejected, or marked for manual review
- Codex knows which skill to use at which stage

## Phase 0: Product and planning hardening

Outcome:

- product strategy
- implementation-ready PRD
- PRD red-team review
- North Star metrics
- roadmap
- risk register
- first vertical-slice plan
- explicit validation of two product modes
- explicit validation of the project-avatar-pack contract

Exit gate:

- PRD has clear user journeys, requirements, non-goals, NFRs, risks, and acceptance criteria
- product modes and project-avatar-pack are reflected in PRD, roadmap, and architecture

## Phase 1: Architecture, security, and AI safety

Outcome:

- architecture blueprint
- ADRs
- security and privacy controls
- AI safety and evaluation gates
- third-party notices
- observability and cost plan

Exit gate:

- architecture defines components, data flow, trust boundaries, provider contracts, and evaluation flow

## Phase 2: Repo quality gates

Outcome:

- local validation commands
- GitHub Actions quality workflow alignment
- PR template
- quality-gate documentation

Exit gate:

- quality workflow is understandable
- future backend/frontend code must add CI wrapper scripts before merge

## Phase 3: Slice 1 — grounded script generation

Outcome:

```text
project creation
→ markdown/text upload
→ ingestion/chunking/storage
→ context retrieval
→ grounded walkthrough script
→ unsupported-claim evaluation
→ stored output
→ UI display
```

Exit gate:

- happy path works
- one failure/refusal path works
- tests pass without real premium provider keys
- generated output is stored and visible

## Phase 4: Translation, subtitles, and run history

Outcome:

- translated script output
- subtitle-ready format
- run history screen
- cached generation results

Exit gate:

- language consistency tests exist
- cached runs are traceable

## Phase 5: Voice generation and media disclosure

Outcome:

- TTS provider interface
- mock TTS provider first
- optional free-first TTS provider after license/terms review
- AI voice disclosure surfaced in output metadata/UI
- no voice cloning

Exit gate:

- generated audio is optional
- tests run without real provider keys
- AI-generated voice disclosure exists where audio is produced

## Phase 6: Pre-rendered multilingual demo video

Outcome:

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

Exit gate:

- video generation remains provider-agnostic
- premium providers are optional adapters
- third-party notices are updated
- output clearly discloses AI-generated media
- no face/voice cloning without explicit documented consent

## Phase 7: Interactive avatar Q&A

Outcome:

```text
user selects language, audience, depth, and style
→ user asks a project question
→ retrieval from approved project knowledge
→ grounded answer generation
→ unsupported-claim evaluation
→ future TTS/avatar response
```

Exit gate:

- Q&A cannot answer outside approved context without saying unavailable
- empty-context refusal works
- prompt-injection tests pass
- context citations/references are stored and shown

## Phase 8: Optional premium provider adapters

Outcome:

- HeyGen/Tavus/D-ID/ElevenLabs adapters if desired
- provider contract tests
- cost tracking
- failure fallback

Exit gate:

- premium provider is optional
- no core logic imports provider SDK directly

## Phase 9: Analytics and portfolio showcase

Outcome:

- language/audience/depth usage analytics
- demo completion metrics
- feedback collection
- cost and latency dashboard or report
- portfolio-ready showcase materials

Exit gate:

- analytics do not expose secrets or private uploaded content
- claims in showcase match implemented behavior

## Phase 10: Release readiness

Outcome:

- release checklist
- demo script
- known limitations
- architecture docs
- local setup docs
- portfolio-ready README

Exit gate:

- new developer can run the project
- all quality gates pass
- claims in README match implemented behavior