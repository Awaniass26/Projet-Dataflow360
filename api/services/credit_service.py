"""Service de scoring du risque de crédit. Voir fraud_service.py pour le
détail des étapes d'intégration du modèle réel (CREDIT_MODEL_PATH / CREDIT_MODEL_VERSION)."""

from dataclasses import dataclass

from api.core.config import Settings
from api.core.exceptions import ModelNotConfiguredError, ModelPredictionError
from api.schemas.common import ProcessingStatus, RiskLevel
from api.schemas.credit import CreditApplicationInput
from api.services.ml_contracts import CREDIT_MODEL_CONTRACT, ModelContract
from api.services.model_loader import load_model
import pandas as pd 

@dataclass
class CreditScoringResult:
    risk_score: float | None
    risk_level: RiskLevel | None
    eligible: bool | None
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

        model = load_model(
            self._settings.credit_model_path,
            self._contract.artifact_format,
        )
        features = self._build_feature_vector(application)

        try:
            predict_fn = getattr(model, self._contract.predict_method)
            raw_output = predict_fn(features)

            probability = (
                float(raw_output[0][1])
                if self._contract.output_is_probability
                else float(raw_output[0])
            )

        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise ModelPredictionError(
                "Le modèle de crédit n'a pas produit un résultat exploitable : "
                f"{exc}"
            ) from exc

        # Seuil d'approbation défini par le Data Scientist : 90 %
        approval_threshold = 0.90

        if probability >= approval_threshold:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.HIGH

        eligible = probability >= approval_threshold

        return CreditScoringResult(
            risk_score=round(probability, 4),
            risk_level=risk_level,
            eligible=eligible,
            status=ProcessingStatus.COMPLETED,
            is_simulation=False,
            message=(
                "Score de risque calculé par le modèle de scoring de crédit. "
                f"Seuil d'approbation : {approval_threshold:.0%}."
            ),
        )


    def score_from_features_dict(self, features: dict) -> "CreditScoringResult":
        """Appelle le modèle avec un dict de features déjà calculées.

        Utilisé par `score_auto` après calcul depuis l'historique.
        """
        if not self.is_configured:
            if self._settings.simulation_enabled:
                # Construire un CreditApplicationInput à partir du dict
                from api.schemas.credit import CreditApplicationInput
                try:
                    app = CreditApplicationInput(**features)
                except Exception:
                    return CreditScoringResult(
                        risk_score=None,
                        risk_level=None,
                        eligible=None,
                        status=ProcessingStatus.SIMULATED,
                        is_simulation=True,
                        message=(
                            "SIMULATION : aucun modèle de scoring de crédit "
                            "n'est configuré. Les features ont été calculées."
                        ),
                    )
                return self._simulate(app)
            raise ModelNotConfiguredError(
                "Aucun modèle de scoring de crédit n'est configuré."
            )

        model = load_model(
            self._settings.credit_model_path,
            self._contract.artifact_format,
        )

        # Construire le DataFrame avec les 15 features
        import pandas as pd
        values = [features.get(name) for name in self._contract.feature_names]
        df = pd.DataFrame([values], columns=self._contract.feature_names)

        try:
            predict_fn = getattr(model, self._contract.predict_method)
            raw_output = predict_fn(df)
            probability = (
                float(raw_output[0][1])
                if self._contract.output_is_probability
                else float(raw_output[0])
            )
        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise ModelPredictionError(
                f"Le modèle de crédit n'a pas produit un résultat exploitable : {exc}"
            ) from exc

        approval_threshold = 0.90
        risk_level = RiskLevel.LOW if probability >= approval_threshold else RiskLevel.HIGH
        eligible = probability >= approval_threshold

        return CreditScoringResult(
            risk_score=round(probability, 4),
            risk_level=risk_level,
            eligible=eligible,
            status=ProcessingStatus.COMPLETED,
            is_simulation=False,
            message=(
                "Score de risque calculé par le modèle de scoring de crédit "
                f"à partir de l'historique du client. Seuil : {approval_threshold:.0%}."
            ),
        )

    def _build_feature_vector(
        self,
        application: CreditApplicationInput,
    ) -> pd.DataFrame:
        """Construit le DataFrame attendu par le pipeline ML."""

        data = {
            "age": application.age,
            "anciennete_compte_mois": application.anciennete_compte_mois,
            "nb_transactions_90j": application.nb_transactions_90j,
            "montant_entrees_90j": application.montant_entrees_90j,
            "montant_sorties_90j": application.montant_sorties_90j,
            "solde_moyen_90j": application.solde_moyen_90j,
            "regularite_revenus": application.regularite_revenus,
            "nombre_credits_precedents": application.nombre_credits_precedents,
            "taux_remboursement": application.taux_remboursement,
            "nombre_credits_en_retard": application.nombre_credits_en_retard,
            "nombre_credits_impayes": application.nombre_credits_impayes,
            "montant_credit_demande": application.montant_credit_demande,
            "duree_credit_demande": application.duree_credit_demande,
            "stabilite_flux": application.stabilite_flux,
            "type_activite": application.type_activite,
        }

        return pd.DataFrame([data], columns=self._contract.feature_names)

    @staticmethod
    def _simulate(application: CreditApplicationInput) -> CreditScoringResult:
        return CreditScoringResult(
            risk_score=None,
            risk_level=None,
            eligible=None,
            status=ProcessingStatus.SIMULATED,
            is_simulation=True,
            message=(
                "SIMULATION : aucun modèle de scoring de crédit n'est "
                "encore branché. Cette réponse ne reflète aucune analyse "
                f"réelle de la demande '{application.application_id}'."
            ),
        )
