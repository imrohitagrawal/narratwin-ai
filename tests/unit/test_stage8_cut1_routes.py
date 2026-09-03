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
    "docs/STATUS.md",
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
    "tests/unit/test_stage8_quality_gate.py",
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
    "tests/unit/test_stage8_quality_gate.py": 40,
    "docs/ADR/0071-cut1-audio-caption-authority.md": 120,
    "docs/API_CONTRACT.md": 60,
    "docs/DATA_MODEL.md": 80,
    "docs/SECURITY_AND_PRIVACY.md": 80,
    "docs/QUALITY_GATES.md": 100,
    "docs/STATUS.md": 100,
    "docs/TRACEABILITY.md": 100,
}
ISSUE478_EXPECTED = {
    "docs/STATUS.md",
    "docs/governance/preflights/issue-478.json",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_stage8_quality_gate.py",
}
ISSUE478_LINE_CAPS = {
    "docs/STATUS.md": 100,
    "docs/governance/preflights/issue-478.json": 220,
    "scripts/quality/stage8_cut1_routes.py": 180,
    "tests/unit/test_stage8_cut1_routes.py": 240,
    "tests/unit/test_stage8_quality_gate.py": 60,
}
ISSUE479_EXPECTED = {
    "docs/governance/preflights/issue-479.json",
    "backend/app/cut1_listening.py",
    "tests/unit/test_cut1_listening.py",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_stage8_quality_gate.py",
    "docs/ADR/0073-cut1-exact-hash-listening-authority.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_MODEL.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE479_LINE_CAPS = {
    "docs/governance/preflights/issue-479.json": 220,
    "backend/app/cut1_listening.py": 620,
    "tests/unit/test_cut1_listening.py": 530,
    "scripts/quality/stage8_cut1_routes.py": 160,
    "tests/unit/test_stage8_cut1_routes.py": 260,
    "tests/unit/test_stage8_quality_gate.py": 60,
    "docs/ADR/0073-cut1-exact-hash-listening-authority.md": 140,
    "docs/API_CONTRACT.md": 80,
    "docs/DATA_MODEL.md": 80,
    "docs/SECURITY_AND_PRIVACY.md": 80,
    "docs/OBSERVABILITY_AND_COST.md": 60,
    "docs/QUALITY_GATES.md": 80,
    "docs/STAGE_ISSUE_PLAN.md": 80,
    "docs/STATUS.md": 100,
    "docs/TRACEABILITY.md": 50,
}
ISSUE482_EXPECTED = {
    "docs/governance/preflights/issue-482.json", "uv.lock",
    "tests/unit/test_dependency_security_contract.py",
    "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_stage8_quality_gate.py", "docs/THIRD_PARTY_NOTICES.md",
    "docs/QUALITY_GATES.md", "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE482_LINE_CAPS = {
    "docs/governance/preflights/issue-482.json": 220, "uv.lock": 1800,
    "tests/unit/test_dependency_security_contract.py": 240,
    "scripts/quality/stage8_cut1_routes.py": 140,
    "tests/unit/test_stage8_cut1_routes.py": 220,
    "tests/unit/test_stage8_quality_gate.py": 40,
    "docs/THIRD_PARTY_NOTICES.md": 100, "docs/QUALITY_GATES.md": 80,
    "docs/STAGE_ISSUE_PLAN.md": 80, "docs/STATUS.md": 100,
    "docs/TRACEABILITY.md": 60,
}
ISSUE495_EXPECTED = {
    "frontend/package-lock.json",
    "docs/governance/preflights/issue-495-browserslist-security-refresh.json",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_dependency_security_contract.py",
    "tests/unit/test_frontend_dependency_security_contract.py",
    "docs/ADR/0074-browserslist-4-28-8-security-refresh.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE499_EXPECTED = {
    "docs/governance/preflights/issue-499-pypdf-6-16-2-security-refresh.json",
    "pyproject.toml",
    "uv.lock",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "tests/unit/test_dependency_security_contract.py",
    "docs/ADR/0075-pypdf-6-16-2-security-refresh.md",
    "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
}
ISSUE502_EXPECTED = {
    "docs/governance/preflights/issue-502.json",
    "frontend/Dockerfile",
    ".github/workflows/security.yml",
    "scripts/ci/docker-image-scan.sh",
    "scripts/ci/check_container_scan_consensus.py",
    "scripts/quality/stage8_node_security.py",
    "scripts/quality/check_stage8_docs.py",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_frontend_container_runtime.py",
    "tests/unit/test_stage8_node_security.py",
    "tests/unit/test_container_scan_consensus.py",
    "tests/unit/test_stage8_quality_gate.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/ADR/0077-frontend-musl-scratch-runtime.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
}
ISSUE502_LINE_CAPS = {
    "docs/governance/preflights/issue-502.json": 320,
    "frontend/Dockerfile": 360,
    ".github/workflows/security.yml": 80,
    "scripts/ci/docker-image-scan.sh": 360,
    "scripts/ci/check_container_scan_consensus.py": 320,
    "scripts/quality/stage8_node_security.py": 300,
    "scripts/quality/check_stage8_docs.py": 80,
    "scripts/quality/stage8_cut1_routes.py": 240,
    "tests/unit/test_frontend_container_runtime.py": 420,
    "tests/unit/test_stage8_node_security.py": 380,
    "tests/unit/test_container_scan_consensus.py": 360,
    "tests/unit/test_stage8_quality_gate.py": 160,
    "tests/unit/test_stage8_cut1_routes.py": 280,
    "docs/ADR/0077-frontend-musl-scratch-runtime.md": 220,
    "docs/SECURITY_AND_PRIVACY.md": 140,
    "docs/THIRD_PARTY_NOTICES.md": 100,
    "docs/QUALITY_GATES.md": 180,
    "docs/STAGE_ISSUE_PLAN.md": 120,
    "docs/STATUS.md": 120,
    "docs/TRACEABILITY.md": 120,
}
ISSUE509_EXPECTED = {
    "docs/governance/preflights/issue-509.json",
    "backend/app/narration.py",
    "backend/app/cut1_audio.py",
    "tests/unit/test_cut1_narration.py",
    "tests/unit/test_cut1_audio.py",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/ADR/0078-cut1-configurable-audio-duration.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/API_CONTRACT.md",
}
ISSUE509_LINE_CAPS = {
    "docs/governance/preflights/issue-509.json": 240,
    "backend/app/narration.py": 180,
    "backend/app/cut1_audio.py": 100,
    "tests/unit/test_cut1_narration.py": 260,
    "tests/unit/test_cut1_audio.py": 300,
    "scripts/quality/stage8_cut1_routes.py": 180,
    "tests/unit/test_stage8_cut1_routes.py": 300,
    "docs/ADR/0078-cut1-configurable-audio-duration.md": 160,
    "docs/QUALITY_GATES.md": 100,
    "docs/STAGE_ISSUE_PLAN.md": 100,
    "docs/STATUS.md": 100,
    "docs/TRACEABILITY.md": 60,
    "docs/SECURITY_AND_PRIVACY.md": 80,
    "docs/OBSERVABILITY_AND_COST.md": 60,
    "docs/API_CONTRACT.md": 80,
}
ISSUE512_EXPECTED = {
    "docs/governance/preflights/issue-512.json",
    "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md",
    "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/TRACEABILITY.md",
    "docs/STATUS.md",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
}
ISSUE512_LINE_CAPS = {
    "docs/governance/preflights/issue-512.json": 180,
    "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md": 650,
    "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md": 40,
    "docs/THIRD_PARTY_NOTICES.md": 40,
    "docs/TRACEABILITY.md": 30,
    "docs/STATUS.md": 30,
    "scripts/quality/stage8_cut1_routes.py": 120,
    "tests/unit/test_stage8_cut1_routes.py": 180,
}
ISSUE507_EXPECTED = {
    "backend/app/google_tts_runtime.py",
    "tests/unit/test_google_tts_runtime.py",
    "docs/governance/preflights/issue-507.json",
    "scripts/quality/stage8_cut1_routes.py",
    "tests/unit/test_stage8_cut1_routes.py",
    "docs/STATUS.md",
    "docs/ADR/0056-cut1-google-gemini-tts.md",
    "docs/TRACEABILITY.md",
}
ISSUE507_LINE_CAPS = {
    "backend/app/google_tts_runtime.py": 20,
    "tests/unit/test_google_tts_runtime.py": 100,
    "docs/governance/preflights/issue-507.json": 60,
    "scripts/quality/stage8_cut1_routes.py": 120,
    "tests/unit/test_stage8_cut1_routes.py": 140,
    "docs/STATUS.md": 50,
    "docs/ADR/0056-cut1-google-gemini-tts.md": 60,
    "docs/TRACEABILITY.md": 60,
}
ISSUE498_EXPECTED = {
    "backend/app/google_tts_runtime.py", "backend/app/tts_provider.py",
    "tests/unit/test_google_tts_runtime.py", "tests/unit/test_stage6_tts_provider.py",
    "tests/unit/test_dependency_security_contract.py", "pyproject.toml", "uv.lock",
    "docs/governance/preflights/issue-498-google-tts-official-grpc.json",
    "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
    "docs/ADR/0056-cut1-google-gemini-tts.md", "docs/STATUS.md",
    "docs/THIRD_PARTY_NOTICES.md", "docs/TRACEABILITY.md",
}
ISSUE498_LINE_CAPS = {
    "backend/app/google_tts_runtime.py": 650, "backend/app/tts_provider.py": 350,
    "tests/unit/test_google_tts_runtime.py": 850,
    "tests/unit/test_stage6_tts_provider.py": 450,
    "tests/unit/test_dependency_security_contract.py": 500, "pyproject.toml": 10,
    "uv.lock": 1000,
    "docs/governance/preflights/issue-498-google-tts-official-grpc.json": 340,
    "scripts/quality/stage8_cut1_routes.py": 240,
    "tests/unit/test_stage8_cut1_routes.py": 320,
    "docs/ADR/0056-cut1-google-gemini-tts.md": 180, "docs/STATUS.md": 140,
    "docs/THIRD_PARTY_NOTICES.md": 180, "docs/TRACEABILITY.md": 140,
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
    "stage8-512-video-provider-landscape": ISSUE512_EXPECTED,
    "stage8-509-configurable-audio-duration": ISSUE509_EXPECTED,
    "stage8-507-google-api-core-grpc-status": ISSUE507_EXPECTED,
    "stage8-502-frontend-musl-runtime-security": ISSUE502_EXPECTED,
    "cut1-process-479-t05c-listening-authority": ISSUE479_EXPECTED,
    "cut1-process-482-dependency-security-refresh": ISSUE482_EXPECTED,
    "stage8-495-browserslist-security-refresh": ISSUE495_EXPECTED,
    "stage8-498-google-tts-official-grpc": ISSUE498_EXPECTED,
    "cut1-process-478-pr477-status-closeout": ISSUE478_EXPECTED,
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
    "stage8-486-reviewer-impact-summary": {
        "docs/governance/preflights/issue-486-reviewer-impact-summary.json",
        ".github/pull_request_template.md",
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/REPOSITORY_GUARDRAILS.md",
        "docs/QUALITY_GATES.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/STATUS.md",
    },
    "stage8-486-reviewer-impact-protected-sources": {
        "AGENTS.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "docs/agent-context/context-policy-manifest-v1.json",
        "docs/governance/preflights/issue-486-protected-reviewer-impact.json",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    "stage8-486-reviewer-impact-hash-cleanup": {
        "scripts/guardrails_check.py",
        "tests/unit/test_guardrails_check.py",
        "docs/governance/preflights/issue-486-protected-hash-cleanup.json",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
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
    "stage8-issue-368-google-presenter-binding-compat": {
        "backend/app/tts_provider.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-368-provider-binding-compat.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-368-google-auth-public-transport-fix": {
        "backend/app/google_tts_runtime.py",
        "tests/unit/test_google_tts_runtime.py",
        "docs/governance/preflights/issue-368-auth-transport.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-368-google-tts-long-response-timeout": {
        "backend/app/google_tts_runtime.py",
        "backend/app/tts_provider.py",
        "tests/unit/test_google_tts_runtime.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-368-google-tts-timeout.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
    },
    "stage8-494-google-tts-failure-diagnostics": {
        "backend/app/tts_provider.py",
        "tests/unit/test_stage6_tts_provider.py",
        "docs/governance/preflights/issue-494-google-tts-failure-diagnostics.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/STATUS.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/TRACEABILITY.md",
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
EXPECTED["stage8-499-pypdf-6-16-2-security-refresh"] = ISSUE499_EXPECTED


def completed(args: list[str], code: int = 0, out: str = "", err: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args, code, out, err)


def test_issue502_musl_runtime_route_is_exact_bounded_and_authority_pinned() -> None:
    branch = "stage8-502-frontend-musl-runtime-security"
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-502.json").read_text(encoding="utf-8")
    )
    assert routes.ISSUE502_BRANCH == branch
    assert routes.ISSUE502_BASE == "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"
    assert routes.ISSUE502_TREE == "76495e566a78a7951c33314ac742606c85ee92e5"
    assert routes.ISSUE502_ROUTE_COMMENT == "5507883668"
    assert routes.ISSUE502_ROUTE_SHA256 == (
        "c114a3f11ac2a52f0834ac9f67119605c1f9d1623f6511eb42fd4c1426e6476f"
    )
    assert routes.ROUTES[branch] == ISSUE502_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 502
    assert routes.TOTAL_LIMITS[branch] == 4660
    assert routes.TEXT_LIMITS[branch] == ISSUE502_LINE_CAPS
    assert set(artifact["scope"]["required"]) == ISSUE502_EXPECTED
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    context = {
        "issue_number": 502,
        "branch": branch,
        "changed_files": artifact["scope"]["required"],
    }
    assert routes.validate_governance_preflight(artifact, context=context) == []
    for value in (
        routes.ISSUE502_BASE,
        routes.ISSUE502_TREE,
        routes.ISSUE502_ROUTE_COMMENT,
        routes.ISSUE502_ROUTE_SHA256,
    ):
        assert value in artifact["objective"]


def test_issue507_google_api_core_grpc_status_route_is_exact_and_bounded() -> None:
    branch = "stage8-507-google-api-core-grpc-status"
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-507.json").read_text(encoding="utf-8")
    )
    assert routes.ISSUE507_BRANCH == branch
    assert routes.ISSUE507_BASE == "615298647609d2656d5e597209a8247467c71e78"
    assert routes.ISSUE507_TREE == "1e4834ff96bf1cdc9a6ffb353de5e97ad68dc0fc"
    assert routes.ROUTES[branch] == ISSUE507_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 507
    assert routes.TOTAL_LIMITS[branch] == 610
    assert routes.TEXT_LIMITS[branch] == ISSUE507_LINE_CAPS
    assert set(artifact["scope"]["required"]) == ISSUE507_EXPECTED
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    context = {"issue_number": 507, "branch": branch, "changed_files": list(ISSUE507_EXPECTED)}
    assert routes.validate_governance_preflight(artifact, context=context) == []
    assert all(
        value in artifact["objective"]
        for value in (
            routes.ISSUE507_BASE,
            routes.ISSUE507_TREE,
            routes.ISSUE507_ROUTE_COMMENT,
            routes.ISSUE507_ROUTE_AMENDMENT_COMMENT,
            routes.ISSUE507_STATUS_AMENDMENT_COMMENT,
            routes.ISSUE507_HOSTED_AMENDMENT_COMMENT,
        )
    )


def test_issue509_configurable_audio_duration_route_is_exact_and_bounded() -> None:
    branch = "stage8-509-configurable-audio-duration"
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-509.json").read_text(encoding="utf-8")
    )
    assert routes.ISSUE509_BRANCH == branch
    assert routes.ISSUE509_BASE == "0f608af347e89c749fcb5bd6ca17a63ceccd56e7"
    assert routes.ISSUE509_TREE == "9418e5b13a1a1acc00371bbf51a4ec78ac50eccc"
    assert routes.ROUTES[branch] == ISSUE509_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 509
    assert routes.TOTAL_LIMITS[branch] == 2400
    assert routes.TEXT_LIMITS[branch] == ISSUE509_LINE_CAPS
    assert set(artifact["scope"]["required"]) == ISSUE509_EXPECTED
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    context = {"issue_number": 509, "branch": branch, "changed_files": list(ISSUE509_EXPECTED)}
    assert routes.validate_governance_preflight(artifact, context=context) == []
    assert all(
        value in artifact["objective"]
        for value in (
            routes.ISSUE509_BASE,
            routes.ISSUE509_TREE,
            routes.ISSUE509_ROUTE_COMMENT,
            routes.ISSUE509_BODY_SHA256,
        )
    )


def test_issue512_video_provider_landscape_route_is_exact_and_bounded() -> None:
    branch = "stage8-512-video-provider-landscape"
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-512.json").read_text(encoding="utf-8")
    )
    assert routes.ISSUE512_BRANCH == branch
    assert routes.ISSUE512_BASE == "60198a86b5558df5dec42c0f90cb3343f67bb286"
    assert routes.ISSUE512_TREE == "f58f42b1b1f069ba23d9b754988e4c023d872706"
    assert routes.ROUTES[branch] == ISSUE512_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 512
    assert routes.TOTAL_LIMITS[branch] == 1270
    assert routes.TEXT_LIMITS[branch] == ISSUE512_LINE_CAPS
    assert set(artifact["scope"]["required"]) == ISSUE512_EXPECTED
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    context = {"issue_number": 512, "branch": branch, "changed_files": list(ISSUE512_EXPECTED)}
    assert routes.validate_governance_preflight(artifact, context=context) == []
    assert all(
        value in artifact["objective"]
        for value in (
            routes.ISSUE512_BASE,
            routes.ISSUE512_TREE,
            routes.ISSUE512_FREEZE_COMMENT,
            routes.ISSUE512_IMMUTABLE_CORRECTION_COMMENT,
            routes.ISSUE512_BRANCH_CORRECTION_COMMENT,
            routes.ISSUE512_ROUTE_AMENDMENT_COMMENT,
        )
    )


def test_issue512_provider_research_preserves_panel_corrections() -> None:
    landscape = (
        REPO / "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md"
    ).read_text(encoding="utf-8")
    demo_plan = (REPO / "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "VEED Fabric 1.0 through fal.ai",
        "Runway Avatar Video API",
        "older indexed copies",
        "44.1 kHz",
        "`BILLABLE_UNKNOWN`",
        "public CDN",
        "API_CHALLENGER_ACTIVATION_BLOCKED",
        "FULL_LENGTH_QUALITY_CHALLENGER_ACTIVATION_BLOCKED",
        "https://runway.com/terms-of-use",
        "https://runway.com/enterprise",
        "https://creatify.ai/privacy",
        "direct Creatify, and Runway Enterprise",
        "https://developers.heygen.com/docs/enterprise-pricing",
    ):
        assert required in landscape
    assert "https://developers.heygen.com/docs/pricing" not in landscape
    heygen_hard_fit = next(
        line
        for line in landscape.splitlines()
        if line.startswith("| HeyGen Avatar IV Photo |")
    )
    assert heygen_hard_fit.startswith(
        "| HeyGen Avatar IV Photo | `CONDITIONAL`: accepted WebP"
    )
    assert "exact accepted WebP compatibility" in landscape
    assert "lossless PNG derivative" in landscape
    for required in (
        "direct VEED Fabric through fal.ai",
        "Runway Avatar Video API",
        "five-minute",
        "immutable 24 kHz",
        "public fal CDN",
        "activation-blocked quality/API challengers",
        "accepted WebP compatibility is unproved",
    ):
        assert required in demo_plan
    assert "https://developers.heygen.com/docs/pricing" not in demo_plan


def test_issue514_video_research_amendment_is_exact_and_bounded() -> None:
    branch = "stage8-514-video-research-amendment"
    expected = {
        "docs/governance/preflights/issue-514.json",
        "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/TRACEABILITY.md",
        "docs/STATUS.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    }
    caps = {
        "docs/governance/preflights/issue-514.json": 180,
        "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md": 400,
        "docs/THIRD_PARTY_NOTICES.md": 30,
        "docs/TRACEABILITY.md": 30,
        "docs/STATUS.md": 30,
        "scripts/quality/stage8_cut1_routes.py": 120,
        "tests/unit/test_stage8_cut1_routes.py": 200,
    }
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-514.json").read_text(encoding="utf-8")
    )

    assert routes.ISSUE514_BRANCH == branch
    assert routes.ISSUE514_BASE == "e15beee4f520ad5786a61effd8ce2eba8f51319c"
    assert routes.ISSUE514_TREE == "bf0775a43bf5af60f2230b3bd9a7cdd3541f3a8c"
    assert routes.ISSUE514_ROUTE_COMMENT == "5527274671"
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 514
    assert routes.TOTAL_LIMITS[branch] == 990
    assert routes.TEXT_LIMITS[branch] == caps
    assert set(artifact["scope"]["required"]) == expected
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    context = {"issue_number": 514, "branch": branch, "changed_files": list(expected)}
    assert routes.validate_governance_preflight(artifact, context=context) == []
    assert all(
        value in artifact["objective"]
        for value in (
            routes.ISSUE514_BASE,
            routes.ISSUE514_TREE,
            routes.ISSUE514_ROUTE_COMMENT,
        )
    )


def test_issue514_research_records_cost_flow_and_precode_plan() -> None:
    landscape = (
        REPO / "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md"
    ).read_text(encoding="utf-8")

    for required in (
        "Exact observed three-provider diagnostic",
        "USD 0.55",
        "USD 2.208",
        "USD 2.10",
        "Uploading audio references is unsupported",
        "visual concept and B-roll benchmark",
        "ProviderCapabilityManifest",
        "VideoCompositor",
        "Sync-3",
        "OmniHuman v1.5",
        "Runway Act-Two",
        "future product-owner Digital Twin",
    ):
        assert required in landscape


def _issue507_route_root(tmp_path: Path) -> Path:
    for relative in ISSUE507_EXPECTED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, target)
    return tmp_path


def _issue507_mode_runner(gitlink: tuple[str, str] | None = None) -> Any:
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "ls-tree"]:
            rows = "".join(
                f"{'160000 commit' if gitlink == ('HEAD', path) else '100644 blob'} "
                f"{'0' * 40}\t{path}\0" for path in sorted(ISSUE507_EXPECTED)
            )
            return completed(args, out=rows)
        if args[:3] == ["git", "ls-files", "--stage"]:
            rows = "".join(
                f"{'160000' if gitlink == ('index', path) else '100644'} "
                f"{'0' * 40} 0\t{path}\0" for path in sorted(ISSUE507_EXPECTED)
            )
            return completed(args, out=rows)
        return completed(args)

    return run


