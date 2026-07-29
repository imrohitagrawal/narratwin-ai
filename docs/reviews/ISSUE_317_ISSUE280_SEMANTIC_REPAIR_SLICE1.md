# Issue 317: Issue 280 Semantic Repair Slice 1

## Pre-implementation evidence

- Controlling authority: Issue #317.
- Verified base: `5fd7840c2219f9bed578e61c0933b2f9c7f45114`.
- First branch commit: `5d5dbd5` contains only GovernancePreflightV1.
- Frozen contract comment: <https://github.com/imrohitagrawal/narratwin-ai/issues/317#issuecomment-5124615153>.
- Architecture authority: ADR 0044 and the completed Issue #313 decision.

The issue body and frozen comment define the complete positive/negative
invariants, acceptance matrix, synthetic proposition meanings, mandatory rows,
thresholds, RED cases, human-only surfaces, stop rule, branch, allowlist, and
budgets before runtime changes.

## Source facts and defect path

Spanish is cataloged as a supported, Latin-script,
`LOCAL_DEMO_FIXTURE`/`CHECKPOINT3A_EXHAUSTIVE` language. The current
`Issue280LocalDemoService` first builds audience-specific English text, but
`_build_multilingual_response` renders each target segment only from the
underlying `Issue280GroundedFact`. The audience choice is absent from
`_translate_fact`, so the seven target bodies collapse even though English
labels, request metadata, citations, artifacts, and correctness status vary.

No new dependency, provider, workflow, database, migration, Docker surface,
license decision, or external model is necessary. The existing local/mock API,
storage, artifact, frontend, pytest, and Playwright boundaries are sufficient.

## Frozen implementation boundary

The independently authored manifest at
`docs/evals/issue280_semantic_repair_slice1.json` owns nine propositions, seven
Spanish `STANDARD` rows, exact citations, glossary requirements, thresholds,
and disallowed fallback text. The executor at
`scripts/eval/issue280_semantic_oracle.py` uses only the standard library and
does not import runtime code. Runtime must not import either oracle path.

Runtime GREEN may recognize only the exact frozen source propositions, compile
them into immutable semantic-frame entries, and render the two essential plus
one audience-required proposition for each mandatory row. Any other language,
depth, or semantic clause must refuse with `ISSUE280_TRANSLATION_REFUSED`.

## Test and evidence order

1. Freeze manifest and oracle boundary.
2. Commit oracle mutations and runtime behavioral RED before runtime edits.
3. Record failures proving collapse, false success, missing semantics, bad
   citations, glossary loss, row manipulation, schema bypass, runtime/oracle
   coupling, unsupported scope, and surface disagreement.
4. Implement the smallest semantic frame and Spanish renderer.
5. Verify API, replayed storage, artifacts, browser-visible text, citations,
   and oracle result for the same identities.
6. Run focused/full gates and independent exact-head review.

## Skill and test selection

Spec-driven development freezes the contract; TDD governs RED/GREEN;
API/interface guidance keeps identities additive and bound; frontend/browser
guidance covers visible non-intercepted behavior; security guidance keeps
untrusted input fail-closed. Skill use is method evidence only. Provider/model,
shipping, deployment, performance, custom-skill, and refusal-only outcome
workflows are rejected as outside this slice.

## Human-only and residual risk

An eligible non-author reviewer must audit bilingual meaning, non-cosmetic
audience emphasis, oracle/runtime independence, citation truth, browser
authenticity, protected forensic preservation, bounded claims, and final
reference-only squash wording. This slice proves no other language/depth,
arbitrary translation quality, provider behavior, hosted/public operation,
production readiness, release, real data, or real/cloned media.
