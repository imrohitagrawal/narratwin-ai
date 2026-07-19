# ADR 0029: CH-M1-02 Real-Stack Local Evidence Boundary

## Status

Accepted for issue `#208` / issue `#209` consolidated Phase 1 Closure PR.

## Context

The existing frontend Playwright smoke test is valuable mocked browser evidence
because it intercepts `/api/v1/**` and validates UI request order against
fixtures. CH-M1-02 needs a different claim: a real local browser reaches the
Next.js frontend, the frontend proxy reaches the FastAPI backend, and the path
runs inside the local Compose stack.

Issue `#209` is directly coupled because reliable local demo validation depends
on unambiguous Phase 1 Closure quality dispatch on `main`.

## Decision

Add a separate real-stack Playwright config and spec that:

- run only when `NARRATWIN_REAL_STACK=1` is set;
- assume the Compose stack is already running on localhost;
- do not intercept application API routes;
- assert the expected frontend-to-backend API sequence and mock/local artifact
  metadata;
- preserve real media, external providers, hosted/public launch, and production
  release as explicit non-goals.

Plain local `make quality` on `main` dispatches Phase 1 Closure while
StatusStateV1 records `SSV1-MODE` as `phase1-closure`. Stage 8 explicit targets
and non-Phase-1 Stage 8 dispatch remain unchanged.

## Consequences

The normal Playwright smoke remains deterministic and fixture-backed. CH-M1-02
runtime evidence uses an explicit Compose command and evidence artifacts rather
than silently expanding routine CI. Production/public release posture remains
No-Go.
