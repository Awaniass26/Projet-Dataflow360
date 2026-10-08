"""Migrations non destructives du schéma PostgreSQL."""

from sqlalchemy import Engine, text

from api.db.models import Base


def migrate_api_schema(engine: Engine) -> None:
    """Créer les tables manquantes et faire évoluer le schéma sans perte."""

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        # ------------------------------------------------------------------
        # api_clients : ajout du nom (nullable d'abord, backfill ensuite)
        # ------------------------------------------------------------------
        connection.execute(
            text(
                """
                ALTER TABLE api_clients
                ADD COLUMN IF NOT EXISTS name VARCHAR(120)
                """
            )
        )

        # Backfill : tout client dont le nom est NULL reçoit "Client <id>"
        # (les vrais noms seront fournis par le seed suivant)
        connection.execute(
            text(
                """
                UPDATE api_clients
                SET name = 'Client ' || client_id
                WHERE name IS NULL
                """
            )
        )

        # ------------------------------------------------------------------
        # api_fraud_alerts : statut + audit
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # api_credit_scores : version du modèle + index non-unique
        # ------------------------------------------------------------------
        connection.execute(
            text(
                """
                ALTER TABLE api_credit_scores
                ADD COLUMN IF NOT EXISTS model_version VARCHAR(50)
                NOT NULL DEFAULT 'simulation'
                """
            )
        )

        # Une application peut maintenant avoir plusieurs scores dans le temps.
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



                # Contrainte sur le rôle utilisateur
        connection.execute(
            text(
                """
                ALTER TABLE api_users
                DROP CONSTRAINT IF EXISTS api_users_role_check
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE api_users
                ADD CONSTRAINT api_users_role_check
                CHECK (role IN ('admin', 'analyst'))
                """
            )
        )