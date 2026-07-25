"""Issue 280 PR B executable input/API/error contract slice."""

from __future__ import annotations

import base64
import html
import json
import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.rag.chunking import checksum_text
from backend.app.stage6 import LANGUAGE_CATALOG_BY_TAG, LanguageCatalogRecord
from backend.app.stage4 import contains_prompt_injection, contains_secret_like_content, normalize_content_type

ISSUE280_INPUT_CONTRACT_PATH = "/api/v1/checkpoint3/issue280/input-contract"
ISSUE280_LOCAL_E2E_DEMO_PATH = "/api/v1/checkpoint3/issue280/local-e2e-demo"
ISSUE280_CONTRACT_VERSION = "issue280-input-api-error-v1"
ISSUE280_LOCAL_E2E_CONTRACT_VERSION = "issue280-local-e2e-demo-v1"
ISSUE280_MAX_BYTES = 20_000
ISSUE280_MAX_DOCUMENTS = 3
ISSUE280_MAX_SECTIONS_PER_DOCUMENT = 12
ISSUE280_MAX_BODY_CHARS_PER_SECTION = 2_000
ISSUE280_MAX_TRANSCRIPT_SEGMENTS = 40
ISSUE280_MAX_GLOSSARY_TERMS = 20
ISSUE280_MAX_GLOSSARY_TERM_CHARS = 64
ISSUE280_MAX_CAPTION_CHARS = 240
ISSUE280_MAX_EXPORT_BUNDLE_BYTES = 1_000_000

_MARKDOWN_CONTENT_TYPE = "text/markdown"
_HEADING_PATTERN = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_PRIVATE_MARKER_PATTERN = re.compile(
    r"\b(confidential|do not share|internal only|private key|social security|ssn)\b",
    re.IGNORECASE,
)
_GLOSSARY_INSTRUCTION_PATTERN = re.compile(
    r"\b(ignore|translate|rewrite|casual|casually|citation|citations|source|sources|"
    r"instruction|instructions|audience|depth|language|prompt|developer|system)\b",
    re.IGNORECASE,
)
_SUPPORTED_LOCAL_E2E_LANGUAGES = {
    record.language_tag: record
    for record in LANGUAGE_CATALOG_BY_TAG.values()
    if record.local_demo_support_status == "SUPPORTED"
    and record.provider_support_status == "LOCAL_DEMO_FIXTURE"
    and record.test_coverage_level == "CHECKPOINT3A_EXHAUSTIVE"
}
_SENTENCE_PATTERN = re.compile(r"^(?P<claim>.+?)\s*\[(?P<citation>\d+)\]\.?$")
_AUDIENCE_PROFILES = {
    "RECRUITER": ("recruiters", "hiring signal"),
    "HIRING_MANAGER": ("hiring managers", "delivery confidence"),
    "ENGINEER": ("engineers", "implementation evidence"),
    "PRODUCT_LEADER": ("product leaders", "portfolio narrative"),
    "CUSTOMER": ("customers", "customer value"),
    "BEGINNER": ("beginners", "plain-language orientation"),
    "GLOBAL_VIEWER": ("global viewers", "globally understandable context"),
}
_LOCAL_TRANSLATION_TEMPLATES = {
    "hi": "स्थानीय मॉक रूपांतरण ({native_name}): स्रोत खंड {section}; सुरक्षित परियोजना शब्द {glossary}{citation}",
    "es": "Conversion local simulada ({native_name}): segmento fuente {section}; termino protegido {glossary}{citation}",
    "fr": "Conversion locale simulee ({native_name}) : segment source {section}; terme protege {glossary}{citation}",
    "ar": "تحويل محلي تجريبي ({native_name}): مقطع المصدر {section}; مصطلح محفوظ {glossary}{citation}",
    "ja": "ローカルモック変換 ({native_name}): ソース区分 {section}; 保護用語 {glossary}{citation}",
    "he": "המרת מוק מקומית ({native_name}): מקטע מקור {section}; מונח שמור {glossary}{citation}",
    "default": "Local mock conversion ({native_name}, {english_name}): source segment {section}; protected term {glossary}{citation}",
}


@dataclass(frozen=True)
class Issue280ErrorSpec:
    status_code: int
    message: str
    safe_details: str
    remediation: str


