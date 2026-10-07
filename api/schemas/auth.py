"""Schémas d'authentification."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=120)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: Literal["admin", "analyst", "viewer"]
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserCreateByAdmin(BaseModel):
    """Création d'un utilisateur par un admin, avec rôle choisi."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=120)
    role: Literal["admin", "analyst", "viewer"] = "analyst"