import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, cast

import pytest


def load_phase1_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "quality" / "check_phase1_closure_docs.py"
    spec = importlib.util.spec_from_file_location("phase1_closure_docs_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


phase1: Any = load_phase1_module()


def read_with_overrides(phase1_module: Any, overrides: dict[str, str]) -> Callable[[str], str]:
    original_read = cast(Callable[[str], str], phase1_module.read)

    def patched_read(rel: str) -> str:
        if rel in overrides:
            return overrides[rel]
        return original_read(rel)

    return patched_read


def replace_text(text: str, search: str, replacement: str) -> str:
    return text.replace(search, replacement, 1)


def remove_normalized_marker(text: str, marker: str) -> str:
    pattern = r"\s+".join(re.escape(part) for part in marker.split())
    mutated, replacements = re.subn(pattern, "REMOVED", text, flags=re.I)
    assert replacements > 0
    return mutated


def run_changed_files_check(monkeypatch: Any, *, branch: str, files: list[str]) -> list[str]:
    monkeypatch.setattr(phase1, "current_branch", lambda: branch)
    monkeypatch.setattr(phase1, "changed_files", lambda: files)
    failures: list[str] = []
    phase1.check_changed_files(failures)
    return failures


def run_branch_check(
    monkeypatch: Any,
    *,
    branch: str,
    ancestor_ok: bool = True,
) -> list[str]:
    monkeypatch.setattr(phase1, "current_branch", lambda: branch)
    monkeypatch.setattr(phase1, "git_ok", lambda args: ancestor_ok)
    failures: list[str] = []
    phase1.check_branch(failures)
    return failures


def run_process_docs_check(
    monkeypatch: Any, *, branch: str, changed: list[str], read_overrides: dict[str, str] | None = None
) -> list[str]:
    monkeypatch.setattr(phase1, "current_branch", lambda: branch)
    monkeypatch.setattr(phase1, "changed_files", lambda: changed)
    if read_overrides:
        monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_process_docs(failures)
    return failures


def run_issue39_closure_plan_check(monkeypatch: Any, *, plan_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md": plan_text},
        ),
    )
    failures: list[str] = []
    phase1.check_issue39_closure_plan(failures)
    return failures


def run_issue39_execution_strategy_check(monkeypatch: Any, *, strategy_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md": strategy_text},
        ),
    )
    failures: list[str] = []
    phase1.check_issue39_execution_strategy(failures)
    return failures


def run_issue241_preflight_check(monkeypatch: Any, *, preflight_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/reviews/ISSUE_241_DEMO_CHECKPOINT1_PR4_AVATAR_VIDEO_PREFLIGHT.md": preflight_text},
        ),
    )
    failures: list[str] = []
    phase1.check_issue241_avatar_video_preflight(failures)
    return failures


def run_issue243_preflight_check(monkeypatch: Any, *, preflight_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/reviews/ISSUE_243_DEMO_CHECKPOINT1_PR5_HOSTED_DEMO_PREFLIGHT.md": preflight_text},
        ),
    )
    failures: list[str] = []
    phase1.check_issue243_hosted_demo_preflight(failures)
    return failures


def run_issue249_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue249_checkpoint3a_preflight(failures)
    return failures


def run_issue253_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue253_c3a_cp1_preflight(failures)
    return failures


def run_issue257_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue257_c3a_cp2_preflight(failures)
    return failures


def run_issue259_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue259_c3a_cp3_preflight(failures)
    return failures


def run_issue261_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue261_c3a_cp4_preflight(failures)
    return failures


def run_issue263_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue263_c3a_cp5_preflight(failures)
    return failures


def run_issue265_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue265_c3a_cp6_preflight(failures)
    return failures


def run_issue39_ch11_contract_check(
    monkeypatch: Any,
    *,
    adr_text: str,
    plan_text: str | None = None,
) -> list[str]:
    overrides = {"docs/ADR/0025-ch11-slo-error-budget.md": adr_text}
    if plan_text is not None:
        overrides["docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"] = plan_text
    monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, overrides))
    failures: list[str] = []
    phase1.check_issue39_ch11_slo_contract(failures)
    return failures


def run_release_docs_check(monkeypatch: Any, *, read_overrides: dict[str, str]) -> list[str]:
    monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_release_docs(failures)
    return failures


def run_real_media_demo_plan_check(monkeypatch: Any, *, plan_text: str) -> list[str]:
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md": plan_text},
        ),
    )
    failures: list[str] = []
    phase1.check_real_media_demo_plan(failures)
    return failures


PHF020A_VALID_POLICY = """
# Phase Plan

## Product Mode Policy Authority

Only the registered tables in this section are authoritative for PHF-020A.

### Authority Registry

| ID | Table | Parent heading | Authority |
|---|---|---|---|
| AUTH-TAXONOMY | Product mode taxonomy | Product Mode Policy Authority | structured |
| AUTH-GATES | Cross-mode gate graph | Product Mode Policy Authority | structured |
| AUTH-MEDIA | Optional media relation | Product Mode Policy Authority | structured |
| AUTH-DUPLICATES | Duplicate reconciliation duties | Product Mode Policy Authority | structured |
| AUTH-ISSUE8 | Issue #8 acceptance transfer | Product Mode Policy Authority | structured |
| AUTH-ACTIVATION | PM-MODE-001 activation evidence | Product Mode Policy Authority | structured |

### Product Mode Taxonomy

| ID | Kind | Owner issue | Definition |
|---|---|---|---|
| DP-1 | delivery-phase | #1 | Product and PRD hardening; no product implementation |
| DP-2 | delivery-phase | #16 | Spec Kit constitution/spec/plan/tasks gate |
| P1C | closure-context | #39 | Phase 1 Closure context; not a product mode owner |
| PM-1 | product-mode | #155 | Controlled local synthetic artifact checkpoint |
| PM-2 | product-mode | #20 | Future interactive Q&A after Mode 1 Checkpoint B and reset |

### Cross-Mode Gate Graph

| Gate ID | From | To | Next gate | Prohibits |
|---|---|---|---|---|
| PM-GATE-00 | DP-1 | DP-2 | PM-GATE-10 | product runtime |
| PM-GATE-10 | DP-2 | PM-1 | PM-GATE-20 | Product Mode 2 |
| PM-GATE-20 | PM-1 | PM-2 | PM-GATE-30 | real media mandatory dependency |
| PM-GATE-30 | PM-2 | Future reset | none | no PHF020A implementation permission |

### Optional Media Relation

| Issue | Relation | Required before gate | Notes |
|---|---|---|---|
| #18 | optional-branch | PM-GATE-10 | TTS audio is not mandatory for PM-GATE-20 |
| #19 | optional-branch | PM-GATE-10 | Avatar video is not mandatory for PM-GATE-20 |

### Duplicate Reconciliation Duties

| Duty ID | Owner | Required action | Evidence |
|---|---|---|---|
| DUP-01 | #155 | Maintain one current module | STATUS row |
| DUP-02 | #8 | Preserve parent acceptance | Issue #8 link |
| DUP-03 | #167 | Preserve stopped predecessor evidence | PR #168 |
| DUP-04 | #184 | Replace prose scanning with structure | PHF020A tests |
| DUP-05 | PHF-020B | Normalize mutable current state later | successor issue |

### Issue #8 Acceptance Transfer

| Acceptance ID | Source | Stable policy row | Evidence |
|---|---|---|---|
| ISSUE8-01 | #8 | taxonomy distinctions | DP-1/DP-2/P1C/PM-1/PM-2 |
| ISSUE8-02 | #8 | Product Mode 1 local checkpoint | PM-1 |
| ISSUE8-03 | #8 | Product Mode 2 future reset | PM-2 |
| ISSUE8-04 | #8 | optional media independence | #18/#19 |
| ISSUE8-05 | #8 | duplicate reconciliation | DUP-01..DUP-05 |
| ISSUE8-06 | #8 | no runtime authorization | PM-GATE prohibitions |

### PM-MODE-001 Activation Evidence

| Evidence ID | Mode | Gate | Status |
|---|---|---|---|
| PM-MODE-001 | PM-1 | PM-GATE-10 | active-local-checkpoint |
""".strip()


PHF020A_SEEDS = (1103, 2207, 3301, 4409, 5519, 6619, 7723, 8837, 9941, 10039)
PHF020A_FAMILY_ORDER = (
    "structure/section",
    "table schema/delimiter",
    "containment/parent",
    "required/unknown/duplicate/reference",
    "taxonomy/enum",
    "graph/gate",
    "optional-media relation",
    "issue-#8 acceptance mapping",
    "current-state mixing",
    "resource/unicode/format bounds",
    "scope/preflight binding",
)
PHF020A_BASE_INVALID_COUNTS = {
    "structure/section": 2,
    "table schema/delimiter": 2,
    "containment/parent": 2,
    "required/unknown/duplicate/reference": 5,
    "taxonomy/enum": 2,
    "graph/gate": 3,
    "optional-media relation": 1,
    "issue-#8 acceptance mapping": 1,
    "current-state mixing": 1,
    "resource/unicode/format bounds": 2,
    "scope/preflight binding": 1,
}
PHF020A_SEED_EXTRA_FAMILIES = {
    1103: ("table schema/delimiter", "containment/parent", "optional-media relation"),
    2207: ("table schema/delimiter", "containment/parent", "issue-#8 acceptance mapping"),
    3301: ("table schema/delimiter", "containment/parent", "current-state mixing"),
    4409: ("table schema/delimiter", "containment/parent", "scope/preflight binding"),
    5519: ("table schema/delimiter", "optional-media relation", "issue-#8 acceptance mapping"),
    6619: ("containment/parent", "current-state mixing", "scope/preflight binding"),
    7723: ("optional-media relation", "issue-#8 acceptance mapping", "current-state mixing"),
    8837: ("optional-media relation", "issue-#8 acceptance mapping", "scope/preflight binding"),
    9941: ("optional-media relation", "current-state mixing", "scope/preflight binding"),
    10039: ("issue-#8 acceptance mapping", "current-state mixing", "scope/preflight binding"),
}
PHF020A_INVALID_TOTALS = {
    "structure/section": 20,
    "table schema/delimiter": 25,
    "containment/parent": 25,
    "required/unknown/duplicate/reference": 50,
    "taxonomy/enum": 20,
    "graph/gate": 30,
    "optional-media relation": 15,
    "issue-#8 acceptance mapping": 15,
    "current-state mixing": 15,
    "resource/unicode/format bounds": 20,
    "scope/preflight binding": 15,
}
PHF020A_SEED_INVALID_TOTALS = {
    seed: {
        family: PHF020A_BASE_INVALID_COUNTS[family]
        + (1 if family in PHF020A_SEED_EXTRA_FAMILIES[seed] else 0)
        for family in PHF020A_FAMILY_ORDER
    }
    for seed in PHF020A_SEEDS
}
PHF020A_ALLOWED_FINDING_FAMILIES = {
    "PHF020A.STRUCTURE",
    "PHF020A.TABLE",
    "PHF020A.CONTAINMENT",
    "PHF020A.REQUIRED",
    "PHF020A.UNKNOWN",
    "PHF020A.DUPLICATE",
    "PHF020A.TYPE",
    "PHF020A.ENUM",
    "PHF020A.REFERENCE",
    "PHF020A.TAXONOMY",
    "PHF020A.GRAPH",
    "PHF020A.MEDIA",
    "PHF020A.ACCEPTANCE",
    "PHF020A.STATE",
    "PHF020A.LIMIT",
    "PHF020A.SCOPE",
}
PHF020A_FAMILY_CODE_PREFIXES = {
    "structure/section": {"PHF020A.STRUCTURE"},
    "table schema/delimiter": {"PHF020A.TABLE"},
    "containment/parent": {"PHF020A.CONTAINMENT"},
    "required/unknown/duplicate/reference": {
        "PHF020A.REQUIRED",
        "PHF020A.UNKNOWN",
        "PHF020A.DUPLICATE",
        "PHF020A.REFERENCE",
    },
    "taxonomy/enum": {"PHF020A.ENUM", "PHF020A.TAXONOMY"},
    "graph/gate": {"PHF020A.GRAPH"},
    "optional-media relation": {"PHF020A.MEDIA"},
    "issue-#8 acceptance mapping": {"PHF020A.ACCEPTANCE"},
    "current-state mixing": {"PHF020A.STATE"},
    "resource/unicode/format bounds": {"PHF020A.LIMIT"},
    "scope/preflight binding": {"PHF020A.SCOPE"},
}


def phf020a_generated_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for seed_index, seed in enumerate(PHF020A_SEEDS):
        for index in range(25):
            cases.append(
                {
                    "id": f"{seed}:valid:{index}",
                    "seed": seed,
                    "valid": True,
                    "family": "valid",
                    "text": PHF020A_VALID_POLICY + f"\n\nSafe explanatory prose {seed}-{index}.\n",
                    "expected": [],
                    "mutation_id": None,
                    "mutation_count": 0,
                }
            )
        invalid_families = [
            family
            for family in PHF020A_FAMILY_ORDER
            for _ in range(PHF020A_SEED_INVALID_TOTALS[seed][family])
        ]
        assert len(invalid_families) == 25
        for index, family in enumerate(invalid_families):
            mutation_id = f"{family}:{seed}:{index}"
            text, expected = phf020a_mutated_policy(family, seed=seed, variant=index)
            mutation_descriptor = f"mutation descriptor: {mutation_id}:{expected[0]}"
            text = text + f"\n\n{mutation_descriptor}\n"
            cases.append(
                {
                    "id": f"{seed}:invalid:{index}:{family}",
                    "seed": seed,
                    "valid": False,
                    "family": family,
                    "text": text,
                    "expected": expected,
                    "mutation_id": mutation_id,
                    "mutation_descriptor": mutation_descriptor,
                    "mutation_count": 1,
                }
            )
    return cases


def phf020a_mutated_policy(family: str, *, seed: int = 0, variant: int = 0) -> tuple[str, list[str]]:
    text = PHF020A_VALID_POLICY
    if family == "structure/section":
        replacements = ("## Product Mode Notes", "### Product Mode Policy Authority")
        return text.replace("## Product Mode Policy Authority", replacements[variant % len(replacements)]), ["PHF020A.STRUCTURE.MISSING_PARENT"]
    if family == "table schema/delimiter":
        if variant % 2 == 0:
            return text.replace("|---|---|---|---|", "| ID | Table | Parent heading | Authority |", 1), ["PHF020A.TABLE.DELIMITER_MISSING"]
        return text.replace("|---|---|---|---|", "|---|---|---|", 1), ["PHF020A.TABLE.DELIMITER_WIDTH"]
    if family == "containment/parent":
        return text.replace("Product Mode Policy Authority | structured |", f"Relocated Policy {seed}-{variant} | structured |", 1), ["PHF020A.CONTAINMENT.PARENT"]
    if family == "required/unknown/duplicate/reference":
        selector = variant % 4
        if selector == 0:
            return text.replace("| AUTH-GATES | Cross-mode gate graph | Product Mode Policy Authority | structured |\n", ""), ["PHF020A.REQUIRED.MISSING_AUTHORITY"]
        if selector == 1:
            return text.replace("| AUTH-ACTIVATION | PM-MODE-001 activation evidence | Product Mode Policy Authority | structured |", f"| AUTH-UNKNOWN-{seed}-{variant} | PM-MODE-001 activation evidence | Product Mode Policy Authority | structured |"), ["PHF020A.UNKNOWN.AUTHORITY"]
        if selector == 2:
            return text.replace("| AUTH-ACTIVATION | PM-MODE-001 activation evidence | Product Mode Policy Authority | structured |", "| AUTH-GATES | PM-MODE-001 activation evidence | Product Mode Policy Authority | structured |"), ["PHF020A.DUPLICATE.AUTHORITY"]
        return text.replace("| PM-1 | product-mode | #155 |", "| PM-1 | product-mode | #8 |"), ["PHF020A.REFERENCE.OWNER"]
    if family == "taxonomy/enum":
        selector = variant % 3
        if selector == 0:
            return text.replace("| PM-2 | product-mode | #20 |", f"| PM-X-{seed}-{variant} | product-mode | #20 |"), ["PHF020A.ENUM.UNKNOWN_TAXONOMY"]
        if selector == 1:
            return text.replace("| PM-2 | product-mode | #20 |", "| PM-2 | launch-mode | #20 |"), ["PHF020A.ENUM.INVALID_KIND"]
        return text.replace(
            "Future interactive Q&A after Mode 1 Checkpoint B and reset",
            f"Immediate runtime authorization {seed}-{variant}",
        ), ["PHF020A.TAXONOMY.DEFINITION"]
    if family == "graph/gate":
        selector = variant % 3
        if selector == 0:
            return text.replace("| PM-GATE-20 | PM-1 | PM-2 | PM-GATE-30 |", "| PM-GATE-20 | PM-1 | PM-2 | none |"), ["PHF020A.GRAPH.EDGE_INVALID"]
        if selector == 1:
            return text.replace("| PM-GATE-30 | PM-2 | Future reset | none |", f"| PM-GATE-X-{seed}-{variant} | PM-2 | Future reset | none |"), ["PHF020A.GRAPH.NODE_INVALID"]
        return text.replace("Product Mode 2", f"none {seed}-{variant}", 1), ["PHF020A.GRAPH.PROHIBITS_INVALID"]
    if family == "optional-media relation":
        selector = variant % 3
        if selector == 0:
            return text.replace("TTS audio is not mandatory for PM-GATE-20", "TTS audio is mandatory for PM-GATE-20"), ["PHF020A.MEDIA.MANDATORY"]
        if selector == 1:
            return text.replace("| #19 | optional-branch | PM-GATE-10 |", "| #19 | required-branch | PM-GATE-20 |"), ["PHF020A.MEDIA.RELATION_INVALID"]
        return text.replace(
            "Avatar video is not mandatory for PM-GATE-20",
            f"Avatar video is not mandatory for PM-GATE-20 and mandatory for PM-GATE-20 {seed}-{variant}",
        ), ["PHF020A.MEDIA.MANDATORY"]
    if family == "issue-#8 acceptance mapping":
        selector = variant % 3
        if selector == 0:
            return text.replace("| ISSUE8-06 | #8 | no runtime authorization | PM-GATE prohibitions |\n", ""), ["PHF020A.ACCEPTANCE.MISSING"]
        if selector == 1:
            return text.replace("| ISSUE8-04 | #8 | optional media independence | #18/#19 |", "| ISSUE8-04 | #155 | optional media independence | #18/#19 |"), ["PHF020A.ACCEPTANCE.SOURCE_INVALID"]
        return text.replace("no runtime authorization", f"runtime authorization {seed}-{variant}"), ["PHF020A.ACCEPTANCE.ROW_INVALID"]
    if family == "current-state mixing":
        return text + f"\n\nCurrent module is CH-M1-{variant + 1:02d}.\n", ["PHF020A.STATE.MUTABLE_CURRENT_STATE"]
    if family == "resource/unicode/format bounds":
        selector = variant % 7
        if selector == 0:
            return ("# Phase Plan\n" + ("x" * (256 * 1024 + 1))), ["PHF020A.LIMIT.BYTES"]
        if selector == 1:
            return "\n".join("# h" for _ in range(10_001)), ["PHF020A.LIMIT.LINES"]
        if selector == 2:
            return "\n".join(f"## h{i}" for i in range(257)), ["PHF020A.LIMIT.HEADINGS"]
        if selector == 3:
            return text.replace("structured |", ("x" * 2049) + " |", 1), ["PHF020A.LIMIT.CELL"]
        if selector == 4:
            return text + "\x00", ["PHF020A.LIMIT.CONTROL"]
        if selector == 5:
            decoys = "\n".join("| A |\n|---|\n| B |" for _ in range(65))
            return text + "\n\n" + decoys, ["PHF020A.LIMIT.TABLES"]
        long_rows = "\n".join("| A |" for _ in range(2049))
        return text + "\n\n" + long_rows, ["PHF020A.LIMIT.ROWS"]
    if family == "scope/preflight binding":
        forbidden = ("backend/app/main.py", "frontend/src/app/page.tsx", "package.json")
        return text.replace("PHF020A tests", forbidden[variant % len(forbidden)]), ["PHF020A.SCOPE.FORBIDDEN_REFERENCE"]
    raise AssertionError(f"unhandled family: {family}")


