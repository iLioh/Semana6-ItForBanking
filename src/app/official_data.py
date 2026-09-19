"""Datasets simulados oficiales; las referencias se cargan por separado."""

from __future__ import annotations

import csv
from io import StringIO

from src.app.config import PROJECT_ROOT, get_settings
from src.app.storage import PrivateBlobStorage

ROOT = PROJECT_ROOT / "data" / "official"
FILES = {
    "companies": ("case1/empresas_simuladas.csv", "case1/empresas_simuladas.csv"),
    "reference": ("case1/referencia_academica.csv", "case1/referencia_academica.csv"),
    "complaints": ("case2/quejas_bancarias_30.csv", "case2/quejas_bancarias_30.csv"),
    "golden": ("case2/golden_humano_30.csv", "case2/golden_humano_30.csv"),
}


def _read(key: str) -> list[dict[str, str]]:
    relative, blob_name = FILES[key]
    settings = get_settings()
    if settings.environment != "local" and settings.azure_storage_account_url:
        content = PrivateBlobStorage(settings).download_prepared(blob_name).decode("utf-8-sig")
    else:
        content = (ROOT / relative).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(StringIO(content)))


def load_companies() -> list[dict[str, str]]:
    rows = _read("companies")
    if len(rows) != 15 or len({row["empresa_id"] for row in rows}) != 15:
        raise ValueError("Se requieren 15 empresas simuladas con IDs únicos")
    return rows


def load_case1_reference() -> dict[str, dict[str, str]]:
    rows = _read("reference")
    if len(rows) != 15 or len({row["empresa_id"] for row in rows}) != 15:
        raise ValueError("Se requieren 15 referencias académicas con IDs únicos")
    return {row["empresa_id"]: row for row in rows}


def load_complaints() -> list[dict[str, str]]:
    rows = _read("complaints")
    if len(rows) != 30 or len({row["caso_id"] for row in rows}) != 30:
        raise ValueError("Se requieren 30 quejas simuladas con IDs únicos")
    return rows


def load_golden() -> dict[str, dict[str, str]]:
    rows = _read("golden")
    labels = [row["categoria_golden"] for row in rows]
    if len(rows) != 30 or len({row["caso_id"] for row in rows}) != 30:
        raise ValueError("Se requieren 30 etiquetas humanas con IDs únicos")
    if any(labels.count(category) != 10 for category in ("FRAUDE", "SERVICIO", "PRODUCTO")):
        raise ValueError("El golden humano debe estar balanceado 10/10/10")
    return {row["caso_id"]: row for row in rows}
