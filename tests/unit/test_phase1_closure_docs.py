import importlib.util
import json
import re
import subprocess
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


def run_issue158_security_history_check(
    monkeypatch: Any, *, read_overrides: dict[str, str] | None = None
) -> list[str]:
    if read_overrides:
        monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_issue158_security_history_contract(failures)
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


def run_issue278_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue278_c3a_r2_preflight(failures)
    return failures


def run_issue280_review_artifacts_check(
    monkeypatch: Any, *, read_overrides: dict[str, str] | None = None
) -> list[str]:
    if read_overrides:
        monkeypatch.setattr(phase1, "read", read_with_overrides(phase1, read_overrides))
    failures: list[str] = []
    phase1.check_issue280_review_artifacts(failures)
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


def run_issue267_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue267_c3a_cp7_preflight(failures)
    return failures


def run_issue269_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue269_c3a_cp8_preflight(failures)
    return failures


def run_issue274_preflight_check(
    monkeypatch: Any, *, preflight_text: str | None = None, missing: bool = False
) -> list[str]:
    if preflight_text is not None:
        monkeypatch.setattr(
            phase1,
            "read",
            read_with_overrides(
                phase1,
                {"docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md": preflight_text},
            ),
        )
    failures: list[str] = []
    if missing:
        original_is_file = cast(Callable[[Path], bool], phase1.Path.is_file)

        def patched_is_file(path: Path) -> bool:
            if str(path).endswith("docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md"):
                return False
            return original_is_file(path)

        monkeypatch.setattr(phase1.Path, "is_file", patched_is_file)
    phase1.check_issue274_c3b_pr1_preflight(failures)
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
| ISSUE8-01 | #8 | PRD names both product modes | docs/PRD.md#6-product-modes |
| ISSUE8-02 | #8 | Project-avatar-pack contract is documented | docs/PROJECT_AVATAR_PACK.md |
| ISSUE8-03 | #8 | Roadmap preserves focused Slice 1 and later video/interactive phases | docs/ROADMAP.md#product-mode-alignment |
| ISSUE8-04 | #8 | AI build brief preserves the full product vision | docs/AI_BUILD_BRIEF.md#product-modes-to-preserve |
| ISSUE8-05 | #8 | Skill plan requires PM/spec validation before coding | docs/SKILL_EXECUTION_PLAN.md#product-mode-policy-authority-handoff |
| ISSUE8-06 | #8 | No application code changes | Issue #311 exact governance-only branch gate |

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
            return text.replace("| ISSUE8-06 | #8 | No application code changes | Issue #311 exact governance-only branch gate |\n", ""), ["PHF020A.ACCEPTANCE.MISSING"]
        if selector == 1:
            return text.replace("| ISSUE8-04 | #8 | AI build brief preserves the full product vision |", "| ISSUE8-04 | #155 | AI build brief preserves the full product vision |"), ["PHF020A.ACCEPTANCE.SOURCE_INVALID"]
        return text.replace("No application code changes", f"Application code changes {seed}-{variant}"), ["PHF020A.ACCEPTANCE.ROW_INVALID"]
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


def test_issue_267_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-267-c3a-cp7-performance-probe"
    allowed = [
        "docs/governance/preflights/issue-267.json",
        "docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_performance.py",
    ]
    assert phase1.ISSUE_267_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_security_observability.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "frontend/package.json",
            "frontend/package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage4.py",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_security_observability.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage4.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_267_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-267-c3a-cp7-performance-probe-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-267.json",
            "docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "tests/acceptance/test_checkpoint3_performance.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-267.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_performance.py.",
    ]


def test_issue_269_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-269-c3a-cp8-real-browser-e2e"
    refresh_branch = "phase-1-closure-269-c3a-cp8-real-browser-e2e-refresh"
    allowed = [
        "docs/governance/preflights/issue-269.json",
        "docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md",
        "docs/ADR/0033-checkpoint3-real-browser-acceptance-evidence.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/playwright.checkpoint3.config.ts",
        "frontend/tests/checkpoint3-real-browser.spec.ts",
    ]
    assert phase1.ISSUE_269_ALLOWED_CHANGED_FILES == set(allowed)
    assert phase1.ISSUE_269_ALLOWED_BRANCHES == {branch, refresh_branch}
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(monkeypatch, branch=refresh_branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "tests/acceptance/test_checkpoint3_performance.py",
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "backend/Dockerfile",
            "pyproject.toml",
            "uv.lock",
            "backend/app/stage4.py",
            "backend/app/stage6.py",
            "backend/app/stage7.py",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change tests/acceptance/test_checkpoint3_performance.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change backend/Dockerfile.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage4.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {branch} may not change backend/app/stage7.py.",
    ]


def test_issue_269_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-269-c3a-cp8-real-browser-e2e-extra"
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            "docs/governance/preflights/issue-269.json",
            "docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md",
            "docs/STATUS.md",
            "scripts/quality/check_checkpoint3_acceptance.py",
            "frontend/playwright.checkpoint3.config.ts",
            "frontend/tests/checkpoint3-real-browser.spec.ts",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-269.json.",
        f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md.",
        f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
        f"Phase 1 Closure branch {branch} may not change scripts/quality/check_checkpoint3_acceptance.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/playwright.checkpoint3.config.ts.",
        f"Phase 1 Closure branch {branch} may not change frontend/tests/checkpoint3-real-browser.spec.ts.",
    ]


def test_issue_276_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-c3a-r1-major-market-multilingual-output-correctness"
    allowed = [
        "backend/app/main.py",
        "backend/app/rag/chunking.py",
        "backend/app/rag/models.py",
        "backend/app/rag/providers.py",
        "backend/app/stage4.py",
        "backend/app/stage6.py",
        "docs/EVAL_REPORT.md",
        "docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md",
        "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
        "docs/governance/preflights/issue-276.json",
        "docs/ADR/0033-checkpoint3-real-browser-acceptance-evidence.md",
        "docs/QUALITY_GATES.md",
        "docs/reviews/ISSUE_276_C3A_R1_PR_BODY.md",
        "docs/reviews/ISSUE_276_C3A_R1_PREFLIGHT.md",
        "docs/reviews/ISSUE_276_C3A_R1_REVIEW_EVIDENCE.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "frontend/src/app/page.module.css",
        "frontend/src/app/page.test.tsx",
        "frontend/src/app/page.tsx",
        "frontend/tests/checkpoint3-real-browser.spec.ts",
        "frontend/tests/real-stack.spec.ts",
        "frontend/tests/smoke.spec.ts",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/acceptance/test_checkpoint3_output_correctness.py",
        "tests/acceptance/test_checkpoint3_media_artifacts.py",
        "tests/api/test_stage4_slice_api.py",
        "tests/api/test_stage6_multilingual_api.py",
        "tests/api/test_stage7_avatar_api.py",
        "tests/fixtures/stage4_project.md",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_chunking.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_retrieval_and_grounding.py",
        "tests/unit/test_stage6_multilingual.py",
    ]

    assert phase1.ISSUE_276_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "frontend/package.json",
            "docs/THIRD_PARTY_NOTICES.md",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change frontend/package.json.",
        f"Phase 1 Closure branch {branch} may not change docs/THIRD_PARTY_NOTICES.md.",
    ]


def test_issue_274_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-c3b-pr1-consent-provenance-planning-274"
    allowed = [
        "docs/governance/preflights/issue-274.json",
        "docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    ]
    assert phase1.ISSUE_274_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "backend/app/main.py",
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "pyproject.toml",
            "uv.lock",
            "docs/THIRD_PARTY_NOTICES.md",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change backend/app/main.py.",
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
        f"Phase 1 Closure branch {branch} may not change docs/THIRD_PARTY_NOTICES.md.",
    ]


def test_issue_274_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    files = [
        "docs/governance/preflights/issue-274.json",
        "docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
    ]
    for branch in (
        "phase-1-closure-c3b-pr1-consent-provenance-planning-274-extra",
        "phase-1-closure-process-274-c3b-pr1-consent-provenance-planning",
        "phase-1-closure-c3b-pr1-consent-provenance-planning-0274",
        "phase-1-closure-274-c3b-pr1-consent-provenance-planning",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=files) == [
            f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-274.json.",
            f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md.",
            f"Phase 1 Closure branch {branch} may not change docs/STATUS.md.",
            f"Phase 1 Closure branch {branch} may not change scripts/quality/check_phase1_closure_docs.py.",
        ]


def test_issue_278_branch_has_exact_scope_allowlist(monkeypatch: Any) -> None:
    branch = "phase-1-closure-278-c3a-r2-full-project-multilingual-corpus"
    allowed = [
        "docs/governance/preflights/issue-278.json",
        "docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md",
        "docs/reviews/ISSUE_278_C3A_R2_REVIEW_EVIDENCE.md",
        "docs/demo/CHECKPOINT3A_FULL_PROJECT_MULTILINGUAL_REHEARSAL_CHECKLIST.md",
        "docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/ADR/0034-c3a-r2-full-project-multilingual-gate.md",
        "backend/app/stage6.py",
        "scripts/quality/check_checkpoint3_acceptance.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/fixtures/checkpoint3_full_project_multilingual_corpus.json",
        "tests/unit/test_checkpoint3_acceptance_gate.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_stage6_multilingual.py",
        "tests/api/test_stage6_multilingual_api.py",
        "tests/acceptance/test_checkpoint3_output_correctness.py",
        "tests/acceptance/test_checkpoint3_full_project_multilingual.py",
        "reports/checkpoint3-multilingual/full-project-coverage-matrix.json",
        "reports/checkpoint3-multilingual/full-project-correctness-report.json",
    ]

    assert phase1.ISSUE_278_ALLOWED_CHANGED_FILES == set(allowed)
    assert run_changed_files_check(monkeypatch, branch=branch, files=allowed) == []
    assert run_changed_files_check(
        monkeypatch,
        branch=branch,
        files=[
            *allowed,
            "frontend/src/app/page.tsx",
            ".github/workflows/quality-gates.yml",
            "docs/THIRD_PARTY_NOTICES.md",
            "pyproject.toml",
            "uv.lock",
        ],
    ) == [
        f"Phase 1 Closure branch {branch} may not change frontend/src/app/page.tsx.",
        f"Phase 1 Closure branch {branch} may not change .github/workflows/quality-gates.yml.",
        f"Phase 1 Closure branch {branch} may not change docs/THIRD_PARTY_NOTICES.md.",
        f"Phase 1 Closure branch {branch} may not change pyproject.toml.",
        f"Phase 1 Closure branch {branch} may not change uv.lock.",
    ]


def test_issue_278_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    files = [
        "docs/governance/preflights/issue-278.json",
        "docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md",
        "backend/app/stage6.py",
        "tests/acceptance/test_checkpoint3_full_project_multilingual.py",
    ]
    for branch in (
        "phase-1-closure-278-c3a-r2-full-project-multilingual-corpus-extra",
        "phase-1-closure-process-278-c3a-r2-full-project-multilingual-corpus",
        "phase-1-closure-0278-c3a-r2-full-project-multilingual-corpus",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=files) == [
            f"Phase 1 Closure branch {branch} may not change docs/governance/preflights/issue-278.json.",
            f"Phase 1 Closure branch {branch} may not change docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md.",
            f"Phase 1 Closure branch {branch} may not change backend/app/stage6.py.",
            (
                f"Phase 1 Closure branch {branch} may not change "
                "tests/acceptance/test_checkpoint3_full_project_multilingual.py."
            ),
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


def test_issue_267_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue267_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://docs.python.org/3/library/time.html#time.perf_counter_ns",
        "C3A-CP7-HARNESS-001",
        "C3A-CP7-FM-002",
        "tests/acceptance/test_checkpoint3_performance.py::test_checkpoint3_performance_executes_runtime_api_critical_path",
        "tests/acceptance/test_checkpoint3_performance.py::test_checkpoint3_performance_rejects_static_or_unbound_evidence",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_performance_evidence_fields",
        "runtime API-visible timings",
        "explicit thresholds",
        "operation names",
        "run/request IDs",
        "local/mock posture",
        "docs/prose/static-snapshot",
        "style-only/status-only",
        "canned success",
        "runtime nonce",
        "source/run binding",
        "cross-project replay",
        "stale performance evidence",
        "timeout/subprocess failures",
        "raw uploaded content",
        "prompt-injection text",
        "sensitive tokens",
        "no hosted deployment",
        "no provider setup",
        "no cloned identity",
        "no production-readiness claim",
        "Issue #249 remains open",
        "Cross-model review is skipped in this autonomous execution context",
        "Stop and open a new issue",
    ),
)
def test_issue_267_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue267_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_267_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue267_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP7 preflight artifact: docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md"
    ]


def test_issue_269_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue269_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://playwright.dev/docs/test-webserver",
        "https://playwright.dev/docs/network",
        "https://playwright.dev/docs/api/class-page#page-route",
        "C3A-CP8-HARNESS-001",
        "C3A-CP8-BROWSER-001",
        "C3A-CP8-NO-INTERCEPTION-001",
        "C3A-CP8-FM-002",
        "C3A-CP8-FM-003",
        "frontend/tests/checkpoint3-real-browser.spec.ts",
        "frontend/playwright.checkpoint3.config.ts",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_all_checkpoint3a_probes",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_browser_probe_api_only_or_static_commands",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_real_browser_e2e_fields",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_skipped_cp8_browser_probe",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_zero_exit_without_browser_evidence",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_minimal_success_shaped_evidence",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_evidence_without_nonce_request_binding",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_cp8_evidence_without_idempotency_binding",
        "tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_browser_config_forces_local_mock_environment",
        "real Playwright browser test",
        "no `page.route`",
        "no `context.route`",
        "no `route.fulfill`",
        "no HAR replay",
        "no MSW success mock",
        "runtime nonce",
        "upload request payload nonce",
        "independently recomputed idempotency evidence",
        "API request sequence",
        "source/eval binding",
        "artifact metadata",
        "bounded ops/status",
        "docs/prose/static-snapshot",
        "API-only tests",
        "route/network interception",
        "canned success",
        "stale evidence",
        "cross-project replay",
        "raw uploaded content",
        "prompt-injection text",
        "sensitive tokens",
        "generated full script text",
        "browser/server failures",
        "no hosted deployment",
        "no provider setup",
        "no cloned identity",
        "no production-readiness claim",
        "Issue #249 remains open",
        "Final sub-agent fan-out findings were accepted and fixed",
        "Stop and open a new issue",
    ),
)
def test_issue_269_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue269_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_269_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue269_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-CP8 preflight artifact: docs/reviews/ISSUE_269_C3A_CP8_PREFLIGHT.md"
    ]


def test_issue_274_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue274_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue",
        "https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/using-keywords-in-issues-and-pull-requests",
        "C3B-PR1-LEDGER-001",
        "C3B-PR1-C3A-001",
        "C3B-PR1-BOUNDARY-001",
        "C3B-PR1-GUARDRAIL-001",
        "C3B-PR1-NONGOAL-001",
        "C3B-PR1-PUBLICSAFE-001",
        "C3B-PR1-TRACKER-001",
        "C3B-PR1-FM-001",
        "C3B-PR1-FM-008",
        "tests/unit/test_phase1_closure_docs.py::test_issue_274_branch_has_exact_scope_allowlist",
        "tests/unit/test_phase1_closure_docs.py::test_issue_274_near_match_branch_fails_closed",
        "RED confirmed before checker update",
        "Four sub-agent reviews covered public-safe scope",
        "Final pre-human-review fan-out is clean",
        "public/private boundary",
        "C3A completion wording without overclaim",
        "C3B consent/provenance planning scope",
        "cloned-identity implementation exclusion",
        "provider/hosted/public/production exclusion",
        "issue `#249` tracker status",
        "issue `#269`/PR `#273` ledger reconciliation",
        "guardrail allowlist behavior",
        "status/traceability consistency",
        "test/quality/CI",
        "governance/taste/scope",
        "Stop and open a new issue",
    ),
)
def test_issue_274_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue274_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_274_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue274_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3B-PR1 preflight artifact: docs/reviews/ISSUE_274_C3B_PR1_PREFLIGHT.md"
    ]


