# Quality Gates

NarraTwin AI quality gates are executable stage contracts. A gate that is not implemented must fail loudly when called directly.

## Stable Command

Use one top-level command:

```bash
make quality
```

During the current stage, `make quality` runs only the active stage checks
by delegating to `scripts/quality/check_quality_stage.py`. The repository stage
marker remains `.stage/current = 8`, so ordinary Stage 8 branches and `main`
dispatch to the Stage 8 gate. Final Review and Phase 1 Closure branches override
that marker by branch prefix and dispatch to their dedicated governance gates.
Product behavior outside approved Phase 1 closure remediation remains blocked.

## Required Make Targets

The `Makefile` must expose:

| Target | Current behavior |
|---|---|
| `make quality` | Runs checks for `.stage/current`, with Final Review and Phase 1 Closure branch-prefix overrides |
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
| `make phase1-closure-quality` | Runs executable Phase 1 Closure governance checks |
| `make lint` | Runs backend Ruff and frontend ESLint |
| `make typecheck` | Runs backend mypy and frontend TypeScript checks |
| `make test` | Runs backend unit tests and frontend unit tests |
| `make api-test` | Runs backend API tests |
| `make ui-test` | Runs frontend unit tests |
| `make e2e` | Runs frontend Playwright smoke |
| `make eval` | Runs eval smoke |
| `make security` | Runs dependency/security wrapper |
| `make ci` | Runs the local CI wrapper set |

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
  every provider output surface must be checked before storage or display;
  provider JSON artifacts must reject duplicate object keys at any nesting level
- HTML demo exports must reject active HTML content and must exactly match
  trusted renderer output for the source run, trace, and disclosure text
- render manifests and video placeholders must be semantically bound to trusted
  provider config, source run, trace, citation/evaluation IDs and checksums,
  disclosure inputs, and public-use license checks, and must reject unexpected
  top-level or nested JSON fields
- source evaluation checksums must use the shared Stage 7
  `build_source_evaluation_checksum` helper over normalized evaluation ID,
  source run ID, trace ID, normalized evaluation status, normalized context ref
  IDs, and normalized citation indexes so route, service, manifest, and
  placeholder evidence binding cannot drift; any caller-supplied checksum must
  match the helper result at the service and mock-provider boundary, and checksum
  string components must reject delimiter/control characters that would make
  comma/newline serialization ambiguous
- positive source context or citation counts must include explicit source
  context ref IDs and citation indexes; Stage 7 must not synthesize placeholder
  evidence identifiers for direct service or mock-provider calls
- failed idempotent render attempts are retained as terminal failed records and
  replay the same error without another provider call
- Stage 7 idempotency request checksums use structured request preimages so
  delimiter characters in user/provider strings cannot collide across fields
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

### Phase 1 Closure

Phase 1 Closure quality is executable through `make phase1-closure-quality`.
On `phase-1-closure-*` branches, the top-level `make quality` dispatcher runs
the Phase 1 Closure gate even though `.stage/current` remains `8`.

Gate validates:

- current branch name matches `phase-1-closure-*` before merge, or is `main`
  after merge; unresolved branch context fails closed
- Final Review baseline artifacts exist and `docs/reviews/GO_NO_GO.md`
  preserves the five No-Go decision lines
- changed files stay within the Phase 1 closure allowlist. Module A branches are
  limited to governance/reporting files, `AGENTS.md`, and CODEOWNERS coverage
  for process-critical guardrails; issue `#38` may also update the
  required `policy-gates` workflow and branch-protection verifier that make its
  evidence reproducible; Module F issue `#37` may also change
  the local-principal implementation, API tests, and active architecture/security
  contract docs needed to reconcile the trusted local principal behavior. Module
  B issue `#42` may change only the Stage 7 checksum-binding implementation,
  Stage 7 unit/API tests, and active checksum contract/governance docs. Issue
  `#39` may also change the Stage 4/6/7 local durability implementation,
  storage helper, ops status endpoint, local durability/API tests, and active
  durability/monitoring docs needed to preserve the production No-Go while
  proving local restart recovery. Process-only follow-ups must use
  `phase-1-closure-process-<issue>-<phf-id>-<slug>` and may change governance
  docs, `scripts/guardrails_check.py`, and guardrail/closure-gate unit tests,
  but not backend, frontend, provider, RAG, avatar, database, Docker, or product
  runtime files. Final Review baseline artifacts are required inputs but not
  allowed closure-branch edits
