from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.storage.postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleOwnerError,
    AcidCasStaleWriteError,
    OperationScope,
    TransactionWrite,
)


def scoped_resource_id(
    entity_type: str,
    tenant_id: str,
    owner_id: str,
    project_id: str,
    entity_id: str,
) -> str:
    return f"{entity_type}:{tenant_id}:{owner_id}:{project_id}:{entity_id}"


def _lease_guarded_run_write(
    *,
    expected_version: int | None,
    status: str,
    lease_id: str,
    lease_epoch: int,
) -> TransactionWrite:
    return TransactionWrite(
        entity_type="run",
        entity_id="run-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        expected_version=expected_version,
        state="OPEN",
        payload={"status": status},
        lease_resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id=lease_id,
        lease_epoch=lease_epoch,
    )


def test_ch02_kernel_applies_atomic_transaction_and_versions_new_rows() -> None:
    kernel = AcidCasKernel()

    result = kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Project One"},
            ),
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
    )

    assert result.outcome == "applied"
    assert result.replayed is False
    assert [record.version for record in result.records] == [1, 1]
    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"name": "Project One"}
    )
    assert (
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"status": "queued"}
    )


def test_ch02_kernel_replays_committed_transaction_without_new_versions() -> None:
    kernel = AcidCasKernel()
    writes = (
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
    )

    first = kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=writes,
    )
    second = kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=writes,
    )

    assert first.outcome == "applied"
    assert second.outcome == "replayed"
    assert second.replayed is True
    assert second.records == first.records
    assert (
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).version
        == 1
    )


def test_ch02_kernel_rejects_conflicting_replay_checksum() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
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
    )

    with pytest.raises(AcidCasConflictError, match="checksum"):
        kernel.commit(
            transaction_id="tx-1",
            request_id="req-1",
            request_checksum="sha256:req-2",
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
        )


def test_ch02_kernel_rejects_replay_when_request_identity_changes() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
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
    )

    with pytest.raises(AcidCasConflictError, match="checksum"):
        kernel.commit(
            transaction_id="tx-1",
            request_id="req-2",
            request_checksum="sha256:req-1",
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
        )


def test_ch02_kernel_rejects_replay_when_write_payload_changes() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
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
    )

    with pytest.raises(AcidCasConflictError, match="checksum"):
        kernel.commit(
            transaction_id="tx-1",
            request_id="req-1",
            request_checksum="sha256:req-1",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=None,
                    state="OPEN",
                    payload={"status": "processing"},
                ),
            ),
        )


def test_ch02_kernel_rejects_stale_write_after_newer_commit() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
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
    )
    kernel.commit(
        transaction_id="tx-2",
        request_id="req-2",
        request_checksum="sha256:req-2",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=1,
                state="OPEN",
                payload={"status": "processing"},
            ),
        ),
    )

    with pytest.raises(AcidCasStaleWriteError, match="expected version 1"):
        kernel.commit(
            transaction_id="tx-3",
            request_id="req-3",
            request_checksum="sha256:req-3",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=1,
                    state="TERMINAL",
                    payload={"status": "done"},
                ),
            ),
        )


def test_ch02_kernel_rejects_post_terminal_write_even_when_version_matches() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
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
    )
    terminal = kernel.commit(
        transaction_id="tx-2",
        request_id="req-2",
        request_checksum="sha256:req-2",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=1,
                state="TERMINAL",
                payload={"status": "done"},
            ),
        ),
    )

    with pytest.raises(AcidCasStaleWriteError, match="already TERMINAL"):
        kernel.commit(
            transaction_id="tx-3",
            request_id="req-3",
            request_checksum="sha256:req-3",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=terminal.records[0].version,
                    state="OPEN",
                    payload={"status": "reopened"},
                ),
            ),
        )


