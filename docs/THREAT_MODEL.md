# Threat Model

## Version

- Version: 1.0
- Stage: Stage 2 architecture, security, AI safety
- Canonical issue: `#2`
- Last updated: 2026-06-29
- Scope: pre-implementation architecture and first vertical slice planning

## Scope

This threat model covers the planned NarraTwin AI system through Stage 4 Slice 1 and
the future provider/media boundaries that Stage 2 must account for.

In scope:

- frontend upload and walkthrough request flow
- backend API boundary
- ingestion worker
- RAG service and vector store
- script generation service
- evaluator service
- storage adapters
- provider abstraction
- avatar rendering adapter boundary
- observability and audit logs
- CI quality gates

Out of scope for implementation in Stage 2:

- product runtime code
- deployed infrastructure
- real avatar/video rendering
- real voice cloning or face cloning
- premium provider integration
- multi-user authentication implementation

## Assets

| Asset | Sensitivity | Notes |
|---|---|---|
| Provider keys | Critical | Must never reach frontend, prompts, logs, or git |
| Uploaded project knowledge | High | May contain confidential project data |
| Generated scripts | Medium to high | May contain unsupported or sensitive claims |
| Source chunks and context refs | High | Grounding basis for outputs |
| Evaluation results | Medium | Reviewer evidence and quality gate input |
| Project metadata | Medium | Future tenant/project isolation boundary |
| Audit logs | Medium | Must not contain secrets |
| Future avatar/voice/video artifacts | High | Consent, disclosure, and licensing risk |
| Future consent records | Critical | Required for identity media |

## Trust Boundaries

```text
Browser/user input
-> Backend API validation
-> Storage and metadata boundary
-> Ingestion worker
-> RAG/vector-store boundary
-> Prompt assembly boundary
-> External provider boundary
-> Evaluator boundary
-> Output display boundary
-> Observability/audit boundary
```

Untrusted:

- uploaded files
- filenames
- request bodies
- user prompts
- project docs used as RAG context
- transcripts
- provider responses
- model outputs
- vector-store records until metadata is verified
- future webhooks/callbacks

## Authorization Boundary

Stage 4 local mode still has an authorization boundary. The actor is the synthetic
local user `user_local` inside synthetic local tenant `tenant_local`. Every
project-scoped operation validates this principal before lookup, retrieval,
generation, evaluation, export, or deletion.

The authorization predicate is `(tenant_id, owner_id, project_id)`. Child resource
queries either include all three fields directly or run only after a server-side
project authorization guard has verified ownership on `Project`.

## STRIDE Analysis

| Boundary | Spoofing | Tampering | Repudiation | Information disclosure | Denial of service | Elevation of privilege |
|---|---|---|---|---|---|---|
| Frontend to backend | forged user/project IDs | modified request parameters | denied upload/generation | leaked project metadata | repeated requests | access another project |
| Upload intake | fake content type | path traversal filename | denied malicious upload | uploaded secrets exposed | huge files/corpus | executable content used |
| Ingestion | fake metadata | poisoned chunks | denied ingestion action | raw content in logs | chunk explosion | bypass validation |
| RAG retrieval | fake project context | altered vector metadata | denied retrieval | cross-project chunks | expensive retrieval | retrieve unauthorized project |
| LLM provider | fake provider config | prompt injection | denied provider call | secrets in prompt | token/cost exhaustion | model controls tools |
| Deterministic Stage 4 evaluator | fake pass result | altered eval result | denied safety failure | raw evaluator payload leakage | eval loop abuse | bypass failed eval |
| Storage | fake artifact IDs | overwritten outputs | denied changes | unauthorized download | storage exhaustion | path traversal |
| Observability | fake event actor | altered logs | missing audit trail | secret logging | log volume abuse | hide malicious actions |
| Future avatar provider | fake consent | altered media output | denied render | identity/media leakage | render cost abuse | clone identity without consent |

