"""Create API tables and seed them once when the Compose database is empty."""

from sqlalchemy import Engine, create_engine, func, select

from api.core.config import Settings
from api.db.migrations import migrate_api_schema
from api.scripts.seed_users import main as seed_users_main  
from api.db.models import (
    Client,
    CreditApplication,
    CreditScore,
    FraudAlert,
    Transaction,
)

_SEED_TABLES = (
    Client,
    Transaction,
    FraudAlert,
    CreditApplication,
    CreditScore,
)


def _has_existing_data(engine: Engine) -> bool:
    with engine.connect() as connection:
        return any(
            (connection.scalar(select(func.count()).select_from(model)) or 0) > 0
            for model in _SEED_TABLES
        )


def main() -> None:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL n'est pas configurée.")

    engine = create_engine(settings.database_url)
    try:
        migrate_api_schema(engine)
        if _has_existing_data(engine):
            print("Données existantes détectées : génération initiale ignorée.")
        else:
            from api.scripts.generate import generate_dataset, insert_data
            print("Base vide : chargement du jeu de démonstration...")
            insert_data(*generate_dataset())

        # Dans tous les cas : s'assurer qu'un admin existe
        seed_users_main()
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()