def test_issue184_branch_allows_only_exact_replacement_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-184.json",
        "AGENTS.md",
        "docs/PHASE_PLAN.md",
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_184_ALLOWED_CHANGED_FILES == expected
    branch = "phase-1-closure-process-184-phf-020a-structured-policy-replacement"
    assert run_changed_files_check(monkeypatch, branch=branch, files=sorted(expected)) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["docs/SKILL_SELECTION_AND_EVIDENCE.md", "scripts/guardrails_check.py"],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/SKILL_SELECTION_AND_EVIDENCE.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/guardrails_check.py.",
    ]
    near_match = branch + "-extra"
    assert run_changed_files_check(monkeypatch, branch=near_match, files=["docs/PHASE_PLAN.md"]) == [
        f"Phase 1 Closure branch {near_match} may not change docs/PHASE_PLAN.md."
    ]


def test_issue188_branch_allows_only_status_state_v1_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-188.json",
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_188_ALLOWED_CHANGED_FILES == expected
    branch = "phase-1-closure-process-188-phf-020b-status-state-v1"
    assert run_changed_files_check(monkeypatch, branch=branch, files=sorted(expected)) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["AGENTS.md", "scripts/guardrails_check.py"],
    ) == [
        f"Phase 1 Closure branch {branch} may not change AGENTS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/guardrails_check.py.",
    ]


def test_issue208_209_branch_allows_only_real_stack_demo_and_quality_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-208.json",
        "docs/reviews/ISSUE_208_209_CH_M1_02_PREFLIGHT.md",
        "docs/ADR/0029-ch-m1-02-real-stack-evidence.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "frontend/playwright.real-stack.config.ts",
        "frontend/tests/real-stack.spec.ts",
        "scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/check_quality_stage.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_quality_dispatcher.py",
    }
    assert phase1.ISSUE_208_209_ALLOWED_CHANGED_FILES == expected
    branch = "phase-1-closure-208-ch-m1-02-demo-evidence"
    assert run_changed_files_check(monkeypatch, branch=branch, files=sorted(expected)) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["backend/app/main.py", "frontend/src/app/page.tsx", "docker-compose.yml"],
    ) == [
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change docker-compose.yml.",
    ]


def test_issue213_branch_allows_only_mode1_checkpoint_a_to_b_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-213.json",
        "docs/reviews/ISSUE_213_CHECKPOINT_A_B_EVIDENCE.md",
        "docs/reviews/ISSUE_213_MODE1_CHECKPOINT_A_TO_B_PREFLIGHT.md",
        "docs/ADR/0030-mode1-stage6-stage7-bundle-binding.md",
        "docs/API_CONTRACT.md",
        "docs/STATUS.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/TRACEABILITY.md",
        "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
        "docs/demo/PHASE_1_DEMO_SCRIPT.md",
        "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
        "demo/stage8_seed_project.md",
        "README.md",
        "portfolio/README.md",
        "backend/app/main.py",
        "backend/app/stage6.py",
        "backend/app/stage7.py",
        "tests/unit/test_stage6_multilingual.py",
        "tests/unit/test_stage7_avatar.py",
        "tests/unit/test_local_durability.py",
        "tests/api/test_stage6_multilingual_api.py",
        "tests/api/test_stage7_avatar_api.py",
        "frontend/src/app/page.tsx",
        "frontend/src/app/page.test.tsx",
        "frontend/playwright.real-stack.config.ts",
        "frontend/tests/smoke.spec.ts",
        "frontend/tests/real-stack.spec.ts",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_213_ALLOWED_CHANGED_FILES == expected
    branch = "phase-1-closure-155-mode1-checkpoint-a-to-b"
    assert run_changed_files_check(monkeypatch, branch=branch, files=sorted(expected)) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["docker-compose.yml", ".github/workflows/ci.yml", "frontend/package.json"],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docker-compose.yml.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/ci.yml.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
    ]


def test_phase1_quality_docs_make_main_dispatch_behavior_unambiguous() -> None:
    quality_gates = Path("docs/QUALITY_GATES.md").read_text(encoding="utf-8")
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")

    assert (
        "When `docs/STATUS.md` StatusStateV1 records `SSV1-MODE` as `phase1-closure`, "
        "plain local `make quality` on `main` dispatches the Phase 1 Closure gate."
    ) in quality_gates
    assert (
        "Plain local `make quality` on `main` dispatches Phase 1 Closure while "
        "StatusStateV1 records `SSV1-MODE` as `phase1-closure`."
    ) in status


def test_real_media_hosted_demo_plan_is_required_and_guarded(monkeypatch: Any) -> None:
    assert "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md" in phase1.REQUIRED_PHASE1_FILES
    text = Path("docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md").read_text(encoding="utf-8")

    for marker in (
        "User uploads or uses project knowledge",
        "Provider-Backed Path",
        "Checkpoint 1: Real Media Without Cloned Identity",
        "Checkpoint 2: Cloned Identity",
        "Failure Matrix Categories",
        "Fan-Out Review Requirements",
        "no production-readiness claim",
        "Cost-minimized first-month demo target",
        "owner-approved pre-generated real-media walkthrough",
        "source-run/eval/citation mismatch",
        "language/audience inputs attempt to override rules",
        "provider-side clone profile deletion",
    ):
        assert marker in text

    assert run_real_media_demo_plan_check(monkeypatch, plan_text=text) == []


@pytest.mark.parametrize(
    "removed_marker",
    (
        "provider-key secret storage outside the repo",
        "owner-approved pre-generated real-media walkthrough",
        "source-run/eval/citation mismatch",
        "language/audience inputs attempt to override rules",
        "MIME/type/size validation failure",
        "provider-side clone profile deletion",
    ),
)
def test_real_media_hosted_demo_plan_rejects_missing_contract_terms(
    monkeypatch: Any, removed_marker: str
) -> None:
    text = Path("docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md").read_text(encoding="utf-8")
    failures = run_real_media_demo_plan_check(
        monkeypatch,
        plan_text=text.replace(removed_marker, "REMOVED", 1),
    )
    assert failures


def test_process_branch_allows_real_media_plan_but_rejects_runtime_files(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-225-demo-real-media-phase0-plan"
    allowed = [
        "docs/governance/preflights/issue-225.json",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "backend/app/stage7.py",
            "frontend/package.json",
            ".github/workflows/quality-gates.yml",
            "docs/PRD.md",
            "portfolio/README.md",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change docs/PRD.md.",
        f"Phase 1 Closure branch {branch} may not change portfolio/README.md.",
    ]


def test_issue_229_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-229-demo-checkpoint1-spec-governance"
    allowed = [
        "docs/governance/preflights/issue-229.json",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[*allowed, "docs/TRACEABILITY.md"],
    ) == [f"Phase 1 Closure branch {branch} may not change docs/TRACEABILITY.md."]


def test_issue_235_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-235-demo-checkpoint1-contract"
    allowed = [
        "docs/governance/preflights/issue-235.json",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/LAUNCH_LEVELS.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[*allowed, "docs/TRACEABILITY.md", "backend/app/stage6.py"],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/TRACEABILITY.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
    ]


def test_issue_237_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-237-demo-checkpoint1-pr3-real-tts"
    allowed = [
        "docs/governance/preflights/issue-237.json",
        "docs/reviews/ISSUE_237_DEMO_CHECKPOINT1_PR3_TTS_PREFLIGHT.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "docs/API_CONTRACT.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "backend/app/tts_provider.py",
        "backend/app/stage6.py",
        "backend/app/main.py",
        "tests/unit/test_stage6_tts_provider.py",
        "tests/unit/test_stage6_multilingual.py",
        "tests/api/test_stage6_multilingual_api.py",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "backend/app/stage7.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
    ]


def test_issue_241_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-241-demo-checkpoint1-pr4-avatar-video"
    allowed = [
        "docs/governance/preflights/issue-241.json",
        "docs/reviews/ISSUE_241_DEMO_CHECKPOINT1_PR4_AVATAR_VIDEO_PREFLIGHT.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "docs/API_CONTRACT.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "backend/app/avatar_video_provider.py",
        "backend/app/stage7.py",
        "backend/app/main.py",
        "tests/unit/test_stage7_avatar_video_provider.py",
        "tests/unit/test_stage7_avatar.py",
        "tests/api/test_stage7_avatar_api.py",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "pyproject.toml",
            "docs/LAUNCH_LEVELS.md",
            "backend/app/stage6.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change docs/LAUNCH_LEVELS.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
    ]


def test_issue_241_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-241-demo-checkpoint1-pr4-avatar-video-typo"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-241.json",
            "docs/STAGE_ISSUE_PLAN.md",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-241.json.",
        f"Phase 1 Closure branch {branch} may not change docs/STAGE_ISSUE_PLAN.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_243_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-243-demo-checkpoint1-pr5-hosted-demo"
    allowed = [
        "docs/governance/preflights/issue-243.json",
        "docs/reviews/ISSUE_243_DEMO_CHECKPOINT1_PR5_HOSTED_DEMO_PREFLIGHT.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/LAUNCH_LEVELS.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "docs/API_CONTRACT.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "backend/app/hosted_demo.py",
        "backend/app/main.py",
        "tests/unit/test_hosted_demo.py",
        "tests/api/test_hosted_demo_api.py",
        "frontend/src/app/page.tsx",
        "frontend/src/app/page.test.tsx",
        "frontend/tests/smoke.spec.ts",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "pyproject.toml",
            "uv.lock",
            "frontend/Dockerfile",
            "docker-compose.yml",
            "backend/app/avatar_video_provider.py",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
            "frontend/package.json",
            "frontend/package-lock.json",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change frontend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change docker-compose.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/app/avatar_video_provider.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
    ]


def test_issue_243_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-243-demo-checkpoint1-pr5-hosted-demo-typo"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-243.json",
            "docs/STAGE_ISSUE_PLAN.md",
            "backend/app/hosted_demo.py",
            "frontend/src/app/page.tsx",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-243.json.",
        f"Phase 1 Closure branch {branch} may not change docs/STAGE_ISSUE_PLAN.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/hosted_demo.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
    ]


def test_issue_245_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-245-checkpoint1-acceptance-hardening"
    allowed = [
        "docs/governance/preflights/issue-245.json",
        "docs/reviews/ISSUE_245_DEMO_CHECKPOINT1_ACCEPTANCE_HARDENING.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/API_CONTRACT.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "backend/app/hosted_demo.py",
        "backend/app/main.py",
        "tests/unit/test_hosted_demo.py",
        "tests/api/test_hosted_demo_api.py",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/src/app/page.tsx",
        "frontend/src/app/page.test.tsx",
        "frontend/tests/smoke.spec.ts",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "pyproject.toml",
            "uv.lock",
            "frontend/Dockerfile",
            "docker-compose.yml",
            "backend/app/avatar_video_provider.py",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change frontend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change docker-compose.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/app/avatar_video_provider.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_245_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-245-checkpoint1-acceptance-hardening-typo"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-245.json",
            "docs/STATUS.md",
            "backend/app/hosted_demo.py",
            "tests/unit/test_hosted_demo.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-245.json.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/hosted_demo.py.",
        f"Phase 1 Closure branch {branch} may not change tests/unit/test_hosted_demo.py.",
    ]


def test_issue_249_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-249-checkpoint3a-planning-guardrails"
    allowed = [
        "docs/governance/preflights/issue-249.json",
        "docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "Makefile",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_249_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-249-checkpoint3a-planning-guardrails-typo"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-249.json",
            "docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-249.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
    ]


def test_issue_253_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-253-c3a-cp1-acceptance-api-e2e"
    allowed = [
        "docs/governance/preflights/issue-253.json",
        "docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_api_e2e.py",
    ]
    assert phase1.ISSUE_253_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_253_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-253-c3a-cp1-acceptance-api-e2e-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-253.json",
            "docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_api_e2e.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-253.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_api_e2e.py.",
    ]


def test_issue_257_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-257-c3a-cp2-output-correctness"
    allowed = [
        "docs/governance/preflights/issue-257.json",
        "docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_output_correctness.py",
    ]
    assert phase1.ISSUE_257_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_api_e2e.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_api_e2e.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_257_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-257-c3a-cp2-output-correctness-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-257.json",
            "docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_output_correctness.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-257.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_output_correctness.py.",
    ]


def test_issue_259_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-259-c3a-cp3-language-quality"
    allowed = [
        "docs/governance/preflights/issue-259.json",
        "docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_language_quality.py",
    ]
    assert phase1.ISSUE_259_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_output_correctness.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_output_correctness.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_259_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-259-c3a-cp3-language-quality-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-259.json",
            "docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_language_quality.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-259.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_language_quality.py.",
    ]


def test_issue_261_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-261-c3a-cp4-media-artifacts"
    allowed = [
        "docs/governance/preflights/issue-261.json",
        "docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_media_artifacts.py",
    ]
    assert phase1.ISSUE_261_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_language_quality.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_language_quality.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_261_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-261-c3a-cp4-media-artifacts-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-261.json",
            "docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_media_artifacts.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-261.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_media_artifacts.py.",
    ]


def test_issue_263_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-263-c3a-cp5-access-quota-retention"
    allowed = [
        "docs/governance/preflights/issue-263.json",
        "docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_access_quota_retention.py",
    ]
    assert phase1.ISSUE_263_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_media_artifacts.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_media_artifacts.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_263_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-263-c3a-cp5-access-quota-retention-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-263.json",
            "docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_access_quota_retention.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-263.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_access_quota_retention.py.",
    ]


def test_issue_265_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-265-c3a-cp6-security-observability"
    allowed = [
        "docs/governance/preflights/issue-265.json",
        "docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_security_observability.py",
    ]
    assert phase1.ISSUE_265_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_access_quota_retention.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_access_quota_retention.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_265_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-265-c3a-cp6-security-observability-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-265.json",
            "docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_security_observability.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-265.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_security_observability.py.",
    ]


def test_issue_255_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-255-post-pr-254-status-reconcile"
    allowed = [
        "docs/governance/preflights/issue-255.json",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert phase1.ISSUE_255_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "docs/TRACEABILITY.md",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/TRACEABILITY.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
    ]


def test_issue_255_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-255-post-pr-254-status-reconcile-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-255.json",
            "docs/STATUS.md",
            "scripts/quality/check_phase1_closure_docs.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-255.json.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_phase1_closure_docs.py.",
    ]


def test_issue_253_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue253_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://fastapi.tiangolo.com/tutorial/testing/",
        "C3A-CP1-HARNESS-001",
        "C3A-CP1-FALSEPASS-001",
        "C3A-CP1-FM-005",
        "tests/acceptance/test_checkpoint3_api_e2e.py::test_checkpoint3_api_e2e_executes_local_product_path",
        "API-visible idempotent replay",
        "ops/status",
        "shell=False",
        "sub-agent",
        "synthetic approved non-NarraTwin project knowledge",
        "no browser/frontend scope is touched",
        "Stop and open a new issue",
    ),
)
def test_issue_253_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue253_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_253_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue253_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP1 preflight artifact: docs/reviews/ISSUE_253_C3A_CP1_PREFLIGHT.md"
    ]


def test_issue_257_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue257_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://fastapi.tiangolo.com/tutorial/testing/",
        "C3A-CP2-HARNESS-001",
        "C3A-CP2-FM-002",
        "tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_executes_runtime_api_evidence_path",
        "API-visible idempotent replay",
        "acceptedScriptText",
        "claimSupports",
        "contextRefs",
        "evidenceSnapshot",
        "timeout=120",
        "Cross-model review is skipped in this autonomous execution context",
        "no browser/frontend scope is touched",
        "Stop and open a new issue",
    ),
)
def test_issue_257_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue257_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_257_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue257_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP2 preflight artifact: docs/reviews/ISSUE_257_C3A_CP2_PREFLIGHT.md"
    ]


def test_issue_259_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue259_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://docs.python.org/3/library/subprocess.html#subprocess.run",
        "C3A-CP3-HARNESS-001",
        "C3A-CP3-FM-002",
        "tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_executes_runtime_api_output_path",
        "tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_style_text_without_runtime_api_evidence",
        "coherent walkthrough structure",
        "audience-appropriate tone",
        "malformed citation placement",
        "API-visible idempotent replay",
        "acceptedScriptText",
        "claimSupports",
        "contextRefs",
        "evidenceSnapshot",
        "timeout=120",
        "Cross-model review is skipped in this autonomous execution context",
        "no browser/frontend scope is touched",
        "Stop and open a new issue",
    ),
)
def test_issue_259_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue259_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_259_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue259_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP3 preflight artifact: docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md"
    ]


def test_issue_261_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue261_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://docs.python.org/3/library/base64.html",
        "C3A-CP4-HARNESS-001",
        "C3A-CP4-FM-002",
        "tests/acceptance/test_checkpoint3_media_artifacts.py::test_checkpoint3_media_artifacts_executes_runtime_api_artifact_path",
        "tests/acceptance/test_checkpoint3_media_artifacts.py::test_checkpoint3_media_artifacts_rejects_artifact_shape_without_source_binding",
        "artifact-shape-only",
        "sourceEvaluationChecksum",
        "contentBase64",
        "translatedScript",
        "voiceManifest",
        "renderManifest",
        "videoExportPlaceholder",
        "local/mock provider posture",
        "no real media binary overclaim",
        "Cross-model review is skipped in this autonomous execution context",
        "no browser/frontend scope is touched",
        "Stop and open a new issue",
    ),
)
def test_issue_261_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue261_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_261_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue261_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP4 preflight artifact: docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md"
    ]


def test_issue_263_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue263_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://fastapi.tiangolo.com/tutorial/testing/",
        "C3A-CP5-HARNESS-001",
        "C3A-CP5-FM-002",
        "tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path",
        "tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_rejects_static_or_status_only_evidence",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_access_quota_retention_evidence_fields",
        "cross-project replay",
        "mismatched source-run replay",
        "idempotency replay cannot bypass",
        "PROJECT_DOCUMENT_LIMIT_EXCEEDED",
        "UPLOAD_TOO_LARGE",
        "RETENTION_DELETED",
        "tombstone",
        "quotaState",
        "ops/status",
        "Cross-model review is skipped in this autonomous execution context",
        "no browser/frontend scope is touched",
        "Stop and open a new issue",
    ),
)
def test_issue_263_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue263_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_263_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue263_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP5 preflight artifact: docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md"
    ]


def test_issue_265_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue265_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "C3A-CP6-HARNESS-001",
        "C3A-CP6-FM-002",
        "tests/acceptance/test_checkpoint3_security_observability.py::test_checkpoint3_security_observability_executes_runtime_api_boundary_path",
        "tests/acceptance/test_checkpoint3_security_observability.py::test_checkpoint3_security_observability_rejects_static_or_unbound_evidence",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_security_observability_evidence_fields",
        "runtime API-visible security controls",
        "privacy/redaction",
        "observability metadata",
        "bounded failure evidence",
        "docs/prose/static-snapshot",
        "canned success",
        "runtime nonce",
        "source/run binding",
        "cross-project replay",
        "idempotency replay",
        "prompt-injection",
        "SECRET_LIKE_CONTENT",
        "PROMPT_INJECTION_DETECTED",
        "UNSAFE_DOCUMENT_CONTENT",
        "UNSUPPORTED_PROJECT_FACT",
        "local/mock provider",
        "no hosted deployment",
        "no provider setup",
        "no cloned identity",
        "no production-readiness claim",
        "Issue #249 remains open",
        "Cross-model review is skipped in this autonomous execution context",
        "Stop and open a new issue",
    ),
)
def test_issue_265_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue265_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_265_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue265_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP6 preflight artifact: docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md"
    ]


def test_issue_249_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue249_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "C3A-LANG-HI-001",
        "Hindi output must contain Devanagari",
        "tests/acceptance/test_checkpoint3_output_correctness.py",
        "real-browser E2E with no success-path interception",
        "server-bound tombstone",
        "raw uploads, prompts, scripts, transcripts, media bytes, URLs, invite secrets, cookies, tokens, provider keys, provider payloads, and private identifiers",
        "no cloned voice",
        "manual adversarial fallback",
    ),
)
def test_issue_249_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue249_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_249_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue249_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A preflight artifact: docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md"
    ]


def test_real_media_demo_plan_requires_checkpoint3a_markers(monkeypatch: Any) -> None:
    plan_text = Path("docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md").read_text(encoding="utf-8")

    assert run_real_media_demo_plan_check(
        monkeypatch,
        plan_text=remove_normalized_marker(
            plan_text,
            "Checkpoint 3A: Non-Cloned Product-Faithful Controlled Demo",
        ),
    )


