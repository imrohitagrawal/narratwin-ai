# Implementation verification — work records

The design received three independent initial reviews and final verification;
see [the preserved design review](proposals/2026-09-14-structure/REVIEW.md).
Implementation verification below is separate from that design result.

## Pre-code findings

- Scope reviewer reproduced that the existing checker reads exact path/cap values
  from the manifest; no new branch-specific scope logic is needed. Prospective
  amendment committed separately before new implementation.
- Entry reviewer reproduced failure of a naive new-hash-only AGENTS prerequisite.
  REQUIRED_CONTRACT: preserve existing anchor and mandatory STATUS/CODEX discovery;
  prepare the explicit navigation consumer separately with transition tests required.
- Integrity reviewer verified which public hashes change and which frozen/private
  descriptors must remain unchanged. Preserve the complete private packet intact.

## Verification state

Implementation verification is in progress; independently reviewed findings are below. No exact-head,
all-CI-green, merge, source semantic acceptance or backup claim is made here.
The original PR536 pre-code PR-link timing deviation remains in historical REVIEW;
the prospective structure amendment does not retroactively erase it.

## Independent implementation findings and root disposition

Scale review passed exact58 issue coverage, generic/profile separation and unchanged
legacy scope code. Entry review resolved all293 relative links across40 documents
and reconstructed effective V1 versus candidate V2, source ownership and next action.
Actual Claude application auto-loading was not tested; tracked bridge contents and
shared required-reading flow were verified. Two navigation advisories were corrected:
the lower CODEX legacy entry and G1 README self-link.

| ID | Reproduction and classification | Root disposition |
|---|---|---|
| IR01 | Two distinct IDs/owners with one restricted source returned VALID. REQUIRED_CONTRACT: violates one-owner identity. Root added a failing alias regression before correction. | Reject duplicate locators and identical original-byte identities independently of display ID; references remain supported. |
| IR02 | A correctly hashed public plan under ignored .evidence passed and was read as public. CRITICAL_BLOCKER: demonstrated private-read boundary bypass. Default and configured-root regressions failed before correction. | Reject all public references into private roots before I/O; validate before generating links. No private actual source was used in reproduction. |

Root observed three behavioral RED failures, then18passing generic tests after the
small boundary corrections. Independent integrity reviewer verified both corrections: duplicate alias rejection,
positive shared-source reuse, zero private-target reads for default/configured roots,
and unchanged INDEX bytes when invalid generation fails. Both findings are resolved;
no remaining blocker in that bounded correction review. These
are new implementation results, not retrospective amendments of the design review.
MIGRATION.json is now bound as public evidence; actual copy preservation and private
read-back are verified separately rather than inferred from metadata alone.
