"""
src/data/load_postgres.py

Insère dans PostgreSQL les tables structurées : clients, comptes, credits,
remboursements, transactions.

Prérequis : PostgreSQL doit être démarré séparément.
Usage     : python load_postgres.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
except ImportError:
    pass

PG_USER = os.getenv("POSTGRES_USER", "terangasafe")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "terangasafe_pwd")
PG_DB = os.getenv("POSTGRES_DB", "terangasafe")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5433")  # 5433 chez toi (5432 natif déjà pris)

SYNTHETIC_DIR = "../../data/synthetic"
TABLES = ["clients", "comptes", "credits", "remboursements", "transactions"]


def get_engine():
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)


def load_table(engine, table_name: str):
    path = f"{SYNTHETIC_DIR}/{table_name}.csv"
    if not os.path.exists(path):
        print(f"  ⚠ {path} introuvable, ignoré (as-tu lancé run_generation.py ?)")
        return
    df = pd.read_csv(path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"  {table_name} : {len(df)} lignes insérées")


if __name__ == "__main__":
    print(f"Connexion à PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DB})...")
    engine = get_engine()
    for table in TABLES:
        load_table(engine, table)
    print("Terminé. Tables PostgreSQL : " + ", ".join(TABLES))