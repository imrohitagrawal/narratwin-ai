#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import os
import signal
import tarfile
import tempfile
import time
from html.parser import HTMLParser
from typing import Callable


BASE_IMAGE = (
    "docker.io/library/python:3.13-alpine@"
    "sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0"
)
CHECK_TO_CVE = {
    "hardlink_outside_destination": "CVE-2026-11940",
    "streaming_tar_terminates": "CVE-2026-11972",
    "html_parser_hostile_input_bounded": "CVE-2026-15308",
}


def hardlink_outside_destination() -> bool:
    with tempfile.TemporaryDirectory() as temp:
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            symlink = tarfile.TarInfo("a/b/s")
            symlink.type = tarfile.SYMTYPE
            symlink.linkname = os.path.join("..", "escape")
            tar.addfile(symlink)
            hardlink = tarfile.TarInfo("s")
            hardlink.type = tarfile.LNKTYPE
            hardlink.linkname = os.path.join("a", "b", "s")
            tar.addfile(hardlink)
        archive.seek(0)
        try:
            with tarfile.open(fileobj=archive, mode="r") as tar:
                tar.extractall(temp, filter="data")
        except tarfile.LinkFallbackError as exc:
            return isinstance(exc.__cause__, tarfile.LinkOutsideDestinationError)
        return False


def streaming_tar_terminates() -> bool:
    class ProbeTimeout(Exception):
        pass

    def _timeout(_signum: int, _frame: object) -> None:
        raise ProbeTimeout

    header = tarfile.TarInfo("huge-file")
    header.size = 1 << 64
    stream = io.BytesIO()
    stream.write(header.tobuf(tarfile.PAX_FORMAT))
    stream.seek(0)
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.setitimer(signal.ITIMER_REAL, 1.0)
    try:
        with tarfile.open(fileobj=stream, mode="r|") as tar:
            tar.getmembers()
    except tarfile.ReadError:
        return True
    except ProbeTimeout:
        return False
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)
    return False


def html_parser_hostile_input_bounded() -> bool:
    parser = HTMLParser()
    chunk = "<" + ("x" * 8)
    start = time.monotonic()
    for _ in range(5_000):
        parser.feed(chunk)
    parser.close()
    return time.monotonic() - start < 2.0


def run_regressions(
    *,
    expect: str,
    max_seconds: float,
    probes: dict[str, Callable[[], bool]] | None = None,
) -> dict[str, object]:
    probes = probes or {
        "hardlink_outside_destination": hardlink_outside_destination,
        "streaming_tar_terminates": streaming_tar_terminates,
        "html_parser_hostile_input_bounded": html_parser_hostile_input_bounded,
    }
    started = time.monotonic()
    checks: dict[str, dict[str, object]] = {}
    details: dict[str, str] = {}
    for name in probes:
        cve = CHECK_TO_CVE[name]
        before = time.monotonic()
        try:
            passed = bool(probes[name]())
        except Exception as exc:  # noqa: BLE001 - fail closed without traceback or secret leakage
            passed = False
            details[name] = type(exc).__name__
        seconds = time.monotonic() - before
        checks[cve] = {"status": "pass" if passed else "fail", "seconds": seconds}
        details.setdefault(name, "executed")
    elapsed = time.monotonic() - started
    fixed = all(item["status"] == "pass" for item in checks.values()) and elapsed < max_seconds
    desired = fixed if expect == "fixed" else not fixed
    return {
        "status": "pass" if desired else "fail", "base_image": BASE_IMAGE,
        "python": ".".join(str(part) for part in __import__("sys").version_info[:3]),
        "checks": checks, "details": details, "maximum_seconds": elapsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=("fixed", "vulnerable"), default="fixed")
    parser.add_argument("--max-seconds", type=float, default=2.0)
    args = parser.parse_args()
    evidence = run_regressions(expect=args.expect, max_seconds=args.max_seconds)
    print(json.dumps(evidence, sort_keys=True))
    return 0 if evidence["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