def test_issue_243_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_243_DEMO_CHECKPOINT1_PR5_HOSTED_DEMO_PREFLIGHT.md").read_text(
        encoding="utf-8"
    )

    assert run_issue243_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://fastapi.tiangolo.com/tutorial/handling-errors/",
        "https://pydantic.dev/docs/validation/2.0/usage/model_config/",
        "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "https://nextjs.org/docs/pages/guides/environment-variables",
        "https://vercel.com/docs/plans/hobby",
        "https://docs.railway.com/pricing/plans",
        "https://render.com/docs/free",
        "HostedDemoAccessConfig",
        "HostedDemoAccessRequest",
        "HostedDemoDecision",
        "PR5-ACCESS-001",
        "PR5-QUOTA-001",
        "PR5-RETENTION-001",
        "PR5-VALIDATE-001",
        "PR5-OBS-001",
        "pending deletion is never recorded as deleted proof",
        "raw prompts, scripts, uploads, provider payloads, URLs, invite secrets, cookies, tokens, session secrets, provider keys, or media bytes",
        "test_hosted_demo.py",
        "test_hosted_demo_api.py",
    ),
)
def test_issue_243_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_243_DEMO_CHECKPOINT1_PR5_HOSTED_DEMO_PREFLIGHT.md").read_text(
        encoding="utf-8"
    )

    assert run_issue243_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_241_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_241_DEMO_CHECKPOINT1_PR4_AVATAR_VIDEO_PREFLIGHT.md").read_text(
        encoding="utf-8"
    )

    assert run_issue241_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://developers.heygen.com/docs/quick-start",
        "https://docs.tavus.io/api-reference/video-request/delete-video",
        "https://www.d-id.com/eula/",
        "No real provider call is approved by PR4",
        "D-ID-approved synthetic-marking policy/version",
        "provider asset provenance enum",
        "prompt-with-existing-avatar references",
        "typed input schema",
        "provider create succeeds remotely, local call times out",
        "pending/unknown quota hold",
        "resolved A/AAAA records",
        "169.254.169.254",
        "provider-specific deletion/retention source facts",
        "structured log event names",
        "bounded-cardinality",
        "test_stage7_avatar_video_provider.py",
    ),
)
def test_issue_241_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_241_DEMO_CHECKPOINT1_PR4_AVATAR_VIDEO_PREFLIGHT.md").read_text(
        encoding="utf-8"
    )

    assert run_issue241_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_237_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-237-demo-checkpoint1-pr3-real-tts-typo"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-237.json",
            "docs/STAGE_ISSUE_PLAN.md",
            "backend/app/stage6.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-237.json.",
        f"Phase 1 Closure branch {branch} may not change docs/STAGE_ISSUE_PLAN.md.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
    ]


def test_phf020a_valid_policy_has_no_findings() -> None:
    assert phase1.phf020a_policy_findings(PHF020A_VALID_POLICY) == []


def test_status_state_v1_contract_rejects_missing_table() -> None:
    status_text = Path("docs/STATUS.md").read_text(encoding="utf-8")
    mutated = re.sub(
        r"\n## StatusStateV1\n.*?(?=\n## )",
        "\n",
        status_text,
        count=1,
        flags=re.S,
    )

    assert "SSV1.STRUCTURE.MISSING" in phase1.status_state_v1_findings(mutated)


def test_status_state_v1_contract_rejects_status_overclaim() -> None:
    status_text = Path("docs/STATUS.md").read_text(encoding="utf-8")
    next_action = "| SSV1-NEXT | " + " | ".join(phase1.STATUS_STATE_V1_ROWS["SSV1-NEXT"]) + " |"
    expected = (
        "| SSV1-ISSUE155 | product-mode-controller | #155 | closed | closed | "
        "Issue #155 is closed for the controlled local/mock Product Mode 1 checkpoint after issue #213 "
        "and PR #214 completed Checkpoint A through Checkpoint B with latest-head human approval and evidence. |"
    )
    assert next_action in status_text
    assert expected in status_text
    mutated = status_text.replace(
        expected,
        expected.replace("| closed | closed |", "| open | open |"),
        1,
    )

    assert phase1.status_state_v1_findings(status_text) == []
    assert "SSV1.STATE.INVALID" in phase1.status_state_v1_findings(mutated)


def test_post_pr250_status_reconciliation_is_recorded() -> None:
    status_text = Path("docs/STATUS.md").read_text(encoding="utf-8")
    normalized_status = re.sub(r"\s+", " ", status_text)

    for marker in (
        "PR `#250`",
        "`41b262fa2431f55cd1c813eab4071968c1c96ba0`",
        "Issue `#249` remains open as the public Checkpoint 3 tracker",
        "post-PR-250 status reconciliation tracked by issue `#251` and PR `#252`",
        "Issue `#253` is closed after PR `#254` merged the first Checkpoint 3A child implementation checkpoint",
        "Issue `#257` is closed after PR `#258` merged the second Checkpoint 3A child implementation checkpoint",
        "Issue `#259` is closed after PR `#260` merged the third Checkpoint 3A child implementation checkpoint",
        "Issue `#261` is closed after PR `#262` merged the fourth Checkpoint 3A child implementation checkpoint",
        "Issue `#263` is closed after PR `#264` merged the fifth Checkpoint 3A child implementation checkpoint",
        "Issue `#265` is satisfied by this PR when merged as the sixth Checkpoint 3A child implementation checkpoint",
        "checkpoint3a-cp6-security-observability-satisfied-by-this-pr",
        "`#254` | Merged | 2026-07-22",
        "`#258` | Merged | 2026-07-22",
        "`#260` | Merged | 2026-07-22",
        "`#262` | Merged | 2026-07-22",
        "`#264` | Merged | 2026-07-23",
        "`58e6ac473bb2cbcd5e99a64007a1cc862117217c`",
        "`de0cdb0c5337a980e478cb3e6b42d2b031909f31`",
        "post-merge main quality workflow run `29925008358` passing",
        "post-merge main quality workflow run `29937721472` passing",
        "This state does not complete Checkpoint 3A",
        "remaining planned probes",
    ):
        assert marker in normalized_status
    assert "C3A-CP1 PR | Pending" not in normalized_status
    assert "Issue `#259` is satisfied by this PR when merged" not in normalized_status


def test_status_state_v1_contract_rejects_duplicate_authority_section() -> None:
    status_text = Path("docs/STATUS.md").read_text(encoding="utf-8")
    duplicate = (
        "\n## StatusStateV1\n\n"
        "| ID | State kind | Owner | Expected status | Current status | Contract |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| SSV1-ISSUE155 | product-mode-controller | #155 | closed | closed | Contradictory duplicate authority. |\n"
    )

    assert "SSV1.STRUCTURE.DUPLICATE" in phase1.status_state_v1_findings(status_text + duplicate)


@pytest.mark.parametrize(
    ("name", "text", "expected"),
    (
        (
            "ignored-prose-with-dashes",
            PHF020A_VALID_POLICY + "\n\nExplanatory successor---issue prose.\n",
            [],
        ),
        (
            "missing-delimiter",
            PHF020A_VALID_POLICY.replace("|---|---|---|---|", "| ID | Table | Parent heading | Authority |", 1),
            ["PHF020A.TABLE.DELIMITER_MISSING"],
        ),
        (
            "wrong-width-delimiter",
            PHF020A_VALID_POLICY.replace("|---|---|---|---|", "|---|---|---|", 1),
            ["PHF020A.TABLE.DELIMITER_WIDTH"],
        ),
        (
            "wrong-parent-container",
            PHF020A_VALID_POLICY.replace("## Product Mode Policy Authority", "## Relocated Policy"),
            ["PHF020A.STRUCTURE.MISSING_PARENT"],
        ),
        (
            "permissive-enum",
            PHF020A_VALID_POLICY.replace("| PM-2 | product-mode | #20 |", "| PM-3 | product-mode | #20 |"),
            ["PHF020A.ENUM.UNKNOWN_TAXONOMY"],
        ),
        (
            "graph-node-only",
            PHF020A_VALID_POLICY.replace("| PM-GATE-20 | PM-1 | PM-2 | PM-GATE-30 |", "| PM-GATE-20 | PM-1 | PM-2 | none |"),
            ["PHF020A.GRAPH.EDGE_INVALID"],
        ),
        (
            "graph-prohibits-weakened",
            PHF020A_VALID_POLICY.replace("Product Mode 2", "none", 1),
            ["PHF020A.GRAPH.PROHIBITS_INVALID"],
        ),
        (
            "taxonomy-definition-weakened",
            PHF020A_VALID_POLICY.replace(
                "Future interactive Q&A after Mode 1 Checkpoint B and reset",
                "Immediate Product Mode 2 start",
            ),
            ["PHF020A.TAXONOMY.DEFINITION"],
        ),
        (
            "media-mandatory-contradiction",
            PHF020A_VALID_POLICY.replace(
                "Avatar video is not mandatory for PM-GATE-20",
                "Avatar video is not mandatory for PM-GATE-20 and mandatory for PM-GATE-20",
            ),
            ["PHF020A.MEDIA.MANDATORY"],
        ),
        (
            "duty-owner-weakened",
            PHF020A_VALID_POLICY.replace("| DUP-04 | #184 |", "| DUP-04 | #8 |"),
            ["PHF020A.DUPLICATE.DUTY_INVALID"],
        ),
        (
            "issue8-transfer-weakened",
            PHF020A_VALID_POLICY.replace("no runtime authorization", "runtime authorization"),
            ["PHF020A.ACCEPTANCE.ROW_INVALID"],
        ),
        (
            "duplicate-authoritative-subsection",
            PHF020A_VALID_POLICY.replace(
                "### Cross-Mode Gate Graph",
                "### Product Mode Taxonomy\n\n| ID | Kind | Owner issue | Definition |\n|---|---|---|---|\n| PM-2 | product-mode | #155 | contradictory duplicate |\n\n### Cross-Mode Gate Graph",
            ),
            ["PHF020A.DUPLICATE.TABLE"],
        ),
        (
            "duplicate-media-row",
            PHF020A_VALID_POLICY.replace(
                "| #18 | optional-branch | PM-GATE-10 | TTS audio is not mandatory for PM-GATE-20 |\n",
                "| #18 | optional-branch | PM-GATE-10 | TTS audio is not mandatory for PM-GATE-20 |\n| #18 | optional-branch | PM-GATE-10 | TTS audio is not mandatory for PM-GATE-20 |\n",
            ),
            ["PHF020A.DUPLICATE.MEDIA"],
        ),
        (
            "duplicate-duty-row",
            PHF020A_VALID_POLICY.replace(
                "| DUP-04 | #184 | Replace prose scanning with structure | PHF020A tests |\n",
                "| DUP-04 | #184 | Replace prose scanning with structure | PHF020A tests |\n| DUP-04 | #184 | Replace prose scanning with structure | PHF020A tests |\n",
            ),
            ["PHF020A.DUPLICATE.DUTY"],
        ),
        (
            "duplicate-acceptance-row",
            PHF020A_VALID_POLICY.replace(
                "| ISSUE8-06 | #8 | no runtime authorization | PM-GATE prohibitions |\n",
                "| ISSUE8-06 | #8 | no runtime authorization | PM-GATE prohibitions |\n| ISSUE8-06 | #8 | no runtime authorization | PM-GATE prohibitions |\n",
            ),
            ["PHF020A.DUPLICATE.ACCEPTANCE"],
        ),
        (
            "duplicate-activation-row",
            PHF020A_VALID_POLICY.replace(
                "| PM-MODE-001 | PM-1 | PM-GATE-10 | active-local-checkpoint |",
                "| PM-MODE-001 | PM-1 | PM-GATE-10 | active-local-checkpoint |\n| PM-MODE-001 | PM-1 | PM-GATE-10 | active-local-checkpoint |",
            ),
            ["PHF020A.DUPLICATE.ACTIVATION"],
        ),
        (
            "global-marker-only",
            "# Phase Plan\n\nProduct Mode Policy Authority marker only.\nPM-GATE-00 PM-GATE-10 PM-GATE-20 PM-GATE-30\n",
            ["PHF020A.STRUCTURE.MISSING_PARENT"],
        ),
        (
            "global-search-satisfaction",
            PHF020A_VALID_POLICY.replace("## Product Mode Policy Authority", "## Relocated Policy")
            + "\n\n## Product Mode Policy Authority\n\nPM-GATE-00 PM-GATE-10 PM-GATE-20 PM-GATE-30\n",
            ["PHF020A.TABLE.MISSING"],
        ),
        (
            "fenced-code-authority",
            "# Phase Plan\n\n## Product Mode Policy Authority\n\n```md\n"
            + PHF020A_VALID_POLICY.split("## Product Mode Policy Authority", 1)[1].strip()
            + "\n```\n",
            ["PHF020A.TABLE.MISSING"],
        ),
        (
            "blockquote-authority",
            "# Phase Plan\n\n" + "\n".join("> " + line for line in PHF020A_VALID_POLICY.splitlines()[2:]),
            ["PHF020A.STRUCTURE.MISSING_PARENT"],
        ),
        (
            "comment-authority",
            "# Phase Plan\n\n<!--\n" + PHF020A_VALID_POLICY + "\n-->\n",
            ["PHF020A.STRUCTURE.MISSING_PARENT"],
        ),
        (
            "duplicate-parent-container",
            PHF020A_VALID_POLICY + "\n\n## Product Mode Policy Authority\n\nDuplicate.\n",
            ["PHF020A.DUPLICATE.PARENT"],
        ),
        (
            "mutable-current-state",
            PHF020A_VALID_POLICY + "\n\nCurrent module is CH-M1-01.\n",
            ["PHF020A.STATE.MUTABLE_CURRENT_STATE"],
        ),
        (
            "forbidden-scope-reference",
            PHF020A_VALID_POLICY.replace("PHF020A tests", "backend/app/main.py"),
            ["PHF020A.SCOPE.FORBIDDEN_REFERENCE"],
        ),
    ),
)
def test_phf020a_policy_single_faults_return_exact_vectors(name: str, text: str, expected: list[str]) -> None:
    del name
    assert phase1.phf020a_policy_findings(PHF020A_VALID_POLICY) == []
    assert phase1.phf020a_policy_findings(text) == expected


@pytest.mark.parametrize(
    ("limit_name", "text", "expected"),
    (
        ("bytes", "# Phase Plan\n" + ("x" * (256 * 1024 + 1)), ["PHF020A.LIMIT.BYTES"]),
        ("lines", "\n".join("# h" for _ in range(10_001)), ["PHF020A.LIMIT.LINES"]),
        ("headings", "\n".join(f"## h{i}" for i in range(257)), ["PHF020A.LIMIT.HEADINGS"]),
        ("cell", PHF020A_VALID_POLICY.replace("structured |", ("x" * 2049) + " |", 1), ["PHF020A.LIMIT.CELL"]),
        ("control", PHF020A_VALID_POLICY + "\x00", ["PHF020A.LIMIT.CONTROL"]),
        ("del-control", PHF020A_VALID_POLICY + "\x7f", ["PHF020A.LIMIT.CONTROL"]),
        ("c1-control", PHF020A_VALID_POLICY + "\x80", ["PHF020A.LIMIT.CONTROL"]),
        ("unicode", PHF020A_VALID_POLICY + "\ud800", ["PHF020A.LIMIT.UNICODE"]),
        (
            "blockquoted-tables",
            PHF020A_VALID_POLICY + "\n\n" + "\n".join("> | A |\n> |---|\n> | B |" for _ in range(65)),
            ["PHF020A.LIMIT.TABLES"],
        ),
    ),
)
def test_phf020a_resource_limits_fail_closed(limit_name: str, text: str, expected: list[str]) -> None:
    del limit_name
    assert phase1.phf020a_policy_findings(text) == expected


def test_phf020a_generated_suite_contract_is_exact() -> None:
    cases = phf020a_generated_cases()
    assert len(cases) == 500
    assert {case["seed"] for case in cases} == set(PHF020A_SEEDS)
    assert len({case["id"] for case in cases}) == 500
    invalid_cases = [case for case in cases if not case["valid"]]
    assert len({case["mutation_id"] for case in invalid_cases}) == 250
    assert len({case["mutation_descriptor"] for case in invalid_cases}) == 250
    assert len({case["text"] for case in invalid_cases}) == 250
    assert all(case["mutation_descriptor"] in case["text"] for case in invalid_cases)
    assert all(case["mutation_count"] == 1 for case in invalid_cases)
    for seed in PHF020A_SEEDS:
        seed_cases = [case for case in cases if case["seed"] == seed]
        assert len(seed_cases) == 50
        assert sum(1 for case in seed_cases if case["valid"]) == 25
        assert sum(1 for case in seed_cases if not case["valid"]) == 25
        seed_invalid_totals = {
            family: sum(1 for case in seed_cases if case["family"] == family)
            for family in PHF020A_INVALID_TOTALS
        }
        assert {
            family: count for family, count in seed_invalid_totals.items() if count
        } == PHF020A_SEED_INVALID_TOTALS[seed]
    family_totals = {
        family: sum(1 for case in cases if case["family"] == family)
        for family in PHF020A_INVALID_TOTALS
    }
    assert family_totals == PHF020A_INVALID_TOTALS
    for case in cases:
        assert phase1.phf020a_policy_findings(PHF020A_VALID_POLICY) == []
        actual = phase1.phf020a_policy_findings(case["text"])
        assert actual == case["expected"], case["id"]
        for code in actual:
            family = ".".join(code.split(".")[:2])
            assert family in PHF020A_ALLOWED_FINDING_FAMILIES, case["id"]
            assert family in PHF020A_FAMILY_CODE_PREFIXES[case["family"]], case["id"]


def run_issue141_platform_contract_check(
    monkeypatch: Any, *, read_overrides: dict[str, str] | None = None
) -> list[str]:
    if read_overrides:
        monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_issue141_platform_ownership_contract(failures)
    return failures


def issue39_plan_with_closed_row_and_record(
    plan_text: str,
    *,
    matrix_id: str = "DUR-ACID-001",
    row_status_search: str,
    row_status_replacement: str,
    child_reference: str = (
        "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
        "https://github.com/imrohitagrawal/narratwin-ai/pull/102"
    ),
    artifact_reference: str = "docs/ADR/0013-production-durability.md",
    evidence: str = (
        "tests/unit/test_phase1_closure_docs.py::test_issue39_closure_plan_accepts_current_matrix "
        "https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123456789"
    ),
    owner: str = "Storage owner",
    reviewer: str = "Architecture reviewer",
    residual_risk: str = "Accepted with production row evidence",
    timestamp: str = "merge commit abc123",
    satisfies: str = "production-grade evidence satisfies the row",
) -> str:
    plan_text = replace_text(plan_text, row_status_search, row_status_replacement)
    record = (
        f"| `{matrix_id}` | {child_reference} | {artifact_reference} | {evidence} | "
        f"{owner} | {reviewer} | {residual_risk} | {timestamp} | {satisfies} |\n"
    )
    return plan_text.replace(
        "## Row Closure Records\n\n| Matrix ID | Child issue / PR | Artifact reference | Validation or human evidence | Owner | Reviewer | Residual-risk decision | Timestamp / merge commit | Satisfies row because |\n|---|---|---|---|---|---|---|---|---|\n",
        "## Row Closure Records\n\n| Matrix ID | Child issue / PR | Artifact reference | Validation or human evidence | Owner | Reviewer | Residual-risk decision | Timestamp / merge commit | Satisfies row because |\n|---|---|---|---|---|---|---|---|---|\n"
        + record,
        1,
    )


def test_process_only_phase1_branch_allows_governance_guardrail_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-55-phf-006-scope-gate",
        files=[
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md",
            "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
            "scripts/guardrails_check.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue181_process_branch_allows_only_lighthouse_maintenance_files(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-181-lighthouse-browser-selection"

    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=sorted(phase1.ISSUE_181_ALLOWED_CHANGED_FILES),
    ) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["frontend/src/app/page.tsx", "frontend/src/app/page.module.css"],
    ) == [
        "Phase 1 Closure branch phase-1-closure-process-181-lighthouse-browser-selection "
        "may not change frontend/src/app/page.tsx.",
        "Phase 1 Closure branch phase-1-closure-process-181-lighthouse-browser-selection "
        "may not change frontend/src/app/page.module.css.",
    ]


