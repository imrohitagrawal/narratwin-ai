# Quality Gates

NarraTwin AI quality gates are executable stage contracts. A gate that is not implemented must fail loudly when called directly.

## Stable Command

Use one top-level command:

```bash
make quality
```

During the current stage, `make quality` runs only the active stage checks
by delegating to `scripts/quality/check_quality_stage.py`. Stage 8 has started
from merged PR `#32` at commit `7f7196a` and is scoped to performance smoke
tests, API latency budget checks, frontend Lighthouse checks, rate limiting,
request size limits, upload MIME validation, dependency audit, Docker image
scan, release checklist, runbook, demo seed data, portfolio README, and release
readiness evidence. Product behavior outside hardening remains blocked.

## Required Make Targets

The `Makefile` must expose:

| Target | Current behavior |
|---|---|
| `make quality` | Runs checks for `.stage/current`; currently Stage 8 |
| `make stage0-quality` | Runs executable Stage 0 documentation and guardrail checks |
| `make stage1-quality` | Runs executable Stage 1 product and PRD documentation checks |
| `make stage2-quality` | Runs executable Stage 2 architecture, security, AI safety, and portability checks |
| `make stage3-quality` | Runs executable Stage 3 repo foundation and CI/CD checks |
| `make stage4-quality` | Runs executable Stage 4 first-slice checks |
| `make stage5-quality` | Runs executable Stage 5 eval/guardrail/observability checks |
| `make stage6-quality` | Runs executable Stage 6 multilingual/subtitle/voice checks |
| `make stage7-quality` | Runs executable Stage 7 avatar rendering/export checks |
| `make stage8-quality` | Runs executable Stage 8 hardening and release-readiness checks |
| `make final-review-quality` | Runs executable Final Review artifact checks |

## Stage 0 Quality Gate

`make stage0-quality` validates:

- required Stage 0 docs and quality scripts exist
- `docs/STATUS.md` exists and passes the required Stage 0 structural tracker checks for stage ledger content, issue and PR references, open gaps, and next approved actions
- `.github/workflows/quality-gates.yml` exists and invokes `make quality`
- `docs/THIRD_PARTY_NOTICES.md` records governed Stage 0 third-party tools and skill sources
- `.stage/current` contains `0`
- current branch name matches the Stage 0 branch pattern before merge, or is `main` after merge
- files changed from `main` stay within the documented Stage 0 allowlist
- Stage 0 through Stage 8 plus Final Review are documented
- no disallowed product/runtime directories or manifests have started outside the Stage 0 allowlist
- allowlisted Stage 0 Python scripts remain stdlib-only and pass the implemented Stage 0 purity checks in `scripts/quality/check_stage0_docs.py`
- operating docs contain no unresolved placeholders
- `docs/SKILL_LOCK.md` records source URL, pin/version status, license status, purpose, active stage, and activation status
- every third-party GitHub Action referenced by checked-in workflows is represented in `docs/SKILL_LOCK.md`
- `Makefile` contains all required quality targets
- working-tree diffs have no whitespace errors
- obvious committed-secret patterns are absent from tracked text files
- required Stage 0 guardrail inputs and scripts exist and compile

## Future Stage Quality Contracts

### Stage 1: Product Strategy And PRD v1.0

`make stage1-quality` validates:

- required Stage 1 product and PRD artifacts exist
- `.stage/current` contains `1`
- current branch name matches the Stage 1 branch pattern before merge, or is `main`
  after merge
- changed files stay within the documented Stage 1 allowlist
- product strategy and PRD v1.0 preserve both product modes
- PRD captures project knowledge upload, RAG ingestion, grounded script generation,
  evaluation gates, security/privacy guardrails, media provider boundaries, and
  free-first/premium-provider modes
- `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md` is the canonical requirement matrix
- `docs/TRACEABILITY.md` links to the canonical matrix instead of duplicating it
- `docs/STATUS.md` records Stage 1 issue and PR state
- Stage 1 changes introduce no product/runtime code or manifests
- Stage 1 Python quality scripts remain stdlib-only and compile
- any Stage 0 quality script changed by the Stage 1 branch also remains
  stdlib-only and compiles
