# Review Rigor Retrospective

## Purpose

This document records why the Stage 8 review did not find several important
issues in the first pass, what remediation is required, and the review approach
that must be used for this repository and future applications.

It is intentionally blunt. Green tests and broad review coverage are not proof of
release readiness. They are only evidence that known checks passed.

## What Went Wrong

The first review pass was too acceptance-oriented and not adversarial enough.

### Green gates were overweighted

`make quality` and remote CI passing were treated as strong evidence of
correctness. They proved only that the implemented checks passed. They did not
prove that the implemented checks encoded the full security, API, performance,
or release contract.

Example: Stage 8 request-size tests covered honest oversized `Content-Length`
and missing `Content-Length`, but not an under-reported `Content-Length` with a
larger actual body. The intended invariant was "actual request bytes are
bounded"; the implemented test only proved "declared request bytes are checked."

### Review prompts were broad instead of exploit-matrix driven

The initial sub-agent prompts asked for quality, depth, security, architecture,
API, AI, performance, and release review. That breadth was useful, but it did not
force every reviewer through concrete negative cases.

For Stage 8, reviewers should have been explicitly asked to test:

- missing `Content-Length`
- malformed `Content-Length`
- negative `Content-Length`
- honest oversized `Content-Length`
- under-reported `Content-Length`
- chunked or multi-message ASGI bodies
- upload streaming over limit
- MIME type parameters such as `text/plain; charset=utf-8`
- idempotency replay status versus documented status
- rate limit before versus after idempotency
- caller-controlled identity headers
- provider-bound prompt, upload, glossary, and metadata secret surfaces
- Docker scanner unavailability and fallback behavior
- GitHub status context names versus documented branch-protection requirements

Because those cases were not required in the first prompts, several reviewers
validated the visible implementation instead of attacking the invariant.

### Header validation was mistaken for body validation

The first fix rejected missing or oversized declared `Content-Length`. That was
necessary but incomplete. The correct boundary is the ASGI body stream, because a
malicious or malformed caller can under-report the header.

The review should have asked: "Can the app consume more bytes than the budget
under any ASGI message sequence?" That question would have exposed the bypass
immediately.

### Docs were not treated as executable contracts

The API contract contained stale or mismatched statements around idempotency
replay status and `BACKPRESSURE_QUEUE_FULL` retry headers. The first pass
reconciled several docs but did not perform a strict line-by-line
contract-to-implementation review.

Docs that define public behavior must be reviewed like tests. If implementation
and contract disagree, one of them is wrong.

### CI compatibility contexts were not protected during workflow hardening

The security Docker job was renamed from the documented compatibility context
`security / docker build` to `security / docker build and scan`. That preserved
the security intent but broke the status-context contract documented for branch
protection.

Workflow hardening must preserve externally referenced status names unless the
ruleset and documentation are changed in the same reviewed step.

### Sub-agents were used as reviewers, not adversarial proof generators

The first sub-agent wave was useful but insufficiently ruthless. The later
architecture and depth reviewers reproduced concrete bypasses because they were
closer to adversarial proof. That should have been the first pass.

Sub-agent review should not merely ask "does this look right?" It should ask
"show me how this invariant fails, or prove the tested cases cover it."

## Root Causes

The root issue was review framing.

- The review optimized for broad coverage before invariant proof.
- Tests were checked for existence before checking whether they represented the
  abuse cases implied by the threat model.
- Documentation was checked for presence and marker strings before being checked
  as a strict behavioral contract.
- CI green status was used as confidence before asking whether CI was enforcing
  the right thing.
- Sub-agent roles were named by expertise, but their tasks were not constrained
  to concrete exploit attempts and contract-drift checks.

## Remediation For Stage 8

Stage 8 remediation must include these actions before the PR is considered ready:

- Enforce actual ASGI body byte limits for all `/api/v1` write requests, not
  only declared `Content-Length`.
- Add regression coverage for under-reported `Content-Length`.
- Preserve the documented `security / docker build` status context while keeping
  Docker image scanning in the job.
- Reconcile API contract language for synchronous local idempotency replay
  status.
- Reconcile `BACKPRESSURE_QUEUE_FULL` documentation with implementation, or add
  real `Retry-After` support.
- Decide whether glossary terms are provider-bound secret surfaces; if yes,
  reject secret-like glossary content at API and domain boundaries.
- Add frontend artifact tests for wrong MIME type and wrong file extension if
  RR-030 claims that coverage.
- Recheck Docker scanner fallback behavior so documented fallbacks are reachable
  for tool/transport failures without masking confirmed vulnerabilities.
- Record branch-protection/ruleset enforcement as a repository settings blocker
  if it cannot be changed through code.

## Final Review Approach Going Forward

Every implementation or release-readiness stage must use a three-layer review:

1. Invariant review
2. Exploit-matrix review
3. Contract-and-gate review

The stage is not ready until all three layers pass.

## Layer 1: Invariant Review

