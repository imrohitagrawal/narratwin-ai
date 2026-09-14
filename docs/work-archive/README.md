# Work archive

Start here when resuming work, checking a decision, or locating recovered evidence.
This directory is the stable repository home for work records. It supplements the
accepted product contracts; archival presence does not make a proposal accepted.

| Material | Location | Meaning |
|---|---|---|
| Current handoff | [14 September recovery](2026-09-14-recovery/HANDOFF.md) | Current state, exact index identity, open work and next action |
| Artifact index | [INDEX.json](2026-09-14-recovery/INDEX.json) | Required originals, hashes, sizes and portable relative locations |
| Comparison plan | [Complete matrix and amendment](2026-09-14-recovery/COMPARISON_AND_AMENDMENT.md) | Archived reviewed proposal; not activated |
| Decisions and discussion coverage | [DECISIONS.md](2026-09-14-recovery/DECISIONS.md) | Reasoning, corrections, supersession and remaining uncertainty |
| Review and limitations | [REVIEW.md](2026-09-14-recovery/REVIEW.md) | Independent verification and what it does not prove |
| Retention and handoff procedure | [PROCESS.md](PROCESS.md) | Capture, verify, resume and restore responsibilities |
| Public normalized program | [Master Program V2](../governance/NARRATWIN_MASTER_PROGRAM_V2.md) | Existing nonactivating candidate; unchanged |
| Exact original owner plan | `.restricted/2026-09-14-recovery/OWNER_PLAN_2026-09-07.md` | Local restricted original, 65,097 bytes; not in public Git |
| Exact supporting files and full packet | `.restricted/2026-09-14-recovery/packet/` | Complete preserved recovery work; includes historical and superseded artifacts |
| Verbatim discussion exports | `.restricted/2026-09-14-recovery/discussions/` | Bounded user-visible session records; coverage receipt lives beside them |

The private archive is physically in the long-lived shared checkout. Other
worktrees and fresh clones contain this index but do not automatically contain
private files. Supply that private root explicitly when verifying from elsewhere.
All private paths are relative to that root; old absolute paths inside historical
records are provenance and must not be used as current retrieval instructions.

```sh
make work-archive-quality
python3 scripts/work_archive.py --private-root docs/work-archive/.restricted/2026-09-14-recovery
```

The first command checks public metadata and regression cases. The second must
read and hash actual private files. A public-only pass cannot establish private
availability. A missing private root is a failed local recovery check, not a reason
to ask the owner to resend a source before checking this index and retained copies.

**Independent backup is UNPROVED.** This local copy and the retained source packet
share a machine. Neither Git ignore rules nor file permissions are encryption or
disaster recovery. Issue #532 owns the separate restricted-store and restore work.

Issue #535 tracks this archive increment. Its branch is separate from the frozen
PR #534 carrier. No carrier certification, comparison activation, provider work,
spending, cleanup, deployment or production readiness follows from this archive.
