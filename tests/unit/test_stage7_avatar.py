import base64
import json
import threading
from typing import cast

import pytest

from backend.app.stage7 import (
    AvatarProviderResult,
    AvatarProvider,
    ExportArtifact,
    ExternalAvatarProviderStub,
    ProviderConfig,
    Stage7Error,
    artifact_from_text,
    create_stage7_service,
)


def test_mock_avatar_render_returns_valid_demo_export_with_disclosure() -> None:
    service = create_stage7_service()

    result = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        source_run_id="run_stage7",
        trace_id="trace_stage7",
        source_context_ref_count=1,
        source_citation_count=1,
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
    )

    assert result.status == "COMPLETED"
    assert result.render_job_status == "COMPLETED"
    assert [event.status for event in result.render_job_status_history] == ["QUEUED", "RUNNING", "COMPLETED"]
    assert result.avatar_provider.provider == "mock"
    assert result.avatar_provider.provider_mode == "LOCAL"
    assert result.provider_config.provider == "mock"
    assert result.provider_config.adapter_kind == "MOCK_LOCAL"
    assert result.provider_config.allow_network_egress is False
    assert result.provider_config.requires_api_key is False
    assert result.provider_config.supports_real_video is False
    assert result.video_renderer.renderer == "local-html"
    assert result.disclosure.ai_generated is True
    assert result.disclosure.cloned_identity is False
    assert result.trace_id == "trace_stage7"
    assert result.source_context_ref_count == 1
    assert result.source_citation_count == 1
    assert result.evaluation_status == "PASSED"
    assert result.artifacts.demo_export.file_name == "run_stage7-avatar-demo.html"
    assert result.artifacts.demo_export.mime_type == "text/html"
    assert result.artifacts.render_manifest.file_name == "run_stage7-avatar-render-manifest.json"
    assert result.artifacts.video_export_placeholder.file_name == "run_stage7-video-export-placeholder.json"
    assert service.avatar_renders[result.avatar_render_id] == result
    assert [artifact.file_name for artifact in service.artifact_metadata[result.avatar_render_id]] == [
        "run_stage7-avatar-demo.html",
        "run_stage7-avatar-render-manifest.json",
        "run_stage7-video-export-placeholder.json",
    ]

    manifest = json.loads(base64.b64decode(result.artifacts.render_manifest.content_base64).decode("utf-8"))
    assert manifest["disclosure"]["message"].startswith("AI-generated avatar demo")
    assert manifest["source"]["citationCount"] == 1
    assert manifest["source"]["contextRefIds"] == ["context_ref_001"]
    assert manifest["source"]["citationIndexes"] == [1]
    assert manifest["source"]["evaluationId"] == "local_evaluation"
    assert manifest["source"]["evaluationChecksum"].startswith("sha256:")
    assert manifest["source"]["evaluationStatus"] == "PASSED"
    assert manifest["provider"]["providerMode"] == "LOCAL"
    assert manifest["providerConfig"]["allowNetworkEgress"] is False
    assert manifest["videoExportPlaceholder"]["realVideoProduced"] is False
    assert manifest["publicUseLicenseCheck"] == "mock-local-provider-only-no-third-party-media"

    placeholder = json.loads(base64.b64decode(result.artifacts.video_export_placeholder.content_base64).decode("utf-8"))
    assert placeholder["status"] == "PLACEHOLDER_ONLY"
    assert placeholder["realVideoProduced"] is False
    assert placeholder["providerConfig"]["providerMode"] == "LOCAL"
    assert placeholder["source"]["contextRefIds"] == ["context_ref_001"]
    assert placeholder["source"]["evaluationId"] == "local_evaluation"
    assert placeholder["disclosure"]["aiGenerated"] is True
    assert placeholder["publicUseLicenseCheck"] == "mock-local-provider-only-no-third-party-media"


def test_mock_avatar_render_allows_benign_escaped_web_terms_in_source_text() -> None:
    service = create_stage7_service()

    result = service.render_avatar_demo(
        source_script=(
            "NarraTwin AI documents CSS modules, src= examples, href= examples, "
            "and url() prose as inert project text. [1]"
        ),
        requested_avatar_provider="mock",
        source_run_id="run_web_terms",
        trace_id="trace_web_terms",
        source_context_ref_count=1,
        source_citation_count=1,
        evaluation_status="PASSED",
        consent_to_use_synthetic_avatar=True,
    )

    assert result.status == "COMPLETED"
    html_text = base64.b64decode(result.artifacts.demo_export.content_base64).decode("utf-8")
    assert "CSS modules" in html_text
    assert "src= examples" in html_text
    assert "href= examples" in html_text
    assert "url() prose" in html_text


