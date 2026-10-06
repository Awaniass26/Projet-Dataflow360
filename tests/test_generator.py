from api.scripts.generate import generate_dataset


def _snapshot() -> tuple[tuple[tuple[object, ...], ...], ...]:
    return tuple(
        tuple(
            tuple(getattr(record, column.name) for column in record.__table__.columns)
            for record in records
        )
        for records in generate_dataset()
    )


def test_generated_dataset_is_identical_across_runs() -> None:
    assert _snapshot() == _snapshot()