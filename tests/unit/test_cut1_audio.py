from __future__ import annotations

import base64
import hashlib
import importlib
import importlib.util
import ast
import inspect
import json
import struct
from dataclasses import asdict, replace
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping

import pytest

from backend.app.narration import (
    TTSConsumptionReceipt,
    canonical_presenter_text,
)


PRESENTERS = ("meera", "myra", "raj")
VOICE_PROFILES = {"meera": "meera-voice-v1", "myra": "myra-voice-v1", "raj": "raj-voice-v1"}
CONFIG_CHECKSUM = "sha256:19e8d9fda744c225ae616101df9b0a6c8f6b5334714fc321edc33473331cc793"


@pytest.fixture(scope="module")
def cut1_audio() -> ModuleType:
    if importlib.util.find_spec("backend.app.cut1_audio") is None:
        pytest.skip("T05B GREEN module is not implemented yet")
    return importlib.import_module("backend.app.cut1_audio")


def test_t05b_audio_caption_authority_module_exists() -> None:
    assert importlib.util.find_spec("backend.app.cut1_audio") is not None, (
        "Issue #459 T05B audio/caption authority module is absent"
    )


def test_t05b_review_correction_requires_materialized_manifest_admission(
    cut1_audio: ModuleType,
) -> None:
    assert hasattr(cut1_audio, "Cut1AudioCommitment")
    assert hasattr(cut1_audio, "Cut1AudioCommitmentManifest")
    assert hasattr(cut1_audio, "build_audio_commitment_manifest")
    constructor = inspect.signature(cut1_audio.Cut1AudioAuthorityService).parameters
    admission = inspect.signature(
        cut1_audio.Cut1AudioAuthorityService.admit_authorities
    ).parameters
    assert "provider" not in constructor
    assert "commitment_resolver" in constructor
    assert "candidates" in admission


@pytest.fixture(scope="module")
def tts_provider() -> ModuleType:
    return importlib.import_module("backend.app.tts_provider")


def _sha(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _json_sha(value: object) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _receipt(presenter_id: str = "meera", *, version: int = 1) -> TTSConsumptionReceipt:
    prefix = {"meera": "a", "myra": "b", "raj": "c"}[presenter_id]
    return TTSConsumptionReceipt(
        tenant_id="tenant_local",
        actor_id="user_local",
        project_id="proj_cut1",
        version=version,
        narration_checksum="sha256:" + prefix * 64,
        presenter_id=presenter_id,
        presenter_version="1.0.0",
        presenter_binding_checksum="sha256:" + "b" * 64,
        source_run_id=f"run_{presenter_id}_{version}",
        source_evaluation_checksum="sha256:" + "c" * 64,
        evaluation_checksum="sha256:" + "d" * 64,
        approval_checksum="sha256:" + "e" * 64,
        request_id=f"consume_{presenter_id}_{version}",
        trace_id=f"trace_{presenter_id}_{version}",
        spoken_text=canonical_presenter_text(presenter_id),
        duration_requirement_seconds=(90, 120),
        receipt_checksum="sha256:" + prefix * 63 + f"{version:x}",
    )


def _speech_wav(*, seconds: int = 90, silent: bool = False) -> bytes:
    sample_rate = 24_000
    frame_count = seconds * sample_rate
    values = (0,) if silent else (-9000, 7000, -4000, 10000, -6000, 5000, -2000, 8000)
    pattern = b"".join(struct.pack("<h", value) for value in values)
    pcm = (pattern * ((frame_count * 2 + len(pattern) - 1) // len(pattern)))[: frame_count * 2]
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(pcm))
        + b"WAVEfmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", len(pcm))
        + pcm
    )


