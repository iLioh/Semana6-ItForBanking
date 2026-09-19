"""Conexion SQLAlchemy compatible con SQLite local y Azure SQL."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.app.config import PROJECT_ROOT, get_settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_directory(url: str) -> None:
    prefix = "sqlite:///"
    if not url.startswith(prefix) or url.endswith(":memory:"):
        return
    relative = Path(url.removeprefix(prefix))
    path = relative if relative.is_absolute() else PROJECT_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)


def build_engine(url: str | None = None):
    resolved = url or get_settings().database_url
    _ensure_sqlite_directory(resolved)
    kwargs = {"connect_args": {"check_same_thread": False}} if resolved.startswith("sqlite") else {}
    created = create_engine(resolved, pool_pre_ping=True, **kwargs)
    if resolved.startswith("mssql+pyodbc://") and "ActiveDirectoryMsi" in resolved:
        @event.listens_for(created, "do_connect")
        def remove_conflicting_trusted_connection(dialect, connection_record, args, params):
            # SQLAlchemy adds Trusted_Connection=Yes for passwordless URLs, but
            # the ODBC driver cannot combine it with ActiveDirectoryMsi.
            args[0] = args[0].replace(";Trusted_Connection=Yes", "")

    return created


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def create_schema() -> None:
    from src.app import models  # noqa: F401

    Base.metadata.create_all(engine)
