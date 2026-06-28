# ADR 0003: Free Mode vs Premium Mode

## Status

Accepted for MVP planning.

## Decision

NarraTwin AI supports two execution modes:

- Free Engineering Mode
- Premium Showcase Mode

Free Engineering Mode is the default and must be enough to build, test, and demonstrate the core product value.

Premium Showcase Mode is optional and must be implemented only through provider adapters.

## Rationale

Free mode proves engineering depth and keeps development cost low. Premium mode enables polished recruiter-facing or customer-facing demos after the grounding loop works.

## Free Engineering Mode

Default capabilities:

- project creation
- markdown/text upload
- ingestion, chunking, and storage
- RAG retrieval
- grounded script generation
- unsupported-claim evaluation
- local storage
- mock media providers
- tests with no real premium provider keys

## Premium Showcase Mode

Future optional adapters may include:

- HeyGen
- Tavus
- D-ID
- ElevenLabs

Premium mode must not be required for:

- local development
- CI
- unit tests
- Slice 1 demo
- portfolio README claims

## Consequences

Positive:

- lower development cost
- safer public showcase
- easier CI
- clear provider boundaries

Negative:

- first demo may look less polished
- extra adapter work is needed later
- provider capability differences must be handled explicitly

## Non-negotiable rules

- Mock avatar provider is required.
- Premium APIs must be optional.
- Cost tracking is required.
- Provider adapters need contract tests.
- Personal identity media features are out of MVP scope.
- AI-generated media disclosure is mandatory where media output exists.

## Slice 1 impact

Slice 1 must stop at grounded script generation, evaluation, storage, and UI display.

Do not add premium provider dependencies to Slice 1.