def test_ch02_kernel_rolls_back_all_writes_when_any_write_is_stale() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Project One"},
            ),
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
    )
    kernel.commit(
        transaction_id="tx-2",
        request_id="req-2",
        request_checksum="sha256:req-2",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=1,
                state="OPEN",
                payload={"name": "Project One v2"},
            ),
        ),
    )

    with pytest.raises(AcidCasStaleWriteError):
        kernel.commit(
            transaction_id="tx-3",
            request_id="req-3",
            request_checksum="sha256:req-3",
            writes=(
                TransactionWrite(
                    entity_type="project",
                    entity_id="project-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=1,
                    state="OPEN",
                    payload={"name": "Project One stale"},
                ),
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=1,
                    state="OPEN",
                    payload={"status": "processing"},
                ),
            ),
        )

    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"name": "Project One v2"}
    )
    assert (
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"status": "queued"}
    )


def test_ch02_kernel_rolls_back_valid_earlier_write_when_later_write_is_stale() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Project One"},
            ),
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
    )
    kernel.commit(
        transaction_id="tx-2",
        request_id="req-2",
        request_checksum="sha256:req-2",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=1,
                state="OPEN",
                payload={"status": "processing"},
            ),
        ),
    )

    with pytest.raises(AcidCasStaleWriteError):
        kernel.commit(
            transaction_id="tx-3",
            request_id="req-3",
            request_checksum="sha256:req-3",
            writes=(
                TransactionWrite(
                    entity_type="project",
                    entity_id="project-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=1,
                    state="OPEN",
                    payload={"name": "Project One v2"},
                ),
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=1,
                    state="TERMINAL",
                    payload={"status": "done"},
                ),
            ),
        )

    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"name": "Project One"}
    )
    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).version
        == 1
    )
    assert (
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"status": "processing"}
    )
    assert (
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).version
        == 2
    )


def test_ch02_kernel_returns_copies_not_mutable_internal_aliases() -> None:
    kernel = AcidCasKernel()

    result = kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Project One"},
            ),
        ),
    )

    result.records[0].payload["name"] = "tampered"
    fetched = kernel.get(
        entity_type="project",
        entity_id="project-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
    )
    fetched.payload["name"] = "tampered-again"
    replay = kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Project One"},
            ),
        ),
    )

    assert replay.records[0].payload == {"name": "Project One"}
    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"name": "Project One"}
    )


def test_ch02_kernel_scopes_identity_by_tenant_owner_and_project() -> None:
    kernel = AcidCasKernel()

    tenant_one = kernel.commit(
        transaction_id="tx-1",
        request_id="req-1",
        request_checksum="sha256:req-1",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Tenant One"},
            ),
        ),
    )
    tenant_two = kernel.commit(
        transaction_id="tx-2",
        request_id="req-2",
        request_checksum="sha256:req-2",
        writes=(
            TransactionWrite(
                entity_type="project",
                entity_id="project-1",
                tenant_id="tenant-2",
                owner_id="owner-2",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"name": "Tenant Two"},
            ),
        ),
    )

    assert tenant_one.records[0].version == 1
    assert tenant_two.records[0].version == 1
    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"name": "Tenant One"}
    )
    assert (
        kernel.get(
            entity_type="project",
            entity_id="project-1",
            tenant_id="tenant-2",
            owner_id="owner-2",
            project_id="project-1",
        ).payload
        == {"name": "Tenant Two"}
    )


def test_context2_idempotency_replays_terminal_success() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    completed = kernel.commit_operation_success(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        response_payload={"status": "done", "runId": "run-1"},
    )
    replay = kernel.start_operation(
        transaction_id="tx-op-3",
        request_id="req-op-1-replay",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-2",
        lease_epoch=8,
    )

    assert started.outcome == "applied"
    assert started.record.state == "RUNNING"
    assert completed.record.state == "TERMINAL_SUCCESS"
    assert completed.record.response_payload == {"status": "done", "runId": "run-1"}
    assert replay.outcome == "replayed"
    assert replay.replayed is True
    assert replay.record.state == "TERMINAL_SUCCESS"
    assert replay.record.response_payload == {"status": "done", "runId": "run-1"}