- working-tree diffs have no whitespace errors
- obvious committed-secret patterns are absent from tracked text files

### Stage 2: Architecture, Security, AI Safety

Stage 2 quality is executable through `scripts/quality/check_stage2_docs.py`.

All stage quality targets also run
`scripts/quality/check_recommended_review_items.py` before the stage-specific
gate. The checker validates [Recommended Review Items](RECOMMENDED_REVIEW_ITEMS.md)
and fails when an item is still open at or after its required stage.

Stage 2 validates:

- `.stage/current` contains `2`
- current branch name matches `stage2-*` before merge, or is `main` after merge
- changed files stay within the documented Stage 2 allowlist
- required Stage 2 architecture, ADR, threat model, security/privacy, AI
  safety/evaluation, portability, API, data model, observability, status, and
  traceability docs exist
- the recommended-review-item register exists and assigns non-blocking review
  items to the correct required stage
- Stage 2 docs include the remediation locks for synthetic local authorization,
  approved-knowledge state, mandatory secret screening before provider egress,
  hard unsupported-claim failure policy, claim-level context references, resource
  budgets, queue/backpressure, provider adapter contracts, event schema, retention,
  tombstones, and API idempotency
- legacy Stage 1 ADRs with duplicate numbers are marked superseded by the Stage 2
  ADR canon
- mock/local provider defaults include LLM, embedding, evaluation, avatar, TTS, STT,
  and storage defaults
- semantic contract checks validate issue `#2`, draft PR `#27`, provider defaults,
  canonical document/approval/ingestion states, idempotency fields, safe
  failed/refused output shapes, retrieval thresholds, cache-key inputs, evidence
  snapshot fields, numeric budgets, and stale-language bans
- the checker scans governance scripts for secrets and does not skip
  `scripts/guardrails_check.py`
- Stage 2 changes introduce no backend, frontend, RAG, provider, avatar, Docker,
  database, dependency manifest, lockfile, or runtime product code
- Stage 2 Python quality scripts remain stdlib-only and compile
- working-tree diffs have no whitespace errors
- obvious committed-secret patterns are absent from tracked text files

### Stage 3: Repo Foundation And CI/CD Quality Gates

Stage 3 quality is executable through `make stage3-quality`, which first runs
`scripts/quality/check_stage3_docs.py` and then executes the repo-local CI
wrappers.

Gate validates:

- `.stage/current` contains `3`
- current branch name matches `stage3-*` before merge, or is `main` after merge
- changed files stay within the documented Stage 3 allowlist
- Stage 3 branch scope is exact-file allowlisted; broad `backend/`,
  `frontend/`, or `tests/` product paths are not accepted
- local development docs include Python and frontend setup commands
- backend FastAPI skeleton exposes health checks only, including versioned
  `/api/v1` health endpoints and baseline security headers
- Python dependency manifests and locks exist for the approved FastAPI foundation
  stack and quality tooling
- the frontend scaffold follows the documented Next.js TypeScript decision and
  does not introduce product feature workflows
- CI wrapper scripts execute backend lint/typecheck, backend unit/API tests,
  frontend lint/typecheck/unit/build, Playwright smoke, Docker build, eval smoke,
  and dependency/security scan path
- tracked GitHub workflows exist for CI, security, eval smoke, and inherited
  quality gates, with third-party actions pinned by immutable SHA
- CI bootstraps `uv` with a pinned version before using `uv.lock`
- dependency/security checks include secret scan, Bandit, `pip-audit`,
  `npm audit --audit-level=high`, Semgrep over source, workflow, Docker,
  Compose, manifest, and env-template files, and local-or-CI Gitleaks coverage
- Docker build paths exist for backend and frontend foundation images; runtime
  containers run as non-root, base/service images are digest pinned, and local
  Compose port bindings are localhost-only
- local Compose includes Postgres and Redis services only as Stage 4 foundation
  readiness; no database schema, migration, queue, or product persistence code is
  implemented in Stage 3
- vector storage defaults to `disabled` until the Stage 4 Chroma/provider
  adapter decision, dependency, persistence path, and tenant-isolation tests are
  locked
- eval smoke loads a deterministic fixture, writes a report artifact, and fails
  on an unsupported health-contract claim mismatch
