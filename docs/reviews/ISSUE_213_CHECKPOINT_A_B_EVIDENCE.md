# Issue #213 Checkpoint A To Checkpoint B Evidence

Parent controller: issue `#155`.

Issue `#213` is the authorized combined Product Mode 1 local/mock checkpoint
child for Checkpoint A, `CH-M1-03`, `CH-M1-04`, `CH-M1-05`, `CH-M1-06`, and
Checkpoint B. Product Mode 2, real audio/video, STT/imported video, external
providers, hosted/public launch, public distribution, production readiness, and
mutation of stopped evidence surfaces `#162`, `#163`, `#166`, `#167`, and
`#168` remain out of scope.

This file is the durable review memo. The final PR body records the exact-head
runtime command after the last commit, because a committed file cannot name the
commit that contains itself without becoming stale.

## Phase Plans

| Phase | Objective | Acceptance criteria | Non-goals | Evidence |
|---|---|---|---|---|
| 0 | Establish Checkpoint A baseline from `origin/main`. | Clean branch/worktree, issue state confirmed, guardrails and Phase 1 quality pass, clean Compose stack reaches health/ready, real browser flow runs without API interception. | Product code changes and stopped evidence mutation. | Baseline worktree at `67d2c196752f96a05dc580d00b4b4aa0b4174c0e`; commands listed below. |
| 1 | Define Stage 6 to Stage 7 multilingual media-bundle contract. | Contract requires source run, multilingual run, target language, checksums, context/citation/evaluation evidence, provider posture, and consent disclosure version. | Product Mode 2 or real timed media. | `docs/API_CONTRACT.md`, ADR 0030, traceability, backend API tests. |
| 2 | Bind backend Stage 7 render to a validated multilingual bundle. | Stage 7 rejects missing, mismatched, stale, replayed, or tampered Stage 6 evidence and renders from the translated Stage 6 script for the checkpoint path. | English overclaiming and provider enablement. | `tests/api/test_stage7_avatar_api.py`; `tests/unit/test_local_durability.py`. |
| 3 | Expose and validate UI artifacts. | Browser can see/download translated script, subtitles, voice manifest, avatar demo HTML, render manifest, and video placeholder with MIME, filename, size, checksum, schema/provider marker, active HTML, language, and provenance checks. | API route interception as success evidence. | `frontend/src/app/page.tsx`; Vitest; real-stack Playwright evidence. |
| 4 | Update deterministic demo docs. | Demo checklist, script, and screenshot guide state mock/local-only posture and all explicit non-goals. | README/portfolio claim expansion or public launch. | `docs/demo/*`; Phase 1 closure docs gate. |
| 5 | Capture Checkpoint B final local evidence. | Clean Compose stack, health/ready, browser -> frontend -> backend flow, artifact checksums, provider posture, logs, screenshot, trace, and quality/security/performance gates are recorded. | Closing `#155` without latest-head human approval. | PR body exact-head evidence plus local ignored reports. |

## Checkpoint A Evidence

Checkpoint A was executed in a temporary worktree checked out as local `main`
at `67d2c196752f96a05dc580d00b4b4aa0b4174c0e`, matching `origin/main`.

Commands executed:

- `python3 scripts/guardrails_check.py`: passed.
- `make quality`: passed.
- `make phase1-closure-quality`: passed.
- `docker compose -f docker-compose.yml -f /tmp/narratwin-issue213-ports.override.yml up --build -d`: stack started from clean state.
- `curl -fsS http://127.0.0.1:18000/api/v1/healthz`: passed.
- `curl -fsS http://127.0.0.1:18000/api/v1/readyz`: passed.
- `NARRATWIN_REAL_STACK=1 NARRATWIN_REAL_STACK_BASE_URL=http://127.0.0.1:13000 NARRATWIN_EVIDENCE_COMMIT=67d2c196752f96a05dc580d00b4b4aa0b4174c0e npx playwright test --config=playwright.real-stack.config.ts`: 3 passed.

Checkpoint A browser evidence summary:

- Case count: 1 real-stack Chromium case plus existing bounded smoke coverage.
- Duration: 408 ms for the real-stack case.
- API call count: 8.
- API sequence: project creation, knowledge upload, approval, ingestion,
  grounded walkthrough run, multilingual run, avatar consent, avatar render.
- Browser interception: `noApiInterception=true`.
- Request origin: `http://127.0.0.1:13000`.
- Providers: LLM, embedding, evaluation, translation, avatar, TTS, STT, and
  subtitles were `mock`; video renderer was `local`.

