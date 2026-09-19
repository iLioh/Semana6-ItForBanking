from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect


def test_official_migration_upgrades_local_sqlite(tmp_path: Path) -> None:
    config = Config(str(Path("alembic.ini").resolve()))
    scripts = ScriptDirectory.from_config(config)
    assert scripts.get_current_head() == "20260919_0003"
    engine = create_engine(f"sqlite:///{(tmp_path / 'lab06_migration.db').as_posix()}")
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        tables = inspect(engine)
        assert "kyc_result" in {item["name"] for item in tables.get_columns("financial_assessments")}
        assert "secondary_category" in {item["name"] for item in tables.get_columns("complaint_predictions")}
        checks = tables.get_check_constraints("complaints")
        assert any("FRAUDE" in check["sqltext"] for check in checks)
        assert all("CONSULTA" not in check["sqltext"] for check in checks)
        model_run_columns = {item["name"]: item for item in tables.get_columns("model_runs")}
        assert model_run_columns["case_type"]["type"].length == 32
    finally:
        engine.dispose()