def test_issue507_rejects_non_utf8_owned_path(monkeypatch: Any, tmp_path: Path) -> None:
    root = _issue507_route_root(tmp_path)
    (root / "docs/STATUS.md").write_bytes(b"\xff")
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE507_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    failures: list[str] = []
    routes.check_exact_route(
        root, _issue507_mode_runner(), routes.ISSUE507_BRANCH,
        ISSUE507_EXPECTED, failures,
    )
    assert any("valid utf-8" in failure for failure in failures)


@pytest.mark.parametrize("source", ("HEAD", "index"))
def test_issue507_rejects_gitlink(
    monkeypatch: Any, tmp_path: Path, source: str,
) -> None:
    root = _issue507_route_root(tmp_path)
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE507_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    failures: list[str] = []
    routes.check_exact_route(
        root, _issue507_mode_runner((source, "docs/STATUS.md")),
        routes.ISSUE507_BRANCH, ISSUE507_EXPECTED, failures,
    )
    assert any("ordinary tracked file" in failure for failure in failures)


def test_issue502_requires_exact_current_main_branch_point() -> None:
    base = "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] in (["git", "rev-parse"], ["git", "merge-base"]):
            return completed(args, out=base + "\n")
        return completed(args)

    assert routes.route_base(good, "stage8-502-frontend-musl-runtime-security") == base

    def drifted(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "merge-base", "origin/main", "HEAD"]:
            return completed(args, out="0" * 40 + "\n")
        return good(args)

    with pytest.raises(RuntimeError, match="Issue #502 fixed base evidence"):
        routes.route_base(drifted, "stage8-502-frontend-musl-runtime-security")


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_issue502_route_path_mutations_fail_closed(
    monkeypatch: Any, mutation: str,
) -> None:
    branch = "stage8-502-frontend-musl-runtime-security"
    changed = set(ISSUE502_EXPECTED)
    if mutation == "missing":
        changed.remove("frontend/Dockerfile")
    else:
        changed.add("frontend/package-lock.json")
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE502_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if "--name-only" in args:
            return completed(args, out="\0".join(sorted(changed)) + "\0")
        if "--name-status" in args:
            return completed(
                args,
                out="".join(f"M\0{path}\0" for path in sorted(changed)),
            )
        return completed(args)

    failures: list[str] = []
    routes.check_exact_route(REPO, run, branch, changed, failures)
    if mutation == "missing":
        assert "Issue #502 route is missing required path: frontend/Dockerfile" in failures
    else:
        assert "Issue #502 route changed unexpected path: frontend/package-lock.json" in failures


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


