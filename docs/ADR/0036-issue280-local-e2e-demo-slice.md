# ADR 0036: Issue 280 Local E2E Demo Slice

## Status

Accepted for issue `#280` PR C.

## Context

PR A locked the issue `#280` requirement matrix and PR B added the bounded
synthetic markdown input/API/error contract. The next slice needs executable
local/mock evidence for arbitrary public-safe synthetic markdown without
claiming hosted/public demo behavior, provider setup, paid spend, real media,
cloned identity runtime, arbitrary real-world quality, provider quality, or
production readiness.

## Decision

Add an issue-specific API facade at
`/api/v1/checkpoint3/issue280/local-e2e-demo`. The endpoint reuses the PR B
request model, limits, provider posture, and error taxonomy, then runs a
deterministic local/mock service that:

- creates a synthetic local demo session;
- derives deterministic chunks/facts from already validated markdown;
- retrieves local context refs;
- generates citation-bound walkthrough text;
- creates narrow local/mock multilingual segments for `en`, `hi`, and `es`;
- evaluates generated claims against retrieved facts;
- stores generated output and evaluation metadata in resettable in-memory
  issue-specific storage.

The response exposes checksums, context refs, claim-support IDs, request trace
metadata, and provider-disabled posture. It does not return full raw markdown in
the response and never returns raw submitted content in error bodies.

## Consequences

This gives PR C executable API evidence for the local end-to-end demo slice
without coupling unfinished issue `#280` behavior into the Stage 4, Stage 6, or
Stage 7 service contracts. The final `make issue280-output-correctness` flow,
exact UI/browser evidence, export parity, hosted/public demo behavior, real
providers, real media, cloned identity runtime, public distribution, arbitrary
real-world quality, provider quality, and production-readiness claims remain
out of scope.

The issue-specific service is reset by `reset_app_state_for_tests()` and is not
a production persistence model.
