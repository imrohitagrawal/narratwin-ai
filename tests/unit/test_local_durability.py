from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
from typing import Any, cast

import pytest

import backend.app.stage4 as stage4_module
import backend.app.stage6 as stage6_module
import backend.app.stage7 as stage7_module
from backend.app.rag.chunking import checksum_text
from backend.app.storage import write_state as storage_write_state
from backend.app.stage4 import LocalPrincipal, Stage4Error, Stage4Service
from backend.app.stage6 import create_stage6_service
from backend.app.stage7 import create_stage7_service


class FailingAfterFirstEmbeddingProvider:
    provider = "mock"
    model = "mock-embedding"
    model_version = "stage4-local-v1"
    dimension = 16

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, text: str) -> tuple[float, ...]:
        del text
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("simulated embedding failure")
        return (1.0,) + (0.0,) * (self.dimension - 1)


def test_stage4_file_state_restores_projects_chunks_runs_and_idempotency(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)

    project = service.create_project(
        principal=principal,
        name="Durable project",
        idempotency_key="create-project",
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=Path("tests/fixtures/stage4_project.md").read_bytes(),
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )
    run = service.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="generate-walkthrough",
    )

    restored = Stage4Service(state_path=state_path)
    replayed_project = restored.create_project(
        principal=principal,
        name="Durable project",
        idempotency_key="create-project",
    )
    replayed_run = restored.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="generate-walkthrough",
    )

    assert replayed_project.project_id == project.project_id
    assert replayed_run.run_id == run.run_id
    assert restored.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) > 0
    assert restored.documents[document.document_id].ingestion_status == "INGESTED"


def test_stage4_file_state_serializes_concurrent_project_writes(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)

    def create_project(index: int) -> str:
        project = service.create_project(
            principal=principal,
            name=f"Concurrent project {index}",
            idempotency_key=f"create-project-{index}",
        )
        return project.project_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        project_ids = list(executor.map(create_project, range(12)))

    assert sorted(project_ids) == [f"proj_{index:06d}" for index in range(1, 13)]

    restored = Stage4Service(state_path=state_path)

    assert len(restored.projects) == 12
    assert sorted(restored.projects) == sorted(project_ids)


def test_file_state_corruption_degrades_to_empty_local_state(tmp_path: Path) -> None:
    stage4_path = tmp_path / "stage4.json"
    stage6_path = tmp_path / "stage6.json"
    stage7_path = tmp_path / "stage7.json"
    for path in (stage4_path, stage6_path, stage7_path):
        path.write_text("{", encoding="utf-8")

    stage4 = Stage4Service(state_path=stage4_path)
    stage6 = create_stage6_service(state_path=stage6_path)
    stage7 = create_stage7_service(state_path=stage7_path)

    assert stage4.projects == {}
    assert stage4.idempotency_records == {}
    assert stage6.idempotency_records == {}
    assert stage7.idempotency_records == {}


def test_file_state_wrong_shape_degrades_to_empty_local_state(tmp_path: Path) -> None:
    stage4_path = tmp_path / "stage4.json"
    stage6_path = tmp_path / "stage6.json"
    stage7_path = tmp_path / "stage7.json"
    stage4_path.write_text(
        json.dumps(
            {
                "schema": "stage4-local-state-v1",
                "projects": [{"project_id": "proj_bad", "unexpected": "field"}],
                "ragStore": {"chunks": [{"chunkId": "chunk_bad"}]},
                "counters": {"project": "not-a-number"},
            }
        ),
        encoding="utf-8",
    )
    stage6_path.write_text(
        json.dumps(
            {
                "schema": "stage6-local-state-v1",
                "idempotencyRecords": [{"endpoint": "missing-required-fields"}],
                "counters": {"run": "not-a-number"},
            }
        ),
        encoding="utf-8",
    )
    stage7_path.write_text(
        json.dumps(
            {
                "schema": "stage7-local-state-v1",
                "avatarRenders": [{"avatar_render_id": "render_bad"}],
                "artifactMetadata": [{"avatar_render_id": "render_bad", "metadata": [{"file_name": "missing"}]}],
                "counters": {"run": "not-a-number"},
            }
        ),
        encoding="utf-8",
    )

    stage4 = Stage4Service(state_path=stage4_path)
    stage6 = create_stage6_service(state_path=stage6_path)
    stage7 = create_stage7_service(state_path=stage7_path)

    assert stage4.projects == {}
    assert stage4.documents == {}
    assert stage4.rag_store.chunk_count_for_project(tenant_id=LocalPrincipal().tenant_id, project_id="proj_bad") == 0
    assert stage6.idempotency_records == {}
    assert stage7.avatar_renders == {}
    assert stage7.artifact_metadata == {}


@pytest.mark.parametrize("rag_store_payload", [None, [], "not-a-rag-store"])
def test_stage4_file_state_non_object_rag_store_degrades_to_empty_local_state(
    tmp_path: Path,
    rag_store_payload: object,
) -> None:
    state_path = tmp_path / "stage4.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage4-local-state-v1",
                "ragStore": rag_store_payload,
                "counters": {"project": 0, "document": 0, "ingestion": 0, "run": 0},
            }
        ),
        encoding="utf-8",
    )

    stage4 = Stage4Service(state_path=state_path)

    assert stage4.projects == {}
    assert stage4.rag_store.chunk_count_for_project(tenant_id=LocalPrincipal().tenant_id, project_id="proj_bad") == 0


def test_file_state_schema_mismatch_degrades_to_empty_local_state(tmp_path: Path) -> None:
    stage4_path = tmp_path / "stage4.json"
    stage6_path = tmp_path / "stage6.json"
    stage7_path = tmp_path / "stage7.json"
    stage4_path.write_text(
        json.dumps({"schema": "stage4-local-state-v999", "projects": [{"project_id": "proj_bad"}]}),
        encoding="utf-8",
    )
    stage6_path.write_text(
        json.dumps({"schema": "stage6-local-state-v999", "idempotencyRecords": [{"endpoint": "bad"}]}),
        encoding="utf-8",
    )
    stage7_path.write_text(
        json.dumps({"schema": "stage7-local-state-v999", "avatarRenders": [{"avatar_render_id": "bad"}]}),
        encoding="utf-8",
    )

    stage4 = Stage4Service(state_path=stage4_path)
    stage6 = create_stage6_service(state_path=stage6_path)
    stage7 = create_stage7_service(state_path=stage7_path)

    assert stage4.projects == {}
    assert stage6.idempotency_records == {}
    assert stage7.avatar_renders == {}