def _timestamp(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def _captions(text: str, *, start_ms: int = 0, end_ms: int = 90_000) -> bytes:
    paragraphs = text.split("\n\n")
    width = (end_ms - start_ms) // len(paragraphs)
    blocks: list[str] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        cue_start = start_ms + ((index - 1) * width)
        cue_end = end_ms if index == len(paragraphs) else start_ms + (index * width)
        blocks.append(f"{index}\n{_timestamp(cue_start)} --> {_timestamp(cue_end)}\n{paragraph}")
    return ("\n\n".join(blocks) + "\n").encode()


def _result(
    tts_provider: ModuleType,
    receipt: TTSConsumptionReceipt,
    *,
    audio_bytes: bytes | None = None,
    overrides: Mapping[str, object] | None = None,
    **field_overrides: object,
) -> Any:
    audio = _speech_wav() if audio_bytes is None else audio_bytes
    values: dict[str, object] = {
        "provider": "offline-test-provider",
        "provider_mode": "LOCAL",
        "presenter_id": receipt.presenter_id,
        "requested_voice": VOICE_PROFILES[receipt.presenter_id],
        "requested_locale": "en-IN",
        "model_id": "offline-test-v1",
        "receipt_checksum": receipt.receipt_checksum,
        "request_checksum": "sha256:" + "2" * 64,
        "config_checksum": CONFIG_CHECKSUM,
        "mime_type": "audio/wav",
        "audio_bytes": audio,
        "artifact_checksum": _sha(audio),
    }
    values.update(overrides or {})
    values.update(field_overrides)
    return tts_provider.ApprovedNarrationTTSResult(**values)


def _config(cut1_audio: ModuleType) -> Any:
    return cut1_audio.Cut1AudioConfig(
        provider="offline-test-provider",
        provider_mode="LOCAL",
        requested_locale="en-IN",
        model_id="offline-test-v1",
        presenter_voices=VOICE_PROFILES,
        config_checksum=CONFIG_CHECKSUM,
    )


def _candidate(
    cut1_audio: ModuleType,
    receipt: TTSConsumptionReceipt,
    result: Any,
    captions: bytes | None = None,
) -> Any:
    return cut1_audio.Cut1AudioCandidate(
        receipt=receipt,
        result=result,
        caption_bytes=captions or _captions(receipt.spoken_text),
    )


def _manifest(
    cut1_audio: ModuleType,
    candidates: tuple[Any, ...],
    *,
    sequence: int = 1,
) -> Any:
    preview = cut1_audio.Cut1AudioAuthorityService(
        receipt_validator=lambda _: True,
        commitment_resolver=lambda: None,
        approved_config=_config(cut1_audio),
    )
    authorities = tuple(
        preview.evaluate_authority(candidate=value) for value in candidates
    )
    return cut1_audio.build_audio_commitment_manifest(
        sequence=sequence,
        commitments=tuple(cut1_audio.audio_commitment(value) for value in authorities),
    )


def _service(
    cut1_audio: ModuleType,
    *,
    state_path: Path,
    current_receipts: tuple[TTSConsumptionReceipt, ...],
    manifest: Any,
    validator: Callable[[TTSConsumptionReceipt], bool] | None = None,
    manifest_resolver: Callable[[], Any] | None = None,
) -> Any:
    return cut1_audio.Cut1AudioAuthorityService(
        receipt_validator=validator
        or (lambda candidate: candidate in current_receipts),
        commitment_resolver=manifest_resolver or (lambda: manifest),
        approved_config=_config(cut1_audio),
        state_path=state_path,
    )


def _service_for_candidate(
    cut1_audio: ModuleType,
    *,
    state_path: Path,
    current_receipt: TTSConsumptionReceipt,
    anchor_candidate: Any,
    validator: Callable[[TTSConsumptionReceipt], bool] | None = None,
) -> tuple[Any, Any]:
    manifest = _manifest(cut1_audio, (anchor_candidate,))
    return (
        _service(
            cut1_audio,
            state_path=state_path,
            current_receipts=(current_receipt,),
            manifest=manifest,
            validator=validator,
        ),
        manifest,
    )


def _assert_failure(
    cut1_audio: ModuleType,
    service: Any,
    candidate: Any,
    code: str,
) -> None:
    with pytest.raises(cut1_audio.AudioCaptionAuthorityError) as caught:
        service.admit_authorities(candidates=(candidate,))
    assert caught.value.code == code
    assert service.authority_count == 0


@pytest.mark.parametrize("presenter_id", PRESENTERS)
def test_t05b_binds_and_restores_each_presenter_without_provider_replay(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    presenter_id: str,
) -> None:
    receipt = _receipt(presenter_id)
    result = _result(tts_provider, receipt)
    candidate = _candidate(cut1_audio, receipt, result)
    manifest = _manifest(cut1_audio, (candidate,))
    state_path = tmp_path / f"{presenter_id}.json"
    service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )

    authority = service.admit_authorities(candidates=(candidate,))[0]

    assert authority.presenter_id == presenter_id
    assert authority.receipt_checksum == receipt.receipt_checksum
    assert authority.narration_checksum == receipt.narration_checksum
    assert authority.source_run_id == receipt.source_run_id
    assert authority.source_evaluation_checksum == receipt.source_evaluation_checksum
    assert authority.evaluation_checksum == receipt.evaluation_checksum
    assert authority.provider == result.provider
    assert authority.request_checksum == result.request_checksum
    assert authority.config_checksum == result.config_checksum
    assert authority.audio_checksum == result.artifact_checksum
    assert authority.caption_checksum == _sha(_captions(receipt.spoken_text))
    assert authority.duration_seconds == 90
    assert authority.authority_checksum.startswith("sha256:")

    restored = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )
    assert restored.authority_count == 1
    assert restored.get_authority(receipt) == authority


