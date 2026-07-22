# Issue #249 Checkpoint 3A Preflight

## Objective

C3-PR1 is a public-safe planning and guardrail PR for Checkpoint 3A:
Non-Cloned Product-Faithful Controlled Demo. It defines the next executable
contract before product implementation starts.

Checkpoint 3A must prove a controlled local demo first. The demo must accept
arbitrary approved project knowledge, generate a grounded walkthrough script,
show that audience/depth/style affects the output, produce fluent selected
language output for every language claimed in the UI, and keep citations,
evaluation, source-run, and claim-support binding intact across translation,
subtitles, audio, video or explicitly approved local product-quality equivalent,
downloads, and UI evidence.

This PR only plans and guards that contract. It may add the
`make checkpoint3-acceptance` failing-by-design gate skeleton, public docs, and
tests for the guardrails. It does not authorize product runtime implementation.

## Non-Goals

- `NONGOAL-C3A-RUNTIME-001`: no backend, frontend, provider, RAG, avatar,
  database, Docker, workflow, dependency, or product runtime implementation may
  be added beyond the smallest safe gate skeleton listed in this preflight.
- `NONGOAL-C3A-CLONE-001`: no cloned voice, cloned face, digital twin,
  real-person likeness, clone enrollment, clone consent capture, clone
  provenance implementation, private media, or real personal data is authorized.
- `NONGOAL-C3A-PROVIDER-001`: no provider setup, provider SDK, provider key,
  provider account work, dashboard configuration, paid plan activation, wallet
  funding, paid spend, real provider calls, or real provider payloads are
  authorized.
- `NONGOAL-C3A-LAUNCH-001`: no public URL, hosted deployment, public
  distribution, production-readiness claim, production durability claim,
  external reviewer access claim, or launch Go claim is authorized.

C3-PR1 must remain explicit: no cloned voice, no cloned face, no digital twin,
no real-person likeness, no public URL, no paid spend, no provider setup, no
real provider calls, and no production-readiness claim. Hindi must be not
romanized Hindi-only output and not English fallback.

## Changed-File Allowlist

Issue `#249` branch
`phase-1-closure-process-249-checkpoint3a-planning-guardrails` may change only:

- `docs/governance/preflights/issue-249.json`
- `docs/reviews/ISSUE_249_CHECKPOINT3A_PREFLIGHT.md`
- `docs/demo/REAL_MEDIA_HOSTED_DEMO_PLAN.md`
- `docs/QUALITY_GATES.md`
- `docs/STAGE_ISSUE_PLAN.md`
- `docs/STATUS.md`
- `Makefile`
- `scripts/quality/check_checkpoint3_acceptance.py`
- `scripts/quality/check_phase1_closure_docs.py`
- `tests/unit/test_checkpoint3_acceptance_gate.py`
- `tests/unit/test_phase1_closure_docs.py`

Near-match issue `#249` branches must fail closed. Backend, frontend, provider,
RAG, avatar, database, Docker, workflow, dependency, launch, and runtime product
paths remain outside this PR.

## Official Source Facts

Accessed date for source facts: 2026-07-22.

| ID | Source | Fact used by this PR |
|---|---|---|
| `SRC-C3A-GH-001` | `https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/using-keywords-in-issues-and-pull-requests` | GitHub pull requests and commits can close linked issues when merged if closing keywords are used. C3-PR1 PR text must therefore use public-safe reference wording unless closure is intentional. |
| `SRC-C3A-MAKE-001` | `https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html` | GNU Make `.PHONY` targets are explicit recipes not tied to same-named files. `make checkpoint3-acceptance` can be a named gate skeleton that fails loudly until implementation replaces the red state. |

## Checkpoint Sequence

1. Checkpoint 3A: Non-Cloned Product-Faithful Controlled Demo.
   Controlled local demo first, any approved project knowledge, grounded
   walkthrough script, selected-language fluency, derived-artifact binding,
   playable media or explicitly approved local product-quality equivalent,
   access/quota/retention/deletion/tombstone evidence, redacted observability,
   and security/performance/API/browser/output-correctness gates.
2. Checkpoint 3B: Cloned Identity Consent And Provenance.
   Planning and consent/provenance gates for cloned identity later. This does
   not start in C3-PR1.
3. Checkpoint 3C: Clone-Integrated Controlled Demo.
   Clone integration only after 3A evidence and 3B consent/provenance gates
   pass.
4. Production later.
   Production remains outside Checkpoint 3 and requires separate launch,
   durability, security, privacy, operations, access, and approval evidence.

