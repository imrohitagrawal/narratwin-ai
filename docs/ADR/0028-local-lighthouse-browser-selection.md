# ADR 0028: Local Lighthouse Browser Selection

## Status

Accepted for issue `#181`.

## Context

The local `frontend-lighthouse` gate failed on clean `origin/main` at
`22d48b9edc0338d613d4926059fa9ef1ef329d1f` with Lighthouse `NO_FCP`.
The standalone Next.js server returned nonblank HTML, and a direct Playwright
Chromium render recorded `first-contentful-paint`. The same Lighthouse command
passed when `CHROME_PATH` pointed to the locally installed Google Chrome binary.

Issue `#181` is a prerequisite maintenance fix for local gate reliability before
issue `#155` can resume. It does not change product runtime behavior, launch
level, provider posture, hosted deployment, real audio/video, or production
claims.

## Decision

`scripts/ci/frontend-lighthouse.sh` sets `CHROME_PATH` to the macOS system
Google Chrome binary when it exists and the caller has not already set
`CHROME_PATH`.

`frontend/scripts/run-lighthouse.mjs` honors an existing `CHROME_PATH` and
falls back to Playwright Chromium otherwise. CI and Linux environments without a
system Chrome binary keep the existing Playwright fallback.

## Consequences

- Local macOS runs use the browser path that passed the Lighthouse audit during
  diagnosis.
- CI remains portable because Playwright Chromium is still the fallback.
- Explicit caller-provided `CHROME_PATH` remains authoritative.
- The frontend application and Lighthouse budgets are unchanged.
- Future browser-selection changes must preserve the explicit-path override and
  fallback behavior with tests.
