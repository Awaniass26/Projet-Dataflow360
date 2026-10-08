"""Accès aux données pour les résultats de scoring de crédit."""

from datetime import datetime
from typing import Protocol

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.db.models import CreditApplication, CreditScore
from api.schemas.common import RiskLevel
from api.schemas.credit import (
    CreditApplicationResponse,
    CreditScoreRecord as CreditScoreRecordSchema,
    CreditStatsResponse,
)


class CreditScoreRepository(Protocol):
    """Contrat d'accès aux scores de crédit."""

    def save_score(
        self,
        application_id: str,
        risk_score: float,
        risk_level: RiskLevel | None,
    ) -> CreditScoreRecordSchema | None:
        ...

    def get_score(
        self,
        application_id: str,
    ) -> CreditScoreRecordSchema | None:
        ...

    def list_applications(
        self,
        limit: int = 50,
    ) -> list[CreditApplicationResponse]:
        ...

    def get_application(
        self,
        application_id: str,
    ) -> CreditApplicationResponse | None:
        ...

    def get_stats(self) -> CreditStatsResponse:
        ...


class PostgresCreditScoreRepository:
    """Implémentation PostgreSQL du repository crédit."""

    APPROVAL_THRESHOLD = 0.90

    def __init__(self, session: Session) -> None:
        self._session = session

    def _latest_score_ids(self):
        """Retourne le dernier score de chaque demande de crédit."""

        ranked_scores = (
            self._session.query(
                CreditScore.id.label("score_id"),
                CreditScore.application_id.label("application_id"),
                func.row_number()
                .over(
                    partition_by=CreditScore.application_id,
                    order_by=(
                        CreditScore.created_at.desc(),
                        CreditScore.id.desc(),
                    ),
                )
                .label("row_number"),
            )
            .subquery()
        )

        return (
            self._session.query(
                ranked_scores.c.score_id,
                ranked_scores.c.application_id,
            )
            .filter(ranked_scores.c.row_number == 1)
            .subquery()
        )

    def save_score(
        self,
        application_id: str,
        risk_score: float,
        risk_level: RiskLevel | None,
    ) -> CreditScoreRecordSchema | None:
        """Enregistre un nouveau score pour une demande."""

        application = self._session.get(
            CreditApplication,
            application_id,
        )

        if application is None:
            return None

        record = CreditScore(
            application_id=application_id,
            risk_score=risk_score,
            risk_level=risk_level.value if risk_level else None,
        )

        self._session.add(record)
        self._session.flush()

        return self._to_schema(record, application)

    def get_score(
        self,
        application_id: str,
    ) -> CreditScoreRecordSchema | None:
        """Retourne le dernier score d'une demande."""

        latest_scores = self._latest_score_ids()

        result = (
            self._session.query(
                CreditScore,
                CreditApplication,
            )
            .join(
                CreditApplication,
                CreditScore.application_id
                == CreditApplication.application_id,
            )
            .join(
                latest_scores,
                CreditScore.id == latest_scores.c.score_id,
            )
            .filter(
                CreditScore.application_id == application_id,
            )
            .first()
        )

        if result is None:
            return None

        score, application = result

        return self._to_schema(
            score,
            application,
        )

    def list_applications(
        self,
        limit: int = 50,
    ) -> list[CreditApplicationResponse]:
        """Liste les demandes avec leur dernier score."""

        latest_scores = self._latest_score_ids()

        rows = (
            self._session.query(
                CreditApplication,
                CreditScore,
            )
            .outerjoin(
                latest_scores,
                latest_scores.c.application_id
                == CreditApplication.application_id,
            )
            .outerjoin(
                CreditScore,
                CreditScore.id == latest_scores.c.score_id,
            )
            .order_by(
                CreditApplication.application_id,
            )
            .limit(limit)
            .all()
        )

        return [
            self._to_application_schema(
                application,
                score,
            )
            for application, score in rows
        ]

    def get_application(
        self,
        application_id: str,
    ) -> CreditApplicationResponse | None:
        """Retourne une demande avec son dernier score."""

        latest_scores = self._latest_score_ids()

        row = (
            self._session.query(
                CreditApplication,
                CreditScore,
            )
            .outerjoin(
                latest_scores,
                latest_scores.c.application_id
                == CreditApplication.application_id,
            )
            .outerjoin(
                CreditScore,
                CreditScore.id == latest_scores.c.score_id,
            )
            .filter(
                CreditApplication.application_id
                == application_id,
            )
            .first()
        )

        if row is None:
            return None

        application, score = row

        return self._to_application_schema(
            application,
            score,
        )

    def get_stats(self) -> CreditStatsResponse:
        """Calcule les KPI crédit à partir des derniers scores."""

        latest_scores = self._latest_score_ids()

        total_applications = (
            self._session.query(
                func.count(
                    CreditApplication.application_id,
                )
            ).scalar()
            or 0
        )

        average_score = (
            self._session.query(
                func.avg(CreditScore.risk_score),
            )
            .join(
                latest_scores,
                CreditScore.id == latest_scores.c.score_id,
            )
            .scalar()
        )

        average_requested_amount = (
            self._session.query(
                func.avg(
                    CreditApplication.requested_amount,
                )
            ).scalar()
        )

        risk_distribution: dict[str, int] = {
            level.value: 0
            for level in RiskLevel
        }

        risk_rows = (
            self._session.query(
                CreditScore.risk_level,
                func.count(CreditScore.id),
            )
            .join(
                latest_scores,
                CreditScore.id == latest_scores.c.score_id,
            )
            .filter(
                CreditScore.risk_level.is_not(None),
            )
            .group_by(
                CreditScore.risk_level,
            )
            .all()
        )

        for risk_level, count in risk_rows:
            risk_distribution[risk_level] = count

        validated_clients = (
            self._session.query(
                func.count(
                    func.distinct(
                        CreditApplication.client_id,
                    )
                )
            )
            .join(
                latest_scores,
                latest_scores.c.application_id
                == CreditApplication.application_id,
            )
            .join(
                CreditScore,
                CreditScore.id == latest_scores.c.score_id,
            )
            .filter(
                CreditScore.risk_score
                >= self.APPROVAL_THRESHOLD,
            )
            .scalar()
            or 0
        )

        return CreditStatsResponse(
            total_applications=total_applications,
            average_score=(
                float(average_score)
                if average_score is not None
                else None
            ),
            average_requested_amount=(
                float(average_requested_amount)
                if average_requested_amount is not None
                else None
            ),
            risk_distribution=risk_distribution,
            validated_clients=validated_clients,
        )

    @staticmethod
    def _to_application_schema(
        application: CreditApplication,
        score: CreditScore | None,
    ) -> CreditApplicationResponse:
        return CreditApplicationResponse(
            application_id=application.application_id,
            account_id=application.client_id,
            requested_amount=application.requested_amount,
            requested_duration_months=application.duration,
            income=application.income,
            expenses=application.expenses,
            risk_score=(
                score.risk_score
                if score
                else None
            ),
            risk_level=(
                RiskLevel(score.risk_level)
                if score and score.risk_level
                else None
            ),
            score_created_at=(
                score.created_at
                if score
                else None
            ),
        )

    @staticmethod
    def _to_schema(
        score: CreditScore,
        application: CreditApplication,
    ) -> CreditScoreRecordSchema:
        return CreditScoreRecordSchema(
            application_id=score.application_id,
            account_id=application.client_id,
            requested_amount=application.requested_amount,
            requested_duration_months=application.duration,
            risk_score=score.risk_score,
            risk_level=(
                RiskLevel(score.risk_level)
                if score.risk_level
                else None
            ),
            created_at=(
                score.created_at
                or datetime.now()
            ),
        )