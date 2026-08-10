from __future__ import annotations

import importlib.util
import hashlib
import json
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


EXPECTED = {
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
    issue368 = json.loads((REPO / "docs/governance/preflights/issue-368.json").read_text(encoding="utf-8"))
    assert issue368["branch"] == routes.ISSUE368_IMPLEMENTATION_BRANCH
    assert set(issue368["scope"]["required"]) == EXPECTED[routes.ISSUE368_IMPLEMENTATION_BRANCH]
    assert set(issue368["scope"]["allowed_prefixes"]) == EXPECTED[routes.ISSUE368_IMPLEMENTATION_BRANCH]
    assert issue368["change_budget"] == {
        "exact_paths": 21,
        "maximum_additions_plus_deletions": 5600,
        "deletions_grant_credit": False,
    }
    assert routes.TOTAL_LIMITS[routes.ISSUE368_IMPLEMENTATION_BRANCH] == 5600
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


def test_legacy_checker_caps_are_unchanged_and_executable() -> None:
    checker = REPO / "scripts/quality/check_stage8_docs.py"
    checker_text = checker.read_text(encoding="utf-8")
    assert len(checker_text.splitlines()) <= 500
    assert checker.stat().st_size <= 32_000
    assert len((REPO / "tests/unit/test_stage8_quality_gate.py").read_text(encoding="utf-8").splitlines()) <= 250
    for relative in (
        "scripts/quality/stage8_brace_expansion_unblock.py",
        "scripts/quality/stage8_cache_pruning.py",
    ):
        assert '"scripts/quality/check_stage8_docs.py": 500' in (REPO / relative).read_text(encoding="utf-8")


def test_exact_route_completeness_lookalikes_and_budgets(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_text_charges", lambda *_: (0, {}))
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES})
    for branch, paths in EXPECTED.items():
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, set(paths), failures)
        assert failures == []
        missing = sorted(paths)[0]
        failures = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, paths - {missing}, failures)
        issue = routes.ROUTE_ISSUES[branch]
        assert failures == [f"Issue #{issue} route is missing required path: {missing}"]
        confusable = (
            branch.replace("stage8", "stageв")
            if "stage8" in branch
            else branch.replace("process", "procesѕ")
        )
        for lookalike in (branch + "-retry", branch.upper(), confusable):
            failures = []
            routes.check_exact_route(REPO, lambda _: completed([]), lookalike, set(paths), failures)
            assert failures == []
            assert lookalike not in stage8.PROCESS_BRANCH_ALLOWED_FILES


def test_per_route_aggregate_per_file_and_binary_caps(monkeypatch: Any) -> None:
    monkeypatch.setattr(routes, "route_base", lambda *_: "base")
    monkeypatch.setattr(routes, "route_binary_sizes", lambda *_: {path: 1 for path in routes.ISSUE383_BINARY_FILES})
    for branch, limit in routes.TOTAL_LIMITS.items():
        monkeypatch.setattr(routes, "route_text_charges", lambda *_, value=limit: (value + 1, {}))
        failures: list[str] = []
        routes.check_exact_route(REPO, lambda _: completed([]), branch, EXPECTED[branch], failures)
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
