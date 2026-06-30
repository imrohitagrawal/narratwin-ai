# Quality Gates

NarraTwin AI quality gates are executable stage contracts. A gate that is not implemented must fail loudly when called directly.

## Stable Command

Use one top-level command:

```bash
make quality
```

During the current stage, `make quality` runs only the active stage checks
by delegating to `scripts/quality/check_quality_stage.py`. Stage 5 now gates
runtime evaluation, prompt-injection guardrails, file-abuse tests, telemetry,
and observability surfaces for the approved first-slice path. Product behavior
outside the approved slice remains blocked.

## Required Make Targets

The `Makefile` must expose:

| Target | Current behavior |
|---|---|
| `make quality` | Runs checks for `.stage/current`; currently Stage 5 |
| `make stage0-quality` | Runs executable Stage 0 documentation and guardrail checks |
| `make stage1-quality` | Runs executable Stage 1 product and PRD documentation checks |
| `make stage2-quality` | Runs executable Stage 2 architecture, security, AI safety, and portability checks |
| `make stage3-quality` | Runs executable Stage 3 repo foundation and CI/CD checks |
| `make stage4-quality` | Runs executable Stage 4 first-slice checks |
| `make stage5-quality` | Runs executable Stage 5 eval/guardrail/observability checks |
| `make stage6-quality` | Fails loudly until Stage 6 quality is implemented |
| `make stage7-quality` | Fails loudly until Stage 7 quality is implemented |
| `make stage8-quality` | Fails loudly until Stage 8 quality is implemented |
| `make final-review-quality` | Fails loudly until Final Review quality is implemented |

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

Gate must validate translation/localization quality, subtitle export, mock/local voice adapter behavior, no required paid provider, accessibility notes, and docs.

### Stage 7: Avatar Rendering Adapter And Export

Gate must validate mock/local avatar rendering, export artifacts, provider adapter contracts, public-use license checks, AI disclosure, consent controls for any cloned identity feature, and docs.

### Stage 8: Performance, Security Hardening, Release Readiness

Gate must validate performance budgets, security hardening, dependency/security scan results, release-readiness evidence, known limitations, rollback notes, and Stage 8 documentation.

### Final Review: Independent Review

Gate must validate independent review evidence across all stages, unresolved risk disposition, quality evidence, security/eval status, release readiness, and no new feature implementation during review.

## CI Relationship

GitHub Actions workflows remain the remote enforcement layer. Local stage targets are the developer and agent contract before pushing.

The CI layer must continue to enforce:

- `make quality` for the current stage
- stage-aware backend contracts so Stage 0 governance scripts do not trigger backend implementation gates
- issue-linked PRs
- least-privilege workflow permissions
- no committed secrets
- mock/local provider defaults
- eval failures block merge when eval reports exist
- critical or high security findings block merge when security reports exist

Direct pushes to `main` remain a repository-settings requirement enforced through branch protection or rulesets rather than the stage-quality workflow itself.
