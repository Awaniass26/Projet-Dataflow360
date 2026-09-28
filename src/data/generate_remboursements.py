"""
src/data/generate_remboursements.py

Table 8/8 — Remboursements.
Point de cohérence important (validé avec le groupe) : `defaut` n'est PAS un
tirage aléatoire indépendant. Il est influencé par la régularité réelle du
client dans ses transactions AVANT la date d'octroi du crédit — sinon le
modèle n'aurait rien de réel à apprendre (pur bruit).

Règle de label utilisée (à documenter dans le rapport) :
    defaut = 1  si  retard_jours > 30  OU  jamais remboursé
    defaut = 0  sinon
"""

import numpy as np
import pandas as pd
from datetime import datetime

RANDOM_SEED = 42


def _regularite_client_avant_date(transactions_df, id_client, date_reference):
    """
    Mesure simple de régularité : nombre de jours actifs dans les 90 jours
    avant date_reference, normalisé sur 90. Une valeur basse = client
    irrégulier = probabilité de défaut plus élevée.
    Respecte la contrainte : n'utilise que des données AVANT date_reference.
    """
    tx = transactions_df
    mask = (
        (tx["id_compte_emetteur_client"] == id_client)
        & (tx["date_dt"] < date_reference)
        & (tx["date_dt"] >= date_reference - pd.Timedelta(days=90))
    )
    jours_actifs = tx.loc[mask, "date_dt"].dt.date.nunique()
    return min(jours_actifs / 90, 1.0)


def generate_remboursements(credits_df: pd.DataFrame, comptes_df: pd.DataFrame,
                             transactions_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Prépare les transactions pour un lookup rapide par client
    tx = transactions_df.copy()
    tx["montant"] = pd.to_numeric(tx["montant"], errors="coerce")
    tx = tx.dropna(subset=["montant"])
    tx["date_dt"] = pd.to_datetime(tx["horodatage"], errors="coerce")
    tx = tx.dropna(subset=["date_dt"])
    compte_to_client = comptes_df.set_index("id_compte")["id_client"].to_dict()
    tx["id_compte_emetteur_client"] = tx["id_compte_emetteur"].map(compte_to_client)

    # --- Étape 1 : calculer la régularité de TOUS les crédits d'abord -------
    # Important : la régularité réelle observée (fraction de jours actifs sur
    # 90j) tourne autour de 0.10-0.15 pour un usage mobile money typique,
    # jamais proche de 1. On calibre donc la probabilité de défaut sur la
    # distribution RÉELLE plutôt que sur une échelle 0-1 théorique, sinon le
    # taux de défaut global explose artificiellement (bug constaté : 40%).
    regularites = []
    for _, credit in credits_df.iterrows():
        date_ref = credit["date_octroi_credit"]
        date_ref = pd.to_datetime(date_ref)
        regularites.append(_regularite_client_avant_date(tx, credit["id_client"], date_ref))
    regularites = np.array(regularites)
    regularite_moyenne = regularites.mean()

    # --- Étape 2 : générer les remboursements avec proba calibrée -----------
    lignes = []
    id_remb = 1
    for i, (_, credit) in enumerate(credits_df.iterrows()):
        regularite = regularites[i]

        # proba = 15% pour un client dans la moyenne, module +/- selon l'écart
        # à la moyenne réelle (pas à un maximum théorique jamais atteint)
        proba_defaut = 0.15 - 1.5 * (regularite - regularite_moyenne)
        proba_defaut = float(np.clip(proba_defaut, 0.03, 0.45))

        est_defaut = rng.random() < proba_defaut
        if est_defaut:
            retard_jours = int(rng.integers(31, 120))
        else:
            retard_jours = int(rng.choice([0, 0, 0, 1, 2, 5, 10, 15], p=[0.5, 0.15, 0.1, 0.1, 0.05, 0.05, 0.03, 0.02]))

        lignes.append({
            "id_remboursement": f"remb_{id_remb:06d}",
            "id_credit": credit["id_credit"],
            "retard_jours": retard_jours,
            "defaut": int(est_defaut),
        })
        id_remb += 1

    return pd.DataFrame(lignes)


if __name__ == "__main__":
    credits = pd.read_csv("../../data/synthetic/credits.csv")
    comptes = pd.read_csv("../../data/synthetic/comptes.csv")
    transactions = pd.read_csv("../../data/synthetic/transactions.csv")

    df = generate_remboursements(credits, comptes, transactions)
    df.to_csv("../../data/synthetic/remboursements.csv", index=False)
    print(f"{len(df)} remboursements -> data/synthetic/remboursements.csv")
    print(f"Taux de défaut global : {df['defaut'].mean():.1%}")