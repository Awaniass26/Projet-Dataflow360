"""Contrats attendus entre le backend et les modèles ML (fraude et crédit).

Ce fichier ne contient AUCUNE logique de prédiction : il documente, sous forme
de types Python, ce que le backend suppose provisoirement et ce qui doit être
confirmé avec le membre ML avant l'intégration finale (voir le README backend,
section "Points à valider").
"""

from dataclasses import dataclass
from enum import StrEnum


class ModelArtifactFormat(StrEnum):
    """Format de sérialisation du modèle sauvegardé.

    NON ARRÊTÉ : à confirmer avec le membre ML. joblib est généralement
    préférable pour les modèles scikit-learn (gros tableaux numpy), pickle
    fonctionne aussi mais est plus sensible aux versions de librairies.
    """

    JOBLIB = "joblib"
    PICKLE = "pickle"


@dataclass(frozen=True)
class ModelContract:
    """Décrit ce que le backend doit savoir pour appeler un modèle.

    Attributes:
        feature_names: Noms des variables, DANS L'ORDRE attendu par le modèle.
            PROVISOIRE tant que le Feature Engineering n'est pas figé.
        artifact_format: Format du fichier modèle (joblib ou pickle).
        predict_method: Nom de la méthode à appeler sur l'objet chargé
            (ex. "predict_proba" pour une probabilité, "predict" pour une
            classe directe). À confirmer avec le membre ML.
        output_is_probability: True si predict_method renvoie une probabilité
            continue (nécessite alors un seuil de classification), False si
            le modèle renvoie déjà une classe/catégorie.
        model_version: Identifiant de version du modèle livré (ex. date ou
            numéro), à faire correspondre au fichier réellement chargé.
    """

    feature_names: tuple[str, ...]
    artifact_format: ModelArtifactFormat
    predict_method: str
    output_is_probability: bool
    model_version: str | None


FRAUD_MODEL_CONTRACT = ModelContract(
    feature_names=(
        "montant",
        "heure",
        "ecart_montant_moyen",
        "ecart_heure_habituelle",
        "nouvel_appareil",
        "nouveau_destinataire",
        "type",
        "canal",
    ),
    artifact_format=ModelArtifactFormat.JOBLIB,
    predict_method="predict_proba",
    output_is_probability=True,
    model_version=None,  # renseigné via FRAUD_MODEL_VERSION dans .env
)

CREDIT_MODEL_CONTRACT = ModelContract(
    feature_names=(
        "age",
        "anciennete_compte_mois",
        "nb_transactions_90j",
        "montant_entrees_90j",
        "montant_sorties_90j",
        "solde_moyen_90j",
        "regularite_revenus",
        "nombre_credits_precedents",
        "taux_remboursement",
        "nombre_credits_en_retard",
        "nombre_credits_impayes",
        "montant_credit_demande",
        "duree_credit_demande",
        "stabilite_flux",
        "type_activite",
    ),
    artifact_format=ModelArtifactFormat.JOBLIB,
    predict_method="predict_proba",
    output_is_probability=True,
    model_version=None,
)
