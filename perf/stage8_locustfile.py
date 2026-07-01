"""Locust smoke profile for Stage 8 local API performance checks.

The stage quality gate uses pytest for deterministic latency budgets. This
profile is kept as the repeatable load-smoke entrypoint for local/manual runs:

    uv run locust -f perf/stage8_locustfile.py --host http://127.0.0.1:8000
"""

from __future__ import annotations

from locust import HttpUser, between, task


class NarraTwinApiUser(HttpUser):
    wait_time = between(0.1, 0.3)

    @task
    def health(self) -> None:
        self.client.get("/api/v1/healthz", name="GET /api/v1/healthz")
