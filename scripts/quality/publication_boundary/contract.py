"""Strict, bounded PublicationBoundaryV1 parsing and compilation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


CONTRACT_PATH = "docs/governance/publication-boundary-v1.json"
MAX_CONTRACT_BYTES = 32_768
PUBLIC_STATEMENT = (
    "NarraTwin turns approved knowledge into grounded, cited, multilingual avatar "
    "explanations and interactive Q&A."
)
AUTHORITY_ORDER = [
    "OWNER_APPROVED_ISSUE_324",
    "VERSIONED_PUBLICATION_CONTRACT",
    "CANONICAL_MERGED_PRODUCT_SOURCES",
    "EXECUTABLE_GATES_AND_TESTS",
    "RUNTIME_EVIDENCE",
    "HISTORICAL_RECORDS_CONTEXT_ONLY",
]
CLASS_ROWS = [
    {
        "id": "PUBLIC",
        "destination": "APPROVED_PUBLIC_SURFACE",
        "defaultAction": "VALIDATE_THEN_ALLOW",
    },
    {
        "id": "INTERNAL",
        "destination": "EXTERNAL_ACCESS_CONTROLLED_SYSTEM",
        "defaultAction": "OMIT_OR_REDACT",
    },
    {
        "id": "RESTRICTED",
        "destination": "APPROVED_RESTRICTED_SYSTEM",
        "defaultAction": "BLOCK",
    },
]
SURFACE_ORDER = [
    "CANONICAL_DOCUMENTS",
    "USER_INTERFACE_COPY",
    "API_FIXTURES_RESPONSES",
    "GENERATED_SCRIPTS_CAPTIONS_DOWNLOADS",
    "ARTIFACT_MANIFESTS_MEDIA_METADATA",
    "FILENAMES_URLS",
    "SCREENSHOTS_RELEASE_MATERIAL",
    "LOGS_TRACES",
    "SEARCH_QUERIES",
    "PROVIDER_REQUEST_METADATA",
    "PROMPTS_MODEL_OUTPUT",
    "RETRIEVED_CONTEXT",
]
SURFACE_ROWS = [
    {
        "id": surface,
        "defaultClassification": "INTERNAL",
        "publicAction": "VALIDATE",
    }
    for surface in SURFACE_ORDER
]
PROMOTION_RULES = {
    "unknownClassAction": "BLOCK",
    "mixedClassAction": "MOST_RESTRICTIVE",
    "promptMayReclassify": False,
    "retrievalMayReclassify": False,
    "modelMayReclassify": False,
    "providerMayReclassify": False,
    "humanApprovalRequired": True,
}
CANONICAL_PUBLIC_SOURCES = [
    "README.md",
    "docs/AI_BUILD_BRIEF.md",
    "docs/PRODUCT_STRATEGY.md",
    "docs/PRD.md",
    "docs/demo/CONTROLLED_LOCAL_DEMO.md",
]
LEGACY_REPLACEMENT = {
    "activePath": "docs/demo/CONTROLLED_LOCAL_DEMO.md",
    "removedPath": "portfolio/README.md",
    "historicalReferences": "PRESERVE_WITH_CONTEXT",
}
LAUNCH_POSTURE = {
    "publicationIsReleaseAuthorization": False,
    "publicDistributionAuthorized": False,
    "productionAuthorized": False,
}
TOP_LEVEL_FIELDS = {
    "schemaVersion",
    "publicProductStatement",
    "authorityOrder",
    "classes",
    "surfaceFamilies",
    "promotionRules",
    "canonicalPublicSources",
    "legacyReplacement",
    "launchPosture",
}


@dataclass(frozen=True)
class CompiledPublicationPolicy:
    """Closed values consumed by the decision engine after full validation."""

    schema_version: str
    authority_order: tuple[str, ...]
    class_ids: tuple[str, ...]
    surface_ids: frozenset[str]
    human_approval_required: bool


class DuplicateKeyError(ValueError):
    """Raised when JSON tries to mimic a valid object with a duplicate key."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def validate_contract_text(
    source: str,
) -> tuple[CompiledPublicationPolicy | None, list[str]]:
    """Validate the complete schema and compile only an exact contract."""
    if not isinstance(source, str):
        return None, ["Publication contract must be valid UTF-8 JSON."]
    if len(source.encode("utf-8", errors="surrogatepass")) > MAX_CONTRACT_BYTES:
        return None, ["Publication contract exceeds its size limit."]
    try:
        value = json.loads(source, object_pairs_hook=_unique_object)
    except DuplicateKeyError:
        return None, ["Publication contract contains a duplicate JSON key."]
    except (json.JSONDecodeError, UnicodeError, TypeError):
        return None, ["Publication contract must be valid UTF-8 JSON."]
    if not isinstance(value, dict):
        return None, ["Publication contract must use a strict top-level schema."]

    checks = (
        (
            set(value) == TOP_LEVEL_FIELDS,
            "Publication contract must use a strict top-level schema.",
        ),
        (
            value.get("schemaVersion") == "PublicationBoundaryV1",
            "Publication contract has the wrong schema version.",
        ),
        (
            value.get("publicProductStatement") == PUBLIC_STATEMENT,
            "Publication contract has the wrong public product statement.",
        ),
        (
            value.get("authorityOrder") == AUTHORITY_ORDER,
            "Publication contract has the wrong authority order.",
        ),
        (
            value.get("classes") == CLASS_ROWS,
            "Publication contract has the wrong classification contract.",
        ),
        (
            value.get("surfaceFamilies") == SURFACE_ROWS,
            "Publication contract must contain the exact 12 surface families.",
        ),
        (
            value.get("promotionRules") == PROMOTION_RULES,
            "Publication contract has unsafe promotion rules.",
        ),
        (
            value.get("canonicalPublicSources") == CANONICAL_PUBLIC_SOURCES,
            "Publication contract has the wrong canonical public sources.",
        ),
        (
            value.get("legacyReplacement") == LEGACY_REPLACEMENT,
            "Publication contract has the wrong legacy replacement semantics.",
        ),
        (
            value.get("launchPosture") == LAUNCH_POSTURE,
            "Publication contract must preserve launch No-Go posture.",
        ),
    )
    failures = [message for passed, message in checks if not passed]
    if failures:
        return None, failures
    return (
        CompiledPublicationPolicy(
            schema_version="PublicationBoundaryV1",
            authority_order=tuple(AUTHORITY_ORDER),
            class_ids=tuple(row["id"] for row in CLASS_ROWS),
            surface_ids=frozenset(SURFACE_ORDER),
            human_approval_required=True,
        ),
        [],
    )
