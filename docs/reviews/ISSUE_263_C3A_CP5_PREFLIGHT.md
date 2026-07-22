# Issue 263 C3A-CP5 Preflight

## Objective

C3A-CP5 implements the fifth Checkpoint 3A child implementation checkpoint for public tracker issue `#249` and child issue `#263`: executable access/quota/retention proof for the local/mock controlled demo path.

The claim is deliberately narrow: `make checkpoint3-acceptance` dispatches the access/quota/retention probe as executable runtime API behavior, and that probe evaluates API-visible local access boundaries, deterministic local quota/resource behavior, retention/deletion evidence, and replay behavior. This work does not complete Checkpoint 3A.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3A-CP5-HARNESS-001 | The Checkpoint 3 acceptance harness implements the `access/quota/retention` probe through `uv run pytest tests/acceptance/test_checkpoint3_access_quota_retention.py -q`, with `shell=False`, `timeout=120`, and bounded/redacted failure output. |
| C3A-CP5-AQR-001 | The acceptance test creates approved synthetic local projects, uploads approved synthetic non-NarraTwin project knowledge, ingests/chunks/stores it, generates grounded walkthroughs, exercises project/run/document/artifact access boundaries, quota/resource limits, retention/deletion/tombstone behavior, and API-visible replay. |
| C3A-CP5-RUNTIME-001 | The proof comes from runtime API responses, idempotent replay, local `/api/v1/ops/status` evidence, and existing local/fake retention storage behavior, not from docs/prose/static snapshots or status-only text. |
| C3A-CP5-NONGOAL-001 | Later security/observability, performance, and real-browser E2E probes remain planned. |

## Scope

In scope:

- `scripts/quality/check_checkpoint3_acceptance.py`
- `tests/acceptance/test_checkpoint3_access_quota_retention.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/governance/preflights/issue-263.json`
- `docs/reviews/ISSUE_263_C3A_CP5_PREFLIGHT.md`

Out of scope: provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, public distribution, production-readiness claims, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime deployment, new dependencies, secrets, private media, private planning files, and real personal data.

The PR may bundle repository-ledger cleanup for PR `#262` and issue `#261` because this is a substantive child checkpoint, not a standalone status-only follow-up.

## Source Facts

Accessed date: 2026-07-22.

| Source | Fact used |
| --- | --- |
| https://fastapi.tiangolo.com/tutorial/testing/ | FastAPI supports `TestClient` for ordinary pytest functions and assertions against app behavior. |
| https://fastapi.tiangolo.com/reference/testclient/ | `TestClient` is the local in-process API client used for deterministic acceptance tests. |
| https://docs.python.org/3/library/subprocess.html#subprocess.run | `subprocess.run` supports argument sequences, timeout, environment, stdout/stderr capture, and explicit `shell=False` execution. |
| https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue | GitHub supports linking pull requests to issues with issue references; the parent tracker is reference-only and must remain open. |
| https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html | Make phony targets are appropriate for command targets that do not represent files. |

Repository facts:

- CP1 API E2E, CP2 output-correctness, CP3 language-quality, and CP4 media-artifacts already execute the local product/API path.
- Stage 4 local API behavior already exposes local principal scoping, project/document/run authorization, idempotency records, upload/request/document/resource limits, grounded runtime evidence, and `/api/v1/ops/status` bounded counts.
- Stage 6 and Stage 7 local APIs already reject cross-project or mismatched source-run media replay.
- The hosted-demo local/fake API already exposes quotaState, retention/deletion/tombstone denial states, metadata-only artifact/source evidence, and trusted local terminal retention storage behavior without hosted deployment or real providers.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3A-CP5-HARNESS-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_api_probe_and_keeps_later_probes_planned` | planned RED before harness implementation |
| C3A-CP5-AQR-001 | `tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path` | planned RED/green before PR |
| C3A-CP5-FALSEPASS-001 | `tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_rejects_static_or_status_only_evidence` | planned RED/green before PR |
| C3A-CP5-RUNTIME-001 | Runtime API responses, idempotent replay, hosted-demo metadata, and `/api/v1/ops/status` assertions | planned RED/green before PR |
| C3A-CP5-REDACTION-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_access_quota_retention_evidence_fields` | planned RED before harness implementation |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3A-CP5-FALSEPASS-001 | The access/quota/retention probe must not pass by grepping docs, reading planned prose, checking static snapshots, or using canned success files. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_static_access_quota_retention_probe_command` |
| C3A-CP5-ACCESS-001 | Cross-actor, cross-project, document, run, and artifact access must remain scoped to the expected local tenant/actor/project boundary. | `tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path` |
| C3A-CP5-IDEMPOTENCY-001 | Idempotency replay cannot bypass access checks, cross-project replay, or mismatched source-run replay. | `tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path` |
| C3A-CP5-QUOTA-001 | Upload/request/body/document limits fail safely with bounded public-safe errors including `PROJECT_DOCUMENT_LIMIT_EXCEEDED`, `UPLOAD_TOO_LARGE`, and hosted-demo `quotaState` exhaustion. | `tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path` |
| C3A-CP5-RETENTION-001 | Deleted or retained records cannot be replayed as active when local policy forbids it; `RETENTION_DELETED` and tombstone evidence must be API-visible. | `tests/acceptance/test_checkpoint3_access_quota_retention.py::test_checkpoint3_access_quota_retention_executes_runtime_api_boundary_path` |
| C3A-CP5-REDACTION-001 | Failure summaries must redact access/quota/retention identifiers, raw uploads, prompts, artifact evidence, and secret/session material. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_access_quota_retention_evidence_fields` |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3A-CP5-FM-001 | Harness leaves access/quota/retention planned. | Implemented probe list requires `API E2E`, `language quality`, `media artifacts`, `access/quota/retention`, and `output-correctness that executes rather than reads`. |
| C3A-CP5-FM-002 | Harness points access/quota/retention to docs/prose/static/snapshot content. | Command validator requires `tests/acceptance/test_checkpoint3_access_quota_retention.py` and forbids docs/static/snapshot/prose/`rg`/`cat`. |
| C3A-CP5-FM-003 | Acceptance test checks status-only text instead of executing the local product/API path. | Positive test creates two projects, uploads/approves/ingests knowledge, generates walkthroughs, checks access boundaries, and requires `/api/v1/ops/status` runtime counts. |
| C3A-CP5-FM-004 | Cross-project replay with valid-looking IDs retrieves or mutates another project. | API calls with mismatched project/run/document/source-run IDs must return `403`, `404`, or `422` without stored evidence leakage. |
| C3A-CP5-FM-005 | Idempotency replay bypasses actor/project/source-run checks. | Reused idempotency keys under another actor or project must not replay another actor/project response and must fail or create only that actor's own scoped resource. |
| C3A-CP5-FM-006 | Quota/resource failures leak raw upload/private payload text. | Upload/request/document-limit errors assert bounded structured error bodies and absence of raw canary text. |
| C3A-CP5-FM-007 | Deleted retention evidence is replayed as active evidence. | Trusted local terminal retention evidence causes active replay denial with `RETENTION_DELETED`, tombstone metadata, and metadata-only output. |
| C3A-CP5-FM-008 | CP5 overclaims security/observability, performance, browser, hosted, provider, cloned identity, or production readiness. | Scope and status docs keep those probes planned or forbidden. |

