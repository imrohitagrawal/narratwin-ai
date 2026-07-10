"""PostgreSQL-compatible ACID/CAS storage kernel for Phase 1 Closure CH-02."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any, Literal

RecordState = Literal["OPEN", "TERMINAL", "ERROR"]
CommitOutcome = Literal["applied", "replayed"]
OutboxEventState = Literal["PENDING", "DELIVERING", "SUCCEEDED", "FAILED"]
EntityKey = tuple[str, str, str, str, str]
OutboxEventKey = tuple[str, str]
ConsumerDeliveryKey = tuple[str, str, str, str, int]


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
class OutboxEventWrite:
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    resource_version: int
    operation_id: str
    payload_hash: str
    payload: dict[str, Any]


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
class StoredOutboxEvent:
    event_id: str
    event_type: str
    resource_id: str
    entity_type: str
    entity_id: str
    tenant_id: str
    owner_id: str
    project_id: str
    resource_version: int
    operation_id: str
    payload_hash: str
    state: OutboxEventState
    attempt_count: int
    next_attempt_at: str
    locked_by: str | None
    locked_until: str | None
    last_error: str | None
    payload: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ConsumerDeliveryRecord:
    event_id: str
    event_type: str
    resource_id: str
    consumer_name: str
    resource_version: int
    duplicate: bool
    delivery_count: int
    first_recorded_at: str
    recorded_at: str


@dataclass(frozen=True, slots=True)
class TransactionCommitResult:
    transaction_id: str
    request_id: str
    request_checksum: str
    outcome: CommitOutcome
    replayed: bool
    committed_at: str
    records: tuple[StoredRecord, ...]
    outbox_events: tuple[StoredOutboxEvent, ...] = ()


class AcidCasKernel:
    """Atomic compare-and-set storage kernel for durable metadata rows."""

    def __init__(self) -> None:
        self._records: dict[EntityKey, StoredRecord] = {}
        self._outbox_events: dict[OutboxEventKey, StoredOutboxEvent] = {}
        self._transactions: dict[str, TransactionCommitResult] = {}
        self._transaction_fingerprints: dict[str, str] = {}
        self._consumer_deliveries: dict[ConsumerDeliveryKey, ConsumerDeliveryRecord] = {}
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
        outbox_events: tuple[OutboxEventWrite, ...] = (),
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

            pending_records = self._validate_and_stage(
                transaction_id=transaction_id,
                request_id=request_id,
                request_checksum=request_checksum,
                writes=writes,
            )
            pending_outbox_events = self._stage_outbox_events(
                transaction_id=transaction_id,
                outbox_events=outbox_events,
                staged_records=pending_records,
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
            committed_outbox_events = tuple(
                StoredOutboxEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    resource_id=outbox_resource_id_for_write(event),
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    tenant_id=event.tenant_id,
                    owner_id=event.owner_id,
                    project_id=event.project_id,
                    resource_version=event.resource_version,
                    operation_id=event.operation_id,
                    payload_hash=event.payload_hash,
                    state="PENDING",
                    attempt_count=0,
                    next_attempt_at=committed_at,
                    locked_by=None,
                    locked_until=None,
                    last_error=None,
                    payload=deepcopy(event.payload),
                    created_at=committed_at,
                    updated_at=committed_at,
                )
                for event in pending_outbox_events
            )
            stored_result = TransactionCommitResult(
                transaction_id=transaction_id,
                request_id=request_id,
                request_checksum=request_checksum,
                outcome="applied",
                replayed=False,
                committed_at=committed_at,
                records=committed_records,
                outbox_events=committed_outbox_events,
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
            for event in committed_outbox_events:
                self._outbox_events[outbox_event_key_for_record(event)] = event
            self._transactions[transaction_id] = stored_result
            self._transaction_fingerprints[transaction_id] = fingerprint
            return clone_result(stored_result)

    def get_outbox_event(self, *, event_id: str, resource_id: str) -> StoredOutboxEvent:
        try:
            return clone_outbox_event(self._outbox_events[(resource_id, event_id)])
        except KeyError as exc:
            raise KeyError(f"No durable outbox event for {resource_id}:{event_id}") from exc

    def acquire_outbox_events(
        self,
        *,
        dispatcher_id: str,
        now: datetime | None = None,
        lock_ttl_seconds: int,
        limit: int,
    ) -> tuple[StoredOutboxEvent, ...]:
        if limit <= 0:
            return ()
        if lock_ttl_seconds <= 0:
            raise AcidCasConflictError("Outbox lock TTL must be a positive second value.")

        current_time = _coerce_datetime(now)
        current_iso = current_time.isoformat()
        lock_until = (current_time + timedelta(seconds=lock_ttl_seconds)).isoformat()
        with self._lock:
            eligible = sorted(
                (
                    event
                    for event in self._outbox_events.values()
                    if _outbox_event_is_eligible(event=event, now=current_time)
                ),
                key=lambda event: (event.next_attempt_at, event.created_at, event.event_id),
            )
            acquired: list[StoredOutboxEvent] = []
            for event in eligible[:limit]:
                updated = StoredOutboxEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    resource_id=event.resource_id,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    tenant_id=event.tenant_id,
                    owner_id=event.owner_id,
                    project_id=event.project_id,
                    resource_version=event.resource_version,
                    operation_id=event.operation_id,
                    payload_hash=event.payload_hash,
                    state="DELIVERING",
                    attempt_count=event.attempt_count + 1,
                    next_attempt_at=event.next_attempt_at,
                    locked_by=dispatcher_id,
                    locked_until=lock_until,
                    last_error=event.last_error,
                    payload=deepcopy(event.payload),
                    created_at=event.created_at,
                    updated_at=current_iso,
                )
                self._outbox_events[outbox_event_key_for_record(updated)] = updated
                acquired.append(clone_outbox_event(updated))
            return tuple(acquired)

    def retry_outbox_event(
        self,
        *,
        event_id: str,
        resource_id: str,
        dispatcher_id: str,
        next_attempt_at: datetime,
        last_error: str,
        now: datetime | None = None,
    ) -> StoredOutboxEvent:
        return self._transition_outbox_event(
            event_id=event_id,
            resource_id=resource_id,
            dispatcher_id=dispatcher_id,
            state="PENDING",
            next_attempt_at=next_attempt_at.isoformat(),
            last_error=last_error,
            now=now,
        )

    def mark_outbox_event_succeeded(
        self,
        *,
        event_id: str,
        resource_id: str,
        dispatcher_id: str,
        now: datetime | None = None,
    ) -> StoredOutboxEvent:
        return self._transition_outbox_event(
            event_id=event_id,
            resource_id=resource_id,
            dispatcher_id=dispatcher_id,
            state="SUCCEEDED",
            next_attempt_at=None,
            last_error=None,
            now=now,
        )

    def mark_outbox_event_failed(
        self,
        *,
        event_id: str,
        resource_id: str,
        dispatcher_id: str,
        last_error: str,
        now: datetime | None = None,
    ) -> StoredOutboxEvent:
        return self._transition_outbox_event(
            event_id=event_id,
            resource_id=resource_id,
            dispatcher_id=dispatcher_id,
            state="FAILED",
            next_attempt_at=None,
            last_error=last_error,
            now=now,
        )

    def record_consumer_delivery(
        self,
        *,
        event_id: str,
        resource_id: str,
        event_type: str,
        consumer_name: str,
        resource_version: int,
    ) -> ConsumerDeliveryRecord:
        key = (event_type, resource_id, event_id, consumer_name, resource_version)
        recorded_at = _now()
        with self._lock:
            committed_event = self._outbox_events.get((resource_id, event_id))
            if committed_event is None:
                raise AcidCasConflictError(f"No committed outbox event exists for {resource_id}:{event_id}.")
            if (
                committed_event.event_type != event_type
                or committed_event.resource_version != resource_version
                or committed_event.resource_id != resource_id
            ):
                raise AcidCasConflictError(
                    f"Consumer delivery for {resource_id}:{event_id} does not match committed outbox event identity/version."
                )
            existing = self._consumer_deliveries.get(key)
            if existing is None:
                record = ConsumerDeliveryRecord(
                    event_id=event_id,
                    event_type=event_type,
                    resource_id=resource_id,
                    consumer_name=consumer_name,
                    resource_version=resource_version,
                    duplicate=False,
                    delivery_count=1,
                    first_recorded_at=recorded_at,
                    recorded_at=recorded_at,
                )
            else:
                record = ConsumerDeliveryRecord(
                    event_id=event_id,
                    event_type=event_type,
                    resource_id=resource_id,
                    consumer_name=consumer_name,
                    resource_version=resource_version,
                    duplicate=True,
                    delivery_count=existing.delivery_count + 1,
                    first_recorded_at=existing.first_recorded_at,
                    recorded_at=recorded_at,
                )
            self._consumer_deliveries[key] = record
            return clone_consumer_delivery_record(record)

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

    def _stage_outbox_events(
        self,
        *,
        transaction_id: str,
        outbox_events: tuple[OutboxEventWrite, ...],
        staged_records: tuple[StoredRecord, ...],
    ) -> tuple[OutboxEventWrite, ...]:
        if not outbox_events:
            return ()

        staged_record_map = {
            entity_key(
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                tenant_id=record.tenant_id,
                owner_id=record.owner_id,
                project_id=record.project_id,
            ): record
            for record in staged_records
        }
        seen_event_keys: set[OutboxEventKey] = set()
        staged_events: list[OutboxEventWrite] = []
        for event in outbox_events:
            event_key = outbox_event_key_for_write(event)
            if event_key in seen_event_keys:
                raise AcidCasConflictError(
                    f"Transaction {transaction_id} references outbox event {event_key[0]}:{event.event_id} more than once."
                )
            if event_key in self._outbox_events:
                raise AcidCasConflictError(
                    f"Outbox event {event_key[0]}:{event.event_id} is already committed."
                )
            seen_event_keys.add(event_key)
            record_key = entity_key(
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                tenant_id=event.tenant_id,
                owner_id=event.owner_id,
                project_id=event.project_id,
            )
            try:
                staged_record = staged_record_map[record_key]
            except KeyError as exc:
                raise AcidCasConflictError(
                    f"Outbox event {event.event_id} must reference a durable state row written in the same transaction."
                ) from exc
            if event.resource_version != staged_record.version:
                raise AcidCasConflictError(
                    f"Outbox event {event.event_id} resource version {event.resource_version} does not match durable version {staged_record.version}."
                )
            staged_events.append(
                OutboxEventWrite(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    entity_type=event.entity_type,
                    entity_id=event.entity_id,
                    tenant_id=event.tenant_id,
                    owner_id=event.owner_id,
                    project_id=event.project_id,
                    resource_version=event.resource_version,
                    operation_id=event.operation_id,
                    payload_hash=event.payload_hash,
                    payload=deepcopy(event.payload),
                )
            )
        return tuple(staged_events)

    def _transition_outbox_event(
        self,
        *,
        event_id: str,
        resource_id: str,
        dispatcher_id: str,
        state: OutboxEventState,
        next_attempt_at: str | None,
        last_error: str | None,
        now: datetime | None = None,
    ) -> StoredOutboxEvent:
        with self._lock:
            try:
                existing = self._outbox_events[(resource_id, event_id)]
            except KeyError as exc:
                raise KeyError(f"No durable outbox event for {resource_id}:{event_id}") from exc
            if existing.state != "DELIVERING" or existing.locked_by != dispatcher_id:
                raise AcidCasConflictError(
                    f"Dispatcher {dispatcher_id} does not own outbox event {resource_id}:{event_id}."
                )
            current_time = _coerce_datetime(now)
            if existing.locked_until is None or _parse_timestamp(existing.locked_until) <= current_time:
                raise AcidCasConflictError(
                    f"Dispatcher {dispatcher_id} lock for outbox event {resource_id}:{event_id} has expired."
                )
            updated_at = _now()
            updated = StoredOutboxEvent(
                event_id=existing.event_id,
                event_type=existing.event_type,
                resource_id=existing.resource_id,
                entity_type=existing.entity_type,
                entity_id=existing.entity_id,
                tenant_id=existing.tenant_id,
                owner_id=existing.owner_id,
                project_id=existing.project_id,
                resource_version=existing.resource_version,
                operation_id=existing.operation_id,
                payload_hash=existing.payload_hash,
                state=state,
                attempt_count=existing.attempt_count,
                next_attempt_at=existing.next_attempt_at if next_attempt_at is None else next_attempt_at,
                locked_by=None,
                locked_until=None,
                last_error=last_error,
                payload=deepcopy(existing.payload),
                created_at=existing.created_at,
                updated_at=updated_at,
            )
            self._outbox_events[(resource_id, event_id)] = updated
            return clone_outbox_event(updated)


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
        outbox_events=tuple(clone_outbox_event(event) for event in result.outbox_events),
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


def clone_outbox_event(event: StoredOutboxEvent) -> StoredOutboxEvent:
    return StoredOutboxEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        resource_id=event.resource_id,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        tenant_id=event.tenant_id,
        owner_id=event.owner_id,
        project_id=event.project_id,
        resource_version=event.resource_version,
        operation_id=event.operation_id,
        payload_hash=event.payload_hash,
        state=event.state,
        attempt_count=event.attempt_count,
        next_attempt_at=event.next_attempt_at,
        locked_by=event.locked_by,
        locked_until=event.locked_until,
        last_error=event.last_error,
        payload=deepcopy(event.payload),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def clone_consumer_delivery_record(record: ConsumerDeliveryRecord) -> ConsumerDeliveryRecord:
    return ConsumerDeliveryRecord(
        event_id=record.event_id,
        event_type=record.event_type,
        resource_id=record.resource_id,
        consumer_name=record.consumer_name,
        resource_version=record.resource_version,
        duplicate=record.duplicate,
        delivery_count=record.delivery_count,
        first_recorded_at=record.first_recorded_at,
        recorded_at=record.recorded_at,
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


def outbox_resource_id_for_write(event: OutboxEventWrite) -> str:
    return f"{event.entity_type}:{event.tenant_id}:{event.owner_id}:{event.project_id}:{event.entity_id}"


def outbox_event_key_for_write(event: OutboxEventWrite) -> OutboxEventKey:
    return (outbox_resource_id_for_write(event), event.event_id)


def outbox_event_key_for_record(event: StoredOutboxEvent) -> OutboxEventKey:
    return (event.resource_id, event.event_id)


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
            }
            for write in writes
        ],
        "outboxEvents": [
            {
                "eventId": event.event_id,
                "eventType": event.event_type,
                "resourceId": outbox_resource_id_for_write(event),
                "entityType": event.entity_type,
                "entityId": event.entity_id,
                "tenantId": event.tenant_id,
                "ownerId": event.owner_id,
                "projectId": event.project_id,
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
    return datetime.now(UTC).isoformat()


def _coerce_datetime(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _outbox_event_is_eligible(*, event: StoredOutboxEvent, now: datetime) -> bool:
    if event.state == "PENDING":
        return _parse_timestamp(event.next_attempt_at) <= now
    if event.state == "DELIVERING" and event.locked_until is not None:
        return _parse_timestamp(event.locked_until) <= now
    return False
