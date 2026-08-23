# ADR-0048: Canonical Cut 1 Presenter and Enterprise Readiness Contracts

## Status

Proposed through Issue #440; becomes accepted only after the dedicated PR is
reviewed, merged, and reconciled in `docs/STATUS.md`.

## Context

NarraTwin AI has substantial product, AI-safety, operations, and release
documentation, but older issue and checkpoint language is distributed across
many files. Fresh work can therefore mistake historical local/mock restrictions
or legacy presenter/disclosure wording for the current product direction.

## Decision

Use three linked canonical documents:

1. `docs/PRODUCT_CONTRACTS/CUT1_PRESENTER_CONTRACT.md` defines Meera, Raj, Myra,
   presenter behavior, eye contact, framing, motion, provenance, and Cut 1/Cut
   2 boundaries.
2. `docs/AI_QUALITY_AND_EVALUATION_CONTRACT.md` defines grounding, data lineage,
   hallucination controls, golden suites, Ragas, DeepEval/custom evaluation,
   calibrated LLM-as-judge, human review, multilingual/media evaluation, drift,
   observability, and rollback.
3. `docs/ENTERPRISE_READINESS_REGISTER.md` indexes enterprise capabilities,
   owners, statuses, evidence, phases, and release impacts.

`STATUS.md` is the current ledger and `PHASE_PLAN.md` is the sequencing plan;
they point to these contracts instead of duplicating acceptance criteria.
Historical wording remains available for audit but cannot override the current
contract. Issue #435 remains an adversarial evidence gate and does not redefine
the product.

## Consequences

- Cut 1 can be expedited without losing the enterprise/SRE/AI-quality roadmap.
- Product implementation, provider activation, public release, and commercial
  readiness remain separately gated.
- Ragas, DeepEval, LLM-as-judge, full-body motion, HA/DR, and commercial launch
  are specified with explicit deferred or phase-gated status rather than being
  implied as already implemented.
- Future changes require one issue, branch, PR, independent review, and status
  reconciliation, preventing another competing authority layer.

## Alternatives rejected

- Continue editing `STATUS.md` and `PHASE_PLAN.md` as independent contracts:
  rejected because it caused historical/current drift.
- Delete historical issue language:
  rejected because it would destroy audit evidence; old records are marked
  historical instead.
- Put enterprise readiness inside Issue #435:
  rejected because #435 is an adversarial evidence gate, not the product
  contract or commercial-readiness authority.
