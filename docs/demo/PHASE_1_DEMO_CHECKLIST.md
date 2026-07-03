# Phase 1 Demo Checklist

Use this checklist for local mock-provider demo readiness.

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
- [ ] Saved output is visible in the UI.
- [ ] Demo presenter states the single-process/local-only limit, optional JSON
      restart snapshots when configured, and no multi-worker or production
      durability.
- [ ] Demo presenter states mock/local providers only.
- [ ] Demo presenter makes no production, real-video, cloned-identity, or public
  synthetic-media distribution claim.
