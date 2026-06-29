# ADR 0004: Avatar Provider Adapter

## Status

Accepted for Stage 2 planning.

## Date

2026-06-29

## Context

NarraTwin AI has a long-term product mode for pre-rendered avatar/video demos and a
future interactive avatar guide. Avatar and voice providers introduce elevated
privacy, consent, provider-lock-in, cost, licensing, and public disclosure risks.

Stage 4 must not implement avatar rendering. Stage 7 may implement avatar rendering
only after the grounded script and evaluation loop works.

## Decision

Define an `AvatarProvider` adapter boundary now and implement only mock/local
behavior when the approved stage arrives.

Avatar rendering input must include:

- grounded script reference
- optional audio artifact reference
- optional subtitle artifact reference
- avatar profile identifier
- consent metadata
- disclosure text
- provider mode
- trace/run identifiers
- consent evidence artifact reference
- consent capture timestamp
- consent verifier
- scope and revocation metadata

Avatar rendering output must include:

- render status
- output artifact reference
- provider metadata
- disclosure text
- fallback reason when applicable
- latency
- estimated cost when available
- error code when applicable

## Alternatives Considered

### Enable a premium avatar provider early

Rejected because it would add cost, provider keys, and public media risks before the
grounding loop is proven.

### Use local lip-sync tools by default

Rejected because avatar/lip-sync tools can have restrictive licenses, model-weight
constraints, or public/commercial-use risks. Wav2Lip remains disabled by default.

### Treat avatar output as a frontend-only feature

Rejected because provider keys, consent checks, disclosure, storage, and audit logs
belong on the backend side of the trust boundary.

## Consequences

Positive:

- media generation can be added without rewriting grounded script generation
- consent and disclosure requirements are explicit
- premium providers remain optional
- mock provider enables tests without real provider keys

Negative:

- first product slice remains text-only
- provider-specific media quality differences need normalization later
- consent and license review remain blockers before real media output

## Non-negotiable Rules

- no avatar rendering in Stage 4
- mock avatar provider is default
- no face cloning in MVP
- no voice cloning in MVP
- explicit documented consent is required for any cloned identity feature
- AI-generated avatar/voice disclosure is mandatory
- third-party notices and license review must be complete before enabling real tools
- consent revocation must invalidate future renders and mark affected artifacts with
  revocation metadata

## Related Documents

- `docs/SECURITY_AND_PRIVACY.md`
- `docs/THIRD_PARTY_NOTICES.md`
- `docs/PORTABILITY_STRATEGY.md`
