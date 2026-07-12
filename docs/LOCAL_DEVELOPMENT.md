# Local Development

This guide explains how to work on NarraTwin AI before and after application code exists.

## Current repo state

The repo is currently in Stage 3 repo foundation and CI/CD quality-gate
hardening mode. Backend and frontend feature workflows still wait for Stage 4,
but dependency manifests, CI wrappers, and a minimal frontend scaffold now exist.

## Prerequisites

Recommended local tools:

```bash
brew install git gh python@3.13 node docker ripgrep ffmpeg
```

Recommended optional tools:

```bash
brew install gitleaks
python3 -m pip install uv==0.11.18
npm install -g npm
```

## Clone

```bash
git clone https://github.com/imrohitagrawal/narratwin-ai.git
cd narratwin-ai
git checkout main
git pull
```

## Branching

Use one branch per stage or vertical slice:

```bash
git checkout -b docs/stage0-prd-hardening
```

Use git worktrees only for parallel Codex tasks that touch different files:

```bash
git worktree add ../narratwin-stage1 stage1/architecture-hardening
```

Do not run two live Codex sessions against the same files in the same working tree.

## Environment

Copy the example env file only when implementation begins:

```bash
cp .env.example .env
```

Do not commit `.env` or real provider keys.

Optional local durable state can be enabled by setting `NARRATWIN_STATE_DIR` in
`.env`, for example:

```bash
NARRATWIN_STATE_DIR=./outputs/state
```

When set, Stage 4 project/document/run/RAG state, Stage 6 multilingual
idempotency replay state, and Stage 7 avatar render/idempotency/artifact metadata
are written as local JSON snapshots. Leave it blank for process-local test
isolation.

Stage 7 restored render rows are treated as untrusted local state. Local restore
keeps only terminal completed render records with legal status-history order, a
mandatory matching persisted render request checksum built from the canonical
source evaluation checksum and idempotency scope/key, checksum-bound artifacts,
matching consumed-consent bindings, and succeeded idempotency records whose
stored request checksum, canonical endpoint, and scope/key still match the
restored render or consent record. Corrupt render rows, stale checksum-bound
replay rows, failed idempotency rows, inconsistent cross-scope render or
idempotency rows, wrong-endpoint idempotency rows, and malformed artifact
metadata rows are skipped without enabling external providers in local/dev/test.
These checks detect malformed or inconsistent snapshot data; they do not make the
local JSON snapshot tamper-proof against a fully rewritten self-consistent file.

Treat these snapshots as sensitive local data. They can include uploaded
document text, retrieved chunks/context, generated scripts, evaluation details,
translations/subtitles, avatar artifact payloads, base64 content, and metadata.
Keep the directory ignored, do not commit it, and delete it when a local review
session no longer needs restart replay evidence.

## Local quality commands

Preferred command:

```bash
make quality
```

Stage-specific command:

```bash
make stage3-quality
```

`make stage3-quality` is the full local Stage 3 gate. It runs the Stage 3
scope/docs contract, backend lint/typecheck, backend unit/API tests, frontend
lint/typecheck/unit/build, production Playwright smoke, dependency/security
scans, eval smoke, and Docker image builds.

The dependency/security wrapper requires the Gitleaks CLI for local parity with
CI. For offline local development only, set
`NARRATWIN_ALLOW_LOCAL_SECRET_SCAN_FALLBACK=1` to use the repository guardrail
secret scan as an explicit reduced fallback.

Install Python dependencies:

```bash
uv sync --frozen
```

Install frontend dependencies:

```bash
npm --prefix frontend ci --strict-allow-scripts=true
```

Run repo foundation wrappers directly:

```bash
bash scripts/ci/backend-lint.sh
bash scripts/ci/backend-test.sh
bash scripts/ci/frontend-build.sh
bash scripts/ci/frontend-smoke.sh
bash scripts/ci/dependency-security.sh
bash scripts/ci/docker-build.sh
bash scripts/ci/eval-smoke.sh
```

Focused CH-01 migration-baseline checks:

```bash
uv run pytest -p no:cacheprovider tests/unit/test_storage_migrations.py
uv run pytest -p no:cacheprovider tests/unit/test_phase1_closure_docs.py
```

Focused CH-02 ACID/CAS kernel checks:

```bash
uv run pytest -p no:cacheprovider tests/unit/test_postgres_state.py
uv run pytest -p no:cacheprovider tests/unit/test_phase1_closure_docs.py -k ch02
```

Focused CH-03 Stage 4 durable graph checks:

```bash
uv run pytest -p no:cacheprovider tests/unit/test_stage4_durable_graph.py
uv run pytest -p no:cacheprovider tests/unit/test_phase1_closure_docs.py -k ch03
```

Focused CH-06 committed-outbox checks:

```bash
uv run pytest -p no:cacheprovider tests/unit/test_postgres_state.py -k outbox
uv run pytest -p no:cacheprovider tests/unit/test_postgres_state.py
uv run pytest -p no:cacheprovider tests/unit/test_phase1_closure_docs.py -k ch06
```

If `make` is unavailable, run the closest applicable checks manually:

```bash
git status --short
git diff --check
```

Backend, frontend, and dependency-security wrappers are now present. They must
continue to avoid paid providers, real provider keys, and product feature
implementation before the approved Stage 4 slice.

Local Compose includes localhost-bound Postgres and Redis services for Stage 4
readiness only. Vector storage remains disabled in Stage 3 until the Chroma
adapter decision is locked.

`scripts/ci/frontend-smoke.sh` installs Chromium for Playwright smoke locally
unless `PLAYWRIGHT_SKIP_INSTALL=1` is set. CI always installs the browser with
system dependencies before running smoke.

Health-check-only local services:

```bash
uv run uvicorn backend.app.main:app --reload
npm --prefix frontend run dev
docker compose up --build
```

Health, readiness, and operational posture endpoints are:

- `/healthz`
- `/readyz`
- `/api/v1/healthz`
- `/api/v1/readyz`
- `/api/v1/ops/status`

## Codex workflow

Use this order:

1. Ask Codex to read `AGENTS.md`.
2. Ask Codex to read `docs/AI_BUILD_BRIEF.md`.
3. Ask Codex to read `docs/SKILL_EXECUTION_PLAN.md` and `docs/SKILL_TRUST_REVIEW.md`.
4. Give Codex one issue or one stage only.
5. Require a short plan before edits.
6. Require changed-file summary after edits.
7. Run local gates.
8. Open a PR.

## Plan mode vs edit mode

Use planning/read-only mode for:

- repo audit
- PRD review
- architecture review
- skill trust review
- issue decomposition
- reviewer pass

Use edit mode only when:

- the current stage is approved
- files to touch are clear
- stop/go gates are known
- the task is scoped to one issue or slice

## Before pushing

```bash
git status --short
git diff --check
make quality
```

If a command is not available yet, document why it is not applicable.

## Recovery

If Codex starts broad scaffolding:

```bash
git status --short
git diff
```

Then revert unrelated files:

```bash
git restore <path>
```

If Codex adds secrets or unsafe files:

```bash
git restore <path>
```

Then rotate any exposed secret before continuing.

## First implementation target

Do not build avatar video first. Slice 1 is:

```text
project creation
→ markdown/text upload
→ ingestion/chunking/storage
→ retrieval
→ grounded walkthrough script
→ unsupported-claim evaluation
→ stored result
→ UI display
```