def test_stage4_file_state_replays_failed_idempotency_after_restart(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)

    with pytest.raises(Stage4Error) as first_error:
        service.create_project(
            principal=principal,
            name="   ",
            idempotency_key="failed-create-project",
        )

    restored = Stage4Service(state_path=state_path)

    with pytest.raises(Stage4Error) as replayed_error:
        restored.create_project(
            principal=principal,
            name="   ",
            idempotency_key="failed-create-project",
        )

    assert replayed_error.value.code == first_error.value.code == "VALIDATION_ERROR"
    assert replayed_error.value.message == first_error.value.message
    assert restored.projects == {}


def test_stage4_file_state_ignores_stale_pending_idempotency_after_restart(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage4-local-state-v1",
                "projects": [],
                "documents": [],
                "ingestionRuns": [],
                "walkthroughRuns": [],
                "idempotencyRecords": [
                    {
                        "idempotency_record_id": "idem_stale",
                        "tenant_id": principal.tenant_id,
                        "actor_id": principal.actor_id,
                        "idempotency_scope": "project:create",
                        "endpoint": "POST /api/v1/projects",
                        "idempotency_key": "stale-pending-create",
                        "request_checksum": "stale",
                        "status": "PENDING",
                        "value": {"kind": "none"},
                        "created_at": "2026-07-03T00:00:00+00:00",
                        "updated_at": "2026-07-03T00:00:00+00:00",
                    }
                ],
                "ragStore": {},
                "counters": {"project": 0, "document": 0, "ingestion": 0, "run": 0},
            }
        ),
        encoding="utf-8",
    )
    restored = Stage4Service(state_path=state_path)

    project = restored.create_project(
        principal=principal,
        name="Recovered project",
        idempotency_key="stale-pending-create",
    )

    assert project.project_id == "proj_000001"


def test_stage4_file_state_drops_completed_idempotency_with_missing_value(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    original = service.create_project(
        principal=principal,
        name="Original project",
        idempotency_key="create-project",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["projects"] = []
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)
    recreated = restored.create_project(
        principal=principal,
        name="Original project",
        idempotency_key="create-project",
    )

    assert original.project_id == "proj_000001"
    assert recreated.project_id == "proj_000002"
    assert len(restored.projects) == 1


def test_stage4_file_state_drops_failed_idempotency_with_missing_error(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    request_checksum = checksum_text("Recovered project\n\nRECRUITER\nen")
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage4-local-state-v1",
                "projects": [],
                "documents": [],
                "ingestionRuns": [],
                "walkthroughRuns": [],
                "ragStore": {},
                "idempotencyRecords": [
                    {
                        "idempotency_record_id": "idem_bad_failed",
                        "tenant_id": principal.tenant_id,
                        "actor_id": principal.actor_id,
                        "idempotency_scope": "project:create",
                        "endpoint": "POST /api/v1/projects",
                        "idempotency_key": "bad-failed",
                        "request_checksum": request_checksum,
                        "status": "FAILED",
                        "value": {"kind": "none"},
                        "created_at": "2026-07-08T00:00:00+00:00",
                        "updated_at": "2026-07-08T00:00:00+00:00",
                    }
                ],
                "counters": {"project": 0, "document": 0, "ingestion": 0, "run": 0},
            }
        ),
        encoding="utf-8",
    )

    restored = Stage4Service(state_path=state_path)
    project = restored.create_project(
        principal=principal,
        name="Recovered project",
        idempotency_key="bad-failed",
    )

    assert project.project_id == "proj_000001"
    assert len(restored.idempotency_records) == 1


def test_stage4_file_state_drops_documents_for_missing_project(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage4-local-state-v1",
                "projects": [],
                "documents": [
                    {
                        "document_id": "doc_000001",
                        "tenant_id": principal.tenant_id,
                        "owner_id": principal.actor_id,
                        "project_id": "proj_missing",
                        "source_filename": "orphan.md",
                        "content_type": "text/markdown",
                        "size_bytes": 6,
                        "checksum": "abc123",
                        "text": "orphan",
                        "document_status": "STORED",
                        "approval_status": "PENDING",
                        "ingestion_status": "NOT_STARTED",
                        "created_at": "2026-07-08T00:00:00+00:00",
                        "approved_at": None,
                        "ingested_at": None,
                    }
                ],
                "ingestionRuns": [],
                "walkthroughRuns": [],
                "ragStore": {},
                "idempotencyRecords": [],
                "counters": {"project": 0, "document": 1, "ingestion": 0, "run": 0},
            }
        ),
        encoding="utf-8",
    )

    restored = Stage4Service(state_path=state_path)

    assert restored.projects == {}
    assert restored.documents == {}


def test_stage4_file_state_prunes_tampered_rag_chunks(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal,
        name="Grounded project",
        idempotency_key="create-project",
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=b"NarraTwin creates grounded walkthrough scripts for recruiters.",
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    injected_text = "Injected content that was never uploaded."
    payload["ragStore"]["chunks"][0]["text"] = injected_text
    payload["ragStore"]["chunks"][0]["tokenCount"] = len(injected_text.split())
    payload["ragStore"]["chunks"][0]["checksum"] = checksum_text(injected_text)
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)

    assert restored.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) == 0


def test_stage4_file_state_drops_walkthrough_runs_with_missing_restored_chunks(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal,
        name="Grounded project",
        idempotency_key="create-project",
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=Path("tests/fixtures/stage4_project.md").read_bytes(),
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )
    run = service.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="generate-walkthrough",
    )
    assert run.status == "COMPLETED"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["ragStore"]["chunks"] = []
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)

    assert run.run_id == "run_000001"
    assert restored.walkthrough_runs == {}
    assert all(
        not (record.endpoint.endswith("/walkthrough-runs") and record.idempotency_key == "generate-walkthrough")
        for record in restored.idempotency_records.values()
    )


def test_stage4_file_state_drops_ingestion_runs_with_missing_restored_chunks(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal,
        name="Grounded project",
        idempotency_key="create-project",
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=Path("tests/fixtures/stage4_project.md").read_bytes(),
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    original = service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["ragStore"]["chunks"] = []
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)
    replayed = restored.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )

    assert original.ingestion_run_id == "ing_000001"
    assert replayed.ingestion_run_id == "ing_000002"
    assert restored.documents[document.document_id].ingestion_status == "INGESTED"


