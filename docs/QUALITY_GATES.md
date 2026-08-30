# Quality Gates

## Issue #16 specification-kit gate

Invariant `I16.QUALITY.DOC` binds exact branch `stage1-16-spec-kit-gate` to the
repository-native, Spec Kit-compatible checker while preserving
`.stage/current = 8`, normal Stage 8/main routing, and legacy Stage 1 semantics.
The external GitHub Spec Kit CLI is not installed or activated by this route.

`make issue16-spec-quality` runs the stdlib-only checker plus focused document
and dispatcher mutation tests. Exact-branch `make quality`, including policy-
only mode, dispatches the checker before Stage 8; near-match branches receive no
Issue #16 authority. The gate proves specification completeness only and grants
no product, provider, media, credential, egress, spending, deployment,
publication, release, public-availability, or production-readiness authority.

NarraTwin AI quality gates are executable stage contracts. A gate that is not implemented must fail loudly when called directly.

## Stable Command

Use one top-level command:

```bash
make quality
```

During the current stage, `make quality` runs only the active stage checks
by delegating to `scripts/quality/check_quality_stage.py`. The repository stage
marker remains `.stage/current = 8`. Ordinary Stage 8 branches dispatch to the
Stage 8 gate. Final Review and Phase 1 Closure branches override that marker by
branch prefix and dispatch to their dedicated governance gates.
When `docs/STATUS.md` StatusStateV1 records `SSV1-MODE` as `phase1-closure`, plain local `make quality` on `main` dispatches the Phase 1 Closure gate.
Product behavior remains blocked except for an exact owner-authorized Stage 8
Cut 1 route described below.

### Issue #451 post-PR-443 reconciliation route

Exact branch `docs/cut1-post-443-reconciliation-451` starts from
`59db96aaab6c4e75b12d134dc9b02330c5a982ac` and must change exactly these eight
text paths:

- `docs/PHASE_PLAN.md`
- `docs/STATUS.md`
- `scripts/quality/stage8_cut1_routes.py`
- `tests/unit/test_adversarial_convergence.py`
- `tests/unit/test_guardrails_check.py`
- `tests/unit/test_stage8_cut1_routes.py`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`

The aggregate additions-plus-deletions limit is 600. Per-path limits are 120,
180, 100, 20, 20, 120, 80, and 80 respectively in the order above. Missing or outside
paths, branch lookalikes, base drift, and aggregate or per-path budget excess
fail closed. Both plain `make quality` and
`NARRATWIN_POLICY_ONLY=1 make quality` must pass. The route is governance-only;
it adds no product, provider, media, deployment, publication, release, or
production authority.

### Historical Issue #435 finite adversarial-convergence route

Issue `#435` completed through merged PR `#453`. The route contract below is
retained as historical evidence; its merged framework remains nonactivating.

Exact branch `governance-435-adversarial-convergence-framework-v1` runs typed
repository-route inspection before the immutable pytest acceptance file; it does not inherit
the legacy Stage 8 branch-name router. Prefix and suffix lookalikes receive no
authority. All unrelated Stage 8, Final Review, Phase 1 Closure, and
policy-only behavior is unchanged.

The route is governance-only with activation `NONE`, authority effect
`NO_AUTHORITY_EFFECT`, and release No-Go. It starts at exact base
`a6284f7d8f1a14ef4c9a99493d6b06046505f20c`, preserves exact C1
`205c02b3bac633d023d753356bc966c194ed36a7` and preflight blob
`c554eaf7f73ea081434b1e2f818441fe0bc3eee9`, and enforces the OWNER-amended
20-path map. C2 must cumulatively contain the 19 non-freeze paths; C3 adds only
the freeze; C4 changes only the marked executor region while the dispatcher,
acceptance test, and all other production bytes remain frozen.

Charged lines are additions plus deletions with no deletion credit. Per-path
caps and the 3,500 non-freeze / 3,620 final aggregates are hard. Binary,
rename/copy, symlink, nonregular, missing, extra, untracked, dirty, wrong-mode,
malformed-numstat, history, base/head, or blob drift fails closed. At 85 percent
record readability review; at 90 percent stop.

The frozen C2 corpus is `ACP-FRAMEWORK-CASES-V1-N40`, exactly 40 stimulus-only
cases with semantic SHA-256
`3b2a0c4b3b13cf6ab71ec4e7a3dd4e3566a0c8195e3c7bed6bf956575e5f9fc6`.
Expected results live only in `tests/unit/test_adversarial_convergence.py`.
Twelve separately named test-only mutants must each execute once and be killed.

C2/C3 are intentionally RED. Required evidence is:

- all bootstrap, corpus/schema, safe-loader, import, mutation-harness,
  dispatcher, guardrail, security, route, and readability tests GREEN;
- exactly 40 future-executor failures and zero errors, each reaching typed
  `ACP.NOT_IMPLEMENTED`;
- `make quality` immutable-runner output with exactly 40 typed
  `ACP.NOT_IMPLEMENTED` failures and zero errors; each worker call exits 3;
- candidate review state `PENDING_EXTERNAL_REVIEW` until four independent
  exact-head/tree reviews pass.

Worker exit 1 is `CONTRACT_FAILURE`; exit 2 is `INFRASTRUCTURE_FAILURE`; exit 3
is intentional unimplemented RED. `make` may map a failed recipe generically,
so the immutable pytest inventory and worker results are the discriminating
evidence. A different RED,
a new threat/path/cap/invariant/corpus, an unapproved correction, post-C3 finding, or
review disagreement stops for OWNER disposition. The framework provides no
product, provider, workflow, dependency, deployment, publication, or release
authority.

### Cut 1 Stage 8 Transition

Exact branches `cut1-process-346-governance-transition`,
`cut1-335-r0c-a2-1-stage4-rag-v1-lineage`, and
`cut1-349-r0c-a2-2-machine-contract-parity` use normal Stage 8/full CI. Exact
branch `cut1-358-quiet-presence-ui` adds the amended 16-path `/demo` local/mock
Quiet Presence route, focused unit/client/browser evidence including an
explicitly enabled local-backend browser proof without request interception,
and no root/backend/API,
provider, dependency, workflow, Docker, deployment, or production claim.
The shared Stage 2 retrieval-v1 parity oracle runs on every Stage 8 invocation.
`SSV1-MODE` and `phase-1-closure-*` remain compatibility routing only;
they cannot route new Cut 1 product work. Scope output is supporting evidence,
not authorization. A non-main push ignores the previous-push `before` SHA and
collects the complete branch from `merge-base(origin/main, exact-head)`; PR and
review events keep their explicit base. The checker binds its checkout to the
GitHub event's PR head or push `after` SHA when the workflow does not forward a
custom head variable, and contradictory, malformed, missing, or stale head
evidence fails closed. Exact merge-base review includes rename/copy sources and
destinations. Existing trusted CI, non-author approval, and confirmed merge
wording remain mandatory. Local scope output without live GitHub evidence is
supporting evidence only. Agent-context remains `SHADOW_ONLY`.

Exact branch `cut1-366-real-media-governance-transition` is the Issue `#366`
governance-only transition. F366-1 through F366-12 require all and only the
seven checked paths, the completed #372 prerequisite, narration child #382
between #367 and #368, StackClimb/Rohit Agrawal authority, latest evaluated
script approval and edit invalidation, measured 90–120-second audio rejection
without silent time-stretch, visible-not-spoken citations, future-only Q&A,
and every still/HTML/JSON/manifest/metadata/silent/placeholder false-media
prohibition. The route is limited to 900 charged lines, including at most 350
in the Stage 8 checker and 300 in its focused test. Missing paths, extra paths,
near-match branches, stale #372 blocker text, required-marker mutations, or
prohibited overclaims fail closed. It adds no product code, assets,
dependencies, providers, media binaries, Docker/workflow changes, cloning,
deployment, release, public availability, trademark-registration, or
production-readiness claim. Later child work requires its own exact issue,
branch, preflight, RED/GREEN evidence, PR approval, merge, and merged-main
acceptance.

