"""Schémas de la fonctionnalité fraude.

Le schéma d'entrée `TransactionInput` est PROVISOIRE : il correspond aux
données transactionnelles synthétiques prévues pour le projet, mais les
features définitives du modèle doivent être confirmées avec le membre ML
(voir `api/services/ml_contracts.py`).
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from api.schemas.common import ProcessingStatus, RiskLevel


class TransactionType(StrEnum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"


class TransactionChannel(StrEnum):
    MOBILE_APP = "mobile_app"
    USSD = "ussd"
    AGENT = "agent"


class TransactionInput(BaseModel):
    """Données d'une transaction Mobile Money à analyser.

    PROVISOIRE : les noms, types et la liste des champs seront ajustés une
    fois le Feature Engineering figé par l'équipe Data.
    """

    transaction_id: str = Field(..., min_length=1, examples=["txn_0001"])
    amount: float = Field(..., gt=0, description="Montant de la transaction (FCFA).")
    transaction_type: TransactionType
    channel: TransactionChannel
    occurred_at: datetime = Field(..., description="Horodatage de la transaction.")
    sender_account_id: str = Field(..., min_length=1)
    recipient_account_id: str = Field(..., min_length=1)

    # Features attendues par `models/modele_fraude_final.pkl`.
    hour: int = Field(..., ge=0, le=23)
    ecart_montant_moyen: float
    ecart_heure_habituelle: float
    nouvel_appareil: bool
    nouveau_destinataire: bool


class FraudPredictionResponse(BaseModel):
    """Réponse de `POST /fraud/predict`.

    Ceci est une AIDE À LA DÉCISION. Aucune décision de blocage n'est prise
    automatiquement par l'API : la politique métier et les personnes
    autorisées restent responsables de l'action à mener.
    """

    transaction_id: str
    risk_score: float | None = Field(
        default=None, description="Score de risque entre 0 et 1, si disponible."
    )
    risk_level: RiskLevel | None = Field(
        default=None, description="Niveau de risque, si un seuil est configuré."
    )
    status: ProcessingStatus
    is_simulation: bool = Field(
        description="True si ce résultat est une simulation et non une vraie prédiction."
    )
    message: str


class FraudAlertResponse(BaseModel):
    """Une alerte de fraude persistée.

    LIMITE ACTUELLE : tant que `DATABASE_URL` n'est pas configuré, la route
    `GET /fraud/alerts` renvoie une erreur explicite plutôt qu'une liste
    vide ou inventée (voir `api/routers/fraud.py`).
    """

    alert_id: int
    transaction_id: str
    risk_score: float
    risk_level: RiskLevel
    created_at: datetime


class FraudAlertEvolutionPoint(BaseModel):
    """Agrégat quotidien des alertes persistées."""

    date: date
    alert_count: int
    suspicious_amount: float


class FraudStatsResponse(BaseModel):
    """KPI fraude calculés depuis les transactions et alertes PostgreSQL."""

    total_transactions: int
    total_alerts: int
    suspicious_rate: float = Field(
        description=(
            "Taux de transactions suspectes, entre 0 et 1; ce n'est pas un "
            "taux de fraude confirmée."
        )
    )
    suspicious_amount: float
    alerts_by_risk_level: dict[str, int]
    alerts_evolution: list[FraudAlertEvolutionPoint]
