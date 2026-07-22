# Issue 267 C3A-CP7 Preflight

## Objective

C3A-CP7 implements the seventh Checkpoint 3A child implementation checkpoint for public tracker issue `#249` and child issue `#267`: an executable performance probe for the local/mock controlled demo path.

The claim is deliberately narrow: `make checkpoint3-acceptance` dispatches the performance probe as executable runtime API behavior, and that probe evaluates bounded local/mock timings from approved synthetic local data. This work does not complete Checkpoint 3A.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3A-CP7-HARNESS-001 | The Checkpoint 3 acceptance harness implements the `performance` probe through `uv run pytest tests/acceptance/test_checkpoint3_performance.py -q`, with `shell=False`, `timeout=120`, and bounded/redacted failure output. |
| C3A-CP7-PERFORMANCE-001 | The acceptance test creates synthetic local projects, uploads approved synthetic knowledge, ingests/chunks/stores it, generates grounded walkthroughs, and records runtime API-visible timings with explicit thresholds, operation names, run/request IDs, local/mock posture, and pass/fail status. |
| C3A-CP7-BINDING-001 | Performance evidence is bound to runtime nonce, source project/document/ingestion/run/evaluation identity, request header binding, operation timings, and generation trace metadata rather than static or stale evidence. |
| C3A-CP7-REDACTION-001 | The probe and harness assert that raw uploaded content, prompt-injection text, private-looking markers, sensitive tokens, accepted script text, and failure context fields do not appear in bounded public failure output. |
| C3A-CP7-FALSEPASS-001 | Docs/prose/static-snapshot checks, style-only/status-only text, canned success, success-shaped timing dictionaries, missing binding, stale evidence, cross-project replay, and implicit thresholds cannot pass. |
| C3A-CP7-NONGOAL-001 | Real-browser E2E remains planned. |

## Scope

In scope:

- `scripts/quality/check_checkpoint3_acceptance.py`
- `tests/acceptance/test_checkpoint3_performance.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_267_C3A_CP7_PREFLIGHT.md`
- `docs/governance/preflights/issue-267.json`

Out of scope: provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, public distribution, production-readiness claims, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime deployment, new dependencies, secrets, private media, private planning files, and real personal data.

The PR may bundle repository-ledger cleanup for PR `#266` and issue `#265` because this is a substantive child checkpoint, not a standalone status-only follow-up. Issue #249 remains open.

## Source Facts

Accessed date: 2026-07-23.

| Source | Fact used |
| --- | --- |
| https://fastapi.tiangolo.com/tutorial/testing/ | FastAPI supports `TestClient` for ordinary pytest functions and assertions against app behavior. |
| https://fastapi.tiangolo.com/reference/testclient/ | `TestClient` is the local in-process API client used for deterministic acceptance tests. |
| https://docs.python.org/3/library/subprocess.html#subprocess.run | `subprocess.run` supports argument sequences, timeout, stdout/stderr capture, text mode, cwd, and explicit `shell=False` execution. |
| https://docs.python.org/3/library/time.html#time.perf_counter_ns | `time.perf_counter_ns()` provides a high-resolution monotonic performance counter for elapsed-duration measurement. |

Repository facts:

