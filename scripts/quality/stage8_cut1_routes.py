"""Fail-closed Stage 8 scope and budget routes for governed Cut 1 prerequisites."""
from __future__ import annotations

import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any, Callable

from scripts.governance_preflight_v1 import validate_governance_preflight

ISSUE150_BRANCH = "cut1-process-150-semgrep-mcp-renewal"
ISSUE386_BRANCH = "cut1-process-386-modular-route-enforcement"
ISSUE413_BRANCH = "cut1-process-413-frontend-runtime-openssl"
ISSUE405_BRANCH = "process-405-heartbeat2-main-reliability"
ISSUE428_BRANCH = "cut1-process-428-nanoid-3-3-18-security"
ISSUE403_BRANCH = "cut1-process-403-nanoid-3-3-17-security"
ISSUE401_BRANCH = "cut1-process-401-pypdf-6-15-0-security"
ISSUE396_BRANCH = "cut1-process-396-js-yaml-4-3-1-security"
ISSUE385_BRANCH = "stage8-385-issue280-language-oracle"
ISSUE384_BRANCH = "stage8-384-presenter-asset-route"
ISSUE383_BRANCH = "stage8-383-presenter-assets"
ISSUE382_BRANCH = "stage8-382-cut1-narration-lock"
ISSUE367_BRANCH = "stage8-367-presenter-registry"
ISSUE397_BRANCH = "stage8-397-presenter-asset-adr-classifier"
ISSUE393_BRANCH = "stage8-393-historical-digest-test-isolation"
ISSUE368_BRANCH = "stage8-368-cut1-local-tts-audio"
ISSUE368_PROMPT_BRANCH = "stage8-368-cut1-google-tts-prompt-contract"
ISSUE368_ADAPTER_BRANCH = "stage8-368-cut1-google-tts-adapter-implementation"
ISSUE368_IMPLEMENTATION_BRANCH = "stage8-368-cut1-google-tts-runtime-transport"
ISSUE368_QUOTA_FIX_BRANCH = "stage8-368-google-tts-quota-project-binding-fix"
ISSUE415_BRANCH = "stage8-415-pr-body-live-state-reconciliation"
ISSUE415_CORRECTION_BRANCH = "stage8-415-pr-body-consistency-canary-fix"
ISSUE421_BRANCH = "stage8-421-cut1-atomic-project-facts"
ISSUE424_BRANCH = "stage8-424-master-program-authority-prelog"
ISSUE386_BASE = "48fc32a2689c9bbc03742d774f3eadb8a500dafc"
ISSUE368_BASE = "ef9cabc23762560912d99f10831241b8a65b869c"
ISSUE368_PROMPT_BASE = "ba77d59b193da8064d67261e13fb50756c2bd9e8"
ISSUE368_IMPLEMENTATION_BASE = "6766da34d73e301358f84f8eefb0985927292a26"
ISSUE368_QUOTA_FIX_BASE = "9c165f739788fb0f09b315673f9125d700d6a96b"
ISSUE421_BASE = "a868137fab607ae75d4b272301e9fc52b898e15c"
ISSUE424_BASE = "afcf0325c3ec925b68b770eda0bb8c839bcce4dd"
ISSUE150_BASE = "a02286240212ad8958915aec01aa5ebaf60fa705"
SECURITY_PREFLIGHTS = {
    150: ("Issue150SecurityRenewalPreflightV1", "e6a569cb6254ef58c36fb44e9cdece26e0816b49c9f62ce08e9d90f3843c97e3"),
    428: ("Issue428NanoidSecurityPreflightV1", "0d8da352c98855bc481581f1ca13cc2d4e994838b1afb31d974ad2b17caf7a9b"),
}

