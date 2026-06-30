"""Evaluation runner for Stage 5 RAG checks."""

from __future__ import annotations

import json
import base64
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.eval.unsupported_claims import unsupported_claim_count
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import GeneratedScript, KnowledgeChunk, RetrievedContext, ScriptClaim

MAX_SMOKE_CASES = 20
MAX_UPLOAD_FIXTURE_BYTES = 16 * 1024


def run_stage5_eval_suite(
    *,
    fixture_path: Path,
    client: TestClient | None = None,
    write_markdown: Callable[[dict[str, object]], str] | None = None,
) -> dict[str, object]:
    if client is None:
        client = TestClient(app)
    suite = _load_json(fixture_path)

    report: dict[str, object] = {
        "suite": suite["name"],
        "generatedAt": "generated-by-stage5-eval-smoke",
        "passed": True,
        "checks": [],
        "metrics": {},
    }

    checks: list[_EvalCheck] = []
    reset_app_state_for_tests()

    project_payload = _as_dict(suite["project"], "suite.project")
    project_response = client.post(
        "/api/v1/projects",
        json=project_payload,
        headers={"Idempotency-Key": "stage5-happy-project"},
    )
    checks.append(
        _EvalCheck(
            name="setup project created",
            passed=project_response.status_code == 201,
            expected=201,
            actual=project_response.status_code,
        )
    )
    project = project_response.json()
    project_id = _as_str(project["projectId"], "project.projectId")

    document = _as_dict(suite["document"], "suite.document")
    document_response = client.post(
        f"/api/v1/projects/{project_id}/knowledge-documents",
        files={
            "file": (
                _as_str(document["filename"], "suite.document.filename"),
                Path(_as_str(document["path"], "suite.document.path")).read_bytes(),
                _as_str(document["contentType"], "suite.document.contentType"),
            )
        },
        headers={"Idempotency-Key": "stage5-happy-upload"},
    )
    checks.append(
        _EvalCheck(
            name="setup document uploaded",
            passed=document_response.status_code == 201,
            expected=201,
            actual=document_response.status_code,
        )
    )
    document_data = document_response.json()
    document_id = _as_str(document_data["documentId"], "document.documentId")

    approval_response = client.patch(
        f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
        json={"approvalStatus": "APPROVED", "reviewNote": "Stage 5 eval fixture."},
        headers={"Idempotency-Key": "approval"},
    )
    checks.append(
        _EvalCheck(
            name="setup document approved",
            passed=approval_response.status_code == 200,
            expected=200,
            actual=approval_response.status_code,
        )
    )
    ingestion_response = client.post(
        f"/api/v1/projects/{project_id}/ingestion-runs",
        json={"documentIds": [document_id]},
        headers={"Idempotency-Key": "ingest"},
    )
    checks.append(
        _EvalCheck(
            name="setup document ingested",
            passed=ingestion_response.status_code == 201,
            expected=201,
            actual=ingestion_response.status_code,
        )
    )

    generation = _as_dict(suite["generation"], "suite.generation")
    generation_payload = dict(generation)
    generation_response = client.post(
        f"/api/v1/projects/{project_id}/walkthrough-runs",
        json=generation_payload,
        headers={"Idempotency-Key": "stage5-happy-generate"},
    )
    happy_run = _as_dict(generation_response.json(), "happyRun")

    expected = _as_dict(suite["expected"], "suite.expected")
    checks.append(
        _EvalCheck(
            name="happy path status",
            passed=happy_run.get("status") == expected["status"],
            expected=expected["status"],
            actual=happy_run.get("status"),
        )
    )
    checks.append(
        _EvalCheck(
            name="happy path eval status",
            passed=happy_run.get("evaluationStatus") == expected["evaluationStatus"],
            expected=expected["evaluationStatus"],
            actual=happy_run.get("evaluationStatus"),
        )
    )
    checks.append(
        _EvalCheck(
            name="happy path unsupported claim count",
            passed=happy_run.get("evaluation", {}).get("unsupportedClaimCount") == expected["unsupportedClaimCount"],
            expected=expected["unsupportedClaimCount"],
            actual=happy_run.get("evaluation", {}).get("unsupportedClaimCount"),
        )
    )

    negative_cases = _capped_optional_cases(suite.get("negativeCases", []), "negativeCases")
    if negative_cases:
        checks.extend(
            _run_negative_cases(
                client=client,
                base_project_id=project_id,
                generation=generation_payload,
                cases=negative_cases,
            )
        )

    unsupported_claim_cases = _capped_optional_cases(suite.get("unsupportedClaimCases", []), "unsupportedClaimCases")
    if unsupported_claim_cases:
        checks.extend(_run_unsupported_claim_cases(cases=unsupported_claim_cases))

    prompt_injection_path = suite.get("promptInjectionSet")
    if isinstance(prompt_injection_path, str) and prompt_injection_path.strip():
        checks.extend(
            _run_prompt_injection_cases(
                client=client,
                project_id=project_id,
                generation=generation_payload,
                suite_path=Path(prompt_injection_path),
            )
        )
        checks.extend(
            _run_uploaded_document_prompt_injection_cases(
                client=client,
                project_id=project_id,
                suite_path=Path(prompt_injection_path),
            )
        )

    file_upload_abuse_path = suite.get("fileUploadAbuseSet")
    if isinstance(file_upload_abuse_path, str) and file_upload_abuse_path.strip():
        checks.extend(
            _run_file_upload_abuse_cases(
                client=client,
                project_id=project_id,
                suite_path=Path(file_upload_abuse_path),
            )
        )

    checks.append(
        _EvalCheck(
            name="trace metadata has latency, token counts, and mock cost",
            passed=_has_trace_latency_tokens_and_cost(happy_run=happy_run),
            expected="traceId present, nonnegative latency, positive tokens, mock cost 0.0",
            actual=_trace_observability_summary(happy_run=happy_run),
        )
    )

    metrics_data = _as_dict(happy_run.get("evaluation", {}), "happyRun.evaluation")
    evaluation_metrics = _EvaluationMetrics.from_dict(metrics_data)
    report["metrics"] = {
        "faithfulness": evaluation_metrics.faithfulness,
        "answerRelevancy": evaluation_metrics.answer_relevancy,
        "contextPrecision": evaluation_metrics.context_precision,
        "contextRecall": evaluation_metrics.context_recall,
    }
    checks.append(
        _EvalCheck(
            name="golden metrics thresholds",
            passed=(
                evaluation_metrics.faithfulness >= 0.85
                and evaluation_metrics.answer_relevancy >= 0.80
                and evaluation_metrics.context_precision >= 0.75
                and evaluation_metrics.context_recall >= 0.70
            ),
            expected={
                "faithfulness": ">= 0.85",
                "answerRelevancy": ">= 0.80",
                "contextPrecision": ">= 0.75",
                "contextRecall": ">= 0.70",
            },
            actual=report["metrics"],
        )
    )

    unsupported_claims = metrics_data.get("unsupportedClaimCount")
    expected_claims = expected["unsupportedClaimCount"]
    checks.append(
        _EvalCheck(
            name="golden unsupported claim count",
            passed=unsupported_claims == expected_claims,
            expected=expected_claims,
            actual=unsupported_claims,
        )
    )

    report["checks"] = [item.as_dict() for item in checks]
    report["passed"] = all(item.passed for item in checks)
    if write_markdown is not None:
        report["markdown"] = write_markdown(report)
    return report


