# Product Strategy

## Product thesis

Static GitHub repos, long README files, and English-only demo videos are not enough for global hiring, product onboarding, and technical storytelling.

NarraTwin AI turns approved project knowledge into a multilingual, audience-aware AI avatar walkthrough that can explain the same project differently for recruiters, hiring managers, engineers, product leaders, customers, and global non-English audiences.

## Strategic bet

The project is not differentiated by avatar generation alone.

The durable product value is the **grounded project knowledge pack**:

- approved source material
- audience-specific explanation
- traceable context
- unsupported-claim checks
- provider-agnostic media generation
- reusable project storytelling across languages and channels

## Target users

- Job seekers building AI/software portfolios.
- Recruiters evaluating technical candidates quickly.
- Hiring managers reviewing project ownership and impact.
- Engineers reviewing architecture and implementation depth.
- Product teams creating onboarding, demo, or training material.
- Global users who prefer non-English explanations.

## Primary use cases

1. Recruiter-facing 60-second project walkthrough.
2. Hiring-manager walkthrough focused on ownership, impact, and trade-offs.
3. Engineer walkthrough focused on architecture, APIs, data flow, testing, and risks.
4. Product/customer walkthrough focused on problem, value, workflow, and outcome.
5. Localized walkthrough for non-English audiences.
6. Future Q&A over approved project knowledge.

## Differentiation

NarraTwin AI is differentiated by:

- grounding in approved project knowledge
- audience-aware explanation
- multilingual output
- provider-agnostic architecture
- free engineering mode plus optional premium showcase mode
- AI evaluation and unsupported-claim prevention
- observability and cost metadata
- reusable project knowledge pack model

## Positioning

Provider-agnostic multilingual AI avatar walkthrough platform for project demos, onboarding, and technical storytelling.

## MVP strategy

Prove the trust loop before media polish:

1. Project creation.
2. Knowledge upload.
3. Ingestion and retrieval.
4. Grounded script generation.
5. Unsupported-claim evaluation.
6. Stored output.
7. Minimal UI display.

Avatar video, TTS, subtitles, premium providers, and interactive Q&A come after this loop is stable.

## Free engineering mode

Free mode proves the product can be built and tested without mandatory paid dependencies.

Default assumptions:

- Gemini or mock LLM provider for local development.
- ChromaDB or local vector-store abstraction.
- local filesystem storage first.
- mock avatar/TTS/STT providers first.
- FFmpeg only after license review.

## Premium showcase mode

Premium providers are optional adapters for polished demos.

They must never be hardcoded into core business logic.

Examples:

- HeyGen
- Tavus
- D-ID
- ElevenLabs

## Key risks

- Avatar quality distracts from the core value.
- RAG output makes unsupported claims.
- Uploaded documents contain prompt injection.
- Users upload confidential project data.
- Local avatar/lip-sync tools have license restrictions.
- Cost rises due to repeated generation.
- The product becomes a broad skeleton instead of a working vertical slice.

## Strategic guardrails

- No mandatory paid APIs in MVP.
- No voice or face cloning in MVP.
- No Wav2Lip default path.
- No unsupported claims.
- No unreviewed third-party avatar tools.
- No large disconnected scaffolding.
- Every slice must produce a working user-facing outcome.
