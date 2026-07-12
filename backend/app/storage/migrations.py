"""Versioned migration ledger helpers for Phase 1 Closure CH-01."""

from __future__ import annotations

import json
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .file_state import write_state
from .ops_metrics import counter_metric

MIGRATION_STATE_SCHEMA = "storage-migration-state-v1"
MigrationPhase = Literal["expand", "contract"]


class MigrationError(Exception):
    """Base class for migration baseline failures."""


class MigrationRegistryError(MigrationError):
    """Raised when the declared migration registry is invalid."""


class MigrationStateError(MigrationError):
    """Raised when persisted migration state is missing or malformed."""


class UnsafeRollbackError(MigrationError):
    """Raised when previous-code rollback compatibility cannot be proven."""


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


@dataclass(frozen=True, slots=True)
class RollbackSchemaState:
    schema_version: int
    compatibility_window_floor: int
    compatibility_window_ceiling: int
    applied_revision_ids: tuple[str, ...]
    compatibility_proof_reference: str
    proof_revision_id: str
    payload: dict[str, Any]
    down_migration_revision: str | None = None


@dataclass(frozen=True, slots=True)
class PayloadFieldRequirement:
    field_name: str
    expected_type: Literal["str", "int", "bool", "dict"]
    allow_empty: bool = False


@dataclass(frozen=True, slots=True)
class PreviousCodeCompatibility:
    code_version: int
    min_supported_schema_version: int
    max_supported_schema_version: int
    required_payload_fields: tuple[PayloadFieldRequirement, ...] = ()
    blocked_payload_fields: tuple[str, ...] = ()
    required_compatibility_proof_reference: str = ""
    required_proof_revision_id: str = ""


@dataclass(frozen=True, slots=True)
class ForwardRepairField:
    target_field: str
    source_field: str | None = None
    default_value: Any = None
    overwrite_existing: bool = False


@dataclass(frozen=True, slots=True)
class ForwardRepairPlan:
    repair_id: str
    repair_revision_id: str
    restores_code_version: int
    updated_compatibility_proof_reference: str
    field_repairs: tuple[ForwardRepairField, ...] = ()


@dataclass(frozen=True, slots=True)
class TrustedRollbackProof:
    applied_revision_ids: tuple[str, ...]
    compatibility_proof_reference: str
    proof_revision_id: str
    payload_fingerprint: str


@dataclass(frozen=True, slots=True)
class TrustedRollbackProofLedger:
    proofs: tuple[TrustedRollbackProof, ...]

    def resolve(
        self,
        *,
        compatibility_proof_reference: str,
        proof_revision_id: str,
    ) -> TrustedRollbackProof:
        matches = tuple(
            proof
            for proof in self.proofs
            if proof.compatibility_proof_reference == compatibility_proof_reference
            and proof.proof_revision_id == proof_revision_id
        )
        if not matches:
            raise UnsafeRollbackError(
                "Rollback blocked until forward repair completes: reviewed rollback proof source is missing "
                f"entry {compatibility_proof_reference} at revision {proof_revision_id}"
            )
        if len(matches) > 1:
            raise UnsafeRollbackError(
                "Rollback blocked until forward repair completes: reviewed rollback proof source has duplicate "
                f"entries for {compatibility_proof_reference} at revision {proof_revision_id}"
            )
        proof = matches[0]
        _validate_trusted_rollback_proof(proof)
        return proof


