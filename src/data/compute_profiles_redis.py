"""
src/data/compute_profiles_redis.py

Job BATCH (à relancer périodiquement, ex. une fois par jour) qui calcule le
profil comportemental de chaque client à partir de son historique dans
PostgreSQL, et le stocke dans Redis pour une lecture quasi instantanée par
le consommateur Kafka en temps réel.

Ce script ne s'exécute PAS en continu — on le relance ponctuellement pour
tenir les profils à jour. Le consommateur, lui, ne fait que LIRE Redis,
jamais recalculer un profil à la volée (trop lent pour du temps réel).

Prérequis : docker-compose up -d (postgres + redis), données déjà chargées
Usage     : python compute_profiles_redis.py
"""

import json
import os
import pandas as pd
import redis
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
PG_PORT = os.getenv("POSTGRES_PORT", "5433")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))


def get_pg_engine():
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)


def compute_and_store_profiles():
    engine = get_pg_engine()
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    print("Extraction des transactions et comptes depuis PostgreSQL...")
    transactions = pd.read_sql_table("transactions", engine)
    comptes = pd.read_sql_table("comptes", engine)

    # Nettoyage minimal (comme dans features.py)
    transactions["montant"] = pd.to_numeric(transactions["montant"], errors="coerce")
    transactions = transactions.dropna(subset=["montant"])
    transactions = transactions[transactions["montant"] > 0]
    transactions["date_dt"] = pd.to_datetime(transactions["horodatage"], errors="coerce")
    transactions = transactions.dropna(subset=["date_dt"])
    transactions["heure"] = transactions["date_dt"].dt.hour

    print(f"Calcul des profils pour {comptes['id_compte'].nunique()} comptes...")

    n_stockes = 0
    for id_compte, groupe in transactions.groupby("id_compte_emetteur"):
        profil = {
            "montant_moyen": float(groupe["montant"].mean()),
            "montant_ecart_type": float(groupe["montant"].std() or 0),
            "heure_moyenne": float(groupe["heure"].mean()),
            "nb_transactions_historique": int(len(groupe)),
            "appareils_connus": sorted(groupe["id_appareil"].dropna().unique().tolist()),
            "destinataires_connus": sorted(
                groupe.loc[groupe["id_compte_destinataire"] != "", "id_compte_destinataire"]
                .dropna().unique().tolist()
            ),
            "zone_habituelle": groupe["zone_geo"].mode().iloc[0] if not groupe["zone_geo"].mode().empty else None,
        }
        r.set(f"profil:{id_compte}", json.dumps(profil))
        n_stockes += 1

    print(f"{n_stockes} profils stockés dans Redis (clé profil:<id_compte>)")


if __name__ == "__main__":
    compute_and_store_profiles()