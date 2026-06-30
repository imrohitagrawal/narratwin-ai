# ADR 0002: Provider-Agnostic Adapters

## Status

Superseded by `docs/ADR/0003-llm-provider-routing.md`.

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

## Stage 6 impact

Stage 6 implements the first multilingual media-adjacent path without hardcoding
paid providers:

- `TranslationProvider` wraps translation/localization behavior.
- `TTSProvider` wraps voice artifact generation behavior.
- The active implementation uses `MockTranslationProvider` and `MockTTSProvider`
  for local/dev/test.
- Subtitle generation remains deterministic local logic that emits downloadable
  SubRip artifacts.
- Stage 6 validates provider output after adapter return and before display or
  artifact creation: translated text must be non-empty, remain within size
  limits, preserve required glossary terms, and preserve citation markers.
- Stage 6 response schemas allow provider IDs beyond `mock` while constraining
  `providerMode` to contract-approved modes, so future local adapters can be
  tested without changing the public response shape.
- Requested unavailable voice providers fall back to the mock/local provider and
  record a structured fallback reason.
- The mock/local voice adapter emits a JSON manifest only. Stage 6 does not
  synthesize playable audio, does not clone voices, and does not send text or
  audio to non-local providers.
- Paid translation or voice providers remain future optional adapters and must
  add contract tests, environment-only keys, license review, and third-party
  notices before activation. A future provider must update `backend/app/stage6.py`,
  API contracts, unit/API tests, security notes, and third-party notices before
  it can be enabled.

This preserves the provider-adapter boundary while allowing Stage 6 to deliver
translation, glossary preservation, subtitles, and mock/local voice artifacts.
