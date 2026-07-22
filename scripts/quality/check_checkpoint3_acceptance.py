#!/usr/bin/env python3
"""Failing-by-design Checkpoint 3 acceptance gate skeleton."""

from __future__ import annotations

PLANNED_PROBES = (
    (
        "API E2E",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_api_e2e.py -q",
    ),
    (
        "language quality",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_language_quality.py -q",
    ),
    (
        "media artifacts",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_media_artifacts.py -q",
    ),
    (
        "access/quota/retention",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_access_quota_retention.py -q",
    ),
    (
        "security/observability",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_security_observability.py -q",
    ),
    (
        "performance",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_performance.py -q",
    ),
    (
        "real-browser E2E with no success-path interception",
        "NARRATWIN_REAL_STACK=1 NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "npm --prefix frontend run test:smoke -- "
        "--config=frontend/playwright.checkpoint3.config.ts",
    ),
    (
        "output-correctness that executes rather than reads",
        "NARRATWIN_CP3_PRODUCT_FAITHFUL=1 "
        "uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q",
    ),
)


def main() -> int:
    print("Checkpoint 3 acceptance is not implemented yet.")
    print("This failing-by-design gate defines the future executable probes:")
    for label, command in PLANNED_PROBES:
        print(f"- {label}: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