def test_t05b_admission_has_no_provider_or_synthesis_capability(
    cut1_audio: ModuleType,
) -> None:
    constructor = inspect.signature(cut1_audio.Cut1AudioAuthorityService).parameters
    source = inspect.getsource(cut1_audio.Cut1AudioAuthorityService)
    assert "provider" not in constructor
    assert ".synthesize(" not in source


@pytest.mark.parametrize("presenter_id", PRESENTERS)
def test_t05b_rejects_cross_presenter_audio_binding(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    presenter_id: str,
) -> None:
    receipt = _receipt(presenter_id)
    other = next(value for value in PRESENTERS if value != presenter_id)
    baseline = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    result = _result(tts_provider, receipt, presenter_id=other)
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / f"cross-{presenter_id}.json",
        current_receipt=receipt,
        anchor_candidate=baseline,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(cut1_audio, receipt, result),
        "PRESENTER_BINDING_MISMATCH",
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_run_id", "run_substituted"),
        ("source_evaluation_checksum", "sha256:" + "4" * 64),
        ("evaluation_checksum", "sha256:" + "5" * 64),
        ("narration_checksum", "sha256:" + "6" * 64),
    ],
)
def test_t05b_rejects_stale_or_substituted_receipt_lineage(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    current = _receipt()
    if field == "source_run_id":
        substituted = replace(current, source_run_id=value)
    elif field == "source_evaluation_checksum":
        substituted = replace(current, source_evaluation_checksum=value)
    elif field == "evaluation_checksum":
        substituted = replace(current, evaluation_checksum=value)
    else:
        assert field == "narration_checksum"
        substituted = replace(current, narration_checksum=value)
    result = _result(tts_provider, substituted)
    baseline = _candidate(cut1_audio, current, _result(tts_provider, current))
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / f"receipt-{field}.json",
        current_receipt=current,
        anchor_candidate=baseline,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(cut1_audio, substituted, result),
        "NARRATION_AUTHORITY_STALE",
    )


@pytest.mark.parametrize(
    "overrides,code",
    [
        ({"receipt_checksum": "sha256:" + "7" * 64}, "RECEIPT_BINDING_MISMATCH"),
        ({"request_checksum": "not-a-checksum"}, "REQUEST_BINDING_INVALID"),
        ({"config_checksum": "not-a-checksum"}, "CONFIG_BINDING_INVALID"),
        ({"config_checksum": "sha256:" + "4" * 64}, "CONFIG_BINDING_MISMATCH"),
        ({"provider": "substituted-provider"}, "CONFIG_BINDING_MISMATCH"),
        ({"requested_voice": "substituted-voice"}, "CONFIG_BINDING_MISMATCH"),
        ({"requested_locale": "en-US"}, "CONFIG_BINDING_MISMATCH"),
        ({"model_id": "substituted-model"}, "CONFIG_BINDING_MISMATCH"),
    ],
)
def test_t05b_rejects_receipt_request_and_configuration_substitution(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    overrides: dict[str, object],
    code: str,
) -> None:
    receipt = _receipt()
    baseline = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    result = _result(tts_provider, receipt, overrides=overrides)
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / f"result-{code}.json",
        current_receipt=receipt,
        anchor_candidate=baseline,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(cut1_audio, receipt, result),
        code,
    )


