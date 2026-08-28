from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from scripts.quality.cut1_presenter_contract import finding_codes, validate_contract_bundle


ROOT = Path(__file__).parents[2]
GOVERNANCE = ROOT / "docs/governance"
V1_FREEZE = GOVERNANCE / "cut1-presenter-contract-red-freeze-v1.json"
V2_BINDING = GOVERNANCE / "cut1-presenter-live-binding-v2.json"
IMMUTABLE_INPUT = "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json"
IMMUTABLE_SHA256 = {
    IMMUTABLE_INPUT: "f61cef9f7731f4603778d1b6a3a9ccccd3682c8e0ad233c9370169320612b2f5",
    "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json": "fa3759985141639185618fbc595057412dd8582f60ed97fc462b30b7548580b8",
    "docs/governance/cut1-provider-bakeoff-contract-v1.json": "1a3fd981644488203e8c7cc38fc0389092b23b579cce860c3d35a1ca7a1786db",
    "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json": "14eac190bd8ee590d1c1bd59cd6fa16b9413322e1e3a5bca23dfb9030afc5f9c",
    "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json": "cb5ad105b53f52e8be888bb8007098368a9f08eafc7ea3eb407f035a5d13b31a",
}
HISTORICAL_V1: dict[str, Any] = {
    "manifestPath": "docs/governance/cut1-presenter-contract-red-freeze-v1.json",
    "manifestSha256": "b9921a468f1383a3525879144992fd9ccb30c3dbf62481dcfc9f6e2d3b8afceb",
    "acceptedPullRequest": 455,
    "acceptedHead": "89164f25998b0088ae2b6c645dbe935efe50cf7e",
    "acceptedTree": "6d42093643a133f239265432a2cca4f539eb392b",
    "mergeCommit": "c3ac83bf05336a539dbdd6af1de9905e6b954289",
}
EXPECTED_BINDING: dict[str, Any] = {
    "schemaVersion": "Cut1PresenterLiveBindingV2",
    "issue": 456,
    "activation": "NONE",
    "authorityEffect": "NO_AUTHORITY_EFFECT",
    "releasePosture": "NO_GO",
    "historicalV1": HISTORICAL_V1,
    "immutableInputSha256": IMMUTABLE_SHA256,
    "limitations": [
        "This live binding changes integrity routing only; every Cut 1 acceptance threshold and presenter requirement remains unchanged.",
        "Mutable ledgers, routes, tests, ADRs, preflights, and canonical prose remain historically auditable through the v1 freeze but are not current-byte inputs.",
        "No product, provider, media, credential, egress, spend, deployment, release, or production-readiness authority is created.",
    ],
}
MUTABLE_V1_INPUTS = (
    "docs/STATUS.md",
    "docs/QUALITY_GATES.md",
    "docs/TRACEABILITY.md",
    "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md",
    "docs/ADR/0065-cut1-all-presenter-acceptance-provider-bakeoff.md",
    "docs/governance/preflights/issue-452.json",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "scripts/quality/cut1_presenter_contract.py",
)


