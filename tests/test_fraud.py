"""Tests de la fonctionnalité fraude."""

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from api.dependencies import get_fraud_alert_repository
from api.main import app
from api.schemas.common import RiskLevel
from api.schemas.fraud import FraudAlertResponse, FraudStatsResponse


class FakeFraudAlertRepository:
    def get_alert(self, alert_id: int) -> FraudAlertResponse | None:
        if alert_id != 7:
            return None
        return FraudAlertResponse(
            alert_id=7,
            transaction_id="txn_0007",
            risk_score=0.91,
            risk_level=RiskLevel.HIGH,
            created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )

    def get_stats(self) -> FraudStatsResponse:
        return FraudStatsResponse(
            total_transactions=10,
            total_alerts=2,
            suspicious_rate=0.2,
            suspicious_amount=30000,
            alerts_by_risk_level={"low": 0, "medium": 1, "high": 1},
            alerts_evolution=[
                {
                    "date": date(2026, 1, 15),
                    "alert_count": 2,
                    "suspicious_amount": 30000,
                }
            ],
        )


def test_predict_returns_simulation_when_model_not_configured(
    client: TestClient, valid_transaction_payload: dict
) -> None:
    response = client.post("/fraud/predict", json=valid_transaction_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["is_simulation"] is True
    assert body["status"] == "simulated"
    assert body["risk_score"] is None
    assert body["transaction_id"] == valid_transaction_payload["transaction_id"]


def test_predict_rejects_missing_required_field(client: TestClient, valid_transaction_payload: dict) -> None:
    payload = dict(valid_transaction_payload)
    del payload["amount"]

    response = client.post("/fraud/predict", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert any(detail["field"] == "amount" for detail in body["error"]["details"])


def test_predict_rejects_negative_amount(client: TestClient, valid_transaction_payload: dict) -> None:
    payload = dict(valid_transaction_payload, amount=-100)

    response = client.post("/fraud/predict", json=payload)

    assert response.status_code == 422


def test_predict_returns_explicit_error_when_no_model_and_no_simulation(
    client: TestClient, valid_transaction_payload: dict, simulation_settings
) -> None:
    simulation_settings.simulation_enabled = False

    response = client.post("/fraud/predict", json=valid_transaction_payload)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_not_configured"


def test_list_alerts_returns_explicit_error_when_database_not_configured(client: TestClient) -> None:
    response = client.get("/fraud/alerts")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_not_configured"


def test_get_fraud_alert_returns_alert(client: TestClient) -> None:
    app.dependency_overrides[get_fraud_alert_repository] = FakeFraudAlertRepository

    response = client.get("/fraud/alerts/7")

    assert response.status_code == 200
    assert response.json()["risk_level"] == "high"


def test_get_unknown_fraud_alert_returns_404(client: TestClient) -> None:
    app.dependency_overrides[get_fraud_alert_repository] = FakeFraudAlertRepository

    response = client.get("/fraud/alerts/8")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"


def test_get_fraud_stats_returns_repository_values(client: TestClient) -> None:
    app.dependency_overrides[get_fraud_alert_repository] = FakeFraudAlertRepository

    response = client.get("/fraud/stats")

    assert response.status_code == 200
    assert response.json()["total_transactions"] == 10
    assert response.json()["suspicious_rate"] == 0.2
