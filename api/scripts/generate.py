"""Génération de données synthétiques pour PostgreSQL."""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from api.core.config import Settings
from api.db.models import (
    Base,
    Client,
    CreditApplication,
    CreditScore,
    FraudAlert,
    Transaction,
)
from api.db.session import _get_engine


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

fake_settings = Settings()

NUMBER_OF_CLIENTS = 500

MIN_TRANSACTIONS_PER_CLIENT = 10
MAX_TRANSACTIONS_PER_CLIENT = 30

MIN_APPLICATIONS_PER_CLIENT = 0
MAX_APPLICATIONS_PER_CLIENT = 3

FRAUD_ALERT_PROBABILITY = 0.08

RANDOM_SEED = 42
DATASET_REFERENCE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _get_rng(rng: random.Random | None) -> random.Random:
    return random.Random(RANDOM_SEED) if rng is None else rng


# ---------------------------------------------------------------------------
# Données de référence
# ---------------------------------------------------------------------------

REGIONS = [
    "Dakar",
    "Thiès",
    "Diourbel",
    "Saint-Louis",
    "Louga",
    "Kaolack",
    "Fatick",
    "Ziguinchor",
    "Kolda",
    "Tambacounda",
    "Matam",
    "Kaffrine",
    "Sédhiou",
    "Kédougou",
]

SEXES = ["F", "M"]

ACCOUNT_TYPES = [
    "standard",
    "premium",
]

TRANSACTION_TYPES = [
    "deposit",
    "withdrawal",
    "transfer",
    "payment",
]

CHANNELS = [
    "mobile_app",
    "ussd",
    "agent",
]


# ---------------------------------------------------------------------------
# Génération des clients
# ---------------------------------------------------------------------------

def generate_clients(rng: random.Random | None = None) -> list[Client]:
    """Génère les clients synthétiques."""

    rng = _get_rng(rng)
    clients = []

    for index in range(NUMBER_OF_CLIENTS):
        client = Client(
            client_id=f"CLI-{index + 1:06d}",
            age=rng.randint(18, 70),
            sexe=rng.choice(SEXES),
            region=rng.choice(REGIONS),
            account_type=rng.choice(ACCOUNT_TYPES),
            created_at=DATASET_REFERENCE_TIME - timedelta(days=rng.randint(0, 365)),
            data_origin="synthetic",
        )

        clients.append(client)

    return clients


# ---------------------------------------------------------------------------
# Génération des transactions
# ---------------------------------------------------------------------------

def generate_transactions(
    clients: list[Client],
    rng: random.Random | None = None,
) -> list[Transaction]:
    """Génère les transactions liées aux clients."""

    rng = _get_rng(rng)
    transactions = []

    for client in clients:
        number_of_transactions = rng.randint(
            MIN_TRANSACTIONS_PER_CLIENT,
            MAX_TRANSACTIONS_PER_CLIENT,
        )

        for _ in range(number_of_transactions):
            occurred_at = DATASET_REFERENCE_TIME - timedelta(
                days=rng.randint(0, 180),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )

            transaction = Transaction(
                transaction_id=f"TX-{len(transactions) + 1:08d}",
                client_id=client.client_id,
                amount=round(
                    rng.uniform(500, 500_000),
                    2,
                ),
                type=rng.choice(TRANSACTION_TYPES),
                channel=rng.choice(CHANNELS),
                occurred_at=occurred_at,
                data_origin="synthetic",
            )

            transactions.append(transaction)

    return transactions


# ---------------------------------------------------------------------------
# Génération des alertes fraude
# ---------------------------------------------------------------------------

def generate_fraud_alerts(
    transactions: list[Transaction],
    rng: random.Random | None = None,
) -> list[FraudAlert]:
    """Génère des alertes fraude synthétiques."""

    rng = _get_rng(rng)
    alerts = []

    for transaction in transactions:

        # Toutes les transactions ne sont pas suspectes.
        if rng.random() > FRAUD_ALERT_PROBABILITY:
            continue

        risk_score = round(
            rng.uniform(0.60, 0.99),
            4,
        )

        if risk_score >= 0.85:
            risk_level = "high"
        else:
            risk_level = "medium"

        alert = FraudAlert(
            alert_id=len(alerts) + 1,
            transaction_id=transaction.transaction_id,
            risk_score=risk_score,
            risk_level=risk_level,
            created_at=transaction.occurred_at,
            data_origin="synthetic",
        )

        alerts.append(alert)

    return alerts


# ---------------------------------------------------------------------------
# Génération des demandes de crédit
# ---------------------------------------------------------------------------

