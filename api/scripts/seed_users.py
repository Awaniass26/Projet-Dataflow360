"""Crée les comptes par défaut (admin + service Kafka) automatiquement.

Idempotent :
- migre les emails legacy (.local → .com)
- réactive l'admin s'il est inactif
- crée l'admin s'il n'existe pas
- crée le compte service (consumer Kafka) s'il n'existe pas
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.security import hash_password
from api.db.models import User
from api.db.session import _get_engine


ADMIN_EMAIL = "admin@dataflow360.com"
ADMIN_PASSWORD = "admin1234"
LEGACY_EMAILS = ["admin@dataflow360.local"]

SERVICE_EMAIL = "service-consumer@dataflow360.com"
SERVICE_PASSWORD = "service-consumer-2026"


def _ensure_user(
    session: Session,
    email: str,
    password: str,
    full_name: str,
    role: str,
) -> None:
    """Crée l'utilisateur s'il n'existe pas, ou le réactive."""
    existing = session.scalars(
        select(User).where(User.email == email)
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            session.commit()
            print(f"✅ {email} réactivé")
        else:
            print(f"✅ {email} existe déjà, rien à faire.")
        return

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    print(f"✅ Créé : {email} ({role})")


def main() -> None:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL n'est pas configurée.")

    engine = _get_engine(settings.database_url)

    with Session(engine) as session:
        # 1. Migrer les emails legacy
        for legacy in LEGACY_EMAILS:
            user = session.scalars(
                select(User).where(User.email == legacy)
            ).first()
            if user:
                user.email = ADMIN_EMAIL
                session.commit()
                print(f"✅ Email migré : {legacy} → {ADMIN_EMAIL}")

        # 2. Créer/réactiver l'admin
        _ensure_user(
            session,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            full_name="Administrateur",
            role="admin",
        )

        # 3. Créer/réactiver le compte service (Kafka consumer)
        _ensure_user(
            session,
            email=SERVICE_EMAIL,
            password=SERVICE_PASSWORD,
            full_name="Service Consumer (Kafka)",
            role="analyst",
        )


if __name__ == "__main__":
    main()