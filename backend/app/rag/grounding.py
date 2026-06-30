"""Claim-level grounding evaluation for generated scripts."""

from __future__ import annotations

import re

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
    unsupported_claims: list[UnsupportedClaim] = []
    claim_supports: list[ClaimSupport] = []
    for claim in candidate.claims:
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