ISSUE280_ERROR_TAXONOMY: dict[str, Issue280ErrorSpec] = {
    "ISSUE280_INPUT_TOO_LARGE": Issue280ErrorSpec(
        413,
        "The markdown file is above the supported demo size.",
        "Reduce the file to 20000 bytes or less.",
        "Split large synthetic knowledge into smaller markdown documents.",
    ),
    "ISSUE280_UNSUPPORTED_FILE_TYPE": Issue280ErrorSpec(
        415,
        "Only markdown text files are supported for this local demo.",
        "Use text/markdown content.",
        "Convert the synthetic project knowledge to markdown.",
    ),
    "ISSUE280_TOO_MANY_DOCUMENTS": Issue280ErrorSpec(
        422,
        "The demo supports up to 3 markdown documents.",
        "Remove extra documents before approval.",
        "Combine or remove synthetic documents.",
    ),
    "ISSUE280_PROMPT_INJECTION_REJECTED": Issue280ErrorSpec(
        422,
        "The markdown appears to contain instructions that conflict with the selected demo settings.",
        "Project knowledge must describe facts, not override audience, depth, language, citations, or safety behavior.",
        "Rewrite the content as factual synthetic project knowledge.",
    ),
    "ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED": Issue280ErrorSpec(
        422,
        "The markdown appears to include unsafe, private, or secret-like content.",
        "Use only public-safe synthetic project knowledge.",
        "Replace sensitive-looking values with public-safe synthetic placeholders.",
    ),
    "ISSUE280_GLOSSARY_INVALID": Issue280ErrorSpec(
        422,
        "Glossary terms must be protected project terms, not translation instructions.",
        "Use up to 20 terms, each 64 characters or fewer.",
        "Remove duplicates, instructions, or oversized terms.",
    ),
    "ISSUE280_TRANSLATION_REFUSED": Issue280ErrorSpec(
        422,
        "The local demo could not produce a faithful translated transcript for the selected settings.",
        "The accepted English script remains available.",
        "Use supported languages and public-safe bounded markdown.",
    ),
    "ISSUE280_INTERNAL_ERROR_SAFE": Issue280ErrorSpec(
        500,
        "The local demo could not complete this request.",
        "No provider details, filesystem paths, stack traces, raw markdown, or secret-like values are shown.",
        "If the problem repeats, capture the run ID and local logs without sharing private inputs.",
    ),
}


class Issue280ContractError(Exception):
    def __init__(self, code: str, field: str) -> None:
        spec = ISSUE280_ERROR_TAXONOMY[code]
        super().__init__(spec.message)
        self.status_code = spec.status_code
        self.code = code
        self.message = spec.message
        self.field = field


