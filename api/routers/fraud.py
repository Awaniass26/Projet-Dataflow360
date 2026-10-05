"""Routes de détection de fraude."""

from fastapi import APIRouter, Depends, Query
from math import ceil


from api.core.exceptions import DatabaseNotConfiguredError, ResourceNotFoundError
from api.dependencies import (
    get_fraud_alert_repository,
    get_fraud_service,
    get_optional_fraud_alert_repository,
)
from api.repositories.fraud_repository import FraudAlertRepository
from api.schemas.common import ERROR_RESPONSES, RiskLevel, FraudAlertStatus
from api.schemas.fraud import (
    FraudAlertListResponse,
    FraudAlertResponse,
    FraudAlertUpdate,
    FraudPredictionResponse,
    FraudStatsResponse,
    TransactionInput,
)
from api.services.fraud_service import FraudDetectionService

router = APIRouter(prefix="/fraud", tags=["Détection de fraude"])


@router.post(
    "/predict",
    response_model=FraudPredictionResponse,
    responses=ERROR_RESPONSES,
    summary="Évalue le risque de fraude d'une transaction",
)
def predict_fraud(
    transaction: TransactionInput,
    service: FraudDetectionService = Depends(get_fraud_service),
    repository: FraudAlertRepository | None = Depends(
        get_optional_fraud_alert_repository
    ),
) -> FraudPredictionResponse:
    """Calcule un score de risque pour une transaction.

    Ce résultat est une AIDE À LA DÉCISION : l'API ne bloque et ne valide
    jamais une transaction elle-même.
    """
    result = service.predict(transaction)
    if result.risk_level == RiskLevel.HIGH and not result.is_simulation:
        if repository is None:
            raise DatabaseNotConfiguredError(
                "PostgreSQL est nécessaire pour persister une alerte réelle."
            )
        repository.save_transaction_and_alert(
            transaction=transaction,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
        )
    return FraudPredictionResponse(
        transaction_id=transaction.transaction_id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        status=result.status,
        is_simulation=result.is_simulation,
        message=result.message,
    )


@router.get(
    "/alerts",
    response_model=FraudAlertListResponse,
    responses=ERROR_RESPONSES,
    summary="Liste paginée des alertes de fraude",
)
def list_fraud_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    risk_level: RiskLevel | None = Query(default=None),
    status: FraudAlertStatus | None = Query(default=None),
    repository: FraudAlertRepository = Depends(
        get_fraud_alert_repository
    ),
) -> FraudAlertListResponse:
    """Liste les alertes avec pagination et filtre par niveau de risque."""

    alerts, total = repository.list_alerts(
        page=page,
        page_size=page_size,
        risk_level=risk_level,
        status=status,
    )

    total_pages = ceil(total / page_size) if total else 0

    return FraudAlertListResponse(
        items=alerts,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get(
    "/alerts/{alert_id}",
    response_model=FraudAlertResponse,
    responses=ERROR_RESPONSES,
    summary="Consulte une alerte de fraude",
)
def get_fraud_alert(
    alert_id: int,
    repository: FraudAlertRepository = Depends(get_fraud_alert_repository),
) -> FraudAlertResponse:
    alert = repository.get_alert(alert_id)
    if alert is None:
        raise ResourceNotFoundError(f"Aucune alerte trouvée pour '{alert_id}'.")
    return alert


@router.patch(
    "/alerts/{alert_id}",
    response_model=FraudAlertResponse,
    responses=ERROR_RESPONSES,
    summary="Traite une alerte de fraude",
)
def update_fraud_alert(
    alert_id: int,
    update: FraudAlertUpdate,
    repository: FraudAlertRepository = Depends(get_fraud_alert_repository),
) -> FraudAlertResponse:
    """Met à jour le statut et le suivi d'une alerte de fraude."""

    alert = repository.update_alert(
        alert_id=alert_id,
        status=update.status,
        reviewed_by=update.reviewed_by,
        explanation=update.explanation,
    )

    if alert is None:
        raise ResourceNotFoundError(
            f"Aucune alerte trouvée pour '{alert_id}'."
        )

    return alert

@router.get(
    "/stats",
    response_model=FraudStatsResponse,
    responses=ERROR_RESPONSES,
    summary="Retourne les KPI fraude calculés depuis PostgreSQL",
)
def get_fraud_stats(
    repository: FraudAlertRepository = Depends(get_fraud_alert_repository),
) -> FraudStatsResponse:
    return repository.get_stats()