def test_issue_278_preflight_contract_is_complete(monkeypatch: Any) -> None:
    text = Path("docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue278_preflight_check(monkeypatch, preflight_text=text) == []


@pytest.mark.parametrize(
    "marker",
    (
        "C3A-R2-CATALOG-001",
        "C3A-R2-FULLPROJECT-001",
        "C3A-R2-ALL-SUPPORTED-001",
        "C3A-R2-STALENESS-001",
        "C3A-R2-PARITY-001",
        "C3A-R2-FM-001",
        "C3A-R2-FM-018",
        "tests/fixtures/checkpoint3_full_project_multilingual_corpus.json",
        "tests/acceptance/test_checkpoint3_full_project_multilingual.py",
        "reports/checkpoint3-multilingual/full-project-coverage-matrix.json",
        "reports/checkpoint3-multilingual/full-project-correctness-report.json",
        "LANGUAGE_CATALOG",
        "LANGUAGE_CATALOG_BY_TAG",
        "SUPPORTED_LANGUAGES",
        "local_demo_support_status",
        "provider_support_status",
        "test_coverage_level",
        "Hindi/Devanagari",
        "RTL",
        "CJK",
        "Latin-script",
        "Priority 2 refusal",
        "fixture hash changed",
        "expected-output hash changed",
        "language catalog version changed",
        "validator version changed",
        "artifact schema version changed",
        "report schema changed",
        "metadata-only success",
        "artifact-only success",
        "citation id preservation without source-span preservation",
        "UI transcript, stored output, metadata, durable report, and exported/downloaded artifacts agree",
        "does not prove arbitrary-project translation quality",
        "does not prove provider quality",
        "does not authorize hosted/public demo",
        "raw uploaded knowledge-document translation API",
        "Final clean fan-out",
        "Stop and open a new issue",
    ),
)
def test_issue_278_preflight_contract_rejects_missing_markers(
    monkeypatch: Any, marker: str
) -> None:
    text = Path("docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md").read_text(encoding="utf-8")

    assert run_issue278_preflight_check(
        monkeypatch, preflight_text=remove_normalized_marker(text, marker)
    )


def test_issue_278_missing_preflight_reports_failure(monkeypatch: Any) -> None:
    assert run_issue278_preflight_check(monkeypatch, missing=True) == [
        "Missing required C3A-R2 preflight artifact: docs/reviews/ISSUE_278_C3A_R2_PREFLIGHT.md"
    ]


def test_issue_278_phase_quality_runs_full_project_probe(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, "kwargs": kwargs})
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="7 passed")

    monkeypatch.setattr(phase1, "current_branch", lambda: phase1.ISSUE_278_BRANCH)
    monkeypatch.setattr(phase1.subprocess, "run", fake_run)
    failures: list[str] = []

    phase1.check_issue278_full_project_probe(failures)

    assert failures == []
    assert calls[0]["args"][0] == phase1.ISSUE_278_FULL_PROJECT_COMMAND
    assert calls[0]["kwargs"]["shell"] is False
    assert calls[0]["kwargs"]["timeout"] == 120
    assert calls[0]["kwargs"]["stdout"] is subprocess.PIPE
    assert calls[0]["kwargs"]["stderr"] is subprocess.STDOUT
    assert calls[0]["kwargs"]["text"] is True
    assert calls[0]["kwargs"]["cwd"] == phase1.ROOT


def test_issue_278_policy_only_quality_skips_uv_subprocess(monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, "kwargs": kwargs})
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="7 passed")

    monkeypatch.setattr(phase1, "current_branch", lambda: phase1.ISSUE_278_BRANCH)
    monkeypatch.setattr(phase1.subprocess, "run", fake_run)
    monkeypatch.setenv(phase1.POLICY_ONLY_ENV, "1")
    failures: list[str] = []

    phase1.check_issue278_full_project_probe(failures)

    assert failures == []
    assert calls == []


def test_issue_278_phase_quality_reports_full_project_probe_failure(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout="FAILED stale evidence")

    monkeypatch.setattr(phase1, "current_branch", lambda: phase1.ISSUE_278_BRANCH)
    monkeypatch.setattr(phase1.subprocess, "run", fake_run)
    failures: list[str] = []

    phase1.check_issue278_full_project_probe(failures)

    assert failures == ["C3A-R2 full-project multilingual corpus probe failed: FAILED stale evidence"]


def test_issue_278_report_artifacts_must_be_tracked(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "current_branch", lambda: phase1.ISSUE_278_BRANCH)
    monkeypatch.setattr(phase1, "run_git", lambda args: "" if args[0] == "ls-files" else "")
    failures: list[str] = []

    phase1.check_issue278_report_artifacts_tracked(failures)

    assert failures == [
        "C3A-R2 report artifact must be tracked by git: "
        "reports/checkpoint3-multilingual/full-project-coverage-matrix.json",
        "C3A-R2 report artifact must be tracked by git: "
        "reports/checkpoint3-multilingual/full-project-correctness-report.json",
    ]


def test_issue_278_report_artifacts_tracked_pass(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "current_branch", lambda: phase1.ISSUE_278_BRANCH)
    monkeypatch.setattr(phase1, "run_git", lambda args: args[-1] if args[0] == "ls-files" else "")
    failures: list[str] = []

    phase1.check_issue278_report_artifacts_tracked(failures)

    assert failures == []


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


def test_issue294_replacement_records_the_post322_live_ledger() -> None:
    status = Path("docs/STATUS.md").read_text(encoding="utf-8")
    stage = Path("docs/STAGE_ISSUE_PLAN.md").read_text(encoding="utf-8")
    traceability = Path("docs/TRACEABILITY.md").read_text(encoding="utf-8")
    normalized_status = re.sub(r"\s+", " ", status)
    normalized_stage = re.sub(r"\s+", " ", stage)

    for marker in (
        "| `#296` | Closed | Frontend brace-expansion audit unblock | Completed through merged PR `#297` at `cc89b2dd52da38e8d8a9acbd813e327737cf0ca1`",
        "| `#317` | Closed | Issue #280 semantic repair slice 1 | Completed through merged PR `#318` at `c293b4a62a5afdaf893af83f3f23efd65f11b950`",
        "| `#321` | Closed | Issue #317 renderer compatibility correction | Completed through merged PR `#322` at `704c5b9536c62e29ba7fd74c7344d067770c728e`",
        "Issue #298 remains open as the semantic multilingual gap tracker.",
        "PR #299 remains immutable open forensic evidence at head `f93653e8a11e697c88766b207fb01c18662339d6`",
        "The next product action requires a separately controlled, repository-owner-authorized Slice 2 issue, branch, and pull request.",
        "Before any Slice 2 controller is created, the Issue #294 replacement must pass merged-tree acceptance, PR #295 must close unmerged as superseded, and Issue #294 must close as satisfied by the replacement.",
    ):
        assert marker in normalized_status

    for stale in (
        "Issue `#300` is the active negative-forensic-only reset",
        "Issue `#317` remains open",
        "Once Issue #321's reviewed correction merges",
        "Until merge, this is an intended target state",
        "Close only after the reviewed correction merges",
        "Do not select a correction without the reserved owner decision",
    ):
        assert stale not in status

    for marker in (
        "Issue `#300` and PR `#301` are completed historical negative containment.",
        "Issue `#313` and PR `#314` completed the architecture and independent-oracle decision.",
        "Issue `#317` and PR `#318` completed the bounded Spanish `STANDARD` semantic slice.",
        "Issue `#321` and PR `#322` completed the renderer compatibility correction.",
        "Further product work requires a separately controlled, repository-owner-authorized Slice 2 issue, branch, and pull request.",
        "Before that controller is created, the Issue `#294` replacement must pass merged-tree acceptance, PR `#295` must close unmerged as superseded, and Issue `#294` must close as satisfied by the replacement.",
    ):
        assert marker in normalized_stage
    assert "Issue `#321` is the single post-merge corrective controller selected" not in stage

    assert (
        "| Phase 1 Closure / `#296` | Completed through PR `#297` at "
        "`cc89b2dd52da38e8d8a9acbd813e327737cf0ca1` |"
    ) in traceability
    assert "| Phase 1 Closure / `#296` | In progress |" not in traceability


def test_issue294_replacement_executable_ledger_rejects_fact_and_stale_mutations() -> None:
    documents = {
        rel: Path(rel).read_text(encoding="utf-8")
        for rel in (
            "docs/STATUS.md",
            "docs/STAGE_ISSUE_PLAN.md",
            "docs/TRACEABILITY.md",
        )
    }
    assert phase1.issue294_replacement_ledger_findings(documents) == []

    mutations = (
        ("docs/STATUS.md", "3b5b24a722beac6cfc6e586ecdc1d46757a5084d", "0" * 40),
        ("docs/STATUS.md", "84be60c6df59c4b482edc4cff5ae2bfd4ab54b25", "0" * 40),
        (
            "docs/STAGE_ISSUE_PLAN.md",
            "Issue `#300` and PR `#301` are completed historical negative containment.",
            "REMOVED",
        ),
        (
            "docs/STAGE_ISSUE_PLAN.md",
            "Issue `#313` and PR `#314` completed the architecture and independent-oracle\ndecision.",
            "REMOVED",
        ),
        (
            "docs/STAGE_ISSUE_PLAN.md",
            "Issue `#317` and PR `#318` completed the bounded Spanish `STANDARD` semantic\nslice.",
            "REMOVED",
        ),
        (
            "docs/STAGE_ISSUE_PLAN.md",
            "Further product work requires a separately\ncontrolled, repository-owner-authorized Slice 2 issue, branch, and pull request.",
            "REMOVED",
        ),
    )
    for rel, old, new in mutations:
        assert old in documents[rel]
        mutated = dict(documents)
        mutated[rel] = documents[rel].replace(old, new)
        assert phase1.issue294_replacement_ledger_findings(mutated)

    for rel, stale in (
        ("docs/STATUS.md", "Close only after the reviewed correction merges"),
        ("docs/STATUS.md", "Do not select a correction without the reserved owner decision"),
    ):
        mutated = dict(documents)
        mutated[rel] += f"\n{stale}\n"
        assert phase1.issue294_replacement_ledger_findings(mutated)


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
        "Issue `#265` is closed after PR `#266` merged the sixth Checkpoint 3A child implementation checkpoint",
        "Issue `#267` is closed after PR `#268` merged the seventh Checkpoint 3A child implementation checkpoint",
        "Issue `#269` is closed after PR `#273` merged the eighth Checkpoint 3A child implementation checkpoint",
        "Issue `#274` is satisfied by its prior reviewed PR as the public-safe Checkpoint 3B consent/provenance planning gate only",
        "Issue `#276` is closed after PR `#277` merged the Checkpoint 3A repair child for major-market multilingual output correctness",
        "Issue `#278` is closed after PR `#279` merged the bounded C3A-R2 full-project multilingual corpus gate",
            "Issue `#280` is closed in GitHub but not fixed",
        "PR `#281`",
        "`3058ea11a808fd7fbfbced3bd1ace07c96ef5f0c`",
        "post-merge main quality workflow run `30085558061` passing",
                "| SSV1-NEXT | next-action | repo owner | decision-required | decision-required |",
        "PR `#282`",
        "`b889604a490c9f014130e420c1c949af7879dd84`",
        "post-merge main quality workflow run `30092008592` passing",
        "PR `#283`",
        "`09584b264c0f30da3eecd6693829e5bcb071e568`",
        "post-merge main quality workflow run `30095714825` passing",
        "Issue `#278` is closed after PR `#279` merged the bounded C3A-R2 full-project multilingual corpus gate",
                "| `#313` | Closed | Issue #280 repair feasibility and independent semantic oracle |",
                "Issue #315 requires self-contained product and end-goal context",
                "Runtime and production authorization remain unchanged",
            "Issue #300 and PR #301 are completed historical negative-containment evidence",
            "The next product action requires a separately controlled, repository-owner-authorized Slice 2 issue, branch, and pull request",
        "full-project multilingual corpus gate",
        "ADR `0034`",
        "major-market multilingual output correctness",
        "`6390ac7c7bcd8fed353587df90e8fa98c2ffef05`",
        "post-merge main quality workflow run `30071081191` passing",
        "`da3efe71b39c1c03a0fd28748a1270ee175cc2dd`",
        "post-merge main quality workflow run `30079561208` passing",
        "`#254` | Merged | 2026-07-22",
        "`#258` | Merged | 2026-07-22",
        "`#260` | Merged | 2026-07-22",
        "`#262` | Merged | 2026-07-22",
        "`#264` | Merged | 2026-07-23",
        "`#266` | Merged | 2026-07-23",
        "`#268` | Merged | 2026-07-23",
        "`#273` | Merged | 2026-07-23",
        "`58e6ac473bb2cbcd5e99a64007a1cc862117217c`",
        "`de0cdb0c5337a980e478cb3e6b42d2b031909f31`",
        "`f79debb641e7198e2d1d41e210ddd537037c7699`",
        "`caa8183be7ebf3fa5a3cf34d653727cc5522bf7f`",
        "`0f737c564f9245b66640988573ac04f4432e06d5`",
        "post-merge main quality workflow run `29925008358` passing",
        "post-merge main quality workflow run `29937721472` passing",
        "post-merge main quality workflow run `29994103118` passing",
        "The current `make issue280-output-correctness` target is negative forensic integrity only",
        "consent/provenance planning",
        "acceptance contracts",
        "risk boundaries",
        "future issue sequencing",
        "real-browser E2E probe",
    ):
        assert marker in normalized_status
    assert "C3A-CP1 PR | Pending" not in normalized_status
    assert "Issue `#259` is satisfied by this PR when merged" not in normalized_status
    assert "Issue `#267` is satisfied by this PR when merged" not in normalized_status
    assert "Issue `#269` is satisfied by this PR when merged" not in normalized_status


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
            PHF020A_VALID_POLICY.replace("No application code changes", "Application code changes"),
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
                "| ISSUE8-06 | #8 | No application code changes | Issue #311 exact governance-only branch gate |\n",
                "| ISSUE8-06 | #8 | No application code changes | Issue #311 exact governance-only branch gate |\n| ISSUE8-06 | #8 | No application code changes | Issue #311 exact governance-only branch gate |\n",
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


ISSUE8_ORIGINAL_ACCEPTANCE_TRANSFER = {
    "ISSUE8-01": (
        "#8",
        "PRD names both product modes",
        "docs/PRD.md#6-product-modes",
    ),
    "ISSUE8-02": (
        "#8",
        "Project-avatar-pack contract is documented",
        "docs/PROJECT_AVATAR_PACK.md",
    ),
    "ISSUE8-03": (
        "#8",
        "Roadmap preserves focused Slice 1 and later video/interactive phases",
        "docs/ROADMAP.md#product-mode-alignment",
    ),
    "ISSUE8-04": (
        "#8",
        "AI build brief preserves the full product vision",
        "docs/AI_BUILD_BRIEF.md#product-modes-to-preserve",
    ),
    "ISSUE8-05": (
        "#8",
        "Skill plan requires PM/spec validation before coding",
        "docs/SKILL_EXECUTION_PLAN.md#product-mode-policy-authority-handoff",
    ),
    "ISSUE8-06": (
        "#8",
        "No application code changes",
        "Issue #311 exact governance-only branch gate",
    ),
}


def issue8_documents() -> dict[str, str]:
    return {
        rel: Path(rel).read_text(encoding="utf-8")
        for rel in (
            "docs/PRD.md",
            "docs/PROJECT_AVATAR_PACK.md",
            "docs/ROADMAP.md",
            "docs/AI_BUILD_BRIEF.md",
            "docs/SKILL_EXECUTION_PLAN.md",
        )
    }


def test_issue311_original_issue8_acceptance_contract_is_current() -> None:
    assert phase1.PHF020A_ACCEPTANCE_TRANSFER == ISSUE8_ORIGINAL_ACCEPTANCE_TRANSFER
    assert phase1.issue8_product_memory_findings(issue8_documents()) == []


@pytest.mark.parametrize(
    ("path", "old", "expected"),
    (
        ("docs/PRD.md", "### Mode 2: Interactive AI Avatar Walkthrough", "I8.AC01.PRODUCT_MODES"),
        ("docs/PROJECT_AVATAR_PACK.md", "# Project Avatar Pack Contract", "I8.AC02.PACK_CONTRACT"),
        ("docs/ROADMAP.md", "### Stage 4: Slice 1, Project Upload To Grounded Script Generation", "I8.AC03.ROADMAP"),
        ("docs/AI_BUILD_BRIEF.md", "## Product modes to preserve", "I8.AC04.BUILD_BRIEF"),
        ("docs/SKILL_EXECUTION_PLAN.md", "`project-avatar-pack`", "I8.AC05.SKILL_PLAN"),
    ),
)
def test_issue311_product_memory_contract_rejects_missing_evidence(
    path: str,
    old: str,
    expected: str,
) -> None:
    documents = issue8_documents()
    documents[path] = documents[path].replace(old, "removed", 1)

    assert expected in phase1.issue8_product_memory_findings(documents)


