# Issue 298 Repo Semantic Gate Preflight

Date: 2026-07-25

## Intent

Make the #280 semantic-output lesson a general repository quality gate for
non-trivial implementation PRs. Future PRs that claim user-visible behavioral
correctness must include executable post-implementation verifier evidence, and
semantic requirement rows may not be marked satisfied with structural,
metadata-only, screenshot-only, artifact-only, or docs-only proof.

## Non-Goals

- No product runtime behavior changes.
- No provider setup, paid spend, hosted/public demo claim, real provider call,
  cloned identity runtime, real media, public distribution, arbitrary
  human-grade translation claim, provider quality claim, or production-readiness
  claim.
- No replacement for human review. This gate reduces false-pass recurrence; it
  does not guarantee defect-free implementation.

## Source Facts

| ID | Source | Fact | Impact |
|---|---|---|---|
| SRC-298-GATE-001 | `docs/ENGINEERING_PROCESS_RCA.md` | Green CI can pass incomplete contracts when the gate omits negative cases. | Guardrails must inspect evidence shape, not only command success. |
| SRC-298-GATE-002 | `docs/SKILL_SELECTION_AND_EVIDENCE.md` | Skills govern method; evidence proves the claim. | A sub-agent or reviewer label is not completion evidence without executable artifacts. |
| SRC-298-GATE-003 | `docs/reviews/ISSUE_280_SEMANTIC_GAP_MEMORY_2026-07-25.md` | #280 exposed metadata-correct but semantically wrong browser-visible multilingual output. | User-visible semantic claims need a dedicated semantic verifier classification. |

## Failure Matrix

| ID | Case | Expected Behavior | Evidence |
|---|---|---|---|
| INV-298-GATE-001 | Non-trivial implementation PR claims user-visible/output correctness but omits a post-implementation execution verifier. | PR guardrail fails. | `tests/unit/test_guardrails_check.py::test_behavioral_pr_requires_post_implementation_execution_verifier` |
| INV-298-GATE-002 | PR body presents screenshot-only, docs-only, matrix-only, or metadata-only evidence as output-correctness proof. | PR guardrail fails. | `tests/unit/test_guardrails_check.py::test_behavioral_pr_rejects_metadata_or_artifact_only_output_correctness_evidence` |
| INV-298-GATE-003 | Multilingual PR body reports target transcript text as a template, English fallback, source-heading summary, or metadata-only sentence. | PR guardrail fails. | `tests/unit/test_guardrails_check.py::test_multilingual_pr_rejects_template_or_english_fallback_semantic_evidence` |
| INV-298-GATE-004 | Requirement matrix rows mark semantic/user-visible rows satisfied with structural pass, not proven, failed, or metadata-only evidence. | PR guardrail fails. | `tests/unit/test_guardrails_check.py::test_requirement_matrix_rejects_semantic_rows_without_semantic_pass` |
| INV-298-GATE-005 | PR body includes a real executable verifier with browser-visible semantics, semantic classification, negative failure modes, and result-bearing validation lines. | PR guardrail passes this semantic verifier contract. | `tests/unit/test_guardrails_check.py::test_behavioral_pr_accepts_semantic_execution_verifier_contract` |

## Test Plan

1. Add RED unit tests for the PR-body semantic verifier contract and matrix
   status false-pass classes.
2. Implement the smallest `scripts/guardrails_check.py` parsing and validation
   logic that makes those tests pass.
3. Update governance docs and the PR template so future authors know the exact
   evidence expected.
4. Run guardrail unit tests, repository guardrails, phase-closure docs checks,
   quality, lint, and mypy.

## Stop Rule

If a new false-pass class appears during this work, pause implementation,
update this failure matrix first, add or adjust the RED test, and only then
continue the implementation.

