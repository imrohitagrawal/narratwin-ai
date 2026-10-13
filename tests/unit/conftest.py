"""Preserve genuine checkout provenance for one frozen baseline subprocess."""

from __future__ import annotations

import os
import subprocess
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def isolate_legacy_local_child_environment(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    if request.node.nodeid != (
        "tests/unit/test_stage8_quality_gate.py::"
        "test_issue366_contract_rejects_partial_scope_and_content_mutations"
    ):
        return
    event = os.environ.get("GITHUB_EVENT_NAME")
    marker = os.environ.get("GITHUB_ACTIONS")
    if not event:
        # This historical test's local child must not inherit an orphaned marker.
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        return
    original_run = subprocess.run

    def run_with_checkout_context(args: Any, *positional: Any, **kwargs: Any) -> Any:
        if args == ["python3", "-S", "scripts/quality/check_stage8_docs.py"]:
            # The frozen body deletes the event name. Restore the actual captured
            # event only for its baseline child; never invent payloads or outputs.
            environment = dict(kwargs.get("env", os.environ))
            environment["GITHUB_EVENT_NAME"] = event
            if marker is not None:
                environment["GITHUB_ACTIONS"] = marker
            kwargs["env"] = environment
        return original_run(args, *positional, **kwargs)

    monkeypatch.setattr(subprocess, "run", run_with_checkout_context)
