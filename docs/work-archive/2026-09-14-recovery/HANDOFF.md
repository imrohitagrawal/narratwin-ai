# Current archive handoff — Issue #535

INDEX_SHA256: b18fecd76056074c8d80536612fde21d389ddd4af396b8a43701f549785928f6

Start from [the index](INDEX.json), [decisions](DECISIONS.md),
[full comparison proposal](COMPARISON_AND_AMENDMENT.md), and
[archive instructions](../PROCESS.md). This is a local preservation and process
increment prepared on `phase-1-closure-process-535-work-archive` from main
`71e0568d460306c3837d9e641c78558486b5ab54`. Local preservation and independent review are complete. This branch is
prepared for repository review; it is not merged or certified by this handoff.

## Saved material

The long-lived shared checkout holds the exact originals under
`docs/work-archive/.restricted/2026-09-14-recovery/`. Use the privatePath values
in INDEX relative to that directory. The original owner plan is a readable
`OWNER_PLAN_2026-09-07.md`, exactly 65,097 bytes. The complete prior packet
contains 978 preserved files, including all ten recovered supporting masters.
Three corrected V2 user-visible discussion snapshots and their coverage receipt
are current; the initial user-only snapshots and their receipt are retained as
historical evidence of the corrected omission. The private inventory lists all content, including its README;
its own bytes are pinned separately by INDEX. The final archive-increment snapshot
also preserves its twenty public files, PR body draft and resource closeout; copied
metadata is historical and does not replace the root INDEX. Historical absolute locators
inside copied evidence are not the current archive paths.

Other worktrees and public clones do not contain private payloads. From an
issue worktree, pass the shared checkout's private directory explicitly to
`python3 scripts/work_archive.py --private-root <local-private-directory>`.
Do not interpret a public-only check as evidence that private files exist.

## Current decisions and open work

The comparison packet has bounded orchestrator approval under delegated user
authority. No further user answer is needed to preserve these files. Its policy
remains nonactivating and its original five payloads remain unchanged. No
provider is qualified, no new output is accepted, and operation defaults remain
uploads 0, creates 0, USD 0, retries 0, fallback NONE.

All ten source files are recovered. The separate semantic finding remains open:
four ADR0000 bibliography links were promoted to current requirements. Preserve
and correct through a bounded dependency replay and explicit governed candidate
supersession before renewed semantic certification; do not declare the unchanged
original mapping passed. Of 859 duplicate groups, the first twenty have bounded
review results (nineteen passes, one failure); 839 remain unreviewed.

Preserve PR #534 head `6fac239e226cfaa2bcd3b79d4e9bbe8e96feb10d` and base
`71e0568d460306c3837d9e641c78558486b5ab54`, frozen V2 fields and PR #522 cleanup.
Do not merge this archive branch ahead of the original carrier closeout. The
later comparison amendment starts from verified current main and requires the
distinct accepted-current transition; #521/#531/#520 dependencies remain.

## Ownership and next action

Root owns archive verification, independent review triage and branch closeout.
Project owner is private-source custodian. Retain all existing source copies and
this archive; no deletion is authorized. Independent backup is UNPROVED: Issue
#532 must establish a separate restricted store, custody and successful restore.
A same-machine archive is useful local preservation, not disaster recovery.

Complete hosted archive checks when the branch is published and retain its
carrier dependency. Resume the bounded semantic correction route; source-location questions are
resolved. At the next handoff, record new decisions and source cursors, refresh
INDEX descriptors, update this exact digest and re-run private read-back.
