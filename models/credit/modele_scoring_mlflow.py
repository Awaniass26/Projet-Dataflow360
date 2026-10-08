"""
Pipeline complet — Scoring d'éligibilité au crédit mobile money (DataFlow360)
================================================================================
Adapté du pipeline de détection de fraude, mais PAS copié à l'identique :
plusieurs choix changent parce que les données sont réellement différentes.
Voir les commentaires "ADAPTATION" ci-dessous pour chaque différence et sa
justification, basée sur l'EDA déjà réalisée par l'équipe (2 000 000 clients).

Étapes :
  1. Préparation des données (exclusion identifiant, retrait de la colonne
     redondante, imputation de taux_remboursement)
  2. Séparation train/test stratifiée
  3. Comparaison de 5 configurations par validation croisée stratifiée
  4. Sélection du meilleur modèle, évaluation finale honnête sur le test
  5. Courbes ROC / Précision-Rappel comparatives
  6. Interprétabilité (SHAP)
  7. Calibration du seuil de décision à trois niveaux (approuver / revue
     manuelle / refuser) — calcul symétrique, voir plus bas pourquoi
  8. Enregistrement du modèle retenu dans le registre MLflow

Prérequis : pip install mlflow shap xgboost scikit-learn pandas imbalanced-learn
"""

import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import shap
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, accuracy_score,
    average_precision_score, confusion_matrix, precision_recall_curve, roc_curve,
)
from imblearn.pipeline import Pipeline  # même pipeline que pour la fraude, par cohérence

RANDOM_STATE = 42
CHEMIN_DONNEES_DEFAUT = "/home/moctar04/Documents/data/data_flow_project/Projet-Dataflow360/models/credit/dataset_Scoring_credit_2000000.csv"
CIBLE = "eligibilite"

# ADAPTATION 1 — client_id exclu : identifiant unique, aucune valeur
# généralisable (même raison que nameOrig/nameDest dans le pipeline fraude).
#
# ADAPTATION 2 — montant_transactions_90j exclu : l'EDA a mesuré des
# corrélations >= 0.80 entre montant_transactions_90j, montant_entrees_90j et
# montant_sorties_90j (0.87 / 0.87 / 0.82) — multicolinéarité forte. On garde
# entrees/sorties (économiquement distincts : revenus vs dépenses) et on
# retire la 3e variable, redondante puisqu'elle n'est qu'une combinaison des
# deux autres.
FEATURES_NUM = [
    "age", "anciennete_compte_mois", "nb_transactions_90j",
    "montant_entrees_90j", "montant_sorties_90j", "solde_moyen_90j",
    "regularite_revenus", "nombre_credits_precedents", "taux_remboursement",
    "nombre_credits_en_retard", "nombre_credits_impayes",
    "montant_credit_demande", "duree_credit_demande", "stabilite_flux",
]
FEATURES_CAT = ["type_activite"]
FEATURES = FEATURES_NUM + FEATURES_CAT

N_SPLITS_CV = 5
# ADAPTATION 3 — taille d'échantillon optionnelle : avec 2 000 000 de lignes,
# 5 configurations x 5 plis de CV + ré-entraînement final représente 30
# entraînements complets. Mettre une valeur ici (ex. 200_000) le temps de
# vérifier que tout fonctionne, puis repasser à None pour le run final sur
# l'intégralité des données.
TAILLE_ECHANTILLON_DEV = None


# =============================================================================
# 1. Chargement et préparation des données
# =============================================================================
def charger_donnees(chemin: str = CHEMIN_DONNEES_DEFAUT, taille_echantillon=None) -> pd.DataFrame:
    """
    Charge le CSV. taux_remboursement garde ses NaN ici (gérés par un
    SimpleImputer DANS le pipeline, pas en amont) — on impute à l'intérieur du
    pipeline pour que l'imputation soit recalculée correctement à chaque pli
    de validation croisée, jamais sur la base de l'ensemble complet (ce qui
    serait une fuite subtile entre les plis).
    """
    df = pd.read_csv(chemin)
    if taille_echantillon:
        df = df.sample(n=min(taille_echantillon, len(df)), random_state=RANDOM_STATE).reset_index(drop=True)
    return df


