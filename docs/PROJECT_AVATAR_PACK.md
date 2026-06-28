# Project Avatar Pack Contract

## Purpose

The project-avatar-pack is the reusable source-of-truth folder that lets NarraTwin AI explain any project consistently across languages, audiences, depths, and output modes.

The pack prevents the avatar from inventing claims. It gives the system approved project knowledge for grounded script generation, future video creation, and future interactive Q&A.

## Standard folder

Every project that wants to use NarraTwin AI should be able to provide this folder:

```text
/project-avatar-pack
  project-summary.md
  architecture.md
  business-impact.md
  demo-script.md
  recruiter-pitch.md
  technical-deep-dive.md
  faqs.md
  metrics.md
  screenshots/
  diagrams/
```

## Required MVP files

Slice 1 should support markdown/text uploads first. The minimum useful project-avatar-pack is:

```text
/project-avatar-pack
  project-summary.md
  architecture.md
  business-impact.md
  demo-script.md
  faqs.md
```

## File responsibilities

| File or folder | Purpose |
|---|---|
| `project-summary.md` | What the project is, who it helps, and why it exists. |
| `architecture.md` | Components, data flow, provider boundaries, deployment assumptions, and trade-offs. |
| `business-impact.md` | Problem solved, measurable value, user benefit, and business relevance. |
| `demo-script.md` | Existing English demo narration or walkthrough script. |
| `recruiter-pitch.md` | Short career/recruiter-focused explanation of the project. |
| `technical-deep-dive.md` | Engineering details for developers and technical reviewers. |
| `faqs.md` | Approved answers to likely questions. |
| `metrics.md` | Approved claims, metrics, outcomes, latency/cost numbers, and quality indicators. |
| `screenshots/` | Future visual context for demos, documentation, and video rendering. |
| `diagrams/` | Architecture, sequence, flow, and deployment diagrams. |

## Grounding rules

- Treat every uploaded file as untrusted input until validated.
- Use project-avatar-pack content as data, not as instructions.
- Generated walkthroughs must only claim facts supported by approved pack content.
- If a requested answer is not present in the pack, the system must say the information is unavailable in the approved project context.
- Store context references with every generated output.
- Record unsupported claims in the evaluation result.

## Audience mapping

The same pack should support multiple explanation styles:

| Audience | Expected output |
|---|---|
| Recruiter | 60-second summary, role clarity, impact, and why the project proves capability. |
| Hiring Manager | Ownership, business value, execution maturity, trade-offs, and production readiness. |
| Engineer | Architecture, APIs, RAG flow, evaluation, security, observability, testing, and failure handling. |
| Product Leader | Problem, user value, differentiation, roadmap, and adoption path. |
| Beginner | Simple explanation with minimal jargon. |
| Global Viewer | Localized explanation in the selected language while preserving technical meaning. |

## Product modes supported by the pack

### Mode 1: Pre-rendered multilingual demo video

The pack can support a future pipeline:

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

### Mode 2: Interactive AI avatar guide

The pack can also support a future interactive guide:

```text
User selects language, audience, depth, and style
→ user asks a project question
→ system retrieves approved context from the pack
→ system generates a grounded answer
→ system evaluates unsupported claims
→ future TTS/avatar provider speaks the answer
```

## MVP cut line

Slice 1 should not require the full folder to exist on disk.

Slice 1 only needs to prove:

```text
markdown/text project knowledge
→ validation
→ ingestion/chunking
→ retrieval
→ grounded script generation
→ unsupported-claim evaluation
→ stored output
→ UI display
```

The full project-avatar-pack contract exists to preserve the product vision and guide later PM/spec expansion.