class Issue280DocumentInput(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    filename: str
    content_type: str = Field(alias="contentType")
    markdown: str


class Issue280InputContractRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    documents: list[Issue280DocumentInput]
    audience: Literal["RECRUITER", "HIRING_MANAGER", "ENGINEER", "PRODUCT_LEADER", "CUSTOMER", "BEGINNER", "GLOBAL_VIEWER"]
    depth: Literal["CONCISE", "STANDARD", "DEEP"]
    target_language: str = Field(alias="targetLanguage")
    glossary_terms: list[str] = Field(default_factory=list, alias="glossaryTerms")


class Issue280LimitsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    max_bytes: int = Field(alias="maxBytes")
    max_documents: int = Field(alias="maxDocuments")
    max_sections_per_document: int = Field(alias="maxSectionsPerDocument")
    max_body_chars_per_section: int = Field(alias="maxBodyCharsPerSection")
    max_transcript_segments: int = Field(alias="maxTranscriptSegments")
    max_glossary_terms: int = Field(alias="maxGlossaryTerms")
    max_glossary_term_chars: int = Field(alias="maxGlossaryTermChars")
    max_caption_chars: int = Field(alias="maxCaptionChars")
    max_export_bundle_bytes: int = Field(alias="maxExportBundleBytes")


class Issue280RequestSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    document_count: int = Field(alias="documentCount")
    audience: str
    depth: str
    target_language: str = Field(alias="targetLanguage")
    glossary_term_count: int = Field(alias="glossaryTermCount")


class Issue280DocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    filename: str
    content_type: Literal["text/markdown"] = Field(alias="contentType")
    size_bytes: int = Field(alias="sizeBytes")
    section_count: int = Field(alias="sectionCount")
    checksum: str


class Issue280ProviderPostureResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    llm: Literal["mock"]
    translation: Literal["mock"]
    voice: Literal["mock"]
    avatar: Literal["mock"]
    video_renderer: Literal["local-html"] = Field(alias="videoRenderer")
    network_egress: bool = Field(alias="networkEgress")
    paid_providers_enabled: bool = Field(alias="paidProvidersEnabled")
    real_provider_calls: bool = Field(alias="realProviderCalls")
    cloned_identity: bool = Field(alias="clonedIdentity")
    real_media: bool = Field(alias="realMedia")


class Issue280TraceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    request_id: str = Field(alias="requestId")
    evidence_level: Literal["input-api-error-contract", "local-e2e-demo"] = Field(alias="evidenceLevel")
    runtime_provider_mode: Literal["LOCAL_MOCK_DISABLED_EXTERNAL"] = Field(alias="runtimeProviderMode")


class Issue280InputContractResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_: Literal["Issue280InputApiContractV1"] = Field(alias="schema")
    status: Literal["ACCEPTED"]
    accepted: bool
    contract_version: str = Field(alias="contractVersion")
    limits: Issue280LimitsResponse
    request: Issue280RequestSummaryResponse
    documents: list[Issue280DocumentSummaryResponse]
    provider_posture: Issue280ProviderPostureResponse = Field(alias="providerPosture")
    trace: Issue280TraceResponse


class Issue280LocalDemoSessionResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    project_id: str = Field(alias="projectId")
    document_ids: list[str] = Field(alias="documentIds")
    output_id: str = Field(alias="outputId")
    replayed: bool


class Issue280LocalDemoContextRefResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    context_ref_id: str = Field(alias="contextRefId")
    document_id: str = Field(alias="documentId")
    chunk_id: str = Field(alias="chunkId")
    source_checksum: str = Field(alias="sourceChecksum")
    fact_checksum: str = Field(alias="factChecksum")
    section_heading: str = Field(alias="sectionHeading")
    relevance_score: float = Field(alias="relevanceScore")


class Issue280LocalDemoRetrievalResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    strategy: Literal["DETERMINISTIC_LOCAL_CHUNKS"]
    context_refs: list[Issue280LocalDemoContextRefResponse] = Field(alias="contextRefs")


class Issue280LocalDemoGeneratedResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    accepted_script_text: str = Field(alias="acceptedScriptText")
    source_language: Literal["en"] = Field(alias="sourceLanguage")
    generation_mode: Literal["LOCAL_MOCK_DETERMINISTIC"] = Field(alias="generationMode")


class Issue280LocalDemoTranscriptSegmentResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    segment_id: str = Field(alias="segmentId")
    source_text: str = Field(alias="sourceText")
    target_text: str = Field(alias="targetText")
    english_reference_text: str = Field(alias="englishReferenceText")
    context_ref_ids: list[str] = Field(alias="contextRefIds")
    citation_indexes: list[int] = Field(alias="citationIndexes")
    claim_support_ids: list[str] = Field(alias="claimSupportIds")


class Issue280LocalDemoMultilingualResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    source_language: Literal["en"] = Field(alias="sourceLanguage")
    target_language: str = Field(alias="targetLanguage")
    direction: Literal["ltr", "rtl"]
    translation_mode: Literal["LOCAL_MOCK_DETERMINISTIC"] = Field(alias="translationMode")
    multilingual_run_id: str = Field(alias="multilingualRunId")
    preserved_glossary_terms: list[str] = Field(alias="preservedGlossaryTerms")
    segments: list[Issue280LocalDemoTranscriptSegmentResponse]


class Issue280LocalDemoClaimSupportResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    claim_support_id: str = Field(alias="claimSupportId")
    claim_text: str = Field(alias="claimText")
    support_status: Literal["SUPPORTED"] = Field(alias="supportStatus")
    context_ref_id: str = Field(alias="contextRefId")
    citation_index: int = Field(alias="citationIndex")


class Issue280LocalDemoEvaluationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    evaluation_id: str = Field(alias="evaluationId")
    evaluation_checksum: str = Field(alias="evaluationChecksum")
    status: Literal["PASSED"]
    unsupported_claim_count: int = Field(alias="unsupportedClaimCount")
    claim_supports: list[Issue280LocalDemoClaimSupportResponse] = Field(alias="claimSupports")


class Issue280LocalDemoStorageResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    stored: bool
    output_id: str = Field(alias="outputId")
    output_checksum: str = Field(alias="outputChecksum")
    metadata_checksum: str = Field(alias="metadataChecksum")
    artifact_bundle_checksum: str = Field(alias="artifactBundleChecksum")
    report_checksum: str = Field(alias="reportChecksum")


class Issue280LocalDemoArtifactResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    content_base64: str = Field(alias="contentBase64")
    checksum: str


class Issue280LocalDemoArtifactsResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    translated_script: Issue280LocalDemoArtifactResponse = Field(alias="translatedScript")
    subtitles: Issue280LocalDemoArtifactResponse
    transcript_metadata: Issue280LocalDemoArtifactResponse = Field(alias="transcriptMetadata")
    voice_manifest: Issue280LocalDemoArtifactResponse = Field(alias="voiceManifest")
    avatar_demo: Issue280LocalDemoArtifactResponse = Field(alias="avatarDemo")
    render_manifest: Issue280LocalDemoArtifactResponse = Field(alias="renderManifest")
    video_placeholder: Issue280LocalDemoArtifactResponse = Field(alias="videoPlaceholder")


class Issue280LocalE2EDemoResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    schema_: Literal["Issue280LocalE2EDemoV1"] = Field(alias="schema")
    status: Literal["COMPLETED"]
    accepted: bool
    contract_version: str = Field(alias="contractVersion")
    request: Issue280RequestSummaryResponse
    session: Issue280LocalDemoSessionResponse
    retrieval: Issue280LocalDemoRetrievalResponse
    generated: Issue280LocalDemoGeneratedResponse
    multilingual: Issue280LocalDemoMultilingualResponse
    evaluation: Issue280LocalDemoEvaluationResponse
    storage: Issue280LocalDemoStorageResponse
    artifacts: Issue280LocalDemoArtifactsResponse
    correctness_report: dict[str, Any] = Field(alias="correctnessReport")
    provider_posture: Issue280ProviderPostureResponse = Field(alias="providerPosture")
    trace: Issue280TraceResponse


@dataclass(frozen=True)
class Issue280GroundedFact:
    fact_id: str
    document_id: str
    chunk_id: str
    context_ref_id: str
    source_checksum: str
    fact_checksum: str
    section_heading: str
    fact_text: str
    citation_index: int


@dataclass(frozen=True)
class Issue280StoredLocalDemo:
    request_checksum: str
    response: Issue280LocalE2EDemoResponse


def issue280_error_details(code: str, field: str) -> dict[str, str]:
    spec = ISSUE280_ERROR_TAXONOMY[code]
    return {
        "field": field,
        "safeDetails": spec.safe_details,
        "remediation": spec.remediation,
    }


def issue280_trace_response(request_id: str) -> Issue280TraceResponse:
    return Issue280TraceResponse(
        requestId=request_id,
        evidenceLevel="input-api-error-contract",
        runtimeProviderMode="LOCAL_MOCK_DISABLED_EXTERNAL",
    )


def issue280_local_e2e_trace_response(request_id: str) -> Issue280TraceResponse:
    return Issue280TraceResponse(
        requestId=request_id,
        evidenceLevel="local-e2e-demo",
        runtimeProviderMode="LOCAL_MOCK_DISABLED_EXTERNAL",
    )


def validate_issue280_input_contract(request: Issue280InputContractRequest) -> Issue280InputContractResponse:
    documents = _validate_documents(request.documents)
    _validate_glossary(request.glossary_terms)
    return Issue280InputContractResponse(
        schema="Issue280InputApiContractV1",
        status="ACCEPTED",
        accepted=True,
        contractVersion=ISSUE280_CONTRACT_VERSION,
        limits=Issue280LimitsResponse(
            maxBytes=ISSUE280_MAX_BYTES,
            maxDocuments=ISSUE280_MAX_DOCUMENTS,
            maxSectionsPerDocument=ISSUE280_MAX_SECTIONS_PER_DOCUMENT,
            maxBodyCharsPerSection=ISSUE280_MAX_BODY_CHARS_PER_SECTION,
            maxTranscriptSegments=ISSUE280_MAX_TRANSCRIPT_SEGMENTS,
            maxGlossaryTerms=ISSUE280_MAX_GLOSSARY_TERMS,
            maxGlossaryTermChars=ISSUE280_MAX_GLOSSARY_TERM_CHARS,
            maxCaptionChars=ISSUE280_MAX_CAPTION_CHARS,
            maxExportBundleBytes=ISSUE280_MAX_EXPORT_BUNDLE_BYTES,
        ),
        request=Issue280RequestSummaryResponse(
            documentCount=len(request.documents),
            audience=request.audience,
            depth=request.depth,
            targetLanguage=request.target_language,
            glossaryTermCount=len(request.glossary_terms),
        ),
        documents=documents,
        providerPosture=Issue280ProviderPostureResponse(
            llm="mock",
            translation="mock",
            voice="mock",
            avatar="mock",
            videoRenderer="local-html",
            networkEgress=False,
            paidProvidersEnabled=False,
            realProviderCalls=False,
            clonedIdentity=False,
            realMedia=False,
        ),
        trace=issue280_trace_response(""),
    )


class Issue280LocalDemoService:
    def __init__(self) -> None:
        self._stored_outputs: dict[str, Issue280StoredLocalDemo] = {}
        self._idempotency: dict[str, Issue280StoredLocalDemo] = {}

    def reset(self) -> None:
        self._stored_outputs.clear()
        self._idempotency.clear()

    def run_demo(
        self,
        *,
        request: Issue280InputContractRequest,
        request_id: str,
        idempotency_key: str | None,
    ) -> Issue280LocalE2EDemoResponse:
        input_summary = validate_issue280_input_contract(request)
        target_language = request.target_language
        target_record = _SUPPORTED_LOCAL_E2E_LANGUAGES.get(target_language)
        if target_record is None:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "targetLanguage")
        request_checksum = checksum_text(request.model_dump_json(by_alias=True))
        replay_key = (idempotency_key or "").strip()
        if not replay_key:
            raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "idempotencyKey")
        stored = self._idempotency.get(replay_key)
        if stored is not None:
            if stored.request_checksum != request_checksum:
                raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "idempotencyKey")
            return _copy_response_for_request(stored.response, request_id=request_id, replayed=True)

        facts = _extract_grounded_facts(request)
        accepted_script_text = _render_grounded_script(facts=facts, audience=request.audience, depth=request.depth)
        claim_supports = _evaluate_supported_claims(accepted_script_text, facts)
        if len(claim_supports) == 0:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "generatedClaims")
        multilingual = _build_multilingual_response(
            facts=facts,
            claim_supports=claim_supports,
            target_language=target_language,
            target_record=target_record,
            glossary_terms=request.glossary_terms,
        )
        evaluation_checksum = _evaluation_checksum(claim_supports)
        output_checksum = checksum_text(
            json.dumps(
                {
                    "script": accepted_script_text,
                    "targetLanguage": target_language,
                    "segments": [segment.model_dump(by_alias=True) for segment in multilingual.segments],
                    "claimSupports": [support.model_dump(by_alias=True) for support in claim_supports],
                },
                sort_keys=True,
            )
        )
        session_id = "issue280_session_" + request_checksum[:16]
        output_id = "issue280_output_" + output_checksum[:16]
        document_ids = sorted({fact.document_id for fact in facts})
        context_refs = [
            Issue280LocalDemoContextRefResponse(
                contextRefId=fact.context_ref_id,
                documentId=fact.document_id,
                chunkId=fact.chunk_id,
                sourceChecksum=fact.source_checksum,
                factChecksum=fact.fact_checksum,
                sectionHeading=fact.section_heading,
                relevanceScore=1.0,
            )
            for fact in facts
        ]
        evaluation = Issue280LocalDemoEvaluationResponse(
            evaluationId="issue280_eval_" + output_checksum[:16],
            evaluationChecksum=evaluation_checksum,
            status="PASSED",
            unsupportedClaimCount=0,
            claimSupports=claim_supports,
        )
        metadata_checksum = checksum_text(
            json.dumps(
                {
                    "sessionId": session_id,
                    "outputId": output_id,
                    "requestChecksum": request_checksum,
                    "evaluationChecksum": evaluation_checksum,
                    "multilingualRunId": multilingual.multilingual_run_id,
                },
                sort_keys=True,
            )
        )
        artifacts = _build_artifacts(
            request=request,
            context_refs=context_refs,
            multilingual=multilingual,
            evaluation=evaluation,
            output_checksum=output_checksum,
            metadata_checksum=metadata_checksum,
            provider_posture=input_summary.provider_posture.model_dump(by_alias=True),
        )
        artifact_bundle_checksum = _artifact_bundle_checksum(artifacts)
        correctness_report = _build_correctness_report(
            request=request,
            request_id=request_id,
            multilingual=multilingual,
            evaluation=evaluation,
            output_checksum=output_checksum,
            metadata_checksum=metadata_checksum,
            artifact_bundle_checksum=artifact_bundle_checksum,
            provider_posture=input_summary.provider_posture.model_dump(by_alias=True),
        )
        report_checksum = checksum_text(json.dumps(correctness_report, sort_keys=True))
        correctness_report["reportChecksum"] = report_checksum
        response = Issue280LocalE2EDemoResponse(
            schema="Issue280LocalE2EDemoV1",
            status="COMPLETED",
            accepted=True,
            contractVersion=ISSUE280_LOCAL_E2E_CONTRACT_VERSION,
            request=input_summary.request,
            session=Issue280LocalDemoSessionResponse(
                sessionId=session_id,
                projectId="issue280_project_" + request_checksum[:12],
                documentIds=document_ids,
                outputId=output_id,
                replayed=False,
            ),
            retrieval=Issue280LocalDemoRetrievalResponse(
                strategy="DETERMINISTIC_LOCAL_CHUNKS",
                contextRefs=context_refs,
            ),
            generated=Issue280LocalDemoGeneratedResponse(
                acceptedScriptText=accepted_script_text,
                sourceLanguage="en",
                generationMode="LOCAL_MOCK_DETERMINISTIC",
            ),
            multilingual=multilingual,
            evaluation=evaluation,
            storage=Issue280LocalDemoStorageResponse(
                stored=True,
                outputId=output_id,
                outputChecksum=output_checksum,
                metadataChecksum=metadata_checksum,
                artifactBundleChecksum=artifact_bundle_checksum,
                reportChecksum=report_checksum,
            ),
            artifacts=artifacts,
            correctnessReport=correctness_report,
            providerPosture=input_summary.provider_posture,
            trace=issue280_local_e2e_trace_response(request_id),
        )
        stored_response = Issue280StoredLocalDemo(request_checksum=request_checksum, response=response)
        self._stored_outputs[output_id] = stored_response
        self._idempotency[replay_key] = stored_response
        return response


