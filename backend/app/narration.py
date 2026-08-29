"""Fail-closed Cut 1 narration review and speech-authority domain."""
from __future__ import annotations
import hashlib
import json
import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any, NoReturn, cast

from backend.app.cut1_grounding import CUT1_POLICY_VERSION, CUT1_STYLE, PRESENTERS
from backend.app.evaluation_lineage import build_source_evaluation_checksum, derive_evaluation_lineage, validate_evaluation_lineage_payload
from backend.app.presenter_registry import PresenterRegistry, PresenterRegistryError, PresenterTraceBinding
from backend.app.rag.chunking import checksum_text
from backend.app.stage4 import LocalPrincipal, Stage4Service, WalkthroughRunRecord
from backend.app.storage import write_state

LOGGER = logging.getLogger(__name__)
SCHEMA = "cut1-narration-state-v1"
CHECKSUM_SCHEMA = "cut1-narration-checksum-v1"
EVALUATION_SCHEMA = "cut1-narration-evaluation-v1"
APPROVAL_SCHEMA = "cut1-speech-approval-v1"
RECEIPT_SCHEMA = "cut1-tts-text-authority-v1"
MAX_TEXT_BYTES = 16_384
MAX_STATE_BYTES = 4_194_304
MAX_PROJECTS = 64
MAX_VERSIONS_PER_PROJECT = 64
MAX_EVIDENCE_ITEMS = 128
MAX_ID_CHARS = 128
DURATION_REQUIREMENT_SECONDS = (90, 120)
BRAND_NAME = "StackClimb"
BRAND_DOMAIN = "stackclimb.com"
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
SHA_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
BARE_SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
CITATION_PATTERN = re.compile(r"\[(\d+)\]")

CANONICAL_MEERA_TEXT = """Hello, everyone, and a very warm welcome to NarraTwin AI. I’m Meera, and I’ll be your host for this walkthrough.

StackClimb is the technology and product innovation brand founded, owned, and led by Rohit Agrawal. NarraTwin AI is a product he conceived, owns, and produces under StackClimb.

Complex projects often contain valuable knowledge spread across documents, code, architecture notes, and technical decisions. NarraTwin AI is designed to turn that information into a clear, guided project walkthrough.

The process begins with approved project material. NarraTwin organizes the content, retrieves the most relevant context, and creates an audience-aware explanation. Important claims are evaluated against their supporting sources, helping the walkthrough remain transparent and grounded instead of presenting unsupported information as fact.

The application combines a Python and FastAPI backend, a Next.js user experience, retrieval-augmented generation, evaluation and safety controls, multilingual content, captions, speech, and presenter-led media. NarraTwin keeps project understanding at its core and is being built with modular provider boundaries, so generation and presentation technologies can evolve over time.

This approach can also be applied to other projects. Once their approved documentation is supplied, NarraTwin can create a tailored explanation of their purpose, architecture, technologies, capabilities, important decisions, and possible integrations.

For this first experience, I’m presenting a prepared walkthrough. Interactive questions and answers are planned as a future capability and are not part of this demonstration.

That is NarraTwin AI: a StackClimb product designed to transform approved project knowledge into clear, grounded, presenter-led experiences. I’m Meera. Thank you for joining me, and I look forward to guiding you through more projects."""
CANONICAL_HASHES = {"meera": "3edffc6169460546ae0bdee867fdeaf3c0ae383535e2976e0333f39c03ff614e",
    "myra": "0cabff207582e80770b798fbb7e90d008e3d9c20f7cb1872773df3b1c6527d71",
    "raj": "42fb220d7dda293c3be551bd14e3292f0449e0a649079a4d36ee67203f370e49"}
INVALIDATED_AUTHORITIES = ("EVALUATION", "SPEECH_APPROVAL", "TTS_AUDIO", "CAPTION", "RENDER", "VIDEO_EXPORT", "REPLAY")
class NarrationState(StrEnum):
    DRAFT = "DRAFT"
    EVALUATION_REQUIRED = "EVALUATION_REQUIRED"
    EVALUATED = "EVALUATED"
    APPROVED_FOR_SPEECH = "APPROVED_FOR_SPEECH"
    CONSUMED_BY_TTS = "CONSUMED_BY_TTS"
class NarrationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
@dataclass(frozen=True)
class NarrationEvaluation:
    evaluation_id: str
    result: str
    reason_codes: tuple[str, ...]
    narration_checksum: str
    source_evaluation_id: str
    source_evaluation_checksum: str
    schema_version: str
    policy_version: str
    checksum: str
@dataclass(frozen=True)
class SpeechApproval:
    approver_id: str
    approved_at: str
    narration_checksum: str
    evaluation_checksum: str
    checksum: str
