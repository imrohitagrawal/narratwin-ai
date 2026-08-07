# ADR 0052: Cut 1 Provider-Neutral Presenter Registry

## Status

Proposed in Issue `#367`; accepted only after reviewed merged-main acceptance.

## Context

Cut 1 has three owner-approved fictional synthetic identity anchors: Meera,
Myra A, and Raj C. Later narration, TTS, rendering, and UI work needs one stable
identity contract without importing provider-specific profiles or trusting a
caller-supplied asset, voice, lifecycle, or trace claim. Issue `#383` accepted
still portraits only; it did not register runtime identities or prove audio or
video behavior.

The eventual consented founder avatar is outside Cut 1. A future personal-avatar
shape must be testable without registering a person, likeness, biometric input,
clone, or media asset.

## Decision

Store the production registry in bounded checked-in JSON and load it through a
small provider-neutral Python boundary. Production identity IDs are exactly
`meera`, `myra`, and `raj`, each at semantic version `1.0.0`. Each record binds:

- structured owner-approved persona and immutable visual anchors;
- canonical repository-relative WebP path, SHA-256, dimensions, media type,
  and existing provenance reference;
- distinct synthetic, non-cloned, provider-neutral voice direction metadata;
- fictional synthetic disclosure and controlled-local permitted-use posture;
- renderer-neutral framing and animation-readiness fields; and
- monotonic lifecycle state.

The loader rejects oversized or malformed UTF-8 JSON, duplicate keys, unknown
fields, noncanonical versions/IDs, path escape, symlinks, missing or substituted
assets, media drift, duplicate voice references, provider selectors, clone
metadata, persona drift, and an inexact production ID set. It revalidates the
asset before selection.

Selection creates a canonical trace binding over presenter ID/version, asset
digest, voice reference/version, registry version/digest, and trace ID. The
binding digest is recomputed during verification. Trace IDs are single-use in a
registry process and claimed under a lock. Lifecycle transitions are monotonic:

```text
ACTIVE -> REVOKED -> DELETED
ACTIVE ------------> DELETED
```

No transition may reactivate or resurrect a record. Revocation/deletion changes
the registry digest and invalidates prior bindings. The current trace-claim and
lifecycle state is in-process controlled-local state; later durable consumers
must persist and revalidate the complete binding rather than infer production
durability from this slice.

One additional `future-personal-test` shape may be parsed only when tests opt in.
It must be `PERSONAL`, `DISABLED`, and `test_only`, has no asset, contains no
real-person attributes, and remains unselectable. It is absent from production
JSON. Aashna/Character 1 and Veer/Character 2 remain audit-only and unregistered.

## Consequences

Positive:

- downstream children share one checksum-bound identity contract;
- assets and owner-approved persona anchors cannot silently drift;
- no provider SDK, key, network call, voice artifact, or renderer is introduced;
- revoked/deleted/stale/mismatched/replayed selections fail closed; and
- the future personal-avatar schema boundary is tested without processing a
  likeness or biometric input.

Limitations:

- Issue `#367` does not produce or validate narration, audio, animation, video,
  synchronization, playback, public use, or production durability;
- qualitative persona meaning and unknown real-person resemblance remain human
  review surfaces; and
- publication/legal review remains separate from controlled-local permission.

## Rejected Alternatives

- Provider-native avatar or voice IDs in the core registry: rejected for lock-in,
  secret/provider activation, and premature downstream scope.
- Caller-supplied identity dictionaries: rejected because they bypass canonical
  assets, disclosure, lifecycle, and trace integrity.
- Registering Aashna, Veer, or a founder avatar now: rejected because none is an
  active Issue `#367` identity and the latter requires separate consented work.
- Reusing one voice reference: rejected because presenter identity and later TTS
  evidence must remain separately bindable without cloning.

## Related

- Issue `#366`, Issue `#367`, Issue `#383`, and Issue `#382`
- ADR `0004` and ADR `0019`
- `docs/THIRD_PARTY_NOTICES.md`
