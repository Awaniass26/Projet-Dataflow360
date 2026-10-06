"""
Pipeline complet — Détection de fraude mobile money (DataFlow360)
===================================================================
Suite de l'EDA déjà réalisée par l'équipe. Ce script couvre :
  1. Préparation des données
  2. Séparation train/test (+ note importante sur le split temporel)
  3. Comparaison de plusieurs modèles — dont deux variantes XGBoost avec
     sur-échantillonnage (SMOTE) et sous-échantillonnage — trackés avec MLflow
  4. Sélection du meilleur modèle (métrique adaptée au déséquilibre)
  5. Courbes ROC et Précision-Rappel comparatives pour tous les modèles
  6. Interprétabilité (SHAP)
  7. Calibration du seuil de décision à trois niveaux (approuver/signaler/bloquer)
  8. Enregistrement du modèle retenu dans le registre MLflow

Prérequis : pip install mlflow shap xgboost scikit-learn pandas imbalanced-learn
"""

import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import shap
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, precision_recall_curve, roc_curve,
)
from imblearn.pipeline import Pipeline  # pipeline compatible avec les étapes de ré-échantillonnage
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

RANDOM_STATE = 42
CHEMIN_DONNEES = "/home/moctar04/Documents/data/data_flow_project/Projet-Dataflow360/notebooks/dataset_fraude_clean.csv"  # <- adapter au vrai fichier (493 000 lignes)

# ---------------------------------------------------------------------------
# 1. Chargement et préparation
# ---------------------------------------------------------------------------
df = pd.read_csv(CHEMIN_DONNEES)

colonnes_bool = ["nouvel_appareil", "nouveau_destinataire"]
for c in colonnes_bool:
    df[c] = df[c].astype(int)

CIBLE = "fraude"
FEATURES_NUM = [
    "montant", "heure", "ecart_montant_moyen", "ecart_heure_habituelle",
] + colonnes_bool
FEATURES_CAT = ["type", "canal"]
FEATURES = FEATURES_NUM + FEATURES_CAT

X = df[FEATURES]
y = df[CIBLE].astype(int)

print(f"Lignes : {len(df):,} | Taux de fraude global : {y.mean():.3%}")

# ---------------------------------------------------------------------------
# 2. Séparation train/test
# ---------------------------------------------------------------------------
# IMPORTANT : ceci est un split ALÉATOIRE STRATIFIÉ, pas temporel, faute de
# colonne de date/timestamp explicite dans cet extrait. Comme on l'a vu dans
# la méthodologie, un split temporel (entraîner sur le passé, tester sur le
# plus récent) est préférable pour éviter toute fuite implicite et obtenir
# une estimation fidèle de la performance en production. Si le dataset
# complet contient une vraie colonne de date/heure d'événement (pas juste
# "heure" qui ne représente que l'heure de la journée), remplacer ce split
# par un tri chronologique + découpage séquentiel.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
print(f"Train : {len(X_train):,} ({y_train.mean():.3%} fraude) | "
      f"Test : {len(X_test):,} ({y_test.mean():.3%} fraude)")

# ---------------------------------------------------------------------------
# 3. Préprocesseur commun (encodage des variables catégorielles)
# ---------------------------------------------------------------------------
preprocesseur = ColumnTransformer(
    transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), FEATURES_CAT)],
    remainder="passthrough",
)

def noms_features_apres_encodage(preprocesseur_fit) -> list[str]:
    """Récupère les noms de colonnes après OneHotEncoding, pour SHAP et le feature importance."""
    noms_cat = list(preprocesseur_fit.named_transformers_["cat"].get_feature_names_out(FEATURES_CAT))
    return noms_cat + FEATURES_NUM


# ---------------------------------------------------------------------------
# 4. Entraînement + tracking MLflow pour chaque modèle
# ---------------------------------------------------------------------------
ratio_desequilibre = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

# Nombre de voisins pour SMOTE : ne peut pas dépasser (nb d'exemples minoritaires - 1).
# Avec une fraude très rare, ce garde-fou évite un plantage si peu de cas positifs.
n_minoritaire_train = int((y_train == 1).sum())
k_voisins_smote = max(1, min(5, n_minoritaire_train - 1))


