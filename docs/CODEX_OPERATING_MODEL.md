# Codex Operating Model

NarraTwin AI is built through issue-linked, PR-reviewed stages. Stage 0 in this branch is limited to operating model, skill lock, and executable quality-gate setup.

## Master Rule

No product implementation may start until Stage 0 and Stage 1 gates pass. Stage 0 must not add backend, frontend, RAG, avatar, provider, Docker, database, or runtime product code.

Product implementation includes:

- backend APIs or services
- frontend application code
- database schemas or migrations
- RAG ingestion, chunking, retrieval, embeddings, or vector stores
- LLM, translation, TTS, STT, avatar, subtitle, storage, evaluation, or observability provider adapters
- Docker/runtime deployment scaffolding
- product tests for not-yet-approved product code

Allowed in Stage 0:

- governance docs
- canonical delivery status tracking
- CI enforcement for Stage 0 quality gates
- stage and issue plans
- skill lock and skill execution plan
- third-party notice updates for newly governed tools and skills
- executable Stage 0 quality checks
- README and agent operating instructions

## Approved Build Stages

| Stage | Name | Required outcome | Product implementation status |
|---|---|---|---|
| Stage 0 | Codex operating model and skill lock | Operating model, skill lock, issue plan, Stage 0 quality gate, current stage marker | Blocked |
| Stage 1 | Product strategy and PRD v1.0 | Product strategy, PRD v1.0, PRD red-team review, metrics, roadmap, traceability | Blocked |
| Stage 2 | Architecture, security, AI safety | Architecture, ADRs, security/privacy model, AI safety and evaluation plan | Blocked |
| Stage 3 | Repo foundation and CI/CD quality gates | Repo foundation, local development docs, CI/CD wrappers, executable stage quality gates | No product feature code |
| Stage 4 | Project upload to grounded script generation | First vertical slice from project creation through grounded script display | Allowed for Slice 1 only |
| Stage 5 | Evaluations, guardrails, observability | Unsupported-claim evals, prompt-injection guardrails, trace/run metadata, observability | Allowed for slice-scoped quality features |
| Stage 6 | Multilingual scripts, subtitles, voice adapter | Translation/localization, subtitle export, mock/local voice adapter boundary | Allowed with mock/local defaults |
| Stage 7 | Avatar rendering adapter and export | Mock/local avatar rendering adapter and export artifacts | Allowed with mock/local defaults |
| Stage 8 | Performance, security hardening, release readiness | Performance review, security hardening, release-readiness evidence | Hardening only |
| Final Review | Independent review | Independent review of stages, risks, quality evidence, and release readiness | No new feature implementation |

## Stage Gate Rules

- Every stage starts from a GitHub issue.
- Every stage uses a dedicated branch.
- Every stage lands through a pull request linked with the issue.
- Every PR must pass local stage quality and CI.
- Stage 8 and Final Review must be documented before any release claim.
- Eval failures block merge once evaluation exists.
- Critical or high security findings block merge once security reports exist.
- Paid providers must never be required for local/dev/test.
- Future provider integrations must include mock/local adapters.

## Merge Closeout Evidence Policy

Post-merge facts are real evidence, but they do not automatically justify a
new repository change. The PR that completes issue A must update
`docs/STATUS.md` in that same PR to describe the intended post-merge target
state: issue A is satisfied by that PR once merged, the next approved work item
is issue B, and no forbidden scope is authorized. After the approved PR merges,
the closeout owner must record the merge SHA, post-merge workflow result,
branch cleanup, and final GitHub issue disposition in the merged PR and linked
issue comments. That GitHub evidence is the durable closeout record for
routine merge facts.

Do not open a successor issue or PR whose only purpose is to update
`docs/STATUS.md` with the previous PR's final merge SHA, post-merge workflow
URL, issue closure, or branch deletion. That pattern creates an infinite
governance loop because the successor PR then creates its own future merge facts.

Update `docs/STATUS.md` in a repository PR only when at least one of these is
true:

- the substantive PR itself changes repository-tracked stage, issue, PR,
  governance, release, or next-action state, in which case the same PR must
  update `docs/STATUS.md` to its intended post-merge target state;
- the ledger would otherwise point engineers at the wrong active work item or
  authorize the wrong scope;
- a later substantive PR is already open and can bundle the status correction
  without widening product/runtime scope;
- a human explicitly approves a one-time terminal reconciliation because stale
  repository state blocks correct work.

Issue `#223` and PR `#224` are the terminal exception that records the
post-PR-222 state and installs this policy. After PR `#224`, do not create a
new `post-PR-224 status reconciliation` issue or PR. If post-merge facts for
PR `#224` need a durable record, comment them on PR `#224` and issue `#223`;
bundle any future `docs/STATUS.md` cleanup into the next material repository
change.

## Stage 0 Exit Criteria

Stage 0 passes only when:

- all Stage 0 operating docs exist
- `docs/STATUS.md` exists and records the repository-tracked stage ledger, issue and PR references, open gaps, and next approved actions
- `.stage/current` contains `0`
- Stage 0 through Stage 8 plus Final Review are documented
- `make stage0-quality` passes
- `make quality` runs Stage 0 quality only
- future stage quality targets exist and fail loudly until implemented
- no disallowed product/runtime directories or manifests have started outside the Stage 0 allowlist
- operating docs contain no unresolved placeholders
- `docs/SKILL_LOCK.md` records source URL, pin/version status, license status, purpose, active stage, and activation status for each locked source

## Stage 1 Boundary

Do not start Stage 1 in the Stage 0 redo branch. Stage 1 may begin only from its own issue, branch, PR, and quality target after this Stage 0 redo is reviewed.
