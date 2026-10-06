"""Fournisseurs de dépendances FastAPI (injection de dépendances).

Centraliser ces fonctions ici permet de les remplacer facilement dans les
tests (`app.dependency_overrides`), sans toucher aux routes.
"""

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends,HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer


from api.core.config import Settings
from api.core.security import decode_access_token
from api.db.session import get_db_session
from api.db.models import User
from api.repositories.credit_repository import CreditScoreRepository, PostgresCreditScoreRepository
from api.repositories.fraud_repository import FraudAlertRepository, PostgresFraudAlertRepository
from api.services.credit_service import CreditScoringService
from api.services.fraud_service import FraudDetectionService
from api.repositories.client_repository import (
    ClientRepository,
    PostgresClientRepository,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Paramètres de l'application (mis en cache : lus une seule fois)."""
    return Settings()


def get_fraud_service(settings: Settings = Depends(get_settings)) -> FraudDetectionService:
    return FraudDetectionService(settings)


def get_credit_service(settings: Settings = Depends(get_settings)) -> CreditScoringService:
    return CreditScoringService(settings)


def get_db(settings: Settings = Depends(get_settings)) -> Generator[Session, None, None]:
    """Session PostgreSQL pour la durée d'une requête.

    Lève `DatabaseNotConfiguredError` (503) si `DATABASE_URL` est absent,
    avant toute tentative de connexion.
    """
    yield from get_db_session(settings)


def get_fraud_alert_repository(session: Session = Depends(get_db)) -> FraudAlertRepository:
    return PostgresFraudAlertRepository(session)


def get_optional_db(
    settings: Settings = Depends(get_settings),
) -> Generator[Session | None, None, None]:
    """Session optionnelle pour les prédictions simulées sans PostgreSQL."""
    if not settings.database_url:
        yield None
        return
    yield from get_db_session(settings)


def get_optional_fraud_alert_repository(
    session: Session | None = Depends(get_optional_db),
) -> FraudAlertRepository | None:
    if session is None:
        return None
    return PostgresFraudAlertRepository(session)


def get_credit_score_repository(session: Session = Depends(get_db)) -> CreditScoreRepository:
    return PostgresCreditScoreRepository(session)


def get_optional_credit_score_repository(
    session: Session | None = Depends(get_optional_db),
) -> CreditScoreRepository | None:
    if session is None:
        return None
    return PostgresCreditScoreRepository(session)


def get_client_repository(
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_db),
) -> ClientRepository:
    """Fournit le repository PostgreSQL des clients."""

    return PostgresClientRepository(session)


def get_current_user_email(
    token: str | None = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    """Renvoie l'email de l'utilisateur connecté, ou lève 401."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = decode_access_token(token, settings)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
        )
    return email

def get_current_user(
    email: str = Depends(get_current_user_email),
    session: Session = Depends(get_db),
) -> User:
    """Renvoie l'utilisateur connecté (objet User complet)."""
    from api.repositories.user_repository import PostgresUserRepository
    repo = PostgresUserRepository(session)
    user = repo.get_by_email(email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable ou inactif.",
        )
    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """Renvoie l'utilisateur connecté s'il est admin, sinon 403."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    return user