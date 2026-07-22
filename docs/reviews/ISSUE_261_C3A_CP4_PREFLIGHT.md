# Issue 261 C3A-CP4 Preflight

## Objective

C3A-CP4 implements the fourth Checkpoint 3A child implementation checkpoint for public tracker issue `#249` and child issue `#261`: executable media artifacts for the local/mock controlled demo path.

The claim is deliberately narrow: `make checkpoint3-acceptance` dispatches the media artifacts probe as executable runtime API behavior, and that probe evaluates API-visible local/mock Stage 6 and Stage 7 artifacts. This work does not complete Checkpoint 3A.

Positive claim IDs:

| ID | Claim |
| --- | --- |
| C3A-CP4-HARNESS-001 | The Checkpoint 3 acceptance harness implements the `media artifacts` probe through `uv run pytest tests/acceptance/test_checkpoint3_media_artifacts.py -q`, with `shell=False`, `timeout=120`, and bounded/redacted failure output. |
| C3A-CP4-MEDIA-001 | The acceptance test creates approved synthetic projects, uploads approved synthetic non-NarraTwin project knowledge, ingests/chunks/stores it, generates a grounded walkthrough, creates Stage 6 `translatedScript`, `subtitles`, and `voiceManifest` artifacts, captures Stage 7 synthetic-avatar consent, creates Stage 7 `demoExport`, `renderManifest`, and `videoExportPlaceholder` artifacts, and verifies API-visible idempotent replay. |
| C3A-CP4-RUNTIME-001 | Media artifact quality is checked from runtime API response fields including `acceptedScriptText`, `contextRefs`, `claimSupports`, `citationIndex`, `sourceEvaluationChecksum`, `contentBase64`, `checksum`, `mimeType`, `fileName`, local/mock provider posture, and `/api/v1/ops/status` durability counts. |
| C3A-CP4-NONGOAL-001 | Later access/quota/retention, security/observability, performance, and real-browser E2E probes remain planned. |

## Scope

In scope:

- `scripts/quality/check_checkpoint3_acceptance.py`
- `tests/acceptance/test_checkpoint3_media_artifacts.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_phase1_closure_docs.py`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `docs/TRACEABILITY.md`
- `docs/governance/preflights/issue-261.json`
- `docs/reviews/ISSUE_261_C3A_CP4_PREFLIGHT.md`

Out of scope: provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, public distribution, production-readiness claims, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime deployment, new dependencies, secrets, private media, and real personal data.

The PR may bundle repository-ledger cleanup for PR `#260` and issue `#259` because this is a substantive child checkpoint, not a standalone status-only follow-up.

## Source Facts

Accessed date: 2026-07-22.

| Source | Fact used |
| --- | --- |
| https://fastapi.tiangolo.com/tutorial/testing/ | FastAPI supports `TestClient` for ordinary pytest functions and assertions against app behavior. |
| https://fastapi.tiangolo.com/reference/testclient/ | `TestClient` is the local in-process API client used for deterministic acceptance tests. |
| https://docs.python.org/3/library/subprocess.html#subprocess.run | `subprocess.run` supports argument sequences, timeout, environment, stdout/stderr capture, and explicit `shell=False` execution. |
| https://docs.python.org/3/library/base64.html | Python's standard `base64` module decodes Base64-encoded API artifact payloads locally for deterministic validation. |
| https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue | GitHub supports linking pull requests to issues with issue references; the parent tracker is reference-only and must remain open. |
| https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html | Make phony targets are appropriate for command targets that do not represent files. |

Repository facts:

- CP1 API E2E, CP2 output-correctness, and CP3 language-quality already execute the local product/API path.
- Stage 6 local/mock artifacts are text/script, subtitle, and JSON voice-manifest artifacts; CP4 does not require real audio.
- Stage 7 local/mock artifacts are HTML demo export, JSON render manifest, and JSON video-export placeholder artifacts; CP4 does not require real video.
- The current API-visible replay proof is idempotent duplicate POST replay, not a documented GET retrieval implementation.

## Positive Claims

| ID | Evidence target | Status |
| --- | --- | --- |
| C3A-CP4-HARNESS-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_dispatches_api_probe_and_keeps_later_probes_planned` | planned before implementation |
| C3A-CP4-MEDIA-001 | `tests/acceptance/test_checkpoint3_media_artifacts.py::test_checkpoint3_media_artifacts_executes_runtime_api_artifact_path` | planned before implementation |
| C3A-CP4-RUNTIME-001 | API-visible idempotent replay, artifact payload decoding, source/evaluation binding, provider posture, and `/api/v1/ops/status` assertions | planned before implementation |
| C3A-CP4-REPLAY-001 | Stage 6 and Stage 7 idempotent replay returns the same stored artifact evidence | planned before implementation |
| C3A-CP4-REDACTION-001 | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_redacts_runtime_evidence_fields` | preserved from implemented harness coverage |

## Negative Invariants

| ID | Invariant | Evidence target |
| --- | --- | --- |
| C3A-CP4-FALSEPASS-001 | The media-artifacts probe must not pass by grepping docs, reading planning prose, checking static snapshots, or using canned success files. | `tests/unit/test_checkpoint3_acceptance_gate.py::test_checkpoint3_acceptance_rejects_static_media_artifacts_probe_command` |
| C3A-CP4-ARTIFACT-001 | Artifact-shape-only evidence without decoded content, valid checksum, safe filename, and expected `mimeType` fails media-artifact quality. | `tests/acceptance/test_checkpoint3_media_artifacts.py::test_checkpoint3_media_artifacts_rejects_checksum_or_mime_mismatch` |
| C3A-CP4-BINDING-001 | Media artifacts without source-run, `sourceEvaluationChecksum`, context, citation, and claim-support binding fail. | `tests/acceptance/test_checkpoint3_media_artifacts.py::test_checkpoint3_media_artifacts_rejects_artifact_shape_without_source_binding` |
| C3A-CP4-POSTURE-001 | Artifacts that overclaim real media binaries, external provider posture, or cloned identity fail. | `tests/acceptance/test_checkpoint3_media_artifacts.py::test_checkpoint3_media_artifacts_rejects_real_media_or_clone_overclaim` |

