import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


def load_branch_protection_module() -> ModuleType:
    module_path = Path(__file__).parents[2] / "scripts" / "ci" / "verify_branch_protection.py"
    spec = importlib.util.spec_from_file_location("branch_protection_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verify_branch_protection: Any = load_branch_protection_module()

HISTORICAL_CONTEXTS = (
    "policy-gates",
    "quality / secrets",
    "quality / markdown",
    "lint / typecheck / unit / api",
    "frontend tests / playwright smoke",
    "ci / docker build",
    "secret scan / bandit / audit / semgrep",
    "security / docker build",
    "eval smoke",
    "stage8 / performance lighthouse",
)
EXPECTED_CONTEXTS = (*HISTORICAL_CONTEXTS, "pr-body-consistency")


def protected_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "protected": True,
        "protection": {
            "enabled": True,
            "required_status_checks": {
                "strict": True,
                "enforcement_level": "everyone",
                "contexts": list(verify_branch_protection.EXPECTED_CONTEXTS),
                "checks": [
                    {
                        "context": context,
                        "app_id": verify_branch_protection.GITHUB_ACTIONS_APP_ID,
                    }
                    for context in verify_branch_protection.EXPECTED_CONTEXTS
                ],
            },
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "dismiss_stale_reviews": True,
                "require_last_push_approval": True,
            },
            "enforce_admins": {"enabled": True},
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
            "required_conversation_resolution": {"enabled": True},
        },
    }
    payload.update(overrides)
    return payload


def status_checks(payload: dict[str, object]) -> dict[str, object]:
    protection = payload["protection"]
    assert isinstance(protection, dict)
    checks = protection["required_status_checks"]
    assert isinstance(checks, dict)
    return checks


def payload_with_contexts(contexts: tuple[str, ...]) -> dict[str, object]:
    payload = protected_payload()
    checks = status_checks(payload)
    checks["contexts"] = list(contexts)
    checks["checks"] = [
        {"context": context, "app_id": 15368}
        for context in contexts
    ]
    return payload


def test_branch_protection_expected_contexts_are_exactly_the_live_eleven() -> None:
    assert verify_branch_protection.EXPECTED_CONTEXTS == EXPECTED_CONTEXTS


def test_branch_protection_verifier_accepts_exact_live_eleven_contexts() -> None:
    assert verify_branch_protection.validate(payload_with_contexts(EXPECTED_CONTEXTS)) == []


def test_branch_protection_verifier_rejects_missing_pr_body_consistency() -> None:
    failures = verify_branch_protection.validate(payload_with_contexts(HISTORICAL_CONTEXTS))

    assert "required status checks missing contexts: pr-body-consistency." in failures


def test_branch_protection_verifier_rejects_wrong_pr_body_consistency_app() -> None:
    payload = payload_with_contexts(EXPECTED_CONTEXTS)
    bindings = status_checks(payload)["checks"]
    assert isinstance(bindings, list)
    bindings[-1] = {"context": "pr-body-consistency", "app_id": 1}

    failures = verify_branch_protection.validate(payload)

    assert (
        "required status checks must bind to the GitHub Actions app "
        "(15368); mismatched contexts: pr-body-consistency."
    ) in failures


def test_branch_protection_verifier_rejects_unexpected_twelfth_context() -> None:
    failures = verify_branch_protection.validate(
        payload_with_contexts((*EXPECTED_CONTEXTS, "unexpected / bypass"))
    )

    assert "required status checks include unexpected contexts: unexpected / bypass." in failures
    assert "required status check bindings include unexpected contexts: unexpected / bypass." in failures


def test_branch_protection_verifier_rejects_removal_of_each_historical_context() -> None:
    for removed in HISTORICAL_CONTEXTS:
        contexts = tuple(context for context in EXPECTED_CONTEXTS if context != removed)

        failures = verify_branch_protection.validate(payload_with_contexts(contexts))

        assert f"required status checks missing contexts: {removed}." in failures
        assert f"required status check bindings missing contexts: {removed}." in failures


def test_branch_protection_verifier_rejects_duplicate_contexts_and_bindings() -> None:
    duplicate_context = payload_with_contexts((*EXPECTED_CONTEXTS, "pr-body-consistency"))
    failures = verify_branch_protection.validate(duplicate_context)
    assert "required status checks contexts must contain exactly eleven unique entries." in failures
    assert "required status check bindings must contain exactly eleven unique entries." in failures


def test_branch_protection_verifier_rejects_missing_or_malformed_check_bindings() -> None:
    missing = protected_payload()
    status_checks(missing).pop("checks")
    assert (
        "branch summary must expose required_status_checks.checks bindings."
        in verify_branch_protection.validate(missing)
    )

    malformed = protected_payload()
    status_checks(malformed)["checks"] = ["not-a-binding"]
    failures = verify_branch_protection.validate(malformed)
    assert "required status check bindings must be context/app_id objects." in failures


def test_branch_protection_verifier_accepts_full_required_protection() -> None:
    assert verify_branch_protection.validate(protected_payload()) == []


def test_branch_protection_verifier_rejects_context_only_payload() -> None:
    payload = protected_payload()
    protection = payload["protection"]
    assert isinstance(protection, dict)
    protection.pop("required_pull_request_reviews")
    protection.pop("enforce_admins")
    protection.pop("allow_force_pushes")
    protection.pop("allow_deletions")
    protection.pop("required_conversation_resolution")

    failures = verify_branch_protection.validate(payload)

    assert "required pull request review must be enabled." in failures
    assert "administrator enforcement must be enabled." in failures
    assert "force pushes must be blocked." in failures
    assert "branch deletions must be blocked." in failures
    assert "conversation resolution must be required." in failures


def test_branch_protection_verifier_treats_permission_limited_details_as_human_only() -> None:
    payload = protected_payload(protection_details_unavailable="HTTP 403 Resource not accessible")
    protection = payload["protection"]
    assert isinstance(protection, dict)
    protection.pop("required_pull_request_reviews")
    protection.pop("enforce_admins")
    protection.pop("allow_force_pushes")
    protection.pop("allow_deletions")
    protection.pop("required_conversation_resolution")

    assert verify_branch_protection.validate(payload) == []


def test_branch_protection_verifier_skips_missing_strict_when_detail_endpoint_is_unavailable() -> None:
    payload = protected_payload(protection_details_unavailable="HTTP 403 Resource not accessible")
    protection = payload["protection"]
    assert isinstance(protection, dict)
    status_checks = protection["required_status_checks"]
    assert isinstance(status_checks, dict)
    status_checks.pop("strict")

    assert verify_branch_protection.validate(payload) == []


def test_branch_protection_verifier_rejects_explicit_non_strict_even_when_details_unavailable() -> None:
    payload = protected_payload(protection_details_unavailable="HTTP 403 Resource not accessible")
    protection = payload["protection"]
    assert isinstance(protection, dict)
    status_checks = protection["required_status_checks"]
    assert isinstance(status_checks, dict)
    status_checks["strict"] = False

    failures = verify_branch_protection.validate(payload)

    assert "required status checks must require branches to be up to date." in failures


def test_branch_protection_verifier_rejects_non_strict_status_checks() -> None:
    payload = protected_payload()
    protection = payload["protection"]
    assert isinstance(protection, dict)
    status_checks = protection["required_status_checks"]
    assert isinstance(status_checks, dict)
    status_checks["strict"] = False

    failures = verify_branch_protection.validate(payload)

    assert "required status checks must require branches to be up to date." in failures
