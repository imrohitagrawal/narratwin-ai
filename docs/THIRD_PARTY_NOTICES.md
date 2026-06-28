# Third-Party Notices

Maintain this file for every third-party package, model, API, dataset, avatar provider, media asset, and generated sample.

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

## Rules

- Do not add a dependency, model, dataset, avatar tool, media asset, or provider without updating this file.
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
