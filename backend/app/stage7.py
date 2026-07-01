"""Stage 7 mock/local avatar rendering and demo export."""

from __future__ import annotations

import base64
import binascii
import html
import json
import re
import threading
from dataclasses import dataclass
from typing import Any, Literal, Protocol, cast

from backend.app.rag.chunking import checksum_text

MAX_SOURCE_SCRIPT_CHARS = 20_000
MAX_EXPORT_ARTIFACT_BYTES = 512 * 1024
MAX_PROVIDER_ID_CHARS = 64
MAX_IDEMPOTENCY_RECORDS_PER_SCOPE = 100
PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
ACTIVE_HTML_PATTERN = re.compile(
    r"(<script\b|<iframe\b|<form\b|<object\b|<embed\b|<link\b|<base\b|<style\b|"
    r"<meta\s+http-equiv\b|<[^>]+\s(?:on[a-z]+|src|href|srcset|style)\s*=|"
    r"<[^>]+javascript:)",
    re.IGNORECASE,
)
CHECKSUM_COMPONENT_DELIMITER_PATTERN = re.compile(r"[\x00-\x1f\x7f,]")
PUBLIC_USE_LICENSE_CHECK = "mock-local-provider-only-no-third-party-media"
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
    ) -> None:
        self.avatar_provider = avatar_provider or MockAvatarProvider()
        self.fallback_avatar_provider = fallback_avatar_provider or MockAvatarProvider()
        self.idempotency_records: dict[tuple[str, str, str], Stage7IdempotencyRecord] = {}
        self.avatar_renders: dict[str, AvatarRenderResult] = {}
        self.artifact_metadata: dict[str, tuple[ExportArtifactMetadata, ...]] = {}
        self._operation_lock = threading.Lock()
        self._run_counter = 0

    def reset(self) -> None:
        with self._operation_lock:
            self.avatar_provider = MockAvatarProvider()
            self.fallback_avatar_provider = MockAvatarProvider()
            self.idempotency_records.clear()
            self.avatar_renders.clear()
            self.artifact_metadata.clear()
            self._run_counter = 0

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
        idempotency_scope: str | None = None,
        idempotency_key: str | None = None,
    ) -> AvatarRenderResult:
        source_text = source_script.strip()
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
            source_evaluation_checksum=source_evaluation_checksum,
            evaluation_status=evaluation_status,
        )
        endpoint = "POST /api/v1/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders"
        record_key: tuple[str, str, str] | None = None
        if idempotency_scope and idempotency_key:
            record_key = (idempotency_scope, endpoint, idempotency_key)
            with self._operation_lock:
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
                    endpoint=endpoint,
                    idempotency_key=idempotency_key,
                    request_checksum=request_checksum,
                    status="RUNNING",
                    value=None,
                )

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
            if source_evaluation_checksum is not None and source_evaluation_checksum != canonical_evaluation_checksum:
                raise Stage7Error(
                    422,
                    "VALIDATION_ERROR",
                    "Source evaluation checksum does not match canonical source evidence.",
                )
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
            raise
        if record_key is not None:
            with self._operation_lock:
                record = self.idempotency_records[record_key]
                record.status = "SUCCEEDED"
                record.value = result
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
        return sum(record.idempotency_scope == idempotency_scope for record in self.idempotency_records.values())


def create_stage7_service() -> Stage7Service:
    return Stage7Service()


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
) -> str:
    return checksum_text(
        json.dumps(
            {
                "clonedIdentityRequested": cloned_identity_requested,
                "consentToUseSyntheticAvatar": consent_to_use_synthetic_avatar,
                "evaluationStatus": evaluation_status,
                "requestedAvatarProvider": requested_avatar_provider,
                "sourceCitationCount": source_citation_count,
                "sourceCitationIndexes": list(source_citation_indexes) if source_citation_indexes is not None else None,
                "sourceContextRefCount": source_context_ref_count,
                "sourceContextRefIds": list(source_context_ref_ids) if source_context_ref_ids is not None else None,
                "sourceEvaluationChecksum": source_evaluation_checksum,
                "sourceEvaluationId": source_evaluation_id,
                "sourceRunId": source_run_id,
                "sourceText": source_text,
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


def artifact_to_api(artifact: ExportArtifact) -> dict[str, str]:
    return {
        "fileName": artifact.file_name,
        "mimeType": artifact.mime_type,
        "contentBase64": artifact.content_base64,
        "checksum": artifact.checksum,
    }


stage7_service = create_stage7_service()
