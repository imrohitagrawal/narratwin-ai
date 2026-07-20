# Phase 1 Demo Checklist

Use this checklist for local mock-provider demo readiness.

This checklist applies only to the `Local mock demo` row in
`docs/LAUNCH_LEVELS.md`. An AWS account is not required. Hosted or external
access requires a separate launch-level decision and must not inherit this
checklist's conditional local-demo posture.

- [ ] `.env` exists from `cp .env.example .env`.
- [ ] `docker compose up --build` starts backend, frontend, Postgres, and Redis.
- [ ] `curl http://localhost:8000/api/v1/healthz` returns successfully.
- [ ] `curl http://localhost:8000/api/v1/readyz` returns successfully.
- [ ] App opens locally at `http://localhost:3000`.
- [ ] User can create project.
- [ ] User can upload project knowledge.
- [ ] Uploaded knowledge is approved and ingested.
- [ ] Chunks are created and retrievable.
- [ ] User can generate walkthrough script.
- [ ] Generated script includes citations.
- [ ] Eval result is visible.
- [ ] Unsupported claims are blocked or flagged.
- [ ] User can generate a multilingual run using mock/local translation,
      subtitles, and voice manifest providers.
- [ ] User can affirm synthetic avatar consent.
- [ ] User can generate the mock/local avatar demo export from the validated
      Stage 6 multilingual bundle.
- [ ] Translated script, subtitles, voice manifest, avatar demo HTML, render
      manifest, and video placeholder JSON are visible and downloadable only
      after MIME type, safe filename, size, checksum, JSON/provider marker, and
      active HTML validation pass.
- [ ] Render manifest and video placeholder show multilingual provenance for
      `sourceRunId`, `multilingualRunId`, target language, artifact checksums,
      context refs, citation indexes, evaluation evidence, provider posture, and
      consent disclosure version.
- [ ] Demo presenter states the single-process/local-only limit, optional JSON
      restart snapshots when configured, and no multi-worker or production
      durability.
- [ ] Demo presenter states mock/local providers only.
- [ ] Demo presenter states no provider keys, no real audio, no real video, no
      external providers, no cloned identity, no hosted launch, no public
      distribution, and no production readiness.
