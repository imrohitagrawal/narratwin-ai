"""Per-file context budgets for the modular Issue #324 implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .scope import PREFLIGHT_REQUIRED_FILES


ROOT = Path(__file__).resolve().parents[3]
IMPLEMENTATION_FILE_LINE_CAP = 250
TEST_FILE_LINE_CAP = 250
ENTRYPOINT_LINE_CAP = 40
EXISTING_INTEGRATION_FILE_LINE_CAP = 500
FILE_BYTE_CAP = 32_000
MAX_LINE_LENGTH = 120
IMPLEMENTATION_DIRECTORIES = (
    ROOT / "scripts" / "quality" / "publication_boundary",
    ROOT / "scripts" / "quality" / "phase1_closure",
)
TEST_DIRECTORIES = (
    ROOT / "tests" / "unit" / "publication_boundary",
    ROOT / "tests" / "unit" / "phase1_closure",
)
ENTRYPOINTS = (
    ROOT / "scripts" / "quality" / "check_publication_boundary.py",
    ROOT / "scripts" / "quality" / "check_phase1_quality.py",
)
EXISTING_INTEGRATION_FILES = (
    ROOT / "scripts" / "quality" / "check_quality_stage.py",
    ROOT / "scripts" / "quality" / "check_stage8_docs.py",
)
SHARED_IMPLEMENTATION_FILES = (
    ROOT / "scripts" / "quality" / "branch_identity.py",
)
FOCUSED_TEST_FILES = (
    ROOT / "tests" / "unit" / "test_branch_identity.py",
    ROOT / "tests" / "unit" / "test_issue324_stage8_quality.py",
    ROOT / "tests" / "unit" / "test_quality_dispatcher.py",
    ROOT / "tests" / "unit" / "test_quality_stage_dispatch.py",
    ROOT / "tests" / "unit" / "test_stage8_quality_gate.py",
)


@dataclass(frozen=True)
class FileMetrics:
    lines: int
    bytes: int
    max_line_length: int


def file_metrics(path: Path) -> FileMetrics | None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        return None
    cursor = ROOT
    if not path.is_file() or path.is_symlink():
        return None
    for part in relative.parts[:-1]:
        cursor /= part
        if cursor.is_symlink():
            return None
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError):
        return None
    lines = text.splitlines()
    return FileMetrics(len(lines), len(raw), max((len(line) for line in lines), default=0))


def _check_file(path: Path, line_cap: int, failures: list[str]) -> None:
    metrics = file_metrics(path)
    label = path.relative_to(ROOT).as_posix()
    if metrics is None:
        failures.append(f"Context metrics unavailable for {label}.")
        return
    if metrics.lines > line_cap:
        failures.append(f"Context file {label} exceeds {line_cap} lines.")
    if metrics.bytes > FILE_BYTE_CAP:
        failures.append(f"Context file {label} exceeds {FILE_BYTE_CAP} bytes.")
    if metrics.max_line_length > MAX_LINE_LENGTH:
        failures.append(f"Context file {label} contains a line over {MAX_LINE_LENGTH} characters.")


def _check_directory(directory: Path, line_cap: int, failures: list[str]) -> None:
    if not directory.is_dir() or directory.is_symlink():
        failures.append(f"Context directory unavailable: {directory.relative_to(ROOT).as_posix()}.")
        return
    paths = sorted(directory.rglob("*.py"))
    if not paths:
        failures.append(f"Context directory contains no Python modules: {directory.name}.")
        return
    for path in paths:
        _check_file(path, line_cap, failures)


def _owned_context_paths() -> tuple[Path, ...]:
    discovered = [
        path
        for directory in (*IMPLEMENTATION_DIRECTORIES, *TEST_DIRECTORIES)
        if directory.is_dir() and not directory.is_symlink()
        for path in directory.rglob("*.py")
    ]
    return tuple(
        sorted(
            set(
                discovered
                + list(ENTRYPOINTS)
                + list(EXISTING_INTEGRATION_FILES)
                + list(SHARED_IMPLEMENTATION_FILES)
                + list(FOCUSED_TEST_FILES)
            )
        )
    )


def check_context_budgets(failures: list[str]) -> None:
    indexed = set(PREFLIGHT_REQUIRED_FILES)
    for path in _owned_context_paths():
        label = path.relative_to(ROOT).as_posix()
        if label not in indexed:
            failures.append(f"Issue #324 owned context file is not indexed: {label}.")
    for relative_path in PREFLIGHT_REQUIRED_FILES:
        if relative_path == "portfolio/README.md":
            continue
        path = ROOT / relative_path
        if file_metrics(path) is None:
            failures.append(f"Issue #324 required regular file unavailable: {relative_path}.")
    for directory in IMPLEMENTATION_DIRECTORIES:
        _check_directory(directory, IMPLEMENTATION_FILE_LINE_CAP, failures)
    for directory in TEST_DIRECTORIES:
        _check_directory(directory, TEST_FILE_LINE_CAP, failures)
    for entrypoint in ENTRYPOINTS:
        _check_file(entrypoint, ENTRYPOINT_LINE_CAP, failures)
    for integration_file in EXISTING_INTEGRATION_FILES:
        _check_file(integration_file, EXISTING_INTEGRATION_FILE_LINE_CAP, failures)
    for shared_file in SHARED_IMPLEMENTATION_FILES:
        _check_file(shared_file, IMPLEMENTATION_FILE_LINE_CAP, failures)
    for test_file in FOCUSED_TEST_FILES:
        _check_file(test_file, TEST_FILE_LINE_CAP, failures)
