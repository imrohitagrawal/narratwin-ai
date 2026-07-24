# Issue 278 C3A-R2 Review Evidence

## Pre-Implementation Review

The first branch commit added only
`docs/governance/preflights/issue-278.json`. The red test pass then introduced
the full-project fixture and regression tests before Stage 6 constants,
dispatcher integration, and fixture translation support were added.

Initial red evidence:

- importing `LANGUAGE_CATALOG_VERSION` from `backend.app.stage6` failed before
  the catalog lock existed
- `scripts/quality/check_checkpoint3_acceptance.py` dispatched eight probes
  before the full-project multilingual corpus probe was registered
- the issue-specific Phase 1 closure allowlist failed closed for near-match
  branches

## Fan-Out Findings

Three read-only sub-agent adversarial reviews were run before human review.
Their high-signal findings and dispositions are recorded here.

| Review area | Finding | Disposition |
|---|---|---|
| public/private boundary | Corpus and docs are synthetic and public-safe; no private strategy, real personal data, real media, private media, provider payload/output, or cloned identity material is used. | Kept in fixture provenance and PR non-goals. |
| arbitrary-project overclaim risk | The gate proves a governed corpus, not arbitrary-project translation quality. | Repeated in preflight, reports, status, and PR body. |
| provider/public-demo/production exclusion | No provider setup, hosted deployment, public URL, real provider calls, or production-readiness claim is included. | Blocked by preflight and stop rule. |
| full-project fixture adequacy | Fixture has multiple documents, multiple sections, six transcript segments, seven cited claims, seven claim supports, four artifacts, and a multi-document claim. | Enforced by `assert_fixture_thresholds`. |
| all-supported-language evidence requirement | Every supported catalog row must be `SUPPORTED` / `LOCAL_DEMO_FIXTURE` / `CHECKPOINT3A_EXHAUSTIVE` and must appear in the generated matrix. | Enforced by supported tag equality and report rows. |
| representative language-class insufficiency | Representative class coverage is not enough by itself. | Every supported language is executed; class checks are additional. |
| Priority 2 refusal | Planned local-demo languages must refuse. | Enforced by `LOCAL_DEMO_LANGUAGE_UNSUPPORTED` checks. |
| stale evidence | Fixture, expected output, catalog, validator, artifact schema, and report schema changes must fail. | Enforced by stale evidence mutation tests. |
| metadata-only/artifact-only false pass | Empty transcript success must fail even if metadata or artifacts exist. | Covered by C3A-R2-FM-015 and C3A-R2-FM-016. |
| citation/source-span continuity | Citation order alone is insufficient without matching source spans. | Covered by citation drift and citation id preservation without source-span preservation mutations. |
| claim-support continuity | Claim supports must remain bound to the same source evidence. | Covered by missing claim-support binding mutation and positive parity rows. |
| native-script/RTL/CJK/Latin edge cases | Hindi, RTL, CJK, and Latin-script checks need class-specific conditions beyond generic script flags. | Enforced by class-specific acceptance assertions. |
| UI/stored/export/report parity | Transcript body, metadata, durable report, and exported artifacts must agree. | Enforced by surface parity assertions and report rows. |
| guardrail allowlist behavior | Exact #278 branch may change only approved files; near-match branches fail closed. | Covered by unit tests and preflight JSON. |
| status/traceability/quality-gate consistency | Status, traceability, quality gates, and stage plan must mention the new gate without closing #249. | Updated in this PR. |
| test/quality/CI | Local targeted and full quality commands must pass before ready for review. | Validation evidence recorded below. |
| governance/taste/scope | Changes are limited to the gate, fixture, reports, catalog locks, and docs. | No provider/frontend/dependency/workflow expansion. |

Sub-agent findings that required changes:

