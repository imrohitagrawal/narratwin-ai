#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

uv run pip-audit
uv run bandit -r backend scripts -x scripts/quality -ll
uv run semgrep --config semgrep.yml --error backend frontend/src frontend/tests scripts tests .github/workflows/ci.yml .github/workflows/security.yml .github/workflows/eval-smoke.yml .github/workflows/quality.yml .github/workflows/quality-gates.yml docker-compose.yml backend/Dockerfile frontend/Dockerfile .env.example pyproject.toml frontend/package.json

if [ -f frontend/package-lock.json ]; then
  npm --prefix frontend audit --audit-level=high
fi

if command -v gitleaks >/dev/null 2>&1; then
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