def separer_train_test(df: pd.DataFrame, test_size: float = 0.2):
    X = df[FEATURES]
    y = df[CIBLE].astype(int)
    return train_test_split(X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y)


# =============================================================================
# 2. Préprocesseur et construction de pipeline
# =============================================================================
def construire_preprocesseur() -> ColumnTransformer:
    """
    ADAPTATION 4 — un SimpleImputer(strategy="median") remplace le
    remainder="passthrough" du pipeline fraude : seule cette base de données
    a des valeurs manquantes (taux_remboursement, NaN quand le client n'a
    jamais eu de crédit). La médiane est un choix neutre : combinée à
    nombre_credits_precedents=0 (déjà une feature à part entière), le modèle
    dispose de l'information "pas d'historique" sans que la valeur imputée ne
    lui fasse croire à un historique de remboursement inventé.
    """
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES_CAT),
            ("num", SimpleImputer(strategy="median"), FEATURES_NUM),
        ],
    )


def noms_features_apres_encodage(preprocesseur_fit) -> list[str]:
    noms_cat = list(preprocesseur_fit.named_transformers_["cat"].get_feature_names_out(FEATURES_CAT))
    return noms_cat + FEATURES_NUM


def construire_pipeline(preprocesseur, modele) -> Pipeline:
    return Pipeline([("prep", preprocesseur), ("model", modele)])


def construire_configurations(y_train: pd.Series) -> dict:
    """
    ADAPTATION 5 — pas de SMOTE ni de sous-échantillonnage ici. L'EDA montre
    des classes globalement équilibrées (60 % / 40 %), très loin du
    déséquilibre extrême de la fraude (<1 %) : la littérature et la pratique
    s'accordent à dire que le ré-échantillonnage apporte peu, voire nuit,
    quand le déséquilibre est déjà modéré. Plutôt que de supposer, on COMPARE
    objectivement pondéré vs non pondéré pour chaque modèle — exactement
    l'esprit "ne jamais présumer, toujours comparer" déjà appliqué sur la
    fraude.
    """
    ratio_desequilibre = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    return {
        "logistic_regression_pondere": (
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
        ),
        "logistic_regression_non_pondere": (
            LogisticRegression(max_iter=1000, class_weight=None, random_state=RANDOM_STATE),
        ),
        "random_forest_pondere": (
            RandomForestClassifier(
                n_estimators=200, max_depth=12, class_weight="balanced",
                random_state=RANDOM_STATE, n_jobs=-1
            ),
        ),
        "xgboost_pondere": (
            XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.08,
                scale_pos_weight=ratio_desequilibre, eval_metric="auc",
                random_state=RANDOM_STATE, n_jobs=-1,
            ),
        ),
        "xgboost_non_pondere": (
            XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.08,
                scale_pos_weight=1, eval_metric="auc",
                random_state=RANDOM_STATE, n_jobs=-1,
            ),
        ),
    }


# =============================================================================
# 3. Validation croisée (identique dans l'esprit au pipeline fraude)
# =============================================================================
def evaluer_par_validation_croisee(pipe: Pipeline, X, y, n_splits: int = N_SPLITS_CV) -> dict:
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    # ADAPTATION 6 — "accuracy" est réintégrée dans les métriques. Elle était
    # proscrite sur la fraude (99%+ de non-fraude la rendait trompeuse) ; ici,
    # avec des classes à 60/40, elle redevient une métrique légitime et
    # facile à communiquer à un non-spécialiste, en complément — pas en
    # remplacement — de precision/recall/F1/ROC-AUC/PR-AUC.
    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "pr_auc": "average_precision",
    }
    resultats_cv = cross_validate(pipe, X, y, cv=cv, scoring=scoring, n_jobs=1, return_train_score=False)
    metriques = {}
    for nom_metrique in scoring:
        valeurs = resultats_cv[f"test_{nom_metrique}"]
        metriques[f"cv_{nom_metrique}_moyenne"] = float(valeurs.mean())
        metriques[f"cv_{nom_metrique}_ecart_type"] = float(valeurs.std())
    return metriques