def test_issue486_route_is_frozen_to_exact_base_paths_and_budgets() -> None:
    branch = "stage8-486-reviewer-impact-summary"
    expected = EXPECTED[branch]
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-486-reviewer-impact-summary.json").read_text(encoding="utf-8")
    )
    expected_limits = {
        "docs/governance/preflights/issue-486-reviewer-impact-summary.json": 320,
        ".github/pull_request_template.md": 100,
        "scripts/guardrails_check.py": 360,
        "tests/unit/test_guardrails_check.py": 480,
        "scripts/quality/stage8_cut1_routes.py": 260,
        "tests/unit/test_stage8_cut1_routes.py": 320,
        "docs/REPOSITORY_GUARDRAILS.md": 120,
        "docs/QUALITY_GATES.md": 120,
        "docs/agent-context/context-policy-manifest-v1.json": 40,
        "docs/STATUS.md": 100,
    }

    assert routes.ISSUE486_BRANCH == branch
    assert routes.ISSUE486_BASE == "01857dc1ffa322700179d301925b444a04f166fa"
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 486
    assert routes.TOTAL_LIMITS[branch] == 1400
    assert routes.TEXT_LIMITS[branch] == expected_limits
    assert artifact["branch"] == branch
    assert artifact["accepted_base"] == routes.ISSUE486_BASE
    assert set(artifact["scope"]["required"]) == expected
    objective = artifact["objective"]
    for marker in (
        "exactly seven distinct ordered labels",
        "**Purpose:**",
        "**Behavior before/after:**",
        "**Who and what is affected:**",
        "**Artifacts/capabilities:**",
        "**Operational impact:**",
        "**Scope boundaries:**",
        "**End-to-end impact:**",
        "57ea2bdddd7f0f3df91c75ecb0e434e25aa0779a54d0a2603a7e32a87b5c9ca7",
        "e70d7c3045a4fec6b8c4feeb276244ea963a778f872955670cc2e209c0b03e2d",
    ):
        assert marker in objective


def test_issue486_route_rejects_lookalike_branch_and_forbidden_path(
    monkeypatch: Any,
) -> None:
    branch = "stage8-486-reviewer-impact-summary"
    lookalike = f"{branch}-extra"
    assert lookalike not in routes.ROUTES
    assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES

    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: [*EXPECTED[branch], "backend/app/main.py"],
    )
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/main.py"]


def test_issue486_route_requires_exact_base_and_main_branch_point() -> None:
    branch = routes.ISSUE486_BRANCH
    base = routes.ISSUE486_BASE

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, branch) == base
    for rejected_call in range(3):
        call_count = 0

        def broken(
            args: list[str], *, rejected: int = rejected_call
        ) -> subprocess.CompletedProcess[str]:
            nonlocal call_count
            call_count += 1
            value = "0" * 40 if call_count == rejected + 1 else base
            return completed(args, out=value + "\n")

        error = pytest.raises(RuntimeError, routes.route_base, broken, branch)
        assert "Issue #486 fixed base" in str(error.value)


def test_issue486_route_rejects_aggregate_and_each_per_path_budget(
    monkeypatch: Any,
) -> None:
    branch = routes.ISSUE486_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE486_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (1401, {}))
    failures: list[str] = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
    assert failures == ["Issue #486 charge 1401 exceeds 1400."]

    for path, limit in routes.TEXT_LIMITS[branch].items():
        monkeypatch.setattr(
            routes,
            "route_text_charges",
            lambda *_, path=path, limit=limit: (limit + 1, {path: limit + 1}),
        )
        failures = []
        routes.check_exact_route(
            REPO, lambda _: completed([]), branch, EXPECTED[branch], failures
        )
        assert failures == [f"Issue #486 charge for {path} exceeds {limit}."]


def test_issue486_protected_source_route_is_exact_and_budgeted() -> None:
    branch = "stage8-486-reviewer-impact-protected-sources"
    expected = EXPECTED[branch]
    expected_limits = {
        "AGENTS.md": 40,
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md": 40,
        "docs/agent-context/context-policy-manifest-v1.json": 50,
        "docs/governance/preflights/issue-486-protected-reviewer-impact.json": 260,
        "docs/STATUS.md": 20,
        "scripts/quality/stage8_cut1_routes.py": 80,
        "tests/unit/test_stage8_cut1_routes.py": 160,
    }
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-486-protected-reviewer-impact.json")
        .read_text(encoding="utf-8")
    )

    assert routes.ISSUE486_PROTECTED_BRANCH == branch
    assert routes.ISSUE486_PROTECTED_BASE == "f55f39bea1e009050c9d3f5e2f829cc8557f11d5"
    assert routes.ROUTES[branch] == expected
    assert stage8.EFFECTIVE_STAGE8_ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 486
    assert routes.TOTAL_LIMITS[branch] == 700
    assert routes.TEXT_LIMITS[branch] == expected_limits
    assert set(artifact["scope"]["required"]) == expected
    assert set(artifact["scope"]["allowed_prefixes"]) == expected
    assert artifact["charged_line_budgets"] == {**expected_limits, "aggregate": 700}
    assert artifact["route_authority"] == {
        "freeze": "https://github.com/imrohitagrawal/narratwin-ai/issues/486#issuecomment-5492539437",
        "ordered_amendments": [
            "https://github.com/imrohitagrawal/narratwin-ai/issues/486#issuecomment-5492585578",
            "https://github.com/imrohitagrawal/narratwin-ai/issues/486#issuecomment-5492618746",
        ],
    }


def test_issue486_protected_source_route_rejects_drift(monkeypatch: Any) -> None:
    branch = "stage8-486-reviewer-impact-protected-sources"
    base = "f55f39bea1e009050c9d3f5e2f829cc8557f11d5"

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, branch) == base
    for rejected_call in range(3):
        call_count = 0

        def broken(
            args: list[str], *, rejected: int = rejected_call
        ) -> subprocess.CompletedProcess[str]:
            nonlocal call_count
            call_count += 1
            value = "0" * 40 if call_count == rejected + 1 else base
            return completed(args, out=value + "\n")

        error = pytest.raises(RuntimeError, routes.route_base, broken, branch)
        assert "Issue #486 fixed base" in str(error.value)

    lookalike = branch + "-extra"
    assert lookalike not in routes.ROUTES
    assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES

    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: [*routes.ROUTES[branch], "backend/app/main.py"],
    )
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/main.py"]

    monkeypatch.setattr(routes, "route_base", lambda *_: base)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (701, {}))
    failures = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, routes.ROUTES[branch], failures)
    assert failures == ["Issue #486 charge 701 exceeds 700."]

    for path, limit in routes.TEXT_LIMITS[branch].items():
        monkeypatch.setattr(
            routes,
            "route_text_charges",
            lambda *_, path=path, limit=limit: (limit + 1, {path: limit + 1}),
        )
        failures = []
        routes.check_exact_route(
            REPO, lambda _: completed([]), branch, routes.ROUTES[branch], failures
        )
        assert failures == [f"Issue #486 charge for {path} exceeds {limit}."]


