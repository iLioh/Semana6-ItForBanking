"""Apply Alembic and grant the App Service identity least-privilege SQL access.

The operator authenticates through Azure CLI; no database password or token is
printed or persisted. Run from the repository root after opening the operator's
public IPv4 in the Azure SQL firewall.
"""

from __future__ import annotations

import argparse
import re
import struct
from uuid import UUID

import pyodbc
from alembic import command
from alembic.config import Config
from azure.identity import AzureCliCredential
from sqlalchemy import create_engine, text

SQL_ACCESS_TOKEN_ATTRIBUTE = 1256
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,127}$")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--principal-client-id", required=True)
    parser.add_argument("--principal-name", default="lab06_app")
    args = parser.parse_args()

    if not IDENTIFIER.fullmatch(args.server) or not IDENTIFIER.fullmatch(args.database):
        parser.error("server y database deben ser identificadores Azure validos")
    if not IDENTIFIER.fullmatch(args.principal_name):
        parser.error("principal-name debe ser un identificador SQL simple")
    client_id = UUID(args.principal_client_id)
    credential = AzureCliCredential()
    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{args.server}.database.windows.net,1433;"
        f"Database={args.database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    def connect() -> pyodbc.Connection:
        token = credential.get_token("https://database.windows.net/.default").token
        encoded = token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(encoded)}s", len(encoded), encoded)
        return pyodbc.connect(
            connection_string,
            attrs_before={SQL_ACCESS_TOKEN_ATTRIBUTE: token_struct},
            autocommit=False,
        )

    engine = create_engine("mssql+pyodbc://", creator=connect, pool_pre_ping=True)
    with engine.begin() as connection:
        alembic_config = Config("alembic.ini")
        alembic_config.attributes["connection"] = connection
        command.upgrade(alembic_config, "head")

    sql_user = args.principal_name
    sid = client_id.bytes_le.hex()
    with engine.begin() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM sys.database_principals WHERE name = :name"),
            {"name": sql_user},
        ).scalar()
        if not exists:
            connection.exec_driver_sql(
                f"CREATE USER [{sql_user}] WITH SID = 0x{sid}, TYPE = E"
            )
        for role in ("db_datareader", "db_datawriter"):
            membership = connection.execute(
                text(
                    "SELECT 1 FROM sys.database_role_members m "
                    "JOIN sys.database_principals r ON r.principal_id = m.role_principal_id "
                    "JOIN sys.database_principals u ON u.principal_id = m.member_principal_id "
                    "WHERE r.name = :role AND u.name = :name"
                ),
                {"role": role, "name": sql_user},
            ).scalar()
            if not membership:
                connection.exec_driver_sql(f"ALTER ROLE [{role}] ADD MEMBER [{sql_user}]")

    print("Azure SQL: migraciones aplicadas; identidad de App Service con lectura/escritura.")


if __name__ == "__main__":
    main()