Start by writing the actual invariants in plain language. Do not start from the
code.

Examples:

- "Actual request bytes consumed by the app must not exceed the configured
  budget."
- "Provider-bound inputs must not carry secrets."
- "A documented required status context must continue to be emitted by CI."
- "Idempotency behavior must match the public API contract."
- "Container vulnerability scanning must fail on confirmed critical/high
  findings and must not silently skip scanning."

For each invariant, ask:

- What is the trusted boundary?
- What input is untrusted?
- What would a malicious or malformed caller try?
- What test proves the invariant?
- What doc states the invariant?
- What CI gate enforces it?

## Layer 2: Exploit-Matrix Review

For each security, API, performance, or release hardening feature, build a small
negative-case matrix before accepting the implementation.

### Request Boundary Matrix

Required cases:

- valid small body
- honest oversized body
- missing `Content-Length`
- malformed `Content-Length`
- negative `Content-Length`
- under-reported `Content-Length`
- body split across multiple ASGI messages
- upload-specific streaming limit
- non-upload JSON limit
- rate limit interaction with rejected bodies

### Provider-Bound Input Matrix

Required cases:

- prompt contains secret-like value
- uploaded document contains secret-like value
- glossary term contains secret-like value
- provider config contains unknown fields
- provider output contains unknown nested fields
- provider output omits required fields
- provider output uses wrong MIME type or artifact extension

### Idempotency Matrix

Required cases:

- first request succeeds
- exact replay returns documented status and body
- same key with different payload conflicts
- in-flight duplicate is rejected
- semantic validation failure is replayed or released according to contract
- rate limiting order is documented

### CI And Release Matrix

Required cases:

- required status context names are unchanged or deliberately migrated
- local gate and remote workflow run equivalent checks
- artifact upload happens on success and failure when needed
- scanner fallback paths are reachable
- confirmed vulnerabilities fail the gate
- tool unavailability fails closed with a clear artifact

## Layer 3: Contract-And-Gate Review

Review docs and gates as executable contracts.

Required checks:

- API contract status codes match implementation and tests.
- Error codes match implementation and tests.
- Headers documented in the contract are actually emitted.
- Quality gate scripts assert the important markers and test names.
- Stage allowlists include every changed file and exclude unrelated drift.
- Release docs include actual evidence or explicitly identify CI artifacts as
  the evidence source.
- Third-party notices and skill lock match every new tool, action, model,
  provider, dataset, or generated artifact.
- Status and traceability documents reflect the current issue, PR, branch,
  stage, and blockers.

## Sub-Agent Review Protocol

Sub-agents should be launched only after the invariants and exploit matrix are
known. Each sub-agent must receive a narrow proof task, not a generic review
request.

### Required Review Roles

- Quality reviewer: tests, typing, checker coverage, allowlists, whitespace,
  maintainability.
- Depth/adversarial reviewer: exploit matrix reproduction and bypass attempts.
- Value reviewer: intended deliverables versus implemented user/reviewer value.
- Architecture reviewer: boundary placement, state model, CI architecture,
  documented decisions.
- API reviewer: status codes, headers, idempotency, error envelopes, API docs.
- AI reviewer: provider-bound inputs/outputs, eval gates, prompt injection,
  synthetic-media consent/provenance.
- Security reviewer: untrusted input, secret handling, dependency/container
  scans, credential posture.
- Performance reviewer: budgets, measurement quality, reproducibility,
  gate runtime.
- Shipping/release reviewer: checklist, runbook, rollback, monitoring,
  branch-protection/status-context readiness.

### Required Prompt Shape

Every reviewer prompt must include:

- exact branch and commit
- files or contracts to inspect
- invariants to prove or disprove
- negative cases to attempt
- instruction to provide file/line findings
- instruction to distinguish blocking issues from residual risks

Example:

```text
Review request-size hardening. Prove or disprove this invariant:
actual bytes consumed by /api/v1 write requests cannot exceed
MAX_API_REQUEST_BYTES or MAX_UPLOAD_REQUEST_BYTES.

Attempt missing Content-Length, malformed Content-Length, under-reported
Content-Length, split ASGI body messages, honest oversized body, and upload
stream over limit. Report file/line findings and exact reproduction result.
```

## Readiness Bar

A stage is not ready when:

- a test exists but does not cover the real invariant
- a doc says behavior exists but implementation cannot emit it
- CI is green but required status contexts drifted
- a scanner exists but fallback behavior is unreachable
- a provider-bound input surface is not covered by the same safety policy
- release evidence lists tools without run results or artifact sources
- known repository settings, such as branch protection, are not enforced

A stage is ready only when:

- invariants are explicit
- exploit matrices have passing tests or documented non-goals
- docs match implementation
- gates enforce the important checks locally and remotely
- residual risks are named, assigned, and accepted in the appropriate review
  register

## Standing Rule

Do not ask "did the checks pass?" first.

Ask "what would make the checks meaningless?"

Only after answering that should green checks be treated as release evidence.
