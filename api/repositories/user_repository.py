"""Accès aux utilisateurs."""

from typing import Protocol

from sqlalchemy.orm import Session

from api.core.security import hash_password, verify_password
from api.db.models import User
from api.schemas.auth import UserResponse


class UserRepository(Protocol):
    def create(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "analyst",
    ) -> UserResponse | None:
        ...

    def get_by_email(self, email: str) -> User | None:
        ...

    def authenticate(self, email: str, password: str) -> User | None:
        ...


class PostgresUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "analyst",
    ) -> UserResponse | None:
        """Crée un user. Retourne None si l'email est déjà pris."""
        if self._session.query(User).filter(User.email == email).first():
            return None

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        self._session.add(user)
        self._session.flush()
        return self._to_response(user)

    def get_by_email(self, email: str) -> User | None:
        return (
            self._session.query(User)
            .filter(User.email == email)
            .one_or_none()
        )

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def _to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )