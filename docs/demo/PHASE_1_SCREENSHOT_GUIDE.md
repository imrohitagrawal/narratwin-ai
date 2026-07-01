# Phase 1 Screenshot Guide

Capture screenshots only from the local mock-provider demo.

Start the app with:

```bash
cp .env.example .env
docker compose up --build
```

Then verify `http://localhost:8000/api/v1/healthz`,
`http://localhost:8000/api/v1/readyz`, and open `http://localhost:3000`.

## Required Screens

1. App open with project form visible.
2. Created project state.
3. Upload project knowledge step.
4. Ingested knowledge/chunk-ready state.
5. Generated walkthrough script.
6. Citations/source references.
7. Eval result showing unsupported claims are zero or blocked/flagged.
8. Saved output and artifact/download area.

## Caption Rules

- State "local mock-provider demo" in the screenshot caption.
- State "single-process, process-local, non-durable" where saved output is shown.
- Do not caption screenshots as production-ready.
- Do not imply real video export, cloned identity, external avatar provider use,
  or public synthetic-media distribution.