def test_issue311_status_requires_terminal_heartbeat2_and_issue8_target() -> None:
    status_text = Path("docs/STATUS.md").read_text(encoding="utf-8")

    assert phase1.issue8_closeout_status_findings(status_text) == []


def test_issue311_branch_scope_and_budget_are_exact() -> None:
    expected = {
        "docs/governance/preflights/issue-311.json",
        "docs/PHASE_PLAN.md",
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }

    assert phase1.ISSUE_311_BRANCH == "phase-1-closure-process-311-issue8-product-memory-closeout"
    assert phase1.ISSUE_311_ALLOWED_CHANGED_FILES == expected
    assert phase1.ISSUE_311_LINE_CAP == 350


def test_issue311_scope_gate_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_311_BRANCH,
        files=sorted(phase1.ISSUE_311_ALLOWED_CHANGED_FILES),
    ) == []
    near_match = f"{phase1.ISSUE_311_BRANCH}-extra"
    assert run_changed_files_check(monkeypatch, branch=near_match, files=["docs/STATUS.md"]) == [
        f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."
    ]
    assert run_changed_files_check(
        monkeypatch, branch=phase1.ISSUE_311_BRANCH, files=["backend/app/main.py"]
    ) == [
        f"Phase 1 Closure branch {phase1.ISSUE_311_BRANCH} may not change backend/app/main.py."
    ]


def test_issue311_charged_line_cap_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "resolve_base", lambda: "branch-base")
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 351)

    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_311_BRANCH, files=[]) == [
        f"Phase 1 Closure branch {phase1.ISSUE_311_BRANCH} exceeds its 350-line cap."
    ]


def test_issue313_branch_scope_and_budget_are_exact() -> None:
    expected = {
        "docs/governance/preflights/issue-313.json",
        "docs/reviews/ISSUE_313_ISSUE280_REPAIR_FEASIBILITY.md",
        "docs/evals/issue280_semantic_oracle_v1.json",
        "docs/ADR/0044-issue280-repair-architecture-feasibility.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }

    assert phase1.ISSUE_313_BRANCH == (
        "phase-1-closure-process-313-issue280-repair-feasibility-oracle"
    )
    assert phase1.ISSUE_313_ALLOWED_CHANGED_FILES == expected
    assert phase1.ISSUE_313_LINE_CAP == 950


def test_issue313_scope_gate_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_313_BRANCH,
        files=sorted(phase1.ISSUE_313_ALLOWED_CHANGED_FILES),
    ) == []
    near_match = f"{phase1.ISSUE_313_BRANCH}-extra"
    assert run_changed_files_check(monkeypatch, branch=near_match, files=["docs/STATUS.md"]) == [
        f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."
    ]
    for path in (
        "backend/app/issue280.py",
        "frontend/src/app/page.tsx",
        "reports/checkpoint3-issue280/requirement-matrix.json",
        "scripts/quality/verify_issue280_output_correctness.py",
    ):
        assert run_changed_files_check(
            monkeypatch, branch=phase1.ISSUE_313_BRANCH, files=[path]
        ) == [f"Phase 1 Closure branch {phase1.ISSUE_313_BRANCH} may not change {path}."]


def test_issue313_charged_line_cap_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "resolve_base", lambda: "branch-base")
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 951)

    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_313_BRANCH, files=[]) == [
        f"Phase 1 Closure branch {phase1.ISSUE_313_BRANCH} exceeds its 950-line cap."
    ]


def test_issue315_branch_scope_and_budget_are_exact() -> None:
    expected = {
        "docs/governance/preflights/issue-315.json",
        "AGENTS.md",
        ".github/pull_request_template.md",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/QUALITY_GATES.md",
        "docs/SKILL_EXECUTION_PLAN.md",
        "docs/STATUS.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    }

    assert phase1.ISSUE_315_BRANCH == (
        "phase-1-closure-process-315-pr-product-context-gate"
    )
    assert phase1.ISSUE_315_ALLOWED_CHANGED_FILES == expected
    assert phase1.ISSUE_315_LINE_CAP == 1000


def test_issue315_scope_gate_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_315_BRANCH,
        files=sorted(phase1.ISSUE_315_ALLOWED_CHANGED_FILES),
    ) == []
    near_match = f"{phase1.ISSUE_315_BRANCH}-extra"
    assert run_changed_files_check(monkeypatch, branch=near_match, files=["docs/STATUS.md"]) == [
        f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."
    ]
    for path in (
        ".github/workflows/quality-gates.yml",
        "backend/app/main.py",
        "frontend/src/app/page.tsx",
        "pyproject.toml",
    ):
        assert run_changed_files_check(
            monkeypatch, branch=phase1.ISSUE_315_BRANCH, files=[path]
        ) == [f"Phase 1 Closure branch {phase1.ISSUE_315_BRANCH} may not change {path}."]


def test_issue315_charged_line_cap_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "resolve_base", lambda: "branch-base")
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 1001)

    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_315_BRANCH, files=[]) == [
        f"Phase 1 Closure branch {phase1.ISSUE_315_BRANCH} exceeds its 1000-line cap."
    ]


def test_issue317_scope_budget_and_surface_contract_are_exact(monkeypatch: Any) -> None:
    assert phase1.ISSUE_317_BRANCH == "phase-1-closure-317-issue280-semantic-repair-slice1"
    assert len(phase1.ISSUE_317_ALLOWED_CHANGED_FILES) == 18
    assert len(phase1.ISSUE_317_MEANINGFUL_SURFACES) == 10
    assert set().union(*phase1.ISSUE_317_MEANINGFUL_SURFACES.values()) == phase1.ISSUE_317_ALLOWED_CHANGED_FILES
    assert phase1.ISSUE_317_LINE_CAP == 3000
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 3000)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_317_BRANCH,
        files=sorted(phase1.ISSUE_317_ALLOWED_CHANGED_FILES),
    ) == []


def test_issue317_scope_gate_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    missing = sorted(phase1.ISSUE_317_ALLOWED_CHANGED_FILES)[0]
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_317_BRANCH,
        files=sorted(phase1.ISSUE_317_ALLOWED_CHANGED_FILES - {missing}) + ["backend/app/main.py"],
    )
    assert f"Phase 1 Closure branch {phase1.ISSUE_317_BRANCH} may not change backend/app/main.py." in failures
    assert f"Phase 1 Closure branch {phase1.ISSUE_317_BRANCH} must change {missing}." in failures
    near_match = f"{phase1.ISSUE_317_BRANCH}-extra"
    assert run_changed_files_check(monkeypatch, branch=near_match, files=["docs/STATUS.md"]) == [
        f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."
    ]


def test_issue317_charged_line_cap_fails_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "resolve_base", lambda: "branch-base")
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 3001)
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_317_BRANCH,
        files=sorted(phase1.ISSUE_317_ALLOWED_CHANGED_FILES),
    )
    assert failures == [
        f"Phase 1 Closure branch {phase1.ISSUE_317_BRANCH} exceeds its 3000-line cap."
    ]


def test_issue319_scope_budget_and_surface_contract_are_exact(monkeypatch: Any) -> None:
    assert phase1.ISSUE_319_BRANCH == (
        "phase-1-closure-process-319-agent-context-architecture-slice1"
    )
    assert len(phase1.ISSUE_319_ALLOWED_CHANGED_FILES) == 22
    assert len(phase1.ISSUE_319_MEANINGFUL_SURFACES) == 10
    assert set().union(*phase1.ISSUE_319_MEANINGFUL_SURFACES.values()) == (
        phase1.ISSUE_319_ALLOWED_CHANGED_FILES
    )
    assert phase1.ISSUE_319_LINE_CAP == 4200
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 4200)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_319_BRANCH,
        files=sorted(phase1.ISSUE_319_ALLOWED_CHANGED_FILES),
    ) == []


def test_issue319_scope_and_budget_fail_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 4201)
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_319_BRANCH,
        files=["backend/app/main.py"],
    )
    assert f"Phase 1 Closure branch {phase1.ISSUE_319_BRANCH} may not change backend/app/main.py." in failures
    assert f"Phase 1 Closure branch {phase1.ISSUE_319_BRANCH} exceeds its 4200-line cap." in failures
    near_match = f"{phase1.ISSUE_319_BRANCH}-extra"
    assert run_changed_files_check(monkeypatch, branch=near_match, files=["docs/STATUS.md"]) == [
        f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."
    ]


def test_issue321_scope_budget_and_surface_contract_are_exact(monkeypatch: Any) -> None:
    assert phase1.ISSUE_321_BRANCH == (
        "phase-1-closure-321-issue317-renderer-compatibility"
    )
    assert len(phase1.ISSUE_321_ALLOWED_CHANGED_FILES) == 9
    assert len(phase1.ISSUE_321_MEANINGFUL_SURFACES) == 6
    assert set().union(*phase1.ISSUE_321_MEANINGFUL_SURFACES.values()) == (
        phase1.ISSUE_321_ALLOWED_CHANGED_FILES
    )
    assert phase1.ISSUE_321_LINE_CAP == 800
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 800)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_321_BRANCH,
        files=sorted(phase1.ISSUE_321_ALLOWED_CHANGED_FILES),
    ) == []


def test_issue321_scope_and_budget_fail_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 801)
    missing = sorted(phase1.ISSUE_321_ALLOWED_CHANGED_FILES)[0]
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_321_BRANCH,
        files=sorted(phase1.ISSUE_321_ALLOWED_CHANGED_FILES - {missing})
        + ["backend/app/main.py"],
    )
    assert (
        f"Phase 1 Closure branch {phase1.ISSUE_321_BRANCH} may not change "
        "backend/app/main.py."
    ) in failures
    assert (
        f"Phase 1 Closure branch {phase1.ISSUE_321_BRANCH} must change {missing}."
    ) in failures
    assert (
        f"Phase 1 Closure branch {phase1.ISSUE_321_BRANCH} exceeds its 800-line cap."
    ) in failures
    near_match = f"{phase1.ISSUE_321_BRANCH}-extra"
    assert run_changed_files_check(
        monkeypatch, branch=near_match, files=["docs/STATUS.md"]
    ) == [f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."]


EXPECTED_ISSUE158_RECORD = {
    "schema_version": "issue-158-security-history-v2",
    "record_verified_on": "2026-08-01",
    "evidence_scope": "public GitHub and merged repository evidence",
    "pr_152": {
        "number": 152,
        "head_commit": "1308e88255724918bbde3a4775a0c973abaca8f4",
        "ready_for_review_at": "2026-07-14T10:51:12Z",
        "approved_by": "rohitagrawal4u",
        "approved_at": "2026-07-14T10:50:43Z",
        "latest_required_checks_at_merge": "passed",
        "earlier_failed_reruns_observed": True,
        "merge_commit": "648c81c066127056334c5c2babae28585fd58d4d",
        "merged_at": "2026-07-14T10:52:59Z",
    },
    "state_at_pr_152_merge": {
        "issue_138": "open",
        "issue_150": "open",
        "issue_151": "open",
        "process_contract_deviation": True,
        "branch_protection_bypass_in_reviewed_evidence": "not-observed",
        "explicit_dated_semgrep_risk_acceptance_in_reviewed_evidence": "not-found",
        "cpython_scanner_consensus": "absent",
        "cpython_remediation": "incomplete",
        "waiver_in_reviewed_evidence": "not-found",
        "blocked_claims": ["clean-container-security", "hosted-release", "production"],
    },
    "issue_138_closeout": {
        "closed_at": "2026-07-14T10:53:41Z",
        "state_after_closeout": "closed",
    },
    "later_issue_151_resolution": {
        "pr": 180,
        "head_commit": "f64cfb3dd34368a4920d9ec79ce9887fc17ca48e",
        "merge_commit": "8d18c3830ab5cb1336b33ce661e0aa33230e95e2",
        "merged_at": "2026-07-16T21:47:31Z",
        "issue_151_at_pr_180_merge": "open",
        "issue_151_closed_at": "2026-07-16T21:48:43Z",
        "issue_151_state_after_closeout": "closed",
        "retroactively_erases_pr_152_deviation": False,
    },
    "state_as_of_record_verification": {
        "issue_150": "open",
        "issue_151": "closed",
        "release_posture": "no-go",
    },
    "issue_158_effect": {
        "runtime_behavior": "unchanged",
        "scanner_behavior": "unchanged",
        "product_behavior": "unchanged", "global_clean_security_claim": "not-established",
    },
    "historical_source": {
        "commit": "648c81c066127056334c5c2babae28585fd58d4d",
        "blobs": {
            "docs/ADR/0006-stage8-release-hardening.md": "fa100222873b640371664a49caa2ba08c1f26073",
            "docs/RISK_REGISTER.md": "517e93cf86365574565f07f25ab44b289ca4e722",
            "docs/TRACEABILITY.md": "48c3c11a6abfa02014d4c044ce4ca906fa486822",
            "docs/reviews/ISSUE_138_CLICK_SECURITY_PREFLIGHT.md": "a44d5be907e54c1e6f661c6d651d605242d668de",
        },
    },
}


def issue158_leaf_paths(value: object, prefix: tuple[object, ...] = ()) -> list[tuple[object, ...]]:
    if isinstance(value, dict):
        return [
            path
            for key, child in value.items()
            for path in issue158_leaf_paths(child, prefix + (key,))
        ]
    if isinstance(value, list):
        return [
            path
            for index, child in enumerate(value)
            for path in issue158_leaf_paths(child, prefix + (index,))
        ]
    return [prefix]


def mutate_issue158_leaf(record: dict[str, object], path: tuple[object, ...]) -> None:
    target: Any = record
    for component in path[:-1]:
        target = target[component]
    leaf = target[path[-1]]
    if type(leaf) is bool:
        target[path[-1]] = not leaf
    elif type(leaf) is int:
        target[path[-1]] = leaf + 1
    else:
        target[path[-1]] = f"{leaf}-mutated"


def replace_issue158_record(text: str, replacement: str) -> str:
    pattern = re.compile(
        rf"({re.escape(phase1.ISSUE_158_RECORD_BEGIN)}\n\n"
        rf"## Issue #158 Security History Chronology\n\n```json\n)"
        rf"(?P<payload>.*?)(\n```\n\n{re.escape(phase1.ISSUE_158_RECORD_END)})",
        flags=re.S,
    )
    match = pattern.search(text)
    assert match is not None
    return text[: match.start("payload")] + replacement + text[match.end("payload") :]


def test_issue158_scope_budget_and_surfaces_are_exact(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-158.json",
        "docs/STATUS.md",
        "docs/ADR/0006-stage8-release-hardening.md",
        "docs/RISK_REGISTER.md",
        "docs/TRACEABILITY.md",
        "docs/reviews/ISSUE_138_CLICK_SECURITY_PREFLIGHT.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_158_BRANCH == (
        "phase-1-closure-process-158-phf-security-history-v2"
    )
    assert phase1.ISSUE_158_ALLOWED_CHANGED_FILES == expected
    assert phase1.ISSUE_158_LINE_CAP == 650
    assert len(phase1.ISSUE_158_MEANINGFUL_SURFACES) == 8
    assert set().union(*phase1.ISSUE_158_MEANINGFUL_SURFACES.values()) == expected
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 650)
    assert run_changed_files_check(
        monkeypatch, branch=phase1.ISSUE_158_BRANCH, files=sorted(expected)
    ) == []


