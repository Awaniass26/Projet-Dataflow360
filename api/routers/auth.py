"""Routes d'authentification.

Deux modes de création de compte :
  - Via `POST /auth/users` : réservé aux admins, rôle choisi.
  - Via `api.scripts.seed_users` : crée le tout premier admin au démarrage.

Pas d'inscription publique : tout compte est créé par un admin.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.core.security import create_access_token, decode_access_token
from api.dependencies import get_current_admin, get_db, get_settings
from api.repositories.user_repository import (
    PostgresUserRepository,
    UserRepository,
)
from api.schemas.auth import (
    TokenResponse,
    UserCreateByAdmin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentification"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_user_repository(session: Session = Depends(get_db)) -> UserRepository:
    return PostgresUserRepository(session)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Connexion et obtention du JWT",
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    repo: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = repo.authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user.email, settings)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expires_minutes * 60,
        user=repo._to_response(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Profil de l'utilisateur connecté",
)
def me(
    token: str | None = Depends(oauth2_scheme),
    repo: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant.",
        )
    email = decode_access_token(token, settings)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
        )
    user = repo.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )
    return repo._to_response(user)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Crée un utilisateur avec un rôle choisi",
)
def create_user_by_admin(
    payload: UserCreateByAdmin,
    _admin=Depends(get_current_admin),
    repo: UserRepository = Depends(get_user_repository),
) -> UserResponse:
    """Endpoint réservé aux admins pour créer un compte.

    Le compte créé peut avoir le rôle `admin`, `analyst` ou `viewer`.
    """
    user = repo.create(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet email est déjà utilisé.",
        )
    return user