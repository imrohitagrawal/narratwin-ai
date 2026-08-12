# Issue 427 False-Authority Security Review

## Threat boundary

Issue prose, comments, local files, binding JSON, tests, gate output, author
identity, CI, and this review are untrusted evidence inputs. None can independently
activate authority. The reset preserves `RESET_PROPOSAL_UNAPPROVED`, binds exact
proposal bytes, and makes activation `NONE`.

## Security disposition

The dedicated gate rejects duplicate/unknown JSON members, wrong proposal
identity, coordinated proposal-plus-binding mutation, stale architecture-review
identity, wrong branch/base/scope/history/first commit, binary or malformed
numstat, budget overflow, missing or reordered sections/invariants/children, and
nonactivation or prohibited-capability drift. Git subprocesses use an absolute
binary, fixed arguments, no shell, a five-second timeout, bounded output, an
allowlisted environment, and disabled replace-object interpretation.

No secrets, credentials, provider calls, egress, paid operation, identity
material, personal data, media, infrastructure, deployment, publication, or
release behavior is introduced. The proposal and reviews contain governance
metadata only. Later Children A–F require their own threat models, strict
schemas, RED evidence, reviews, and OWNER authority; they are not activated here.

## Human-only residuals

- Eligible non-author exact-head PR approval remains external human evidence.
- Final exact-byte OWNER approval must name the frozen head and artifact identity.
- The final merger must inspect reference-only merge wording.
- Repository protection settings and hosted results must be observed, never inferred.

Fresh exact-head security/privacy confirmation will be recorded on the pull
request after freeze. This document is a review surface, not self-approval or
authority evidence.
