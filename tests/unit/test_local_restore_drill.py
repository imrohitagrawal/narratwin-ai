from dataclasses import asdict
import json
from pathlib import Path

from backend.app.storage.local_restore_drill import run_local_restore_drill


def test_local_restore_drill_replays_restored_state_without_new_ids(tmp_path: Path) -> None:
    summary = run_local_restore_drill(workdir=tmp_path)

    assert summary.schema_version == "local-restore-drill-v1"
    assert summary.elapsed_ms >= 0
    assert summary.seeded_counts == summary.restored_counts
    assert summary.replay_ids["stage4ProjectId"] == "proj_000001"
    assert summary.replay_ids["stage4RunId"] == "run_000001"
    assert summary.replay_ids["stage6RunId"] == "mlrun_000001"
    assert summary.replay_ids["stage7ConsentId"] == "consent_000001"
    assert summary.replay_ids["stage7RenderId"] == "avrun_000001"
    assert len(summary.state_files) == 3
    assert {item.service for item in summary.state_files} == {"stage4", "stage6", "stage7"}
    assert all(item.byte_size > 0 for item in summary.state_files)
    assert all(len(item.sha256) == 64 for item in summary.state_files)


def test_local_restore_drill_writes_json_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "evidence" / "restore-drill.json"

    summary = run_local_restore_drill(workdir=tmp_path, output_path=output_path)
    written = json.loads(output_path.read_text(encoding="utf-8"))

    summary_dict = asdict(summary)
    summary_dict["state_files"] = list(summary_dict["state_files"])

    assert written == summary_dict
    assert written["seeded_counts"]["stage4"]["ragChunks"] > 0
    assert written["restored_counts"]["stage7"]["renders"] == 1