## Failure Matrix

| ID | Failure mode | Guard |
| --- | --- | --- |
| C3A-CP4-FM-001 | Harness leaves media artifacts planned. | Implemented probe list requires `API E2E`, `language quality`, `media artifacts`, and `output-correctness that executes rather than reads`. |
| C3A-CP4-FM-002 | Harness points media artifacts to docs/prose/static/snapshot content. | Command validator requires `tests/acceptance/test_checkpoint3_media_artifacts.py` and forbids docs/static/snapshot/prose/`rg`/`cat`. |
| C3A-CP4-FM-003 | Acceptance test checks canned artifacts instead of executing the local product/API path. | Positive test creates projects, uploads knowledge, approves, ingests, generates, creates Stage 6 and Stage 7 artifacts, replays, and checks ops counts. |
| C3A-CP4-FM-004 | Artifact response has plausible fields but malformed content. | Base64 decode, checksum, `mimeType`, and safe `fileName` checks run against runtime artifacts. |
| C3A-CP4-FM-005 | Artifacts are valid files but not bound to the source run. | Stage 6 and Stage 7 evidence must include source run, evaluation checksum, context refs, citation indexes, and claim-support IDs. |
| C3A-CP4-FM-006 | Media artifact checks overclaim real audio/video or cloned identity. | Provider posture and artifact fields must remain local/mock, no real media binary overclaim, and no cloned identity. |
| C3A-CP4-FM-007 | Assertion failures leak generated bodies or artifact payloads. | Public-safe synthetic fixtures plus bounded/redacted harness summaries. |
| C3A-CP4-FM-008 | CP4 overclaims access/quota/retention, security/observability, performance, browser, hosted, provider, cloned identity, or production readiness. | Scope and status docs keep those probes planned or forbidden. |

## Fan-Out Review Findings

Manual adversarial fallback is used before implementation.

Disposition:

- Media-artifacts/harness review: implement the probe, add a media-specific command validator, and add a static media-artifacts canary.
- API/interface review: CP4 uses local FastAPI `TestClient`; API-visible idempotent replay is the stored output/evidence proof. It does not claim implemented GET run retrieval.
- Output correctness/grounding review: CP4 requires Stage 4 source `claimSupports`, `contextRefs`, and citation indexes to remain bound through Stage 6 and Stage 7 artifacts.
- Security/privacy/observability review: CP4 uses public synthetic content only, clears provider/state env vars, keeps providers local/mock, checks `/api/v1/ops/status`, and avoids assertion messages that dump raw artifact payloads.
- Access/quota/reliability/retention review: these remain later Checkpoint 3A probes; CP4 checks only idempotent artifact replay and bounded local record counts.
- Performance review: CP4 adds one focused executable pytest probe under the existing `timeout=120` subprocess boundary.
- Governance/taste/scope review: exact issue `#261` allowlist and preflight checker are added; no backend, frontend, provider, dependency, Docker, or workflow scope is touched.
- UX/demo flow review: no browser/frontend scope is touched, so browser-testing-with-devtools is rejected for CP4.

Cross-model review is skipped in this autonomous execution context because the available review path is same-repository sub-agent fan-out and local adversarial review.

## Skill And Tool Selection Ledger

| Skill/tool | Decision | Evidence or prevented action |
| --- | --- | --- |
| planning-and-task-breakdown | Invoked | Sequenced issue, branch, first-commit preflight, allowlist tests, harness, acceptance test, docs, validation, PR. |
| spec-driven-development | Invoked | CP4 contract and failure matrix defined before implementation. |
| test-driven-development | Invoked | Unit and acceptance regressions are added before harness implementation is completed. |
| source-driven-development | Invoked | Official FastAPI, Python subprocess, Python base64, GitHub issue linking, and GNU Make docs were consulted. |
| security-and-hardening | Invoked | Public synthetic fixtures, local/mock provider posture, artifact payload validation, and redaction checks. |
| api-and-interface-design | Invoked | API-visible replay and artifact evidence fields are asserted without adding or overclaiming API surfaces. |
| observability-and-instrumentation | Invoked | Trace/provider/ops evidence and redaction behavior are part of CP4. |
| performance-optimization | Invoked | Probe remains focused and bounded by the existing timeout. |
| code-review-and-quality | Invoked | Fan-out findings and local review are recorded. |
| doubt-driven-development | Invoked | False-pass and overclaim risks are encoded as canaries. |
| taste-check | Invoked | No backend abstractions or dependencies are added for a test-harness slice. |
| git-workflow-and-versioning | Invoked | Issue `#261`, dedicated branch, and preflight-only first commit preserve workflow. |
| browser-testing-with-devtools | Rejected | Browser/UX scope remains planned and untouched. |

## Stop Rule

Stop and open a new issue if CP4 requires provider setup, provider SDKs, real provider calls, paid spend, hosted deployment, public URL, cloned voice, cloned face, digital twin, real-person likeness, Checkpoint 3B, Checkpoint 3C, Product Mode 2, browser/frontend implementation, Docker/runtime changes, new dependencies, private data, private media, secrets, or real personal data.