def test_stage4_file_state_drops_completed_walkthrough_without_evaluation(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(principal=principal, name="Grounded project", idempotency_key="create-project")
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=Path("tests/fixtures/stage4_project.md").read_bytes(),
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )
    run = service.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="generate-walkthrough",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["walkthroughRuns"][0]["evaluation"] = None
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)

    assert run.status == "COMPLETED"
    assert restored.walkthrough_runs == {}


def test_stage4_file_state_drops_walkthrough_with_tampered_evaluation_support(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(principal=principal, name="Grounded project", idempotency_key="create-project")
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=Path("tests/fixtures/stage4_project.md").read_bytes(),
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )
    run = service.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="generate-walkthrough",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    support = payload["walkthroughRuns"][0]["evaluation"]["claim_supports"][0]
    support["claim_id"] = "claim_missing"
    support["context_ref_id"] = "ctx_missing"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)

    assert run.status == "COMPLETED"
    assert restored.walkthrough_runs == {}


def test_stage4_file_state_derives_missing_counters_from_restored_ids(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    first = service.create_project(
        principal=principal,
        name="First project",
        idempotency_key="first-project",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload.pop("counters")
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)
    second = restored.create_project(
        principal=principal,
        name="Second project",
        idempotency_key="second-project",
    )

    assert first.project_id == "proj_000001"
    assert second.project_id == "proj_000002"
    assert sorted(restored.projects) == ["proj_000001", "proj_000002"]


def test_stage4_file_state_derives_stale_low_counters_from_restored_ids(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    first = service.create_project(
        principal=principal,
        name="First project",
        idempotency_key="first-project",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["counters"]["project"] = 0
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = Stage4Service(state_path=state_path)
    second = restored.create_project(
        principal=principal,
        name="Second project",
        idempotency_key="second-project",
    )

    assert first.project_id == "proj_000001"
    assert second.project_id == "proj_000002"
    assert sorted(restored.projects) == ["proj_000001", "proj_000002"]


def test_stage4_file_state_write_failure_rolls_back_in_memory_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)

    def fail_write_state(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated disk write failure")

    monkeypatch.setattr(stage4_module, "write_state", fail_write_state)
    with pytest.raises(OSError, match="simulated disk write failure"):
        service.create_project(
            principal=principal,
            name="Write failure project",
            idempotency_key="write-failure-project",
        )

    assert service.projects == {}
    assert service.idempotency_records == {}

    monkeypatch.setattr(stage4_module, "write_state", storage_write_state)
    retried = service.create_project(
        principal=principal,
        name="Write failure project",
        idempotency_key="write-failure-project",
    )

    assert retried.project_id == "proj_000001"


def test_stage4_file_state_ingest_write_failure_removes_failed_chunks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal,
        name="Ingest terminal write failure project",
        idempotency_key="create-project",
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=b"# Project\n\nContent that should be removed from the live RAG store when persist fails.",
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )

    def fail_ingestion_terminal_write(path: Path, payload: object) -> None:
        assert isinstance(payload, dict)
        if payload.get("ingestionRuns"):
            raise OSError("simulated ingestion terminal write failure")
        storage_write_state(path, payload)

    monkeypatch.setattr(stage4_module, "write_state", fail_ingestion_terminal_write)
    with pytest.raises(OSError, match="simulated ingestion terminal write failure"):
        service.ingest_documents(
            principal=principal,
            project_id=project.project_id,
            document_ids=[document.document_id],
            idempotency_key="ingest-document",
        )

    assert service.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) == 0
    assert service.documents[document.document_id].ingestion_status == "NOT_STARTED"
    assert service.ingestion_runs == {}
    assert all(record.idempotency_key != "ingest-document" for record in service.idempotency_records.values())

    monkeypatch.setattr(stage4_module, "write_state", storage_write_state)
    retried = service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )

    assert retried.ingestion_run_id == "ing_000001"
    assert service.documents[document.document_id].ingestion_status == "INGESTED"


def test_stage4_file_state_ingest_embedding_failure_rolls_back_partial_chunks(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal,
        name="Embedding failure project",
        idempotency_key="create-project",
    )
    document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=(
            "# Embedding failure project\n"
            + " ".join(f"alpha-{index}" for index in range(900))
            + "\n\n"
            + " ".join(f"beta-{index}" for index in range(900))
        ).encode(),
        idempotency_key="upload-document",
    )
    service.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="approve-document",
    )
    service.embedder = cast(Any, FailingAfterFirstEmbeddingProvider())

    with pytest.raises(RuntimeError, match="simulated embedding failure"):
        service.ingest_documents(
            principal=principal,
            project_id=project.project_id,
            document_ids=[document.document_id],
            idempotency_key="ingest-document",
        )

    assert service.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) == 0
    assert service.documents[document.document_id].ingestion_status == "NOT_STARTED"
    assert service.ingestion_runs == {}
    assert all(record.idempotency_key != "ingest-document" for record in service.idempotency_records.values())

    restored = Stage4Service(state_path=state_path)
    assert restored.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) == 0
    retried = restored.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="ingest-document",
    )

    assert retried.ingestion_run_id == "ing_000001"
    assert restored.documents[document.document_id].ingestion_status == "INGESTED"


def test_stage4_file_state_multidoc_embedding_failure_rolls_back_partial_ingestion(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    project = service.create_project(
        principal=principal,
        name="Multi-document embedding failure project",
        idempotency_key="create-project",
    )
    first_document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="first.md",
        content_type="text/markdown",
        data=b"# First document\n\nFirst document content for ingestion.",
        idempotency_key="upload-first-document",
    )
    second_document = service.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="second.md",
        content_type="text/markdown",
        data=b"# Second document\n\nSecond document content for ingestion.",
        idempotency_key="upload-second-document",
    )
    for document, key in (
        (first_document, "approve-first-document"),
        (second_document, "approve-second-document"),
    ):
        service.approve_document(
            principal=principal,
            project_id=project.project_id,
            document_id=document.document_id,
            idempotency_key=key,
        )
    service.embedder = cast(Any, FailingAfterFirstEmbeddingProvider())

    with pytest.raises(RuntimeError, match="simulated embedding failure"):
        service.ingest_documents(
            principal=principal,
            project_id=project.project_id,
            document_ids=[first_document.document_id, second_document.document_id],
            idempotency_key="ingest-documents",
        )

    assert service.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) == 0
    assert service.documents[first_document.document_id].ingestion_status == "NOT_STARTED"
    assert service.documents[second_document.document_id].ingestion_status == "NOT_STARTED"
    assert service.ingestion_runs == {}
    assert all(record.idempotency_key != "ingest-documents" for record in service.idempotency_records.values())

    restored = Stage4Service(state_path=state_path)
    assert restored.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
    ) == 0
    retried = restored.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[first_document.document_id, second_document.document_id],
        idempotency_key="ingest-documents",
    )

    assert retried.ingestion_run_id == "ing_000001"
    assert restored.documents[first_document.document_id].ingestion_status == "INGESTED"
    assert restored.documents[second_document.document_id].ingestion_status == "INGESTED"