- the policy-gates workflow runs repository guardrails and the static Stage 3
  contract check; the dedicated CI, security, Docker, frontend smoke, and eval
  workflows own the expensive PR-blocking wrappers
- compatibility status contexts remain for repository rulesets that still require
  `quality / secrets` and `security / docker build`; the authoritative secret
  scan remains the security workflow and the authoritative Docker gate remains
  `ci / docker build`
- pre-commit configuration runs local lint, typecheck, test, frontend, and
  guardrail checks
- Stage 3 docs and third-party notices record newly introduced packages and tools
- Stage 3 changes introduce no product implementation beyond health checks, no
  RAG, provider, avatar, database migrations, or deployment environment logic
- Stage 3 Python quality scripts compile
- working-tree diffs have no whitespace errors

### Stage 4: Project Upload To Grounded Script Generation

Stage 4 quality is executable through `make stage4-quality`, which first runs
`scripts/quality/check_stage4_docs.py` and then executes the repo-local CI
wrappers.

Gate validates:

- `.stage/current` contains `4`
- current branch name matches `stage4-*` before merge, or is `main` after merge
- first-slice files exist for project creation, markdown/txt upload, parsing,
  chunking, mock embeddings, local storage, retrieval, grounded script
  generation, citations, grounding evaluation, UI display, tests, and eval smoke
- direct Stage 4 dependencies are locked and avatar/TTS/video dependencies remain
  absent from Slice 1
- provider interfaces use deterministic mock/local providers for tests and do not
  require paid provider keys
- every accepted generated claim maps to a retrieved source chunk through context
  refs and claim-support records
- unsupported claims fail evaluation and are not exposed as accepted script text
- upload validation rejects unsupported media types and avoids echoing raw upload
  content in public errors
- Stage 4 changed files remain within the documented first-slice allowlist
- retrieval is partitioned by tenant and project
- deterministic RAG eval smoke fixture requires zero unsupported claims and at
  least one citation
- frontend unit and Playwright smoke tests cover the result and citation display
- Docker images build after Stage 4 runtime/API changes
- Stage 4 due recommended review items are resolved, accepted with rationale, or
  superseded

### Stage 5: Evaluations, Guardrails, Observability

Stage 5 quality is executable through `make stage5-quality`, which first runs
`scripts/quality/check_stage5_docs.py` and then executes the repo-local CI
wrappers.

Gate validates:

- `.stage/current` contains `5`
- current branch name matches `stage5-*` before merge, or is `main` after merge
- Stage 5 quality artifacts exist for eval runner, prompt-injection tests,
  unsupported-claim fixtures, and file-upload abuse fixtures
- `backend/app/eval` exposes groundedness, faithfulness, answer-relevancy,
  context precision/recall, and unsupported-claim detectors
- `backend/app/observability` exposes OpenTelemetry trace-id generation,
  Langfuse tracing adapter, structured logs, and token/cost/latency metadata
- eval smoke validates:
  - unsupported claims are zero on the golden run
  - refusal behavior for prompt-injection paths and file-upload abuse paths
  - trace metadata includes latency and cost
  - metrics thresholds:
    - faithfulness >= 0.85
    - answer relevancy >= 0.80
    - context precision >= 0.75
    - context recall >= 0.70
  - unsupported-claim count check remains zero for the happy-path fixture
- `scripts/ci/eval-smoke.sh` writes both JSON (`reports/eval-smoke/stage5-eval-smoke-report.json`) and markdown (`docs/EVAL_REPORT.md`) artifacts
- Stage 5 dependency and security posture remains unchanged: no new provider keys,
  no committed secret findings, and no untracked security-scope drift
- trace-run metadata is returned in `WalkthroughRunResponse.trace` fields
- Stage 5 due recommended review items are resolved, accepted with rationale, or
  superseded

### Stage 6: Multilingual Scripts, Subtitles, Voice Adapter

Stage 6 quality is executable through `make stage6-quality`, which first runs
`scripts/quality/check_stage6_docs.py` and then executes the repo-local CI
wrappers.

Gate validates:

