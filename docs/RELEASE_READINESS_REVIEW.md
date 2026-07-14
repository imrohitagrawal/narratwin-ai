# Release Readiness Review

Issue baseline: Stage 8 `#13`, Final Review `#6`, Phase 1 Closure issues `#35`
through `#44`

Review date: 2026-07-01

## Decision

No-Go for production release, multi-worker deployment, external paid/provider-backed
generation, real video export, and public synthetic-media distribution.

Conditional local mock-provider portfolio/demo review remains distinct from
production go-live. With `#35`, `#36`, `#37`, `#40`, `#41`, and `#42` closed,
`#38` resolved with live branch-protection evidence, and `#39` adding optional
local file-backed restart recovery plus `/api/v1/ops/status`, local/mock
single-process demo readiness can be reviewed through the local gates and
documented limitations. Production release remains No-Go. No release tag has
been created.

`docs/LAUNCH_LEVELS.md` is the canonical launch-level boundary. AWS is not
required for the controlled local mock demo. A hosted internal synthetic demo
requires a separate environment review and does not inherit local-demo approval.
External/invite-only soft launch remains No-Go and is production-adjacent even
when audience size is small or hosting is free. Production-like durability
validation is also No-Go until its separate environment and evidence gates pass;
it is not a user launch.

## Current Baseline

- Stage 8 merged to `main` through PR `#33` at merge commit `fb40113`.
- Final Review merged to `main` through PR `#45` at merge commit
  `5a294c72d2b4b8cbbc0339f7bcb3f17089bddece`.
- Final Review issue `#6` is closed.
- Final Review artifacts are the baseline for the current No-Go posture, with
  issue-level dispositions superseded by reviewed Phase 1 Closure evidence:
  `docs/reviews/FINAL_REVIEW.md`, `docs/reviews/RISK_REGISTER.md`,
  `docs/reviews/DEFECT_BACKLOG.md`, and `docs/reviews/GO_NO_GO.md`.
- Phase 1 Closure is tracked through issues `#35` through `#44` and
  `docs/reviews/PHASE_1_CLOSURE_REPORT.md`.
- PR `#46` merged Phase 1 Closure governance/traceability and closed `#35`,
  `#36`, `#40`, and `#41`.
- PR `#47` merged trusted local principal contract remediation and closed `#37`.
- PR `#50` merged Stage 7 checksum-binding remediation and closed `#42`.
- Live GitHub `main` branch protection was enabled and verified on 2026-07-02
  for issue `#38` and recorded through PR `#53`.

## Stage 8 Evidence

Stage 8 added release-readiness hardening evidence but did not approve production.

| Budget | Evidence |
|---|---|
| health endpoint < 200 ms local | `tests/api/test_stage8_hardening_api.py::test_health_reports_stage8_with_local_latency_budget` |
| script generation mocked path < 2 sec | `tests/api/test_stage8_hardening_api.py::test_mocked_script_generation_path_stays_under_two_seconds` |
| upload limit enforced | Fail-closed `Content-Length` checks, ASGI body-byte counting, upload content-size limits, and Stage 8 API tests |
| no critical/high dependency vulnerabilities | `scripts/ci/dependency-security.sh` |
| no critical/high container vulnerabilities | `scripts/ci/docker-image-scan.sh` using Trivy, Grype, pinned Dockerized Trivy, or Docker Scout |
| Locust and Lighthouse budgets | `scripts/ci/performance-smoke.sh`, `scripts/ci/frontend-lighthouse.sh`, and PR CI status `stage8 / performance lighthouse` |
| eval/security gates | `make stage8-quality` plus PR CI policy, security, Docker scan, and Stage 8 budget statuses |

Latest Stage 8 local evidence recorded before PR `#33` merged:

- `make quality` passed on `stage8-performance-security-release-readiness`.
- Locust health smoke: 175 requests, 0 failures, p95 7 ms.
- Lighthouse: performance 1.00, accessibility 1.00, best-practices 0.96, SEO
  1.00, LCP 1057 ms, CLS 0, TBT 0 ms, 10 network requests.
- Docker scan SARIF: backend 0 results, frontend 0 results.
- Dependency audit: no critical/high Python or frontend dependency findings;
  moderate Lighthouse dev-tool findings remain below the Stage 8 blocking
  threshold.

## Final Review Outcome

Final Review produced a No-Go decision and opened follow-up issues `#35` through
`#44`. Required Phase 1 closure blockers are recorded in
`docs/reviews/GO_NO_GO.md` and mapped in
`docs/reviews/PHASE_1_CLOSURE_REPORT.md`.

P0/P1 closure items must complete before Phase 2. Current reconciliation:

- `#35` Governance and release docs stale after Stage 8 merge: closed through
  merged PR `#46`.
- `#36` Final Review gate and branch-policy evidence: closed through merged PR
  `#46`; live repository branch-protection proof is now recorded under `#38`.
- `#37` Local principal contract mismatch: closed through merged PR `#47` with
  trusted local/dev/test-only principal simulation evidence.
- `#38` Branch protection/ruleset evidence: live GitHub `main` branch
  protection is enabled and requires the documented CI contexts.
- `#39` Production durability and monitoring blockers: partially remediated for
  local restart recovery and local ops posture visibility; still release-blocking
  for production go-live.
- `#40` Canonical RTM stale: closed through merged PR `#46`.
- `#41` Portfolio local-demo durability disclosure: closed through merged PR
  `#46`.
- `#42` Stage 7 source-evaluation checksum binding: closed through merged PR
  `#50`.

