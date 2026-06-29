# PRD v1.0: NarraTwin AI

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29
- Implementation status: blocked until approved Stage 4 vertical slice

## 1. Summary

NarraTwin AI is a provider-agnostic multilingual AI avatar walkthrough platform. It
turns approved project knowledge into audience-aware, grounded scripts and later
voice, subtitle, video, and interactive avatar outputs.

The first usable product slice must prove the trust loop: upload project knowledge,
ingest and retrieve context, generate a grounded walkthrough script, evaluate
unsupported claims, store the result, and display it to the user. Avatar rendering,
voice, subtitles, premium providers, and interactive Q&A are future slices built on
that trusted foundation.

## 2. Contacts

| Role | Owner | Responsibility |
|---|---|---|
| Product owner | Rohit Agrawal | Product direction, stage approval, portfolio use case |
| Engineering agent | Codex | Issue-linked docs, specs, implementation plans, and code changes after gates pass |
| Reviewer | GitHub PR reviewer | Guardrail, safety, scope, and quality review |
| Future independent reviewer | TBD | Final review before release claims |

## 3. Background

Technical projects are often explained through long README files, architecture docs,
or English-only demo videos. Different viewers need different explanations:
recruiters want a short impact summary, hiring managers want ownership and trade-offs,
engineers want architecture and failure modes, product leaders want value and roadmap,
and global viewers may need a localized walkthrough.

Generic LLM summaries can hallucinate. Avatar tools can produce polished media without
knowing whether the script is true. NarraTwin AI solves this by making approved project
knowledge the source of truth and requiring generated outputs to carry context
references, evaluation results, and run metadata.

## 4. Objectives

### Product Objective

Enable a project creator to turn approved project knowledge into a grounded,
audience-aware walkthrough that can later be reused for multilingual video and
interactive avatar experiences.

### Stage 1 Objective

Harden product strategy and PRD v1.0 without adding product code.

### Stage 4 Slice 1 Objective

Deliver the first working user-facing path:

```text
project creation
-> markdown/text upload
-> ingestion/chunking/storage
-> context retrieval
-> grounded walkthrough script generation
-> unsupported-claim evaluation
-> stored output
-> UI display
```

### Key Results

| Key result | Target for first implementation slice |
|---|---|
| Activation | A user can create a project and produce one stored grounded walkthrough |
| Groundedness | Generated script contains context references for project-specific claims |
| Safety | Empty context, prompt injection, and unsupported claims are refused or flagged |
| Provider independence | Tests pass without real paid provider keys |
| Traceability | Run metadata links output to project, request parameters, provider mode, context, and evaluation |

## 5. Market Segments

| Segment | Problem | Primary output |
|---|---|---|
| Project creator | Needs reusable project storytelling for portfolio and interviews | Audience-aware grounded walkthrough |
| Recruiter | Needs fast signal from a technical project | 60-second summary with role and impact |
| Hiring manager | Needs ownership, trade-offs, maturity, and delivery scope | Concise walkthrough with decisions and outcomes |
| Engineer | Needs architecture and implementation evidence | Technical walkthrough with citations/context references |
| Product/customer viewer | Needs problem, value, workflow, and differentiation | Outcome-focused product walkthrough |
| Global viewer | Needs the same project in a preferred language | Localized script, subtitle, voice, and future avatar output |

## 6. Product Modes

### Mode 1: Pre-rendered Multilingual Demo Video

User value: create a shareable demo for portfolios, LinkedIn, YouTube, customer
education, or onboarding.

Target flow:

```text
English demo video or demo script
-> transcription or script cleanup
-> audience-specific grounded script generation
-> translation and localization
-> voiceover generation
-> avatar or video rendering
-> subtitles
-> export or shareable demo
```

Mode 1 is not fully implemented in Slice 1. Slice 1 produces the grounded script that
later video, voice, subtitle, and avatar providers consume. Existing demo script or
transcript cleanup is future scope, and uploaded demo video/audio transcription
requires an approved STT boundary in a future stage before implementation.

### Mode 2: Interactive AI Avatar Walkthrough

