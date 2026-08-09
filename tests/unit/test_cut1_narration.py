from __future__ import annotations

import hashlib
import importlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

from backend.app.presenter_registry import PresenterLifecycle, load_cut1_presenter_registry
from backend.app.rag.chunking import checksum_text, count_tokens
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import GeneratedScript, KnowledgeChunk, RetrievedContext, ScriptClaim
from backend.app.stage4 import LocalPrincipal, ProjectRecord, Stage4Service, WalkthroughRunRecord


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-08-08T18:10:00+00:00"
ORIGINAL_OPENING = "Hey, hi! I’m Meera, a synthetic AI presenter for NarraTwin AI."
AMENDED_OPENING = "Hello, everyone, and a very warm welcome to NarraTwin AI. I’m Meera, and I’ll be your host for this walkthrough."
MEERA_TEXT = """Hello, everyone, and a very warm welcome to NarraTwin AI. I’m Meera, and I’ll be your host for this walkthrough.

StackClimb is the technology and product innovation brand founded, owned, and led by Rohit Agrawal. NarraTwin AI is a product he conceived, owns, and produces under StackClimb.

Complex projects often contain valuable knowledge spread across documents, code, architecture notes, and technical decisions. NarraTwin AI is designed to turn that information into a clear, guided project walkthrough.

The process begins with approved project material. NarraTwin organizes the content, retrieves the most relevant context, and creates an audience-aware explanation. Important claims are evaluated against their supporting sources, helping the walkthrough remain transparent and grounded instead of presenting unsupported information as fact.

The application combines a Python and FastAPI backend, a Next.js user experience, retrieval-augmented generation, evaluation and safety controls, multilingual content, captions, speech, and synthetic-presenter media. Its provider-neutral design allows individual technologies to change while preserving the same project-understanding workflow.

This approach can also be applied to other projects. Once their approved documentation is supplied, NarraTwin can create a tailored explanation of their purpose, architecture, technologies, capabilities, important decisions, and possible integrations.

For this first experience, I’m presenting a prepared walkthrough. Interactive questions and answers are planned as a future capability and are not part of this demonstration.

That is NarraTwin AI: a StackClimb product designed to transform approved project knowledge into clear, grounded, presenter-led experiences. I’m Meera. Thank you for joining me, and I look forward to guiding you through more projects."""
HASHES = {
    "meera": "fe9e874748d365a9ebb333426b0e69877cbdbca725ea7082c02334eb724031f0",
    "myra": "dd05b795b142e5d18ef0c10a8c6b7dc6873235179efc9d661ad7902cf16463d6",
    "raj": "6972ba4d9d9e5da57fadcddf5f9519d9d18a3e3beec4147eb9ad95ff9e178546",
}
BYTE_LENGTHS = {"meera": 1_868, "myra": 1_866, "raj": 1_864}


@pytest.fixture
def narration() -> ModuleType:
    try:
        return importlib.import_module("backend.app.narration")
    except ModuleNotFoundError:
        pytest.fail("Issue #382 narration contract module is absent")


def _visible(text: str) -> tuple[str, list[ScriptClaim]]:
    source_sentences = list(re.finditer(r"\S.*?[.!?](?=\s|$)", text, re.DOTALL))
    rendered: list[str] = []
    claims: list[ScriptClaim] = []
    cursor = 0
    for index, match in enumerate(source_sentences, start=1):
        gap = text[cursor : match.start()]
        sentence = match.group(0)
        marker = f" [{(index - 1) % 6 + 1}]"
        start = sum(len(part) for part in rendered) + len(gap)
        rendered.extend((gap, sentence, marker))
        claims.append(ScriptClaim(
            claim_id=f"claim_{index:03d}", text=sentence,
            citation_index=(index - 1) % 6 + 1, chunk_id=f"chunk_{(index - 1) % 6 + 1:03d}",
            script_span_start=start, script_span_end=start + len(sentence) + len(marker),
        ))
        cursor = match.end()
    rendered.append(text[cursor:])
    return "".join(rendered), claims


