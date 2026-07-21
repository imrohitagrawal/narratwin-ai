# Issue 245 Demo Checkpoint 1 Acceptance Hardening

## Objective

Issue `#245` repairs blockers found during the post-PR244 Checkpoint 1
acceptance pass. The work remains local/fake and disabled-default: no hosted
deployment, public URL, provider account, provider key, paid spend, real
provider call, cloned identity, Product Mode 2 implementation, public
distribution, or production-readiness claim is authorized.

## Acceptance Findings And Dispositions

| Lens | Finding | Disposition |
|---|---|---|
| Output-correctness that executes rather than reads | `disclosureText` could echo raw-output/provider-payload canaries such as `sourceScriptText`, `translatedScriptText`, `contentBase64`, provider payload canary, and raw script canary in a granted metadata response. | Repaired with allowlisted disclosure text, raw-output marker rejection, API/unit regressions, and direct executable probe. |
| Security/privacy/access | Client-controlled `sessionExpiresAt` could extend a fake hosted-demo session beyond configured TTL. | Repaired by denying sessions whose caller-provided expiry exceeds the configured local/fake TTL. |
| Security/privacy/access | Disclosure metadata could claim cloned identity or real-person likeness despite Checkpoint 1 non-goals. | Repaired by rejecting cloned-identity and real-person-likeness display markers while keeping the safe no-cloned-identity disclosure. |
| Security/privacy/access | Deeply encoded unsafe URLs and encoded prompt-injection markers could bypass display validation. | Repaired by bounded percent-decoding before unsafe URL and prompt-injection checks. |
| Quota/reliability/idempotency | Idempotent replay could bypass invite/session secret checks because replay lookup happened before current access validation. | Repaired by checking enabled posture, current invite/session credentials, session TTL, and terminal retention state before returning stored decisions; secret-bound replay comparison stays internal, while returned request checksum, public idempotency scope, and access record ID redact invite/session secret material. |
| Retention/deletion/tombstone | Tombstone proof was caller-supplied metadata rather than deterministic local/fake evidence bound to artifact/source/retention metadata. | Repaired with deterministic local/fake tombstone checksum, tombstone ID, deletion evidence ID, deletion request time, deleted time, provider deletion status, and local-only evidence validation; caller-supplied terminal metadata is validation-only denial metadata. |
| Retention/deletion/tombstone | Old active idempotency replay could keep returning reviewer-visible artifact metadata after terminal retention evidence. | Repaired with trusted in-process local terminal retention evidence tracking that blocks stale active replay with `RETENTION_PENDING_DELETION` or `RETENTION_DELETED`; caller-supplied terminal tombstone metadata cannot seed or poison that state, changed caller-controlled `retentionRecordId` cannot bypass it, stale replay returns trusted terminal retention metadata, and `DELETED` evidence cannot downgrade to pending. |
| Governance/taste/scope | `docs/STATUS.md` and the executable gate still represented PR5 as active after PR `#244` merged. | Repaired by moving StatusStateV1 to Checkpoint 1 local acceptance complete after issue `#245`, adding an exact #245 branch allowlist, and adding negative allowlist tests. |

## Executable Evidence

Required local evidence for this repair:

- `uv run pytest tests/unit/test_hosted_demo.py tests/api/test_hosted_demo_api.py -q`
- `uv run pytest tests/unit/test_phase1_closure_docs.py -q`
- `python3 scripts/quality/check_phase1_closure_docs.py`
- Direct FastAPI/TestClient probes for raw disclosure canaries, invalid replay
  secrets, encoded injection, future session expiry, deterministic tombstone
  evidence, same-idempotency tombstone overwrite attempts, changed
  `retentionRecordId` bypass attempts, public response identifier
  secret-verifier checks, and stale active retention replay.

## Remaining Boundaries

Checkpoint 1 acceptance remains local/fake only. Checkpoint 2 must start from a
new consent/provenance planning issue before any cloned voice, cloned face,
Digital Twin, replica profile, real-person likeness, provider enrollment,
provider egress, hosted deployment, or public synthetic-media distribution work.