def isolated_bundle(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    freeze = json.loads(V1_FREEZE.read_text(encoding="utf-8"))
    paths = set(freeze["frozenFileSha256"]) | {
        "docs/governance/cut1-presenter-contract-red-freeze-v1.json"
    }
    for relative in sorted(paths):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    binding = root / "docs/governance/cut1-presenter-live-binding-v2.json"
    binding.parent.mkdir(parents=True, exist_ok=True)
    if V2_BINDING.exists():
        shutil.copyfile(V2_BINDING, binding)
    else:
        binding.write_text(json.dumps(EXPECTED_BINDING, indent=2) + "\n", encoding="utf-8")
    return root


def assert_rejected(root: Path) -> None:
    assert finding_codes(validate_contract_bundle(root)) == ("CUT1.BUNDLE.PROTOCOL",)


def test_repository_manifest_matches_frozen_expected_value() -> None:
    assert V2_BINDING.is_file()
    assert json.loads(V2_BINDING.read_text(encoding="utf-8")) == EXPECTED_BINDING


def test_v1_history_identity_is_preserved() -> None:
    assert hashlib.sha256(V1_FREEZE.read_bytes()).hexdigest() == HISTORICAL_V1["manifestSha256"]
    assert HISTORICAL_V1["acceptedHead"] == "89164f25998b0088ae2b6c645dbe935efe50cf7e"
    assert HISTORICAL_V1["acceptedTree"] == "6d42093643a133f239265432a2cca4f539eb392b"


def test_pristine_bundle_passes(tmp_path: Path) -> None:
    assert finding_codes(validate_contract_bundle(isolated_bundle(tmp_path))) == ()


def test_mutable_status_evolution_does_not_reject_immutable_bundle(tmp_path: Path) -> None:
    root = isolated_bundle(tmp_path)
    status = root / "docs/STATUS.md"
    status.write_text(status.read_text(encoding="utf-8") + "\nTruthful later ledger entry.\n", encoding="utf-8")

    assert finding_codes(validate_contract_bundle(root)) == ()


def test_immutable_contract_tamper_remains_rejected(tmp_path: Path) -> None:
    root = isolated_bundle(tmp_path)
    immutable = root / IMMUTABLE_INPUT
    immutable.write_text(immutable.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert_rejected(root)


@pytest.mark.parametrize("relative", tuple(IMMUTABLE_SHA256))
@pytest.mark.parametrize("fault", ("tamper", "missing", "directory", "symlink", "oversized"))
def test_every_immutable_input_fault_fails_closed(tmp_path: Path, relative: str, fault: str) -> None:
    root = isolated_bundle(tmp_path)
    target = root / relative
    if fault == "tamper":
        target.write_bytes(target.read_bytes() + b"\n")
    else:
        target.unlink()
        if fault == "directory":
            target.mkdir()
        elif fault == "symlink":
            target.symlink_to(root / IMMUTABLE_INPUT)
        elif fault == "oversized":
            target.write_bytes(b"x" * 65_537)
    assert_rejected(root)


@pytest.mark.parametrize("relative", MUTABLE_V1_INPUTS)
def test_mutable_historical_surface_evolution_is_not_a_live_integrity_failure(tmp_path: Path, relative: str) -> None:
    root = isolated_bundle(tmp_path)
    target = root / relative
    target.write_bytes(target.read_bytes() + b"\nTruthful later change.\n")
    assert finding_codes(validate_contract_bundle(root)) == ()


@pytest.mark.parametrize("relative", ("docs", "docs/governance"))
def test_symlinked_parent_component_fails_closed(tmp_path: Path, relative: str) -> None:
    root = isolated_bundle(tmp_path)
    parent = root / relative
    relocated = parent.with_name(parent.name + "-real")
    parent.rename(relocated)
    parent.symlink_to(relocated, target_is_directory=True)
    assert_rejected(root)


@pytest.mark.parametrize("relative", (
    "docs/governance/cut1-presenter-contract-red-freeze-v1.json",
    "docs/governance/cut1-presenter-live-binding-v2.json",
))
@pytest.mark.parametrize("fault", ("missing", "directory", "symlink", "oversized"))
def test_binding_files_fail_closed_when_not_bounded_regular_files(tmp_path: Path, relative: str, fault: str) -> None:
    root = isolated_bundle(tmp_path)
    target = root / relative
    target.unlink()
    if fault == "directory":
        target.mkdir()
    elif fault == "symlink":
        target.symlink_to(root / IMMUTABLE_INPUT)
    elif fault == "oversized":
        target.write_bytes(b"x" * 65_537)
    assert_rejected(root)


@pytest.mark.parametrize("fault", (
    "malformed", "invalid-utf8", "duplicate", "duplicate-nested", "unknown", "unknown-nested",
    "missing", "wrong-history", "non-object", "non-finite",
))
def test_v2_manifest_shape_and_history_fail_closed(tmp_path: Path, fault: str) -> None:
    root = isolated_bundle(tmp_path)
    target = root / "docs/governance/cut1-presenter-live-binding-v2.json"
    value = json.loads(target.read_text(encoding="utf-8"))
    if fault == "malformed":
        target.write_text("{", encoding="utf-8")
    elif fault == "invalid-utf8":
        target.write_bytes(b"\xff")
    elif fault == "duplicate":
        target.write_text(target.read_text(encoding="utf-8").replace('"issue": 456,', '"issue": 456,\n  "issue": 456,'), encoding="utf-8")
    elif fault == "duplicate-nested":
        target.write_text(target.read_text(encoding="utf-8").replace('"acceptedPullRequest": 455,', '"acceptedPullRequest": 455,\n    "acceptedPullRequest": 455,'), encoding="utf-8")
    elif fault == "unknown":
        value["unknown"] = True
        target.write_text(json.dumps(value), encoding="utf-8")
    elif fault == "unknown-nested":
        value["historicalV1"]["unknown"] = True
        target.write_text(json.dumps(value), encoding="utf-8")
    elif fault == "missing":
        value.pop("authorityEffect")
        target.write_text(json.dumps(value), encoding="utf-8")
    elif fault == "wrong-history":
        value["historicalV1"]["acceptedHead"] = "0" * 40
        target.write_text(json.dumps(value), encoding="utf-8")
    elif fault == "non-object":
        target.write_text("[]", encoding="utf-8")
    else:
        target.write_text('{"value": NaN}', encoding="utf-8")
    assert_rejected(root)


def test_coherent_input_and_manifest_digest_tamper_still_fails(tmp_path: Path) -> None:
    root = isolated_bundle(tmp_path)
    immutable = root / IMMUTABLE_INPUT
    immutable.write_bytes(immutable.read_bytes() + b"\n")
    binding = root / "docs/governance/cut1-presenter-live-binding-v2.json"
    value = json.loads(binding.read_text(encoding="utf-8"))
    value["immutableInputSha256"][IMMUTABLE_INPUT] = hashlib.sha256(immutable.read_bytes()).hexdigest()
    binding.write_text(json.dumps(value), encoding="utf-8")
    assert_rejected(root)
