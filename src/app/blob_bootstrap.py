"""Carga única de los cuatro CSV simulados oficiales y retiro exacto de blobs legacy."""

from __future__ import annotations

import logging

from src.app.config import PROJECT_ROOT, get_settings
from src.app.storage import PrivateBlobStorage

log = logging.getLogger("lab06.blob_bootstrap")
FILES = (
    "case1/empresas_simuladas.csv",
    "case1/referencia_academica.csv",
    "case2/quejas_bancarias_30.csv",
    "case2/golden_humano_30.csv",
)
LEGACY = ("reactiva_anonimizada.csv", "complaints_golden.csv")


def bootstrap_official_blobs() -> None:
    storage = PrivateBlobStorage(get_settings())
    root = PROJECT_ROOT / "data" / "official"
    for name in FILES:
        content = (root / name).read_bytes()
        storage.upload_prepared_if_absent(name, content)
    container = storage.client.get_container_client("prepared-private")
    existing = {blob.name for blob in container.list_blobs()}
    if not set(FILES) <= existing:
        raise RuntimeError("No están presentes los cuatro CSV oficiales en Blob")
    for name in LEGACY:
        if name in existing:
            container.delete_blob(name)
            log.info("legacy_blob_deleted name=%s", name)
    log.info("official_blobs_ready count=%s", len(FILES))
