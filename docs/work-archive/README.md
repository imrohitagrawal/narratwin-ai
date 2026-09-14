# Historical recovery sources

Active programs, comparisons and working records now start at
[docs/work/INDEX.md](../work/INDEX.md). Follow the shared
[working-record procedure](../work/PROCESS.md). This retained directory holds
historical recovery decisions, source descriptors and compatibility verification.

The [recovery index](2026-09-14-recovery/INDEX.json) remains the exact eleven-source
verification profile. Its private payloads stay intact under the existing ignored
location; see the [custody map](../work/working-records/MIGRATION.json). A public
clone does not contain those private bytes. Independent backup remains UNPROVED.

The [active comparison](../work/demo-comparison/README.md),
[original program source owner](../work/master-program/README.md) and
[G1 source owner](../work/g1-certification/README.md) provide current navigation.
Old plans/reviews retain their historical status; retention is not acceptance.

Public verification: `make work-records-quality`. Explicit private read-back:
`python3 scripts/work_archive.py --private-root /path/to/registered-private-store`.
This command verifies original bytes and the inventory, not semantic certification
or backup. No sources may be deleted through this navigation change.
