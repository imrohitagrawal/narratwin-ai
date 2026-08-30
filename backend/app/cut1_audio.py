"""Offline, provider-neutral Cut 1 narration audio/caption authority binding.

This module validates already-materialized results. It has no provider, network,
credential, environment, synthesis, or media-generation capability.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import re
import struct
import sys
import threading
from array import array
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, NoReturn, cast

from backend.app.narration import TTSConsumptionReceipt, canonical_presenter_text
from backend.app.storage import write_state
from backend.app.tts_provider import ApprovedNarrationTTSResult, TTSProvider, TTSProviderError

SCHEMA = "cut1-audio-caption-authority-v1"
MAX_AUTHORITIES = 3
MAX_AUDIO_BYTES = 6_000_000
MAX_CAPTION_BYTES = 256_000
MAX_STATE_BYTES = 24_000_000
CHECKSUM = re.compile(r"sha256:[0-9a-f]{64}\Z")
CITATION = re.compile(r"\[(?:\d{1,3}(?:\s*,\s*\d{1,3})*)\]")
TIMING = re.compile(
    r"(?P<sh>\d{2}):(?P<sm>\d{2}):(?P<ss>\d{2}),(?P<sms>\d{3})"
    r" --> (?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2}),(?P<ems>\d{3})\Z"
)


class AudioCaptionAuthorityError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> NoReturn:
    raise AudioCaptionAuthorityError(code, message)


def _sha(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _json_sha(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return _sha(encoded)


def _pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise ValueError("Duplicate state member.")
        result[key] = value
    return result


@dataclass(frozen=True)
class Cut1AudioConfig:
    provider: str
    provider_mode: str
    requested_locale: str
    model_id: str
    presenter_voices: Mapping[str, str]
    config_checksum: str

    def __post_init__(self) -> None:
        voices = dict(self.presenter_voices)
        if (
            set(voices) != {"meera", "myra", "raj"}
            or any(not isinstance(value, str) or not value.strip() for value in voices.values())
            or any(
                not isinstance(value, str) or not value.strip()
                for value in (
                    self.provider,
                    self.provider_mode,
                    self.requested_locale,
                    self.model_id,
                )
            )
            or CHECKSUM.fullmatch(self.config_checksum) is None
        ):
            raise ValueError("Cut 1 audio configuration is invalid.")
        object.__setattr__(self, "presenter_voices", MappingProxyType(voices))


@dataclass(frozen=True)
class AudioMeasurements:
    duration_seconds: float
    sample_rate_hertz: int
    channels: int
    bits_per_sample: int
    frame_count: int
    rms: float
    peak: int
    active_ratio: float


@dataclass(frozen=True)
class CaptionCue:
    index: int
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class Cut1AudioCaptionAuthority:
    schema_version: str
    tenant_id: str
    actor_id: str
    project_id: str
    version: int
    narration_checksum: str
    presenter_id: str
    presenter_version: str
    presenter_binding_checksum: str
    source_run_id: str
    source_evaluation_checksum: str
    evaluation_checksum: str
    approval_checksum: str
    request_id: str
    trace_id: str
    receipt_checksum: str
    spoken_text_checksum: str
    provider: str
    provider_mode: str
    requested_voice: str
    requested_locale: str
    model_id: str
    request_checksum: str
    config_checksum: str
    audio_checksum: str
    audio_byte_count: int
    duration_seconds: float
    sample_rate_hertz: int
    channels: int
    bits_per_sample: int
    frame_count: int
    rms: float
    peak: int
    active_ratio: float
    caption_checksum: str
    caption_byte_count: int
    caption_text_checksum: str
    caption_timing_checksum: str
    cues: tuple[CaptionCue, ...]
    authority_checksum: str


def _milliseconds(match: re.Match[str], prefix: str) -> int:
    hours = int(match[f"{prefix}h"])
    minutes = int(match[f"{prefix}m"])
    seconds = int(match[f"{prefix}s"])
    millis = int(match[f"{prefix}ms"])
    if minutes >= 60 or seconds >= 60:
        _fail("CAPTION_TIMING_INVALID", "Caption time is invalid.")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def _validate_captions(
    caption_bytes: bytes, spoken_text: str, duration_seconds: float
) -> tuple[tuple[CaptionCue, ...], str, str]:
    if not caption_bytes or len(caption_bytes) > MAX_CAPTION_BYTES:
        _fail("CAPTION_TEXT_MISMATCH", "Caption bytes are empty or oversized.")
    try:
        text = caption_bytes.decode("utf-8")
    except UnicodeDecodeError:
        _fail("CAPTION_TEXT_MISMATCH", "Captions are not strict UTF-8.")
    if "\r" in text or not text.endswith("\n"):
        _fail("CAPTION_TEXT_MISMATCH", "Captions are not canonical SRT bytes.")
    cues: list[CaptionCue] = []
    previous_end = 0
    for expected_index, block in enumerate(text.rstrip("\n").split("\n\n"), start=1):
        lines = block.split("\n")
        if len(lines) < 3 or lines[0] != str(expected_index):
            _fail("CAPTION_TEXT_MISMATCH", "Caption indexes are noncanonical.")
        match = TIMING.fullmatch(lines[1])
        if match is None:
            _fail("CAPTION_TIMING_INVALID", "Caption timing is malformed.")
        start_ms = _milliseconds(match, "s")
        end_ms = _milliseconds(match, "e")
        cue_text = "\n".join(lines[2:])
        if (
            not cue_text.strip()
            or start_ms != previous_end
            or end_ms <= start_ms
            or end_ms > round(duration_seconds * 1000)
        ):
            _fail("CAPTION_TIMING_INVALID", "Caption timing is incomplete or overlapping.")
        cues.append(CaptionCue(expected_index, start_ms, end_ms, cue_text))
        previous_end = end_ms
    if not cues or previous_end != round(duration_seconds * 1000):
        _fail("CAPTION_TIMING_INVALID", "Captions do not cover the audio timeline.")
    caption_words = " ".join(" ".join(cue.text.split()) for cue in cues)
    spoken_words = " ".join(spoken_text.split())
    if caption_words != spoken_words or CITATION.search(caption_words):
        _fail("CAPTION_TEXT_MISMATCH", "Captions do not match exact spoken narration.")
    timing = [[cue.index, cue.start_ms, cue.end_ms] for cue in cues]
    return tuple(cues), _sha(spoken_words.encode("utf-8")), _json_sha(timing)


def _validate_wav(audio: bytes, duration_bounds: tuple[int, int]) -> AudioMeasurements:
    if (
        len(audio) < 44
        or len(audio) > MAX_AUDIO_BYTES
        or audio[:4] != b"RIFF"
        or audio[8:12] != b"WAVE"
    ):
        _fail("AUDIO_WAV_INVALID", "Audio is not a bounded RIFF/WAVE artifact.")
    if struct.unpack_from("<I", audio, 4)[0] != len(audio) - 8:
        _fail("AUDIO_WAV_INVALID", "WAV length is invalid.")
    offset = 12
    fmt: tuple[int, int, int, int, int, int] | None = None
    pcm: bytes | None = None
    seen: set[bytes] = set()
    while offset < len(audio):
        if offset + 8 > len(audio):
            _fail("AUDIO_WAV_INVALID", "WAV is truncated.")
        chunk_id = audio[offset : offset + 4]
        size = struct.unpack_from("<I", audio, offset + 4)[0]
        start, end = offset + 8, offset + 8 + size
        if chunk_id in seen or chunk_id not in {b"fmt ", b"data"} or end > len(audio) or size % 2:
            _fail("AUDIO_WAV_INVALID", "WAV chunks are invalid.")
        seen.add(chunk_id)
        if chunk_id == b"fmt ":
            if size != 16:
                _fail("AUDIO_WAV_INVALID", "WAV format is invalid.")
            fmt = struct.unpack_from("<HHIIHH", audio, start)
        else:
            pcm = audio[start:end]
        offset = end
    expected = (1, 1, 24_000, 48_000, 2, 16)
    if (
        offset != len(audio)
        or fmt != expected
        or pcm is None
        or not pcm
        or seen != {b"fmt ", b"data"}
    ):
        _fail("AUDIO_WAV_INVALID", "WAV must be mono PCM16 at 24 kHz.")
    frame_count = len(pcm) // 2
    duration = frame_count / 24_000
    if not duration_bounds[0] <= duration <= duration_bounds[1]:
        _fail("AUDIO_DURATION_INVALID", "Audio duration is outside the narration authority.")
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(value) for value in samples)
    rms = math.sqrt(sum(value * value for value in samples) / len(samples))
    active_ratio = sum(abs(value) >= 300 for value in samples) / len(samples)
    if peak < 500 or rms < 200 or active_ratio < 0.05:
        _fail("AUDIO_SILENT", "Audio is silent or near-silent.")
    return AudioMeasurements(duration, 24_000, 1, 16, frame_count, rms, peak, active_ratio)


def _authority_checksum(authority: Cut1AudioCaptionAuthority) -> str:
    payload = asdict(authority)
    payload.pop("authority_checksum")
    return _json_sha({"schema": SCHEMA, "authority": payload})


class Cut1AudioAuthorityService:
    def __init__(
        self,
        *,
        provider: TTSProvider | None,
        receipt_validator: Callable[[TTSConsumptionReceipt], bool],
        approved_config: Cut1AudioConfig,
        state_path: Path | None = None,
    ) -> None:
        self.provider = provider
        self.receipt_validator = receipt_validator
        self.approved_config = approved_config
        self.state_path = state_path
        self._authorities: dict[str, Cut1AudioCaptionAuthority] = {}
        self._rows: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self.quarantine_reason: str | None = None
        self._restore()

    @property
    def authority_count(self) -> int:
        return len(self._authorities)

    def get_authority(self, receipt_checksum: str) -> Cut1AudioCaptionAuthority:
        return self._authorities[receipt_checksum]

    def create_authority(
        self, *, receipt: TTSConsumptionReceipt, caption_bytes: bytes
    ) -> Cut1AudioCaptionAuthority:
        with self._lock:
            if self.quarantine_reason is not None:
                _fail("AUTHORITY_STATE_QUARANTINED", "Audio authority state is quarantined.")
            self._validate_receipt(receipt)
            if receipt.receipt_checksum in self._authorities:
                _fail("RECEIPT_REPLAYED", "Narration receipt was already bound.")
            if self.provider is None:
                _fail("TTS_PROVIDER_DISABLED", "Approved narration TTS is disabled.")
            try:
                result = self.provider.synthesize(receipt=receipt)
            except TTSProviderError as error:
                raise AudioCaptionAuthorityError(error.code, error.message) from error
            authority = self._validate_candidate(receipt, result, caption_bytes)
            row = self._row(receipt, result, caption_bytes, authority)
            candidate_rows = [*self._rows, row]
            self._persist(candidate_rows)
            self._rows = candidate_rows
            self._authorities[receipt.receipt_checksum] = authority
            return authority

    def _validate_receipt(self, receipt: TTSConsumptionReceipt) -> None:
        try:
            current = self.receipt_validator(receipt)
        except Exception:
            current = False
        if not current:
            _fail("NARRATION_AUTHORITY_STALE", "Narration receipt is not current.")
        checksums = (
            receipt.narration_checksum,
            receipt.presenter_binding_checksum,
            receipt.source_evaluation_checksum,
            receipt.evaluation_checksum,
            receipt.approval_checksum,
            receipt.receipt_checksum,
        )
        if (
            receipt.presenter_id not in self.approved_config.presenter_voices
            or receipt.duration_requirement_seconds != (90, 120)
            or any(CHECKSUM.fullmatch(value) is None for value in checksums)
        ):
            _fail("NARRATION_AUTHORITY_STALE", "Narration receipt shape is invalid.")
        if CITATION.search(receipt.spoken_text):
            _fail("SPOKEN_CITATION_MARKER", "Spoken narration contains a citation marker.")
        if receipt.spoken_text != canonical_presenter_text(receipt.presenter_id):
            _fail("NARRATION_AUTHORITY_STALE", "Spoken narration is noncanonical.")

    def _validate_candidate(
        self,
        receipt: TTSConsumptionReceipt,
        result: ApprovedNarrationTTSResult,
        caption_bytes: bytes,
    ) -> Cut1AudioCaptionAuthority:
        if result.presenter_id != receipt.presenter_id:
            _fail("PRESENTER_BINDING_MISMATCH", "Audio presenter does not match narration.")
        if result.receipt_checksum != receipt.receipt_checksum:
            _fail("RECEIPT_BINDING_MISMATCH", "Audio receipt does not match narration.")
        if CHECKSUM.fullmatch(result.request_checksum) is None:
            _fail("REQUEST_BINDING_INVALID", "Audio request checksum is invalid.")
        if CHECKSUM.fullmatch(result.config_checksum) is None:
            _fail("CONFIG_BINDING_INVALID", "Audio configuration checksum is invalid.")
        config = self.approved_config
        expected = (
            config.provider,
            config.provider_mode,
            config.presenter_voices[receipt.presenter_id],
            config.requested_locale,
            config.model_id,
            config.config_checksum,
        )
        observed = (
            result.provider,
            result.provider_mode,
            result.requested_voice,
            result.requested_locale,
            result.model_id,
            result.config_checksum,
        )
        if observed != expected:
            _fail("CONFIG_BINDING_MISMATCH", "Audio configuration is not approved.")
        if result.mime_type != "audio/wav" or not isinstance(result.audio_bytes, bytes):
            _fail("AUDIO_WAV_INVALID", "Audio artifact type is invalid.")
        audio_checksum = _sha(result.audio_bytes)
        if audio_checksum != result.artifact_checksum:
            _fail("AUDIO_CHECKSUM_MISMATCH", "Audio checksum does not match bytes.")
        measurements = _validate_wav(result.audio_bytes, receipt.duration_requirement_seconds)
        cues, caption_text_checksum, caption_timing_checksum = _validate_captions(
            caption_bytes, receipt.spoken_text, measurements.duration_seconds
        )
        values: dict[str, Any] = {
            "schema_version": SCHEMA,
            **{
                name: getattr(receipt, name)
                for name in (
                    "tenant_id",
                    "actor_id",
                    "project_id",
                    "version",
                    "narration_checksum",
                    "presenter_id",
                    "presenter_version",
                    "presenter_binding_checksum",
                    "source_run_id",
                    "source_evaluation_checksum",
                    "evaluation_checksum",
                    "approval_checksum",
                    "request_id",
                    "trace_id",
                    "receipt_checksum",
                )
            },
            "spoken_text_checksum": _sha(receipt.spoken_text.encode("utf-8")),
            **{
                name: getattr(result, name)
                for name in (
                    "provider",
                    "provider_mode",
                    "requested_voice",
                    "requested_locale",
                    "model_id",
                    "request_checksum",
                    "config_checksum",
                )
            },
            "audio_checksum": audio_checksum,
            "audio_byte_count": len(result.audio_bytes),
            **asdict(measurements),
            "caption_checksum": _sha(caption_bytes),
            "caption_byte_count": len(caption_bytes),
            "caption_text_checksum": caption_text_checksum,
            "caption_timing_checksum": caption_timing_checksum,
            "cues": cues,
            "authority_checksum": "",
        }
        authority = Cut1AudioCaptionAuthority(**values)
        return Cut1AudioCaptionAuthority(
            **{
                **asdict(authority),
                "cues": authority.cues,
                "authority_checksum": _authority_checksum(authority),
            }
        )

    @staticmethod
    def _row(
        receipt: TTSConsumptionReceipt,
        result: ApprovedNarrationTTSResult,
        caption_bytes: bytes,
        authority: Cut1AudioCaptionAuthority,
    ) -> dict[str, Any]:
        receipt_row = asdict(receipt)
        result_row = {
            name: getattr(result, name)
            for name in (
                "provider",
                "provider_mode",
                "presenter_id",
                "requested_voice",
                "requested_locale",
                "model_id",
                "receipt_checksum",
                "request_checksum",
                "config_checksum",
                "mime_type",
                "artifact_checksum",
            )
        }
        result_row["audioBase64"] = base64.b64encode(result.audio_bytes).decode("ascii")
        return {
            "receipt": receipt_row,
            "result": result_row,
            "captionBase64": base64.b64encode(caption_bytes).decode("ascii"),
            "authority": asdict(authority),
        }

    def _persist(self, rows: list[dict[str, Any]]) -> None:
        if self.state_path is None:
            return
        core = {"schema": SCHEMA, "records": rows}
        write_state(self.state_path, {**core, "stateChecksum": _json_sha(core)})

    def _restore(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            if (
                self.state_path.is_symlink()
                or not self.state_path.is_file()
                or self.state_path.stat().st_size > MAX_STATE_BYTES
            ):
                raise ValueError("Unsafe state path.")
            payload = json.loads(
                self.state_path.read_bytes().decode("utf-8"), object_pairs_hook=_pairs
            )
            if not isinstance(payload, dict) or set(payload) != {
                "schema",
                "records",
                "stateChecksum",
            }:
                raise ValueError("State schema.")
            core = {"schema": payload["schema"], "records": payload["records"]}
            if payload["schema"] != SCHEMA or payload["stateChecksum"] != _json_sha(core):
                raise ValueError("State checksum.")
            records = payload["records"]
            if not isinstance(records, list) or len(records) > MAX_AUTHORITIES:
                raise ValueError("State count.")
            restored: dict[str, Cut1AudioCaptionAuthority] = {}
            restored_rows: list[dict[str, Any]] = []
            for row in records:
                receipt, result, captions, stored = self._decode_row(row)
                self._validate_receipt(receipt)
                authority = self._validate_candidate(receipt, result, captions)
                if (
                    _json_sha(asdict(authority)) != _json_sha(stored)
                    or receipt.receipt_checksum in restored
                ):
                    raise ValueError("Authority mismatch.")
                restored[receipt.receipt_checksum] = authority
                restored_rows.append(cast(dict[str, Any], row))
            self._authorities, self._rows = restored, restored_rows
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            binascii.Error,
            KeyError,
            TypeError,
            ValueError,
            AudioCaptionAuthorityError,
        ):
            self._authorities, self._rows = {}, []
            self.quarantine_reason = "STATE_INVALID"

    @staticmethod
    def _decode_row(
        value: Any,
    ) -> tuple[TTSConsumptionReceipt, ApprovedNarrationTTSResult, bytes, dict[str, Any]]:
        if not isinstance(value, dict) or set(value) != {
            "receipt",
            "result",
            "captionBase64",
            "authority",
        }:
            raise ValueError("Record schema.")
        receipt_row = cast(dict[str, Any], value["receipt"])
        receipt_row = dict(receipt_row)
        receipt_row["duration_requirement_seconds"] = tuple(
            receipt_row["duration_requirement_seconds"]
        )
        receipt = TTSConsumptionReceipt(**receipt_row)
        result_row = cast(dict[str, Any], value["result"])
        if set(result_row) != {
            "provider",
            "provider_mode",
            "presenter_id",
            "requested_voice",
            "requested_locale",
            "model_id",
            "receipt_checksum",
            "request_checksum",
            "config_checksum",
            "mime_type",
            "artifact_checksum",
            "audioBase64",
        }:
            raise ValueError("Result schema.")
        audio = base64.b64decode(result_row["audioBase64"], validate=True)
        captions = base64.b64decode(value["captionBase64"], validate=True)
        result = ApprovedNarrationTTSResult(
            **{name: result_row[name] for name in result_row if name != "audioBase64"},
            audio_bytes=audio,
        )
        stored = cast(dict[str, Any], value["authority"])
        return receipt, result, captions, stored
