"""Stage 7 mock/local avatar rendering and demo export."""

from __future__ import annotations

import base64
import binascii
import html
import json
import logging
import re
import threading
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from backend.app.rag.chunking import checksum_text
from backend.app.storage import load_state, resolve_state_file, write_state

MAX_SOURCE_SCRIPT_CHARS = 20_000
MAX_EXPORT_ARTIFACT_BYTES = 512 * 1024
MAX_PROVIDER_ID_CHARS = 64
MAX_IDEMPOTENCY_RECORDS_PER_SCOPE = 100
MAX_CONSENT_STATEMENT_CHARS = 256
PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
LOGGER = logging.getLogger(__name__)
ACTIVE_HTML_PATTERN = re.compile(
    r"(<script\b|<iframe\b|<form\b|<object\b|<embed\b|<link\b|<base\b|<style\b|"
    r"<meta\s+http-equiv\b|<[^>]+\s(?:on[a-z]+|src|href|srcset|style)\s*=|"
    r"<[^>]+javascript:)",
    re.IGNORECASE,
)
CHECKSUM_COMPONENT_DELIMITER_PATTERN = re.compile(r"[\x00-\x1f\x7f,]")
PUBLIC_USE_LICENSE_CHECK = "mock-local-provider-only-no-third-party-media"
AVATAR_RENDER_ENDPOINT = "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders"
AVATAR_CONSENT_ENDPOINT = "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents"
SYNTHETIC_AVATAR_CONSENT_VERSION = "stage7-synthetic-avatar-consent-v1"
SYNTHETIC_AVATAR_CONSENT_TEXT = (
    "I affirm that I am authorized to approve this Stage 7 synthetic local avatar "
    "demo for the selected walkthrough run."
)
ALLOWED_FALLBACK_REASONS = {"REQUESTED_PROVIDER_UNAVAILABLE", "PROVIDER_RENDER_FAILED"}
ProviderMode = Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"]
EvaluationStatus = Literal["PASSED", "FAILED", "UNKNOWN"]
ProviderAdapterKind = Literal["MOCK_LOCAL", "EXTERNAL_STUB"]
RenderJobStatus = Literal["QUEUED", "RUNNING", "FAILED", "FALLBACK", "COMPLETED"]
FallbackReason = Literal["REQUESTED_PROVIDER_UNAVAILABLE", "PROVIDER_RENDER_FAILED"]


class Stage7Error(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ExportArtifact:
    file_name: str
    mime_type: str
    content_base64: str
    checksum: str


@dataclass(frozen=True)
class ExportArtifactMetadata:
    file_name: str
    mime_type: str
    checksum: str


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    provider_mode: ProviderMode
    adapter_kind: ProviderAdapterKind
    allow_network_egress: bool
    requires_api_key: bool
    supports_real_video: bool
    supports_cloned_identity: bool


@dataclass(frozen=True)
class RenderJobStatusEvent:
    status: RenderJobStatus
    message: str


@dataclass(frozen=True)
class AvatarProviderResult:
    provider: str
    provider_mode: str
    requested_provider: str
    fallback_reason: str | None
    provider_config: ProviderConfig
    demo_export: ExportArtifact
    render_manifest: ExportArtifact
    video_export_placeholder: ExportArtifact


@dataclass(frozen=True)
class AvatarProviderMetadata:
    provider: str
    provider_mode: ProviderMode
    requested_provider: str
    fallback_reason: str | None


@dataclass(frozen=True)
class VideoRendererMetadata:
    renderer: str
    renderer_mode: Literal["LOCAL"]
    export_format: Literal["html"]


@dataclass(frozen=True)
class DisclosureMetadata:
    ai_generated: bool
    cloned_identity: bool
    consent_required: bool
    consent_status: Literal["CONFIRMED", "NOT_REQUIRED"]
    message: str


@dataclass(frozen=True)
class AvatarArtifacts:
    demo_export: ExportArtifact
    render_manifest: ExportArtifact
    video_export_placeholder: ExportArtifact


@dataclass(frozen=True)
class AvatarRenderResult:
    avatar_render_id: str
    tenant_id: str | None
    project_id: str | None
    actor_id: str | None
    consent_record_id: str | None
    source_run_id: str
    status: Literal["COMPLETED"]
    render_job_status: Literal["COMPLETED"]
    render_job_status_history: tuple[RenderJobStatusEvent, ...]
    source_script_text: str
    avatar_provider: AvatarProviderMetadata
    provider_config: ProviderConfig
    video_renderer: VideoRendererMetadata
    disclosure: DisclosureMetadata
    artifacts: AvatarArtifacts
    trace_id: str
    source_context_ref_count: int
    source_citation_count: int
    source_context_ref_ids: tuple[str, ...]
    source_citation_indexes: tuple[int, ...]
    source_evaluation_id: str
    source_evaluation_checksum: str
    evaluation_status: EvaluationStatus
    request_checksum: str
    idempotency_scope: str | None
    idempotency_key: str | None


@dataclass(frozen=True)
class SyntheticAvatarConsentRecord:
    consent_record_id: str
    tenant_id: str
    project_id: str
    actor_id: str
    source_run_id: str
    trace_id: str
    source_context_ref_ids: tuple[str, ...]
    source_citation_indexes: tuple[int, ...]
    source_evaluation_id: str
    source_evaluation_checksum: str
    evaluation_status: EvaluationStatus
    consent_statement_version: str
    consent_statement_text: str
    granted_at: str
    request_checksum: str
    idempotency_scope: str | None
    idempotency_key: str | None
    avatar_render_id: str | None = None
    artifact_checksums: tuple[str, ...] = ()


@dataclass(frozen=True)
class DurableAvatarRenderScope:
    tenant_id: str
    project_id: str
    actor_id: str
    consent_record_id: str


@dataclass
class Stage7IdempotencyRecord:
    idempotency_scope: str
    endpoint: str
    idempotency_key: str
    request_checksum: str
    status: Literal["RUNNING", "SUCCEEDED", "FAILED"]
    value: AvatarRenderResult | None
    error_status_code: int | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass
class Stage7ConsentIdempotencyRecord:
    idempotency_scope: str
    endpoint: str
    idempotency_key: str
    request_checksum: str
    status: Literal["RUNNING", "SUCCEEDED", "FAILED"]
    value: SyntheticAvatarConsentRecord | None
    error_status_code: int | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class ConsentOperationSnapshot:
    prior_consent_idempotency_record: Stage7ConsentIdempotencyRecord | None
    consent_counter: int


@dataclass(frozen=True)
class RenderOperationSnapshot:
    prior_render_idempotency_record: Stage7IdempotencyRecord | None
    prior_consent_record: SyntheticAvatarConsentRecord | None
    run_counter: int


class AvatarProvider(Protocol):
    provider: str
    provider_mode: str

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
    ) -> AvatarProviderResult:
        ...


class MockAvatarProvider:
    provider = "mock"
    provider_mode = "LOCAL"

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
    ) -> AvatarProviderResult:
        disclosure = disclosure_metadata()
        scene_count = estimate_scene_count(source_script)
        source_context_ref_ids = normalize_evidence_ids(
            source_context_ref_ids or None,
            count=source_context_ref_count,
            prefix="context_ref",
        )
        source_citation_indexes = normalize_citation_indexes(
            source_citation_indexes or None,
            count=source_citation_count,
        )
        source_evaluation_id = normalize_evaluation_id(source_evaluation_id)
        evaluation_status = validate_evaluation_status(evaluation_status)
        canonical_evaluation_checksum = build_source_evaluation_checksum(
            source_evaluation_id=source_evaluation_id,
            source_run_id=source_run_id,
            trace_id=trace_id,
            evaluation_status=evaluation_status,
            source_context_ref_ids=source_context_ref_ids,
            source_context_ref_count=source_context_ref_count,
            source_citation_indexes=source_citation_indexes,
            source_citation_count=source_citation_count,
        )
        if source_evaluation_checksum and source_evaluation_checksum != canonical_evaluation_checksum:
            raise Stage7Error(
                422,
                "VALIDATION_ERROR",
                "Source evaluation checksum does not match canonical source evidence.",
            )
        source_evaluation_checksum = canonical_evaluation_checksum
        provider_config = ProviderConfig(
            provider=self.provider,
            provider_mode="LOCAL",
            adapter_kind="MOCK_LOCAL",
            allow_network_egress=False,
            requires_api_key=False,
            supports_real_video=False,
            supports_cloned_identity=False,
        )
        manifest = {
            "schema": "Stage7AvatarRenderManifest",
            "version": "stage7-mock-avatar-render-v1",
            "provider": {
                "provider": self.provider,
                "providerMode": self.provider_mode,
                "requestedProvider": requested_provider,
                "fallbackReason": fallback_reason,
            },
            "providerConfig": provider_config_to_manifest(provider_config),
            "renderer": {
                "renderer": "local-html",
                "rendererMode": "LOCAL",
                "exportFormat": "html",
            },
            "source": {
                "runId": source_run_id,
                "traceId": trace_id,
                "contextRefCount": source_context_ref_count,
                "contextRefIds": list(source_context_ref_ids),
                "citationCount": source_citation_count,
                "citationIndexes": list(source_citation_indexes),
                "evaluationId": source_evaluation_id,
                "evaluationChecksum": source_evaluation_checksum,
                "evaluationStatus": evaluation_status,
                "scriptChecksum": checksum_text(source_script),
            },
            "disclosure": {
                "aiGenerated": disclosure.ai_generated,
                "clonedIdentity": disclosure.cloned_identity,
                "consentRequired": disclosure.consent_required,
                "consentStatus": disclosure.consent_status,
                "message": disclosure.message,
            },
            "sceneCountEstimate": scene_count,
            "videoExportPlaceholder": {
                "status": "PLACEHOLDER_ONLY",
                "mimeType": "application/json",
                "realVideoProduced": False,
            },
            "publicUseLicenseCheck": PUBLIC_USE_LICENSE_CHECK,
        }
        video_placeholder = {
            "schema": "Stage7VideoExportPlaceholder",
            "version": "stage7-video-export-placeholder-v1",
            "status": "PLACEHOLDER_ONLY",
            "realVideoProduced": False,
            "renderer": "local-html",
            "providerConfig": provider_config_to_manifest(provider_config),
            "disclosure": {
                "aiGenerated": disclosure.ai_generated,
                "clonedIdentity": disclosure.cloned_identity,
                "consentRequired": disclosure.consent_required,
                "consentStatus": disclosure.consent_status,
                "message": disclosure.message,
            },
            "source": {
                "runId": source_run_id,
                "traceId": trace_id,
                "contextRefCount": source_context_ref_count,
                "contextRefIds": list(source_context_ref_ids),
                "citationCount": source_citation_count,
                "citationIndexes": list(source_citation_indexes),
                "evaluationId": source_evaluation_id,
                "evaluationChecksum": source_evaluation_checksum,
                "evaluationStatus": evaluation_status,
                "scriptChecksum": checksum_text(source_script),
            },
            "publicUseLicenseCheck": PUBLIC_USE_LICENSE_CHECK,
            "sourceRunId": source_run_id,
            "traceId": trace_id,
            "reason": "Stage 7 exports a validated HTML demo and metadata, not a real video binary.",
        }
        demo_html = render_demo_html(
            source_script=source_script,
            source_run_id=source_run_id,
            trace_id=trace_id,
            scene_count=scene_count,
            disclosure=disclosure,
        )
        return AvatarProviderResult(
            provider=self.provider,
            provider_mode=self.provider_mode,
            requested_provider=requested_provider,
            fallback_reason=fallback_reason,
            provider_config=provider_config,
            demo_export=artifact_from_text(
                file_name=f"{source_run_id}-avatar-demo.html",
                mime_type="text/html",
                text=demo_html,
            ),
            render_manifest=artifact_from_text(
                file_name=f"{source_run_id}-avatar-render-manifest.json",
                mime_type="application/json",
                text=json.dumps(manifest, sort_keys=True),
            ),
            video_export_placeholder=artifact_from_text(
                file_name=f"{source_run_id}-video-export-placeholder.json",
                mime_type="application/json",
                text=json.dumps(video_placeholder, sort_keys=True),
            ),
        )