def test_stage4_file_state_public_rollback_preserves_concurrent_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)

    class GateLock:
        def __init__(self) -> None:
            self._lock = threading.RLock()
            self._attempts: dict[str, int] = {}
            self.slow_ready = threading.Event()
            self.allow_slow = threading.Event()

        def __enter__(self) -> "GateLock":
            name = threading.current_thread().name
            attempt = self._attempts.get(name, 0)
            self._attempts[name] = attempt + 1
            if name == "slow" and attempt == 1:
                self.slow_ready.set()
                assert self.allow_slow.wait(timeout=5)
            self._lock.acquire()
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            self._lock.release()

    gate = GateLock()
    service._operation_lock = cast(Any, gate)

    def fail_slow_terminal_write(path: Path, payload: object) -> None:
        assert isinstance(payload, dict)
        if any(row.get("name") == "Slow failed project" for row in payload.get("projects", [])):
            raise OSError("simulated slow terminal write failure")
        storage_write_state(path, payload)

    def create_slow_project() -> str:
        threading.current_thread().name = "slow"
        project = service.create_project(
            principal=principal,
            name="Slow failed project",
            idempotency_key="slow-project",
        )
        return project.project_id

    monkeypatch.setattr(stage4_module, "write_state", fail_slow_terminal_write)
    with ThreadPoolExecutor(max_workers=2) as executor:
        slow = executor.submit(create_slow_project)
        assert gate.slow_ready.wait(timeout=5)
        fast = executor.submit(
            service.create_project,
            principal=principal,
            name="Fast committed project",
            idempotency_key="fast-project",
        )
        fast_project = fast.result(timeout=5)
        gate.allow_slow.set()
        with pytest.raises(OSError, match="simulated slow terminal write failure"):
            slow.result(timeout=5)

    assert sorted(service.projects) == [fast_project.project_id]
    assert sorted(record.idempotency_key for record in service.idempotency_records.values()) == ["fast-project"]
    assert [row["name"] for row in json.loads(state_path.read_text(encoding="utf-8"))["projects"]] == [
        "Fast committed project"
    ]


def test_stage4_file_state_ingest_write_failure_preserves_concurrent_chunks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    slow_project = service.create_project(
        principal=principal,
        name="Slow ingest write failure project",
        idempotency_key="slow-create-project",
    )
    slow_document = service.upload_document(
        principal=principal,
        project_id=slow_project.project_id,
        source_filename="slow.md",
        content_type="text/markdown",
        data=b"# Slow\n\nSlow document content.",
        idempotency_key="slow-upload-document",
    )
    fast_project = service.create_project(
        principal=principal,
        name="Fast ingest committed project",
        idempotency_key="fast-create-project",
    )
    fast_document = service.upload_document(
        principal=principal,
        project_id=fast_project.project_id,
        source_filename="fast.md",
        content_type="text/markdown",
        data=b"# Fast\n\nFast document content.",
        idempotency_key="fast-upload-document",
    )
    for project, document, key in (
        (slow_project, slow_document, "slow-approve-document"),
        (fast_project, fast_document, "fast-approve-document"),
    ):
        service.approve_document(
            principal=principal,
            project_id=project.project_id,
            document_id=document.document_id,
            idempotency_key=key,
        )

    class GateLock:
        def __init__(self) -> None:
            self._lock = threading.RLock()
            self._attempts: dict[str, int] = {}
            self.slow_ready = threading.Event()
            self.allow_slow = threading.Event()

        def __enter__(self) -> "GateLock":
            name = threading.current_thread().name
            attempt = self._attempts.get(name, 0)
            self._attempts[name] = attempt + 1
            if name == "slow" and attempt == 1:
                self.slow_ready.set()
                assert self.allow_slow.wait(timeout=5)
            self._lock.acquire()
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            self._lock.release()

    gate = GateLock()
    service._operation_lock = cast(Any, gate)

    def fail_slow_terminal_write(path: Path, payload: object) -> None:
        assert isinstance(payload, dict)
        if any(row.get("project_id") == slow_project.project_id for row in payload.get("ingestionRuns", [])):
            raise OSError("simulated slow ingestion terminal write failure")
        storage_write_state(path, payload)

    def ingest_slow_document() -> str:
        threading.current_thread().name = "slow"
        run = service.ingest_documents(
            principal=principal,
            project_id=slow_project.project_id,
            document_ids=[slow_document.document_id],
            idempotency_key="slow-ingest-document",
        )
        return run.ingestion_run_id

    monkeypatch.setattr(stage4_module, "write_state", fail_slow_terminal_write)
    with ThreadPoolExecutor(max_workers=2) as executor:
        slow = executor.submit(ingest_slow_document)
        assert gate.slow_ready.wait(timeout=5)
        fast = executor.submit(
            service.ingest_documents,
            principal=principal,
            project_id=fast_project.project_id,
            document_ids=[fast_document.document_id],
            idempotency_key="fast-ingest-document",
        )
        fast_run = fast.result(timeout=5)
        gate.allow_slow.set()
        with pytest.raises(OSError, match="simulated slow ingestion terminal write failure"):
            slow.result(timeout=5)

    assert service.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=slow_project.project_id,
    ) == 0
    assert service.rag_store.chunk_count_for_project(
        tenant_id=principal.tenant_id,
        project_id=fast_project.project_id,
    ) == fast_run.chunk_count
    assert service.documents[slow_document.document_id].ingestion_status == "NOT_STARTED"
    assert service.documents[fast_document.document_id].ingestion_status == "INGESTED"
    assert sorted(service.ingestion_runs) == [fast_run.ingestion_run_id]
    assert sorted(record.idempotency_key for record in service.idempotency_records.values()) == [
        "fast-approve-document",
        "fast-create-project",
        "fast-ingest-document",
        "fast-upload-document",
        "slow-approve-document",
        "slow-create-project",
        "slow-upload-document",
    ]