# trois façons de traiter le déséquilibre : pondération (scale_pos_weight),
# sur-échantillonnage (SMOTE) et sous-échantillonnage (RandomUnderSampler) —
# plutôt que de supposer a priori laquelle fonctionne le mieux sur ces données.
CONFIGURATIONS = {
    "logistic_regression": (
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
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
            n_estimators=300, max_depth=5, learning_rate=0.05,
            scale_pos_weight=ratio_desequilibre, eval_metric="aucpr",
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        None,
    ),
    "xgboost_surechantillonnage_smote": (
        # scale_pos_weight=1 (pas de pondération en plus) : SMOTE a déjà rééquilibré
        # les classes dans le jeu d'entraînement, cumuler les deux techniques
        # sur-corrigerait inutilement.
        XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            scale_pos_weight=1, eval_metric="aucpr",
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        SMOTE(random_state=RANDOM_STATE, k_neighbors=k_voisins_smote),
    ),
    "xgboost_sous_echantillonnage": (
        XGBClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            scale_pos_weight=1, eval_metric="aucpr",
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        RandomUnderSampler(random_state=RANDOM_STATE),
    ),
}

mlflow.set_experiment("dataflow360_detection_fraude")

courbes = {}  # nom_modele -> courbes ROC/PR, pour le graphique comparatif


def construire_pipeline(modele, echantillonneur=None) -> Pipeline:
    etapes = [("prep", preprocesseur)]
    if echantillonneur is not None:
        # Le ré-échantillonnage (imblearn) n'agit QUE pendant .fit() sur le train ;
        # il est automatiquement ignoré lors de .predict()/.predict_proba() sur le
        # jeu de test, qui doit impérativement rester dans sa distribution réelle.
        etapes.append(("echantillonnage", echantillonneur))
    etapes.append(("model", modele))
    return Pipeline(etapes)


def entrainer_et_logger(nom_modele: str, modele, echantillonneur=None) -> tuple[Pipeline, dict]:
    with mlflow.start_run(run_name=nom_modele):
        pipe = construire_pipeline(modele, echantillonneur)
        pipe.fit(X_train, y_train)

        proba_test = pipe.predict_proba(X_test)[:, 1]
        preds_test = (proba_test >= 0.5).astype(int)

        metriques = {
            "precision": precision_score(y_test, preds_test, zero_division=0),
            "recall": recall_score(y_test, preds_test, zero_division=0),
            "f1": f1_score(y_test, preds_test, zero_division=0),
            "roc_auc": roc_auc_score(y_test, proba_test),
            "pr_auc": average_precision_score(y_test, proba_test),  # métrique clé en cas de fort déséquilibre
        }

        mlflow.log_param("modele", nom_modele)
        mlflow.log_param("echantillonnage", type(echantillonneur).__name__ if echantillonneur else "aucun")
        mlflow.log_params({f"hp_{k}": v for k, v in modele.get_params().items()})
        mlflow.log_metrics(metriques)
        mlflow.sklearn.log_model(pipe, artifact_path="model", serialization_format="pickle")

        tn, fp, fn, tp = confusion_matrix(y_test, preds_test).ravel()
        print(f"\n=== {nom_modele} ===")
        for k, v in metriques.items():
            print(f"  {k:10s} : {v:.4f}")
        print(f"  Matrice de confusion -> VN={tn} FP={fp} FN={fn} VP={tp}")

        # Courbes complètes, conservées pour le graphique comparatif (étape 5)
        fpr, tpr, _ = roc_curve(y_test, proba_test)
        prec_c, rec_c, _ = precision_recall_curve(y_test, proba_test)
        courbes[nom_modele] = {
            "fpr": fpr, "tpr": tpr, "roc_auc": metriques["roc_auc"],
            "precision": prec_c, "recall": rec_c, "pr_auc": metriques["pr_auc"],
        }

        return pipe, metriques


resultats = {}
for nom, (modele, echantillonneur) in CONFIGURATIONS.items():
    pipe, metriques = entrainer_et_logger(nom, modele, echantillonneur)
    resultats[nom] = {"pipeline": pipe, "metriques": metriques}

# ---------------------------------------------------------------------------
# 5. Sélection du meilleur modèle — sur le PR-AUC, pas l'accuracy ni même
#    le ROC-AUC seul, car bien plus fiable en cas de fort déséquilibre.
# ---------------------------------------------------------------------------
meilleur_nom = max(resultats, key=lambda n: resultats[n]["metriques"]["pr_auc"])
meilleur_pipe = resultats[meilleur_nom]["pipeline"]
print(f"\n>>> Meilleur modèle : {meilleur_nom} "
      f"(PR-AUC = {resultats[meilleur_nom]['metriques']['pr_auc']:.4f})")

# --- Sauvegarde du modèle retenu en .pkl, et du jeu de test associé ---
# Le .pkl est indépendant de MLflow : utile pour le charger directement dans
# l'API FastAPI de scoring (voir architecture du projet), ou pour les tests
# automatisés ci-dessous (test_modele_fraude.py), sans dépendre du serveur
# MLflow ni de son registre.
import joblib

