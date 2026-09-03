# Third-Party Notices

Maintain this file for every third-party package, tool, skill source, GitHub Action, model, API, dataset, avatar provider, media asset, and generated sample.

This file is not legal advice. Treat it as the engineering license-review register.

| Component | Purpose | License/Terms | Commercial/Public Use Allowed? | Decision for MVP | Notes |
|---|---|---|---|---|---|
| brace-expansion 5.0.9 | Frontend development-tool transitive glob expansion | MIT; 5.0.9 fixes GHSA-rgw5-rvv9-x895 / CVE-2026-69152 affecting 5.0.8 | Tooling use only; product/public authority unchanged | Exact npm override for Issue `#360` | Mechanical lock refresh only; no runtime feature, provider, deployment, release, or production-readiness decision. |
| Minimal composed Node.js 26.7.0 dependency image | Frontend dependency/build stage | Node.js MIT; exact Docker Official Node Bookworm-slim source digest `sha256:cd565714d4da3e84bfd341e31448f81d47c6362198f152345297c9c1154e6341`; Chainguard image terms and included package licenses for exact `glibc-dynamic` digest `sha256:eaec65b25f35619be16f4992e7bae1128eafcf63c114f2859b800a7020c1ef70` and `gcc-glibc` digest `sha256:8cfe0b01dcf3ad08aa8d51811175749f7390228be059497ddc6d94551a68f66e` | Controlled local/container use only; public/commercial use remains unapproved | Issue `#376` builder isolation, replacing the expired Issue `#374` Alpine builder | Imports only Node, npm JavaScript, and GPL-3.0-or-later WITH GCC-exception-3.1 `libatomic` with truthful APK/SPDX identity. Node embeds non-shared OpenSSL 3.5.7 with QUIC disabled; no OS OpenSSL package, shell, package manager, or OpenSSL executable is included. This is not an upstream-fix or VEX claim. Exact dependency images must pass Trivy and Grype through Medium. |
| npm 12.0.2 with brace-expansion 5.0.9, ip-address 10.3.1, tar 7.5.21, and undici 6.28.0 | SHA-256/SHA-512-bound exact frontend build-stage package manager and affected nested package tarballs | npm and transitive package licenses require release review | Local/container build use only; omitted from final runtime | Issue `#374` dependency stage, isolated by Issue `#376` | Replaces vulnerable npm packages without ranged repair installs; BuildKit verifies exact registry archive SHA-256, Node verifies SHA-512 and extracted identity, and the resulting dependency stage must pass both Trivy and Grype through Medium. |
| Chainguard Node container image | Minimal non-root frontend standalone runtime | Chainguard Images terms and included package licenses require release review; signed multi-architecture image pinned to index digest `sha256:d8d2883b26d4fde4e524d0068cd78abbb23c7c2113a22e67a02cc73a9182552d`; signed SPDX declares Node.js 26.7.0 MIT and `npm-12 12.0.2-r2` Artistic-2.0 | Controlled local/container use only; public/commercial use remains unapproved | Issue `#374` runtime stage, refreshed by Issue `#389` | The final layer removes all general-purpose shell, network, and build tooling, including npm, npx, and BusyBox; final Trivy and Grype review remains clean through Medium. The immutable inventory uses a source-bound Next build ID, normalizes only validated per-build preview/server-action secret values, and requires secret freshness across an uncached reproduction build. The vulnerable Issue #374 digest/npm r1, mutable tags, and unscanned rollback are forbidden. No deployment, release, public-availability, or production-readiness authority is created. |
| Gemini API | LLM, translation, evaluation, optional embeddings/TTS | Google AI terms | Review before use | Optional | API key via `.env`; tests must not require a real key. |
| Amazon Web Services durability control plane (RDS for PostgreSQL, S3, KMS, Secrets Manager, IAM Identity Center) | Proposed production-like relational state, versioned artifact bytes, encryption, secret rotation, short-lived operator access, backup catalog and restore-validation isolation | AWS Customer Agreement and service terms; account, region, cost, data-residency and Security review required before activation | Subject to authorized AWS account and terms approval | Proposed by issue `#141`; disabled/not provisioned | ADR `0027` proposes RDS PostgreSQL 17.10 Multi-AZ and versioned S3 buckets in `ap-south-1`. No account, resource, credential, backup, object, target, or restore evidence exists. Paid/cloud usage must not be required by local/dev/test/CI. |
| ChromaDB | Local vector store candidate | Apache License 2.0 per upstream license file; `chromadb==1.5.9` currently has `PYSEC-2026-311` / `CVE-2026-45829` with no fixed version listed by `pip-audit` | Blocked until non-vulnerable version or explicit security exception | Deferred from Stage 4 active dependencies | Removed from active dependencies because dependency security gates block known vulnerable packages. Future use must stay behind an internal vector-store interface. |
| FFmpeg | Video/subtitle assembly | LGPL/GPL depending on build configuration | Depends on build and linked codecs | Not needed for Slice 1 | Review exact package/build before enabling video output. |
| SadTalker | Optional local avatar provider candidate | Apache License 2.0 per upstream repository summary; exact code, model weights, dependencies, assets, and generated-output rights still need review | Needs review | Demo Phase 0 / Checkpoint 1 research candidate only | Issues `#225`, `#229`, and `#235` may compare SadTalker as a local-model alternative, but no dependency, model, service, avatar behavior, or hosted output is enabled by this planning entry. |
| Wav2Lip | Lip-sync model candidate | Official repository says personal/research/non-commercial only | No for external/public/commercial paths by default | Rejected for default hosted demo path | Issues `#225`, `#229`, and `#235` record this as a rejected local-model candidate unless a future legal/license review explicitly changes the decision. |
| OpenVoice | Optional local voice-clone provider candidate | MIT per upstream repository summary; exact code, model weights, dependencies, and generated-output rights still need review | Needs review | Demo Phase 0 / Checkpoint 1 research candidate only | Issues `#225`, `#229`, and `#235` may compare OpenVoice as a local-model alternative, but no dependency, model, service, or voice-clone behavior is enabled by this planning entry. |
| XTTS-v2 | Local voice-clone model candidate | Coqui Public Model License 1.0.0; official Hugging Face license permits only non-commercial use of the model and outputs | No for external/public/commercial paths by default | Rejected for default hosted demo path | Issues `#225`, `#229`, and `#235` record this as a rejected local-model candidate for public or commercial-facing clone output. |
| HeyGen | Premium avatar/video provider candidate | Official API auth, async job/polling, pricing, usage limits, prompt-to-avatar, and Digital Twin consent docs refreshed 2026-07-21 | Review before use; disabled by default | Demo Checkpoint 1 PR4 optional avatar/video boundary candidate | Issues `#225`, `#229`, `#235`, and `#241` compare HeyGen for possible future Checkpoint 1 real avatar/video output. PR4 installs no SDK, stores no key, makes no provider call, enables no paid spend, and rejects Digital Twin or prompt-with-reference likeness paths without a later consent/provenance issue. |
| Tavus | Premium avatar/video provider candidate | Official API auth, create/get/delete video, stock/custom face, replica rights, and pricing docs refreshed 2026-07-21 | Review before use; disabled by default | Demo Checkpoint 1 PR4 optional avatar/video boundary candidate | Issues `#225`, `#229`, `#235`, and `#241` compare Tavus for possible future Checkpoint 1 real avatar/video output. PR4 installs no SDK, stores no key, makes no provider call, enables no paid spend, and rejects custom replica or real-person likeness paths without a later consent/provenance issue. |
| D-ID | Premium avatar/video provider candidate | Official Talks API, account-credit/pricing, and EULA synthetic-mark/watermark docs refreshed 2026-07-21 | Review before use; disabled by default | Demo Checkpoint 1 PR4 optional avatar/video boundary candidate | Issues `#225`, `#229`, `#235`, and `#241` compare D-ID for possible future Checkpoint 1 real avatar/video output. PR4 installs no SDK, stores no key, makes no provider call, enables no paid spend, and blocks D-ID egress unless a D-ID-approved synthetic-marking policy/version and deletion/retention facts are recorded. |
| ElevenLabs | Optional TTS provider adapter boundary | Official API pricing, API authentication, TTS endpoint, retention/deletion, errors/rate-limit, use policy, and voice-clone verification docs reviewed 2026-07-21 | Optional only; disabled by default | Demo Checkpoint 1 PR3 server-side TTS adapter boundary | Issues `#225`, `#229`, and `#235` compared ElevenLabs for future Checkpoint 1 real TTS; issue `#237` adds a disabled-by-default, SDK-free, fake-transport-tested Stage 6 adapter boundary. No real provider calls, provider account setup, dashboard configuration, paid plan activation, wallet funding, paid spend, client-side key exposure, or voice-clone behavior is enabled. Checkpoint 1 permits only stock/non-cloned voice provenance. Voice cloning remains out of scope and requires explicit documented consent in a later issue. |
| Railway | Hosted demo platform candidate | Official pricing/cost-control docs refreshed 2026-07-22; subscription plus usage costs can apply | Review before use | Future optional hosted-demo infrastructure | Issues `#225`, `#229`, `#235`, and `#243` compare Railway for possible invite-only hosted demo deployment, but PR5 creates only local/fake access/quota/retention evidence. No account, resource, secret, deployment, paid spend, or production claim is enabled. |
| Vercel | Hosted frontend platform candidate | Official pricing/plan docs refreshed 2026-07-22; Hobby is personal/non-commercial and commercial use requires paid tiers | Review before use | Future optional hosted-demo infrastructure | Issues `#225`, `#229`, `#235`, and `#243` compare Vercel for possible invite-only hosted demo frontend hosting, but PR5 creates only local/fake access/quota/retention evidence. No account, resource, secret, deployment, paid spend, or production claim is enabled. |
| Render | Hosted demo platform candidate | Official free-instance docs refreshed 2026-07-22; free web services spin down after idle time and can cold-start slowly | Review before use | Future optional hosted-demo infrastructure | Issues `#225`, `#229`, `#235`, and `#243` compare Render for possible invite-only hosted demo deployment, but PR5 creates only local/fake access/quota/retention evidence. No account, resource, secret, deployment, paid spend, or production claim is enabled. |
| PM Skills | Product-management skill bundle | Pending upstream license review before activation | Not approved until reviewed | Governance only in Stage 0; candidate for Stage 1 | Recorded in `docs/SKILL_LOCK.md`; not activated in Stage 0. |
| GitHub Spec Kit | Spec and planning toolkit | Pending upstream license review before activation | Not approved until reviewed | Candidate for Stage 2 and Stage 3 planning | Recorded in `docs/SKILL_LOCK.md`; implementation commands blocked in Stage 0. |
| Addy Osmani Agent Skills | Engineering skill bundle | Pending upstream license review before activation | Not approved until reviewed | Reference-only guidance in Stage 0 | Used as local guidance only; no Stage 0 product implementation allowed. |
| Agent Skills Standard | Skill packaging convention | Pending upstream license review before activation | Not approved until reviewed | Governance source for future skill packaging | Recorded for operating-model consistency only. |
| UI/UX Pro Max CLI and Codex skill | UI/UX design intelligence for Stage 7 avatar rendering/export workflow design review | MIT per `ui-ux-pro-max-cli@2.10.0` npm metadata; upstream repository pin still requires release review | Yes for internal design guidance after pin review; not a runtime dependency | Stage 7 design guidance only | Installed globally as `ui-ux-pro-max-cli@2.10.0` and initialized with `uipro init --ai codex`; generated `.codex/skills/ui-ux-pro-max` files are ignored and must not be committed. |
| Addy Osmani Performance Optimization Skill | Stage 8 performance budget and smoke-test guidance | Pending upstream license verification for the locally vendored copy | Guidance only | Stage 8 skill guidance | Activated as `.codex/skills/active/performance-optimization`; not a runtime dependency. |
| Addy Osmani Security and Hardening Skill | Stage 8 request/upload/dependency/container hardening guidance | Pending upstream license verification for the locally vendored copy | Guidance only | Stage 8 skill guidance | Activated as `.codex/skills/active/security-and-hardening`; not a runtime dependency. |
| Addy Osmani Shipping and Launch Skill | Stage 8 release checklist, runbook, rollback, and launch-readiness guidance | Pending upstream license verification for the locally vendored copy | Guidance only | Stage 8 skill guidance | Activated as `.codex/skills/active/shipping-and-launch`; not a runtime dependency. |
| Stage 7 mock/local avatar demo artifacts | First-party generated HTML demo export, JSON render manifest, and JSON video export placeholder samples | First-party generated from approved grounded script text; no third-party avatar media, model, or provider asset used | Yes for local/dev/test review with AI-generated avatar/video disclosure | Stage 7 mock/local avatar rendering and export | The mock/local `AvatarProvider` emits deterministic `text/html` and `application/json` artifacts only, including provider config and placeholder metadata. It does not use paid avatar providers, cloned identities, third-party likenesses, stock media, real video encoders, or non-commercial research tools. |
| Quiet Presence synthetic presenter sample | Project-directed photorealistic fictional adult Indian woman presenter still for `/demo` | Selected from three OpenAI image-generation candidates created on 2026-08-05 from text-only product visual direction, without an uploaded or real-person reference, cloned identity, customer data, credentials, or copied third-party media; output need not be unique and is not intended to depict or endorse a real person | Internal local/mock product review only pending separate public-distribution and legal review | Issue `#358` local asset | Selected source PNG SHA-256 `47860cae597affd9e41f16077a76ef9d60fd6260058d9c400fb2701e150cdcb8`; mechanically converted with Sharp `0.35.3` to the committed 1536×1024 RGB WebP at `frontend/public/demo/narratwin-synthetic-presenter.webp`, 182,126 bytes, SHA-256 `d8c4ecb2acadcc3440b7be345b5620717ea0644a5643e41986b9d3f2ea1c30d1`. Conversion may not preserve every embedded provenance signal, so the repository checksum binds the reviewed derivative, not generation authenticity. The UI visibly and accessibly labels it as a fictional synthetic still preview and makes no speaking, animation, video, personal identity, product-runtime provider, deployment, release, or production claim. Design-time generation was external; product-runtime provider calls and spend remained zero. |
| Myra synthetic presenter sample | Owner-selected original fictional Indian adult presenter still for the controlled-local Cut 1 | OpenAI image generation on 2026-08-07 under the OpenAI Rest-of-World Terms of Use and OpenAI Service Terms from text-only direction with no uploaded or real-person reference, cloned identity, biometric data, customer data, or copied third-party media; output need not be unique and is not intended to depict or endorse a real person | Controlled-local review only pending separate public-distribution and legal review | Issue `#383` local asset | Owner selected Myra A. Source PNG SHA-256 `a4186431ca0a037620c90f5835e6fb6964d29934b4e2dc517c2929a87396c27d`; converted with Sharp `0.35.3` under Apache-2.0 to `frontend/public/demo/myra-synthetic-presenter.webp`, 1536×1024 WebP/yuv420p, 155,374 bytes, SHA-256 `30290deeea9abc85dde851006e3886dd0d9d6d299e4b54aa86ae3300a5e05d97`. The reviewed derivative is checksum-bound; no public, distribution, release, deployment, or production authority is created. |
| Raj synthetic presenter sample | Owner-selected original fictional Indian adult presenter still for the controlled-local Cut 1 | OpenAI image generation on 2026-08-07 under the OpenAI Rest-of-World Terms of Use and OpenAI Service Terms from text-only direction with no uploaded or real-person reference, cloned identity, biometric data, customer data, or copied third-party media; output need not be unique and is not intended to depict or endorse a real person | Controlled-local review only pending separate public-distribution and legal review | Issue `#383` local asset | Owner selected Raj C. Source PNG SHA-256 `d829196db1d84173fa077ff099450dde5dd186b39efdd5a3b9a1bac2ab6528a4`; converted with Sharp `0.35.3` under Apache-2.0 to `frontend/public/demo/raj-synthetic-presenter.webp`, 1536×1024 WebP/yuv420p, 59,192 bytes, SHA-256 `663007e0c7603e80c179cfd2b92bb463d80765890c06ec4886eddabafafa26dd`. The reviewed derivative is checksum-bound; no public, distribution, release, deployment, or production authority is created. |
| Stage 8 demo seed data | First-party markdown fixture for the controlled local release-readiness demo | First-party repository content | Yes for local/dev/test and controlled demonstrations | Stage 8 demo seed data | `demo/stage8_seed_project.md` contains synthetic product facts only; no third-party media, model output, provider output, personal data, or secrets. |
| Hosted-demo local/fake evidence records | First-party local access/quota/retention/disclosure metadata for reviewer evidence | First-party generated metadata only | Yes for local/dev/test review | Demo Checkpoint 1 PR5 hosted-demo access evidence | `backend/app/hosted_demo.py` creates metadata-only local/fake records and redacted events. It does not add hosting infrastructure, third-party SDKs, provider calls, hosted URLs, paid spend, cloned identity, media bytes, provider payloads, or secrets. |
| Phase 1 golden-question dataset | First-party JSONL governance/eval acceptance contract | First-party repository content | Yes for local/dev/test and governance review | Phase 1 Closure static eval contract | `docs/evals/phase1_golden_questions.jsonl` contains first-party questions, expected answers, required claims, forbidden claims, evidence paths, citation policy, metric floors, and safety-boundary fixtures. It is not third-party data and is not yet executed by the eval runner. |
| GitHub Action: Checkout | CI repository checkout | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/checkout`. Not a product runtime dependency. |
| GitHub Action: Setup Python | CI Python runtime setup | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/setup-python`. Not a product runtime dependency. |
| GitHub Action: Setup Node | CI Node.js runtime setup | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Stage 3 CI dependency | Source: `actions/setup-node`. Not a product runtime dependency. |
| GitHub Action: Upload Artifact | CI artifact upload | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/upload-artifact`; used for eval and Docker image scan reports. Not a product runtime dependency. |
| Gitleaks GitHub Action | CI secret scanning | Upstream action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `gitleaks/gitleaks-action`. Not a product runtime dependency. |
| GitHub Action: Markdownlint CLI2 | CI markdown validation | Upstream action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `DavidAnson/markdownlint-cli2-action`. Not a product runtime dependency. |
| OWASP ZAP | Future OWASP baseline scan for web security review | Apache License 2.0 per OWASP ZAP project; exact action/container pin required before CI use | Yes after pin and config review | Planned Stage 3/8 security tool, not enabled yet | Reference: `https://www.zaproxy.org/`; baseline scan to run only after a web surface exists. |
| OWASP ASVS | Application security control reference | OWASP documentation/license terms; do not copy large text without review | Yes as reference material | Reference only | Used to frame security baseline controls; not a runtime dependency. Reference: `https://owasp.org/www-project-application-security-verification-standard/`. |
| OWASP Top 10 for LLM Applications | AI safety risk reference | OWASP documentation/license terms; do not copy large text without review | Yes as reference material | Reference only | Used to frame prompt injection, vector/embedding, output-handling, supply-chain, and consumption risks. Reference: `https://genai.owasp.org/llm-top-10/`. |
| FastAPI | Future backend HTTP API foundation | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; no backend product routes implemented in Stage 3. |
| Uvicorn | Future local ASGI server foundation | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; no runtime deployment code implemented in Stage 3. |
| Pydantic | Future schema validation foundation | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; supports future typed contracts. |
| SQLAlchemy | Future relational persistence foundation | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; no database schema or migrations implemented in Stage 3. |
| psycopg and psycopg-binary | Future PostgreSQL driver foundation | Pending dependency license review before release | Needs review before release | Stage 3 manifest only | Added through `pyproject.toml`; no database connection code implemented in Stage 3. |
| Alembic | Future database migration tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; no migration scripts implemented in Stage 3. |
| Redis Python client | Future queue/cache integration foundation | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; no Redis runtime code implemented in Stage 3. |
| python-multipart | Future upload parsing dependency for FastAPI | Pending dependency license review before release | Likely yes after dependency review | Stage 3 manifest only | Added through `pyproject.toml`; upload handling remains Stage 4 scope. |
| pypdf | Future PDF text extraction for project knowledge ingestion | BSD-3-Clause per upstream license and PyPI metadata; full public-distribution review remains pending | Permitted for controlled-local dependency preparation; public use remains unapproved | Stage 4 dependency prep; Issues `#401`, `#499` security prerequisites | Direct lower bound and sole lock record move to official 6.16.2 after new advisories affected 6.15.0. Official PyPI binds wheel SHA-256 `c8b09a59399062fb45a1b8156c18a787a10a3dae03ac9674397a226712c94604` and sdist SHA-256 `595647f6191de6f402cfde1d0c455d6cbccbd509aac32b34783009c032de5d6e`. Product code does not import pypdf; PDF uploads remain rejected and are not represented as supported. |
| nanoid | Transitive PostCSS identifier utility in the frontend toolchain | MIT per upstream and official npm metadata | Permitted for controlled-local dependency tooling; public-distribution review remains pending | Frontend transitive dependency; Issues `#403`, `#428` | Sole lock record moves to official 3.3.18 for the expanded CVE-2026-67213 range. Registry SHA-512 is `DTg4MJbGMWkfi6VZFdNt2/caMbQy4Ou+Op/hJQvGEWcnVfoA1QA+xzRKAzw9jD6+GVOOeYr/mIcuDSdug6F6+w==`. No direct dependency or product behavior is added. |
| python-docx | DOCX text extraction for project knowledge ingestion | Pending dependency license review before release | Likely yes after dependency review | Stage 4 dependency prep | Added as `python-docx==1.2.0`; DOCX upload behavior still requires Stage 4 validation and safety controls. |
| Markdown | Markdown parsing for approved project knowledge | Pending dependency license review before release | Likely yes after dependency review | Stage 4 dependency prep | Added as `markdown==3.10.2`; markdown input must still be treated as untrusted uploaded content. |
| Beautiful Soup | HTML parsing and sanitization support for ingested content | Pending dependency license review before release | Likely yes after dependency review | Stage 4 dependency prep | Added as `beautifulsoup4==4.15.0`; output encoding and sanitization rules remain required. |
| tiktoken | Token counting for chunking and prompt budget controls | Pending dependency license review before release | Likely yes after dependency review | Stage 4 dependency prep | Added as `tiktoken==0.13.0`; budget enforcement still requires Stage 4 implementation and tests. |
| sentence-transformers | Local embedding model runtime candidate | Pending dependency and model license review before release | Needs review before release | Stage 4 optional provider extra, disabled by default | Declared as optional `sentence-transformers>=5.6.0`; not installed in the backend runtime image for the mock/local slice. Any selected embedding model must be separately recorded before use. |
| OpenAI Python SDK | Optional provider SDK for future LLM integration | Provider and package terms require review before use | Review before use | Stage 4 optional provider extra, disabled by default | Declared as optional `openai>=2.44.0`; local/dev/test must keep paid providers optional and disabled. |
| LiteLLM | Provider routing abstraction candidate | Pending dependency license and telemetry review before use | Review before use | Stage 4 optional provider extra, disabled by default | Declared as optional `litellm>=1.90.1`; provider keys must remain environment-only and tests must use mocks. |
| pgvector Python package | PostgreSQL vector type integration candidate | Pending dependency license review before release | Likely yes after dependency review | Stage 4 dependency prep | Added as `pgvector==0.4.2`; no database schema or migration is enabled by this dependency alone. |
| Langfuse Python SDK | Observability and trace export candidate for Stage 5 AI runs | Pending dependency license and telemetry review before release | Review before use | Stage 5 dependency prep, disabled until explicitly configured | Added as `langfuse==4.12.0`; local/dev/test must not require a Langfuse service or key, and trace export must avoid prompts, uploaded content, provider secrets, and PII by default. |
| OpenTelemetry Python API/SDK and FastAPI instrumentation | Local trace/run metadata and FastAPI request instrumentation | Pending dependency license review before release | Likely yes after dependency review | Stage 5 dependency prep | Added as `opentelemetry-api==1.37.0`, `opentelemetry-sdk==1.37.0`, and `opentelemetry-instrumentation-fastapi==0.58b0`; exporters must remain local/mock by default until telemetry sinks are explicitly configured. |
| Prometheus Python client | Local metrics endpoint/counter support for Stage 5 observability | Pending dependency license review before release | Likely yes after dependency review | Stage 5 dependency prep | Added as `prometheus-client==0.25.0`; metrics must use bounded labels and avoid user content, prompts, source text, or provider outputs. |
| structlog | Structured application logging for Stage 5 observability | Pending dependency license review before release | Likely yes after dependency review | Stage 5 dependency prep | Added as `structlog==26.1.0`; log events must avoid secrets, raw uploads, prompts, provider payloads, and generated content unless explicitly redacted. |
| audioop-lts | Python 3.13-compatible `audioop` module shim required by pydub | Pending dependency license review before release | Likely yes after dependency review | Stage 6 dependency prep | Added as `audioop-lts==0.2.2` after `pydub==0.25.1` failed import on Python 3.13 without the removed stdlib `audioop` module. |
| Babel | Locale-aware formatting and localization support for Stage 6 multilingual scripts | Pending dependency license review before release | Likely yes after dependency review | Stage 6 dependency prep | Added as `babel==2.18.0`; used for mock/local voice manifest language display names; localization logic must stay deterministic in tests and must not require paid providers. |
| langcodes | Language tag parsing and normalization for multilingual script, subtitle, and voice-adapter metadata | Pending dependency license review before release | Likely yes after dependency review | Stage 6 dependency prep | Added as `langcodes==3.5.1`; accepted language tags must be validated before use in provider routing or rendered output. |
| pydub | Audio segment handling for mock/local voice-adapter timing profiles | Pending dependency and FFmpeg/runtime review before release | Review before release | Stage 6 dependency prep | Added as `pydub==0.25.1`; used only to derive a local mock audio profile in the JSON voice manifest, not to export playable audio. Local/dev/test must not require premium TTS providers, and any FFmpeg dependency must remain documented separately before audio export is enabled. |
| srt | SubRip subtitle parsing and serialization for Stage 6 subtitle export | Pending dependency license review before release | Likely yes after dependency review | Stage 6 dependency prep | Added as `srt==3.5.3`; subtitle output must include accessibility notes and deterministic tests. |
| Ragas | Retrieval/generation evaluation framework candidate | `ragas==0.4.3` currently has `CVE-2026-6587` with no fixed version listed by `pip-audit` | Blocked until non-vulnerable version or explicit security exception | Deferred from Stage 4 active dependencies | Removed from active dependencies; Stage 4 eval smoke uses deterministic local JSON fixtures instead. |
| Giskard | Model and LLM testing framework candidate for Stage 5 guardrail evaluation | `giskard==2.5.0` has `CVE-2024-52524`; fixed releases currently require `scipy<1.12.0`, which conflicts with the repo's Python 3.13 baseline | Blocked until a secure Python 3.13-compatible dependency set exists | Not active | Evaluated during Stage 5 dependency prep and removed from active dependencies after import and `pip-audit` failures. |
| Hugging Face Datasets | Evaluation and fixture dataset loading candidate | Pending dependency and dataset license review before release | Dataset-dependent | Stage 4 optional eval extra | Declared as optional `datasets>=5.0.0`; Stage 4 smoke eval uses deterministic JSON fixtures and does not install datasets in the backend runtime image. Every dataset used by the product must be separately recorded. |
| Stage 4 Python transitive dependencies | Locked dependency graph for Stage 4 dependency prep | See each upstream package license; review required before release | Pending dependency review | Stage 4 dependency prep | `uv.lock` records active transitive additions from the Stage 4 dependency set. Vulnerable ChromaDB/Ragas transitives, including `diskcache==5.6.3`, were removed after dependency security review. |
| pytest and pytest-cov | Python test and coverage tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 quality tooling | Runs locally without paid providers. |
| Ruff | Python lint tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 quality tooling | Used by `scripts/ci/backend-lint.sh`. |
| mypy | Python type checking tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 quality tooling | Used by `scripts/ci/backend-lint.sh`. |
| Bandit | Python security lint tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 quality tooling | Added to dev dependencies for future security checks. |
| pip-audit | Python dependency vulnerability scanning | Pending dependency license review before release | Likely yes after dependency review | Stage 3 dependency-security tooling | Used by `scripts/ci/dependency-security.sh`. |
| pre-commit | Local hook framework | Pending dependency license review before release | Likely yes after dependency review | Stage 3 local quality tooling | Added to dev dependencies; hooks are not installed automatically. |
| Next.js | Frontend framework | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend foundation; issue `#269` dependency-audit patch | Chosen by Stage 2 architecture; minimal scaffold only, no provider or hosted/public workflow. Issue `#269` updates the existing Next.js dependency to clear current high-severity npm audit advisories required by `make dependency-audit`. |
| React and React DOM | Frontend UI runtime | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend foundation | Required by Next.js scaffold. |
| PostCSS | CSS processing dependency used through Next.js and Vite | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend dependency override; issue `#289` audit remediation | `frontend/package.json` pins an override to `8.5.23` to clear the current PostCSS audit advisory while preserving the Next.js scaffold and avoiding a Next downgrade. |
| minimatch and brace-expansion | Transitive glob/brace expansion dependencies used through frontend ESLint tooling | MIT per npm package metadata; pending full dependency license review before release | Likely yes after dependency review | Stage 3 frontend dependency override; issue `#296` audit remediation | `frontend/package.json` pins overrides to `minimatch@10.2.5` and `brace-expansion@5.0.8` to clear GHSA-mh99-v99m-4gvg in the current npm audit without changing product runtime behavior. |
| sharp, unrs-resolver, fsevents install scripts | npm install-script approvals for frontend dependency tree | Pending dependency script review before release | Accepted for Stage 3 after local install review | Stage 3 frontend dependency install hygiene | `frontend/package.json` records pinned `allowScripts` entries for the currently installed versions so npm 11 installs are explicit and warning-free. Issue `#245` adds a `sharp` override to `^0.35.3` to clear GHSA-f88m-g3jw-g9cj in the Next.js optional image dependency path without changing application runtime behavior. |
| TypeScript | Frontend type checking | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Used by frontend `typecheck` script. |
| ESLint and eslint-config-next | Frontend lint tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Used by frontend `lint` script. |
| js-yaml | Transitive YAML parser used through `@eslint/eslintrc` frontend lint tooling | MIT per npm registry package metadata; full dependency and public-distribution review remains pending | Permitted for controlled-local development/test tooling only; public use remains unapproved | Issue `#396` security prerequisite | The lockfile-only repair moves the sole transitive entry from affected 4.3.0 to exact 4.3.1 with npm-registry URL and SHA-512 integrity for `GHSA-5p4m-2wfm-xmqj`. Its build-input effect is bound to independently reproduced arm64/amd64 final-runtime inventories. It adds no direct dependency, override, product runtime behavior, provider, media, or public-distribution authority. |
| Vitest | Frontend unit test runner | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Installed for future component/unit tests. |
| Playwright | Browser automation and E2E test tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Used for the Stage 3 health-check-only frontend smoke test. |
| Lighthouse | Frontend performance/accessibility/best-practices/SEO audit tooling | Apache License 2.0 per upstream Lighthouse project; package metadata review still required before release | Yes as dev tooling after dependency review | Stage 8 frontend Lighthouse checks | Added as a frontend dev dependency and locked in `frontend/package-lock.json`; issue `#219` updates the lock to `lighthouse@13.4.1` with `@sentry/node@10.67.0` and `@opentelemetry/core@2.9.0`; issue `#296` supersedes the older `brace-expansion` transitive note by pinning `minimatch@10.2.5` and `brace-expansion@5.0.8` for the current npm audit advisory. Not a product runtime dependency. |
| Locust | Local HTTP load/performance smoke tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 8 API performance smoke profile | Added as a Python dev dependency and locked in `uv.lock`; not installed in the backend runtime image. |
| Trivy | Docker image vulnerability scan tooling | Apache License 2.0 per upstream project; Homebrew formula and Docker image metadata still require release review | Yes as local/CI security tooling after dependency review | Stage 8 Docker image scan | Installed locally as `trivy 0.72.0`; `scripts/ci/docker-image-scan.sh` uses local Trivy first and pinned Dockerized Trivy `aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f` as fallbacks to block critical/high backend/frontend image vulnerabilities and emit SARIF. Confirmed vulnerability reports fail; tool failures without usable SARIF can fall through to the next scanner. |
| Docker Scout CLI | Docker image vulnerability scan tooling | Docker Desktop/Docker Scout terms | Review before CI dependency claims | Stage 8 Docker image scan fallback | `scripts/ci/docker-image-scan.sh` uses Docker Scout after Trivy/Grype/Dockerized Trivy fail to produce a usable SARIF report, while preserving hard failure for confirmed critical/high findings. |
| Grype | Docker image and filesystem vulnerability scan tooling | Apache License 2.0 per upstream project; Homebrew formula metadata still requires release review | Yes as local/CI security tooling after dependency review | Stage 8 Docker image scan | Installed locally as `grype 0.115.0` to scan backend/frontend images without Docker Scout login; not a product runtime dependency. |
| CPython security backports | Three official Python 3.13 runtime security patches for issue `#151` | Python Software Foundation License v2; source commits recorded in `security/cpython-3.13.14/backports.json` | Yes for backend runtime only after review | Issue `#151` security remediation | Historical Python `3.13.14` image repair for `CVE-2026-11940`, `CVE-2026-11972`, and `CVE-2026-15308`; superseded in the backend container when Issue `#436` is accepted. |
| CPython 3.13.15 source release | Backend interpreter built from official source | Python Software Foundation License v2; archive SHA-256 `1e66a7945a48390ee4c2a4268a0e4185884059a13c4aab6d148aa208deea4a76`; PSF release signature verified during build | Yes for backend runtime only after review | Issue `#436` backend TLS isolation | Compiler and source remain build-only; the final image retains the source-built interpreter and its discoverable binary identity. |
| Alpine 3.21.7 minimal backend components | Backend TLS, CA, timezone, and runtime libraries | Alpine package licenses; official multi-architecture index digest `sha256:48b0309ca019d89d40f670aa1bc06e426dc0931948452e8491e3d65087abc07d`; exact `libcrypto3`/`libssl3` `3.3.7-r0` | Local/container use only; release review remains required | Issue `#436` backend TLS isolation | The final scratch image retains truthful Alpine package records. OpenSSL 3.3 predates the OpenSSL 3.5 QUIC server implementation affected by `CVE-2026-14456`; this is not a claim that the package is free of all vulnerabilities. |
| uv | Python package/project manager used in the backend image build | Pending dependency license review before release | Likely yes after dependency review | PR `#284` Docker image scan unblock; Issue `#436` minimization | `backend/Dockerfile` uses `uv==0.11.32` only in the build stage to create the application virtual environment. The final Issue `#436` scratch runtime excludes uv, pip, and their build-only implementation metadata. |
| httpx | FastAPI TestClient transport dependency for API tests | Pending dependency license review before release | Likely yes after dependency review | Stage 3 API test tooling | Used only in tests. |
| httpx2 | Starlette/FastAPI TestClient transport dependency for API tests | Pending dependency license review before release | Likely yes after dependency review | Stage 3 API test tooling | Used only in tests to avoid deprecated TestClient transport warnings. |
| Semgrep | Static analysis/security rule runner | Pending dependency license review before release; version `1.175.0` is isolated under `tools/semgrep` and resolves upstream Click `8.4.2`, MCP `1.29.0`, and PyJWT `2.13.0` without an override | Likely yes after dependency and security-owner review | Stage 3 security tooling only; excluded from application/runtime lock and image | Runs repo-local `semgrep.yml` with metrics disabled, Python 3.13, strict zero-ignore audits, scan and canaries. MCP server functionality is not started or used. Issue `#460` removes the expired Issue `#150` compatibility exception and rejects future overrides. |
| Docker Compose | Local service orchestration | Docker terms and component licenses require review before release | Yes after dependency review | Stage 3 repo foundation | Used for local health-check-only backend and frontend containers. |
| PostgreSQL container image | Local relational metadata service foundation | PostgreSQL License; pinned to `postgres:17-alpine@sha256:dc17045ccfd343b49600570ea734b9c4991cf1c3f3302e67df51e3b402dd55c4` for Stage 3 | Yes for local/dev after release review | Stage 3 local Compose foundation | Local service only; no schema, migration, or product persistence code is implemented in Stage 3. |
| Redis container image | Local cache/queue service foundation | BSD-3-Clause for Redis OSS; pinned to `redis:8-alpine@sha256:9d317178eceac8454a2284a9e6df2466b93c745529947f0cd42a0fa9609d7005` for Stage 3 | Yes for local/dev after release review | Stage 3 local Compose foundation | Local service only; no cache, queue, or product runtime code is implemented in Stage 3. |

