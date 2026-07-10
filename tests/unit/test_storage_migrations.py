from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

import pytest

from backend.app.storage.migrations import (
    MigrationContext,
    MigrationRegistryError,
    MigrationRevision,
    MigrationRunner,
    MigrationStateError,
)


def test_ch01_runner_applies_ordered_expand_only_migrations(tmp_path: Path) -> None:
    events: list[str] = []
    context = MigrationContext(state={"tables": []})
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_append_table("schema_migrations", events),
            ),
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Add transition audit table.",
                apply=_append_table("project_state_transition", events),
            ),
        ],
        state_path=tmp_path / "migration-state.json",
    )

    result = runner.run(context=context)

    assert [record.revision_id for record in result.applied] == ["20260711_01", "20260711_02"]
    assert result.current_revision == "20260711_02"
    assert context.state["tables"] == ["schema_migrations", "project_state_transition"]
    assert events == ["schema_migrations", "project_state_transition"]


def test_ch01_runner_rejects_unknown_or_out_of_order_dependency(tmp_path: Path) -> None:
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Depends on a missing earlier revision.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Out of order in the registry.",
                apply=_noop,
            ),
        ],
        state_path=tmp_path / "migration-state.json",
    )

    with pytest.raises(MigrationRegistryError, match="ordered"):
        runner.run(context=MigrationContext())


def test_ch01_runner_rejects_duplicate_revision_ids(tmp_path: Path) -> None:
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="First revision.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260711_01",
                down_revision="20260711_01",
                phase="expand",
                description="Duplicate revision id.",
                apply=_noop,
            ),
        ],
        state_path=tmp_path / "migration-state.json",
    )

    with pytest.raises(MigrationRegistryError, match="Duplicate revision"):
        runner.run(context=MigrationContext())


def test_ch01_runner_does_not_record_failed_revision_as_applied(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Fails before apply completes.",
                apply=_raise_runtime_error,
            )
        ],
        state_path=state_path,
    )

    with pytest.raises(RuntimeError, match="boom"):
        runner.run(context=MigrationContext())

    restored = MigrationRunner(revisions=[], state_path=state_path).load_applied()
    assert restored == []


def test_ch01_runner_preserves_last_good_revision_when_a_later_revision_fails(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    context = MigrationContext(state={"tables": []})
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_append_table("schema_migrations"),
            ),
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Fails after the first revision is already durable.",
                apply=_raise_runtime_error,
            ),
        ],
        state_path=state_path,
    )

    with pytest.raises(RuntimeError, match="boom"):
        runner.run(context=context)

    restored = MigrationRunner(revisions=[], state_path=state_path).load_applied()

    assert [record.revision_id for record in restored] == ["20260711_01"]
    assert context.state["tables"] == ["schema_migrations"]


def test_ch01_runner_is_idempotent_for_already_applied_revisions(tmp_path: Path) -> None:
    context = MigrationContext(state={"tables": []})
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_append_table("schema_migrations"),
            )
        ],
        state_path=tmp_path / "migration-state.json",
    )

    first = runner.run(context=context)
    second = runner.run(context=context)

    assert [record.revision_id for record in first.applied] == ["20260711_01"]
    assert second.applied == ()
    assert second.current_revision == "20260711_01"
    assert context.state["tables"] == ["schema_migrations"]


def test_ch01_runner_rejects_tampered_current_revision_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_02",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_01",
                        "down_revision": None,
                        "phase": "expand",
                        "description": "Create schema version ledger.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = MigrationRunner(revisions=[], state_path=state_path)

    with pytest.raises(MigrationStateError, match="currentRevision"):
        runner.load_applied()


def test_ch01_runner_rejects_unreadable_json_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text("{", encoding="utf-8")

    runner = MigrationRunner(revisions=[], state_path=state_path)

    with pytest.raises(MigrationStateError, match="unreadable"):
        runner.load_applied()


def test_ch01_runner_rejects_tampered_metadata_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_01",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_01",
                        "down_revision": None,
                        "phase": "contract",
                        "description": "Tampered metadata.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            )
        ],
        state_path=state_path,
    )

    with pytest.raises(MigrationStateError, match="phase does not match"):
        runner.run(context=MigrationContext())


def test_ch01_runner_rejects_tampered_applied_prefix_state(tmp_path: Path) -> None:
    state_path = tmp_path / "migration-state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "storage-migration-state-v1",
                "currentRevision": "20260711_02",
                "appliedRevisions": [
                    {
                        "revision_id": "20260711_02",
                        "down_revision": "20260711_01",
                        "phase": "expand",
                        "description": "Out-of-order persisted revision.",
                        "applied_at": "2026-07-11T00:00:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="expand",
                description="Create schema version ledger.",
                apply=_noop,
            ),
            MigrationRevision(
                revision_id="20260711_02",
                down_revision="20260711_01",
                phase="expand",
                description="Add transition audit table.",
                apply=_noop,
            ),
        ],
        state_path=state_path,
    )

    with pytest.raises(MigrationStateError, match="declared registry order"):
        runner.run(context=MigrationContext())


def test_ch01_runner_rejects_contract_migrations_without_explicit_opt_in(tmp_path: Path) -> None:
    runner = MigrationRunner(
        revisions=[
            MigrationRevision(
                revision_id="20260711_01",
                down_revision=None,
                phase="contract",
                description="Drops a compatibility column.",
                apply=_noop,
            )
        ],
        state_path=tmp_path / "migration-state.json",
    )

    with pytest.raises(MigrationRegistryError, match="contract migrations require explicit opt-in"):
        runner.run(context=MigrationContext())


def _append_table(table_name: str, events: list[str] | None = None) -> Callable[[MigrationContext], None]:
    def apply(context: MigrationContext) -> None:
        tables = context.state.setdefault("tables", [])
        assert isinstance(tables, list)
        tables.append(table_name)
        if events is not None:
            events.append(table_name)

    return apply


def _raise_runtime_error(context: MigrationContext) -> None:
    del context
    raise RuntimeError("boom")


def _noop(context: MigrationContext) -> None:
    del context
