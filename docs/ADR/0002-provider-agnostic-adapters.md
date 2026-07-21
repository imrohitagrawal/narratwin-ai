# ADR 0002: Provider-Agnostic Adapters

## Status

Accepted and amended for Stage 7.

`docs/ADR/0003-llm-provider-routing.md` supersedes only the LLM routing details
that previously lived here. The general provider-adapter rule remains
authoritative for avatar, video, speech, storage, vector, evaluation, and
observability adapters unless a later ADR explicitly replaces it.

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
- `TTSProvider` wraps voice artifact generation behavior; issue `#237` adds a
  narrow `backend/app/tts_provider.py` boundary for optional server-side real
  TTS without provider SDKs or default egress.
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
- Legacy unavailable voice providers such as `external` fall back to the
  mock/local provider and record a structured fallback reason. Named real TTS
  providers such as `elevenlabs` fail closed instead of silently falling back.
- The mock/local voice adapter emits a JSON manifest only. Optional real TTS
  emits a provider-neutral `stage6-tts-manifest-v2` plus a normalized audio
  artifact after source/eval binding, strict citation preservation, language and
  script-length checks, quota reservation, bounded retry/timeout/backpressure,
  output validation, and redacted logging gates pass.
- PR3 uses injected fake transports in tests, installs no provider SDK, reads no
  provider key by default, makes no real provider calls in CI, and permits only
  stock/non-cloned voice provenance. It does not implement avatar/video provider
  work or make real TTS output valid for Stage 7 avatar rendering; that remains
  a later issue-linked avatar/video provider integration decision.
- Additional paid translation or voice providers remain future optional adapters
  and must add contract tests, environment-only keys, license review, and
  third-party notices before activation. A future provider must update
  `backend/app/tts_provider.py`, `backend/app/stage6.py`, API contracts,
  unit/API tests, security notes, and third-party notices before it can be
  enabled.

This preserves the provider-adapter boundary while allowing Stage 6 to deliver
translation, glossary preservation, subtitles, and mock/local voice artifacts.

## Stage 7 impact

Stage 7 implements the first avatar-rendering export path without hardcoding paid
providers:

- `AvatarProvider` wraps avatar-render preparation behavior.
- A local HTML `VideoRenderer` export path emits a deterministic demo export
  artifact rather than a real video binary.
- The active implementation uses `MockAvatarProvider` for local/dev/test.
- `ExternalAvatarProviderStub` exists only as a disabled adapter stub; it does
  not contain paid provider SDK calls, real provider keys, or network behavior.
- `ProviderConfig` records provider mode, adapter kind, network egress, key
  requirement, real-video support, and cloned-identity support, and is validated
  before the render result is stored or returned.
- Successful Stage 7 outputs must be mock/local-only: no external stub may
  produce a successful render, and no successful output may advertise network
  egress, required API keys, real video, or cloned identity support.
- Successful Stage 7 provider metadata must agree with validated provider config:
  both `avatarProvider.providerMode` and `providerConfig.providerMode` are
  `LOCAL`, and provider-supplied fallback reasons are restricted to the contract
  enum values.
- Render job status history records `QUEUED`, `RUNNING`, `FALLBACK`, `FAILED`,
  and `COMPLETED` events so fallback behavior is auditable.
- Requested unavailable avatar providers fall back to the mock/local provider and
  record `REQUESTED_PROVIDER_UNAVAILABLE`.
- Disabled or failed provider stubs fall back to the mock/local provider and
  record `PROVIDER_RENDER_FAILED` when fallback succeeds.
- Stage 7 validates provider output after adapter return and before display or
  artifact creation: demo export artifacts must use `text/html`, render manifests
  and video export placeholders must use `application/json`, filenames must be
  safe, decoded content must stay within size limits, checksums must match
  decoded content, provider config must be local-only for the mock adapter, and
  manifests must include AI-generated avatar/video disclosure, source citations,
  trace metadata, evaluation status, provider config, and placeholder metadata.
- HTML demo exports also reject active HTML content and must match trusted source
  run, trace, and disclosure text exactly; JSON manifest and placeholder
  artifacts are semantically cross-checked against trusted render inputs,
  including source context-ref IDs, citation indexes, evaluation ID/checksum,
  provider config, disclosure, and public-use license checks before storage or
  API response. The video placeholder is self-contained metadata, not a hidden
  real-video export.
  This is intentionally stricter from the start because Stage 6 showed that
  validating one provider output surface while leaving another unchecked creates
  late review findings.
- Failed idempotent render attempts are retained as terminal failed records so a
  matching retry returns the same error without re-entering the provider.
- Synthetic avatar demo export requires explicit consent and records consent
  metadata. Cloned identity rendering remains disabled and fails with
  `CLONED_IDENTITY_DISABLED` until consent controls, provenance metadata, and
  review evidence are implemented in a later approved scope.
- Stage 7 response schemas allow provider IDs beyond `mock` while constraining
  `providerMode` to contract-approved modes, so future local adapters can be
  tested without changing the public response shape.
- Paid avatar providers remain future optional adapters and must add contract
  tests, environment-only keys, license review, identity consent/provenance
  review, third-party notices, and provider-output validation before activation.
- Demo Checkpoint 1 PR4 issue `#241` adds `backend/app/avatar_video_provider.py`
  as the optional server-side avatar/video provider boundary. It uses injected
  transports, fake DNS resolution, fake sleeps, and fake provider responses in
  tests; installs no provider SDK; reads no provider key by default; and makes no
  real provider calls in local/dev/test/CI.
- The PR4 boundary accepts only fully synthetic no-real-person or provider-stock
  licensed non-identifiable asset provenance by default. Prompt-with-reference,
  custom replica, Digital Twin, user-provided likeness image, cloned identity,
  and real-person likeness assets fail before transport calls unless a later
  consent/provenance issue approves them.
- PR4 provider output validation rejects failed/stale evals, source/eval/media
  binding mismatches, citation mismatches, prompt-injection markers, malformed or
  duplicate-key JSON, unexpected fields, retry cap overrun, unsafe URLs including
  private/reserved/link-local/cloud-metadata resolved addresses, redirects,
  MIME/extension mismatch, oversized artifacts, and providers lacking deletion
  evidence when deletion is requested.
- Stage 7 API responses, render manifests, and video placeholders now include a
  disabled `avatarVideoProvider` metadata surface recording provider mode,
  disabled egress, asset provenance policy, disclosure version, and
  retention/deletion state. This is not a hosted URL, public distribution link,
  real video output, or production-readiness claim.

This preserves the provider-adapter boundary while allowing Stage 7 to deliver a
mock/local avatar demo export with public-use license checks, disclosure, consent
controls, source citations, and evaluation status preservation.
