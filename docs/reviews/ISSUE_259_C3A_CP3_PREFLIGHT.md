# Issue 259 C3A-CP3 Preflight

## Objective

C3A-CP3 implements the third Checkpoint 3A child implementation checkpoint for public tracker issue `#249` and child issue `#259`: executable language quality for local Stage 4 walkthrough generation.

The claim is deliberately narrow: `make checkpoint3-acceptance` dispatches the language quality probe as executable runtime API behavior, and that probe evaluates generated `acceptedScriptText` plus API-visible evidence. This work does not complete Checkpoint 3A.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3A-CP3-HARNESS-001 | The Checkpoint 3 acceptance harness implements the `language quality` probe through `uv run pytest tests/acceptance/test_checkpoint3_language_quality.py -q`, with `shell=False`, `timeout=120`, and bounded/redacted failure output. |
| C3A-CP3-LANGUAGE-001 | The acceptance test creates approved synthetic projects, uploads approved synthetic non-NarraTwin project knowledge, ingests/chunks/stores it, generates a grounded walkthrough, performs API-visible idempotent replay, and checks coherent walkthrough structure, audience-appropriate tone, placeholder text absence, internal debug leakage absence, trivially short output rejection, malformed citation placement rejection, cross-project rejection, and unsupported language rejection. |
| C3A-CP3-RUNTIME-001 | Language quality is checked from runtime API response fields including `acceptedScriptText`, `contextRefs`, `claimSupports`, `citationIndex`, `evidenceSnapshot`, and `redactedExcerpt`, plus `/api/v1/ops/status` durability counts. |
| C3A-CP3-NONGOAL-001 | Later media artifacts, access/quota/retention, security/observability, performance, and real-browser E2E probes remain planned. |

## Scope

In scope:

- `scripts/quality/check_checkpoint3_acceptance.py`
- `tests/acceptance/test_checkpoint3_language_quality.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/governance/preflights/issue-259.json`
- `docs/reviews/ISSUE_259_C3A_CP3_PREFLIGHT.md`

Out of scope: provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, public distribution, production-readiness claims, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime deployment, new dependencies, secrets, private media, and real personal data.

## Source Facts

Accessed date: 2026-07-22.

| Source | Fact used |
| --- | --- |
| https://fastapi.tiangolo.com/tutorial/testing/ | FastAPI supports `TestClient` for ordinary pytest functions and standard assertions against app behavior. |
| https://fastapi.tiangolo.com/reference/testclient/ | `TestClient` is the local in-process API client used for deterministic Stage 4 acceptance tests. |
| https://docs.python.org/3/library/subprocess.html#subprocess.run | `subprocess.run` supports argument sequences, timeout, environment, stdout/stderr capture, and explicit `shell=False` execution. |
| https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue | GitHub supports linking pull requests to issues with issue references; the parent tracker is reference-only and must remain open. |
| https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html | Make phony targets are appropriate for command targets that do not represent files. |

Repository facts:

