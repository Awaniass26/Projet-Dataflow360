"""Routes de scoring de crédit."""

from fastapi import APIRouter, Depends, Query

from api.core.exceptions import DatabaseNotConfiguredError, ResourceNotFoundError
from api.dependencies import (
    get_credit_score_repository,
    get_credit_service,
    get_optional_credit_score_repository,
)
from api.repositories.credit_repository import CreditScoreRepository
from api.schemas.common import ERROR_RESPONSES
from api.schemas.credit import (
    CreditApplicationInput,
    CreditApplicationResponse,
    CreditScoreRecord,
    CreditScoreResponse,
    CreditStatsResponse,
)
from api.services.credit_service import CreditScoringService

router = APIRouter(prefix="/credit", tags=["Scoring de crédit"])


@router.post(
    "/score",
    response_model=CreditScoreResponse,
    responses=ERROR_RESPONSES,
    summary="Évalue le risque de crédit d'une demande",
)
def score_credit_application(
    application: CreditApplicationInput,
    service: CreditScoringService = Depends(get_credit_service),
    repository: CreditScoreRepository | None = Depends(
        get_optional_credit_score_repository
    ),
) -> CreditScoreResponse:
    """Ce résultat est une AIDE À LA DÉCISION : l'octroi ou le refus du
    crédit reste une décision métier, jamais automatisée par cette réponse."""
    result = service.score(application)
    if not result.is_simulation:
        if repository is None:
            raise DatabaseNotConfiguredError(
                "PostgreSQL est nécessaire pour persister un score réel."
            )
        if repository.save_score(
            application_id=application.application_id,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
        ) is None:
            raise ResourceNotFoundError(
                f"Aucune demande de crédit trouvée pour '{application.application_id}'."
            )
    return CreditScoreResponse(
        application_id=application.application_id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        status=result.status,
        is_simulation=result.is_simulation,
        message=result.message,
        explanation_factors=None,  # jamais inventé : voir services/credit_service.py
    )


@router.get(
    "/score/{application_id}",
    response_model=CreditScoreRecord,
    responses=ERROR_RESPONSES,
    summary="Consulte un résultat de scoring déjà calculé",
)
def get_credit_score(
    application_id: str,
    repository: CreditScoreRepository = Depends(get_credit_score_repository),
) -> CreditScoreRecord:
    """LIMITE ACTUELLE : si `DATABASE_URL` n'est pas configuré, cette route
    renvoie une erreur 503 explicite (voir `api/db/session.py`)."""
    record = repository.get_score(application_id)
    if record is None:
        raise ResourceNotFoundError(f"Aucun résultat de scoring pour '{application_id}'.")
    return record


@router.get(
    "/applications",
    response_model=list[CreditApplicationResponse],
    responses=ERROR_RESPONSES,
    summary="Liste les demandes de crédit",
)
def list_credit_applications(
    limit: int = Query(default=50, ge=1, le=100),
    repository: CreditScoreRepository = Depends(get_credit_score_repository),
) -> list[CreditApplicationResponse]:
    return repository.list_applications(limit=limit)


@router.get(
    "/applications/{application_id}",
    response_model=CreditApplicationResponse,
    responses=ERROR_RESPONSES,
    summary="Consulte une demande de crédit",
)
def get_credit_application(
    application_id: str,
    repository: CreditScoreRepository = Depends(get_credit_score_repository),
) -> CreditApplicationResponse:
    application = repository.get_application(application_id)
    if application is None:
        raise ResourceNotFoundError(f"Aucune demande trouvée pour '{application_id}'.")
    return application


@router.get(
    "/stats",
    response_model=CreditStatsResponse,
    responses=ERROR_RESPONSES,
    summary="Retourne les KPI crédit calculés depuis PostgreSQL",
)
def get_credit_stats(
    repository: CreditScoreRepository = Depends(get_credit_score_repository),
) -> CreditStatsResponse:
    return repository.get_stats()
