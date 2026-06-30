"""Langfuse tracing adapter for Stage 5 observability.

Langfuse is optional; this module degrades to a no-op when credentials are
absent or initialization fails. It keeps tracing instrumentation import-safe in
both local test and offline environments.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any
import os
from typing import cast

LangfuseClient: Any | None

try:  # pragma: no cover - depends on optional install
    from langfuse import Langfuse as LangfuseClient
except Exception:  # pragma: no cover - optional dependency behavior
    LangfuseClient = None
_LANGFUSE_CLIENT: Any | None = None
_LANGFUSE_AVAILABLE = LangfuseClient is not None


def is_langfuse_enabled() -> bool:
    """Return true when Langfuse credentials are configured and usable."""
    if not _LANGFUSE_AVAILABLE:
        return False

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not (public_key and secret_key):
        return False

    host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
    return bool(public_key.strip()) and bool(secret_key.strip()) and bool(host.strip())


def _client() -> Any | None:
    global _LANGFUSE_CLIENT

    if not is_langfuse_enabled() or LangfuseClient is None:
        return None
    if _LANGFUSE_CLIENT is not None:
        return _LANGFUSE_CLIENT

    try:
        _LANGFUSE_CLIENT = cast(Any, LangfuseClient)(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "https://us.cloud.langfuse.com"),
            release=os.getenv("NARRATWIN_VERSION", "0.1.0"),
        )
    except Exception:
        return None

    return _LANGFUSE_CLIENT


def _clean_metadata(metadata: Mapping[str, object] | None) -> dict[str, object]:
    cleaned: dict[str, object] = {}
    if not metadata:
        return cleaned
    for key, value in metadata.items():
        key_text = str(key)
        if "token" in key_text.lower() or "secret" in key_text.lower():
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key_text] = value
    return cleaned


@contextmanager
def langfuse_observation(
    *,
    name: str,
    trace_id: str,
    run_id: str,
    metadata: Mapping[str, object] | None = None,
) -> Iterator[dict[str, object]]:
    """Wrap a unit of work in a Langfuse observation.

    The implementation stays intentionally conservative and best-effort: when
    Langfuse is not configured or fails to initialize, this yields a lightweight
    metadata payload so call sites can continue without hard dependency.
    """
    clean_metadata = _clean_metadata(metadata)
    clean_metadata["trace_id"] = trace_id
    clean_metadata["run_id"] = run_id
    client = _client()

    if client is None:
        yield clean_metadata
        return

    try:
        trace = getattr(client, "trace", None)
        if trace is None:
            yield clean_metadata
            return

        lf_trace = trace(name="narratwin-walkthrough", input={"runId": run_id}, output=clean_metadata)
        start_obs = getattr(lf_trace, "generation", None)
        if start_obs is None:
            lf_observation = lf_trace
        else:
            lf_observation = start_obs(
                name=name,
                input={"runId": run_id},
                metadata=clean_metadata,
            )

        if hasattr(lf_observation, "__enter__") and hasattr(lf_observation, "__exit__"):
            with lf_observation as observation:
                payload = {**clean_metadata}
                if hasattr(observation, "span_id"):
                    payload["langfuseSpanId"] = str(getattr(observation, "span_id"))
                if hasattr(lf_trace, "trace_id"):
                    payload["langfuseTraceId"] = str(getattr(lf_trace, "trace_id"))
                yield payload
        else:
            yield clean_metadata
    except Exception:
        yield clean_metadata
