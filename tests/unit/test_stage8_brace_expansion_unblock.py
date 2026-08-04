from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "scripts/quality/stage8_brace_expansion_unblock.py"
BRANCH = "cut1-process-360-security-brace-expansion-5-0-9-unblock"
BASE = "b9a2a8cd4aa05328116565990fc30ae44592c875"
FILES = {
    "docs/governance/preflights/issue-360.json", "docs/QUALITY_GATES.md", "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md", "docs/TRACEABILITY.md",
    "docs/ADR/0050-brace-expansion-5-0-9-security-refresh.md", "frontend/package.json",
    "frontend/package-lock.json", "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_brace_expansion_unblock.py", "tests/unit/test_dependency_security_contract.py",
    "tests/unit/test_stage8_brace_expansion_unblock.py",
}


def load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_issue360_sidecar_and_effective_route_are_exact() -> None:
    assert SIDECAR.is_file(), "RED: the bounded Issue #360 Stage 8 sidecar is absent"
    sidecar: Any = load(SIDECAR, "brace_security_under_test")
    checker: Any = load(ROOT / "scripts/quality/check_stage8_docs.py", "stage8_issue360_under_test")
    preflight = json.loads((ROOT / "docs/governance/preflights/issue-360.json").read_text(encoding="utf-8"))

    assert (sidecar.BRANCH, sidecar.BASE, sidecar.ALLOWED_FILES) == (BRANCH, BASE, FILES)
    assert sidecar.BRACE_EXPANSION_ROUTES == {BRANCH: FILES}
    assert BRANCH not in checker.PROCESS_BRANCH_ALLOWED_FILES
    assert checker.EFFECTIVE_STAGE8_ROUTES[BRANCH] == FILES
    assert preflight["branch"] == BRANCH and set(preflight["scope"]["required"]) == FILES
    assert preflight["objective"].count(BASE) == 1
