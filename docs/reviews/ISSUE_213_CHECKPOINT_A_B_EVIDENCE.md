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
  `reports/ch-m1-02/playwright-output/real-stack-CH-M1-02-real-b-fef05-es-without-API-interception-chromium/ch-m1-02-avatar-export.png`.
- Evidence JSON:
  `reports/ch-m1-02/playwright-output/real-stack-CH-M1-02-real-b-fef05-es-without-API-interception-chromium/ch-m1-02-evidence.json`.
- Trace:
  `reports/ch-m1-02/playwright-output/real-stack-CH-M1-02-real-b-fef05-es-without-API-interception-chromium/trace.zip`.
- Lighthouse:
  `reports/lighthouse/stage8-lighthouse.json`.
- Performance smoke:
  `reports/performance/stage8-locust_stats.csv`.
- Container scan:
  `reports/security/container-scan-case.json` plus raw/envelope scanner artifacts.

The latest pre-PR evidence run against the implementation commit recorded:

- Base URL: `http://127.0.0.1:13000`.
- Case count: 1 real-stack Chromium case plus two existing smoke tests.
- Real-stack case duration: 471 ms.
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
- `make test`: pass; 1298 Python tests and 9 frontend component tests.
- `make api-test`: pass; 84 API tests.
- `make ui-test`: pass; 9 frontend component tests.
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
- `make performance-smoke`: pass. Locust health smoke recorded 181 requests,
  0 failures, median 1 ms, average 1.586 ms, max 10.43 ms.
- `make ci`: pass.
- `NARRATWIN_REAL_STACK=1 NARRATWIN_REAL_STACK_BASE_URL=http://127.0.0.1:13000 NARRATWIN_EVIDENCE_COMMIT=$(git rev-parse HEAD) npx --prefix frontend playwright test --config frontend/playwright.real-stack.config.ts`: pass; 3 Chromium tests.

## Reviews

Security and safety review result:

- No Critical, High, or Required finding remains.
- Verified controls cover untrusted upload handling, provider output validation,
  safe artifact exposure, active HTML/script rejection, consent binding, cloned
  identity denial, provider posture, and overclaim prevention for the local/mock
  checkpoint path.

Performance and reliability review result:

- No Critical, High, or Required finding remains.
- Local Compose flow starts from clean state on alternate localhost ports and
  completes the real-stack browser path. The demo uses process-local API state
  for this checkpoint; optional file-backed JSON state is not configured in
  Compose and is not claimed as evidence.

Independent review result:

- No Critical, High, or Required finding remains after the implemented fix loop.
- Residual human-only items are PR review approval, final merge wording,
  post-merge main sync/quality verification, and any controller issue `#155`
  closure wording.

## Human-Only Surfaces

| Surface | Status |
|---|---|
| Latest-head PR approval | Pending human reviewer. |
| Final merge wording | Pending human merge action; use reference-only wording unless closure is explicitly approved. |
| Issue `#155` closure | Do not close until Checkpoint B evidence is accepted and latest-head human approval exists. |
| Production/public release | No-Go; no hosted launch or public distribution is authorized. |