def test_issue158_scope_and_budget_fail_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 651)
    missing = "docs/STATUS.md"
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_158_BRANCH,
        files=sorted(phase1.ISSUE_158_ALLOWED_CHANGED_FILES - {missing})
        + ["backend/app/main.py"],
    )
    assert f"Phase 1 Closure branch {phase1.ISSUE_158_BRANCH} may not change backend/app/main.py." in failures
    assert f"Phase 1 Closure branch {phase1.ISSUE_158_BRANCH} must change {missing}." in failures
    assert f"Phase 1 Closure branch {phase1.ISSUE_158_BRANCH} exceeds its 650-line cap." in failures
    near_match = f"{phase1.ISSUE_158_BRANCH}-extra"
    assert run_changed_files_check(
        monkeypatch, branch=near_match, files=["docs/STATUS.md"]
    ) == [f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."]


def test_issue158_record_schema_and_current_documents(monkeypatch: Any) -> None:
    assert phase1.ISSUE_158_SECURITY_HISTORY_RECORD == EXPECTED_ISSUE158_RECORD
    assert run_issue158_security_history_check(monkeypatch) == []


@pytest.mark.parametrize("leaf_path", issue158_leaf_paths(EXPECTED_ISSUE158_RECORD))
def test_issue158_rejects_every_leaf_value_mutation(
    monkeypatch: Any, leaf_path: tuple[object, ...]
) -> None:
    rel = "docs/ADR/0006-stage8-release-hardening.md"
    record = json.loads(json.dumps(EXPECTED_ISSUE158_RECORD))
    mutate_issue158_leaf(record, leaf_path)
    mutated = replace_issue158_record(phase1.read(rel), json.dumps(record, indent=2))
    failures = run_issue158_security_history_check(
        monkeypatch, read_overrides={rel: mutated}
    )
    assert any("record differs" in failure for failure in failures)


@pytest.mark.parametrize(
    ("path", "invalid"),
    (
        (("pr_152", "number"), 152.0),
        (("pr_152", "earlier_failed_reruns_observed"), 1),
        (("state_at_pr_152_merge", "process_contract_deviation"), 1),
        (("state_at_pr_152_merge", "blocked_claims"), "production"),
        (("later_issue_151_resolution", "retroactively_erases_pr_152_deviation"), 0),
    ),
)
def test_issue158_rejects_json_type_substitution(
    monkeypatch: Any, path: tuple[str, ...], invalid: object
) -> None:
    rel = "docs/RISK_REGISTER.md"
    record = json.loads(json.dumps(EXPECTED_ISSUE158_RECORD))
    target: Any = record
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = invalid
    mutated = replace_issue158_record(phase1.read(rel), json.dumps(record, indent=2))
    failures = run_issue158_security_history_check(
        monkeypatch, read_overrides={rel: mutated}
    )
    assert any("record type differs" in failure for failure in failures)


@pytest.mark.parametrize("mutation", ("duplicate-key", "missing-key", "unknown-key", "nonstandard", "malformed"))
def test_issue158_rejects_invalid_json_shape(monkeypatch: Any, mutation: str) -> None:
    rel = "docs/TRACEABILITY.md"
    payload = json.dumps(EXPECTED_ISSUE158_RECORD, indent=2)
    if mutation == "duplicate-key":
        payload = payload.replace(
            '  "record_verified_on": "2026-08-01",',
            '  "record_verified_on": "2026-08-01",\n  "record_verified_on": "2026-08-01",',
            1,
        )
    elif mutation == "missing-key":
        payload = payload.replace('  "record_verified_on": "2026-08-01",\n', "", 1)
    elif mutation == "unknown-key":
        payload = payload.replace(
            '  "record_verified_on": "2026-08-01",',
            '  "record_verified_on": "2026-08-01",\n  "unknown": true,',
            1,
        )
    elif mutation == "nonstandard":
        payload = payload.replace('"number": 152', '"number": NaN', 1)
    else:
        payload = "{not-json}"
    mutated = replace_issue158_record(phase1.read(rel), payload)
    failures = run_issue158_security_history_check(
        monkeypatch, read_overrides={rel: mutated}
    )
    assert any("record" in failure for failure in failures)


def test_issue158_rejects_duplicate_or_unstructured_bounded_record(monkeypatch: Any) -> None:
    rel = "docs/reviews/ISSUE_138_CLICK_SECURITY_PREFLIGHT.md"
    original = phase1.read(rel)
    start = original.index(phase1.ISSUE_158_RECORD_BEGIN)
    end = original.index(phase1.ISSUE_158_RECORD_END) + len(phase1.ISSUE_158_RECORD_END)
    duplicated = original + "\n\n" + original[start:end]
    extra_prose = original.replace(
        "## Issue #158 Security History Chronology\n\n```json",
        "## Issue #158 Security History Chronology\n\nUnstructured claim.\n\n```json",
        1,
    )
    for mutated in (duplicated, extra_prose):
        failures = run_issue158_security_history_check(
            monkeypatch, read_overrides={rel: mutated}
        )
        assert any("bounded record" in failure for failure in failures)


def test_issue158_allows_future_content_outside_bounded_record(monkeypatch: Any) -> None:
    rel = "docs/TRACEABILITY.md"
    mutated = (
        "## Earlier valid context\n\nPreserved.\n\n"
        + phase1.read(rel)
        + "\n\n## Later valid traceability entry\n\nFuture repository work remains editable.\n"
    )
    assert run_issue158_security_history_check(
        monkeypatch, read_overrides={rel: mutated}
    ) == []


def test_issue158_rejects_unreproducible_historical_blob(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "run_git", lambda args: "")
    assert any("historical Git blob anchor" in failure for failure in run_issue158_security_history_check(monkeypatch))


def test_issue294_replacement_scope_budget_and_surfaces_are_exact(
    monkeypatch: Any,
) -> None:
    expected = {
        "docs/governance/preflights/issue-294.json",
        "docs/STATUS.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_294_REPLACEMENT_BRANCH == (
        "phase-1-closure-process-294-post-322-ledger-replacement"
    )
    assert phase1.ISSUE_294_REPLACEMENT_ALLOWED_CHANGED_FILES == expected
    assert phase1.ISSUE_294_REPLACEMENT_LINE_CAP == 500
    assert len(phase1.ISSUE_294_REPLACEMENT_MEANINGFUL_SURFACES) == 4
    assert set().union(
        *phase1.ISSUE_294_REPLACEMENT_MEANINGFUL_SURFACES.values()
    ) == expected
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 500)
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_294_REPLACEMENT_BRANCH,
        files=sorted(expected),
    ) == []


def test_issue294_replacement_scope_and_budget_fail_closed(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 501)
    missing = sorted(phase1.ISSUE_294_REPLACEMENT_ALLOWED_CHANGED_FILES)[0]
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_294_REPLACEMENT_BRANCH,
        files=sorted(phase1.ISSUE_294_REPLACEMENT_ALLOWED_CHANGED_FILES - {missing})
        + ["backend/app/issue280.py"],
    )
    assert (
        f"Phase 1 Closure branch {phase1.ISSUE_294_REPLACEMENT_BRANCH} may not "
        "change backend/app/issue280.py."
    ) in failures
    assert (
        f"Phase 1 Closure branch {phase1.ISSUE_294_REPLACEMENT_BRANCH} must "
        f"change {missing}."
    ) in failures
    assert (
        f"Phase 1 Closure branch {phase1.ISSUE_294_REPLACEMENT_BRANCH} exceeds "
        "its 500-line cap."
    ) in failures
    near_match = f"{phase1.ISSUE_294_REPLACEMENT_BRANCH}-extra"
    assert run_changed_files_check(
        monkeypatch, branch=near_match, files=["docs/STATUS.md"]
    ) == [f"Phase 1 Closure branch {near_match} may not change docs/STATUS.md."]


@pytest.mark.parametrize(("is_file", "is_symlink"), ((False, False), (True, True)))
def test_issue294_replacement_rejects_deleted_or_symlinked_required_path(
    monkeypatch: Any, is_file: bool, is_symlink: bool
) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    target = "tests/unit/test_phase1_closure_docs.py"
    original_is_file = Path.is_file
    original_is_symlink = Path.is_symlink

    def patched_is_file(path: Path) -> bool:
        if path == phase1.ROOT / target:
            return is_file
        return original_is_file(path)

    def patched_is_symlink(path: Path) -> bool:
        if path == phase1.ROOT / target:
            return is_symlink
        return original_is_symlink(path)

    monkeypatch.setattr(Path, "is_file", patched_is_file)
    monkeypatch.setattr(Path, "is_symlink", patched_is_symlink)
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_294_REPLACEMENT_BRANCH,
        files=sorted(phase1.ISSUE_294_REPLACEMENT_ALLOWED_CHANGED_FILES),
    )

    assert failures == [
        f"Phase 1 Closure branch {phase1.ISSUE_294_REPLACEMENT_BRANCH} must retain "
        f"{target} as a regular file."
    ]


def test_issue319_fixture_provenance_fails_closed(monkeypatch: Any) -> None:
    fixtures = json.loads(
        Path("docs/agent-context/fixtures/routing-fixtures-v1.json").read_text()
    )
    fixtures["provenance"]["routerOutputUsedAsExpectedValue"] = True
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {"docs/agent-context/fixtures/routing-fixtures-v1.json": json.dumps(fixtures)},
        ),
    )
    monkeypatch.setattr(
        phase1.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "{}", ""),
    )
    failures: list[str] = []
    phase1.check_issue319_agent_context(failures)
    assert failures == [
        "Issue #319 routing fixtures lost frozen independent provenance or coverage."
    ]


def test_issue313_semantic_oracle_contract_is_complete() -> None:
    oracle = json.loads(
        Path("docs/evals/issue280_semantic_oracle_v1.json").read_text(encoding="utf-8")
    )

    assert phase1.issue313_oracle_findings(oracle) == []


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("unknown-key", "F280.ORACLE.SCHEMA"),
        ("weaken-threshold", "F280.ORACLE.METRICS"),
        ("remove-adversarial-case", "F280.ORACLE.ADVERSARIAL"),
        ("self-authored-verdict", "F280.ORACLE.VERDICT"),
        ("runtime-import", "F280.ORACLE.INDEPENDENCE"),
    ),
)
def test_issue313_semantic_oracle_rejects_false_pass_mutations(
    mutation: str, expected: str
) -> None:
    oracle = json.loads(
        Path("docs/evals/issue280_semantic_oracle_v1.json").read_text(encoding="utf-8")
    )
    if mutation == "unknown-key":
        oracle["authorVerdict"] = "FIXED"
    elif mutation == "weaken-threshold":
        oracle["mandatoryMetrics"][0]["threshold"] = 0.8
    elif mutation == "remove-adversarial-case":
        oracle["adversarialCases"].pop()
    elif mutation == "self-authored-verdict":
        oracle["verdict"]["computedOnly"] = False
    else:
        oracle["independence"]["forbiddenInputs"].remove("runtime converter source")

    assert expected in phase1.issue313_oracle_findings(oracle)


def test_issue313_feasibility_decision_contract_is_complete() -> None:
    decision = Path("docs/reviews/ISSUE_313_ISSUE280_REPAIR_FEASIBILITY.md").read_text(
        encoding="utf-8"
    )
    adr = Path("docs/ADR/0044-issue280-repair-architecture-feasibility.md").read_text(
        encoding="utf-8"
    )

    assert phase1.issue313_decision_findings(decision, adr) == []


def test_issue313_status_corrects_closed_issue300_and_merged_pr301() -> None:
    status_text = Path("docs/STATUS.md").read_text(encoding="utf-8")

    assert phase1.issue313_status_findings(status_text) == []
    assert "Issue #300 is the active negative-forensic-only reset" not in status_text
    assert "Complete PR #301 negative forensic containment" not in status_text


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


def test_changed_files_uses_final_worktree_diff_from_base(monkeypatch: Any) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(phase1, "resolve_base", lambda: "pinned-base")

    def fake_run(args: list[str], **kwargs: Any) -> Any:
        git_args = args[1:]
        calls.append(git_args)
        stdout = "docs/STATUS.md" if git_args[0] == "diff" else "tests/unit/new_test.py"
        return type("GitResult", (), {"returncode": 0, "stdout": stdout})()

    monkeypatch.setattr(phase1.subprocess, "run", fake_run)

    assert phase1.changed_files() == ["docs/STATUS.md", "tests/unit/new_test.py"]
    assert calls == [
        ["diff", "--name-only", "pinned-base"],
        ["ls-files", "--others", "--exclude-standard"],
    ]


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


def test_issue287_branch_allows_only_stage8_governance_drift_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-287.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
    }
    assert phase1.ISSUE_287_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-287-stage8-quality-gate-drift",
        files=sorted(expected),
    ) == []


def test_issue287_allowlist_rejects_near_match_and_dependency_files(monkeypatch: Any) -> None:
    allowed_path = "scripts/quality/check_stage8_docs.py"
    for branch in (
        "phase-1-closure-process-287-stage8-quality-gate-drift-extra",
        "phase-1-closure-process-278-stage8-quality-gate-drift",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[allowed_path]) == [
            f"Phase 1 Closure branch {branch} may not change {allowed_path}."
        ]

    branch = "phase-1-closure-process-287-stage8-quality-gate-drift"
    for path in ("frontend/package.json", "frontend/package-lock.json", "backend/app/main.py"):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
            f"Phase 1 Closure branch {branch} may not change {path}."
        ]


def test_issue289_branch_allows_combined_security_unblock_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-289.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/ADR/0037-postcss-audit-remediation.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "frontend/package.json",
        "frontend/package-lock.json",
        "scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_stage8_quality_gate.py",
    }
    assert phase1.ISSUE_289_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-289-security-postcss-stage8-gate-unblock",
        files=sorted(expected),
    ) == []


def test_issue289_allowlist_rejects_near_match_and_runtime_files(monkeypatch: Any) -> None:
    allowed_path = "frontend/package-lock.json"
    for branch in (
        "phase-1-closure-process-289-security-postcss-stage8-gate-unblock-extra",
        "phase-1-closure-process-287-stage8-quality-gate-drift",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[allowed_path]) == [
            f"Phase 1 Closure branch {branch} may not change {allowed_path}."
        ]

    branch = "phase-1-closure-process-289-security-postcss-stage8-gate-unblock"
    for path in ("backend/app/main.py", "frontend/src/app/page.tsx"):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
            f"Phase 1 Closure branch {branch} may not change {path}."
        ]


def test_issue296_allowlist_allows_only_frontend_brace_expansion_audit_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/governance/preflights/issue-296.json",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/ADR/0039-frontend-brace-expansion-audit-remediation.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "frontend/package.json",
        "frontend/package-lock.json",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_phase1_closure_docs.py",
    }
    assert phase1.ISSUE_296_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-process-296-frontend-brace-expansion-audit",
        files=sorted(expected),
    ) == []

    for branch in (
        "phase-1-closure-process-296-frontend-brace-expansion-audit-extra",
        "phase-1-closure-process-294-issue280-closure-ledger",
    ):
        assert run_changed_files_check(monkeypatch, branch=branch, files=["frontend/package-lock.json"]) == [
            f"Phase 1 Closure branch {branch} may not change frontend/package-lock.json."
        ]

    branch = "phase-1-closure-process-296-frontend-brace-expansion-audit"
    for path in ("backend/app/main.py", "frontend/src/app/page.tsx"):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
            f"Phase 1 Closure branch {branch} may not change {path}."
        ]


def test_issue300_allowlist_is_exact_bounded_forensic_scope(monkeypatch: Any) -> None:
    expected = {
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/governance/preflights/issue-300.json",
        "docs/reviews/ISSUE_300_GOVERNANCE_RESET_PREFLIGHT.md",
        "reports/checkpoint3-issue280/requirement-matrix.json",
        "scripts/quality/check_phase1_closure_docs.py",
        "scripts/quality/verify_issue280_output_correctness.py",
        "tests/unit/test_phase1_closure_docs.py",
        "tests/unit/test_issue280_forensic_verifier.py",
    }
    assert phase1.ISSUE_300_ALLOWED_CHANGED_FILES == expected
    branch = "phase-1-closure-process-300-issue280-semantic-closure-reset"
    assert run_changed_files_check(monkeypatch, branch=branch, files=sorted(expected)) == []

    for path in ("backend/app/issue280.py", "frontend/src/app/page.tsx", ".github/workflows/quality.yml"):
        assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
            f"Phase 1 Closure branch {branch} may not change {path}."
        ]


def test_issue300_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-process-300-issue280-semantic-closure-reset-extra"
    path = "scripts/quality/verify_issue280_output_correctness.py"
    assert run_changed_files_check(monkeypatch, branch=branch, files=[path]) == [
        f"Phase 1 Closure branch {branch} may not change {path}."
    ]


def test_issue300_contract_rejects_positive_closure_path(monkeypatch: Any) -> None:
    verifier_path = "scripts/quality/verify_issue280_output_correctness.py"
    original = phase1.read(verifier_path)
    monkeypatch.setattr(
        phase1,
        "read",
        read_with_overrides(
            phase1,
            {verifier_path: original + "\n# closure passed\n"},
        ),
    )
    failures: list[str] = []

    phase1.check_issue300_semantic_governance(failures)

    assert "Issue #280 forensic verifier must not contain a positive closure path." in failures


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


