#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

mkdir -p reports/eval-smoke

uv run python - <<'PY'
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests
from backend.app.rag.grounding import evaluate_grounding
from backend.app.rag.models import GeneratedScript, ScriptClaim
from backend.app.stage4 import stage4_service

fixture_path = Path("evals/smoke/stage4_grounded_script_dataset.json")
report_path = Path("reports/eval-smoke/stage4-grounded-script-report.json")
fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

reset_app_state_for_tests()
client = TestClient(app)

project_response = client.post(
    "/api/v1/projects",
    json=fixture["project"],
    headers={"Idempotency-Key": "eval-project"},
)
project_id = project_response.json()["projectId"]

document = fixture["document"]
document_path = Path(document["path"])
upload_response = client.post(
    f"/api/v1/projects/{project_id}/knowledge-documents",
    files={
        "file": (
            document["filename"],
            document_path.read_bytes(),
            document["contentType"],
        )
    },
    headers={"Idempotency-Key": "eval-upload"},
)
document_id = upload_response.json()["documentId"]

approve_response = client.patch(
    f"/api/v1/projects/{project_id}/knowledge-documents/{document_id}/approval",
    json={"approvalStatus": "APPROVED", "reviewNote": "Stage 4 eval fixture."},
    headers={"Idempotency-Key": "eval-approval"},
)
ingest_response = client.post(
    f"/api/v1/projects/{project_id}/ingestion-runs",
    json={"documentIds": [document_id]},
    headers={"Idempotency-Key": "eval-ingest"},
)
generation_response = client.post(
    f"/api/v1/projects/{project_id}/walkthrough-runs",
    json=fixture["generation"],
    headers={"Idempotency-Key": "eval-generate"},
)
run = generation_response.json()
expected = fixture["expected"]
context_ref_ids = {context["contextRefId"] for context in run.get("contextRefs", [])}
context_chunk_ids = {context["chunkId"] for context in run.get("contextRefs", [])}
claim_supports = run.get("evaluation", {}).get("claimSupports", [])
claim_ids = [support.get("claimId") for support in claim_supports]

checks = [
    {
        "name": "project created",
        "passed": project_response.status_code == 201,
        "expected": 201,
        "actual": project_response.status_code,
    },
    {
        "name": "document uploaded",
        "passed": upload_response.status_code == 201,
        "expected": 201,
        "actual": upload_response.status_code,
    },
    {
        "name": "document approved",
        "passed": approve_response.json().get("approvalStatus") == "APPROVED",
        "expected": "APPROVED",
        "actual": approve_response.json().get("approvalStatus"),
    },
    {
        "name": "ingestion completed",
        "passed": ingest_response.json().get("status") == "COMPLETED",
        "expected": "COMPLETED",
        "actual": ingest_response.json().get("status"),
    },
    {
        "name": "walkthrough status",
        "passed": run.get("status") == expected["status"],
        "expected": expected["status"],
        "actual": run.get("status"),
    },
    {
        "name": "evaluation status",
        "passed": run.get("evaluationStatus") == expected["evaluationStatus"],
        "expected": expected["evaluationStatus"],
        "actual": run.get("evaluationStatus"),
    },
    {
        "name": "unsupported claim count",
        "passed": run.get("evaluation", {}).get("unsupportedClaimCount") == expected["unsupportedClaimCount"],
        "expected": expected["unsupportedClaimCount"],
        "actual": run.get("evaluation", {}).get("unsupportedClaimCount"),
    },
    {
        "name": "citation count",
        "passed": len(run.get("contextRefs", [])) >= expected["requiredCitations"],
        "expected": expected["requiredCitations"],
        "actual": len(run.get("contextRefs", [])),
    },
    {
        "name": "claim supports exist",
        "passed": bool(claim_supports),
        "expected": "non-empty claimSupports",
        "actual": len(claim_supports),
    },
    {
        "name": "claim supports map to context refs",
        "passed": all(
            support.get("supportStatus") == "SUPPORTED"
            and support.get("contextRefId") in context_ref_ids
            and support.get("chunkId") in context_chunk_ids
            for support in claim_supports
        ),
        "expected": "all supports map to retrieved context",
        "actual": claim_supports,
    },
    {
        "name": "claim ids unique",
        "passed": len(claim_ids) == len(set(claim_ids)),
        "expected": "unique claim ids",
        "actual": claim_ids,
    },
    {
        "name": "full context coverage",
        "passed": run.get("evaluation", {}).get("contextRefCoverage") == 1.0,
        "expected": 1.0,
        "actual": run.get("evaluation", {}).get("contextRefCoverage"),
    },
]

if run.get("contextRefs") and claim_supports:
    first_context = run["contextRefs"][0]
    first_support = claim_supports[0]
    negative_candidate = GeneratedScript(
        text=f"{run['acceptedScriptText']} NarraTwin guarantees hiring outcomes. [1]",
        claims=[
            ScriptClaim(
                claim_id=first_support["claimId"],
                text=run["acceptedScriptText"].split("[1]", maxsplit=1)[0].replace("For recruiters, ", "").strip(),
                citation_index=1,
                chunk_id=first_context["chunkId"],
                script_span_start=0,
                script_span_end=run["acceptedScriptText"].find("[1]") + 3,
            )
        ],
    )
    retrieved_context = stage4_service.walkthrough_runs[run["runId"]].retrieved_context
    negative_eval = evaluate_grounding(
        tenant_id=run["tenantId"],
        project_id=project_id,
        run_id="run_eval_negative",
        candidate=negative_candidate,
        retrieved_context=retrieved_context,
    )
    checks.append(
        {
            "name": "negative visible unsupported claim fails",
            "passed": negative_eval.evaluation_status == "FAILED",
            "expected": "FAILED",
            "actual": negative_eval.evaluation_status,
        }
    )

failed = [check for check in checks if not check["passed"]]
report = {
    "fixture": fixture["name"],
    "passed": not failed,
    "unsupported_claim_count": run.get("evaluation", {}).get("unsupportedClaimCount"),
    "checks": checks,
}
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

if failed:
    raise SystemExit(f"eval smoke failed; report written to {report_path}")

print(f"eval smoke report written to {report_path}")
print("eval smoke passed: Stage 4 grounded script has citations and no unsupported claims")
PY
