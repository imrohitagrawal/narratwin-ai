#!/usr/bin/env python3
"""Offline, deterministic checks for Issue #521 Master Program V2 candidate."""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, cast
try:
    from scripts.agent_context.core import validate_schema_instance
except ModuleNotFoundError:  # Direct `python scripts/quality/...py` execution.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.agent_context.core import validate_schema_instance
DOCUMENT_PATH = "docs/governance/NARRATWIN_MASTER_PROGRAM_V2.md"
BINDING_PATH = "docs/governance/narratwin-master-program-v2.json"
MAPPING_PATH = "docs/governance/superset-mapping-v2.json"
TAXONOMY_PATH = "docs/governance/cut-taxonomy-v2.json"
MAPPING_SCHEMA_PATH = "docs/governance/schemas/superset-mapping-v2.schema.json"
TAXONOMY_SCHEMA_PATH = "docs/governance/schemas/cut-taxonomy-v2.schema.json"
REVIEW_PATHS = (
    "docs/reviews/ISSUE_521_SUPERSET_SEMANTIC_REVIEW.md",
    "docs/reviews/ISSUE_521_FALSE_SUCCESS_SECURITY_REVIEW.md",
)
REQUIRED_ARTIFACTS = (
    DOCUMENT_PATH,
    BINDING_PATH,
    MAPPING_PATH,
    TAXONOMY_PATH,
    MAPPING_SCHEMA_PATH,
    TAXONOMY_SCHEMA_PATH,
    *REVIEW_PATHS,
)
BASE_SHA = "b6b0c05c7227428ff0841361f3970b0b2c40aa86"
V1_PATH = "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
V1_SHA256 = "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
DOCUMENT_SHA256 = "0b0f85e8e849cc4ce9513360d67bd8d22102b55ca39faaa075a928c6a25407ea"
EXTERNAL_CLASSIFICATION_PRECEDENCE_INPUT_SHA256 = (
    "746e23fcd200f25e1fcd91ef4dd39b59abc6e34ea00b28db7dee667da81db75f"
)
MAPPING_SHA256 = "766cbfcf6666e52cc2f158796577f797b771015716a07b4665efad7e721c2bcb"
TAXONOMY_SHA256 = "c0fba5183c284f2d8854eefb30caaf76bb2979ac00328b67ccd6d027a971cdb7"
MAPPING_SCHEMA_SHA256 = "eab8f273a9c84e9a45b492efc75f176415ea1937bf85704a31e3c5bc40cab96f"
TAXONOMY_SCHEMA_SHA256 = "7ac62fbe1a92b43eccba782038f8002818b80c9c02246f35d3f117941e69ccc8"
REVIEW_SHA256 = {
    REVIEW_PATHS[0]: "2c2b451a124728e89c55630e499660759dad5c4f0c5a775aa05661cf9273569b",
    REVIEW_PATHS[1]: "7d8f6461e1065901a057349a646e71a223c979f331db383b8fce242a7788121b",
}
EXTERNAL_AUTHORITY_MANIFEST_SHA256 = (
    "b47e111cf0af5b6fb1b09b2659d89798e4f97a241612ea1eb5da4f664f8bc7a2"
)
MAPPING_MAX_BYTES = 50 * 1024 * 1024
ROADMAP_PATH = "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md"
ROADMAP_SHA256 = "e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b"
ADR0079_PATH = "docs/ADR/0079-cut1-t06-dual-plan-video-strategy.md"
ADR0079_SHA256 = "a20ae1b9fae9e12e9e50baa372b0672c43a9417a21b36a2dc4276f5be1529fd5"
GITLEAKS_FALSE_POSITIVE_CLAUSE_SHA256 = (
    "845855204badc3593c9f4e729d2395d4c443ab2f83771cb1731f7a560f3089c1"
)
GITHUB_REPOSITORY_ID = 1_282_502_888
GITHUB_REPOSITORY = "imrohitagrawal/narratwin-ai"
OWNER_PLAN_ADOPTION_COMMENT_ID = 0
OWNER_PLAN_ADOPTION_BODY_SHA256 = "PENDING_OWNER_ADOPTION"
OWNER_PLAN_ADOPTION_DOCUMENT_SHA256 = "PENDING_OWNER_ADOPTION"
OWNER_PLAN_RESTRICTED_SOURCE_REF = "restricted-evidence:OWNER_PLAN_2026_09_07"
OWNER_PLAN_RESTRICTED_SOURCE_SHA256 = (
    "986fd1604b385cd1ecd0dad1bfe0e09e6357d0e4b1d58bc94e3c055cc9bec58c"
)
OWNER_PLAN_RESTRICTED_SOURCE_BYTES = 65_097
def _paths(prefix: str, names: str) -> tuple[str, ...]:
    return tuple(prefix + name for name in names.split())
_SPECIAL_SOURCE_IDS = {
    V1_PATH: "MASTER_PROGRAM_V1",
    ROADMAP_PATH: "FIVE_CUT_ROADMAP",
    "docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md": "CUT1_PRESENTER_CONTRACT",
    "docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md": "AI_QUALITY_CONTRACT",
    "docs/ENTERPRISE_READINESS_REGISTER.md": "ENTERPRISE_REGISTER",
    "docs/SECURITY_AND_PRIVACY.md": "SECURITY_PRIVACY",
    "docs/ARCHITECTURE.md": "ARCHITECTURE",
    "docs/STATUS.md": "STATUS",
    "docs/PHASE_PLAN.md": "PHASE_PLAN",
    "docs/STAGE_ISSUE_PLAN.md": "STAGE_ISSUE_PLAN",
    "docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md": "CUT1_ACCEPTANCE",
    ADR0079_PATH: "ADR_0079",
    "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md": "REAL_MEDIA_HOSTED_DEMO_PLAN",
    "docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md": "CUT1_T06_PROVIDER_LANDSCAPE",
    "docs/PRD.md": "PRD",
    "docs/API_CONTRACT.md": "API_CONTRACT",
    "docs/OBSERVABILITY_AND_COST.md": "OBSERVABILITY_COST",
    "docs/PORTABILITY_STRATEGY.md": "PORTABILITY",
    "backend/app/avatar_video_provider.py": "AVATAR_PROVIDER_CODE",
    "backend/app/tts_provider.py": "TTS_PROVIDER_CODE",
}
def _source_id(path: str, object_kind: str) -> str:
    special = _SPECIAL_SOURCE_IDS.get(path)
    if special is not None:
        return special
    stem = Path(path).name.rsplit(".", 1)[0]
    slug = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_").upper()
    if path.startswith("docs/ADR/"):
        return "ADR_" + slug
    prefix = "TREE" if object_kind == "GIT_TREE" else "SOURCE"
    digest = hashlib.sha256(path.encode("utf-8")).hexdigest()[:8].upper()
    return f"{prefix}_{slug}_{digest}"
def _default_destination(path: str) -> str:
    special = {
        value: destination
        for value, destination in (
            (V1_PATH, "MPV2-SECTION-1"), (ROADMAP_PATH, "MPV2-SECTION-5"),
            ("docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md", "MPV2-CUT1"),
            ("docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md", "MPV2-SECTION-11"),
            ("docs/ENTERPRISE_READINESS_REGISTER.md", "MPV2-CUT6"),
            ("docs/SECURITY_AND_PRIVACY.md", "MPV2-SECTION-11"),
            ("docs/ARCHITECTURE.md", "MPV2-SECTION-7"),
            ("docs/STATUS.md", "MPV2-SECTION-4"),
            ("docs/PHASE_PLAN.md", "MPV2-SECTION-10"),
            ("docs/STAGE_ISSUE_PLAN.md", "MPV2-SECTION-10"),
            ("docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md", "MPV2-SECTION-11"),
            (ADR0079_PATH, "MPV2-CUT4"),
            ("docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md", "MPV2-SECTION-6"),
            ("docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md", "MPV2-SECTION-7"),
            ("docs/PRD.md", "MPV2-SECTION-2"),
            ("docs/API_" "CONTRACT.md", "MPV2-SECTION-9"),
            ("docs/OBSERVABILITY_AND_COST.md", "MPV2-SECTION-8"),
            ("docs/PORTABILITY_STRATEGY.md", "MPV2-SECTION-7"),
        )
    }
    if path in special:
        return special[path]
    lowered = path.lower()
    if any(word in lowered for word in ("presenter", "avatar", "narration", "audio", "tts", "grounding")):
        return "MPV2-CUT1"
    if any(word in lowered for word in ("release", "launch", "enterprise", "slo", "runbook")):
        return "MPV2-CUT6"
    if any(word in lowered for word in ("security", "safety", "quality", "eval", "threat")):
        return "MPV2-SECTION-11"
    if any(word in lowered for word in ("authority", "program-route", "governance", "pull_request")):
        return "MPV2-SECTION-1"
    if any(word in lowered for word in ("architecture", "provider", "portability")):
        return "MPV2-SECTION-7"
    return "MPV2-SECTION-9"
_MARKDOWN_GROUPS = (
    ("ACTIVE", _paths("", """.github/pull_request_template.md docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md docs/AI_SAFETY_AND_EVALUATION.md docs/API_CONTRACT.md docs/ARCHITECTURE.md docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md docs/DATA_MODEL.md docs/ENTERPRISE_READINESS_REGISTER.md docs/LAUNCH_LEVELS.md docs/OBSERVABILITY_AND_COST.md docs/PORTABILITY_STRATEGY.md docs/PRD.md docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md docs/PUBLICATION_BOUNDARY.md docs/QUALITY_GATES.md docs/RELEASE_CHECKLIST.md docs/RELEASE_QUALITY_BAR.md docs/RELEASE_READINESS_REVIEW.md docs/REPOSITORY_GUARDRAILS.md docs/REQUIREMENTS_TRACEABILITY_MATRIX.md docs/ROADMAP.md docs/RUNBOOK.md docs/SECURITY_AND_PRIVACY.md docs/THREAT_MODEL.md docs/TRACEABILITY.md docs/demo/CUT1_ACCEPTANCE_CHECKLIST.md""")),
    ("ACCEPTED", _paths("", """docs/PROJECT_AVATAR_PACK.md docs/governance/AUTHORITY_CORE_SCHEMAS_AND_STATE_MATRICES_V1.md docs/governance/AUTHORITY_RECONCILIATION_AND_STALE_ROUTE_PHASE_SPEC_V1.md""")),
    ("MIXED", _paths("", """docs/PHASE_PLAN.md docs/STAGE_ISSUE_PLAN.md docs/STATUS.md docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md""")),
    ("NO_AUTHORITY", ("docs/governance/AUTHORITY_EVIDENCE_AND_TRUST_V1.md",)),
    ("OWNER_BASELINE", (V1_PATH,)),
)
_STRUCTURED_GROUPS = (
    ("ACTIVE", _paths("", """backend/app/presenter_registry.json docs/governance/GOVERNANCE_PREFLIGHT_V1.schema.json docs/governance/cut1-all-presenter-acceptance-matrix-v1.json docs/governance/cut1-blinded-human-evaluation-protocol-v1.json docs/governance/cut1-google-gemini-tts-style-prompts-v1.json docs/governance/cut1-presenter-derivatives-v1.json docs/governance/cut1-presenter-live-binding-v2.json docs/governance/cut1-project-facts-v1.json docs/governance/cut1-provider-bakeoff-contract-v1.json docs/governance/publication-boundary-v1.json docs/governance/schemas/cut1-controlled-presenter-evidence-v1.schema.json docs/governance/schemas/cut1-human-realism-evaluation-v1.schema.json docs/governance/schemas/cut1-presenter-provider-acceptance-v1.schema.json""")),
    ("ACCEPTED", _paths("", """docs/STAGE2_ARCHITECTURE_CONTRACT.json docs/governance/authority-core-state-matrices-v1.json docs/governance/authority-reconciliation-and-stale-route-phase-spec-v1.json docs/governance/schemas/active-program-route-v1.schema.json docs/governance/schemas/cut1-authority-manifest-v1.schema.json docs/governance/schemas/master-program-authority-decision-v1.schema.json""")),
    ("NO_AUTHORITY", _paths("", """docs/governance/adversarial-convergence-framework-v1.schema.json docs/governance/authority-evidence-trust-state-matrices-v1.json docs/governance/schemas/authority-evidence-envelope-v1.schema.json docs/governance/schemas/authority-evidence-reconstruction-v1.schema.json docs/governance/schemas/authority-producer-key-v1.schema.json docs/governance/schemas/authority-producer-trust-root-v1.schema.json""")),
    ("PROPOSED_NONACTIVATING", ("docs/governance/narratwin-master-program-v1.json",)),
)
_CODE_PATHS = _paths("", """backend/app/avatar_video_provider.py backend/app/cut1_audio.py backend/app/cut1_controlled_presenter.py backend/app/cut1_grounding.py backend/app/cut1_listening.py backend/app/evaluation_lineage.py backend/app/evaluation_lineage_state.py backend/app/google_tts_runtime.py backend/app/hosted_demo.py backend/app/main.py backend/app/narration.py backend/app/presenter_registry.py backend/app/rag/providers.py backend/app/stage4.py backend/app/stage6.py backend/app/stage7.py backend/app/storage/stage4_graph.py backend/app/tts_provider.py frontend/src/app/demo/guide-client.ts frontend/src/app/demo/page.tsx scripts/guardrails_check.py""")
_MANIFEST_BLOB_GROUPS = (
    ("ACCEPTED", ("docs/THIRD_PARTY_NOTICES.md",)),
    ("EVIDENCE", _paths("", """docs/EVAL_REPORT.md docs/governance/ISSUE_434_AUTHORITY_EVIDENCE_TRUST_SOURCE_FACTS.md docs/governance/ISSUE_459_CONTROLLED_PRESENTER_PREFLIGHT_V1.md docs/governance/adversarial-convergence-framework-cases-v1.json docs/governance/adversarial-convergence-red-freeze-v1.json docs/governance/cut1-controlled-presenter-red-corpus-v1.json docs/governance/cut1-presenter-contract-red-freeze-v1.json""")),
    ("HISTORICAL", _paths("", """docs/demo/CHECKPOINT3A_FULL_PROJECT_MULTILINGUAL_REHEARSAL_CHECKLIST.md docs/demo/CHECKPOINT3A_MULTILINGUAL_REHEARSAL_CHECKLIST.md docs/demo/CHECKPOINT3A_R3_REHEARSAL_CHECKLIST.md docs/demo/CONTROLLED_LOCAL_DEMO.md docs/demo/PHASE_1_DEMO_CHECKLIST.md docs/demo/PHASE_1_DEMO_SCRIPT.md docs/demo/PHASE_1_SCREENSHOT_GUIDE.md""")),
)
_TREE_GROUPS = (
    ("ACCEPTED", (".github/ISSUE_TEMPLATE",)),
    ("EVIDENCE", _paths("", """.github/workflows docs/evals docs/governance/preflights frontend/public/demo tests""")),
    ("HISTORICAL", ("docs/reviews",)),
    ("SHADOW", ("docs/agent-context",)),
)
_ADR_ATOMIC_GROUPS = (
    ("ACTIVE", _paths("docs/ADR/", """0002-provider-agnostic-adapters.md 0004-avatar-provider-adapter.md 0005-observability-and-evals.md 0006-stage8-release-hardening.md 0019-ch16-consent-capture.md 0024-ch10-production-metrics-contract.md 0025-ch11-slo-error-budget.md 0040-pr-body-live-state-reconciliation.md 0044-issue280-repair-architecture-feasibility.md 0047-publication-boundary.md 0048-cut1-presenter-enterprise-readiness-contracts.md 0054-cut1-presenter-registry.md 0055-cut1-narration-speech-lock.md 0056-cut1-google-gemini-tts.md 0058-cut1-atomic-project-facts-grounding.md 0065-cut1-all-presenter-acceptance-provider-bakeoff.md 0066-cut1-presenter-live-binding-v2.md 0068-cut1-controlled-presenter-controller.md 0069-cut1-presenter-derivative-readiness-binding.md 0070-cut1-t05-grounded-narration-handoff.md 0071-cut1-audio-caption-authority.md 0072-cut1-presenter-source-integrity.md 0073-cut1-exact-hash-listening-authority.md 0078-cut1-configurable-audio-duration.md""")),
    ("ACCEPTED", _paths("docs/ADR/", """0000-adr-process.md 0001-system-architecture.md 0002-rag-storage.md 0003-llm-provider-routing.md 0007-local-principal-contract.md 0013-ch01-migration-baseline-runner.md 0014-ch02-acid-cas-storage-kernel.md 0015-ch04-idempotency-semantics.md 0016-ch05-lease-fencing.md 0017-ch06-committed-outbox.md 0018-ch03-stage4-durable-graph.md 0020-ch07-stage6-durable-replay.md 0021-ch08-stage7-render-artifact-state.md 0022-ch09-technical-rollback-compatibility.md 0023-local-restore-integrity-drill.md 0026-ch14-restore-readiness-contract.md 0028-local-lighthouse-browser-selection.md 0029-ch-m1-02-real-stack-evidence.md 0030-mode1-stage6-stage7-bundle-binding.md 0032-local-demo-refusal-ux-boundary.md 0033-checkpoint3-real-browser-acceptance-evidence.md 0034-c3a-r2-full-project-multilingual-gate.md 0043-heartbeat2-curated-reviewer-demo.md 0045-issue280-semantic-repair-slice1.md 0048-quiet-presence-embedded-guide.md 0060-authority-reconciliation-and-stale-route-phase-spec.md 0061-core-authority-schemas-state-matrices.md""")),
    ("NO_AUTHORITY", (ADR0079_PATH,)),
    ("PROPOSED_BLOCKED", ("docs/ADR/0027-production-like-durability-platform-ownership.md",)),
    ("PROPOSED_NONACTIVATING", ("docs/ADR/0059-master-program-authority-and-route-bootstrap.md",)),
)
_ADR_MANIFEST_GROUPS = (
    ("ADVISORY_ONLY", _paths("docs/ADR/", """0008-postgresql-durability-schema-boundary.md 0009-context2-idempotency-lease-outbox-contract.md 0010-context3-migrations-rollback-compatibility.md 0011-context4-backup-restore-drill.md 0012-context5-metrics-slos-watch.md""")),
    ("HISTORICAL", _paths("docs/ADR/", """0031-frontend-lighthouse-audit-remediation.md 0035-issue280-input-api-error-contract.md 0036-issue280-local-e2e-demo-slice.md 0037-issue280-ui-browser-demo-slice.md 0037-postcss-audit-remediation.md 0038-issue280-pr-e-local-demo-closure-contract.md 0039-frontend-brace-expansion-audit-remediation.md 0040-heartbeat1-a1-curated-eligibility.md 0041-heartbeat1-a2-exclusion-summary.md 0042-heartbeat1-b-browser-reopen-evidence.md 0049-semgrep-cryptography-50-lock-refresh.md 0050-brace-expansion-5-0-9-security-refresh.md 0051-js-yaml-4-3-1-security-refresh.md 0062-nanoid-3-3-18-security-refresh.md 0069-semgrep-1-175-override-removal.md 0074-browserslist-4-28-8-security-refresh.md 0075-pypdf-6-16-2-security-refresh.md 0077-frontend-musl-scratch-runtime.md""")),
    ("NO_AUTHORITY", _paths("docs/ADR/", """0063-authority-evidence-and-trust.md 0064-adversarial-convergence-protocol.md""")),
    ("SHADOW", ("docs/ADR/0046-agent-context-shadow-architecture.md",)),
    ("SUPERSEDED", _paths("docs/ADR/", """0001-architecture-approach.md 0003-free-mode-vs-premium-mode.md 0052-pypdf-6-15-0-security-refresh.md 0053-nanoid-3-3-17-security-refresh.md 0057-frontend-runtime-openssl-3-6-4.md 0061-semgrep-1-172-mcp-override-renewal.md""")),
)
def _repository_source_specs() -> tuple[tuple[str, str, str, str, str, str, str, str], ...]:
    specs: list[tuple[str, str, str, str, str, str, str, str]] = []
    groups = (
        *[("ATOMIC_MARKDOWN", lifecycle, paths) for lifecycle, paths in (*_MARKDOWN_GROUPS, *_ADR_ATOMIC_GROUPS)],
        *[("STRUCTURED_SCHEMA", lifecycle, paths) for lifecycle, paths in _STRUCTURED_GROUPS],
        *[("MANIFEST_ONLY", lifecycle, paths) for lifecycle, paths in (*_MANIFEST_BLOB_GROUPS, *_ADR_MANIFEST_GROUPS)],
    )
    for coverage, lifecycle, paths in groups:
        atomizer = {"ATOMIC_MARKDOWN": "MARKDOWN_ATOMIC_V2", "STRUCTURED_SCHEMA": "JSON_POINTER_ATOMIC_V1", "MANIFEST_ONLY": "MANIFEST_ONLY"}[coverage]
        for path in paths:
            specs.append((_source_id(path, "GIT_BLOB"), "REPOSITORY_FILE", path, atomizer, _default_destination(path), coverage, lifecycle, "GIT_BLOB"))
    for path in _CODE_PATHS:
        atomizer = "PYTHON_CONTRACT_V2" if path.endswith(".py") else "MANIFEST_ONLY"
        specs.append((_source_id(path, "GIT_BLOB"), "REPOSITORY_FILE", path, atomizer, _default_destination(path), "IMPLEMENTED_CODE", "IMPLEMENTED", "GIT_BLOB"))
    for lifecycle, paths in _TREE_GROUPS:
        for path in paths:
            specs.append((_source_id(path, "GIT_TREE"), "REPOSITORY_FILE", path, "MANIFEST_ONLY", _default_destination(path), "MANIFEST_ONLY", lifecycle, "GIT_TREE"))
    return tuple(sorted(specs, key=lambda item: item[2]))
