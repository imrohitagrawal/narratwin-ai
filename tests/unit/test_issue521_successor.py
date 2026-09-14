"""Independent expectations for the bounded four-entry G1 correction."""
from pathlib import Path

from scripts.quality import issue521_master_program_v2 as predecessor

ROOT = Path(__file__).resolve().parents[2]
SUCCESSOR = "docs/governance/successors/g1-adr0000/superset-mapping-v2.json"
REMOVED = frozenset({
    "MPV2-6FD1AF1B119751D12FE6", "MPV2-29F6F8A4F175178310E3",
    "MPV2-7A08CF034D6B2A3D447D", "MPV2-D5086F6004054DDDA5F6",
})


def test_bibliography_candidate_excludes_exact_four_normative_rows() -> None:
    # Before the successor exists, exercise the actual predecessor's semantics.
    # This makes the recorded RED a source classification failure, not an import failure.
    candidate = ROOT / SUCCESSOR
    if not candidate.exists():
        candidate = ROOT / predecessor.MAPPING_PATH
    mapping = predecessor.decode_mapping_artifact(predecessor._load_json(candidate))
    rows = mapping["rows"]
    promoted = [row for row in rows if row["requirementId"] in REMOVED]
    assert not promoted, "Bibliography-only references remain promoted to normative mapping rows"
    assert len(rows) == 31_394
    partition = mapping["repositorySemanticDecisionPartition"]
    adr = next(entry for entry in partition["sources"] if entry[0] == "ADR_0000_ADR_PROCESS")
    assert adr[4][18:22] == "RRRR"
    assert len([row for row in rows if row["sourceId"] == "ADR_0000_ADR_PROCESS"]) == 17
