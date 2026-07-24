"""Issue 280 PR B executable input/API/error contract slice."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.rag.chunking import checksum_text
from backend.app.stage4 import contains_prompt_injection, contains_secret_like_content, normalize_content_type

ISSUE280_INPUT_CONTRACT_PATH = "/api/v1/checkpoint3/issue280/input-contract"
ISSUE280_CONTRACT_VERSION = "issue280-input-api-error-v1"
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
    evidence_level: Literal["input-api-error-contract"] = Field(alias="evidenceLevel")
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