_REPOSITORY_SOURCE_SPECS = _repository_source_specs()
_SOURCE_SPECS = (
    ("OWNER_PLAN_2026_09_07", "OWNER_PLAN", DOCUMENT_PATH, "MARKDOWN_ATOMIC_V2", "MPV2-SECTION-1", "ATOMIC_MARKDOWN", "OWNER_CANDIDATE", "RESTRICTED_OWNER_MESSAGE"),
    *_REPOSITORY_SOURCE_SPECS,
)
_V1_DESTINATIONS = {
    **{number: "MPV2-SECTION-1" for number in (1, 2, 3, 4, 5, 6)},
    7: "MPV2-SECTION-4", 8: "MPV2-SECTION-7", 9: "MPV2-SECTION-9",
    10: "MPV2-SECTION-7", 11: "MPV2-SECTION-9", 12: "MPV2-SECTION-9",
    13: "MPV2-SECTION-7", 14: "MPV2-SECTION-7", 15: "MPV2-SECTION-2",
    16: "MPV2-SECTION-7", 17: "MPV2-SECTION-9", 18: "MPV2-SECTION-11",
    19: "MPV2-SECTION-11",
    **{number: "MPV2-CUT1" for number in range(20, 36)},
    **{number: "MPV2-SECTION-10" for number in range(36, 41)},
    41: "MPV2-SECTION-12", 42: "MPV2-SECTION-1",
}
_DESTINATION_IDS = (
    *tuple(f"MPV2-SECTION-{number}" for number in range(1, 13)),
    *tuple(f"MPV2-CUT{number}" for number in range(1, 7)),
    "MPV2-CUT1-MEERA-CELL",
)
DESTINATION_POLICY = (
    "At every registered `MPV2-DESTINATION`, only a `CURRENT_NORMATIVE` row "
    "incorporates its normalized atomic focus. Its bound normalized source context "
    "resolves grammar, scope, and logical operators; that context is not independently "
    "incorporated and cannot reactivate a changed sibling focus. `HISTORICAL_ONLY` "
    "and `EVIDENCE_ONLY` rows preserve provenance but cannot authorize an operation, "
    "set a threshold, satisfy a gate, or establish acceptance. Disposition applies "
    "only to that focus: `PRESERVED` keeps it, `STRENGTHENED` keeps it plus the "
    "replacement, `RELOCATED` moves it, and "
    "`SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY` makes only the resolved owner-authorized "
    "replacement normative."
)
DESTINATION_CLAUSES = dict.fromkeys(_DESTINATION_IDS, DESTINATION_POLICY)
_DESTINATION_SOURCE_CONTEXTS = frozenset(
    sentence
    for clause in DESTINATION_CLAUSES.values()
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9`'\"(\[])", clause)
)
_ROW_FIELDS = frozenset("requirementId sourceAtomId sourceId sourceKind sourcePath sourceAuthorityRefs sourceCommit sourceGitBlob sourceContentSha256 sourceAnchor sourceSpan atomicFocusSha256 normalizedAtomicRequirement normalizedSourceContext normalizedSourceContextSha256 atomicFocusStart atomicFocusEnd atomicFocusOccurrence governingContext semanticClass normativeEffect v2DestinationClause disposition replacementId ownerAuthorityRef thresholdComparison rationale accountableOwner reviewer reviewTime result".split())
ROW_COLUMNS = tuple(sorted(_ROW_FIELDS))
STORED_ROW_COLUMNS = tuple(column for column in ROW_COLUMNS if column != "thresholdComparison")
_MAPPING_FIELDS = frozenset("schemaVersion mappingId proposalState cutoff ownerAuthority sources externalAuthorityManifest semanticDuplicateCensus rows certification".split())
_MAPPING_ARTIFACT_FIELDS = _MAPPING_FIELDS | {"rowEncoding", "rowValues"}
_SOURCE_FIELDS = frozenset("sourceId sourceKind repositoryPath sourceCommit sourceGitBlob contentSha256 atomizer semanticCoverage authorityRefs defaultV2Destination authorityOrigin coverageMode authorityLifecycle objectKind coverageStatus treeEntries treeManifestSha256".split())
_EXTERNAL_MANIFEST_FIELDS = frozenset("schemaVersion repository cutoff referenceCount orderedReferenceCensusSha256 recordCount orderedRecordSha256 retrievedAt records governingContextDecisionPartition closure".split())
_EXTERNAL_RECORD_FIELDS = frozenset("reference sourceKind sourceLocator recordIdentity author createdAt updatedAt byteCount contentSha256 cutoffEligible representation authorityEffect coverageMode coverageStatus contentAddressedRef title classificationBasis semanticCoverage sanitization clauses".split())
_EXTERNAL_CLAUSE_FIELDS = frozenset("atomicFocusEnd atomicFocusOccurrence atomicFocusSha256 atomicFocusStart classificationBasisCode clauseId governingContextDecisionRef losslessNormalizationAttestation normalizedAtomicFocus normalizedSourceContext normalizedSourceContextSha256 normativeEffect offsetCoordinateSystem redactionAttestation sourceAnchor sourceContentSha256 sourceReference sourceSpan suggestedAlias".split())
_TAXONOMY_FIELDS = frozenset("schemaVersion taxonomyId proposalState effectiveAt engineeringStages productModes cuts cutDependencySemantics cut5CapabilityDependencies laneA historicalCheckpoints adrPlans digitalTwinSequence legacyAliases compatibilityMigration activation".split())
_DISPOSITIONS = {
    "PRESERVED", "STRENGTHENED", "RELOCATED",
    "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
}
_THRESHOLD_RELATIONS = {
    "EQUAL_OR_STRONGER",
    "OWNER_AUTHORIZED_CHANGE",
    "NOT_APPLICABLE_NON_NORMATIVE",
}
_SEMANTIC_EFFECTS = {
    "NORMATIVE_REQUIREMENT": "CURRENT_NORMATIVE",
    "CURRENT_STATE_FACT": "EVIDENCE_ONLY",
    "HISTORICAL_FACT": "HISTORICAL_ONLY",
    "USER_OBSERVATION": "EVIDENCE_ONLY",
    "AUTOMATED_RESULT": "EVIDENCE_ONLY",
    "COST_ESTIMATE": "EVIDENCE_ONLY",
    "IMPLEMENTED_BEHAVIOR": "EVIDENCE_ONLY",
}
_SEMANTIC_CLASSES = tuple(_SEMANTIC_EFFECTS)
_CONTEXT_FOCUS_SPAN_OVERRIDES = {
    GITLEAKS_FALSE_POSITIVE_CLAUSE_SHA256: (
        (0, 24), (26, 45), (47, 61), (63, 82), (84, 93), (95, 160),
        (162, 187), (189, 206), (208, 229), (231, 250), (256, 273),
    ),
    # STATUS contains factual history followed by a still-binding rule in one
    # grammatical sentence. These exact, source-hash-bound spans prevent either
    # half from inheriting the other's authority effect.
    "f069ef5a129fd8b2130110c6c516b2900be44fb03eaa27359faa238888ce03a7": (
        (0, 49), (51, 101), (106, 251),
    ),
    "a78e087e32c3bced1f007fac8223c5b6c1b2839f9183e8eabf132fb9d7aa0f4d": (
        (0, 120), (124, 204),
    ),
    "c8a9d58257448d2efb1f6091616960f75f5234905b3b9afb204eec8e08a64dd4": (
        (0, 113), (115, 249),
    ),
    "87df208e6ae52f7ceb289f3e6be8544fdafa0dca46ccff1b3bf0a449beaf683b": (
        (0, 105), (107, 161), (166, 187),
    ),
    "e85ad28414a72ee79bed1645d30ec487d721ec6ee519202f1faf2dcf2d1a9b49": (
        (0, 118), (120, 142), (147, 251), (253, 315), (317, 335),
        (337, 357), (363, 390),
    ),
    "51bb8f5484d4cb4d47a716fc92b7737ce36ce59fb4f19139c2bd1b32de54be74": ((0, 72), (78, 239)),
    "9c3212c947a2874b0e6510345225a69f96e4005ebc96c14b8782b9710f4da8a5": ((0, 65), (71, 163)),
    "93603a442b71dbabf88f1d4dfba1a1824490dac44816fe3d02d53ebf0e245bbe": ((0, 122), (128, 298)),
    "4c841fe50a9553f83b47c903a7fbd2847b50b0f37a171882029396fa4d41de29": ((0, 54), (60, 223)),
    "172bb333c0125c9583009236adef2bd21e2fc372269817f724944eb355e56147": ((0, 92), (98, 214)),
    "9d9f9426006b88bd78bfd26c700af745f4393ff3bb0c26bc71598b786edbdf3f": ((0, 82), (90, 133), (138, 167)),
    "5d78a5cedae116de31b01d6370a563e257dab189ff530e93139a57fce78b701b": ((0, 25), (33, 94)),
    "f92030aa3a76371d7ec0e4f5918f2ce442f77b3f97f41941e40696b9a8826350": ((0, 77), (79, 104), (109, 276)),
    "820f161e3e0852f8c8b973b5709ea0e6a0af195cd719ad4ad602551ac4bef65b": ((0, 11), (17, 54)),
    "74abdc6e3adede54a984e828980b89623d1074472915aca94a35545d154cdb09": ((0, 80), (82, 176), (205, 273), (280, 376)),
    "30b8bf63b93a4306a3c0c7e4a6ac7fa983dce4c73b3c7aa16f36e509cf313dda": ((0, 26), (28, 51), (56, 95)),
}
_PRIVATE_PATTERNS = (
    re.compile(r"/Users/", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"https?://[^\s]+[?&](?:sig|signature|token|credential|key)=", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
_COMPATIBILITY_MIGRATION_SURFACES = (
    "SCHEMA_VERSIONS", "ROADMAP_REFERENCES", "STATUS_RECORDS", "TESTS",
    "ISSUE_TEMPLATES", "COMPLETION_EVENTS", "TRACEABILITY_RECORDS",
)
class DuplicateJsonMember(ValueError):
    pass
@dataclass(frozen=True)
class ClauseUnit:
    exact_source_clause: str
    atomic_focus: str
    focus_start: int
    focus_end: int
    focus_occurrence: int
@dataclass(frozen=True)
class Atom:
    source_id: str
    anchor: str
    text: str
    exact_source_clause: str | None = None
    focus_start: int = 0
    focus_end: int | None = None
    focus_occurrence: int = 1
    source_span_start_line: int = 1
    source_span_end_line: int = 1
    raw_source_span_sha256: str = ""
    @property
    def source_clause(self) -> str:
        return self.exact_source_clause or self.text
    @property
    def resolved_focus_end(self) -> int:
        return self.focus_end if self.focus_end is not None else len(self.text)
    @property
    def clause_sha256(self) -> str:
        return _sha256(self.text.encode("utf-8"))
    @property
    def source_context_sha256(self) -> str:
        return _sha256(self.source_clause.encode("utf-8"))
    @property
    def atom_id(self) -> str:
        material = (
            f"{self.source_id}\0{self.anchor}\0{self.source_clause}\0"
            f"{self.focus_start}:{self.resolved_focus_end}:{self.focus_occurrence}\0"
            f"{self.source_span_start_line}:{self.source_span_end_line}:"
            f"{self.raw_source_span_sha256}\0{self.text}"
        ).encode("utf-8")
        return "atom:" + _sha256(material)
    @property
    def requirement_id(self) -> str:
        return "MPV2-" + self.atom_id.removeprefix("atom:")[:20].upper()
def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def _git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
def encode_requirement(atom: Atom) -> str | dict[str, Any]:
    """Keep one reviewed false positive exact without creating a live secret match."""
    return _encode_source_text(atom.text)
def _encode_source_text(value: str) -> str | dict[str, Any]:
    if _sha256(value.encode("utf-8")) != GITLEAKS_FALSE_POSITIVE_CLAUSE_SHA256:
        return value
    return {
        "encoding": "UNICODE_CODEPOINTS_V1",
        "codepoints": [ord(character) for character in value],
    }
def decode_requirement(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict) or set(value) != {"encoding", "codepoints"}:
        raise ValueError("unsupported requirement encoding")
    if value.get("encoding") != "UNICODE_CODEPOINTS_V1":
        raise ValueError("unsupported requirement encoding")
    codepoints = value.get("codepoints")
    if (
        not isinstance(codepoints, list)
        or not codepoints
        or not all(
            isinstance(codepoint, int)
            and not isinstance(codepoint, bool)
            and 0 <= codepoint <= 0x10FFFF
            and not 0xD800 <= codepoint <= 0xDFFF
            for codepoint in codepoints
        )
    ):
        raise ValueError("invalid Unicode codepoints")
    return "".join(chr(codepoint) for codepoint in codepoints)
def _normalize(lines: Iterable[str]) -> str:
    return " ".join(part for line in lines if (part := " ".join(line.strip().split())))
def _split_outside_backticks(value: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    start = 0
    in_code = False
    for index, character in enumerate(value):
        if character == "`":
            in_code = not in_code
        elif character == delimiter and not in_code:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return [part for part in parts if part]
def _comma_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    start = 0
    in_code = False
    depth = 0
    for index, character in enumerate(value):
        if character == "`":
            in_code = not in_code
        elif not in_code and character in "([":
            depth += 1
        elif not in_code and character in ")]":
            depth = max(0, depth - 1)
        elif (
            character == ","
            and not in_code
            and depth == 0
            and not (
                index > 0
                and index + 1 < len(value)
                and value[index - 1].isdigit()
                and value[index + 1].isdigit()
            )
        ):
            fragment = value[start:index].strip()
            if fragment:
                fragments.append(fragment)
            start = index + 1
    fragment = value[start:].strip()
    if fragment:
        fragments.append(fragment)
    return fragments
def _parenthetical_transition_fragments(value: str) -> list[str]:
    """Separate a closed parenthetical rule from the factual clause after it."""
    marker = value.find("):")
    if marker < 0:
        return [value]
    before = value[:marker].rstrip()
    after = value[marker + 2 :].strip()
    return [fragment for fragment in (before, after) if fragment]
def _exact_focus_span_units(value: str) -> list[ClauseUnit] | None:
    exact_spans = _CONTEXT_FOCUS_SPAN_OVERRIDES.get(_sha256(value.encode("utf-8")))
    if exact_spans is None:
        return None
    if any(start < 0 or start >= end or end > len(value) for start, end in exact_spans):
        raise ValueError("exact focus-span override is invalid")
    return [
        ClauseUnit(
            exact_source_clause=value,
            atomic_focus=value[start:end],
            focus_start=start,
            focus_end=end,
            focus_occurrence=value[:start].count(value[start:end]) + 1,
        )
        for start, end in exact_spans
    ]
def _requires_comma_focuses(value: str) -> bool:
    context_hash = _sha256(value.encode("utf-8"))
    return context_hash in _CONTEXT_FOCUS_SPAN_OVERRIDES or any(
        target.context_sha256 == context_hash
        for targets in globals().get("_CONFLICT_TARGETS", ())
        for target in targets
    )
def _contextual_clause_units(
    value: str, *, force_comma_focuses: bool = False
) -> list[ClauseUnit]:
    """Identify exact focus spans without inventing inherited natural language."""
    normalized = _normalize([value])
    if not normalized:
        return []
    exact_units = _exact_focus_span_units(normalized)
    if exact_units is not None:
        return exact_units
    descriptor = re.match(r"^(?P<prefix>[-*+]\s+`[^`]+`\s+—\s+)(?P<body>.+)$", normalized)
    if descriptor:
        focuses = (
            _comma_fragments(descriptor.group("body"))
            if force_comma_focuses or _requires_comma_focuses(normalized)
            else [descriptor.group("body")]
        )
        sentence = normalized
        descriptor_units: list[ClauseUnit] = []
        cursor = len(descriptor.group("prefix"))
        for raw_focus in focuses:
            focus = re.sub(
                r"^(?:and|but|or|plus)\s+", "", raw_focus, flags=re.IGNORECASE
            )
            if re.fullmatch(r"(?:and|but|or|plus)", focus, re.IGNORECASE):
                continue
            start = sentence.find(focus, cursor)
            if start < 0:
                raise ValueError("atomic focus is not an exact source substring")
            end = start + len(focus)
            descriptor_units.append(
                ClauseUnit(
                    exact_source_clause=sentence,
                    atomic_focus=focus,
                    focus_start=start,
                    focus_end=end,
                    focus_occurrence=sentence[:start].count(focus) + 1,
                )
            )
            cursor = end
        return descriptor_units
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9`'\"(\[])", normalized)
    result: list[ClauseUnit] = []
    for sentence in sentences:
        exact_units = _exact_focus_span_units(sentence)
        if exact_units is not None:
            result.extend(exact_units)
            continue
        cursor = 0
        semicolon_parts = _split_outside_backticks(sentence, ";")
        for part in semicolon_parts:
            for transition_fragment in _parenthetical_transition_fragments(part):
                raw_focuses = (
                    _comma_fragments(transition_fragment)
                    if force_comma_focuses or _requires_comma_focuses(sentence)
                    else [transition_fragment]
                )
                for raw_focus in raw_focuses:
                    focus = re.sub(
                        r"^(?:and|but|or|plus)\s+",
                        "",
                        raw_focus,
                        flags=re.IGNORECASE,
                    )
                    if re.fullmatch(
                        r"(?:and|but|or|plus|[-*+]|\d+[.)])",
                        focus.strip(),
                        re.IGNORECASE,
                    ):
                        continue
                    start = sentence.find(focus, cursor)
                    if start < 0:
                        raise ValueError("atomic focus is not an exact source substring")
                    end = start + len(focus)
                    result.append(
                        ClauseUnit(
                            exact_source_clause=sentence,
                            atomic_focus=focus,
                            focus_start=start,
                            focus_end=end,
                            focus_occurrence=sentence[:start].count(focus) + 1,
                        )
                    )
                    cursor = end
    return result
def _clause_units(value: str) -> list[str]:
    return [unit.atomic_focus for unit in _contextual_clause_units(value)]
def _table_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.replace(r"\|", "|").strip() for cell in re.split(r"(?<!\\)\|", stripped)]
def _table_value_units(header: str, value: str) -> list[str]:
    """Keep table-field predicates intact; split only explicit set-valued fields."""
    units: list[str] = []
    for clause in _clause_units(value):
        if header in {"Included", "Explicitly excluded"}:
            units.extend(_comma_fragments(clause))
        else:
            units.append(clause)
    return units
_SEMANTIC_FIRST_TABLE_HEADERS = frozenset({"requirement", "requirement/decision"})
def _markdown_atoms(source_id: str, text: str) -> list[Atom]:
    lines = text.splitlines()
    atoms: list[Atom] = []
    headings: list[str] = []
    block: list[str] = []
    block_start = 1
    block_heading = "# document"
    block_kind = "prose"
    in_fence = False
    table_candidate: list[str] | None = None
    table_headers: list[str] | None = None
    def context() -> str:
        return " > ".join(headings) if headings else "# document"
    def flush(*, split: bool = True) -> None:
        nonlocal block, block_kind
        normalized = _normalize(block)
        if normalized:
            raw_span_sha256 = _sha256("\n".join(block).encode("utf-8"))
            span_end = block_start + len(block) - 1
            units = (
                _contextual_clause_units(normalized)
                if split
                else [
                    ClauseUnit(
                        exact_source_clause=normalized,
                        atomic_focus=normalized,
                        focus_start=0,
                        focus_end=len(normalized),
                        focus_occurrence=1,
                    )
                ]
            )
            for clause_index, unit in enumerate(units, start=1):
                atoms.append(
                    Atom(
                        source_id,
                        f"{block_heading}::{block_kind}:L{block_start}:C{clause_index}",
                        unit.atomic_focus,
                        unit.exact_source_clause,
                        unit.focus_start,
                        unit.focus_end,
                        unit.focus_occurrence,
                        block_start,
                        span_end,
                        raw_span_sha256,
                    )
                )
        block = []
        block_kind = "prose"
    def reset_table() -> None:
        nonlocal table_candidate, table_headers
        table_candidate = None
        table_headers = None
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_fence:
                flush()
                block_start = index
                block_heading = context()
                block_kind = "fence"
                block = [line]
                in_fence = True
            else:
                block.append(line)
                flush(split=False)
                in_fence = False
            continue
        if in_fence:
            block.append(line)
            continue
        heading_match = re.match(r"^(#{1,6})\s+\S", stripped)
        if heading_match:
            flush()
            level = len(heading_match.group(1))
            headings[:] = headings[: level - 1]
            headings.append(stripped)
            reset_table()
            continue
        if not stripped:
            flush()
            reset_table()
            continue
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            flush()
            reset_table()
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            flush()
            cells = _table_cells(stripped)
            if all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in cells):
                if table_candidate is not None:
                    table_headers = table_candidate
                continue
            if table_candidate is None:
                table_candidate = cells
                continue
            if table_headers is None:
                reset_table()
                table_candidate = cells
                continue
            padded = cells + [""] * max(0, len(table_headers) - len(cells))
            normalized_cells = [_normalize([value]) for value in padded]
            row_key = (
                f"{table_headers[0]}={normalized_cells[0]}"
                if table_headers and table_headers[0] and normalized_cells[0]
                else f"row={index}"
            )
            row_parts: list[str] = []
            value_starts: dict[int, int] = {}
            cursor = 0
            for column, header in enumerate(table_headers):
                if not header or not normalized_cells[column]:
                    continue
                part = f"{header}={normalized_cells[column]}"
                value_starts[column] = cursor + len(header) + 1
                row_parts.append(part)
                cursor += len(part) + 3
            exact_clause = " | ".join(row_parts)
            for column, header in enumerate(table_headers):
                if (
                    column == 0
                    and header.casefold() not in _SEMANTIC_FIRST_TABLE_HEADERS
                ) or not header or not normalized_cells[column]:
                    continue
                context_cursor = 0
                context_start = 0
                prior_context: str | None = None
                for unit_index, unit in enumerate(
                    _contextual_clause_units(
                        normalized_cells[column],
                        force_comma_focuses=_requires_comma_focuses(exact_clause),
                    ),
                    start=1,
                ):
                    if unit.exact_source_clause != prior_context:
                        context_start = normalized_cells[column].find(
                            unit.exact_source_clause, context_cursor
                        )
                        if context_start < 0:
                            raise ValueError("table focus context is not in its source cell")
                        context_cursor = context_start + len(unit.exact_source_clause)
                        prior_context = unit.exact_source_clause
                    start = value_starts[column] + context_start + unit.focus_start
                    atoms.append(
                        Atom(
                            source_id,
                            f"{context()}::table:L{index}:{row_key}:{header}:U{unit_index}",
                            unit.atomic_focus,
                            exact_clause,
                            start,
                            value_starts[column] + context_start + unit.focus_end,
                            exact_clause[:start].count(unit.atomic_focus) + 1,
                            index,
                            index,
                            _sha256(line.encode("utf-8")),
                        )
                    )
            continue
        reset_table()
        if re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", stripped):
            flush()
            block_start = index
            block_heading = context()
            block_kind = "list"
            block = [line]
            continue
        if not block:
            block_start = index
            block_heading = context()
            block_kind = "prose"
        block.append(line)
    flush(split=not in_fence)
    return atoms
def _python_declaration(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
        return f"{prefix} {node.name}({ast.unparse(node.args)}){returns}:"
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(base) for base in node.bases]
        bases.extend(f"{keyword.arg}={ast.unparse(keyword.value)}" for keyword in node.keywords)
        return f"class {node.name}{f'({', '.join(bases)})' if bases else ''}:"
    return ""
def _python_atoms(source_id: str, text: str) -> list[Atom]:
    tree = ast.parse(text)
    atoms: list[Atom] = []
    source_lines = text.splitlines()
    def expression(node: ast.AST) -> str:
        nested_string = any(
            isinstance(child, ast.Constant) and isinstance(child.value, str)
            for joined in ast.walk(node) if isinstance(joined, ast.JoinedStr) for part in joined.values if isinstance(part, ast.FormattedValue) for child in ast.walk(part.value))
        return (ast.get_source_segment(text, node) if nested_string else None) or ast.unparse(node)
    def span(node: ast.AST) -> tuple[int, int, str]:
        start = getattr(node, "lineno", 1)
        end = getattr(node, "end_lineno", start)
        raw = "\n".join(source_lines[start - 1 : end])
        return start, end, _sha256(raw.encode("utf-8"))
    def emit(
        owner: str,
        node: ast.AST,
        kind: str,
        value: str,
        control_path: tuple[str, ...] = (),
    ) -> None:
        normalized = _normalize(value.splitlines())
        if not normalized:
            return
        path = " -> ".join(control_path)
        contract = f"control-path {path}: {normalized}" if path else normalized
        path_id = _sha256(path.encode("utf-8"))[:12] if path else "root"
        span_start, span_end, span_sha256 = span(node)
        atoms.append(
            Atom(
                source_id,
                f"python:{owner}:{kind}:L{getattr(node, 'lineno', 1)}:P{path_id}",
                contract,
                source_span_start_line=span_start,
                source_span_end_line=span_end,
                raw_source_span_sha256=span_sha256,
            )
        )
    def emit_docstring(owner: str, node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        docstring = ast.get_docstring(node, clean=False)
        if not docstring:
            return
        doc_node = node.body[0] if node.body else node
        span_start, span_end, span_sha256 = span(doc_node)
        for index, unit in enumerate(_contextual_clause_units(docstring), start=1):
            atoms.append(
                Atom(
                    source_id,
                    f"python:{owner}:doc:L{span_start}:C{index}",
                    unit.atomic_focus,
                    unit.exact_source_clause,
                    unit.focus_start,
                    unit.focus_end,
                    unit.focus_occurrence,
                    span_start,
                    span_end,
                    span_sha256,
                )
            )
    def handler_label(handler: ast.ExceptHandler) -> str:
        exception = ast.unparse(handler.type) if handler.type else "BaseException"
        suffix = f" as {handler.name}" if handler.name else ""
        return f"except {exception}{suffix}"
    def visit_body(
        statements: list[ast.stmt], owner: str, control_path: tuple[str, ...]
    ) -> None:
        for statement in statements:
            if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                declaration_owner = (
                    statement.name if owner == "module" else f"{owner}.{statement.name}"
                )
                for index, decorator in enumerate(statement.decorator_list, start=1):
                    emit(
                        declaration_owner,
                        statement,
                        f"decorator-{index}",
                        "@" + ast.unparse(decorator),
                        control_path,
                    )
                emit(
                    declaration_owner,
                    statement,
                    type(statement).__name__,
                    _python_declaration(statement),
                    control_path,
                )
                emit_docstring(declaration_owner, statement)
                visit_body(statement.body, declaration_owner, control_path)
                continue
            if isinstance(statement, ast.If):
                label = f"if {expression(statement.test)}"
                emit(owner, statement, "If", label, control_path)
                visit_body(statement.body, owner, (*control_path, label))
                visit_body(
                    statement.orelse,
                    owner,
                    (*control_path, f"else of {label}"),
                )
                continue
            if isinstance(statement, (ast.For, ast.AsyncFor)):
                keyword = "async for" if isinstance(statement, ast.AsyncFor) else "for"
                label = (
                    f"{keyword} {ast.unparse(statement.target)} in "
                    f"{ast.unparse(statement.iter)}"
                )
                emit(owner, statement, type(statement).__name__, label, control_path)
                visit_body(statement.body, owner, (*control_path, label))
                visit_body(
                    statement.orelse,
                    owner,
                    (*control_path, f"else of {label}"),
                )
                continue
            if isinstance(statement, ast.While):
                label = f"while {ast.unparse(statement.test)}"
                emit(owner, statement, "While", label, control_path)
                visit_body(statement.body, owner, (*control_path, label))
                visit_body(
                    statement.orelse,
                    owner,
                    (*control_path, f"else of {label}"),
                )
                continue
            if isinstance(statement, (ast.With, ast.AsyncWith)):
                keyword = "async with" if isinstance(statement, ast.AsyncWith) else "with"
                label = f"{keyword} " + ", ".join(
                    ast.unparse(item) for item in statement.items
                )
                emit(owner, statement, type(statement).__name__, label, control_path)
                visit_body(statement.body, owner, (*control_path, label))
                continue
            if isinstance(statement, (ast.Try, ast.TryStar)):
                handlers = ", ".join(handler_label(item) for item in statement.handlers)
                label = (
                    f"try handlers=[{handlers}] else={bool(statement.orelse)} "
                    f"finally={bool(statement.finalbody)}"
                )
                emit(owner, statement, type(statement).__name__, label, control_path)
                visit_body(statement.body, owner, (*control_path, "try"))
                for handler in statement.handlers:
                    visit_body(
                        handler.body,
                        owner,
                        (*control_path, handler_label(handler)),
                    )
                visit_body(statement.orelse, owner, (*control_path, "try else"))
                visit_body(statement.finalbody, owner, (*control_path, "finally"))
                continue
            if isinstance(statement, ast.Match):
                label = f"match {ast.unparse(statement.subject)}"
                emit(owner, statement, "Match", label, control_path)
                for case in statement.cases:
                    case_label = f"case {ast.unparse(case.pattern)}"
                    if case.guard is not None:
                        case_label += f" if {ast.unparse(case.guard)}"
                    visit_body(case.body, owner, (*control_path, label, case_label))
                continue
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            ):
                continue
            source = ast.get_source_segment(text, statement) or ast.unparse(statement)
            emit(owner, statement, type(statement).__name__, source, control_path)
    emit_docstring("module", tree)
    visit_body(tree.body, "module", ())
    return sorted(
        atoms,
        key=lambda atom: (
            int(cast(re.Match[str], re.search(r":L(\d+)", atom.anchor)).group(1)),
            atom.anchor,
            atom.text,
        ),
    )
_JSON_SCHEMA_CONSTRAINT_KEYS = frozenset(
    {
        "$defs", "$ref", "additionalProperties", "allOf", "anyOf", "const",
        "dependentRequired", "else", "enum", "exclusiveMaximum",
        "exclusiveMinimum", "format", "if", "items", "maxItems", "maxLength",
        "maximum", "minItems", "minLength", "minimum", "multipleOf", "not",
        "oneOf", "pattern", "properties", "required", "then", "type",
        "uniqueItems",
    }
)
def _json_pointer_atomizer(source_id: str, text: str) -> list[Atom]:
    """Atomize duplicate-free JSON leaves with explicit schema/fact semantics."""
    value = _load_json_text(text)
    schema_document = isinstance(value, dict) and (
        "$schema" in value or "$id" in value
    )
    raw_hash = _sha256(text.encode("utf-8"))
    end_line = max(1, len(text.splitlines()))
    atoms: list[Atom] = []
    def escaped(segment: str) -> str:
        return segment.replace("~", "~0").replace("/", "~1")
    def emit(path: tuple[str, ...], leaf: Any) -> None:
        pointer = "" if not path else "/" + "/".join(escaped(item) for item in path)
        role = (
            "SCHEMA_CONSTRAINT"
            if schema_document and any(item in _JSON_SCHEMA_CONSTRAINT_KEYS for item in path)
            else "INSTANCE_FACT"
        )
        encoded = _canonical_json(leaf)
        context = f"{role} {pointer or '/'} = {encoded}"
        focus_start = len(context) - len(encoded)
        atoms.append(
            Atom(
                source_id,
                f"json-pointer:{pointer or '/'}::{role}:L1",
                encoded,
                exact_source_clause=context,
                focus_start=focus_start,
                focus_end=len(context),
                focus_occurrence=context[:focus_start].count(encoded) + 1,
                source_span_start_line=1,
                source_span_end_line=end_line,
                raw_source_span_sha256=raw_hash,
            )
        )
    def walk(item: Any, path: tuple[str, ...]) -> None:
        if isinstance(item, dict):
            if not item:
                emit(path, item)
            for key in sorted(item):
                walk(item[key], (*path, key))
        elif isinstance(item, list):
            if not item:
                emit(path, item)
            for index, child in enumerate(item):
                walk(child, (*path, str(index)))
        else:
            emit(path, item)
    walk(value, ())
    return sorted(atoms, key=lambda atom: (atom.anchor, atom.atom_id))
@lru_cache(maxsize=512)
def _cached_atoms(source_id: str, atomizer: str, data: bytes) -> tuple[Atom, ...]:
    text = data.decode("utf-8")
    if atomizer == "MARKDOWN_ATOMIC_V2":
        return tuple(_markdown_atoms(source_id, text))
    if atomizer == "PYTHON_CONTRACT_V2":
        return tuple(_python_atoms(source_id, text))
    if atomizer == "JSON_POINTER_ATOMIC_V1":
        return tuple(_json_pointer_atomizer(source_id, text))
    if atomizer == "MANIFEST_ONLY":
        return ()
    raise ValueError(f"unknown atomizer: {atomizer}")
def _atoms(source_id: str, atomizer: str, data: bytes) -> list[Atom]:
    return list(_cached_atoms(source_id, atomizer, data))
def _git_directory(root: Path) -> Path:
    marker = root / ".git"
    if marker.is_dir():
        return marker.resolve()
    try:
        value = marker.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise ValueError("frozen repository source unavailable") from exc
    if not value.startswith("gitdir: "):
        raise ValueError("frozen repository source unavailable")
    target = Path(value.removeprefix("gitdir: "))
    return (target if target.is_absolute() else marker.parent / target).resolve()
def _frozen_git(git_directory: Path, arguments: list[str]) -> bytes:
    try:
        result = subprocess.run(
            ["/usr/bin/git", "--git-dir", str(git_directory), *arguments],
            env={
                "PATH": "/usr/bin:/bin",
                "LC_ALL": "C",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_NO_LAZY_FETCH": "1",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_TERMINAL_PROMPT": "0",
            },
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("frozen repository source unavailable") from exc
    if result.returncode != 0:
        raise ValueError("frozen repository source unavailable")
    return bytes(result.stdout)
def _parse_ls_tree_record(record: bytes) -> tuple[str, str, str, str]:
    try:
        metadata, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = raw_path.decode("utf-8")
    except (UnicodeError, ValueError) as exc:
        raise ValueError("frozen repository object metadata invalid") from exc
    if (
        re.fullmatch(r"[0-7]{6}", mode) is None
        or kind not in {"blob", "tree", "commit"}
        or re.fullmatch(r"[0-9a-f]{40}", object_id) is None
        or not path
    ):
        raise ValueError("frozen repository object metadata invalid")
    return mode, kind, object_id, path
@lru_cache(maxsize=2_048)
def _frozen_repository_object_cached(
    git_directory: Path, commit: str, relative: str
) -> tuple[str, str, list[dict[str, str]], bytes]:
    records = [
        item
        for item in _frozen_git(git_directory, ["ls-tree", "-z", commit, "--", relative]).split(b"\0")
        if item
    ]
    if len(records) != 1:
        raise ValueError("frozen repository source unavailable")
    mode, kind, object_id, selected_path = _parse_ls_tree_record(records[0])
    if selected_path != relative or kind not in {"blob", "tree"}:
        raise ValueError("frozen repository source unavailable")
    if kind == "blob":
        data = _frozen_git(git_directory, ["cat-file", "blob", object_id])
        if _git_blob(data) != object_id:
            raise ValueError("frozen repository object mismatch")
        return "GIT_BLOB", object_id, [], data
    descendants: list[dict[str, str]] = []
    prefix = relative.rstrip("/") + "/"
    raw_entries = _frozen_git(
        git_directory, ["ls-tree", "-r", "-t", "-z", commit, "--", relative]
    )
    for raw in raw_entries.split(b"\0"):
        if not raw:
            continue
        child_mode, child_kind, child_id, child_path = _parse_ls_tree_record(raw)
        if not child_path.startswith(prefix):
            continue
        descendants.append(
            {
                "mode": child_mode,
                "objectKind": child_kind.upper(),
                "objectId": child_id,
                "repositoryPath": child_path,
            }
        )
    descendants.sort(key=lambda item: item["repositoryPath"])
    if not descendants or len({item["repositoryPath"] for item in descendants}) != len(descendants):
        raise ValueError("frozen repository tree manifest invalid")
    data = _canonical_json(descendants).encode("utf-8")
    return "GIT_TREE", object_id, descendants, data
def _frozen_repository_object(
    root: Path, commit: str, relative: str
) -> tuple[str, str, list[dict[str, str]], bytes]:
    return _frozen_repository_object_cached(_git_directory(root), commit, relative)
def frozen_source_bytes(root: Path, source: dict[str, Any]) -> bytes:
    """Read repository sources only from the declared frozen Git object."""
    commit = source.get("sourceCommit")
    relative = source.get("repositoryPath")
    source_kind = source.get("sourceKind")
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
        or ".." in Path(relative).parts
    ):
        raise ValueError("frozen source path invalid")
    repository_source = source_kind == "REPOSITORY_FILE" or (
        source_kind is None and commit is not None
    )
    if repository_source:
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise ValueError("repository source commit invalid")
        actual_kind, _, _, data = _frozen_repository_object(root, commit, relative)
        declared_kind = source.get("objectKind")
        if declared_kind is not None and declared_kind != actual_kind:
            raise ValueError("frozen repository object kind mismatch")
        return data
    if source_kind not in {
        "OWNER_PLAN",
        "OWNER_PLAN_CANDIDATE",
        "OWNER_ADOPTED_PLAN",
    } or commit is not None or relative != DOCUMENT_PATH:
        raise ValueError("non-repository source binding invalid")
    return (root / relative).read_bytes()
_REFERENCED_PULL_REQUEST_NUMBERS = frozenset(
    int(value)
    for value in """7 15 22 23 26 27 29 30 31 32 33 45 46 47 50 53 54 56 59 62 63 64 73 74 75 76 77 78 79 80 85 87 90 92 94 98 102 103 106 108 110 112 116 120 124 133 134 135 137 140 153 162 163 166 168 170 173 175 177 179 182 185 187 189 191 193 195 197 199 201 203 205 207 210 212 214 216 218 220 222 224 226 230 232 234 236 238 242 244 246 248 250 252 254 258 260 262 264 266 268 273 277 279 281 282 283 284 286 288 293 295 297 299 301 303 305 309 310 314 318 320 322 325 331 333 347 348 350 352 354 362 373 380 381 388 392 395 398 399 400 402 404 407 409 410 411 412 414 422 425 429 430 433 437 443 453 455 457 458 461 462 463 464 465 467 470 477 483 491 492 497 501 505""".split()
)
def _issue_refs(text: str, source_path: str) -> list[str]:
    comments = {
        f"github-comment:{match}"
        for match in re.findall(r"issuecomment-([0-9]{10})", text, re.IGNORECASE)
    }
    logical_text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    authority_phrases = re.finditer(
        r"\b(?:OWNER\s+)?(?:comments?|record|amendment|correction|replan|"
        r"checkpoint|transition(?:\s+comment)?)\b(?P<body>[^.\n]{0,600})",
        logical_text,
        re.IGNORECASE,
    )
    for phrase in authority_phrases:
        comments.update(
            f"github-comment:{match}"
            for match in re.findall(
                r"(?<![0-9a-f])([0-9]{10})(?![0-9a-f])",
                phrase.group("body"),
                re.IGNORECASE,
            )
        )
    typed: set[str] = set()
    typed_numbers: set[str] = set()
    for match in re.finditer(
        r"\b(?:Owner\s+|Canonical\s+)?"
        r"(?P<kind>Issues?|PRs?|Pull\s+Requests?)\s*(?::|=)?\s*"
        r"(?P<body>`?#\d+`?(?:\s*(?:,\s*(?:and\s+)?|/\s*|and\s+|;\s*)`?#\d+`?)*)",
        text,
        re.IGNORECASE,
    ):
        prefix = (
            "github-issue"
            if match.group("kind").lower().startswith("issue")
            else "github-pull-request"
        )
        for number in re.findall(r"#(\d+)", match.group("body")):
            typed.add(f"{prefix}:{number}")
            typed_numbers.add(number)
    for match in re.finditer(
        r"(?P<kind>PR|Pull\s+Request|Issue)\s+`?#(?P<number>\d+)`?",
        text,
        re.IGNORECASE,
    ):
        kind = match.group("kind").lower()
        number = match.group("number")
        if kind in {"pr", "pull request"}:
            typed.add(f"github-pull-request:{number}")
        else:
            typed.add(f"github-issue:{number}")
        typed_numbers.add(number)
    for number in re.findall(r"(?<![A-Za-z0-9])#(\d+)", text):
        if number not in typed_numbers:
            typed.add(f"github-reference:{number}")
    canonical = {
        (
            "github-pull-request"
            if int(reference.rsplit(":", 1)[1])
            in _REFERENCED_PULL_REQUEST_NUMBERS
            else "github-issue"
        )
        + ":"
        + reference.rsplit(":", 1)[1]
        for reference in typed
    }
    refs = sorted(comments | canonical)
    return refs or [f"repository:{source_path}@{BASE_SHA}"]
def _tree_issue_refs(
    root: Path, entries: Iterable[dict[str, str]], source_path: str
) -> list[str]:
    # Executable/test literals are code evidence, not external normative citations.
    if not source_path.startswith("docs/"):
        return [f"repository:{source_path}@{BASE_SHA}"]
    refs: set[str] = set()
    text_suffixes = {".css", ".html", ".js", ".json", ".md", ".py", ".sh", ".toml", ".ts", ".tsx", ".txt", ".yaml", ".yml"}
    for entry in entries:
        path = entry["repositoryPath"]
        if entry["objectKind"] != "BLOB" or Path(path).suffix.lower() not in text_suffixes:
            continue
        data = _frozen_git(_git_directory(root), ["cat-file", "blob", entry["objectId"]])
        if _git_blob(data) != entry["objectId"]:
            raise ValueError("frozen repository descendant mismatch")
        try:
            found = _issue_refs(data.decode("utf-8"), path)
        except UnicodeDecodeError:
            continue
        refs.update(item for item in found if item.startswith("github-"))
    return sorted(refs) or [f"repository:{source_path}@{BASE_SHA}"]
@dataclass(frozen=True)
class ConflictRule:
    source_id: str
    needle: str
    destination: str
    disposition: str
    replacement_key: str | None
    comparison: str
    rationale: str
