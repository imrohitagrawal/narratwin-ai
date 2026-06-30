"""Prometheus counters and histograms for Stage 5 run-level observability."""

from __future__ import annotations

from collections.abc import Mapping

from prometheus_client import Counter, Histogram

ALLOWED_STATUSES = {"COMPLETED", "FAILED", "REFUSED"}
ALLOWED_EVALUATION_STATUSES = {"", "PASSED", "FAILED"}
ALLOWED_REASON_CODES = {
    "",
    "LOW_RETRIEVAL_CONFIDENCE",
    "PROMPT_INJECTION_DETECTED",
    "UNSAFE_RETRIEVED_CONTEXT",
    "UNSUPPORTED_PROJECT_FACT",
}
ALLOWED_TOKEN_TYPES = {"inputTokens", "outputTokens", "totalTokens"}


_RUNS_TOTAL = Counter(
    "narratwin_walkthrough_runs_total",
    "Total walkthrough generation runs by status.",
    ["status", "evaluation_status", "reason_code"],
)
_LATENCY_MS = Histogram(
    "narratwin_walkthrough_latency_ms",
    "Walkthrough generation latency in milliseconds.",
    ["status", "evaluation_status"],
)
_TOKEN_USAGE_TOTAL = Counter(
    "narratwin_walkthrough_token_usage_total",
    "Cumulative token usage measured during walkthrough runs.",
    ["token_type", "status", "evaluation_status"],
)
_TOKEN_USAGE_PER_RUN = Histogram(
    "narratwin_walkthrough_token_usage_per_run",
    "Token usage observed per walkthrough run.",
    ["token_type", "status", "evaluation_status"],
    buckets=(0, 1, 10, 25, 50, 100, 250, 500, 1000, 2500),
)
_ESTIMATED_COST_USD_TOTAL = Counter(
    "narratwin_walkthrough_estimated_cost_usd_total",
    "Cumulative estimated cost recorded for walkthrough runs.",
    ["status", "evaluation_status"],
)
_ESTIMATED_COST_USD_PER_RUN = Histogram(
    "narratwin_walkthrough_estimated_cost_usd_per_run",
    "Estimated cost observed per walkthrough run.",
    ["status", "evaluation_status"],
    buckets=(0.0, 0.0001, 0.001, 0.01, 0.1, 1.0),
)


def record_walkthrough_metrics(
    *,
    tenant_id: str,
    run_id: str,
    status: str,
    evaluation_status: str | None,
    reason_code: str | None,
    latency_ms: int,
    token_usage: Mapping[str, int],
    estimated_cost: float,
) -> None:
    """Record counters and gauges for an executed walkthrough request."""
    del tenant_id
    del run_id
    normalized_status = _bounded_label(status, ALLOWED_STATUSES)
    normalized_reason = _bounded_label(reason_code or "", ALLOWED_REASON_CODES)
    normalized_evaluation_status = _bounded_label(evaluation_status or "", ALLOWED_EVALUATION_STATUSES)
    _RUNS_TOTAL.labels(
        status=normalized_status,
        evaluation_status=normalized_evaluation_status,
        reason_code=normalized_reason,
    ).inc()
    _LATENCY_MS.labels(
        status=normalized_status,
        evaluation_status=normalized_evaluation_status,
    ).observe(max(0, latency_ms))
    for metric_name, value in token_usage.items():
        token_value = max(0, value)
        token_labels = {
            "token_type": _bounded_label(metric_name, ALLOWED_TOKEN_TYPES),
            "status": normalized_status,
            "evaluation_status": normalized_evaluation_status,
        }
        _TOKEN_USAGE_TOTAL.labels(**token_labels).inc(token_value)
        _TOKEN_USAGE_PER_RUN.labels(**token_labels).observe(token_value)
    cost_value = max(0.0, estimated_cost)
    cost_labels = dict(
        status=normalized_status,
        evaluation_status=normalized_evaluation_status,
    )
    _ESTIMATED_COST_USD_TOTAL.labels(**cost_labels).inc(cost_value)
    _ESTIMATED_COST_USD_PER_RUN.labels(**cost_labels).observe(cost_value)


def _bounded_label(value: str, allowed: set[str]) -> str:
    return value if value in allowed else "OTHER"