@pytest.mark.parametrize(
    "audio,checksum,code",
    [
        (b"not-wav", None, "AUDIO_WAV_INVALID"),
        (_speech_wav(seconds=89), None, "AUDIO_DURATION_INVALID"),
        (_speech_wav(seconds=121), None, "AUDIO_DURATION_INVALID"),
        (_speech_wav(silent=True), None, "AUDIO_SILENT"),
        (_speech_wav(), "sha256:" + "9" * 64, "AUDIO_CHECKSUM_MISMATCH"),
    ],
    ids=("malformed", "too-short", "too-long", "silent", "checksum"),
)
def test_t05b_rejects_malformed_silent_wrong_duration_or_replaced_audio(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    audio: bytes,
    checksum: str | None,
    code: str,
) -> None:
    receipt = _receipt()
    overrides = {} if checksum is None else {"artifact_checksum": checksum}
    result = _result(tts_provider, receipt, audio_bytes=audio, overrides=overrides)
    baseline = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / f"audio-{code}.json",
        current_receipt=receipt,
        anchor_candidate=baseline,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(cut1_audio, receipt, result),
        code,
    )


@pytest.mark.parametrize("mutation", ["wrong", "partial", "reordered"])
def test_t05b_rejects_wrong_partial_or_reordered_caption_text(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    mutation: str,
) -> None:
    receipt = _receipt()
    paragraphs = receipt.spoken_text.split("\n\n")
    if mutation == "wrong":
        paragraphs[1] = paragraphs[1].replace("StackClimb", "Stack Climb", 1)
    elif mutation == "partial":
        paragraphs.pop()
    else:
        paragraphs[0], paragraphs[1] = paragraphs[1], paragraphs[0]
    captions = _captions("\n\n".join(paragraphs))
    result = _result(tts_provider, receipt)
    baseline = _candidate(cut1_audio, receipt, result)
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / f"caption-{mutation}.json",
        current_receipt=receipt,
        anchor_candidate=baseline,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(cut1_audio, receipt, result, captions),
        "CAPTION_TEXT_MISMATCH",
    )


@pytest.mark.parametrize(
    "start_ms,end_ms",
    [(1_000, 90_000), (0, 89_000), (0, 90_001), (10_000, 9_000)],
)
def test_t05b_rejects_caption_gaps_bounds_and_reversed_timing(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    start_ms: int,
    end_ms: int,
) -> None:
    receipt = _receipt()
    result = _result(tts_provider, receipt)
    baseline = _candidate(cut1_audio, receipt, result)
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / f"timing-{start_ms}-{end_ms}.json",
        current_receipt=receipt,
        anchor_candidate=baseline,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(
            cut1_audio,
            receipt,
            result,
            _captions(receipt.spoken_text, start_ms=start_ms, end_ms=end_ms),
        ),
        "CAPTION_TIMING_INVALID",
    )


def test_t05b_rejects_citation_markers_in_spoken_and_caption_text(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = replace(_receipt(), spoken_text=canonical_presenter_text("meera") + " [1]")
    current = _receipt()
    baseline = _candidate(cut1_audio, current, _result(tts_provider, current))
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / "spoken-citation.json",
        current_receipt=current,
        anchor_candidate=baseline,
        validator=lambda candidate: candidate == receipt,
    )

    _assert_failure(
        cut1_audio,
        service,
        _candidate(cut1_audio, receipt, _result(tts_provider, receipt)),
        "SPOKEN_CITATION_MARKER",
    )