## Checkpoint 3A Acceptance Matrix

| ID | Claim | Required future proof | Failure proof |
|---|---|---|---|
| `C3A-SCOPE-001` | C3-PR1 is planning and guardrails only. | Changed-file allowlist rejects unrelated files and near-match issue `#249` branches. | Add a backend, frontend, provider, Docker, workflow, dependency, or runtime path and observe the checker fail. |
| `C3A-FLOW-001` | Controlled local product-faithful demo path executes end to end. | API E2E creates a project, loads approved knowledge, retrieves context, generates a grounded walkthrough, evaluates unsupported claims, stores output, and exposes UI evidence. | A docs-only or fixture-only pass fails. |
| `C3A-KNOWLEDGE-001` | Demo accepts arbitrary approved project knowledge, not only a NarraTwin seed. | At least two synthetic approved non-NarraTwin project fixtures execute end to end with fixture-specific facts and unsupported-fact rejection. | Hardcoded seed wording or cross-project replay fails. |
| `C3A-AUDIENCE-001` | Audience/depth/style affects output without overriding grounding or safety. | Same source run executes materially different audience/depth/style inputs and assertions inspect generated text, not metadata only. | Metadata-only changes or unsupported safety override fail. |
| `C3A-LANG-UI-001` | Every language claimed in the UI has an executable acceptance case. | UI language list and backend supported-language list match; each claimed language runs through the API and browser path. | UI claims a language that backend rejects or never executes. |
| `C3A-LANG-HI-001` | Hindi output is fluent Hindi, not English fallback or romanized token substitution. | Hindi output must contain Devanagari, preserve citation markers, retain required project terms, and reject English fallback, mock translation, romanized Hindi-only output, mixed-script low-quality output, missing Devanagari, dropped citations, and mistranslated required terms. | `[hi] English text`, romanized-only Hindi, or marker-preserving but semantically unsupported output fails. |
| `C3A-BINDING-001` | Citations/eval/source-run/claim binding survives derived artifacts. | Translated script, subtitles, audio manifest, video manifest, downloads, and UI evidence expose matching `sourceRunId`, `multilingualRunId`, `targetLanguage`, `evaluationId`, checksums, citation indexes, context refs, and claim-support linkage. | Citation markers survive translation, but claim-support IDs/eval/source-run binding is lost. |
| `C3A-MEDIA-AUDIO-001` | Audio is playable or explicitly approved as a local product-quality equivalent. | Artifact manifest proves safe MIME, filename, checksum, schema, target language, disclosure, source-run binding, and playable validation or approved equivalent criteria. | Hidden real provider path, unsafe MIME, checksum mismatch, empty artifact, or unapproved placeholder fails. |
| `C3A-MEDIA-VIDEO-001` | Video artifact or local equivalent stays bound to the same approved run. | Video/equivalent manifest binds audio/script/source/eval/checksum and blocks stale source-run replay. | Video from one project/run replays against another project/run. |
| `C3A-ACCESS-001` | Controlled local access and quota behavior is explicit. | Local access gate, per-run/per-principal quota, quota reservation before artifact visibility, and quota refund/error paths are tested. | Anonymous/public URL claim, quota-after-visibility, or duplicate-use bypass fails. |
| `C3A-RETENTION-001` | Retention, deletion, and tombstone evidence are server-bound. | Server-bound tombstone ID/checksum, deletion evidence ID, terminal deleted state, and replay/export blocking after deletion are tested; caller-supplied tombstones are rejected. | Deleted artifacts remain downloadable, replayable, cached, or visible through stale source-run IDs. |
| `C3A-OBS-001` | Observability is redacted and bounded. | Logs/traces include only bounded fields such as `trace_id`, status/code, access outcome, quota outcome, retention/deletion state, artifact validation result, and checksums. They exclude raw uploads, prompts, scripts, transcripts, media bytes, URLs, invite secrets, cookies, tokens, provider keys, provider payloads, and private identifiers. | Raw user knowledge, generated script text, provider-shaped payloads, invite/access identifiers, or secret-like values appear in logs, API errors, persisted state, downloads, or browser-visible UI. |
| `C3A-SECURITY-001` | Uploaded docs, prompts, transcripts, and generated/provider-shaped outputs remain untrusted input. | Prompt-injection, unsafe filename/MIME, active content, unsafe URL, oversized artifact, duplicate JSON key, and output-encoding negatives fail closed. | User-controlled fields override grounding, call providers, expose secrets, or force unsupported claims. |
| `C3A-PERF-001` | Product-faithful local demo has explicit performance gates. | Acceptance records bounded local latency and artifact validation limits for the approved stack and fails on timeout/backpressure conditions. | Long-running paths pass without timeout, budget, or queue/backpressure evidence. |
| `C3A-BROWSER-001` | Browser E2E proves real local stack behavior. | Real-browser E2E with no success-path interception exercises UI -> API -> local stack and validates artifacts/evidence from network responses and rendered state. | Route interception or mocked success is used while claiming real-stack output correctness. |
| `C3A-OUTPUT-CORRECTNESS-001` | Output-correctness executes rather than reads. | The acceptance gate calls or replays the local API/demo pipeline, decodes artifacts, parses subtitles/manifests, and asserts actual content and bindings. | A checker that greps docs for planned phrases fails canary tests. |

