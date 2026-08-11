import json
from pathlib import Path
from typing import Any

import pytest

from backend.app.evaluation_lineage import (
    build_source_evaluation_checksum,
    canonical_stage4_checksum,
    validate_evaluation_lineage_payload,
)

_contract = Path("docs/API_CONTRACT.md").read_text(encoding="utf-8")
GOLDEN_V2_LINEAGE = json.loads(_contract.rsplit("```json\n", 1)[1].split("\n```", 1)[0])
GOLDEN_V2_DIGEST = "sha256:a956a969f4f147fb020fa06b71722d8fcf76ad850f0c5f6be8d78bbbadb81377"


def _leaf_paths(value: Any, path: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    if isinstance(value, dict):
        return [leaf for key, child in value.items() for leaf in _leaf_paths(child, (*path, key))]
    if isinstance(value, list):
        return [
            leaf for index, child in enumerate(value) for leaf in _leaf_paths(child, (*path, index))
        ]
    return [path]


def test_runtime_reproduces_frozen_v2_digest_and_binds_every_leaf() -> None:
    assert build_source_evaluation_checksum(GOLDEN_V2_LINEAGE) == GOLDEN_V2_DIGEST
    for path in _leaf_paths(GOLDEN_V2_LINEAGE):
        mutated = json.loads(json.dumps(GOLDEN_V2_LINEAGE))
        cursor = mutated
        for key in path[:-1]:
            cursor = cursor[key]
        original = cursor[path[-1]]
        cursor[path[-1]] = (
            not original
            if isinstance(original, bool)
            else original + 1
            if isinstance(original, int)
            else original + "x"
        )
        try:
            digest = build_source_evaluation_checksum(validate_evaluation_lineage_payload(mutated))
        except ValueError:
            continue
        assert digest != GOLDEN_V2_DIGEST


def test_checksum_requires_payload_and_rejects_legacy_call_shape() -> None:
    with pytest.raises(TypeError):
        build_source_evaluation_checksum()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        build_source_evaluation_checksum(  # type: ignore[call-arg]
            source_evaluation_id="eval",
            source_run_id="run",
        )


def test_stage4_source_checksum_is_normalized_without_weakening_payload_validation() -> None:
    digest = "1" * 64
    assert canonical_stage4_checksum(digest) == f"sha256:{digest}"
    with pytest.raises(ValueError):
        canonical_stage4_checksum("not-a-checksum")


@pytest.mark.parametrize("score", [0.91, True, "nan", "inf", "-0", "1.1", "-0.1", "9.1e-1", "0.910"])
def test_checksum_rejects_noncanonical_score_encodings(score: object) -> None:
    payload = json.loads(json.dumps(GOLDEN_V2_LINEAGE))
    payload["selectedContext"][0]["retrievalScore"] = score
    with pytest.raises(ValueError, match="score"):
        build_source_evaluation_checksum(payload)


def test_payload_rejects_duplicate_identity_cross_scope_and_invalid_refusal_state() -> None:
    mutations = []
    duplicate = json.loads(json.dumps(GOLDEN_V2_LINEAGE))
    duplicate["selectedContext"].append(duplicate["selectedContext"][0])
    mutations.append(duplicate)
    cross_scope = json.loads(json.dumps(GOLDEN_V2_LINEAGE))
    cross_scope["selectedContext"][0]["tenantId"] = "tenant_other"
    mutations.append(cross_scope)
    refused = json.loads(json.dumps(GOLDEN_V2_LINEAGE))
    refused["selectedContext"] = []
    mutations.append(refused)
    for payload in mutations:
        with pytest.raises(ValueError):
            validate_evaluation_lineage_payload(payload)


def test_cut1_grounding_evidence_is_checksum_bound_without_changing_v2_payloads() -> None:
    payload = json.loads(json.dumps(GOLDEN_V2_LINEAGE))
    claims = [
        {
            "claimId": "claim_001",
            "propositionEvidenceChecksum": "sha256:" + "1" * 64,
            "propositionIds": ["fact_001", "fact_002"],
        }
    ]
    payload["sourceCitationIndexes"] = [1]
    payload["groundingEvidence"] = {
        "checksum": canonical_stage4_checksum(
            __import__("hashlib").sha256(
                json.dumps(claims, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
        ),
        "claims": claims,
        "policyVersion": "cut1-atomic-grounding-v1",
    }

    validated = validate_evaluation_lineage_payload(payload)
    digest = build_source_evaluation_checksum(validated)

    assert digest != GOLDEN_V2_DIGEST
    mutated = json.loads(json.dumps(payload))
    mutated["groundingEvidence"]["claims"][0]["propositionIds"].pop()
    with pytest.raises(ValueError, match="checksum"):
        validate_evaluation_lineage_payload(mutated)