# =============================================================================
# 4. Entraînement + validation croisée + évaluation finale + tracking MLflow
# =============================================================================
def entrainer_evaluer_et_logger(nom_configuration, modele, preprocesseur, X_train, y_train, X_test, y_test, n_splits_cv=N_SPLITS_CV) -> dict:
    with mlflow.start_run(run_name=nom_configuration):
        pipe = construire_pipeline(preprocesseur, modele)

        metriques_cv = evaluer_par_validation_croisee(pipe, X_train, y_train, n_splits=n_splits_cv)
        mlflow.log_metrics(metriques_cv)

        print(f"\n=== {nom_configuration} ===")
        print(f"  [Validation croisée {n_splits_cv} plis]")
        print(f"    Accuracy : {metriques_cv['cv_accuracy_moyenne']:.4f} (+/- {metriques_cv['cv_accuracy_ecart_type']:.4f})")
        print(f"    ROC-AUC  : {metriques_cv['cv_roc_auc_moyenne']:.4f} (+/- {metriques_cv['cv_roc_auc_ecart_type']:.4f})")
        print(f"    F1       : {metriques_cv['cv_f1_moyenne']:.4f} (+/- {metriques_cv['cv_f1_ecart_type']:.4f})")

        pipe.fit(X_train, y_train)
        proba_test = pipe.predict_proba(X_test)[:, 1]
        preds_test = (proba_test >= 0.5).astype(int)

        metriques_test = {
            "test_accuracy": accuracy_score(y_test, preds_test),
            "test_precision": precision_score(y_test, preds_test, zero_division=0),
            "test_recall": recall_score(y_test, preds_test, zero_division=0),
            "test_f1": f1_score(y_test, preds_test, zero_division=0),
            "test_roc_auc": roc_auc_score(y_test, proba_test),
            "test_pr_auc": average_precision_score(y_test, proba_test),
        }

        mlflow.log_param("modele", nom_configuration)
        mlflow.log_param("n_splits_cv", n_splits_cv)
        mlflow.log_params({f"hp_{k}": v for k, v in modele.get_params().items()})
        mlflow.log_metrics(metriques_test)
        mlflow.sklearn.log_model(pipe, artifact_path="model", serialization_format="pickle")

        tn, fp, fn, tp = confusion_matrix(y_test, preds_test).ravel()
        print(f"  [Évaluation finale sur le test tenu à l'écart]")
        for k, v in metriques_test.items():
            print(f"    {k:16s} : {v:.4f}")
        print(f"    Matrice de confusion -> VN={tn} FP={fp} FN={fn} VP={tp}")

        fpr, tpr, _ = roc_curve(y_test, proba_test)
        prec_c, rec_c, _ = precision_recall_curve(y_test, proba_test)
        courbe = {
            "fpr": fpr, "tpr": tpr, "roc_auc": metriques_test["test_roc_auc"],
            "precision": prec_c, "recall": rec_c, "pr_auc": metriques_test["test_pr_auc"],
        }

        return {"pipeline": pipe, "metriques_cv": metriques_cv, "metriques_test": metriques_test, "courbe": courbe}


def comparer_toutes_les_configurations(configurations, preprocesseur, X_train, y_train, X_test, y_test, n_splits_cv=N_SPLITS_CV) -> dict:
    mlflow.set_experiment("dataflow360_scoring_credit")
    resultats = {}
    for nom, (modele,) in configurations.items():
        resultats[nom] = entrainer_evaluer_et_logger(nom, modele, preprocesseur, X_train, y_train, X_test, y_test, n_splits_cv)
    return resultats


def selectionner_meilleure_configuration(resultats: dict) -> str:
    """
    ADAPTATION 7 — sélection sur le ROC-AUC moyen en CV, pas le PR-AUC.
    Avec des classes équilibrées (60/40), le ROC-AUC n'est plus optimiste de
    façon trompeuse (contrairement au cas très déséquilibré de la fraude) et
    reste la métrique la plus standard et la plus interprétable pour du
    scoring de crédit, où l'on compare constamment des modèles entre eux.
    """
    return max(resultats, key=lambda n: resultats[n]["metriques_cv"]["cv_roc_auc_moyenne"])