def test_issue486_hash_cleanup_route_is_exact_and_budgeted() -> None:
    branch = "stage8-486-reviewer-impact-hash-cleanup"
    expected = EXPECTED[branch]
    expected_limits = {
        "scripts/guardrails_check.py": 40,
        "tests/unit/test_guardrails_check.py": 120,
        "docs/governance/preflights/issue-486-protected-hash-cleanup.json": 220,
        "docs/STATUS.md": 20,
        "scripts/quality/stage8_cut1_routes.py": 80,
        "tests/unit/test_stage8_cut1_routes.py": 180,
    }

    assert routes.ISSUE486_HASH_CLEANUP_BRANCH == branch
    assert routes.ISSUE486_HASH_CLEANUP_BASE == "a2a9dfd044610b2bd51b37c0d914e09c1b3837b9"
    assert routes.ROUTES[branch] == expected
    assert stage8.EFFECTIVE_STAGE8_ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 486
    assert routes.TOTAL_LIMITS[branch] == 700
    assert routes.TEXT_LIMITS[branch] == expected_limits

    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-486-protected-hash-cleanup.json")
        .read_text(encoding="utf-8")
    )
    assert set(artifact["scope"]["required"]) == expected
    assert set(artifact["scope"]["allowed_prefixes"]) == expected
    assert artifact["charged_line_budgets"] == {**expected_limits, "aggregate": 700}
    assert artifact["route_authority"] == {
        "freeze": "https://github.com/imrohitagrawal/narratwin-ai/issues/486#issuecomment-5493662538"
    }


def test_issue486_hash_cleanup_route_rejects_drift(monkeypatch: Any) -> None:
    branch = "stage8-486-reviewer-impact-hash-cleanup"
    base = "a2a9dfd044610b2bd51b37c0d914e09c1b3837b9"

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, branch) == base
    for rejected_call in range(3):
        call_count = 0

        def broken(
            args: list[str], *, rejected: int = rejected_call
        ) -> subprocess.CompletedProcess[str]:
            nonlocal call_count
            call_count += 1
            value = "0" * 40 if call_count == rejected + 1 else base
            return completed(args, out=value + "\n")

        error = pytest.raises(RuntimeError, routes.route_base, broken, branch)
        assert "Issue #486 fixed base" in str(error.value)

    lookalike = branch + "-extra"
    assert lookalike not in routes.ROUTES
    assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES

    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: [*routes.ROUTES[branch], "backend/app/main.py"],
    )
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: backend/app/main.py"]

    monkeypatch.setattr(routes, "route_base", lambda *_: base)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (701, {}))
    failures = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, routes.ROUTES[branch], failures)
    assert failures == ["Issue #486 charge 701 exceeds 700."]

    for path, limit in {
        "scripts/guardrails_check.py": 40,
        "tests/unit/test_guardrails_check.py": 120,
        "docs/governance/preflights/issue-486-protected-hash-cleanup.json": 220,
        "docs/STATUS.md": 20,
        "scripts/quality/stage8_cut1_routes.py": 80,
        "tests/unit/test_stage8_cut1_routes.py": 180,
    }.items():
        monkeypatch.setattr(
            routes,
            "route_text_charges",
            lambda *_, path=path, limit=limit: (limit + 1, {path: limit + 1}),
        )
        failures = []
        routes.check_exact_route(
            REPO, lambda _: completed([]), branch, routes.ROUTES[branch], failures
        )
        assert failures == [f"Issue #486 charge for {path} exceeds {limit}."]


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
    assert routes.ISSUE475_HOSTED_COMMENT == "5471282345"
    assert routes.ISSUE475_HOSTED_SHA256 == (
        "0cac623417e1645403dca44b4cdc9fe09e4f23efd6c0acdb5b28af1f6dd9ffe1"
    )
    assert routes.ROUTES[branch] == ISSUE475_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 475
    assert routes.TOTAL_LIMITS[branch] == 1800
    assert routes.TEXT_LIMITS[branch] == ISSUE475_LINE_CAPS
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES


def test_issue478_route_freezes_corrected_authority_scope_and_budgets() -> None:
    branch = "cut1-process-478-pr477-status-closeout"
    assert getattr(routes, "ISSUE478_BRANCH", None) == branch
    assert routes.ISSUE478_BASE == "81c1884157502e8a911df63c1d9d0a1704964d63"
    assert routes.ISSUE478_BRANCH_SHA256 == (
        "3c42143d50b21916cc9e063f9a06855b7d57b398310b19dfd64cb9309613e8f2"
    )
    assert routes.ISSUE478_REVIEW_COMMENT == "5474383480"
    assert routes.ISSUE478_REVIEW_SHA256 == (
        "444a43fcd953c961d31d3cdc3387e12a8c2fc3d297c1e6805eba21ba3e893b1f"
    )
    assert routes.ROUTES[branch] == ISSUE478_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 478
    assert routes.TOTAL_LIMITS[branch] == 800
    assert routes.TEXT_LIMITS[branch] == ISSUE478_LINE_CAPS
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES
    preflight = json.loads((REPO / "docs/governance/preflights/issue-478.json").read_text())
    assert preflight["issue_number"] == 478 and preflight["branch"] == branch
    assert set(preflight["scope"]["required"]) == ISSUE478_EXPECTED
    assert set(preflight["scope"]["allowed_prefixes"]) == ISSUE478_EXPECTED
    authority = {
        routes.ISSUE478_BASE,
        routes.ISSUE478_ROUTE_COMMENT,
        routes.ISSUE478_ROUTE_SHA256,
        routes.ISSUE478_BRANCH_COMMENT,
        routes.ISSUE478_BRANCH_SHA256,
        routes.ISSUE478_REVIEW_COMMENT,
        routes.ISSUE478_REVIEW_SHA256,
    }
    assert all(value in preflight["objective"] for value in authority)


def test_issue479_route_freezes_t05c_authority_scope_and_budgets() -> None:
    branch = "cut1-process-479-t05c-listening-authority"
    assert getattr(routes, "ISSUE479_BRANCH", None) == branch
    assert routes.ISSUE479_BASE == "98fa8b41ccea68c840b5462bd5377057f4a3eb14"
    assert routes.ISSUE479_ROUTE_COMMENT == "5481284482"
    assert routes.ISSUE479_ROUTE_SHA256 == (
        "bc878f9886a1decc2fbab102d1d9be7e8e23ab870a9850d486445564813dc2b4"
    )
    assert routes.ISSUE479_CLARIFICATION_COMMENT == "5473637391"
    assert routes.ISSUE479_CLARIFICATION_SHA256 == (
        "9a08ee1c2ce085cec47ca3981ccfa8a9e79c700b75fc8ab1f66b301417e1a05f"
    )
    assert routes.ISSUE479_BUDGET_COMMENT == "5481522433"
    assert routes.ISSUE479_BUDGET_SHA256 == (
        "6e71a7301a9e9f2eb7fb251a4d38b37f0101804f8cdfddd68f36f87d9961223e"
    )
    assert routes.ISSUE479_TRANSITION_COMMENT == "5484097802"
    assert routes.ISSUE479_TRANSITION_SHA256 == (
        "3f1dac2e24bb52caea5db6cf8ea1a224a7f776277af490cee4189595c316bf57"
    )
    assert routes.ROUTES[branch] == ISSUE479_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 479
    assert routes.TOTAL_LIMITS[branch] == 2600
    assert routes.TEXT_LIMITS[branch] == ISSUE479_LINE_CAPS
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES
    preflight = json.loads((REPO / "docs/governance/preflights/issue-479.json").read_text())
    assert preflight["issue_number"] == 479 and preflight["branch"] == branch
    assert set(preflight["scope"]["required"]) == ISSUE479_EXPECTED
    assert set(preflight["scope"]["allowed_prefixes"]) == ISSUE479_EXPECTED
    authority = {
        routes.ISSUE479_BASE,
        routes.ISSUE479_ROUTE_COMMENT,
        routes.ISSUE479_ROUTE_SHA256,
        routes.ISSUE479_CLARIFICATION_COMMENT,
        routes.ISSUE479_CLARIFICATION_SHA256,
        routes.ISSUE479_BUDGET_COMMENT,
        routes.ISSUE479_BUDGET_SHA256,
        routes.ISSUE479_FROZEN_HEAD,
        routes.ISSUE479_TRANSITION_BASE,
        routes.ISSUE479_TRANSITION_MERGE,
        routes.ISSUE479_TRANSITION_COMMENT,
        routes.ISSUE479_TRANSITION_SHA256,
    }
    assert all(value in preflight["objective"] for value in authority)


def test_issue479_requires_exact_reviewed_main_transition() -> None:
    original = "98fa8b41ccea68c840b5462bd5377057f4a3eb14"
    frozen = "773ba43e870a1a18785829c3093d8a74f4416078"
    transition_base = "9b5472a53844495a9d54637167ce48a33a572e11"
    transition_merge = "56f92e969c8de3d39bd452e6917cb8017a6abf98"
    assert routes.ISSUE479_BASE == original
    assert routes.ISSUE479_FROZEN_HEAD == frozen
    assert routes.ISSUE479_TRANSITION_BASE == transition_base
    assert routes.ISSUE479_TRANSITION_MERGE == transition_merge

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            value = transition_base if args[2] == "origin/main^{commit}" else args[2].removesuffix("^{commit}")
            return completed(args, out=value + "\n")
        if args[:3] == ["git", "merge-base", "--is-ancestor"]:
            return completed(args)
        if args[:4] == ["git", "show", "-s", "--format=%P"]:
            return completed(args, out=f"{frozen} {transition_base}\n")
        raise AssertionError(args)

    assert routes.route_base(good, routes.ISSUE479_BRANCH) == transition_base
    for rejected in ("object", "current-main", "ancestry", "parents"):
        def broken(args: list[str], *, rejected: str = rejected) -> subprocess.CompletedProcess[str]:
            if rejected == "object" and args[:2] == ["git", "rev-parse"] and args[2].startswith(frozen):
                return completed(args, code=128)
            if rejected == "current-main" and args[:2] == ["git", "rev-parse"] and args[2].startswith("origin/main"):
                return completed(args, out="0" * 40 + "\n")
            if rejected == "ancestry" and args[:3] == ["git", "merge-base", "--is-ancestor"]:
                return completed(args, code=1)
            if rejected == "parents" and args[:4] == ["git", "show", "-s", "--format=%P"]:
                return completed(args, out=f"{transition_base} {frozen}\n")
            return good(args)

        error = pytest.raises(RuntimeError, routes.route_base, broken, routes.ISSUE479_BRANCH)
        assert "Issue #479 reviewed transition" in str(error.value)


