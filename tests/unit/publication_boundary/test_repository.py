from __future__ import annotations

from typing import Any, Callable

import pytest


def read_with_overrides(module: Any, overrides: dict[str, str]) -> Callable[[str], str]:
    def _read(path: str) -> str:
        if path in overrides:
            return overrides[path]
        return (module.ROOT / path).read_text(encoding="utf-8")

    return _read


def run_repository_check(
    package: Any,
    monkeypatch: pytest.MonkeyPatch,
    *,
    overrides: dict[str, str] | None = None,
) -> list[str]:
    if overrides:
        monkeypatch.setattr(
            package.repository,
            "read",
            read_with_overrides(package.repository, overrides),
        )
    failures: list[str] = []
    package.check_publication_boundary(failures)
    return failures


def test_current_contract_and_canonical_sources_pass(
    publication_boundary: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert run_repository_check(publication_boundary, monkeypatch) == []


def test_canonical_source_marker_mutation_fails(
    publication_boundary: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = publication_boundary
    source = package.repository.read("docs/PRODUCT_STRATEGY.md")
    failures = run_repository_check(
        package,
        monkeypatch,
        overrides={
            "docs/PRODUCT_STRATEGY.md": source.replace(
                package.PUBLIC_STATEMENT, "NarraTwin is a generic avatar.", 1
            )
        },
    )
    assert any("approved public product statement" in failure for failure in failures)


def test_policy_preserves_no_go_and_human_decisions(
    publication_boundary: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = publication_boundary
    policy = package.repository.read("docs/PUBLICATION_BOUNDARY.md")
    failures = run_repository_check(
        package,
        monkeypatch,
        overrides={
            "docs/PUBLICATION_BOUNDARY.md": policy.replace(
                "A publication classification is not a release authorization.",
                "Publication classification authorizes release.",
                1,
            )
        },
    )
    assert any("release authorization" in failure for failure in failures)