The Stage 4 evaluator boundary is deterministic and rule-backed. Model-as-judge evaluation is future scope and requires an ADR before it can affect acceptance or security decisions.

## Abuse Cases

### A1: Prompt Injection In Uploaded Markdown

Attack:

- uploaded doc tells the model to ignore system rules, reveal secrets, or make
  unsupported claims

Controls:

- treat uploaded docs as untrusted evidence
- delimiter prompt context
- enforce provider/tool permissions in code
- add malicious fixture tests
- evaluate unsupported claims

### A2: Cross-project Retrieval

Attack:

- user causes retrieval to include chunks from another project

Controls:

- every retrieval query includes `tenant_id` and `project_id` after the
  `(tenant_id, owner_id, project_id)` authorization guard
- vector-store metadata is validated
- tests assert cross-project isolation
- provider prompt includes only authorized context

### A2b: Approved Knowledge Poisoning

Attack:

- attacker uploads markdown that passes file validation and is silently treated as
  approved source-of-truth RAG content

Controls:

- uploaded documents start as `UPLOADED`, `STORED`, or `QUARANTINED`
- `document_status = STORED`, `approval_status = APPROVED`, and
  `ingestion_status = INGESTED` are required before retrieval or non-local provider
  egress
- prompt-injection text remains untrusted evidence, not instructions
- approval, quarantine, rejection, and deletion emit audit events

### A3: Secret Exfiltration Through Provider Prompt

Attack:

- uploaded file or environment accidentally includes provider key or token and is
  sent to an external provider

Controls:

- repository secret scanning
- mandatory `SecretScreeningResult` before any non-local provider egress, with
  scanner version, categories, blocking decision, redaction decision, optional
  reviewer override, and audit event
- secret screening is mandatory before any non-local provider egress
- no secrets in prompt assembly
- provider egress disabled by default locally
- no raw prompts in logs

### A4: Unsupported Portfolio Claims

Attack:

- generated script invents metrics, architecture, users, or business impact

Controls:

- context references required
- unsupported-claim evaluator
- empty-context refusal
- UI warnings
- failed eval blocks silent acceptance

### A5: Path Traversal Upload

Attack:

- filename such as `../../.env` attempts to overwrite local files

Controls:

- generated storage paths
- filename sanitization
- extension/content allowlists
- no direct use of original filename as filesystem path

### A6: Cost Exhaustion

Attack:

- repeated generation or huge uploads drive provider cost

Controls:

- upload and corpus limits
- token/output caps
- route and provider-mode rate limits
- caching
- estimated cost metadata

### A7: Identity Media Misuse

Attack:

- avatar or voice output implies consent from a real person

Controls:

- mock avatar default
- no face or voice cloning in MVP
- explicit documented consent before cloned identity features
- AI-generated media disclosure
- third-party/license review

## Control Matrix

| Risk | Primary control | Evidence required |
|---|---|---|
| Secret leakage | secret scanning and no secret logging | CI scan and log redaction review |
| Prompt injection | context-as-data pattern | malicious upload fixture |
| Unsafe uploads | validation and generated paths | upload security tests |
| Cross-project data leak | project-scoped queries | isolation tests |
| Provider key exposure | backend-only adapters | config and adapter tests |
| Unsupported claims | evaluator and context refs | eval fixture report |
| DoS/cost abuse | rate limits and caps | rate-limit and token-cap tests |
| Supply-chain risk | dependency scanning | scan artifacts and notices |
| Web baseline issues | OWASP ZAP baseline when web exists | scan artifact |
| Identity media misuse | consent and disclosure | consent/disclosure tests |

## Open Threats Before Stage 4

- exact local vector-store dependency must pass review
- OWASP baseline scan cannot run until a web surface exists

## Review Cadence

Update this threat model when:

- a new external provider is added
- a new upload type is allowed
- authentication or multi-user access is implemented
- storage or vector-store architecture changes
- avatar, voice, subtitle, or video output is introduced
- security scans produce critical/high findings
