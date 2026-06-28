# PRD Red-Team Review

## Review goal

Challenge the NarraTwin AI PRD before implementation so Codex does not build a broad, shallow, or unsafe product skeleton.

## Critical risks to challenge

### Risk 1: MVP scope is too broad

Concern:

- Avatar, TTS, subtitles, Q&A, translation, and premium providers can distract from the grounded-script loop.

Decision:

- Slice 1 must stop at grounded script generation, evaluation, storage, and UI display.
- Avatar/video output comes later.

### Risk 2: Avatar quality distracts from product value

Concern:

- Poor avatar quality can make the product look weak even if the grounding engine works.

Decision:

- Mock avatar provider first.
- Do not judge MVP success by avatar realism.

### Risk 3: Free/local avatar tools may have licensing risk

Concern:

- Some lip-sync or avatar tools may be research-only, non-commercial, or unclear for public portfolio use.

Decision:

- License review before adding any local avatar dependency.
- Wav2Lip is disabled by default.

### Risk 4: RAG may hallucinate

Concern:

- Generated scripts may claim capabilities not present in uploaded project knowledge.

Decision:

- Unsupported-claim evaluation is part of Slice 1.
- Empty context must result in refusal.

### Risk 5: Uploaded docs can contain prompt injection

Concern:

- A README or markdown file can include malicious instructions such as "ignore previous instructions".

Decision:

- Uploaded docs are treated as data, not instructions.
- Prompt-injection tests are mandatory.

### Risk 6: Users may upload confidential data

Concern:

- Users may upload private architecture docs, credentials, or customer data.

Decision:

- Local-first storage for MVP.
- Secrets scanning and upload validation are mandatory.
- Future external provider upload behavior must be explicit.

### Risk 7: Costs rise silently

Concern:

- Repeated generations, translations, and media outputs can create unexpected cost.

Decision:

- Store provider, cache, token usage when available, and estimated cost per run.
- Default to free engineering mode.

### Risk 8: Codex builds too much too early

Concern:

- Codex may create backend, frontend, providers, dashboard, avatar, and CI all at once.

Decision:

- Work only by vertical slices.
- Use the stage gates in `docs/SKILL_TRUST_REVIEW.md` and `docs/ROADMAP.md`.

## Required mitigations

- First slice must not depend on avatar video.
- Mock avatar provider first.
- License review before any local avatar dependency.
- Unsupported-claim tests.
- Prompt-injection tests.
- Empty-context refusal tests.
- Caching and cost metadata from early slices.
- PRD acceptance criteria must beat broad skill suggestions.

## Go/no-go before coding

Go only if:

- PRD clearly separates MVP from future scope.
- Architecture has provider interfaces.
- Security file covers uploads and prompt injection.
- AI safety file defines evaluation gates.
- Third-party notices list license blockers.
- Quality workflow and local validation expectations are documented.
