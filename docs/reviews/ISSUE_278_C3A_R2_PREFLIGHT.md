# Issue 278 C3A-R2 Preflight

## Objective

C3A-R2 proves a governed full-project multilingual correctness acceptance gate
for the local/mock Checkpoint 3A product path. The gate exists so a future PR
cannot treat full-project multilingual correctness as chat-only context.

Durable scope marker: C3A-R2-CATALOG-001 anchors support claims to
`backend/app/stage6.py` catalog fields: `LANGUAGE_CATALOG`,
`LANGUAGE_CATALOG_BY_TAG`, `SUPPORTED_LANGUAGES`,
`local_demo_support_status`, `provider_support_status`, and
`test_coverage_level`.

## Scope

Allowed work is limited to issue `#278` governance, tests, local/mock Stage 6
catalog locks, the public-safe synthetic corpus, checked reports, and the
Checkpoint 3 acceptance dispatcher.

This does not prove arbitrary-project translation quality. This does not prove
provider quality. This does not authorize hosted/public demo, provider setup,
paid spend, cloned identity runtime, real media, public distribution, or
production readiness. The raw uploaded knowledge-document translation API
surface remains out of scope unless a future issue adds equivalent executable
evidence.

## Positive Claims

- C3A-R2-FULLPROJECT-001: the gate uses
  `tests/fixtures/checkpoint3_full_project_multilingual_corpus.json`, not a
  short snippet.
- C3A-R2-ALL-SUPPORTED-001: every language in `SUPPORTED_LANGUAGES` must have a
  current full-project corpus row when catalog fields mark it `SUPPORTED`,
  `LOCAL_DEMO_FIXTURE`, and `CHECKPOINT3A_EXHAUSTIVE`.
- C3A-R2-PARITY-001: the API transcript surface consumed by the UI, stored
  output, metadata, durable report, and exported/downloaded artifacts agree for
  source English, target text, English reference, citations, context refs, and
  claim-support ids. The phrase "UI transcript, stored output, metadata,
  durable report, and exported/downloaded artifacts agree" is not accepted from
  metadata flags alone; C3A-R2 validates the Stage 6 API/artifact body content
  and relies on prior Checkpoint 3A browser evidence for direct UI rendering.
- The fixture includes Hindi/Devanagari native-script coverage, RTL direction
  coverage, CJK segmentation and wrapping checks, and Latin-script diacritic and
  leakage checks.
- Priority 2 refusal remains required unless equivalent evidence is introduced.

## Failure Matrix

Each failure row reports language tag, fixture row, segment id, source ref,
expected condition, observed violation, and remediation category.

| ID | Required rejection |
|---|---|
| C3A-R2-FM-001 | partial project translation |
| C3A-R2-FM-002 | missing document translation |
| C3A-R2-FM-003 | missing section translation |
| C3A-R2-FM-004 | single-segment partial success |
| C3A-R2-FM-005 | heading-only success |
| C3A-R2-FM-006 | untranslated English fallback for non-English targets |
| C3A-R2-FM-007 | wrong script |
| C3A-R2-FM-008 | romanized fallback where native script is expected |
| C3A-R2-FM-009 | illegitimate source-term leakage |
| C3A-R2-FM-010 | broader, narrower, or altered translated claims that lose source support |
| C3A-R2-FM-011 | citation drift |
| C3A-R2-FM-012 | citation id preservation without source-span preservation |
| C3A-R2-FM-013 | missing source, target, or English reference |
| C3A-R2-FM-014 | missing context ref or claim-support binding |
| C3A-R2-FM-015 | metadata-only success |
| C3A-R2-FM-016 | artifact-only success |
| C3A-R2-FM-017 | stale coverage rows or planned-language fake success |
| C3A-R2-FM-018 | marking a planned language supported, or removing supported-language coverage, without complete evidence or demotion/refusal |

## Stale Evidence Definition

C3A-R2-STALENESS-001 defines stale evidence as any of:

- fixture hash changed
- expected-output hash changed
- language catalog version changed
- validator version changed
- artifact schema version changed
- report schema changed

Any stale lock must fail before a supported-language success is accepted.

## Matrix-To-Test Mapping

- `tests/acceptance/test_checkpoint3_full_project_multilingual.py` executes the
  full-project positive corpus path, false-pass mutation set, stale evidence
  mutations, and Priority 2 refusal checks.
- `tests/unit/test_checkpoint3_acceptance_gate.py` proves
  `scripts/quality/check_checkpoint3_acceptance.py` dispatches the new
  full-project multilingual corpus probe through `make checkpoint3-acceptance`.
- `tests/unit/test_phase1_closure_docs.py` proves the branch allowlist,
  required preflight markers, and near-match branch fail-closed behavior.
- Checked outputs are
  `reports/checkpoint3-multilingual/full-project-coverage-matrix.json` and
  `reports/checkpoint3-multilingual/full-project-correctness-report.json`.

## Full-Project Corpus

The corpus is public-safe and synthetic. Required thresholds cover document
count, section count, transcript segment count, cited claim count,
claim-support count, artifact/export count, and coverage row count.

Fixture adequacy:

- at least three documents and seven sections
- at least six transcript segments
- at least seven cited claims and seven claim supports
- at least four exported artifacts
- at least 450 coverage rows
- at least one translated segment with support spanning multiple source
  documents
- at least one segment that exposes heading-only, partial-section, or
  missing-body translation
- provenance notes exclude private strategy, real personal data, real media,
  private media, provider payload/output, and cloned identity material

## Fan-Out Review Plan

Manual adversarial fallback is required if sub-agents are unavailable. The
review must cover public/private boundary, arbitrary-project overclaim risk,
provider/public-demo/production exclusion, full-project fixture adequacy,
all-supported-language evidence, representative language-class insufficiency,
Priority 2 refusal, stale evidence, metadata-only success, artifact-only
success, citation/source-span continuity, claim-support continuity,
native-script/RTL/CJK/Latin edge cases, UI/stored/export/report parity,
guardrail allowlist behavior, status/traceability/quality-gate consistency,
test/quality/CI, and governance/taste/scope.

Final clean fan-out must be recorded before human review.

## Skill And Tool Selection Ledger

Invoked skills: planning-and-task-breakdown, spec-driven-development,
test-driven-development, source-driven-development, security-and-hardening,
api-and-interface-design, observability-and-instrumentation,
code-review-and-quality, doubt-driven-development, taste-check, and
git-workflow-and-versioning.

Rejected options:

- provider setup or provider calls: blocked by issue boundary
- hosted/public demo: blocked by issue boundary
- frontend or public URL work: not needed for this gate
- new dependencies or third-party data: not needed because the corpus is
  synthetic and public-safe

Evidence must come from executable tests, generated reports, guardrails, and CI;
skill invocation alone is not evidence.

## Stop Rule

Stop and open a new issue if the work requires provider setup, paid spend,
hosted/public demo, real media, cloned identity runtime, public distribution,
production-readiness claims, private strategy, raw provider payload/output,
private media, real personal data, or raw uploaded knowledge-document
translation API claims without equivalent executable evidence.
