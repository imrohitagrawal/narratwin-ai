from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.quality.cut1_presenter_contract import finding_codes, validate_contract_bundle


ROOT = Path(__file__).parents[2]
GOVERNANCE = ROOT / "docs/governance"
V1_FREEZE = GOVERNANCE / "cut1-presenter-contract-red-freeze-v1.json"
V2_BINDING = GOVERNANCE / "cut1-presenter-live-binding-v2.json"
IMMUTABLE_INPUT = "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json"


def isolated_bundle(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    freeze = json.loads(V1_FREEZE.read_text(encoding="utf-8"))
    paths = set(freeze["frozenFileSha256"]) | {
        "docs/governance/cut1-presenter-contract-red-freeze-v1.json"
    }
    if V2_BINDING.exists():
        paths.add("docs/governance/cut1-presenter-live-binding-v2.json")
    for relative in sorted(paths):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return root


def test_mutable_status_evolution_does_not_reject_immutable_bundle(tmp_path: Path) -> None:
    root = isolated_bundle(tmp_path)
    status = root / "docs/STATUS.md"
    status.write_text(status.read_text(encoding="utf-8") + "\nTruthful later ledger entry.\n", encoding="utf-8")

    assert finding_codes(validate_contract_bundle(root)) == ()


def test_immutable_contract_tamper_remains_rejected(tmp_path: Path) -> None:
    root = isolated_bundle(tmp_path)
    immutable = root / IMMUTABLE_INPUT
    immutable.write_text(immutable.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert finding_codes(validate_contract_bundle(root)) == ("CUT1.BUNDLE.PROTOCOL",)
