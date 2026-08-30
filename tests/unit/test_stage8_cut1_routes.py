from __future__ import annotations

import copy
import importlib.util
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


REPO = Path(__file__).parents[2]
MODULE_PATH = REPO / "scripts/quality/stage8_cut1_routes.py"
PROMPT_CONTRACT_PATH = REPO / "docs/governance/cut1-google-gemini-tts-style-prompts-v1.json"
PROMPT_CONTRACT_VERSION = "cut1-google-gemini-tts-style-prompts-v1"
PROMPT_EXPECTED = {
    "meera": ("Despina", 1398, "1ccd1f295369674878e13640384eac139b8b663639b29066bef86ffc0bb3b0ba"),
    "myra": ("Leda", 1128, "62da228f0db362fe5d7ba07f5e76c4c5ab3d6bb77357009bb188be69b19254f1"),
    "raj": ("Achird", 1326, "1b2426927b82140a76c5927006edc54558778ac76b7c508a704dd70dccd2575e"),
}
REFERENCE_EXPECTED = {
    "meera": (
        "4a650279a67a4a5a328b907e4447a0760a1cf8fe6014dbc9258db803df26c06a",
        ["d6f3f3a250e773bd8528586d9a29ca2732170394c65cc8b56a14330a88ce1e2f"],
    ),
    "myra": (
        "0b8b798d5690a6be3b21aa2779bcb7133cabed08343cb01bb6128b46cf7472a1",
        [
            "a1891952b0bdc9b62ada4dad73f1573ac9713f3bd1874149022e01a18ea8eb6c",
            "7d57778f34ca992ba114a1ada6a34eb41a4af3041eda04de7bddbbdbafffe86b",
            "9c57a380800372902a2b79893cf3cd7fbcd286567e6067285fb84b3367ff86e0",
        ],
    ),
    "raj": (
        "87e942edebde3084e465b20042eaf1c32d64e06f3cd8a6e40458397834978c74",
        ["530a7744fd65af88faf53e1e49dff07035a4bd6f7e5779876b474fd265ecfdd7"],
    ),
}


def load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


routes: Any = load(MODULE_PATH, "stage8_cut1_routes_under_test")
stage8: Any = load(REPO / "scripts/quality/check_stage8_docs.py", "stage8_with_cut1_routes")

ISSUE460_EXPECTED = {
    "docs/governance/preflights/issue-460.json",
    "docs/ADR/0069-semgrep-1-175-override-removal.md",
    "docs/RELEASE_CHECKLIST.md", "docs/RISK_REGISTER.md", "docs/SECURITY_AND_PRIVACY.md",
    "scripts/ci/check_semgrep_security.py", "tools/semgrep/pyproject.toml",
    "tools/semgrep/reviewed-inputs.sha256", "tools/semgrep/uv.lock",
    "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_dependency_security_contract.py", "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/THIRD_PARTY_NOTICES.md", "docs/TRACEABILITY.md",
    "scripts/quality/check_issue16_spec_kit.py", "tests/unit/test_issue16_spec_kit_gate.py",
    "tests/unit/test_issue427_architecture_reset.py", "tests/unit/test_stage8_quality_gate.py",
    ".gitleaksignore", "scripts/ci/check_gitleaks_regression.py",
    "scripts/ci/dependency-security.sh", "tests/unit/test_gitleaks_regression.py",
}
ISSUE460_CORRECTION_PATHS = {
    "scripts/quality/check_issue16_spec_kit.py", "tests/unit/test_issue16_spec_kit_gate.py",
    "tests/unit/test_issue427_architecture_reset.py", "tests/unit/test_stage8_quality_gate.py",
}
ISSUE460_HOSTED_SECURITY_PATHS = {
    ".gitleaksignore", "scripts/ci/check_gitleaks_regression.py",
    "scripts/ci/dependency-security.sh", "tests/unit/test_gitleaks_regression.py",
}
ISSUE460_LINE_CAPS = {
    "docs/governance/preflights/issue-460.json": 180,
    "docs/ADR/0069-semgrep-1-175-override-removal.md": 180,
    "docs/RELEASE_CHECKLIST.md": 80, "docs/RISK_REGISTER.md": 80, "docs/SECURITY_AND_PRIVACY.md": 80,
    "scripts/ci/check_semgrep_security.py": 220, "tools/semgrep/pyproject.toml": 20,
    "tools/semgrep/reviewed-inputs.sha256": 20, "tools/semgrep/uv.lock": 500,
    "scripts/quality/stage8_cut1_routes.py": 180, "tests/unit/test_stage8_cut1_routes.py": 300,
    "tests/unit/test_dependency_security_contract.py": 250, "docs/QUALITY_GATES.md": 80,
    "docs/STAGE_ISSUE_PLAN.md": 80, "docs/STATUS.md": 80, "docs/THIRD_PARTY_NOTICES.md": 80,
    "docs/TRACEABILITY.md": 80,
    "scripts/quality/check_issue16_spec_kit.py": 420,
    "tests/unit/test_issue16_spec_kit_gate.py": 500,
    "tests/unit/test_issue427_architecture_reset.py": 80,
    "tests/unit/test_stage8_quality_gate.py": 80,
    ".gitleaksignore": 20,
    "scripts/ci/check_gitleaks_regression.py": 220,
    "scripts/ci/dependency-security.sh": 80,
    "tests/unit/test_gitleaks_regression.py": 260,
}

ISSUE452_EXPECTED = {
    "docs/governance/preflights/issue-452.json",
    "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json",
    "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json",
    "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json",
    "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json",
    "docs/governance/cut1-provider-bakeoff-contract-v1.json",
    "docs/governance/cut1-presenter-contract-red-freeze-v1.json",
    "scripts/quality/cut1_presenter_contract.py",
    "tests/unit/test_cut1_presenter_contract.py",
    "scripts/quality/check_quality_stage.py",
    "tests/unit/test_issue452_quality_dispatcher.py",
    "tests/unit/test_quality_dispatcher.py",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/ADR/0065-cut1-all-presenter-acceptance-provider-bakeoff.md",
    "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md",
    "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md",
    "docs/ENTERPRISE_READINESS_REGISTER.md",
    "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md",
    "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md",
    "docs/QUALITY_GATES.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
}

