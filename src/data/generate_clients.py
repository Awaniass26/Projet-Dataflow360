"""
src/data/generate_clients.py

Table 1/8 — Clients.
Base de toute la chaîne : comptes, appareils, activités, credits en dépendent.

Utilise Faker (comme indiqué dans le README du projet) pour les numéros de
téléphone, afin d'avoir un format réaliste sans être de vraies données.
"""

import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

RANDOM_SEED = 42
AUJOURD_HUI = datetime(2026, 9, 24)

REGIONS = [
    "Dakar", "Thiès", "Diourbel", "Saint-Louis", "Kaolack",
    "Ziguinchor", "Louga", "Fatick", "Kolda", "Tambacounda",
]
POIDS_REGIONS = [0.32, 0.13, 0.08, 0.07, 0.08, 0.06, 0.06, 0.06, 0.07, 0.07]


def generate_clients(n_clients: int = 6000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    fake = Faker("fr_FR")
    Faker.seed(seed)

    # Téléphones sénégalais réalistes : préfixes 77/78/76/70 + 7 chiffres
    prefixes = rng.choice(["77", "78", "76", "70"], size=n_clients)
    telephones = [f"{p}{rng.integers(1000000, 9999999)}" for p in prefixes]

    ages = np.clip(rng.normal(loc=34, scale=11, size=n_clients), 18, 75).astype(int)
    regions = rng.choice(REGIONS, size=n_clients, p=POIDS_REGIONS)

    # 12% de marchands, 88% de particuliers (cohérent avec l'usage mobile money réel)
    types_client = rng.choice(["particulier", "marchand"], size=n_clients, p=[0.88, 0.12])

    jours_inscription = rng.integers(1, 730, size=n_clients)
    dates_inscription = [AUJOURD_HUI - timedelta(days=int(j)) for j in jours_inscription]

    df = pd.DataFrame({
        "id_client": [f"cli_{i:06d}" for i in range(1, n_clients + 1)],
        "telephone": telephones,
        "age": ages,
        "region": regions,
        "type_client": types_client,
        "date_inscription": [d.strftime("%Y-%m-%d") for d in dates_inscription],
    })
    return df


if __name__ == "__main__":
    df = generate_clients()
    df.to_csv("../../data/synthetic/clients.csv", index=False)
    print(f"{len(df)} clients -> data/synthetic/clients.csv")
    print(df["type_client"].value_counts())