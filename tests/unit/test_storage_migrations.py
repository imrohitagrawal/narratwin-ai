from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path

import pytest

from backend.app.storage.migrations import (
    ForwardRepairField,
    ForwardRepairPlan,
    MigrationContext,
    MigrationRegistryError,
    MigrationRevision,
    MigrationRunner,
    MigrationStateError,
    PayloadFieldRequirement,
    PreviousCodeCompatibility,
    RollbackSchemaState,
    TrustedRollbackProof,
    TrustedRollbackProofLedger,
    UnsafeRollbackError,
    apply_forward_repair,
    apply_forward_repair_from_ledger,
    assert_previous_code_rollback_safe,
)


def test_ch01_runner_applies_ordered_expand_only_migrations(tmp_path: Path) -> None:
    events: list[str] = []
    context = MigrationContext(state={"tables": []})
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_append_table("schema_migrations", events),
            ),
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Add transition audit table.",
                apply=_append_table("project_state_transition", events),
            ),
        ],
        state_path=tmp_path / "migration-state.json",
    )

    result = runner.run(context=context)

    assert [record.revision_id for record in result.applied] == ["20260711_01", "20260711_02"]
    assert result.current_revision == "20260711_02"
    assert context.state["tables"] == ["schema_migrations", "project_state_transition"]
    assert events == ["schema_migrations", "project_state_transition"]


def test_ch01_runner_rejects_unknown_or_out_of_order_dependency(tmp_path: Path) -> None:
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Depends on a missing earlier revision.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Out of order in the registry.",
                apply=_noop,
            ),
        ],
        state_path=tmp_path / "migration-state.json",
    )

    with pytest.raises(MigrationRegistryError, match="ordered"):
        runner.run(context=MigrationContext())


def test_ch01_runner_rejects_duplicate_revision_ids(tmp_path: Path) -> None:
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="First revision.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260711_01",
                down_revision="20260711_01",
                phase="expand",
                description="Duplicate revision id.",
                apply=_noop,
            ),
        ],
        state_path=tmp_path / "migration-state.json",
    )

    with pytest.raises(MigrationRegistryError, match="Duplicate revision"):
        runner.run(context=MigrationContext())


def test_ch01_runner_does_not_record_failed_revision_as_applied(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Fails before apply completes.",
                apply=_raise_runtime_error,
            )
        ],
        state_path=state_path,
    )

    with pytest.raises(RuntimeError, match="boom"):
        runner.run(context=MigrationContext())

    restored = MigrationRunner(revisions=[], state_path=state_path).load_applied()
    assert restored == []


def test_ch01_runner_preserves_last_good_revision_when_a_later_revision_fails(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    context = MigrationContext(state={"tables": []})
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_append_table("schema_migrations"),
            ),
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Fails after the first revision is already durable.",
                apply=_raise_runtime_error,
            ),
        ],
        state_path=state_path,
    )

    with pytest.raises(RuntimeError, match="boom"):
        runner.run(context=context)

    restored = MigrationRunner(revisions=[], state_path=state_path).load_applied()

    assert [record.revision_id for record in restored] == ["20260711_01"]
    assert context.state["tables"] == ["schema_migrations"]


def test_ch01_runner_is_idempotent_for_already_applied_revisions(tmp_path: Path) -> None:
    context = MigrationContext(state={"tables": []})
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_append_table("schema_migrations"),
            )
        ],
        state_path=tmp_path / "migration-state.json",
    )

    first = runner.run(context=context)
    second = runner.run(context=context)

    assert [record.revision_id for record in first.applied] == ["20260711_01"]
    assert second.applied == ()
    assert second.current_revision == "20260711_01"
    assert context.state["tables"] == ["schema_migrations"]


def test_ch01_runner_rejects_tampered_current_revision_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_02",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_01",
                        "down_revision": None,
                        "phase": "expand",
                        "description": "Create schema version ledger.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = MigrationRunner(revisions=[], state_path=state_path)

    with pytest.raises(MigrationStateError, match="currentRevision"):
        runner.load_applied()


