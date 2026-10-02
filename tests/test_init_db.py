from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.db.models import Base, Client
from api.scripts.init_db import _has_existing_data


def test_empty_schema_is_eligible_for_initial_seed() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    assert _has_existing_data(engine) is False


def test_existing_records_prevent_initial_seed() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            Client(
                client_id="client_existing",
                age=30,
                sexe="F",
                region="Dakar",
                account_type="standard",
            )
        )
        session.commit()

    assert _has_existing_data(engine) is True