| Finding | Disposition |
|---|---|
| CI did not execute the new C3A-R2 probe because `make quality` only ran the Phase 1 static gate. | `scripts/quality/check_phase1_closure_docs.py` now executes `uv run pytest tests/acceptance/test_checkpoint3_full_project_multilingual.py -q` on the exact issue `#278` branch, so PR CI's `make quality` path runs the same full-project gate. |
| `docs/STATUS.md` marked issue `#278` as already satisfied before merge approval. | StatusStateV1 now keeps current status `c3a-r2-active` and says issue `#278` will be satisfied by this PR when merged. |
| `expectedOutputHash` did not cover target-language outputs. | `expected_output_hash` now includes deterministic target transcript rows for every supported language, including target text, citations, source refs, context refs, and claim-support ids. |
| Required durable report artifacts were generated under ignored `reports/` paths. | The two full-project report files are force-added as checked artifacts in this PR. |
| Source-span continuity used opaque citation-only IDs. | Context refs and claim-support ids now encode the fixture `sourceRefs`, including the multi-document segment. |
| Metadata-only and artifact-only false-pass cases were empty-transcript duplicates. | The gate now mutates API/artifact success-shaped payloads and requires body/artifact parity assertions to reject them. |
| Artifact/export count was copied from a fixture threshold. | The gate now counts actual API artifacts and decodes translated script, subtitles, voice manifest, and metadata content. |
| Heading-only coverage used the wrong segment. | The gate now mutates `seg_004`, the fixture row designed to expose heading-only, partial-section, and missing-body translation. |
| Class-specific checks were too thin. | The gate now adds per-segment Hindi native-script checks, RTL artifact direction checks, Korean-specific Hangul checks, Japanese/Chinese spacing checks, and existing Latin leakage/diacritic checks. |
| UI parity was overclaimed for this backend corpus gate. | The preflight now states that C3A-R2 validates the Stage 6 API/artifact body consumed by UI surfaces and relies on prior Checkpoint 3A browser evidence for direct UI rendering. |

## PR 277 Regression Mapping

Generalized assumptions:

- supported local-demo multilingual output must include source English, target
  text, English reference, citations, context refs, and claim supports for each
  body segment
- native script alone is not sufficient; deterministic corpus output and
  source-span binding must pass
- unsupported or planned languages must refuse locally instead of reporting
  success

Not generalized:

- arbitrary uploaded knowledge-document translation quality is not proved
- provider translation quality is not proved
- hosted/public demo behavior is not proved
- production-readiness is not proved

Cases that would have caught the earlier failure mode sooner:

- the multi-document claim row would have exposed evidence-binding assumptions
  that only held for a single source
- the missing-body/heading-only row would have rejected metadata-only and
  heading-only success
- the stale evidence locks would have forced catalog and validator updates to
  refresh the checked report
- the all-supported-language matrix would have prevented class-representative
  evidence from standing in for every supported catalog entry

## Validation Evidence

- `uv run pytest tests/unit/test_guardrails_check.py -q` -> passed.
- `uv run pytest tests/unit/test_phase1_closure_docs.py -q` -> passed.
- `uv run pytest tests/unit/test_checkpoint3_acceptance_gate.py -q` -> `49 passed`.
- `uv run pytest tests/unit/test_stage6_multilingual.py -q` -> passed.
- `uv run pytest tests/api/test_stage6_multilingual_api.py -q` -> `18 passed`.
- `uv run pytest tests/acceptance/test_checkpoint3_output_correctness.py -q` -> `7 passed`.
- `uv run pytest tests/acceptance/test_checkpoint3_full_project_multilingual.py -q` -> `7 passed`.
- `python3 scripts/guardrails_check.py` -> `All NarraTwin AI repository guardrails passed.`
- `python3 scripts/quality/check_phase1_closure_docs.py` -> `Phase 1 Closure governance quality checks passed.`
- `python3 scripts/quality/check_checkpoint3_acceptance.py` -> `Checkpoint 3 acceptance complete: 9 passed, 0 planned, 0 failed.`
- `make quality` -> `Phase 1 Closure governance quality checks passed.`
- `uv run ruff check scripts tests` -> `All checks passed!`
- `uv run mypy scripts tests` -> `Success: no issues found in 67 source files`
- `make dependency-audit` -> no known vulnerabilities; frontend audit found 0 vulnerabilities.
- `make security` -> Bandit no issues, Semgrep repository scan 0 findings, canary contract passed, Gitleaks no leaks found.
- `make secrets-scan` -> guardrails passed; dependency security, Semgrep, and Gitleaks completed with no blocking findings.
- `make eval` -> eval smoke report written to `reports/eval-smoke/stage5-eval-smoke-report.json` and `docs/EVAL_REPORT.md`.
- `make ci` -> exited 0 after stage quality, ruff, frontend lint, mypy, frontend typecheck, `2108` backend unit tests, `109` API tests, frontend tests/build/smoke, eval smoke, dependency security, Docker build/scan consensus pass, and frontend Lighthouse wrapper.

## Final Clean Fan-Out

Final clean fan-out: all three adversarial sub-agent reviews completed, all
high-severity findings were either fixed in executable evidence or narrowed in
public-safe wording, and no remaining finding blocks human review. The remaining
residual risks below are explicit non-goals rather than hidden acceptance
claims.

## Residual Risks

- The gate proves deterministic local/mock corpus behavior only.
- The checked fixture is synthetic and public-safe; it is intentionally not a
  private strategy, provider, public demo, or production dataset.
- Future raw uploaded knowledge-document translation claims require a separate
  issue and equivalent executable evidence.
