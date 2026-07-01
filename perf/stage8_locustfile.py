"""Locust smoke profile for Stage 8 local API performance checks.

The stage quality gate runs this profile headlessly and fails if the health
endpoint exceeds the Stage 8 local p95 budget:

    uv run locust -f perf/stage8_locustfile.py --headless --host http://127.0.0.1:8000
"""

from __future__ import annotations

import os

from locust import HttpUser, between, events, task


MAX_HEALTH_P95_MS = float(os.environ.get("NARRATWIN_LOCUST_HEALTH_P95_MS", "200"))


class NarraTwinApiUser(HttpUser):
    wait_time = between(0.1, 0.3)

    @task
    def health(self) -> None:
        self.client.get("/api/v1/healthz", name="GET /api/v1/healthz")


@events.quitting.add_listener
def enforce_stage8_budgets(environment: object, **_kwargs: object) -> None:
    stats = getattr(environment, "stats")
    health_stats = stats.get("GET /api/v1/healthz", "GET")
    if health_stats.num_requests == 0:
        setattr(environment, "process_exit_code", 1)
        print("Locust Stage 8 smoke failed: no health requests were recorded.")
        return
    if health_stats.num_failures > 0:
        setattr(environment, "process_exit_code", 1)
        print(f"Locust Stage 8 smoke failed: {health_stats.num_failures} health failures.")
        return
    p95_ms = health_stats.get_response_time_percentile(0.95)
    if p95_ms > MAX_HEALTH_P95_MS:
        setattr(environment, "process_exit_code", 1)
        print(f"Locust Stage 8 smoke failed: health p95 {p95_ms:.2f} ms exceeds {MAX_HEALTH_P95_MS:.2f} ms.")
