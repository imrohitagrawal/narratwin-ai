#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/reports/lighthouse"
PORT="${NARRATWIN_LIGHTHOUSE_PORT:-3300}"

mkdir -p "${REPORT_DIR}"
cd "${ROOT_DIR}/frontend"

if [ ! -d node_modules ]; then
  npm ci --strict-allow-scripts=true
fi

npm run build
if [ "${CI:-}" = "true" ]; then
  npx playwright install --with-deps chromium
elif [ "${PLAYWRIGHT_SKIP_INSTALL:-}" = "1" ]; then
  echo "Skipping Playwright browser install because PLAYWRIGHT_SKIP_INSTALL=1"
else
  npx playwright install chromium
fi

if [ -z "${CHROME_PATH:-}" ] && [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
fi

NARRATWIN_API_PROXY_TARGET="${NARRATWIN_API_PROXY_TARGET:-http://127.0.0.1:8000}" \
HOSTNAME=127.0.0.1 \
PORT="${PORT}" \
node .next/standalone/server.js > "${REPORT_DIR}/frontend-server.log" 2>&1 &
SERVER_PID=$!
trap 'kill "${SERVER_PID}" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}" >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:${PORT}" >/dev/null
node scripts/run-lighthouse.mjs "http://127.0.0.1:${PORT}"
