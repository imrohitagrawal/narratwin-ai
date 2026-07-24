"""Provider-agnostic local mocks for Stage 4 tests."""

from __future__ import annotations

import math
import re
from typing import Protocol

from backend.app.rag.models import GeneratedScript, RetrievedContext, ScriptClaim

WORD_PATTERN = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(Protocol):
    provider: str
    model: str
    model_version: str
    dimension: int

    def embed(self, text: str) -> tuple[float, ...]:
        """Embed text into a deterministic vector."""


class LLMProvider(Protocol):
    provider: str
    provider_mode: str

    def generate_script(
        self,
        *,
        audience: str,
        prompt: str,
        retrieved_context: list[RetrievedContext],
    ) -> GeneratedScript:
        """Generate a script from retrieved context."""


class MockEmbeddingProvider:
    provider = "mock"
    model = "mock-embedding"
    model_version = "stage4-local-v1"
    dimension = 16

    def embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimension
        for word in WORD_PATTERN.findall(text.lower()):
            bucket = sum(ord(char) for char in word) % self.dimension
            vector[bucket] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return tuple(vector)
        return tuple(value / magnitude for value in vector)


class MockLLMProvider:
    provider = "mock"
    provider_mode = "LOCAL"
    trace_metadata = "run_id is assigned by orchestration before persistence"

    def __init__(self, extra_unsupported_claim: str | None = None) -> None:
        self._extra_unsupported_claim = extra_unsupported_claim

    def generate_script(
        self,
        *,
        audience: str,
        prompt: str,
        retrieved_context: list[RetrievedContext],
    ) -> GeneratedScript:
        del prompt
        audience_label = audience_label_for_script(audience)
        script_parts: list[str] = []
        claims: list[ScriptClaim] = []
        for index, context in enumerate(retrieved_context, start=1):
            claim_text = _first_claim_sentence(context.chunk.text)
            sentence = f"For {audience_label}, {claim_text} [{index}]"
            start = sum(len(part) + 1 for part in script_parts)
            end = start + len(sentence)
            script_parts.append(sentence)
            claims.append(
                ScriptClaim(
                    claim_id=f"claim_{index:03d}",
                    text=claim_text,
                    citation_index=index,
                    chunk_id=context.chunk.chunk_id,
                    script_span_start=start,
                    script_span_end=end,
                )
            )
        if self._extra_unsupported_claim:
            start = sum(len(part) + 1 for part in script_parts)
            script_parts.append(self._extra_unsupported_claim)
            claims.append(
                ScriptClaim(
                    claim_id=f"claim_{len(claims) + 1:03d}",
                    text=self._extra_unsupported_claim,
                    citation_index=len(claims) + 1,
                    chunk_id=None,
                    script_span_start=start,
                    script_span_end=start + len(self._extra_unsupported_claim),
                )
            )
        return GeneratedScript(text=" ".join(script_parts), claims=claims)


def audience_label_for_script(audience: str) -> str:
    return {
        "RECRUITER": "recruiters",
        "HIRING_MANAGER": "hiring managers",
        "ENGINEER": "engineers",
        "PRODUCT_LEADER": "product leaders",
        "BEGINNER": "beginners",
        "GLOBAL_VIEWER": "global viewers",
        "CUSTOMER": "customers",
    }.get(audience, audience.lower().replace("_", " "))


def _first_claim_sentence(text: str) -> str:
    content_lines = [
        line.strip()
        for line in text.strip().splitlines()
        if line.strip() and not re.fullmatch(r"#{1,6}\s+.+", line.strip())
    ]
    content = " ".join(content_lines)
    for raw_sentence in re.split(r"(?<=[.!?])\s+", content):
        sentence = raw_sentence.strip()
        if sentence:
            return sentence.rstrip(".") + "."
    return text.strip()
