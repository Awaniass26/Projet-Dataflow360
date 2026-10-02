"""Routes de détection de fraude."""

from fastapi import APIRouter, Depends, Query

from api.core.exceptions import DatabaseNotConfiguredError, ResourceNotFoundError
from api.dependencies import (
    get_fraud_alert_repository,
    get_fraud_service,
    get_optional_fraud_alert_repository,
)
from api.repositories.fraud_repository import FraudAlertRepository
from api.schemas.common import ERROR_RESPONSES, RiskLevel
from api.schemas.fraud import (
    FraudAlertResponse,
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
    response_model=list[FraudAlertResponse],
    responses=ERROR_RESPONSES,
    summary="Liste les alertes de fraude enregistrées",
)
def list_fraud_alerts(
    limit: int = Query(default=50, ge=1, le=100),
    repository: FraudAlertRepository = Depends(get_fraud_alert_repository),
) -> list[FraudAlertResponse]:
    """LIMITE ACTUELLE : si `DATABASE_URL` n'est pas configuré, cette route
    renvoie une erreur 503 explicite plutôt qu'une liste vide ou simulée."""
    return repository.list_alerts(limit=limit)


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
