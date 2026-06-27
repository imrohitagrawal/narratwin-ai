# Methodology

NarraTwin AI should be built using a **spec-anchored, TDD-driven, vertical-slice AI product development methodology**.

## Principles

- Product strategy before implementation.
- PRD before architecture.
- Architecture before code.
- TDD before production backend logic.
- Vertical slices instead of horizontal skeletons.
- AI evaluation gates for generated outputs.
- Security, privacy, and license review from day one.
- Provider-agnostic interfaces to avoid vendor lock-in.
- Cost tracking and caching from the first usable slice.

## Vertical slice quality bar

Each slice must include:

- working user-facing outcome
- backend tests
- UI smoke validation
- security notes
- observability metadata
- docs update
- reviewer pass
- known limitations
