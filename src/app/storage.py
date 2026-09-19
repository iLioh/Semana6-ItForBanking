"""Acceso privado a Blob Storage exclusivamente desde el backend."""

from __future__ import annotations

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from src.app.config import AppSettings, get_settings


class PrivateBlobStorage:
    def __init__(self, settings: AppSettings | None = None):
        resolved = settings or get_settings()
        if not resolved.azure_storage_account_url:
            raise ValueError("AZURE_STORAGE_ACCOUNT_URL no esta configurado")
        self.client = BlobServiceClient(
            account_url=resolved.azure_storage_account_url,
            credential=DefaultAzureCredential(),
        )

    def download_prepared(self, blob_name: str) -> bytes:
        """Descarga exclusivamente datasets simulados del contenedor privado."""

        blob = self.client.get_blob_client(container="prepared-private", blob=blob_name)
        return blob.download_blob(max_concurrency=1).readall()

    def upload_prepared_if_absent(self, blob_name: str, content: bytes) -> bool:
        """Carga un dataset oficial sin sobrescribir blobs existentes."""

        from azure.core.exceptions import ResourceExistsError

        blob = self.client.get_blob_client(container="prepared-private", blob=blob_name)
        try:
            blob.upload_blob(content, overwrite=False)
        except ResourceExistsError:
            if self.download_prepared(blob_name) != content:
                raise ValueError(f"Blob oficial existente con contenido distinto: {blob_name}") from None
            return False
        return True

    def upload_artifact(self, blob_name: str, content: bytes) -> None:
        """Guarda un artefacto de evaluacion en un contenedor privado."""

        blob = self.client.get_blob_client(container="evaluation-artifacts", blob=blob_name)
        blob.upload_blob(content, overwrite=True)