def _issue479_runner(
    args: list[str], name_status: str = "",
) -> subprocess.CompletedProcess[str]:
    output = "\0".join(sorted(ISSUE479_EXPECTED)) + "\0" if "--name-only" in args else name_status
    return completed(args, out=output)


def _issue494_runner(
    args: list[str], name_status: str = "",
) -> subprocess.CompletedProcess[str]:
    output = "\0".join(sorted(EXPECTED[routes.ISSUE494_BRANCH])) + "\0" \
        if "--name-only" in args else name_status
    return completed(args, out=output)


def _issue498_runner(args: list[str]) -> subprocess.CompletedProcess[str]:
    if tuple(args[:2]) in {
        ("git", "log"),
        ("git", "show"),
        ("git", "rev-parse"),
        ("git", "merge-base"),
    }:
        return subprocess.run(args, cwd=REPO, check=False, capture_output=True, text=True)
    return completed(args)


@pytest.mark.parametrize(
    "name_status",
    (
        "D\0backend/app/cut1_listening.py\0",
        "R100\0backend/app/cut1_listening.py\0backend/app/listening.py\0",
        "C100\0backend/app/cut1_listening.py\0backend/app/listening.py\0",
    ),
)
def test_issue479_rejects_destructive_path_transitions(
    monkeypatch: Any, name_status: str,
) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE479_TRANSITION_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    calls: list[list[str]] = []

    def destructive(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return _issue479_runner(args, name_status)

    failures: list[str] = []
    routes.check_exact_route(
        REPO, destructive, routes.ISSUE479_BRANCH, ISSUE479_EXPECTED, failures
    )
    assert len(calls) == 6
    assert failures == ["Issue #479 route forbids deleted, renamed, or copied paths."]


def test_issue479_rejects_missing_extra_and_budget_drift(monkeypatch: Any) -> None:
    branch = routes.ISSUE479_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE479_TRANSITION_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    missing = sorted(ISSUE479_EXPECTED)[0]
    snapshots = 0

    def missing_snapshot(args: list[str]) -> subprocess.CompletedProcess[str]:
        nonlocal snapshots
        if "--name-only" not in args:
            return completed(args)
        snapshots += 1
        paths = ISSUE479_EXPECTED - ({missing} if snapshots == 1 else set())
        return completed(args, out="\0".join(sorted(paths)) + "\0")

    failures: list[str] = []
    routes.check_exact_route(REPO, missing_snapshot, branch, ISSUE479_EXPECTED, failures)
    assert failures == [f"Issue #479 route snapshot is missing required path: {missing}"]
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope",
                        lambda: [*ISSUE479_EXPECTED, "rogue.txt"])
    monkeypatch.setattr(stage8.cut1_routes, "route_base",
                        lambda *_: routes.ISSUE479_TRANSITION_BASE)
    monkeypatch.setattr(stage8.cut1_routes, "route_text_charges", lambda *_: (0, {}))
    failures = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: rogue.txt"]
    for total, charges, expected in (
        (2601, {}, "Issue #479 charge 2601 exceeds 2600."),
        (1, {"backend/app/cut1_listening.py": 621},
         "Issue #479 charge for backend/app/cut1_listening.py exceeds 620."),
        (1, {"tests/unit/test_cut1_listening.py": 531},
         "Issue #479 charge for tests/unit/test_cut1_listening.py exceeds 530."),
    ):
        monkeypatch.setattr(routes, "route_text_charges",
                            lambda *_, values=(total, charges): values)
        failures = []
        routes.check_exact_route(REPO, _issue479_runner, branch, ISSUE479_EXPECTED, failures)
        assert failures == [expected]
    for lookalike in (branch + "-retry", branch + "/child"):
        assert lookalike not in routes.ROUTES
        assert lookalike not in stage8.EFFECTIVE_STAGE8_ROUTES


def test_issue482_route_freezes_dependency_scope_and_budgets() -> None:
    branch = "cut1-process-482-dependency-security-refresh"
    assert routes.ISSUE482_BRANCH == branch
    assert routes.ISSUE482_BASE == "98fa8b41ccea68c840b5462bd5377057f4a3eb14"
    assert routes.ISSUE482_BODY_SHA256 == (
        "736252b09e0b79a57e5ed8643f5b915feff7522693427fe2d48d4dba372c5289"
    )
    assert routes.ISSUE482_ROUTE_COMMENT == "5481998106"
    assert routes.ISSUE482_ROUTE_SHA256 == (
        "a006437d5b773fa2a6a555c0744b40b292d55224c4d60aa739fe9da5ab2af46f"
    )
    assert routes.ISSUE482_CORRECTION_COMMENT == "5482139606"
    assert routes.ISSUE482_CORRECTION_SHA256 == (
        "85ad9dbf5dcc91948f625a15c1b58c9306be2fc014c6e298e7ddb760a538e699"
    )
    assert routes.ROUTES[branch] == ISSUE482_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 482
    assert routes.TOTAL_LIMITS[branch] == 3200
    assert routes.TEXT_LIMITS[branch] == ISSUE482_LINE_CAPS
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES
    preflight = json.loads((REPO / "docs/governance/preflights/issue-482.json").read_text())
    assert set(preflight["scope"]["required"]) == ISSUE482_EXPECTED
    assert set(preflight["scope"]["allowed_prefixes"]) == ISSUE482_EXPECTED
    assert all(value in preflight["objective"] for value in (
        routes.ISSUE482_BASE, routes.ISSUE482_BODY_SHA256,
        routes.ISSUE482_ROUTE_COMMENT, routes.ISSUE482_ROUTE_SHA256,
        routes.ISSUE482_CORRECTION_COMMENT, routes.ISSUE482_CORRECTION_SHA256,
    ))


def _issue482_route_root(tmp_path: Path) -> Path:
    for relative in ISSUE482_EXPECTED:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / relative, target)
    return tmp_path


def _issue482_mode_runner(gitlink: tuple[str, str] | None = None) -> Any:
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "ls-tree"]:
            rows = "".join(
                f"{'160000 commit' if gitlink == ('HEAD', path) else '100644 blob'} "
                f"{'0' * 40}\t{path}\0"
                for path in sorted(ISSUE482_EXPECTED)
            )
            return completed(args, out=rows)
        if args[:3] == ["git", "ls-files", "--stage"]:
            rows = "".join(
                f"{'160000' if gitlink == ('index', path) else '100644'} "
                f"{'0' * 40} 0\t{path}\0"
                for path in sorted(ISSUE482_EXPECTED)
            )
            return completed(args, out=rows)
        return completed(args)

    return run


@pytest.mark.parametrize(
    ("kind", "expected"),
    (("symlink", "regular non-symlink"), ("directory", "regular non-symlink"),
     ("missing", "is missing")),
)
def test_issue482_rejects_missing_or_nonregular_owned_path(
    monkeypatch: Any, tmp_path: Path, kind: str, expected: str,
) -> None:
    root = _issue482_route_root(tmp_path)
    target = root / "docs/STATUS.md"
    target.unlink()
    if kind == "symlink":
        target.symlink_to(REPO / "docs/STATUS.md")
    elif kind == "directory":
        target.mkdir()
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE482_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    failures: list[str] = []
    routes.check_exact_route(
        root, _issue482_mode_runner(), routes.ISSUE482_BRANCH,
        ISSUE482_EXPECTED, failures,
    )
    assert any(expected in failure for failure in failures)


@pytest.mark.parametrize("source", ("HEAD", "index"))
def test_issue482_rejects_gitlink(
    monkeypatch: Any, tmp_path: Path, source: str,
) -> None:
    root = _issue482_route_root(tmp_path)
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE482_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    failures: list[str] = []
    routes.check_exact_route(
        root, _issue482_mode_runner((source, "uv.lock")), routes.ISSUE482_BRANCH,
        ISSUE482_EXPECTED, failures,
    )
    assert any("ordinary tracked file" in failure for failure in failures)


@pytest.mark.parametrize(
    "name_status",
    (
        "D\0docs/STATUS.md\0",
        "R100\0docs/STATUS.md\0docs/STATUS-renamed.md\0",
        "C100\0docs/STATUS.md\0docs/STATUS-copy.md\0",
    ),
)
def test_issue478_rejects_destructive_path_transitions(
    monkeypatch: Any, name_status: str,
) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE478_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    calls: list[list[str]] = []

    def destructive(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=name_status)

    failures: list[str] = []
    routes.check_exact_route(
        REPO,
        destructive,
        routes.ISSUE478_BRANCH,
        ISSUE478_EXPECTED,
        failures,
    )
    assert calls == [
        ["git", "diff", "--name-status", "-z", "--find-copies-harder",
         routes.ISSUE478_BASE, "HEAD", "--"],
        ["git", "diff", "--cached", "--name-status", "-z",
         "--find-copies-harder", routes.ISSUE478_BASE, "--"],
        ["git", "diff", "--name-status", "-z", "--find-copies-harder",
         routes.ISSUE478_BASE, "--"],
    ]
    assert failures == ["Issue #478 route forbids deleted, renamed, or copied paths."]


def test_issue478_rejects_wrong_base_and_preflight_bindings(
    monkeypatch: Any, tmp_path: Path,
) -> None:
    branch = routes.ISSUE478_BRANCH
    base = routes.ISSUE478_BASE

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        return completed(args, out=base + "\n")

    assert routes.route_base(good, branch) == base
    for call in range(3):
        count = 0

        def broken(args: list[str], *, rejected: int = call) -> subprocess.CompletedProcess[str]:
            nonlocal count
            count += 1
            return completed(args, out=("0" * 40 if count == rejected + 1 else base) + "\n")

        assert "Issue #478 fixed base" in str(pytest.raises(RuntimeError, routes.route_base, broken, branch).value)
    artifact = json.loads((REPO / "docs/governance/preflights/issue-478.json").read_text())
    monkeypatch.setattr(routes, "route_base", lambda *_: base)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    target = tmp_path / "docs/governance/preflights/issue-478.json"
    target.parent.mkdir(parents=True)
    cases = (("branch", branch + "-retry", "BRANCH_MISMATCH"),
             ("issue_number", 479, "ISSUE_MISMATCH"))
    for field, value, code in cases:
        drifted = copy.deepcopy(artifact)
        drifted[field] = value
        target.write_text(json.dumps(drifted))
        failures: list[str] = []
        routes.check_exact_route(tmp_path, lambda _: completed([]), branch, ISSUE478_EXPECTED, failures)
        assert any(code in failure for failure in failures)
    drifted = copy.deepcopy(artifact)
    drifted["scope"]["required"][1] = "wrong/path.md"
    target.write_text(json.dumps(drifted))
    failures = []
    routes.check_exact_route(tmp_path, lambda _: completed([]), branch, ISSUE478_EXPECTED, failures)
    assert any("SCOPE." in failure for failure in failures)


