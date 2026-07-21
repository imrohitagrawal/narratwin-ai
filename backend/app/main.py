"""FastAPI application for NarraTwin AI local stages."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import os
import re
import time
from datetime import UTC, datetime
from threading import Lock
from typing import Annotated, Literal, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, File, Header, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.app.rag.models import OWNER_LOCAL
from backend.app.observability import is_langfuse_enabled
from backend.app.stage4 import (
    MAX_API_REQUEST_BYTES,
    LocalPrincipal,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_REQUEST_BYTES,
    Stage4Error,
    WalkthroughRunRecord,
    document_to_api,
    ingestion_to_api,
    project_to_api,
    stage4_service,
    walkthrough_to_api,
)
from backend.app.stage6 import (
    MAX_GLOSSARY_TERM_CHARS,
    MAX_GLOSSARY_TERMS,
    MAX_PROVIDER_ID_CHARS,
    Stage6Error,
    multilingual_to_api,
    stage6_service,
)
from backend.app.stage7 import (
    MAX_PROVIDER_ID_CHARS as MAX_AVATAR_PROVIDER_ID_CHARS,
    DurableAvatarRenderScope,
    SYNTHETIC_AVATAR_CONSENT_VERSION,
    Stage7MultilingualBundle,
    Stage7Error,
    avatar_consent_to_api,
    avatar_render_to_api,
    build_source_evaluation_checksum,
    stage7_service,
)
from backend.app.hosted_demo import (
    HostedDemoAccessRequest,
    HostedDemoDecision,
    HostedDemoError,
    HostedDemoJsonError,
    hosted_demo_service,
    parse_hosted_demo_json,
)

ErrorDetailValue = str | int | float | bool


@dataclass(frozen=True)
class Stage7RenderableSource:
    source_run: WalkthroughRunRecord
    source_context_ref_ids: tuple[str, ...]
    source_citation_indexes: tuple[int, ...]
    source_evaluation_checksum: str


class HealthResponse(BaseModel):
    """Stable health response shape used by CI smoke checks."""

    model_config = ConfigDict(frozen=True)

    status: Literal["ok"]
    service: Literal["narratwin-ai-backend"]
    stage: Literal["8"]


class ReadinessResponse(HealthResponse):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    checked_at: str = Field(alias="checkedAt")


class Stage4OpsRecordCountsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    projects: int
    documents: int
    ingestion_runs: int = Field(alias="ingestionRuns")
    walkthrough_runs: int = Field(alias="walkthroughRuns")
    idempotency_records: int = Field(alias="idempotencyRecords")


class Stage6OpsRecordCountsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    idempotency_records: int = Field(alias="idempotencyRecords")


class Stage7OpsRecordCountsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    avatar_renders: int = Field(alias="avatarRenders")
    artifact_metadata: int = Field(alias="artifactMetadata")
    idempotency_records: int = Field(alias="idempotencyRecords")


class OpsStage4DurabilityResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    durable_state_enabled: bool = Field(alias="durableStateEnabled")
    state_backend: Literal["memory", "json-file"] = Field(alias="stateBackend")
    record_counts: Stage4OpsRecordCountsResponse = Field(alias="recordCounts")


class OpsStage6DurabilityResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    durable_state_enabled: bool = Field(alias="durableStateEnabled")
    state_backend: Literal["memory", "json-file"] = Field(alias="stateBackend")
    record_counts: Stage6OpsRecordCountsResponse = Field(alias="recordCounts")


class OpsStage7DurabilityResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    durable_state_enabled: bool = Field(alias="durableStateEnabled")
    state_backend: Literal["memory", "json-file"] = Field(alias="stateBackend")
    record_counts: Stage7OpsRecordCountsResponse = Field(alias="recordCounts")


class OpsDurabilityResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    stage4: OpsStage4DurabilityResponse
    stage6: OpsStage6DurabilityResponse
    stage7: OpsStage7DurabilityResponse


class OpsMonitoringResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    health_endpoint: bool = Field(alias="healthEndpoint")
    readiness_endpoint: bool = Field(alias="readinessEndpoint")
    ops_status_endpoint: bool = Field(alias="opsStatusEndpoint")
    structured_logging_configured: bool = Field(alias="structuredLoggingConfigured")
    walkthrough_metrics_instrumented: bool = Field(alias="walkthroughMetricsInstrumented")
    metrics_endpoint_exposed: bool = Field(alias="metricsEndpointExposed")
    production_alerts_configured: bool = Field(alias="productionAlertsConfigured")
    langfuse_configured: bool = Field(alias="langfuseConfigured")


class OpsStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    status: Literal["ok"]
    service: Literal["narratwin-ai-backend"]
    stage: Literal["8"]
    checked_at: str = Field(alias="checkedAt")
    operational_posture: Literal["LOCAL_ONLY"] = Field(alias="operationalPosture")
    durability: OpsDurabilityResponse
    monitoring: OpsMonitoringResponse


class ErrorBody(BaseModel):
    """API error detail shape from the locked contract."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    code: str
    message: str
    details: dict[str, ErrorDetailValue] = Field(default_factory=dict)
    request_id: str = Field(alias="requestId")


class ErrorResponse(BaseModel):
    """Locked error envelope for future /api/v1 endpoints."""

    model_config = ConfigDict(frozen=True)

    error: ErrorBody


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    name: str
    description: str = ""
    default_audience: str = Field(default="RECRUITER", alias="defaultAudience")
    default_language: str = Field(default="en", alias="defaultLanguage")


class ApproveDocumentRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    approval_status: Literal["APPROVED"] = Field(alias="approvalStatus")
    review_note: str = Field(default="", alias="reviewNote")


class StartIngestionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    document_ids: list[str] = Field(alias="documentIds")


class GenerateWalkthroughRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    audience: Literal["RECRUITER", "HIRING_MANAGER", "ENGINEER", "PRODUCT_LEADER", "BEGINNER", "GLOBAL_VIEWER"] = "RECRUITER"
    requested_language: Literal["en"] = Field(default="en", alias="requestedLanguage")
    depth: Literal["CONCISE", "STANDARD", "DEEP"] = "CONCISE"
    style: Literal["PLAIN", "CONFIDENT", "TECHNICAL", "EXECUTIVE"] = "CONFIDENT"
    prompt: str = "Create a concise grounded walkthrough."


class GenerateMultilingualWalkthroughRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    target_language: str = Field(
        alias="targetLanguage",
        min_length=2,
        max_length=16,
        pattern=r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*$",
    )
    glossary_terms: list[Annotated[str, Field(min_length=1, max_length=MAX_GLOSSARY_TERM_CHARS)]] = Field(
        default_factory=list,
        alias="glossaryTerms",
        max_length=MAX_GLOSSARY_TERMS,
    )
    requested_voice_provider: str = Field(
        default="mock",
        alias="requestedVoiceProvider",
        min_length=1,
        max_length=MAX_PROVIDER_ID_CHARS,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$",
    )

    @field_validator("glossary_terms")
    @classmethod
    def normalize_glossary_terms(cls, terms: list[str]) -> list[str]:
        normalized: list[str] = []
        for term in terms:
            candidate = " ".join(term.strip().split())
            if not candidate:
                raise ValueError("Glossary terms must not be blank.")
            normalized.append(candidate)
        return normalized


class GenerateAvatarRenderRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    requested_avatar_provider: str = Field(
        default="mock",
        alias="requestedAvatarProvider",
        min_length=1,
        max_length=MAX_AVATAR_PROVIDER_ID_CHARS,
        pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$",
    )
    consent_to_use_synthetic_avatar: bool = Field(alias="consentToUseSyntheticAvatar")
    consent_record_id: str = Field(alias="consentRecordId", min_length=1, max_length=128)
    cloned_identity_requested: bool = Field(default=False, alias="clonedIdentityRequested")
    multilingual_bundle: "Stage7MultilingualBundleRequest | None" = Field(default=None, alias="multilingualBundle")


class Stage7ProviderPostureRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    translation_provider: str = Field(alias="translationProvider", min_length=1, max_length=MAX_PROVIDER_ID_CHARS)
    translation_provider_mode: Literal["LOCAL"] = Field(alias="translationProviderMode")
    voice_provider: str = Field(alias="voiceProvider", min_length=1, max_length=MAX_PROVIDER_ID_CHARS)
    voice_provider_mode: Literal["LOCAL"] = Field(alias="voiceProviderMode")


class Stage7MultilingualBundleRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    source_run_id: str = Field(alias="sourceRunId", min_length=1, max_length=128)
    multilingual_run_id: str = Field(alias="multilingualRunId", min_length=1, max_length=128)
    target_language: str = Field(alias="targetLanguage", min_length=2, max_length=16)
    translated_script_checksum: str = Field(alias="translatedScriptChecksum", min_length=8, max_length=128)
    subtitles_checksum: str = Field(alias="subtitlesChecksum", min_length=8, max_length=128)
    voice_manifest_checksum: str = Field(alias="voiceManifestChecksum", min_length=8, max_length=128)
    context_ref_ids: list[str] = Field(alias="contextRefIds", min_length=1)
    citation_indexes: list[int] = Field(alias="citationIndexes", min_length=1)
    evaluation_id: str = Field(alias="evaluationId", min_length=1, max_length=128)
    evaluation_checksum: str = Field(alias="evaluationChecksum", min_length=8, max_length=128)
    provider_posture: Stage7ProviderPostureRequest = Field(alias="providerPosture")
    consent_disclosure_version: str = Field(alias="consentDisclosureVersion", min_length=1, max_length=128)


class CaptureAvatarConsentRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    consent_to_use_synthetic_avatar: bool = Field(alias="consentToUseSyntheticAvatar")


def resolve_stage7_renderable_source(
    project_id: str,
    run_id: str,
    principal: LocalPrincipal,
) -> Stage7RenderableSource:
    project = stage4_service.projects.get(project_id)
    if project is None:
        raise Stage7Error(404, "NOT_FOUND", "Project not found.")
    if project.tenant_id != principal.tenant_id or project.owner_id != principal.actor_id:
        raise Stage7Error(403, "FORBIDDEN", "Project is not accessible to this principal.")
    source_run = stage4_service.walkthrough_runs.get(run_id)
    if source_run is None or source_run.project_id != project_id:
        raise Stage7Error(404, "NOT_FOUND", "Walkthrough run not found.")
    if source_run.tenant_id != principal.tenant_id or source_run.actor_id != principal.actor_id:
        raise Stage7Error(403, "FORBIDDEN", "Walkthrough run is not accessible to this principal.")
    if source_run.status != "COMPLETED" or not source_run.accepted_script_text:
        raise Stage7Error(422, "SOURCE_RUN_NOT_RENDERABLE", "Only completed grounded walkthrough runs can be rendered.")
    if source_run.evaluation_status != "PASSED":
        raise Stage7Error(422, "SOURCE_RUN_NOT_RENDERABLE", "Only passed grounded walkthrough runs can be rendered.")
    if source_run.evaluation is None or not source_run.evaluation.claim_supports or not source_run.retrieved_context:
        raise Stage7Error(
            422,
            "SOURCE_RUN_NOT_RENDERABLE",
            "Avatar rendering requires grounded evaluation evidence.",
        )

    source_context_ref_ids = tuple(context.context_ref_id for context in source_run.retrieved_context)
    source_citation_indexes = tuple(support.citation_index for support in source_run.evaluation.claim_supports)
    return Stage7RenderableSource(
        source_run=source_run,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_evaluation_checksum=build_source_evaluation_checksum(
            source_evaluation_id=source_run.evaluation.evaluation_id,
            source_run_id=source_run.run_id,
            trace_id=source_run.trace_id,
            evaluation_status=source_run.evaluation_status or "UNKNOWN",
            source_context_ref_ids=source_context_ref_ids,
            source_context_ref_count=len(source_run.retrieved_context),
            source_citation_indexes=source_citation_indexes,
            source_citation_count=len(source_run.evaluation.claim_supports),
        ),
    )


def validate_stage7_multilingual_bundle(
    request_bundle: Stage7MultilingualBundleRequest | None,
    *,
    project_id: str,
    run_id: str,
    principal: LocalPrincipal,
    renderable: Stage7RenderableSource,
) -> Stage7MultilingualBundle:
    if request_bundle is None:
        raise Stage7Error(
            422,
            "MULTILINGUAL_BUNDLE_REQUIRED",
            "Stage 7 Mode 1 avatar rendering requires validated Stage 6 multilingual bundle evidence.",
        )
    multilingual_run = stage6_service.multilingual_runs.get(request_bundle.multilingual_run_id)
    if multilingual_run is None:
        raise Stage7Error(422, "MULTILINGUAL_BUNDLE_INVALID", "Stage 6 multilingual bundle was not found.")
    expected_provider_posture = {
        "translationProvider": multilingual_run.translation_provider.provider,
        "translationProviderMode": multilingual_run.translation_provider.provider_mode,
        "voiceProvider": multilingual_run.voice.provider,
        "voiceProviderMode": multilingual_run.voice.provider_mode,
    }
    actual_provider_posture = {
        "translationProvider": request_bundle.provider_posture.translation_provider,
        "translationProviderMode": request_bundle.provider_posture.translation_provider_mode,
        "voiceProvider": request_bundle.provider_posture.voice_provider,
        "voiceProviderMode": request_bundle.provider_posture.voice_provider_mode,
    }
    bundle_matches = (
        multilingual_run.tenant_id == principal.tenant_id
        and multilingual_run.project_id == project_id
        and multilingual_run.actor_id == principal.actor_id
        and multilingual_run.source_run_id == run_id
        and request_bundle.source_run_id == run_id
        and request_bundle.target_language == multilingual_run.target_language
        and request_bundle.translated_script_checksum == multilingual_run.artifacts.translated_script.checksum
        and request_bundle.subtitles_checksum == multilingual_run.artifacts.subtitles.checksum
        and request_bundle.voice_manifest_checksum == multilingual_run.artifacts.voice_manifest.checksum
        and tuple(request_bundle.context_ref_ids) == renderable.source_context_ref_ids
        and tuple(request_bundle.citation_indexes) == renderable.source_citation_indexes
        and request_bundle.evaluation_id == multilingual_run.source_evaluation_id
        and request_bundle.evaluation_checksum == multilingual_run.source_evaluation_checksum
        and request_bundle.evaluation_checksum == renderable.source_evaluation_checksum
        and multilingual_run.evaluation_status == "PASSED"
        and actual_provider_posture == expected_provider_posture
        and request_bundle.consent_disclosure_version == SYNTHETIC_AVATAR_CONSENT_VERSION
    )
    if not bundle_matches:
        raise Stage7Error(
            422,
            "MULTILINGUAL_BUNDLE_INVALID",
            "Stage 7 multilingual bundle evidence does not match the stored Stage 6 run.",
        )
    return Stage7MultilingualBundle(
        source_run_id=request_bundle.source_run_id,
        multilingual_run_id=request_bundle.multilingual_run_id,
        target_language=request_bundle.target_language,
        translated_script_checksum=request_bundle.translated_script_checksum,
        subtitles_checksum=request_bundle.subtitles_checksum,
        voice_manifest_checksum=request_bundle.voice_manifest_checksum,
        context_ref_ids=tuple(request_bundle.context_ref_ids),
        citation_indexes=tuple(request_bundle.citation_indexes),
        evaluation_id=request_bundle.evaluation_id,
        evaluation_checksum=request_bundle.evaluation_checksum,
        provider_posture=expected_provider_posture,
        consent_disclosure_version=request_bundle.consent_disclosure_version,
    )


class ProjectResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    project_id: str = Field(alias="projectId")
    tenant_id: str = Field(alias="tenantId")
    owner_id: str = Field(alias="ownerId")
    name: str
    description: str
    project_status: Literal["ACTIVE"] = Field(alias="projectStatus")
    default_audience: str = Field(alias="defaultAudience")
    default_language: str = Field(alias="defaultLanguage")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")


class DocumentResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    document_id: str = Field(alias="documentId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    source_filename: str = Field(alias="sourceFilename")
    content_type: str = Field(alias="contentType")
    size_bytes: int = Field(alias="sizeBytes")
    checksum: str
    document_status: Literal["STORED"] = Field(alias="documentStatus")
    approval_status: Literal["PENDING", "APPROVED"] = Field(alias="approvalStatus")
    ingestion_status: Literal["NOT_STARTED", "INGESTED"] = Field(alias="ingestionStatus")
    created_at: str = Field(alias="createdAt")
    approved_at: str | None = Field(default=None, alias="approvedAt")


class IngestionRunResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    ingestion_run_id: str = Field(alias="ingestionRunId")
    tenant_id: str = Field(alias="tenantId")
    actor_id: str = Field(alias="actorId")
    project_id: str = Field(alias="projectId")
    status: Literal["COMPLETED"]
    document_ids: list[str] = Field(alias="documentIds")
    chunk_count: int = Field(alias="chunkCount")
    embedding_count: int = Field(alias="embeddingCount")
    created_at: str = Field(alias="createdAt")


class EvidenceSnapshotResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    evidence_snapshot_id: str = Field(alias="evidenceSnapshotId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    document_id: str = Field(alias="documentId")
    chunk_id: str = Field(alias="chunkId")
    source_filename: str = Field(alias="sourceFilename")
    chunk_index: int = Field(alias="chunkIndex")
    source_document_checksum: str = Field(alias="sourceDocumentChecksum")
    chunk_checksum: str = Field(alias="chunkChecksum")
    chunking_strategy_version: str = Field(alias="chunkingStrategyVersion")
    retrieval_score: float = Field(alias="retrievalScore")
    redacted_excerpt: str = Field(alias="redactedExcerpt")
    excerpt_start: int = Field(alias="excerptStart")
    excerpt_end: int = Field(alias="excerptEnd")
    redaction_flags: list[str] = Field(alias="redactionFlags")
    captured_at: str = Field(alias="capturedAt")
    snapshot_checksum: str = Field(alias="snapshotChecksum")


class ContextRefResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    context_ref_id: str = Field(alias="contextRefId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    claim_id: str = Field(alias="claimId")
    chunk_id: str = Field(alias="chunkId")
    document_id: str = Field(alias="documentId")
    source_filename: str = Field(alias="sourceFilename")
    chunk_index: int = Field(alias="chunkIndex")
    checksum: str
    script_span_start: int = Field(alias="scriptSpanStart")
    script_span_end: int = Field(alias="scriptSpanEnd")
    evidence_snapshot: EvidenceSnapshotResponse = Field(alias="evidenceSnapshot")


class UnsupportedClaimResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_id: str = Field(alias="claimId")
    claim_text: str = Field(alias="claimText")
    reason: str


class ClaimSupportResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_support_id: str = Field(alias="claimSupportId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    run_id: str = Field(alias="runId")
    evaluation_id: str = Field(alias="evaluationId")
    claim_id: str = Field(alias="claimId")
    context_ref_id: str = Field(alias="contextRefId")
    chunk_id: str = Field(alias="chunkId")
    document_id: str = Field(alias="documentId")
    support_status: Literal["SUPPORTED"] = Field(alias="supportStatus")
    support_score: float = Field(alias="supportScore")
    support_reason: str = Field(alias="supportReason")
    evidence_snapshot: EvidenceSnapshotResponse = Field(alias="evidenceSnapshot")
    citation_index: int = Field(alias="citationIndex")


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_name: Literal["EvaluationSummary"] = Field(alias="schema")
    evaluation_id: str = Field(alias="evaluationId")
    evaluation_status: Literal["PASSED", "FAILED"] = Field(alias="evaluationStatus")
    groundedness_score: float = Field(alias="groundednessScore")
    faithfulness: float = Field(alias="faithfulness")
    answer_relevancy: float = Field(alias="answerRelevancy")
    context_precision: float = Field(alias="contextPrecision")
    context_recall: float = Field(alias="contextRecall")
    unsupported_claim_count: int = Field(alias="unsupportedClaimCount")
    unsupported_claims: list[UnsupportedClaimResponse] = Field(alias="unsupportedClaims")
    claim_supports: list[ClaimSupportResponse] = Field(alias="claimSupports")
    context_ref_coverage: float = Field(alias="contextRefCoverage")
    embedding_provider: str = Field(alias="embeddingProvider")
    embedding_model: str = Field(alias="embeddingModel")
    embedding_model_version: str = Field(alias="embeddingModelVersion")
    embedding_dimension: int = Field(alias="embeddingDimension")
    vector_store: str = Field(alias="vectorStore")
    retrieval_strategy_version: str = Field(alias="retrievalStrategyVersion")
    retrieval_top_k: int = Field(alias="retrievalTopK")
    retrieval_score_threshold: float = Field(alias="retrievalScoreThreshold")
    policy_version: str = Field(alias="policyVersion")
    schema_version: str = Field(alias="schemaVersion")
    safety_policy_version: str = Field(alias="safetyPolicyVersion")
    context_refs: list[ContextRefResponse] = Field(alias="contextRefs")


class ProviderResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: Literal["mock"]
    provider_mode: Literal["LOCAL"] = Field(alias="providerMode")


class TraceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    trace_id: str = Field(alias="traceId")
    latency_ms: int = Field(alias="latencyMs")
    input_tokens: int = Field(default=0, alias="inputTokens")
    output_tokens: int = Field(default=0, alias="outputTokens")
    estimated_cost: float = Field(alias="estimatedCost")


class FailureResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    reason_code: str = Field(alias="reasonCode")
    message: str
    unsupported_claim_count: int = Field(alias="unsupportedClaimCount")


class WalkthroughRunResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    run_id: str = Field(alias="runId")
    tenant_id: str = Field(alias="tenantId")
    actor_id: str = Field(alias="actorId")
    project_id: str = Field(alias="projectId")
    status: Literal["COMPLETED", "FAILED", "REFUSED"]
    evaluation_status: Literal["PASSED", "FAILED"] | None = Field(alias="evaluationStatus")
    audience: str
    requested_language: str = Field(alias="requestedLanguage")
    depth: str
    style: str
    context_refs: list[ContextRefResponse] = Field(alias="contextRefs")
    provider: ProviderResponse
    trace: TraceResponse
    created_at: str = Field(alias="createdAt")
    accepted_script_text: str | None = Field(default=None, alias="acceptedScriptText")
    evaluation: EvaluationResponse | None = None
    failure: FailureResponse | None = None
    redacted_unsupported_excerpts: list[str] = Field(default_factory=list, alias="redactedUnsupportedExcerpts")


class DownloadableArtifactResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    content_base64: str = Field(alias="contentBase64")
    checksum: str


class TranslationProviderResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: str = Field(min_length=1, max_length=MAX_PROVIDER_ID_CHARS, pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    provider_mode: Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"] = Field(alias="providerMode")


class VoiceProviderResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: str = Field(min_length=1, max_length=MAX_PROVIDER_ID_CHARS, pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    provider_mode: Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"] = Field(alias="providerMode")
    requested_provider: str = Field(
        alias="requestedProvider",
        min_length=1,
        max_length=MAX_PROVIDER_ID_CHARS,
        pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$",
    )
    fallback_reason: str | None = Field(default=None, alias="fallbackReason")
    language: str
    artifact: DownloadableArtifactResponse


class MultilingualArtifactsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    translated_script: DownloadableArtifactResponse = Field(alias="translatedScript")
    subtitles: DownloadableArtifactResponse
    voice_manifest: DownloadableArtifactResponse = Field(alias="voiceManifest")
    voice_audio: DownloadableArtifactResponse | None = Field(default=None, alias="voiceAudio")
    metadata: DownloadableArtifactResponse


class MultilingualTraceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    trace_id: str = Field(alias="traceId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    actor_id: str = Field(alias="actorId")
    source_run_id: str = Field(alias="sourceRunId")
    source_language: str = Field(alias="sourceLanguage")
    target_language: str = Field(alias="targetLanguage")
    source_text_checksum: str = Field(alias="sourceTextChecksum")
    source_context_ref_count: int = Field(alias="sourceContextRefCount")
    source_citation_count: int = Field(alias="sourceCitationCount")
    source_context_ref_ids: list[str] = Field(alias="sourceContextRefIds")
    source_citation_indexes: list[int] = Field(alias="sourceCitationIndexes")
    source_claim_support_ids: list[str] = Field(alias="sourceClaimSupportIds")
    source_evaluation_id: str = Field(alias="sourceEvaluationId")
    source_evaluation_checksum: str = Field(alias="sourceEvaluationChecksum")
    evaluation_status: Literal["PASSED", "FAILED", "UNKNOWN"] = Field(alias="evaluationStatus")


class MultilingualWalkthroughResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    multilingual_run_id: str = Field(alias="multilingualRunId")
    source_run_id: str = Field(alias="sourceRunId")
    source_language: str = Field(alias="sourceLanguage")
    target_language: str = Field(alias="targetLanguage")
    status: Literal["COMPLETED"]
    source_script_text: str = Field(alias="sourceScriptText")
    translated_script_text: str = Field(alias="translatedScriptText")
    subtitles_text: str = Field(alias="subtitlesText")
    glossary_terms: list[str] = Field(alias="glossaryTerms")
    preserved_terms: list[str] = Field(alias="preservedTerms")
    translation_provider: TranslationProviderResponse = Field(alias="translationProvider")
    voice: VoiceProviderResponse
    artifacts: MultilingualArtifactsResponse
    trace: MultilingualTraceResponse


class AvatarProviderRenderResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: str = Field(
        min_length=1,
        max_length=MAX_AVATAR_PROVIDER_ID_CHARS,
        pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$",
    )
    provider_mode: Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"] = Field(alias="providerMode")
    requested_provider: str = Field(
        alias="requestedProvider",
        min_length=1,
        max_length=MAX_AVATAR_PROVIDER_ID_CHARS,
        pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$",
    )
    fallback_reason: str | None = Field(default=None, alias="fallbackReason")


class ProviderConfigResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: str = Field(
        min_length=1,
        max_length=MAX_AVATAR_PROVIDER_ID_CHARS,
        pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$",
    )
    provider_mode: Literal["LOCAL", "DISABLED", "OPTIONAL_EXTERNAL"] = Field(alias="providerMode")
    adapter_kind: Literal["MOCK_LOCAL", "EXTERNAL_STUB"] = Field(alias="adapterKind")
    allow_network_egress: bool = Field(alias="allowNetworkEgress")
    requires_api_key: bool = Field(alias="requiresApiKey")
    supports_real_video: bool = Field(alias="supportsRealVideo")
    supports_cloned_identity: bool = Field(alias="supportsClonedIdentity")


class AvatarVideoProviderBoundaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    provider: str = Field(min_length=1, max_length=MAX_AVATAR_PROVIDER_ID_CHARS)
    provider_mode: Literal["DISABLED", "OPTIONAL_EXTERNAL"] = Field(alias="providerMode")
    enabled: bool
    allow_network_egress: bool = Field(alias="allowNetworkEgress")
    requires_api_key: bool = Field(alias="requiresApiKey")
    supports_real_video: bool = Field(alias="supportsRealVideo")
    supports_cloned_identity: bool = Field(alias="supportsClonedIdentity")
    asset_provenance_policy: Literal["fully_synthetic_or_provider_stock_non_identifiable_only"] = Field(
        alias="assetProvenancePolicy"
    )
    disclosure_text: str = Field(alias="disclosureText")
    disclosure_version: str = Field(alias="disclosureVersion")
    retention_state: Literal["NOT_CREATED", "ACTIVE", "DELETED"] = Field(alias="retentionState")
    deletion_state: Literal["NOT_REQUESTED", "PENDING", "DELETED", "FAILED"] = Field(alias="deletionState")


class RenderJobStatusEventResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    status: Literal["QUEUED", "RUNNING", "FAILED", "FALLBACK", "COMPLETED"]
    message: str


class VideoRendererResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    renderer: Literal["local-html"]
    renderer_mode: Literal["LOCAL"] = Field(alias="rendererMode")
    export_format: Literal["html"] = Field(alias="exportFormat")


class AvatarDisclosureResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    ai_generated: bool = Field(alias="aiGenerated")
    cloned_identity: bool = Field(alias="clonedIdentity")
    consent_required: bool = Field(alias="consentRequired")
    consent_status: Literal["CONFIRMED", "NOT_REQUIRED"] = Field(alias="consentStatus")
    message: str


class AvatarArtifactsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    demo_export: DownloadableArtifactResponse = Field(alias="demoExport")
    render_manifest: DownloadableArtifactResponse = Field(alias="renderManifest")
    video_export_placeholder: DownloadableArtifactResponse = Field(alias="videoExportPlaceholder")


class AvatarTraceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    trace_id: str = Field(alias="traceId")
    source_context_ref_count: int = Field(alias="sourceContextRefCount")
    source_citation_count: int = Field(alias="sourceCitationCount")
    source_context_ref_ids: list[str] = Field(alias="sourceContextRefIds")
    source_citation_indexes: list[int] = Field(alias="sourceCitationIndexes")
    source_evaluation_id: str = Field(alias="sourceEvaluationId")
    source_evaluation_checksum: str = Field(alias="sourceEvaluationChecksum")
    evaluation_status: Literal["PASSED", "FAILED", "UNKNOWN"] = Field(alias="evaluationStatus")
    multilingual_run_id: str | None = Field(default=None, alias="multilingualRunId")
    target_language: str | None = Field(default=None, alias="targetLanguage")
    translated_script_checksum: str | None = Field(default=None, alias="translatedScriptChecksum")
    subtitles_checksum: str | None = Field(default=None, alias="subtitlesChecksum")
    voice_manifest_checksum: str | None = Field(default=None, alias="voiceManifestChecksum")


class AvatarRenderResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    avatar_render_id: str = Field(alias="avatarRenderId")
    consent_record_id: str | None = Field(default=None, alias="consentRecordId")
    source_run_id: str = Field(alias="sourceRunId")
    status: Literal["COMPLETED"]
    render_job_status: Literal["COMPLETED"] = Field(alias="renderJobStatus")
    render_job_status_history: list[RenderJobStatusEventResponse] = Field(alias="renderJobStatusHistory")
    source_script_text: str = Field(alias="sourceScriptText")
    avatar_provider: AvatarProviderRenderResponse = Field(alias="avatarProvider")
    provider_config: ProviderConfigResponse = Field(alias="providerConfig")
    avatar_video_provider: AvatarVideoProviderBoundaryResponse = Field(alias="avatarVideoProvider")
    video_renderer: VideoRendererResponse = Field(alias="videoRenderer")
    disclosure: AvatarDisclosureResponse
    artifacts: AvatarArtifactsResponse
    trace: AvatarTraceResponse


class AvatarConsentResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    consent_record_id: str = Field(alias="consentRecordId")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    actor_id: str = Field(alias="actorId")
    source_run_id: str = Field(alias="sourceRunId")
    trace_id: str = Field(alias="traceId")
    source_context_ref_ids: list[str] = Field(alias="sourceContextRefIds")
    source_citation_indexes: list[int] = Field(alias="sourceCitationIndexes")
    source_evaluation_id: str = Field(alias="sourceEvaluationId")
    source_evaluation_checksum: str = Field(alias="sourceEvaluationChecksum")
    evaluation_status: Literal["PASSED", "FAILED", "UNKNOWN"] = Field(alias="evaluationStatus")
    consent_statement_version: str = Field(alias="consentStatementVersion")
    consent_statement_text: str = Field(alias="consentStatementText")
    granted_at: str = Field(alias="grantedAt")
    request_checksum: str = Field(alias="requestChecksum")
    avatar_render_id: str | None = Field(default=None, alias="avatarRenderId")
    artifact_checksums: list[str] = Field(alias="artifactChecksums")


def normalize_local_user_id_header(value: str | None, *, app_env: str | None = None) -> str:
    candidate = (value or "").strip()
    if not candidate:
        return OWNER_LOCAL

    normalized_env = (app_env if app_env is not None else os.environ.get("APP_ENV", "local")).strip().lower() or "local"
    if normalized_env not in LOCAL_PRINCIPAL_SIMULATION_ENVS:
        raise Stage4Error(
            400,
            "LOCAL_PRINCIPAL_HEADER_NOT_ALLOWED",
            "X-Local-User-Id is only allowed in trusted local, dev, and test environments.",
        )
    if not LOCAL_USER_ID_PATTERN.fullmatch(candidate):
        raise Stage4Error(
            400,
            "VALIDATION_ERROR",
            "X-Local-User-Id must contain only ASCII letters, digits, underscore, or dash, with a maximum length of 64.",
        )
    return candidate


async def local_principal(x_local_user_id: str | None = Header(default=None, alias="X-Local-User-Id")) -> LocalPrincipal:
    return LocalPrincipal(actor_id=normalize_local_user_id_header(x_local_user_id))


async def idempotency_key_header(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> str:
    key = (idempotency_key or "").strip()
    if not key:
        raise Stage4Error(400, "IDEMPOTENCY_KEY_REQUIRED", "Idempotency-Key header is required for write requests.")
    return key


app = FastAPI(
    title="NarraTwin AI API",
    version="0.1.0",
    docs_url=None,
    openapi_url="/api/v1/openapi.json",
    redoc_url=None,
)
API_V1_HEALTH_PATH = "/api/v1/healthz"
API_V1_READY_PATH = "/api/v1/readyz"
API_V1_PROJECTS_PATH = "/api/v1/projects"
api_v1 = APIRouter(prefix="/api/v1")
FOUNDATION_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}
MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE = 120
STAGE8_RATE_LIMIT_WINDOW_SECONDS = 60.0
MAX_STAGE8_RATE_LIMIT_KEYS = 2_048
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
LOCAL_PRINCIPAL_SIMULATION_ENVS = {"local", "dev", "test"}
LOCAL_USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class Stage8BodyTooLarge(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class Stage8RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not stage8_write_scope(scope):
            await self.app(scope, receive, send)
            return

        request_id = request_id_from_scope(scope)
        request_limit = stage8_request_limit_for_scope(scope)
        content_length = content_length_from_scope(scope)
        if content_length is None:
            await send_stage8_error(
                scope,
                send,
                status_code=411,
                code="CONTENT_LENGTH_REQUIRED",
                message="Content-Length is required for Stage 8 local write request limits.",
                request_id=request_id,
            )
            return
        try:
            declared_bytes = int(content_length)
        except ValueError:
            await send_stage8_error(
                scope,
                send,
                status_code=400,
                code="INVALID_CONTENT_LENGTH",
                message="Content-Length must be a non-negative integer.",
                request_id=request_id,
            )
            return
        if declared_bytes < 0:
            await send_stage8_error(
                scope,
                send,
                status_code=400,
                code="INVALID_CONTENT_LENGTH",
                message="Content-Length must be a non-negative integer.",
                request_id=request_id,
            )
            return
        if declared_bytes > request_limit:
            await send_stage8_error(
                scope,
                send,
                status_code=413,
                code="UPLOAD_TOO_LARGE" if request_limit == MAX_UPLOAD_REQUEST_BYTES else "REQUEST_TOO_LARGE",
                message="Request exceeds the Stage 8 size limit.",
                request_id=request_id,
            )
            return

        rate_limit_key = rate_limit_key_from_scope(scope)
        if not stage8_write_rate_limiter.allow(key=rate_limit_key):
            await send_stage8_error(
                scope,
                send,
                status_code=429,
                code="RATE_LIMIT_EXCEEDED",
                message="Too many write requests. Retry after the Stage 8 local rate-limit window.",
                request_id=request_id,
            )
            return

        messages: list[Message] = []
        actual_bytes = 0
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] == "http.request":
                body = cast(bytes, message.get("body", b""))
                actual_bytes += len(body)
                if actual_bytes > request_limit:
                    exc = Stage8BodyTooLarge(
                        status_code=413,
                        code="UPLOAD_TOO_LARGE" if request_limit == MAX_UPLOAD_REQUEST_BYTES else "REQUEST_TOO_LARGE",
                        message="Request exceeds the Stage 8 size limit.",
                    )
                    await send_stage8_error(
                        scope,
                        send,
                        status_code=exc.status_code,
                        code=exc.code,
                        message=exc.message,
                        request_id=request_id,
                    )
                    return
                if not message.get("more_body", False):
                    break
            else:
                break

        replay_index = 0

        async def replay_receive() -> Message:
            nonlocal replay_index
            if replay_index < len(messages):
                message = messages[replay_index]
                replay_index += 1
                return message
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)


def stage8_write_scope(scope: Scope) -> bool:
    return (
        scope["type"] == "http"
        and scope.get("method") in WRITE_METHODS
        and str(scope.get("path", "")).startswith("/api/v1/")
    )


def stage8_request_limit_for_scope(scope: Scope) -> int:
    return (
        MAX_UPLOAD_REQUEST_BYTES
        if scope.get("method") == "POST" and str(scope.get("path", "")).endswith("/knowledge-documents")
        else MAX_API_REQUEST_BYTES
    )


def content_length_from_scope(scope: Scope) -> str | None:
    for name, value in headers_from_scope(scope):
        if name.lower() == b"content-length":
            return value.decode("ascii", errors="ignore")
    return None


def request_id_from_scope(scope: Scope) -> str:
    for name, value in headers_from_scope(scope):
        if name.lower() == b"x-request-id":
            decoded = value.decode("ascii", errors="ignore").strip()
            if decoded:
                return decoded
    return str(uuid4())


def headers_from_scope(scope: Scope) -> list[tuple[bytes, bytes]]:
    return cast(list[tuple[bytes, bytes]], scope.get("headers", []))


def rate_limit_key_from_scope(scope: Scope) -> str:
    client = scope.get("client")
    if isinstance(client, tuple) and client:
        return f"ip:{client[0]}"
    return "ip:local"


async def send_stage8_error(
    scope: Scope,
    send: Send,
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
) -> None:
    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details={},
            requestId=request_id,
        )
    )
    response = JSONResponse(
        status_code=status_code,
        content=payload.model_dump(by_alias=True),
        headers={**FOUNDATION_HEADERS, "X-Request-Id": request_id},
    )

    async def empty_receive() -> Message:
        return {"type": "http.disconnect"}

    await response(scope, empty_receive, send)


class Stage8WriteRateLimiter:
    def __init__(self, *, limit: int, window_seconds: float, max_keys: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._events_by_key: dict[str, list[float]] = {}
        self._lock = Lock()

    def allow(self, *, key: str, now: float | None = None) -> bool:
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self.window_seconds
        with self._lock:
            for existing_key, existing_events in list(self._events_by_key.items()):
                retained_events = [event for event in existing_events if event > cutoff]
                if retained_events:
                    self._events_by_key[existing_key] = retained_events
                else:
                    del self._events_by_key[existing_key]

            events = [event for event in self._events_by_key.get(key, []) if event > cutoff]
            if key not in self._events_by_key and len(self._events_by_key) >= self.max_keys:
                return False
            if len(events) >= self.limit:
                self._events_by_key[key] = events
                return False
            events.append(timestamp)
            self._events_by_key[key] = events
            return True

    def reset(self) -> None:
        with self._lock:
            self._events_by_key.clear()


stage8_write_rate_limiter = Stage8WriteRateLimiter(
    limit=MAX_STAGE8_WRITE_REQUESTS_PER_MINUTE,
    window_seconds=STAGE8_RATE_LIMIT_WINDOW_SECONDS,
    max_keys=MAX_STAGE8_RATE_LIMIT_KEYS,
)


@app.middleware("http")
async def add_foundation_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-Id") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    for header, value in FOUNDATION_HEADERS.items():
        response.headers[header] = value
    response.headers["X-Request-Id"] = request_id
    return response


app.add_middleware(Stage8RequestSizeLimitMiddleware)


def request_id_for(request: Request) -> str:
    return str(getattr(request.state, "request_id", "")) or str(uuid4())


def error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, ErrorDetailValue] | None = None,
) -> JSONResponse:
    request_id = request_id_for(request)
    payload = ErrorResponse(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or {},
            requestId=request_id,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(by_alias=True),
        headers={**FOUNDATION_HEADERS, "X-Request-Id": request_id},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "INTERNAL_SERVER_ERROR" if exc.status_code >= 500 else "HTTP_ERROR"
    message = "Internal server error." if exc.status_code >= 500 else str(exc.detail) if exc.detail else "Request failed."
    return error_response(request=request, status_code=exc.status_code, code=code, message=message)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_error_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    code = "NOT_FOUND" if exc.status_code == 404 else "INTERNAL_SERVER_ERROR" if exc.status_code >= 500 else "HTTP_ERROR"
    message = "Internal server error." if exc.status_code >= 500 else str(exc.detail) if exc.detail else "Request failed."
    return error_response(request=request, status_code=exc.status_code, code=code, message=message)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
        details={"errorCount": len(exc.errors())},
    )


@app.exception_handler(Stage4Error)
async def stage4_error_handler(request: Request, exc: Stage4Error) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


@app.exception_handler(Stage6Error)
async def stage6_error_handler(request: Request, exc: Stage6Error) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


@app.exception_handler(Stage7Error)
async def stage7_error_handler(request: Request, exc: Stage7Error) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


@app.exception_handler(HostedDemoError)
async def hosted_demo_error_handler(request: Request, exc: HostedDemoError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, _exc: Exception) -> JSONResponse:
    return error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error.",
    )


def health_payload() -> HealthResponse:
    return HealthResponse(status="ok", service="narratwin-ai-backend", stage="8")


@app.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthz() -> HealthResponse:
    return health_payload()


@app.get("/readyz", response_model=ReadinessResponse, tags=["health"])
def readyz() -> ReadinessResponse:
    return ReadinessResponse(
        **health_payload().model_dump(),
        checkedAt=datetime.now(UTC).isoformat(),
    )


@api_v1.get("/healthz", response_model=HealthResponse, tags=["health"])
def api_healthz() -> HealthResponse:
    return health_payload()


@api_v1.get("/readyz", response_model=ReadinessResponse, tags=["health"])
def api_readyz() -> ReadinessResponse:
    return readyz()


@api_v1.get("/ops/status", response_model=OpsStatusResponse, tags=["operations"])
def api_ops_status() -> OpsStatusResponse:
    return OpsStatusResponse(
        status="ok",
        service="narratwin-ai-backend",
        stage="8",
        checkedAt=datetime.now(UTC).isoformat(),
        operationalPosture="LOCAL_ONLY",
        durability=OpsDurabilityResponse(
            stage4=OpsStage4DurabilityResponse(
                durableStateEnabled=stage4_service.state_path is not None,
                stateBackend="json-file" if stage4_service.state_path is not None else "memory",
                recordCounts=Stage4OpsRecordCountsResponse(
                    projects=len(stage4_service.projects),
                    documents=len(stage4_service.documents),
                    ingestionRuns=len(stage4_service.ingestion_runs),
                    walkthroughRuns=len(stage4_service.walkthrough_runs),
                    idempotencyRecords=len(stage4_service.idempotency_records),
                ),
            ),
            stage6=OpsStage6DurabilityResponse(
                durableStateEnabled=stage6_service.state_path is not None,
                stateBackend="json-file" if stage6_service.state_path is not None else "memory",
                recordCounts=Stage6OpsRecordCountsResponse(
                    idempotencyRecords=len(stage6_service.idempotency_records),
                ),
            ),
            stage7=OpsStage7DurabilityResponse(
                durableStateEnabled=stage7_service.state_path is not None,
                stateBackend="json-file" if stage7_service.state_path is not None else "memory",
                recordCounts=Stage7OpsRecordCountsResponse(
                    avatarRenders=len(stage7_service.avatar_renders),
                    artifactMetadata=len(stage7_service.artifact_metadata),
                    idempotencyRecords=len(stage7_service.idempotency_records),
                ),
            ),
        ),
        monitoring=OpsMonitoringResponse(
            healthEndpoint=True,
            readinessEndpoint=True,
            opsStatusEndpoint=True,
            structuredLoggingConfigured=True,
            walkthroughMetricsInstrumented=True,
            metricsEndpointExposed=False,
            productionAlertsConfigured=False,
            langfuseConfigured=is_langfuse_enabled(),
        ),
    )


@api_v1.post("/projects", status_code=201, response_model=ProjectResponse, tags=["projects"])
def create_project(
    request: CreateProjectRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> ProjectResponse:
    project = stage4_service.create_project(
        principal=principal,
        name=request.name,
        description=request.description,
        default_audience=request.default_audience,
        default_language=request.default_language,
        idempotency_key=idempotency_key,
    )
    return ProjectResponse.model_validate(project_to_api(project))


@api_v1.post(
    "/projects/{project_id}/knowledge-documents",
    status_code=201,
    response_model=DocumentResponse,
    tags=["knowledge"],
)
async def upload_knowledge_document(
    project_id: str,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
    file: UploadFile = File(...),
) -> DocumentResponse:
    data = await read_upload_with_limit(file)
    document = stage4_service.upload_document(
        principal=principal,
        project_id=project_id,
        source_filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        idempotency_key=idempotency_key,
    )
    return DocumentResponse.model_validate(document_to_api(document))


@api_v1.patch(
    "/projects/{project_id}/knowledge-documents/{document_id}/approval",
    response_model=DocumentResponse,
    tags=["knowledge"],
)
def approve_knowledge_document(
    project_id: str,
    document_id: str,
    request: ApproveDocumentRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> DocumentResponse:
    del request
    document = stage4_service.approve_document(
        principal=principal,
        project_id=project_id,
        document_id=document_id,
        idempotency_key=idempotency_key,
    )
    return DocumentResponse.model_validate(document_to_api(document))


@api_v1.post(
    "/projects/{project_id}/ingestion-runs",
    status_code=201,
    response_model=IngestionRunResponse,
    tags=["ingestion"],
)
def start_ingestion_run(
    project_id: str,
    request: StartIngestionRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> IngestionRunResponse:
    run = stage4_service.ingest_documents(
        principal=principal,
        project_id=project_id,
        document_ids=request.document_ids,
        idempotency_key=idempotency_key,
    )
    return IngestionRunResponse.model_validate(ingestion_to_api(run))


@api_v1.post(
    "/projects/{project_id}/walkthrough-runs",
    status_code=201,
    response_model=WalkthroughRunResponse,
    response_model_exclude_none=True,
    tags=["walkthrough"],
)
def generate_walkthrough_run(
    project_id: str,
    request: GenerateWalkthroughRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> WalkthroughRunResponse:
    run = stage4_service.generate_walkthrough(
        principal=principal,
        project_id=project_id,
        audience=request.audience,
        requested_language=request.requested_language,
        depth=request.depth,
        style=request.style,
        prompt=request.prompt,
        idempotency_key=idempotency_key,
    )
    return WalkthroughRunResponse.model_validate(walkthrough_to_api(run))


@api_v1.post(
    "/projects/{project_id}/walkthrough-runs/{run_id}/multilingual-runs",
    status_code=201,
    response_model=MultilingualWalkthroughResponse,
    response_model_exclude_none=True,
    tags=["walkthrough"],
)
def generate_multilingual_walkthrough_run(
    project_id: str,
    run_id: str,
    request: GenerateMultilingualWalkthroughRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> MultilingualWalkthroughResponse:
    project = stage4_service.projects.get(project_id)
    if project is None:
        raise Stage6Error(404, "NOT_FOUND", "Project not found.")
    if project.tenant_id != principal.tenant_id or project.owner_id != principal.actor_id:
        raise Stage6Error(403, "FORBIDDEN", "Project is not accessible to this principal.")
    source_run = stage4_service.walkthrough_runs.get(run_id)
    if source_run is None or source_run.project_id != project_id:
        raise Stage6Error(404, "NOT_FOUND", "Walkthrough run not found.")
    if source_run.tenant_id != principal.tenant_id or source_run.actor_id != principal.actor_id:
        raise Stage6Error(403, "FORBIDDEN", "Walkthrough run is not accessible to this principal.")
    if source_run.status != "COMPLETED" or not source_run.accepted_script_text:
        raise Stage6Error(422, "SOURCE_RUN_NOT_TRANSLATABLE", "Only completed grounded walkthrough runs can be translated.")
    if source_run.evaluation_status != "PASSED":
        raise Stage6Error(422, "SOURCE_RUN_NOT_TRANSLATABLE", "Only passed grounded walkthrough runs can be translated.")
    if source_run.evaluation is None or not source_run.evaluation.claim_supports or not source_run.retrieved_context:
        raise Stage6Error(
            422,
            "SOURCE_RUN_NOT_TRANSLATABLE",
            "Multilingual replay requires grounded evaluation evidence.",
        )

    source_citation_count = len(source_run.evaluation.claim_supports)
    source_context_ref_ids = tuple(context.context_ref_id for context in source_run.retrieved_context)
    source_citation_indexes = tuple(support.citation_index for support in source_run.evaluation.claim_supports)
    source_claim_support_ids = tuple(support.claim_support_id for support in source_run.evaluation.claim_supports)
    source_evaluation_checksum = build_source_evaluation_checksum(
        source_evaluation_id=source_run.evaluation.evaluation_id,
        source_run_id=source_run.run_id,
        trace_id=source_run.trace_id,
        evaluation_status=source_run.evaluation_status or "UNKNOWN",
        source_context_ref_ids=source_context_ref_ids,
        source_context_ref_count=len(source_run.retrieved_context),
        source_citation_indexes=source_citation_indexes,
        source_citation_count=source_citation_count,
    )

    multilingual_run = stage6_service.generate_multilingual_walkthrough(
        source_script=source_run.accepted_script_text,
        source_language=source_run.requested_language,
        target_language=request.target_language,
        glossary_terms=request.glossary_terms,
        tenant_id=principal.tenant_id,
        project_id=project_id,
        actor_id=principal.actor_id,
        requested_voice_provider=request.requested_voice_provider,
        source_run_id=source_run.run_id,
        trace_id=source_run.trace_id,
        source_context_ref_count=len(source_run.retrieved_context),
        source_citation_count=source_citation_count,
        source_context_ref_ids=source_context_ref_ids,
        source_citation_indexes=source_citation_indexes,
        source_claim_support_ids=source_claim_support_ids,
        source_evaluation_id=source_run.evaluation.evaluation_id,
        source_evaluation_checksum=source_evaluation_checksum,
        evaluation_status=source_run.evaluation_status or "UNKNOWN",
        idempotency_scope=f"{principal.tenant_id}:{principal.actor_id}:{project_id}:{run_id}",
        idempotency_key=idempotency_key,
    )
    return MultilingualWalkthroughResponse.model_validate(multilingual_to_api(multilingual_run))


@api_v1.post(
    "/projects/{project_id}/walkthrough-runs/{run_id}/avatar-consents",
    status_code=201,
    response_model=AvatarConsentResponse,
    tags=["walkthrough"],
)
def capture_avatar_consent(
    project_id: str,
    run_id: str,
    request: CaptureAvatarConsentRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> AvatarConsentResponse:
    renderable = resolve_stage7_renderable_source(project_id, run_id, principal)
    source_run = renderable.source_run
    evaluation = source_run.evaluation
    assert evaluation is not None
    consent = stage7_service.capture_synthetic_avatar_consent(
        tenant_id=principal.tenant_id,
        project_id=project_id,
        actor_id=principal.actor_id,
        source_run_id=source_run.run_id,
        trace_id=source_run.trace_id,
        source_context_ref_ids=renderable.source_context_ref_ids,
        source_citation_indexes=renderable.source_citation_indexes,
        source_evaluation_id=evaluation.evaluation_id,
        source_evaluation_checksum=renderable.source_evaluation_checksum,
        evaluation_status=source_run.evaluation_status or "UNKNOWN",
        consent_to_use_synthetic_avatar=request.consent_to_use_synthetic_avatar,
        idempotency_scope=f"{principal.tenant_id}:{principal.actor_id}:{project_id}:{run_id}",
        idempotency_key=idempotency_key,
    )
    return AvatarConsentResponse.model_validate(avatar_consent_to_api(consent))


@api_v1.post(
    "/projects/{project_id}/walkthrough-runs/{run_id}/avatar-renders",
    status_code=201,
    response_model=AvatarRenderResponse,
    tags=["walkthrough"],
)
def generate_avatar_render(
    project_id: str,
    run_id: str,
    request: GenerateAvatarRenderRequest,
    principal: LocalPrincipal = Depends(local_principal),
    idempotency_key: str | None = Depends(idempotency_key_header),
) -> AvatarRenderResponse:
    renderable = resolve_stage7_renderable_source(project_id, run_id, principal)
    source_run = renderable.source_run
    evaluation = source_run.evaluation
    assert evaluation is not None
    multilingual_bundle = validate_stage7_multilingual_bundle(
        request.multilingual_bundle,
        project_id=project_id,
        run_id=run_id,
        principal=principal,
        renderable=renderable,
    )
    multilingual_run = stage6_service.multilingual_runs[multilingual_bundle.multilingual_run_id]
    citation_count = len(renderable.source_citation_indexes)
    avatar_render = stage7_service.render_avatar_demo(
        source_script=multilingual_run.translated_script_text,
        requested_avatar_provider=request.requested_avatar_provider,
        source_run_id=source_run.run_id,
        trace_id=source_run.trace_id,
        source_context_ref_count=len(source_run.retrieved_context),
        source_citation_count=citation_count,
        source_context_ref_ids=renderable.source_context_ref_ids,
        source_citation_indexes=renderable.source_citation_indexes,
        source_evaluation_id=evaluation.evaluation_id,
        source_evaluation_checksum=renderable.source_evaluation_checksum,
        evaluation_status=source_run.evaluation_status or "UNKNOWN",
        multilingual_bundle=multilingual_bundle,
        cloned_identity_requested=request.cloned_identity_requested,
        consent_to_use_synthetic_avatar=request.consent_to_use_synthetic_avatar,
        durable_consent=DurableAvatarRenderScope(
            tenant_id=principal.tenant_id,
            project_id=project_id,
            actor_id=principal.actor_id,
            consent_record_id=request.consent_record_id,
        ),
        idempotency_scope=f"{principal.tenant_id}:{principal.actor_id}:{project_id}:{run_id}",
        idempotency_key=idempotency_key,
    )
    return AvatarRenderResponse.model_validate(avatar_render_to_api(avatar_render))


@api_v1.post(
    "/hosted-demo/access-decisions",
    response_model=HostedDemoDecision,
    response_model_exclude_none=True,
    tags=["hosted-demo"],
)
async def create_hosted_demo_access_decision(request: Request) -> HostedDemoDecision:
    raw_body = await request.body()
    try:
        payload = parse_hosted_demo_json(raw_body)
    except HostedDemoJsonError as exc:
        raise HostedDemoError(400, exc.code, exc.message) from exc
    try:
        access_request = HostedDemoAccessRequest.model_validate(payload)
    except ValueError as exc:
        raise HostedDemoError(422, "VALIDATION_ERROR", "Hosted-demo request validation failed.") from exc
    return hosted_demo_service.decide(access_request)


async def read_upload_with_limit(file: UploadFile) -> bytes:
    data = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            return bytes(data)
        data.extend(chunk)
        if len(data) > MAX_UPLOAD_BYTES:
            raise Stage4Error(413, "UPLOAD_TOO_LARGE", "Upload exceeds the Stage 4 size limit.")


def reset_app_state_for_tests() -> None:
    stage4_service.reset()
    stage6_service.reset()
    stage7_service.reset()
    hosted_demo_service.reset()
    stage8_write_rate_limiter.reset()


app.include_router(api_v1)
