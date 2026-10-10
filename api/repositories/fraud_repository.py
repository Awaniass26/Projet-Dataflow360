"""Accès aux données pour les alertes de fraude."""

from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.core.exceptions import DatabaseError
from api.db.models import Client, FraudAlert, Transaction
from api.schemas.common import FraudAlertStatus, RiskLevel
from api.schemas.fraud import (
    FraudAlertEvolutionPoint,
    FraudAlertZonePoint,
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
        page: int = 1,
        page_size: int = 50,
        risk_level: RiskLevel | None = None,
        status: FraudAlertStatus | None = None,
        data_origin: str | None = None,
    ) -> tuple[list[FraudAlertResponse], int]:
        ...

    def get_alert(
        self,
        alert_id: int,
    ) -> FraudAlertResponse | None:
        ...

    def update_alert(
        self,
        alert_id: int,
        status: FraudAlertStatus,
        reviewed_by: str,
        explanation: str | None = None,
    ) -> FraudAlertResponse | None:
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
            data_origin="kafka",  # ← AJOUT
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
            if self._session.get(
                Client,
                transaction.sender_account_id,
            ) is None:
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
                data_origin="kafka",     # ← AJOUT
            )

            self._session.add(existing_transaction)
            self._session.flush()

        existing_alert = (
            self._session.query(FraudAlert)
            .filter(
                FraudAlert.transaction_id
                == transaction.transaction_id
            )
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
        page: int = 1,
        page_size: int = 50,
        risk_level: RiskLevel | None = None,
        status: FraudAlertStatus | None = None,
        data_origin: str | None = None,
    ) -> tuple[list[FraudAlertResponse], int]:
        """Retourne une page d'alertes avec filtres optionnels."""

        query = self._session.query(FraudAlert)

        if risk_level is not None:
            query = query.filter(
                FraudAlert.risk_level == risk_level.value
            )

        if status is not None:
            query = query.filter(
                FraudAlert.status == status.value
            )

        if data_origin is not None:            # ← AJOUT
            query = query.filter(
                FraudAlert.data_origin == data_origin
            )

        total = query.count()

        records = (
            query
            .order_by(FraudAlert.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        alerts = [
            self._to_response(record)
            for record in records
        ]

        return alerts, total

    def get_alert(
        self,
        alert_id: int,
    ) -> FraudAlertResponse | None:
        """Retourne une alerte par son identifiant."""

        record = self._session.get(FraudAlert, alert_id)

        return (
            self._to_response(record)
            if record is not None
            else None
        )

    def update_alert(
        self,
        alert_id: int,
        status: FraudAlertStatus,
        reviewed_by: str,
        explanation: str | None = None,
    ) -> FraudAlertResponse | None:
        """Met à jour le traitement d'une alerte."""

        record = self._session.get(FraudAlert, alert_id)

        if record is None:
            return None

        record.status = status.value
        record.reviewed_by = reviewed_by
        record.reviewed_at = datetime.now(timezone.utc)
        record.explanation = explanation

        self._session.flush()

        return self._to_response(record)

    def get_stats(self) -> FraudStatsResponse:
        """Retourne les statistiques de fraude."""

        total_transactions = (
            self._session
            .query(func.count(Transaction.transaction_id))
            .scalar()
            or 0
        )

        total_alerts = (
            self._session
            .query(func.count(FraudAlert.alert_id))
            .scalar()
            or 0
        )

        suspicious_amount = (
            self._session
            .query(func.sum(Transaction.amount))
            .join(
                FraudAlert,
                FraudAlert.transaction_id
                == Transaction.transaction_id,
            )
            .scalar()
            or 0.0
        )

        alerts_by_risk_level = {
            level.value: 0
            for level in RiskLevel
        }

        alerts_by_status = {
            status.value: 0
            for status in FraudAlertStatus
        }

        status_rows = (
            self._session
            .query(
                FraudAlert.status,
                func.count(FraudAlert.alert_id),
            )
            .group_by(FraudAlert.status)
            .all()
        )

        for status, count in status_rows:
            alerts_by_status[status] = count

        risk_rows = (
            self._session
            .query(
                FraudAlert.risk_level,
                func.count(FraudAlert.alert_id),
            )
            .group_by(FraudAlert.risk_level)
            .all()
        )

        for risk_level, count in risk_rows:
            alerts_by_risk_level[risk_level] = count

        evolution_rows = (
            self._session
            .query(
                func.date(FraudAlert.created_at).label("date"),
                func.count(FraudAlert.alert_id).label(
                    "alert_count"
                ),
                func.sum(Transaction.amount).label(
                    "suspicious_amount"
                ),
            )
            .join(
                FraudAlert,
                FraudAlert.transaction_id
                == Transaction.transaction_id,
            )
            .group_by(func.date(FraudAlert.created_at))
            .order_by(func.date(FraudAlert.created_at))
            .all()
        )

        # Alertes et taux par zone géographique (région client)
        zone_tx_rows = (
            self._session.query(
                Client.region.label("zone"),
                func.count(Transaction.transaction_id).label("transaction_count"),
            )
            .join(Transaction, Transaction.client_id == Client.client_id)
            .group_by(Client.region)
            .all()
        )
        zone_alert_rows = (
            self._session.query(
                Client.region.label("zone"),
                func.count(FraudAlert.alert_id).label("alert_count"),
            )
            .join(Transaction, Transaction.client_id == Client.client_id)
            .join(
                FraudAlert,
                FraudAlert.transaction_id == Transaction.transaction_id,
            )
            .group_by(Client.region)
            .all()
        )
        alerts_by_zone_map = {
            row.zone: row.alert_count for row in zone_alert_rows
        }
        alerts_by_zone = []
        for row in zone_tx_rows:
            zone = row.zone or "Inconnue"
            tx_count = int(row.transaction_count or 0)
            alert_count = int(alerts_by_zone_map.get(row.zone, 0))
            alerts_by_zone.append(
                FraudAlertZonePoint(
                    zone=zone,
                    alert_count=alert_count,
                    transaction_count=tx_count,
                    alert_rate=(
                        alert_count / tx_count if tx_count else 0.0
                    ),
                )
            )
        alerts_by_zone.sort(key=lambda z: z.alert_rate, reverse=True)

        return FraudStatsResponse(
            total_transactions=total_transactions,
            total_alerts=total_alerts,
            suspicious_rate=(
                total_alerts / total_transactions
                if total_transactions
                else 0.0
            ),
            suspicious_amount=float(suspicious_amount),
            alerts_by_risk_level=alerts_by_risk_level,
            alerts_by_status=alerts_by_status,
            alerts_evolution=[
                FraudAlertEvolutionPoint(
                    date=row.date,
                    alert_count=row.alert_count,
                    suspicious_amount=float(
                        row.suspicious_amount or 0.0
                    ),
                )
                for row in evolution_rows
            ],
            alerts_by_zone=alerts_by_zone,
        )

    @staticmethod
    def _to_response(
        record: FraudAlert,
    ) -> FraudAlertResponse:
        """Convertit un modèle SQLAlchemy en réponse API."""

        return FraudAlertResponse(
            alert_id=record.alert_id,
            transaction_id=record.transaction_id,
            risk_score=record.risk_score,
            risk_level=RiskLevel(record.risk_level),
            status=FraudAlertStatus(record.status),
            explanation=record.explanation,
            reviewed_at=record.reviewed_at,
            reviewed_by=record.reviewed_by,
            created_at=(
                record.created_at
                or datetime.now(timezone.utc)
            ),
        )