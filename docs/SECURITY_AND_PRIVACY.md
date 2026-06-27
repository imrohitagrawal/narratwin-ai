# Security and Privacy

## Risks

- secret leakage
- unsafe file uploads
- prompt injection in uploaded documents
- hallucinated project claims
- cloned voice/face without consent
- unsafe third-party media/model licensing
- costly repeated generation
- public demo misuse

## Required controls

- `.env` for secrets
- `.env.example` with placeholder values only
- upload type allowlist
- filename sanitization
- file size limits
- prompt-injection tests
- RAG grounding tests
- AI-generated avatar/voice disclosure
- consent requirement for cloned voice/face
- third-party notices for all dependencies
