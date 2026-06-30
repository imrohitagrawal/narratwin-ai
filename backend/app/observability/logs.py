"""Structured logging utilities for Stage 5 observability."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any

structlog: Any | None = None
try:  # pragma: no cover - optional dependency behavior
    import structlog as _structlog
    structlog = _structlog
except Exception:  # pragma: no cover - optional dependency behavior
    structlog = None

_LOGGER: Any | None = None



def configure_structured_logging() -> None:
    """Initialize logging once and keep process-wide configuration."""
    global _LOGGER

    if _LOGGER is not None:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if structlog is None:
        _LOGGER = logging.getLogger("narratwin-ai")
        return

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
    _LOGGER = structlog.get_logger("narratwin-ai")



def get_structured_logger() -> Any:
    """Return a structured logger when available, otherwise stdlib logger."""
    configure_structured_logging()
    if _LOGGER is None:  # pragma: no cover - defensive fallback
        return logging.getLogger("narratwin-ai")
    return _LOGGER



def _serialize_fields(fields: dict[str, object]) -> dict[str, object]:
    serialized: dict[str, object] = {}
    for key, value in fields.items():
        if isinstance(value, Mapping):
            serialized[key] = {str(k): _serialize_fields(dict(value)) if isinstance(v, Mapping) else v for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            serialized[key] = [
                {str(k): _serialize_fields(dict(v)) if isinstance(v, Mapping) else v for k, v in item.items()}
                if isinstance(item, Mapping)
                else item
                for item in value
            ]
        else:
            serialized[key] = value
    return serialized



def log_event(
    *,
    event_name: str,
    **fields: object,
) -> None:
    """Emit a structured event suitable for audit and security review."""
    logger = get_structured_logger()
    payload = _serialize_fields(fields)
    payload["event"] = event_name

    if structlog is None:
        safe_payload = json.dumps(payload, sort_keys=True)
        logger.info(safe_payload)
        return

    logger.info(payload)
