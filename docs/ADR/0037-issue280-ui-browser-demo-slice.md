# ADR 0037: Issue 280 UI Browser Demo Slice

## Status

Accepted for issue `#280` PR D.

## Context

PR C added the local/mock API facade at
`/api/v1/checkpoint3/issue280/local-e2e-demo`. PR D needs exact user-visible
browser evidence for that facade without changing the backend contract or
claiming the final issue `#280` output-correctness closure gate.

The existing frontend page already drives the broader Stage 4, Stage 6, and
Stage 7 local avatar export flow. Feeding the PR C response into that flow would
blur contracts because PR C returns issue-specific nested fields and no Stage
6/7 artifact bundle.

## Decision

Add a narrow Issue 280 UI adapter inside the existing frontend page. The adapter
posts the PR B/PR C request shape directly to
`/api/v1/checkpoint3/issue280/local-e2e-demo` and renders only display fields
from the PR C response:

- accepted script text from `generated.acceptedScriptText`;
- transcript segments from `multilingual.segments`;
- citations and context refs from `retrieval.contextRefs`;
- claim support and evaluation metadata from `evaluation.claimSupports`;
- session, storage, replay, and request trace metadata;
- local/mock provider-disabled posture.

The adapter does not pass PR C output into the existing Stage 6/7 artifact or
avatar render flows. A dedicated Playwright config launches local backend and
frontend services, uses desktop and mobile browser projects, observes the
actual request/response path without success-path interception, disables
committed Playwright trace zips, and stores only public-safe local evidence
artifacts under ignored `reports/` paths.

## Consequences

PR D can prove the exact user-visible browser slice while preserving the PR C
backend API contract. The existing Stage 4/6/7 UI path remains available and
its browser probe continues to pass with distinct accessible names for the new
Issue 280 controls.

The final `make issue280-output-correctness` flow, export/API/stored report
parity, hosted/public demo behavior, provider setup, paid spend, real provider
calls, real media, cloned identity runtime, public distribution, arbitrary
real-world quality, provider quality, and production-readiness claims remain
out of scope. Issues `#249` and `#280` remain open after PR D unless all
remaining R280 rows are later satisfied with executable evidence or
reviewed/re-scoped.
