# North Star Metrics

## Version

- Version: 1.0
- Stage: Stage 1 product strategy and PRD hardening
- Canonical issue: `#1`
- Last updated: 2026-06-29

## North Star Metric

Successful grounded walkthroughs generated from approved project knowledge.

A walkthrough is successful when it is:

- generated from approved project knowledge
- adapted to the selected audience, language, depth, and style
- linked to source context references
- evaluated for unsupported claims
- stored with run metadata
- visible to the user

## One Metric That Matters

For the first implementation slice:

```text
percentage of walkthrough generation runs that produce a stored output with
context references and a passing unsupported-claim evaluation
```

This metric keeps the team focused on trusted project explanations instead of early
avatar polish.

## Metric Tree

| Metric family | Metric | Definition | Target direction |
|---|---|---|---|
| Activation | Time to first grounded walkthrough | Time from project creation to first successful stored output | Lower |
| Activation | Upload completion rate | Share of users who upload at least one valid markdown/text source | Higher |
| Grounding | Groundedness score | Share of generated project-specific claims supported by retrieved context | Higher |
| Grounding | Unsupported claim rate | Share of generated outputs with unsupported claims | Lower |
| Grounding | Context reference coverage | Share of project-specific claims linked to context refs | Higher |
| Safety | Empty-context refusal pass rate | Share of empty-context requests that refuse instead of inventing | Higher |
| Safety | Prompt-injection resistance | Pass rate against malicious uploaded-document tests | Higher |
| Audience quality | Audience fit score | Human or rubric score for recruiter, hiring manager, engineer, product, and global-viewer outputs | Higher |
| Language quality | Language success rate | Output appears in requested language and preserves key technical meaning | Higher |
| Media readiness | Subtitle readiness | Share of scripts that can become subtitle-ready without structural rewrite | Higher |
| Media readiness | Voice/avatar adapter success | Future share of optional media runs that complete with disclosure and metadata | Higher |
| Cost | Estimated cost per run | Provider cost estimate when available | Lower |
| Cost | Cache hit rate | Share of repeated eligible runs served from cache | Higher |
| Reliability | Generation success rate | Share of runs that complete without system error | Higher |
| Portfolio value | Reviewer usefulness score | Recruiter/hiring-manager/engineer feedback on usefulness | Higher |

## Slice 1 Required Measurements

Slice 1 must store enough metadata to measure:

- run count
- success/failure/refusal status
- selected audience
- selected language
- selected depth and style
- provider and provider mode
- retrieved context count
- context refs attached to output
- unsupported claim count
- evaluation status
- latency
- cache hit/miss
- estimated cost when available

## Release Thresholds For Slice 1

Slice 1 is not acceptable unless:

- happy path creates a stored grounded walkthrough
- output includes context refs
- unsupported-claim detection or refusal works on a controlled test
- empty-context refusal works
- prompt-injection uploaded-document test works
- tests pass without real paid provider keys
- run metadata is stored with provider mode and evaluation status

## Future Thresholds

| Stage | Threshold |
|---|---|
| Stage 5 | Unsupported-claim evals are blocking and visible in validation evidence |
| Stage 6 | Multilingual output passes language sanity checks for approved test cases |
| Stage 6 | Subtitle export has valid structure for generated scripts |
| Stage 7 | Mock avatar/video render completes with AI disclosure and provider metadata |
| Stage 8 | Premium provider runs record cost, latency, failure mode, and fallback behavior |

## Anti-metrics

Do not optimize for:

- number of providers integrated before trust loop works
- avatar realism before script grounding
- number of languages before translation quality checks
- total generated text length
- demo claims that exceed implemented product behavior
