# Documentation architecture audit

Source checkpoint: PR536 head9e35fb357835c518be0c6ffcdda06c7f51dc91fe; 460 tracked docs, 51 root docs, 91 ADR sources, one native issue form and distributed embedded templates. Three read-only reviewers independently audited authority, lifecycle and executable integration.

| Finding | Evidence and root classification | Disposition / owner |
|---|---|---|
| Fragmented discovery | README and work index route work, but omit a complete document/template catalog. ADVISORY_DEBT now accepted scope. | Root: one generated catalog and contributor route. |
| Intake lacks user/source/owner context | stage_guardrail.yml at checkpoint contains six fields. ADVISORY_DEBT now intake requirement. | Root: distinct discovery/bug/implementation routes and form-specific required fields. |
| Guidance already exists | Engineering playbook intent/spec/design/preflight/PR/closeout sections and RCA own rules. DUPLICATE symptoms of discovery gap. | Link existing sources; no replacement policy or PR template. |
| Historical stage prose | ARCHITECTURE Stage2 baseline and CODEX Stage0 prose coexist with later changes. ADVISORY_DEBT. | Catalog labels historical limitations; preserve source bytes and use STATUS for current effect. |
| ADR numeric collisions | Prefixes0001,0002,0003,0037,0040,0048,0061,0069 have multiple distinct filenames. Outstanding registry requirement. | Stable full-path aliases and source-declared lifecycle; no renumbering or inferred acceptance. |
| Full documentation/capability contracts unfinished | Master Program V1 section8 requires more than navigation; no full capability implementation found. REQUIRED_CONTRACT outstanding program requirement. | Explicit partial scope; preserve broader328/426 and readiness ownership. |
| Weak entry substring check | Prior work validator accepted a commented expected path and broken real link; missing PROCESS/WORK template was unread. Existing ADVISORY_DEBT; new required navigation contract. | New checker validates actual supported links, targets and anchors. |
| Stacked push would fail | Guardrails discards non-main push base; a new537 stack includes two preflights. Legacy route rejects new paths. REQUIRED_CONTRACT for rejected route. | Reuse535 dedicated stage branch with prospective amended manifest; no routing change. |

No inference of complete conversation capture, private backup, full enterprise compliance or product readiness follows from this audit. Existing issues356/328/391/426/532/521/39 retain broader ownership.