## Checkpoint 3 Acceptance Gate

`make checkpoint3-acceptance` is intentionally failing-by-design in C3-PR1. It
must list these planned probes and return nonzero until implementation issues
create the executable acceptance suite:

- API E2E:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_api_e2e.py -q`
- language quality:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_language_quality.py -q`
- media artifacts:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_media_artifacts.py -q`
- access/quota/retention:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_access_quota_retention.py -q`
- security/observability:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_security_observability.py -q`
- performance:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_performance.py -q`
- real-browser E2E with no success-path interception:
  `NARRATWIN_REAL_STACK=1 NARRATWIN_CP3_PRODUCT_FAITHFUL=1 npm --prefix frontend run test:smoke -- --config=frontend/playwright.checkpoint3.config.ts`
- output-correctness that executes rather than reads:
  `NARRATWIN_CP3_PRODUCT_FAITHFUL=1 uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q`

## Old-Behavior and Failure Proof

Old behavior is not adequate for Checkpoint 3A because the existing accepted
state proves a local/mock checkpoint, not a product-faithful non-cloned
controlled demo.

Public-safe old-behavior failures the future acceptance suite must reject:

- NarraTwin-only or hardcoded demo seed behavior passes without arbitrary
  approved project knowledge.
- Audience/depth/style request fields change metadata only while generated text
  stays materially the same.
- A mock translation like `[hi] English text...` passes as Hindi.
- Romanized-only Hindi passes because the gate checks only `targetLanguage=hi`.
- Citation markers survive translation, but claim-support IDs/eval/source-run
  binding is lost in subtitles, audio/video manifests, downloads, or UI
  evidence.
- Mock/local media manifests or placeholders pass as playable media without
  explicit owner-approved product-quality equivalent criteria.
- Local/fake hosted access evidence is mistaken for public URL, hosted launch,
  external reviewer access, or production-readiness evidence.
- Browser E2E intercepts success responses and never proves the real local UI
  -> API -> artifact path.
- Output-correctness reads planning docs or snapshots rather than executing or
  replaying generated artifacts and manifests.

## Child Issue Breakdown

Public-safe child issues after C3-PR1 should be created as separate slices:

| Child | Scope | Required first proof |
|---|---|---|
| C3A-API | API E2E and approved project knowledge fixture contract. | Failing tests for two approved non-NarraTwin fixtures and cross-project replay. |
| C3A-LANGUAGE | UI/backend claimed-language contract and language-quality gates. | Negative Hindi cases for English fallback, romanized-only output, mixed-script low quality, dropped citations, and mistranslated required terms. |
| C3A-BINDING | Citation/eval/source-run/claim-support binding across translation, subtitles, media manifests, downloads, and UI evidence. | Stale checksum/source-run and missing claim-support negatives. |
| C3A-MEDIA | Playable audio/video artifact or explicitly approved local product-quality equivalent. | Artifact schema, MIME, checksum, disclosure, and stale-run replay negatives. |
| C3A-ACCESS-RETENTION | Access, quota, retention, deletion, and tombstone evidence. | Quota-before-visibility, terminal deletion, caller-tombstone rejection, and replay/export blocking after deletion. |
| C3A-SECURITY-OBS | Untrusted input handling and redacted observability. | Prompt-injection, unsafe artifact, and raw-data leak regression tests for logs, traces, API errors, downloads, persisted state, and UI. |
| C3A-PERF-BROWSER | Performance and real-browser E2E with no success-path interception. | Timeout/backpressure negatives and browser proof from real local stack network and rendered artifacts. |
| C3A-OUTPUT-CORRECTNESS | Executable output-correctness runner. | Canary that fails if checker is replaced by docs/prose scanning. |

