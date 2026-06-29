#!/usr/bin/env bash
set -euo pipefail

python3 -m py_compile scripts/guardrails_check.py
python3 scripts/guardrails_check.py
