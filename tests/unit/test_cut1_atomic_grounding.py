from __future__ import annotations

import json
import re
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterator

import pytest

from backend.app.narration import NarrationService, canonical_presenter_text
from backend.app.presenter_registry import load_cut1_presenter_registry
from backend.app.rag.grounding import GROUNDING_POLICY_VERSION, evaluate_grounding
from backend.app.rag.models import GeneratedScript, ScriptClaim
from backend.app.stage4 import LocalPrincipal, Stage4Service


ROOT = Path(__file__).resolve().parents[2]
FACTS_PATH = ROOT / "docs/governance/cut1-project-facts-v1.json"
SOURCE_PATHS = (
    ROOT / "README.md",
    ROOT / "docs/AI_BUILD_BRIEF.md",
    ROOT / "docs/PRD.md",
)
REQUEST = {
    "audience": "GENERAL",
    "requested_language": "en",
    "depth": "CONCISE",
    "style": "CUT1_ATOMIC_FACTS_V1",
    "prompt": "Create the governed Cut 1 walkthrough from approved project facts.",
}


@contextmanager
def _no_observation(**_: object) -> Iterator[dict[str, object]]:
    yield {}


class CanonicalCut1Generator:
    def __init__(self, presenter_id: str = "meera") -> None:
        self.presenter_id = presenter_id

    def generate_script(
        self,
        *,
        audience: str,
        prompt: str,
        retrieved_context: list[Any],
    ) -> GeneratedScript:
        del audience, prompt
        text = canonical_presenter_text(self.presenter_id)
        source_sentences = list(re.finditer(r"\S.*?[.!?](?=\s|$)", text, re.DOTALL))
        facts_index = next(
            (
                index
                for index, context in enumerate(retrieved_context, start=1)
                if context.chunk.source_filename == "cut1-project-facts-v1.md"
            ),
            1,
        )
        context = retrieved_context[facts_index - 1]
        rendered: list[str] = []
        claims: list[ScriptClaim] = []
        cursor = 0
        for index, match in enumerate(source_sentences, start=1):
            gap = text[cursor : match.start()]
            sentence = match.group(0)
            marker = f" [{facts_index}]"
            start = sum(len(part) for part in rendered) + len(gap)
            rendered.extend((gap, sentence, marker))
            claims.append(
                ScriptClaim(
                    claim_id=f"claim_{index:03d}",
                    text=sentence,
                    citation_index=facts_index,
                    chunk_id=context.chunk.chunk_id,
                    script_span_start=start,
                    script_span_end=start + len(sentence) + len(marker),
                )
            )
            cursor = match.end()
        rendered.append(text[cursor:])
        return GeneratedScript(text="".join(rendered), claims=claims)


def _seed_public_stage4(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    include_facts: bool,
    presenter_id: str = "meera",
) -> tuple[Stage4Service, LocalPrincipal, str]:
    monkeypatch.setattr("backend.app.stage4.langfuse_observation", _no_observation)
    service = Stage4Service(state_path=tmp_path / f"stage4-{presenter_id}.json")
    service.llm = CanonicalCut1Generator(presenter_id)
    principal = LocalPrincipal()
    project = service.create_project(
        principal=principal,
        name="NarraTwin AI",
        description="Controlled local Cut 1 authority preparation.",
        default_audience="GENERAL",
        default_language="en",
        idempotency_key=f"{presenter_id}-project",
    )
    document_ids: list[str] = []
    for index, source_path in enumerate(SOURCE_PATHS, start=1):
        document = service.upload_document(
            principal=principal,
            project_id=project.project_id,
            source_filename=f"accepted-{index}.md",
            content_type="text/markdown",
            data=source_path.read_bytes(),
            idempotency_key=f"{presenter_id}-upload-{index}",
        )
        service.approve_document(
            principal=principal,
            project_id=project.project_id,
            document_id=document.document_id,
            idempotency_key=f"{presenter_id}-approve-{index}",
        )
        document_ids.append(document.document_id)
    if include_facts:
        from backend.app.cut1_grounding import load_cut1_grounding_contract

        facts_bytes = load_cut1_grounding_contract(root=ROOT).project_source_bytes()
        facts = service.upload_document(
            principal=principal,
            project_id=project.project_id,
            source_filename="cut1-project-facts-v1.md",
            content_type="text/markdown",
            data=facts_bytes,
            idempotency_key=f"{presenter_id}-upload-facts",
        )
        service.approve_document(
            principal=principal,
            project_id=project.project_id,
            document_id=facts.document_id,
            idempotency_key=f"{presenter_id}-approve-facts",
        )
        document_ids.append(facts.document_id)
    service.ingest_documents(
        principal=principal,
        project_id=project.project_id,
        document_ids=document_ids,
        idempotency_key=f"{presenter_id}-ingest",
    )
    return service, principal, project.project_id


