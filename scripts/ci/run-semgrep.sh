#!/usr/bin/env bash
set -euo pipefail

export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${PWD}/.uv-cache/semgrep-venv}"

readonly TOOL_PROJECT="tools/semgrep"
readonly TARGET_MANIFEST="scripts/ci/semgrep-targets.txt"
readonly SCAN_RESULT=".uv-cache/semgrep-scan.json"
readonly CANARY_RESULT=".uv-cache/semgrep-canary.json"
readonly SCAN_STDOUT=".uv-cache/semgrep-scan.stdout"
readonly CANARY_STDOUT=".uv-cache/semgrep-canary.stdout"

SEMGREP_TARGETS=()
while IFS= read -r target; do
  if [ -n "${target}" ] && [[ "${target}" != \#* ]]; then
    SEMGREP_TARGETS+=("${target}")
  fi
done < "${TARGET_MANIFEST}"

python3 scripts/ci/check_semgrep_security.py contract

uv run --project "${TOOL_PROJECT}" --frozen semgrep scan \
  --validate \
  --config semgrep.yml \
  --metrics=off

uv run --project "${TOOL_PROJECT}" --frozen semgrep \
  --config semgrep.yml \
  --error \
  --metrics=off \
  --json \
  --json-output "${SCAN_RESULT}" \
  "${SEMGREP_TARGETS[@]}" > "${SCAN_STDOUT}"
python3 scripts/ci/check_semgrep_security.py scan-result "${SCAN_RESULT}"

uv run --project "${TOOL_PROJECT}" --frozen semgrep \
  --config scripts/ci/semgrep-canary.yml \
  --metrics=off \
  --json \
  --json-output "${CANARY_RESULT}" \
  scripts/ci/fixtures/semgrep/clean.py \
  scripts/ci/fixtures/semgrep/positive.py > "${CANARY_STDOUT}"
python3 scripts/ci/check_semgrep_security.py canary-result "${CANARY_RESULT}"
