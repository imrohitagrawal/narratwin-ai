#!/usr/bin/env bash
set -euo pipefail

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"

docker run --rm --entrypoint /app/.venv/bin/python "${BACKEND_IMAGE}" -c '
import importlib.metadata
import importlib.util
import ssl
from pathlib import Path

records = Path("/lib/apk/db/installed").read_text(encoding="utf-8").split("\n\n")
packages = {}
for record in records:
    fields = dict(
        line.split(":", 1) for line in record.splitlines() if ":" in line
    )
    if "P" in fields and "V" in fields:
        packages[fields["P"]] = fields["V"]

if not ssl.OPENSSL_VERSION.startswith("OpenSSL 3.3.7 "):
    raise SystemExit(f"backend image has unexpected TLS library {ssl.OPENSSL_VERSION}")
if not (
    packages["libcrypto3"] == "3.3.7-r0"
    and packages["libssl3"] == "3.3.7-r0"
):
    raise SystemExit("backend image TLS package inventory drifted")
context = ssl.create_default_context()
if context.verify_mode != ssl.CERT_REQUIRED or not Path(ssl.get_default_verify_paths().cafile or "").is_file():
    raise SystemExit("backend image TLS certificate verification is unavailable")
if importlib.util.find_spec("pip") is not None or importlib.util.find_spec("_sqlite3") is not None:
    raise SystemExit("backend image retained a build-only package manager or database capability")

click_version = tuple(int(part) for part in importlib.metadata.version("click").split("."))
if click_version < (8, 3, 3):
    raise SystemExit(f"backend image contains vulnerable Click {click_version}")
try:
    importlib.metadata.version("semgrep")
except importlib.metadata.PackageNotFoundError:
    pass
else:
    raise SystemExit("backend image must not contain Semgrep")
print("backend image dependency inventory: TLS and Click are fixed; Semgrep is absent")
'