- `.stage/current` contains `6`
- current branch name matches `stage6-*` before merge, or is `main` after merge
- changed files stay within the documented Stage 6 allowlist
- direct Stage 6 dependencies are locked: `babel`, `langcodes`, `pydub`,
  `audioop-lts`, and `srt`
- no paid/avatar provider dependencies are introduced
- backend exposes a provider-adapter based multilingual path with
  `TranslationProvider`, `TTSProvider`, `MockTranslationProvider`, and
  `MockTTSProvider`
- translation preserves configured glossary/project terms
- provider output is validated before display or artifact creation for non-empty
  output, size limits, glossary preservation, and citation-marker preservation
- Stage 6 idempotency uses a locked pending/completed record so duplicate
  in-flight write requests fail with `IDEMPOTENCY_IN_PROGRESS`
- API request fields enforce Stage 6 boundary limits for target language,
  glossary terms, and requested provider IDs
- unsupported language tags fail cleanly with `UNSUPPORTED_LANGUAGE`
- requested unavailable voice providers fall back to mock/local behavior without
  hardcoded paid-provider calls
- mock/local voice behavior emits a JSON manifest only; Stage 6 does not
  synthesize real audio, play audio, clone voices, or call non-local providers
- voice provider artifacts are validated as JSON manifests with safe `.json`
  filenames, `application/json` MIME type, parseable JSON object content, and
  matching checksums before they are returned
- subtitle export emits valid deterministic SubRip timing
- API responses include downloadable translated-script and subtitle artifacts
- frontend exposes target language selection and script/subtitle download links,
  uses glossary-aware multilingual idempotency keys, and only enables artifact
  links after safe artifact MIME, extension, base64, and filename validation
- accessibility notes document downloadable text subtitle behavior and readable
  caption sizing
- Stage 6 docs, traceability, third-party notices, and provider ADR updates are
  present

### Stage 7: Avatar Rendering Adapter And Export

Stage 7 quality is executable through `make stage7-quality`, which first runs
`scripts/quality/check_stage7_docs.py` and then executes the repo-local CI
wrappers.

Gate validates:

- `.stage/current` contains `7`
- current branch name matches `stage7-*` before merge, or is `main` after merge
- changed files stay within the documented Stage 7 allowlist
- backend exposes `AvatarProvider`, `MockAvatarProvider`, and a local HTML
  `VideoRenderer` export path through `backend/app/stage7.py`
- backend exposes a validated provider config model, disabled external adapter
  stub, render job status lifecycle, and video export placeholder artifact
- `POST /api/v1/projects/{projectId}/walkthrough-runs/{runId}/avatar-renders`
  requires a completed, passed grounded source run before rendering
- avatar rendering uses mock/local defaults and does not call paid avatar
  providers in local/dev/test
- requested unavailable avatar providers fall back to the mock/local provider and
  record `REQUESTED_PROVIDER_UNAVAILABLE`
- provider failure fallback records only enum fallback reasons and successful
  provider metadata must match local provider config
- cloned identity requests fail with `CLONED_IDENTITY_DISABLED`
- synthetic avatar demo export requires explicit consent and fails with
  `AVATAR_CONSENT_REQUIRED` when missing
- export artifacts are validated for expected MIME type, extension, size,
  checksum, base64 decoding, JSON manifest shape, active HTML content, and safe
  filename before API response or frontend download
- provider-produced config, manifest, and video placeholder output are validated
  from the first Stage 7 implementation, applying the Stage 6 learning that
  every provider output surface must be checked before storage or display
- HTML demo exports must reject active HTML content and must exactly match
  trusted renderer output for the source run, trace, and disclosure text
- render manifests and video placeholders must be semantically bound to trusted
  provider config, source run, trace, citation/evaluation IDs and checksums,
  disclosure inputs, and public-use license checks, and must reject unexpected
  top-level or nested JSON fields
- failed idempotent render attempts are retained as terminal failed records and
  replay the same error without another provider call
- Stage 7 semantic validation failures with an idempotency key, including
  missing consent and cloned identity requests, are retained and replayed or
  conflict on changed retry bodies
- malformed provider output shapes must fail with `PROVIDER_OUTPUT_INVALID`, not
  uncontrolled server errors
- generated demo exports carry AI-generated avatar/video disclosure metadata
- provider contracts preserve trace/run metadata, source citations, and
  evaluation status from the grounded script path
