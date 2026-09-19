"""Elimina solo datos de ejecución del Lab06 tras confirmar la base objetivo."""

from __future__ import annotations

import argparse
import json
import re
import struct
from datetime import UTC, datetime
from pathlib import Path

import pyodbc
from azure.identity import AzureCliCredential
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

TABLES = (
    "human_reviews", "complaint_predictions", "complaints", "financial_assessments",
    "companies_processed", "model_runs", "processing_batches",
)
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")
SQL_ACCESS_TOKEN_ATTRIBUTE = 1256


def _azure_engine(server: str, database: str):
    if not IDENTIFIER.fullmatch(server) or not IDENTIFIER.fullmatch(database):
        raise ValueError("Servidor o base Azure SQL inválidos")
    credential = AzureCliCredential()
    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{server}.database.windows.net,1433;"
        f"Database={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    def connect():
        token = credential.get_token("https://database.windows.net/.default").token
        encoded = token.encode("utf-16-le")
        packed = struct.pack(f"<I{len(encoded)}s", len(encoded), encoded)
        return pyodbc.connect(
            connection_string, attrs_before={SQL_ACCESS_TOKEN_ATTRIBUTE: packed}, autocommit=False
        )

    return create_engine("mssql+pyodbc://", creator=connect, pool_pre_ping=True)


def reset_data(
    database_url: str | None, expected_database: str, confirmed: bool,
    *, azure_server: str | None = None, backup_path: Path | None = None,
) -> dict[str, dict[str, int]]:
    if not confirmed:
        raise ValueError("Se requiere --yes")
    if not any(marker in expected_database.lower() for marker in ("lab06", "laboratorio06")):
        raise ValueError("El nombre esperado debe identificar explícitamente Lab06")
    if azure_server:
        if backup_path is None:
            raise ValueError("Azure SQL requiere --backup-path antes del borrado")
        engine = _azure_engine(azure_server, expected_database)
        backend = "mssql"
        sqlite_name = None
    else:
        if not database_url:
            raise ValueError("Se requiere URL de base local o --server Azure")
        url = make_url(database_url)
        backend = url.get_backend_name()
        if backend not in {"mssql", "sqlite"}:
            raise ValueError("Solo se admite Azure SQL o SQLite local de prueba")
        sqlite_name = url.database.rsplit("/", 1)[-1] if backend == "sqlite" else None
        engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            actual = (connection.scalar(text("SELECT DB_NAME()")) if backend == "mssql"
                      else sqlite_name)
            if actual != expected_database:
                raise ValueError(f"Base equivocada: se esperaba {expected_database}, se obtuvo {actual}")
            before = {table: connection.scalar(text(f"SELECT COUNT(*) FROM {table}"))
                      for table in TABLES}
            print("Antes:", before)
            if backup_path is not None:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                snapshot = {
                    "database": actual, "created_at": datetime.now(UTC).isoformat(),
                    "tables": {
                        table: [dict(row) for row in connection.execute(text(f"SELECT * FROM {table}")).mappings()]
                        for table in TABLES
                    },
                }
                with backup_path.open("x", encoding="utf-8") as file:
                    json.dump(snapshot, file, ensure_ascii=False, default=str)
                print(f"Respaldo local: {backup_path}")
            for table in TABLES:
                connection.execute(text(f"DELETE FROM {table}"))
            after = {table: connection.scalar(text(f"SELECT COUNT(*) FROM {table}"))
                     for table in TABLES}
            print("Después:", after)
            return {"before": before, "after": after}
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--database-url")
    target.add_argument("--server", help="Azure SQL con identidad del operador en Azure CLI")
    parser.add_argument("--expected-database", required=True)
    parser.add_argument("--backup-path", type=Path)
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    reset_data(args.database_url, args.expected_database, args.yes,
               azure_server=args.server, backup_path=args.backup_path)


if __name__ == "__main__":
    main()