def test_t05b_rejects_exact_receipt_replay_without_creating_a_second_record(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    captions = _captions(receipt.spoken_text)
    candidate = _candidate(cut1_audio, receipt, _result(tts_provider, receipt), captions)
    manifest = _manifest(cut1_audio, (candidate,))
    service = _service(
        cut1_audio,
        state_path=tmp_path / "replay.json",
        current_receipts=(receipt,),
        manifest=manifest,
    )
    authority = service.admit_authorities(candidates=(candidate,))[0]

    with pytest.raises(cut1_audio.AudioCaptionAuthorityError) as caught:
        service.admit_authorities(candidates=(candidate,))
    assert caught.value.code == "RECEIPT_REPLAYED"
    assert service.authority_count == 1
    assert service.get_authority(receipt) == authority


def _replace_first(value: Any, old: object, new: object) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if child == old:
                value[key] = new
                return True
            if _replace_first(child, old, new):
                return True
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if child == old:
                value[index] = new
                return True
            if _replace_first(child, old, new):
                return True
    return False


def _refresh_state_checksum(payload: dict[str, Any]) -> None:
    payload["stateChecksum"] = _json_sha(
        {
            "schema": payload["schema"],
            "manifestSequence": payload["manifestSequence"],
            "manifestChecksum": payload["manifestChecksum"],
            "records": payload["records"],
        }
    )


def test_t05b_rejects_valid_request_checksum_not_in_trusted_manifest(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    baseline = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / "request-commitment.json",
        current_receipt=receipt,
        anchor_candidate=baseline,
    )
    substituted = _candidate(
        cut1_audio,
        receipt,
        _result(tts_provider, receipt, request_checksum="sha256:" + "9" * 64),
    )

    _assert_failure(
        cut1_audio, service, substituted, "AUTHORITY_COMMITMENT_MISMATCH"
    )


def test_t05b_configuration_checksum_is_derived_from_canonical_content(
    cut1_audio: ModuleType,
) -> None:
    with pytest.raises(ValueError, match="configuration is invalid"):
        cut1_audio.Cut1AudioConfig(
            provider="offline-test-provider",
            provider_mode="LOCAL",
            requested_locale="en-IN",
            model_id="substituted-model",
            presenter_voices=VOICE_PROFILES,
            config_checksum=CONFIG_CHECKSUM,
        )


def test_t05b_revalidates_receipt_immediately_before_persistence(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    candidate = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    calls = 0

    def current(value: TTSConsumptionReceipt) -> bool:
        nonlocal calls
        calls += 1
        return value == receipt and calls == 1

    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / "stale-before-persist.json",
        current_receipt=receipt,
        anchor_candidate=candidate,
        validator=current,
    )

    _assert_failure(cut1_audio, service, candidate, "NARRATION_AUTHORITY_STALE")
    assert not (tmp_path / "stale-before-persist.json").exists()


def test_t05b_revalidates_receipt_on_retrieval(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    candidate = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    is_current = True
    service, _ = _service_for_candidate(
        cut1_audio,
        state_path=tmp_path / "stale-get.json",
        current_receipt=receipt,
        anchor_candidate=candidate,
        validator=lambda value: is_current and value == receipt,
    )
    service.admit_authorities(candidates=(candidate,))
    is_current = False

    with pytest.raises(cut1_audio.AudioCaptionAuthorityError) as caught:
        service.get_authority(receipt)
    assert caught.value.code == "NARRATION_AUTHORITY_STALE"


def test_t05b_restore_quarantines_persisted_tamper(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    state_path = tmp_path / "tamper.json"
    candidate = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    manifest = _manifest(cut1_audio, (candidate,))
    service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )
    service.admit_authorities(candidates=(candidate,))
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert _replace_first(payload, receipt.presenter_id, "raj")
    _refresh_state_checksum(payload)
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )

    assert restored.authority_count == 0
    assert restored.quarantine_reason


def test_t05b_restore_rejects_fully_rechecksummed_audio_substitution(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    state_path = tmp_path / "coherent-audio-tamper.json"
    original = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    manifest = _manifest(cut1_audio, (original,))
    service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )
    service.admit_authorities(candidates=(original,))

    substituted_audio = bytearray(_speech_wav())
    substituted_audio[44:46] = struct.pack("<h", 1234)
    substituted_result = _result(
        tts_provider, receipt, audio_bytes=bytes(substituted_audio)
    )
    substituted = _candidate(cut1_audio, receipt, substituted_result)
    preview = cut1_audio.Cut1AudioAuthorityService(
        receipt_validator=lambda _: True,
        commitment_resolver=lambda: manifest,
        approved_config=_config(cut1_audio),
    )
    substituted_authority = preview.evaluate_authority(candidate=substituted)

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    result_row = payload["records"][0]["result"]
    result_row["artifact_checksum"] = substituted_result.artifact_checksum
    result_row["audioBase64"] = base64.b64encode(substituted_result.audio_bytes).decode()
    payload["records"][0]["authority"] = asdict(substituted_authority)
    _refresh_state_checksum(payload)
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )
    assert restored.authority_count == 0
    assert restored.quarantine_reason == "STATE_INVALID"


