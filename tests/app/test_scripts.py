import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from scripts.reset_lab06_data import reset_data
from scripts.seed_official_datasets import validate_official_datasets
from src.app.database import Base
from src.app.models import ProcessingBatch


def test_seed_validation_is_local_and_balanced() -> None:
    files = validate_official_datasets()
    assert [len(rows) for rows in files.values()] == [15, 15, 30, 30]


def test_reset_requires_confirmation_and_exact_lab06_target(tmp_path) -> None:
    path = tmp_path / "lab06_reset.db"
    url = f"sqlite:///{path.as_posix()}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(ProcessingBatch(case_type="CASE1_OFFICIAL", source="test"))
        session.commit()
    with pytest.raises(ValueError, match="--yes"):
        reset_data(url, "lab06_reset.db", False)
    with pytest.raises(ValueError, match="Base equivocada"):
        reset_data(url, "lab06_other.db", True)
    with Session(engine) as session:
        assert session.scalar(select(ProcessingBatch)) is not None
    counts = reset_data(url, "lab06_reset.db", True)
    assert counts["before"]["processing_batches"] == 1
    assert counts["after"]["processing_batches"] == 0
    engine.dispose()