def test_stage4_file_state_failed_operation_rollback_preserves_later_success(tmp_path: Path) -> None:
    state_path = tmp_path / "stage4.json"
    principal = LocalPrincipal()
    service = Stage4Service(state_path=state_path)
    snapshot = service._runtime_snapshot_locked()
    slow_project = service.create_project(
        principal=principal,
        name="Slow failed project",
        idempotency_key="slow-project",
    )
    fast_project = service.create_project(
        principal=principal,
        name="Fast committed project",
        idempotency_key="fast-project",
    )
    slow_key = (
        principal.tenant_id,
        principal.actor_id,
        "project:create",
        "POST /api/v1/projects",
        "slow-project",
    )

    service._restore_failed_operation_locked(snapshot, record_key=slow_key, value=slow_project)

    assert sorted(service.projects) == [fast_project.project_id]
    assert sorted(record.idempotency_key for record in service.idempotency_records.values()) == ["fast-project"]


def test_stage6_file_state_replays_completed_multilingual_idempotency(tmp_path: Path) -> None:
    state_path = tmp_path / "stage6.json"
    service = create_stage6_service(state_path=state_path)

    result = service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        glossary_terms=["NarraTwin AI"],
        source_context_ref_count=1,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="translate",
    )

    restored = create_stage6_service(state_path=state_path)
    replayed = restored.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        glossary_terms=["NarraTwin AI"],
        source_context_ref_count=1,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="translate",
    )

    assert replayed.multilingual_run_id == result.multilingual_run_id
    assert replayed.artifacts.subtitles.checksum == result.artifacts.subtitles.checksum


def test_stage6_file_state_terminal_persist_failure_preserves_concurrent_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PausingTranslationProvider:
        provider = "mock"
        provider_mode = "LOCAL"

        def __init__(self) -> None:
            self._mock = stage6_module.MockTranslationProvider()
            self.slow_started = threading.Event()
            self.allow_slow_finish = threading.Event()

        def translate(
            self,
            *,
            source_text: str,
            source_language: str,
            target_language: str,
            glossary_terms: list[str],
        ) -> stage6_module.TranslationProviderResult:
            if "SLOW_FAILURE" in source_text:
                self.slow_started.set()
                assert self.allow_slow_finish.wait(timeout=5)
            return self._mock.translate(
                source_text=source_text,
                source_language=source_language,
                target_language=target_language,
                glossary_terms=glossary_terms,
            )

    state_path = tmp_path / "stage6.json"
    provider = PausingTranslationProvider()
    service = stage6_module.Stage6Service(translation_provider=provider, state_path=state_path)

    def fail_only_slow_terminal_persist(path: Path | None, payload: object) -> None:
        assert isinstance(payload, dict)
        records = payload.get("idempotencyRecords", [])
        for row in records:
            if not isinstance(row, dict):
                continue
            value = row.get("value", {})
            if isinstance(value, dict) and value.get("kind") == "result":
                result = value.get("result", {})
                if isinstance(result, dict) and result.get("source_run_id") == "run_slow_failure":
                    raise OSError("simulated slow terminal write failure")
        storage_write_state(path, payload)

    monkeypatch.setattr(stage6_module, "write_state", fail_only_slow_terminal_persist)

    def generate(run_id: str, idempotency_key: str, marker: str) -> stage6_module.MultilingualWalkthroughResult:
        return service.generate_multilingual_walkthrough(
            source_script=f"NarraTwin AI creates grounded walkthrough scripts. {marker} [1]",
            target_language="es",
            source_context_ref_count=1,
            source_run_id=run_id,
            trace_id=f"trace_{run_id}",
            idempotency_scope="tenant:user:project:run",
            idempotency_key=idempotency_key,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        slow = executor.submit(generate, "run_slow_failure", "translate-slow-failure", "SLOW_FAILURE")
        assert provider.slow_started.wait(timeout=5)
        fast = executor.submit(generate, "run_fast_success", "translate-fast-success", "FAST_SUCCESS")
        fast_result = fast.result(timeout=5)
        provider.allow_slow_finish.set()
        with pytest.raises(OSError, match="simulated slow terminal write failure"):
            slow.result(timeout=5)

    assert sorted(record.idempotency_key for record in service.idempotency_records.values()) == [
        "translate-fast-success"
    ]
    fast_record = next(iter(service.idempotency_records.values()))
    assert isinstance(fast_record.value, stage6_module.MultilingualWalkthroughResult)
    assert fast_record.value.multilingual_run_id == fast_result.multilingual_run_id

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert [row["idempotency_key"] for row in payload["idempotencyRecords"]] == ["translate-fast-success"]


def test_stage6_file_state_drops_tampered_nonlocal_provider_result(tmp_path: Path) -> None:
    state_path = tmp_path / "stage6.json"
    service = create_stage6_service(state_path=state_path)
    service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        source_context_ref_count=1,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="translate",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    result = payload["idempotencyRecords"][0]["value"]["result"]
    result["translation_provider"]["provider_mode"] = "OPTIONAL_EXTERNAL"
    result["voice"]["provider_mode"] = "OPTIONAL_EXTERNAL"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage6_service(state_path=state_path)

    assert restored.idempotency_records == {}


def test_stage6_file_state_drops_inconsistent_restored_artifact_payload(tmp_path: Path) -> None:
    state_path = tmp_path / "stage6.json"
    service = create_stage6_service(state_path=state_path)
    service.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        source_context_ref_count=1,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="translate",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    result = payload["idempotencyRecords"][0]["value"]["result"]
    result["translated_script_text"] = "tampered restored field without citation"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage6_service(state_path=state_path)

    assert restored.idempotency_records == {}


def test_stage6_file_state_drops_failed_idempotency_with_missing_error(tmp_path: Path) -> None:
    state_path = tmp_path / "stage6.json"
    request_checksum = checksum_text(
        json.dumps(
            {
                "sourceScript": "NarraTwin AI creates grounded walkthrough scripts. [1]",
                "sourceLanguage": "en",
                "targetLanguage": "es",
                "requestedVoiceProvider": "mock",
                "glossaryTerms": [],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage6-local-state-v1",
                "idempotencyRecords": [
                    {
                        "idempotency_scope": "tenant:user:project:run",
                        "endpoint": "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
                        "idempotency_key": "bad-failed",
                        "request_checksum": request_checksum,
                        "status": "FAILED",
                        "value": {"kind": "none"},
                    }
                ],
                "counters": {"run": 0},
            }
        ),
        encoding="utf-8",
    )

    restored = create_stage6_service(state_path=state_path)
    result = restored.generate_multilingual_walkthrough(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        target_language="es",
        source_context_ref_count=1,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="bad-failed",
    )

    assert result.multilingual_run_id == "mlrun_000001"
    assert len(restored.idempotency_records) == 1


def test_stage7_file_state_replays_completed_avatar_idempotency(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)

    result = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_durable",
        trace_id="trace_durable",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_durable",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_durable",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render",
    )

    restored = create_stage7_service(state_path=state_path)
    replayed = restored.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_durable",
        trace_id="trace_durable",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_durable",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_durable",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render",
    )

    assert replayed.avatar_render_id == result.avatar_render_id
    assert restored.artifact_metadata[result.avatar_render_id][0].checksum == result.artifacts.demo_export.checksum


