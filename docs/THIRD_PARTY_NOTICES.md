# Third-Party Notices

Maintain this file for every third-party package, tool, skill source, GitHub Action, model, API, dataset, avatar provider, media asset, and generated sample.

This file is not legal advice. Treat it as the engineering license-review register.

| Component | Purpose | License/Terms | Commercial/Public Use Allowed? | Decision for MVP | Notes |
|---|---|---|---|---|---|
| Gemini API | LLM, translation, evaluation, optional embeddings/TTS | Google AI terms | Review before use | Optional | API key via `.env`; tests must not require a real key. |
| ChromaDB | Local vector store candidate | Apache License 2.0 per upstream license file; `chromadb==1.5.9` currently has `PYSEC-2026-311` / `CVE-2026-45829` with no fixed version listed by `pip-audit` | Blocked until non-vulnerable version or explicit security exception | Deferred from Stage 4 active dependencies | Removed from active dependencies because dependency security gates block known vulnerable packages. Future use must stay behind an internal vector-store interface. |
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
| GitHub Action: Setup Node | CI Node.js runtime setup | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Stage 3 CI dependency | Source: `actions/setup-node`. Not a product runtime dependency. |
| GitHub Action: Upload Artifact | CI artifact upload | GitHub Action terms; immutable pin review required in Stage 3 | Yes after pin review | Existing CI dependency | Source: `actions/upload-artifact`. Not a product runtime dependency. |
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
| pypdf | PDF text extraction for project knowledge ingestion | Pending dependency license review before release | Likely yes after dependency review | Stage 4 dependency prep | Added as `pypdf==6.14.2`; PDF upload behavior still requires Stage 4 validation and safety controls. |
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
| Next.js | Frontend framework | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend foundation | Chosen by Stage 2 architecture; minimal scaffold only, no product feature workflow. |
| React and React DOM | Frontend UI runtime | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend foundation | Required by Next.js scaffold. |
| PostCSS | CSS processing dependency used through Next.js and Vite | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend dependency override | `frontend/package.json` pins an override to `^8.5.16` to clear GHSA-qx2v-qp2m-jg93 while preserving the Next.js scaffold. |
| sharp, unrs-resolver, fsevents install scripts | npm install-script approvals for frontend dependency tree | Pending dependency script review before release | Accepted for Stage 3 after local install review | Stage 3 frontend dependency install hygiene | `frontend/package.json` records pinned `allowScripts` entries for the currently installed versions so npm 11 installs are explicit and warning-free. |
| TypeScript | Frontend type checking | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Used by frontend `typecheck` script. |
| ESLint and eslint-config-next | Frontend lint tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Used by frontend `lint` script. |
| Vitest | Frontend unit test runner | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Installed for future component/unit tests. |
| Playwright | Browser automation and E2E test tooling | Pending dependency license review before release | Likely yes after dependency review | Stage 3 frontend quality tooling | Used for the Stage 3 health-check-only frontend smoke test. |
| httpx | FastAPI TestClient transport dependency for API tests | Pending dependency license review before release | Likely yes after dependency review | Stage 3 API test tooling | Used only in tests. |
| httpx2 | Starlette/FastAPI TestClient transport dependency for API tests | Pending dependency license review before release | Likely yes after dependency review | Stage 3 API test tooling | Used only in tests to avoid deprecated TestClient transport warnings. |
| Semgrep | Static analysis/security rule runner | Pending dependency license review before release | Likely yes after dependency review | Stage 3 security tooling | Runs repo-local `semgrep.yml`; no remote rules are required for the local gate. |
| Docker Compose | Local service orchestration | Docker terms and component licenses require review before release | Yes after dependency review | Stage 3 repo foundation | Used for local health-check-only backend and frontend containers. |
| PostgreSQL container image | Local relational metadata service foundation | PostgreSQL License; pinned to `postgres:17-alpine@sha256:dc17045ccfd343b49600570ea734b9c4991cf1c3f3302e67df51e3b402dd55c4` for Stage 3 | Yes for local/dev after release review | Stage 3 local Compose foundation | Local service only; no schema, migration, or product persistence code is implemented in Stage 3. |
| Redis container image | Local cache/queue service foundation | BSD-3-Clause for Redis OSS; pinned to `redis:8-alpine@sha256:9d317178eceac8454a2284a9e6df2466b93c745529947f0cd42a0fa9609d7005` for Stage 3 | Yes for local/dev after release review | Stage 3 local Compose foundation | Local service only; no cache, queue, or product runtime code is implemented in Stage 3. |

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