def generate_credit_applications(
    clients: list[Client],
    rng: random.Random | None = None,
) -> list[CreditApplication]:
    """Génère les demandes de crédit."""

    rng = _get_rng(rng)
    applications = []

    for client in clients:

        number_of_applications = rng.randint(
            MIN_APPLICATIONS_PER_CLIENT,
            MAX_APPLICATIONS_PER_CLIENT,
        )

        for _ in range(number_of_applications):

            income = round(
                rng.uniform(80_000, 1_500_000),
                2,
            )

            expenses = round(
                income * rng.uniform(0.20, 0.80),
                2,
            )

            application = CreditApplication(
                application_id=f"APP-{len(applications) + 1:08d}",
                client_id=client.client_id,
                requested_amount=round(
                    rng.uniform(25_000, 2_000_000),
                    2,
                ),
                duration=rng.choice(
                    [3, 6, 9, 12, 18, 24]
                ),
                income=income,
                expenses=expenses,
                data_origin="synthetic",
            )

            applications.append(application)

    return applications


# ---------------------------------------------------------------------------
# Génération des scores crédit
# ---------------------------------------------------------------------------

def generate_credit_scores(
    applications: list[CreditApplication],
    rng: random.Random | None = None,
) -> list[CreditScore]:
    """Génère des scores crédit synthétiques."""

    rng = _get_rng(rng)
    scores = []

    for index, application in enumerate(applications):

        debt_ratio = application.expenses / application.income

        risk_score = 0.20 + (debt_ratio * 0.50)

        if application.requested_amount > application.income * 2:
            risk_score += 0.20

        risk_score += rng.uniform(-0.05, 0.05)

        risk_score = min(
            max(risk_score, 0.0),
            1.0,
        )

        risk_score = round(risk_score, 4)

        if risk_score < 0.35:
            risk_level = "low"
        elif risk_score < 0.65:
            risk_level = "medium"
        else:
            risk_level = "high"

        score = CreditScore(
            id=index + 1,
            application_id=application.application_id,
            risk_score=risk_score,
            risk_level=risk_level,
            created_at=DATASET_REFERENCE_TIME,
            data_origin="synthetic",
        )

        scores.append(score)

    return scores


def generate_dataset() -> tuple[
    list[Client],
    list[Transaction],
    list[FraudAlert],
    list[CreditApplication],
    list[CreditScore],
]:
    """Construit le même jeu de données à chaque appel."""
    rng = random.Random(RANDOM_SEED)
    clients = generate_clients(rng)
    transactions = generate_transactions(clients, rng)
    alerts = generate_fraud_alerts(transactions, rng)
    applications = generate_credit_applications(clients, rng)
    scores = generate_credit_scores(applications, rng)
    return clients, transactions, alerts, applications, scores


# ---------------------------------------------------------------------------
# Insertion PostgreSQL
# ---------------------------------------------------------------------------

def insert_data(
    clients: list[Client],
    transactions: list[Transaction],
    alerts: list[FraudAlert],
    applications: list[CreditApplication],
    scores: list[CreditScore],
) -> None:
    """Crée les tables et insère les données."""

    if not fake_settings.database_url:
        raise RuntimeError(
            "DATABASE_URL n'est pas configurée."
        )

    engine = _get_engine(fake_settings.database_url)

    # Création des tables si elles n'existent pas.
    Base.metadata.create_all(engine)

    with Session(engine) as session:

        # Nettoyage des anciennes données.
        # L'ordre respecte les clés étrangères.
        session.execute(delete(FraudAlert))
        session.execute(delete(CreditScore))
        session.execute(delete(Transaction))
        session.execute(delete(CreditApplication))
        session.execute(delete(Client))

        session.add_all(clients)
        session.flush()

        session.add_all(transactions)
        session.flush()

        session.add_all(alerts)
        session.add_all(applications)
        session.flush()

        session.add_all(scores)

        session.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('api_fraud_alerts', 'alert_id'),
                    COALESCE(MAX(alert_id), 1),
                    COUNT(*) > 0
                )
                FROM api_fraud_alerts
                """
            )
        )
        session.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('api_credit_scores', 'id'),
                    COALESCE(MAX(id), 1),
                    COUNT(*) > 0
                )
                FROM api_credit_scores
                """
            )
        )

        session.commit()

    print()
    print("======================================")
    print("  Données DataFlow360 générées")
    print("======================================")
    print(f"Clients              : {len(clients)}")
    print(f"Transactions         : {len(transactions)}")
    print(f"Alertes fraude       : {len(alerts)}")
    print(f"Demandes de crédit  : {len(applications)}")
    print(f"Scores crédit        : {len(scores)}")
    print("======================================")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Point d'entrée du script."""

    print("Génération des données synthétiques...")

    clients, transactions, alerts, applications, scores = generate_dataset()

    insert_data(
        clients=clients,
        transactions=transactions,
        alerts=alerts,
        applications=applications,
        scores=scores,
    )


if __name__ == "__main__":
    main()