## Fan-Out Review Findings and Dispositions

| Review area | Finding | Disposition |
|---|---|---|
| output-correctness | Output-correctness can falsely pass by reading docs or snapshot text. | `C3A-OUTPUT-CORRECTNESS-001` requires executing or replaying the local API/demo pipeline, decoding artifacts, parsing subtitles/manifests, and asserting actual content and binding. |
| multilingual quality | Hindi can pass as English fallback, romanized substitution, or marker-preserving low-quality text. | `C3A-LANG-HI-001` requires Devanagari, fluent selected-language behavior, negative Hindi fixtures, citation preservation, and required project-term handling. |
| security/privacy | Uploaded knowledge, prompts, transcripts, and provider-shaped outputs are untrusted and can leak through logs, errors, artifacts, or UI. | `C3A-SECURITY-001` and `C3A-OBS-001` require prompt-injection negatives and bounded telemetry only. |
| API/interface | UI and backend language claims can drift, and derived artifacts can lose source-run/eval/claim binding. | `C3A-LANG-UI-001` and `C3A-BINDING-001` require executable API/browser proof and shared identifiers across artifacts. |
| UX/demo flow | A local placeholder can be misread as product-quality media. | `C3A-MEDIA-AUDIO-001` and `C3A-MEDIA-VIDEO-001` require playable validation or explicit local-equivalent criteria. |
| access/quota/reliability/retention | Quota can be enforced after visibility, and deleted artifacts can remain replayable. | `C3A-ACCESS-001` and `C3A-RETENTION-001` require reservation before visibility, server-bound tombstones, and replay/export blocking after deletion. |
| observability/redaction | Trace evidence can leak raw uploads, scripts, provider-shaped payloads, URLs, invite data, cookies, tokens, or keys. | Redaction markers are part of the preflight and future acceptance gate. |
| performance | Long-running local artifact paths can pass without timeout or backpressure evidence. | `C3A-PERF-001` requires bounded local latency and timeout/backpressure negatives. |
| test/quality/CI | A branch can drift into implementation or unrelated files unless the allowlist is exact. | `C3A-SCOPE-001` adds exact changed-file allowlist and near-match branch regression tests. |
| governance/taste/scope | C3A could be collapsed into clone, provider, hosted, or production scope. | Non-goals are explicit and checked; Checkpoint 3B, Checkpoint 3C, and production later remain separate. |

Sub-agents were available and used for public-safe read-only fan-out where
possible. Any uncovered angles are handled as manual adversarial fallback in
this table before implementation and must be repeated before human review.

## Skill and Evidence Ledger

| Skill or review mode | Invoked or rejected | Evidence |
|---|---|---|
| planning-and-task-breakdown | Invoked | C3A sequence, acceptance matrix, child issue breakdown, and stop rule are explicit. |
| spec-driven-development | Invoked | Positive claims and negative invariants are represented by stable `C3A-*` and `NONGOAL-C3A-*` IDs. |
| test-driven-development | Invoked | Failing-by-design gate and regression tests define failure before implementation. |
| source-driven-development | Invoked | Official GitHub and GNU Make source facts are cited with accessed date. |
| security-and-hardening | Invoked | Untrusted input, no provider egress, no clone/likeness, deletion/tombstone, and redaction gates are explicit. |
| api-and-interface-design | Invoked | API/browser/language/artifact binding IDs define interface invariants before implementation. |
| observability-and-instrumentation | Invoked | Bounded telemetry and redaction fields are specified. |
| performance-optimization | Invoked | Performance probe and timeout/backpressure failure proof are part of the gate. |
| browser-testing-with-devtools / web app testing | Invoked | Future real-browser E2E must use no success-path interception. |
| code-review-and-quality | Invoked | Fan-out findings and dispositions are recorded before implementation. |
| doubt-driven-development | Invoked | Old-behavior failure proof attacks false passes. |
| taste-check | Invoked | Scope stays small: docs, gate skeleton, and tests only. |
| git-workflow-and-versioning | Invoked | Issue-linked branch and preflight-only first commit are preserved. |

## Stop Rule

Stop and open a new issue before proceeding if work requires backend, frontend,
provider, RAG, avatar, database, Docker, dependency, CI workflow, runtime
product implementation, cloned identity, real-person likeness, private media,
provider setup, provider key handling, real provider calls, public URL, hosted
deployment, paid spend, public distribution, or production-readiness claims.
