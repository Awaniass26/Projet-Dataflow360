"""Routes de consultation des clients."""

from fastapi import APIRouter, Depends, Query

from api.core.exceptions import ResourceNotFoundError
from api.dependencies import get_client_repository
from api.repositories.client_repository import ClientRepository
from api.schemas.client import ClientDetailResponse, ClientResponse,ClientListResponse
from api.schemas.common import ERROR_RESPONSES
from math import ceil


router = APIRouter(
    prefix="/clients",
    tags=["Clients"],
)


@router.get(
    "",
    response_model=ClientListResponse,
    responses=ERROR_RESPONSES,
    summary="Liste paginée des clients",
)
def list_clients(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    repository: ClientRepository = Depends(get_client_repository),
) -> ClientListResponse:
    """Retourne une page de clients."""

    clients, total = repository.list_clients(
        page=page,
        page_size=page_size,
    )

    total_pages = ceil(total / page_size) if total else 0

    return ClientListResponse(
        items=clients,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


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