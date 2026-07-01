#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-reports/security}"
mkdir -p "${REPORT_DIR}"
REPORT_DIR_ABS="$(cd "${REPORT_DIR}" && pwd)"

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-narratwin-ai-frontend:ci}"
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f}"

scan_with_docker_scout() {
  local image="$1"
  local output="$2"
  docker scout cves \
    --only-severity critical,high \
    --exit-code \
    --format sarif \
    --output "${output}" \
    "local://${image}"
}

scan_with_trivy() {
  local image="$1"
  local output="$2"
  trivy image \
    --severity CRITICAL,HIGH \
    --exit-code 1 \
    --format sarif \
    --output "${output}" \
    "${image}"
}

scan_with_grype() {
  local image="$1"
  local output="$2"
  grype "${image}" \
    --fail-on high \
    --output sarif="${output}"
}

scan_with_trivy_container() {
  local image="$1"
  local output="$2"
  docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${REPORT_DIR_ABS}:/reports" \
    "${TRIVY_IMAGE}" image \
    --severity CRITICAL,HIGH \
    --exit-code 1 \
    --format sarif \
    --output "/reports/$(basename "${output}")" \
    "${image}"
}

if command -v trivy >/dev/null 2>&1; then
  scan_with_trivy "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-image-scan.sarif.json"
  scan_with_trivy "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-image-scan.sarif.json"
elif command -v grype >/dev/null 2>&1; then
  scan_with_grype "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-image-scan.sarif.json"
  scan_with_grype "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-image-scan.sarif.json"
elif docker version >/dev/null 2>&1; then
  scan_with_trivy_container "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-image-scan.sarif.json"
  scan_with_trivy_container "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-image-scan.sarif.json"
elif docker scout version >/dev/null 2>&1; then
  scan_with_docker_scout "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-image-scan.sarif.json"
  scan_with_docker_scout "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-image-scan.sarif.json"
else
  cat > "${REPORT_DIR}/docker-image-scan-unavailable.json" <<'JSON'
{"status":"tool_unavailable","required":"trivy, grype, dockerized trivy, or docker scout","budget":"no critical/high container vulnerabilities"}
JSON
  echo "Docker image vulnerability scanning requires trivy, grype, dockerized trivy, or docker scout."
  exit 1
fi