def test_issue478_rejects_missing_and_budget_drift(monkeypatch: Any) -> None:
    branch = routes.ISSUE478_BRANCH
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE478_BASE)
    missing = sorted(ISSUE478_EXPECTED)[0]
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    failures: list[str] = []
    routes.check_exact_route(REPO, lambda _: completed([]), branch, ISSUE478_EXPECTED - {missing}, failures)
    assert failures == [f"Issue #478 route is missing required path: {missing}"]
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(stage8, "changed_files_for_stage_scope",
                        lambda: [*ISSUE478_EXPECTED, "rogue.txt"])
    monkeypatch.setattr(stage8.cut1_routes, "route_base", lambda *_: routes.ISSUE478_BASE)
    monkeypatch.setattr(stage8.cut1_routes, "route_text_charges", lambda *_: (0, {}))
    failures = []
    stage8.check_stage_scope(failures)
    assert failures == ["Stage 8 changed file outside the allowlist: rogue.txt"]
    path = "docs/STATUS.md"
    for total, charges, expected in (
        (801, {}, "Issue #478 charge 801 exceeds 800."),
        (1, {path: 101}, f"Issue #478 charge for {path} exceeds 100."),
    ):
        monkeypatch.setattr(routes, "route_text_charges", lambda *_, values=(total, charges): values)
        failures = []
        routes.check_exact_route(
            REPO, lambda _: completed([]), branch, ISSUE478_EXPECTED, failures
        )
        assert failures == [expected]


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
    monkeypatch.setattr(routes, "route_text_integrity", lambda *_: None)
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES | set(routes.ISSUE452_BYTE_LIMITS) | set(routes.ISSUE459_BYTE_LIMITS) | set(routes.ISSUE459_T03_BYTE_LIMITS)})
    for branch, paths in EXPECTED.items():
        failures: list[str] = []
        runner = (issue459_run if branch == routes.ISSUE459_BRANCH else
                  _issue479_runner if branch == routes.ISSUE479_BRANCH else
                  _issue494_runner if branch == routes.ISSUE494_BRANCH else
                  _issue498_runner if branch == routes.ISSUE498_BRANCH else
                  lambda _: completed([]))
        routes.check_exact_route(REPO, runner, branch, set(paths), failures)
        assert failures == []
        if branch in {
            routes.ISSUE459_BRANCH, routes.ISSUE479_BRANCH, routes.ISSUE494_BRANCH,
        }:
            continue
        missing = sorted(paths)[0]
        failures = []
        routes.check_exact_route(REPO, runner, branch, paths - {missing}, failures)
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
        suffix = branch + "-retry"
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), suffix, set(paths), failures)
        assert failures == [
            f"Stage 8 branch collides with exact reviewed route {branch}: {suffix}."
        ]
        for lookalike in (branch.upper(), confusable):
            failures = []
            routes.check_exact_route(REPO, lambda _: completed([]), lookalike, set(paths), failures)
            assert failures == []
            assert lookalike not in stage8.PROCESS_BRANCH_ALLOWED_FILES


def test_per_route_aggregate_per_file_and_binary_caps(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES | set(routes.ISSUE452_BYTE_LIMITS) | set(routes.ISSUE459_BYTE_LIMITS) | set(routes.ISSUE459_T03_BYTE_LIMITS)})
    monkeypatch.setattr(routes, "route_text_integrity", lambda *_: None)
    for branch, limit in routes.TOTAL_LIMITS.items():
        monkeypatch.setattr(routes, "route_text_charges", lambda *_, value=limit: (value + 1, {}))
        failures: list[str] = []
        runner = (issue459_run if branch == routes.ISSUE459_BRANCH else
                  _issue479_runner if branch == routes.ISSUE479_BRANCH else
                  _issue494_runner if branch == routes.ISSUE494_BRANCH else
                  _issue498_runner if branch == routes.ISSUE498_BRANCH else
                  lambda _: completed([]))
        routes.check_exact_route(REPO, runner, branch, EXPECTED[branch], failures)
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


def test_issue368_binding_compat_route_is_exact_bounded_and_base_pinned() -> None:
    branch = routes.ISSUE368_BINDING_COMPAT_BRANCH
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-368-provider-binding-compat.json").read_text()
    )
    assert branch == "stage8-issue-368-google-presenter-binding-compat"
    assert set(artifact["scope"]["required"]) == EXPECTED[branch] == routes.ROUTES[branch]
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    assert routes.TOTAL_LIMITS[branch] == 800
    assert routes.TEXT_LIMITS[branch]["backend/app/tts_provider.py"] == 20
    assert routes.TEXT_LIMITS[branch]["docs/STATUS.md"] == 100
    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_BINDING_COMPAT_BASE + "\n")

    assert routes.route_base(good, branch) == routes.ISSUE368_BINDING_COMPAT_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_BINDING_COMPAT_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_BINDING_COMPAT_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]


def test_issue368_auth_transport_route_is_exact_bounded_and_base_pinned() -> None:
    branch = routes.ISSUE368_AUTH_TRANSPORT_BRANCH
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-368-auth-transport.json").read_text()
    )
    expected = EXPECTED[branch]
    assert branch == "stage8-368-google-auth-public-transport-fix"
    assert set(artifact["scope"]["required"]) == expected == routes.ROUTES[branch]
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    assert routes.ROUTE_ISSUES[branch] == 368
    assert routes.TOTAL_LIMITS[branch] == 900
    assert routes.TEXT_LIMITS[branch] == {
        "backend/app/google_tts_runtime.py": 20,
        "tests/unit/test_google_tts_runtime.py": 80,
        "docs/governance/preflights/issue-368-auth-transport.json": 220,
        "scripts/quality/stage8_cut1_routes.py": 140,
        "tests/unit/test_stage8_cut1_routes.py": 200,
        "docs/STATUS.md": 100,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 60,
        "docs/TRACEABILITY.md": 80,
    }
    context = {
        "issue_number": 368,
        "branch": branch,
        "changed_files": artifact["scope"]["required"],
    }
    assert routes.validate_governance_preflight(artifact, context=context) == []
    mutated = copy.deepcopy(context)
    mutated["changed_files"] = [*mutated["changed_files"], "backend/app/tts_provider.py"]
    assert [
        finding.code
        for finding in routes.validate_governance_preflight(artifact, context=mutated)
    ] == ["GPF.SCOPE.CHANGE_FORBIDDEN"]

    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_REFRESH_TRANSPORT_BASE + "\n")

    assert routes.route_base(good, branch) == routes.ISSUE368_REFRESH_TRANSPORT_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_REFRESH_TRANSPORT_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_REFRESH_TRANSPORT_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]


def test_issue368_timeout_route_is_exact_bounded_and_base_pinned() -> None:
    branch = routes.ISSUE368_TIMEOUT_BRANCH
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-368-google-tts-timeout.json").read_text()
    )
    expected = EXPECTED[branch]
    assert branch == "stage8-368-google-tts-long-response-timeout"
    assert set(artifact["scope"]["required"]) == expected == routes.ROUTES[branch]
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    assert routes.ROUTE_ISSUES[branch] == 368
    assert routes.TOTAL_LIMITS[branch] == 1220
    assert routes.TEXT_LIMITS[branch] == {
        "backend/app/google_tts_runtime.py": 40,
        "backend/app/tts_provider.py": 40,
        "tests/unit/test_google_tts_runtime.py": 100,
        "tests/unit/test_stage6_tts_provider.py": 120,
        "docs/governance/preflights/issue-368-google-tts-timeout.json": 260,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 220,
        "docs/STATUS.md": 100,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 100,
        "docs/TRACEABILITY.md": 80,
    }
    context = {
        "issue_number": 368,
        "branch": branch,
        "changed_files": artifact["scope"]["required"],
    }
    assert routes.validate_governance_preflight(artifact, context=context) == []
    mutated = copy.deepcopy(context)
    mutated["changed_files"] = [*mutated["changed_files"], "frontend/package.json"]
    assert [
        finding.code
        for finding in routes.validate_governance_preflight(artifact, context=mutated)
    ] == ["GPF.SCOPE.CHANGE_FORBIDDEN"]

    calls: list[list[str]] = []

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return completed(args, out=routes.ISSUE368_TIMEOUT_BASE + "\n")

    assert routes.route_base(good, branch) == routes.ISSUE368_TIMEOUT_BASE
    assert calls == [
        ["git", "rev-parse", f"{routes.ISSUE368_TIMEOUT_BASE}^{{commit}}"],
        ["git", "merge-base", routes.ISSUE368_TIMEOUT_BASE, "HEAD"],
        ["git", "merge-base", "origin/main", "HEAD"],
    ]


def test_issue494_failure_diagnostic_route_is_exact_bounded_and_base_pinned() -> None:
    branch = routes.ISSUE494_BRANCH
    artifact = json.loads(
        (
            REPO
            / "docs/governance/preflights/issue-494-google-tts-failure-diagnostics.json"
        ).read_text()
    )
    expected = EXPECTED[branch]
    assert branch == "stage8-494-google-tts-failure-diagnostics"
    assert set(artifact["scope"]["required"]) == expected == routes.ROUTES[branch]
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    assert routes.ROUTE_ISSUES[branch] == 494
    assert routes.TOTAL_LIMITS[branch] == 1420
    assert routes.TEXT_LIMITS[branch] == {
        "backend/app/tts_provider.py": 180,
        "tests/unit/test_stage6_tts_provider.py": 260,
        "docs/governance/preflights/issue-494-google-tts-failure-diagnostics.json": 260,
        "scripts/quality/stage8_cut1_routes.py": 160,
        "tests/unit/test_stage8_cut1_routes.py": 220,
        "docs/STATUS.md": 120,
        "docs/ADR/0056-cut1-google-gemini-tts.md": 120,
        "docs/TRACEABILITY.md": 100,
    }
    context = {"issue_number": 494, "branch": branch, "changed_files": list(expected)}
    assert routes.validate_governance_preflight(artifact, context=context) == []
    mutated = copy.deepcopy(context)
    mutated["changed_files"] = [*mutated["changed_files"], "backend/app/google_tts_runtime.py"]
    assert [
        finding.code
        for finding in routes.validate_governance_preflight(artifact, context=mutated)
    ] == ["GPF.SCOPE.CHANGE_FORBIDDEN"]
    assert all(
        value in artifact["objective"]
        for value in (
            routes.ISSUE494_BASE,
            routes.ISSUE494_FROZEN_HEAD,
            routes.ISSUE494_TRANSITION_BASE,
            routes.ISSUE494_TRANSITION_MERGE,
            routes.ISSUE494_TRANSITION_COMMENT,
            routes.ISSUE494_TRANSITION_SHA256,
        )
    )


