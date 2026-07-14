#!/usr/bin/env python3
"""Executable Phase 1 Closure artifact gate for NarraTwin AI."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PHASE1_BRANCH = re.compile(r"^phase-1-closure-.+")

REQUIRED_INPUT_FILES = {
    "docs/reviews/FINAL_REVIEW.md",
    "docs/reviews/RISK_REGISTER.md",
    "docs/reviews/DEFECT_BACKLOG.md",
    "docs/reviews/GO_NO_GO.md",
}

REQUIRED_PHASE1_FILES = {
    "docs/reviews/PHASE_1_CLOSURE_REPORT.md",
    "docs/RELEASE_READINESS_REVIEW.md",
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/RISK_REGISTER.md",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/reviews/PROCESS_HARDENING_FINDINGS.md",
    "docs/evals/phase1_golden_questions.jsonl",
    "docs/demo/PHASE_1_DEMO_SCRIPT.md",
    "docs/demo/PHASE_1_DEMO_CHECKLIST.md",
    "docs/demo/PHASE_1_SCREENSHOT_GUIDE.md",
    "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
}

MODULE_A_ALLOWED_CHANGED_FILES = REQUIRED_PHASE1_FILES | {
    ".github/CODEOWNERS",
    ".github/pull_request_template.md",
    ".github/workflows/quality-gates.yml",
    "AGENTS.md",
    "Makefile",
    "README.md",
    "docs/PRD.md",
    "docs/QUALITY_GATES.md",
    "docs/RECOMMENDED_REVIEW_ITEMS.md",
    "docs/REPOSITORY_GUARDRAILS.md",
    "docs/ENGINEERING_PROCESS_RCA.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/RUNBOOK.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/PROJECT_GOVERNANCE_LEARNINGS.md",
    "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    "portfolio/README.md",
    "scripts/ci/verify_branch_protection.py",
    "scripts/quality/check_phase1_closure_docs.py",
    "scripts/quality/check_quality_stage.py",
    "scripts/quality/check_recommended_review_items.py",
}
PROCESS_ONLY_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    "scripts/guardrails_check.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_159_BRANCH_PREFIX = "phase-1-closure-process-159-"
ISSUE_159_ALLOWED_CHANGED_FILES = {
    "docs/RELEASE_CHECKLIST.md",
    "docs/RELEASE_READINESS_REVIEW.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_issue159_release_evidence.py",
}
ISSUE_138_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/reviews/ISSUE_138_CLICK_SECURITY_PREFLIGHT.md",
    "pyproject.toml",
    "scripts/__init__.py",
    "scripts/ci/__init__.py",
    "scripts/ci/backend-image-package-check.sh",
    "scripts/ci/check_semgrep_security.py",
    "scripts/ci/dependency-audit.sh",
    "scripts/ci/dependency-security.sh",
    "scripts/ci/docker-build.sh",
    "scripts/ci/fixtures/semgrep/clean.py",
    "scripts/ci/fixtures/semgrep/positive.py",
    "scripts/ci/run-semgrep.sh",
    "scripts/ci/semgrep-canary.yml",
    "scripts/ci/semgrep-targets.txt",
    "scripts/quality/check_stage3_docs.py",
    "tests/unit/test_dependency_security_contract.py",
    "tests/unit/test_phase1_closure_docs.py",
    "tools/semgrep/pyproject.toml",
    "tools/semgrep/reviewed-inputs.sha256",
    "tools/semgrep/uv.lock",
    "uv.lock",
}
ISSUE_141_ALLOWED_CHANGED_FILES = {
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
ISSUE_141_EXPECTED_LAUNCH_LEVEL_ROWS = {
    "Local development/test": (
        "Developers; synthetic or local test data only.",
        "Local Docker PostgreSQL, in-memory state, optional JSON snapshots, and local/mock artifact and provider paths.",
        "No.",
        "Not a launch.",
        "Test evidence only; no availability, shared durability, backup, restore, RTO, or RPO claim.",
    ),
    "Local mock demo": (
        "Controlled presenter-led reviewers; synthetic demo data only; no public endpoint.",
        "The reviewed local Compose/mock stack and optional local restart snapshots.",
        "No.",
        "Conditional Go only through `docs/demo/PHASE_1_DEMO_CHECKLIST.md`.",
        "Product-flow demonstration only; no production-like durability, real-provider, multi-worker, or service-level claim.",
    ),
    "Hosted internal synthetic demo": (
        "Named internal workforce reviewers; synthetic product data only; internal environment access/SSO and minimum employee identity/access audit metadata under documented retention; non-public.",
        "A free or low-cost hosted resource may be considered only after an environment owner documents access control, secret handling, retention, teardown, logging, limits, and incident contact.",
        "No. If the environment is intended to produce production-like evidence, it must move to the production-like validation row and satisfy issues `#142` through `#149`.",
        "No-Go until an environment-specific review records those controls and the applicable product gates pass.",
        "Convenience hosting only; it is not production-like durability evidence and cannot inherit local-demo approval.",
    ),
    "External/invite-only soft launch": (
        "Any external identity or user, customer/content personal data, customer-facing application authentication, public or customer-reachable endpoint, or reliability promise.",
        "Reviewed hosted tenancy with durable data/artifact storage, backup, access control, secrets, monitoring, retention/deletion, incident response, rollback, and named owners.",
        "AWS is the current durability baseline; a different provider requires a reviewed ADR amendment and re-baselined evidence before durability or launch claims.",
        "No-Go.",
        "External users or customer data make this production-adjacent regardless of the words `demo`, `beta`, or `soft launch`.",
    ),
    "Production-like durability validation": (
        "Authorized reviewers; synthetic seed only; no application, customer, or public traffic.",
        "The ADR `0027` non-production RDS/S3/KMS/private-network source and isolated restore-validation landing zone.",
        "Yes, for the current selected baseline.",
        "No-Go until issues `#142` through `#149`, named human approvals, and live environment evidence pass; actual restore results remain with later issue `#126`.",
        "Validates production-shaped durability controls only; it is neither a demo launch nor production authorization.",
    ),
    "Production": (
        "External users and approved production data/traffic.",
        "Separate production tenancy/account with reviewed application, durability, security, privacy, operations, monitoring, rollback, and support controls.",
        "Yes, a separate production AWS account under the current baseline; an alternative requires a superseding ADR and equivalent evidence.",
        "No-Go.",
        "Requires an independent production Go decision; production-like evidence does not automatically authorize production.",
    ),
}
ISSUE_141_EXPECTED_STAGE_ROWS = {
    "Stage 4": ("PostgreSQL:", "S3:", "approved original upload version", "secrets"),
    "Stage 6": ("translation/voice run", "generated audio/downloadable artifact versions", "Raw provider responses"),
    "Stage 7": ("synthetic-media consent", "render/export artifact versions", "cloned-identity material"),
}
ISSUE_141_EXPECTED_CHILD_DEPENDENCIES = {
    "#142": {"#141"},
    "#143": {"#141", "#142"},
    "#144": {"#141"},
    "#145": {"#141", "#144"},
    "#146": {"#141", "#143", "#144", "#145"},
    "#147": {"#144", "#145", "#146"},
    "#148": {"#130", "#141", "#144", "#145", "#146", "#147"},
    "#149": {"#130", *(f"#{number}" for number in range(141, 149))},
}
ISSUE_141_CHILD_ACCEPTANCE_TERMS = {
    "#142": ("connection-backed adapter", "migrations", "No cloud provisioning"),
    "#143": ("S3-version-first", "durable intent", "crash-window", "contiguous", "orphan"),
    "#144": ("exact workflow/environment/OIDC", "IAM DB authentication", "No pre-created target DB"),
    "#145": ("15-day S3", "version-aware journal", "separately signed", "reviewer-export split"),
    "#146": ("immutable source cutoff", "integrity-linked deletion-journal event", "negative corruption"),
    "#147": (
        "creates a new RDS target",
        "IAM-auth",
        "<=5,000,000,000 bytes",
        "SkipFinalSnapshot",
        "live-inventory block",
    ),
    "#148": (
        "RDS/S3 restore",
        "target-configuration/isolation",
        "tested CH-12 route handoff",
        "restore timeout/failure",
        "cleanup overdue/orphan",
        "journal gap/backlog/signature failure",
        "KMS loss",
        "severity",
        "owner acknowledgment/escalation",
        "runbook links",
        "immutable-cutoff",
    ),
    "#149": (
        "tested `#130`/CH-12 routes",
        "later drill",
        "without actual RTO/RPO",
        "leave `#126`",
        "`DUR-RESTORE-001`",
        "`#39` open",
    ),
}
ISSUE_39_EXECUTION_STRATEGY_ALLOWED_CHANGED_FILES = {
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    ".github/workflows/eval-smoke.yml",
    ".github/workflows/quality-gates.yml",
    ".github/workflows/security.yml",
    "docs/QUALITY_GATES.md",
    "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/reviews/ISSUE_39_CH04_CH05_CH06_CONTRACT_DECISIONS.md",
    "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/guardrails_check.py",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_72_ALLOWED_CHANGED_FILES = PROCESS_ONLY_ALLOWED_CHANGED_FILES | {
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "docs/reviews/ISSUE_72_CLOSURE_EVIDENCE_HARDENING_PREFLIGHT.md",
}
ISSUE_37_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    "backend/app/main.py",
    "docs/ADR/0007-local-principal-contract.md",
    "docs/API_CONTRACT.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_MODEL.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/THREAT_MODEL.md",
    "tests/api/test_stage4_slice_api.py",
}
ISSUE_42_ALLOWED_CHANGED_FILES = {
    "backend/app/main.py",
    "backend/app/stage7.py",
    "docs/ADR/0004-avatar-provider-adapter.md",
    "docs/API_CONTRACT.md",
    "docs/QUALITY_GATES.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/PHASE_1_CLOSURE_REPORT.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/api/test_stage7_avatar_api.py",
    "tests/unit/test_stage7_avatar.py",
}
ISSUE_39_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    ".env.example",
    "backend/app/main.py",
    "backend/app/rag/store.py",
    "backend/app/stage4.py",
    "backend/app/stage6.py",
    "backend/app/stage7.py",
    "backend/app/storage/__init__.py",
    "backend/app/storage/file_state.py",
    "docs/ADR/0008-postgresql-durability-schema-boundary.md",
    "docs/API_CONTRACT.md",
    "docs/ADR/0006-stage8-release-hardening.md",
    "docs/LOCAL_DEVELOPMENT.md",
    "docs/OBSERVABILITY_AND_COST.md",
    "docs/PORTABILITY_STRATEGY.md",
    "docs/PROJECT_LEARNINGS_TRACKER.md",
    "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "docs/RISK_REGISTER.md",
    "docs/reviews/RISK_REGISTER.md",
    "docs/SKILLS_AND_CODEX_SETUP.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "scripts/guardrails_check.py",
    "tests/api/test_health_api.py",
    "tests/unit/test_branch_protection_verifier.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
    "tests/unit/test_local_durability.py",
}
ISSUE_39_CONTEXT0_ALLOWED_CHANGED_FILES = MODULE_A_ALLOWED_CHANGED_FILES | {
    ".github/workflows/quality.yml",
    ".github/workflows/security.yml",
    "docs/PROJECT_LEARNINGS_TRACKER.md",
    "docs/REVIEW_RIGOR_RETROSPECTIVE.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "docs/SKILLS_AND_CODEX_SETUP.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/SKILL_TRUST_REVIEW.md",
    "scripts/guardrails_check.py",
    "tests/unit/test_guardrails_check.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT1_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0008-postgresql-durability-schema-boundary.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT2_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT3_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0010-context3-migrations-rollback-compatibility.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CH01_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH02_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH03_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH04_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH05_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH06_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH07_ALLOWED_CHANGED_FILES = {
    "backend/app/main.py",
    "backend/app/stage6.py",
    "backend/app/storage/__init__.py",
    "backend/app/storage/file_state.py",
    "docs/ADR/0009-context2-idempotency-lease-outbox-contract.md",
    "docs/ADR/0020-ch07-stage6-durable-replay.md",
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
}
ISSUE_39_CH08_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH09_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_RESTORE_LOCAL_DRILL_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH14_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0026-ch14-restore-readiness-contract.md",
    "docs/STATUS.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md",
    "docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CH10_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CH11_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0025-ch11-slo-error-budget.md",
    "docs/STATUS.md",
    "docs/STAGE_ISSUE_PLAN.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CH16_ALLOWED_CHANGED_FILES = {
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
}
ISSUE_39_CONTEXT4_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0011-context4-backup-restore-drill.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT5_ALLOWED_CHANGED_FILES = {
    "docs/ADR/0012-context5-metrics-slos-watch.md",
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}
ISSUE_39_CONTEXT6_ALLOWED_CHANGED_FILES = {
    "docs/STATUS.md",
    "docs/TRACEABILITY.md",
    "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md",
    "scripts/quality/check_phase1_closure_docs.py",
    "tests/unit/test_phase1_closure_docs.py",
}

EXPECTED_ISSUE_PRIORITIES = {
    "#35": "P0",
    "#36": "P0",
    "#37": "P1",
    "#38": "P1",
    "#39": "P1",
    "#40": "P0",
    "#41": "P0",
    "#42": "P1",
    "#43": "P2",
    "#44": "P2",
}
EXPECTED_MODULES = {
    "Module A",
    "Module B",
    "Module C",
    "Module D",
    "Module E",
    "Module F",
    "Module G",
}
METRIC_FLOORS = {
    "faithfulnessMin": 0.85,
    "answerRelevancyMin": 0.80,
    "contextPrecisionMin": 0.75,
    "contextRecallMin": 0.70,
}
REQUIRED_GOLDEN_QUESTIONS = {
    "What is this project?",
    "Who is the audience?",
    "What problem does it solve?",
    "What are Mode 1 and Mode 2?",
    "What data sources does it use?",
    "What should the system not claim?",
    "What are the current limitations?",
    "What is the demo flow?",
}
GOLDEN_KEYS = {
    "id",
    "fixtureType",
    "question",
    "expectedAnswer",
    "expectedEvidence",
    "requiredClaims",
    "forbiddenClaims",
    "expectedCitationPolicy",
    "metrics",
    "unsupportedClaimsMax",
}

REQUIRED_PR_TEMPLATE_SECTIONS = (
    "Preflight evidence",
    "Human-only review surfaces",
    "Pre-implementation evidence",
    "Validation evidence",
)

REQUIRED_PR_PREFLIGHT_TABLE_HEADERS = (
    "Evidence",
    "Artifact reference",
    "Matrix IDs",
    "Command / CI / Source",
    "Reviewer",
    "Evidence type",
    "Completion status",
    "Residual risk decision",
)

REQUIRED_PR_HUMAN_ONLY_TABLE_HEADERS = (
    "Surface",
    "Automation gap",
    "Owner",
    "Evidence",
    "Residual risk decision",
    "Expiry / revisit trigger",
)

REQUIRED_PHASE1_VALIDATION_COMMANDS = (
    "uv run pytest tests/unit/test_guardrails_check.py",
    "uv run pytest tests/unit/test_phase1_closure_docs.py",
    "python3 scripts/guardrails_check.py",
    "make quality",
    "uv run ruff check scripts tests",
    "uv run mypy scripts tests",
    "make ci",
    "make security",
    "make dependency-audit",
    "make container-scan",
    "make secrets-scan",
    "make eval",
    "NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1",
)

OPTIONAL_PHASE1_VALIDATION_COMMANDS = (
    "uv run pytest tests/unit/test_branch_protection_verifier.py",
)
REQUIRED_MEDIUM_LOW_PHF_ITEMS = {
    "PHF-007",
    "PHF-008",
    "PHF-009",
    "PHF-010",
    "PHF-011",
    "PHF-012",
    "PHF-013",
}
AUTOMATED_EVIDENCE_TEST = re.compile(r"(?<!/)\btest_[A-Za-z0-9_]+\b(?!\.py)")
AUTOMATED_EVIDENCE_SCRIPT = re.compile(r"\bscripts/[A-Za-z0-9_./-]+\.py\b")
AUTOMATED_EVIDENCE_COMMAND = re.compile(
    r"\b(?:make quality|python3 scripts/guardrails_check\.py|uv run pytest [^`|\n]+)"
)
PHF_CLOSED_STATUSES = {"closed by local edits", "superseded by local edits"}
REQUIRED_ISSUE_39_MATRIX_IDS = {
    "DUR-ACID-001",
    "DUR-IDEMP-001",
    "DUR-STAGE4-001",
    "DUR-LEASE-001",
    "DUR-OUTBOX-001",
    "DUR-STAGE6-001",
    "DUR-STAGE7-001",
    "DUR-MIG-001",
    "DUR-ROLLBACK-001",
    "DUR-RESTORE-001",
    "OPS-METRICS-001",
    "OPS-SLO-001",
    "OPS-ALERT-001",
    "OPS-WATCH-001",
    "OPS-ROLLBACK-001",
    "MEDIA-CONSENT-001",
    "MEDIA-REVOKE-001",
    "MEDIA-PROVENANCE-001",
    "MEDIA-DISCLOSURE-001",
    "PROVIDER-POSTURE-001",
    "SEC-RETENTION-001",
    "SEC-UNTRUSTED-001",
    "GOV-SCOPE-001",
}
VALID_ISSUE_39_MATRIX_STATUSES = {"open", "closed"}
REPOSITORY_FULL_NAME = "imrohitagrawal/narratwin-ai"
ISSUE_39_PLANNING_PR_NUMBERS = {str(number) for number in range(64, 81)}
EXPECTED_ISSUE_39_CHUNK_MATRIX_IDS = {
    "CH-00": {"GOV-SCOPE-001"},
    "CH-01": {"DUR-MIG-001"},
    "CH-02": {"DUR-ACID-001"},
    "CH-03": {"DUR-STAGE4-001"},
    "CH-04": {"DUR-IDEMP-001"},
    "CH-05": {"DUR-LEASE-001"},
    "CH-06": {"DUR-OUTBOX-001"},
    "CH-07": {"DUR-STAGE6-001"},
    "CH-08": {"DUR-STAGE7-001"},
    "CH-09": {"DUR-ROLLBACK-001"},
    "CH-10": {"OPS-METRICS-001"},
    "CH-11": {"OPS-SLO-001"},
    "CH-12": {"OPS-ALERT-001"},
    "CH-13": {"OPS-WATCH-001"},
    "CH-14": {"DUR-RESTORE-001"},
    "CH-15": {"OPS-ROLLBACK-001"},
    "CH-16": {"MEDIA-CONSENT-001"},
    "CH-17": {"MEDIA-REVOKE-001"},
    "CH-18": {"MEDIA-PROVENANCE-001"},
    "CH-19": {"MEDIA-DISCLOSURE-001"},
    "CH-20": {"PROVIDER-POSTURE-001"},
    "CH-21": {"SEC-RETENTION-001"},
    "CH-22": {"SEC-UNTRUSTED-001"},
    "CH-23": REQUIRED_ISSUE_39_MATRIX_IDS,
}
EXPECTED_ISSUE_39_CHUNK_DEPENDENCIES = {
    "CH-00": set(),
    "CH-01": {"CH-00"},
    "CH-02": {"CH-01"},
    "CH-03": {"CH-02", "CH-04", "CH-06"},
    "CH-04": {"CH-02"},
    "CH-05": {"CH-02"},
    "CH-06": {"CH-02"},
    "CH-07": {"CH-03", "CH-04"},
    "CH-08": {"CH-03", "CH-04", "CH-16"},
    "CH-09": {"CH-01", "CH-02", "CH-03"},
    "CH-10": {"CH-04", "CH-05", "CH-06"},
    "CH-11": {"CH-10"},
    "CH-12": {"CH-10", "CH-11"},
    "CH-13": {"CH-12"},
    "CH-14": {"CH-01", "CH-02", "CH-10", "CH-12"},
    "CH-15": {"CH-09", "CH-12", "CH-13"},
    "CH-16": {"CH-02"},
    "CH-17": {"CH-16"},
    "CH-18": {"CH-08", "CH-16"},
    "CH-19": {"CH-18"},
    "CH-20": {"CH-18"},
    "CH-21": {"CH-02", "CH-14", "CH-16", "CH-17", "CH-18"},
    "CH-22": {"CH-03", "CH-07", "CH-08", "CH-21"},
    "CH-23": {f"CH-{index:02d}" for index in range(23)},
}
ISSUE_39_SENSITIVE_ROW_REQUIRED_TERMS = {
    "MEDIA-CONSENT-001": (
        "actor",
        "timestamp",
        "consent text/version",
        "artifact refs",
        "source-run",
        "scope",
        "audit retention",
    ),
    "MEDIA-REVOKE-001": ("retain", "block replay", "takedown", "communication paths"),
    "MEDIA-PROVENANCE-001": (
        "source run",
        "consent record",
        "artifact checksum",
        "identity/likeness denial",
    ),
    "MEDIA-DISCLOSURE-001": ("disclosure versioning", "validation", "artifacts"),
    "PROVIDER-POSTURE-001": (
        "legal/license",
        "mock/local",
        "no real keys in local/dev/test/ci",
        "deny-by-default egress",
        "key isolation",
        "no secret logging",
        "prompt inclusion",
        "rollback disablement",
        "explicit production enablement",
    ),
    "SEC-RETENTION-001": (
        "encryption",
        "redaction",
        "retention",
        "deletion/erasure",
        "backup expiry",
        "restore re-delete",
        "access control",
        "replay/export blocking",
    ),
    "SEC-UNTRUSTED-001": (
        "uploaded docs",
        "prompts",
        "transcripts",
        "provider outputs",
        "model outputs",
        "restored artifacts",
        "exported media metadata",
        "replayed provenance",
        "validation",
        "output encoding",
        "log redaction",
        "prompt-injection/poisoned-retrieval",
        "restore-time revalidation",
        "replay/export safety",
    ),
}
ISSUE_39_OPERATIONAL_CLOSURE_EVIDENCE_TERMS = {
    "DUR-MIG-001": (("migration",), ("dry run", "execution log", "migration log")),
    "DUR-ROLLBACK-001": (("rollback",), ("compatibility", "forward repair")),
    "DUR-RESTORE-001": (("restore drill",), ("rto",), ("rpo",)),
    "OPS-METRICS-001": (("metric",), ("dashboard", "query")),
    "OPS-SLO-001": (("slo",), ("threshold", "error budget")),
    "OPS-ALERT-001": (("alert",), ("route", "routing")),
    "OPS-WATCH-001": (("watch log",), ("120",), ("180",)),
    "OPS-ROLLBACK-001": (("rollback comms", "rollback communication"),),
    "MEDIA-CONSENT-001": (("consent",), ("actor",), ("scope",), ("audit",)),
    "MEDIA-REVOKE-001": (("revocation",), ("block replay",), ("takedown",)),
    "MEDIA-PROVENANCE-001": (("provenance",), ("source run",), ("checksum",)),
    "MEDIA-DISCLOSURE-001": (("disclosure",), ("version",), ("export", "artifact")),
    "PROVIDER-POSTURE-001": (
        ("provider",),
        ("legal/license",),
        ("egress",),
        ("key",),
        ("explicit production enablement",),
    ),
    "SEC-RETENTION-001": (("retention",), ("deletion", "erasure"), ("redaction",), ("restore re-delete",)),
    "SEC-UNTRUSTED-001": (("untrusted",), ("validation",), ("output encoding",), ("log redaction",)),
}
ISSUE_39_PRODUCTION_GRADE_ROW_PREFIXES = ("DUR-", "OPS-", "MEDIA-", "SEC-", "PROVIDER-")
ISSUE_39_DRILL_LOG_PREFIXES = ("docs/reviews/drills/", "reports/", "artifacts/", "logs/")
ISSUE_39_DRILL_LOG_SUFFIXES = {".json", ".jsonl", ".log", ".md", ".txt"}
ISSUE_39_BRANCH_REQUIRED_ANCESTORS = {
    "phase-1-closure-39-ch-02-": ("824a07c2bd546648b96d9ab555b63a8f2415898e",),
    "phase-1-closure-39-ch-03-": (
        "947a96891fd84085b6fce433e604a8e249b25c23",
        "d0a2c80f084d8ec9e25b24b841e4f22031953a73",
    ),
    "phase-1-closure-39-ch-04-": ("b5992a599be06ea444ca66d3f088956eee8c70e6",),
    "phase-1-closure-39-ch-05-": ("b5992a599be06ea444ca66d3f088956eee8c70e6",),
    "phase-1-closure-39-ch-06-": ("b5992a599be06ea444ca66d3f088956eee8c70e6",),
    "phase-1-closure-39-ch-07-": (
        "6449786069dd38eeaa5a4a31f5ed73cbfc52d248",
        "947a96891fd84085b6fce433e604a8e249b25c23",
    ),
    "phase-1-closure-39-ch-08-": (
        "6449786069dd38eeaa5a4a31f5ed73cbfc52d248",
        "947a96891fd84085b6fce433e604a8e249b25c23",
        "1f3d66d9b1b545e5d5c41e88a83cc731a2a8b31a",
        "acccd6939ebe172b9a2d95f51fa96212035f55b0",
    ),
    "phase-1-closure-39-ch-09-": (
        "824a07c2bd546648b96d9ab555b63a8f2415898e",
        "c47471d0c8218d59509cba936fe216b86c9ac1e9",
        "6449786069dd38eeaa5a4a31f5ed73cbfc52d248",
    ),
    "phase-1-closure-39-ch-14-": (
        "384c15ac67810d30096794500da1c90ce056dd54",
        "4b7594c8ae14c6a91dff9f0916447b0e6dec39a9",
        "f94776f6602d4c6feec2412b4764a7368049a080",
    ),
    "phase-1-closure-39-ch-11-": ("384c15ac67810d30096794500da1c90ce056dd54",),
    "phase-1-closure-39-ch-16-": ("824a07c2bd546648b96d9ab555b63a8f2415898e",),
}
PHASE1_STACKED_BASE_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/workflows/eval-smoke.yml",
)
ISSUE_39_STACKED_PUSH_BASE_BRANCH = "origin/phase-1-closure-39-execution-strategy"
ISSUE_39_STACKED_PUSH_BRANCH_PREFIXES = (
    "phase-1-closure-39-ch-04-",
    "phase-1-closure-39-ch-05-",
    "phase-1-closure-39-ch-06-",
)


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=False, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def git_ok(args: list[str]) -> bool:
    result = subprocess.run(["git", *args], cwd=ROOT, check=False, text=True, capture_output=True)
    return result.returncode == 0


def current_branch() -> str:
    return os.environ.get("GITHUB_HEAD_REF", "").strip() or run_git(["branch", "--show-current"])


def preferred_diff_base_for_current_event() -> str:
    base = os.environ.get("GITHUB_BASE_SHA", "").strip()
    if os.environ.get("GITHUB_EVENT_NAME", "").strip() != "push":
        return base
    ref_name = os.environ.get("GITHUB_REF_NAME", "").strip() or os.environ.get("GITHUB_HEAD_REF", "").strip()
    if ref_name and ref_name != "main":
        if ref_name.startswith(ISSUE_39_STACKED_PUSH_BRANCH_PREFIXES):
            return ISSUE_39_STACKED_PUSH_BASE_BRANCH
        return ""
    return base


def resolve_base() -> str:
    preferred = preferred_diff_base_for_current_event()
    if preferred and not re.fullmatch(r"0+", preferred):
        verified = run_git(["rev-parse", "--verify", f"{preferred}^{{commit}}"])
        if verified:
            return preferred
    for candidate in ("origin/main", "main"):
        merge_base = run_git(["merge-base", candidate, "HEAD"])
        if merge_base:
            return merge_base
    return "HEAD~1"


def changed_files() -> list[str]:
    base = resolve_base()
    outputs: list[str] = []
    for args in (
        ["diff", "--name-only", base, "HEAD"],
        ["diff", "--name-only", "HEAD"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        output = run_git(args)
        outputs.append(output)
    return sorted(
        {line.strip() for output in outputs for line in output.splitlines() if line.strip()}
    )


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def known_test_names() -> set[str]:
    return {test_name for test_names in known_tests_by_path().values() for test_name in test_names}


def known_tests_by_path() -> dict[str, set[str]]:
    tests_by_path: dict[str, set[str]] = {}
    test_root = ROOT / "tests"
    for path in test_root.rglob("*.py"):
        relative_path = path.relative_to(ROOT).as_posix()
        tests_by_path[relative_path] = set(
            re.findall(
                r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(",
                path.read_text(encoding="utf-8"),
                flags=re.M,
            )
        )
    return tests_by_path


def pytest_target_paths(text: str) -> set[str]:
    paths, _, _ = pytest_targets_invalid_targets_and_node_ids(text)
    return paths


def pytest_targets_invalid_targets_and_node_ids(text: str) -> tuple[set[str], set[str], set[tuple[str, str, str]]]:
    paths: set[str] = set()
    invalid_targets: set[str] = set()
    node_ids: set[tuple[str, str, str]] = set()
    for command_match in re.finditer(r"\buv run pytest (?P<targets>[^`|\n]+)", text):
        target_text = command_match.group("targets").split("->", maxsplit=1)[0]
        target_text = target_text.split("#", maxsplit=1)[0]
        for token in target_text.split():
            cleaned = token.strip("` ,;:")
            if not cleaned or cleaned.startswith("-"):
                continue
            target_path, separator, node_part = cleaned.partition("::")
            if target_path.startswith("./"):
                target_path = target_path[2:]
            if target_path.endswith(".py") or target_path.startswith("tests/"):
                paths.add(target_path)
                if separator:
                    node_match = re.search(r"\b(test_[A-Za-z0-9_]+)\b", node_part)
                    if node_match:
                        node_ids.add((target_path, node_match.group(1), f"{target_path}::{node_match.group(1)}"))
                    else:
                        invalid_targets.add(cleaned)
            else:
                invalid_targets.add(cleaned)
    return paths, invalid_targets, node_ids


def phf_automated_evidence_failures(item: str, automated: str) -> list[str]:
    failures: list[str] = []
    cited_tests = set(AUTOMATED_EVIDENCE_TEST.findall(automated))
    for test_name in sorted(cited_tests - known_test_names()):
        failures.append(f"{item} Medium/Low matrix cites unknown test evidence: {test_name}")

    cited_scripts = {match.strip("`") for match in AUTOMATED_EVIDENCE_SCRIPT.findall(automated)}
    for script_path in sorted(path for path in cited_scripts if not (ROOT / path).is_file()):
        failures.append(f"{item} Medium/Low matrix cites missing script evidence: {script_path}")

    target_paths, invalid_targets, node_ids = pytest_targets_invalid_targets_and_node_ids(automated)
    for target_path in sorted(path for path in target_paths if not (ROOT / path).is_file()):
        failures.append(f"{item} Medium/Low matrix cites missing pytest target: {target_path}")
    for target in sorted(invalid_targets):
        failures.append(f"{item} Medium/Low matrix cites unsupported pytest target: {target}")
    tests_by_path = known_tests_by_path()
    for target_path, test_name, node_id in sorted(node_ids):
        if (ROOT / target_path).is_file() and test_name not in tests_by_path.get(target_path, set()):
            failures.append(f"{item} Medium/Low matrix cites pytest node id with test outside target: {node_id}")

    has_automated_evidence = bool(
        cited_tests or cited_scripts or AUTOMATED_EVIDENCE_COMMAND.search(automated)
    )
    if not has_automated_evidence:
        failures.append(f"{item} Medium/Low matrix must map to an automated test/guardrail or human-only surface.")
    return failures


def fail(failures: list[str], message: str) -> None:
    failures.append(message)


def table_rows(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def section(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group("body") if match else ""


def subsection(text: str, heading: str) -> str:
    pattern = rf"^### {re.escape(heading)}\n(?P<body>.*?)(?=^### |^## |\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group("body") if match else ""


def has_heading(text: str, heading: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(heading)}\s*$", text, flags=re.M))


def parse_table_lines(section_text: str) -> tuple[list[str], list[list[str]]]:
    lines = section_text.splitlines()
    headers: list[str] = []
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if headers and rows:
                break
            continue
        if "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if not headers:
            headers = cells
            continue
        rows.append(cells)
    return headers, rows


def expanded_issue_numbers(value: str) -> set[str]:
    issues = set(re.findall(r"#\d+", value))
    for start_text, end_text in re.findall(r"#(\d+)`?\s+(?:through|to)\s+`?#(\d+)", value):
        start = int(start_text)
        end = int(end_text)
        if start <= end and end - start <= 100:
            issues.update(f"#{number}" for number in range(start, end + 1))
    return issues


def non_negated_pattern_present(text: str, pattern: str) -> bool:
    for match in re.finditer(pattern, text, flags=re.I):
        prefix = text[max(0, match.start() - 64) : match.start()]
        if re.search(
            r"\b(?:there\s+(?:is|are)\s+)?"
            r"(?:no|not|never|neither|without)\s+(?:an?\s+)?$",
            prefix,
            re.I,
        ):
            continue
        return True
    return False


def yaml_inline_list_contains_token(value: str, token: str) -> bool:
    if "[" not in value or "]" not in value:
        return False
    start = value.find("[")
    end = value.rfind("]")
    if end <= start:
        return False
    list_body = value[start + 1 : end]
    for item in list_body.split(","):
        if item.strip().strip("\"'").lower() == token:
            return True
    return False


def workflow_has_pull_request_edited(yaml_text: str) -> bool:
    lines = yaml_text.splitlines()
    for index, line in enumerate(lines):
        on_match = re.match(r"^(?P<indent>\s*)on:\s*$", line)
        if not on_match or on_match.group("indent"):
            continue
        on_indent = 0
        i = index + 1
        direct_child_indent: int | None = None
        while i < len(lines):
            current = lines[i]
            if not current.strip() or current.lstrip().startswith("#"):
                i += 1
                continue
            current_indent = len(current) - len(current.lstrip(" "))
            if current_indent <= on_indent:
                break
            if direct_child_indent is None:
                direct_child_indent = current_indent
            if current_indent != direct_child_indent:
                i += 1
                continue
            pull_match = re.match(r"^(?P<indent>\s*)pull_request:\s*$", current)
            if not pull_match:
                i += 1
                continue
            pull_indent = len(pull_match.group("indent"))
            i += 1
            pull_child_indent: int | None = None
            while i < len(lines):
                current = yaml_line_without_inline_comment(lines[i])
                if not current.strip() or current.lstrip().startswith("#"):
                    i += 1
                    continue
                indent = len(current) - len(current.lstrip(" "))
                if indent <= pull_indent:
                    break
                if pull_child_indent is None:
                    pull_child_indent = indent
                if indent != pull_child_indent:
                    i += 1
                    continue
                types_match = re.match(r"^(?P<indent>\s*)types:\s*(?P<value>.*)$", current)
                if not types_match:
                    i += 1
                    continue
                types_indent = len(types_match.group("indent"))
                value = types_match.group("value").strip()
                if value:
                    if yaml_inline_list_contains_token(yaml_line_without_inline_comment(value), "edited"):
                        return True
                    i += 1
                    continue
                i += 1
                while i < len(lines):
                    item = yaml_line_without_inline_comment(lines[i])
                    if not item.strip() or item.lstrip().startswith("#"):
                        i += 1
                        continue
                    item_indent = len(item) - len(item.lstrip(" "))
                    if item_indent <= types_indent:
                        break
                    item_value_match = re.match(r"^\s*-\s*(?P<value>[A-Za-z0-9_-]+)\s*$", item)
                    if item_value_match and item_value_match.group("value").lower() == "edited":
                        return True
                    i += 1
                continue
            continue

    return False


def guardrail_workflow_paths() -> list[str]:
    workflow_dir = ROOT / ".github" / "workflows"
    paths = sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")])
    return [
        path.relative_to(ROOT).as_posix()
        for path in paths
        if "scripts/guardrails_check.py" in read(path.relative_to(ROOT).as_posix())
    ]


def workflow_has_guardrail_github_token_wiring(yaml_text: str) -> bool:
    guardrail_steps = workflow_guardrail_step_blocks(yaml_text)
    if not guardrail_steps:
        return False
    return (
        workflow_has_permission(yaml_text, "issues", "read")
        and workflow_has_permission(yaml_text, "pull-requests", "read")
        and all(workflow_step_has_guardrail_github_token_env(step) for step in guardrail_steps)
    )


def workflow_step_has_guardrail_github_token_env(step: str) -> bool:
    token_env = re.compile(
        r"^\s*GITHUB_TOKEN:\s*['\"]?\$\{\{\s*(?:github\.token|secrets\.GITHUB_TOKEN)\s*\}\}['\"]?\s*$"
    )
    return any(token_env.fullmatch(yaml_line_without_inline_comment(line)) for line in step.splitlines())


def workflow_has_permission(yaml_text: str, permission: str, value: str) -> bool:
    expected = f"{permission}: {value}"
    lines = yaml_text.splitlines()
    for index, raw_line in enumerate(lines):
        line = yaml_line_without_inline_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if line.strip() != "permissions:":
            continue
        child_indent: int | None = None
        for child_raw in lines[index + 1 :]:
            child = yaml_line_without_inline_comment(child_raw)
            if not child.strip():
                continue
            child_current_indent = len(child) - len(child.lstrip(" "))
            if child_current_indent <= indent:
                break
            if child_indent is None:
                child_indent = child_current_indent
            if child_current_indent == child_indent and child.strip() == expected:
                return True
    return False


def workflow_has_stage_quality_base_sha(yaml_text: str) -> bool:
    return any(
        "run: make quality" in step and "GITHUB_BASE_SHA:" in step and "GITHUB_EVENT_NAME:" in step
        for step in workflow_step_blocks(yaml_text)
    )


def workflow_allows_phase1_pull_request_bases(yaml_text: str) -> bool:
    in_on_block = False
    on_child_indent: int | None = None
    pull_request_indent: int | None = None
    branches_indent: int | None = None
    for raw_line in yaml_text.splitlines():
        without_comment = yaml_line_without_inline_comment(raw_line)
        if not without_comment.strip():
            continue
        indent = len(without_comment) - len(without_comment.lstrip(" "))
        stripped = without_comment.strip()
        if indent == 0:
            in_on_block = stripped == "on:"
            on_child_indent = None
            pull_request_indent = None
            branches_indent = None
            continue
        if not in_on_block:
            continue
        if on_child_indent is None:
            on_child_indent = indent
        if pull_request_indent is None:
            if indent == on_child_indent and stripped == "pull_request:":
                pull_request_indent = indent
            continue
        if indent <= pull_request_indent:
            pull_request_indent = indent if stripped == "pull_request:" else None
            branches_indent = None
            continue
        if branches_indent is None:
            if indent == pull_request_indent + 2 and stripped.startswith("branches:"):
                branches_indent = indent
                inline_branches = stripped.removeprefix("branches:").strip()
                if workflow_branch_tokens_include_phase1(inline_branches):
                    return True
            continue
        if indent <= branches_indent:
            branches_indent = None
            if indent == pull_request_indent + 2 and stripped.startswith("branches:"):
                branches_indent = indent
                inline_branches = stripped.removeprefix("branches:").strip()
                if workflow_branch_tokens_include_phase1(inline_branches):
                    return True
            continue
        if stripped.startswith("- ") and workflow_branch_tokens_include_phase1(stripped.removeprefix("- ").strip()):
            return True
    return False


def yaml_line_without_inline_comment(line: str) -> str:
    quote: str | None = None
    for index, char in enumerate(line):
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        if char == "#" and quote is None:
            return line[:index].rstrip()
    return line.rstrip()


def workflow_branch_tokens_include_phase1(branches: str) -> bool:
    if not branches:
        return False
    normalized = branches.strip()
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    tokens = [token.strip().strip("'\"") for token in normalized.split(",")]
    return "phase-1-closure-**" in tokens


def workflow_guardrail_step_blocks(yaml_text: str) -> list[str]:
    return [
        step
        for step in workflow_step_blocks(yaml_text)
        if "scripts/guardrails_check.py" in step
    ]


def workflow_step_blocks(yaml_text: str) -> list[str]:
    lines = yaml_text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        step_match = re.match(r"^(?P<indent>\s*)-\s+name:\s+.*$", line)
        if not step_match:
            index += 1
            continue
        step_indent = len(step_match.group("indent"))
        block_lines = [yaml_line_without_inline_comment(line)]
        index += 1
        while index < len(lines):
            current = lines[index]
            if current.strip() and not current.lstrip().startswith("#"):
                current_indent = len(current) - len(current.lstrip(" "))
                if current_indent <= step_indent:
                    break
            block_lines.append(yaml_line_without_inline_comment(current))
            index += 1
        block = "\n".join(line for line in block_lines if line.strip())
        blocks.append(block)
    return blocks


def check_required_headings(failures: list[str], text: str, owner: str, headings: tuple[str, ...]) -> None:
    for heading in headings:
        if not has_heading(text, heading):
            failures.append(f"{owner} missing required heading: {heading}")


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def section_contains_required_commands(section_text: str, required: tuple[str, ...]) -> list[str]:
    normalized = section_text.lower()
    return [command for command in required if command.lower() not in normalized]


def check_preflight_table_columns(
    failures: list[str], *, section_name: str, section_text: str, required_headers: tuple[str, ...]
) -> None:
    headers, _ = parse_table_lines(section_text)
    if not headers:
        failures.append(f"{section_name} section in .github/pull_request_template.md is missing a table header row.")
        return
    normalized_headers = {normalize_header(header) for header in headers}
    missing = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing:
        failures.append(
            f"{section_name} table in .github/pull_request_template.md is missing headers: {', '.join(missing)}"
        )


def check_matrix_template_rows(
    failures: list[str],
    *,
    section_name: str,
    section_text: str,
    required_keyword_groups: tuple[tuple[str, ...], ...],
) -> None:
    headers, rows = parse_table_lines(section_text)
    normalized_headers = [normalize_header(header) for header in headers]
    required_headers = (
        "id",
        "area",
        "invariant",
        "old failure / false-pass risk",
        "positive test",
        "negative / mutation test",
        "status",
    )
    missing_headers = [header for header in required_headers if header not in normalized_headers]
    if missing_headers:
        failures.append(f"{section_name} matrix template missing headers: {', '.join(missing_headers)}")
        return

    index_by_header = {header: normalized_headers.index(header) for header in required_headers}
    seen_ids: set[str] = set()
    for row in rows:
        if len(row) < len(headers):
            failures.append(f"{section_name} matrix row has too few columns: {row}")
            continue
        row_id = row[index_by_header["id"]].strip("` ")
        positive_test = row[index_by_header["positive test"]].strip()
        negative_test = row[index_by_header["negative / mutation test"]].strip()
        status = row[index_by_header["status"]].strip("` ").lower()
        row_text = " ".join(row).lower()
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}", row_id):
            failures.append(f"{section_name} matrix row has non-concrete ID: {row_id}")
        if row_id in seen_ids:
            failures.append(f"{section_name} matrix row duplicates ID: {row_id}")
        seen_ids.add(row_id)
        if status != "pass":
            failures.append(f"{section_name} matrix row {row_id} must use status pass, not {status or '<empty>'}.")
        if re.search(r"\b(?:through|thru|to)\b|\.{2,}|[–—]", row_id, flags=re.I):
            failures.append(f"{section_name} matrix row {row_id} uses range or placeholder ID syntax.")
        if row_id.startswith("HUMAN-"):
            continue
        if "test_" not in positive_test.lower() and "make test" not in positive_test.lower():
            failures.append(f"{section_name} matrix row {row_id} must name positive test evidence.")
        if "test_" not in negative_test.lower() and "make test" not in negative_test.lower():
            failures.append(f"{section_name} matrix row {row_id} must name negative test evidence.")
        if "test_" not in row_text and "make test" not in row_text:
            failures.append(f"{section_name} matrix row {row_id} must name test evidence.")
        if not any(
            term in row_text
            for term in ("break-test", "mutation", "old behavior failed", "old-behavior proof", "fails-before")
        ):
            failures.append(f"{section_name} matrix row {row_id} must name old-behavior or mutation proof.")

    for keywords in required_keyword_groups:
        if not any(all(keyword in " ".join(row).lower() for keyword in keywords) for row in rows):
            failures.append(
                f"{section_name} matrix template missing one row with required binding terms: {', '.join(keywords)}"
            )


def check_process_hardening_findings(failures: list[str], text: str) -> None:
    remaining_headers, remaining_rows = parse_table_lines(section(text, "Medium/Low PHF Follow-up Matrix (Remaining)"))
    required_remaining_headers = (
        "item",
        "risk",
        "failure mode",
        "prior review evidence",
        "owning doc / script / template",
        "automated test / guardrail",
        "human-only surface (if not automatable)",
        "residual risk",
    )
    normalized_remaining_headers = [normalize_header(header) for header in remaining_headers]
    missing_remaining_headers = [
        header for header in required_remaining_headers if header not in normalized_remaining_headers
    ]
    if missing_remaining_headers:
        failures.append(
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md Medium/Low matrix missing headers: "
            + ", ".join(missing_remaining_headers)
        )
        return

    remaining_index = {header: normalized_remaining_headers.index(header) for header in required_remaining_headers}
    seen_remaining: set[str] = set()
    for row in remaining_rows:
        if len(row) < len(remaining_headers):
            failures.append(f"PHF Medium/Low matrix row has too few columns: {row}")
            continue
        item = row[remaining_index["item"]].strip("` ")
        seen_remaining.add(item)
        automated = row[remaining_index["automated test / guardrail"]]
        human_only = row[remaining_index["human-only surface (if not automatable)"]]
        residual = row[remaining_index["residual risk"]]
        for field_name, value in (
            ("failure mode", row[remaining_index["failure mode"]]),
            ("prior review evidence", row[remaining_index["prior review evidence"]]),
            ("owning doc / script / template", row[remaining_index["owning doc / script / template"]]),
            ("automated test / guardrail", automated),
            ("residual risk", residual),
        ):
            if value.strip().lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"{item} Medium/Low matrix has placeholder {field_name}.")
        if human_only.strip().lower() in {"", "todo", "tbd", "pending"}:
            failures.append(f"{item} Medium/Low matrix has placeholder human-only surface.")
        human_only_is_na = human_only.strip().lower() in {"n/a", "na"}
        evidence_failures = phf_automated_evidence_failures(item, automated)
        if human_only_is_na:
            failures.extend(evidence_failures)
        else:
            failures.extend(
                failure
                for failure in evidence_failures
                if "must map to an automated test/guardrail or human-only surface" not in failure
            )

    missing_remaining = sorted(REQUIRED_MEDIUM_LOW_PHF_ITEMS - seen_remaining)
    if missing_remaining:
        failures.append("Medium/Low PHF matrix missing items: " + ", ".join(missing_remaining))

    register_headers, register_rows = parse_table_lines(section(text, "Findings Register"))
    normalized_register_headers = [normalize_header(header) for header in register_headers]
    required_register_headers = ("id", "severity", "status", "acceptance criteria")
    missing_register_headers = [
        header for header in required_register_headers if header not in normalized_register_headers
    ]
    if missing_register_headers:
        failures.append(
            "docs/reviews/PROCESS_HARDENING_FINDINGS.md Findings Register missing headers: "
            + ", ".join(missing_register_headers)
        )
        return
    register_index = {header: normalized_register_headers.index(header) for header in required_register_headers}
    seen_register: set[str] = set()
    for row in register_rows:
        if len(row) < len(register_headers):
            failures.append(f"PHF findings register row has too few columns: {row}")
            continue
        item = row[register_index["id"]].strip("` ")
        if item in seen_register:
            failures.append(f"PHF findings register duplicates item: {item}")
        seen_register.add(item)
        if item in REQUIRED_MEDIUM_LOW_PHF_ITEMS:
            status = row[register_index["status"]].strip().lower()
            acceptance = row[register_index["acceptance criteria"]].strip()
            if status not in PHF_CLOSED_STATUSES:
                failures.append(f"{item} must be closed or superseded in the findings register; got {status}.")
            if acceptance.lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"{item} findings register has placeholder acceptance criteria.")


def check_issue39_closure_plan(failures: list[str]) -> None:
    rel = "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
    path = ROOT / rel
    if not path.is_file():
        failures.append(f"Missing required issue #39 production closure plan: {rel}")
        return

    headers, rows = parse_table_lines(section(read(rel), "Master Evidence Matrix"))
    required_headers = ("ID", "Requirement", "Evidence target", "Owner", "Minimum evidence contract", "Status")
    normalized_headers = [normalize_header(header) for header in headers]
    missing_headers = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing_headers:
        failures.append(
            "Issue #39 production closure plan Master Evidence Matrix missing headers: "
            + ", ".join(missing_headers)
        )
        return

    seen_ids: set[str] = set()
    closed_ids: set[str] = set()
    for row in rows:
        if len(row) != len(headers):
            failures.append(f"Issue #39 matrix row must have 6 columns: {row}")
            continue
        row_id = row[normalized_headers.index("id")].strip("` ")
        status = row[normalized_headers.index("status")].strip("` ")
        if row_id in seen_ids:
            failures.append(f"Issue #39 production closure plan duplicates matrix ID: {row_id}")
        seen_ids.add(row_id)
        if not re.fullmatch(r"[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}", row_id):
            failures.append(f"Issue #39 matrix row has invalid ID: {row_id}")
        if status.lower() not in VALID_ISSUE_39_MATRIX_STATUSES:
            failures.append(f"Issue #39 matrix row {row_id} status must be Open or Closed; got {status}.")
        if status.lower() == "closed":
            closed_ids.add(row_id)
        for value in row[1:5]:
            if value.strip().lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"Issue #39 matrix row {row_id} has placeholder evidence contract content.")
                break
        required_terms = ISSUE_39_SENSITIVE_ROW_REQUIRED_TERMS.get(row_id, ())
        row_contract = " ".join(row[1:5]).lower()
        missing_terms = [term for term in required_terms if term.lower() not in row_contract]
        if missing_terms:
            failures.append(
                f"Issue #39 matrix row {row_id} missing required contract terms: "
                + ", ".join(missing_terms)
            )

    missing_ids = sorted(REQUIRED_ISSUE_39_MATRIX_IDS - seen_ids)
    if missing_ids:
        failures.append("Issue #39 production closure plan missing matrix IDs: " + ", ".join(missing_ids))

    unexpected_ids = sorted(seen_ids - REQUIRED_ISSUE_39_MATRIX_IDS)
    if unexpected_ids:
        failures.append("Issue #39 production closure plan has unexpected matrix IDs: " + ", ".join(unexpected_ids))

    if closed_ids:
        check_issue39_closed_row_records(failures, read(rel), closed_ids)


def check_issue125_local_restore_contract(failures: list[str]) -> None:
    rel = "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"
    text = read(rel)
    normalized_text = re.sub(r"\s+", " ", text)
    required_markers = (
        "### Issue `#125` local restore-integrity drill status and evidence mapping",
        "Matrix status remains exactly `Open` for `DUR-RESTORE-001`.",
        "Issue `#125` is an executable local-only evidence slice",
        "does not satisfy the production `CH-14` closure bar",
        "must not be represented as production backup/restore evidence",
        "`CTX4-LOCAL-RESTORE-EVID-001`",
        "persists inspectable evidence paths",
        "Production backup platform evidence, restore metrics, RTO/RPO proof, retention/re-delete behavior, and operational signoff remain open.",
    )
    missing_markers = [marker for marker in required_markers if marker not in normalized_text]
    if missing_markers:
        failures.append(
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md missing issue #125 restore markers: "
            + ", ".join(missing_markers)
        )


def check_issue141_structural_contract(failures: list[str], adr_text: str) -> None:
    stage_section = subsection(adr_text, "Durable-state ownership for Stages 4, 6, and 7")
    stage_headers, stage_rows = parse_table_lines(stage_section)
    if [normalize_header(header) for header in stage_headers] != [
        "stage",
        "authoritative durable state",
        "deliberately excluded from recovery scope",
    ]:
        failures.append("ADR 0027 durable-state ownership table headers are malformed.")
    stage_rows_by_id: dict[str, list[str]] = {}
    duplicate_stages: set[str] = set()
    for row in stage_rows:
        if len(row) != len(stage_headers):
            continue
        stage_id = row[0].strip()
        if stage_id in stage_rows_by_id:
            duplicate_stages.add(stage_id)
        stage_rows_by_id[stage_id] = row
    expected_stages = set(ISSUE_141_EXPECTED_STAGE_ROWS)
    actual_stages = set(stage_rows_by_id)
    if actual_stages != expected_stages or duplicate_stages:
        failures.append(
            "ADR 0027 durable-state ownership rows must be exactly Stage 4, Stage 6, Stage 7; "
            f"missing {', '.join(sorted(expected_stages - actual_stages)) or 'none'}; "
            f"unexpected {', '.join(sorted(actual_stages - expected_stages)) or 'none'}; "
            f"duplicates {', '.join(sorted(duplicate_stages)) or 'none'}."
        )
    for stage_id, required_terms in ISSUE_141_EXPECTED_STAGE_ROWS.items():
        stage_row = stage_rows_by_id.get(stage_id)
        if not stage_row:
            continue
        row_text = " ".join(stage_row[1:])
        missing_terms = [term for term in required_terms if term not in row_text]
        if missing_terms:
            failures.append(
                f"ADR 0027 {stage_id} durable-state ownership row missing: " + ", ".join(missing_terms)
            )

    child_section = subsection(adr_text, "Dependencies and acceptance for issues #142-#149")
    child_headers, child_rows = parse_table_lines(child_section)
    if [normalize_header(header) for header in child_headers] != [
        "issue",
        "dependencies",
        "acceptance owned by that issue",
    ]:
        failures.append("ADR 0027 child acceptance table headers are malformed.")
    child_rows_by_id: dict[str, list[str]] = {}
    duplicate_children: set[str] = set()
    for row in child_rows:
        if len(row) != len(child_headers):
            continue
        issue_match = re.search(r"#\d+", row[0])
        if not issue_match:
            continue
        issue_id = issue_match.group(0)
        if issue_id in child_rows_by_id:
            duplicate_children.add(issue_id)
        child_rows_by_id[issue_id] = row
    expected_children = set(ISSUE_141_EXPECTED_CHILD_DEPENDENCIES)
    actual_children = set(child_rows_by_id)
    if actual_children != expected_children or duplicate_children:
        failures.append(
            "ADR 0027 child acceptance rows must be exactly #142 through #149; "
            f"missing {', '.join(sorted(expected_children - actual_children)) or 'none'}; "
            f"unexpected {', '.join(sorted(actual_children - expected_children)) or 'none'}; "
            f"duplicates {', '.join(sorted(duplicate_children)) or 'none'}."
        )
    for issue_id, expected_dependencies in ISSUE_141_EXPECTED_CHILD_DEPENDENCIES.items():
        child_row = child_rows_by_id.get(issue_id)
        if not child_row:
            continue
        actual_dependencies = expanded_issue_numbers(child_row[1])
        if re.search(r"\b(?:no|not|never|without|except|optional)\b", child_row[1], flags=re.I):
            failures.append(f"ADR 0027 {issue_id} dependency statement must be affirmative.")
        if actual_dependencies != expected_dependencies:
            failures.append(
                f"ADR 0027 {issue_id} dependencies must be "
                f"{', '.join(sorted(expected_dependencies))}; got "
                f"{', '.join(sorted(actual_dependencies)) or 'none'}."
            )
        missing_terms = [
            term for term in ISSUE_141_CHILD_ACCEPTANCE_TERMS[issue_id] if term not in child_row[2]
        ]
        if missing_terms:
            failures.append(
                f"ADR 0027 {issue_id} acceptance contract missing: " + ", ".join(missing_terms)
            )

    journal_section = re.sub(r"\s+", " ", subsection(adr_text, "Backup mechanism and artifact catalog"))
    journal_terms = (
        "unique write-once key",
        "monotonic outbox sequence",
        "previous-event digest",
        "event checksum",
        "policy version",
        "deletion time",
        "opaque entity/object identities",
        "confirmed S3 Version ID",
        "last contiguous, version-verified sequence",
        "signed/versioned manifest",
        "delete marker",
        "fails closed",
    )
    missing_journal_terms = [term for term in journal_terms if term not in journal_section]
    if missing_journal_terms:
        failures.append(
            "ADR 0027 deletion-journal integrity fields missing: " + ", ".join(missing_journal_terms)
        )


def check_issue141_detailed_controls(failures: list[str], adr_text: str) -> None:
    normalized_sections = {
        heading: re.sub(r"\s+", " ", subsection(adr_text, heading))
        for heading in (
            "Environment, account, and region boundaries",
            "Backup mechanism and artifact catalog",
            "Access control and secrets",
            "Retention, encryption, and integrity",
            "RTO/RPO ownership and measurement",
            "Dependencies and acceptance for issues #142-#149",
        )
    }
    security_terms_by_section = {
        "Backup mechanism and artifact catalog": (
            "writer has create- only permissions and cannot overwrite",
            "every use is alerted, dated, and reviewed",
            "Control-key disablement/deletion safeguards and alarms are mandatory",
            "Reviewer exports use a field allowlist",
            "separate read roles and access audit",
            "dedicated Security-owned manifest-signing principal",
            "separate asymmetric KMS signing key",
            "no journal-write, reconciliation, retention-bypass, or catalog-mutation permission",
            "journal writer and reconciler cannot sign",
            "pins the signing-key ARN, algorithm, manifest policy version and prior signed watermark",
            "missing, invalid, unexpected-key, or rolled-back signature fails closed",
        ),
        "Access control and secrets": (
            ".github/workflows/durability-deploy.yml@refs/heads/main",
            "id-token: write",
            "aud=sts.amazonaws.com",
            "repo:imrohitagrawal/narratwin-ai:environment:production-like-durability",
            "refs/pull/*/merge",
            "prevents self-review",
            "disallows administrator bypass",
            "no larger than `5,000,000,000 bytes`",
            "`s3:GetObjectVersion`",
            "kms:Decrypt",
            "`s3:PutObject`",
            "s3:PutObjectTagging",
            "fixed run/deadline tag set",
            "kms:GenerateDataKey",
            "internet/NAT, source-VPC, application, provider, or production connectivity",
            "private AWS endpoints are the only egress",
            "separate target-cleanup role may remove deletion protection",
            "`rds:DescribeDBInstances`",
            "`rds:ModifyDBInstance`",
            "`rds:DeleteDBInstance`",
            "`rds:DescribeDBSnapshots`",
            "`rds:DescribeDBInstanceAutomatedBackups`",
            "`rds:DeleteDBSnapshot`",
            "`rds:DeleteDBInstanceAutomatedBackup`",
            "run-tagged target ARN",
            "run-tagged orphan",
            "restore bucket/run prefix",
            "`s3:ListBucketVersions`",
            "`s3:GetObjectVersionTagging`",
            "`s3:DeleteObjectVersion`",
            "cannot put/read object content, change tags, bypass retention",
            "source/control bucket and KMS ARN denies apply independently of tags",
        ),
    }
    missing_security: list[str] = []
    for heading, terms in security_terms_by_section.items():
        section_text = normalized_sections[heading]
        missing_security.extend(f"{heading}: {term}" for term in terms if term not in section_text)
    if missing_security:
        failures.append("ADR 0027 detailed security controls missing: " + ", ".join(missing_security))

    operational_terms_by_section = {
        "Environment, account, and region boundaries": (
            "PITR API has no `EngineVersion` input",
            "PubliclyAccessible=false",
            "EnableIAMDatabaseAuthentication=true",
            "rather than accepting service defaults",
            "After creation, platform APIs must prove engine version `17.10`",
        ),
        "Retention, encryption, and integrity": (
            "cleanup_due_utc` before the create request",
            "Automatically tear down the target/delete copied versions within 24 hours",
            "SkipFinalSnapshot=true",
            "DeleteAutomatedBackups=true",
            "tag-based live-inventory discovery",
            "both catalog and live inventory prove cleanup",
        ),
        "RTO/RPO ownership and measurement": (
            "only after DB availability, migration compatibility, database integrity",
            "live API proof of Multi-AZ",
            "IAM database authentication",
            "no-traffic isolation pass",
            "reviewed holdpoint and before any recovery action",
            "version-writes and checksum-verifies that immutable source cutoff",
            "moving post-start source query",
        ),
        "Dependencies and acceptance for issues #142-#149": (
            "alert routing owned by CH-12",
            "no service defaults",
            "SkipFinalSnapshot=true",
            "next-exercise live-inventory block",
        ),
    }
    missing_operational: list[str] = []
    for heading, terms in operational_terms_by_section.items():
        section_text = normalized_sections[heading]
        missing_operational.extend(f"{heading}: {term}" for term in terms if term not in section_text)
    if missing_operational:
        failures.append(
            "ADR 0027 detailed operational controls missing: " + ", ".join(missing_operational)
        )

    threat_headers, threat_rows = parse_table_lines(section(read("docs/THREAT_MODEL.md"), "STRIDE Analysis"))
    threat_rows_by_boundary = {
        row[0]: row for row in threat_rows if len(row) == len(threat_headers) and row
    }
    required_threat_terms = {
        "Versioned S3 artifact path": ("Version-ID substitution", "delete marker", "protected source versions"),
        "Security-control journal path": ("high-watermark rollback", "retention bypass", "journal/KMS/manifest unavailable"),
    }
    missing_threat: list[str] = []
    for boundary, terms in required_threat_terms.items():
        row = threat_rows_by_boundary.get(boundary)
        if not row:
            missing_threat.append(boundary)
            continue
        row_text = " ".join(row[1:])
        missing_threat.extend(f"{boundary}: {term}" for term in terms if term not in row_text)
    if missing_threat:
        failures.append("Threat model S3/journal STRIDE rows missing: " + ", ".join(missing_threat))


def check_issue141_launch_level_contract(failures: list[str]) -> None:
    launch_rel = "docs/LAUNCH_LEVELS.md"
    headers, rows = parse_table_lines(section(read(launch_rel), "Launch-level boundary"))
    expected_headers = [
        "Level",
        "Audience and data",
        "Permitted infrastructure",
        "AWS requirement under ADR 0027",
        "Current posture",
        "Claim boundary",
    ]
    if headers != expected_headers:
        failures.append(
            f"{launch_rel} launch-level boundary headers must be: " + ", ".join(expected_headers)
        )
        return

    malformed_rows = [row for row in rows if len(row) != len(headers)]
    if malformed_rows:
        failures.append(f"{launch_rel} launch-level boundary contains malformed rows")

    valid_rows = [row for row in rows if len(row) == len(headers)]
    levels = [row[0] for row in valid_rows]
    duplicate_levels = sorted({level for level in levels if levels.count(level) > 1})
    if duplicate_levels:
        failures.append(
            f"{launch_rel} launch-level boundary contains duplicate rows: "
            + ", ".join(duplicate_levels)
        )

    rows_by_level = {row[0]: row for row in valid_rows}
    unexpected_levels = sorted(set(rows_by_level) - set(ISSUE_141_EXPECTED_LAUNCH_LEVEL_ROWS))
    if unexpected_levels:
        failures.append(
            f"{launch_rel} launch-level boundary contains unexpected rows: "
            + ", ".join(unexpected_levels)
        )
    missing_levels = sorted(set(ISSUE_141_EXPECTED_LAUNCH_LEVEL_ROWS) - set(rows_by_level))
    if missing_levels:
        failures.append(f"{launch_rel} launch-level boundary rows missing: " + ", ".join(missing_levels))

    for level, expected_cells in ISSUE_141_EXPECTED_LAUNCH_LEVEL_ROWS.items():
        row = rows_by_level.get(level)
        if not row:
            continue
        for column_name, actual, expected in zip(headers[1:], row[1:], expected_cells, strict=True):
            if actual == expected:
                continue
            failures.append(
                f"{launch_rel} {level} {column_name} must equal: {expected}"
            )


def check_issue141_platform_ownership_contract(failures: list[str]) -> None:
    adr_rel = "docs/ADR/0027-production-like-durability-platform-ownership.md"
    adr_text = read(adr_rel)
    check_issue141_structural_contract(failures, adr_text)
    check_issue141_detailed_controls(failures, adr_text)
    check_issue141_launch_level_contract(failures)
    required_markers_by_file = {
        adr_rel: (
            "Amazon RDS for PostgreSQL `17.10`, Multi-AZ DB instance deployment",
            "AWS region `ap-south-1` (Mumbai)",
            "dedicated non-production AWS account",
            "Same non-production account and region",
            "point-in-time API has no target storage `KmsKeyId` parameter",
            "storage KMS ARN is inherited",
            "Amazon S3 general-purpose buckets with Versioning are authoritative",
            "source, restore-validation, and security-control S3 buckets",
            "S3 recovery uses Versioning",
            "unique write-once key",
            "last contiguous, version-verified sequence",
            "signed/versioned manifest",
            "is not rolled back with RDS PITR",
            "Platform/Storage owner is accountable for backup configuration",
            "Operations is accountable for measured RTO",
            "Platform/Storage is accountable for measured RPO",
            "RTO `<= 75 minutes` and RPO `<= 5 minutes`",
            "CH-14 owns backup configuration, catalog lifecycle, restore-target TTL",
            "CH-21 owns data-class erasure policy",
            "negative delta, target-ahead sequence, clock ambiguity, cutoff mismatch, or manifest mismatch invalidates the evidence",
            "No target DB exists before the later drill",
            "repo:imrohitagrawal/narratwin-ai:environment:production-like-durability",
            "restricted operational catalog",
            "Reviewer exports use a field allowlist",
            "issue `#149` reviews only environment, tooling, calculation-test, and reviewer-handoff readiness",
            "Issues `#142` through `#149`",
            "No environment, backup, target, or restore evidence exists",
            "issue `#126`, close matrix row `DUR-RESTORE-001`, or close issue `#39`",
            "AWS is not required for local development or the controlled local mock demo",
            "docs/LAUNCH_LEVELS.md",
        ),
        "docs/LAUNCH_LEVELS.md": (
            "Status: Merged documentation baseline through PR `#153` at `2fb5569`",
            "ADR `0027` selects AWS for the production-like durability evidence and eventual production paths",
            "An AWS account is not required for local development or the controlled local mock demo.",
            "A free or low-cost resource does not, by price alone, prove security, durability, privacy, or operational readiness.",
            "External users or customer data make this production-adjacent regardless of the words `demo`, `beta`, or `soft launch`.",
            "Internal workforce authentication and minimum identity/access audit metadata do not alone promote an otherwise qualifying hosted internal synthetic demo to soft launch.",
            "Real provider credentials do not alone change the audience tier",
            "a different provider requires a reviewed ADR amendment",
            "issues `#142` through `#149`",
            "later issue `#126`",
            "No AWS spend or resource creation is authorized by issue `#141` or PR `#153`.",
            "This document creates no account, resource, backup, target, restore evidence, or launch authorization.",
        ),
        "docs/reviews/ISSUE_141_DURABILITY_PLATFORM_PREFLIGHT.md": (
            "`PLAT-DEC-001`",
            "`PLAT-SCOPE-001`",
            "`PLAT-BACKUP-001`",
            "`PLAT-ISOLATION-001`",
            "`PLAT-ACCESS-001`",
            "`PLAT-RETENTION-001`",
            "`PLAT-SLO-001`",
            "`PLAT-DEPS-001`",
            "`PLAT-OVERCLAIM-001`",
            "`HUMAN-PLAT-001` remains blocked",
            "No successful production-like durability or restore claim is permitted.",
            "deletion journal",
            "immutable source cutoff",
            "negative/mismatched deltas invalidate evidence",
            "REV141-JOURNAL-001",
        ),
        "docs/STAGE_ISSUE_PLAN.md": (
            "`phase-1-closure-141-*` is reserved for issue `#141`",
            "does not provision infrastructure, connect runtime code, configure backups",
            "issue `#126`, `DUR-RESTORE-001`, or issue `#39`",
        ),
        "docs/STATUS.md": (
            "| `#141` | Open, architecture recorded; human approvals blocked |",
            "Documentation baseline merged through PR `#153` at `2fb5569`.",
            "| `#142` | Open, depends on `#141` |",
            "| `#149` | Open, depends on `#130`, `#141`-`#148` |",
            "| `#126` | Open |",
            "No environment, backup/version source, restore target, or restore evidence has been verified.",
            "versioned S3 artifact/control buckets",
            "separately signed contiguous deletion journal",
            "at least 15-day S3 version retention",
            "AWS is not required for local development or the controlled local mock demo",
            "docs/LAUNCH_LEVELS.md",
        ),
        "docs/TRACEABILITY.md": (
            "Issue `#141` production-like durability platform and ownership contract",
            "Merged at `2fb5569`; external approvals blocked",
            "launch-level boundary",
            "docs/LAUNCH_LEVELS.md",
        ),
        "docs/RELEASE_READINESS_REVIEW.md": (
            "docs/LAUNCH_LEVELS.md",
            "External/invite-only soft launch remains No-Go",
            "AWS is not required for the controlled local mock demo",
        ),
        "docs/demo/PHASE_1_DEMO_CHECKLIST.md": (
            "docs/LAUNCH_LEVELS.md",
            "An AWS account is not required",
            "Hosted or external access requires a separate launch-level decision",
        ),
        "docs/THREAT_MODEL.md": (
            "### A8: Source/Restore Target Confusion",
            "### A9: Backup, Catalog, or Restore Evidence Exfiltration",
            "### A10: S3 Artifact Version Substitution Or Publication Split-Brain",
            "### A11: Deletion Journal Suppression, Reordering, Or Rollback",
            "Same-account isolation has not been approved or deployed.",
            "shared account/key blast radius is an explicit residual",
            "versioned/Object-Locked control-bucket journal outside RDS PITR",
            "No platform, backup, target, RTO/RPO, or restore result is evidenced",
        ),
        "docs/THIRD_PARTY_NOTICES.md": (
            "Amazon Web Services durability control plane",
            "Proposed by issue `#141`; disabled/not provisioned",
            "No account, resource, credential, backup, object, target, or restore evidence exists.",
        ),
        "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md": (
            "environment readiness issues `#141`-`#149`",
            "CH-21 owns erasure behavior proof",
            "proof that restored deleted records are re-deleted",
            "last-contiguous, integrity-verified current independent deletion journal",
            "`CH-02`, `CH-14`, `CH-16`, `CH-17`, `CH-18`",
        ),
        "docs/ADR/0008-postgresql-durability-schema-boundary.md": (
            "ADR `0027` supersedes this ADR's provider-neutral platform boundary",
            "No shared database or verified production-like durability is present.",
        ),
        "docs/ADR/0011-context4-backup-restore-drill.md": (
            "ADR `0027` specializes this advisory plan",
            "RDS automated backups/PITR plus S3 Versioning",
            "last-contiguous, integrity-linked control-bucket deletion journal",
            "CH-14 owns backup/catalog/restore-target lifecycle",
            "CH-21 owns erasure enforcement",
            "RTO `<= 75 minutes` and RPO `<= 5 minutes` remain unmeasured planning targets.",
        ),
    }
    for rel, required_markers in required_markers_by_file.items():
        normalized_text = re.sub(r"\s+", " ", read(rel))
        missing_markers = [marker for marker in required_markers if marker not in normalized_text]
        if missing_markers:
            failures.append(f"{rel} missing issue #141 markers: " + ", ".join(missing_markers))

    stale_lifecycle_status_by_file = {
        "docs/LAUNCH_LEVELS.md": (
            "Status: Proposed clarification for issue `#141` and draft PR `#153`.",
        ),
        "docs/STATUS.md": (
            "Documentation baseline remains proposed on the feature branch.",
        ),
        "docs/TRACEABILITY.md": (
            "Proposed on branch; external approvals blocked",
        ),
    }
    for rel, stale_statuses in stale_lifecycle_status_by_file.items():
        normalized_text = re.sub(r"\s+", " ", read(rel)).casefold()
        present = [status for status in stale_statuses if status.casefold() in normalized_text]
        if present:
            failures.append(
                f"{rel} contains stale issue #141 lifecycle status: " + ", ".join(present)
            )

    forbidden_patterns = (
        r"\bazure sql\b[^.]{0,120}\bauthoritative production-like\b",
        r"\bsingle-zone\b[^.]{0,120}\bauthoritative production-like\b",
        r"\bpublicly accessible\b[^.]{0,120}\bauthoritative production-like\b",
        r"\bproduction-like durability (?:exists|is deployed|is verified|has been verified)\b",
        r"\b(?:managed\s+)?backup (?:is\s+|has\s+been\s+)?(?:created|available|queryable|verified)\b",
        r"\bbackup artifact exists\b",
        r"\b(?:recoverable\s+)?(?:snapshot|recovery point) (?:exists|is available|has been created)\b",
        r"\brds has been provisioned\b",
        r"\brestore (?:target is deployed|drill (?:succeeded|passed|completed))\b",
        r"\b(?:restoration|restore) (?:was|is|has been) (?:successful|completed|verified)\b",
        r"\b(?:observed|actual|measured) rto\s+(?:is\s+)?(?:\d|zero)\w*\b",
        r"\b(?:observed|actual|measured) rpo\s+(?:is|was)?\s*(?:\d|zero)\w*\b",
        r"\b(?:rto|rpo) target (?:was|is|has been) (?:met|achieved|satisfied)\b",
        r"\bplatform is approved by operations and security\b",
        r"\bgo for launch\b",
        r"\bapproved for launch\b",
        r"\bplatform/storage signed off\b",
        r"\b(?:operations(?:/security)?|security(?:/operations)?) (?:has\s+|have\s+)?approved\b",
        r"\b(?:all|required) signoffs? (?:was|were|is|are|has been|have been) (?:obtained|complete|completed|approved)\b",
        r"\bissue\s+`?#126`?\s+(?:is|has been)\s+(?:now\s+)?(?:closed|complete|resolved|satisfied)\b",
        r"\b(?:matrix row\s+)?`?dur-restore-001`?\s+(?:is|has been)\s+(?:now\s+)?(?:closed|complete|resolved|satisfied)\b",
        r"\bissue\s+`?#39`?\s+(?:is|has been)\s+(?:now\s+)?(?:closed|complete|resolved|satisfied)\b",
        r"\bissue\s+`?#139`?\s+(?:is|has been)\s+(?:now\s+)?(?:closed|complete|completed|resolved|satisfied)\b",
        r"\bissue\s+`?#141`?\s+(?:is|has been)\s+(?:now\s+)?(?:closed|complete|completed|resolved|satisfied)\b",
    )
    for rel in required_markers_by_file:
        normalized_text = re.sub(r"\s+", " ", read(rel)).lower()
        present = [
            pattern for pattern in forbidden_patterns if non_negated_pattern_present(normalized_text, pattern)
        ]
        if present:
            failures.append(f"{rel} contains issue #141 overclaim markers: " + ", ".join(present))


def check_issue126_restore_readiness_contract(failures: list[str]) -> None:
    required_markers_by_file = {
        "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md": (
            "### Issue `#126` CH-14 restore-readiness contract status and evidence mapping",
            "Matrix status remains exactly `Open` for `DUR-RESTORE-001`.",
            "Issue `#126` is a narrow repo-checked restore-readiness contract slice",
            "does not satisfy final `CH-14` restore-drill closure",
            "does not satisfy `CTX4-RESTORE-EVID-001`",
            "must not be represented as successful production backup/restore evidence or production restore readiness",
            "`CTX4-RESTORE-READINESS-EVID-001`",
            "enumerate the required human-only production drill surfaces",
            "Successful production restore execution, actual RTO/RPO proof, restore metrics export, retention/re-delete evidence, and operational signoff remain open.",
        ),
        "docs/ADR/0026-ch14-restore-readiness-contract.md": (
            "This slice establishes a repo-checked restore-readiness contract for issue `#126`.",
            "It does not close issue `#126` unless the live issue scope is formally updated to accept contract-only readiness evidence.",
            "if evidence is limited to local file-backed replay, local restore-adjacent load metrics, or advisory SLO text, the row stays `Open` and issue `#39` stays open.",
            "The repo cannot claim a successful production restore drill, production restore readiness, or closure of `DUR-RESTORE-001`.",
            "Issue `#39` remains open.",
        ),
        "docs/STAGE_ISSUE_PLAN.md": (
            "`phase-1-closure-39-ch-14-*` is reserved for issue `#126`, the narrow",
            "current repo-baselined `CH-10` and `CH-11`",
            "This branch does not execute a successful production restore drill.",
            "adds anti-overclaim guardrails.",
        ),
        "docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md": (
            "No successful production restore drill claim.",
            "No closure of issue `#39` or matrix row `DUR-RESTORE-001`.",
            "current repo-baselined restore-adjacent metrics/SLO contracts",
            "Any fresh finding that identifies a new overclaim path resets this slice to",
        ),
        "docs/reviews/ISSUE_125_LOCAL_RESTORE_PREFLIGHT.md": (
            "final `CH-14` `DUR-RESTORE-001` closure tied to successful restore-drill evidence; later issue `#126` may add only narrower readiness-contract guardrails until that final proof exists.",
        ),
        "docs/STATUS.md": (
            "| `#125` | Closed |",
            "| `#126` | Open |",
            "It does not claim successful production restore execution, final RTO/RPO proof, restore metrics export, operational signoff, or issue `#39` closure.",
        ),
    }
    for rel, required_markers in required_markers_by_file.items():
        normalized_text = re.sub(r"\s+", " ", read(rel))
        missing_markers = [marker for marker in required_markers if marker not in normalized_text]
        if missing_markers:
            failures.append(f"{rel} missing issue #126 restore markers: " + ", ".join(missing_markers))

    completed_status_terms = (
        r"closed|complete|completed|satisfied|fully satisfied|"
        r"resolved(?!\s+or\s+explicitly\s+downgraded)"
    )
    status_claim_prefix = r"(?:is\s+|has\s+been\s+)?(?:now\s+)?"
    issue_subject_prefix = r"(?<!for\s)(?<!on\s)\bissue\s+`?"
    production_drill_claim = (
        r"\b(?:successful\s+)?production restore drill\s+"
        r"(?:(?:was\s+|has\s+been\s+)?(?:successful|complete|completed|passed|succeeded|verified|proven))\b"
    )
    production_readiness_claim = (
        r"\bproduction restore readiness\s+"
        r"(?:(?:is\s+|has\s+been\s+)?(?:achieved|ready|complete|completed|passed|succeeded|verified|proven))\b"
    )
    production_restore_claim = (
        r"\bproduction restore\s+(?:(?:is\s+|has\s+been\s+)?(?:ready|verified|proven))\b"
    )
    dur_restore_claim = (
        r"\b(?:matrix row\s+)?dur-restore-001\s+" + status_claim_prefix + r"(?:" + completed_status_terms + r")\b"
    )
    issue_126_claim = issue_subject_prefix + r"#126`?\s+" + status_claim_prefix + r"(?:" + completed_status_terms + r")\b"
    issue_39_claim = issue_subject_prefix + r"#39`?\s+" + status_claim_prefix + r"(?:" + completed_status_terms + r")\b"
    forbidden_overclaims_by_file = {
        "docs/ADR/0026-ch14-restore-readiness-contract.md": (
            ("successful production restore drill complete", production_drill_claim),
            ("production restore readiness achieved", production_readiness_claim),
            ("production restore is ready", production_restore_claim),
            ("dur-restore-001 closed", dur_restore_claim),
            ("issue #126 closed or satisfied", issue_126_claim),
            ("issue #39 closed or resolved", issue_39_claim),
        ),
        "docs/reviews/ISSUE_126_CH14_RESTORE_READINESS_PREFLIGHT.md": (
            ("successful production restore drill complete", production_drill_claim),
            ("production restore readiness achieved", production_readiness_claim),
            ("production restore is ready", production_restore_claim),
            ("dur-restore-001 closed", dur_restore_claim),
            ("issue #39 closed or resolved", issue_39_claim),
        ),
        "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md": (
            ("successful production restore drill complete", production_drill_claim),
            ("production restore readiness achieved", production_readiness_claim),
            ("production restore is ready", production_restore_claim),
            ("dur-restore-001 closed", dur_restore_claim),
            ("issue #39 closed or resolved", issue_39_claim),
        ),
        "docs/STATUS.md": (
            ("successful production restore drill complete", production_drill_claim),
            ("production restore readiness achieved", production_readiness_claim),
            ("production restore is ready", production_restore_claim),
            ("dur-restore-001 closed", dur_restore_claim),
            ("issue #39 closed or resolved", issue_39_claim),
        ),
    }
    for rel, forbidden_patterns in forbidden_overclaims_by_file.items():
        normalized_text = re.sub(r"\s+", " ", read(rel)).lower()
        present_markers = [
            label for label, pattern in forbidden_patterns if re.search(pattern, normalized_text, flags=re.IGNORECASE)
        ]
        if present_markers:
            failures.append(f"{rel} contains issue #126 restore overclaim markers: " + ", ".join(present_markers))


def check_issue39_closed_row_records(failures: list[str], text: str, closed_ids: set[str]) -> None:
    headers, rows = parse_table_lines(section(text, "Row Closure Records"))
    normalized_headers = [normalize_header(header) for header in headers]
    required_headers = (
        "Matrix ID",
        "Child issue / PR",
        "Artifact reference",
        "Validation or human evidence",
        "Owner",
        "Reviewer",
        "Residual-risk decision",
        "Timestamp / merge commit",
        "Satisfies row because",
    )
    missing_headers = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing_headers:
        failures.append("Issue #39 Row Closure Records missing headers: " + ", ".join(missing_headers))
        return

    index = {header: normalized_headers.index(normalize_header(header)) for header in required_headers}
    records_by_id: dict[str, list[str]] = {}
    for row in rows:
        if len(row) != len(headers):
            failures.append(f"Issue #39 row closure record has wrong column count: {row}")
            continue
        row_id = row[index["Matrix ID"]].strip("` ")
        records_by_id[row_id] = row

    for row_id in sorted(closed_ids):
        record = records_by_id.get(row_id)
        if not record:
            failures.append(f"Issue #39 matrix row {row_id} is Closed without a row closure record.")
            continue
        for header in required_headers[1:]:
            value = record[index[header]].strip()
            if value.lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"Issue #39 closed row {row_id} has placeholder {header}.")
        child_reference = record[index["Child issue / PR"]]
        issue_numbers = same_repo_issue_numbers(child_reference)
        pr_numbers = same_repo_pr_numbers(child_reference)
        if not issue_numbers or not pr_numbers:
            failures.append(
                f"Issue #39 closed row {row_id} must cite concrete same-repository child issue and PR URLs."
            )
        if "39" in issue_numbers:
            failures.append(f"Issue #39 closed row {row_id} must cite a child issue distinct from #39.")
        planning_pr_numbers = sorted(pr_numbers & ISSUE_39_PLANNING_PR_NUMBERS, key=int)
        if planning_pr_numbers:
            failures.append(
                f"Issue #39 closed row {row_id} must not use planning PRs #64-#80 as final proof: "
                + ", ".join(f"#{number}" for number in planning_pr_numbers)
            )
        if "64" in pr_numbers:
            failures.append(f"Issue #39 closed row {row_id} must not use Context 0 PR #64 as final proof.")
        artifact = record[index["Artifact reference"]]
        evidence = record[index["Validation or human evidence"]]
        reason = record[index["Satisfies row because"]]
        combined_evidence = " ".join((artifact, evidence, reason)).lower()
        if "docs/reviews/issue_39_production_closure_plan.md" in artifact.lower() and not any(
            token in combined_evidence for token in ("test_", "actions/runs/", "drill log", "human-only")
        ):
            failures.append(
                f"Issue #39 closed row {row_id} must not use the production closure plan alone as final proof."
            )
        if not has_concrete_issue39_closure_evidence(
            row_id=row_id,
            evidence=evidence,
            owner=record[index["Owner"]],
            residual_risk=record[index["Residual-risk decision"]],
        ):
            failures.append(f"Issue #39 closed row {row_id} lacks concrete validation or human-only evidence.")
        missing_groups = missing_issue39_operational_evidence_terms(row_id, combined_evidence)
        if missing_groups:
            failures.append(
                f"Issue #39 closed row {row_id} missing operational closure evidence terms: "
                + "; ".join(" or ".join(group) for group in missing_groups)
            )


def same_repo_issue_numbers(text: str) -> set[str]:
    return set(
        re.findall(
            rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/issues/(\d+)\b",
            text,
            flags=re.I,
        )
    )


def same_repo_pr_numbers(text: str) -> set[str]:
    return set(
        re.findall(
            rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/pull/(\d+)\b",
            text,
            flags=re.I,
        )
    )


def has_concrete_issue39_closure_evidence(
    *, row_id: str, evidence: str, owner: str, residual_risk: str
) -> bool:
    normalized_evidence = evidence.lower()
    cited_tests = set(AUTOMATED_EVIDENCE_TEST.findall(normalized_evidence))
    valid_node_ids = valid_pytest_node_ids_in_text(normalized_evidence)
    if cited_tests and {test_name for _, test_name in valid_node_ids} != cited_tests:
        return False
    has_actions_run = has_same_repo_actions_run_or_artifact_url(normalized_evidence)
    has_drill_log = has_existing_drill_log_reference(normalized_evidence, row_id=row_id)
    has_automated_evidence = bool(valid_node_ids and (has_actions_run or has_drill_log))
    if row_id.startswith(ISSUE_39_PRODUCTION_GRADE_ROW_PREFIXES):
        return has_automated_evidence
    if has_automated_evidence:
        return True
    if has_actions_run:
        return True
    if has_drill_log:
        return True
    if "human-only" in normalized_evidence and owner.strip() and residual_risk.strip().lower() not in {
        "",
        "n/a",
        "na",
        "todo",
        "tbd",
        "pending",
    }:
        return True
    return False


def has_same_repo_actions_run_or_artifact_url(evidence: str) -> bool:
    boundary = r"(?=$|[\s),.;:])"
    run_pattern = rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/actions/runs/\d+{boundary}"
    artifact_pattern = (
        rf"https://github\.com/{re.escape(REPOSITORY_FULL_NAME)}/actions/runs/\d+/artifacts/\d+{boundary}"
    )
    return bool(re.search(run_pattern, evidence) or re.search(artifact_pattern, evidence))


def has_existing_drill_log_reference(evidence: str, *, row_id: str) -> bool:
    if "drill log" not in evidence:
        return False
    for match in re.finditer(r"\b(?P<path>(?:docs|reports|artifacts|logs)/[A-Za-z0-9_./-]+)", evidence):
        path = match.group("path").rstrip(".,;:)")
        if ".." in Path(path).parts:
            continue
        if not path.startswith(ISSUE_39_DRILL_LOG_PREFIXES):
            continue
        resolved = (ROOT / path).resolve()
        try:
            resolved.relative_to(ROOT)
        except ValueError:
            continue
        if resolved.is_file() and drill_log_file_satisfies_row(resolved, row_id):
            return True
    return has_same_repo_actions_run_or_artifact_url(evidence)


def drill_log_file_satisfies_row(path: Path, row_id: str) -> bool:
    if path.suffix.lower() not in ISSUE_39_DRILL_LOG_SUFFIXES:
        return False
    content = path.read_text(encoding="utf-8").lower()
    if "drill" not in content:
        return False
    required_groups = ISSUE_39_OPERATIONAL_CLOSURE_EVIDENCE_TERMS.get(row_id, ())
    return all(any(term in content for term in group) for group in required_groups)


def valid_pytest_node_ids_in_text(text: str) -> set[tuple[str, str]]:
    tests_by_path = known_tests_by_path()
    valid_node_ids: set[tuple[str, str]] = set()
    for match in re.finditer(r"\b(?P<path>tests/[A-Za-z0-9_./-]+\.py)::(?P<test>test_[A-Za-z0-9_]+)\b", text):
        target_path = match.group("path")
        test_name = match.group("test")
        if test_name in tests_by_path.get(target_path, set()):
            valid_node_ids.add((target_path, test_name))
    return valid_node_ids


def missing_issue39_operational_evidence_terms(row_id: str, evidence: str) -> list[tuple[str, ...]]:
    required_groups = ISSUE_39_OPERATIONAL_CLOSURE_EVIDENCE_TERMS.get(row_id, ())
    return [group for group in required_groups if not any(term in evidence for term in group)]


def check_issue39_execution_strategy(failures: list[str]) -> None:
    rel = "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md"
    path = ROOT / rel
    if not path.is_file():
        failures.append(f"Missing required issue #39 execution strategy: {rel}")
        return

    text = read(rel)
    check_required_headings(
        failures,
        text,
        rel,
        (
            "Objective",
            "Tracking Contract",
            "Chunk Definition Of Done",
            "Execution State Machine",
            "Parallelization Model",
            "Agent Review Protocol",
            "Re-Review After Fixes",
            "Chunk Work Plan",
            "Deployment Transition Plan",
            "Stop Rules And Handoffs",
        ),
    )

    required_markers = (
        "Refs #39",
        "reference-only",
        "pre-code",
        "positive invariants",
        "negative invariants",
        "false-pass",
        "RED tests",
        "adversarial-review",
        "re-review",
        "GOV-SCOPE-001",
        "DUR-ACID-001",
        "OPS-WATCH-001",
        "SEC-UNTRUSTED-001",
        "No-Go",
        "Go",
        "phase-1-closure-39-",
    )
    missing_markers = [marker for marker in required_markers if marker not in text]
    if missing_markers:
        failures.append(
            "Issue #39 execution strategy missing required markers: "
            + ", ".join(missing_markers)
        )

    if re.search(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#39\b", text, flags=re.I):
        failures.append("Issue #39 execution strategy must not use auto-closing #39 wording.")

    check_issue39_strategy_required_terms(failures, text)

    headers, rows = parse_table_lines(section(text, "Chunk Work Plan"))
    required_headers = (
        "Chunk",
        "Matrix IDs",
        "Dependencies",
        "Parallel group",
        "Required planning artifact",
        "Required review agents",
        "Done when",
    )
    normalized_headers = [normalize_header(header) for header in headers]
    missing_headers = [header for header in required_headers if normalize_header(header) not in normalized_headers]
    if missing_headers:
        failures.append("Issue #39 execution strategy Chunk Work Plan missing headers: " + ", ".join(missing_headers))
        return

    matrix_index = normalized_headers.index("matrix ids")
    chunk_index = normalized_headers.index("chunk")
    dependencies_index = normalized_headers.index("dependencies")
    parallel_index = normalized_headers.index("parallel group")
    planning_index = normalized_headers.index("required planning artifact")
    review_index = normalized_headers.index("required review agents")
    done_index = normalized_headers.index("done when")

    seen_ids: set[str] = set()
    chunks_by_id: dict[str, set[str]] = {}
    dependencies_by_chunk: dict[str, set[str]] = {}
    for row in rows:
        if len(row) != len(headers):
            failures.append(f"Issue #39 execution strategy chunk row has wrong column count: {row}")
            continue
        chunk = row[chunk_index].strip("` ")
        chunk_match = re.match(r"^(CH-\d{2})\b", chunk)
        if not chunk_match:
            failures.append(f"Issue #39 execution strategy chunk has invalid chunk label: {chunk}")
            continue
        chunk_id = chunk_match.group(1)
        if chunk_id in chunks_by_id:
            failures.append(f"Issue #39 execution strategy duplicates chunk: {chunk_id}")
        matrix_ids = set(re.findall(r"[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{3}", row[matrix_index]))
        if not matrix_ids:
            failures.append(f"Issue #39 execution strategy chunk {chunk} has no matrix IDs.")
        chunks_by_id[chunk_id] = matrix_ids
        dependencies_by_chunk[chunk_id] = set(re.findall(r"CH-\d{2}", row[dependencies_index]))
        seen_ids.update(matrix_ids)
        for index, label in (
            (dependencies_index, "Dependencies"),
            (parallel_index, "Parallel group"),
            (planning_index, "Required planning artifact"),
            (review_index, "Required review agents"),
            (done_index, "Done when"),
        ):
            if row[index].strip().lower() in {"", "n/a", "na", "todo", "tbd", "pending"}:
                failures.append(f"Issue #39 execution strategy chunk {chunk} has placeholder {label}.")

    missing_ids = sorted(REQUIRED_ISSUE_39_MATRIX_IDS - seen_ids)
    if missing_ids:
        failures.append("Issue #39 execution strategy missing matrix IDs: " + ", ".join(missing_ids))

    unexpected_ids = sorted(seen_ids - REQUIRED_ISSUE_39_MATRIX_IDS)
    if unexpected_ids:
        failures.append("Issue #39 execution strategy has unexpected matrix IDs: " + ", ".join(unexpected_ids))

    expected_chunks = set(EXPECTED_ISSUE_39_CHUNK_MATRIX_IDS)
    actual_chunks = set(chunks_by_id)
    missing_chunks = sorted(expected_chunks - actual_chunks)
    if missing_chunks:
        failures.append("Issue #39 execution strategy missing chunks: " + ", ".join(missing_chunks))
    unexpected_chunks = sorted(actual_chunks - expected_chunks)
    if unexpected_chunks:
        failures.append("Issue #39 execution strategy has unexpected chunks: " + ", ".join(unexpected_chunks))

    for chunk_id, expected_ids in EXPECTED_ISSUE_39_CHUNK_MATRIX_IDS.items():
        if chunk_id not in chunks_by_id:
            continue
        actual_ids = chunks_by_id[chunk_id]
        if actual_ids != expected_ids:
            failures.append(
                f"Issue #39 execution strategy chunk {chunk_id} matrix IDs must be "
                f"{', '.join(sorted(expected_ids))}; got {', '.join(sorted(actual_ids))}."
            )

    for chunk_id, dependencies in dependencies_by_chunk.items():
        unknown = sorted(dependencies - actual_chunks)
        if unknown:
            failures.append(
                f"Issue #39 execution strategy chunk {chunk_id} depends on unknown chunks: "
                + ", ".join(unknown)
            )
    for chunk_id, expected_dependencies in EXPECTED_ISSUE_39_CHUNK_DEPENDENCIES.items():
        if chunk_id not in dependencies_by_chunk:
            continue
        actual_dependencies = dependencies_by_chunk[chunk_id]
        if actual_dependencies != expected_dependencies:
            failures.append(
                f"Issue #39 execution strategy chunk {chunk_id} dependencies must be "
                f"{', '.join(sorted(expected_dependencies)) or 'None'}; got "
                f"{', '.join(sorted(actual_dependencies)) or 'None'}."
            )
    cycle = issue39_chunk_dependency_cycle(dependencies_by_chunk)
    if cycle:
        failures.append("Issue #39 execution strategy has dependency cycle: " + " -> ".join(cycle))


def check_issue39_ch11_slo_contract(failures: list[str]) -> None:
    rel = "docs/ADR/0025-ch11-slo-error-budget.md"
    path = ROOT / rel
    if not path.is_file():
        failures.append(f"Missing required issue #39 CH-11 contract ADR: {rel}")
        return

    text = read(rel)
    check_required_headings(
        failures,
        text,
        rel,
        (
            "Status",
            "Date",
            "Context",
            "Decision",
            "SLO Catalog",
            "Burn Policy And Breach Actions",
            "Explicit Deferrals",
            "Consequences",
            "Related Documents",
        ),
    )
    required_markers = (
        "Issue `#127`",
        "Issue `#128`",
        "OPS-SLO-001",
        "OPS-METRICS-001",
        "CTX5-SLO-EVID-001",
        "issue `#39` remains open",
        "matrix row `OPS-SLO-001` remains `Open`",
        "executable now",
        "advisory-only",
        "manual review contract",
        "error budget",
        "burn policy",
        "release-blocking",
        "`CH-12`",
        "`CH-13`",
        "`CH-14`",
        "`CH-15`",
    )
    missing_markers = [marker for marker in required_markers if marker not in text]
    if missing_markers:
        failures.append(f"{rel} missing required markers: " + ", ".join(missing_markers))

    required_metrics = (
        "narratwin_ops_run_backlog_gauge",
        "narratwin_ops_lease_state_count",
        "narratwin_ops_lease_staleness_seconds",
        "narratwin_ops_lease_reacquire_total",
        "narratwin_ops_idempotency_contract_drift_total",
        "narratwin_ops_idempotency_replay_total",
        "narratwin_ops_idempotency_terminal_replay_fail_total",
        "narratwin_ops_stale_writer_reject_total",
        "narratwin_ops_outbox_backlog_count",
        "narratwin_ops_outbox_age_seconds",
        "narratwin_ops_outbox_redelivery_total",
        "narratwin_ops_restore_attempts_total",
        "narratwin_ops_restore_duration_seconds",
        "narratwin_ops_rollback_block_total",
    )
    missing_metrics = [metric for metric in required_metrics if metric not in text]
    if missing_metrics:
        failures.append(f"{rel} missing CH-10 metric bindings: " + ", ".join(missing_metrics))

    if re.search(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#39\b", text, flags=re.I):
        failures.append(f"{rel} must not use auto-closing #39 wording.")

    plan_text = read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md")
    required_plan_markers = (
        "### Issue `#127` CH-11 SLO and error-budget contract status and evidence mapping",
        "Issue `#127` is the narrow executable `CH-11` slice",
        "does not close `OPS-SLO-001`",
        "does not satisfy `OPS-ALERT-001` or `OPS-WATCH-001`",
        "does not create production restore-drill or rollback-communications evidence",
        "`docs/ADR/0025-ch11-slo-error-budget.md`",
    )
    missing_plan_markers = [marker for marker in required_plan_markers if marker not in plan_text]
    if missing_plan_markers:
        failures.append(
            "docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md missing CH-11 markers: "
            + ", ".join(missing_plan_markers)
        )


def check_issue39_strategy_required_terms(failures: list[str], text: str) -> None:
    required_by_section = {
        "Chunk Definition Of Done": (
            "pre-code plan exists before implementation",
            "source facts",
            "non-goals",
            "positive invariants",
            "negative invariants",
            "failure or false-pass",
            "test mapping",
            "RED tests",
            "executable negative tests",
            "documented human-only evidence surface",
            "implementation and tests",
            "recorded disposition",
            "fixed",
            "rejected with evidence",
            "non-goal with rationale",
            "human-only follow-up",
            "re-reviewed by a fresh reviewer",
        ),
        "Deployment Transition Plan": (
            "Production deployment remains blocked",
            "Staging/pre-production transition",
            "make quality",
            "make ci",
            "make security",
            "make dependency-audit",
            "make container-scan",
            "make secrets-scan",
            "make eval",
            "migration dry run",
            "backup/restore drill evidence",
            "dashboard, alert, and watch evidence",
            "docs/reviews/GO_NO_GO.md",
            "docs/RELEASE_CHECKLIST.md",
            "health",
            "readiness",
            "metrics",
            "alerts",
            "rollback probes",
            "Failed production transition probes halt before enablement",
            "watch or SLO threshold",
            "rollback communications",
        ),
    }
    for heading, terms in required_by_section.items():
        section_text = section(text, heading).lower()
        missing_terms = [term for term in terms if term.lower() not in section_text]
        if missing_terms:
            failures.append(
                f"docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md {heading} missing required terms: "
                + ", ".join(missing_terms)
            )
    headers, rows = parse_table_lines(section(text, "Chunk Work Plan"))
    normalized_headers = [normalize_header(header) for header in headers]
    if "chunk" not in normalized_headers or "done when" not in normalized_headers:
        return
    chunk_index = normalized_headers.index("chunk")
    done_index = normalized_headers.index("done when")
    for row in rows:
        if len(row) != len(headers):
            continue
        chunk = row[chunk_index]
        if "`CH-10`" not in chunk:
            continue
        done_when = row[done_index].lower()
        required_ch10_terms = (
            "metric catalog",
            "shared instrumentation contracts",
            "restore and rollback metric emissions close with `ch-14` and `ch-15`",
        )
        missing_ch10_terms = [term for term in required_ch10_terms if term not in done_when]
        if missing_ch10_terms:
            failures.append(
                "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md CH-10 row missing required terms: "
                + ", ".join(missing_ch10_terms)
            )

    for row in rows:
        if len(row) != len(headers):
            continue
        chunk = row[chunk_index]
        if "`CH-14`" not in chunk:
            continue
        row_contract = " ".join(row).lower()
        required_ch14_terms = (
            "tested failure/timeout/cleanup/journal/kms routes",
            "tested alert severity/ack/escalation/runbook links",
        )
        missing_ch14_terms = [term for term in required_ch14_terms if term not in row_contract]
        if missing_ch14_terms:
            failures.append(
                "docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md CH-14 row missing required terms: "
                + ", ".join(missing_ch14_terms)
            )


def issue39_chunk_dependency_cycle(dependencies_by_chunk: dict[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(chunk_id: str) -> list[str]:
        if chunk_id in visiting:
            start = stack.index(chunk_id)
            return [*stack[start:], chunk_id]
        if chunk_id in visited:
            return []
        visiting.add(chunk_id)
        stack.append(chunk_id)
        for dependency in sorted(dependencies_by_chunk.get(chunk_id, set())):
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(chunk_id)
        visited.add(chunk_id)
        return []

    for chunk_id in sorted(dependencies_by_chunk):
        cycle = visit(chunk_id)
        if cycle:
            return cycle
    return []


def issues_from_cell(value: str) -> set[str]:
    return set(re.findall(r"#\d+", value))


def check_branch(failures: list[str]) -> None:
    branch = current_branch()
    if not branch:
        fail(failures, "Phase 1 Closure gate could not resolve the current branch; failing closed.")
    elif branch != "main" and not PHASE1_BRANCH.match(branch):
        fail(failures, f"Phase 1 Closure work must run on phase-1-closure-* or main; got {branch}.")
    else:
        for prefix, required_commits in ISSUE_39_BRANCH_REQUIRED_ANCESTORS.items():
            if not branch.startswith(prefix):
                continue
            missing = [
                commit
                for commit in required_commits
                if not git_ok(["merge-base", "--is-ancestor", commit, "HEAD"])
            ]
            if missing:
                fail(
                    failures,
                    f"Phase 1 Closure branch {branch} must contain dependency commits: {', '.join(missing)}.",
                )


def check_required_files(failures: list[str]) -> None:
    for rel in sorted(REQUIRED_INPUT_FILES | REQUIRED_PHASE1_FILES):
        if not (ROOT / rel).is_file():
            fail(failures, f"Missing required Phase 1 Closure file: {rel}")


def check_changed_files(failures: list[str]) -> None:
    branch = current_branch()
    if branch.startswith("phase-1-closure-141-"):
        allowed_files = ISSUE_141_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-138-"):
        allowed_files = ISSUE_138_ALLOWED_CHANGED_FILES
    elif branch.startswith(ISSUE_159_BRANCH_PREFIX):
        allowed_files = ISSUE_159_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-process-72-"):
        allowed_files = ISSUE_72_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-process-"):
        allowed_files = PROCESS_ONLY_ALLOWED_CHANGED_FILES
    elif branch == "phase-1-closure-39-execution-strategy":
        allowed_files = ISSUE_39_EXECUTION_STRATEGY_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-37-"):
        allowed_files = ISSUE_37_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context0-"):
        allowed_files = ISSUE_39_CONTEXT0_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context1-"):
        allowed_files = ISSUE_39_CONTEXT1_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context2-"):
        allowed_files = ISSUE_39_CONTEXT2_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context3-"):
        allowed_files = ISSUE_39_CONTEXT3_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch01-"):
        allowed_files = ISSUE_39_CH01_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-02-"):
        allowed_files = ISSUE_39_CH02_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-03-"):
        allowed_files = ISSUE_39_CH03_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-04-"):
        allowed_files = ISSUE_39_CH04_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-05-"):
        allowed_files = ISSUE_39_CH05_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-06-"):
        allowed_files = ISSUE_39_CH06_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-07-"):
        allowed_files = ISSUE_39_CH07_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-08-"):
        allowed_files = ISSUE_39_CH08_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-09-"):
        allowed_files = ISSUE_39_CH09_ALLOWED_CHANGED_FILES
    elif branch == "phase-1-closure-39-restore-local-drill":
        allowed_files = ISSUE_39_RESTORE_LOCAL_DRILL_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-14-"):
        allowed_files = ISSUE_39_CH14_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-10-"):
        allowed_files = ISSUE_39_CH10_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-11-"):
        allowed_files = ISSUE_39_CH11_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-ch-16-"):
        allowed_files = ISSUE_39_CH16_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context4-"):
        allowed_files = ISSUE_39_CONTEXT4_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context5-"):
        allowed_files = ISSUE_39_CONTEXT5_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-context6-"):
        allowed_files = ISSUE_39_CONTEXT6_ALLOWED_CHANGED_FILES
    elif branch == "phase-1-closure-39-durability-monitoring":
        allowed_files = ISSUE_39_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-39-"):
        allowed_files = ISSUE_39_EXECUTION_STRATEGY_ALLOWED_CHANGED_FILES
    elif branch.startswith("phase-1-closure-42-"):
        allowed_files = ISSUE_42_ALLOWED_CHANGED_FILES
    else:
        allowed_files = MODULE_A_ALLOWED_CHANGED_FILES
    for rel in changed_files():
        if rel not in allowed_files:
            fail(failures, f"Phase 1 Closure branch {branch} may not change {rel}.")


def check_final_review_baseline(failures: list[str]) -> None:
    text = read("docs/reviews/GO_NO_GO.md")
    required_lines = (
        "No-Go for production release.",
        "No-Go for multi-worker deployment.",
        "No-Go for external paid/provider-backed generation.",
        "No-Go for real video export.",
        "No-Go for public synthetic-media distribution.",
    )
    for line in required_lines:
        if line not in text:
            fail(failures, f"GO_NO_GO.md must preserve Final Review baseline line: {line}")
    if "issues `#35` through `#44`" not in text:
        fail(failures, "GO_NO_GO.md must continue to reference issues #35 through #44.")


def check_closure_report(failures: list[str]) -> None:
    text = read("docs/reviews/PHASE_1_CLOSURE_REPORT.md")
    if "No release tag has been created" not in text:
        fail(failures, "Phase 1 closure report must state that no release tag has been created.")
    if "No Final Review follow-up is currently classified as P3" not in text:
        fail(failures, "Phase 1 closure report must explicitly state the current P3 posture.")

    reconciliation = table_rows(section(text, "Finding-To-Issue Reconciliation"))
    issue_rows = [row for row in reconciliation if row and re.fullmatch(r"`#\d+`", row[0])]
    seen: dict[str, list[str]] = {}
    for row in issue_rows:
        if len(row) != 4:
            fail(failures, f"Finding row must have 4 columns: {row}")
            continue
        issue = row[0].strip("`")
        priority = row[1]
        module = row[2].split(":", maxsplit=1)[0]
        disposition = row[3]
        seen[issue] = row
        expected_priority = EXPECTED_ISSUE_PRIORITIES.get(issue)
        if expected_priority is None:
            fail(failures, f"Unexpected Phase 1 issue in reconciliation table: {issue}")
        elif priority != expected_priority:
            fail(failures, f"{issue} priority must be {expected_priority}; got {priority}.")
        if priority not in {"P0", "P1", "P2", "P3"}:
            fail(failures, f"{issue} priority must be one of P0/P1/P2/P3.")
        if priority in {"P0", "P1"} and module not in EXPECTED_MODULES:
            fail(failures, f"{issue} must map to a valid closure module; got {module}.")
        if not disposition:
            fail(failures, f"{issue} must include a Phase 1 disposition.")

    missing_issues = sorted(set(EXPECTED_ISSUE_PRIORITIES) - set(seen))
    if missing_issues:
        fail(failures, f"Finding reconciliation missing issues: {', '.join(missing_issues)}")
    duplicate_count = len([row[0].strip("`") for row in issue_rows])
    if duplicate_count != len(seen):
        fail(failures, "Finding reconciliation contains duplicate issue rows.")

    module_rows = table_rows(section(text, "Closure Modules"))
    modules: dict[str, list[str]] = {}
    covered_issues: set[str] = set()
    for row in module_rows:
        if len(row) != 4 or not row[0].startswith("Module "):
            continue
        module, _scope, issue_cell, evidence = row
        modules[module] = row
        covered_issues.update(issues_from_cell(issue_cell))
        if module not in EXPECTED_MODULES:
            fail(failures, f"Unexpected closure module row: {module}")
        if not evidence or evidence.lower() == "none":
            fail(failures, f"{module} must include required evidence.")

    missing_modules = sorted(EXPECTED_MODULES - set(modules))
    if missing_modules:
        fail(failures, f"Closure module table missing modules: {', '.join(missing_modules)}")

    required_coverage = {
        issue for issue, priority in EXPECTED_ISSUE_PRIORITIES.items() if priority in {"P0", "P1"}
    }
    missing_coverage = sorted(required_coverage - covered_issues)
    if missing_coverage:
        fail(
            failures,
            f"Closure module table does not cover P0/P1 issues: {', '.join(missing_coverage)}",
        )


def check_golden_questions(failures: list[str]) -> None:
    path = ROOT / "docs/evals/phase1_golden_questions.jsonl"
    questions: set[str] = set()
    ids: set[str] = set()
    fixture_types: set[str] = set()

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(failures, f"Golden question line {index} is invalid JSON: {exc}")
            continue

        unknown = set(row) - GOLDEN_KEYS
        missing = GOLDEN_KEYS - set(row)
        if unknown:
            fail(
                failures,
                f"Golden question line {index} has unknown keys: {', '.join(sorted(unknown))}",
            )
        if missing:
            fail(
                failures,
                f"Golden question line {index} missing keys: {', '.join(sorted(missing))}",
            )

        row_id = row.get("id")
        if not isinstance(row_id, str) or not re.fullmatch(r"phase1-q\d{3}", row_id):
            fail(failures, f"Golden question line {index} id must match phase1-qNNN.")
        elif row_id in ids:
            fail(failures, f"Golden question id is duplicated: {row_id}")
        else:
            ids.add(row_id)

        question = row.get("question")
        if not isinstance(question, str) or not question:
            fail(failures, f"Golden question line {index} must include a non-empty question.")
        else:
            questions.add(question)

        fixture_type = row.get("fixtureType")
        if not isinstance(fixture_type, str) or not fixture_type:
            fail(failures, f"Golden question line {index} must include fixtureType.")
        else:
            fixture_types.add(fixture_type)

        for key in ("expectedAnswer", "expectedCitationPolicy"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                fail(failures, f"Golden question line {index} must include non-empty {key}.")
        for key in ("expectedEvidence", "requiredClaims", "forbiddenClaims"):
            value = row.get(key)
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(item, str) and item for item in value)
            ):
                fail(
                    failures,
                    f"Golden question line {index} must include a non-empty string list for {key}.",
                )
        for evidence in row.get("expectedEvidence", []):
            if isinstance(evidence, str) and not (ROOT / evidence).exists():
                fail(
                    failures,
                    f"Golden question line {index} references missing evidence path: {evidence}",
                )

        metrics = row.get("metrics")
        if not isinstance(metrics, dict):
            fail(failures, f"Golden question line {index} must include metrics object.")
        else:
            for metric, floor in METRIC_FLOORS.items():
                value = metrics.get(metric)
                if not isinstance(value, (int, float)) or value < floor:
                    fail(failures, f"Golden question line {index} {metric} must be >= {floor}.")
        if row.get("unsupportedClaimsMax") != 0:
            fail(failures, f"Golden question line {index} must require unsupportedClaimsMax = 0.")

    missing_questions = sorted(REQUIRED_GOLDEN_QUESTIONS - questions)
    if missing_questions:
        fail(failures, f"Golden question set missing questions: {', '.join(missing_questions)}")
    if "prompt_injection_refusal" not in fixture_types:
        fail(failures, "Golden question set must include a prompt_injection_refusal fixture.")
    if "safety_boundary" not in fixture_types:
        fail(failures, "Golden question set must include a safety_boundary fixture.")


def check_demo_docs(failures: list[str]) -> None:
    script = read("docs/demo/PHASE_1_DEMO_SCRIPT.md")
    checklist = read("docs/demo/PHASE_1_DEMO_CHECKLIST.md")
    screenshot = read("docs/demo/PHASE_1_SCREENSHOT_GUIDE.md")
    portfolio = read("portfolio/README.md")
    combined = "\n".join((script, checklist, screenshot, portfolio))
    for marker in (
        "cp .env.example .env",
        "docker compose up --build",
        "http://localhost:3000",
        "/api/v1/healthz",
        "/api/v1/readyz",
        "create project",
        "upload project knowledge",
        "generate walkthrough script",
        "citations",
        "eval result",
        "saved output",
        "single-process",
        "local-only",
        "JSON restart snapshots",
        "production durability",
        "mock/local providers only",
    ):
        if marker not in combined:
            fail(failures, f"Phase 1 demo docs missing marker: {marker}")


def check_release_docs(failures: list[str]) -> None:
    files = {
        "docs/RELEASE_READINESS_REVIEW.md": read("docs/RELEASE_READINESS_REVIEW.md"),
        "docs/RELEASE_CHECKLIST.md": read("docs/RELEASE_CHECKLIST.md"),
        "docs/RUNBOOK.md": read("docs/RUNBOOK.md"),
        "docs/STATUS.md": read("docs/STATUS.md"),
        "docs/RISK_REGISTER.md": read("docs/RISK_REGISTER.md"),
        "docs/THIRD_PARTY_NOTICES.md": read("docs/THIRD_PARTY_NOTICES.md"),
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": read(
            "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md"
        ),
    }
    expected_by_file = {
        "docs/RELEASE_READINESS_REVIEW.md": (
            "No-Go",
            "PR `#45`",
            "issues `#35` through `#44`",
            "No tag is permitted",
            "downgraded with evidence",
        ),
        "docs/RELEASE_CHECKLIST.md": ("Phase 1", "make ci", "make security", "make eval"),
        "docs/RUNBOOK.md": ("make phase1-closure-quality", "make ci", "docker compose up --build"),
        "docs/STATUS.md": ("Phase 1 Closure", "PR `#45`", "`#35`"),
        "docs/RISK_REGISTER.md": ("Final Review Risk Register", "Phase 1 Closure"),
        "docs/THIRD_PARTY_NOTICES.md": (
            "Phase 1 golden-question dataset",
            "docs/evals/phase1_golden_questions.jsonl",
        ),
        "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": (
            "Canonical issue: `#1`",
            "Reconciliation issue: `#40`",
        ),
    }
    for rel, markers in expected_by_file.items():
        for marker in markers:
            if marker not in files[rel]:
                fail(failures, f"{rel} missing marker: {marker}")
    check_issue159_release_security_evidence(
        failures,
        files["docs/RELEASE_CHECKLIST.md"],
        files["docs/RELEASE_READINESS_REVIEW.md"],
    )
    check_issue39_status_ledger(failures, files["docs/STATUS.md"], read("docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md"))


def check_issue159_release_security_evidence(
    failures: list[str], checklist: str, readiness: str
) -> None:
    def normalize(text: str) -> str:
        return " ".join(text.split())

    def require(rel: str, location: str, text: str, markers: tuple[str, ...]) -> None:
        normalized = normalize(text)
        for marker in markers:
            if marker not in normalized:
                fail(
                    failures,
                    f"{rel} {location} missing issue #159 release-evidence marker: {marker}",
                )

    checklist_preamble = checklist.split("\n## ", maxsplit=1)[0]
    checklist_merged = section(checklist, "Implemented And Merged Evidence")
    checklist_unresolved = section(
        checklist, "Unresolved Accountable Acceptance And Security Gates"
    )
    readiness_decision = section(readiness, "Decision")
    readiness_historical = subsection(readiness, "Historical Scanner Evidence")
    readiness_reconciliation = section(readiness, "Final Review Outcome")

    require(
        "docs/RELEASE_CHECKLIST.md",
        "preamble",
        checklist_preamble,
        (
            "production-grade durability and monitoring scope in issue `#39` is open",
            "unresolved issue `#151` CPython HIGH/scanner-consensus security posture remains open",
            "PR `#152`",
            "Issue `#151` remains open",
            "issue closure do not constitute explicit dated residual-risk acceptance",
        ),
    )
    require(
        "docs/RELEASE_CHECKLIST.md",
        "Implemented And Merged Evidence section",
        checklist_merged,
        (
            "PR `#152` merged",
            "Historical Stage 8 and Final Review Docker scan evidence",
            "superseded for any current clean-container-security claim",
        ),
    )
    require(
        "docs/RELEASE_CHECKLIST.md",
        "Unresolved Accountable Acceptance And Security Gates section",
        checklist_unresolved,
        (
            "Remaining production-grade portion of `#39`",
            "Issue `#151` resolves the stable CPython HIGH findings",
            "explicit dated residual-risk acceptance",
            "collaborator approval or merge action does not constitute that acceptance",
        ),
    )
    require(
        "docs/RELEASE_READINESS_REVIEW.md",
        "Decision section",
        readiness_decision,
        (
            "Production release remains No-Go",
            "No release tag has been created",
            "local-only: no hosted",
            "PR `#152`",
            "merge commit `648c81c066127056334c5c2babae28585fd58d4d`",
            "Issue `#151` remains open",
            "issue closure do not constitute explicit dated residual-risk acceptance",
        ),
    )
    require(
        "docs/RELEASE_READINESS_REVIEW.md",
        "Historical Scanner Evidence subsection",
        readiness_historical,
        (
            "historical execution evidence, not current absence evidence",
            "Grype `0.115.0`",
            "Trivy `0.72.0`",
            "CVE-2026-11940",
            "CVE-2026-11972",
            "CVE-2026-15308",
            "superseded for any current clean-container-security claim",
        ),
    )
    require(
        "docs/RELEASE_READINESS_REVIEW.md",
        "Final Review Outcome section",
        readiness_reconciliation,
        (
            "`#138` Click dependency remediation",
            "`#151` CPython HIGH findings and Trivy/Grype disagreement: open",
            "does not resolve `#151`",
        ),
    )

    expected_decisions = {
        "implementation_152": "merged",
        "issue_151": "open",
        "explicit_dated_acceptance": "absent",
        "historical_scan_role": "dated-history-not-current-absence",
        "hosted_release": "blocked",
        "production": "blocked",
        "public_distribution": "blocked",
    }
    canonical_header = "| Decision key | Required value |"
    canonical_separator = "|---|---|"
    canonical_rows = {
        f"| `{key}` | `{value}` |": key for key, value in expected_decisions.items()
    }
    for rel, text in (
        ("docs/RELEASE_CHECKLIST.md", checklist),
        ("docs/RELEASE_READINESS_REVIEW.md", readiness),
    ):
        heading_matches = list(
            re.finditer(r"^## Current Security Decision Record[ \t]*$", text, flags=re.M)
        )
        if len(heading_matches) != 1:
            fail(
                failures,
                f"{rel} must contain exactly one Current Security Decision Record section; "
                f"got {len(heading_matches)}.",
            )
            continue

        body_start = heading_matches[0].end()
        next_heading = re.search(r"^## ", text[body_start:], flags=re.M)
        body_end = body_start + next_heading.start() if next_heading else len(text)
        record_lines = [line.strip() for line in text[body_start:body_end].splitlines()]

        header_count = record_lines.count(canonical_header)
        if header_count != 1:
            fail(
                failures,
                f"{rel} Current Security Decision Record must contain exactly one canonical "
                f"header row; got {header_count}.",
            )
        separator_count = record_lines.count(canonical_separator)
        if separator_count != 1:
            fail(
                failures,
                f"{rel} Current Security Decision Record must contain exactly one canonical "
                f"separator row; got {separator_count}.",
            )

        seen: set[str] = set()
        for line in record_lines:
            if not line or line in {canonical_header, canonical_separator}:
                continue
            if not line.startswith("|"):
                fail(
                    failures,
                    f"{rel} Current Security Decision Record contains non-table claim: {line}",
                )
                continue
            key = canonical_rows.get(line)
            if key is None:
                cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
                unknown_detail = (
                    f" with unknown decision key: {cells[0]}"
                    if len(cells) == 2 and cells[0] not in expected_decisions
                    else ""
                )
                fail(
                    failures,
                    f"{rel} Current Security Decision Record contains unexpected pipe row"
                    f"{unknown_detail}: {line}",
                )
                continue
            if key in seen:
                fail(
                    failures,
                    f"{rel} Current Security Decision Record has duplicate decision key: {key}",
                )
                continue
            seen.add(key)

        for key in sorted(set(expected_decisions) - set(seen)):
            fail(
                failures,
                f"{rel} Current Security Decision Record missing decision key: {key}",
            )

    prohibited_literal_markers = (
        "[x] Docker image scan reports no critical/high vulnerabilities",
        "| no critical/high container vulnerabilities |",
    )
    for marker in prohibited_literal_markers:
        if marker in checklist or marker in readiness:
            fail(failures, f"Issue #159 retains superseded clean-security marker: {marker}")


def check_issue39_status_ledger(failures: list[str], status_text: str, closure_plan_text: str) -> None:
    issue39_row = next(
        (line for line in status_text.splitlines() if line.startswith("| `#39` |")),
        "",
    )
    if not issue39_row:
        failures.append("docs/STATUS.md missing issue #39 ledger row.")
        return
    cells = [cell.strip() for cell in issue39_row.strip("|").split("|")]
    if len(cells) < 2:
        failures.append("docs/STATUS.md issue #39 ledger row is malformed.")
        return
    status_match = re.match(r"[a-z]+", cells[1].strip().lower())
    status_token = status_match.group(0) if status_match else ""
    if not issue39_all_matrix_rows_closed(closure_plan_text) and status_token != "open":
        failures.append("docs/STATUS.md issue #39 must remain Open while production closure matrix rows are Open.")


def issue39_all_matrix_rows_closed(closure_plan_text: str) -> bool:
    headers, rows = parse_table_lines(section(closure_plan_text, "Master Evidence Matrix"))
    normalized_headers = [normalize_header(header) for header in headers]
    if "id" not in normalized_headers or "status" not in normalized_headers:
        return False
    id_index = normalized_headers.index("id")
    status_index = normalized_headers.index("status")
    statuses = {
        row[id_index].strip("` "): row[status_index].strip("` ").lower()
        for row in rows
        if len(row) == len(headers)
    }
    return (
        set(statuses) == REQUIRED_ISSUE_39_MATRIX_IDS
        and all(status == "closed" for status in statuses.values())
    )


def check_process_docs(failures: list[str]) -> None:
    required_files = (
        ".github/CODEOWNERS",
        ".github/pull_request_template.md",
        "AGENTS.md",
        "docs/ENGINEERING_PROCESS_RCA.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
    )
    for rel in required_files:
        if not (ROOT / rel).is_file():
            fail(failures, f"Missing required process artifact: {rel}")

    pr_template = read(".github/pull_request_template.md")
    changed = set(changed_files())
    check_required_headings(
        failures,
        pr_template,
        ".github/pull_request_template.md",
        REQUIRED_PR_TEMPLATE_SECTIONS,
    )
    check_preflight_table_columns(
        failures,
        section_name=".github/pull_request_template.md preflight evidence table",
        section_text=section(pr_template, "Preflight evidence"),
        required_headers=REQUIRED_PR_PREFLIGHT_TABLE_HEADERS,
    )
    check_preflight_table_columns(
        failures,
        section_name=".github/pull_request_template.md human-only review table",
        section_text=section(pr_template, "Human-only review surfaces"),
        required_headers=REQUIRED_PR_HUMAN_ONLY_TABLE_HEADERS,
    )
    if "tests/unit/test_branch_protection_verifier.py" in changed:
        missing_optional_validation = section_contains_required_commands(
            section(pr_template, "Validation evidence"), OPTIONAL_PHASE1_VALIDATION_COMMANDS
        )
        if missing_optional_validation:
            fail(
                failures,
                "Validation evidence section in .github/pull_request_template.md should include optional command "
                f"{OPTIONAL_PHASE1_VALIDATION_COMMANDS[0]} when branch-protection verifier evidence is relevant.",
            )
    missing_required_validation = section_contains_required_commands(
        section(pr_template, "Validation evidence"), REQUIRED_PHASE1_VALIDATION_COMMANDS
    )
    if missing_required_validation:
        fail(
            failures,
            ".github/pull_request_template.md Validation evidence section missing required commands: "
            + ", ".join(missing_required_validation),
        )

    agents = read("AGENTS.md")
    for marker in (
        "docs/ENGINEERING_PROCESS_RCA.md",
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        "preflight evidence",
        "merge-closeout cycle",
        "new issue, branch, or pull request",
    ):
        if marker not in agents:
            fail(failures, f"AGENTS.md missing process marker: {marker}")

    codeowners = read(".github/CODEOWNERS")
    for marker in (
        ".github/workflows/",
        "scripts/guardrails_check.py",
        "scripts/ci/verify_branch_protection.py",
        "scripts/quality/",
        "tests/unit/test_guardrails_check.py",
        "docs/ENGINEERING_PROCESS_RCA.md",
    ):
        if marker not in codeowners:
            fail(failures, f".github/CODEOWNERS missing process marker: {marker}")

    for workflow_path in guardrail_workflow_paths():
        workflow_text = read(workflow_path)
        if not workflow_has_pull_request_edited(workflow_text):
            fail(failures, f"{workflow_path} must rerun guardrails on pull_request.edited")
        if not workflow_has_guardrail_github_token_wiring(workflow_text):
            fail(
                failures,
                f"{workflow_path} must provide issues: read, pull-requests: read, and GITHUB_TOKEN to guardrails",
            )
        if workflow_path == ".github/workflows/quality-gates.yml" and not workflow_has_stage_quality_base_sha(workflow_text):
            fail(failures, f"{workflow_path} must pass GITHUB_BASE_SHA to make quality")
        if workflow_path == ".github/workflows/quality-gates.yml" and not workflow_allows_phase1_pull_request_bases(workflow_text):
            fail(failures, f"{workflow_path} must run for phase-1-closure stacked pull request bases")

    for workflow_path in PHASE1_STACKED_BASE_WORKFLOWS:
        workflow_text = read(workflow_path)
        if not workflow_allows_phase1_pull_request_bases(workflow_text):
            fail(failures, f"{workflow_path} must run for phase-1-closure stacked pull request bases")

    rca = read("docs/ENGINEERING_PROCESS_RCA.md")
    check_required_headings(
        failures,
        rca,
        "docs/ENGINEERING_PROCESS_RCA.md",
        (
            "Durability Restore Invariant Checklist",
            "Governance / CI / False-Pass",
            "Invariant-To-Test Matrix Template",
            "Bad Partial Fixes Versus Complete Coverage",
            "Mandatory Rule For Future Durability And Process PRs",
            "Required Future Workflow For NarraTwin",
        ),
    )
    check_preflight_table_columns(
        failures,
        section_name="docs/ENGINEERING_PROCESS_RCA.md matrix template",
        section_text=section(rca, "Invariant-To-Test Matrix Template"),
        required_headers=("ID", "Area", "Invariant"),
    )
    check_matrix_template_rows(
        failures,
        section_name="docs/ENGINEERING_PROCESS_RCA.md",
        section_text=section(rca, "Invariant-To-Test Matrix Template"),
        required_keyword_groups=(
            ("source run", "retrieved context", "evaluation", "citation", "claim-support"),
            ("canonical-stage", "issue-closing", "final squash"),
        ),
    )

    playbook = read("docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md")
    check_required_headings(
        failures,
        playbook,
        "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        (
            "Durability / Restore / Replay Checklist",
            "Derived Artifact Consistency Checklist",
            "Governance / CI / False-Pass Checklist",
            "Human-Only Review Surfaces",
            "Invariant-to-Test Matrix Template",
            "Definition of Done for Process-Sensitive Work",
            "RCA Pause Artifact",
            "Stop Rules",
            "Definition Of Done",
        ),
    )
    check_preflight_table_columns(
        failures,
        section_name="docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md matrix template",
        section_text=section(playbook, "Invariant-to-Test Matrix Template"),
        required_headers=("ID", "Area", "Invariant"),
    )
    check_matrix_template_rows(
        failures,
        section_name="docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md",
        section_text=section(playbook, "Invariant-to-Test Matrix Template"),
        required_keyword_groups=(
            ("source run", "retrieved context", "evaluation", "citation", "claim-support"),
            ("concrete artifacts", "matrix-id coverage", "old-behavior proof"),
        ),
    )
    normalized_playbook = re.sub(r"\s+", " ", playbook)
    for marker in (
        "merge closeout as the default continuation",
        "required workflow default, not proof that automation has already completed each post-merge step",
        "open the required follow-up issue/branch/pr",
    ):
        if marker not in normalized_playbook.lower():
            fail(
                failures,
                "docs/templates/NEW_PROJECT_ENGINEERING_PLAYBOOK.md missing merge-closeout marker: "
                f"{marker}",
            )

    check_process_hardening_findings(
        failures,
        read("docs/reviews/PROCESS_HARDENING_FINDINGS.md"),
    )


def main() -> int:
    failures: list[str] = []
    check_branch(failures)
    check_required_files(failures)
    check_changed_files(failures)
    if not failures:
        check_final_review_baseline(failures)
        check_closure_report(failures)
        check_golden_questions(failures)
        check_demo_docs(failures)
        check_release_docs(failures)
        check_issue39_closure_plan(failures)
        check_issue125_local_restore_contract(failures)
        check_issue141_platform_ownership_contract(failures)
        check_issue126_restore_readiness_contract(failures)
        check_issue39_execution_strategy(failures)
        check_issue39_ch11_slo_contract(failures)
        check_process_docs(failures)

    if failures:
        print("Phase 1 Closure quality failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Phase 1 Closure governance quality checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
