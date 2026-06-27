# Architecture

## High-level flow

Project Knowledge Pack
→ Ingestion
→ Chunking
→ Vector Store
→ RAG Retrieval
→ Grounded Script Generation
→ Evaluation
→ Translation/TTS/Avatar providers
→ Output Storage
→ UI

## Provider interfaces

- LLMProvider
- EmbeddingProvider
- TranslationProvider
- TTSProvider
- STTProvider
- AvatarProvider
- SubtitleProvider
- VideoRenderer
- StorageProvider
- EvaluationProvider
- ObservabilityProvider

## Default providers

- LLMProvider: Gemini
- EmbeddingProvider: Gemini or local fallback
- VectorStore: ChromaDB first
- StorageProvider: local filesystem first
- AvatarProvider: mock first
- VideoRenderer: FFmpeg
- ObservabilityProvider: structured logs first

## Architecture rule

Core business logic must depend on interfaces, not provider SDKs.
