"""
Test manuel du modèle sur des transactions exemples très simples
===================================================================
Pas un test automatisé (voir test_modele_fraude.py pour ça) : ici, on
fabrique à la main quelques transactions faciles à comprendre, pour
vérifier concrètement que le modèle réagit dans le bon sens avant de
lui faire confiance sur de vraies données.

À lancer avec :  python3 tester_exemples_simples.py
(modele_fraude_final.pkl doit être dans le même dossier)
"""

import joblib
import pandas as pd

modele = joblib.load("modele_fraude_final.pkl")

# ---------------------------------------------------------------------------
# On fabrique quelques transactions "à la main", volontairement caricaturales
# pour bien voir si le modèle distingue le normal du suspect.
# ---------------------------------------------------------------------------
exemples = pd.DataFrame([
    {
        # Cas 1 : transaction tout à fait normale
        "nom_cas": "Normale (petit montant, habitudes respectées)",
        "montant": 3000,
        "type": "paiement",
        "canal": "app",
        "heure": 14,
        "ecart_montant_moyen": 0.1,       # très proche de sa moyenne habituelle
        "ecart_heure_habituelle": 0.5,    # heure très proche de son habitude
        "nouvel_appareil": 0,
        "nouveau_destinataire": 0,
    },
    {
        # Cas 2 : transaction très suspecte
        "nom_cas": "Suspecte (montant inhabituel + nouvel appareil + nouveau destinataire)",
        "montant": 500000,
        "type": "transfert",
        "canal": "app",
        "heure": 3,
        "ecart_montant_moyen": 8.5,        # 8,5x plus élevé que sa moyenne habituelle
        "ecart_heure_habituelle": 9.0,     # très loin de ses horaires habituels
        "nouvel_appareil": 1,
        "nouveau_destinataire": 1,
    },
    {
        # Cas 3 : cas intermédiaire, pour voir la sensibilité du modèle
        "nom_cas": "Intermédiaire (montant un peu élevé, mais appareil connu)",
        "montant": 45000,
        "type": "transfert",
        "canal": "USSD",
        "heure": 21,
        "ecart_montant_moyen": 2.5,
        "ecart_heure_habituelle": 3.0,
        "nouvel_appareil": 0,
        "nouveau_destinataire": 1,
    },
    {
        # Cas 4 : montant élevé mais tout le reste est cohérent avec ses habitudes
        "nom_cas": "Gros montant mais habituel pour ce client (ex. commerçant)",
        "montant": 3000,
        "type": "dépôt",
        "canal": "agent",
        "heure": 11,
        "ecart_montant_moyen": 0.2,       # proche de sa moyenne à LUI (gros client habituel)
        "ecart_heure_habituelle": 0.3,
        "nouvel_appareil": 0,
        "nouveau_destinataire": 0,
    },
])

# Seuils de décision — reprendre ici les seuils calibrés par
# pipeline_fraude_mlflow.py (affichés à l'exécution) plutôt que 0.5 par défaut,
# une fois que tu les auras sur tes vraies données.
SEUIL_BLOCAGE = 0.90
SEUIL_SIGNALEMENT = 0.50


def decision(proba: float) -> str:
    if proba >= SEUIL_BLOCAGE:
        return "🚫 BLOQUER"
    elif proba >= SEUIL_SIGNALEMENT:
        return "⚠️  SIGNALER pour revue"
    else:
        return "✅ APPROUVER"


colonnes_modele = [c for c in exemples.columns if c != "nom_cas"]
probabilites = modele.predict_proba(exemples[colonnes_modele])[:, 1]

print(f"{'Cas':60s} {'Proba. fraude':>15s}   Décision")
print("-" * 100)
for i, row in exemples.iterrows():
    proba = probabilites[i]
    print(f"{row['nom_cas']:60s} {proba:14.2%}   {decision(proba)}")