def test_stage7_file_state_drops_tampered_nonlocal_provider_result(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_tampered",
        trace_id="trace_tampered",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_tampered",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_tampered",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["avatarRenders"][0]["avatar_provider"]["provider_mode"] = "OPTIONAL_EXTERNAL"
    payload["avatarRenders"][0]["provider_config"]["provider_mode"] = "OPTIONAL_EXTERNAL"
    payload["avatarRenders"][0]["provider_config"]["allow_network_egress"] = True
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage7_service(state_path=state_path)

    assert restored.avatar_renders == {}
    assert restored.idempotency_records == {}


def test_stage7_file_state_terminal_persist_failure_does_not_leave_orphan_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)

    def fail_terminal_persist(path: Path | None, payload: object) -> None:
        assert isinstance(payload, dict)
        avatar_renders = payload.get("avatarRenders")
        terminal_records = payload.get("idempotencyRecords")
        if avatar_renders and terminal_records:
            raise OSError("simulated terminal write failure")
        storage_write_state(path, payload)

    monkeypatch.setattr(stage7_module, "write_state", fail_terminal_persist)

    with pytest.raises(OSError, match="simulated terminal write failure"):
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            source_run_id="run_terminal_failure",
            trace_id="trace_terminal_failure",
            source_context_ref_count=1,
            source_citation_count=1,
            source_context_ref_ids=("ctx_terminal_failure",),
            source_citation_indexes=(1,),
            source_evaluation_id="eval_terminal_failure",
            evaluation_status="PASSED",
            consent_to_use_synthetic_avatar=True,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="render-terminal-failure",
        )

    assert service.avatar_renders == {}
    assert service.idempotency_records == {}
    if state_path.exists():
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        assert payload.get("avatarRenders", []) == []
        assert payload.get("idempotencyRecords", []) == []


def test_stage7_file_state_terminal_persist_failure_preserves_concurrent_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class PausingAvatarProvider:
        provider = "mock"
        provider_mode = "LOCAL"

        def __init__(self) -> None:
            self._mock = stage7_module.MockAvatarProvider()
            self.slow_started = threading.Event()
            self.allow_slow_finish = threading.Event()

        def render(
            self,
            *,
            source_script: str,
            requested_provider: str,
            fallback_reason: str | None,
            source_run_id: str,
            trace_id: str,
            source_context_ref_count: int,
            source_citation_count: int,
            source_context_ref_ids: tuple[str, ...] = (),
            source_citation_indexes: tuple[int, ...] = (),
            source_evaluation_id: str = "local_evaluation",
            source_evaluation_checksum: str = "",
            evaluation_status: str = "UNKNOWN",
        ) -> stage7_module.AvatarProviderResult:
            if source_run_id == "run_slow_failure":
                self.slow_started.set()
                assert self.allow_slow_finish.wait(timeout=5)
            return self._mock.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                source_context_ref_ids=source_context_ref_ids,
                source_citation_indexes=source_citation_indexes,
                source_evaluation_id=source_evaluation_id,
                source_evaluation_checksum=source_evaluation_checksum,
                evaluation_status=evaluation_status,
            )

    state_path = tmp_path / "stage7.json"
    provider = PausingAvatarProvider()
    service = stage7_module.Stage7Service(avatar_provider=provider, state_path=state_path)

    def fail_only_slow_terminal_persist(path: Path | None, payload: object) -> None:
        assert isinstance(payload, dict)
        avatar_renders = payload.get("avatarRenders", [])
        if any(row.get("source_run_id") == "run_slow_failure" for row in avatar_renders):
            raise OSError("simulated slow terminal write failure")
        storage_write_state(path, payload)

    monkeypatch.setattr(stage7_module, "write_state", fail_only_slow_terminal_persist)

    def render(run_id: str, idempotency_key: str) -> stage7_module.AvatarRenderResult:
        return service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            source_run_id=run_id,
            trace_id=f"trace_{run_id}",
            source_context_ref_count=1,
            source_citation_count=1,
            source_context_ref_ids=(f"ctx_{run_id}",),
            source_citation_indexes=(1,),
            source_evaluation_id=f"eval_{run_id}",
            evaluation_status="PASSED",
            consent_to_use_synthetic_avatar=True,
            idempotency_scope="tenant:user:project:run",
            idempotency_key=idempotency_key,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        slow = executor.submit(render, "run_slow_failure", "render-slow-failure")
        assert provider.slow_started.wait(timeout=5)
        fast = executor.submit(render, "run_fast_success", "render-fast-success")
        fast_result = fast.result(timeout=5)
        provider.allow_slow_finish.set()
        with pytest.raises(OSError, match="simulated slow terminal write failure"):
            slow.result(timeout=5)

    assert sorted(service.avatar_renders) == [fast_result.avatar_render_id]
    assert service.avatar_renders[fast_result.avatar_render_id].source_run_id == "run_fast_success"
    assert sorted(record.idempotency_key for record in service.idempotency_records.values()) == ["render-fast-success"]

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert [row["source_run_id"] for row in payload["avatarRenders"]] == ["run_fast_success"]
    assert [row["idempotency_key"] for row in payload["idempotencyRecords"]] == ["render-fast-success"]


def test_stage7_file_state_drops_completed_idempotency_with_missing_value(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    original = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_dangling",
        trace_id="trace_dangling",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_dangling",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_dangling",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["avatarRenders"] = []
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage7_service(state_path=state_path)
    recreated = restored.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_dangling",
        trace_id="trace_dangling",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_dangling",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_dangling",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render",
    )

    assert original.avatar_render_id == "avrun_000001"
    assert recreated.avatar_render_id == "avrun_000002"
    assert len(restored.avatar_renders) == 1


