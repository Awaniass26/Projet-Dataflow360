"""Initialisation non destructive du schéma SQLAlchemy."""

from sqlalchemy import Engine

from api.db.models import Base


def migrate_api_schema(engine: Engine) -> None:
    """Créer les tables manquantes sans supprimer les données existantes."""
    Base.metadata.create_all(bind=engine)