def test_issue494_requires_exact_reviewed_main_transition() -> None:
    original = "ca49843ada493162fa02ff7331b7c6adf3b505c9"
    frozen = "c217a088af84f62138f874a164bdbb75cc0f5987"
    transition_base = "99f1d6a46bf9ee42d28aa04f46792ea56f392ab2"
    transition_merge = "97671772b7ab8ef2c583cecde98f35a9e472457b"
    assert routes.ISSUE494_BASE == original
    assert routes.ISSUE494_FROZEN_HEAD == frozen
    assert routes.ISSUE494_TRANSITION_BASE == transition_base
    assert routes.ISSUE494_TRANSITION_MERGE == transition_merge
    assert routes.ISSUE494_TRANSITION_COMMENT == "5499248540"
    assert routes.ISSUE494_TRANSITION_SHA256 == (
        "3c0968ef0827dfa314a8591230e410b4dd5a4b4092223b5f76fdc72499bbe9a3"
    )

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "rev-parse"]:
            value = (
                transition_base
                if args[2] == "origin/main^{commit}"
                else args[2].removesuffix("^{commit}")
            )
            return completed(args, out=value + "\n")
        if args[:3] == ["git", "show", "-s"]:
            return completed(args, out=f"{frozen} {transition_base}\n")
        return completed(args)

    assert routes.route_base(good, routes.ISSUE494_BRANCH) == transition_base

    def drifted_main(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "rev-parse", "origin/main^{commit}"]:
            return completed(args, out=original + "\n")
        return good(args)

    def forged_parents(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:3] == ["git", "show", "-s"]:
            return completed(args, out=f"{transition_base} {frozen}\n")
        return good(args)

    for broken in (drifted_main, forged_parents):
        error = pytest.raises(
            RuntimeError, routes.route_base, broken, routes.ISSUE494_BRANCH
        )
        assert "Issue #494 reviewed transition" in str(error.value)


def test_issue494_rejects_transition_snapshot_drift_and_rename(monkeypatch: Any) -> None:
    branch = routes.ISSUE494_BRANCH
    expected = EXPECTED[branch]
    missing = "backend/app/tts_provider.py"
    monkeypatch.setattr(routes, "route_base", lambda *_: routes.ISSUE494_TRANSITION_BASE)
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))

    def drifted(args: list[str]) -> subprocess.CompletedProcess[str]:
        if "--name-only" in args:
            return completed(args, out="\0".join(sorted(expected - {missing})) + "\0")
        if "--name-status" in args:
            return completed(
                args,
                out="R100\0backend/app/tts_provider.py\0backend/app/tts_diagnostic.py\0",
            )
        return completed(args)

    failures: list[str] = []
    routes.check_exact_route(REPO, drifted, branch, expected, failures)
    assert f"Issue #494 route snapshot is missing required path: {missing}" in failures
    assert "Issue #494 route forbids deleted, renamed, or copied paths." in failures


def test_issue498_official_grpc_route_is_exact_bounded_and_base_pinned() -> None:
    branch = routes.ISSUE498_BRANCH
    artifact = json.loads((REPO / "docs/governance/preflights/issue-498-google-tts-official-grpc.json").read_text())
    assert branch == "stage8-498-google-tts-official-grpc"
    assert routes.ISSUE498_BASE == "8fb9b6d143515a6e5cfe3c395477e51696fe782b"
    assert routes.ISSUE498_TREE == "21b5c26355262482b02554d4115fc5567b6fb253"
    assert routes.ISSUE498_FREEZE_COMMENT == "5500521261"
    assert routes.ISSUE498_FREEZE_SHA256 == "fafc0f0a8ae18c9cc08d9dbab668235546f652aa780256792d5d1cb0e8f9f58b"
    assert routes.ISSUE498_AMENDMENT_COMMENT == "5500539931"
    assert routes.ISSUE498_AMENDMENT_SHA256 == "30faa0f1062545413efaa7b6e9bc38f9b2cd82f2554078f666aac04e4f8ef843"
    assert routes.ISSUE498_BASE_AMENDMENT_COMMENT == "5504413401"
    assert routes.ISSUE498_BASE_AMENDMENT_SHA256 == "f575ac4c5eb75a2d7e45740e90b4652d08cd5601837a29a2dffe477279e604e9"
    assert set(artifact["scope"]["required"]) == ISSUE498_EXPECTED == routes.ROUTES[branch]
    assert artifact["scope"]["required"] == artifact["scope"]["allowed_prefixes"]
    assert routes.ROUTE_ISSUES[branch] == 498
    assert routes.TOTAL_LIMITS[branch] == 5200
    assert routes.TEXT_LIMITS[branch] == ISSUE498_LINE_CAPS
    context = {"issue_number": 498, "branch": branch,
               "changed_files": artifact["scope"]["required"]}
    assert routes.validate_governance_preflight(artifact, context=context) == []
    mutated = copy.deepcopy(context)
    mutated["changed_files"] = [*mutated["changed_files"], "backend/app/narration.py"]
    assert [finding.code for finding in routes.validate_governance_preflight(
        artifact, context=mutated)] == ["GPF.SCOPE.CHANGE_FORBIDDEN"]
    assert all(value in artifact["objective"] for value in (
        routes.ISSUE498_BASE, routes.ISSUE498_TREE, routes.ISSUE498_FREEZE_COMMENT,
        routes.ISSUE498_FREEZE_SHA256, routes.ISSUE498_AMENDMENT_COMMENT,
        routes.ISSUE498_AMENDMENT_SHA256, routes.ISSUE498_BASE_AMENDMENT_COMMENT,
        routes.ISSUE498_BASE_AMENDMENT_SHA256,
    ))


def test_issue498_requires_exact_current_main_branch_point() -> None:
    base = routes.ISSUE498_BASE

    def good(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] in (["git", "rev-parse"], ["git", "merge-base"]):
            return completed(args, out=base + "\n")
        return completed(args)

    assert routes.route_base(good, routes.ISSUE498_BRANCH) == base

    def drifted(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "merge-base", "origin/main", "HEAD"]:
            return completed(args, out="0" * 40 + "\n")
        return good(args)

    with pytest.raises(RuntimeError, match="Issue #498 fixed base evidence"):
        routes.route_base(drifted, routes.ISSUE498_BRANCH)


def test_issue498_requires_exact_sixteen_commit_tdd_topology_and_final_authority() -> None:
    artifact = json.loads(
        (REPO / "docs/governance/preflights/issue-498-google-tts-official-grpc.json").read_text()
    )
    assert routes.ISSUE498_TOPOLOGY_COMMENT == "5504600826"
    assert routes.ISSUE498_TOPOLOGY_SHA256 == (
        "ec2477cfc8ce73eb624ce3e4b154b34336859fb100997dcfb6202234f191205f"
    )
    assert routes.ISSUE498_REVIEW_CORRECTION_COMMENT == "5504653805"
    assert routes.ISSUE498_REVIEW_CORRECTION_SHA256 == (
        "a5cea09fcf3964caabd34ea7ea3a1ff991bc79599a2442b3680b960f5b8c7b5e"
    )
    assert routes.ISSUE498_TRACEBACK_CORRECTION_COMMENT == "5504746823"
    assert routes.ISSUE498_TRACEBACK_CORRECTION_SHA256 == (
        "9a179acb4bdc513cb2a6d122ebe271885ee927baf4972e8113f8ca66f1137217"
    )
    assert routes.ISSUE498_MERGE_PARITY_COMMENT == "5504929555"
    assert routes.ISSUE498_MERGE_PARITY_SHA256 == (
        "ec19733768f13672b8d322ae262c19fd8316c69a91ce197784f7cd5783b0b95c"
    )
    assert all(
        value in artifact["objective"]
        for value in (
            routes.ISSUE498_TOPOLOGY_COMMENT,
            routes.ISSUE498_TOPOLOGY_SHA256,
            routes.ISSUE498_REVIEW_CORRECTION_COMMENT,
            routes.ISSUE498_REVIEW_CORRECTION_SHA256,
            routes.ISSUE498_TRACEBACK_CORRECTION_COMMENT,
            routes.ISSUE498_TRACEBACK_CORRECTION_SHA256,
            routes.ISSUE498_MERGE_PARITY_COMMENT,
            routes.ISSUE498_MERGE_PARITY_SHA256,
        )
    )

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, cwd=REPO, check=False, capture_output=True, text=True)

    assert routes.issue498_commit_topology_failures(run) == []


@pytest.mark.parametrize("mutation", ["missing", "extra", "old-hash", "subject", "command"])
def test_issue498_tdd_topology_mutations_fail_closed(mutation: str) -> None:
    records = list(routes.ISSUE498_COMMIT_TOPOLOGY)
    if mutation == "missing":
        records.pop()
    elif mutation == "extra":
        records.append(("f" * 40, "fix(tts): unauthorized extra commit (#498)"))
    elif mutation == "old-hash":
        records[0] = ("0" * 40, records[0][1])
    elif mutation == "subject":
        records[-1] = (records[-1][0], "fix(tts): changed subject (#498)")
    output = "".join(
        f"{commit if commit is not None else 'a' * 40}\0{subject}\0"
        for commit, subject in records
    )

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "rev-parse", "HEAD"]:
            return completed(
                args,
                1 if mutation == "command" else 0,
                "e8a0ab585d8bb95625646fb626b4fe3980926d14\n",
            )
        return completed(args, out=output)

    assert routes.issue498_commit_topology_failures(run) == [
        "Issue #498 exact TDD commit topology drifted."
    ]


def test_issue498_tdd_topology_accepts_exact_two_parent_hosted_merge() -> None:
    feature_head = "e8a0ab585d8bb95625646fb626b4fe3980926d14"
    output = "".join(
        f"{commit if commit is not None else feature_head}\0{subject}\0"
        for commit, subject in routes.ISSUE498_COMMIT_TOPOLOGY
    )

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "show", "-s", "--format=%P%x00%T", "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"]:
            return completed(args, out=f"{routes.ISSUE498_BASE}\0{'76495e566a78a7951c33314ac742606c85ee92e5'}\n")
        if args == ["git", "rev-parse", "HEAD"]:
            return completed(args, out="a" * 40 + "\n")
        if args == ["git", "show", "-s", "--format=%P", "HEAD"]:
            return completed(args, out=f"{routes.ISSUE498_BASE} {feature_head}\n")
        if args[-1] == f"{routes.ISSUE498_BASE}..{feature_head}":
            return completed(args, out=output)
        return completed(args, code=1)

    assert routes.issue498_commit_topology_failures(run) == []