def test_process_only_phase1_branch_allows_matching_governance_preflight(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-155-post-pr-c-reconciliation"

    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-155.json",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    ) == []


def test_issue223_loop_breaker_allows_only_terminal_policy_files(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-223-post-pr-222-status-reconciliation"

    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=sorted(phase1.ISSUE_223_ALLOWED_CHANGED_FILES),
    ) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["frontend/src/app/page.tsx", "backend/app/main.py"],
    ) == [
        "Phase 1 Closure branch phase-1-closure-process-223-post-pr-222-status-reconciliation "
        "may not change frontend/src/app/page.tsx.",
        "Phase 1 Closure branch phase-1-closure-process-223-post-pr-222-status-reconciliation "
        "may not change backend/app/main.py.",
    ]


def test_process_only_phase1_branch_rejects_mismatched_governance_preflight(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-155-post-pr-c-reconciliation"

    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["docs/governance/preflights/issue-156.json"],
    ) == [
        "Phase 1 Closure branch phase-1-closure-process-155-post-pr-c-reconciliation "
        "may not change docs/governance/preflights/issue-156.json."
    ]


def test_skill_governance_process_branch_allows_only_governance_files(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-164-phf-019-skill-evidence-governance"
    failures = run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "AGENTS.md",
            "docs/SKILL_EXECUTION_PLAN.md",
            "docs/SKILL_SELECTION_AND_EVIDENCE.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=["backend/app/main.py"],
    ) == [
        "Phase 1 Closure branch phase-1-closure-process-164-phf-019-skill-evidence-governance "
        "may not change backend/app/main.py."
    ]


@pytest.mark.parametrize(
    "skill_doc",
    [
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/SKILL_SELECTION_AND_EVIDENCE.md",
    ],
)
def test_skill_governance_docs_are_confined_to_process_branches(
    monkeypatch: Any,
    skill_doc: str,
) -> None:
    branch = "phase-1-closure-138-click-security-remediation"

    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[skill_doc],
    ) == [
        "Phase 1 Closure branch phase-1-closure-138-click-security-remediation may not change "
        f"{skill_doc}."
    ]


def test_process_docs_reject_skill_selection_contract_without_activation_trigger(
    monkeypatch: Any,
) -> None:
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=["docs/SKILL_SELECTION_AND_EVIDENCE.md"],
        read_overrides={
            "docs/SKILL_SELECTION_AND_EVIDENCE.md": "# Skill Selection And Evidence\n",
        },
    )

    assert (
        "docs/SKILL_SELECTION_AND_EVIDENCE.md missing required heading: "
        "Verification-Skill Activation Trigger"
    ) in failures


@pytest.mark.parametrize(
    ("search", "replacement", "expected_failure"),
    [
        (
            "skills govern the method; evidence proves the claim",
            "skills are evidence",
            "skills govern the method; evidence proves the claim",
        ),
        (
            "FIRED authorizes a capability and trust evaluation only.",
            "FIRED authorizes installation.",
            "fired authorizes a capability and trust evaluation only",
        ),
        (
            "| Initial — 2026-07-15 | 0 | 0 | ARMED |",
            "| Initial — 2026-07-15 | 1 | 0 | ARMED |",
            "must keep the initial trigger baseline at 0 eligible PRs",
        ),
        (
            "baseline, and at least 2 qualifying",
            "baseline, or at least 2 qualifying",
            "trigger must require both thresholds",
        ),
        (
            "The following do not count:",
            "The following count toward the trigger:",
            "trigger exclusions must remain exclusions",
        ),
        (
            "| Mocked browser workflow | Does the assembled UI handle expected response shapes? | TDD plus frontend testing | Playwright with route interception | Explicitly labelled mocked browser smoke | Calling the result real-stack E2E |",
            "| Mocked browser workflow | Does the assembled UI handle expected response shapes? | TDD plus frontend testing | Playwright with route interception | Real-stack E2E evidence | Nothing |",
            "mocked browser workflow must not claim real-stack E2E evidence",
        ),
        (
            "- be discovered after merge;",
            "- be discovered after an explicit pre-merge completion claim;",
            "qualifying escapes must be discovered after merge",
        ),
        (
            "deferred real media",
            "future media",
            "deferred real media",
        ),
        (
            "cosmetic preferences outside acceptance criteria",
            "cosmetic preferences",
            "cosmetic preferences outside acceptance criteria",
        ),
    ],
)
def test_process_docs_reject_skill_selection_contract_mutations(
    monkeypatch: Any,
    search: str,
    replacement: str,
    expected_failure: str,
) -> None:
    skill_selection = phase1.read("docs/SKILL_SELECTION_AND_EVIDENCE.md")
    assert search in skill_selection
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=["docs/SKILL_SELECTION_AND_EVIDENCE.md"],
        read_overrides={
            "docs/SKILL_SELECTION_AND_EVIDENCE.md": skill_selection.replace(
                search,
                replacement,
                1,
            ),
        },
    )

    assert any(expected_failure in failure for failure in failures)


@pytest.mark.parametrize(
    ("contradiction", "expected_failure"),
    [
        (
            "When FIRED persists, install the skill automatically.",
            "forbidden skill-selection contradiction",
        ),
        (
            "When FIRED persists, automatically install the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "When FIRED persists, the skill is installed automatically.",
            "forbidden skill-selection contradiction",
        ),
        (
            "When FIRED persists, the agent installs the skill automatically.",
            "forbidden skill-selection contradiction",
        ),
        (
            "FIRED enables auto-install of the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "At FIRED, activation is automatic.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Install the skill automatically; do not skip audit logging.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Activation is automatic, and never bypass the audit log.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Auto-install the skill whenever FIRED persists.",
            "forbidden skill-selection contradiction",
        ),
        (
            "The pipeline will auto-activate the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Installation happens, automatically, at FIRED.",
            "forbidden skill-selection contradiction",
        ),
        (
            "The skill is activated, automatically and silently.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Installation happens, automatically, at FIRED, and does not skip audit logging.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Automatically, the skill is installed, and never bypasses audit logging.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Silently and automatically, install the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Do not skip audit logging, but silently and automatically, install the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Do not, however, skip audit logging, but silently and automatically, install the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Whether or not, audited, silently and automatically, install the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Set the flag to not, then silently and automatically, install the skill.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Present on disk is sufficient for approval and operation.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Present on disk counts as approval.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Disk presence equals repository approval.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Disk presence counts as approval, not as execution consent.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Disk presence, in effect, counts as approval.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Disk presence, in effect, counts as approval, not as execution consent.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Composite skill quality score = weighted mean of all measures.",
            "forbidden skill-selection contradiction",
        ),
        (
            "Composite skill quality score is the weighted mean of all measures.",
            "forbidden skill-selection contradiction",
        ),
    ],
)
def test_process_docs_reject_additive_skill_selection_contradictions(
    monkeypatch: Any,
    contradiction: str,
    expected_failure: str,
) -> None:
    skill_selection = phase1.read("docs/SKILL_SELECTION_AND_EVIDENCE.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=["docs/SKILL_SELECTION_AND_EVIDENCE.md"],
        read_overrides={
            "docs/SKILL_SELECTION_AND_EVIDENCE.md": f"{skill_selection}\n{contradiction}\n",
        },
    )

    assert any(expected_failure in failure for failure in failures)


@pytest.mark.parametrize(
    "negated_statement",
    [
        "Do not install the skill automatically.",
        "Never activate the skill automatically.",
        "The skill will not be installed automatically.",
        "Activation is not automatic.",
        "Present on disk does not count as approval.",
        "Disk presence does not equal repository approval.",
        "Do not auto-install the skill.",
        "The pipeline will never auto-activate the skill.",
        "Auto-install is not permitted.",
        "Installation happens, not automatically, at FIRED.",
        "The skill is activated, not automatically but manually.",
        "Automatically, installation is not permitted.",
        "Do not, automatically, install the skill.",
        "Never, automatically, activate the skill.",
        "Do not, silently and automatically, install the skill.",
        "Do not, quietly but automatically, activate the skill.",
        "Never, silently and automatically, install the skill.",
        "The pipeline will not, quietly but automatically, activate the skill.",
        "Do not, silently, and automatically, install the skill.",
        "Never, under policy, silently and automatically, activate the skill.",
        "Disk presence, in effect, does not count as approval.",
        "There is no composite skill quality score: use raw measures.",
    ],
)
def test_process_docs_allow_negated_skill_selection_contradictions(
    monkeypatch: Any,
    negated_statement: str,
) -> None:
    skill_selection = phase1.read("docs/SKILL_SELECTION_AND_EVIDENCE.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=["docs/SKILL_SELECTION_AND_EVIDENCE.md"],
        read_overrides={
            "docs/SKILL_SELECTION_AND_EVIDENCE.md": f"{skill_selection}\n{negated_statement}\n",
        },
    )

    assert not any("forbidden skill-selection contradiction" in failure for failure in failures)


def test_process_docs_require_exact_skill_execution_selection_rule(monkeypatch: Any) -> None:
    skill_plan = phase1.read("docs/SKILL_EXECUTION_PLAN.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=["docs/SKILL_EXECUTION_PLAN.md"],
        read_overrides={
            "docs/SKILL_EXECUTION_PLAN.md": skill_plan.replace(
                "start from the claim and boundary, choose the smallest test that can disprove\n"
                "the claim, use a skill to govern the method, and record the resulting evidence\n"
                "or prevented unsafe action.",
                "Review the claim, available boundaries, and evidence.",
                1,
            ),
        },
    )

    assert any("missing exact selection rule" in failure for failure in failures)


def test_skill_selection_table_failure_names_the_owning_document(monkeypatch: Any) -> None:
    skill_selection = phase1.read("docs/SKILL_SELECTION_AND_EVIDENCE.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=["docs/SKILL_SELECTION_AND_EVIDENCE.md"],
        read_overrides={
            "docs/SKILL_SELECTION_AND_EVIDENCE.md": skill_selection.replace(
                "| Phase | Question being answered | Preferred skill/workflow | Test/tool or artifact | Required evidence | Do not use it for |",
                "| Phase | Question being answered | Preferred skill/workflow | Test/tool or artifact | Required evidence |",
                1,
            ),
        },
    )

    matching = [failure for failure in failures if "missing headers: Do not use it for" in failure]
    assert matching
    assert all(".github/pull_request_template.md" not in failure for failure in matching)


def test_current_skill_selection_and_evidence_contract_passes(monkeypatch: Any) -> None:
    assert run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-164-phf-019-skill-evidence-governance",
        changed=[
            "docs/SKILL_EXECUTION_PLAN.md",
            "docs/SKILL_SELECTION_AND_EVIDENCE.md",
        ],
    ) == []


def test_issue138_branch_allows_only_click_security_remediation_files(
    monkeypatch: Any,
) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-138-click-security-remediation",
        files=sorted(phase1.ISSUE_138_ALLOWED_CHANGED_FILES),
    )

    assert failures == []

    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-138-click-security-remediation",
        files=["backend/app/main.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-138-click-security-remediation "
        "may not change backend/app/main.py."
    ]


def test_issue141_branch_allows_only_durability_decision_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-141-durability-platform-ownership",
        files=sorted(phase1.ISSUE_141_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue141_branch_allowlist_is_an_independent_literal_contract() -> None:
    assert phase1.ISSUE_141_ALLOWED_CHANGED_FILES == {
        "docs/ADR/0008-postgresql-durability-schema-boundary.md",
        "docs/ADR/0011-context4-backup-restore-drill.md",
        "docs/ADR/0027-production-like-durability-platform-ownership.md",
        "docs/LAUNCH_LEVELS.md",
        "docs/RELEASE_READINESS_REVIEW.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THREAT_MODEL.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
        "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
        "docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md",
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }


def test_issue141_branch_rejects_runtime_or_infrastructure_changes(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-141-durability-platform-ownership",
        files=["backend/app/storage/postgres_state.py", "infra/rds.tf"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-141-durability-platform-ownership may not change "
        "backend/app/storage/postgres_state.py.",
        "Phase 1 Closure branch phase-1-closure-141-durability-platform-ownership may not change "
        "infra/rds.tf.",
    ]


def test_issue72_process_branch_allows_closure_evidence_contract_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-72-closure-evidence-hardening",
        files=[
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md",
            "scripts/guardrails_check.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue72_process_branch_rejects_unrelated_review_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-72-closure-evidence-hardening",
        files=["docs/reviews/unrelated.md"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-process-72-closure-evidence-hardening may not change "
        "docs/reviews/unrelated.md."
    ]


def test_issue39_chunk_branch_requires_dependency_commit_ancestry(monkeypatch: Any) -> None:
    failures = run_branch_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-04-idempotency-semantics",
        ancestor_ok=False,
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-04-idempotency-semantics must contain dependency "
        "commits: b5992a599be06ea444ca66d3f088956eee8c70e6."
    ]


def test_issue39_chunk_branch_accepts_required_dependency_commit_ancestry(monkeypatch: Any) -> None:
    assert (
        run_branch_check(
            monkeypatch,
            branch="phase-1-closure-39-ch-05-lease-fencing",
            ancestor_ok=True,
        )
        == []
    )


@pytest.mark.parametrize(
    "branch",
    [
        "phase-1-closure-39-ch-04-idempotency-semantics",
        "phase-1-closure-39-ch-05-lease-fencing",
        "phase-1-closure-39-ch-06-committed-outbox",
    ],
)
def test_issue39_chunk_branches_check_exact_post_pr98_dependency_commit(
    monkeypatch: Any,
    branch: str,
) -> None:
    calls: list[list[str]] = []

    def fake_git_ok(args: list[str]) -> bool:
        calls.append(args)
        return True

    monkeypatch.setattr(phase1, "current_branch", lambda: branch)
    monkeypatch.setattr(phase1, "git_ok", fake_git_ok)

    failures: list[str] = []
    phase1.check_branch(failures)

    assert failures == []
    assert calls == [
        [
            "merge-base",
            "--is-ancestor",
            "b5992a599be06ea444ca66d3f088956eee8c70e6",
            "HEAD",
        ]
    ]


def test_issue39_ch07_branch_checks_exact_stage4_and_stage6_dependency_commits(
    monkeypatch: Any,
) -> None:
    calls: list[list[str]] = []

    def fake_git_ok(args: list[str]) -> bool:
        calls.append(args)
        return True

    monkeypatch.setattr(phase1, "current_branch", lambda: "phase-1-closure-39-ch-07-stage6-durable-replay")
    monkeypatch.setattr(phase1, "git_ok", fake_git_ok)

    failures: list[str] = []
    phase1.check_branch(failures)

    assert failures == []
    assert calls == [
        [
            "merge-base",
            "--is-ancestor",
            "6449786069dd38eeaa5a4a31f5ed73cbfc52d248",
            "HEAD",
        ],
        [
            "merge-base",
            "--is-ancestor",
            "947a96891fd84085b6fce433e604a8e249b25c23",
            "HEAD",
        ],
    ]


def test_issue39_ch09_branch_checks_exact_migration_storage_graph_dependency_commits(
    monkeypatch: Any,
) -> None:
    calls: list[list[str]] = []

    def fake_git_ok(args: list[str]) -> bool:
        calls.append(args)
        return True

    monkeypatch.setattr(
        phase1,
        "current_branch",
        lambda: "phase-1-closure-39-ch-09-technical-rollback-compatibility",
    )
    monkeypatch.setattr(phase1, "git_ok", fake_git_ok)

    failures: list[str] = []
    phase1.check_branch(failures)

    assert failures == []
    assert calls == [
        [
            "merge-base",
            "--is-ancestor",
            "824a07c2bd546648b96d9ab555b63a8f2415898e",
            "HEAD",
        ],
        [
            "merge-base",
            "--is-ancestor",
            "c47471d0c8218d59509cba936fe216b86c9ac1e9",
            "HEAD",
        ],
        [
            "merge-base",
            "--is-ancestor",
            "6449786069dd38eeaa5a4a31f5ed73cbfc52d248",
            "HEAD",
        ],
    ]


def test_issue39_ch09_branch_allows_only_rollback_compatibility_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-09-technical-rollback-compatibility",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/migrations.py",
            "docs/ADR/0022-ch09-technical-rollback-compatibility.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_storage_migrations.py",
        ],
    )

    assert failures == []


def test_issue39_ch10_branch_allows_only_metrics_contract_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-10-production-metrics-contract",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/file_state.py",
            "backend/app/storage/migrations.py",
            "backend/app/storage/ops_metrics.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0024-ch10-production-metrics-contract.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_ops_metrics.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_ch10_branch_rejects_alert_and_stage_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-10-production-metrics-contract",
        files=[
            "backend/app/stage4.py",
            "docs/ADR/0012-context5-metrics-slos-watch.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-10-production-metrics-contract may not change backend/app/stage4.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-10-production-metrics-contract may not change docs/ADR/0012-context5-metrics-slos-watch.md.",
    ]


def test_issue39_ch11_branch_checks_exact_ch10_dependency_commit(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fake_git_ok(args: list[str]) -> bool:
        calls.append(args)
        return True

    monkeypatch.setattr(phase1, "current_branch", lambda: "phase-1-closure-39-ch-11-slo-error-budget")
    monkeypatch.setattr(phase1, "git_ok", fake_git_ok)

    failures: list[str] = []
    phase1.check_branch(failures)

    assert failures == []
    assert calls == [
        [
            "merge-base",
            "--is-ancestor",
            "384c15ac67810d30096794500da1c90ce056dd54",
            "HEAD",
        ]
    ]


def test_issue39_ch11_branch_allows_only_slo_contract_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-11-slo-error-budget",
        files=[
            "docs/ADR/0025-ch11-slo-error-budget.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_ch11_branch_rejects_runtime_and_watch_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-11-slo-error-budget",
        files=[
            "backend/app/storage/ops_metrics.py",
            "docs/ADR/0012-context5-metrics-slos-watch.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-11-slo-error-budget may not change backend/app/storage/ops_metrics.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-11-slo-error-budget may not change docs/ADR/0012-context5-metrics-slos-watch.md.",
    ]


def test_issue39_ch14_branch_checks_issue125_merge_baseline(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fake_git_ok(args: list[str]) -> bool:
        calls.append(args)
        return True

    monkeypatch.setattr(phase1, "current_branch", lambda: "phase-1-closure-39-ch-14-restore-readiness-contract")
    monkeypatch.setattr(phase1, "git_ok", fake_git_ok)

    failures: list[str] = []
    phase1.check_branch(failures)

    assert failures == []
    assert calls == [
        [
            "merge-base",
            "--is-ancestor",
            "384c15ac67810d30096794500da1c90ce056dd54",
            "HEAD",
        ],
        [
            "merge-base",
            "--is-ancestor",
            "4b7594c8ae14c6a91dff9f0916447b0e6dec39a9",
            "HEAD",
        ],
        [
            "merge-base",
            "--is-ancestor",
            "f94776f6602d4c6feec2412b4764a7368049a080",
            "HEAD",
        ]
    ]


def test_issue39_ch14_branch_rejects_missing_issue125_merge_baseline(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "current_branch", lambda: "phase-1-closure-39-ch-14-restore-readiness-contract")
    monkeypatch.setattr(phase1, "git_ok", lambda args: False)

    failures: list[str] = []
    phase1.check_branch(failures)

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-14-restore-readiness-contract must contain dependency commits: 384c15ac67810d30096794500da1c90ce056dd54, 4b7594c8ae14c6a91dff9f0916447b0e6dec39a9, f94776f6602d4c6feec2412b4764a7368049a080."
    ]


def test_issue39_ch14_branch_allows_only_restore_readiness_contract_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-14-restore-readiness-contract",
        files=[
            "docs/ADR/0026-ch14-restore-readiness-contract.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md",
            "docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_ch14_branch_rejects_runtime_and_local_restore_impl_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-14-restore-readiness-contract",
        files=[
            "backend/app/storage/local_restore_drill.py",
            "docs/LOCAL_DEVELOPMENT.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-14-restore-readiness-contract may not change backend/app/storage/local_restore_drill.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-14-restore-readiness-contract may not change docs/LOCAL_DEVELOPMENT.md.",
    ]


def test_stacked_child_push_resolve_base_uses_stacked_base_ref(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fake_run_git(args: list[str]) -> str:
        calls.append(args)
        if args == ["rev-parse", "--verify", "origin/phase-1-closure-39-execution-strategy^{commit}"]:
            return "stacked-base"
        return ""

    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "phase-1-closure-39-ch-05-lease-fencing")
    monkeypatch.setenv("GITHUB_HEAD_REF", "phase-1-closure-39-ch-05-lease-fencing")
    monkeypatch.setenv("GITHUB_BASE_SHA", "previous-child-head")
    monkeypatch.setattr(phase1, "run_git", fake_run_git)

    assert phase1.resolve_base() == "origin/phase-1-closure-39-execution-strategy"
    assert ["rev-parse", "--verify", "previous-child-head^{commit}"] not in calls


def test_non_stacked_non_main_push_resolve_base_ignores_previous_branch_head(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fake_run_git(args: list[str]) -> str:
        calls.append(args)
        if args == ["merge-base", "origin/main", "HEAD"]:
            return "main-merge-base"
        return ""

    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "feature-branch")
    monkeypatch.setenv("GITHUB_HEAD_REF", "feature-branch")
    monkeypatch.setenv("GITHUB_BASE_SHA", "previous-feature-head")
    monkeypatch.setattr(phase1, "run_git", fake_run_git)

    assert phase1.resolve_base() == "main-merge-base"
    assert ["rev-parse", "--verify", "previous-feature-head^{commit}"] not in calls


def test_main_push_resolve_base_keeps_previous_commit(monkeypatch: Any) -> None:
    calls: list[list[str]] = []

    def fake_run_git(args: list[str]) -> str:
        calls.append(args)
        if args == ["rev-parse", "--verify", "previous-main^{commit}"]:
            return "previous-main"
        return ""

    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_BASE_SHA", "previous-main")
    monkeypatch.setattr(phase1, "run_git", fake_run_git)

    assert phase1.resolve_base() == "previous-main"
    assert calls == [["rev-parse", "--verify", "previous-main^{commit}"]]


def test_quality_gates_workflow_passes_event_name_to_stage_quality(monkeypatch: Any) -> None:
    workflow_text = phase1.read(".github/workflows/quality-gates.yml")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[".github/workflows/quality-gates.yml"],
        read_overrides={
            ".github/workflows/quality-gates.yml": workflow_text.replace(
                "          VECTOR_STORE: disabled\n"
                "          GITHUB_EVENT_NAME: ${{ github.event_name }}\n"
                    "          NARRATWIN_HEAD_REF: ${{ github.event.pull_request.head.ref || github.ref_name }}",
                "          VECTOR_STORE: disabled\n"
                    "          NARRATWIN_HEAD_REF: ${{ github.event.pull_request.head.ref || github.ref_name }}",
                1,
            ),
        },
    )

    assert ".github/workflows/quality-gates.yml must pass GITHUB_BASE_SHA to make quality" in failures


def test_issue39_closure_plan_accepts_current_matrix() -> None:
    failures: list[str] = []
    phase1.check_issue39_closure_plan(failures)

    assert failures == []


def test_issue39_closure_plan_rejects_missing_required_matrix_row(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `OPS-WATCH-001` | First-hour watch with follow-up checkpoints | Triage cadence and owner communication for the first 60 minutes, plus explicit 120/180-minute follow-up checkpoints | Release/Operations | Active watch log template, handoff rules, timeout actions, rollback escalation threshold | Open |\n",
            "",
        ),
    )

    assert "Issue #39 production closure plan missing matrix IDs: OPS-WATCH-001" in failures


def test_issue39_closure_plan_rejects_invalid_matrix_status(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |",
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Done |",
        ),
    )

    assert "Issue #39 matrix row DUR-ACID-001 status must be Open or Closed; got Done." in failures