def test_ch01_runner_rejects_unreadable_json_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text("{", encoding="utf-8")

    runner = MigrationRunner(revisions=[], state_path=state_path)

    with pytest.raises(MigrationStateError, match="unreadable"):
        runner.load_applied()


def test_ch01_runner_rejects_tampered_metadata_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_01",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_01",
                        "down_revision": None,
                        "phase": "contract",
                        "description": "Tampered metadata.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )

    with pytest.raises(MigrationStateError, match="phase does not match"):
        runner.run(context=MigrationContext())


def test_ch01_runner_rejects_tampered_applied_prefix_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_02",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_02",
                        "down_revision": "20260711_01",
                        "phase": "expand",
                        "description": "Out-of-order persisted revision.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Add transition audit table.",
                apply=_noop,
            ),
        ],
        state_path=state_path,
    )

    with pytest.raises(MigrationStateError, match="declared registry order"):
        runner.run(context=MigrationContext())


def test_ch01_runner_rejects_contract_migrations_without_explicit_opt_in(tmp_path: Path) -> None:
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="contract",
                description="Drops a compatibility column.",
                apply=_noop,
            )
        ],
        state_path=tmp_path / "migration-state.json",
    )

    with pytest.raises(MigrationRegistryError, match="contract migrations require explicit opt-in"):
        runner.run(context=MigrationContext())


def test_ch09_runner_persists_and_loads_rollback_compatibility(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())
    rollback_state = _rollback_state(
        payload={"request_checksum": "req-123"},
        proof_reference="CTX3-ROLLBACK-EVID-001",
        proof_revision_id="20260711_01",
        applied_revision_ids=("20260711_01",),
    )

    runner.persist_rollback_compatibility(rollback_state)

    restored = runner.load_rollback_compatibility()

    assert restored == rollback_state


def test_ch09_runner_asserts_persisted_previous_code_rollback_safety_from_reviewed_proof_source(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())
    runner.persist_rollback_compatibility(
        _rollback_state(
            payload={"request_checksum": "req-123"},
            proof_reference="CTX3-ROLLBACK-EVID-001",
            proof_revision_id="20260711_01",
            applied_revision_ids=("20260711_01",),
        )
    )

    result = runner.assert_persisted_previous_code_rollback_safe(
        previous_code=_previous_code(
            required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
            required_proof_revision_id="20260711_01",
        ),
        trusted_proof_ledger=_trusted_proof_ledger(
            _trusted_proof(
                applied_revision_ids=("20260711_01",),
                proof_reference="CTX3-ROLLBACK-EVID-001",
                proof_revision_id="20260711_01",
                payload={"request_checksum": "req-123"},
            )
        ),
    )

    assert result.compatible is True


def test_ch09_runner_rejects_rollback_compatibility_with_mismatched_applied_ledger(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())

    with pytest.raises(MigrationStateError, match="must match the persisted applied migration ledger"):
        runner.persist_rollback_compatibility(
            _rollback_state(
                payload={"request_checksum": "req-123"},
                proof_reference="CTX3-ROLLBACK-EVID-001",
                proof_revision_id="20260711_01",
                applied_revision_ids=("20260711_01", "20260712_expand_checksum"),
            )
        )


def test_ch09_runner_drops_stale_rollback_compatibility_when_new_migration_applies(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())
    runner.persist_rollback_compatibility(
        _rollback_state(
            payload={"request_checksum": "req-123"},
            proof_reference="CTX3-ROLLBACK-EVID-001",
            proof_revision_id="20260711_01",
            applied_revision_ids=("20260711_01",),
        )
    )

    advanced_runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260712_02",
                down_revision="20260711_01",
                phase="expand",
                description="Add rollback metadata proof anchor.",
                apply=_noop,
            ),
        ],
        state_path=state_path,
    )

    advanced_runner.run(context=MigrationContext())

    assert advanced_runner.load_rollback_compatibility() is None