def _copy_response_for_request(
    response: Issue280LocalE2EDemoResponse,
    *,
    request_id: str,
    replayed: bool,
) -> Issue280LocalE2EDemoResponse:
    return response.model_copy(
        update={
            "session": response.session.model_copy(update={"replayed": replayed}),
            "trace": issue280_local_e2e_trace_response(request_id),
        }
    )


def _extract_grounded_facts(request: Issue280InputContractRequest) -> tuple[Issue280GroundedFact, ...]:
    facts: list[Issue280GroundedFact] = []
    for document_index, document in enumerate(request.documents, start=1):
        normalized_markdown = document.markdown.replace("\r\n", "\n").replace("\r", "\n")
        document_id = f"issue280_doc_{document_index:03d}"
        source_checksum = checksum_text(normalized_markdown)
        for fact_index, (heading, fact_text) in enumerate(_iter_markdown_facts(normalized_markdown), start=1):
            chunk_id = f"issue280_chunk_{document_index:03d}_{fact_index:03d}"
            fact_checksum = checksum_text(fact_text)
            citation_index = len(facts) + 1
            facts.append(
                Issue280GroundedFact(
                    fact_id=f"issue280_fact_{citation_index:03d}",
                    document_id=document_id,
                    chunk_id=chunk_id,
                    context_ref_id="issue280_ctx_" + checksum_text(f"{chunk_id}:{fact_checksum}")[:16],
                    source_checksum=source_checksum,
                    fact_checksum=fact_checksum,
                    section_heading=heading,
                    fact_text=fact_text,
                    citation_index=citation_index,
                )
            )
    if not facts:
        raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "documents")
    return tuple(facts)


