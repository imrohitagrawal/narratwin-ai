from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.storage.postgres_state import (
    AcidCasConflictError,
    AcidCasKernel,
    AcidCasStaleWriteError,
    OutboxEventWrite,
    StoredOutboxEvent,
    TransactionWrite,
    payload_hash_for,
)


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def set(self, value: datetime) -> None:
        self.value = value


def scoped_resource_id(
    entity_type: str,
    tenant_id: str,
    owner_id: str,
    project_id: str,
    entity_id: str,
) -> str:
    return f"{entity_type}:{tenant_id}:{owner_id}:{project_id}:{entity_id}"


def outbox_lock_token_for(
    events: tuple[StoredOutboxEvent, ...],
    event_id: str,
    resource_id: str | None = None,
) -> str:
    for event in events:
        if event.event_id == event_id and (resource_id is None or event.resource_id == resource_id):
            assert event.lock_token is not None
            return event.lock_token
    raise AssertionError(f"No acquired outbox event {event_id}")


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


def test_context2_outbox_writes_state_and_event_atomically() -> None:
    kernel = AcidCasKernel()

    result = kernel.commit(
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
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    assert result.records[0].version == 1
    assert result.outbox_events[0].state == "PENDING"
    assert result.outbox_events[0].attempt_count == 0
    assert result.outbox_events[0].resource_version == 1
    assert kernel.get_outbox_event(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    ).payload == {"status": "queued"}

    with pytest.raises(AcidCasConflictError, match="resource version"):
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
                OutboxEventWrite(
                    event_id="evt-2",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-2",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=2,
                    operation_id="op-2",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(KeyError):
        kernel.get(
            entity_type="run",
            entity_id="run-2",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )
    with pytest.raises(KeyError):
        kernel.get_outbox_event(
            event_id="evt-2",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-2"),
        )

    with pytest.raises(AcidCasConflictError, match="same transaction"):
        kernel.commit(
            transaction_id="tx-outbox-3",
            request_id="req-outbox-3",
            request_checksum="sha256:req-outbox-3",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-3",
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
                    event_id="evt-3",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-missing",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-3",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(AcidCasConflictError, match="already committed"):
        kernel.commit(
            transaction_id="tx-outbox-4",
            request_id="req-outbox-4",
            request_checksum="sha256:req-outbox-4",
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
            outbox_events=(
                OutboxEventWrite(
                    event_id="evt-1",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=2,
                    operation_id="op-4",
                    payload_hash=payload_hash_for({"status": "processing"}),
                    payload={"status": "processing"},
                ),
            ),
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


def test_context2_outbox_rejects_forged_payload_or_hash() -> None:
    kernel = AcidCasKernel()

    with pytest.raises(AcidCasConflictError, match="payload does not match"):
        kernel.commit(
            transaction_id="tx-outbox-forged-payload",
            request_id="req-outbox-forged-payload",
            request_checksum="sha256:req-outbox-forged-payload",
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
                    event_id="evt-forged-payload",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-forged-payload",
                    payload_hash=payload_hash_for({"status": "done"}),
                    payload={"status": "done"},
                ),
            ),
        )

    with pytest.raises(AcidCasConflictError, match="payload hash"):
        kernel.commit(
            transaction_id="tx-outbox-forged-hash",
            request_id="req-outbox-forged-hash",
            request_checksum="sha256:req-outbox-forged-hash",
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
                OutboxEventWrite(
                    event_id="evt-forged-hash",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-2",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-forged-hash",
                    payload_hash=payload_hash_for({"status": "done"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(KeyError):
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )
    with pytest.raises(KeyError):
        kernel.get(
            entity_type="run",
            entity_id="run-2",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )
    with pytest.raises(KeyError):
        kernel.get_outbox_event(
            event_id="evt-forged-payload",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        )
    with pytest.raises(KeyError):
        kernel.get_outbox_event(
            event_id="evt-forged-hash",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-2"),
        )


def test_context2_outbox_rejects_duplicate_events_in_same_transaction_atomically() -> None:
    kernel = AcidCasKernel()

    with pytest.raises(AcidCasConflictError, match="more than once"):
        kernel.commit(
            transaction_id="tx-outbox-duplicate-same-transaction",
            request_id="req-outbox-duplicate-same-transaction",
            request_checksum="sha256:req-outbox-duplicate-same-transaction",
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
                    event_id="evt-duplicate",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-duplicate-1",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
                OutboxEventWrite(
                    event_id="evt-duplicate",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-duplicate-2",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(KeyError):
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )
    with pytest.raises(KeyError):
        kernel.get_outbox_event(
            event_id="evt-duplicate",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        )


def test_context2_outbox_rejects_non_canonical_resource_identity() -> None:
    kernel = AcidCasKernel()

    with pytest.raises(AcidCasConflictError, match="non-empty colon-free entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.commit(
            transaction_id="tx-outbox-invalid-identity",
            request_id="req-outbox-invalid-identity",
            request_checksum="sha256:req-outbox-invalid-identity",
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
                    event_id="evt-invalid-identity",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-invalid-identity",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(KeyError):
        kernel.get(
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
        )

    with pytest.raises(AcidCasConflictError, match="colon-free"):
        kernel.commit(
            transaction_id="tx-outbox-invalid-colon",
            request_id="req-outbox-invalid-colon",
            request_checksum="sha256:req-outbox-invalid-colon",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run:1",
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
                    event_id="evt-invalid-colon",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run:1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-invalid-colon",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(AcidCasConflictError, match="event_id must be non-empty"):
        kernel.commit(
            transaction_id="tx-outbox-blank-event",
            request_id="req-outbox-blank-event",
            request_checksum="sha256:req-outbox-blank-event",
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
                OutboxEventWrite(
                    event_id=" ",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-2",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-blank-event",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(AcidCasConflictError, match="event_id must be non-empty"):
        kernel.commit(
            transaction_id="tx-outbox-padded-event",
            request_id="req-outbox-padded-event",
            request_checksum="sha256:req-outbox-padded-event",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-3",
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
                    event_id=" evt-padded ",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-3",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-padded-event",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(AcidCasConflictError, match="non-empty colon-free entity_type:tenant_id:owner_id:project_id:entity_id"):
        kernel.commit(
            transaction_id="tx-outbox-padded-identity",
            request_id="req-outbox-padded-identity",
            request_checksum="sha256:req-outbox-padded-identity",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-3",
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
                    event_id="evt-padded-identity",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-3",
                    tenant_id="tenant-1",
                    owner_id=" owner-1 ",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-padded-identity",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )


def test_context2_outbox_replays_committed_transaction_without_duplicate_events() -> None:
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
    outbox_events = (
        OutboxEventWrite(
            event_id="evt-replay-1",
            event_type="run.status.changed",
            entity_type="run",
            entity_id="run-1",
            tenant_id="tenant-1",
            owner_id="owner-1",
            project_id="project-1",
            resource_version=1,
            operation_id="op-replay-1",
            payload_hash=payload_hash_for({"status": "queued"}),
            payload={"status": "queued"},
        ),
    )

    first = kernel.commit(
        transaction_id="tx-outbox-replay-1",
        request_id="req-outbox-replay-1",
        request_checksum="sha256:req-outbox-replay-1",
        writes=writes,
        outbox_events=outbox_events,
    )
    replayed = kernel.commit(
        transaction_id="tx-outbox-replay-1",
        request_id="req-outbox-replay-1",
        request_checksum="sha256:req-outbox-replay-1",
        writes=writes,
        outbox_events=outbox_events,
    )

    assert first.outcome == "applied"
    assert replayed.outcome == "replayed"
    assert replayed.replayed is True
    assert len(replayed.outbox_events) == 1
    assert replayed.outbox_events[0].event_id == "evt-replay-1"
    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        lock_ttl_seconds=30,
        limit=10,
    )
    assert len(acquired) == 1
    assert acquired[0].event_id == "evt-replay-1"
    assert acquired[0].attempt_count == 1

    with pytest.raises(AcidCasConflictError, match="replay checksum"):
        kernel.commit(
            transaction_id="tx-outbox-replay-1",
            request_id="req-outbox-replay-1",
            request_checksum="sha256:req-outbox-replay-1",
            writes=writes,
            outbox_events=(
                OutboxEventWrite(
                    event_id="evt-replay-1",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-1",
                    tenant_id="tenant-1",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-replay-1",
                    payload_hash="sha256:evt-replay-drift",
                    payload={"status": "queued"},
                ),
            ),
        )

    with pytest.raises(AcidCasConflictError, match="same transaction"):
        kernel.commit(
            transaction_id="tx-outbox-4",
            request_id="req-outbox-4",
            request_checksum="sha256:req-outbox-4",
            writes=(
                TransactionWrite(
                    entity_type="run",
                    entity_id="run-4",
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
                    event_id="evt-4",
                    event_type="run.status.changed",
                    entity_type="run",
                    entity_id="run-4",
                    tenant_id="tenant-2",
                    owner_id="owner-1",
                    project_id="project-1",
                    resource_version=1,
                    operation_id="op-4",
                    payload_hash=payload_hash_for({"status": "queued"}),
                    payload={"status": "queued"},
                ),
            ),
        )


def test_context2_outbox_redelivery_is_at_least_once() -> None:
    base = datetime(2026, 7, 11, 10, 0, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)

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
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    first_attempt = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(first_attempt) == 1
    assert first_attempt[0].state == "DELIVERING"
    assert first_attempt[0].attempt_count == 1
    assert first_attempt[0].locked_by == "worker-1"
    first_token = outbox_lock_token_for(first_attempt, "evt-1")
    assert first_token != payload_hash_for(
        {
            "dispatcher_id": "worker-1",
            "resource_id": scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            "event_id": "evt-1",
            "attempt_count": 1,
            "acquired_at": base.isoformat(),
        }
    )
    readable_event = kernel.get_outbox_event(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    )
    assert readable_event.locked_by is None
    assert readable_event.lock_token is None

    clock.set(base + timedelta(seconds=31))
    redelivered = kernel.acquire_outbox_events(
        dispatcher_id="worker-2",
        now=base + timedelta(seconds=31),
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(redelivered) == 1
    assert redelivered[0].event_id == "evt-1"
    assert redelivered[0].state == "DELIVERING"
    assert redelivered[0].attempt_count == 2
    assert redelivered[0].locked_by == "worker-2"

    retry = kernel.retry_outbox_event(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        dispatcher_id="worker-2",
        lock_token=outbox_lock_token_for(redelivered, "evt-1"),
        next_attempt_at=base + timedelta(seconds=90),
        last_error="transient timeout",
    )
    assert retry.state == "PENDING"
    assert retry.attempt_count == 2
    assert retry.last_error == "transient timeout"
    assert retry.locked_by is None

    clock.set(base + timedelta(seconds=89))
    assert (
        kernel.acquire_outbox_events(
            dispatcher_id="worker-3",
            now=base + timedelta(seconds=89),
            lock_ttl_seconds=30,
            limit=1,
        )
        == ()
    )

    clock.set(base + timedelta(seconds=91))
    final_attempt = kernel.acquire_outbox_events(
        dispatcher_id="worker-3",
        now=base + timedelta(seconds=91),
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(final_attempt) == 1
    assert final_attempt[0].event_id == "evt-1"
    assert final_attempt[0].attempt_count == 3
    assert final_attempt[0].locked_by == "worker-3"

    succeeded = kernel.mark_outbox_event_succeeded(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        dispatcher_id="worker-3",
        lock_token=outbox_lock_token_for(final_attempt, "evt-1"),
    )
    assert succeeded.state == "SUCCEEDED"
    assert succeeded.attempt_count == 3
    assert succeeded.locked_by is None
    clock.set(base + timedelta(seconds=200))
    assert (
        kernel.acquire_outbox_events(
            dispatcher_id="worker-4",
            now=base + timedelta(seconds=200),
            lock_ttl_seconds=30,
            limit=1,
        )
        == ()
    )


def test_context2_outbox_rejects_non_positive_lock_ttl() -> None:
    kernel = AcidCasKernel()
    kernel.commit(
        transaction_id="tx-outbox-ttl-1",
        request_id="req-outbox-ttl-1",
        request_checksum="sha256:req-outbox-ttl-1",
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
                event_id="evt-ttl-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-ttl-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    with pytest.raises(AcidCasConflictError, match="Outbox lock TTL must be a positive second value"):
        kernel.acquire_outbox_events(
            dispatcher_id="worker-1",
            lock_ttl_seconds=0,
            limit=1,
        )


def test_context2_outbox_rejects_wrong_dispatcher_transition() -> None:
    base = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    kernel = AcidCasKernel(clock=MutableClock(base))

    kernel.commit(
        transaction_id="tx-outbox-owner-1",
        request_id="req-outbox-owner-1",
        request_checksum="sha256:req-outbox-owner-1",
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
                event_id="evt-owner-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-owner-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    with pytest.raises(AcidCasConflictError, match="does not own outbox event"):
        kernel.mark_outbox_event_succeeded(
            event_id="evt-owner-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            dispatcher_id="worker-2",
            lock_token=outbox_lock_token_for(acquired, "evt-owner-1"),
        )


def test_context2_outbox_rejects_blank_dispatcher_and_consumer_identity() -> None:
    base = datetime(2026, 7, 11, 12, 30, tzinfo=UTC)
    kernel = AcidCasKernel(clock=MutableClock(base))

    kernel.commit(
        transaction_id="tx-outbox-identity-1",
        request_id="req-outbox-identity-1",
        request_checksum="sha256:req-outbox-identity-1",
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
                event_id="evt-identity-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-identity-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    with pytest.raises(AcidCasConflictError, match="dispatcher_id must be non-empty"):
        kernel.acquire_outbox_events(
            dispatcher_id=" ",
            now=base,
            lock_ttl_seconds=30,
            limit=1,
        )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    with pytest.raises(AcidCasConflictError, match="dispatcher_id must be non-empty"):
        kernel.mark_outbox_event_succeeded(
            event_id="evt-identity-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            dispatcher_id=" ",
            lock_token=outbox_lock_token_for(acquired, "evt-identity-1"),
        )
    with pytest.raises(AcidCasConflictError, match="consumer_name must be non-empty"):
        kernel.record_consumer_delivery(
            event_id="evt-identity-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name=" ",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-identity-1"),
        )


def test_context2_outbox_scopes_duplicate_event_ids_by_resource_identity() -> None:
    kernel = AcidCasKernel()

    first = kernel.commit(
        transaction_id="tx-outbox-scope-1",
        request_id="req-outbox-scope-1",
        request_checksum="sha256:req-outbox-scope-1",
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
                event_id="evt-shared",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-scope-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )
    second = kernel.commit(
        transaction_id="tx-outbox-scope-2",
        request_id="req-outbox-scope-2",
        request_checksum="sha256:req-outbox-scope-2",
        writes=(
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-2",
                owner_id="owner-2",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"status": "queued"},
            ),
        ),
        outbox_events=(
            OutboxEventWrite(
                event_id="evt-shared",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-2",
                owner_id="owner-2",
                project_id="project-1",
                resource_version=1,
                operation_id="op-scope-2",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    assert first.outbox_events[0].resource_id == scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    assert second.outbox_events[0].resource_id == scoped_resource_id("run", "tenant-2", "owner-2", "project-1", "run-1")
    assert kernel.get_outbox_event(
        event_id="evt-shared",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
    ).payload_hash == payload_hash_for({"status": "queued"})
    assert kernel.get_outbox_event(
        event_id="evt-shared",
        resource_id=scoped_resource_id("run", "tenant-2", "owner-2", "project-1", "run-1"),
    ).payload_hash == payload_hash_for({"status": "queued"})


def test_context2_outbox_consumer_dedupe_scopes_same_event_id_by_resource_identity() -> None:
    kernel = AcidCasKernel()

    kernel.commit(
        transaction_id="tx-outbox-scope-delivery-1",
        request_id="req-outbox-scope-delivery-1",
        request_checksum="sha256:req-outbox-scope-delivery-1",
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
            TransactionWrite(
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-2",
                owner_id="owner-2",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"status": "queued"},
            ),
        ),
        outbox_events=(
            OutboxEventWrite(
                event_id="evt-shared",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-scope-delivery-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
            OutboxEventWrite(
                event_id="evt-shared",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-2",
                owner_id="owner-2",
                project_id="project-1",
                resource_version=1,
                operation_id="op-scope-delivery-2",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        lock_ttl_seconds=30,
        limit=10,
    )
    assert len(acquired) == 2

    first_resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")
    second_resource_id = scoped_resource_id("run", "tenant-2", "owner-2", "project-1", "run-1")

    first_resource = kernel.record_consumer_delivery(
        event_id="evt-shared",
        resource_id=first_resource_id,
        event_type="run.status.changed",
        consumer_name="walkthrough-consumer",
        resource_version=1,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-shared", first_resource_id),
    )
    second_resource = kernel.record_consumer_delivery(
        event_id="evt-shared",
        resource_id=second_resource_id,
        event_type="run.status.changed",
        consumer_name="walkthrough-consumer",
        resource_version=1,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-shared", second_resource_id),
    )
    duplicate_first = kernel.record_consumer_delivery(
        event_id="evt-shared",
        resource_id=first_resource_id,
        event_type="run.status.changed",
        consumer_name="walkthrough-consumer",
        resource_version=1,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-shared", first_resource_id),
    )

    assert first_resource.duplicate is False
    assert second_resource.duplicate is False
    assert duplicate_first.duplicate is True


def test_context2_outbox_consumer_dedupes_duplicate_delivery() -> None:
    kernel = AcidCasKernel()

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
            TransactionWrite(
                entity_type="run",
                entity_id="run-2",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                expected_version=None,
                state="OPEN",
                payload={"status": "processing"},
            ),
        ),
        outbox_events=(
            OutboxEventWrite(
                event_id="evt-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
            OutboxEventWrite(
                event_id="evt-2",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-2",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-2",
                payload_hash=payload_hash_for({"status": "processing"}),
                payload={"status": "processing"},
            ),
        ),
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
                expected_version=1,
                state="OPEN",
                payload={"status": "done"},
            ),
        ),
        outbox_events=(
            OutboxEventWrite(
                event_id="evt-3",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-2",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=2,
                operation_id="op-3",
                payload_hash=payload_hash_for({"status": "done"}),
                payload={"status": "done"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        lock_ttl_seconds=30,
        limit=10,
    )
    assert {event.event_id for event in acquired} == {"evt-1", "evt-2", "evt-3"}

    first = kernel.record_consumer_delivery(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        event_type="run.status.changed",
        consumer_name="walkthrough-consumer",
        resource_version=1,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-1"),
    )
    duplicate = kernel.record_consumer_delivery(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        event_type="run.status.changed",
        consumer_name="walkthrough-consumer",
        resource_version=1,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-1"),
    )
    other_version = kernel.record_consumer_delivery(
        event_id="evt-3",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-2"),
        event_type="run.status.changed",
        consumer_name="walkthrough-consumer",
        resource_version=2,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-3"),
    )
    other_consumer = kernel.record_consumer_delivery(
        event_id="evt-2",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-2"),
        event_type="run.status.changed",
        consumer_name="audit-consumer",
        resource_version=1,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-2"),
    )

    assert first.duplicate is False
    assert first.delivery_count == 1
    assert duplicate.duplicate is True
    assert duplicate.delivery_count == 2
    assert other_version.duplicate is False
    assert other_version.delivery_count == 1
    assert other_consumer.duplicate is False
    assert other_consumer.delivery_count == 1


def test_context2_outbox_consumer_delivery_requires_matching_committed_event() -> None:
    kernel = AcidCasKernel()

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
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    with pytest.raises(AcidCasConflictError, match="No committed outbox event"):
        kernel.record_consumer_delivery(
            event_id="evt-missing",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token="missing-lock-token",
        )

    with pytest.raises(AcidCasConflictError, match="requires active dispatcher ownership"):
        kernel.record_consumer_delivery(
            event_id="evt-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token="stale-lock-token",
        )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    with pytest.raises(AcidCasConflictError, match="does not match committed outbox event"):
        kernel.record_consumer_delivery(
            event_id="evt-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="other.event",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-1"),
        )

    with pytest.raises(AcidCasConflictError, match="does not match committed outbox event"):
        kernel.record_consumer_delivery(
            event_id="evt-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=2,
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-1"),
        )


def test_context2_outbox_consumer_delivery_rejects_expired_or_superseded_dispatch() -> None:
    base = datetime(2026, 7, 11, 14, 0, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)

    kernel.commit(
        transaction_id="tx-outbox-stale-1",
        request_id="req-outbox-stale-1",
        request_checksum="sha256:req-outbox-stale-1",
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
                event_id="evt-stale-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-stale-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    clock.set(base + timedelta(seconds=31))
    with pytest.raises(AcidCasConflictError, match="requires active dispatcher ownership"):
        kernel.record_consumer_delivery(
            event_id="evt-stale-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-stale-1"),
            now=base + timedelta(seconds=31),
        )

    reacquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-2",
        now=base + timedelta(seconds=31),
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(reacquired) == 1

    clock.set(base + timedelta(seconds=32))
    with pytest.raises(AcidCasConflictError, match="requires active dispatcher ownership"):
        kernel.record_consumer_delivery(
            event_id="evt-stale-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-stale-1"),
            now=base + timedelta(seconds=32),
        )


def test_context2_outbox_rejects_stale_same_dispatcher_lock_token() -> None:
    base = datetime(2026, 7, 11, 14, 30, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")

    kernel.commit(
        transaction_id="tx-outbox-stale-token-1",
        request_id="req-outbox-stale-token-1",
        request_checksum="sha256:req-outbox-stale-token-1",
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
                event_id="evt-stale-token-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-stale-token-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    first_attempt = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    first_token = outbox_lock_token_for(first_attempt, "evt-stale-token-1")

    clock.set(base + timedelta(seconds=31))
    second_attempt = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base + timedelta(seconds=31),
        lock_ttl_seconds=30,
        limit=1,
    )
    second_token = outbox_lock_token_for(second_attempt, "evt-stale-token-1")
    assert second_token != first_token

    clock.set(base + timedelta(seconds=32))
    with pytest.raises(AcidCasConflictError, match="does not own outbox event"):
        kernel.mark_outbox_event_succeeded(
            event_id="evt-stale-token-1",
            resource_id=resource_id,
            dispatcher_id="worker-1",
            lock_token=first_token,
            now=base + timedelta(seconds=32),
        )
    with pytest.raises(AcidCasConflictError, match="requires active dispatcher ownership"):
        kernel.record_consumer_delivery(
            event_id="evt-stale-token-1",
            resource_id=resource_id,
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token=first_token,
            now=base + timedelta(seconds=32),
        )

    succeeded = kernel.mark_outbox_event_succeeded(
        event_id="evt-stale-token-1",
        resource_id=resource_id,
        dispatcher_id="worker-1",
        lock_token=second_token,
        now=base + timedelta(seconds=32),
    )
    assert succeeded.state == "SUCCEEDED"


def test_context2_outbox_retry_normalizes_naive_next_attempt_at() -> None:
    base = datetime(2026, 7, 11, 15, 0, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)
    resource_id = scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1")

    kernel.commit(
        transaction_id="tx-outbox-naive-retry-1",
        request_id="req-outbox-naive-retry-1",
        request_checksum="sha256:req-outbox-naive-retry-1",
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
                event_id="evt-naive-retry-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-naive-retry-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    retried = kernel.retry_outbox_event(
        event_id="evt-naive-retry-1",
        resource_id=resource_id,
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-naive-retry-1"),
        next_attempt_at=datetime(2026, 7, 11, 15, 1),
        last_error="transient",
    )
    assert retried.next_attempt_at == "2026-07-11T15:01:00+00:00"

    clock.set(datetime(2026, 7, 11, 15, 2, tzinfo=UTC))
    reacquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-2",
        now=datetime(2026, 7, 11, 15, 2, tzinfo=UTC),
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(reacquired) == 1
    assert reacquired[0].event_id == "evt-naive-retry-1"


def test_context2_outbox_marks_dispatch_failure_terminal() -> None:
    base = datetime(2026, 7, 11, 12, 0, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)

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
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    failed = kernel.mark_outbox_event_failed(
        event_id="evt-1",
        resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
        dispatcher_id="worker-1",
        lock_token=outbox_lock_token_for(acquired, "evt-1"),
        last_error="permanent schema mismatch",
    )
    assert failed.state == "FAILED"
    assert failed.attempt_count == 1
    assert failed.last_error == "permanent schema mismatch"
    assert failed.locked_by is None
    clock.set(base + timedelta(minutes=5))
    assert (
        kernel.acquire_outbox_events(
            dispatcher_id="worker-2",
            now=base + timedelta(minutes=5),
            lock_ttl_seconds=30,
            limit=1,
        )
        == ()
    )


def test_context2_outbox_rejects_transition_after_lock_expiry() -> None:
    base = datetime(2026, 7, 11, 13, 0, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)

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
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    clock.set(base + timedelta(seconds=31))
    with pytest.raises(AcidCasConflictError, match="lock for outbox event .*evt-1 has expired"):
        kernel.mark_outbox_event_succeeded(
            event_id="evt-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-1"),
            now=base + timedelta(seconds=31),
        )


def test_context2_outbox_lock_expiry_uses_kernel_clock_not_caller_timestamp() -> None:
    base = datetime(2026, 7, 11, 13, 15, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)

    kernel.commit(
        transaction_id="tx-outbox-clock-1",
        request_id="req-outbox-clock-1",
        request_checksum="sha256:req-outbox-clock-1",
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
                event_id="evt-clock-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-clock-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )
    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    clock.set(base + timedelta(seconds=31))
    with pytest.raises(AcidCasConflictError, match="lock for outbox event .*evt-clock-1 has expired"):
        kernel.mark_outbox_event_succeeded(
            event_id="evt-clock-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-clock-1"),
            now=base + timedelta(seconds=1),
        )
    with pytest.raises(AcidCasConflictError, match="requires active dispatcher ownership"):
        kernel.record_consumer_delivery(
            event_id="evt-clock-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            event_type="run.status.changed",
            consumer_name="walkthrough-consumer",
            resource_version=1,
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-clock-1"),
            now=base + timedelta(seconds=1),
        )


def test_context2_outbox_rejects_transition_at_exact_lock_expiry() -> None:
    base = datetime(2026, 7, 11, 13, 30, tzinfo=UTC)
    clock = MutableClock(base)
    kernel = AcidCasKernel(clock=clock)

    kernel.commit(
        transaction_id="tx-outbox-exact-1",
        request_id="req-outbox-exact-1",
        request_checksum="sha256:req-outbox-exact-1",
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
                event_id="evt-exact-1",
                event_type="run.status.changed",
                entity_type="run",
                entity_id="run-1",
                tenant_id="tenant-1",
                owner_id="owner-1",
                project_id="project-1",
                resource_version=1,
                operation_id="op-exact-1",
                payload_hash=payload_hash_for({"status": "queued"}),
                payload={"status": "queued"},
            ),
        ),
    )

    acquired = kernel.acquire_outbox_events(
        dispatcher_id="worker-1",
        now=base,
        lock_ttl_seconds=30,
        limit=1,
    )
    assert len(acquired) == 1

    clock.set(base + timedelta(seconds=30))
    with pytest.raises(AcidCasConflictError, match="lock for outbox event .*evt-exact-1 has expired"):
        kernel.mark_outbox_event_succeeded(
            event_id="evt-exact-1",
            resource_id=scoped_resource_id("run", "tenant-1", "owner-1", "project-1", "run-1"),
            dispatcher_id="worker-1",
            lock_token=outbox_lock_token_for(acquired, "evt-exact-1"),
            now=base + timedelta(seconds=30),
        )