def test_ch09_runner_rejects_boolean_rollback_window_fields(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_01",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_01",
                        "down_revision": None,
                        "phase": "expand",
                        "description": "Create schema version ledger.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
                "rollbackCompatibility": {
                    "schemaVersion": True,
                    "compatibilityWindowFloor": 1,
                    "compatibilityWindowCeiling": 2,
                    "appliedRevisionIds": ["20260711_01"],
                    "compatibilityProofReference": "CTX3-ROLLBACK-EVID-001",
                    "proofRevisionId": "20260711_01",
                    "payload": {"request_checksum": "req-123"},
                    "downMigrationRevision": None,
                },
            }
        ),
        encoding="utf-8",
    )
    runner = MigrationRunner(revisions=[], state_path=state_path)

    with pytest.raises(MigrationStateError, match="schemaVersion must be an integer"):
        runner.load_rollback_compatibility()


def test_ch09_runner_blocks_when_persisted_rollback_compatibility_is_missing(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())

    with pytest.raises(UnsafeRollbackError, match="persisted rollback compatibility is missing"):
        runner.assert_persisted_previous_code_rollback_safe(
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260711_01",
            ),
            trusted_proof_ledger=_trusted_proof_ledger(
                _trusted_proof(
                    applied_revision_ids=("20260711_01",),
                    proof_revision_id="20260711_01",
                    payload={"request_checksum": "req-123"},
                )
            ),
        )


def test_ch09_runner_rejects_tampered_persisted_rollback_compatibility_ledger_on_read(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_01",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_01",
                        "down_revision": None,
                        "phase": "expand",
                        "description": "Create schema version ledger.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
                "rollbackCompatibility": {
                    "schemaVersion": 2,
                    "compatibilityWindowFloor": 1,
                    "compatibilityWindowCeiling": 2,
                    "appliedRevisionIds": ["20260711_01", "20260712_expand_checksum"],
                    "compatibilityProofReference": "CTX3-ROLLBACK-EVID-001",
                    "proofRevisionId": "20260712_expand_checksum",
                    "payload": {"request_checksum": "req-123"},
                    "downMigrationRevision": None,
                },
            }
        ),
        encoding="utf-8",
    )
    runner = MigrationRunner(revisions=[], state_path=state_path)

    with pytest.raises(MigrationStateError, match="does not match the persisted applied migration ledger"):
        runner.load_rollback_compatibility()


def test_ch09_runner_blocks_when_reviewed_proof_source_entry_is_missing(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())
    runner.persist_rollback_compatibility(
        _rollback_state(
            payload={"request_checksum": "req-123"},
            proof_reference="CTX3-ROLLBACK-EVID-001",
            proof_revision_id="20260711_01",
            applied_revision_ids=("20260711_01",),
        )
    )

    with pytest.raises(UnsafeRollbackError, match="reviewed rollback proof source is missing entry"):
        runner.assert_persisted_previous_code_rollback_safe(
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260711_01",
            ),
            trusted_proof_ledger=_trusted_proof_ledger(),
        )


def test_ch09_runner_rejects_self_attested_proof_reconstructed_from_persisted_metadata(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())
    runner.persist_rollback_compatibility(
        _rollback_state(
            payload={"request_checksum": "req-123"},
            proof_reference="CTX3-ROLLBACK-EVID-001",
            proof_revision_id="20260711_01",
            applied_revision_ids=("20260711_01",),
        )
    )
    restored = runner.load_rollback_compatibility()
    assert restored is not None
    self_attested_proof = TrustedRollbackProof(
        applied_revision_ids=restored.applied_revision_ids,
        compatibility_proof_reference=restored.compatibility_proof_reference,
        proof_revision_id=restored.proof_revision_id,
        payload_fingerprint=_payload_fingerprint(restored.payload),
    )

    with pytest.raises(UnsafeRollbackError, match="reviewed rollback proof source is missing entry"):
        runner.assert_persisted_previous_code_rollback_safe(
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260711_01",
            ),
            trusted_proof_ledger=_trusted_proof_ledger(),
        )

    assert self_attested_proof.compatibility_proof_reference == restored.compatibility_proof_reference


