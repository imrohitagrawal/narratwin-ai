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


def _scalar_paths(value: Any, prefix: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
    if isinstance(value, dict):
        return [path for key, item in value.items() for path in _scalar_paths(item, (*prefix, key))]
    if isinstance(value, list):
        return [path for index, item in enumerate(value) for path in _scalar_paths(item, (*prefix, index))]
    return [prefix]


SCALAR_PATHS = tuple(_scalar_paths(baseline()))


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


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("gazeRatio", 1.01),
        ("maxOffCameraMs", -1),
        ("maxOffCameraMs", 1.5),
        ("lipOffsetP95Ms", -1),
        ("maxLipErrorMs", -1),
        ("captionWordAccuracy", 1.01),
        ("captionCoverage", 1.01),
        ("maxCaptionGapMs", -1),
        ("maxRepeatedGesture", -1),
        ("scriptEvaluationP95Ms", -1),
        ("previewAfterReadyMs", -1),
    ),
)
def test_schema_invalid_metric_domains_fail_closed(field: str, value: object) -> None:
    evidence = baseline()
    evidence["cells"][0]["metrics"][field] = value
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.INPUT.MALFORMED",
    )


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("cells", 0, "presenterId"), {}),
        (("cells", 0), None),
        (("cells", 0, "lineage", "approvalId"), None),
        (("cells", 0, "artifact", "width"), []),
        (("providerPosture", "credentialCount"), {}),
    ),
)
def test_ordinary_json_shape_corruption_never_raises(
    path: tuple[str | int, ...], value: object
) -> None:
    evidence = baseline()
    cursor: Any = evidence
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.INPUT.MALFORMED",
    )


@pytest.mark.parametrize(
    "value",
    ("Tenant-459", "x" * 129, "/private/sensitive/path"),
)
def test_schema_invalid_observability_ids_fail_closed(value: str) -> None:
    evidence = baseline()
    evidence["observability"]["tenantId"] = value
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.INPUT.MALFORMED",
    )


@pytest.mark.parametrize(
    ("started", "finished"),
    (
        ("2026-W35-5T00:00:00Z", "2026-W35-5T00:00:01Z"),
        ("20260828T000000Z", "20260828T000001Z"),
    ),
)
def test_schema_invalid_timestamp_lexemes_fail_closed(started: str, finished: str) -> None:
    evidence = baseline()
    evidence["observability"]["startedAt"] = started
    evidence["observability"]["finishedAt"] = finished
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.OBSERVABILITY.START_INVALID",
    )


@pytest.mark.parametrize(
    "field",
    ("gazeRatio", "maxOffCameraMs", "identityMismatchCount", "contrastRatio"),
)
def test_extreme_json_integer_is_bounded(field: str) -> None:
    evidence = baseline()
    evidence["cells"][0]["metrics"][field] = 10**10_000
    first = controller.evaluate_controlled_presenter(evidence)
    second = controller.evaluate_controlled_presenter(evidence)
    assert len(first) <= 1
    assert first == second


def test_extreme_artifact_duration_rejects_before_register_serialization() -> None:
    evidence = baseline()
    evidence["cells"][0]["artifact"]["durationMs"] = 10**10_000
    assert controller.finding_codes(controller.evaluate_controlled_presenter(evidence)) == (
        "CUT1.MEDIA.DURATION",
    )


@pytest.mark.parametrize("path", SCALAR_PATHS, ids=lambda path: ".".join(map(str, path)))
def test_every_json_scalar_shape_corruption_is_bounded_and_deterministic(
    path: tuple[str | int, ...],
) -> None:
    evidence = baseline()
    cursor: Any = evidence
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = {}
    first = controller.evaluate_controlled_presenter(evidence)
    second = controller.evaluate_controlled_presenter(evidence)
    assert len(first) == 1
    assert first == second
