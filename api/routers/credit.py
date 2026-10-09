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
    CreditApplicationAutoInput,
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
        eligible=result.eligible,
        status=result.status,
        is_simulation=result.is_simulation,
        message=result.message,
        explanation_factors=None,
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



@router.post(
    "/score/auto",
    response_model=CreditScoreResponse,
    responses=ERROR_RESPONSES,
    summary="Évalue une demande de crédit en calculant les features automatiquement",
)
def score_credit_auto(
    application: CreditApplicationAutoInput,
    service: CreditScoringService = Depends(get_credit_service),
    repository: CreditScoreRepository = Depends(get_credit_score_repository),
) -> CreditScoreResponse:
    """Évalue une demande de crédit.

    Le backend calcule les 10 features manquantes depuis l'historique
    du client (transactions, crédits précédents), puis appelle le modèle ML.

    L'analyste ne saisit que :
    - account_id
    - montant_credit_demande
    - duree_credit_demande
    - type_activite
    """
    import time

    # 1. Calcul des features depuis l'historique
    features = repository.compute_features_from_history(
        client_id=application.account_id,
        montant_credit_demande=application.montant_credit_demande,
        duree_credit_demande=application.duree_credit_demande,
        type_activite=application.type_activite,
    )

    if features is None:
        raise ResourceNotFoundError(
            f"Aucun client trouvé pour '{application.account_id}'."
        )

    # 2. Application_id auto si non fourni
    application_id = application.application_id or f"AUTO-{int(time.time())}"

    # 3. Appel du modèle avec les features calculées
    result = service.score_from_features_dict(features)

    return CreditScoreResponse(
        application_id=application_id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        eligible=result.eligible,
        status=result.status,
        is_simulation=result.is_simulation,
        message=result.message,
        explanation_factors=None,
    )