"""
src/features/build_dataset_fraude.py

Assemble dataset_fraude.csv (1 ligne = 1 transaction historique) en
appelant les fonctions PARTAGÉES de features.py — les mêmes qui serviront
en production plus tard.
"""

import os
import pandas as pd
from features import build_features_fraude

if __name__ == "__main__":
    os.makedirs("../../data/processed", exist_ok=True)
    transactions = pd.read_csv("../../data/synthetic/transactions.csv")

    dataset = build_features_fraude(transactions)
    dataset.to_csv("../../data/processed/dataset_fraude.csv", index=False)

    print(f"{len(dataset)} lignes -> data/processed/dataset_fraude.csv")
    print(f"Taux de fraude dans le dataset : {dataset['fraude'].mean():.2%}")
    print(dataset.head(3).to_string(index=False))