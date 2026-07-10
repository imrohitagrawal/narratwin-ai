"""PostgreSQL-compatible ACID/CAS storage kernel for Phase 1 Closure CH-02."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
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

    def __init__(self) -> None:
        self._records: dict[EntityKey, StoredRecord] = {}
        self._transactions: dict[str, TransactionCommitResult] = {}
        self._transaction_fingerprints: dict[str, str] = {}
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
    ) -> TransactionCommitResult:
        if not writes:
            raise AcidCasConflictError("ACID/CAS transactions must include at least one write.")

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
            )
            committed_at = _now()
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

    def _validate_and_stage(
        self,
        *,
        transaction_id: str,
        request_id: str,
        request_checksum: str,
        writes: tuple[TransactionWrite, ...],
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
    ) -> StoredRecord:
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


def entity_key(
    *,
    entity_type: str,
    entity_id: str,
    tenant_id: str,
    owner_id: str,
    project_id: str,
) -> EntityKey:
    return (entity_type, tenant_id, owner_id, project_id, entity_id)


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
            }
            for write in writes
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _now() -> str:
    return datetime.now(UTC).isoformat()
