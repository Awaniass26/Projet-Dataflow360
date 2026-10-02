"""Fixtures partagées : l'app se teste sans PostgreSQL ni modèle réel."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.core.config import Settings
from api.dependencies import get_settings
from api.main import app


@pytest.fixture
def simulation_settings() -> Settings:
    return Settings(
        environment="test",
        simulation_enabled=True,
        database_url=None,
        fraud_model_path=None,
        credit_model_path=None,
    )


@pytest.fixture
def client(simulation_settings: Settings) -> Iterator[TestClient]:
    app.dependency_overrides[get_settings] = lambda: simulation_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_transaction_payload() -> dict:
    return {
        "transaction_id": "txn_0001",
        "amount": 15000,
        "transaction_type": "transfer",
        "channel": "mobile_app",
        "occurred_at": "2026-01-15T10:30:00Z",
        "sender_account_id": "acc_sender_1",
        "recipient_account_id": "acc_recipient_1",
        "hour": 10,
        "ecart_montant_moyen": 5000,
        "ecart_heure_habituelle": 1.5,
        "nouvel_appareil": False,
        "nouveau_destinataire": True,
    }


@pytest.fixture
def valid_credit_application_payload() -> dict:
    return {
        "application_id": "credit_app_0001",
        "account_id": "acc_0001",
        "requested_amount": 50000,
        "requested_duration_months": 6,
    }
