"""
streaming/producer.py

Simule le flux de transactions arrivant en temps réel sur la plateforme.
Contrairement au générateur historique (Sprint 1), ce script :
  - génère des transactions datées de MAINTENANT, en continu
  - ne contient JAMAIS de label `fraude` — personne ne le sait à cet instant
  - publie chaque transaction sur Kafka, topic "transactions.raw"

Usage : python producer.py [--intervalle-sec 1] [--n-max 0]
    --n-max 0 = tourne indéfiniment (Ctrl+C pour arrêter)
"""

import argparse
import json
import os
import time
from datetime import datetime

import numpy as np
import pandas as pd
from kafka import KafkaProducer
from sqlalchemy import create_engine

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

PG_USER = os.getenv("POSTGRES_USER", "terangasafe")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "terangasafe_pwd")
PG_DB = os.getenv("POSTGRES_DB", "terangasafe")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5433")

KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT = os.getenv("KAFKA_PORT", "9092")
TOPIC = "transactions.raw"

TYPES = ["transfert", "paiement", "retrait", "dépôt"]
POIDS_TYPES = [0.50, 0.30, 0.15, 0.05]
CANAUX = ["app", "USSD", "agent"]
POIDS_CANAUX = [0.55, 0.30, 0.15]


import random

def map_compte_vers_client(id_compte: str) -> str:
    """Convertit 'cpt_000001' → 'CLI-000001' (format attendu par l'API DataFlow360)."""
    # Extrait le numéro : cpt_000001 → 000001
    num = id_compte.replace("cpt_", "").replace("C", "")
    try:
        n = int(num)
        return f"CLI-{n:06d}"
    except ValueError:
        return f"CLI-{random.randint(1, 500):06d}"

def charger_comptes_et_appareils():
    """Récupère les clients depuis les tables API DataFlow360."""
    url = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    engine = create_engine(url)

    comptes = pd.read_sql_table("api_clients", engine)
    # Renommer pour matcher le reste du code
    comptes = comptes.rename(columns={
        "client_id": "id_compte",
        "region": "zone_habituelle",
    })
    if "statut_compte" not in comptes.columns:
        comptes["statut_compte"] = "actif"

    # Appareils : on n'a pas d'info dans api_transactions, on génère un ID par client
    appareils_par_compte = {
        cid: [f"dev_{cid}"]
        for cid in comptes["id_compte"].unique()
    }

    return comptes, appareils_par_compte


def generer_une_transaction(rng, comptes_df, appareils_par_compte, id_transaction):
    ligne = comptes_df.sample(1, random_state=None).iloc[0]
    id_compte_emetteur = ligne["id_compte"]
    zone = ligne["zone_habituelle"]

    montant = float(np.clip(rng.lognormal(mean=8.3, sigma=0.9), 100, 300000))
    type_ = str(rng.choice(TYPES, p=POIDS_TYPES))
    canal = str(rng.choice(CANAUX, p=POIDS_CANAUX))

    # destinataire aléatoire (pour transfert/paiement) parmi tous les comptes,
    # en excluant explicitement l'émetteur lui-même (bug détecté en test :
    # un compte ne doit jamais s'envoyer de l'argent à lui-même)
    destinataire = ""
    if type_ in ["transfert", "paiement"]:
        autres_comptes = comptes_df[comptes_df["id_compte"] != id_compte_emetteur]
        if len(autres_comptes) > 0:
            destinataire = str(autres_comptes.sample(1).iloc[0]["id_compte"])

    # appareil : la plupart du temps l'appareil habituel du client, parfois un nouveau
    devs_connus = appareils_par_compte.get(id_compte_emetteur, [])
    if devs_connus and rng.random() < 0.95:
        id_appareil = rng.choice(devs_connus)
    else:
        id_appareil = f"dev_new_{rng.integers(100000, 999999)}"  # appareil jamais vu

    return {
        "id_transaction": f"txn_live_{id_transaction:010d}",
        "id_compte_emetteur": str(id_compte_emetteur),
        "id_compte_destinataire_client": str(destinataire) if destinataire else "",
        "id_compte_emetteur_original": str(id_compte_emetteur),
        "id_compte_destinataire": str(destinataire),
        "montant": round(montant, 0),
        "horodatage": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "type": type_,
        "canal": canal,
        "zone_geo": zone,
        "id_appareil": str(id_appareil),
    }


def verifier_client_existe(client_id: str, engine) -> bool:
    """Vérifie que le client existe dans api_clients."""
    from sqlalchemy import text
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT 1 FROM api_clients WHERE client_id = :cid LIMIT 1"),
            {"cid": client_id},
        ).fetchone()
        return result is not None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intervalle-sec", type=float, default=1.0,
                         help="Délai entre deux transactions simulées")
    parser.add_argument("--n-max", type=int, default=0,
                         help="Nombre de transactions à envoyer (0 = illimité)")
    args = parser.parse_args()

    print("Chargement des comptes/appareils depuis PostgreSQL...")
    comptes_df, appareils_par_compte = charger_comptes_et_appareils()
    print(f"{len(comptes_df)} comptes actifs chargés.")

    print(f"Connexion à Kafka ({KAFKA_HOST}:{KAFKA_PORT})...")
    producer = KafkaProducer(
        bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    rng = np.random.default_rng()
    compteur = 0
    print(f"Démarrage de la simulation (topic '{TOPIC}'). Ctrl+C pour arrêter.")

    try:
        while args.n_max == 0 or compteur < args.n_max:
            tx = generer_une_transaction(rng, comptes_df, appareils_par_compte, compteur)
            producer.send(TOPIC, value=tx)
            print(f"  -> envoyé {tx['id_transaction']} | {tx['montant']} FCFA | {tx['type']}")
            compteur += 1
            time.sleep(args.intervalle_sec)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        producer.flush()
        producer.close()
        print(f"Total envoyé : {compteur} transactions.")


if __name__ == "__main__":
    main()