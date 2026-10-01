"""
src/features/build_dataset_fraude.py (v2 — pipeline d'extraction)

Ne lit plus un CSV local : EXTRAIT les transactions directement depuis
PostgreSQL (la vraie source, chargée par load_postgres.py), applique le
feature engineering partagé (features.py), puis écrit le résultat.

C'est le schéma complet demandé par le groupe :
    Génération → PostgreSQL (source) → Extraction (ce script) → dataset_fraude.csv

Prérequis : docker-compose up -d, puis python load_all.py (au moins une fois)
Usage     : python build_dataset_fraude.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from features import build_features_fraude

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
    transactions = pd.read_sql_table("transactions", engine)
    print(f"  {len(transactions)} transactions extraites")

    dataset = build_features_fraude(transactions)
    dataset.to_csv("../../data/processed/dataset_fraude.csv", index=False)

    print(f"{len(dataset)} lignes -> data/processed/dataset_fraude.csv")
    print(f"Taux de fraude dans le dataset : {dataset['fraude'].mean():.2%}")