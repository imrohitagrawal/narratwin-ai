from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backend.app.storage import (
    OPS_METRIC_CONTRACTS,
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleWriteError,
    MigrationRunner,
    OperationScope,
    OutboxEventWrite,
    PreviousCodeCompatibility,
    TransactionWrite,
    TrustedRollbackProofLedger,
    UnsafeRollbackError,
    load_state,
    reset_ops_metric_snapshots,
    snapshot_ops_metrics,
)


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def test_ch10_metric_contract_declares_required_ops_metric_boundaries() -> None:
    contracts = {key: contract.name for key, contract in OPS_METRIC_CONTRACTS.items()}

    assert contracts["run_backlog"] == "narratwin_ops_run_backlog_gauge"
    assert contracts["lease_staleness_seconds"] == "narratwin_ops_lease_staleness_seconds"
    assert contracts["idempotency_contract_drift_total"] == "narratwin_ops_idempotency_contract_drift_total"
    assert contracts["idempotency_replay_total"] == "narratwin_ops_idempotency_replay_total"
    assert contracts["outbox_backlog_count"] == "narratwin_ops_outbox_backlog_count"
    assert contracts["restore_attempts_total"] == "narratwin_ops_restore_attempts_total"
    assert contracts["rollback_block_total"] == "narratwin_ops_rollback_block_total"
    assert OPS_METRIC_CONTRACTS["restore_attempts_total"].deferred_chunk == "CH-14"
    assert OPS_METRIC_CONTRACTS["rollback_block_total"].deferred_chunk == "CH-15"


def test_ch10_file_state_load_emits_restore_contract_metrics(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    reset_ops_metric_snapshots()

    state_path.write_text('{"schema":"stage4-local-state-v1"}', encoding="utf-8")
    assert load_state(state_path) == {"schema": "stage4-local-state-v1"}

    state_path.write_text("[1,2,3]\n", encoding="utf-8")
    assert load_state(state_path) is None

    state_path.write_text("{", encoding="utf-8")
    assert load_state(state_path) is None

    snapshot = snapshot_ops_metrics()
    assert snapshot["counters"]["narratwin_ops_restore_attempts_total{surface=local-state:stage4,result=loaded}"] == 1.0
    assert (
        snapshot["counters"]["narratwin_ops_restore_attempts_total{surface=local-state:stage4,result=invalid-shape}"]
        == 1.0
    )
    assert (
        snapshot["counters"]["narratwin_ops_restore_attempts_total{surface=local-state:stage4,result=unreadable}"]
        == 1.0
    )
    assert "narratwin_ops_restore_duration_seconds{surface=local-state:stage4,result=loaded}" in snapshot["histograms"]


def test_ch10_kernel_emits_idempotency_lease_and_backlog_metrics() -> None:
    clock = MutableClock(datetime(2026, 7, 12, 12, 0, tzinfo=UTC))
    kernel = AcidCasKernel(clock=clock)
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id="run:tenant-1:owner-1:project-1:run-1",
    )
    reset_ops_metric_snapshots()

    kernel.acquire_lease(resource_id=scope.resource_id, lease_id="lease-1", lease_ttl_ms=30_000)
    kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="op-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="lease-1",
        lease_epoch=1,
    )
    replay = kernel.start_operation(
        transaction_id="tx-op-2",
        request_id="req-op-2",
        operation_id="op-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="lease-1",
        lease_epoch=1,
    )

    with pytest.raises(AcidCasConflictError, match="payload hash"):
        kernel.start_operation(
            transaction_id="tx-op-3",
            request_id="req-op-3",
            operation_id="op-1",
            scope=scope,
            payload_hash="sha256:payload-2",
            lease_owner_id="lease-1",
            lease_epoch=1,
        )

    with pytest.raises(AcidCasStaleWriteError, match="expected lease epoch 2"):
        kernel.heartbeat_lease(resource_id=scope.resource_id, lease_id="lease-1", lease_epoch=2)

    kernel.commit(
        transaction_id="tx-run-1",
        request_id="req-run-1",
        request_checksum="sha256:req-run-1",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"status": "queued"},
                lease_resource_id=scope.resource_id,
                lease_id="lease-1",
                lease_epoch=1,
            ),
        ),
    )

    snapshot = snapshot_ops_metrics()
    assert replay.replayed is True
    assert snapshot["counters"]["narratwin_ops_idempotency_replay_total{state=running}"] == 1.0
    assert snapshot["counters"]["narratwin_ops_idempotency_contract_drift_total{surface=operation-payload-hash}"] == 1.0
    assert snapshot["counters"]["narratwin_ops_stale_writer_reject_total{surface=lease-heartbeat}"] == 1.0
    assert snapshot["gauges"]["narratwin_ops_lease_state_count{state=active}"] == 1.0
    assert snapshot["gauges"]["narratwin_ops_run_backlog_gauge{state=open}"] == 1.0


def test_ch10_kernel_emits_outbox_retry_contract_metrics() -> None:
    clock = MutableClock(datetime(2026, 7, 12, 12, 0, tzinfo=UTC))
    kernel = AcidCasKernel(clock=clock)
    reset_ops_metric_snapshots()

    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"status": "queued"},
            ),
        ),
        outbox_events=(
            OutboxEventWrite(
                event_id="evt-1",
                event_type="run.updated",
                resource_id="run:tenant-1:owner-1:project-1:run-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash="sha256:" + hashlib.sha256(
                    json.dumps({"status": "queued"}, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                payload={"status": "queued"},
            ),
        ),
    )

    kernel.acquire_outbox_event(
        event_id="evt-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        lock_ttl_ms=60_000,
    )
    clock.value = clock.value + timedelta(seconds=5)
    kernel.retry_outbox_event(
        event_id="evt-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        last_error="temporary failure",
    )
    clock.value = clock.value + timedelta(seconds=5)
    kernel.acquire_outbox_event(
        event_id="evt-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-2",
        lock_ttl_ms=60_000,
    )
    kernel.complete_outbox_event(
        event_id="evt-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-2",
    )

    snapshot = snapshot_ops_metrics()
    assert snapshot["counters"]["narratwin_ops_outbox_redelivery_total{event_type=run.updated}"] == 1.0
    assert snapshot["gauges"]["narratwin_ops_outbox_backlog_count{state=pending}"] == 0.0
    assert snapshot["gauges"]["narratwin_ops_outbox_backlog_count{state=delivering}"] == 0.0
    assert "narratwin_ops_outbox_age_seconds{event_type=run.updated,phase=retry}" in snapshot["histograms"]


def test_ch10_rollback_assertion_emits_block_metric(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(revisions=[], state_path=state_path)
    reset_ops_metric_snapshots()

    with pytest.raises(UnsafeRollbackError, match="persisted rollback compatibility is missing"):
        runner.assert_persisted_previous_code_rollback_safe(
            previous_code=PreviousCodeCompatibility(
                code_version=1,
                min_supported_schema_version=1,
                max_supported_schema_version=1,
            ),
            trusted_proof_ledger=TrustedRollbackProofLedger(proofs=()),
        )

    snapshot = snapshot_ops_metrics()
    assert snapshot["counters"]["narratwin_ops_rollback_block_total{reason=missing-compatibility}"] == 1.0
