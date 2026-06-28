# Quality Gates

NarraTwin AI uses quality gates to keep Codex work scoped, reviewable, and safe.

## Existing GitHub workflow

The repository uses `.github/workflows/quality.yml` as the primary CI workflow.

Current jobs:

- `quality / secrets`
- `quality / markdown`
- `quality / backend-lint`
- `quality / backend-tests`
- `quality / frontend-build`
- `quality / dependency-security`

The workflow intentionally supports an early bootstrap repo:

- If backend/frontend/dependency manifests do not exist, related jobs say the check is not applicable.
- Once code or manifests appear, the workflow requires repo-local wrappers such as `scripts/ci/backend-test.sh`.
- This prevents Codex from adding code without also adding validation commands.

## Secrets gate

`quality / secrets` must use a dedicated secret-scanning tool, not only a handcrafted regex.

Current implementation:

- checks out full history for the secrets job
- runs `gitleaks/gitleaks-action@v3`
- disables automatic PR comments to avoid noisy bot output
- does not require a Gitleaks license for this personal-account repository

A lightweight regex scan may be added later as a supplemental fast check, but it must not replace the dedicated scanner.

## Local gates before every PR

Run the closest applicable local checks before pushing:

```bash
make quality
```

If `make` is not available, run the individual checks listed in this file.

## Documentation-only gate

For docs-only changes:

- no secrets in docs
- no unsupported product claims
- markdown is readable
- changed docs reference the correct source of truth
- skill commands are marked as unverified unless trust review is complete

## Stage gates

### Stage -1: Skill trust review

Required before installing or using external skills:

- `docs/SKILL_TRUST_REVIEW.md` exists
- every skill source has a decision
- unclear license/install behavior is blocked
- `.agents/vendor` is not created by default

### Stage 0: Product and PRD

Required before architecture/code work:

- strategy is specific to NarraTwin AI
- PRD has user journeys, MVP/non-goals, functional requirements, NFRs, metrics, and failure cases
- PRD red-team review challenges scope, safety, cost, and license assumptions
- roadmap is sliced by user-visible outcomes

### Stage 1: Architecture and safety

Required before implementation:

- architecture defines backend, frontend, provider, RAG, evaluation, and storage boundaries
- ADRs define decisions, alternatives, consequences, and test/security impact
- security/privacy controls cover uploads, secrets, prompt injection, consent, and provider risks
- AI evaluation gates are explicit
- third-party notices have no blockers for the planned slice

### Stage 2: Repo validation contracts

Required before product features:

- local development guide exists
- quality-gate guide exists
- PR template exists
- existing `quality.yml` is documented
- future backend/frontend code must add CI wrapper scripts before merge

### Stage 3: Slice 1

Required before merging Slice 1:

- user can create a project
- user can upload markdown/text knowledge
- system chunks/stores/retrieves context
- grounded script generation works through mocks/fakes if needed
- unsupported claims are detected or refused
- output is stored and visible in UI
- happy path and failure/refusal tests pass
- no paid provider key is required
- docs and known limitations are updated

## Required wrapper scripts once code exists

When backend code appears, Codex must add:

```text
scripts/ci/backend-lint.sh
scripts/ci/backend-test.sh
```

When frontend code appears, Codex must add:

```text
scripts/ci/frontend-build.sh
```

When lockfiles or dependency manifests appear, Codex must add:

```text
scripts/ci/dependency-security.sh
```

## Branch protection recommendation

When the workflow has run successfully at least once, protect `main` with required checks:

- `quality / secrets`
- `quality / markdown`
- `quality / backend-lint`
- `quality / backend-tests`
- `quality / frontend-build`
- `quality / dependency-security`

Also require:

- pull request before merge
- conversation resolution
- no force pushes
- latest branch update before merge when practical

## Codex stop rule

Codex must stop and report instead of continuing when:

- a quality gate is missing
- a command fails
- a skill install command is unverified
- a license is unclear
- a generated output can make unsupported project claims
- a provider requires a paid key for the MVP path
