# Roadmap

## Roadmap principle

Build NarraTwin AI as reviewed vertical slices. Do not build a large disconnected skeleton.

Each phase must produce a working, tested, documented outcome before the next phase starts.

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

Exit gate:

- PRD has clear user journeys, requirements, non-goals, NFRs, risks, and acceptance criteria

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

## Phase 5: Mock avatar/video output

Outcome:

- mock avatar provider
- AI disclosure
- FFmpeg-based placeholder video or subtitle assembly after license review

Exit gate:

- no face/voice cloning
- third-party notices updated
- output clearly discloses AI-generated media

## Phase 6: Interactive Q&A

Outcome:

- Q&A over approved project knowledge
- empty-context refusal
- prompt-injection tests
- context citations/references

Exit gate:

- Q&A cannot answer outside approved context without saying unavailable

## Phase 7: Optional premium provider adapters

Outcome:

- HeyGen/Tavus/D-ID/ElevenLabs adapters if desired
- provider contract tests
- cost tracking
- failure fallback

Exit gate:

- premium provider is optional
- no core logic imports provider SDK directly

## Phase 8: Release readiness and showcase

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
