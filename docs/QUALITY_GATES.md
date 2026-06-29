# Quality Gates

NarraTwin AI quality gates are executable stage contracts. A gate that is not implemented must fail loudly when called directly.

## Stable Command

Use one top-level command:

```bash
make quality
```

During Stage 1, `make quality` runs only Stage 1 documentation and governance checks
by delegating to `scripts/quality/check_quality_stage.py`. It must not run backend,
frontend, Docker, database, RAG, avatar, or provider checks because those product
areas are not allowed before Stage 4.

## Required Make Targets

The `Makefile` must expose:

| Target | Current Stage 1 behavior |
|---|---|
| `make quality` | Runs checks for `.stage/current`; currently Stage 2 |
| `make stage0-quality` | Runs executable Stage 0 documentation and guardrail checks |
| `make stage1-quality` | Runs executable Stage 1 product and PRD documentation checks |
| `make stage2-quality` | Runs executable Stage 2 architecture, security, AI safety, and portability checks |
| `make stage3-quality` | Fails loudly until Stage 3 quality is implemented |
| `make stage4-quality` | Fails loudly until Stage 4 quality is implemented |
| `make stage5-quality` | Fails loudly until Stage 5 quality is implemented |
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

Stage 2 validates:

- `.stage/current` contains `2`
- current branch name matches `stage2-*` before merge, or is `main` after merge
- changed files stay within the documented Stage 2 allowlist
- required Stage 2 architecture, ADR, threat model, security/privacy, AI
  safety/evaluation, portability, API, data model, observability, status, and
  traceability docs exist
- Stage 2 docs include the remediation locks for synthetic local authorization,
  approved-knowledge state, mandatory secret screening before provider egress,
  hard unsupported-claim failure policy, claim-level context references, resource
  budgets, queue/backpressure, provider adapter contracts, event schema, retention,
  tombstones, and API idempotency
- legacy Stage 1 ADRs with duplicate numbers are marked superseded by the Stage 2
  ADR canon
- mock/local provider defaults include LLM, embedding, evaluation, avatar, TTS, STT,
  and storage defaults
- Stage 2 changes introduce no backend, frontend, RAG, provider, avatar, Docker,
  database, dependency manifest, lockfile, or runtime product code
- Stage 2 Python quality scripts remain stdlib-only and compile
- working-tree diffs have no whitespace errors
- obvious committed-secret patterns are absent from tracked text files

### Stage 3: Repo Foundation And CI/CD Quality Gates

Gate must validate local development docs, CI workflows, CI wrapper scripts, dependency/security scan path, branch protection recommendations, and mock/local provider defaults. Product feature code remains blocked.

### Stage 4: Project Upload To Grounded Script Generation

Gate must validate the first vertical slice: project creation, markdown upload, ingest/chunk/store, retrieval, grounded script generation, unsupported-claim evaluation, storage, UI display, tests, docs, security notes, observability metadata, limitations, and reviewer pass.

### Stage 5: Evaluations, Guardrails, Observability

Gate must validate prompt-injection tests, unsupported-claim evals, failure blocking, trace/run metadata, source chunk or context citations, and observability events.

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
