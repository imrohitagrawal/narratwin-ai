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

scan_report_exists() {
  local output="$1"
  [ -s "${output}" ] && grep -q '"runs"' "${output}"
}

prepare_scan_output() {
  local output="$1"
  rm -f "${output}"
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

scan_with_dockerized_trivy_or_scout() {
  local image="$1"
  local output="$2"
  prepare_scan_output "${output}"
  set +e
  scan_with_trivy_container "${image}" "${output}"
  local scan_status=$?
  set -e
  if [ "${scan_status}" -eq 0 ]; then
    return 0
  fi
  if scan_report_exists "${output}"; then
    return "${scan_status}"
  fi
  if docker scout version >/dev/null 2>&1; then
    echo "Dockerized Trivy did not produce a scan report for ${image}; falling back to Docker Scout." >&2
    scan_with_docker_scout "${image}" "${output}"
    return
  fi
  return "${scan_status}"
}

scan_with_available_scanners() {
  local image="$1"
  local output="$2"
  local attempted=0
  local scan_status=1

  if command -v trivy >/dev/null 2>&1; then
    attempted=1
    prepare_scan_output "${output}"
    set +e
    scan_with_trivy "${image}" "${output}"
    scan_status=$?
    set -e
    if [ "${scan_status}" -eq 0 ]; then
      return 0
    fi
    if scan_report_exists "${output}"; then
      return "${scan_status}"
    fi
    echo "Local Trivy did not produce a usable SARIF report for ${image}; trying the next scanner." >&2
  fi

  if command -v grype >/dev/null 2>&1; then
    attempted=1
    prepare_scan_output "${output}"
    set +e
    scan_with_grype "${image}" "${output}"
    scan_status=$?
    set -e
    if [ "${scan_status}" -eq 0 ]; then
      return 0
    fi
    if scan_report_exists "${output}"; then
      return "${scan_status}"
    fi
    echo "Grype did not produce a usable SARIF report for ${image}; trying the next scanner." >&2
  fi

  if docker version >/dev/null 2>&1; then
    attempted=1
    set +e
    scan_with_dockerized_trivy_or_scout "${image}" "${output}"
    scan_status=$?
    set -e
    if [ "${scan_status}" -eq 0 ]; then
      return 0
    fi
    if scan_report_exists "${output}"; then
      return "${scan_status}"
    fi
    echo "Dockerized Trivy/Docker Scout did not produce a usable SARIF report for ${image}." >&2
  elif docker scout version >/dev/null 2>&1; then
    attempted=1
    prepare_scan_output "${output}"
    set +e
    scan_with_docker_scout "${image}" "${output}"
    scan_status=$?
    set -e
    if [ "${scan_status}" -eq 0 ]; then
      return 0
    fi
    if scan_report_exists "${output}"; then
      return "${scan_status}"
    fi
    echo "Docker Scout did not produce a usable SARIF report for ${image}." >&2
  fi

  if [ "${attempted}" -eq 1 ]; then
    return "${scan_status}"
  fi
  return 127
}

if scan_with_available_scanners "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-image-scan.sarif.json"; then
  :
else
  backend_status=$?
  if [ "${backend_status}" -ne 127 ]; then
    exit "${backend_status}"
  fi
  cat > "${REPORT_DIR}/docker-image-scan-unavailable.json" <<'JSON'
{"status":"tool_unavailable","required":"trivy, grype, dockerized trivy, or docker scout","budget":"no critical/high container vulnerabilities"}
JSON
  echo "Docker image vulnerability scanning requires trivy, grype, dockerized trivy, or docker scout."
  exit 1
fi

if scan_with_available_scanners "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-image-scan.sarif.json"; then
  :
else
  frontend_status=$?
  if [ "${frontend_status}" -ne 127 ]; then
    exit "${frontend_status}"
  fi
  cat > "${REPORT_DIR}/docker-image-scan-unavailable.json" <<'JSON'
{"status":"tool_unavailable","required":"trivy, grype, dockerized trivy, or docker scout","budget":"no critical/high container vulnerabilities"}
JSON
  echo "Docker image vulnerability scanning requires trivy, grype, dockerized trivy, or docker scout."
  exit 1
fi
