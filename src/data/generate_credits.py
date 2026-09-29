"""
src/data/generate_credits.py

Table 7/8 — Demandes/octrois de crédit.
Séparée de remboursements (correctif validé avec le groupe) : cette table
porte la date_octroi_credit, indispensable pour calculer les features sans
fuite temporelle (on ne doit utiliser que l'historique AVANT cette date).

Règle métier appliquée ici : seuls les comptes >= 90 jours d'ancienneté
sont éligibles (cohérent avec la règle cold start définie dans le guide
technique). Ce n'est pas une variable du modèle, c'est un filtre en amont.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
AUJOURD_HUI = datetime(2026, 9, 24)

MONTANTS_POSSIBLES = [5000, 10000, 15000, 25000, 50000, 100000]
POIDS_MONTANTS = [0.25, 0.25, 0.20, 0.15, 0.10, 0.05]
DUREES_POSSIBLES = [3, 6, 9, 12]
POIDS_DUREES = [0.30, 0.40, 0.20, 0.10]

TAUX_CLIENTS_AVEC_CREDIT = 0.35


def generate_credits(comptes_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    eligibles = comptes_df[
        (comptes_df["anciennete_jours"] >= 90) & (comptes_df["statut_compte"] == "actif")
    ].copy()

    n_avec_credit = int(len(eligibles) * TAUX_CLIENTS_AVEC_CREDIT)
    clients_avec_credit = eligibles.sample(n=n_avec_credit, random_state=seed)

    lignes = []
    id_credit = 1
    for _, row in clients_avec_credit.iterrows():
        n_credits = rng.choice([1, 2, 3], p=[0.60, 0.28, 0.12])
        date_creation_compte = datetime.strptime(row["date_creation_compte"], "%Y-%m-%d")

        for _ in range(n_credits):
            # la date d'octroi doit être postérieure à date_creation_compte + 90 jours
            plus_tot_possible = date_creation_compte + timedelta(days=90)
            marge_jours = (AUJOURD_HUI - plus_tot_possible).days
            if marge_jours <= 0:
                continue
            offset = rng.integers(0, marge_jours)
            date_octroi = plus_tot_possible + timedelta(days=int(offset))

            lignes.append({
                "id_credit": f"cred_{id_credit:06d}",
                "id_client": row["id_client"],
                "date_octroi_credit": date_octroi.strftime("%Y-%m-%d"),
                "montant_credit_demande": rng.choice(MONTANTS_POSSIBLES, p=POIDS_MONTANTS),
                "duree_credit_demande": rng.choice(DUREES_POSSIBLES, p=POIDS_DUREES),
            })
            id_credit += 1

    df = pd.DataFrame(lignes).sort_values("date_octroi_credit").reset_index(drop=True)
    return df


if __name__ == "__main__":
    comptes = pd.read_csv("../../data/synthetic/comptes.csv")
    df = generate_credits(comptes)
    df.to_csv("../../data/synthetic/credits.csv", index=False)
    print(f"{len(df)} crédits générés -> data/synthetic/credits.csv")
    print(f"Clients concernés : {df['id_client'].nunique()}")