@dataclass(frozen=True)
class NarrationVersion:
    tenant_id: str
    actor_id: str
    project_id: str
    version: int
    presenter_id: str
    presenter_version: str
    presenter_binding: PresenterTraceBinding
    registry_sha256: str
    review_text: str
    spoken_text: str
    source_run_id: str
    source_request_checksum: str
    source_trace_id: str
    source_lineage_json: str
    claim_evidence_json: str
    source_evaluation_id: str
    source_evaluation_checksum: str
    context_ref_ids: tuple[str, ...]
    citation_indexes: tuple[int, ...]
    claim_support_ids: tuple[str, ...]
    narration_checksum: str
    state: NarrationState
    evaluation: NarrationEvaluation | None = None
    approval: SpeechApproval | None = None
    invalidated_authorities: tuple[str, ...] = ()
    invalidated_version: int | None = None
    invalidated_checksum: str | None = None
    def checksum_payload(self) -> dict[str, Any]:
        return {
            "schema": CHECKSUM_SCHEMA,
            "brand": {"domain": BRAND_DOMAIN, "name": BRAND_NAME},
            "scope": {"actorId": self.actor_id, "projectId": self.project_id,
                      "tenantId": self.tenant_id},
            "presenter": asdict(self.presenter_binding),
            "narration": {
                "presenterId": self.presenter_id, "presenterVersion": self.presenter_version,
                "registrySha256": self.registry_sha256, "reviewText": self.review_text,
                "reviewTextSha256": checksum_text(self.review_text), "spokenText": self.spoken_text,
                "spokenTextSha256": checksum_text(self.spoken_text), "version": self.version,
                "invalidatedAuthorities": list(self.invalidated_authorities),
                "invalidatedVersion": self.invalidated_version,
                "invalidatedChecksum": self.invalidated_checksum,
            },
            "source": {
                "citationIndexes": list(self.citation_indexes),
                "claimSupportIds": list(self.claim_support_ids),
                "claimEvidenceJson": self.claim_evidence_json,
                "contextRefIds": list(self.context_ref_ids),
                "evaluationId": self.source_evaluation_id,
                "evaluationChecksum": self.source_evaluation_checksum,
                "lineageJson": self.source_lineage_json, "requestChecksum": self.source_request_checksum,
                "runId": self.source_run_id, "traceId": self.source_trace_id,
            },
            "downstream": {"measuredAudioSeconds": [90, 120], "status": "REQUIREMENT_ONLY"},
        }
@dataclass(frozen=True)
class TTSConsumptionReceipt:
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
    spoken_text: str
    duration_requirement_seconds: tuple[int, int]
    receipt_checksum: str
class _DuplicateKey(ValueError):
    pass
def _fail(code: str, message: str) -> NoReturn:
    raise NarrationError(code, message)
def _sha(payload: Mapping[str, Any], *, schema: str | None = None) -> str:
    value = dict(payload)
    if schema is not None:
        value = {"schema": schema, "value": value}
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
def checksum_payload(payload: Mapping[str, Any]) -> str:
    return _sha(payload)