## Issue #383 source and conversion record

The approved image-generation skill created three independent text-only
candidates per presenter on 2026-08-07. No reference image was supplied, Meera
was not a facial reference, and neither prompt named a real person. The owner
selected Myra A and Raj C in Issue `#383` comment `5219144636`.

The exact Myra generation prompt, including its negative prompt, is frozen at
SHA-256 `17605aaf0bd34ac29b0e56b09e61a6791ccc2b340832f2f6bd9fea47f2b9c26d`:

```text
Use case: photorealistic-natural
Asset type: NarraTwin AI controlled-local synthetic presenter identity portrait and future speaking-animation anchor

Primary request: Create a completely original fictional adult Indian woman presenter named Myra, visibly and unambiguously 24–28 years old. She must not be based on, copied from, or intended to resemble any actress, celebrity, influencer, public figure, known individual, existing presenter, or uploaded image. Give her exceptionally beautiful, memorable, leading-lady-caliber screen presence while keeping her believable, culturally respectful, professional, warm, technically credible, and entirely original.

Scene/backdrop: Neutral, elegant premium studio background in a restrained warm taupe or softly graded neutral tone, with subtle depth and no objects, signage, patterns, or clutter.

Subject and presence: A young adult Indian woman with a natural fair or light-warm Indian complexion, realistic skin texture, and refined harmonious facial structure. She appears highly intelligent, technically credible, calm, composed, confident, emotionally intelligent, graceful, sophisticated, well-cultured, warm, sweet, approachable, persuasive, and compelling. Her charisma should come from beauty, warmth, clarity, confidence, and direct audience engagement. Her presentation may be tastefully alluring through a captivating, subtly seductive but professional gaze; never sexualized, explicit, vulgar, coercive, or inappropriate for a public technology demonstration.

Face and eyes: Large, expressive, beautiful dark eyes; direct but warm eye contact with the camera; intelligent, confident, magnetic gaze; natural eyebrows; refined facial proportions; realistic pores and subtle natural skin variation; polished but restrained professional makeup; no artificial doll-like treatment. Use a friendly, composed expression with a relaxed closed mouth, fully visible lips, unobstructed jawline, and a neutral mouth position suitable for later lip synchronization.

Hair: Long, open, naturally black Indian hair, thick, healthy, and glossy, extending clearly below both shoulders. Style it in soft natural waves or refined straight-to-wavy layers. Keep the hair visibly open while arranging it away from the eyes, lips, jawline, and critical facial-animation regions.

Attire: A premium deep-maroon, wine-red, burgundy, or dark-red Indian saree with a clearly visible refined golden or gold-zari border. Use realistic luxurious textile texture, elegant authentic drape, and a sophisticated matching blouse. Show enough upper torso for the saree construction and gold border to be unmistakable. The styling must feel modern yet traditional, youthful, refined, culturally grounded, and suitable for a premium AI technology presenter—not bridal, costume-like, excessively ceremonial, or gaudy.

Jewelry: Jewelry is mandatory and clearly visible. Give Myra a coordinated, premium, realistic, restrained gold, Kundan, or Polki necklace with subtle diamond accents, plus refined matching earrings or restrained jhumkas. A small elegant bindi may be included if it improves the composition. Jewelry must harmonize with the saree’s gold border, look intentionally professionally styled, and remain consistent as an identity anchor. Keep every piece clear of the mouth, jawline, hair, neck-animation region, and facial features. Do not make the jewelry oversized, heavy, cheap-looking, bridal, or costume-like.

Style/medium: High-end cinematic photorealistic studio portrait photography with professional color grading, realistic skin, hair, textile, gold, gemstone, and jewelry textures. Original fictional identity; premium technology-presenter polish without glamour-retouched plasticity.

Composition/framing: Exact 3:2 landscape composition intended for a 1536×1024 derivative. Centered, symmetrical, front-facing head, shoulders, and upper-torso portrait at eye level. Full head, long hair below the shoulders, neck, both shoulders, saree drape, golden border, necklace, earrings, and sufficient upper torso must be visible. Direct natural camera engagement. Keep the face large enough for later animation while leaving clean margin around the hair and shoulders. No hands are required in frame.

Lighting/mood: Soft flattering frontal key light with gentle fill and controlled separation light. Preserve natural facial dimensionality while keeping the eyes, mouth, jaw, hair edges, saree border, and jewelry clearly readable. Cinematic, elegant, warm, magnetic, confident, intelligent, and approachable mood.

Constraints: One anatomically coherent fictional adult Indian woman only; apparent age 24–28; natural complexion without bleaching or artificial whitening; long open black hair; deep-red or deep-maroon saree with clearly visible gold border; mandatory visible coordinated necklace and earrings; unobstructed eyes, lips, mouth, teeth area, jawline, and animation regions; realistic facial symmetry and anatomy; no facial or image reference; no cloning; no biometric or customer data; no copied third-party media; no text, letters, numbers, logo, trademark, symbol, watermark, signature, border, UI, microphone, headset, handheld object, or background prop.

Negative prompt: Do not depict a child, teenager, person under 18, woman over 28, middle-aged woman, older woman, age-ambiguous adult, non-Indian identity, celebrity lookalike, recognizable actress, influencer, public figure, or real-person resemblance. No bob, pixie cut, short hair, shoulder-length hair, tied-back hair, ponytail, braid, bun, gray hair, salt-and-pepper hair, dyed fashion color, or hair covering the eyes, mouth, lips, or jaw. No Western blazer, terracotta blazer, ivory blouse, business suit, shirt-and-jacket styling, casual clothing, bridal saree, wedding styling, costume, crown, veil, excessively ceremonial drape, gaudy embroidery, or cheap fabric. No missing jewelry, jewelry-free styling, oversized necklace, heavy bridal set, gaudy jewelry, duplicate earrings, asymmetric accidental jewelry, melting metal, malformed gemstones, jewelry covering the face, or jewelry tangled into hair. No exaggerated glamour makeup, bleached skin, unnaturally white skin, plastic skin, waxy face, doll face, uncanny eyes, crossed eyes, asymmetrical pupils, distorted face, malformed ears, duplicate features, extra teeth, visible teeth, open mouth, distorted lips, obscured jaw, cropped head, cropped necklace, cropped saree border, extra people, hands, malformed hands, props, microphone, headset, text, caption, logo, watermark, border, UI, signage, clutter, explicit sexuality, fetish styling, vulgar pose, coercive expression, caricature, illustration, painting, CGI appearance, low resolution, blur, compression artifacts, over-sharpening, or inconsistent lighting.

Generate one distinct candidate.
```

