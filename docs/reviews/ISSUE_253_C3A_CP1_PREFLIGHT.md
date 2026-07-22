# Issue #253 C3A-CP1 Preflight

## Objective

C3A-CP1 is the first Checkpoint 3A child implementation checkpoint under
public tracker issue `#249`. It converts `make checkpoint3-acceptance` from a
failing-by-design placeholder into an executable local acceptance harness and
implements the first real probe: API E2E foundation.

The probe must execute the local product path. It must not pass by grepping
docs, reading planning prose, or checking static snapshots only.

Later probes for language quality, media artifacts, access/quota/retention,
security/observability, performance, real-browser E2E, and output-correctness
remain planned and non-passing in CP1.

## Scope

In scope:

- dispatcher-style Checkpoint 3 acceptance harness
- executable API E2E foundation probe
- synthetic approved non-NarraTwin project knowledge
- negative coverage for false-pass behavior
- planned status for later Checkpoint 3A probes
- public-safe docs/status/traceability updates required by repository policy

Out of scope:

- cloned voice, cloned face, digital twin, or real-person likeness
- hosted deployment, public URL, public distribution, or production readiness
- provider setup, provider SDKs, provider keys, provider accounts, provider
  dashboards, real provider calls, paid plans, wallet funding, or paid spend
- Checkpoint 3B, Checkpoint 3C, Product Mode 2, or production implementation
- frontend/browser scope beyond preserving later planned probe labels

## Source Facts

Accessed date: 2026-07-22.

| ID | Source | Fact Used |
|---|---|---|
| `SRC-C3A-CP1-FASTAPI-001` | `https://fastapi.tiangolo.com/tutorial/testing/` | FastAPI documents using `TestClient` with pytest by passing the FastAPI application and making normal HTTP-style requests. CP1 can exercise local API route behavior without starting an external server or using network-dependent provider logic. |
| `SRC-C3A-CP1-FASTAPI-002` | `https://fastapi.tiangolo.com/reference/testclient/` | FastAPI's `TestClient` communicates directly with FastAPI code without opening a real HTTP/socket connection. This supports deterministic local API E2E foundation evidence while remaining inside local/dev/test boundaries. |
| `SRC-C3A-CP1-GH-001` | `https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue` | GitHub issue-linking keywords can close issues when PRs merge. CP1 public text must use reference-only wording for `#249` and close only the child issue if closure is intentionally selected at merge. |
| `SRC-C3A-CP1-MAKE-001` | `https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html` | GNU Make phony targets are explicit named recipes. `make checkpoint3-acceptance` remains a named local gate target and may return nonzero while planned later probes are not implemented. |

## Positive Claims

| ID | Claim | Evidence |
|---|---|---|
| `C3A-CP1-HARNESS-001` | The acceptance gate dispatches probe definitions and returns probe-specific evidence instead of a static placeholder. | `tests/unit/test_checkpoint3_acceptance_gate.py` and `make checkpoint3-acceptance` output. |
| `C3A-CP1-API-001` | The API E2E foundation probe executes local API behavior for project creation, approved knowledge upload/load, ingestion/chunk/store, retrieval, grounded script generation, unsupported-claim evaluation, output storage, and API evidence retrieval. | `tests/acceptance/test_checkpoint3_api_e2e.py::test_checkpoint3_api_e2e_executes_local_product_path`, API-visible idempotent replay of the walkthrough response, and bounded `GET /api/v1/ops/status` record counts. |
| `C3A-CP1-PLANNED-001` | Later Checkpoint 3A probes stay visible as planned and do not count as completed. | Harness probe statuses and docs. |

## Negative Invariants

| ID | Must remain false | Evidence |
|---|---|---|
| `C3A-CP1-NONGOAL-001` | CP1 does not enable providers, paid spend, hosted deployment, public URL, cloned identity, public distribution, or production readiness. | Branch allowlist and docs/status wording. |
| `C3A-CP1-FALSEPASS-001` | A checker that succeeds by reading docs/prose/static snapshots is inadequate. | Unit canary rejects command definitions that target docs/prose instead of executable acceptance tests. |
| `C3A-CP1-APPROVAL-001` | Unapproved knowledge cannot be ingested while claiming API E2E success. | Acceptance negative for `DOCUMENT_NOT_APPROVED`. |
| `C3A-CP1-ISOLATION-001` | Cross-project replay cannot retrieve another project's chunks. | Acceptance negative with two synthetic projects and source-specific output checks. |
| `C3A-CP1-UNSUPPORTED-001` | Unsupported generated claims cannot be accepted as a passing output. | Acceptance negative monkeypatches local mock LLM to add an unsupported claim and expects failed/refused output evidence. |

## Failure Matrix

