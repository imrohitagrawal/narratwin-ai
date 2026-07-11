# ADR 0018: CH-03 Stage 4 Durable Graph for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#107`.

## Date

2026-07-11

## Context

Issue `#39` remains open and production release remains No-Go. `CH-02`
completed the ACID/CAS storage kernel, `CH-04` completed idempotency semantics,
and `CH-06` completed committed outbox semantics. `CH-03` is now the next
blocking runtime graph chunk for `DUR-STAGE4-001`.

`CH-03` must prove durable Stage 4 graph semantics without absorbing later
chunks:

- no Stage 6 or Stage 7 durable artifact replay,
- no rollback, restore, metrics, alerts, watch, media, provider, retention, or
  final issue `#39` disposition work,
- no exactly-once side-effect claim,
- no paid-provider enablement or real provider keys.

## Source Facts

| ID | Source | Fact used | Design impact | Status |
|---|---|---|---|---|
| SRC-STAGE4-001 | `docs/ADR/0008-postgresql-durability-schema-boundary.md` | `project`, `document`, `chunk`, `run`, and `evaluation` are the minimum durable production surface for `DUR-STAGE4-001`. | CH-03 durable graph records use those entity types and keep raw uploads/provider outputs outside this chunk. | pass |
| SRC-STAGE4-002 | `docs/ADR/0014-ch02-acid-cas-storage-kernel.md` | The CH-02 kernel owns row versions, transaction identity, replay fingerprints, and atomic multi-row validation. | CH-03 composes graph writes through `AcidCasKernel.commit(...)`; it does not create a second durability store. | pass |
| SRC-STAGE4-003 | `docs/ADR/0015-ch04-idempotency-semantics.md` | Terminal operation replay is read-only and payload-hash guarded. | CH-03 does not replace operation idempotency; it records graph payloads under durable row identities only. | pass |
| SRC-STAGE4-004 | `docs/ADR/0017-ch06-committed-outbox.md` | Outbox events bind to same-transaction durable row versions and are at least once. | CH-03 may emit graph events only through the existing outbox event contract; no exactly-once side effect is claimed. | pass |

## Decision

Add a Stage 4 durable graph adapter on top of the existing storage kernel.

The adapter owns graph validation for:

- project metadata,
- immutable approved document metadata,
- chunk metadata derived from approved documents,
- walkthrough run metadata,
- evaluation and claim-support metadata.

The adapter stores only metadata needed to resume and validate the graph. Raw
uploaded bytes, parsed text buffers, provider prompts, provider outputs,
generated script payloads, and media artifacts remain outside the durable
production boundary for this chunk.

The adapter permits additional approved documents to be appended to an existing
durable project without changing the shared storage kernel. Exact transaction
replay preserves the original create-project write fingerprint; new append
transactions validate the existing project metadata and write only document and
chunk rows. Approved document metadata is terminal to prevent later checksum or
approval timestamp drift from invalidating already-indexed chunks.

Passed evaluations are bounded to the Stage 4 retrieval/evaluation contract:
at least one context ref, at least one claim support, no more than six context
refs, no more than twenty-four generated claims, no more than twenty-four claim
supports, support coverage for every generated claim, and run-completed outbox
payloads of at most 4096 encoded bytes.