def test_context2_idempotency_stores_operation_through_row_kernel() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    row_kernel_record = kernel.get(
        entity_type="operation",
        entity_id=f"operation-1::{scope.resource_id}",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
    )

    assert started.record.version == 1
    assert row_kernel_record.version == started.record.version
    assert row_kernel_record.transaction_id == "tx-op-1"
    assert row_kernel_record.payload["operationId"] == "operation-1"
    assert row_kernel_record.payload["operationState"] == "RUNNING"
    assert row_kernel_record.payload["payloadHash"] == "sha256:payload-1"


def test_context2_idempotency_terminal_updates_are_visible_through_row_kernel() -> None:
    kernel = AcidCasKernel()
    success_scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-success"),
    )
    error_scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-error"),
    )

    started_success = kernel.start_operation(
        transaction_id="tx-op-success-1",
        request_id="req-op-success-1",
        operation_id="operation-success",
        scope=success_scope,
        payload_hash="sha256:payload-success",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    kernel.commit_operation_success(
        transaction_id="tx-op-success-2",
        request_id="req-op-success-1",
        operation_id="operation-success",
        scope=success_scope,
        payload_hash="sha256:payload-success",
        expected_version=started_success.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        response_payload={"status": "done"},
    )

    started_error = kernel.start_operation(
        transaction_id="tx-op-error-1",
        request_id="req-op-error-1",
        operation_id="operation-error",
        scope=error_scope,
        payload_hash="sha256:payload-error",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    kernel.commit_operation_error(
        transaction_id="tx-op-error-2",
        request_id="req-op-error-1",
        operation_id="operation-error",
        scope=error_scope,
        payload_hash="sha256:payload-error",
        expected_version=started_error.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        error_payload={"code": "UPSTREAM_FAILURE"},
    )

    success_row = kernel.get(
        entity_type="operation",
        entity_id=f"operation-success::{success_scope.resource_id}",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
    )
    error_row = kernel.get(
        entity_type="operation",
        entity_id=f"operation-error::{error_scope.resource_id}",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
    )

    assert success_row.state == "TERMINAL"
    assert success_row.version == 2
    assert success_row.payload["operationState"] == "TERMINAL_SUCCESS"
    assert success_row.payload["responsePayload"] == {"status": "done"}
    assert error_row.state == "ERROR"
    assert error_row.version == 2
    assert error_row.payload["operationState"] == "TERMINAL_ERROR"
    assert error_row.payload["errorPayload"] == {"code": "UPSTREAM_FAILURE"}


def test_context2_idempotency_rejects_cross_scope_resource_identity() -> None:
    kernel = AcidCasKernel()

    with pytest.raises(AcidCasConflictError, match="must match OperationScope"):
        kernel.start_operation(
            transaction_id="tx-op-invalid-1",
            request_id="req-op-invalid-1",
            operation_id="operation-invalid",
            scope=OperationScope(
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_id=scoped_resource_id("run", "tenant-2", "owner-2", "project-9", "run-evil"),
            ),
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )

    with pytest.raises(AcidCasConflictError, match="canonical non-empty colon-free"):
        kernel.start_operation(
            transaction_id="tx-op-invalid-2",
            request_id="req-op-invalid-2",
            operation_id="operation-invalid",
            scope=OperationScope(
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_id="run-1",
            ),
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )

    with pytest.raises(AcidCasConflictError, match="non-empty colon-free"):
        kernel.start_operation(
            transaction_id="tx-op-invalid-3",
            request_id="req-op-invalid-3",
            operation_id="operation-invalid",
            scope=OperationScope(
                tenant_id=" ",
                owner_id=" ",
                project_id=" ",
                resource_id=scoped_resource_id("run", " ", " ", " ", "run-1"),
            ),
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )

    with pytest.raises(AcidCasConflictError, match="non-empty colon-free"):
        kernel.start_operation(
            transaction_id="tx-op-invalid-4",
            request_id="req-op-invalid-4",
            operation_id="operation-invalid",
            scope=OperationScope(
                tenant_id="tenant-1",
                owner_id=" owner-1 ",
                project_id="project-1",
                resource_id=scoped_resource_id("run", "tenant-1", " owner-1 ", "project-1", "run-1"),
            ),
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )


def test_context2_idempotency_rejects_generic_operation_row_commit() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )
    started = kernel.start_operation(
        transaction_id="tx-op-reserved-1",
        request_id="req-op-reserved-1",
        operation_id="operation-reserved",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    with pytest.raises(AcidCasConflictError, match="Operation rows must be written through the operation API"):
        kernel.commit(
            transaction_id="tx-op-reserved-forgery",
            request_id="req-op-reserved-forgery",
            request_checksum="sha256:req-op-reserved-forgery",
            writes=(
                TransactionWrite(
                    entity_type="operation",
                    entity_id=f"operation-reserved::{scope.resource_id}",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=started.record.version,
                    state="OPEN",
                    payload={
                        "operationId": "operation-reserved",
                        "resourceId": scope.resource_id,
                        "payloadHash": "sha256:forged",
                        "operationState": "RUNNING",
                        "leaseOwnerId": "attacker",
                        "leaseEpoch": 99,
                        "responsePayload": None,
                        "errorPayload": None,
                    },
                ),
            ),
        )

    stored = kernel.get_operation(operation_id="operation-reserved", scope=scope)
    assert stored.payload_hash == "sha256:payload-1"
    assert stored.lease_owner_id == "worker-1"
    assert stored.lease_epoch == 7


def test_context2_idempotency_rejects_initial_generic_operation_row_commit() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    with pytest.raises(AcidCasConflictError, match="Operation rows must be written through the operation API"):
        kernel.commit(
            transaction_id="tx-op-reserved-initial-forgery",
            request_id="req-op-reserved-initial-forgery",
            request_checksum="sha256:req-op-reserved-initial-forgery",
            writes=(
                TransactionWrite(
                    entity_type="operation",
                    entity_id=f"operation-reserved::{scope.resource_id}",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    expected_version=None,
                    state="OPEN",
                    payload={
                        "operationId": "operation-reserved",
                        "resourceId": scope.resource_id,
                        "payloadHash": "sha256:forged",
                        "operationState": "RUNNING",
                        "leaseOwnerId": "attacker",
                        "leaseEpoch": 99,
                        "responsePayload": None,
                        "errorPayload": None,
                    },
                ),
            ),
        )

    with pytest.raises(KeyError, match="No durable operation"):
        kernel.get_operation(operation_id="operation-reserved", scope=scope)


def test_context2_idempotency_rejects_blank_operation_identity_fields() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    with pytest.raises(AcidCasConflictError, match="operation_id must be non-empty"):
        kernel.start_operation(
            transaction_id="tx-op-blank-1",
            request_id="req-op-blank-1",
            operation_id=" ",
            scope=scope,
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )
    with pytest.raises(AcidCasConflictError, match="operation_id must be non-empty"):
        kernel.start_operation(
            transaction_id="tx-op-padded-1",
            request_id="req-op-padded-1",
            operation_id=" operation-1 ",
            scope=scope,
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )
    with pytest.raises(AcidCasConflictError, match="payload_hash must be non-empty"):
        kernel.start_operation(
            transaction_id="tx-op-blank-2",
            request_id="req-op-blank-2",
            operation_id="operation-1",
            scope=scope,
            payload_hash=" ",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )
    with pytest.raises(AcidCasConflictError, match="lease_owner_id must be non-empty"):
        kernel.start_operation(
            transaction_id="tx-op-blank-3",
            request_id="req-op-blank-3",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            lease_owner_id=" ",
            lease_epoch=7,
        )


def test_context2_idempotency_replays_terminal_error() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    failed = kernel.commit_operation_error(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        error_payload={"code": "UPSTREAM_FAILURE", "message": "provider timeout"},
    )
    replay = kernel.start_operation(
        transaction_id="tx-op-3",
        request_id="req-op-1-replay",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-2",
        lease_epoch=8,
    )

    assert failed.record.state == "TERMINAL_ERROR"
    assert failed.record.error_payload == {
        "code": "UPSTREAM_FAILURE",
        "message": "provider timeout",
    }
    assert replay.outcome == "replayed"
    assert replay.record.state == "TERMINAL_ERROR"
    assert replay.record.error_payload == {
        "code": "UPSTREAM_FAILURE",
        "message": "provider timeout",
    }


def test_context2_idempotency_rejects_payload_hash_conflict() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    with pytest.raises(AcidCasConflictError, match="payload hash"):
        kernel.start_operation(
            transaction_id="tx-op-2",
            request_id="req-op-2",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-2",
            lease_owner_id="worker-1",
            lease_epoch=7,
        )


def test_context2_idempotency_rejects_terminal_start_replay_payload_hash_conflict() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    kernel.commit_operation_success(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        response_payload={"status": "done", "runId": "run-1"},
    )

    with pytest.raises(AcidCasConflictError, match="payload hash"):
        kernel.start_operation(
            transaction_id="tx-op-3",
            request_id="req-op-1-drift",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-2",
            lease_owner_id="worker-2",
            lease_epoch=8,
        )


def test_context2_idempotency_rejects_terminal_error_start_replay_payload_hash_conflict() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    kernel.commit_operation_error(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        error_payload={"code": "UPSTREAM_FAILURE", "message": "provider timeout"},
    )

    with pytest.raises(AcidCasConflictError, match="payload hash"):
        kernel.start_operation(
            transaction_id="tx-op-3",
            request_id="req-op-1-drift",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-2",
            lease_owner_id="worker-2",
            lease_epoch=8,
        )


def test_context2_idempotency_scopes_identity_by_scope_dimension() -> None:
    kernel = AcidCasKernel()
    scope_one = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )
    scope_two = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-2"),
    )

    first = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope_one,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    second = kernel.start_operation(
        transaction_id="tx-op-2",
        request_id="req-op-2",
        operation_id="operation-1",
        scope=scope_two,
        payload_hash="sha256:payload-2",
        lease_owner_id="worker-2",
        lease_epoch=8,
    )

    assert first.outcome == "applied"
    assert second.outcome == "applied"
    assert first.record.version == 1
    assert second.record.version == 1
    assert kernel.get_operation(operation_id="operation-1", scope=scope_one).payload_hash == "sha256:payload-1"
    assert kernel.get_operation(operation_id="operation-1", scope=scope_two).payload_hash == "sha256:payload-2"
    assert (
        kernel.get_operation(operation_id="operation-1", scope=scope_one).scope.resource_id
        == scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    )
    assert (
        kernel.get_operation(operation_id="operation-1", scope=scope_two).scope.resource_id
        == scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-2")
    )


