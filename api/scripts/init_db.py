"""Create the API tables in the configured database for local Compose runs."""

from sqlalchemy import create_engine

from api.core.config import Settings
from api.db.models import Base


def main() -> None:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL n'est pas configurée.")

    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    engine.dispose()


if __name__ == "__main__":
    main()