The exact Raj generation prompt, including its negative prompt, is frozen at
SHA-256 `79d35ec0d6ce11cdb481f91dc7358a0408b298012ab86f0b50c08c2309f4b9b9`:

```text
Use case: photorealistic-natural
Asset type: NarraTwin AI controlled-local synthetic presenter identity portrait and future speaking-animation anchor

Primary request: Create a completely original fictional adult Indian man presenter named Raj, visibly and unambiguously 24–28 years old. He must not be based on, copied from, or intended to resemble any actor, celebrity, influencer, public figure, known individual, existing presenter, or uploaded image. Raj is a tall, slim, fit, exceptionally handsome, smart, polished, and charismatic young man with leading-man-caliber presence while remaining believable, culturally respectful, professional, warm, technically credible, and entirely original.

Scene/backdrop: Neutral, elegant premium studio background in a restrained cool charcoal-gray or softly graded neutral tone, with subtle depth and no objects, signage, patterns, or clutter.

Subject and presence: A youthful adult Indian man with a natural fair or light-warm Indian complexion, realistic skin texture, refined Indian facial features, and tall, lean, slim, athletic proportions conveyed through an upright elongated posture, long clean neckline, lean shoulders, and tailored fit. He appears highly intelligent, technically credible, exceptionally handsome, smart, confident, calm, composed, persuasive, socially intelligent, well-cultured, refined, approachable, warm, and charismatic. He should look as though he knows exactly what he is explaining. His charisma must come from appearance, eye contact, warmth, clarity, confidence, and credibility—not aggression, arrogance, dominance, manipulation, or romantic behavior.

Face and hair: Youthful, handsome, harmonious facial structure; direct warm intelligent eye contact; natural eyebrows; friendly composed expression; relaxed closed mouth with fully visible lips and unobstructed jawline suitable for later lip synchronization. Use naturally black or very dark, dense, healthy, neatly groomed hair with a modern youthful style and no gray strands. He may be clean-shaven or have only restrained, carefully groomed light stubble that leaves the lips and jaw-animation regions visually clear.

Attire: A tailored premium Indian formal bandhgala, gala-bandh, refined Jodhpuri, or sophisticated Nehru-style jacket in deep navy, charcoal, black, or dark maroon. Use a youthful contemporary fit, refined collar, elegant minimal buttons, realistic premium textile texture, and culturally grounded styling. Show enough upper torso to make the Indian formal construction unmistakable. The outfit must be formal and polished without looking like wedding attire, a ceremonial costume, or an older executive uniform. Do not use the Western business-suit fallback.

Accessories: Keep accessories minimal and refined. A discreet premium watch or subtle culturally appropriate detail may be present only if naturally visible and non-distracting. No prominent jewelry is required.

Style/medium: High-end cinematic photorealistic studio portrait photography with professional color grading and realistic skin, hair, stubble, fabric, collar, and button textures. Original fictional identity; premium technology-presenter polish without glamour-retouched plasticity or rugged aging.

Composition/framing: Exact 3:2 landscape composition intended for a 1536×1024 derivative. Centered, symmetrical, front-facing head, shoulders, and upper-torso portrait at eye level. Full head, long neck, lean shoulders, formal Indian jacket collar, buttons, and sufficient upper torso must be visible. Use posture and proportions that clearly suggest a tall, slim, fit man while remaining natural. Direct natural camera engagement. Keep the face large enough for later animation while leaving clean margin around the hair and shoulders. No hands are required in frame.

Lighting/mood: Soft flattering frontal key light with gentle fill and controlled separation light. Preserve natural facial dimensionality while keeping the eyes, mouth, jaw, hairline, collar, and jacket details clearly readable. Cinematic, confident, intelligent, warm, composed, magnetic, polished, handsome, smart, charismatic, and approachable mood.

Constraints: One anatomically coherent fictional adult Indian man only; apparent age 24–28; tall, slim, fit, exceptionally handsome, smart, and charismatic identity; natural complexion without bleaching or artificial whitening; naturally black or very dark non-gray hair; youthful grooming; approved formal Indian attire; unobstructed eyes, lips, mouth, jawline, and animation regions; realistic facial symmetry and anatomy; no facial or image reference; no cloning; no biometric or customer data; no copied third-party media; no text, letters, numbers, logo, trademark, symbol, watermark, signature, border, UI, microphone, headset, handheld object, or background prop.

Negative prompt: Do not depict a child, teenager, person under 18, man over 28, middle-aged man, older man, senior executive, age-ambiguous adult, short or stocky build, bulky bodybuilder build, slouched compressed posture, non-Indian identity, celebrity lookalike, recognizable actor, influencer, public figure, or real-person resemblance. No gray hair, salt-and-pepper hair, silver temples, receding older-looking hairline, thinning hair, weathered face, tired eyes, deep aging lines, heavy rugged beard, large moustache, or unkempt facial hair. No green jacket, forest-green jacket, casual band-collar leisure jacket, bomber jacket, field jacket, utility jacket, casual Nehru jacket over a T-shirt, gray crew-neck shirt, T-shirt, crew neck, streetwear, hoodie, casual shirt, open collar, Western business suit, wedding sherwani, wedding attire, ceremonial costume, ornate royal styling, or gaudy buttons. No arrogant smirk, aggressive stare, dominance pose, predatory expression, caricature masculinity, bleached skin, unnaturally white skin, plastic skin, waxy face, doll-like treatment, uncanny eyes, crossed eyes, asymmetrical pupils, distorted face, malformed ears, duplicate features, extra teeth, visible teeth, open mouth, distorted lips, obscured jaw, cropped head, cropped jacket collar, extra people, hands, malformed hands, props, microphone, headset, text, caption, logo, watermark, border, UI, signage, clutter, illustration, painting, CGI appearance, low resolution, blur, compression artifacts, over-sharpening, or inconsistent lighting.

Generate one distinct candidate.
```

