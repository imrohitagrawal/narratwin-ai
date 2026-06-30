"""OpenTelemetry helpers for Stage 5 tracing and trace IDs."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider


def _ensure_tracer() -> None:
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        return
    tracer_provider = TracerProvider(
        resource=Resource.create({"service.name": "narratwin-ai", "service.version": "0.1.0"})
    )
    trace.set_tracer_provider(tracer_provider)


@contextmanager
def with_trace(*, scope: str, name: str, attributes: dict[str, object] | None = None) -> Iterator[str]:
    """Run a code path inside an OpenTelemetry span and expose its trace ID."""
    _ensure_tracer()
    tracer = trace.get_tracer(scope)
    attrs = attributes or {}
    with tracer.start_as_current_span(name) as span:
        for key, value in attrs.items():
            span.set_attribute(str(key), str(value))
        trace_id = span.get_span_context().trace_id
        yield f"trace_{trace_id:032x}"
