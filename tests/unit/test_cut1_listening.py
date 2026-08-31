from __future__ import annotations

import ast
import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from backend.app.cut1_audio import (
    CaptionCue,
    Cut1AudioCaptionAuthority,
    audio_commitment,
    build_audio_commitment_manifest,
)
from backend.app.cut1_listening import (
    LISTENING_CRITERIA,
    CurrentCut1AudioAuthoritySet,
    Cut1ListeningArtifactBinding,
    Cut1ListeningAuthorityService,
    Cut1ListeningDecision,
    Cut1ListeningDecisionCommitment,
    ListeningAuthorityError,
    build_listening_commitment_manifest,
    decision_checksum,
)


PRESENTERS = ("meera", "myra", "raj")
VOICES = {"meera": "Despina", "myra": "Leda", "raj": "Achird"}


def checksum(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def authority(presenter_id: str) -> Cut1AudioCaptionAuthority:
    return Cut1AudioCaptionAuthority(
        schema_version="cut1-audio-caption-authority-v2",
        tenant_id="tenant-cut1",
        actor_id="narration-actor",
        project_id="project-cut1",
        version=1,
        narration_checksum=checksum(f"narration-{presenter_id}"),
        presenter_id=presenter_id,
        presenter_version="cut1-v1",
        presenter_binding_checksum=hashlib.sha256(
            f"presenter-{presenter_id}".encode()
        ).hexdigest(),
        source_run_id="stage4-run-cut1",
        source_evaluation_checksum=checksum("source-evaluation"),
        evaluation_checksum=checksum("evaluation"),
        approval_checksum=checksum(f"approval-{presenter_id}"),
        request_id=f"request-{presenter_id}",
        trace_id=f"trace-{presenter_id}",
        receipt_checksum=checksum(f"receipt-{presenter_id}"),
        spoken_text_checksum=checksum(f"spoken-{presenter_id}"),
        provider="google-gemini-tts",
        provider_mode="HOSTED",
        requested_voice=VOICES[presenter_id],
        requested_locale="en-IN",
        model_id="gemini-2.5-pro-tts",
        request_checksum=checksum(f"request-payload-{presenter_id}"),
        config_checksum=checksum("public-config"),
        provider_runtime_config_checksum=checksum("runtime-config"),
        audio_checksum=checksum(f"audio-{presenter_id}"),
        audio_byte_count=4_320_044,
        duration_seconds=90.0,
        sample_rate_hertz=24_000,
        channels=1,
        bits_per_sample=16,
        frame_count=2_160_000,
        rms=1000.0,
        peak=2000,
        active_ratio=0.8,
        caption_checksum=checksum(f"captions-{presenter_id}"),
        caption_byte_count=1000,
        caption_text_checksum=checksum(f"caption-text-{presenter_id}"),
        caption_timing_checksum=checksum(f"caption-timing-{presenter_id}"),
        cues=(CaptionCue(1, 0, 90_000, "metadata excluded from T05C"),),
        authority_checksum=checksum(f"authority-{presenter_id}"),
    )


def audio_set() -> CurrentCut1AudioAuthoritySet:
    authorities = tuple(authority(value) for value in PRESENTERS)
    manifest = build_audio_commitment_manifest(
        sequence=7,
        commitments=tuple(audio_commitment(value) for value in authorities),
    )
    return CurrentCut1AudioAuthoritySet(
        manifest_sequence=manifest.sequence,
        manifest_checksum=manifest.manifest_checksum,
        authorities=authorities,
    )


def binding(
    item: Cut1AudioCaptionAuthority,
    current: CurrentCut1AudioAuthoritySet,
) -> Cut1ListeningArtifactBinding:
    return Cut1ListeningArtifactBinding(
        audio_manifest_sequence=current.manifest_sequence,
        audio_manifest_checksum=current.manifest_checksum,
        presenter_id=item.presenter_id,
        presenter_version=item.presenter_version,
        presenter_binding_checksum=item.presenter_binding_checksum,
        requested_voice=item.requested_voice,
        narration_checksum=item.narration_checksum,
        source_run_id=item.source_run_id,
        source_evaluation_checksum=item.source_evaluation_checksum,
        evaluation_checksum=item.evaluation_checksum,
        approval_checksum=item.approval_checksum,
        receipt_checksum=item.receipt_checksum,
        spoken_text_checksum=item.spoken_text_checksum,
        request_checksum=item.request_checksum,
        config_checksum=item.config_checksum,
        provider_runtime_config_checksum=item.provider_runtime_config_checksum,
        audio_checksum=item.audio_checksum,
        caption_checksum=item.caption_checksum,
        caption_text_checksum=item.caption_text_checksum,
        caption_timing_checksum=item.caption_timing_checksum,
        audio_authority_checksum=item.authority_checksum,
    )


def accepted_decisions(
    current: CurrentCut1AudioAuthoritySet,
) -> tuple[Cut1ListeningDecision, ...]:
    decisions = []
    for item in current.authorities:
        decision = Cut1ListeningDecision(
            decision_id=f"decision-{item.presenter_id}-001",
            reviewer_id="reviewer-human-01",
            artifact_author_id=f"audio-author-{item.presenter_id}",
            reviewed_at="2026-08-31T12:00:00Z",
            binding=binding(item, current),
            criteria={name: True for name in LISTENING_CRITERIA},
            decision_checksum="",
        )
        decisions.append(replace(decision, decision_checksum=decision_checksum(decision)))
    return tuple(decisions)


def commitment_manifest(
    current: CurrentCut1AudioAuthoritySet,
    decisions: tuple[Cut1ListeningDecision, ...],
    *,
    revoked_ids: tuple[str, ...] = (),
):
    commitments = tuple(
        Cut1ListeningDecisionCommitment(
            presenter_id=value.binding.presenter_id,
            decision_id=value.decision_id,
            reviewer_id=value.reviewer_id,
            artifact_author_id=value.artifact_author_id,
            decision_checksum=value.decision_checksum,
        )
        for value in decisions
    )
    return build_listening_commitment_manifest(
        sequence=11,
        audio_manifest_sequence=current.manifest_sequence,
        audio_manifest_checksum=current.manifest_checksum,
        commitments=commitments,
        revoked_decision_ids=revoked_ids,
    )


def service(
    current: CurrentCut1AudioAuthoritySet,
    decisions: tuple[Cut1ListeningDecision, ...],
    *,
    state_path: Path | None = None,
    authors: dict[str, str] | None = None,
) -> Cut1ListeningAuthorityService:
    manifest = commitment_manifest(current, decisions)
    return Cut1ListeningAuthorityService(
        audio_authority_resolver=lambda: current,
        artifact_author_resolver=lambda: authors
        or {value: f"audio-author-{value}" for value in PRESENTERS},
        decision_commitment_resolver=lambda: manifest,
        state_path=state_path,
    )


def rehash(decision: Cut1ListeningDecision) -> Cut1ListeningDecision:
    return replace(decision, decision_checksum=decision_checksum(decision))


def assert_code(expected: str, call: Any) -> None:
    with pytest.raises(ListeningAuthorityError) as error:
        call()
    assert error.value.code == expected


def test_admits_exact_three_independent_human_decisions() -> None:
    current = audio_set()
    decisions = accepted_decisions(current)
    authority_service = service(current, decisions)
    admitted = authority_service.admit_decisions(decisions=decisions)
    assert authority_service.authority_count == 3
    assert admitted == authority_service.get_authority()
    assert tuple(value.binding.presenter_id for value in admitted.decisions) == PRESENTERS
    assert admitted.audio_manifest_checksum == current.manifest_checksum
    assert admitted.decision_manifest_sequence == 11


@pytest.mark.parametrize(
    ("mutate", "code"),
    (
        (lambda values: values[:2], "DECISION_SET_INCOMPLETE"),
        (lambda values: (values[1], values[0], values[2]), "DECISION_ORDER_INVALID"),
        (
            lambda values: (values[0], values[1], replace(values[2], decision_id=values[0].decision_id)),
            "DECISION_ID_DUPLICATE",
        ),
        (
            lambda values: (
                rehash(replace(values[0], criteria={**values[0].criteria, "pacing": False})),
                *values[1:],
            ),
            "LISTENING_CRITERIA_REJECTED",
        ),
        (
            lambda values: (
                rehash(replace(values[0], criteria={**values[0].criteria, "pacing": 1})),
                *values[1:],
            ),
            "LISTENING_CRITERIA_INVALID",
        ),
        (
            lambda values: (
                rehash(replace(values[0], reviewer_id=values[0].artifact_author_id)),
                *values[1:],
            ),
            "REVIEWER_NOT_INDEPENDENT",
        ),
    ),
)
def test_rejects_incomplete_reordered_duplicate_or_nonliteral_decisions(
    mutate: Any, code: str,
) -> None:
    current = audio_set()
    decisions = accepted_decisions(current)
    candidate = tuple(mutate(decisions))
    assert_code(code, lambda: service(current, decisions).admit_decisions(decisions=candidate))


@pytest.mark.parametrize(
    "field",
    (
        "audio_manifest_checksum",
        "presenter_binding_checksum",
        "requested_voice",
        "narration_checksum",
        "source_run_id",
        "source_evaluation_checksum",
        "evaluation_checksum",
        "approval_checksum",
        "receipt_checksum",
        "spoken_text_checksum",
        "request_checksum",
        "config_checksum",
        "provider_runtime_config_checksum",
        "audio_checksum",
        "caption_checksum",
        "caption_text_checksum",
        "caption_timing_checksum",
        "audio_authority_checksum",
    ),
)
def test_rejects_each_stale_or_substituted_t05b_binding(field: str) -> None:
    current = audio_set()
    decisions = accepted_decisions(current)
    first = decisions[0]
    changed = replace(first.binding, **{field: checksum(f"mutated-{field}")})
    candidate = (rehash(replace(first, binding=changed)), *decisions[1:])
    assert_code(
        "AUDIO_AUTHORITY_MISMATCH",
        lambda: service(current, candidate).admit_decisions(decisions=candidate),
    )


def test_rejects_candidate_author_substitution_and_coherent_rehash() -> None:
    current = audio_set()
    decisions = accepted_decisions(current)
    substituted = (
        rehash(replace(decisions[0], artifact_author_id="claimed-other-author")),
        *decisions[1:],
    )
    assert_code(
        "ARTIFACT_AUTHOR_MISMATCH",
        lambda: service(current, substituted).admit_decisions(decisions=substituted),
    )
    coherently_rehashed = (
        rehash(replace(decisions[0], reviewed_at="2026-08-31T12:01:00Z")),
        *decisions[1:],
    )
    assert_code(
        "DECISION_COMMITMENT_MISMATCH",
        lambda: service(current, decisions).admit_decisions(decisions=coherently_rehashed),
    )


def test_rejects_revocation_replay_and_current_t05b_drift() -> None:
    current = audio_set()
    decisions = accepted_decisions(current)
    manifest = commitment_manifest(current, decisions, revoked_ids=(decisions[0].decision_id,))
    revoked = Cut1ListeningAuthorityService(
        audio_authority_resolver=lambda: current,
        artifact_author_resolver=lambda: {
            value: f"audio-author-{value}" for value in PRESENTERS
        },
        decision_commitment_resolver=lambda: manifest,
    )
    assert_code("DECISION_REVOKED", lambda: revoked.admit_decisions(decisions=decisions))
    authority_service = service(current, decisions)
    authority_service.admit_decisions(decisions=decisions)
    assert_code(
        "DECISION_REPLAYED", lambda: authority_service.admit_decisions(decisions=decisions)
    )
    changed = replace(current, manifest_sequence=current.manifest_sequence + 1)
    authority_service.audio_authority_resolver = lambda: changed
    assert_code("AUDIO_AUTHORITY_STALE", authority_service.get_authority)


def test_fails_closed_when_trusted_commitment_is_unavailable() -> None:
    current = audio_set()
    decisions = accepted_decisions(current)

    def unavailable():
        raise RuntimeError("offline registry")

    authority_service = Cut1ListeningAuthorityService(
        audio_authority_resolver=lambda: current,
        artifact_author_resolver=lambda: {
            value: f"audio-author-{value}" for value in PRESENTERS
        },
        decision_commitment_resolver=unavailable,
    )
    assert_code(
        "DECISION_COMMITMENT_UNAVAILABLE",
        lambda: authority_service.admit_decisions(decisions=decisions),
    )


def test_persists_metadata_only_and_quarantines_tampered_state(tmp_path: Path) -> None:
    current = audio_set()
    decisions = accepted_decisions(current)
    state = tmp_path / "listening.json"
    authority_service = service(current, decisions, state_path=state)
    accepted = authority_service.admit_decisions(decisions=decisions)
    restored = service(current, decisions, state_path=state)
    assert restored.get_authority() == accepted
    text = state.read_text(encoding="utf-8")
    for forbidden in ("audioBase64", "captionBase64", "spoken_text", "narration_text"):
        assert forbidden not in text
    state.write_text(text.replace(decisions[0].reviewer_id, "tampered-reviewer"), encoding="utf-8")
    quarantined = service(current, decisions, state_path=state)
    assert quarantined.quarantine_reason == "STATE_INVALID"
    assert_code("AUTHORITY_STATE_QUARANTINED", quarantined.get_authority)


def test_module_has_no_provider_network_environment_or_acceptance_factory() -> None:
    source = (Path(__file__).parents[2] / "backend/app/cut1_listening.py").read_text()
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported.isdisjoint(
        {"socket", "subprocess", "requests", "httpx", "aiohttp", "os", "google", "openai"}
    )
    names = {node.name.lower() for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert not any(
        token in name for name in names for token in ("accept_decision", "infer_criteria", "listen_audio")
    )