- frontend exposes the avatar export workflow, disclosure metadata, consent
  control, demo preview, export artifacts page section, and download links for
  script, subtitles, avatar demo HTML, render manifest, and video placeholder
  artifacts only after artifact safety checks
- UI work follows the activated UI/UX Pro Max guidance without committing
  `.codex` generated skill files
- Stage 7 docs, traceability, third-party notices, skill lock, and provider ADR
  updates are present

### Stage 8: Performance, Security Hardening, Release Readiness

Stage 8 quality is executable through `make stage8-quality`, which first runs
`scripts/quality/check_stage8_docs.py` and then executes the repo-local CI
wrappers.

Gate validates:

- `.stage/current` contains `8`
- current branch name matches `stage8-*` before merge, or is `main` after merge
- changed files stay within the documented Stage 8 allowlist
- health endpoint < 200 ms local
- script generation mocked path < 2 sec
- upload limit enforced through fail-closed `Content-Length` checks, actual
  ASGI body-byte counting, and upload content-size limits
- upload MIME validation rejects octet-stream compatibility for markdown/text
- write rate limiting returns `RATE_LIMIT_EXCEEDED`, uses the client IP as the
  local actor key, and bounds retained rate-limit keys
- `locust` is locked as dev-only performance tooling
- performance smoke runs a headless Locust profile and enforces the health
  endpoint p95 latency budget
- frontend Lighthouse checks are locked and enforce both category and named audit
  budgets
- PR CI emits `stage8 / performance lighthouse` and runs
  `scripts/ci/performance-smoke.sh` plus `scripts/ci/frontend-lighthouse.sh`
  when `.stage/current` is `8`
- dependency audit blocks critical/high findings
- Docker image scan blocks critical/high container vulnerabilities through
  Trivy, Grype, pinned Dockerized Trivy, or Docker Scout, including the PR
  security workflow scan
- frontend production image strips npm/npx from the runner layer before
  scanning so package-manager-only vulnerabilities are not shipped
- release checklist, runbook, demo seed data, portfolio README, and
  `docs/RELEASE_READINESS_REVIEW.md` exist
- RR-029 through RR-035 have explicit Stage 8 dispositions, especially
  multi-worker durability blocks, real video export/license posture, persistent
  synthetic-media consent/provenance, and source-run based avatar rendering
- no paid provider or production credential dependency is introduced

### Final Review: Independent Review

Final Review quality is executable through `make final-review-quality`.
On `final-review-*` branches, the top-level `make quality` dispatcher runs the
Final Review artifact gate even though `.stage/current` remains `8` until Phase 1
closure decides whether to advance the stage marker.

Gate validates:

- current branch name matches `final-review-*` before merge, or is `main` after
  merge
- required review artifacts exist under `docs/reviews/`
- required PRD, RTM, quality, AI safety, security/privacy, and release-readiness
  inputs exist
- changed files stay within the Final Review artifact/gate allowlist
- review artifacts link issue `#6`, Stage 8 merge `fb40113`, and findings/issues
  `#35` through `#44`
- `GO_NO_GO.md` keeps production release No-Go and limits any conditional demo
  claim to local mock-provider review
- defect IDs in `DEFECT_BACKLOG.md` are unique
- no backend, frontend, provider, RAG, avatar, runtime, Docker, database, or
  product feature implementation is introduced by the Final Review artifact PR

## CI Relationship

GitHub Actions workflows remain the remote enforcement layer. Local stage targets are the developer and agent contract before pushing.

The CI layer must continue to enforce:

- `make quality` for the current stage; Stage 8 PR CI also runs the dedicated
  `stage8 / performance lighthouse` budget job because policy-only quality gates
  validate static stage contracts rather than long-running browser/load checks
- stage-aware backend contracts so Stage 0 governance scripts do not trigger backend implementation gates
- issue-linked PRs
- least-privilege workflow permissions
- no committed secrets
- mock/local provider defaults
- eval failures block merge when eval reports exist
- critical or high security findings block merge when security reports exist

Direct pushes to `main` remain a repository-settings requirement enforced through branch protection or rulesets rather than the stage-quality workflow itself.