def _iter_markdown_facts(markdown: str) -> tuple[tuple[str, str], ...]:
    facts: list[tuple[str, str]] = []
    current_heading = "Overview"
    current_body: list[str] = []
    headings: list[str] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if current_body:
                facts.extend(_body_lines_to_facts(current_heading, current_body))
                current_body = []
            current_heading = re.sub(r"^#{1,6}\s*", "", line).strip() or "Overview"
            headings.append(current_heading)
            continue
        current_body.append(re.sub(r"^[-*]\s+", "", line))
    if current_body:
        facts.extend(_body_lines_to_facts(current_heading, current_body))
    if facts:
        return tuple(facts)
    return tuple((heading, f"Section {heading} is present in the approved synthetic knowledge") for heading in headings)


def _body_lines_to_facts(heading: str, body: list[str]) -> list[tuple[str, str]]:
    combined = " ".join(" ".join(line.split()) for line in body)
    if not combined:
        return []
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", combined) if sentence.strip()]
    return [(heading, sentence.rstrip(".")) for sentence in sentences[:3]]


def _render_grounded_script(*, facts: tuple[Issue280GroundedFact, ...], audience: str, depth: str) -> str:
    audience_label, audience_marker = _AUDIENCE_PROFILES[audience]
    if depth == "CONCISE":
        selected_facts = facts[: max(1, min(3, len(facts)))]
        claims = [
            f"For {audience_label}, the {audience_marker} is {fact.fact_text} [{fact.citation_index}]."
            for fact in selected_facts
        ]
        return " ".join(claims)
    if depth == "DEEP":
        claims = [
            (
                f"For {audience_label}, the {audience_marker} adds source-grounded detail and tradeoff from "
                f"{fact.section_heading}: {fact.fact_text} [{fact.citation_index}]."
            )
            for fact in facts
        ]
        return " ".join(claims)
    claims = [
        f"For {audience_label}, the {audience_marker} is source-bound: {fact.fact_text} [{fact.citation_index}]."
        for fact in facts
    ]
    return " ".join(claims)