@dataclass(frozen=True, slots=True)
class RollbackCompatibilityResult:
    compatible: bool
    reason: str | None
    down_migration_supported: bool


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
        rollback_compatibility = None
        current_payload = self._load_payload()
        if current_payload is not None:
            candidate = current_payload.get("rollbackCompatibility")
            if candidate is not None:
                candidate_state = _deserialize_rollback_schema_state(candidate)
                applied_revision_ids = tuple(record.revision_id for record in applied)
                if candidate_state.applied_revision_ids == applied_revision_ids:
                    rollback_compatibility = candidate
        payload = {
            "schema": MIGRATION_STATE_SCHEMA,
            "currentRevision": applied[-1].revision_id if applied else None,
            "appliedRevisions": [asdict(record) for record in applied],
        }
        if rollback_compatibility is not None:
            payload["rollbackCompatibility"] = rollback_compatibility
        write_state(self._state_path, payload)

    def load_rollback_compatibility(self) -> RollbackSchemaState | None:
        payload = self._load_payload()
        if payload is None:
            return None
        rollback_payload = payload.get("rollbackCompatibility")
        if rollback_payload is None:
            return None
        state = _deserialize_rollback_schema_state(rollback_payload)
        applied_revision_ids = tuple(record.revision_id for record in self.load_applied())
        if state.applied_revision_ids != applied_revision_ids:
            raise MigrationStateError("Rollback compatibility ledger does not match the persisted applied migration ledger.")
        return state

    def persist_rollback_compatibility(self, state: RollbackSchemaState) -> None:
        _validate_rollback_state(state)
        payload = self._load_payload()
        if payload is None:
            raise MigrationStateError("Migration state must exist before persisting rollback compatibility.")
        applied_records = self.load_applied()
        applied_revision_ids = tuple(record.revision_id for record in applied_records)
        if state.applied_revision_ids != applied_revision_ids:
            raise MigrationStateError("Rollback compatibility ledger must match the persisted applied migration ledger.")
        payload["rollbackCompatibility"] = _serialize_rollback_schema_state(state)
        write_state(self._state_path, payload)

    def assert_persisted_previous_code_rollback_safe(
        self,
        *,
        previous_code: PreviousCodeCompatibility,
        trusted_proof_ledger: TrustedRollbackProofLedger,
    ) -> RollbackCompatibilityResult:
        try:
            state = self.load_rollback_compatibility()
            if state is None:
                raise UnsafeRollbackError(
                    "Rollback blocked until forward repair completes: persisted rollback compatibility is missing"
                )
            trusted_proof = trusted_proof_ledger.resolve(
                compatibility_proof_reference=state.compatibility_proof_reference,
                proof_revision_id=state.proof_revision_id,
            )
            return assert_previous_code_rollback_safe(
                previous_code=previous_code,
                state=state,
                trusted_proof=trusted_proof,
            )
        except UnsafeRollbackError as exc:
            counter_metric("rollback_block_total", reason=_rollback_block_reason(str(exc)))
            raise

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


def assert_previous_code_rollback_safe(
    *,
    previous_code: PreviousCodeCompatibility,
    state: RollbackSchemaState,
    trusted_proof: TrustedRollbackProof,
) -> RollbackCompatibilityResult:
    _validate_rollback_state(state)
    _validate_previous_code(previous_code)
    _validate_trusted_rollback_proof(trusted_proof)

    reasons: list[str] = []
    if not (previous_code.min_supported_schema_version <= state.schema_version <= previous_code.max_supported_schema_version):
        reasons.append(
            "schema version "
            f"{state.schema_version} is outside the previous-code support window "
            f"{previous_code.min_supported_schema_version}-{previous_code.max_supported_schema_version}"
        )
    if not (state.compatibility_window_floor <= previous_code.code_version <= state.compatibility_window_ceiling):
        reasons.append(
            "previous code version "
            f"{previous_code.code_version} is outside the expanded-schema compatibility window "
            f"{state.compatibility_window_floor}-{state.compatibility_window_ceiling}"
        )
    if state.compatibility_proof_reference != trusted_proof.compatibility_proof_reference:
        reasons.append("expanded schema compatibility proof reference does not match the trusted rollback proof")
    if state.proof_revision_id != trusted_proof.proof_revision_id:
        reasons.append("expanded schema proof revision does not match the trusted rollback proof revision")
    if state.applied_revision_ids != trusted_proof.applied_revision_ids:
        reasons.append("expanded schema applied revision ledger does not match the trusted rollback proof ledger")
    if _payload_fingerprint(state.payload) != trusted_proof.payload_fingerprint:
        reasons.append("expanded schema payload fingerprint does not match the trusted rollback proof payload")
    if state.compatibility_proof_reference != previous_code.required_compatibility_proof_reference:
        reasons.append("expanded schema compatibility proof reference does not match the required reviewed proof")
    if state.proof_revision_id != previous_code.required_proof_revision_id:
        reasons.append("expanded schema proof revision does not match the required reviewed revision")
    if state.proof_revision_id not in state.applied_revision_ids:
        reasons.append("expanded schema proof revision is not present in the applied migration ledger")

    invalid_fields = sorted(
        requirement.field_name
        for requirement in previous_code.required_payload_fields
        if not _payload_field_satisfies_requirement(state.payload, requirement)
    )
    if invalid_fields:
        reasons.append("expanded schema is missing or invalid for required legacy fields: " + ", ".join(invalid_fields))

    blocked_fields = sorted(
        field_name
        for field_name in previous_code.blocked_payload_fields
        if field_name in state.payload and state.payload[field_name] is not None
    )
    if blocked_fields:
        reasons.append("expanded schema still exposes rollback-blocking fields: " + ", ".join(blocked_fields))

    if reasons:
        raise UnsafeRollbackError("Rollback blocked until forward repair completes: " + "; ".join(reasons))

    return RollbackCompatibilityResult(
        compatible=True,
        reason=None,
        down_migration_supported=False,
    )