def _run_unsupported_claim_cases(*, cases: list[object]) -> list[_EvalCheck]:
    checks: list[_EvalCheck] = []
    supported_claim = "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts."
    unsupported_claim = "NarraTwin AI guarantees hiring outcomes."
    chunk = KnowledgeChunk(
        chunk_id="chunk_stage5_eval_001",
        document_id="doc_stage5_eval_001",
        project_id="proj_stage5_eval_001",
        tenant_id="tenant_stage5_eval",
        source_filename="stage5_eval.md",
        chunk_index=0,
        text=supported_claim,
        token_count=10,
        checksum="stage5_eval_checksum",
        source_document_checksum="stage5_eval_document_checksum",
        approved_at="2026-06-30T00:00:00Z",
        heading_path=[],
        line_start=1,
        line_end=1,
    )
    retrieved_context = [
        RetrievedContext(
            context_ref_id="ctx_stage5_eval_001",
            chunk=chunk,
            score=1.0,
        )
    ]

    for index, case in enumerate(cases):
        case_payload = _as_dict(case, f"unsupportedClaimCase[{index}]")
        case_type = _as_str(case_payload.get("type"), f"unsupportedClaimCase[{index}].type")
        expected_status = _as_str(case_payload.get("expectedEvaluationStatus"), "expectedEvaluationStatus")
        expected_count = _as_int(case_payload.get("expectedUnsupportedClaimCount"), "expectedUnsupportedClaimCount")

        candidate = _unsupported_claim_candidate(
            case_type=case_type,
            supported_claim=supported_claim,
            unsupported_claim=unsupported_claim,
            chunk_id=chunk.chunk_id,
        )
        evaluation = evaluate_grounding(
            tenant_id=chunk.tenant_id,
            project_id=chunk.project_id,
            run_id=f"run_stage5_eval_{index:03d}",
            candidate=candidate,
            retrieved_context=retrieved_context,
            prompt="Evaluate unsupported claim behavior.",
            all_chunks=[chunk],
        )
        actual_count = unsupported_claim_count(evaluation=evaluation)
        checks.append(
            _EvalCheck(
                name=f"unsupported claim detector: {_as_str(case_payload.get('name'), f'unsupportedClaimCase[{index}].name')}",
                passed=evaluation.evaluation_status == expected_status and actual_count == expected_count,
                expected={"evaluationStatus": expected_status, "unsupportedClaimCount": expected_count},
                actual={
                    "evaluationStatus": evaluation.evaluation_status,
                    "unsupportedClaimCount": actual_count,
                },
            )
        )
    return checks