def test_issue125_local_restore_contract_accepts_current_docs() -> None:
    failures: list[str] = []
    phase1.check_issue125_local_restore_contract(failures)

    assert failures == []


def test_issue125_local_restore_contract_rejects_missing_local_only_marker(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md": replace_text(
                    plan_text,
                    "Issue `#125` is an executable local-only evidence slice for the optional\n  file-backed Stage 4/6/7 state already present in the repo.",
                    "Issue `#125` is an evidence slice for Stage 4/6/7 state already present in the repo.",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue125_local_restore_contract(failures)

    assert (
        "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md missing issue #125 restore markers: "
        "Issue `#125` is an executable local-only evidence slice"
    ) in failures


def test_issue141_platform_ownership_contract_accepts_current_docs(monkeypatch: Any) -> None:
    assert run_issue141_platform_contract_check(monkeypatch) == []


@pytest.mark.parametrize(
    ("rel", "search", "replacement", "missing_marker"),
    [
        (
            "docs/LAUNCH_LEVELS.md",
            "Status: Merged documentation baseline through PR `#153` at `2fb5569`;",
            "Status: Proposed clarification for issue `#141` and draft PR `#153`.",
            "Status: Merged documentation baseline through PR `#153` at `2fb5569`",
        ),
        (
            "docs/STATUS.md",
            "Documentation baseline merged through PR `#153` at `2fb5569`.",
            "Documentation baseline remains proposed on the feature branch.",
            "Documentation baseline merged through PR `#153` at `2fb5569`.",
        ),
        (
            "docs/TRACEABILITY.md",
            "Merged at `2fb5569`; external approvals blocked",
            "Proposed on branch; external approvals blocked",
            "Merged at `2fb5569`; external approvals blocked",
        ),
    ],
)
def test_issue141_post_merge_reconciliation_rejects_stale_status(
    monkeypatch: Any, rel: str, search: str, replacement: str, missing_marker: str
) -> None:
    text = phase1.read(rel)
    mutated = replace_text(text, search, replacement)

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={rel: mutated},
    )

    assert any(
        f"{rel} missing issue #141 markers" in failure and missing_marker in failure
        for failure in failures
    )


@pytest.mark.parametrize(
    ("rel", "stale_status"),
    [
        (
            "docs/LAUNCH_LEVELS.md",
            "Status: Proposed clarification for issue `#141` and draft PR `#153`.",
        ),
        (
            "docs/STATUS.md",
            "Documentation baseline remains proposed on the feature branch.",
        ),
        (
            "docs/TRACEABILITY.md",
            "Proposed on branch; external approvals blocked",
        ),
    ],
)
def test_issue141_post_merge_reconciliation_rejects_coexisting_stale_status(
    monkeypatch: Any, rel: str, stale_status: str
) -> None:
    mutated = f"{phase1.read(rel)}\n{stale_status}\n"

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={rel: mutated},
    )

    assert any(
        f"{rel} contains stale issue #141 lifecycle status" in failure
        and stale_status in failure
        for failure in failures
    )


def test_issue141_launch_level_contract_rejects_missing_level(monkeypatch: Any) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    mutated = re.sub(r"^\| Hosted internal synthetic demo \|.*\n", "", launch_text, count=1, flags=re.M)
    assert mutated != launch_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(
        "launch-level boundary rows" in failure and "Hosted internal synthetic demo" in failure
        for failure in failures
    )


def test_issue141_launch_level_contract_rejects_aws_as_local_demo_prerequisite(
    monkeypatch: Any,
) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    mutated = replace_text(
        launch_text,
        "An AWS account is not required for local development or the controlled local mock demo.",
        "An AWS account is required for every local demo.",
    )

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(
        "docs/LAUNCH_LEVELS.md missing issue #141 markers" in failure
        and "An AWS account is not required" in failure
        for failure in failures
    )


def test_issue141_launch_level_contract_rejects_soft_launch_as_demo(
    monkeypatch: Any,
) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    mutated = replace_text(
        launch_text,
        "External users or customer data make this production-adjacent regardless of the words `demo`, `beta`, or `soft launch`.",
        "An invite-only external soft launch is treated as a local demo.",
    )

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(
        "docs/LAUNCH_LEVELS.md missing issue #141 markers" in failure
        and "production-adjacent" in failure
        for failure in failures
    )


@pytest.mark.parametrize(
    ("extra_row", "expected_failure"),
    [
        (
            "| Free external beta | External users. | Free database. | No. | Go. | Demo only. |\n",
            "launch-level boundary contains unexpected rows: Free external beta",
        ),
        (
            "| Local mock demo | Duplicate audience. | Duplicate stack. | No. | Go. | Demo only. |\n",
            "launch-level boundary contains duplicate rows: Local mock demo",
        ),
        (
            "| Malformed beta | External users. | Free database. | Go. | Demo only. |\n",
            "launch-level boundary contains malformed rows",
        ),
    ],
)
def test_issue141_launch_level_contract_rejects_extra_duplicate_or_malformed_rows(
    monkeypatch: Any, extra_row: str, expected_failure: str
) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    table_end = (
        "| Production | External users and approved production data/traffic. | Separate production "
        "tenancy/account with reviewed application, durability, security, privacy, operations, "
        "monitoring, rollback, and support controls. | Yes, a separate production AWS account under "
        "the current baseline; an alternative requires a superseding ADR and equivalent evidence. | "
        "No-Go. | Requires an independent production Go decision; production-like evidence does not "
        "automatically authorize production. |\n"
    )
    mutated = replace_text(launch_text, table_end, table_end + extra_row)

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(expected_failure in failure for failure in failures)


def test_issue141_launch_level_contract_rejects_aws_required_local_demo_cell(
    monkeypatch: Any,
) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    mutated = replace_text(
        launch_text,
        "| No. | Conditional Go only through `docs/demo/PHASE_1_DEMO_CHECKLIST.md`. |",
        "| AWS required; No. exception applies. | Conditional Go only through `docs/demo/PHASE_1_DEMO_CHECKLIST.md`. |",
    )

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(
        "Local mock demo AWS requirement under ADR 0027 must equal: No." in failure
        for failure in failures
    )


def test_issue141_launch_level_contract_rejects_soft_launch_go_posture(
    monkeypatch: Any,
) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    mutated = replace_text(
        launch_text,
        "before durability or launch claims. | No-Go. | External users or customer data",
        "before durability or launch claims. | Go. | External users or customer data",
    )

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(
        "External/invite-only soft launch Current posture must equal: No-Go." in failure
        for failure in failures
    )


def test_issue141_launch_level_contract_rejects_internal_auth_soft_launch_conflation(
    monkeypatch: Any,
) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    launch_text = phase1.read(launch_rel)
    mutated = replace_text(
        launch_text,
        "Internal workforce\nauthentication and minimum identity/access audit metadata do not alone promote\nan otherwise qualifying hosted internal synthetic demo to soft launch.",
        "Any authentication always promotes a hosted internal demo to soft launch.",
    )

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={launch_rel: mutated},
    )

    assert any(
        "docs/LAUNCH_LEVELS.md missing issue #141 markers" in failure
        and "Internal workforce authentication" in failure
        for failure in failures
    )


def test_issue141_platform_ownership_contract_rejects_missing_platform_choice(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0027-production-like-durability-platform-ownership.md")
    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={
            "docs/ADR/0027-production-like-durability-platform-ownership.md": replace_text(
                adr_text,
                "Amazon RDS for PostgreSQL `17.10`,\nMulti-AZ DB instance deployment",
                "A managed relational database selected later",
            )
        },
    )

    assert (
        "docs/ADR/0027-production-like-durability-platform-ownership.md missing issue #141 markers: "
        "Amazon RDS for PostgreSQL `17.10`, Multi-AZ DB instance deployment"
    ) in failures


def test_issue141_platform_ownership_contract_rejects_missing_human_blocker(monkeypatch: Any) -> None:
    preflight_text = phase1.read("docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md")
    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={
            "docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md": replace_text(
                preflight_text,
                "`HUMAN-PLAT-001` remains blocked",
                "`HUMAN-PLAT-001` is documented",
            )
        },
    )

    assert (
        "docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md missing issue #141 markers: "
        "`HUMAN-PLAT-001` remains blocked"
    ) in failures


def test_issue141_platform_ownership_contract_rejects_missing_object_store(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0027-production-like-durability-platform-ownership.md")
    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={
            "docs/ADR/0027-production-like-durability-platform-ownership.md": replace_text(
                adr_text,
                "Amazon S3\ngeneral-purpose buckets with Versioning are authoritative",
                "A future object store may be authoritative",
            )
        },
    )

    assert any("Amazon S3 general-purpose buckets with Versioning are authoritative" in item for item in failures)


def test_issue141_platform_ownership_contract_rejects_rolled_back_deletion_source(
    monkeypatch: Any,
) -> None:
    adr_text = phase1.read("docs/ADR/0027-production-like-durability-platform-ownership.md")
    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={
            "docs/ADR/0027-production-like-durability-platform-ownership.md": replace_text(
                adr_text,
                "is not rolled back\nwith RDS PITR",
                "is reconstructed from the restored database",
            )
        },
    )

    assert any("is not rolled back with RDS PITR" in item for item in failures)


def test_issue141_platform_ownership_contract_rejects_clamped_negative_rpo(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0027-production-like-durability-platform-ownership.md")
    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={
            "docs/ADR/0027-production-like-durability-platform-ownership.md": replace_text(
                adr_text,
                "negative delta, target-ahead sequence, clock ambiguity, cutoff mismatch, or\n  manifest mismatch invalidates the evidence",
                "A negative delta is clamped to zero",
            )
        },
    )

    assert any("negative delta, target-ahead sequence" in item for item in failures)