def apply_forward_repair(
    *,
    state: RollbackSchemaState,
    repair: ForwardRepairPlan,
    previous_code: PreviousCodeCompatibility,
    trusted_proof: TrustedRollbackProof,
) -> RollbackSchemaState:
    _validate_rollback_state(state)
    _validate_previous_code(previous_code)
    _validate_trusted_rollback_proof(trusted_proof)
    if repair.restores_code_version <= 0:
        raise UnsafeRollbackError("Forward repair must restore a positive code schema version.")
    if repair.restores_code_version != previous_code.code_version:
        raise UnsafeRollbackError("Forward repair must restore exactly the reviewed previous code version.")
    if not repair.repair_revision_id:
        raise UnsafeRollbackError("Forward repair must name the reviewed repair revision id.")
    if repair.repair_revision_id in state.applied_revision_ids:
        raise UnsafeRollbackError("Forward repair must record a new reviewed repair revision id.")
    if not repair.updated_compatibility_proof_reference:
        raise UnsafeRollbackError("Forward repair must name the reviewed compatibility proof reference.")
    if repair.restores_code_version > state.compatibility_window_ceiling:
        raise UnsafeRollbackError(
            "Forward repair must not widen the compatibility ceiling beyond the currently reviewed window."
        )
    if not _is_revision_prefix(state.applied_revision_ids, trusted_proof.applied_revision_ids):
        raise UnsafeRollbackError("Forward repair input lineage must be a prefix of the trusted rollback proof ledger.")
    if repair.repair_revision_id != trusted_proof.proof_revision_id:
        raise UnsafeRollbackError("Forward repair revision id must match the trusted rollback proof revision.")
    if repair.updated_compatibility_proof_reference != trusted_proof.compatibility_proof_reference:
        raise UnsafeRollbackError(
            "Forward repair compatibility proof reference must match the trusted rollback proof reference."
        )
    expected_repaired_ledger = (*state.applied_revision_ids, repair.repair_revision_id)
    if trusted_proof.applied_revision_ids != expected_repaired_ledger:
        raise UnsafeRollbackError(
            "Forward repair trusted rollback proof ledger must equal the current lineage plus the reviewed repair revision."
        )

    payload = dict(state.payload)
    changed = False
    for field_repair in repair.field_repairs:
        if not field_repair.target_field:
            raise UnsafeRollbackError("Forward repair target_field must be non-empty.")
        if field_repair.target_field in payload and not field_repair.overwrite_existing:
            continue
        if field_repair.source_field is not None:
            if field_repair.source_field not in payload:
                raise UnsafeRollbackError(
                    f"Forward repair {repair.repair_id} cannot copy missing source field {field_repair.source_field}."
                )
            new_value = payload[field_repair.source_field]
            if payload.get(field_repair.target_field) != new_value:
                changed = True
            payload[field_repair.target_field] = new_value
            continue
        if payload.get(field_repair.target_field) != field_repair.default_value:
            changed = True
        payload[field_repair.target_field] = field_repair.default_value

    if not changed:
        raise UnsafeRollbackError(
            "Forward repair must make a material compatibility change before widening the rollback window."
        )

    repaired_state = RollbackSchemaState(
        schema_version=state.schema_version,
        compatibility_window_floor=min(state.compatibility_window_floor, repair.restores_code_version),
        compatibility_window_ceiling=state.compatibility_window_ceiling,
        applied_revision_ids=expected_repaired_ledger,
        compatibility_proof_reference=trusted_proof.compatibility_proof_reference,
        proof_revision_id=trusted_proof.proof_revision_id,
        payload=payload,
        down_migration_revision=state.down_migration_revision,
    )
    assert_previous_code_rollback_safe(
        previous_code=previous_code,
        state=repaired_state,
        trusted_proof=trusted_proof,
    )
    return repaired_state


