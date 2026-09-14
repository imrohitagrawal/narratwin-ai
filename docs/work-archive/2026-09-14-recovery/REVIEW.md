# Archive review and verification record

## Scope

Issue #535 concerns preservation, discovery and integrity. The initial review used
three existing independent agents for repository retention/routing, privacy/source
copy, and verification design. The quality agent subsequently implemented only the
verifier and its tests; it cannot independently approve its own implementation.
Root implements documents and integration. Final independent checks are recorded
below when completed; no pending check is represented as a pass.

## Evidence already established

- Root copied all 978 files present in the external recovery packet, plus the exact
  65,097-byte original owner plan, and re-read every copy: 979 matching content files,
  219,884,151 bytes. The source packet was retained.
- Independent privacy reviewer re-read the same 979 entries and verified the ten
  required masters and owner plan, their hashes/sizes, file0600/directory0700, and
  absence of tracked restricted paths in shared and issue535 worktrees.
- Root added three bounded user-visible discussion snapshots and a coverage receipt;
  the private inventory initially contained 983 entries; adding its README made 984. The eleven required masters remain
  separately indexed so a total-file count cannot substitute for their presence.
- The existing source recovery separately established exact ten-artifact identity
  and 605 matching source bodies. These historical results do not certify semantics.

## Findings and disposition

| Finding | Evidence and classification | Owner and disposition |
|---|---|---|
| Handoff could not locate exact sources despite stored hashes | Recovered source locator and ten supporting artifacts; REQUIRED_CONTRACT retention/discovery gap | Root: preserve exact files, public index, private read-back and handoff digest. Independent correction verification required. |
| Public repository versus restricted originals | Personal-path markers in 76 packet files; owner source explicitly restricted; CRITICAL_BLOCKER if published | Root: ignored private subtree, explicit tracked-file check, safe public derivative review. No raw publication. |
| Generic Phase1 scope rejects archive additions | Existing closed legacy path list; REQUIRED_CONTRACT for this branch integration | Root: exact issue535 route, manifest line charges and preserved legacy checks; no blanket scope exemption. |
| Local copy cannot establish independent backup | Both surviving locations are on one machine; ADVISORY_DEBT for bounded local preservation, open mandatory store work remains in Issue #532 | Project owner/store work: backup UNPROVED; no deletion or independent-restore claim. |
| Four ADR bibliography references treated as requirements | Existing reproduced semantic finding; OUT_OF_SCOPE for this archive correction | G1 correction route: retained open, blocks relevant semantic acceptance; recovery does not erase it. |
| Earlier original-plan unavailable claim | The source survived; the premature unavailable conclusion was unsupported and withdrawn. Actual supporting-file gaps required separate recovery. REQUIRED_CONTRACT: accurate history | Root: preserve the incorrect claim as historical evidence; current HANDOFF/DECISIONS explicitly correct it. |

## Verification limits

File identity is not semantic correctness, provenance approval, privacy clearance,
independent backup, production readiness or provider qualification. Public metadata
checks explicitly cannot read the private archive in hosted CI. The local verifier
must receive the actual private root to prove availability. Public marker screening
and independent review do not prove that every possible confidential datum is absent.

No frozen candidate approval or hosted-parity claim is made before the existing
required workflow boundaries pass. PR #534 and the earlier five comparison payloads
retain their own review scopes, counts and acceptance conditions.

## Export correction and independent verification

Independent review reproduced an omitted-message defect: the first discussion
export selected assistant `channel`, but the stored records use `phase` values
`commentary` and `final_answer`. Its 91 records were all user messages. Root
classified this REQUIRED_CONTRACT under ARCH05, preserved the initial exports,
and created V2 snapshots from the same exact source prefixes. The correction
includes the stored visible phases, keeps tool/hidden/system/developer records
excluded, and records separate role counts. `DISCUSSION_COVERAGE_V2.json` is now
the current private coverage record. Independent verification re-read every selected source record and matched
all 1,170 exported messages (91 user, 1,079 assistant), 1,006,613 bytes. No
eligible record was omitted or ineligible/hidden record included under the
declared selector; the original exports remained exact. This finding is resolved.

## Final archive verification

The bounded preservation and verifier review is complete. Independent reviewers
verified both required corrections: accurate historical wording and complete
visible-message selection within the recorded prefixes. The optional malformed
mapping correction was also independently verified: `sources=[null]` now produces
structured `AUTHORITY_CENSUS_INVALID` without a traceback or personal path.

Root verification on the prepared working tree:

- All eleven required masters and 988 inventory entries re-read successfully:
  221,077,803 bytes. Public mode reports private NOT_CHECKED; explicit local mode
  reports VERIFIED. Backup stays UNPROVED and semantic acceptance NOT_GRANTED.
- Twenty standalone verifier tests and nine scope/route tests pass. Negative cases
  reject missing/duplicate/substituted artifacts, bad bytes, escaping/symlink paths,
  stale handoffs, tracked private files, fake acceptance, invalid timeouts and malformed
  authority. Actual synthetic Git histories reject wrong first-commit order and dirty
  hosted execution; deletions count toward the measured budget.
- Existing Phase1 modular, preflight-core and preflight-repository tests pass; ruff
  passes all changed Python files; mypy passes both new verifier/scope modules.
- `make quality` passes after retaining the existing 250-line context limit and
  refreshing only the evidence-quality module's whole-RCA-source hash. Existing
  selected text, rules, routing fixtures and the eight frozen V2 artifacts are unchanged.
- All public relative links resolve; independent public archive screening found no
  sensitive markers. The complete original comparison text is an exact suffix below
  its archival notice. Restricted sources are ignored and untracked in both worktrees.

First commit `5392dfe1` contains only the Issue535 preflight. The adapted preflight
was recorded locally before utility code; the GitHub PR is prepared after local
implementation. Therefore the playbook's pre-code PR-link checkpoint was not met;
commit ordering must not be cited as proof of that earlier publication checkpoint.
Root records this process deviation for review rather than rewriting its chronology.
Future increments must open the linked draft before implementation. This deviation
does not change the verified local copies or authorize merge.

This is approval of bounded local preservation and implementation review, under
user-delegated orchestration. It is not an exact-head freeze, hosted-parity result,
merge eligibility or carrier certification. Hosted commands/topologies remain
required before an exact candidate approval. The archive branch must retain the
PR534 integration dependency. No provider or paid service was used.