ISSUE459_FROZEN_EXPECTED = {
    "docs/governance/preflights/issue-459.json",
    "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md",
    "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json",
    "docs/governance/cut1-controlled-presenter-red-corpus-v1.json",
    "scripts/quality/cut1_controlled_presenter.py",
    "tests/unit/test_cut1_controlled_presenter_red.py",
    "scripts/quality/check_quality_stage.py",
    "tests/unit/test_issue459_quality_dispatcher.py",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/PHASE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "backend/app/cut1_controlled_presenter.py",
    "tests/unit/test_cut1_controlled_presenter.py",
    "docs/ADR/0068-cut1-controlled-presenter-controller.md",
}
ISSUE459_EXPECTED = ISSUE459_FROZEN_EXPECTED | {".gitleaksignore", "scripts/ci/check_gitleaks_regression.py", "tests/unit/test_gitleaks_regression.py", "scripts/quality/check_stage8_docs.py", "tests/unit/test_stage8_quality_gate.py"}
ISSUE459_LINE_CAPS = {
    "docs/governance/preflights/issue-459.json": 220,
    "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md": 850,
    "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json": 450,
    "docs/governance/cut1-controlled-presenter-red-corpus-v1.json": 500,
    "scripts/quality/cut1_controlled_presenter.py": 140,
    "tests/unit/test_cut1_controlled_presenter_red.py": 700,
    "scripts/quality/check_quality_stage.py": 60,
    "tests/unit/test_issue459_quality_dispatcher.py": 140,
    "scripts/quality/stage8_cut1_routes.py": 180,
    "tests/unit/test_stage8_cut1_routes.py": 340,
    "docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md": 500,
    "docs/QUALITY_GATES.md": 120, "docs/STAGE_ISSUE_PLAN.md": 120,
    "docs/PHASE_PLAN.md": 100, "docs/STATUS.md": 160, "docs/TRACEABILITY.md": 120,
    "backend/app/cut1_controlled_presenter.py": 900,
    "tests/unit/test_cut1_controlled_presenter.py": 900,
    "docs/ADR/0068-cut1-controlled-presenter-controller.md": 260, ".gitleaksignore": 20, "scripts/ci/check_gitleaks_regression.py": 220, "tests/unit/test_gitleaks_regression.py": 260, "scripts/quality/check_stage8_docs.py": 60, "tests/unit/test_stage8_quality_gate.py": 100,
}
ISSUE459_BYTE_CAPS = {
    "docs/governance/preflights/issue-459.json": 32_000,
    "docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md": 64_000,
    "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json": 40_000,
    "docs/governance/cut1-controlled-presenter-red-corpus-v1.json": 48_000,
    "scripts/quality/cut1_controlled_presenter.py": 16_000,
    "tests/unit/test_cut1_controlled_presenter_red.py": 60_000,
    "tests/unit/test_issue459_quality_dispatcher.py": 24_000,
    "docs/reviews/ISSUE_459_ENTRY_GATE_REVIEW.md": 48_000,
    "docs/ADR/0068-cut1-controlled-presenter-controller.md": 32_000, ".gitleaksignore": 2_000, "scripts/ci/check_gitleaks_regression.py": 24_000, "tests/unit/test_gitleaks_regression.py": 32_000, "scripts/quality/check_stage8_docs.py": 48_000, "tests/unit/test_stage8_quality_gate.py": 40_000,
}
ISSUE459_T03_EXPECTED = {
    "pyproject.toml",
    "uv.lock",
    "docs/governance/preflights/issue-459-t03.json",
    "docs/governance/cut1-presenter-derivatives-v1.json",
    "frontend/public/demo/cut1/raj-waist-up.webp",
    "frontend/public/demo/cut1/myra-waist-up.webp",
    "backend/app/presenter_registry.py",
    "tests/unit/test_cut1_presenter_derivatives.py",
    "tests/unit/test_dependency_security_contract.py",
    "docs/ADR/0069-cut1-presenter-derivative-readiness-binding.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE459_T03_LINE_CAPS = {
    "pyproject.toml": 20,
    "uv.lock": 200,
    "docs/governance/preflights/issue-459-t03.json": 220,
    "docs/governance/cut1-presenter-derivatives-v1.json": 420,
    "backend/app/presenter_registry.py": 500,
    "tests/unit/test_cut1_presenter_derivatives.py": 700,
    "tests/unit/test_dependency_security_contract.py": 220,
    "docs/ADR/0069-cut1-presenter-derivative-readiness-binding.md": 180,
    "docs/THIRD_PARTY_NOTICES.md": 260,
    "scripts/quality/stage8_cut1_routes.py": 220,
    "tests/unit/test_stage8_cut1_routes.py": 340,
    "docs/QUALITY_GATES.md": 120,
    "docs/STAGE_ISSUE_PLAN.md": 120,
    "docs/STATUS.md": 160,
    "docs/TRACEABILITY.md": 120,
}
ISSUE459_T03_BYTE_CAPS = {
    "frontend/public/demo/cut1/raj-waist-up.webp": 500_000,
    "frontend/public/demo/cut1/myra-waist-up.webp": 500_000,
}
ISSUE459_T05A_EXPECTED = {
    "docs/governance/preflights/issue-459-t05a.json",
    "backend/app/cut1_grounding.py",
    "backend/app/narration.py",
    "tests/unit/test_cut1_atomic_grounding.py",
    "tests/unit/test_cut1_narration.py",
    "docs/ADR/0070-cut1-t05-grounded-narration-handoff.md",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE459_T05A_LINE_CAPS = {
    "docs/governance/preflights/issue-459-t05a.json": 180,
    "backend/app/cut1_grounding.py": 120,
    "backend/app/narration.py": 180,
    "tests/unit/test_cut1_atomic_grounding.py": 260,
    "tests/unit/test_cut1_narration.py": 240,
    "docs/ADR/0070-cut1-t05-grounded-narration-handoff.md": 180,
    "scripts/quality/stage8_cut1_routes.py": 180,
    "tests/unit/test_stage8_cut1_routes.py": 320,
    "docs/QUALITY_GATES.md": 100,
    "docs/STAGE_ISSUE_PLAN.md": 120,
    "docs/STATUS.md": 120,
    "docs/TRACEABILITY.md": 100,
}
ISSUE466_EXPECTED = {
    "docs/governance/preflights/issue-466.json",
    "docs/governance/cut1-project-facts-v1.json",
    "backend/app/cut1_grounding.py",
    "tests/unit/test_cut1_atomic_grounding.py",
    "tests/unit/test_cut1_narration.py",
    "docs/ADR/0072-cut1-presenter-source-integrity.md",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_stage8_quality_gate.py",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE466_LINE_CAPS = {
    "docs/governance/preflights/issue-466.json": 320,
    "docs/governance/cut1-project-facts-v1.json": 220,
    "backend/app/cut1_grounding.py": 320,
    "tests/unit/test_cut1_atomic_grounding.py": 520,
    "tests/unit/test_cut1_narration.py": 240,
    "docs/ADR/0072-cut1-presenter-source-integrity.md": 220,
    "scripts/quality/stage8_cut1_routes.py": 140,
    "tests/unit/test_stage8_cut1_routes.py": 240,
    "tests/unit/test_stage8_quality_gate.py": 40,
    "docs/QUALITY_GATES.md": 120,
    "docs/STAGE_ISSUE_PLAN.md": 120,
    "docs/STATUS.md": 180,
    "docs/TRACEABILITY.md": 120,
}
ISSUE459_T05B_EXPECTED = {
    ".gitleaksignore",
    "docs/governance/preflights/issue-459-t05b.json",
    "backend/app/cut1_audio.py",
    "backend/app/tts_provider.py",
    "backend/app/stage6.py",
    "tests/unit/test_cut1_audio.py",
    "tests/unit/test_stage6_tts_provider.py",
    "docs/ADR/0071-cut1-audio-caption-authority.md",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/DATA_MODEL.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "scripts/ci/check_gitleaks_regression.py",
    "tests/unit/test_gitleaks_regression.py",
}
ISSUE459_T05B_LINE_CAPS = {path: 3600 for path in ISSUE459_T05B_EXPECTED}
ISSUE475_EXPECTED = {
    "backend/app/cut1_audio.py",
    "tests/unit/test_cut1_audio.py",
    "docs/governance/preflights/issue-475.json",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/ADR/0071-cut1-audio-caption-authority.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_MODEL.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/QUALITY_GATES.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE475_LINE_CAPS = {
    "backend/app/cut1_audio.py": 340,
    "tests/unit/test_cut1_audio.py": 600,
    "docs/governance/preflights/issue-475.json": 260,
    "scripts/quality/stage8_cut1_routes.py": 160,
    "tests/unit/test_stage8_cut1_routes.py": 240,
    "docs/ADR/0071-cut1-audio-caption-authority.md": 120,
    "docs/API_CONTRACT.md": 60,
    "docs/DATA_MODEL.md": 80,
    "docs/SECURITY_AND_PRIVACY.md": 80,
    "docs/QUALITY_GATES.md": 100,
    "docs/STATUS.md": 100,
    "docs/TRACEABILITY.md": 100,
}
ISSUE468_EXPECTED = {
    "AGENTS.md",
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    "docs/governance/preflights/issue-468-scoped-merge-cleanup.json",
    "docs/STATUS.md",
    "docs/agent-context/context-policy-manifest-v1.json",
    "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_quality_gate.py",
    "tests/unit/test_stage8_cut1_routes.py",
}
ISSUE468_LINE_CAPS = {
    "AGENTS.md": 70,
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 180,
    "docs/governance/preflights/issue-468-scoped-merge-cleanup.json": 260,
    "docs/STATUS.md": 90,
    "docs/agent-context/context-policy-manifest-v1.json": 200,
    "scripts/quality/check_stage8_docs.py": 80,
    "scripts/quality/stage8_cut1_routes.py": 180,
    "tests/unit/test_stage8_quality_gate.py": 160, "tests/unit/test_stage8_cut1_routes.py": 220,
}
ISSUE468_CLEANUP_CONTRACT = {
    "AGENTS.md": (
        "resolve scoped resource ownership before deletion", "prohibit broad prune operations",
        "before-and-after hashes and status counts", "main...origin/main is 0 ahead / 0 behind",
        "retained, deleted, and recoverability report", "proof of absence",
    ),
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": (
        "inventory every cleanup target and resolve its ownership to the completed PR before deletion",
        "completed implementation and verification worktrees",
        "PR-owned Docker containers, images, volumes, and networks",
        "PR-owned temporary clones, files, and isolated dependencies",
        "do not run broad prune operations",
        "hash staged, unstaged, and untracked state before and after preservation",
        "verify `main...origin/main` is `0` ahead and `0` behind",
        "retained, deleted, and recoverability", "prove scoped resources are absent",
    ),
}


def cleanup_documents() -> dict[str, str]:
    return {path: (REPO / path).read_text(encoding="utf-8") for path in ISSUE468_CLEANUP_CONTRACT}


def remove_cleanup_marker(text: str, marker: str) -> str:
    return re.sub(re.escape(marker).replace(r"\ ", r"\s+"), "removed marker", text, count=1)


EXPECTED = {
    "cut1-475-t05b-runtime-receipt-binding": ISSUE475_EXPECTED,
    "governance-468-scoped-merge-cleanup": ISSUE468_EXPECTED,
    "cut1-466-t05a-presenter-source-integrity": ISSUE466_EXPECTED,
    "governance-473-cleanup-anchor-consumer-fixture": {
        "tests/unit/test_guardrails_check.py",
        "docs/governance/preflights/issue-473-cleanup-anchor-consumer.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
    },
    "governance-471-cleanup-authority-anchor": {
        "docs/governance/preflights/issue-471-cleanup-authority-anchor.json",
        "docs/STATUS.md", "scripts/guardrails_check.py", "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
    },
    "lane-a-cut1-459-controlled-presenter": ISSUE459_EXPECTED,
    "stage8-459-t03-presenter-derivatives": ISSUE459_T03_EXPECTED,
    "stage8-459-t05a-grounded-narration-handoff": ISSUE459_T05A_EXPECTED,
    "stage8-459-t05b-audio-caption-authority": ISSUE459_T05B_EXPECTED,
    "security-460-semgrep-override-removal": ISSUE460_EXPECTED,
    "docs/cut1-acceptance-provider-contract-452": ISSUE452_EXPECTED,
    "docs/cut1-post-443-reconciliation-451": {
        "docs/PHASE_PLAN.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_adversarial_convergence.py",
        "tests/unit/test_guardrails_check.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    "cut1-process-150-semgrep-mcp-renewal": {
        "docs/governance/preflights/issue-150.json",
        "docs/ADR/0061-semgrep-1-172-mcp-override-renewal.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/RISK_REGISTER.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "scripts/ci/check_semgrep_security.py",
        "tools/semgrep/pyproject.toml",
        "tools/semgrep/reviewed-inputs.sha256",
        "tools/semgrep/uv.lock",
        "docs/governance/preflights/issue-428.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0062-nanoid-3-3-18-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    "cut1-process-428-nanoid-3-3-18-security": {
        "docs/governance/preflights/issue-428.json", "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0062-nanoid-3-3-18-security-refresh.md", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "stage8-424-master-program-authority-prelog": {
        "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md",
        "docs/governance/narratwin-master-program-v1.json",
        "docs/governance/preflights/issue-424.json",
        "docs/reviews/ISSUE_424_EXECUTION_SPEC_REVIEW.md",
        "docs/reviews/ISSUE_424_CUT1_FALSE_SUCCESS_REVIEW.md",
        "docs/reviews/ISSUE_424_PLATFORM_SECURITY_LEARNING_REVIEW.md",
        "docs/ADR/0059-master-program-authority-and-route-bootstrap.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
    },
    "stage8-421-cut1-atomic-project-facts": {
        "docs/governance/preflights/issue-421.json",
        "docs/governance/cut1-project-facts-v1.json",
        "backend/app/narration.py",
        "backend/app/cut1_grounding.py",
        "backend/app/rag/models.py",
        "backend/app/stage4.py",
        "backend/app/evaluation_lineage.py",
        "tests/unit/test_cut1_atomic_grounding.py",
        "tests/unit/test_cut1_narration.py",
        "tests/unit/test_evaluation_lineage.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0058-cut1-atomic-project-facts-grounding.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-415-pr-body-live-state-reconciliation": {
        ".github/pull_request_template.md", ".github/workflows/pr-body-consistency.yml", "AGENTS.md", "Makefile",
        "docs/ADR/0040-pr-body-live-state-reconciliation.md", "docs/CODEX_OPERATING_MODEL.md", "docs/QUALITY_GATES.md", "docs/STATUS.md",
        "docs/agent-context/context-policy-manifest-v1.json", "docs/governance/preflights/issue-415.json",
        "scripts/quality/pr_body_consistency.py", "scripts/quality/pr_body_consistency_cli.py", "scripts/quality/stage8_cut1_routes.py",
        "tests/fixtures/pr_body_consistency/live_pr.json", "tests/unit/test_pr_body_consistency.py", "tests/unit/test_stage8_cut1_routes.py",
    },
    "stage8-415-pr-body-consistency-canary-fix": {
        ".github/workflows/pr-body-consistency.yml",
        "docs/STATUS.md",
        "docs/governance/preflights/issue-415.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_pr_body_consistency.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    "cut1-process-413-frontend-runtime-openssl": {
        "docs/governance/preflights/issue-413.json",
        "frontend/Dockerfile",
        "scripts/ci/docker-image-scan.sh",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "tests/unit/test_frontend_container_runtime.py",
        "tests/unit/test_stage8_quality_gate.py",
        "scripts/quality/stage8_cut1_routes.py",
        "scripts/quality/stage8_node_security.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_node_security.py",
        "docs/ADR/0057-frontend-runtime-openssl-3-6-4.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/STAGE_ISSUE_PLAN.md",
    },
    "stage8-368-cut1-google-tts-adapter-implementation": {
        "docs/governance/preflights/issue-368.json",
        "backend/app/narration.py",
        "backend/app/tts_provider.py",
        "backend/app/stage6.py",
        "tests/unit/test_cut1_narration.py",
        "tests/unit/test_stage6_tts_provider.py",
        "tests/unit/test_stage6_multilingual.py",
        "tests/api/test_stage6_multilingual_api.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ARCHITECTURE.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
    },
    "stage8-368-cut1-google-tts-runtime-transport": {
        "docs/governance/preflights/issue-368.json",
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "pyproject.toml",
        "uv.lock",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ARCHITECTURE.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-368-google-tts-quota-project-binding-fix": {
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-368.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/API_CONTRACT.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/ci/verify_branch_protection.py",
        "tests/unit/test_branch_protection_verifier.py",
        "tests/unit/test_governance_preflight_github.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
    },
    "stage8-368-cut1-google-tts-prompt-contract": {
        "docs/governance/preflights/issue-368.json",
        "docs/governance/cut1-google-gemini-tts-style-prompts-v1.json",
        "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    "stage8-368-cut1-local-tts-audio": {
        "docs/governance/preflights/issue-368.json",
        "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/ADR/0002-provider-agnostic-adapters.md",
        "docs/ARCHITECTURE.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    "stage8-382-cut1-narration-lock": {
        "docs/governance/preflights/issue-382.json",
        "backend/app/narration.py",
        "tests/unit/test_cut1_narration.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0055-cut1-narration-speech-lock.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/OBSERVABILITY_AND_COST.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "process-405-heartbeat2-main-reliability": {
        "docs/governance/preflights/issue-405.json",
        ".github/workflows/ci.yml",
        "scripts/ci/heartbeat2-browser.sh",
        "scripts/ci/heartbeat2_evidence.py",
        "tests/unit/test_heartbeat2_evidence.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STATUS.md",
    },
    "cut1-process-403-nanoid-3-3-17-security": {
        "docs/governance/preflights/issue-403.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/ADR/0053-nanoid-3-3-17-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "cut1-process-401-pypdf-6-15-0-security": {
        "docs/governance/preflights/issue-401.json",
        "pyproject.toml",
        "uv.lock",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0052-pypdf-6-15-0-security-refresh.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "cut1-process-396-js-yaml-4-3-1-security": {
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "docs/governance/preflights/issue-396.json",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    "cut1-process-386-modular-route-enforcement": {
        "docs/governance/preflights/issue-386.json",
        "scripts/quality/stage8_cut1_routes.py",
        "scripts/quality/check_stage8_docs.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    "stage8-385-issue280-language-oracle": {
        "docs/governance/preflights/issue-385.json",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    "stage8-384-presenter-asset-route": {
        "docs/governance/preflights/issue-384.json",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-383-presenter-assets": {
        "docs/governance/preflights/issue-383.json",
        "frontend/public/demo/myra-synthetic-presenter.webp",
        "frontend/public/demo/raj-synthetic-presenter.webp",
        "tests/unit/test_cut1_presenter_assets.py",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-367-presenter-registry": {
        "docs/governance/preflights/issue-367.json",
        "backend/app/presenter_registry.py",
        "backend/app/presenter_registry.json",
        "tests/unit/test_cut1_presenter_registry.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/ADR/0054-cut1-presenter-registry.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/SECURITY_AND_PRIVACY.md",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-397-presenter-asset-adr-classifier": {
        "docs/governance/preflights/issue-397.json",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-393-historical-digest-test-isolation": {
        "docs/governance/preflights/issue-393.json",
        "docs/governance/preflights/issue-396.json",
        "docs/ADR/0051-js-yaml-4-3-1-security-refresh.md",
        "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_stage8_quality_gate.py",
        "tests/unit/test_dependency_security_contract.py",
        "scripts/ci/check_container_scan_consensus.py",
        "tests/unit/test_container_scan_consensus.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
}


def completed(args: list[str], code: int = 0, out: str = "", err: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args, code, out, err)


def test_issue471_cleanup_authority_anchor_route_is_exact() -> None:
    branch, base = routes.ISSUE471_BRANCH, routes.ISSUE471_BASE
    expected = {
        "docs/governance/preflights/issue-471-cleanup-authority-anchor.json",
        "docs/STATUS.md",
        "scripts/guardrails_check.py", "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
    }
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 471 and routes.TOTAL_LIMITS[branch] == 1400
    assert routes.TEXT_LIMITS[branch] == {
        "docs/governance/preflights/issue-471-cleanup-authority-anchor.json": 240,
        "docs/STATUS.md": 100,
        "scripts/guardrails_check.py": 260, "tests/unit/test_guardrails_check.py": 360,
        "scripts/quality/stage8_cut1_routes.py": 180, "tests/unit/test_stage8_cut1_routes.py": 260,
    }

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base)

    assert routes.route_base(good, branch) == base


def test_issue473_cleanup_anchor_consumer_route_is_exact() -> None:
    branch, base = routes.ISSUE473_BRANCH, routes.ISSUE473_BASE
    expected = EXPECTED[branch]
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 473
    assert routes.TOTAL_LIMITS[branch] == 580
    assert routes.TEXT_LIMITS[branch] == {
        "tests/unit/test_guardrails_check.py": 80,
        "docs/governance/preflights/issue-473-cleanup-anchor-consumer.json": 180,
        "scripts/quality/stage8_cut1_routes.py": 100,
        "tests/unit/test_stage8_cut1_routes.py": 140,
        "docs/STATUS.md": 80,
    }

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base)

    assert routes.route_base(good, branch) == base


def issue459_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return completed(args, out="".join(f"{path}\0" for path in sorted(ISSUE459_FROZEN_EXPECTED if f"{routes.ISSUE459_BASE}..{routes.ISSUE459_FROZEN_HEAD}" in args else ISSUE459_EXPECTED)) if args[:4] == ["git", "diff", "--name-only", "-z"] else "")


def validate_prompt_contract(contract: dict[str, Any]) -> None:
    assert set(contract) == {
        "schema_version",
        "prompt_contract_version",
        "canonical_encoding",
        "caller_prompt_control",
        "implementation_authorized",
        "profiles",
    }
    assert contract["schema_version"] == "Cut1GoogleGeminiTTSStylePromptContractV1"
    assert contract["prompt_contract_version"] == PROMPT_CONTRACT_VERSION
    assert contract["caller_prompt_control"] is False
    assert contract["implementation_authorized"] is False
    assert contract["canonical_encoding"] == {
        "charset": "UTF-8",
        "bom": False,
        "unicode_normalization": "none",
        "leading_whitespace": False,
        "trailing_whitespace": False,
        "trailing_newline": False,
        "hash_scope": "decoded prompt UTF-8 bytes only",
    }
    profiles = contract["profiles"]
    assert isinstance(profiles, list) and len(profiles) == 3
    assert [profile["semantic_profile_id"] for profile in profiles] == ["meera", "myra", "raj"]
    assert len({profile["semantic_profile_id"] for profile in profiles}) == 3
    expected_fields = {
        "semantic_profile_id",
        "provider_id",
        "provider_name",
        "model",
        "locale",
        "endpoint",
        "provider_voice",
        "prompt_contract_version",
        "prompt",
        "prompt_utf8_bytes",
        "prompt_sha256",
        "accepted_screening_reference_sha256",
        "selected_request_manifest_sha256",
        "limitations",
    }
    for profile in profiles:
        assert set(profile) == expected_fields
        profile_id = profile["semantic_profile_id"]
        voice, byte_count, prompt_sha = PROMPT_EXPECTED[profile_id]
        reference_sha, manifest_shas = REFERENCE_EXPECTED[profile_id]
        prompt = profile["prompt"]
        prompt_bytes = prompt.encode("utf-8")
        assert profile["provider_id"] == "google-cloud-text-to-speech"
        assert profile["provider_name"] == "Google Cloud Text-to-Speech"
        assert profile["model"] == "gemini-2.5-pro-tts"
        assert profile["locale"] == "en-IN"
        assert profile["endpoint"] == "https://eu-texttospeech.googleapis.com"
        assert profile["provider_voice"] == voice
        assert profile["prompt_contract_version"] == PROMPT_CONTRACT_VERSION
        assert len(prompt_bytes) == profile["prompt_utf8_bytes"] == byte_count
        assert hashlib.sha256(prompt_bytes).hexdigest() == profile["prompt_sha256"] == prompt_sha
        assert prompt == prompt.strip() and not prompt.endswith("\n") and not prompt.startswith("\ufeff")
        assert profile["accepted_screening_reference_sha256"] == reference_sha
        assert profile["selected_request_manifest_sha256"] == manifest_shas
        assert profile["limitations"] == {
            "output_nondeterministic": True,
            "accepted_screening_hash_is_reference_evidence_only": True,
            "final_90_to_120_second_narration_requires_validation_and_owner_listening": True,
        }


def test_google_tts_prompt_contract_exact_bytes_hashes_and_closed_schema() -> None:
    contract = json.loads(PROMPT_CONTRACT_PATH.read_text(encoding="utf-8"))
    validate_prompt_contract(contract)
    myra = next(profile for profile in contract["profiles"] if profile["semantic_profile_id"] == "myra")
    assert "Meera’s" in myra["prompt"]
    assert "Meera's" not in myra["prompt"]


def test_google_tts_prompt_contract_rejects_unknown_fourth_profile() -> None:
    contract = json.loads(PROMPT_CONTRACT_PATH.read_text(encoding="utf-8"))
    contract["profiles"].append({**contract["profiles"][0], "semantic_profile_id": "unknown"})
    with pytest.raises(AssertionError):
        validate_prompt_contract(contract)


def test_google_tts_prompt_contract_has_no_forbidden_fields_or_content() -> None:
    contract = json.loads(PROMPT_CONTRACT_PATH.read_text(encoding="utf-8"))
    forbidden_keys = {
        "narration",
        "narration_text",
        "path",
        "private_path",
        "project_id",
        "project_identifier",
        "credential",
        "credentials",
        "token",
        "api_key",
        "secret",
        "request_payload",
        "audio",
        "personal_data",
        "hidden_prompt_alternatives",
    }

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)
        elif isinstance(value, str):
            assert "/Users/" not in value and "file://" not in value

    walk(contract)


def test_google_tts_governance_marks_prompt_prerequisite_satisfied_only() -> None:
    review = (REPO / "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md").read_text(
        encoding="utf-8"
    )
    assert "The prerequisite left open by PR #409 is satisfied" in review
    assert "The governed prompt contract is closed and exact" in review
    assert "callers cannot supply or modify it" in review
    assert "unresolved prompt row" not in review
    assert "**BLOCKED** until a prerequisite" not in review
    assert "not authorize adapter implementation" in review
    assert "Output remains nondeterministic" in review
    assert "exact-hash OWNER listening" in review


def test_routes_are_exact_pre_registered_and_issue386_preflight_matches() -> None:
    assert routes.ROUTES == EXPECTED
    assert {branch: stage8.EFFECTIVE_STAGE8_ROUTES[branch] for branch in EXPECTED} == EXPECTED
    issue150 = json.loads((REPO / "docs/governance/preflights/issue-150.json").read_text(encoding="utf-8"))
    issue150_route = EXPECTED["cut1-process-150-semgrep-mcp-renewal"]
    assert issue150["branch"] == "cut1-process-150-semgrep-mcp-renewal"
    assert set(issue150["scope"]["required"]) == issue150_route
    assert not any(
        path == rule or (rule.endswith("/") and path.startswith(rule))
        for path in issue150_route for rule in issue150["scope"]["forbidden"]
    )
    assert issue150["change_budget"]["maximum_additions_plus_deletions"] == 1000
    assert routes.security_preflight_failures(REPO, 150) == []
    assert routes.security_preflight_failures(REPO, 428) == []
    assert routes.security_preflight_failures(REPO, 460) == []


def test_issue468_route_preflight_and_budgets_are_exact() -> None:
    assert routes.ISSUE468_BRANCH == "governance-468-scoped-merge-cleanup"
    path = REPO / "docs/governance/preflights/issue-468-scoped-merge-cleanup.json"
    preflight = json.loads(path.read_text(encoding="utf-8"))
    assert set(preflight) == {
        "schema_version", "issue_number", "branch", "objective", "status_decision", "scope",
    }
    assert preflight["schema_version"] == "GovernancePreflightV1"
    assert preflight["issue_number"] == 468
    assert preflight["branch"] == routes.ISSUE468_BRANCH
    comments = {"5468560507", "5468813566", "5468861375", "5468898843",
                "5468986974", "5469141049", "5470386759", "5470396865", "5470664256"}
    assert comments <= set(re.findall(r"\d{10}", preflight["objective"]))
    assert {"0b9497679f12502276b15f759263bf32a803cf81",
            "55a0810e2ff327490d6dbadbf58580c06edef600", "35f7beddc9f5ad8c109011bce05eef077c8194f6",
            "af960c9de16e0f648737f105bca275e38895a410"} <= set(preflight["objective"].split())
    assert set(preflight["scope"]["required"]) == ISSUE468_EXPECTED
    assert set(preflight["scope"]["allowed_prefixes"]) == ISSUE468_EXPECTED
    assert routes.ROUTE_ISSUES[routes.ISSUE468_BRANCH] == 468
    assert routes.TOTAL_LIMITS[routes.ISSUE468_BRANCH] == 1500
    assert routes.TEXT_LIMITS[routes.ISSUE468_BRANCH] == ISSUE468_LINE_CAPS


def test_issue468_route_requires_exact_fixed_base_and_branch_point() -> None:
    base = "35f7beddc9f5ad8c109011bce05eef077c8194f6"
    assert getattr(routes, "ISSUE468_BASE", None) == base
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=base + "\n")

    assert routes.route_base(good, routes.ISSUE468_BRANCH) == base
    assert calls == [
        ["git", "rev-parse", f"{base}^{{commit}}"],
        ["git", "merge-base", base, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]

    later = "a" * 40
    for results in (
        (completed([], out=later + "\n"), completed([], out=later + "\n")),
        (completed([], code=1), completed([], out=base + "\n")),
        (completed([], out=base + "\n"), completed([], out=later + "\n"),
         completed([], out=base + "\n")),
    ):
        error = pytest.raises(
            RuntimeError, routes.route_base, lambda _, values=iter(results): next(values),
            routes.ISSUE468_BRANCH,
        )
        assert "Issue #468 fixed base" in str(error.value)


def test_issue468_route_hash_forgery_cannot_bypass_independent_anchor(monkeypatch: Any) -> None:
    documents, clause, real_sha256 = cleanup_documents(), "\nroute-local hash bypass\n", hashlib.sha256
    documents["AGENTS.md"] += clause
    monkeypatch.setattr(routes.hashlib, "sha256",
                        lambda data: real_sha256(data.replace(clause.encode(), b"")))
    assert routes.merge_cleanup_contract_failures(REPO, documents.__getitem__) == [
        "Merge-cleanup authority anchor rejected AGENTS.md bytes."]


@pytest.mark.parametrize(
    ("path", "marker"),
    [(path, marker) for path, markers in ISSUE468_CLEANUP_CONTRACT.items() for marker in markers],
)
def test_issue468_cleanup_contract_rejects_each_marker_mutation(
    path: str, marker: str,
) -> None:
    documents = cleanup_documents()
    documents[path] = remove_cleanup_marker(documents[path], marker)

    failures = routes.merge_cleanup_contract_failures(REPO, documents.__getitem__)

    assert f"Stage 8 merge-closeout contract missing {path} marker: {marker}." in failures


@pytest.mark.parametrize(
    ("path", "marker"),
    (
        ("AGENTS.md", "prohibit broad prune operations"),
        ("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md", "do not run broad prune operations"),
    ),
)
def test_issue468_cleanup_contract_rejects_wrong_section_decoy(
    path: str, marker: str,
) -> None:
    documents = cleanup_documents()
    documents[path] = f"{remove_cleanup_marker(documents[path], marker)}\n\n## Decoy\n\n{marker}\n"

    failures = routes.merge_cleanup_contract_failures(REPO, documents.__getitem__)

    assert f"Stage 8 merge-closeout contract missing {path} marker: {marker}." in failures


@pytest.mark.parametrize(
    ("path", "old", "unsafe"),
    (
        ("AGENTS.md", "prohibit broad prune operations", "need not prohibit broad prune operations"),
        ("AGENTS.md", "Merge cleanup must", 'Deprecated quotation: "Merge cleanup must'),
        ("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md", "do not run broad prune operations",
         "disregard the instruction to do not run broad prune operations"),
        ("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md", "- do not run broad prune operations",
         "- historical quotation: do not run broad prune operations"),
    ),
)
def test_issue468_cleanup_contract_rejects_semantic_reversal_or_deprecation(
    path: str, old: str, unsafe: str,
) -> None:
    documents = cleanup_documents()
    documents[path] = documents[path].replace(old, unsafe, 1)

    assert routes.merge_cleanup_contract_failures(REPO, documents.__getitem__)


@pytest.mark.parametrize("mutation", ("comment", "fence", "subsection", "override"))
def test_issue468_cleanup_contract_rejects_nonoperative_decoys_and_overrides(
    mutation: str,
) -> None:
    documents = cleanup_documents()
    if mutation == "override":
        path, anchor = "AGENTS.md", "   absence for removed resources."
        documents[path] = documents[path].replace(
            anchor, anchor + "\n   This rule is deprecated; broad prune operations are allowed.", 1,
        )
    elif mutation == "comment":
        path, start, end = "AGENTS.md", "   Merge cleanup must", "   absence for removed resources."
        block = documents[path][documents[path].index(start):documents[path].index(end) + len(end)]
        documents[path] = documents[path].replace(
            block, f"<!-- obsolete example\n{block}\n-->\nBroad prune operations are authorized.", 1,
        )
    else:
        path = "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"
        start, end = "- inventory every cleanup target", "  deletion is recoverable"
        prefix = "```text\n" if mutation == "fence" else "#### Historical quotation\n\n"
        suffix = "\n```" if mutation == "fence" else ""
        documents[path] = documents[path].replace(start, prefix + start, 1).replace(
            end, end + suffix + "\n\nBroad prune operations are allowed.", 1,
        )

    assert routes.merge_cleanup_contract_failures(REPO, documents.__getitem__)


def test_issue468_playbook_prohibits_broad_prune_unconditionally() -> None:
    playbook = cleanup_documents()["docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"]
    assert "recursive filesystem pruning; broad prune operations are prohibited" in playbook
    assert "when ownership is unresolved" not in playbook


@pytest.mark.parametrize("countermand", ("Broad prune operations are allowed.", "Broad prune operations are approved.", "Broad prune operations are sanctioned.", "It is permissible to run broad prune operations.", "Broad pruning is encouraged.", "Run broad prune operations.", "Do not prohibit broad prune operations.", "The prohibition on broad prune operations is waived.", "Broad prune operations are not disallowed.", "Broad pruning is prohibited until ownership is resolved.", "Broad-prune operations are allowed.", "Broad\u200b prune operations are allowed.", "Broad prunе operations are allowed.", "Broad " + "scope " * 24 + "prune operations are allowed."))
def test_issue468_cleanup_contract_rejects_coherently_rehashed_countermand(monkeypatch: Any, countermand: str) -> None:
    documents = cleanup_documents()
    path, clause = "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md", f"\n{countermand}\n"
    documents[path] += clause
    real_sha256 = hashlib.sha256
    monkeypatch.setattr(routes.hashlib, "sha256", lambda data: real_sha256(data.replace(clause.encode(), b"")))
    assert "unsafe broad-prune authorization" in " ".join(routes.merge_cleanup_contract_failures(REPO, documents.__getitem__))


def test_issue468_cleanup_contract_rejects_sibling_heading_override() -> None:
    documents = cleanup_documents()
    path = "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md"
    documents[path] = documents[path].replace(
        "\n## Stop Rules", "\n### Cleanup override\n\nBroad prune is allowed.\n\n## Stop Rules", 1,
    )
    assert routes.merge_cleanup_contract_failures(REPO, documents.__getitem__)


def test_security_preflights_reject_duplicate_and_exact_byte_drift(tmp_path: Path) -> None:
    for issue in (150, 428, 460):
        source = REPO / f"docs/governance/preflights/issue-{issue}.json"
        target = tmp_path / f"docs/governance/preflights/issue-{issue}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes() + b"\n")
        assert routes.security_preflight_failures(tmp_path, issue) == [
            f"Issue #{issue} security preflight exact bytes drifted."
        ]
        target.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
        assert routes.security_preflight_failures(tmp_path, issue) == [
            f"Issue #{issue} security preflight is malformed or unreadable."
        ]


def test_security_preflight_identity_rejects_coordinated_branch_mutation(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    issue = 150
    source = REPO / "docs/governance/preflights/issue-150.json"
    target = tmp_path / "docs/governance/preflights/issue-150.json"
    target.parent.mkdir(parents=True)
    artifact = json.loads(source.read_text(encoding="utf-8"))
    artifact["branch"] = routes.ISSUE428_BRANCH
    target.write_text(json.dumps(artifact), encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    monkeypatch.setitem(routes.SECURITY_PREFLIGHTS, issue, (artifact["schema_version"], digest))
    assert routes.security_preflight_failures(tmp_path, issue) == [
        "Issue #150 security preflight identity drifted."
    ]
    issue421 = json.loads((REPO / "docs/governance/preflights/issue-421.json").read_text(encoding="utf-8"))
    issue421_route = EXPECTED[routes.ISSUE421_BRANCH]
    assert issue421["branch"] == routes.ISSUE421_BRANCH
    assert set(issue421["scope"]["required"]) == issue421_route
    assert set(issue421["scope"]["allowed_prefixes"]) == issue421_route
    assert issue421["change_budget"]["exact_paths"] == len(issue421_route) == 21
    assert issue421["change_budget"]["maximum_additions_plus_deletions"] == 4000
    assert issue421["change_budget"]["deletions_grant_credit"] is False
    assert routes.TOTAL_LIMITS[routes.ISSUE421_BRANCH] == 4000
    assert routes.TEXT_LIMITS[routes.ISSUE421_BRANCH] == issue421["change_budget"]["per_file_charged_lines"]

    issue424 = json.loads((REPO / "docs/governance/preflights/issue-424.json").read_text(encoding="utf-8"))
    issue424_branch = "stage8-424-master-program-authority-prelog"
    issue424_route = EXPECTED[issue424_branch]
    assert issue424["branch"] == issue424_branch
    assert set(issue424["scope"]["required"]) == issue424_route
    assert set(issue424) == {
        "schema_version", "issue_number", "branch", "objective", "status_decision", "scope"
    }
    assert issue424["schema_version"] == "GovernancePreflightV1"
    assert issue424["status_decision"] == "update-minimally"
    assert set(issue424["scope"]["allowed_prefixes"]) == issue424_route
    assert len(issue424_route) == 14
    assert routes.ROUTE_ISSUES[issue424_branch] == 424
    assert routes.TOTAL_LIMITS[issue424_branch] == 8500
    assert routes.TEXT_LIMITS[issue424_branch]["scripts/quality/stage8_cut1_routes.py"] == 300
    assert routes.TEXT_LIMITS[issue424_branch]["scripts/guardrails_check.py"] == 100
    assert routes.TEXT_LIMITS[issue424_branch]["tests/unit/test_guardrails_check.py"] == 180


def issue424_fixture(tmp_path: Path) -> Path:
    for relative in (
        "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md",
        "docs/governance/narratwin-master-program-v1.json",
        "docs/governance/preflights/issue-424.json",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, destination)
    return tmp_path


def test_issue424_controller_and_proposal_binding_are_exact_and_fail_closed(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    assert routes.issue424_governance_failures(repository) == []


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("schemaVersion", "MasterProgramBindingV1", "schemaVersion"),
        ("controllerIssue", 425, "controllerIssue"),
        ("documentSha256", "0" * 64, "SHA-256"),
        ("documentBytes", 1, "byte count"),
        ("documentLines", 1, "line count"),
        ("hasTrailingNewline", False, "trailing-newline"),
        ("documentPath", "docs/governance/other.md", "documentPath"),
        ("numberedSections", 41, "numberedSections"),
        ("firstNumberedSection", "1. Wrong", "firstNumberedSection"),
        ("lastNumberedSection", "42. Wrong", "lastNumberedSection"),
        ("acceptedBaseSha", "0" * 40, "accepted base"),
        ("bootstrapBranch", "stage8-424-master-program-authority-prelog-extra", "branch"),
        ("proposalState", "ACCEPTED", "proposal state"),
        ("implementationAuthority", "ACTIVE", "implementation authority"),
        ("activeProgramRoute", {"route": "forbidden"}, "active route"),
    ],
)
def test_issue424_binding_mutations_fail(
    tmp_path: Path, field: str, value: object, expected: str
) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/narratwin-master-program-v1.json"
    binding = json.loads(path.read_text(encoding="utf-8"))
    binding[field] = value
    path.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8")
    assert any(expected in failure for failure in routes.issue424_governance_failures(repository))


def test_issue424_binding_rejects_unknown_fields(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/narratwin-master-program-v1.json"
    binding = json.loads(path.read_text(encoding="utf-8"))
    binding["unreviewedBypass"] = True
    path.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8")
    assert any("unknown binding field" in failure for failure in routes.issue424_governance_failures(repository))


def test_issue424_coordinated_controller_and_binding_mutation_fails(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    controller_path = repository / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    original = controller_path.read_text(encoding="utf-8")
    controller = original.replace(
        "Implementation is forbidden when its governing phase specification",
        "Implementation is permitted when its governing phase specification",
        1,
    )
    assert controller != original
    controller_path.write_text(controller, encoding="utf-8")
    controller_bytes = controller_path.read_bytes()
    binding_path = repository / "docs/governance/narratwin-master-program-v1.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding.update(
        documentSha256=hashlib.sha256(controller_bytes).hexdigest(),
        documentBytes=len(controller_bytes),
        documentLines=len(controller_bytes.splitlines()),
        hasTrailingNewline=controller_bytes.endswith(b"\n"),
    )
    binding_path.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8")
    assert any(
        "pinned controller fingerprint" in failure
        for failure in routes.issue424_governance_failures(repository)
    )


@pytest.mark.parametrize(
    ("canonical", "duplicate"),
    [
        ('"proposalState": "PROPOSED",', '"proposalState": "ACCEPTED",'),
        (
            '"authorityTransition": {',
            '"authorityTransition": {"routeActivationFromProposal": "PERMITTED"},',
        ),
        (
            '"routeActivationGuard": "This proposal never grants execution authority.',
            '"routeActivationGuard": "BYPASS",',
        ),
    ],
)
def test_issue424_binding_rejects_duplicate_authority_members(
    tmp_path: Path, canonical: str, duplicate: str
) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/narratwin-master-program-v1.json"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(canonical, f"{duplicate}\n  {canonical}", 1), encoding="utf-8")
    assert any(
        "duplicate JSON member" in failure
        for failure in routes.issue424_governance_failures(repository)
    )


def test_issue424_binding_rejects_nested_duplicate_transition_member(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/narratwin-master-program-v1.json"
    text = path.read_text(encoding="utf-8").replace(
        '"decisionPath": "docs/governance/narratwin-master-program-authority-decision-v1.json",',
        '"decisionPath": "docs/governance/bypass.json",\n'
        '    "decisionPath": "docs/governance/narratwin-master-program-authority-decision-v1.json",',
        1,
    )
    path.write_text(text, encoding="utf-8")
    assert any(
        "duplicate JSON member" in failure
        for failure in routes.issue424_governance_failures(repository)
    )


def test_issue424_heading_and_waist_up_asset_mutations_fail(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    controller = path.read_text(encoding="utf-8")
    controller = controller.replace(
        "## 42. Final pre-log review gate", "## 99. Final pre-log review gate"
    ).replace("waist-up derivative path and SHA-256", "derivative path and SHA-256")
    path.write_text(controller, encoding="utf-8")
    failures = routes.issue424_governance_failures(repository)
    assert any("numbered heading" in failure for failure in failures)
    assert any("waist-up derivative" in failure for failure in failures)


@pytest.mark.parametrize(
    ("mutate"),
    [
        lambda text: text.replace("## 1. Purpose, claims, and execution authority\n", "", 1),
        lambda text: text.replace("## 1. Purpose, claims, and execution authority", "## 1. Wrong title", 1),
        lambda text: text.replace(
            "## 1. Purpose, claims, and execution authority", "## __FIRST__", 1
        ).replace(
            "## 2. Capability and evidence classification", "## 1. Purpose, claims, and execution authority", 1
        ).replace("## __FIRST__", "## 2. Capability and evidence classification", 1),
    ],
)
def test_issue424_heading_count_title_and_order_mutations_fail(
    tmp_path: Path, mutate: Any
) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    path.write_text(mutate(path.read_text(encoding="utf-8")), encoding="utf-8")
    assert any("numbered heading" in failure for failure in routes.issue424_governance_failures(repository))


def test_issue424_canonical_preflight_rejects_schema_and_scope_mutations(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/preflights/issue-424.json"
    preflight = json.loads(path.read_text(encoding="utf-8"))
    preflight["unreviewed_extension"] = True
    preflight["scope"].pop("allowed_prefixes", None)
    path.write_text(json.dumps(preflight, indent=2) + "\n", encoding="utf-8")
    failures = routes.issue424_governance_failures(repository)
    assert any("GovernancePreflightV1" in failure for failure in failures)


@pytest.mark.parametrize(
    ("canonical", "duplicate"),
    [
        ('"issue_number": 424,', '"issue_number": 999,'),
        ('"status_decision": "update-minimally",', '"status_decision": "activate",'),
        ('"scope": {', '"scope": {"required": [], "allowed_prefixes": []},'),
    ],
)
def test_issue424_preflight_rejects_duplicate_identity_status_and_scope_members(
    tmp_path: Path, canonical: str, duplicate: str
) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/preflights/issue-424.json"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(canonical, f"{duplicate}\n  {canonical}", 1), encoding="utf-8")
    assert any(
        "duplicate JSON member" in failure
        for failure in routes.issue424_governance_failures(repository)
    )


def test_issue424_preflight_rejects_nested_duplicate_required_member(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/preflights/issue-424.json"
    text = path.read_text(encoding="utf-8").replace(
        '"required": [',
        '"required": [],\n    "required": [',
        1,
    )
    path.write_text(text, encoding="utf-8")
    assert any(
        "duplicate JSON member" in failure
        for failure in routes.issue424_governance_failures(repository)
    )


def test_issue424_proposal_requires_a_separate_future_decision_record(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    path = repository / "docs/governance/narratwin-master-program-v1.json"
    binding = json.loads(path.read_text(encoding="utf-8"))
    binding["authorityTransition"]["decisionPath"] = binding["documentPath"]
    path.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8")
    assert any("separate authority decision" in failure for failure in routes.issue424_governance_failures(repository))


def test_issue424_proposal_rejects_a_decision_record_in_the_bootstrap_pr(tmp_path: Path) -> None:
    repository = issue424_fixture(tmp_path)
    decision = repository / routes.ISSUE424_TRANSITION["decisionPath"]
    decision.write_text("{}\n", encoding="utf-8")
    assert any("must not be this proposal or exist" in failure
               for failure in routes.issue424_governance_failures(repository))


def test_issue421_route_requires_exact_accepted_base_and_branch_point() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE421_BASE + "\n")

    assert routes.route_base(good, routes.ISSUE421_BRANCH) == routes.ISSUE421_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE421_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE421_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]

    drifted = iter(
        (
            completed([], out=routes.ISSUE421_BASE + "\n"),
            completed([], out=routes.ISSUE421_BASE + "\n"),
            completed([], out="a" * 40 + "\n"),
        )
    )
    error = pytest.raises(
        RuntimeError,
        routes.route_base,
        lambda _: next(drifted),
        routes.ISSUE421_BRANCH,
    )
    assert "Issue #421 fixed base" in str(error.value)
    issue413 = json.loads((REPO / "docs/governance/preflights/issue-413.json").read_text(encoding="utf-8"))
    issue413_route = EXPECTED["cut1-process-413-frontend-runtime-openssl"]
    assert issue413["branch"] == "cut1-process-413-frontend-runtime-openssl"
    assert set(issue413["scope"]["required"]) == issue413_route
    assert set(issue413["scope"]["allowed_prefixes"]) == issue413_route
    assert issue413_route.isdisjoint(issue413["scope"]["forbidden"])
    assert "exactly nineteen paths" in (REPO / "docs/QUALITY_GATES.md").read_text(encoding="utf-8")
    assert "exact nineteen-path route" in (REPO / "docs/STAGE_ISSUE_PLAN.md").read_text(encoding="utf-8")
    issue368 = json.loads((REPO / "docs/governance/preflights/issue-368.json").read_text(encoding="utf-8"))
    assert issue368["branch"] == routes.ISSUE368_QUOTA_FIX_BRANCH
    assert set(issue368["scope"]["required"]) == EXPECTED[routes.ISSUE368_QUOTA_FIX_BRANCH]
    assert set(issue368["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE368_QUOTA_FIX_BRANCH]
    assert issue368["change_budget"]["exact_paths"] == 19
    assert issue368["change_budget"]["maximum_additions_plus_deletions"] == 2800
    assert issue368["change_budget"]["deletions_grant_credit"] is False
    assert issue368["change_budget"]["per_file_charged_lines"]["backend/app/google_tts_runtime.py"] == 500
    assert issue368["change_budget"]["per_file_charged_lines"]["tests/unit/test_google_tts_runtime.py"] == 600
    assert issue368["change_budget"]["per_file_charged_lines"]["tests/unit/test_stage6_tts_provider.py"] == 800
    assert issue368["change_budget"]["per_file_charged_lines"]["docs/TRACEABILITY.md"] == 220
    assert issue368["change_budget"]["per_file_charged_lines"]["scripts/ci/verify_branch_protection.py"] == 80
    assert issue368["change_budget"]["per_file_charged_lines"]["tests/unit/test_branch_protection_verifier.py"] == 220
    assert issue368["change_budget"]["per_file_charged_lines"]["tests/unit/test_governance_preflight_github.py"] == 80
    assert issue368["change_budget"]["per_file_charged_lines"]["docs/REPOSITORY_GUARDRAILS.md"] == 80
    assert issue368["change_budget"]["per_file_charged_lines"]["docs/agent-context/context-policy-manifest-v1.json"] == 10
    assert "unsafe need outside the nineteen-path route" in issue368["stop_conditions"]
    assert "exact nineteen-path route" in (REPO / "docs/STATUS.md").read_text(encoding="utf-8")
    assert routes.TOTAL_LIMITS[routes.ISSUE368_IMPLEMENTATION_BRANCH] == 3600
    assert routes.TOTAL_LIMITS[routes.ISSUE368_QUOTA_FIX_BRANCH] == 2800
    assert routes.TOTAL_LIMITS[routes.ISSUE368_PROMPT_BRANCH] == 1000
    issue405 = json.loads((REPO / "docs/governance/preflights/issue-405.json").read_text(encoding="utf-8"))
    assert issue405["branch"] == routes.ISSUE405_BRANCH
    assert set(issue405["scope"]["required"]) == EXPECTED[routes.ISSUE405_BRANCH]
    assert set(issue405["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE405_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE405_BRANCH] == 800
    assert routes.TEXT_LIMITS[routes.ISSUE405_BRANCH]["docs/governance/preflights/issue-405.json"] == 220
    artifact = json.loads((REPO / "docs/governance/preflights/issue-386.json").read_text(encoding="utf-8"))
    assert artifact["branch"] == routes.ISSUE386_BRANCH
    assert set(artifact["scope"]["required"]) == EXPECTED[routes.ISSUE386_BRANCH]
    assert set(artifact["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE386_BRANCH]
    assert routes.TEXT_LIMITS[routes.ISSUE386_BRANCH]["tests/unit/test_stage8_quality_gate.py"] == 20
    assert routes.TEXT_LIMITS[routes.ISSUE384_BRANCH]["scripts/quality/check_stage8_docs.py"] == 10
    assert routes.TEXT_LIMITS[routes.ISSUE384_BRANCH]["scripts/quality/stage8_cut1_routes.py"] == 20
    assert routes.TEXT_LIMITS[routes.ISSUE384_BRANCH]["tests/unit/test_stage8_cut1_routes.py"] == 20
    issue393 = json.loads((REPO / "docs/governance/preflights/issue-393.json").read_text(encoding="utf-8"))
    assert issue393["branch"] == routes.ISSUE393_BRANCH and set(issue393["scope"]["required"]) == EXPECTED[routes.ISSUE393_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE393_BRANCH] == 700
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["tests/unit/test_stage8_quality_gate.py"] == 160
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["tests/unit/test_dependency_security_contract.py"] == 80
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["scripts/ci/check_container_scan_consensus.py"] == 80
    assert routes.TEXT_LIMITS[routes.ISSUE393_BRANCH]["tests/unit/test_container_scan_consensus.py"] == 80
    issue396 = json.loads((REPO / "docs/governance/preflights/issue-396.json").read_text(encoding="utf-8"))
    assert issue396["branch"] == routes.ISSUE396_BRANCH
    assert set(issue396["scope"]["required"]) == EXPECTED[routes.ISSUE396_BRANCH]
    assert set(issue396["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE396_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE396_BRANCH] == 500
    assert routes.TEXT_LIMITS[routes.ISSUE396_BRANCH] == {
        path: 180 if path.endswith("issue-396.json") else 80 if path.startswith("tests/unit/") else 40
        for path in EXPECTED[routes.ISSUE396_BRANCH]
    }
    issue397 = json.loads((REPO / "docs/governance/preflights/issue-397.json").read_text(encoding="utf-8"))
    assert issue397["branch"] == routes.ISSUE397_BRANCH
    assert set(issue397["scope"]["required"]) == EXPECTED[routes.ISSUE397_BRANCH]
    assert set(issue397["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE397_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE397_BRANCH] == 500
    assert routes.TEXT_LIMITS[routes.ISSUE397_BRANCH]["scripts/guardrails_check.py"] == 100
    assert routes.TEXT_LIMITS[routes.ISSUE397_BRANCH]["tests/unit/test_guardrails_check.py"] == 160
    assert routes.TEXT_LIMITS[routes.ISSUE397_BRANCH]["docs/agent-context/context-policy-manifest-v1.json"] == 10
    issue401 = json.loads((REPO / "docs/governance/preflights/issue-401.json").read_text(encoding="utf-8"))
    assert issue401["branch"] == routes.ISSUE401_BRANCH
    assert set(issue401["scope"]["required"]) == EXPECTED[routes.ISSUE401_BRANCH]
    assert set(issue401["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE401_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE401_BRANCH] == 600
    issue367 = json.loads((REPO / "docs/governance/preflights/issue-367.json").read_text(encoding="utf-8"))
    assert issue367["branch"] == routes.ISSUE367_BRANCH
    assert set(issue367["scope"]["required"]) == EXPECTED[routes.ISSUE367_BRANCH]
    assert set(issue367["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE367_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE367_BRANCH] == 2000
    assert routes.TEXT_LIMITS[routes.ISSUE367_BRANCH]["backend/app/presenter_registry.py"] == 500
    assert routes.TEXT_LIMITS[routes.ISSUE367_BRANCH]["tests/unit/test_cut1_presenter_registry.py"] == 500
    assert routes.TEXT_LIMITS[routes.ISSUE367_BRANCH]["backend/app/presenter_registry.json"] == 260
    issue403 = json.loads((REPO / "docs/governance/preflights/issue-403.json").read_text(encoding="utf-8"))
    assert issue403["branch"] == routes.ISSUE403_BRANCH
    assert set(issue403["scope"]["required"]) == EXPECTED[routes.ISSUE403_BRANCH]
    assert set(issue403["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE403_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE403_BRANCH] == 650
    assert routes.TEXT_LIMITS[routes.ISSUE403_BRANCH]["scripts/ci/check_container_scan_consensus.py"] == 80
    assert routes.TEXT_LIMITS[routes.ISSUE403_BRANCH]["tests/unit/test_container_scan_consensus.py"] == 80
    issue382 = json.loads((REPO / "docs/governance/preflights/issue-382.json").read_text(encoding="utf-8"))
    assert issue382["branch"] == routes.ISSUE382_BRANCH
    assert set(issue382["scope"]["required"]) == EXPECTED[routes.ISSUE382_BRANCH]
    assert set(issue382["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE382_BRANCH]
    assert routes.TOTAL_LIMITS[routes.ISSUE382_BRANCH] == 3200
    assert routes.TEXT_LIMITS[routes.ISSUE382_BRANCH] == {
        path: 220 if path.endswith("issue-382.json") or path.startswith("docs/ADR/0055-")
        else 750 if path == "backend/app/narration.py"
        else 900 if path == "tests/unit/test_cut1_narration.py"
        else 120 for path in EXPECTED[routes.ISSUE382_BRANCH]
    }
    for path in ("docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md"):
        issue403_contract = (REPO / path).read_text(encoding="utf-8")
        assert "requires exactly fifteen paths" in issue403_contract
        assert "permits at most 650 additions plus deletions" in issue403_contract
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    assert "from scripts.quality.check_stage8_docs" not in module_source
    assert "import scripts.quality.check_stage8_docs" not in module_source


def test_issue424_bootstrap_route_requires_exact_accepted_base_and_branch_point() -> None:
    branch = "stage8-424-master-program-authority-prelog"
    expected_base = "afcf0325c3ec925b68b770eda0bb8c839bcce4dd"
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=expected_base + "\n")

    assert routes.ISSUE424_BASE == expected_base
    assert routes.route_base(good, branch) == expected_base
    assert calls == [
        ["git", "rev-parse", f"{expected_base}^{{commit}}"],
        ["git", "merge-base", expected_base, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]

    drifted = iter(
        (
            completed([], out=expected_base + "\n"),
            completed([], out=expected_base + "\n"),
            completed([], out="a" * 40 + "\n"),
        )
    )
    error = pytest.raises(
        RuntimeError,
        routes.route_base,
        lambda _: next(drifted),
        branch,
    )
    assert "Issue #424 fixed base" in str(error.value)


def test_issue415_route_is_frozen_to_the_authorized_recovery_paths() -> None:
    branch = "stage8-415-pr-body-live-state-reconciliation"
    expected = {
        ".github/pull_request_template.md", ".github/workflows/pr-body-consistency.yml", "AGENTS.md", "Makefile",
        "docs/ADR/0040-pr-body-live-state-reconciliation.md", "docs/CODEX_OPERATING_MODEL.md", "docs/QUALITY_GATES.md", "docs/STATUS.md",
        "docs/agent-context/context-policy-manifest-v1.json", "docs/governance/preflights/issue-415.json",
        "scripts/quality/pr_body_consistency.py", "scripts/quality/pr_body_consistency_cli.py", "scripts/quality/stage8_cut1_routes.py",
        "tests/fixtures/pr_body_consistency/live_pr.json", "tests/unit/test_pr_body_consistency.py", "tests/unit/test_stage8_cut1_routes.py",
    }
    artifact = json.loads((REPO / "docs/governance/preflights/issue-415.json").read_text(encoding="utf-8"))
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 415
    assert routes.TOTAL_LIMITS[branch] == 5000
    assert artifact["branch"] == branch
    assert set(artifact["allowed_paths"]) == expected


def test_issue415_correction_route_is_fixed_to_its_base_and_six_paths() -> None:
    branch = "stage8-415-pr-body-consistency-canary-fix"
    expected = {
        ".github/workflows/pr-body-consistency.yml",
        "docs/STATUS.md",
        "docs/governance/preflights/issue-415.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_pr_body_consistency.py",
        "tests/unit/test_stage8_cut1_routes.py",
    }
    artifact = json.loads((REPO / "docs/governance/preflights/issue-415.json").read_text(encoding="utf-8"))
    correction = artifact["correction_routes"][0]
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 415
    assert routes.TOTAL_LIMITS[branch] == 800
    assert correction["branch"] == branch
    assert correction["accepted_base"] == "20c1f4f19ee20e613f87bbfa6339f17ebb0ad205"
    assert set(correction["allowed_paths"]) == expected


def test_issue415_correction_route_rejects_wrong_fixed_base() -> None:
    branch = "stage8-415-pr-body-consistency-canary-fix"
    outputs = iter((
        completed([], out="20c1f4f19ee20e613f87bbfa6339f17ebb0ad205\n"),
        completed([], out="a" * 40 + "\n"),
    ))
    error = pytest.raises(RuntimeError, routes.route_base, lambda _: next(outputs), branch)
    assert "Issue #415 fixed base" in str(error.value)


def test_issue415_correction_route_cannot_be_claimed_by_a_wrong_branch() -> None:
    branch = routes.ISSUE415_CORRECTION_BRANCH
    lookalike = branch + "-retry"
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES
    assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES
    assert stage8.EFFECTIVE_STAGE8_ROUTES[branch] == EXPECTED[branch]


def test_issue415_correction_route_rejects_an_extra_path_at_stage8_scope(monkeypatch: Any) -> None:
    branch = routes.ISSUE415_CORRECTION_BRANCH
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: [*EXPECTED[branch], "rogue.txt"])
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: rogue.txt"]


def test_issue415_correction_route_rejects_charge_801(monkeypatch: Any) -> None:
    branch = routes.ISSUE415_CORRECTION_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (801, {}))
    failures: list[str] = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == ["Issue #415 charge 801 exceeds 800."]


def test_issue451_route_is_fixed_to_exact_base_paths_and_limits() -> None:
    branch = "docs/cut1-post-443-reconciliation-451"
    expected = EXPECTED[branch]
    assert routes.ISSUE451_BRANCH == branch
    assert routes.ISSUE451_BASE == "59db96aaab6c4e75b12d134dc9b02330c5a982ac"
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 451
    assert routes.TOTAL_LIMITS[branch] == 600
    assert routes.TEXT_LIMITS[branch] == {
        "docs/PHASE_PLAN.md": 120,
        "docs/STATUS.md": 180,
        "scripts/quality/stage8_cut1_routes.py": 100,
        "tests/unit/test_adversarial_convergence.py": 20,
        "tests/unit/test_guardrails_check.py": 20,
        "tests/unit/test_stage8_cut1_routes.py": 120,
        "docs/QUALITY_GATES.md": 80,
        "docs/STAGE_ISSUE_PLAN.md": 80,
    }


def test_issue451_route_requires_exact_fixed_base_and_branch_point() -> None:
    base = "59db96aaab6c4e75b12d134dc9b02330c5a982ac"

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, routes.ISSUE451_BRANCH) == base
    drifted = iter((
        completed([], out=base + "\n"),
        completed([], out="a" * 40 + "\n"),
        completed([], out=base + "\n"),
    ))
    error = pytest.raises(
        RuntimeError,
        routes.route_base,
        lambda _: next(drifted),
        routes.ISSUE451_BRANCH,
    )
    assert "Issue #451 fixed base" in str(error.value)


def test_issue451_route_accepts_exact_scope_and_rejects_every_missing_or_outside_path(
    monkeypatch: Any,
) -> None:
    branch = "docs/cut1-post-443-reconciliation-451"
    expected = EXPECTED[branch]
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(stage8.cut1_routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(stage8.cut1_routes, "route_text_charges", lambda *_: (0, {}))
    for missing in expected:
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, expected - {missing}, failures)
        assert failures == [f"Issue #451 route is missing required path: {missing}"]
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: sorted(expected))
    failures = []
    stage8.check_stage_scope(failures)
    assert failures == []
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope", lambda: [*expected, "rogue.txt"])
    failures = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: rogue.txt"]


def test_issue451_route_rejects_near_match_child_and_unicode_lookalikes(monkeypatch: Any) -> None:
    branch = "docs/cut1-post-443-reconciliation-451"
    for lookalike in (
        branch + "-retry",
        branch + "/child",
        branch.replace("docs", "docѕ"),
    ):
        assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES
        monkeypatch.setattr(stage8, "current_branch", lambda value=lookalike: value)
        failures: list[str] = []
        stage8.check_stage_scope(failures)
        assert failures == [f"Stage 8 scope requires an exact reviewed branch; got {lookalike}."]


def test_issue451_route_rejects_aggregate_and_each_per_path_budget(monkeypatch: Any) -> None:
    branch = "docs/cut1-post-443-reconciliation-451"
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (601, {}))
    failures: list[str] = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == ["Issue #451 charge 601 exceeds 600."]
    for path, limit in {
        "docs/PHASE_PLAN.md": 120,
        "docs/STATUS.md": 180,
        "scripts/quality/stage8_cut1_routes.py": 100,
        "tests/unit/test_adversarial_convergence.py": 20,
        "tests/unit/test_guardrails_check.py": 20,
        "tests/unit/test_stage8_cut1_routes.py": 120,
        "docs/QUALITY_GATES.md": 80,
        "docs/STAGE_ISSUE_PLAN.md": 80,
    }.items():
        monkeypatch.setattr(
            routes,
            "route_text_charges",
            lambda *_, path=path, limit=limit: (limit + 1, {path: limit + 1}),
        )
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
        assert failures == [f"Issue #451 charge for {path} exceeds {limit}."]


def test_issue460_route_is_exact_fixed_budgeted_and_preflight_bound() -> None:
    branch = routes.ISSUE460_BRANCH
    assert branch == "security-460-semgrep-override-removal"
    assert routes.ISSUE460_BASE == "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
    assert routes.ROUTES[branch] == ISSUE460_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 460
    assert routes.TOTAL_LIMITS[branch] == 2600
    assert routes.TEXT_LIMITS[branch] == ISSUE460_LINE_CAPS

    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-460.json").read_text(encoding="utf-8")
    )
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    assert set(artifact["scope"]["required"]) == (
        ISSUE460_EXPECTED - ISSUE460_CORRECTION_PATHS - ISSUE460_HOSTED_SECURITY_PATHS
    )
    assert routes.ISSUE460_CORRECTION_PATHS == ISSUE460_CORRECTION_PATHS
    assert routes.ISSUE460_HOSTED_SECURITY_PATHS == ISSUE460_HOSTED_SECURITY_PATHS
    assert artifact["branch"] == branch


def test_issue452_route_is_exact_fixed_and_budgeted() -> None:
    branch = "docs/cut1-acceptance-provider-contract-452"
    limits = {
        "docs/governance/preflights/issue-452.json": 260,
        "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json": 360,
        "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json": 400,
        "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json": 300,
        "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json": 300,
        "docs/governance/cut1-provider-bakeoff-contract-v1.json": 360,
        "docs/governance/cut1-presenter-contract-red-freeze-v1.json": 220,
        "scripts/quality/cut1_presenter_contract.py": 480,
        "tests/unit/test_cut1_presenter_contract.py": 450,
        "scripts/quality/check_quality_stage.py": 50,
        "tests/unit/test_issue452_quality_dispatcher.py": 120,
        "tests/unit/test_quality_dispatcher.py": 100,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 240,
        "docs/ADR/0065-cut1-all-presenter-acceptance-provider-bakeoff.md": 240,
        "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md": 100,
        "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md": 120,
        "docs/ENTERPRISE_READINESS_REGISTER.md": 100,
        "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md": 100,
        "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md": 120,
        "docs/QUALITY_GATES.md": 100,
        "docs/STATUS.md": 120,
        "docs/THIRD_PARTY_NOTICES.md": 100,
        "docs/TRACEABILITY.md": 100,
    }
    assert routes.ISSUE452_BRANCH == branch
    assert routes.ISSUE452_BASE == "97e8173c2ec1323aa9ced23d43059bca2e5a204f"
    assert routes.ROUTES[branch] == ISSUE452_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 452
    assert routes.TOTAL_LIMITS[branch] == 3600
    assert routes.TEXT_LIMITS[branch] == limits
    assert set(routes.ISSUE452_BYTE_LIMITS) == {
        "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json",
        "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json",
        "scripts/quality/cut1_presenter_contract.py",
        "tests/unit/test_cut1_presenter_contract.py",
        "tests/unit/test_issue452_quality_dispatcher.py",
    }
    assert routes.ISSUE452_BYTE_LIMITS == {
        "docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json": 30_000,
        "docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json": 30_000,
        "scripts/quality/cut1_presenter_contract.py": 40_000,
        "tests/unit/test_cut1_presenter_contract.py": 30_000,
        "tests/unit/test_issue452_quality_dispatcher.py": 30_000,
    }


def test_issue452_requires_fixed_base_and_branch_point() -> None:
    base = routes.ISSUE452_BASE

    def good(_: list[str]) -> subprocess.CompletedProcess[str]:
        return completed([], out=base + "\n")

    assert routes.route_base(good, routes.ISSUE452_BRANCH) == base
    drifted = iter((completed([], out=base + "\n"), completed([], out=base + "\n"), completed([], out="c" * 40 + "\n")))
    error = pytest.raises(RuntimeError, routes.route_base, lambda _: next(drifted), routes.ISSUE452_BRANCH)
    assert "Issue #452 fixed base" in str(error.value)


def test_issue459_route_is_exact_fixed_and_budgeted() -> None:
    branch = routes.ISSUE459_BRANCH
    assert branch == "lane-a-cut1-459-controlled-presenter"
    assert routes.ISSUE459_BASE == "ab97b6eecba6db9c66c37d19b29257c7398f3ab7"
    assert routes.ROUTES[branch] == ISSUE459_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 459
    assert routes.TOTAL_LIMITS[branch] == 4300
    assert routes.TEXT_LIMITS[branch] == ISSUE459_LINE_CAPS
    assert routes.ISSUE459_BYTE_LIMITS == ISSUE459_BYTE_CAPS
    assert routes.ISSUE459_SOURCE_SHA256 == {
        "specs/001-grounded-walkthrough-script/spec.md": "cd16ea947a70271f60a5ce7086e577c1cc25f380baf9a338342bfafb522b8c35",
        "specs/001-grounded-walkthrough-script/plan.md": "166dd8021026eb334607d0dab290c2b121964bcb979e7e502b574f830b45dfd4",
        "specs/001-grounded-walkthrough-script/tasks.md": "9c244de820bf0df1c1d7d7e4c323e5317ba5818cb625f88165e675ce51817fdc",
        "docs/reviews/ISSUE_16_SPEC_KIT_REVIEW_CHECKPOINT.md": "14dbdeb898af240fd30d203e131be8c6e8e29c5803c82463c1b50dc4c8616877",
        ".specify/memory/constitution.md": "ebb0c16c8aa9d967e4c946f31ae600e6e45016bf5c3aa6f098ceac795cd142c2",
        "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md": "2e864e044253a98ea10fdf6dde1ab32a026354aaa5c00cebe3b40756d653936e",
        "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md": "14dbbb6f005d9887ad8ab90340bca9fdcc5fb969579ef3d03f69d5566d0616f8",
        "docs/ENTERPRISE_READINESS_REGISTER.md": "fd42d73871b62f48e018ced1eb5020ffcb53a62cdbdd53936b7c257c22940c1d",
        "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md": "e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b",
        "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md": "7c041dfcca1e5f7e067744eaec18b1577df4be2cf391eb128b786bde7ca1521b",
        "docs/governance/cut1-all-presenter-acceptance-matrix-v1.json": "f61cef9f7731f4603778d1b6a3a9ccccd3682c8e0ad233c9370169320612b2f5",
        "docs/governance/cut1-presenter-live-binding-v2.json": "89199278feabfdcee21fffe4a9ad4d157dd7fc9a11a2529562876cb6ecc74702",
        "docs/governance/cut1-project-facts-v1.json": "cb50de12ce2debb3d52308892428b9711e5efb41fe2ad59b175563809e7d314b",
        "demo/stage8_seed_project.md": "49b75655ddbbe43145a35215069bce2751de66393b39eb68d69b584d7ecfcc5e",
        "docs/demo/PHASE_1_DEMO_SCRIPT.md": "3b071180d4723784d84f5005644fc5a2aa5ef6b6adb6f7caeba2de76d68be435",
        "backend/app/presenter_registry.json": "eb31a953b85ffaf2c43f54e4da7fb89eda740c724967a9301f726c6091ab01c2",
        "docs/PRD.md": "2cde5d9ec7d8e932b25f2fdf66d4dd11f49065b50078f16f59b6a65cbb7d720a",
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": "0a3c14d0d61fbfaf5fe6dec0a7ca3a9412f1b1fd8aa458837f0c3b37b5570db3",
        "docs/ARCHITECTURE.md": "e7515ee96dce07e0d583e15984ea335b6f2499bfd8aa6e9f519bc4a830122fa4",
        "docs/API_CONTRACT.md": "910259f61acbbec4e3432c482d821fd56f2fe8b2073211c7ce112c3cd87405bf",
        "docs/DATA_MODEL.md": "f073c9bff26717233f23c6317b03736c02bee5952b88fa840767f79287b6ec09",
        "docs/SECURITY_AND_PRIVACY.md": "185fe98ffa0b12287b6e7e8a532fac89ffa7a29380db71f8dd6aa4d1b7bc4b62",
        "docs/OBSERVABILITY_AND_COST.md": "c77a0d4ea071e6ea364d9c1f4175361633d4d54962c7fc8d9527033e160d91c6",
        "docs/governance/cut1-blinded-human-evaluation-protocol-v1.json": "fa3759985141639185618fbc595057412dd8582f60ed97fc462b30b7548580b8",
        "docs/governance/cut1-provider-bakeoff-contract-v1.json": "1a3fd981644488203e8c7cc38fc0389092b23b579cce860c3d35a1ca7a1786db",
    }
    assert routes.ISSUE459_EDITABLE_AUTHORITY_SHA256 == {
        "Issue #459": "dd03b171f25b0d249a79834f22674c728e539fa8b171a97b3a4728474e0039d5",
        "5449632582": "07b7cb91660a21ba0a70419ff07195a2532089a087d7a289806142dc81151fa0",
        "5449637037": "f236d2840a7ce35e074b6e370dcc706278772c47fa09b6c18b20a344b22fd1a0",
        "5449765467": "75882f1f3deb8dea77ab945cd58f0526b04644fb4cb208bcd50ddea29846bbe7",
        "5449822130": "48f86809e1032884d5576ceefde06d64785b486e1adae940fe32c2b6391e6cf3",
        "5451872197": "a5241954c115e6849da70401cc029cc4517f83a3629b043462a42becc6146e7d",
        "5452170084": "8c9297b3faf1d6894442017afef2ce58dcb3ec2a6ee6c3037be2024abb2d0fce",
        "5456406377": "dcbc20d52a6acb636463389f7a4996d79b7262f30209576e13522e3576782a7a",
        "5460884573": "6ef7158ffa8347defbed97b3c18a7ad0728cec02ff217b8a0984048fb44887ac", "5461065184": "33a87c363da666be77362291e338323b57311f78c5f1ed22155f619dbe9726fc", "5461070398": "66a28207adc9c9a0438a0d1012baf626561bfca0e6e6644d837328f08808cb1f",
    }
    assert routes.ISSUE459_BASE_SOURCE_SHA256 == {
        "docs/STATUS.md": "9045b595ca1622680f621dffa4dff88435e2fde0d13e3c061ced7eb6df9ae8bf",
        "docs/TRACEABILITY.md": "e597069e3d6b765a9d68e5336ff9597d6d7b809e5ea6f316f22312ca71ea136a",
        "docs/QUALITY_GATES.md": "9f628d22ec62075e560ef478820cf094d923cdf1cfded56a512291c61f6e542b",
        "docs/REPOSITORY_GUARDRAILS.md": "04f8b405bc7ba9b615cc1d5d7e489bcbf643b9de4bfc9b331e5a60c38629e82f",
    }


def test_issue459_requires_exact_reviewed_transition() -> None:
    expected = {routes.ISSUE459_BASE, routes.ISSUE459_FROZEN_HEAD, routes.ISSUE459_TRANSITION_BASE, routes.ISSUE459_TRANSITION_MERGE}

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            value = args[2].removesuffix("^{commit}")
            assert value in expected
            return completed(args, out=value + "\n")
        if args[:4] == ["git", "show", "-s", "--format=%P"]:
            return completed(args, out=f"{routes.ISSUE459_FROZEN_HEAD} {routes.ISSUE459_TRANSITION_BASE}\n")
        assert args[:3] == ["git", "merge-base", "--is-ancestor"]
        return completed(args)

    assert routes.route_base(good, routes.ISSUE459_BRANCH) == routes.ISSUE459_TRANSITION_BASE

    for rejected in expected:
        def missing(args: list[str], *, target: str = rejected) -> subprocess.CompletedProcess[str]:
            result = good(args)
            if args[:2] == ["git", "rev-parse"] and args[2] == f"{target}^{{commit}}":
                return completed(args, code=128)
            return result

        error = pytest.raises(RuntimeError, routes.route_base, missing, routes.ISSUE459_BRANCH)
        assert "Issue #459 reviewed transition" in str(error.value)

    for corrupt in ("parents", "ancestry"):
        def broken(args: list[str], *, kind: str = corrupt) -> subprocess.CompletedProcess[str]:
            if kind == "parents" and args[:4] == ["git", "show", "-s", "--format=%P"]:
                return completed(args, out=f"{routes.ISSUE459_TRANSITION_BASE}\n")
            return (completed(args, code=1) if kind == "ancestry" and
                    args[:3] == ["git", "merge-base", "--is-ancestor"] else good(args))
        error = pytest.raises(RuntimeError, routes.route_base, broken, routes.ISSUE459_BRANCH)
        assert "Issue #459 reviewed transition" in str(error.value)


def test_issue459_t03_route_freezes_authority_scope_and_budgets() -> None:
    branch = routes.ISSUE459_T03_BRANCH
    assert routes.ISSUE459_T03_BASE == "4ef3a8ba70cbf97b7704f5f589b0887f840081cb"
    assert routes.ISSUE459_T03_AUTHORITY_COMMENT == "5463568867"
    assert routes.ISSUE459_T03_AUTHORITY_SHA256 == "728705c278db4b05d4072bcacc3af657b069662e21fbf4f5f5ee2f934a155da8"
    assert routes.ISSUE459_T03_CORRECTION_COMMENT == "5463979365"
    assert routes.ISSUE459_T03_CORRECTION_SHA256 == "c8816f6243e5810267b66c84fcaa6bd471d78fca24463f6b9e46352a93c42113"
    assert routes.ISSUE459_T03_DEPENDENCY_COMMENT == "5464081073"
    assert routes.ISSUE459_T03_DEPENDENCY_SHA256 == "1e07f4d261216e3d3b218160e1b46bf84f3f395fbe816db926f004314182f369"
    assert routes.ISSUE459_T03_MYRA_CORRECTION_COMMENT == "5464690216"
    assert routes.ISSUE459_T03_MYRA_CORRECTION_SHA256 == (
        "4b69e4707492c6e6c7d8b8527680d8ef0987043745220e19e0c2036faaf62bfa"
    )
    assert routes.ROUTES[branch] == ISSUE459_T03_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 459
    assert routes.TOTAL_LIMITS[branch] == 2400
    assert routes.TEXT_LIMITS[branch] == ISSUE459_T03_LINE_CAPS
    assert routes.ISSUE459_T03_BYTE_LIMITS == ISSUE459_T03_BYTE_CAPS


def test_issue459_t05a_route_freezes_authority_scope_and_budgets() -> None:
    branch = routes.ISSUE459_T05A_BRANCH
    assert branch == "stage8-459-t05a-grounded-narration-handoff"
    assert routes.ISSUE459_T05A_BASE == "0d70fa8e27ad4760249d75e7782ac06b5d68b173"
    assert routes.ISSUE459_T05A_AUTHORITY_COMMENT == "5465050919"
    assert routes.ISSUE459_T05A_AUTHORITY_SHA256 == (
        "ab0d0b486bf77eac59db2b83c0d33bd0ae61bb52ed26b37b4d7a8402b2ec31c8"
    )
    assert routes.ROUTES[branch] == ISSUE459_T05A_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 459
    assert routes.TOTAL_LIMITS[branch] == 2200
    assert routes.TEXT_LIMITS[branch] == ISSUE459_T05A_LINE_CAPS


def test_issue459_t05a_requires_exact_main_branch_point() -> None:
    base = routes.ISSUE459_T05A_BASE

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            return completed(args, out=base + "\n")
        assert args[:2] == ["git", "merge-base"]
        return completed(args, out=base + "\n")

    assert routes.route_base(good, routes.ISSUE459_T05A_BRANCH) == base
    for command in ("rev-parse", "fixed-merge-base", "branch-point"):
        def broken(args: list[str], *, rejected: str = command) -> subprocess.CompletedProcess[str]:
            if rejected == "rev-parse" and args[:2] == ["git", "rev-parse"]:
                return completed(args, code=128)
            if rejected == "fixed-merge-base" and args[:3] == ["git", "merge-base", base]:
                return completed(args, out="0" * 40 + "\n")
            if rejected == "branch-point" and args[:3] == ["git", "merge-base", "origin/main"]:
                return completed(args, out="0" * 40 + "\n")
            return good(args)
        error = pytest.raises(RuntimeError, routes.route_base, broken, routes.ISSUE459_T05A_BRANCH)
        assert "Issue #459 fixed base" in str(error.value)


def test_issue459_t05a_rejects_authority_drift_and_rename(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    branch = routes.ISSUE459_T05A_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE459_T05A_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-459-t05a.json").read_text()
    )
    target = tmp_path / "docs/governance/preflights/issue-459-t05a.json"
    target.parent.mkdir(parents=True)
    drifted = copy.deepcopy(artifact)
    drifted["objective"] = drifted["objective"].replace(
        routes.ISSUE459_T05A_AUTHORITY_SHA256, "0" * 64
    )
    target.write_text(json.dumps(drifted))
    failures: list[str] = []
    routes.check_exact_route(
        tmp_path, lambda _: completed([]), branch, ISSUE459_T05A_EXPECTED, failures
    )
    assert failures == ["Issue #459 T05A governance authority drifted."]

    renamed = completed([], out="R100\0old\0new\0")
    failures = []
    routes.check_exact_route(
        REPO, lambda _: renamed, branch, ISSUE459_T05A_EXPECTED, failures
    )
    assert failures == ["Issue #459 route forbids deleted, renamed, or copied paths."]


def test_issue466_route_freezes_source_authority_scope_and_budgets() -> None:
    branch = routes.ISSUE466_BRANCH
    assert branch == "cut1-466-t05a-presenter-source-integrity"
    assert routes.ISSUE466_BASE == "7eb4b99d7bc2bcf11cfc8c959baacb6cf3a21e81"
    assert routes.ISSUE466_AUTHORITY_REVISION == "issue:466@2026-08-30T09:44:54Z"
    assert routes.ISSUE466_AUTHORITY_SHA256 == (
        "3e4c9c483bdea609be70c46863a36f64a1900cac058615a22e213ea218c9212c"
    )
    assert routes.ISSUE466_SPAN_SHA256 == (
        "6ed0e9270ca03d6940ecc11e3e174d8024a54aba306f18d5b8eedb1ed9241396"
    )
    assert routes.ISSUE466_FREEZE_COMMENT == "5467958861"
    assert routes.ISSUE466_FREEZE_SHA256 == (
        "12699c91eaa0cb23dbd20622ef5aaf87238d9fca0cadba0d98d60cc349867fbf"
    )
    assert routes.ISSUE466_CORRECTION_COMMENT == "5468026907"
    assert routes.ISSUE466_CORRECTION_SHA256 == (
        "91682bed3814d7d89c70c635b690e5b6f47111d51fd5e800e82399e03fbc6398"
    )
    assert routes.ISSUE466_SKILL_LEDGER_COMMENT == "5468042606"
    assert routes.ISSUE466_SKILL_LEDGER_SHA256 == (
        "5a976b8a72f7df10f8bbfee746a7eb098293aae19e32e6abcab1c7e9a22ce0c1"
    )
    assert routes.ROUTES[branch] == ISSUE466_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 466
    assert routes.TOTAL_LIMITS[branch] == 2000
    assert routes.TEXT_LIMITS[branch] == ISSUE466_LINE_CAPS


def test_issue466_retains_original_source_authority_base() -> None:
    assert routes.ISSUE466_BASE == "7eb4b99d7bc2bcf11cfc8c959baacb6cf3a21e81"

    def broken(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out="0" * 40 + "\n")

    error = pytest.raises(RuntimeError, routes.route_base, broken, routes.ISSUE466_BRANCH)
    assert "Issue #466 reviewed transition" in str(error.value)


def test_issue466_requires_exact_reviewed_main_transition() -> None:
    original = "7eb4b99d7bc2bcf11cfc8c959baacb6cf3a21e81"
    frozen = "24c778b4b7ac99b8bdcd34b094f51d5513723958"
    transition_base = "3b186af6f5787a47bbfa5f7aebaa2dc9661866ca"
    transition_merge = "23a12d6845f9e441d37f322da3cd73251b6de191"
    assert routes.ISSUE466_BASE == original
    assert routes.ISSUE466_FROZEN_HEAD == frozen
    assert routes.ISSUE466_TRANSITION_BASE == transition_base
    assert routes.ISSUE466_TRANSITION_MERGE == transition_merge

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            if args[2] == "origin/main^{commit}":
                return completed(args, out=transition_base + "\n")
            return completed(args, out=args[2].removesuffix("^{commit}") + "\n")
        if args[:3] == ["git", "merge-base", "--is-ancestor"]:
            return completed(args)
        if args[:4] == ["git", "show", "-s", "--format=%P"]:
            return completed(args, out=f"{frozen} {transition_base}\n")
        raise AssertionError(args)

    assert routes.route_base(good, routes.ISSUE466_BRANCH) == transition_base

    def forged_parent(args: list[str]) -> subprocess.CompletedProcess[str]:
        result = good(args)
        if args[:4] == ["git", "show", "-s", "--format=%P"]:
            return completed(args, out=f"{frozen} {'0' * 40}\n")
        return result

    error = pytest.raises(
        RuntimeError, routes.route_base, forged_parent, routes.ISSUE466_BRANCH
    )
    assert "Issue #466 reviewed transition" in str(error.value)


def test_issue459_t05b_route_freezes_authority_scope_and_budgets() -> None:
    branch = routes.ISSUE459_T05B_BRANCH
    assert branch == "stage8-459-t05b-audio-caption-authority"
    assert routes.ISSUE459_T05B_BASE == "bfb8487760dc6aeef8b05af95e0ecd40d0076f3a"
    assert routes.ISSUE459_T05B_AUTHORITY_COMMENT == "5466871459"
    assert routes.ISSUE459_T05B_AUTHORITY_SHA256 == (
        "f53e919836ea5edd58620d789497d945f317c354d0b5405a88d49e570c778b28"
    )
    assert routes.ISSUE459_T05B_CORRECTION_COMMENT == "5466962967"
    assert routes.ISSUE459_T05B_CORRECTION_SHA256 == (
        "4d4cd204972abfa70b687f416813937b41329c930cf1676706ce278798579032"
    )
    assert routes.ISSUE459_T05B_FINGERPRINT_CORRECTION_COMMENT == "5467038670"
    assert routes.ISSUE459_T05B_FINGERPRINT_CORRECTION_SHA256 == (
        "41e41763e52382b3eeeea6f265dd42e2078293a3325e5df6c62f9e01d5bbc340"
    )
    assert routes.ISSUE459_T05B_REVIEW_CORRECTION_COMMENT == "5467125295"
    assert routes.ISSUE459_T05B_REVIEW_CORRECTION_SHA256 == (
        "6f05484d33e69ede373841fbb57755ae3139e5c1e06280252b8bc1558d42b263"
    )
    assert routes.ISSUE459_T05B_HOSTED_PROVENANCE_COMMENT == "5467552503"
    assert routes.ISSUE459_T05B_HOSTED_PROVENANCE_SHA256 == (
        "a00a8a8348303a82d46d3dcddddeeb0307d6af230118879a04fbda7ff4476ccb"
    )
    assert routes.ROUTES[branch] == ISSUE459_T05B_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 459
    assert routes.TOTAL_LIMITS[branch] == 3600
    assert routes.TEXT_LIMITS[branch] == ISSUE459_T05B_LINE_CAPS
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES


def test_issue475_route_freezes_authority_scope_and_budgets() -> None:
    branch = routes.ISSUE475_BRANCH
    assert branch == "cut1-475-t05b-runtime-receipt-binding"
    assert routes.ISSUE475_BASE == "fb963f92057b8ccd5c0c070a3c9b5406ee9e884f"
    assert routes.ISSUE475_RUNTIME_COMMENT == "5470636741"
    assert routes.ISSUE475_RUNTIME_SHA256 == (
        "27b21d3db0ec01f310ac5db57260ea656b3f73bac50a40b78106a99d823159fe"
    )
    assert routes.ISSUE475_RECEIPT_COMMENT == "5470701562"
    assert routes.ISSUE475_RECEIPT_SHA256 == (
        "415139a73d27173eb406654ca66acd0ecf928f40b4eea0d3d71a7572558a49c1"
    )
    assert routes.ISSUE475_FREEZE_COMMENT == "5471056591"
    assert routes.ISSUE475_FREEZE_SHA256 == (
        "239c2dcd903e0e5a056a2af4d9abdb80b8b148430c107549984f0ac2bb627348"
    )
    assert routes.ROUTES[branch] == ISSUE475_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 475
    assert routes.TOTAL_LIMITS[branch] == 1800
    assert routes.TEXT_LIMITS[branch] == ISSUE475_LINE_CAPS
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES


def test_issue475_requires_exact_main_branch_point() -> None:
    base = "fb963f92057b8ccd5c0c070a3c9b5406ee9e884f"

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, routes.ISSUE475_BRANCH) == base
    for command in ("rev-parse", "fixed-merge-base", "branch-point"):
        calls = 0

        def broken(
            args: list[str], *, rejected: str = command
        ) -> subprocess.CompletedProcess[str]:
            nonlocal calls
            calls += 1
            if rejected == "rev-parse" and calls == 1:
                return completed(args, code=128)
            if rejected == "fixed-merge-base" and calls == 2:
                return completed(args, out="0" * 40 + "\n")
            if rejected == "branch-point" and calls == 3:
                return completed(args, out="0" * 40 + "\n")
            return good(args)

        error = pytest.raises(RuntimeError, routes.route_base, broken, routes.ISSUE475_BRANCH)
        assert "Issue #475 fixed base" in str(error.value)


def test_issue475_rejects_authority_drift_and_destructive_paths(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    branch = routes.ISSUE475_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE475_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-475.json").read_text()
    )
    target = tmp_path / "docs/governance/preflights/issue-475.json"
    target.parent.mkdir(parents=True)
    drifted = copy.deepcopy(artifact)
    drifted["objective"] = drifted["objective"].replace(
        routes.ISSUE475_FREEZE_SHA256, "0" * 64
    )
    target.write_text(json.dumps(drifted))
    failures: list[str] = []
    routes.check_exact_route(
        tmp_path, lambda _: completed([]), branch, ISSUE475_EXPECTED, failures
    )
    assert failures == ["Issue #475 T05B binding authority drifted."]

    for status in ("D\0old\0", "R100\0old\0new\0", "C100\0old\0new\0"):
        failures = []
        routes.check_exact_route(
            REPO,
            lambda args, output=status: completed(args, out=output),
            branch,
            ISSUE475_EXPECTED,
            failures,
        )
        assert failures == ["Issue #475 route forbids deleted, renamed, or copied paths."]


def test_issue459_t05b_requires_exact_main_branch_point() -> None:
    base = "bfb8487760dc6aeef8b05af95e0ecd40d0076f3a"

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, routes.ISSUE459_T05B_BRANCH) == base
    for command in ("rev-parse", "fixed-merge-base", "branch-point"):
        calls = 0

        def broken(
            args: list[str], *, rejected: str = command
        ) -> subprocess.CompletedProcess[str]:
            nonlocal calls
            calls += 1
            if rejected == "rev-parse" and calls == 1:
                return completed(args, code=128)
            if rejected == "fixed-merge-base" and calls == 2:
                return completed(args, out="0" * 40 + "\n")
            if rejected == "branch-point" and calls == 3:
                return completed(args, out="0" * 40 + "\n")
            return good(args)

        error = pytest.raises(
            RuntimeError, routes.route_base, broken, routes.ISSUE459_T05B_BRANCH
        )
        assert "Issue #459 fixed base" in str(error.value)


def test_issue459_t05b_rejects_authority_drift_and_destructive_paths(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    branch = routes.ISSUE459_T05B_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE459_T05B_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-459-t05b.json").read_text()
    )
    target = tmp_path / "docs/governance/preflights/issue-459-t05b.json"
    target.parent.mkdir(parents=True)
    drifted = copy.deepcopy(artifact)
    drifted["objective"] = drifted["objective"].replace(
        routes.ISSUE459_T05B_AUTHORITY_SHA256, "0" * 64
    )
    target.write_text(json.dumps(drifted))
    failures: list[str] = []
    routes.check_exact_route(
        tmp_path, lambda _: completed([]), branch, ISSUE459_T05B_EXPECTED, failures
    )
    assert failures == ["Issue #459 T05B governance authority drifted."]

    for status in ("D\0old\0", "R100\0old\0new\0", "C100\0old\0new\0"):
        failures = []
        routes.check_exact_route(
            REPO,
            lambda args, output=status: completed(args, out=output),
            branch,
            ISSUE459_T05B_EXPECTED,
            failures,
        )
        assert failures == ["Issue #459 route forbids deleted, renamed, or copied paths."]


def test_issue459_t05b_does_not_broaden_old_routes() -> None:
    for branch in (
        routes.ISSUE459_BRANCH,
        routes.ISSUE459_T03_BRANCH,
        routes.ISSUE459_T05A_BRANCH,
    ):
        assert "backend/app/cut1_audio.py" not in routes.ROUTES[branch]
        assert "docs/governance/preflights/issue-459-t05b.json" not in routes.ROUTES[branch]


def test_issue459_t03_requires_exact_main_branch_point() -> None:
    base = routes.ISSUE459_T03_BASE

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            return completed(args, out=base + "\n")
        assert args[:2] == ["git", "merge-base"]
        return completed(args, out=base + "\n")

    assert routes.route_base(good, routes.ISSUE459_T03_BRANCH) == base
    for command in ("rev-parse", "fixed-merge-base", "branch-point"):
        def broken(args: list[str], *, rejected: str = command) -> subprocess.CompletedProcess[str]:
            if rejected == "rev-parse" and args[:2] == ["git", "rev-parse"]:
                return completed(args, code=128)
            if rejected == "fixed-merge-base" and args[:3] == ["git", "merge-base", base]:
                return completed(args, out="0" * 40 + "\n")
            if rejected == "branch-point" and args[:3] == ["git", "merge-base", "origin/main"]:
                return completed(args, out="0" * 40 + "\n")
            return good(args)
        error = pytest.raises(RuntimeError, routes.route_base, broken, routes.ISSUE459_T03_BRANCH)
        assert "Issue #459 fixed base" in str(error.value)


def test_issue459_t03_rejects_authority_rename_and_binary_boundary(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    branch = routes.ISSUE459_T03_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE459_T03_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    artifact = json.loads((REPO / "docs/governance/preflights/issue-459-t03.json").read_text())
    target = tmp_path / "docs/governance/preflights/issue-459-t03.json"
    target.parent.mkdir(parents=True)
    monkeypatch.setattr(routes, "route_binary_sizes",
                        lambda *_: {path: 1 for path in ISSUE459_T03_BYTE_CAPS})
    for authority_sha256 in (
        routes.ISSUE459_T03_AUTHORITY_SHA256,
        routes.ISSUE459_T03_CORRECTION_SHA256,
        routes.ISSUE459_T03_DEPENDENCY_SHA256,
        routes.ISSUE459_T03_MYRA_CORRECTION_SHA256,
    ):
        drifted = copy.deepcopy(artifact)
        drifted["objective"] = drifted["objective"].replace(authority_sha256, "0" * 64)
        target.write_text(json.dumps(drifted))
        failures: list[str] = []
        routes.check_exact_route(tmp_path, lambda _: completed([]), branch,
                                 ISSUE459_T03_EXPECTED, failures)
        assert failures == ["Issue #459 T03 governance authority drifted."]

    for path, limit in ISSUE459_T03_BYTE_CAPS.items():
        monkeypatch.setattr(routes, "route_binary_sizes", lambda *_, p=path, n=limit: {
            candidate: n if candidate == p else 1 for candidate in ISSUE459_T03_BYTE_CAPS
        })
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch,
                                 ISSUE459_T03_EXPECTED, failures)
        assert failures == [f"Issue #459 file {path} must be smaller than {limit} bytes."]

    monkeypatch.setattr(routes, "route_binary_sizes",
                        lambda *_: {path: 1 for path in ISSUE459_T03_BYTE_CAPS})
    renamed = completed([], out="R100\0old\0new\0")
    failures = []
    routes.check_exact_route(REPO, lambda _: renamed, branch,
                             ISSUE459_T03_EXPECTED, failures)
    assert failures == ["Issue #459 route forbids deleted, renamed, or copied paths."]


def test_issue459_rejects_each_byte_boundary(monkeypatch: Any) -> None:
    branch = routes.ISSUE459_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    for path, limit in routes.ISSUE459_BYTE_LIMITS.items():
        sizes = {candidate: maximum - 1 for candidate, maximum in routes.ISSUE459_BYTE_LIMITS.items()}
        monkeypatch.setattr(routes, "route_binary_sizes",
                            lambda *_, values=sizes | {path: limit}: values)
        failures: list[str] = []
        routes.check_exact_route(REPO, issue459_run, branch,
                                 ISSUE459_EXPECTED, failures)
        assert failures == [f"Issue #459 file {path} must be smaller than {limit} bytes."]


def test_issue459_rejects_extra_and_each_text_budget(monkeypatch: Any) -> None:
    branch = routes.ISSUE459_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_binary_sizes",
                        lambda *_: {path: 1 for path in ISSUE459_BYTE_CAPS})
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    for path, limit in ISSUE459_LINE_CAPS.items():
        monkeypatch.setattr(routes, "route_text_charges",
                            lambda *_, p=path, n=limit: (n + 1, {p: n + 1}))
        failures: list[str] = []
        routes.check_exact_route(REPO, issue459_run, branch,
                                 ISSUE459_EXPECTED, failures)
        assert failures == [f"Issue #459 charge for {path} exceeds {limit}."]
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope",
                        lambda: [*ISSUE459_EXPECTED, "rogue.txt"])
    failures = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: rogue.txt"]


def test_issue459_route_unions_current_correction_on_incremental_hosted_push(
    monkeypatch: Any,
) -> None:
    """A push's `before` SHA cannot hide paths added after the frozen base."""
    branch = routes.ISSUE459_BRANCH
    hidden = {
        "docs/governance/cut1-controlled-presenter-red-corpus-v1.json",
        "docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json",
    }
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE459_TRANSITION_BASE)
    monkeypatch.setattr(routes, "issue459_source_failures", lambda *_: [])
    monkeypatch.setattr(routes, "issue459_base_source_failures", lambda *_: [])
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(
        routes,
        "route_binary_sizes",
        lambda *_: {path: 1 for path in routes.ISSUE459_BYTE_LIMITS},
    )

    snapshots = iter((ISSUE459_FROZEN_EXPECTED, ISSUE459_FROZEN_EXPECTED))

    def hosted(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:4] == ["git", "diff", "--name-only", "-z"]:
            paths = next(snapshots)
            return completed(args, out="".join(f"{path}\0" for path in sorted(paths)))
        return completed(args)

    failures: list[str] = []
    routes.check_exact_route(
        REPO, hosted, branch, ISSUE459_EXPECTED - hidden, failures
    )
    assert failures == []


def test_issue459_rejects_unauthorized_path_in_either_transition_snapshot(
    monkeypatch: Any,
) -> None:
    branch = routes.ISSUE459_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE459_TRANSITION_BASE)
    monkeypatch.setattr(routes, "issue459_source_failures", lambda *_: [])
    monkeypatch.setattr(routes, "issue459_base_source_failures", lambda *_: [])
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(
        routes,
        "route_binary_sizes",
        lambda *_: {path: 1 for path in routes.ISSUE459_BYTE_LIMITS},
    )
    missing = "backend/app/cut1_controlled_presenter.py"
    for frozen_paths, active_paths, expected in (
        ({*ISSUE459_FROZEN_EXPECTED, "frozen-rogue.txt"}, ISSUE459_EXPECTED,
         "Issue #459 route contains unauthorized path: frozen-rogue.txt"),
        (ISSUE459_FROZEN_EXPECTED, {*ISSUE459_EXPECTED, "active-rogue.txt"},
         "Issue #459 route contains unauthorized path: active-rogue.txt"),
        (ISSUE459_FROZEN_EXPECTED - {missing}, ISSUE459_EXPECTED,
         f"Issue #459 route snapshot is missing required path: {missing}"),
        (ISSUE459_FROZEN_EXPECTED, ISSUE459_EXPECTED - {missing},
         f"Issue #459 route snapshot is missing required path: {missing}"),
    ):
        snapshots = iter((frozen_paths, active_paths))

        def run(args: list[str]) -> subprocess.CompletedProcess[str]:
            if args[:4] == ["git", "diff", "--name-only", "-z"]:
                paths = next(snapshots)
                return completed(args, out="".join(f"{path}\0" for path in sorted(paths)))
            return completed(args)

        failures: list[str] = []
        routes.check_exact_route(REPO, run, branch, ISSUE459_EXPECTED, failures)
        assert failures == [expected]


def test_issue459_required_text_files_fail_closed(tmp_path: Path) -> None:
    path = "required.txt"
    with pytest.raises(RuntimeError, match="Route binary is missing"):
        routes.route_binary_sizes(tmp_path, {path}, "utf-8")
    target = tmp_path / path
    target.write_bytes(b"\xff")
    with pytest.raises(RuntimeError, match="not valid utf-8"):
        routes.route_binary_sizes(tmp_path, {path}, "utf-8")
    target.unlink()
    target.symlink_to(tmp_path)
    with pytest.raises(RuntimeError, match="regular non-symlink"):
        routes.route_binary_sizes(tmp_path, {path}, "utf-8")


def test_issue459_source_snapshot_fails_closed_when_frozen_commit_is_unavailable(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(routes, "ISSUE459_SOURCE_SHA256", {"docs/PRD.md": "0" * 64})
    monkeypatch.setattr(
        routes.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 128, b"", b"missing"),
    )
    assert routes.issue459_source_failures(REPO) == [
        "Issue #459 frozen source identity drifted: docs/PRD.md"
    ]


def test_issue459_rejects_source_authority_and_rename_copy_drift(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "ISSUE459_SOURCE_SHA256", {"docs/PRD.md": "0" * 64})
    assert routes.issue459_source_failures(REPO) == [
        "Issue #459 frozen source identity drifted: docs/PRD.md"
    ]
    monkeypatch.setattr(routes, "ISSUE459_SOURCE_SHA256", {})
    monkeypatch.setattr(routes, "ISSUE459_EDITABLE_AUTHORITY_SHA256",
                        {"missing-authority": "0" * 64})
    assert routes.issue459_source_failures(REPO) == [
        "Issue #459 editable authority identity drifted: missing-authority"
    ]
    monkeypatch.undo()
    assert routes.issue459_base_source_failures(REPO) == []
    monkeypatch.setattr(routes, "ISSUE459_BASE_SOURCE_SHA256", {"docs/STATUS.md": "0" * 64})
    assert routes.issue459_base_source_failures(REPO) == [
        "Issue #459 base source identity drifted: docs/STATUS.md"
    ]
    monkeypatch.undo()
    assert routes.route_has_copy_or_rename("R100\0old\0new\0")
    assert routes.route_has_copy_or_rename("C056\0old\0new\0")
    assert routes.route_has_copy_or_rename("D\0deleted\0")
    assert not routes.route_has_copy_or_rename("M\0file\0")
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(routes, "route_binary_sizes",
                        lambda *_: {path: 1 for path in ISSUE459_BYTE_CAPS})
    renamed = completed([], out="R100\0docs/PHASE_PLAN.md\0docs/STATUS.md\0")
    def renamed_run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if "--name-only" in args:
            return issue459_run(args)
        return renamed
    failures: list[str] = []
    routes.check_exact_route(REPO, renamed_run, routes.ISSUE459_BRANCH,
                             ISSUE459_EXPECTED, failures)
    assert failures == ["Issue #459 route forbids deleted, renamed, or copied paths."]


def test_issue452_contract_bytes_schemas_and_authority_hashes() -> None:
    governance = REPO / "docs/governance"
    objective = json.loads((governance / "preflights/issue-452.json").read_text())["objective"]
    assert "5445887301" in objective
    assert "6c667549e12c3db9478f69ea6dfe580ecf9e0b0e0b603550c7e62657df8d66e8" in objective
    protocol_path = governance / "cut1-blinded-human-evaluation-protocol-v1.json"
    bakeoff_path = governance / "cut1-provider-bakeoff-contract-v1.json"
    assert hashlib.sha256(protocol_path.read_bytes()).hexdigest() == "fa3759985141639185618fbc595057412dd8582f60ed97fc462b30b7548580b8"
    assert hashlib.sha256(bakeoff_path.read_bytes()).hexdigest() == "1a3fd981644488203e8c7cc38fc0389092b23b579cce860c3d35a1ca7a1786db"
    protocol = json.loads(protocol_path.read_text())
    assert [row["bodySha256"] for row in protocol["authority"]] == ["03e23b4faaea5389514d55529d284743a034efd0fad126bb704ea22c0d51c450", "4f599502ee3658a97c5dbfee8296193880a732641eea1a26b196e3ce9d79ab1c", "391de2e22898416fa9192d9bd47f8bb3e97d6a73d263e65721ff4e6b99448a33", "63c5fcd41bfb86971abe8c28f44903a12ad5d825dd988b85737c8f0b06644ae7"]
    assert hashlib.sha256(protocol["endpoint"]["prompt"].encode()).hexdigest() == protocol["endpoint"]["promptSha256"]
    matrix = json.loads((governance / "cut1-all-presenter-acceptance-matrix-v1.json").read_text())
    bakeoff = json.loads(bakeoff_path.read_text())
    assert matrix["assetCheckpoint"]["bodySha256"] == "c6383a73611294f43bbd7528015f6e661f42d4c3d5b0000483f25a19daa748ee"
    assert bakeoff["sourceCheckpoint"]["bodySha256"] == "19f1619ce83591f4e70285603487d823b7ebe90b208030dd4370846aff425a77"
    for name in ("cut1-human-realism-evaluation-v1.schema.json", "cut1-presenter-provider-acceptance-v1.schema.json"):
        schema = json.loads((governance / "schemas" / name).read_text())
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["type"] == "object" and schema["additionalProperties"] is False


def test_issue452_rejects_each_missing_path_and_lookalikes(monkeypatch: Any) -> None:
    branch = routes.ISSUE452_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    for missing in ISSUE452_EXPECTED:
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, ISSUE452_EXPECTED - {missing}, failures)
        assert failures == [f"Issue #452 route is missing required path: {missing}"]
    for lookalike in (branch + "-retry", branch + "/child", branch.replace("docs", "docѕ")):
        assert lookalike not in routes.ROUTES
        assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES


def test_issue452_rejects_aggregate_and_each_path_budget(monkeypatch: Any) -> None:
    branch = routes.ISSUE452_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (3601, {}))
    failures: list[str] = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, ISSUE452_EXPECTED, failures)
    assert failures == ["Issue #452 charge 3601 exceeds 3600."]
    for path, limit in routes.TEXT_LIMITS[branch].items():
        monkeypatch.setattr(routes, "route_text_charges", lambda *_, p=path, n=limit: (n + 1, {p: n + 1}))
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, ISSUE452_EXPECTED, failures)
        assert failures == [f"Issue #452 charge for {path} exceeds {limit}."]


def test_issue452_rejects_each_file_at_30kb_boundary(monkeypatch: Any) -> None:
    branch = routes.ISSUE452_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    for path, limit in routes.ISSUE452_BYTE_LIMITS.items():
        sizes = {candidate: maximum - 1 for candidate, maximum in routes.ISSUE452_BYTE_LIMITS.items()}
        monkeypatch.setattr(routes, "route_binary_sizes", lambda *_, values=sizes | {path: limit}: values)
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, ISSUE452_EXPECTED, failures)
        assert failures == [f"Issue #452 file {path} must be smaller than {limit} bytes."]


def test_legacy_checker_caps_are_unchanged_and_executable() -> None:
    checker = REPO / "scripts/quality/check_stage8_docs.py"
    checker_text = checker.read_text(encoding="utf-8")
    assert len(checker_text.splitlines()) <= 500
    assert checker.stat().st_size <= 32_000
    legacy_test_lines = (REPO / "tests/unit/test_stage8_quality_gate.py").read_text(encoding="utf-8").splitlines()
    assert len(legacy_test_lines) <= 250
    assert max(map(len, legacy_test_lines), default=0) <= 120
    for relative in (
        "scripts/quality/stage8_brace_expansion_unblock.py",
        "scripts/quality/stage8_cache_pruning.py",
    ):
        assert '"scripts/quality/check_stage8_docs.py": 500' in (REPO / relative).read_text(encoding="utf-8")


def test_exact_route_completeness_lookalikes_and_budgets(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES | set(routes.ISSUE452_BYTE_LIMITS) | set(routes.ISSUE459_BYTE_LIMITS) | set(routes.ISSUE459_T03_BYTE_LIMITS)})
    for branch, paths in EXPECTED.items():
        failures: list[str] = []
        routes.check_exact_route(REPO, issue459_run if branch == routes.ISSUE459_BRANCH else lambda _: completed([]), branch, set(paths), failures)
        assert failures == []
        if branch == routes.ISSUE459_BRANCH:
            continue
        missing = sorted(paths)[0]
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, paths - {missing}, failures)
        issue = routes.ROUTE_ISSUES[branch]
        assert failures == [f"Issue #{issue} route is missing required path: {missing}"]
        confusable = (
            branch.replace("stage8", "stageв")
            if "stage8" in branch
            else branch.replace("process", "procesѕ")
            if "process" in branch
            else branch.replace("security", "securitу")
            if "security" in branch
            else branch.replace("docs", "docѕ")
            if "docs" in branch
            else branch.replace("governance", "governancе")
            if "governance" in branch
            else branch.replace("lane", "lanе")
            if "lane" in branch
            else branch.replace("cut1", "cutі")
        )
        for lookalike in (branch + "-retry", branch.upper(), confusable):
            failures = []
            routes.check_exact_route(REPO, lambda _: completed([]), lookalike, set(paths), failures)
            assert failures == []
            assert lookalike not in stage8.PROCESS_BRANCH_ALLOWED_FILES


def test_per_route_aggregate_per_file_and_binary_caps(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES | set(routes.ISSUE452_BYTE_LIMITS) | set(routes.ISSUE459_BYTE_LIMITS) | set(routes.ISSUE459_T03_BYTE_LIMITS)})
    for branch, limit in routes.TOTAL_LIMITS.items():
        monkeypatch.setattr(routes, "route_text_charges", lambda *_, value=limit: (value + 1, {}))
        failures: list[str] = []
        routes.check_exact_route(REPO, issue459_run if branch == routes.ISSUE459_BRANCH else lambda _: completed([]), branch, EXPECTED[branch], failures)
        assert failures == [f"Issue #{routes.ROUTE_ISSUES[branch]} charge {limit + 1} exceeds {limit}."]
    branch = routes.ISSUE383_BRANCH
    path = "tests/unit/test_cut1_presenter_assets.py"
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (1, {path: 261}))
    failures = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == [f"Issue #383 charge for {path} exceeds 260."]
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {
        path: 500001 if "myra" in path else 1 for path in routes.ISSUE383_BINARY_FILES
    })
    failures = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == [
        "Issue #383 binary frontend/public/demo/myra-synthetic-presenter.webp exceeds 500000 bytes."
    ]


def test_dynamic_base_requires_current_origin_main_ancestor() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out="a" * 40 + "\n")

    assert routes.route_base(good, routes.ISSUE385_BRANCH) == "a" * 40
    assert calls == [
        ["git", "rev-parse", "origin/main^{commit}"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]
    outputs = iter((completed([], out="a" * 40 + "\n"), completed([], out="b" * 40 + "\n")))
    assert "current main" in str(pytest.raises(RuntimeError, routes.route_base, lambda _: next(outputs),
                                               routes.ISSUE385_BRANCH).value)
    assert "fixed base" in str(pytest.raises(RuntimeError, routes.route_base,
        lambda args: completed(args, 1, err="failed"), routes.ISSUE386_BRANCH).value)


def test_issue368_route_requires_exact_accepted_base() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_BASE + "\n")

    assert routes.route_base(good, routes.ISSUE368_BRANCH) == routes.ISSUE368_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]
    drifted = iter((completed([], out=routes.ISSUE368_BASE + "\n"),
                    completed([], out=routes.ISSUE368_BASE + "\n"),
                    completed([], out="a" * 40 + "\n")))
    error = pytest.raises(RuntimeError, routes.route_base, lambda _: next(drifted), routes.ISSUE368_BRANCH)
    assert "Issue #368 fixed base" in str(error.value)


def test_issue368_implementation_route_requires_exact_merged_prompt_base() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_IMPLEMENTATION_BASE + "\n")

    assert routes.route_base(good, routes.ISSUE368_IMPLEMENTATION_BRANCH) == routes.ISSUE368_IMPLEMENTATION_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_IMPLEMENTATION_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_IMPLEMENTATION_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]


def test_issue368_quota_fix_route_requires_exact_accepted_base() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_QUOTA_FIX_BASE + "\n")

    assert routes.route_base(good, routes.ISSUE368_QUOTA_FIX_BRANCH) == routes.ISSUE368_QUOTA_FIX_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_QUOTA_FIX_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_QUOTA_FIX_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]


