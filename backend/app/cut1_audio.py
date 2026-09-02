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

from backend.app.narration import (
    TTSConsumptionReceipt,
    canonical_presenter_text,
    validate_duration_requirement,
)
from backend.app.storage import write_state
from backend.app.tts_provider import ApprovedNarrationTTSResult

SCHEMA = "cut1-audio-caption-authority-v2"
CONFIG_SCHEMA = "cut1-audio-config-v1"
COMMITMENT_SCHEMA = "cut1-audio-commitment-v2"
MANIFEST_SCHEMA = "cut1-audio-commitment-manifest-v2"
MAX_AUTHORITIES = 3
MAX_MANIFEST_SEQUENCE = 2_147_483_647
MAX_CAPTION_BYTES = 256_000
MAX_STATE_BYTES = 24_000_000
CHECKSUM = re.compile(r"sha256:[0-9a-f]{64}\Z")
BARE_CHECKSUM = re.compile(r"[0-9a-f]{64}\Z")
LOCAL_PROVIDER_MODES = frozenset({"LOCAL", "MOCK"})
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


def build_audio_config_checksum(
    *,
    provider: str,
    provider_mode: str,
    requested_locale: str,
    model_id: str,
    presenter_voices: Mapping[str, str],
) -> str:
    return _json_sha(
        {
            "schema": CONFIG_SCHEMA,
            "provider": provider,
            "providerMode": provider_mode,
            "requestedLocale": requested_locale,
            "modelId": model_id,
            "presenterVoices": dict(sorted(presenter_voices.items())),
        }
    )


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
        expected_checksum = build_audio_config_checksum(
            provider=self.provider,
            provider_mode=self.provider_mode,
            requested_locale=self.requested_locale,
            model_id=self.model_id,
            presenter_voices=voices,
        )
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
            or self.config_checksum != expected_checksum
        ):
            raise ValueError("Cut 1 audio configuration is invalid.")
        object.__setattr__(self, "presenter_voices", MappingProxyType(voices))


@dataclass(frozen=True)
class Cut1AudioCommitment:
    presenter_id: str
    receipt_checksum: str
    request_checksum: str
    config_checksum: str
    provider_runtime_config_checksum: str | None
    authority_checksum: str


@dataclass(frozen=True)
class Cut1AudioCommitmentManifest:
    schema_version: str
    sequence: int
    commitments: tuple[Cut1AudioCommitment, ...]
    manifest_checksum: str


@dataclass(frozen=True)
class Cut1AudioCandidate:
    receipt: TTSConsumptionReceipt
    result: ApprovedNarrationTTSResult
    caption_bytes: bytes
    config_checksum: str
    provider_runtime_config_checksum: str | None


def _commitment_payload(commitment: Cut1AudioCommitment) -> dict[str, str | None]:
    return {
        "schema": COMMITMENT_SCHEMA,
        "presenterId": commitment.presenter_id,
        "receiptChecksum": commitment.receipt_checksum,
        "requestChecksum": commitment.request_checksum,
        "configChecksum": commitment.config_checksum,
        "providerRuntimeConfigChecksum": commitment.provider_runtime_config_checksum,
        "authorityChecksum": commitment.authority_checksum,
    }


def build_audio_commitment_manifest(
    *, sequence: int, commitments: tuple[Cut1AudioCommitment, ...]
) -> Cut1AudioCommitmentManifest:
    checksum = _json_sha(
        {
            "schema": MANIFEST_SCHEMA,
            "sequence": sequence,
            "commitments": [_commitment_payload(value) for value in commitments],
        }
    )
    return Cut1AudioCommitmentManifest(
        schema_version=MANIFEST_SCHEMA,
        sequence=sequence,
        commitments=commitments,
        manifest_checksum=checksum,
    )


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
    provider_runtime_config_checksum: str | None
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


