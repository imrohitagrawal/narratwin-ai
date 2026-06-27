# ADR 0001: Architecture Approach

## Decision

Use a modular provider-agnostic architecture with FastAPI backend, Next.js frontend, local-first storage, and explicit provider interfaces.

## Rationale

The product must support free engineering mode and optional premium showcase mode without rewriting core logic.

## Consequences

- More interfaces up front.
- Easier provider replacement.
- Better testing via mocks/fakes.
