"""
streaming/consumer.py

Lit chaque transaction publiée par producer.py sur Kafka, puis l'envoie
à l'API DataFlow360 (POST /fraud/predict) pour scoring temps réel.

L'API :
  - appelle le VRAI modèle fraude
  - renvoie risk_score + risk_level
  - persiste automatiquement dans api_fraud_alerts si HIGH

Le consumer NE persiste RIEN lui-même (délégation à l'API).
Le producer calcule déjà les features : le consumer les transmet telles quelles.

Usage : python consumer.py
"""

import json
import os
import time
from datetime import datetime

import requests
from kafka import KafkaConsumer

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

# --- Configuration Kafka ---
KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT = os.getenv("KAFKA_PORT", "9092")
TOPIC = "transactions.raw"

# --- Configuration API DataFlow360 ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_LOGIN_URL = f"{API_BASE_URL}/auth/login"
API_PREDICT_URL = f"{API_BASE_URL}/fraud/predict"

# --- Identifiants du compte de service ---
SERVICE_EMAIL = os.getenv("SERVICE_EMAIL", "service-consumer@dataflow360.com")
SERVICE_PASSWORD = os.getenv("SERVICE_PASSWORD", "service-consumer-2026")

API_TIMEOUT_SEC = 5


# ---------------------------------------------------------------------------
# Authentification JWT
# ---------------------------------------------------------------------------
_token_cache = {"access_token": None, "expires_at": 0}


def get_token() -> str | None:
    """Récupère un token JWT valide (avec cache)."""
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    try:
        resp = requests.post(
            API_LOGIN_URL,
            data={"username": SERVICE_EMAIL, "password": SERVICE_PASSWORD},
            timeout=API_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        data = resp.json()
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 3600)
        print(f"  🔑 Nouveau token obtenu (valide {data.get('expires_in', 3600)}s)")
        return data["access_token"]
    except requests.exceptions.RequestException as exc:
        print(f"  ❌ Échec du login : {exc}")
        return None


# ---------------------------------------------------------------------------
# Mapping des champs Data Ing → API DataFlow360
# ---------------------------------------------------------------------------
_TYPE_MAPPING = {
    "deposit": "deposit",
    "withdrawal": "withdrawal",
    "transfer": "transfer",
    "payment": "payment",
    "dépôt": "deposit",
    "retrait": "withdrawal",
    "transfert": "transfer",
    "paiement": "payment",
}

_CHANNEL_MAPPING = {
    "mobile_app": "mobile_app",
    "ussd": "ussd",
    "agent": "agent",
    "app": "mobile_app",
    "USSD": "ussd",
}


def _normaliser_type(value: str) -> str:
    """Convertit les types Data Ing (FR) → types API (EN)."""
    return _TYPE_MAPPING.get(value, value)


def _normaliser_canal(value: str) -> str:
    """Convertit les canaux Data Ing → canaux API."""
    return _CHANNEL_MAPPING.get(value, value)


def _build_api_payload(tx: dict) -> dict:
    """Construit le payload attendu par POST /fraud/predict.

    Le producer calcule déjà les features : on les transmet telles quelles.
    """
    occurred_at = tx["horodatage"]
    if not occurred_at.endswith("Z") and "+" not in occurred_at:
        occurred_at = occurred_at + "Z"

    hour = datetime.fromisoformat(tx["horodatage"].replace("Z", "")).hour

    return {
        "transaction_id": tx["id_transaction"],
        "amount": float(tx["montant"]),
        "transaction_type": _normaliser_type(tx["type"]),
        "channel": _normaliser_canal(tx["canal"]),
        "occurred_at": occurred_at,
        "sender_account_id": tx["id_compte_emetteur"],
        "recipient_account_id": (
            tx["id_compte_destinataire"]
            if tx["id_compte_destinataire"]
            else tx["id_compte_emetteur"]
        ),
        "hour": int(tx.get("hour", hour)),
        "ecart_montant_moyen": float(tx.get("ecart_montant_moyen", 1.0)),
        "ecart_heure_habituelle": float(tx.get("ecart_heure_habituelle", 0.0)),
        "nouvel_appareil": bool(tx.get("nouvel_appareil", False)),
        "nouveau_destinataire": bool(tx.get("nouveau_destinataire", False)),
    }


# ---------------------------------------------------------------------------
# Appel API DataFlow360
# ---------------------------------------------------------------------------
def appeler_api(tx: dict) -> dict | None:
    """Appelle POST /fraud/predict. Retourne None si échec."""
    token = get_token()
    if token is None:
        return None

    payload = _build_api_payload(tx)

    try:
        resp = requests.post(
            API_PREDICT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=API_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        print(f"  ❌ Échec appel API : {exc}")
        return None


# ---------------------------------------------------------------------------
# Traitement d'une transaction
# ---------------------------------------------------------------------------
def traiter_transaction(tx: dict):
    resultat = appeler_api(tx)

    if resultat is None:
        print(f"  ⚠️  API indisponible : {tx['id_transaction']} ignoré")
        return

    risk_score = resultat.get("risk_score")
    risk_level = resultat.get("risk_level")
    is_simulation = resultat.get("is_simulation", True)

    emoji = "🚨" if risk_level == "high" else ("⚠️" if risk_level == "medium" else "✅")
    score_str = f"{risk_score:.3f}" if risk_score is not None else "N/A"
    print(f"  {emoji} {tx['id_transaction']} | score={score_str} | {risk_level} | sim={is_simulation}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"API ciblée : {API_PREDICT_URL}")
    print(f"Service    : {SERVICE_EMAIL}")

    # Test du login au démarrage
    token = get_token()
    if token is None:
        print("❌ Impossible de s'authentifier — vérifier API et identifiants")
        return
    print("✅ Authentification OK")

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
            traiter_transaction(message.value)
    except KeyboardInterrupt:
        print("\nArrêt demandé.")


if __name__ == "__main__":
    main()