def _generate(
    service: Stage4Service,
    principal: LocalPrincipal,
    project_id: str,
    *,
    key: str,
) -> Any:
    return service.generate_walkthrough(
        principal=principal,
        project_id=project_id,
        idempotency_key=key,
        **REQUEST,
    )


def test_red_genuine_accepted_sources_produce_exactly_eighteen_unsupported_claims(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, principal, project_id = _seed_public_stage4(
        tmp_path,
        monkeypatch,
        include_facts=False,
    )

    run = _generate(service, principal, project_id, key="red-generate")

    assert run.status == "FAILED"
    assert run.accepted_script_text is None
    assert run.evaluation is not None
    assert run.evaluation.policy_version == GROUNDING_POLICY_VERSION
    assert run.evaluation.unsupported_claim_count == 18
    assert len(run.evaluation.unsupported_claims) == 18
    assert not run.evaluation.claim_supports


def test_governed_atomic_facts_complete_the_public_persisted_stage4_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, principal, project_id = _seed_public_stage4(
        tmp_path,
        monkeypatch,
        include_facts=True,
    )

    run = _generate(service, principal, project_id, key="green-generate")

    assert run.status == "COMPLETED"
    assert run.evaluation_status == "PASSED"
    assert run.evaluation is not None
    assert run.evaluation.unsupported_claim_count == 0
    assert len(run.evaluation.claim_supports) == 18
    assert all(support.proposition_ids for support in run.evaluation.claim_supports)
    assert all(support.proposition_evidence_checksum for support in run.evaluation.claim_supports)
    assert run.accepted_script_text == run.generated_script.text

    restored = Stage4Service(state_path=service.state_path)
    replayed = _generate(restored, principal, project_id, key="green-generate")
    assert replayed == run


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_proposition",
        "duplicate_proposition",
        "foreign_proposition",
        "claim_hash",
        "source_path",
        "source_revision",
        "source_byte_range",
        "source_checksum",
        "span_checksum",
        "span_text",
        "unknown_field",
    ],
)
def test_atomic_fact_contract_mutations_fail_closed(mutation: str) -> None:
    from backend.app.cut1_grounding import Cut1GroundingError, load_cut1_grounding_contract

    payload = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
    if mutation == "missing_proposition":
        payload["propositions"].pop()
    elif mutation == "duplicate_proposition":
        payload["propositions"].append(payload["propositions"][0])
    elif mutation == "foreign_proposition":
        payload["claimMappings"][0]["propositionIds"].append("fact_foreign")
    elif mutation == "claim_hash":
        payload["claimMappings"][0]["claimSha256ByPresenter"]["meera"] = "0" * 64
    elif mutation == "source_path":
        payload["sources"][0]["path"] = "tests/unit/test_cut1_narration.py"
    elif mutation == "source_revision":
        payload["sources"][0]["revision"] = "0" * 40
    elif mutation == "source_byte_range":
        payload["sources"][0]["spans"][0]["byteEnd"] += 1
    elif mutation == "source_checksum":
        payload["sources"][0]["sha256"] = "0" * 64
    elif mutation == "span_checksum":
        payload["sources"][0]["spans"][0]["sha256"] = "0" * 64
    elif mutation == "span_text":
        payload["sources"][0]["spans"][0]["text"] += " changed"
    elif mutation == "unknown_field":
        payload["callerApproved"] = True

    with pytest.raises(Cut1GroundingError):
        load_cut1_grounding_contract(root=ROOT, payload=payload)


