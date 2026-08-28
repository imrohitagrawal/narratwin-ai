# Tasks: Lane A Cut 1 Presenter Path

Status: planned only; `$speckit-implement` blocked
Future Lane A Cut 1 issue: TBD after Issue #16 closes

## Mapping rule

Issue #16 owns only constitution/specification/planning/review. After it merges
and closes, the primary orchestrator creates one separately authorized Lane A
Cut 1 implementation issue and copies every task ID, dependency, acceptance,
verification class and stop condition below into its body. Until then, no
concrete future issue number or branch exists. `I16.ISSUE.SEQUENCING`.

| Task ID | Summary | Dependencies | GitHub issue mapping | Acceptance | Verification | Owned paths |
|---|---|---|---|---|---|---|
| LA-C1-T01 | Freeze future authority, source/script/presenter inputs, provenance, route, budgets and stops | None | POST_MERGE_ISSUE_REQUIRED | Exact base, six cells, paths, budgets, metrics, invariants and human-only decisions accepted before code. | Preflight, source/metric digests, matrix review, committed RED. | Future issue/preflight/tests. |
| LA-C1-T02 | Commit RED corpus, schemas, positive/negative/mutation cases and cell independence | LA-C1-T01 | POST_MERGE_ISSUE_REQUIRED | Every canonical requirement/metric has discriminating old-behavior evidence; pooled/missing/stale/substituted false passes fail. | Frozen corpus/schema tests, mutation receipts, RED review. | Future tests/evals/governance. |
| LA-C1-T03 | Produce/register authorized provenance-bound derivatives without overwriting originals | LA-C1-T01, LA-C1-T02 | POST_MERGE_ISSUE_REQUIRED | Derivatives have authority, provenance, checksum, consent/privacy/deletion posture; unauthorized identity/media rejects. | Asset/provenance manifests, decode/integrity mutations, human permitted-use review. | Future governed assets/registry/provenance. |
| LA-C1-T04 | Build provider-neutral controlled executor and credential/egress/spend controls | LA-C1-T01, LA-C1-T02 | POST_MERGE_ISSUE_REQUIRED | Local/key-free deterministic execution; credentials, egress, spend, unsafe output and activation fail closed. | Fake-boundary, zero-egress/spend, timeout/retry/idempotency/security tests. | Future executor/provider-neutral boundary/tests. |
| LA-C1-T05 | Bind narration, voice, captions, grounding and immutable lineage | LA-C1-T02, LA-C1-T03, LA-C1-T04 | POST_MERGE_ISSUE_REQUIRED | Audio/caption/script/source/evaluation/presenter/config bind exactly; unsupported/stale/substituted/partial state cannot pass. | Lineage, grounding/abstention, caption/audio, atomic-failure mutations. | Future narration/media/evaluation binding/tests. |
| LA-C1-T06 | Produce independently reviewable landscape/portrait presenter artifacts | LA-C1-T03, LA-C1-T04, LA-C1-T05 | POST_MERGE_ISSUE_REQUIRED | Six cells are separately present, valid and measurable; no aggregate hides failed cell/severe defect. | Artifact/schema/integrity tests and per-cell canonical metric reports. | Future artifact/render paths/tests. |
| LA-C1-T07 | Integrate controlled reviewer path and cross-cutting evidence | LA-C1-T05, LA-C1-T06 | POST_MERGE_ISSUE_REQUIRED | Reviewer inspects evidence/captions/errors/limits/provider posture through secure, private, accessible, reproducible bounded local behavior. | Component/browser, security/privacy, accessibility, performance, observability, two-run parity. | Future UI/reviewer path/tests/docs. |
| LA-C1-T08 | Run exact-artifact acceptance, human review, limitations and closeout | LA-C1-T07 | POST_MERGE_ISSUE_REQUIRED | Tests, docs, security notes, observability metadata, known limitations, reviewer pass, separately authorized study, hosted checks and approval complete. | Full/negative/security/governance, exact-artifact protocol, PR reconciliation, hosted CI/reviews. | Future docs/traceability/review/PR evidence. |

## Checkpoints and stops

- After T01: no code until RED and contract review pass.
- After T03: provenance/security/privacy approval precedes consumption.
- After T06: every cell's artifact/lineage and mutations pass before UI.
- After T08: merge eligibility requires hosted checks and independent approval.

Stop for authority/base/path/budget/source drift, new dependency/provider,
credential/egress/spend/deployment/publication/release action, consent/
provenance/legal uncertainty, disclosure, unsupported-claim false acceptance,
missing cell/rollback evidence, unresolved reproduced `CRITICAL_BLOCKER` or
`REQUIRED_CONTRACT`, or two new substantive post-review blocker classes without
contract rewrite.

## Reviewer pass

Confirm dependency order, canonical metric binding, task/evidence coverage,
security/privacy abuse cases, provenance/consent/deletion, observability without
sensitive data, accessibility/performance, known limitations and post-merge
sequencing. `ADVISORY_DEBT` never silently expands the future issue.
