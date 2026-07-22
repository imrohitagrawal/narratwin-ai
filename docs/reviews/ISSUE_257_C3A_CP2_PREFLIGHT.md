# Issue #257 C3A-CP2 Preflight

## Objective

C3A-CP2 is tracked by child issue `#257` as the next Checkpoint 3A child
implementation checkpoint under public tracker issue `#249`. It implements an
executable output-correctness probe for `make checkpoint3-acceptance`.

The probe must execute the local product/API path and verify generated output
against runtime API evidence. It must not pass by grepping docs, reading
planning prose, checking static snapshots, or accepting canned success files.

Later probes for language quality, media artifacts, access/quota/retention,
security/observability, performance, and real-browser E2E remain planned and
non-passing in CP2.

## Scope

In scope:

- output-correctness that executes rather than reads
- executable local acceptance harness update
- exact output-correctness probe dispatch through pytest with `shell=False`
- approved synthetic non-NarraTwin project knowledge
- API-visible idempotent replay as stored output/evidence retrieval
- runtime citation/source/evidence binding checks
- negative coverage for correct-looking text without evidence binding
- negative coverage for unsupported claim acceptance
- negative coverage for cross-project fact replay
- public-safe docs/status/traceability updates required by repository policy

Out of scope:

- cloned voice, cloned face, digital twin, or real-person likeness
- hosted deployment, public URL, public distribution, or production readiness
- provider setup, provider SDKs, provider keys, provider accounts, provider
  dashboards, real provider calls, paid plans, wallet funding, or paid spend
- Checkpoint 3B, Checkpoint 3C, Product Mode 2, or production implementation
- backend route changes, frontend/browser scope, Stage 6 internals, Stage 7
  internals, Docker, workflows, dependency manifests, or provider code

## Source Facts

Accessed date: 2026-07-22.

| ID | Source | Fact Used |
|---|---|---|
| `SRC-C3A-CP2-FASTAPI-001` | `https://fastapi.tiangolo.com/tutorial/testing/` | FastAPI documents `TestClient` with pytest tests, HTTP-style client calls, and normal Python assertions. CP2 can exercise local route behavior without hosted deployment or provider network calls. |
| `SRC-C3A-CP2-FASTAPI-002` | `https://fastapi.tiangolo.com/reference/testclient/` | FastAPI exposes `fastapi.testclient.TestClient` for local application testing. CP2 uses it only for local/mock API evidence. |
| `SRC-C3A-CP2-GH-001` | `https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue` | GitHub issue-linking keywords can close issues when a linked PR merges. CP2 public PR text must use reference-only wording for both `#249` and `#257`; any satisfied child-issue closeout must happen after merge without PR auto-close keywords. |
| `SRC-C3A-CP2-MAKE-001` | `https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html` | GNU Make phony targets are explicit named recipes. `make checkpoint3-acceptance` remains a local named gate and may return nonzero while later planned probes are incomplete. |

## Positive Claims

| ID | Claim | Evidence |
|---|---|---|
| `C3A-CP2-HARNESS-001` | The acceptance harness implements exactly two probes: API E2E and output-correctness, while later Checkpoint 3A probes remain planned. | `tests/unit/test_checkpoint3_acceptance_gate.py` and `make checkpoint3-acceptance` output. |
| `C3A-CP2-OUTPUT-001` | The output-correctness probe executes local API behavior for project creation, approved knowledge upload/load, ingestion/chunk/store, grounded walkthrough generation, stored output replay, and runtime evidence checks. | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_executes_runtime_api_evidence_path`. |
| `C3A-CP2-EVIDENCE-001` | Required output facts pass only when `acceptedScriptText`, visible citation marker, `evaluation.claimSupports`, `contextRefs`, `citationIndex`, project/document IDs, checksums, and `evidenceSnapshot` agree. | `assert_runtime_output_fact_is_grounded` in `tests/acceptance/test_checkpoint3_output_correctness.py`. |

## Negative Invariants

| ID | Must remain false | Evidence |
|---|---|---|
| `C3A-CP2-NONGOAL-001` | CP2 does not enable providers, paid spend, hosted deployment, public URL, cloned identity, public distribution, browser scope, or production readiness. | Branch allowlist and docs/status wording. |
| `C3A-CP2-FALSEPASS-001` | A docs/prose/static-snapshot or canned-success checker cannot satisfy output-correctness. | Harness command canaries and runtime acceptance negatives. |
| `C3A-CP2-BINDING-001` | Correct-looking output text without citation/evidence binding cannot pass. | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_rejects_correct_text_without_evidence_binding`. |
| `C3A-CP2-UNSUPPORTED-001` | Unsupported generated claims cannot be accepted as passing output. | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_rejects_unsupported_claim_acceptance`. |
| `C3A-CP2-ISOLATION-001` | Cross-project facts cannot replay through another project's generated output. | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_rejects_cross_project_fact_replay`. |
| `C3A-CP2-REDACTION-001` | Failed probe output must be bounded and redact runtime evidence fields such as `acceptedScriptText`, `claimText`, `contextRefs`, `claimSupports`, `evidenceSnapshot`, and `redactedExcerpt`. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_runtime_evidence_fields`. |
| `C3A-CP2-TIMEOUT-001` | Implemented probe subprocesses must not run without a bounded timeout. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_timeout_is_bounded_and_redacted`. |

## Failure Matrix

