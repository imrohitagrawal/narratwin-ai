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
8. Multilingual translated script, subtitles, and voice manifest.
9. Synthetic avatar consent and mock/local avatar metadata.
10. Avatar demo preview.
11. Export artifact area showing translated script, subtitles, voice manifest,
    avatar demo HTML, render manifest, and video placeholder JSON.
12. Render manifest or video placeholder metadata showing validated
    `sourceRunId`, `multilingualRunId`, target language, artifact checksums,
    context refs, citation indexes, evaluation evidence, provider posture, and
    consent disclosure version.

## Caption Rules

- State "local mock-provider demo" in the screenshot caption.
- State "single-process, local-only, optional JSON restart snapshots, no
  multi-worker or production durability" where saved output is shown.
- Do not caption screenshots as production-ready.
- Do not imply provider keys, real audio, real video export, cloned identity,
  external provider use, hosted/public launch, public distribution, or
  production readiness.