| Matrix ID | Case | Expected behavior | Evidence type | Test/source/doc |
|---|---|---|---|---|
| `C3A-CP1-FM-001` | Executable API path with approved synthetic knowledge | Completed run with citations, context refs, zero unsupported claims, trace metadata, and stored run evidence | test | `tests/acceptance/test_checkpoint3_api_e2e.py::test_checkpoint3_api_e2e_executes_local_product_path` |
| `C3A-CP1-FM-002` | Missing approval before ingestion | Fails with `DOCUMENT_NOT_APPROVED` and stores no chunks | test | `tests/acceptance/test_checkpoint3_api_e2e.py::test_checkpoint3_api_e2e_rejects_unapproved_knowledge_before_ingestion` |
| `C3A-CP1-FM-003` | Cross-project replay attempt | Project A generation does not cite or expose Project B-only facts | test | `tests/acceptance/test_checkpoint3_api_e2e.py::test_checkpoint3_api_e2e_rejects_cross_project_replay` |
| `C3A-CP1-FM-004` | Unsupported claim emitted by local provider | Run is not accepted as passed and unsupported claim evidence is present | test | `tests/acceptance/test_checkpoint3_api_e2e.py::test_checkpoint3_api_e2e_rejects_unsupported_claim_acceptance` |
| `C3A-CP1-FM-005` | Docs/prose/static checker substitution | Harness tests fail when implemented probes point to docs/static paths rather than executable tests | test | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_docs_only_probe_commands` |
| `C3A-CP1-FM-006` | Later C3A probes not implemented | Harness reports planned labels and overall nonzero without claiming Checkpoint 3A completion | test/doc | `tests/unit/test_checkpoint3_acceptance_gate.py` and `docs/QUALITY_GATES.md` |

## Fan-Out Review Findings

Sub-agent fan-out was run after the issue and preflight-only first commit were
created. Manual adversarial fallback supplements the sub-agent findings.
Cross-model review is skipped in this autonomous execution context.

| Area | Finding | Disposition |
|---|---|---|
| output-correctness | A static scanner could pass by finding planned phrases in docs. | Add `C3A-CP1-FM-005`, make probe definitions require executable acceptance test commands, run implemented probes with `shell=False`, and reject `docs/`, prose, snapshot, `rg`, `cat`, or no-op command substitutions before reporting success. |
| API/interface | E2E proof can accidentally inspect in-memory state only, and CP1's allowed scope does not add a new GET run route. | The positive probe must drive FastAPI routes, prove API-visible idempotent replay of the stored walkthrough response, and use `GET /api/v1/ops/status` only for bounded record-count evidence. Direct service dictionaries may supplement debugging but are not the API evidence retrieval claim. |
| security/privacy | Synthetic project knowledge is still untrusted input and must not include secrets or private data. | Use small public-safe fixtures and preserve existing upload/approval safeguards. |
| access/quota/reliability/retention | Later access/quota/retention probes are not implemented by CP1. | Keep them planned and non-passing in the harness. |
| observability/redaction | E2E output should prove trace/run metadata without logging raw uploads/scripts as evidence, and optional observability environment variables must not cause external egress in CP1 tests. Final security review also found that failed subprocess output must not be printed unbounded. | Assert bounded response metadata, clear Langfuse environment variables in the acceptance tests, require local provider mode and zero estimated cost, require redacted evidence surfaces where unsafe output is returned, summarize failed probe output with a denylist redactor and length cap, and avoid raw telemetry dumps in docs/PR text. |
| performance | CP1 should not overclaim performance, but the harness must prepare a future performance probe. | Keep the performance probe planned and non-passing. |
| test/quality/CI | The branch can drift into unrelated runtime or provider work. | Add exact issue `#253` allowlist and near-match regression tests before implementation. |
| governance/taste/scope | A large harness abstraction could obscure which probes are real versus planned. | Keep a small explicit dispatcher with typed probe statuses. |

## Skill And Tool Selection Ledger

| Skill or review mode | Decision | Evidence |
|---|---|---|
| planning-and-task-breakdown | Invoked | CP1 is limited to preflight, allowlist, harness, one API E2E probe, and docs/status updates. |
| spec-driven-development | Invoked | Positive claims, negative invariants, and failure matrix are listed above. |
| test-driven-development | Invoked | RED target is unit/acceptance tests before harness implementation. |
| source-driven-development | Invoked | FastAPI, GitHub, and GNU Make source facts are recorded. |
| security-and-hardening | Invoked | Upload/approval, no providers, no secrets, no private data, and unsupported-claim negatives are explicit. |
| api-and-interface-design | Invoked | API route behavior and response evidence are the CP1 proof boundary. |
| observability-and-instrumentation | Invoked | Trace/run metadata is part of the E2E proof; raw content is not logged as evidence. |
| performance-optimization | Invoked | Performance remains a planned probe, not a CP1 success claim. |
| browser-testing-with-devtools | Rejected for this CP1 implementation | No browser/frontend scope is touched; real-browser E2E remains a later planned probe. |
| code-review-and-quality | Invoked | Fan-out findings and final manual review will inspect tests, scope, and docs. |
| doubt-driven-development | Invoked | False-pass matrix attacks docs-only success, missing approval, cross-project replay, and unsupported claim acceptance. |
| taste-check | Invoked | Dispatcher should stay explicit and avoid broad framework abstraction. |
| git-workflow-and-versioning | Invoked | Issue-linked branch and preflight-only first commit are preserved. |

## Stop Rule

Stop and open a new issue if implementation requires backend product behavior
changes, frontend changes, provider setup, provider SDKs, real provider calls,
paid spend, hosted deployment, public URL, cloned identity, Checkpoint 3B,
Checkpoint 3C, Product Mode 2, production readiness, private data, private
media, or secrets.
