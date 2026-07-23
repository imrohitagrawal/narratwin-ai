# ADR 0033: Checkpoint 3 Real-Browser Acceptance Evidence

## Status

Accepted for issue `#269`.

## Context

Checkpoint 3A CP8 needs executable evidence that the local/mock controlled-demo
path works through a real browser. Earlier Checkpoint 3A probes cover API E2E,
output correctness, language quality, media artifacts, access/quota/retention,
security/observability, and performance. CP8 adds the missing browser boundary:
the user-visible path must execute without docs-only checks, static snapshots,
API-only substitutes, or success-path route interception.

The repository is public. Browser evidence must therefore avoid raw uploaded
content, prompt-injection text, private-looking markers, sensitive tokens,
provider payloads, generated full script text, real media, and provider output.

## Decision

Use a dedicated Playwright configuration for the CP8 acceptance probe. The
configuration launches the local backend and frontend, forces local/mock
provider posture, clears provider key/state environment variables, and runs the
CP8 browser test only.

The browser test may observe requests and responses, but it must not fabricate
success with `page.route`, `context.route`, `route.fulfill`, HAR replay, or MSW.
The test records bounded public-safe evidence: runtime nonce binding,
browser-observed request sequence, local origin, source/evaluation/run IDs,
artifact metadata, ops/status counts, local/mock provider posture, and
idempotency evidence. The Python acceptance harness independently recomputes
expected idempotency keys from bounded runtime fields and rejects boolean-only
or self-attested fabricated idempotency evidence.

## Boundaries

- This ADR authorizes only local/mock Checkpoint 3A CP8 acceptance evidence.
- It does not authorize Checkpoint 3B, Checkpoint 3C, hosted deployment, public
  URL, provider setup, paid spend, cloned identity, real media, public
  distribution, or production-readiness claims.
- Browser failure output must remain bounded and redacted.
- The CP8 probe must preserve CP1 through CP7 acceptance probes.

## Validation

- `make checkpoint3-acceptance` reports CP1 through CP8 as executable probes.
- `tests/unit/test_checkpoint3_acceptance_gate.py` rejects docs/prose/static,
  API-only, skipped browser, missing artifact, minimal success-shaped,
  boolean-only idempotency, and self-attested idempotency false passes.
- `frontend/tests/checkpoint3-real-browser.spec.ts` drives the local browser UI
  and records bounded runtime evidence without success-path interception.
- `frontend/playwright.checkpoint3.config.ts` launches local services and forces
  local/mock provider posture.