User value: let a viewer ask project-specific questions and receive grounded answers
from a future avatar-style guide.

Target flow:

```text
viewer selects language, audience, depth, and style
-> viewer asks a project question
-> system retrieves approved project context
-> system generates a grounded answer
-> system evaluates unsupported claims
-> future TTS/avatar provider speaks or displays the answer
```

Mode 2 is future scope. It must reuse the same project knowledge, retrieval,
grounding, evaluation, and provider-adapter principles as Mode 1.

## 7. Core Product Contract

### Project Knowledge Upload

The user uploads approved project knowledge. In Slice 1, accepted formats are
markdown and plain text only.

Requirements:

- Validate file type and extension.
- Enforce file size limits.
- Sanitize filenames.
- Reject binary, executable, archive, and unknown formats.
- Treat content and filenames as untrusted input.
- Store source metadata and checksums.

### Project Avatar Pack

The project-avatar-pack is the reusable source-of-truth contract documented in
`docs/PROJECT_AVATAR_PACK.md`.

Slice 1 does not require a full folder structure, but its data model and UX must not
block future support for:

- `project-summary.md`
- `architecture.md`
- `business-impact.md`
- `demo-script.md`
- `recruiter-pitch.md`
- `technical-deep-dive.md`
- `faqs.md`
- `metrics.md`
- future screenshots and diagrams

### RAG Ingestion

The system chunks approved project knowledge and stores source metadata so generated
outputs can reference context IDs or source chunks.

Requirements:

- Deterministic chunking for repeatable tests.
- Chunk metadata includes project, source file, checksum, and position.
- Retrieval is scoped to the selected project.
- Empty or insufficient context produces a refusal or warning.

### Grounded Script Generation

The generated walkthrough must use approved retrieved context only.

Requirements:

- Support audience, requested language, depth, and style parameters.
- Produce a script suitable for later voice/subtitle/avatar use.
- Cite context references for project-specific claims.
- Refuse or flag claims not supported by approved context.
- Store generation request, provider mode, and run metadata.

### Multilingual Script, Voice, And Subtitle Flow

Future slices must support:

- translation/localization of grounded scripts while preserving context references
- subtitle-ready WebVTT or SRT export once timing information exists
- untimed subtitle draft export before media timing exists
- optional TTS provider boundary with text input, voice profile metadata, audio
  artifact reference, provider mode, latency, and cost metadata
- AI voice disclosure in output metadata and UI wherever audio is produced
- language quality checks against approved source meaning
- fallback to script-only output when translation, subtitle, or voice generation fails

Slice 1 must store the requested language parameter, but generated script acceptance
is English-only until Stage 6. No translation, mock localization, best-effort
localization, multilingual evaluation, voice, or subtitle acceptance belongs to
Stage 4.

### Avatar And Lip-sync Provider Adapter

Future avatar/video output must use provider-agnostic adapters.

Requirements:

- Mock avatar provider is default until Stage 7.
- Adapter input includes grounded script, optional audio artifact, optional subtitle
  artifact, avatar profile, consent metadata, and provider mode.
- Adapter output includes render status, output artifact reference, provider metadata,
  disclosure text, fallback reason, and estimated cost when available.
- Premium provider SDKs stay outside core domain logic.
- Wav2Lip is not enabled by default.
- Any local or cloud lip-sync/avatar tool requires license review.
- Face cloning and voice cloning require explicit documented consent and are out of
  MVP scope.

## 8. Functional Requirements

