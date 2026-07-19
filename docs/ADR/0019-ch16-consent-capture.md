# ADR 0019: CH-16 Durable Synthetic-Avatar Consent Capture

## Status

Proposed in Issue `#111` for `CH-16` / `MEDIA-CONSENT-001`.

## Context

Stage 7 already required a request-time boolean
`consentToUseSyntheticAvatar`, but that signal was process-local and was not
durable, scoped, auditable, or replay-safe. Phase 1 Closure issue `#39`
requires a narrower contract for synthetic-media consent before later
provenance, disclosure, revocation, retention, and provider-release chunks can
build on top of it.

The scope of this ADR is intentionally narrow:

- durable affirmative consent capture for Stage 7 synthetic local avatar render
  requests
- safe restore and replay of consent records
- Stage 7 render gating against a matching consent record

This ADR does not close or claim:

- consent revocation
- provenance closure
- disclosure closure
- provider release posture
- retention/erasure closure
- untrusted-input closure
- production multi-worker durability

## Decision

Add a dedicated Stage 7 consent-capture operation and durable consent record
model.

The record stores:

- `consent_record_id`
- `tenant_id`
- `project_id`
- `actor_id`
- `source_run_id`
- `trace_id`
- source context-ref and citation hooks
- `source_evaluation_id`
- `source_evaluation_checksum`
- `evaluation_status`
- canonical consent statement version and text
- `granted_at`
- request checksum
- idempotency scope/key linkage
- optional `avatar_render_id`
- bounded artifact checksum hooks

The API path is split into two steps:

1. `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-consents`
   captures or replays a scoped affirmative consent record.
2. `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-renders`
   requires both the request boolean and an explicit durable scope containing a
   matching `consentRecordId`.

Product Mode 1 `CH-M1-01` applies the same two-step durable-consent chain to
the local/mock frontend path. The frontend must call `/avatar-consents` after a
passed source walkthrough/multilingual flow and before `/avatar-renders`, then
send the returned `consentRecordId` in the render request. The render
idempotency seed includes that durable consent identity so the UI no longer
reuses the old boolean-only render request seed.

This frontend repair does not change backend consent semantics, consent
statement text, storage, provider behavior, real audio/video posture, hosted or
public launch posture, Product Mode 2, or production durability/release claims.

Render-time validation checks:

- same tenant
- same project
- same actor
- same source run
- same trace
- same source evaluation ID/checksum
- current canonical consent statement version/text
- unused consent record; a consumed consent row bound to an earlier render is
  invalid for future durable render attempts

Restore-time validation drops:

- malformed or incomplete consent rows
- rows with stale consent statement version/text
- rows whose stored request checksum no longer matches restored scope fields
- rows with malformed or timezone-less `granted_at` timestamps
- rows whose render hook points to a mismatched or missing render
- succeeded consent-idempotency rows whose value record is missing
- running consent-idempotency rows

## Consequences

Positive:

- Stage 7 durable paths no longer trust only a transient request boolean.
- Consent records become reviewable and replay-safe in local file-backed state.
- Later provenance/disclosure chunks can bind to an explicit consent record ID.

Tradeoffs:

- The API contract now requires a prior consent-capture call before durable
  Stage 7 render calls can succeed.
- Consent records are modeled as single-use durable approvals once a successful
  render binds `avatar_render_id` and artifact checksums.
- Current implementation remains local/mock and single-process; this ADR does
  not claim production-grade multi-worker storage semantics.

## Non-Goals

- No consent revocation or takedown logic
- No public-release or provider enablement claims
- No durable deletion or erasure semantics
- No HTML rendering of consent text or restored metadata as trusted content
