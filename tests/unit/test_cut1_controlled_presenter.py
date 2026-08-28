from __future__ import annotations

import importlib.util
import json
import socket
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

import pytest

from backend.app import cut1_controlled_presenter as controller
from scripts.quality import cut1_controlled_presenter as adapter


def _load_baseline_factory() -> Callable[[], dict[str, Any]]:
    path = Path(__file__).with_name("test_cut1_controlled_presenter_red.py")
    spec = importlib.util.spec_from_file_location("cut1_red_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("controlled-presenter fixture could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Callable[[], dict[str, Any]], module.baseline)


baseline = _load_baseline_factory()


def test_quality_module_is_a_thin_canonical_adapter() -> None:
    assert adapter.Finding is controller.Finding
    assert adapter.evaluate_controlled_presenter is controller.evaluate_controlled_presenter
    assert adapter.finding_codes is controller.finding_codes


@pytest.mark.parametrize(
    ("field", "value", "code"),
    (
        ("providerClass", "MockAvatarProvider", "CUT1.PROVIDER.MOCK_EVIDENCE"),
        ("providerClass", "ExternalAvatarProviderStub", "CUT1.PROVIDER.STUB_EVIDENCE"),
        ("supportsRealVideo", False, "CUT1.MEDIA.REAL_VIDEO_REQUIRED"),
    ),
)
def test_mock_stub_and_non_video_capability_never_produce_evidence(
    field: str, value: object, code: str
) -> None:
    evidence = baseline()
    evidence["cells"][0]["artifact"][field] = value
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        code,
    )


@pytest.mark.parametrize("mime_type", ("text/html", "application/json"))
def test_html_and_json_placeholders_are_rejected(mime_type: str) -> None:
    evidence = baseline()
    evidence["cells"][0]["artifact"]["mimeType"] = mime_type
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.MEDIA.TYPE",
    )


def test_evaluation_does_not_touch_network_credentials_or_filesystem(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("side-effect boundary touched")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr("os.getenv", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    before = tuple(tmp_path.iterdir())
    assert controller.evaluate_controlled_presenter(baseline()) == ()
    assert tuple(tmp_path.iterdir()) == before


def test_invalid_evaluation_writes_no_artifact(tmp_path: Path) -> None:
    evidence = baseline()
    evidence["providerPosture"]["egressAttemptCount"] = 1
    before = tuple(tmp_path.iterdir())
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.PROVIDER.EGRESS",
    )
    assert tuple(tmp_path.iterdir()) == before


def test_repeated_evaluation_is_byte_for_byte_deterministic() -> None:
    evidence = baseline()
    evidence["cells"][0]["metrics"]["gazeRatio"] = 0.79

    def encoded() -> bytes:
        findings = controller.evaluate_controlled_presenter(evidence)
        return json.dumps(
            [asdict(finding) for finding in findings],
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")

    assert encoded() == encoded()


def test_evaluation_does_not_mutate_caller_evidence() -> None:
    evidence = baseline()
    before = json.dumps(evidence, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    controller.evaluate_controlled_presenter(evidence)
    after = json.dumps(evidence, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    assert after == before
