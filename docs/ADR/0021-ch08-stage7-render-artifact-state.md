# ADR 0021: CH-08 Stage 7 Render Artifact-State Restore Contract

## Status

Accepted for Phase 1 Closure CH-08 implementation evidence.

## Context

Issue `#119` implements the CH-08 Stage 7 render artifact-state chunk for
`DUR-STAGE7-001`, with issue `#39` remaining open. PR `#116` completed only the
preflight matrix for this chunk.

Stage 7 local JSON restore handles provider output, generated text, artifact
metadata, status history, consent references, and idempotency records. Those
values are untrusted after restart and must be revalidated before they can
re-enter service state.

This decision is limited to local/dev/test restore semantics for the Stage 7
mock/local render path. It does not define production ACID storage, provider
release posture, provenance/disclosure closure, retention/erasure closure, or
untrusted replay closure.

## Decision

Stage 7 restore accepts a render row only when all of these checks pass:

- the render is terminal completed state;
- render status history matches one legal runtime sequence:
  `QUEUED -> RUNNING -> COMPLETED`,
  `QUEUED -> FALLBACK -> RUNNING -> COMPLETED`,
  `QUEUED -> RUNNING -> FAILED -> FALLBACK -> COMPLETED`, or
  `QUEUED -> FALLBACK -> RUNNING -> FAILED -> FALLBACK -> COMPLETED`;
- fallback status history is consistent with provider fallback metadata;
- the persisted render request checksum is present and matches the canonical
  request checksum preimage;
- the source-evaluation checksum matches canonical source evidence;
- render idempotency scope/key are checksum-bound and match restored ownership
  scope when tenant, actor, project, and source run are present;
- artifact metadata is parsed and kept only when it matches a restored render;
- succeeded render and consent idempotency rows replay only when endpoint,
  request checksum, scope, and key match the restored value;
- failed restored Stage 7 idempotency rows are dropped instead of replayed.

The local JSON file is not cryptographic tamper-proofing. A fully rewritten,
self-consistent snapshot remains outside this local restore contract and is left
for later production durability and untrusted-input closure work.

## Consequences

The Stage 7 local restore path rejects malformed, stale, or inconsistent rows
without enabling paid or external providers in local/dev/test.

Legacy restored render rows without `request_checksum` no longer replay. This is
intentional for CH-08 because the invariant requires persisted render checksums.

The implementation adds focused local durability regressions for status-history
replay/rejection, missing or mismatched checksums, cross-scope render and
idempotency rows, failed restored idempotency rows, artifact metadata isolation,
and retained consumed-consent and terminal-persist rollback evidence.

Issue `#39` remains open after this ADR and implementation.