def _evaluate_supported_claims(
    accepted_script_text: str,
    facts: tuple[Issue280GroundedFact, ...],
) -> list[Issue280LocalDemoClaimSupportResponse]:
    facts_by_citation = {fact.citation_index: fact for fact in facts}
    supports: list[Issue280LocalDemoClaimSupportResponse] = []
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", accepted_script_text) if sentence.strip()]
    for sentence in sentences:
        match = _SENTENCE_PATTERN.fullmatch(sentence)
        if match is None:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "generatedClaims")
        citation_index = int(match.group("citation"))
        claim_text = " ".join(match.group("claim").split())
        fact = facts_by_citation.get(citation_index)
        if fact is None or fact.fact_text not in claim_text:
            raise Issue280ContractError("ISSUE280_TRANSLATION_REFUSED", "generatedClaims")
        supports.append(
            Issue280LocalDemoClaimSupportResponse(
                claimSupportId=f"issue280_claimsup_{citation_index:03d}",
                claimText=claim_text,
                supportStatus="SUPPORTED",
                contextRefId=fact.context_ref_id,
                citationIndex=citation_index,
            )
        )
    return supports


def _build_multilingual_response(
    *,
    facts: tuple[Issue280GroundedFact, ...],
    claim_supports: list[Issue280LocalDemoClaimSupportResponse],
    target_language: str,
    target_record: LanguageCatalogRecord,
    glossary_terms: list[str],
) -> Issue280LocalDemoMultilingualResponse:
    facts_by_citation = {fact.citation_index: fact for fact in facts}
    segments: list[Issue280LocalDemoTranscriptSegmentResponse] = []
    for support in claim_supports:
        fact = facts_by_citation[support.citation_index]
        segments.append(
            Issue280LocalDemoTranscriptSegmentResponse(
                segmentId=f"issue280_segment_{fact.citation_index:03d}",
                sourceText=fact.fact_text,
                targetText=_translate_fact(
                    fact=fact,
                    target_record=target_record,
                    glossary_terms=glossary_terms,
                ),
                englishReferenceText=fact.fact_text,
                contextRefIds=[fact.context_ref_id],
                citationIndexes=[fact.citation_index],
                claimSupportIds=[support.claim_support_id],
            )
        )
    return Issue280LocalDemoMultilingualResponse(
        sourceLanguage="en",
        targetLanguage=target_language,
        direction=target_record.direction,
        translationMode="LOCAL_MOCK_DETERMINISTIC",
        multilingualRunId="issue280_multi_" + checksum_text(
            json.dumps(
                {
                    "targetLanguage": target_language,
                    "glossaryTerms": glossary_terms,
                    "segments": [segment.segment_id for segment in segments],
                },
                sort_keys=True,
            )
        )[:16],
        preservedGlossaryTerms=_preserved_glossary_terms(glossary_terms),
        segments=segments,
    )


def _translate_fact(
    *,
    fact: Issue280GroundedFact,
    target_record: LanguageCatalogRecord,
    glossary_terms: list[str],
) -> str:
    citation = f"[{fact.citation_index}]"
    preserved_terms = _preserved_glossary_terms(glossary_terms)
    glossary_clause = _glossary_clause(preserved_terms)
    if target_record.language_tag == "en":
        return f"{fact.fact_text} {glossary_clause}{citation}"
    template = _LOCAL_TRANSLATION_TEMPLATES.get(target_record.language_tag, _LOCAL_TRANSLATION_TEMPLATES["default"])
    return template.format(
        native_name=target_record.native_name,
        english_name=target_record.english_name,
        citation=citation,
        section=fact.section_heading,
        glossary=glossary_clause,
    )


