"""Pruebas del entorno base del laboratorio."""

import pytest

from scripts.check_environment import check_datasets, normalize_column
from src.config import load_azure_settings

AZURE_VARIABLES = (
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT",
    "AZURE_OPENAI_API_VERSION",
)


def test_normalize_column_removes_accents() -> None:
    assert normalize_column("Número de Resolución") == "Numero de Resolucion"


def test_required_datasets_are_readable() -> None:
    assert check_datasets()


def test_missing_azure_configuration_has_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in AZURE_VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    with pytest.raises(ValueError, match="Faltan variables de Azure OpenAI"):
        load_azure_settings(env_file=None)
