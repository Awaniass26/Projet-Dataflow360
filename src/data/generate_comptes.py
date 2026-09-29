"""
src/data/generate_comptes.py

Table 2/8 — Comptes mobile money.
1 client peut avoir 1 compte (hypothèse simplificatrice assumée : pas de
multi-comptes pour ce projet). L'ancienneté du compte est ce qui alimentera
la règle métier du "cold start" (>= 90 jours pour être éligible au crédit).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
AUJOURD_HUI = datetime(2026, 9, 24)

ZONES = [
    "Dakar-Plateau", "Pikine", "Guédiawaye", "Parcelles Assainies",
    "Rufisque", "Thiès", "Mbour", "Touba", "Saint-Louis", "Kaolack",
    "Ziguinchor", "Diourbel",
]
POIDS_ZONES = [0.22, 0.10, 0.08, 0.09, 0.07, 0.09, 0.06, 0.08, 0.06, 0.06, 0.05, 0.04]


def generate_comptes(clients_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(clients_df)

    # Le compte est créé le même jour que l'inscription client ou quelques
    # jours après (délai réaliste d'activation)
    dates_inscription = pd.to_datetime(clients_df["date_inscription"])
    delai_activation = rng.integers(0, 5, size=n)
    dates_creation_compte = dates_inscription + pd.to_timedelta(delai_activation, unit="D")

    anciennete_jours = (AUJOURD_HUI - dates_creation_compte).dt.days

    zones = rng.choice(ZONES, size=n, p=POIDS_ZONES)
    # 97% actifs, 2% suspendus, 1% fermés (réaliste, faible taux de churn simulé)
    statuts = rng.choice(["actif", "suspendu", "fermé"], size=n, p=[0.97, 0.02, 0.01])

    df = pd.DataFrame({
        "id_compte": [f"cpt_{i:06d}" for i in range(1, n + 1)],
        "id_client": clients_df["id_client"].values,
        "date_creation_compte": dates_creation_compte.dt.strftime("%Y-%m-%d"),
        "anciennete_jours": anciennete_jours,
        "zone_habituelle": zones,
        "statut_compte": statuts,
    })
    return df


if __name__ == "__main__":
    clients = pd.read_csv("../../data/synthetic/clients.csv")
    df = generate_comptes(clients)
    df.to_csv("../../data/synthetic/comptes.csv", index=False)
    print(f"{len(df)} comptes -> data/synthetic/comptes.csv")
    print(f"Comptes < 90 jours (cold start) : {(df['anciennete_jours'] < 90).sum()} "
          f"({(df['anciennete_jours'] < 90).mean():.1%})")