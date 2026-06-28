#!/usr/bin/env bash
set -euo pipefail

python -m py_compile scripts/guardrails_check.py
python scripts/guardrails_check.py