P2 follow-ups `#43` and `#44` remain deferred unless they block Phase 1
correctness.

## Current Release Blockers

- Optional file-backed JSON snapshots now cover local restart recovery for Stage
  4 project/document/run/RAG state, Stage 6 multilingual idempotency replay, and
  Stage 7 avatar render/idempotency/artifact metadata. This is single-node only;
  multi-worker production remains blocked until ACID/CAS metadata, locking,
  migrations, backup/restore, and production idempotency semantics are
  implemented and reviewed.
- `/api/v1/ops/status` reports local durable-state enablement, bounded record
  counts, and monitoring flags. Production dashboards, alert routes, first-hour
  watch procedure, and rollback communication channels are still not defined for
  a real deployment.
- External providers remain disabled unless provider-specific evals, egress
  controls, and red-team cases are implemented.
- Real video export and public synthetic-media distribution remain blocked until
  renderer/provider license posture, persistent consent, provenance, and any
  source-run based avatar export decision are implemented and reviewed.
- Issues `#48` and `#49` are classified as pre-production/P2 hardening: `#48`
  blocks production auth/durable-storage authorization claims, and `#49` blocks
  local-demo durability, multi-worker, or production-readiness claims. They do
  not block local/mock Phase 1 demo review while production remains No-Go.

## Conditional Local Demo Conditions

The local demo can be reviewed only when:

- the activity still satisfies the `Local mock demo` row in
  `docs/LAUNCH_LEVELS.md`; hosted or external access requires a separate decision

- mock/local providers remain the only active providers
- no real provider keys are required
- no real video, cloned face, cloned voice, or public synthetic-media claim is made
- demo docs disclose single-process/single-node local state: process-local by
  default, optional JSON restart snapshots only when configured, and no
  multi-worker or production durability
- `#39` remains explicitly represented as a production/release blocker unless
  it is closed or downgraded with evidence
- local quality, eval, security, and CI gates pass

## Downgrade Evidence Rule

A P0/P1 issue may be downgraded only by the active closure reviewer through a
reviewed PR linked to the GitHub issue. The PR must record the issue, previous
priority, new priority, evidence, reviewer/date, and release impact in
`docs/reviews/PHASE_1_CLOSURE_REPORT.md`. If the downgrade changes the release
posture, the same PR must update `docs/reviews/GO_NO_GO.md`; otherwise the issue
remains release-blocking.

Static governance artifacts do not by themselves close implementation blockers.
Issues `#37` and `#42` now have separate executable evidence through merged PRs
`#47` and `#50`. Issue `#38` now has live GitHub repository-settings evidence
plus the required `policy-gates` branch-protection context verifier added in PR
`#53`.
Issue `#39` now has implementation evidence for local file-backed restart
recovery and local operational status visibility, but still requires production
database/locking/backup and monitoring evidence or a reviewed No-Go exception
before production release can be treated as Phase 1 closure-ready. The
unchanged Final Review artifacts preserve the original July 1 reviewer baseline;
this Phase 1 Closure review is the current issue-disposition source for `#38`.

## Issue #38 Evidence

GitHub API verification on 2026-07-02 recorded `main` branch protection as
enabled. The classic branch-protection endpoint
`repos/imrohitagrawal/narratwin-ai/branches/main/protection` returns:

- `required_status_checks.strict: true`
- required contexts: `policy-gates`, `quality / secrets`,
  `quality / markdown`, `lint / typecheck / unit / api`,
  `frontend tests / playwright smoke`, `ci / docker build`,
  `secret scan / bandit / audit / semgrep`, `security / docker build`,
  `eval smoke`, and `stage8 / performance lighthouse`
- GitHub Actions app binding for each required check: `app_id: 15368`
- `required_pull_request_reviews.required_approving_review_count: 1`
- `required_pull_request_reviews.dismiss_stale_reviews: true`
- `required_pull_request_reviews.require_last_push_approval: true`
- `enforce_admins.enabled: true`
- `allow_force_pushes.enabled: false`
- `allow_deletions.enabled: false`
- `required_conversation_resolution.enabled: true`

The only documented repository-settings item not configured as a classic branch
protection restriction is direct pusher allowlisting. GitHub rejected that
setting for this user-owned repository with `Only organization repositories can
have users and team restrictions`; the live protection response keeps
`restrictions: null`. The accepted enforcement path for this repository is
required PR review, strict required checks, administrator enforcement, blocked
force pushes, blocked deletions, and required conversation resolution.

The branch summary endpoint
`repos/imrohitagrawal/narratwin-ai/branches/main` returns `protected: true`,
`protection.enabled: true`, and `required_status_checks.enforcement_level:
everyone`.

PR `#53` adds `scripts/ci/verify_branch_protection.py` to the required
`policy-gates` workflow. That verifier queries the same branch summary endpoint
on every pull request to `main` and every non-main branch push, and fails if the
endpoint no longer reports `protected: true`, exact required CI contexts,
`enforcement_level: everyone`, or GitHub Actions app bindings for those
contexts. Admin-only settings such as strictness, required review count,
administrator enforcement, force-push/deletion blocking, and conversation
resolution remain recorded from the classic branch-protection endpoint evidence
above.

## Tagging Policy

Create a release tag only after every Phase 1 P0/P1 gate passes locally and in CI,
the PRs are reviewed and merged, and `docs/reviews/GO_NO_GO.md` is updated from
No-Go to the reviewed target posture. No tag is permitted from the current state.