joblib.dump(meilleur_pipe, "modele_fraude_final.pkl")
X_test.to_csv("X_test.csv", index=False)
y_test.to_csv("y_test.csv", index=False)
print("Modèle sauvegardé -> modele_fraude_final.pkl")
print("Jeu de test sauvegardé -> X_test.csv, y_test.csv (utilisés par les tests automatisés)")

# ---------------------------------------------------------------------------
# 5bis. Courbes ROC et Précision-Rappel comparatives (tous les modèles,
#       XGBoost inclus) — permettent de voir visuellement, pas seulement sur
#       un chiffre unique, où chaque modèle/stratégie de ré-échantillonnage
#       se situe sur toute la gamme de seuils possibles.
# ---------------------------------------------------------------------------
fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(14, 6))

for nom, c in courbes.items():
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
plt.savefig("courbes_roc_pr_comparaison.png", dpi=150)
plt.close()
print("Courbes ROC et Précision-Rappel sauvegardées -> courbes_roc_pr_comparaison.png")
print("(le modèle retenu apparaît en pointillés plus épais sur le graphique)")

# ---------------------------------------------------------------------------
# 6. Interprétabilité (SHAP) sur le meilleur modèle
# ---------------------------------------------------------------------------
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
    plt.savefig("shap_summary.png", dpi=150)
    plt.close()
    print("Graphique d'importance SHAP sauvegardé -> shap_summary.png")
except Exception as e:
    print(f"SHAP non calculé pour ce modèle ({e}).")

# ---------------------------------------------------------------------------
# 7. Calibration du seuil de décision à trois niveaux
#    (Approuver / Signaler pour revue / Bloquer avant écriture en base)
# ---------------------------------------------------------------------------
proba_finale = meilleur_pipe.predict_proba(X_test)[:, 1]
precisions, rappels, seuils = precision_recall_curve(y_test, proba_finale)

# Exemple de règle : on choisit le seuil de BLOCAGE comme celui atteignant au
# moins 90% de précision (peu de faux positifs bloqués à tort), et le seuil
# de SIGNALEMENT comme celui atteignant au moins 50% de précision (on tolère
# plus de faux positifs, car il n'y a pas de blocage, juste une revue humaine).
def seuil_pour_precision_minimale(precisions, seuils, precision_visee):
    indices_valides = np.where(precisions[:-1] >= precision_visee)[0]
    if len(indices_valides) == 0:
        return None
    return seuils[indices_valides[0]]

seuil_blocage = seuil_pour_precision_minimale(precisions, seuils, precision_visee=0.90)
seuil_signalement = seuil_pour_precision_minimale(precisions, seuils, precision_visee=0.50)

print("\n--- Seuils de décision calibrés sur le jeu de test ---")
print(f"Seuil de BLOCAGE      (précision >= 90%) : {seuil_blocage}")
print(f"Seuil de SIGNALEMENT  (précision >= 50%) : {seuil_signalement}")
print("En dessous du seuil de signalement -> transaction approuvée.")
print("NOTE : ces seuils doivent être recalibrés avec l'équipe métier selon")
print("le coût réel d'un faux positif vs un faux négatif (voir méthodologie).")
if seuil_blocage is None:
    print("ATTENTION : aucun seuil n'atteint 90% de précision avec ce modèle —")
    print("le modèle n'est pas encore assez précis pour un blocage automatique ;")
    print("revoir le feature engineering ou le choix de modèle avant la mise en prod.")

with mlflow.start_run(run_name=f"{meilleur_nom}_seuils"):
    mlflow.log_metric("seuil_blocage", float(seuil_blocage) if seuil_blocage is not None else -1.0)
    mlflow.log_metric("seuil_signalement", float(seuil_signalement) if seuil_signalement is not None else -1.0)

# ---------------------------------------------------------------------------
# 8. Enregistrement du modèle retenu dans le registre MLflow
# ---------------------------------------------------------------------------
with mlflow.start_run(run_name=f"{meilleur_nom}_final_registre"):
    mlflow.sklearn.log_model(
        meilleur_pipe,
        artifact_path="model",
        registered_model_name="dataflow360_fraude_production",
        serialization_format="pickle",
    )
    mlflow.log_metrics(resultats[meilleur_nom]["metriques"])
    mlflow.log_param("seuil_blocage", seuil_blocage)
    mlflow.log_param("seuil_signalement", seuil_signalement)

print("\nModèle enregistré dans le registre MLflow sous le nom "
      "'dataflow360_fraude_production'. Lancer `mlflow ui` pour explorer "
      "toutes les runs et comparer les modèles visuellement.")