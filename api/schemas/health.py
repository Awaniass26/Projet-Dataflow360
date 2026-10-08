"""Schémas des routes générales."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WelcomeResponse(BaseModel):
    message: str
    version: str
    docs_url: str


class ConfigurationStatus(BaseModel):
    """Indique si chaque dépendance est CONFIGURÉE.

    "Configurée" ne veut pas dire "joignable" ni "valide" : aucun appel réseau
    n'est fait par /health.
    """

    database_configured: bool
    fraud_model_configured: bool
    credit_model_configured: bool
    simulation_enabled: bool


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(description="Heure du serveur (UTC).")
    configuration: ConfigurationStatus