| Matrix ID | Case | Expected behavior | Evidence type | Test/source/doc |
|---|---|---|---|---|
| `C3A-CP2-FM-001` | Executable output-correctness API path with approved synthetic knowledge | Completed run with required fact, citation marker, matching context refs, claim supports, evidence snapshots, checksums, zero unsupported claims, trace metadata, and idempotent replay equality | test | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_executes_runtime_api_evidence_path` |
| `C3A-CP2-FM-002` | Correct-looking text with missing or mismatched evidence binding | Assertion helper rejects missing `claimSupports` and mismatched `evidenceSnapshot.redactedExcerpt`; old static text-only behavior fails-before | test | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_rejects_correct_text_without_evidence_binding` |
| `C3A-CP2-FM-003` | Unsupported claim emitted by local mock provider | Run is failed, no `acceptedScriptText` is exposed, and redacted unsupported evidence is present | test | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_rejects_unsupported_claim_acceptance` |
| `C3A-CP2-FM-004` | Cross-project fact replay in generated output | Run is failed and all runtime context refs remain bound to the current project without the cross-project marker | test | `tests/acceptance/test_checkpoint3_output_correctness.py::test_checkpoint3_output_correctness_rejects_cross_project_fact_replay` |
| `C3A-CP2-FM-005` | Output-correctness command points at static snapshot or wrong acceptance file | Harness validation fails before reporting probe success | test | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_static_output_correctness_probe_command` |
| `C3A-CP2-FM-006` | Failed subprocess output includes runtime evidence fields | Failure summary redacts sensitive field lines and remains bounded | test | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_runtime_evidence_fields` |
| `C3A-CP2-FM-007` | Probe subprocess hangs or exceeds local budget | Harness returns failed probe with timeout evidence and redacted output | test | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_timeout_is_bounded_and_redacted` |
| `C3A-CP2-FM-008` | Later C3A probes not implemented | Harness reports planned labels and overall nonzero without claiming Checkpoint 3A completion | test/doc | `tests/unit/test_checkpoint3_acceptance_gate.py`, `docs/QUALITY_GATES.md` |

## Fan-Out Review Findings

Sub-agent fan-out was run after the issue and preflight-only first commit were
created. Cross-model review is skipped in this autonomous execution context.

| Area | Finding | Disposition |
|---|---|---|
| output-correctness | Harness was CP1-locked and did not exact-match the output-correctness acceptance file. | Update implemented probe list to API E2E plus output-correctness and add exact command canary for `tests/acceptance/test_checkpoint3_output_correctness.py`. |
| output-correctness | CP1 assertions were not enough because text presence plus any citation could still false-pass. | Add fact-level assertions binding visible text to citation index, claim support, context ref, project/document IDs, checksums, and evidence snapshot. |
| API/interface | The repository contract mentions GET retrieval, but the current backend scope exposes only POST generation for walkthrough runs. | CP2 uses API-visible idempotent POST replay plus `/api/v1/ops/status` record counts and does not add backend routes. |
| security/privacy | Failure diffs could expose output/evidence fields. | Keep assertions granular and redact `acceptedScriptText`, `claimText`, `contextRefs`, `claimSupports`, `evidenceSnapshot`, and `redactedExcerpt` in harness summaries. |
| access/quota/reliability/retention | Probe execution lacked a subprocess timeout, and local JSON state env vars could make acceptance reset touch developer state. | Add `timeout=120`, timeout handling, harness env denylist, and acceptance import-time state env clearing. Access/quota/retention remains planned. |
| observability/redaction | CP2 should prove trace/run metadata without dumping raw output. | Assert trace metadata and zero local cost through API JSON only. |
| performance | CP2 should stay small and not claim performance acceptance. | Use two small synthetic projects and keep the performance probe planned/non-passing. |
| test/quality/CI | Branch could drift into backend/frontend/provider work. | Add exact issue `#257` allowlist and near-match regression before implementation. |
| governance/taste/scope | Broad harness abstraction could hide planned versus implemented status. | Keep explicit `Probe` definitions and exact implemented labels. |

## Skill And Tool Selection Ledger

| Skill or review mode | Decision | Evidence |
|---|---|---|
| planning-and-task-breakdown | Invoked | CP2 is limited to preflight, allowlist, harness update, one acceptance probe, and public-safe docs/status updates. |
| spec-driven-development | Invoked | Positive claims, negative invariants, and failure matrix are listed above. |
| test-driven-development | Invoked | RED dispatcher tests failed until output-correctness became implemented; runtime negative tests prove old text/static false-pass behavior inadequate. |
| source-driven-development | Invoked | FastAPI, GitHub, and GNU Make source facts are recorded with official URLs and accessed date. |
| security-and-hardening | Invoked | Upload/approval, no providers, no secrets, no private data, runtime field redaction, and unsupported-claim negatives are explicit. |
| api-and-interface-design | Invoked | API route behavior, idempotent replay, and response evidence are the CP2 proof boundary. |
| observability-and-instrumentation | Invoked | Trace/run metadata is part of the E2E proof; raw content is not logged as evidence. |
| performance-optimization | Invoked | Runtime is bounded by small fixtures and subprocess timeout; performance remains a planned probe. |
| browser-testing-with-devtools | Rejected for this CP2 implementation | No browser/frontend scope is touched; real-browser E2E remains a later planned probe. |
| code-review-and-quality | Invoked | Fan-out findings and final manual review inspect tests, scope, and docs. |
| doubt-driven-development | Invoked | False-pass matrix attacks docs-only success, missing evidence binding, unsupported claim acceptance, and cross-project replay. |
| taste-check | Invoked | Dispatcher remains explicit and avoids a larger framework abstraction. |
| git-workflow-and-versioning | Invoked | Issue-linked branch and preflight-only first commit are preserved. |

## Stop Rule

Stop and open a new issue if implementation requires backend product behavior
changes, frontend changes, provider setup, provider SDKs, real provider calls,
paid spend, hosted deployment, public URL, cloned identity, Checkpoint 3B,
Checkpoint 3C, Product Mode 2, production readiness, private data, private
media, or secrets.
