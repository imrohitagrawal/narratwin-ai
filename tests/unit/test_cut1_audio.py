from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import struct
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

from backend.app.narration import (
    TTSConsumptionReceipt,
    canonical_presenter_text,
)


PRESENTERS = ("meera", "myra", "raj")
VOICE_PROFILES = {"meera": "meera-voice-v1", "myra": "myra-voice-v1", "raj": "raj-voice-v1"}
CONFIG_CHECKSUM = "sha256:" + "3" * 64


@pytest.fixture(scope="module")
def cut1_audio() -> ModuleType:
    if importlib.util.find_spec("backend.app.cut1_audio") is None:
        pytest.skip("T05B GREEN module is not implemented yet")
    return importlib.import_module("backend.app.cut1_audio")


def test_t05b_audio_caption_authority_module_exists() -> None:
    assert importlib.util.find_spec("backend.app.cut1_audio") is not None, (
        "Issue #459 T05B audio/caption authority module is absent"
    )


@pytest.fixture(scope="module")
def tts_provider() -> ModuleType:
    return importlib.import_module("backend.app.tts_provider")


def _sha(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


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
        receipt_checksum="sha256:" + f"{version:x}" * 64,
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
        blocks.append(
            f"{index}\n{_timestamp(cue_start)} --> {_timestamp(cue_end)}\n{paragraph}"
        )
    return ("\n\n".join(blocks) + "\n").encode()


def _result(
    tts_provider: ModuleType,
    receipt: TTSConsumptionReceipt,
    *,
    audio_bytes: bytes | None = None,
    **overrides: object,
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
    values.update(overrides)
    return tts_provider.ApprovedNarrationTTSResult(**values)


class _FakeProvider:
    def __init__(self, result: Any) -> None:
        self.result = result

    def synthesize(self, *, receipt: TTSConsumptionReceipt) -> Any:
        del receipt
        return self.result


def _service(
    cut1_audio: ModuleType,
    *,
    state_path: Path,
    receipt: TTSConsumptionReceipt,
    provider: object | None,
    validator: Callable[[TTSConsumptionReceipt], bool] | None = None,
) -> Any:
    return cut1_audio.Cut1AudioAuthorityService(
        provider=provider,
        receipt_validator=validator or (lambda candidate: candidate == receipt),
        approved_config=cut1_audio.Cut1AudioConfig(
            provider="offline-test-provider",
            provider_mode="LOCAL",
            requested_locale="en-IN",
            model_id="offline-test-v1",
            presenter_voices=VOICE_PROFILES,
            config_checksum=CONFIG_CHECKSUM,
        ),
        state_path=state_path,
    )


def _assert_failure(
    cut1_audio: ModuleType,
    service: Any,
    receipt: TTSConsumptionReceipt,
    captions: bytes,
    code: str,
) -> None:
    with pytest.raises(cut1_audio.AudioCaptionAuthorityError) as caught:
        service.create_authority(receipt=receipt, caption_bytes=captions)
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
    state_path = tmp_path / f"{presenter_id}.json"
    service = _service(
        cut1_audio,
        state_path=state_path,
        receipt=receipt,
        provider=_FakeProvider(result),
    )

    authority = service.create_authority(
        receipt=receipt,
        caption_bytes=_captions(receipt.spoken_text),
    )

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
        receipt=receipt,
        provider=None,
    )
    assert restored.authority_count == 1
    assert restored.get_authority(receipt.receipt_checksum) == authority


def test_t05b_provider_is_absent_and_disabled_by_default(
    cut1_audio: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    service = _service(
        cut1_audio,
        state_path=tmp_path / "disabled.json",
        receipt=receipt,
        provider=None,
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        _captions(receipt.spoken_text),
        "TTS_PROVIDER_DISABLED",
    )


@pytest.mark.parametrize("presenter_id", PRESENTERS)
def test_t05b_rejects_cross_presenter_audio_binding(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
    presenter_id: str,
) -> None:
    receipt = _receipt(presenter_id)
    other = next(value for value in PRESENTERS if value != presenter_id)
    result = _result(tts_provider, receipt, presenter_id=other)
    service = _service(
        cut1_audio,
        state_path=tmp_path / f"cross-{presenter_id}.json",
        receipt=receipt,
        provider=_FakeProvider(result),
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        _captions(receipt.spoken_text),
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
    substituted = replace(current, **{field: value})
    result = _result(tts_provider, substituted)
    service = _service(
        cut1_audio,
        state_path=tmp_path / f"receipt-{field}.json",
        receipt=current,
        provider=_FakeProvider(result),
    )

    _assert_failure(
        cut1_audio,
        service,
        substituted,
        _captions(substituted.spoken_text),
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
    result = _result(tts_provider, receipt, **overrides)
    service = _service(
        cut1_audio,
        state_path=tmp_path / f"result-{code}.json",
        receipt=receipt,
        provider=_FakeProvider(result),
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        _captions(receipt.spoken_text),
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
    result = _result(tts_provider, receipt, audio_bytes=audio, **overrides)
    service = _service(
        cut1_audio,
        state_path=tmp_path / f"audio-{code}.json",
        receipt=receipt,
        provider=_FakeProvider(result),
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        _captions(receipt.spoken_text),
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
    service = _service(
        cut1_audio,
        state_path=tmp_path / f"caption-{mutation}.json",
        receipt=receipt,
        provider=_FakeProvider(_result(tts_provider, receipt)),
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        captions,
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
    service = _service(
        cut1_audio,
        state_path=tmp_path / f"timing-{start_ms}-{end_ms}.json",
        receipt=receipt,
        provider=_FakeProvider(_result(tts_provider, receipt)),
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        _captions(receipt.spoken_text, start_ms=start_ms, end_ms=end_ms),
        "CAPTION_TIMING_INVALID",
    )


def test_t05b_rejects_citation_markers_in_spoken_and_caption_text(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = replace(_receipt(), spoken_text=canonical_presenter_text("meera") + " [1]")
    service = _service(
        cut1_audio,
        state_path=tmp_path / "spoken-citation.json",
        receipt=receipt,
        provider=_FakeProvider(_result(tts_provider, receipt)),
    )

    _assert_failure(
        cut1_audio,
        service,
        receipt,
        _captions(receipt.spoken_text),
        "SPOKEN_CITATION_MARKER",
    )


def test_t05b_rejects_exact_receipt_replay_without_creating_a_second_record(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    captions = _captions(receipt.spoken_text)
    service = _service(
        cut1_audio,
        state_path=tmp_path / "replay.json",
        receipt=receipt,
        provider=_FakeProvider(_result(tts_provider, receipt)),
    )
    authority = service.create_authority(receipt=receipt, caption_bytes=captions)

    with pytest.raises(cut1_audio.AudioCaptionAuthorityError) as caught:
        service.create_authority(receipt=receipt, caption_bytes=captions)
    assert caught.value.code == "RECEIPT_REPLAYED"
    assert service.authority_count == 1
    assert service.get_authority(receipt.receipt_checksum) == authority


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


def test_t05b_restore_quarantines_persisted_tamper(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    receipt = _receipt()
    state_path = tmp_path / "tamper.json"
    service = _service(
        cut1_audio,
        state_path=state_path,
        receipt=receipt,
        provider=_FakeProvider(_result(tts_provider, receipt)),
    )
    service.create_authority(receipt=receipt, caption_bytes=_captions(receipt.spoken_text))
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert _replace_first(payload, receipt.presenter_id, "raj")
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    restored = _service(
        cut1_audio,
        state_path=state_path,
        receipt=receipt,
        provider=None,
    )

    assert restored.authority_count == 0
    assert restored.quarantine_reason


def test_t05b_restore_rejects_valid_but_rolled_back_narration_authority(
    cut1_audio: ModuleType,
    tts_provider: ModuleType,
    tmp_path: Path,
) -> None:
    old_receipt = _receipt(version=1)
    current_receipt = _receipt(version=2)
    state_path = tmp_path / "rollback.json"
    old_service = _service(
        cut1_audio,
        state_path=state_path,
        receipt=old_receipt,
        provider=_FakeProvider(_result(tts_provider, old_receipt)),
    )
    old_service.create_authority(
        receipt=old_receipt,
        caption_bytes=_captions(old_receipt.spoken_text),
    )

    restored = _service(
        cut1_audio,
        state_path=state_path,
        receipt=current_receipt,
        provider=None,
    )

    assert restored.authority_count == 0
    assert restored.quarantine_reason
