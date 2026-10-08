"""Tests des routes générales."""

from fastapi.testclient import TestClient


def test_root_route_returns_welcome_message(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert body["docs_url"] == "/docs"


def test_health_route_reports_configuration_state(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["configuration"]["database_configured"] is False
    assert body["configuration"]["fraud_model_configured"] is False
    assert body["configuration"]["simulation_enabled"] is True


def test_unknown_route_returns_structured_404(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.json()
