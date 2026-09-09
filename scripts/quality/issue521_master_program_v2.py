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
REVIEW_PATHS = ("docs/reviews/ISSUE_521_SUPERSET_SEMANTIC_REVIEW.md", "docs/reviews/ISSUE_521_FALSE_SUCCESS_SECURITY_REVIEW.md")
REQUIRED_ARTIFACTS = (DOCUMENT_PATH, BINDING_PATH, MAPPING_PATH, TAXONOMY_PATH, MAPPING_SCHEMA_PATH, TAXONOMY_SCHEMA_PATH, *REVIEW_PATHS)
BASE_SHA = "b6b0c05c7227428ff0841361f3970b0b2c40aa86"
V1_PATH = "docs/governance/NARRATWIN_MASTER_PROGRAM_V1.md"
V1_SHA256 = "c3e3c85bb980aab4f818e80be3db5484e564423d77bc3ab6e81ba736c3af3420"
DOCUMENT_SHA256 = "31d879568cd4bbeea9e238d14e20bf66de565842204372ee54ccf071564396f1"
EXTERNAL_CLASSIFICATION_PRECEDENCE_INPUT_SHA256 = "746e23fcd200f25e1fcd91ef4dd39b59abc6e34ea00b28db7dee667da81db75f"
MAPPING_SHA256 = "f4e8dff41ce5532860189904bb10a78f2c85e9f70082f321de88740954745bc6"
TAXONOMY_SHA256 = "c0fba5183c284f2d8854eefb30caaf76bb2979ac00328b67ccd6d027a971cdb7"
MAPPING_SCHEMA_SHA256 = "27372ca1657e1fd7d4ac336dd5cad5e9aff4efbb2792b00faf8bea4d10138763"
TAXONOMY_SCHEMA_SHA256 = "7ac62fbe1a92b43eccba782038f8002818b80c9c02246f35d3f117941e69ccc8"
REVIEW_SHA256 = {REVIEW_PATHS[0]: "636c088e03ef99bfb5ad83b5854385810a9c03f4d6f7d0d024fcd05ba9c843b1", REVIEW_PATHS[1]: "48759b965cf7f2ccbd1e5c4c0e1c1880e156aecf1988a631865d43379f469672"}
EXTERNAL_AUTHORITY_MANIFEST_SHA256 = "87e4198c4344b35a89ad74efa768e7fe27ba6d3668b8fb76bd86a15b956f53ec"
LEGACY_EXTERNAL_AUTHORITY_MANIFEST_SHA256 = "b47e111cf0af5b6fb1b09b2659d89798e4f97a241612ea1eb5da4f664f8bc7a2"
LEGACY_EXTERNAL_AUTHORITY_SOURCE_COMMIT = "6e9623b04f1d5c0b5a12aa79b7eb6fe84437e861"
LEGACY_EXTERNAL_AUTHORITY_SOURCE_MAPPING_SHA256 = "766cbfcf6666e52cc2f158796577f797b771015716a07b4665efad7e721c2bcb"
_EXTERNAL_PULL_REQUEST_IDENTITY_CORRECTIONS = {152: (4_882_032_247, 4_051_522_269), 165: (4_886_863_961, 4_055_669_990), 180: (4_906_025_761, 4_072_009_918), 240: (4_941_712_853, 4_102_001_384), 271: (4_956_475_658, 4_114_525_426), 272: (4_956_925_298, 4_114_905_603), 417: (5_120_627_051, 4_253_563_363), 418: (5_121_963_693, 4_254_700_175), 419: (5_121_988_446, 4_254_721_403), 474: (5_293_726_604, 4_397_064_810)}
REPOSITORY_SEMANTIC_PARTITION_SHA256 = "1a7650934378462a520ed1ddd0f57f6339254de0ea0304478c4752e42b2384fe"
REPOSITORY_CONTEXT_PARTITION_SHA256 = "9939476b97f156ccdbc9585b7ee24b0dbfee43fe11561ee0fe365ff63982fcac"
EXTERNAL_IDENTITY_EQUIVALENCE_ATTESTATION_SHA256 = "5698d5172a4eaa320d59180d1e644f755d1cc4e3a57a0a0ce322b18e191da4e0"
EXTERNAL_SEMANTIC_CORRECTION_OVERLAY_SHA256 = "91b67cee86764cb21b2ba177a02a5807ecc092f7fc20495f80993237d53524f6"
MAPPING_MAX_BYTES = 50 * 1024 * 1024
ROADMAP_PATH = "docs/CUT_ROADMAP_AND_EVIDENCE_MATRIX.md"
ROADMAP_SHA256 = "e358396e7be7ecee89539b1bfb9eb7eb4d331799dd41a64b4cfca4f74e22489b"
ADR0079_PATH = "docs/ADR/0079-cut1-t06-dual-plan-video-strategy.md"
ADR0079_SHA256 = "a20ae1b9fae9e12e9e50baa372b0672c43a9417a21b36a2dc4276f5be1529fd5"
GITLEAKS_FALSE_POSITIVE_CLAUSE_SHA256 = "845855204badc3593c9f4e729d2395d4c443ab2f83771cb1731f7a560f3089c1"
GITHUB_REPOSITORY_ID = 1_282_502_888
GITHUB_REPOSITORY = "imrohitagrawal/narratwin-ai"
OWNER_PLAN_ADOPTION_COMMENT_ID = 0
OWNER_PLAN_ADOPTION_BODY_SHA256 = "PENDING_OWNER_ADOPTION"
OWNER_PLAN_ADOPTION_DOCUMENT_SHA256 = "PENDING_OWNER_ADOPTION"
OWNER_PLAN_RESTRICTED_SOURCE_REF = "restricted-evidence:OWNER_PLAN_2026_09_07"
OWNER_PLAN_RESTRICTED_SOURCE_SHA256 = "986fd1604b385cd1ecd0dad1bfe0e09e6357d0e4b1d58bc94e3c055cc9bec58c"
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
_ROW_FIELDS = frozenset("requirementId sourceAtomId sourceId sourceKind sourcePath sourceAuthorityRefs sourceCommit sourceGitBlob sourceContentSha256 sourceAnchor sourceSpan atomicFocusSha256 normalizedAtomicRequirement normalizedSourceContext normalizedSourceContextSha256 atomicFocusStart atomicFocusEnd atomicFocusOccurrence governingContext repositoryContextDecisionRef semanticClass normativeEffect v2DestinationClause disposition replacementId ownerAuthorityRef thresholdComparison rationale accountableOwner reviewer reviewTime result".split())
ROW_COLUMNS = tuple(sorted(_ROW_FIELDS))
STORED_ROW_COLUMNS = tuple(column for column in ROW_COLUMNS if column != "thresholdComparison")
_MAPPING_FIELDS = frozenset("schemaVersion mappingId proposalState cutoff ownerAuthority sources repositorySemanticDecisionPartition repositoryContextDecisionPartition externalAuthorityManifest externalSemanticCorrectionOverlay semanticDuplicateCensus rows certification".split())
_MAPPING_ARTIFACT_FIELDS = _MAPPING_FIELDS | {"rowEncoding", "rowValues"}
_SOURCE_FIELDS = frozenset("sourceId sourceKind repositoryPath sourceCommit sourceGitBlob contentSha256 atomizer semanticCoverage authorityRefs defaultV2Destination authorityOrigin coverageMode authorityLifecycle objectKind coverageStatus treeEntries treeManifestSha256".split())
_EXTERNAL_MANIFEST_FIELDS = frozenset("schemaVersion repository cutoff referenceCount orderedReferenceCensusSha256 recordCount orderedRecordSha256 retrievedAt records governingContextDecisionPartition closure".split())
_EXTERNAL_RECORD_FIELDS = frozenset("reference sourceKind sourceLocator recordIdentity author createdAt updatedAt byteCount contentSha256 cutoffEligible representation authorityEffect coverageMode coverageStatus contentAddressedRef title classificationBasis semanticCoverage sanitization clauses".split())
_EXTERNAL_CLAUSE_FIELDS = frozenset("atomicFocusEnd atomicFocusOccurrence atomicFocusSha256 atomicFocusStart classificationBasisCode clauseId governingContextDecisionRef losslessNormalizationAttestation normalizedAtomicFocus normalizedSourceContext normalizedSourceContextSha256 normativeEffect offsetCoordinateSystem redactionAttestation sourceAnchor sourceContentSha256 sourceReference sourceSpan suggestedAlias".split())
_TAXONOMY_FIELDS = frozenset("schemaVersion taxonomyId proposalState effectiveAt engineeringStages productModes cuts cutDependencySemantics cut5CapabilityDependencies laneA historicalCheckpoints adrPlans digitalTwinSequence legacyAliases compatibilityMigration activation".split())
_DISPOSITIONS = {"PRESERVED", "STRENGTHENED", "RELOCATED", "SUPERSEDED_BY_EXPLICIT_OWNER_AUTHORITY"}
_THRESHOLD_RELATIONS = {"EQUAL_OR_STRONGER", "OWNER_AUTHORIZED_CHANGE", "NOT_APPLICABLE_NON_NORMATIVE"}
_SEMANTIC_EFFECTS = {"NORMATIVE_REQUIREMENT": "CURRENT_NORMATIVE", "CURRENT_STATE_FACT": "EVIDENCE_ONLY", "HISTORICAL_FACT": "HISTORICAL_ONLY", "USER_OBSERVATION": "EVIDENCE_ONLY", "AUTOMATED_RESULT": "EVIDENCE_ONLY", "COST_ESTIMATE": "EVIDENCE_ONLY", "IMPLEMENTED_BEHAVIOR": "EVIDENCE_ONLY", "CONTEXT_INTRODUCER": "EVIDENCE_ONLY", "EVIDENCE": "EVIDENCE_ONLY", "REFERENCE": "EVIDENCE_ONLY"}
_SEMANTIC_CLASSES = tuple(_SEMANTIC_EFFECTS)
_REPOSITORY_CLASS_CODES = {"N": "NORMATIVE_REQUIREMENT", "S": "CURRENT_STATE_FACT", "H": "HISTORICAL_FACT", "U": "USER_OBSERVATION", "A": "AUTOMATED_RESULT", "C": "COST_ESTIMATE", "I": "IMPLEMENTED_BEHAVIOR", "X": "CONTEXT_INTRODUCER", "E": "EVIDENCE", "R": "REFERENCE"}
_CONTEXT_FOCUS_SPAN_OVERRIDES = {
    GITLEAKS_FALSE_POSITIVE_CLAUSE_SHA256: (
        (0, 24), (26, 45), (47, 61), (63, 82), (84, 93), (95, 160),
        (162, 187), (189, 206), (208, 229), (231, 250), (256, 273),
    ),
    "44d6f818c7a42e24df019791be18525755c2ef78857e759165539ad3c2042ab8": (
        (0, 104), (106, 138), (143, 183),
    ),
    "f5e42852fdab183388fbf6324075224801e64ee6833d2152ea69519d5780c592": (
        (0, 100), (102, 134), (139, 188),
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
def _assert_frozen_git_available(git_directory: Path) -> None:
    _frozen_git(
        git_directory,
        ["fsck", "--connectivity-only", "--no-dangling", BASE_SHA],
    )
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
    for value in """7 15 22 23 26 27 29 30 31 32 33 45 46 47 50 53 54 56 59 62 63 64 73 74 75 76 77 78 79 80 85 87 90 92 94 98 102 103 106 108 110 112 116 120 124 133 134 135 137 140 152 153 162 163 165 166 168 170 173 175 177 179 180 182 185 187 189 191 193 195 197 199 201 203 205 207 210 212 214 216 218 220 222 224 226 230 232 234 236 238 240 242 244 246 248 250 252 254 258 260 262 264 266 268 271 272 273 277 279 281 282 283 284 286 288 293 295 297 299 301 303 305 309 310 314 318 320 322 325 331 333 347 348 350 352 354 362 373 380 381 388 392 395 398 399 400 402 404 407 409 410 411 412 414 417 418 419 422 425 429 430 433 437 443 453 455 457 458 461 462 463 464 465 467 470 474 477 483 491 492 497 501 505""".split()
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
    def canonical_reference(reference: str) -> str:
        _, number = reference.rsplit(":", 1)
        kind = (
            "github-pull-request"
            if int(number) in _REFERENCED_PULL_REQUEST_NUMBERS
            else "github-issue"
        )
        return f"{kind}:{number}"
    canonical = {canonical_reference(reference) for reference in typed}
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
def _semantic_class(atom: Atom, authority_lifecycle: str) -> str:
    """Classify non-Markdown sources; Markdown requires the exact frozen partition."""
    if authority_lifecycle == "IMPLEMENTED" or atom.source_id in {"AVATAR_PROVIDER_CODE", "TTS_PROVIDER_CODE"}:
        return "IMPLEMENTED_BEHAVIOR"
    if authority_lifecycle in {"HISTORICAL", "SUPERSEDED"}:
        return "HISTORICAL_FACT"
    if authority_lifecycle in {"ADVISORY_ONLY", "EVIDENCE", "NO_AUTHORITY", "PROPOSED_BLOCKED", "PROPOSED_NONACTIVATING", "SHADOW"}:
        return "CURRENT_STATE_FACT"
    if "::INSTANCE_FACT:" in atom.anchor:
        return "NORMATIVE_REQUIREMENT" if _json_instance_is_normative(atom) else "CURRENT_STATE_FACT"
    if "::SCHEMA_CONSTRAINT:" in atom.anchor:
        return "NORMATIVE_REQUIREMENT"
    raise ValueError("explicit semantic partition required")
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
def _repository_partition_input(root: Path, supplied: dict[str, Any] | None) -> dict[str, Any]:
    if supplied is not None:
        return supplied
    try:
        artifact = _load_json(root / MAPPING_PATH)
        selected = artifact["repositorySemanticDecisionPartition"]
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("repository semantic decisions unavailable") from exc
    if not isinstance(selected, dict):
        raise ValueError("repository semantic decisions unavailable")
    return selected
def _partitioned_markdown_source(source: dict[str, Any]) -> bool:
    return source.get("atomizer") == "MARKDOWN_ATOMIC_V2" and source.get(
        "sourceKind"
    ) in {"REPOSITORY_FILE", "OWNER_PLAN_CANDIDATE", "OWNER_ADOPTED_PLAN"}
def _repository_semantic_classes(
    sources: list[dict[str, Any]], atoms_by_source: dict[str, list[Atom]],
    partition: dict[str, Any],
) -> dict[str, str]:
    fields = {"schemaVersion", "reviewState", "classCodes", "sourceColumns", "sourceCount", "candidateUnitCount", "classCounts", "unclassifiedUnitCount", "sources", "orderedSourceDecisionSha256", "partitionSha256"}
    columns = ["sourceId", "sourceContentSha256", "orderedAtomIdSha256", "atomCount", "classificationVector", "decisionSha256"]
    expected = [source for source in sources if _partitioned_markdown_source(source)]
    if (set(partition) != fields or partition.get("schemaVersion") != "RepositorySemanticDecisionPartitionV1" or partition.get("reviewState") != "PENDING_INDEPENDENT_REVIEW" or partition.get("classCodes") != _REPOSITORY_CLASS_CODES or partition.get("sourceColumns") != columns or partition.get("sourceCount") != len(expected) or partition.get("unclassifiedUnitCount") != 0 or not isinstance(partition.get("sources"), list) or len(partition["sources"]) != len(expected) or partition.get("partitionSha256") != REPOSITORY_SEMANTIC_PARTITION_SHA256 or partition.get("partitionSha256") != _sha256(_canonical_json({key: value for key, value in partition.items() if key != "partitionSha256"}).encode())):
        raise ValueError("repository semantic decision partition invalid")
    classes: dict[str, str] = {}
    counts = {name: 0 for name in _SEMANTIC_CLASSES}
    decisions: list[str] = []
    for source, entry in zip(expected, partition["sources"], strict=True):
        atoms = atoms_by_source[source["sourceId"]]
        if not isinstance(entry, list) or len(entry) != len(columns):
            raise ValueError("repository semantic source decision invalid")
        source_id, content_sha, atom_sha, atom_count, vector, decision_sha = entry
        material = entry[:-1]
        if (source_id != source["sourceId"] or content_sha != source["contentSha256"] or atom_sha != _sha256(_canonical_json([atom.atom_id for atom in atoms]).encode()) or atom_count != len(atoms) or not isinstance(vector, str) or len(vector) != len(atoms) or any(code not in _REPOSITORY_CLASS_CODES for code in vector) or decision_sha != _sha256(_canonical_json(material).encode())):
            raise ValueError("repository semantic source decision invalid")
        decisions.append(decision_sha)
        for atom, code in zip(atoms, vector, strict=True):
            semantic_class = _REPOSITORY_CLASS_CODES[code]
            if source["authorityLifecycle"] in {"HISTORICAL", "SUPERSEDED", "NO_AUTHORITY", "ADVISORY_ONLY", "EVIDENCE", "PROPOSED_BLOCKED", "PROPOSED_NONACTIVATING", "SHADOW"} and _SEMANTIC_EFFECTS[semantic_class] == "CURRENT_NORMATIVE":
                raise ValueError("repository semantic lifecycle ceiling invalid")
            classes[atom.atom_id] = semantic_class
            counts[semantic_class] += 1
    if (partition.get("candidateUnitCount") != len(classes) or partition.get("classCounts") != counts or partition.get("orderedSourceDecisionSha256") != _sha256(_canonical_json(decisions).encode())):
        raise ValueError("repository semantic decision census invalid")
    return classes
def _semantic_coverage(
    atoms: list[Atom], authority_lifecycle: str, coverage_mode: str,
    semantic_classes: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Bind every extracted unit to exactly one authority-effect partition."""
    entries: list[dict[str, str]] = []
    counts = {name: 0 for name in _SEMANTIC_CLASSES}
    normative_ids: list[str] = []
    for atom in atoms:
        semantic_class = semantic_classes.get(atom.atom_id) if semantic_classes is not None else _semantic_class(atom, authority_lifecycle)
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
_SOURCE_RECORD_CACHE: dict[tuple[Any, ...], bytes] = {}
def _source_records(
    root: Path, repository_semantic_partition: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    try:
        owner_bytes = (root / DOCUMENT_PATH).read_bytes()
        repository_semantic_partition = _repository_partition_input(root, repository_semantic_partition)
        cache_key = (
            str(_git_directory(root)), BASE_SHA, _sha256(owner_bytes),
            OWNER_PLAN_ADOPTION_COMMENT_ID, OWNER_PLAN_ADOPTION_BODY_SHA256,
            OWNER_PLAN_ADOPTION_DOCUMENT_SHA256,
            _sha256(_canonical_json(repository_semantic_partition).encode()),
        )
    except OSError as exc:
        raise ValueError("frozen owner source unavailable") from exc
    cached = _SOURCE_RECORD_CACHE.get(cache_key)
    if cached is not None:
        _assert_frozen_git_available(Path(cache_key[0]))
        return cast(list[dict[str, Any]], json.loads(cached))
    if (
        len(_REPOSITORY_SOURCE_SPECS) != 192
        or len({item[0] for item in _REPOSITORY_SOURCE_SPECS}) != 192
        or len({item[2] for item in _REPOSITORY_SOURCE_SPECS}) != 192
    ):
        raise ValueError("frozen repository inventory definition invalid")
    records: list[dict[str, Any]] = []
    atoms_by_source: dict[str, list[Atom]] = {}
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
        atoms_by_source[source_id] = atoms
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
                "semanticCoverage": None,
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
    repository_classes = _repository_semantic_classes(records, atoms_by_source, repository_semantic_partition)
    for source in records:
        selected = repository_classes if _partitioned_markdown_source(source) else None
        source["semanticCoverage"] = _semantic_coverage(atoms_by_source[source["sourceId"]], source["authorityLifecycle"], source["coverageMode"], selected)
    _SOURCE_RECORD_CACHE.clear()
    _SOURCE_RECORD_CACHE[cache_key] = _canonical_json(records).encode("utf-8")
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
_EXTERNAL_CORRECTION_SPEC = {
    "HISTORICAL_FACT": "comment:4968602415:c780c8c3f55792c4584121297260 comment:5122147727:875d5ce60e4585de9f2bfc4e5e03 comment:5195747476:02e4c51c46c4c5f9019d647ef115 comment:5198618791:94720387351cac6f782e467242a1 comment:5256656667:a3edad9d70c66137c981cd8066a2 comment:5256656667:d830a4ec24fc5620fbf4c7798fa4 comment:5296192826:1a1fbacbdd66c6d65773c3e36345 comment:5296192826:9c62989e8bfb275bcb9f89174dd6 comment:5473594761:f5b16d5f1ba259cb352418e2733a",
    "REFERENCE": "comment:5442862365:1f7f17bec83ebbf16b8851d09582 comment:5442862365:3a889f155e1b6b27dc4a4fd38ffa comment:5442862365:bc1f41186d5ab4f8cf4bc6f9a753 comment:5442862365:c13c07bb8568491b6c628dd0269f comment:5442862365:e16f979d5ddeebd7b762369554ed comment:5442862365:bb12097244a08cbaf41e56c67ff7 comment:5442862365:b99e9281a2089790722e42a67723 comment:5256656667:a183ef755217ad2e1da2f487283b comment:5256656667:2c177aaf099c1f39439cb377cb24 issue:427:EXTREQ-bfdf2b422556a6e622e26dd36ece",
    "COST_ESTIMATE": "issue:494:EXTREQ-236be27d599f9125afa792e22e54",
    "CURRENT_STATE_FACT": "comment:4968602415:ff2740884d513cb4a8a8d71c7acd comment:4968602415:cad7a437312a122ea296762618dc comment:5442862365:69b67f26d8cd44f74f5dbe692687 comment:5442862365:22efa6f467a610f65ef3c12810b9 comment:5442862365:586c0c2e078e715ac5b33b4cdecb comment:5442862365:015b6f7e7149a8f04fea80ece1d3 comment:5442862365:fbb0e648c35f8b3e81dd8dc31882 comment:5442862365:7d5cf4b69d0847ccf808debd209c comment:5442862365:38b4a3e47bf909b92d14e81719be comment:5442862365:bdc6664fe4a3bcc71dcce87ea428 comment:5113777002:ee1949ca3938d11345a7b2123b95 comment:5124615153:223ceab39dae3ceea0939af14294 comment:5313522538:06279880e72ea1190fcd81d010ad comment:5449632582:f1e5f3ea8a9d852ca333b5c33883 comment:5449637037:43052409e29943b32e1044e0ec7b comment:5449637037:0da494e561515ed84b98a707faa0 comment:5463979365:d540b1818aad12c8a58147884e7c comment:5464081073:4e25a4ebf0e37958230254b34aa5 comment:5468493806:da0c9a960baef7bb4a1994185da9 comment:5468986974:0186c3443acd36c03ed82392f81d comment:5474383480:87f658539c3f35a61e5e6670b13d comment:5485657599:540c88fb96fb9198c079771ddc42 comment:5507883668:8d0aa4d804de1df7ff79259b71cc comment:5541564267:72520f25dd17b03afc7df6392833 issue:139:EXTREQ-1f15b8ef68252fe57e57a075c5df issue:144:EXTREQ-8a4004434f963997173de68da96d issue:351:EXTREQ-bc21a05607733f6aa57611b80d8e issue:494:EXTREQ-1b8dfe7a2bd9e84a7ceb655e42d6 issue:494:EXTREQ-37f7723975858bea13780dcc1531",
    "AUTOMATED_RESULT": "comment:5113777002:f769e7ada0870822ee320f2c4af6 comment:5121265229:d525ba5c5833260026911413776d comment:5122147727:ef082e56487496eda0a87aba667c comment:5296192826:72f517ba45866c71b4febb30e4be comment:5313543617:c4b925460835dc7e9f45bf50fae6 comment:5347583669:e88906dbf9e54328fd71f89b2e5a comment:5347583669:b5dfb1d36616b00bee23840e9c18 comment:5446644219:f15d6ea8bce3e539935c4933c8e3 comment:5452170084:5d994aac90112e0b5a803eb9ef7e comment:5463979365:31461c4d5822729f82ae9e19d1ff comment:5464081073:9609b002cbf18b532ba9e29e1ef1 comment:5468511334:b754e935733eeec96ebab486ef08 comment:5470701562:8e7ad122bfabbe944e776bc0b57b comment:5470701562:789055dfc366827cf758247b23d7 comment:5470701562:847a9d4bc81cc49b06d2566bc1e5 comment:5470701562:f8b54774910bf96bc59beac4785c comment:5485657599:fa4018dca2d00676960f07e9f741 comment:5485891564:555cc89325db902280e2482a96e6 comment:5542161744:f82940f73ae37e5da69ee719e049 issue:351:EXTREQ-bbad7daef132e62b692bb5a20445 issue:405:EXTREQ-4f41ad95b4f6dd706a39fdd49610 issue:405:EXTREQ-1fbbd438a9c55f4f0861e3fade64 issue:428:EXTREQ-ece0a967dcd77a96330f1de5036a issue:428:EXTREQ-afa141a8d2c0621c621c1993c656 issue:466:EXTREQ-882003e16c073ccc39c9d2b421ba issue:482:EXTREQ-3913ad7eee7a16607714649ad1be issue:494:EXTREQ-715d4e1d6534b2952f5031d28f79 issue:495:EXTREQ-7325de650f74cdc6ce60b3349600 comment:5256656667:d19984e421280d365a4f284510be comment:5256656667:da4c64141447e44d643fae8d996d comment:5256656667:f9791caf0c0174ae5e62d5421d82",
    "IMPLEMENTED_BEHAVIOR": "comment:5124615153:231728c47bd59004ca199571f5cd comment:5256656667:1d3cc2ae923d76f0d95f5afb4b42 comment:5256656667:0b432f294d0de4dc32951f2257c9 comment:5256656667:bae3c8e2a57ef5af2496b97a7652 comment:5256656667:542c57b7eab727d39959ac04aeab comment:5256656667:92f60dfefab4e7b99af2f9a3657f comment:5466871459:5d7e35acbe6956f3e9b5f8a354db comment:5468813566:9215d0c18c92709c9f0f36050e73 comment:5470636741:cd2ae90f03d8e01a5bac97a08437 comment:5470636741:bd46947e291867d43623febadff6 comment:5470701562:4fc4ce85e6743bed3210aee831e1 issue:17:EXTREQ-ab587f9cfbbb7416451555456c3c issue:315:EXTREQ-d3347e2c519cd0772248d45b98fa issue:349:EXTREQ-bc6c0839f19a9addff17ef8207c6 issue:349:EXTREQ-b91a226b63d3934596be6b23e5cd issue:401:EXTREQ-659fb51a987ea35a9952739d5f59 issue:450:EXTREQ-c6b6f231bf14e27f4d8f4c6d4c36 issue:475:EXTREQ-29ed66aaa418bfe39d1b4fbce676 issue:494:EXTREQ-28e7df77d4af99af97301b74b61e issue:494:EXTREQ-0c04fb90384e9c9520f79d67c4c4 issue:507:EXTREQ-e5ab0f01775d62ded378f6928a18",
    "EVIDENCE": "comment:4968602415:1029417a8e1e0506003273b318ff comment:5461065184:196dcfb1f5caf2f58335257de3b4 comment:5466962967:e60e136c21d8049b1c5e1adee612 comment:5467958861:04bd7dba0fbed66373293d16d1c5 comment:5468026907:a1e76684a1ae4bdba5a354256b7c comment:5468493806:c19faa555aaaa3d0a498f177b2a4 comment:5468511334:2d4283f7f6fb7d3691237a393d51 comment:5468560507:4ce49a32d695eb0f35f0126e7889 comment:5469141049:7b9206a775c7abf75f1c4eca6e9f comment:5471282345:51ce6cf48fc6433613dd54ced5ff comment:5473694821:79031b38841d6bd9b7c723eb5e92 comment:5473718767:dbf631e5f933e82afaf59fc14c39 comment:5481522433:553f55c5b7c3e6f45696490830e0 comment:5484097802:06d2975c514eb63f13d7865ad162 comment:5492585578:440dc599d206aef97badd0082b0f comment:5492618746:e2fb3a1e44b05fb681ba6a17333f comment:5495025249:c34f34bbd5957e21f01e6a1f2367 comment:5498589302:0b8e4ad04348ccae72d1f218a016 comment:5498765949:991cfacd06ea74b7b639ad9f3cef comment:5511888548:d76a6aae4067c1c4b0d961f04ff3 comment:5511933453:9f70ef9ce93b9a5c59ade2c0f039 comment:5512191367:0acb89ac075f6b2373f0522dc09e comment:5522092317:383df3b6abaaf8c075ddbd377e52 comment:5522141413:3aa4db39bf845b0e1371a79d7e24 comment:5522156212:1f9d3e9badade48f45811c433a61 issue:466:EXTREQ-596aa19ad43efbabab6958377355 issue:468:EXTREQ-c96d15554e6bb05204f008c19f8e issue:471:EXTREQ-e7548f436307a40f6b6305cefd1e issue:473:EXTREQ-527f6540c71e71e6ec3c12dfa7bd issue:475:EXTREQ-41d1b1969b7f0837224bb6ccd2a4 issue:479:EXTREQ-7ea1d654fc1f5073944b94319469 issue:482:EXTREQ-6227dba7bf641042e9c510ee06d8 comment:5521410237:4fcd8b5165d85324a4cdd82c8723 comment:5521410237:42ddfc29e5c1b63ab2ae1938b232 comment:5521410237:569a61409332125a0b239e3888c4 comment:5521410237:cf0ad7cd56102324a469439604fa comment:5521410237:245a44501c46d376217290ef220e comment:5521410237:ba43ed76b50c631fefa415489635 comment:5521410237:8786e19a66fba2b1fc8c003a7a97 comment:5521410237:d58a311f38d047da8b4a1a531b47 comment:5521410237:af281e50926f0863ad19bc185526 comment:5521410237:e96b918111316093e9b8b45d7580 comment:5521410237:88d035140abdfd6a655c5d1b31f8 comment:5521410237:333076a81b4871be3f773e2e296f comment:5521410237:68402b87b47e403c17a3c3b31a83 comment:5521410237:e9c136d4f6af85d0323c32981214 comment:5521410237:a2ad8b90b54d1fa3a8e16270d1d6 comment:5521410237:c01faa44c01bd99e28dec2655627 comment:5521410237:90b219ec64caac9b7e5ff9f20475 comment:5521410237:e1dbdad35d358929eb3679852bf5 comment:5521410237:bce721e2843bc0c9cfcacaf5cd7c comment:5521410237:cb4b9b0d9bb5ea29ba4928b60603 comment:5521410237:8828689b848ac400152b43ce2e1f comment:5521410237:e821b7be627de55711cc296f4087 comment:5521410237:7ee46f3a468b7cbefcd8636ed85c comment:5521410237:067e65a8821ce856cc4712e917c6 comment:5521410237:b48501550982cb9e9f034534043a comment:5521410237:e522fdd7230774b7cda46d102f0e comment:5521410237:98325f7d8aacfdee6589ea88f6e4 comment:5521410237:b21a59f3a884d344e7da556cfb33 comment:5521410237:8af58b2f566b5994ad5582a46000 comment:5521410237:60b0b0e4e8379fd0665bbc4cca0d comment:5521410237:077dbb1827657f8f1e2231202904 comment:5521410237:dda8045365b1f8ebef1a2e1fcb5e comment:5521410237:a37454df48d38b677a1f5d7b8125 comment:5521410237:adb4ed1e6384e7128b4c61e5b330 comment:5521588438:06f5793cdb77dd882651cde85a04 comment:5521588438:a2876e447193319929f362a4f09f comment:5521588438:a9ada1ca02fabc18bcde9a9f53d6 comment:5521588438:3ce487f23da7e23cf56cc0e215f1 comment:5521588438:ff29096e8fbd3dcf68b02d9c7d18 comment:5521588438:c0e62cfc3daf22340cae20381100 comment:5521588438:c05beaace2de64a55921a781a275 comment:5521588438:a622409ba6f55c17bd71174cd758 comment:5521588438:83c1103f300b0e0d8cc83892be4f comment:5521588438:b1ed9e9f3e052b456a9d0d71de11 comment:5521588438:41147067b1535f5c0e08ae7b2164 comment:5521588438:f89848840b5c8ecd491bd7744043 comment:5521588438:7a1803e2362d9294de4828c4bb8d comment:5521588438:7540c912a17bb73c2c5f349051f5 comment:5521588438:93dcc7891e44152cf93a092b5718 comment:5521588438:98292d6f221c78cb04699bee7a8a comment:5521588438:c3da181843e5f54fc1e782398f26 comment:5521588438:9a00aff1068bfeadb887b33c0f10",
}
def _expected_external_semantic_corrections() -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for semantic_class, specification in _EXTERNAL_CORRECTION_SPEC.items():
        for item in specification.split():
            kind, number, clause_id = item.split(":")
            if kind == "comment":
                clause_id = "EXTCOMMENTCLAUSE-" + clause_id
            key = (f"github-{kind}:{number}", clause_id)
            if key in result:
                raise ValueError("duplicate external correction")
            result[key] = semantic_class
    if len(result) != 185:
        raise ValueError("external correction census drift")
    return result
def _legacy_external_authority_manifest(root: Path) -> dict[str, Any]:
    data = _frozen_git(
        _git_directory(root),
        [
            "show",
            f"{LEGACY_EXTERNAL_AUTHORITY_SOURCE_COMMIT}:{MAPPING_PATH}",
        ],
    )
    if _sha256(data) != LEGACY_EXTERNAL_AUTHORITY_SOURCE_MAPPING_SHA256:
        raise ValueError("legacy external authority source mapping invalid")
    artifact = _load_json_text(data.decode("utf-8"))
    manifest = artifact.get("externalAuthorityManifest")
    if (
        not isinstance(manifest, dict)
        or _sha256(_canonical_json(manifest).encode())
        != LEGACY_EXTERNAL_AUTHORITY_MANIFEST_SHA256
    ):
        raise ValueError("legacy external authority manifest invalid")
    return manifest
def _build_external_identity_equivalence_attestation(
    root: Path, manifest: dict[str, Any],
) -> dict[str, Any]:
    legacy_manifest = _legacy_external_authority_manifest(root)
    legacy_records = {
        record["reference"]: record for record in legacy_manifest["records"]
    }
    records = {record["reference"]: record for record in manifest["records"]}
    columns = [
        "legacyReference", "legacyRecordId", "legacyApiUrl",
        "legacyContentAddressedRef", "legacyClassificationBasisSha256",
        "correctedReference", "correctedRecordId", "correctedApiUrl",
        "correctedContentAddressedRef", "correctedClassificationBasisSha256",
        "contentSha256", "byteCount", "nodeId", "authorityEffect",
        "normativeClauseCount", "decisionSha256",
    ]
    corrections: list[list[Any]] = []
    for number, (legacy_id, corrected_id) in sorted(
        _EXTERNAL_PULL_REQUEST_IDENTITY_CORRECTIONS.items()
    ):
        legacy_reference = f"github-issue:{number}"
        corrected_reference = f"github-pull-request:{number}"
        legacy = legacy_records.get(legacy_reference)
        record = records.get(corrected_reference)
        if (
            not isinstance(legacy, dict)
            or not isinstance(record, dict)
            or legacy.get("sourceKind") != "EXTERNAL_GITHUB_ISSUE_BODY"
            or legacy.get("sourceLocator", {}).get("apiUrl")
            != f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{number}"
            or legacy.get("recordIdentity", {}).get("recordId") != legacy_id
            or record.get("sourceKind") != "EXTERNAL_GITHUB_PULL_REQUEST_BODY"
            or record.get("sourceLocator", {}).get("apiUrl")
            != f"https://api.github.com/repos/{GITHUB_REPOSITORY}/pulls/{number}"
            or record.get("recordIdentity", {}).get("recordId") != corrected_id
            or record.get("authorityEffect") != "EVIDENCE_ONLY"
            or record.get("clauses") != []
            or record.get("semanticCoverage", {}).get("normativeClauseCount") != 0
        ):
            raise ValueError("external pull-request identity correction invalid")
        comparison = copy.deepcopy(record)
        for path, legacy_value in (
            (("reference",), legacy["reference"]),
            (("sourceKind",), legacy["sourceKind"]),
            (("sourceLocator", "apiUrl"), legacy["sourceLocator"]["apiUrl"]),
            (("recordIdentity", "recordId"), legacy["recordIdentity"]["recordId"]),
            (("contentAddressedRef",), legacy["contentAddressedRef"]),
            (("classificationBasis", "contentAddressedRef"), legacy["classificationBasis"]["contentAddressedRef"]),
            (("classificationBasis", "basisSha256"), legacy["classificationBasis"]["basisSha256"]),
        ):
            target = comparison
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = legacy_value
        if comparison != legacy:
            raise ValueError("external identity correction changed semantic payload")
        material: list[Any] = [
            legacy_reference, legacy_id, legacy["sourceLocator"]["apiUrl"],
            legacy["contentAddressedRef"],
            legacy["classificationBasis"]["basisSha256"], corrected_reference,
            corrected_id, record["sourceLocator"]["apiUrl"],
            record["contentAddressedRef"],
            record["classificationBasis"]["basisSha256"],
            record["contentSha256"], record["byteCount"],
            record["recordIdentity"]["nodeId"], record["authorityEffect"],
            record["semanticCoverage"]["normativeClauseCount"],
        ]
        corrections.append(
            [*material, _sha256(_canonical_json(material).encode())]
        )
    value: dict[str, Any] = {
        "schemaVersion": "ExternalSourceIdentityEquivalenceAttestationV1",
        "reviewState": "PENDING_INDEPENDENT_REVIEW",
        "legacySourceManifestSha256": LEGACY_EXTERNAL_AUTHORITY_MANIFEST_SHA256,
        "correctedSourceManifestSha256": _sha256(
            _canonical_json(manifest).encode()
        ),
        "classifierSourceArtifactRef": (
            f"git:{LEGACY_EXTERNAL_AUTHORITY_SOURCE_COMMIT}:{MAPPING_PATH}"
            "#/externalAuthorityManifest"
        ),
        "equivalenceMethod": (
            "FROZEN_MANIFEST_EXACT_RECORD_DIFF_PLUS_AUTHENTICATED_ENDPOINT_"
            "BODY_EQUIVALENCE_NO_CLASSIFIER_REPLAY"
        ),
        "reuseScope": "EVIDENCE_ONLY_ZERO_NORMATIVE_CLAUSE_RESULT_ONLY",
        "correctionColumns": columns,
        "correctionCount": len(corrections),
        "corrections": corrections,
        "orderedCorrectionSha256": _sha256(
            _canonical_json([item[-1] for item in corrections]).encode()
        ),
    }
    value["attestationSha256"] = _sha256(_canonical_json(value).encode())
    return value
def _external_semantic_corrections(
    root: Path, manifest: dict[str, Any], overlay: dict[str, Any],
) -> dict[tuple[str, str], str]:
    fields = {"schemaVersion", "reviewState", "sourceManifestSha256", "sourceIdentityEquivalenceAttestation", "decisionColumns", "decisionCount", "recordCount", "classCounts", "unreviewedNormativeClauseCount", "decisions", "orderedDecisionSha256", "overlaySha256"}
    columns = ["sourceReference", "sourceContentSha256", "clauseId", "correctedSemanticClass", "basisCode", "decisionSha256"]
    identity_attestation = overlay.get("sourceIdentityEquivalenceAttestation")
    if set(overlay) != fields or overlay.get("schemaVersion") != "ExternalSemanticCorrectionOverlayV1" or overlay.get("reviewState") != "PARTIAL_DEFINITE_CORRECTIONS_PENDING_EXHAUSTIVE_REVIEW" or overlay.get("sourceManifestSha256") != _sha256(_canonical_json(manifest).encode()) or identity_attestation != _build_external_identity_equivalence_attestation(root, manifest) or not isinstance(identity_attestation, dict) or identity_attestation.get("attestationSha256") != EXTERNAL_IDENTITY_EQUIVALENCE_ATTESTATION_SHA256 or overlay.get("decisionColumns") != columns or overlay.get("overlaySha256") != EXTERNAL_SEMANTIC_CORRECTION_OVERLAY_SHA256 or overlay.get("overlaySha256") != _sha256(_canonical_json({key: value for key, value in overlay.items() if key != "overlaySha256"}).encode()) or not isinstance(overlay.get("decisions"), list):
        raise ValueError("external semantic correction overlay invalid")
    clause_index = {(record["reference"], clause["clauseId"]): (record["contentSha256"], clause) for record in manifest["records"] for clause in record["clauses"]}
    corrections: dict[tuple[str, str], str] = {}
    counts: Counter[str] = Counter()
    digests: list[str] = []
    for decision in overlay["decisions"]:
        if not isinstance(decision, list) or len(decision) != 6 or tuple(decision[:2]) != (decision[0], clause_index.get((decision[0], decision[2]), (None,))[0]) or decision[4] != "INDEPENDENT_REPRODUCED_FALSE_NORMATIVE" or decision[3] not in _SEMANTIC_EFFECTS or _SEMANTIC_EFFECTS[decision[3]] == "CURRENT_NORMATIVE" or decision[5] != _sha256(_canonical_json(decision[:-1]).encode()) or (decision[0], decision[2]) in corrections:
            raise ValueError("external semantic correction decision invalid")
        corrections[(decision[0], decision[2])] = decision[3]
        counts[decision[3]] += 1
        digests.append(decision[5])
    total = sum(len(record["clauses"]) for record in manifest["records"])
    if corrections != _expected_external_semantic_corrections() or overlay.get("decisionCount") != 185 or overlay.get("recordCount") != 78 or overlay.get("classCounts") != dict(sorted(counts.items())) or overlay.get("unreviewedNormativeClauseCount") != total - len(corrections) or overlay.get("orderedDecisionSha256") != _sha256(_canonical_json(digests).encode()):
        raise ValueError("external semantic correction census invalid")
    return corrections
def _external_new_atoms(
    manifest: dict[str, Any], corrected: frozenset[tuple[str, str]] = frozenset(),
) -> dict[str, Atom]:
    atoms: dict[str, Atom] = {}
    for record in manifest.get("records", []):
        if not isinstance(record, dict):
            continue
        for clause in record.get("clauses", []):
            if (record["reference"], clause["clauseId"]) in corrected:
                continue
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
    repository_context_decision_ref: str | None = None,
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
        "repositoryContextDecisionRef": repository_context_decision_ref,
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
    repository_semantic_partition: dict[str, Any] | None = None,
    repository_context_partition: dict[str, Any] | None = None,
    external_semantic_correction_overlay: dict[str, Any] | None = None,
    *,
    copy_result: bool = True,
) -> dict[str, Any]:
    repository_semantic_partition = _repository_partition_input(root, repository_semantic_partition)
    sources = _source_records(root, repository_semantic_partition)
    if repository_context_partition is None or external_semantic_correction_overlay is None:
        try:
            current_artifact = _load_json(root / MAPPING_PATH)
        except (OSError, TypeError, ValueError):
            current_artifact = {}
        if repository_context_partition is None:
            repository_context_partition = current_artifact.get("repositoryContextDecisionPartition")
        if external_semantic_correction_overlay is None:
            external_semantic_correction_overlay = current_artifact.get("externalSemanticCorrectionOverlay")
    if not isinstance(repository_context_partition, dict) or not isinstance(external_semantic_correction_overlay, dict):
        raise ValueError("mapping decision overlays unavailable")
    selected_external = _selected_external_authority_manifest(
        root, sources, external_manifest
    )
    external_corrections = _external_semantic_corrections(
        root, selected_external, external_semantic_correction_overlay
    )
    cache_key = _sha256(
        _canonical_json(
            {
                "sources": sources,
                "repositorySemanticDecisionPartition": repository_semantic_partition,
                "repositoryContextDecisionPartition": repository_context_partition,
                "externalSemanticCorrectionOverlay": external_semantic_correction_overlay,
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
    repository_classes = _repository_semantic_classes(sources, atoms_by_source, repository_semantic_partition)
    skeleton = _repository_context_skeleton(sources, source_bytes_by_id, atoms_by_source)
    repository_context_refs, repository_context_hashes = _repository_context_bindings(skeleton, repository_classes, repository_context_partition)
    _validate_conflict_rules(atoms_by_source)
    owner_source = next(source for source in sources if source["sourceId"] == "OWNER_PLAN_2026_09_07")
    adoption_ref = owner_source["authorityRefs"][0]
    replacements = _owner_replacements(atoms_by_source["OWNER_PLAN_2026_09_07"])
    rows: list[dict[str, Any]] = []
    for source in sources:
        for atom in atoms_by_source[source["sourceId"]]:
            semantic_class = repository_classes[atom.atom_id] if atom.atom_id in repository_classes else _semantic_class(atom, source["authorityLifecycle"])
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
                    repository_context_decision_ref=repository_context_refs.get(atom.atom_id),
                )
            )
    rows_by_atom = {row["sourceAtomId"]: row for row in rows}
    for record in selected_external.get("records", []):
        if not isinstance(record, dict) or record.get("authorityEffect") not in {
            "CURRENT_NORMATIVE", "SUPERSEDED_NORMATIVE", "MIXED_NORMATIVE",
        }:
            continue
        for clause in record.get("clauses", []):
            if (record["reference"], clause["clauseId"]) in external_corrections:
                continue
            alias = clause.get("suggestedAlias")
            if isinstance(alias, dict) and alias.get("kind") == "EXISTING_REQUIREMENT":
                target = rows_by_atom.get(alias.get("sourceAtomId"))
                if target is None:
                    raise ValueError("external alias target is not normative")
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
    context_hashes = _context_chain_hashes(rows, repository_context_hashes, selected_external)
    duplicate_census = semantic_duplicate_census(rows, context_hashes)
    mapping = {
        "schemaVersion": "SupersetMappingV2",
        "mappingId": "narratwin-master-program-v2-superset",
        "proposalState": "PROPOSED",
        "cutoff": "2026-09-06T23:59:59+05:30",
        "ownerAuthority": adoption_ref,
        "sources": sources,
        "repositorySemanticDecisionPartition": repository_semantic_partition,
        "repositoryContextDecisionPartition": repository_context_partition,
        "externalAuthorityManifest": selected_external,
        "externalSemanticCorrectionOverlay": external_semantic_correction_overlay,
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
    _GENERATED_MAPPING_CACHE.clear()
    _GENERATED_MAPPING_CACHE[cache_key] = copy.deepcopy(mapping)
    return mapping
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
def _markdown_line_kind(line: str) -> tuple[str, int, int]:
    body = (text := line.rstrip("\r\n")).lstrip(" \t")
    heading = re.match(r"^(#{1,6})\s+\S", body)
    kind = "BLANK" if not body or body.startswith("<!--") and body.endswith("-->") else "HEADING" if heading else "LIST" if re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", body) else "FENCE" if body.startswith("```") else "TABLE" if body.startswith("|") and body.endswith("|") else "PROSE"
    return kind, len(text[: len(text) - len(body)].expandtabs(4)), len(heading.group(1)) if heading else 0
def _markdown_block_continues(parent: tuple[str, int, int], first: tuple[str, int, int], base: int, item: tuple[str, int, int]) -> bool:
    return (item[0] != "HEADING" or item[2] > base) if first[0] == "HEADING" else (item[0] == "BLANK" or item[0] != "HEADING" and item[1] > parent[1]) if parent[0] == "LIST" else (item[0] == "BLANK" or item[0] == "LIST" and item[1] >= first[1] or item[0] != "HEADING" and item[1] > first[1]) if first[0] == "LIST" else item[0] == "TABLE" if first[0] == "TABLE" else item[0] not in {"BLANK", "HEADING"}
def _governed_markdown_block(
    lines: list[str], atom: Atom, metadata: list[tuple[str, int, int]] | None = None,
) -> tuple[int, int, str] | None:
    metadata = metadata or [_markdown_line_kind(line) for line in lines]
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
def _repository_context_skeleton(
    sources: list[dict[str, Any]], source_bytes: dict[str, bytes],
    atoms_by_source: dict[str, list[Atom]],
) -> list[list[Any]]:
    parents: list[list[Any]] = []
    for source in sources:
        if not _partitioned_markdown_source(source):
            continue
        lines = source_bytes[source["sourceId"]].decode().splitlines(keepends=True)
        metadata = [_markdown_line_kind(line) for line in lines]
        atoms = atoms_by_source[source["sourceId"]]
        atoms_by_span: dict[tuple[int, int], list[Atom]] = defaultdict(list)
        for atom in atoms:
            atoms_by_span[(atom.source_span_start_line, atom.source_span_end_line)].append(atom)
        for atom in atoms:
            span_atoms = atoms_by_span[(atom.source_span_start_line, atom.source_span_end_line)]
            colon_candidate = re.fullmatch(r"[^\n]+:", atom.text.strip()) is not None
            prose_block_candidate = (
                "::prose:" in atom.anchor
                and not any(re.fullmatch(r"[^\n]+:", item.text.strip()) for item in span_atoms)
            )
            block = _governed_markdown_block(lines, atom, metadata)
            if block is None or not (
                colon_candidate
                or prose_block_candidate
                and metadata[block[0] - 1][0] in {"LIST", "TABLE", "FENCE", "HEADING"}
            ):
                continue
            children = [child.atom_id for child in sorted((child for child in atoms if child.atom_id != atom.atom_id and block[0] <= child.source_span_start_line <= block[1]), key=lambda child: (child.source_span_start_line, child.source_span_end_line, child.anchor, child.focus_start, child.atom_id))]
            parents.append([source["sourceId"], source["contentSha256"], atom.atom_id, atom.clause_sha256, atom.source_span_start_line, atom.source_span_end_line, block[0], block[1], block[2], children])
    if len(parents) != 985:
        raise ValueError("repository context skeleton drift")
    return parents
_REPOSITORY_CONTEXT_DISPOSITIONS = {
    "COLLECTIVE_NORMATIVE_OPERATOR": ("COLLECTIVE_SET_REQUIREMENT", "PRESERVE_EXPLICIT_CLASS"),
    "NORMATIVE_CHILD_OPERATOR": ("NORMATIVE_SCOPE_OPERATOR", "INHERIT_CURRENT_NORMATIVE"),
    "NORMATIVE_PARENT_AND_CHILD_OPERATOR": ("NORMATIVE_PARENT_AND_SCOPE_OPERATOR", "INHERIT_CURRENT_NORMATIVE"),
    "NORMATIVE_PARENT_SCOPE": ("NORMATIVE_PARENT_BOUND_SCOPE", "PRESERVE_EXPLICIT_CLASS"),
    "CONTEXT_ONLY_SCOPE": ("BOUND_SCOPE", "PRESERVE_EXPLICIT_CLASS"),
    "NONNORMATIVE_EVIDENCE_OR_STATE_CONTEXT": ("EVIDENCE_CEILING", "CAP_NONNORMATIVE"),
    "NONNORMATIVE_HISTORICAL_CONTEXT": ("HISTORICAL_CEILING", "CAP_NONNORMATIVE"),
    "NONNORMATIVE_IMPLEMENTED_CONTEXT": ("IMPLEMENTED_CEILING", "CAP_NONNORMATIVE"),
    "NO_GOVERNING_RELATION": ("NO_GOVERNING_OPERATOR", "NO_RELATION"),
}
def _build_repository_context_partition(
    skeleton: list[list[Any]], classes: dict[str, str], dispositions: dict[str, str],
) -> dict[str, Any]:
    relation_basis = "EXACT_GOVERNED_BLOCK_MEMBERSHIP"
    child_basis = "EXPLICIT_CLASS_WITH_ORDERED_CONTEXT_CHAIN"
    parent_columns = ["sourceId", "sourceContentSha256", "parentAtomId", "parentAtomicFocusSha256", "parentStartLine", "parentEndLine", "blockStartLine", "blockEndLine", "blockSha256", "disposition", "operatorCode", "basisCode", "decisionSha256"]
    relation_columns = ["parentIndex", "childAtomId", "effect", "decisionSha256"]
    child_columns = ["childAtomId", "orderedRelationIndexes", "orderedRelationDecisionSha256", "semanticClass", "decisionSha256"]
    parents: list[list[Any]] = []
    relations: list[list[Any]] = []
    by_child: dict[str, list[int]] = {}
    for parent_index, raw in enumerate(skeleton):
        disposition = dispositions[raw[2]]
        operator, effect = _REPOSITORY_CONTEXT_DISPOSITIONS[disposition]
        material = [*raw[:-1], disposition, operator, "EXPLICIT_EXACT_PARENT_DECISION"]
        parents.append([*material, _sha256(_canonical_json(material).encode())])
        if effect == "NO_RELATION":
            continue
        for child_id in raw[-1]:
            relation_material = [parent_index, parents[-1][-1], child_id, effect, relation_basis]
            by_child.setdefault(child_id, []).append(len(relations))
            relations.append([parent_index, child_id, effect, _sha256(_canonical_json(relation_material).encode())])
    parent_spans = [(parent[6], parent[7]) for parent in parents]
    children: list[list[Any]] = []
    for child_id, indexes in sorted(by_child.items()):
        ordered = sorted(indexes, key=lambda index: (parent_spans[relations[index][0]][0], -parent_spans[relations[index][0]][1], index))
        chain_sha256 = _sha256(_canonical_json([relations[index][-1] for index in ordered]).encode())
        material = [child_id, ordered, chain_sha256, classes[child_id], child_basis]
        children.append([child_id, ordered, chain_sha256, classes[child_id], _sha256(_canonical_json(material).encode())])
    value: dict[str, Any] = {"schemaVersion": "RepositoryContextDecisionPartitionV1", "reviewState": "PENDING_INDEPENDENT_REVIEW", "parentColumns": parent_columns, "relationColumns": relation_columns, "relationBasisCode": relation_basis, "childColumns": child_columns, "childBasisCode": child_basis, "parentCount": len(parents), "relationCount": len(relations), "uniqueChildCount": len(children), "unresolvedDecisionCount": 0, "parents": parents, "relations": relations, "children": children, "orderedParentDecisionSha256": _sha256(_canonical_json([item[-1] for item in parents]).encode()), "orderedRelationDecisionSha256": _sha256(_canonical_json([item[-1] for item in relations]).encode()), "orderedChildDecisionSha256": _sha256(_canonical_json([item[-1] for item in children]).encode())}
    value["partitionSha256"] = _sha256(_canonical_json(value).encode())
    return value
def _repository_context_bindings(
    skeleton: list[list[Any]], classes: dict[str, str], partition: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    expected_fields = {"schemaVersion", "reviewState", "parentColumns", "relationColumns", "relationBasisCode", "childColumns", "childBasisCode", "parentCount", "relationCount", "uniqueChildCount", "unresolvedDecisionCount", "parents", "relations", "children", "orderedParentDecisionSha256", "orderedRelationDecisionSha256", "orderedChildDecisionSha256", "partitionSha256"}
    parent_columns = ["sourceId", "sourceContentSha256", "parentAtomId", "parentAtomicFocusSha256", "parentStartLine", "parentEndLine", "blockStartLine", "blockEndLine", "blockSha256", "disposition", "operatorCode", "basisCode", "decisionSha256"]
    relation_columns = ["parentIndex", "childAtomId", "effect", "decisionSha256"]
    child_columns = ["childAtomId", "orderedRelationIndexes", "orderedRelationDecisionSha256", "semanticClass", "decisionSha256"]
    relation_basis = "EXACT_GOVERNED_BLOCK_MEMBERSHIP"
    child_basis = "EXPLICIT_CLASS_WITH_ORDERED_CONTEXT_CHAIN"
    if set(partition) != expected_fields or partition.get("schemaVersion") != "RepositoryContextDecisionPartitionV1" or partition.get("reviewState") != "PENDING_INDEPENDENT_REVIEW" or partition.get("parentColumns") != parent_columns or partition.get("relationColumns") != relation_columns or partition.get("relationBasisCode") != relation_basis or partition.get("childColumns") != child_columns or partition.get("childBasisCode") != child_basis or partition.get("unresolvedDecisionCount") != 0 or partition.get("partitionSha256") != REPOSITORY_CONTEXT_PARTITION_SHA256 or partition.get("partitionSha256") != _sha256(_canonical_json({key: value for key, value in partition.items() if key != "partitionSha256"}).encode()):
        raise ValueError("repository context decision partition invalid")
    parents, relations, children = partition.get("parents"), partition.get("relations"), partition.get("children")
    if not isinstance(parents, list) or not isinstance(relations, list) or not isinstance(children, list) or partition.get("parentCount") != len(skeleton) or (partition.get("relationCount"), partition.get("uniqueChildCount")) != (len(relations), len(children)) or len(parents) != 985:
        raise ValueError("repository context decision census invalid")
    dispositions: dict[str, str] = {}
    for raw, decision in zip(skeleton, parents, strict=True):
        if not isinstance(decision, list) or len(decision) != 13 or decision[:9] != raw[:9] or decision[9] not in _REPOSITORY_CONTEXT_DISPOSITIONS or decision[10:12] != [*_REPOSITORY_CONTEXT_DISPOSITIONS[decision[9]][:1], "EXPLICIT_EXACT_PARENT_DECISION"] or decision[-1] != _sha256(_canonical_json(decision[:-1]).encode()):
            raise ValueError("repository context parent decision invalid")
        dispositions[raw[2]] = decision[9]
        if decision[9] in {"NORMATIVE_PARENT_AND_CHILD_OPERATOR", "NORMATIVE_PARENT_SCOPE"} and classes[raw[2]] != "NORMATIVE_REQUIREMENT" or decision[9] in {"NONNORMATIVE_EVIDENCE_OR_STATE_CONTEXT", "NONNORMATIVE_HISTORICAL_CONTEXT", "NONNORMATIVE_IMPLEMENTED_CONTEXT"} and _SEMANTIC_EFFECTS[classes[raw[2]]] == "CURRENT_NORMATIVE":
            raise ValueError("repository context parent semantics invalid")
    expected_relations: list[list[Any]] = []
    for parent_index, raw in enumerate(skeleton):
        effect = _REPOSITORY_CONTEXT_DISPOSITIONS[dispositions[raw[2]]][1]
        if effect == "NO_RELATION":
            continue
        for child_id in raw[-1]:
            material = [parent_index, parents[parent_index][-1], child_id, effect, relation_basis]
            expected_relations.append([parent_index, child_id, effect, _sha256(_canonical_json(material).encode())])
            if effect == "CAP_NONNORMATIVE" and _SEMANTIC_EFFECTS[classes[child_id]] == "CURRENT_NORMATIVE":
                raise ValueError("repository context ceiling bypassed")
            if effect == "INHERIT_CURRENT_NORMATIVE" and _SEMANTIC_EFFECTS[classes[child_id]] != "CURRENT_NORMATIVE":
                raise ValueError("repository normative context inheritance missing")
    if relations != expected_relations:
        raise ValueError("repository context relation decision invalid")
    by_child: dict[str, list[int]] = {}
    for index, relation in enumerate(relations):
        by_child.setdefault(relation[1], []).append(index)
    spans = [(parent[6], parent[7]) for parent in parents]
    expected_children: list[list[Any]] = []
    for child_id, indexes in sorted(by_child.items()):
        ordered = sorted(indexes, key=lambda index: (spans[relations[index][0]][0], -spans[relations[index][0]][1], index))
        chain_sha256 = _sha256(_canonical_json([relations[index][-1] for index in ordered]).encode())
        material = [child_id, ordered, chain_sha256, classes[child_id], child_basis]
        expected_children.append([child_id, ordered, chain_sha256, classes[child_id], _sha256(_canonical_json(material).encode())])
    if children != expected_children or partition["orderedParentDecisionSha256"] != _sha256(_canonical_json([item[-1] for item in parents]).encode()) or partition["orderedRelationDecisionSha256"] != _sha256(_canonical_json([item[-1] for item in relations]).encode()) or partition["orderedChildDecisionSha256"] != _sha256(_canonical_json([item[-1] for item in children]).encode()):
        raise ValueError("repository context decision digest invalid")
    child_decisions = {item[0]: item[-1] for item in children}
    parent_decisions = {
        raw[2]: parent[-1]
        for raw, parent in zip(skeleton, parents, strict=True)
        if _REPOSITORY_CONTEXT_DISPOSITIONS[parent[9]][1] != "NO_RELATION"
        and classes[raw[2]] == "NORMATIVE_REQUIREMENT"
    }
    refs = {atom_id: "RCTX-C-" + decision for atom_id, decision in child_decisions.items()}
    refs.update({atom_id: "RCTX-P-" + decision for atom_id, decision in parent_decisions.items() if atom_id not in child_decisions})
    for atom_id in child_decisions.keys() & parent_decisions.keys():
        binding = _sha256(
            _canonical_json(
                [
                    "REPOSITORY_CONTEXT_DUAL_ROLE_V1",
                    child_decisions[atom_id],
                    parent_decisions[atom_id],
                ]
            ).encode()
        )
        refs[atom_id] = "RCTX-B-" + binding
    hashes = {atom_id: _sha256(reference.encode()) for atom_id, reference in refs.items()}
    return refs, hashes
def _context_chain_hashes(rows: list[dict[str, Any]], repository_hashes: dict[str, str], manifest: dict[str, Any]) -> dict[str, str]:
    out = dict(repository_hashes)
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
        '  "repositorySemanticDecisionPartition":' + compact(mapping["repositorySemanticDecisionPartition"]) + ",",
        '  "repositoryContextDecisionPartition":' + compact(mapping["repositoryContextDecisionPartition"]) + ",",
        '  "externalAuthorityManifest":'
        + compact(mapping["externalAuthorityManifest"])
        + ",",
        '  "externalSemanticCorrectionOverlay":' + compact(mapping["externalSemanticCorrectionOverlay"]) + ",",
        '  "semanticDuplicateCensus":'
        + compact(mapping["semanticDuplicateCensus"])
        + ",",
        '  "rowEncoding":' + compact(row_encoding) + ",",
        '  "rowValues":' + detector_safe(row_values) + ",",
        '  "rows":' + compact(encoded_rows) + ",",
        '  "certification":' + compact(mapping["certification"]),
        "}",
    ]
    rendered = "\n".join(lines) + "\n"
    for suffix in ('"', '.md"'):
        marker = "API" + "_CONTRACT" + suffix
        rendered = rendered.replace(marker + ',"', marker + ',      "')
    return rendered
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
def expected_source_records(
    root: Path, repository_semantic_partition: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    return {source["sourceId"]: source for source in _source_records(root, repository_semantic_partition)}
def expected_source_atoms(root: Path, mapping: dict[str, Any] | None = None) -> dict[str, Atom]:
    result: dict[str, Atom] = {}
    partition = mapping.get("repositorySemanticDecisionPartition") if isinstance(mapping, dict) else None
    for source in expected_source_records(root, partition).values():
        data = frozen_source_bytes(root, source)
        for atom in _atoms(source["sourceId"], source["atomizer"], data):
            result[atom.atom_id] = atom
    return result
def expected_normative_atoms(
    root: Path, repository_semantic_partition: dict[str, Any] | None = None,
) -> dict[str, Atom]:
    result: dict[str, Atom] = {}
    sources = expected_source_records(root, repository_semantic_partition)
    atoms_by_source = {source["sourceId"]: _atoms(source["sourceId"], source["atomizer"], frozen_source_bytes(root, source)) for source in sources.values()}
    repository_classes = _repository_semantic_classes(list(sources.values()), atoms_by_source, _repository_partition_input(root, repository_semantic_partition))
    for source in sources.values():
        for atom in atoms_by_source[source["sourceId"]]:
            semantic_class = repository_classes[atom.atom_id] if atom.atom_id in repository_classes else _semantic_class(atom, source["authorityLifecycle"])
            if _SEMANTIC_EFFECTS[semantic_class] == "CURRENT_NORMATIVE":
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
            or (match.group(1) == "pull-request") != identity["nodeId"].startswith("PR_")
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
        expected_sources = expected_source_records(root, mapping.get("repositorySemanticDecisionPartition"))
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
    external_overlay = mapping.get("externalSemanticCorrectionOverlay")
    failures.extend(
        _external_authority_failures(
            expected_sources.values(), external_manifest
        )
    )
    try:
        if not isinstance(external_manifest, dict) or not isinstance(external_overlay, dict):
            raise TypeError
        external_corrections = _external_semantic_corrections(
            root, external_manifest, external_overlay,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        external_corrections = {}
        failures.append("MPV2.MAPPING.EXTERNAL_SEMANTIC_CORRECTION_INVALID")
    try:
        expected = expected_normative_atoms(root, mapping.get("repositorySemanticDecisionPartition"))
        if isinstance(external_manifest, dict):
            expected.update(_external_new_atoms(external_manifest, frozenset(external_corrections)))
    except (AttributeError, KeyError, OSError, TypeError, UnicodeError, SyntaxError, ValueError):
        expected = {}
        failures.append("MPV2.MAPPING.ATOMIZATION_FAILED")
    generated_mapping: dict[str, Any] = {}
    try:
        if not isinstance(external_manifest, dict):
            raise ValueError("external authority manifest invalid")
        generated_mapping = generate_mapping(
            root, external_manifest=external_manifest,
            repository_semantic_partition=mapping.get("repositorySemanticDecisionPartition"),
            repository_context_partition=mapping.get("repositoryContextDecisionPartition"),
            external_semantic_correction_overlay=mapping.get("externalSemanticCorrectionOverlay"),
            copy_result=False,
        )
        generated_rows = {
            row["sourceAtomId"]: row for row in generated_mapping["rows"]
        }
        generated_ids = [row["sourceAtomId"] for row in generated_mapping["rows"]]
        for record in external_manifest.get("records", []):
            for clause in record.get("clauses", []):
                if (record["reference"], clause["clauseId"]) in external_corrections:
                    continue
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
            "repositoryContextDecisionRef", "sourceSpan", "sourceGitBlob",
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
                "EXTERNAL_GITHUB_PULL_REQUEST_BODY",
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
                "EXTERNAL_GITHUB_PULL_REQUEST_BODY",
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
            or not isinstance(row.get("repositoryContextDecisionRef"), (str, type(None)))
            or isinstance(row.get("repositoryContextDecisionRef"), str)
            and re.fullmatch(r"RCTX-[BCP]-[0-9a-f]{64}", row["repositoryContextDecisionRef"]) is None
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
            isinstance(generated, dict)
            and row["sourcePath"] == source.get("repositoryPath")
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
            and row["repositoryContextDecisionRef"] == generated.get("repositoryContextDecisionRef")
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
    source_counts = Counter(row.get("sourceId") for row in rows if isinstance(row, dict))
    for source in expected_sources.values():
        count = source_counts[source.get("sourceId")]
        if count != source.get("semanticCoverage", {}).get(
            "normativeRequirementCount"
        ):
            failures.append("MPV2.MAPPING.SOURCE_COUNT_MISMATCH")
    if (
        mapping.get("repositorySemanticDecisionPartition") != generated_mapping.get("repositorySemanticDecisionPartition")
        or mapping.get("repositoryContextDecisionPartition") != generated_mapping.get("repositoryContextDecisionPartition")
        or mapping.get("externalSemanticCorrectionOverlay") != generated_mapping.get("externalSemanticCorrectionOverlay")
    ):
        failures.append("MPV2.MAPPING.DECISION_PARTITION_INVALID")
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
    mapping_shape: tuple[int, int],
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
    expected_shape = {
        "documentBytes": len(document_bytes),
        "documentLines": len(document_bytes.splitlines()),
        "mappingBytes": len(mapping_bytes),
        "mappingLines": len(mapping_bytes.splitlines()),
        "mappingSources": mapping_shape[0],
        "mappingRows": mapping_shape[1],
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
_EXACT_MAPPING_VALIDATION_CACHE: dict[
    tuple[Any, ...], tuple[tuple[str, ...], int, int]
] = {}
def _mapping_artifact_validation_failures(
    root: Path,
    document: str,
    mapping_bytes: bytes,
    mapping_schema_bytes: bytes,
) -> tuple[list[str], int, int]:
    mapping_sha = _sha256(mapping_bytes)
    schema_sha = _sha256(mapping_schema_bytes)
    cacheable = (
        _sha256(document.encode("utf-8")) == DOCUMENT_SHA256
        and mapping_sha == MAPPING_SHA256
        and schema_sha == MAPPING_SCHEMA_SHA256
    )
    try:
        git_directory = str(_git_directory(root))
    except (OSError, ValueError):
        git_directory, cacheable = "UNRESOLVED", False
    cache_key: tuple[Any, ...] = (
        git_directory, BASE_SHA, DOCUMENT_SHA256, mapping_sha,
        schema_sha, OWNER_PLAN_ADOPTION_COMMENT_ID,
        OWNER_PLAN_ADOPTION_BODY_SHA256, OWNER_PLAN_ADOPTION_DOCUMENT_SHA256,
        EXTERNAL_AUTHORITY_MANIFEST_SHA256,
    )
    if cacheable and (cached := _EXACT_MAPPING_VALIDATION_CACHE.get(cache_key)) is not None:
        try:
            _assert_frozen_git_available(Path(git_directory))
        except ValueError:
            return ["MPV2.MAPPING.SOURCE_INVENTORY_FAILED"], cached[1], cached[2]
        return list(cached[0]), cached[1], cached[2]
    failures: list[str] = []
    try:
        mapping_artifact = _load_json_text(mapping_bytes.decode())
        mapping_schema = _load_json_text(mapping_schema_bytes.decode())
    except DuplicateJsonMember:
        return ["MPV2.JSON.DUPLICATE_MEMBER"], -1, -1
    except (UnicodeError, json.JSONDecodeError, ValueError):
        return ["MPV2.JSON.INVALID"], -1, -1
    mapping_sources = mapping_artifact.get("sources") if isinstance(mapping_artifact, dict) else None
    mapping_rows = mapping_artifact.get("rows") if isinstance(mapping_artifact, dict) else None
    shape = (
        len(mapping_sources) if isinstance(mapping_sources, list) else -1,
        len(mapping_rows) if isinstance(mapping_rows, list) else -1,
    )
    try:
        mapping = decode_mapping_artifact(mapping_artifact)
    except (KeyError, TypeError, ValueError):
        mapping = {}
        failures.append("MPV2.MAPPING.ENCODING_INVALID")
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
    result = tuple(dict.fromkeys(failures))
    if cacheable:
        _EXACT_MAPPING_VALIDATION_CACHE.clear()
        _EXACT_MAPPING_VALIDATION_CACHE[cache_key] = (result, shape[0], shape[1])
    return list(result), *shape
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
        taxonomy = _load_json_text(artifact_bytes[TAXONOMY_PATH].decode())
        taxonomy_schema = _load_json_text(artifact_bytes[TAXONOMY_SCHEMA_PATH].decode())
        binding = _load_json_text(artifact_bytes[BINDING_PATH].decode())
    except DuplicateJsonMember:
        return ["MPV2.JSON.DUPLICATE_MEMBER"]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return ["MPV2.JSON.INVALID"]
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
    mapping_validation, mapping_sources, mapping_rows = (
        _mapping_artifact_validation_failures(
            root, document, mapping_bytes, mapping_schema_bytes
        )
    )
    failures.extend(mapping_validation)
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
            (mapping_sources, mapping_rows),
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
