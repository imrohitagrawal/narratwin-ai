from __future__ import annotations

import importlib.util
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "scripts/quality/stage8_brace_expansion_unblock.py"
BRANCH = "cut1-process-360-security-brace-expansion-5-0-9-unblock"
BASE = "b9a2a8cd4aa05328116565990fc30ae44592c875"
FILES = {
    "docs/governance/preflights/issue-360.json", "docs/QUALITY_GATES.md", "docs/SECURITY_AND_PRIVACY.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md", "docs/TRACEABILITY.md",
    "docs/ADR/0049-semgrep-cryptography-50-lock-refresh.md",
    "docs/ADR/0050-brace-expansion-5-0-9-security-refresh.md", "frontend/package.json", "frontend/package-lock.json",
    "scripts/ci/check_semgrep_security.py", "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_brace_expansion_unblock.py", "tests/unit/test_dependency_security_contract.py",
    "tests/unit/test_stage8_brace_expansion_unblock.py", "tools/semgrep/reviewed-inputs.sha256",
    "tools/semgrep/uv.lock",
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


def test_issue360_preflight_and_base_mutations_fail_closed() -> None:
    sidecar: Any = load(SIDECAR, "brace_security_mutations")
    data = json.loads((ROOT / "docs/governance/preflights/issue-360.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    sidecar.validate_preflight(data, failures)
    assert failures == []
    for mutate in (
        lambda value: value.update(issue_number=359),
        lambda value: value.update(branch=f"{BRANCH}-retry"),
        lambda value: value.update(objective=value["objective"].replace(BASE, "0" * 40)),
        lambda value: value["scope"]["required"].append("nineteenth-path"),
    ):
        candidate = copy.deepcopy(data)
        mutate(candidate)
        failures = []
        sidecar.validate_preflight(candidate, failures)
        assert failures

    head = "f" * 40
    valid = {
        ("git", "rev-parse", f"{BASE}^{{commit}}"): BASE,
        ("git", "rev-parse", "HEAD^{commit}"): head,
        ("git", "merge-base", BASE, head): BASE,
        ("git", "diff", "--numstat", "--no-renames", f"{BASE}..{head}", "--"):
            "\n".join(f"1\t0\t{path}" for path in sorted(FILES)),
    }
    def run(args: list[str]) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout=valid[tuple(args)], stderr="")
    failures = []
    sidecar.check_exact_route(ROOT, run, failures, True)
    assert failures == []
    excessive = dict(valid)
    diff_command = ("git", "diff", "--numstat", "--no-renames", f"{BASE}..{head}", "--")
    excessive[diff_command] = "\n".join(
        f"{651 if index == 0 else 0}\t0\t{path}" for index, path in enumerate(sorted(FILES))
    )
    failures = []
    sidecar.check_exact_route(
        ROOT, lambda args: SimpleNamespace(returncode=0, stdout=excessive[tuple(args)]), failures, True
    )
    assert failures == ["Issue #360 requires exactly 18 paths and at most 650 charged lines."]
    for command in list(valid)[:3]:
        broken = dict(valid)
        broken[command] = ""
        failures = []
        sidecar.check_exact_route(
            ROOT, lambda args, values=broken: SimpleNamespace(returncode=0, stdout=values[tuple(args)]),
            failures, True,
        )
        assert failures
        failures = []
        sidecar.check_exact_route(
            ROOT, lambda args, target=command: SimpleNamespace(
                returncode=int(tuple(args) == target), stdout=valid[tuple(args)]
            ), failures, True,
        )
        assert failures


def test_issue360_near_match_and_nineteenth_path_are_denied(monkeypatch: Any) -> None:
    checker: Any = load(ROOT / "scripts/quality/check_stage8_docs.py", "stage8_issue360_mutations")
    monkeypatch.setattr(checker, "current_branch", lambda: f"{BRANCH}-retry")
    monkeypatch.setattr(checker, "changed_files_for_stage_scope", lambda: [])
    failures: list[str] = []
    checker.check_stage_marker_and_branch(failures)
    checker.check_stage_scope(failures)
    assert len(failures) == 2
    monkeypatch.setattr(checker, "current_branch", lambda: BRANCH)
    monkeypatch.setattr(checker, "changed_files_for_stage_scope", lambda: ["nineteenth-path"])
    failures = []
    checker.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: nineteenth-path"]