def test_context2_idempotency_allows_distinct_operation_ids_in_same_scope() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    first = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    second = kernel.start_operation(
        transaction_id="tx-op-2",
        request_id="req-op-2",
        operation_id="operation-2",
        scope=scope,
        payload_hash="sha256:payload-2",
        lease_owner_id="worker-2",
        lease_epoch=8,
    )

    assert first.outcome == "applied"
    assert second.outcome == "applied"
    assert first.record.version == 1
    assert second.record.version == 1
    assert kernel.get_operation(operation_id="operation-1", scope=scope).payload_hash == "sha256:payload-1"
    assert kernel.get_operation(operation_id="operation-2", scope=scope).payload_hash == "sha256:payload-2"


def test_context2_idempotency_success_rejects_stale_owner() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    with pytest.raises(AcidCasStaleOwnerError, match="stale owner"):
        kernel.commit_operation_success(
            transaction_id="tx-op-2",
            request_id="req-op-1",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=started.record.version,
            lease_owner_id="worker-2",
            lease_epoch=8,
            response_payload={"status": "done", "runId": "run-1"},
        )


def test_context2_idempotency_start_rejects_stale_owner_for_inflight_operation() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    with pytest.raises(AcidCasStaleOwnerError, match="stale owner"):
        kernel.start_operation(
            transaction_id="tx-op-2",
            request_id="req-op-2",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-2",
            lease_epoch=8,
        )


