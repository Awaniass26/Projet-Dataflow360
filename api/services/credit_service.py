"""Service de scoring du risque de crédit. Voir fraud_service.py pour le
détail des étapes d'intégration du modèle réel (CREDIT_MODEL_PATH / CREDIT_MODEL_VERSION)."""

from dataclasses import dataclass

from api.core.config import Settings
from api.core.exceptions import ModelNotConfiguredError, ModelPredictionError
from api.schemas.common import ProcessingStatus, RiskLevel
from api.schemas.credit import CreditApplicationInput
from api.services.ml_contracts import CREDIT_MODEL_CONTRACT, ModelContract
from api.services.model_loader import load_model


@dataclass
class CreditScoringResult:
    risk_score: float | None
    risk_level: RiskLevel | None
    status: ProcessingStatus
    is_simulation: bool
    message: str


class CreditScoringService:
    """Un score est une AIDE À LA DÉCISION : ce service ne décide jamais
    d'accorder ou de refuser un crédit."""

    def __init__(self, settings: Settings, contract: ModelContract = CREDIT_MODEL_CONTRACT) -> None:
        self._settings = settings
        self._contract = contract

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.credit_model_path)

    def score(self, application: CreditApplicationInput) -> CreditScoringResult:
        if not self.is_configured:
            if self._settings.simulation_enabled:
                return self._simulate(application)
            raise ModelNotConfiguredError(
                "Aucun modèle de scoring de crédit n'est configuré "
                "(CREDIT_MODEL_PATH absent). Activez SIMULATION_ENABLED=true "
                "en développement pour tester les routes sans modèle réel."
            )

        model = load_model(self._settings.credit_model_path, self._contract.artifact_format)
        features = self._build_feature_vector(application)

        try:
            predict_fn = getattr(model, self._contract.predict_method)
            raw_output = predict_fn([features])
            probability = float(raw_output[0][1]) if self._contract.output_is_probability else float(raw_output[0])
        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise ModelPredictionError(
                f"Le modèle de crédit n'a pas produit un résultat exploitable : {exc}"
            ) from exc

        return CreditScoringResult(
            risk_score=round(probability, 4),
            risk_level=None,
            status=ProcessingStatus.COMPLETED,
            is_simulation=False,
            message="Score de risque calculé par le modèle de scoring de crédit.",
        )

    def _build_feature_vector(self, application: CreditApplicationInput) -> list[float]:
        """PROVISOIRE, à revoir avec le membre ML."""
        values: list[float] = []
        for name in self._contract.feature_names:
            value = getattr(application, name, None)
            if value is None:
                raise ModelPredictionError(
                    f"Feature manquante pour le modèle de crédit : '{name}'."
                )
            values.append(float(value))
        return values

    @staticmethod
    def _simulate(application: CreditApplicationInput) -> CreditScoringResult:
        return CreditScoringResult(
            risk_score=None,
            risk_level=None,
            status=ProcessingStatus.SIMULATED,
            is_simulation=True,
            message=(
                "SIMULATION : aucun modèle de scoring de crédit n'est "
                "encore branché. Cette réponse ne reflète aucune analyse "
                f"réelle de la demande '{application.application_id}'."
            ),
        )
