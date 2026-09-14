# Prepared AGENTS navigation consumer

The current AGENTS already requires STATUS and CODEX_OPERATING_MODEL; both carry the new work-record flow. Mandatory session discovery therefore works while the exact anchored authority stays unchanged. CLAUDE is a tracked bridge to that authority.

The adjacent patch adds only navigation. Old SHA-256: `57ea2bdddd7f0f3df91c75ecb0e434e25aa0779a54d0a2603a7e32a87b5c9ca7`; proposed: `ea28b974127459e465cdb0b9bf1f19c4c54beaff3b1417be994f262786270532`. Independent entry review found no change to selected sections in repo-constitution, stage-authority or delegation; only their whole-source hashes would change.

A naive anchor-first replacement fails: Stage8 unconditionally checks the current AGENTS bytes and tests reject the historical pending-hash mechanism. A separate prerequisite must prove old-document validity, exact reviewed new-byte admission, rejection of same-PR authority/anchor edits, arbitrary bytes and later rollback, and retirement of the old hash. Design/test that transition under a separate prospective issue after carrier closeout. Do not apply a permissive two-hash allowlist or apply this patch on PR536.

The explicit heading is pending; the common discovery flow works through existing mandatory references.
