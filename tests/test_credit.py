"""Tests de la fonctionnalité credit scoring."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from api.dependencies import get_credit_score_repository
from api.main import app
from api.schemas.common import RiskLevel
from api.schemas.credit import CreditApplicationResponse, CreditStatsResponse


class FakeCreditScoreRepository:
    def list_applications(self, limit: int = 50) -> list[CreditApplicationResponse]:
        return [
            CreditApplicationResponse(
                application_id="credit_app_0001",
                account_id="acc_0001",
                requested_amount=50000,
                requested_duration_months=6,
                income=100000,
                expenses=40000,
                risk_score=0.35,
                risk_level=RiskLevel.LOW,
                score_created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            )
        ][:limit]

    def get_application(self, application_id: str) -> CreditApplicationResponse | None:
        applications = self.list_applications()
        return applications[0] if application_id == applications[0].application_id else None

    def get_stats(self) -> CreditStatsResponse:
        return CreditStatsResponse(
            total_applications=1,
            average_score=0.35,
            average_requested_amount=50000,
            risk_distribution={"low": 1, "medium": 0, "high": 0},
        )


def test_score_returns_simulation_when_model_not_configured(
    client: TestClient, valid_credit_application_payload: dict
) -> None:
    response = client.post("/credit/score", json=valid_credit_application_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["is_simulation"] is True
    assert body["status"] == "simulated"
    assert body["risk_score"] is None
    assert body["application_id"] == valid_credit_application_payload["application_id"]


def test_score_rejects_missing_required_field(
    client: TestClient, valid_credit_application_payload: dict
) -> None:
    payload = dict(valid_credit_application_payload)
    del payload["requested_amount"]

    response = client.post("/credit/score", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_score_rejects_zero_duration(client: TestClient, valid_credit_application_payload: dict) -> None:
    payload = dict(valid_credit_application_payload, requested_duration_months=0)

    response = client.post("/credit/score", json=payload)

    assert response.status_code == 422


def test_score_returns_explicit_error_when_no_model_and_no_simulation(
    client: TestClient, valid_credit_application_payload: dict, simulation_settings
) -> None:
    simulation_settings.simulation_enabled = False

    response = client.post("/credit/score", json=valid_credit_application_payload)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_not_configured"


def test_get_score_returns_explicit_error_when_database_not_configured(client: TestClient) -> None:
    response = client.get("/credit/score/credit_app_0001")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_not_configured"


def test_list_credit_applications_returns_repository_values(client: TestClient) -> None:
    app.dependency_overrides[get_credit_score_repository] = FakeCreditScoreRepository

    response = client.get("/credit/applications")

    assert response.status_code == 200
    assert response.json()[0]["application_id"] == "credit_app_0001"


def test_get_unknown_credit_application_returns_404(client: TestClient) -> None:
    app.dependency_overrides[get_credit_score_repository] = FakeCreditScoreRepository

    response = client.get("/credit/applications/unknown")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"


def test_get_credit_stats_returns_repository_values(client: TestClient) -> None:
    app.dependency_overrides[get_credit_score_repository] = FakeCreditScoreRepository

    response = client.get("/credit/stats")

    assert response.status_code == 200
    assert response.json()["total_applications"] == 1
    assert "default_rate" not in response.json()
