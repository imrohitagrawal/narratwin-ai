# North Star Metrics

## North Star

Successful grounded walkthrough generated per project.

A successful grounded walkthrough means:

- generated from approved project knowledge
- adapted to selected audience and language
- evaluated for unsupported claims
- stored with run metadata
- visible to the user

## Supporting metrics

| Metric | Definition | Target direction |
|---|---|---|
| Time to first walkthrough | Time from project creation to first stored output | Lower |
| Groundedness score | Share of generated claims supported by approved context | Higher |
| Unsupported claim rate | Share of outputs with unsupported claims | Lower |
| Prompt-injection resistance | Pass rate against malicious uploaded-document tests | Higher |
| Language success rate | Output appears in requested language with acceptable meaning | Higher |
| Audience fit score | Output matches recruiter, hiring manager, engineer, or product-leader intent | Higher |
| Cache hit rate | Share of repeated runs served from cache where appropriate | Higher |
| Estimated generation cost | Estimated provider cost per run | Lower |
| User feedback score | User rating or approval of generated walkthrough | Higher |

## MVP measurement

For Slice 1, track only:

- run count
- success/failure status
- unsupported-claim count
- selected audience
- selected language
- provider
- latency
- cache hit/miss
- estimated cost when available

## Release thresholds for Slice 1

Slice 1 is not acceptable unless:

- happy path creates a stored walkthrough
- unsupported-claim detection works on at least one controlled test
- empty context refusal works
- prompt-injection uploaded-document test works
- no paid provider key is required for tests

## Future metrics

- subtitle generation success rate
- avatar render success rate
- provider fallback rate
- translation quality review score
- demo completion rate
- recruiter/hiring-manager/engineer mode usage split
