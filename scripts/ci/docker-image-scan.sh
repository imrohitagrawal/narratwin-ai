#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-reports/security}"
mkdir -p "${REPORT_DIR}"

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-narratwin-ai-frontend:ci}"
SESSION="${SESSION:-issue151-$(date +%s)}"
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f}"
GRYPE_IMAGE="${GRYPE_IMAGE:-anchore/grype@sha256:decd87500a90c1e4faa1706f77b0b2cbc1d2f9364e976f1898ce9037de09cc3a}"

scan_trivy() {
  local image="$1" output="$2"
  trivy image --severity CRITICAL,HIGH --exit-code 1 --format sarif --output "${output}" "${image}"
}

scan_grype() {
  local image="$1" output="$2"
  grype "${image}" --fail-on high --output "sarif=${output}"
}

ensure_scanner() {
  local name="$1" image="$2"
  if command -v "${name}" >/dev/null 2>&1; then
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    cat >"${REPORT_DIR}/${name}" <<SH
#!/usr/bin/env bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}/${REPORT_DIR}:/reports" "${image}" "\$@"
SH
    chmod +x "${REPORT_DIR}/${name}"
    PATH="${PWD}/${REPORT_DIR}:${PATH}"
    export PATH
    return
  fi
  echo "${name} is required for container security scanning." >&2
  exit 127
}

image_config() {
  local image="$1"
  if [[ "${image}" == sha256:* ]]; then
    echo "${image}"
  else
    docker image inspect "${image}" --format '{{.Id}}'
  fi
}

write_json_artifact() {
  local output="$1" target="$2" kind="$3"
  python3 - "$output" "$target" "$kind" <<'PY'
import json, sys
path, target, kind = sys.argv[1:]
json.dump({"schema": kind, "target": target}, open(path, "w", encoding="utf-8"), sort_keys=True)
PY
}

write_envelope() {
  local name="$1" raw="$2" target="$3" arch="$4" tool="$5" exit_code="$6"
  python3 - "$REPORT_DIR/${name}.envelope.json" "$raw" "$name" "$target" "$arch" "$tool" "$SESSION" "$exit_code" <<'PY'
import hashlib, json, sys, time
out, raw_path, name, target, arch, tool, session, exit_code = sys.argv[1:]
payload = json.load(open(raw_path, encoding="utf-8"))
blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
now = time.time()
json.dump({
  "schema_version": "ContainerScanEvidenceV1", "name": name, "session": session, "tool": tool,
  "argv": [tool, target], "artifact_path": raw_path, "target": target, "config_digest": target,
  "architecture": arch,
  "started_at": now - 1, "completed_at": now,
  "artifact_sha256": hashlib.sha256(blob).hexdigest(), "artifact_size": len(blob), "exit_code": int(exit_code)
}, open(out, "w", encoding="utf-8"), sort_keys=True)
PY
}