Issue `#386` keeps the monolithic Stage 8 checker below its unchanged 500-line
legacy caps by moving new Cut 1 route mechanics to
`scripts/quality/stage8_cut1_routes.py`. Its exact nine-path #386 route absorbs
the stale Issue #280 unsupported-language oracle without changing German support
or runtime/catalog behavior and isolates only the generic route-enumeration test
under a 20-line charge cap. The dedicated Issue #366 tests retain the genuine
unrestricted fixed-base index/worktree snapshot. The sidecar pre-registers routes for
Issues `#385`, `#384`, and `#383`; it requires complete path sets, current-main
ancestry (fixed base for #386), additions-plus-deletions budgets over the larger
index/worktree snapshot, fail-closed malformed/binary/untracked text evidence,
and regular bounded #383 portrait files. Lookalikes inherit no authority. This
is governance enforcement, not product, asset, provider, or media approval.

Issue `#384` resumes through an owner-reset exact eight-path modular route. It
charges additions plus deletions over the larger current-main index/worktree
snapshot and caps the aggregate at 500: five governance/preflight paths at 160,
the checker at 10 solely for the exact bound digest, and the sidecar plus its
test at 20 each solely for route/cap enforcement. The sidecar separately retains
Issue `#383`'s exact seven-path text/binary contract. No portrait, asset
implementation, dependency, provider, or product behavior is authorized.

Issue `#393` is the mandatory test-isolation prerequisite discovered by Issue
`#383` readiness. The accepted #383 route requires `STATUS.md` and
`TRACEABILITY.md` changes, while the legacy Issue #366 route-test helper read
those mutable live files when simulating the historical branch. The exact
combined 15-path #393/#396 route preserves the fixed digest, keeps direct
byte-mutation coverage, supplies the accepted digest only inside the historical
route-scope fixture, patches only `js-yaml` 4.3.0 to 4.3.1, and replaces the
stale frontend inventory set with independently reproduced architecture-bound
values. It caps additions plus deletions at 700 with 180/160/80/40 per-path
tiers. No #383 asset, route, budget, or product behavior changes.

Issue `#397` corrects the next mandatory #383 readiness false positive: the
generic `frontend/` ADR rule included two exact immutable presenter WebP data
paths. Only those two paths are classified as non-architectural; neighboring,
lookalike, arbitrary-media, code/config, and mixed frontend changes remain
ADR-gated. Owner comment `5212555339` resets its route to exactly eleven paths,
adding only the agent-context manifest with a 10-line cap to renew the unchanged
merge-closeout section's source-file hash. The route charges additions plus
deletions against current main, caps the aggregate at 500, and preserves #383's
seven-path route plus every other manifest field and agent-context control.

Issue `#367` uses exact branch `stage8-367-presenter-registry` and exactly the
fourteen paths in its GovernancePreflightV1. The route charges additions plus
deletions against current `main`: 2,000 aggregate; 500 each for the registry
implementation and focused test; 260 for registry JSON; 220 each for preflight
and ADR; 180 each for the route sidecar and route test; and 120 for every other
document. Missing/extra/lookalike/untracked/nonregular paths, malformed numstat,
or budget excess fail closed. Focused tests require exact production identities,
assets/personas/disclosure/permission, non-cloned provider-neutral voice refs,
exact canonical production-field integrity, renderer neutrality, monotonic
lifecycle, canonical trace bindings, replay rejection, hostile JSON/media
rejection, and an unselectable test-only personal shape. Voice references are
direction metadata only: no inference, synthesis, implementation, validation,
or listenable audio exists. No API, provider, renderer, UI, clone, public,
release, or production capability is established.

## Required Make Targets

The `Makefile` must expose:

| Target | Current behavior |
|---|---|
| `make quality` | Runs checks for `.stage/current`, with Final Review and Phase 1 Closure branch-prefix overrides and Phase 1 Closure `main` dispatch when StatusStateV1 records `phase1-closure` |
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
| `make checkpoint3-acceptance` | Executable Checkpoint 3A acceptance harness with C3A-CP1 API E2E, C3A-CP2 output-correctness, C3A-CP3 language-quality, C3A-CP4 media-artifacts, C3A-CP5 access/quota/retention, C3A-CP6 security/observability, C3A-CP7 performance, C3A-CP8 real-browser E2E, and C3A-R2 full-project multilingual corpus probes implemented for local/mock controlled-demo evidence only |
| `make issue280-output-correctness` | Runs only the negative Issue #280 forensic-integrity verifier; valid known-failure evidence is intentionally nonzero and the target executes no backend, API, or browser product path |
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
- the application lock and isolated frozen Semgrep tool environment are audited
  separately with no ignored advisories; Semgrep targets, rules, invocations,
  canaries, and the tool lock are hash-bound as reviewed inputs, engine config
  validation must pass, JSON output must prove nonempty file coverage with no
  findings or parse/engine errors, and positive/clean canaries must pass
- Issue `#460` replaces the expired Issue `#150` exception with exact isolated
  Semgrep `1.175.0`, upstream Click `8.4.2`, MCP `1.29.0`, and PyJWT `2.13.0`;
  every tool dependency override now fails closed; its bounded convergence
  route also evaluates Issue `#16`, `#427`, and `#434` historical contracts
  from their immutable accepted snapshots instead of mutable successor state
- Issue `#460` permits exactly three full-history Gitleaks fingerprints whose
  lines bind the frozen API-contract SHA-256; an executable provenance checker
  rejects any omission, addition, source-head/ancestry/line drift, and a real-
  secret stdin canary must fail detection before the full-history scan proceeds
- the backend Docker build explicitly verifies Click `>=8.3.3` and Semgrep
  absence in addition to the critical/high image vulnerability scan
- Issue `#428` requires the sole transitive frontend Nano ID record to be exact
  official `3.3.18`, with no direct dependency, unrelated lock drift, audit
  ignore, or threshold reduction; current architecture-checked container
  evidence must pass unchanged
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
- Voice provider artifacts must be JSON manifests.
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
- Docker Scout remains an optional documented scanner path; the executable Stage
  8 gate requires the mandatory Trivy, Grype, and pinned Dockerized scanner
  markers rather than treating Docker Scout command syntax as mandatory.
- frontend production image strips npm/npx from the runner layer before
  scanning so package-manager-only vulnerabilities are not shipped
- release checklist, runbook, demo seed data, controlled local demo guide, and
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
When `docs/STATUS.md` StatusStateV1 records `SSV1-MODE` as `phase1-closure`, plain local `make quality` on `main` dispatches the Phase 1 Closure gate.

Issue `#324` makes `scripts/quality/check_phase1_quality.py` the canonical Phase
1 entry point for both `make quality` and `make phase1-closure-quality`. Its
runner invokes the modular publication gate first, then preserved legacy global
contracts. The exact Issue `#324` scope and removed demo-document check replace
only their obsolete legacy counterparts. Source characterization fails if a
legacy check or demo marker is silently added, removed, or reordered. Other
branches and merged `main` retain legacy scope enforcement. The publication
gate derives scope from pinned Git evidence, rejects unavailable/binary
evidence, reconciles event and Git branch identity, and enforces per-file line,
byte, and maximum-line-length budgets over both recursively indexed new
packages, their mirrored tests, shared helpers, and both thin entry points.
Controlled files must be regular non-symlink files. A 500-line grandfathered
ceiling also prevents the touched pre-existing integration gates from becoming
new monoliths. Whole-file receipts prevent silent growth in the frozen legacy
checker and test. Bounded reporting prevents untrusted failure content from
creating log injection or unbounded output. A
written claim that the gate passed is not evidence; the executable exit status
is authoritative.

Issue `#319` adds `make agent-context-quality` as a shadow-only sub-gate. It
validates exact source/section hashes, module closure, active rule uniqueness,
current/history separation, frozen fixture independence, and the focused
authority/router/receipt/security tests. The Phase 1 checker invokes the
shadow validator on the worktree so a known source-hash, internal contradiction,
or fixture-provenance change fails `make quality`. A pass establishes only
schema, hash, fixture, and authored-field consistency for the evaluated bytes.
It does not authenticate command execution, check observation age, query live
GitHub, or prove semantic currency. The opt-in router can emit shadow proposals,
but it cannot select or authorize consequential work routing. A packet, capsule,
receipt, copied log, command-result field, or green shadow gate cannot establish
current truth, approval, merge eligibility, completion, release, or readiness.
Mandatory reading remains binding.

### R0C residual live-state trust boundary

Issue `#332`, under Issue `#328` OWNER comment `5152829686`, keeps agent-context
`SHADOW_ONLY` and classifies its mutable state as `STALE_GOVERNANCE`. It does
not repair or activate freshness. Consequential GitHub actions therefore retain
a human-reviewed live bootstrap boundary:

- record a non-authoritative observation with repository, issue or PR,
  `observedAt`, base SHA, and exact head SHA;
- for every required context, record check/run identity, details URL, status,
  conclusion, and the trusted GitHub Actions application identity;
- record reviewer identity, association, reviewed commit, and submission time,
  and require eligible non-author approval after the latest push;
- present the exact proposed final squash title and body for human confirmation,
  and record the confirmer and confirmation time; and
- repeat the affected observation after any relevant head, check, review,
  authority, or merge-text change.

The repository guardrails and live branch protection remain the owners of the
required-check set; this note does not replace or reconfigure them. Unavailable,
stale, wrong-head, wrong-application, self-authored, or contradictory evidence
leaves the affected consequential action `UNVERIFIED` and stops that action.
Unrelated local tests may continue. Local output and agent-authored receipts
never substitute for the live checks, eligible review, or human merge-text
confirmation. The frozen `StatusStateV1` check for `SSV1-NEXT` preserves a
legacy compatibility row only; while A1.2 remains incomplete, its green result
is not current routing evidence and cannot override the Issue `#346` to exact
Issue `#335` Cut 1 recovery pointer.
For stacked Phase 1 Closure chunk PRs whose reviewed base is another
`phase-1-closure-*` branch, local evidence must run against that reviewed base:
`GITHUB_BASE_SHA=<reviewed-prereq-head> make phase1-closure-quality` or
`GITHUB_BASE_SHA=<reviewed-prereq-head> make quality`.

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
  runtime files. Issue `#172` has a narrower named exception for only the
  GovernancePreflightV1 schema, offline validator, and focused unit test; it
  does not admit repository or GitHub integration paths. Issue `#176` admits
  only its frozen ten repository-integration paths. Its local adapter enforces
  a preflight-only first commit and final scope for the exact PR B branch and
  later process branches whose base tree contains the adapter; legacy and
  non-process branches remain unchanged. Issue `#178` alone admits its frozen CI-only GitHub verifier, exact workflow, tests, and governance paths; local quality remains offline.
  Final Review baseline
  artifacts are required inputs but not allowed closure-branch edits
- `docs/reviews/PHASE_1_CLOSURE_REPORT.md` parses as an issue table covering
  issues `#35` through `#44` with expected P0/P1/P2/P3 priorities
- `docs/reviews/PROCESS_HARDENING_FINDINGS.md` tracks deduplicated
  process-hardening review findings from sub-agent, cross-model, and blind
  reviews when those reviews produce actionable process gaps
- `docs/reviews/ISSUE_39_PRODUCTION_CLOSURE_PLAN.md` keeps the exact required
  `#39` production-closure matrix ID set, 6-column row shape, and `Open` or
  `Closed` status values valid on every Phase 1 closure quality run, not only
  when a PR attempts to close `#39`. The same validator is also enforced from
  the always-on repository guardrail so malformed matrix structure blocks PRs
  with `Refs #39` reference-only wording.
- `docs/reviews/ISSUE_39_EXECUTION_STRATEGY.md` exists and keeps the issue
  `#39` per-chunk execution protocol complete, including Definition of Done,
  pre-code planning, parallelization, review-agent, fix re-review, deployment
  transition, and complete matrix-ID coverage.
- every P0/P1 issue maps to a valid closure module and the module table covers
  the P0/P1 issue set with non-empty required evidence
- `docs/RELEASE_READINESS_REVIEW.md` preserves the Final Review No-Go posture,
  tagging block, and downgrade evidence rule
- `docs/evals/phase1_golden_questions.jsonl` is valid JSONL with the required
  minimum questions, expected answers, evidence paths, required/forbidden
  claims, citation policy, metric floors, unsupported-claim threshold of zero,
  and at least one prompt-injection and one safety-boundary fixture
- Phase 1 demo docs, including `docs/demo/CONTROLLED_LOCAL_DEMO.md`, include runnable local startup,
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

### Checkpoint 3 Acceptance Harness

`make checkpoint3-acceptance` is a standalone Checkpoint 3A target. C3A-CP1
implements the first executable probe, API E2E foundation, by dispatching
`uv run pytest tests/acceptance/test_checkpoint3_api_e2e.py -q` through the
local/mock API path. The API E2E probe proves project creation, approved
synthetic knowledge upload and approval, ingestion/chunk/store, retrieved
grounded context, grounded walkthrough generation, unsupported-claim
evaluation, stored output replay through the API idempotency boundary, and
bounded `/api/v1/ops/status` record-count evidence.

C3A-CP2 implements the second executable probe, output-correctness, by
dispatching
`uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q`
through the same local/mock API path. The output-correctness probe verifies
required generated facts against runtime `acceptedScriptText`,
`evaluation.claimSupports`, `contextRefs`, citation indexes, project/document
IDs, source checksums, evidence snapshots, idempotent API replay, and bounded
ops record-count evidence. It includes negative coverage for correct-looking
text without citation/evidence binding, unsupported generated claims, and
cross-project fact replay.

Issue `#276` repairs C3A-CP2 so it also proves real user-visible multilingual
output correctness for the Priority 1 catalog: `en`, `hi`, `es`, `de`, `fr`,
`pt-BR`, `it`, `nl`, `pl`, `uk`, `ru`, `zh-Hans`, `zh-Hant`, `ja`, `ko`, `ar`,
`arz`, `he`, `fa`, `tr`, `vi`, `id`, `fil`, `th`, and `ms`. The probe requires
the backend-driven language catalog, catalogs Priority 2 Indian regional
languages as planned/unsupported local demo, executes every Priority 1 runtime
API path, requires source English plus target-language transcript plus English
reference/back-translation per segment, validates native scripts and RTL
direction, preserves citation/source/evaluation/context/claim-support bindings,
requires selected-audience semantic preservation, rejects heading-only generated
claims, requires full generated-script segment coverage, expands small approved
local/demo documents within retrieval top-k to all approved claim chunks, compares supported
controlled translations against independent golden strings rather than the
implementation fixture alone, requires Stage 6 metadata artifact parity,
requires the downloadable translated-script artifact to contain the same
trilingual transcript data as the UI and metadata artifact rather than only the
flat target-language text, and writes
`reports/checkpoint3-multilingual/priority1-coverage-matrix.json` plus
`reports/checkpoint3-multilingual/checkpoint3a-multilingual-summary.json`.
The coverage matrix must include one positive row per Priority 1 language plus
mutation rows that fail for partial text, one-segment partial text, English
fallback, romanized or wrong-script fallback, missing source English, missing
English reference, citation drift, missing bindings, metadata-only success,
artifact-only success, glossary-forced English leakage, and untranslated
source-domain term leakage such as standalone `walkthrough`. `COMPLETED` is
invalid unless transcript correctness validation passes. The current local/demo
translation boundary is generated walkthrough scripts from approved local/demo
knowledge, not a separate raw uploaded knowledge-document translation API; a
raw-document translation surface requires a future issue and equal executable
coverage before it may be claimed.

C3A-R2 implements the full-project multilingual correctness repair gate for
issue `#278` by dispatching
`uv run pytest tests/acceptance/test_checkpoint3_full_project_multilingual.py -q`
through the same Checkpoint 3 acceptance harness. The probe is anchored to
`backend/app/stage6.py` catalog fields: `LANGUAGE_CATALOG`,
`LANGUAGE_CATALOG_BY_TAG`, `SUPPORTED_LANGUAGES`,
`local_demo_support_status`, `provider_support_status`, and
`test_coverage_level`. Every language marked `SUPPORTED`,
`LOCAL_DEMO_FIXTURE`, and `CHECKPOINT3A_EXHAUSTIVE` must have current evidence
in the full-project matrix; Priority 2 languages remain planned/unsupported
locally unless a future issue introduces equivalent evidence.

The C3A-R2 fixture is public-safe and synthetic. It covers a multi-document
project, multiple sections, full body transcript segments, multiple cited
claims, claim-support bindings, exported artifacts, class-specific checks for
Hindi/Devanagari, RTL, CJK, and Latin-script languages, at least one
multi-document supported claim, and at least one row that exposes heading-only,
partial-section, or missing-body translation. Stale evidence is defined by
fixture hash changed, expected-output hash changed, language catalog version
changed, validator version changed, artifact schema version changed, or report
schema changed. The probe writes
`reports/checkpoint3-multilingual/full-project-coverage-matrix.json` and
`reports/checkpoint3-multilingual/full-project-correctness-report.json`, and it
rejects metadata-only success, artifact-only success, citation id preservation
without source-span preservation, citation drift, unsupported/planned-language
fake success, stale coverage rows, and supported-language coverage removal
without demotion/refusal. This proves a governed full-project corpus gate only;
it does not prove arbitrary-project translation quality, provider quality,
hosted/public demo readiness, raw uploaded knowledge-document translation API
behavior, public distribution, or production readiness.

C3A-R3 PR A-D and the attempted PR E remain historical implementation records,
not current completion authority. Two deterministic executions of canonical
`tests/acceptance/test_issue280_pr_e_closure.py::payload` at evidence head
`f93653e8a11e697c88766b207fb01c18662339d6` completed all 525 combinations with
zero translation refusals: CONCISE, STANDARD, and DEEP each completed 175. All
75 successful language/depth groups retained seven distinct accepted English
scripts but collapsed to one visible target body across seven audiences. The
historical 217-completed/308-refused/31-group aggregate was not reproduced and
is a superseded, unsupported assertion rather than current evidence.

`make issue280-output-correctness` now reads only the strict negative forensic
artifact. It does not start services or execute backend, API, contract, browser,
download, or canonical product-path tests. Valid evidence returns
`ISSUE_280_NOT_FIXED`; stale, malformed, and contradictory artifacts return
distinct nonzero results. Issue #280 is closed in GitHub but is not fixed. Any
future execution runner, oracle, or product repair requires a separate issue,
branch, PR, tests, evidence, and approval.

C3A-CP3 implements the third executable probe, language quality, by dispatching
`uv run pytest tests/acceptance/test_checkpoint3_language_quality.py -q`
through the same local/mock API path. The language-quality probe verifies
runtime `acceptedScriptText` against deterministic checks for coherent
walkthrough structure, audience-appropriate English Stage 4 tone, citation
readability, placeholder absence, debug/internal leakage absence, non-trivial
length, no unsupported cross-project language, API-visible idempotent replay,
`evaluation.claimSupports`, `contextRefs`, evidence snapshots, and bounded ops
record-count evidence. It includes negative coverage for docs/prose/static or
canned-success substitutions, grounded-looking placeholder output, trivially
short citation-bearing output, debug/internal leakage, malformed citation
placement, cross-project language insertion, and style text without runtime API
evidence.

C3A-CP4 implements the fourth executable probe, media artifacts, by dispatching
`uv run pytest tests/acceptance/test_checkpoint3_media_artifacts.py -q`
through the same local/mock API path. The media-artifacts probe verifies
runtime Stage 6 and Stage 7 local/mock artifact evidence: translated script,
subtitles, voice manifest, synthetic-avatar consent, demo HTML, render manifest,
and video-export placeholder. It checks artifact MIME type, safe filename,
Base64 content, checksum, source-run/evaluation/citation/context/claim-support
binding, local/mock provider posture, idempotent API replay, no real media
binary overclaim, no cloned identity, and bounded ops record-count evidence. It
includes negative coverage for docs/prose/static or canned-success
substitutions, artifact-shape-only evidence without source binding, checksum or
MIME mismatch, real-media overclaim, and cloned-identity overclaim.

C3A-CP5 implements the fifth executable probe, access/quota/retention, by
dispatching
`uv run pytest tests/acceptance/test_checkpoint3_access_quota_retention.py -q`
through the same local/mock API path. The access/quota/retention probe verifies
runtime project creation for at least two approved synthetic local projects,
knowledge upload/approval/ingestion, grounded walkthrough generation,
cross-actor and cross-project access boundaries, mismatched source-run replay
rejection, scoped idempotency replay, deterministic upload, prompt, document,
and local hosted-demo quota behavior, API-visible terminal retention replay
denial, tombstone evidence, bounded `/api/v1/ops/status` evidence, local/mock
provider posture, and public-safe redaction. It includes negative coverage for
docs/prose/static or canned-success substitutions, status-only evidence,
cross-project or mismatched source-run replay, idempotency bypass attempts,
over-limit request leakage, and deleted/retained evidence replayed as active.

C3A-CP6 implements the sixth executable probe, security/observability, by
dispatching
`uv run pytest tests/acceptance/test_checkpoint3_security_observability.py -q`
through the same local/mock API path. The security/observability probe verifies
runtime API-visible security controls, privacy/redaction behavior,
observability metadata, bounded failure evidence, and anti-false-pass guards
from approved synthetic local project knowledge. It creates synthetic projects,
uploads/approves/ingests knowledge, generates grounded walkthrough runs,
checks trace/run/evaluation metadata, bounded `/api/v1/ops/status`
evidence, local/mock provider posture, redacted hosted-demo events, missing
approval failure, unsafe upload failure, prompt-injection refusal, unsupported
claim rejection, cross-project replay rejection, same-payload cross-actor access
denial with a reused idempotency key, same-actor idempotency conflict behavior,
and source/run binding failure. It includes
negative coverage for docs/prose/static-snapshot or canned-success
substitutions, style-only/status-only text, success-shaped dictionaries without
acceptance-runtime nonce/source/run/observability binding, raw unsafe payload leakage, and
token/password/secret/api-key redaction including snake_case variants.

C3A-CP7 implements the seventh executable probe, performance, by dispatching
`uv run pytest tests/acceptance/test_checkpoint3_performance.py -q` through the
same local/mock API path. The performance probe verifies runtime project
creation for approved synthetic local projects, knowledge upload/approval/
ingestion, grounded walkthrough generation, idempotent replay, and bounded
`/api/v1/ops/status` evidence. It records named operation timings, explicit
thresholds, request ID binding, elapsed durations, pass/fail status,
source-run/evaluation binding, generation trace latency, local/mock provider
posture, and public-safe failure context. It includes negative coverage for
docs/prose/static-snapshot or canned-success substitutions, style-only/
status-only text, success-shaped timing dictionaries without runtime nonce,
missing request/source/run/performance binding, stale run evidence,
cross-project replay, implicit thresholds, zero-duration fake timings, unsafe
public/provider/production claims, raw uploaded content leakage,
prompt-injection text leakage, sensitive token leakage, bounded subprocess
timeout handling, and redacted failure summaries.

C3A-CP8 implements the eighth executable probe, real-browser E2E with no
success-path interception, by dispatching
`npm --prefix frontend run test:smoke -- --config=playwright.checkpoint3.config.ts`.
The acceptance harness assigns isolated loopback backend/frontend ports for the
CP8 subprocess unless the caller explicitly provides CP8 port environment
overrides, so stale local browser-review servers cannot make the default gate
nondeterministic. The Playwright probe launches the local backend and frontend,
drives the user-visible controlled-demo workflow with approved synthetic
knowledge, observes browser API requests and responses without fabricating
success, captures runtime nonce, request sequence, project/document/ingestion/
run/evaluation/source binding, artifact metadata, bounded `/api/v1/ops/status`
evidence, and local/mock provider posture, and rejects missing binding,
stale/cross-project replay, static snapshots, API-only substitutes, and
success-shaped canned evidence.

`make checkpoint3-acceptance` remains the standalone Checkpoint 3A quality
target. On branch
`phase-1-closure-278-c3a-r2-full-project-multilingual-corpus`, the Phase 1
Closure `make quality` path also executes
`uv run pytest tests/acceptance/test_checkpoint3_full_project_multilingual.py -q`
through `scripts/quality/check_phase1_closure_docs.py`, so PR CI runs the same
C3A-R2 full-project corpus check for issue `#278`. The harness must reject
docs/prose/static-snapshot command substitutions for implemented probes, run
implemented probes with `subprocess.run(..., shell=False, timeout=120)`, and
summarize failed probe output with bounded/redacted text. It must not claim
Checkpoint 3B, Checkpoint 3C, hosted/public demo, provider setup,
cloned-identity readiness, real-media readiness, public distribution, or
production-readiness success from Checkpoint 3A local/mock evidence.

C3B-PR1 is a Phase 1 Closure planning/governance gate, not a runtime acceptance
target. The issue `#274` scope is checked through the Phase 1 closure docs gate:
the exact branch/file allowlist must pass, near-match branches must fail closed,
the preflight artifact must define Checkpoint 3B consent/provenance planning,
acceptance contracts, risk boundaries, and future issue sequencing, and the
status ledger must keep issue `#249` open while reconciling PR `#273` and issue
`#269` as merged/closed. C3B-PR1 must not authorize Checkpoint 3B
implementation, Checkpoint 3C, hosted/public demo, provider setup, paid spend,
public URLs, cloned identity runtime, real media, public distribution, or
production readiness.

The repository guardrail also checks PR body content on pull-request events:
generic PRs must use reference-only issue linkage such as `Refs #<issue>` and
must not include issue-closing keywords in the title/body/branch commit
messages except for explicitly allowed canonical stage issue closures, which are
`#2`, `#5`, `#4`, `#10`, `#11`, `#12`, and `#13`. Issue `#39` must not
appear with auto-closing keywords in the title/body/branch commit messages.
Non-trivial PRs must provide the template's meaningful five-point `Reviewer
overview` before detailed governance/evidence sections; placeholders and copied
template instructions fail. Separately,
non-trivial PRs must include completed preflight evidence rows for
the required intent/spec, source-facts, failure-matrix, test, docs/gates,
adversarial-review, review-prompt-set, stop-rule, and skill/tool-selection
categories. The guardrail rejects false-pass preflight
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
Failure-matrix, review-prompt-set, stop-rule, and skill/tool-selection rows must
link PR-specific artifacts rather than generic governance docs. Skill/tool rows
must prove approved installed skills/docs were checked first and that custom
skills/plugins were not used without documented gap, lock, notice, and approval
evidence.
Process-critical governance docs and process-review registers stay in the
non-trivial category even for text-only edits because those files define future
automation behavior and review-loop prevention.

Issue `#300` makes `make issue280-output-correctness` negative-only. Its verifier
exits `1` with `ISSUE_280_NOT_FIXED`; stale, malformed, and contradictory evidence
have distinct nonzero exits. It is not a required green CI job; CI may run its
tests and static integrity through `make quality`. Make reports recipe failure as exit `2`.
Product/runtime repair, including the runtime/browser
`correctnessReport.status = "PASSED"` surface, belongs to a later issue.

The required `Product and reviewer context` section is executable policy for
every non-trivial PR. `scripts/guardrails_check.py` applies
`product_context_failures` to the PR body on pull-request events and requires
ten PR-specific subsections: end product goal, current state, problem, exact
changes, completed state, expected outcome, not-expected scope, end-goal
impact, remaining gap, and reviewer validation. The parser removes issue
references and links before measuring whether prose is self-contained, rejects
template instructions and generic filler, requires expected/prohibited/
evidence/pass/fail reviewer fields, and rejects unsupported affirmative claims
of production readiness, production deployment, release, or public
availability. When `Exact changes` claims a number of fields, changes,
controls, checks, items, components, files, paths, rules, or requirements, the
same section must contain at least that many distinct, meaningful Markdown list
entries. A bare count, duplicated entries, or placeholder entries therefore
cannot pass as a complete explanation.

This gate connects each contribution to the end-to-end demo and eventual
production path without treating that direction as production authorization.
CI can verify section shape and known false-pass classes; the independent
reviewer must validate the truth of the product position, the expected and
prohibited outcomes, and the remaining gap. Because `policy-gates` is required
by branch protection and reruns on `pull_request.edited`, an incomplete edited
body blocks merge even when code checks remain green.

The PR template also requires a `Human verification checklist` for non-trivial
PRs. This checklist converts reviewer-focus points into rows with exact
data/source/artifact references, official URL and verified/accessed date when
facts can change, pass/fail criteria, and residual-risk owner. It is the
durable PR-body surface for human-only verification work such as provider/tool
comparisons, pricing, quota, rate-limit, latency, capacity, retry/backoff/
timeout assumptions, user-facing demo or recruiter-flow checks, legal/license/
consent decisions, upload/prompt/transcript/provider-output/model-output trust
boundaries, deletion/erasure, disclosure, provenance, AI/RAG/generated-media
claims, citations, unsupported-claim checks, source-run/eval/media binding,
launch-boundary checks, production-readiness posture, and final merge-message
wording. Absence of this checklist is a blocking human-review finding for
non-trivial PRs even when the current script-level policy gates have passed. A
future guardrail PR may make the checklist executable; until then reviewers
enforce it through the PR body and template.

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
- CPython image scanner disagreement may pass only through issue-specific fixed
  evidence that still preserves raw Trivy and Grype reports.

Direct pushes to `main` remain a repository-settings requirement enforced through branch protection or rulesets rather than the stage-quality workflow itself.

## Heartbeat 1 B browser evidence gate

Issue `#306` must run `scripts/ci/heartbeat1-browser.sh` at the exact reviewed head.
The gate owns one frontend and two sequential backend PIDs, proves a waited-for restart against one hash-bound snapshot, and permits no browser interception or direct-backend shortcut.
Traces begin only after both controlled responses and protected runtime inputs are deleted.
Full evidence may upload only after `scripts/ci/heartbeat1_evidence.py` recursively scans the snapshot, logs, reports, DOM, screenshots, archives, and archive members and records `ZERO_MATCH` for the exact run/head.
Focused A1/A2 regressions, exact-branch/allowlist enforcement, `make quality`, required CI/security checks, and independent exact-head approval remain mandatory.

## Heartbeat 2 evidence integrity gate

Issue `#308` directly authorizes a post-Checkpoint-B local/mock curated reviewer demo; it is not Product Mode 2 or Issue `#20`. Contract reset 6 sets PR A to at most nine files, 1,600 charged lines, and five surfaces; PR B remains 12/900/6 and the aggregate is 15/2,500/8.

`scripts/ci/heartbeat2_evidence.py` must fail closed on stale identity, malformed provenance, any skipped/non-passing result, malformed ledgers, request/response mismatch, non-local trace traffic, source drift, broken product joins, artifact mismatch, unsafe archive, or forbidden material. `SEMANTIC_PASS_LOCAL` is not execution evidence. CI acceptance additionally requires exact-head checkout, zero-exit runner execution, `CI_EXECUTION_BOUND`, success-only upload, and post-run artifact/workflow metadata reconciliation. PR B remains blocked until PR A is approved at exact head, merged, and verified.

Both PRs require behavioral RED before GREEN, exact branch/allowlist checks, focused regressions, guardrails, `make quality`, required CI/security gates, and eligible non-author exact-head approval. Evidence upload is success-only; providers, real media, deployment, hosting, production claims, private data, and Q&A remain absent.

## Issue 317 semantic repair slice 1 gates

Issue `#317` uses exact branch
`phase-1-closure-317-issue280-semantic-repair-slice1`, exactly 18 changed paths,
at most 3,000 charged lines, and ten meaningful surfaces. The Phase 1 checker
fails closed for missing, extra, near-match, over-budget, or binary scope.

Required focused evidence is:

```bash
uv run pytest -p no:cacheprovider tests/unit/test_issue280_semantic_oracle.py tests/acceptance/test_issue280_semantic_repair_slice1.py
uv run pytest -p no:cacheprovider tests/contract/test_issue280_ui_api_artifact_parity.py tests/acceptance/test_issue280_pr_e_closure.py
npm --prefix frontend exec playwright test -- --config=playwright.issue280.config.ts --project=issue280-desktop --grep "seven distinct Spanish"
uv run pytest -p no:cacheprovider tests/unit/test_phase1_closure_docs.py
```

The first command must prove every zero-tolerance semantic threshold over all
seven mandatory rows and reject all frozen false-pass mutations. Browser
evidence must use the real Next-to-backend path without interception. Full
validation additionally requires repository guardrails, `make quality`, lint,
typing, `make ci`, security, dependency audit, container scan, secrets scan,
evaluation, and a forced pull-request-event guardrails run against the final PR
body. The negative `make issue280-output-correctness` command remains
intentionally nonzero historical evidence and is not converted into a green
runtime gate.

## A2.3a evaluation-lineage contract gate

Issue #351 adds no runtime behavior. The Stage 8 checker requires the exact
eight-file route and freezes checksum-v2 schema, field set, serialization,
golden vector, local/mock claim boundary, migration, and rollback prose.
The second and final implementation repair binds scope independent of context
count, every accepted retrieval/refusal semantic, exact approval timestamps,
unique evidence identity, and one canonical full stored-score conversion.
Focused tests must fail for every marker mutation, golden-vector drift, a
near-match branch, a ninth file, or missing, stale, forged, legacy-v1,
duplicate, cross-scope, wrong-schema, and normalization drift. Context budgets use
`uv run pytest -q tests/unit/publication_boundary/test_scope.py -k per_file_context_budgets_are_executable`.
A2.3b must later supply runtime mutation proof; exact-head required CI and
eligible non-author approval remain pending human-only merge gates.

## Issue #360 dependency-security convergence gate

The exact Issue #360 Stage 8 route requires base `b9a2a8cd4aa05328116565990fc30ae44592c875`, exactly
18 paths, and at most 650 charged lines. It refreshes only frontend development-tool `brace-expansion` 5.0.8 to
5.0.9 and isolated Semgrep `cryptography` 49.0.0 to 50.0.0, preserving all other package versions. Parsed-lock
isolation, strict audits, installed identities, Semgrep validation/scan/canaries, full gates, exact-head CI, and
independent review are mandatory. Issue #359 remains open with its branch immutable until convergence merge and
merged-main verification; that historical Issue #360 route did not change Issue #150 or Issue #358. Issue #150's
later MCP-only renewal expires `2026-08-28`. This reference-only gate grants no
product, provider, deployment, release, public-availability, or production-readiness authority.

## Issue #375 ignored-cache pruning gate

The Issue #375 Stage 8 route is bound to base
`f2312947ef670becfa0373000c8ae6ef1f411e20`, exactly seven paths, and at most
600 charged lines. The A2.3b semantic scan must use `Path.walk()` top-down and
remove governed ignored/generated directory names before descent.
It must still scan similarly named repository-owned directories and must not
follow directory or file symlinks. Focused mutations, context budgets,
guardrails, full quality, CI, exact-head checks, and independent review remain
mandatory. This traversal repair grants no product, provider, media, release,
public-availability, or production-readiness authority.

Source fact verified 2026-08-05: the official Python
[`Path.walk()` 3.13 documentation](https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.walk)
and [3.14 documentation](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.walk)
specify top-down `dirnames` mutation for pruning and no directory-symlink
following by default. The implementation also rejects file symlinks and raises
every walk error rather than silently omitting repository-owned source.

## Issue #372 citation-lineage parity gate

The exact `cut1-372-citation-index-parity-post380` route from
`372fb78245b8890157ffe54f48b90e523017bc43` is limited to the eleven
preflight paths. Its RED/GREEN evidence proves:

- every claim-support index equals the marker in its exact visible `scriptSpanStart`/`scriptSpanEnd` slice and context;
- valid stored/replayed results preserve accepted/generated text, provider claims, supports, context refs, and indexes;
- restored text, marker, provider-claim, support-index, and link drift fails closed without completed-run replay; and
- raw lineage types/status and restore-time size/count/marker work fail closed per row without clearing valid siblings;
- both exact-base-to-index and exact-base-to-working-tree charges are validated, using the greater value; and
- tenant/project isolation, unsupported-claim refusal, retrieval order, and key-free local/mock posture stay unchanged.

Focused verification starts with:
```bash
uv run --python 3.13 --frozen pytest -p no:cacheprovider tests/acceptance/test_checkpoint3_output_correctness.py tests/unit/test_local_durability.py
uv run --isolated --python 3.14 --frozen pytest -p no:cacheprovider tests/acceptance/test_checkpoint3_output_correctness.py tests/unit/test_local_durability.py
uv run --python 3.13 --frozen pytest -p no:cacheprovider tests/unit/test_stage8_quality_gate.py tests/unit/publication_boundary/test_scope.py
make checkpoint3-acceptance
```
The complete suite, quality, CI, security, evaluation, and applicable real-browser gates remain mandatory. A fixed
citation value, renumbering, loosened assertion, skipped test, narrowed gate, retrieval change, or extra path fails.
This repair is not presenter/media, deployment, release, public availability, production readiness, or Cut 1 evidence.

The complete diff must remain at or below 1200 charged lines. A twelfth path or charge 1201 is a gate failure.

## Issue #389 frontend runtime npm security gate

The exact `cut1-process-389-frontend-runtime-npm12-security` route starts from
`48fc32a2689c9bbc03742d774f3eadb8a500dafc`, requires exactly fourteen paths,
and permits at most 900 additions plus deletions. Per-path change ceilings are
180 for `stage8_node_security.py`, 220 for its test, and 40 for the Stage 8
checker. Complete Git evidence, preflight identity, missing/extra paths, binary
numstat, branch/base drift, and every budget fail closed.

The shipped frontend must use signed Chainguard index
`sha256:d8d2883b26d4fde4e524d0068cd78abbb23c7c2113a22e67a02cc73a9182552d`,
execute Node 26.7.0, derive from Wolfi `npm-12 12.0.2-r2`, match a finite
architecture-bound inventory, and pass the existing runtime-hardening,
reproduction, SBOM, and Trivy/Grype consensus checks through Medium. The old
digest, npm r1, mutable tags, scanner suppression, waiver, and product or
release expansion are prohibited.

## Issue #396 transitive js-yaml security gate

The exact `cut1-process-396-js-yaml-4-3-1-security` route starts from
`9ee3f4a4d3b8cf1e78b5a878904748b60d557a76`, requires exactly eleven paths, and
permits at most 500 additions plus deletions. The preflight cap is 180, each
focused test cap is 80, and every other path cap is 40.

Only `node_modules/js-yaml` may change in `frontend/package-lock.json`, from
4.3.0 to integrity-bound 4.3.1. `frontend/package.json`, direct dependencies,
overrides, and every unrelated lock entry must remain identical to the base.
Focused mutation tests, `npm ci`, `npm audit --audit-level=high`, repository
dependency/security gates, complete quality and CI, exact-head review,
eligible non-author approval, and merged-main acceptance are mandatory. No
waiver, product/media behavior, deployment, release, public, or production
claim is authorized.

Issue #396 is absorbed into PR #395 because its mandatory STATUS update needs
Issue #393 isolation while #395 needs its audit repair; both close only after the
combined exact head passes review, approval, merge, and merged-main acceptance.

## Issue #401 pypdf 6.15.0 security gate

The exact `cut1-process-401-pypdf-6-15-0-security` route starts from
`9cf6e01f9d0c32f25c229b5adf38c6eb716ca9a0`, requires exactly thirteen paths, and
permits at most 600 additions plus deletions. The preflight cap is 190, each
focused test cap is 100, the route sidecar cap is 80, the ADR cap is 60, and
every other path cap is 40.

Only the direct pypdf requirement, root lock metadata, and sole pypdf package
record may change from 6.14.2 to official 6.15.0. Exact PyPI artifact URLs,
sizes, SHA-256 values, unrelated-dependency isolation, existing PDF rejection,
strict `pip-audit`, repository security gates, full quality/CI, exact-head
review, eligible non-author approval, and merged-main acceptance are mandatory.
No waiver, PDF support, product/provider/media, deployment, release, public, or
production claim is authorized. PR #400 must refresh from accepted main only
after this prerequisite passes merged-main acceptance.

## Issue #403 nanoid 3.3.17 security gate

The exact `cut1-process-403-nanoid-3-3-17-security` route starts from
`246042d82483e0d84c74a5d5c9736a72c710e369`, requires exactly fifteen paths, and
permits at most 650 additions plus deletions. Only the transitive
`node_modules/nanoid` lock record may move from 3.3.16 to official 3.3.17.

The gate proves exact registry URL and SHA-512 integrity, unchanged
`frontend/package.json`, no direct nanoid dependency, and no unrelated lock
drift. `npm audit --audit-level=high`, repository dependency/security gates,
complete hosted CI/container evidence, exact-head review, eligible approval,
and merged-main acceptance are mandatory. No waiver, product/UI/provider/media,
Docker/workflow, deployment, release, public, or production claim is authorized.

## Issue #405 Heartbeat 2 accepted-main reliability gate

The exact `process-405-heartbeat2-main-reliability` route starts from accepted
main `03b82c6471b66f9ca8a2781e93a90397a9cf8921`, requires exactly nine paths,
and permits at most 800 additions plus deletions. A hosted Heartbeat 2 failure
must remain a failing check. It may publish only a bounded diagnostic tail
after the complete candidate and minimized output both pass the existing
controlled-input and canary privacy scan. The diagnostic binds exact run, head,
failure stage, and source log; raw candidate evidence remains unpublished.

The gate rejects retries as acceptance, failure swallowing, stale or foreign
diagnostics, symlinks, malformed identifiers, oversized logs, output
collisions, privacy-scan failures, and any weakening of trusted success
evidence. Focused hostile tests, full quality/CI/security/eval/browser/
performance/container evidence, independent exact-head review, eligible
approval, and merged-main acceptance remain mandatory.

The recovered diagnostic identifies `CI_PROVENANCE`: the browser completed,
but the verifier historically allowed only `push` and `pull_request` events.
`workflow_dispatch` is eligible solely when GitHub binds the workflow ref
exactly to `refs/heads/main` and the workflow SHA equals the expected accepted
head. Manual feature-branch, tag, lookalike-main, stale-SHA, or foreign-context
dispatch remains ineligible.

## Issue #382 Cut 1 narration speech-lock gate

Branch `stage8-382-cut1-narration-lock` starts from accepted main
`b5c102dd3be7278aac8bb009211feed4d365d5d2`, requires exactly fourteen paths,
and permits at most 3,200 additions plus deletions with the OWNER-approved
per-path ceilings. Deletions grant no credit.

The gate requires the OWNER-amended NarraTwin-host opening, exact canonical
presenter bytes/two-token substitutions, citation
review/spoken separation, ordered lifecycle and illegal-edge refusal, current
passing evaluation and explicit approval, edit invalidation, latest-only
single-use consumption, complete checksum/receipt binding, exact consumed-key
to validated-receipt-key equality on restore, strict bounded
restore/replay, scope/presenter/source tamper rejection, concurrency proof,
redacted logs, and exact route/budget mutations. Focused CPython 3.13/3.14,
Ruff, mypy, relevant regressions, and every applicable aggregate repository
gate must pass. No API/UI/TTS/audio/provider/media/deployment/release or
production evidence is claimed.

### Issue #368 Google TTS governance reconciliation gate

The governance-only branch must change exactly the 14 preflight paths and stay
within 3,200 additions plus deletions with no deletion credit. It must pass the
focused route tests, guardrails and `make quality`; contain no runtime,
dependency, credential, audio, frontend, workflow or release mutation; and
resolve every Critical/High/Medium/Required adversarial finding.

A later implementation gate starts with failing tests for semantic profile
mapping, pre-egress validation, injected ADC/transport behavior, zero network in
tests, untrusted audio decoding/signal checks, current authority binding,
idempotency/concurrency/crash recovery, billable-unknown timeout handling,
redaction, retention/deletion and exact replay. Automated tests never call
Google. A final 90–120-second artifact still requires exact-hash OWNER listening.

### Issue #368 Google TTS runtime-transport prerequisite gate

Exact branch `stage8-368-cut1-google-tts-runtime-transport` starts at
accepted main `6766da34d73e301358f84f8eefb0985927292a26`, changes exactly 18 governed paths,
and stays within 3,600 additions plus deletions with no deletion credit. The
route requires committed RED-before-GREEN proof; optional lazy ADC with the
fixed cloud-platform scope; exact quota-project/checksum binding; all-answer
DNS screening; direct checked-peer port-443 TLS/SNI; no proxy/redirect;
single-use prepared sessions; bounded response reads; redacted errors; truthful
pre-egress versus egress-possible failures; no retry; and provider-neutral,
disabled-default startup regressions. The dependency-contract test preserves the
immutable Issue #401 pypdf exactness while normalizing only the reviewed
`google-auth==2.56.3` optional-provider closure and rejects any other drift.
`google-auth==2.56.3` is optional and locked with its complete closure. Tests use fakes only; Google remains disabled,
no credentials or real call/audio exists, and release remains No-Go.

The historical adapter route remains independently enforced. Exact branch
`stage8-368-cut1-google-tts-adapter-implementation` starts at
`de0cd683cd05dda91c8f0df53d05c8b55c81d213`, changes exactly the governed 21
paths, and stays within 5,600 additions plus deletions with no deletion credit.
The route requires committed RED-before-GREEN proof; exact prompt/hash and unary
request tests; receipt, privacy, budget, quota, concurrency and activation
preconditions before fake identity/transport; redirect/DNS/TLS/proxy refusal;
strict response/base64/WAV/signal validation; durable replay, billable-unknown,
tombstone and tamper tests; pre-write transport proof, post-egress authority
revalidation, privacy-screen evidence, cost reconciliation, transactional
deletion, cross-instance locking/stale-instance tombstones, required durable
state, opaque prepared-session send capability and bounded-restore fault tests;
provider-neutral API regressions; and zero real
network/provider calls. Google remains disabled and release remains No-Go.

### Issue #413 frontend runtime security gate

### PR-body consistency gate

Issue #415 introduces `make pr-body-check PR=<number>` and `make
pr-reconcile PR=<number>`. The check fails closed when the unique managed block
is missing, malformed, stale, unsafe, or inconsistent with the live pull
request. Its workflow is trusted-base only and must not become a required main
context until post-merge canary evidence confirms no unexpected mutation.
Its bootstrap Issue #415 PR receives no self-hosted check because GitHub sources
`pull_request_target` workflows from default branch; committed and live local
evidence replaces it only for that introducing PR.

Branch `cut1-process-413-frontend-runtime-openssl` owns exactly nineteen paths
and at most 5,000 charged lines. The gate binds exact multi-arch runtime,
Node-binary and `libatomic` source indexes plus amd64/arm64 manifests; verifies
effective OpenSSL 3.5.7 and exactly eight Wolfi package records; preserves
package/SBOM metadata; checks the non-root Node entrypoint,
minimal filesystem, permissions and HTTP startup; reproduces two independent
builds with same-builder normalized inventory equality; validates CycloneDX
SBOM identity; and requires Trivy/Grype consensus through Medium. Exact image,
platform, config, package and OpenSSL identities remain portable invariants;
the complete application-layer filesystem hash is not hardcoded across native
and emulated builders. Floating references, affected 3.6.0–3.6.3, hidden
metadata, wrong architecture, malformed or unequal inventories, scanner
disagreement, and weakened thresholds fail closed. Product behavior,
deployment and release are outside this gate.
## Issue #421 Cut 1 atomic grounding repair gate

Branch `stage8-421-cut1-atomic-project-facts` is limited to the exact twenty-one
paths in `docs/governance/preflights/issue-421.json` and 4,000 additions plus
deletions without deletion credit. The committed RED reproduces exactly
eighteen unsupported claims from genuine accepted sources before the special
policy exists.

GREEN requires exact facts/source/classification/span validation, code-owned required-predicate
coverage and complete proposition mapping, all-style caller-injection refusal,
generic-evaluator parity, project/tenant isolation,
persist/restore replay, conditional evaluation-lineage binding, and all three
Issue #382 narration/approval/receipt steps for the selected Meera candidate
through public service methods. The gate pins 261 words, 1,904 UTF-8 bytes,
SHA-256 `3edffc6169460546ae0bdee867fdeaf3c0ae383535e2976e0333f39c03ff614e`,
and rejects non-selected presenter authority.
Adversarial RED/GREEN additionally proves that canonical narration uploaded as
ordinary knowledge cannot pass, Cut 1 mismatch cannot retain generic supports,
style/policy drift cannot restore, ambient telemetry hooks are never invoked,
the project-core premise has an entailing PRD span, and live receipt replay
rejects post-consumption source or presenter drift.
It also removes or tampers the current facts contract after draft and after
receipt issuance and requires both live evaluation and receipt replay to fail.
No real provider call, telemetry egress, audio, deployment, distribution,
production-readiness, or release claim is part of this gate.

### Issue #427 Architecture Reset Gate

The exact branch `cut1-process-427-authority-architecture-reset` dispatches to
Stage 8 and delegates to `scripts/quality/issue427_architecture_reset.py`. The
dedicated standard-library gate fails closed on exact branch/base/history,
preflight-only first commit, no merge or replace-ref interference, fourteen-path
scope, 2,000 aggregate additions-plus-deletions, valid text numstat, strict
duplicate-free closed JSON, approved proposal hash/bytes/lines, Sections 1–12,
AK-001 through AK-023, ordered Children A–F, frozen architecture-review identity,
nonactivation, and prohibited-capability boundaries.

Required local commands are:

```text
uv run pytest -q tests/unit/test_issue427_architecture_reset.py
uv run pytest -q tests/unit/test_stage8_quality_gate.py
python3 scripts/guardrails_check.py
GITHUB_BASE_SHA=f2a32b8c022c015dfa4e87c700fbfe1ed0d85183 NARRATWIN_POLICY_ONLY=1 make quality
GITHUB_BASE_SHA=f2a32b8c022c015dfa4e87c700fbfe1ed0d85183 make stage8-quality
make quality
uv run ruff check scripts tests
uv run mypy scripts tests
git diff --check
make ci
make security
make dependency-audit
make container-scan
make secrets-scan
make eval
```

For Issue #427, `make phase1-closure-quality` is exactly
`NOT_APPLICABLE_SUPERSEDED_BY_OWNER`; it must not be run or reported as passed.
Hosted exact-head protected contexts, fresh specialist reviews, eligible
non-author approval, final exact-byte OWNER approval, reference-only merge text,
merged-main verification, status reconciliation and explicit issue closeout
remain human/external gates. A green local gate creates no authority decision,
active route, automatic Child A–F authorization, or runtime/release/production
capability.

## Issue #431 Child A authority-core gate

The exact branch `cut1-process-431-authority-core-schemas-state-matrices` starts
at `4d239942eeda0c0b6c385b2d85dae873af076aa6`, owns the original sixteen paths
in `docs/governance/preflights/issue-431.json` plus the two exact Issue #427
compatibility paths approved by OWNER comment `5301054923`, and permits at most
4,000 aggregate additions plus deletions. Commit `7a5594357c24ac864c850a2e1cb92f9cd8acb940`
is the preflight-only first commit. The following test/fixture-only commit
`b7f122f704dc2168c64202c090e3e11164c67e80` records genuine RED route failures.
After the frozen reviews exposed successor-compatibility defects, OWNER comment
`5301231033` authorized one final bounded correction wave. Test-only commit
`5bfcb0017ecce6646aa9a840ce3c111351151e44` reproduces those defects before the
corresponding GREEN implementation.

`scripts/quality/issue431_authority_core.py` enforces strict canonical JSON,
three closed V1 schemas, immutable hash-linked lineage, exhaustive legal and
illegal lifecycle grids, exact actor/guard/effect/recovery rows, fixture-only
boundaries, AK-001 false-authority refusal, and exact route/history/budget
constraints. The Stage 8 gate invokes it on the Child A branch and after merge.
The final correction pins the merged #427 head only for descendants containing
the exact #427 merge; rewritten or pre-merge histories remain rejected.

Required commands are the approved Issue #431 command matrix: focused Child A
tests; full Stage 8 tests; guardrails; exact-base policy-only quality and Stage
8 quality; normal quality; CI; security; dependency audit; container scan;
secrets scan; eval; Ruff; mypy; strict JSON/canonicalization/mutation checks;
diff, path, charge, history, shallow/replace/merge and PR-template checks.
`make phase1-closure-quality` is not the Child A gate and must not be reported
as passed. This classification is specific to the OWNER-approved Child A route
and is not inherited from Issue #427.

A green gate means documentation-quality structural enforcement only. It does
not create an accepted decision, current manifest, active route, runtime
service, provider call, credential use, egress, spend, media, deployment,
publication, release, SLA, commercial-readiness, or production claim.

## Issue #434 Child B authority-evidence and trust gate

Child A Issue `#431` / PR `#433` completed at merge `87b8504` with 18 paths and
4,107/4,128 charged lines. Issue `#434` is the current nonactivating Child B
route. Its focused verifier closes envelope, root, producer-key, pin, explicit
time, freshness, reconstruction, replay, taxonomy and historical/current trust
boundaries with activation `NONE` and `NO_AUTHORITY_EFFECT`.

The Stage 8 wrapper registers the exact governed branch scope and invokes the
Child B verifier only as `uv run python
scripts/quality/issue434_authority_evidence_trust.py`; system Python never
imports its dev-only `cryptography==50.0.0` dependency. Missing `uv`, a missing
frozen environment, or a nonzero verifier exit fails closed. The required local
and hosted commands are those frozen in Issue `#434`; green execution creates
no trust root, signer, authority, runtime, release, or production claim.

Issue `#432` remains unmerged source authority outside this gate. Child C is
next unless parent `#426` is separately amended after Child B closeout.

## Issue #452 Cut 1 presenter-contract gate

On exact branch `docs/cut1-acceptance-provider-contract-452`, the quality
dispatcher first runs the Stage 8 route checker, then the isolated
`tests/unit/test_cut1_presenter_contract.py` suite with plugin autoload disabled.
C2 intentionally records exact `CUT1.NOT_IMPLEMENTED` RED failures. After an
independently reviewed C3 freeze, C4 may implement only the marked validator
region. The final gate requires zero findings plus route, focused, mutation,
Ruff, strict mypy, policy-only/full quality and regression evidence. Green
governance checks authorize no provider call, media, spend or release.

## Issue #456 Cut 1 presenter live-binding v2 gate

Issue #456 preserves the Issue #452 v1 freeze byte-for-byte while moving
current-worktree integrity to the five immutable contract-owned inputs recorded
in `cut1-presenter-live-binding-v2.json`. The v2 bytes are independently pinned;
malformed, duplicate, unknown, missing, oversized, non-regular, symlinked, or
tampered bindings and inputs fail with generic `CUT1.BUNDLE.PROTOCOL`. Mutable
ledger, prose, ADR, preflight, route, validator-copy, and test evolution is not
a live bundle-integrity failure.

The Phase 1 order is publication boundary, Cut 1 live binding, then preserved
contracts. On the exact Issue #456 branch, fixed-base preflight validation and
hard-coded twelve-path equality replace only the frozen legacy changed-path
list; all legacy parity, branch, required-file, and preserved checks remain.
All other branches retain the frozen behavior. Required evidence is:

```text
python3 -m pytest -q tests/unit/test_cut1_presenter_live_binding_v2.py tests/unit/test_cut1_presenter_contract.py tests/unit/phase1_closure/test_runner.py
python3 scripts/quality/cut1_presenter_contract.py --kind bundle --root .
make phase1-closure-quality
make quality
uv run pytest -q tests/unit/test_stage8_cut1_routes.py tests/unit/test_issue452_quality_dispatcher.py tests/unit/test_quality_dispatcher.py
uv run pytest -q tests/unit/test_stage8_quality_gate.py::test_issue366_contract_rejects_partial_scope_and_content_mutations
uv run pytest -q tests/unit
uv run ruff check scripts tests
uv run mypy scripts tests
python3 scripts/guardrails_check.py
git diff --check
```

The exact route is capped at 1,200 charged lines, with review at 1,020 and
stop/rescope at 1,080. The validator must remain below 500 physical lines and
32,000 bytes; its dedicated v2 test must remain below 300 physical lines and
32,000 bytes. Green execution creates no product, provider, media, spend,
deployment, release, production, or acceptance authority.
Direct `make stage8-quality` is not this phase-closure branch's route and is
expected to reject its branch identity; the listed Stage 8 unit regressions are
the applicable inherited route evidence.
The OWNER corrective amendment adds only the inherited Stage 8 test as path 12.
Its subprocess assertion replaces the historical branch-specific receipt with
a branch-canonical complete-tuple receipt: only the current branch token is
normalized before hashing, canonical success and branch rejection are pinned,
and independent stdout/stderr mutations are rejected. The Issue #434 verifier,
Stage 8 checker, workflows, and all v1/v2 identities remain unchanged.

## Issue #459 Lane A Cut 1 T01/T02 entry and T04 controller gate

Exact branch `lane-a-cut1-459-controlled-presenter` preserves original base
`ab97b6eecba6db9c66c37d19b29257c7398f3ab7`, frozen T04 head `570239ef`,
reviewed prerequisite main `285458f2`, and exact transition merge `b569e0b`.
The route validates both original and active path snapshots, exact merge
parents/ancestry, every per-path line cap, the 4,300 aggregate cap, eight byte
caps, and preflight/path equality. Active charges start at reviewed prerequisite
main, so accepted Issue `#460` files are neither owned nor double-charged.
Hosted checkpoint comments `5461065184` and `5461070398` expand only the
active snapshot to 24 paths: an exact fourth immutable-SHA Gitleaks fingerprint
plus its checker/test, and pinned push-scope selection plus its test. The frozen
snapshot stays 19 paths; the real-secret canary and all other branch/PR scope
behavior remain blocking and unchanged.

T04 additionally freezes a 2,000-line incremental implementation budget across
the canonical backend evaluator, its focused test, and the quality adapter.
Issue comment `5452170084` adds ADR `0068` under 260 lines/32,000 bytes to
satisfy the unchanged architecture guardrail inside the cumulative route.
The adapter re-exports the backend implementation. The evaluator is pure,
deterministic, single-finding, and forbidden from network, credentials,
environment lookup, providers, spend, retry, rendering, or writes.

`NARRATWIN_POLICY_ONLY=1 make quality` must pass the route. Full `make quality`
must run the frozen 136-case oracle plus the focused T04 side-effect and media-
authenticity tests. During RED, only typed `CUT1.ENTRY.NOT_IMPLEMENTED` behavior
is accepted; after implementation, all assertions must be GREEN. Focused evidence:

```text
uv run pytest -q tests/unit/test_stage8_cut1_routes.py tests/unit/test_issue459_quality_dispatcher.py
uv run pytest -q tests/unit/test_cut1_controlled_presenter_red.py tests/unit/test_cut1_controlled_presenter.py
NARRATWIN_POLICY_ONLY=1 make quality
make quality
```

This gate validates synthetic blocked evidence; an empty finding set is not Cut
1 acceptance. Audio remains with Issue
`#368` pending reviewed handoff; human-study and provider activation remain
with `#432` and `#449`; Raj/Myra derivatives and presenter-specific grounding
must satisfy the recorded stops before T03/T05/T06. Mock/stub/HTML/JSON and
`supportsRealVideo=false` results can never serve as Cut 1 evidence.

## Issue #459 T03 presenter-derivative readiness gate

Exact branch `stage8-459-t03-presenter-derivatives` is pinned to accepted main
`4ef3a8ba70cbf97b7704f5f589b0887f840081cb` and OWNER checkpoint
`5463568867`, with Myra attempt-2 correction checkpoint `5464690216`. Its exact
seventeen-path route allows 2,400 charged text lines and
two regular non-symlink WebPs, each strictly below 500,000 bytes. Missing or
extra paths, wrong base/branch point, unavailable snapshots, authority/preflight
drift, deletion/rename/copy drift, budget overrun, and binary boundary violations
fail closed.

The focused gate proves original immutability, exact derivative hashes and
dimensions, WebP decoding/container safety, Raj/Myra presenter binding, explicit
Meera source-only readiness, T04/source-registry digest preservation, and exact
privacy/provenance/deletion references. It also binds Myra's maximum second
attempt and owner-superseded attempt-1 disposition while Raj remains attempt 1:

```text
uv run pytest -q tests/unit/test_cut1_presenter_derivatives.py tests/unit/test_cut1_presenter_registry.py tests/unit/test_cut1_controlled_presenter.py tests/unit/test_cut1_controlled_presenter_red.py
uv run pytest -q tests/unit/test_stage8_cut1_routes.py
NARRATWIN_POLICY_ONLY=1 make quality
make quality
bash scripts/ci/backend-test.sh
```

Green T03 evidence activates only controlled-local Raj/Myra still-image
derivative readiness. It activates no provider/runtime, audio, video, UI,
publication, human study, release, production, or Cut 1 acceptance claim.

## Issue #459 T05A grounded-narration handoff gate

Exact branch `stage8-459-t05a-grounded-narration-handoff` is pinned to merged
T03 main `0d70fa8e27ad4760249d75e7782ac06b5d68b173` and checkpoint
`5465050919` with exact body SHA-256
`ab0d0b486bf77eac59db2b83c0d33bd0ae61bb52ed26b37b4d7a8402b2ec31c8`.
Its exact twelve-path route permits 2,200 charged text lines. Wrong base,
branch-point drift, missing or extra paths, authority/preflight drift,
deletion/rename/copy drift, and aggregate or per-path overrun fail closed.

The focused gate proves that each complete canonical eighteen-claim sequence
matches exactly one governed presenter, all three presenter runs and narration
receipts persist and replay independently, and mixed or cross-presenter
substitution fails:

```text
uv run pytest -q tests/unit/test_cut1_atomic_grounding.py tests/unit/test_cut1_narration.py
uv run pytest -q tests/unit/test_stage8_cut1_routes.py
NARRATWIN_POLICY_ONLY=1 make quality
make quality
bash scripts/ci/backend-test.sh
```

This gate produces provider-neutral narration input authority only. It does not
produce or validate audio, captions, video, providers, credentials, egress,
spend, publication, release, production readiness, or Cut 1 acceptance.
Issue `#368` retains the real audio/caption handoff.

## Issue #459 T05B offline audio/caption authority gate

Exact branch `stage8-459-t05b-audio-caption-authority` is pinned to merged
T05A main `bfb8487760dc6aeef8b05af95e0ecd40d0076f3a` and checkpoint
`5466871459` with exact body SHA-256
`f53e919836ea5edd58620d789497d945f317c354d0b5405a88d49e570c778b28`.
Correction checkpoint `5466962967`, body SHA-256
`4d4cd204972abfa70b687f416813937b41329c930cf1676706ce278798579032`,
expands the exact route to nineteen paths under the unchanged 3,600-line cap
for three immutable public CPython signing-key false positives. Only exact
fingerprints may be ignored; public-key blob/line/context provenance,
missing/extra/wildcard drift, and the representative real-secret canary fail
closed before the unchanged full-history scan. Wrong base,
branch-point drift, missing or extra paths, authority/preflight drift,
deletion/rename/copy drift, and aggregate or per-path overrun fail closed.
Checkpoint `5467038670`, body SHA-256
`41e41763e52382b3eeeea6f265dd42e2078293a3325e5df6c62f9e01d5bbc340`,
corrects one truncated commit token and requires all fingerprint commits to be
exactly 40 lowercase hexadecimal characters; it changes no scope or budget.
Independent-review correction checkpoint `5467125295`, body SHA-256
`6f05484d33e69ede373841fbb57755ae3139e5c1e06280252b8bc1558d42b263`,
changes no path or budget. It removes synthesis capability from admission,
derives configuration identity, requires a trusted external request/final-
authority commitment manifest, binds exact record completeness/order, checks
live receipt authority before persistence and retrieval, and atomically
replaces a superseded authority set. Valid rehash, deletion, reorder, stale-
during-admission, stale retrieval, manifest drift, and detached-checksum
mutations fail closed.

The focused gate proves typed materialized results, current receipt/derived-
configuration/immutable-manifest binding, independent WAV/SRT validation,
atomic full-set persistence/replacement, replay rejection, and fail-closed
restore/retrieval across all three presenters:

```text
uv run pytest -q tests/unit/test_cut1_audio.py tests/unit/test_stage6_tts_provider.py
uv run pytest -q tests/unit/test_stage8_cut1_routes.py
NARRATWIN_POLICY_ONLY=1 make quality
uv run ruff check backend
uv run mypy backend
make quality
bash scripts/ci/dependency-security.sh
bash scripts/ci/backend-test.sh
```

Test WAV/SRT bytes are mutation stimuli only. This gate does not prove
intelligibility, voice identity, real provider output, listening acceptance,
T05 completion, T06 readiness, Cut 1 acceptance, release, or production.
