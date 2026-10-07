"""Producteur Kafka — simule un flux continu de transactions."""

import json
import random
import time
from datetime import UTC, datetime

from confluent_kafka import Producer

from api.core.config import Settings

TOPIC_FALLBACK = "transactions"


def _generate_transaction() -> dict:
    return {
        "transaction_id": f"TX-KAFKA-{int(time.time() * 1000)}",
        "sender_account_id": f"CLI-{random.randint(1, 500):06d}",
        "recipient_account_id": f"CLI-{random.randint(1, 500):06d}",
        "amount": round(random.uniform(500, 500_000), 2),
        "transaction_type": random.choice(
            ["deposit", "withdrawal", "transfer", "payment"]
        ),
        "channel": random.choice(["mobile_app", "ussd", "agent"]),
        "occurred_at": datetime.now(UTC).isoformat(),
        "hour": random.randint(0, 23),
        "ecart_montant_moyen": round(random.uniform(-5000, 50000), 2),
        "ecart_heure_habituelle": random.randint(-3, 3),
        "nouvel_appareil": random.choice([True, False]),
        "nouveau_destinataire": random.choice([True, False]),
    }


def main() -> None:
    settings = Settings()
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    topic = settings.kafka_topic_transactions or TOPIC_FALLBACK

    print(f"Producteur Kafka → {settings.kafka_bootstrap_servers}, topic={topic}")

    while True:
        try:
            tx = _generate_transaction()
            producer.produce(topic, json.dumps(tx).encode("utf-8"))
            producer.flush()
            print(f"Envoyé : {tx['transaction_id']} ({tx['amount']} FCFA)")
        except Exception as exc:  # noqa: BLE001
            print(f"Erreur producteur : {exc}")
        time.sleep(3)


if __name__ == "__main__":
    main()