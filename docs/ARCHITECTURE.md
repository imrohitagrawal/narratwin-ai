# Architecture

## Architecture goal

NarraTwin AI must be provider-agnostic, free-first, testable with mocks, and safe for public portfolio use.

Core product logic must depend on internal interfaces, not on Gemini, HeyGen, Tavus, D-ID, ElevenLabs, FFmpeg, ChromaDB, or any provider SDK directly.

## High-level flow

```text
Project Knowledge Pack
→ Upload Validation
→ Ingestion
→ Chunking
→ Vector Store
→ RAG Retrieval
→ Grounded Script Generation
→ Unsupported-Claim Evaluation
→ Translation/TTS/Avatar/Subtitle/Video Providers
→ Output Storage
→ UI
```

## MVP flow

```text
Create project
→ upload markdown/text knowledge
→ validate upload
→ ingest and chunk
→ store chunks
→ retrieve relevant context
→ generate grounded walkthrough script
→ evaluate unsupported claims
→ store run
→ display result in UI
```

Avatar video, TTS, subtitles, and premium providers are outside Slice 1.

## Component boundaries

### Frontend

Responsibilities:

- project creation screen
- project list screen
- knowledge upload screen
- walkthrough request form
- generated output display
- warning and evaluation result display

Must not:

- hold provider secrets
- perform direct provider calls
- bypass backend upload validation
- hide unsupported-claim warnings

### Backend API

Responsibilities:

- project CRUD
- upload validation
- ingestion orchestration
- run orchestration
- provider adapter calls
- evaluation and refusal decisions
- output persistence
- observability metadata

### Domain core

Responsibilities:

- project entity
- knowledge document entity
- chunk entity
- walkthrough request entity
- walkthrough run entity
- evaluation result entity
- provider interfaces
- business rules and refusals

Must not import provider SDKs directly.

### Providers/adapters

Adapters implement provider interfaces.

Examples:

- `GeminiLLMProvider`
- `MockLLMProvider`
- `ChromaVectorStore`
- `LocalStorageProvider`
- `MockAvatarProvider`
- `FFmpegVideoRenderer`

Adapters must have contract tests.

## Provider interfaces

- `LLMProvider`
- `EmbeddingProvider`
- `TranslationProvider`
- `TTSProvider`
- `STTProvider`
- `AvatarProvider`
- `SubtitleProvider`
- `VideoRenderer`
- `StorageProvider`
- `EvaluationProvider`
- `ObservabilityProvider`

## Default providers

- LLMProvider: Gemini or mock provider during local tests.
- EmbeddingProvider: Gemini or local fallback after review.
- VectorStore: ChromaDB first through an internal interface.
- StorageProvider: local filesystem first.
- AvatarProvider: mock first.
- VideoRenderer: FFmpeg after license review.
- ObservabilityProvider: structured logs first.

## Data model

### Project

- `project_id`
- `name`
- `description`
- `default_language`
- `default_audience`
- `created_at`
- `updated_at`

### KnowledgeDocument

- `document_id`
- `project_id`
- `filename`
- `content_type`
- `size_bytes`
- `checksum`
- `storage_path`
- `created_at`

### KnowledgeChunk

- `chunk_id`
- `project_id`
- `document_id`
- `chunk_index`
- `text`
- `metadata`
- `embedding_ref`

### WalkthroughRun

- `run_id`
- `project_id`
- `audience`
- `language`
- `depth`
- `style`
- `provider`
- `status`
- `script_text`
- `evaluation_status`
- `unsupported_claims`
- `context_refs`
- `latency_ms`
- `estimated_cost`
- `created_at`

## Trust boundaries

### Untrusted

- uploaded documents
- filenames
- user prompts
- generated provider outputs
- external provider callbacks
- browser input

### Trusted after validation

- server-side configuration
- approved project metadata
- sanitized document metadata
- stored chunk records
- internal provider interfaces

## Upload security flow

1. Receive upload through backend only.
2. Enforce allowed types: markdown/text in MVP.
3. Enforce file size limit.
4. Sanitize filename.
5. Store with generated safe path.
6. Treat file content as untrusted context.
7. Strip or ignore instructions that attempt to override system/developer rules.
8. Chunk and store with source metadata.

## Generation safety flow

1. Retrieve context from approved chunks.
2. Build prompt with explicit grounding rules.
3. Require the model to use only retrieved context.
4. Evaluate generated script for unsupported claims.
5. Refuse, flag, or regenerate if unsupported claims are found.
6. Store evaluation metadata with output.
7. Show warnings in UI.

## Observability flow

Each run should emit:

- `run_id`
- `project_id`
- `audience`
- `language`
- `provider`
- `latency_ms`
- `cache_hit`
- `estimated_cost`
- `evaluation_status`
- `error_code`

## Architecture rules

- Core business logic must depend on interfaces, not provider SDKs.
- All provider adapters must be optional and replaceable.
- Paid providers must be disabled by default.
- Mock providers must support local tests.
- New provider adapters require contract tests.
- All new slices require docs, tests, security notes, and known limitations.
