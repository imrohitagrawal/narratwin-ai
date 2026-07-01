# Phase 1 Demo Script

Purpose: demonstrate the local mock-provider Phase 1 flow without production,
multi-worker, real video, cloned identity, or public synthetic-media claims.

## Flow

1. Start the local demo:

   ```bash
   cp .env.example .env
   docker compose up --build
   ```

2. Verify backend health and readiness:

   ```bash
   curl http://localhost:8000/api/v1/healthz
   curl http://localhost:8000/api/v1/readyz
   ```

3. Open the app locally at `http://localhost:3000`.
4. Create project using the NarraTwin AI demo name and a short description.
5. Upload project knowledge from `demo/stage8_seed_project.md`.
6. Approve and ingest the uploaded project knowledge.
7. Generate walkthrough script for the recruiter audience.
8. Show citations and source references attached to the generated script.
9. Show the eval result with unsupported claims equal to zero.
10. Show saved output in the UI.

## Required Talking Points

- This is a local mock-provider demo.
- The current state is single-process, process-local, and non-durable.
- The demo uses mock/local providers only and does not require provider keys.
- The demo does not produce real video, cloned face, cloned voice, or public
  synthetic-media output.
- Final Review remains No-Go for production until Phase 1 P0/P1 blockers close.
