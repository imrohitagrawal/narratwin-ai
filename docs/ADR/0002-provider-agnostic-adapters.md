# ADR 0002: Provider-Agnostic Adapters

## Status

Accepted for MVP planning.

## Decision

All external AI, speech, avatar, video, storage, vector, evaluation, and observability systems must be accessed through internal interfaces.

Core domain logic must not import external provider SDKs directly.

## Required interfaces

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

## Rationale

NarraTwin AI needs free engineering mode and optional premium showcase mode.

Provider-agnostic adapters allow:

- mock/fake providers for tests
- Gemini or local providers for free mode
- HeyGen/Tavus/D-ID/ElevenLabs as optional adapters later
- clean license/provider review
- failure fallback without rewriting core business logic

## Adapter rules

- Provider SDK imports live only in adapter modules.
- Provider keys are read only from environment/config.
- Tests must use mocks/fakes by default.
- Real provider tests must be opt-in.
- Adapters must expose structured errors.
- Provider response must be evaluated before display.
- New provider adapters require contract tests.

## Rejected alternative

Hardcoding provider SDK calls inside services or routes was rejected because it creates vendor lock-in, makes tests expensive, and increases risk of accidental paid API usage.

## Consequences

Positive:

- easier provider replacement
- safer tests
- clearer premium/free separation
- better reviewability

Negative:

- more boilerplate
- interface design must stay disciplined
- adapter contract tests are mandatory

## Slice 1 impact

Slice 1 should use:

- mock LLM provider if real keys are unavailable
- local storage provider
- vector-store abstraction
- mock evaluation or deterministic evaluation first

Slice 1 must not require:

- HeyGen
- Tavus
- D-ID
- ElevenLabs
- real avatar video provider
- real voice or face cloning
