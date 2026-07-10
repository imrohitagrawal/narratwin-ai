"""Versioned migration ledger helpers for Phase 1 Closure CH-01."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .file_state import write_state

MIGRATION_STATE_SCHEMA = "storage-migration-state-v1"
MigrationPhase = Literal["expand", "contract"]


class MigrationError(Exception):
    """Base class for migration baseline failures."""


class MigrationRegistryError(MigrationError):
    """Raised when the declared migration registry is invalid."""


class MigrationStateError(MigrationError):
    """Raised when persisted migration state is missing or malformed."""


@dataclass(slots=True)
class MigrationContext:
    state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AppliedMigrationRecord:
    revision_id: str
    down_revision: str | None
    phase: MigrationPhase
    description: str
    applied_at: str


@dataclass(frozen=True, slots=True)
class MigrationRevision:
    revision_id: str
    down_revision: str | None
    phase: MigrationPhase
    description: str
    apply: Any


@dataclass(frozen=True, slots=True)
class MigrationRunResult:
    applied: tuple[AppliedMigrationRecord, ...]
    current_revision: str | None


class MigrationRunner:
    def __init__(
        self,
        *,
        revisions: list[MigrationRevision],
        state_path: Path | None = None,
        allow_contract_migrations: bool = False,
    ) -> None:
        self._revisions = revisions
        self._state_path = state_path
        self._allow_contract_migrations = allow_contract_migrations

    def load_applied(self) -> list[AppliedMigrationRecord]:
        payload = self._load_payload()
        if payload is None:
            return []
        if payload.get("schema") != MIGRATION_STATE_SCHEMA:
            raise MigrationStateError("Migration state schema mismatch.")

        rows = payload.get("appliedRevisions")
        if not isinstance(rows, list):
            raise MigrationStateError("Migration state appliedRevisions must be a list.")

        records: list[AppliedMigrationRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                raise MigrationStateError("Migration state rows must be JSON objects.")
            try:
                record = AppliedMigrationRecord(
                    revision_id=str(row["revision_id"]),
                    down_revision=self._optional_string(row.get("down_revision")),
                    phase=self._coerce_phase(row.get("phase")),
                    description=str(row["description"]),
                    applied_at=str(row["applied_at"]),
                )
            except KeyError as exc:
                raise MigrationStateError(f"Migration state row missing key: {exc.args[0]}") from exc
            records.append(record)

        current_revision = self._optional_string(payload.get("currentRevision"))
        if records:
            if current_revision != records[-1].revision_id:
                raise MigrationStateError("Migration state currentRevision does not match the latest applied revision.")
        elif current_revision is not None:
            raise MigrationStateError("Migration state currentRevision must be null when no revisions are applied.")
        return records

    def run(self, *, context: MigrationContext | None = None) -> MigrationRunResult:
        self._validate_registry()
        applied = self.load_applied()
        self._validate_applied_prefix(applied)

        active_context = context or MigrationContext()
        newly_applied: list[AppliedMigrationRecord] = []
        current_revision = applied[-1].revision_id if applied else None
        applied_ids = {record.revision_id for record in applied}

        for revision in self._revisions:
            if revision.revision_id in applied_ids:
                continue
            if revision.down_revision != current_revision:
                raise MigrationStateError(
                    "Pending migration order no longer matches persisted state; replay must start from the latest applied revision."
                )
            revision.apply(active_context)
            record = AppliedMigrationRecord(
                revision_id=revision.revision_id,
                down_revision=revision.down_revision,
                phase=revision.phase,
                description=revision.description,
                applied_at=_now(),
            )
            applied.append(record)
            newly_applied.append(record)
            applied_ids.add(record.revision_id)
            current_revision = record.revision_id
            self._persist(applied)

        return MigrationRunResult(applied=tuple(newly_applied), current_revision=current_revision)

    def _persist(self, applied: list[AppliedMigrationRecord]) -> None:
        payload = {
            "schema": MIGRATION_STATE_SCHEMA,
            "currentRevision": applied[-1].revision_id if applied else None,
            "appliedRevisions": [asdict(record) for record in applied],
        }
        write_state(self._state_path, payload)

    def _validate_registry(self) -> None:
        seen: set[str] = set()
        previous_revision: str | None = None
        for revision in self._revisions:
            if revision.revision_id in seen:
                raise MigrationRegistryError(f"Duplicate revision id: {revision.revision_id}")
            if revision.phase == "contract" and not self._allow_contract_migrations:
                raise MigrationRegistryError("contract migrations require explicit opt-in")
            if previous_revision is None:
                if revision.down_revision is not None:
                    raise MigrationRegistryError(
                        f"Migration registry must be ordered from the base revision; {revision.revision_id} depends on {revision.down_revision}."
                    )
            elif revision.down_revision != previous_revision:
                raise MigrationRegistryError(
                    f"Migration registry must be ordered by down_revision; {revision.revision_id} depends on {revision.down_revision}, expected {previous_revision}."
                )
            seen.add(revision.revision_id)
            previous_revision = revision.revision_id

    def _validate_applied_prefix(self, applied: list[AppliedMigrationRecord]) -> None:
        if len(applied) > len(self._revisions):
            raise MigrationStateError("Persisted migration state references revisions outside the declared registry.")
        for index, record in enumerate(applied):
            expected = self._revisions[index]
            if expected.revision_id != record.revision_id:
                raise MigrationStateError("Persisted migration state does not match the declared registry order.")
            if expected.down_revision != record.down_revision:
                raise MigrationStateError("Persisted migration state down_revision does not match the declared registry.")
            if expected.phase != record.phase:
                raise MigrationStateError("Persisted migration state phase does not match the declared registry.")
            if expected.description != record.description:
                raise MigrationStateError("Persisted migration state description does not match the declared registry.")

    def _load_payload(self) -> dict[str, Any] | None:
        if self._state_path is None or not self._state_path.exists():
            return None
        try:
            with self._state_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise MigrationStateError(f"Migration state is unreadable: {exc}") from exc
        if not isinstance(payload, dict):
            raise MigrationStateError("Migration state payload must be a JSON object.")
        return payload

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise MigrationStateError("Expected a string or null in persisted migration state.")
        return value

    @staticmethod
    def _coerce_phase(value: object) -> MigrationPhase:
        if value not in ("expand", "contract"):
            raise MigrationStateError("Persisted migration state phase must be expand or contract.")
        return value


def _now() -> str:
    return datetime.now(UTC).isoformat()