def authoritative_leaf_paths(value: Any, path: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    if isinstance(value, dict):
        return [leaf for key, child in value.items() for leaf in authoritative_leaf_paths(child, (*path, key))]
    if isinstance(value, list):
        return [leaf for key, child in enumerate(value) for leaf in authoritative_leaf_paths(child, (*path, key))]
    return [path]
def canonical_presenter_text(presenter_id: str) -> str:
    if presenter_id not in CANONICAL_HASHES:
        _fail("PRESENTER_INVALID", "Presenter is not authorized for Cut 1 narration.")
    if CANONICAL_MEERA_TEXT.count("Meera") != 2:
        _fail("CANONICAL_NARRATION_DRIFT", "Canonical presenter token count drifted.")
    value = CANONICAL_MEERA_TEXT if presenter_id == "meera" else CANONICAL_MEERA_TEXT.replace(
        "Meera", presenter_id.title()
    )
    if hashlib.sha256(value.encode()).hexdigest() != CANONICAL_HASHES[presenter_id]:
        _fail("CANONICAL_NARRATION_DRIFT", "Canonical narration bytes drifted.")
    return value
def validate_canonical_text(presenter_id: str, value: str) -> str:
    if value != canonical_presenter_text(presenter_id):
        _fail("CANONICAL_NARRATION_DRIFT", "Canonical narration bytes drifted.")
    return value
def spoken_projection(review_text: str, validated_indexes: tuple[int, ...]) -> str:
    allowed = set(validated_indexes)
    return re.sub(
        r"\s*\[(\d+)\]",
        lambda match: "" if int(match.group(1)) in allowed else match.group(0),
        review_text,
    )
def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result
def _object(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Noncanonical object fields.")
    return cast(dict[str, Any], value)
def _identifier(value: Any) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
        raise ValueError("Invalid identifier.")
    return value
def _checksum(value: Any, *, bare: bool = False) -> str:
    pattern = BARE_SHA_PATTERN if bare else SHA_PATTERN
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError("Invalid checksum.")
    return value
def _text(value: Any) -> str:
    try:
        size = len(value.encode("utf-8")) if isinstance(value, str) else 0
    except UnicodeEncodeError:
        size = 0
    if not isinstance(value, str) or not value.strip() or not 0 < size <= MAX_TEXT_BYTES:
        _fail("TEXT_INVALID", "Narration text is empty or oversized.")
    return value
def _timestamp(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("Invalid timestamp.")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed) or parsed.isoformat() != value:
        raise ValueError("Invalid timestamp.")
    return value
def _current_timestamp(clock: Callable[[], datetime]) -> str:
    value = clock()
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        _fail("TIMESTAMP_INVALID", "Approval clock must produce UTC.")
    return value.isoformat()
class NarrationService:
    def __init__(self, *, stage4: Stage4Service, registry: PresenterRegistry,
                 state_path: Path | None = None, clock: Callable[[], datetime] | None = None) -> None:
        self.stage4, self.registry, self.state_path = stage4, registry, state_path
        self.clock = clock or (lambda: datetime.now(UTC))
        self._versions: dict[str, list[NarrationVersion]] = {}
        self._receipts: list[TTSConsumptionReceipt] = []
        self._lock = RLock()
        self._restore()
    @property
    def authority_count(self) -> int:
        return sum(len(rows) for rows in self._versions.values())
    @property
    def receipt_count(self) -> int:
        return len(self._receipts)
    def latest(self, *, principal: LocalPrincipal, project_id: str) -> NarrationVersion:
        with self._lock:
            rows = self._versions.get(project_id, [])
            if not rows:
                _fail("AUTHORITY_STALE", "No current narration authority exists.")
            row = rows[-1]
            self._scope(row, principal, project_id)
            return row
    def create_draft(self, *, principal: LocalPrincipal, project_id: str, source_run_id: str,
                     presenter_binding: PresenterTraceBinding, review_text: str | None) -> NarrationVersion:
        with self._lock:
            if self._versions.get(project_id):
                _fail("LIFECYCLE_INVALID", "Existing narration must be edited into a new version.")
            return self._create(principal, project_id, source_run_id, presenter_binding, review_text,
                                1, (), None, None)
    def edit(self, *, principal: LocalPrincipal, project_id: str, source_run_id: str,
             presenter_binding: PresenterTraceBinding, review_text: str | None) -> NarrationVersion:
        with self._lock:
            current = self.latest(principal=principal, project_id=project_id)
            return self._create(principal, project_id, source_run_id, presenter_binding, review_text,
                                current.version + 1, INVALIDATED_AUTHORITIES,
                                current.version, current.narration_checksum)
    def _create(self, principal: LocalPrincipal, project_id: str, source_run_id: str,
                presenter_binding: PresenterTraceBinding, review_text: str | None, version: int,
                invalidations: tuple[str, ...], invalidated_version: int | None,
                invalidated_checksum: str | None) -> NarrationVersion:
        if len(self._versions) >= MAX_PROJECTS and project_id not in self._versions:
            _fail("RESOURCE_LIMIT", "Narration project limit reached.")
        if len(self._versions.get(project_id, ())) >= MAX_VERSIONS_PER_PROJECT:
            _fail("RESOURCE_LIMIT", "Narration version limit reached.")
        review = _text(review_text)
        _, run = self._source(principal, project_id, source_run_id)
        binding = self._presenter(presenter_binding)
        evaluation = cast(Any, run.evaluation)
        generated = cast(Any, run.generated_script)
        indexes = tuple(support.citation_index for support in evaluation.claim_supports)
        context_ids = tuple(context.context_ref_id for context in run.retrieved_context)
        support_ids = tuple(support.claim_support_id for support in evaluation.claim_supports)
        evidence_counts = (len(indexes), len(context_ids), len(support_ids), len(generated.claims))
        if (
            max(evidence_counts) > MAX_EVIDENCE_ITEMS
            or not indexes
            or len(indexes) != len(support_ids)
            or len(generated.claims) != len(evaluation.claim_supports)
            or len(generated.claims) != 18
            or len(support_ids) != len(set(support_ids))
            or any(
                not support.proposition_ids
                or support.proposition_evidence_checksum is None
                for support in evaluation.claim_supports
            )
        ):
            _fail("EVIDENCE_INVALID", "Narration evidence is missing, duplicated, or exceeds its bounded limit.")
        spoken = spoken_projection(review, indexes)
        if (
            binding.presenter_id not in PRESENTERS
            or spoken != canonical_presenter_text(binding.presenter_id)
        ):
            _fail("AUTHORITY_MISMATCH", "Narration source and presenter do not match.")
        lineage = derive_evaluation_lineage(run)
        lineage_json = json.dumps(lineage, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        source_checksum = build_source_evaluation_checksum(lineage)
        claim_evidence_json = json.dumps({"claims": [asdict(item) for item in generated.claims], "supports": [asdict(item) for item in evaluation.claim_supports]}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        row = NarrationVersion(
            principal.tenant_id, principal.actor_id, project_id, version,
            binding.presenter_id, binding.presenter_version, binding, binding.registry_sha256,
            review, spoken, run.run_id, _checksum(run.request_checksum),
            _identifier(run.trace_id), lineage_json, claim_evidence_json, _identifier(evaluation.evaluation_id), source_checksum,
            context_ids, indexes, support_ids, "", NarrationState.DRAFT,
            invalidated_authorities=invalidations, invalidated_version=invalidated_version,
            invalidated_checksum=invalidated_checksum,
        )
        row = replace(row, narration_checksum=checksum_payload(row.checksum_payload()))
        self._versions.setdefault(project_id, []).append(row)
        self._persist_or_rollback(project_id)
        self._log("created", row)
        return row
    def request_evaluation(self, *, principal: LocalPrincipal, project_id: str,
                           narration_version: int, narration_checksum: str) -> NarrationVersion:
        with self._lock:
            row = self._required(principal, project_id, narration_version, narration_checksum,
                                 NarrationState.DRAFT)
            return self._transition(row, state=NarrationState.EVALUATION_REQUIRED, event="evaluation_required")
    def evaluate(self, *, principal: LocalPrincipal, project_id: str,
                 narration_version: int, narration_checksum: str) -> NarrationVersion:
        with self._lock:
            row = self._required(principal, project_id, narration_version, narration_checksum,
                                 NarrationState.EVALUATION_REQUIRED)
            reasons = self._binding_failures(row)
            result = "FAILED" if reasons else "PASSED"
            payload = {
                "evaluationId": f"narr_eval_{row.version}", "narrationChecksum": row.narration_checksum,
                "policyVersion": EVALUATION_SCHEMA, "reasonCodes": list(reasons), "result": result,
                "schemaVersion": EVALUATION_SCHEMA, "sourceEvaluationChecksum": row.source_evaluation_checksum,
                "sourceEvaluationId": row.source_evaluation_id,
            }
            evaluation = NarrationEvaluation(
                f"narr_eval_{row.version}", result, reasons, row.narration_checksum,
                row.source_evaluation_id, row.source_evaluation_checksum, EVALUATION_SCHEMA,
                EVALUATION_SCHEMA, _sha(payload),
            )
            return self._transition(row, state=NarrationState.EVALUATED,
                                    evaluation=evaluation, event="evaluated")
    def approve_for_speech(self, *, principal: LocalPrincipal, project_id: str,
                           narration_version: int, narration_checksum: str,
                           approver_id: str) -> NarrationVersion:
        with self._lock:
            row = self._required(principal, project_id, narration_version, narration_checksum,
                                 NarrationState.EVALUATED)
            if approver_id != row.actor_id or _identifier(approver_id) != approver_id:
                _fail("AUTHORITY_MISMATCH", "Approver identity does not match the narration actor.")
            if row.evaluation is None or row.evaluation.result != "PASSED" or not _evaluation_current(row) or self._binding_failures(row):
                _fail("EVALUATION_FAILED", "Current narration evaluation is not passing.")
            evaluation = row.evaluation
            approved_at = _current_timestamp(self.clock)
            payload = {"approvedAt": approved_at, "approverId": approver_id,
                       "evaluationChecksum": evaluation.checksum,
                       "narrationChecksum": row.narration_checksum, "schema": APPROVAL_SCHEMA}
            approval = SpeechApproval(approver_id, approved_at, row.narration_checksum,
                                      evaluation.checksum, _sha(payload))
            return self._transition(row, state=NarrationState.APPROVED_FOR_SPEECH,
                                    approval=approval, event="approved")
    def consume_for_tts(self, *, principal: LocalPrincipal, project_id: str,
                        narration_version: int, narration_checksum: str,
                        request_id: str, trace_id: str) -> TTSConsumptionReceipt:
        with self._lock:
            row = self._current(principal, project_id, narration_version, narration_checksum)
            if row.state is NarrationState.CONSUMED_BY_TTS:
                _fail("CONSUMPTION_REPLAY", "Narration text authority was already consumed.")
            if row.state is not NarrationState.APPROVED_FOR_SPEECH:
                _fail("LIFECYCLE_INVALID", "Narration is not approved for speech.")
            self._presenter(row.presenter_binding)
            if self._binding_failures(row) or not _evaluation_current(row) or not _approval_current(row):
                _fail("AUTHORITY_MISMATCH", "Narration authority is stale or incomplete.")
            evaluation, approval = cast(NarrationEvaluation, row.evaluation), cast(SpeechApproval, row.approval)
            request, trace = _identifier(request_id), _identifier(trace_id)
            payload = {
                "approvalChecksum": approval.checksum, "evaluationChecksum": evaluation.checksum,
                "narrationChecksum": row.narration_checksum, "presenterBindingChecksum": row.presenter_binding.binding_sha256,
                "presenterId": row.presenter_id, "presenterVersion": row.presenter_version,
                "projectId": row.project_id, "requestId": request, "schema": RECEIPT_SCHEMA,
                "sourceEvaluationChecksum": row.source_evaluation_checksum, "sourceRunId": row.source_run_id,
                "spokenText": row.spoken_text, "tenantId": row.tenant_id, "actorId": row.actor_id,
                "traceId": trace, "version": row.version,
            }
            receipt = TTSConsumptionReceipt(
                row.tenant_id, row.actor_id, row.project_id, row.version, row.narration_checksum,
                row.presenter_id, row.presenter_version, row.presenter_binding.binding_sha256,
                row.source_run_id, row.source_evaluation_checksum, evaluation.checksum,
                approval.checksum, request, trace, row.spoken_text,
                DURATION_REQUIREMENT_SECONDS, _sha(payload),
            )
            consumed = replace(row, state=NarrationState.CONSUMED_BY_TTS)
            self._replace(consumed)
            self._receipts.append(receipt)
            try:
                self._persist()
            except Exception:
                self._receipts.pop()
                self._replace(row)
                raise
            self._log("consumed", consumed)
            return receipt
    def validate_tts_consumption_receipt(self, *, principal: LocalPrincipal,
                                         receipt: TTSConsumptionReceipt) -> TTSConsumptionReceipt:
        """Revalidate persisted speech authority without creating a second receipt."""
        with self._lock:
            if not isinstance(receipt, TTSConsumptionReceipt):
                _fail("AUTHORITY_MISMATCH", "TTS receipt is malformed.")
            row = self._current(
                principal,
                receipt.project_id,
                receipt.version,
                receipt.narration_checksum,
            )
            if row.state is not NarrationState.CONSUMED_BY_TTS:
                _fail("AUTHORITY_MISMATCH", "TTS receipt is not current.")
            try:
                self._presenter(row.presenter_binding)
            except NarrationError:
                _fail("AUTHORITY_MISMATCH", "TTS receipt authority is stale or incomplete.")
            if self._binding_failures(row) or not _evaluation_current(row) or not _approval_current(row):
                _fail("AUTHORITY_MISMATCH", "TTS receipt authority is stale or incomplete.")
            if receipt not in self._receipts or not _receipt_matches_version(receipt, row):
                _fail("AUTHORITY_MISMATCH", "TTS receipt is stale or mismatched.")
            if _receipt_checksum(receipt) != receipt.receipt_checksum:
                _fail("AUTHORITY_MISMATCH", "TTS receipt checksum is invalid.")
            return receipt
    def _required(self, principal: LocalPrincipal, project_id: str, narration_version: int,
                  narration_checksum: str, state: NarrationState) -> NarrationVersion:
        row = self._current(principal, project_id, narration_version, narration_checksum)
        if row.state is not state:
            _fail("LIFECYCLE_INVALID", "Narration lifecycle transition is illegal.")
        return row
    def _current(self, principal: LocalPrincipal, project_id: str, version: int,
                 digest: str) -> NarrationVersion:
        if not isinstance(principal, LocalPrincipal) or not isinstance(project_id, str):
            _fail("AUTHORITY_MISMATCH", "Narration scope is malformed.")
        rows = self._versions.get(project_id, [])
        if not rows:
            _fail("AUTHORITY_MISMATCH", "Narration authority does not match this scope.")
        row = rows[-1]
        self._scope(row, principal, project_id)
        if type(version) is not int or version != row.version:
            code = "AUTHORITY_STALE" if type(version) is int and version < row.version else "AUTHORITY_MISMATCH"
            _fail(code, "Narration version is not current.")
        if digest != row.narration_checksum or checksum_payload(row.checksum_payload()) != row.narration_checksum:
            _fail("AUTHORITY_MISMATCH", "Narration checksum is stale or mismatched.")
        return row
    def _scope(self, row: NarrationVersion, principal: LocalPrincipal, project_id: str) -> None:
        project = self.stage4.projects.get(project_id)
        if project is None or (row.tenant_id, row.actor_id, row.project_id) != (
            principal.tenant_id, principal.actor_id, project_id
        ) or (project.tenant_id, project.owner_id) != (principal.tenant_id, principal.actor_id):
            _fail("AUTHORITY_MISMATCH", "Narration authority does not match this scope.")
    def _source(self, principal: LocalPrincipal, project_id: str,
                run_id: str) -> tuple[Any, WalkthroughRunRecord]:
        project = self.stage4.projects.get(project_id)
        run = self.stage4.walkthrough_runs.get(run_id)
        if project is None or run is None or (project.tenant_id, project.owner_id) != (
            principal.tenant_id, principal.actor_id
        ) or (run.tenant_id, run.actor_id, run.project_id) != (
            principal.tenant_id, principal.actor_id, project_id
        ):
            _fail("AUTHORITY_MISMATCH", "Stage 4 narration source does not match this scope.")
        evaluation = run.evaluation
        if (
            run.status != "COMPLETED"
            or run.failure_reason is not None
            or run.evaluation_status != "PASSED"
            or run.style != CUT1_STYLE
            or run.generated_script is None
            or run.accepted_script_text != run.generated_script.text
            or evaluation is None
            or evaluation.evaluation_status != "PASSED"
            or evaluation.policy_version != CUT1_POLICY_VERSION
        ):
            _fail("AUTHORITY_MISMATCH", "Stage 4 narration source is not governed Cut 1 authority.")
        return project, run
    def _presenter(self, binding: PresenterTraceBinding) -> PresenterTraceBinding:
        try:
            identity = self.registry.get(binding.presenter_id, binding.presenter_version)
        except (AttributeError, PresenterRegistryError, TypeError):
            _fail("PRESENTER_INACTIVE", "Narration presenter is not currently active.")
        asset = identity.asset
        values = {
            "presenter_id": binding.presenter_id, "presenter_version": binding.presenter_version,
            "trace_id": binding.trace_id, "asset_sha256": binding.asset_sha256,
            "voice_reference_id": binding.voice_reference_id,
            "voice_reference_version": binding.voice_reference_version,
            "registry_version": binding.registry_version, "registry_sha256": binding.registry_sha256,
        }
        expected = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if asset is None or (binding.asset_sha256, binding.voice_reference_id,
                             binding.voice_reference_version, binding.registry_version,
                             binding.registry_sha256, binding.binding_sha256) != (
            asset.sha256, identity.voice.reference_id, identity.voice.version,
            self.registry.registry_version, self.registry.manifest_sha256, expected,
        ):
            _fail("AUTHORITY_MISMATCH", "Narration presenter binding is stale or mismatched.")
        return binding
    def _binding_failures(self, row: NarrationVersion) -> tuple[str, ...]:
        try:
            project, run = self._source(LocalPrincipal(row.tenant_id, row.actor_id),
                                        row.project_id, row.source_run_id)
            self._presenter(row.presenter_binding)
            if not self.stage4.cut1_run_authority_is_current(run):
                return ("GROUNDING_OR_BINDING_STALE",)
            lineage = derive_evaluation_lineage(run)
            lineage_json = json.dumps(lineage, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            evaluation = cast(Any, run.evaluation)
            claim_evidence_json = json.dumps({"claims": [asdict(item) for item in cast(Any, run.generated_script).claims], "supports": [asdict(item) for item in evaluation.claim_supports]}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            indexes = tuple(support.citation_index for support in evaluation.claim_supports)
            markers = tuple(int(value) for value in CITATION_PATTERN.findall(row.review_text))
            valid = (
                row.presenter_id in PRESENTERS
                and run.style == CUT1_STYLE
                and evaluation.policy_version == CUT1_POLICY_VERSION
                and len(cast(Any, run.generated_script).claims) == len(evaluation.claim_supports) == 18
                and all(
                    support.proposition_ids and support.proposition_evidence_checksum
                    for support in evaluation.claim_supports
                )
                and run.accepted_script_text == row.review_text
                and run.request_checksum == row.source_request_checksum and run.trace_id == row.source_trace_id
                and lineage_json == row.source_lineage_json
                and build_source_evaluation_checksum(lineage) == row.source_evaluation_checksum
                and claim_evidence_json == row.claim_evidence_json
                and evaluation.evaluation_id == row.source_evaluation_id
                and tuple(context.context_ref_id for context in run.retrieved_context) == row.context_ref_ids
                and tuple(support.claim_support_id for support in evaluation.claim_supports) == row.claim_support_ids
                and indexes == row.citation_indexes == markers
                and spoken_projection(row.review_text, indexes) == row.spoken_text
                and BRAND_NAME in row.spoken_text and BRAND_DOMAIN not in row.spoken_text
                and project.name in row.spoken_text
            )
            canonical = canonical_presenter_text(row.presenter_id)
            valid = valid and project.name == "NarraTwin AI" and row.spoken_text == canonical
            return () if valid else ("GROUNDING_OR_BINDING_STALE",)
        except (NarrationError, PresenterRegistryError, TypeError, ValueError):
            return ("GROUNDING_OR_BINDING_STALE",)
    def _transition(self, row: NarrationVersion, *, state: NarrationState, event: str,
                    evaluation: NarrationEvaluation | None = None,
                    approval: SpeechApproval | None = None) -> NarrationVersion:
        updated = replace(row, state=state, evaluation=evaluation or row.evaluation,
                          approval=approval or row.approval)
        self._replace(updated)
        try:
            self._persist()
        except Exception:
            self._replace(row)
            raise
        self._log(event, updated)
        return updated
    def _replace(self, row: NarrationVersion) -> None:
        self._versions[row.project_id][-1] = row
    def _persist_or_rollback(self, project_id: str) -> None:
        try:
            self._persist()
        except Exception:
            rows = self._versions[project_id]
            rows.pop()
            if not rows:
                self._versions.pop(project_id)
            raise
    def _persist(self) -> None:
        payload = {"schema": SCHEMA, "receipts": [_receipt_to_row(row) for row in self._receipts],
            "versions": [_version_to_row(row) for rows in self._versions.values() for row in rows]}
        write_state(self.state_path, payload)
    def _restore(self) -> None:
        if self.state_path is None or not self.state_path.exists():
            return
        try:
            if self.state_path.is_symlink() or not self.state_path.is_file() \
                    or self.state_path.stat().st_size > MAX_STATE_BYTES:
                raise ValueError("Unsafe narration state file.")
            with self.state_path.open("rb") as stream:
                data = stream.read(MAX_STATE_BYTES + 1)
            payload = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
            root = _object(payload, {"schema", "versions", "receipts"})
            if root["schema"] != SCHEMA or not isinstance(root["versions"], list) \
                    or not isinstance(root["receipts"], list):
                raise ValueError("Narration state schema mismatch.")
            versions = [_version_from_row(row) for row in root["versions"]]
            receipts = [_receipt_from_row(row) for row in root["receipts"]]
            if len({row.project_id for row in versions}) > MAX_PROJECTS \
                    or max(len(versions), len(receipts)) > MAX_PROJECTS * MAX_VERSIONS_PER_PROJECT:
                raise ValueError("Narration state count exceeded.")
            restored: dict[str, list[NarrationVersion]] = {}
            for row in versions:
                rows = restored.setdefault(row.project_id, [])
                if row.version != len(rows) + 1 or checksum_payload(row.checksum_payload()) != row.narration_checksum or bool(rows) != bool(row.invalidated_authorities):
                    raise ValueError("Narration version chain is invalid.")
                if rows and (row.invalidated_version, row.invalidated_checksum) != (
                    rows[-1].version, rows[-1].narration_checksum
                ):
                    raise ValueError("Narration invalidation chain is invalid.")
                rows.append(row)
            self._versions, self._receipts = restored, receipts
            if any(self._binding_failures(row) for rows in restored.values() for row in rows):
                raise ValueError("Narration external authority is stale.")
            by_key = {(row.project_id, row.version): row for rows in restored.values() for row in rows}
            consumed_keys = {key for key, row in by_key.items() if row.state is NarrationState.CONSUMED_BY_TTS}
            receipt_keys: set[tuple[str, int]] = set()
            for receipt in receipts:
                key = (receipt.project_id, receipt.version)
                version = by_key.get(key)
                if key in receipt_keys or version is None or version.state is not NarrationState.CONSUMED_BY_TTS \
                        or _receipt_checksum(receipt) != receipt.receipt_checksum \
                        or not _receipt_matches_version(receipt, version):
                    raise ValueError("Narration receipt is invalid.")
                receipt_keys.add(key)
            if receipt_keys != consumed_keys:
                raise ValueError("Narration consumed authority and receipts are incomplete.")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, _DuplicateKey,
                KeyError, TypeError, ValueError, NarrationError):
            self._versions, self._receipts = {}, []
            LOGGER.warning("narration_event event=restore_refused code=STATE_INVALID")
    @staticmethod
    def _log(event: str, row: NarrationVersion) -> None:
        LOGGER.info("narration_event event=%s project=%s version=%d state=%s digest=%s",
                    event, row.project_id[:MAX_ID_CHARS], row.version, row.state, row.narration_checksum)
def _version_to_row(row: NarrationVersion) -> dict[str, Any]:
    return {"content": row.checksum_payload(), "narrationChecksum": row.narration_checksum,
            "state": row.state, "evaluation": asdict(row.evaluation) if row.evaluation else None,
            "approval": asdict(row.approval) if row.approval else None,
            "invalidatedAuthorities": list(row.invalidated_authorities)}
def _version_from_row(value: Any) -> NarrationVersion:
    row = _object(value, {"content", "narrationChecksum", "state", "evaluation", "approval",
                          "invalidatedAuthorities"})
    content = _object(row["content"], {"schema", "brand", "scope", "presenter", "narration",
                                      "source", "downstream"})
    if content["schema"] != CHECKSUM_SCHEMA or content["brand"] != {"domain": BRAND_DOMAIN, "name": BRAND_NAME} \
            or content["downstream"] != {"measuredAudioSeconds": [90, 120], "status": "REQUIREMENT_ONLY"}:
        raise ValueError("Narration content contract drifted.")
    scope = _object(content["scope"], {"actorId", "projectId", "tenantId"})
    narration = _object(content["narration"], {"presenterId", "presenterVersion", "registrySha256",
        "reviewText", "reviewTextSha256", "spokenText", "spokenTextSha256", "version",
        "invalidatedAuthorities", "invalidatedVersion", "invalidatedChecksum"})
    source = _object(content["source"], {"citationIndexes", "claimEvidenceJson", "claimSupportIds", "contextRefIds",
        "evaluationId", "evaluationChecksum", "lineageJson", "requestChecksum", "runId", "traceId"})
    binding_row = _object(content["presenter"], set(PresenterTraceBinding.__dataclass_fields__))
    binding = PresenterTraceBinding(**{key: _identifier(value) if "sha256" not in key else _checksum(value, bare=True)
                                      for key, value in binding_row.items()})
    version = narration["version"]
    if type(version) is not int or not 0 < version <= MAX_VERSIONS_PER_PROJECT:
        raise ValueError("Narration version is invalid.")
    review, spoken = _text(narration["reviewText"]), _text(narration["spokenText"])
    if narration["reviewTextSha256"] != checksum_text(review) or narration["spokenTextSha256"] != checksum_text(spoken):
        raise ValueError("Narration text checksum is invalid.")
    indexes = source["citationIndexes"]
    if not isinstance(indexes, list) or not indexes or len(indexes) > MAX_EVIDENCE_ITEMS \
            or any(type(item) is not int or item <= 0 for item in indexes):
        raise ValueError("Narration citations are invalid.")
    contexts = _id_list(source["contextRefIds"])
    supports = _id_list(source["claimSupportIds"])
    lineage_json = source["lineageJson"]
    if not isinstance(lineage_json, str) or len(lineage_json.encode()) > MAX_STATE_BYTES:
        raise ValueError("Narration lineage is invalid.")
    lineage = json.loads(lineage_json, object_pairs_hook=_pairs)
    canonical = validate_evaluation_lineage_payload(lineage)
    if json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")) != lineage_json \
            or build_source_evaluation_checksum(canonical) != source["evaluationChecksum"]:
        raise ValueError("Narration lineage checksum is invalid.")
    evaluation = _evaluation_from_row(row["evaluation"])
    approval = _approval_from_row(row["approval"])
    invalidations = row["invalidatedAuthorities"]
    if not isinstance(invalidations, list) or tuple(invalidations) not in {(), INVALIDATED_AUTHORITIES} \
            or invalidations != narration["invalidatedAuthorities"]:
        raise ValueError("Narration invalidations are invalid.")
    invalidated_version = narration["invalidatedVersion"]
    invalidated_checksum = narration["invalidatedChecksum"]
    if ((not invalidations and (invalidated_version is not None or invalidated_checksum is not None))
            or (invalidations and (type(invalidated_version) is not int
                or invalidated_version != version - 1 or not isinstance(invalidated_checksum, str)))):
        raise ValueError("Narration invalidation binding is invalid.")
    state = NarrationState(row["state"])
    result = NarrationVersion(
        _identifier(scope["tenantId"]), _identifier(scope["actorId"]), _identifier(scope["projectId"]),
        version, _identifier(narration["presenterId"]), _identifier(narration["presenterVersion"]),
        binding, _checksum(narration["registrySha256"], bare=True), review, spoken,
        _identifier(source["runId"]), _checksum(source["requestChecksum"]), _identifier(source["traceId"]),
        lineage_json, cast(str, source["claimEvidenceJson"]), _identifier(source["evaluationId"]), _checksum(source["evaluationChecksum"]),
        contexts, tuple(indexes), supports, _checksum(row["narrationChecksum"]), state,
        evaluation, approval, tuple(invalidations), invalidated_version,
        _checksum(invalidated_checksum) if invalidated_checksum is not None else None,
    )
    if not _legal_state_shape(result) or (evaluation is not None and not _evaluation_current(result)) \
            or (approval is not None and not _approval_current(result)):
        raise ValueError("Narration lifecycle shape is invalid.")
    return result
def _id_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or len(value) > MAX_EVIDENCE_ITEMS:
        raise ValueError("Narration evidence list is invalid.")
    result = tuple(_identifier(item) for item in value)
    if len(set(result)) != len(result):
        raise ValueError("Narration evidence identity is duplicated.")
    return result
def _evaluation_from_row(value: Any) -> NarrationEvaluation | None:
    if value is None:
        return None
    row = _object(value, set(NarrationEvaluation.__dataclass_fields__))
    reasons = row["reason_codes"]
    if not isinstance(reasons, list) or len(reasons) > MAX_EVIDENCE_ITEMS:
        raise ValueError("Narration evaluation reasons are invalid.")
    payload = {"evaluationId": _identifier(row["evaluation_id"]),
        "narrationChecksum": _checksum(row["narration_checksum"]),
        "policyVersion": _identifier(row["policy_version"]), "reasonCodes": reasons,
        "result": row["result"], "schemaVersion": _identifier(row["schema_version"]),
        "sourceEvaluationChecksum": _checksum(row["source_evaluation_checksum"]),
        "sourceEvaluationId": _identifier(row["source_evaluation_id"])}
    if row["result"] not in {"PASSED", "FAILED"} or _sha(payload) != row["checksum"]:
        raise ValueError("Narration evaluation is invalid.")
    return NarrationEvaluation(payload["evaluationId"], row["result"], tuple(reasons),
        payload["narrationChecksum"], payload["sourceEvaluationId"], payload["sourceEvaluationChecksum"],
        payload["schemaVersion"], payload["policyVersion"], _checksum(row["checksum"]))
def _approval_from_row(value: Any) -> SpeechApproval | None:
    if value is None:
        return None
    row = _object(value, set(SpeechApproval.__dataclass_fields__))
    payload = {"approvedAt": _timestamp(row["approved_at"]), "approverId": _identifier(row["approver_id"]),
        "evaluationChecksum": _checksum(row["evaluation_checksum"]),
        "narrationChecksum": _checksum(row["narration_checksum"]), "schema": APPROVAL_SCHEMA}
    if _sha(payload) != row["checksum"]:
        raise ValueError("Narration approval is invalid.")
    return SpeechApproval(payload["approverId"], payload["approvedAt"], payload["narrationChecksum"],
                          payload["evaluationChecksum"], _checksum(row["checksum"]))
def _legal_state_shape(row: NarrationVersion) -> bool:
    return ((row.state in {NarrationState.DRAFT, NarrationState.EVALUATION_REQUIRED}
             and row.evaluation is None and row.approval is None)
            or (row.state is NarrationState.EVALUATED and row.evaluation is not None and row.approval is None)
            or (row.state in {NarrationState.APPROVED_FOR_SPEECH, NarrationState.CONSUMED_BY_TTS}
                and row.evaluation is not None and row.evaluation.result == "PASSED" and row.approval is not None))
def _evaluation_current(row: NarrationVersion) -> bool:
    value = row.evaluation
    if value is None or value.result not in {"PASSED", "FAILED"}:
        return False
    payload = {"evaluationId": value.evaluation_id, "narrationChecksum": value.narration_checksum,
        "policyVersion": value.policy_version, "reasonCodes": list(value.reason_codes),
        "result": value.result, "schemaVersion": value.schema_version,
        "sourceEvaluationChecksum": value.source_evaluation_checksum,
        "sourceEvaluationId": value.source_evaluation_id}
    return (value.narration_checksum, value.source_evaluation_id, value.source_evaluation_checksum,
            value.schema_version, value.policy_version, value.checksum) == (
        row.narration_checksum, row.source_evaluation_id, row.source_evaluation_checksum,
        EVALUATION_SCHEMA, EVALUATION_SCHEMA, _sha(payload))
def _approval_current(row: NarrationVersion) -> bool:
    value, evaluation = row.approval, row.evaluation
    if value is None or evaluation is None:
        return False
    payload = {"approvedAt": value.approved_at, "approverId": value.approver_id,
        "evaluationChecksum": value.evaluation_checksum,
        "narrationChecksum": value.narration_checksum, "schema": APPROVAL_SCHEMA}
    try:
        canonical_time = _timestamp(value.approved_at)
    except (TypeError, ValueError):
        return False
    return canonical_time == value.approved_at and (
        value.approver_id, value.narration_checksum, value.evaluation_checksum, value.checksum
    ) == (row.actor_id, row.narration_checksum, evaluation.checksum, _sha(payload))
def _receipt_to_row(row: TTSConsumptionReceipt) -> dict[str, Any]:
    return asdict(row)
def _receipt_from_row(value: Any) -> TTSConsumptionReceipt:
    row = _object(value, set(TTSConsumptionReceipt.__dataclass_fields__))
    duration = row["duration_requirement_seconds"]
    if duration != [90, 120]:
        raise ValueError("Narration duration requirement drifted.")
    return TTSConsumptionReceipt(
        _identifier(row["tenant_id"]), _identifier(row["actor_id"]), _identifier(row["project_id"]),
        row["version"] if type(row["version"]) is int else cast(int, None),
        _checksum(row["narration_checksum"]), _identifier(row["presenter_id"]),
        _identifier(row["presenter_version"]), _checksum(row["presenter_binding_checksum"], bare=True),
        _identifier(row["source_run_id"]), _checksum(row["source_evaluation_checksum"]),
        _checksum(row["evaluation_checksum"]), _checksum(row["approval_checksum"]),
        _identifier(row["request_id"]), _identifier(row["trace_id"]), _text(row["spoken_text"]),
        DURATION_REQUIREMENT_SECONDS, _checksum(row["receipt_checksum"]),
    )
def _receipt_checksum(row: TTSConsumptionReceipt) -> str:
    payload = {"approvalChecksum": row.approval_checksum, "evaluationChecksum": row.evaluation_checksum,
        "narrationChecksum": row.narration_checksum, "presenterBindingChecksum": row.presenter_binding_checksum,
        "presenterId": row.presenter_id, "presenterVersion": row.presenter_version,
        "projectId": row.project_id, "requestId": row.request_id, "schema": RECEIPT_SCHEMA,
        "sourceEvaluationChecksum": row.source_evaluation_checksum, "sourceRunId": row.source_run_id,
        "spokenText": row.spoken_text, "tenantId": row.tenant_id, "actorId": row.actor_id,
        "traceId": row.trace_id, "version": row.version}
    return _sha(payload)
def _receipt_matches_version(receipt: TTSConsumptionReceipt, row: NarrationVersion) -> bool:
    evaluation, approval = row.evaluation, row.approval
    return evaluation is not None and approval is not None and (
        receipt.tenant_id, receipt.actor_id, receipt.project_id, receipt.version,
        receipt.narration_checksum, receipt.presenter_id, receipt.presenter_version,
        receipt.presenter_binding_checksum, receipt.source_run_id, receipt.source_evaluation_checksum,
        receipt.evaluation_checksum, receipt.approval_checksum, receipt.spoken_text,
    ) == (
        row.tenant_id, row.actor_id, row.project_id, row.version, row.narration_checksum,
        row.presenter_id, row.presenter_version, row.presenter_binding.binding_sha256,
        row.source_run_id, row.source_evaluation_checksum, evaluation.checksum,
        approval.checksum, row.spoken_text,
    )
