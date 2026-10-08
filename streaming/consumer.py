"""
streaming/consumer.py

Lit chaque transaction publiée par producer.py sur Kafka, calcule ses
features EN TEMPS RÉEL (profil lu dans Redis), puis envoie le tout à
l'API du backend pour scoring (vrai modèle) et stockage.

Si l'API backend n'est pas encore disponible (en cours de développement),
ce script retombe automatiquement sur un scoring PLACEHOLDER local, pour
que le pipeline reste testable sans bloquer sur le travail du backend.
Dès que l'API répond, elle est utilisée en priorité, sans rien changer
au code.

Voir CONTRAT_API_FRAUDE.md pour le format attendu par l'API.
-----
Usage : python consumer.py
"""

import json
import os
from datetime import datetime

import redis
import requests
from kafka import KafkaConsumer
from sqlalchemy import create_engine, text

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

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))

KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT = os.getenv("KAFKA_PORT", "9092")
TOPIC = "transactions.raw"

API_FRAUD_URL = os.getenv("API_FRAUD_URL", "http://localhost:8000/api/fraud/score")
API_TIMEOUT_SEC = 2

SEUIL_ALERTE = 0.7  # utilisé seulement en mode fallback local


def get_pg_engine():
    url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(url)


def creer_tables_si_absentes(engine):
    """Tables de secours, utilisées uniquement en mode fallback (API backend
    pas encore disponible) — une fois l'API prête, c'est elle qui stocke."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions_production (
                id_transaction TEXT PRIMARY KEY,
                id_compte_emetteur TEXT,
                id_compte_destinataire TEXT,
                montant DOUBLE PRECISION,
                horodatage TIMESTAMP,
                type TEXT,
                canal TEXT,
                zone_geo TEXT,
                id_appareil TEXT,
                ecart_montant_moyen DOUBLE PRECISION,
                nouvel_appareil BOOLEAN,
                nouveau_destinataire BOOLEAN,
                score_risque DOUBLE PRECISION,
                decision TEXT,
                source_scoring TEXT
            )
        """))
        # Migration : si la table existait déjà avant l'ajout de cette colonne
        # (CREATE TABLE IF NOT EXISTS ne modifie jamais une table existante)
        conn.execute(text(
            "ALTER TABLE transactions_production ADD COLUMN IF NOT EXISTS source_scoring TEXT"
        ))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alertes_fraude (
                id_transaction TEXT PRIMARY KEY,
                id_compte_emetteur TEXT,
                montant DOUBLE PRECISION,
                horodatage TIMESTAMP,
                score_risque DOUBLE PRECISION,
                motif TEXT
            )
        """))


def lire_profil(r: redis.Redis, id_compte: str) -> dict:
    brut = r.get(f"profil:{id_compte}")
    if brut is None:
        return {"montant_moyen": None, "appareils_connus": [], "destinataires_connus": []}
    return json.loads(brut)


def calculer_features(tx: dict, profil: dict) -> dict:
    montant = tx["montant"]
    montant_moyen = profil.get("montant_moyen")
    ecart_montant_moyen = (montant / montant_moyen) if montant_moyen else 1.0
    nouvel_appareil = tx["id_appareil"] not in profil.get("appareils_connus", [])
    nouveau_destinataire = (
        tx["id_compte_destinataire"] != ""
        and tx["id_compte_destinataire"] not in profil.get("destinataires_connus", [])
    )
    return {
        "ecart_montant_moyen": ecart_montant_moyen,
        "nouvel_appareil": nouvel_appareil,
        "nouveau_destinataire": nouveau_destinataire,
    }


def appeler_api_backend(tx: dict, features: dict):
    """Tente d'appeler l'API du backend. Retourne None si indisponible
    (timeout, connexion refusée, erreur serveur) — le fallback prend le relais."""
    payload = {**tx, "features": features}
    try:
        resp = requests.post(API_FRAUD_URL, json=payload, timeout=API_TIMEOUT_SEC)
        resp.raise_for_status()
        return resp.json()  # attendu : {"id_transaction", "score_risque", "decision"}
    except requests.exceptions.RequestException:
        return None


def scorer_fallback_local(tx: dict, features: dict) -> dict:
    """PLACEHOLDER local — utilisé uniquement si l'API backend ne répond pas."""
    score = 0.0
    if features["ecart_montant_moyen"] > 8:
        score += 0.5
    if features["nouvel_appareil"]:
        score += 0.25
    if features["nouveau_destinataire"]:
        score += 0.25
    heure = datetime.fromisoformat(tx["horodatage"]).hour
    if 1 <= heure <= 4:
        score += 0.2
    score = min(score, 1.0)
    decision = "bloquée" if score >= SEUIL_ALERTE else "validée"
    return {"id_transaction": tx["id_transaction"], "score_risque": score, "decision": decision}


def stocker_fallback_local(tx: dict, features: dict, resultat: dict, engine):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO transactions_production
            (id_transaction, id_compte_emetteur, id_compte_destinataire, montant,
             horodatage, type, canal, zone_geo, id_appareil,
             ecart_montant_moyen, nouvel_appareil, nouveau_destinataire,
             score_risque, decision, source_scoring)
            VALUES (:id_transaction, :id_compte_emetteur, :id_compte_destinataire, :montant,
                    :horodatage, :type, :canal, :zone_geo, :id_appareil,
                    :ecart_montant_moyen, :nouvel_appareil, :nouveau_destinataire,
                    :score_risque, :decision, 'fallback_local')
            ON CONFLICT (id_transaction) DO NOTHING
        """), {**tx, **features, "score_risque": resultat["score_risque"], "decision": resultat["decision"]})

        if resultat["decision"] == "bloquée":
            conn.execute(text("""
                INSERT INTO alertes_fraude
                (id_transaction, id_compte_emetteur, montant, horodatage, score_risque, motif)
                VALUES (:id_transaction, :id_compte_emetteur, :montant, :horodatage, :score_risque, :motif)
                ON CONFLICT (id_transaction) DO NOTHING
            """), {**tx, "score_risque": resultat["score_risque"],
                    "motif": f"fallback local - ecart_montant={features['ecart_montant_moyen']:.1f}, "
                             f"nouvel_appareil={features['nouvel_appareil']}, "
                             f"nouveau_destinataire={features['nouveau_destinataire']}"})


def traiter_transaction(tx: dict, r: redis.Redis, engine):
    profil = lire_profil(r, tx["id_compte_emetteur"])
    features = calculer_features(tx, profil)

    resultat = appeler_api_backend(tx, features)
    if resultat is not None:
        print(f"  [API backend] {resultat['id_transaction']} | "
              f"score={resultat['score_risque']:.2f} | {resultat['decision']}")
        return

    resultat = scorer_fallback_local(tx, features)
    stocker_fallback_local(tx, features, resultat, engine)
    print(f"  [fallback local] {resultat['id_transaction']} | "
          f"score={resultat['score_risque']:.2f} | {resultat['decision']}")


def main():
    engine = get_pg_engine()
    creer_tables_si_absentes(engine)
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    print(f"API backend ciblée : {API_FRAUD_URL}")
    print(f"Connexion à Kafka ({KAFKA_HOST}:{KAFKA_PORT}), topic '{TOPIC}'...")
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
    )

    print("En écoute... Ctrl+C pour arrêter.")
    try:
        for message in consumer:
            traiter_transaction(message.value, r, engine)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")


if __name__ == "__main__":
    main()