def test_issue141_platform_ownership_contract_rejects_missing_stage_inventory_row(
    monkeypatch: Any,
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = re.sub(r"^\| Stage 6 \|.*\n", "", adr_text, count=1, flags=re.M)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("durable-state ownership rows" in failure and "Stage 6" in failure for failure in failures)


def test_issue141_platform_ownership_contract_rejects_missing_child_acceptance_row(
    monkeypatch: Any,
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = re.sub(r"^\| `#146`.*\n", "", adr_text, count=1, flags=re.M)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("child acceptance rows" in failure and "#146" in failure for failure in failures)


def test_issue141_platform_ownership_contract_rejects_child_dependency_drift(
    monkeypatch: Any,
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = adr_text.replace(
        "| `#148` restore observability and evidence export | `#130`, `#141`, `#144`, `#145`, `#146`, `#147`;",
        "| `#148` restore observability and evidence export | `#141`, `#144`;",
        1,
    )
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("#148 dependencies" in failure for failure in failures)


@pytest.mark.parametrize(
    ("search", "replacement"),
    [
        ("`#141` approved baseline", "not `#141` approved baseline"),
        ("`#130`, `#141` through `#148`", "not `#130` and not `#141` through `#148`"),
    ],
)
def test_issue141_platform_contract_rejects_negated_dependencies(
    monkeypatch: Any, search: str, replacement: str
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = replace_text(adr_text, search, replacement)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("dependency statement must be affirmative" in failure for failure in failures)


@pytest.mark.parametrize(
    "removed_term",
    [
        "restore timeout/failure",
        "cleanup overdue/orphan",
        "journal gap/backlog/signature failure",
        "KMS loss",
        "severity",
        "owner acknowledgment/escalation",
        "runbook links",
    ],
)
def test_issue141_platform_contract_rejects_incomplete_ch12_route_acceptance(
    monkeypatch: Any, removed_term: str
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    search = "KMS loss with severity" if removed_term == "severity" else removed_term
    replacement = "KMS loss with route detail removed" if removed_term == "severity" else "route detail removed"
    mutated = replace_text(adr_text, search, replacement)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("#148 acceptance contract missing" in failure for failure in failures)


@pytest.mark.parametrize(
    "removed_term",
    [
        "tested failure/timeout/cleanup/journal/KMS routes",
        "tested alert severity/ack/escalation/runbook links",
    ],
)
def test_issue141_ch14_strategy_rejects_incomplete_alert_route_contract(
    monkeypatch: Any, removed_term: str
) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    mutated = replace_text(strategy_text, removed_term, "route evidence removed")
    assert mutated != strategy_text

    failures = run_issue39_execution_strategy_check(monkeypatch, strategy_text=mutated)

    assert any("CH-14 row missing required terms" in failure for failure in failures)


def test_issue141_platform_ownership_contract_rejects_incomplete_journal_integrity_fields(
    monkeypatch: Any,
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = adr_text.replace("event checksum, policy version", "policy version", 1)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("deletion-journal integrity fields" in failure for failure in failures)


@pytest.mark.parametrize(
    "overclaim_text",
    [
        "Azure SQL in westus2, single-zone and publicly accessible, is the authoritative production-like datastore.",
        "The platform is approved by Operations and Security and is Go for launch.",
        "RDS has been provisioned and a backup artifact exists.",
        "Measured RPO was 3 minutes; Platform/Storage signed off.",
    ],
)
def test_issue141_platform_ownership_contract_rejects_structured_contradictions_and_overclaims(
    monkeypatch: Any, overclaim_text: str
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: adr_text + f"\n\n{overclaim_text}\n"},
    )

    assert any("contains issue #141 overclaim markers" in failure for failure in failures)


def test_issue141_platform_ownership_contract_accepts_truthful_backup_negation(
    monkeypatch: Any,
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: adr_text + "\n\nNo managed backup is available.\n"},
    )

    assert not any("contains issue #141 overclaim markers" in failure for failure in failures)


@pytest.mark.parametrize(
    "overclaim_text",
    [
        "There is no question managed backup is verified.",
        "No blocker remains because RDS has been provisioned.",
        "There is not any doubt the restore drill succeeded.",
    ],
)
def test_issue141_platform_contract_rejects_adversarial_negation_lead_ins(
    monkeypatch: Any, overclaim_text: str
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: adr_text + f"\n\n{overclaim_text}\n"},
    )

    assert any("contains issue #141 overclaim markers" in failure for failure in failures)


@pytest.mark.parametrize(
    ("search", "replacement"),
    [
        (
            "`.github/workflows/durability-deploy.yml@refs/heads/main`",
            "an unspecified deployment workflow",
        ),
        ("`id-token: write`", "broad token permission"),
        ("`aud=sts.amazonaws.com`", "an unspecified audience"),
        ("`refs/pull/*/merge`", "pull-request refs"),
        ("prevents self-review", "permits self-review"),
        ("disallows administrator bypass", "permits administrator bypass"),
        ("no larger than `5,000,000,000 bytes`", "of any size"),
        ("`s3:GetObjectVersion`", "`s3:GetObject`"),
        ("destination `s3:PutObject`,", "destination copy action removed,"),
        ("`s3:PutObjectTagging`", "broad destination tag administration"),
        ("fixed run/deadline\n  tag set", "unrestricted tags"),
        ("restore-key `kms:GenerateDataKey`", "restore-key administration"),
        ("internet/NAT, source-VPC, application, provider, or production connectivity", "public internet connectivity"),
        ("Reviewer exports use a field allowlist", "Reviewer exports copy the operational catalog"),
        ("separate read roles and access audit", "a shared unaudited read role"),
        ("writer has create-\nonly permissions and cannot overwrite", "writer may overwrite"),
        ("every use is\nalerted, dated, and reviewed", "use is not audited"),
        ("Control-key disablement/deletion safeguards and\nalarms are mandatory", "Control-key alarms are optional"),
        ("separate asymmetric KMS signing key", "shared symmetric encryption key"),
        (
            "no journal-write,\nreconciliation, retention-bypass, or catalog-mutation permission",
            "journal and catalog administrator permissions",
        ),
        (
            "pins the signing-key ARN,\nalgorithm, manifest policy version and prior signed watermark",
            "accepts any signing key and watermark",
        ),
        (
            "missing,\ninvalid, unexpected-key, or rolled-back signature fails closed",
            "signature errors are ignored",
        ),
        (
            "separate target-cleanup role may remove deletion protection",
            "restore operator may delete any resource",
        ),
        ("`rds:DescribeDBInstances`", "unscoped RDS inventory"),
        ("`rds:ModifyDBInstance`", "unscoped RDS modification"),
        ("`rds:DeleteDBInstance`", "unscoped RDS deletion"),
        ("`rds:DescribeDBSnapshots`", "no snapshot inventory"),
        ("`rds:DescribeDBInstanceAutomatedBackups`", "no automated-backup inventory"),
        ("`rds:DeleteDBSnapshot`", "unscoped snapshot deletion"),
        ("`rds:DeleteDBInstanceAutomatedBackup`", "unscoped automated-backup deletion"),
        ("run-tagged target ARN", "any RDS resource"),
        ("run-tagged orphan", "any retained resource"),
        ("restore\n  bucket/run prefix", "all S3 buckets"),
        ("`s3:ListBucketVersions`", "unversioned bucket listing"),
        ("`s3:GetObjectVersionTagging`", "no version tag inspection"),
        ("`s3:DeleteObjectVersion`", "unversioned object deletion"),
        (
            "It cannot put/read\n  object content, change tags, bypass retention",
            "It can read and mutate object content and tags",
        ),
        (
            "source/control bucket and KMS\n  ARN denies apply independently of tags",
            "source denies depend only on mutable tags",
        ),
    ],
)
def test_issue141_platform_contract_rejects_security_control_regressions(
    monkeypatch: Any, search: str, replacement: str
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = replace_text(adr_text, search, replacement)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("detailed security controls" in failure for failure in failures)


@pytest.mark.parametrize(
    "row_prefix",
    [
        "| Versioned S3 artifact path |",
        "| Security-control journal path |",
    ],
)
def test_issue141_platform_contract_rejects_missing_s3_stride_rows(
    monkeypatch: Any, row_prefix: str
) -> None:
    threat_rel = "docs/THREAT_MODEL.md"
    threat_text = phase1.read(threat_rel)
    mutated = re.sub(rf"^{re.escape(row_prefix)}.*\n", "", threat_text, count=1, flags=re.M)
    assert mutated != threat_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={threat_rel: mutated},
    )

    assert any("S3/journal STRIDE rows" in failure for failure in failures)


@pytest.mark.parametrize(
    ("search", "replacement"),
    [
        (
            "PITR API has no\n`EngineVersion` input",
            "PITR request supplies an `EngineVersion` input",
        ),
        ("`EnableIAMDatabaseAuthentication=true`", "IAM database authentication defaults off"),
        (
            "request explicitly selects `MultiAZ=true`,\n`PubliclyAccessible=false`",
            "request may accept service defaults",
        ),
        (
            "only after DB availability, migration compatibility, database integrity",
            "after DB availability",
        ),
        (
            "At the\n  reviewed holdpoint and before any recovery action",
            "After recovery, from a moving source query",
        ),
        (
            "Automatically tear down the target/delete copied versions within 24 hours",
            "optionally tear down the target when convenient",
        ),
        ("`SkipFinalSnapshot=true`", "`SkipFinalSnapshot=false`"),
        ("`DeleteAutomatedBackups=true`", "`DeleteAutomatedBackups=false`"),
        ("tag-based live-inventory discovery", "catalog-only discovery"),
        ("both catalog and live inventory prove cleanup", "catalog says cleanup is complete"),
        (
            "alert routing owned by CH-12",
            "alert routing is unassigned",
        ),
    ],
)
def test_issue141_platform_contract_rejects_operational_control_regressions(
    monkeypatch: Any, search: str, replacement: str
) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = phase1.read(adr_rel)
    mutated = replace_text(adr_text, search, replacement)
    assert mutated != adr_text

    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={adr_rel: mutated},
    )

    assert any("detailed operational controls" in failure for failure in failures)


@pytest.mark.parametrize(
    "overclaim_text",
    [
        "Production-like durability exists and has been verified.",
        "Issue #126 is closed by this platform decision.",
        "DUR-RESTORE-001 is complete.",
        "Issue #39 has been resolved by issue #141.",
        "Issue #139 is complete and ready to close.",
        "Issue #141 has been completed.",
        "Managed backup verified and queryable.",
        "The restore drill succeeded.",
        "Observed RTO 12m and RPO zero.",
        "Operations/Security approved the platform.",
        "Restore target is deployed.",
        "A recoverable snapshot exists; restoration was successful; the RTO target was met; all signoffs were obtained.",
    ],
)
def test_issue141_platform_ownership_contract_rejects_evidence_and_closure_overclaims(
    monkeypatch: Any, overclaim_text: str
) -> None:
    adr_text = phase1.read("docs/ADR/0027-production-like-durability-platform-ownership.md")
    failures = run_issue141_platform_contract_check(
        monkeypatch,
        read_overrides={
            "docs/ADR/0027-production-like-durability-platform-ownership.md": (
                adr_text + f"\n\n{overclaim_text}\n"
            )
        },
    )

    assert any("contains issue #141 overclaim markers" in failure for failure in failures)


def test_issue126_restore_readiness_contract_accepts_current_docs() -> None:
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert failures == []


def test_issue126_restore_readiness_contract_rejects_missing_no_ready_claim_marker(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md": replace_text(
                    plan_text,
                    "must not be represented as successful\n  production backup/restore evidence or production restore readiness.",
                    "must not be represented as successful production backup/restore evidence.",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md missing issue #126 restore markers: "
        "must not be represented as successful production backup/restore evidence or production restore readiness"
    ) in failures


def test_issue126_restore_readiness_contract_rejects_missing_adr_open_marker(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0026-ch14-restore-readiness-contract.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/ADR/0026-ch14-restore-readiness-contract.md": replace_text(
                    adr_text,
                    "Issue `#39` remains open.",
                    "Issue `#39` follows the usual closure workflow.",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/ADR/0026-ch14-restore-readiness-contract.md missing issue #126 restore markers: "
        "Issue `#39` remains open."
    ) in failures


def test_issue126_restore_readiness_contract_rejects_adr_issue126_closure_overclaim(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0026-ch14-restore-readiness-contract.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/ADR/0026-ch14-restore-readiness-contract.md": (
                    adr_text + "\n\nIssue `#126` is closed by this contract-only readiness slice.\n"
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/ADR/0026-ch14-restore-readiness-contract.md contains issue #126 restore overclaim markers: "
        "issue #126 closed or satisfied"
    ) in failures


@pytest.mark.parametrize(
    ("overclaim_text", "expected_marker"),
    [
        (
            "Successful production restore drill complete and production restore readiness achieved for DUR-RESTORE-001.",
            "successful production restore drill complete, production restore readiness achieved",
        ),
        (
            "Issue #126 is now fully satisfied by this readiness contract.",
            "issue #126 closed or satisfied",
        ),
        (
            "Matrix row DUR-RESTORE-001 is Closed by the CH-14 slice.",
            "dur-restore-001 closed",
        ),
        (
            "Production restore is ready based on this repo evidence.",
            "production restore is ready",
        ),
        (
            "Issue #39 is resolved for restore readiness.",
            "issue #39 closed or resolved",
        ),
        (
            "Issue #39 has been resolved for restore readiness.",
            "issue #39 closed or resolved",
        ),
        (
            "Issue #126 has been closed by this readiness contract.",
            "issue #126 closed or satisfied",
        ),
        (
            "DUR-RESTORE-001 has been satisfied by this CH-14 slice.",
            "dur-restore-001 closed",
        ),
        (
            "Production restore readiness is achieved by this evidence.",
            "production restore readiness achieved",
        ),
        (
            "Production restore has been verified by this evidence.",
            "production restore is ready",
        ),
        (
            "The production restore drill was successful.",
            "successful production restore drill complete",
        ),
    ],
)
def test_issue126_restore_readiness_contract_rejects_production_restore_overclaim_variants(
    monkeypatch: Any, overclaim_text: str, expected_marker: str
) -> None:
    adr_text = phase1.read("docs/ADR/0026-ch14-restore-readiness-contract.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/ADR/0026-ch14-restore-readiness-contract.md": adr_text + f"\n\n{overclaim_text}\n",
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/ADR/0026-ch14-restore-readiness-contract.md contains issue #126 restore overclaim markers: "
        f"{expected_marker}"
    ) in failures


def test_issue126_restore_readiness_contract_rejects_missing_stage_issue_plan_marker(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/STAGE_ISSUE_PLAN.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/STAGE_ISSUE_PLAN.md": replace_text(
                    plan_text,
                    "adds anti-overclaim guardrails.",
                    "adds documentation updates.",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/STAGE_ISSUE_PLAN.md missing issue #126 restore markers: "
        "adds anti-overclaim guardrails."
    ) in failures


def test_issue126_restore_readiness_contract_rejects_missing_issue125_boundary_marker(monkeypatch: Any) -> None:
    preflight_text = phase1.read("docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md": replace_text(
                    preflight_text,
                    "issue `#126` may add only narrower readiness-contract guardrails until that\n  final proof exists.",
                    "issue `#126` may add later follow-up guardrails.",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md missing issue #126 restore markers: "
        "final `CH-14` `DUR-RESTORE-001` closure tied to successful restore-drill evidence; later issue `#126` may add only narrower readiness-contract guardrails until that final proof exists."
    ) in failures


def test_issue126_restore_readiness_contract_rejects_missing_issue126_preflight_marker(monkeypatch: Any) -> None:
    preflight_text = phase1.read("docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md": replace_text(
                    preflight_text,
                    "current repo-baselined restore-adjacent metrics/SLO contracts",
                    "restore-adjacent metrics/SLO contracts",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert (
        "docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md missing issue #126 restore markers: "
        "current repo-baselined restore-adjacent metrics/SLO contracts"
    ) in failures


def test_issue126_restore_readiness_contract_rejects_status_drift(monkeypatch: Any) -> None:
    status_text = phase1.read("docs/STATUS.md")
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {
                "docs/STATUS.md": replace_text(
                    status_text,
                    "| `#126` | Open |",
                    "| `#126` | Closed |",
                ),
            },
        ),
    )
    failures: list[str] = []
    phase1.check_issue126_restore_readiness_contract(failures)

    assert "docs/STATUS.md missing issue #126 restore markers: | `#126` | Open |" in failures


def test_issue39_closure_plan_rejects_closed_row_without_closure_record(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |",
            "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable identifiers, versioning, and compare-and-set invariants | Architecture + storage | PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Closed |",
        ),
    )

    assert "Issue #39 matrix row DUR-ACID-001 is Closed without a row closure record." in failures


def test_issue39_closure_plan_accepts_closed_row_with_valid_closure_record(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    row_closed = row_open.replace("| Open |", "| Closed |")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_closed,
        ),
    )

    assert failures == []


def test_issue39_closure_plan_rejects_closed_row_with_external_repo_pr(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/example/other-repo/pull/102"
            ),
        ),
    )

    assert (
        "Issue #39 closed row DUR-ACID-001 must cite concrete same-repository child issue and PR URLs."
        in failures
    )


def test_issue39_closure_plan_rejects_context0_pr_as_final_proof(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/64"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 must not use Context 0 PR #64 as final proof." in failures


def test_issue39_closure_plan_rejects_planning_pr_as_final_proof(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/80"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 must not use planning PRs #64-#80 as final proof: #80" in failures


def test_issue39_closure_plan_rejects_parent_issue_as_child_issue(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            child_reference=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/39 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/102"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 must cite a child issue distinct from #39." in failures


def test_issue39_closure_plan_rejects_vague_artifact_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="artifact attached in PR",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_nonexistent_test_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_nonexistent_evidence",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_nonexistent_test_even_with_artifact_url(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence=(
                "test_issue39_nonexistent_evidence "
                "https://github.com/imrohitagrawal/narratwin-ai/blob/main/docs/STATUS.md"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_bare_existing_test_name_without_node_and_ci(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix restore drill rto rpo",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_node_id_without_ci_or_drill_artifact(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="tests/unit/test_phase1_closure_docs.py::test_issue39_closure_plan_accepts_current_matrix",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_issue_pr_urls_as_validation_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence=(
                "https://github.com/imrohitagrawal/narratwin-ai/issues/101 "
                "https://github.com/imrohitagrawal/narratwin-ai/pull/102"
            ),
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_bare_drill_log_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="drill log reviewed",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_nonexistent_drill_log_path(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="docs/reviews/no_such_drill.md drill log restore drill rto rpo",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_drill_log_path_traversal(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="docs/../.git/config drill log restore drill rto rpo",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_existing_unrelated_drill_log_file(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="docs/evals/phase1_golden_questions.jsonl drill log restore drill rto rpo",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_malformed_actions_run_url(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-ACID-001` | ACID/CAS durable metadata | Production transaction model for durable "
        "identifiers, versioning, and compare-and-set invariants | Architecture + storage | "
        "PostgreSQL-compatible ADR section with conflict example and replay invariant checklist | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="https://github.com/imrohitagrawal/narratwin-ai/actions/runs/123fake",
        ),
    )

    assert "Issue #39 closed row DUR-ACID-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_ops_row_without_row_specific_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="human-only evidence reviewed",
            satisfies="generic production review evidence",
        ),
    )

    assert (
        "Issue #39 closed row DUR-RESTORE-001 missing operational closure evidence terms: "
        "restore drill; rto; rpo"
    ) in failures


def test_issue39_closure_plan_rejects_operational_human_only_keyword_prose(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `DUR-RESTORE-001` | Backup/restore drill | Backup scope, integrity, restore smoke, and RTO/RPO "
        "verification | Ops | Operable restore playbook with evidence of at least one successful restore drill | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="DUR-RESTORE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="human-only restore drill rto rpo reviewed by ops",
            satisfies="restore drill rto rpo evidence",
        ),
    )

    assert "Issue #39 closed row DUR-RESTORE-001 lacks concrete validation or human-only evidence." in failures


def test_issue39_closure_plan_rejects_sensitive_row_without_row_specific_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `PROVIDER-POSTURE-001` | Provider release posture | External provider legal, license, network, "
        "egress, key, and rollout controls | Security/Privacy + Platform | Provider release checklist with "
        "legal/license review, mock/local default, no real keys in local/dev/test/CI, explicit production "
        "enablement, deny-by-default egress, key isolation, no secret logging or prompt inclusion, and "
        "rollback disablement evidence | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="PROVIDER-POSTURE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix",
            satisfies="generic production review evidence",
        ),
    )

    assert (
        "Issue #39 closed row PROVIDER-POSTURE-001 missing operational closure evidence terms: "
        "provider; legal/license; egress; key; explicit production enablement"
    ) in failures


@pytest.mark.parametrize(
    ("matrix_id", "row_open", "expected_terms"),
    [
        (
            "MEDIA-CONSENT-001",
            "| `MEDIA-CONSENT-001` | Consent capture | Affirmative consent record for synthetic-media generation | Security/Privacy | Consent schema with actor, timestamp, consent text/version, artifact refs, source-run binding, scope, and audit retention | Open |",
            "consent; actor; scope; audit",
        ),
        (
            "SEC-UNTRUSTED-001",
            "| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Uploaded docs, prompts, transcripts, provider outputs, model outputs, restored artifacts, exported media metadata, and replayed provenance remain untrusted | Security/Privacy + Runtime + Ops | Validation, output encoding, log redaction, prompt-injection/poisoned-retrieval controls, restore-time revalidation, and replay/export safety evidence for durable untrusted content | Open |",
            "untrusted; validation; output encoding; log redaction",
        ),
    ],
)
def test_issue39_closure_plan_rejects_media_and_sec_rows_without_row_specific_evidence(
    monkeypatch: Any,
    matrix_id: str,
    row_open: str,
    expected_terms: str,
) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id=matrix_id,
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix",
            satisfies="generic production review evidence",
        ),
    )

    assert (
        f"Issue #39 closed row {matrix_id} missing operational closure evidence terms: "
        f"{expected_terms}"
    ) in failures


def test_issue39_closure_plan_rejects_provider_closure_without_enablement_evidence(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    row_open = (
        "| `PROVIDER-POSTURE-001` | Provider release posture | External provider legal, license, network, "
        "egress, key, and rollout controls | Security/Privacy + Platform | Provider release checklist with "
        "legal/license review, mock/local default, no real keys in local/dev/test/CI, explicit production "
        "enablement, deny-by-default egress, key isolation, no secret logging or prompt inclusion, and "
        "rollback disablement evidence | Open |"
    )
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=issue39_plan_with_closed_row_and_record(
            plan_text,
            matrix_id="PROVIDER-POSTURE-001",
            row_status_search=row_open,
            row_status_replacement=row_open.replace("| Open |", "| Closed |"),
            evidence="test_issue39_closure_plan_accepts_current_matrix",
            satisfies="provider legal/license egress key evidence",
        ),
    )

    assert (
        "Issue #39 closed row PROVIDER-POSTURE-001 missing operational closure evidence terms: "
        "explicit production enablement"
    ) in failures


def test_issue39_closure_plan_rejects_weakened_sensitive_row(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(plan_text, "restored artifacts", "restored records"),
    )

    assert (
        "Issue #39 matrix row SEC-UNTRUSTED-001 missing required contract terms: restored artifacts"
        in failures
    )


def test_issue39_closure_plan_rejects_weakened_provider_enablement(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(plan_text, "explicit production enablement", "production review"),
    )

    assert (
        "Issue #39 matrix row PROVIDER-POSTURE-001 missing required contract terms: "
        "explicit production enablement"
    ) in failures


def test_issue39_closure_plan_rejects_malformed_matrix_row(monkeypatch: Any) -> None:
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_closure_plan_check(
        monkeypatch,
        plan_text=replace_text(
            plan_text,
            "| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Uploaded docs, prompts, transcripts, provider outputs, model outputs, restored artifacts, exported media metadata, and replayed provenance remain untrusted | Security/Privacy + Runtime + Ops | Validation, output encoding, log redaction, prompt-injection/poisoned-retrieval controls, restore-time revalidation, and replay/export safety evidence for durable untrusted content | Open |",
            "| `SEC-UNTRUSTED-001` | Untrusted durable/replayed input handling | Open |",
        ),
    )

    assert "Issue #39 matrix row must have 6 columns:" in failures[0]


def test_issue39_execution_strategy_accepts_current_chunk_plan() -> None:
    failures: list[str] = []
    phase1.check_issue39_execution_strategy(failures)

    assert failures == []


def test_issue39_execution_strategy_rejects_missing_matrix_id(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("`SEC-UNTRUSTED-001`", "`SEC-RETENTION-001`"),
    )

    assert "Issue #39 execution strategy missing matrix IDs: SEC-UNTRUSTED-001" in failures


def test_issue39_execution_strategy_rejects_missing_chunk_even_with_matrix_id_preserved(
    monkeypatch: Any,
) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    strategy_text = strategy_text.replace(
        "| `CH-21` retention and erasure | `SEC-RETENTION-001` |",
        "| `CH-21` retention and erasure | `SEC-RETENTION-001`, `SEC-UNTRUSTED-001` |",
        1,
    )
    strategy_text = strategy_text.replace(
        "| `CH-22` untrusted replayed input | `SEC-UNTRUSTED-001` | `CH-03`, `CH-07`, `CH-08`, `CH-21` | Security/runtime | Untrusted-input preflight covering uploads, prompts, transcripts, provider outputs, restored artifacts, metadata | Security/privacy reviewer, runtime reviewer, operations reviewer | Durable and replayed content is revalidated, encoded, redacted, and protected from poisoned retrieval and prompt injection. |\n",
        "",
        1,
    )
    failures = run_issue39_execution_strategy_check(monkeypatch, strategy_text=strategy_text)

    assert "Issue #39 execution strategy missing chunks: CH-22" in failures
    assert (
        "Issue #39 execution strategy chunk CH-21 matrix IDs must be SEC-RETENTION-001; "
        "got SEC-RETENTION-001, SEC-UNTRUSTED-001."
    ) in failures


def test_issue39_execution_strategy_rejects_dependency_cycle(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(
            "| `CH-08` Stage 7 render artifact state | `DUR-STAGE7-001` | `CH-03`, `CH-04`, `CH-16` |",
            "| `CH-08` Stage 7 render artifact state | `DUR-STAGE7-001` | `CH-03`, `CH-04`, `CH-16`, `CH-18` |",
            1,
        ),
    )

    assert "Issue #39 execution strategy has dependency cycle:" in "\n".join(failures)


def test_issue39_execution_strategy_rejects_missing_final_dependency(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(", `CH-22` | Final sequential", " | Final sequential", 1),
    )

    assert "Issue #39 execution strategy chunk CH-23 dependencies must be" in "\n".join(failures)


def test_issue39_execution_strategy_rejects_missing_deployment_stop_rule(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("Failed production transition probes halt before enablement", "Probe failures are handled", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md Deployment Transition Plan missing required terms: "
        "Failed production transition probes halt before enablement"
    ) in failures


def test_issue39_execution_strategy_rejects_weakened_dod_review_loop(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("re-reviewed by a fresh reviewer", "checked again", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md Chunk Definition Of Done missing required terms: "
        "re-reviewed by a fresh reviewer"
    ) in failures


@pytest.mark.parametrize(
    "term",
    [
        "documented human-only evidence surface",
        "fixed",
        "rejected with evidence",
        "non-goal with rationale",
        "human-only follow-up",
    ],
)
def test_issue39_execution_strategy_rejects_weakened_dod_disposition_terms(
    monkeypatch: Any,
    term: str,
) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(term, "removed required DoD term", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md Chunk Definition Of Done missing required terms: "
        f"{term}"
    ) in failures


def test_issue39_execution_strategy_rejects_weakened_ch10_metric_contract(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace(
            "restore and rollback metric emissions close with `CH-14` and `CH-15` evidence",
            "restore and rollback metric emissions are complete in this chunk",
            1,
        ),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md CH-10 row missing required terms: "
        "restore and rollback metric emissions close with `ch-14` and `ch-15`"
    ) in failures


def test_issue39_ch11_contract_accepts_current_docs(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0025-ch11-slo-error-budget.md")
    failures = run_issue39_ch11_contract_check(monkeypatch, adr_text=adr_text)

    assert failures == []


def test_issue39_ch11_contract_rejects_missing_manual_review_contract_marker(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0025-ch11-slo-error-budget.md")
    failures = run_issue39_ch11_contract_check(
        monkeypatch,
        adr_text=adr_text.replace("manual review contract", "unsupported wording"),
    )

    assert (
        "docs/ADR/0025-ch11-slo-error-budget.md missing required markers: manual review contract"
        in failures
    )


def test_issue39_ch11_contract_rejects_missing_plan_mapping(monkeypatch: Any) -> None:
    adr_text = phase1.read("docs/ADR/0025-ch11-slo-error-budget.md")
    plan_text = phase1.read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    failures = run_issue39_ch11_contract_check(
        monkeypatch,
        adr_text=adr_text,
        plan_text=plan_text.replace(
            "### Issue `#127` CH-11 SLO and error-budget contract status and evidence mapping",
            "### Issue `#127` CH-11 mapping removed",
            1,
        ),
    )

    assert (
        "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md missing CH-11 markers: "
        "### Issue `#127` CH-11 SLO and error-budget contract status and evidence mapping"
    ) in failures


def test_issue39_execution_strategy_rejects_missing_rereview_protocol(monkeypatch: Any) -> None:
    strategy_text = phase1.read("docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md")
    failures = run_issue39_execution_strategy_check(
        monkeypatch,
        strategy_text=strategy_text.replace("## Re-Review After Fixes", "## Review Fix Handling", 1),
    )

    assert (
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md missing required heading: Re-Review After Fixes"
        in failures
    )


def test_issue39_execution_strategy_branch_allows_strategy_doc(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        files=[
            ".github/workflows/ci.yml",
            ".github/workflows/eval-smoke.yml",
            ".github/workflows/security.yml",
            "docs/QUALITY_GATES.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md",
            "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/guardrails_check.py",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_execution_strategy_branch_rejects_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-execution-strategy may not change backend/app/stage4.py."
    ]


def test_issue39_unknown_generic_chunk_branch_rejects_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-99-unreviewed-kernel",
        files=["backend/app/storage/postgres_state.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-99-unreviewed-kernel may not change "
        "backend/app/storage/postgres_state.py."
    ]


def test_issue247_branch_allows_only_demo_refusal_ux_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-247-demo-422-refusal-ux",
        files=sorted(phase1.ISSUE_247_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue247_branch_rejects_adjacent_frontend_or_backend_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-247-demo-422-refusal-ux",
        files=[
            "backend/app/main.py",
            "frontend/tests/real-stack.spec.ts",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-247-demo-422-refusal-ux may not change backend/app/main.py.",
        "Phase 1 Closure branch phase-1-closure-247-demo-422-refusal-ux may not change frontend/tests/real-stack.spec.ts.",
    ]


def test_issue39_ch02_branch_allows_storage_kernel_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-02-acid-cas-kernel",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0014-ch02-acid-cas-storage-kernel.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_postgres_state.py",
        ],
    )

    assert failures == []


def test_issue39_ch02_branch_rejects_stage_runtime_or_later_chunk_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-02-acid-cas-kernel",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-02-acid-cas-kernel may not change backend/app/stage4.py."
    ]


def test_issue39_ch02_branch_rejects_adjacent_chunk_or_issue39_doc_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-02-acid-cas-kernel",
        files=[
            "backend/app/storage/migrations.py",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-02-acid-cas-kernel may not change backend/app/storage/migrations.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-02-acid-cas-kernel may not change docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md.",
    ]


def test_issue39_ch03_branch_allows_stage4_durable_graph_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-03-stage4-durable-graph",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/stage4_graph.py",
            "docs/ADR/0018-ch03-stage4-durable-graph.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_stage4_durable_graph.py",
        ],
    )

    assert failures == []


def test_issue39_ch03_branch_rejects_adjacent_chunk_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-03-stage4-durable-graph",
        files=[
            "backend/app/storage/postgres_state.py",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
            "docs/ADR/0017-ch06-committed-outbox.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-03-stage4-durable-graph may not change backend/app/storage/postgres_state.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-03-stage4-durable-graph may not change backend/app/stage6.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-03-stage4-durable-graph may not change backend/app/stage7.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-03-stage4-durable-graph may not change docs/ADR/0017-ch06-committed-outbox.md.",
    ]


def test_issue39_ch04_branch_allows_idempotency_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-04-idempotency-semantics",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0015-ch04-idempotency-semantics.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_postgres_state.py",
        ],
    )

    assert failures == []


