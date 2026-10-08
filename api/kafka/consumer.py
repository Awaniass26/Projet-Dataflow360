"""Consumer Kafka — détecte la fraude sur les transactions en temps réel."""

import json

from confluent_kafka import Consumer, KafkaError
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.db.session import _get_engine
from api.repositories.fraud_repository import PostgresFraudAlertRepository
from api.schemas.common import RiskLevel
from api.schemas.fraud import TransactionInput
from api.services.fraud_service import FraudDetectionService


def main() -> None:
    settings = Settings()
    engine = _get_engine(settings.database_url)
    service = FraudDetectionService(settings)

    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": settings.kafka_consumer_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        }
    )
    consumer.subscribe([settings.kafka_topic_transactions])

    print(
        f"Consumer Kafka → {settings.kafka_bootstrap_servers}, "
        f"topic={settings.kafka_topic_transactions}, "
        f"group={settings.kafka_consumer_group}"
    )

    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            print(f"Erreur Kafka : {msg.error()}")
            continue

        try:
            payload = json.loads(msg.value().decode("utf-8"))
            transaction = TransactionInput(**payload)

            result = service.predict(transaction)

            if (
                result.risk_level == RiskLevel.HIGH
                and not result.is_simulation
            ):
                with Session(engine) as session:
                    repo = PostgresFraudAlertRepository(session)
                    repo.save_transaction_and_alert(
                        transaction=transaction,
                        risk_score=result.risk_score,
                        risk_level=result.risk_level,
                    )
                    session.commit()
                print(f"ALERTE persistée : {transaction.transaction_id}")
            else:
                print(f"OK : {transaction.transaction_id}")

        except Exception as exc:  # noqa: BLE001
            print(f"Erreur traitement : {exc}")


if __name__ == "__main__":
    main()