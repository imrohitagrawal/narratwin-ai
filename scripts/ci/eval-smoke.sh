#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

mkdir -p reports/eval-smoke

uv run python - <<'PY'
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app

fixture_path = Path("evals/smoke/stage3_health_fixture.json")
report_path = Path("reports/eval-smoke/stage3-health-report.json")
fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

client = TestClient(app)
responses = {
    "/healthz": client.get("/healthz"),
    "/api/v1/healthz": client.get("/api/v1/healthz"),
}
checks = []
for route, response in responses.items():
    payload = response.json()
    checks.append(
        {
            "name": f"{route} status code",
            "passed": response.status_code == 200,
            "expected": 200,
            "actual": response.status_code,
        }
    )
    checks.append(
        {
            "name": f"{route} exact health payload",
            "passed": payload == fixture["expected"],
            "expected": fixture["expected"],
            "actual": payload,
        }
    )
    for key, expected in fixture["expected"].items():
        checks.append(
            {
                "name": f"{route} {key}",
                "passed": payload.get(key) == expected,
                "expected": expected,
                "actual": payload.get(key),
            }
        )
unsupported_claims = [check for check in checks if not check["passed"]]
report = {
    "fixture": fixture["name"],
    "passed": not unsupported_claims,
    "unsupported_claim_count": len(unsupported_claims),
    "checks": checks,
}
report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

if len(unsupported_claims) > fixture["max_unsupported_claims"]:
    raise SystemExit(f"eval smoke failed; report written to {report_path}")

print(f"eval smoke report written to {report_path}")
print("eval smoke passed: health-only foundation contract is stable")
PY
