from __future__ import annotations

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
        lease_owner_id="worker-1",
        lease_epoch=7,
    )

    assert started.outcome == "applied"
    assert started.record.state == "RUNNING"
    assert completed.record.state == "TERMINAL_SUCCESS"
    assert completed.record.response_payload == {"status": "done", "runId": "run-1"}
    assert replay.outcome == "replayed"
    assert replay.replayed is True
    assert replay.record.state == "TERMINAL_SUCCESS"
    assert replay.record.response_payload == {"status": "done", "runId": "run-1"}

    with pytest.raises(AcidCasStaleOwnerError, match="stale owner"):
        kernel.start_operation(
            transaction_id="tx-op-4",
            request_id="req-op-1-replay-stale",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-2",
            lease_epoch=8,
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
        lease_owner_id="worker-1",
        lease_epoch=7,
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

    with pytest.raises(AcidCasStaleOwnerError, match="stale owner"):
        kernel.start_operation(
            transaction_id="tx-op-4",
            request_id="req-op-1-replay-stale",
            operation_id="operation-1",
            scope=scope,
            payload_hash="sha256:payload-1",
            lease_owner_id="worker-2",
            lease_epoch=8,
        )


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
