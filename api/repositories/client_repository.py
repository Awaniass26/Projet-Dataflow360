"""Accès aux données des clients."""

from typing import Protocol

from sqlalchemy.orm import Session

from api.db.models import Client
from api.schemas.client import (
    ClientDetailResponse,
    ClientResponse,
    ClientTransactionResponse,
    ClientCreditResponse,
)


class ClientRepository(Protocol):
    """Contrat d'accès aux clients."""

    def list_clients(self, limit: int = 50) -> list[ClientResponse]:
        ...

    def get_client(
        self,
        client_id: str,
    ) -> ClientDetailResponse | None:
        ...


class PostgresClientRepository:
    """Implémentation PostgreSQL du repository client."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_clients(
        self,
        limit: int = 50,
    ) -> list[ClientResponse]:
        clients = (
            self._session.query(Client)
            .order_by(Client.client_id)
            .limit(limit)
            .all()
        )

        return [
            ClientResponse(
                client_id=client.client_id,
                age=client.age,
                sexe=client.sexe,
                region=client.region,
                account_type=client.account_type,
            )
            for client in clients
        ]

    def get_client(
        self,
        client_id: str,
    ) -> ClientDetailResponse | None:
        client = self._session.get(Client, client_id)

        if client is None:
            return None

        transactions = [
            ClientTransactionResponse(
                transaction_id=transaction.transaction_id,
                amount=transaction.amount,
                type=transaction.type,
                channel=transaction.channel,
                occurred_at=transaction.occurred_at,
            )
            for transaction in client.transactions
        ]

        credit_applications = [
            ClientCreditResponse(
                application_id=application.application_id,
                requested_amount=application.requested_amount,
                duration=application.duration,
                income=application.income,
                expenses=application.expenses,
            )
            for application in client.credit_applications
        ]

        return ClientDetailResponse(
            client_id=client.client_id,
            age=client.age,
            sexe=client.sexe,
            region=client.region,
            account_type=client.account_type,
            transactions=transactions,
            credit_applications=credit_applications,
        )