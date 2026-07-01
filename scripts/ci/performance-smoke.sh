#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

uv run python -c "import locust; print(locust.__version__)" >/dev/null 2>/dev/null
uv run pytest tests/api/test_stage8_hardening_api.py
