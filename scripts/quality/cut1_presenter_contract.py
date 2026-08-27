#!/usr/bin/env python3
"""Issue #452 executable Cut 1 governance contract.

C2 intentionally exposes a typed, import-safe RED skeleton. C4 may replace only
the marked implementation region after the C3 freeze binds this exact contract.
No function performs provider calls, media work, credential resolution, or egress.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class Finding:
    """A deterministic contract finding."""

    code: str
    path: str
    message: str


NOT_IMPLEMENTED = Finding(
    code="CUT1.NOT_IMPLEMENTED",
    path="$",
    message="Issue #452 C2 RED skeleton; implementation is frozen for C4.",
)


def finding_codes(findings: Sequence[Finding]) -> tuple[str, ...]:
    """Return stable codes for literal test expectations."""

    return tuple(finding.code for finding in findings)


# C4_IMPLEMENTATION_REGION_START
def validate_human_evaluation(data: Mapping[str, Any]) -> tuple[Finding, ...]:
    """Validate one complete Cut1HumanRealismEvaluationV1 record."""

    del data
    return (NOT_IMPLEMENTED,)


def validate_provider_acceptance(data: Mapping[str, Any]) -> tuple[Finding, ...]:
    """Validate one complete Cut1PresenterProviderAcceptanceV1 record."""

    del data
    return (NOT_IMPLEMENTED,)


def validate_contract_documents(data: Mapping[str, Any]) -> tuple[Finding, ...]:
    """Validate materialized static Issue #452 contract documents."""

    del data
    return (NOT_IMPLEMENTED,)


def validate_contract_bundle(root: Path) -> tuple[Finding, ...]:
    """Validate the static Issue #452 protocol, matrix, and bake-off bundle."""

    del root
    return (NOT_IMPLEMENTED,)


# C4_IMPLEMENTATION_REGION_END


def _load_object(path: Path) -> Mapping[str, Any]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("contract input must be a JSON object")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("human", "provider", "bundle"), required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.kind == "bundle":
        findings = validate_contract_bundle(args.root)
    else:
        if args.input is None:
            parser.error("--input is required for human/provider validation")
        data = _load_object(args.input)
        findings = (
            validate_human_evaluation(data)
            if args.kind == "human"
            else validate_provider_acceptance(data)
        )
    print(json.dumps([asdict(finding) for finding in findings], sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
