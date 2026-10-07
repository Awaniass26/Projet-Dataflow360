"""Connexion PostgreSQL (SQLAlchemy). Le moteur n'est créé QUE si
`DATABASE_URL` est configuré, et seulement au premier appel (pas au démarrage
de l'API) : une base non configurée ou injoignable ne doit jamais empêcher
l'API de démarrer."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.core.config import Settings
from api.core.exceptions import DatabaseNotConfiguredError


@lru_cache(maxsize=1)
def _get_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def get_session_factory(settings: Settings) -> sessionmaker[Session]:
    """Raises DatabaseNotConfiguredError si `settings.database_url` est vide."""
    if not settings.database_url:
        raise DatabaseNotConfiguredError()
    engine = _get_engine(settings.database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session(settings: Settings) -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session PostgreSQL le temps d'une requête."""
    session_factory = get_session_factory(settings)  # lève l'erreur si non configuré
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
