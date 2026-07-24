# ADR 0035: Issue 280 Input API Error Contract Slice

Date: 2026-07-24

Status: Accepted for issue `#280` PR B scope only

## Context

Issue `#280` C3A-R3 PR A defined a future local/mock demo contract but did not
implement runtime behavior. PR B needs the first executable contract slice:
bounded arbitrary synthetic markdown input, public-safe request/response/error
taxonomy, prompt-injection and unsafe/private/secret-like input rejection, and
provider-disabled local/mock posture.

The slice must not implement the full local end-to-end multilingual demo, exact
UI evidence, hosted/public demo, provider setup, paid spend, cloned identity
runtime, real media, public distribution, arbitrary real-world translation
quality, provider quality, or production-readiness claims.

## Decision

Add a narrow versioned FastAPI endpoint:

```text
POST /api/v1/checkpoint3/issue280/input-contract
```

The endpoint accepts JSON request data for bounded synthetic markdown documents
and returns only public-safe metadata:

- contract version
- input limits
- request summary
- document filename/content-type/size/section/checksum metadata
- explicit local/mock provider-disabled posture
- bounded trace metadata with request ID

The endpoint rejects unsafe requests using the Issue 280 taxonomy and the
existing NarraTwin error envelope. It never returns raw submitted markdown,
provider payloads, model internals, filesystem paths, stack traces,
credentials, tokens, provider keys, or private values in API errors.

The endpoint is implemented in a small `backend/app/issue280.py` contract module
and wired through `backend/app/main.py`. Stage 4, Stage 6, and Stage 7 product
services are intentionally unchanged.

## Consequences

- PR B can prove executable evidence for the PR B-owned `R280-INPUT`,
  `R280-ERROR`, and `R280-TEST-STRATEGY-002` rows without claiming the full
  #280 demo is complete.
- Future #280 slices can consume or replace this contract boundary when they
  implement the full create/upload/ingest/generate/translate/render/export/UI
  flow.
- The final `make issue280-output-correctness` gate remains planned.
- Issues `#249` and `#280` remain open after PR B.

## Validation

- `uv run pytest tests/unit/test_issue280_contract.py -q`
- `uv run pytest tests/acceptance/test_issue280_input_contract.py -q`
- `uv run pytest tests/acceptance/test_issue280_api_contract.py -q`
- `uv run pytest tests/acceptance/test_issue280_error_taxonomy.py -q`
- `python3 scripts/quality/check_phase1_closure_docs.py`
- `make ci`