@pytest.mark.parametrize("mutation", ("delete", "reverse"))
def test_t05b_restore_rejects_rechecksummed_partial_or_reordered_record_set(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    mutation: str,
) -> None:
    receipts = tuple(_receipt(value) for value in PRESENTERS)
    candidates = tuple(
        _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
        for receipt in receipts
    )
    manifest = _manifest(cut1_audio, candidates)
    state_path = tmp_path / f"record-{mutation}.json"
    service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=receipts,
        manifest=manifest,
    )
    service.admit_authorities(candidates=candidates)
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if mutation == "delete":
        payload["records"].pop()
    else:
        payload["records"].reverse()
    _refresh_state_checksum(payload)
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=receipts,
        manifest=manifest,
    )
    assert restored.authority_count == 0
    assert restored.quarantine_reason == "STATE_INVALID"


def test_t05b_restore_rejects_valid_but_rolled_back_narration_authority(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    old_receipt = _receipt(version=1)
    current_receipt = _receipt(version=2)
    state_path = tmp_path / "rollback.json"
    old_candidate = _candidate(
        cut1_audio, old_receipt, _result(tts_provider, old_receipt)
    )
    old_manifest = _manifest(cut1_audio, (old_candidate,), sequence=1)
    old_service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(old_receipt,),
        manifest=old_manifest,
    )
    old_service.admit_authorities(candidates=(old_candidate,))
    current_candidate = _candidate(
        cut1_audio, current_receipt, _result(tts_provider, current_receipt)
    )
    current_manifest = _manifest(cut1_audio, (current_candidate,), sequence=2)

    restored = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(current_receipt,),
        manifest=current_manifest,
    )

    assert restored.authority_count == 0
    assert restored.quarantine_reason


def test_t05b_new_trusted_manifest_atomically_replaces_superseded_presenter(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    old_receipt = _receipt(version=1)
    new_receipt = _receipt(version=2)
    old_candidate = _candidate(
        cut1_audio, old_receipt, _result(tts_provider, old_receipt)
    )
    new_candidate = _candidate(
        cut1_audio, new_receipt, _result(tts_provider, new_receipt)
    )
    manifest_box = {"value": _manifest(cut1_audio, (old_candidate,), sequence=1)}
    current_box = {"value": old_receipt}
    state_path = tmp_path / "supersede.json"
    service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(old_receipt,),
        manifest=manifest_box["value"],
        validator=lambda value: value == current_box["value"],
        manifest_resolver=lambda: manifest_box["value"],
    )
    service.admit_authorities(candidates=(old_candidate,))

    manifest_box["value"] = _manifest(cut1_audio, (new_candidate,), sequence=2)
    current_box["value"] = new_receipt
    new_authority = service.admit_authorities(candidates=(new_candidate,))[0]

    assert service.authority_count == 1
    assert service.get_authority(new_receipt) == new_authority
    with pytest.raises(cut1_audio.AudioCaptionAuthorityError) as caught:
        service.get_authority(old_receipt)
    assert caught.value.code == "NARRATION_AUTHORITY_STALE"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert len(payload["records"]) == 1
    assert payload["records"][0]["receipt"]["version"] == 2


def test_t05b_persistence_failure_commits_no_partial_authority(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _receipt()
    state_path = tmp_path / "write-failure.json"
    candidate = _candidate(cut1_audio, receipt, _result(tts_provider, receipt))
    manifest = _manifest(cut1_audio, (candidate,))
    service = _service(
        cut1_audio,
        state_path=state_path,
        current_receipts=(receipt,),
        manifest=manifest,
    )

    def fail_write(_path: Path, _payload: object) -> None:
        raise OSError("bounded-test-write-failure")

    monkeypatch.setattr(cut1_audio, "write_state", fail_write)
    with pytest.raises(OSError, match="bounded-test-write-failure"):
        service.admit_authorities(candidates=(candidate,))
    assert service.authority_count == 0
    assert not state_path.exists()


def test_t05b_module_has_no_direct_credential_network_or_process_capability() -> None:
    source = (Path(__file__).parents[2] / "backend/app/cut1_audio.py").read_text()
    imported_roots = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
    }
    imported_roots.update(
        node.module.split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots.isdisjoint(
        {"os", "socket", "subprocess", "requests", "httpx", "urllib", "google"}
    )
    assert all(token not in source for token in ("getenv(", "environ["))
