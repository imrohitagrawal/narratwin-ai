#!/usr/bin/env python3
"""Stage 0 quality gate for NarraTwin AI.

This check is intentionally documentation-first. It must pass before backend,
frontend, RAG, avatar, or provider implementation begins.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/SKILLS_AND_CODEX_SETUP.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
    "docs/PRD.md",
    "docs/METHODOLOGY.md",
    "docs/ARCHITECTURE.md",
    "docs/SECURITY_AND_PRIVACY.md",
    "docs/AI_SAFETY_AND_EVALUATION.md",
    ".stage/current",
    "Makefile",
]

CORE_OPERATING_DOCS = [
    "AGENTS.md",
    "docs/SKILLS_AND_CODEX_SETUP.md",
    "docs/SKILL_EXECUTION_PLAN.md",
    "docs/SKILL_LOCK.md",
    "docs/CODEX_OPERATING_MODEL.md",
    "docs/QUALITY_GATES.md",
]

DISALLOWED_MARKERS = [
    "TODO",
    "TBD",
    "FIXME",
    "coming soon",
    "lorem ipsum",
]

PRODUCT_CODE_PATHS = [
    "backend",
    "frontend",
    "app",
    "src",
    "packages",
    "services",
    "migrations",
]

STAGE_TERMS = [
    "Stage 0",
    "Stage 1",
    "Stage 2",
    "Stage 3",
    "Stage 4",
    "Stage 5",
    "Stage 6",
    "Stage 7",
    "Stage 8",
    "Final Review",
]

SKILL_SOURCES = [
    "https://github.com/phuryn/pm-skills",
    "https://github.com/github/spec-kit",
    "https://github.com/addyosmani/agent-skills",
    "https://github.com/agentskills/agentskills",
]


def fail(message: str) -> None:
    print(f"[stage0-quality] FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path: str) -> str:
    full_path = ROOT / path
    if not full_path.exists():
        fail(f"missing required file: {path}")
    if not full_path.is_file():
        fail(f"required path is not a file: {path}")
    text = full_path.read_text(encoding="utf-8").strip()
    if not text:
        fail(f"required file is empty: {path}")
    return text


def check_required_files() -> None:
    for path in REQUIRED_FILES:
        read_text(path)


def check_current_stage() -> None:
    current = read_text(".stage/current")
    if current != "0":
        fail(f".stage/current must be 0 during Stage 0, found: {current!r}")


def check_stage_model_documented() -> None:
    combined = "\n".join(read_text(path) for path in [
        "AGENTS.md",
        "docs/CODEX_OPERATING_MODEL.md",
        "docs/QUALITY_GATES.md",
        "docs/SKILLS_AND_CODEX_SETUP.md",
    ])
    for term in STAGE_TERMS:
        if term not in combined:
            fail(f"stage model is missing required term: {term}")


def check_no_unresolved_markers() -> None:
    for path in CORE_OPERATING_DOCS:
        text = read_text(path)
        lowered = text.lower()
        for marker in DISALLOWED_MARKERS:
            if marker.lower() in lowered:
                fail(f"unresolved marker {marker!r} found in {path}")


def check_skill_lock() -> None:
    text = read_text("docs/SKILL_LOCK.md")
    required_terms = [
        "Source URL",
        "Pin or version",
        "License status",
        "Purpose",
        "Active stage",
    ]
    for term in required_terms:
        if term not in text:
            fail(f"docs/SKILL_LOCK.md is missing required lock field: {term}")
    for source in SKILL_SOURCES:
        if source not in text:
            fail(f"docs/SKILL_LOCK.md is missing source: {source}")


def check_no_product_code_started() -> None:
    existing = [path for path in PRODUCT_CODE_PATHS if (ROOT / path).exists()]
    if existing:
        fail(
            "product implementation paths exist during Stage 0: "
            + ", ".join(existing)
            + ". Move implementation to Stage 3+ or document why this is non-product scaffolding."
        )


def check_makefile_targets() -> None:
    text = read_text("Makefile")
    for target in [
        "quality:",
        "stage0-quality:",
        "stage1-quality:",
        "stage2-quality:",
        "stage3-quality:",
        "stage4-quality:",
        "stage5-quality:",
        "stage6-quality:",
        "stage7-quality:",
        "stage8-quality:",
        "final-review-quality:",
    ]:
        if target not in text:
            fail(f"Makefile is missing target: {target}")


def main() -> None:
    check_required_files()
    check_current_stage()
    check_stage_model_documented()
    check_no_unresolved_markers()
    check_skill_lock()
    check_no_product_code_started()
    check_makefile_targets()
    print("[stage0-quality] PASS")


if __name__ == "__main__":
    main()
