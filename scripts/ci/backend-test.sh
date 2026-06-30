#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

if [ -d tests ]; then
  uv run pytest tests/unit tests/api
  exit 0
fi

python3 -m py_compile scripts/guardrails_check.py scripts/quality/*.py
python3 scripts/guardrails_check.py
