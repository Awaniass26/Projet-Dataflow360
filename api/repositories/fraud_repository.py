"""Accès aux données pour les alertes de fraude."""

from datetime import datetime
from typing import Protocol

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.core.exceptions import DatabaseError
from api.db.models import Client, FraudAlert, Transaction
from api.schemas.common import RiskLevel
from api.schemas.fraud import (
    FraudAlertEvolutionPoint,
    FraudAlertResponse,
    FraudStatsResponse,
    TransactionInput,
)


class FraudAlertRepository(Protocol):
    """Contrat d'accès aux alertes de fraude."""

    def save_alert(
        self,
        transaction_id: str,
        risk_score: float,
        risk_level: RiskLevel,
    ) -> FraudAlertResponse:
        ...

    def list_alerts(
        self,
        limit: int = 50,
    ) -> list[FraudAlertResponse]:
        ...

    def get_alert(self, alert_id: int) -> FraudAlertResponse | None:
        ...

    def get_stats(self) -> FraudStatsResponse:
        ...

    def save_transaction_and_alert(
        self,
        transaction: TransactionInput,
        risk_score: float,
        risk_level: RiskLevel,
    ) -> FraudAlertResponse:
        ...


class PostgresFraudAlertRepository:
    """Implémentation PostgreSQL du repository fraude."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_alert(
        self,
        transaction_id: str,
        risk_score: float,
        risk_level: RiskLevel,
    ) -> FraudAlertResponse:
        record = FraudAlert(
            transaction_id=transaction_id,
            risk_score=risk_score,
            risk_level=risk_level.value,
        )

        self._session.add(record)
        self._session.flush()

        return self._to_response(record)

    def save_transaction_and_alert(
        self,
        transaction: TransactionInput,
        risk_score: float,
        risk_level: RiskLevel,
    ) -> FraudAlertResponse:
        existing_transaction = self._session.get(
            Transaction,
            transaction.transaction_id,
        )
        if existing_transaction is None:
            if self._session.get(Client, transaction.sender_account_id) is None:
                raise DatabaseError(
                    "La transaction ne peut pas être persistée : "
                    f"client '{transaction.sender_account_id}' introuvable."
                )
            existing_transaction = Transaction(
                transaction_id=transaction.transaction_id,
                client_id=transaction.sender_account_id,
                amount=transaction.amount,
                type=transaction.transaction_type.value,
                channel=transaction.channel.value,
                occurred_at=transaction.occurred_at,
            )
            self._session.add(existing_transaction)
            self._session.flush()

        existing_alert = (
            self._session.query(FraudAlert)
            .filter(FraudAlert.transaction_id == transaction.transaction_id)
            .one_or_none()
        )
        if existing_alert is not None:
            return self._to_response(existing_alert)

        return self.save_alert(
            transaction_id=transaction.transaction_id,
            risk_score=risk_score,
            risk_level=risk_level,
        )

    def list_alerts(
        self,
        limit: int = 50,
    ) -> list[FraudAlertResponse]:
        records = (
            self._session.query(FraudAlert)
            .order_by(FraudAlert.created_at.desc())
            .limit(limit)
            .all()
        )

        return [self._to_response(record) for record in records]

    def get_alert(self, alert_id: int) -> FraudAlertResponse | None:
        record = self._session.get(FraudAlert, alert_id)
        return self._to_response(record) if record is not None else None

    def get_stats(self) -> FraudStatsResponse:
        total_transactions = (
            self._session.query(func.count(Transaction.transaction_id)).scalar() or 0
        )
        total_alerts = (
            self._session.query(func.count(FraudAlert.alert_id)).scalar() or 0
        )
        suspicious_amount = (
            self._session.query(func.sum(Transaction.amount))
            .join(FraudAlert, FraudAlert.transaction_id == Transaction.transaction_id)
            .scalar()
            or 0.0
        )

        alerts_by_risk_level = {level.value: 0 for level in RiskLevel}
        risk_rows = (
            self._session.query(FraudAlert.risk_level, func.count(FraudAlert.alert_id))
            .group_by(FraudAlert.risk_level)
            .all()
        )
        for risk_level, count in risk_rows:
            alerts_by_risk_level[risk_level] = count

        evolution_rows = (
            self._session.query(
                func.date(FraudAlert.created_at).label("date"),
                func.count(FraudAlert.alert_id).label("alert_count"),
                func.sum(Transaction.amount).label("suspicious_amount"),
            )
            .join(FraudAlert, FraudAlert.transaction_id == Transaction.transaction_id)
            .group_by(func.date(FraudAlert.created_at))
            .order_by(func.date(FraudAlert.created_at))
            .all()
        )

        return FraudStatsResponse(
            total_transactions=total_transactions,
            total_alerts=total_alerts,
            suspicious_rate=(total_alerts / total_transactions)
            if total_transactions
            else 0.0,
            suspicious_amount=float(suspicious_amount),
            alerts_by_risk_level=alerts_by_risk_level,
            alerts_evolution=[
                FraudAlertEvolutionPoint(
                    date=row.date,
                    alert_count=row.alert_count,
                    suspicious_amount=float(row.suspicious_amount or 0.0),
                )
                for row in evolution_rows
            ],
        )

    @staticmethod
    def _to_response(record: FraudAlert) -> FraudAlertResponse:
        return FraudAlertResponse(
            alert_id=record.alert_id,
            transaction_id=record.transaction_id,
            risk_score=record.risk_score,
            risk_level=RiskLevel(record.risk_level),
            created_at=record.created_at or datetime.now(),
        )