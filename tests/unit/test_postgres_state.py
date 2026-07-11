from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.storage.postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleOwnerError,
    AcidCasStaleWriteError,
    OutboxEventWrite,
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


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def set(self, value: datetime) -> None:
        self.value = value


class LockOwnedClock(MutableClock):
    def __init__(self, value: datetime) -> None:
        super().__init__(value)
        self.kernel: AcidCasKernel | None = None

    def __call__(self) -> datetime:
        assert self.kernel is not None
        is_owned = getattr(self.kernel._lock, "_is_owned")
        assert is_owned(), "trusted clock sampled outside the storage lock"
        return self.value

    def bind(self, kernel: AcidCasKernel) -> None:
        self.kernel = kernel


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
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=30_000,
        now=acquired_at,
    )

    heartbeat_at = acquired_at + timedelta(seconds=10)
    clock.set(heartbeat_at)
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
    first_acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(first_acquired_at)
    kernel = AcidCasKernel(clock=clock)

    first = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=first_acquired_at,
    )
    clock.set(first_acquired_at + timedelta(seconds=11))
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
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=5))
    with pytest.raises(AcidCasConflictError, match="already held"):
        kernel.acquire_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_ttl_ms=10_000,
            now=acquired_at + timedelta(seconds=5),
        )


def test_context2_lease_rejects_non_canonical_resource_identity() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    kernel = AcidCasKernel(clock=MutableClock(acquired_at))

    with pytest.raises(AcidCasConflictError, match="canonical entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.acquire_lease(
            resource_id="run-1",
            lease_id="worker-1",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )

    with pytest.raises(AcidCasConflictError, match="canonical entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.acquire_lease(
            resource_id="run:tenant-1::project-1:run-1",
            lease_id="worker-1",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )

    with pytest.raises(AcidCasConflictError, match="canonical entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.acquire_lease(
            resource_id="run:tenant-1: :project-1:run-1",
            lease_id="worker-1",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )

    with pytest.raises(AcidCasConflictError, match="canonical entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.acquire_lease(
            resource_id="run:tenant-1: owner-1 :project-1:run-1",
            lease_id="worker-1",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )

    with pytest.raises(AcidCasConflictError, match="canonical entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.acquire_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1:extra",
            lease_id="worker-1",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )


def test_context2_lease_rejects_blank_lease_identity() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    with pytest.raises(AcidCasConflictError, match="lease_id must be non-empty"):
        kernel.acquire_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id=" ",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )

    with pytest.raises(AcidCasConflictError, match="lease_id must be non-empty"):
        kernel.acquire_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id=" worker-1 ",
            lease_ttl_ms=10_000,
            now=acquired_at,
        )

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasConflictError, match="lease_id must be non-empty"):
        kernel.commit(
            transaction_id="tx-lease-blank-owner",
            request_id="req-lease-blank-owner",
            request_checksum="sha256:req-lease-blank-owner",
            writes=(
                _lease_guarded_run_write(
                    expected_version=None,
                    status="queued",
                    lease_id=" ",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_heartbeat_rejects_owner_mismatch() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=5))
    with pytest.raises(AcidCasStaleWriteError, match="expected owner worker-2"):
        kernel.heartbeat_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_epoch=lease.lease_epoch,
            now=acquired_at + timedelta(seconds=5),
        )


def test_context2_lease_rejects_stale_writer_epoch() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    clock.set(acquired_at + timedelta(seconds=1))
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
    clock.set(acquired_at + timedelta(seconds=12))
    reclaimed = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    clock.set(acquired_at + timedelta(seconds=13))
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
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

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

    clock.set(acquired_at + timedelta(seconds=1))
    first = kernel.commit(
        transaction_id="tx-lease-replay-1",
        request_id="req-lease-replay-1",
        request_checksum="sha256:req-lease-replay-1",
        writes=writes,
        now=acquired_at + timedelta(seconds=1),
    )

    clock.set(acquired_at + timedelta(seconds=12))
    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    clock.set(acquired_at + timedelta(seconds=13))
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

    clock.set(acquired_at + timedelta(seconds=14))
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
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    clock.set(acquired_at + timedelta(seconds=1))
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

    clock.set(acquired_at + timedelta(seconds=11))
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


