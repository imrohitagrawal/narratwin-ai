"""Shared validation for persisted Stage 6/7 evaluation lineage."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable, Mapping, cast

from backend.app.evaluation_lineage import (
    build_source_evaluation_checksum,
    derive_evaluation_lineage,
    validate_evaluation_lineage_payload,
)
from backend.app.stage4 import WalkthroughRunRecord


@dataclass(frozen=True)
class PersistedLineage:
    component: str
    source_run_id: str
    payload: Mapping[str, object]
    digest: str
    row_id: str = ""
    upstream_row_id: str | None = None
    connected_values: Mapping[str, object] | None = None


@dataclass(frozen=True)
class LineageActivation:
    payload: dict[str, Any]
    digest: str
    rows: tuple[PersistedLineage, ...]


STAGE7_CONSENT_DISCLOSURE_VERSION = "stage7-synthetic-avatar-consent-v1"


def validate_lineage_binding(
    payload: Mapping[str, object] | None,
    checksum: str,
    **expected: object,
) -> dict[str, Any]:
    if payload is None:
        raise ValueError("Canonical v2 evaluation lineage is required.")
    canonical = validate_evaluation_lineage_payload(payload)
    identity, scope = canonical["evaluation"], canonical["scope"]
    actual = {
        "evaluation_id": identity["evaluationId"],
        "run_id": identity["runId"],
        "trace_id": identity["traceId"],
        "status": identity["status"],
        "tenant_id": scope["tenantId"],
        "project_id": scope["projectId"],
        "context_ref_ids": tuple(row["contextRefId"] for row in canonical["selectedContext"]),
        "citation_indexes": tuple(canonical["sourceCitationIndexes"]),
    }
    if actual != expected or build_source_evaluation_checksum(canonical) != checksum:
        raise ValueError("Request mismatch.")
    return canonical


def validate_connected_lineages(
    expected_payload: Mapping[str, object],
    expected_digest: str,
    rows: Iterable[PersistedLineage],
) -> LineageActivation:
    canonical = validate_evaluation_lineage_payload(expected_payload)
    if build_source_evaluation_checksum(canonical) != expected_digest:
        raise ValueError("Stage 4 lineage digest is invalid.")
    source_run_id = str(canonical["evaluation"]["runId"])
    connected = tuple(rows)
    for row in connected:
        if row.source_run_id != source_run_id:
            raise ValueError(f"{row.component} source run is mismatched.")
        candidate = validate_evaluation_lineage_payload(row.payload)
        if candidate != canonical or row.digest != expected_digest:
            raise ValueError(f"{row.component} lineage is mismatched.")
    return LineageActivation(payload=canonical, digest=expected_digest, rows=connected)


def validate_rows_against_stage4(
    walkthrough_runs: Mapping[str, WalkthroughRunRecord],
    rows: Iterable[PersistedLineage],
) -> tuple[LineageActivation, ...]:
    grouped: dict[str, list[PersistedLineage]] = {}
    for row in rows:
        grouped.setdefault(row.source_run_id, []).append(row)
    activations: list[LineageActivation] = []
    for source_run_id, connected in grouped.items():
        source_run = walkthrough_runs[source_run_id]
        payload = derive_evaluation_lineage(source_run)
        digest = build_source_evaluation_checksum(payload)
        activations.append(validate_connected_lineages(payload, digest, connected))
    return tuple(activations)


def validate_cross_store_lineages(
    walkthrough_runs: Mapping[str, WalkthroughRunRecord],
    rows: Iterable[PersistedLineage],
) -> tuple[LineageActivation, ...]:
    connected = tuple(rows)
    activations = validate_rows_against_stage4(walkthrough_runs, connected)
    validate_upstream_connections(connected)
    return activations


def validate_upstream_connections(rows: Iterable[PersistedLineage]) -> None:
    connected = tuple(rows)
    upstream = {row.row_id: row for row in connected if row.row_id and row.upstream_row_id is None}
    for row in connected:
        if row.upstream_row_id is None:
            continue
        source = upstream.get(row.upstream_row_id)
        if (source is None or source.source_run_id != row.source_run_id
                or source.connected_values != row.connected_values):
            raise ValueError(f"{row.component} upstream Stage 6 bundle is mismatched.")


def quarantine_reason_for_schema(
    schema: object,
    *,
    current: str,
    legacy: frozenset[str],
    stage: str,
) -> str | None:
    if schema == current:
        return None
    if schema in legacy:
        return f"legacy {stage} state"
    raise ValueError(f"{stage} state schema mismatch.")


def refuse_quarantined_write(reason: str | None) -> None:
    if reason is not None:
        raise OSError(f"Refusing to overwrite quarantined {reason}.")


def restored_state_matches(
    original: Mapping[str, object],
    active: Mapping[str, object],
    *,
    transient_collections: tuple[str, ...] = (),
    derived_keys: tuple[str, ...] = (),
    optional_empty_collections: tuple[str, ...] = (),
) -> bool:
    """Compare parsed JSON with a serializer result without tuple/list false mismatches."""
    candidate = cast(dict[str, Any], json.loads(json.dumps(original)))
    normalized = cast(
        dict[str, Any],
        json.loads(json.dumps(active, sort_keys=True, separators=(",", ":"))),
    )
    for key in transient_collections:
        rows = candidate.get(key, [])
        if isinstance(rows, list):
            candidate[key] = [
                row
                for row in rows
                if not isinstance(row, dict) or row.get("status") not in {"PENDING", "RUNNING"}
            ]
    for key in derived_keys:
        candidate[key] = normalized.get(key)
    for key in optional_empty_collections:
        if key not in candidate and normalized.get(key) == []:
            candidate[key] = []
    return candidate == normalized