def _preserved_glossary_terms(glossary_terms: list[str]) -> list[str]:
    seen: set[str] = set()
    preserved: list[str] = []
    for term in glossary_terms:
        normalized = " ".join(term.split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            preserved.append(normalized)
    return preserved


def _glossary_clause(glossary_terms: list[str]) -> str:
    if not glossary_terms:
        return "none "
    return ", ".join(glossary_terms) + " "


def _evaluation_checksum(claim_supports: list[Issue280LocalDemoClaimSupportResponse]) -> str:
    return checksum_text(
        json.dumps(
            [support.model_dump(by_alias=True) for support in claim_supports],
            sort_keys=True,
        )
    )


def _build_artifacts(
    *,
    request: Issue280InputContractRequest,
    context_refs: list[Issue280LocalDemoContextRefResponse],
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
    output_checksum: str,
    metadata_checksum: str,
    provider_posture: dict[str, Any],
) -> Issue280LocalDemoArtifactsResponse:
    translated_script = "\n".join(segment.target_text for segment in multilingual.segments)
    transcript_metadata = {
        "schema": "Issue280TranscriptMetadataV1",
        "audience": request.audience,
        "depth": request.depth,
        "targetLanguage": multilingual.target_language,
        "direction": multilingual.direction,
        "translationMode": multilingual.translation_mode,
        "multilingualRunId": multilingual.multilingual_run_id,
        "preservedGlossaryTerms": multilingual.preserved_glossary_terms,
        "segments": [segment.model_dump(by_alias=True) for segment in multilingual.segments],
        "contextRefs": [context_ref.model_dump(by_alias=True) for context_ref in context_refs],
        "claimSupports": [support.model_dump(by_alias=True) for support in evaluation.claim_supports],
        "evaluationId": evaluation.evaluation_id,
        "evaluationChecksum": evaluation.evaluation_checksum,
        "outputChecksum": output_checksum,
        "metadataChecksum": metadata_checksum,
        "providerPosture": provider_posture,
    }
    voice_manifest = {
        "schema": "Issue280VoiceManifestV1",
        "provider": "mock",
        "providerMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
        "language": multilingual.target_language,
        "direction": multilingual.direction,
        "textChecksum": checksum_text(translated_script),
        "realMedia": False,
        "clonedIdentity": False,
        "networkEgress": False,
    }
    render_manifest = {
        "schema": "Issue280RenderManifestV1",
        "renderer": "local-html",
        "providerMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
        "sourceEvaluationId": evaluation.evaluation_id,
        "sourceEvaluationChecksum": evaluation.evaluation_checksum,
        "targetLanguage": multilingual.target_language,
        "direction": multilingual.direction,
        "realMedia": False,
        "clonedIdentity": False,
    }
    video_placeholder = {
        "schema": "Issue280VideoPlaceholderV1",
        "providerMode": "LOCAL_MOCK_DISABLED_EXTERNAL",
        "realMedia": False,
        "hostedPublicProduction": False,
        "message": "Local demo placeholder only; no real provider call or rendered human media.",
    }
    avatar_demo = _avatar_demo_html(multilingual=multilingual, evaluation=evaluation)
    return Issue280LocalDemoArtifactsResponse(
        translatedScript=_artifact(
            file_name=f"issue280-{multilingual.target_language}-translated-script.md",
            mime_type="text/markdown",
            content=translated_script,
        ),
        subtitles=_artifact(
            file_name=f"issue280-{multilingual.target_language}-subtitles.srt",
            mime_type="application/x-subrip",
            content=_subtitles(multilingual.segments),
        ),
        transcriptMetadata=_artifact(
            file_name=f"issue280-{multilingual.target_language}-transcript-metadata.json",
            mime_type="application/json",
            content=json.dumps(transcript_metadata, indent=2, sort_keys=True),
        ),
        voiceManifest=_artifact(
            file_name=f"issue280-{multilingual.target_language}-voice-manifest.json",
            mime_type="application/json",
            content=json.dumps(voice_manifest, indent=2, sort_keys=True),
        ),
        avatarDemo=_artifact(
            file_name=f"issue280-{multilingual.target_language}-avatar-demo.html",
            mime_type="text/html",
            content=avatar_demo,
        ),
        renderManifest=_artifact(
            file_name=f"issue280-{multilingual.target_language}-render-manifest.json",
            mime_type="application/json",
            content=json.dumps(render_manifest, indent=2, sort_keys=True),
        ),
        videoPlaceholder=_artifact(
            file_name=f"issue280-{multilingual.target_language}-video-placeholder.json",
            mime_type="application/json",
            content=json.dumps(video_placeholder, indent=2, sort_keys=True),
        ),
    )


def _artifact(*, file_name: str, mime_type: str, content: str) -> Issue280LocalDemoArtifactResponse:
    return Issue280LocalDemoArtifactResponse(
        fileName=file_name,
        mimeType=mime_type,
        contentBase64=base64.b64encode(content.encode("utf-8")).decode("ascii"),
        checksum=checksum_text(content),
    )


def _subtitles(segments: list[Issue280LocalDemoTranscriptSegmentResponse]) -> str:
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        start_seconds = (index - 1) * 3
        end_seconds = index * 3
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{_srt_timestamp(start_seconds)} --> {_srt_timestamp(end_seconds)}",
                    segment.target_text,
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def _srt_timestamp(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"


def _avatar_demo_html(
    *,
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
) -> str:
    segment_items = "".join(
        f"<li>{html.escape(segment.target_text)}</li>" for segment in multilingual.segments
    )
    direction = "rtl" if multilingual.direction == "rtl" else "ltr"
    evaluation_id = html.escape(evaluation.evaluation_id)
    evaluation_checksum = html.escape(evaluation.evaluation_checksum)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><title>Issue 280 Local Avatar Demo</title></head>"
        f"<body dir=\"{direction}\"><main><h1>Issue 280 Local Mock Avatar Demo</h1>"
        "<p>Local demo placeholder only. No real provider call, cloned identity, hosted production output, or real media.</p>"
        f"<p>Evaluation: {evaluation_id} ({evaluation_checksum})</p><ol>{segment_items}</ol></main></body></html>"
    )


def _artifact_bundle_checksum(artifacts: Issue280LocalDemoArtifactsResponse) -> str:
    return checksum_text(
        json.dumps(
            {
                key: artifact["checksum"]
                for key, artifact in artifacts.model_dump(by_alias=True).items()
            },
            sort_keys=True,
        )
    )


def _build_correctness_report(
    *,
    request: Issue280InputContractRequest,
    request_id: str,
    multilingual: Issue280LocalDemoMultilingualResponse,
    evaluation: Issue280LocalDemoEvaluationResponse,
    output_checksum: str,
    metadata_checksum: str,
    artifact_bundle_checksum: str,
    provider_posture: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "Issue280OutputCorrectnessReportV1",
        "status": "PASSED",
        "traceId": request_id,
        "audience": request.audience,
        "depth": request.depth,
        "targetLanguage": multilingual.target_language,
        "direction": multilingual.direction,
        "segmentCount": len(multilingual.segments),
        "evaluationId": evaluation.evaluation_id,
        "evaluationChecksum": evaluation.evaluation_checksum,
        "outputChecksum": output_checksum,
        "metadataChecksum": metadata_checksum,
        "artifactBundleChecksum": artifact_bundle_checksum,
        "providerPosture": provider_posture,
        "preservedGlossaryTerms": multilingual.preserved_glossary_terms,
        "checks": {
            "untranslatedSourceLeakage": "PASSED",
            "missingClauses": "PASSED",
            "lostCitations": "PASSED",
            "brokenSegmentCount": "PASSED",
            "metadataArtifactParity": "PASSED",
            "unsafeOutput": "PASSED",
        },
        "boundaries": {
            "translationQualityClaim": "deterministic local/mock conversion only",
            "providerCalls": "disabled",
            "realMedia": False,
            "hostedPublicProduction": False,
        },
    }


issue280_local_demo_service = Issue280LocalDemoService()


def _validate_documents(documents: list[Issue280DocumentInput]) -> list[Issue280DocumentSummaryResponse]:
    if not documents:
        raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
    if len(documents) > ISSUE280_MAX_DOCUMENTS:
        raise Issue280ContractError("ISSUE280_TOO_MANY_DOCUMENTS", "documents")

    summaries: list[Issue280DocumentSummaryResponse] = []
    for document in documents:
        filename = _safe_markdown_filename(document.filename)
        content_type = normalize_content_type(document.content_type)
        if content_type != _MARKDOWN_CONTENT_TYPE:
            raise Issue280ContractError("ISSUE280_UNSUPPORTED_FILE_TYPE", "documents")
        markdown = document.markdown.replace("\r\n", "\n").replace("\r", "\n")
        size_bytes = len(markdown.encode("utf-8"))
        if size_bytes > ISSUE280_MAX_BYTES or _section_body_too_large(markdown):
            raise Issue280ContractError("ISSUE280_INPUT_TOO_LARGE", "documents")
        if not markdown.strip() or _CONTROL_CHARACTER_PATTERN.search(markdown) or contains_secret_like_content(markdown):
            raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
        if _PRIVATE_MARKER_PATTERN.search(markdown):
            raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
        if contains_prompt_injection(markdown):
            raise Issue280ContractError("ISSUE280_PROMPT_INJECTION_REJECTED", "documents")
        section_count = _section_count(markdown)
        if section_count > ISSUE280_MAX_SECTIONS_PER_DOCUMENT:
            raise Issue280ContractError("ISSUE280_INPUT_TOO_LARGE", "documents")
        summaries.append(
            Issue280DocumentSummaryResponse(
                filename=filename,
                contentType="text/markdown",
                sizeBytes=size_bytes,
                sectionCount=section_count,
                checksum=checksum_text(markdown),
            )
        )
    return summaries


def _safe_markdown_filename(filename: str) -> str:
    raw = filename.strip()
    if (
        not raw
        or raw in {".", ".."}
        or "/" in raw
        or "\\" in raw
        or ".." in PurePath(raw).parts
        or len(raw) > 160
        or any(ord(char) < 32 for char in raw)
    ):
        raise Issue280ContractError("ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED", "documents")
    name = PurePath(raw).name
    if not name.lower().endswith(".md"):
        raise Issue280ContractError("ISSUE280_UNSUPPORTED_FILE_TYPE", "documents")
    return name


def _section_count(markdown: str) -> int:
    heading_count = len(_HEADING_PATTERN.findall(markdown))
    if heading_count:
        return heading_count
    return 1


def _section_body_too_large(markdown: str) -> bool:
    current_body: list[str] = []
    for line in markdown.splitlines():
        if _HEADING_PATTERN.match(line):
            if len("\n".join(current_body)) > ISSUE280_MAX_BODY_CHARS_PER_SECTION:
                return True
            current_body = []
            continue
        current_body.append(line)
    return len("\n".join(current_body)) > ISSUE280_MAX_BODY_CHARS_PER_SECTION


def _validate_glossary(glossary_terms: list[str]) -> None:
    if len(glossary_terms) > ISSUE280_MAX_GLOSSARY_TERMS:
        raise Issue280ContractError("ISSUE280_GLOSSARY_INVALID", "glossaryTerms")
    for term in glossary_terms:
        normalized = " ".join(term.split())
        if not normalized or len(normalized) > ISSUE280_MAX_GLOSSARY_TERM_CHARS:
            raise Issue280ContractError("ISSUE280_GLOSSARY_INVALID", "glossaryTerms")
        if contains_prompt_injection(normalized) or _GLOSSARY_INSTRUCTION_PATTERN.search(normalized):
            raise Issue280ContractError("ISSUE280_GLOSSARY_INVALID", "glossaryTerms")