def apply_forward_repair_from_ledger(
    *,
    state: RollbackSchemaState,
    repair: ForwardRepairPlan,
    previous_code: PreviousCodeCompatibility,
    trusted_proof_ledger: TrustedRollbackProofLedger,
) -> RollbackSchemaState:
    trusted_proof = trusted_proof_ledger.resolve(
        compatibility_proof_reference=repair.updated_compatibility_proof_reference,
        proof_revision_id=repair.repair_revision_id,
    )
    return apply_forward_repair(
        state=state,
        repair=repair,
        previous_code=previous_code,
        trusted_proof=trusted_proof,
    )


def _validate_rollback_state(state: RollbackSchemaState) -> None:
    if state.schema_version <= 0:
        raise MigrationStateError("Rollback schema_version must be positive.")
    if state.compatibility_window_floor <= 0 or state.compatibility_window_ceiling <= 0:
        raise MigrationStateError("Rollback compatibility window bounds must be positive.")
    if state.compatibility_window_floor > state.compatibility_window_ceiling:
        raise MigrationStateError("Rollback compatibility window floor must be <= ceiling.")
    if not state.applied_revision_ids:
        raise MigrationStateError("Rollback applied revision ledger must not be empty.")
    if not state.compatibility_proof_reference:
        raise MigrationStateError("Rollback compatibility proof reference must be non-empty.")
    if not state.proof_revision_id:
        raise MigrationStateError("Rollback proof revision id must be non-empty.")
    if state.proof_revision_id not in state.applied_revision_ids:
        raise MigrationStateError("Rollback proof revision id must exist in the applied migration ledger.")
    if not isinstance(state.payload, dict):
        raise MigrationStateError("Rollback payload must be a JSON-like object.")


def _validate_previous_code(previous_code: PreviousCodeCompatibility) -> None:
    if previous_code.code_version <= 0:
        raise UnsafeRollbackError("Previous code version must be positive.")
    if previous_code.min_supported_schema_version <= 0 or previous_code.max_supported_schema_version <= 0:
        raise UnsafeRollbackError("Previous-code schema support window must be positive.")
    if previous_code.min_supported_schema_version > previous_code.max_supported_schema_version:
        raise UnsafeRollbackError("Previous-code schema support floor must be <= ceiling.")
    if not previous_code.required_compatibility_proof_reference:
        raise UnsafeRollbackError("Previous-code compatibility proof reference must be non-empty.")
    if not previous_code.required_proof_revision_id:
        raise UnsafeRollbackError("Previous-code proof revision id must be non-empty.")


def _validate_trusted_rollback_proof(trusted_proof: TrustedRollbackProof) -> None:
    if not trusted_proof.applied_revision_ids:
        raise UnsafeRollbackError("Trusted rollback proof ledger must not be empty.")
    if not trusted_proof.compatibility_proof_reference:
        raise UnsafeRollbackError("Trusted rollback proof reference must be non-empty.")
    if not trusted_proof.proof_revision_id:
        raise UnsafeRollbackError("Trusted rollback proof revision id must be non-empty.")
    if trusted_proof.proof_revision_id not in trusted_proof.applied_revision_ids:
        raise UnsafeRollbackError("Trusted rollback proof revision must exist in the trusted applied ledger.")
    if not trusted_proof.payload_fingerprint:
        raise UnsafeRollbackError("Trusted rollback proof payload fingerprint must be non-empty.")