def test_issue39_ch04_branch_rejects_runtime_or_adjacent_chunk_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-04-idempotency-semantics",
        files=[
            "backend/app/stage4.py",
            "docs/ADR/0016-ch05-lease-fencing.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-04-idempotency-semantics may not change backend/app/stage4.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-04-idempotency-semantics may not change docs/ADR/0016-ch05-lease-fencing.md.",
    ]


def test_issue39_ch05_branch_allows_lease_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-05-lease-fencing",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0016-ch05-lease-fencing.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_postgres_state.py",
        ],
    )

    assert failures == []


def test_issue39_ch05_branch_rejects_runtime_or_adjacent_chunk_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-05-lease-fencing",
        files=[
            "backend/app/stage6.py",
            "docs/ADR/0017-ch06-committed-outbox.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-05-lease-fencing may not change backend/app/stage6.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-05-lease-fencing may not change docs/ADR/0017-ch06-committed-outbox.md.",
    ]


def test_issue39_ch06_branch_allows_outbox_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-06-committed-outbox",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0017-ch06-committed-outbox.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_postgres_state.py",
        ],
    )

    assert failures == []


def test_issue39_ch06_branch_rejects_runtime_or_adjacent_chunk_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-06-committed-outbox",
        files=[
            "backend/app/stage7.py",
            "docs/ADR/0015-ch04-idempotency-semantics.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-06-committed-outbox may not change backend/app/stage7.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-06-committed-outbox may not change docs/ADR/0015-ch04-idempotency-semantics.md.",
    ]


def test_issue39_ch07_branch_allows_stage6_durable_replay_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-07-stage6-durable-replay",
        files=[
            "backend/app/main.py",
            "backend/app/stage6.py",
            "backend/app/storage/__init__.py",
            "backend/app/storage/file_state.py",
            "docs/API_CONTRACT.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/api/test_stage6_multilingual_api.py",
            "tests/unit/test_local_durability.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_stage6_multilingual.py",
        ],
    )

    assert failures == []


def test_issue39_ch08_branch_allows_stage7_render_artifact_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-08-stage7-render-artifact-state",
        files=[
            "backend/app/main.py",
            "backend/app/stage7.py",
            "backend/app/storage/file_state.py",
            "docs/ADR/0021-ch08-stage7-render-artifact-state.md",
            "docs/API_CONTRACT.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/api/test_stage7_avatar_api.py",
            "tests/unit/test_local_durability.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_stage7_avatar.py",
        ],
    )

    assert failures == []


def test_issue39_ch16_branch_allows_consent_capture_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-16-consent-capture",
        files=[
            "backend/app/main.py",
            "backend/app/stage7.py",
            "docs/ADR/0019-ch16-consent-capture.md",
            "docs/API_CONTRACT.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/api/test_stage7_avatar_api.py",
            "tests/unit/test_local_durability.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_stage7_avatar.py",
        ],
    )

    assert failures == []


def test_issue39_ch16_branch_rejects_adjacent_runtime_or_scope_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-16-consent-capture",
        files=[
            "backend/app/stage6.py",
            "docs/ADR/0017-ch06-committed-outbox.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-16-consent-capture may not change backend/app/stage6.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-16-consent-capture may not change docs/ADR/0017-ch06-committed-outbox.md.",
    ]


def test_issue39_ch08_branch_rejects_adjacent_runtime_or_scope_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-08-stage7-render-artifact-state",
        files=[
            "backend/app/storage/stage4_graph.py",
            "backend/app/stage6.py",
            "backend/app/rag/providers.py",
            "docs/ADR/0008-postgresql-durability-schema-boundary.md",
            "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
            "docs/ADR/0011-context4-backup-restore-drill.md",
            "docs/ADR/0012-context5-metrics-slos-watch.md",
            "docs/ADR/0017-ch06-committed-outbox.md",
            "docs/ADR/0019-ch16-consent-capture.md",
            "docs/ADR/0020-ch07-stage6-durable-replay.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change backend/app/storage/stage4_graph.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change backend/app/stage6.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change backend/app/rag/providers.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0008-postgresql-durability-schema-boundary.md.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0009-context2-idempotency-lease-outbox-contract.md.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0011-context4-backup-restore-drill.md.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0012-context5-metrics-slos-watch.md.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0017-ch06-committed-outbox.md.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0019-ch16-consent-capture.md.",
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state may not change docs/ADR/0020-ch07-stage6-durable-replay.md.",
    ]


def test_issue39_ch07_branch_rejects_adjacent_chunk_or_stage7_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-07-stage6-durable-replay",
        files=[
            "backend/app/stage7.py",
            "backend/app/storage/postgres_state.py",
            "docs/ADR/0017-ch06-committed-outbox.md",
        ],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-07-stage6-durable-replay may not change backend/app/stage7.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-07-stage6-durable-replay may not change backend/app/storage/postgres_state.py.",
        "Phase 1 Closure branch phase-1-closure-39-ch-07-stage6-durable-replay may not change docs/ADR/0017-ch06-committed-outbox.md.",
    ]


def test_issue39_ch08_branch_requires_ch03_ch04_ch07_and_ch16_dependency_commits(
    monkeypatch: Any,
) -> None:
    failures = run_branch_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-08-stage7-render-artifact-state",
        ancestor_ok=False,
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-08-stage7-render-artifact-state must contain dependency "
        "commits: 6449786069dd38eeaa5a4a31f5ed73cbfc52d248, 947a96891fd84085b6fce433e604a8e249b25c23, "
        "1f3d66d9b1b545e5d5c41e88a83cc731a2a8b31a, acccd6939ebe172b9a2d95f51fa96212035f55b0.",
    ]


def test_issue39_ch16_branch_requires_ch02_dependency_commit_ancestry(monkeypatch: Any) -> None:
    failures = run_branch_check(
        monkeypatch,
        branch="phase-1-closure-39-ch-16-consent-capture",
        ancestor_ok=False,
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch-16-consent-capture must contain dependency "
        "commits: 824a07c2bd546648b96d9ab555b63a8f2415898e.",
    ]


def test_status_keeps_issue39_open_while_matrix_rows_are_open(monkeypatch: Any) -> None:
    status_text = phase1.read("docs/STATUS.md")
    failures = run_release_docs_check(
        monkeypatch,
        read_overrides={
            "docs/STATUS.md": status_text.replace(
                "| `#39` | Open, partially remediated |",
                "| `#39` | Closed |",
                1,
            )
        },
    )

    assert "docs/STATUS.md issue #39 must remain Open while production closure matrix rows are Open." in failures


def test_status_rejects_closed_issue39_with_open_substring(monkeypatch: Any) -> None:
    status_text = phase1.read("docs/STATUS.md")
    failures = run_release_docs_check(
        monkeypatch,
        read_overrides={
            "docs/STATUS.md": status_text.replace(
                "| `#39` | Open, partially remediated |",
                "| `#39` | Closed (no reopening planned) |",
                1,
            )
        },
    )

    assert "docs/STATUS.md issue #39 must remain Open while production closure matrix rows are Open." in failures


def test_process_only_phase1_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-55-phf-006-scope-gate",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-process-55-phf-006-scope-gate may not change backend/app/stage4.py."
    ]


def test_issue172_branch_allows_only_offline_preflight_core_paths(monkeypatch: Any) -> None:
    files = [
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/governance/GOVERNANCE_PREFLIGHT_V1.schema.json",
        "scripts/governance_preflight_v1.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_governance_preflight_v1.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert phase1.ISSUE_172_ALLOWED_CHANGED_FILES == set(files)
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-172-gpf-v1-offline-core",
        files=files,
    ) == []


def test_issue172_branch_does_not_pre_authorize_repository_adapter(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-172-gpf-v1-offline-core",
        files=["scripts/governance_preflight_repository.py", ".github/workflows/quality-gates.yml"],
    )
    assert failures == [
        "Phase 1 Closure branch phase-1-closure-process-172-gpf-v1-offline-core "
        "may not change scripts/governance_preflight_repository.py.",
        "Phase 1 Closure branch phase-1-closure-process-172-gpf-v1-offline-core "
        "may not change .github/workflows/quality-gates.yml.",
    ]


def test_issue176_branch_allows_only_frozen_repository_integration_paths(monkeypatch: Any) -> None:
    files = [
        "docs/governance/preflights/issue-176.json",
        "scripts/governance_preflight_repository.py",
        "tests/unit/test_governance_preflight_repository.py",
        "scripts/guardrails_check.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    ]
    assert phase1.ISSUE_176_ALLOWED_CHANGED_FILES == set(files)
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-176-gpf-v1-repository-integration",
        files=files,
    ) == []


def test_issue176_branch_rejects_pr_c_workflow_and_runtime_paths(monkeypatch: Any) -> None:
    files = [
        ".github/workflows/quality-gates.yml",
        "scripts/governance_preflight_github.py",
        "backend/app/main.py",
    ]
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-176-gpf-v1-repository-integration",
        files=files,
    ) == [
        "Phase 1 Closure branch phase-1-closure-process-176-gpf-v1-repository-integration "
        f"may not change {path}."
        for path in files
    ]


def test_issue176_allowlist_does_not_apply_to_near_match_branch(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-176-gpf-v1-repository-integration-suffix"
    assert run_changed_files_check(
        monkeypatch, branch=branch, files=["scripts/governance_preflight_repository.py"]
    ) == [f"Phase 1 Closure branch {branch} may not change scripts/governance_preflight_repository.py."]


def test_issue151_branch_allows_only_frozen_security_remediation_paths(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-151.json", "backend/Dockerfile", "security/cpython-3.13.14/backports.json",
        "security/cpython-3.13.14/apply_backports.py", "scripts/ci/verify-cpython-backports.py",
        "scripts/ci/check_container_scan_consensus.py", "scripts/ci/docker-build.sh", "scripts/ci/docker-image-scan.sh",
        "scripts/ci/check_semgrep_security.py", "tools/semgrep/pyproject.toml", "tools/semgrep/uv.lock", "tools/semgrep/reviewed-inputs.sha256",
        "tests/unit/test_cpython_security_backports.py", "tests/unit/test_container_scan_consensus.py", "tests/unit/test_dependency_security_contract.py", "tests/unit/test_governance_preflight_repository.py",
        "scripts/quality/check_phase1_closure_docs.py", "tests/unit/test_phase1_closure_docs.py", "docs/ADR/0006-stage8-release-hardening.md",
        "docs/QUALITY_GATES.md", "docs/REPOSITORY_GUARDRAILS.md", "docs/RELEASE_CHECKLIST.md", "docs/THIRD_PARTY_NOTICES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/TRACEABILITY.md", "docs/STATUS.md",
    }
    assert phase1.ISSUE_151_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-151-cpython313-security-remediation",
        files=sorted(expected),
    ) == []


def test_issue151_allowlist_rejects_near_match_and_unauthorized_path(monkeypatch: Any) -> None:
    allowed_path = "backend/Dockerfile"
    for branch in (
        "phase-1-closure-process-151-cpython313-security-remediation-extra",
        "phase-1-closure-process-115-cpython313-security-remediation",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[allowed_path]) == [
            f"Phase 1 Closure branch {branch} may not change {allowed_path}."
        ]
    branch = "phase-1-closure-process-151-cpython313-security-remediation"
    for path in ("backend/app/main.py", "scripts/governance_preflight_github.py"):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
            f"Phase 1 Closure branch {branch} may not change {path}."
        ]


def test_issue219_branch_allows_only_frontend_audit_remediation_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-219.json",
        "frontend/package.json",
        "frontend/package-lock.json",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/ADR/0031-frontend-lighthouse-audit-remediation.md",
        "docs/TRACEABILITY.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_219_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-security-219-frontend-npm-audit",
        files=sorted(expected),
    ) == []


def test_issue219_allowlist_rejects_near_match_and_runtime_files(monkeypatch: Any) -> None:
    allowed_path = "frontend/package-lock.json"
    for branch in (
        "phase-1-closure-security-219-frontend-npm-audit-extra",
        "phase-1-closure-security-912-frontend-npm-audit",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[allowed_path]) == [
            f"Phase 1 Closure branch {branch} may not change {allowed_path}."
        ]

    branch = "phase-1-closure-security-219-frontend-npm-audit"
    for path in ("frontend/src/app/page.tsx", "backend/app/main.py"):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
            f"Phase 1 Closure branch {branch} may not change {path}."
        ]


def test_issue178_branch_uses_only_exact_ci_evidence_scope(monkeypatch: Any) -> None:
    assert run_changed_files_check(monkeypatch, branch="phase-1-closure-process-178-gpf-v1-ci-evidence", files=sorted(phase1.ISSUE_178_ALLOWED_CHANGED_FILES)) == []
    branch = "phase-1-closure-process-178-gpf-v1-ci-evidence-extra"
    assert run_changed_files_check(monkeypatch, branch=branch, files=["scripts/governance_preflight_github.py"]) == [
        f"Phase 1 Closure branch {branch} may not change scripts/governance_preflight_github.py."
    ]


def test_issue155_ch_m1_01_branch_allows_only_durable_consent_chain_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/ADR/0019-ch16-consent-capture.md",
        "docs/reviews/ISSUE_204_CH_M1_01_PREFLIGHT.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "frontend/src/app/page.tsx",
        "frontend/tests/smoke.spec.ts",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }

    assert phase1.ISSUE_155_CH_M1_01_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-155-ch-m1-01-durable-consent-chain",
        files=sorted(expected),
    ) == []


def test_issue155_ch_m1_01_branch_rejects_backend_provider_and_unrelated_files(
    monkeypatch: Any,
) -> None:
    files = [
        "backend/app/stage7.py",
        "frontend/package.json",
        "docs/API_CONTRACT.md",
    ]

    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-155-ch-m1-01-durable-consent-chain",
        files=files,
    ) == [
        "Phase 1 Closure branch phase-1-closure-155-ch-m1-01-durable-consent-chain "
        f"may not change {path}."
        for path in files
    ]


def test_issue155_ch_m1_01_allowlist_does_not_apply_to_near_match_branch(monkeypatch: Any) -> None:
    branch = "phase-1-closure-155-ch-m1-010-durable-consent-chain"

    assert run_changed_files_check(monkeypatch, branch=branch, files=["frontend/src/app/page.tsx"]) == [
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx."
    ]


def test_issue39_durability_branch_keeps_existing_runtime_allowlist(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-durability-monitoring",
        files=["backend/app/stage4.py"],
    )

    assert failures == []


def test_issue39_context1_issue65_branch_allows_schema_boundary_adr(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context1-postgresql-durability-adr",
        files=["docs/ADR/0008-postgresql-durability-schema-boundary.md"],
    )

    assert failures == []


def test_issue39_context1_issue65_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context1-postgresql-durability-adr",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context1-postgresql-durability-adr may not change backend/app/stage4.py."
    ]


def test_issue39_context2_issue66_branch_allows_idempotency_lease_outbox_adr(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context2-idempotency-lease-outbox",
        files=[
            "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context2_issue66_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context2-idempotency-lease-outbox",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context2-idempotency-lease-outbox may not change backend/app/stage4.py."
    ]


def test_issue39_context3_issue67_branch_allows_migrations_and_plan_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context3-migrations-rollback",
        files=[
            "docs/ADR/0010-context3-migrations-rollback-compatibility.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context3_issue67_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context3-migrations-rollback",
        files=["backend/app/stage6.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context3-migrations-rollback may not change backend/app/stage6.py."
    ]


def test_issue39_context3_issue67_branch_rejects_unrelated_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context3-migrations-rollback",
        files=["docs/unrelated-runtime-plan.md"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context3-migrations-rollback may not change "
        "docs/unrelated-runtime-plan.md."
    ]


def test_issue39_ch01_branch_allows_migration_baseline_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch01-migration-baseline",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/migrations.py",
            "docs/ADR/0013-ch01-migration-baseline-runner.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
            "tests/unit/test_storage_migrations.py",
        ],
    )

    assert failures == []


def test_issue39_ch01_branch_rejects_unrelated_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch01-migration-baseline",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch01-migration-baseline may not change backend/app/stage4.py."
    ]


