#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

bash scripts/ci/dependency-audit.sh
uv run uvicorn --version
uv run locust --version
uv run bandit -r backend scripts -x scripts/quality -ll

TOOL_ENVIRONMENT="${PWD}/.uv-cache/semgrep-venv"
UV_PROJECT_ENVIRONMENT="${TOOL_ENVIRONMENT}" bash scripts/ci/run-semgrep.sh

if [ -f frontend/package-lock.json ]; then
  npm --prefix frontend audit --audit-level=high
fi

python3 scripts/ci/check_gitleaks_regression.py

if command -v gitleaks >/dev/null 2>&1; then
  set +e
  printf '%s%s%s%s%s%s%s%s\n' 'api_' 'key = "' 'sk-proj-' 'a1B2c3D4' \
    'e5F6g7H8' 'i9J0k1L2' 'm3N4o5P6q7R8s9T0' '"' \
    | gitleaks stdin --redact --exit-code 86 --no-banner >/dev/null 2>&1
  GITLEAKS_CANARY_STATUS=$?
  set -e
  if [ "${GITLEAKS_CANARY_STATUS}" -ne 86 ]; then
    echo "Gitleaks real-secret canary failed closed with status ${GITLEAKS_CANARY_STATUS}."
    exit 1
  fi
  gitleaks detect --redact --source .
elif [ "${CI:-}" = "true" ] && [ "${NARRATWIN_GITLEAKS_ACTION_COMPLETED:-}" = "1" ]; then
  echo "Gitleaks action completed in CI; skipping duplicate CLI scan in wrapper."
elif [ "${NARRATWIN_ALLOW_LOCAL_SECRET_SCAN_FALLBACK:-}" = "1" ]; then
  echo "gitleaks CLI not installed locally; using explicit guardrail fallback."
  python3 scripts/guardrails_check.py
else
  echo "gitleaks CLI is required for local secret-scan parity."
  echo "Install gitleaks or set NARRATWIN_ALLOW_LOCAL_SECRET_SCAN_FALLBACK=1 for an explicit reduced local fallback."
  exit 1
fi