def test_issue280_pr_a_allowed_files_pass(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_BRANCH,
        files=sorted(phase1.ISSUE_280_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue280_pr_a_rejects_runtime_product_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_BRANCH,
        files=["backend/app/main.py"],
    )

    assert any("backend/app/main.py" in failure for failure in failures)


def test_issue280_pr_b_allowed_files_pass(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_B_BRANCH,
        files=sorted(phase1.ISSUE_280_PR_B_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue280_pr_b_rejects_full_e2e_runtime_files(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_B_BRANCH,
        files=["frontend/src/app/page.tsx"],
    )

    assert any("frontend/src/app/page.tsx" in failure for failure in failures)


def test_issue280_pr_c_allowed_files_pass(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_C_BRANCH,
        files=sorted(phase1.ISSUE_280_PR_C_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue280_pr_c_rejects_ui_without_exact_ui_scope(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_C_BRANCH,
        files=["frontend/src/app/page.tsx"],
    )

    assert any("frontend/src/app/page.tsx" in failure for failure in failures)


def test_issue280_pr_d_allowed_files_pass(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_D_BRANCH,
        files=sorted(phase1.ISSUE_280_PR_D_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue280_pr_d_rejects_backend_contract_changes(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_D_BRANCH,
        files=["backend/app/issue280.py"],
    )

    assert any("backend/app/issue280.py" in failure for failure in failures)


def test_issue280_pr_d_security_unblock_allowlist_stays_narrow(monkeypatch: Any) -> None:
    assert run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_D_BRANCH,
        files=["backend/Dockerfile", "docs/THIRD_PARTY_NOTICES.md"],
    ) == []

    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_D_BRANCH,
        files=["frontend/Dockerfile", "pyproject.toml", "uv.lock"],
    )

    assert failures == [
        f"Phase 1 Closure branch {phase1.ISSUE_280_PR_D_BRANCH} may not change frontend/Dockerfile.",
        f"Phase 1 Closure branch {phase1.ISSUE_280_PR_D_BRANCH} may not change pyproject.toml.",
        f"Phase 1 Closure branch {phase1.ISSUE_280_PR_D_BRANCH} may not change uv.lock.",
    ]


def test_issue280_pr_e_allowed_files_pass(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_E_BRANCH,
        files=sorted(phase1.ISSUE_280_PR_E_ALLOWED_CHANGED_FILES),
    )

    assert failures == []


def test_issue280_pr_e_rejects_provider_dependency_changes(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch=phase1.ISSUE_280_PR_E_BRANCH,
        files=["pyproject.toml", "frontend/package.json", "backend/app/stage6.py"],
    )

    assert set(failures) == {
        f"Phase 1 Closure branch {phase1.ISSUE_280_PR_E_BRANCH} may not change backend/app/stage6.py.",
        f"Phase 1 Closure branch {phase1.ISSUE_280_PR_E_BRANCH} may not change frontend/package.json.",
        f"Phase 1 Closure branch {phase1.ISSUE_280_PR_E_BRANCH} may not change pyproject.toml.",
    }


def test_issue280_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    failures = run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-280-c3a-r3-runtime-implementation",
        files=["docs/governance/preflights/issue-280.json"],
    )

    assert any("docs/governance/preflights/issue-280.json" in failure for failure in failures)


def test_issue280_matrix_rejects_unknown_top_level_key(monkeypatch: Any) -> None:
    matrix = json.loads(phase1.read(phase1.ISSUE_280_MATRIX_PATH))
    matrix["overallVerdict"] = "PASSED"
    failures = run_issue280_review_artifacts_check(
        monkeypatch,
        read_overrides={phase1.ISSUE_280_MATRIX_PATH: json.dumps(matrix)},
    )

    assert f"{phase1.ISSUE_280_MATRIX_PATH} must use only the strict top-level forensic schema." in failures


def test_issue280_matrix_rejects_unknown_nested_key(monkeypatch: Any) -> None:
    matrix = json.loads(phase1.read(phase1.ISSUE_280_MATRIX_PATH))
    matrix["forensicEvidence"]["observedExecution"]["authorVerdict"] = "FIXED"
    failures = run_issue280_review_artifacts_check(
        monkeypatch,
        read_overrides={phase1.ISSUE_280_MATRIX_PATH: json.dumps(matrix)},
    )

    assert f"{phase1.ISSUE_280_MATRIX_PATH} must use only strict observedExecution keys." in failures


def test_issue280_matrix_rejects_stale_forensic_identity(monkeypatch: Any) -> None:
    matrix = json.loads(phase1.read(phase1.ISSUE_280_MATRIX_PATH))
    matrix["forensicEvidence"]["evidenceHead"] = "0" * 40
    failures = run_issue280_review_artifacts_check(
        monkeypatch,
        read_overrides={phase1.ISSUE_280_MATRIX_PATH: json.dumps(matrix)},
    )

    assert f"{phase1.ISSUE_280_MATRIX_PATH} forensic evidenceHead must match the preserved identity." in failures


def test_issue280_preflight_requires_public_safe_boundaries(monkeypatch: Any) -> None:
    preflight = phase1.read("docs/reviews/ISSUE_280_C3A_R3_PREFLIGHT.md")
    failures = run_issue280_review_artifacts_check(
        monkeypatch,
        read_overrides={
            "docs/reviews/ISSUE_280_C3A_R3_PREFLIGHT.md": replace_text(
                preflight,
                "no provider setup",
                "provider setup marker removed",
            )
        },
    )

    assert any("no provider setup" in failure for failure in failures)


def test_issue280_red_evidence_rejects_permanent_failing_tests(monkeypatch: Any) -> None:
    plan = json.loads(phase1.read(phase1.ISSUE_280_RED_EVIDENCE_PATH))
    plan["permanentFailingTestsCommitted"] = True
    failures = run_issue280_review_artifacts_check(
        monkeypatch,
        read_overrides={phase1.ISSUE_280_RED_EVIDENCE_PATH: json.dumps(plan)},
    )

    assert f"{phase1.ISSUE_280_RED_EVIDENCE_PATH} must reject permanently failing tests." in failures


def test_issue306_heartbeat1_b_exact_branch_accepts_only_the_frozen_allowlist(monkeypatch: Any) -> None:
    expected = {
        ".github/workflows/ci.yml",
        "docs/ADR/0042-heartbeat1-b-browser-reopen-evidence.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "frontend/playwright.heartbeat1.config.ts",
        "frontend/src/app/page.tsx",
        "frontend/tests/heartbeat1-browser.spec.ts",
        "scripts/ci/heartbeat1-browser.sh",
        "scripts/ci/heartbeat1_evidence.py",
        "scripts/quality/check_phase1_closure_docs.py",
        "tests/unit/test_heartbeat1_evidence.py",
        "tests/unit/test_phase1_closure_docs.py",
    }

    assert phase1.ISSUE_306_B_BRANCH == "phase-1-closure-306-heartbeat1-b-browser-reopen"
    assert phase1.ISSUE_306_B_ALLOWED_CHANGED_FILES == expected
    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_306_B_BRANCH, files=sorted(expected)) == []


def test_issue306_heartbeat1_b_near_match_branch_fails_closed(monkeypatch: Any) -> None:
    branch = "phase-1-closure-306-heartbeat1-b-browser-reopen-extra"
    rel = "frontend/tests/heartbeat1-browser.spec.ts"

    assert run_changed_files_check(monkeypatch, branch=branch, files=[rel]) == [
        f"Phase 1 Closure branch {branch} may not change {rel}."
    ]


def test_issue306_heartbeat1_b_rejects_backend_or_ninth_surface(monkeypatch: Any) -> None:
    rel = "backend/app/main.py"

    assert run_changed_files_check(monkeypatch, branch="phase-1-closure-306-heartbeat1-b-browser-reopen", files=[rel]) == [
        "Phase 1 Closure branch phase-1-closure-306-heartbeat1-b-browser-reopen may not change backend/app/main.py."
    ]
def load_heartbeat2_evidence_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "ci" / "heartbeat2_evidence.py"
    spec = importlib.util.spec_from_file_location("heartbeat2_evidence_under_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
def test_issue308_exact_branches_accept_only_the_frozen_allowlists(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    evidence = {".github/workflows/ci.yml", "docs/ADR/0043-heartbeat2-curated-reviewer-demo.md", "docs/PHASE_PLAN.md", "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "scripts/ci/heartbeat2_evidence.py", "scripts/quality/check_phase1_closure_docs.py", "tests/unit/test_phase1_closure_docs.py"}
    demo = {"docs/ADR/0043-heartbeat2-curated-reviewer-demo.md", "docs/STATUS.md", "docs/TRACEABILITY.md", "frontend/playwright.heartbeat2.config.ts", "frontend/src/app/page.tsx", "frontend/src/app/page.test.tsx", "frontend/tests/heartbeat2-browser.spec.ts", "scripts/ci/heartbeat2-browser.sh", "scripts/ci/heartbeat2_evidence.py", "scripts/quality/check_phase1_closure_docs.py", "tests/unit/test_phase1_closure_docs.py"}
    assert phase1.ISSUE_308_H2_A_BRANCH == "phase-1-closure-308-heartbeat2-evidence-contract"
    assert phase1.ISSUE_308_H2_A_ALLOWED_CHANGED_FILES == evidence
    assert phase1.ISSUE_308_H2_B_BRANCH == "phase-1-closure-308-heartbeat2-curated-reviewer-demo"
    assert phase1.ISSUE_308_H2_B_ALLOWED_CHANGED_FILES == demo
    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_308_H2_A_BRANCH, files=sorted(evidence)) == []
    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_308_H2_B_BRANCH, files=sorted(demo)) == []


def test_issue308_near_match_and_backend_changes_fail_closed(monkeypatch: Any) -> None:
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 0)
    branch = "phase-1-closure-308-heartbeat2-evidence-contract-extra"
    rel = "docs/STATUS.md"
    assert run_changed_files_check(monkeypatch, branch=branch, files=[rel]) == [
        f"Phase 1 Closure branch {branch} may not change {rel}."
    ]
    assert run_changed_files_check(
        monkeypatch,
        branch="phase-1-closure-308-heartbeat2-curated-reviewer-demo",
        files=["backend/app/main.py"],
    ) == [
        "Phase 1 Closure branch phase-1-closure-308-heartbeat2-curated-reviewer-demo may not change backend/app/main.py."
    ]


def test_issue308_charged_line_caps_fail_closed(monkeypatch: Any) -> None:
    real_changed_files = phase1.changed_files
    monkeypatch.setattr(phase1, "resolve_base", lambda: "branch-base")
    monkeypatch.setattr(phase1, "charged_lines", lambda base: 1601 if base == "branch-base" else 2501)
    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_308_H2_A_BRANCH, files=[]) == [
        f"Phase 1 Closure branch {phase1.ISSUE_308_H2_A_BRANCH} exceeds its 1600-line or 2500-line aggregate cap."
    ]
    monkeypatch.setattr(phase1, "charged_lines", lambda base: None)
    assert run_changed_files_check(monkeypatch, branch=phase1.ISSUE_308_H2_B_BRANCH, files=[]) == [
        f"Phase 1 Closure branch {phase1.ISSUE_308_H2_B_BRANCH} has uncountable or binary charged lines."
    ]
    failed = type("FailedGit", (), {"returncode": 1, "stdout": ""})()
    monkeypatch.setattr(phase1, "changed_files", real_changed_files)
    monkeypatch.setattr(phase1.subprocess, "run", lambda *args, **kwargs: failed)
    assert phase1.charged_lines("missing-base") is None
    failures: list[str] = []
    phase1.check_changed_files(failures)
    assert failures == [f"Phase 1 Closure branch {phase1.ISSUE_308_H2_B_BRANCH} could not resolve its changed-file set."]


def write_heartbeat2_packet(root: Path, source_root: Path, evidence: Any) -> dict[str, Any]:
    import ast
    import base64
    import hashlib
    root.mkdir(parents=True, exist_ok=True)
    graph = []
    for relative in evidence.SOURCES:
        path = source_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = "bounded committed source\n"
        if relative == "frontend/tests/heartbeat2-browser.spec.ts":
            content = '''import { test, type Request } from "@playwright/test";
test.skip(!process.env.H2_CANDIDATE_DIR, "runs only through the canonical Heartbeat 2 evidence runner");
test("Heartbeat 2 local reviewer demo", async ({ page }) => {
const requestIds = new WeakMap<Request, string>();
page.on("request", (request) => {
  requestIds.set(request, request.url());
  requests.push({ method: request.method(), body: request.postDataBuffer() });
});
page.on("response", async (response) => {
  const request = response.request();
  responses.push({ requestId: requestIds.get(request), status: response.status(), body: await response.body() });
});
await page.goto("/");
});
'''
        path.write_text(content, encoding="utf-8")
        graph.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    artifacts = {}
    translated = "# Recorrido sintético [1]\n"
    subtitles = "1\n00:00:00,000 --> 00:00:01,000\nBounded synthetic caption [1]\n"
    voice = json.dumps({"provider": "mock", "providerMode": "LOCAL", "language": "es", "languageDisplayName": "Spanish", "textChecksum": f"sha256:{hashlib.sha256(translated.encode()).hexdigest()}", "durationSecondsEstimate": 1, "mockAudioProfile": {"durationMillisecondsEstimate": 1000, "sampleRateHz": 16000, "channels": 1}, "disclosure": "Mock local TTS placeholder"})
    source_meta = {"runId": "run-1", "traceId": "trace-1", "contextRefCount": 1, "contextRefIds": ["context-1"], "citationCount": 1, "citationIndexes": [1], "evaluationId": "eval-1", "evaluationChecksum": "eval-sha", "evaluationStatus": "PASSED", "scriptChecksum": "sha256:script-sha"}
    local_provider = {"provider": "mock", "providerMode": "LOCAL", "adapterKind": "MOCK_LOCAL", "allowNetworkEgress": False, "requiresApiKey": False, "supportsRealVideo": False, "supportsClonedIdentity": False}
    avatar_boundary = {"provider": "disabled", "providerMode": "DISABLED", "enabled": False, "allowNetworkEgress": False, "requiresApiKey": True, "supportsRealVideo": True, "supportsClonedIdentity": False, "assetProvenancePolicy": "fully_synthetic_or_provider_stock_non_identifiable_only", "disclosureText": "AI-generated synthetic avatar/video. No cloned identity was used.", "disclosureVersion": "stage7-avatar-video-disclosure-v1", "retentionState": "NOT_CREATED", "deletionState": "NOT_REQUESTED"}
    disclosure = {"aiGenerated": True, "clonedIdentity": False, "consentRequired": True, "consentStatus": "CONFIRMED", "message": "Synthetic local avatar disclosure"}
    multilingual_meta = {"sourceRunId": "run-1", "multilingualRunId": "multi-1", "targetLanguage": "es", "translatedScriptChecksum": f"sha256:{hashlib.sha256(translated.encode()).hexdigest()}", "subtitlesChecksum": f"sha256:{hashlib.sha256(subtitles.encode()).hexdigest()}", "voiceManifestChecksum": f"sha256:{hashlib.sha256(voice.encode()).hexdigest()}", "contextRefIds": ["context-1"], "citationIndexes": [1], "evaluationId": "eval-1", "evaluationChecksum": "eval-sha", "providerPosture": {"translationProvider": "mock", "translationProviderMode": "LOCAL", "voiceProvider": "mock", "voiceProviderMode": "LOCAL"}, "consentDisclosureVersion": "avatar-consent-v1"}
    payloads = {
        "translated": translated,
        "subtitles": subtitles,
        "voice": voice,
        "preview": "<!doctype html><html><body>Local synthetic preview</body></html>",
        "renderManifest": json.dumps({"schema": "Stage7AvatarRenderManifest", "version": "stage7-mock-avatar-render-v1", "provider": {"provider": "mock", "providerMode": "LOCAL", "requestedProvider": "mock", "fallbackReason": None}, "providerConfig": local_provider, "avatarVideoProvider": avatar_boundary, "renderer": {"renderer": "local-html", "rendererMode": "LOCAL", "exportFormat": "html"}, "source": source_meta, "disclosure": disclosure, "sceneCountEstimate": 1, "videoExportPlaceholder": {"status": "PLACEHOLDER_ONLY", "mimeType": "application/json", "realVideoProduced": False}, "publicUseLicenseCheck": "mock-local-provider-only-no-third-party-media", "multilingualBundle": multilingual_meta}),
        "video": json.dumps({"schema": "Stage7VideoExportPlaceholder", "version": "stage7-video-export-placeholder-v1", "status": "PLACEHOLDER_ONLY", "realVideoProduced": False, "renderer": "local-html", "providerConfig": local_provider, "avatarVideoProvider": avatar_boundary, "disclosure": disclosure, "source": source_meta, "publicUseLicenseCheck": "mock-local-provider-only-no-third-party-media", "sourceRunId": "run-1", "traceId": "trace-1", "reason": "Stage 7 exports a validated HTML demo and metadata, not a real video binary.", "multilingualBundle": multilingual_meta}),
    }
    for name, filename, mime in (("translated", "translated.md", "text/markdown"), ("subtitles", "captions.srt", "application/x-subrip"), ("voice", "voice.json", "application/json"), ("preview", "preview.html", "text/html"), ("renderManifest", "render.json", "application/json"), ("video", "video.json", "application/json")):
        path = root / "artifacts" / filename
        path.parent.mkdir(exist_ok=True)
        path.write_text(payloads[name], encoding="utf-8")
        artifacts[name] = {"path": path.relative_to(root).as_posix(), "filename": filename, "mime": mime, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    report = {"config": {"configFile": "frontend/playwright.heartbeat2.config.ts", "rootDir": "frontend/tests", "version": "1.61.1", "projects": [{"id": "chromium", "name": "chromium"}]}, "errors": [], "stats": {"startTime": "2026-07-29T00:00:00Z", "duration": 10, "expected": 1, "unexpected": 0, "skipped": 0, "flaky": 0}, "suites": [{"title": "", "file": "heartbeat2-browser.spec.ts", "line": 0, "column": 0, "specs": [{"title": "Heartbeat 2 local reviewer demo", "id": "spec-1", "file": "heartbeat2-browser.spec.ts", "line": 3, "column": 1, "ok": True, "tags": [], "tests": [{"expectedStatus": "passed", "status": "expected", "projectId": "chromium", "projectName": "chromium", "timeout": 30000, "annotations": [], "results": [{"status": "passed", "retry": 0, "errors": [], "duration": 10, "startTime": "2026-07-29T00:00:00Z", "workerIndex": 0, "parallelIndex": 0, "stdout": [], "stderr": [], "annotations": [], "attachments": [{"name": "trace", "contentType": "application/zip", "path": "/tmp/trace.zip"}]}]}]}]}]}
    fixture = b"# Heartbeat 2 controlled synthetic public reviewer fixture.\n"
    fixture_tree = ast.parse((Path(__file__).parents[1] / "api" / "test_stage6_multilingual_api.py").read_bytes())
    fixture = next(
        value
        for node in ast.walk(fixture_tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, (str, bytes))
        and hashlib.sha256(value := node.value.encode() if isinstance(node.value, str) else node.value).hexdigest()
        == "9cefe4184b2a67d4cdc56d66d005b90409e06ad449c4c426b7d6e012125bfcb6"
    )
    source_checksum = hashlib.sha256(fixture).hexdigest()
    source = {"sourceId": "source-1", "checksum": source_checksum, "decisionId": "decision-1", "policyVersion": "curation-policy-v1", "sourceVersion": "heartbeat2-public-v1", "assertionsFingerprint": "assertions-sha", "serverDecision": "ACCEPT_FOR_REVIEW", "decisionState": "APPROVED", "ingestionStatus": "INGESTED", "acceptedChunks": [{"chunkId": "chunk-1", "checksum": "chunk-sha"}]}
    snapshot = {"sourceDocumentChecksum": source_checksum, "chunkChecksum": "chunk-sha"}
    contexts = [{"contextRefId": "context-1", "claimId": "claim-1", "documentId": "source-1", "chunkId": "chunk-1", "evidenceSnapshot": snapshot}]
    supports = [{"claimId": "claim-1", "contextRefId": "context-1", "documentId": "source-1", "chunkId": "chunk-1", "citationIndex": 1, "evidenceSnapshot": snapshot}]
    evaluation = {"evaluationId": "eval-1", "evaluationStatus": "PASSED", "unsupportedClaimCount": 0, "claimSupports": supports}
    walkthrough = {"projectId": "project-1", "runId": "run-1", "status": "COMPLETED", "acceptedScriptText": "Synthetic grounded walkthrough [1]", "contextRefs": contexts, "evaluation": evaluation}
    media_artifacts = {key: {"checksum": f"sha256:{artifacts[name]['sha256']}"} for key, name in (("translatedScript", "translated"), ("subtitles", "subtitles"), ("voiceManifest", "voice"))}
    trace = {"projectId": "project-1", "sourceContextRefIds": ["context-1"], "sourceCitationIndexes": [1], "sourceEvaluationId": "eval-1", "sourceEvaluationChecksum": "eval-sha"}
    media = {"multilingualRunId": "multi-1", "sourceRunId": "run-1", "targetLanguage": "es", "translatedScriptText": translated, "status": "COMPLETED", "translationProvider": {"provider": "mock", "providerMode": "LOCAL"}, "voice": {"provider": "mock", "providerMode": "LOCAL"}, "artifacts": media_artifacts, "trace": trace}
    render_artifacts = {key: {"checksum": f"sha256:{artifacts[name]['sha256']}"} for key, name in (("demoExport", "preview"), ("renderManifest", "renderManifest"), ("videoExportPlaceholder", "video"))}
    consent = {"consentRecordId": "consent-1", "projectId": "project-1", "sourceRunId": "run-1", "sourceContextRefIds": ["context-1"], "sourceCitationIndexes": [1], "sourceEvaluationId": "eval-1", "sourceEvaluationChecksum": "eval-sha", "evaluationStatus": "PASSED", "consentStatementVersion": "avatar-consent-v1"}
    render = {"avatarRenderId": "render-1", "consentRecordId": "consent-1", "sourceRunId": "run-1", "providerConfig": local_provider, "disclosure": disclosure, "artifacts": render_artifacts, "trace": trace | {"multilingualRunId": "multi-1"}}
    bundle = {"principal": "curator_demo", "projectCount": 1, "projectId": "project-1", "legacySources": [], "source": source, "walkthrough": walkthrough, "visibleCitations": [{"claimId": "claim-1", "contextRefId": "context-1", "chunkId": "chunk-1"}], "multilingual": media, "consent": consent, "render": render, "artifacts": artifacts, "otherDemo": {"actionsHidden": True}}
    methods = [("project", "POST", 201), ("submit", "POST", 201), ("approve", "PATCH", 200), ("ingest", "POST", 201), ("walkthrough", "POST", 201), ("multilingual", "POST", 201), ("consent", "POST", 201), ("render", "POST", 201)]
    paths = ["/api/v1/projects", "/api/v1/projects/project-1/knowledge-documents", "/api/v1/projects/project-1/knowledge-documents/source-1/approval", "/api/v1/projects/project-1/ingestion-runs", "/api/v1/projects/project-1/walkthrough-runs", "/api/v1/projects/project-1/walkthrough-runs/run-1/multilingual-runs", "/api/v1/projects/project-1/walkthrough-runs/run-1/avatar-consents", "/api/v1/projects/project-1/walkthrough-runs/run-1/avatar-renders"]
    writes = [{"sequence": i, "operation": op, "method": method, "path": paths[i - 1], "origin": evidence.ORIGIN, "principal": "curator_demo", "projectId": "project-1", "id": f"w{i}"} for i, (op, method, status) in enumerate(methods, 1)]
    reads = [{"sequence": i, "operation": op, "method": method, "path": "/api/v1/languages" if i == 1 else "/api/v1/projects/project-1/source-curation-summary", "origin": evidence.ORIGIN, "principal": principal, "projectId": "" if i == 1 else "project-1", "id": f"r{i}"} for i, (op, method, status, principal) in enumerate(evidence.READS, 1)]
    denial_paths = paths[4:5] + paths[5:8]
    denials = [{"sequence": i, "operation": op, "method": method, "path": denial_paths[i - 1], "origin": evidence.ORIGIN, "principal": "other_demo", "projectId": "project-1", "id": f"d{i}"} for i, (op, method, status) in enumerate(evidence.DENIALS, 1)]
    requests = [reads[0], *writes[:4], reads[1], *writes[4:], reads[2], *denials]
    boundary = "heartbeat2-reset5-boundary"
    form = {"action": "ACCEPT_FOR_REVIEW", "classification": "PUBLIC_SAFE", "provenance": "PROJECT_AUTHORED_SYNTHETIC", "rightsBasis": "PROJECT_OWNED", "rightsStatus": "ELIGIBLE", "usagePolicy": "LOCAL_TEST_REUSE_ALLOWED", "curationSchemaVersion": "source-curation-v1", "sourceVersion": source["sourceVersion"]}
    multipart = b"".join(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode() for name, value in form.items()) + f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"heartbeat2-public.md\"\r\nContent-Type: text/markdown\r\n\r\n".encode() + fixture + f"\r\n--{boundary}--\r\n".encode()
    multilingual_bundle = {"sourceRunId": "run-1", "multilingualRunId": "multi-1", "targetLanguage": "es", "translatedScriptChecksum": f"sha256:{artifacts['translated']['sha256']}", "subtitlesChecksum": f"sha256:{artifacts['subtitles']['sha256']}", "voiceManifestChecksum": f"sha256:{artifacts['voice']['sha256']}", "contextRefIds": ["context-1"], "citationIndexes": [1], "evaluationId": "eval-1", "evaluationChecksum": "eval-sha", "providerPosture": {"translationProvider": "mock", "translationProviderMode": "LOCAL", "voiceProvider": "mock", "voiceProviderMode": "LOCAL"}, "consentDisclosureVersion": consent["consentStatementVersion"]}
    write_payloads = [{"name": "Heartbeat 2 reviewer demo", "description": "Controlled synthetic curated walkthrough", "defaultAudience": "RECRUITER", "defaultLanguage": "en"}, None, {"approvalStatus": "APPROVED", "action": "APPROVE", "curationSchemaVersion": "source-curation-v1", "sourceId": source["sourceId"], "decisionId": source["decisionId"], "policyVersion": source["policyVersion"], "sourceVersion": source["sourceVersion"], "checksum": source["checksum"], "assertionsFingerprint": source["assertionsFingerprint"]}, {"documentIds": [], "sourceIds": [source["sourceId"]]}, {"audience": "RECRUITER", "requestedLanguage": "en", "depth": "CONCISE", "style": "CONFIDENT", "prompt": "Create the controlled synthetic grounded reviewer walkthrough."}, {"targetLanguage": "es", "glossaryTerms": [], "requestedVoiceProvider": "mock"}, {"consentToUseSyntheticAvatar": True}, {"requestedAvatarProvider": "mock", "consentToUseSyntheticAvatar": True, "consentRecordId": "consent-1", "clonedIdentityRequested": False, "multilingualBundle": multilingual_bundle}]
    payload_by_operation = dict(zip((item[0] for item in methods), write_payloads, strict=True))
    for request in requests:
        operation = request["operation"].removeprefix("other-")
        raw = multipart if operation == "submit" else json.dumps(payload_by_operation.get(operation, {}), separators=(",", ":"), sort_keys=True).encode() if request["method"] != "GET" else b""
        content_type = f"multipart/form-data; boundary={boundary}" if operation == "submit" else "application/json" if raw else ""
        request.update({"bodyBase64": base64.b64encode(raw).decode(), "bodySha256": hashlib.sha256(raw).hexdigest(), "contentType": content_type})
    statuses = {op: status for op, _, status in methods} | {op: status for op, _, status, _ in evidence.READS} | {op: status for op, _, status in evidence.DENIALS}
    response_payloads = {"project": {"projectId": "project-1"}, "submit": {"sourceId": "source-1", "checksum": source_checksum, "decisionState": "PENDING_REVIEW"}, "approve": {"sourceId": "source-1", "checksum": source_checksum, "decisionState": "APPROVED"}, "ingest": {"status": "COMPLETED", "sourceIds": ["source-1"], "chunkCount": 1}, "walkthrough": walkthrough, "multilingual": media, "consent": consent, "render": render, "languages": {"languages": [{"languageTag": "es", "localDemoSupportStatus": "SUPPORTED"}]}, "summary": {"projectId": "project-1", "curatedSources": [source], "legacySources": []}}
    responses = []
    for request in requests:
        body = response_payloads.get(request["operation"], {"error": {"code": "FORBIDDEN"}})
        raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        responses.append({"requestId": request["id"], "status": statuses[request["operation"]], "bodyBase64": base64.b64encode(raw).decode(), "bodySha256": hashlib.sha256(raw).hexdigest()})
    import zipfile
    records = []
    resources: dict[str, bytes] = {}
    for request, response in zip(requests, responses, strict=True):
        raw = base64.b64decode(response["bodyBase64"])
        resource = f"{hashlib.sha1(raw).hexdigest()}.json"
        resources[resource] = raw
        request_raw = base64.b64decode(request["bodyBase64"])
        records.append({"type": "resource-snapshot", "snapshot": {"request": {"url": request["origin"] + request["path"], "method": request["method"], "headers": [{"name": "X-Local-User-Id", "value": request["principal"]}, {"name": "Content-Type", "value": request["contentType"]}], "postData": {"text": request_raw.decode()} if request_raw else None}, "response": {"status": response["status"], "content": {"_sha1": resource}}}})
    with zipfile.ZipFile(root / "trace.zip", "w") as archive:
        actions = ["goto", "click", "setInputFiles", "click", "click", "click", "selectOption", "dispatchEvent"]
        trace_records = [{"version": 8, "type": "context-options", "browserName": "chromium", "playwrightVersion": "1.61.1", "options": {"baseURL": evidence.ORIGIN, "serviceWorkers": "block"}}] + [item for index, method in enumerate(actions, 1) for item in ({"type": "before", "callId": f"call@{index}", "class": "Frame", "method": method, "pageId": "page@1"}, {"type": "after", "callId": f"call@{index}"})]
        archive.writestr("0-trace.trace", "\n".join(json.dumps(item) for item in trace_records))
        archive.writestr("0-trace.network", "\n".join(json.dumps(record) for record in records))
        archive.writestr("0-trace.stacks", json.dumps({"files": ["/workspace/frontend/tests/heartbeat2-browser.spec.ts"], "stacks": [[index, [[0, min(3 + index, 12), 1, ""]]] for index in range(1, 9)]}))
        for name, raw in resources.items():
            archive.writestr(f"resources/{name}", raw)
    trace_sha = hashlib.sha256((root / "trace.zip").read_bytes()).hexdigest()
    manifest = {"schema": "heartbeat2-evidence-v2", "runId": "run-308", "headSha": "a" * 40, "testReport": "playwright.json", "traffic": "traffic.json", "trace": "trace.zip", "traceSha256": trace_sha, "bundle": "bundle.json", "sourceGraph": graph}
    for filename, payload in (("playwright.json", report), ("traffic.json", {"requests": requests, "responses": responses}), ("bundle.json", bundle), ("manifest.json", manifest)):
        (root / filename).write_text(json.dumps(payload), encoding="utf-8")
    return {"manifest": manifest, "report": report, "traffic": {"requests": requests, "responses": responses}, "bundle": bundle, "artifact": root / "artifacts" / "video.json"}


def rewrite_heartbeat2_trace(root: Path, mutate: Callable[[dict[str, bytes]], None], evidence: Any) -> None:
    import zipfile
    path = root / "trace.zip"
    with zipfile.ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    mutate(members)
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["traceSha256"] = evidence.sha256(path.read_bytes())
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def replace_heartbeat2_response(root: Path, index: int, body: dict[str, Any], evidence: Any) -> None:
    import base64
    import hashlib
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    traffic = json.loads((root / "traffic.json").read_text())
    traffic["responses"][index].update({"bodyBase64": base64.b64encode(raw).decode(), "bodySha256": evidence.sha256(raw)})
    (root / "traffic.json").write_text(json.dumps(traffic), encoding="utf-8")
    def mutate(members: dict[str, bytes]) -> None:
        records = [json.loads(line) for line in members["0-trace.network"].splitlines()]
        resource = f"{hashlib.sha1(raw).hexdigest()}.json"
        records[index]["snapshot"]["response"]["content"]["_sha1"] = resource
        members["0-trace.network"] = "\n".join(json.dumps(item) for item in records).encode()
        members[f"resources/{resource}"] = raw
    rewrite_heartbeat2_trace(root, mutate, evidence)


def test_heartbeat2_verifier_accepts_exact_packet_and_rejects_false_passes(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "evidence", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    result = evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    assert result["outcome"] == "SEMANTIC_PASS_LOCAL"
    assert result["writeCount"] == 8
    assert packet["report"]["stats"]["startTime"]
    with pytest.raises(evidence.EvidenceError, match="FORBIDDEN_INPUT"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources, committed=True)
    packet["report"].pop("config")
    (root / "playwright.json").write_text(json.dumps(packet["report"]), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="PLAYWRIGHT_RESULT"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["report"]["stats"].update({"expected": 0, "skipped": 1})
    (root / "playwright.json").write_text(json.dumps(packet["report"]), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="PLAYWRIGHT_RESULT"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_ledger_artifact_source_and_forbidden_mutations(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    mutations = (
        ("traffic", "traffic", lambda p: p["traffic"]["requests"][0].__setitem__("principal", "other_demo"), "READ_LEDGER"),
        ("method", "traffic", lambda p: p["traffic"]["requests"][10].__setitem__("method", "POST"), "READ_LEDGER"),
        ("joins", "bundle", lambda p: p["bundle"]["walkthrough"]["contextRefs"][0]["evidenceSnapshot"].__setitem__("sourceDocumentChecksum", "wrong"), "PRODUCT_JOIN"),
        ("lifecycle", "bundle", lambda p: p["bundle"]["source"].__setitem__("decisionState", "PENDING_REVIEW"), "PRODUCT_JOIN"),
        ("source", "manifest", lambda p: p["manifest"]["sourceGraph"].pop(), "SOURCE_GRAPH"),
    )
    for label, payload, mutate, code in mutations:
        root, packet = tmp_path / label, write_heartbeat2_packet(tmp_path / label, sources, evidence)
        cast(Callable[[dict[str, Any]], Any], mutate)(packet)
        (root / f"{payload}.json").write_text(json.dumps(packet[payload]), encoding="utf-8")
        with pytest.raises(evidence.EvidenceError, match=code):
            evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "artifact"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["artifact"].write_bytes(b"tampered")
    with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN|ARTIFACT_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "payload"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["artifact"].write_text("not-json", encoding="utf-8")
    packet["bundle"]["artifacts"]["video"]["sha256"] = evidence.sha256(packet["artifact"].read_bytes())
    (root / "bundle.json").write_text(json.dumps(packet["bundle"]), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN|ARTIFACT_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "privacy"
    write_heartbeat2_packet(root, sources, evidence)
    marker = b"synthetic-forbidden-308"
    import io
    import zipfile
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr("member.bin", marker)
    with zipfile.ZipFile(root / "nested-privacy.zip", "w") as archive:
        archive.writestr("nested.zip", nested.getvalue())
    with pytest.raises(evidence.EvidenceError, match="FORBIDDEN_OR_ARCHIVE"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", forbidden=(marker,), source_root=sources)
    root = tmp_path / "unsafe-archive"
    write_heartbeat2_packet(root, sources, evidence)
    with zipfile.ZipFile(root / "unsafe.zip", "w") as archive:
        archive.writestr("../../escape.txt", "bounded")
    with pytest.raises(evidence.EvidenceError, match="FORBIDDEN_OR_ARCHIVE"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_unrelated_test_and_non_genuine_trace(tmp_path: Path) -> None:
    import zipfile

    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    root = tmp_path / "unrelated-test"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["report"]["suites"][0]["specs"][0].update({"file": "unrelated.spec.ts", "title": "unrelated passing test"})
    (root / "playwright.json").write_text(json.dumps(packet["report"]), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="PLAYWRIGHT_RESULT"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "metadata-trace"
    write_heartbeat2_packet(root, sources, evidence)
    rewrite_heartbeat2_trace(root, lambda members: members.__setitem__("0-trace.trace", members["0-trace.trace"].splitlines()[0]), evidence)
    with pytest.raises(evidence.EvidenceError, match="TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "network-only"
    write_heartbeat2_packet(root, sources, evidence)
    with zipfile.ZipFile(root / "trace.zip", "w") as archive:
        archive.writestr("0-trace.network", "")
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["traceSha256"] = evidence.sha256((root / "trace.zip").read_bytes())
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_dead_listener_markers_and_payload_disagreement(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    root = tmp_path / "dead-listeners"
    write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text('const dead = [\'page.on("request")\', \'page.on("response")\', "response.request()", "new WeakMap<Request"];\n', encoding="utf-8")
    manifest = json.loads((root / "manifest.json").read_text())
    next(item for item in manifest["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "payload-disagreement"
    packet = write_heartbeat2_packet(root, sources, evidence)
    forged = dict(packet["bundle"]["walkthrough"])
    forged["status"] = "FORGED"
    raw = json.dumps(forged, separators=(",", ":"), sort_keys=True).encode()
    import base64
    packet["traffic"]["responses"][6].update({"bodyBase64": base64.b64encode(raw).decode(), "bodySha256": evidence.sha256(raw)})
    packet["bundle"]["walkthrough"] = forged
    (root / "traffic.json").write_text(json.dumps(packet["traffic"]), encoding="utf-8")
    (root / "bundle.json").write_text(json.dumps(packet["bundle"]), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_duplicate_claim_consent_and_semantic_artifact_forgery(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    mutations = (
        ("duplicate", lambda p: p["bundle"]["source"]["acceptedChunks"].append(dict(p["bundle"]["source"]["acceptedChunks"][0]))),
        ("claim", lambda p: p["bundle"]["walkthrough"]["evaluation"]["claimSupports"][0].__setitem__("claimId", "claim-other")),
        ("consent", lambda p: p["bundle"]["consent"].update({"sourceRunId": "run-other", "sourceEvaluationId": "eval-other"})),
    )
    for label, mutate in mutations:
        root = tmp_path / label
        packet = write_heartbeat2_packet(root, sources, evidence)
        cast(Callable[[dict[str, Any]], Any], mutate)(packet)
        (root / "bundle.json").write_text(json.dumps(packet["bundle"]), encoding="utf-8")
        with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN"):
            evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "semantic-artifact"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["artifact"].write_text('{"forged":"unrelated"}', encoding="utf-8")
    digest = evidence.sha256(packet["artifact"].read_bytes())
    packet["bundle"]["artifacts"]["video"]["sha256"] = digest
    (root / "bundle.json").write_text(json.dumps(packet["bundle"]), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="ARTIFACT_BINDING"):
        evidence._artifacts(root, packet["bundle"]["artifacts"], packet["bundle"])
    with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN|ARTIFACT_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_aggregate_nested_archive_expansion(tmp_path: Path, monkeypatch: Any) -> None:
    import io
    import zipfile

    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "aggregate", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    monkeypatch.setattr(evidence, "MAX_SCAN_BYTES", 1024)
    nested_archives = []
    for marker in (b"a", b"b"):
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("payload.bin", marker * 700)
        nested_archives.append(nested.getvalue())
    with zipfile.ZipFile(root / "aggregate.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("one.zip", nested_archives[0])
        archive.writestr("two.zip", nested_archives[1])
    with pytest.raises(evidence.EvidenceError, match="FORBIDDEN_OR_ARCHIVE"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_nested_listener_and_request_body_laundering(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    root = tmp_path / "nested-listener"
    write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text('test("Heartbeat 2 local reviewer demo", async ({ page }) => { function neverCalled() { const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); } await page.goto("/"); });', encoding="utf-8")
    manifest = json.loads((root / "manifest.json").read_text())
    next(item for item in manifest["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "request-body"
    write_heartbeat2_packet(root, sources, evidence)
    def forge_request(members: dict[str, bytes]) -> None:
        records = [json.loads(line) for line in members["0-trace.network"].splitlines()]
        records[0]["snapshot"]["request"]["postData"] = {"text": "forged"}
        members["0-trace.network"] = "\n".join(json.dumps(item) for item in records).encode()
    rewrite_heartbeat2_trace(root, forge_request, evidence)
    with pytest.raises(evidence.EvidenceError, match="TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_verifier_rejects_response_scope_duplicates_and_active_artifact_fields(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    root = tmp_path / "consent-response"
    write_heartbeat2_packet(root, sources, evidence)
    replace_heartbeat2_response(root, 8, {"consentRecordId": "consent-1", "projectId": "wrong", "sourceRunId": "wrong", "sourceEvaluationId": "wrong", "sourceEvaluationChecksum": "wrong"}, evidence)
    with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "empty-languages"
    write_heartbeat2_packet(root, sources, evidence)
    replace_heartbeat2_response(root, 0, {"languages": []}, evidence)
    with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    root = tmp_path / "duplicate-support"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["bundle"]["walkthrough"]["evaluation"]["claimSupports"].append(dict(packet["bundle"]["walkthrough"]["evaluation"]["claimSupports"][0]))
    with pytest.raises(evidence.EvidenceError, match="PRODUCT_JOIN"):
        evidence._joins(root, packet["bundle"])
    video = json.loads(packet["artifact"].read_text())
    video.update({"allowNetworkEgress": True, "providerCallMade": True, "hostedUrl": "https://example.invalid", "realAudioProduced": True})
    packet["artifact"].write_text(json.dumps(video), encoding="utf-8")
    digest = evidence.sha256(packet["artifact"].read_bytes())
    packet["bundle"]["artifacts"]["video"]["sha256"] = digest
    with pytest.raises(evidence.EvidenceError, match="ARTIFACT_BINDING"):
        evidence._artifacts(root, packet["bundle"]["artifacts"], packet["bundle"])


def test_heartbeat2_reset5_binds_canonical_authority() -> None:
    assert phase1.ISSUE_308_RESET5_AUTHORITY == {
        "url": "https://github.com/imrohitagrawal/narratwin-ai/issues/308#issuecomment-5118185764",
        "databaseId": 5118185764,
        "author": "imrohitagrawal",
        "createdAt": "2026-07-29T13:09:38Z",
        "updatedAt": "2026-07-29T15:34:06Z",
        "sha256": "31da9a24040a729c46f4d0f6c4c465b0b24145765b58f50394aab5fc0948626f",
        "preflightSha256": "1310c249e4ebe793c9fbfe94d833e9e7d5bde8191927f3b2a52237663a4e9cbd",
    }


def test_heartbeat2_reset5_uses_capture_safe_browser_source_policy(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"

    assert evidence.scan_h2_browser_sources(spec)["forbiddenMatchCount"] == 0
    spec.write_text(spec.read_text().replace('await page.goto("/");', 'await page.route("**/*", route => route.fulfill());'), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence.scan_h2_browser_sources(spec)


def test_heartbeat2_reset5_rejects_handcrafted_minimal_execution(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    def minimal(members: dict[str, bytes]) -> None:
        members["0-trace.trace"] = b'{"version":8,"type":"context-options","browserName":"chromium","options":{"baseURL":"http://127.0.0.1:3122","serviceWorkers":"block"}}\n{"type":"before","callId":"call@1","class":"Frame","method":"goto","pageId":"page@1"}\n{"type":"after","callId":"call@1"}'
        members["0-trace.stacks"] = b'{"files":["/workspace/frontend/tests/heartbeat2-browser.spec.ts"],"stacks":[[1,[[0,12,1,""]]]]}'
    rewrite_heartbeat2_trace(root, minimal, evidence)

    with pytest.raises(evidence.EvidenceError, match="PLAYWRIGHT_RESULT|TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_reset5_rejects_decoy_title_listener_capture(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text('''import { test, type Request } from "@playwright/test";
const title = "Heartbeat 2 local reviewer demo";
const neverCalled = (page: any) => {
  const requestIds = new WeakMap<Request, string>();
  page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); });
  page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); });
};
test(title, async ({ page }) => { await page.goto("/"); });
''', encoding="utf-8")
    next(item for item in packet["manifest"]["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())

    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence._sources(packet["manifest"], "a" * 40, committed=False, source_root=sources)


def test_heartbeat2_reset5_rejects_rebound_write_request_body(tmp_path: Path) -> None:
    import base64

    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    raw = b'{"operation":"submit","body":"unrelated"}'
    packet["traffic"]["requests"][1].update({"bodyBase64": base64.b64encode(raw).decode(), "bodySha256": evidence.sha256(raw)})
    (root / "traffic.json").write_text(json.dumps(packet["traffic"]), encoding="utf-8")
    def rebind(members: dict[str, bytes]) -> None:
        rows = [json.loads(line) for line in members["0-trace.network"].splitlines()]
        rows[1]["snapshot"]["request"]["postData"] = {"text": raw.decode()}
        members["0-trace.network"] = "\n".join(json.dumps(row) for row in rows).encode()
    rewrite_heartbeat2_trace(root, rebind, evidence)

    with pytest.raises(evidence.EvidenceError, match="REQUEST_BINDING|PRODUCT_JOIN|TRAFFIC_LEDGER"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_reset5_rejects_semantic_artifact_aliases(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    video = json.loads(packet["artifact"].read_text())
    video.update({"networkEgressEnabled": True, "externalProviderCallMade": True, "realAudioGenerated": True})
    packet["artifact"].write_text(json.dumps(video), encoding="utf-8")
    digest = evidence.sha256(packet["artifact"].read_bytes())
    packet["bundle"]["artifacts"]["video"]["sha256"] = digest

    with pytest.raises(evidence.EvidenceError, match="ARTIFACT_BINDING"):
        evidence._artifacts(root, packet["bundle"]["artifacts"], packet["bundle"])


@pytest.mark.parametrize("forbidden", [(b"", b""), (b"same", b"same"), (b"unrelated-one", b"unrelated-two")])
def test_heartbeat2_reset5_rejects_unbound_forbidden_sentinels(tmp_path: Path, monkeypatch: Any, forbidden: tuple[bytes, bytes]) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["manifest"]["forbiddenInputs"] = {
        "controlledSha256": evidence.sha256(b"reset5-controlled"),
        "canarySha256": evidence.sha256(b"reset5-canary"),
    }
    (root / "manifest.json").write_text(json.dumps(packet["manifest"]), encoding="utf-8")
    monkeypatch.setattr(evidence, "_sources", lambda *args, **kwargs: (3, 14))

    with pytest.raises(evidence.EvidenceError, match="FORBIDDEN_INPUT"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources, committed=True, forbidden=forbidden)


def test_heartbeat2_reset5_accepts_only_canonical_forbidden_sentinels(tmp_path: Path, monkeypatch: Any) -> None:
    from scripts.ci.heartbeat1_evidence import fixture_constants

    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    values = fixture_constants(Path(__file__).parents[1] / "api" / "test_heartbeat1_a2_exclusion_api.py")
    packet["manifest"]["forbiddenInputs"] = evidence.FORBIDDEN_SHA256S
    (root / "manifest.json").write_text(json.dumps(packet["manifest"]), encoding="utf-8")
    monkeypatch.setattr(evidence, "_sources", lambda *args, **kwargs: (3, 14))

    result = evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources, committed=True, forbidden=(values["INTERNAL_FIXTURE"], values["canary"]))
    assert result["outcome"] == "SEMANTIC_PASS_LOCAL"


def test_heartbeat2_verifier_redacts_forbidden_bytes_from_failure_frame(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    marker = b"controlled-diagnostic-marker"
    with pytest.raises(evidence.EvidenceError, match="STALE_EVIDENCE") as captured:
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="other-run", source_root=sources, forbidden=(marker,))
    verifier_frame = next(entry.frame for entry in captured.traceback if entry.name == "verify_evidence")
    assert "forbidden" not in verifier_frame.f_locals
    assert marker.decode() not in repr(verifier_frame.f_locals)


def test_heartbeat2_verifier_drops_privacy_exception_chain_and_rejects_unsafe_artifact_paths(tmp_path: Path, monkeypatch: Any) -> None:
    import base64
    import traceback

    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    def fail_scan(*args: Any, **kwargs: Any) -> None:
        protected_local = b"controlled-chain-marker"
        encoded_local = base64.b64encode(protected_local)
        if encoded_local:
            raise evidence.PrivacyError("FORBIDDEN")
    monkeypatch.setattr(evidence, "scan_evidence", fail_scan)
    with pytest.raises(evidence.EvidenceError, match="FORBIDDEN_OR_ARCHIVE") as captured:
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    rendered = "".join(traceback.TracebackException.from_exception(captured.value, capture_locals=True).format())
    assert "controlled-chain-marker" not in rendered
    assert "Y29udHJvbGxlZC1jaGFpbi1tYXJrZXI=" not in rendered
    for filename in ("../escape.json", "/tmp/escape.json", "nested/escape.json", "nested\\escape.json"):
        with pytest.raises(evidence.EvidenceError, match="ARTIFACT_BINDING"):
            evidence._artifact_path(root, filename)


@pytest.mark.parametrize("body", [
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); await page.evaluate(() => Function("globalThis.fe" + "tch = () => ({ok:true})")());''',
    '''const marker = "}"; if (false) { const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); }''',
    '''return; const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); });''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); await page.context().newCDPSession(page);''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); eval("globalThis.fe" + "tch = () => ({ok:true})");''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); page.removeAllListeners("request"); page.removeAllListeners("response");''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); (0, eval)("globalThis.fe" + "tch = () => ({ok:true})");''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); ([]["filter"]["constructor"])("globalThis.fe" + "tch = () => ({ok:true})")();''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); page.removeAllListeners.bind(page)("request"); page.removeAllListeners.bind(page)("response");''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); return;''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); test.skip();''',
    '''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); throw new Error("stop");''',
    r'''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); \u0065val("globalThis.fe" + "tch = () => ({ok:true})");''',
    r'''const requestIds = new WeakMap<Request, string>(); page.on("request", (request) => { requestIds.set(request, request.url()); requests.push({body: request.postDataBuffer()}); }); page.on("response", async (response) => { const request = response.request(); responses.push({requestId: requestIds.get(request), body: await response.body()}); }); page.rem\u006fveAllListeners("request");''',
])
def test_heartbeat2_reset5_rejects_dynamic_execution_and_dead_listener_control_flow(tmp_path: Path, body: str) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text(f'import {{ test, type Request }} from "@playwright/test"; test("Heartbeat 2 local reviewer demo", async ({{ page }}) => {{ {body} await page.goto("/"); }});', encoding="utf-8")
    next(item for item in packet["manifest"]["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence._sources(packet["manifest"], "a" * 40, committed=False, source_root=sources)


def test_heartbeat2_reset5_rejects_shadowed_playwright_test_binding(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text(spec.read_text().replace("import { test, type Request }", "import { type Request }; const test = (...args: unknown[]) => undefined;"), encoding="utf-8")
    next(item for item in packet["manifest"]["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence._sources(packet["manifest"], "a" * 40, committed=False, source_root=sources)


@pytest.mark.parametrize("replacement", ["", "test.skip(!process.env.H2_WRONG_DIR, \"runs only through the canonical Heartbeat 2 evidence runner\");"])
def test_heartbeat2_rejects_missing_or_altered_canonical_test_guard(tmp_path: Path, replacement: str) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text(spec.read_text().replace(evidence.TEST_GUARD, replacement), encoding="utf-8")
    next(item for item in packet["manifest"]["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence._sources(packet["manifest"], "a" * 40, committed=False, source_root=sources)


def test_heartbeat2_reset5_rejects_conditional_top_level_test_registration(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    spec = sources / "frontend/tests/heartbeat2-browser.spec.ts"
    spec.write_text(spec.read_text().replace("\ntest(", "\nfalse && test("), encoding="utf-8")
    next(item for item in packet["manifest"]["sourceGraph"] if item["path"].endswith("heartbeat2-browser.spec.ts"))["sha256"] = evidence.sha256(spec.read_bytes())
    with pytest.raises(evidence.EvidenceError, match="BROWSER_SOURCE"):
        evidence._sources(packet["manifest"], "a" * 40, committed=False, source_root=sources)


def test_heartbeat2_reset5_rejects_uncorrelated_report_and_trace_stacks(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["report"]["stats"]["startTime"] = "2040-01-01T00:00:00Z"
    packet["report"]["suites"][0]["specs"][0]["line"] = 999
    (root / "playwright.json").write_text(json.dumps(packet["report"]), encoding="utf-8")
    rewrite_heartbeat2_trace(root, lambda members: members.__setitem__("0-trace.stacks", b'{"files":["/workspace/frontend/tests/heartbeat2-browser.spec.ts"],"stacks":[[900,[[0,999,1,""]]],[901,[[0,999,1,""]]],[902,[[0,999,1,""]]],[903,[[0,999,1,""]]],[904,[[0,999,1,""]]],[905,[[0,999,1,""]]],[906,[[0,999,1,""]]],[907,[[0,999,1,""]]]]}'), evidence)
    with pytest.raises(evidence.EvidenceError, match="PLAYWRIGHT_RESULT|TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def replace_heartbeat2_request(root: Path, index: int, raw: bytes, evidence: Any) -> None:
    import base64
    traffic = json.loads((root / "traffic.json").read_text())
    traffic["requests"][index].update({"bodyBase64": base64.b64encode(raw).decode(), "bodySha256": evidence.sha256(raw)})
    (root / "traffic.json").write_text(json.dumps(traffic), encoding="utf-8")
    def mutate(members: dict[str, bytes]) -> None:
        rows = [json.loads(line) for line in members["0-trace.network"].splitlines()]
        rows[index]["snapshot"]["request"]["postData"] = {"text": raw.decode()}
        members["0-trace.network"] = "\n".join(json.dumps(row) for row in rows).encode()
    rewrite_heartbeat2_trace(root, mutate, evidence)


def test_heartbeat2_reset5_rejects_duplicate_multipart_and_json_keys(tmp_path: Path) -> None:
    import base64
    evidence: Any = load_heartbeat2_evidence_module()
    sources = tmp_path / "sources"
    mutations: tuple[tuple[str, int, Callable[[bytes], bytes]], ...] = (("multipart", 2, lambda raw: raw.replace(b'name="action"', b'name="action"\r\n\r\nACCEPT_FOR_REVIEW\r\n--heartbeat2-reset5-boundary\r\nContent-Disposition: form-data; name="action"', 1)), ("json", 1, lambda raw: raw.replace(b"{", b'{"name":"conflict",', 1)))
    for label, index, mutate in mutations:
        root = tmp_path / label
        packet = write_heartbeat2_packet(root, sources, evidence)
        raw = mutate(base64.b64decode(packet["traffic"]["requests"][index]["bodyBase64"]))
        replace_heartbeat2_request(root, index, raw, evidence)
        with pytest.raises(evidence.EvidenceError, match="REQUEST_BINDING"):
            evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


@pytest.mark.parametrize("active", ['<script src="//example.invalid/active.js"></script>', '<video poster="//example.invalid/frame.png"></video>'])
def test_heartbeat2_reset5_rejects_active_local_preview_content(tmp_path: Path, active: str) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    preview = root / packet["bundle"]["artifacts"]["preview"]["path"]
    preview.write_text(preview.read_text().replace("</body>", active + "</body>"), encoding="utf-8")
    digest = evidence.sha256(preview.read_bytes())
    packet["bundle"]["artifacts"]["preview"]["sha256"] = digest
    with pytest.raises(evidence.EvidenceError, match="ARTIFACT_BINDING"):
        evidence._artifacts(root, packet["bundle"]["artifacts"], packet["bundle"])


def test_heartbeat2_reset5_rejects_non_json_write_content_type(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    packet["traffic"]["requests"][1]["contentType"] = "text/plain"
    with pytest.raises(evidence.EvidenceError, match="REQUEST_BINDING"):
        evidence._request_contract([item for item in packet["traffic"]["requests"] if item["operation"] in {row[0] for row in evidence.WRITES}], packet["bundle"])


@pytest.mark.parametrize("mutate", [
    lambda voice: voice.update({"textChecksum": "sha256:unbound"}),
    lambda voice: voice.update({"textChecksum": "sha256:" + "0" * 64}),
    lambda voice: voice["mockAudioProfile"].update({"durationMillisecondsEstimate": -1}),
    lambda voice: voice.update({"disclosure": {"text": "Mock local TTS placeholder"}}),
])
def test_heartbeat2_reset5_rejects_malformed_voice_semantics(tmp_path: Path, mutate: Any) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    voice = root / packet["bundle"]["artifacts"]["voice"]["path"]
    payload = json.loads(voice.read_text())
    mutate(payload)
    voice.write_text(json.dumps(payload), encoding="utf-8")
    digest = evidence.sha256(voice.read_bytes())
    packet["bundle"]["artifacts"]["voice"]["sha256"] = digest
    with pytest.raises(evidence.EvidenceError, match="ARTIFACT_BINDING"):
        evidence._artifacts(root, packet["bundle"]["artifacts"], packet["bundle"])


def test_heartbeat2_reset5_rejects_duplicate_response_json_keys(tmp_path: Path) -> None:
    import base64
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet = write_heartbeat2_packet(root, sources, evidence)
    response = packet["traffic"]["responses"][0]
    raw = base64.b64decode(response["bodyBase64"]).replace(b"{", b'{"languages":"conflict",', 1)
    response.update({"bodyBase64": base64.b64encode(raw).decode(), "bodySha256": evidence.sha256(raw)})
    with pytest.raises(evidence.EvidenceError, match="TRAFFIC_LEDGER"):
        evidence._traffic(packet["traffic"], packet["bundle"])


def heartbeat2_ci_context() -> dict[str, str]:
    return {"repository": "imrohitagrawal/narratwin-ai", "eventName": "pull_request", "workflow": "ci", "workflowRef": "imrohitagrawal/narratwin-ai/.github/workflows/ci.yml@refs/pull/309/merge", "workflowSha": "b" * 40, "job": "frontend", "runId": "5121265229", "runAttempt": "1", "headSha": "a" * 40}


def bind_heartbeat2_ci_execution(root: Path, packet: dict[str, Any], evidence: Any, ci: dict[str, str]) -> dict[str, Any]:
    graph = {item["path"]: item["sha256"] for item in packet["manifest"]["sourceGraph"]}
    record = {"schema": "heartbeat2-ci-execution-v1", "provider": "github-actions", **ci, "evidenceRunId": "run-308", "producer": "scripts/ci/heartbeat2-browser.sh", "playwrightExitCode": 0, "startedAt": "2026-07-29T17:00:00Z", "completedAt": "2026-07-29T17:00:10Z", "workflowSourceSha256": graph[".github/workflows/ci.yml"], "runnerSourceSha256": graph["scripts/ci/heartbeat2-browser.sh"], "reportSha256": evidence.sha256((root / "playwright.json").read_bytes()), "traceSha256": evidence.sha256((root / "trace.zip").read_bytes())}
    (root / "execution.json").write_text(json.dumps(record), encoding="utf-8")
    packet["manifest"]["execution"] = "execution.json"
    (root / "manifest.json").write_text(json.dumps(packet["manifest"]), encoding="utf-8")
    return record


def test_heartbeat2_reset6_binds_authority_budget_and_workflow_allowlist() -> None:
    assert phase1.ISSUE_308_RESET6_AUTHORITY == {"url": "https://github.com/imrohitagrawal/narratwin-ai/issues/308#issuecomment-5121265229", "databaseId": 5121265229, "author": "imrohitagrawal", "createdAt": "2026-07-29T17:24:48Z", "updatedAt": "2026-07-29T17:24:48Z", "sha256": "6fcfa8d626f45a0791a157c810471c057eed1d6160543406ecf6a22baa3a6810", "preflightSha256": "20d7c1be5154d139a7149d43b960df639c31a671e7da5f9d8ba1b1c0447a0db6"}
    assert phase1.ISSUE_308_LINE_CAPS[phase1.ISSUE_308_H2_A_BRANCH] == 1600
    assert ".github/workflows/ci.yml" in phase1.ISSUE_308_H2_A_ALLOWED_CHANGED_FILES


def test_heartbeat2_pr_b_binds_preflight_and_product_faithful_fixture() -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    assert phase1.ISSUE_308_H2_B_PREFLIGHT_AUTHORITY == {
        "url": "https://github.com/imrohitagrawal/narratwin-ai/issues/308#issuecomment-5122147727",
        "databaseId": 5122147727,
        "author": "imrohitagrawal",
        "createdAt": "2026-07-29T18:47:19Z",
        "updatedAt": "2026-07-29T18:47:19Z",
        "sha256": "0b2272ae16352f5dbc723598abbcaf28518ed5106e6c678214cf1c6775e40534",
    }
    assert phase1.ISSUE_308_LINE_CAPS[phase1.ISSUE_308_H2_B_BRANCH] == 900
    assert len(phase1.ISSUE_308_H2_B_ALLOWED_CHANGED_FILES) == 11
    assert ".github/workflows/ci.yml" not in phase1.ISSUE_308_H2_B_ALLOWED_CHANGED_FILES
    assert evidence.PUBLIC_FIXTURE_SHA256 == "9cefe4184b2a67d4cdc56d66d005b90409e06ad449c4c426b7d6e012125bfcb6"


def test_heartbeat2_reset6_workflow_is_exact_head_fail_fast_and_success_only() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "ref: ${{ github.event.pull_request.head.sha || github.sha }}" in workflow
    assert "NARRATWIN_H2_EXPECTED_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}" in workflow
    assert "if: ${{ hashFiles('scripts/ci/heartbeat2-browser.sh') != '' }}" in workflow
    assert "run: bash scripts/ci/heartbeat2-browser.sh" in workflow
    assert "jq -e '.outcome == \"CI_EXECUTION_BOUND\" and .executionAuthenticity == \"GITHUB_ACTIONS\" and .headSha == env.NARRATWIN_H2_EXPECTED_HEAD and .githubRunId == env.GITHUB_RUN_ID and .githubRunAttempt == env.GITHUB_RUN_ATTEMPT' reports/heartbeat2/published/ci-verification.json" in workflow
    assert "if: success() && hashFiles('scripts/ci/heartbeat2-browser.sh') != '' && hashFiles('reports/heartbeat2/published/**') != ''" in workflow
    assert "name: heartbeat2-browser-evidence-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "if-no-files-found: error" in workflow
    assert "continue-on-error" not in workflow


def test_heartbeat2_runner_supports_clean_checkout_without_optional_public_directory() -> None:
    runner = Path("scripts/ci/heartbeat2-browser.sh").read_text(encoding="utf-8")
    assert "if [ -d frontend/public ]; then" in runner
    assert "mkdir -p frontend/.next/standalone/public" in runner
    assert 'cp "$RUNTIME/verification.json" "$PUBLISHED/ci-verification.json"' in runner


def test_heartbeat2_reset6_separates_local_semantics_from_ci_execution(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    local = evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)
    assert local["outcome"] == "SEMANTIC_PASS_LOCAL" and local["executionAuthenticity"] == "UNATTESTED"


def test_heartbeat2_reset6_accepts_exact_ci_execution_binding(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    packet, ci = write_heartbeat2_packet(root, sources, evidence), heartbeat2_ci_context()
    bind_heartbeat2_ci_execution(root, packet, evidence, ci)
    result = evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources, ci_context=ci)
    assert result["outcome"] == "CI_EXECUTION_BOUND" and result["executionAuthenticity"] == "GITHUB_ACTIONS"
    assert result["githubRunId"] == ci["runId"] and result["githubRunAttempt"] == ci["runAttempt"]


@pytest.mark.parametrize(("field", "value"), [("headSha", "c" * 40), ("runAttempt", "2"), ("evidenceRunId", "other-run"), ("playwrightExitCode", 1), ("traceSha256", "0" * 64)])
def test_heartbeat2_reset6_rejects_rebound_or_failed_ci_execution(tmp_path: Path, field: str, value: Any) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / field, tmp_path / "sources"
    packet, ci = write_heartbeat2_packet(root, sources, evidence), heartbeat2_ci_context()
    record = bind_heartbeat2_ci_execution(root, packet, evidence, ci)
    record[field] = value
    (root / "execution.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(evidence.EvidenceError, match="CI_PROVENANCE"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources, ci_context=ci)


def test_heartbeat2_reset6_rejects_ignored_external_trace_resource(tmp_path: Path) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    root, sources = tmp_path / "packet", tmp_path / "sources"
    write_heartbeat2_packet(root, sources, evidence)
    def add_external(members: dict[str, bytes]) -> None:
        rows = members["0-trace.network"].splitlines()
        rows.append(json.dumps({"type": "resource-snapshot", "snapshot": {"request": {"url": "https://example.invalid/ignored", "method": "GET", "headers": []}, "response": {"status": 200, "content": {}}}}).encode())
        members["0-trace.network"] = b"\n".join(rows)
    rewrite_heartbeat2_trace(root, add_external, evidence)
    with pytest.raises(evidence.EvidenceError, match="TRACE_BINDING"):
        evidence.verify_evidence(root, expected_head="a" * 40, expected_run_id="run-308", source_root=sources)


def test_heartbeat2_reset6_cli_refuses_ci_claim_outside_github_actions(monkeypatch: Any) -> None:
    evidence: Any = load_heartbeat2_evidence_module()
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    with pytest.raises(evidence.EvidenceError, match="CI_PROVENANCE"):
        evidence._main(["--evidence", "missing", "--head", "a" * 40, "--run-id", "run-308", "--ci"])
