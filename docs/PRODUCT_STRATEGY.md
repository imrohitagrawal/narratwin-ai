# Product Strategy: NarraTwin AI

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29

## Strategy Thesis

NarraTwin AI helps project creators turn approved project knowledge into grounded,
audience-aware walkthroughs for hiring, portfolio, onboarding, and product education.
The product is not an avatar generator with a chatbot attached. The durable value is
a reusable project knowledge system that can explain the same project consistently
across audiences, languages, scripts, subtitles, voice, video, and future interactive
avatar Q&A.

The first strategic bet is trust before media polish:

```text
approved project knowledge
-> safe ingestion and retrieval
-> grounded script generation
-> unsupported-claim evaluation
-> stored output with citations and run metadata
-> later voice, subtitles, avatar, and export adapters
```

## Vision

Make every strong project explainable to the right audience in the right language,
with claims grounded in approved source material and media generation kept optional,
auditable, and provider-agnostic.

## Product Modes

NarraTwin AI preserves two product modes from the start, even though the first
implementation slice proves only the grounded script loop.

### Mode 1: Pre-rendered Multilingual Demo Video

This mode helps project creators produce portfolio-ready and recruiter-ready demo
assets for LinkedIn, YouTube, portfolio sites, customer onboarding, and product
education.

Target flow:

```text
English demo video or demo script
-> transcription or script cleanup
-> audience-specific grounded script generation
-> translation and localization
-> optional voiceover generation
-> optional avatar or video rendering
-> subtitles
-> export or shareable demo
```

### Mode 2: Interactive AI Avatar Walkthrough

This mode helps a viewer ask project-specific questions and receive grounded,
audience-aware answers through a future avatar-style guide.

Target flow:

```text
viewer selects language, audience, depth, and style
-> viewer asks a project question
-> system retrieves approved project context
-> system generates a grounded answer
-> system evaluates unsupported claims
-> future TTS/avatar provider speaks or displays the answer
```

## First Market Segment

The first segment is project creators who need to present technical work clearly to
recruiters, hiring managers, and engineering reviewers.

This segment comes first because the pain is acute, the source material usually
already exists, the first workflow can be proven with markdown/text uploads, and
success can be evaluated without building full avatar rendering first.

## Jobs To Be Done

| Segment | Job | Desired outcome | Constraint |
|---|---|---|---|
| Project creator | Turn project docs into a polished explanation | A reusable walkthrough that can be adapted by audience and language | Must avoid unsupported claims |
| Recruiter | Quickly understand what a project proves | A short, credible explanation of purpose, role, and impact | Limited review time |
| Hiring manager | Assess ownership and engineering maturity | Clear trade-offs, scope, decisions, and outcomes | Needs signal without reading every file |
| Engineer | Review technical depth | Architecture, data flow, tests, failure modes, and risks | Needs evidence and citations |
| Product/customer viewer | Understand product value | Problem, workflow, differentiation, and outcomes | Needs less technical framing |
| Global viewer | Consume the same project in a preferred language | Localized explanation that preserves meaning | Translation must not invent facts |

## Value Propositions

### Project Creator

- Before: project value is trapped in long docs, English-only videos, or ad hoc
  explanations.
- How: upload approved project knowledge, select audience and language, generate a
  grounded walkthrough with evaluation metadata.
- After: the creator has reusable project storytelling for portfolios, interviews,
  onboarding, and demos.
- Alternatives: hand-written scripts, generic chatbots, static README files, manual
  video editing, and one-off demo recordings.

### Recruiter And Hiring Manager

- Before: project review depends on scanning README files and guessing the creator's
  role.
- How: NarraTwin AI generates a concise, audience-specific walkthrough grounded in
  approved project facts.
- After: reviewers get a faster, clearer signal about project purpose, ownership,
  impact, and maturity.
- Alternatives: resume bullets, GitHub links, portfolio pages, and generic video
  demos.

### Engineering Reviewer

- Before: technical depth is hard to assess from a short demo.
- How: the same project pack can produce deeper architecture and trade-off views
  with source context references.
- After: reviewers can inspect claims, constraints, and risks without relying on
  unsupported AI summaries.
- Alternatives: architecture docs, code review, manual Q&A, and static diagrams.

## Competitive Positioning

NarraTwin AI competes against several partial alternatives:

- generic LLM summaries
- avatar video tools
- manual demo video editing
- static portfolio pages
- README-driven project review
- presentation decks and walkthrough scripts

The product wins by combining:

- grounded project-specific context
- audience-aware explanation
- multilingual output path
- evaluation gates for unsupported claims
- reusable project-avatar-pack contract
- free-first local/dev/test mode
- optional premium provider mode through adapters

## Strategic Trade-offs

