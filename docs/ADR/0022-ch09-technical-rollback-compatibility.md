# ADR 0022: CH-09 Technical Rollback Compatibility for Issue #39

## Status

Accepted for implementation in Phase 1 Closure issue `#123`.

## Date

2026-07-12

## Context

Issue `#39` remains open and production release remains No-Go. `CH-01`,
`CH-02`, and `CH-03` are already merged, so `CH-09` is now the next unblocked
release-safety chunk for `DUR-ROLLBACK-001`.

This chunk must prove one narrow claim and reject the unsafe alternative:

- previous code may run against expanded durable metadata only when
  compatibility is explicit and test-proven;
- otherwise rollback is blocked until a bounded forward repair restores
  compatibility;
- no default down-migration safety claim is allowed.

## Source Facts

| ID | Source | Fact used | Design impact | Status |
|---|---|---|---|---|
| SRC-RBK-001 | `docs/ADR/0010-context3-migrations-rollback-compatibility.md` | Rollback is valid only when the previous deploy can safely read expanded metadata inside a declared compatibility window. | CH-09 adds explicit compatibility-window checks before rollback can be claimed safe. | pass |
| SRC-RBK-002 | `docs/ADR/0013-ch01-migration-baseline-runner.md` | The migration runner already encodes expand-first and forward-only posture but does not close rollback compatibility. | CH-09 extends the migration-layer contract instead of inventing a separate rollback ledger. | pass |
| SRC-RBK-003 | `docs/ADR/0018-ch03-stage4-durable-graph.md` | Later durable graph chunks depend on durable metadata remaining replay-safe across release transitions. | CH-09 treats missing legacy fields or unproven schema windows as rollback blockers, not warnings. | pass |

## Decision

Add a narrow rollback-compatibility contract to `backend/app/storage/migrations.py`.
The contract is persisted alongside the migration runner ledger and evaluated
through runner-level rollback preflight helpers; it is still not a production
rollback orchestrator.

### 1. Expanded schema state must carry an explicit compatibility window

Rollback evaluation uses a typed `RollbackSchemaState` with:

- `schema_version`
- `compatibility_window_floor`
- `compatibility_window_ceiling`
- durable metadata payload
- applied migration revision ledger
- reviewed compatibility proof reference
- proof-bearing revision id

Compatibility is not inferred from additive fields alone. It must be declared.
The migration runner now persists and reloads this state under the same durable
migration ledger, so rollback proof is not only an in-memory helper fixture.

### 2. Previous code must declare the schema window and legacy fields it needs

Rollback evaluation uses a typed `PreviousCodeCompatibility` contract with:

- previous code version
- supported schema-version floor and ceiling
- required legacy payload fields
- optional rollback-blocking fields
- required reviewed compatibility proof reference
- required proof-bearing revision id

If any required legacy field is missing, or if the previous code falls outside
either compatibility window, rollback is blocked.

### 3. Unsafe rollback fails closed behind a reviewed proof-source boundary

`assert_previous_code_rollback_safe(...)` raises `UnsafeRollbackError` when
compatibility cannot be proven. The error is intentionally explicit that
rollback remains blocked until forward repair completes.

The low-level compatibility check still consumes a `TrustedRollbackProof`
value, but the runner-side safe path now resolves that proof from an
out-of-band reviewed proof source keyed by proof reference and proof-bearing
revision id. Persisted expanded metadata alone is not enough to satisfy the
runner preflight. The expanded state cannot certify its own proof reference,
proof revision, applied revision ledger, or payload fingerprint.

This is a reviewed proof-source boundary, not a production-grade independent
trust root. CH-09 does not add signed release manifests, external trust
services, or deployment-orchestration guarantees.

### 4. Forward repair restores compatibility without claiming destructive rollback

`apply_forward_repair(...)` may materialize legacy-compatible fields and reopen
the declared compatibility window floor for the restored previous code version.
It does not widen the compatibility ceiling, and it must produce a repaired
state that immediately passes the rollback-safe assertion against a reviewed
proof-source entry before the repair is accepted.

Forward repair in this chunk:

- does not lower the durable `schema_version`
- does not claim DDL reversal
- does not imply exact down-migration support

### 5. Down-migration support remains disabled in CH-09

This chunk does not implement or certify down-migration support.
`down_migration_supported` remains `False` even when rollback compatibility is
otherwise proven, so CH-09 cannot overclaim destructive downgrade safety.

## Invariant-To-Test Matrix

