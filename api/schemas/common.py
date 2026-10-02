"""Schémas et énumérations partagés."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class RiskLevel(StrEnum):
    """Niveaux de risque.

    PROVISOIRE : les seuils qui définissent ces niveaux doivent être arrêtés
    par l'équipe ML (voir `api/services/ml_contracts.py`).
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ProcessingStatus(StrEnum):
    """Statut du traitement d'une demande."""

    COMPLETED = "completed"  # résultat produit par un vrai modèle
    SIMULATED = "simulated"  # réponse de simulation (aucune prédiction réelle)


class ErrorDetail(BaseModel):
    """Contenu d'une erreur."""

    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    """Format commun de toutes les erreurs de l'API."""

    error: ErrorDetail


# Réponses d'erreur communes, pour la documentation OpenAPI (/docs).
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": "Requête invalide."},
    503: {
        "model": ErrorResponse,
        "description": "Dépendance non configurée ou indisponible "
        "(modèle ML ou PostgreSQL).",
    },
}
