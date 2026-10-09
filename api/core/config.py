"""Configuration de l'application, lue depuis les variables d'environnement.

Les valeurs se définissent dans le fichier `.env` placé à la racine du dépôt
(voir `.env.example`). Aucune valeur secrète ne doit figurer dans ce fichier.
"""

from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du dépôt : api/core/config.py -> api/core -> api -> racine.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Paramètres de l'API.

    Une variable d'environnement vide (ex. `DATABASE_URL=`) est considérée comme
    non définie : la fonctionnalité correspondante est alors "non configurée".
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "DataFlow360 API"
    app_version: str = "0.1.0"
    app_description: str = (
        "API de démonstration DataFlow360 (mobile money, Sénégal) : "
        "détection de transactions potentiellement frauduleuses et scoring du "
        "risque de défaut de crédit. Les résultats sont des aides à la décision, "
        "jamais des décisions automatiques. Projet académique : les données "
        "utilisées sont synthétiques ou publiques."
    )
    environment: Literal["development", "test", "production"] = "development"

    # --- Authentification JWT ---
    jwt_secret: str = "change-me-in-production-please-use-a-real-secret"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24  # 24h

    # --- CORS : liste d'origines séparées par des virgules ---
    cors_allowed_origins: str = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "https://localhost:3000,"
    "http://127.0.0.1:3000"
    "http://localhost:8050,"
    "http://127.0.0.1:8050"
)

    # --- Mode simulation (désactivé par défaut, interdit en production) ---
    simulation_enabled: bool = False

    # --- PostgreSQL ---
    database_url: str | None = None

    # --- Modèles ML : à renseigner dans .env quand le membre ML les livre ---
    fraud_model_path: str | None = None
    fraud_model_version: str | None = None
    fraud_decision_threshold: float | None = Field(default=None, ge=0, le=1)
    credit_model_path: str | None = None
    credit_model_version: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        """Origines autorisées, nettoyées."""
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def _forbid_simulation_in_production(self) -> Self:
        if self.environment == "production" and self.simulation_enabled:
            raise ValueError(
                "SIMULATION_ENABLED ne peut pas être activé en production."
            )
        return self