class ExternalAvatarProviderStub:
    provider = "external-avatar-stub"
    provider_mode = "DISABLED"

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
    ) -> AvatarProviderResult:
        del (
            source_script,
            requested_provider,
            fallback_reason,
            source_run_id,
            trace_id,
            source_context_ref_count,
            source_citation_count,
            source_context_ref_ids,
            source_citation_indexes,
            source_evaluation_id,
            source_evaluation_checksum,
            evaluation_status,
        )
        raise Stage7Error(
            502,
            "PROVIDER_RENDER_FAILED",
            "External avatar adapter stubs are disabled in Stage 7.",
        )


class Stage7Service:
    def __init__(
        self,
        *,
        avatar_provider: AvatarProvider | None = None,
        fallback_avatar_provider: AvatarProvider | None = None,
        state_path: Path | None = None,
    ) -> None:
        self.avatar_provider = avatar_provider or MockAvatarProvider()
        self.fallback_avatar_provider = fallback_avatar_provider or MockAvatarProvider()
        self.state_path = state_path
        self.idempotency_records: dict[tuple[str, str, str], Stage7IdempotencyRecord] = {}
        self.consent_idempotency_records: dict[tuple[str, str, str], Stage7ConsentIdempotencyRecord] = {}
        self._idempotency_scope_counts: dict[str, int] = {}
        self.synthetic_media_consents: dict[str, SyntheticAvatarConsentRecord] = {}
        self.avatar_renders: dict[str, AvatarRenderResult] = {}
        self.artifact_metadata: dict[str, tuple[ExportArtifactMetadata, ...]] = {}
        self._operation_lock = threading.Lock()
        self._run_counter = 0
        self._consent_counter = 0
        self._restore()

    def reset(self) -> None:
        with self._operation_lock:
            self.avatar_provider = MockAvatarProvider()
            self.fallback_avatar_provider = MockAvatarProvider()
            self._clear_runtime_state()
            self._persist_locked()

    def _clear_runtime_state(self) -> None:
        self.idempotency_records.clear()
        self.consent_idempotency_records.clear()
        self._idempotency_scope_counts.clear()
        self.synthetic_media_consents.clear()
        self.avatar_renders.clear()
        self.artifact_metadata.clear()
        self._run_counter = 0
        self._consent_counter = 0

    def _restore(self) -> None:
        payload = load_state(self.state_path)
        if payload is None:
            return
        try:
            if payload.get("schema") != "stage7-local-state-v1":
                raise ValueError("Stage 7 state schema mismatch.")
            counters = payload.get("counters", {})
            run_counter = 0
            consent_counter = 0
            if isinstance(counters, dict):
                run_counter = int(counters.get("run", 0))
                consent_counter = int(counters.get("consent", 0))
            for row in payload.get("avatarRenders", []):
                if not isinstance(row, dict):
                    continue
                try:
                    result = avatar_render_result_from_dict(row)
                except (KeyError, TypeError, ValueError, Stage7Error) as exc:
                    LOGGER.warning("Skipping incompatible Stage 7 avatar render at %s: %s", self.state_path, exc)
                    continue
                self.avatar_renders[result.avatar_render_id] = result
            run_counter = max(run_counter, max_numeric_suffix(self.avatar_renders, "avrun_"))
            self._run_counter = run_counter
            for row in payload.get("syntheticMediaConsents", []):
                if not isinstance(row, dict):
                    continue
                try:
                    record = synthetic_avatar_consent_record_from_dict(row)
                except (KeyError, TypeError, ValueError, Stage7Error) as exc:
                    LOGGER.warning("Skipping incompatible Stage 7 consent record at %s: %s", self.state_path, exc)
                    continue
                self.synthetic_media_consents[record.consent_record_id] = record
            consent_counter = max(consent_counter, max_numeric_suffix(self.synthetic_media_consents, "consent_"))
            self._consent_counter = consent_counter
            for row in payload.get("artifactMetadata", []):
                if not isinstance(row, dict):
                    continue
                try:
                    render_id, metadata = artifact_metadata_from_dict(row)
                except (KeyError, TypeError, ValueError) as exc:
                    LOGGER.warning("Skipping incompatible Stage 7 artifact metadata at %s: %s", self.state_path, exc)
                    continue
                self.artifact_metadata[render_id] = metadata
            self.artifact_metadata = {
                render_id: metadata
                for render_id, metadata in self.artifact_metadata.items()
                if render_id in self.avatar_renders and self._artifact_metadata_matches_render(render_id, metadata)
            }
            self.synthetic_media_consents = {
                consent_id: record
                for consent_id, record in self.synthetic_media_consents.items()
                if self._consent_record_is_valid(record)
            }
            self.avatar_renders = {
                render_id: result
                for render_id, result in self.avatar_renders.items()
                if self._render_matches_consent(result)
            }
            self.artifact_metadata = {
                render_id: metadata
                for render_id, metadata in self.artifact_metadata.items()
                if render_id in self.avatar_renders
            }
            self.synthetic_media_consents = {
                consent_id: record
                for consent_id, record in self.synthetic_media_consents.items()
                if self._consent_record_is_valid(record)
            }
            invalid_render_ids: set[str] = set()
            for row in payload.get("idempotencyRecords", []):
                if not isinstance(row, dict):
                    continue
                if row.get("status") == "RUNNING":
                    continue
                try:
                    idempotency_record = stage7_idempotency_record_from_dict(row, self)
                except (KeyError, TypeError, ValueError) as exc:
                    LOGGER.warning("Skipping incompatible Stage 7 idempotency record at %s: %s", self.state_path, exc)
                    value_ref = row.get("value", {})
                    if (
                        isinstance(value_ref, dict)
                        and value_ref.get("kind") == "render"
                        and "request checksum" in str(exc)
                    ):
                        invalid_render_ids.add(str(value_ref.get("id", "")))
                    continue
                key = (
                    idempotency_record.idempotency_scope,
                    idempotency_record.endpoint,
                    idempotency_record.idempotency_key,
                )
                self.idempotency_records[key] = idempotency_record
            self._drop_invalid_restored_renders_locked(invalid_render_ids)
            for row in payload.get("consentIdempotencyRecords", []):
                if not isinstance(row, dict):
                    continue
                if row.get("status") == "RUNNING":
                    continue
                try:
                    consent_idempotency_record = stage7_consent_idempotency_record_from_dict(row, self)
                except (KeyError, TypeError, ValueError) as exc:
                    LOGGER.warning(
                        "Skipping incompatible Stage 7 consent idempotency record at %s: %s",
                        self.state_path,
                        exc,
                    )
                    continue
                key = (
                    consent_idempotency_record.idempotency_scope,
                    consent_idempotency_record.endpoint,
                    consent_idempotency_record.idempotency_key,
                )
                self.consent_idempotency_records[key] = consent_idempotency_record
            self._rebuild_idempotency_scope_counts_locked()
        except (KeyError, TypeError, ValueError, Stage7Error) as exc:
            LOGGER.warning("Ignoring incompatible Stage 7 local state snapshot at %s: %s", self.state_path, exc)
            self._clear_runtime_state()

    def _artifact_metadata_matches_render(self, render_id: str, metadata: tuple[ExportArtifactMetadata, ...]) -> bool:
        result = self.avatar_renders.get(render_id)
        if result is None:
            return False
        expected = tuple(
            ExportArtifactMetadata(
                file_name=artifact.file_name,
                mime_type=artifact.mime_type,
                checksum=artifact.checksum,
            )
            for artifact in (
                result.artifacts.demo_export,
                result.artifacts.render_manifest,
                result.artifacts.video_export_placeholder,
            )
        )
        return metadata == expected

    def _consent_record_is_valid(self, record: SyntheticAvatarConsentRecord) -> bool:
        if record.consent_statement_version != SYNTHETIC_AVATAR_CONSENT_VERSION:
            return False
        if record.consent_statement_text != SYNTHETIC_AVATAR_CONSENT_TEXT:
            return False
        if record.avatar_render_id is None:
            return True
        render = self.avatar_renders.get(record.avatar_render_id)
        if render is None:
            return False
        if render.consent_record_id != record.consent_record_id:
            return False
        if (
            render.tenant_id != record.tenant_id
            or render.project_id != record.project_id
            or render.actor_id != record.actor_id
            or render.source_run_id != record.source_run_id
            or render.trace_id != record.trace_id
            or render.source_evaluation_id != record.source_evaluation_id
            or render.source_evaluation_checksum != record.source_evaluation_checksum
        ):
            return False
        expected_checksums = (
            render.artifacts.demo_export.checksum,
            render.artifacts.render_manifest.checksum,
            render.artifacts.video_export_placeholder.checksum,
        )
        return record.artifact_checksums == expected_checksums

    def _render_matches_consent(self, result: AvatarRenderResult) -> bool:
        if result.consent_record_id is None:
            return True
        record = self.synthetic_media_consents.get(result.consent_record_id)
        if record is None:
            return False
        return (
            record.avatar_render_id == result.avatar_render_id
            and record.artifact_checksums
            == (
                result.artifacts.demo_export.checksum,
                result.artifacts.render_manifest.checksum,
                result.artifacts.video_export_placeholder.checksum,
            )
            and result.consent_record_id == record.consent_record_id
            and result.tenant_id == record.tenant_id
            and result.project_id == record.project_id
            and result.actor_id == record.actor_id
            and result.source_run_id == record.source_run_id
            and result.trace_id == record.trace_id
            and result.source_evaluation_id == record.source_evaluation_id
            and result.source_evaluation_checksum == record.source_evaluation_checksum
        )

    def _drop_invalid_restored_renders_locked(self, render_ids: set[str]) -> None:
        if not render_ids:
            return
        self.avatar_renders = {
            render_id: result
            for render_id, result in self.avatar_renders.items()
            if render_id not in render_ids
        }
        self.artifact_metadata = {
            render_id: metadata
            for render_id, metadata in self.artifact_metadata.items()
            if render_id in self.avatar_renders and self._artifact_metadata_matches_render(render_id, metadata)
        }
        self.idempotency_records = {
            key: record
            for key, record in self.idempotency_records.items()
            if record.value is None or record.value.avatar_render_id in self.avatar_renders
        }
        self.synthetic_media_consents = {
            consent_id: record
            for consent_id, record in self.synthetic_media_consents.items()
            if self._consent_record_is_valid(record)
        }

    def _rebuild_idempotency_scope_counts_locked(self) -> None:
        counts: dict[str, int] = {}
        for record in self.idempotency_records.values():
            counts[record.idempotency_scope] = counts.get(record.idempotency_scope, 0) + 1
        for consent_record in self.consent_idempotency_records.values():
            counts[consent_record.idempotency_scope] = counts.get(consent_record.idempotency_scope, 0) + 1
        self._idempotency_scope_counts = counts

    def _increment_idempotency_scope_count_locked(self, idempotency_scope: str) -> None:
        self._idempotency_scope_counts[idempotency_scope] = self._idempotency_scope_counts.get(idempotency_scope, 0) + 1

    def _snapshot_consent_operation_locked(
        self,
        consent_record_key: tuple[str, str, str] | None = None,
    ) -> ConsentOperationSnapshot:
        prior_record = None
        if consent_record_key is not None:
            existing = self.consent_idempotency_records.get(consent_record_key)
            prior_record = deepcopy(existing) if existing is not None else None
        return ConsentOperationSnapshot(
            prior_consent_idempotency_record=prior_record,
            consent_counter=self._consent_counter,
        )

    def _snapshot_render_operation_locked(
        self,
        *,
        render_record_key: tuple[str, str, str] | None = None,
        consent_record_id: str | None = None,
    ) -> RenderOperationSnapshot:
        prior_record = None
        if render_record_key is not None:
            existing = self.idempotency_records.get(render_record_key)
            prior_record = deepcopy(existing) if existing is not None else None
        prior_consent = None
        if consent_record_id is not None:
            existing_consent = self.synthetic_media_consents.get(consent_record_id)
            prior_consent = deepcopy(existing_consent) if existing_consent is not None else None
        return RenderOperationSnapshot(
            prior_render_idempotency_record=prior_record,
            prior_consent_record=prior_consent,
            run_counter=self._run_counter,
        )

    def _restore_failed_consent_operation_locked(
        self,
        snapshot: ConsentOperationSnapshot,
        *,
        consent_record_key: tuple[str, str, str] | None,
        consent_record_id: str | None,
    ) -> None:
        if consent_record_key is not None:
            if snapshot.prior_consent_idempotency_record is None:
                self.consent_idempotency_records.pop(consent_record_key, None)
            else:
                self.consent_idempotency_records[consent_record_key] = deepcopy(
                    snapshot.prior_consent_idempotency_record
                )
        if consent_record_id is not None:
            self.synthetic_media_consents.pop(consent_record_id, None)
        self._consent_counter = max(
            snapshot.consent_counter,
            max_numeric_suffix(self.synthetic_media_consents, "consent_"),
        )
        self._rebuild_idempotency_scope_counts_locked()

    def _restore_failed_render_operation_locked(
        self,
        snapshot: RenderOperationSnapshot,
        *,
        render_record_key: tuple[str, str, str] | None,
        avatar_render_id: str | None,
        consent_record_id: str | None,
    ) -> None:
        if render_record_key is not None:
            if snapshot.prior_render_idempotency_record is None:
                self.idempotency_records.pop(render_record_key, None)
            else:
                self.idempotency_records[render_record_key] = deepcopy(snapshot.prior_render_idempotency_record)
        if avatar_render_id is not None:
            self.avatar_renders.pop(avatar_render_id, None)
            self.artifact_metadata.pop(avatar_render_id, None)
        if consent_record_id is not None:
            prior_consent = snapshot.prior_consent_record
            if prior_consent is None:
                self.synthetic_media_consents.pop(consent_record_id, None)
            else:
                self.synthetic_media_consents[consent_record_id] = deepcopy(prior_consent)
        self._run_counter = max(snapshot.run_counter, max_numeric_suffix(self.avatar_renders, "avrun_"))
        self._rebuild_idempotency_scope_counts_locked()

    def _persist_locked(self) -> None:
        write_state(
            self.state_path,
            {
                "schema": "stage7-local-state-v1",
                "syntheticMediaConsents": [
                    synthetic_avatar_consent_record_to_dict(record) for record in self.synthetic_media_consents.values()
                ],
                "avatarRenders": [
                    avatar_render_result_to_dict(result) for result in self.avatar_renders.values()
                ],
                "artifactMetadata": [
                    {"avatar_render_id": render_id, "metadata": [asdict(item) for item in metadata]}
                    for render_id, metadata in self.artifact_metadata.items()
                ],
                "idempotencyRecords": [
                    stage7_idempotency_record_to_dict(record)
                    for record in self.idempotency_records.values()
                    if record.status != "RUNNING"
                ],
                "consentIdempotencyRecords": [
                    stage7_consent_idempotency_record_to_dict(record)
                    for record in self.consent_idempotency_records.values()
                    if record.status != "RUNNING"
                ],
                "counters": {"run": self._run_counter, "consent": self._consent_counter},
            },
        )

    def capture_synthetic_avatar_consent(
        self,
        *,
        tenant_id: str,
        project_id: str,
        actor_id: str,
        source_run_id: str,
        trace_id: str,
        source_context_ref_ids: tuple[str, ...],
        source_citation_indexes: tuple[int, ...],
        source_evaluation_id: str,
        source_evaluation_checksum: str,
        evaluation_status: str,
        consent_to_use_synthetic_avatar: bool,
        idempotency_scope: str | None = None,
        idempotency_key: str | None = None,
    ) -> SyntheticAvatarConsentRecord:
        if not consent_to_use_synthetic_avatar:
            raise Stage7Error(
                422,
                "AVATAR_CONSENT_REQUIRED",
                "Synthetic avatar demo export requires explicit consent.",
            )
        normalized_tenant_id = validate_checksum_component(tenant_id, field_name="Tenant identifier")
        normalized_project_id = validate_checksum_component(project_id, field_name="Project identifier")
        normalized_actor_id = validate_checksum_component(actor_id, field_name="Actor identifier")
        normalized_source_run_id = validate_checksum_component(source_run_id, field_name="Source run identifier")
        normalized_trace_id = validate_checksum_component(trace_id, field_name="Source trace identifier")
        normalized_context_ref_ids = normalize_evidence_ids(
            source_context_ref_ids,
            count=len(source_context_ref_ids),
            prefix="context_ref",
        )
        normalized_citation_indexes = normalize_citation_indexes(
            source_citation_indexes,
            count=len(source_citation_indexes),
        )
        normalized_evaluation_id = normalize_evaluation_id(source_evaluation_id)
        normalized_evaluation_checksum = validate_checksum_component(
            source_evaluation_checksum,
            field_name="Source evaluation checksum",
        )
        normalized_evaluation_status = validate_evaluation_status(evaluation_status)
        request_checksum = build_avatar_consent_request_checksum(
            tenant_id=normalized_tenant_id,
            project_id=normalized_project_id,
            actor_id=normalized_actor_id,
            source_run_id=normalized_source_run_id,
            trace_id=normalized_trace_id,
            source_context_ref_ids=normalized_context_ref_ids,
            source_citation_indexes=normalized_citation_indexes,
            source_evaluation_id=normalized_evaluation_id,
            source_evaluation_checksum=normalized_evaluation_checksum,
            evaluation_status=normalized_evaluation_status,
            idempotency_scope=idempotency_scope,
            idempotency_key=idempotency_key,
        )
        record_key: tuple[str, str, str] | None = None
        consent_record_id: str | None = None
        with self._operation_lock:
            snapshot = self._snapshot_consent_operation_locked()
        if idempotency_scope and idempotency_key:
            record_key = (idempotency_scope, AVATAR_CONSENT_ENDPOINT, idempotency_key)
            with self._operation_lock:
                snapshot = self._snapshot_consent_operation_locked(consent_record_key=record_key)
                existing = self.consent_idempotency_records.get(record_key)
                if existing is not None:
                    if existing.request_checksum != request_checksum:
                        raise Stage7Error(
                            409,
                            "IDEMPOTENCY_CONFLICT",
                            "Idempotency key was reused with a different request.",
                        )
                    if existing.status == "RUNNING":
                        raise Stage7Error(
                            409,
                            "IDEMPOTENCY_IN_PROGRESS",
                            "Idempotency key is already in progress.",
                        )
                    if existing.status == "FAILED":
                        raise Stage7Error(
                            existing.error_status_code or 500,
                            existing.error_code or "INTERNAL_SERVER_ERROR",
                            existing.error_message or "Consent capture failed.",
                        )
                    return cast(SyntheticAvatarConsentRecord, existing.value)
                if self._idempotency_count_for_scope(idempotency_scope) >= MAX_IDEMPOTENCY_RECORDS_PER_SCOPE:
                    raise Stage7Error(
                        429,
                        "RESOURCE_LIMIT_EXCEEDED",
                        "Idempotency record limit exceeded for this Stage 7 scope.",
                    )
                self.consent_idempotency_records[record_key] = Stage7ConsentIdempotencyRecord(
                    idempotency_scope=idempotency_scope,
                    endpoint=AVATAR_CONSENT_ENDPOINT,
                    idempotency_key=idempotency_key,
                    request_checksum=request_checksum,
                    status="RUNNING",
                    value=None,
                )
                self._increment_idempotency_scope_count_locked(idempotency_scope)

        try:
            with self._operation_lock:
                self._consent_counter += 1
                consent_record_id = f"consent_{self._consent_counter:06d}"
                consent = SyntheticAvatarConsentRecord(
                    consent_record_id=consent_record_id,
                    tenant_id=normalized_tenant_id,
                    project_id=normalized_project_id,
                    actor_id=normalized_actor_id,
                    source_run_id=normalized_source_run_id,
                    trace_id=normalized_trace_id,
                    source_context_ref_ids=normalized_context_ref_ids,
                    source_citation_indexes=normalized_citation_indexes,
                    source_evaluation_id=normalized_evaluation_id,
                    source_evaluation_checksum=normalized_evaluation_checksum,
                    evaluation_status=normalized_evaluation_status,
                    consent_statement_version=SYNTHETIC_AVATAR_CONSENT_VERSION,
                    consent_statement_text=SYNTHETIC_AVATAR_CONSENT_TEXT,
                    granted_at=utc_now_isoformat(),
                    request_checksum=request_checksum,
                    idempotency_scope=idempotency_scope,
                    idempotency_key=idempotency_key,
                )
                self.synthetic_media_consents[consent.consent_record_id] = consent
                if record_key is not None:
                    record = self.consent_idempotency_records[record_key]
                    record.status = "SUCCEEDED"
                    record.value = consent
                self._persist_locked()
                return consent
        except Stage7Error as exc:
            if record_key is not None:
                with self._operation_lock:
                    failed_record = self.consent_idempotency_records.get(record_key)
                    if failed_record is not None:
                        failed_record.status = "FAILED"
                        failed_record.error_status_code = exc.status_code
                        failed_record.error_code = exc.code
                        failed_record.error_message = exc.message
                    try:
                        self._persist_locked()
                    except OSError:
                        self._restore_failed_consent_operation_locked(
                            snapshot,
                            consent_record_key=record_key,
                            consent_record_id=consent_record_id,
                        )
                        raise exc
            raise
        except OSError:
            with self._operation_lock:
                self._restore_failed_consent_operation_locked(
                    snapshot,
                    consent_record_key=record_key,
                    consent_record_id=consent_record_id,
                )
            raise

    def render_avatar_demo(
        self,
        *,
        source_script: str,
        requested_avatar_provider: str = "mock",
        source_run_id: str = "local_source_run",
        trace_id: str = "local_trace",
        source_context_ref_count: int = 0,
        source_citation_count: int = 0,
        source_context_ref_ids: tuple[str, ...] | None = None,
        source_citation_indexes: tuple[int, ...] | None = None,
        source_evaluation_id: str = "local_evaluation",
        source_evaluation_checksum: str | None = None,
        evaluation_status: str = "UNKNOWN",
        cloned_identity_requested: bool = False,
        consent_to_use_synthetic_avatar: bool = False,
        durable_consent: DurableAvatarRenderScope | None = None,
        idempotency_scope: str | None = None,
        idempotency_key: str | None = None,
    ) -> AvatarRenderResult:
        source_text = source_script.strip()
        canonical_evaluation_checksum = build_source_evaluation_checksum(
            source_evaluation_id=source_evaluation_id,
            source_run_id=source_run_id,
            trace_id=trace_id,
            evaluation_status=evaluation_status,
            source_context_ref_ids=source_context_ref_ids,
            source_context_ref_count=source_context_ref_count,
            source_citation_indexes=source_citation_indexes,
            source_citation_count=source_citation_count,
        )
        checksum_for_request = (
            canonical_evaluation_checksum
            if source_evaluation_checksum is None or source_evaluation_checksum == canonical_evaluation_checksum
            else source_evaluation_checksum
        )
        request_checksum = build_avatar_render_request_checksum(
            source_text=source_text,
            requested_avatar_provider=requested_avatar_provider,
            cloned_identity_requested=cloned_identity_requested,
            consent_to_use_synthetic_avatar=consent_to_use_synthetic_avatar,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=checksum_for_request,
            evaluation_status=evaluation_status,
            consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
            idempotency_scope=idempotency_scope,
            idempotency_key=idempotency_key,
        )
        normalized_tenant_id: str | None = None
        normalized_project_id: str | None = None
        normalized_actor_id: str | None = None
        required_consent: SyntheticAvatarConsentRecord | None = None
        record_key: tuple[str, str, str] | None = None
        result: AvatarRenderResult | None = None
        with self._operation_lock:
            snapshot = self._snapshot_render_operation_locked(
                consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
            )
        if idempotency_scope and idempotency_key:
            record_key = (idempotency_scope, AVATAR_RENDER_ENDPOINT, idempotency_key)
            with self._operation_lock:
                snapshot = self._snapshot_render_operation_locked(
                    render_record_key=record_key,
                    consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
                )
                existing = self.idempotency_records.get(record_key)
                if existing is not None:
                    if existing.request_checksum != request_checksum:
                        raise Stage7Error(
                            409,
                            "IDEMPOTENCY_CONFLICT",
                            "Idempotency key was reused with a different request.",
                        )
                    if existing.status == "RUNNING":
                        raise Stage7Error(
                            409,
                            "IDEMPOTENCY_IN_PROGRESS",
                            "Idempotency key is already in progress.",
                        )
                    if existing.status == "FAILED":
                        raise Stage7Error(
                            existing.error_status_code or 500,
                            existing.error_code or "INTERNAL_SERVER_ERROR",
                            existing.error_message or "Avatar render failed.",
                        )
                    return cast(AvatarRenderResult, existing.value)
                if self._idempotency_count_for_scope(idempotency_scope) >= MAX_IDEMPOTENCY_RECORDS_PER_SCOPE:
                    raise Stage7Error(
                        429,
                        "RESOURCE_LIMIT_EXCEEDED",
                        "Idempotency record limit exceeded for this Stage 7 scope.",
                    )
                self.idempotency_records[record_key] = Stage7IdempotencyRecord(
                    idempotency_scope=idempotency_scope,
                    endpoint=AVATAR_RENDER_ENDPOINT,
                    idempotency_key=idempotency_key,
                    request_checksum=request_checksum,
                    status="RUNNING",
                    value=None,
                )
                self._increment_idempotency_scope_count_locked(idempotency_scope)

        try:
            if not source_text:
                raise Stage7Error(422, "VALIDATION_ERROR", "Source walkthrough script is required.")
            if len(source_text) > MAX_SOURCE_SCRIPT_CHARS:
                raise Stage7Error(413, "SOURCE_SCRIPT_TOO_LARGE", "Source script exceeds the Stage 7 limit.")
            if cloned_identity_requested:
                raise Stage7Error(
                    422,
                    "CLONED_IDENTITY_DISABLED",
                    "Cloned identity avatar rendering is disabled for Stage 7.",
                )
            if not consent_to_use_synthetic_avatar:
                raise Stage7Error(
                    422,
                    "AVATAR_CONSENT_REQUIRED",
                    "Synthetic avatar demo export requires explicit consent.",
                )
            if durable_consent is not None:
                normalized_tenant_id = validate_checksum_component(
                    durable_consent.tenant_id,
                    field_name="Tenant identifier",
                )
                normalized_project_id = validate_checksum_component(
                    durable_consent.project_id,
                    field_name="Project identifier",
                )
                normalized_actor_id = validate_checksum_component(
                    durable_consent.actor_id,
                    field_name="Actor identifier",
                )
                if source_evaluation_checksum is None:
                    raise Stage7Error(
                        422,
                        "VALIDATION_ERROR",
                        "Source evaluation checksum is required for durable consent gating.",
                    )
                with self._operation_lock:
                    required_consent = self._require_durable_synthetic_avatar_consent_locked(
                        tenant_id=normalized_tenant_id,
                        project_id=normalized_project_id,
                        actor_id=normalized_actor_id,
                        source_run_id=source_run_id,
                        trace_id=trace_id,
                        source_evaluation_id=source_evaluation_id,
                        source_evaluation_checksum=source_evaluation_checksum,
                        consent_record_id=durable_consent.consent_record_id,
                    )
            if source_evaluation_checksum is not None and source_evaluation_checksum != canonical_evaluation_checksum:
                raise Stage7Error(
                    422,
                    "VALIDATION_ERROR",
                    "Source evaluation checksum does not match canonical source evidence.",
                )

            requested_provider, fallback_reason = resolve_avatar_provider(requested_avatar_provider)
            normalized_evaluation_status = validate_evaluation_status(evaluation_status)
            normalized_context_ref_ids = normalize_evidence_ids(
                source_context_ref_ids,
                count=source_context_ref_count,
                prefix="context_ref",
            )
            normalized_citation_indexes = normalize_citation_indexes(
                source_citation_indexes,
                count=source_citation_count,
            )
            normalized_evaluation_id = normalize_evaluation_id(source_evaluation_id)
            normalized_evaluation_checksum = canonical_evaluation_checksum
            result = self._create_avatar_render(
                source_text=source_text,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                source_context_ref_ids=normalized_context_ref_ids,
                source_citation_indexes=normalized_citation_indexes,
                source_evaluation_id=normalized_evaluation_id,
                source_evaluation_checksum=normalized_evaluation_checksum,
                evaluation_status=normalized_evaluation_status,
                tenant_id=normalized_tenant_id,
                project_id=normalized_project_id,
                actor_id=normalized_actor_id,
                consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
                request_checksum=request_checksum,
                idempotency_scope=idempotency_scope,
                idempotency_key=idempotency_key,
            )
        except Stage7Error as exc:
            if record_key is not None:
                with self._operation_lock:
                    record = self.idempotency_records.get(record_key)
                    if record is not None:
                        record.status = "FAILED"
                        record.error_status_code = exc.status_code
                        record.error_code = exc.code
                        record.error_message = exc.message
                    try:
                        self._persist_locked()
                    except OSError:
                        self._restore_failed_render_operation_locked(
                            snapshot,
                            render_record_key=record_key,
                            avatar_render_id=None,
                            consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
                        )
                        raise exc
            raise
        except OSError:
            with self._operation_lock:
                self._restore_failed_render_operation_locked(
                    snapshot,
                    render_record_key=record_key,
                    avatar_render_id=result.avatar_render_id if result is not None else None,
                    consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
                )
            raise
        except Exception:
            if record_key is not None:
                with self._operation_lock:
                    record = self.idempotency_records.get(record_key)
                    if record is not None:
                        record.status = "FAILED"
                        record.error_status_code = 500
                        record.error_code = "INTERNAL_SERVER_ERROR"
                        record.error_message = "Avatar render failed."
                    try:
                        self._persist_locked()
                    except OSError:
                        self._restore_failed_render_operation_locked(
                            snapshot,
                            render_record_key=record_key,
                            avatar_render_id=None,
                            consent_record_id=durable_consent.consent_record_id if durable_consent is not None else None,
                        )
                        raise
            raise
        assert result is not None
        with self._operation_lock:
            if record_key is not None:
                record = self.idempotency_records[record_key]
                record.status = "SUCCEEDED"
                record.value = result
            if required_consent is not None:
                self.synthetic_media_consents[required_consent.consent_record_id] = replace(
                    required_consent,
                    avatar_render_id=result.avatar_render_id,
                    artifact_checksums=(
                        result.artifacts.demo_export.checksum,
                        result.artifacts.render_manifest.checksum,
                        result.artifacts.video_export_placeholder.checksum,
                    ),
                )
            try:
                self._persist_locked()
            except OSError:
                self._restore_failed_render_operation_locked(
                    snapshot,
                    render_record_key=record_key,
                    avatar_render_id=result.avatar_render_id,
                    consent_record_id=required_consent.consent_record_id if required_consent is not None else None,
                )
                raise
        return result

    def _create_avatar_render(
        self,
        *,
        source_text: str,
        requested_provider: str,
        fallback_reason: str | None,
        source_run_id: str,
        trace_id: str,
        source_context_ref_count: int,
        source_citation_count: int,
        source_context_ref_ids: tuple[str, ...],
        source_citation_indexes: tuple[int, ...],
        source_evaluation_id: str,
        source_evaluation_checksum: str,
        evaluation_status: EvaluationStatus,
        tenant_id: str | None,
        project_id: str | None,
        actor_id: str | None,
        consent_record_id: str | None,
        request_checksum: str,
        idempotency_scope: str | None,
        idempotency_key: str | None,
    ) -> AvatarRenderResult:
        status_history = [RenderJobStatusEvent(status="QUEUED", message="Avatar render job queued.")]
        if fallback_reason is not None:
            status_history.append(
                RenderJobStatusEvent(status="FALLBACK", message="Requested avatar provider is unavailable locally.")
            )
        status_history.append(RenderJobStatusEvent(status="RUNNING", message="Avatar provider render started."))
        try:
            provider_result = self.avatar_provider.render(
                source_script=source_text,
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
        except Stage7Error as exc:
            if exc.code != "PROVIDER_RENDER_FAILED":
                raise
            provider_result = self._render_with_mock_fallback(
                status_history=status_history,
                source_text=source_text,
                requested_provider=requested_provider,
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
        except Exception:
            provider_result = self._render_with_mock_fallback(
                status_history=status_history,
                source_text=source_text,
                requested_provider=requested_provider,
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
        status_history.append(RenderJobStatusEvent(status="COMPLETED", message="Avatar render job completed."))
        provider_result = validate_provider_result(provider_result)
        fallback_reason = validate_fallback_reason(provider_result.fallback_reason)
        avatar_provider = AvatarProviderMetadata(
            provider=validate_provider_id(provider_result.provider, field_name="avatar provider"),
            provider_mode=validate_provider_mode(provider_result.provider_mode),
            requested_provider=requested_provider,
            fallback_reason=fallback_reason,
        )
        provider_config = validate_provider_config(provider_result.provider_config, provider=avatar_provider.provider)
        validate_provider_metadata_matches_config(avatar_provider, provider_config)
        demo_export = validate_export_artifact(
            provider_result.demo_export,
            expected_mime_type="text/html",
            expected_extension=".html",
        )
        validate_demo_html_export(
            demo_export,
            source_script=source_text,
            source_run_id=source_run_id,
            trace_id=trace_id,
            disclosure=disclosure_metadata(),
        )
        render_manifest = validate_export_artifact(
            provider_result.render_manifest,
            expected_mime_type="application/json",
            expected_extension=".json",
        )
        video_export_placeholder = validate_export_artifact(
            provider_result.video_export_placeholder,
            expected_mime_type="application/json",
            expected_extension=".json",
        )
        disclosure = disclosure_metadata()
        validate_render_manifest(
            render_manifest,
            avatar_provider=avatar_provider,
            provider_config=provider_config,
            source_script=source_text,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
            disclosure=disclosure,
        )
        validate_video_export_placeholder(
            video_export_placeholder,
            provider_config=provider_config,
            source_script=source_text,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
            disclosure=disclosure,
        )
        with self._operation_lock:
            self._run_counter += 1
            avatar_render_id = f"avrun_{self._run_counter:06d}"
        result = AvatarRenderResult(
            avatar_render_id=avatar_render_id,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor_id,
            consent_record_id=consent_record_id,
            source_run_id=source_run_id,
            status="COMPLETED",
            render_job_status="COMPLETED",
            render_job_status_history=tuple(status_history),
            source_script_text=source_text,
            avatar_provider=avatar_provider,
            provider_config=provider_config,
            video_renderer=VideoRendererMetadata(
                renderer="local-html",
                renderer_mode="LOCAL",
                export_format="html",
            ),
            disclosure=disclosure,
            artifacts=AvatarArtifacts(
                demo_export=demo_export,
                render_manifest=render_manifest,
                video_export_placeholder=video_export_placeholder,
            ),
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
            request_checksum=request_checksum,
            idempotency_scope=idempotency_scope,
            idempotency_key=idempotency_key,
        )
        with self._operation_lock:
            self.avatar_renders[avatar_render_id] = result
            self.artifact_metadata[avatar_render_id] = tuple(
                ExportArtifactMetadata(
                    file_name=artifact.file_name,
                    mime_type=artifact.mime_type,
                    checksum=artifact.checksum,
                )
                for artifact in (
                    result.artifacts.demo_export,
                    result.artifacts.render_manifest,
                    result.artifacts.video_export_placeholder,
                )
            )
        return result

    def _render_with_mock_fallback(
        self,
        *,
        status_history: list[RenderJobStatusEvent],
        source_text: str,
        requested_provider: str,
        source_run_id: str,
        trace_id: str,
        source_context_ref_count: int,
        source_citation_count: int,
        source_context_ref_ids: tuple[str, ...],
        source_citation_indexes: tuple[int, ...],
        source_evaluation_id: str,
        source_evaluation_checksum: str,
        evaluation_status: EvaluationStatus,
    ) -> AvatarProviderResult:
        status_history.append(RenderJobStatusEvent(status="FAILED", message="Avatar provider render failed."))
        status_history.append(RenderJobStatusEvent(status="FALLBACK", message="Mock local fallback render started."))
        try:
            return self.fallback_avatar_provider.render(
                source_script=source_text,
                requested_provider=requested_provider,
                fallback_reason="PROVIDER_RENDER_FAILED",
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
        except Stage7Error:
            raise
        except Exception as exc:
            raise Stage7Error(502, "PROVIDER_RENDER_FAILED", "Avatar provider fallback failed.") from exc

    def _idempotency_count_for_scope(self, idempotency_scope: str) -> int:
        return self._idempotency_scope_counts.get(idempotency_scope, 0)

    def _require_durable_synthetic_avatar_consent_locked(
        self,
        *,
        tenant_id: str,
        project_id: str,
        actor_id: str,
        source_run_id: str,
        trace_id: str,
        source_evaluation_id: str,
        source_evaluation_checksum: str,
        consent_record_id: str,
    ) -> SyntheticAvatarConsentRecord:
        record = self.synthetic_media_consents.get(consent_record_id)
        if record is None:
            raise Stage7Error(
                422,
                "AVATAR_CONSENT_RECORD_REQUIRED",
                "Avatar rendering requires a matching durable consent record.",
            )
        if not self._consent_record_is_valid(record):
            raise Stage7Error(
                422,
                "AVATAR_CONSENT_INVALID",
                "Avatar rendering requires a valid durable consent record.",
            )
        if record.avatar_render_id is not None:
            raise Stage7Error(
                422,
                "AVATAR_CONSENT_INVALID",
                "Avatar rendering requires an unused durable consent record.",
            )
        if (
            record.tenant_id != tenant_id
            or record.project_id != project_id
            or record.actor_id != actor_id
            or record.source_run_id != source_run_id
            or record.trace_id != trace_id
            or record.source_evaluation_id != normalize_evaluation_id(source_evaluation_id)
            or record.source_evaluation_checksum != validate_checksum_component(
                source_evaluation_checksum,
                field_name="Source evaluation checksum",
            )
        ):
            raise Stage7Error(
                422,
                "AVATAR_CONSENT_INVALID",
                "Avatar rendering consent record does not match the requested durable scope.",
            )
        return record


def stage7_idempotency_record_to_dict(record: Stage7IdempotencyRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "idempotency_scope": record.idempotency_scope,
        "endpoint": record.endpoint,
        "idempotency_key": record.idempotency_key,
        "request_checksum": record.request_checksum,
        "status": record.status,
        "error_status_code": record.error_status_code,
        "error_code": record.error_code,
        "error_message": record.error_message,
    }
    if record.value is not None:
        row["value"] = {"kind": "render", "id": record.value.avatar_render_id}
    else:
        row["value"] = {"kind": "none"}
    return row


def stage7_consent_idempotency_record_to_dict(record: Stage7ConsentIdempotencyRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "idempotency_scope": record.idempotency_scope,
        "endpoint": record.endpoint,
        "idempotency_key": record.idempotency_key,
        "request_checksum": record.request_checksum,
        "status": record.status,
        "error_status_code": record.error_status_code,
        "error_code": record.error_code,
        "error_message": record.error_message,
    }
    if record.value is not None:
        row["value"] = {"kind": "consent", "id": record.value.consent_record_id}
    else:
        row["value"] = {"kind": "none"}
    return row


def stage7_idempotency_record_from_dict(row: dict[str, Any], service: Stage7Service) -> Stage7IdempotencyRecord:
    value_ref = row.get("value", {})
    value: AvatarRenderResult | None = None
    if isinstance(value_ref, dict) and value_ref.get("kind") == "render":
        value = service.avatar_renders.get(str(value_ref.get("id", "")))
    status = str(row["status"])
    if status not in {"RUNNING", "SUCCEEDED", "FAILED"}:
        raise ValueError(f"Unsupported Stage 7 idempotency status: {status}")
    endpoint = str(row["endpoint"])
    if endpoint != AVATAR_RENDER_ENDPOINT:
        raise ValueError("Stage 7 render idempotency endpoint does not match the canonical endpoint.")
    if status == "SUCCEEDED" and value is None:
        raise ValueError("Succeeded Stage 7 idempotency record references missing value.")
    request_checksum = str(row["request_checksum"])
    idempotency_scope = str(row["idempotency_scope"])
    idempotency_key = str(row["idempotency_key"])
    if status == "SUCCEEDED" and value is not None:
        if not restored_render_request_checksum_matches(value, request_checksum):
            raise ValueError("Succeeded Stage 7 idempotency record request checksum does not match restored render.")
        if value.idempotency_scope != idempotency_scope or value.idempotency_key != idempotency_key:
            raise ValueError("Succeeded Stage 7 idempotency record does not match restored render idempotency binding.")
        if not restored_render_idempotency_scope_matches(value, idempotency_scope):
            raise ValueError("Succeeded Stage 7 idempotency record does not match restored render scope.")
    if status == "FAILED":
        raise ValueError("Failed Stage 7 idempotency records are not replayed from restored local state.")
    return Stage7IdempotencyRecord(
        idempotency_scope=idempotency_scope,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_checksum=request_checksum,
        status=cast(Literal["RUNNING", "SUCCEEDED", "FAILED"], status),
        value=value,
        error_status_code=int(row["error_status_code"]) if row.get("error_status_code") is not None else None,
        error_code=str(row["error_code"]) if row.get("error_code") is not None else None,
        error_message=str(row["error_message"]) if row.get("error_message") is not None else None,
    )


def stage7_consent_idempotency_record_from_dict(
    row: dict[str, Any],
    service: Stage7Service,
) -> Stage7ConsentIdempotencyRecord:
    value_ref = row.get("value", {})
    value: SyntheticAvatarConsentRecord | None = None
    if isinstance(value_ref, dict) and value_ref.get("kind") == "consent":
        value = service.synthetic_media_consents.get(str(value_ref.get("id", "")))
    status = str(row["status"])
    if status not in {"RUNNING", "SUCCEEDED", "FAILED"}:
        raise ValueError(f"Unsupported Stage 7 consent idempotency status: {status}")
    endpoint = str(row["endpoint"])
    if endpoint != AVATAR_CONSENT_ENDPOINT:
        raise ValueError("Stage 7 consent idempotency endpoint does not match the canonical endpoint.")
    if status == "SUCCEEDED" and value is None:
        raise ValueError("Succeeded Stage 7 consent idempotency record references missing value.")
    request_checksum = str(row["request_checksum"])
    idempotency_scope = str(row["idempotency_scope"])
    idempotency_key = str(row["idempotency_key"])
    if status == "SUCCEEDED" and value is not None:
        if value.request_checksum != request_checksum:
            raise ValueError("Succeeded Stage 7 consent idempotency request checksum does not match restored consent.")
        if value.idempotency_scope != idempotency_scope or value.idempotency_key != idempotency_key:
            raise ValueError("Succeeded Stage 7 consent idempotency binding does not match restored consent.")
    if status == "FAILED":
        raise ValueError("Failed Stage 7 consent idempotency records are not replayed from restored local state.")
    return Stage7ConsentIdempotencyRecord(
        idempotency_scope=idempotency_scope,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_checksum=request_checksum,
        status=cast(Literal["RUNNING", "SUCCEEDED", "FAILED"], status),
        value=value,
        error_status_code=int(row["error_status_code"]) if row.get("error_status_code") is not None else None,
        error_code=str(row["error_code"]) if row.get("error_code") is not None else None,
        error_message=str(row["error_message"]) if row.get("error_message") is not None else None,
    )


def max_numeric_suffix(records: Mapping[str, object], prefix: str) -> int:
    maximum = 0
    for identifier in records:
        if identifier.startswith(prefix):
            try:
                maximum = max(maximum, int(identifier.removeprefix(prefix)))
            except ValueError:
                continue
    return maximum


def avatar_render_result_to_dict(result: AvatarRenderResult) -> dict[str, Any]:
    return asdict(result)


def avatar_render_result_from_dict(row: dict[str, Any]) -> AvatarRenderResult:
    avatar_provider = cast(dict[str, Any], row["avatar_provider"])
    provider_config = cast(dict[str, Any], row["provider_config"])
    video_renderer = cast(dict[str, Any], row["video_renderer"])
    disclosure = cast(dict[str, Any], row["disclosure"])
    artifacts = cast(dict[str, Any], row["artifacts"])
    restored_provider = AvatarProviderMetadata(
        provider=validate_provider_id(str(avatar_provider["provider"]), field_name="avatar provider"),
        provider_mode=validate_provider_mode(str(avatar_provider["provider_mode"])),
        requested_provider=validate_provider_id(
            str(avatar_provider["requested_provider"]),
            field_name="requested avatar provider",
        ),
        fallback_reason=validate_fallback_reason(
            str(avatar_provider["fallback_reason"]) if avatar_provider.get("fallback_reason") is not None else None
        ),
    )
    restored_config = validate_provider_config(
        ProviderConfig(
            provider=str(provider_config["provider"]),
            provider_mode=cast(ProviderMode, provider_config["provider_mode"]),
            adapter_kind=cast(ProviderAdapterKind, provider_config["adapter_kind"]),
            allow_network_egress=provider_config["allow_network_egress"],
            requires_api_key=provider_config["requires_api_key"],
            supports_real_video=provider_config["supports_real_video"],
            supports_cloned_identity=provider_config["supports_cloned_identity"],
        ),
        provider=restored_provider.provider,
    )
    validate_provider_metadata_matches_config(restored_provider, restored_config)
    restored_disclosure = DisclosureMetadata(
        ai_generated=validate_bool(disclosure["ai_generated"], field_name="disclosure ai_generated"),
        cloned_identity=validate_bool(disclosure["cloned_identity"], field_name="disclosure cloned_identity"),
        consent_required=validate_bool(disclosure["consent_required"], field_name="disclosure consent_required"),
        consent_status=validate_consent_status(str(disclosure["consent_status"])),
        message=str(disclosure["message"]),
    )
    demo_export = validate_export_artifact(
        export_artifact_from_dict(cast(dict[str, Any], artifacts["demo_export"])),
        expected_mime_type="text/html",
        expected_extension=".html",
    )
    render_manifest = validate_export_artifact(
        export_artifact_from_dict(cast(dict[str, Any], artifacts["render_manifest"])),
        expected_mime_type="application/json",
        expected_extension=".json",
    )
    video_export_placeholder = validate_export_artifact(
        export_artifact_from_dict(cast(dict[str, Any], artifacts["video_export_placeholder"])),
        expected_mime_type="application/json",
        expected_extension=".json",
    )
    source_script = str(row["source_script_text"])
    source_run_id = str(row["source_run_id"])
    trace_id = str(row["trace_id"])
    source_context_ref_count = int(row["source_context_ref_count"])
    source_citation_count = int(row["source_citation_count"])
    source_context_ref_ids = tuple(str(value) for value in row.get("source_context_ref_ids", ()))
    source_citation_indexes = tuple(int(value) for value in row.get("source_citation_indexes", ()))
    source_evaluation_id = normalize_evaluation_id(str(row["source_evaluation_id"]))
    evaluation_status = validate_evaluation_status(str(row["evaluation_status"]))
    source_evaluation_checksum = validate_checksum_component(
        str(row["source_evaluation_checksum"]),
        field_name="Source evaluation checksum",
    )
    canonical_evaluation_checksum = build_source_evaluation_checksum(
        source_evaluation_id=source_evaluation_id,
        source_run_id=source_run_id,
        trace_id=trace_id,
        evaluation_status=evaluation_status,
        source_context_ref_ids=source_context_ref_ids,
        source_context_ref_count=source_context_ref_count,
        source_citation_indexes=source_citation_indexes,
        source_citation_count=source_citation_count,
    )
    if source_evaluation_checksum != canonical_evaluation_checksum:
        raise ValueError("Stage 7 render source evaluation checksum does not match canonical source evidence.")
    idempotency_scope = str(row["idempotency_scope"]) if row.get("idempotency_scope") is not None else None
    idempotency_key = str(row["idempotency_key"]) if row.get("idempotency_key") is not None else None
    if "request_checksum" not in row or row.get("request_checksum") is None:
        raise ValueError("Stage 7 restored render is missing request checksum.")
    request_checksum = validate_checksum_component(
        str(row["request_checksum"]),
        field_name="Render request checksum",
    )
    tenant_id = str(row["tenant_id"]) if row.get("tenant_id") is not None else None
    project_id = str(row["project_id"]) if row.get("project_id") is not None else None
    actor_id = str(row["actor_id"]) if row.get("actor_id") is not None else None
    if (
        tenant_id is not None
        and project_id is not None
        and actor_id is not None
        and idempotency_scope != f"{tenant_id}:{actor_id}:{project_id}:{source_run_id}"
    ):
        raise ValueError("Stage 7 restored render idempotency scope does not match render ownership.")
    status = str(row["status"])
    render_job_status = str(row["render_job_status"])
    if status != "COMPLETED" or render_job_status != "COMPLETED":
        raise ValueError("Stage 7 restored render is not terminal completed state.")
    raw_render_status_history = row.get("render_job_status_history", [])
    if not isinstance(raw_render_status_history, list):
        raise ValueError("Stage 7 restored render status history is invalid.")
    if not all(isinstance(item, dict) for item in raw_render_status_history):
        raise ValueError("Stage 7 restored render status history contains invalid events.")
    render_status_history = tuple(
        RenderJobStatusEvent(
            status=validate_render_job_status(str(item["status"])),
            message=str(item["message"]),
        )
        for item in raw_render_status_history
    )
    validate_restored_render_status_history(render_status_history, fallback_reason=restored_provider.fallback_reason)
    if not render_request_checksum_matches(
        source_text=source_script,
        requested_avatar_provider=restored_provider.requested_provider,
        cloned_identity_requested=False,
        consent_to_use_synthetic_avatar=True,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        consent_record_id=str(row["consent_record_id"]) if row.get("consent_record_id") is not None else None,
        idempotency_scope=idempotency_scope,
        idempotency_key=idempotency_key,
        request_checksum=request_checksum,
    ):
        raise ValueError("Stage 7 render request checksum does not match the restored render.")
    validate_demo_html_export(
        demo_export,
        source_script=source_script,
        source_run_id=source_run_id,
        trace_id=trace_id,
        disclosure=restored_disclosure,
    )
    validate_render_manifest(
        render_manifest,
        avatar_provider=restored_provider,
        provider_config=restored_config,
        source_script=source_script,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        disclosure=restored_disclosure,
    )
    validate_video_export_placeholder(
        video_export_placeholder,
        provider_config=restored_config,
        source_script=source_script,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        disclosure=restored_disclosure,
    )
    return AvatarRenderResult(
        avatar_render_id=str(row["avatar_render_id"]),
        tenant_id=tenant_id,
        project_id=project_id,
        actor_id=actor_id,
        consent_record_id=str(row["consent_record_id"]) if row.get("consent_record_id") is not None else None,
        source_run_id=source_run_id,
        status=cast(Literal["COMPLETED"], status),
        render_job_status=cast(Literal["COMPLETED"], render_job_status),
        render_job_status_history=render_status_history,
        source_script_text=source_script,
        avatar_provider=restored_provider,
        provider_config=restored_config,
        video_renderer=VideoRendererMetadata(
            renderer=str(video_renderer["renderer"]),
            renderer_mode="LOCAL",
            export_format="html",
        ),
        disclosure=restored_disclosure,
        artifacts=AvatarArtifacts(
            demo_export=demo_export,
            render_manifest=render_manifest,
            video_export_placeholder=video_export_placeholder,
        ),
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        request_checksum=request_checksum,
        idempotency_scope=idempotency_scope,
        idempotency_key=idempotency_key,
    )


def artifact_metadata_from_dict(row: dict[str, Any]) -> tuple[str, tuple[ExportArtifactMetadata, ...]]:
    render_id = str(row["avatar_render_id"])
    if not render_id:
        raise ValueError("Stage 7 artifact metadata references missing render.")
    metadata = row["metadata"]
    if not isinstance(metadata, list):
        raise ValueError("Stage 7 artifact metadata shape is invalid.")
    parsed: list[ExportArtifactMetadata] = []
    for item in metadata:
        if not isinstance(item, dict):
            raise ValueError("Stage 7 artifact metadata entry shape is invalid.")
        parsed.append(
            ExportArtifactMetadata(
                file_name=str(item["file_name"]),
                mime_type=str(item["mime_type"]),
                checksum=str(item["checksum"]),
            )
        )
    return render_id, tuple(parsed)


def validate_restored_render_status_history(
    history: tuple[RenderJobStatusEvent, ...],
    *,
    fallback_reason: str | None,
) -> None:
    statuses = tuple(event.status for event in history)
    if not statuses:
        raise ValueError("Stage 7 restored render status history is empty.")
    if statuses[0] != "QUEUED" or statuses[-1] != "COMPLETED":
        raise ValueError("Stage 7 restored render status history is not terminal.")
    if "RUNNING" not in statuses:
        raise ValueError("Stage 7 restored render status history is missing RUNNING.")
    if statuses.count("COMPLETED") != 1:
        raise ValueError("Stage 7 restored render status history has invalid terminal markers.")
    completed_index = statuses.index("COMPLETED")
    if completed_index != len(statuses) - 1:
        raise ValueError("Stage 7 restored render status history has events after terminal completion.")
    if "FAILED" in statuses and "FALLBACK" not in statuses:
        raise ValueError("Stage 7 restored render status history has failed provider state without fallback.")
    expected_statuses: tuple[RenderJobStatus, ...] = ("QUEUED", "RUNNING", "COMPLETED")
    if "FALLBACK" in statuses:
        if fallback_reason is None:
            raise ValueError("Stage 7 restored render status history has fallback without provider fallback metadata.")
        if fallback_reason == "REQUESTED_PROVIDER_UNAVAILABLE":
            expected_statuses = ("QUEUED", "FALLBACK", "RUNNING", "COMPLETED")
        else:
            failed_fallback_statuses: tuple[tuple[RenderJobStatus, ...], ...] = (
                ("QUEUED", "RUNNING", "FAILED", "FALLBACK", "COMPLETED"),
                ("QUEUED", "FALLBACK", "RUNNING", "FAILED", "FALLBACK", "COMPLETED"),
            )
            if statuses not in failed_fallback_statuses:
                raise ValueError("Stage 7 restored render status history has invalid transition order.")
            return
    elif fallback_reason is not None:
        raise ValueError("Stage 7 restored render provider fallback metadata lacks fallback status history.")
    if statuses != expected_statuses:
        raise ValueError("Stage 7 restored render status history has invalid transition order.")


def restored_render_request_checksum_matches(result: AvatarRenderResult, request_checksum: str) -> bool:
    return result.request_checksum == request_checksum


def restored_render_idempotency_scope_matches(result: AvatarRenderResult, idempotency_scope: str) -> bool:
    if result.tenant_id is None or result.project_id is None or result.actor_id is None:
        return True
    return idempotency_scope == f"{result.tenant_id}:{result.actor_id}:{result.project_id}:{result.source_run_id}"


def synthetic_avatar_consent_record_to_dict(record: SyntheticAvatarConsentRecord) -> dict[str, Any]:
    return asdict(record)


def synthetic_avatar_consent_record_from_dict(row: dict[str, Any]) -> SyntheticAvatarConsentRecord:
    consent_statement_version = str(row["consent_statement_version"])
    if consent_statement_version != SYNTHETIC_AVATAR_CONSENT_VERSION:
        raise ValueError("Unsupported Stage 7 consent statement version.")
    consent_statement_text = str(row["consent_statement_text"])
    if consent_statement_text != SYNTHETIC_AVATAR_CONSENT_TEXT:
        raise ValueError("Stage 7 consent statement text does not match the canonical text.")
    granted_at = validate_granted_at_timestamp(str(row["granted_at"]))
    artifact_checksums = tuple(str(value) for value in row.get("artifact_checksums", ()))
    for checksum in artifact_checksums:
        validate_checksum_component(checksum, field_name="Consent artifact checksum")
    tenant_id = validate_checksum_component(str(row["tenant_id"]), field_name="Tenant identifier")
    project_id = validate_checksum_component(str(row["project_id"]), field_name="Project identifier")
    actor_id = validate_checksum_component(str(row["actor_id"]), field_name="Actor identifier")
    source_run_id = validate_checksum_component(str(row["source_run_id"]), field_name="Source run identifier")
    trace_id = validate_checksum_component(str(row["trace_id"]), field_name="Source trace identifier")
    source_context_ref_ids = tuple(
        normalize_evidence_ids(
            tuple(str(value) for value in row.get("source_context_ref_ids", ())),
            count=len(tuple(str(value) for value in row.get("source_context_ref_ids", ()))),
            prefix="context_ref",
        )
    )
    source_citation_indexes = tuple(
        normalize_citation_indexes(
            tuple(int(value) for value in row.get("source_citation_indexes", ())),
            count=len(tuple(int(value) for value in row.get("source_citation_indexes", ()))),
        )
    )
    source_evaluation_id = normalize_evaluation_id(str(row["source_evaluation_id"]))
    source_evaluation_checksum = validate_checksum_component(
        str(row["source_evaluation_checksum"]),
        field_name="Source evaluation checksum",
    )
    evaluation_status = validate_evaluation_status(str(row["evaluation_status"]))
    idempotency_scope = str(row["idempotency_scope"]) if row.get("idempotency_scope") is not None else None
    idempotency_key = str(row["idempotency_key"]) if row.get("idempotency_key") is not None else None
    request_checksum = validate_checksum_component(str(row["request_checksum"]), field_name="Consent request checksum")
    expected_request_checksum = build_avatar_consent_request_checksum(
        tenant_id=tenant_id,
        project_id=project_id,
        actor_id=actor_id,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        idempotency_scope=idempotency_scope,
        idempotency_key=idempotency_key,
    )
    if request_checksum != expected_request_checksum:
        raise ValueError("Stage 7 consent request checksum does not match the restored scope.")
    return SyntheticAvatarConsentRecord(
        consent_record_id=str(row["consent_record_id"]),
        tenant_id=tenant_id,
        project_id=project_id,
        actor_id=actor_id,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        consent_statement_version=consent_statement_version,
        consent_statement_text=consent_statement_text,
        granted_at=granted_at,
        request_checksum=request_checksum,
        idempotency_scope=idempotency_scope,
        idempotency_key=idempotency_key,
        avatar_render_id=str(row["avatar_render_id"]) if row.get("avatar_render_id") is not None else None,
        artifact_checksums=artifact_checksums,
    )


def export_artifact_from_dict(row: dict[str, Any]) -> ExportArtifact:
    return ExportArtifact(
        file_name=str(row["file_name"]),
        mime_type=str(row["mime_type"]),
        content_base64=str(row["content_base64"]),
        checksum=str(row["checksum"]),
    )


def create_stage7_service(*, state_path: Path | None = None) -> Stage7Service:
    return Stage7Service(state_path=state_path)


def resolve_avatar_provider(requested_provider: str) -> tuple[str, str | None]:
    normalized = validate_provider_id(requested_provider or "mock", field_name="requested avatar provider")
    if normalized == "mock":
        return "mock", None
    return normalized, "REQUESTED_PROVIDER_UNAVAILABLE"


def validate_provider_id(provider: str, *, field_name: str) -> str:
    if not isinstance(provider, str):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name} identifier.")
    candidate = provider.strip().lower()
    if not PROVIDER_ID_PATTERN.fullmatch(candidate):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", f"Invalid {field_name} identifier.")
    return candidate


def validate_provider_mode(provider_mode: str) -> ProviderMode:
    if not isinstance(provider_mode, str):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid provider mode.")
    candidate = provider_mode.strip().upper()
    if candidate not in {"LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"}:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid provider mode.")
    return cast(ProviderMode, candidate)


def validate_fallback_reason(fallback_reason: str | None) -> FallbackReason | None:
    if fallback_reason is None:
        return None
    if not isinstance(fallback_reason, str):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid avatar provider fallback reason.")
    candidate = fallback_reason.strip().upper()
    if candidate not in ALLOWED_FALLBACK_REASONS:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid avatar provider fallback reason.")
    return cast(FallbackReason, candidate)


def validate_provider_adapter_kind(adapter_kind: str) -> ProviderAdapterKind:
    if not isinstance(adapter_kind, str):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid provider adapter kind.")
    candidate = adapter_kind.strip().upper()
    if candidate not in {"MOCK_LOCAL", "EXTERNAL_STUB"}:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid provider adapter kind.")
    return cast(ProviderAdapterKind, candidate)


def validate_bool(value: object, *, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", f"{field_name} must be a boolean.")
    return value


def validate_consent_status(consent_status: str) -> Literal["CONFIRMED", "NOT_REQUIRED"]:
    candidate = consent_status.strip().upper()
    if candidate not in {"CONFIRMED", "NOT_REQUIRED"}:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid disclosure consent status.")
    return cast(Literal["CONFIRMED", "NOT_REQUIRED"], candidate)


def validate_render_job_status(status: str) -> RenderJobStatus:
    candidate = status.strip().upper()
    if candidate not in {"QUEUED", "RUNNING", "FAILED", "FALLBACK", "COMPLETED"}:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Invalid render job status.")
    return cast(RenderJobStatus, candidate)


def validate_provider_result(result: AvatarProviderResult) -> AvatarProviderResult:
    if not isinstance(result, AvatarProviderResult):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar provider result shape is invalid.")
    return result


def validate_provider_config(config: ProviderConfig, *, provider: str) -> ProviderConfig:
    if not isinstance(config, ProviderConfig):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Provider config shape is invalid.")
    config_provider = validate_provider_id(config.provider, field_name="provider config provider")
    if config_provider != provider:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Provider config does not match render provider.")
    provider_mode = validate_provider_mode(config.provider_mode)
    adapter_kind = validate_provider_adapter_kind(config.adapter_kind)
    for field_value in (
        config.allow_network_egress,
        config.requires_api_key,
        config.supports_real_video,
        config.supports_cloned_identity,
    ):
        if not isinstance(field_value, bool):
            raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Provider config flags must be booleans.")
    if adapter_kind != "MOCK_LOCAL":
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Stage 7 successful renders must use mock local adapters.")
    if provider_mode != "LOCAL":
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Stage 7 successful renders must be local.")
    if (
        config.allow_network_egress
        or config.requires_api_key
        or config.supports_real_video
        or config.supports_cloned_identity
    ):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Mock avatar provider config must be local-only.")
    return ProviderConfig(
        provider=config_provider,
        provider_mode=provider_mode,
        adapter_kind=adapter_kind,
        allow_network_egress=config.allow_network_egress,
        requires_api_key=config.requires_api_key,
        supports_real_video=config.supports_real_video,
        supports_cloned_identity=config.supports_cloned_identity,
    )


def validate_provider_metadata_matches_config(
    avatar_provider: AvatarProviderMetadata,
    provider_config: ProviderConfig,
) -> None:
    if avatar_provider.provider != provider_config.provider or avatar_provider.provider_mode != provider_config.provider_mode:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar provider metadata does not match provider config.")
    if avatar_provider.provider_mode != "LOCAL" or provider_config.provider_mode != "LOCAL":
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Stage 7 successful avatar renders must be local.")


def validate_evaluation_status(evaluation_status: str) -> EvaluationStatus:
    if not isinstance(evaluation_status, str):
        return "UNKNOWN"
    candidate = evaluation_status.strip().upper() or "UNKNOWN"
    if candidate not in {"PASSED", "FAILED", "UNKNOWN"}:
        return "UNKNOWN"
    return cast(EvaluationStatus, candidate)


def validate_checksum_component(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 128:
        raise Stage7Error(422, "VALIDATION_ERROR", f"{field_name} is invalid.")
    if CHECKSUM_COMPONENT_DELIMITER_PATTERN.search(value):
        raise Stage7Error(422, "VALIDATION_ERROR", f"{field_name} contains invalid checksum delimiters.")
    return value


def normalize_evidence_ids(values: tuple[str, ...] | None, *, count: int, prefix: str) -> tuple[str, ...]:
    if count < 0:
        raise Stage7Error(422, "VALIDATION_ERROR", "Source evidence count is invalid.")
    if values is None:
        if count == 0:
            return ()
        raise Stage7Error(422, "VALIDATION_ERROR", "Source evidence identifiers are required.")
    normalized = values
    if len(normalized) != count:
        raise Stage7Error(422, "VALIDATION_ERROR", "Source evidence identifiers do not match source evidence count.")
    for value in normalized:
        if not isinstance(value, str) or not value.strip() or len(value) > 128:
            raise Stage7Error(422, "VALIDATION_ERROR", "Source evidence identifier is invalid.")
    return tuple(
        validate_checksum_component(value.strip(), field_name="Source evidence identifier") for value in normalized
    )


def normalize_citation_indexes(values: tuple[int, ...] | None, *, count: int) -> tuple[int, ...]:
    if count < 0:
        raise Stage7Error(422, "VALIDATION_ERROR", "Source citation count is invalid.")
    if values is None:
        if count == 0:
            return ()
        raise Stage7Error(422, "VALIDATION_ERROR", "Source citation indexes are required.")
    normalized = values
    if len(normalized) != count:
        raise Stage7Error(422, "VALIDATION_ERROR", "Source citation indexes do not match source citation count.")
    for value in normalized:
        if not isinstance(value, int) or value <= 0:
            raise Stage7Error(422, "VALIDATION_ERROR", "Source citation index is invalid.")
    return tuple(normalized)


def normalize_evaluation_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 128:
        raise Stage7Error(422, "VALIDATION_ERROR", "Source evaluation identifier is invalid.")
    return validate_checksum_component(value.strip(), field_name="Source evaluation identifier")


def build_source_evaluation_checksum(
    *,
    source_evaluation_id: str,
    source_run_id: str,
    trace_id: str,
    evaluation_status: str,
    source_context_ref_ids: tuple[str, ...] | None,
    source_context_ref_count: int,
    source_citation_indexes: tuple[int, ...] | None,
    source_citation_count: int,
) -> str:
    normalized_evaluation_id = normalize_evaluation_id(source_evaluation_id)
    normalized_source_run_id = validate_checksum_component(source_run_id, field_name="Source run identifier")
    normalized_trace_id = validate_checksum_component(trace_id, field_name="Source trace identifier")
    normalized_evaluation_status = validate_evaluation_status(evaluation_status)
    normalized_context_ref_ids = normalize_evidence_ids(
        source_context_ref_ids,
        count=source_context_ref_count,
        prefix="context_ref",
    )
    normalized_citation_indexes = normalize_citation_indexes(
        source_citation_indexes,
        count=source_citation_count,
    )
    return checksum_text(
        "\n".join(
            [
                normalized_evaluation_id,
                normalized_source_run_id,
                normalized_trace_id,
                normalized_evaluation_status,
                ",".join(normalized_context_ref_ids),
                ",".join(str(index) for index in normalized_citation_indexes),
            ]
        )
    )


def build_avatar_render_request_checksum(
    *,
    source_text: str,
    requested_avatar_provider: str,
    cloned_identity_requested: bool,
    consent_to_use_synthetic_avatar: bool,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...] | None,
    source_citation_indexes: tuple[int, ...] | None,
    source_evaluation_id: str,
    source_evaluation_checksum: str | None,
    evaluation_status: str,
    consent_record_id: str | None = None,
    idempotency_scope: str | None = None,
    idempotency_key: str | None = None,
) -> str:
    normalized_source_text = source_text.strip()
    normalized_requested_avatar_provider = (requested_avatar_provider or "mock").strip().lower()
    normalized_source_run_id = validate_checksum_component(source_run_id, field_name="Source run identifier")
    normalized_trace_id = validate_checksum_component(trace_id, field_name="Source trace identifier")
    normalized_context_ref_ids = normalize_evidence_ids(
        source_context_ref_ids,
        count=source_context_ref_count,
        prefix="context_ref",
    )
    normalized_citation_indexes = normalize_citation_indexes(
        source_citation_indexes,
        count=source_citation_count,
    )
    normalized_evaluation_id = normalize_evaluation_id(source_evaluation_id)
    normalized_evaluation_checksum = (
        validate_checksum_component(source_evaluation_checksum, field_name="Source evaluation checksum")
        if source_evaluation_checksum is not None
        else None
    )
    normalized_evaluation_status = validate_evaluation_status(evaluation_status)
    normalized_consent_record_id = (
        validate_checksum_component(consent_record_id, field_name="Consent record identifier")
        if consent_record_id is not None
        else None
    )
    normalized_idempotency_scope = (
        validate_checksum_component(idempotency_scope, field_name="Idempotency scope")
        if idempotency_scope is not None
        else None
    )
    normalized_idempotency_key = (
        validate_checksum_component(idempotency_key, field_name="Idempotency key")
        if idempotency_key is not None
        else None
    )
    return checksum_text(
        json.dumps(
            {
                "clonedIdentityRequested": cloned_identity_requested,
                "consentRecordId": normalized_consent_record_id,
                "consentToUseSyntheticAvatar": consent_to_use_synthetic_avatar,
                "evaluationStatus": normalized_evaluation_status,
                "idempotencyKey": normalized_idempotency_key,
                "idempotencyScope": normalized_idempotency_scope,
                "requestedAvatarProvider": normalized_requested_avatar_provider,
                "sourceCitationCount": source_citation_count,
                "sourceCitationIndexes": list(normalized_citation_indexes),
                "sourceContextRefCount": source_context_ref_count,
                "sourceContextRefIds": list(normalized_context_ref_ids),
                "sourceEvaluationChecksum": normalized_evaluation_checksum,
                "sourceEvaluationId": normalized_evaluation_id,
                "sourceRunId": normalized_source_run_id,
                "sourceText": normalized_source_text,
                "traceId": normalized_trace_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def render_request_checksum_matches(
    *,
    source_text: str,
    requested_avatar_provider: str,
    cloned_identity_requested: bool,
    consent_to_use_synthetic_avatar: bool,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...] | None,
    source_citation_indexes: tuple[int, ...] | None,
    source_evaluation_id: str,
    source_evaluation_checksum: str | None,
    evaluation_status: str,
    consent_record_id: str | None,
    idempotency_scope: str | None,
    idempotency_key: str | None,
    request_checksum: str,
) -> bool:
    return request_checksum == build_avatar_render_request_checksum(
        source_text=source_text,
        requested_avatar_provider=requested_avatar_provider,
        cloned_identity_requested=cloned_identity_requested,
        consent_to_use_synthetic_avatar=consent_to_use_synthetic_avatar,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        consent_record_id=consent_record_id,
        idempotency_scope=idempotency_scope,
        idempotency_key=idempotency_key,
    )


def build_avatar_consent_request_checksum(
    *,
    tenant_id: str,
    project_id: str,
    actor_id: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    idempotency_scope: str | None = None,
    idempotency_key: str | None = None,
) -> str:
    normalized_idempotency_scope = (
        validate_checksum_component(idempotency_scope, field_name="Idempotency scope")
        if idempotency_scope is not None
        else None
    )
    normalized_idempotency_key = (
        validate_checksum_component(idempotency_key, field_name="Idempotency key")
        if idempotency_key is not None
        else None
    )
    return checksum_text(
        json.dumps(
            {
                "actorId": actor_id,
                "consentStatementText": SYNTHETIC_AVATAR_CONSENT_TEXT,
                "consentStatementVersion": SYNTHETIC_AVATAR_CONSENT_VERSION,
                "evaluationStatus": evaluation_status,
                "idempotencyKey": normalized_idempotency_key,
                "idempotencyScope": normalized_idempotency_scope,
                "projectId": project_id,
                "sourceCitationIndexes": list(source_citation_indexes),
                "sourceContextRefIds": list(source_context_ref_ids),
                "sourceEvaluationChecksum": source_evaluation_checksum,
                "sourceEvaluationId": source_evaluation_id,
                "sourceRunId": source_run_id,
                "tenantId": tenant_id,
                "traceId": trace_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError(f"Duplicate JSON key: {key}")
        parsed[key] = value
    return parsed


def parse_provider_json_object(artifact: ExportArtifact, *, artifact_name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(decode_artifact_text(artifact), object_pairs_hook=reject_duplicate_json_keys)
    except json.JSONDecodeError as exc:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", f"{artifact_name} must contain valid JSON.") from exc
    except ValueError as exc:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", f"{artifact_name} must not contain duplicate JSON keys.") from exc
    if not isinstance(parsed, dict):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", f"{artifact_name} must be a JSON object.")
    return parsed


def validate_export_artifact(
    artifact: ExportArtifact,
    *,
    expected_mime_type: str,
    expected_extension: str,
) -> ExportArtifact:
    if not isinstance(artifact, ExportArtifact):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact shape is invalid.")
    if not all(
        isinstance(value, str)
        for value in (artifact.file_name, artifact.mime_type, artifact.content_base64, artifact.checksum)
    ):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact fields are invalid.")
    if artifact.mime_type != expected_mime_type:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact MIME type is invalid.")
    if not artifact.file_name.endswith(expected_extension) or not is_safe_artifact_filename(artifact.file_name):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact filename is invalid.")
    try:
        decoded_bytes = base64.b64decode(artifact.content_base64, validate=True)
        decoded_text = decoded_bytes.decode("utf-8")
    except (binascii.Error, TypeError, UnicodeDecodeError) as exc:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact content is invalid.") from exc
    if len(decoded_bytes) > MAX_EXPORT_ARTIFACT_BYTES:
        raise Stage7Error(413, "PROVIDER_OUTPUT_TOO_LARGE", "Avatar export artifact exceeds the Stage 7 limit.")
    if artifact.checksum != checksum_text(decoded_text):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact checksum is invalid.")
    return artifact


def decode_artifact_text(artifact: ExportArtifact) -> str:
    try:
        return base64.b64decode(artifact.content_base64, validate=True).decode("utf-8")
    except (binascii.Error, TypeError, UnicodeDecodeError) as exc:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar export artifact content is invalid.") from exc


def validate_demo_html_export(
    artifact: ExportArtifact,
    *,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    disclosure: DisclosureMetadata,
) -> None:
    decoded = decode_artifact_text(artifact)
    if ACTIVE_HTML_PATTERN.search(decoded):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar HTML export contains active content.")
    expected = render_demo_html(
        source_script=source_script,
        source_run_id=source_run_id,
        trace_id=trace_id,
        scene_count=estimate_scene_count(source_script),
        disclosure=disclosure,
    )
    if decoded != expected:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Avatar HTML export does not match trusted renderer output.")


def validate_render_manifest(
    artifact: ExportArtifact,
    *,
    avatar_provider: AvatarProviderMetadata,
    provider_config: ProviderConfig,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    disclosure: DisclosureMetadata,
) -> None:
    parsed = parse_provider_json_object(artifact, artifact_name="Render manifest")
    expected = expected_render_manifest_payload(
        avatar_provider=avatar_provider,
        provider_config=provider_config,
        source_script=source_script,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        disclosure=disclosure,
        scene_count=estimate_scene_count(source_script),
    )
    if parsed != expected:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Render manifest metadata is invalid.")


def validate_video_export_placeholder(
    artifact: ExportArtifact,
    *,
    provider_config: ProviderConfig,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    disclosure: DisclosureMetadata,
) -> None:
    parsed = parse_provider_json_object(artifact, artifact_name="Video export placeholder")
    expected = expected_video_export_placeholder_payload(
        provider_config=provider_config,
        source_script=source_script,
        source_run_id=source_run_id,
        trace_id=trace_id,
        source_context_ref_count=source_context_ref_count,
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_id=source_evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=evaluation_status,
        disclosure=disclosure,
    )
    if parsed != expected:
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Video export placeholder metadata is invalid.")


def expected_disclosure_payload(disclosure: DisclosureMetadata) -> dict[str, object]:
    return {
        "aiGenerated": disclosure.ai_generated,
        "clonedIdentity": disclosure.cloned_identity,
        "consentRequired": disclosure.consent_required,
        "consentStatus": disclosure.consent_status,
        "message": disclosure.message,
    }


def expected_source_payload(
    *,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
) -> dict[str, object]:
    return {
        "runId": source_run_id,
        "traceId": trace_id,
        "contextRefCount": source_context_ref_count,
        "contextRefIds": list(source_context_ref_ids),
        "citationCount": source_citation_count,
        "citationIndexes": list(source_citation_indexes),
        "evaluationId": source_evaluation_id,
        "evaluationChecksum": source_evaluation_checksum,
        "evaluationStatus": evaluation_status,
        "scriptChecksum": checksum_text(source_script),
    }


def expected_render_manifest_payload(
    *,
    avatar_provider: AvatarProviderMetadata,
    provider_config: ProviderConfig,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    disclosure: DisclosureMetadata,
    scene_count: object,
) -> dict[str, object]:
    if not isinstance(scene_count, int):
        raise Stage7Error(422, "PROVIDER_OUTPUT_INVALID", "Render manifest scene count is invalid.")
    return {
        "schema": "Stage7AvatarRenderManifest",
        "version": "stage7-mock-avatar-render-v1",
        "provider": {
            "provider": avatar_provider.provider,
            "providerMode": avatar_provider.provider_mode,
            "requestedProvider": avatar_provider.requested_provider,
            "fallbackReason": avatar_provider.fallback_reason,
        },
        "providerConfig": provider_config_to_manifest(provider_config),
        "renderer": {
            "renderer": "local-html",
            "rendererMode": "LOCAL",
            "exportFormat": "html",
        },
        "source": expected_source_payload(
            source_script=source_script,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
        ),
        "disclosure": expected_disclosure_payload(disclosure),
        "sceneCountEstimate": scene_count,
        "videoExportPlaceholder": {
            "status": "PLACEHOLDER_ONLY",
            "mimeType": "application/json",
            "realVideoProduced": False,
        },
        "publicUseLicenseCheck": PUBLIC_USE_LICENSE_CHECK,
    }


def expected_video_export_placeholder_payload(
    *,
    provider_config: ProviderConfig,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    source_context_ref_count: int,
    source_citation_count: int,
    source_context_ref_ids: tuple[str, ...],
    source_citation_indexes: tuple[int, ...],
    source_evaluation_id: str,
    source_evaluation_checksum: str,
    evaluation_status: EvaluationStatus,
    disclosure: DisclosureMetadata,
) -> dict[str, object]:
    return {
        "schema": "Stage7VideoExportPlaceholder",
        "version": "stage7-video-export-placeholder-v1",
        "status": "PLACEHOLDER_ONLY",
        "realVideoProduced": False,
        "renderer": "local-html",
        "providerConfig": provider_config_to_manifest(provider_config),
        "disclosure": expected_disclosure_payload(disclosure),
        "source": expected_source_payload(
            source_script=source_script,
            source_run_id=source_run_id,
            trace_id=trace_id,
            source_context_ref_count=source_context_ref_count,
            source_citation_count=source_citation_count,
            source_context_ref_ids=source_context_ref_ids,
            source_citation_indexes=source_citation_indexes,
            source_evaluation_id=source_evaluation_id,
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
        ),
        "publicUseLicenseCheck": PUBLIC_USE_LICENSE_CHECK,
        "sourceRunId": source_run_id,
        "traceId": trace_id,
        "reason": "Stage 7 exports a validated HTML demo and metadata, not a real video binary.",
    }


def is_safe_artifact_filename(file_name: str) -> bool:
    if not file_name or "/" in file_name or "\\" in file_name:
        return False
    return not any(ord(character) < 32 or ord(character) == 127 for character in file_name)


def disclosure_metadata() -> DisclosureMetadata:
    return DisclosureMetadata(
        ai_generated=True,
        cloned_identity=False,
        consent_required=True,
        consent_status="CONFIRMED",
        message=(
            "AI-generated avatar demo export using a synthetic local presenter. "
            "No cloned face, cloned voice, or paid avatar provider was used."
        ),
    )


def utc_now_isoformat() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_granted_at_timestamp(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("Stage 7 consent record granted_at is required.")
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Stage 7 consent record granted_at must be an ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None:
        raise ValueError("Stage 7 consent record granted_at must include a timezone offset.")
    return candidate


def estimate_scene_count(source_script: str) -> int:
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", source_script.strip()) if part]
    return max(1, min(12, len(sentences)))


def render_demo_html(
    *,
    source_script: str,
    source_run_id: str,
    trace_id: str,
    scene_count: int,
    disclosure: DisclosureMetadata,
) -> str:
    escaped_script = html.escape(source_script)
    escaped_disclosure = html.escape(disclosure.message)
    escaped_run = html.escape(source_run_id)
    escaped_trace = html.escape(trace_id)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        "  <title>NarraTwin AI Avatar Demo Export</title>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        "    <h1>NarraTwin AI Avatar Demo Export</h1>\n"
        f"    <p>{escaped_disclosure}</p>\n"
        f"    <p>Source run: {escaped_run}</p>\n"
        f"    <p>Trace: {escaped_trace}</p>\n"
        f"    <p>Scene count estimate: {scene_count}</p>\n"
        f"    <article>{escaped_script}</article>\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def artifact_from_text(*, file_name: str, mime_type: str, text: str) -> ExportArtifact:
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return ExportArtifact(
        file_name=file_name,
        mime_type=mime_type,
        content_base64=encoded,
        checksum=checksum_text(text),
    )


def provider_config_to_manifest(config: ProviderConfig) -> dict[str, object]:
    return {
        "provider": config.provider,
        "providerMode": config.provider_mode,
        "adapterKind": config.adapter_kind,
        "allowNetworkEgress": config.allow_network_egress,
        "requiresApiKey": config.requires_api_key,
        "supportsRealVideo": config.supports_real_video,
        "supportsClonedIdentity": config.supports_cloned_identity,
    }


def avatar_render_to_api(result: AvatarRenderResult) -> dict[str, object]:
    return {
        "avatarRenderId": result.avatar_render_id,
        "consentRecordId": result.consent_record_id,
        "sourceRunId": result.source_run_id,
        "status": result.status,
        "renderJobStatus": result.render_job_status,
        "renderJobStatusHistory": [
            {"status": event.status, "message": event.message} for event in result.render_job_status_history
        ],
        "sourceScriptText": result.source_script_text,
        "avatarProvider": {
            "provider": result.avatar_provider.provider,
            "providerMode": result.avatar_provider.provider_mode,
            "requestedProvider": result.avatar_provider.requested_provider,
            "fallbackReason": result.avatar_provider.fallback_reason,
        },
        "providerConfig": {
            "provider": result.provider_config.provider,
            "providerMode": result.provider_config.provider_mode,
            "adapterKind": result.provider_config.adapter_kind,
            "allowNetworkEgress": result.provider_config.allow_network_egress,
            "requiresApiKey": result.provider_config.requires_api_key,
            "supportsRealVideo": result.provider_config.supports_real_video,
            "supportsClonedIdentity": result.provider_config.supports_cloned_identity,
        },
        "videoRenderer": {
            "renderer": result.video_renderer.renderer,
            "rendererMode": result.video_renderer.renderer_mode,
            "exportFormat": result.video_renderer.export_format,
        },
        "disclosure": {
            "aiGenerated": result.disclosure.ai_generated,
            "clonedIdentity": result.disclosure.cloned_identity,
            "consentRequired": result.disclosure.consent_required,
            "consentStatus": result.disclosure.consent_status,
            "message": result.disclosure.message,
        },
        "artifacts": {
            "demoExport": artifact_to_api(result.artifacts.demo_export),
            "renderManifest": artifact_to_api(result.artifacts.render_manifest),
            "videoExportPlaceholder": artifact_to_api(result.artifacts.video_export_placeholder),
        },
        "trace": {
            "traceId": result.trace_id,
            "sourceContextRefCount": result.source_context_ref_count,
            "sourceCitationCount": result.source_citation_count,
            "sourceContextRefIds": list(result.source_context_ref_ids),
            "sourceCitationIndexes": list(result.source_citation_indexes),
            "sourceEvaluationId": result.source_evaluation_id,
            "sourceEvaluationChecksum": result.source_evaluation_checksum,
            "evaluationStatus": result.evaluation_status,
        },
    }


def avatar_consent_to_api(record: SyntheticAvatarConsentRecord) -> dict[str, object]:
    return {
        "consentRecordId": record.consent_record_id,
        "tenantId": record.tenant_id,
        "projectId": record.project_id,
        "actorId": record.actor_id,
        "sourceRunId": record.source_run_id,
        "traceId": record.trace_id,
        "sourceContextRefIds": list(record.source_context_ref_ids),
        "sourceCitationIndexes": list(record.source_citation_indexes),
        "sourceEvaluationId": record.source_evaluation_id,
        "sourceEvaluationChecksum": record.source_evaluation_checksum,
        "evaluationStatus": record.evaluation_status,
        "consentStatementVersion": record.consent_statement_version,
        "consentStatementText": record.consent_statement_text,
        "grantedAt": record.granted_at,
        "requestChecksum": record.request_checksum,
        "avatarRenderId": record.avatar_render_id,
        "artifactChecksums": list(record.artifact_checksums),
    }


def artifact_to_api(artifact: ExportArtifact) -> dict[str, str]:
    return {
        "fileName": artifact.file_name,
        "mimeType": artifact.mime_type,
        "contentBase64": artifact.content_base64,
        "checksum": artifact.checksum,
    }


stage7_service = create_stage7_service(state_path=resolve_state_file("stage7"))