def test_requested_avatar_provider_falls_back_to_mock_local_provider() -> None:
    service = create_stage7_service()

    result = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="external-avatar",
        consent_to_use_synthetic_avatar=True,
    )

    assert result.avatar_provider.provider == "mock"
    assert result.avatar_provider.requested_provider == "external-avatar"
    assert result.avatar_provider.fallback_reason == "REQUESTED_PROVIDER_UNAVAILABLE"
    assert [event.status for event in result.render_job_status_history] == [
        "QUEUED",
        "FALLBACK",
        "RUNNING",
        "COMPLETED",
    ]


def test_failed_provider_uses_mock_fallback_and_records_status_history() -> None:
    service = create_stage7_service()
    service.avatar_provider = ExternalAvatarProviderStub()

    result = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="external-avatar-stub",
        source_run_id="run_failed_provider",
        consent_to_use_synthetic_avatar=True,
    )

    assert result.status == "COMPLETED"
    assert result.avatar_provider.provider == "mock"
    assert result.avatar_provider.fallback_reason == "PROVIDER_RENDER_FAILED"
    assert result.provider_config.adapter_kind == "MOCK_LOCAL"
    assert [event.status for event in result.render_job_status_history] == [
        "QUEUED",
        "FALLBACK",
        "RUNNING",
        "FAILED",
        "FALLBACK",
        "COMPLETED",
    ]


def test_cloned_identity_request_is_disabled_without_export() -> None:
    service = create_stage7_service()

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            cloned_identity_requested=True,
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "CLONED_IDENTITY_DISABLED"


def test_synthetic_avatar_consent_is_required() -> None:
    service = create_stage7_service()

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=False,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "AVATAR_CONSENT_REQUIRED"


