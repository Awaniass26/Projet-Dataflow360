"""Sécurité : hash de mot de passe + JWT."""

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from api.core.config import Settings


def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt (tronqué à 72 bytes si nécessaire)."""
    # bcrypt limite à 72 bytes : on tronque pour éviter le ValueError
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash bcrypt."""
    try:
        plain_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(plain_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    settings: Settings,
    expires_minutes: int | None = None,
) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.jwt_expires_minutes
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str, settings: Settings) -> str | None:
    """Renvoie le `sub` (email) si valide, sinon None."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None