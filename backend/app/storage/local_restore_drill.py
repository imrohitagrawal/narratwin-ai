"""Executable local restore-integrity drill for file-backed Stage 4/6/7 state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from time import perf_counter

from backend.app.stage4 import LocalPrincipal, Stage4Service
from backend.app.stage6 import Stage6Service
from backend.app.stage7 import (
    DurableAvatarRenderScope,
    build_source_evaluation_checksum,
    create_stage7_service,
)


class LocalRestoreDrillError(RuntimeError):
    """Raised when the local restore drill cannot prove the expected invariant."""


@dataclass(frozen=True)
class StateFileIntegrity:
    service: str
    source_path: str
    restore_path: str
    byte_size: int
    sha256: str


@dataclass(frozen=True)
class RestoreDrillSummary:
    schema_version: str
    started_at: str
    completed_at: str
    elapsed_ms: int
    workdir: str
    source_state_dir: str
    restored_state_dir: str
    state_files: tuple[StateFileIntegrity, ...]
    seeded_counts: dict[str, dict[str, int]]
    restored_counts: dict[str, dict[str, int]]
    replay_ids: dict[str, str]


def run_local_restore_drill(
    *,
    workdir: Path | None = None,
    output_path: Path | None = None,
) -> RestoreDrillSummary:
    started_at = _utc_now_isoformat()
    start_clock = perf_counter()
    with tempfile.TemporaryDirectory(dir=workdir, prefix="narratwin-restore-drill-") as temp_dir:
        base_dir = Path(temp_dir)
        source_dir = base_dir / "source-state"
        restored_dir = base_dir / "restored-state"
        source_dir.mkdir(parents=True, exist_ok=True)
        restored_dir.mkdir(parents=True, exist_ok=True)

        source_paths = _state_paths(source_dir)
        restored_paths = _state_paths(restored_dir)
        seeded = _seed_source_state(source_paths)
        seeded_counts = _collect_counts(seeded["stage4"], seeded["stage6"], seeded["stage7"])
        state_files = _copy_and_verify_state_files(source_paths, restored_paths)
        restored = _restore_services(restored_paths)
        restored_counts = _collect_counts(restored["stage4"], restored["stage6"], restored["stage7"])
        if restored_counts != seeded_counts:
            raise LocalRestoreDrillError("Restored record counts do not match the seeded local state.")
        replay_ids = _assert_replay_safety(seeded, restored)

        summary = RestoreDrillSummary(
            schema_version="local-restore-drill-v1",
            started_at=started_at,
            completed_at=_utc_now_isoformat(),
            elapsed_ms=int((perf_counter() - start_clock) * 1000),
            workdir=str(base_dir),
            source_state_dir=str(source_dir),
            restored_state_dir=str(restored_dir),
            state_files=state_files,
            seeded_counts=seeded_counts,
            restored_counts=restored_counts,
            replay_ids=replay_ids,
        )
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(asdict(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return summary


def _state_paths(directory: Path) -> dict[str, Path]:
    return {
        "stage4": directory / "stage4.json",
        "stage6": directory / "stage6.json",
        "stage7": directory / "stage7.json",
    }


def _seed_source_state(paths: dict[str, Path]) -> dict[str, object]:
    principal = LocalPrincipal()
    stage4 = Stage4Service(state_path=paths["stage4"])
    project = stage4.create_project(
        principal=principal,
        name="Restore drill project",
        idempotency_key="restore-drill-create-project",
    )
    document = stage4.upload_document(
        principal=principal,
        project_id=project.project_id,
        source_filename="project.md",
        content_type="text/markdown",
        data=Path("tests/fixtures/stage4_project.md").read_bytes(),
        idempotency_key="restore-drill-upload-document",
    )
    stage4.approve_document(
        principal=principal,
        project_id=project.project_id,
        document_id=document.document_id,
        idempotency_key="restore-drill-approve-document",
    )
    stage4.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=[document.document_id],
        idempotency_key="restore-drill-ingest-document",
    )
    walkthrough = stage4.generate_walkthrough(
        principal=principal,
        project_id=project.project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="restore-drill-generate-walkthrough",
    )
    source_script = walkthrough.accepted_script_text
    if source_script is None or walkthrough.generated_script is None or walkthrough.evaluation is None:
        raise LocalRestoreDrillError("Stage 4 walkthrough seed did not produce the required grounded artifacts.")

    context_ref_ids = tuple(item.context_ref_id for item in walkthrough.retrieved_context)
    citation_indexes = tuple(claim.citation_index for claim in walkthrough.generated_script.claims)
    claim_support_ids = tuple(item.claim_support_id for item in walkthrough.evaluation.claim_supports)
    evaluation_checksum = build_source_evaluation_checksum(
        source_evaluation_id=walkthrough.evaluation.evaluation_id,
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        evaluation_status=walkthrough.evaluation.evaluation_status,
        source_context_ref_ids=context_ref_ids,
        source_context_ref_count=len(context_ref_ids),
        source_citation_indexes=citation_indexes,
        source_citation_count=len(citation_indexes),
    )

    stage6_scope = f"{principal.tenant_id}:{principal.actor_id}:{project.project_id}:{walkthrough.run_id}"
    stage6 = Stage6Service(state_path=paths["stage6"])
    multilingual = stage6.generate_multilingual_walkthrough(
        source_script=source_script,
        source_language="en",
        target_language="es",
        requested_voice_provider="mock",
        glossary_terms=["NarraTwin AI"],
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
        actor_id=principal.actor_id,
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        source_context_ref_count=len(context_ref_ids),
        source_citation_count=len(citation_indexes),
        source_context_ref_ids=context_ref_ids,
        source_citation_indexes=citation_indexes,
        source_claim_support_ids=claim_support_ids,
        source_evaluation_id=walkthrough.evaluation.evaluation_id,
        source_evaluation_checksum=evaluation_checksum,
        evaluation_status=walkthrough.evaluation.evaluation_status,
        idempotency_scope=stage6_scope,
        idempotency_key="restore-drill-stage6",
    )

    stage7_scope = f"{principal.tenant_id}:{principal.actor_id}:{project.project_id}:{walkthrough.run_id}"
    stage7 = create_stage7_service(state_path=paths["stage7"])
    consent = stage7.capture_synthetic_avatar_consent(
        tenant_id=principal.tenant_id,
        project_id=project.project_id,
        actor_id=principal.actor_id,
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        source_context_ref_ids=context_ref_ids,
        source_citation_indexes=citation_indexes,
        source_evaluation_id=walkthrough.evaluation.evaluation_id,
        source_evaluation_checksum=evaluation_checksum,
        evaluation_status=walkthrough.evaluation.evaluation_status,
        consent_to_use_synthetic_avatar=True,
        idempotency_scope=stage7_scope,
        idempotency_key="restore-drill-stage7-consent",
    )
    render = stage7.render_avatar_demo(
        source_script=source_script,
        requested_avatar_provider="mock",
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        source_context_ref_count=len(context_ref_ids),
        source_citation_count=len(citation_indexes),
        source_context_ref_ids=context_ref_ids,
        source_citation_indexes=citation_indexes,
        source_evaluation_id=walkthrough.evaluation.evaluation_id,
        source_evaluation_checksum=evaluation_checksum,
        evaluation_status=walkthrough.evaluation.evaluation_status,
        consent_to_use_synthetic_avatar=True,
        durable_consent=DurableAvatarRenderScope(
            tenant_id=principal.tenant_id,
            project_id=project.project_id,
            actor_id=principal.actor_id,
            consent_record_id=consent.consent_record_id,
        ),
        idempotency_scope=stage7_scope,
        idempotency_key="restore-drill-stage7-render",
    )

    return {
        "principal": principal,
        "project_id": project.project_id,
        "document_id": document.document_id,
        "walkthrough": walkthrough,
        "stage4": stage4,
        "stage6": stage6,
        "stage7": stage7,
        "context_ref_ids": context_ref_ids,
        "citation_indexes": citation_indexes,
        "claim_support_ids": claim_support_ids,
        "evaluation_checksum": evaluation_checksum,
        "stage6_scope": stage6_scope,
        "stage7_scope": stage7_scope,
        "stage6_result": multilingual,
        "consent": consent,
        "render": render,
    }


def _copy_and_verify_state_files(
    source_paths: dict[str, Path],
    restored_paths: dict[str, Path],
) -> tuple[StateFileIntegrity, ...]:
    reports: list[StateFileIntegrity] = []
    for service in ("stage4", "stage6", "stage7"):
        source_path = source_paths[service]
        restore_path = restored_paths[service]
        shutil.copy2(source_path, restore_path)
        source_bytes = source_path.read_bytes()
        restored_bytes = restore_path.read_bytes()
        if source_bytes != restored_bytes:
            raise LocalRestoreDrillError(f"Restored {service} state file content does not match the source snapshot.")
        reports.append(
            StateFileIntegrity(
                service=service,
                source_path=str(source_path),
                restore_path=str(restore_path),
                byte_size=len(source_bytes),
                sha256=hashlib.sha256(source_bytes).hexdigest(),
            )
        )
    return tuple(reports)


def _restore_services(paths: dict[str, Path]) -> dict[str, object]:
    return {
        "stage4": Stage4Service(state_path=paths["stage4"]),
        "stage6": Stage6Service(state_path=paths["stage6"]),
        "stage7": create_stage7_service(state_path=paths["stage7"]),
    }


def _collect_counts(stage4: Stage4Service, stage6: Stage6Service, stage7: object) -> dict[str, dict[str, int]]:
    return {
        "stage4": {
            "projects": len(stage4.projects),
            "documents": len(stage4.documents),
            "ingestionRuns": len(stage4.ingestion_runs),
            "walkthroughRuns": len(stage4.walkthrough_runs),
            "idempotencyRecords": len(stage4.idempotency_records),
            "ragChunks": sum(len(chunks) for chunks in stage4.rag_store._chunks_by_project.values()),
        },
        "stage6": {
            "multilingualRuns": len(stage6.multilingual_runs),
            "idempotencyRecords": len(stage6.idempotency_records),
            "requestDedupeIndex": len(stage6.request_dedupe_index),
        },
        "stage7": {
            "consents": len(stage7.synthetic_media_consents),
            "renders": len(stage7.avatar_renders),
            "artifactMetadata": len(stage7.artifact_metadata),
            "renderIdempotencyRecords": len(stage7.idempotency_records),
            "consentIdempotencyRecords": len(stage7.consent_idempotency_records),
        },
    }


def _assert_replay_safety(seeded: dict[str, object], restored: dict[str, object]) -> dict[str, str]:
    principal = seeded["principal"]
    walkthrough = seeded["walkthrough"]
    stage4 = restored["stage4"]
    stage6 = restored["stage6"]
    stage7 = restored["stage7"]
    project_id = seeded["project_id"]
    context_ref_ids = seeded["context_ref_ids"]
    citation_indexes = seeded["citation_indexes"]
    claim_support_ids = seeded["claim_support_ids"]
    evaluation_checksum = seeded["evaluation_checksum"]
    source_script = walkthrough.accepted_script_text
    evaluation = walkthrough.evaluation
    if source_script is None or evaluation is None:
        raise LocalRestoreDrillError("Restored replay check is missing grounded Stage 4 source artifacts.")

    replayed_project = stage4.create_project(
        principal=principal,
        name="Restore drill project",
        idempotency_key="restore-drill-create-project",
    )
    replayed_walkthrough = stage4.generate_walkthrough(
        principal=principal,
        project_id=project_id,
        audience="RECRUITER",
        requested_language="en",
        depth="CONCISE",
        style="CONFIDENT",
        prompt="Create a concise grounded walkthrough for a recruiter.",
        idempotency_key="restore-drill-generate-walkthrough",
    )
    replayed_stage6 = stage6.generate_multilingual_walkthrough(
        source_script=source_script,
        source_language="en",
        target_language="es",
        requested_voice_provider="mock",
        glossary_terms=["NarraTwin AI"],
        tenant_id=principal.tenant_id,
        project_id=project_id,
        actor_id=principal.actor_id,
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        source_context_ref_count=len(context_ref_ids),
        source_citation_count=len(citation_indexes),
        source_context_ref_ids=context_ref_ids,
        source_citation_indexes=citation_indexes,
        source_claim_support_ids=claim_support_ids,
        source_evaluation_id=evaluation.evaluation_id,
        source_evaluation_checksum=evaluation_checksum,
        evaluation_status=evaluation.evaluation_status,
        idempotency_scope=seeded["stage6_scope"],
        idempotency_key="restore-drill-stage6",
    )
    replayed_consent = stage7.capture_synthetic_avatar_consent(
        tenant_id=principal.tenant_id,
        project_id=project_id,
        actor_id=principal.actor_id,
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        source_context_ref_ids=context_ref_ids,
        source_citation_indexes=citation_indexes,
        source_evaluation_id=evaluation.evaluation_id,
        source_evaluation_checksum=evaluation_checksum,
        evaluation_status=evaluation.evaluation_status,
        consent_to_use_synthetic_avatar=True,
        idempotency_scope=seeded["stage7_scope"],
        idempotency_key="restore-drill-stage7-consent",
    )
    replayed_render = stage7.render_avatar_demo(
        source_script=source_script,
        requested_avatar_provider="mock",
        source_run_id=walkthrough.run_id,
        trace_id=walkthrough.trace_id,
        source_context_ref_count=len(context_ref_ids),
        source_citation_count=len(citation_indexes),
        source_context_ref_ids=context_ref_ids,
        source_citation_indexes=citation_indexes,
        source_evaluation_id=evaluation.evaluation_id,
        source_evaluation_checksum=evaluation_checksum,
        evaluation_status=evaluation.evaluation_status,
        consent_to_use_synthetic_avatar=True,
        durable_consent=DurableAvatarRenderScope(
            tenant_id=principal.tenant_id,
            project_id=project_id,
            actor_id=principal.actor_id,
            consent_record_id=seeded["consent"].consent_record_id,
        ),
        idempotency_scope=seeded["stage7_scope"],
        idempotency_key="restore-drill-stage7-render",
    )

    expected_ids = {
        "stage4ProjectId": seeded["project_id"],
        "stage4RunId": walkthrough.run_id,
        "stage6RunId": seeded["stage6_result"].multilingual_run_id,
        "stage7ConsentId": seeded["consent"].consent_record_id,
        "stage7RenderId": seeded["render"].avatar_render_id,
    }
    replayed_ids = {
        "stage4ProjectId": replayed_project.project_id,
        "stage4RunId": replayed_walkthrough.run_id,
        "stage6RunId": replayed_stage6.multilingual_run_id,
        "stage7ConsentId": replayed_consent.consent_record_id,
        "stage7RenderId": replayed_render.avatar_render_id,
    }
    if replayed_ids != expected_ids:
        raise LocalRestoreDrillError("Replayed restored operations did not return the original durable identifiers.")
    return replayed_ids


def _utc_now_isoformat() -> str:
    return datetime.now(UTC).isoformat()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the local NarraTwin restore-integrity drill.")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Optional parent directory for the temporary drill workspace.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path for the JSON drill summary.",
    )
    args = parser.parse_args()
    summary = run_local_restore_drill(workdir=args.workdir, output_path=args.output)
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