Checkpoint A limitation: local host port `5432` was occupied by an unrelated
container, so the evidence used a temporary host-port override mapping frontend
to `13000`, backend to `18000`, Postgres to `15432`, and Redis to `16379`.
Compose service networking and provider posture were otherwise unchanged.

## Checkpoint B Evidence Packet

The local evidence packet is generated under ignored `reports/` paths:

- Screenshot:
  `reports/issue-213-checkpoint-b/playwright-output/<case>/issue-213-checkpoint-b-avatar-export.png`.
- Evidence JSON:
  `reports/issue-213-checkpoint-b/playwright-output/<case>/issue-213-checkpoint-b-evidence.json`.
- Trace:
  `reports/issue-213-checkpoint-b/playwright-output/<case>/trace.zip`.
- Lighthouse:
  `reports/lighthouse/stage8-lighthouse.json`.
- Performance smoke:
  `reports/performance/stage8-locust_stats.csv`.
- Container scan:
  `reports/security/container-scan-case.json` plus raw/envelope scanner artifacts.

The latest pre-PR evidence run against the implementation commit recorded:

- Base URL: `http://127.0.0.1:13000`.
- Case count: 1 no-interception real-stack Chromium case plus 3 mocked smoke
  cases kept separate under `frontend/playwright.config.ts`.
- Real-stack case duration: 408 ms.
- API call count: 8.
- Browser interception: `noApiInterception=true`.
- Request origin: `http://127.0.0.1:13000`.
- API sequence from backend logs: `POST /projects`, `POST /knowledge-documents`,
  `PATCH /approval`, `POST /ingestion-runs`, `POST /walkthrough-runs`,
  `POST /multilingual-runs`, `POST /avatar-consents`,
  `POST /avatar-renders`.
- Provider posture: LLM, embedding, evaluation, translation, avatar, TTS, STT,
  and subtitles were `mock`; video renderer was `local`.
- Compose services: frontend, backend, Postgres, and Redis were running on
  localhost-only alternate host ports; backend, Postgres, and Redis were
  healthy.

Artifact metadata recorded by the browser:

| Artifact | Filename | MIME | Bytes | SHA-256 |
|---|---|---:|---:|---|
| Translated script | `run_000001-es-script.md` | `text/markdown` | 149 | `sha256:1cd1eb803bec9ca71131c59e3bc165a8a738310ee84bff947f9ceb74d4479170` |
| Subtitles | `run_000001-es.srt` | `application/x-subrip` | 249 | `sha256:113fef542beec7c5beb3d2c7074c554cb5253c4cd38e14f480e926e4174b11e2` |
| Voice manifest | `voice-manifest-es.json` | `application/json` | 404 | `sha256:e3925d1a2b8226657a0ff24b8e5cfba5e1ab211515ea3b12c780b4d78c249773` |
| Avatar demo | `run_000001-avatar-demo.html` | `text/html` | 650 | `sha256:0e1708f22bc2181e6294cfd2f7d34836c6423fe463ffc9ad5348b1bffe0198d1` |
| Render manifest | `run_000001-avatar-render-manifest.json` | `application/json` | 2237 | `sha256:22facda62eaa1ad15a842838f0678ef106fc277da2f94bf96e47dc411886ce43` |
| Video placeholder | `run_000001-video-export-placeholder.json` | `application/json` | 2157 | `sha256:e8109fb2fc6f80d66e021a70cfa0f70ebd6494ec63f9fc8fb87266332b1c4a9e` |

## Validation

Executed validation:

- `python3 scripts/guardrails_check.py`: pass.
- `make quality`: pass.
- `make phase1-closure-quality`: pass.
- `make lint`: pass.
- `make typecheck`: pass.
- `make test`: pass; 1298 Python tests and 12 frontend component tests.
- `make api-test`: pass; 86 API tests.
- `make ui-test`: pass; 12 frontend component tests.
- `make security`: pass. Semgrep repository scan found 0 findings, the canary
  found the expected single finding, Bandit found 0 issues, and gitleaks found
  no leaks. `npm audit` reported 17 moderate Lighthouse/OpenTelemetry-chain
  advisories, below the configured high-severity blocking threshold.
- `make dependency-audit`: pass with the same moderate npm advisory disclosure.
- `make container-scan`: pass by consensus policy; raw scanner findings were
  evaluated, no consensus findings remained, and the CPython `3.13.14` VEX
  status remained fixed for CVE-2026-11940, CVE-2026-11972, and
  CVE-2026-15308.
