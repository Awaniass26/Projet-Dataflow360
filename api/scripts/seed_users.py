"""Crée l'admin par défaut, ou corrige les emails legacy automatiquement."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.security import hash_password
from api.db.models import User
from api.db.session import _get_engine


ADMIN_EMAIL = "admin@dataflow360.com"
ADMIN_PASSWORD = "admin1234"
LEGACY_EMAILS = ["admin@dataflow360.local"]


def main() -> None:
    settings = Settings()
    engine = _get_engine(settings.database_url)

    with Session(engine) as session:
        # 1. Migrer les emails legacy vers l'email canonique
        for legacy in LEGACY_EMAILS:
            user = session.scalars(
                select(User).where(User.email == legacy)
            ).first()
            if user:
                user.email = ADMIN_EMAIL
                session.commit()
                print(f"✅ Email migré : {legacy} → {ADMIN_EMAIL}")

        # 2. S'assurer que l'admin existe et est actif
        existing = session.scalars(
            select(User).where(User.email == ADMIN_EMAIL)
        ).first()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                session.commit()
                print(f"✅ {ADMIN_EMAIL} réactivé")
            else:
                print(f"✅ {ADMIN_EMAIL} existe déjà, rien à faire.")
            return

        # 3. Créer l'admin s'il n'existe pas
        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name="Administrateur",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        print(f"✅ Admin créé : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    main()