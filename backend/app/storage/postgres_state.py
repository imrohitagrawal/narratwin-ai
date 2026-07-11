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
OperationState = Literal[
    "RUNNING",
    "REPLAYING",
    "FAILED_TRANSIENT",
    "TERMINAL_SUCCESS",
    "TERMINAL_ERROR",
]


class AcidCasError(Exception):
    """Base class for CH-02 storage-kernel errors."""


class AcidCasConflictError(AcidCasError):
    """Raised when a CAS transaction conflicts with committed transaction state."""


class AcidCasStaleWriteError(AcidCasError):
    """Raised when a write uses a stale version or targets a terminal row."""


class AcidCasStaleOwnerError(AcidCasStaleWriteError):
    """Raised when a non-terminal operation write uses a stale owner/epoch."""


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


@dataclass(frozen=True, slots=True)
class OperationScope:
    tenant_id: str
    owner_id: str
    project_id: str
    resource_id: str


@dataclass(frozen=True, slots=True)
class OperationRecord:
    operation_id: str
    scope: OperationScope
    payload_hash: str
    state: OperationState
    version: int
    request_id: str
    transaction_id: str
    lease_owner_id: str
    lease_epoch: int
    committed_at: str
    response_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class OperationCommitResult:
    operation_id: str
    request_id: str
    payload_hash: str
    outcome: CommitOutcome
    replayed: bool
    committed_at: str
    record: OperationRecord


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

    def get_operation(self, *, operation_id: str, scope: OperationScope) -> OperationRecord:
        validate_operation_scope(scope)
        key = operation_entity_key(operation_id=operation_id, scope=scope)
        try:
            return clone_operation_record(operation_record_from_stored_record(self._records[key]))
        except KeyError as exc:
            raise KeyError(
                "No durable operation for "
                f"{operation_id}:{scope.tenant_id}:{scope.owner_id}:{scope.project_id}:{scope.resource_id}"
            ) from exc

    def start_operation(
        self,
        *,
        transaction_id: str,
        request_id: str,
        operation_id: str,
        scope: OperationScope,
        payload_hash: str,
        lease_owner_id: str,
        lease_epoch: int,
    ) -> OperationCommitResult:
        validate_operation_scope(scope)
        with self._lock:
            existing = self._get_optional_operation(operation_id=operation_id, scope=scope)
            if existing is None:
                stored = self._store_operation_record(
                    operation_id=operation_id,
                    scope=scope,
                    payload_hash=payload_hash,
                    state="RUNNING",
                    version=1,
                    request_id=request_id,
                    transaction_id=transaction_id,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                )
                return clone_operation_result(
                    OperationCommitResult(
                        operation_id=operation_id,
                        request_id=request_id,
                        payload_hash=payload_hash,
                        outcome="applied",
                        replayed=False,
                        committed_at=stored.committed_at,
                        record=stored,
                    )
                )

            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state in ("TERMINAL_SUCCESS", "TERMINAL_ERROR"):
                return replay_operation_result(existing)

            self._assert_operation_owner(
                existing=existing,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            return replay_operation_result(existing)

    def commit_operation_success(
        self,
        *,
        transaction_id: str,
        request_id: str,
        operation_id: str,
        scope: OperationScope,
        payload_hash: str,
        expected_version: int,
        lease_owner_id: str,
        lease_epoch: int,
        response_payload: dict[str, Any],
    ) -> OperationCommitResult:
        validate_operation_scope(scope)
        with self._lock:
            existing = self._get_required_operation(operation_id=operation_id, scope=scope)
            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state == "TERMINAL_SUCCESS":
                if existing.response_payload != response_payload:
                    raise AcidCasConflictError(
                        f"Operation {operation_id} terminal success replay payload does not match the durable response."
                    )
                return replay_operation_result(existing)
            if existing.state == "TERMINAL_ERROR":
                raise AcidCasConflictError(
                    f"Operation {operation_id} is already TERMINAL_ERROR and cannot transition to TERMINAL_SUCCESS."
                )
            self._assert_operation_owner(
                existing=existing,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            self._assert_operation_expected_version(existing=existing, expected_version=expected_version)
            self._assert_operation_state(
                existing=existing,
                allowed_states=("RUNNING", "REPLAYING"),
                next_state="TERMINAL_SUCCESS",
            )
            stored = self._store_operation_record(
                operation_id=operation_id,
                scope=scope,
                payload_hash=payload_hash,
                state="TERMINAL_SUCCESS",
                version=existing.version + 1,
                request_id=request_id,
                transaction_id=transaction_id,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                response_payload=response_payload,
            )
            return clone_operation_result(
                OperationCommitResult(
                    operation_id=operation_id,
                    request_id=request_id,
                    payload_hash=payload_hash,
                    outcome="applied",
                    replayed=False,
                    committed_at=stored.committed_at,
                    record=stored,
                )
            )

    def commit_operation_error(
        self,
        *,
        transaction_id: str,
        request_id: str,
        operation_id: str,
        scope: OperationScope,
        payload_hash: str,
        expected_version: int,
        lease_owner_id: str,
        lease_epoch: int,
        error_payload: dict[str, Any],
    ) -> OperationCommitResult:
        validate_operation_scope(scope)
        with self._lock:
            existing = self._get_required_operation(operation_id=operation_id, scope=scope)
            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state == "TERMINAL_ERROR":
                if existing.error_payload != error_payload:
                    raise AcidCasConflictError(
                        f"Operation {operation_id} terminal error replay payload does not match the durable error."
                    )
                return replay_operation_result(existing)
            if existing.state == "TERMINAL_SUCCESS":
                raise AcidCasConflictError(
                    f"Operation {operation_id} is already TERMINAL_SUCCESS and cannot transition to TERMINAL_ERROR."
                )
            self._assert_operation_owner(
                existing=existing,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            self._assert_operation_expected_version(existing=existing, expected_version=expected_version)
            self._assert_operation_state(
                existing=existing,
                allowed_states=("RUNNING", "REPLAYING"),
                next_state="TERMINAL_ERROR",
            )
            stored = self._store_operation_record(
                operation_id=operation_id,
                scope=scope,
                payload_hash=payload_hash,
                state="TERMINAL_ERROR",
                version=existing.version + 1,
                request_id=request_id,
                transaction_id=transaction_id,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                error_payload=error_payload,
            )
            return clone_operation_result(
                OperationCommitResult(
                    operation_id=operation_id,
                    request_id=request_id,
                    payload_hash=payload_hash,
                    outcome="applied",
                    replayed=False,
                    committed_at=stored.committed_at,
                    record=stored,
                )
            )

    def fail_operation_transient(
        self,
        *,
        transaction_id: str,
        request_id: str,
        operation_id: str,
        scope: OperationScope,
        payload_hash: str,
        expected_version: int,
        lease_owner_id: str,
        lease_epoch: int,
    ) -> OperationCommitResult:
        validate_operation_scope(scope)
        with self._lock:
            existing = self._get_required_operation(operation_id=operation_id, scope=scope)
            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state == "FAILED_TRANSIENT":
                self._assert_operation_owner(
                    existing=existing,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                )
                return replay_operation_result(existing)
            if existing.state in ("TERMINAL_SUCCESS", "TERMINAL_ERROR"):
                return replay_operation_result(existing)
            self._assert_operation_owner(
                existing=existing,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            self._assert_operation_expected_version(existing=existing, expected_version=expected_version)
            self._assert_operation_state(
                existing=existing,
                allowed_states=("RUNNING", "REPLAYING"),
                next_state="FAILED_TRANSIENT",
            )
            stored = self._store_operation_record(
                operation_id=operation_id,
                scope=scope,
                payload_hash=payload_hash,
                state="FAILED_TRANSIENT",
                version=existing.version + 1,
                request_id=request_id,
                transaction_id=transaction_id,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            return clone_operation_result(
                OperationCommitResult(
                    operation_id=operation_id,
                    request_id=request_id,
                    payload_hash=payload_hash,
                    outcome="applied",
                    replayed=False,
                    committed_at=stored.committed_at,
                    record=stored,
                )
            )

    def recover_operation(
        self,
        *,
        transaction_id: str,
        request_id: str,
        operation_id: str,
        scope: OperationScope,
        payload_hash: str,
        expected_version: int,
        lease_owner_id: str,
        lease_epoch: int,
    ) -> OperationCommitResult:
        validate_operation_scope(scope)
        with self._lock:
            existing = self._get_required_operation(operation_id=operation_id, scope=scope)
            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state in ("TERMINAL_SUCCESS", "TERMINAL_ERROR"):
                return replay_operation_result(existing)
            self._assert_operation_expected_version(existing=existing, expected_version=expected_version)
            self._assert_operation_state(
                existing=existing,
                allowed_states=("FAILED_TRANSIENT",),
                next_state="REPLAYING",
            )
            self._assert_recovery_epoch_advance(
                existing=existing,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            stored = self._store_operation_record(
                operation_id=operation_id,
                scope=scope,
                payload_hash=payload_hash,
                state="REPLAYING",
                version=existing.version + 1,
                request_id=request_id,
                transaction_id=transaction_id,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            return clone_operation_result(
                OperationCommitResult(
                    operation_id=operation_id,
                    request_id=request_id,
                    payload_hash=payload_hash,
                    outcome="applied",
                    replayed=False,
                    committed_at=stored.committed_at,
                    record=stored,
                )
            )

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

    def _get_required_operation(self, *, operation_id: str, scope: OperationScope) -> OperationRecord:
        try:
            return operation_record_from_stored_record(self._records[operation_entity_key(operation_id=operation_id, scope=scope)])
        except KeyError as exc:
            raise AcidCasConflictError(
                "Operation does not exist for "
                f"{operation_id}:{scope.tenant_id}:{scope.owner_id}:{scope.project_id}:{scope.resource_id}."
            ) from exc

    def _get_optional_operation(self, *, operation_id: str, scope: OperationScope) -> OperationRecord | None:
        stored = self._records.get(operation_entity_key(operation_id=operation_id, scope=scope))
        if stored is None:
            return None
        return operation_record_from_stored_record(stored)

    def _store_operation_record(
        self,
        *,
        operation_id: str,
        scope: OperationScope,
        payload_hash: str,
        state: OperationState,
        version: int,
        request_id: str,
        transaction_id: str,
        lease_owner_id: str,
        lease_epoch: int,
        response_payload: dict[str, Any] | None = None,
        error_payload: dict[str, Any] | None = None,
    ) -> OperationRecord:
        result = self.commit(
            transaction_id=transaction_id,
            request_id=request_id,
            request_checksum=operation_request_checksum(
                operation_id=operation_id,
                scope=scope,
                payload_hash=payload_hash,
                state=state,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                response_payload=response_payload,
                error_payload=error_payload,
            ),
            writes=(
                TransactionWrite(
                    entity_type="operation",
                    entity_id=operation_entity_id(operation_id=operation_id, scope=scope),
                    tenant_id=scope.tenant_id,
                    owner_id=scope.owner_id,
                    project_id=scope.project_id,
                    expected_version=None if version == 1 else version - 1,
                    state=operation_record_state(state),
                    payload=operation_record_payload(
                        operation_id=operation_id,
                        scope=scope,
                        payload_hash=payload_hash,
                        state=state,
                        lease_owner_id=lease_owner_id,
                        lease_epoch=lease_epoch,
                        response_payload=response_payload,
                        error_payload=error_payload,
                    ),
                ),
            ),
        )
        return operation_record_from_stored_record(result.records[0])

    def _assert_operation_payload_hash(self, *, existing: OperationRecord, payload_hash: str) -> None:
        if existing.payload_hash != payload_hash:
            raise AcidCasConflictError(
                f"Operation {existing.operation_id} payload hash does not match the durable operation."
            )

    def _assert_operation_owner(
        self,
        *,
        existing: OperationRecord,
        lease_owner_id: str,
        lease_epoch: int,
    ) -> None:
        if existing.lease_owner_id != lease_owner_id or existing.lease_epoch != lease_epoch:
            raise AcidCasStaleOwnerError(
                "Operation "
                f"{existing.operation_id} stale owner: expected "
                f"{existing.lease_owner_id}@{existing.lease_epoch} but received "
                f"{lease_owner_id}@{lease_epoch}."
            )

    def _assert_recovery_epoch_advance(
        self,
        *,
        existing: OperationRecord,
        lease_owner_id: str,
        lease_epoch: int,
    ) -> None:
        if lease_owner_id != existing.lease_owner_id:
            raise AcidCasStaleOwnerError(
                "Operation "
                f"{existing.operation_id} recovery owner must remain {existing.lease_owner_id} until "
                "CH-05 durable lease transfer semantics are enforced."
            )
        if lease_owner_id == existing.lease_owner_id and lease_epoch == existing.lease_epoch:
            raise AcidCasConflictError(
                f"Operation {existing.operation_id} recovery requires an explicit epoch advance."
            )
        if lease_epoch <= existing.lease_epoch:
            raise AcidCasStaleOwnerError(
                "Operation "
                f"{existing.operation_id} stale recovery epoch: durable epoch is "
                f"{existing.lease_epoch} but received {lease_owner_id}@{lease_epoch}."
            )

    def _assert_operation_expected_version(self, *, existing: OperationRecord, expected_version: int) -> None:
        if expected_version < existing.version:
            raise AcidCasStaleWriteError(
                f"Operation {existing.operation_id} expected version {expected_version} but durable version is {existing.version}."
            )
        if expected_version > existing.version:
            raise AcidCasConflictError(
                f"Operation {existing.operation_id} expected version {expected_version} but durable version is {existing.version}."
            )

    def _assert_operation_state(
        self,
        *,
        existing: OperationRecord,
        allowed_states: tuple[OperationState, ...],
        next_state: OperationState,
    ) -> None:
        if existing.state not in allowed_states:
            allowed = ", ".join(allowed_states)
            raise AcidCasConflictError(
                f"Operation {existing.operation_id} must be in one of [{allowed}] to transition to {next_state}; found {existing.state}."
            )

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


def clone_operation_result(result: OperationCommitResult) -> OperationCommitResult:
    return OperationCommitResult(
        operation_id=result.operation_id,
        request_id=result.request_id,
        payload_hash=result.payload_hash,
        outcome=result.outcome,
        replayed=result.replayed,
        committed_at=result.committed_at,
        record=clone_operation_record(result.record),
    )


def replay_operation_result(record: OperationRecord) -> OperationCommitResult:
    return OperationCommitResult(
        operation_id=record.operation_id,
        request_id=record.request_id,
        payload_hash=record.payload_hash,
        outcome="replayed",
        replayed=True,
        committed_at=record.committed_at,
        record=clone_operation_record(record),
    )


def clone_operation_record(record: OperationRecord) -> OperationRecord:
    return OperationRecord(
        operation_id=record.operation_id,
        scope=clone_operation_scope(record.scope),
        payload_hash=record.payload_hash,
        state=record.state,
        version=record.version,
        request_id=record.request_id,
        transaction_id=record.transaction_id,
        lease_owner_id=record.lease_owner_id,
        lease_epoch=record.lease_epoch,
        committed_at=record.committed_at,
        response_payload=deepcopy(record.response_payload),
        error_payload=deepcopy(record.error_payload),
    )


def clone_operation_scope(scope: OperationScope) -> OperationScope:
    return OperationScope(
        tenant_id=scope.tenant_id,
        owner_id=scope.owner_id,
        project_id=scope.project_id,
        resource_id=scope.resource_id,
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


def operation_entity_id(*, operation_id: str, scope: OperationScope) -> str:
    return f"{operation_id}::{scope.resource_id}"


def validate_operation_scope(scope: OperationScope) -> None:
    parts = scope.resource_id.split(":")
    if len(parts) != 5 or any(part == "" for part in parts):
        raise AcidCasConflictError(
            "Operation scope resource_id must use canonical entity_type:tenant_id:owner_id:project_id:entity_id identity."
        )
    _, tenant_id, owner_id, project_id, _ = parts
    if (tenant_id, owner_id, project_id) != (scope.tenant_id, scope.owner_id, scope.project_id):
        raise AcidCasConflictError(
            "Operation scope resource_id tenant_id, owner_id, and project_id must match OperationScope."
        )


def operation_entity_key(*, operation_id: str, scope: OperationScope) -> EntityKey:
    return entity_key(
        entity_type="operation",
        entity_id=operation_entity_id(operation_id=operation_id, scope=scope),
        tenant_id=scope.tenant_id,
        owner_id=scope.owner_id,
        project_id=scope.project_id,
    )


def operation_record_state(state: OperationState) -> RecordState:
    if state == "TERMINAL_SUCCESS":
        return "TERMINAL"
    if state == "TERMINAL_ERROR":
        return "ERROR"
    return "OPEN"


def operation_record_payload(
    *,
    operation_id: str,
    scope: OperationScope,
    payload_hash: str,
    state: OperationState,
    lease_owner_id: str,
    lease_epoch: int,
    response_payload: dict[str, Any] | None,
    error_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "operationId": operation_id,
        "resourceId": scope.resource_id,
        "payloadHash": payload_hash,
        "operationState": state,
        "leaseOwnerId": lease_owner_id,
        "leaseEpoch": lease_epoch,
        "responsePayload": deepcopy(response_payload),
        "errorPayload": deepcopy(error_payload),
    }


def operation_request_checksum(
    *,
    operation_id: str,
    scope: OperationScope,
    payload_hash: str,
    state: OperationState,
    lease_owner_id: str,
    lease_epoch: int,
    response_payload: dict[str, Any] | None,
    error_payload: dict[str, Any] | None,
) -> str:
    return json.dumps(
        operation_record_payload(
            operation_id=operation_id,
            scope=scope,
            payload_hash=payload_hash,
            state=state,
            lease_owner_id=lease_owner_id,
            lease_epoch=lease_epoch,
            response_payload=response_payload,
            error_payload=error_payload,
        ),
        sort_keys=True,
        separators=(",", ":"),
    )


def operation_record_from_stored_record(record: StoredRecord) -> OperationRecord:
    payload = record.payload
    scope = OperationScope(
        tenant_id=record.tenant_id,
        owner_id=record.owner_id,
        project_id=record.project_id,
        resource_id=payload["resourceId"],
    )
    return OperationRecord(
        operation_id=payload["operationId"],
        scope=scope,
        payload_hash=payload["payloadHash"],
        state=payload["operationState"],
        version=record.version,
        request_id=record.request_id,
        transaction_id=record.transaction_id,
        lease_owner_id=payload["leaseOwnerId"],
        lease_epoch=payload["leaseEpoch"],
        committed_at=record.committed_at,
        response_payload=deepcopy(payload["responsePayload"]),
        error_payload=deepcopy(payload["errorPayload"]),
    )


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
