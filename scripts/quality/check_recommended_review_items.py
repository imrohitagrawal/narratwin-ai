#!/usr/bin/env python3
"""Check staged disposition for non-blocking review recommendations."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "docs" / "RECOMMENDED_REVIEW_ITEMS.md"
CURRENT_STAGE = ROOT / ".stage" / "current"

STAGE_ORDER = {
    "Stage 0": 0,
    "Stage 1": 1,
    "Stage 2": 2,
    "Stage 3": 3,
    "Stage 4": 4,
    "Stage 5": 5,
    "Stage 6": 6,
    "Stage 7": 7,
    "Stage 8": 8,
    "Final Review": 9,
}

OPEN_STATUSES = {"Open", "In Progress"}
CLOSED_STATUSES = {"Done", "Accepted Non-blocking", "Superseded"}
VALID_STATUSES = OPEN_STATUSES | CLOSED_STATUSES

EXPECTED_ITEMS = {
    "RR-001": ("Stage 3", "LOCAL_STORAGE_ROOT"),
    "RR-002": ("Stage 3", "lockfile"),
    "RR-003": ("Stage 3", "GitHub Actions"),
    "RR-004": ("Stage 3", "untracked"),
    "RR-005": ("Stage 4", "Ingestion status"),
    "RR-006": ("Stage 2", "review prompt pack"),
    "RR-007": ("Stage 2", "WARNING"),
    "RR-008": ("Stage 2", "observability"),
}


@dataclass(frozen=True)
class ReviewItem:
    item_id: str
    recommendation: str
    required_stage: str
    status: str
    source: str
    acceptance_criteria: str


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def normalize_stage(value: str) -> str | None:
    value = value.strip()
    if value in STAGE_ORDER:
        return value
    if re.fullmatch(r"\d+", value):
        candidate = f"Stage {value}"
        return candidate if candidate in STAGE_ORDER else None
    match = re.fullmatch(r"Stage\s+(\d+)", value, flags=re.IGNORECASE)
    if match:
        candidate = f"Stage {match.group(1)}"
        return candidate if candidate in STAGE_ORDER else None
    if value.lower() in {"final", "final review"}:
        return "Final Review"
    return None


def target_stage() -> str:
    if len(sys.argv) > 1:
        normalized = normalize_stage(sys.argv[1])
        if normalized is None:
            raise ValueError(f"Unknown target stage: {sys.argv[1]}")
        return normalized
    if not CURRENT_STAGE.exists():
        raise ValueError("Missing .stage/current. Cannot check recommended review items.")
    normalized = normalize_stage(CURRENT_STAGE.read_text(encoding="utf-8").strip())
    if normalized is None:
        raise ValueError(".stage/current must contain 0 through 8 or Final Review.")
    return normalized


def parse_items(text: str) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| RR-"):
            continue
        columns = [part.strip() for part in line.strip("|").split("|")]
        if len(columns) != 6:
            raise ValueError(f"Malformed recommendation row: {raw_line}")
        items.append(ReviewItem(*columns))
    return items


def check_register(target: str) -> list[str]:
    failures: list[str] = []
    if not REGISTER.is_file():
        return [f"Missing recommended review item register: {REGISTER.relative_to(ROOT)}"]

    text = REGISTER.read_text(encoding="utf-8")
    for required in ("# Recommended Review Items", "## Policy", "## Items"):
        if required not in text:
            fail(f"docs/RECOMMENDED_REVIEW_ITEMS.md must include {required}.", failures)

    try:
        items = parse_items(text)
    except ValueError as exc:
        return [str(exc)]

    if not items:
        fail("docs/RECOMMENDED_REVIEW_ITEMS.md must contain at least one RR-* item.", failures)

    seen: set[str] = set()
    target_order = STAGE_ORDER[target]
    by_id = {item.item_id: item for item in items}

    for item in items:
        if item.item_id in seen:
            fail(f"Duplicate recommended review item ID: {item.item_id}", failures)
        seen.add(item.item_id)
        if item.required_stage not in STAGE_ORDER:
            fail(f"{item.item_id} has unknown required stage: {item.required_stage}", failures)
            continue
        if item.status not in VALID_STATUSES:
            fail(f"{item.item_id} has unknown status: {item.status}", failures)
        if not item.recommendation or not item.source or not item.acceptance_criteria:
            fail(f"{item.item_id} must include recommendation, source, and acceptance criteria.", failures)
        if STAGE_ORDER[item.required_stage] <= target_order and item.status in OPEN_STATUSES:
            fail(
                f"{item.item_id} is {item.status} but is due by {item.required_stage}; "
                "resolve it, accept it as non-blocking with rationale, or supersede it.",
                failures,
            )

    for item_id, (required_stage, required_term) in EXPECTED_ITEMS.items():
        item = by_id.get(item_id)
        if item is None:
            fail(f"Missing expected recommended review item: {item_id}", failures)
            continue
        if item.required_stage != required_stage:
            fail(f"{item_id} must be assigned to {required_stage}.", failures)
        if required_term not in item.recommendation and required_term not in item.acceptance_criteria:
            fail(f"{item_id} must retain review context term: {required_term}", failures)

    return failures


def main() -> int:
    try:
        target = target_stage()
    except ValueError as exc:
        print(f"Recommended review item check failed:\n- {exc}")
        return 1

    failures = check_register(target)
    if failures:
        print("Recommended review item check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Recommended review item check passed for {target}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
