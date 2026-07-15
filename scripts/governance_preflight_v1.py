"""Pure offline validation for the GovernancePreflightV1 artifact."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True)
class GovernanceFinding:
    code: str


_ARTIFACT_FIELDS = {
    "schema_version",
    "issue_number",
    "branch",
    "objective",
    "status_decision",
    "scope",
}
_CONTEXT_FIELDS = {"issue_number", "branch", "changed_files"}
_SCOPE_FIELDS = {"required", "allowed_prefixes", "forbidden"}
_LIST_FIELDS = ("required", "allowed_prefixes", "forbidden")


def _findings(codes: list[str]) -> list[GovernanceFinding]:
    return [GovernanceFinding(code) for code in codes]


def _add(codes: list[str], code: str, condition: bool) -> None:
    if condition and code not in codes:
        codes.append(code)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _schema_codes(artifact: Any, context: Any) -> list[str]:
    if not isinstance(artifact, dict) or not isinstance(context, dict):
        return ["GPF.SCHEMA.TYPE"]

    codes: list[str] = []
    _add(codes, "GPF.SCHEMA.REQUIRED", bool(_ARTIFACT_FIELDS - artifact.keys()))
    _add(codes, "GPF.SCHEMA.REQUIRED", bool(_CONTEXT_FIELDS - context.keys()))
    if codes:
        return codes
    _add(codes, "GPF.SCHEMA.UNKNOWN", bool(artifact.keys() - _ARTIFACT_FIELDS))
    _add(codes, "GPF.SCHEMA.UNKNOWN", bool(context.keys() - _CONTEXT_FIELDS))

    scope = artifact.get("scope")
    if isinstance(scope, dict):
        _add(codes, "GPF.SCHEMA.REQUIRED", bool(_SCOPE_FIELDS - scope.keys()))
        _add(codes, "GPF.SCHEMA.UNKNOWN", bool(scope.keys() - _SCOPE_FIELDS))
    if codes:
        return codes

    strings = tuple(artifact.get(name) for name in ("schema_version", "branch", "objective", "status_decision"))
    context_strings = (context.get("branch"),)
    lists = tuple(scope.get(name) for name in _LIST_FIELDS) if isinstance(scope, dict) else ()
    typed = (
        all(isinstance(value, str) for value in strings + context_strings)
        and _is_int(artifact.get("issue_number"))
        and _is_int(context.get("issue_number"))
        and isinstance(scope, dict)
        and len(lists) == len(_LIST_FIELDS)
        and all(_string_list(value) for value in lists)
        and _string_list(context.get("changed_files"))
    )
    _add(codes, "GPF.SCHEMA.TYPE", not typed)
    if codes:
        return codes

    strings = cast(tuple[str, ...], strings + context_strings)
    path_lists = cast(tuple[list[str], ...], lists) + (
        cast(list[str], context["changed_files"]),
    )
    if any(any(unicodedata.category(char) == "Cs" for char in value) for value in strings):
        return ["GPF.SCHEMA.TYPE"]
    _add(
        codes,
        "GPF.SCHEMA.BLANK",
        any(not value.strip() for value in strings)
        or any(not item.strip() for values in path_lists for item in values),
    )
    _add(codes, "GPF.SCHEMA.VERSION", artifact["schema_version"] != "GovernancePreflightV1")
    over_limit = (
        len(artifact["objective"]) > 2000
        or any(len(values) > 128 for values in path_lists)
        or any(len(item) > 512 for values in path_lists for item in values)
    )
    if not over_limit:
        serialized = json.dumps(artifact, ensure_ascii=False, separators=(",", ":"))
        over_limit = len(serialized.encode(errors="surrogatepass")) > 65536
    _add(codes, "GPF.SCHEMA.LIMIT", over_limit)
    if over_limit:
        return codes
    _add(
        codes,
        "GPF.SCHEMA.DUPLICATE",
        any(len(values) != len(set(values)) for values in path_lists),
    )
    return codes


def _valid_path(path: str, *, prefix: bool) -> bool:
    if path.startswith(("/", "\\", "~/")) or re.match(r"^[A-Za-z]:", path):
        return False
    if "\\" in path or any(unicodedata.category(char).startswith("C") for char in path):
        return False
    parts = path.split("/")
    if prefix and path.endswith("/"):
        parts.pop()
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def _matches(path: str, rules: list[str]) -> bool:
    return any(path.startswith(rule) if rule.endswith("/") else path == rule for rule in rules)


def validate_governance_preflight(
    artifact: Any, *, context: Any
) -> list[GovernanceFinding]:
    """Return deterministic findings without filesystem, process, or network access."""
    schema_codes = _schema_codes(artifact, context)
    if schema_codes:
        return _findings(schema_codes)

    scope = artifact["scope"]
    path_groups = (
        (scope["required"], False),
        (scope["allowed_prefixes"], True),
        (scope["forbidden"], True),
        (context["changed_files"], False),
    )
    if any(not _valid_path(path, prefix=prefix) for paths, prefix in path_groups for path in paths):
        return _findings(["GPF.PATH.INVALID"])

    if artifact["status_decision"] != "update-minimally":
        return _findings(["GPF.STATUS.DECISION_INVALID"])
    if "docs/STATUS.md" not in scope["required"]:
        return _findings(["GPF.STATUS.REQUIRED_MISSING"])
    if not _matches("docs/STATUS.md", scope["allowed_prefixes"]):
        return _findings(["GPF.STATUS.ALLOWED_MISSING"])

    required = scope["required"]
    allowed = scope["allowed_prefixes"]
    forbidden = scope["forbidden"]
    changed = context["changed_files"]
    non_required_changes = [path for path in changed if path not in required]
    codes: list[str] = []
    _add(codes, "GPF.SCOPE.REQUIRED_FORBIDDEN", any(_matches(path, forbidden) for path in required))
    _add(
        codes,
        "GPF.SCOPE.REQUIRED_NOT_ALLOWED",
        any(not _matches(path, allowed) and not _matches(path, forbidden) for path in required),
    )
    _add(
        codes,
        "GPF.SCOPE.REQUIRED_NOT_CHANGED",
        any(path not in changed and _matches(path, allowed) and not _matches(path, forbidden) for path in required),
    )
    _add(
        codes,
        "GPF.SCOPE.CHANGE_FORBIDDEN",
        any(_matches(path, forbidden) for path in non_required_changes),
    )
    _add(
        codes,
        "GPF.SCOPE.CHANGE_NOT_ALLOWED",
        any(
            not _matches(path, allowed) and not _matches(path, forbidden)
            for path in non_required_changes
        ),
    )
    _add(codes, "GPF.BINDING.ISSUE_MISMATCH", artifact["issue_number"] != context["issue_number"])
    _add(codes, "GPF.BINDING.BRANCH_MISMATCH", artifact["branch"] != context["branch"])
    return _findings(codes)