def test_issue368_prompt_route_requires_exact_merged_governance_base() -> None:
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_PROMPT_BASE + "\n")

    assert routes.route_base(good, routes.ISSUE368_PROMPT_BRANCH) == routes.ISSUE368_PROMPT_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_PROMPT_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_PROMPT_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]


def test_text_charges_use_additions_deletions_and_larger_complete_snapshot() -> None:
    calls: list[list[str]] = []

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if "ls-files" in args:
            return completed(args)
        return completed(args, out="4\t3\tdocs/file.md\n" if "--cached" in args else "5\t4\tdocs/file.md\n")

    assert routes.route_text_charges(run, "base", {"docs/file.md"}) == (9, {"docs/file.md": 9})
    assert ["git", "diff", "--cached", "--numstat", "--no-renames", "base", "--", "docs/file.md"] in calls
    assert ["git", "diff", "--numstat", "--no-renames", "base", "--", "docs/file.md"] in calls


@pytest.mark.parametrize(
    ("untracked", "diff", "message"),
    [
        (completed([], out="docs/file.md\0"), completed([]), "untracked"),
        (completed([], code=1, err="failed"), completed([]), "failed"),
        (completed([]), completed([], out="-\t1\tdocs/file.md\n"), "malformed or binary"),
        (completed([]), completed([], out="1\t1\tdocs/other.md\n"), "unexpected path"),
    ],
)
def test_text_charges_fail_closed(
    untracked: subprocess.CompletedProcess[str], diff: subprocess.CompletedProcess[str], message: str
) -> None:
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return untracked if "ls-files" in args else diff

    assert message in str(pytest.raises(RuntimeError, routes.route_text_charges,
                                        run, "base", {"docs/file.md"}).value)