## Invariant-To-Test Matrix

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| STAGE4-GRAPH-001 | Project/document/chunk graph | Documents and chunks must share tenant, owner, project, document checksum, source filename, approval timestamp, chunk checksum, and derived metadata; approved document metadata is immutable; additional documents can append to an existing project without mutating the shared kernel. | Durable rows can have valid IDs while a chunk belongs to another document or stale upload; approved document metadata can drift after chunks are indexed; a project can become one-upload-only. | `test_ch03_stage4_graph_commits_project_document_and_chunks_atomically`; `test_ch03_stage4_graph_appends_second_document_to_existing_project`; `test_ch03_stage4_graph_records_approved_document_as_terminal_metadata` | `test_ch03_stage4_graph_rejects_chunk_with_mismatched_document_checksum`; RED proof required before implementation and again after independent review findings. | `uv run pytest tests/unit/test_stage4_durable_graph.py` | Storage + API | pass |
| STAGE4-RUN-001 | Run/evaluation graph | A completed run must bind retrieved context refs, chunks, documents, generated claims, evaluation, and claim supports; passed evaluations require non-empty context/support data and support coverage for every generated claim. | A run can resume with a passing evaluation whose supports point at unrelated chunks or claims, or with no grounded support evidence at all. | `test_ch03_stage4_graph_commits_completed_run_with_evaluation_supports` | `test_ch03_stage4_graph_rejects_passed_evaluation_without_context_refs`; `test_ch03_stage4_graph_rejects_passed_evaluation_without_claim_supports`; `test_ch03_stage4_graph_rejects_generated_claim_without_support`; `test_ch03_stage4_graph_rejects_evaluation_support_for_unknown_context_ref`; RED proof required before implementation and again after independent review findings. | `uv run pytest tests/unit/test_stage4_durable_graph.py` | Storage + API | pass |
| STAGE4-REPLAY-001 | Replay semantics | Exact transaction replay returns the same graph records, while changed graph payloads conflict. | Retried graph writes can silently drift from the first durable graph. | `test_ch03_stage4_graph_replays_exact_transaction` | `test_ch03_stage4_graph_rejects_changed_replay_payload`; RED proof required before implementation. | `uv run pytest tests/unit/test_stage4_durable_graph.py` | Runtime/state | pass |
| STAGE4-BOUNDS-001 | Runtime boundedness | Stage 4 graph validation is bounded by at most six context refs, twenty-four generated claims, twenty-four claim supports, and 4096 encoded bytes for run-completed event payloads. | A production durable graph path can become an unbounded N+1 lookup and serialization hot path. | `test_ch03_stage4_graph_commits_completed_run_with_evaluation_supports` | `test_ch03_stage4_graph_rejects_unbounded_context_refs`; `test_ch03_stage4_graph_rejects_unbounded_generated_claim_ids`; `test_ch03_stage4_graph_rejects_unbounded_claim_supports`; `test_ch03_stage4_graph_bounds_run_completed_event_payload_by_encoded_size`; RED proof required after independent review finding. | `uv run pytest tests/unit/test_stage4_durable_graph.py` | Runtime/performance | pass |
| STAGE4-OUTBOX-001 | Side-effect posture | Graph events, when present, must use CH-06 outbox binding and remain at-least-once. | Stage 4 graph persistence can claim side effects without committed outbox evidence. | `test_ch03_stage4_graph_binds_outbox_event_to_run_version` | `test_ch03_stage4_graph_rejects_outbox_event_without_matching_graph_write`; RED proof required before implementation. | `uv run pytest tests/unit/test_stage4_durable_graph.py` | Runtime/integration | pass |
| NONGOAL-STAGE4-001 | Scope | CH-03 does not implement Stage 6/7 replay, operations, restore, rollback, media, provider, retention, untrusted-input closure, or final `#39` disposition. | A durable graph PR could overclaim production readiness or close `#39`. | N/A | N/A | PR body, status, and reference-only merge wording keep `Refs #39` posture. | Governance | pass |
| HUMAN-STAGE4-001 | Merge wording | Final merge/squash text remains reference-only for `#39`. | CI cannot inspect text typed into the final merge dialog before merge. | N/A | N/A | Human-only owner: repo owner; residual risk accepted for PR only with no issue-closing keyword. | Governance | pass |

## Review Prompt Set

1. Test/false-pass review: verify every `STAGE4-*` row has positive and
   negative coverage that fails before implementation and asserts graph state,
   not private implementation calls.
2. Architecture/shared-state review: verify CH-03 uses the CH-02 kernel and
   preserves CH-04 idempotency, CH-05 lease, and CH-06 outbox semantics without
   adding a parallel store.
3. Security/guardrail review: verify uploaded docs, prompts, retrieved context,
   generated output, and provider/model output stay untrusted; no secrets,
   provider enablement, issue-closing wording, or release overclaim entered the
   diff.
4. Code quality review: verify the adapter is narrow, names match Stage 4
   concepts, and no adjacent chunk files or unrelated cleanup are absorbed.
5. Performance review: verify graph validation is bounded by the supplied graph
   payload and does not introduce unbounded scans in runtime hot paths.

## Stop Rule

Stop implementation and update this ADR before another code patch if review
finds any new defect class in:

- project/document/chunk relationship validation,
- run/evaluation/support binding,
- replay conflict detection,
- outbox event binding,
- issue `#39` reference-only posture,
- or CH-03 scope boundaries.

Two distinct blocker classes after green local checks require a contract reset
and re-review before further implementation.

## Non-Goals

- No Stage 6 multilingual artifact replay.
- No Stage 7 render/artifact/provenance state.
- No SQL driver, external queue, backup/restore, monitoring, dashboard, alert,
  watch, rollback, retention, provider, media, or release enablement.
- No paid-provider calls or real provider keys.
- No issue `#39` closure or `DUR-STAGE4-001` row closure.

## Consequences

Positive:

- `CH-03` gets executable proof for durable Stage 4 graph relationship
  validation and replay behavior.
- Later `CH-07`, `CH-08`, `CH-09`, and `CH-22` chunks can depend on a concrete
  durable Stage 4 graph boundary.

Negative:

- The production release remains No-Go.
- Runtime Stage 6/7 replay, operations, restore, rollback, privacy, provider,
  and final-disposition evidence remain open.

## Related Documents

- `docs/ADR/0008-postgresql-durability-schema-boundary.md`
- `docs/ADR/0014-ch02-acid-cas-storage-kernel.md`
- `docs/ADR/0015-ch04-idempotency-semantics.md`
- `docs/ADR/0016-ch05-lease-fencing.md`
- `docs/ADR/0017-ch06-committed-outbox.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