def _stage4(text: str = MEERA_TEXT, *, project_name: str = "NarraTwin AI") -> tuple[Stage4Service, LocalPrincipal, str]:
    principal = LocalPrincipal()
    service = Stage4Service()
    project_id, run_id = "proj_narration", "run_narration"
    service.projects[project_id] = ProjectRecord(
        project_id, principal.tenant_id, principal.actor_id, project_name,
        "Grounded narration fixture", "GENERAL", "en", NOW, NOW,
    )
    visible, claims = _visible(text)
    contexts: list[RetrievedContext] = []
    for citation_index in range(1, 7):
        supported = "\n".join(claim.text for claim in claims if claim.citation_index == citation_index)
        chunk = KnowledgeChunk(
            chunk_id=f"chunk_{citation_index:03d}", tenant_id=principal.tenant_id,
            project_id=project_id, document_id=f"doc_{(citation_index - 1) // 3 + 1:03d}",
            source_filename="approved.md",
            source_document_checksum=checksum_text(text), approved_at=NOW, chunk_index=citation_index - 1,
            text=supported, token_count=count_tokens(supported), checksum=checksum_text(supported),
            heading_path=[project_name], line_start=1, line_end=1,
        )
        contexts.append(RetrievedContext(f"ctx_{citation_index:016x}", chunk, 1.0))
    generated = GeneratedScript(visible, claims)
    evaluation = evaluate_grounding(
        tenant_id=principal.tenant_id, project_id=project_id, run_id=run_id,
        candidate=generated, retrieved_context=contexts, prompt=text, all_chunks=[row.chunk for row in contexts],
    )
    evaluation = replace(
        evaluation, retrieval_strategy_version="stage4-rag-v1", retrieval_top_k=6,
        retrieval_score_threshold=0.72,
    )
    service.walkthrough_runs[run_id] = WalkthroughRunRecord(
        run_id, principal.tenant_id, principal.actor_id, project_id, "COMPLETED", None, "PASSED",
        "trace_stage4_narration", 1, 1, 1, 0.0, "GENERAL", "en", "CONCISE", "CONFIDENT",
        visible, generated, contexts, evaluation, NOW, checksum_text("request"),
        "stage4-rag-v1", 6, 0.72,
    )
    return service, principal, project_id


def _registry_binding(presenter_id: str = "meera") -> tuple[Any, Any]:
    registry = load_cut1_presenter_registry(asset_root=ROOT)
    identity = registry.get(presenter_id, "1.0.0")
    assert identity.asset is not None
    binding = registry.bind_for_trace(
        presenter_id=presenter_id, presenter_version="1.0.0",
        trace_id=f"trace_narration_{presenter_id}", asset_sha256=identity.asset.sha256,
        voice_reference_id=identity.voice.reference_id,
        voice_reference_version=identity.voice.version,
    )
    return registry, binding


def _service(narration: ModuleType, tmp_path: Path, presenter_id: str = "meera", text: str | None = None) -> tuple[Any, Any, Any, str]:
    selected = MEERA_TEXT.replace("Meera", presenter_id.title()) if text is None else text
    stage4, principal, project_id = _stage4(selected)
    registry, binding = _registry_binding(presenter_id)
    service = narration.NarrationService(
        stage4=stage4, registry=registry, state_path=tmp_path / "narration.json",
        clock=lambda: datetime(2026, 8, 8, 18, 10, tzinfo=UTC),
    )
    return service, principal, binding, project_id


def _draft(narration: ModuleType, tmp_path: Path, presenter_id: str = "meera", text: str | None = None) -> tuple[Any, Any, Any, str]:
    service, principal, binding, project_id = _service(narration, tmp_path, presenter_id, text)
    run = service.stage4.walkthrough_runs["run_narration"]
    draft = service.create_draft(
        principal=principal, project_id=project_id, source_run_id=run.run_id,
        presenter_binding=binding, review_text=run.accepted_script_text,
    )
    return service, principal, draft, project_id


def _approve(narration: ModuleType, tmp_path: Path) -> tuple[Any, Any, Any, str]:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    required = service.request_evaluation(
        principal=principal, project_id=project_id, narration_version=draft.version,
        narration_checksum=draft.narration_checksum,
    )
    evaluated = service.evaluate(
        principal=principal, project_id=project_id, narration_version=required.version,
        narration_checksum=required.narration_checksum,
    )
    approved = service.approve_for_speech(
        principal=principal, project_id=project_id, narration_version=evaluated.version,
        narration_checksum=evaluated.narration_checksum, approver_id=principal.actor_id,
    )
    return service, principal, approved, project_id


