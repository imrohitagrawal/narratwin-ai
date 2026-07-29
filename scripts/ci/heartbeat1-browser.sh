#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
RUN_ID="h1-${GITHUB_RUN_ID:-local}-$(date -u +%Y%m%dT%H%M%SZ)"
CANDIDATE="$ROOT/reports/heartbeat1/candidate"
PUBLISH_ROOT="$ROOT/reports/heartbeat1/published"
RUNTIME="$(mktemp -d "${TMPDIR:-/tmp}/narratwin-h1.XXXXXX")"
STATE="$CANDIDATE/state.json"
FIXTURE_SOURCE="$ROOT/tests/api/test_heartbeat1_a2_exclusion_api.py"
HEAD_SHA="$(git rev-parse HEAD)"
BACKEND_PID="" FRONTEND_PID="" ACTIVE_PID=""

owned_descendants() {
  local parent="$1" child
  for child in $(pgrep -P "$parent" 2>/dev/null || true); do owned_descendants "$child"; echo "$child"; done
}
stop_owned() {
  local pid="${1:-}" pids candidate alive
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  pids="$pid $(owned_descendants "$pid")"
  for candidate in $pids; do kill "$candidate" >/dev/null 2>&1 || true; done
  for _ in $(seq 1 5); do
    alive=false; for candidate in $pids; do kill -0 "$candidate" >/dev/null 2>&1 && alive=true; done
    $alive || break; sleep 1
  done
  for candidate in $pids; do kill -0 "$candidate" >/dev/null 2>&1 && kill -KILL "$candidate" >/dev/null 2>&1 || true; done
  wait "$pid" >/dev/null 2>&1 || true
}
cleanup() {
  rm -f "$RUNTIME/public.md" "$RUNTIME/internal.md" "$RUNTIME/canary.bin"
  stop_owned "$ACTIVE_PID"; stop_owned "$BACKEND_PID"; stop_owned "$FRONTEND_PID"
  case "$RUNTIME" in "${TMPDIR:-/tmp}"/narratwin-h1.*) rm -rf -- "$RUNTIME";; esac
}
trap cleanup EXIT INT TERM

bounded() {
  local limit="$1" elapsed rc; shift
  elapsed=$((295 - SECONDS)); (( elapsed < limit )) && limit="$elapsed"
  (( limit > 0 )) || return 124
  "$@" & ACTIVE_PID=$!
  for _ in $(seq 1 "$limit"); do
    if ! kill -0 "$ACTIVE_PID" >/dev/null 2>&1; then
      set +e; wait "$ACTIVE_PID"; rc=$?; set -e; ACTIVE_PID=""; return "$rc"
    fi
    sleep 1
  done
  stop_owned "$ACTIVE_PID"; ACTIVE_PID=""; return 124
}
ready() {
  local url="$1" pid="$2" limit
  limit=$((295 - SECONDS)); (( limit > 30 )) && limit=30
  (( limit > 0 )) || return 1
  for _ in $(seq 1 "$limit"); do
    kill -0 "$pid" >/dev/null 2>&1 || return 1
    curl -fsS "$url" >/dev/null 2>&1 && return 0
    sleep 1
  done
  return 1
}
start_backend() {
  local log="$1"
  NARRATWIN_STAGE4_STATE_FILE="$STATE" uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8122 >"$log" 2>&1 &
  BACKEND_PID=$!
  ready "http://127.0.0.1:8122/api/v1/readyz" "$BACKEND_PID"
}
scan_candidate() {
  bounded 60 uv run python scripts/ci/heartbeat1_evidence.py scan \
    --fixture-source "$FIXTURE_SOURCE" --run-id "$RUN_ID" --head-sha "$HEAD_SHA" \
    --browser-entry frontend/tests/heartbeat1-browser.spec.ts --input "$CANDIDATE" \
    --output "$RUNTIME/privacy.json" --failure-output "$RUNTIME/failure.json" \
    >"$RUNTIME/scanner.log" 2>&1
}
withhold() {
  rm -f "$RUNTIME/public.md" "$RUNTIME/internal.md" "$RUNTIME/canary.bin"
  stop_owned "$BACKEND_PID"; BACKEND_PID=""; stop_owned "$FRONTEND_PID"; FRONTEND_PID=""
  scan_candidate || true
  discard
}
discard() {
  case "$CANDIDATE" in "$ROOT"/reports/heartbeat1/candidate) rm -rf -- "$CANDIDATE";; esac
  echo "Heartbeat 1B evidence withheld."
  exit 1
}

