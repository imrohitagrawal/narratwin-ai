from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).parents[3]
PACKAGE_PATH = ROOT / "scripts" / "quality" / "publication_boundary"


@pytest.fixture
def publication_boundary() -> ModuleType:
    assert PACKAGE_PATH.is_dir(), "Issue #324 requires a dedicated publication-boundary package."
    for name in list(sys.modules):
        if name == "scripts.quality.publication_boundary" or name.startswith(
            "scripts.quality.publication_boundary."
        ):
            sys.modules.pop(name)
    return importlib.import_module("scripts.quality.publication_boundary")