- CP1 API E2E, CP2 output-correctness, CP3 language-quality, CP4 media-artifacts, CP5 access/quota/retention, and CP6 security/observability already execute the local product/API path.
- The API echoes request IDs through response headers; only walkthrough generation exposes body-level trace timing as `trace.latencyMs`, so CP7 must not claim body-level timing fields for every operation.
- Stage 4 local API behavior already exposes local principal scoping, project/document/run authorization, idempotency records, approved upload requirements, unsupported claim evaluation, trace metadata, evidence snapshots, local provider posture, and `/api/v1/ops/status` bounded counts.
- C3A-CP7 must use approved synthetic project knowledge only and must not rely on docs/prose/static-snapshot evidence, canned success files, success-shaped dictionaries, provider calls, provider SDKs, external network product logic, public URLs, or private data.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3A-CP7-HARNESS-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_api_probe_and_keeps_later_probes_planned` | planned RED before harness implementation, green before PR |
| C3A-CP7-PERFORMANCE-001 | `tests/acceptance/test_checkpoint3_performance.py::test_checkpoint3_performance_executes_runtime_api_critical_path` | planned RED/green before PR |
| C3A-CP7-BINDING-001 | Runtime nonce, operation names, request binding booleans, project/document/ingestion/run/evaluation IDs, trace metadata, and local/mock posture assertions | planned RED/green before PR |
| C3A-CP7-REDACTION-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_performance_evidence_fields` and acceptance redaction assertions | planned RED/green before PR |
| C3A-CP7-FALSEPASS-001 | `tests/acceptance/test_checkpoint3_performance.py::test_checkpoint3_performance_rejects_static_or_unbound_evidence` and harness command canaries | planned RED/green before PR |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3A-CP7-FALSEPASS-001 | The performance probe must not pass by grepping docs, reading planned prose, checking static snapshots, using canned success files, or accepting success-shaped dictionaries without runtime nonce, source/run binding, request binding, trace, evaluation, operation timing, and explicit threshold evidence. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_static_performance_probe_command` and `tests/acceptance/test_checkpoint3_performance.py::test_checkpoint3_performance_rejects_static_or_unbound_evidence` |
| C3A-CP7-PERFORMANCE-001 | Timings must be measured from the local FastAPI product/API path and checked only against explicit reviewable thresholds that are broad enough for local CI. | Runtime operation timing assertions |
| C3A-CP7-BINDING-001 | Missing run/request/performance binding, stale performance evidence from a different run, and cross-project replay of valid-looking performance evidence cannot pass. | Acceptance evidence contract mutation assertions |
| C3A-CP7-REDACTION-001 | Raw uploaded content, prompt-injection text, private-looking markers, sensitive tokens, and accepted script text must not appear in bounded failure output. | Acceptance public-safe checks and harness redaction canaries |
| C3A-CP7-NONGOAL-001 | CP7 must not overclaim real-browser E2E, hosted deployment, provider setup, cloned identity, real media, public distribution, or production-readiness. | Scope docs, status docs, and acceptance harness planned-probe reporting |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3A-CP7-FM-001 | Harness leaves performance planned. | Implemented probe list requires API E2E, output-correctness, language quality, media artifacts, access/quota/retention, security/observability, and performance. |
| C3A-CP7-FM-002 | Harness points performance to docs/prose/static-snapshot content. | Command validator requires `tests/acceptance/test_checkpoint3_performance.py` and forbids docs/static/snapshot/prose/`rg`/`cat`. |
| C3A-CP7-FM-003 | Acceptance test checks style-only/status-only text instead of executing the local product/API path. | Positive test creates runtime projects, uploads/approves/ingests knowledge, generates runtime runs, and measures named API operations. |
| C3A-CP7-FM-004 | Performance evidence is a canned success dict or success-shaped timing table. | Evidence contract requires runtime nonce, `fastapi-testclient`, operation timings, explicit thresholds, request binding, source/run binding, trace metadata, and local/mock posture. |
| C3A-CP7-FM-005 | Missing run/request/performance binding passes. | Evidence contract validates operation binding, request header binding, source project/document/ingestion/run/evaluation IDs, and generation trace binding. |
| C3A-CP7-FM-006 | Stale performance evidence from another run or cross-project replay passes. | Mutated evidence from a second runtime project/run must fail source/run binding checks. |
| C3A-CP7-FM-007 | Raw uploaded content, prompt-injection text, private-looking markers, or sensitive tokens leak in bounded failure output. | Harness and acceptance checks redact performance fields and sensitive token/password/secret/api-key strings. |
| C3A-CP7-FM-008 | Timeout/subprocess failures or missing thresholds are treated as pass-by-existence. | Harness uses `timeout=120`, redacted summaries, and acceptance evidence requires explicit threshold fields and pass/fail booleans. |

## Fan-Out Review Findings

Pre-implementation sub-agent fan-out was used before implementation. Cross-model review is skipped in this autonomous execution context.

Disposition before implementation:

- Synthetic-data and public/private boundary: accepted. CP7 uses approved synthetic local knowledge only and adds CP7-specific raw upload, prompt, injection, private marker, and sensitive token canaries.
- Performance evidence design and flake risk: accepted. CP7 uses broad CI-safe explicit thresholds, records all operation timings, uses stable operation names, gates gross regressions only, and accepts API `trace.latencyMs >= 0` because local/mock runs may truncate to zero milliseconds.
- API/interface behavior: accepted. CP7 uses existing FastAPI `TestClient`, existing response header request IDs, existing walkthrough trace metadata, and adds no API schema or endpoint.
- Security/redaction preservation: accepted. CP7 adds harness redaction for CP7 canaries and performance evidence fields, and acceptance evidence avoids raw request/run IDs in public failure context.
- Observability metadata preservation: accepted. Generation evidence binds to `traceId`, `runId`, `evaluationId`, provider posture, and ops/status counts where the current API exposes them.
- Output correctness and grounding preservation: accepted. CP7 preserves source citations, `contextRefs`, `claimSupports`, evaluation status, and accepted grounded output while keeping raw accepted script text out of public failure context.
- Access/replay/idempotency preservation: accepted. CP7 uses a replay operation and rejects stale/cross-project performance evidence rather than relying on CP5 alone.
- Quota/retention regression risk: accepted as preserved by CP5 in the harness. CP7 does not edit quota or retention implementation.
- Test/quality/CI: accepted. Exact issue #267 allowlist, near-match branch denial, CP7 preflight contract checks, dispatcher canaries, and runtime acceptance tests are required.
- Governance/taste/scope: accepted. CP7 changes only harness, tests, and public governance/status docs. It keeps no provider setup, no hosted deployment, no cloned identity, and no production-readiness claim.

Pre-implementation blocker dispositions:

- Missing CP7 markdown preflight artifact. Disposition: accepted and fixed by this file before product-path implementation.
- CP7 claim marker mismatch between `C3A-CP7-PERF-001` and `C3A-CP7-PERFORMANCE-001`. Disposition: accepted and fixed by using `C3A-CP7-PERFORMANCE-001` consistently.
- Harness still CP6-shaped. Disposition: accepted and fixed by dispatcher/test updates.
- CP7 failure summaries can leak CP7 canaries. Disposition: accepted and fixed by CP7 redaction canaries in `scripts/quality/check_checkpoint3_acceptance.py`.
- CP7 request/run IDs need public-safe representation. Disposition: accepted; evidence records binding booleans and ID equality/hash checks rather than dumping raw IDs in failure context.
- Stage 8 latency smoke is insufficient CP7 evidence. Disposition: accepted; CP7 creates new runtime evidence with operation names, request binding, source/run binding, explicit thresholds, and local/mock posture.

Final fan-out disposition before PR:

- A final fan-out review must run after implementation. The last fan must be clean before human review; accepted findings must be fixed and rejected findings must include file/test evidence.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue, branch, first-commit preflight, allowlist tests, preflight doc, acceptance test, harness, docs, validation, PR, CI watch, and approval-bound merge closeout. |
| spec-driven-development | Invoked | CP7 contract and failure matrix are defined before implementation. |
| test-driven-development | Invoked | Unit and acceptance regressions are added before harness implementation is completed. |
| source-driven-development | Invoked | Official FastAPI and Python subprocess/timing sources are cited. |
| security-and-hardening | Invoked | Synthetic fixtures, provider env clearing, public-safe failure output, prompt-injection text canaries, and sensitive token redaction are part of CP7. |
| api-and-interface-design | Invoked | Existing API-visible project, document, run, request header, idempotency, and error shapes are asserted without adding API surfaces. |
| observability-and-instrumentation | Invoked | Runtime trace/run/evaluation metadata, local/mock provider posture, and `/api/v1/ops/status` bounded counts are tested. |
| performance-optimization | Invoked | CP7 measures before asserting, uses explicit broad thresholds, and avoids machine-variance-sensitive micro-benchmarks. |
| code-review-and-quality | Invoked | Fan-out findings and dispositions are recorded and will be refreshed before human review. |
| doubt-driven-development | Invoked | False-pass, canned success, missing binding, stale evidence, cross-project replay, timeout, and redaction risks are encoded as canaries. |
| taste-check | Invoked | No backend abstractions or dependencies are added for a test-harness slice. |
| git-workflow-and-versioning | Invoked | Issue `#267`, dedicated branch, and preflight-only first commit preserve workflow. |
| browser-testing-with-devtools | Rejected | Browser/UX scope remains planned and untouched. |

## Stop Rule

Stop and open a new issue if CP7 requires provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime changes, new dependencies, private data, private media, private planning files, secrets, or real personal data.