- `make frontend-lighthouse`: pass. Lighthouse scores: performance 1.00,
  accessibility 1.00, best-practices 0.96, SEO 1.00.
- `make performance-smoke`: pass. Locust health smoke recorded 190 requests,
  0 failures, median 2 ms, average 2 ms, max 16 ms.
- `make ci`: pass.
- `npm --prefix frontend run build && npx --prefix frontend playwright test --config frontend/playwright.config.ts frontend/tests/smoke.spec.ts --project=chromium`: pass; 3 mocked Chromium smoke tests.
- `NARRATWIN_REAL_STACK=1 NARRATWIN_REAL_STACK_BASE_URL=http://127.0.0.1:13000 NARRATWIN_EVIDENCE_COMMIT=$(git rev-parse HEAD) npx --prefix frontend playwright test --config frontend/playwright.real-stack.config.ts`: pass; 1 no-interception Chromium test.

## Review Disposition

| Review angle | Severity | Finding evidence | Fix | Rerun evidence |
|---|---|---|---|---|
| Backend/API | Required | `tests/api/test_stage7_avatar_api.py` lacked direct unknown and cross-project replay coverage for `multilingualRunId`. | Added unknown multilingual-run and cross-project replay rejection tests with distinct idempotency key prefixes. | `uv run pytest tests/api/test_stage7_avatar_api.py tests/unit/test_local_durability.py -q`: pass, 111 tests. |
| Frontend/UI | Required | `frontend/src/app/page.tsx` allowed Stage 7 JSON artifacts without full language/provenance context; later review found `voiceManifest` accepted a minimal provider/language JSON object. | Added artifact validation context, render/video multilingual provenance checks, exact Stage 6 voice-manifest key validation, local provider/disclosure checks, and translated-script checksum binding. Added Vitest and Playwright negative cases. | `npm --prefix frontend test`: pass, 12 tests; `npm --prefix frontend run typecheck`: pass; `npm --prefix frontend run lint`: pass; mocked Playwright smoke: pass, 3 tests. |
| Frontend/UI | Required | `frontend/playwright.real-stack.config.ts` could discover route-intercepted smoke tests, making the no-interception evidence command ambiguous. | Scoped the real-stack config to `real-stack.spec.ts` and moved output to `reports/issue-213-checkpoint-b/playwright-output`. | Final no-interception real-stack rerun is recorded in the PR body at the pushed head. |
| Security/Safety | Required | Evidence and PR claims became stale after review fixes changed the working tree. | This memo and the PR body are refreshed after the final fix commit and final-head reruns; moderate Lighthouse/OpenTelemetry audit advisories remain disclosed below the configured blocking threshold. | Final guardrails, quality, security, dependency audit, and real-stack evidence are recorded in the PR body. |
| Performance/Reliability | Required | Checkpoint B paths reused the older `reports/ch-m1-02` namespace and stale counts/durations. | Renamed the no-interception test and output namespace to issue `#213` Checkpoint B, updated counts, and reran the performance smoke. | `make performance-smoke`: pass, 190 requests, 0 failures, median 2 ms, max 16 ms. |
| Governance/Docs | Required | `docs/STATUS.md` and PR ledger omitted current `#213`/`#214` mapping, and the StatusStateV1 forbidden row conflicted with the authorized local/mock issue `#213` path. | Updated status/PR ledgers and the executable StatusStateV1 checker while preserving forbidden Product Mode 2, real media, provider, hosted/public, production, and stopped-evidence boundaries. | `python3 scripts/guardrails_check.py`: pass; `make phase1-closure-quality`: pass; `make quality`: pass. |
| Governance/Docs | Required | Controller issue `#155` needed a reference-only ledger comment for `#213`/`#214`. | Post a reference-only comment to `#155` after final push; `#155` remains open pending human approval and accepted Checkpoint B evidence. | Live GitHub issue comment timestamp is recorded in the PR body. |

No Critical or High findings remain in the sub-agent review loop. Required
findings above were routed back through implementation and verification before
the PR was refreshed.

Residual human-only items are PR review approval, final merge wording, post-merge
main sync/quality verification, and any controller issue `#155` closure wording.

## Human-Only Surfaces

| Surface | Status |
|---|---|
| Latest-head PR approval | Pending human reviewer. |
| Final merge wording | Pending human merge action; use reference-only wording unless closure is explicitly approved. |
| Issue `#155` closure | Do not close until Checkpoint B evidence is accepted and latest-head human approval exists. |
| Production/public release | No-Go; no hosted launch or public distribution is authorized. |