def test_issue39_ch01_branch_rejects_broader_issue39_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-ch01-migration-baseline",
        files=["backend/app/storage/file_state.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-ch01-migration-baseline may not change "
        "backend/app/storage/file_state.py."
    ]


def test_issue39_context4_issue68_branch_allows_backup_restore_drill_artifacts(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context4-backup-restore-drill",
        files=[
            "docs/ADR/0011-context4-backup-restore-drill.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context4_issue68_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context4-backup-restore-drill",
        files=["backend/app/stage7.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context4-backup-restore-drill may not change backend/app/stage7.py."
    ]


def test_issue39_restore_local_drill_branch_allows_local_restore_drill_artifacts(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-restore-local-drill",
        files=[
            "backend/app/storage/__init__.py",
            "backend/app/storage/local_restore_drill.py",
            "docs/ADR/0023-local-restore-integrity-drill.md",
            "docs/LOCAL_DEVELOPMENT.md",
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_local_restore_drill.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_restore_local_drill_branch_rejects_unrelated_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-restore-local-drill",
        files=["backend/app/stage7.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-restore-local-drill may not change backend/app/stage7.py."
    ]


def test_issue39_context5_issue69_branch_allows_metrics_slos_watch_planning_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context5-metrics-slos-watch",
        files=[
            "docs/ADR/0012-context5-metrics-slos-watch.md",
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context5_issue69_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context5-metrics-slos-watch",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context5-metrics-slos-watch may not change backend/app/stage4.py."
    ]


def test_issue39_context6_issue70_branch_allows_planning_and_governance_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context6-media-provider-posture-retention",
        files=[
            "docs/STATUS.md",
            "docs/TRACEABILITY.md",
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
            "scripts/quality/check_phase1_closure_docs.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context6_issue70_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context6-media-provider-posture-retention",
        files=["backend/app/stage7.py", "backend/app/main.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context6-media-provider-posture-retention may not change backend/app/stage7.py.",
        "Phase 1 Closure branch phase-1-closure-39-context6-media-provider-posture-retention may not change backend/app/main.py.",
    ]


def test_issue39_context0_branch_allows_targeted_process_and_skill_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        files=[
            ".github/workflows/quality.yml",
            ".github/workflows/security.yml",
            "docs/ENGINEERING_PROCESS_RCA.md",
            "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
            "docs/PROJECT_LEARNINGS_TRACKER.md",
            "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
            "docs/SKILLS_AND_CODEX_SETUP.md",
            "docs/SKILL_EXECUTION_PLAN.md",
            "docs/SKILL_LOCK.md",
            "docs/SKILL_TRUST_REVIEW.md",
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
            "scripts/guardrails_check.py",
            "tests/unit/test_guardrails_check.py",
            "tests/unit/test_phase1_closure_docs.py",
        ],
    )

    assert failures == []


def test_issue39_context0_branch_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        files=["backend/app/stage4.py"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context0-production-durability may not change backend/app/stage4.py."
    ]


def test_issue39_context0_branch_still_rejects_unrelated_docs(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        files=["docs/unrelated-process-note.md"],
    )

    assert failures == [
        "Phase 1 Closure branch phase-1-closure-39-context0-production-durability may not change "
        "docs/unrelated-process-note.md."
    ]


def test_workflow_pull_request_edited_detected_from_multiline_yaml(monkeypatch: Any) -> None:
    workflow_text = """
name: test

on:
  pull_request:
    types:
      - opened
      - edited
"""

    assert phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_detected_from_inline_yaml_list(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    types: [opened, synchronize, edited, reopened]
"""

    assert phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_missing_is_detected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    types:
      - opened
      - synchronize
      - reopened
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_inline_comment_decoy_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    types: [opened, synchronize] # , edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_decoy_under_jobs_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  push:
    branches: [main]

jobs:
  test:
    pull_request:
      types: [edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_decoy_under_push_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  push:
    pull_request:
      types: [edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


def test_workflow_pull_request_edited_nested_decoy_under_pull_request_is_rejected(monkeypatch: Any) -> None:
    workflow_text = """
on:
  pull_request:
    branches:
      types: [edited]
"""

    assert not phase1.workflow_has_pull_request_edited(workflow_text)


@pytest.mark.parametrize("workflow_path", [".github/workflows/quality.yml", ".github/workflows/security.yml"])
def test_process_docs_rejects_guardrail_workflow_without_pull_request_edited(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("edited, ", "").replace(", edited", ""),
        },
    )

    assert f"{workflow_path} must rerun guardrails on pull_request.edited" in failures


@pytest.mark.parametrize("workflow_path", [".github/workflows/quality.yml", ".github/workflows/security.yml"])
def test_process_docs_rejects_guardrail_workflow_without_token_permissions(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("  issues: read\n", "").replace("  pull-requests: read\n", ""),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


@pytest.mark.parametrize("workflow_path", [".github/workflows/quality.yml", ".github/workflows/security.yml"])
def test_process_docs_rejects_commented_guardrail_token_permissions(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("  issues: read\n", "  # issues: read\n").replace(
                "  pull-requests: read\n",
                "  # pull-requests: read\n",
            ),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


@pytest.mark.parametrize("workflow_path", [".github/workflows/quality.yml", ".github/workflows/security.yml"])
def test_process_docs_rejects_permission_decoys_outside_permissions_block(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("  issues: read\n", "").replace(
                "  pull-requests: read\n",
                "  env:\n    issues: read\n    pull-requests: read\n",
            ),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/quality-gates.yml",
        ".github/workflows/security.yml",
    ],
)
def test_process_docs_rejects_guardrail_step_without_token_even_when_other_steps_have_token(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: remove_guardrail_step_token(workflow_text),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/quality-gates.yml",
        ".github/workflows/security.yml",
    ],
)
def test_process_docs_rejects_commented_guardrail_step_token(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("          GITHUB_TOKEN:", "          # GITHUB_TOKEN:"),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/quality-gates.yml",
        ".github/workflows/security.yml",
    ],
)
def test_process_docs_rejects_empty_guardrail_step_token_with_decoy_token_text(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-context0-production-durability",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace(
                "          GITHUB_TOKEN: ${{ github.token }}",
                "          GITHUB_TOKEN: \"\"\n          DECOY_TOKEN_TEXT: github.token",
            ),
        },
    )

    assert (
        f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails"
        in failures
    )


def test_quality_gates_workflow_must_pass_base_sha_to_make_quality(monkeypatch: Any) -> None:
    workflow_path = ".github/workflows/quality-gates.yml"
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace(
                    "          GITHUB_BASE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}\n",
                "",
            ),
        },
    )

    assert f"{workflow_path} must pass GITHUB_BASE_SHA to make quality" in failures

@pytest.mark.parametrize(("old", "new"), (("NARRATWIN_HEAD_REF:", "REMOVED_NARRATWIN_HEAD_REF:"), ('run: GITHUB_HEAD_REF="$NARRATWIN_HEAD_REF" make quality', 'run: GITHUB_HEAD_REF="$NARRATWIN_HEAD_REF" make quality && echo unsafe')))
def test_stage_quality_bridge_rejects_missing_source_and_command_suffix(old: str, new: str) -> None:
    workflow = phase1.read(".github/workflows/quality-gates.yml")
    assert phase1.workflow_has_stage_quality_base_sha(workflow) and not phase1.workflow_has_stage_quality_base_sha(workflow.replace(old, new, 1))


def test_quality_gates_workflow_must_run_for_phase1_stacked_pull_request_bases(monkeypatch: Any) -> None:
    workflow_path = ".github/workflows/quality-gates.yml"
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("      - phase-1-closure-**\n", ""),
        },
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


def test_quality_gates_workflow_rejects_phase1_base_pattern_outside_pull_request_branches(monkeypatch: Any) -> None:
    workflow_path = ".github/workflows/quality-gates.yml"
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace(
        "      - phase-1-closure-**\n",
        "  # decoy only: phase-1-closure-**\n",
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


def test_quality_gates_workflow_rejects_inline_comment_phase1_base_decoy(monkeypatch: Any) -> None:
    workflow_path = ".github/workflows/quality-gates.yml"
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace(
        "      - main\n      - phase-1-closure-**\n",
        "      - main # phase-1-closure-**\n",
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


def test_quality_gates_workflow_rejects_nested_phase1_base_decoy(monkeypatch: Any) -> None:
    workflow_path = ".github/workflows/quality-gates.yml"
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace(
        "    branches:\n      - main\n      - phase-1-closure-**\n",
        "    types:\n      branches: [phase-1-closure-**]\n",
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


def test_quality_gates_workflow_rejects_pull_request_nested_under_push_decoy(monkeypatch: Any) -> None:
    workflow_path = ".github/workflows/quality-gates.yml"
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace("      - phase-1-closure-**\n", "").replace(
        "  push:\n",
        "  push:\n    pull_request:\n      branches: [phase-1-closure-**]\n",
        1,
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        ".github/workflows/eval-smoke.yml",
    ],
)
def test_runtime_workflows_must_run_for_phase1_stacked_pull_request_bases(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={
            workflow_path: workflow_text.replace("      - phase-1-closure-**\n", ""),
        },
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        ".github/workflows/eval-smoke.yml",
    ],
)
def test_runtime_workflows_reject_phase1_base_pattern_outside_pull_request_branches(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace(
        "      - phase-1-closure-**\n",
        "  # decoy only: phase-1-closure-**\n",
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        ".github/workflows/eval-smoke.yml",
    ],
)
def test_runtime_workflows_reject_inline_comment_phase1_base_decoy(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace(
        "      - main\n      - phase-1-closure-**\n",
        "      - main # phase-1-closure-**\n",
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        ".github/workflows/eval-smoke.yml",
    ],
)
def test_runtime_workflows_reject_nested_phase1_base_decoy(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace(
        "    branches:\n      - main\n      - phase-1-closure-**\n",
        "    types:\n      branches: [phase-1-closure-**]\n",
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        ".github/workflows/eval-smoke.yml",
    ],
)
def test_runtime_workflows_reject_pull_request_nested_under_push_decoy(
    monkeypatch: Any,
    workflow_path: str,
) -> None:
    workflow_text = phase1.read(workflow_path)
    decoy_workflow = workflow_text.replace("      - phase-1-closure-**\n", "").replace(
        "  push:\n",
        "  push:\n    pull_request:\n      branches: [phase-1-closure-**]\n",
        1,
    )
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-39-execution-strategy",
        changed=[workflow_path],
        read_overrides={workflow_path: decoy_workflow},
    )

    assert f"{workflow_path} must run for phase-1-closure stacked pull request bases" in failures


def remove_guardrail_step_token(workflow_text: str) -> str:
    lines = workflow_text.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        step_match = re.match(r"^(?P<indent>\s*)-\s+name:\s+.*$", line)
        if not step_match:
            output.append(line)
            index += 1
            continue
        step_indent = len(step_match.group("indent"))
        block = [line]
        index += 1
        while index < len(lines):
            current = lines[index]
            if current.strip() and not current.lstrip().startswith("#"):
                current_indent = len(current) - len(current.lstrip(" "))
                if current_indent <= step_indent:
                    break
            block.append(current)
            index += 1
        if any("scripts/guardrails_check.py" in item for item in block):
            block = [item for item in block if "GITHUB_TOKEN:" not in item]
        output.extend(block)
    return "\n".join(output) + "\n"


def test_process_docs_rejects_missing_validation_command(monkeypatch: Any) -> None:
    original_template = phase1.read(".github/pull_request_template.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=[
            "docs/ENGINEERING_PROCESS_RCA.md",
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        ],
        read_overrides={
            ".github/pull_request_template.md": replace_text(
                original_template,
                "uv run mypy scripts tests",
                "uv run mypy scripts scripts/unit",
            )
        },
    )

    assert ".github/pull_request_template.md Validation evidence section missing required commands:" in failures[0]


def test_process_docs_rejects_optional_branch_protection_validation_when_relevant(monkeypatch: Any) -> None:
    original_template = phase1.read(".github/pull_request_template.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=[
            "docs/ENGINEERING_PROCESS_RCA.md",
            "tests/unit/test_branch_protection_verifier.py",
        ],
        read_overrides={
            ".github/pull_request_template.md": replace_text(
                original_template,
                "# Optional when changed:\n# uv run pytest tests/unit/test_branch_protection_verifier.py",
                "# Optional when changed:\n# ",
            )
        },
    )

    assert (
        "Validation evidence section in .github/pull_request_template.md should include optional command "
        "uv run pytest tests/unit/test_branch_protection_verifier.py when branch-protection verifier evidence is relevant."
        in failures
    )


def test_process_docs_rejects_pending_matrix_template_status(monkeypatch: Any) -> None:
    original_playbook = phase1.read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        read_overrides={
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": replace_text(
                original_playbook,
                "| DERIVED-SOURCE-001 | Derived source binding | Source run, retrieved context refs, evaluation status/checksum, citation indexes, and claim-support records stay bound to the derived artifact | A valid export/artifact ID can replay with source evidence from another run | `test_replay_valid_source_bound_artifact` | `test_drop_artifact_with_mismatched_source_run`; break-test proves old behavior failed | `make test`; source-evidence gate | owner | pass |",
                "| DERIVED-SOURCE-001 | Derived source binding | Source run, retrieved context refs, evaluation status/checksum, citation indexes, and claim-support records stay bound to the derived artifact | A valid export/artifact ID can replay with source evidence from another run | `test_replay_valid_source_bound_artifact` | `test_drop_artifact_with_mismatched_source_run`; break-test proves old behavior failed | `make test`; source-evidence gate | owner | pending |",
            )
        },
    )

    assert (
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md matrix row DERIVED-SOURCE-001 must use status pass, not pending."
        in failures
    )


def test_process_docs_rejects_matrix_template_without_source_binding(monkeypatch: Any) -> None:
    original_rca = phase1.read("docs/ENGINEERING_PROCESS_RCA.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/ENGINEERING_PROCESS_RCA.md"],
        read_overrides={
            "docs/ENGINEERING_PROCESS_RCA.md": replace_text(
                original_rca,
                "Source run, retrieved context refs, evaluation ID/status/checksum, citation indexes, and claim-support records agree before translated or subtitle artifacts replay",
                "Source artifact, retrieved context refs, evaluation ID/status/checksum, citation indexes, and claim-support records agree before translated or subtitle artifacts replay",
            )
        },
    )

    assert (
        "docs/ENGINEERING_PROCESS_RCA.md matrix template missing one row with required binding terms: source run, retrieved context, evaluation, citation, claim-support"
        in failures
    )


def test_process_docs_rejects_duplicate_matrix_template_id(monkeypatch: Any) -> None:
    original_playbook = phase1.read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        read_overrides={
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": replace_text(
                original_playbook,
                "| DERIVED-SOURCE-001 | Derived source binding |",
                "| DERIVED-ARTIFACT-001 | Derived source binding |",
            )
        },
    )

    assert "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md matrix row duplicates ID: DERIVED-ARTIFACT-001" in failures


def test_process_docs_rejects_agents_missing_merge_closeout_follow_up_marker(monkeypatch: Any) -> None:
    original_agents = phase1.read("AGENTS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-89-implicit-merge-closeout",
        changed=["AGENTS.md"],
        read_overrides={
            "AGENTS.md": replace_text(
                original_agents,
                "new issue, branch, or pull request",
                "follow-up governance work",
            )
        },
    )

    assert "AGENTS.md missing process marker: new issue, branch, or pull request" in failures


def test_process_docs_rejects_playbook_missing_merge_closeout_follow_up_marker(monkeypatch: Any) -> None:
    original_playbook = phase1.read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-89-implicit-merge-closeout",
        changed=["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"],
        read_overrides={
            "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": replace_text(
                original_playbook,
                "required follow-up issue/branch/PR",
                "required follow-up work",
            )
        },
    )

    assert (
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md missing merge-closeout marker: "
        "open the required follow-up issue/branch/pr"
    ) in failures


def test_process_docs_rejects_open_medium_low_phf_register_status(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "| PHF-013 | Medium | Closed by local edits |",
                "| PHF-013 | Medium | Needs triage |",
            )
        },
    )

    assert "PHF-013 must be closed or superseded in the findings register; got needs triage." in failures


def test_process_docs_rejects_placeholder_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_nontrivial_pull_request_rejects_missing_validation_evidence_commands` fails actual PR bodies without command evidence; `test_process_docs_rejects_missing_validation_command` and `test_process_docs_rejects_optional_branch_protection_validation_when_relevant` enforce template/gate command evidence.",
                "TBD",
            )
        },
    )

    assert "PHF-011 Medium/Low matrix has placeholder automated test / guardrail." in failures


def test_process_docs_rejects_bare_scripts_directory_as_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_workflow_pull_request_edited_detected_from_inline_yaml_list`, `test_workflow_pull_request_edited_detected_from_multiline_yaml`, and `test_workflow_pull_request_edited_missing_is_detected` verify parsed workflow events; table-header checks now fail on missing required section columns.",
                "`scripts/`",
            )
        },
    )

    assert "PHF-012 Medium/Low matrix must map to an automated test/guardrail or human-only surface." in failures


def test_process_docs_rejects_nonexistent_test_name_as_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_process_docs_rejects_missing_validation_command`",
                "`test_this_does_not_exist_anywhere`",
            )
        },
    )

    assert "PHF-011 Medium/Low matrix cites unknown test evidence: test_this_does_not_exist_anywhere" in failures


def test_process_docs_rejects_nonexistent_test_name_on_human_only_phf_row(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_process_docs_rejects_pending_matrix_template_status`",
                "`test_this_human_only_row_fake_does_not_exist`",
            )
        },
    )

    assert (
        "PHF-008 Medium/Low matrix cites unknown test evidence: "
        "test_this_human_only_row_fake_does_not_exist"
    ) in failures


def test_process_docs_rejects_nonexistent_script_as_phf_matrix_evidence(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "table-header checks now fail on missing required section columns.",
                "`scripts/quality/does_not_exist.py`",
            )
        },
    )

    assert "PHF-012 Medium/Low matrix cites missing script evidence: scripts/quality/does_not_exist.py" in failures


def test_process_docs_rejects_nonexistent_script_on_human_only_phf_row(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "guardrail tests reject partial matrix-ID coverage",
                "`scripts/quality/does_not_exist_for_human_only.py` rejects partial matrix-ID coverage",
            )
        },
    )

    assert (
        "PHF-008 Medium/Low matrix cites missing script evidence: "
        "scripts/quality/does_not_exist_for_human_only.py"
    ) in failures


def test_process_docs_rejects_nonexistent_pytest_node_id_target(monkeypatch: Any) -> None:
    original_findings = phase1.read("docs/reviews/PROCESS_HARDENING_FINDINGS.md")
    failures = run_process_docs_check(
        monkeypatch,
        branch="phase-1-closure-process-60-phf-hardening-docs",
        changed=["docs/reviews/PROCESS_HARDENING_FINDINGS.md"],
        read_overrides={
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md": replace_text(
                original_findings,
                "`test_process_docs_rejects_matrix_template_without_source_binding`",
                "uv run pytest tests/unit/does_not_exist.py::test_missing",
            )
        },
    )

    assert "PHF-007 Medium/Low matrix cites missing pytest target: tests/unit/does_not_exist.py" in failures


def test_phf_automated_evidence_rejects_non_path_pytest_target() -> None:
    failures = phase1.phf_automated_evidence_failures("PHF-X", "uv run pytest not_a_real_target")

    assert "PHF-X Medium/Low matrix cites unsupported pytest target: not_a_real_target" in failures


def test_phf_automated_evidence_rejects_pytest_node_id_test_from_wrong_file() -> None:
    failures = phase1.phf_automated_evidence_failures(
        "PHF-X",
        "uv run pytest tests/unit/test_guardrails_check.py::"
        "test_workflow_pull_request_edited_decoy_under_jobs_is_rejected",
    )

    assert (
        "PHF-X Medium/Low matrix cites pytest node id with test outside target: "
        "tests/unit/test_guardrails_check.py::test_workflow_pull_request_edited_decoy_under_jobs_is_rejected"
    ) in failures


def test_phf_automated_evidence_accepts_dot_prefixed_pytest_target() -> None:
    failures = phase1.phf_automated_evidence_failures(
        "PHF-X",
        "uv run pytest "
        "./tests/unit/test_phase1_closure_docs.py::test_phf_automated_evidence_accepts_dot_prefixed_pytest_target",
    )

    assert failures == []
