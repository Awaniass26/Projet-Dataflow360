"""Point d'entrée de l'API DataFlow360.

Lancement (depuis la racine du dépôt) :
    python -m uvicorn api.main:app --reload
"""

from datetime import UTC, datetime

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import Settings
from api.core.error_handlers import register_exception_handlers
from api.dependencies import get_settings
from api.routers import credit, fraud, client
from api.schemas.health import ConfigurationStatus, HealthResponse, WelcomeResponse

# Utilisée uniquement pour les réglages fixés au démarrage du processus
# (titre, CORS...). Les routes, elles, reçoivent `Settings` via `Depends`
# pour rester surchargeables dans les tests (`app.dependency_overrides`).
_startup_settings = get_settings()

app = FastAPI(
    title=_startup_settings.app_name,
    description=_startup_settings.app_description,
    version=_startup_settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_startup_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(fraud.router)
app.include_router(credit.router)
app.include_router(client.router)


@app.get("/", response_model=WelcomeResponse, tags=["Général"], summary="Route de bienvenue")
def read_root(settings: Settings = Depends(get_settings)) -> WelcomeResponse:
    return WelcomeResponse(
        message=f"Bienvenue sur {settings.app_name}.",
        version=settings.app_version,
        docs_url="/docs",
    )


@app.get("/health", response_model=HealthResponse, tags=["Général"], summary="Vérifie l'état de l'API")
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Indique quelles dépendances sont CONFIGURÉES (pas nécessairement joignables).

    Aucun appel réseau n'est fait ici : /health reste rapide même si
    PostgreSQL est indisponible.
    """
    return HealthResponse(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        configuration=ConfigurationStatus(
            database_configured=bool(settings.database_url),
            fraud_model_configured=bool(settings.fraud_model_path),
            credit_model_configured=bool(settings.credit_model_path),
            simulation_enabled=settings.simulation_enabled,
        ),
    )