def test_context2_lease_expiry_uses_kernel_clock_not_caller_timestamp() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    clock.set(acquired_at + timedelta(seconds=1))
    kernel.commit(
        transaction_id="tx-lease-clock-1",
        request_id="req-lease-clock-1",
        request_checksum="sha256:req-lease-clock-1",
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

    clock.set(acquired_at + timedelta(seconds=11))
    with pytest.raises(AcidCasStaleWriteError, match="expired"):
        kernel.commit(
            transaction_id="tx-lease-clock-2",
            request_id="req-lease-clock-2",
            request_checksum="sha256:req-lease-clock-2",
            writes=(
                _lease_guarded_run_write(
                    expected_version=1,
                    status="backdated-stale-worker-update",
                    lease_id="worker-1",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_commit_timestamp_uses_kernel_clock_not_caller_timestamp() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    trusted_commit_time = acquired_at + timedelta(seconds=5)
    caller_backdated_time = acquired_at + timedelta(seconds=1)
    clock.set(trusted_commit_time)

    result = kernel.commit(
        transaction_id="tx-lease-clock-3",
        request_id="req-lease-clock-3",
        request_checksum="sha256:req-lease-clock-3",
        writes=(
            _lease_guarded_run_write(
                expected_version=None,
                status="queued",
                lease_id="worker-1",
                lease_epoch=lease.lease_epoch,
            ),
        ),
        now=caller_backdated_time,
    )

    assert result.committed_at == trusted_commit_time.isoformat()
    assert result.records[0].committed_at == trusted_commit_time.isoformat()


def test_context2_lease_commit_samples_kernel_clock_inside_storage_lock() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = LockOwnedClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)
    clock.bind(kernel)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    clock.set(acquired_at + timedelta(seconds=11))

    with pytest.raises(AcidCasStaleWriteError, match="expired"):
        kernel.commit(
            transaction_id="tx-lease-clock-lock-1",
            request_id="req-lease-clock-lock-1",
            request_checksum="sha256:req-lease-clock-lock-1",
            writes=(
                _lease_guarded_run_write(
                    expected_version=None,
                    status="queued",
                    lease_id="worker-1",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at,
        )


def test_context2_lease_acquire_uses_kernel_clock_not_caller_timestamp() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=5))
    with pytest.raises(AcidCasConflictError, match="already held"):
        kernel.acquire_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_ttl_ms=10_000,
            now=acquired_at + timedelta(seconds=11),
        )


def test_context2_lease_heartbeat_uses_kernel_clock_not_caller_timestamp() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=11))
    with pytest.raises(AcidCasStaleWriteError, match="expired"):
        kernel.heartbeat_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-1",
            lease_epoch=lease.lease_epoch,
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_release_uses_kernel_clock_not_caller_timestamp() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=11))
    with pytest.raises(AcidCasStaleWriteError, match="expired"):
        kernel.release_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-1",
            lease_epoch=lease.lease_epoch,
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_get_uses_kernel_clock_not_caller_timestamp() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=11))
    with pytest.raises(KeyError, match="No active lease"):
        kernel.get_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_rejects_unrelated_live_lease_for_different_row() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    unrelated_lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-2",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=1))
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
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=3))
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


