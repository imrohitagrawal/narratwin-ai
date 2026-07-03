from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading

import pytest

import backend.app.stage4 as stage4_module
import backend.app.stage6 as stage6_module
import backend.app.stage7 as stage7_module
from backend.app.storage import write_state as storage_write_state
from backend.app.stage4 import LocalPrincipal, Stage4Error, Stage4Service
from backend.app.stage6 import create_stage6_service
from backend.app.stage7 import create_stage7_service


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
        data=b"NarraTwin AI creates grounded walkthrough scripts for recruiters.",
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
