"""JSON file persistence helpers for optional local durable state."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .ops_metrics import timed_restore_load

LOGGER = logging.getLogger(__name__)


def resolve_state_file(service_name: str) -> Path | None:
    """Resolve the optional state file for a service.

    Persistence is disabled unless either NARRATWIN_STATE_DIR or a
    service-specific NARRATWIN_<SERVICE>_STATE_FILE variable is configured.
    """
    env_name = f"NARRATWIN_{service_name.upper()}_STATE_FILE"
    explicit_path = os.environ.get(env_name, "").strip()
    if explicit_path:
        return Path(explicit_path)

    state_dir = os.environ.get("NARRATWIN_STATE_DIR", "").strip()
    if not state_dir:
        return None
    return Path(state_dir) / f"{service_name.lower()}.json"


def load_state(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    timer = timed_restore_load(surface=f"local-state:{path.stem}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Ignoring unreadable local state snapshot at %s: %s", path, exc)
        timer.observe(result="unreadable")
        return None
    if not isinstance(payload, dict):
        LOGGER.warning("Ignoring local state snapshot at %s because it is not a JSON object.", path)
        timer.observe(result="invalid-shape")
        return None
    timer.observe(result="loaded")
    return payload


def write_state(path: Path | None, payload: Mapping[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
        fsync_directory(path.parent)
    except Exception:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        try:
            os.fsync(descriptor)
        except OSError:
            pass
    finally:
        os.close(descriptor)
