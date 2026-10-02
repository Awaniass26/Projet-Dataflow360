"""Schémas de la fonctionnalité credit scoring.

Le schéma d'entrée `CreditApplicationInput` est PROVISOIRE : les variables
définitives seront confirmées avec le membre ML une fois le Feature
Engineering figé (voir `api/services/ml_contracts.py`).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from api.schemas.common import ProcessingStatus, RiskLevel


class CreditApplicationInput(BaseModel):
    """Données d'une demande de micro-crédit à évaluer. PROVISOIRE."""

    application_id: str = Field(..., min_length=1, examples=["credit_app_0001"])
    account_id: str = Field(..., min_length=1)
    requested_amount: float = Field(..., gt=0, description="Montant demandé (FCFA).")
    requested_duration_months: int = Field(..., gt=0)

    estimated_monthly_income: float | None = Field(default=None, ge=0)
    estimated_monthly_expenses: float | None = Field(default=None, ge=0)
    monthly_transaction_volume: float | None = Field(default=None, ge=0)
    monthly_transaction_frequency: int | None = Field(default=None, ge=0)
    repayment_history_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Indicateur agrégé d'historique de remboursement (0 à 1).",
    )


class CreditScoreResponse(BaseModel):
    """Réponse de `POST /credit/score`.

    Ceci est une AIDE À LA DÉCISION : l'octroi ou le refus du crédit reste
    une décision métier, jamais automatisée par cette réponse.
    """

    application_id: str
    risk_score: float | None = Field(default=None, description="Score entre 0 et 1, si disponible.")
    risk_level: RiskLevel | None = Field(
        default=None,
        description="Catégorie de risque, uniquement si l'équipe ML en définit une.",
    )
    status: ProcessingStatus
    is_simulation: bool
    message: str
    explanation_factors: list[str] | None = Field(
        default=None,
        description="Facteurs explicatifs, uniquement si une méthode "
        "explicative réelle (ex. SHAP) les fournit. Jamais inventés.",
    )


class CreditScoreRecord(BaseModel):
    """Un résultat de scoring persisté, consultable par identifiant.

    LIMITE ACTUELLE : tant que `DATABASE_URL` n'est pas configuré, la route
    `GET /credit/score/{application_id}` renvoie une erreur explicite.
    """

    application_id: str
    account_id: str
    requested_amount: float
    requested_duration_months: int
    risk_score: float
    risk_level: RiskLevel | None
    created_at: datetime


class CreditApplicationResponse(BaseModel):
    """Demande de crédit stockée, avec son score s'il existe."""

    application_id: str
    account_id: str
    requested_amount: float
    requested_duration_months: int
    income: float
    expenses: float
    risk_score: float | None
    risk_level: RiskLevel | None
    score_created_at: datetime | None


class CreditStatsResponse(BaseModel):
    """KPI crédit calculés depuis les demandes et scores PostgreSQL."""

    total_applications: int
    average_score: float | None
    average_requested_amount: float | None
    risk_distribution: dict[str, int]