def test_atomic_fact_asset_bytes_are_immutable(tmp_path: Path) -> None:
    from backend.app.cut1_grounding import Cut1GroundingError, load_cut1_grounding_contract

    target = tmp_path / "docs/governance/cut1-project-facts-v1.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(FACTS_PATH.read_bytes() + b"\n")

    with pytest.raises(Cut1GroundingError):
        load_cut1_grounding_contract(root=tmp_path)


def test_caller_supplied_proposition_metadata_cannot_turn_generic_grounding_green() -> None:
    claim = ScriptClaim(
        claim_id="claim_injected",
        text="An unsupported caller assertion.",
        citation_index=1,
        chunk_id=None,
        script_span_start=0,
        script_span_end=len("An unsupported caller assertion. [1]"),
        proposition_ids=("fact_injected",),
        proposition_evidence_checksum="sha256:" + "0" * 64,
    )
    candidate = GeneratedScript("An unsupported caller assertion. [1]", [claim])

    evaluation = evaluate_grounding(
        tenant_id="tenant_local",
        project_id="proj_local",
        run_id="run_injected",
        candidate=candidate,
        retrieved_context=[],
        prompt="",
        all_chunks=[],
    )

    assert evaluation.evaluation_status == "FAILED"
    assert evaluation.unsupported_claim_count == 1
    assert not evaluation.claim_supports


def test_cut1_evidence_checksum_changes_when_any_proposition_binding_changes() -> None:
    from backend.app.cut1_grounding import load_cut1_grounding_contract

    contract = load_cut1_grounding_contract(root=ROOT)
    first = contract.claim_mappings[2]
    changed = replace(first, proposition_ids=tuple(reversed(first.proposition_ids)))

    assert contract.evidence_checksum(first) != contract.evidence_checksum(changed)


@pytest.mark.parametrize("presenter_id", ["meera", "myra", "raj"])
def test_public_stage4_and_issue382_lifecycle_persists_one_bound_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    presenter_id: str,
) -> None:
    stage4, principal, project_id = _seed_public_stage4(
        tmp_path,
        monkeypatch,
        include_facts=True,
        presenter_id=presenter_id,
    )
    run = _generate(stage4, principal, project_id, key=f"{presenter_id}-generate")
    registry = load_cut1_presenter_registry(asset_root=ROOT)
    identity = registry.get(presenter_id, "1.0.0")
    assert identity.asset is not None
    binding = registry.bind_for_trace(
        presenter_id=presenter_id,
        presenter_version="1.0.0",
        trace_id=f"trace_{presenter_id}_authority",
        asset_sha256=identity.asset.sha256,
        voice_reference_id=identity.voice.reference_id,
        voice_reference_version=identity.voice.version,
    )
    state_path = tmp_path / f"narration-{presenter_id}.json"
    narration = NarrationService(stage4=stage4, registry=registry, state_path=state_path)
    draft = narration.create_draft(
        principal=principal,
        project_id=project_id,
        source_run_id=run.run_id,
        presenter_binding=binding,
        review_text=run.accepted_script_text,
    )
    required = narration.request_evaluation(
        principal=principal,
        project_id=project_id,
        narration_version=draft.version,
        narration_checksum=draft.narration_checksum,
    )
    evaluated = narration.evaluate(
        principal=principal,
        project_id=project_id,
        narration_version=required.version,
        narration_checksum=required.narration_checksum,
    )
    approved = narration.approve_for_speech(
        principal=principal,
        project_id=project_id,
        narration_version=evaluated.version,
        narration_checksum=evaluated.narration_checksum,
        approver_id=principal.actor_id,
    )
    receipt = narration.consume_for_tts(
        principal=principal,
        project_id=project_id,
        narration_version=approved.version,
        narration_checksum=approved.narration_checksum,
        request_id=f"request_{presenter_id}_authority",
        trace_id=f"trace_{presenter_id}_tts",
    )

    restored_stage4 = Stage4Service(state_path=stage4.state_path)
    restored = NarrationService(
        stage4=restored_stage4,
        registry=load_cut1_presenter_registry(asset_root=ROOT),
        state_path=state_path,
    )
    assert restored.validate_tts_consumption_receipt(principal=principal, receipt=receipt) == receipt
    assert receipt.spoken_text == canonical_presenter_text(presenter_id)
    assert receipt.receipt_checksum.startswith("sha256:")
