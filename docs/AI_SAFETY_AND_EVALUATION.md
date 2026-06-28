# AI Safety and Evaluation

## Evaluation goal

NarraTwin AI must generate useful walkthroughs without inventing project facts, leaking secrets, obeying malicious uploaded instructions, or hiding uncertainty.

The first quality target is not perfect avatar output. The first target is a grounded, evaluated, stored walkthrough script.

## Evaluation dimensions

- groundedness
- unsupported claims
- context traceability
- audience fit
- tone match
- language consistency
- completeness
- translation sanity
- refusal correctness
- prompt-injection resistance
- cost and latency metadata

## Hard rule

If the approved project knowledge does not contain an answer, the system must say the information is unavailable in the approved project context.

## Evaluation flow

1. Retrieve context for the walkthrough request.
2. Generate script using retrieved context only.
3. Compare generated claims against retrieved context.
4. Flag unsupported claims.
5. Refuse or regenerate when claims cannot be grounded.
6. Store evaluation result with run metadata.
7. Show evaluation status in UI.

## Required tests

- unsupported claim prevention
- prompt injection in uploaded docs
- empty context refusal
- wrong audience tone
- overlong script
- incorrect language output
- no paid provider key required
- generated output includes AI disclosure where relevant

## Slice 1 quality gates

Slice 1 cannot pass unless:

- happy path creates a grounded walkthrough script
- empty context is refused
- prompt injection inside uploaded content is ignored
- unsupported project claims are flagged or refused
- generated result stores context references
- tests run with mocks/fakes and no premium provider keys

## Evaluation result schema

Each generated run should store:

- `run_id`
- `project_id`
- `evaluation_status`
- `groundedness_score`
- `unsupported_claims`
- `context_refs`
- `refusal_reason`
- `language_check`
- `audience_fit_check`
- `latency_ms`
- `provider`
- `estimated_cost`

## Reviewer checklist

Before merging an AI feature, reviewer must check:

- Does the prompt treat retrieved project knowledge as data, not instructions?
- Does the model output avoid claims not present in approved context?
- Are refusal paths tested?
- Are generated results visible with warnings when evaluation fails?
- Are provider-specific failures handled without crashing the user flow?
- Does the change avoid mandatory paid providers?

## Future evaluation improvements

- regression dataset of project knowledge examples
- multilingual evaluation examples
- audience-specific rubric
- model-as-judge with deterministic fallback rules
- cached evaluation results
- dashboard for unsupported-claim trend