def _unsupported_claim_candidate(
    *,
    case_type: str,
    supported_claim: str,
    unsupported_claim: str,
    chunk_id: str,
) -> GeneratedScript:
    if case_type == "supported":
        return _generated_script_from_claims([(supported_claim, chunk_id, 1)])
    if case_type == "unsupported":
        return _generated_script_from_claims([(unsupported_claim, chunk_id, 1)])
    if case_type == "mixed":
        return _generated_script_from_claims(
            [
                (supported_claim, chunk_id, 1),
                (unsupported_claim, chunk_id, 1),
            ]
        )
    raise ValueError(f"Unsupported unsupportedClaimCase.type: {case_type}")


def _generated_script_from_claims(claim_specs: list[tuple[str, str, int]]) -> GeneratedScript:
    script_parts: list[str] = []
    claims: list[ScriptClaim] = []
    cursor = 0
    for index, (claim_text, chunk_id, citation_index) in enumerate(claim_specs, start=1):
        sentence = f"For recruiters, {claim_text} [{citation_index}]"
        if script_parts:
            cursor += 1
        script_parts.append(sentence)
        start = cursor + len("For recruiters, ")
        end = start + len(claim_text)
        claims.append(
            ScriptClaim(
                claim_id=f"claim_stage5_eval_{index:03d}",
                text=claim_text,
                citation_index=citation_index,
                chunk_id=chunk_id,
                script_span_start=start,
                script_span_end=end,
            )
        )
        cursor += len(sentence)
    return GeneratedScript(text=" ".join(script_parts), claims=claims)


def _run_negative_cases(
    *,
    client: TestClient,
    base_project_id: str,
    generation: dict[str, object],
    cases: list[object],
) -> list[_EvalCheck]:
    checks: list[_EvalCheck] = []
    for case in cases:
        case_payload = _as_dict(case, "negativeCase")
        prompt = _as_str(case_payload.get("prompt"), "negativeCase.prompt")
        reason_code_value = case_payload.get("reasonCode", case_payload.get("expectedReasonCode"))
        if reason_code_value is None:
            raise TypeError("negativeCase.reasonCode missing.")
        reason_code = _as_str(reason_code_value, "negativeCase.reasonCode")
        response = client.post(
            f"/api/v1/projects/{base_project_id}/walkthrough-runs",
            json={
                "audience": _as_str(generation.get("audience"), "suite.generation.audience"),
                "requestedLanguage": _as_str(generation.get("requestedLanguage"), "suite.generation.requestedLanguage"),
                "depth": _as_str(generation.get("depth"), "suite.generation.depth"),
                "style": _as_str(generation.get("style"), "suite.generation.style"),
                "prompt": prompt,
            },
            headers={"Idempotency-Key": f"stage5-negative-{_as_str(case_payload.get('name'), 'negativeCase.name')}"},
        )
        payload = _as_dict(response.json(), "negativeCaseRun")
        checks.append(
            _EvalCheck(
                name=f"prompt injection negative case: {_as_str(case_payload.get('name'), 'negativeCase.name')}",
                passed=payload.get("status") == "REFUSED"
                and payload.get("failure", {}).get("reasonCode") == reason_code,
                expected=reason_code,
                actual=payload.get("failure", {}),
            )
        )
    return checks