def test_context2_lease_rejects_non_canonical_write_identity_before_fencing_lookup() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    with pytest.raises(AcidCasConflictError, match="canonical entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.commit(
            transaction_id="tx-lease-padded-row",
            request_id="req-lease-padded-row",
            request_checksum="sha256:req-lease-padded-row",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-1 ",
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

    with pytest.raises(KeyError):
        kernel.get(
            entity_type="run",
            entity_id="run-1 ",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )


def test_context2_lease_rejects_partial_fencing_tuple() -> None:
    kernel = AcidCasKernel()

    partial_writes = (
        TransactionWrite(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            expected_version=None,
            state="OPEN",
            payload={"status": "queued"},
            lease_id="worker-1",
            lease_epoch=1,
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
            lease_resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_epoch=1,
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
            lease_resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-1",
        ),
    )

    for index, partial_write in enumerate(partial_writes, start=1):
        with pytest.raises(
            AcidCasConflictError,
            match="must include lease_resource_id, lease_id, and lease_epoch together",
        ):
            kernel.commit(
                transaction_id=f"tx-lease-partial-{index}",
                request_id=f"req-lease-partial-{index}",
                request_checksum=f"sha256:req-lease-partial-{index}",
                writes=(partial_write,),
            )


def test_context2_lease_rejects_stale_operation_success_after_lease_transfer() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=resource_id,
    )

    lease = kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    started = kernel.start_operation(
        transaction_id="tx-op-lease-1",
        request_id="req-op-lease-1",
        operation_id="operation-lease-1",
        scope=scope,
        payload_hash="sha256:payload-1",
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
    )

    clock.set(acquired_at + timedelta(seconds=12))
    kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    clock.set(acquired_at + timedelta(seconds=13))
    with pytest.raises(AcidCasStaleOwnerError, match="lease epoch"):
        kernel.commit_operation_success(
            transaction_id="tx-op-lease-1-success",
            request_id="req-op-lease-1",
            operation_id="operation-lease-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            expected_version=started.record.version,
            lease_owner_id="worker-1",
            lease_epoch=lease.lease_epoch,
            response_payload={"status": "done"},
        )


def test_context2_lease_rejects_stale_operation_error_after_lease_transfer() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=resource_id,
    )

    lease = kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    started = kernel.start_operation(
        transaction_id="tx-op-lease-2",
        request_id="req-op-lease-2",
        operation_id="operation-lease-2",
        scope=scope,
        payload_hash="sha256:payload-2",
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
    )

    clock.set(acquired_at + timedelta(seconds=12))
    kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    clock.set(acquired_at + timedelta(seconds=13))
    with pytest.raises(AcidCasStaleOwnerError, match="lease epoch"):
        kernel.commit_operation_error(
            transaction_id="tx-op-lease-2-error",
            request_id="req-op-lease-2",
            operation_id="operation-lease-2",
            scope=scope,
            payload_hash="sha256:payload-2",
            expected_version=started.record.version,
            lease_owner_id="worker-1",
            lease_epoch=lease.lease_epoch,
            error_payload={"code": "timeout"},
        )


def test_context2_lease_rejects_stale_operation_transient_failure_after_lease_transfer() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=resource_id,
    )

    lease = kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    started = kernel.start_operation(
        transaction_id="tx-op-lease-3",
        request_id="req-op-lease-3",
        operation_id="operation-lease-3",
        scope=scope,
        payload_hash="sha256:payload-3",
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
    )

    clock.set(acquired_at + timedelta(seconds=12))
    kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    clock.set(acquired_at + timedelta(seconds=13))
    with pytest.raises(AcidCasStaleOwnerError, match="lease epoch"):
        kernel.fail_operation_transient(
            transaction_id="tx-op-lease-3-failed",
            request_id="req-op-lease-3",
            operation_id="operation-lease-3",
            scope=scope,
            payload_hash="sha256:payload-3",
            expected_version=started.record.version,
            lease_owner_id="worker-1",
            lease_epoch=lease.lease_epoch,
        )


def test_context2_lease_allows_terminal_operation_success_replay_after_lease_transfer() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=resource_id,
    )

    lease = kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    started = kernel.start_operation(
        transaction_id="tx-op-lease-4",
        request_id="req-op-lease-4",
        operation_id="operation-lease-4",
        scope=scope,
        payload_hash="sha256:payload-4",
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
    )
    completed = kernel.commit_operation_success(
        transaction_id="tx-op-lease-4-success",
        request_id="req-op-lease-4",
        operation_id="operation-lease-4",
        scope=scope,
        payload_hash="sha256:payload-4",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
        response_payload={"status": "done"},
    )

    clock.set(acquired_at + timedelta(seconds=12))
    kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    replayed = kernel.commit_operation_success(
        transaction_id="tx-op-lease-4-success-replay",
        request_id="req-op-lease-4",
        operation_id="operation-lease-4",
        scope=scope,
        payload_hash="sha256:payload-4",
        expected_version=completed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
        response_payload={"status": "done"},
    )

    assert replayed.outcome == "replayed"
    assert replayed.record.response_payload == {"status": "done"}


