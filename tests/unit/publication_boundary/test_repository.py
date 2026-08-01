from __future__ import annotations

from typing import Any, Callable

import pytest


def read_with_overrides(module: Any, overrides: dict[str, str]) -> Callable[[str], str]:
    def _read(path: str) -> str:
        if path in overrides:
            return overrides[path]
        return str((module.ROOT / path).read_text(encoding="utf-8"))

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
                "NarraTwin turns approved knowledge into grounded, cited, multilingual avatar",
                "NarraTwin is a generic avatar",
                1,
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

    human_mutation = policy.replace(
        "Qualified humans retain legal, privacy, biometric, licensing, confidentiality,",
        "The publication gate accepts all risk decisions.",
        1,
    )
    failures = run_repository_check(
        package,
        monkeypatch,
        overrides={"docs/PUBLICATION_BOUNDARY.md": human_mutation},
    )
    assert any("Qualified humans retain" in failure for failure in failures)


def test_known_private_framing_regressions_are_exact_supplemental_checks(
    publication_boundary: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = publication_boundary
    assert package.repository.KNOWN_PRIVATE_REGRESSIONS
    for path, markers in package.repository.KNOWN_PRIVATE_REGRESSIONS.items():
        source = package.repository.read(path)
        failures = run_repository_check(
            package,
            monkeypatch,
            overrides={path: f"{source}\n{markers[0]}\n"},
        )
        assert any("known private-framing regression" in failure for failure in failures)
    policy = " ".join(package.repository.read("docs/PUBLICATION_BOUNDARY.md").split())
    assert "A vocabulary scan is not data-loss prevention" in policy


def test_current_state_calls_interactive_q_and_a_planned_not_implemented(
    publication_boundary: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = publication_boundary
    readme = package.repository.read("README.md")
    marker = "Interactive avatar Q&A remains intended and is not currently implemented."
    assert marker in readme
    failures = run_repository_check(
        package,
        monkeypatch,
        overrides={"README.md": readme.replace(marker, "", 1)},
    )
    assert any("Interactive avatar Q&A remains intended" in failure for failure in failures)


def test_legacy_active_path_reintroduction_fails(
    publication_boundary: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    package = publication_boundary
    monkeypatch.setattr(package.repository, "ROOT", tmp_path)
    for path in package.contract.CANONICAL_PUBLIC_SOURCES:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(package.PUBLIC_STATEMENT, encoding="utf-8")
    legacy = tmp_path / "portfolio" / "README.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("legacy", encoding="utf-8")
    failures: list[str] = []
    package.repository.check_legacy_path(failures)
    assert failures == ["Legacy portfolio/README.md must be replaced prospectively."]
