from fastapi.testclient import TestClient

from gateway.app import app


client = TestClient(app)


def test_request_flow_creates_decision_and_log() -> None:
    response = client.post(
        "/request",
        json={
            "url": "wikipedia.org/chemistry",
            "user_age": 13,
            "request_context": "homework research",
            "device_id": "demo-device-1",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "id" in body

    logs_response = client.get("/logs?n=5")
    assert logs_response.status_code == 200
    assert logs_response.json()["count"] >= 1
