"""
src/data/generate_activites.py

Table 4/8 — Activités (connexions app/USSD, consultations de solde).
Volume volontairement plus modeste que les transactions : ce ne sont pas
des mouvements d'argent, juste des événements d'usage de l'application.
Utile pour l'EDA et pour enrichir de futurs indicateurs d'engagement.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
AUJOURD_HUI = datetime(2026, 9, 24)

TYPES_ACTIVITE = ["connexion_app", "connexion_ussd", "consultation_solde"]
POIDS_TYPES = [0.55, 0.30, 0.15]


def generate_activites(clients_df: pd.DataFrame, appareils_df: pd.DataFrame,
                        n_activites: int = 120_000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Chaque activité est rattachée à un appareil existant (donc au bon client)
    idx_appareils = rng.integers(0, len(appareils_df), size=n_activites)
    ids_appareils = appareils_df["id_appareil"].values[idx_appareils]
    ids_clients = appareils_df["id_client"].values[idx_appareils]

    types_ = rng.choice(TYPES_ACTIVITE, size=n_activites, p=POIDS_TYPES)
    jours_offset = rng.integers(0, 730, size=n_activites)
    heures = np.clip(rng.normal(loc=15, scale=4.5, size=n_activites), 0, 23).astype(int)

    horodatages = [
        (AUJOURD_HUI - timedelta(days=int(j))).replace(
            hour=int(h), minute=int(rng.integers(0, 60)), second=int(rng.integers(0, 60))
        )
        for j, h in zip(jours_offset, heures)
    ]

    df = pd.DataFrame({
        "id_activite": [f"act_{i:08d}" for i in range(1, n_activites + 1)],
        "id_client": ids_clients,
        "id_appareil": ids_appareils,
        "type_activite": types_,
        "horodatage": [h.strftime("%Y-%m-%dT%H:%M:%S") for h in horodatages],
    })
    return df


if __name__ == "__main__":
    clients = pd.read_csv("../../data/synthetic/clients.csv")
    appareils = pd.read_csv("../../data/synthetic/appareils.csv")
    df = generate_activites(clients, appareils)
    df.to_csv("../../data/synthetic/activites.csv", index=False)
    print(f"{len(df)} activités -> data/synthetic/activites.csv")