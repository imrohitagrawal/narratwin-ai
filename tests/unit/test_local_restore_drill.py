from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import pytest

import backend.app.storage.local_restore_drill as drill
from backend.app.storage.local_restore_drill import LocalRestoreDrillError, run_local_restore_drill


def test_local_restore_drill_replays_restored_state_without_new_ids(tmp_path: Path) -> None:
    summary = run_local_restore_drill(workdir=tmp_path)

    assert summary.schema_version == "local-restore-drill-v1"
    assert summary.elapsed_ms >= 0
    assert summary.seeded_counts == summary.restored_counts
    assert summary.restored_counts == summary.post_replay_counts
    assert summary.replay_ids["stage4ProjectId"] == "proj_000001"
    assert summary.replay_ids["stage4DocumentId"] == "doc_000001"
    assert summary.replay_ids["stage4ApprovedDocumentId"] == "doc_000001"
    assert summary.replay_ids["stage4IngestionRunId"] == "ing_000001"
    assert summary.replay_ids["stage4RunId"] == "run_000001"
    assert summary.replay_ids["stage6RunId"] == "mlrun_000001"
    assert summary.replay_ids["stage7ConsentId"] == "consent_000001"
    assert summary.replay_ids["stage7RenderId"] == "avrun_000001"
    assert len(summary.state_files) == 3
    assert {item.service for item in summary.state_files} == {"stage4", "stage6", "stage7"}
    state_by_service = {item.service: json.loads(Path(item.source_path).read_text()) for item in summary.state_files}
    schemas = [state_by_service[stage]["schema"] for stage in ("stage6", "stage7")]
    assert schemas == ["stage6-local-state-v3", "stage7-local-state-v2"]
    assert all(item.byte_size > 0 for item in summary.state_files)
    assert all(len(item.sha256) == 64 for item in summary.state_files)
    assert all(Path(item.source_path).is_file() for item in summary.state_files)
    assert all(Path(item.restore_path).is_file() for item in summary.state_files)
    assert Path(summary.source_state_dir).is_dir()
    assert Path(summary.restored_state_dir).is_dir()


def test_local_restore_drill_writes_json_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "evidence" / "restore-drill.json"

    summary = run_local_restore_drill(workdir=tmp_path, output_path=output_path)
    written = json.loads(output_path.read_text(encoding="utf-8"))

    summary_dict = asdict(summary)
    summary_dict["state_files"] = list(summary_dict["state_files"])

    assert written == summary_dict
    assert written["seeded_counts"]["stage4"]["ragChunks"] > 0
    assert written["restored_counts"]["stage7"]["renders"] == 1
    assert written["post_replay_counts"] == written["restored_counts"]
    assert Path(written["source_state_dir"]).is_dir()
    assert Path(written["restored_state_dir"]).is_dir()


@pytest.mark.parametrize(
    ("service", "path", "value"),
    [
        ("stage4", ("walkthroughRuns", 0, "evaluation_status"), "FAILED"),
        ("stage6", ("schema",), "stage6-local-state-v2"),
        ("stage6", ("multilingualRuns", 0, "source_evaluation_checksum"), "sha256:stale"),
        ("stage6", ("multilingualRuns", 0, "source_evaluation_lineage", "selectedContext", 0,
                    "contextRefId"), "ctx_stale"),
        ("stage6", ("idempotencyRecords", 0, "request_checksum"), "sha256:stale"),
        ("stage7", ("schema",), "stage7-local-state-v1"),
        ("stage7", ("syntheticMediaConsents", 0, "source_evaluation_checksum"), "sha256:stale"),
        ("stage7", ("avatarRenders", 0, "source_evaluation_lineage", "sourceCitationIndexes", 0), 99),
        ("stage7", ("artifactMetadata", 0, "metadata", 0, "checksum"), "sha256:stale"),
        ("stage7", ("idempotencyRecords", 0, "request_checksum"), "sha256:stale"),
    ],
)
def test_local_restore_drill_rejects_mutated_connected_graph_before_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    service: str,
    path: tuple[str | int, ...],
    value: object,
) -> None:
    copy_state = drill._copy_and_verify_state_files
    replay_calls = 0

    def corrupt(source_paths: Any, restored_paths: Any) -> Any:
        reports = copy_state(source_paths, restored_paths)
        state_path = restored_paths[service]
        payload = json.loads(state_path.read_text())
        cursor = payload
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        state_path.write_text(json.dumps(payload))
        return reports

    def replay(*args: Any, **kwargs: Any) -> None:
        nonlocal replay_calls
        replay_calls += 1

    monkeypatch.setattr(drill, "_copy_and_verify_state_files", corrupt)
    monkeypatch.setattr(drill, "_assert_replay_safety", replay)
    with pytest.raises(LocalRestoreDrillError):
        run_local_restore_drill(workdir=tmp_path)
    assert replay_calls == 0