Myra A is the 2,204,077-byte 1536×1024 RGB PNG created at
`2026-08-07T20:33:39+05:30`, SHA-256
`a4186431ca0a037620c90f5835e6fb6964d29934b4e2dc517c2929a87396c27d`, at
`/private/tmp/narratwin-issue383-candidates-lhIQbq/myra-a.png`. Raj C is the
2,012,461-byte 1536×1024 RGB PNG created at `2026-08-07T20:37:57+05:30`,
SHA-256 `d829196db1d84173fa077ff099450dde5dd186b39efdd5a3b9a1bac2ab6528a4`, at
`/private/tmp/narratwin-issue383-candidates-lhIQbq/raj-c.png`.

The rejected source PNG and derivative evidence remains audit-preserved: female
source `953ce827...a9f08`, derivative `bdd62ae7...a5e27`, frozen prompt
`cbdfd1be...9b31`; male source `8feb72c3...c6a2`, derivative
`f6419cc5...b65`, frozen prompt `660a927d...d78`. Their contrary directions
were late-30s/early-40s bob/blazer and mid-to-late-40s salt-and-pepper casual
jacket. They are future-only Aashna/Character 1 and Veer/Character 2 concepts,
not registered presenters; activation requires a separate governed issue.

Both selected sources were mechanically converted on 2026-08-07 with Sharp
`0.35.3` under Apache-2.0 using auto-orientation, exact 1536×1024 fill resize,
alpha removal, and WebP quality 88, effort 6, and smart chroma subsampling.
FFprobe identified one WebP/yuv420p stream per derivative and FFmpeg decoded one
complete frame. The committed derivatives are path- and checksum-bound.