@pytest.mark.parametrize("head", ["e1fe126372d5c5a06dc7d2f9c76cb205da8643e7", "d" * 40])
def test_issue498_tdd_topology_accepts_exact_squash_anchor_and_descendant(head: str) -> None:
    squash = "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"
    tree = "76495e566a78a7951c33314ac742606c85ee92e5"

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "show", "-s", "--format=%P%x00%T", squash]:
            return completed(args, out=f"{routes.ISSUE498_BASE}\0{tree}\n")
        if args == ["git", "rev-parse", "HEAD"]:
            return completed(args, out=head + "\n")
        if args == ["git", "show", "-s", "--format=%P", "HEAD"]:
            return completed(args, out=routes.ISSUE498_BASE + "\n")
        if args == ["git", "merge-base", "--is-ancestor", squash, head]:
            return completed(args)
        return completed(args, code=1)

    assert routes.issue498_commit_topology_failures(run) == []


@pytest.mark.parametrize("mutation", ["parent", "tree", "ancestry", "anchor-command"])
def test_issue498_tdd_topology_rejects_post_squash_mutations(mutation: str) -> None:
    squash = "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"
    head = "d" * 40
    parent = "0" * 40 if mutation == "parent" else routes.ISSUE498_BASE
    tree = "0" * 40 if mutation == "tree" else "76495e566a78a7951c33314ac742606c85ee92e5"

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "show", "-s", "--format=%P%x00%T", squash]:
            return completed(args, code=1 if mutation == "anchor-command" else 0, out=f"{parent}\0{tree}\n")
        if args == ["git", "rev-parse", "HEAD"]:
            return completed(args, out=head + "\n")
        if args == ["git", "show", "-s", "--format=%P", "HEAD"]:
            return completed(args, out=routes.ISSUE498_BASE + "\n")
        if args == ["git", "merge-base", "--is-ancestor", squash, head]:
            return completed(args, code=1 if mutation == "ancestry" else 0)
        return completed(args, code=1)

    assert routes.issue498_commit_topology_failures(run) == [
        "Issue #498 exact TDD commit topology drifted."
    ]


def test_issue498_tdd_topology_rejects_synthetic_merge_when_anchor_is_unavailable() -> None:
    feature_head = "e8a0ab585d8bb95625646fb626b4fe3980926d14"

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "show", "-s", "--format=%P%x00%T", "e1fe126372d5c5a06dc7d2f9c76cb205da8643e7"]:
            return completed(args, code=1)
        if args == ["git", "rev-parse", "HEAD"]:
            return completed(args, out="a" * 40 + "\n")
        if args == ["git", "show", "-s", "--format=%P", "HEAD"]:
            return completed(args, out=f"{routes.ISSUE498_BASE} {feature_head}\n")
        return completed(args)

    assert routes.issue498_commit_topology_failures(run) == [
        "Issue #498 exact TDD commit topology drifted."
    ]


@pytest.mark.parametrize(
    "parents",
    (
        f"{'0' * 40} {'f' * 40}",
        f"{routes.ISSUE498_BASE} {'f' * 40} {'e' * 40}",
        "",
    ),
)
def test_issue498_tdd_topology_rejects_invalid_merge_parents(parents: str) -> None:
    output = "".join(
        f"{commit if commit is not None else 'f' * 40}\0{subject}\0"
        for commit, subject in routes.ISSUE498_COMMIT_TOPOLOGY
    )

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args == ["git", "show", "-s", "--format=%P", "HEAD"]:
            return completed(args, out=parents + "\n")
        return completed(args, out=output)

    assert routes.issue498_commit_topology_failures(run) == [
        "Issue #498 exact TDD commit topology drifted."
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


def test_issue495_route_freezes_the_lockfile_only_security_refresh() -> None:
    branch = "stage8-495-browserslist-security-refresh"
    expected = {
        "frontend/package-lock.json",
        "docs/governance/preflights/issue-495-browserslist-security-refresh.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_dependency_security_contract.py",
        "tests/unit/test_frontend_dependency_security_contract.py",
        "docs/ADR/0074-browserslist-4-28-8-security-refresh.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    }
    assert routes.ISSUE495_BRANCH == branch
    assert routes.ISSUE495_BASE == "ca49843ada493162fa02ff7331b7c6adf3b505c9"
    assert routes.ROUTES[branch] == expected
    assert routes.ROUTE_ISSUES[branch] == 495
    assert routes.TOTAL_LIMITS[branch] == 1300
    assert routes.TEXT_LIMITS[branch] == {
        "frontend/package-lock.json": 120,
        "docs/governance/preflights/issue-495-browserslist-security-refresh.json": 220,
        "scripts/quality/stage8_cut1_routes.py": 120,
        "tests/unit/test_stage8_cut1_routes.py": 160,
        "tests/unit/test_dependency_security_contract.py": 180,
        "tests/unit/test_frontend_dependency_security_contract.py": 140,
        "docs/ADR/0074-browserslist-4-28-8-security-refresh.md": 160,
        "docs/STATUS.md": 80,
        "docs/TRACEABILITY.md": 80,
    }
    preflight = json.loads(
        (REPO / "docs/governance/preflights/issue-495-browserslist-security-refresh.json")
        .read_text(encoding="utf-8")
    )
    assert set(preflight["scope"]["required"]) == expected
    assert preflight["scope"]["required"] == preflight["scope"]["allowed_prefixes"]
    assert branch in stage8.EFFECTIVE_STAGE8_ROUTES


def test_issue499_route_freezes_the_exact_pypdf_security_refresh() -> None:
    branch = "stage8-499-pypdf-6-16-2-security-refresh"
    assert routes.ISSUE499_BRANCH == branch
    assert routes.ISSUE499_BASE == "d1f5400f5c6dfec5d4b63eb3a83aa82e3330743f"
    assert routes.ROUTES[branch] == ISSUE499_EXPECTED
    assert routes.ROUTE_ISSUES[branch] == 499
    assert routes.TOTAL_LIMITS[branch] == 1000
    assert routes.TEXT_LIMITS[branch] == {
        "docs/governance/preflights/issue-499-pypdf-6-16-2-security-refresh.json": 220,
        "pyproject.toml": 20,
        "uv.lock": 100,
        "scripts/quality/stage8_cut1_routes.py": 120,
        "tests/unit/test_stage8_cut1_routes.py": 140,
        "tests/unit/test_dependency_security_contract.py": 220,
        "docs/ADR/0075-pypdf-6-16-2-security-refresh.md": 80,
        "docs/STATUS.md": 40,
        "docs/THIRD_PARTY_NOTICES.md": 40,
        "docs/TRACEABILITY.md": 20,
    }
    preflight = json.loads(
        (REPO / "docs/governance/preflights/issue-499-pypdf-6-16-2-security-refresh.json")
        .read_text(encoding="utf-8")
    )
    assert set(preflight["scope"]["required"]) == ISSUE499_EXPECTED
    assert preflight["scope"]["required"] == preflight["scope"]["allowed_prefixes"]


def test_issue499_route_rejects_branch_suffix_drift(monkeypatch: Any) -> None:
    branch = routes.ISSUE499_BRANCH + "-retry"
    assert branch not in stage8.EFFECTIVE_STAGE8_ROUTES
    assert stage8.STAGE8_BRANCH_PATTERN.match(branch)
    monkeypatch.setattr(stage8, "current_branch", lambda: branch)
    monkeypatch.setattr(
        stage8,
        "changed_files_for_stage_scope",
        lambda: ["pyproject.toml", "uv.lock"],
    )
    failures: list[str] = []
    stage8.check_stage_scope(failures)
    assert failures == [
        f"Stage 8 branch collides with exact reviewed route {routes.ISSUE499_BRANCH}: {branch}."
    ]


def test_issue499_route_rejects_fixed_base_drift_and_every_path_cap(monkeypatch: Any) -> None:
    outputs = iter(
        (
            completed([], out=routes.ISSUE499_BASE + "\n"),
            completed([], out="a" * 40 + "\n"),
        )
    )
    error = pytest.raises(
        RuntimeError,
        routes.route_base,
        lambda _: next(outputs),
        routes.ISSUE499_BRANCH,
    )
    assert "Issue #499 fixed base" in str(error.value)
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    for path, limit in routes.TEXT_LIMITS[routes.ISSUE499_BRANCH].items():
        monkeypatch.setattr(
            routes,
            "route_text_charges",
            lambda *_, value_path=path, value_limit=limit: (
                value_limit + 1,
                {value_path: value_limit + 1},
            ),
        )
        failures: list[str] = []
        routes.check_exact_route(
            REPO,
            lambda _: completed([]),
            routes.ISSUE499_BRANCH,
            ISSUE499_EXPECTED,
            failures,
        )
        assert f"Issue #499 charge for {path} exceeds {limit}." in failures


def test_issue495_lock_refresh_changes_only_six_transitive_records() -> None:
    lock_path = "frontend/package-lock.json"
    base_result = subprocess.run(
        ["git", "show", f"{routes.ISSUE495_BASE}:{lock_path}"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    before = json.loads(base_result.stdout)["packages"]
    after = json.loads((REPO / lock_path).read_text(encoding="utf-8"))["packages"]
    expected = {
        "baseline-browser-mapping": ("2.11.20", "sha512-H0ulySigv6icDJ1F7SjtdCD6PrhTpdYCmP0CactWy1+ekh0AFd0o1Wn5T8b+hnTmdBx19u9yhL6wvCylXMY7zw=="),
        "browserslist": ("4.28.8", "sha512-V2NpofLblG64mfOtSgDhOJESZEGogzDMBv/q+W6oc4LXWP/q75eOXoOaaOu1EOadB9U4Bwx/e0yzbvwKH8zalA=="),
        "caniuse-lite": ("1.0.30001810", "sha512-TITQPUkaz+aVk5GL6NhOdwk1aEaNTSDPsGFWrTuhKGtjTF70jL/Oht2W4c6rXUe5fu7Ie19VIahAXHIIiWWNeg=="),
        "electron-to-chromium": ("1.5.419", "sha512-nHMPn8x4yCxCI0iSnL+LlHL5sUoUfjLXkcRIagZ4GBdrfFLFaiLNvzJWbJqZhFT9IAhw5tUSNlhggWN+otvp/A=="),
        "node-releases": ("2.0.54", "sha512-YHs7BmmcsdAI5Ozuf8JZo6PT0mv2GIWC9vMfvUC3dp65M8hn7Ux8CPL+2oBI7juNuj9d0ndhTcznq2ODBps9cQ=="),
        "update-browserslist-db": ("1.3.2", "sha512-UQ+MSxlhRm1bzjhU+DcuXfjFO1FzNtqhK5+9Yvlp90ItDLk5vT932A0rFu619nf7RVS+Y/VeaUW1jaRDqZ8VJw=="),
    }
    changed = {path for path in before | after if before.get(path) != after.get(path)}
    assert changed == {f"node_modules/{name}" for name in expected}
    for name, identity in expected.items():
        record = after[f"node_modules/{name}"]
        assert (record["version"], record["integrity"]) == identity