def test_stage7_file_state_drops_artifact_metadata_for_missing_render(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage7-local-state-v1",
                "avatarRenders": [],
                "artifactMetadata": [
                    {
                        "avatar_render_id": "avrun_missing",
                        "metadata": [
                            {
                                "file_name": "demo.html",
                                "mime_type": "text/html",
                                "checksum": "abc123",
                            }
                        ],
                    }
                ],
                "idempotencyRecords": [],
                "counters": {"run": 0},
            }
        ),
        encoding="utf-8",
    )

    restored = create_stage7_service(state_path=state_path)

    assert restored.avatar_renders == {}
    assert restored.artifact_metadata == {}


def test_stage7_file_state_drops_artifact_metadata_that_mismatches_render(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    result = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_metadata",
        trace_id="trace_metadata",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_metadata",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_metadata",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["artifactMetadata"][0]["metadata"][0]["checksum"] = "sha256:tampered"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage7_service(state_path=state_path)

    assert result.avatar_render_id == "avrun_000001"
    assert restored.avatar_renders[result.avatar_render_id].avatar_render_id == result.avatar_render_id
    assert restored.artifact_metadata == {}


def test_stage7_file_state_drops_failed_idempotency_with_missing_error(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    request_checksum = stage7_module.build_avatar_render_request_checksum(
        source_text="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        cloned_identity_requested=False,
        consent_to_use_synthetic_avatar=True,
        source_run_id="run_failed",
        trace_id="trace_failed",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_failed",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_failed",
        source_evaluation_checksum=None,
        evaluation_status="PASSED",
    )
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage7-local-state-v1",
                "avatarRenders": [],
                "artifactMetadata": [],
                "idempotencyRecords": [
                    {
                        "idempotency_scope": "tenant:user:project:run",
                        "endpoint": "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
                        "idempotency_key": "bad-failed",
                        "request_checksum": request_checksum,
                        "status": "FAILED",
                        "error_status_code": None,
                        "error_code": None,
                        "error_message": None,
                        "value": {"kind": "none"},
                    }
                ],
                "counters": {"run": 0},
            }
        ),
        encoding="utf-8",
    )

    restored = create_stage7_service(state_path=state_path)
    result = restored.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_failed",
        trace_id="trace_failed",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_failed",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_failed",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="bad-failed",
    )

    assert result.avatar_render_id == "avrun_000001"
    assert len(restored.idempotency_records) == 1


def test_stage7_file_state_derives_missing_counters_from_restored_ids(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    first = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_first",
        trace_id="trace_first",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_first",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_first",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render-first",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload.pop("counters")
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage7_service(state_path=state_path)
    second = restored.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_second",
        trace_id="trace_second",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_second",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_second",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render-second",
    )

    assert first.avatar_render_id == "avrun_000001"
    assert second.avatar_render_id == "avrun_000002"
    assert sorted(restored.avatar_renders) == ["avrun_000001", "avrun_000002"]


def test_stage7_file_state_derives_stale_low_counters_from_restored_ids(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    first = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_first",
        trace_id="trace_first",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_first",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_first",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render-first",
    )
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["counters"]["run"] = 0
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = create_stage7_service(state_path=state_path)
    second = restored.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_second",
        trace_id="trace_second",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_second",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_second",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant:user:project:run",
        idempotency_key="render-second",
    )

    assert first.avatar_render_id == "avrun_000001"
    assert second.avatar_render_id == "avrun_000002"
    assert sorted(restored.avatar_renders) == ["avrun_000001", "avrun_000002"]


