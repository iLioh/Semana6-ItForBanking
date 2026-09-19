"""Configuracion por ambiente sin cargar secretos en el frontend."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AppSettings(BaseModel):
    environment: str = "local"
    database_url: str = "sqlite:///./outputs/lab06.db"
    ai_provider: str = "mock"
    ai_timeout_seconds: float = Field(default=20, gt=0, le=120)
    ai_max_retries: int = Field(default=2, ge=0, le=5)
    cors_origins: list[str] = ["http://localhost:5173"]
    auth_required: bool = False
    entra_tenant_id: str = ""
    entra_client_id: str = ""
    entra_audience: str = ""
    entra_issuer: str = ""
    entra_required_scope: str = "Lab.Access"
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_api_key: str = ""
    azure_storage_account_url: str = ""
    applicationinsights_connection_string: str = ""

    @field_validator("ai_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"mock", "azure"}:
            raise ValueError("AI_PROVIDER debe ser mock o azure")
        return normalized

    def validate_production(self) -> None:
        if self.environment != "production":
            return
        missing = [
            name
            for name, value in {
                "ENTRA_TENANT_ID": self.entra_tenant_id,
                "ENTRA_CLIENT_ID": self.entra_client_id,
                "ENTRA_AUDIENCE": self.entra_audience,
                "ENTRA_ISSUER": self.entra_issuer,
                "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
                "AZURE_OPENAI_DEPLOYMENT": self.azure_openai_deployment,
                "AZURE_STORAGE_ACCOUNT_URL": self.azure_storage_account_url,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError("Configuracion de produccion incompleta: " + ", ".join(missing))
        if not self.auth_required:
            raise ValueError("AUTH_REQUIRED debe ser true en produccion")
        if self.ai_provider != "azure":
            raise ValueError("AI_PROVIDER debe ser azure en produccion")


@lru_cache
def get_settings() -> AppSettings:
    load_dotenv(PROJECT_ROOT / ".env")
    settings = AppSettings(
        environment=os.getenv("APP_ENV", "local"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./outputs/lab06.db"),
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
        ai_timeout_seconds=os.getenv("AI_TIMEOUT_SECONDS", "20"),
        ai_max_retries=os.getenv("AI_MAX_RETRIES", "2"),
        cors_origins=[
            value.strip()
            for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if value.strip()
        ],
        auth_required=os.getenv("AUTH_REQUIRED", "false").lower() == "true",
        entra_tenant_id=os.getenv("ENTRA_TENANT_ID", ""),
        entra_client_id=os.getenv("ENTRA_CLIENT_ID", ""),
        entra_audience=os.getenv("ENTRA_AUDIENCE", ""),
        entra_issuer=os.getenv("ENTRA_ISSUER", ""),
        entra_required_scope=os.getenv("ENTRA_REQUIRED_SCOPE", "Lab.Access"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
        azure_storage_account_url=os.getenv("AZURE_STORAGE_ACCOUNT_URL", ""),
        applicationinsights_connection_string=os.getenv(
            "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
        ),
    )
    settings.validate_production()
    return settings
