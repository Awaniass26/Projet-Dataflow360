"""Tests des repositories PostgreSQL avec une base SQLite isolée."""

from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.db.models import Base, Client, CreditApplication
from api.repositories.credit_repository import PostgresCreditScoreRepository
from api.repositories.fraud_repository import PostgresFraudAlertRepository
from api.schemas.common import RiskLevel
from api.schemas.fraud import TransactionInput


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _transaction() -> TransactionInput:
    return TransactionInput(
        transaction_id="txn_repo_1",
        amount=15000,
        transaction_type="transfer",
        channel="mobile_app",
        occurred_at=datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc),
        sender_account_id="client_repo_1",
        recipient_account_id="client_repo_2",
        hour=10,
        ecart_montant_moyen=5000,
        ecart_heure_habituelle=1.5,
        nouvel_appareil=False,
        nouveau_destinataire=True,
    )


def test_fraud_repository_persists_transaction_and_alert_idempotently() -> None:
    session = _session()
    session.add(
        Client(
            client_id="client_repo_1",
            age=30,
            sexe="F",
            region="Dakar",
            account_type="standard",
        )
    )
    session.commit()

    repository = PostgresFraudAlertRepository(session)
    first = repository.save_transaction_and_alert(_transaction(), 0.9, RiskLevel.HIGH)
    session.commit()
    second = repository.save_transaction_and_alert(_transaction(), 0.9, RiskLevel.HIGH)

    assert first.alert_id == second.alert_id
    stats = repository.get_stats()
    assert stats.total_transactions == 1
    assert stats.total_alerts == 1
    assert stats.suspicious_amount == 15000


def test_credit_repository_lists_applications_and_computes_stats() -> None:
    session = _session()
    session.add(
        Client(
            client_id="client_credit_1",
            age=35,
            sexe="M",
            region="Dakar",
            account_type="standard",
        )
    )
    session.add(
        CreditApplication(
            application_id="application_repo_1",
            client_id="client_credit_1",
            requested_amount=50000,
            duration=6,
            income=100000,
            expenses=40000,
        )
    )
    session.commit()

    repository = PostgresCreditScoreRepository(session)
    score = repository.save_score("application_repo_1", 0.35, RiskLevel.LOW)
    session.commit()

    assert score is not None
    assert repository.list_applications()[0].risk_score == 0.35
    stats = repository.get_stats()
    assert stats.total_applications == 1
    assert stats.average_score == 0.35
    assert stats.average_requested_amount == 50000
    assert "default_rate" not in stats.model_dump()