def test_ch09_runner_rejects_reviewed_proof_source_payload_fingerprint_mismatch(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )
    runner.run(context=MigrationContext())
    runner.persist_rollback_compatibility(
        _rollback_state(
            payload={"request_checksum": "req-123"},
            proof_reference="CTX3-ROLLBACK-EVID-001",
            proof_revision_id="20260711_01",
            applied_revision_ids=("20260711_01",),
        )
    )

    with pytest.raises(UnsafeRollbackError, match="payload fingerprint"):
        runner.assert_persisted_previous_code_rollback_safe(
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260711_01",
            ),
            trusted_proof_ledger=_trusted_proof_ledger(
                _trusted_proof(
                    applied_revision_ids=("20260711_01",),
                    proof_reference="CTX3-ROLLBACK-EVID-001",
                    proof_revision_id="20260711_01",
                    payload={"request_checksum": "different"},
                )
            ),
        )


def test_context3_previous_code_runs_against_backward_compatible_expanded_schema() -> None:
    state = _rollback_state(
        payload={
            "request_checksum": "req-123",
            "resource_version": 4,
            "expanded_field": "safe additive metadata",
        }
    )
    trusted_proof = _trusted_proof(payload=state.payload)

    result = assert_previous_code_rollback_safe(
        previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
        state=state,
        trusted_proof=trusted_proof,
    )

    assert result.compatible is True
    assert result.reason is None
    assert result.down_migration_supported is False


