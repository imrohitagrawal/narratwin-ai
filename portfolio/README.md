# NarraTwin AI Portfolio Demo

NarraTwin AI is a local-first AI avatar walkthrough platform. The current portfolio-safe demo supports:

- project creation
- markdown knowledge upload
- grounded walkthrough generation with citations
- multilingual script and subtitle artifacts
- mock/local avatar demo export metadata
- release-readiness checks for performance, dependency audit, Docker image scan, and Lighthouse

Run the release gate:

```bash
make quality
```

Use `demo/stage8_seed_project.md` as safe demo seed data. The portfolio demo does not require paid providers, real provider keys, cloned identities, or real video export.