def test_context2_lease_allows_terminal_operation_error_replay_after_lease_transfer() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    scope = OperationScope(
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        resource_id=resource_id,
    )

    lease = kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )
    started = kernel.start_operation(
        transaction_id="tx-op-lease-5",
        request_id="req-op-lease-5",
        operation_id="operation-lease-5",
        scope=scope,
        payload_hash="sha256:payload-5",
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
    )
    completed = kernel.commit_operation_error(
        transaction_id="tx-op-lease-5-error",
        request_id="req-op-lease-5",
        operation_id="operation-lease-5",
        scope=scope,
        payload_hash="sha256:payload-5",
        expected_version=started.record.version,
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
        error_payload={"code": "timeout"},
    )

    clock.set(acquired_at + timedelta(seconds=12))
    kernel.acquire_lease(
        resource_id=resource_id,
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=12),
    )

    replayed = kernel.commit_operation_error(
        transaction_id="tx-op-lease-5-error-replay",
        request_id="req-op-lease-5",
        operation_id="operation-lease-5",
        scope=scope,
        payload_hash="sha256:payload-5",
        expected_version=completed.record.version,
        lease_owner_id="worker-1",
        lease_epoch=lease.lease_epoch,
        error_payload={"code": "timeout"},
    )

    assert replayed.outcome == "replayed"
    assert replayed.record.error_payload == {"code": "timeout"}


def test_context2_lease_rejects_owner_mismatch_for_lease_guarded_write() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=1))
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

    with pytest.raises(AcidCasConflictError, match="lease_id must be non-empty"):
        kernel.commit(
            transaction_id="tx-lease-padded-owner",
            request_id="req-lease-padded-owner",
            request_checksum="sha256:req-lease-padded-owner",
            writes=(
                _lease_guarded_run_write(
                    expected_version=None,
                    status="queued",
                    lease_id=" worker-1 ",
                    lease_epoch=lease.lease_epoch,
                ),
            ),
            now=acquired_at + timedelta(seconds=1),
        )


def test_context2_lease_release_removes_active_lease_and_next_acquire_advances_epoch() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=1))
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

    clock.set(acquired_at + timedelta(seconds=2))
    reacquired = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-2",
        lease_ttl_ms=10_000,
        now=acquired_at + timedelta(seconds=2),
    )
    assert reacquired.lease_epoch == lease.lease_epoch + 1

    clock.set(acquired_at + timedelta(seconds=3))
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
            now=acquired_at + timedelta(seconds=3),
        )


def test_context2_lease_release_rejects_stale_owner() -> None:
    acquired_at = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(acquired_at)
    kernel = AcidCasKernel(clock=clock)

    lease = kernel.acquire_lease(
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        lease_id="worker-1",
        lease_ttl_ms=10_000,
        now=acquired_at,
    )

    clock.set(acquired_at + timedelta(seconds=1))
    with pytest.raises(AcidCasStaleWriteError, match="expected owner worker-2"):
        kernel.release_lease(
            resource_id="run:tenant-1:owner-1:project-1:run-1",
            lease_id="worker-2",
            lease_epoch=lease.lease_epoch,
            now=acquired_at + timedelta(seconds=1),
        )


def _run_write(*, expected_version: int | None, status: str) -> TransactionWrite:
    return TransactionWrite(
        entity_type="run",
        entity_id="run-1",
        tenant_id="tenant-1",
        owner_id="owner-1",
        project_id="project-1",
        expected_version=expected_version,
        state="OPEN",
        payload={"status": status},
    )