def test_context3_rollback_blocks_when_unsafe_without_repair() -> None:
    state = _rollback_state(
        compatibility_window_floor=2,
        payload={"request_hash_v2": "req-123"},
    )

    with pytest.raises(UnsafeRollbackError, match="Rollback blocked until forward repair completes"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_forward_repair_restores_rollback_compatibility() -> None:
    previous_code = _previous_code(
        required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
        required_proof_revision_id="20260712_forward_repair_checksum",
    )
    trusted_proof = _trusted_proof(
        applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_forward_repair_checksum"),
        proof_reference="CTX3-ROLLBACK-EVID-001",
        proof_revision_id="20260712_forward_repair_checksum",
        payload={"request_hash_v2": "req-123", "request_checksum": "req-123"},
    )
    state = _rollback_state(
        compatibility_window_floor=2,
        payload={"request_hash_v2": "req-123"},
        proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
    )
    repaired = apply_forward_repair(
        state=state,
        repair=ForwardRepairPlan(
            repair_id="repair-request-checksum",
            repair_revision_id="20260712_forward_repair_checksum",
            restores_code_version=1,
            updated_compatibility_proof_reference="CTX3-ROLLBACK-EVID-001",
            field_repairs=(
                ForwardRepairField(target_field="request_checksum", source_field="request_hash_v2"),
            ),
        ),
        previous_code=previous_code,
        trusted_proof=trusted_proof,
    )

    result = assert_previous_code_rollback_safe(
        previous_code=previous_code,
        state=repaired,
        trusted_proof=trusted_proof,
    )

    assert repaired.payload["request_checksum"] == "req-123"
    assert repaired.compatibility_window_floor == 1
    assert repaired.compatibility_window_ceiling == 2
    assert repaired.proof_revision_id == "20260712_forward_repair_checksum"
    assert result.compatible is True


def test_context3_forward_repair_restores_rollback_compatibility_from_reviewed_proof_source() -> None:
    previous_code = _previous_code(
        required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
        required_proof_revision_id="20260712_forward_repair_checksum",
    )
    ledger = _trusted_proof_ledger(
        _trusted_proof(
            applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_forward_repair_checksum"),
            proof_reference="CTX3-ROLLBACK-EVID-001",
            proof_revision_id="20260712_forward_repair_checksum",
            payload={"request_hash_v2": "req-123", "request_checksum": "req-123"},
        )
    )
    repaired = apply_forward_repair_from_ledger(
        state=_rollback_state(
            compatibility_window_floor=2,
            payload={"request_hash_v2": "req-123"},
            proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
        ),
        repair=ForwardRepairPlan(
            repair_id="repair-request-checksum",
            repair_revision_id="20260712_forward_repair_checksum",
            restores_code_version=1,
            updated_compatibility_proof_reference="CTX3-ROLLBACK-EVID-001",
            field_repairs=(ForwardRepairField(target_field="request_checksum", source_field="request_hash_v2"),),
        ),
        previous_code=previous_code,
        trusted_proof_ledger=ledger,
    )

    assert repaired.compatibility_window_floor == 1
    assert repaired.proof_revision_id == "20260712_forward_repair_checksum"


def test_context3_schema_version_and_compatibility_window_enforced() -> None:
    state = _rollback_state(
        compatibility_window_floor=2,
        payload={"request_checksum": "req-123"},
    )

    with pytest.raises(UnsafeRollbackError, match="previous code version 1 is outside the expanded-schema compatibility window 2-2"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_schema_version_support_window_rejects_newer_expanded_schema() -> None:
    state = _rollback_state(
        schema_version=3,
        compatibility_window_ceiling=3,
        applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_expand_v3"),
        payload={"request_checksum": "req-123"},
        proof_revision_id="20260712_expand_v3",
    )
    trusted_proof = _trusted_proof(
        applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_expand_v3"),
        proof_revision_id="20260712_expand_v3",
    )

    with pytest.raises(UnsafeRollbackError, match="schema version 3 is outside the previous-code support window 1-2"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                max_supported_schema_version=2,
                required_proof_revision_id="20260712_expand_v3",
            ),
            state=state,
            trusted_proof=trusted_proof,
        )


def test_context3_no_false_down_migration_support_without_tested_path() -> None:
    state = _rollback_state(payload={"request_checksum": "req-123"}, down_migration_revision="20260712_rollback")

    result = assert_previous_code_rollback_safe(
        previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
        state=state,
        trusted_proof=_trusted_proof(),
    )

    assert result.compatible is True
    assert result.down_migration_supported is False


def test_context3_rollback_blocks_when_required_legacy_field_has_wrong_type() -> None:
    state = _rollback_state(payload={"request_checksum": {"unexpected": "object"}})

    with pytest.raises(UnsafeRollbackError, match="request_checksum"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_rollback_blocks_when_required_legacy_int_field_is_boolean() -> None:
    state = _rollback_state(payload={"resource_version": True})

    with pytest.raises(UnsafeRollbackError, match="resource_version"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("resource_version", "int"),)),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_rollback_blocks_when_required_legacy_field_is_missing() -> None:
    state = _rollback_state(payload={"request_hash_v2": "req-123"})

    with pytest.raises(UnsafeRollbackError, match="request_checksum"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_rollback_blocks_when_proof_revision_missing_from_trusted_ledger() -> None:
    state = _rollback_state(payload={"request_checksum": "req-123"})

    with pytest.raises(UnsafeRollbackError, match="trusted applied ledger"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(applied_revision_ids=("20260711_01",), proof_revision_id="20260712_expand_checksum"),
        )


def test_context3_rollback_blocks_when_state_proof_revision_is_missing_from_state_ledger() -> None:
    state = _rollback_state(
        applied_revision_ids=("20260711_01",),
        proof_revision_id="20260712_expand_checksum",
        payload={"request_checksum": "req-123"},
    )

    with pytest.raises(MigrationStateError, match="must exist in the applied migration ledger"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(applied_revision_ids=("20260711_01",), proof_revision_id="20260712_expand_checksum"),
        )


def test_context3_forward_repair_requires_material_change_before_widening_window() -> None:
    previous_code = _previous_code(
        required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
        required_proof_revision_id="20260712_forward_repair_noop",
    )
    trusted_proof = _trusted_proof(
        applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_forward_repair_noop"),
        proof_revision_id="20260712_forward_repair_noop",
    )
    state = _rollback_state(
        compatibility_window_floor=2,
        payload={"request_checksum": "already-present"},
        proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
    )

    with pytest.raises(UnsafeRollbackError, match="material compatibility change"):
        apply_forward_repair(
            state=state,
            repair=ForwardRepairPlan(
                repair_id="noop-repair",
                repair_revision_id="20260712_forward_repair_noop",
                restores_code_version=1,
                updated_compatibility_proof_reference="CTX3-ROLLBACK-EVID-001",
                field_repairs=(ForwardRepairField(target_field="request_checksum"),),
            ),
            previous_code=previous_code,
            trusted_proof=trusted_proof,
        )


def test_context3_forward_repair_requires_new_reviewed_repair_revision() -> None:
    state = _rollback_state(
        compatibility_window_floor=2,
        payload={"request_hash_v2": "req-123"},
        proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
    )

    with pytest.raises(UnsafeRollbackError, match="new reviewed repair revision id"):
        apply_forward_repair(
            state=state,
            repair=ForwardRepairPlan(
                repair_id="reuse-existing-revision",
                repair_revision_id="20260712_expand_checksum",
                restores_code_version=1,
                updated_compatibility_proof_reference="CTX3-ROLLBACK-EVID-001",
                field_repairs=(ForwardRepairField(target_field="request_checksum", source_field="request_hash_v2"),),
            ),
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
            ),
            trusted_proof=_trusted_proof(
                applied_revision_ids=("20260711_01", "20260712_expand_checksum"),
                proof_reference="CTX3-ROLLBACK-EVID-001",
                proof_revision_id="20260712_expand_checksum",
                payload={"request_hash_v2": "req-123", "request_checksum": "req-123"},
            ),
        )


def test_context3_rollback_blocks_when_proof_reference_or_revision_mismatch() -> None:
    state = _rollback_state(
        payload={"request_checksum": "req-123"},
        proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
    )

    with pytest.raises(UnsafeRollbackError, match="compatibility proof reference"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(
                code_version=3,
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260712_forward_repair_checksum",
            ),
            state=state,
            trusted_proof=_trusted_proof(
                applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_forward_repair_checksum"),
                proof_revision_id="20260712_forward_repair_checksum",
            ),
        )


def test_context3_rollback_blocks_when_state_proof_is_not_trusted() -> None:
    state = _rollback_state(
        payload={"request_checksum": "req-123"},
        proof_reference="CTX3-ROLLBACK-EVID-TAMPERED-001",
    )

    with pytest.raises(UnsafeRollbackError, match="trusted rollback proof"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),)),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_rollback_blocks_when_blocked_payload_field_is_present() -> None:
    state = _rollback_state(
        payload={
            "request_checksum": "req-123",
            "rollback_blocker": {"unexpected": "expanded-only field"},
        }
    )

    with pytest.raises(UnsafeRollbackError, match="rollback_blocker"):
        assert_previous_code_rollback_safe(
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                blocked_payload_fields=("rollback_blocker",),
            ),
            state=state,
            trusted_proof=_trusted_proof(),
        )


