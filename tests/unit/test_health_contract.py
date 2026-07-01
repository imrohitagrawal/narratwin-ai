from backend.app.main import health_payload


def test_health_payload_is_stage7_contract() -> None:
    payload = health_payload()

    assert payload.status == "ok"
    assert payload.service == "narratwin-ai-backend"
    assert payload.stage == "7"