def _serialize_rollback_schema_state(state: RollbackSchemaState) -> dict[str, Any]:
    return {
        "schemaVersion": state.schema_version,
        "compatibilityWindowFloor": state.compatibility_window_floor,
        "compatibilityWindowCeiling": state.compatibility_window_ceiling,
        "appliedRevisionIds": list(state.applied_revision_ids),
        "compatibilityProofReference": state.compatibility_proof_reference,
        "proofRevisionId": state.proof_revision_id,
        "payload": state.payload,
        "downMigrationRevision": state.down_migration_revision,
    }


def _deserialize_rollback_schema_state(value: object) -> RollbackSchemaState:
    if not isinstance(value, dict):
        raise MigrationStateError("Rollback compatibility payload must be a JSON object.")
    applied_revision_ids = value.get("appliedRevisionIds")
    if not isinstance(applied_revision_ids, list) or not all(isinstance(item, str) for item in applied_revision_ids):
        raise MigrationStateError("Rollback compatibility appliedRevisionIds must be a list of strings.")
    payload = value.get("payload")
    if not isinstance(payload, dict):
        raise MigrationStateError("Rollback compatibility payload field must be a JSON object.")
    down_migration_revision = value.get("downMigrationRevision")
    if down_migration_revision is not None and not isinstance(down_migration_revision, str):
        raise MigrationStateError("Rollback compatibility downMigrationRevision must be a string or null.")
    try:
        state = RollbackSchemaState(
            schema_version=_coerce_int_field(value, "schemaVersion"),
            compatibility_window_floor=_coerce_int_field(value, "compatibilityWindowFloor"),
            compatibility_window_ceiling=_coerce_int_field(value, "compatibilityWindowCeiling"),
            applied_revision_ids=tuple(applied_revision_ids),
            compatibility_proof_reference=_coerce_string_field(value, "compatibilityProofReference"),
            proof_revision_id=_coerce_string_field(value, "proofRevisionId"),
            payload=payload,
            down_migration_revision=down_migration_revision,
        )
    except KeyError as exc:
        raise MigrationStateError(f"Rollback compatibility payload missing key: {exc.args[0]}") from exc
    _validate_rollback_state(state)
    return state


def _coerce_int_field(value: dict[str, Any], key: str) -> int:
    raw = value[key]
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise MigrationStateError(f"Rollback compatibility {key} must be an integer.")
    return raw


def _coerce_string_field(value: dict[str, Any], key: str) -> str:
    raw = value[key]
    if not isinstance(raw, str):
        raise MigrationStateError(f"Rollback compatibility {key} must be a string.")
    return raw


def _payload_fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _append_revision(applied_revision_ids: tuple[str, ...], revision_id: str) -> tuple[str, ...]:
    if revision_id in applied_revision_ids:
        return applied_revision_ids
    return (*applied_revision_ids, revision_id)


def _is_revision_prefix(candidate: tuple[str, ...], trusted: tuple[str, ...]) -> bool:
    return len(candidate) <= len(trusted) and trusted[: len(candidate)] == candidate


def _payload_field_satisfies_requirement(
    payload: dict[str, Any],
    requirement: PayloadFieldRequirement,
) -> bool:
    if requirement.field_name not in payload:
        return False
    value = payload[requirement.field_name]
    if not _value_matches_expected_type(value, requirement.expected_type):
        return False
    if value == "" and not requirement.allow_empty:
        return False
    if value == {} and not requirement.allow_empty:
        return False
    return True


def _value_matches_expected_type(value: Any, expected_type: Literal["str", "int", "bool", "dict"]) -> bool:
    if expected_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "bool":
        return isinstance(value, bool)
    if expected_type == "str":
        return isinstance(value, str)
    return isinstance(value, dict)

def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rollback_block_reason(message: str) -> str:
    normalized = message.lower()
    if "persisted rollback compatibility is missing" in normalized:
        return "missing-compatibility"
    if "reviewed rollback proof source is missing entry" in normalized:
        return "missing-proof"
    if "payload fingerprint" in normalized:
        return "payload-fingerprint-mismatch"
    if "compatibility window" in normalized or "schema version" in normalized:
        return "compatibility-window"
    return "blocked"