def _outbox_event(
    *,
    event_id: str = "event-1",
    resource_id: str = "run:tenant-1:owner-1:project-1:run-1",
    resource_version: int = 1,
    payload_hash: str = "sha256:payload-1",
    payload: dict[str, str] | None = None,
) -> OutboxEventWrite:
    return OutboxEventWrite(
        event_id=event_id,
        event_type="run.updated",
        resource_id=resource_id,
        resource_version=resource_version,
        operation_id="operation-1",
        payload_hash=payload_hash,
        payload=payload or {"status": "queued"},
    )


def test_context2_outbox_writes_state_and_event_atomically() -> None:
    kernel = AcidCasKernel()

    result = kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(),),
    )

    event = kernel.get_outbox_event(event_id="event-1")
    assert result.outcome == "applied"
    assert result.outbox_events == (event,)
    assert result.records[0].version == 1
    assert event.state == "PENDING"
    assert event.resource_id == "run:tenant-1:owner-1:project-1:run-1"
    assert event.resource_version == result.records[0].version
    assert event.payload == {"status": "queued"}


def test_context2_outbox_rolls_back_state_when_event_identity_is_duplicate() -> None:
    kernel = AcidCasKernel()
    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(),),
    )

    with pytest.raises(AcidCasConflictError, match="outbox event"):
        kernel.commit(
            transaction_id="tx-outbox-2",
            request_id="req-outbox-2",
            request_checksum="sha256:req-outbox-2",
            writes=(_run_write(expected_version=1, status="processing"),),
            outbox_events=(_outbox_event(payload={"status": "processing"}),),
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
    assert kernel.get_outbox_event(event_id="event-1").payload == {"status": "queued"}


def test_context2_outbox_binds_event_to_staged_resource_payload() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(
            _outbox_event(
                resource_version=1,
                payload_hash="sha256:queued",
                payload={"status": "queued"},
            ),
        ),
    )

    event = kernel.get_outbox_event(event_id="event-1")
    assert event.resource_version == 1
    assert event.payload_hash == "sha256:queued"
    assert event.payload == {"status": "queued"}


def test_context2_outbox_rejects_unmatched_resource_version() -> None:
    kernel = AcidCasKernel()

    with pytest.raises(AcidCasConflictError, match="resource version"):
        kernel.commit(
            transaction_id="tx-outbox-1",
            request_id="req-outbox-1",
            request_checksum="sha256:req-outbox-1",
            writes=(_run_write(expected_version=None, status="queued"),),
            outbox_events=(_outbox_event(resource_version=2),),
        )

    with pytest.raises(KeyError, match="No durable record"):
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )


def test_context2_outbox_replays_committed_state_and_event() -> None:
    kernel = AcidCasKernel()
    writes = (_run_write(expected_version=None, status="queued"),)
    events = (_outbox_event(),)

    first = kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=writes,
        outbox_events=events,
    )
    second = kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=writes,
        outbox_events=events,
    )

    assert second.outcome == "replayed"
    assert second.replayed is True
    assert second.records == first.records
    assert second.outbox_events == first.outbox_events


def test_context2_outbox_rejects_replay_when_event_payload_changes() -> None:
    kernel = AcidCasKernel()
    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(payload={"status": "queued"}),),
    )

    with pytest.raises(AcidCasConflictError, match="checksum"):
        kernel.commit(
            transaction_id="tx-outbox-1",
            request_id="req-outbox-1",
            request_checksum="sha256:req-outbox-1",
            writes=(_run_write(expected_version=None, status="queued"),),
            outbox_events=(_outbox_event(payload={"status": "tampered"}),),
        )


def test_context2_outbox_redelivery_is_at_least_once() -> None:
    clock = MutableClock(datetime(2026, 7, 11, 12, 0, tzinfo=UTC))
    kernel = AcidCasKernel(clock=clock)
    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(),),
    )

    first = kernel.acquire_outbox_event(
        event_id="event-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        lock_ttl_ms=1_000,
    )
    kernel.retry_outbox_event(
        event_id="event-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        last_error="temporary network failure",
    )
    second = kernel.acquire_outbox_event(
        event_id="event-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-2",
        lock_ttl_ms=1_000,
    )

    assert first.state == "DELIVERING"
    assert first.attempt_count == 1
    assert second.state == "DELIVERING"
    assert second.attempt_count == 2
    assert second.last_error == "temporary network failure"


