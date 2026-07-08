# NarraTwin AI Portfolio Demo

NarraTwin AI is a local-first AI avatar walkthrough platform. The current portfolio-safe demo supports:

- project creation
- markdown knowledge upload
- grounded walkthrough generation with citations
- multilingual script and subtitle artifacts
- mock/local avatar demo export metadata
- release-readiness checks for performance, dependency audit, Docker image scan, and Lighthouse

Important limits for the current demo:

- single-process runtime state
- process-local project, run, idempotency, and artifact metadata by default
- optional single-node JSON restart snapshots when explicitly configured
- no multi-worker or production-durable storage for demo outputs
- mock/local providers only
- no production or multi-worker readiness claim
- no real video export, cloned identity, external avatar provider, or public synthetic-media distribution claim

Start the local demo:

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/api/v1/healthz
curl http://localhost:8000/api/v1/readyz
```

Open `http://localhost:3000`, create project, upload project knowledge, generate
a walkthrough script, show citations, show eval result, and show saved output.
Use `demo/stage8_seed_project.md` as safe demo seed data.

Run the governance and full local gates before treating the demo as review-ready:

```bash
make quality
make ci
```

The portfolio demo does not require paid providers, real provider keys, cloned
identities, or real video export.