def test_context2_idempotency_recovery_allows_same_owner_higher_epoch_advance() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    failed = kernel.fail_operation_transient(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    with pytest.raises(AcidCasStaleOwnerError, match="stale owner"):
        kernel.commit_operation_success(
            transaction_id="tx-op-3a",
            request_id="req-op-1-replay",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=failed.record.version,
            lease_owner_id="worker-2",
            lease_epoch=8,
            response_payload={"status": "done", "runId": "run-1"},
        )

    recovered = kernel.recover_operation(
        transaction_id="tx-op-3",
        request_id="req-op-1-replay",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=failed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=8,
    )

    assert recovered.outcome == "applied"
    assert recovered.record.state == "REPLAYING"
    assert recovered.record.lease_owner_id == "worker-1"
    assert recovered.record.lease_epoch == 8

    with pytest.raises(AcidCasStaleOwnerError, match="stale owner"):
        kernel.fail_operation_transient(
            transaction_id="tx-op-4",
            request_id="req-op-1-replay-stale",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=failed.record.version,
            lease_owner_id="worker-2",
            lease_epoch=8,
        )


def test_context2_idempotency_recovery_replays_exact_transaction_after_epoch_advance() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    failed = kernel.fail_operation_transient(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    recovered = kernel.recover_operation(
        transaction_id="tx-op-3",
        request_id="req-op-1-replay",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=failed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=8,
    )

    replayed = kernel.recover_operation(
        transaction_id="tx-op-3",
        request_id="req-op-1-replay",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=failed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=8,
    )

    assert recovered.outcome == "applied"
    assert replayed.outcome == "replayed"
    assert replayed.replayed is True
    assert replayed.record.state == "REPLAYING"
    assert replayed.record.version == recovered.record.version
    assert replayed.record.transaction_id == "tx-op-3"


def test_context2_idempotency_recovery_rejects_cross_owner_or_non_advancing_epoch() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    failed = kernel.fail_operation_transient(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    with pytest.raises(AcidCasConflictError, match="explicit epoch advance"):
        kernel.recover_operation(
            transaction_id="tx-op-3",
            request_id="req-op-1-replay",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=failed.record.version,
            lease_owner_id="worker-1",
            lease_epoch=7,
        )

    with pytest.raises(AcidCasStaleOwnerError, match="must remain worker-1"):
        kernel.recover_operation(
            transaction_id="tx-op-4",
            request_id="req-op-1-replay",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=failed.record.version,
            lease_owner_id="worker-2",
            lease_epoch=8,
        )

    with pytest.raises(AcidCasStaleOwnerError, match="stale recovery epoch"):
        kernel.recover_operation(
            transaction_id="tx-op-5",
            request_id="req-op-1-replay",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=failed.record.version,
            lease_owner_id="worker-1",
            lease_epoch=6,
        )


def test_context2_idempotency_terminal_success_replay_rejects_payload_drift() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    completed = kernel.commit_operation_success(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        response_payload={"status": "done", "runId": "run-1"},
    )

    replayed = kernel.commit_operation_success(
        transaction_id="tx-op-2-replay",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=completed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        response_payload={"status": "done", "runId": "run-1"},
    )
    assert replayed.outcome == "replayed"
    assert replayed.record.response_payload == {"status": "done", "runId": "run-1"}

    with pytest.raises(AcidCasConflictError, match="terminal success replay payload"):
        kernel.commit_operation_success(
            transaction_id="tx-op-2-drift",
            request_id="req-op-1",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=completed.record.version,
            lease_owner_id="worker-1",
            lease_epoch=7,
            response_payload={"status": "done", "runId": "run-1", "extra": "drift"},
        )


def test_context2_idempotency_terminal_error_replay_rejects_payload_drift() -> None:
    kernel = AcidCasKernel()
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )

    started = kernel.start_operation(
        transaction_id="tx-op-1",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=7,
    )
    completed = kernel.commit_operation_error(
        transaction_id="tx-op-2",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        error_payload={"code": "timeout", "message": "retry later"},
    )

    replayed = kernel.commit_operation_error(
        transaction_id="tx-op-2-replay",
        request_id="req-op-1",
        operation_id="operation-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        expected_version=completed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=7,
        error_payload={"code": "timeout", "message": "retry later"},
    )
    assert replayed.outcome == "replayed"
    assert replayed.record.error_payload == {"code": "timeout", "message": "retry later"}

    with pytest.raises(AcidCasConflictError, match="terminal error replay payload"):
        kernel.commit_operation_error(
            transaction_id="tx-op-2-drift",
            request_id="req-op-1",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=completed.record.version,
            lease_owner_id="worker-1",
            lease_epoch=7,
            error_payload={"code": "timeout", "message": "retry later", "extra": "drift"},
        )


def test_context2_lease_renew_preserves_epoch_and_extends_expiry() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=30_000,
        now=acquired_at,
    )

    heartbeat_at = acquired_at + timedelta(seconds=10)
    renewed = kernel.heartbeat_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_epoch=lease.lease_epoch,
        now=heartbeat_at,
    )

    assert renewed.lease_epoch == lease.lease_epoch == 1
    assert renewed.acquired_at == lease.acquired_at
    assert renewed.heartbeat_at == heartbeat_at.isoformat()
    assert renewed.expires_at == (heartbeat_at + timedelta(seconds=30)).isoformat()


