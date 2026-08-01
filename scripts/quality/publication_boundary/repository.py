"""Canonical-source and known-regression checks for Issue #324."""

from __future__ import annotations

from pathlib import Path

from .contract import CANONICAL_PUBLIC_SOURCES, CONTRACT_PATH, PUBLIC_STATEMENT
from .contract import validate_contract_text


ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = "docs/PUBLICATION_BOUNDARY.md"
ADR_PATH = "docs/ADR/0047-publication-boundary.md"

# Exact regression protection for already-observed wording. This is not semantic
# classification or DLP; the classification/approval boundary remains authoritative.
KNOWN_PRIVATE_REGRESSIONS = {
    "docs/AI_BUILD_BRIEF.md": (
        "linkedin, youtube, portfolio pages, recruiter sharing",
    ),
    "docs/PRODUCT_STRATEGY.md": (
        "portfolio-ready and recruiter-ready",
        "visible portfolio artifacts",
    ),
    "docs/PRD.md": ("portfolio use case",),
    "docs/NORTH_STAR_METRICS.md": ("portfolio value",),
    "docs/QUALITY_GATES.md": ("portfolio readme", "portfolio docs"),
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": (
        "portfolio/recruiter walkthrough",
    ),
    "docs/THREAT_MODEL.md": ("unsupported portfolio claims",),
    "docs/RELEASE_READINESS_REVIEW.md": (
        "portfolio/demo review",
        "portfolio local-demo durability disclosure",
    ),
    "docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md": (
        "recruiter-visible",
        "recruiter first impression",
        "recruiter viewport",
        "recruiter flow ux contract",
        "ux/demo/recruiter flow",
    ),
}

REQUIRED_MARKERS = {
    POLICY_PATH: (
        "A publication classification is not a release authorization.",
        "A vocabulary scan is not data-loss prevention",
        "Qualified humans retain legal, privacy, biometric, licensing, "
        "confidentiality, and security-risk decisions.",
        "not a cryptographic or runtime enforcement boundary",
    ),
    ADR_PATH: (
        "responsibility-split",
        "per-file context budgets",
        "no product runtime or release authority",
    ),
    "README.md": (
        "Interactive avatar Q&A remains intended and is not currently implemented.",
    ),
    "docs/QUALITY_GATES.md": ("docs/demo/CONTROLLED_LOCAL_DEMO.md",),
    "docs/REQUIREMENTS_TRACEABILITY_MATRIX.md": (
        "Audience-adapted project walkthrough",
    ),
    "docs/THREAT_MODEL.md": ("Unsupported Project Claims",),
    "docs/RELEASE_READINESS_REVIEW.md": (
        "Controlled local mock-provider review",
    ),
    "docs/STAGE_ISSUE_PLAN.md": ("Issue #324 publication boundary",),
    "docs/TRACEABILITY.md": ("PUB-324-001",),
    "docs/STATUS.md": ("Issue #324", "PublicationBoundaryV1"),
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check_legacy_path(failures: list[str]) -> None:
    if (ROOT / "portfolio" / "README.md").exists():
        failures.append("Legacy portfolio/README.md must be replaced prospectively.")


def _check_canonical_sources(failures: list[str]) -> None:
    for path in CANONICAL_PUBLIC_SOURCES:
        try:
            normalized = " ".join(read(path).split())
        except OSError:
            failures.append(f"Missing canonical public source: {path}.")
            continue
        if PUBLIC_STATEMENT not in normalized:
            failures.append(
                f"Canonical source {path} must contain the approved public product statement."
            )


def _check_known_regressions(failures: list[str]) -> None:
    for path, markers in KNOWN_PRIVATE_REGRESSIONS.items():
        try:
            source = read(path).casefold()
        except OSError:
            failures.append(f"Missing publication-reviewed source: {path}.")
            continue
        for marker in markers:
            if marker in source:
                failures.append(
                    f"Publication source {path} contains known private-framing regression: {marker}."
                )


def _check_required_markers(failures: list[str]) -> None:
    for path, markers in REQUIRED_MARKERS.items():
        try:
            source = " ".join(read(path).split())
        except OSError:
            failures.append(f"Missing publication evidence source: {path}.")
            continue
        for marker in markers:
            if marker not in source:
                failures.append(f"Publication evidence source {path} must include {marker}.")


def check_publication_boundary(failures: list[str]) -> None:
    try:
        source = read(CONTRACT_PATH)
    except OSError:
        failures.append(f"Missing publication contract: {CONTRACT_PATH}.")
    else:
        _policy, contract_failures = validate_contract_text(source)
        failures.extend(contract_failures)
    _check_canonical_sources(failures)
    _check_known_regressions(failures)
    _check_required_markers(failures)
    check_legacy_path(failures)
