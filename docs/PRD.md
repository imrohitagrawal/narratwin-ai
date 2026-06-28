# PRD: NarraTwin AI

## Product summary

NarraTwin AI is a provider-agnostic multilingual AI avatar walkthrough platform.

It turns approved project knowledge into audience-aware walkthrough scripts, subtitles, voice/video-ready outputs, and later interactive Q&A.

## Problem

Project creators often explain technical work using English-only README files, long architecture docs, or raw demo videos. Recruiters, hiring managers, engineers, product leaders, customers, and non-English audiences need different levels of explanation.

Without a grounded walkthrough system, project demos become:

- too technical for recruiters
- too shallow for engineering reviewers
- too long for hiring managers
- too English-centric for global audiences
- too easy for AI tools to hallucinate unsupported claims

## Goal

Create a platform that transforms approved project knowledge into grounded, multilingual, audience-aware walkthroughs that can later be rendered through avatar, voice, subtitle, and video providers.

## MVP scope

The MVP proves the core trust loop, not avatar polish.

Included:

- create/select project
- upload markdown/text project knowledge
- validate file type, filename, and size
- ingest/chunk/store project knowledge
- retrieve relevant context
- select audience, language, depth, and style
- generate grounded walkthrough script
- evaluate unsupported claims
- store generated output and evaluation metadata
- display result in UI
- run tests without real paid provider keys

## Non-goals for MVP

- full realtime avatar conversation
- paid provider dependency
- voice cloning
- face cloning
- production-grade video rendering quality
- commercial avatar marketplace
- automatic LinkedIn posting
- direct ingestion of private repos or private documents
- multilingual dubbing at production quality
- premium provider adapters as default behavior

## Personas

### Recruiter

Wants a 60-second project summary that explains what the project does, why it matters, and what role the creator played.

### Hiring Manager

Wants ownership, trade-offs, business impact, delivery scope, and engineering maturity.

### Engineer

Wants architecture, implementation decisions, risks, testing strategy, provider boundaries, and failure handling.

### Product Leader

Wants use case, differentiation, value, constraints, roadmap, and go-to-market clarity.

### Global Viewer

Wants a localized explanation in their preferred language without losing the technical meaning.

### Project Creator

Wants reusable project storytelling that is grounded in approved content and can be adapted for different audiences.

## Primary user journey

1. User creates a project.
2. User uploads markdown/text project knowledge.
3. System validates upload safety.
4. System chunks and stores approved knowledge.
5. User chooses audience, language, depth, and tone.
6. System retrieves relevant context.
7. System generates a grounded walkthrough script.
8. System evaluates unsupported claims.
9. System stores output, citations/context references, and evaluation metadata.
10. User views the generated walkthrough script in the UI.

## Functional requirements

### Project management

- Create project with name, description, language default, and audience default.
- List existing projects.
- Store generated walkthrough runs per project.

### Knowledge upload

- Accept markdown and plain text in MVP.
- Reject unsupported file types.
- Sanitize filenames.
- Enforce file size limits.
- Treat uploaded content as untrusted input.
- Store source metadata.

### Ingestion and retrieval

- Chunk uploaded knowledge deterministically.
- Store chunks with source metadata.
- Retrieve relevant context for a walkthrough request.
- Include context IDs or references with generated output.

### Script generation

- Generate a walkthrough script using only approved project context.
- Support audience-specific output.
- Support language parameter in MVP, even if translation quality is basic.
- Refuse or flag information not found in approved context.

### Evaluation

- Detect unsupported claims.
- Detect empty-context output.
- Detect prompt injection attempts inside uploaded documents.
- Store evaluation result with the run.

### UI

- Provide minimal UI for project creation, upload, run request, and output display.
- Show unsupported-claim warnings.
- Show AI-generated content disclosure where relevant.

## Non-functional requirements

- No mandatory paid provider APIs for MVP.
- No secrets committed.
- Provider SDKs must stay outside core domain logic.
- Tests must run locally without real premium provider keys.
- Generated output must include run metadata.
- Uploads must be bounded by type and size.
- Documentation must be updated with each vertical slice.
- Quality workflow must pass before merge.

## First vertical slice acceptance criteria

- User can create a project.
- User can upload markdown/text knowledge.
- System chunks and stores documents.
- User can request a walkthrough script.
- Script is grounded in uploaded content.
- Unsupported claims are flagged or refused.
- Output is visible in UI and stored.
- Tests pass without real paid provider keys.
- Docs explain how to run and validate the slice.

## Hard safety rules

- If approved project knowledge does not contain an answer, say the information is unavailable in the approved project context.
- Uploaded documents must never be allowed to override system/developer instructions.
- Premium avatar, TTS, face clone, and voice clone providers are disabled by default.
- Cloned face or voice requires explicit documented consent.
- Wav2Lip is not enabled by default.

## Success metrics

- Time to first grounded walkthrough.
- Groundedness score.
- Unsupported claim rate.
- Prompt-injection refusal pass rate.
- Language success rate.
- Cache hit rate.
- Cost estimate per run.
- User feedback score.

## MVP cut line

The first MVP is successful when a user can upload project knowledge and receive a stored, evaluated, grounded walkthrough script through a minimal UI.

Avatar video, voice, subtitles, premium providers, and interactive Q&A come after the grounding loop works.