| ID | Requirement | Stage target | Priority |
|---|---|---:|---|
| FR-001 | Create and select a project | Stage 4 | Must |
| FR-002 | Upload markdown/text project knowledge | Stage 4 | Must |
| FR-003 | Validate upload type, filename, size, and path safety | Stage 4 | Must |
| FR-004 | Ingest, chunk, and store approved knowledge with metadata | Stage 4 | Must |
| FR-005 | Retrieve project-scoped context for a walkthrough request | Stage 4 | Must |
| FR-006 | Generate a grounded walkthrough script for selected audience, stored requested language, depth, and style; Stage 4 script acceptance is English-only | Stage 4 | Must |
| FR-007 | Include context references for project-specific claims | Stage 4 | Must |
| FR-008 | Evaluate unsupported claims and empty-context output | Stage 4 | Must |
| FR-009 | Detect or neutralize prompt injection inside uploaded documents | Stage 4 and Stage 5 | Must |
| FR-010 | Store output, request parameters, context refs, and evaluation metadata | Stage 4 | Must |
| FR-011 | Display generated output and evaluation warnings in UI | Stage 4 | Must |
| FR-012 | Produce multilingual scripts from grounded source content | Stage 6 | Should |
| FR-013 | Export subtitle-ready output | Stage 6 | Should |
| FR-014 | Generate optional voice through mock/local-first TTS adapter | Stage 6 | Should |
| FR-015 | Render optional avatar/video output through adapter boundary | Stage 7 | Should |
| FR-016 | Support interactive Q&A over approved project knowledge | Future approved stage / `#20` | Should |
| FR-017 | Support optional premium providers without requiring them locally | Stage 7 adapter scope / `#21` | Should |
| FR-018 | Import an existing demo script or transcript and clean it into approved grounded source material | Stage 6 or later | Should |
| FR-019 | Support optional STT/transcription boundary for demo video or audio input before script cleanup | Future approved stage after provider and license review | Should |

## 9. Non-functional Requirements

| ID | Requirement |
|---|---|
| NFR-001 | No mandatory paid provider APIs for local development, tests, or CI |
| NFR-002 | No secrets, credentials, provider keys, private certificates, or tokens committed |
| NFR-003 | Provider keys are read only from environment variables |
| NFR-004 | Uploaded docs, prompts, transcripts, filenames, and provider outputs are untrusted |
| NFR-005 | Generated outputs include run metadata and source context references |
| NFR-006 | Evaluation failures block merge once evaluation exists |
| NFR-007 | Critical/high security findings block merge once security reports exist |
| NFR-008 | Architecture-impacting changes require ADR updates |
| NFR-009 | PRD-impacting changes require traceability updates |
| NFR-010 | Third-party tools, models, providers, APIs, datasets, and media assets are recorded in `docs/THIRD_PARTY_NOTICES.md` |
| NFR-011 | Public avatar or voice output includes AI-generated media disclosure |
| NFR-012 | Costs and provider mode are traceable per run |

## 10. User Journeys

### Journey A: Portfolio Creator Generates Recruiter Walkthrough

1. Creator creates a project.
2. Creator uploads markdown project knowledge.
3. System validates and stores source metadata.
4. Creator selects recruiter audience, English, concise depth, and confident style.
5. System retrieves project context.
6. System generates a grounded 60-second script.
7. System evaluates unsupported claims.
8. Creator sees the script, warnings if any, and source context references.

### Journey B: Hiring Manager Reviews Deeper Walkthrough

1. Hiring manager or creator selects the same project.
2. User selects hiring-manager audience and medium depth.
3. System generates a walkthrough focused on ownership, impact, trade-offs, and
   delivery maturity.
4. Unsupported claims are flagged or refused.

### Journey C: Engineer Reviews Technical Walkthrough

1. User selects engineer audience and deep depth.
2. System retrieves architecture and implementation context.
3. System generates a technical script with context references.
4. UI shows evaluation result and warnings.

### Journey D: Future Multilingual Demo Video

1. Creator starts from approved script or demo video transcript.
2. System grounds and adapts the script by audience.
3. System translates/localizes the script.
4. System generates subtitles and optional voice.
5. System sends output to an avatar/video adapter.
6. System exports a shareable demo with AI disclosure.

### Journey E: Future Interactive Avatar Walkthrough

1. Viewer selects language, audience, depth, and style.
2. Viewer asks a project question.
3. System retrieves approved project context.
4. System answers only from approved context.
5. Unsupported claims or missing context produce refusal/warning.
6. Future TTS/avatar adapter presents the answer.

## 11. Evaluation Gates

Every implementation slice that generates or evaluates AI output must define and run
evaluation gates appropriate to that stage.

Slice 1 gates:

