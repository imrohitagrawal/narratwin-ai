"""Bounded Git diff evidence for the exact Issue #324 scope."""

from __future__ import annotations

import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ISSUE_324_BASE_SHA = "11385d661e1da23f9be4101d9e8d3b3d2ca679e4"
GIT = "/usr/bin/git"
GIT_TIMEOUT_SECONDS = 5
MAX_GIT_PATHS = 256
MAX_GIT_PATH_LENGTH = 512
MAX_UNTRACKED_FILE_BYTES = 262_144
MAX_UNTRACKED_TOTAL_BYTES = 2_097_152


def _run_git(*args: str) -> subprocess.CompletedProcess[bytes] | None:
    env = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_LAZY_FETCH": "1",
    }
    try:
        return subprocess.run(
            [GIT, *args],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def resolve_base() -> str | None:
    exists = _run_git("cat-file", "-e", f"{ISSUE_324_BASE_SHA}^{{commit}}")
    ancestor = _run_git("merge-base", "--is-ancestor", ISSUE_324_BASE_SHA, "HEAD")
    if not exists or exists.returncode or not ancestor or ancestor.returncode:
        return None
    return ISSUE_324_BASE_SHA


def _nul_paths(raw: bytes) -> list[str] | None:
    if raw and not raw.endswith(b"\0"):
        return None
    try:
        paths = [item.decode("utf-8") for item in raw.split(b"\0")[:-1]]
    except UnicodeError:
        return None
    return paths if len(paths) <= MAX_GIT_PATHS else None


def _regular_untracked_file(relative_path: str) -> Path | None:
    if (
        not relative_path
        or len(relative_path) > MAX_GIT_PATH_LENGTH
        or relative_path.startswith(("/", "\\", "~/"))
        or "\\" in relative_path
        or any(unicodedata.category(char).startswith("C") for char in relative_path)
        or any(part in {"", ".", ".."} for part in relative_path.split("/"))
    ):
        return None
    path = ROOT / relative_path
    cursor = ROOT
    for part in Path(relative_path).parts[:-1]:
        cursor /= part
        if cursor.is_symlink():
            return None
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_UNTRACKED_FILE_BYTES:
            return None
    except OSError:
        return None
    return path


def changed_files(base: str) -> list[str] | None:
    tracked = _run_git("diff", "--name-only", "-z", base)
    untracked = _run_git("ls-files", "--others", "--exclude-standard", "-z")
    if not tracked or tracked.returncode or not untracked or untracked.returncode:
        return None
    tracked_paths = _nul_paths(tracked.stdout)
    untracked_paths = _nul_paths(untracked.stdout)
    if tracked_paths is None or untracked_paths is None:
        return None
    return sorted(set(tracked_paths + untracked_paths))


def parse_numstat(source: str) -> int | None:
    total = 0
    for row in source.splitlines():
        fields = row.split("\t")
        if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
            return None
        total += int(fields[0]) + int(fields[1])
    return total


def charged_lines(base: str) -> int | None:
    diff = _run_git("diff", "--numstat", base)
    untracked = _run_git("ls-files", "--others", "--exclude-standard", "-z")
    if not diff or diff.returncode or not untracked or untracked.returncode:
        return None
    try:
        total = parse_numstat(diff.stdout.decode("utf-8"))
    except UnicodeError:
        return None
    paths = _nul_paths(untracked.stdout)
    if total is None or paths is None:
        return None
    untracked_bytes = 0
    for path in paths:
        target = _regular_untracked_file(path)
        if target is None:
            return None
        try:
            raw = target.read_bytes()
            untracked_bytes += len(raw)
            if untracked_bytes > MAX_UNTRACKED_TOTAL_BYTES:
                return None
            text = raw.decode("utf-8")
        except (OSError, UnicodeError):
            return None
        total += len(text.splitlines())
    return total
