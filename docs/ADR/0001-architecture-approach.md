# ADR 0001: Architecture Approach

## Status

Superseded by `docs/ADR/0001-system-architecture.md`.

## Decision

Use a modular provider-agnostic architecture with FastAPI backend, Next.js frontend, local-first storage, explicit provider interfaces, and mock providers for tests.

## Context

NarraTwin AI must support:

- free engineering mode
- optional premium provider mode
- grounded script generation
- future avatar/video/TTS providers
- multilingual output
- AI safety and unsupported-claim checks
- public portfolio usage without mandatory paid APIs

A tightly coupled provider-first architecture would make the product hard to test, expensive to run, and risky to showcase publicly.

## Options considered

### Option A: Provider-first build

Start directly with Gemini, HeyGen, Tavus, D-ID, ElevenLabs, or avatar SDKs.

Rejected because:

- paid providers become hard dependencies
- tests require real keys
- core logic becomes vendor-specific
- license and consent risks appear too early

### Option B: Full platform skeleton first

Create backend, frontend, dashboard, providers, avatar, TTS, subtitles, and Q&A at once.

Rejected because:

- high chance of shallow scaffolding
- hard to validate
- Codex may drift into unrelated modules
- user-facing value is delayed

### Option C: Provider-agnostic vertical slices

Build one working user-facing path through internal interfaces and mocks/fakes first.

Accepted.

## Consequences

Positive:

- easier provider replacement
- tests can run without paid keys
- premium providers remain optional
- security and safety rules stay central
- vertical-slice delivery is easier to review

Negative:

- more interfaces up front
- more contract tests needed
- slightly slower initial implementation

## Implementation impact

- Define provider interfaces before provider SDK adapters.
- Keep core domain logic independent from SDK imports.
- Use mock providers in Slice 1.
- Add contract tests for any real provider adapter.
- Do not add avatar/video provider until the grounding loop works.

## Security impact

- Uploaded documents stay untrusted.
- Provider outputs must be evaluated before display.
- Secrets stay in `.env` and CI secrets only.
- No premium provider key is required for tests.

## Test impact

- Unit tests target domain logic.
- Contract tests target provider adapters.
- Integration tests target the end-to-end slice.
- E2E tests target the UI path after the frontend exists.