def _run_prompt_injection_cases(
    *,
    client: TestClient,
    project_id: str,
    generation: dict[str, object],
    suite_path: Path,
) -> list[_EvalCheck]:
    checks: list[_EvalCheck] = []
    suite = _load_json(suite_path)
    cases = _capped_optional_cases(suite.get("cases", []), "prompt injection cases")
    for index, case in enumerate(cases):
        case_payload = _as_dict(case, f"promptInjectionCase[{index}]")
        response = client.post(
            f"/api/v1/projects/{project_id}/walkthrough-runs",
            json={
                "audience": _as_str(generation.get("audience"), "suite.generation.audience"),
                "requestedLanguage": _as_str(generation.get("requestedLanguage"), "suite.generation.requestedLanguage"),
                "depth": _as_str(generation.get("depth"), "suite.generation.depth"),
                "style": _as_str(generation.get("style"), "suite.generation.style"),
                "prompt": _as_str(case_payload.get("prompt"), f"promptInjectionCase[{index}].prompt"),
            },
            headers={"Idempotency-Key": f"stage5-prompt-injection-{index}"},
        )
        payload = _as_dict(response.json(), "promptInjectionRun")
        expected_reason = _as_str(case_payload.get("expectedReasonCode"), f"promptInjectionCase[{index}].expectedReasonCode")
        checks.append(
            _EvalCheck(
                name=f"prompt injection rejected: {_as_str(case_payload.get('name'), f'promptInjectionCase[{index}].name')}",
                passed=payload.get("status") == "REFUSED"
                and payload.get("failure", {}).get("reasonCode") == expected_reason,
                expected=expected_reason,
                actual=payload.get("failure", {}).get("reasonCode"),
            )
        )
    return checks


def _run_file_upload_abuse_cases(
    *,
    client: TestClient,
    project_id: str,
    suite_path: Path,
) -> list[_EvalCheck]:
    del project_id
    checks: list[_EvalCheck] = []
    suite = _load_json(suite_path)
    cases = _capped_optional_cases(suite.get("cases", []), "file upload abuse cases")
    for index, test_case in enumerate(cases):
        case_project_id, setup_check = _create_case_project(client=client, idempotency_prefix="stage5-abuse", index=index)
        if setup_check is not None:
            checks.append(setup_check)
            continue
        case_payload = _as_dict(test_case, f"fileUploadCase[{index}]")
        filename = _as_str(case_payload.get("filename"), f"fileUploadCase[{index}].filename")
        content_type = _as_str(case_payload.get("contentType"), f"fileUploadCase[{index}].contentType")
        content = _as_str(case_payload.get("content"), f"fileUploadCase[{index}].content")
        if "contentBase64" in case_payload:
            content_bytes = base64.b64decode(_as_str(case_payload.get("contentBase64"), f"fileUploadCase[{index}].contentBase64"))
        else:
            content_bytes = content.encode("utf-8")
        if len(content_bytes) > MAX_UPLOAD_FIXTURE_BYTES:
            raise ValueError(f"fileUploadCase[{index}] exceeds {MAX_UPLOAD_FIXTURE_BYTES} bytes.")
        expected_status = _as_int(case_payload.get("status"), f"fileUploadCase[{index}].status")
        expected_error_code = case_payload.get("expectedErrorCode")

        response = client.post(
            f"/api/v1/projects/{case_project_id}/knowledge-documents",
            files={
                "file": (
                    filename,
                    content_bytes,
                    content_type,
                )
            },
            headers={"Idempotency-Key": f"stage5-abuse-upload-{index}"},
        )

        passed = response.status_code == expected_status
        body = response.json()
        if passed and expected_error_code is not None:
            expected_code = _as_str(expected_error_code, f"fileUploadCase[{index}].expectedErrorCode")
            passed = passed and body.get("error", {}).get("code") == expected_code

        checks.append(
            _EvalCheck(
                name=f"file upload abuse rejected: {filename}",
                passed=passed,
                expected={"status": expected_status, "errorCode": expected_error_code},
                actual={"status": response.status_code, "errorCode": body.get("error", {}).get("code")},
            )
        )
    return checks


