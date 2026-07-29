#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
RUN_ID="h2-${GITHUB_RUN_ID:-local}-$(date -u +%Y%m%dT%H%M%SZ)"
CANDIDATE="$ROOT/reports/heartbeat2/candidate"
PUBLISHED="$ROOT/reports/heartbeat2/published"
RUNTIME="$(mktemp -d "${TMPDIR:-/tmp}/narratwin-h2.XXXXXX")"
FIXTURE_SOURCE="$ROOT/tests/api/test_heartbeat1_a2_exclusion_api.py"
HEAD_SHA="${NARRATWIN_H2_EXPECTED_HEAD:-$(git rev-parse HEAD)}"
BACKEND_PID="" FRONTEND_PID="" ACTIVE_PID="" FAILURE_STAGE="preflight"

descendants() { local child; for child in $(pgrep -P "$1" 2>/dev/null || true); do descendants "$child"; echo "$child"; done; }
stop_owned() {
  local pid="${1:-}" child alive pids
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  pids="$pid $(descendants "$pid")"
  for child in $pids; do kill "$child" >/dev/null 2>&1 || true; done
  for _ in $(seq 1 5); do alive=false; for child in $pids; do kill -0 "$child" >/dev/null 2>&1 && alive=true; done; $alive || break; sleep 1; done
  for child in $pids; do kill -0 "$child" >/dev/null 2>&1 && kill -KILL "$child" >/dev/null 2>&1 || true; done
  wait "$pid" >/dev/null 2>&1 || true
}
cleanup() {
  stop_owned "$ACTIVE_PID"; stop_owned "$BACKEND_PID"; stop_owned "$FRONTEND_PID"
  case "$RUNTIME" in "${TMPDIR:-/tmp}"/narratwin-h2.*) rm -rf -- "$RUNTIME";; esac
}
trap cleanup EXIT INT TERM
bounded() {
  local limit="$1" rc; shift
  "$@" & ACTIVE_PID=$!
  for _ in $(seq 1 "$limit"); do
    if ! kill -0 "$ACTIVE_PID" >/dev/null 2>&1; then set +e; wait "$ACTIVE_PID"; rc=$?; set -e; ACTIVE_PID=""; return "$rc"; fi
    sleep 1
  done
  stop_owned "$ACTIVE_PID"; ACTIVE_PID=""; return 124
}
ready() {
  local url="$1" pid="$2"
  for _ in $(seq 1 30); do kill -0 "$pid" >/dev/null 2>&1 || return 1; curl -fsS "$url" >/dev/null 2>&1 && return 0; sleep 1; done
  return 1
}
withhold() {
  local retained="${TMPDIR:-/tmp}/narratwin-heartbeat2-failure-${RUN_ID}"
  stop_owned "$BACKEND_PID"; BACKEND_PID=""; stop_owned "$FRONTEND_PID"; FRONTEND_PID=""
  if uv run python -c 'from pathlib import Path; from scripts.ci.heartbeat1_evidence import scan_evidence; import sys; scan_evidence([Path(sys.argv[1])], controlled=Path(sys.argv[2]).read_bytes(), canary=Path(sys.argv[3]).read_bytes())' "$CANDIDATE" "$RUNTIME/internal.md" "$RUNTIME/canary.bin" >/dev/null 2>&1; then
    mv "$CANDIDATE" "$retained"
    printf 'stage=%s\nrunId=%s\nhead=%s\n' "$FAILURE_STAGE" "$RUN_ID" "$HEAD_SHA" >"$retained/failure-summary.txt"
    echo "Heartbeat 2 evidence withheld; zero-match diagnostics retained at $retained."
  else
    case "$CANDIDATE" in "$ROOT"/reports/heartbeat2/candidate) rm -rf -- "$CANDIDATE";; esac
    echo "Heartbeat 2 evidence withheld after privacy-scan failure; candidate deleted."
  fi
  exit 1
}

[ "$(git rev-parse HEAD)" = "$HEAD_SHA" ] || { echo "Heartbeat 2 exact head mismatch."; exit 1; }
[ -z "$(git status --porcelain=v1 --untracked-files=all)" ] || { echo "Heartbeat 2 requires a clean exact-head worktree."; exit 1; }
[ ! -e "$CANDIDATE" ] || { echo "Heartbeat 2 candidate path is not empty."; exit 1; }
mkdir -p "$PUBLISHED"
[ -z "$(find "$PUBLISHED" -mindepth 1 -print -quit)" ] || { echo "Heartbeat 2 published path is not empty."; exit 1; }
mkdir -p "$CANDIDATE"
export APP_ENV=test LLM_PROVIDER=mock EMBEDDING_PROVIDER=mock EVALUATION_PROVIDER=mock STORAGE_PROVIDER=local
export NARRATWIN_API_PROXY_TARGET="http://127.0.0.1:8122" NARRATWIN_STAGE4_STATE_FILE="$RUNTIME/regression-stage4.json" NARRATWIN_STAGE6_STATE_FILE="$RUNTIME/regression-stage6.json" NARRATWIN_STAGE7_STATE_FILE="$RUNTIME/regression-stage7.json"
export H2_CANDIDATE_DIR="$CANDIDATE" H2_PLAYWRIGHT_REPORT="$CANDIDATE/playwright.json" H2_STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
unset OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY GOOGLE_API_KEY OPENROUTER_API_KEY LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY

FAILURE_STAGE="materialize"
uv run python scripts/ci/heartbeat1_evidence.py materialize --fixture-source "$FIXTURE_SOURCE" --runtime-dir "$RUNTIME" --metadata-output "$CANDIDATE/forbidden-inputs.json" >"$CANDIDATE/materialize.log" 2>&1 || withhold
uv run python -c 'import ast,hashlib,sys; from pathlib import Path; tree=ast.parse(Path(sys.argv[1]).read_bytes()); data=next(v for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,(str,bytes)) and hashlib.sha256(v:=n.value.encode() if isinstance(n.value,str) else n.value).hexdigest()==sys.argv[3]); Path(sys.argv[2]).write_bytes(data)' "$ROOT/tests/api/test_stage6_multilingual_api.py" "$RUNTIME/public.md" "9cefe4184b2a67d4cdc56d66d005b90409e06ad449c4c426b7d6e012125bfcb6" || withhold
export H2_PUBLIC_FIXTURE="$RUNTIME/public.md"
FAILURE_STAGE="regressions"
bounded 90 bash -c 'uv run pytest -q -p no:cacheprovider tests/api/test_stage4_slice_api.py -k a1 && uv run pytest -q -p no:cacheprovider tests/api/test_heartbeat1_a2_exclusion_api.py && uv run pytest -q -p no:cacheprovider tests/api/test_stage6_multilingual_api.py tests/api/test_stage7_avatar_api.py' >"$CANDIDATE/regressions.log" 2>&1 || withhold
export NARRATWIN_STAGE4_STATE_FILE="$CANDIDATE/stage4-state.json" NARRATWIN_STAGE6_STATE_FILE="$CANDIDATE/stage6-state.json" NARRATWIN_STAGE7_STATE_FILE="$CANDIDATE/stage7-state.json"
FAILURE_STAGE="backend"
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8122 >"$CANDIDATE/backend.log" 2>&1 & BACKEND_PID=$!
ready "http://127.0.0.1:8122/api/v1/readyz" "$BACKEND_PID" || withhold
FAILURE_STAGE="frontend-build"
bounded 75 npm --prefix frontend run build >"$CANDIDATE/frontend-build.log" 2>&1 || withhold
cp -R frontend/.next/static frontend/.next/standalone/.next/static
if [ -d frontend/public ]; then
  cp -R frontend/public frontend/.next/standalone/public
else
  mkdir -p frontend/.next/standalone/public
fi
FAILURE_STAGE="frontend"
(cd "$ROOT/frontend" && exec env HOSTNAME=127.0.0.1 PORT=3122 npm start) >"$CANDIDATE/frontend.log" 2>&1 & FRONTEND_PID=$!
ready "http://127.0.0.1:3122" "$FRONTEND_PID" || withhold
FAILURE_STAGE="browser"
bounded 75 frontend/node_modules/.bin/playwright test --config frontend/playwright.heartbeat2.config.ts --output "$CANDIDATE/playwright-output" >"$CANDIDATE/browser.log" 2>&1 || withhold
TRACE_PATH="$(find "$CANDIDATE/playwright-output" -type f -name trace.zip -print)"
[ -n "$TRACE_PATH" ] && [ "$(printf '%s\n' "$TRACE_PATH" | wc -l | tr -d ' ')" = 1 ] || withhold
cp "$TRACE_PATH" "$CANDIDATE/trace.zip"
stop_owned "$BACKEND_PID"; BACKEND_PID=""; stop_owned "$FRONTEND_PID"; FRONTEND_PID=""
export H2_COMPLETED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
FAILURE_STAGE="verification"
VERIFY_ARGS=(--evidence "$CANDIDATE" --head "$HEAD_SHA" --run-id "$RUN_ID" --prepare --forbidden-file "$RUNTIME/internal.md" --forbidden-file "$RUNTIME/canary.bin")
[ "${GITHUB_ACTIONS:-}" = true ] && VERIFY_ARGS+=(--ci)
if ! uv run python -m scripts.ci.heartbeat2_evidence "${VERIFY_ARGS[@]}" >"$RUNTIME/verification.json" 2>"$RUNTIME/verification-error.json"; then
  cp "$RUNTIME/verification-error.json" "$CANDIDATE/verification-error.json"
  withhold
fi
if [ "${GITHUB_ACTIONS:-}" = true ]; then
  cp "$RUNTIME/verification.json" "$CANDIDATE/ci-verification.json"
  mv "$CANDIDATE" "$PUBLISHED/$RUN_ID"
  echo "Heartbeat 2 trusted evidence published."
else
  cp "$RUNTIME/verification.json" "$CANDIDATE/local-verification.json"
  echo "Heartbeat 2 local semantic evidence complete; execution authenticity remains unattested."
fi
