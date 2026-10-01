"""
src/features/build_dataset_credit.py (v2 — pipeline d'extraction)

Ne lit plus les CSV locaux : EXTRAIT credits, comptes, transactions et
remboursements directement depuis PostgreSQL, applique le feature
engineering partagé (features.py), puis écrit le résultat.

    Génération → PostgreSQL (source) → Extraction (ce script) → dataset_credit.csv

Prérequis : docker-compose up -d, puis python load_all.py (au moins une fois)
Usage     : python build_dataset_credit.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from features import build_features_credit

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except ImportError:
    pass

PG_USER = os.getenv("POSTGRES_USER", "terangasafe")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "terangasafe_pwd")
PG_DB = os.getenv("POSTGRES_DB", "terangasafe")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5433")


def get_engine():
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)


if __name__ == "__main__":
    os.makedirs("../../data/processed", exist_ok=True)

    print(f"Extraction depuis PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DB})...")
    engine = get_engine()

    credits = pd.read_sql_table("credits", engine)
    comptes = pd.read_sql_table("comptes", engine)
    transactions = pd.read_sql_table("transactions", engine)
    remboursements = pd.read_sql_table("remboursements", engine)
    print(f"  {len(credits)} credits, {len(comptes)} comptes, "
          f"{len(transactions)} transactions, {len(remboursements)} remboursements extraits")

    dataset = build_features_credit(credits, comptes, transactions, remboursements)
    dataset.to_csv("../../data/processed/dataset_credit.csv", index=False)

    print(f"{len(dataset)} lignes -> data/processed/dataset_credit.csv")
    print(f"Taux de défaut dans le dataset : {dataset['defaut'].mean():.2%}")
    print(f"Cold start (taux_remboursement manquant) : {dataset['taux_remboursement'].isna().sum()} lignes")