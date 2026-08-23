# AI Quality and Evaluation Contract

Status: proposed; implementation is phase-gated. This document is the single
AI-quality authority for grounded generation, multilingual output, and presenter
content. Detailed architecture, threat, and operations documents remain linked
evidence, not competing contracts.

## Grounding and hallucination control

- Generate only from approved, versioned project sources.
- Bind every material claim to source/document/chunk/run/evaluation evidence.
- Reject unsupported claims, missing citations, stale source runs, cross-project
  replay, prompt-injection attempts, and malformed evaluation records.
- Permit abstention or clarification when evidence is insufficient.
- Invalidate script approval, audio, captions, render, and replay artifacts when
  the source, prompt, model, evaluator, or approved script version changes.

## Data integrity and lineage

Maintain immutable source and artifact checksums, document/chunk lineage,
retrieval IDs, evaluation IDs, approval state, model/provider versions, prompt
versions, and reproducible run metadata. Enforce tenant/project isolation,
retention/deletion rules, redaction, and restore/replay consistency.

## Evaluation layers

1. Deterministic schema, citation, policy, safety, and unsupported-claim checks.
2. Golden suites covering normal, boundary, multilingual, adversarial,
   prompt-injection, stale-context, cross-project, and presenter-script cases.
3. Ragas metrics where the approved dependency and license review permit them:
   faithfulness, context precision, context recall, answer relevance, and
   citation correctness.
4. DeepEval or equivalent custom evaluators for regression and task-specific
   criteria, with versioned test data and thresholds.
5. LLM-as-judge only as supplemental evidence, calibrated against human labels,
   checked for judge drift, and never used as the sole release gate.
6. Human review for factuality, usefulness, language quality, eye contact,
   synchronization, presenter identity, and high-risk or novel failures.

## Regression, drift, and release gates

Pin model/provider/prompt/evaluator versions for each evaluated run. Compare
quality, safety, latency, cost, and failure distributions against the approved
baseline. Block release on groundedness, citation, safety, privacy, regression,
or provenance failure. Retain an auditable report and support rollback to the
last approved model, prompt, index, script, and media bundle.

## Multilingual and media evaluation

Golden suites cover each supported language, translation fidelity, pronunciation,
captions, unsupported-language refusal, voice consistency, lip sync, eye contact,
facial motion, hand/body motion, framing, and identity continuity for Meera, Raj,
and Myra.

## Observability and privacy

Record safe run IDs, source/evaluation bindings, model/provider/version, scores,
latency, token/cost data, and failure reasons. Do not log secrets, raw private
documents, raw prompts, transcripts, provider payloads, or unapproved media.

## Status vocabulary

Every evaluator and suite is `Specified`, `Designed`, `Implementing`,
`Validated`, `Deferred`, `Blocked`, `Accepted risk`, or `Superseded`, with an
owner, evidence artifact, threshold, and release impact in the enterprise
readiness register.
