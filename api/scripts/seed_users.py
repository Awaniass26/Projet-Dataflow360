"""Crée un admin par défaut si la table api_users est vide."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.security import hash_password
from api.db.models import User
from api.db.session import _get_engine


def main() -> None:
    settings = Settings()
    engine = _get_engine(settings.database_url)

    with Session(engine) as session:
        count = session.scalar(select(func.count()).select_from(User)) or 0
        if count > 0:
            print(f"{count} utilisateur(s) déjà présent(s), rien à faire.")
            return

        admin = User(
            email="admin@dataflow360.com",
            hashed_password=hash_password("admin1234"),
            full_name="Administrateur",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        print("Admin créé : admin@dataflow360.com / admin1234")


if __name__ == "__main__":
    main()