from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.app import auth, case1, case2, main, official_data, routes
from src.app.ai import MockAIProvider
from src.app.config import AppSettings
from src.app.database import Base, get_session
from src.app.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    local = AppSettings(environment="local", ai_provider="mock", auth_required=False)
    original_settings_dependency = auth.get_settings
    for module in (auth, main, official_data, routes):
        monkeypatch.setattr(module, "get_settings", lambda: local)
    for module in (case1, case2):
        monkeypatch.setattr(module, "get_ai_provider", MockAIProvider)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Generator[Session, None, None]:
        with sessions() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[original_settings_dependency] = lambda: local
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)