def audio_commitment(authority: Cut1AudioCaptionAuthority) -> Cut1AudioCommitment:
    return Cut1AudioCommitment(
        presenter_id=authority.presenter_id,
        receipt_checksum=authority.receipt_checksum,
        request_checksum=authority.request_checksum,
        config_checksum=authority.config_checksum,
        provider_runtime_config_checksum=authority.provider_runtime_config_checksum,
        authority_checksum=authority.authority_checksum,
    )


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
    try:
        _, maximum_seconds = validate_duration_requirement(duration_bounds)
    except ValueError:
        _fail("AUDIO_DURATION_INVALID", "Audio duration authority is invalid.")
    maximum_audio_bytes = 44 + maximum_seconds * 24_000 * 2
    if len(audio) > maximum_audio_bytes:
        _fail("AUDIO_DURATION_INVALID", "Audio duration is outside the narration authority.")
    if (
        len(audio) < 44
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
        receipt_validator: Callable[[TTSConsumptionReceipt], bool],
        commitment_resolver: Callable[[], Cut1AudioCommitmentManifest],
        approved_config: Cut1AudioConfig,
        state_path: Path | None = None,
    ) -> None:
        self.receipt_validator = receipt_validator
        self.commitment_resolver = commitment_resolver
        self.approved_config = approved_config
        self.state_path = state_path
        self._authorities: dict[str, Cut1AudioCaptionAuthority] = {}
        self._receipts: dict[str, TTSConsumptionReceipt] = {}
        self._rows: list[dict[str, Any]] = []
        self._manifest: Cut1AudioCommitmentManifest | None = None
        self._lock = threading.RLock()
        self.quarantine_reason: str | None = None
        self._restore()

    @property
    def authority_count(self) -> int:
        return len(self._authorities)

    def get_authority(self, receipt: TTSConsumptionReceipt) -> Cut1AudioCaptionAuthority:
        with self._lock:
            if self.quarantine_reason is not None:
                _fail("AUTHORITY_STATE_QUARANTINED", "Audio authority state is quarantined.")
            self._validate_receipt(receipt)
            authority = self._authorities.get(receipt.receipt_checksum)
            if authority is None or self._receipts.get(receipt.receipt_checksum) != receipt:
                _fail("AUTHORITY_NOT_FOUND", "Current audio authority is unavailable.")
            manifest = self._trusted_manifest()
            stored_commitments = tuple(
                audio_commitment(value) for value in self._authorities.values()
            )
            if self._manifest != manifest or stored_commitments != manifest.commitments:
                _fail("AUTHORITY_COMMITMENT_STALE", "Audio authority set is not current.")
            return authority

    def evaluate_authority(
        self, *, candidate: Cut1AudioCandidate
    ) -> Cut1AudioCaptionAuthority:
        self._validate_receipt(candidate.receipt)
        return self._validate_candidate(
            candidate.receipt,
            candidate.result,
            candidate.caption_bytes,
            candidate.config_checksum,
            candidate.provider_runtime_config_checksum,
        )

    def admit_authorities(
        self, *, candidates: tuple[Cut1AudioCandidate, ...]
    ) -> tuple[Cut1AudioCaptionAuthority, ...]:
        with self._lock:
            if self.quarantine_reason is not None:
                _fail("AUTHORITY_STATE_QUARANTINED", "Audio authority state is quarantined.")
            manifest = self._trusted_manifest()
            self._validate_manifest_transition(manifest)
            if not candidates or len(candidates) != len(manifest.commitments):
                _fail("AUTHORITY_SET_INCOMPLETE", "Audio authority set is incomplete.")
            authorities = tuple(self.evaluate_authority(candidate=value) for value in candidates)
            commitments = tuple(audio_commitment(value) for value in authorities)
            if commitments != manifest.commitments:
                _fail("AUTHORITY_COMMITMENT_MISMATCH", "Audio authority set is not trusted.")
            receipt_checksums = tuple(value.receipt.receipt_checksum for value in candidates)
            if receipt_checksums == tuple(self._authorities) and self._authorities:
                _fail("RECEIPT_REPLAYED", "Narration receipt was already bound.")
            for candidate in candidates:
                self._validate_receipt(candidate.receipt)
            if self._trusted_manifest() != manifest:
                _fail("AUTHORITY_COMMITMENT_STALE", "Audio commitment changed during admission.")
            rows = [
                self._row(value, authority)
                for value, authority in zip(candidates, authorities, strict=True)
            ]
            self._persist(rows, manifest)
            try:
                for candidate in candidates:
                    self._validate_receipt(candidate.receipt)
                if self._trusted_manifest() != manifest:
                    _fail(
                        "AUTHORITY_COMMITMENT_STALE",
                        "Audio commitment changed during admission.",
                    )
            except AudioCaptionAuthorityError:
                self._authorities, self._receipts, self._rows = {}, {}, []
                self._manifest = None
                self.quarantine_reason = "STATE_INVALID"
                raise
            self._rows = rows
            self._authorities = {
                value.receipt.receipt_checksum: authority
                for value, authority in zip(candidates, authorities, strict=True)
            }
            self._receipts = {
                value.receipt.receipt_checksum: value.receipt for value in candidates
            }
            self._manifest = manifest
            return authorities

    def _validate_manifest_transition(
        self, manifest: Cut1AudioCommitmentManifest
    ) -> None:
        current = self._manifest
        if current is None:
            return
        if manifest.sequence < current.sequence or (
            manifest.sequence == current.sequence and manifest != current
        ):
            self._authorities, self._receipts, self._rows = {}, {}, []
            self._manifest = None
            self.quarantine_reason = "STATE_INVALID"
            _fail("AUTHORITY_COMMITMENT_STALE", "Audio commitment manifest regressed.")

    def _trusted_manifest(self) -> Cut1AudioCommitmentManifest:
        try:
            manifest = self.commitment_resolver()
        except Exception:
            _fail("AUTHORITY_COMMITMENT_UNAVAILABLE", "Trusted commitment is unavailable.")
        if not isinstance(manifest, Cut1AudioCommitmentManifest):
            _fail("AUTHORITY_COMMITMENT_INVALID", "Trusted commitment is invalid.")
        commitments = manifest.commitments
        presenters = tuple(value.presenter_id for value in commitments)
        receipt_checksums = tuple(value.receipt_checksum for value in commitments)
        expected = build_audio_commitment_manifest(
            sequence=manifest.sequence, commitments=commitments
        )
        if (
            manifest.schema_version != MANIFEST_SCHEMA
            or type(manifest.sequence) is not int
            or not 1 <= manifest.sequence <= MAX_MANIFEST_SEQUENCE
            or not 0 < len(commitments) <= MAX_AUTHORITIES
            or presenters != tuple(sorted(presenters))
            or len(set(presenters)) != len(presenters)
            or len(set(receipt_checksums)) != len(receipt_checksums)
            or any(
                value.presenter_id not in self.approved_config.presenter_voices
                or value.config_checksum != self.approved_config.config_checksum
                or (
                    self.approved_config.provider_mode in LOCAL_PROVIDER_MODES
                    and value.provider_runtime_config_checksum is not None
                )
                or (
                    self.approved_config.provider_mode not in LOCAL_PROVIDER_MODES
                    and (
                        not isinstance(value.provider_runtime_config_checksum, str)
                        or CHECKSUM.fullmatch(value.provider_runtime_config_checksum) is None
                        or value.provider_runtime_config_checksum == value.config_checksum
                    )
                )
                or any(
                    not isinstance(checksum, str) or CHECKSUM.fullmatch(checksum) is None
                    for checksum in (
                        value.receipt_checksum,
                        value.request_checksum,
                        value.config_checksum,
                        value.authority_checksum,
                    )
                )
                for value in commitments
            )
            or manifest.manifest_checksum != expected.manifest_checksum
        ):
            _fail("AUTHORITY_COMMITMENT_INVALID", "Trusted commitment is invalid.")
        return manifest

    def _validate_receipt(self, receipt: TTSConsumptionReceipt) -> None:
        try:
            current = self.receipt_validator(receipt)
        except Exception:
            current = False
        if not current:
            _fail("NARRATION_AUTHORITY_STALE", "Narration receipt is not current.")
        checksums = (
            receipt.narration_checksum,
            receipt.source_evaluation_checksum,
            receipt.evaluation_checksum,
            receipt.approval_checksum,
            receipt.receipt_checksum,
        )
        try:
            validate_duration_requirement(receipt.duration_requirement_seconds)
        except ValueError:
            _fail("NARRATION_AUTHORITY_STALE", "Narration receipt shape is invalid.")
        if (
            receipt.presenter_id not in self.approved_config.presenter_voices
            or not isinstance(receipt.presenter_binding_checksum, str)
            or BARE_CHECKSUM.fullmatch(receipt.presenter_binding_checksum) is None
            or any(
                not isinstance(value, str) or CHECKSUM.fullmatch(value) is None
                for value in checksums
            )
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
        config_checksum: str,
        provider_runtime_config_checksum: str | None,
    ) -> Cut1AudioCaptionAuthority:
        if result.presenter_id != receipt.presenter_id:
            _fail("PRESENTER_BINDING_MISMATCH", "Audio presenter does not match narration.")
        if result.receipt_checksum != receipt.receipt_checksum:
            _fail("RECEIPT_BINDING_MISMATCH", "Audio receipt does not match narration.")
        if CHECKSUM.fullmatch(result.request_checksum) is None:
            _fail("REQUEST_BINDING_INVALID", "Audio request checksum is invalid.")
        if (
            not isinstance(config_checksum, str)
            or CHECKSUM.fullmatch(config_checksum) is None
            or not isinstance(result.config_checksum, str)
            or CHECKSUM.fullmatch(result.config_checksum) is None
        ):
            _fail("CONFIG_BINDING_INVALID", "Audio configuration checksum is invalid.")
        config = self.approved_config
        expected = (
            config.provider,
            config.provider_mode,
            config.presenter_voices[receipt.presenter_id],
            config.requested_locale,
            config.model_id,
        )
        observed = (
            result.provider,
            result.provider_mode,
            result.requested_voice,
            result.requested_locale,
            result.model_id,
        )
        if observed != expected or config_checksum != config.config_checksum:
            _fail("CONFIG_BINDING_MISMATCH", "Audio configuration is not approved.")
        if config.provider_mode in LOCAL_PROVIDER_MODES:
            if provider_runtime_config_checksum is not None:
                _fail(
                    "PROVIDER_RUNTIME_CONFIG_FORBIDDEN",
                    "Local audio must not fabricate hosted runtime authority.",
                )
            if result.config_checksum != config_checksum:
                _fail("CONFIG_BINDING_MISMATCH", "Audio configuration is not approved.")
        else:
            if provider_runtime_config_checksum is None:
                _fail(
                    "PROVIDER_RUNTIME_CONFIG_REQUIRED",
                    "Hosted audio runtime authority is required.",
                )
            if (
                not isinstance(provider_runtime_config_checksum, str)
                or CHECKSUM.fullmatch(provider_runtime_config_checksum) is None
            ):
                _fail(
                    "PROVIDER_RUNTIME_CONFIG_INVALID",
                    "Hosted audio runtime authority is invalid.",
                )
            if provider_runtime_config_checksum == config_checksum:
                _fail(
                    "PROVIDER_RUNTIME_CONFIG_NOT_DISTINCT",
                    "Hosted runtime and public configurations must be distinct.",
                )
            if result.config_checksum != provider_runtime_config_checksum:
                _fail(
                    "PROVIDER_RUNTIME_CONFIG_MISMATCH",
                    "Hosted audio runtime authority does not match the provider result.",
                )
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
                )
            },
            "config_checksum": config_checksum,
            "provider_runtime_config_checksum": provider_runtime_config_checksum,
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
        candidate: Cut1AudioCandidate,
        authority: Cut1AudioCaptionAuthority,
    ) -> dict[str, Any]:
        receipt = candidate.receipt
        result = candidate.result
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
            "configChecksum": candidate.config_checksum,
            "providerRuntimeConfigChecksum": candidate.provider_runtime_config_checksum,
            "captionBase64": base64.b64encode(candidate.caption_bytes).decode("ascii"),
            "authority": asdict(authority),
        }

    def _persist(
        self, rows: list[dict[str, Any]], manifest: Cut1AudioCommitmentManifest
    ) -> None:
        if self.state_path is None:
            return
        core = {
            "schema": SCHEMA,
            "manifestSequence": manifest.sequence,
            "manifestChecksum": manifest.manifest_checksum,
            "records": rows,
        }
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
                "manifestSequence",
                "manifestChecksum",
                "records",
                "stateChecksum",
            }:
                raise ValueError("State schema.")
            persisted_sequence = payload["manifestSequence"]
            if (
                type(persisted_sequence) is not int
                or not 1 <= persisted_sequence <= MAX_MANIFEST_SEQUENCE
            ):
                raise ValueError("State manifest sequence.")
            core = {
                "schema": payload["schema"],
                "manifestSequence": payload["manifestSequence"],
                "manifestChecksum": payload["manifestChecksum"],
                "records": payload["records"],
            }
            if payload["schema"] != SCHEMA or payload["stateChecksum"] != _json_sha(core):
                raise ValueError("State checksum.")
            manifest = self._trusted_manifest()
            if (
                payload["manifestSequence"] != manifest.sequence
                or payload["manifestChecksum"] != manifest.manifest_checksum
            ):
                raise ValueError("State manifest.")
            records = payload["records"]
            if not isinstance(records, list) or len(records) != len(manifest.commitments):
                raise ValueError("State count.")
            restored: dict[str, Cut1AudioCaptionAuthority] = {}
            restored_receipts: dict[str, TTSConsumptionReceipt] = {}
            restored_rows: list[dict[str, Any]] = []
            restored_commitments: list[Cut1AudioCommitment] = []
            for row in records:
                candidate, stored = self._decode_row(row)
                receipt = candidate.receipt
                self._validate_receipt(receipt)
                authority = self._validate_candidate(
                    receipt,
                    candidate.result,
                    candidate.caption_bytes,
                    candidate.config_checksum,
                    candidate.provider_runtime_config_checksum,
                )
                if (
                    _json_sha(asdict(authority)) != _json_sha(stored)
                    or receipt.receipt_checksum in restored
                ):
                    raise ValueError("Authority mismatch.")
                restored[receipt.receipt_checksum] = authority
                restored_receipts[receipt.receipt_checksum] = receipt
                restored_commitments.append(audio_commitment(authority))
                restored_rows.append(cast(dict[str, Any], row))
            if tuple(restored_commitments) != manifest.commitments:
                raise ValueError("State commitments.")
            self._authorities = restored
            self._receipts = restored_receipts
            self._rows = restored_rows
            self._manifest = manifest
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
            self._authorities, self._receipts, self._rows = {}, {}, []
            self._manifest = None
            self.quarantine_reason = "STATE_INVALID"

    @staticmethod
    def _decode_row(
        value: Any,
    ) -> tuple[Cut1AudioCandidate, dict[str, Any]]:
        if not isinstance(value, dict) or set(value) != {
            "receipt",
            "result",
            "configChecksum",
            "providerRuntimeConfigChecksum",
            "captionBase64",
            "authority",
        }:
            raise ValueError("Record schema.")
        if any(
            not isinstance(value[name], dict)
            for name in ("receipt", "result", "authority")
        ):
            raise ValueError("Record object schema.")
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
        candidate = Cut1AudioCandidate(
            receipt=receipt,
            result=result,
            caption_bytes=captions,
            config_checksum=cast(str, value["configChecksum"]),
            provider_runtime_config_checksum=cast(
                str | None, value["providerRuntimeConfigChecksum"]
            ),
        )
        return candidate, stored