def test_context2_lease_transfer_increments_epoch() -> None:
    kernel = AcidCasKernel()
    first_acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    first = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=first_acquired_at,
    )
    transferred = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=first_acquired_at + timedelta(seconds=11),
    )

    assert first.lease_epoch == 1
    assert transferred.lease_epoch == 2
    assert transferred.lease_id == "worker-2"


def test_context2_lease_rejects_double_acquire_while_active() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasConflictError, match="already held"):
        kernel.acquire_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_ttl_ms=10_000,
            now=acquired_at + timedelta(seconds=5),
        )


def test_context2_lease_heartbeat_rejects_owner_mismatch() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasStaleWriteError, match="expected owner worker-2"):
        kernel.heartbeat_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_epoch=lease.lease_epoch,
            now=acquired_at + timedelta(seconds=5),
        )


def test_context2_lease_rejects_stale_writer_epoch() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    kernel.commit(
        transaction_id="tx-lease-1",
        request_id="req-lease-1",
        request_checksum="sha256:req-lease-1",
        writes=(
            _lease_guarded_run_write(
                expected_version=None,
                status="queued",
                lease_id="worker-1",
                lease_epoch=lease.lease_epoch,
            ),
        ),
        now=acquired_at + timedelta(seconds=1),
    )
    reclaimed = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    with pytest.raises(AcidCasStaleWriteError, match="lease epoch"):
        kernel.commit(
            transaction_id="tx-lease-2",
            request_id="req-lease-2",
            request_checksum="sha256:req-lease-2",
            writes=(
                _lease_guarded_run_write(
                    expected_version=1,
                    status="stale-worker-update",
                    lease_id="worker-1",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=13),
        )

    assert reclaimed.lease_epoch == lease.lease_epoch + 1
    assert (
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        ).payload
        == {"status": "queued"}
    )