| ID | Area | Invariant | Old failure / false-pass risk | Positive test | Negative / mutation test | Evidence | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| `RBK-COMPAT-001` | Previous-code compatibility | Previous code is treated as rollback-safe only when the expanded schema stays inside both declared version windows, binds to a reviewed compatibility proof in the applied migration ledger, and still carries the typed legacy fields that older code needs. | Additive schema changes can look harmless while silently dropping fields or proof bindings the previous deploy still requires. | `test_context3_previous_code_runs_against_backward_compatible_expanded_schema` | `test_context3_rollback_blocks_when_required_legacy_field_is_missing`; `test_context3_rollback_blocks_when_required_legacy_field_has_wrong_type`; `test_context3_rollback_blocks_when_required_legacy_int_field_is_boolean`; `test_context3_rollback_blocks_when_proof_reference_or_revision_mismatch`; `test_context3_rollback_blocks_when_proof_revision_missing_from_trusted_ledger`; `test_context3_rollback_blocks_when_state_proof_is_not_trusted` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/ADR/0010-context3-migrations-rollback-compatibility.md` | Platform/storage | pass |
| `RBK-BLOCK-001` | Unsafe rollback block | Rollback raises an explicit block when compatibility cannot be proven. | Release logic can misread incomplete compatibility evidence as a soft warning and still roll back. | `test_context3_rollback_blocks_when_unsafe_without_repair`; `test_ch09_runner_asserts_persisted_previous_code_rollback_safety_from_reviewed_proof_source` | mutate compatibility floor or remove the legacy field and prove the block fires | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` | Release safety | pass |
| `RBK-TRUST-001` | Reviewed proof source boundary | Runner-side rollback preflight resolves reviewed proof entries from an out-of-band proof source, so restored durable metadata cannot satisfy the trusted path by self-attestation alone. | Persisted rollback metadata can be internally consistent while still being reconstructed from tampered restored state. | `test_ch09_runner_asserts_persisted_previous_code_rollback_safety_from_reviewed_proof_source`; `test_context3_forward_repair_restores_rollback_compatibility_from_reviewed_proof_source` | `test_ch09_runner_blocks_when_reviewed_proof_source_entry_is_missing`; `test_ch09_runner_rejects_self_attested_proof_reconstructed_from_persisted_metadata`; `test_ch09_runner_rejects_reviewed_proof_source_payload_fingerprint_mismatch` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` | Platform/storage + release | pass |
| `RBK-REPAIR-001` | Forward repair | Forward repair can restore the required typed legacy field path, record a new reviewed repair revision, and reopen the compatibility window for the previous code version without destructive rollback. | Repair can backfill data but still leave the previous deploy outside the allowed compatibility window or without reviewed proof. | `test_context3_forward_repair_restores_rollback_compatibility` | `test_context3_forward_repair_requires_material_change_before_widening_window`; `test_context3_forward_repair_requires_new_reviewed_repair_revision`; `test_context3_forward_repair_does_not_widen_compatibility_ceiling`; `test_context3_forward_repair_blocks_when_repaired_payload_is_still_incompatible` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; `docs/ADR/0010-context3-migrations-rollback-compatibility.md` | Platform/storage + release | pass |
| `RBK-WINDOW-001` | Schema/window enforcement | Schema-version floors and ceilings plus compatibility-window bounds are enforced before rollback compatibility is claimed. | A newer expanded schema can slip past rollback checks because only one side of the window is validated. | `test_context3_previous_code_runs_against_backward_compatible_expanded_schema` | `test_context3_schema_version_and_compatibility_window_enforced`; `test_context3_schema_version_support_window_rejects_newer_expanded_schema` | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py` | Platform/storage | pass |
| `RBK-NODOWN-001` | No false down-migration claim | Down-migration support remains false throughout CH-09. | Reviewers can mistake rollback compatibility for full down-migration support. | `test_context3_no_false_down_migration_support_without_tested_path` | supply a down-migration marker and prove the result still stays false | `uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py`; human review of PR wording | Release safety + governance | pass |

## Non-Goals

- No SQL DDL, migration execution, or production rollout orchestration.
- No Stage 4/6/7 runtime replay changes.
- No CH-10 metrics, CH-11 SLOs, CH-12 alerts, CH-13 watch, CH-14 restore, or
  CH-15 rollback communications work.
- No claim that `DUR-ROLLBACK-001` or issue `#39` is closed.

## Consequences

Positive:

- `CH-09` gets executable proof for compatibility-window enforcement,
  runner-persisted rollback evidence, reviewed proof-source boundary
  enforcement, and forward-repair posture.
- Release review can distinguish safe rollback from blocked rollback using one
  typed contract plus a runner-level persisted preflight.

Negative:

- This chunk still does not provide production rollback orchestration or
  rollback communications.
- This chunk models a reviewed proof-source boundary but does not provide a
  production independent trust root.
- Down-migration remains unimplemented by default.

## Related Documents

- `docs/ADR/0010-context3-migrations-rollback-compatibility.md`
- `docs/ADR/0013-ch01-migration-baseline-runner.md`
- `docs/ADR/0018-ch03-stage4-durable-graph.md`
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md`
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md`
- `tests/unit/test_storage_migrations.py`
