# ADR 0002: Provider-Agnostic Adapters

## Decision

All external AI, speech, avatar, video, storage, and observability systems must be accessed through interfaces.

## Rationale

Avoid vendor lock-in and allow free/premium execution modes.

## Consequences

- Provider SDKs must stay outside core domain logic.
- Contract tests are mandatory for each adapter.