def _assert_code(narration: ModuleType, code: str, operation: Callable[[], object]) -> None:
    with pytest.raises(narration.NarrationError) as caught:
        operation()
    assert caught.value.code == code
    assert len(str(caught.value)) <= 160


@pytest.mark.parametrize("presenter_id", ["meera", "myra", "raj"])
def test_f382_01_03_exact_owner_text_substitutions_and_brand(narration: ModuleType, presenter_id: str) -> None:
    expected = MEERA_TEXT if presenter_id == "meera" else MEERA_TEXT.replace("Meera", presenter_id.title())
    actual = narration.canonical_presenter_text(presenter_id)
    assert actual == expected
    assert actual.split("\n\n", 1)[0] == AMENDED_OPENING.replace("Meera", presenter_id.title())
    assert len(actual.split("\n\n")) == 8
    assert len(actual.encode()) == BYTE_LENGTHS[presenter_id]
    assert hashlib.sha256(actual.encode()).hexdigest() == HASHES[presenter_id]
    assert actual.count(presenter_id.title()) == 2
    assert actual.replace(presenter_id.title(), "Meera") == MEERA_TEXT
    assert "StackClimb" in actual and "stackclimb.com" not in actual and "®" not in actual
    assert "planned as a future capability" in actual


def test_f382_01_03_owner_amendment_changes_only_original_opening() -> None:
    historical = MEERA_TEXT.replace(AMENDED_OPENING, ORIGINAL_OPENING, 1)
    assert hashlib.sha256(historical.encode()).hexdigest() == (
        "2ce08a2e573ad0af0d77d818d8b2ffac018f587a711e10164c724c817a7ad4fc"
    )
    assert historical.split("\n\n")[1:] == MEERA_TEXT.split("\n\n")[1:]


@pytest.mark.parametrize("mutation", ["extra", "missing", "punctuation", "whitespace", "paragraph", "brand", "domain", "attribution"])
def test_f382_01_03_canonical_drift_fails(narration: ModuleType, mutation: str) -> None:
    values = {
        "extra": MEERA_TEXT + " Meera", "missing": MEERA_TEXT.replace("Meera", "", 1),
        "punctuation": MEERA_TEXT.replace("Hello, everyone,", "Hello everyone,", 1),
        "whitespace": MEERA_TEXT.replace("\n\nStackClimb", "\nStackClimb"),
        "paragraph": MEERA_TEXT.replace("\n\nComplex", "\n\n\nComplex"),
        "brand": MEERA_TEXT.replace("StackClimb", "Stack Climb", 1),
        "domain": MEERA_TEXT + " stackclimb.com", "attribution": MEERA_TEXT.replace("founded, owned, and led", "led"),
    }
    _assert_code(narration, "CANONICAL_NARRATION_DRIFT", lambda: narration.validate_canonical_text("meera", values[mutation]))


def test_f382_20_spoken_projection_removes_only_validated_markers(narration: ModuleType) -> None:
    review = "Version 2.0 remains in 2026 [note]. Grounded claim. [1] Ordinary 42 stays. [2]"
    assert narration.spoken_projection(review, (1, 2)) == (
        "Version 2.0 remains in 2026 [note]. Grounded claim. Ordinary 42 stays."
    )
    assert narration.spoken_projection("Keep [2026] and remove [1].", (1,)) == "Keep [2026] and remove."