def test_stage7_records_durable_synthetic_media_consent_and_replays_it(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    source_evaluation_checksum = stage7_module.build_source_evaluation_checksum(
        source_evaluation_id="eval_stage7",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        evaluation_status="PASSED",
        source_context_ref_ids=("ctx_stage7",),
        source_context_ref_count=1,
        source_citation_indexes=(1,),
        source_citation_count=1,
    )

    record = service.capture_synthetic_avatar_consent(
        tenant_id="tenant_local",
        project_id="proj_stage7",
        actor_id="user_local",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_ids=("ctx_stage7",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_stage7",
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant_local:user_local:proj_stage7:run_stage7",
        idempotency_key="capture-consent",
    )

    restored = create_stage7_service(state_path=state_path)
    replayed = restored.capture_synthetic_avatar_consent(
        tenant_id="tenant_local",
        project_id="proj_stage7",
        actor_id="user_local",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_ids=("ctx_stage7",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_stage7",
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant_local:user_local:proj_stage7:run_stage7",
        idempotency_key="capture-consent",
    )

    assert replayed.consent_record_id == record.consent_record_id
    assert restored.synthetic_media_consents[record.consent_record_id].actor_id == "user_local"


def test_stage7_file_state_terminal_persist_failure_restores_consent_bound_render_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "stage7.json"
    service = create_stage7_service(state_path=state_path)
    source_evaluation_checksum = stage7_module.build_source_evaluation_checksum(
        source_evaluation_id="eval_stage7",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        evaluation_status="PASSED",
        source_context_ref_ids=("ctx_stage7",),
        source_context_ref_count=1,
        source_citation_indexes=(1,),
        source_citation_count=1,
    )
    consent = service.capture_synthetic_avatar_consent(
        tenant_id="tenant_local",
        project_id="proj_stage7",
        actor_id="user_local",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_ids=("ctx_stage7",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_stage7",
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant_local:user_local:proj_stage7:run_stage7",
        idempotency_key="capture-consent",
    )

    def fail_terminal_persist(path: Path | None, payload: object) -> None:
        assert isinstance(payload, dict)
        avatar_renders = payload.get("avatarRenders", [])
        if avatar_renders:
            raise OSError("simulated terminal write failure")
        storage_write_state(path, payload)

    monkeypatch.setattr(stage7_module, "write_state", fail_terminal_persist)

    with pytest.raises(OSError, match="simulated terminal write failure"):
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            source_run_id="run_stage7",
            trace_id="trace_stage7",
            source_context_ref_count=1,
            source_citation_count=1,
            source_context_ref_ids=("ctx_stage7",),
            source_citation_indexes=(1,),
            source_evaluation_id="eval_stage7",
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status="PASSED",
            consent_to_use_synthetic_avatar=True,
            tenant_id="tenant_local",
            project_id="proj_stage7",
            actor_id="user_local",
            consent_record_id=consent.consent_record_id,
            idempotency_scope="tenant_local:user_local:proj_stage7:run_stage7",
            idempotency_key="render-stage7",
        )

    restored_consent = service.synthetic_media_consents[consent.consent_record_id]
    assert restored_consent.avatar_render_id is None
    assert restored_consent.artifact_checksums == ()
    assert service.avatar_renders == {}
    monkeypatch.setattr(stage7_module, "write_state", storage_write_state)
    replay = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_count=1,
        source_citation_count=1,
        source_context_ref_ids=("ctx_stage7",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_stage7",
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        tenant_id="tenant_local",
        project_id="proj_stage7",
        actor_id="user_local",
        consent_record_id=consent.consent_record_id,
        idempotency_scope="tenant_local:user_local:proj_stage7:run_stage7",
        idempotency_key="render-stage7-retry",
    )
    assert replay.consent_record_id == consent.consent_record_id


def test_stage7_drops_running_consent_idempotency_record_on_restore(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    request_checksum = checksum_text(
        json.dumps(
            {
                "actorId": "user_local",
                "consentStatementVersion": "stage7-synthetic-avatar-consent-v1",
                "projectId": "proj_stage7",
                "sourceEvaluationChecksum": "sha256:eval",
                "sourceEvaluationId": "eval_stage7",
                "sourceRunId": "run_stage7",
                "tenantId": "tenant_local",
                "traceId": "trace_stage7",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage7-local-state-v1",
                "avatarRenders": [],
                "artifactMetadata": [],
                "syntheticMediaConsents": [],
                "idempotencyRecords": [],
                "consentIdempotencyRecords": [
                    {
                        "idempotency_scope": "tenant_local:user_local:proj_stage7:run_stage7",
                        "endpoint": "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
                        "idempotency_key": "capture-consent",
                        "request_checksum": request_checksum,
                        "status": "RUNNING",
                        "value": {"kind": "none"},
                    }
                ],
                "counters": {"run": 0, "consent": 0},
            }
        ),
        encoding="utf-8",
    )

    restored = create_stage7_service(state_path=state_path)
    consent = restored.capture_synthetic_avatar_consent(
        tenant_id="tenant_local",
        project_id="proj_stage7",
        actor_id="user_local",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_ids=("ctx_stage7",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_stage7",
        source_evaluation_checksum="sha256:eval",
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
        idempotency_scope="tenant_local:user_local:proj_stage7:run_stage7",
        idempotency_key="capture-consent",
    )

    assert consent.consent_record_id == "consent_000001"
    assert len(restored.consent_idempotency_records) == 1


def test_stage7_drops_malformed_or_cross_boundary_consent_record_on_restore(tmp_path: Path) -> None:
    state_path = tmp_path / "stage7.json"
    expected_checksum = stage7_module.build_avatar_consent_request_checksum(
        tenant_id="tenant_local",
        project_id="proj_stage7",
        actor_id="user_local",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_ids=("ctx_stage7",),
        source_citation_indexes=(1,),
        source_evaluation_id="eval_stage7",
        source_evaluation_checksum="sha256:eval",
        evaluation_status="PASSED",
    )
    state_path.write_text(
        json.dumps(
            {
                "schema": "stage7-local-state-v1",
                "avatarRenders": [],
                "artifactMetadata": [],
                "syntheticMediaConsents": [
                    {
                        "consent_record_id": "consent_000001",
                        "tenant_id": "tenant_local",
                        "project_id": "proj_stage7",
                        "actor_id": "user_local",
                        "source_run_id": "run_stage7",
                        "trace_id": "trace_stage7",
                        "source_evaluation_id": "eval_stage7",
                        "source_evaluation_checksum": "sha256:eval",
                        "source_context_ref_ids": ["ctx_stage7"],
                        "source_citation_indexes": [1],
                        "consent_statement_version": "stage7-synthetic-avatar-consent-v1",
                        "consent_statement_text": "tampered text",
                        "granted_at": "2026-07-12T00:00:00Z",
                        "request_checksum": "sha256:req",
                        "idempotency_scope": "tenant_local:user_local:proj_stage7:run_stage7",
                        "idempotency_key": "capture-consent",
                        "avatar_render_id": None,
                        "artifact_checksums": [],
                    },
                    {
                        "consent_record_id": "consent_000002",
                        "tenant_id": "tenant_local",
                        "project_id": "proj_other",
                        "actor_id": "user_other",
                        "source_run_id": "run_other",
                        "trace_id": "trace_other",
                        "source_evaluation_id": "eval_other",
                        "source_evaluation_checksum": "sha256:other",
                        "source_context_ref_ids": ["ctx_stage7"],
                        "source_citation_indexes": [1],
                        "consent_statement_version": "stage7-synthetic-avatar-consent-v1",
                        "consent_statement_text": stage7_module.SYNTHETIC_AVATAR_CONSENT_TEXT,
                        "granted_at": "2026-07-12T00:00:00Z",
                        "request_checksum": expected_checksum,
                        "idempotency_scope": "tenant_local:user_local:proj_stage7:run_stage7",
                        "idempotency_key": "capture-consent",
                        "avatar_render_id": None,
                        "artifact_checksums": [],
                    },
                    {
                        "consent_record_id": "consent_000003",
                        "tenant_id": "tenant_local",
                        "project_id": "proj_stage7",
                        "actor_id": "user_local",
                        "source_run_id": "run_stage7",
                        "trace_id": "trace_stage7",
                        "source_evaluation_id": "eval_stage7",
                        "source_evaluation_checksum": "sha256:eval",
                        "source_context_ref_ids": ["ctx_stage7"],
                        "source_citation_indexes": [1],
                        "consent_statement_version": "stage7-synthetic-avatar-consent-v1",
                        "consent_statement_text": stage7_module.SYNTHETIC_AVATAR_CONSENT_TEXT,
                        "granted_at": "not-a-timestamp",
                        "request_checksum": expected_checksum,
                        "idempotency_scope": "tenant_local:user_local:proj_stage7:run_stage7",
                        "idempotency_key": "capture-consent",
                        "avatar_render_id": None,
                        "artifact_checksums": [],
                    }
                ],
                "idempotencyRecords": [],
                "consentIdempotencyRecords": [],
                "counters": {"run": 0, "consent": 1},
            }
        ),
        encoding="utf-8",
    )

    restored = create_stage7_service(state_path=state_path)

    assert restored.synthetic_media_consents == {}