def test_context2_outbox_rejects_stale_dispatch_completion_after_reclaim() -> None:
    clock = MutableClock(datetime(2026, 7, 11, 12, 0, tzinfo=UTC))
    kernel = AcidCasKernel(clock=clock)
    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(),),
    )
    first = kernel.acquire_outbox_event(
        event_id="event-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        lock_ttl_ms=1_000,
    )
    clock.set(datetime(2026, 7, 11, 12, 0, 2, tzinfo=UTC))
    reclaimed = kernel.acquire_outbox_event(
        event_id="event-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-2",
        lock_ttl_ms=1_000,
    )

    with pytest.raises(AcidCasStaleWriteError, match="lock token"):
        kernel.complete_outbox_event(
            event_id="event-1",
            dispatcher_id=first.locked_by or "",
            lock_token=first.lock_token or "",
        )

    completed = kernel.complete_outbox_event(
        event_id="event-1",
        dispatcher_id=reclaimed.locked_by or "",
        lock_token=reclaimed.lock_token or "",
    )
    assert completed.state == "SUCCEEDED"


def test_context2_outbox_consumer_dedupes_duplicate_delivery() -> None:
    kernel = AcidCasKernel()
    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(),),
    )
    event = kernel.acquire_outbox_event(
        event_id="event-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        lock_ttl_ms=1_000,
    )

    first = kernel.record_outbox_consumer_delivery(
        event_id="event-1",
        consumer_name="script-indexer",
        dispatcher_id=event.locked_by or "",
        lock_token=event.lock_token or "",
    )
    second = kernel.record_outbox_consumer_delivery(
        event_id="event-1",
        consumer_name="script-indexer",
        dispatcher_id=event.locked_by or "",
        lock_token=event.lock_token or "",
    )

    assert first == second
    assert first.consumer_name == "script-indexer"
    assert first.event_type == "run.updated"
    assert first.resource_id == "run:tenant-1:owner-1:project-1:run-1"
    assert first.resource_version == 1


def test_context2_outbox_consumer_dedupe_keeps_same_event_id_cross_resource_separate() -> None:
    kernel = AcidCasKernel()
    kernel.commit(
        transaction_id="tx-outbox-1",
        request_id="req-outbox-1",
        request_checksum="sha256:req-outbox-1",
        writes=(_run_write(expected_version=None, status="queued"),),
        outbox_events=(_outbox_event(event_id="shared-event"),),
    )
    kernel.commit(
        transaction_id="tx-outbox-2",
        request_id="req-outbox-2",
        request_checksum="sha256:req-outbox-2",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-2",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"status": "queued"},
            ),
        ),
        outbox_events=(
            _outbox_event(
                event_id="shared-event",
                resource_id="run:tenant-1:owner-1:project-1:run-2",
                resource_version=1,
            ),
        ),
    )

    first_event = kernel.acquire_outbox_event(
        event_id="shared-event",
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        dispatcher_id="dispatcher-1",
        lock_token="lock-1",
        lock_ttl_ms=1_000,
    )
    second_event = kernel.acquire_outbox_event(
        event_id="shared-event",
        resource_id="run:tenant-1:owner-1:project-1:run-2",
        dispatcher_id="dispatcher-1",
        lock_token="lock-2",
        lock_ttl_ms=1_000,
    )
    first = kernel.record_outbox_consumer_delivery(
        event_id="shared-event",
        resource_id="run:tenant-1:owner-1:project-1:run-1",
        consumer_name="script-indexer",
        dispatcher_id=first_event.locked_by or "",
        lock_token=first_event.lock_token or "",
    )
    second = kernel.record_outbox_consumer_delivery(
        event_id="shared-event",
        resource_id="run:tenant-1:owner-1:project-1:run-2",
        consumer_name="script-indexer",
        dispatcher_id=second_event.locked_by or "",
        lock_token=second_event.lock_token or "",
    )

    assert first.event_id == "shared-event"
    assert second.event_id == "shared-event"
    assert first.resource_id != second.resource_id
