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

## Concrete evaluation protocol

The minimum Cut 1 golden suite contains 200 cases: 100 supported happy paths,
40 boundary/ambiguity cases, 40 prompt-injection/stale/cross-project cases, and
20 unsupported-claim or abstention cases. Each case is versioned, checksummed,
tenant-scoped, and labelled with expected citations and expected refusal or
answer behavior. A future multilingual cut adds at least 50 labelled cases per
approved language rather than silently reusing English scores.

Cut 1 blocks on all of the following: material-claim citation coverage 100%;
unsupported-claim rate 0% on the negative suite; abstention/refusal recall 100%
on deliberately unsupported cases; exact source-ID/checksum parity 100%; all
deterministic schema and policy checks passing; no critical privacy,
prompt-injection, cross-tenant, or provenance failure; and two repeated runs
with identical canonical output and manifest checksum.

Ragas is permitted only after dependency and license review. Faithfulness,
context precision, context recall, answer relevance, and citation correctness
are reported, but no aggregate score overrides a failed safety or grounding
gate. DeepEval or a custom evaluator is versioned with its dataset and
thresholds. An LLM judge is supplemental: it must be calibrated against at
least 100 human-labelled cases, achieve at least 0.85 exact pass/fail agreement
and Cohen's kappa of at least 0.80, and be checked for judge drift each release.
Human review remains authoritative for safety-critical, novel, media, and
public-use decisions.

## MLOps promotion and drift rules

Every model, provider, prompt, retriever, evaluator, dataset, and renderer has
an immutable version, owner, license, checksum, and approval state. A run
manifest binds those versions to tenant/project, source snapshot, retrieval,
output, evaluation, and media artifacts. Promotion requires deterministic
checks, the golden suite, adversarial cases, calibrated review, and a canary
comparison. A 5% relative quality regression, 10% distribution or latency
shift, or any safety/privacy/provenance regression opens an investigation; two
consecutive failing windows block promotion. The last approved bundle must be
restorable within 15 minutes in an operational environment. No uncontrolled
online self-training or agent-led production weight/policy changes are allowed.
