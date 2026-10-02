"""Service de détection de fraude.

Intégration du modèle réel (pour le membre ML / la personne qui branche le
modèle) :
     1. Déposer le modèle fraude fourni, sérialisé avec joblib, dans
         `models/modele_fraude_final.pkl` (voir
       `api/services/ml_contracts.py` - FRAUD_MODEL_CONTRACT.artifact_format,
       à confirmer ensemble).
    2. Renseigner FRAUD_MODEL_PATH dans `.env` (chemin vers le fichier .pkl)
       et FRAUD_MODEL_VERSION (identifiant de version).
    3. Vérifier `ml_contracts.FRAUD_MODEL_CONTRACT` : noms et ORDRE des
       features, méthode de prédiction, seuil de classification
       (FRAUD_DECISION_THRESHOLD dans `.env`).
    4. Redémarrer l'API : `is_configured` passera automatiquement à True.
"""

from dataclasses import dataclass

import pandas as pd

from api.core.config import Settings
from api.core.exceptions import ModelNotConfiguredError, ModelPredictionError
from api.schemas.common import ProcessingStatus, RiskLevel
from api.schemas.fraud import TransactionInput
from api.services.ml_contracts import FRAUD_MODEL_CONTRACT, ModelContract
from api.services.model_loader import load_model


@dataclass
class FraudPredictionResult:
    risk_score: float | None
    risk_level: RiskLevel | None
    status: ProcessingStatus
    is_simulation: bool
    message: str


class FraudDetectionService:
    """Un score de risque est une AIDE À LA DÉCISION : ce service ne bloque et
    ne valide jamais une transaction lui-même."""

    def __init__(self, settings: Settings, contract: ModelContract = FRAUD_MODEL_CONTRACT) -> None:
        self._settings = settings
        self._contract = contract

    @property
    def is_configured(self) -> bool:
        return bool(self._settings.fraud_model_path)

    def predict(self, transaction: TransactionInput) -> FraudPredictionResult:
        if not self.is_configured:
            if self._settings.simulation_enabled:
                return self._simulate(transaction)
            raise ModelNotConfiguredError(
                "Aucun modèle de détection de fraude n'est configuré "
                "(FRAUD_MODEL_PATH absent). Activez SIMULATION_ENABLED=true "
                "en développement pour tester les routes sans modèle réel."
            )

        model = load_model(self._settings.fraud_model_path, self._contract.artifact_format)
        features = self._build_feature_vector(transaction)

        try:
            predict_fn = getattr(model, self._contract.predict_method)
            raw_output = predict_fn(features)
            probability = float(raw_output[0][1]) if self._contract.output_is_probability else float(raw_output[0])
        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise ModelPredictionError(
                f"Le modèle de fraude n'a pas produit un résultat exploitable : {exc}"
            ) from exc

        threshold = self._settings.fraud_decision_threshold
        risk_level = self._score_to_risk_level(probability, threshold) if threshold is not None else None

        return FraudPredictionResult(
            risk_score=round(probability, 4),
            risk_level=risk_level,
            status=ProcessingStatus.COMPLETED,
            is_simulation=False,
            message="Score de risque calculé par le modèle de détection de fraude.",
        )

    def _build_feature_vector(self, transaction: TransactionInput) -> pd.DataFrame:
        """Construit les colonnes nommées attendues par le pipeline ML."""
        values = {
            "montant": transaction.amount,
            "heure": transaction.hour,
            "ecart_montant_moyen": transaction.ecart_montant_moyen,
            "ecart_heure_habituelle": transaction.ecart_heure_habituelle,
            "nouvel_appareil": transaction.nouvel_appareil,
            "nouveau_destinataire": transaction.nouveau_destinataire,
            "type": transaction.transaction_type.value,
            "canal": transaction.channel.value,
        }
        return pd.DataFrame([[values[name] for name in self._contract.feature_names]], columns=self._contract.feature_names)

    @staticmethod
    def _score_to_risk_level(score: float, threshold: float) -> RiskLevel:
        """PROVISOIRE, à valider avec l'équipe."""
        if score < threshold / 2:
            return RiskLevel.LOW
        if score < threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.HIGH

    @staticmethod
    def _simulate(transaction: TransactionInput) -> FraudPredictionResult:
        return FraudPredictionResult(
            risk_score=None,
            risk_level=None,
            status=ProcessingStatus.SIMULATED,
            is_simulation=True,
            message=(
                "SIMULATION : aucun modèle de détection de fraude n'est "
                "encore branché. Cette réponse ne reflète aucune analyse "
                f"réelle de la transaction '{transaction.transaction_id}'."
            ),
        )