# =============================================================================
# 5. Courbes ROC / Précision-Rappel comparatives
# =============================================================================
def tracer_courbes_comparatives(resultats, meilleur_nom, y_test, chemin_sortie="courbes_roc_pr_scoring_credit.png"):
    fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(14, 6))
    for nom, r in resultats.items():
        c = r["courbe"]
        style = "--" if nom == meilleur_nom else "-"
        largeur = 2.5 if nom == meilleur_nom else 1.3
        ax_roc.plot(c["fpr"], c["tpr"], style, linewidth=largeur, label=f"{nom} (AUC={c['roc_auc']:.3f})")
        ax_pr.plot(c["recall"], c["precision"], style, linewidth=largeur, label=f"{nom} (AUC={c['pr_auc']:.3f})")

    ax_roc.plot([0, 1], [0, 1], ":", color="gray", label="Hasard")
    ax_roc.set_xlabel("Taux de faux positifs"); ax_roc.set_ylabel("Taux de vrais positifs")
    ax_roc.set_title("Courbes ROC — comparaison des modèles"); ax_roc.legend(fontsize=8)

    taux_eligible = y_test.mean()
    ax_pr.axhline(taux_eligible, color="gray", linestyle=":", label=f"Hasard ({taux_eligible:.1%})")
    ax_pr.set_xlabel("Rappel"); ax_pr.set_ylabel("Précision")
    ax_pr.set_title("Courbes Précision-Rappel — comparaison des modèles"); ax_pr.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=150)
    plt.close()
    print(f"Courbes sauvegardées -> {chemin_sortie}")


# =============================================================================
# 6. Interprétabilité (SHAP)
# =============================================================================
def calculer_et_sauvegarder_shap(meilleur_pipe: Pipeline, X_test, chemin_sortie="shap_summary_scoring_credit.png", taille_echantillon_shap=2000):
    # ADAPTATION 8 — sous-échantillon pour SHAP : avec un jeu de test pouvant
    # dépasser 400 000 lignes (20% de 2M), calculer SHAP sur l'intégralité
    # serait inutilement long. Un échantillon aléatoire de 2000 lignes donne
    # une estimation fiable de l'importance globale des variables.
    X_echantillon = X_test.sample(n=min(taille_echantillon_shap, len(X_test)), random_state=RANDOM_STATE)
    X_transforme = meilleur_pipe.named_steps["prep"].transform(X_echantillon)
    if hasattr(X_transforme, "toarray"):
        X_transforme = X_transforme.toarray()
    noms_colonnes = noms_features_apres_encodage(meilleur_pipe.named_steps["prep"])
    X_df = pd.DataFrame(X_transforme, columns=noms_colonnes)

    modele_final = meilleur_pipe.named_steps["model"]
    try:
        if isinstance(modele_final, LogisticRegression):
            explainer = shap.LinearExplainer(modele_final, X_df)
        else:
            explainer = shap.TreeExplainer(modele_final)
        valeurs_shap = explainer.shap_values(X_df)
        shap.summary_plot(valeurs_shap, X_df, show=False)
        plt.tight_layout()
        plt.savefig(chemin_sortie, dpi=150)
        plt.close()
        print(f"Graphique SHAP sauvegardé -> {chemin_sortie}")
    except Exception as e:
        print(f"SHAP non calculé pour ce modèle ({e}).")


# =============================================================================
# 7. Calibration du seuil de décision à trois niveaux
#    ADAPTATION 9 — contrairement à la fraude (un seul sens de risque),
#    l'éligibilité a DEUX sens à sécuriser symétriquement : approuver à tort
#    (mauvais payeur accepté) ET refuser à tort (bon payeur rejeté, manque à
#    gagner). On calibre donc DEUX seuils indépendamment, chacun sur sa
#    propre notion de précision.
# =============================================================================
def seuil_pour_precision_minimale(precisions, seuils, precision_visee: float):
    indices_valides = np.where(precisions[:-1] >= precision_visee)[0]
    if len(indices_valides) == 0:
        return None
    return seuils[indices_valides[0]]