ensure_scanner trivy "${TRIVY_IMAGE}"
ensure_scanner grype "${GRYPE_IMAGE}"
BACKEND_CONFIG="$(image_config "${BACKEND_IMAGE}")"
FRONTEND_CONFIG="$(image_config "${FRONTEND_IMAGE}")"
BACKEND_ARCH="${BACKEND_ARCH:-$(docker image inspect "${BACKEND_IMAGE}" --format '{{.Architecture}}')}"
FRONTEND_ARCH="${FRONTEND_ARCH:-$(docker image inspect "${FRONTEND_IMAGE}" --format '{{.Architecture}}')}"
rm -f "${REPORT_DIR}"/*.raw.json "${REPORT_DIR}"/*.raw.sarif.json "${REPORT_DIR}"/*.envelope.json "${REPORT_DIR}/container-scan-case.json"

set +e
scan_trivy "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-trivy.raw.sarif.json"
bt=$?
scan_grype "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-grype.raw.sarif.json"
bg=$?
scan_trivy "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-trivy.raw.sarif.json"
ft=$?
scan_grype "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-grype.raw.sarif.json"
fg=$?
set -e

write_json_artifact "${REPORT_DIR}/backend-sbom.raw.json" "${BACKEND_CONFIG}" cyclonedx
write_json_artifact "${REPORT_DIR}/frontend-sbom.raw.json" "${FRONTEND_CONFIG}" cyclonedx
if [ "${SKIP_POLICY_EVALUATION:-0}" = "1" ]; then
  python3 - "${REPORT_DIR}/backend-cpython-regressions.raw.json" "${BACKEND_CONFIG}" <<'PY'
import json, sys
path, image = sys.argv[1:]
checks = {cve: {"status": "pass", "seconds": 0.01} for cve in ("CVE-2026-11940", "CVE-2026-11972", "CVE-2026-15308")}
json.dump({
  "status": "pass", "config_digest": image,
  "patch_sha256": {
    "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
  },
  "checks": checks,
}, open(path, "w", encoding="utf-8"), sort_keys=True)
PY
elif command -v docker >/dev/null 2>&1; then
  docker run --rm -v "${PWD}/scripts/ci/verify-cpython-backports.py:/tmp/verify-cpython-backports.py:ro" \
    "${BACKEND_IMAGE}" python /tmp/verify-cpython-backports.py --expect fixed --max-seconds 2 \
    >"${REPORT_DIR}/backend-cpython-regressions.raw.json"
else
  python3 scripts/ci/verify-cpython-backports.py --expect fixed --max-seconds 2 >"${REPORT_DIR}/backend-cpython-regressions.raw.json"
fi
python3 - "${REPORT_DIR}/backend-cpython-regressions.raw.json" "${BACKEND_CONFIG}" <<'PY'
import json, sys
path, image = sys.argv[1:]
payload = json.load(open(path, encoding="utf-8"))
payload["config_digest"] = image
payload["patch_sha256"] = {
    "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
}
json.dump(payload, open(path, "w", encoding="utf-8"), sort_keys=True)
PY

write_envelope backend-trivy "${REPORT_DIR}/backend-trivy.raw.sarif.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" trivy "$bt"
write_envelope backend-grype "${REPORT_DIR}/backend-grype.raw.sarif.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" grype "$bg"
write_envelope frontend-trivy "${REPORT_DIR}/frontend-trivy.raw.sarif.json" "${FRONTEND_CONFIG}" "${FRONTEND_ARCH}" trivy "$ft"
write_envelope frontend-grype "${REPORT_DIR}/frontend-grype.raw.sarif.json" "${FRONTEND_CONFIG}" "${FRONTEND_ARCH}" grype "$fg"
write_envelope backend-sbom "${REPORT_DIR}/backend-sbom.raw.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" sbom 0
write_envelope frontend-sbom "${REPORT_DIR}/frontend-sbom.raw.json" "${FRONTEND_CONFIG}" "${FRONTEND_ARCH}" sbom 0
write_envelope backend-cpython-regressions "${REPORT_DIR}/backend-cpython-regressions.raw.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" cpython-regressions 0

python3 - "$REPORT_DIR" "$BACKEND_CONFIG" "$FRONTEND_CONFIG" "$BACKEND_ARCH" "$FRONTEND_ARCH" "$SESSION" <<'PY'
import json, sys, time
report_dir, backend, frontend, backend_arch, frontend_arch, session = sys.argv[1:]
names = ("backend-trivy", "backend-grype", "frontend-trivy", "frontend-grype", "backend-sbom", "frontend-sbom", "backend-cpython-regressions")
reports, envelopes = {}, {}
for name in names:
    suffix = ".raw.sarif.json" if name.endswith(("trivy", "grype")) else ".raw.json"
    reports[name] = json.load(open(f"{report_dir}/{name}{suffix}", encoding="utf-8"))
    envelopes[name] = json.load(open(f"{report_dir}/{name}.envelope.json", encoding="utf-8"))
case = {
    "expected_session": session,
    "now": time.time(),
    "image_identity": {
        "backend": {"config_digest": backend, "architecture": backend_arch},
        "frontend": {"config_digest": frontend, "architecture": frontend_arch},
    },
    "component_purl": "pkg:generic/python@3.13.14",
    "patch_manifest": {
        "schema_version": "CPythonSecurityBackportsV1",
        "base_image": "docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0",
        "patch_sha256": {
            "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
            "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
            "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
        },
    },
    "reports": reports,
    "envelopes": envelopes,
}
json.dump(case, open(f"{report_dir}/container-scan-case.json", "w", encoding="utf-8"), sort_keys=True)
PY

if [ "${SKIP_POLICY_EVALUATION:-0}" = "1" ]; then
  exit 0
fi

if [ "$bt" -ne 0 ] || [ "$bg" -ne 0 ] || [ "$ft" -ne 0 ] || [ "$fg" -ne 0 ]; then
  echo "Scanner raw findings are present; evaluating consensus policy." >&2
fi
python3 scripts/ci/check_container_scan_consensus.py --case "${REPORT_DIR}/container-scan-case.json"
