"""
Pipeline complet — Détection de fraude mobile money (DataFlow360)
===================================================================
Suite de l'EDA déjà réalisée par Mariama Diallo. Ce script couvre :
  1. Préparation des données
  2. Séparation train/test (+ note importante sur le split temporel)
  3. Comparaison de plusieurs modèles (dont SMOTE / sous-échantillonnage),
     chacun évalué par VALIDATION CROISÉE stratifiée sur le train
  4. Sélection du meilleur modèle sur la moyenne de validation croisée
     (plus robuste qu'un seul split), puis ré-entraînement complet et
     évaluation finale honnête sur le jeu de test tenu à l'écart
  5. Courbes ROC et Précision-Rappel comparatives
  6. Interprétabilité (SHAP)
  7. Calibration du seuil de décision à trois niveaux
  8. Enregistrement du modèle retenu dans le registre MLflow

Tout le code de construction/évaluation est organisé en FONCTIONS RÉUTILISABLES
(voir en bas de fichier le bloc `if __name__ == "__main__":` pour l'orchestration) :
on peut importer et réutiliser n'importe laquelle depuis un notebook ou un autre
script, par exemple :
    from pipeline_fraude_mlflow import construire_pipeline, evaluer_par_validation_croisee

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
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, precision_recall_curve, roc_curve,
)
from imblearn.pipeline import Pipeline  # compatible ré-échantillonnage (SMOTE, etc.)
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

RANDOM_STATE = 42
CHEMIN_DONNEES_DEFAUT = "/home/moctar04/Documents/data/data_flow_project/Projet-Dataflow360/eda/notebooks/dataset_fraude_clean.csv"  # <- adapter au vrai fichier (493 000 lignes)
CIBLE = "fraude"
FEATURES_NUM_BASE = ["montant", "heure", "ecart_montant_moyen", "ecart_heure_habituelle"]
COLONNES_BOOL = ["nouvel_appareil", "nouveau_destinataire"]
FEATURES_NUM = FEATURES_NUM_BASE + COLONNES_BOOL
FEATURES_CAT = ["type", "canal"]
FEATURES = FEATURES_NUM + FEATURES_CAT

N_SPLITS_CV = 5  # nombre de plis pour la validation croisée (réduire à 3 si le temps de calcul est trop long)


# =============================================================================
# 1. Chargement et préparation des données
# =============================================================================
def charger_donnees(chemin: str = CHEMIN_DONNEES_DEFAUT) -> pd.DataFrame:
    """Charge le CSV et convertit les colonnes booléennes en 0/1."""
    df = pd.read_csv(chemin)
    for c in COLONNES_BOOL:
        df[c] = df[c].astype(int)
    return df


def separer_train_test(df: pd.DataFrame, test_size: float = 0.2):
    """
    Sépare X/y puis train/test de façon ALÉATOIRE STRATIFIÉE, faute de colonne
    de date/timestamp explicite (voir la méthodologie : un split temporel,
    entraîner sur le passé et tester sur le plus récent, reste préférable si
    une vraie colonne de date existe dans le fichier complet).
    """
    #Nous utilisons la méthode aléatoire stratifiée pour préserver la proportion de fraude dans les ensembles train et test.
    #et parce que aussi nous avons pas une colonne date ou timestamps explicite 
    #ce serait mieux car le modele doit predire sur des données futures : entrainer sur anciens transactions et tester sur les plus récentes.
    X = df[FEATURES]
    y = df[CIBLE].astype(int)
    return train_test_split(X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y)


# =============================================================================
# 2. Préprocesseur et construction de pipeline (réutilisables)
# =============================================================================
def construire_preprocesseur() -> ColumnTransformer:
    """Encode les variables catégorielles, laisse passer les numériques telles quelles."""
    return ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES_CAT)],
        remainder="passthrough",
    )


def noms_features_apres_encodage(preprocesseur_fit) -> list[str]:
    """Récupère les noms de colonnes après OneHotEncoding, pour SHAP et le feature importance."""
    noms_cat = list(preprocesseur_fit.named_transformers_["cat"].get_feature_names_out(FEATURES_CAT))
    return noms_cat + FEATURES_NUM


def construire_pipeline(preprocesseur, modele, echantillonneur=None) -> Pipeline:
    """
    Construit un pipeline complet (encodage [+ ré-échantillonnage] + modèle),
    réutilisable tel quel pour l'entraînement, la validation croisée OU le
    service en production (API de scoring) — une seule définition, jamais de
    risque d'appliquer une transformation différente entre les deux.
    """
    etapes = [("prep", preprocesseur)]
    if echantillonneur is not None:
        # Le ré-échantillonnage (imblearn) n'agit QUE pendant .fit() sur les
        # données d'entraînement ; il est automatiquement ignoré lors de
        # .predict()/.predict_proba(), et — point clé pour la validation
        # croisée ci-dessous — ré-appliqué indépendamment sur chaque pli
        # d'entraînement, jamais sur le pli de validation correspondant.
        etapes.append(("echantillonnage", echantillonneur))
    etapes.append(("model", modele))
    return Pipeline(etapes)


def construire_configurations(y_train: pd.Series) -> dict:
    """
    Retourne {nom_configuration: (modele, echantillonneur_ou_None)}.
    Fonction pure, réutilisable avec n'importe quel y_train pour recalculer
    automatiquement le ratio de déséquilibre et le nombre de voisins SMOTE.
    """
    ratio_desequilibre = (y_train == 0).sum() / max((y_train == 1).sum(), 1) #calcule le rapport entre le nombre de transactions normales et le nombre de transactions frauduleuses. Exemple : 9 000 normales / 1 000 frauduleuses = 9.
    n_minoritaire = int((y_train == 1).sum()) #ompte le nombre de fraudes, supposées être la classe minoritaire.
    k_voisins_smote = max(1, min(5, n_minoritaire - 1)) #détermine le nombre de voisins utilisés par SMOTE pour générer de nouvelles transactions frauduleuses synthétiques. Il est limité entre 1 et 5.

    return {
        "logistic_regression": (
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),#augmente automatiquement le poids accordé à la classe minoritaire pendant l'apprentissage.
            None,
        ),
        "random_forest": (
            RandomForestClassifier(
                n_estimators=300, max_depth=None, class_weight="balanced",
                random_state=RANDOM_STATE, n_jobs=-1
            ),
            None,
        ),
        "xgboost": (
            XGBClassifier(
                n_estimators=300, #Nombre d'arbres de décision construits successivement. Plus il y a d'arbres, plus le modèle peut apprendre des relations complexes, mais le temps d'entraînement augmente.
                max_depth=5, #Profondeur maximale de chaque arbre. Une profondeur plus grande permet au modèle de capturer des interactions plus complexes entre les caractéristiques, mais peut entraîner un surapprentissage.
                learning_rate=0.05,
                scale_pos_weight=ratio_desequilibre, #Donne davantage de poids aux fraudes lorsque celles-ci sont minoritaires. Permet de mieux prendre en compte le déséquilibre des classes.
                eval_metric="aucpr", #Utilise l'aire sous la courbe Precision-Recall pour évaluer les performances pendant l'entraînement. Particulièrement pertinente pour les données fortement déséquilibrées.
                random_state=RANDOM_STATE, 
                n_jobs=-1,
            ),
            None,
        ),
        "xgboost_surechantillonnage_smote": (
            XGBClassifier(
                n_estimators=300, 
                max_depth=5, learning_rate=0.05,
                scale_pos_weight=1, 
                eval_metric="aucpr",
                random_state=RANDOM_STATE, 
                n_jobs=-1,
            ),
            SMOTE(random_state=RANDOM_STATE, k_neighbors=k_voisins_smote),
        ),
        "xgboost_sous_echantillonnage": (
            XGBClassifier(
                n_estimators=300, 
                max_depth=5, learning_rate=0.05,
                scale_pos_weight=1, 
                eval_metric="aucpr",
                random_state=RANDOM_STATE, 
                n_jobs=-1,
            ),
            RandomUnderSampler(random_state=RANDOM_STATE),
        ),
    }


# =============================================================================
# 3. Validation croisée (réutilisable pour n'importe quel pipeline/jeu de données)
# =============================================================================
def evaluer_par_validation_croisee(pipe: Pipeline, X, y, n_splits: int = N_SPLITS_CV) -> dict:
    """
    Évalue un pipeline par validation croisée stratifiée (K-Fold), bien plus
    fiable qu'un seul split train/test pour choisir entre plusieurs modèles :
    la moyenne sur plusieurs plis lisse la variance d'un découpage malchanceux,
    et l'écart-type indique la stabilité du modèle.

    StratifiedKFold (et non KFold classique) préserve la même proportion de
    fraude dans chaque pli — indispensable avec une classe aussi minoritaire.
    Le ré-échantillonnage éventuel du pipeline (SMOTE, etc.) est recalculé
    indépendamment à l'intérieur de chaque pli d'entraînement, jamais sur la
    validation, grâce au pipeline imblearn utilisé dans construire_pipeline().
    """
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    scoring = {
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "pr_auc": "average_precision",
    }
    resultats_cv = cross_validate(
        pipe, X, y, cv=cv, scoring=scoring, n_jobs=1, return_train_score=False
    )
    metriques = {}
    for nom_metrique in scoring:
        valeurs = resultats_cv[f"test_{nom_metrique}"]
        metriques[f"cv_{nom_metrique}_moyenne"] = float(valeurs.mean())
        metriques[f"cv_{nom_metrique}_ecart_type"] = float(valeurs.std())
    return metriques


# =============================================================================
# 4. Entraînement + validation croisée + évaluation finale + tracking MLflow
# =============================================================================
def entrainer_evaluer_et_logger(
    nom_configuration: str, modele, echantillonneur, preprocesseur,
    X_train, y_train, X_test, y_test, n_splits_cv: int = N_SPLITS_CV,
) -> dict:
    """
    Pour une configuration donnée :
      1. L'évalue par validation croisée sur X_train/y_train (sélection robuste)
      2. Ré-entraîne une fois sur tout X_train
      3. L'évalue une seule fois sur X_test, tenu à l'écart (estimation finale honnête)
      4. Logge l'intégralité (CV + test + courbes) dans MLflow
    Retourne un dict avec le pipeline entraîné, les métriques CV et les métriques test.
    """
    with mlflow.start_run(run_name=nom_configuration):
        pipe = construire_pipeline(preprocesseur, modele, echantillonneur)

        # --- Validation croisée sur le train uniquement ---
        metriques_cv = evaluer_par_validation_croisee(pipe, X_train, y_train, n_splits=n_splits_cv)
        mlflow.log_metrics(metriques_cv)

        print(f"\n=== {nom_configuration} ===")
        print(f"  [Validation croisée {n_splits_cv} plis]")
        print(f"    PR-AUC  : {metriques_cv['cv_pr_auc_moyenne']:.4f} (+/- {metriques_cv['cv_pr_auc_ecart_type']:.4f})")
        print(f"    ROC-AUC : {metriques_cv['cv_roc_auc_moyenne']:.4f} (+/- {metriques_cv['cv_roc_auc_ecart_type']:.4f})")
        print(f"    Recall  : {metriques_cv['cv_recall_moyenne']:.4f} (+/- {metriques_cv['cv_recall_ecart_type']:.4f})")

        # --- Ré-entraînement complet + évaluation finale sur le test tenu à l'écart ---
        pipe.fit(X_train, y_train)
        proba_test = pipe.predict_proba(X_test)[:, 1]
        preds_test = (proba_test >= 0.5).astype(int)

        metriques_test = {
            "test_precision": precision_score(y_test, preds_test, zero_division=0),
            "test_recall": recall_score(y_test, preds_test, zero_division=0),
            "test_f1": f1_score(y_test, preds_test, zero_division=0),
              "test_roc_auc": roc_auc_score(y_test, proba_test),
            "test_pr_auc": average_precision_score(y_test, proba_test),
        }

        mlflow.log_param("modele", nom_configuration)
        mlflow.log_param("echantillonnage", type(echantillonneur).__name__ if echantillonneur else "aucun")
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

        return {
            "pipeline": pipe,
            "metriques_cv": metriques_cv,
            "metriques_test": metriques_test,
            "courbe": courbe,
        }


def comparer_toutes_les_configurations(
    configurations: dict, preprocesseur, X_train, y_train, X_test, y_test, n_splits_cv: int = N_SPLITS_CV,
) -> dict:
    """Boucle réutilisable : entraîne/évalue toutes les configurations fournies et renvoie leurs résultats."""
    mlflow.set_experiment("dataflow360_detection_fraude")
    resultats = {}
    for nom, (modele, echantillonneur) in configurations.items():
        resultats[nom] = entrainer_evaluer_et_logger(
            nom, modele, echantillonneur, preprocesseur, X_train, y_train, X_test, y_test, n_splits_cv
        )
    return resultats


def selectionner_meilleure_configuration(resultats: dict) -> str:
    """
    Sélectionne la configuration gagnante sur la moyenne de PR-AUC en
    validation croisée (plus robuste qu'un seul split) — PAS sur le score du
    jeu de test, qui doit rester une estimation finale non utilisée pour
    décider, afin de ne pas biaiser optimistement l'évaluation.
    """
    return max(resultats, key=lambda n: resultats[n]["metriques_cv"]["cv_pr_auc_moyenne"])


# =============================================================================
# 5. Courbes ROC / Précision-Rappel comparatives
# =============================================================================
def tracer_courbes_comparatives(resultats: dict, meilleur_nom: str, y_test, chemin_sortie: str = "courbes_roc_pr_comparaison.png"):
    fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(14, 6))

    for nom, r in resultats.items():
        c = r["courbe"]
        style = "--" if nom == meilleur_nom else "-"
        largeur = 2.5 if nom == meilleur_nom else 1.3
        ax_roc.plot(c["fpr"], c["tpr"], style, linewidth=largeur, label=f"{nom} (AUC={c['roc_auc']:.3f})")
        ax_pr.plot(c["recall"], c["precision"], style, linewidth=largeur, label=f"{nom} (AUC={c['pr_auc']:.3f})")

    ax_roc.plot([0, 1], [0, 1], ":", color="gray", label="Hasard")
    ax_roc.set_xlabel("Taux de faux positifs")
    ax_roc.set_ylabel("Taux de vrais positifs")
    ax_roc.set_title("Courbes ROC — comparaison des modèles")
    ax_roc.legend(fontsize=8)

    taux_fraude_test = y_test.mean()
    ax_pr.axhline(taux_fraude_test, color="gray", linestyle=":", label=f"Hasard ({taux_fraude_test:.3%})")
    ax_pr.set_xlabel("Rappel")
    ax_pr.set_ylabel("Précision")
    ax_pr.set_title("Courbes Précision-Rappel — comparaison des modèles")
    ax_pr.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(chemin_sortie, dpi=150)
    plt.close()
    print(f"Courbes ROC et Précision-Rappel sauvegardées -> {chemin_sortie}")


# =============================================================================
# 6. Interprétabilité (SHAP)
# =============================================================================
def calculer_et_sauvegarder_shap(meilleur_pipe: Pipeline, X_test, chemin_sortie: str = "shap_summary.png"):
    X_test_transforme = meilleur_pipe.named_steps["prep"].transform(X_test)
    if hasattr(X_test_transforme, "toarray"):
        X_test_transforme = X_test_transforme.toarray()
    noms_colonnes = noms_features_apres_encodage(meilleur_pipe.named_steps["prep"])
    X_test_df = pd.DataFrame(X_test_transforme, columns=noms_colonnes)

    modele_final = meilleur_pipe.named_steps["model"]
    try:
        if isinstance(modele_final, LogisticRegression):
            explainer = shap.LinearExplainer(modele_final, X_test_df)
        else:
            explainer = shap.TreeExplainer(modele_final)
        valeurs_shap = explainer.shap_values(X_test_df)
        shap.summary_plot(valeurs_shap, X_test_df, show=False)
        plt.tight_layout()
        plt.savefig(chemin_sortie, dpi=150)
        plt.close()
        print(f"Graphique d'importance SHAP sauvegardé -> {chemin_sortie}")
    except Exception as e:
        print(f"SHAP non calculé pour ce modèle ({e}).")


# =============================================================================
# 7. Calibration du seuil de décision à trois niveaux
# =============================================================================
def seuil_pour_precision_minimale(precisions, seuils, precision_visee: float):
    indices_valides = np.where(precisions[:-1] >= precision_visee)[0]
    if len(indices_valides) == 0:
        return None
    return seuils[indices_valides[0]]


def calibrer_seuils(meilleur_pipe: Pipeline, X_test, y_test, precision_blocage=0.90, precision_signalement=0.50):
    proba_finale = meilleur_pipe.predict_proba(X_test)[:, 1]
    precisions, rappels, seuils = precision_recall_curve(y_test, proba_finale)
    seuil_blocage = seuil_pour_precision_minimale(precisions, seuils, precision_blocage)
    seuil_signalement = seuil_pour_precision_minimale(precisions, seuils, precision_signalement)

    print("\n--- Seuils de décision calibrés sur le jeu de test ---")
    print(f"Seuil de BLOCAGE      (précision >= {precision_blocage:.0%}) : {seuil_blocage}")
    print(f"Seuil de SIGNALEMENT  (précision >= {precision_signalement:.0%}) : {seuil_signalement}")
    print("En dessous du seuil de signalement -> transaction approuvée.")
    if seuil_blocage is None:
        print("ATTENTION : aucun seuil n'atteint la précision visée pour le blocage —")
        print("le modèle n'est pas encore assez précis pour un blocage automatique ;")
        print("revoir le feature engineering ou le choix de modèle avant la mise en prod.")
    return seuil_blocage, seuil_signalement


# =============================================================================
# ORCHESTRATION — exécuté uniquement si le script est lancé directement
# =============================================================================
if __name__ == "__main__":
    df = charger_donnees(CHEMIN_DONNEES_DEFAUT)
    print(f"Lignes : {len(df):,} | Taux de fraude global : {df[CIBLE].mean():.3%}")

    X_train, X_test, y_train, y_test = separer_train_test(df)
    print(f"Train : {len(X_train):,} ({y_train.mean():.3%} fraude) | "
          f"Test : {len(X_test):,} ({y_test.mean():.3%} fraude)")

    preprocesseur = construire_preprocesseur()
    configurations = construire_configurations(y_train)

    resultats = comparer_toutes_les_configurations(
        configurations, preprocesseur, X_train, y_train, X_test, y_test, n_splits_cv=N_SPLITS_CV
    )

    meilleur_nom = selectionner_meilleure_configuration(resultats)
    meilleur_pipe = resultats[meilleur_nom]["pipeline"]
    print(f"\n>>> Meilleure configuration (sur la moyenne CV du PR-AUC) : {meilleur_nom}")
    print(f"    CV   PR-AUC : {resultats[meilleur_nom]['metriques_cv']['cv_pr_auc_moyenne']:.4f}")
    print(f"    Test PR-AUC : {resultats[meilleur_nom]['metriques_test']['test_pr_auc']:.4f}")

    # --- Sauvegarde du modèle retenu en .pkl, et du jeu de test associé ---
    joblib.dump(meilleur_pipe, "modele_fraude_final.pkl")
    X_test.to_csv("X_test.csv", index=False)
    y_test.to_csv("y_test.csv", index=False)
    print("Modèle sauvegardé -> modele_fraude_final.pkl")
    print("Jeu de test sauvegardé -> X_test.csv, y_test.csv (utilisés par les tests automatisés)")

    tracer_courbes_comparatives(resultats, meilleur_nom, y_test)
    calculer_et_sauvegarder_shap(meilleur_pipe, X_test)
    seuil_blocage, seuil_signalement = calibrer_seuils(meilleur_pipe, X_test, y_test)

    with mlflow.start_run(run_name=f"{meilleur_nom}_seuils"):
        mlflow.log_metric("seuil_blocage", float(seuil_blocage) if seuil_blocage is not None else -1.0)
        mlflow.log_metric("seuil_signalement", float(seuil_signalement) if seuil_signalement is not None else -1.0)

    # --- Enregistrement du modèle retenu dans le registre MLflow ---
    with mlflow.start_run(run_name=f"{meilleur_nom}_final_registre"):
        mlflow.sklearn.log_model(
            meilleur_pipe,
            artifact_path="model",
            registered_model_name="dataflow360_fraude_production",
            serialization_format="pickle",
        )
        mlflow.log_metrics(resultats[meilleur_nom]["metriques_test"])
        mlflow.log_metrics(resultats[meilleur_nom]["metriques_cv"])
        mlflow.log_param("seuil_blocage", seuil_blocage)
        mlflow.log_param("seuil_signalement", seuil_signalement)

    print("\nModèle enregistré dans le registre MLflow sous le nom "
          "'dataflow360_fraude_production'. Lancer `mlflow ui` pour explorer "
          "toutes les runs et comparer les modèles visuellement.")