ROUTES = {
    ISSUE150_BRANCH: {
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
    ISSUE424_BRANCH: {
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
    ISSUE421_BRANCH: {
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
    ISSUE415_BRANCH: {
        ".github/pull_request_template.md", ".github/workflows/pr-body-consistency.yml", "AGENTS.md", "Makefile",
        "docs/ADR/0040-pr-body-live-state-reconciliation.md", "docs/CODEX_OPERATING_MODEL.md", "docs/QUALITY_GATES.md", "docs/STATUS.md",
        "docs/agent-context/context-policy-manifest-v1.json", "docs/governance/preflights/issue-415.json",
        "scripts/quality/pr_body_consistency.py", "scripts/quality/pr_body_consistency_cli.py", "scripts/quality/stage8_cut1_routes.py",
        "tests/fixtures/pr_body_consistency/live_pr.json", "tests/unit/test_pr_body_consistency.py", "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE415_CORRECTION_BRANCH: {
        ".github/workflows/pr-body-consistency.yml",
        "docs/STATUS.md",
        "docs/governance/preflights/issue-415.json",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_pr_body_consistency.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE413_BRANCH: {
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
    ISSUE368_ADAPTER_BRANCH: {
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
    ISSUE368_IMPLEMENTATION_BRANCH: {
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
    ISSUE368_QUOTA_FIX_BRANCH: {
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
    ISSUE368_PROMPT_BRANCH: {
        "docs/governance/preflights/issue-368.json",
        "docs/governance/cut1-google-gemini-tts-style-prompts-v1.json",
        "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        "docs/ADR/0056-cut1-google-gemini-tts.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
    },
    ISSUE368_BRANCH: {
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
    ISSUE382_BRANCH: {
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
    ISSUE405_BRANCH: {
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
    ISSUE428_BRANCH: {
        "docs/governance/preflights/issue-428.json", "frontend/package-lock.json",
        "scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
        "tests/unit/test_frontend_dependency_security_contract.py", "tests/unit/test_stage8_quality_gate.py",
        "docs/ADR/0062-nanoid-3-3-18-security-refresh.md", "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md", "docs/STATUS.md", "docs/TRACEABILITY.md",
        "docs/THIRD_PARTY_NOTICES.md",
    },
    ISSUE403_BRANCH: {
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
    ISSUE401_BRANCH: {
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
    ISSUE396_BRANCH: {
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
    ISSUE386_BRANCH: {
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
    ISSUE385_BRANCH: {
        "docs/governance/preflights/issue-385.json",
        "tests/acceptance/test_issue280_local_e2e_demo.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
    },
    ISSUE384_BRANCH: {
        "docs/governance/preflights/issue-384.json",
        "scripts/quality/check_stage8_docs.py",
        "scripts/quality/stage8_cut1_routes.py",
        "tests/unit/test_stage8_cut1_routes.py",
        "docs/QUALITY_GATES.md",
        "docs/STAGE_ISSUE_PLAN.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE383_BRANCH: {
        "docs/governance/preflights/issue-383.json",
        "frontend/public/demo/myra-synthetic-presenter.webp",
        "frontend/public/demo/raj-synthetic-presenter.webp",
        "tests/unit/test_cut1_presenter_assets.py",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/STATUS.md",
        "docs/TRACEABILITY.md",
    },
    ISSUE367_BRANCH: {
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
    ISSUE397_BRANCH: {
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
    ISSUE393_BRANCH: {
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
ROUTE_ISSUES = {ISSUE150_BRANCH: 150, ISSUE424_BRANCH: 424, ISSUE421_BRANCH: 421, ISSUE415_BRANCH: 415, ISSUE415_CORRECTION_BRANCH: 415, ISSUE413_BRANCH: 413, ISSUE368_ADAPTER_BRANCH: 368, ISSUE368_IMPLEMENTATION_BRANCH: 368, ISSUE368_QUOTA_FIX_BRANCH: 368, ISSUE368_PROMPT_BRANCH: 368, ISSUE368_BRANCH: 368, ISSUE405_BRANCH: 405, ISSUE428_BRANCH: 428, ISSUE403_BRANCH: 403, ISSUE401_BRANCH: 401, ISSUE396_BRANCH: 396,
                ISSUE386_BRANCH: 386, ISSUE385_BRANCH: 385,
                ISSUE384_BRANCH: 384, ISSUE383_BRANCH: 383, ISSUE397_BRANCH: 397,
                ISSUE393_BRANCH: 393, ISSUE382_BRANCH: 382, ISSUE367_BRANCH: 367}
TOTAL_LIMITS = {ISSUE150_BRANCH: 1000, ISSUE424_BRANCH: 8500, ISSUE421_BRANCH: 4000, ISSUE415_BRANCH: 5000, ISSUE415_CORRECTION_BRANCH: 800, ISSUE413_BRANCH: 5000, ISSUE368_ADAPTER_BRANCH: 5600, ISSUE368_IMPLEMENTATION_BRANCH: 3600, ISSUE368_QUOTA_FIX_BRANCH: 2800, ISSUE368_PROMPT_BRANCH: 1000, ISSUE368_BRANCH: 3200, ISSUE405_BRANCH: 800, ISSUE428_BRANCH: 500, ISSUE403_BRANCH: 650, ISSUE401_BRANCH: 600, ISSUE396_BRANCH: 500,
                ISSUE386_BRANCH: 700, ISSUE385_BRANCH: 350,
                ISSUE384_BRANCH: 500, ISSUE383_BRANCH: 700, ISSUE397_BRANCH: 500,
                ISSUE393_BRANCH: 700, ISSUE382_BRANCH: 3200, ISSUE367_BRANCH: 2000}
ISSUE383_BINARY_FILES = {
    "frontend/public/demo/myra-synthetic-presenter.webp",
    "frontend/public/demo/raj-synthetic-presenter.webp",
}
TEXT_LIMITS = {
    ISSUE150_BRANCH: {
        path: 180 if path.endswith("issue-150.json")
        else 150 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 120 if path.startswith("tests/unit/") or path.endswith("issue-428.json")
        else 100
        for path in ROUTES[ISSUE150_BRANCH]
    },
    ISSUE424_BRANCH: {
        path: {
            "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md": 5000,
            "docs/governance/narratwin-master-program-v1.json": 180,
            "docs/governance/preflights/issue-424.json": 500,
            "docs/reviews/ISSUE_424_EXECUTION_SPEC_REVIEW.md": 500,
            "docs/reviews/ISSUE_424_CUT1_FALSE_SUCCESS_REVIEW.md": 500,
            "docs/reviews/ISSUE_424_PLATFORM_SECURITY_LEARNING_REVIEW.md": 500,
            "docs/ADR/0059-master-program-authority-and-route-bootstrap.md": 400,
            "docs/STAGE_ISSUE_PLAN.md": 250,
            "docs/STATUS.md": 250,
            "docs/TRACEABILITY.md": 250,
            "scripts/quality/stage8_cut1_routes.py": 300,
            "tests/unit/test_stage8_cut1_routes.py": 320,
            "scripts/guardrails_check.py": 100,
            "tests/unit/test_guardrails_check.py": 180,
        }[path]
        for path in ROUTES[ISSUE424_BRANCH]
    },
    ISSUE421_BRANCH: {
        path: {
            "docs/governance/preflights/issue-421.json": 500,
            "docs/governance/cut1-project-facts-v1.json": 600,
            "backend/app/narration.py": 160,
            "backend/app/cut1_grounding.py": 900,
            "backend/app/rag/models.py": 180,
            "backend/app/stage4.py": 600,
            "backend/app/evaluation_lineage.py": 300,
            "tests/unit/test_cut1_atomic_grounding.py": 1200,
            "tests/unit/test_cut1_narration.py": 500,
            "tests/unit/test_evaluation_lineage.py": 400,
            "scripts/quality/stage8_cut1_routes.py": 180,
            "tests/unit/test_stage8_cut1_routes.py": 300,
            "docs/ADR/0058-cut1-atomic-project-facts-grounding.md": 320,
            "docs/API_CONTRACT.md": 180,
            "docs/DATA_MODEL.md": 180,
            "docs/SECURITY_AND_PRIVACY.md": 220,
            "docs/OBSERVABILITY_AND_COST.md": 180,
            "docs/QUALITY_GATES.md": 180,
            "docs/STAGE_ISSUE_PLAN.md": 180,
            "docs/STATUS.md": 220,
            "docs/TRACEABILITY.md": 220,
        }[path]
        for path in ROUTES[ISSUE421_BRANCH]
    },
    ISSUE415_BRANCH: {path: 1200 if path == "scripts/quality/pr_body_consistency.py" else 900 if path == "tests/unit/test_pr_body_consistency.py" else 400 if path in {"scripts/quality/pr_body_consistency_cli.py", ".github/workflows/pr-body-consistency.yml"} else 250 for path in ROUTES[ISSUE415_BRANCH]},
    ISSUE415_CORRECTION_BRANCH: {path: 250 for path in ROUTES[ISSUE415_CORRECTION_BRANCH]},
    ISSUE413_BRANCH: {
        path: 700 if path in {"scripts/ci/docker-image-scan.sh", "tests/unit/test_container_scan_consensus.py"}
        else 500 if path in {"scripts/ci/check_container_scan_consensus.py", "tests/unit/test_stage8_quality_gate.py"}
        else 350 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 400 if path == "tests/unit/test_stage8_node_security.py"
        else 300 if path == "scripts/quality/stage8_node_security.py"
        else 80 if path == "scripts/quality/check_stage8_docs.py"
        else 300 if path in {"frontend/Dockerfile", "tests/unit/test_frontend_container_runtime.py",
                             "docs/governance/preflights/issue-413.json"}
        else 220
        for path in ROUTES[ISSUE413_BRANCH]
    },
    ISSUE368_ADAPTER_BRANCH: {
        path: 1700 if path == "backend/app/tts_provider.py"
        else 1200 if path == "tests/unit/test_stage6_tts_provider.py"
        else 600 if path in {"backend/app/narration.py", "backend/app/stage6.py",
                             "tests/unit/test_cut1_narration.py", "tests/unit/test_stage6_multilingual.py"}
        else 400 if path in {"tests/api/test_stage6_multilingual_api.py",
                             "scripts/quality/stage8_cut1_routes.py",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 300 if path == "docs/governance/preflights/issue-368.json" else 240
        for path in ROUTES[ISSUE368_ADAPTER_BRANCH]
    },
    ISSUE368_IMPLEMENTATION_BRANCH: {
        path: {
            "docs/governance/preflights/issue-368.json": 240,
            "backend/app/google_tts_runtime.py": 700,
            "backend/app/tts_provider.py": 220,
            "pyproject.toml": 20,
            "uv.lock": 300,
            "tests/unit/test_google_tts_runtime.py": 800,
            "tests/unit/test_dependency_security_contract.py": 220,
            "scripts/quality/stage8_cut1_routes.py": 60,
            "tests/unit/test_stage8_cut1_routes.py": 160,
            "docs/ADR/0056-cut1-google-gemini-tts.md": 180,
            "docs/ARCHITECTURE.md": 70,
            "docs/OBSERVABILITY_AND_COST.md": 70,
            "docs/QUALITY_GATES.md": 70,
            "docs/SECURITY_AND_PRIVACY.md": 100,
            "docs/STAGE_ISSUE_PLAN.md": 100,
            "docs/STATUS.md": 120,
            "docs/THIRD_PARTY_NOTICES.md": 150,
            "docs/TRACEABILITY.md": 220,
        }[path]
        for path in ROUTES[ISSUE368_IMPLEMENTATION_BRANCH]
    },
    ISSUE368_QUOTA_FIX_BRANCH: {
        path: {
            "backend/app/google_tts_runtime.py": 500,
            "backend/app/tts_provider.py": 500,
            "tests/unit/test_google_tts_runtime.py": 600,
            "tests/unit/test_stage6_tts_provider.py": 800,
            "docs/governance/preflights/issue-368.json": 500,
            "scripts/quality/stage8_cut1_routes.py": 160,
            "tests/unit/test_stage8_cut1_routes.py": 260,
            "docs/ADR/0056-cut1-google-gemini-tts.md": 240,
            "docs/API_CONTRACT.md": 160,
            "docs/DATA_MODEL.md": 160,
            "docs/SECURITY_AND_PRIVACY.md": 220,
            "docs/OBSERVABILITY_AND_COST.md": 180,
            "docs/STATUS.md": 220,
            "docs/TRACEABILITY.md": 220,
            "scripts/ci/verify_branch_protection.py": 80,
            "tests/unit/test_branch_protection_verifier.py": 220,
            "tests/unit/test_governance_preflight_github.py": 80,
            "docs/REPOSITORY_GUARDRAILS.md": 80,
            "docs/agent-context/context-policy-manifest-v1.json": 10,
        }[path]
        for path in ROUTES[ISSUE368_QUOTA_FIX_BRANCH]
    },
    ISSUE368_PROMPT_BRANCH: {
        path: 260 if path == "tests/unit/test_stage8_cut1_routes.py"
        else 180 if path == "docs/governance/preflights/issue-368.json"
        else 140 if path in {
            "docs/governance/cut1-google-gemini-tts-style-prompts-v1.json",
            "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md",
        }
        else 100 if path == "scripts/quality/stage8_cut1_routes.py" else 60
        for path in ROUTES[ISSUE368_PROMPT_BRANCH]
    },
    ISSUE368_BRANCH: {
        path: 1200 if path == "docs/reviews/ISSUE_368_GOOGLE_GEMINI_TTS_GOVERNANCE.md"
        else 500 if path == "docs/ADR/0056-cut1-google-gemini-tts.md"
        else 300 if path == "docs/governance/preflights/issue-368.json"
        else 220 if path in {"docs/SECURITY_AND_PRIVACY.md", "docs/OBSERVABILITY_AND_COST.md",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 180 if path == "scripts/quality/stage8_cut1_routes.py" else 160
        for path in ROUTES[ISSUE368_BRANCH]
    },
    ISSUE382_BRANCH: {
        path: 220 if path.endswith("issue-382.json") or path.startswith("docs/ADR/0055-")
        else 750 if path == "backend/app/narration.py"
        else 900 if path == "tests/unit/test_cut1_narration.py"
        else 120 for path in ROUTES[ISSUE382_BRANCH]
    },
    ISSUE405_BRANCH: {
        path: 220 if path.endswith("issue-405.json") else 160
        for path in ROUTES[ISSUE405_BRANCH]
    },
    ISSUE403_BRANCH: {
        path: 180 if path.endswith("issue-403.json")
        else 110 if path == "tests/unit/test_frontend_dependency_security_contract.py"
        else 80 if path in {"scripts/ci/check_container_scan_consensus.py",
                            "tests/unit/test_container_scan_consensus.py"}
        else 70 if path == "scripts/quality/stage8_cut1_routes.py"
        else 60 if path.startswith("docs/ADR/") else 40
        for path in ROUTES[ISSUE403_BRANCH]
    },
    ISSUE428_BRANCH: {
        path: 150 if path.endswith("issue-428.json") else 110
        if path == "tests/unit/test_frontend_dependency_security_contract.py" else 70
        for path in ROUTES[ISSUE428_BRANCH]
    },
    ISSUE401_BRANCH: {
        path: 190 if path.endswith("issue-401.json")
        else 100 if path.startswith("tests/unit/")
        else 80 if path == "scripts/quality/stage8_cut1_routes.py"
        else 60 if path.startswith("docs/ADR/") else 40
        for path in ROUTES[ISSUE401_BRANCH]
    },
    ISSUE396_BRANCH: {
        path: 180 if path.endswith("issue-396.json") else 80 if path.startswith("tests/unit/") else 40
        for path in ROUTES[ISSUE396_BRANCH]
    },
    ISSUE386_BRANCH: {
        path: 300 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 120 if path == "tests/acceptance/test_issue280_local_e2e_demo.py"
        else 20 if path == "tests/unit/test_stage8_quality_gate.py"
        else 80 if path == "scripts/quality/check_stage8_docs.py" else 120
        for path in ROUTES[ISSUE386_BRANCH]
    },
    ISSUE385_BRANCH: {
        path: 120 if path == "tests/acceptance/test_issue280_local_e2e_demo.py" else 100
        for path in ROUTES[ISSUE385_BRANCH]
    },
    ISSUE384_BRANCH: {
        path: 10 if path == "scripts/quality/check_stage8_docs.py"
        else 20 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py"}
        else 160 for path in ROUTES[ISSUE384_BRANCH]
    },
    ISSUE383_BRANCH: {
        path: 260 if path == "tests/unit/test_cut1_presenter_assets.py" else 160
        for path in ROUTES[ISSUE383_BRANCH] - ISSUE383_BINARY_FILES
    },
    ISSUE367_BRANCH: {
        path: 500 if path in {"backend/app/presenter_registry.py",
                              "tests/unit/test_cut1_presenter_registry.py"}
        else 260 if path == "backend/app/presenter_registry.json"
        else 220 if path in {"docs/governance/preflights/issue-367.json",
                             "docs/ADR/0054-cut1-presenter-registry.md"}
        else 180 if path in {"scripts/quality/stage8_cut1_routes.py",
                             "tests/unit/test_stage8_cut1_routes.py"}
        else 120 for path in ROUTES[ISSUE367_BRANCH]
    },
    ISSUE397_BRANCH: {
        path: 160 if path in {"docs/governance/preflights/issue-397.json",
                             "tests/unit/test_guardrails_check.py"}
        else 100 if path == "scripts/guardrails_check.py"
        else 10 if path == "docs/agent-context/context-policy-manifest-v1.json" else 80
        for path in ROUTES[ISSUE397_BRANCH]
    },
    ISSUE393_BRANCH: {
        path: 180 if path.endswith(("issue-393.json", "issue-396.json"))
        else 160 if path == "tests/unit/test_stage8_quality_gate.py"
        else 80 if path in {"scripts/quality/stage8_cut1_routes.py", "tests/unit/test_stage8_cut1_routes.py",
                            "tests/unit/test_dependency_security_contract.py",
                            "scripts/ci/check_container_scan_consensus.py",
                            "tests/unit/test_container_scan_consensus.py"} else 40
        for path in ROUTES[ISSUE393_BRANCH]
    },
}


ISSUE424_HEADINGS = (
    "1. Purpose, claims, and execution authority",
    "2. Capability and evidence classification",
    "3. Stale-plan and route enforcement",
    "4. Cut1AuthorityManifestV1",
    "5. Planning and delivery layers",
    "6. Roles and separation of duties",
    "7. Intended-versus-implemented baseline",
    "8. Architecture and living documentation",
    "9. Project requirements intake",
    "10. Composition and provider resolution",
    "11. Provider-neutral contracts",
    "12. Credentials and BYOK",
    "13. Provider governance",
    "14. Provider switching and migration",
    "15. Product AI workflow",
    "16. RAG and knowledge portability",
    "17. Run lineage",
    "18. Observability and NFR controls",
    "19. Controlled feedback and learning",
    "20. Serialized Cut 1 route",
    "21. Canonical Meera narration and audio",
    "22. Meera asset authority",
    "23. Media calibration",
    "24. Renderer prequalification",
    "25. Audition fixture and scoring",
    "26. Winner lock",
    "27. PaidOperationV1",
    "28. ArtifactStore and MediaValidator",
    "29. Cut1VisualArtifactAcceptanceV1",
    "30. Independent full renders",
    "31. Captions",
    "32. Cut1RealMediaAcceptanceV1",
    "33. Disclosure policy",
    "34. UI and browser acceptance",
    "35. Required negative tests",
    "36. Task resource ledger",
    "37. Docker, temporary-file, and process hygiene",
    "38. Git, main synchronization, and branch cleanup",
    "39. End-of-process closeout verification",
    "40. Mandatory plain-English handoff",
    "41. Completion claims",
    "42. Final pre-log review gate",
)
ISSUE424_CONTROLLER_SHA256 = "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
ISSUE424_CONTROLLER_BYTES = 40135
ISSUE424_CONTROLLER_LINES = 887
ISSUE424_CONTROLLER_HAS_TRAILING_NEWLINE = True
ISSUE424_BINDING_FIELDS = {
    "schemaVersion", "controllerId", "controllerIssue", "bootstrapBranch", "acceptedBaseSha",
    "documentPath", "documentSha256", "documentBytes", "documentLines", "hasTrailingNewline",
    "numberedSections", "firstNumberedSection", "lastNumberedSection", "proposalState",
    "implementationAuthority", "activeProgramRoute", "requiredReviews", "requiredApprovals",
    "predecessor", "authorityTransition", "prohibitedClaims", "routeActivationGuard",
}
ISSUE424_REVIEWS = [
    {"id": "execution-specification", "artifact": "docs/reviews/ISSUE_424_EXECUTION_SPEC_REVIEW.md",
     "state": "PENDING_INDEPENDENT_REVIEW"},
    {"id": "cut1-false-success-media", "artifact": "docs/reviews/ISSUE_424_CUT1_FALSE_SUCCESS_REVIEW.md",
     "state": "PENDING_INDEPENDENT_REVIEW"},
    {"id": "platform-security-learning", "artifact": "docs/reviews/ISSUE_424_PLATFORM_SECURITY_LEARNING_REVIEW.md",
     "state": "PENDING_INDEPENDENT_REVIEW"},
]
ISSUE424_APPROVALS = {
    "ownerExactBytes": "PENDING", "eligibleNonAuthorExactHead": "PENDING",
    "referenceOnlyMergeWording": "PENDING",
}
ISSUE424_TRANSITION = {
    "decisionSchemaVersion": "MasterProgramAuthorityDecisionV1",
    "decisionPath": "docs/governance/narratwin-master-program-authority-decision-v1.json",
    "createdBy": "separately-governed authority-reconciliation-and-stale-route-enforcement child",
    "requiredDecisionStateForActivation": "ACCEPTED",
    "requiredEvidence": [
        "controllerProposalSha256", "exactHeadSha", "ownerExactBytesApproval",
        "independentReviewDispositions", "eligibleNonAuthorApproval", "mergeSha",
        "mergedMainChecks", "statusReconciliation", "issueDisposition", "authorityState",
        "verificationState", "expiryOrRevalidation",
    ],
    "routeActivationFromProposal": "PROHIBITED",
}
ISSUE424_PREDECESSOR = {
    "issue": 421, "pullRequest": 422,
    "reviewedHeadSha": "f68c87c6e82715a903666db13a39131b806837c7",
    "mergeSha": ISSUE424_BASE,
    "treeSha": "9c5aa188c84757db9b2c851fc11ab77d503200fe",
    "mergedMainRun": 31593554541, "mergedMainRunConclusion": "SUCCESS",
    "issueDisposition": "CLOSED_COMPLETED",
}
ISSUE424_PROHIBITED_CLAIMS = [
    "Cut1DemoCompleteV1", "CUT1_REAL_MEDIA_ACCEPTED", "full plug-and-play",
    "hosted operation", "production durability", "production readiness",
    "public availability", "release",
]
ISSUE424_ROUTE_GUARD = (
    "This proposal never grants execution authority. A current ACCEPTED "
    "MasterProgramAuthorityDecisionV1 created by the separately governed "
    "authority-reconciliation and stale-route-enforcement child is required before any "
    "implementation route may activate."
)


class DuplicateJsonMember(ValueError):
    """Reject authority bytes whose meaning depends on parser key precedence."""


def load_json_without_duplicate_members(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJsonMember(key)
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )


def security_preflight_failures(root: Path, issue: int) -> list[str]:
    path = root / f"docs/governance/preflights/issue-{issue}.json"
    schema, expected_sha = SECURITY_PREFLIGHTS[issue]
    try:
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 65536:
            raise ValueError("preflight must be a bounded regular file")
        payload = path.read_bytes()
        artifact = load_json_without_duplicate_members(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateJsonMember, ValueError):
        return [f"Issue #{issue} security preflight is malformed or unreadable."]
    failures: list[str] = []
    if hashlib.sha256(payload).hexdigest() != expected_sha:
        failures.append(f"Issue #{issue} security preflight exact bytes drifted.")
    if artifact.get("schema_version") != schema:
        failures.append(f"Issue #{issue} security preflight schema drifted.")
    if artifact.get("issue_number") != issue or artifact.get("branch") not in ROUTES:
        failures.append(f"Issue #{issue} security preflight identity drifted.")
    scope = artifact.get("scope")
    required = scope.get("required") if isinstance(scope, dict) else None
    forbidden = scope.get("forbidden") if isinstance(scope, dict) else None
    expected = ROUTES[ISSUE150_BRANCH if issue == 150 else ISSUE428_BRANCH]
    if not isinstance(required, list) or set(required) != expected or len(required) != len(expected):
        failures.append(f"Issue #{issue} security preflight scope drifted.")
    if not isinstance(forbidden, list) or any(
        path == rule or (isinstance(rule, str) and rule.endswith("/") and path.startswith(rule))
        for path in expected for rule in (forbidden if isinstance(forbidden, list) else [])
    ):
        failures.append(f"Issue #{issue} security preflight forbidden scope conflicts.")
    return failures


def issue424_governance_failures(root: Path) -> list[str]:
    """Validate the exact controller proposal without network or mutable external state."""
    failures: list[str] = []
    controller_path = root / "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
    binding_path = root / "docs/governance/narratwin-master-program-v1.json"
    preflight_path = root / "docs/governance/preflights/issue-424.json"
    try:
        controller_bytes = controller_path.read_bytes()
        controller = controller_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return ["Issue #424 controller bytes are unavailable or invalid UTF-8."]
    headings = tuple(re.findall(r"^## ([0-9]+\. .+)$", controller, flags=re.MULTILINE))
    if headings != ISSUE424_HEADINGS:
        failures.append("Issue #424 numbered heading order/titles differ from the exact 42-section contract.")
    if "exact waist-up derivative path and SHA-256" not in controller:
        failures.append("Issue #424 controller omits the exact waist-up derivative path and SHA-256 invariant.")
    actual_fingerprint = (
        hashlib.sha256(controller_bytes).hexdigest(),
        len(controller_bytes),
        len(controller_bytes.splitlines()),
        controller_bytes.endswith(b"\n"),
    )
    expected_fingerprint = (
        ISSUE424_CONTROLLER_SHA256,
        ISSUE424_CONTROLLER_BYTES,
        ISSUE424_CONTROLLER_LINES,
        ISSUE424_CONTROLLER_HAS_TRAILING_NEWLINE,
    )
    if actual_fingerprint != expected_fingerprint:
        failures.append("Issue #424 pinned controller fingerprint is inconsistent.")

    try:
        binding = load_json_without_duplicate_members(binding_path)
    except DuplicateJsonMember:
        return failures + ["Issue #424 proposal binding contains a duplicate JSON member."]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return failures + ["Issue #424 proposal binding is unavailable or invalid JSON."]
    if not isinstance(binding, dict):
        return failures + ["Issue #424 proposal binding must be a JSON object."]
    unknown = sorted(set(binding) - ISSUE424_BINDING_FIELDS)
    missing = sorted(ISSUE424_BINDING_FIELDS - set(binding))
    if unknown:
        failures.append(f"Issue #424 unknown binding field: {unknown[0]}")
    if missing:
        failures.append(f"Issue #424 missing binding field: {missing[0]}")
    expected_scalars = {
        "schemaVersion": "MasterProgramProposalBindingV1",
        "controllerId": "narratwin-authoritative-master-program-v1",
        "controllerIssue": 424,
        "bootstrapBranch": ISSUE424_BRANCH,
        "acceptedBaseSha": ISSUE424_BASE,
        "documentPath": "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md",
        "documentSha256": ISSUE424_CONTROLLER_SHA256,
        "documentBytes": ISSUE424_CONTROLLER_BYTES,
        "documentLines": ISSUE424_CONTROLLER_LINES,
        "hasTrailingNewline": ISSUE424_CONTROLLER_HAS_TRAILING_NEWLINE,
        "numberedSections": len(ISSUE424_HEADINGS),
        "firstNumberedSection": ISSUE424_HEADINGS[0],
        "lastNumberedSection": ISSUE424_HEADINGS[-1],
        "proposalState": "PROPOSED",
        "implementationAuthority": "NONE",
        "activeProgramRoute": None,
    }
    labels = {
        "documentSha256": "SHA-256", "documentBytes": "byte count",
        "documentLines": "line count", "hasTrailingNewline": "trailing-newline state",
        "acceptedBaseSha": "accepted base", "bootstrapBranch": "branch",
        "proposalState": "proposal state", "implementationAuthority": "implementation authority",
        "activeProgramRoute": "active route",
    }
    for field, expected in expected_scalars.items():
        if binding.get(field) != expected:
            failures.append(f"Issue #424 binding {labels.get(field, field)} is inconsistent.")
    if binding.get("requiredReviews") != ISSUE424_REVIEWS:
        failures.append("Issue #424 binding review contract is inconsistent.")
    if binding.get("requiredApprovals") != ISSUE424_APPROVALS:
        failures.append("Issue #424 binding approval contract is inconsistent.")
    if binding.get("authorityTransition") != ISSUE424_TRANSITION:
        failures.append("Issue #424 separate authority decision transition is inconsistent.")
    if binding.get("predecessor") != ISSUE424_PREDECESSOR:
        failures.append("Issue #424 binding predecessor evidence is inconsistent.")
    if binding.get("prohibitedClaims") != ISSUE424_PROHIBITED_CLAIMS:
        failures.append("Issue #424 binding prohibited-claim contract is inconsistent.")
    if binding.get("routeActivationGuard") != ISSUE424_ROUTE_GUARD:
        failures.append("Issue #424 binding route-activation guard is inconsistent.")
    decision_path = str(ISSUE424_TRANSITION["decisionPath"])
    if decision_path == binding.get("documentPath") or (root / decision_path).exists():
        failures.append("Issue #424 separate authority decision record must not be this proposal or exist in this PR.")

    try:
        preflight = load_json_without_duplicate_members(preflight_path)
    except DuplicateJsonMember:
        failures.append("Issue #424 preflight contains a duplicate JSON member.")
        preflight = None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        preflight = None
    findings = validate_governance_preflight(
        preflight,
        context={"issue_number": 424, "branch": ISSUE424_BRANCH,
                 "changed_files": sorted(ROUTES[ISSUE424_BRANCH])},
    )
    if findings:
        codes = ", ".join(finding.code for finding in findings)
        failures.append(f"Issue #424 GovernancePreflightV1 failed closed: {codes}")
    return failures


def parse_paths_z(output: str) -> list[str]:
    if not output:
        return []
    if not output.endswith("\0"):
        raise RuntimeError("Malformed NUL-delimited Git path output.")
    paths = output[:-1].split("\0")
    if any(not path for path in paths):
        raise RuntimeError("Malformed empty Git path.")
    return paths


def parse_name_status_z(output: str) -> list[str]:
    fields = parse_paths_z(output)
    paths: list[str] = []
    index = 0
    while index < len(fields):
        status_value = fields[index]
        index += 1
        if status_value in {"A", "B", "D", "M", "T", "U"}:
            arity = 1
        elif re.fullmatch(r"[RC]\d{1,3}", status_value) and int(status_value[1:]) <= 100:
            arity = 2
        else:
            raise RuntimeError(f"Malformed Git name-status record: {status_value!r}")
        record_paths = fields[index : index + arity]
        if len(record_paths) != arity:
            raise RuntimeError(f"Incomplete Git name-status record: {status_value!r}")
        paths.extend(record_paths)
        index += arity
    return paths


def route_base(run: Callable[[list[str]], Any], branch: str) -> str:
    fixed_routes = {
        ISSUE150_BRANCH: (150, ISSUE150_BASE),
        ISSUE424_BRANCH: (424, ISSUE424_BASE),
        ISSUE421_BRANCH: (421, ISSUE421_BASE),
        ISSUE368_IMPLEMENTATION_BRANCH: (368, ISSUE368_IMPLEMENTATION_BASE),
        ISSUE368_QUOTA_FIX_BRANCH: (368, ISSUE368_QUOTA_FIX_BASE),
        ISSUE368_PROMPT_BRANCH: (368, ISSUE368_PROMPT_BASE),
        ISSUE368_BRANCH: (368, ISSUE368_BASE),
        ISSUE386_BRANCH: (386, ISSUE386_BASE),
        ISSUE415_CORRECTION_BRANCH: (415, "20c1f4f19ee20e613f87bbfa6339f17ebb0ad205"),
    }
    if branch in fixed_routes:
        issue, base = fixed_routes[branch]
        fixed = run(["git", "rev-parse", f"{base}^{{commit}}"])
        common = run(["git", "merge-base", base, "HEAD"])
        fixed_value = str(fixed.stdout).strip()
        common_value = str(common.stdout).strip()
        branch_point_invalid = False
        if branch in {ISSUE150_BRANCH, ISSUE424_BRANCH, ISSUE421_BRANCH, ISSUE368_IMPLEMENTATION_BRANCH,
                      ISSUE368_QUOTA_FIX_BRANCH, ISSUE368_BRANCH,
                      ISSUE368_PROMPT_BRANCH}:
            branch_point = run(["git", "merge-base", "origin/main", "HEAD"])
            branch_point_invalid = branch_point.returncode != 0 or str(branch_point.stdout).strip() != base
        if (fixed.returncode or common.returncode or fixed_value != base or common_value != base
                or branch_point_invalid):
            raise RuntimeError(f"Issue #{issue} fixed base evidence is unavailable or inconsistent.")
        return base
    current = run(["git", "rev-parse", "origin/main^{commit}"])
    common = run(["git", "merge-base", "origin/main", "HEAD"])
    current_value = str(current.stdout).strip()
    common_value = str(common.stdout).strip()
    if current.returncode or common.returncode or not re.fullmatch(r"[0-9a-f]{40}", current_value):
        raise RuntimeError("Cut 1 current main evidence is unavailable.")
    if common_value != current_value:
        raise RuntimeError("Cut 1 route does not descend from current main.")
    return current_value


def route_text_charges(
    run: Callable[[list[str]], Any], base: str, paths: set[str]
) -> tuple[int, dict[str, int]]:
    ordered = sorted(paths)
    untracked = run(["git", "ls-files", "-z", "--others", "--exclude-standard", "--", *ordered])
    if untracked.returncode:
        raise RuntimeError(untracked.stderr.strip() or "Route untracked-text evidence failed.")
    if untracked.stdout:
        found = parse_paths_z(untracked.stdout)
        raise RuntimeError(f"Route required text path is untracked: {found[0]}")
    snapshots: list[dict[str, int]] = []
    for cached in (True, False):
        charges: dict[str, int] = {}
        for path in ordered:
            args = ["git", "diff"] + (["--cached"] if cached else [])
            result = run([*args, "--numstat", "--no-renames", base, "--", path])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Route charged-line evidence failed.")
            rows = result.stdout.splitlines()
            if len(rows) > 1:
                raise RuntimeError("Route charged-line evidence contains an unexpected path.")
            if not rows:
                continue
            fields = rows[0].split("\t")
            if len(fields) != 3 or fields[2] != path:
                raise RuntimeError("Route charged-line evidence contains an unexpected path.")
            if not fields[0].isdigit() or not fields[1].isdigit():
                raise RuntimeError("Route charged-line evidence is malformed or binary.")
            charges[path] = int(fields[0]) + int(fields[1])
        snapshots.append(charges)
    all_paths = set().union(*snapshots)
    return max(sum(snapshot.values()) for snapshot in snapshots), {
        path: max(snapshot.get(path, 0) for snapshot in snapshots) for path in all_paths
    }


def cut1_transition_charges(
    run: Callable[[list[str]], Any], base: str, _paths: set[str]
) -> tuple[int, dict[str, int]]:
    merge = run(["git", "merge-base", base, "HEAD"])
    if merge.returncode or merge.stdout.strip() != base:
        raise RuntimeError("Issue #366 base diff unavailable.")
    results = (
        run(["git", "diff", "--cached", "--numstat", base, "--"]),
        run(["git", "diff", "--numstat", base, "--"]),
    )
    if any(result.returncode for result in results):
        raise RuntimeError("Issue #366 base diff unavailable.")
    try:
        charges = [
            {path: int(added) + int(deleted) for added, deleted, path in
             (line.split("\t") for line in result.stdout.splitlines())}
            for result in results
        ]
    except ValueError as error:
        raise RuntimeError("Issue #366 malformed or binary numstat.") from error
    charged_paths = set().union(*charges)
    return max(sum(snapshot.values()) for snapshot in charges), {
        path: max(snapshot.get(path, 0) for snapshot in charges) for path in charged_paths
    }


def route_binary_sizes(root: Path, paths: set[str]) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for path in sorted(paths):
        target = root / path
        try:
            metadata = target.lstat()
        except FileNotFoundError as error:
            raise RuntimeError(f"Route binary is missing: {path}") from error
        if target.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"Route binary must be a regular non-symlink file: {path}")
        if metadata.st_size <= 0:
            raise RuntimeError(f"Route binary is empty: {path}")
        sizes[path] = metadata.st_size
    return sizes


def check_exact_route(
    root: Path, run: Callable[[list[str]], Any], branch: str, changed: set[str], failures: list[str]
) -> None:
    if branch not in ROUTES:
        return
    issue = ROUTE_ISSUES[branch]
    files = ROUTES[branch]
    failures.extend(f"Issue #{issue} route is missing required path: {path}" for path in sorted(files - changed))
    if branch == ISSUE150_BRANCH:
        failures.extend(security_preflight_failures(root, 150))
        failures.extend(security_preflight_failures(root, 428))
    elif branch == ISSUE428_BRANCH:
        failures.extend(security_preflight_failures(root, 428))
    if branch == ISSUE424_BRANCH:
        failures.extend(issue424_governance_failures(root))
    try:
        base = route_base(run, branch)
        total, charges = route_text_charges(run, base, set(TEXT_LIMITS[branch]))
        if total > TOTAL_LIMITS[branch]:
            failures.append(f"Issue #{issue} charge {total} exceeds {TOTAL_LIMITS[branch]}.")
        failures.extend(
            f"Issue #{issue} charge for {path} exceeds {limit}."
            for path, limit in TEXT_LIMITS[branch].items() if charges.get(path, 0) > limit
        )
        if branch == ISSUE383_BRANCH:
            sizes = route_binary_sizes(root, ISSUE383_BINARY_FILES)
            failures.extend(
                f"Issue #383 binary {path} exceeds 500000 bytes."
                for path, size in sizes.items() if size > 500000
            )
    except RuntimeError as error:
        failures.append(f"Issue #{issue} route evidence failed closed: {error}")