def test_context2_lease_replays_guarded_transaction_after_lease_transfer() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    writes = (
        _lease_guarded_run_write(
            expected_version=None,
            status="queued",
            lease_id="worker-1",
            lease_epoch=lease.lease_epoch,
        ),
    )

    first = kernel.commit(
        transaction_id="tx-lease-replay-1",
        request_id="req-lease-replay-1",
        request_checksum="sha256:req-lease-replay-1",
        writes=writes,
        now=acquired_at + timedelta(seconds=1),
    )

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    replayed = kernel.commit(
        transaction_id="tx-lease-replay-1",
        request_id="req-lease-replay-1",
        request_checksum="sha256:req-lease-replay-1",
        writes=writes,
        now=acquired_at + timedelta(seconds=13),
    )

    assert first.outcome == "applied"
    assert replayed.outcome == "replayed"
    assert replayed.replayed is True
    assert replayed.records[0].version == 1

    with pytest.raises(AcidCasConflictError, match="replay checksum"):
        kernel.commit(
            transaction_id="tx-lease-replay-1",
            request_id="req-lease-replay-1",
            request_checksum="sha256:req-lease-replay-1",
            writes=(
                _lease_guarded_run_write(
                    expected_version=None,
                    status="queued",
                    lease_id="worker-2",
                    lease_epoch=lease.lease_epoch + 1,
                ),
            ),
            now=acquired_at + timedelta(seconds=14),
        )