_CONFLICT_RULES = (
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "Only one retry is allowed, and only for a predeclared independently evidenced technical failure.",
        "MPV2-CUT1-MEERA-CELL",
        "STRENGTHENED",
        "retry",
        "The maximum controllable create-retry count decreases from one to zero for prototype and provider qualification; every V1 non-retryable category remains non-retryable.",
        "The stricter zero-retry prototype policy retains the V1 failure exclusions and removes an avoidable duplicate-create path.",
    ),
    ConflictRule(
        "API_CONTRACT",
        "- Create retries may run only when provider idempotency and billable retry safety are both documented in the provider config/policy.",
        "MPV2-SECTION-9",
        "STRENGTHENED",
        "code_retry",
        "The existing idempotency and billable-safety prerequisites remain mandatory, and the retry path is additionally unreachable for prototype or unqualified provider activation because its effective retry budget is zero.",
        "The provider-neutral guard is retained while the prototype boundary removes create retries before qualification.",
    ),
    ConflictRule(
        "API_CONTRACT",
        "Safe retries honor clamped HTTP `Retry-After`",
        "MPV2-SECTION-9",
        "STRENGTHENED",
        "code_retry",
        "Clamped Retry-After handling remains valid for an authorized future route, while a zero effective create-retry budget makes it unreachable during prototype and provider qualification.",
        "The transport control is preserved without allowing it to grant a prequalification retry.",
    ),
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "freeze the sample-addressed 15-second audition excerpt",
        "MPV2-SECTION-6",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "fixture",
        "The owner-authorized fixture changes from 15.000 seconds to one uninterrupted 29.494-second trim: 29.494 is 14.494 seconds longer and 1.96627 times the former duration, with two consecutive caption blocks and difficult-phrase coverage.",
        "The continuous sample replaces the shorter audition fixture without promoting the earlier stitched diagnostic artifact.",
    ),
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "US$100 total audition ceiling",
        "MPV2-SECTION-8",
        "STRENGTHENED",
        "budget",
        "Current authorized exposure is USD 0, which is less than or equal to the retained US$100 outer audition ceiling; every future operation also requires an exact reservation and fresh authority.",
        "The outer ceiling remains intact while exhausted authority and per-operation reservation make the current posture stricter.",
    ),
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "The US$100 ceiling applies only to auditions.",
        "MPV2-SECTION-8",
        "PRESERVED",
        None,
        "The US$100 value remains only an outer audition ceiling; final renders still require a separate exact quote and owner approval.",
        "The legacy scope distinction remains normative and grants no current spend authority.",
    ),
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "decoded duration 90.000–120.000 seconds",
        "MPV2-CUT1-MEERA-CELL",
        "PRESERVED",
        None,
        "The accepted Meera duration 117.981917 seconds remains inside the exact 90.000–120.000-second interval; Myra's separate cell does not alter this Meera threshold.",
        "The exact Meera duration floor and ceiling remain unchanged at the Meera-cell destination.",
    ),
    ConflictRule(
        "API_CONTRACT",
        "the service may apply `cut1-atomic-grounding-v1` only to the selected Meera narration",
        "MPV2-CUT1-MEERA-CELL",
        "PRESERVED",
        None,
        "The exact selected-Meera grounding restriction remains unchanged and is scoped only to the Meera cell; it cannot establish Raj/Myra or aggregate Cut 1 acceptance.",
        "The implemented Meera grounding policy remains a cell-specific duty rather than an aggregate presenter-selection rule.",
    ),
    ConflictRule(
        "API_CONTRACT",
        "Narration and TTS receipt authority additionally require selected Meera",
        "MPV2-CUT1-MEERA-CELL",
        "PRESERVED",
        None,
        "The selected-Meera narration and receipt restriction remains unchanged at the Meera cell; Raj and Myra require their own accepted authority and evidence.",
        "The existing Meera receipt boundary is preserved without allowing it to satisfy another presenter cell.",
    ),
    *tuple(
        ConflictRule(
            "MASTER_PROGRAM_V1",
            needle,
            "MPV2-CUT1-MEERA-CELL",
            "STRENGTHENED",
            "aggregate",
            comparison,
            "The V1 Meera-cell artifact minimum is retained while the outer Cut 1 aggregate expands to three separately accepted presenters and six independent aspect cells.",
        )
        for needle, comparison in (
            (
                "The aggregate requires exactly one accepted canonical WAV",
                "The exact one-WAV Meera minimum remains, and the outer aggregate requires three presenter-specific WAVs; three is greater than or equal to one and cross-presenter substitution is prohibited.",
            ),
            (
                "The aggregate requires one distinct accepted 1920×1080 MP4",
                "The distinct Meera landscape MP4 remains required, and the outer aggregate requires one independently accepted landscape MP4 for each of three presenters; three is greater than or equal to one.",
            ),
            (
                "The aggregate requires one distinct accepted 1080×1920 MP4",
                "The distinct Meera portrait MP4 remains required, and the outer aggregate requires one independently accepted portrait MP4 for each of three presenters; three is greater than or equal to one.",
            ),
        )
    ),
    *tuple(
        ConflictRule(
            source_id,
            needle,
            "MPV2-CUT1",
            "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
            "presenter",
            "The required presenter count changes from one selected primary with deferred or fallback presenters to three co-required presenters and from two aspect outputs to six independent presenter/aspect cells; all per-presenter quality duties remain.",
            "The owner-authorized six-cell contract replaces only primary, backup, fallback, or deferred selection semantics.",
        )
        for source_id, needle in (
            ("MASTER_PROGRAM_V1", "selected presenter Meera only, with Myra and Raj explicitly deferred"),
            ("FIVE_CUT_ROADMAP", "User-visible outcome=A human-like Meera-led project explanation that a reviewer can run locally"),
            ("FIVE_CUT_ROADMAP", "Included=Meera primary"),
            ("FIVE_CUT_ROADMAP", "Included=Raj/Myra fallback"),
            ("CUT1_PRESENTER_CONTRACT", "Meera is the primary presenter, Raj is the first backup, and Myra is the second backup."),
            ("CUT1_PRESENTER_CONTRACT", "Required Cut 1 behavior=Meera primary"),
            ("CUT1_PRESENTER_CONTRACT", "Required Cut 1 behavior=Raj first backup"),
            ("CUT1_PRESENTER_CONTRACT", "Required Cut 1 behavior=Myra second backup"),
            ("STATUS", "`docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` — Meera primary"),
            ("STATUS", "`docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` — Raj first backup"),
            ("STATUS", "`docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` — Myra second backup"),
        )
    ),
    *tuple(
        ConflictRule(
            "CUT1_ACCEPTANCE",
            needle,
            "MPV2-CUT1",
            "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
            "presenter",
            "The legacy run contract changes from one selected presenter with two backups to three co-required presenter cells; all per-presenter quality and run duties remain.",
            "The six-cell owner contract replaces only the presenter selection order in the acceptance checklist.",
        )
        for needle in (
            "- Presenter: Meera",
            "Raj is first backup",
            "Myra is second backup.",
        )
    ),
    ConflictRule(
        "PHASE_PLAN",
        "The five-cut scope, exclusions, thresholds, evidence owners, and later decisions are defined only in `docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md`",
        "MPV2-SECTION-2",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "roadmap",
        "The sole-roadmap authority changes from the five-cut index to the certified six-cut V2 taxonomy while historical five-cut evidence remains immutable and explicitly migrated.",
        "The old five-cut document is preserved as a frozen source but no longer remains the sole future taxonomy after V2 activation.",
    ),
    *tuple(
        ConflictRule(
            "STAGE_ISSUE_PLAN",
            needle,
            "MPV2-CUT1",
            "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
            "duration",
            "The blanket 90–120-second all-presenter rule becomes exact presenter-specific accepted durations: Meera 117.981917 seconds, Myra 127.661917 seconds, and Raj 117.701917 seconds; the V1 Meera 90.000–120.000 interval remains preserved only for Meera.",
            "Presenter-specific accepted WAV authority replaces an obsolete blanket duration statement without weakening Meera or configurable local-default controls.",
        )
        for needle in (
            "Issue `#368` owns key-free intelligible local audio and requires the 90–120-second requirement.",
            "Accepted audio must measure 90–120 seconds",
        )
    ),
    ConflictRule(
        "CUT1_PRESENTER_CONTRACT",
        "Ordinary product UX does not label a presenter as an AI avatar or synthetic presenter.",
        "MPV2-SECTION-9",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "disclosure_destination",
        "The clean restricted archival-master exception remains, while invite-only Digital Twin/synthetic derivatives require visible disclosure and public/commercial derivatives require destination-specific visible and metadata disclosure.",
        "Destination-specific disclosure replaces the blanket ordinary-UX no-label rule without removing internal provenance.",
    ),
    ConflictRule(
        "ARCHITECTURE",
        "- retry budget of one retry for retryable provider or storage failures",
        "MPV2-SECTION-7",
        "STRENGTHENED",
        "retry",
        "The combined one-retry allowance is narrowed to zero provider-create retries during prototype and unqualified operation; storage retries and any later qualified idempotent runtime policy remain separately configured and retain billable-safety controls.",
        "The strengthening prevents duplicate provider creates without silently deleting the independent storage-retry obligation.",
    ),
    ConflictRule(
        "FIVE_CUT_ROADMAP",
        "Explicitly excluded=paid providers",
        "MPV2-CUT1",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "paid_provider",
        "The former allowed paid-provider operation count was zero; the replacement keeps zero default authority but permits only a separately authorized, bounded prototype operation before code, so this is an explicit scope change rather than a no-weakening inference.",
        "The categorical exclusion changes only enough to obtain real-provider proof; optional and disabled local/dev/test/CI boundaries remain intact.",
    ),
    ConflictRule(
        "FIVE_CUT_ROADMAP",
        "this is the single roadmap and acceptance index for Cut 1 through Cut 5.",
        "MPV2-SECTION-2",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "roadmap",
        "The canonical taxonomy count changes from five to six while every historical evidence record remains immutable and receives an explicit legacy alias or migration rule.",
        "The six-cut taxonomy replaces the old singleton without treating the global roadmap sentence as enterprise-only content.",
    ),
    ConflictRule(
        "FIVE_CUT_ROADMAP",
        "Gate / owner=Cuts 1/5 / UX/Legal",
        "MPV2-SECTION-2",
        "RELOCATED",
        "e017",
        "The Cut 1 accessibility leg and UX/Legal ownership remain unchanged; only the enterprise/public-use leg moves from historical Cut 5 to Cut 6, with its evidence burden preserved.",
        "The legacy slash-form gate is explicitly migrated so it cannot be mistaken for new Digital Twin Cut 5.",
    ),
    ConflictRule(
        "AVATAR_PROVIDER_CODE",
        "max_retries: int = 1",
        "MPV2-SECTION-9",
        "PRESERVED",
        None,
        "The disabled legacy default changes from one create retry to zero for the future qualified route; G1 does not activate or edit runtime product code.",
        "The observed retry-capable default is retained as a tracked implementation gap and cannot authorize provider activation.",
    ),
    ConflictRule(
        "AVATAR_PROVIDER_CODE",
        "retry_can_create_billable_job: bool = True",
        "MPV2-SECTION-9",
        "PRESERVED",
        None,
        "The disabled legacy billable-create retry default changes from true to false for the future qualified route; ambiguous acceptance continues to block duplicate create.",
        "The observed billable-retry default remains evidence of a post-proof correction duty, not authority to call a provider.",
    ),
    ConflictRule(
        "STATUS",
        "OWNER amendment `5500512956` authorizes twelve additional deliberate attempts and revises the total global envelope to US$8.00.",
        "MPV2-SECTION-8",
        "PRESERVED",
        None,
        "The dated twelve-attempt/US$8 authority remains historical evidence, but its present allowed attempt and spend values both become zero because every prior operation authority is exhausted.",
        "A historical funding record cannot be replayed as current provider or spend authority.",
    ),
    ConflictRule(
        "STATUS",
        "Four attempts and 253,208 microUSD are conservatively consumed, leaving fifteen attempts and 7,746,792 microUSD.",
        "MPV2-SECTION-8",
        "PRESERVED",
        None,
        "The dated residual balance remains historical accounting evidence, but its current authorized attempts and spend both become zero pending a new exact operation authority.",
        "A historical remaining envelope cannot be replayed after the owner declared prior operation authorities exhausted.",
    ),
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "The access-controlled clean master has no voluntary spoken, burned-in, or adjacent visible AI-use statement.",
        "MPV2-SECTION-9",
        "RELOCATED",
        "disclosure_archive",
        "The no-voluntary-visible-label rule is retained for the restricted archival master at the disclosure-destination contract; internal provenance remains mandatory.",
        "The clean-master rule changes only its explicit destination name and keeps its provenance burden.",
    ),
    ConflictRule(
        "MASTER_PROGRAM_V1",
        "NarraTwin adds disclosure only when a reviewed law/country/platform/destination/onboarding/publication-contract rule requires it.",
        "MPV2-SECTION-9",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "disclosure_destination",
        "The restricted archival master remains unlabeled unless required, while invite-only Digital Twin/synthetic derivatives now always require visible disclosure and public/commercial derivatives add destination-specific visible and metadata disclosure.",
        "Destination-specific mandatory disclosure replaces the former law-only trigger without removing internal provenance or unresolved-destination blocking.",
    ),
    *tuple(
        ConflictRule(
            "STATUS",
            needle,
            "MPV2-SECTION-7",
            "PRESERVED",
            None,
            "The dated HeyGen-first instruction is replaced after exact diagnostic rejection; unchanged GWM and HeyGen hypotheses have zero permitted repeat attempts and remain negative evidence.",
            "Later owner-observed rejection and the no-unchanged-rerun rule replace only the stale next-provider instruction.",
        )
        for needle in (
            "HeyGen is the recommended first compatibility test",
            "The next route is one optimized HeyGen Avatar IV diagnostic under a new exact package",
        )
    ),
    ConflictRule(
        "ENTERPRISE_REGISTER",
        "The detailed Cut 1–5 roadmap",
        "MPV2-SECTION-2",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "roadmap",
        "The canonical roadmap expands from five cuts to six; the historical source remains immutable and every former Cut 5 enterprise reference requires explicit Cut 6 migration validation.",
        "The six-cut taxonomy replaces only the stale roadmap count and singleton reference.",
    ),
    ConflictRule(
        "PHASE_PLAN",
        "the single Cut 1–5 roadmap",
        "MPV2-SECTION-2",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "roadmap",
        "The canonical roadmap expands from five cuts to six while the sibling numeric, MLOps, tenant, and evidence duties remain independently preserved.",
        "Only the stale five-cut singleton is replaced.",
    ),
    ConflictRule(
        "PHASE_PLAN",
        "Cut 2–5 remain gated",
        "MPV2-SECTION-2",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "roadmap",
        "The gated future-cut range expands from Cuts 2–5 to Cuts 2–6; no historical pass carries into new Cut 5 or Cut 6.",
        "The six-cut taxonomy replaces only the obsolete range.",
    ),
    ConflictRule(
        "STATUS",
        "the single Cut 1–5 roadmap",
        "MPV2-SECTION-2",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "roadmap",
        "The canonical roadmap expands from five cuts to six while every sibling quality, tenant, and evidence contract remains independently preserved.",
        "Only the stale five-cut singleton is replaced.",
    ),
    *tuple(
        ConflictRule(
            source_id,
            needle,
            "MPV2-CUT1",
            "STRENGTHENED",
            "presenter",
            "The original provenance/evidence duty remains, and its presenter-selection proof expands to three co-required presenters and six independent presenter/aspect cells.",
            "The six-cell contract strengthens the prior presenter-order evidence record.",
        )
        for source_id, needle in (
            ("CUT1_PRESENTER_CONTRACT", "registry and selection test"),
            ("FIVE_CUT_ROADMAP", "Presenter order and original provenance"),
            ("ENTERPRISE_REGISTER", "Meera/Raj/Myra order"),
        )
    ),
    ConflictRule(
        "PHASE_PLAN",
        "The intended end product is the human-like Meera presenter",
        "MPV2-CUT1",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "presenter",
        "The singular Meera outcome expands to Meera, Raj, and Myra as co-required presenters; multilingual, audience, Q&A, and enterprise siblings remain separately preserved.",
        "The six-cell owner contract replaces only the singular presenter scope.",
    ),
    ConflictRule(
        "REAL_MEDIA_HOSTED_DEMO_PLAN",
        "stale demo spend envelope",
        "MPV2-SECTION-8",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "budget",
        "The former $30-$60 target, $75-$200 planning ceiling, one-output default, and unspecified small aggregate ceiling become USD 0 current authority; a future operation requires an exact separately approved reservation.",
        "Planning amounts and default output counts cannot survive as reusable spend or create authority after the owner exhausted every prior operation authorization.",
    ),
    ConflictRule(
        "REAL_MEDIA_HOSTED_DEMO_PLAN",
        "stale two-minute media ceiling",
        "MPV2-SECTION-6",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "prepared_duration",
        "The old 120-second planning ceiling becomes a 300-second prepared-walkthrough ceiling; the current exact proofs remain the accepted 117.981917, 127.661917, and 117.701917-second WAV durations.",
        "The 120-second planning limit cannot contain the accepted Myra narration and is replaced only at the duration boundary.",
    ),
    ConflictRule(
        "REAL_MEDIA_HOSTED_DEMO_PLAN",
        "stale retry and regeneration allowances",
        "MPV2-SECTION-3",
        "STRENGTHENED",
        "retry",
        "The controllable create-retry and regeneration allowance decreases from one to zero during prototype qualification; polling an accepted asynchronous job remains a non-retry operation.",
        "The zero-retry rule prevents a failed, ambiguous, or rejected create from silently consuming another paid attempt while retaining every no-retry failure category.",
    ),
    ConflictRule(
        "REAL_MEDIA_HOSTED_DEMO_PLAN",
        "stale retry reservation path",
        "MPV2-SECTION-3",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "retry",
        "The qualification retry reservation path becomes unreachable because its effective create-retry budget is zero; any future post-qualification runtime retry policy requires a separately governed hypothesis and receipt.",
        "Pre-reserving a retry cannot preserve an otherwise prohibited duplicate-create route during provider qualification.",
    ),
    ConflictRule(
        "CUT1_T06_PROVIDER_LANDSCAPE",
        "stale provider package",
        "MPV2-SECTION-7",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "candidate_intake",
        "The preselected HeyGen, VEED/fal, and Aurora package becomes governed candidate intake with at most three shortlisted candidates and no selected provider before exact account, governance, quality, deletion, cost, and direct-API proof.",
        "Previously named candidates remain research evidence but no longer constitute an executable call package.",
    ),
    ConflictRule(
        "CUT1_T06_PROVIDER_LANDSCAPE",
        "stale 10-15-second provider fixture",
        "MPV2-SECTION-6",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "fixture",
        "The old 10-15-second excerpt becomes one uninterrupted sample-aligned 29.494-second canonical Meera fixture with two consecutive caption blocks and the difficult phrase frozen before generation.",
        "The continuous owner-selected fixture replaces the short diagnostic excerpt without promoting stitched prior evidence.",
    ),
    ConflictRule(
        "CUT1_T06_PROVIDER_LANDSCAPE",
        "stale aggregate provider spend ceiling",
        "MPV2-SECTION-8",
        "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY",
        "budget",
        "The unspecified aggregate ceiling becomes USD 0 current authority and any candidate call requires a separately frozen maximum debit and exact owner approval.",
        "An unspecified legacy ceiling cannot authorize a new call or provider package.",
    ),
)
@dataclass(frozen=True)
class ConflictTarget:
    context_sha256: str
    focus_start: int
    atomic_focus: str
def _targets(
    context_sha256: str, *focuses: tuple[int, str]
) -> tuple[ConflictTarget, ...]:
    return tuple(ConflictTarget(context_sha256, start, focus) for start, focus in focuses)
# Positional to _CONFLICT_RULES by design: every curated exception is bound to
# an immutable normalized-context hash, Unicode focus offset, and exact focus.
# Insertion/removal without the corresponding selector fails at import-time.
_CONFLICT_TARGETS = (
    _targets("467ae36f291706427f940b3ac60067d30711abe099229918c5ed95871bc1f795", (0, "Only one retry is allowed")),
    _targets("1db4464571a8f3c8c15f513372d1c40681abb0078e324e6a23d9f5fc26e5321a", (0, "- Create retries may run only when provider idempotency and billable retry safety are both documented in the provider config/policy.")),
    _targets("47a28b0b22162830f1ecc5d4f6f7c7c36d50bce17145ddb88094d0f0e305574a", (0, "Safe retries honor clamped HTTP `Retry-After`")),
    _targets("86ae272f9ee45fc1090aa1bd6579d86fd2bfc78596868ce1a700cebb821b78e9", (0, "19. freeze the sample-addressed 15-second audition excerpt")),
    _targets("958f47b9b0866191fa27f247cba8e15e297c5df9fa505d148f360454790b3d20", (0, "- US$100 total audition ceiling")),
    _targets("496eabe97a1ece12ad084da7a44b192b80a0944c0bea13d6da232cb33ac93a33", (0, "The US$100 ceiling applies only to auditions.")),
    _targets("36e009a786244eab4fa4e2f5c496fb3a7b9b1eccfcebbf792acce601f36e9ae2", (84, "decoded duration 90.000–120.000 seconds")),
    _targets("b54559c514285c18249b6a524a309a9d1adc83194d4a01e15aa2df6baea9003f", (57, "the service may apply `cut1-atomic-grounding-v1` only to the selected Meera narration when all eighteen canonical claim hashes")),
    _targets("77e94a3d60a08b975a80878c070548f015a9f76a40a10a26bfc55a3dec9a353b", (0, "Narration and TTS receipt authority additionally require selected Meera and all eighteen proposition-bound supports to remain current.")),
    _targets("478e3af92de82b785e9d9ca2714b1fb1d51ad72a66de94eef7469b0f1bc4097f", (0, "The aggregate requires exactly one accepted canonical WAV")),
    _targets("478e3af92de82b785e9d9ca2714b1fb1d51ad72a66de94eef7469b0f1bc4097f", (59, "one distinct accepted 1920×1080 MP4")),
    _targets("478e3af92de82b785e9d9ca2714b1fb1d51ad72a66de94eef7469b0f1bc4097f", (96, "one distinct accepted 1080×1920 MP4")),
    _targets("c5e59907222f9bfae1d01ace8323dbf2c271e04aebb53c08e52ec1d387fa0093", (0, "- selected presenter Meera only"), (33, "with Myra and Raj explicitly deferred")),
    _targets("40c883761e754371a8fb4c7809e926b9fa693243ab9c5a3c4ca1b50b8f12d3e4", (33, "A human-like Meera-led project explanation that a reviewer can run locally")),
    _targets("40c883761e754371a8fb4c7809e926b9fa693243ab9c5a3c4ca1b50b8f12d3e4", (119, "Meera primary")),
    _targets("40c883761e754371a8fb4c7809e926b9fa693243ab9c5a3c4ca1b50b8f12d3e4", (134, "Raj/Myra fallback")),
    _targets("c2b08baac65443a43aa9f8f1ae2751171680149630681797cf691bfb747b0bd4", (0, "Meera is the primary presenter"), (32, "Raj is the first backup"), (61, "Myra is the second backup.")),
    _targets("d8a2a703176dfc269ad61c186b7f3c8b55fbbef8616d79c687718352a74019bb", (48, "Meera primary")),
    _targets("d8a2a703176dfc269ad61c186b7f3c8b55fbbef8616d79c687718352a74019bb", (63, "Raj first backup")),
    _targets("d8a2a703176dfc269ad61c186b7f3c8b55fbbef8616d79c687718352a74019bb", (81, "Myra second backup")),
    _targets("7e8a9f33dc59c8a42bf5e2ff20da8cbdf4faa05351f74e8161fb2feb6f44af38", (56, "Meera primary")),
    _targets("7e8a9f33dc59c8a42bf5e2ff20da8cbdf4faa05351f74e8161fb2feb6f44af38", (71, "Raj first backup")),
    _targets("7e8a9f33dc59c8a42bf5e2ff20da8cbdf4faa05351f74e8161fb2feb6f44af38", (89, "Myra second backup")),
    _targets("22b3c26330dfff47303b1a33f384a83559470fcb34284dffaee5b273aeea4cb5", (0, "- Presenter: Meera")),
    _targets("22b3c26330dfff47303b1a33f384a83559470fcb34284dffaee5b273aeea4cb5", (20, "Raj is first backup")),
    _targets("22b3c26330dfff47303b1a33f384a83559470fcb34284dffaee5b273aeea4cb5", (41, "Myra is second backup.")),
    _targets("4e2a2f31e8ac1c69d03d70f933955246432e5ddd55b1aa0d0a2ffac50225e4ab", (0, "The five-cut scope"), (20, "exclusions"), (32, "thresholds"), (44, "evidence owners"), (65, "later decisions are defined only in `docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md`")),
    _targets("48d66509b16b83b5896a60d304442457eebc35249a146b27dec07ad4b6c0afa7", (442, "the 90–120-second requirement.")),
    _targets("ce9fa7ea598906e9a9971349cf1ae0d5030c0597e70044da9adc4387b22b7c1d", (0, "Accepted audio must measure 90–120 seconds"), (44, "shorter or longer audio is rejected.")),
    _targets("a4400a7c47069d7d257c1aaabfd0076d495a4291226f180739bd4586b0e13a2a", (0, "Ordinary product UX does not label a presenter as an AI avatar or synthetic presenter.")),
    _targets("dc2a1cffb400904250dadb1fcc417e22889ed2bbae9d34baf72f11940fda3d75", (0, "- retry budget of one retry for retryable provider or storage failures")),
    _targets("40c883761e754371a8fb4c7809e926b9fa693243ab9c5a3c4ca1b50b8f12d3e4", (423, "paid providers")),
    _targets("820550e7edeae5030abcb2983d50bceeab38c6964278953c27594eed44cb16e5", (34, "this is the single roadmap and acceptance index for Cut 1 through Cut 5.")),
    _targets("0fec52fc4987d239c4215154668a83c74d490f57141519c423b0e9fbf7c1aafa", (200, "Cuts 1/5 / UX/Legal")),
    _targets("24bcd3a9d9c4bf16d49d9a8414ce9c9e8a898bf132c64e31384770d123c37dc0", (0, "max_retries: int = 1")),
    _targets("b72690f5c1bbcd70dcb127e4e6fa7837c92c8d1cf6a5aa16080f7b3a93a758d2", (0, "retry_can_create_billable_job: bool = True")),
    _targets("19c5d7930a300b03a0840e74d1b80ab89569be3c473bf4bd6856f453d8ef082d", (0, "- OWNER amendment `5500512956` authorizes twelve additional deliberate attempts and revises the total global envelope to US$8.00.")),
    _targets("c623be3eb1f834929b1ee4b308ef41998d60749b8bc2036b0b925f11af0dd7bb", (64, "leaving fifteen attempts and 7,746,792 microUSD.")),
    _targets("06877a0823887543268c9832c698c810b3fdee0e659472be39bfd60d1738d24b", (0, "The access-controlled clean master has no voluntary spoken"), (60, "burned-in"), (74, "adjacent visible AI-use statement.")),
    _targets("3654d8e9b50002bb0ac9ebf66dd045a6cad113896294af4f4a2b093c77c54d8f", (0, "NarraTwin adds disclosure only when a reviewed law/country/platform/destination/onboarding/publication-contract rule requires it.")),
    _targets("471b97487f15d5b99800537361ee5e025f06620738d6d785768988627156337e", (0, "HeyGen is the recommended first compatibility test")),
    _targets("27de6a3b7b75d4866d4b1767181973e7666988b1774f6f8e890a5cf7fb4c9afd", (0, "- The next route is one optimized HeyGen Avatar IV diagnostic under a new exact package")),
    _targets("09da15cf2469eb3ecc7b6feb83d6546ad54fc1b276ad2400a1482eabf045ce9d", (0, "The detailed Cut 1–5 roadmap and requirement-to-evidence mapping are in `docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md`.")),
    _targets("07a3eeaef5bb21531edf992d858f78a3ddc1bfa82a46bab0b95d6ce54d8b1f5b", (0, "`docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md` for the single Cut 1–5 roadmap")),
    _targets("c8d01d87e93bb5a546ad06ece55236ae4f67d8eef130fadd3cf89e8ecc8bf684", (0, "Cut 2–5 remain gated by their listed evidence and the enterprise register.")),
    _targets("307cde6ce4266dd944dda0949d70335c6c676feef9df7a57acb440985884c43e", (46, "the single Cut 1–5 roadmap")),
    _targets("d8a2a703176dfc269ad61c186b7f3c8b55fbbef8616d79c687718352a74019bb", (111, "registry and selection test")),
    _targets("ea0f36553adaac840bc44d39c05814f134f6d118a229bfb28775c5497eb5c792", (23, "Presenter order and original provenance")),
    _targets("e49191e7301955757d8fce4d98c027ac3ae82f794293f334adb19b7ead3d0656", (40, "Cut 1 presenter contract and Meera/Raj/Myra order")),
    _targets("b967d03e86ba1e65aec7fe8d37d2d53bfc891cb2175bdc023fb2a8aed7300907", (0, "The intended end product is the human-like Meera presenter with multilingual delivery")),
    _targets(
        "1b70f8b921ec712c3ebd9bf23d240162ddf5f0cb315a1dee9311630d760ed4f6",
        (47, "target first-month spend is `$30-$60`"),
        (86, "`$75-$200` is an owner-approved ceiling"),
    ) + _targets(
        "6bfa7a00feb781208d440d1e461fb7a7b3a80c96724af5f1be43be76fd10b80c",
        (0, "- Target spend: `$30-$60`."),
    ) + _targets(
        "7633cb1a0a3d9336295ec50b444e102ef0d3a5a721bcb238dd41971acdd99866",
        (0, "- Approval ceiling: `$75-$200`"),
    ) + _targets(
        "a06dc761fadd4ace19f572ceaa28948299f3bc507303c84be980195c29796b42",
        (75, "`$30-$60` target"),
        (93, "`$75-$200` owner-approved ceiling"),
    ),
    _targets(
        "95225178caeac1177083026d1ae7419524c9573e477ba5ec5f027378f4891138",
        (0, "- Default generated media length: cap at 2 minutes unless the owner approves a higher per-run budget."),
    ) + _targets(
        "8f08a586c912b81cc04cc9f65e577c7ed6662da5aab633182ca4000c5a0c39cf",
        (77, "selected-provider estimate for max 2 minutes or capped characters"),
    ) + _targets(
        "1715a65dc8f102542f43149f64183f9542a91747378e264781a0480f7585a7d1",
        (58, "2-minute cap"),
    ),
    _targets(
        "946f3aba95bf279bfbc87fac79671a91ff2327b69c3949c44c2cbb31d16aae27",
        (86, "optional one regeneration per reviewer only if quota remains and the selected model-specific cost fits the target."),
    ) + _targets(
        "08aecd4a65e581f6fcb9f88205785a8da405cad4f6eb44300a289b884928cd63",
        (0, "- Default retry budget: at most one automatic retry for transient provider failure"),
    ) + _targets(
        "1a35eb02863b0b81dc67bb4d1121827581d21672d2323fce6caecbad4d93a934",
        (73, "one optional regeneration after viewing owner-approved artifact"),
    ) + _targets(
        "9641f1aab3428d5965bfd8e53239346bbf1e781b7d4ea27db7d679a4d756e795",
        (73, "at most one transient retry per provider job"),
    ),
    _targets(
        "9641f1aab3428d5965bfd8e53239346bbf1e781b7d4ea27db7d679a4d756e795",
        (139, "reserve retry budget before retry"),
    ),
    _targets(
        "2008ea3461512497f668880b4ec78e5f216c5402d6a9babcb3b8da6cda0a4911",
        (0, "Recommended first package shape after Gate 0 is complete: one call each for the available HeyGen and direct VEED/fal routes"),
        (130, "one Aurora quality benchmark when fal privacy is accepted"),
    ) + _targets(
        "a233364df1cea0ca3c2354b12736045e4bfa15709260f3a4a4677592be2fa40e",
        (0, "First compare HeyGen and VEED Fabric through fal.ai if their Gate 0 account/privacy stops clear"),
        (97, "add Aurora as the short quality benchmark."),
    ),
    _targets(
        "2008ea3461512497f668880b4ec78e5f216c5402d6a9babcb3b8da6cda0a4911",
        (226, "the same 10–15-second diagnostic excerpt and presenter image"),
    ) + _targets(
        "e4aa946dd5628126223c056de5d92f17b5ba1678dff92835a2aeb45b108af228",
        (0, "2. **Gate 1 — short compatibility smoke.** Use the same separately labelled 10–15-second diagnostic excerpt of an accepted WAV with the same accepted image."),
    ) + _targets(
        "e1d26b78c2f110b98bd9f46e174a5a18f6ed7f6c3ac456eea363925c88c31f73",
        (0, "The smallest Plan A experiment"),
        (65, "is one short Meera landscape diagnostic with one selected canonical frame and one complete sentence."),
    ),
    _targets(
        "2008ea3461512497f668880b4ec78e5f216c5402d6a9babcb3b8da6cda0a4911",
        (292, "a small aggregate spend ceiling."),
    ),
)
if len(_CONFLICT_TARGETS) != len(_CONFLICT_RULES):
    raise RuntimeError("conflict rule and exact-target registries differ")
def _conflict_rule(atom: Atom) -> ConflictRule | None:
    matches = []
    for rule, targets in zip(_CONFLICT_RULES, _CONFLICT_TARGETS, strict=True):
        if rule.source_id != atom.source_id:
            continue
        if any(
            target.context_sha256 == atom.source_context_sha256
            and target.focus_start == atom.focus_start
            and target.atomic_focus == atom.text
            for target in targets
        ):
            matches.append(rule)
    if len(matches) > 1:
        raise ValueError(f"multiple conflict rules match {atom.source_id}: {atom.atom_id}")
    return matches[0] if matches else None
def _validate_conflict_rules(atoms_by_source: dict[str, list[Atom]]) -> None:
    """Prove every exact curated selector resolves one unique frozen atom."""
    selected: dict[str, int] = {}
    for index, (rule, targets) in enumerate(
        zip(_CONFLICT_RULES, _CONFLICT_TARGETS, strict=True)
    ):
        for target in targets:
            matches = [
                atom
                for atom in atoms_by_source.get(rule.source_id, [])
                if target.context_sha256 == atom.source_context_sha256
                and target.focus_start == atom.focus_start
                and target.atomic_focus == atom.text
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"conflict rule {index} for {rule.source_id} resolved "
                    f"{len(matches)} atoms"
                )
            atom_id = matches[0].atom_id
            if atom_id in selected:
                raise ValueError(
                    f"conflict rules {selected[atom_id]} and {index} select {atom_id}"
                )
            selected[atom_id] = index
def _destination(atom: Atom, default: str) -> str:
    source_id = atom.source_id
    heading = atom.anchor.split("::", 1)[0]
    context = atom.source_clause
    rule = _conflict_rule(atom)
    if rule is not None:
        return rule.destination
    if source_id == "OWNER_PLAN_2026_09_07":
        cut = re.search(r"### Cut ([1-6])\b", heading)
        if cut:
            return f"MPV2-CUT{cut.group(1)}"
        section_match = re.search(r"## (\d{1,2})\.", heading)
        if section_match and 1 <= int(section_match.group(1)) <= 12:
            return f"MPV2-SECTION-{section_match.group(1)}"
        return default
    if source_id == "MASTER_PROGRAM_V1":
        match = re.search(r"## (\d+)\.", heading)
        if match:
            section_number = int(match.group(1))
            if 20 <= section_number <= 35:
                return "MPV2-CUT1-MEERA-CELL"
            return _V1_DESTINATIONS[section_number]
    if source_id == "FIVE_CUT_ROADMAP" and (
        "## Enterprise and tenant targets" in heading
        or "Cut=Cut 5" in heading
        or context.startswith("Cut=Cut 5 |")
    ):
        return "MPV2-CUT6"
    if source_id != "OWNER_PLAN_2026_09_07" and re.search(
        r"Cut 5.{0,100}(?:enterprise|commercial)|(?:enterprise|commercial).{0,100}Cut 5",
        heading + " " + context,
        re.IGNORECASE,
    ):
        return "MPV2-CUT6"
    if source_id != "OWNER_PLAN_2026_09_07" and re.search(
        r"Checkpoint(?:s)?\s+(?:2|3B|3C)", heading + " " + context, re.IGNORECASE
    ):
        return "MPV2-CUT5"
    if source_id in {"SECURITY_PRIVACY", "PRD"} and re.search(
        r"\b(?:Digital Twin|biometric|(?:face|voice|identity)\s+clon(?:e|ing)|"
        r"cloned\s+(?:face|voice|identity)|(?:owner|real-person)(?:'s)?\s+likeness)\b",
        context,
        re.IGNORECASE,
    ):
        return "MPV2-CUT5"
    return default
def _owner_replacements(atoms: list[Atom]) -> dict[str, str]:
    needles = {
        "cut6": "historical enterprise Cut 5 becomes new Cut 6",
        "presenter": "former Meera-primary and Raj/Myra-fallback order will be superseded",
        "retry": "The V1 one-conditional-retry allowance is strengthened to zero create retries",
        "fixture": "former sample-addressed 15-second audition fixture will be superseded",
        "budget": "All prior authority under the US$100 audition ceiling is exhausted",
        "aggregate": "The V1 Meera-cell minimum of one accepted WAV and two independently generated aspect MP4s is retained",
        "duration": "V2 adds presenter-specific exact accepted WAV authority for Meera",
        "paid_provider": "old categorical Cut 1 exclusion of paid providers will be superseded",
        "roadmap": "former five-cut roadmap singleton be superseded by the six-cut taxonomy",
        "e017": "Legacy E-017 `Cuts 1/5 / UX/Legal` will be relocated as `Cuts 1/6 / UX/Legal`",
        "code_retry": "Existing disabled avatar-adapter defaults `max_retries=1` and `retry_can_create_billable_job=True`",
        "disclosure_archive": "Restricted archival masters retain internal provenance and no voluntary visible label unless provider or law requires it.",
        "disclosure_destination": "Invite-only derivatives visibly disclose Digital Twin/synthetic media",
        "heygen": "Do not repeat unchanged GWM or HeyGen.",
        "candidate_intake": "At most three shortlisted candidates may receive paid tests for one unresolved capability.",
        "prepared_duration": "Prepared walkthroughs are capped at 300 seconds unless a later owner-approved contract changes the ceiling.",
    }
    replacements: dict[str, str] = {}
    for key, needle in needles.items():
        matches = [atom for atom in atoms if needle in atom.text]
        if len(matches) != 1:
            raise ValueError(f"owner replacement {key} resolved {len(matches)} times")
        replacements[key] = matches[0].requirement_id
    return replacements
def _owner_plan_adoption_ready(document_bytes: bytes) -> bool:
    return (
        OWNER_PLAN_ADOPTION_COMMENT_ID > 0
        and bool(re.fullmatch(r"[0-9a-f]{64}", OWNER_PLAN_ADOPTION_BODY_SHA256))
        and _sha256(document_bytes) == OWNER_PLAN_ADOPTION_DOCUMENT_SHA256
    )
def _owner_plan_adoption_ref(document_bytes: bytes) -> str:
    if not _owner_plan_adoption_ready(document_bytes):
        return "OWNER_PLAN_ADOPTION_PENDING"
    return (
        f"github-comment:{OWNER_PLAN_ADOPTION_COMMENT_ID}"
        f"@sha256:{OWNER_PLAN_ADOPTION_BODY_SHA256}"
    )
def _owner_authority_ref(replacement_id: str, adoption_ref: str) -> str:
    return f"{adoption_ref}#replacement:{replacement_id}"
def _legacy_enterprise(atom: Atom) -> bool:
    source_id, anchor, text = atom.source_id, atom.anchor, atom.source_clause
    if source_id == "FIVE_CUT_ROADMAP":
        return (
            "## Enterprise and tenant targets" in anchor
            or "Cut=Cut 5" in anchor
            or text.startswith("Cut=Cut 5 |")
        )
    return source_id != "OWNER_PLAN_2026_09_07" and bool(
        re.search(
            r"Cut 5.{0,100}(?:enterprise|commercial)|(?:enterprise|commercial).{0,100}Cut 5",
            anchor + " " + text,
            re.IGNORECASE,
        )
    )