def _run_uploaded_document_prompt_injection_cases(
    *,
    client: TestClient,
    project_id: str,
    suite_path: Path,
) -> list[_EvalCheck]:
    del project_id
    checks: list[_EvalCheck] = []
    suite = _load_json(suite_path)
    cases = _capped_optional_cases(suite.get("cases", []), "prompt injection cases")
    for index, case in enumerate(cases):
        case_project_id, setup_check = _create_case_project(client=client, idempotency_prefix="stage5-uploaded-injection", index=index)
        if setup_check is not None:
            checks.append(setup_check)
            continue
        case_payload = _as_dict(case, f"promptInjectionCase[{index}]")
        name = _as_str(case_payload.get("name"), f"promptInjectionCase[{index}].name")
        prompt = _as_str(case_payload.get("prompt"), f"promptInjectionCase[{index}].prompt")
        upload_response = client.post(
            f"/api/v1/projects/{case_project_id}/knowledge-documents",
            files={"file": (f"injection-{index}.md", prompt.encode("utf-8"), "text/markdown")},
            headers={"Idempotency-Key": f"stage5-uploaded-injection-{index}"},
        )
        document_id = upload_response.json().get("documentId") if upload_response.status_code == 201 else None
        if isinstance(document_id, str):
            client.patch(
                f"/api/v1/projects/{case_project_id}/knowledge-documents/{document_id}/approval",
                json={"approvalStatus": "APPROVED", "reviewNote": "Stage 5 uploaded prompt-injection case."},
                headers={"Idempotency-Key": f"stage5-uploaded-injection-approval-{index}"},
            )
            ingestion_response = client.post(
                f"/api/v1/projects/{case_project_id}/ingestion-runs",
                json={"documentIds": [document_id]},
                headers={"Idempotency-Key": f"stage5-uploaded-injection-ingest-{index}"},
            )
            actual = {
                "uploadStatus": upload_response.status_code,
                "ingestionStatus": ingestion_response.status_code,
                "errorCode": ingestion_response.json().get("error", {}).get("code"),
            }
        else:
            actual = {
                "uploadStatus": upload_response.status_code,
                "ingestionStatus": None,
                "errorCode": upload_response.json().get("error", {}).get("code"),
            }

        checks.append(
            _EvalCheck(
                name=f"uploaded document prompt injection rejected: {name}",
                passed=actual["uploadStatus"] == 201
                and actual["ingestionStatus"] == 422
                and actual["errorCode"] == "UNSAFE_DOCUMENT_CONTENT",
                expected={"uploadStatus": 201, "ingestionStatus": 422, "errorCode": "UNSAFE_DOCUMENT_CONTENT"},
                actual=actual,
            )
        )
    return checks


def _create_case_project(*, client: TestClient, idempotency_prefix: str, index: int) -> tuple[str | None, _EvalCheck | None]:
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Stage 5 isolated case {idempotency_prefix}-{index}"},
        headers={"Idempotency-Key": f"{idempotency_prefix}-project-{index}"},
    )
    if response.status_code != 201:
        return None, _EvalCheck(
            name=f"setup isolated project: {idempotency_prefix}-{index}",
            passed=False,
            expected=201,
            actual=response.status_code,
        )
    project = _as_dict(response.json(), "caseProject")
    return _as_str(project["projectId"], "caseProject.projectId"), None