def test_provider_artifacts_must_use_safe_expected_export_shapes() -> None:
    class InvalidAvatarProvider:
        provider = "invalid-local"
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            del (
                source_script,
                requested_provider,
                fallback_reason,
                source_run_id,
                trace_id,
                source_context_ref_count,
                source_citation_count,
                evaluation_status,
            )
            artifact = ExportArtifact(
                file_name="../demo.mp4",
                mime_type="video/mp4",
                content_base64=base64.b64encode(b"not-html").decode("ascii"),
                checksum="sha256:not-the-content",
            )
            return AvatarProviderResult(
                provider=self.provider,
                provider_mode=self.provider_mode,
                requested_provider="mock",
                fallback_reason=None,
                provider_config=ProviderConfig(
                    provider=self.provider,
                    provider_mode="LOCAL",
                    adapter_kind="MOCK_LOCAL",
                    allow_network_egress=False,
                    requires_api_key=False,
                    supports_real_video=False,
                    supports_cloned_identity=False,
                ),
                demo_export=artifact,
                render_manifest=artifact,
                video_export_placeholder=artifact,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, InvalidAvatarProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_provider_config_is_validated_before_artifacts_are_stored() -> None:
    class InvalidConfigProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            del (
                source_context_ref_count,
                source_citation_count,
                evaluation_status,
            )
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=0,
                source_citation_count=0,
                evaluation_status="PASSED",
            )
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=ProviderConfig(
                    provider="mock",
                    provider_mode="LOCAL",
                    adapter_kind="MOCK_LOCAL",
                    allow_network_egress=True,
                    requires_api_key=False,
                    supports_real_video=False,
                    supports_cloned_identity=False,
                ),
                demo_export=valid_result.demo_export,
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, InvalidConfigProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_external_stub_config_cannot_produce_successful_stage7_output() -> None:
    class ExternalConfigProvider:
        provider = "external-avatar-stub"
        provider_mode = "OPTIONAL_EXTERNAL"

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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            return AvatarProviderResult(
                provider=self.provider,
                provider_mode=self.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=ProviderConfig(
                    provider=self.provider,
                    provider_mode="OPTIONAL_EXTERNAL",
                    adapter_kind="EXTERNAL_STUB",
                    allow_network_egress=True,
                    requires_api_key=True,
                    supports_real_video=True,
                    supports_cloned_identity=True,
                ),
                demo_export=valid_result.demo_export,
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, ExternalConfigProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_provider_mode_must_match_validated_provider_config() -> None:
    class MismatchedProviderModeProvider:
        provider = "mock"
        provider_mode = "OPTIONAL_EXTERNAL"

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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=self.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=valid_result.demo_export,
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, MismatchedProviderModeProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_provider_fallback_reason_is_enum_validated() -> None:
    class InvalidFallbackReasonProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason="network timeout with internal host details",
                provider_config=valid_result.provider_config,
                demo_export=valid_result.demo_export,
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, InvalidFallbackReasonProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_malformed_provider_output_is_rejected_without_server_error() -> None:
    class MalformedProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            return AvatarProviderResult(
                provider=self.provider,
                provider_mode=self.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=cast(ProviderConfig, None),
                demo_export=cast(ExportArtifact, {"fileName": "not-a-dataclass"}),
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, MalformedProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


@pytest.mark.parametrize(
    "html_payload",
    [
        "<html><body><script>alert('x')</script></body></html>",
        "<html><head><style>@import url('https://example.test/a.css')</style></head><body></body></html>",
        '<html><head><base href="https://example.test/"></head><body></body></html>',
        '<html><body><img srcset="x 1x"></body></html>',
    ],
)
def test_provider_html_export_rejects_active_content(html_payload: str) -> None:
    class ActiveHtmlProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=artifact_from_text(
                    file_name=f"{source_run_id}-avatar-demo.html",
                    mime_type="text/html",
                    text=html_payload,
                ),
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, ActiveHtmlProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_provider_html_export_must_exactly_match_trusted_renderer() -> None:
    class TamperedHtmlProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            html_text = base64.b64decode(valid_result.demo_export.content_base64).decode("utf-8")
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=artifact_from_text(
                    file_name=valid_result.demo_export.file_name,
                    mime_type=valid_result.demo_export.mime_type,
                    text=html_text.replace("</main>", "<p>extra provider note</p></main>"),
                ),
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, TamperedHtmlProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_render_manifest_must_match_trusted_source_and_disclosure() -> None:
    class MismatchedManifestProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            manifest = json.loads(base64.b64decode(valid_result.render_manifest.content_base64).decode("utf-8"))
            manifest["source"]["traceId"] = "trace_wrong"
            manifest["disclosure"]["clonedIdentity"] = True
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=valid_result.demo_export,
                render_manifest=artifact_from_text(
                    file_name=valid_result.render_manifest.file_name,
                    mime_type=valid_result.render_manifest.mime_type,
                    text=json.dumps(manifest, sort_keys=True),
                ),
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, MismatchedManifestProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            source_run_id="run_stage7",
            trace_id="trace_stage7",
            source_context_ref_count=1,
            source_citation_count=1,
            evaluation_status="PASSED",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_render_manifest_rejects_unexpected_provider_metadata_fields() -> None:
    class ExtraManifestFieldProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            manifest = json.loads(base64.b64decode(valid_result.render_manifest.content_base64).decode("utf-8"))
            manifest["provider"]["unreviewedProviderField"] = "not allowed"
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=valid_result.demo_export,
                render_manifest=artifact_from_text(
                    file_name=valid_result.render_manifest.file_name,
                    mime_type=valid_result.render_manifest.mime_type,
                    text=json.dumps(manifest, sort_keys=True),
                ),
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, ExtraManifestFieldProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            source_run_id="run_stage7",
            trace_id="trace_stage7",
            source_context_ref_count=1,
            source_citation_count=1,
            evaluation_status="PASSED",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_video_placeholder_rejects_unexpected_provider_metadata_fields() -> None:
    class ExtraPlaceholderFieldProvider:
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            placeholder = json.loads(
                base64.b64decode(valid_result.video_export_placeholder.content_base64).decode("utf-8")
            )
            placeholder["source"]["unreviewedSourceField"] = "not allowed"
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=valid_result.demo_export,
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=artifact_from_text(
                    file_name=valid_result.video_export_placeholder.file_name,
                    mime_type=valid_result.video_export_placeholder.mime_type,
                    text=json.dumps(placeholder, sort_keys=True),
                ),
            )

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, ExtraPlaceholderFieldProvider())

    with pytest.raises(Stage7Error) as exc:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            source_run_id="run_stage7",
            trace_id="trace_stage7",
            source_context_ref_count=1,
            source_citation_count=1,
            evaluation_status="PASSED",
            consent_to_use_synthetic_avatar=True,
        )

    assert exc.value.status_code == 422
    assert exc.value.code == "PROVIDER_OUTPUT_INVALID"


def test_unexpected_provider_exception_uses_mock_fallback() -> None:
    class ExplodingProvider:
        provider = "exploding-local"
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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            del (
                source_script,
                requested_provider,
                fallback_reason,
                source_run_id,
                trace_id,
                source_context_ref_count,
                source_citation_count,
                evaluation_status,
            )
            raise RuntimeError("provider timeout")

    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, ExplodingProvider())

    result = service.render_avatar_demo(
        source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
        requested_avatar_provider="mock",
        consent_to_use_synthetic_avatar=True,
    )

    assert result.avatar_provider.provider == "mock"
    assert result.avatar_provider.fallback_reason == "PROVIDER_RENDER_FAILED"
    assert [event.status for event in result.render_job_status_history] == [
        "QUEUED",
        "RUNNING",
        "FAILED",
        "FALLBACK",
        "COMPLETED",
    ]


