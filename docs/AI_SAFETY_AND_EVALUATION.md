# AI Safety and Evaluation

## Evaluation dimensions

- groundedness
- unsupported claims
- audience fit
- tone match
- language consistency
- completeness
- translation sanity
- refusal correctness

## Hard rule

If the approved project knowledge does not contain an answer, the system must say the information is unavailable in the approved project context.

## Required tests

- unsupported claim prevention
- prompt injection in uploaded docs
- empty context refusal
- wrong audience tone
- overlong script
- incorrect language output
