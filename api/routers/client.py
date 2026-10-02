"""Routes de consultation des clients."""

from fastapi import APIRouter, Depends, Query

from api.core.exceptions import ResourceNotFoundError
from api.dependencies import get_client_repository
from api.repositories.client_repository import ClientRepository
from api.schemas.client import ClientDetailResponse, ClientResponse
from api.schemas.common import ERROR_RESPONSES


router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
)


@router.get(
    "",
    response_model=list[ClientResponse],
    responses=ERROR_RESPONSES,
    summary="Liste les clients",
)
def list_clients(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    repository: ClientRepository = Depends(get_client_repository),
) -> list[ClientResponse]:
    """Retourne une liste paginée simplement par limite."""

    return repository.list_clients(limit=limit)


@router.get(
    "/{client_id}",
    response_model=ClientDetailResponse,
    responses=ERROR_RESPONSES,
    summary="Consulte le détail et l'historique d'un client",
)
def get_client(
    client_id: str,
    repository: ClientRepository = Depends(get_client_repository),
) -> ClientDetailResponse:
    """Retourne les informations et l'historique d'un client."""

    client = repository.get_client(client_id)

    if client is None:
        raise ResourceNotFoundError(
            f"Aucun client trouvé pour '{client_id}'."
        )

    return client