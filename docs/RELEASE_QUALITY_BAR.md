# Release Quality Bar

A release candidate is not acceptable unless the implemented behavior matches the documented claims.

## Universal quality bar

Every slice must include:

- scoped implementation
- tests or explicit not-applicable reason
- docs update
- security/privacy notes
- known limitations
- reviewer pass
- no unsupported product claims

## Required checks

- GitHub Actions `quality` workflow passes.
- No secrets are committed.
- Markdown docs pass quality checks.
- Backend lint/test wrappers exist once backend code exists.
- Frontend build wrapper exists once frontend code exists.
- Dependency/security wrapper exists once lockfiles or manifests exist.

## AI quality gates

- Prompt-injection tests exist once uploaded-document handling is implemented.
- Unsupported-claim tests exist once generation is implemented.
- Empty-context refusal test exists once retrieval/generation is implemented.
- Provider adapters have contract tests once real adapters are added.
- Generated outputs include AI disclosure where media output is relevant.

## MVP release blocker list

Do not release if:

- app requires premium provider keys for the default path
- uploaded documents can override system rules
- generated scripts can silently include unsupported claims
- output is not stored with run metadata
- third-party notices are missing for used dependencies
- public docs claim avatar/video/voice features that are not implemented
- Wav2Lip or other restricted media tooling is enabled by default

## Documentation bar

Docs must explain:

- product scope
- architecture and provider boundaries
- setup and local validation
- quality gates
- security and privacy controls
- AI safety and evaluation gates
- known limitations
- roadmap and non-goals

## Reviewer pass

Reviewer must explicitly check:

- PR scope stayed within one stage or slice
- no broad disconnected skeleton was added
- tests match the changed behavior
- docs match the changed behavior
- premium providers remain optional
- new dependencies are recorded in third-party notices
