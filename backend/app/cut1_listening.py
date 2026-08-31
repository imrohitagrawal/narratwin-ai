"""Metadata-only exact-hash authority for independently authored Cut 1 listening decisions."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import threading
from dataclasses import dataclass, fields, replace
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, NoReturn

from backend.app.cut1_audio import (
    Cut1AudioCaptionAuthority,
    _authority_checksum as canonical_audio_authority_checksum,
    audio_commitment,
    build_audio_commitment_manifest,
)
from backend.app.storage import write_state

SCHEMA = "cut1-listening-authority-v1"
DECISION_SCHEMA = "cut1-human-listening-decision-v1"
COMMITMENT_SCHEMA = "cut1-listening-decision-commitment-v1"
MANIFEST_SCHEMA = "cut1-listening-decision-manifest-v1"
PRESENTERS = ("meera", "myra", "raj")
LISTENING_CRITERIA = (
    "intelligibility",
    "exact_spoken_words",
    "pronunciation",
    "naturalness",
    "accent",
    "effective_selected_voice_identity",
    "warmth",
    "pacing",
    "presenter_fit",
)
MAX_STATE_BYTES = 256_000
MAX_SEQUENCE = 2_147_483_647
CHECKSUM = re.compile(r"sha256:[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}\Z")
UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


class ListeningAuthorityError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> NoReturn:
    raise ListeningAuthorityError(code, message)


def _json_sha(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise ValueError("Duplicate state member.")
        result[key] = value
    return result


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


@dataclass(frozen=True)
class CurrentCut1AudioAuthoritySet:
    manifest_sequence: int
    manifest_checksum: str
    authorities: tuple[Cut1AudioCaptionAuthority, ...]


@dataclass(frozen=True)
class Cut1ListeningArtifactBinding:
    audio_manifest_sequence: int
    audio_manifest_checksum: str
    presenter_id: str
    presenter_version: str
    presenter_binding_checksum: str
    requested_voice: str
    narration_checksum: str
    source_run_id: str
    source_evaluation_checksum: str
    evaluation_checksum: str
    approval_checksum: str
    receipt_checksum: str
    spoken_text_checksum: str
    request_checksum: str
    config_checksum: str
    provider_runtime_config_checksum: str | None
    audio_checksum: str
    caption_checksum: str
    caption_text_checksum: str
    caption_timing_checksum: str
    audio_authority_checksum: str


@dataclass(frozen=True)
class Cut1ListeningDecision:
    decision_id: str
    reviewer_id: str
    artifact_author_id: str
    reviewed_at: str
    binding: Cut1ListeningArtifactBinding
    criteria: Mapping[str, bool]
    decision_checksum: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "criteria", MappingProxyType(dict(self.criteria)))


@dataclass(frozen=True)
class Cut1ListeningDecisionCommitment:
    presenter_id: str
    decision_id: str
    reviewer_id: str
    artifact_author_id: str
    decision_checksum: str


@dataclass(frozen=True)
class Cut1ListeningDecisionManifest:
    schema_version: str
    sequence: int
    audio_manifest_sequence: int
    audio_manifest_checksum: str
    commitments: tuple[Cut1ListeningDecisionCommitment, ...]
    revoked_decision_ids: tuple[str, ...]
    manifest_checksum: str


@dataclass(frozen=True)
class Cut1ListeningAuthority:
    schema_version: str
    audio_manifest_sequence: int
    audio_manifest_checksum: str
    decision_manifest_sequence: int
    decision_manifest_checksum: str
    decisions: tuple[Cut1ListeningDecision, ...]
    authority_checksum: str


def _binding_payload(value: Cut1ListeningArtifactBinding) -> dict[str, Any]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _decision_payload(value: Cut1ListeningDecision) -> dict[str, Any]:
    return {
        "schema": DECISION_SCHEMA,
        "decisionId": value.decision_id,
        "reviewerId": value.reviewer_id,
        "artifactAuthorId": value.artifact_author_id,
        "reviewedAt": value.reviewed_at,
        "binding": _binding_payload(value.binding),
        "criteria": dict(value.criteria),
    }


def decision_checksum(decision: Cut1ListeningDecision) -> str:
    """Hash decision metadata; this does not create or attest a human decision."""
    return _json_sha(_decision_payload(decision))


def _commitment_payload(value: Cut1ListeningDecisionCommitment) -> dict[str, str]:
    return {
        "schema": COMMITMENT_SCHEMA,
        "presenterId": value.presenter_id,
        "decisionId": value.decision_id,
        "reviewerId": value.reviewer_id,
        "artifactAuthorId": value.artifact_author_id,
        "decisionChecksum": value.decision_checksum,
    }


def build_listening_commitment_manifest(
    *,
    sequence: int,
    audio_manifest_sequence: int,
    audio_manifest_checksum: str,
    commitments: tuple[Cut1ListeningDecisionCommitment, ...],
    revoked_decision_ids: tuple[str, ...] = (),
) -> Cut1ListeningDecisionManifest:
    core = {
        "schema": MANIFEST_SCHEMA,
        "sequence": sequence,
        "audioManifestSequence": audio_manifest_sequence,
        "audioManifestChecksum": audio_manifest_checksum,
        "commitments": [_commitment_payload(value) for value in commitments],
        "revokedDecisionIds": list(revoked_decision_ids),
    }
    return Cut1ListeningDecisionManifest(
        schema_version=MANIFEST_SCHEMA,
        sequence=sequence,
        audio_manifest_sequence=audio_manifest_sequence,
        audio_manifest_checksum=audio_manifest_checksum,
        commitments=commitments,
        revoked_decision_ids=revoked_decision_ids,
        manifest_checksum=_json_sha(core),
    )


def _binding(
    authority: Cut1AudioCaptionAuthority, current: CurrentCut1AudioAuthoritySet
) -> Cut1ListeningArtifactBinding:
    return Cut1ListeningArtifactBinding(
        audio_manifest_sequence=current.manifest_sequence,
        audio_manifest_checksum=current.manifest_checksum,
        **{
            name: getattr(authority, name)
            for name in (
                "presenter_id",
                "presenter_version",
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
            )
        },
        audio_authority_checksum=authority.authority_checksum,
    )


def _authority_checksum(value: Cut1ListeningAuthority) -> str:
    return _json_sha(
        {
            "schema": SCHEMA,
            "audioManifestSequence": value.audio_manifest_sequence,
            "audioManifestChecksum": value.audio_manifest_checksum,
            "decisionManifestSequence": value.decision_manifest_sequence,
            "decisionManifestChecksum": value.decision_manifest_checksum,
            "decisions": [
                _decision_payload(item) | {"decisionChecksum": item.decision_checksum}
                for item in value.decisions
            ],
        }
    )


class Cut1ListeningAuthorityService:
    def __init__(
        self,
        *,
        audio_authority_resolver: Callable[[], CurrentCut1AudioAuthoritySet],
        artifact_author_resolver: Callable[[], Mapping[str, str]],
        decision_commitment_resolver: Callable[[], Cut1ListeningDecisionManifest],
        state_path: Path | None = None,
    ) -> None:
        self.audio_authority_resolver = audio_authority_resolver
        self.artifact_author_resolver = artifact_author_resolver
        self.decision_commitment_resolver = decision_commitment_resolver
        self.state_path = state_path
        self._authority: Cut1ListeningAuthority | None = None
        self._audio: CurrentCut1AudioAuthoritySet | None = None
        self._manifest: Cut1ListeningDecisionManifest | None = None
        self._lock = threading.RLock()
        self.quarantine_reason: str | None = None
        self._restore()

    @property
    def authority_count(self) -> int:
        return 0 if self._authority is None else len(self._authority.decisions)

    def admit_decisions(
        self, *, decisions: tuple[Cut1ListeningDecision, ...]
    ) -> Cut1ListeningAuthority:
        with self._lock:
            if self.quarantine_reason is not None:
                _fail("AUTHORITY_STATE_QUARANTINED", "Listening state is quarantined.")
            if self._authority is not None:
                _fail("DECISION_REPLAYED", "Listening decisions were already consumed.")
            audio = self._trusted_audio()
            authors = self._trusted_authors()
            manifest = self._trusted_manifest(audio)
            authority = self._validate(decisions, audio, authors, manifest)
            self._persist(authority, "PREPARED")
            try:
                if (
                    self._trusted_audio() != audio
                    or self._trusted_authors() != authors
                    or self._trusted_manifest(audio) != manifest
                ):
                    _fail("DECISION_COMMITMENT_STALE", "Trusted authority changed during admission.")
                self._persist(authority, "COMMITTED")
            except (ListeningAuthorityError, OSError):
                self.quarantine_reason = "STATE_INVALID"
                raise
            self._authority, self._audio, self._manifest = authority, audio, manifest
            return authority

    def get_authority(self) -> Cut1ListeningAuthority:
        with self._lock:
            if self.quarantine_reason is not None:
                _fail("AUTHORITY_STATE_QUARANTINED", "Listening state is quarantined.")
            if self._authority is None or self._audio is None or self._manifest is None:
                _fail("AUTHORITY_NOT_FOUND", "Listening authority is unavailable.")
            try:
                audio = self._trusted_audio()
                authors = self._trusted_authors()
                manifest = self._trusted_manifest(audio)
                current = self._validate(self._authority.decisions, audio, authors, manifest)
            except ListeningAuthorityError:
                _fail("AUDIO_AUTHORITY_STALE", "Current T05B/listening authority drifted.")
            if audio != self._audio or manifest != self._manifest or current != self._authority:
                _fail("AUDIO_AUTHORITY_STALE", "Current T05B/listening authority drifted.")
            return self._authority

    def _trusted_audio(self) -> CurrentCut1AudioAuthoritySet:
        try:
            current = self.audio_authority_resolver()
        except Exception:
            _fail("AUDIO_AUTHORITY_UNAVAILABLE", "Current T05B authority is unavailable.")
        if not isinstance(current, CurrentCut1AudioAuthoritySet):
            _fail("AUDIO_AUTHORITY_INVALID", "Current T05B authority is invalid.")
        authorities = current.authorities
        try:
            manifest = build_audio_commitment_manifest(
                sequence=current.manifest_sequence,
                commitments=tuple(audio_commitment(value) for value in authorities),
            )
            canonical = tuple(canonical_audio_authority_checksum(value) for value in authorities)
        except (AttributeError, TypeError, ValueError):
            _fail("AUDIO_AUTHORITY_INVALID", "Current T05B authority is invalid.")
        if (
            type(current.manifest_sequence) is not int
            or not 1 <= current.manifest_sequence <= MAX_SEQUENCE
            or not all(isinstance(value, Cut1AudioCaptionAuthority) for value in authorities)
            or tuple(value.presenter_id for value in authorities) != PRESENTERS
            or tuple(value.authority_checksum for value in authorities) != canonical
            or current.manifest_checksum != manifest.manifest_checksum
        ):
            _fail("AUDIO_AUTHORITY_INVALID", "Current T05B authority is invalid.")
        return current

    def _trusted_authors(self) -> dict[str, str]:
        try:
            authors = dict(self.artifact_author_resolver())
        except Exception:
            _fail("ARTIFACT_AUTHOR_UNAVAILABLE", "Trusted artifact authors are unavailable.")
        if set(authors) != set(PRESENTERS) or any(
            not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None
            for value in authors.values()
        ):
            _fail("ARTIFACT_AUTHOR_INVALID", "Trusted artifact authors are invalid.")
        return authors

    def _trusted_manifest(
        self, audio: CurrentCut1AudioAuthoritySet
    ) -> Cut1ListeningDecisionManifest:
        try:
            manifest = self.decision_commitment_resolver()
        except Exception:
            _fail("DECISION_COMMITMENT_UNAVAILABLE", "Trusted decisions are unavailable.")
        if not isinstance(manifest, Cut1ListeningDecisionManifest):
            _fail("DECISION_COMMITMENT_INVALID", "Trusted decision commitment is invalid.")
        if (
            not isinstance(manifest.commitments, tuple)
            or not all(
                isinstance(value, Cut1ListeningDecisionCommitment)
                for value in manifest.commitments
            )
            or not isinstance(manifest.revoked_decision_ids, tuple)
            or any(not _valid_id(value) for value in manifest.revoked_decision_ids)
        ):
            _fail("DECISION_COMMITMENT_INVALID", "Trusted decision commitment is invalid.")
        try:
            expected = build_listening_commitment_manifest(
                sequence=manifest.sequence,
                audio_manifest_sequence=manifest.audio_manifest_sequence,
                audio_manifest_checksum=manifest.audio_manifest_checksum,
                commitments=manifest.commitments,
                revoked_decision_ids=manifest.revoked_decision_ids,
            )
        except (TypeError, ValueError):
            _fail("DECISION_COMMITMENT_INVALID", "Trusted decision commitment is invalid.")
        commitments = manifest.commitments
        if (
            manifest.schema_version != MANIFEST_SCHEMA
            or type(manifest.sequence) is not int
            or not 1 <= manifest.sequence <= MAX_SEQUENCE
            or manifest.audio_manifest_sequence != audio.manifest_sequence
            or manifest.audio_manifest_checksum != audio.manifest_checksum
            or not all(isinstance(value, Cut1ListeningDecisionCommitment) for value in commitments)
            or tuple(value.presenter_id for value in commitments) != PRESENTERS
            or len({value.decision_id for value in commitments}) != 3
            or len(set(manifest.revoked_decision_ids)) != len(manifest.revoked_decision_ids)
            or any(
                not all(
                    isinstance(item, str)
                    and (
                        CHECKSUM.fullmatch(item) is not None
                        if name == "decision_checksum"
                        else IDENTIFIER.fullmatch(item) is not None
                    )
                    for name, item in (
                        ("presenter_id", value.presenter_id),
                        ("decision_id", value.decision_id),
                        ("reviewer_id", value.reviewer_id),
                        ("artifact_author_id", value.artifact_author_id),
                        ("decision_checksum", value.decision_checksum),
                    )
                )
                for value in commitments
            )
            or manifest.manifest_checksum != expected.manifest_checksum
        ):
            _fail("DECISION_COMMITMENT_INVALID", "Trusted decision commitment is invalid.")
        return manifest

    def _validate(
        self,
        decisions: tuple[Cut1ListeningDecision, ...],
        audio: CurrentCut1AudioAuthoritySet,
        authors: Mapping[str, str],
        manifest: Cut1ListeningDecisionManifest,
    ) -> Cut1ListeningAuthority:
        if not isinstance(decisions, tuple) or not all(
            isinstance(value, Cut1ListeningDecision) for value in decisions
        ):
            _fail("DECISION_SET_INVALID", "Listening decisions are invalid.")
        if not all(isinstance(value.binding, Cut1ListeningArtifactBinding) for value in decisions):
            _fail("DECISION_SET_INVALID", "Listening decision bindings are invalid.")
        if len(decisions) != 3:
            _fail("DECISION_SET_INCOMPLETE", "Exactly three decisions are required.")
        presenters = tuple(value.binding.presenter_id for value in decisions)
        if presenters != PRESENTERS:
            _fail("DECISION_ORDER_INVALID", "Decisions must use canonical presenter order.")
        ids = tuple(value.decision_id for value in decisions)
        if len(set(ids)) != 3:
            _fail("DECISION_ID_DUPLICATE", "Decision identifiers must be unique.")
        commitments: list[Cut1ListeningDecisionCommitment] = []
        for decision, audio_authority in zip(decisions, audio.authorities, strict=True):
            self._validate_decision(decision, audio_authority, audio, authors)
            commitments.append(
                Cut1ListeningDecisionCommitment(
                    presenter_id=decision.binding.presenter_id,
                    decision_id=decision.decision_id,
                    reviewer_id=decision.reviewer_id,
                    artifact_author_id=decision.artifact_author_id,
                    decision_checksum=decision.decision_checksum,
                )
            )
        if any(value in manifest.revoked_decision_ids for value in ids):
            _fail("DECISION_REVOKED", "A listening decision is revoked.")
        if tuple(commitments) != manifest.commitments:
            _fail("DECISION_COMMITMENT_MISMATCH", "Decisions are not externally trusted.")
        value = Cut1ListeningAuthority(
            schema_version=SCHEMA,
            audio_manifest_sequence=audio.manifest_sequence,
            audio_manifest_checksum=audio.manifest_checksum,
            decision_manifest_sequence=manifest.sequence,
            decision_manifest_checksum=manifest.manifest_checksum,
            decisions=decisions,
            authority_checksum="",
        )
        return replace(value, authority_checksum=_authority_checksum(value))

    @staticmethod
    def _validate_decision(
        decision: Cut1ListeningDecision,
        audio_authority: Cut1AudioCaptionAuthority,
        audio: CurrentCut1AudioAuthoritySet,
        authors: Mapping[str, str],
    ) -> None:
        if not all(
            _valid_id(value)
            for value in (decision.decision_id, decision.reviewer_id, decision.artifact_author_id)
        ):
            _fail("DECISION_ID_INVALID", "Decision identities are invalid.")
        if not UTC_TIMESTAMP.fullmatch(decision.reviewed_at):
            _fail("DECISION_TIMESTAMP_INVALID", "Decision timestamp is not canonical UTC.")
        try:
            datetime.strptime(decision.reviewed_at, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            _fail("DECISION_TIMESTAMP_INVALID", "Decision timestamp is invalid.")
        criteria = dict(decision.criteria)
        if set(criteria) != set(LISTENING_CRITERIA):
            _fail("LISTENING_CRITERIA_INVALID", "Listening criteria are incomplete or unknown.")
        if any(type(value) is not bool for value in criteria.values()):
            _fail("LISTENING_CRITERIA_INVALID", "Listening criteria must be literal booleans.")
        if any(value is not True for value in criteria.values()):
            _fail("LISTENING_CRITERIA_REJECTED", "Every listening criterion must pass.")
        presenter = audio_authority.presenter_id
        if decision.artifact_author_id != authors[presenter]:
            _fail("ARTIFACT_AUTHOR_MISMATCH", "Claimed artifact author is not trusted.")
        if decision.reviewer_id == authors[presenter]:
            _fail("REVIEWER_NOT_INDEPENDENT", "Reviewer must differ from artifact author.")
        if decision.binding != _binding(audio_authority, audio):
            _fail("AUDIO_AUTHORITY_MISMATCH", "Decision does not bind current T05B authority.")
        if CHECKSUM.fullmatch(
            decision.decision_checksum
        ) is None or decision.decision_checksum != decision_checksum(decision):
            _fail("DECISION_CHECKSUM_INVALID", "Decision checksum is invalid.")

    def _persist(self, authority: Cut1ListeningAuthority, status: str) -> None:
        if self.state_path is None:
            return
        core = {
            "schema": SCHEMA,
            "status": status,
            "decisions": [
                _decision_payload(value) | {"decisionChecksum": value.decision_checksum}
                for value in authority.decisions
            ],
            "authorityChecksum": authority.authority_checksum,
        }
        write_state(self.state_path, core | {"stateChecksum": _json_sha(core)})

    def _restore(self) -> None:
        if self.state_path is None:
            return
        try:
            try:
                metadata = self.state_path.lstat()
            except FileNotFoundError:
                return
            if (
                self.state_path.is_symlink()
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size > MAX_STATE_BYTES
            ):
                raise ValueError("Unsafe state path.")
            payload = json.loads(
                self.state_path.read_text(encoding="utf-8"), object_pairs_hook=_pairs
            )
            expected_keys = {
                "schema", "status", "decisions", "authorityChecksum", "stateChecksum"
            }
            if not isinstance(payload, dict) or set(payload) != expected_keys:
                raise ValueError("State schema.")
            core = {key: payload[key] for key in expected_keys - {"stateChecksum"}}
            if (
                payload["schema"] != SCHEMA
                or payload["status"] != "COMMITTED"
                or payload["stateChecksum"] != _json_sha(core)
            ):
                raise ValueError("State checksum.")
            rows = payload["decisions"]
            if not isinstance(rows, list) or len(rows) != 3:
                raise ValueError("State count.")
            decisions = tuple(self._decode_decision(value) for value in rows)
            audio = self._trusted_audio()
            authors = self._trusted_authors()
            manifest = self._trusted_manifest(audio)
            authority = self._validate(decisions, audio, authors, manifest)
            if payload["authorityChecksum"] != authority.authority_checksum:
                raise ValueError("State authority.")
            self._authority, self._audio, self._manifest = authority, audio, manifest
        except (
            OSError,
            UnicodeError,
            ValueError,
            TypeError,
            KeyError,
            json.JSONDecodeError,
            ListeningAuthorityError,
        ):
            self._authority, self._audio, self._manifest = None, None, None
            self.quarantine_reason = "STATE_INVALID"

    @staticmethod
    def _decode_decision(value: Any) -> Cut1ListeningDecision:
        if (
            not isinstance(value, dict)
            or set(value)
            != {
                "schema",
                "decisionId",
                "reviewerId",
                "artifactAuthorId",
                "reviewedAt",
                "binding",
                "criteria",
                "decisionChecksum",
            }
            or value["schema"] != DECISION_SCHEMA
        ):
            raise ValueError("Decision state schema.")
        binding_value = value["binding"]
        if (
            not isinstance(binding_value, dict)
            or set(binding_value) != {field.name for field in fields(Cut1ListeningArtifactBinding)}
            or not isinstance(value["criteria"], dict)
        ):
            raise ValueError("Decision state binding.")
        return Cut1ListeningDecision(
            decision_id=value["decisionId"],
            reviewer_id=value["reviewerId"],
            artifact_author_id=value["artifactAuthorId"],
            reviewed_at=value["reviewedAt"],
            binding=Cut1ListeningArtifactBinding(**binding_value),
            criteria=value["criteria"],
            decision_checksum=value["decisionChecksum"],
        )