- CP1 API E2E and CP2 output-correctness already execute the local product/API path.
- The current API-visible replay proof for walkthrough output is idempotent duplicate POST replay, not a documented GET run retrieval implementation.
- `evaluation.claimSupports` is the authoritative claim-to-evidence binding for CP3; top-level `contextRefs` are evidence rows.
- Stage 4 scope is English local/mock walkthrough generation. CP3 does not claim multilingual, browser, provider, or UI coverage.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3A-CP3-HARNESS-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_api_probe_and_keeps_later_probes_planned` | passed after implementation |
| C3A-CP3-LANGUAGE-001 | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_executes_runtime_api_output_path` | passed after implementation |
| C3A-CP3-RUNTIME-001 | API-visible idempotent replay, `acceptedScriptText`, `claimSupports`, `contextRefs`, `citationIndex`, `evidenceSnapshot`, `redactedExcerpt`, and `/api/v1/ops/status` assertions | passed after implementation |
| C3A-CP3-REDACTION-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_runtime_evidence_fields` | passed after implementation |
| C3A-CP3-TIMEOUT-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_timeout_is_bounded_and_redacted` | passed after implementation |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3A-CP3-FALSEPASS-001 | The language-quality probe must not pass by grepping docs, reading planning prose, checking static snapshots, or using canned success files. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_static_language_quality_probe_command` |
| C3A-CP3-PLACEHOLDER-001 | A grounded-looking output with placeholder text or boilerplate fails language quality. | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_grounded_placeholder_boilerplate_output` |
| C3A-CP3-SHORT-001 | A trivially short cited output fails language quality. | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_trivially_short_citation_output` |
| C3A-CP3-DEBUG-001 | Generated output with internal debug leakage fails language quality. | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_debug_or_internal_leakage` |
| C3A-CP3-CITATION-001 | Malformed citation placement that harms readability fails language quality. | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_malformed_citation_placement` |
| C3A-CP3-ISOLATION-001 | Cross-project or unsupported language insertion fails language quality. | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_cross_project_or_unsupported_language_insertions` |
| C3A-CP3-FALSEPASS-002 | Style text without runtime API evidence fails even when the text looks readable. | `tests/acceptance/test_checkpoint3_language_quality.py::test_checkpoint3_language_quality_rejects_style_text_without_runtime_api_evidence` |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3A-CP3-FM-001 | Harness leaves language quality planned. | Implemented probe list requires `API E2E`, `language quality`, and `output-correctness that executes rather than reads`. |
| C3A-CP3-FM-002 | Harness points language quality to docs/prose/static/snapshot content. | Command validator requires `tests/acceptance/test_checkpoint3_language_quality.py` and forbids docs/static/snapshot/prose/`rg`/`cat`. |
| C3A-CP3-FM-003 | Acceptance test checks a canned success file instead of executing the local product/API path. | Positive test creates projects, uploads knowledge, approves, ingests, generates, replays, and checks ops counts. |
| C3A-CP3-FM-004 | Output is grounded but unreadable. | Placeholder, short-output, debug-leak, and malformed-citation canaries fail the helper. |
| C3A-CP3-FM-005 | Output inserts cross-project language to satisfy style. | Two synthetic projects and Beacon isolation marker canary. |
| C3A-CP3-FM-006 | Assertion failures leak generated bodies or evidence. | Public-safe synthetic fixtures plus bounded/redacted harness summaries. |
| C3A-CP3-FM-007 | CP3 overclaims API retrieval support. | Evidence wording says API-visible idempotent replay rather than GET run retrieval. |
| C3A-CP3-FM-008 | CP3 overclaims browser, provider, multilingual, cloned identity, hosted, or production readiness. | Scope and status docs keep those probes planned or forbidden. |

## Fan-Out Review Findings

Sub-agent review was used before implementation.

Disposition:

- Language-quality/harness review: implemented the probe, added a language-specific command validator, and added a static language-quality canary.
- API/interface review: CP3 uses local FastAPI `TestClient`; API-visible idempotent replay is the stored output/evidence proof. It does not claim implemented GET run retrieval.
- Output correctness/grounding review: CP3 treats `evaluation.claimSupports` as authoritative evidence binding and validates `contextRefs` as evidence rows.
- Security/privacy/observability review: CP3 uses public synthetic content only, clears provider/state env vars, keeps provider local/mock, and avoids assertion messages that dump raw generated bodies.
- Performance/reliability review: CP3 adds one focused executable pytest probe under the existing `timeout=120` subprocess boundary.
- Governance/taste/scope review: exact issue `#259` allowlist and preflight checker were added; no browser/frontend scope is touched.
- UX/demo flow review: no browser/frontend scope is touched, so browser-testing-with-devtools is rejected for CP3.

Cross-model review is skipped in this autonomous execution context because the available review path is same-repository sub-agent fan-out and local adversarial review.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue, branch, first-commit preflight, tests, harness, docs, validation, PR. |
| spec-driven-development | Invoked | CP3 contract and failure matrix defined before implementation. |
| test-driven-development | Invoked | Unit and acceptance regressions were added before harness implementation was completed. |
| source-driven-development | Invoked | Official FastAPI, Python subprocess, GitHub issue linking, and GNU Make docs were consulted. |
| security-and-hardening | Invoked | Public synthetic fixtures, env cleanup, provider disabled/default local path, and redaction checks. |
| api-and-interface-design | Invoked | API-visible replay and evidence fields are asserted without adding or overclaiming API surfaces. |
| observability-and-instrumentation | Invoked | Trace/provider/ops evidence and redaction behavior are part of CP3. |
| performance-optimization | Invoked | Probe remains focused and bounded by the existing timeout. |
| code-review-and-quality | Invoked | Fan-out findings and local review are recorded. |
| doubt-driven-development | Invoked | False-pass and overclaim risks are encoded as canaries. |
| taste-check | Invoked | No backend abstractions or dependencies were added for a test-harness slice. |
| git-workflow-and-versioning | Invoked | Issue `#259`, dedicated branch, and preflight-only first commit preserve workflow. |
| browser-testing-with-devtools | Rejected | Browser/UX scope remains planned and untouched. |

## Stop Rule

Stop and open a new issue if CP3 requires provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime changes, new dependencies, private data, private media, secrets, or real personal data.
