# Issue 265 C3A-CP6 Preflight

## Objective

C3A-CP6 implements the sixth Checkpoint 3A child implementation checkpoint for public tracker issue `#249` and child issue `#265`: an executable security/observability probe for the local/mock controlled demo path.

The claim is deliberately narrow: `make checkpoint3-acceptance` dispatches the security/observability probe as executable runtime API behavior, and that probe evaluates runtime API-visible security controls, privacy/redaction behavior, observability metadata, bounded failure evidence, and anti-false-pass guarantees from approved synthetic local data. This work does not complete Checkpoint 3A.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3A-CP6-HARNESS-001 | The Checkpoint 3 acceptance harness implements the `security/observability` probe through `uv run pytest tests/acceptance/test_checkpoint3_security_observability.py -q`, with `shell=False`, `timeout=120`, and bounded/redacted failure output. |
| C3A-CP6-SECURITY-001 | The acceptance test creates synthetic local projects, uploads approved synthetic knowledge, ingests/chunks/stores it, generates grounded walkthroughs, and exercises missing approval, unsafe upload, prompt-injection, unsupported-claim, cross-project replay, same-payload cross-actor access denial with a reused idempotency key, and same-actor idempotency conflict boundaries. |
| C3A-CP6-OBSERVABILITY-001 | The acceptance test checks API-visible trace/run/evaluation metadata, status/ops bounded evidence, local/mock provider posture, acceptance-runtime evidence nonce, and source/run binding tied to generated runtime runs rather than static fixtures. |
| C3A-CP6-REDACTION-001 | The probe and harness assert that raw uploaded content, prompt-injection text, private-looking markers, token/password/secret/api-key strings, and snake_case variants do not appear in public-safe failure output. |
| C3A-CP6-NONGOAL-001 | Later performance and real-browser E2E probes remain planned. |

## Scope

In scope:

- `scripts/quality/check_checkpoint3_acceptance.py`
- `tests/acceptance/test_checkpoint3_security_observability.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/reviews/ISSUE_265_C3A_CP6_PREFLIGHT.md`
- `docs/governance/preflights/issue-265.json`

Out of scope: provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, public distribution, production-readiness claims, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime deployment, new dependencies, secrets, private media, private planning files, and real personal data.

The PR may bundle repository-ledger cleanup for PR `#264` and issue `#263` because this is a substantive child checkpoint, not a standalone status-only follow-up. Issue #249 remains open.

## Source Facts

Accessed date: 2026-07-23.

| Source | Fact used |
| --- | --- |
| https://fastapi.tiangolo.com/tutorial/testing/ | FastAPI supports `TestClient` for ordinary pytest functions and assertions against app behavior. |
| https://fastapi.tiangolo.com/reference/testclient/ | `TestClient` is the local in-process API client used for deterministic acceptance tests. |
| https://docs.python.org/3/library/subprocess.html#subprocess.run | `subprocess.run` supports argument sequences, timeout, stdout/stderr capture, text mode, cwd, and explicit `shell=False` execution. |
| https://owasp.org/www-project-top-10-for-large-language-model-applications/ | LLM application security review should account for prompt-injection and sensitive information disclosure risks. |
| https://csrc.nist.gov/Projects/ssdf | Secure software work should include verifiable practices and evidence for security-relevant controls. |

Repository facts:

