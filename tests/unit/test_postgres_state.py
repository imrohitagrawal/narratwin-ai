from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.storage.postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleWriteError,
    TransactionWrite,
)


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def set(self, value: datetime) -> None:
        self.value = value


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
