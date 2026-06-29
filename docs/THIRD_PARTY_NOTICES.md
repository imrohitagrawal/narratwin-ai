# Third-Party Notices

Maintain this file for every third-party package, tool, skill source, GitHub Action, model, API, dataset, avatar provider, media asset, and generated sample.

This file is not legal advice. Treat it as the engineering license-review register.

| Component | Purpose | License/Terms | Commercial/Public Use Allowed? | Decision for MVP | Notes |
|---|---|---|---|---|---|
| Gemini API | LLM, translation, evaluation, optional embeddings/TTS | Google AI terms | Review before use | Optional | API key via `.env`; tests must not require a real key. |
| ChromaDB | Local vector store | Apache License 2.0 per upstream license file | Likely yes, subject to dependency review | Allowed after dependency review | Use behind internal vector-store interface. |
| FFmpeg | Video/subtitle assembly | LGPL/GPL depending on build configuration | Depends on build and linked codecs | Not needed for Slice 1 | Review exact package/build before enabling video output. |
| SadTalker | Optional local avatar provider | Apache License 2.0 per upstream license file; model/assets still need review | Needs review | Not enabled by default | Consent, privacy, model weights, and asset licensing must be checked. |
| Wav2Lip | Lip sync | Research/non-commercial risk must be treated as blocker for public/commercial path | No by default | Rejected for default path | Do not enable by default; only revisit after legal/license review. |
| HeyGen | Premium avatar provider | Provider terms | Review before use | Future optional adapter | Must not be hardcoded into core logic. |
| Tavus | Premium avatar provider | Provider terms | Review before use | Future optional adapter | Must not be hardcoded into core logic. |
| D-ID | Premium avatar provider | Provider terms | Review before use | Future optional adapter | Must not be hardcoded into core logic. |
| ElevenLabs | Premium TTS/voice provider | Provider terms | Review before use | Future optional adapter | Voice cloning requires explicit documented consent. |
| PM Skills | Product-management skill bundle | Pending upstream license review before activation | Not approved until reviewed | Governance only in Stage 0; candidate for Stage 1 | Recorded in `docs/SKILL_LOCK.md`; not activated in Stage 0. |
| GitHub Spec Kit | Spec and planning toolkit | Pending upstream license review before activation | Not approved until reviewed | Candidate for Stage 2 and Stage 3 planning | Recorded in `docs/SKILL_LOCK.md`; implementation commands blocked in Stage 0. |
| Addy Osmani Agent Skills | Engineering skill bundle | Pending upstream license review before activation | Not approved until reviewed | Reference-only guidance in Stage 0 | Used as local guidance only; no Stage 0 product implementation allowed. |
| Agent Skills Standard | Skill packaging convention | Pending upstream license review before activation | Not approved until reviewed | Governance source for future skill packaging | Recorded for operating-model consistency only. |
| GitHub Action: Checkout | CI repository checkout | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/checkout`. Not a product runtime dependency. |
| GitHub Action: Setup Python | CI Python runtime setup | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/setup-python`. Not a product runtime dependency. |
| GitHub Action: Upload Artifact | CI artifact upload | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/upload-artifact`. Not a product runtime dependency. |
| Gitleaks GitHub Action | CI secret scanning | Upstream action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `gitleaks/gitleaks-action`. Not a product runtime dependency. |
| GitHub Action: Markdownlint CLI2 | CI markdown validation | Upstream action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `DavidAnson/markdownlint-cli2-action`. Not a product runtime dependency. |

## Rules

- Do not add a dependency, tool, skill source, GitHub Action, model, dataset, avatar tool, media asset, or provider without updating this file.
- Do not enable non-commercial or research-only tools in recruiter-facing, public, portfolio, or commercial workflows.
- Do not enable voice cloning or face cloning without explicit consent workflow.
- Do not use premium providers in tests unless mocked.
- Document exact package names, versions, and license decisions when implementation begins.

## Slice 1 decision

Slice 1 should avoid avatar, TTS, subtitle, and video-rendering dependencies.

Allowed Slice 1 dependency classes:

- backend framework
- local storage
- vector-store abstraction
- test framework
- mock provider implementation
- frontend framework

Blocked for Slice 1:

- real avatar generation
- real voice cloning
- real face cloning
- Wav2Lip
- paid-only provider integration