def test_f382_04_07_lifecycle_is_ordered_and_approval_is_explicit(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    assert draft.state == narration.NarrationState.DRAFT and draft.evaluation is None and draft.approval is None
    _assert_code(narration, "LIFECYCLE_INVALID", lambda: service.approve_for_speech(
        principal=principal, project_id=project_id, narration_version=draft.version,
        narration_checksum=draft.narration_checksum, approver_id=principal.actor_id,
    ))
    required = service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    evaluated = service.evaluate(principal=principal, project_id=project_id,
        narration_version=required.version, narration_checksum=required.narration_checksum)
    assert evaluated.state == narration.NarrationState.EVALUATED and evaluated.evaluation.result == "PASSED"
    approved = service.approve_for_speech(principal=principal, project_id=project_id,
        narration_version=evaluated.version, narration_checksum=evaluated.narration_checksum,
        approver_id=principal.actor_id)
    assert approved.state == narration.NarrationState.APPROVED_FOR_SPEECH
    assert approved.approval.approver_id == principal.actor_id
    assert approved.approval.approved_at == NOW


@pytest.mark.parametrize("operation", ["evaluate_draft", "approve_draft", "consume_draft", "request_twice", "evaluate_twice", "approve_twice"])
def test_f382_05_every_illegal_transition_fails(narration: ModuleType, tmp_path: Path, operation: str) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    kwargs = dict(principal=principal, project_id=project_id, narration_version=draft.version,
                  narration_checksum=draft.narration_checksum)
    if operation == "evaluate_draft":
        call = partial(service.evaluate, **kwargs)
    elif operation == "approve_draft":
        call = partial(service.approve_for_speech, **kwargs, approver_id=principal.actor_id)
    elif operation == "consume_draft":
        call = partial(service.consume_for_tts, **kwargs, request_id="consume_1", trace_id="trace_tts_1")
    else:
        required = service.request_evaluation(**kwargs)
        if operation == "request_twice":
            call = partial(service.request_evaluation, **kwargs)
        else:
            evaluated = service.evaluate(**kwargs)
            if operation == "evaluate_twice":
                call = partial(service.evaluate, **kwargs)
            else:
                service.approve_for_speech(**kwargs, approver_id=principal.actor_id)
                call = partial(service.approve_for_speech, **kwargs, approver_id=principal.actor_id)
            assert evaluated.version == required.version
    _assert_code(narration, "LIFECYCLE_INVALID", call)


def test_f382_06_12_14_current_passing_grounding_is_required(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    run = service.stage4.walkthrough_runs["run_narration"]
    service.stage4.walkthrough_runs[run.run_id] = replace(run, accepted_script_text=run.accepted_script_text + " Foreign claim. [1]")
    evaluated = service.evaluate(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    assert evaluated.evaluation.result == "FAILED"
    _assert_code(narration, "EVALUATION_FAILED", lambda: service.approve_for_speech(
        principal=principal, project_id=project_id, narration_version=draft.version,
        narration_checksum=draft.narration_checksum, approver_id=principal.actor_id,
    ))


@pytest.mark.parametrize("mutation", ["missing_citation", "failed_evaluation", "foreign_context"])
def test_f382_06_12_13_distinct_grounding_failures_do_not_collapse(
    narration: ModuleType, tmp_path: Path, mutation: str
) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    run = service.stage4.walkthrough_runs["run_narration"]
    if mutation == "missing_citation":
        service.stage4.walkthrough_runs[run.run_id] = replace(
            run, accepted_script_text=run.accepted_script_text.replace(" [1]", "", 1)
        )
    elif mutation == "failed_evaluation":
        service.stage4.walkthrough_runs[run.run_id] = replace(
            run, evaluation_status="FAILED", evaluation=replace(run.evaluation, evaluation_status="FAILED")
        )
    else:
        foreign = replace(run.retrieved_context[0].chunk, project_id="proj_foreign")
        service.stage4.walkthrough_runs[run.run_id] = replace(
            run, retrieved_context=[replace(run.retrieved_context[0], chunk=foreign), *run.retrieved_context[1:]]
        )
    evaluated = service.evaluate(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    assert evaluated.evaluation.result == "FAILED"


@pytest.mark.parametrize("mutation", ["empty", "duplicate"])
def test_f382_13_missing_or_duplicate_support_identity_fails(
    narration: ModuleType, tmp_path: Path, mutation: str
) -> None:
    service, principal, binding, project_id = _service(narration, tmp_path)
    run = service.stage4.walkthrough_runs["run_narration"]
    supports = list(run.evaluation.claim_supports)
    if mutation == "empty":
        supports = []
    else:
        supports[1] = replace(supports[1], claim_support_id=supports[0].claim_support_id)
    service.stage4.walkthrough_runs[run.run_id] = replace(
        run, evaluation=replace(run.evaluation, claim_supports=supports)
    )
    _assert_code(narration, "EVIDENCE_INVALID", lambda: service.create_draft(
        principal=principal, project_id=project_id, source_run_id=run.run_id,
        presenter_binding=binding, review_text=run.accepted_script_text))


def test_f382_08_10_checksum_binds_every_authority_leaf(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    payload = draft.checksum_payload()
    assert narration.checksum_payload(payload) == draft.narration_checksum
    for path in narration.authoritative_leaf_paths(payload):
        mutated = json.loads(json.dumps(payload))
        cursor: Any = mutated
        for key in path[:-1]:
            cursor = cursor[key]
        value = cursor[path[-1]]
        cursor[path[-1]] = value + 1 if type(value) is int else str(value) + "x"
        assert narration.checksum_payload(mutated) != draft.narration_checksum
    assert service.latest(principal=principal, project_id=project_id) == draft


@pytest.mark.parametrize("boundary", ["tenant", "actor", "project", "presenter", "registry", "version", "checksum"])
def test_f382_09_10_18_cross_boundary_and_stale_inputs_fail(narration: ModuleType, tmp_path: Path, boundary: str) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    kwargs: dict[str, Any] = dict(principal=principal, project_id=project_id,
        narration_version=approved.version, narration_checksum=approved.narration_checksum,
        request_id="consume_1", trace_id="trace_tts_1")
    if boundary == "tenant":
        kwargs["principal"] = replace(principal, tenant_id="tenant_foreign")
    elif boundary == "actor":
        kwargs["principal"] = replace(principal, actor_id="actor_foreign")
    elif boundary == "project":
        kwargs["project_id"] = "proj_foreign"
    elif boundary == "version":
        kwargs["narration_version"] = approved.version + 1
    elif boundary == "checksum":
        kwargs["narration_checksum"] = "sha256:" + "0" * 64
    elif boundary == "presenter":
        service._versions[project_id][-1] = replace(approved, presenter_id="raj")
    else:
        service._versions[project_id][-1] = replace(approved, registry_sha256="0" * 64)
    _assert_code(narration, "AUTHORITY_MISMATCH", lambda: service.consume_for_tts(**kwargs))


@pytest.mark.parametrize("lifecycle", [PresenterLifecycle.REVOKED, PresenterLifecycle.DELETED, PresenterLifecycle.DISABLED])
def test_f382_11_inactive_presenter_cannot_authorize_speech(narration: ModuleType, tmp_path: Path, lifecycle: PresenterLifecycle) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    if lifecycle is PresenterLifecycle.DISABLED:
        service.registry._identities["meera"] = replace(service.registry._identities["meera"], lifecycle=lifecycle)
    else:
        service.registry.transition("meera", lifecycle)
    _assert_code(narration, "PRESENTER_INACTIVE", lambda: service.consume_for_tts(
        principal=principal, project_id=project_id, narration_version=approved.version,
        narration_checksum=approved.narration_checksum, request_id="consume_1", trace_id="trace_tts_1",
    ))


def test_f382_15_17_edit_versions_and_invalidates_every_authority(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    run = service.stage4.walkthrough_runs["run_narration"]
    edited = service.edit(principal=principal, project_id=project_id, source_run_id=run.run_id,
        presenter_binding=approved.presenter_binding, review_text=run.accepted_script_text)
    assert edited.version == approved.version + 1 and edited.state == narration.NarrationState.DRAFT
    assert set(edited.invalidated_authorities) == {
        "EVALUATION", "SPEECH_APPROVAL", "TTS_AUDIO", "CAPTION", "RENDER", "VIDEO_EXPORT", "REPLAY",
    }
    assert (edited.invalidated_version, edited.invalidated_checksum) == (
        approved.version, approved.narration_checksum
    )
    _assert_code(narration, "AUTHORITY_STALE", lambda: service.consume_for_tts(
        principal=principal, project_id=project_id, narration_version=approved.version,
        narration_checksum=approved.narration_checksum, request_id="consume_old", trace_id="trace_tts_old",
    ))


def test_f382_18_19_consumption_is_latest_single_use_bound_text_receipt(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    receipt = service.consume_for_tts(principal=principal, project_id=project_id,
        narration_version=approved.version, narration_checksum=approved.narration_checksum,
        request_id="consume_1", trace_id="trace_tts_1")
    assert receipt.spoken_text == MEERA_TEXT and receipt.presenter_id == "meera"
    assert receipt.evaluation_checksum == approved.evaluation.checksum
    assert receipt.approval_checksum == approved.approval.checksum
    assert receipt.duration_requirement_seconds == (90, 120)
    assert not hasattr(receipt, "audio") and not hasattr(receipt, "duration_seconds")
    _assert_code(narration, "CONSUMPTION_REPLAY", lambda: service.consume_for_tts(
        principal=principal, project_id=project_id, narration_version=approved.version,
        narration_checksum=approved.narration_checksum, request_id="consume_1", trace_id="trace_tts_1",
    ))


def test_f382_06_19_evaluation_approval_and_receipt_chains_reject_tampering(
    narration: ModuleType, tmp_path: Path
) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    forged_evaluation = replace(approved.evaluation, checksum="sha256:" + "0" * 64)
    service._versions[project_id][-1] = replace(approved, evaluation=forged_evaluation)
    _assert_code(narration, "AUTHORITY_MISMATCH", lambda: service.consume_for_tts(
        principal=principal, project_id=project_id, narration_version=approved.version,
        narration_checksum=approved.narration_checksum, request_id="consume_1", trace_id="trace_tts_1",
    ))


def test_f382_08_claim_checksum_binds_complete_claim_support_evidence(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    evidence = json.loads(draft.claim_evidence_json)
    assert set(evidence) == {"claims", "supports"} and evidence["claims"] and evidence["supports"]
    run = service.stage4.walkthrough_runs["run_narration"]
    changed = replace(run.evaluation.claim_supports[0], support_reason="forged support")
    service.stage4.walkthrough_runs[run.run_id] = replace(
        run, evaluation=replace(run.evaluation, claim_supports=[changed, *run.evaluation.claim_supports[1:]])
    )
    service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    evaluated = service.evaluate(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    assert evaluated.evaluation.result == "FAILED"


def test_f382_22_unknown_command_field_is_rejected(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    with pytest.raises(TypeError):
        service.request_evaluation(principal=principal, project_id=project_id,
            narration_version=draft.version, narration_checksum=draft.narration_checksum,
            unknown=True)


@pytest.mark.parametrize("value", ["", " ", "x" * 16_385], ids=["empty", "blank", "oversized"])
def test_f382_21_empty_and_oversized_text_fails(narration: ModuleType, tmp_path: Path, value: str) -> None:
    service, principal, binding, project_id = _service(narration, tmp_path)
    _assert_code(narration, "TEXT_INVALID", lambda: service.create_draft(
        principal=principal, project_id=project_id, source_run_id="run_narration",
        presenter_binding=binding, review_text=value,
    ))


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "utf8", "checksum", "timestamp", "oversized"])
def test_f382_21_25_persistence_fails_closed(narration: ModuleType, tmp_path: Path, mutation: str) -> None:
    service, _, _, _ = _approve(narration, tmp_path)
    state_path = service.state_path
    raw = state_path.read_bytes()
    if mutation == "duplicate":
        raw = b'{"schema":"duplicate",' + raw[1:]
    elif mutation == "unknown":
        payload = json.loads(raw)
        payload["unknown"] = True
        raw = json.dumps(payload).encode()
    elif mutation == "utf8":
        raw = b"\xff"
    elif mutation == "checksum":
        raw = raw.replace(
            service.latest(principal=LocalPrincipal(), project_id="proj_narration").narration_checksum.encode(),
            b"sha256:" + b"0" * 64, 1,
        )
    elif mutation == "timestamp":
        raw = raw.replace(NOW.encode(), b"2026-08-08 18:10:00", 1)
    else:
        raw = b" " * (narration.MAX_STATE_BYTES + 1)
    state_path.write_bytes(raw)
    restored = narration.NarrationService(stage4=service.stage4, registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=state_path)
    assert restored.authority_count == 0


@pytest.mark.parametrize("mutation", ["invalidation", "evaluation", "approval"])
def test_f382_15_24_restore_rejects_self_consistent_authority_forgery(
    narration: ModuleType, tmp_path: Path, mutation: str
) -> None:
    service = (_draft(narration, tmp_path) if mutation == "invalidation" else _approve(narration, tmp_path))[0]
    payload = json.loads(service.state_path.read_bytes())
    row = payload["versions"][0]
    if mutation == "invalidation":
        row["content"]["narration"].update(invalidatedAuthorities=list(narration.INVALIDATED_AUTHORITIES),
            invalidatedVersion=0, invalidatedChecksum="sha256:" + "0" * 64)
        row["invalidatedAuthorities"] = list(narration.INVALIDATED_AUTHORITIES)
    elif mutation == "evaluation":
        row["state"], row["approval"] = "EVALUATED", None
        row["evaluation"]["source_evaluation_id"] = "eval_forged"
        row["evaluation"]["checksum"] = narration._sha({
            "evaluationId": row["evaluation"]["evaluation_id"], "narrationChecksum": row["evaluation"]["narration_checksum"],
            "policyVersion": row["evaluation"]["policy_version"], "reasonCodes": row["evaluation"]["reason_codes"],
            "result": row["evaluation"]["result"], "schemaVersion": row["evaluation"]["schema_version"],
            "sourceEvaluationChecksum": row["evaluation"]["source_evaluation_checksum"],
            "sourceEvaluationId": "eval_forged",
        })
    else:
        row["approval"]["approver_id"] = "actor_foreign"
        row["approval"]["checksum"] = narration._sha({
            "approvedAt": row["approval"]["approved_at"], "approverId": "actor_foreign",
            "evaluationChecksum": row["approval"]["evaluation_checksum"],
            "narrationChecksum": row["approval"]["narration_checksum"], "schema": narration.APPROVAL_SCHEMA,
        })
    row["narrationChecksum"] = narration.checksum_payload(row["content"])
    service.state_path.write_text(json.dumps(payload), encoding="utf-8")
    restored = narration.NarrationService(stage4=service.stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=service.state_path)
    assert restored.authority_count == 0


def test_f382_06_restored_failed_evaluation_cannot_approve(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    service.evaluate(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    payload = json.loads(service.state_path.read_bytes())
    evaluation = payload["versions"][0]["evaluation"]
    evaluation["result"], evaluation["reason_codes"] = "FAILED", ["FORGED_FAILURE"]
    evaluation["checksum"] = narration._sha({
        "evaluationId": evaluation["evaluation_id"], "narrationChecksum": evaluation["narration_checksum"],
        "policyVersion": evaluation["policy_version"], "reasonCodes": evaluation["reason_codes"],
        "result": evaluation["result"], "schemaVersion": evaluation["schema_version"],
        "sourceEvaluationChecksum": evaluation["source_evaluation_checksum"],
        "sourceEvaluationId": evaluation["source_evaluation_id"],
    })
    service.state_path.write_text(json.dumps(payload), encoding="utf-8")
    restored = narration.NarrationService(stage4=service.stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=service.state_path)
    current = restored.latest(principal=principal, project_id=project_id)
    _assert_code(narration, "EVALUATION_FAILED", lambda: restored.approve_for_speech(
        principal=principal, project_id=project_id, narration_version=current.version,
        narration_checksum=current.narration_checksum, approver_id=principal.actor_id))


def test_f382_21_malformed_presenter_binding_fails_closed(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, binding, project_id = _service(narration, tmp_path)
    malformed = replace(binding, presenter_id=[])
    _assert_code(narration, "PRESENTER_INACTIVE", lambda: service.create_draft(
        principal=principal, project_id=project_id, source_run_id="run_narration",
        presenter_binding=malformed, review_text=service.stage4.walkthrough_runs["run_narration"].accepted_script_text,
    ))


def test_f382_24_restore_recomputes_external_state_and_replay(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    run = service.stage4.walkthrough_runs["run_narration"]
    service.stage4.walkthrough_runs[run.run_id] = replace(run, request_checksum=checksum_text("changed"))
    restored = narration.NarrationService(stage4=service.stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=service.state_path)
    assert restored.authority_count == 0
    _assert_code(narration, "AUTHORITY_STALE", lambda: restored.latest(principal=principal, project_id=project_id))
    assert approved.narration_checksum


def test_f382_19_25_restore_reconciles_receipt_to_consumed_version(
    narration: ModuleType, tmp_path: Path
) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    service.consume_for_tts(principal=principal, project_id=project_id,
        narration_version=approved.version, narration_checksum=approved.narration_checksum,
        request_id="consume_1", trace_id="trace_tts_1")
    payload = json.loads(service.state_path.read_bytes())
    payload["receipts"][0]["source_run_id"] = "run_foreign"
    forged = narration.TTSConsumptionReceipt(**{
        **payload["receipts"][0],
        "duration_requirement_seconds": (90, 120),
    })
    payload["receipts"][0]["receipt_checksum"] = narration._receipt_checksum(forged)
    service.state_path.write_text(json.dumps(payload), encoding="utf-8")
    restored = narration.NarrationService(stage4=service.stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=service.state_path)
    assert restored.authority_count == 0 and restored.receipt_count == 0


def test_f382_19_25_restore_rejects_consumed_version_without_receipt(
    narration: ModuleType, tmp_path: Path
) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    service.consume_for_tts(principal=principal, project_id=project_id,
        narration_version=approved.version, narration_checksum=approved.narration_checksum,
        request_id="consume_1", trace_id="trace_tts_1")
    payload = json.loads(service.state_path.read_bytes())
    payload["receipts"] = []
    service.state_path.write_text(json.dumps(payload), encoding="utf-8")
    restored = narration.NarrationService(stage4=service.stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=service.state_path)
    assert restored.authority_count == 0 and restored.receipt_count == 0


def test_f382_19_25_restore_accepts_consumed_version_with_exact_receipt(
    narration: ModuleType, tmp_path: Path
) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    service.consume_for_tts(principal=principal, project_id=project_id,
        narration_version=approved.version, narration_checksum=approved.narration_checksum,
        request_id="consume_1", trace_id="trace_tts_1")
    restored = narration.NarrationService(stage4=service.stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT), state_path=service.state_path)
    current = restored.latest(principal=principal, project_id=project_id)
    assert current.state is narration.NarrationState.CONSUMED_BY_TTS
    assert restored.authority_count == 1 and restored.receipt_count == 1


def test_f382_26_other_project_requires_its_own_grounded_body(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, binding, project_id = _service(narration, tmp_path)
    service.stage4.projects[project_id] = replace(service.stage4.projects[project_id], name="AI")
    draft = service.create_draft(principal=principal, project_id=project_id, source_run_id="run_narration",
        presenter_binding=binding, review_text=service.stage4.walkthrough_runs["run_narration"].accepted_script_text)
    service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    evaluated = service.evaluate(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    assert evaluated.evaluation.result == "FAILED"


def test_f382_27_logs_and_errors_are_redacted(narration: ModuleType, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    service, principal, draft, project_id = _draft(narration, tmp_path)
    service.request_evaluation(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    service.evaluate(principal=principal, project_id=project_id,
        narration_version=draft.version, narration_checksum=draft.narration_checksum)
    output = caplog.text
    for forbidden in (MEERA_TEXT, "approved.md", "supporting sources", "provider payload", "secret-value"):
        assert forbidden not in output
    assert len(output) <= 4_096


def test_f382_29_concurrent_consumption_issues_exactly_one_receipt(narration: ModuleType, tmp_path: Path) -> None:
    service, principal, approved, project_id = _approve(narration, tmp_path)
    def consume(index: int) -> str:
        try:
            service.consume_for_tts(principal=principal, project_id=project_id,
                narration_version=approved.version, narration_checksum=approved.narration_checksum,
                request_id=f"consume_{index}", trace_id=f"trace_tts_{index}")
            return "receipt"
        except narration.NarrationError as exc:
            return str(exc.code)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(consume, (1, 2)))
    assert sorted(outcomes) == ["CONSUMPTION_REPLAY", "receipt"]
    assert service.receipt_count == 1


def test_f382_28_module_has_no_external_capability(narration: ModuleType) -> None:
    assert narration.__file__ is not None
    source = Path(narration.__file__).read_text(encoding="utf-8")
    for forbidden in ("import fastapi", "import requests", "import httpx", "import openai",
                      "import elevenlabs", "import subprocess", "audio_bytes", "render_video"):
        assert forbidden not in source.lower()
