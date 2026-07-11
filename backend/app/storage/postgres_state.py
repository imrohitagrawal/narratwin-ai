"""PostgreSQL-compatible ACID/CAS storage kernel for Phase 1 Closure CH-02."""

from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Literal

RecordState = Literal["OPEN", "TERMINAL", "ERROR"]
CommitOutcome = Literal["applied", "replayed"]
EntityKey = tuple[str, str, str, str, str]


class AcidCasError(Exception):
    """Base class for CH-02 storage-kernel errors."""


class AcidCasConflictError(AcidCasError):
    """Raised when a CAS transaction conflicts with committed transaction state."""


class AcidCasStaleWriteError(AcidCasError):
    """Raised when a write uses a stale version or targets a terminal row."""


@dataclass(frozen=True, slots=True)
class TransactionWrite:
    entity_type: str
    entity_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    expected_version: int | None
    state: RecordState
    payload: dict[str, Any]
    terminal_reason: str | None = None
    lease_resource_id: str | None = None
    lease_id: str | None = None
    lease_epoch: int | None = None


@dataclass(frozen=True, slots=True)
class StoredRecord:
    entity_type: str
    entity_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    state: RecordState
    version: int
    request_id: str
    request_checksum: str
    transaction_id: str
    payload: dict[str, Any]
    committed_at: str
    terminal_reason: str | None = None


@dataclass(frozen=True, slots=True)
class LeaseRecord:
    resource_id: str
    lease_id: str
    lease_epoch: int
    lease_ttl_ms: int
    acquired_at: str
    heartbeat_at: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class TransactionCommitResult:
    transaction_id: str
    request_id: str
    request_checksum: str
    outcome: CommitOutcome
    replayed: bool
    committed_at: str
    records: tuple[StoredRecord, ...]