def test_issue466_docs_do_not_expose_issue_references_as_atx_headings() -> None:
    for relative in (
        "docs/ADR/0072-cut1-presenter-source-integrity.md",
        "docs/STATUS.md",
    ):
        bare_issue_lines = [
            line for line in (REPO / relative).read_text(encoding="utf-8").splitlines()
            if line.startswith("#") and line[1:2].isdigit()
        ]
        assert bare_issue_lines == [], f"{relative}: {bare_issue_lines}"


def test_issue366_charge_uses_the_complete_fixed_base_snapshot() -> None:
    calls: list[list[str]] = []

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if "merge-base" in args:
            return completed(args, out="base\n")
        return completed(args, out="1\t1\tforeign/path.txt\n")

    assert routes.cut1_transition_charges(run, "base", {"docs/bound.md"}) == (
        2, {"foreign/path.txt": 2}
    )
    assert ["git", "diff", "--cached", "--numstat", "base", "--"] in calls
    assert ["git", "diff", "--numstat", "base", "--"] in calls


def test_binary_sizes_reject_missing_non_regular_empty_and_expose_oversize(tmp_path: Path) -> None:
    path = "frontend/public/demo/myra-synthetic-presenter.webp"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    assert "missing" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
    target.mkdir()
    assert "regular" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
    target.rmdir()
    target.write_bytes(b"")
    assert "empty" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
    target.write_bytes(b"x" * 500001)
    assert routes.route_binary_sizes(tmp_path, {path}) == {path: 500001}
    target.unlink()
    source = tmp_path / "source"
    source.write_bytes(b"x")
    target.symlink_to(source)
    assert "regular" in str(pytest.raises(RuntimeError, routes.route_binary_sizes, tmp_path, {path}).value)
