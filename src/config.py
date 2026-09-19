"""Carga y validacion de la configuracion local del laboratorio."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, HttpUrl, SecretStr

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AzureOpenAISettings(BaseModel):
    """Credenciales requeridas para conectarse a Azure OpenAI."""

    model_config = ConfigDict(frozen=True)

    endpoint: HttpUrl
    api_key: SecretStr
    deployment: str
    api_version: str


def load_azure_settings(
    env_file: Path | None = PROJECT_ROOT / ".env",
) -> AzureOpenAISettings:
    """Carga la configuracion y reporta variables faltantes sin revelar secretos."""

    if env_file is not None:
        load_dotenv(env_file)
    variable_names = {
        "endpoint": "AZURE_OPENAI_ENDPOINT",
        "api_key": "AZURE_OPENAI_API_KEY",
        "deployment": "AZURE_OPENAI_DEPLOYMENT",
        "api_version": "AZURE_OPENAI_API_VERSION",
    }
    values = {field: os.getenv(variable, "").strip() for field, variable in variable_names.items()}
    missing = [variable_names[field] for field, value in values.items() if not value]

    if missing:
        raise ValueError(
            "Faltan variables de Azure OpenAI: " + ", ".join(sorted(missing))
        )

    return AzureOpenAISettings(**values)
