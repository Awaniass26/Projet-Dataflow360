"""
src/data/generate_appareils.py

Table 3/8 — Appareils.
La plupart des clients ont 1 appareil ; une minorité en a 2 (changement de
téléphone au cours du temps). C'est ce qui permettra plus tard de détecter
le signal "nouvel appareil" pour les scénarios de fraude combinés.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RANDOM_SEED = 42
AUJOURD_HUI = datetime(2026, 9, 24)


def generate_appareils(clients_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_clients = len(clients_df)

    # 82% des clients ont 1 seul appareil sur toute la période, 18% en ont eu 2
    n_avec_2_appareils = int(n_clients * 0.18)
    clients_2_appareils = rng.choice(clients_df["id_client"], size=n_avec_2_appareils, replace=False)
    set_2_appareils = set(clients_2_appareils)

    lignes = []
    id_app = 1
    for id_client, date_inscription in zip(clients_df["id_client"], clients_df["date_inscription"]):
        date_inscription = datetime.strptime(date_inscription, "%Y-%m-%d")
        type_appareil_1 = rng.choice(["smartphone", "feature_phone"], p=[0.68, 0.32])
        lignes.append({
            "id_appareil": f"dev_{id_app:06d}",
            "id_client": id_client,
            "date_premiere_utilisation": date_inscription.strftime("%Y-%m-%d"),
            "type_appareil": type_appareil_1,
        })
        id_app += 1

        if id_client in set_2_appareils:
            # changement d'appareil à un moment aléatoire après l'inscription
            jours_apres = rng.integers(30, 500)
            date_2 = date_inscription + timedelta(days=int(jours_apres))
            if date_2 < AUJOURD_HUI:
                type_appareil_2 = rng.choice(["smartphone", "feature_phone"], p=[0.75, 0.25])
                lignes.append({
                    "id_appareil": f"dev_{id_app:06d}",
                    "id_client": id_client,
                    "date_premiere_utilisation": date_2.strftime("%Y-%m-%d"),
                    "type_appareil": type_appareil_2,
                })
                id_app += 1

    return pd.DataFrame(lignes)


if __name__ == "__main__":
    clients = pd.read_csv("../../data/synthetic/clients.csv")
    df = generate_appareils(clients)
    df.to_csv("../../data/synthetic/appareils.csv", index=False)
    print(f"{len(df)} appareils -> data/synthetic/appareils.csv")
    print(f"Clients avec 2 appareils : {(df.groupby('id_client').size() > 1).sum()}")