Owner visual selection confirms the still identities only. Engineering review
found distinct coherent fictional adults, unobstructed mouths, required attire
and Myra jewelry, suitable framing, and no obvious text, logo, watermark, or
artifact. This is not legal advice or proof of voice, animation, video, public
use, release, deployment, or production readiness. A latest-head non-author
reviewer must inspect the images, persona contract, and provenance before merge;
public distribution remains blocked on separate legal and publication review.

## Rules

- Do not add a dependency, tool, skill source, GitHub Action, model, dataset, avatar tool, media asset, or provider without updating this file.
- Do not enable non-commercial or research-only tools in external, public, or commercial workflows.
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

## Google Cloud Text-to-Speech — disabled adapter record

Issue #368 selects Google Cloud Text-to-Speech `gemini-2.5-pro-tts` as an
optional hosted adapter using `en-IN` and the Europe endpoint. This repository
implementation contains Python standard-library validation, the optional
official Google Cloud Text-to-Speech SDK, and injected fake protocols. It
contains no Google binary/model/voice asset, makes no provider call during tests
or ordinary disabled-default execution, and grants no redistribution,
commercial-use, indemnification or output-right conclusion.

Applicable first-party product documentation, pricing, service terms,
acceptable-use/prohibited-use policies, data-location terms and deprecation
policy are recorded with exact URLs and unresolved blockers in the Issue #368
governance review. Private screening references and generated audio are not
third-party assets committed to Git.
The optional runtime adds `google-auth==2.56.3` from official PyPI under
Apache-2.0. Its locked closure is `cryptography==50.0.0` (Apache-2.0 OR
BSD-3-Clause), `pyasn1-modules==0.4.2` (BSD-2-Clause), `pyasn1==0.6.4`
(BSD-2-Clause), `cffi==2.0.0` (MIT), and `pycparser==3.0` (BSD-3-Clause).
The corresponding source/wheel hashes are recorded in `uv.lock`; the canonical
google-auth wheel hash is
`8ec438808f813ad034535000261eed1067475d229d05bbf4216e78c3f2362e53`.
Issue #498 adds `google-cloud-texttospeech==2.37.0` under Apache-2.0 in the
optional runtime `providers` extra and the exact development/test dependency group
used by default hosted checks. Its newly materialized locked delta is
`google-api-core==2.34.0` (Apache-2.0), `grpcio==1.83.1` (Apache-2.0),
`grpcio-status==1.83.1` (Apache-2.0), and `proto-plus==1.28.4` (Apache-2.0);
their exact source and wheel hashes are recorded in `uv.lock`. Existing
`googleapis-common-protos`, `protobuf`, `requests`, and authentication closure
records are reused without version drift. No gcloud binary, API key, service
account JSON, credential, model, voice asset, or generated media is added. The
runtime remains disabled by default and hosted activation remains separately
governed. Sources: [Google Cloud TTS SDK PyPI](https://pypi.org/project/google-cloud-texttospeech/2.37.0/), [Google API Core PyPI](https://pypi.org/project/google-api-core/2.34.0/), [gRPC Python PyPI](https://pypi.org/project/grpcio/1.83.1/), [gRPC status PyPI](https://pypi.org/project/grpcio-status/1.83.1/), [proto-plus PyPI](https://pypi.org/project/proto-plus/1.28.4/), [google-auth PyPI](https://pypi.org/project/google-auth/2.56.3/), [cryptography PyPI](https://pypi.org/project/cryptography/50.0.0/), [pyasn1 PyPI](https://pypi.org/project/pyasn1/0.6.4/), [pyasn1-modules PyPI](https://pypi.org/project/pyasn1-modules/0.4.2/), [cffi PyPI](https://pypi.org/project/cffi/2.0.0/), [pycparser PyPI](https://pypi.org/project/pycparser/3.0/).

## Authority-evidence public verification

Issue #434 also declares the already locked `cryptography==50.0.0` package as
a direct development dependency for offline Ed25519 public-key verification.
License: Apache-2.0 OR BSD-3-Clause. No private key, signer, key generator,
provider SDK, model, dataset, media asset, or generated sample is added. Source:
[cryptography 50.0.0 documentation](https://cryptography.io/en/50.0.0/hazmat/primitives/asymmetric/ed25519/)
and [PyPI metadata](https://pypi.org/project/cryptography/50.0.0/).
## Minimal composed frontend runtime

Issue #413 composes the final image from exact Chainguard `glibc-dynamic`,
Docker Official Node 26.7.0 Bookworm-slim, and Chainguard `gcc-glibc` digests.
Only the MIT-licensed Node binary and GPL-3.0-or-later WITH
GCC-exception-3.1 `libatomic` component are copied into the minimal glibc image.
The final eight Wolfi components retain exact APK/SPDX identities and declared
MIT, MPL-2.0, LGPL-2.1-or-later, or GCC runtime-exception licensing. No compiler,
npm, shell, package manager, application package, model, provider, dataset,
media asset or generated sample is added.

Issue #376 reuses those same exact source digests for the non-shipping
dependency builder and additionally imports the npm JavaScript tree. Node's
embedded OpenSSL 3.5.7 remains truthfully reported, shared OpenSSL and QUIC are
build-time failures, and no OS OpenSSL package is imported. This removes the
affected builder capability without claiming an upstream fix, VEX, scanner
exception, deployment, release, public availability or production readiness.

## Issue #452 provider research records

The governance-only provider bake-off records official documentation, terms,
privacy and pricing URLs for Google Gemini TTS, ElevenLabs, HeyGen, D-ID,
Synthesia, Higgsfield and Tavus. No SDK, package, model, voice, media, dataset,
account, credential or provider output is added. No provider call, egress,
spend, redistribution right, legal clearance or final selection is authorized.
Sources and provider-specific constraints are enumerated in
`docs/governance/cut1-provider-bakeoff-contract-v1.json` and must be refreshed
before any later experiment.

Issue `#512` refreshes the batch-video research on 2026-09-03 in
`docs/governance/CUT1_T06_VIDEO_PROVIDER_LANDSCAPE_2026-09-03.md`. The record
adds official-source evaluation of HeyGen Avatar IV Photo, VEED Fabric through
Hedra, Colossyan NEO/Instant Avatar, LongCat-Video-Avatar 1.5 and fal.ai, Hedra
Avatar, D-ID, Sync, Higgsfield, Google Veo/Flow/Pomelli, Seedance, OmniHuman,
Runway Act-Two, Synthesia, and Tavus. These are researched providers, tools, or
models only: none is installed, selected, activated, called, or approved for
credentials, egress, spend, media generation, publication, or release. Exact
terms, pricing, license, training, retention, deletion, region, and API facts
remain refresh-required for the selected account before any demonstration.

## Issue #459 T03 controlled-local presenter derivatives

Issue #459 uses OpenAI's built-in `gpt-image-2.0` image-edit capability on
project-owned fictional synthetic identity anchors. Raj used one accepted
attempt. Myra used the authorized maximum of two attempts: owner review
superseded attempt 1 for hand lighting, gesture, coordinated jewelry, and
deep-maroon nail-polish continuity; attempt 2 passed independent visual,
provenance, and privacy review. No third attempt is authorized. The private PNG
sources are excluded from Git and retained only for owner cleanup after merge.
Exact source, candidate, output, conversion, review, rights, privacy, and
deletion records are in
`docs/governance/cut1-presenter-derivatives-v1.json`.

Accepted repository outputs are metadata-stripped WebPs for controlled local
Cut 1 use only. Independent review found no real-person reference, text, logo,
watermark, identity substitution, blocking anatomy defect, or
conversion-induced drift. Myra attempt 2 is private SHA-256
`00d71d0e6d25ff3772c2f6e05617853a240248e5e4ffa3ac623f7de5d7eed6bf`;
its generated PNG contains C2PA provenance identifying `gpt-image 2.0`, trained
algorithmic media, and OpenAI Media Service. The metadata-stripped WebP is
SHA-256
`46390ac627662bff38c9bb4ec904520a808e42030ff698741b5c32519f0be4c3`,
1086×1448, and 150246 bytes.
Pillow `12.3.0` under the MIT-CMU license is installed only in the development
dependency group to decode one complete frame from each frozen WebP during
tests and to reject a structurally plausible WebP with corrupted VP8 pixels.
It is not added to the application runtime or used to generate or modify media.
This record grants no publication, distribution, provider/runtime activation,
credential, egress, spend, human-study, release, production, or Cut 1 acceptance
authority. The Meera, Raj, and Myra originals remain immutable, and no new Meera
binary was generated or activated.

## Issue #482 security refresh

The resolved Python graph refreshes `aiohttp` to 3.14.3, `datasets` to 5.0.1,
`setuptools` to 84.0.0, and `torch` to 2.13.0 to remove newly reported
advisories. Torch resolution also updates `cuda-toolkit` to 13.0.3.0 and
narrows the unchanged `cuda-bindings` 13.3.1 CUDA-pathfinder marker to Python
below 3.15. Existing
licenses, upstream sources, direct dependency intent, optional/local behavior,
and notices remain applicable; no new provider, dataset, model, or media asset
is introduced by this lock-only refresh.

## Issue #502 musl scratch frontend runtime

Issue #502 replaces the final Wolfi/glibc composition with the immutable
Docker Official `node:26.7.0-alpine3.24` source. The scratch final image retains
Node.js under MIT and exact Alpine records for `alpine-keys` (MIT),
`alpine-release` (MIT), `ca-certificates-bundle` (MPL-2.0 and MIT), `libgcc`
and `libstdc++` (GPL-2.0-or-later and LGPL-2.1-or-later runtime terms), and
`musl` (MIT). Sharp and its locked musl libvips package remain existing
application dependencies; no package version or lockfile changes here.

Source: [Docker Official Node image](https://hub.docker.com/_/node) and
[Node Docker Alpine variant guidance](https://github.com/nodejs/docker-node#image-variants).
This notice does not authorize redistribution beyond applicable licenses,
deployment, public availability, release, or production use.
