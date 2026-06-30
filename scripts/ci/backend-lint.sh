#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

uv run ruff check backend scripts tests
uv run mypy backend scripts tests
python3 -m py_compile scripts/guardrails_check.py scripts/quality/*.py backend/app/*.py
