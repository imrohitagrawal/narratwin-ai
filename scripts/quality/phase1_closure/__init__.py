"""Indexed API for the modular Phase 1 quality runner."""

from .legacy import ACTIVE_DEMO_DOCUMENT, DEMO_MARKERS, PRESERVED_CHECKS
from .legacy import run_preserved_contracts
from .runner import main


__all__ = [
    "ACTIVE_DEMO_DOCUMENT",
    "DEMO_MARKERS",
    "PRESERVED_CHECKS",
    "main",
    "run_preserved_contracts",
]
