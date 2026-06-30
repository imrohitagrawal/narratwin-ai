#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

mkdir -p reports/eval-smoke

uv run python - <<'PY'
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app, reset_app_state_for_tests

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
]

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
