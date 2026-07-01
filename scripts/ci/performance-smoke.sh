#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/reports/performance"
PORT="${NARRATWIN_PERFORMANCE_PORT:-8400}"

uv run python -c "import locust; print(locust.__version__)" >/dev/null 2>/dev/null
uv run pytest tests/api/test_stage8_hardening_api.py

mkdir -p "${REPORT_DIR}"
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port "${PORT}" \
  > "${REPORT_DIR}/stage8-api-server.log" 2>&1 &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/v1/healthz" >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:${PORT}/api/v1/healthz" >/dev/null
uv run locust \
  -f perf/stage8_locustfile.py \
  --headless \
  --users "${NARRATWIN_LOCUST_USERS:-4}" \
  --spawn-rate "${NARRATWIN_LOCUST_SPAWN_RATE:-4}" \
  --run-time "${NARRATWIN_LOCUST_RUN_TIME:-10s}" \
  --host "http://127.0.0.1:${PORT}" \
  --csv "${REPORT_DIR}/stage8-locust" \
  --only-summary
