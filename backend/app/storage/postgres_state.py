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
OutboxKey = tuple[str, str, str, int]
ConsumerDeliveryKey = tuple[str, str, str, str, int]
OperationState = Literal[
    "RUNNING",
    "REPLAYING",
    "FAILED_TRANSIENT",
    "TERMINAL_SUCCESS",
    "TERMINAL_ERROR",
]
OutboxState = Literal["PENDING", "DELIVERING", "SUCCEEDED", "FAILED"]


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
class OutboxEventWrite:
    event_id: str
    event_type: str
    resource_id: str
    resource_version: int
    operation_id: str
    payload_hash: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class OutboxRecord:
    event_id: str
    event_type: str
    resource_id: str
    resource_version: int
    operation_id: str
    payload_hash: str
    payload: dict[str, Any]
    state: OutboxState
    attempt_count: int
    next_attempt_at: str | None
    locked_by: str | None
    locked_until: str | None
    lock_token: str | None
    last_error: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ConsumerDeliveryRecord:
    event_id: str
    event_type: str
    resource_id: str
    resource_version: int
    consumer_name: str
    delivered_at: str


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
    outbox_events: tuple[OutboxRecord, ...] = ()


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

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._records: dict[EntityKey, StoredRecord] = {}
        self._outbox: dict[OutboxKey, OutboxRecord] = {}
        self._consumer_deliveries: dict[ConsumerDeliveryKey, ConsumerDeliveryRecord] = {}
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
        validate_operation_identity(
            operation_id=operation_id,
            payload_hash=payload_hash,
            lease_owner_id=lease_owner_id,
        )
        with self._lock:
            existing = self._get_optional_operation(operation_id=operation_id, scope=scope)
            if existing is None:
                self._assert_operation_active_lease(
                    operation_id=operation_id,
                    scope=scope,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                    now=self._trusted_now(),
                )
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
        validate_operation_identity(
            operation_id=operation_id,
            payload_hash=payload_hash,
            lease_owner_id=lease_owner_id,
        )
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
            self._assert_operation_active_lease(
                operation_id=operation_id,
                scope=scope,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                now=self._trusted_now(),
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
        validate_operation_identity(
            operation_id=operation_id,
            payload_hash=payload_hash,
            lease_owner_id=lease_owner_id,
        )
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
            self._assert_operation_active_lease(
                operation_id=operation_id,
                scope=scope,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                now=self._trusted_now(),
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
        validate_operation_identity(
            operation_id=operation_id,
            payload_hash=payload_hash,
            lease_owner_id=lease_owner_id,
        )
        with self._lock:
            existing = self._get_required_operation(operation_id=operation_id, scope=scope)
            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state == "FAILED_TRANSIENT":
                self._assert_operation_owner(
                    existing=existing,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                )
                self._assert_operation_active_lease(
                    operation_id=operation_id,
                    scope=scope,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                    now=self._trusted_now(),
                )
                return replay_operation_result(existing)
            if existing.state in ("TERMINAL_SUCCESS", "TERMINAL_ERROR"):
                return replay_operation_result(existing)
            self._assert_operation_owner(
                existing=existing,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
            )
            self._assert_operation_active_lease(
                operation_id=operation_id,
                scope=scope,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                now=self._trusted_now(),
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
        validate_operation_identity(
            operation_id=operation_id,
            payload_hash=payload_hash,
            lease_owner_id=lease_owner_id,
        )
        with self._lock:
            existing = self._get_required_operation(operation_id=operation_id, scope=scope)
            self._assert_operation_payload_hash(existing=existing, payload_hash=payload_hash)
            if existing.state in ("TERMINAL_SUCCESS", "TERMINAL_ERROR"):
                return replay_operation_result(existing)
            if existing.state == "REPLAYING" and existing.transaction_id == transaction_id:
                self._assert_operation_active_lease(
                    operation_id=operation_id,
                    scope=scope,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                    now=self._trusted_now(),
                )
                stored = self._store_operation_record(
                    operation_id=operation_id,
                    scope=scope,
                    payload_hash=payload_hash,
                    state="REPLAYING",
                    version=expected_version + 1,
                    request_id=request_id,
                    transaction_id=transaction_id,
                    lease_owner_id=lease_owner_id,
                    lease_epoch=lease_epoch,
                )
                return replay_operation_result(stored)
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
            self._assert_operation_active_lease(
                operation_id=operation_id,
                scope=scope,
                lease_owner_id=lease_owner_id,
                lease_epoch=lease_epoch,
                now=self._trusted_now(),
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
        outbox_events: tuple[OutboxEventWrite, ...] = (),
        now: datetime | None = None,
    ) -> TransactionCommitResult:
        return self._commit(
            transaction_id=transaction_id,
            request_id=request_id,
            request_checksum=request_checksum,
            writes=writes,
            outbox_events=outbox_events,
            allow_operation_rows=False,
            now=now,
        )

    def _commit(
        self,
        *,
        transaction_id: str,
        request_id: str,
        request_checksum: str,
        writes: tuple[TransactionWrite, ...],
        outbox_events: tuple[OutboxEventWrite, ...] = (),
        allow_operation_rows: bool,
        now: datetime | None = None,
    ) -> TransactionCommitResult:
        if not writes:
            raise AcidCasConflictError("ACID/CAS transactions must include at least one write.")

        fingerprint = _transaction_fingerprint(
            request_id=request_id,
            request_checksum=request_checksum,
            writes=writes,
            outbox_events=outbox_events,
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

            commit_time = self._trusted_now()
            pending_records = self._validate_and_stage(
                transaction_id=transaction_id,
                request_id=request_id,
                request_checksum=request_checksum,
                writes=writes,
                allow_operation_rows=allow_operation_rows,
                now=commit_time,
            )
            pending_outbox_events = self._validate_and_stage_outbox_events(
                outbox_events=outbox_events,
                staged_records=pending_records,
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
                outbox_events=tuple(
                    OutboxRecord(
                        event_id=event.event_id,
                        event_type=event.event_type,
                        resource_id=event.resource_id,
                        resource_version=event.resource_version,
                        operation_id=event.operation_id,
                        payload_hash=event.payload_hash,
                        payload=deepcopy(event.payload),
                        state=event.state,
                        attempt_count=event.attempt_count,
                        next_attempt_at=event.next_attempt_at,
                        locked_by=event.locked_by,
                        locked_until=event.locked_until,
                        lock_token=event.lock_token,
                        last_error=event.last_error,
                        created_at=committed_at,
                        updated_at=committed_at,
                    )
                    for event in pending_outbox_events
                ),
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
            for event in stored_result.outbox_events:
                self._outbox[outbox_key_from_record(event)] = event
            self._transactions[transaction_id] = stored_result
            self._transaction_fingerprints[transaction_id] = fingerprint
            return clone_result(stored_result)

    def get_outbox_event(
        self,
        *,
        event_id: str,
        resource_id: str | None = None,
        event_type: str | None = None,
        resource_version: int | None = None,
    ) -> OutboxRecord:
        with self._lock:
            return clone_outbox_record(
                self._outbox[
                    self._resolve_outbox_key(
                        event_id=event_id,
                        resource_id=resource_id,
                        event_type=event_type,
                        resource_version=resource_version,
                    )
                ]
            )

    def acquire_outbox_event(
        self,
        *,
        event_id: str,
        dispatcher_id: str,
        lock_token: str,
        lock_ttl_ms: int,
        resource_id: str | None = None,
        event_type: str | None = None,
        resource_version: int | None = None,
    ) -> OutboxRecord:
        validate_outbox_identity(dispatcher_id=dispatcher_id, lock_token=lock_token)
        if lock_ttl_ms <= 0:
            raise AcidCasConflictError("Outbox lock TTL must be a positive millisecond value.")
        with self._lock:
            effective_now = self._trusted_now()
            key = self._resolve_outbox_key(
                event_id=event_id,
                resource_id=resource_id,
                event_type=event_type,
                resource_version=resource_version,
            )
            current = self._outbox[key]
            if current.state in ("SUCCEEDED", "FAILED"):
                raise AcidCasConflictError(f"Outbox event {event_id} is already {current.state}.")
            if current.state == "DELIVERING" and not _outbox_lock_is_expired(current, effective_now):
                raise AcidCasConflictError(
                    f"Outbox event {event_id} is already delivering under lock token {current.lock_token}."
                )
            updated = replace_outbox_record(
                current,
                state="DELIVERING",
                attempt_count=current.attempt_count + 1,
                locked_by=dispatcher_id,
                locked_until=_isoformat(effective_now + timedelta(milliseconds=lock_ttl_ms)),
                lock_token=lock_token,
                updated_at=_isoformat(effective_now),
            )
            self._outbox[key] = updated
            return clone_outbox_record(updated)

    def retry_outbox_event(
        self,
        *,
        event_id: str,
        dispatcher_id: str,
        lock_token: str,
        last_error: str,
        resource_id: str | None = None,
        event_type: str | None = None,
        resource_version: int | None = None,
    ) -> OutboxRecord:
        with self._lock:
            effective_now = self._trusted_now()
            key, current = self._locked_outbox_event(
                event_id=event_id,
                dispatcher_id=dispatcher_id,
                lock_token=lock_token,
                resource_id=resource_id,
                event_type=event_type,
                resource_version=resource_version,
                now=effective_now,
            )
            updated = replace_outbox_record(
                current,
                state="PENDING",
                next_attempt_at=_isoformat(effective_now),
                locked_by=None,
                locked_until=None,
                lock_token=None,
                last_error=last_error,
                updated_at=_isoformat(effective_now),
            )
            self._outbox[key] = updated
            return clone_outbox_record(updated)

    def complete_outbox_event(
        self,
        *,
        event_id: str,
        dispatcher_id: str,
        lock_token: str,
        resource_id: str | None = None,
        event_type: str | None = None,
        resource_version: int | None = None,
    ) -> OutboxRecord:
        with self._lock:
            effective_now = self._trusted_now()
            key, current = self._locked_outbox_event(
                event_id=event_id,
                dispatcher_id=dispatcher_id,
                lock_token=lock_token,
                resource_id=resource_id,
                event_type=event_type,
                resource_version=resource_version,
                now=effective_now,
            )
            updated = replace_outbox_record(
                current,
                state="SUCCEEDED",
                locked_by=None,
                locked_until=None,
                lock_token=None,
                updated_at=_isoformat(effective_now),
            )
            self._outbox[key] = updated
            return clone_outbox_record(updated)

    def record_outbox_consumer_delivery(
        self,
        *,
        event_id: str,
        consumer_name: str,
        dispatcher_id: str,
        lock_token: str,
        resource_id: str | None = None,
        event_type: str | None = None,
        resource_version: int | None = None,
    ) -> ConsumerDeliveryRecord:
        if not _is_valid_identifier(consumer_name):
            raise AcidCasConflictError("Outbox consumer_name must be non-empty.")
        with self._lock:
            effective_now = self._trusted_now()
            _, event = self._locked_outbox_event(
                event_id=event_id,
                dispatcher_id=dispatcher_id,
                lock_token=lock_token,
                resource_id=resource_id,
                event_type=event_type,
                resource_version=resource_version,
                now=effective_now,
            )
            delivery_key = (
                event.event_type,
                event.resource_id,
                event.event_id,
                consumer_name,
                event.resource_version,
            )
            existing = self._consumer_deliveries.get(delivery_key)
            if existing is not None:
                return clone_consumer_delivery(existing)
            delivery = ConsumerDeliveryRecord(
                event_id=event.event_id,
                event_type=event.event_type,
                resource_id=event.resource_id,
                resource_version=event.resource_version,
                consumer_name=consumer_name,
                delivered_at=_isoformat(effective_now),
            )
            self._consumer_deliveries[delivery_key] = delivery
            return clone_consumer_delivery(delivery)

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

        with self._lock:
            effective_now = self._trusted_now()
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
        with self._lock:
            effective_now = self._trusted_now()
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
        with self._lock:
            effective_now = self._trusted_now()
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
        with self._lock:
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
        allow_operation_rows: bool,
        now: datetime,
    ) -> tuple[StoredRecord, ...]:
        seen_keys: set[EntityKey] = set()
        staged: list[StoredRecord] = []
        for write in writes:
            if write.entity_type == "operation" and not allow_operation_rows:
                raise AcidCasConflictError("Operation rows must be written through the operation API.")
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

    def _validate_and_stage_outbox_events(
        self,
        *,
        outbox_events: tuple[OutboxEventWrite, ...],
        staged_records: tuple[StoredRecord, ...],
        now: datetime,
    ) -> tuple[OutboxRecord, ...]:
        seen_keys: set[OutboxKey] = set()
        staged_by_resource = {
            lease_resource_id_for_record(record): record
            for record in staged_records
        }
        events: list[OutboxRecord] = []
        for event in outbox_events:
            validate_outbox_event_write(event)
            key = outbox_key_from_write(event)
            if key in seen_keys or key in self._outbox:
                raise AcidCasConflictError(
                    f"Transaction references outbox event {event.event_type}:{event.resource_id}:{event.event_id}:{event.resource_version} more than once."
                )
            seen_keys.add(key)
            bound_record = staged_by_resource.get(event.resource_id)
            if bound_record is None:
                bound_record = self._record_for_resource_id(event.resource_id)
            if bound_record.version != event.resource_version:
                raise AcidCasConflictError(
                    f"Outbox event {event.event_id} resource version {event.resource_version} "
                    f"does not match durable resource version {bound_record.version}."
                )
            if bound_record.payload != event.payload:
                raise AcidCasConflictError(
                    f"Outbox event {event.event_id} payload must match the bound durable resource payload."
                )
            timestamp = _isoformat(now)
            events.append(
                OutboxRecord(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    resource_id=event.resource_id,
                    resource_version=event.resource_version,
                    operation_id=event.operation_id,
                    payload_hash=event.payload_hash,
                    payload=deepcopy(event.payload),
                    state="PENDING",
                    attempt_count=0,
                    next_attempt_at=timestamp,
                    locked_by=None,
                    locked_until=None,
                    lock_token=None,
                    last_error=None,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        return tuple(events)

    def _record_for_resource_id(self, resource_id: str) -> StoredRecord:
        entity_type, tenant_id, owner_id, project_id, entity_id = resource_id.split(":", maxsplit=4)
        key = entity_key(
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            owner_id=owner_id,
            project_id=project_id,
        )
        try:
            return self._records[key]
        except KeyError as exc:
            raise AcidCasConflictError(f"Outbox event resource {resource_id} does not match a durable row.") from exc

    def _resolve_outbox_key(
        self,
        *,
        event_id: str,
        resource_id: str | None,
        event_type: str | None,
        resource_version: int | None,
    ) -> OutboxKey:
        if resource_id is not None and event_type is not None and resource_version is not None:
            key = (event_type, resource_id, event_id, resource_version)
            if key not in self._outbox:
                raise KeyError(f"No outbox event for {event_id}")
            return key
        matches = [
            key
            for key in self._outbox
            if key[2] == event_id
            and (resource_id is None or key[1] == resource_id)
            and (event_type is None or key[0] == event_type)
            and (resource_version is None or key[3] == resource_version)
        ]
        if len(matches) != 1:
            raise KeyError(f"No unique outbox event for {event_id}")
        return matches[0]

    def _locked_outbox_event(
        self,
        *,
        event_id: str,
        dispatcher_id: str,
        lock_token: str,
        resource_id: str | None,
        event_type: str | None,
        resource_version: int | None,
        now: datetime,
    ) -> tuple[OutboxKey, OutboxRecord]:
        validate_outbox_identity(dispatcher_id=dispatcher_id, lock_token=lock_token)
        key = self._resolve_outbox_key(
            event_id=event_id,
            resource_id=resource_id,
            event_type=event_type,
            resource_version=resource_version,
        )
        current = self._outbox[key]
        if current.state != "DELIVERING":
            raise AcidCasStaleWriteError(f"Outbox event {event_id} is not actively delivering.")
        if _outbox_lock_is_expired(current, now):
            raise AcidCasStaleWriteError(f"Outbox event {event_id} lock token is expired.")
        if current.locked_by != dispatcher_id:
            raise AcidCasStaleWriteError(
                f"Outbox event {event_id} expected dispatcher {dispatcher_id} but durable dispatcher is {current.locked_by}."
            )
        if current.lock_token != lock_token:
            raise AcidCasStaleWriteError(
                f"Outbox event {event_id} expected lock token {lock_token} but durable lock token is {current.lock_token}."
            )
        return key, current

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
        result = self._commit(
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
            allow_operation_rows=True,
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

    def _assert_operation_active_lease(
        self,
        *,
        operation_id: str,
        scope: OperationScope,
        lease_owner_id: str,
        lease_epoch: int,
        now: datetime,
    ) -> None:
        if scope.resource_id not in self._lease_epochs:
            return
        current = self._leases.get(scope.resource_id)
        if current is None or _lease_is_expired(current, now):
            raise AcidCasStaleOwnerError(
                f"Operation {operation_id} lease {scope.resource_id} is expired."
            )
        if current.lease_epoch != lease_epoch:
            raise AcidCasStaleOwnerError(
                f"Operation {operation_id} expected lease epoch {lease_epoch} "
                f"but durable lease epoch is {current.lease_epoch}."
            )
        if current.lease_id != lease_owner_id:
            raise AcidCasStaleOwnerError(
                f"Operation {operation_id} expected lease owner {lease_owner_id} "
                f"but durable owner is {current.lease_id}."
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
        if write.entity_type == "operation":
            return
        validate_write_resource_identity(write)
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
        outbox_events=replayed.outbox_events,
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
        outbox_events=tuple(clone_outbox_record(event) for event in result.outbox_events),
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


def clone_outbox_record(record: OutboxRecord) -> OutboxRecord:
    return OutboxRecord(
        event_id=record.event_id,
        event_type=record.event_type,
        resource_id=record.resource_id,
        resource_version=record.resource_version,
        operation_id=record.operation_id,
        payload_hash=record.payload_hash,
        payload=deepcopy(record.payload),
        state=record.state,
        attempt_count=record.attempt_count,
        next_attempt_at=record.next_attempt_at,
        locked_by=record.locked_by,
        locked_until=record.locked_until,
        lock_token=record.lock_token,
        last_error=record.last_error,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def clone_consumer_delivery(record: ConsumerDeliveryRecord) -> ConsumerDeliveryRecord:
    return ConsumerDeliveryRecord(
        event_id=record.event_id,
        event_type=record.event_type,
        resource_id=record.resource_id,
        resource_version=record.resource_version,
        consumer_name=record.consumer_name,
        delivered_at=record.delivered_at,
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


def operation_entity_id(*, operation_id: str, scope: OperationScope) -> str:
    return f"{operation_id}::{scope.resource_id}"


def validate_operation_scope(scope: OperationScope) -> None:
    parts = scope.resource_id.split(":")
    if len(parts) != 5 or any(not _is_valid_identity_part(part) for part in parts):
        raise AcidCasConflictError(
            "Operation scope resource_id must use canonical non-empty colon-free entity_type:tenant_id:owner_id:project_id:entity_id identity."
        )
    _, tenant_id, owner_id, project_id, _ = parts
    if any(not _is_valid_identity_part(part) for part in (scope.tenant_id, scope.owner_id, scope.project_id)):
        raise AcidCasConflictError("OperationScope tenant_id, owner_id, and project_id must be non-empty and colon-free.")
    if (tenant_id, owner_id, project_id) != (scope.tenant_id, scope.owner_id, scope.project_id):
        raise AcidCasConflictError(
            "Operation scope resource_id tenant_id, owner_id, and project_id must match OperationScope."
        )


def validate_operation_identity(*, operation_id: str, payload_hash: str, lease_owner_id: str) -> None:
    for label, value in (
        ("operation_id", operation_id),
        ("payload_hash", payload_hash),
        ("lease_owner_id", lease_owner_id),
    ):
        if not _is_valid_identifier(value):
            raise AcidCasConflictError(f"Operation {label} must be non-empty.")


def _is_valid_identity_part(value: str) -> bool:
    return bool(value.strip()) and value == value.strip() and ":" not in value


def _is_valid_identifier(value: str) -> bool:
    return bool(value.strip()) and value == value.strip()


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


def lease_resource_id_for_write(write: TransactionWrite) -> str:
    return f"{write.entity_type}:{write.tenant_id}:{write.owner_id}:{write.project_id}:{write.entity_id}"


def lease_resource_id_for_record(record: StoredRecord) -> str:
    return f"{record.entity_type}:{record.tenant_id}:{record.owner_id}:{record.project_id}:{record.entity_id}"


def validate_write_resource_identity(write: TransactionWrite) -> None:
    validate_canonical_resource_id(lease_resource_id_for_write(write))


def validate_canonical_resource_id(resource_id: str) -> None:
    parts = resource_id.split(":")
    if len(parts) != 5 or any(not part.strip() or part != part.strip() for part in parts):
        raise AcidCasConflictError(
            "Lease resource_id must use canonical entity_type:tenant_id:owner_id:project_id:entity_id identity."
        )


def validate_lease_id(lease_id: str) -> None:
    if not lease_id.strip() or lease_id != lease_id.strip():
        raise AcidCasConflictError("Lease lease_id must be non-empty.")


def validate_outbox_event_write(event: OutboxEventWrite) -> None:
    validate_canonical_resource_id(event.resource_id)
    for label, value in (
        ("event_id", event.event_id),
        ("event_type", event.event_type),
        ("operation_id", event.operation_id),
        ("payload_hash", event.payload_hash),
    ):
        if not _is_valid_identifier(value):
            raise AcidCasConflictError(f"Outbox {label} must be non-empty.")
    if event.resource_version <= 0:
        raise AcidCasConflictError("Outbox resource_version must be positive.")


def validate_outbox_identity(*, dispatcher_id: str, lock_token: str) -> None:
    for label, value in (("dispatcher_id", dispatcher_id), ("lock_token", lock_token)):
        if not _is_valid_identifier(value):
            raise AcidCasConflictError(f"Outbox {label} must be non-empty.")


def outbox_key_from_write(event: OutboxEventWrite) -> OutboxKey:
    return (event.event_type, event.resource_id, event.event_id, event.resource_version)


def outbox_key_from_record(event: OutboxRecord) -> OutboxKey:
    return (event.event_type, event.resource_id, event.event_id, event.resource_version)


def replace_outbox_record(
    record: OutboxRecord,
    *,
    state: OutboxState,
    attempt_count: int | None = None,
    next_attempt_at: str | None = None,
    locked_by: str | None = None,
    locked_until: str | None = None,
    lock_token: str | None = None,
    last_error: str | None = None,
    updated_at: str,
) -> OutboxRecord:
    return OutboxRecord(
        event_id=record.event_id,
        event_type=record.event_type,
        resource_id=record.resource_id,
        resource_version=record.resource_version,
        operation_id=record.operation_id,
        payload_hash=record.payload_hash,
        payload=deepcopy(record.payload),
        state=state,
        attempt_count=record.attempt_count if attempt_count is None else attempt_count,
        next_attempt_at=next_attempt_at,
        locked_by=locked_by,
        locked_until=locked_until,
        lock_token=lock_token,
        last_error=record.last_error if last_error is None else last_error,
        created_at=record.created_at,
        updated_at=updated_at,
    )


def _transaction_fingerprint(
    *,
    request_id: str,
    request_checksum: str,
    writes: tuple[TransactionWrite, ...],
    outbox_events: tuple[OutboxEventWrite, ...],
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
        "outboxEvents": [
            {
                "eventId": event.event_id,
                "eventType": event.event_type,
                "resourceId": event.resource_id,
                "resourceVersion": event.resource_version,
                "operationId": event.operation_id,
                "payloadHash": event.payload_hash,
                "payload": event.payload,
            }
            for event in outbox_events
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


def _outbox_lock_is_expired(record: OutboxRecord, now: datetime) -> bool:
    if record.locked_until is None:
        return True
    return now >= datetime.fromisoformat(record.locked_until).astimezone(UTC)
