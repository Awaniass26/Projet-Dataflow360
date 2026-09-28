"""
src/features/build_dataset_credit.py

Assemble dataset_credit.csv (1 ligne = 1 demande de crédit historique) en
appelant les fonctions PARTAGÉES de features.py.

Rappel : la règle d'éligibilité (ancienneté >= 90 jours) est déjà appliquée
en amont, au moment de générer credits.csv — elle ne réapparaît donc pas
comme variable ici, conformément à la séparation règles métier / ML.
"""

import os
import pandas as pd
from features import build_features_credit

if __name__ == "__main__":
    os.makedirs("../../data/processed", exist_ok=True)
    credits = pd.read_csv("../../data/synthetic/credits.csv")
    comptes = pd.read_csv("../../data/synthetic/comptes.csv")
    transactions = pd.read_csv("../../data/synthetic/transactions.csv")
    remboursements = pd.read_csv("../../data/synthetic/remboursements.csv")

    dataset = build_features_credit(credits, comptes, transactions, remboursements)
    dataset.to_csv("../../data/processed/dataset_credit.csv", index=False)

    print(f"{len(dataset)} lignes -> data/processed/dataset_credit.csv")
    print(f"Taux de défaut dans le dataset : {dataset['defaut'].mean():.2%}")
    print(f"Cold start (taux_remboursement manquant) : {dataset['taux_remboursement'].isna().sum()} lignes")
    print(dataset.head(3).to_string(index=False))