- `docs/reviews/PHASE_1_CLOSURE_REPORT.md` parses as an issue table covering
  issues `#35` through `#44` with expected P0/P1/P2/P3 priorities
- `docs/reviews/PROCESS_HARDENING_FINDINGS.md` tracks deduplicated
  process-hardening review findings from sub-agent, cross-model, and blind
  reviews when those reviews produce actionable process gaps
- every P0/P1 issue maps to a valid closure module and the module table covers
  the P0/P1 issue set with non-empty required evidence
- `docs/RELEASE_READINESS_REVIEW.md` preserves the Final Review No-Go posture,
  tagging block, and downgrade evidence rule
- `docs/evals/phase1_golden_questions.jsonl` is valid JSONL with the required
  minimum questions, expected answers, evidence paths, required/forbidden
  claims, citation policy, metric floors, unsupported-claim threshold of zero,
  and at least one prompt-injection and one safety-boundary fixture
- Phase 1 demo docs and portfolio docs include runnable local startup,
  health/readiness, project/upload/generation/citation/eval/saved-output flow,
  and single-process, local-only, optional JSON restart snapshot,
  no-production-durability, mock/local-only disclosures
- process-loop governance artifacts preserve a reference-only PR template,
  preflight evidence table, PR `#54` finding evidence table, NarraTwin-specific
  RCA gates, and reusable new-project bootstrap/source-control/source-facts/
  failure-matrix/RCA-pause controls
- `policy-gates` reruns on `pull_request.edited`, so a PR title/body edit after
  green checks cannot bypass the issue-linking and `#39` auto-close guard

The Phase 1 Closure quality gate validates the static governance contract. It
does not replace `make ci` and does not execute the Phase 1 golden questions
through the RAG pipeline until a later eval-runner PR wires that dataset into
`make eval`. Live branch-protection drift is verified remotely by the required
`policy-gates` workflow step `scripts/ci/verify_branch_protection.py`, which
queries GitHub's branch summary API for `main` and fails if `protected: true`,
exact required contexts, `enforcement_level: everyone`, or GitHub Actions app
bindings drift. When the workflow token can read GitHub's protected-branch
detail endpoint, the verifier also checks strict up-to-date status checks,
required PR review, administrator enforcement, blocked force pushes, blocked
deletions, and required conversation resolution. When GitHub returns a
permission boundary for that detail endpoint, missing detail-only fields such as
`strict` remain an explicit human-only review surface while visible branch
summary fields continue to fail closed.

The repository guardrail also checks PR body content on pull-request events:
generic PRs must use reference-only issue linkage such as `Refs #<issue>` and
must not include issue-closing keywords in the title/body/branch commit
messages except for explicitly allowed canonical stage issue closures. Issue
`#39` must not appear with auto-closing keywords in the title/body/branch commit
messages, and non-trivial PRs must include completed preflight evidence rows for
the required intent/spec, source-facts, failure-matrix, test, docs/gates, and
adversarial-review categories. The guardrail rejects false-pass preflight
tables when the failure-matrix IDs are not fully covered by test, gate, source,
human-only, or non-goal evidence; when completion status is not `pass` or
`passed`; when artifacts are directories, placeholder URLs, or missing files; or
when the tests row lacks old-behavior proof language such as RED, mutation,
break-test, regression-reproduced, or fails-before evidence. Durability,
restore/replay, derived-artifact, release, CI, and governance-process PRs must
provide the invariant-to-test mapping before implementation; human-only
surfaces, including the final squash/merge message, must be listed separately
with owner and residual-risk decision, and pre-implementation evidence must show
the matrix/source facts existed before implementation or guardrail edits began
through a specific issue-comment URL, PR URL, or verified commit ordering.
Process-critical governance docs and process-review registers stay in the
non-trivial category even for text-only edits because those files define future
automation behavior and review-loop prevention.
Local validation that claims to cover PR-body checks must run with a pull-request
event payload and `NARRATWIN_FORCE_PULL_REQUEST_GUARDRAILS=1`; plain
`python3 scripts/guardrails_check.py` covers repository files but not PR title,
body, or branch commit-message semantics outside a pull-request event.

Changes to `scripts/quality/check_phase1_closure_docs.py`,
`scripts/quality/check_quality_stage.py`, or
`scripts/quality/check_recommended_review_items.py` require explicit reviewer
attention because in-repo gate scripts are executed from the PR branch under
review.

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
