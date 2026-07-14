#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

python3 scripts/ci/check_semgrep_security.py contract
uv run pip-audit --strict

TOOL_ENVIRONMENT="${PWD}/.uv-cache/semgrep-venv"
UV_PROJECT_ENVIRONMENT="${TOOL_ENVIRONMENT}" uv sync --project tools/semgrep --frozen --no-dev
TOOL_SITE_PACKAGES="$("${TOOL_ENVIRONMENT}/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
python3 scripts/ci/check_semgrep_security.py installed-tool --site-packages "${TOOL_SITE_PACKAGES}"
uv run pip-audit --strict --path "${TOOL_SITE_PACKAGES}"