## Fan-Out Review Findings

Manual adversarial fallback is used before implementation.

Disposition:

- Access-boundary review: test local actor headers, project/document/run checks, Stage 6/7 source-run binding, cross-project replay, and same-key idempotency under a mismatched actor.
- Quota/resource review: test Stage 4 upload/document limits and hosted-demo local/fake quotaState exhaustion with public-safe error assertions.
- Retention/deletion/replay review: test local/fake hosted-demo terminal retention evidence, stale active replay denial, tombstone metadata, and changed retention-record replay denial.
- Output correctness/grounding review: CP5 must preserve grounded walkthrough generation and context/claim-support evidence from CP1-CP4.
- API/interface review: CP5 uses current API-visible behavior and does not add new endpoints or schemas.
- Security/privacy review: fixtures are synthetic, provider env vars are cleared, raw canaries are not exposed in errors, and no provider calls or secrets are used.
- Observability/redaction review: `/api/v1/ops/status` is used only for bounded counts, and harness failure output redacts access/quota/retention evidence fields.
- Performance review: CP5 adds one focused pytest probe under the existing `timeout=120` subprocess boundary.
- Test/quality/CI review: exact branch allowlist and static false-pass canaries are added before harness implementation.
- Governance/taste/scope review: no backend, frontend, provider, dependency, Docker, workflow, private plan, or public/production scope is touched.
- UX/demo flow review: no browser/frontend scope is touched, so browser-testing-with-devtools is rejected for CP5.

Cross-model review is skipped in this autonomous execution context because the available review path is local adversarial review and test-driven negative canaries.

Fan-out disposition before PR:

- Access/quota/retention reviewer found no blocker and requested a stronger hosted-demo idempotency canary; disposition: added a reused-idempotency forged artifact/source replay assertion expecting `IDEMPOTENCY_CONFLICT`.
- API/security/observability reviewer found blocker-level gaps in snake_case failure-field redaction and artifact-boundary proof; disposition: expanded harness redaction for snake_case access/quota/retention fields and added the forged artifact/source replay assertion.
- Governance/performance/test reviewer found blocker-level static-success risk in the acceptance helper and repeated the artifact-boundary gap; disposition: the runtime evidence contract now requires a positive-path `cp5-runtime-` nonce plus `fastapi-testclient` source marker, and the forged artifact/source replay assertion covers artifact-boundary proof.
- Non-blocking retention setup note: the terminal deletion state is seeded through trusted local/fake storage because this slice has no deletion HTTP endpoint; the replay denial itself is still verified through the runtime API.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue, branch, first-commit preflight, allowlist tests, acceptance test, harness, docs, validation, PR. |
| spec-driven-development | Invoked | CP5 contract and failure matrix defined before implementation. |
| test-driven-development | Invoked | Unit and acceptance regressions are added before harness implementation is completed. |
| source-driven-development | Invoked | Official FastAPI, Python subprocess, GitHub issue linking, and GNU Make docs were consulted. |
| security-and-hardening | Invoked | Public synthetic fixtures, local/mock provider posture, access redaction, secret/session redaction, and no raw payload leakage. |
| api-and-interface-design | Invoked | Existing API-visible access, idempotency, quota, retention, and error shapes are asserted without adding new API surfaces. |
| observability-and-instrumentation | Invoked | Bounded `/api/v1/ops/status` and harness redaction are part of CP5. |
| performance-optimization | Invoked | Probe remains focused and bounded by the existing timeout. |
| code-review-and-quality | Invoked | Fan-out findings and local review are recorded. |
| doubt-driven-development | Invoked | False-pass, cross-project replay, idempotency, quota, and retention risks are encoded as canaries. |
| taste-check | Invoked | No backend abstractions or dependencies are added for a test-harness slice. |
| git-workflow-and-versioning | Invoked | Issue `#263`, dedicated branch, and preflight-only first commit preserve workflow. |
| browser-testing-with-devtools | Rejected | Browser/UX scope remains planned and untouched. |

## Stop Rule

Stop and open a new issue if CP5 requires provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime changes, new dependencies, private data, private media, private planning files, secrets, or real personal data.