def calibrer_seuils(meilleur_pipe: Pipeline, X_test, y_test, precision_approbation=0.90, precision_refus=0.90):
    proba_eligible = meilleur_pipe.predict_proba(X_test)[:, 1]

    # Seuil d'approbation automatique : précision élevée sur la classe "éligible"
    precisions_approb, _, seuils_approb = precision_recall_curve(y_test, proba_eligible)
    seuil_approbation = seuil_pour_precision_minimale(precisions_approb, seuils_approb, precision_approbation)

    # Seuil de refus automatique : précision élevée sur la classe "non éligible",
    # calculée en inversant labels et scores (même fonction, réutilisée telle quelle).
    precisions_refus, _, seuils_refus_inv = precision_recall_curve(1 - y_test, 1 - proba_eligible)
    seuil_refus_inv = seuil_pour_precision_minimale(precisions_refus, seuils_refus_inv, precision_refus)
    seuil_refus = 1 - seuil_refus_inv if seuil_refus_inv is not None else None

    print("\n--- Seuils de décision calibrés sur le jeu de test ---")
    print(f"Seuil d'APPROBATION automatique (precision >= {precision_approbation:.0%} sur 'éligible')  : {seuil_approbation}")
    print(f"Seuil de REFUS automatique      (precision >= {precision_refus:.0%} sur 'non-éligible')     : {seuil_refus}")
    print("Entre les deux -> dossier envoyé en revue manuelle.")
    if seuil_approbation is None or seuil_refus is None:
        print("ATTENTION : au moins un des deux seuils cibles n'est pas atteignable avec ce modèle —")
        print("élargir la zone de revue manuelle ou améliorer le modèle avant automatisation complète.")
    return seuil_approbation, seuil_refus


# =============================================================================
# ORCHESTRATION
# =============================================================================
if __name__ == "__main__":
    df = charger_donnees(CHEMIN_DONNEES_DEFAUT, taille_echantillon=TAILLE_ECHANTILLON_DEV)
    print(f"Lignes : {len(df):,} | Taux d'éligibilité global : {df[CIBLE].mean():.3%}")

    X_train, X_test, y_train, y_test = separer_train_test(df)
    print(f"Train : {len(X_train):,} ({y_train.mean():.3%} éligibles) | "
          f"Test : {len(X_test):,} ({y_test.mean():.3%} éligibles)")

    preprocesseur = construire_preprocesseur()
    configurations = construire_configurations(y_train)

    resultats = comparer_toutes_les_configurations(configurations, preprocesseur, X_train, y_train, X_test, y_test, N_SPLITS_CV)

    meilleur_nom = selectionner_meilleure_configuration(resultats)
    meilleur_pipe = resultats[meilleur_nom]["pipeline"]
    print(f"\n>>> Meilleure configuration (sur la moyenne CV du ROC-AUC) : {meilleur_nom}")
    print(f"    CV   ROC-AUC : {resultats[meilleur_nom]['metriques_cv']['cv_roc_auc_moyenne']:.4f}")
    print(f"    Test ROC-AUC : {resultats[meilleur_nom]['metriques_test']['test_roc_auc']:.4f}")

    joblib.dump(meilleur_pipe, "modele_scoring_credit_final.pkl")
    X_test.to_csv("X_test_scoring_credit.csv", index=False)
    y_test.to_csv("y_test_scoring_credit.csv", index=False)
    print("Modèle sauvegardé -> modele_scoring_credit_final.pkl")

    tracer_courbes_comparatives(resultats, meilleur_nom, y_test)
    calculer_et_sauvegarder_shap(meilleur_pipe, X_test)
    seuil_approbation, seuil_refus = calibrer_seuils(meilleur_pipe, X_test, y_test)

    with mlflow.start_run(run_name=f"{meilleur_nom}_final_registre"):
        mlflow.sklearn.log_model(
            meilleur_pipe, artifact_path="model",
            registered_model_name="dataflow360_scoring_credit_production",
            serialization_format="pickle",
        )
        mlflow.log_metrics(resultats[meilleur_nom]["metriques_test"])
        mlflow.log_metrics(resultats[meilleur_nom]["metriques_cv"])
        mlflow.log_param("seuil_approbation", seuil_approbation)
        mlflow.log_param("seuil_refus", seuil_refus)

    print("\nModèle enregistré dans le registre MLflow sous le nom "
          "'dataflow360_scoring_credit_production'.")