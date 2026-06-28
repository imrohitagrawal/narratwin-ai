# Security and Privacy

## Security posture

NarraTwin AI processes user-uploaded project knowledge and produces generated walkthrough content. The platform must assume uploaded content, filenames, prompts, provider outputs, and browser input are untrusted.

## Primary risks

- secret leakage
- unsafe file uploads
- path traversal through filenames
- prompt injection in uploaded documents
- hallucinated project claims
- confidential project data exposure
- cloned voice or face without consent
- unsafe third-party media/model licensing
- costly repeated generation
- public demo misuse
- provider lock-in and accidental paid API dependency

## Required controls

### Secrets

- Use `.env` for local secrets.
- Keep `.env.example` placeholder-only.
- Never commit provider keys, GitHub tokens, cookies, private URLs, or credentials.
- Keep secret scanning enabled in GitHub Actions.

### Uploads

- Accept only markdown and plain text in MVP.
- Enforce file size limits.
- Sanitize filenames.
- Store files under generated safe paths.
- Do not trust MIME type alone.
- Reject binary, executable, archive, and unknown formats in MVP.
- Record checksum and source metadata.

### Prompt injection

- Treat uploaded documents as data, not instructions.
- Do not allow uploaded text to override system, developer, or safety rules.
- Add tests for malicious instructions inside uploaded documents.
- Keep grounding rules close to generation and evaluation code.

### Hallucination and unsupported claims

- Generated output must be grounded in approved project context.
- Unsupported claims must be flagged, refused, or regenerated.
- Empty context must produce a refusal.
- UI must show warnings when evaluation fails.

### Avatar, face, and voice safety

- Mock avatar provider is default.
- Voice cloning is out of MVP scope.
- Face cloning is out of MVP scope.
- Any cloned face or voice feature requires explicit documented consent.
- AI-generated avatar or voice disclosure is mandatory.

### Provider safety

- Paid providers are optional adapters.
- Provider SDKs must not be imported into core domain logic.
- Provider keys must never be required for tests.
- Provider responses must be treated as untrusted until evaluated.

### License safety

- Every third-party package, model, API, dataset, avatar provider, media asset, and generated sample must be recorded in `docs/THIRD_PARTY_NOTICES.md`.
- Non-commercial or research-only tools must not be enabled in public or commercial workflows.
- Wav2Lip must not be enabled by default.

## Privacy rules

- Do not upload private user documents to external providers without explicit configuration.
- Avoid storing raw secrets or personal tokens in logs.
- Store only necessary project metadata.
- Keep local-first storage for MVP.
- Document any future cloud storage or provider data retention behavior.

## Minimum tests before Slice 1 merge

- upload type rejection
- filename sanitization
- file size rejection
- prompt-injection-in-document test
- empty-context refusal test
- unsupported-claim detection test
- no-paid-provider-key test
- no-secret-commit scan in CI

## Release blocker list

A slice cannot merge if:

- tests require real premium provider keys
- unsupported claims can pass silently
- uploaded documents can override system instructions
- `.env` or provider keys are committed
- third-party licensing is unresolved for used components
- AI avatar or voice outputs lack disclosure where relevant
