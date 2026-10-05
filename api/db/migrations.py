"""Migrations non destructives du schéma PostgreSQL."""

from sqlalchemy import Engine, text

from api.db.models import Base


def migrate_api_schema(engine: Engine) -> None:
    """Créer les tables manquantes et faire évoluer le schéma sans perte."""

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        # Évolution de api_fraud_alerts
        connection.execute(
            text(
                """
                ALTER TABLE api_fraud_alerts
                ADD COLUMN IF NOT EXISTS status VARCHAR(20)
                NOT NULL DEFAULT 'pending'
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE api_fraud_alerts
                ADD COLUMN IF NOT EXISTS explanation TEXT
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE api_fraud_alerts
                ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE api_fraud_alerts
                ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100)
                """
            )
        )

        # Évolution de api_credit_scores
        connection.execute(
            text(
                """
                ALTER TABLE api_credit_scores
                ADD COLUMN IF NOT EXISTS model_version VARCHAR(50)
                NOT NULL DEFAULT 'simulation'
                """
            )
        )

        # Une application peut maintenant avoir plusieurs scores.
        connection.execute(
            text(
                """
                DROP INDEX IF EXISTS ix_credit_scores_application_id
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_credit_scores_application_id
                ON api_credit_scores(application_id)
                """
            )
        )