- happy-path grounded walkthrough generation
- empty-context refusal
- prompt-injection-in-uploaded-doc test
- unsupported-claim detection or refusal
- source context references present
- run metadata stored
- no paid provider key required

Later gates:

- translation sanity and language consistency
- subtitle structure validation
- TTS adapter fallback
- avatar/video adapter fallback
- premium provider cost and failure handling

## 12. Security And Privacy Guardrails

Hard rules:

- Uploaded project knowledge is data, not instructions.
- Empty context must not produce invented facts.
- Premium providers are disabled by default.
- Provider responses are untrusted until evaluated.
- No cloned voice or face without explicit documented consent.
- Wav2Lip is not enabled by default.
- Private data must not be sent to external providers without explicit configuration.
- Logs must not store raw secrets, tokens, or private provider keys.
- Project data must be isolated by project identifier and future tenant/user boundary.
- Uploaded source files and generated runs must have a documented retention and
  deletion policy before external storage or multi-user access ships.
- External provider egress requires explicit provider-mode configuration and visible
  run metadata.
- Uploaded content must be screened for obvious secrets before being sent to external
  providers in any non-local mode.
- The system must record which files are approved sources for each run so users and
  reviewers can audit the grounding basis.

## 13. Free-first And Premium-provider Modes

### Free-first Engineering Mode

Default for local/dev/test:

- mock providers where possible
- local filesystem storage first
- no required premium provider key
- deterministic test fixtures
- provider mode visible in run metadata

### Premium-provider Mode

Optional future mode:

- HeyGen, Tavus, D-ID, ElevenLabs, or similar providers may be adapters.
- Premium provider use must be explicit.
- Cost, provider, latency, and failure metadata must be recorded.
- Core domain logic must not depend directly on provider SDKs.
- Stage 8 may harden premium-provider behavior only after an adapter exists in an
  earlier approved stage; it must not introduce new provider features during
  hardening.

## 14. MVP Scope

Included in first implementation slice:

- project creation
- markdown/text upload
- upload validation
- ingestion/chunking/storage
- project-scoped retrieval
- audience/requested-language/depth/style request
- grounded script generation
- unsupported-claim evaluation
- stored output with context refs and metadata
- minimal UI display

Excluded from first implementation slice:

- full avatar rendering
- lip-sync
- TTS audio generation
- subtitles
- production translation quality
- video export
- interactive Q&A
- premium provider adapters
- voice cloning
- face cloning
- private repo ingestion

## 15. Success Criteria

Stage 1 succeeds when:

- strategy and PRD v1.0 are explicit about product modes, users, requirements,
  non-goals, safety, and metrics
- requirements are mapped in a traceability matrix
- phase plan preserves gated vertical slices
- no product code is introduced

Slice 1 succeeds when:

- user can produce a stored grounded walkthrough from uploaded markdown/text
- output includes at least one context reference for each project-specific paragraph
  or a refusal explaining why context is insufficient
- unsupported claims are flagged or refused across a controlled fixture set with at
  least one supported claim, one unsupported claim, and one mixed-claim response
- empty-context refusal works for a project with no stored chunks and for a retrieval
  miss against an existing project
- prompt injection inside uploaded content is neutralized for at least one fixture
  containing instructions to ignore system/developer rules
- tests run without real paid provider keys
- docs describe validation evidence and known limitations
- requested language is stored in run metadata, while production translation quality
  remains explicitly out of Slice 1 scope

## 16. Open Questions

| Question | Default decision until resolved |
|---|---|
| Which LLM provider is used first outside mocks? | Use mock/local defaults; optional Gemini only after provider review |
| What language behavior is required before Stage 6? | Store requested language in Slice 1; generated script acceptance stays English-only until Stage 6 |
| How many languages are required for first multilingual slice? | Start with a narrow reviewed set in Stage 6 |
| What is the first avatar provider? | Mock avatar first; premium provider after adapter and license review |
| What storage persists project runs? | Local filesystem first unless Stage 2/3 architecture changes this |
| How will human reviewers score recruiter usefulness? | Start with simple acceptance rubric and feedback field |
