"""Bounded, control-safe reporting shared by modular and legacy gates."""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence


MAX_FAILURES = 50
MAX_FAILURE_CHARS = 500
TRUNCATION_SUFFIX = " ... [truncated]"


def safe_failure(value: object) -> str:
    if not isinstance(value, str):
        return "Unprintable quality-gate failure."
    truncated = len(value) > MAX_FAILURE_CHARS
    limit = MAX_FAILURE_CHARS - len(TRUNCATION_SUFFIX) if truncated else MAX_FAILURE_CHARS
    bounded = value[:limit]
    normalized = "".join(
        " " if unicodedata.category(character).startswith("C") else character
        for character in bounded
    )
    result = " ".join(normalized.split()) or "Empty quality-gate failure."
    return f"{result}{TRUNCATION_SUFFIX}" if truncated else result


def print_result(*, header: str, success: str, failures: Sequence[object]) -> int:
    if not failures:
        print(success)
        return 0
    print(header)
    for failure in failures[:MAX_FAILURES]:
        print(f"- {safe_failure(failure)}")
    if len(failures) > MAX_FAILURES:
        print("- Additional failures omitted.")
    return 1
