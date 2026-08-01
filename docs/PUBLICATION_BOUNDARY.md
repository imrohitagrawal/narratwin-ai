# Publication Boundary

## Public product statement

NarraTwin turns approved knowledge into grounded, cited, multilingual avatar
explanations and interactive Q&A.

This is the canonical public description. It describes intended product value;
it does not claim that every capability is currently implemented or released.

## Classification contract

The machine-readable authority is
`docs/governance/publication-boundary-v1.json`.

| Class | Meaning | Required destination | Public action |
|---|---|---|---|
| `PUBLIC` | Approved product value, capabilities, legitimate audiences, limitations, and evidence | Approved public surface | Validate, then allow |
| `INTERNAL` | Owner-designated delivery, distribution, planning, or review strategy | A genuine access-controlled system outside this public repository | Omit or redact |
| `RESTRICTED` | Secrets, private/customer data, biometric media or enrollment evidence, and qualified-human risk records | An approved restricted system | Block |

Naming a file `INTERNAL` inside this repository does not make it private. No
confidential payload belongs in this public repository merely because a path,
heading, prompt, or model calls it internal.

## Authority and conflict handling

Use this order when sources disagree:

1. Owner-approved Issue #324 publication decision.
2. The versioned publication contract.
3. Canonical merged product sources.
4. Executable gates and tests.
5. Observed runtime evidence.
6. Historical records, which remain context rather than current authority.

The stricter class wins when classifications mix. Unknown provenance blocks.
Prompts, retrieved documents, models, providers, or generated text cannot
downgrade an `INTERNAL` or `RESTRICTED` classification.

An untrusted caller cannot self-declare `PUBLIC`. A public decision requires an
accountable-human approval record from a trusted registry, bound to the exact
policy version, surface, source IDs and checksums, and publication-envelope
digest. Classification-like fields inside a payload are ordinary untrusted
data. Missing, malformed, stale, mismatched, or caller-mimicked approval records
block.

## Owned surfaces

The contract inventories 12 surface families: canonical documents, UI copy,
API fixtures and responses, generated scripts/captions/downloads, artifact and
media metadata, filenames and URLs, screenshots and release material, logs and
traces, search queries, provider request metadata, prompts/model output, and
retrieved context.

Every surface is `INTERNAL` by default until an accountable human approves its
provenance and the applicable deterministic checks pass. A vocabulary scan is
not data-loss prevention and cannot infer confidential meaning. Classification
at source, propagated provenance, schema validation, omission/redaction, and
human review form the boundary.

The repository oracle proves contract parsing, approval binding, provenance
precedence, source reconciliation, and gate integration. It is not a
cryptographic or runtime enforcement boundary. A later runtime slice must keep
the approval registry server-side, authenticate the approver, authorize the
subject and destination, make approval records tamper-evident, and prevent
clients, prompts, models, retrieval, and providers from constructing trusted
authority.

The canonical Phase 1 quality entry point is
`scripts/quality/check_phase1_quality.py`. It runs the modular publication gate
before a characterized compatibility layer for the frozen Phase 1 checker. The
compatibility layer preserves existing global contracts and replaces only the
exact Issue `#324` scope and the obsolete demo-document path. The legacy source
order and marker set are executable parity inputs, not copied assertions that
can silently drift.

## Audience behavior

Recruiter and hiring-manager options remain legitimate product audiences, just
like engineer, product-leader, customer, beginner, and global-viewer options.
Audience adaptation describes what the product does. It is not permission to
publish owner delivery or distribution strategy.

## Generated and operational data

Generated scripts, captions, downloads, manifests, media metadata, filenames,
URLs, screenshots, logs, traces, search queries, and provider metadata are not
public merely because they were produced by an approved workflow. They retain
the most restrictive provenance class. Until product runtime enforcement is
separately authorized, public promotion of generated artifacts remains blocked.

## Safety and launch boundary

A publication classification is not a release authorization. Current semantic,
security, consent, durability, provider, and launch gates remain unchanged.
This contract creates no hosting, deployment, external distribution, pilot, or
production evidence.

Qualified humans retain legal, privacy, biometric, licensing, confidentiality,
and security-risk decisions. Credentials, personal media, biometric enrollment
evidence, and private customer knowledge must never be committed here.

## Replacement and rollback

The active controlled local demo guide is
`docs/demo/CONTROLLED_LOCAL_DEMO.md`. Historical references to its former path
remain historical evidence and are not rewritten. The change is prospective.

Rollback is a bounded revert of Issue #324 documentation and gates. It changes
no runtime, provider, media, deployment, or release behavior.