def test_context3_forward_repair_does_not_widen_compatibility_ceiling() -> None:
    state = _rollback_state(
        compatibility_window_floor=2,
        compatibility_window_ceiling=2,
        payload={"request_hash_v2": "req-123"},
        proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
    )

    with pytest.raises(UnsafeRollbackError, match="must not widen the compatibility ceiling"):
        apply_forward_repair(
            state=state,
            repair=ForwardRepairPlan(
                repair_id="repair-invalid-ceiling",
                repair_revision_id="20260712_forward_repair_checksum",
                restores_code_version=3,
                updated_compatibility_proof_reference="CTX3-ROLLBACK-EVID-001",
                field_repairs=(ForwardRepairField(target_field="request_checksum", source_field="request_hash_v2"),),
            ),
            previous_code=_previous_code(
                code_version=3,
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260712_forward_repair_checksum",
            ),
            trusted_proof=_trusted_proof(
                applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_forward_repair_checksum"),
                proof_revision_id="20260712_forward_repair_checksum",
            ),
        )


def test_context3_forward_repair_blocks_when_repaired_payload_is_still_incompatible() -> None:
    state = _rollback_state(
        compatibility_window_floor=2,
        payload={"request_hash_v2": {"bad": "shape"}},
        proof_reference="CTX3-ROLLBACK-EVID-UNSAFE-001",
    )

    with pytest.raises(UnsafeRollbackError, match="request_checksum"):
        apply_forward_repair(
            state=state,
            repair=ForwardRepairPlan(
                repair_id="repair-invalid-payload",
                repair_revision_id="20260712_forward_repair_checksum",
                restores_code_version=1,
                updated_compatibility_proof_reference="CTX3-ROLLBACK-EVID-001",
                field_repairs=(ForwardRepairField(target_field="request_checksum", source_field="request_hash_v2"),),
            ),
            previous_code=_previous_code(
                required_payload_fields=(PayloadFieldRequirement("request_checksum", "str"),),
                required_proof_revision_id="20260712_forward_repair_checksum",
            ),
            trusted_proof=_trusted_proof(
                applied_revision_ids=("20260711_01", "20260712_expand_checksum", "20260712_forward_repair_checksum"),
                proof_revision_id="20260712_forward_repair_checksum",
            ),
        )