class AcidCasKernel:
    """Atomic compare-and-set storage kernel for durable metadata rows."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._records: dict[EntityKey, StoredRecord] = {}
        self._leases: dict[str, LeaseRecord] = {}
        self._lease_epochs: dict[str, int] = {}
        self._transactions: dict[str, TransactionCommitResult] = {}
        self._transaction_fingerprints: dict[str, str] = {}
        self._clock = clock
        self._lock = RLock()

    def get(
        self,
        *,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        owner_id: str,
        project_id: str,
    ) -> StoredRecord:
        key = entity_key(
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            project_id=project_id,
        )
        try:
            return clone_record(self._records[key])
        except KeyError as exc:
            raise KeyError(
                f"No durable record for {entity_type}:{tenant_id}:{owner_id}:{project_id}:{entity_id}"
            ) from exc

    def commit(
        self,
        *,
        transaction_id: str,
        request_id: str,
        request_checksum: str,
        writes: tuple[TransactionWrite, ...],
        now: datetime | None = None,
    ) -> TransactionCommitResult:
        if not writes:
            raise AcidCasConflictError("ACID/CAS transactions must include at least one write.")

        commit_time = self._trusted_now()
        fingerprint = _transaction_fingerprint(
            request_id=request_id,
            request_checksum=request_checksum,
            writes=writes,
        )
        with self._lock:
            replay = self._transactions.get(transaction_id)
            if replay is not None:
                prior_fingerprint = self._transaction_fingerprints[transaction_id]
                if prior_fingerprint != fingerprint:
                    raise AcidCasConflictError(
                        f"Transaction {transaction_id} replay checksum does not match the committed transaction."
                    )
                return replay_result(replay)

            pending_records = self._validate_and_stage(
                transaction_id=transaction_id,
                request_id=request_id,
                request_checksum=request_checksum,
                writes=writes,
                now=commit_time,
            )
            committed_at = _isoformat(commit_time)
            committed_records = tuple(
                StoredRecord(
                    entity_type=record.entity_type,
                    entity_id=record.entity_id,
                    tenant_id=record.tenant_id,
                    owner_id=record.owner_id,
                    project_id=record.project_id,
                    state=record.state,
                    version=record.version,
                    request_id=record.request_id,
                    request_checksum=record.request_checksum,
                    transaction_id=record.transaction_id,
                    payload=deepcopy(record.payload),
                    committed_at=committed_at,
                    terminal_reason=record.terminal_reason,
                )
                for record in pending_records
            )
            stored_result = TransactionCommitResult(
                transaction_id=transaction_id,
                request_id=request_id,
                request_checksum=request_checksum,
                outcome="applied",
                replayed=False,
                committed_at=committed_at,
                records=committed_records,
            )
            for record in committed_records:
                self._records[
                    entity_key(
                        entity_type=record.entity_type,
                        entity_id=record.entity_id,
                        tenant_id=record.tenant_id,
                        owner_id=record.owner_id,
                        project_id=record.project_id,
                    )
                ] = record
            self._transactions[transaction_id] = stored_result
            self._transaction_fingerprints[transaction_id] = fingerprint
            return clone_result(stored_result)

    def acquire_lease(
        self,
        *,
        resource_id: str,
        lease_id: str,
        lease_ttl_ms: int,
        now: datetime | None = None,
    ) -> LeaseRecord:
        if lease_ttl_ms <= 0:
            raise AcidCasConflictError("Lease TTL must be a positive millisecond value.")
        validate_canonical_resource_id(resource_id)
        validate_lease_id(lease_id)

        effective_now = self._trusted_now()
        with self._lock:
            current = self._leases.get(resource_id)
            if current is not None and not _lease_is_expired(current, effective_now):
                raise AcidCasConflictError(
                    f"Lease {resource_id} is already held by {current.lease_id} through {current.expires_at}."
                )

            lease_epoch = self._lease_epochs.get(resource_id, 0) + 1
            stamped_now = _isoformat(effective_now)
            lease = LeaseRecord(
                resource_id=resource_id,
                lease_id=lease_id,
                lease_epoch=lease_epoch,
                lease_ttl_ms=lease_ttl_ms,
                acquired_at=stamped_now,
                heartbeat_at=stamped_now,
                expires_at=_isoformat(effective_now + timedelta(milliseconds=lease_ttl_ms)),
            )
            self._leases[resource_id] = lease
            self._lease_epochs[resource_id] = lease_epoch
            return clone_lease(lease)

    def heartbeat_lease(
        self,
        *,
        resource_id: str,
        lease_id: str,
        lease_epoch: int,
        now: datetime | None = None,
    ) -> LeaseRecord:
        validate_canonical_resource_id(resource_id)
        validate_lease_id(lease_id)
        effective_now = self._trusted_now()
        with self._lock:
            current = self._leases.get(resource_id)
            if current is None or _lease_is_expired(current, effective_now):
                raise AcidCasStaleWriteError(
                    f"Lease {resource_id} is expired and owner {lease_id} must reacquire before heartbeating."
                )
            if current.lease_epoch != lease_epoch:
                raise AcidCasStaleWriteError(
                    f"Lease {resource_id} expected lease epoch {lease_epoch} but durable lease epoch is {current.lease_epoch}."
                )
            if current.lease_id != lease_id:
                raise AcidCasStaleWriteError(
                    f"Lease {resource_id} expected owner {lease_id} but durable owner is {current.lease_id}."
                )

            renewed = LeaseRecord(
                resource_id=current.resource_id,
                lease_id=current.lease_id,
                lease_epoch=current.lease_epoch,
                lease_ttl_ms=current.lease_ttl_ms,
                acquired_at=current.acquired_at,
                heartbeat_at=_isoformat(effective_now),
                expires_at=_isoformat(effective_now + timedelta(milliseconds=current.lease_ttl_ms)),
            )
            self._leases[resource_id] = renewed
            return clone_lease(renewed)

    def release_lease(
        self,
        *,
        resource_id: str,
        lease_id: str,
        lease_epoch: int,
        now: datetime | None = None,
    ) -> None:
        validate_canonical_resource_id(resource_id)
        validate_lease_id(lease_id)
        effective_now = self._trusted_now()
        with self._lock:
            current = self._leases.get(resource_id)
            if current is None or _lease_is_expired(current, effective_now):
                raise AcidCasStaleWriteError(
                    f"Lease {resource_id} is expired and cannot be released by owner {lease_id}."
                )
            if current.lease_epoch != lease_epoch:
                raise AcidCasStaleWriteError(
                    f"Lease {resource_id} expected lease epoch {lease_epoch} but durable lease epoch is {current.lease_epoch}."
                )
            if current.lease_id != lease_id:
                raise AcidCasStaleWriteError(
                    f"Lease {resource_id} expected owner {lease_id} but durable owner is {current.lease_id}."
                )
            del self._leases[resource_id]

    def get_lease(self, *, resource_id: str, now: datetime | None = None) -> LeaseRecord:
        validate_canonical_resource_id(resource_id)
        effective_now = self._trusted_now()
        try:
            lease = self._leases[resource_id]
        except KeyError as exc:
            raise KeyError(f"No active lease for {resource_id}") from exc
        if _lease_is_expired(lease, effective_now):
            raise KeyError(f"No active lease for {resource_id}")
        return clone_lease(lease)

    def _validate_and_stage(
        self,
        *,
        transaction_id: str,
        request_id: str,
        request_checksum: str,
        writes: tuple[TransactionWrite, ...],
        now: datetime,
    ) -> tuple[StoredRecord, ...]:
        seen_keys: set[EntityKey] = set()
        staged: list[StoredRecord] = []
        for write in writes:
            key = entity_key(
                entity_type=write.entity_type,
                entity_id=write.entity_id,
                tenant_id=write.tenant_id,
                owner_id=write.owner_id,
                project_id=write.project_id,
            )
            if key in seen_keys:
                raise AcidCasConflictError(
                    "Transaction "
                    f"{transaction_id} references "
                    f"{write.entity_type}:{write.tenant_id}:{write.owner_id}:{write.project_id}:{write.entity_id} "
                    "more than once."
                )
            seen_keys.add(key)
            existing = self._records.get(key)
            staged.append(
                self._stage_write(
                    existing=existing,
                    write=write,
                    transaction_id=transaction_id,
                    request_id=request_id,
                    request_checksum=request_checksum,
                    now=now,
                )
            )
        return tuple(staged)

    def _stage_write(
        self,
        *,
        existing: StoredRecord | None,
        write: TransactionWrite,
        transaction_id: str,
        request_id: str,
        request_checksum: str,
        now: datetime,
    ) -> StoredRecord:
        self._validate_lease_guard(write=write, now=now)
        if existing is None:
            if write.expected_version is not None:
                raise AcidCasConflictError(
                    f"{write.entity_type}:{write.entity_id} expected version {write.expected_version} but no durable row exists."
                )
            version = 1
        else:
            if existing.state in ("TERMINAL", "ERROR"):
                raise AcidCasStaleWriteError(
                    f"{write.entity_type}:{write.entity_id} is already {existing.state} at version {existing.version}."
                )
            if write.expected_version is None:
                raise AcidCasConflictError(
                    f"{write.entity_type}:{write.entity_id} already exists at version {existing.version}."
                )
            if write.expected_version < existing.version:
                raise AcidCasStaleWriteError(
                    f"{write.entity_type}:{write.entity_id} expected version {write.expected_version} but durable version is {existing.version}."
                )
            if write.expected_version > existing.version:
                raise AcidCasConflictError(
                    f"{write.entity_type}:{write.entity_id} expected version {write.expected_version} but durable version is {existing.version}."
                )
            version = existing.version + 1

        return StoredRecord(
            entity_type=write.entity_type,
            entity_id=write.entity_id,
            tenant_id=write.tenant_id,
            owner_id=write.owner_id,
            project_id=write.project_id,
            state=write.state,
            version=version,
            request_id=request_id,
            request_checksum=request_checksum,
            transaction_id=transaction_id,
            payload=deepcopy(write.payload),
            committed_at="pending-commit",
            terminal_reason=write.terminal_reason,
        )

    def _validate_lease_guard(self, *, write: TransactionWrite, now: datetime) -> None:
        expected_resource_id = lease_resource_id_for_write(write)
        current = self._leases.get(expected_resource_id)
        requires_fencing = expected_resource_id in self._lease_epochs
        lease_fields = (write.lease_resource_id, write.lease_id, write.lease_epoch)
        if lease_fields == (None, None, None):
            if requires_fencing:
                raise AcidCasStaleWriteError(
                    f"{write.entity_type}:{write.entity_id} is lease-fenced by {expected_resource_id} and requires lease fencing fields."
                )
            return
        if write.lease_resource_id is None or write.lease_id is None or write.lease_epoch is None:
            raise AcidCasConflictError(
                "Lease-guarded writes must include lease_resource_id, lease_id, and lease_epoch together."
            )
        validate_lease_id(write.lease_id)

        if write.lease_resource_id != expected_resource_id:
            raise AcidCasStaleWriteError(
                f"{write.entity_type}:{write.entity_id} lease resource {write.lease_resource_id} does not match scoped row identity {expected_resource_id}."
            )

        if current is None or _lease_is_expired(current, now):
            raise AcidCasStaleWriteError(
                f"{write.entity_type}:{write.entity_id} lease {write.lease_resource_id} is expired."
            )
        if current.lease_epoch != write.lease_epoch:
            raise AcidCasStaleWriteError(
                f"{write.entity_type}:{write.entity_id} expected lease epoch {write.lease_epoch} but durable lease epoch is {current.lease_epoch}."
            )
        if current.lease_id != write.lease_id:
            raise AcidCasStaleWriteError(
                f"{write.entity_type}:{write.entity_id} expected lease owner {write.lease_id} but durable owner is {current.lease_id}."
            )

    def _trusted_now(self) -> datetime:
        if self._clock is None:
            return datetime.now(UTC)
        return _coerce_now(self._clock())


def replay_result(result: TransactionCommitResult) -> TransactionCommitResult:
    replayed = clone_result(result)
    return TransactionCommitResult(
        transaction_id=replayed.transaction_id,
        request_id=replayed.request_id,
        request_checksum=replayed.request_checksum,
        outcome="replayed",
        replayed=True,
        committed_at=replayed.committed_at,
        records=replayed.records,
    )


def clone_result(result: TransactionCommitResult) -> TransactionCommitResult:
    return TransactionCommitResult(
        transaction_id=result.transaction_id,
        request_id=result.request_id,
        request_checksum=result.request_checksum,
        outcome=result.outcome,
        replayed=result.replayed,
        committed_at=result.committed_at,
        records=tuple(clone_record(record) for record in result.records),
    )


def clone_record(record: StoredRecord) -> StoredRecord:
    return StoredRecord(
        entity_type=record.entity_type,
        entity_id=record.entity_id,
        tenant_id=record.tenant_id,
        owner_id=record.owner_id,
        project_id=record.project_id,
        state=record.state,
        version=record.version,
        request_id=record.request_id,
        request_checksum=record.request_checksum,
        transaction_id=record.transaction_id,
        payload=deepcopy(record.payload),
        committed_at=record.committed_at,
        terminal_reason=record.terminal_reason,
    )


def clone_lease(lease: LeaseRecord) -> LeaseRecord:
    return LeaseRecord(
        resource_id=lease.resource_id,
        lease_id=lease.lease_id,
        lease_epoch=lease.lease_epoch,
        lease_ttl_ms=lease.lease_ttl_ms,
        acquired_at=lease.acquired_at,
        heartbeat_at=lease.heartbeat_at,
        expires_at=lease.expires_at,
    )


def entity_key(
    *,
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    owner_id: str,
    project_id: str,
) -> EntityKey:
    return (entity_type, tenant_id, owner_id, project_id, entity_id)


def lease_resource_id_for_write(write: TransactionWrite) -> str:
    return (
        f"{write.entity_type}:{write.tenant_id}:{write.owner_id}:{write.project_id}:{write.entity_id}"
    )


def validate_canonical_resource_id(resource_id: str) -> None:
    parts = resource_id.split(":")
    if len(parts) != 5 or any(part == "" for part in parts):
        raise AcidCasConflictError(
            "Lease resource_id must use canonical entity_type:tenant_id:owner_id:project_id:entity_id identity."
        )


def validate_lease_id(lease_id: str) -> None:
    if not lease_id.strip():
        raise AcidCasConflictError("Lease lease_id must be non-empty.")


def _transaction_fingerprint(
    *,
    request_id: str,
    request_checksum: str,
    writes: tuple[TransactionWrite, ...],
) -> str:
    payload = {
        "requestId": request_id,
        "requestChecksum": request_checksum,
        "writes": [
            {
                "entityType": write.entity_type,
                "entityId": write.entity_id,
                "tenantId": write.tenant_id,
                "ownerId": write.owner_id,
                "projectId": write.project_id,
                "expectedVersion": write.expected_version,
                "state": write.state,
                "payload": write.payload,
                "terminalReason": write.terminal_reason,
                "leaseResourceId": write.lease_resource_id,
                "leaseId": write.lease_id,
                "leaseEpoch": write.lease_epoch,
            }
            for write in writes
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _now() -> str:
    return _isoformat(datetime.now(UTC))


def _coerce_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    return now.astimezone(UTC)


def _isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _lease_is_expired(lease: LeaseRecord, now: datetime) -> bool:
    return now >= datetime.fromisoformat(lease.expires_at).astimezone(UTC)
