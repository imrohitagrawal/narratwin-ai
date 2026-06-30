"""Claim-level grounding evaluation for generated scripts."""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.app.rag.models import (
    ClaimSupport,
    EvaluationResult,
    GeneratedScript,
    RetrievedContext,
    UnsupportedClaim,
)

GROUNDING_POLICY_VERSION = "stage4-grounding-policy-v1"
EVALUATION_SCHEMA_VERSION = "stage4-evaluation-schema-v1"
SAFETY_POLICY_VERSION = "stage4-safety-policy-v1"


def evaluate_grounding(
    *,
    tenant_id: str,
    project_id: str,
    run_id: str,
    candidate: GeneratedScript,
    retrieved_context: list[RetrievedContext],
) -> EvaluationResult:
    context_by_chunk = {context.chunk.chunk_id: context for context in retrieved_context}
    context_by_citation_index = {
        index: context for index, context in enumerate(retrieved_context, start=1)
    }
    unsupported_claims: list[UnsupportedClaim] = []
    claim_supports: list[ClaimSupport] = []
    matched_claim_ids: set[str] = set()
    failed_sentence_claim_ids: set[str] = set()

    for sentence_index, sentence in enumerate(_script_sentences(candidate.text), start=1):
        matching_claims = [
            claim
            for claim in candidate.claims
            if _spans_overlap(
                sentence.start,
                sentence.end,
                claim.script_span_start,
                claim.script_span_end,
            )
            or _normalize(claim.text) in _normalize(sentence.text)
        ]
        if not matching_claims:
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=f"script_span_{sentence_index:03d}",
                    claim_text=sentence.text,
                    reason="Visible generated script text has no provider claim metadata.",
                )
            )
            continue
        markers = _citation_markers(sentence.text)
        if len(markers) != 1:
            failed_sentence_claim_ids.add(matching_claims[0].claim_id)
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=matching_claims[0].claim_id,
                    claim_text=sentence.text,
                    reason="Visible generated script claim must contain exactly one citation marker.",
                )
            )
            continue
        marker_index = markers[0]
        marker_context = context_by_citation_index.get(marker_index)
        if marker_context is None:
            failed_sentence_claim_ids.add(matching_claims[0].claim_id)
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=matching_claims[0].claim_id,
                    claim_text=sentence.text,
                    reason="Visible citation marker does not map to retrieved context.",
                )
            )
            continue
        claim = matching_claims[0]
        if claim.citation_index != marker_index or claim.chunk_id != marker_context.chunk.chunk_id:
            failed_sentence_claim_ids.add(claim.claim_id)
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    reason="Visible citation marker does not match provider claim support metadata.",
                )
            )
            continue
        visible_claim_text = _visible_claim_text(sentence.text)
        if _normalize(visible_claim_text) != _normalize(claim.text):
            failed_sentence_claim_ids.add(claim.claim_id)
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=claim.claim_id,
                    claim_text=sentence.text,
                    reason="Visible generated claim text does not exactly match supported claim metadata.",
                )
            )
            continue
        matched_claim_ids.add(claim.claim_id)

    for claim in candidate.claims:
        if claim.claim_id in failed_sentence_claim_ids:
            continue
        if claim.claim_id not in matched_claim_ids:
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    reason="Provider claim metadata does not map to a visible cited script claim.",
                )
            )
            continue
        context = context_by_chunk.get(claim.chunk_id or "")
        if context is None or _normalize(claim.text) not in _normalize(context.chunk.text):
            unsupported_claims.append(
                UnsupportedClaim(
                    claim_id=claim.claim_id,
                    claim_text=claim.text,
                    reason="Claim text is not directly present in the cited retrieved chunk.",
                )
            )
            continue
        claim_supports.append(
            ClaimSupport(
                claim_support_id=f"claimsup_{len(claim_supports) + 1:03d}",
                claim_id=claim.claim_id,
                context_ref_id=context.context_ref_id,
                chunk_id=context.chunk.chunk_id,
                document_id=context.chunk.document_id,
                support_status="SUPPORTED",
                support_score=1.0,
                support_reason="The claim is directly supported by the cited retrieved chunk.",
                citation_index=claim.citation_index,
            )
        )
    supported_count = len(claim_supports)
    total_count = len(candidate.claims)
    coverage = supported_count / total_count if total_count else 0.0
    return EvaluationResult(
        evaluation_id=f"eval_{run_id.removeprefix('run_')}",
        run_id=run_id,
        tenant_id=tenant_id,
        project_id=project_id,
        evaluation_status="PASSED" if not unsupported_claims and total_count > 0 else "FAILED",
        groundedness_score=coverage,
        unsupported_claim_count=len(unsupported_claims),
        unsupported_claims=unsupported_claims,
        claim_supports=claim_supports,
        context_ref_coverage=coverage,
        policy_version=GROUNDING_POLICY_VERSION,
        schema_version=EVALUATION_SCHEMA_VERSION,
        safety_policy_version=SAFETY_POLICY_VERSION,
    )


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


@dataclass(frozen=True)
class _ScriptSentence:
    text: str
    start: int
    end: int


def _script_sentences(text: str) -> list[_ScriptSentence]:
    pattern = re.compile(r"\S.*?(?:[.!?](?:\s*\[\d+\])?)(?=\s+\S|$)", re.DOTALL)
    sentences: list[_ScriptSentence] = []
    last_end = 0
    for match in pattern.finditer(text):
        gap = text[last_end : match.start()].strip()
        if gap:
            gap_start = text.find(gap, last_end, match.start())
            sentences.append(_ScriptSentence(text=gap, start=gap_start, end=gap_start + len(gap)))
        sentence = match.group(0).strip()
        if sentence:
            sentences.append(_ScriptSentence(text=sentence, start=match.start(), end=match.end()))
        last_end = match.end()
    trailing = text[last_end:].strip()
    if trailing:
        trailing_start = text.find(trailing, last_end)
        sentences.append(
            _ScriptSentence(
                text=trailing,
                start=trailing_start,
                end=trailing_start + len(trailing),
            )
        )
    if sentences:
        return sentences
    stripped = text.strip()
    return [_ScriptSentence(text=stripped, start=0, end=len(text))] if stripped else []


def _citation_markers(text: str) -> list[int]:
    return [int(match.group(1)) for match in re.finditer(r"\[(\d+)\]", text)]


def _spans_overlap(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return max(left_start, right_start) < min(left_end, right_end)


def _visible_claim_text(text: str) -> str:
    without_citation = re.sub(r"\s*\[\d+\]\s*", " ", text).strip()
    return re.sub(r"(?i)^for\s+[a-z_ -]+s,\s*", "", without_citation).strip()
