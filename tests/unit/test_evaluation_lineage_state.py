import json
from dataclasses import replace
from pathlib import Path

import pytest

from backend.app.evaluation_lineage import build_source_evaluation_checksum
from backend.app.evaluation_lineage_state import (
    PersistedLineage,
    quarantine_reason_for_schema,
    refuse_quarantined_write,
    validate_connected_lineages,
    validate_lineage_binding,
    validate_upstream_connections,
)

_contract = Path("docs/API_CONTRACT.md").read_text(encoding="utf-8")
GOLDEN_V2_LINEAGE = json.loads(_contract.rsplit("```json\n", 1)[1].split("\n```", 1)[0])


def test_connected_rows_require_exact_canonical_payload_and_digest() -> None:
    digest = build_source_evaluation_checksum(GOLDEN_V2_LINEAGE)
    identity = GOLDEN_V2_LINEAGE["evaluation"]
    activation = validate_connected_lineages(
        GOLDEN_V2_LINEAGE,
        digest,
        (
            PersistedLineage(
                component="Stage 6 multilingual run",
                row_id="mlrun_000001",
                source_run_id=identity["runId"],
                payload=GOLDEN_V2_LINEAGE,
                digest=digest,
            ),
        ),
    )
    assert activation.digest == digest
    assert len(activation.rows) == 1

    with pytest.raises(ValueError, match="mismatched"):
        validate_connected_lineages(
            GOLDEN_V2_LINEAGE,
            digest,
            (
                PersistedLineage(
                    component="Stage 7 render",
                    source_run_id=identity["runId"],
                    payload=GOLDEN_V2_LINEAGE,
                    digest="sha256:" + "0" * 64,
                ),
            ),
        )


def test_request_binding_rejects_missing_payload_before_replay() -> None:
    with pytest.raises(ValueError, match="required"):
        validate_lineage_binding(None, "sha256:" + "0" * 64)


def test_stage7_bundle_requires_the_exact_connected_stage6_row() -> None:
    stage6 = PersistedLineage(
        component="Stage 6", source_run_id="run", row_id="mlrun", payload={}, digest="",
        connected_values=("es", "translated", "subtitles", "voice"),
    )
    stage7 = replace(stage6, component="Stage 7", row_id="render", upstream_row_id="mlrun")
    validate_upstream_connections((stage6, stage7))
    with pytest.raises(ValueError, match="upstream Stage 6 bundle"):
        validate_upstream_connections((stage6, replace(stage7, connected_values=("stale",))))


def test_schema_decision_distinguishes_current_legacy_and_future() -> None:
    assert (
        quarantine_reason_for_schema(
            "stage6-local-state-v3",
            current="stage6-local-state-v3",
            legacy=frozenset({"stage6-local-state-v1", "stage6-local-state-v2"}),
            stage="Stage 6",
        )
        is None
    )
    reason = quarantine_reason_for_schema(
        "stage6-local-state-v2",
        current="stage6-local-state-v3",
        legacy=frozenset({"stage6-local-state-v1", "stage6-local-state-v2"}),
        stage="Stage 6",
    )
    assert reason == "legacy Stage 6 state"
    with pytest.raises(ValueError, match="schema mismatch"):
        quarantine_reason_for_schema(
            "stage6-local-state-v999",
            current="stage6-local-state-v3",
            legacy=frozenset({"stage6-local-state-v1", "stage6-local-state-v2"}),
            stage="Stage 6",
        )
    with pytest.raises(OSError, match="quarantined legacy Stage 6"):
        refuse_quarantined_write(reason)