# Exact normalized evidence contexts; hashes prevent keyword inference.
_OWNER_CONTEXT_CLASS = dict(zip("777fd8f0bb63be00df4a02119f75a1fc54b2ad57fb0b14a1a2f8ae8a13bf99d1 c5ee194d9450a18ea92f434e22e172eb0d5e046571d74c2edd2828e363cf6301 41d174e04ba5bc6db1364b18444b197e6a153f8fabe35bbfb12ddbd8d74b7de9 6c5703a0954198ee969b22f9ab853284d07f2fe77a1ae12608719678dacd9355 dda4eb60048e0f8b400b308f6150b96c929107a64f191c1e1b437156c8955ef1 b6a8849dbb2320aa92f891ef3fe5ded80935da8c45f69dd199386cd3a0f3c144 f8666600d48ee47c0f2059aa8ab134976dbe41d60fc294f5c28c998abf6ccd90 4ec6c4106d4b60a81ce5327d2fc58c4ad82d56478f3c14fead47c1eb928cc3c0 db0cb362d1d319c2cf8c20eba105cc270386a585e45ad7efb9fd038acf20f26c".split(), "AUTOMATED_RESULT USER_OBSERVATION COST_ESTIMATE USER_OBSERVATION COST_ESTIMATE COST_ESTIMATE COST_ESTIMATE NORMATIVE_REQUIREMENT NORMATIVE_REQUIREMENT".split(), strict=True))
_OWNER_FOCUS_CLASS = {
    # Mixed contexts classify only the exact focus coordinate that carries the
    # observation or estimate; sibling technical facts remain evidence facts.
    ("a3d0bbc33e28d1ab8bb49ce6088ade57a9ca5585e01dd6b846180ebdb4595092", 29): "COST_ESTIMATE",
    ("44d6f818c7a42e24df019791be18525755c2ef78857e759165539ad3c2042ab8", 106): "USER_OBSERVATION",
    ("f5e42852fdab183388fbf6324075224801e64ee6833d2152ea69519d5780c592", 102): "USER_OBSERVATION",
}
_OWNER_NORMATIVE_CONTEXTS = frozenset("f09e61c9711cbb05060e8396a04e9fb0fd87c30a2361063874ae7d803ba76e0d f961f5f63a3dbe827bc5198439e38af5658a7c064e7babf9ca98cb4d84c7c357 97c122cd02843e41690136c0afca9c2d2cd4584e2426c72da90aec5b7d073ae5".split())
_OWNER_NORMATIVE_FOCI = {
    ("87df208e6ae52f7ceb289f3e6be8544fdafa0dca46ccff1b3bf0a449beaf683b", 166),
}
_STATUS_NORMATIVE_HEADINGS = ("## Canonical Current Product and Readiness Contract", "## Source Of Truth", "## Maintenance Protocol")
_STATUS_HISTORICAL_HEADINGS = ("## Change Log", "## Pull Request Ledger", "## Completed Work", "Heartbeat", "Historical pre-merge", "completed state", "merged and closed", "> ## Issue")
_STATUS_NORMATIVE_CONTEXTS = frozenset("884b3cb89c50ba4c6cb5c1f34e124f14a0e3b64292fbe412120c7f7542e5c4df 54fd34751d1bda9ea692cf8d059bd6d0e88654e5d71f186b35ac6c9c7839cc44 299a0bb082edaa18e023769f3698de53dab3b58b3ca11b33a33d799f53ff71f1 6e322d80d6f3948229fa793ff028d390f5d92b921226fa3f181a2dd815e9807c afddfa2c2ba577d8ed281efbae49cb6113b74fbb9893e406eaba04b547f782b4 0243ac9faaa4e0eab52e6d2aabc1763273025a05371f5ef7f0ca36e13440ea29 6b8d309892a73662a344ea422906793fa299cdc28d19dd0e02a17f9a8a4fe8d5 7b859dd344e4bb69a02b94c7ea75f9f753ccbbc1630c0fad47ca13956a750f68 9b7d131e37a4e5ac35db41ccbbb54572ffcacc7a828f15bb493bbb128b8e0a00 3eed1d9abf9c7d01b6555b28fd5a3b439c3e43223d9b75c0a849b7ee88ce26be e7894bae1bbd510cdf4cc345000625f022ef582c18708bd590ac437f43aaa348 823908680176905eb86dba617245b8283670318eef61b7ca1f48af8a05edad65 3b11a49a5f2c98a7183ce9e67c564119821c1e03b17c0f98cb562a41db393a7e 7127e1a7e3c53a6feaf8a672ac6169307c6dadf4f80a4a6e0f7172ac00e565fc d3f52b21e8ccd60b8c975f2bc12fe19b75432f2a1ea5f1844f741491efa2f024 b52e5f25272414a4e063cbfdd0e0998e9db31022c40cdd434df746fd75de408d a583b004d017ad46c53bc572c4ffc170041f320ae209dbea532452de4f753800 f8a5efbccc0fea923b201d8dcf250bdbba439c09446c3b90a5791fc5abaa35b1 5d78a5cedae116de31b01d6370a563e257dab189ff530e93139a57fce78b701b 621cf065081533ce9590c444dd23bb84c2478fe531ee0a2bb02904947d0d89db af607902dbd396bab7d6983c8aaa26cf34a2610fa66369c4eb38d30906fc556e 35901c231d4fc69671a28e1a9932ddf9092a917d587a218b2f104216d9b91a45 decd565e333340f407bb9cbeb0c6cb89b3fc50e968ad38c8e14765fa9c15963c 7d7bdb2ffadede689a70cbaff6b652631718a3baa3a3f922d21eb1d52e634202 3619b4e147f50a13d3fa6ba0d7f48d16f3ed40ced697b2293f0618703be312dd 1319a26067a66e03909458c400cc9f0b84e362d6cf3a4375beb7273fcba6a95c c1286e57b91e589f8e224d7f00ad1a22e552a214364071ede620751cd0f1700f 5222a3b40007632666234e6c08b174c57c8834112e7649a09999620a14ed72d4 67e04c07dabcf32de2507169e5c8cc19f40e7aec48e5f69b268a5931f85916b0 d2696328adce0748631b7317384260aad1cfe6e82532fd161418a70b05abba35 bdebda406ba8c99d84b7755156957b29dec9cbb913f2fc2ea7a9d6b334457533".split())
_STATUS_NORMATIVE_FOCI = {("7ba675f0fead80ddb54b871d2abb81cb79f0b279b386f459fe96d533b063fe37", 119), ("b590c5203b7f290fbb493614a3ee9629d70f5af00e4722ca242b43299d892b2b", 119), ("67443ec19d0694f35d9025b4a0a0112e3f31d24f97865eb0ef19868b815cf16f", 117), ("f069ef5a129fd8b2130110c6c516b2900be44fb03eaa27359faa238888ce03a7", 106), ("a78e087e32c3bced1f007fac8223c5b6c1b2839f9183e8eabf132fb9d7aa0f4d", 124), ("8c57470ec98fdb21b59e5b10ac6d202ef7f34322c2678514d51031b7fb0c6253", 235), ("c8a9d58257448d2efb1f6091616960f75f5234905b3b9afb204eec8e08a64dd4", 115)}
_EXACT_CONTEXT_CLASS = {
    (
        "SECURITY_PRIVACY",
        "3c67e476663d4fac7a29176acdacaa1e6bbe76d7ab11358b1f481b0a563c26bd",
    ): "HISTORICAL_FACT",
    (
        "REAL_MEDIA_HOSTED_DEMO_PLAN",
        "43c09faffa42f375c8e3977872fd935d0b2dd5e15187049478ead5bc511c4412",
    ): "CURRENT_STATE_FACT",
    (
        "STAGE_ISSUE_PLAN",
        "23db41ccfaa4ed35b06ae263e76b02de80f85b9480be8b3233c680e139e2c9e1",
    ): "HISTORICAL_FACT",
    (
        "STATUS",
        "f6d9ae2f99def730abeff4fafb7da1854aec06b54cd87123acb75ba64f12c354",
    ): "HISTORICAL_FACT",
    (
        "PHASE_PLAN",
        "f6d9ae2f99def730abeff4fafb7da1854aec06b54cd87123acb75ba64f12c354",
    ): "HISTORICAL_FACT",
    (
        "STATUS",
        "d02336122e3e2474bfd239e3b10cfa8372ade9671524056d7f931815580ed55e",
    ): "HISTORICAL_FACT",
    (
        "STATUS",
        "c0ee35dce13a070c06fde33ad62df7052f19f8c5f51df3d591ba91d5104f72d3",
    ): "HISTORICAL_FACT",
    (
        "STATUS",
        "8e6dd0483c31ddf55856b9fb79d60c3844bd313af0d006eb534f1013c91e033b",
    ): "HISTORICAL_FACT",
    (
        "OBSERVABILITY_COST",
        "461562dae3a6b7deff94b391d7d6e79e02946b9b2a502f9f3f6a58fe3a0d2bc9",
    ): "IMPLEMENTED_BEHAVIOR",
    (
        "OBSERVABILITY_COST",
        "e990b865241062b6048d760bf7f32308e3305d5f3db3b5c50fce1939da9d9f64",
    ): "COST_ESTIMATE",
    (
        "OBSERVABILITY_COST",
        "14bf13e0ffc918cf3881a0ba808bc8f9cafb56a52e199b171009c5ea065d855a",
    ): "HISTORICAL_FACT",
    **{
        ("STAGE_ISSUE_PLAN", context_hash): "HISTORICAL_FACT"
        for context_hash in (
            "cb012d23ac2d71d8d75114e77bbe551e6b9a53f8f640c02eb9e7213accb60e4e",
            "82182bb7049aea8e4b5d0cbcf0c261e6c1f1166029a2ea68bdb23fc6ed15b079",
            "6722e1b28f9be0e92c9d53e35050043d3138fac89a14456de5048091283b2af3",
        )
    },
    **{
        ("CUT1_T06_PROVIDER_LANDSCAPE", context_hash): semantic_class
        for context_hash, semantic_class in (
            ("fc7615001ad137f613bd856747bd41707f368c636d021f256d3aca5c50319926", "CURRENT_STATE_FACT"),
            ("7e8023231eb0198a9145fd9fb9f8839eb80103ca702aa7486dce7350b38d998e", "COST_ESTIMATE"),
            ("51f4634e77ed2675c0d12d740a110b4420705f50dca7351627786fd891fcc369", "COST_ESTIMATE"),
            ("3c089492a806ab8f8806f77192146db59f72ee2976065bdae2e5b793a4569e03", "CURRENT_STATE_FACT"),
            ("af6ab6864870881c6d3426584d29cb2b8fd5d1f7316cc49fe9ccc17018b727f2", "CURRENT_STATE_FACT"),
            ("aa4ad2aeee38886b9116108f3a29e2ef2cfd3c68b8dda360b2e027bd8e20c3f1", "CURRENT_STATE_FACT"),
            ("cc26df47633e42a486777e6896031ea25ac5bbc759a6bfb455b892278fa4db80", "CURRENT_STATE_FACT"),
        )
    },
}
_EXACT_FOCUS_CLASS = {
    ("ADR_0013_CH01_MIGRATION_BASELINE_RUNNER", "51bb8f5484d4cb4d47a716fc92b7737ce36ce59fb4f19139c2bd1b32de54be74", 0): "HISTORICAL_FACT",
    ("ADR_0013_CH01_MIGRATION_BASELINE_RUNNER", "51bb8f5484d4cb4d47a716fc92b7737ce36ce59fb4f19139c2bd1b32de54be74", 78): "NORMATIVE_REQUIREMENT",
    ("ADR_0006_STAGE8_RELEASE_HARDENING", "9c3212c947a2874b0e6510345225a69f96e4005ebc96c14b8782b9710f4da8a5", 0): "IMPLEMENTED_BEHAVIOR",
    ("ADR_0006_STAGE8_RELEASE_HARDENING", "9c3212c947a2874b0e6510345225a69f96e4005ebc96c14b8782b9710f4da8a5", 71): "AUTOMATED_RESULT",
    ("SOURCE_RELEASE_READINESS_REVIEW_70CA1F2E", "93603a442b71dbabf88f1d4dfba1a1824490dac44816fe3d02d53ebf0e245bbe", 0): "IMPLEMENTED_BEHAVIOR",
    ("SOURCE_RELEASE_READINESS_REVIEW_70CA1F2E", "93603a442b71dbabf88f1d4dfba1a1824490dac44816fe3d02d53ebf0e245bbe", 128): "NORMATIVE_REQUIREMENT",
    ("ADR_0056_CUT1_GOOGLE_GEMINI_TTS", "4c841fe50a9553f83b47c903a7fbd2847b50b0f37a171882029396fa4d41de29", 0): "CURRENT_STATE_FACT",
    ("ADR_0056_CUT1_GOOGLE_GEMINI_TTS", "4c841fe50a9553f83b47c903a7fbd2847b50b0f37a171882029396fa4d41de29", 60): "NORMATIVE_REQUIREMENT",
    ("ADR_0056_CUT1_GOOGLE_GEMINI_TTS", "172bb333c0125c9583009236adef2bd21e2fc372269817f724944eb355e56147", 0): "IMPLEMENTED_BEHAVIOR",
    ("ADR_0056_CUT1_GOOGLE_GEMINI_TTS", "172bb333c0125c9583009236adef2bd21e2fc372269817f724944eb355e56147", 98): "NORMATIVE_REQUIREMENT",
    ("ADR_0069_CUT1_PRESENTER_DERIVATIVE_READINESS_BINDING", "9d9f9426006b88bd78bfd26c700af745f4393ff3bb0c26bc71598b786edbdf3f", 0): "NORMATIVE_REQUIREMENT",
    ("ADR_0069_CUT1_PRESENTER_DERIVATIVE_READINESS_BINDING", "9d9f9426006b88bd78bfd26c700af745f4393ff3bb0c26bc71598b786edbdf3f", 90): "CURRENT_STATE_FACT",
    ("ADR_0069_CUT1_PRESENTER_DERIVATIVE_READINESS_BINDING", "9d9f9426006b88bd78bfd26c700af745f4393ff3bb0c26bc71598b786edbdf3f", 138): "NORMATIVE_REQUIREMENT",
    ("STATUS", "5d78a5cedae116de31b01d6370a563e257dab189ff530e93139a57fce78b701b", 0): "CURRENT_STATE_FACT",
    ("STATUS", "5d78a5cedae116de31b01d6370a563e257dab189ff530e93139a57fce78b701b", 33): "NORMATIVE_REQUIREMENT",
    ("STAGE_ISSUE_PLAN", "23db41ccfaa4ed35b06ae263e76b02de80f85b9480be8b3233c680e139e2c9e1", 125): "NORMATIVE_REQUIREMENT",
    ("STATUS", "d02336122e3e2474bfd239e3b10cfa8372ade9671524056d7f931815580ed55e", 53): "NORMATIVE_REQUIREMENT",
    ("STATUS", "d02336122e3e2474bfd239e3b10cfa8372ade9671524056d7f931815580ed55e", 162): "NORMATIVE_REQUIREMENT",
    ("STATUS", "c0ee35dce13a070c06fde33ad62df7052f19f8c5f51df3d591ba91d5104f72d3", 167): "NORMATIVE_REQUIREMENT",
    ("SOURCE_TRACEABILITY_7B284BCF", "d7d4802108035e4755df2238a4c9f456ccc0e3a1a82aa0a672247846b66dfb0b", 1274): "CURRENT_STATE_FACT",
    ("SOURCE_TRACEABILITY_7B284BCF", "d7d4802108035e4755df2238a4c9f456ccc0e3a1a82aa0a672247846b66dfb0b", 1304): "NORMATIVE_REQUIREMENT",
    ("SOURCE_TRACEABILITY_7B284BCF", "561583ede14d521aadd210164cb70a9985f0355d9c78fe38998718e2d7aa838d", 176): "IMPLEMENTED_BEHAVIOR",
    ("SOURCE_TRACEABILITY_7B284BCF", "561583ede14d521aadd210164cb70a9985f0355d9c78fe38998718e2d7aa838d", 193): "NORMATIVE_REQUIREMENT",
    ("STATUS", "05c68405eabd1c3f8a22998678c116c07365616a8866933e07ba021961fb9864", 159): "HISTORICAL_FACT",
    ("STATUS", "05c68405eabd1c3f8a22998678c116c07365616a8866933e07ba021961fb9864", 282): "NORMATIVE_REQUIREMENT",
    ("STATUS", "05c68405eabd1c3f8a22998678c116c07365616a8866933e07ba021961fb9864", 357): "NORMATIVE_REQUIREMENT",
    ("SOURCE_TRACEABILITY_7B284BCF", "bc70a38f50f156ebd0cff87c36f195e4a3036c3aee60dfafcb1c6ab2a2e48f3d", 204): "CURRENT_STATE_FACT",
    ("SOURCE_TRACEABILITY_7B284BCF", "bc70a38f50f156ebd0cff87c36f195e4a3036c3aee60dfafcb1c6ab2a2e48f3d", 232): "NORMATIVE_REQUIREMENT",
    **{
        ("STATUS", "8e6dd0483c31ddf55856b9fb79d60c3844bd313af0d006eb534f1013c91e033b", start): "NORMATIVE_REQUIREMENT"
        for start in (219, 325, 389, 409, 435, 463, 522, 532, 539, 558, 574, 595, 620)
    },
    ("REAL_MEDIA_HOSTED_DEMO_PLAN", "1715a65dc8f102542f43149f64183f9542a91747378e264781a0480f7585a7d1", 0): "CURRENT_STATE_FACT",
    **{
        ("REAL_MEDIA_HOSTED_DEMO_PLAN", context_hash, start): "COST_ESTIMATE"
        for context_hash, starts in {
            "757499f298d44e993eb5d2cfabc1626125ce0a31b894b1f6fe6e8dc823cdb269": (69, 118),
            "9ef5c7610bac736d31e818e6ced8e6eb65f18af22e4744a0735243308aa51227": (55, 104),
            "03e9814e949a429536b2086bfa575461d9da89dbdfbc1424c7a36dfac01a84ed": (54, 101),
            "df72ce9909aff9fe512148ec8f2b0357c83ca77af6abbb2d933fa0fa76dcb42f": (59, 108),
            "7fc40181ef48c9c28662654988a864ab2b46d35e79077163308e4cd83925c9e7": (73, 122),
        }.items()
        for start in starts
    },
    **{
        ("REAL_MEDIA_HOSTED_DEMO_PLAN", context_hash, start): "CURRENT_STATE_FACT"
        for context_hash, starts in {
            "d6f460ab6842c8688986367fb2281a386c382fe4d3b6f91bb8576f97a749d2fe": (54, 100, 109, 133),
            "be933999d386a2540f3bddffcdc7aa3a040ea7843dd7f338b5c5b7eef832935a": (37,),
        }.items()
        for start in starts
    },
}
_REVIEWED_NORMATIVE_REQUIREMENT_IDS = frozenset(
    "MPV2-" + suffix for suffix in """
D4C6D50703909651C2DC E4403B5208E6B8CB6240 803BF56BAE6FF419723B 7D6107A5596FDBDE2F5B 1286D2A00896453FBB0E 615608BD92DD6AC173FF 8B31346351ED2A7310E6 3BFE526C12B61B24E699 7CAC70478D4FCF04C112 24769FA70F2EBF0636D3 1341E80EBEFA9E6A5294 1E1A8881E0FBD6B072F5 14BFF28D016A32AD31C7 0D2C918C41D0C46C01AF 582DE098BFB50A54F8D1 20C2E2CB6A75A137BD41 356230BD89DBAC0947A5 7488A709B64B27F0DE93 7D1F2541B980BC75FEA5 F29C57BFA4ED059F358C BA3353C4A0B52A67B592 1CB9F43CEFA2B2452FA3 866331F8ED47F88510C1 D5A86314140DCF89B428 3E3684ACCA3E9BFE432D 96B6B230BD65AC977E18 4BFD666BB10B901F2603 243B2B73C6287D4418FC 5350700C906FCF6FD6B6 96567E193B75E27476D6 8D7DB10D87941837205D 909A72C093CCE374CB20 B571B40EAFB00B5EBCFF 0E02A6B124EA4F8C7027 B137D68C8E65BCED3652 ADBF999C0D509EBE4110 C0C8A150BC1F9CF643AC 740D9DE53A25EF964361 34E849FA4FAA53DE5661 70738CBB5B6284EDA409 4BC9B0369312424BDE61 B88B5E68FECEB51ECEE5 47B6E0F8CC6FBE8D3C94 1012A867D90659979672 5C4F22B0B8588A659C7E C8D6DCD4727E5CD92E28 4D0B397F1D57C559A44A 85D2642EF7420F2ED7B1 7BA09695E7AF93663683 59CDE6A41F2342B0853F FAAF0A729199420EE8A9 6D3CB21E4B79F0914C35 1D9C673C479E6DAA8DC0 DFBA4DF9BBDD9D356CBD CB9D1ED4953FD95F3330 7942470C5B16A5A5192E C3AA9F5E4B6A97C6E086 C8322B78DE8B11B0F794 FE2DF7632FEC5D02048D EF9CA0D7A590804DC9DD 23D75E3F0B56787593F6 6148825EB218AF24480C E287038C61F57AFBFB33 F329FE5CC59786A69329 CF1506D7C7BAC3998B22 7395759517D9A61B498D 9FB0EDA30C50BD911B19 432A74B6ACC0654429B5 EAD8094AAEE2969F98F6 80CC7F210CADFB55AB8F 483C9005CA65A8628A3F 71E163891030C509226A F00FF885E7A5BAC806CA C943E1FFB82C3A2FECB9 0A1D29C0B192B42D766B 3A7AB6FA57D80E874548 3C96231437BBF2E12812 7CA806B7BA574A83538F 5A41CBBE75FE51AF6433 7F05D842E5FE6335F040 1E63CA0E8AE96D9DC954 DED3294C17B78A450D29 D12F5A7CB7FC347A9B99 DC1DB7059EAC9270768C 51ED3DB54CAB03205025 FC77D02EA37A2300471E 156662793ADB949299F2 3AE7429BDE20A3E5FFD3 F2F440F049C0AB1C51BA 634F13B0B8FE36DAD7F4 51847AF2EEE8B235D5C7 FD53709F9CD9039B8082 6CC4D9208C1DE240F616 3844A35470E72A2CCDD9 4FC34F4693CE477A1766 D4452C6F8F2511D54902 31FF1D8E9537902BCA38 4E5122115963F6918F01 2CEF50280DF56594F02B B8A0F30D7CE23048BFD1 F4ECC2CE81780C1C70F4 801B0C39A7A6ED23AF05 231A69BE95F4F3DF0AFF F07F79084BDFE0BB8CE7 10EAC6736536C894F255 084409ADB4D71CF9C1A6 77EC85768DBE00E65E07 17742BD154B008874755 8AD1134B84E5FC44576A 3C91C124E4353C3FCE1A 6171E7F774BD4BC94EA0 91823FE0BA0A18D535E5 6C81E1716AA310836E66 FC8F283513EA8C45D0BC A1C6003BB1BD62EB6185 8AFB67FD6199C59CB250 F9B6D953EF79EB3698D4 246FA22E9A305D842B5E 00AD82152CE8371FD815 2AE57C1DDF56865A10E6 6168F92E6F87D21D88FE FC743E16118ACF8424F3 F8FCB7D9FFF476BEDD79 906A13EC9859902A1137 AA31A4BB1C529B8C876C 051196228420F7B13EC3 312555BF71C83B214387 9DAE484C292E844DC3BE 9E1D7CC5F4445504E77B 7E0AA6A1050B5003F663 1C72AE29ABEAA173C9E0
""".split()
)
_REVIEWED_NORMATIVE_REQUIREMENT_IDS -= frozenset(
    "MPV2-5A41CBBE75FE51AF6433 MPV2-7F05D842E5FE6335F040 MPV2-1E63CA0E8AE96D9DC954".split()
)
_REVIEWED_CURRENT_STATE_IDS = frozenset("MPV2-9A90C15F1DC6BA9C3760 MPV2-8EB1658AC249240ACA9F MPV2-F51B0170CE4DEB8E6DE4 MPV2-308B847D98552CA9257F MPV2-9527A6B6FC8829207AD7 MPV2-473C5AF158B4555D0AEA MPV2-C646D6D83878D0CDC226 MPV2-AA75609211ABFD96A19C MPV2-4C5FCBDB48F3EA26F921 MPV2-86495A5996499F8BD281 MPV2-D8D151D309628E497833 MPV2-20D6F4182C70BFCF265B MPV2-058A9D9D3F38FB9623B8 MPV2-E771B80430F2206577DA MPV2-B023F1178D95FE07A4C3 MPV2-E76B5C84B423D2D776E6 MPV2-FD1B240A8EFB1124874B MPV2-F45CBDE2F8FFDEE33AFA MPV2-A4C7429CF4BA2B935687 MPV2-170910F747BF71919D53 MPV2-6B47A07C8B71E13C0B93 MPV2-1E5CFBE52820D8D7D7BC MPV2-3EF788E07BC381E754C6 MPV2-EE1EC6F015246D8F03EC MPV2-313E7977214D90485076 MPV2-3CB35494DA57D4C7DE7D MPV2-1ABAE9BF055A4BCA7684 MPV2-ED0CD51B906315AA8D7D MPV2-289EE4279249A9357994 MPV2-44FC37A358C47DDAD4EF MPV2-DCF467A9875B01C906C4 MPV2-D7830BCE46B0E5926B91 MPV2-FE21A1E7EBB63935B46B MPV2-51639C3B9894AB568C4E".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-61A152015FDAA83803DE MPV2-A418E2606183AC268529 MPV2-8E713AA88F9A765BA6C5".split())
_REVIEWED_HISTORICAL_IDS = frozenset("MPV2-F58F4579A398AE494ED6 MPV2-AD64C9BC53F5D0C95402".split())
_REVIEWED_CURRENT_STATE_IDS |= {"MPV2-906A1A00A0F238093C3A"}
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-C7A9E37D10BE6B67CF75 MPV2-C9F9D3E0F6CEE5B56ED1".split())
_REVIEWED_AUTOMATED_IDS = frozenset("MPV2-027D9483900841289C50 MPV2-1C8888CEDAEBEB29005A MPV2-AF832C70B91DD0C6D676 MPV2-455F22A7F3C3049BC209 MPV2-DE486F6DE3C99BEAF291 MPV2-3A646CE09F0669F83BD1 MPV2-CC297D72BFBE55971B94".split())
_REVIEWED_IMPLEMENTED_IDS = {"MPV2-48CE841A1EB771598E52"}
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-D875402EDD76101470CE MPV2-DB8E3367586912546A2C MPV2-525047FF1DEC7C20E000 MPV2-84BF80C39002B4A47469 MPV2-976AC94EAAB045531039 MPV2-3C9E357757D97F126C2C MPV2-136B07A9E42C4532C068".split())
_REVIEWED_AUTOMATED_IDS |= frozenset("MPV2-188AF7496BE21E27C7CF MPV2-5320FDCF8F264A6A182B MPV2-573325485FDB8B0DBC34 MPV2-24FAB2FB4C986014E01C".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-B2D4E2A1B420DAA15E96 MPV2-42C748289A07B0C91295 MPV2-4CE428B3906CC29238BE MPV2-77DC00F2DD82F9F60DA8 MPV2-6918F5D8487750956036 MPV2-3094435F4D0504D809EB MPV2-13E971C4BFFDDEF28C0B MPV2-F90ECEC5F9E0F65815A1 MPV2-B57388514D1FF452E460 MPV2-DCAA73B898AD8C48F20D MPV2-8D2790B47F238B777C7A MPV2-8D3F3E89F50344D95F5B".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-8CBCF641D0C785F7A6F8 MPV2-C993A608B7F07706FA1F MPV2-ABB669B62C985241733B MPV2-4D6C98B16B65460044FF MPV2-FA4F17423C0B1BA46DBA MPV2-68C300C014EFC7B867D6".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-865420E5FE6478E15194 MPV2-266E2763C20A90A6B779 MPV2-2E95B5A855B3FFC42D44 MPV2-57D8D1DF7D162655AD80 MPV2-77F69B5AB4DF4F51C14E MPV2-A3CA9716923F13798FE4 MPV2-F19D6EC741D6C1A36A50 MPV2-0DC3310497C3E9E6DBCB MPV2-30D3848DF474EEB4A3EE MPV2-07428BD22DA42B74CFB2 MPV2-52EBBC6AFCBD58A7F91A MPV2-FB5A33500349E5F5C9AF MPV2-2044694A397DBDA8020D MPV2-CB5D033F49C9492FCA5E".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-4971414841589C5C25D1 MPV2-503D41FD940376601523 MPV2-301FD7FB5B71BF981AF5 MPV2-576AD6D9E83B913EA08F MPV2-594842B36DC4AE5DE108 MPV2-1B02B200A5A151A552A8 MPV2-FC0C0E4AE074239F91C8 MPV2-DE32BADB5D6472B89425 MPV2-AC490074BE1E8B80D0D9 MPV2-7F3EF7FA9262BABA2BD0 MPV2-AF41F2E498A4B3BDB8AE MPV2-C0CF6096ACD6321FEEF2 MPV2-D477999D361FA94A570A MPV2-7EA9710BA688AB552B84 MPV2-D2A5E3DAEED6B64070F9 MPV2-FA7799C52A884EBDACED".split())
_REVIEWED_AUTOMATED_IDS |= frozenset("MPV2-38CA7B41DF7D33D5C339 MPV2-0B8F801BC8F17CA49E03 MPV2-07215B3F1CF9C6CE77A5 MPV2-5E4C47E1FA0FA4A7C655 MPV2-571AE067B59767809AEF MPV2-CF6A31F590DE8D681427 MPV2-735591E61605F52E265A MPV2-EAA58A8598FC3C91B300 MPV2-51502D40AF0AE01F5824 MPV2-CC04A82568A92C8B997E MPV2-442EEAEAF035692E5A99 MPV2-D8BF0DE21AEDAB0D0D7C MPV2-25755221975E027E5115 MPV2-E6BB695D94506646EE3F MPV2-933E4F1A36178968C2CD MPV2-CBB19B0D42AB929AEE4D MPV2-4CAC3A1F7A62D1EB29D0 MPV2-647EE42B39B96E637491 MPV2-BAE4AC4564524344E2BA MPV2-43FE4FBF94CB59566C7E MPV2-7F10048060A8EF0E1203 MPV2-5E978100A73C967CFED0 MPV2-8D9E3B4AE31D4DB51B98 MPV2-663FF946E6ABB9DF9C26".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-782F5606C5D9A2046967 MPV2-1B6CE74CC69731FE12D4 MPV2-E8D25148728211B382DE MPV2-A4A854C4E13A1CB055BD MPV2-4A83F42D5098DF332211".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-0C114E72479C3108B87B MPV2-43D6F9AD3B2E5037C383 MPV2-3FEF925BF11479BBA63B MPV2-265BCA5C6CB385D0BB93 MPV2-54A7B6B72B6133742155 MPV2-CAF6B4E61BB1F7EC1635 MPV2-9FB65B815FC94AA6BEBF MPV2-0C75B135986BCA82BA92 MPV2-4DCC1714CD32B372170E MPV2-8A2F7D7556BA684404E7 MPV2-B4E1047C813FCB90AEF1 MPV2-309F95589592FEFB3BCA MPV2-C4B24DC00C1883F97F35 MPV2-4BA486D5A3C339BF203C MPV2-756BDBCD51BA073857B6 MPV2-5539473BF8DC570C7F64 MPV2-11B7F95FFE49FAB58AFB MPV2-95F3AB2B3A8CD5C1CB99".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-73FBA77460BEC4616E84 MPV2-141CD9E2374A0EABF1C0 MPV2-2BB34E7D8E39710221B5 MPV2-6C08AF37D195D5233066 MPV2-B8C8A8C8B5E0560ED95D MPV2-85BBA53058E50CF664B0".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-26E7185DC3EE61BD1426 MPV2-D73935D5CFEDECFAE2D7".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-FE6B81A6974A1DF79EE4 MPV2-8E908062CB247B1AB2BD MPV2-DA9EE58247DAC2AD40DC MPV2-BD16A4A1AD1DC0CD701C MPV2-529B126774BC20362333 MPV2-A7EF6720B7A0E638FE26".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-3AC5342DB47B093B22AF MPV2-EDFFF34B889305ECEEE8 MPV2-38FB2E8776F05D132EB4".split())
_REVIEWED_HISTORICAL_IDS |= {"MPV2-421755ADAFFDD9CC84D1"}
_REVIEWED_AUTOMATED_IDS |= frozenset("MPV2-CF8918EB275AA8A80B5B MPV2-037467E14BAED0004027 MPV2-EA274443FE6CAEFB9D35 MPV2-E12613FF2FA5AB006140".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-82606E1F6D51C7F88E5C MPV2-13000FA28D82EC5AAA2A MPV2-1B08449673529A15A3AF MPV2-7FED15B94485B53DC2A0 MPV2-D27ACFE249A0F282CF22 MPV2-B554891824CDBDE34F31 MPV2-CD6535617886066C3CCD MPV2-9C46F98AEADAFE6BC54B MPV2-CAB7FB5E5FBDF5E961DD MPV2-CDD6CE77673FCE0E59CD MPV2-48FCDB362525FCEDDAF5 MPV2-5CDE902B019C92024FDE MPV2-0DCDFACF9F6A5BB56786 MPV2-1F85B7D0CA5121EE825D MPV2-1821F861F3C36D18675B MPV2-E555355017C2E26DC5FE MPV2-64D9298755972FF7CBC5 MPV2-1B06C17A22348DB1044B MPV2-45FE76666F335E681481 MPV2-B74CC80EC539A91E45DF MPV2-3D84B8F0C5AD0CC030B6 MPV2-86EC74B33C4126687DF2 MPV2-FFA86C702E534B63DFB7 MPV2-A6745D7564FC6D6A8C46 MPV2-46D7994BFA71925B1E58 MPV2-24365F91BED9F29961D3 MPV2-3C5788DD59811B28A239 MPV2-16B0908D68C6EA3E13AA MPV2-10FB4CDE35BCB341EE78 MPV2-55DEC873E08FC7C31028 MPV2-0274C56E33826B91E520 MPV2-5DE8E173B35010A86566 MPV2-BA20E6F5BD8B1D9A1634 MPV2-952E15363F80BD4EE7D0 MPV2-AAFEAAF3A6738F281514 MPV2-14C0396DD0E5D90B4E8F MPV2-C08CEB874D1EA2A71B77 MPV2-805AA5AE551B45683E84 MPV2-E6E13BD346303031E575 MPV2-DE2A3418653F3789DDF4 MPV2-5ACDA3F291DF778B5286 MPV2-8946D08C145717A3DD11 MPV2-C51E55A63FFBF6C124F2 MPV2-166C705B7D969CE54A9E MPV2-FE27884A53EC3E0A78EC MPV2-72FD9F53E24141FDD050 MPV2-8595F8F37F9DE7368651 MPV2-51757BE9CCEF7B2E438C MPV2-C3D4EB2F300C09DFBF8E".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-30A8AB425F60B2B17EC9 MPV2-03947E8A179C6F3772C0 MPV2-A76123E29A3EB730BDE7 MPV2-ECFECBB053AE5D4D0566 MPV2-FEEBD2F0E9BE804A5B2C MPV2-5F7CFD546FC52DE8416B MPV2-A48F3120C61A12174857 MPV2-7BA8DD97CE5F1AE46AED MPV2-E269ACF8A8093F129D46 MPV2-5FAA781F19A6CD6A96F3 MPV2-8766BA59C4723BD78D29".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-AA0C181B66247E81E6F8 MPV2-1125A08DE05E9C5CE57D MPV2-BF07591DCFA1320B2FAB MPV2-423848521D301EDC6842 MPV2-94AD0B616661E06C4CF9 MPV2-9CD650752203B14A21A6 MPV2-00B2BB2DC4D86748B14E MPV2-6672D218CA98F1764461 MPV2-F1349B0C9E6D06D6DA42".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-F8155AFAA69C0AAB0A89 MPV2-FBDF3EF12E28593C5CB1 MPV2-FFD3DFF55866708FB4E3 MPV2-AACB54A4AE39022880A7 MPV2-09F4FCDC3BB4D39CD5B0 MPV2-2AFE8D20B3092B2105CD MPV2-5295484176EBEFB122E4 MPV2-65B7F345667375A1D359 MPV2-9AADAF34CC43507A2FE6 MPV2-EDDD716CF4B0772EFF86 MPV2-CD6B07D765FD66C526C8 MPV2-8EF44C125789DD33EEB8 MPV2-66494729B8B44FF5971D MPV2-2D5A5385F5D0380AC6D6 MPV2-8B14B3AC81A38F6C617C MPV2-63B70297036BF721A2D8 MPV2-3BA6CE805F1026567C19 MPV2-27C4AC692E2209508AA2 MPV2-3C98BAF3D8EF708F001B MPV2-2EE343492EDF155D369F MPV2-C8E3FDF8CB7ED9121CA3".split())
_REVIEWED_AUTOMATED_IDS |= frozenset("MPV2-CCAF42DBEF97676D88F8 MPV2-48BF17A52A046F247D62 MPV2-17D30CD13D225F539E3D MPV2-6456B66F20F73ED10E15 MPV2-8BF4A6C8189AC12A795C MPV2-F93717588DAF6779A254 MPV2-2FFC9886B74A716E3F7B MPV2-A7BDBB0F61AAD2780281 MPV2-5D01520A94832D67CC34 MPV2-6A765319F8DDEBA0CCF5 MPV2-8E8EB592B72073576958 MPV2-7ACCB844FC1795BF209D MPV2-8B74492F06D5832FF655 MPV2-314B510235351440D2CC".split())
_REVIEWED_AUTOMATED_IDS |= frozenset("MPV2-970937A2DFF2BCB3CE52 MPV2-7D731E8F7AC6216A4A92 MPV2-53980BAA4C33917BA5C3 MPV2-4B0A5AF620C7BE9A17D4 MPV2-19AAE646523FA9391CA6 MPV2-E80C93444FE616EB0607 MPV2-8062179D33C10B231620 MPV2-3A37133CC8A7BC1851FD MPV2-889EF1BFDC8B52B325A1 MPV2-8E89934662C396018FF2 MPV2-C473F7AEDDD33D85E55C".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-28AE723265C0B4197825 MPV2-612BCDE2ECF9190FE82A MPV2-FA3C5FF27646976DF658 MPV2-E270650B6FB9808D6D3F MPV2-57805C9430B7E4F0230F MPV2-10C5BE6559067E0FBB06 MPV2-FD9B72704E3E1D9D79E2 MPV2-86B3007C3B196F9DEC7A MPV2-DE6211D7F1B16FFDA67E MPV2-2E3E26E9CDE6033C24C6 MPV2-E0FACBB30B45E89D8C1D MPV2-4F4504223DFCC52F84EE".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-437414E3DB9127EE038C MPV2-54F6F18DB65C73AE9A21 MPV2-039FBA9F779EC829AAE6 MPV2-AB8DDE627AE95F0D2AEA MPV2-36EC22F3A35E3838C2E0 MPV2-1409AB91022894BBB418 MPV2-720A7399F197B8205B60 MPV2-C7C9C323466042E2ABF0 MPV2-ED7ED8B6116A8F85A565 MPV2-5A06083EE3CBD4588FB3 MPV2-EFD36B6D1E42447E21C2 MPV2-510EAC7810C1C40C819E MPV2-686BCD90FE7573468D5B MPV2-C5B97C70F01EAFA8F0DC MPV2-517058BA63382B48EA69 MPV2-2BAA76B84AE21B254D3C MPV2-C45920FCC3B766256AA8 MPV2-ABC67DA5EFD998F54226 MPV2-47FBAC7492DCBBA73929 MPV2-574557BED503483581A3 MPV2-8C38C455C5AB332E76D5 MPV2-C1ACBFC750FF67E9A396 MPV2-4EF0921FF5758FDF0D32 MPV2-57DB075D70CDBC71D537 MPV2-604B987B59362D9C9560 MPV2-7D54E109346BB562C5F6 MPV2-6FC9C15ED25FBC89CB83 MPV2-50FAFE07734892A37DD1 MPV2-9F55C9BA2A15F1B7A25B MPV2-7CA5ECE1C7245039AC94 MPV2-881D48BDAB7A5420E611 MPV2-6664BF7A00CEDCD207F3 MPV2-C5A6589607F4D39B1D9A MPV2-FC0A7635CD7A239832F6 MPV2-8F7845481B70EB2283B0 MPV2-8C6E6AAE4B24D0F1F469 MPV2-802C2FEE97E0E37E3AAE MPV2-CE035D1825F5195D7D66 MPV2-73BB802F2704D236C6C6 MPV2-205C1C17DF59169D8377 MPV2-65D9F0F616BEC9723B70 MPV2-4873BE6167612ECAFE2C MPV2-3B147BD2C253D2699E52 MPV2-84AD2344510B7C9F24DA MPV2-5E550880DEB7C24A66A9 MPV2-B8EDA3C6A3E2EC1A99DC MPV2-D78C8D2E578FE31E446D MPV2-A71877E181868309A2FE MPV2-5FB0291D4D248A237EF3 MPV2-EA1C58F0D791B7500CBC MPV2-EF5FFF97EDEE5778189C MPV2-4970D12537992AA37CFD MPV2-3974267491FEE406B539 MPV2-FEA6573415906084FB1B MPV2-C9D0733D71845F57E0FC MPV2-12AAECF3C4D9205F7C20 MPV2-CEEF8A82F36375DEA5EE MPV2-1FC4D310ED6C34F6E7BC MPV2-9B803308038A6DE51105 MPV2-4C8BD12AAFAE6B46EB17 MPV2-45A51946EE40BB202154 MPV2-72F02B40D63AF2D12672".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-D925624C460D1F73CCB5 MPV2-CF827DEFFDCAB4E8F71C MPV2-60818F449220AEC9D256 MPV2-C9D9AABBA7494166CC66 MPV2-8C6A9ABFD60C35EB9716 MPV2-1224A20E334825E287DD MPV2-A669D6EC9EE00F496C72 MPV2-D8FC5F1FEC8777CB8342 MPV2-D1B08BA99A5B7E6ACBB0 MPV2-A34AAA08237747FE5EBE MPV2-98C460280791E68F6C50 MPV2-5A04772DB8FFDB3E9211 MPV2-FFF0A58803A0C27B4DD1 MPV2-815348E9B4428BC3CE3E MPV2-A28689B7C7D8A50FDF92 MPV2-0220A05C1E9C4902A343 MPV2-6740EA33C994992ACDB0 MPV2-2528CDD755919252EABD MPV2-134DB4296E66219A6C2A MPV2-75EDD2238828DAE39B78 MPV2-C5256CA4A5232A8040F3 MPV2-1E40B32A52A437159A04 MPV2-E7197EF43291EB5908D2 MPV2-DA46FB00E7790D74D391 MPV2-0CAF5790EB3CE09B7DB5 MPV2-194AE8D705265676F56A MPV2-CABFA11769B4B0238DED MPV2-1FC83B3496E283442B62 MPV2-AC723CCB49C8C8EC71DC MPV2-E394E3CDABB6265EEA14".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-46AB9DF84B9B195C7F7C MPV2-A66CC4150158C1E47336 MPV2-E8EAFBC5FEE3E1B4461D MPV2-58CC3F2BDD5E03D32339 MPV2-83CB3D7C601C68E8D806 MPV2-8F0346B5E757385D190D MPV2-36B11A35EE89A0C3D652 MPV2-88C5F02F50FC16D7BC69".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-336E4B62B7BA9B7646B0 MPV2-8905CC133416F10604FD MPV2-8B4CD250BA18DF93FB42".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-193793536BFCA7A5FC69 MPV2-AC9CAF31E6EB62BD56EF MPV2-8D451F48CFDEDE54490D MPV2-A2A81A46DA693F09EEA2".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-DD8ACFCF5B8C2D66751B MPV2-6784FB8E59A560114447 MPV2-728728F63E96A7B94F4F MPV2-45FFDF419651585F285B MPV2-7F4B2C58ED1C2F19EC0E MPV2-D4AB9B18C8F8FEB6D4FF MPV2-63562A7438D1A29EB62E MPV2-7DF01AAF72CFB21F3D87 MPV2-A2F192DED3297EAC0A9C MPV2-C6AB1D98773E116D48E9 MPV2-233FD5E23934D56FBF5A MPV2-084A0BD1B9B9E206A4C4 MPV2-605C23E13168CCBFADBC MPV2-B362A7F3A038EFBFEA34 MPV2-9497CF502C63F3E8448F MPV2-8A71E5A2548934F7AD8E MPV2-C178C2036CFAE229A8A5 MPV2-55446E54069838F32201 MPV2-7E58E5956F815C036CC9 MPV2-F164446D99CDE3A435E1 MPV2-553E6AD964F18B710D15 MPV2-DA39C682685F8BE6D9B3 MPV2-4123540249B5A859A3B1 MPV2-A796A5F66376802246C1 MPV2-5DD7E0EE79F8564055EC MPV2-3BD55D27E0A0988363A4 MPV2-7685F4FDEB34E3D67A84 MPV2-9BBBC20B9F49354B8B57 MPV2-5957D449538904E527B8 MPV2-5E2184FA465537A40539".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-E570E6C022129DCB147E MPV2-E72A7A0C15DE4B2C4A52".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-B69F601B752C8C3325D8 MPV2-61D889F2215BD98536E6 MPV2-E0FF8E7422787CD4BC94 MPV2-1F4F0D77205C02E73C1D MPV2-3C66E3D38C6C0B28F76D MPV2-254E356AF14756748A05 MPV2-619A2A8C52C5A2805C8E MPV2-66F23BC17AD074628A18 MPV2-7FA14448F24ED9B5C05F MPV2-03EF425A60642AA1ECBE MPV2-6CE894802717F38C472E MPV2-60750C6F805A0DEC140B MPV2-BB4D7B35152092DFEB07 MPV2-C4946D8E5812ABDCE279 MPV2-EC99C79134D7E1677829 MPV2-4E1D38DC1498CDE4BC61 MPV2-6005F99AD1AC4ACEB1AB MPV2-9D7C9425114ECBB3AA32 MPV2-7B2C284ABAEA7E5DB00B MPV2-CB9DDC0C7661D7963518".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-BDD6FE390A5ABEA65402 MPV2-5FA5DAF31BD637378335 MPV2-1471DA746AE448A41468 MPV2-358524EDE86B4CD79185 MPV2-FCEF00C3B8B1271E42BA MPV2-FCE2B40111BF1C6A5F1E MPV2-8AADD6B78A304AE4CC18 MPV2-921F5BD6D211DFA918B5 MPV2-FA7C452EE36951B4056B MPV2-F4177087E3631F36BB1F MPV2-E15C45983C299E359EDD MPV2-6C7A3CCF1847975236BB MPV2-951FFC98620E3AADA66D MPV2-26E076DFC55BEBEC35DF MPV2-EB942D3313A1D75C7F52 MPV2-2D2653228E2407A9ED82 MPV2-A05C28AC199D878939BE MPV2-442B9E87C37975FF193B MPV2-87CAF3D41FC51994C9AF MPV2-9925FFF35D0B7375A0F5 MPV2-851EAF61DFA867328B82 MPV2-73417F04797A51A109DF".split())
_REVIEWED_HISTORICAL_IDS |= frozenset("MPV2-0AD402E3E71510EF4C84 MPV2-8E8377759C9BDA98C708 MPV2-E5D013A797FC0228C637 MPV2-0708AA3693FB84D3C824 MPV2-1BF8E7E24027BBF141B8 MPV2-DA19B9D565031FF6BE77".split())
_REVIEWED_CURRENT_STATE_IDS |= frozenset("MPV2-F05C1C844EF7C105F69E MPV2-D0039745D0A646CA4064 MPV2-CEEAF6DD15466CA1213F MPV2-B97B619D8F9A0DC2E8D9".split())
_REVIEWED_AUTOMATED_IDS |= frozenset("MPV2-73E611EF338B3194E36D MPV2-5146778BA810D7C0420A MPV2-69F715108FE7F6780C14".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-36918597D1DB3012C4E6 MPV2-B9916D1EF66797F821BA MPV2-EEE85E1FA9595BF8AA79 MPV2-99D4230D3083BB1AC9C7 MPV2-A2C0B967DEF17FCFC4FB MPV2-EE837085B3B6AABBE786 MPV2-835D9BA34A269FB66C1E MPV2-57ACE808FC2EBF309DF2 MPV2-D57131E71C25196FF8C9 MPV2-93070852C85597683356".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-50088E8036FA5F4978F1 MPV2-CFEFA70E04AD3920CF4C MPV2-8579780BFB1BCD690BCC MPV2-87352A477BE2FCA4DCEC MPV2-D04E1172329DE6F5E45A MPV2-4CC5FDAF2C3BAF0246F5".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-B5B7096BD54758625387 MPV2-85C75B809F08945B1E46 MPV2-386B83DF96E3ADA689EC MPV2-7CCF80BDA31B547F18D8".split())
_REVIEWED_IMPLEMENTED_IDS |= frozenset("MPV2-3F50256C904F286134CC MPV2-0589730E1174C9CB6246".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= {"MPV2-DFB56BCB57E377582EF8"}
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-D80D334B6E1FE62B143E MPV2-54D345526A13122829CA MPV2-9E3D610A9DA1FF615A61 MPV2-4B35D3CF4DE66C97FDD8 MPV2-05F8576C44005E2DF8F2 MPV2-73CE3F56EA363BEFBA58 MPV2-35489F475AF0E73DFFEC".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-A90B12DA583AC36832B8 MPV2-2508A0580BCE70728107 MPV2-B91EA8C838990E76E385 MPV2-8091A71A5630ABEB9B2A MPV2-42A56D304851DFDD2156 MPV2-B79F6DB3EF5027134958".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-E40326A6DE7EE7F4BFC9 MPV2-D2D2293B040B7171ED66 MPV2-BD9E155AD06C1AD61004 MPV2-0B9A6622419700768D87 MPV2-E47CA8D2EAC360DBC6A5 MPV2-3F1B5DD8B285DF1512F4 MPV2-5C9713918E61B1EE1E49 MPV2-E2B1D215E26CF7CAAA8D MPV2-A5B8F936DCB0830B01AD MPV2-1385D8C7CF122982017D MPV2-2D0225354945AF05685E MPV2-8627D69E3BE4B3D24724 MPV2-34B3BA6B0ABB22351350 MPV2-8CBEE2E64BE4D800EBBA MPV2-C58C3D6F8A1789FABBA6 MPV2-362725AC7F5706827DB2 MPV2-42846A9A871856111C24 MPV2-0399E69007A9332E301E MPV2-00063703E8CA849CB107 MPV2-C59DFEFED42A3A9E9EC7 MPV2-7908E764445ED8D57256 MPV2-BBA2552663CE6FB4620D".split())
_REVIEWED_NORMATIVE_REQUIREMENT_IDS |= frozenset("MPV2-30DCBFB46B13229A9A67 MPV2-04540680D9C3D977507E MPV2-3FE4100AFE54F9E6D759".split())
_JSON_INSTANCE_POLICY_SOURCE_IDS = frozenset("SOURCE_PRESENTER_REGISTRY_D3ECDDB1 SOURCE_STAGE2_ARCHITECTURE_CONTRACT_F748F325 SOURCE_AUTHORITY_CORE_STATE_MATRICES_V1_7CD36E27 SOURCE_AUTHORITY_RECONCILIATION_AND_STALE_ROUTE_PHASE_SPEC_V1_4FC31FFB SOURCE_CUT1_ALL_PRESENTER_ACCEPTANCE_MATRIX_V1_9597559E SOURCE_CUT1_BLINDED_HUMAN_EVALUATION_PROTOCOL_V1_C374C7E7 SOURCE_CUT1_GOOGLE_GEMINI_TTS_STYLE_PROMPTS_V1_7A42BD24 SOURCE_CUT1_PRESENTER_DERIVATIVES_V1_05780D7A SOURCE_CUT1_PRESENTER_LIVE_BINDING_V2_FF41196F SOURCE_CUT1_PROJECT_FACTS_V1_5A84887A SOURCE_CUT1_PROVIDER_BAKEOFF_CONTRACT_V1_295A1DA2 SOURCE_PUBLICATION_BOUNDARY_V1_1B85CD76 SOURCE_ACTIVE_PROGRAM_ROUTE_V1_SCHEMA_A52A17D4 SOURCE_CUT1_AUTHORITY_MANIFEST_V1_SCHEMA_C042B903 SOURCE_MASTER_PROGRAM_AUTHORITY_DECISION_V1_SCHEMA_470B2053".split())
# Exact hash-bound mixed leaves stay normative because their style limitation,
# retention/cleanup duty, or MUST_PIN duty governs the complete frozen value.
_JSON_MIXED_DOMINANT_NORMATIVE_IDS = frozenset("MPV2-020C1D52989CF32F2F24 MPV2-F068002A4DEE85FB1898 MPV2-5B6F739CDE8F1600EEBF MPV2-A0E20012C8BEF9724E17 MPV2-024B6AB140D70C69FC57 MPV2-E666A52ADD63EE842B01".split())
def _json_instance_is_normative(atom: Atom) -> bool:
    pointer = atom.anchor.split("::", 1)[0].removeprefix("json-pointer:/")
    s = tuple(part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/"))
    root = s[0] if s else ""
    source = atom.source_id
    if atom.requirement_id in _JSON_MIXED_DOMINANT_NORMATIVE_IDS:
        return True
    if source == "SOURCE_PRESENTER_REGISTRY_D3ECDDB1":
        return root in {"schema_version", "registry_version"} or root == "presenters" and not (len(s) > 2 and (s[2] == "lifecycle" or s[2] == "permission" and len(s) > 3 and s[3] == "provenance_review" or s[2] == "voice" and len(s) > 3 and s[3] == "description"))
    if source == "SOURCE_STAGE2_ARCHITECTURE_CONTRACT_F748F325":
        return root not in {"version", "stage", "canonicalIssue", "canonicalPullRequest"}
    if source == "SOURCE_AUTHORITY_CORE_STATE_MATRICES_V1_7CD36E27":
        return root in {"evaluationOutcomes", "matrices"}
    if source in {"SOURCE_AUTHORITY_RECONCILIATION_AND_STALE_ROUTE_PHASE_SPEC_V1_4FC31FFB", "SOURCE_CUT1_PROJECT_FACTS_V1_5A84887A"}:
        return False
    if source == "SOURCE_CUT1_ALL_PRESENTER_ACCEPTANCE_MATRIX_V1_9597559E":
        return root in {"claimScope", "presenterOrder", "registry", "approvedInputs", "presenters", "identityAndRights", "acceptance", "fallback"}
    if source == "SOURCE_CUT1_BLINDED_HUMAN_EVALUATION_PROTOCOL_V1_C374C7E7":
        return root in set("claimScope exceptionPolicy preregistration cells endpoint analysis sample power frozenBundleMutations matching orderAndFatigue viewerEligibility exclusions subgroups dimensionReview objectiveThresholds defectReview retest privacyAndEvidence".split())
    if source == "SOURCE_CUT1_GOOGLE_GEMINI_TTS_STYLE_PROMPTS_V1_7A42BD24":
        return root in {"caller_prompt_control", "canonical_encoding"} or root == "profiles" and len(s) > 2 and (s[2] not in {"accepted_screening_reference_sha256", "selected_request_manifest_sha256", "limitations"} or s[2] == "limitations" and len(s) > 3 and s[3] in {"accepted_screening_hash_is_reference_evidence_only", "final_90_to_120_second_narration_requires_validation_and_owner_listening"})
    if source == "SOURCE_CUT1_PRESENTER_DERIVATIVES_V1_05780D7A":
        return root in {"source_ready_without_derivative", "source_registry"} or root == "posture" and len(s) > 1 and s[1] in {"permitted_use", "publication_allowed"} or root == "derivatives" and len(s) > 2 and (s[2] in {"presenter_id", "presenter_version", "source_asset", "asset"} or s[2] == "rights" and len(s) > 3 and s[3] not in {"rejected_candidate_disposition", "deletion_posture"})
    if source == "SOURCE_CUT1_PRESENTER_LIVE_BINDING_V2_FF41196F":
        return root in {"immutableInputSha256", "limitations"}
    if source == "SOURCE_CUT1_PROVIDER_BAKEOFF_CONTRACT_V1_295A1DA2":
        if root == "sourceCheckpoint":
            return len(s) > 1 and s[1] == "refreshRequiredBeforeExperiment"
        if root in {"selectionPriority", "commonRules", "requiredAcceptanceRecord", "providerFailureSemantics", "deletionAndRevocation", "frozenProviderMutations"}:
            return True
        return root in {"voice", "batchVideo", "futureQa"} and len(s) > 2 and s[2] not in {"sources", "eligibility"} and not (root == "voice" and s[2] == "lifecycle" or root == "batchVideo" and (s[1] == "3" and s[2] == "api" or s[1] in {"2", "3"} and s[2] == "modelOrEngine"))
    if source == "SOURCE_PUBLICATION_BOUNDARY_V1_1B85CD76":
        return root != "schemaVersion" and (root != "launchPosture" or len(s) > 1 and s[1] == "publicationIsReleaseAuthorization")
    if source in {"SOURCE_ACTIVE_PROGRAM_ROUTE_V1_SCHEMA_A52A17D4", "SOURCE_CUT1_AUTHORITY_MANIFEST_V1_SCHEMA_C042B903", "SOURCE_MASTER_PROGRAM_AUTHORITY_DECISION_V1_SCHEMA_470B2053"}:
        return root in {"closed", "canonicalProfile", "$defs", "root"}
    return False
def _status_semantic_class(atom: Atom) -> str:
    if atom.source_context_sha256 in _STATUS_NORMATIVE_CONTEXTS or (
        atom.source_context_sha256,
        atom.focus_start,
    ) in _STATUS_NORMATIVE_FOCI:
        return "NORMATIVE_REQUIREMENT"
    if any(heading in atom.anchor for heading in _STATUS_HISTORICAL_HEADINGS):
        return "HISTORICAL_FACT"
    if any(heading in atom.anchor for heading in _STATUS_NORMATIVE_HEADINGS):
        return "NORMATIVE_REQUIREMENT"
    return "CURRENT_STATE_FACT"
def _owner_semantic_class(atom: Atom) -> str:
    if "## 4." not in atom.anchor:
        return "NORMATIVE_REQUIREMENT"
    if atom.source_clause in _DESTINATION_SOURCE_CONTEXTS:
        return "NORMATIVE_REQUIREMENT"
    if "### Canonical accepted input authority" in atom.anchor or (
        "### Evidence inventory and immediate security duties" in atom.anchor
    ):
        return "NORMATIVE_REQUIREMENT"
    if "### Current implementation evidence" in atom.anchor:
        if atom.source_clause.startswith(
            "Existing `AvatarVideoProvider` and `TTSProvider` boundaries"
        ):
            return "NORMATIVE_REQUIREMENT"
        return "CURRENT_STATE_FACT"
    context_hash = atom.source_context_sha256
    if context_hash in _OWNER_NORMATIVE_CONTEXTS or (
        context_hash,
        atom.focus_start,
    ) in _OWNER_NORMATIVE_FOCI:
        return "NORMATIVE_REQUIREMENT"
    override = _OWNER_FOCUS_CLASS.get((context_hash, atom.focus_start))
    if override is not None:
        return override
    return _OWNER_CONTEXT_CLASS.get(context_hash, "CURRENT_STATE_FACT")
def _provider_landscape_semantic_class(atom: Atom) -> str:
    heading = atom.anchor
    if "## Historical pre-v9 pre-implementation plan" in heading:
        return "HISTORICAL_FACT"
    normative_headings = (
        "## Product need and non-negotiable inputs",
        "## Research method and limits",
        "## Demo-before-code recommendation",
        "## Exact call lineage and billable-unknown behavior",
        "## Invariant and evidence matrix",
        "## Exact owner/operator inputs for Gate 0",
        "## Decision rule",
        "## Finding classification and disposition",
        "### Permitted exploration role",
        "## Issue #516 controlling amendment",
        "### Plan A — presenter-led compatibility",
        "### Plan B — editorial hybrid",
        "## Multi-reference character pack",
        "## Current decision sequence",
    )
    return (
        "NORMATIVE_REQUIREMENT"
        if any(value in heading for value in normative_headings)
        else "CURRENT_STATE_FACT"
    )
def _real_media_plan_semantic_class(atom: Atom) -> str:
    heading = atom.anchor
    evidence_headings = (
        "## Version",
        "### Cut 1 T06 research refresh",
        "### Source-Fact Snapshot",
        "## Cost Planning",
        "## Checkpoint 1 Source Facts",
        "## Checkpoint 1 Skill/Tool Selection",
        "## Checkpoint 1 Fan-Out Review Record",
    )
    if any(value in heading for value in evidence_headings):
        return "CURRENT_STATE_FACT"
    normative_headings = (
        "## Purpose",
        "## Demo Boundary",
        "## Provider Strategy",
        "## Checkpoints",
        "## Checkpoint 1 Implementation Contract",
        "### Checkpoint 1 PR",
        "### Future PR",
        "## Cost-Minimized Controlled Demo Constraints",
        "### Quota, Retry, And Cost Contract",
        "### Async Provider Lifecycle Contract",
        "### Media Artifact Cache Contract",
        "### Multilingual Grounding Contract",
        "### External Reviewer Flow UX Contract",
        "## Checkpoint 1 Failure Matrix",
        "## Checkpoint 1 Review Prompt Set",
        "## Checkpoint 1 Stop Rule",
        "### Checkpoint 2:",
        "### Checkpoint 3",
        "## Failure Matrix Categories",
        "## Fan-Out Review Requirements",
        "## Autonomous Execution Rule",
        "## Non-Goals For Issue",
    )
    return (
        "NORMATIVE_REQUIREMENT"
        if any(value in heading for value in normative_headings)
        else "CURRENT_STATE_FACT"
    )
def _semantic_class(atom: Atom, authority_lifecycle: str) -> str:
    """Classify authority effect through closed source/anchor/context rules."""
    if authority_lifecycle == "IMPLEMENTED":
        return "IMPLEMENTED_BEHAVIOR"
    if authority_lifecycle in {"HISTORICAL", "SUPERSEDED"}:
        return "HISTORICAL_FACT"
    if authority_lifecycle in {
        "ADVISORY_ONLY", "EVIDENCE", "NO_AUTHORITY", "PROPOSED_BLOCKED",
        "PROPOSED_NONACTIVATING", "SHADOW",
    }:
        return "CURRENT_STATE_FACT"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", atom.text.strip()):
        return "CURRENT_STATE_FACT"
    if atom.source_id in {"SOURCE_TRACEABILITY_7B284BCF", "STATUS"} and (
        "## Change Log" in atom.anchor
    ):
        return "HISTORICAL_FACT"
    if atom.requirement_id in _REVIEWED_HISTORICAL_IDS:
        return "HISTORICAL_FACT"
    if atom.requirement_id in _REVIEWED_AUTOMATED_IDS:
        return "AUTOMATED_RESULT"
    if atom.requirement_id in _REVIEWED_IMPLEMENTED_IDS:
        return "IMPLEMENTED_BEHAVIOR"
    if atom.requirement_id in _REVIEWED_CURRENT_STATE_IDS:
        return "CURRENT_STATE_FACT"
    if atom.requirement_id in _REVIEWED_NORMATIVE_REQUIREMENT_IDS:
        return "NORMATIVE_REQUIREMENT"
    focus_exact = _EXACT_FOCUS_CLASS.get(
        (atom.source_id, atom.source_context_sha256, atom.focus_start)
    )
    if focus_exact is not None:
        return focus_exact
    exact = _EXACT_CONTEXT_CLASS.get(
        (atom.source_id, atom.source_context_sha256)
    )
    if exact is not None:
        return exact
    table_column = re.search(r":([^:]+):U[0-9]+$", atom.anchor)
    if table_column and table_column.group(1).casefold() == "evidence" and atom.source_id in {
        "FIVE_CUT_ROADMAP", "CUT1_PRESENTER_CONTRACT",
    }:
        return "NORMATIVE_REQUIREMENT"
    if table_column and table_column.group(1).casefold() in {
        "date", "evidence", "issue / pr", "official source", "result", "status",
    }:
        return "CURRENT_STATE_FACT"
    stripped = atom.text.strip()
    if atom.source_id == "MASTER_PROGRAM_V1" and atom.source_span_start_line >= 11:
        return "NORMATIVE_REQUIREMENT"
    if atom.source_id == "OWNER_PLAN_2026_09_07":
        return _owner_semantic_class(atom)
    if any(
        heading in atom.anchor
        for heading in (
            "## Version", "## Document control", "## Related Documents",
            "## Related decisions and evidence", "## References",
        )
    ):
        return "CURRENT_STATE_FACT"
    if stripped in {"Fields:", "Positive:", "Controls:", "Negative:", "Indexes:", "Attack:", "N/A", "PASS", "FAIL"}:
        return "CURRENT_STATE_FACT"
    if re.search(r"\bIssue\s+`?#\d+`?\s+remains\s+open\b", stripped):
        return "CURRENT_STATE_FACT"
    if "::fence:" in atom.anchor and "historical evidence" in stripped.casefold():
        return "HISTORICAL_FACT"
    if atom.source_id in {"AVATAR_PROVIDER_CODE", "TTS_PROVIDER_CODE"}:
        return "IMPLEMENTED_BEHAVIOR"
    if "::INSTANCE_FACT:" in atom.anchor:
        return "NORMATIVE_REQUIREMENT" if _json_instance_is_normative(atom) else "CURRENT_STATE_FACT"
    if "::SCHEMA_CONSTRAINT:" in atom.anchor:
        return "NORMATIVE_REQUIREMENT"
    if atom.source_id == "STATUS":
        return _status_semantic_class(atom)
    if atom.source_id == "STAGE_ISSUE_PLAN":
        return (
            "NORMATIVE_REQUIREMENT"
            if 168 <= atom.source_span_start_line < 700
            or "## Phase 1 Closure Branch Scope" in atom.anchor
            else "HISTORICAL_FACT"
        )
    if atom.source_id == "CUT1_T06_PROVIDER_LANDSCAPE":
        return _provider_landscape_semantic_class(atom)
    if atom.source_id == "REAL_MEDIA_HOSTED_DEMO_PLAN":
        return _real_media_plan_semantic_class(atom)
    if atom.source_id == "ADR_0079":
        if "## Alternatives rejected" in atom.anchor:
            return "HISTORICAL_FACT"
        if "## Context" in atom.anchor or "## Remaining decisions" in atom.anchor:
            return "CURRENT_STATE_FACT"
    if atom.source_id == "PRD" and any(
        heading in atom.anchor
        for heading in ("## 2. Contacts", "## 3. Background", "## 16. Open Questions")
    ):
        return "CURRENT_STATE_FACT"
    if atom.source_id == "SECURITY_PRIVACY" and "### Secret Screening Result" in atom.anchor:
        return "NORMATIVE_REQUIREMENT"
    if atom.source_id == "SECURITY_PRIVACY" and "## Version" in atom.anchor:
        return "CURRENT_STATE_FACT"
    if atom.source_id == "ARCHITECTURE" and "## Version" in atom.anchor:
        return "CURRENT_STATE_FACT"
    if atom.source_id == "ENTERPRISE_REGISTER" and (
        "## Issue #452 readiness disposition" in atom.anchor
    ):
        return "CURRENT_STATE_FACT"
    if atom.source_id == "OBSERVABILITY_COST" and (
        "## Local operational status" in atom.anchor
    ):
        return "IMPLEMENTED_BEHAVIOR"
    return "NORMATIVE_REQUIREMENT"
def _disposition(
    atom: Atom,
    replacements: dict[str, str],
    adoption_ref: str,
) -> tuple[str, str | None, str | None]:
    rule = (
        None
        if atom.source_id == "OWNER_PLAN_2026_09_07"
        else _conflict_rule(atom)
    )
    if rule is not None:
        if rule.replacement_key is None:
            return rule.disposition, None, None
        replacement = replacements[rule.replacement_key]
        return (
            rule.disposition,
            replacement,
            _owner_authority_ref(replacement, adoption_ref),
        )
    if _legacy_enterprise(atom):
        replacement = replacements["cut6"]
        return "RELOCATED", replacement, _owner_authority_ref(replacement, adoption_ref)
    return "PRESERVED", None, None
def _row_atom(row: dict[str, Any]) -> Atom:
    return Atom(
        source_id=row["sourceId"],
        anchor=row["sourceAnchor"],
        text=decode_requirement(row["normalizedAtomicRequirement"]),
        exact_source_clause=decode_requirement(row["normalizedSourceContext"]),
        focus_start=row["atomicFocusStart"],
        focus_end=row["atomicFocusEnd"],
        focus_occurrence=row["atomicFocusOccurrence"],
    )
def _governing_context(atom: Atom) -> dict[str, Any]:
    table_row = "::table:" in atom.anchor
    return {
        "kind": (
            "FULL_NORMALIZED_TABLE_ROW_CONTEXT"
            if table_row
            else "FULL_NORMALIZED_SOURCE_CONTEXT"
        ),
        "normalization": (
            "MARKDOWN_TABLE_HEADER_VALUE_V1"
            if table_row
            else "WHITESPACE_COLLAPSE_V1"
        ),
        "coordinateSystem": "UNICODE_CODEPOINTS_ZERO_BASED_HALF_OPEN",
        "semanticBinding": "PENDING_INDEPENDENT_REVIEW",
        "start": 0,
        "end": len(atom.source_clause),
    }
def expected_comparison_basis(row: dict[str, Any]) -> str:
    if row["normativeEffect"] == "SUPERSEDED_NORMATIVE":
        return (
            f"{row['sourceAtomId']} remains auditable as superseded normative "
            "lineage; it cannot independently authorize current work or establish "
            "current acceptance."
        )
    rule = _conflict_rule(_row_atom(row))
    if rule is not None:
        return rule.comparison
    if row["disposition"] == "PRESERVED":
        return (
            f"Exact-focus incorporation preserves {row['sourceAtomId']} at "
            f"{row['v2DestinationClause']} without semantic or threshold weakening."
        )
    if row["disposition"] == "RELOCATED":
        return (
            f"The exact atomic focus is retained at {row['v2DestinationClause']}; "
            f"{row['replacementId']} changes only its owner-authorized taxonomy placement."
        )
    if row["disposition"] == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY":
        return (
            f"Only this atomic clause changes under {row['ownerAuthorityRef']}; "
            f"{row['replacementId']} is the exact replacement and sibling atoms remain preserved."
        )
    return "STRENGTHENED requires an exact retained-source and additive-control proof."
def _derived_threshold_comparison(row: dict[str, Any]) -> dict[str, str]:
    return {
        "relation": (
            "OWNER_AUTHORIZED_CHANGE"
            if row["disposition"] == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"
            else "EQUAL_OR_STRONGER"
        ),
        "basis": expected_comparison_basis(row),
    }
def _expected_rationale(row: dict[str, Any]) -> str:
    if row["normativeEffect"] == "SUPERSEDED_NORMATIVE":
        return (
            "The formerly normative clause and provenance remain mapped without "
            "reviving superseded execution authority."
        )
    rule = _conflict_rule(_row_atom(row))
    if rule is not None:
        return rule.rationale
    if row["disposition"] == "PRESERVED":
        return "Only the exact atomic-focus semantics are incorporated under the bound context; descriptive evidence is not promoted to acceptance."
    if row["disposition"] == "RELOCATED":
        return "The legacy enterprise requirement moves only to Cut 6 and retains its original evidence burden."
    if row["disposition"] == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY":
        return "The independently atomic legacy clause is replaced; adjacent obligations remain separate and preserved."
    return "No generated strengthening is permitted without independent clause-level proof."
def _semantic_coverage(
    atoms: list[Atom], authority_lifecycle: str, coverage_mode: str
) -> dict[str, Any]:
    """Bind every extracted unit to exactly one authority-effect partition."""
    entries: list[dict[str, str]] = []
    counts = {name: 0 for name in _SEMANTIC_CLASSES}
    normative_ids: list[str] = []
    for atom in atoms:
        semantic_class = _semantic_class(atom, authority_lifecycle)
        if semantic_class not in counts:
            raise ValueError("source unit semantic class is unclassified")
        counts[semantic_class] += 1
        effect = _SEMANTIC_EFFECTS[semantic_class]
        entries.append(
            {
                "sourceAtomId": atom.atom_id,
                "semanticClass": semantic_class,
                "normativeEffect": effect,
            }
        )
        if effect == "CURRENT_NORMATIVE":
            normative_ids.append(atom.atom_id)
    candidate_count = len(entries)
    normative_count = len(normative_ids)
    if candidate_count != sum(counts.values()):
        raise ValueError("source semantic partition is incomplete")
    return {
        "partitionPolicy": (
            "MANIFEST_ONLY"
            if coverage_mode == "MANIFEST_ONLY"
            else "NO_NORMATIVE_AUTHORITY"
            if normative_count == 0
            else "EXPLICIT_HASH_BOUND_PARTITION"
        ),
        "candidateUnitCount": candidate_count,
        "normativeRequirementCount": normative_count,
        "excludedUnitCount": candidate_count - normative_count,
        "classCounts": counts,
        "orderedPartitionSha256": _sha256(
            _canonical_json(entries).encode("utf-8")
        ),
        "orderedNormativeAtomSha256": _sha256(
            _canonical_json(normative_ids).encode("utf-8")
        ),
    }
_SOURCE_RECORD_CACHE: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
def _source_records(root: Path) -> list[dict[str, Any]]:
    try:
        owner_bytes = (root / DOCUMENT_PATH).read_bytes()
        cache_key = (
            str(_git_directory(root)), BASE_SHA, _sha256(owner_bytes),
            OWNER_PLAN_ADOPTION_COMMENT_ID, OWNER_PLAN_ADOPTION_BODY_SHA256,
            OWNER_PLAN_ADOPTION_DOCUMENT_SHA256,
        )
    except OSError as exc:
        raise ValueError("frozen owner source unavailable") from exc
    cached = _SOURCE_RECORD_CACHE.get(cache_key)
    if cached is not None:
        return copy.deepcopy(cached)
    if (
        len(_REPOSITORY_SOURCE_SPECS) != 192
        or len({item[0] for item in _REPOSITORY_SOURCE_SPECS}) != 192
        or len({item[2] for item in _REPOSITORY_SOURCE_SPECS}) != 192
    ):
        raise ValueError("frozen repository inventory definition invalid")
    records: list[dict[str, Any]] = []
    for (
        source_id, kind, relative, atomizer, default, coverage_mode,
        authority_lifecycle, declared_object_kind,
    ) in _SOURCE_SPECS:
        is_owner_plan = kind == "OWNER_PLAN"
        commit = None if is_owner_plan else BASE_SHA
        if is_owner_plan:
            data = frozen_source_bytes(
                root,
                {"sourceKind": kind, "sourceCommit": commit, "repositoryPath": relative},
            )
            object_kind = declared_object_kind
            object_id = _git_blob(data)
            tree_entries: list[dict[str, str]] = []
        else:
            object_kind, object_id, tree_entries, data = _frozen_repository_object(
                root, BASE_SHA, relative
            )
            if object_kind != declared_object_kind:
                raise ValueError("frozen repository inventory object kind invalid")
        source_kind = (
            "OWNER_ADOPTED_PLAN"
            if is_owner_plan and _owner_plan_adoption_ready(data)
            else "OWNER_PLAN_CANDIDATE"
            if is_owner_plan
            else kind
        )
        atoms = _atoms(source_id, atomizer, data)
        refs = (
            [_owner_plan_adoption_ref(data)]
            if is_owner_plan
            else _tree_issue_refs(root, tree_entries, relative)
            if object_kind == "GIT_TREE"
            else _issue_refs(data.decode("utf-8"), relative)
        )
        effective_lifecycle = (
            "OWNER_ADOPTED"
            if is_owner_plan and source_kind == "OWNER_ADOPTED_PLAN"
            else authority_lifecycle
        )
        authority_origin = (
            {
                "kind": "RESTRICTED_OWNER_MESSAGE",
                "reference": OWNER_PLAN_RESTRICTED_SOURCE_REF,
                "contentSha256": OWNER_PLAN_RESTRICTED_SOURCE_SHA256,
                "byteCount": OWNER_PLAN_RESTRICTED_SOURCE_BYTES,
                "publicRepresentation": "NORMALIZED_REDACTED_CANDIDATE",
                "normalizationAttestation": (
                    "PASS" if _owner_plan_adoption_ready(data) else "PENDING"
                ),
            }
            if is_owner_plan
            else {
                "kind": "FROZEN_GIT_TREE" if object_kind == "GIT_TREE" else "FROZEN_GIT_BLOB",
                "reference": f"git:{BASE_SHA}:{relative}@{object_id}",
                "contentSha256": _sha256(data),
                "byteCount": len(data),
                "publicRepresentation": "EXACT_SOURCE_BYTES",
                "normalizationAttestation": "NOT_APPLICABLE",
            }
        )
        records.append(
            {
                "sourceId": source_id,
                "sourceKind": source_kind,
                "repositoryPath": relative,
                "sourceCommit": commit,
                "sourceGitBlob": object_id,
                "contentSha256": _sha256(data),
                "atomizer": atomizer,
                "semanticCoverage": _semantic_coverage(
                    atoms, effective_lifecycle, coverage_mode
                ),
                "authorityRefs": refs,
                "defaultV2Destination": default,
                "authorityOrigin": authority_origin,
                "coverageMode": coverage_mode,
                "authorityLifecycle": effective_lifecycle,
                "objectKind": object_kind,
                "coverageStatus": (
                    "PENDING_EXTERNAL_ATTESTATION" if is_owner_plan and source_kind == "OWNER_PLAN_CANDIDATE" else "COMPLETE"
                ),
                "treeEntries": tree_entries,
                "treeManifestSha256": _sha256(data) if object_kind == "GIT_TREE" else None,
            }
        )
    _SOURCE_RECORD_CACHE[cache_key] = copy.deepcopy(records)
    return records
def _pending_external_authority_manifest(
    sources: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    references = sorted(
        {
            reference
            for source in sources
            if source["sourceKind"] == "REPOSITORY_FILE"
            for reference in source["authorityRefs"]
            if reference.startswith("github-")
        }
    )
    return {
        "schemaVersion": "ExternalAuthorityManifestV1",
        "repository": {
            "id": GITHUB_REPOSITORY_ID,
            "fullName": GITHUB_REPOSITORY,
        },
        "cutoff": "2026-09-06T23:59:59+05:30",
        "referenceCount": len(references),
        "orderedReferenceCensusSha256": _sha256(
            _canonical_json(references).encode("utf-8")
        ),
        "recordCount": len(references),
        "orderedRecordSha256": _sha256(
            _canonical_json(
                [
                    {
                        "reference": reference,
                        "resolution": "DISCOVERED_UNRESOLVED",
                    }
                    for reference in references
                ]
            ).encode("utf-8")
        ),
        "retrievedAt": None,
        "records": [
            {"reference": reference, "resolution": "DISCOVERED_UNRESOLVED"}
            for reference in references
        ],
        "governingContextDecisionPartition": None,
        "closure": "PENDING",
    }
def _selected_external_authority_manifest(
    root: Path,
    sources: list[dict[str, Any]],
    supplied: dict[str, Any] | None,
) -> dict[str, Any]:
    if supplied is not None:
        return copy.deepcopy(supplied)
    try:
        existing = _load_json(root / MAPPING_PATH)
        candidate = existing.get("externalAuthorityManifest")
    except (AttributeError, DuplicateJsonMember, OSError, ValueError):
        candidate = None
    expected = _pending_external_authority_manifest(sources)
    if not isinstance(candidate, dict):
        return expected
    records = candidate.get("records")
    if (
        candidate.get("closure") == "CLASSIFIED_AND_ATOMIZED"
        and isinstance(records, list)
        and [record.get("reference") for record in records if isinstance(record, dict)]
        == [record["reference"] for record in expected["records"]]
    ):
        return copy.deepcopy(candidate)
    return expected
def _content_addressed_reference_map(
    manifest: dict[str, Any],
) -> dict[str, str]:
    return {
        record["reference"]: record["contentAddressedRef"]
        for record in manifest.get("records", [])
        if isinstance(record, dict)
        and isinstance(record.get("reference"), str)
        and isinstance(record.get("contentAddressedRef"), str)
    }
def _external_source_id(reference: str) -> str:
    return "EXTERNAL_" + re.sub(r"[^A-Z0-9]+", "_", reference.upper())
def _external_clause_atom(record: dict[str, Any], clause: dict[str, Any]) -> Atom:
    span = clause["sourceSpan"]
    return Atom(
        source_id=_external_source_id(record["reference"]),
        anchor=clause["sourceAnchor"],
        text=clause["normalizedAtomicFocus"],
        exact_source_clause=clause["normalizedSourceContext"],
        focus_start=clause["atomicFocusStart"],
        focus_end=clause["atomicFocusEnd"],
        focus_occurrence=clause["atomicFocusOccurrence"],
        source_span_start_line=span["startLine"],
        source_span_end_line=span["endLine"],
        raw_source_span_sha256=span["restrictedSourceSpanBindingSha256"],
    )
def _external_default_destination(record: dict[str, Any], atom: Atom) -> str:
    if atom.requirement_id in {"MPV2-EBF89EEC9E95E26A0F9D", "MPV2-0E3D0BD726CBD0E008BB", "MPV2-AA474AFCF10BF9049EDF", "MPV2-4902F39C170E14867575"}:
        return "MPV2-SECTION-10"
    subject = " ".join(
        (record.get("title", ""), atom.anchor, atom.source_clause)
    )
    if re.search(r"\b(?:Digital Twin|biometric|clone[ds]? (?:voice|face))\b", subject, re.I):
        return "MPV2-CUT5"
    if re.search(r"\bCut\s*5\b.{0,100}\b(?:enterprise|commercial)\b", subject, re.I):
        return "MPV2-CUT6"
    cut = re.search(r"\bCut\s*([1-6])\b", subject, re.I)
    if cut:
        return f"MPV2-CUT{cut.group(1)}"
    if re.search(r"\b(?:test|acceptance|quality|review|browser)\b", subject, re.I):
        return "MPV2-SECTION-11"
    if re.search(r"\b(?:provider|architecture|adapter|renderer|TTS|avatar)\b", subject, re.I):
        return "MPV2-SECTION-7"
    if re.search(r"\b(?:cost|spend|billing|credit|price)\b", subject, re.I):
        return "MPV2-SECTION-8"
    if re.search(r"\b(?:security|privacy|credential|secret|evidence)\b", subject, re.I):
        return "MPV2-SECTION-4"
    return "MPV2-SECTION-10"
def _external_new_atoms(manifest: dict[str, Any]) -> dict[str, Atom]:
    atoms: dict[str, Atom] = {}
    for record in manifest.get("records", []):
        if not isinstance(record, dict):
            continue
        for clause in record.get("clauses", []):
            alias = clause.get("suggestedAlias")
            if isinstance(alias, dict) and alias.get("kind") == "EXISTING_REQUIREMENT":
                continue
            atom = _external_clause_atom(record, clause)
            if atom.atom_id in atoms:
                raise ValueError("duplicate external authority atom")
            atoms[atom.atom_id] = atom
    return atoms
def _mapping_row(
    atom: Atom,
    *,
    source_kind: str,
    source_path: str,
    authority_refs: list[str],
    source_commit: str | None,
    source_git_blob: str | None,
    source_content_sha256: str,
    default_destination: str,
    normative_effect: str,
    replacements: dict[str, str],
    adoption_ref: str,
    span_coordinate_system: str = "ONE_BASED_INCLUSIVE_LINES",
) -> dict[str, Any]:
    destination = _destination(atom, default_destination)
    disposition, replacement, owner_ref = _disposition(
        atom, replacements, adoption_ref
    )
    row: dict[str, Any] = {
        "requirementId": atom.requirement_id,
        "sourceAtomId": atom.atom_id,
        "sourceId": atom.source_id,
        "sourceKind": source_kind,
        "sourcePath": source_path,
        "sourceAuthorityRefs": authority_refs,
        "sourceCommit": source_commit,
        "sourceGitBlob": source_git_blob,
        "sourceContentSha256": source_content_sha256,
        "sourceAnchor": atom.anchor,
        "sourceSpan": {
            "coordinateSystem": span_coordinate_system,
            "startLine": atom.source_span_start_line,
            "endLine": atom.source_span_end_line,
            "rawSha256": atom.raw_source_span_sha256,
        },
        "atomicFocusSha256": atom.clause_sha256,
        "normalizedAtomicRequirement": encode_requirement(atom),
        "normalizedSourceContext": _encode_source_text(atom.source_clause),
        "normalizedSourceContextSha256": atom.source_context_sha256,
        "atomicFocusStart": atom.focus_start,
        "atomicFocusEnd": atom.resolved_focus_end,
        "atomicFocusOccurrence": atom.focus_occurrence,
        "governingContext": _governing_context(atom),
        "semanticClass": "NORMATIVE_REQUIREMENT",
        "normativeEffect": normative_effect,
        "v2DestinationClause": destination,
        "disposition": disposition,
        "replacementId": replacement,
        "ownerAuthorityRef": owner_ref,
        "thresholdComparison": {},
        "rationale": "",
        "accountableOwner": "REPOSITORY_OWNER",
        "reviewer": "INDEPENDENT_REVIEWER_PENDING",
        "reviewTime": None,
        "result": "PENDING",
    }
    row["thresholdComparison"] = _derived_threshold_comparison(row)
    row["rationale"] = _expected_rationale(row)
    return row
_GENERATED_MAPPING_CACHE: dict[str, dict[str, Any]] = {}
def generate_mapping(
    root: Path,
    external_manifest: dict[str, Any] | None = None,
    *,
    copy_result: bool = True,
) -> dict[str, Any]:
    sources = _source_records(root)
    selected_external = _selected_external_authority_manifest(
        root, sources, external_manifest
    )
    cache_key = _sha256(
        _canonical_json(
            {
                "sources": sources,
                "externalAuthorityManifest": selected_external,
            }
        ).encode("utf-8")
    )
    cached = _GENERATED_MAPPING_CACHE.get(cache_key)
    if cached is not None:
        return copy.deepcopy(cached) if copy_result else cached
    content_addressed_refs = _content_addressed_reference_map(selected_external)
    source_bytes_by_id = {
        source["sourceId"]: frozen_source_bytes(root, source) for source in sources
    }
    atoms_by_source = {
        source["sourceId"]: _atoms(
            source["sourceId"], source["atomizer"],
            source_bytes_by_id[source["sourceId"]],
        )
        for source in sources
    }
    _validate_conflict_rules(atoms_by_source)
    owner_source = next(source for source in sources if source["sourceId"] == "OWNER_PLAN_2026_09_07")
    adoption_ref = owner_source["authorityRefs"][0]
    replacements = _owner_replacements(atoms_by_source["OWNER_PLAN_2026_09_07"])
    rows: list[dict[str, Any]] = []
    for source in sources:
        for atom in atoms_by_source[source["sourceId"]]:
            semantic_class = _semantic_class(atom, source["authorityLifecycle"])
            normative_effect = _SEMANTIC_EFFECTS[semantic_class]
            if normative_effect != "CURRENT_NORMATIVE":
                continue
            rows.append(
                _mapping_row(
                    atom,
                    source_kind=source["sourceKind"],
                    source_path=source["repositoryPath"],
                    authority_refs=(
                        [
                            content_addressed_refs.get(reference, reference)
                            for reference in _issue_refs(
                                f"{atom.anchor}\n{atom.source_clause}",
                                source["repositoryPath"],
                            )
                        ]
                        if source["sourceKind"] == "REPOSITORY_FILE"
                        else source["authorityRefs"]
                    ),
                    source_commit=source["sourceCommit"],
                    source_git_blob=source["sourceGitBlob"],
                    source_content_sha256=source["contentSha256"],
                    default_destination=source["defaultV2Destination"],
                    normative_effect=normative_effect,
                    replacements=replacements,
                    adoption_ref=adoption_ref,
                )
            )
    rows_by_atom = {row["sourceAtomId"]: row for row in rows}
    for record in selected_external.get("records", []):
        if not isinstance(record, dict) or record.get("authorityEffect") not in {
            "CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE", "MIXED_NORMATIVE",
        }:
            continue
        for clause in record.get("clauses", []):
            alias = clause.get("suggestedAlias")
            if isinstance(alias, dict) and alias.get("kind") == "EXISTING_REQUIREMENT":
                target = rows_by_atom.get(alias.get("sourceAtomId"))
                if target is not None:
                    target["sourceAuthorityRefs"] = sorted(
                        {*target["sourceAuthorityRefs"], record["contentAddressedRef"]}
                    )
                continue
            atom = _external_clause_atom(record, clause)
            row = _mapping_row(
                atom,
                source_kind=record["sourceKind"],
                source_path=record["sourceLocator"]["apiUrl"],
                authority_refs=[record["contentAddressedRef"]],
                source_commit=None,
                source_git_blob=None,
                source_content_sha256=record["contentSha256"],
                default_destination=_external_default_destination(record, atom),
                normative_effect=clause["normativeEffect"],
                replacements=replacements,
                adoption_ref=adoption_ref,
                span_coordinate_system="ORIGINAL_BODY_LINES_ONE_BASED_INCLUSIVE",
            )
            rows.append(row)
            rows_by_atom[row["sourceAtomId"]] = row
    rows.sort(key=lambda item: (item["sourceId"], item["sourceAnchor"], item["sourceAtomId"]))
    context_hashes = _context_chain_hashes(sources, source_bytes_by_id, atoms_by_source, rows, selected_external)
    duplicate_census = semantic_duplicate_census(rows, context_hashes)
    mapping = {
        "schemaVersion": "SupersetMappingV2",
        "mappingId": "narratwin-master-program-v2-superset",
        "proposalState": "PROPOSED",
        "cutoff": "2026-09-06T23:59:59+05:30",
        "ownerAuthority": adoption_ref,
        "sources": sources,
        "externalAuthorityManifest": selected_external,
        "semanticDuplicateCensus": duplicate_census,
        "rows": rows,
        "certification": {
            "structuralResult": "PASS",
            "semanticReview": "PENDING_INDEPENDENT_REVIEW",
            "ownerExactBytesApproval": "PENDING",
            "eligibleNonAuthorExactHead": "PENDING",
            "activation": "NONE",
        },
    }
    _GENERATED_MAPPING_CACHE[cache_key] = copy.deepcopy(mapping)
    return mapping if copy_result else _GENERATED_MAPPING_CACHE[cache_key]
def _indexed_mapping_rows(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[Any], list[list[int]]]:
    """Encode complete logical rows through one canonical first-use value table."""
    values: list[Any] = []
    indexes: dict[str, int] = {}
    encoded_rows: list[list[int]] = []
    for row in rows:
        if set(row) != _ROW_FIELDS:
            raise ValueError("logical mapping row shape invalid")
        expected_comparison = _derived_threshold_comparison(row)
        if row["thresholdComparison"] != expected_comparison:
            raise ValueError("logical mapping threshold comparison invalid")
        encoded: list[int] = []
        for column in STORED_ROW_COLUMNS:
            value = row[column]
            key = _canonical_json(value)
            index = indexes.get(key)
            if index is None:
                index = len(values)
                indexes[key] = index
                values.append(value)
            encoded.append(index)
        encoded_rows.append(encoded)
    value_sha256 = _sha256(_canonical_json(values).encode("utf-8"))
    comparison_sha256 = _sha256(
        _canonical_json([_derived_threshold_comparison(row) for row in rows]).encode()
    )
    return (
        {
            "kind": "INDEXED_VALUE_TABLE_WITH_COMMITTED_DERIVED_THRESHOLD_V2",
            "columns": list(STORED_ROW_COLUMNS),
            "coordinateSystem": "ROW_MAJOR_COLUMN_INDEX",
            "valueTableSha256": value_sha256,
            "derivedThresholdComparisonsSha256": comparison_sha256,
        },
        values,
        encoded_rows,
    )
_COLLECTIVE_CONTEXT_PARENT = "atom:56976cc2cab5ed0900e9351af1246afe8b66dd634f8473a8c02c44c47b845f98"
def _markdown_line_kind(line: str) -> tuple[str, int, int]:
    body = (text := line.rstrip("\r\n")).lstrip(" \t")
    heading = re.match(r"^(#{1,6})\s+\S", body)
    kind = "BLANK" if not body or body.startswith("<!--") and body.endswith("-->") else "HEADING" if heading else "LIST" if re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", body) else "FENCE" if body.startswith("```") else "TABLE" if body.startswith("|") and body.endswith("|") else "PROSE"
    return kind, len(text[: len(text) - len(body)].expandtabs(4)), len(heading.group(1)) if heading else 0
def _markdown_block_continues(parent: tuple[str, int, int], first: tuple[str, int, int], base: int, item: tuple[str, int, int]) -> bool:
    return (item[0] != "HEADING" or item[2] > base) if first[0] == "HEADING" else (item[0] == "BLANK" or item[0] != "HEADING" and item[1] > parent[1]) if parent[0] == "LIST" else (item[0] == "BLANK" or item[0] == "LIST" and item[1] >= first[1] or item[0] != "HEADING" and item[1] > first[1]) if first[0] == "LIST" else item[0] == "TABLE" if first[0] == "TABLE" else item[0] not in {"BLANK", "HEADING"}
def _governed_markdown_block(lines: list[str], atom: Atom) -> tuple[int, int, str] | None:
    metadata = [_markdown_line_kind(line) for line in lines]
    parent = metadata[atom.source_span_start_line - 1]
    start = next((index for index in range(atom.source_span_end_line, len(lines)) if metadata[index][0] != "BLANK"), len(lines))
    if start == len(lines):
        return None
    first = metadata[start]
    if first[0] == "FENCE":
        stop = next((index + 1 for index in range(start + 1, len(lines)) if metadata[index][0] == "FENCE"), len(lines))
        return start + 1, stop, _sha256("".join(lines[start:stop]).encode())
    base = next((metadata[index][2] for index in range(atom.source_span_start_line - 2, -1, -1) if metadata[index][0] == "HEADING"), 0)
    if first[0] == "HEADING" and first[2] <= base:
        return None
    stop = next((index for index in range(start + 1, len(lines)) if not _markdown_block_continues(parent, first, base, metadata[index])), len(lines))
    end = max(index for index in range(start, stop) if metadata[index][0] != "BLANK")
    return start + 1, end + 1, _sha256("".join(lines[start : end + 1]).encode())
def _markdown_parent(source: dict[str, Any], lines: list[str], atoms: list[Atom], atom: Atom) -> tuple[Atom, tuple[int, int, str], frozenset[str], str] | None:
    eligible = re.fullmatch(r"[^\n]+:", atom.text.strip()) and _SEMANTIC_EFFECTS[_semantic_class(atom, source["authorityLifecycle"])] == "CURRENT_NORMATIVE"
    if not eligible or (block := _governed_markdown_block(lines, atom)) is None:
        return None
    children = [child.atom_id for child in sorted((child for child in atoms if child.atom_id != atom.atom_id and block[0] <= child.source_span_start_line <= block[1] and (atom.atom_id != _COLLECTIVE_CONTEXT_PARENT or _SEMANTIC_EFFECTS[_semantic_class(child, source["authorityLifecycle"])] != "CURRENT_NORMATIVE")), key=lambda child: (child.source_span_start_line, child.source_span_end_line, child.anchor, child.focus_start, child.atom_id))]
    mode = "COLLECTIVE_SET_REQUIREMENT" if atom.atom_id == _COLLECTIVE_CONTEXT_PARENT else "BOUND_CONTEXT"
    material = {"kind": "REPOSITORY_MARKDOWN_GOVERNING_PARENT_V1", "sourceId": source["sourceId"], "sourceContentSha256": source["contentSha256"], "parentSourceAtomId": atom.atom_id, "parentAtomicFocusSha256": atom.clause_sha256, "parentSpan": [atom.source_span_start_line, atom.source_span_end_line], "governedBlock": [*block], "orderedGovernedChildAtomIds": children, "bindingMode": mode}
    if atom.atom_id == _COLLECTIVE_CONTEXT_PARENT and len(children) != 12:
        raise ValueError("collective governed set drift")
    return atom, block, frozenset(children), "RMGCTX-P-" + _sha256(_canonical_json(material).encode())
def _context_chain_hashes(sources: list[dict[str, Any]], source_bytes: dict[str, bytes], atoms_by_source: dict[str, list[Atom]], rows: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    parent_atoms: set[str] = set()
    for source in sources:
        if source["sourceKind"] != "REPOSITORY_FILE" or source["atomizer"] != "MARKDOWN_ATOMIC_V2":
            continue
        lines, atoms = source_bytes[source["sourceId"]].decode().splitlines(keepends=True), atoms_by_source[source["sourceId"]]
        parents = [parent for atom in atoms if (parent := _markdown_parent(source, lines, atoms, atom)) is not None]
        own = {atom.atom_id: parent_id for atom, _, _, parent_id in parents}
        parent_atoms.update(own)
        for child in atoms:
            enclosing = sorted((atom.source_span_start_line, -block[1], parent_id) for atom, block, governed, parent_id in parents if child.atom_id in governed)
            material = {"kind": "REPOSITORY_MARKDOWN_CONTEXT_CHAIN_V1", "sourceId": source["sourceId"], "sourceContentSha256": source["contentSha256"], "sourceAnchorSha256": _sha256(child.anchor.encode()), "ownGoverningParentId": own.get(child.atom_id), "orderedParentIds": [item[2] for item in enclosing]}
            out[child.atom_id] = _sha256(_canonical_json(material).encode())
    if _COLLECTIVE_CONTEXT_PARENT not in parent_atoms or not parent_atoms <= {row["sourceAtomId"] for row in rows}:
        raise ValueError("governing parent row missing")
    records, partition = manifest["records"], manifest["governingContextDecisionPartition"]
    if _external_governing_context_bindings_invalid(records, partition):
        raise ValueError("external context partition invalid")
    children = {item["childDecisionId"]: item for item in partition["childDecisions"]}
    relations = {item["relationId"]: item for item in partition["relations"]}
    parent_by_id = {item["parentId"]: item for item in partition["parents"]}
    for record in records:
        for clause in record["clauses"]:
            atom, ref = _external_clause_atom(record, clause), clause["governingContextDecisionRef"]
            relation_ids = [] if ref is None else children[ref["childDecisionId"]]["orderedRelationIds"]
            chain = [{"relationId": rid, "relationDecisionSha256": relations[rid]["relationDecisionSha256"], "parentId": relations[rid]["parentId"], "parentDecisionSha256": parent_by_id[relations[rid]["parentId"]]["parentDecisionSha256"]} for rid in relation_ids]
            material = {"kind": "EXTERNAL_AUTHORITY_CONTEXT_CHAIN_V1", "sourceId": atom.source_id, "sourceContentSha256": record["contentSha256"], "sourceAnchorSha256": _sha256(atom.anchor.encode()), "childDecisionRef": ref, "orderedContextChain": chain}
            out[atom.atom_id] = _sha256(_canonical_json(material).encode())
    for row in rows:
        material = {"kind": "STRUCTURAL_ATOM_CONTEXT_V1", "sourceId": row["sourceId"], "sourceContentSha256": row["sourceContentSha256"], "sourceAnchorSha256": _sha256(row["sourceAnchor"].encode())}
        out.setdefault(row["sourceAtomId"], _sha256(_canonical_json(material).encode()))
    return out
def semantic_duplicate_census(
    rows: list[dict[str, Any]], context_hashes: dict[str, str]
) -> dict[str, Any]:
    """Bind every repeated focus/context signature for independent resolution."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["atomicFocusSha256"], row["normalizedSourceContextSha256"])
        grouped.setdefault(key, []).append(row)
    groups: list[dict[str, Any]] = []
    for (focus_hash, context_hash), members in sorted(grouped.items()):
        if len(members) < 2:
            continue
        bindings = [{"sourceAtomId": member["sourceAtomId"], "contextChainSha256": context_hashes[member["sourceAtomId"]]} for member in sorted(members, key=lambda item: item["sourceAtomId"])]
        material = {"atomicFocusSha256": focus_hash, "normalizedSourceContextSha256": context_hash}
        groups.append(
            {
                "groupId": "duplicate:" + _sha256(_canonical_json(material).encode("utf-8")),
                **material,
                "members": bindings,
            }
        )
    summary = {
        "schemaVersion": "SemanticDuplicateCensusV1",
        "signature": "ATOMIC_FOCUS_SHA256_PLUS_NORMALIZED_SOURCE_CONTEXT_SHA256",
        "groupCount": len(groups),
        "occurrenceCount": sum(len(group["members"]) for group in groups),
        "excessOccurrenceCount": sum(len(group["members"]) - 1 for group in groups),
        "groups": groups,
    }
    ordered_group_sha256 = _sha256(_canonical_json(groups).encode("utf-8"))
    return summary | {
        "orderedGroupSha256": ordered_group_sha256,
        "resolutionOverlay": {
            "schemaVersion": "SemanticDuplicateResolutionOverlayV1",
            "state": "PENDING_INDEPENDENT_REVIEW",
            "censusSha256": ordered_group_sha256,
            "decisions": [],
            "orderedDecisionSha256": _sha256(b"[]"),
            "reviewerReceiptRef": None,
            "reviewedAt": None,
            "result": "PENDING",
        },
    }
def decode_mapping_artifact(artifact: Any) -> dict[str, Any]:
    """Expand the committed indexed representation into complete logical rows."""
    if not isinstance(artifact, dict) or set(artifact) != _MAPPING_ARTIFACT_FIELDS:
        raise ValueError("mapping artifact shape invalid")
    encoding = artifact.get("rowEncoding")
    values = artifact.get("rowValues")
    encoded_rows = artifact.get("rows")
    if (
        not isinstance(encoding, dict)
        or set(encoding)
        != {"kind", "columns", "coordinateSystem", "valueTableSha256", "derivedThresholdComparisonsSha256"}
        or encoding.get("kind") != "INDEXED_VALUE_TABLE_WITH_COMMITTED_DERIVED_THRESHOLD_V2"
        or encoding.get("columns") != list(STORED_ROW_COLUMNS)
        or encoding.get("coordinateSystem") != "ROW_MAJOR_COLUMN_INDEX"
        or not isinstance(values, list)
        or not isinstance(encoded_rows, list)
        or encoding.get("valueTableSha256")
        != _sha256(_canonical_json(values).encode("utf-8"))
    ):
        raise ValueError("mapping row encoding invalid")
    canonical_values = [_canonical_json(value) for value in values]
    if len(canonical_values) != len(set(canonical_values)):
        raise ValueError("mapping value table duplicates")
    referenced = [False] * len(values)
    rows: list[dict[str, Any]] = []
    for encoded in encoded_rows:
        if (
            not isinstance(encoded, list)
            or len(encoded) != len(STORED_ROW_COLUMNS)
            or any(
                isinstance(index, bool)
                or not isinstance(index, int)
                or index < 0
                or index >= len(values)
                for index in encoded
            )
        ):
            raise ValueError("mapping encoded row invalid")
        for index in encoded:
            referenced[index] = True
        row = {column: copy.deepcopy(values[index]) for column, index in zip(STORED_ROW_COLUMNS, encoded, strict=True)}
        row["thresholdComparison"] = _derived_threshold_comparison(row)
        rows.append(row)
    if values and not all(referenced):
        raise ValueError("mapping value table contains unreferenced value")
    if encoding["derivedThresholdComparisonsSha256"] != _sha256(
        _canonical_json([row["thresholdComparison"] for row in rows]).encode()
    ):
        raise ValueError("mapping derived threshold digest invalid")
    return {
        key: copy.deepcopy(value)
        for key, value in artifact.items()
        if key not in {"rowEncoding", "rowValues", "rows"}
    } | {"rows": rows}
def render_mapping(mapping: dict[str, Any]) -> str:
    def compact(value: Any) -> str:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
    def detector_safe(value: Any) -> str:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",      ", ":      ")
        )
    expected_metadata = {
        "schemaVersion": "SupersetMappingV2",
        "mappingId": "narratwin-master-program-v2-superset",
        "proposalState": "PROPOSED",
        "cutoff": "2026-09-06T23:59:59+05:30",
    }
    if (
        set(mapping) != _MAPPING_FIELDS
        or not isinstance(mapping.get("rows"), list)
        or any(mapping.get(key) != value for key, value in expected_metadata.items())
    ):
        raise ValueError("logical mapping shape invalid")
    row_encoding, row_values, encoded_rows = _indexed_mapping_rows(mapping["rows"])
    lines = [
        "{",
        '  "schemaVersion":"SupersetMappingV2",',
        '  "mappingId":"narratwin-master-program-v2-superset",',
        '  "proposalState":"PROPOSED",',
        '  "cutoff":"2026-09-06T23:59:59+05:30",',
        '  "ownerAuthority":' + compact(mapping["ownerAuthority"]) + ",",
        '  "sources":' + compact(mapping["sources"]) + ",",
        '  "externalAuthorityManifest":'
        + compact(mapping["externalAuthorityManifest"])
        + ",",
        '  "semanticDuplicateCensus":'
        + compact(mapping["semanticDuplicateCensus"])
        + ",",
        '  "rowEncoding":' + compact(row_encoding) + ",",
        '  "rowValues":' + detector_safe(row_values) + ",",
        '  "rows":' + compact(encoded_rows) + ",",
        '  "certification":' + compact(mapping["certification"]),
        "}",
    ]
    return "\n".join(lines) + "\n"
def _load_json(path: Path) -> Any:
    return _load_json_text(path.read_text(encoding="utf-8"))
def _load_json_text(text: str) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateJsonMember(key)
            result[key] = value
        return result
    return json.loads(
        text,
        object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
    )
def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
def ordered_requirement_digest(mapping: dict[str, Any]) -> str:
    ordered = [
        {
            "requirementId": row["requirementId"],
            "sourceAtomId": row["sourceAtomId"],
            "sourceSpan": row["sourceSpan"],
            "atomicFocusSha256": row["atomicFocusSha256"],
            "normalizedSourceContextSha256": row[
                "normalizedSourceContextSha256"
            ],
            "atomicFocusStart": row["atomicFocusStart"],
            "atomicFocusEnd": row["atomicFocusEnd"],
            "v2DestinationClause": row["v2DestinationClause"],
            "disposition": row["disposition"],
            "replacementId": row["replacementId"],
            "ownerAuthorityRef": row["ownerAuthorityRef"],
            "thresholdComparison": row["thresholdComparison"],
        }
        for row in mapping["rows"]
    ]
    return _sha256(_canonical_json(ordered).encode("utf-8"))
def _schema_instance_failures(
    value: Any,
    schema: Any,
    *,
    definition: str,
    failure_code: str,
) -> list[str]:
    """Execute the closed JSON-Schema subset already used by repository tooling."""
    schema_maps = {"$defs", "properties"}
    schema_lists = {"oneOf"}
    executable = {
        "$schema", "$id", "$ref", "title", "$defs", "type", "oneOf",
        "const", "enum", "minimum", "required", "properties",
        "additionalProperties", "minItems", "maxItems", "uniqueItems",
        "items", "minLength", "pattern", "format",
    }
    def unsupported(rule: Any) -> bool:
        if not isinstance(rule, dict) or set(rule) - executable:
            return True
        if "$ref" in rule and set(rule) != {"$ref"}:
            return True
        if "oneOf" in rule and set(rule) != {"oneOf"}:
            return True
        for key in schema_maps:
            children = rule.get(key)
            if children is not None and (
                not isinstance(children, dict)
                or any(unsupported(child) for child in children.values())
            ):
                return True
        for key in schema_lists:
            children = rule.get(key)
            if children is not None and (
                not isinstance(children, list)
                or any(unsupported(child) for child in children)
            ):
                return True
        for key in ("items", "additionalProperties"):
            child = rule.get(key)
            if child is not None and not isinstance(child, bool) and unsupported(child):
                return True
        return False
    if (
        not isinstance(schema, dict)
        or not isinstance(schema.get("$defs"), dict)
        or unsupported(schema)
    ):
        return [failure_code]
    root_rule = {
        key: item
        for key, item in schema.items()
        if key not in {"$schema", "$id", "title", "$defs"}
    }
    contract = {"$defs": {**schema["$defs"], definition: root_rule}}
    try:
        invalid = bool(validate_schema_instance(value, contract, definition))
    except Exception:
        return [failure_code]
    return [failure_code] if invalid else []
def expected_source_records(root: Path) -> dict[str, dict[str, Any]]:
    return {source["sourceId"]: source for source in _source_records(root)}
def expected_source_atoms(root: Path, mapping: dict[str, Any] | None = None) -> dict[str, Atom]:
    del mapping
    result: dict[str, Atom] = {}
    for source in expected_source_records(root).values():
        data = frozen_source_bytes(root, source)
        for atom in _atoms(source["sourceId"], source["atomizer"], data):
            result[atom.atom_id] = atom
    return result
def expected_normative_atoms(root: Path) -> dict[str, Atom]:
    result: dict[str, Atom] = {}
    for source in expected_source_records(root).values():
        for atom in _atoms(
            source["sourceId"], source["atomizer"], frozen_source_bytes(root, source)
        ):
            if (
                _SEMANTIC_EFFECTS[
                    _semantic_class(atom, source["authorityLifecycle"])
                ]
                == "CURRENT_NORMATIVE"
            ):
                result[atom.atom_id] = atom
    return result
def _taxonomy_failures(value: Any) -> list[str]:
    if (
        not isinstance(value, dict)
        or set(value) != _TAXONOMY_FIELDS
        or value.get("schemaVersion") != "CutTaxonomyV2"
        or value.get("taxonomyId") != "narratwin-six-cut-taxonomy-v2"
        or value.get("proposalState") != "PROPOSED"
        or value.get("effectiveAt") is not None
    ):
        return ["MPV2.TAXONOMY.SCHEMA_INVALID"]
    failures: list[str] = []
    collections = ("engineeringStages", "productModes", "cuts", "cut5CapabilityDependencies", "laneA", "historicalCheckpoints", "adrPlans", "digitalTwinSequence")
    ids: list[str] = []
    for name in collections:
        items = value.get(name)
        if not isinstance(items, list):
            failures.append("MPV2.TAXONOMY.SCHEMA_INVALID")
            continue
        if not all(isinstance(item, dict) for item in items):
            failures.append("MPV2.TAXONOMY.SCHEMA_INVALID")
            continue
        local = [item.get("id") for item in items]
        if not all(isinstance(item, str) for item in local):
            failures.append("MPV2.TAXONOMY.SCHEMA_INVALID")
            continue
        if len(local) != len(set(local)):
            failures.append("MPV2.TAXONOMY.DUPLICATE_ID")
        ids.extend(item for item in local if isinstance(item, str))
    if "MPV2.TAXONOMY.SCHEMA_INVALID" in failures:
        return list(dict.fromkeys(failures))
    if len(ids) != len(set(ids)):
        failures.append("MPV2.TAXONOMY.DUPLICATE_ID")
    cuts = {item.get("id"): item for item in value.get("cuts", []) if isinstance(item, dict)}
    if cuts.get("Cut5", {}).get("name") != "Owner personal Digital Twin" or cuts.get("Cut6", {}).get("name") != "Enterprise and commercial readiness":
        failures.append("MPV2.TAXONOMY.CUT_MEANING_INVALID")
    expected_dependencies = {
        "Cut1": [],
        "Cut2": ["Cut1"],
        "Cut3": ["Cut1"],
        "Cut4": ["Cut1"],
        "Cut5": ["Cut1", "Cut2", "Cut3"],
        "Cut6": ["Cut1", "Cut2", "Cut3", "Cut4", "Cut5"],
    }
    if {
        cut_id: cuts.get(cut_id, {}).get("dependsOn")
        for cut_id in expected_dependencies
    } != expected_dependencies:
        failures.append("MPV2.TAXONOMY.CUT_DEPENDENCY_INVALID")
    expected_capability_dependencies = {
        "PREPARED_ENGLISH": ("DT4", ["Cut1"], True),
        "SCREEN_GUIDED": ("DT5", ["Cut1"], True),
        "MULTILINGUAL_PREPARED": ("DT5", ["Cut1", "Cut2"], True),
        "GROUNDED_REALTIME": ("DT6", ["Cut1", "Cut3"], True),
        "EXPANDED_MOTION": ("DT4", ["Cut1", "Cut4"], False),
    }
    capability_dependencies = value.get("cut5CapabilityDependencies", [])
    actual_capability_dependencies = {
        item.get("id"): (
            item.get("minimumStep"),
            item.get("requiresCuts"),
            item.get("requiredForCut5Completion"),
        )
        for item in capability_dependencies
        if isinstance(item, dict)
    }
    if (
        value.get("cutDependencySemantics")
        != "CUT_COMPLETION_PREREQUISITES"
        or len(actual_capability_dependencies) != len(capability_dependencies)
        or actual_capability_dependencies != expected_capability_dependencies
    ):
        failures.append("MPV2.TAXONOMY.CUT5_CAPABILITY_DEPENDENCY_INVALID")
    aliases = value.get("legacyAliases", [])
    alias = (
        aliases[0]
        if isinstance(aliases, list)
        and len(aliases) == 1
        and isinstance(aliases[0], dict)
        else {}
    )
    if alias.get("alias") != "LegacyCut5Enterprise" or alias.get("canonicalCut") != "Cut6":
        failures.append("MPV2.TAXONOMY.LEGACY_CUT5_TARGET_INVALID")
    if alias.get("canSatisfyNewCut5") is not False:
        failures.append("MPV2.TAXONOMY.LEGACY_EVIDENCE_CROSSED")
    if alias.get("cut6MigrationValidationRequired") is not True:
        failures.append("MPV2.TAXONOMY.CUT6_MIGRATION_BYPASSED")
    expected_migration = {
        "migrationId": "legacy-cut5-enterprise-to-cut6-v1",
        "candidateState": "PENDING_ACCEPTED_CURRENT_TRANSITION",
        "atomicity": "ALL_REQUIRED_SURFACES_OR_NONE",
        "effectiveTimeSource": "ACCEPTED_CURRENT_TRANSITION_MERGED_AT",
        "requiredSurfaces": [
            "SCHEMA_VERSIONS", "ROADMAP_REFERENCES", "STATUS_RECORDS", "TESTS",
            "ISSUE_TEMPLATES", "COMPLETION_EVENTS", "TRACEABILITY_RECORDS",
        ],
        "postEffectiveLegacyReferencePolicy": (
            "TYPED_SCHEMA_VERSION_OR_LEGACY_ALIAS_REQUIRED"
        ),
    }
    if value.get("compatibilityMigration") != expected_migration:
        failures.append("MPV2.TAXONOMY.COMPATIBILITY_MIGRATION_INVALID")
    digital_twin_sequence = value.get("digitalTwinSequence", [])
    if [item.get("id") for item in digital_twin_sequence] != [f"DT{i}" for i in range(8)]:
        failures.append("MPV2.TAXONOMY.DT_SEQUENCE_INCOMPLETE")
    expected_step_dependencies = {
        "DT0": [],
        **{f"DT{number}": [f"DT{number - 1}"] for number in range(1, 8)},
    }
    if {
        item.get("id"): item.get("dependsOnSteps")
        for item in digital_twin_sequence
        if isinstance(item, dict)
    } != expected_step_dependencies:
        failures.append("MPV2.TAXONOMY.DT_DEPENDENCY_INVALID")
    checkpoints = {item.get("id"): item.get("v2Destinations") for item in value.get("historicalCheckpoints", []) if isinstance(item, dict)}
    for checkpoint in ("Checkpoint2", "Checkpoint3B", "Checkpoint3C"):
        if checkpoints.get(checkpoint) != ["Cut5"]:
            failures.append("MPV2.TAXONOMY.CHECKPOINT_MIGRATION_INVALID")
            break
    activation = value.get("activation", {})
    if activation != {"authority": "NONE", "v1RemainsEffective": True, "candidatePresenceActivates": False, "requiresSeparateAcceptedCurrentTransition": True}:
        failures.append("MPV2.TAXONOMY.ACTIVATION_INVALID")
    return failures
def _destination_registry_failures(document: str) -> list[str]:
    if document.count(DESTINATION_POLICY) != 1:
        return ["MPV2.MAPPING.DESTINATION_REGISTRY_MISSING"]
    for clause_id in DESTINATION_CLAUSES:
        marker = f"<!-- MPV2-DESTINATION:{clause_id} -->"
        if document.count(marker) != 1:
            return ["MPV2.MAPPING.DESTINATION_REGISTRY_MISSING"]
    return []
def _parse_github_time(value: Any) -> datetime:
    if not isinstance(value, str) or re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value
    ) is None:
        raise ValueError("invalid GitHub timestamp")
    parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    if parsed.tzinfo is None:
        raise ValueError("invalid GitHub timestamp")
    return parsed
def _external_alias_invalid(alias: Any) -> bool:
    if alias == "NEW_ROW_REQUIRED":
        return False
    if not isinstance(alias, dict):
        return True
    if alias.get("kind") == "EXISTING_REQUIREMENT":
        return (
            set(alias) != {
                "equivalentCandidateCount", "kind", "matchBasis", "requirementId",
                "sourceAtomId", "sourceId", "v2DestinationClause",
            }
            or alias.get("equivalentCandidateCount") != 1
            or alias.get("matchBasis")
            != "EXACT_CANONICAL_ATOMIC_FOCUS_AND_CONTEXT_AND_SCOPE"
            or not isinstance(alias.get("sourceAtomId"), str)
            or re.fullmatch(r"atom:[0-9a-f]{64}", alias.get("sourceAtomId", ""))
            is None
        )
    if alias.get("disposition") == "NEW_ROW_REQUIRED":
        return set(alias) != {"disposition"}
    return alias.get("disposition") != "ALIAS_PROPOSED"
def _external_classification_invalid(record: dict[str, Any]) -> bool:
    clauses = record.get("clauses")
    basis = record.get("classificationBasis")
    coverage = record.get("semanticCoverage")
    sanitization = record.get("sanitization")
    candidate_count = (
        coverage.get("candidateUnitCount") if isinstance(coverage, dict) else None
    )
    excluded_count = (
        coverage.get("excludedUnitCount") if isinstance(coverage, dict) else None
    )
    normative_count = (
        coverage.get("normativeClauseCount") if isinstance(coverage, dict) else None
    )
    authority_effect = record.get("authorityEffect")
    representation = record.get("representation")
    coverage_mode = record.get("coverageMode")
    partition_sha256 = (
        coverage.get("orderedCandidatePartitionSha256")
        if isinstance(coverage, dict)
        else None
    )
    if (
        not isinstance(authority_effect, str) or authority_effect not in {
            "CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE", "MIXED_NORMATIVE",
            "HISTORICAL_ONLY", "EVIDENCE_ONLY", "REFERENCE_ONLY",
        }
        or not isinstance(representation, str) or representation not in {
            "SANITIZED_ATOMIC_CLAUSES", "HASH_ONLY_CLASSIFIED",
        }
        or not isinstance(coverage_mode, str) or coverage_mode not in {
            "ATOMIC_SANITIZED_CLAUSES", "HASH_BOUND_NONNORMATIVE_DISPOSITION",
        }
        or record.get("coverageStatus") != "CLASSIFIED_AND_ATOMIZED"
        or not isinstance(record.get("title"), str)
        or not isinstance(clauses, list)
        or not isinstance(basis, dict)
        or set(basis) != {
            "code", "contentAddressedRef", "facts", "rationale", "basisSha256",
        }
        or not all(isinstance(basis.get(key), str) and basis[key] for key in (
            "code", "contentAddressedRef", "rationale", "basisSha256"
        ))
        or not isinstance(basis.get("facts"), dict)
        or basis["contentAddressedRef"] != record.get("contentAddressedRef")
        or basis["basisSha256"] != _sha256(
            _canonical_json({
                key: value for key, value in basis.items() if key != "basisSha256"
            }).encode("utf-8")
        )
        or not isinstance(coverage, dict)
        or set(coverage) != {
            "candidateUnitCount", "excludedUnitCount", "mode",
            "normativeClauseCount", "orderedCandidatePartitionSha256",
            "zeroUnclassifiedUnits",
        }
        or not isinstance(candidate_count, int)
        or isinstance(candidate_count, bool)
        or candidate_count < 0
        or not isinstance(excluded_count, int)
        or isinstance(excluded_count, bool)
        or excluded_count < 0
        or not isinstance(normative_count, int)
        or isinstance(normative_count, bool)
        or normative_count < 0
        or not isinstance(coverage.get("mode"), str)
        or not isinstance(partition_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", partition_sha256) is None
        or coverage.get("zeroUnclassifiedUnits") is not True
        or normative_count != len(clauses)
        or candidate_count != normative_count + excluded_count
        or not isinstance(sanitization, dict)
        or set(sanitization) != {
            "personalAbsolutePathsNeverEmitted", "rawBodyNeverEmitted",
            "recognizedSecretsNeverEmitted", "redactionClasses",
            "redactionCount", "result",
        }
        or any(sanitization.get(key) is not True for key in (
            "personalAbsolutePathsNeverEmitted", "rawBodyNeverEmitted",
            "recognizedSecretsNeverEmitted",
        ))
        or sanitization.get("result") != "PASS"
        or not isinstance(sanitization.get("redactionClasses"), list)
        or not all(isinstance(item, str) for item in sanitization["redactionClasses"])
        or sanitization["redactionClasses"] != sorted(set(sanitization["redactionClasses"]))
        or not isinstance(sanitization.get("redactionCount"), int)
        or isinstance(sanitization["redactionCount"], bool)
        or sanitization["redactionCount"] < 0
    ):
        return True
    effects: set[str] = set()
    clause_ids: list[str] = []
    for clause in clauses:
        if not isinstance(clause, dict) or set(clause) != _EXTERNAL_CLAUSE_FIELDS:
            return True
        focus = clause.get("normalizedAtomicFocus")
        context = clause.get("normalizedSourceContext")
        start, end = clause.get("atomicFocusStart"), clause.get("atomicFocusEnd")
        occurrence = clause.get("atomicFocusOccurrence")
        span = clause.get("sourceSpan")
        redaction = clause.get("redactionAttestation")
        alias = clause.get("suggestedAlias")
        if (
            not isinstance(focus, str) or not focus
            or not isinstance(context, str) or not context
            or not isinstance(start, int) or isinstance(start, bool)
            or not isinstance(end, int) or isinstance(end, bool)
            or not isinstance(occurrence, int) or isinstance(occurrence, bool)
            or start < 0 or end <= start or occurrence < 1
            or context[start:end] != focus
            or context[:start].count(focus) + 1 != occurrence
            or clause.get("atomicFocusSha256") != _sha256(focus.encode("utf-8"))
            or clause.get("normalizedSourceContextSha256")
            != _sha256(context.encode("utf-8"))
            or clause.get("offsetCoordinateSystem")
            != "UNICODE_CODEPOINTS_ZERO_BASED_HALF_OPEN"
            or clause.get("sourceReference") != record["reference"]
            or clause.get("sourceContentSha256") != record["contentSha256"]
            or not isinstance(clause.get("normativeEffect"), str)
            or clause["normativeEffect"] not in {
                "CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE",
            }
            or not isinstance(clause.get("classificationBasisCode"), str)
            or not isinstance(clause.get("clauseId"), str)
            or not isinstance(clause.get("sourceAnchor"), str)
            or not isinstance(clause.get("losslessNormalizationAttestation"), dict)
            or not clause["losslessNormalizationAttestation"]
            or not isinstance(span, dict)
            or set(span) != {
                "bindingKind", "coordinateSystem", "endLine",
                "restrictedSourceSpanBindingSha256", "sanitizedSpanSha256",
                "startLine",
            }
            or not isinstance(span.get("bindingKind"), str)
            or span["bindingKind"] not in {
                "EXACT_ORIGINAL_LINE_SPAN",
                "SOURCE_HASH_LINES_AND_NORMALIZED_CONTEXT",
            }
            or span.get("coordinateSystem")
            != "ORIGINAL_BODY_LINES_ONE_BASED_INCLUSIVE"
            or not all(
                isinstance(span.get(key), int) and span[key] >= 1
                for key in ("startLine", "endLine")
            )
            or span["endLine"] < span["startLine"]
            or any(
                not isinstance(span.get(key), str)
                or re.fullmatch(r"[0-9a-f]{64}", span[key]) is None
                for key in (
                    "restrictedSourceSpanBindingSha256", "sanitizedSpanSha256"
                )
            )
            or not isinstance(redaction, dict)
            or set(redaction) != {"applied", "classes", "removedValuesNeverEmitted"}
            or not isinstance(redaction.get("applied"), bool)
            or not isinstance(redaction.get("classes"), list)
            or redaction["applied"] != bool(redaction["classes"])
            or redaction.get("removedValuesNeverEmitted") is not True
            or _external_alias_invalid(alias)
        ):
            return True
        effects.add(clause["normativeEffect"])
        clause_ids.append(clause["clauseId"])
    if len(clause_ids) != len(set(clause_ids)):
        return True
    if coverage["excludedUnitCount"] == 0 and coverage[
        "orderedCandidatePartitionSha256"
    ] != _sha256(_canonical_json(clause_ids).encode("utf-8")):
        return True
    expected_effect = (
        "MIXED_NORMATIVE" if len(effects) > 1 else next(iter(effects), record["authorityEffect"])
    )
    normative_record = record["authorityEffect"] in {
        "CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE", "MIXED_NORMATIVE",
    }
    return (
        (normative_record != bool(clauses))
        or (clauses and record["authorityEffect"] != expected_effect)
        or (record["representation"] == "SANITIZED_ATOMIC_CLAUSES") != bool(clauses)
        or (record["coverageMode"] == "ATOMIC_SANITIZED_CLAUSES") != bool(clauses)
    )
def _external_context_semantics_invalid(records: Any, p: Any) -> bool:
    prec = (
        "NON_ACTIVATING_SEMANTIC_PRECEDENCE_INPUT",
        EXTERNAL_CLASSIFICATION_PRECEDENCE_INPUT_SHA256,
        "NONE",
    )
    def digest(value: Any) -> str:
        return _sha256(_canonical_json(value).encode())
    def identity(value: dict[str, Any]) -> tuple[Any, ...]:
        return value["sourceReference"], value["candidateUnitId"], value["atomicFocusSha256"]
    def parent_identity(value: dict[str, Any]) -> tuple[Any, ...]:
        return value["parentReference"], value["parentCandidateUnitId"], value["parentAtomicFocusSha256"]
    def precedence(value: dict[str, Any]) -> tuple[Any, ...]:
        return value["semanticPrecedenceInputRole"], value["semanticPrecedenceInputSha256"], value["semanticPrecedenceInputActivation"]
    def binding_key(value: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(value[key] for key in ("sourceReference", "sourceContentSha256", "atomicFocusSha256", "atomicFocusStart", "atomicFocusEnd", "atomicFocusOccurrence", "normalizedSourceContextSha256"))
    def parent_projection(value: dict[str, Any]) -> dict[str, Any]:
        return {"reference": value["parentReference"], "candidateUnitId": value["parentCandidateUnitId"], "atomicFocusSha256": value["parentAtomicFocusSha256"]}
    try:
        parents, rels, children, succs, leaves = (p[k] for k in ("parents", "relations", "childDecisions", "resolvedExactContextSuccessions", "contextSuccessionLeafReviews"))
        pb, rb, cb = ({x[key]: x for x in values} for values, key in ((parents, "parentId"), (rels, "relationId"), (children, "childDecisionId")))
        pairs = {"GOVERNING_CONTEXT_PRESERVES_CHILD_CLASS": {"BOUND_GOVERNING_CONTEXT_PRESERVES_CHILD_CLASS"}, "STRUCTURAL_NO_INHERITANCE": {"STRUCTURAL_BOUNDARY_WITHOUT_SEMANTIC_INHERITANCE"}, "GOVERNING_CONTEXT_PROMOTES_CHILD": {"EXACT_GOVERNING_PARENT_PATH_MEMBER_CAUSALLY_PROMOTES_REFERENCE", "EXACT_GOVERNING_PARENT_DIGEST_MEMBER_CAUSALLY_PROMOTES_REFERENCE"}}
        if any((precedence(x) != prec if x["parentDisposition"] == "GOVERNING_INTRODUCER" else precedence(x) != (None, None, None)) for x in parents):
            return True
        if any(r["relationDecisionBasisCode"] not in pairs.get(r["relationEffect"], set()) or r["parentReference"] != cb[r["childDecisionId"]]["sourceReference"] for r in rels):
            return True
        incoming = defaultdict(list)
        for relation in rels:
            incoming[relation["childDecisionId"]].append(relation)
        for c in children:
            effects = [b["normativeEffect"] for b in c["projectedClauseBindings"]]
            folded = "MIXED_NORMATIVE" if len(set(effects)) > 1 else effects[0] if effects else None
            promoted = c["originalSemanticClass"] == "REFERENCE" and c["effectiveSemanticClass"] == "NORMATIVE_REQUIREMENT"
            edges = [r for r in incoming[c["childDecisionId"]] if r["relationEffect"] == "GOVERNING_CONTEXT_PROMOTES_CHILD"]
            nonnorm = {"CONTEXT_INTRODUCER": "CONTEXT_ONLY", "COST_ESTIMATE": "EVIDENCE_ONLY", "EVIDENCE": "EVIDENCE_ONLY", "HISTORICAL_FACT": "HISTORICAL_ONLY", "REFERENCE": "REFERENCE_ONLY"}
            if not incoming[c["childDecisionId"]] or bool(effects) != (c["effectiveSemanticClass"] == "NORMATIVE_REQUIREMENT") or (effects and c["effectiveAuthorityEffect"] != folded) or (not effects and c["effectiveAuthorityEffect"] != nonnorm[c["effectiveSemanticClass"]]):
                return True
            if promoted != bool(edges) or len(edges) > 1 or (promoted and (c["inheritanceDisposition"], c["effectiveAuthorityEffect"]) != ("INHERITED_CURRENT_NORMATIVE", "CURRENT_NORMATIVE")):
                return True
            if not promoted and c["originalSemanticClass"] != "NORMATIVE_REQUIREMENT" and c["effectiveSemanticClass"] != c["originalSemanticClass"]:
                return True
        if set(pb) != {r["parentId"] for r in rels}:
            return True
        bypred = defaultdict(list)
        for succession in succs:
            bypred[identity(succession["predecessor"])].append(succession)
        for parent in parents:
            matches = bypred[parent_identity(parent)]
            if parent["contextAuthorityEffect"] == "SUPERSEDED_CONTEXT":
                if len(matches) != 1 or parent["contextSuccessionRuleCode"] != matches[0]["ruleCode"] or parent["contextSuccessorBinding"] != matches[0]["successor"]:
                    return True
            elif matches or parent["contextSuccessionRuleCode"] is not None or parent["contextSuccessorBinding"] is not None:
                return True
        clauses = {c["clauseId"]: (r, c) for r in records for c in r["clauses"]}
        for s in succs:
            legacy = s["relocatedFromClauseSuccession"]
            roles = []
            if precedence(s) != prec or precedence(legacy) != prec or legacy["partialCandidateProjection"] is not False or legacy["pairDecisionSha256"] != digest({k: v for k, v in legacy.items() if k != "pairDecisionSha256"}):
                return True
            for side in ("predecessor", "successor"):
                endpoint, sem, inner = s[side], s[side + "EndpointSemantics"], legacy[side]
                parent = next((x for x in parents if parent_identity(x) == identity(endpoint)), None)
                if parent:
                    expected: tuple[str, list[str], str, str, str | None] = ("GOVERNING_CONTEXT", [], "CONTEXT_INTRODUCER", "CONTEXT_ONLY", parent["contextAuthorityEffect"])
                else:
                    record, clause = clauses[inner["clauseId"]]
                    source = {"sourceReference": record["reference"], "sourceContentSha256": record["contentSha256"], **clause}
                    fields = ("sourceReference", "sourceContentSha256", "atomicFocusSha256", "atomicFocusStart", "atomicFocusEnd", "atomicFocusOccurrence", "normalizedSourceContextSha256")
                    if any(inner[k] != source[k] for k in fields):
                        return True
                    expected = ("NORMATIVE_CLAUSE", [inner["clauseId"]], "NORMATIVE_REQUIREMENT", clause["normativeEffect"], None)
                if (sem["endpointRole"], sem["clauseIds"], sem["semanticClass"], sem["candidateAuthorityEffect"], sem["contextAuthorityEffect"]) != expected:
                    return True
                roles.append(expected[0])
            if s["successionKind"] != "_TO_".join(roles):
                return True
        exact = {(r["reference"], r["contentSha256"], c["atomicFocusSha256"], c["atomicFocusStart"], c["atomicFocusEnd"], c["atomicFocusOccurrence"], c["normalizedSourceContextSha256"]) for r in records for c in r["clauses"]}
        reviewed, semantic, proofs, dispositions = cast(tuple[set[str], list[dict[str, Any]], Counter[str], Counter[str]], (set(), [], Counter(), Counter()))
        for leaf in leaves:
            relation, child = rb[leaf["parentRelationId"]], cb[leaf["childDecisionId"]]
            parent = pb[relation["parentId"]]
            reviewed.add(relation["relationId"])
            if parent["contextAuthorityEffect"] != "SUPERSEDED_CONTEXT" or leaf["contextSuccessorBinding"] != parent["contextSuccessorBinding"] or leaf["effectiveAuthorityEffect"] != child["effectiveAuthorityEffect"] or precedence(leaf) != prec:
                return True
            member, successor, independent, disposition = leaf["successorMemberBinding"], leaf["leafSuccessorBinding"], leaf["independentAuthorityBinding"], leaf["disposition"]
            proof = None
            if disposition == "RETAINED_MEMBER_OF_SUPERSEDING_SET":
                if successor is not None or independent is not None or not member or leaf["matchBasisCode"] != "EXACT_OWNER_SUCCESSOR_RETAINS_PREDECESSOR_SET_MEMBERS" or child["effectiveAuthorityEffect"] != "CURRENT_NORMATIVE":
                    return True
                predecessor, proof = member["predecessorMemberBinding"], member["bindingKind"]
                if member["predecessorMemberRelationId"] != leaf["parentRelationId"] or (predecessor["sourceReference"], predecessor["candidateUnitId"], predecessor["atomicFocusSha256"]) != (child["sourceReference"], child["childCandidateUnitId"], child["childAtomicFocusSha256"]) or member["successorAuthorityBinding"] != leaf["contextSuccessorBinding"] or member["memberMatchSha256"] != digest({k: v for k, v in member.items() if k != "memberMatchSha256"}):
                    return True
                if proof == "EXACT_SUCCESSOR_CANDIDATE_MEMBER" and (member["successorMemberBinding"] is None or member["successorOperatorBinding"] is not None or binding_key(member["successorMemberBinding"]) not in exact):
                    return True
                if proof == "EXACT_PREDECESSOR_MEMBER_RETAINED_BY_SUCCESSOR_SET_REFERENCE" and (member["successorMemberBinding"] is not None or not member["successorOperatorBinding"] or member["successorOperatorBinding"]["operatorBindingSha256"] != digest({k: v for k, v in member["successorOperatorBinding"].items() if k != "operatorBindingSha256"})):
                    return True
                if proof not in {"EXACT_SUCCESSOR_CANDIDATE_MEMBER", "EXACT_PREDECESSOR_MEMBER_RETAINED_BY_SUCCESSOR_SET_REFERENCE"}:
                    return True
            elif disposition == "REMOVED_MEMBER_SUPERSEDED":
                if member is not None or independent is not None or successor is None or binding_key(successor) not in exact or leaf["matchBasisCode"] != "EXACT_HASH_BOUND_LEAF_REPLACEMENT" or child["effectiveAuthorityEffect"] != "SUPERSEDED_NORMATIVE":
                    return True
            elif disposition == "INDEPENDENT_CURRENT_AUTHORITY":
                if member is not None or successor is not None or independent is None or binding_key(independent) not in exact or independent["atomicFocusSha256"] != child["childAtomicFocusSha256"] or leaf["matchBasisCode"] != "EXACT_LATER_CURRENT_OWNER_AUTHORITY" or child["effectiveAuthorityEffect"] != "CURRENT_NORMATIVE":
                    return True
                proof = "EXACT_LATER_CURRENT_AUTHORITY"
            else:
                return True
            proofs[proof or "NONE"] += 1
            dispositions[disposition] += 1
            semantic.append({"parentRelationId": leaf["parentRelationId"], "childDecisionId": leaf["childDecisionId"], "childCandidateUnitId": child["childCandidateUnitId"], "childAtomicFocusSha256": child["childAtomicFocusSha256"], "disposition": disposition, "proofKind": proof, "independentAuthority": ({"candidateUnitId": independent["candidateUnitId"], "atomicFocusSha256": independent["atomicFocusSha256"]} if independent else None)})
        order = {r["reference"]: i for i, r in enumerate(records)}
        source_ordered_parents = sorted(parents, key=lambda x: (order[x["parentReference"]], x["parentSourceCoordinates"]["rawCodepointWindow"]["start"]))
        source_projection = [parent_projection(x) for x in source_ordered_parents]
        lex_projection = sorted(source_projection, key=lambda x: (x["reference"], x["candidateUnitId"], x["atomicFocusSha256"]))
        expected_reviewed = {r["relationId"] for r in rels if pb[r["parentId"]]["contextAuthorityEffect"] == "SUPERSEDED_CONTEXT"}
        counts = p["decisionCounts"] == {k: sum(c["inheritanceDisposition"] == k for c in children) for k in p["decisionCounts"]} and p["contextSuccessionKindCounts"] == dict(Counter(s["successionKind"] for s in succs)) and p["contextSuccessionLeafDispositionCounts"] == dict(dispositions) and p["contextSuccessionLeafProofKindCounts"] == {k: proofs[k] for k in p["contextSuccessionLeafProofKindCounts"]} and p["parentFocusPrivacyCounts"] == {"emitted": sum(x["parentNormalizedAtomicFocus"] is not None for x in parents), "withheld": sum(x["parentNormalizedAtomicFocus"] is None for x in parents)} and p["promotionSyntacticTypeCounts"] == {"PURE_DIGEST": sum(r["relationDecisionBasisCode"].endswith("DIGEST_MEMBER_CAUSALLY_PROMOTES_REFERENCE") for r in rels), "PURE_PATH": sum(r["relationDecisionBasisCode"].endswith("PATH_MEMBER_CAUSALLY_PROMOTES_REFERENCE") for r in rels)}
        digests = p["preservedReferenceChildCount"] == sum(c["originalSemanticClass"] == "REFERENCE" and c["effectiveSemanticClass"] == "REFERENCE" for c in children) and p["sourceOrderedParentIdentitySha256"] == digest(source_projection) and p["lexicographicParentIdentitySha256"] == digest(lex_projection) and p["orderedContextSuccessionLeafSemanticSha256"] == digest(semantic)
        return reviewed != expected_reviewed or not counts or not digests
    except (IndexError, KeyError, TypeError, ValueError, StopIteration):
        return True
def _external_governing_context_bindings_invalid(
    records: Any, partition: Any
) -> bool:
    """Reject self-consistent hashes that conceal crossed context bindings."""
    try:
        parents, relations = partition["parents"], partition["relations"]
        children = partition["childDecisions"]
        successions = partition["resolvedExactContextSuccessions"]
        leaf_reviews = partition["contextSuccessionLeafReviews"]
        components = (
            (parents, "parentId", "parentDecisionSha256"),
            (relations, "relationId", "relationDecisionSha256"),
            (children, "childDecisionId", "childDecisionSha256"),
            (successions, "contextSuccessionId", "contextSuccessionDecisionSha256"),
            (leaf_reviews, "contextSuccessionLeafReviewId", "reviewDecisionSha256"),
        )
        for values, id_field, hash_field in components:
            if len(values) != len({item[id_field] for item in values}) or any(
                item[hash_field]
                != _sha256(_canonical_json({k: v for k, v in item.items() if k != hash_field}).encode("utf-8"))
                for item in values
            ):
                return True
        array_contracts = (
            (parents, "parentCount", "orderedParentDecisionSha256"),
            (relations, "relationCount", "orderedRelationDecisionSha256"),
            (children, "uniqueChildCount", "orderedChildDecisionSha256"),
            (successions, "resolvedExactContextSuccessionCount", "orderedContextSuccessionDecisionSha256"),
            (leaf_reviews, "contextSuccessionLeafReviewCount", "orderedContextSuccessionLeafReviewSha256"),
        )
        if any(
            partition[count] != len(values)
            or partition[digest] != _sha256(_canonical_json(values).encode("utf-8"))
            for values, count, digest in array_contracts
        ) or partition["operatorCodeOrderSha256"] != _sha256(
            _canonical_json(partition["operatorCodeOrder"]).encode("utf-8")
        ):
            return True
        parent_by_id = {item["parentId"]: item for item in parents}
        child_by_id = {item["childDecisionId"]: item for item in children}
        relation_by_id = {item["relationId"]: item for item in relations}
        incoming: dict[str, list[str]] = {child_id: [] for child_id in child_by_id}
        relation_identities = []
        for relation in relations:
            parent, child = parent_by_id[relation["parentId"]], child_by_id[relation["childDecisionId"]]
            parent_identity = {key: relation[key] for key in ("parentReference", "parentCandidateUnitId", "parentAtomicFocusSha256")}
            relation_identity = parent_identity | {key: relation[key] for key in ("childCandidateUnitId", "childAtomicFocusSha256")}
            if (
                relation["relationId"] != "GCTX-R-" + _sha256(_canonical_json(relation_identity).encode("utf-8"))
                or any(parent[key] != value for key, value in parent_identity.items())
                or child["childCandidateUnitId"] != relation["childCandidateUnitId"]
                or child["childAtomicFocusSha256"] != relation["childAtomicFocusSha256"]
            ):
                return True
            incoming[relation["childDecisionId"]].append(relation["relationId"])
            relation_identities.append(relation_identity)
        if any(
            parent["parentId"] != "GCTX-P-" + _sha256(_canonical_json({"parentReference": parent["parentReference"], "parentCandidateUnitId": parent["parentCandidateUnitId"], "parentAtomicFocusSha256": parent["parentAtomicFocusSha256"]}).encode("utf-8"))
            for parent in parents
        ) or any(
            child["childDecisionId"] != "GCTX-C-" + _sha256(_canonical_json({"sourceReference": child["sourceReference"], "childCandidateUnitId": child["childCandidateUnitId"], "childAtomicFocusSha256": child["childAtomicFocusSha256"]}).encode("utf-8"))
            or child["orderedRelationIds"] != sorted(incoming[child["childDecisionId"]], key=lambda relation_id: (parent_by_id[relation_by_id[relation_id]["parentId"]]["governedBlockSourceSpan"]["startLine"], -parent_by_id[relation_by_id[relation_id]["parentId"]]["governedBlockSourceSpan"]["endLine"], parent_by_id[relation_by_id[relation_id]["parentId"]]["parentSourceCoordinates"]["rawCodepointWindow"]["start"], relation_by_id[relation_id]["parentId"]))
            for child in children
        ):
            return True
        relation_identities.sort(key=lambda item: tuple(item[key] for key in item))
        if partition["orderedRelationIdentitySha256"] != _sha256(
            _canonical_json(relation_identities).encode("utf-8")
        ) or any(
            review["childDecisionId"] not in child_by_id
            or review["parentRelationId"] not in relation_by_id
            or relation_by_id[review["parentRelationId"]]["childDecisionId"] != review["childDecisionId"]
            or review["contextSuccessionLeafReviewId"] != "GCTX-L-" + _sha256(_canonical_json({"parentRelationId": review["parentRelationId"], "childDecisionId": review["childDecisionId"]}).encode("utf-8"))
            for review in leaf_reviews
        ) or any(
            succession["contextSuccessionId"] != "GCTX-S-" + _sha256(_canonical_json({"ruleCode": succession["ruleCode"], "predecessorCandidateUnitId": succession["predecessor"]["candidateUnitId"], "successorCandidateUnitId": succession["successor"]["candidateUnitId"]}).encode("utf-8"))
            or succession["predecessor"] != {key: value for key, value in succession["relocatedFromClauseSuccession"]["predecessor"].items() if key != "clauseId"}
            or succession["successor"] != {key: value for key, value in succession["relocatedFromClauseSuccession"]["successor"].items() if key != "clauseId"}
            or any(succession[key] != succession["relocatedFromClauseSuccession"][key] for key in ("ruleCode", "semanticPrecedenceInputActivation", "semanticPrecedenceInputRole", "semanticPrecedenceInputSha256"))
            or succession["disposition"] != "RESOLVED_EXACT_CONTEXT_SUPERSESSION"
            or succession["relocatedFromClauseSuccession"]["disposition"] != "RESOLVED_EXACT_CLAUSE_SUPERSESSION"
            for succession in successions
        ):
            return True
        promoted = [item for item in children if item["effectiveSemanticClass"] == "NORMATIVE_REQUIREMENT" and item["originalSemanticClass"] != "NORMATIVE_REQUIREMENT"]
        promoted_identity = sorted(({"candidateUnitId": item["childCandidateUnitId"], "atomicFocusSha256": item["childAtomicFocusSha256"]} for item in promoted), key=lambda item: (item["candidateUnitId"], item["atomicFocusSha256"]))
        promotion_decisions = [{key: item[key] for key in ("parentReference", "parentCandidateUnitId", "parentAtomicFocusSha256", "childCandidateUnitId", "childAtomicFocusSha256", "relationDecisionBasisCode")} for item in relations if item["relationEffect"] == "GOVERNING_CONTEXT_PROMOTES_CHILD"]
        if (
            partition["promotionCount"] != len(promoted)
            or partition["orderedPromotedChildIdentitySha256"] != _sha256(_canonical_json(promoted_identity).encode("utf-8"))
            or partition["orderedPromotionDecisionSha256"] != _sha256(_canonical_json(promotion_decisions).encode("utf-8"))
        ):
            return True
        projections, references = [], []
        for child in children:
            for binding in child["projectedClauseBindings"]:
                projections.append((child["childDecisionId"], child["sourceReference"], binding["clauseId"], binding["atomicFocusSha256"], binding["normativeEffect"]))
        for record in records:
            for clause in record["clauses"]:
                reference = clause["governingContextDecisionRef"]
                if reference is None:
                    continue
                child = child_by_id[reference["childDecisionId"]]
                if reference["childDecisionSha256"] != child["childDecisionSha256"]:
                    return True
                references.append((child["childDecisionId"], record["reference"], clause["clauseId"], clause["atomicFocusSha256"], clause["normativeEffect"]))
        if len(projections) != len(set(projections)) or len(references) != len(set(references)) or set(projections) != set(references):
            return True
        return _external_context_semantics_invalid(records, partition) or partition["partitionSha256"] != _sha256(
            _canonical_json({key: value for key, value in partition.items() if key != "partitionSha256"}).encode("utf-8")
        )
    except (KeyError, TypeError, ValueError):
        return True
def _external_authority_failures(
    sources: Iterable[dict[str, Any]], manifest: Any
) -> list[str]:
    pending = _pending_external_authority_manifest(sources)
    if not isinstance(manifest, dict) or set(manifest) != _EXTERNAL_MANIFEST_FIELDS:
        return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_MANIFEST_INVALID"]
    if manifest.get("closure") == "PENDING":
        return (
            []
            if manifest == pending
            else ["MPV2.MAPPING.EXTERNAL_AUTHORITY_MANIFEST_INVALID"]
        )
    records = manifest.get("records")
    expected_references = [record["reference"] for record in pending["records"]]
    if (
        manifest.get("schemaVersion") != "ExternalAuthorityManifestV2"
        or manifest.get("repository")
        != {"id": GITHUB_REPOSITORY_ID, "fullName": GITHUB_REPOSITORY}
        or manifest.get("cutoff") != pending["cutoff"]
        or manifest.get("closure") != "CLASSIFIED_AND_ATOMIZED"
        or not isinstance(records, list)
        or [record.get("reference") for record in records if isinstance(record, dict)]
        != expected_references
        or manifest.get("referenceCount") != len(expected_references)
        or manifest.get("recordCount") != len(expected_references)
        or manifest.get("orderedReferenceCensusSha256")
        != pending["orderedReferenceCensusSha256"]
        or manifest.get("orderedRecordSha256")
        != _sha256(_canonical_json(records).encode("utf-8"))
        or not isinstance(manifest.get("retrievedAt"), str)
    ):
        return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_MANIFEST_INVALID"]
    try:
        retrieved_at = _parse_github_time(manifest["retrievedAt"])
        cutoff = datetime.fromisoformat(manifest["cutoff"])
    except (TypeError, ValueError):
        return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_MANIFEST_INVALID"]
    if retrieved_at <= cutoff:
        return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_MANIFEST_INVALID"]
    for record in records:
        if not isinstance(record, dict) or set(record) != _EXTERNAL_RECORD_FIELDS:
            return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_RECORD_INVALID"]
        reference = record["reference"]
        match = re.fullmatch(
            r"github-(comment|issue|pull-request):([1-9][0-9]*)", reference
        )
        expected_kind = {
            "comment": "EXTERNAL_GITHUB_COMMENT",
            "issue": "EXTERNAL_GITHUB_ISSUE_BODY",
            "pull-request": "EXTERNAL_GITHUB_PULL_REQUEST_BODY",
        }.get(match.group(1) if match else "")
        identity = record.get("recordIdentity")
        author = record.get("author")
        locator = record.get("sourceLocator")
        if (
            match is None
            or record.get("sourceKind") != expected_kind
            or not isinstance(identity, dict)
            or set(identity)
            != {"recordId", "nodeId", "issueNumber", "parentIssueId"}
            or not isinstance(identity.get("recordId"), int)
            or isinstance(identity.get("recordId"), bool)
            or identity["recordId"] < 1
            or (
                match.group(1) == "comment"
                and identity["recordId"] != int(match.group(2))
            )
            or not isinstance(identity.get("nodeId"), str)
            or not identity["nodeId"]
            or not isinstance(identity.get("issueNumber"), int)
            or isinstance(identity.get("issueNumber"), bool)
            or identity["issueNumber"] < 1
            or (
                match.group(1) != "comment"
                and identity["issueNumber"] != int(match.group(2))
            )
            or (
                match.group(1) == "comment"
                and (
                    not isinstance(identity.get("parentIssueId"), int)
                    or isinstance(identity.get("parentIssueId"), bool)
                    or identity["parentIssueId"] < 1
                )
            )
            or (
                match.group(1) != "comment"
                and identity.get("parentIssueId") is not None
            )
            or not isinstance(author, dict)
            or set(author) != {"userId", "login", "type", "association"}
            or not isinstance(author.get("userId"), int)
            or isinstance(author.get("userId"), bool)
            or author["userId"] < 1
            or not all(
                isinstance(author.get(key), str) and bool(author[key])
                for key in ("login", "type", "association")
            )
            or not isinstance(locator, dict)
            or set(locator) != {"apiUrl", "htmlUrl"}
            or not all(isinstance(locator.get(key), str) for key in locator)
            or not isinstance(record.get("byteCount"), int)
            or isinstance(record.get("byteCount"), bool)
            or record["byteCount"] < 0
            or not isinstance(record.get("contentSha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", record["contentSha256"]) is None
            or record.get("cutoffEligible") is not True
            or _external_classification_invalid(record)
            or record.get("contentAddressedRef")
            != f"{reference}@sha256:{record['contentSha256']}"
        ):
            return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_RECORD_INVALID"]
        try:
            created_at = _parse_github_time(record["createdAt"])
            updated_at = _parse_github_time(record["updatedAt"])
        except (TypeError, ValueError):
            return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_RECORD_INVALID"]
        if created_at > updated_at or updated_at > cutoff:
            return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_CUTOFF_INVALID"]
        api_suffix = (
            f"issues/comments/{identity['recordId']}"
            if match.group(1) == "comment"
            else f"pulls/{identity['issueNumber']}"
            if match.group(1) == "pull-request"
            else f"issues/{identity['issueNumber']}"
        )
        html = (
            f"https://github.com/{GITHUB_REPOSITORY}/"
            f"{'pull' if identity['issueNumber'] in _REFERENCED_PULL_REQUEST_NUMBERS else 'issues'}/"
            f"{identity['issueNumber']}#issuecomment-{identity['recordId']}"
            if match.group(1) == "comment"
            else f"https://github.com/{GITHUB_REPOSITORY}/"
            f"{'pull' if match.group(1) == 'pull-request' or identity['nodeId'].startswith('PR_') else 'issues'}/"
            f"{identity['issueNumber']}"
        )
        if locator != {
            "apiUrl": f"https://api.github.com/repos/{GITHUB_REPOSITORY}/{api_suffix}",
            "htmlUrl": html,
        }:
            return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_RECORD_INVALID"]
    if _external_governing_context_bindings_invalid(
        records, manifest.get("governingContextDecisionPartition")
    ):
        return ["MPV2.MAPPING.EXTERNAL_GOVERNING_CONTEXT_INVALID"]
    if _sha256(_canonical_json(manifest).encode("utf-8")) != (
        EXTERNAL_AUTHORITY_MANIFEST_SHA256
    ):
        return ["MPV2.MAPPING.EXTERNAL_AUTHORITY_HASH_DRIFT"]
    return []
def _mapping_failures(root: Path, mapping: Any, document: str) -> list[str]:
    expected_metadata = {
        "schemaVersion": "SupersetMappingV2",
        "mappingId": "narratwin-master-program-v2-superset",
        "proposalState": "PROPOSED",
        "cutoff": "2026-09-06T23:59:59+05:30",
        "ownerAuthority": _owner_plan_adoption_ref(document.encode("utf-8")),
    }
    if (
        not isinstance(mapping, dict)
        or set(mapping) != _MAPPING_FIELDS
        or any(mapping.get(key) != value for key, value in expected_metadata.items())
    ):
        return ["MPV2.MAPPING.SCHEMA_INVALID"]
    failures: list[str] = []
    sources = mapping.get("sources")
    rows = mapping.get("rows")
    if not isinstance(sources, list) or not isinstance(rows, list):
        return ["MPV2.MAPPING.SCHEMA_INVALID"]
    try:
        expected_sources = expected_source_records(root)
    except (AttributeError, KeyError, OSError, TypeError, UnicodeError, SyntaxError, ValueError):
        return ["MPV2.MAPPING.SOURCE_INVENTORY_FAILED"]
    source_by_id: dict[str, dict[str, Any]] = {}
    source_ids = [source.get("sourceId") for source in sources if isinstance(source, dict)]
    if (
        len(source_ids) != len(sources)
        or not all(isinstance(source_id, str) for source_id in source_ids)
        or source_ids != list(expected_sources)
        or len(source_ids) != len(set(cast(list[str], source_ids)))
    ):
        failures.append("MPV2.MAPPING.SOURCE_INVENTORY_INVALID")
    for source in sources:
        if (
            not isinstance(source, dict)
            or set(source) != _SOURCE_FIELDS
            or not isinstance(source.get("sourceId"), str)
        ):
            failures.append("MPV2.MAPPING.SOURCE_INVALID")
            continue
        source_by_id[source["sourceId"]] = source
        expected_source = expected_sources.get(source["sourceId"])
        if expected_source is None or source != expected_source:
            failures.append("MPV2.MAPPING.SOURCE_BINDING_INVALID")
        try:
            data = frozen_source_bytes(root, source)
        except (KeyError, OSError, TypeError, ValueError):
            failures.append("MPV2.SOURCE.MISSING")
            continue
        if _sha256(data) != source.get("contentSha256") or (
            source.get("objectKind") == "GIT_BLOB"
            and _git_blob(data) != source.get("sourceGitBlob")
        ):
            failures.append("MPV2.SOURCE.HASH_MISMATCH")
    external_manifest = mapping.get("externalAuthorityManifest")
    failures.extend(
        _external_authority_failures(
            expected_sources.values(), external_manifest
        )
    )
    try:
        expected = expected_normative_atoms(root)
        if isinstance(external_manifest, dict):
            expected.update(_external_new_atoms(external_manifest))
    except (AttributeError, KeyError, OSError, TypeError, UnicodeError, SyntaxError, ValueError):
        expected = {}
        failures.append("MPV2.MAPPING.ATOMIZATION_FAILED")
    generated_mapping: dict[str, Any] = {}
    try:
        if not isinstance(external_manifest, dict):
            raise ValueError("external authority manifest invalid")
        generated_mapping = generate_mapping(
            root, external_manifest=external_manifest, copy_result=False
        )
        generated_rows = {
            row["sourceAtomId"]: row for row in generated_mapping["rows"]
        }
        generated_ids = [row["sourceAtomId"] for row in generated_mapping["rows"]]
        for record in external_manifest.get("records", []):
            for clause in record.get("clauses", []):
                alias = clause.get("suggestedAlias")
                if not isinstance(alias, dict) or alias.get("kind") != "EXISTING_REQUIREMENT":
                    continue
                target = generated_rows.get(alias.get("sourceAtomId"))
                candidates = [
                    row for row in generated_mapping["rows"]
                    if not row["sourceKind"].startswith("EXTERNAL_")
                    and row["atomicFocusSha256"] == clause["atomicFocusSha256"]
                    and row["normalizedSourceContextSha256"]
                    == clause["normalizedSourceContextSha256"]
                ]
                if (
                    not isinstance(target, dict)
                    or candidates != [target]
                    or target.get("requirementId") != alias.get("requirementId")
                    or target.get("sourceId") != alias.get("sourceId")
                    or target.get("v2DestinationClause")
                    != alias.get("v2DestinationClause")
                    or record.get("contentAddressedRef")
                    not in target.get("sourceAuthorityRefs", [])
                ):
                    failures.append("MPV2.MAPPING.EXTERNAL_ALIAS_INVALID")
    except (AttributeError, KeyError, OSError, TypeError, UnicodeError, SyntaxError, ValueError):
        generated_rows = {}
        generated_ids = []
        failures.append("MPV2.MAPPING.SEMANTIC_GENERATION_FAILED")
    failures.extend(_destination_registry_failures(document))
    actual_ids: list[str] = []
    requirement_ids: list[str] = []
    row_by_requirement = {
        row.get("requirementId"): row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("requirementId"), str)
    }
    for row in rows:
        if not isinstance(row, dict):
            failures.append("MPV2.MAPPING.ROW_SCHEMA_INVALID")
            continue
        strings = _ROW_FIELDS - {
            "normalizedAtomicRequirement", "normalizedSourceContext", "replacementId",
            "ownerAuthorityRef", "reviewTime", "sourceAuthorityRefs",
            "thresholdComparison", "sourceCommit", "atomicFocusStart",
            "atomicFocusEnd", "atomicFocusOccurrence", "governingContext",
            "sourceSpan", "sourceGitBlob",
        }
        source_commit_valid = (
            row.get("sourceKind") == "REPOSITORY_FILE"
            and isinstance(row.get("sourceCommit"), str)
            and bool(re.fullmatch(r"[0-9a-f]{40}", row["sourceCommit"]))
        ) or (
            row.get("sourceKind")
            in {
                "OWNER_PLAN_CANDIDATE", "OWNER_ADOPTED_PLAN",
                "EXTERNAL_GITHUB_COMMENT", "EXTERNAL_GITHUB_ISSUE_BODY",
            }
            and row.get("sourceCommit") is None
        )
        source_blob_valid = (
            row.get("sourceKind") in {
                "REPOSITORY_FILE", "OWNER_PLAN_CANDIDATE", "OWNER_ADOPTED_PLAN",
            }
            and isinstance(row.get("sourceGitBlob"), str)
            and bool(re.fullmatch(r"[0-9a-f]{40}", row["sourceGitBlob"]))
        ) or (
            row.get("sourceKind") in {
                "EXTERNAL_GITHUB_COMMENT", "EXTERNAL_GITHUB_ISSUE_BODY",
            }
            and row.get("sourceGitBlob") is None
        )
        if (
            set(row) != _ROW_FIELDS
            or not all(isinstance(row.get(field), str) for field in strings)
            or not isinstance(row.get("sourceAuthorityRefs"), list)
            or not all(
                isinstance(reference, str)
                for reference in row.get("sourceAuthorityRefs", [])
            )
            or not isinstance(row.get("thresholdComparison"), dict)
            or set(row.get("thresholdComparison", {})) != {"relation", "basis"}
            or not all(
                isinstance(row["thresholdComparison"].get(field), str)
                for field in ("relation", "basis")
            )
            or not isinstance(row.get("replacementId"), (str, type(None)))
            or not isinstance(row.get("ownerAuthorityRef"), (str, type(None)))
            or not all(
                isinstance(row.get(field), int)
                and not isinstance(row.get(field), bool)
                for field in (
                    "atomicFocusStart",
                    "atomicFocusEnd",
                    "atomicFocusOccurrence",
                )
            )
            or not isinstance(row.get("governingContext"), dict)
            or set(row.get("governingContext", {})) != {
                "kind",
                "normalization",
                "coordinateSystem",
                "semanticBinding",
                "start",
                "end",
            }
            or not isinstance(row.get("sourceSpan"), dict)
            or set(row.get("sourceSpan", {})) != {
                "coordinateSystem",
                "startLine",
                "endLine",
                "rawSha256",
            }
            or row.get("sourceSpan", {}).get("coordinateSystem") not in {
                "ONE_BASED_INCLUSIVE_LINES",
                "ORIGINAL_BODY_LINES_ONE_BASED_INCLUSIVE",
            }
            or not all(
                isinstance(row.get("sourceSpan", {}).get(field), int)
                and not isinstance(row.get("sourceSpan", {}).get(field), bool)
                and row["sourceSpan"][field] >= 1
                for field in ("startLine", "endLine")
            )
            or row.get("sourceSpan", {}).get("endLine", 0)
            < row.get("sourceSpan", {}).get("startLine", 1)
            or not isinstance(row.get("sourceSpan", {}).get("rawSha256"), str)
            or not bool(
                re.fullmatch(
                    r"[0-9a-f]{64}", row.get("sourceSpan", {}).get("rawSha256", "")
                )
            )
            or row.get("reviewTime") is not None
            or not source_commit_valid
            or not source_blob_valid
        ):
            failures.append("MPV2.MAPPING.ROW_SCHEMA_INVALID")
            continue
        try:
            normalized_requirement = decode_requirement(
                row["normalizedAtomicRequirement"]
            )
            normalized_source_context = decode_requirement(
                row["normalizedSourceContext"]
            )
        except (TypeError, ValueError):
            failures.append("MPV2.MAPPING.ROW_SCHEMA_INVALID")
            continue
        atom_id = row["sourceAtomId"]
        actual_ids.append(atom_id)
        requirement_ids.append(row["requirementId"])
        if row["v2DestinationClause"] not in DESTINATION_CLAUSES:
            failures.append("MPV2.MAPPING.DESTINATION_MISSING")
        atom = expected.get(atom_id)
        if atom is None:
            continue
        source = expected_sources.get(row["sourceId"], {})
        generated = generated_rows.get(atom_id)
        exact_source = row == generated if row["sourceKind"].startswith("EXTERNAL_") else (
            row["sourcePath"] == source.get("repositoryPath")
            and row["sourceKind"] == source.get("sourceKind")
            and row["sourceCommit"] == source.get("sourceCommit")
            and row["sourceGitBlob"] == source.get("sourceGitBlob")
            and row["sourceContentSha256"] == source.get("contentSha256")
            and row["sourceAnchor"] == atom.anchor
            and row["atomicFocusSha256"] == atom.clause_sha256
            and normalized_requirement == atom.text
            and row["normalizedSourceContextSha256"]
            == atom.source_context_sha256
            and normalized_source_context == atom.source_clause
            and row["sourceSpan"]
            == {
                "coordinateSystem": "ONE_BASED_INCLUSIVE_LINES",
                "startLine": atom.source_span_start_line,
                "endLine": atom.source_span_end_line,
                "rawSha256": atom.raw_source_span_sha256,
            }
            and row["atomicFocusStart"] == atom.focus_start
            and row["atomicFocusEnd"] == atom.resolved_focus_end
            and row["atomicFocusOccurrence"] == atom.focus_occurrence
            and row["governingContext"] == _governing_context(atom)
            and normalized_source_context[
                row["atomicFocusStart"] : row["atomicFocusEnd"]
            ]
            == normalized_requirement
            and normalized_source_context[: row["atomicFocusStart"]].count(
                normalized_requirement
            )
            + 1
            == row["atomicFocusOccurrence"]
        )
        if not exact_source:
            failures.append("MPV2.MAPPING.SOURCE_BINDING_INVALID")
        expected_destination = (
            generated["v2DestinationClause"]
            if row["sourceKind"].startswith("EXTERNAL_")
            and isinstance(generated, dict)
            else _destination(
                atom, source.get("defaultV2Destination", "MPV2-SECTION-1")
            )
        )
        if row["v2DestinationClause"] != expected_destination:
            failures.append("MPV2.MAPPING.DESTINATION_INVALID")
        if row["disposition"] not in _DISPOSITIONS:
            failures.append("MPV2.MAPPING.DISPOSITION_INVALID")
        semantic_class = row.get("semanticClass")
        if semantic_class != "NORMATIVE_REQUIREMENT" or row.get(
            "normativeEffect"
        ) not in {"CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE"}:
            failures.append("MPV2.MAPPING.NON_NORMATIVE_ROW")
        comparison = row["thresholdComparison"]
        expected_relation = (
            "OWNER_AUTHORIZED_CHANGE"
            if row["disposition"] == "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"
            else "EQUAL_OR_STRONGER"
        )
        if (
            not isinstance(comparison, dict)
            or set(comparison) != {"relation", "basis"}
            or comparison.get("relation") != expected_relation
            or comparison.get("basis") != expected_comparison_basis(row)
        ):
            failures.append("MPV2.MAPPING.THRESHOLD_WEAKENED")
        changed = row["disposition"] in {
            "RELOCATED", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY", "STRENGTHENED"
        }
        replacement = row_by_requirement.get(row["replacementId"])
        if changed and not row["replacementId"]:
            failures.append("MPV2.MAPPING.REPLACEMENT_REQUIRED")
        elif changed and (
            not isinstance(replacement, dict)
            or replacement.get("sourceId") != "OWNER_PLAN_2026_09_07"
        ):
            failures.append("MPV2.MAPPING.REPLACEMENT_UNRESOLVED")
        expected_authority = (
            _owner_authority_ref(
                row["replacementId"], mapping["ownerAuthority"]
            )
            if changed and isinstance(replacement, dict)
            else None
        )
        if changed and not row["ownerAuthorityRef"]:
            failures.append("MPV2.MAPPING.OWNER_AUTHORITY_REQUIRED")
        elif changed and row["ownerAuthorityRef"] != expected_authority:
            failures.append("MPV2.MAPPING.OWNER_AUTHORITY_UNRESOLVED")
        if not changed and (row["replacementId"] is not None or row["ownerAuthorityRef"] is not None):
            failures.append("MPV2.MAPPING.UNAUTHORIZED_REPLACEMENT")
        if row["rationale"] != _expected_rationale(row):
            failures.append("MPV2.MAPPING.RATIONALE_INVALID")
        if (
            row["reviewer"] != "INDEPENDENT_REVIEWER_PENDING"
            or row["reviewTime"] is not None
            or row["result"] != "PENDING"
        ):
            failures.append("MPV2.MAPPING.REVIEW_RESULT_INVALID")
        if generated is not None and row != generated:
            failures.append("MPV2.MAPPING.SEMANTIC_ROW_INVALID")
    if len(actual_ids) != len(set(actual_ids)):
        failures.append("MPV2.MAPPING.SOURCE_ATOM_DUPLICATE")
    if len(requirement_ids) != len(set(requirement_ids)):
        failures.append("MPV2.MAPPING.REQUIREMENT_ID_DUPLICATE")
    missing = set(expected) - set(actual_ids)
    extra = set(actual_ids) - set(expected)
    if missing:
        failures.append("MPV2.MAPPING.SOURCE_ATOM_MISSING")
    if extra:
        failures.append("MPV2.MAPPING.SOURCE_ATOM_UNKNOWN")
    if generated_ids and actual_ids != generated_ids:
        failures.append("MPV2.MAPPING.SOURCE_ORDER_INVALID")
    for source in expected_sources.values():
        count = sum(row.get("sourceId") == source.get("sourceId") for row in rows if isinstance(row, dict))
        if count != source.get("semanticCoverage", {}).get(
            "normativeRequirementCount"
        ):
            failures.append("MPV2.MAPPING.SOURCE_COUNT_MISMATCH")
    if (
        not isinstance(mapping.get("semanticDuplicateCensus"), dict)
        or mapping.get("semanticDuplicateCensus")
        != generated_mapping.get("semanticDuplicateCensus")
    ):
        failures.append("MPV2.MAPPING.DUPLICATE_CENSUS_INVALID")
    certification = mapping.get("certification")
    expected_certification = {
        "structuralResult": "PASS",
        "semanticReview": "PENDING_INDEPENDENT_REVIEW",
        "ownerExactBytesApproval": "PENDING",
        "eligibleNonAuthorExactHead": "PENDING",
        "activation": "NONE",
    }
    if certification != expected_certification:
        failures.append("MPV2.MAPPING.CERTIFICATION_STATE_INVALID")
    return failures
def public_sanitization_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_ARTIFACTS:
        path = root / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            failures.append(f"MPV2.PUBLIC.UTF8_INVALID:{relative}")
            continue
        if any(pattern.search(text) for pattern in _PRIVATE_PATTERNS):
            failures.append(f"MPV2.PUBLIC.PRIVATE_DATA:{relative}")
    return failures
def _binding_failures(
    binding: Any,
    artifact_bytes: dict[str, bytes],
    document_bytes: bytes,
    mapping_bytes: bytes,
    taxonomy_bytes: bytes,
    mapping_schema_bytes: bytes,
    taxonomy_schema_bytes: bytes,
) -> list[str]:
    if not isinstance(binding, dict):
        return ["MPV2.BINDING.SCHEMA_INVALID"]
    failures: list[str] = []
    top_level = {
        "schemaVersion", "controllerId", "controllerIssue", "bootstrapBranch",
        "acceptedBaseSha", "researchCutoff", "documentPath", "mappingPath",
        "taxonomyPath", "mappingSchemaPath", "taxonomySchemaPath",
        "artifactHashes", "artifactShape", "proposalState",
        "implementationAuthority", "activeProgramRoute", "supersedesV1",
        "predecessor", "requiredReviews", "requiredApprovals",
        "activationTransition", "prohibitedClaims",
    }
    if set(binding) != top_level:
        failures.append("MPV2.BINDING.SCHEMA_INVALID")
    expected = {
        "schemaVersion": "MasterProgramProposalBindingV2",
        "controllerId": "narratwin-master-program-v2",
        "controllerIssue": 521,
        "bootstrapBranch": "phase-1-closure-process-521-master-program-v2",
        "acceptedBaseSha": BASE_SHA,
        "researchCutoff": "2026-09-06T23:59:59+05:30",
        "documentPath": DOCUMENT_PATH,
        "mappingPath": MAPPING_PATH,
        "taxonomyPath": TAXONOMY_PATH,
        "mappingSchemaPath": MAPPING_SCHEMA_PATH,
        "taxonomySchemaPath": TAXONOMY_SCHEMA_PATH,
        "proposalState": "PROPOSED",
        "implementationAuthority": "NONE",
        "activeProgramRoute": None,
        "supersedesV1": False,
    }
    for key, value in expected.items():
        if binding.get(key) != value:
            failures.append("MPV2.BINDING.AUTHORITY_INVALID")
    actual_review_hashes = {path: _sha256(artifact_bytes[path]) for path in REVIEW_PATHS}
    hashes = binding.get("artifactHashes")
    expected_hashes = {
        "documentSha256": _sha256(document_bytes),
        "mappingSha256": _sha256(mapping_bytes),
        "taxonomySha256": _sha256(taxonomy_bytes),
        "mappingSchemaSha256": _sha256(mapping_schema_bytes),
        "taxonomySchemaSha256": _sha256(taxonomy_schema_bytes),
        "reviewSurfaceSha256": actual_review_hashes,
    }
    if hashes != expected_hashes:
        if not isinstance(hashes, dict) or hashes.get("documentSha256") != expected_hashes["documentSha256"]:
            failures.append("MPV2.BINDING.DOCUMENT_HASH_MISMATCH")
        if not isinstance(hashes, dict) or hashes.get("mappingSha256") != expected_hashes["mappingSha256"]:
            failures.append("MPV2.BINDING.MAPPING_HASH_MISMATCH")
        if not isinstance(hashes, dict) or hashes.get("taxonomySha256") != expected_hashes["taxonomySha256"]:
            failures.append("MPV2.BINDING.TAXONOMY_HASH_MISMATCH")
        if not isinstance(hashes, dict) or hashes.get("mappingSchemaSha256") != expected_hashes["mappingSchemaSha256"]:
            failures.append("MPV2.BINDING.MAPPING_SCHEMA_HASH_MISMATCH")
        if not isinstance(hashes, dict) or hashes.get("taxonomySchemaSha256") != expected_hashes["taxonomySchemaSha256"]:
            failures.append("MPV2.BINDING.TAXONOMY_SCHEMA_HASH_MISMATCH")
        if not isinstance(hashes, dict) or hashes.get("reviewSurfaceSha256") != actual_review_hashes:
            failures.append("MPV2.REVIEW.HASH_MISMATCH")
    if actual_review_hashes != REVIEW_SHA256:
        failures.append("MPV2.REVIEW.HASH_MISMATCH")
    try:
        parsed_mapping = json.loads(mapping_bytes)
    except (UnicodeError, json.JSONDecodeError):
        parsed_mapping = {}
    mapping = parsed_mapping if isinstance(parsed_mapping, dict) else {}
    mapping_sources = mapping.get("sources")
    mapping_rows = mapping.get("rows")
    expected_shape = {
        "documentBytes": len(document_bytes),
        "documentLines": len(document_bytes.splitlines()),
        "mappingBytes": len(mapping_bytes),
        "mappingLines": len(mapping_bytes.splitlines()),
        "mappingSources": len(mapping_sources) if isinstance(mapping_sources, list) else -1,
        "mappingRows": len(mapping_rows) if isinstance(mapping_rows, list) else -1,
        "taxonomyBytes": len(taxonomy_bytes),
        "taxonomyLines": len(taxonomy_bytes.splitlines()),
        "mappingSchemaBytes": len(mapping_schema_bytes),
        "mappingSchemaLines": len(mapping_schema_bytes.splitlines()),
        "taxonomySchemaBytes": len(taxonomy_schema_bytes),
        "taxonomySchemaLines": len(taxonomy_schema_bytes.splitlines()),
        "hasTrailingNewlines": all(
            value.endswith(b"\n")
            for value in (
                document_bytes,
                mapping_bytes,
                taxonomy_bytes,
                mapping_schema_bytes,
                taxonomy_schema_bytes,
            )
        ),
    }
    if binding.get("artifactShape") != expected_shape:
        failures.append("MPV2.BINDING.ARTIFACT_SHAPE_INVALID")
    predecessor = binding.get("predecessor")
    expected_predecessor = {
        "v1Path": V1_PATH,
        "v1GitBlob": "2216951d9716b7c946098ab454265eafa25975bd",
        "v1DocumentSha256": V1_SHA256,
        "fiveCutRoadmapSha256": ROADMAP_SHA256,
        "adr0079Sha256": ADR0079_SHA256,
        "v1RemainsEffective": True,
    }
    if predecessor != expected_predecessor:
        failures.append("MPV2.BINDING.PREDECESSOR_INVALID")
    expected_reviews = [
        {"id": "superset-semantic", "artifact": REVIEW_PATHS[0], "state": "PENDING_INDEPENDENT_REVIEW"},
        {"id": "false-success-security", "artifact": REVIEW_PATHS[1], "state": "PENDING_INDEPENDENT_REVIEW"},
    ]
    if binding.get("requiredReviews") != expected_reviews:
        failures.append("MPV2.BINDING.REVIEWS_INVALID")
    approvals = binding.get("requiredApprovals")
    if approvals != {"ownerExactBytes": "PENDING", "eligibleNonAuthorExactHead": "PENDING", "referenceOnlyMergeWording": "PENDING"}:
        failures.append("MPV2.BINDING.APPROVAL_STATE_INVALID")
    required_evidence = [
        "v2DocumentSha256", "supersetMappingSha256", "cutTaxonomySha256",
        "externalAuthorityCoverageDisposition", "independentReviewDispositions",
        "ownerExactBytesApproval",
        "eligibleNonAuthorExactHeadApproval", "mergeSha", "mergedMainChecks",
        "cutTaxonomyEffectiveAt", "compatibilityMigrationId",
        "compatibilityMigrationSurfaceEvidence", "requiredReadingHashTransition",
        "statusReconciliation", "issueDisposition", "v1SupersessionLink",
    ]
    expected_transition = {
        "createdBy": "separately-governed accepted-current transition after protected merge",
        "requiredEvidence": required_evidence,
        "proposalMayActivate": False,
    }
    if binding.get("activationTransition") != expected_transition:
        failures.append("MPV2.BINDING.ACTIVATION_PATH_INVALID")
    prohibited = [
        "V2 supersedes V1", "IMPLEMENTATION_ELIGIBLE", "CUT1_REAL_MEDIA_ACCEPTED",
        "Digital Twin activated", "commercial readiness", "public availability",
        "production readiness", "release",
    ]
    if binding.get("prohibitedClaims") != prohibited:
        failures.append("MPV2.BINDING.PROHIBITED_CLAIMS_INVALID")
    return failures
def validate_repository(
    root: Path,
    *,
    certification: bool,
) -> list[str]:
    failures: list[str] = []
    missing = [relative for relative in REQUIRED_ARTIFACTS if not (root / relative).is_file()]
    if missing:
        return [f"MPV2.ARTIFACT.MISSING:{relative}" for relative in missing]
    artifact_bytes: dict[str, bytes] = {}
    for relative in REQUIRED_ARTIFACTS:
        try:
            artifact_bytes[relative] = (root / relative).read_bytes()
        except OSError:
            return [f"MPV2.ARTIFACT.UNREADABLE:{relative}"]
    try:
        mapping_artifact = _load_json_text(artifact_bytes[MAPPING_PATH].decode())
        taxonomy = _load_json_text(artifact_bytes[TAXONOMY_PATH].decode())
        mapping_schema = _load_json_text(artifact_bytes[MAPPING_SCHEMA_PATH].decode())
        taxonomy_schema = _load_json_text(artifact_bytes[TAXONOMY_SCHEMA_PATH].decode())
        binding = _load_json_text(artifact_bytes[BINDING_PATH].decode())
    except DuplicateJsonMember:
        return ["MPV2.JSON.DUPLICATE_MEMBER"]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return ["MPV2.JSON.INVALID"]
    try:
        mapping = decode_mapping_artifact(mapping_artifact)
    except (KeyError, TypeError, ValueError):
        mapping = {}
        failures.append("MPV2.MAPPING.ENCODING_INVALID")
    document_bytes, mapping_bytes = artifact_bytes[DOCUMENT_PATH], artifact_bytes[MAPPING_PATH]
    taxonomy_bytes = artifact_bytes[TAXONOMY_PATH]
    mapping_schema_bytes = artifact_bytes[MAPPING_SCHEMA_PATH]
    taxonomy_schema_bytes = artifact_bytes[TAXONOMY_SCHEMA_PATH]
    if _sha256(document_bytes) != DOCUMENT_SHA256:
        failures.append("MPV2.SOURCE.DOCUMENT_HASH_DRIFT")
    if _sha256(mapping_bytes) != MAPPING_SHA256:
        failures.append("MPV2.SOURCE.MAPPING_HASH_DRIFT")
    if len(mapping_bytes) >= MAPPING_MAX_BYTES:
        failures.append("MPV2.MAPPING.HOSTED_FILE_SIZE_EXCEEDED")
    if _sha256(taxonomy_bytes) != TAXONOMY_SHA256:
        failures.append("MPV2.SOURCE.TAXONOMY_HASH_DRIFT")
    if _sha256(mapping_schema_bytes) != MAPPING_SCHEMA_SHA256:
        failures.append("MPV2.SOURCE.MAPPING_SCHEMA_HASH_DRIFT")
    if _sha256(taxonomy_schema_bytes) != TAXONOMY_SCHEMA_SHA256:
        failures.append("MPV2.SOURCE.TAXONOMY_SCHEMA_HASH_DRIFT")
    try:
        document = document_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return ["MPV2.DOCUMENT.UTF8_INVALID"]
    failures.extend(_mapping_failures(root, mapping, document))
    failures.extend(
        _schema_instance_failures(
            mapping_artifact,
            mapping_schema,
            definition="SupersetMappingV2Root",
            failure_code="MPV2.MAPPING.SCHEMA_INSTANCE_INVALID",
        )
    )
    try:
        rendered_mapping = render_mapping(mapping).encode("utf-8")
    except (KeyError, TypeError, ValueError):
        rendered_mapping = b""
    if rendered_mapping != mapping_bytes:
        failures.append("MPV2.MAPPING.RENDERING_INVALID")
    failures.extend(_taxonomy_failures(taxonomy))
    failures.extend(
        _schema_instance_failures(
            taxonomy,
            taxonomy_schema,
            definition="CutTaxonomyV2Root",
            failure_code="MPV2.TAXONOMY.SCHEMA_INSTANCE_INVALID",
        )
    )
    failures.extend(
        _binding_failures(
            binding,
            artifact_bytes,
            document_bytes,
            mapping_bytes,
            taxonomy_bytes,
            mapping_schema_bytes,
            taxonomy_schema_bytes,
        )
    )
    failures.extend(public_sanitization_failures(root))
    try:
        v1_bytes = (root / V1_PATH).read_bytes()
    except OSError:
        v1_bytes = b""
    if _sha256(v1_bytes) != V1_SHA256:
        failures.append("MPV2.SOURCE.V1_MUTATED")
    if certification:
        failures.extend(
            [
                "MPV2.CERTIFICATION.OWNER_PLAN_ADOPTION_PENDING",
                "MPV2.CERTIFICATION.INDEPENDENT_REVIEW_PENDING",
                "MPV2.CERTIFICATION.DUPLICATE_RESOLUTION_PENDING",
                "MPV2.CERTIFICATION.ELIGIBLE_NON_AUTHOR_PENDING",
                "MPV2.CERTIFICATION.OWNER_EXACT_BYTES_PENDING",
                "MPV2.CERTIFICATION.ACTIVATION_PENDING",
            ]
        )
    return list(dict.fromkeys(failures))
def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--emit-mapping", action="store_true")
    parser.add_argument("--certification", action="store_true")
    args = parser.parse_args(argv)
    if args.emit_mapping:
        if args.certification:
            parser.error("--emit-mapping cannot certify")
        sys.stdout.write(render_mapping(generate_mapping(args.root)))
        return 0
    failures = validate_repository(args.root, certification=args.certification)
    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print("PASS Master Program V2 candidate structure")
    return 0
if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