def test_concurrent_duplicate_avatar_idempotency_key_is_rejected_in_flight() -> None:
    class SlowAvatarProvider:
        provider = "slow-local"
        provider_mode = "LOCAL"

        def __init__(self) -> None:
            self.entered = threading.Event()
            self.release = threading.Event()
            self.call_count = 0
            self.lock = threading.Lock()

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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            with self.lock:
                self.call_count += 1
            self.entered.set()
            assert self.release.wait(timeout=2)
            return create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )

    provider = SlowAvatarProvider()
    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, provider)
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()

    def render() -> None:
        try:
            result = service.render_avatar_demo(
                source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
                consent_to_use_synthetic_avatar=True,
                idempotency_scope="tenant:user:project:run",
                idempotency_key="same-key",
            )
            value = result.avatar_render_id
        except Stage7Error as exc:
            value = exc.code
        with outcomes_lock:
            outcomes.append(value)

    first = threading.Thread(target=render)
    second = threading.Thread(target=render)
    first.start()
    assert provider.entered.wait(timeout=2)
    second.start()
    second.join(timeout=2)
    provider.release.set()
    first.join(timeout=2)

    assert sorted(outcomes) == ["IDEMPOTENCY_IN_PROGRESS", "avrun_000001"]
    assert provider.call_count == 1


def test_failed_avatar_idempotency_key_replays_terminal_failure_without_retry() -> None:
    class InvalidHtmlProvider:
        provider = "mock"
        provider_mode = "LOCAL"

        def __init__(self) -> None:
            self.call_count = 0

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
            evaluation_status: str,
            **_extra: object,
        ) -> AvatarProviderResult:
            self.call_count += 1
            valid_result = create_stage7_service().avatar_provider.render(
                source_script=source_script,
                requested_provider=requested_provider,
                fallback_reason=fallback_reason,
                source_run_id=source_run_id,
                trace_id=trace_id,
                source_context_ref_count=source_context_ref_count,
                source_citation_count=source_citation_count,
                evaluation_status=evaluation_status,
            )
            return AvatarProviderResult(
                provider=valid_result.provider,
                provider_mode=valid_result.provider_mode,
                requested_provider=valid_result.requested_provider,
                fallback_reason=valid_result.fallback_reason,
                provider_config=valid_result.provider_config,
                demo_export=artifact_from_text(
                    file_name=valid_result.demo_export.file_name,
                    mime_type=valid_result.demo_export.mime_type,
                    text="<html><body><script>alert('x')</script></body></html>",
                ),
                render_manifest=valid_result.render_manifest,
                video_export_placeholder=valid_result.video_export_placeholder,
            )

    provider = InvalidHtmlProvider()
    service = create_stage7_service()
    service.avatar_provider = cast(AvatarProvider, provider)

    with pytest.raises(Stage7Error) as first:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="failed-key",
        )
    with pytest.raises(Stage7Error) as second:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=True,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="failed-key",
        )

    assert first.value.code == "PROVIDER_OUTPUT_INVALID"
    assert second.value.code == "PROVIDER_OUTPUT_INVALID"
    assert provider.call_count == 1


def test_avatar_consent_failure_idempotency_key_replays_terminal_failure() -> None:
    service = create_stage7_service()

    with pytest.raises(Stage7Error) as first:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=False,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="consent-failed-key",
        )
    with pytest.raises(Stage7Error) as second:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            consent_to_use_synthetic_avatar=False,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="consent-failed-key",
        )

    assert first.value.code == "AVATAR_CONSENT_REQUIRED"
    assert second.value.code == "AVATAR_CONSENT_REQUIRED"


def test_avatar_validation_failure_idempotency_key_conflicts_on_changed_request() -> None:
    service = create_stage7_service()

    with pytest.raises(Stage7Error) as first:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            cloned_identity_requested=True,
            consent_to_use_synthetic_avatar=True,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="clone-failed-key",
        )
    with pytest.raises(Stage7Error) as second:
        service.render_avatar_demo(
            source_script="NarraTwin AI creates grounded walkthrough scripts. [1]",
            requested_avatar_provider="mock",
            cloned_identity_requested=False,
            consent_to_use_synthetic_avatar=True,
            idempotency_scope="tenant:user:project:run",
            idempotency_key="clone-failed-key",
        )

    assert first.value.code == "CLONED_IDENTITY_DISABLED"
    assert second.value.code == "IDEMPOTENCY_CONFLICT"
