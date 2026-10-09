"""Schémas de la fonctionnalité credit scoring.

Le schéma d'entrée `CreditApplicationInput` est PROVISOIRE : les variables
définitives seront confirmées avec le membre ML une fois le Feature
Engineering figé (voir `api/services/ml_contracts.py`).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from api.schemas.common import ProcessingStatus, RiskLevel


class CreditApplicationInput(BaseModel):
    """Données nécessaires au modèle réel de scoring de crédit."""

    application_id: str = Field(
        ...,
        min_length=1,
        examples=["credit_app_0001"],
    )
    account_id: str = Field(..., min_length=1)

    # Variables du modèle ML
    age: int = Field(..., ge=18)
    anciennete_compte_mois: int = Field(..., ge=0)
    nb_transactions_90j: int = Field(..., ge=0)
    montant_entrees_90j: float = Field(..., ge=0)
    montant_sorties_90j: float = Field(..., ge=0)
    solde_moyen_90j: float = Field(..., ge=0)
    regularite_revenus: float = Field(..., ge=0)
    nombre_credits_precedents: int = Field(..., ge=0)
    taux_remboursement: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )
    nombre_credits_en_retard: int = Field(..., ge=0)
    nombre_credits_impayes: int = Field(..., ge=0)
    montant_credit_demande: float = Field(..., gt=0)
    duree_credit_demande: int = Field(..., gt=0)
    stabilite_flux: float = Field(..., ge=0)

    type_activite: str = Field(
        ...,
        min_length=1,
        examples=["commerce"],
    )


class CreditScoreResponse(BaseModel):
    """Réponse de `POST /credit/score`.

    Ceci est une AIDE À LA DÉCISION : l'octroi ou le refus du crédit reste
    une décision métier, jamais automatisée par cette réponse.
    """

    application_id: str
    risk_score: float | None = Field(default=None, description="Score entre 0 et 1, si disponible.")
    eligible: bool | None = Field(
    default=None,
    description="True si le score atteint le seuil d'approbation de 90 %.",
)
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
    validated_clients: int


class CreditApplicationAutoInput(BaseModel):
    """Entrée simplifiée pour `POST /credit/score/auto`.

    Le backend calcule automatiquement 10 des 15 features
    à partir de l'historique du client.
    """

    application_id: str | None = Field(
        default=None,
        description="Si absent, généré automatiquement (AUTO-{timestamp}).",
    )
    account_id: str = Field(..., min_length=1, examples=["CLI-000001"])
    montant_credit_demande: float = Field(..., gt=0)
    duree_credit_demande: int = Field(..., gt=0)
    type_activite: str = Field(
        ...,
        min_length=1,
        examples=["commerce", "agriculture", "transport", "services"],
    )