NarraTwin AI will not:

- build avatar realism before grounding works
- require paid providers for local development or tests
- enable voice cloning or face cloning in the MVP
- enable Wav2Lip by default
- ingest private repositories or arbitrary binary files in Slice 1
- claim facts that are not present in approved project knowledge
- import premium provider SDKs into core product logic
- create broad horizontal scaffolding before vertical slices are approved

These trade-offs keep the product focused on trusted explanations rather than
unreviewed media generation.

## Business Model Direction

The default path is free-first engineering mode:

- mock/local providers for tests
- local filesystem storage first
- optional Gemini or equivalent free/low-cost LLM mode after provider review
- no required premium provider keys

Premium showcase mode is optional:

- HeyGen, Tavus, D-ID, ElevenLabs, or similar adapters can improve production media
  quality later.
- Premium providers must remain replaceable, disabled by default, and visible in run
  metadata and cost reporting.

## Strategic Metrics

North Star:

- successful grounded walkthrough generated per approved project

One Metric That Matters for Stage 4 Slice 1:

- percentage of walkthrough generation runs that produce a stored output with
  context references and a passing unsupported-claim evaluation

Supporting metric families:

- activation: time to first grounded walkthrough
- quality: groundedness score and unsupported-claim rate
- safety: prompt-injection refusal pass rate and empty-context refusal pass rate
- media readiness: subtitle, voice, and avatar render success rates in later stages
- cost: estimated cost per run and cache hit rate
- portfolio usefulness: creator approval and recruiter/hiring-manager usefulness
  feedback

## Growth Strategy

Initial growth is product-led through visible portfolio artifacts:

- project creators generate recruiter-ready walkthroughs
- portfolio visitors consume short explanations
- hiring and engineering reviewers request deeper views
- shared demos expose the value of the reusable project-avatar-pack

Later growth can include:

- team onboarding walkthroughs
- customer education demos
- multilingual product explainers
- premium export and avatar provider integrations

## Required Capabilities

| Capability | Why it matters | First allowed stage |
|---|---|---|
| Project knowledge upload | User-owned source material enters the system | Stage 4 |
| RAG ingestion and retrieval | Keeps generation grounded in approved context | Stage 4 |
| Grounded script generation | Core user-facing value | Stage 4 |
| Unsupported-claim evaluation | Blocks hallucinated project claims | Stage 4 and Stage 5 |
| Prompt-injection defenses | Uploaded docs are untrusted input | Stage 4 and Stage 5 |
| Multilingual script flow | Supports global viewers | Stage 6 |
| Subtitles | Makes pre-rendered demos accessible and shareable | Stage 6 |
| Voice adapter | Enables audio without hardcoding paid providers | Stage 6 |
| Avatar/lip-sync adapter | Enables media rendering without provider lock-in | Stage 7 |
| Observability and cost metadata | Makes runs debuggable and affordable | Stage 4 onward |

## Defensibility

The defensible asset is the project-avatar-pack plus the evaluation-backed generation
workflow. Generic avatar tools can render a talking head, but they do not provide a
repo-specific, audience-aware, multilingual, citation-backed explanation system with
security, privacy, and provider-mode controls.

## Critical Hypotheses

1. Project creators will upload or maintain enough approved knowledge to generate a
   useful walkthrough.
2. Recruiters and hiring managers value a short, grounded walkthrough more than
   another generic portfolio page.
3. Evaluation gates can reduce unsupported claims enough to make generated scripts
   reviewable.
4. Free-first mode can prove the product without premium media providers.
5. Premium avatar/video quality is valuable only after the script and grounding loop
   are trusted.

## Low-effort Validation Experiments

| Hypothesis | Experiment | Kill criterion |
|---|---|---|
| Creators can provide useful source knowledge | Use 3 real project-avatar-pack examples and generate scripts manually or with a mock pipeline | Fewer than 2 produce a useful recruiter script |
| Recruiter/hiring-manager walkthroughs are valuable | Ask 5 reviewers to compare README-only review with generated walkthrough review | Fewer than 3 prefer the walkthrough |
| Grounding can be evaluated | Build a controlled unsupported-claim test set before implementation | Evaluation cannot catch obvious false claims |
| Free-first mode is viable | Run all Stage 4 tests with mocks and no premium keys | Any required test needs a paid provider |
| Media should wait | Compare polished avatar with weak script vs. plain text with strong grounding | Reviewers prefer media despite unsupported claims |

## Stage 1 Decision

Stage 1 hardens the product definition and PRD. It does not permit product
implementation. Product implementation remains blocked until Stage 2 architecture,
Stage 3 repository foundation, and the approved Stage 4 vertical slice are reviewed
through issue-linked PRs.