[ -z "$(git status --porcelain=v1 --untracked-files=all)" ] || { echo "Heartbeat 1B requires a clean exact-head worktree."; exit 1; }
[ ! -e "$CANDIDATE" ] || { echo "Heartbeat 1B candidate path is not empty."; exit 1; }
mkdir -p "$PUBLISH_ROOT"
[ -z "$(find "$PUBLISH_ROOT" -mindepth 1 -print -quit)" ] || { echo "Heartbeat 1B published path is not empty."; exit 1; }
mkdir -p "$CANDIDATE"
export APP_ENV=test LLM_PROVIDER=mock EMBEDDING_PROVIDER=mock EVALUATION_PROVIDER=mock STORAGE_PROVIDER=local
export PYTEST_ADDOPTS="--tb=no --assert=plain"
unset OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY GOOGLE_API_KEY OPENROUTER_API_KEY LANGFUSE_PUBLIC_KEY LANGFUSE_SECRET_KEY
export NARRATWIN_API_PROXY_TARGET="http://127.0.0.1:8122" NARRATWIN_HEARTBEAT1_RUN_ID="$RUN_ID"
export NARRATWIN_HEARTBEAT1_CANDIDATE_DIR="$CANDIDATE" NARRATWIN_HEARTBEAT1_HANDOFF="$CANDIDATE/handoff.json"

bounded 85 bash -c 'uv run pytest -p no:cacheprovider tests/api/test_stage4_slice_api.py -k a1 && uv run pytest -p no:cacheprovider tests/api/test_heartbeat1_a2_exclusion_api.py' \
  >"$CANDIDATE/regressions.log" 2>&1 || withhold
uv run python scripts/ci/heartbeat1_evidence.py materialize --fixture-source "$FIXTURE_SOURCE" \
  --runtime-dir "$RUNTIME" --metadata-output "$CANDIDATE/runtime-input.json" \
  >"$CANDIDATE/materialize.log" 2>&1 || withhold
rm -f "$RUNTIME/canary.bin"
export NARRATWIN_HEARTBEAT1_PUBLIC_FILE="$RUNTIME/public.md" NARRATWIN_HEARTBEAT1_INTERNAL_FILE="$RUNTIME/internal.md"

start_backend "$CANDIDATE/backend-1.log" || withhold
(cd "$ROOT/frontend" && exec node_modules/.bin/next dev --hostname 127.0.0.1 --port 3122) >"$CANDIDATE/frontend.log" 2>&1 &
FRONTEND_PID=$!
ready "http://127.0.0.1:3122" "$FRONTEND_PID" || withhold
OWNED_FRONTEND_PID="$FRONTEND_PID"
bounded 85 env NARRATWIN_HEARTBEAT1_PHASE=submit frontend/node_modules/.bin/playwright test \
  --config frontend/playwright.heartbeat1.config.ts >"$CANDIDATE/submit.log" 2>&1 || withhold
rm -f "$RUNTIME/public.md" "$RUNTIME/internal.md" "$RUNTIME/canary.bin"

FIRST_PID="$BACKEND_PID"; stop_owned "$BACKEND_PID"; BACKEND_PID=""
SNAPSHOT_SHA="$(shasum -a 256 "$STATE" | awk '{print $1}')"
start_backend "$CANDIDATE/backend-2.log" || withhold
[ "$FIRST_PID" != "$BACKEND_PID" ] || withhold
SECOND_PID="$BACKEND_PID"
bounded 85 env NARRATWIN_HEARTBEAT1_PHASE=reopen frontend/node_modules/.bin/playwright test \
  --config frontend/playwright.heartbeat1.config.ts >"$CANDIDATE/reopen.log" 2>&1 || withhold
for artifact in handoff.json submit-result.json browser-result.json reopen-owner-dom.txt reopen-owner.png reopen-dom.txt reopen.png reopen-trace.zip state.json; do
  [ -s "$CANDIDATE/$artifact" ] || withhold
done
if [ -z "$FRONTEND_PID" ] || ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then withhold; fi
stop_owned "$BACKEND_PID"; BACKEND_PID=""; stop_owned "$FRONTEND_PID"; FRONTEND_PID=""
[ "$SNAPSHOT_SHA" = "$(shasum -a 256 "$STATE" | awk '{print $1}')" ] || withhold
printf 'runId=%s\nfrontendPid=%s\nbackend1Pid=%s\nbackend2Pid=%s\nbackend1StoppedAndWaited=true\nfrontendContinuous=true\nsnapshotSha256=%s\ntotalSeconds=%s\n' \
  "$RUN_ID" "$OWNED_FRONTEND_PID" "$FIRST_PID" "$SECOND_PID" "$SNAPSHOT_SHA" "$SECONDS" >"$CANDIDATE/run-metadata.txt"
(( SECONDS <= 300 )) || withhold
scan_candidate || discard
(( SECONDS <= 300 )) || discard
mv "$CANDIDATE" "$PUBLISH_ROOT/$RUN_ID"
mv "$RUNTIME/privacy.json" "$PUBLISH_ROOT/$RUN_ID/privacy.json"
echo "Heartbeat 1B privacy-safe evidence published."
