"""Shared validation for persisted Stage 6/7 evaluation lineage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

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


@dataclass(frozen=True)
class LineageActivation:
    payload: dict[str, Any]
    digest: str
    rows: tuple[PersistedLineage, ...]


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


def validate_lineage_for_run(
    payload: Mapping[str, object],
    checksum: str,
    run: WalkthroughRunRecord,
) -> dict[str, Any]:
    derived = derive_evaluation_lineage(run)
    given = validate_evaluation_lineage_payload(payload)
    if given != derived or build_source_evaluation_checksum(derived) != checksum:
        raise ValueError("Stage 4 mismatch.")
    return derived


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