- CP1 API E2E, CP2 output-correctness, CP3 language-quality, CP4 media-artifacts, and CP5 access/quota/retention already execute the local product/API path.
- Stage 4 local API behavior already exposes local principal scoping, project/document/run authorization, idempotency records, approved upload requirements, unsafe document rejection, unsupported claim evaluation, trace metadata, evidence snapshots, local provider posture, and `/api/v1/ops/status` bounded counts.
- The hosted-demo local/fake API already exposes metadata-only source/evaluation/artifact decisions, retention metadata, quotaState, local provider posture, and redacted event summaries without hosted deployment or real providers.
- C3A-CP6 must use approved synthetic project knowledge only and must not rely on docs/prose/static-snapshot evidence, canned success files, success-shaped dictionaries, provider calls, provider SDKs, external network product logic, public URLs, or private data.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3A-CP6-HARNESS-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_api_probe_and_keeps_later_probes_planned` | planned RED before harness implementation, green before PR |
| C3A-CP6-SECURITY-001 | `tests/acceptance/test_checkpoint3_security_observability.py::test_checkpoint3_security_observability_executes_runtime_api_boundary_path` | planned RED/green before PR |
| C3A-CP6-OBSERVABILITY-001 | Runtime API responses, hosted-demo metadata, redacted event summaries, and `/api/v1/ops/status` assertions | planned RED/green before PR |
| C3A-CP6-REDACTION-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_security_observability_evidence_fields` and acceptance redaction assertions | planned RED/green before PR |
| C3A-CP6-FALSEPASS-001 | `tests/acceptance/test_checkpoint3_security_observability.py::test_checkpoint3_security_observability_rejects_static_or_unbound_evidence` and harness command canaries | planned RED/green before PR |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3A-CP6-FALSEPASS-001 | The security/observability probe must not pass by grepping docs, reading planned prose, checking static snapshots, using canned success files, or accepting success-shaped dictionaries without acceptance-runtime nonce, source/run binding, trace, run, evaluation, and observability binding. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_static_security_observability_probe_command` and `tests/acceptance/test_checkpoint3_security_observability.py::test_checkpoint3_security_observability_rejects_static_or_unbound_evidence` |
| C3A-CP6-SECURITY-001 | Missing approval, unsafe upload text, prompt-injection, unsupported claim generation, cross-project replay, same-payload cross-actor access denial with a reused idempotency key, and same-actor idempotency conflict cannot bypass security controls or produce accepted grounded evidence when policy forbids it. | `tests/acceptance/test_checkpoint3_security_observability.py::test_checkpoint3_security_observability_executes_runtime_api_boundary_path` |
| C3A-CP6-OBSERVABILITY-001 | Observability metadata must be tied to generated runtime runs and include bounded trace/run/evaluation evidence where the current implementation exposes it. | Runtime `trace_` metadata, evaluation checksum, local/mock provider posture, redacted hosted-demo events, and `/api/v1/ops/status` assertions |
| C3A-CP6-REDACTION-001 | Raw uploaded content, raw prompt-injection text, private-looking markers, and sensitive token/password/secret/api-key markers including snake_case variants must not appear in public-safe errors, ops/status, logs, redacted events, or failure output. | Acceptance public-safe response checks and harness bounded failure redaction canaries |
| C3A-CP6-NONGOAL-001 | CP6 must not overclaim performance, browser coverage, hosted deployment, provider setup, cloned identity, real media, public distribution, or production-readiness. | Scope docs, status docs, and acceptance harness planned-probe reporting |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3A-CP6-FM-001 | Harness leaves security/observability planned. | Implemented probe list requires API E2E, output-correctness, language quality, media artifacts, access/quota/retention, and security/observability. |
| C3A-CP6-FM-002 | Harness points security/observability to docs/prose/static-snapshot content. | Command validator requires `tests/acceptance/test_checkpoint3_security_observability.py` and forbids docs/static/snapshot/prose/`rg`/`cat`. |
| C3A-CP6-FM-003 | Acceptance test checks style-only/status-only text instead of executing the local product/API path. | Positive test creates two projects, uploads/approves/ingests knowledge, generates runtime runs, checks trace/run/evaluation metadata, and requires bounded ops/status runtime counts. |
| C3A-CP6-FM-004 | Unsafe upload or missing approval is accepted as grounded evidence. | API calls must fail safely with `DOCUMENT_NOT_APPROVED`, `UNSAFE_DOCUMENT_CONTENT`, or `SECRET_LIKE_CONTENT` and no accepted script evidence. |
| C3A-CP6-FM-005 | Prompt-injection or unsupported claim text is accepted as grounded output. | API generation must return `PROMPT_INJECTION_DETECTED`, `UNSUPPORTED_PROJECT_FACT`, or visibly failed evaluation without raw unsafe text leakage. |
| C3A-CP6-FM-006 | Cross-project replay, cross-actor same-payload access attempts, or same-actor idempotency conflicts bypass actor/project/source-run checks. | Valid-looking mismatched IDs, a reused idempotency key under another actor with the same completed payload, and a conflicting same-actor idempotency payload must fail without replaying another actor/project response. |
| C3A-CP6-FM-007 | Observability evidence is static, self-attested only, or not bound to the runtime run. | Evidence contract requires an acceptance-runtime nonce, `trace_` metadata, source/run binding, evaluation checksum, runtime ops/status counts, and hosted-demo checksum mismatch rejection. |
| C3A-CP6-FM-008 | Failure output leaks raw payloads or sensitive markers. | Harness and acceptance checks redact security/observability fields and sensitive token/password/secret/api-key style strings including snake_case variants. |

## Fan-Out Review Findings

Manual adversarial fallback is used before implementation. Cross-model review is skipped in this autonomous execution context because the available review path is local adversarial review and test-driven negative canaries.

Disposition before implementation:

- Security/privacy boundary and synthetic-data posture: accepted. CP6 uses synthetic project knowledge only, clears provider env vars, rejects secret-like upload/prompt content, rejects unsafe prompt-injection content, and scans API-visible responses for raw canaries.
- Observability/redaction evidence design: accepted. CP6 requires trace/run/evaluation metadata, local/mock provider posture, redacted events, deterministic privacy/redaction checks, and bounded failure evidence tied to runtime runs.
- API/interface behavior: accepted. CP6 uses existing API-visible behavior and does not add new endpoints or schemas.
- Access/replay/idempotency preservation: accepted. CP6 exercises cross-project replay, same-payload cross-actor access denial with a reused idempotency key, conflicting same-actor idempotency replay, and hosted-demo source/evaluation checksum mismatch rejection.
- Output correctness and grounding preservation: accepted. CP6 preserves the CP1-CP5 grounded generation path before testing security and observability controls.
- Quota/retention regression risk: accepted as covered by CP5 preservation. CP6 does not edit quota or retention implementation and keeps CP5 in the acceptance harness.
- Performance impact: accepted. CP6 adds one focused pytest subprocess under the existing `timeout=120` boundary and keeps later performance probes planned.
- Test/quality/CI: accepted. Branch allowlist tests, preflight contract tests, harness anti-false-pass canaries, and executable acceptance coverage are required before PR.
- Governance/taste/scope: accepted. CP6 changes only harness, tests, and public governance/status docs. It keeps no provider setup, no hosted deployment, no cloned identity, and no production-readiness claim.

Final fan-out disposition before PR:

- Security/privacy reviewer finding: failed CP6 pytest assertions could echo bare canary strings before harness redaction. Disposition: accepted and fixed by adding whole-line CP6 canary and prompt-injection phrase redaction in `scripts/quality/check_checkpoint3_acceptance.py` with regression coverage in `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_security_observability_evidence_fields`.
- Review artifact wording finding: this file used pending/future final-review wording after implementation. Disposition: accepted and fixed in this section.
- API/replay reviewer finding: CP6 overclaimed request metadata and cross-actor idempotency replay semantics. Disposition: accepted and fixed by narrowing docs to API-visible trace/run/evaluation metadata plus acceptance-runtime nonce evidence, and by changing the cross-actor test to reuse the same completed payload while documenting it as cross-actor access denial with a reused idempotency key rather than idempotency replay provenance.
- Remaining final fan-out reviewers must be clean before human review; any later accepted finding must be fixed and rerun before the PR is marked ready.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue, branch, first-commit preflight, allowlist tests, acceptance test, harness, docs, validation, PR, CI watch, and approval-bound merge closeout. |
| spec-driven-development | Invoked | CP6 contract and failure matrix are defined before implementation. |
| test-driven-development | Invoked | Unit and acceptance regressions are added before harness implementation is completed. |
| source-driven-development | Invoked | Official FastAPI, Python subprocess, OWASP LLM security, and NIST SSDF sources are cited. |
| security-and-hardening | Invoked | Synthetic fixtures, provider env clearing, prompt-injection/secret rejection, public-safe error checks, and redaction canaries are part of CP6. |
| api-and-interface-design | Invoked | Existing API-visible project, document, run, hosted-demo, idempotency, and error shapes are asserted without adding API surfaces. |
| observability-and-instrumentation | Invoked | Runtime trace/run/evaluation metadata, local/mock provider posture, redacted events, and `/api/v1/ops/status` bounded counts are tested. |
| performance-optimization | Invoked | Probe remains focused and bounded by the existing subprocess timeout; dedicated performance probe remains planned. |
| code-review-and-quality | Invoked | Fan-out findings and dispositions are recorded and will be refreshed before human review. |
| doubt-driven-development | Invoked | False-pass, canned success, unbound evidence, unsafe upload, prompt-injection, unsupported claim, replay, and redaction risks are encoded as canaries. |
| taste-check | Invoked | No backend abstractions or dependencies are added for a test-harness slice. |
| git-workflow-and-versioning | Invoked | Issue `#265`, dedicated branch, and preflight-only first commit preserve workflow. |
| browser-testing-with-devtools | Rejected | Browser/UX scope remains planned and untouched. |

## Stop Rule

Stop and open a new issue if CP6 requires provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime changes, new dependencies, private data, private media, private planning files, secrets, or real personal data.
