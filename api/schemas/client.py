"""Schémas de l'API pour les clients."""

from datetime import datetime

from pydantic import BaseModel


class ClientResponse(BaseModel):
    """Informations principales d'un client."""

    client_id: str
    age: int
    sexe: str
    region: str
    account_type: str


class ClientTransactionResponse(BaseModel):
    """Transaction d'un client."""

    transaction_id: str
    amount: float
    type: str
    channel: str
    occurred_at: datetime


class ClientCreditResponse(BaseModel):
    """Demande de crédit d'un client."""

    application_id: str
    requested_amount: float
    duration: int
    income: float
    expenses: float


class ClientDetailResponse(BaseModel):
    """Détail d'un client avec son historique."""

    client_id: str
    age: int
    sexe: str
    region: str
    account_type: str
    transactions: list[ClientTransactionResponse]
    credit_applications: list[ClientCreditResponse]