# ADR 0023: Local Restore-Integrity Drill for DUR-RESTORE-001

## Status

Accepted for issue `#125`; local-only implementation evidence.

## Date

2026-07-12

## Context

Issue `#39` remains open. `DUR-RESTORE-001` still lacks the production restore
evidence required by `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` `CH-14`,
including production backup scope, restore metrics, RTO/RPO proof, and
operations/security review.

The repository does already provide one executable restore surface today:
optional file-backed JSON state for Stage 4, Stage 6, and Stage 7. Those local
state loaders already reject malformed, incomplete, cross-scope, or
checksum-mismatched restored rows before replay.

The narrowest defensible slice we can honestly close now is therefore a
reproducible local drill that:

- seeds representative Stage 4/6/7 file-backed state,
- copies the local state files into a restored directory,
- verifies copied-file integrity,
- rehydrates the services from the restored files,
- proves count parity across the restored services,
- proves replay safety by reissuing the same Stage 4/6/7 idempotent operations
  after restore and observing the original durable identifiers,
- and persists the emitted evidence snapshot so reviewers can inspect the copied
  source and restored JSON state after the command exits.

## Decision

Add an executable local restore drill in
`backend/app/storage/local_restore_drill.py` and expose it through:

```bash
uv run python -m backend.app.storage.local_restore_drill --output outputs/restore-drill.json
```

The drill is intentionally scoped to the existing local file-backed durability
paths only. It does not claim production backup orchestration, storage
operators, cloud snapshots, managed restore services, restore metrics/SLOs, or
watch/alert evidence.

## Restore Contract For This Slice

The drill must prove all of the following in one executable path:

1. Stage 4 local state restores project/document/ingestion/run/idempotency
   state without changing durable identifiers when the drill replays
   `create_project`, `upload_document`, `approve_document`, `ingest_documents`,
   and `generate_walkthrough`.
2. Stage 6 local state restores multilingual result/idempotency/dedupe state
   without producing a second durable run on replay.
3. Stage 7 local state restores consent/render/artifact metadata/idempotency
   state without producing a second durable consent or render on replay.
4. Copied local state files remain byte-identical across source and restored
   directories and remain inspectable in the persisted evidence snapshot.
5. Restored record counts match the seeded record counts before replay.
6. Replayed operations do not increase any Stage 4/6/7 durable record counts
   after restore.

## Non-Goals

- No production `CH-14` closure.
- No backup retention, expiry, or re-delete behavior.
- No restore metrics, SLOs, alerts, dashboards, or first-hour watch.
- No provider posture, retention/erasure, provenance/disclosure, or untrusted
  input closure.
- No claim that issue `#39` or matrix row `DUR-RESTORE-001` is closed.

## Consequences

The repository gains executable local restore evidence that is stronger than the
earlier planning-only ADR `0011`, but it remains explicitly below the
production-grade evidence bar for `DUR-RESTORE-001`.

Residual gap that remains open:

- production backup source/target platform evidence,
- production restore drill timings and RTO/RPO proof,
- restore metric emission and operational review,
- deletion/erasure and untrusted-input restore-time controls,
- and final row closure evidence for issue `#39`.