def _rollback_state(
    *,
    schema_version: int = 2,
    compatibility_window_floor: int = 1,
    compatibility_window_ceiling: int = 2,
    applied_revision_ids: tuple[str, ...] = ("20260711_01", "20260712_expand_checksum"),
    proof_reference: str = "CTX3-ROLLBACK-EVID-001",
    proof_revision_id: str = "20260712_expand_checksum",
    payload: dict[str, object],
    down_migration_revision: str | None = None,
) -> RollbackSchemaState:
    return RollbackSchemaState(
        schema_version=schema_version,
        compatibility_window_floor=compatibility_window_floor,
        compatibility_window_ceiling=compatibility_window_ceiling,
        applied_revision_ids=applied_revision_ids,
        compatibility_proof_reference=proof_reference,
        proof_revision_id=proof_revision_id,
        payload=payload,
        down_migration_revision=down_migration_revision,
    )


def _previous_code(
    *,
    code_version: int = 1,
    min_supported_schema_version: int = 1,
    max_supported_schema_version: int = 2,
    required_payload_fields: tuple[PayloadFieldRequirement, ...] = (),
    blocked_payload_fields: tuple[str, ...] = (),
    required_proof_reference: str = "CTX3-ROLLBACK-EVID-001",
    required_proof_revision_id: str = "20260712_expand_checksum",
) -> PreviousCodeCompatibility:
    return PreviousCodeCompatibility(
        code_version=code_version,
        min_supported_schema_version=min_supported_schema_version,
        max_supported_schema_version=max_supported_schema_version,
        required_payload_fields=required_payload_fields,
        blocked_payload_fields=blocked_payload_fields,
        required_compatibility_proof_reference=required_proof_reference,
        required_proof_revision_id=required_proof_revision_id,
    )


def _trusted_proof(
    *,
    applied_revision_ids: tuple[str, ...] = ("20260711_01", "20260712_expand_checksum"),
    proof_reference: str = "CTX3-ROLLBACK-EVID-001",
    proof_revision_id: str = "20260712_expand_checksum",
    payload: dict[str, object] | None = None,
) -> TrustedRollbackProof:
    return TrustedRollbackProof(
        applied_revision_ids=applied_revision_ids,
        compatibility_proof_reference=proof_reference,
        proof_revision_id=proof_revision_id,
        payload_fingerprint=_payload_fingerprint(payload or {"request_checksum": "req-123"}),
    )


def _trusted_proof_ledger(*proofs: TrustedRollbackProof) -> TrustedRollbackProofLedger:
    return TrustedRollbackProofLedger(proofs=proofs)


def _payload_fingerprint(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _append_table(table_name: str, events: list[str] | None = None) -> Callable[[MigrationContext], None]:
    def apply(context: MigrationContext) -> None:
        tables = context.state.setdefault("tables", [])
        assert isinstance(tables, list)
        tables.append(table_name)
        if events is not None:
            events.append(table_name)

    return apply


def _raise_runtime_error(context: MigrationContext) -> None:
    del context
    raise RuntimeError("boom")


def _noop(context: MigrationContext) -> None:
    del context
