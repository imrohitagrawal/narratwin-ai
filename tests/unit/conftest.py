"""Isolate the legacy local-child fixture without altering frozen test bytes."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_legacy_local_child_environment(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    # This fixture explicitly removes the event name in its body to run a local
    # child. Restore matching local provenance; production missing-event checks
    # still fail closed and every other hosted test keeps its inherited context.
    if request.node.nodeid == (
        "tests/unit/test_stage8_quality_gate.py::"
        "test_issue366_contract_rejects_partial_scope_and_content_mutations"
    ):
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
