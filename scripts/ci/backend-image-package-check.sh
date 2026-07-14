#!/usr/bin/env bash
set -euo pipefail

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"

docker run --rm --entrypoint /app/.venv/bin/python "${BACKEND_IMAGE}" -c '
import importlib.metadata

click_version = tuple(int(part) for part in importlib.metadata.version("click").split("."))
if click_version < (8, 3, 3):
    raise SystemExit(f"backend image contains vulnerable Click {click_version}")
try:
    importlib.metadata.version("semgrep")
except importlib.metadata.PackageNotFoundError:
    pass
else:
    raise SystemExit("backend image must not contain Semgrep")
print("backend image dependency inventory: Click is fixed; Semgrep is absent")
'