def _has_trace_latency_tokens_and_cost(*, happy_run: dict[str, object]) -> bool:
    trace = _as_dict(happy_run.get("trace", {}), "happyRun.trace")
    trace_id = trace.get("traceId")
    latency = trace.get("latencyMs")
    input_tokens = trace.get("inputTokens")
    output_tokens = trace.get("outputTokens")
    estimated_cost = trace.get("estimatedCost")
    return (
        isinstance(trace_id, str)
        and trace_id.startswith("trace_")
        and isinstance(latency, int)
        and latency >= 0
        and isinstance(input_tokens, int)
        and input_tokens > 0
        and isinstance(output_tokens, int)
        and output_tokens > 0
        and isinstance(estimated_cost, (int, float))
        and float(estimated_cost) == 0.0
    )


def _trace_observability_summary(*, happy_run: dict[str, object]) -> dict[str, object]:
    trace = _as_dict(happy_run.get("trace", {}), "happyRun.trace")
    input_tokens = trace.get("inputTokens")
    output_tokens = trace.get("outputTokens")
    return {
        "traceId": "present" if isinstance(trace.get("traceId"), str) and trace["traceId"] else "missing",
        "latencyMs": "nonnegative int"
        if isinstance(trace.get("latencyMs"), int) and trace["latencyMs"] >= 0
        else trace.get("latencyMs"),
        "inputTokens": "positive int" if isinstance(input_tokens, int) and input_tokens > 0 else input_tokens,
        "outputTokens": "positive int" if isinstance(output_tokens, int) and output_tokens > 0 else output_tokens,
        "estimatedCost": trace.get("estimatedCost"),
    }


def to_markdown(report: dict[str, object]) -> str:
    checks = _as_list(report.get("checks", []), "report.checks")
    checks = [_as_dict(c, "report.checks item") for c in checks]
    checks_passed = sum(1 for item in checks if bool(item.get("passed")))
    markdown = [
        "# Evaluation Report",
        "",
        f"Generated: {report.get('generatedAt')}",
        "",
        "## Summary",
        "",
    ]
    markdown.append(f"- Suite: {report.get('suite')}")
    markdown.append(f"- Passed: {'YES' if report.get('passed') else 'NO'}")
    markdown.append(f"- Checks: {checks_passed}/{len(checks)} passed")
    markdown.extend(["", "## Metrics", "", "| Metric | Value |", "| --- | --- |"])
    metrics = _as_dict(report.get("metrics", {}), "report.metrics")
    for key, value in metrics.items():
        markdown.append(f"| {key} | {value} |")
    markdown.append("")
    markdown.extend(["## Checks", "", "| Check | Passed | Expected | Actual |", "| --- | --- | --- | --- |"])
    for item_dict in checks:
        markdown.append(
            f"| {item_dict.get('name')} | { 'PASS' if item_dict.get('passed') else 'FAIL' } | {item_dict.get('expected')} | {item_dict.get('actual')} |"
        )
    return "\n".join(markdown) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    return _as_dict(json.loads(path.read_text(encoding="utf-8")), f"fixture:{path}")


def _as_dict(value: object, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{field_name} expected mapping, got {type(value)!s}")
    return cast(dict[str, Any], value)


def _as_list(value: object, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{field_name} expected list, got {type(value)!s}")
    return value


def _capped_optional_cases(value: object, field_name: str) -> list[Any]:
    cases = _as_list(value, field_name)
    if len(cases) > MAX_SMOKE_CASES:
        raise ValueError(f"{field_name} exceeds {MAX_SMOKE_CASES} smoke cases.")
    return cases


def _as_str(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} expected string, got {type(value)!s}")
    return value


def _as_int(value: object, field_name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{field_name} expected int, got {type(value)!s}")
    return value


def _as_float(value: object, field_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} expected number, got {type(value)!s}")
    return float(value)


@dataclass(frozen=True)
class _EvalCheck:
    name: str
    passed: bool
    expected: object
    actual: object

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass(frozen=True)
class _EvaluationMetrics:
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float

    @classmethod
    def from_dict(cls, evaluation: dict[str, Any]) -> "_EvaluationMetrics":
        return cls(
            faithfulness=_as_float(evaluation.get("faithfulness"), "evaluation.faithfulness"),
            answer_relevancy=_as_float(evaluation.get("answerRelevancy"), "evaluation.answerRelevancy"),
            context_precision=_as_float(evaluation.get("contextPrecision"), "evaluation.contextPrecision"),
            context_recall=_as_float(evaluation.get("contextRecall"), "evaluation.contextRecall"),
        )