def test_context2_lease_expiry_blocks_stale_owner_commit() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    kernel.commit(
        transaction_id="tx-lease-1",
        request_id="req-lease-1",
        request_checksum="sha256:req-lease-1",
        writes=(
            _lease_guarded_run_write(
                expected_version=None,
                status="queued",
                lease_id="worker-1",
                lease_epoch=lease.lease_epoch,
            ),
        ),
        now=acquired_at + timedelta(seconds=1),
    )

    with pytest.raises(AcidCasStaleWriteError, match="expired"):
        kernel.commit(
            transaction_id="tx-lease-2",
            request_id="req-lease-2",
            request_checksum="sha256:req-lease-2",
            writes=(
                _lease_guarded_run_write(
                    expected_version=1,
                    status="expired-owner-update",
                    lease_id="worker-1",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=11),
        )

    stored = kernel.get(
        entity_type="run",
        entity_id="run-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
    )
    assert stored.version == 1
    assert stored.payload == {"status": "queued"}


def test_context2_lease_rejects_unrelated_live_lease_for_different_row() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    unrelated_lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-2",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasStaleWriteError, match="does not match"):
        kernel.commit(
            transaction_id="tx-lease-3",
            request_id="req-lease-3",
            request_checksum="sha256:req-lease-3",
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
                    lease_resource_id=unrelated_lease.resource_id,
                    lease_id="worker-1",
                    lease_epoch=unrelated_lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_rejects_unguarded_write_while_row_has_active_lease() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasStaleWriteError, match="requires lease fencing fields"):
        kernel.commit(
            transaction_id="tx-lease-3a",
            request_id="req-lease-3a",
            request_checksum="sha256:req-lease-3a",
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
            now=acquired_at + timedelta(seconds=3),
        )


def test_context2_lease_rejects_partial_fencing_tuple() -> None:
    kernel = AcidCasKernel()

    with pytest.raises(AcidCasConflictError, match="must include lease_resource_id, lease_id, and lease_epoch together"):
        kernel.commit(
            transaction_id="tx-lease-3b",
            request_id="req-lease-3b",
            request_checksum="sha256:req-lease-3b",
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
                    lease_resource_id="run:tenant-1:owner-1:project-1:run-1",
                    lease_id="worker-1",
                ),
            ),
        )


def test_context2_lease_rejects_owner_mismatch_for_lease_guarded_write() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasStaleWriteError, match="expected lease owner worker-2"):
        kernel.commit(
            transaction_id="tx-lease-4",
            request_id="req-lease-4",
            request_checksum="sha256:req-lease-4",
            writes=(
                _lease_guarded_run_write(
                    expected_version=None,
                    status="queued",
                    lease_id="worker-2",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_release_removes_active_lease_and_next_acquire_advances_epoch() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    kernel.release_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_epoch=lease.lease_epoch,
        now=acquired_at + timedelta(seconds=1),
    )

    with pytest.raises(KeyError, match="No active lease"):
        kernel.get_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            now=acquired_at + timedelta(seconds=1),
        )

    reacquired = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=2),
    )
    assert reacquired.lease_epoch == lease.lease_epoch + 1

    with pytest.raises(AcidCasStaleWriteError, match="requires lease fencing fields"):
        kernel.commit(
            transaction_id="tx-lease-release-unguarded",
            request_id="req-lease-release-unguarded",
            request_checksum="sha256:req-lease-release-unguarded",
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
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_release_rejects_stale_owner() -> None:
    kernel = AcidCasKernel()
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasStaleWriteError, match="expected owner worker-2"):
        kernel.release_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_epoch=lease.lease_epoch,
            now=acquired_at + timedelta(seconds=1),
        )
