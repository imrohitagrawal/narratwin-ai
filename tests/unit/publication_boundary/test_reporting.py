from __future__ import annotations

from typing import Any


def test_safe_failure_bounds_and_normalizes_untrusted_text(publication_boundary: Any) -> None:
    reporting = publication_boundary.reporting
    result = reporting.safe_failure("secret\n\x00" + "x" * 1_000_000)

    assert len(result) <= reporting.MAX_FAILURE_CHARS
    assert "\n" not in result
    assert "\x00" not in result
    assert result.endswith(reporting.TRUNCATION_SUFFIX)


def test_print_result_bounds_failure_count_and_each_message(
    publication_boundary: Any, capsys: Any
) -> None:
    reporting = publication_boundary.reporting
    failures = ["x" * 10_000 for _index in range(reporting.MAX_FAILURES + 10)]

    assert reporting.print_result(header="failed", success="passed", failures=failures) == 1
    output = capsys.readouterr().out.splitlines()
    assert len(output) == reporting.MAX_FAILURES + 2
    assert max(map(len, output)) <= reporting.MAX_FAILURE_CHARS + 2
    assert output[-1] == "- Additional failures omitted."


def test_non_string_failure_does_not_invoke_attacker_stringification(
    publication_boundary: Any,
) -> None:
    class ExplodingText:
        def __str__(self) -> str:
            raise RuntimeError("must not run")

    assert (
        publication_boundary.reporting.safe_failure(ExplodingText())
        == "Unprintable quality-gate failure."
    )
